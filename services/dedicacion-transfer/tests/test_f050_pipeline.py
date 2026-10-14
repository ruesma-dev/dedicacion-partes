# tests/test_f050_pipeline.py
"""F-050 · La propuesta de partida dentro del preflight y del registro
(R7, R9, R10, R20, R21) y en modo pruebas.

El pipeline habla con el `ClienteFalso` de `conftest.py`, ampliado aquí con
un historial de líneas `M*` (`historial_partidas`) que anota cada lectura.
Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.propuesta_partida import LineaHistorial
from domain.models.registro_models import ObraEntrada

from tests.conftest import (
    EMPRESA,
    OBRA_ORIGEN,
    ClienteFalso,
    SettingsFalso,
    _fila,
    linea,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)
ORIGEN_IDE = 555001          # `obra_origen` del doble

#: Presupuesto de origen con hojas en desorden de código y una de baja.
PRESUPUESTO = [
    _fila(80000, 0, 0, "CI", "COSTES INDIRECTOS"),
    _fila(80001, 80000, 1, "CI.1.10", "ENCARGADO (ACUNA)"),
    _fila(80002, 80000, 2, "CI.1.20", "JEFE DE OBRA"),
    _fila(80003, 80000, 3, "CI.1.9", "ADMINISTRATIVO"),
    _fila(80004, 80000, 4, "CI.1.8", "VIGILANTE", tipdes=1),
]


def _h(*, recurso=200, obra=ORIGEN_IDE, mes=7, can=1.0, paride=80003,
       cod="CI.1.9", res="ADMINISTRATIVO") -> LineaHistorial:
    return LineaHistorial(reside=recurso, obride=obra, obra_cod="0678",
                          parte_cod="PT26/00100", ano=2026, mes=mes, can=can,
                          paride=paride, par_cod=cod, par_res=res)


class ClienteHistorial(ClienteFalso):
    """El doble de `conftest.py` con historial y presupuesto propios."""

    def __init__(self, historial=(), *, fallo=None, **kw) -> None:
        super().__init__(**kw)
        self.partidas_origen = PRESUPUESTO
        self.historial = list(historial)
        self.fallo = fallo
        self.lecturas: list[tuple] = []

    def historial_partidas(self, resides, desde, hasta):
        self.lecturas.append((sorted(resides), desde, hasta))
        if self.fallo is not None:
            raise self.fallo
        return list(self.historial)


def _pl(cli, **kw) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**kw))


def _accion(pf, registro_id=1):
    return next(a for a in pf.acciones if a.registro_id == registro_id)


# ======================= R9 · propuesta en el preflight =================== #
def test_f050_r9_la_automatica_es_la_propuesta_del_parte_anterior():
    cli = ClienteHistorial([_h()])
    a = _accion(_pl(cli).preflight(obra=OBRA, lineas=[linea()]))
    assert (a.accion, a.paride, a.partida_cod, a.partida_metodo) == (
        "escribir", 80003, "CI.1.9", "parte_anterior")
    assert a.partida_origen == "parte PT26/00100 · 07/2026 · obra 0678"
    assert a.aviso is None


def test_f050_r9_sin_historial_el_casamiento_de_siempre():
    cli = ClienteHistorial([])
    a = _accion(_pl(cli).preflight(obra=OBRA, lineas=[linea()]))
    assert (a.paride, a.partida_metodo, a.partida_origen) == (
        80001, "auto_nombre", None)


def test_f050_r9_sin_propuesta_sigue_sin_partida():
    cli = ClienteHistorial([])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(categoria="Astronauta", nombre="Nadie Nunca")])
    a = _accion(pf)
    assert (a.paride, a.partida_metodo) == (0, None)
    assert [c.motivo for c in pf.conflictos] == ["sin_partida"]


def test_f050_r7_una_sola_lectura_con_los_recursos_automaticos():
    cli = ClienteHistorial([_h(), _h(recurso=400, paride=80002,
                                     cod="CI.1.20", res="JEFE DE OBRA")])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1),
        linea(registro_id=2, recurso_ide=400, nombre="Otro", categoria="X"),
        linea(registro_id=3, paride=80001, partida_cod="CI.1.10"),
        linea(registro_id=4, es_postventa=True)])
    assert cli.lecturas == [([200, 400], 202407, 202607)]
    assert [(a.paride, a.partida_metodo) for a in pf.acciones] == [
        (80003, "parte_anterior"), (80002, "parte_anterior"),
        (80001, "manual"), (70001, "postventa")]


def test_f050_r7_ventana_del_ajuste_y_del_periodo():
    cli = ClienteHistorial([])
    _pl(cli, propuesta_meses_atras=3).preflight(
        obra=OBRA, lineas=[linea(ano=2026, mes=2)])
    assert cli.lecturas == [([200], 202511, 202602)]


@pytest.mark.parametrize("lineas", [
    [linea(paride=80001, partida_cod="CI.1.10")],
    [linea(es_postventa=True)],
    [linea(recurso_ide=100)],                       # sin M*: omitida
], ids=["manual", "postventa", "omitida"])
def test_f050_r7_sin_lineas_automaticas_no_se_lee_el_historial(lineas):
    cli = ClienteHistorial([_h()])
    _pl(cli).preflight(obra=OBRA, lineas=lineas)
    assert cli.lecturas == []


def test_f050_r7_si_la_lectura_falla_no_se_propone_ni_se_escribe():
    cli = ClienteHistorial(fallo=RuntimeError("sigrid-api devolvio una "
                                              "respuesta truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert cli.escritos == []


def test_f050_r9_ejecutar_escribe_la_propuesta():
    cli = ClienteHistorial([_h()])
    r = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert [i["paride"] for i in cli.inserts()] == [80003]
    assert r.escritas[0]["partida_cod"] == "CI.1.9"


def test_f050_modo_pruebas_el_historial_es_el_de_la_obra_de_origen():
    """En pruebas se escribe en la 0404, pero la propuesta sale de la obra de
    origen (sus partes y su presupuesto), no de la de pruebas."""
    cli = ClienteHistorial([_h(obra=cli_pruebas_ide(), paride=80002,
                               cod="CI.1.20", res="JEFE DE OBRA", mes=7),
                            _h(mes=6)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    assert pf.forzada_pruebas and pf.obra_destino.codigo == "0404"
    a = _accion(pf)
    assert (a.paride, a.partida_metodo) == (80003, "parte_anterior")


def cli_pruebas_ide() -> int:
    return ClienteFalso().obra.ide


# ============================ R20 · manual ================================ #
@pytest.mark.parametrize("paride, cod", [
    (80004, "CI.1.8"),          # hoja de baja
    (80000, "CI"),              # capítulo
    (12345, "X.9"),             # no es de esta obra
])
@pytest.mark.parametrize("forzar", [True, False])
def test_f050_r20_manual_que_no_es_hoja_activa_se_omite(paride, cod,
                                                        forzar):
    cli = ClienteHistorial([])
    pf = _pl(cli, obra_pruebas_forzar=forzar).preflight(
        obra=OBRA, lineas=[linea(paride=paride, partida_cod=cod)])
    a = _accion(pf)
    assert a.accion == "omitir"
    assert a.motivo == (
        f"la partida {cod} elegida no es una partida hoja activa del "
        "presupuesto de la obra 0678: no se escribe; elige otra partida")
    assert pf.conflictos == [] and a.aviso is None


def test_f050_r20_manual_sin_codigo_nombra_el_ide():
    cli = ClienteHistorial([])
    a = _accion(_pl(cli).preflight(obra=OBRA, lineas=[linea(paride=12345)]))
    assert a.motivo.startswith("la partida 12345 elegida no es")


def test_f050_r20_manual_hoja_activa_se_escribe():
    cli = ClienteHistorial([_h()])
    r = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(paride=80002, partida_cod="CI.1.20")])
    assert [i["paride"] for i in cli.inserts()] == [80002]
    assert r.omitidas == []


def test_f050_r20_ejecutar_no_escribe_la_manual_que_no_vale():
    cli = ClienteHistorial([])
    r = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(paride=80004, partida_cod="CI.1.8")])
    assert cli.inserts() == []
    assert [o["registro_id"] for o in r.omitidas] == [1]


# ============================= R21 · origen =============================== #
def test_f050_r21_cada_accion_publica_metodo_y_origen():
    cli = ClienteHistorial([_h()])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1),
        linea(registro_id=2, recurso_ide=400, paride=80002,
              partida_cod="CI.1.20")])
    publicadas = [asdict(a) for a in pf.acciones]
    assert [(p["partida_metodo"], p["partida_origen"]) for p in publicadas] \
        == [("parte_anterior", "parte PT26/00100 · 07/2026 · obra 0678"),
            ("manual", None)]


# ===================== R10 · catálogo del preflight ======================= #
def test_f050_r10_partidas_obra_en_orden_natural_sin_mayor():
    cli = ClienteHistorial([])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    assert pf.partidas_obra == [
        {"ide": 80003, "cod": "CI.1.9", "res": "ADMINISTRATIVO",
         "categoria": "CI"},
        {"ide": 80001, "cod": "CI.1.10", "res": "ENCARGADO (ACUNA)",
         "categoria": "CI"},
        {"ide": 80002, "cod": "CI.1.20", "res": "JEFE DE OBRA",
         "categoria": "CI"}]


def test_f050_r10_partidas_postventa_en_orden_natural():
    """`0656` y `656` empatan en el orden natural: decide el `ide`."""
    cli = ClienteHistorial([])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea(es_postventa=True)])
    assert [p["cod"] for p in pf.partidas_postventa] == [
        "11.01", "0656", "656", "0664", "664", "0678", "0713", "0998",
        "0999"]
    assert EMPRESA == 1 and "mayor" not in pf.partidas_postventa[0]


# ============ T15 · casos que la campaña de mutación dejó vivos ============ #
def test_f050_r7_el_historial_solo_lleva_los_recursos_automaticos():
    """Ni el de una línea de postventa, ni el de una manual, ni el de una
    omitida: solo los que van a llevar propuesta."""
    cli = ClienteHistorial([])
    _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1),
        linea(registro_id=2, recurso_ide=400, es_postventa=True),
        linea(registro_id=3, recurso_ide=400, paride=80001,
              partida_cod="CI.1.10"),
        linea(registro_id=4, recurso_ide=100)])
    assert cli.lecturas == [([200], 202407, 202607)]
