# tests/test_f068_api.py
"""F-068 · la api con la partida del vinculado como la del trabajador
(design §4 «api»; requirements R17, R18).

- R17: guarda como propuesta de subfila (preflight, selector y cola del
  mes) la de cualquiera de los métodos propios del vinculado
  (`parte_anterior`, `ci_tipo`, `auto_nombre`, `auto_categoria`,
  `capitulo_ci4`) y `titular`; `manual` no se guarda.
- R18: manda en cada vinculado su `descripcion` (`recurso_vinculado`) al
  registrar y al proponer, y su `tipo_res` también al proponer; lo que no
  tiene valor no viaja (la entrada de hoy).

Dobles de `test_f044_cuadrante_vinculados.py` y `test_f044_payload_traza.py`
con la forma del productor (la respuesta del transfer: `asdict(Propuesta)`
con `origen`). Ni red ni BBDD.
"""
from __future__ import annotations

import dataclasses

import pytest
from application.partidas_linea import peticion_de_subfilas
from application.registro_sigrid import (
    METODOS_PROPUESTA_VINCULADO,
    RegistroSigrid,
    es_metodo_de_propuesta_vinculado,
)
from domain.models import SubfilaVinculado
from infrastructure.db.orm_models import AsignacionVinculadoORM
from infrastructure.db.repositories import PgAsignacionRepository, _a_subfila

from tests.test_f044_cuadrante_vinculados import (
    P_ACT,
    TEL,
    _asig,
    _con,
    _ln,
    _mes,
    _obra,
    _periodos_abiertos,
    _rv,
    _selector,
    _SesionPorTabla,
    _sql,
    _Transfer,
    _TransferLote,
    _uow_selector,
)
from tests.test_f044_payload_traza import _Cargador, _lineas
from tests.test_f051_hmores_ide import _fila

PROPIOS = ("parte_anterior", "ci_tipo", "auto_nombre", "auto_categoria",
           "capitulo_ci4")
ORIGEN = "parte PT26/00300 · 06/2026 · obra 0678"


def _prop(metodo: str, origen: str | None = ORIGEN) -> dict:
    """Una propuesta de subfila como la manda el transfer
    (`asdict(Propuesta)`: las cinco claves, `origen` incluido)."""
    return {"paride": 82413, "cod": "CI.4.13", "res": "TELEFONIA",
            "metodo": metodo, "origen": origen}


# ================================ R17 ==================================== #
def test_f068_r17_metodos_de_propuesta_de_subfila():
    assert METODOS_PROPUESTA_VINCULADO == (
        "ci_tipo", "titular", "parte_anterior", "auto_nombre",
        "auto_categoria", "capitulo_ci4")


@pytest.mark.parametrize("metodo", [*PROPIOS, "titular"])
def test_f068_r17_se_guardan(metodo):
    assert es_metodo_de_propuesta_vinculado(metodo) is True


@pytest.mark.parametrize("metodo", [
    "manual", "ultimo_parte", "postventa", "var", None, "", "CI_TIPO"])
def test_f068_r17_no_se_guardan(metodo):
    assert es_metodo_de_propuesta_vinculado(metodo) is False


class _S:
    """Sesión que apunta lo que ejecuta (la del test de F-044)."""

    def __init__(self) -> None:
        self.ejecutadas: list = []
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def execute(self, stmt):
        self.ejecutadas.append(stmt)

    def commit(self):
        self.commits += 1


def test_f068_r17_el_preflight_guarda_las_de_metodo_propio():
    s = _S()
    reg = RegistroSigrid(lambda: s, None, 1)  # type: ignore[arg-type]
    vinculados = [
        {"registro_id": 41, "recurso_ide": 20 + i, "accion": "escribir",
         "paride": 82413, "partida_cod": "CI.4.13",
         "partida_res": "TELEFONIA", "partida_metodo": m,
         "partida_origen": ORIGEN if m == "parte_anterior" else None}
        for i, m in enumerate(PROPIOS)]
    vinculados.append({"registro_id": 41, "recurso_ide": 30,
                       "accion": "escribir", "paride": 82001,
                       "partida_cod": "CI.0.01", "partida_res": None,
                       "partida_metodo": "manual", "partida_origen": None})
    reg._guardar_propuestas([{"ok": True, "acciones": [],
                              "vinculados": vinculados}])
    cabecera = ("INSERT INTO asignacion_vinculado (asignacion_id, "
                "vinculado_ide, propuesta_ide, propuesta_cod, propuesta_res, "
                "propuesta_metodo, propuesta_origen) VALUES ")
    assert [_sql(x).split(" ON CONFLICT")[0] for x in s.ejecutadas] == [
        cabecera + f"(41, {20 + i}, 82413, 'CI.4.13', 'TELEFONIA', '{m}', "
        + (f"'{ORIGEN}')" if m == "parte_anterior" else "NULL)")
        for i, m in enumerate(PROPIOS)]
    assert s.commits == 1


@pytest.mark.parametrize("metodo", PROPIOS)
def test_f068_r17_el_selector_guarda_la_de_metodo_propio(metodo):
    uow = _uow_selector(_con(_ln(100, "60"), TEL))
    r = _selector(uow, _Transfer({"linea": {"10": _prop(metodo)}}),
                  vinculado_ide=10)
    assert r["propuesta"] == _prop(metodo)
    assert uow.asignaciones.guardadas == [
        ("vinculado", P_ACT, 10, (100, False), 10, _prop(metodo), False)]


def test_f068_r17_el_selector_no_guarda_la_manual():
    uow = _uow_selector(_con(_ln(100, "60"), TEL))
    _selector(uow, _Transfer({"linea": {"10": _prop("manual")}}),
              vinculado_ide=10)
    assert uow.asignaciones.guardadas == []


def test_f068_r17_la_cola_del_mes_guarda_las_de_metodo_propio():
    gas = dataclasses.replace(TEL, vinculado_ide=11, tipo="CO",
                              tipo_res="GASOIL", cod="CO-11")
    uow = _uow_selector(_con(_ln(100, "60"), TEL, gas))
    _periodos_abiertos(uow)
    por_recurso = {"10": _prop("parte_anterior"),
                   "11": _prop("capitulo_ci4", None)}
    t = _TransferLote(lambda ps: {"ok": True, "obras": [
        {"ok": True, "propuestas": {}, "vinculados": {
            ln["clave"]: por_recurso for ln in p["lineas"]}}
        for p in ps]})
    _mes(uow, t).encolar(2026, 7)
    assert uow.asignaciones.guardadas == [
        ("vinculado", P_ACT, 10, (100, False), 10,
         _prop("parte_anterior"), True),
        ("vinculado", P_ACT, 10, (100, False), 11,
         _prop("capitulo_ci4", None), True)]


def test_f068_r17_la_cola_del_mes_no_guarda_la_manual():
    uow = _uow_selector(_con(_ln(100, "60"), TEL))
    _periodos_abiertos(uow)
    t = _TransferLote(lambda ps: {"ok": True, "obras": [
        {"ok": True, "propuestas": {}, "vinculados": {
            ln["clave"]: {"10": _prop("manual")} for ln in p["lineas"]}}
        for p in ps]})
    _mes(uow, t).encolar(2026, 7)
    assert uow.asignaciones.guardadas == []


# ================================ R18 ==================================== #
def _tel_d() -> SubfilaVinculado:
    return dataclasses.replace(TEL, descripcion="MOVIL 600111222")


def test_f068_r18_al_registrar_manda_la_descripcion():
    [l] = _lineas([_fila(1)], desde=(2026, 10),
                  cargador=_Cargador({1: (_tel_d(),)}))
    assert l["vinculados"] == [
        {"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
         "cod": "TF-10", "descripcion": "MOVIL 600111222"}]


def test_f068_r18_al_registrar_sin_descripcion_la_de_hoy():
    [l] = _lineas([_fila(1)], desde=(2026, 10),
                  cargador=_Cargador({1: (TEL,)}))
    assert l["vinculados"] == [
        {"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
         "cod": "TF-10"}]


def test_f068_r18_al_proponer_manda_tipo_res_y_descripcion():
    linea = _ln(100, "60")
    sin_tipo = SubfilaVinculado(vinculado_ide=12, tipo="VE", cod="VE-12")
    assert peticion_de_subfilas(linea, [_tel_d(), TEL, sin_tipo]) == {
        "vinculados": [
            {"recurso_ide": 10, "tipo": "TF", "categoria": None,
             "cod": "TF-10", "tipo_res": "TELEFONO",
             "descripcion": "MOVIL 600111222"},
            {"recurso_ide": 10, "tipo": "TF", "categoria": None,
             "cod": "TF-10", "tipo_res": "TELEFONO"},
            {"recurso_ide": 12, "tipo": "VE", "categoria": None,
             "cod": "VE-12"}]}


def test_f068_r18_el_selector_y_la_cola_mandan_los_textos():
    uow = _uow_selector(_con(_ln(100, "60"), _tel_d()))
    t = _Transfer({"linea": {"10": _prop("parte_anterior")}})
    _selector(uow, t, vinculado_ide=10)
    [p] = t.payloads
    assert p["lineas"][0]["vinculados"] == [
        {"recurso_ide": 10, "tipo": "TF", "categoria": None, "cod": "TF-10",
         "tipo_res": "TELEFONO", "descripcion": "MOVIL 600111222"}]
    uow = _uow_selector(_con(_ln(100, "60"), _tel_d()))
    _periodos_abiertos(uow)
    t = _TransferLote(lambda ps: {"ok": True, "obras": [
        {"ok": True, "propuestas": {}} for _ in ps]})
    _mes(uow, t).encolar(2026, 7)
    [[pet]] = t.peticiones
    assert pet["lineas"][0]["vinculados"][0]["descripcion"] == (
        "MOVIL 600111222")


def test_f068_r18_la_subfila_lleva_la_descripcion_del_vinculado():
    rv = _rv(10, 14)
    assert _a_subfila(rv, None).descripcion == "NO SALE"
    fila = AsignacionVinculadoORM(asignacion_id=41, vinculado_ide=10,
                                  propuesta_ide=82413,
                                  propuesta_metodo="parte_anterior")
    con = _a_subfila(rv, fila)
    assert (con.descripcion, con.propuesta_metodo) == (
        "NO SALE", "parte_anterior")
    s = _SesionPorTabla([(_asig(41, 14), _obra())], vinculados=[rv])
    [ln] = PgAsignacionRepository(s).lineas_de_trabajador(2, 14)  # type: ignore[arg-type]
    assert [v.descripcion for v in ln.vinculados] == ["NO SALE"]


def test_f068_r18_sin_descripcion_por_defecto():
    assert SubfilaVinculado(vinculado_ide=10).descripcion is None
