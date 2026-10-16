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
- Estado en memoria de UNA réplica (ARCHITECTURE «Topología»).
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterable
from typing import Any

from domain.models import EstadoPeriodo
from domain.ports import UnitOfWork

from application.registro_sigrid import es_metodo_de_propuesta
from application.use_cases import _periodo_o_error

logger = logging.getLogger(__name__)

#: (periodo_id, trabajador_ide, obra_ide): una línea de obra normal.
Clave = tuple[int, int, int]


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
        self._sin_propuesta: set[Clave] = set()

    # ------------------------------------------------------------- #
    def en_curso(self, periodo_id: int) -> bool:
        """¿Alguna línea del periodo en cola o en marcha? (R30)."""
        with self._lock:
            return any(c[0] == periodo_id for c in self._en_cola)

    def cerrar(self) -> None:
        """Parada de la api (T17b, O5 de la review): cancela lo encolado y
        no espera al trozo en marcha; lo cortado se relanza con el próximo
        cuadrante o escritura, como un transfer caído (R33)."""
        self._ejecutor.shutdown(wait=False, cancel_futures=True)

    def olvidar(self) -> None:
        """Vacía la memoria de «sin propuesta» (R32: tras un sync)."""
        with self._lock:
            self._sin_propuesta.clear()

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
        try:
            return self._lanzar(anio, mes, trabajadores)
        except Exception:                           # noqa: BLE001
            logger.exception("[propuestas] no se pudo encolar %02d/%s",
                             mes, anio)
            return False

    def _lanzar(self, anio, mes, trabajadores) -> bool:
        solo = None if trabajadores is None else set(trabajadores)
        with self._uow() as uow:
            r = uow.periodos.obtener(anio, mes)
            if r is None or r[1].estado is not EstadoPeriodo.ABIERTO:
                return False
            periodo_id = r[0]
            pendientes = []
            for ide, lineas in sorted(
                    uow.asignaciones.lineas_del_periodo(periodo_id).items()):
                if solo is not None and ide not in solo:
                    continue
                for ln in lineas:
                    if ln.es_postventa or ln.partida_fija \
                            or ln.partida_ide is not None \
                            or ln.propuesta_ide is not None:
                        continue
                    t = uow.trabajadores.obtener(ide)
                    pendientes.append({
                        "clave": (periodo_id, ide, ln.obra_ide),
                        "obra": {"ide": ln.obra_ide, "codigo": ln.cod,
                                 "nombre": ln.descripcion},
                        "linea": {"clave": str(ide), "recurso_ide": ide,
                                  "nombre": t.nombre if t else None,
                                  "categoria": t.categoria if t else None,
                                  "es_postventa": False}})
        with self._lock:
            nuevas = [p for p in pendientes
                      if p["clave"] not in self._en_cola
                      and p["clave"] not in self._sin_propuesta]
            self._en_cola.update(p["clave"] for p in nuevas)
        if nuevas:
            try:
                self._ejecutor.submit(self._calcular, anio, mes, nuevas)
            except Exception:
                with self._lock:
                    self._en_cola.difference_update(p["clave"]
                                                    for p in nuevas)
                raise
        return self.en_curso(periodo_id)

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
                self._trozo(anio, mes, obras[i:i + self._n])
        except Exception:                           # noqa: BLE001
            logger.warning("[propuestas] propuestas del mes %02d/%s "
                           "paradas: el transfer no responde o falla; se "
                           "relanzan con el próximo cuadrante o escritura",
                           mes, anio, exc_info=True)
        finally:
            with self._lock:
                self._en_cola.difference_update(p["clave"]
                                                for p in pendientes)

    def _trozo(self, anio: int, mes: int,
               obras: list[tuple[int, list[dict]]]) -> None:
        r = self._transfer.propuesta_lote([
            {"empresa": self._empresa, "obra": ps[0]["obra"], "ano": anio,
             "mes": mes, "lineas": [p["linea"] for p in ps]}
            for _, ps in obras])
        sin: list[Clave] = []
        with self._uow() as uow:
            for (obra_ide, ps), entrada in zip(obras, r["obras"]):
                for p in ps:
                    prop = (entrada.get("propuestas") or {}).get(
                        p["linea"]["clave"]) if entrada.get("ok") else None
                    if prop is None or not es_metodo_de_propuesta(
                            prop.get("metodo")):
                        sin.append(p["clave"])
                        continue
                    _, trabajador, obra = p["clave"]
                    uow.asignaciones.guardar_propuesta(
                        p["clave"][0], trabajador, (obra, False), prop,
                        solo_si_vacia=True)
            uow.commit()
        with self._lock:
            self._sin_propuesta.update(sin)

    # ------------------------------------------------------------- #
    def estado(self, uow: UnitOfWork, anio: int, mes: int) -> dict[str, Any]:
        """R35: `{en_curso, lineas}`: las automáticas con propuesta guardada
        del periodo. Solo lee."""
        periodo_id, _ = _periodo_o_error(uow, anio, mes)
        lineas = [
            {"trabajador_ide": ide, "obra_ide": ln.obra_ide,
             "es_postventa": ln.es_postventa,
             "propuesta_cod": ln.propuesta_cod,
             "propuesta_res": ln.propuesta_res,
             "propuesta_metodo": ln.propuesta_metodo}
            for ide, lns in sorted(
                uow.asignaciones.lineas_del_periodo(periodo_id).items())
            for ln in lns
            if ln.propuesta_ide is not None and ln.partida_ide is None]
        return {"en_curso": self.en_curso(periodo_id), "lineas": lineas}
