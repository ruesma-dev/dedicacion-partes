# tests/test_f055_propuestas_mes.py
"""F-055 · T12: las propuestas del mes en segundo plano (R29-R33, R35).

`PropuestasDelMes` con un ejecutor SÍNCRONO (corre la tarea al encolarla) o
RETENIDO (la guarda hasta que el test la suelta), una UnitOfWork en memoria
y un transfer falso. Rutas con `TestClient`: el cuadrante publica
`propuestas_en_curso`, `/sync` con éxito olvida y relanza los abiertos y
`GET …/propuestas` devuelve `{en_curso, lineas}`. Sin red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from application.propuestas_mes import PropuestasDelMes
from domain.errors import PropuestaNoDisponible
from domain.models import EstadoPeriodo, Periodo

from tests.test_f024_cuadrante_empresa import ANIO, MES, P_ACT, _Periodos
from tests.test_f024_rutas_empresa import (  # noqa: F401  (fixture `api`)
    _PropuestasFalsas,
    api,
)
from tests.test_f055_propuesta_guardada import (
    DEL_TRANSFER,
    PR,
    _lp,
    _uow,
)
from tests.test_f050_partida_linea import P


class _PeriodosR29(_Periodos):
    def __init__(self, estado=EstadoPeriodo.ABIERTO) -> None:
        self.estado = estado

    def obtener(self, anio, mes):
        r = super().obtener(anio, mes)
        return None if r is None else (r[0], Periodo(anio, mes, self.estado))

    def listar(self):
        return [Periodo(ANIO, MES, self.estado), Periodo(ANIO, MES - 1,
                                                         EstadoPeriodo.CERRADO)]


def _uow_cm(lineas, estado=EstadoPeriodo.ABIERTO):
    uow = _uow(actual=lineas)
    uow.periodos = _PeriodosR29(estado)
    uow.commits = 0

    def commit():
        uow.commits += 1
    uow.commit = commit
    uow.__class__ = type("_UowCM", (uow.__class__,), {
        "__enter__": lambda self: self, "__exit__": lambda self, *e: None})
    return uow


class _Sincrono:
    def __init__(self) -> None:
        self.tareas = 0

    def submit(self, fn, *a):
        self.tareas += 1
        fn(*a)


class _Retenido:
    def __init__(self) -> None:
        self.pendientes: list = []

    def submit(self, fn, *a):
        self.pendientes.append((fn, a))

    def soltar(self) -> None:
        while self.pendientes:
            fn, a = self.pendientes.pop(0)
            fn(*a)


class _Transfer:
    """Contesta por obra: `propuestas[obra]` o `{ok: false}` si está en
    `fallan`; `caido` hace que la llamada lance."""

    def __init__(self, propuestas=None, fallan=(), caido=False) -> None:
        self.propuestas = propuestas or {}
        self.fallan = set(fallan)
        self.caido = caido
        self.llamadas: list[list[dict]] = []

    def propuesta_lote(self, peticiones):
        self.llamadas.append(peticiones)
        if self.caido:
            raise PropuestaNoDisponible("propuesta de partidas no "
                                        "disponible: transfer inaccesible")
        obras = []
        for p in peticiones:
            o = p["obra"]["ide"]
            if o in self.fallan:
                obras.append({"ok": False, "error": "otra empresa"})
                continue
            obras.append({"ok": True, "propuestas": {
                l["clave"]: self.propuestas.get((int(l["clave"]), o))
                for l in p["lineas"]}})
        return {"ok": True, "obras": obras}


def _pm(uow, transfer, ejecutor=None, n=10):
    return PropuestasDelMes(lambda: uow, transfer, ejecutor or _Sincrono(),
                            obras_por_llamada=n, empresa_obras=1)


def _prop(uow, ide, obra):
    ln = next(l for l in uow.lineas[P_ACT][ide] if l.obra_ide == obra)
    return ln.propuesta_ide


# ======================= R29 · qué se encola ============================= #
def test_f055_r29_solo_pendientes_y_las_guarda():
    uow = _uow_cm({14: [_lp(100, "40"), _lp(101, "30", **P),
                        _lp(102, "20", **PR), _lp(100, "10", pv=True)],
                   10: [_lp(900, "100", partida_fija=True)]})
    t = _Transfer({(14, 100): DEL_TRANSFER})
    assert _pm(uow, t).lanzar(ANIO, MES) is False
    [[peticion]] = t.llamadas
    assert peticion == {
        "empresa": 1, "obra": {"ide": 100, "codigo": "0100",
                               "nombre": "OBRA 100"},
        "ano": ANIO, "mes": MES,
        "lineas": [{"clave": "14", "recurso_ide": 14, "nombre": "Eva",
                    "categoria": "Encargado", "es_postventa": False}]}
    assert _prop(uow, 14, 100) == 80002 and uow.commits == 1


def test_f055_r29_con_trabajadores_solo_los_suyos():
    uow = _uow_cm({14: [_lp(100, "100")], 10: [_lp(101, "100")]})
    t = _Transfer()
    _pm(uow, t).lanzar(ANIO, MES, [10])
    assert [p["lineas"][0]["clave"] for p in t.llamadas[0]] == ["10"]


@pytest.mark.parametrize("anio, mes, estado", [
    (ANIO, MES, EstadoPeriodo.CERRADO), (2030, 1, EstadoPeriodo.ABIERTO)],
    ids=["cerrado", "inexistente"])
def test_f055_r29_periodo_cerrado_o_inexistente_no_lanza(anio, mes, estado):
    uow = _uow_cm({14: [_lp(100, "100")]}, estado)
    t, ej = _Transfer(), _Sincrono()
    assert _pm(uow, t, ej).lanzar(anio, mes) is False
    assert ej.tareas == 0 and t.llamadas == []


def test_f055_r29_nada_pendiente_falso_y_sin_tarea():
    uow = _uow_cm({14: [_lp(100, "100", **PR)]})
    ej = _Sincrono()
    assert _pm(uow, _Transfer(), ej).lanzar(ANIO, MES) is False
    assert ej.tareas == 0


# ===================== R30 · cola, en curso y orden ====================== #
def test_f055_r30_en_curso_mientras_quede_alguna_y_no_se_reencola():
    uow = _uow_cm({14: [_lp(100, "100")], 10: [_lp(101, "100")]})
    t, ej = _Transfer(), _Retenido()
    pm = _pm(uow, t, ej)
    assert pm.lanzar(ANIO, MES, [14]) is True
    assert pm.lanzar(ANIO, MES, [14]) is True       # ya en cola
    assert len(ej.pendientes) == 1
    assert pm.lanzar(ANIO, MES) is True             # solo entra la de 10
    assert len(ej.pendientes) == 2
    assert pm.en_curso(P_ACT) is True and pm.en_curso(99) is False
    ej.soltar()
    assert pm.en_curso(P_ACT) is False
    assert [[p["lineas"][0]["clave"] for p in ll] for ll in t.llamadas] == [
        ["14"], ["10"]]                              # orden de llegada


# ================== R31 · trozos y sin pisar ============================= #
def test_f055_r31_trozos_de_10_obras_una_llamada_cada_uno():
    lineas = {14: [_lp(100, "50"), _lp(101, "50")]}
    lineas.update({t: [_lp(100 + i % 2, "100")]
                   for i, t in enumerate((10, 11, 12, 13, 15))})
    uow = _uow_cm(lineas)
    t = _Transfer()
    _pm(uow, t, n=1).lanzar(ANIO, MES)
    assert [len(ll) for ll in t.llamadas] == [1, 1]
    assert sorted(len(p["lineas"]) for ll in t.llamadas for p in ll) == [3, 4]


def test_f055_r31_no_pisa_lo_puesto_entre_medias():
    uow = _uow_cm({14: [_lp(100, "50"), _lp(101, "50")]})
    t, ej = _Transfer({(14, 100): DEL_TRANSFER,
                       (14, 101): DEL_TRANSFER}), _Retenido()
    pm = _pm(uow, t, ej)
    pm.lanzar(ANIO, MES)
    import dataclasses
    a, b = uow.lineas[P_ACT][14]
    uow.lineas[P_ACT][14] = [dataclasses.replace(a, **P),
                             dataclasses.replace(b, propuesta_ide=7)]
    ej.soltar()
    a, b = uow.lineas[P_ACT][14]
    assert (a.partida_ide, a.propuesta_ide) == (80003, None)
    assert b.propuesta_ide == 7


# ============================ R32 · memoria ============================== #
def test_f055_r32_sin_propuesta_y_obra_que_falla_a_la_memoria():
    uow = _uow_cm({14: [_lp(100, "50"), _lp(101, "50")]})
    t, ej = _Transfer(fallan={101}), _Sincrono()
    pm = _pm(uow, t, ej)
    pm.lanzar(ANIO, MES)
    assert pm.lanzar(ANIO, MES) is False and ej.tareas == 1
    pm.olvidar()
    pm.lanzar(ANIO, MES)
    assert ej.tareas == 2


# ======================== R33 · transfer caído =========================== #
def test_f055_r33_transfer_caido_nada_guardado_y_se_relanza(caplog):
    import logging
    caplog.set_level(logging.WARNING)
    uow = _uow_cm({14: [_lp(100, "100")]})
    t = _Transfer({(14, 100): DEL_TRANSFER}, caido=True)
    ej = _Sincrono()
    pm = _pm(uow, t, ej)
    assert pm.lanzar(ANIO, MES) is False
    assert _prop(uow, 14, 100) is None and pm.en_curso(P_ACT) is False
    assert any("propuestas del mes" in r.getMessage() for r in caplog.records)
    t.caido = False
    pm.lanzar(ANIO, MES)                    # la memoria no se tocó
    assert _prop(uow, 14, 100) == 80002 and ej.tareas == 2


def test_f055_r33_fallo_en_el_segundo_trozo_guarda_el_primero():
    uow = _uow_cm({14: [_lp(100, "50"), _lp(101, "50")]})

    class _Medio(_Transfer):
        def propuesta_lote(self, peticiones):
            if self.llamadas:
                self.llamadas.append(peticiones)
                raise RuntimeError("caído")
            return super().propuesta_lote(peticiones)

    t = _Medio({(14, 100): DEL_TRANSFER, (14, 101): DEL_TRANSFER})
    pm = _pm(uow, t, n=1)
    pm.lanzar(ANIO, MES)
    assert (_prop(uow, 14, 100), _prop(uow, 14, 101)) == (80002, None)
    assert pm.lanzar(ANIO, MES) is False and len(t.llamadas) == 3


def test_f055_r37_lanzar_nunca_lanza(caplog):
    class _Roto:
        def __enter__(self):
            raise RuntimeError("bbdd caída")

        def __exit__(self, *e):
            return None

    pm = PropuestasDelMes(lambda: _Roto(), _Transfer(), _Sincrono(),
                          empresa_obras=1)
    assert pm.lanzar(ANIO, MES) is False
    assert pm.tras_sync() is None


def test_f055_r37_si_encolar_falla_salen_de_la_cola():
    class _NoEncola:
        def submit(self, fn, *a):
            raise RuntimeError("pool cerrado")

    uow = _uow_cm({14: [_lp(100, "100")]})
    pm = _pm(uow, _Transfer(), _NoEncola())
    assert pm.lanzar(ANIO, MES) is False
    assert pm.en_curso(P_ACT) is False


# ===================== tras el sync y R35 ================================ #
def test_f055_r29_tras_sync_olvida_y_lanza_los_abiertos():
    uow = _uow_cm({14: [_lp(100, "100")]})
    t, ej = _Transfer(), _Sincrono()
    pm = _pm(uow, t, ej)
    pm.lanzar(ANIO, MES)                    # sin propuesta: a la memoria
    assert pm.lanzar(ANIO, MES) is False and ej.tareas == 1
    pm.tras_sync()
    assert ej.tareas == 2                   # olvidó y relanzó el abierto


def test_f055_r35_estado_en_curso_y_lineas_con_propuesta():
    uow = _uow_cm({14: [_lp(100, "40", **PR), _lp(101, "30", **P, **PR),
                        _lp(102, "30")]})
    pm = _pm(uow, _Transfer(), _Retenido())
    pm.lanzar(ANIO, MES)
    assert pm.estado(uow, ANIO, MES) == {"en_curso": True, "lineas": [
        {"trabajador_ide": 14, "obra_ide": 100, "es_postventa": False,
         "propuesta_cod": "CI.1.20", "propuesta_res": "JEFE DE OBRA",
         "propuesta_metodo": "parte_anterior"}]}


# ============================ el cliente HTTP ============================ #
def _cliente_http(monkeypatch, respuesta):
    from infrastructure.transfer import transfer_client as mod
    llamadas = []

    def post(url, json, timeout):
        llamadas.append((url, json, timeout))
        return SimpleNamespace(status_code=200, json=lambda: respuesta)

    monkeypatch.setattr(mod.httpx, "post", post)
    return mod.TransferClient(SimpleNamespace(
        transfer_base_url="http://t.invalid", transfer_timeout_s=9.0)), \
        llamadas


def test_f055_r34_cliente_propuesta_lote(monkeypatch):
    cli, llamadas = _cliente_http(monkeypatch, {"ok": True, "obras": []})
    assert cli.propuesta_lote([{"x": 1}]) == {"ok": True, "obras": []}
    assert llamadas == [("http://t.invalid/api/partidas/propuesta-lote",
                         {"peticiones": [{"x": 1}]}, 9.0)]


@pytest.mark.parametrize("respuesta", [
    {"ok": False, "error": "caído"}, {"ok": True}])
def test_f055_r33_cliente_propuesta_lote_sin_obras_lanza(monkeypatch,
                                                         respuesta):
    cli, _ = _cliente_http(monkeypatch, respuesta)
    with pytest.raises(PropuestaNoDisponible):
        cli.propuesta_lote([])


# ================================ rutas ================================== #
PropuestasFalsas = _PropuestasFalsas


@pytest.mark.parametrize("en_curso", [True, False])
def test_f055_r30_el_cuadrante_lanza_y_publica_en_curso(api, en_curso):
    cliente, contenedor = api
    contenedor.propuestas_mes.en_curso = en_curso
    r = cliente.get(f"/api/v1/periodos/{ANIO}/{MES}/cuadrante")
    assert r.status_code == 200, r.text
    assert r.json()["propuestas_en_curso"] is en_curso
    assert contenedor.propuestas_mes.lanzadas == [(ANIO, MES, None)]


def test_f055_r35_get_propuestas(api):
    cliente, contenedor = api
    contenedor.propuestas_mes.en_curso = True
    r = cliente.get(f"/api/v1/periodos/{ANIO}/{MES}/propuestas")
    assert r.status_code == 200, r.text
    assert r.json() == contenedor.propuestas_mes.estado(None, ANIO, MES)
    assert contenedor.propuestas_mes.lanzadas == []      # solo lee


def _app_sync(pipeline, propuestas):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.api.app import build_app
    from interface_adapters.api.deps import obtener_contenedor

    class _U:
        def __enter__(self):
            return self

        def __exit__(self, *e):
            return None

    contenedor = SimpleNamespace(sync_pipeline=pipeline, uow=lambda: _U(),
                                 propuestas_mes=propuestas)
    app = build_app(Settings(_env_file=None))
    app.dependency_overrides[obtener_contenedor] = lambda: contenedor
    return TestClient(app)


def test_f055_r29_sync_con_exito_olvida_y_lanza_los_abiertos():
    from domain.models import ResultadoSync, ResultadoSyncMaestro
    pipeline = SimpleNamespace(ejecutar=lambda uow: ResultadoSync(
        ResultadoSyncMaestro(), ResultadoSyncMaestro(), 0.5))
    propuestas = PropuestasFalsas()
    r = _app_sync(pipeline, propuestas).post("/api/v1/sync")
    assert r.status_code == 200, r.text
    assert propuestas.lanzadas == ["tras_sync"]


def test_f055_r29_sync_que_falla_no_lanza():
    from domain.errors import UniversoPostventaNoDisponible

    def falla(uow):
        raise UniversoPostventaNoDisponible("transfer inaccesible")

    propuestas = PropuestasFalsas(falla=True)
    r = _app_sync(SimpleNamespace(ejecutar=falla), propuestas) \
        .post("/api/v1/sync")
    assert r.status_code == 502 and propuestas.lanzadas == []


def test_f055_r29_el_contenedor_tiene_su_cola_de_un_hilo():
    from concurrent.futures import ThreadPoolExecutor

    from interface_adapters.api import deps
    assert "propuestas_mes" in deps.Contenedor.__dataclass_fields__
    import inspect
    fuente = inspect.getsource(deps.construir_contenedor)
    assert "PropuestasDelMes(" in fuente
    assert "ThreadPoolExecutor(max_workers=1" in fuente
    assert ThreadPoolExecutor


