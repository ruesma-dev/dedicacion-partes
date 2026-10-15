# tests/test_f055_pipeline_partidas.py
"""F-055 · T4: el preflight sin búsquedas de partidas (R3-R12).

- R3/R4: una línea de obra normal con partida (elegida o propuesta guardada)
  no lee presupuesto ni historial: se valida con `validar_partidas`, UNA
  lectura por petición, por `ide` (obra de origen, hoja, alta).
- R5: la elegida que no vale se omite con `MOTIVO_PARTIDA_NO_HOJA`.
- R6/R7: la propuesta guardada que no vale es pendiente: el camino de hoy
  (presupuesto, una lectura de historial, `proponer_partida`).
- R8: la propuesta guardada válida se escribe con sus `partida_*`.
- R9: toda acción con partida publica `partida_res`.
- R10: `partidas_obra` solo lleva catálogo si se leyó el presupuesto.
- R11/R12: postventa, VAR, conflictos e idempotencia, con lo leído.

El `ClienteHistorial` de `test_f050_pipeline.py` anota el historial y aquí,
además, cada lectura de presupuesto. Sin red ni BBDD; `ide` inventados.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import AccionLinea, LineaEntrada
from fastapi.testclient import TestClient

from tests.conftest import (
    SettingsFalso,
    linea,
    linea_previa,
)
from tests.test_f050_pipeline import OBRA, ClienteHistorial, _h

#: Lo que el cuadrante guardó como propuesta de la línea (80002, CI.1.20).
GUARDADA = dict(propuesta_paride=80002, propuesta_cod="CI.1.20",
                propuesta_res="JEFE DE OBRA (guardada)",
                propuesta_metodo="parte_anterior",
                propuesta_origen="parte PT26/00050 · 05/2026 · obra 0678")


class Cliente(ClienteHistorial):
    """Anota también las lecturas de presupuesto."""

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.presupuestos: list[int] = []

    def capitulos_de_obra(self, obride):
        self.presupuestos.append(int(obride))
        return super().capitulos_de_obra(obride)


def _pf(cli, *lineas, **ajustes):
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes)) \
        .preflight(obra=OBRA, lineas=list(lineas))


def _a(pf, registro_id=1) -> AccionLinea:
    return next(a for a in pf.acciones if a.registro_id == registro_id)


# ===================== R3 · la elegida, sin búsquedas ==================== #
def test_f055_r3_elegida_sin_presupuesto_ni_historial():
    cli = Cliente([_h()])
    pf = _pf(cli, linea(paride=80002, partida_cod="CI.1.20"))
    a = _a(pf)
    assert (a.accion, a.paride, a.partida_cod, a.partida_metodo) == (
        "escribir", 80002, "CI.1.20", "manual")
    assert cli.presupuestos == [] and cli.lecturas == []
    assert cli.validadas == [[80002]]


def test_f055_r3_una_sola_validacion_por_peticion():
    cli = Cliente([])
    _pf(cli, linea(registro_id=1, paride=80002, partida_cod="CI.1.20"),
        linea(registro_id=2, recurso_ide=400, paride=80001,
              partida_cod="CI.1.10"),
        linea(registro_id=3, recurso_ide=400, nombre="Otro", categoria="X",
              **GUARDADA),
        linea(registro_id=4, es_postventa=True, paride=70002,
              partida_cod="0713"),
        linea(registro_id=5, recurso_ide=100, paride=80003))   # omitida
    assert cli.validadas == [[80001, 80002]]
    assert cli.obra_origen.ide not in cli.presupuestos     # solo la de PV
    assert cli.lecturas == []


def test_f055_r3_sin_partidas_no_valida():
    cli = Cliente([])
    _pf(cli, linea())
    assert cli.validadas == []


def test_f055_r3_la_elegida_manda_sobre_la_propuesta():
    cli = Cliente([])
    a = _a(_pf(cli, linea(paride=80001, partida_cod="CI.1.10", **GUARDADA)))
    assert (a.paride, a.partida_metodo, a.partida_origen) == (
        80001, "manual", None)
    assert cli.validadas == [[80001]]


# ======================= R4/R5 · la elegida no vale ====================== #
@pytest.mark.parametrize("paride", [80004, 80000, 70001, 12345],
                         ids=["baja", "capitulo", "otra_obra", "inexistente"])
def test_f055_r5_elegida_que_no_vale_se_omite(paride):
    cli = Cliente([])
    a = _a(_pf(cli, linea(paride=paride, partida_cod="X.1")))
    assert (a.accion, a.paride, a.partida_res) == ("omitir", 0, None)
    assert a.motivo == (
        "la partida X.1 elegida no es una partida hoja activa del "
        "presupuesto de la obra 0678: no se escribe; elige otra partida")
    assert cli.presupuestos == []


# ============== R6/R7 · propuesta que no vale y pendientes =============== #
@pytest.mark.parametrize("paride", [80004, 80000, 70001, 12345],
                         ids=["baja", "capitulo", "otra_obra", "inexistente"])
def test_f055_r6_propuesta_que_no_vale_se_recalcula(paride):
    cli = Cliente([_h()])
    a = _a(_pf(cli, linea(**dict(GUARDADA, propuesta_paride=paride))))
    assert (a.accion, a.paride, a.partida_metodo, a.partida_res) == (
        "escribir", 80003, "parte_anterior", "ADMINISTRATIVO")
    assert a.partida_origen == "parte PT26/00100 · 07/2026 · obra 0678"
    assert cli.presupuestos == [cli.obra_origen.ide]
    assert cli.lecturas == [([200], 202407, 202607)]


def test_f055_r7_pendientes_una_lectura_de_cada_y_solo_sus_recursos():
    cli = Cliente([])
    pf = _pf(cli, linea(registro_id=1),
             linea(registro_id=2, recurso_ide=400, nombre="Otro",
                   categoria="X", **GUARDADA),
             linea(registro_id=3, nombre="Nadie", categoria="Jefe de obra"))
    assert cli.presupuestos == [cli.obra_origen.ide]
    assert cli.lecturas == [([200], 202407, 202607)]
    assert [(a.paride, a.partida_metodo) for a in pf.acciones] == [
        (80001, "auto_nombre"), (80002, "parte_anterior"),
        (80002, "auto_categoria")]


# ================= R8 · la propuesta guardada que vale =================== #
def test_f055_r8_propuesta_guardada_valida_se_escribe_con_lo_guardado():
    cli = Cliente([_h()])
    pf = _pf(cli, linea(**GUARDADA))
    a = _a(pf)
    assert (a.accion, a.paride, a.partida_cod, a.partida_res,
            a.partida_metodo, a.partida_origen) == (
        "escribir", 80002, "CI.1.20", "JEFE DE OBRA (guardada)",
        "parte_anterior", "parte PT26/00050 · 05/2026 · obra 0678")
    assert a.aviso is None and pf.conflictos == []
    assert cli.presupuestos == [] and cli.lecturas == []


def test_f055_r8_ejecutar_inserta_la_propuesta_guardada():
    cli = Cliente([])
    r = RegistroPipeline(cliente=cli, settings=SettingsFalso()).ejecutar(
        obra=OBRA, lineas=[linea(**GUARDADA)])
    assert [i["paride"] for i in cli.inserts()] == [80002]
    assert r.escritas[0]["partida_cod"] == "CI.1.20"


# ============================ R9 · partida_res =========================== #
def test_f055_r9_toda_accion_con_partida_publica_su_descripcion():
    cli = Cliente([_h(recurso=400, paride=80001, cod="CI.1.10",
                      res="ENCARGADO (ACUNA)")])
    pf = _pf(cli,
             linea(registro_id=1, paride=80003, partida_cod="CI.1.9"),
             linea(registro_id=2, **GUARDADA),
             linea(registro_id=3, recurso_ide=400, nombre="Otro",
                   categoria="X"),
             linea(registro_id=4, nombre="Nadie Nunca",
                   categoria="Astronauta"),
             linea(registro_id=5, es_postventa=True),
             linea(registro_id=6, es_postventa=True, paride=70002,
                   partida_cod="0713"),
             linea(registro_id=7, recurso_ide=100))
    assert [(a.registro_id, a.paride, a.partida_res) for a in pf.acciones] \
        == [(1, 80003, "ADMINISTRATIVO"),
            (2, 80002, "JEFE DE OBRA (guardada)"),
            (3, 80001, "ENCARGADO (ACUNA)"),
            (4, 0, None),
            (5, 70001, "15 VIVIENDAS Y HOSTEL"),
            (6, 70002, "CLUB DEPORTIVO"),
            (7, 0, None)]
    assert "partida_res" in asdict(pf.acciones[0])


def test_f055_r9_la_var_publica_su_descripcion():
    from tests.test_f039_preflight_var import P29, _pf as pf_var
    a = pf_var().acciones[0]
    assert (a.paride, a.partida_metodo) == (P29, "var")
    assert a.partida_res


# ======================= R10 · partidas_obra ============================= #
def test_f055_r10_sin_pendientes_partidas_obra_vacio_y_sin_lectura():
    cli = Cliente([])
    pf = _pf(cli, linea(registro_id=1, paride=80002, partida_cod="CI.1.20"),
             linea(registro_id=2, recurso_ide=400, **GUARDADA))
    assert pf.partidas_obra == []
    assert cli.presupuestos == []


def test_f055_r10_con_una_pendiente_el_catalogo_de_hoy():
    cli = Cliente([])
    pf = _pf(cli, linea(registro_id=1, paride=80002, partida_cod="CI.1.20"),
             linea(registro_id=2, recurso_ide=400))
    assert [p["cod"] for p in pf.partidas_obra] == [
        "CI.1.9", "CI.1.10", "CI.1.20"]
    assert cli.presupuestos == [cli.obra_origen.ide]


# ===================== R12 · conflictos e idempotencia =================== #
def test_f055_r12_el_pisado_usa_la_partida_guardada():
    cli = Cliente([])
    cli.lineas_parte = [linea_previa(paride=80002, fecha_int=20260715)]
    pf = _pf(cli, linea(**GUARDADA))
    assert [c.clave for c in pf.conflictos] == ["200|202607|5|80002"]
    cli.lineas_parte = [linea_previa(paride=80001, fecha_int=20260715)]
    assert [c.motivo for c in _pf(cli, linea(**GUARDADA)).conflictos] == [
        "sobrecarga"]                       # otra partida: no es pisado


def test_f055_r12_ya_registrada_con_propuesta_guardada():
    from infrastructure.sigrid.sigrid_write_client import synckey_de
    cli = Cliente([])
    cli.synckeys = {synckey_de(1): linea_previa(ide=9001)}
    a = _a(_pf(cli, linea(**GUARDADA)))
    assert (a.accion, a.hmores_ide) == ("ya_registrado", 9001)


# ======================== el contrato HTTP (LineaIn) ===================== #
def test_f055_r8_la_linea_http_acepta_la_propuesta_guardada(monkeypatch):
    from types import SimpleNamespace

    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES
    cli = Cliente([])
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    api = TestClient(modulo_app.build_app(SimpleNamespace(**AJUSTES)))
    cuerpo = {"obra": {"codigo": "0678"}, "lineas": [
        {"registro_id": 1, "ano": 2026, "mes": 7, "porcentaje": 0.4,
         "recurso_ide": 200, "nombre": "Acuna Mera, Antonio",
         "categoria": "Encargado", "empresa": 1, **GUARDADA}]}
    r = api.post("/api/registro/preflight", json=cuerpo)
    assert r.status_code == 200, r.text
    [a] = r.json()["acciones"]
    assert (a["paride"], a["partida_cod"], a["partida_res"],
            a["partida_metodo"], a["partida_origen"]) == (
        80002, "CI.1.20", "JEFE DE OBRA (guardada)", "parte_anterior",
        "parte PT26/00050 · 05/2026 · obra 0678")


def test_f055_r8_la_linea_de_dominio_lleva_los_cinco_campos():
    l = LineaEntrada(registro_id=1, ano=2026, mes=7, porcentaje=0.5)
    assert (l.propuesta_paride, l.propuesta_cod, l.propuesta_res,
            l.propuesta_metodo, l.propuesta_origen) == (None,) * 5
