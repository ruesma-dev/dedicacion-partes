# tests/test_f057_pendientes.py
"""F-057 · Qué líneas están PENDIENTES de propuesta lo dice la api.

«Pendiente» = la línea está en la cola de las propuestas del mes (en cola o
calculándose), la misma memoria que llena `lanzar()`: la regla de qué se
encola no se copia en ningún sitio.

- r2 (`PropuestasDelMes`): `pendientes(periodo_id)` con la línea encolada,
  en cálculo, de postventa, en la memoria «sin propuesta», con partida
  elegida, con partida fija y con propuesta ya guardada; `encolar()` da
  `(en_curso, pendientes)` de una sola vez y nunca lanza; `estado()` añade
  la lista `pendientes`.
- r2 (rutas): cada línea del cuadrante y de las escrituras que devuelven la
  fila lleva `propuesta_pendiente`, calculado DESPUÉS de encolar; `GET
  …/propuestas` añade `pendientes`.

`PropuestasDelMes` real con el ejecutor RETENIDO de F-055 y rutas con
`TestClient` sobre el contenedor falso de `test_f024_rutas_empresa`. Sin red
ni BBDD.
"""
from __future__ import annotations

import pytest
from application.propuestas_mes import PropuestasDelMes
from domain.models import EstadoPeriodo

from tests.test_f024_cuadrante_empresa import ANIO, MES, P_ACT
from tests.test_f024_rutas_empresa import (  # noqa: F401  (fixture `api`)
    _PropuestasFalsas,
    api,
)
from tests.test_f050_partida_linea import P
from tests.test_f055_propuesta_guardada import DEL_TRANSFER, PR, _lp
from tests.test_f055_propuestas_mes import (
    _Retenido,
    _Sincrono,
    _Transfer,
    _uow_cm,
)

BASE = f"/api/v1/periodos/{ANIO}/{MES}"


def _pm(uow, transfer=None, ejecutor=None):
    return PropuestasDelMes(lambda: uow, transfer or _Transfer(),
                            ejecutor or _Retenido(), empresa_obras=1)


# =================== r2 · `pendientes` con la regla de encolar ============ #
def test_f057_r2_encolada_es_pendiente_y_las_demas_no():
    """Encolada sí; postventa, partida elegida, partida fija y propuesta ya
    guardada no (no se encolan: es la regla de `lanzar`, no otra)."""
    uow = _uow_cm({14: [_lp(100, "40"), _lp(100, "10", pv=True),
                        _lp(101, "30", **P), _lp(102, "20", **PR)],
                   10: [_lp(900, "100", partida_fija=True)]})
    pm = _pm(uow)
    assert pm.pendientes(P_ACT) == frozenset()
    pm.lanzar(ANIO, MES)
    assert pm.pendientes(P_ACT) == frozenset({(14, 100, False)})
    assert pm.pendientes(P_ACT + 1) == frozenset()          # otro periodo


def test_f057_r2_en_calculo_sigue_pendiente_y_al_acabar_deja_de_serlo():
    uow = _uow_cm({14: [_lp(100, "100")]})
    vistas = []

    class _Mira(_Transfer):
        def propuesta_lote(self, peticiones):
            vistas.append(pm.pendientes(P_ACT))          # calculándose
            return super().propuesta_lote(peticiones)

    ej = _Retenido()
    pm = _pm(uow, _Mira({(14, 100): DEL_TRANSFER}), ej)
    pm.lanzar(ANIO, MES)
    ej.soltar()
    assert vistas == [frozenset({(14, 100, False)})]
    assert pm.pendientes(P_ACT) == frozenset()


def test_f057_r2_en_la_memoria_sin_propuesta_no_es_pendiente():
    uow = _uow_cm({14: [_lp(100, "100")]})
    ej = _Retenido()
    pm = _pm(uow, _Transfer(), ej)          # el transfer no propone nada
    pm.lanzar(ANIO, MES)
    ej.soltar()
    assert pm.encolar(ANIO, MES) == (False, frozenset())
    assert ej.pendientes == []


def test_f057_r2_encolar_da_en_curso_y_pendientes_de_una_vez():
    uow = _uow_cm({14: [_lp(100, "50"), _lp(101, "50")],
                   10: [_lp(100, "100")]})
    pm = _pm(uow)
    assert pm.encolar(ANIO, MES, [14]) == (
        True, frozenset({(14, 100, False), (14, 101, False)}))
    # Las de todo el periodo, no solo las del trabajador que se escribe.
    assert pm.encolar(ANIO, MES, [10]) == (True, frozenset(
        {(14, 100, False), (14, 101, False), (10, 100, False)}))
    assert pm.en_curso(P_ACT) is True
    assert pm.lanzar(ANIO, MES) is True


@pytest.mark.parametrize("anio, mes, estado", [
    (ANIO, MES, EstadoPeriodo.CERRADO), (2030, 1, EstadoPeriodo.ABIERTO)],
    ids=["cerrado", "inexistente"])
def test_f057_r2_periodo_cerrado_o_inexistente_sin_pendientes(anio, mes,
                                                              estado):
    uow = _uow_cm({14: [_lp(100, "100")]}, estado)
    assert _pm(uow).encolar(anio, mes) == (False, frozenset())


def test_f057_r2_encolar_nunca_lanza():
    class _Roto:
        def __enter__(self):
            raise RuntimeError("bbdd caída")

        def __exit__(self, *e):
            return None

    pm = PropuestasDelMes(lambda: _Roto(), _Transfer(), _Sincrono(),
                          empresa_obras=1)
    assert pm.encolar(ANIO, MES) == (False, frozenset())


def test_f057_r2_estado_publica_pendientes():
    uow = _uow_cm({14: [_lp(101, "50"), _lp(100, "50")],
                   10: [_lp(100, "100", **PR)]})
    pm = _pm(uow)
    pm.lanzar(ANIO, MES)
    e = pm.estado(uow, ANIO, MES)
    assert e["en_curso"] is True
    assert e["pendientes"] == [
        {"trabajador_ide": 14, "obra_ide": 100, "es_postventa": False},
        {"trabajador_ide": 14, "obra_ide": 101, "es_postventa": False}]
    assert [ln["trabajador_ide"] for ln in e["lineas"]] == [10]


def test_f057_r2_estado_sin_cola_sin_pendientes():
    uow = _uow_cm({14: [_lp(100, "100")]})
    e = _pm(uow).estado(uow, ANIO, MES)
    assert (e["en_curso"], e["pendientes"]) == (False, [])


# =========================== r2 · las rutas =============================== #
def _pendiente(cuerpo_trabajador):
    return {(ln["obra_ide"], ln["es_postventa"]): ln["propuesta_pendiente"]
            for ln in cuerpo_trabajador["lineas"]}


def test_f057_r2_cuadrante_marca_cada_linea(api):  # noqa: F811
    cliente, contenedor = api
    contenedor.propuestas_mes = _PropuestasFalsas(
        en_curso=True, pendientes={(10, 100, False), (16, 900, False),
                                   (99, 100, False)})
    r = cliente.get(f"{BASE}/cuadrante")
    assert r.status_code == 200, r.text
    filas = {t["ide"]: _pendiente(t) for t in r.json()["trabajadores"]}
    assert filas[10] == {(100, False): True, (900, False): False}
    assert filas[16] == {(100, False): False, (900, False): True}
    assert filas[12] == {(900, False): False}
    assert contenedor.propuestas_mes.lanzadas == [(ANIO, MES, None)]


def test_f057_r2_la_postventa_de_la_misma_obra_no_es_pendiente(api):  # noqa: F811
    import dataclasses
    cliente, contenedor = api
    uow = contenedor.uow()
    pv = dataclasses.replace(uow.lineas[P_ACT][10][0], es_postventa=True)
    uow.lineas[P_ACT][10].append(pv)
    contenedor.propuestas_mes = _PropuestasFalsas(
        en_curso=True, pendientes={(10, 100, False)})
    r = cliente.get(f"{BASE}/cuadrante")
    assert r.status_code == 200, r.text
    [ana] = [t for t in r.json()["trabajadores"] if t["ide"] == 10]
    assert _pendiente(ana) == {(100, False): True, (900, False): False,
                               (100, True): False}


def test_f057_r2_sin_cola_ninguna_linea_pendiente(api):  # noqa: F811
    cliente, _ = api
    r = cliente.get(f"{BASE}/cuadrante")
    assert r.status_code == 200, r.text
    assert not any(ln["propuesta_pendiente"]
                   for t in r.json()["trabajadores"] for ln in t["lineas"])


#: (método, ruta, cuerpo, trabajador). F8 con Eva (14): es la que tiene
#: datos en el mes anterior del contenedor falso.
ESCRITURAS_CON_FILA = [
    ("PUT", "/trabajadores/10/asignaciones",
     {"lineas": [{"obra_ide": 100, "porcentaje": 60},
                 {"obra_ide": 101, "porcentaje": 40}]}, 10),
    ("PUT", "/trabajadores/10/partida",
     {"obra_ide": 100, "es_postventa": False, "partida": None}, 10),
    ("POST", "/trabajadores/10/deshacer", None, 10),
    ("POST", "/trabajadores/14/copiar-anterior", None, 14),
]


@pytest.mark.parametrize("metodo, ruta, cuerpo, ide", ESCRITURAS_CON_FILA,
                         ids=["guardar_fila", "partida", "deshacer", "f8"])
def test_f057_r2_las_escrituras_marcan_la_fila_tras_encolar(
        api, metodo, ruta, cuerpo, ide):  # noqa: F811
    cliente, contenedor = api
    cliente.put(f"{BASE}/trabajadores/{ide}/asignaciones",
                json={"lineas": [{"obra_ide": 100, "porcentaje": 60},
                                 {"obra_ide": 900, "porcentaje": 40}]},
                headers={"X-Usuario": "ana"})

    class _TrasEncolar(_PropuestasFalsas):
        """La cola cambia AL encolar: lo que vale es lo de después."""

        def encolar(self, anio, mes, trabajadores=None):
            self.pendientes = frozenset(
                {(t, o, False) for t in trabajadores or [] for o in (100, 101,
                                                                  900)})
            return super().encolar(anio, mes, trabajadores)

    contenedor.propuestas_mes = _TrasEncolar(en_curso=True)
    r = cliente.request(metodo, f"{BASE}{ruta}", json=cuerpo,
                        headers={"X-Usuario": "ana"})
    assert r.status_code == 200, r.text
    cuerpo_r = r.json()
    assert cuerpo_r["propuestas_en_curso"] is True
    lineas = cuerpo_r["trabajador"]["lineas"]
    assert lineas and all(ln["propuesta_pendiente"] for ln in lineas)
    assert contenedor.propuestas_mes.lanzadas == [(ANIO, MES, [ide])]


def test_f057_r2_si_encolar_falla_nada_pendiente(api):  # noqa: F811
    cliente, contenedor = api

    class _Rota(_PropuestasFalsas):
        def lanzar(self, anio, mes, trabajadores=None):
            raise RuntimeError("cola rota")

    contenedor.propuestas_mes = _Rota(en_curso=True,
                                      pendientes={(10, 100, False)})
    r = cliente.get(f"{BASE}/cuadrante")
    assert r.status_code == 200, r.text
    assert r.json()["propuestas_en_curso"] is False
    assert not any(ln["propuesta_pendiente"]
                   for t in r.json()["trabajadores"] for ln in t["lineas"])


def test_f057_r2_get_propuestas_publica_pendientes(api):  # noqa: F811
    cliente, contenedor = api
    contenedor.propuestas_mes = _PropuestasFalsas(
        en_curso=True, pendientes={(10, 100, False)})
    r = cliente.get(f"{BASE}/propuestas")
    assert r.status_code == 200, r.text
    assert r.json()["pendientes"] == [
        {"trabajador_ide": 10, "obra_ide": 100, "es_postventa": False}]
    assert contenedor.propuestas_mes.lanzadas == []        # solo lee


def test_f057_r2_de_punta_a_punta_con_la_cola_real(api):  # noqa: F811
    """El cuadrante con `PropuestasDelMes` real: las líneas encoladas al
    pedirlo salen pendientes; la de postventa y la de partida elegida, no;
    al acabar la tarea, el sondeo ya no las da por pendientes."""
    import dataclasses
    cliente, contenedor = api
    uow = contenedor.uow()
    ana = uow.lineas[P_ACT][10]
    uow.lineas[P_ACT][10] = [ana[0], dataclasses.replace(ana[1], **P),
                             dataclasses.replace(ana[0], es_postventa=True)]
    ej = _Retenido()
    contenedor.propuestas_mes = PropuestasDelMes(
        contenedor.uow, _Transfer(), ej, empresa_obras=1)
    r = cliente.get(f"{BASE}/cuadrante")
    assert r.status_code == 200, r.text
    assert r.json()["propuestas_en_curso"] is True
    [fila] = [t for t in r.json()["trabajadores"] if t["ide"] == 10]
    assert _pendiente(fila) == {(100, False): True, (900, False): False,
                                (100, True): False}
    ej.soltar()
    p = cliente.get(f"{BASE}/propuestas").json()
    assert (p["en_curso"], p["pendientes"]) == (False, [])
