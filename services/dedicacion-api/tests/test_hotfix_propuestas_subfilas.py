# tests/test_hotfix_propuestas_subfilas.py
"""Hotfix del 2026-11-03: `GET …/propuestas` daba 500 en cuanto una subfila
de vinculado tenía propuesta guardada.

`PropuestasDelMes.estado()` (F-044 R9) devuelve la clave `subfilas` y
`PropuestasOut` no la declaraba; con `extra="forbid"` la ruta reventaba y el
front se quedaba pintando «automática». Aquí la ruta con y sin subfilas.
"""
from __future__ import annotations

from tests.test_f024_cuadrante_empresa import ANIO, MES
from tests.test_f024_rutas_empresa import api  # noqa: F401  (fixture `api`)

SUBFILA = {"trabajador_ide": 1150675, "obra_ide": 2313811,
           "es_postventa": False, "vinculado_ide": 1923784,
           "propuesta_cod": "CI.03P.9", "propuesta_res": "VEHICULOS",
           "propuesta_metodo": "parte_anterior"}


def _con_estado(contenedor, estado: dict) -> None:
    contenedor.propuestas_mes.estado = lambda uow, anio, mes: estado


def test_hotfix_get_propuestas_con_subfilas_no_da_500(api):  # noqa: F811
    cliente, contenedor = api
    estado = {"en_curso": False, "lineas": [], "pendientes": [],
              "subfilas": [SUBFILA]}
    _con_estado(contenedor, estado)
    r = cliente.get(f"/api/v1/periodos/{ANIO}/{MES}/propuestas")
    assert r.status_code == 200, r.text
    assert r.json() == estado


def test_hotfix_get_propuestas_sin_subfilas_es_la_de_antes(api):  # noqa: F811
    cliente, contenedor = api
    _con_estado(contenedor, {"en_curso": True, "lineas": [],
                             "pendientes": []})
    r = cliente.get(f"/api/v1/periodos/{ANIO}/{MES}/propuestas")
    assert r.status_code == 200, r.text
    # Sin subfilas, la respuesta de siempre: sin la clave.
    assert r.json() == {"en_curso": True, "lineas": [], "pendientes": []}
