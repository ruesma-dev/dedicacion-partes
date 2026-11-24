# tests/test_f074_motivos.py
"""F-074 · T1: la regla, solo en segundo plano, y el motivo del «no
encuentra» (R8-R10; D6 b).

- R8: `partidas/propuesta(-lote)` y `postventa/universo` siguen siendo los
  únicos sitios donde corre la regla, con el mismo resultado (lo cubren
  intactos `test_f050_endpoint_propuesta.py` y `test_f055_orden_propuesta.py`).
- R9: la propuesta gana `motivos` (`{clave: texto}`) de cada línea sin
  propuesta y `motivos_vinculados` (`{clave: {recurso: texto}}`) de cada
  subfila sin ella; sin ninguna, la respuesta de siempre (sin las claves).
- R10: el universo de postventa gana `motivos` (`{ide: texto}`) de las obras
  pedidas que no casan, con el texto de `casar_postventa`.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

from types import SimpleNamespace

from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.partida_definida import (
    MOTIVO_NINGUN_PASO,
    MOTIVO_SIN_HOJAS,
    MOTIVO_TITULAR_NO_VALIDA,
    MOTIVO_TITULAR_SIN_PARTIDA,
    motivo_sin_propuesta,
)
from application.services.partida_resolver import construir_catalogo
from application.services.reglas_vinculados import (
    MOTIVO_SIN_CI,
    MOTIVO_VARIAS_CI,
    por_que_sin_ci,
)
from application.services.universo_postventa import UniversoPostventa
from domain.models.registro_models import ObraEntrada
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app

from tests.conftest import (
    OBRA_ORIGEN,
    OBRA_SIN_PARTIDA_PV,
    ClienteFalso,
    SettingsFalso,
    _fila,
)
from tests.test_f044_pipeline_vinculados import ClienteVin, _linea, _vin
from tests.test_f050_endpoint_propuesta import AJUSTES
from tests.test_f050_pipeline import ClienteHistorial, _h
from tests.test_f055_lote import _ajustes

NADIE = {"categoria": "Astronauta", "nombre": "Nadie Nunca"}


def _proponer(cli, *lineas, obra=None) -> dict:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso()).proponer(
        empresa=1, obra=obra or ObraEntrada(codigo=OBRA_ORIGEN), ano=2026,
        mes=7, lineas=list(lineas))


# ===================== R9 · motivo de cada línea ======================= #
def test_f074_r9_linea_sin_propuesta_lleva_su_motivo():
    r = _proponer(ClienteHistorial([]), _linea("a", **NADIE),
                  _linea("b"))
    assert r["propuestas"]["a"] is None
    assert r["propuestas"]["b"]["cod"] == "CI.1.10"
    assert r["motivos"] == {"a": MOTIVO_NINGUN_PASO}


def test_f074_r9_presupuesto_sin_hojas_activas():
    cli = ClienteHistorial([])
    cli.partidas_origen = [_fila(80000, 0, 0, "CI", "COSTES INDIRECTOS"),
                           _fila(80001, 80000, 1, "CI.1", "X", tipdes=1)]
    r = _proponer(cli, _linea("a"))
    assert r["motivos"] == {"a": MOTIVO_SIN_HOJAS}


def test_f074_r9_todas_con_propuesta_sin_la_clave():
    r = _proponer(ClienteHistorial([_h()]), _linea("a"))
    assert "motivos" not in r and "motivos_vinculados" not in r


def test_f074_r9_postventa_que_no_casa_con_el_motivo_del_casado():
    r = _proponer(ClienteFalso(), _linea("a", pv=True),
                  obra=ObraEntrada(codigo=OBRA_SIN_PARTIDA_PV))
    assert r["propuestas"]["a"] is None
    assert r["motivos"]["a"] == (
        f"la obra {OBRA_SIN_PARTIDA_PV} no casa con ninguna partida de "
        "POSTV2")


def test_f074_r9_motivo_sin_propuesta_puro():
    assert motivo_sin_propuesta({}) == MOTIVO_SIN_HOJAS
    nodos = construir_catalogo([_fila(1, 0, 0, "CI", "X"),
                                _fila(2, 1, 1, "CI.1", "Y")])
    assert motivo_sin_propuesta(nodos) == MOTIVO_NINGUN_PASO


# ==================== R9 · motivo de cada subfila ====================== #
def test_f074_r9_subfilas_sin_propuesta_con_el_motivo_de_la_regla():
    """13 (sin cuenta) y 12 (dos hojas con su cuenta) no tienen propuesta;
    10 sí: solo salen las dos primeras."""
    r = _proponer(ClienteVin(), _linea("a", vinculados=_vin(10, 12, 13)))
    assert r["vinculados"]["a"]["10"]["cod"] == "CICO13"
    assert r["motivos_vinculados"] == {"a": {
        "12": por_que_sin_ci(MOTIVO_VARIAS_CI),
        "13": por_que_sin_ci(MOTIVO_SIN_CI)}}


def test_f074_r9_subfila_con_titular_sin_partida():
    """Titular de postventa sin casado: la subfila va con él y no tiene."""
    cli = ClienteVin()
    r = _proponer(cli, _linea("a", pv=True, vinculados=_vin(10)),
                  obra=ObraEntrada(codigo=OBRA_SIN_PARTIDA_PV))
    assert r["vinculados"] == {"a": {"10": None}}
    assert r["motivos_vinculados"] == {"a": {"10": MOTIVO_TITULAR_SIN_PARTIDA}}


def test_f074_r9_subfila_con_elegida_del_titular_que_no_vale():
    r = _proponer(ClienteVin(), _linea("a", paride=80000,
                                       vinculados=_vin(10)))
    assert r["motivos_vinculados"] == {"a": {"10": MOTIVO_TITULAR_NO_VALIDA}}


def test_f074_r9_el_lote_lleva_los_mismos_motivos():
    lineas = [_linea("a", **NADIE), _linea("b", vinculados=_vin(13))]
    suelta = _proponer(ClienteVin(), *lineas)
    [lote] = RegistroLote(cliente=ClienteVin(), settings=_ajustes()).proponer(
        [{"empresa": 1, "obra": ObraEntrada(codigo=OBRA_ORIGEN), "ano": 2026,
          "mes": 7, "lineas": lineas}])
    assert lote["motivos"] == suelta["motivos"] == {"a": MOTIVO_NINGUN_PASO}
    assert lote["motivos_vinculados"] == suelta["motivos_vinculados"]


def test_f074_r9_por_http(monkeypatch):
    cli = ClienteHistorial([])
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    api = TestClient(modulo_app.build_app(SimpleNamespace(**AJUSTES)))
    r = api.post("/api/partidas/propuesta", json={
        "empresa": 1, "obra": {"codigo": OBRA_ORIGEN}, "ano": 2026, "mes": 7,
        "lineas": [{"clave": "a", "recurso_ide": 200, "es_postventa": False,
                    **NADIE}]})
    assert r.status_code == 200, r.text
    assert r.json()["motivos"] == {"a": MOTIVO_NINGUN_PASO}


# ================== R10 · motivos del universo ========================= #
def _universo(cli, *obras, **ajustes) -> dict:
    return UniversoPostventa(cliente=cli, settings=SettingsFalso(**ajustes)) \
        .calcular(1, list(obras))


def test_f074_r10_las_que_no_casan_con_su_motivo():
    cli = ClienteFalso()
    r = _universo(cli, ObraEntrada(ide=555001, codigo=OBRA_ORIGEN,
                                   nombre="15 VIVIENDAS"),
                  ObraEntrada(ide=555002, codigo=OBRA_SIN_PARTIDA_PV,
                              nombre="SIN PARTIDA PV"))
    assert [o["ide"] for o in r["obras"]] == [555001]
    assert r["motivos"] == {555002: (
        f"la obra {OBRA_SIN_PARTIDA_PV} no casa con ninguna partida de "
        "POSTV2")}


def test_f074_r10_sin_obra_de_postventa_el_motivo_de_su_catalogo():
    cli = ClienteFalso(obra_postventa_existe=False)
    r = _universo(cli, ObraEntrada(ide=555001, codigo=OBRA_ORIGEN))
    assert r["motivos"] == {555001: r["motivo"]}
    assert "no encontrada" in r["motivo"]


def test_f074_r10_todas_casan_sin_la_clave():
    r = _universo(ClienteFalso(), ObraEntrada(ide=555001, codigo=OBRA_ORIGEN))
    assert "motivos" not in r


def test_f074_r10_por_http_con_claves_de_texto(monkeypatch):
    cli = ClienteFalso()
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    api = TestClient(modulo_app.build_app(SimpleNamespace(**AJUSTES)))
    r = api.post("/api/postventa/universo", json={"empresa": 1, "obras": [
        {"ide": 555002, "codigo": OBRA_SIN_PARTIDA_PV, "nombre": "X"}]})
    assert r.status_code == 200, r.text
    assert r.json()["motivos"] == {"555002": (
        f"la obra {OBRA_SIN_PARTIDA_PV} no casa con ninguna partida de "
        "POSTV2")}
