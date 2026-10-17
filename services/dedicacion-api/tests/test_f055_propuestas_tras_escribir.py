# tests/test_f055_propuestas_tras_escribir.py
"""F-055 · T12b: encolar las propuestas tras escribir (D9; R29, R30, R37).

Las seis escrituras del cuadrante, tras cerrar su UoW, encolan las líneas
pendientes de los trabajadores que tocan (copiar el mes, las de todo el
periodo) y publican `propuestas_en_curso`; el resto de su respuesta no
cambia. Si encolar falla, la escritura responde igual con
`propuestas_en_curso` falso y un log. `TestClient` con el contenedor falso
de `test_f024_rutas_empresa` (lista cerrada). Sin red ni BBDD.
"""
from __future__ import annotations

import logging

import pytest

from tests.test_f024_cuadrante_empresa import ANIO, MES
from tests.test_f024_rutas_empresa import (  # noqa: F401  (fixture `api`)
    _PropuestasFalsas,
    api,
)

BASE = f"/api/v1/periodos/{ANIO}/{MES}"
ESCRITURAS = [
    ("put", "/trabajadores/14/asignaciones",
     {"lineas": [{"obra_ide": 101, "porcentaje": 100}]}, [14]),
    ("put", "/trabajadores/14/partida",
     {"obra_ide": 100, "es_postventa": False,
      "partida": {"ide": 1, "cod": "X", "res": "Y"}}, [14]),
    ("post", "/trabajadores/10/copiar-anterior", None, [10]),
    ("post", "/completar", {"trabajadores": [14, 11], "obra_ide": 101},
     [14, 11]),
    ("post", "/copiar-anterior", None, None),
]
IDS = ["guardar_fila", "partida", "f8", "completar", "copiar_mes"]


def _llamar(cliente, metodo, ruta, cuerpo):
    return cliente.request(metodo.upper(), f"{BASE}{ruta}", json=cuerpo,
                           headers={"X-Usuario": "ana"})


@pytest.mark.parametrize("en_curso", [True, False])
@pytest.mark.parametrize("metodo, ruta, cuerpo, trabajadores", ESCRITURAS,
                         ids=IDS)
def test_f055_r37_cada_escritura_encola_los_suyos_y_publica(
        api, metodo, ruta, cuerpo, trabajadores, en_curso):  # noqa: F811
    cliente, contenedor = api
    if ruta.endswith("/partida"):
        _llamar(cliente, "put", "/trabajadores/14/asignaciones",
                {"lineas": [{"obra_ide": 100, "porcentaje": 100}]})
    contenedor.propuestas_mes = _PropuestasFalsas(en_curso=en_curso)
    r = _llamar(cliente, metodo, ruta, cuerpo)
    assert r.status_code == 200, r.text
    assert r.json()["propuestas_en_curso"] is en_curso
    assert contenedor.propuestas_mes.lanzadas == [(ANIO, MES, trabajadores)]


def test_f055_r37_deshacer_encola_al_trabajador(api):  # noqa: F811
    cliente, contenedor = api
    _llamar(cliente, "put", "/trabajadores/14/asignaciones",
            {"lineas": [{"obra_ide": 101, "porcentaje": 100}]})
    contenedor.propuestas_mes = _PropuestasFalsas(en_curso=True)
    r = _llamar(cliente, "post", "/trabajadores/14/deshacer", None)
    assert r.status_code == 200, r.text
    assert r.json()["propuestas_en_curso"] is True
    assert contenedor.propuestas_mes.lanzadas == [(ANIO, MES, [14])]


def test_f055_r37_el_resto_del_cuerpo_no_cambia(api):  # noqa: F811
    cliente, _ = api
    r = _llamar(cliente, "put", "/trabajadores/14/asignaciones",
                {"lineas": [{"obra_ide": 101, "porcentaje": 100}]})
    cuerpo = r.json()
    assert set(cuerpo) == {"trabajador", "resumen", "propuestas_en_curso"}


class _Rota(_PropuestasFalsas):
    def lanzar(self, anio, mes, trabajadores=None):
        raise RuntimeError("cola rota")


@pytest.mark.parametrize("metodo, ruta, cuerpo, trabajadores", ESCRITURAS,
                         ids=IDS)
def test_f055_r37_si_encolar_falla_responde_igual(
        api, caplog, metodo, ruta, cuerpo, trabajadores):  # noqa: F811
    caplog.set_level(logging.WARNING)
    cliente, contenedor = api
    if ruta.endswith("/partida"):
        _llamar(cliente, "put", "/trabajadores/14/asignaciones",
                {"lineas": [{"obra_ide": 100, "porcentaje": 100}]})
    contenedor.propuestas_mes = _Rota()
    r = _llamar(cliente, metodo, ruta, cuerpo)
    assert r.status_code == 200, r.text
    assert r.json()["propuestas_en_curso"] is False
    [aviso] = [x for x in caplog.records
               if "no se pudieron encolar" in x.getMessage()]
    assert aviso.exc_info and aviso.exc_info[0] is not None   # traza (T16)


def test_f055_r30_el_cuadrante_tambien_resiste_una_cola_rota(api):  # noqa: F811
    cliente, contenedor = api
    contenedor.propuestas_mes = _Rota()
    r = cliente.get(f"{BASE}/cuadrante")
    assert r.status_code == 200 and r.json()["propuestas_en_curso"] is False


def test_f055_r37_periodo_cerrado_no_encola(api):  # noqa: F811
    from tests.test_f050_rutas_partida import _PeriodoCerrado
    cliente, contenedor = api
    contenedor.uow().periodos = _PeriodoCerrado()
    r = _llamar(cliente, "put", "/trabajadores/14/asignaciones",
                {"lineas": [{"obra_ide": 101, "porcentaje": 100}]})
    assert r.status_code == 409 and contenedor.propuestas_mes.lanzadas == []


# ===== con el `PropuestasDelMes` real: solo las líneas nuevas del que toca ==
def test_f055_r29_guardar_una_obra_nueva_encola_esa_linea_y_no_la_otra():
    from application.propuestas_mes import PropuestasDelMes
    from application.use_cases import GuardarAsignaciones

    from tests.test_f050_partida_linea import FILTRO
    from tests.test_f055_propuesta_guardada import PR, _lp
    from tests.test_f055_propuestas_mes import _Retenido, _Transfer, _uow_cm
    uow = _uow_cm({14: [_lp(100, "50", **PR)], 10: [_lp(102, "100")]})
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14, [{"obra_ide": 100, "porcentaje": "50"},
                             {"obra_ide": 101, "porcentaje": "50"}], "ana",
        filtro=FILTRO)
    ej, t = _Retenido(), _Transfer()
    pm = PropuestasDelMes(lambda: uow, t, ej, empresa_obras=1)
    assert pm.lanzar(ANIO, MES, [14]) is True
    ej.soltar()
    [[peticion]] = t.llamadas
    assert peticion["obra"]["ide"] == 101
    assert [l["clave"] for l in peticion["lineas"]] == ["14"]
