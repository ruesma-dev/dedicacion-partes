# application/propuestas_mes.py
"""Propuestas de partida del mes, en segundo plano (F-055, R29-R33, R35,
R37; design §5.5; docs/ARCHITECTURE.md#regla-partida).

Al pedir el cuadrante de un periodo ABIERTO, tras un sync con éxito y tras
cada escritura del cuadrante, la api ENCOLA sus líneas pendientes (obra
normal, sin partida fija, sin elegida ni propuesta guardada, fuera de la
memoria de «sin propuesta» y no encoladas ya). Un solo hilo (el ejecutor del
contenedor) las calcula por orden de llegada: agrupa por obra, llama al
transfer (`POST /api/partidas/propuesta-lote`) por trozos de obras y guarda
cada propuesta SOLO si la línea sigue sin elegida ni propuesta (sin
evento). La api no propone: guarda lo que devuelve el transfer.

- Una línea sin propuesta posible, o cuya obra vuelve `{ok: false}`, entra
  en una memoria del proceso hasta el próximo sync con éxito o un reinicio.
- Si el transfer no responde o falla, la tarea se para con un log, sin
  guardar ese trozo ni tocar la memoria; el próximo cuadrante o escritura la
  relanza.
- `lanzar` nunca lanza: si algo falla, log y `False`.
- F-057: `pendientes` dice qué líneas siguen en la cola (en cola o
  calculándose) y `encolar` lo devuelve junto con `en_curso`; con eso la
  api marca `propuesta_pendiente` en cada línea y el front solo pinta.
- Estado en memoria de UNA réplica (ARCHITECTURE «Topología»).
- F-044 (R9): igual las SUBFILAS de los vinculados (también bajo una línea
  de postventa) sin elegida ni propuesta y fuera de su propia memoria de
  «sin propuesta»: su línea va al transfer con `paride` (la elegida del
  titular) y `vinculados` (`peticion_de_subfilas`), y la propuesta de cada
  una se guarda en su fila de `asignacion_vinculado` solo si sigue vacía.
  Las subfilas tienen su cola aparte: `pendientes` sigue siendo de líneas;
  `en_curso` cuenta las dos.
- F-074 (R13-R15): las memorias guardan el MOTIVO del transfer (el de su
  `motivos` / `motivos_vinculados` o el error de la obra `{ok: false}`), y
  `encolar_marcas` devuelve, de la misma foto de la cola, las `Marcas` de
  líneas y subfilas (pendientes y no encontradas con su motivo): la api las
  publica y el front pinta «buscando partida…» o «no encuentra partida».
  `olvidar_subfilas` saca de la memoria las subfilas de una línea cuyo
  titular cambia de partida, para recalcularlas.
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterable
from typing import Any

from domain.models import EstadoPeriodo, Linea
from domain.ports import UnitOfWork

from application.estado_partida import Marcas
from application.partidas_linea import peticion_de_subfilas
from application.registro_sigrid import (
    es_metodo_de_propuesta,
    es_metodo_de_propuesta_vinculado,
)
from application.use_cases import _periodo_o_error

logger = logging.getLogger(__name__)

#: (periodo_id, trabajador_ide, obra_ide): una línea de obra normal.
Clave = tuple[int, int, int]
#: (trabajador_ide, obra_ide, es_postventa): una línea en la cola (F-057).
Pendiente = tuple[int, int, bool]
#: (periodo_id, trabajador_ide, obra_ide, es_postventa, vinculado_ide): una
#: subfila de vinculado (F-044, R9).
ClaveSubfila = tuple[int, int, int, bool, int]


class PropuestasDelMes:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], transfer,
                 ejecutor, *, empresa_obras: int,
                 obras_por_llamada: int = 10) -> None:
        self._uow = uow_factory
        self._transfer = transfer
        self._ejecutor = ejecutor
        # La empresa de las obras (EMPRESA_IMPUTACION): la misma que manda
        # el selector y el registro (F-034).
        self._empresa = empresa_obras
        self._n = int(obras_por_llamada)
        self._lock = threading.Lock()
        self._en_cola: set[Clave] = set()
        # F-074 (R13, R14): la memoria de «sin propuesta», con el motivo.
        self._sin_propuesta: dict[Clave, str | None] = {}
        self._en_cola_sub: set[ClaveSubfila] = set()
        self._sin_propuesta_sub: dict[ClaveSubfila, str | None] = {}
        # Marca de parada de la api (T17b): `_calcular` la mira entre trozos.
        self._parada = threading.Event()

    # ------------------------------------------------------------- #
    def pendientes(self, periodo_id: int) -> frozenset[Pendiente]:
        """F-057: las líneas del periodo en cola o calculándose, como
        `(trabajador_ide, obra_ide, es_postventa)`. Es la misma memoria que
        llena `lanzar()`: «pendiente» es lo que se encoló, sin otra regla.
        Solo se encolan líneas de obra normal, así que `es_postventa` es
        siempre falso; va en la tupla para que quien la use case la línea
        por su identidad completa y no confunda la de postventa."""
        return self._foto(periodo_id)[1].pendientes

    def en_curso(self, periodo_id: int) -> bool:
        """¿Alguna línea o subfila (F-044) del periodo en cola o en marcha?
        (R30)."""
        return self._foto(periodo_id)[0]

    def _foto(self, periodo_id: int) -> tuple[bool, Marcas]:
        """`(en_curso, marcas)` del periodo, de una sola lectura de la cola
        (F-057); `en_curso` cuenta también las subfilas (F-044). F-074 (R13,
        R14): las marcas, también las no encontradas con su motivo y las de
        las subfilas, de la misma lectura."""
        with self._lock:
            pendientes = frozenset((c[1], c[2], False) for c in self._en_cola
                                   if c[0] == periodo_id)
            subfilas = frozenset(c[1:] for c in self._en_cola_sub
                                 if c[0] == periodo_id)
            marcas = Marcas(
                pendientes=pendientes,
                no_encontradas={(c[1], c[2], False): m for c, m
                                in self._sin_propuesta.items()
                                if c[0] == periodo_id},
                subfilas_pendientes=subfilas,
                subfilas_no_encontradas={c[1:]: m for c, m
                                         in self._sin_propuesta_sub.items()
                                         if c[0] == periodo_id})
        return bool(pendientes) or bool(subfilas), marcas

    def cerrar(self) -> None:
        """Parada de la api (T17b, O5 de la review): levanta la marca de
        parada y cancela las tareas encoladas. La tarea en marcha termina el
        trozo que está calculando (Python la espera al salir del proceso:
        como mucho un trozo, el timeout del transfer) y no empieza el
        siguiente; lo que quede se relanza con el próximo cuadrante o
        escritura, como un transfer caído (R33)."""
        self._parada.set()
        self._ejecutor.shutdown(wait=False, cancel_futures=True)

    def olvidar(self) -> None:
        """Vacía la memoria de «sin propuesta» (R32: tras un sync)."""
        with self._lock:
            self._sin_propuesta.clear()
            self._sin_propuesta_sub.clear()

    def olvidar_subfilas(self, periodo_id: int, trabajador_ide: int,
                         obra_ide: int, es_postventa: bool) -> None:
        """F-074 (R15): saca de la memoria de «sin propuesta» las subfilas
        de una línea cuyo titular cambia de partida (`CambiarPartida` les
        borra la propuesta), para que el próximo `encolar` las recalcule
        con la partida nueva del titular."""
        linea = (periodo_id, trabajador_ide, obra_ide, es_postventa)
        with self._lock:
            for c in [c for c in self._sin_propuesta_sub if c[:4] == linea]:
                del self._sin_propuesta_sub[c]

    def tras_sync(self) -> None:
        """Tras un sync con éxito: olvida y lanza cada periodo ABIERTO
        (R29, R32). Nunca lanza."""
        self.olvidar()
        try:
            with self._uow() as uow:
                abiertos = [p for p in uow.periodos.listar()
                            if p.estado is EstadoPeriodo.ABIERTO]
        except Exception:                           # noqa: BLE001
            logger.exception("[propuestas] tras el sync: no se leen los "
                             "periodos abiertos")
            return
        for p in abiertos:
            self.lanzar(p.anio, p.mes)

    def lanzar(self, anio: int, mes: int,
               trabajadores: Iterable[int] | None = None) -> bool:
        """Encola las pendientes del periodo (o solo de `trabajadores`) y
        devuelve `en_curso`. Nunca lanza (R37)."""
        return self.encolar(anio, mes, trabajadores)[0]

    def encolar(self, anio: int, mes: int,
                trabajadores: Iterable[int] | None = None,
                ) -> tuple[bool, frozenset[Pendiente]]:
        """Como `lanzar`, y además las pendientes de TODO el periodo tras
        encolar (F-057), leídas a la vez que `en_curso`: las dos salen de la
        misma foto de la cola. Periodo cerrado o inexistente, o un fallo:
        `(False, frozenset())`. Nunca lanza (R37). F-074: el envoltorio de
        `encolar_marcas` con solo las pendientes de líneas."""
        en_curso, marcas = self.encolar_marcas(anio, mes, trabajadores)
        return en_curso, marcas.pendientes

    def encolar_marcas(self, anio: int, mes: int,
                       trabajadores: Iterable[int] | None = None,
                       ) -> tuple[bool, Marcas]:
        """F-074 (R13, R14): como `encolar`, con TODAS las marcas del
        periodo tras encolar (`Marcas`), de la misma foto que `en_curso`.
        Periodo cerrado o inexistente, o un fallo: `(False, Marcas())`.
        Nunca lanza (R37)."""
        try:
            return self._lanzar(anio, mes, trabajadores)
        except Exception:                           # noqa: BLE001
            logger.exception("[propuestas] no se pudo encolar %02d/%s",
                             mes, anio)
            return False, Marcas()

    def _lanzar(self, anio, mes, trabajadores) -> tuple[bool, Marcas]:
        solo = None if trabajadores is None else set(trabajadores)
        with self._uow() as uow:
            r = uow.periodos.obtener(anio, mes)
            if r is None or r[1].estado is not EstadoPeriodo.ABIERTO:
                return False, Marcas()
            periodo_id = r[0]
            candidatas = []
            for ide, lineas in sorted(
                    uow.asignaciones.lineas_del_periodo(periodo_id).items()):
                if solo is not None and ide not in solo:
                    continue
                for ln in lineas:
                    if ln.partida_fija:
                        continue
                    titular = not ln.es_postventa \
                        and ln.partida_ide is None \
                        and ln.propuesta_ide is None
                    subfilas = [v for v in ln.vinculados
                                if v.partida_ide is None
                                and v.propuesta_ide is None]
                    if titular or subfilas:
                        candidatas.append((ide, ln, titular, subfilas))
            trabajadores = {ide: uow.trabajadores.obtener(ide)
                            for ide, *_ in candidatas}
        with self._lock:
            nuevas = []
            for ide, ln, titular, subfilas in candidatas:
                clave = (periodo_id, ide, ln.obra_ide)
                if titular and (clave in self._en_cola
                                or clave in self._sin_propuesta):
                    titular = False
                subs = [v for v in subfilas
                        if self._clave_sub(periodo_id, ide, ln, v)
                        not in self._en_cola_sub.union(
                            self._sin_propuesta_sub)]
                if not titular and not subs:
                    continue
                nuevas.append(self._pendiente(
                    periodo_id, ide, ln, trabajadores[ide],
                    clave if titular else None, subs))
            self._en_cola.update(p["clave"] for p in nuevas if p["clave"])
            self._en_cola_sub.update(c for p in nuevas for c in p["subfilas"])
        if nuevas:
            try:
                self._ejecutor.submit(self._calcular, anio, mes, nuevas)
            except Exception:
                self._desencolar(nuevas)
                raise
        return self._foto(periodo_id)

    @staticmethod
    def _clave_sub(periodo_id: int, ide: int, ln: Linea, v) -> ClaveSubfila:
        return (periodo_id, ide, ln.obra_ide, ln.es_postventa,
                v.vinculado_ide)

    def _pendiente(self, periodo_id: int, ide: int, ln: Linea, t,
                   clave: Clave | None, subs: list) -> dict:
        """Una línea de la cola: su clave si el titular está pendiente (si
        no, None) y las claves de sus subfilas pendientes (F-044). La de
        postventa lleva `:pv` en la clave del transfer."""
        linea = {"clave": f"{ide}:pv" if ln.es_postventa else str(ide),
                 "recurso_ide": ide, "nombre": t.nombre if t else None,
                 "categoria": t.categoria if t else None,
                 "es_postventa": ln.es_postventa}
        if subs:
            linea.update(peticion_de_subfilas(ln, subs))
        return {"clave": clave,
                "subfilas": [self._clave_sub(periodo_id, ide, ln, v)
                             for v in subs],
                "obra": {"ide": ln.obra_ide, "codigo": ln.cod,
                         "nombre": ln.descripcion},
                "linea": linea}

    def _desencolar(self, pendientes: list[dict]) -> None:
        with self._lock:
            self._en_cola.difference_update(p["clave"] for p in pendientes
                                            if p["clave"])
            self._en_cola_sub.difference_update(c for p in pendientes
                                                for c in p["subfilas"])

    # ------------------------------------------------------------- #
    def _calcular(self, anio: int, mes: int, pendientes: list[dict]) -> None:
        """La tarea del hilo: por trozos de obras, una llamada al transfer y
        una UoW que guarda y confirma (R31-R33)."""
        try:
            por_obra: dict[int, list[dict]] = {}
            for p in pendientes:
                por_obra.setdefault(p["obra"]["ide"], []).append(p)
            obras = sorted(por_obra.items())
            for i in range(0, len(obras), self._n):
                if self._parada.is_set():
                    logger.info("[propuestas] %02d/%s: la api se para; "
                                "quedan trozos sin calcular", mes, anio)
                    break
                self._trozo(anio, mes, obras[i:i + self._n])
        except Exception:                           # noqa: BLE001
            logger.warning("[propuestas] propuestas del mes %02d/%s "
                           "paradas: el transfer no responde o falla; se "
                           "relanzan con el próximo cuadrante o escritura",
                           mes, anio, exc_info=True)
        finally:
            self._desencolar(pendientes)

    def _trozo(self, anio: int, mes: int,
               obras: list[tuple[int, list[dict]]]) -> None:
        r = self._transfer.propuesta_lote([
            {"empresa": self._empresa, "obra": ps[0]["obra"], "ano": anio,
             "mes": mes, "lineas": [p["linea"] for p in ps]}
            for _, ps in obras])
        sin: dict[Clave, str | None] = {}
        sin_sub: dict[ClaveSubfila, str | None] = {}
        with self._uow() as uow:
            for (obra_ide, ps), entrada in zip(obras, r["obras"]):
                ok = bool(entrada.get("ok"))
                for p in ps:
                    clave_t = p["linea"]["clave"]
                    if p["clave"] is not None:
                        prop = (entrada.get("propuestas") or {}).get(
                            clave_t) if ok else None
                        if prop is None or not es_metodo_de_propuesta(
                                prop.get("metodo")):
                            # F-074 (R13): con el motivo del transfer o el
                            # error de la obra.
                            sin[p["clave"]] = _motivo(
                                entrada, (entrada.get("motivos") or {})
                                .get(clave_t))
                        else:
                            _, trabajador, obra = p["clave"]
                            uow.asignaciones.guardar_propuesta(
                                p["clave"][0], trabajador, (obra, False),
                                prop, solo_si_vacia=True)
                    # F-044 (R9): las subfilas de la línea.
                    de_linea = ((entrada.get("vinculados") or {}).get(clave_t)
                                or {}) if ok else {}
                    motivos_sub = ((entrada.get("motivos_vinculados") or {})
                                   .get(clave_t) or {})
                    for c in p["subfilas"]:
                        periodo_id, trabajador, obra, pv, vid = c
                        prop = de_linea.get(str(vid))
                        if prop is None or not es_metodo_de_propuesta_vinculado(
                                prop.get("metodo")):
                            sin_sub[c] = _motivo(entrada,
                                                 motivos_sub.get(str(vid)))
                            continue
                        uow.asignaciones.guardar_propuesta_vinculado(
                            periodo_id, trabajador, (obra, pv), vid, prop,
                            solo_si_vacia=True)
            uow.commit()
        with self._lock:
            self._sin_propuesta.update(sin)
            self._sin_propuesta_sub.update(sin_sub)

    # ------------------------------------------------------------- #
    def estado(self, uow: UnitOfWork, anio: int, mes: int) -> dict[str, Any]:
        """R35: `{en_curso, lineas, pendientes}`: las automáticas con
        propuesta guardada del periodo y (F-057) las que siguen en la cola,
        de la misma foto que `en_curso`. Solo lee. F-074 (R13, R14): y, solo
        si hay alguna, `no_encontradas` (con su motivo),
        `subfilas_pendientes` y `subfilas_no_encontradas`."""
        periodo_id, _ = _periodo_o_error(uow, anio, mes)
        en_curso, marcas = self._foto(periodo_id)
        pendientes = marcas.pendientes
        por_trabajador = uow.asignaciones.lineas_del_periodo(periodo_id)
        lineas = [
            {"trabajador_ide": ide, "obra_ide": ln.obra_ide,
             "es_postventa": ln.es_postventa,
             "propuesta_cod": ln.propuesta_cod,
             "propuesta_res": ln.propuesta_res,
             "propuesta_metodo": ln.propuesta_metodo}
            for ide, lns in sorted(por_trabajador.items())
            for ln in lns
            if ln.propuesta_ide is not None and ln.partida_ide is None]
        # F-044 (R9): las subfilas automáticas con propuesta guardada; la
        # clave solo sale si hay alguna (sin vinculados, la de siempre).
        subfilas = [
            {"trabajador_ide": ide, "obra_ide": ln.obra_ide,
             "es_postventa": ln.es_postventa,
             "vinculado_ide": v.vinculado_ide,
             "propuesta_cod": v.propuesta_cod,
             "propuesta_res": v.propuesta_res,
             "propuesta_metodo": v.propuesta_metodo}
            for ide, lns in sorted(por_trabajador.items())
            for ln in lns for v in ln.vinculados
            if v.propuesta_ide is not None and v.partida_ide is None]
        return {"en_curso": en_curso, "lineas": lineas,
                "pendientes": [
                    {"trabajador_ide": t, "obra_ide": o, "es_postventa": pv}
                    for t, o, pv in sorted(pendientes)],
                **({"subfilas": subfilas} if subfilas else {}),
                **_listas_de_marcas(marcas)}


def _motivo(entrada: dict, motivo: str | None) -> str | None:
    """F-074 (R13): el motivo de una línea o subfila sin propuesta: el que
    manda el transfer o, si su obra vuelve `{ok: false}`, su error."""
    if not entrada.get("ok"):
        return entrada.get("error") or motivo
    return motivo


def _listas_de_marcas(marcas: Marcas) -> dict[str, Any]:
    """F-074 (R13, R14): las listas de `estado()`, solo las que tienen
    alguna (sin ninguna, la respuesta de siempre)."""
    out: dict[str, Any] = {}
    if marcas.no_encontradas:
        out["no_encontradas"] = [
            {"trabajador_ide": t, "obra_ide": o, "es_postventa": pv,
             "motivo": m}
            for (t, o, pv), m in sorted(marcas.no_encontradas.items())]
    if marcas.subfilas_pendientes:
        out["subfilas_pendientes"] = [
            {"trabajador_ide": t, "obra_ide": o, "es_postventa": pv,
             "vinculado_ide": vid}
            for t, o, pv, vid in sorted(marcas.subfilas_pendientes)]
    if marcas.subfilas_no_encontradas:
        out["subfilas_no_encontradas"] = [
            {"trabajador_ide": t, "obra_ide": o, "es_postventa": pv,
             "vinculado_ide": vid, "motivo": m}
            for (t, o, pv, vid), m
            in sorted(marcas.subfilas_no_encontradas.items())]
    return out
