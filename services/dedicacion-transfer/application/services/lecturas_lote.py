# application/services/lecturas_lote.py
"""Lecturas de Sigrid de UN lote de peticiones (F-055, R20-R24; design §2
y §5.2).

`LecturasDelLote` se pone delante del cliente de Sigrid y tiene sus mismos
métodos de lectura, así que el pipeline de registro no cambia: un
`RegistroPipeline(cliente=memoria)` por obra.

- `precargar` lee AGRUPADO lo que van a pedir las obras del lote, en rondas
  de lecturas independientes en paralelo (hasta `limite` a la vez):
  A) obras por `ide`, obras por código (origen, pruebas, postventa, VAR),
  horas, `synckey`, validación de partidas e historial; B) partes de los
  periodos, presupuestos y cuentas de partida; C) líneas de esos partes.
- Una lectura del pipeline se responde de lo precargado SOLO si la consulta
  está entera dentro (los mismos `ide`, un subconjunto de recursos, la
  misma ventana…); si no, va al cliente real y se apunta un fallo de
  memoria (log y contador). Nunca se responde vacío ni con datos de otra
  consulta (R22).
- Las lecturas que se comparten por clave (obra por código, presupuesto,
  cuentas de un centro, siguiente código de parte) van una sola vez: un
  solo vuelo por clave, y quien llega después espera ese mismo resultado o
  esa misma excepción.
- La memoria vive lo que vive el lote (D4: nada entre peticiones) y no
  escribe: `escribir` lanza `RuntimeError`.
- Una lectura agrupada que falla hace fallar `precargar` (R24: dependen de
  ella todas las obras del lote). Las compartidas que fallan en la ronda no
  la paran: el fallo vuelve a la obra que las pida, como en suelto.
"""
from __future__ import annotations

import contextvars
import logging
import threading
from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor

from application.services.cuenta_analitica import subcuenta_de_linea
from application.services.propuesta_partida import ventana
from application.services.reglas_porcentajes import empresa_de_peticion
from domain.models.registro_models import LineaEntrada, ObraEntrada
from infrastructure.sigrid.sigrid_write_client import synckey_de

logger = logging.getLogger(__name__)


def _ides(valores: Iterable) -> set[int]:
    return {int(v) for v in valores if v}


class LecturasDelLote:
    """Memoria de las lecturas de un lote (ver el docstring del módulo)."""

    def __init__(self, cliente, limite: int) -> None:
        self._cli = cliente
        self._limite = int(limite)
        self._lock = threading.Lock()
        self._vuelos: dict[tuple, Future] = {}
        self.fallos_de_memoria: dict[str, int] = {}
        # Lo precargado: lo consultado (para saber si una consulta está
        # dentro) y lo leído.
        self._obras: dict[int, ObraEntrada | None] = {}
        self._horas: tuple[set[int], dict] | None = None
        self._validas: tuple[set[int], dict] | None = None
        self._partidas: tuple[set[int], dict] | None = None
        self._synckeys: tuple[set[str], dict] | None = None
        self._historial: dict[tuple[int, int], tuple[set[int], list]] = {}
        self._partes: dict[tuple[int, int, int], list] = {}
        self._lineas: tuple[set[int], dict] | None = None

    # ------------------------------------------------------------ #
    #  Utilidades
    # ------------------------------------------------------------ #
    def _fallo(self, nombre: str) -> None:
        with self._lock:
            self.fallos_de_memoria[nombre] = \
                self.fallos_de_memoria.get(nombre, 0) + 1
        logger.info("[lote] fallo de memoria %s: se lee de Sigrid", nombre)

    def _una_vez(self, clave: tuple, leer: Callable):
        """Un solo vuelo por clave: el primero lee; los demás esperan su
        resultado o su excepción."""
        with self._lock:
            futuro = self._vuelos.get(clave)
            primero = futuro is None
            if primero:
                futuro = Future()
                self._vuelos[clave] = futuro
        if primero:
            try:
                futuro.set_result(leer())
            except BaseException as exc:            # noqa: BLE001
                futuro.set_exception(exc)
        return futuro.result()

    def _ya(self, clave: tuple):
        """Resultado de un vuelo terminado, o None si no lo hay o falló."""
        futuro = self._vuelos.get(clave)
        if futuro is None or futuro.exception() is not None:
            return None
        return futuro.result()

    def _ronda(self, tareas: list[Callable]) -> None:
        """Las tareas en paralelo (hasta `limite`), cada una con una copia
        del contexto (la medición de F-055 R1). La primera excepción, en el
        orden de las tareas, sube (R24)."""
        if not tareas:
            return
        with ThreadPoolExecutor(max_workers=self._limite) as pool:
            futuros = [pool.submit(contextvars.copy_context().run, t)
                       for t in tareas]
        for f in futuros:
            f.result()

    def _tolerante(self, clave: tuple, leer: Callable) -> Callable:
        """Tarea de ronda para una lectura compartida: su fallo no para la
        ronda; vuelve a la obra que la pida (como en suelto)."""
        def tarea() -> None:
            try:
                self._una_vez(clave, leer)
            except Exception:                       # noqa: BLE001
                pass
        return tarea

    # ------------------------------------------------------------ #
    #  Precarga
    # ------------------------------------------------------------ #
    def precargar(self, peticiones: list[tuple[ObraEntrada,
                                               list[LineaEntrada]]],
                  settings) -> None:
        """Rondas A-C de design §2 para las peticiones del lote."""
        empresas: dict[int, int | None] = {}
        for i, (_, lineas) in enumerate(peticiones):
            try:
                empresas[i] = empresa_de_peticion(lineas)
            except Exception:                       # noqa: BLE001
                empresas[i] = None      # la petición fallará sola
        todas = [l for _, ls in peticiones for l in ls]
        con_empresa = sorted({e for e in empresas.values() if e})

        # --- Ronda A ---
        tareas: list[Callable] = []
        compartidas: set[str] = set()       # códigos de postventa y VAR
        ides = _ides(o.ide for o, _ in peticiones)
        if ides:
            tareas.append(lambda: self._cargar_obras(ides))
        for i, (o, _) in enumerate(peticiones):
            if not o.ide and o.codigo and empresas[i]:
                tareas.append(self._codigo(o.codigo, empresas[i]))
        for emp in con_empresa:
            if settings.obra_pruebas_forzar:
                tareas.append(self._codigo(settings.obra_pruebas_cod, emp))
            if settings.postventa_registrar and any(
                    l.es_postventa for i, (_, ls) in enumerate(peticiones)
                    if empresas[i] == emp for l in ls):
                tareas.append(self._codigo(settings.postventa_obra_cod, emp))
                compartidas.add(settings.postventa_obra_cod)
            if any(l.var_paride is not None
                   for i, (_, ls) in enumerate(peticiones)
                   if empresas[i] == emp for l in ls):
                var = (settings.var_obra_cod or "").strip()
                if var:
                    tareas.append(self._codigo(var, emp))
                    compartidas.add(var)
        resides = _ides(l.recurso_ide for l in todas)
        if resides:
            tareas.append(lambda: self._cargar_horas(resides))
        claves = {synckey_de(l.registro_id) for l in todas}
        if claves:
            tareas.append(lambda: self._cargar_synckeys(claves))
        normales = [l for l in todas
                    if not l.es_postventa and l.var_paride is None]
        parides = _ides(l.paride or l.propuesta_paride for l in normales)
        if parides:
            tareas.append(lambda: self._cargar_validas(parides))
        for (desde, hasta), recursos in self._ventanas(
                peticiones, settings).items():
            tareas.append(self._historial_de(desde, hasta, recursos))
        self._ronda(tareas)

        # --- Ronda B ---
        tareas = []
        destinos: set[int] = set()
        origenes: dict[int, int] = {}
        for i, (o, ls) in enumerate(peticiones):
            emp = empresas[i]
            origen = (self._obras.get(int(o.ide)) if o.ide else
                      self._ya(("obra_por_codigo", o.codigo, emp)))
            if origen is not None:
                origenes[i] = int(origen.ide)
            if emp is None:
                continue
            if settings.obra_pruebas_forzar:
                pruebas = self._ya(("obra_por_codigo",
                                    settings.obra_pruebas_cod, emp))
                if pruebas is not None:
                    destinos.add(int(pruebas.ide))
                continue
            if i in origenes:
                destinos.add(origenes[i])
            pv = self._ya(("obra_por_codigo", settings.postventa_obra_cod,
                           emp))
            if pv is not None and any(l.es_postventa for l in ls):
                destinos.add(int(pv.ide))
        periodos = {(int(l.ano), int(l.mes)) for l in todas}
        if destinos and periodos:
            tareas.append(lambda: self._cargar_partes(destinos, periodos))
        presupuestos: set[int] = set()
        for cod in sorted(compartidas):             # postventa y VAR
            for emp in con_empresa:
                obra = self._ya(("obra_por_codigo", cod, emp))
                if obra is not None:
                    presupuestos.add(int(obra.ide))
        for i, (_, ls) in enumerate(peticiones):
            if i in origenes and any(
                    not l.es_postventa and l.var_paride is None
                    and not l.paride and not l.propuesta_paride for l in ls):
                presupuestos.add(origenes[i])       # con pendientes
        for obride in sorted(presupuestos):
            tareas.append(self._tolerante(
                ("capitulos_de_obra", obride),
                lambda o=obride: self._cli.capitulos_de_obra(o)))
        sin_sub = _ides(
            l.paride or l.propuesta_paride or l.var_paride for l in todas
            if self._sin_subcuenta(l.recurso_ide))
        if sin_sub:
            tareas.append(lambda: self._cargar_partidas(sin_sub))
        self._ronda(tareas)

        # --- Ronda C ---
        hmoides = {int(p.ide) for ps in self._partes.values() for p in ps}
        if hmoides and resides:
            self._ronda([lambda: self._cargar_lineas(hmoides, resides)])

    def precargar_propuestas(self, peticiones: list[dict], settings) -> None:
        """Design §2.1 (R34): A) obras e historial de TODOS los recursos de
        las líneas de obra normal (misma ventana: el lote es de un periodo)
        y B) el presupuesto de cada obra, hasta `limite` a la vez. Cada
        petición: `{empresa, obra, ano, mes, lineas}`, como
        `RegistroPipeline.proponer`."""
        tareas: list[Callable] = []
        ides = _ides(p["obra"].ide for p in peticiones)
        if ides:
            tareas.append(lambda: self._cargar_obras(ides))
        for p in peticiones:
            o = p["obra"]
            if not o.ide and o.codigo:
                tareas.append(self._codigo(o.codigo, p["empresa"]))
        por_ventana: dict[tuple[int, int], set[int]] = {}
        for p in peticiones:
            recursos = _ides(l["recurso_ide"] for l in p["lineas"]
                             if not l["es_postventa"])
            if recursos:
                clave = ventana(p["ano"], p["mes"],
                                settings.propuesta_meses_atras)
                por_ventana.setdefault(clave, set()).update(recursos)
        for (desde, hasta), recursos in por_ventana.items():
            tareas.append(self._historial_de(desde, hasta, recursos))
        self._ronda(tareas)
        origenes = set()
        for p in peticiones:
            o = p["obra"]
            obra = (self._obras.get(int(o.ide)) if o.ide else
                    self._ya(("obra_por_codigo", o.codigo,
                              int(p["empresa"]))))
            if obra is not None:
                origenes.add(int(obra.ide))
        self._ronda([self._tolerante(
            ("capitulos_de_obra", obride),
            lambda o=obride: self._cli.capitulos_de_obra(o))
            for obride in sorted(origenes)])

    def _codigo(self, cod: str, empresa: int) -> Callable:
        return self._tolerante(
            ("obra_por_codigo", cod, int(empresa)),
            lambda: self._cli.obra_por_codigo(cod, int(empresa)))

    def _ventanas(self, peticiones, settings) -> dict[tuple, set[int]]:
        """Recursos de las líneas automáticas de cada petición con alguna
        sin propuesta guardada (pendiente segura), por ventana del
        historial (la del pipeline: la que acaba en su periodo)."""
        out: dict[tuple[int, int], set[int]] = {}
        for _, ls in peticiones:
            auto = [l for l in ls if not l.es_postventa
                    and l.var_paride is None and not l.paride]
            if not any(not l.propuesta_paride for l in auto):
                continue
            ano, mes = max((l.ano, l.mes) for l in auto)
            clave = ventana(ano, mes, settings.propuesta_meses_atras)
            out.setdefault(clave, set()).update(
                _ides(l.recurso_ide for l in auto))
        return {k: v for k, v in out.items() if v}

    def _sin_subcuenta(self, recurso) -> bool:
        """¿Alguna hora mensual del recurso se queda sin subcuenta? Solo
        acota qué cuentas de partida se precargan (un superconjunto)."""
        if self._horas is None or not recurso:
            return False
        horas = self._horas[1].get(int(recurso), [])
        return any(h.es_mensual and not subcuenta_de_linea(horas, h.horide)
                   for h in horas)

    def _cargar_obras(self, ides: set[int]) -> None:
        leidas = self._cli.obras_por_ide(sorted(ides))
        self._obras = {i: leidas.get(i) for i in ides}

    def _cargar_horas(self, resides: set[int]) -> None:
        self._horas = (resides, self._cli.horas_de_recursos(sorted(resides)))

    def _cargar_synckeys(self, claves: set[str]) -> None:
        self._synckeys = (claves,
                          self._cli.lineas_por_synckey(sorted(claves)))

    def _cargar_validas(self, parides: set[int]) -> None:
        self._validas = (parides,
                         self._cli.validar_partidas(sorted(parides)))

    def _cargar_partidas(self, parides: set[int]) -> None:
        self._partidas = (parides,
                          self._cli.partidas_de_lineas(sorted(parides)))

    def _historial_de(self, desde: int, hasta: int,
                      recursos: set[int]) -> Callable:
        def tarea() -> None:
            self._historial[(desde, hasta)] = (recursos, list(
                self._cli.historial_partidas(sorted(recursos), desde,
                                             hasta)))
        return tarea

    def _cargar_partes(self, obrides: set[int],
                       periodos: set[tuple[int, int]]) -> None:
        self._partes = dict(self._cli.partes_de_periodos(sorted(obrides),
                                                         sorted(periodos)))

    def _cargar_lineas(self, hmoides: set[int], resides: set[int]) -> None:
        self._lineas = (resides, self._cli.lineas_de_partes(
            sorted(hmoides), sorted(resides)))

    # ------------------------------------------------------------ #
    #  Las lecturas del pipeline
    # ------------------------------------------------------------ #
    def obra_por_ide(self, ide):
        if int(ide) in self._obras:
            return self._obras[int(ide)]
        self._fallo("obra_por_ide")
        return self._cli.obra_por_ide(ide)

    def obra_por_codigo(self, cod, empresa):
        return self._una_vez(("obra_por_codigo", cod, int(empresa)),
                             lambda: self._cli.obra_por_codigo(cod, empresa))

    def capitulos_de_obra(self, obride):
        return self._una_vez(("capitulos_de_obra", int(obride)),
                             lambda: self._cli.capitulos_de_obra(obride))

    def cuentas_de_centro(self, cenide, empresa, subcuentas):
        subs = tuple(sorted({s for s in subcuentas if s}))
        return self._una_vez(
            ("cuentas_de_centro", int(cenide), int(empresa), subs),
            lambda: self._cli.cuentas_de_centro(cenide, empresa, subs))

    def siguiente_cod_pt(self, ano, empresa):
        return self._una_vez(
            ("siguiente_cod_pt", int(ano), int(empresa)),
            lambda: self._cli.siguiente_cod_pt(ano, empresa))

    def horas_de_recursos(self, resides):
        pedidas = _ides(resides)
        if self._horas is not None and pedidas <= self._horas[0]:
            leidas = self._horas[1]
            return {r: leidas[r] for r in sorted(pedidas) if r in leidas}
        self._fallo("horas_de_recursos")
        return self._cli.horas_de_recursos(resides)

    def validar_partidas(self, parides):
        pedidas = _ides(parides)
        if self._validas is not None and pedidas <= self._validas[0]:
            leidas = self._validas[1]
            return {p: leidas[p] for p in sorted(pedidas) if p in leidas}
        self._fallo("validar_partidas")
        return self._cli.validar_partidas(parides)

    def partidas_de_lineas(self, parides):
        pedidas = _ides(parides)
        if self._partidas is not None and pedidas <= self._partidas[0]:
            leidas = self._partidas[1]
            return {p: leidas[p] for p in sorted(pedidas) if p in leidas}
        self._fallo("partidas_de_lineas")
        return self._cli.partidas_de_lineas(parides)

    def lineas_por_synckey(self, claves):
        pedidas = {k for k in claves if k}
        if self._synckeys is not None and pedidas <= self._synckeys[0]:
            leidas = self._synckeys[1]
            return {k: leidas[k] for k in sorted(pedidas) if k in leidas}
        self._fallo("lineas_por_synckey")
        return self._cli.lineas_por_synckey(claves)

    def historial_partidas(self, resides, desde, hasta):
        pedidos = _ides(resides)
        cargado = self._historial.get((int(desde), int(hasta)))
        if cargado is not None and pedidos <= cargado[0]:
            return [l for l in cargado[1] if l.reside in pedidos]
        self._fallo("historial_partidas")
        return self._cli.historial_partidas(resides, desde, hasta)

    def partes_del_periodo(self, obra_ide, ano, mes):
        clave = (int(obra_ide), int(ano), int(mes))
        if clave in self._partes:
            return list(self._partes[clave])
        self._fallo("partes_del_periodo")
        return self._cli.partes_del_periodo(obra_ide, ano, mes)

    def lineas_del_parte(self, hmoide, resides):
        pedidos = _ides(resides)
        if self._lineas is not None and int(hmoide) in self._lineas[1] \
                and pedidos <= self._lineas[0]:
            return [l for l in self._lineas[1][int(hmoide)]
                    if l.reside in pedidos]
        self._fallo("lineas_del_parte")
        return self._cli.lineas_del_parte(hmoide, resides)

    def escribir(self, statements):
        raise RuntimeError("las lecturas de un lote no escriben en Sigrid")
