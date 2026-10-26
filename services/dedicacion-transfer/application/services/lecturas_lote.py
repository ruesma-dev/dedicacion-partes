# application/services/lecturas_lote.py
"""Lecturas de Sigrid de UN lote de peticiones (F-055, R20-R24; design §2
y §5.2).

`LecturasDelLote` se pone delante del cliente de Sigrid y tiene sus mismos
métodos de lectura, así que el pipeline de registro no cambia: un
`RegistroPipeline(cliente=memoria)` por obra.

- `precargar` lee AGRUPADO lo que van a pedir las obras del lote, en rondas
  de lecturas independientes en paralelo (hasta `limite` a la vez):
  A) obras por `ide`, obras por código (origen, pruebas, postventa, VAR),
  horas y lo ya registrado (`synckey` y, F-051, `hmores.ide`); B) partes
  de los periodos, validación de partidas, historial, presupuestos y
  cuentas de partida; C) líneas de esos partes y (F-062) las líneas de
  incidencia en ventana; D) solo con cierres D14, los partes de M−1.
  F-044 (R27, R29): los recursos vinculados de cada línea van en las
  mismas lecturas que su titular (horas, líneas de los partes, `synckey` y
  `hmores.ide`, partidas); las cuentas del presupuesto, una vez por obra y
  solo si alguna subfila las pide.
  Validación e historial no dependen de A: van en B para que una obra con
  elegidas quepa en una tanda de `limite` (4) por ronda (C2).
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
from application.services.rachas import (
    lectura_de_peticion, mes_anterior, obras_de_m1, rachas_de_designados,
)
from application.services.reglas_incidencias import (
    CODIGO_FIN, decidir_incidencia,
)
from application.services.reglas_porcentajes import empresa_de_peticion
from application.services.reglas_vinculados import synckey_vinculado
from domain.models.registro_models import ContextoRachas, ObraEntrada
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
        # F-051 (R15): claves e `ide` pedidos y `({synckey: línea},
        # {ide: línea})` leídos por `lineas_registradas`.
        self._registradas: tuple[set[str], set[int], dict, dict] | None = None
        self._historial: dict[tuple[int, int], tuple[set[int], list]] = {}
        self._partes: dict[tuple[int, int, int], list] = {}
        self._lineas: tuple[set[int], dict] | None = None
        # F-062 (R19): por obra de pruebas (o None), recursos, `ide`,
        # ventana y líneas de incidencia leídas.
        self._ventana: dict[int | None, tuple] = {}

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
    def precargar(self, peticiones: list[tuple], settings) -> None:
        """Rondas A-C (design §2, con validación e historial en B) para
        las peticiones del lote: `(obra, lineas)` o, con incidencias
        (F-030), `(obra, lineas, incidencias)` y (F-062) su contexto,
        `(obra, lineas, incidencias, contexto)`. Ronda D (F-062 R20): los
        partes de M−1 de los cierres D14, solo si los hay."""
        incs = [list(p[2]) if len(p) > 2 else [] for p in peticiones]
        ctxs = [p[3] if len(p) > 3 else None for p in peticiones]
        peticiones = [(p[0], p[1]) for p in peticiones]
        empresas: dict[int, int | None] = {}
        for i, (_, lineas) in enumerate(peticiones):
            try:
                # F-062 (R17): las quitadas también dan la empresa.
                quitadas = ctxs[i].quitadas if ctxs[i] else []
                empresas[i] = empresa_de_peticion(
                    [*lineas, *incs[i], *quitadas])
            except Exception:                       # noqa: BLE001
                empresas[i] = None      # la petición fallará sola
        todas = [l for _, ls in peticiones for l in ls]
        todas_inc = [x for xs in incs for x in xs]
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
        # F-044 (R27): cada vinculado con la línea de su titular.
        vins = [(l, v) for l in todas for v in l.vinculados]
        resides = _ides([*(l.recurso_ide for l in todas),
                         *(v.recurso_ide for _, v in vins)])
        con_inc = resides | _ides(x.recurso_ide for x in todas_inc)
        if con_inc:
            tareas.append(lambda: self._cargar_horas(con_inc))
        claves = {synckey_de(l.registro_id) for l in todas}
        claves |= {synckey_vinculado(l.registro_id, v.recurso_ide)
                   for l, v in vins}
        hmores = _ides([*(l.hmores_ide for l in todas),
                        *(v.hmores_ide for _, v in vins)])
        if claves:
            tareas.append(lambda: self._cargar_registradas(claves, hmores))
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
        periodos = {(int(l.ano), int(l.mes)) for l in [*todas, *todas_inc]}
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
        normales = [l for l in todas
                    if not l.es_postventa and l.var_paride is None]
        parides = _ides(l.paride or l.propuesta_paride for l in normales)
        parides |= _ides(x.paride for x in todas_inc)
        # F-044 (R15): la elegida o la propuesta guardada de cada vinculado
        # de una línea que no va a postventa (ni a VAR: superconjunto).
        parides |= _ides(v.paride or v.propuesta_paride for l, v in vins
                         if not l.es_postventa and l.var_paride is None)
        if parides:
            tareas.append(lambda: self._cargar_validas(parides))
        for (desde, hasta), recursos in self._ventanas(
                peticiones, settings).items():
            tareas.append(self._historial_de(desde, hasta, recursos))
        sin_sub = _ides(
            l.paride or l.propuesta_paride or l.var_paride for l in todas
            if self._sin_subcuenta(l.recurso_ide))
        sin_sub |= _ides(x.paride for x in todas_inc
                         if self._inc_sin_subcuenta(x))
        # F-044 (R12): la del vinculado sin subcuenta, que puede ser la
        # suya o la de su titular (superconjunto; la CI de su tipo, que
        # sale de las cuentas del presupuesto, no se conoce aquí).
        sin_sub |= _ides(p for l, v in vins
                         if self._sin_subcuenta(v.recurso_ide)
                         for p in (v.paride, v.propuesta_paride, l.paride,
                                   l.propuesta_paride, l.var_paride))
        if sin_sub:
            tareas.append(lambda: self._cargar_partidas(sin_sub))
        self._ronda(tareas)

        # --- Ronda C ---
        tareas = []
        hmoides = {int(p.ide) for ps in self._partes.values() for p in ps}
        if hmoides and resides:
            tareas.append(lambda: self._cargar_lineas(hmoides, resides))
        rachas = self._lecturas_rachas(incs, ctxs, peticiones, empresas,
                                       settings)
        por_pruebas: dict[int | None, list] = {}
        for lec, pruebas in rachas.values():
            por_pruebas.setdefault(pruebas, []).append(lec)
        for pruebas, lecturas in por_pruebas.items():
            tareas.append(lambda p=pruebas, x=lecturas:
                          self._cargar_ventana(p, x))
        self._ronda(tareas)

        # --- Ronda D (F-062) ---
        self._ronda(self._partes_m1(rachas, settings))

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
        # F-044 (R27, R29): las horas de TODOS los vinculados del lote, en
        # una lectura; las cuentas del presupuesto, por obra y solo si
        # alguna subfila las pide (`cuentas_del_presupuesto`, una vez).
        vinculados = _ides(v["recurso_ide"] for p in peticiones
                           for l in p["lineas"]
                           for v in l.get("vinculados") or [])
        if vinculados:
            tareas.append(lambda: self._cargar_horas(vinculados))
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

    def _inc_sin_subcuenta(self, inc) -> bool:
        """F-030: ¿alguna de las dos horas de la incidencia se queda sin
        subcuenta del recurso? Acota, como `_sin_subcuenta`, qué cuentas de
        partida se precargan (un superconjunto)."""
        if self._horas is None or not inc.recurso_ide:
            return False
        horas = self._horas[1].get(int(inc.recurso_ide), [])
        return any(h.cod in (inc.codigo, CODIGO_FIN)
                   and not subcuenta_de_linea(horas, h.horide)
                   for h in horas)

    def _lecturas_rachas(self, incs: list[list], ctxs: list, peticiones,
                         empresas: dict, settings) -> dict[int, tuple]:
        """F-062 (R19, R26): por petición, `(LecturaRachas, obride de
        pruebas o None)` de las que leerán las rachas: con alguna
        incidencia que se escribiría (`decidir_incidencia` con las horas ya
        leídas: un superconjunto de las del pipeline), recursos designados
        o quitadas. En pruebas, sin obra de pruebas, la petición fallará
        sola."""
        horas = self._horas[1] if self._horas is not None else {}
        out: dict[int, tuple] = {}
        for i, (_, lineas) in enumerate(peticiones):
            ctx = ctxs[i] or ContextoRachas()
            if empresas[i] is None:
                continue
            escriben = any(a.accion == "escribir" for x in incs[i]
                           for a in decidir_incidencia(x, horas))
            if not (escriben or ctx.cierres_recursos or ctx.quitadas):
                continue
            pruebas = None
            if settings.obra_pruebas_forzar:
                obra = self._ya(("obra_por_codigo", settings.obra_pruebas_cod,
                                 empresas[i]))
                if obra is None:
                    continue
                pruebas = int(obra.ide)
            out[i] = (lectura_de_peticion(
                incs[i], lineas, ctx, int(settings.incidencias_meses_atras)),
                pruebas)
        return out

    def _cargar_ventana(self, pruebas: int | None,
                        lecturas: list) -> None:
        """R19-R20: UNA lectura por obra de pruebas (o ninguna): la unión de
        recursos e `ide` y la ventana que lo cubre todo."""
        recursos = {r for x in lecturas for r in x.recursos}
        ides = {v for x in lecturas for v in x.ides}
        desde = min(x.desde for x in lecturas)
        hasta = max(x.hasta for x in lecturas)
        self._ventana[pruebas] = (recursos, ides, desde, hasta, list(
            self._cli.incidencias_en_ventana(
                sorted(recursos), desde, hasta, obride_pruebas=pruebas,
                ides=sorted(ides))))

    def _partes_m1(self, rachas: dict[int, tuple],
                   settings) -> list[Callable]:
        """Ronda D (R20, D14): los partes de M−1 de las obras de los
        inicios anteriores a M−1 por cerrar de los designados; solo si los
        hay. Se añaden a los del periodo."""
        est = int(settings.est_parte_activo)
        obras: set[int] = set()
        periodos: set[tuple[int, int]] = set()
        for lec, pruebas in rachas.values():
            if not lec.designados:
                continue
            leidas = self.incidencias_en_ventana(
                lec.recursos, lec.desde, lec.hasta, obride_pruebas=pruebas,
                ides=lec.ides)
            de_m1 = obras_de_m1(
                rachas_de_designados(lec.designados, leidas),
                lec.incidencias_mes, lec.ano, lec.mes, est=est,
                obride_pruebas=pruebas)
            if de_m1:
                m1 = mes_anterior(lec.ano * 100 + lec.mes)
                obras |= de_m1
                periodos.add((m1 // 100, m1 % 100))

        def tarea() -> None:
            for k, v in self._cli.partes_de_periodos(
                    sorted(obras), sorted(periodos)).items():
                self._partes.setdefault(k, v)
        return [tarea] if obras else []

    def _cargar_obras(self, ides: set[int]) -> None:
        leidas = self._cli.obras_por_ide(sorted(ides))
        self._obras = {i: leidas.get(i) for i in ides}

    def _cargar_horas(self, resides: set[int]) -> None:
        self._horas = (resides, self._cli.horas_de_recursos(sorted(resides)))

    def _cargar_registradas(self, claves: set[str], ides: set[int]) -> None:
        por_sk, por_ide = self._cli.lineas_registradas(sorted(claves),
                                                       sorted(ides))
        self._registradas = (claves, ides, por_sk, por_ide)

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

    def cuentas_del_presupuesto(self, obra_ide):
        """F-044 (R29): una lectura por obra en todo el lote."""
        return self._una_vez(
            ("cuentas_del_presupuesto", int(obra_ide)),
            lambda: self._cli.cuentas_del_presupuesto(obra_ide))

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
        if self._registradas is not None and pedidas <= self._registradas[0]:
            leidas = self._registradas[2]
            return {k: leidas[k] for k in sorted(pedidas) if k in leidas}
        self._fallo("lineas_por_synckey")
        return self._cli.lineas_por_synckey(claves)

    def lineas_registradas(self, claves, ides):
        pedidas, pedidos = {k for k in claves if k}, _ides(ides)
        r = self._registradas
        if r is not None and pedidas <= r[0] and pedidos <= r[1]:
            return ({k: r[2][k] for k in sorted(pedidas) if k in r[2]},
                    {i: r[3][i] for i in sorted(pedidos) if i in r[3]})
        self._fallo("lineas_registradas")
        return self._cli.lineas_registradas(claves, ides)

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

    def incidencias_en_ventana(self, resides, desde, hasta, *,
                               obride_pruebas=None, ides=()):
        """F-062 (R19): de lo precargado si es la misma obra de pruebas (o
        ninguna), los recursos y los `ide` están dentro y la ventana
        también, con el criterio de la consulta: del recurso, en la ventana
        y `CI*`, o pedida por su `ide`; en el orden leído (`fec`, `ide`)."""
        pedidos, lineas = _ides(resides), _ides(ides)
        clave = None if obride_pruebas is None else int(obride_pruebas)
        c = self._ventana.get(clave)
        if c is not None and pedidos <= c[0] and lineas <= c[1] \
                and c[2] <= int(desde) and int(hasta) <= c[3]:
            return [l for l in c[4]
                    if (l.reside in pedidos
                        and int(desde) <= l.fecha_int <= int(hasta)
                        and (l.hora_codigo or "").startswith("CI"))
                    or l.ide in lineas]
        self._fallo("incidencias_en_ventana")
        return self._cli.incidencias_en_ventana(
            resides, desde, hasta, obride_pruebas=obride_pruebas, ides=ides)

    def partes_de_periodos(self, obrides, periodos):
        """F-062 (R12-R13): de lo precargado (rondas B y D) si están todas
        las claves `(obride, ano, mes)` pedidas."""
        claves = [(o, int(a), int(m)) for o in sorted(_ides(obrides))
                  for a, m in sorted(set(periodos))]
        if all(k in self._partes for k in claves):
            return {k: list(self._partes[k]) for k in claves}
        self._fallo("partes_de_periodos")
        return self._cli.partes_de_periodos(obrides, periodos)

    def escribir(self, statements):
        raise RuntimeError("las lecturas de un lote no escriben en Sigrid")
