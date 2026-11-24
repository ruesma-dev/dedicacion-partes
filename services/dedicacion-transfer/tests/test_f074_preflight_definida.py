# tests/test_f074_preflight_definida.py
"""F-074 · T2-T4: al registrar, la partida ya viene DEFINIDA (R1-R7, R23;
C1 y C2 de design §8).

- R1: el preflight no propone ni casa: elegida, propuesta guardada o, en
  postventa, la de su obra (la que manda la api como `propuesta_*`).
- R2: cada subfila, su elegida, la de su titular (postventa, VAR o no
  `CI*`) o su propuesta guardada de método propio; sin leer nada.
- R3: todas se validan por `ide` en la lectura única (`validar_partidas`),
  la de postventa contra la obra de postventa.
- R4: la definida que no vale se omite nombrándola (`partida_no_valida`).
- R5: sin definida, la normal y la subfila van al conflicto «sin partida»
  (confirmable, D8 a); la de postventa se omite con su motivo.
- R6/R23: ni presupuestos de origen o de postventa, ni historial, ni
  cuentas; `partidas_obra` y `partidas_postventa`, `[]`.
- R7: cada obra de un lote da lo mismo que su petición suelta.
- C1: un lote de 10 obras sin ninguna partida definida no lee presupuesto,
  historial ni cuentas. C2: uno con postventa lee la obra de postventa y no
  su presupuesto.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.partida_definida import (
    MOTIVO_GUARDADA_VINCULADO_NO_VALIDA,
    MOTIVO_PROPUESTA_NO_VALIDA,
    MOTIVO_PROPUESTA_PV_NO_VALIDA,
    MOTIVO_PV_SIN_DEFINIDA,
    POR_QUE_SIN_DEFINIDA,
    DefinidaVinculado,
    partida_definida_del_vinculado,
)
from application.services.propuesta_partida import Propuesta
from application.services.reglas_porcentajes import (
    AVISO_SIN_PARTIDA,
    MOTIVO_PARTIDA_PV_NO_HOJA,
    clave_sin_partida,
)
from application.services.reglas_vinculados import (
    MOTIVO_ELEGIDA_NO_VALIDA,
    PartidaElegida,
    PartidaTitular,
    PartidaVinculado,
    clave_sin_partida_vinculado,
)
from domain.models.registro_models import ObraEntrada, VinculadoEntrada
from interface_adapters.api.app import _respuesta_preflight

from tests.conftest import OBRA_ORIGEN, SettingsFalso, linea
from tests.test_f044_pipeline_vinculados import ClienteVin
from tests.test_f050_pipeline import OBRA, ClienteHistorial, _h
from tests.test_f055_lecturas_lote import ClienteQueAnota
from tests.test_f055_lote import ClienteObras, _ajustes, _obra

#: La propuesta guardada de una línea de obra normal (80002, CI.1.20).
GUARDADA = {"propuesta_paride": 80002, "propuesta_cod": "CI.1.20",
            "propuesta_res": "JEFE DE OBRA", "propuesta_metodo":
            "auto_nombre"}
#: La partida de postventa de la obra 0678 que manda la api (F-074 R12):
#: 70001 «0678» en el presupuesto de la obra de postventa del doble.
PV_0678 = {"propuesta_paride": 70001, "propuesta_cod": "0678",
           "propuesta_res": "15 VIVIENDAS Y HOSTEL",
           "propuesta_metodo": "postventa"}
LECTURAS_DE_LA_REGLA = {"capitulos_de_obra", "historial_partidas",
                        "historial_de_vinculados", "cuentas_del_presupuesto"}


class Cliente(ClienteHistorial):
    """Anota también las lecturas de presupuesto y de cuentas."""

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.presupuestos: list[int] = []
        self.cuentas: list[int] = []
        self.historial_vin: list[int] = []

    def capitulos_de_obra(self, obride):
        self.presupuestos.append(int(obride))
        return super().capitulos_de_obra(obride)

    def cuentas_del_presupuesto(self, obra_ide):
        self.cuentas.append(int(obra_ide))
        return {}

    def historial_de_vinculados(self, resides, obra_ide, desde, hasta):
        self.historial_vin.append(int(obra_ide))
        return []

    def sin_lecturas_de_la_regla(self) -> bool:
        return not (self.presupuestos or self.lecturas or self.cuentas
                    or self.historial_vin)


def _pf(cli, *lineas, **ajustes):
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes)) \
        .preflight(obra=OBRA, lineas=list(lineas))


def _a(pf, registro_id=1):
    return next(a for a in pf.acciones if a.registro_id == registro_id)


# ======================= R1 · la línea, definida ========================= #
def test_f074_r1_sin_definida_no_se_propone_aunque_casaria():
    """`linea()` casaría por nombre con CI.1.10 y su historial daría
    CI.1.9: el preflight no mira ninguno de los dos."""
    cli = Cliente([_h()])
    pf = _pf(cli, linea())
    a = _a(pf)
    assert (a.accion, a.paride, a.partida_metodo, a.aviso) == (
        "escribir", 0, None, AVISO_SIN_PARTIDA)
    assert cli.sin_lecturas_de_la_regla()


def test_f074_r1_la_guardada_se_escribe_tal_cual():
    cli = Cliente([_h()])
    a = _a(_pf(cli, linea(**GUARDADA)))
    assert (a.accion, a.paride, a.partida_cod, a.partida_metodo) == (
        "escribir", 80002, "CI.1.20", "auto_nombre")
    assert cli.sin_lecturas_de_la_regla() and cli.validadas == [[80002]]


def test_f074_r1_la_elegida_manda_sobre_la_guardada():
    cli = Cliente([])
    a = _a(_pf(cli, linea(paride=80001, partida_cod="CI.1.10", **GUARDADA)))
    assert (a.paride, a.partida_metodo) == (80001, "manual")
    assert cli.validadas == [[80001]]


def test_f074_r1_postventa_escribe_la_de_su_obra_sin_casar():
    cli = Cliente([])
    pf = _pf(cli, linea(es_postventa=True, **PV_0678))
    a = _a(pf)
    assert (a.accion, a.destino, a.paride, a.partida_cod, a.partida_res,
            a.partida_metodo) == ("escribir", "postventa", 70001, "0678",
                                  "15 VIVIENDAS Y HOSTEL", "postventa")
    assert cli.sin_lecturas_de_la_regla()
    assert pf.capitulo_postventa == {"ide": 70001, "cod": "0678",
                                     "res": "15 VIVIENDAS Y HOSTEL"}


def test_f074_r1_postventa_escribe_la_definida_aunque_casaria_otra():
    """La de la obra 0678 casaría con 70001: si la definida es 70002, el
    preflight escribe 70002 (lo que enseña la celda)."""
    cli = Cliente([])
    a = _a(_pf(cli, linea(es_postventa=True, propuesta_paride=70002,
                          propuesta_cod="0713", propuesta_metodo="postventa")))
    assert (a.accion, a.paride, a.partida_cod) == ("escribir", 70002, "0713")


def test_f074_r1_postventa_con_elegida():
    cli = Cliente([])
    a = _a(_pf(cli, linea(es_postventa=True, paride=70002, partida_cod="0713",
                          **PV_0678)))
    assert (a.paride, a.partida_metodo, a.partida_res) == (
        70002, "manual", "CLUB DEPORTIVO")


# ================= R3 · validadas por `ide`, en una lectura ============== #
def test_f074_r3_una_sola_validacion_con_las_de_postventa():
    cli = Cliente([])
    _pf(cli, linea(registro_id=1, **GUARDADA),
        linea(registro_id=2, recurso_ide=400, es_postventa=True, **PV_0678),
        linea(registro_id=3, recurso_ide=400, paride=80001,
              partida_cod="CI.1.10"))
    assert cli.validadas == [[70001, 80001, 80002]]


def test_f074_r3_la_de_postventa_se_valida_contra_la_obra_de_postventa():
    """80002 es hoja activa, pero de la obra de origen: no vale en
    postventa."""
    cli = Cliente([])
    a = _a(_pf(cli, linea(es_postventa=True, propuesta_paride=80002,
                          propuesta_cod="CI.1.20",
                          propuesta_metodo="postventa")))
    assert (a.accion, a.partida_no_valida) == ("omitir", "CI.1.20")


# ===================== R4 · la definida que no vale ====================== #
@pytest.mark.parametrize("paride", [80004, 80000, 70001, 12345],
                         ids=["baja", "capitulo", "otra_obra", "inexistente"])
def test_f074_r4_guardada_que_no_vale_se_omite_nombrandola(paride):
    cli = Cliente([_h()])
    a = _a(_pf(cli, linea(**dict(GUARDADA, propuesta_paride=paride))))
    assert (a.accion, a.paride, a.partida_no_valida) == (
        "omitir", 0, "CI.1.20")
    assert a.motivo == MOTIVO_PROPUESTA_NO_VALIDA.format(cod="CI.1.20",
                                                          obra=OBRA_ORIGEN)
    assert cli.sin_lecturas_de_la_regla()


def test_f074_r4_guardada_sin_codigo_se_nombra_por_su_ide():
    a = _a(_pf(Cliente([]), linea(propuesta_paride=12345,
                                  propuesta_metodo="auto_nombre")))
    assert a.partida_no_valida == "12345"
    assert "la partida 12345 propuesta" in a.motivo


def test_f074_r4_elegida_que_no_vale_tambien_lleva_su_codigo():
    a = _a(_pf(Cliente([]), linea(paride=80004, partida_cod="CI.1.8")))
    assert (a.accion, a.partida_no_valida) == ("omitir", "CI.1.8")


@pytest.mark.parametrize("paride", [69100, 69000, 80001, 12345],
                         ids=["capitulo", "raiz", "de_otra_obra",
                              "inexistente"])
def test_f074_r4_postventa_guardada_que_no_vale(paride):
    cli = Cliente([])
    a = _a(_pf(cli, linea(es_postventa=True, propuesta_paride=paride,
                          propuesta_cod="X.9", propuesta_metodo="postventa")))
    assert (a.accion, a.partida_no_valida) == ("omitir", "X.9")
    assert a.motivo == MOTIVO_PROPUESTA_PV_NO_VALIDA.format(cod="X.9")
    assert cli.sin_lecturas_de_la_regla()


def test_f074_r4_postventa_guardada_de_baja_con_su_codigo():
    cli = Cliente([], presupuesto_postventa="hojas_inactivas")
    a = _a(_pf(cli, linea(es_postventa=True, **PV_0678)))
    assert (a.accion, a.partida_no_valida) == ("omitir", "0678")
    assert a.motivo == MOTIVO_PROPUESTA_PV_NO_VALIDA.format(cod="0678")


def test_f074_r4_postventa_elegida_que_no_vale_el_motivo_de_siempre():
    cli = Cliente([])
    a = _a(_pf(cli, linea(es_postventa=True, paride=69100, **PV_0678)))
    assert (a.accion, a.partida_no_valida) == ("omitir", "11")
    assert a.motivo == MOTIVO_PARTIDA_PV_NO_HOJA.format(paride="11")


def test_f074_r4_sin_partida_no_valida_en_las_demas():
    pf = _pf(Cliente([]), linea(registro_id=1, **GUARDADA),
             linea(registro_id=2, recurso_ide=100, **GUARDADA))
    assert [a.partida_no_valida for a in pf.acciones] == [None, None]
    assert _a(pf, 2).accion == "omitir"         # sin M*: otro motivo


# ======================= R5 · sin partida definida ======================= #
def test_f074_r5_normal_sin_definida_es_el_conflicto_sin_partida():
    pf = _pf(Cliente([]), linea())
    assert [(c.motivo, c.clave) for c in pf.conflictos] == [
        ("sin_partida", clave_sin_partida(_a(pf)))]


def test_f074_r5_d8_confirmada_se_escribe_sin_partida():
    cli = Cliente([])
    pl = RegistroPipeline(cliente=cli, settings=SettingsFalso())
    pf = pl.preflight(obra=OBRA, lineas=[linea()])
    res = pl.ejecutar(obra=OBRA, lineas=[linea()],
                      pisar_claves=[c.clave for c in pf.conflictos])
    assert [i["paride"] for i in cli.inserts()] == [0]
    assert res.escritas


def test_f074_r5_postventa_sin_definida_se_omite_con_motivo():
    cli = Cliente([])
    a = _a(_pf(cli, linea(es_postventa=True)))
    assert (a.accion, a.motivo) == ("omitir", MOTIVO_PV_SIN_DEFINIDA)
    assert cli.sin_lecturas_de_la_regla()


def test_f074_r5_postventa_sin_obra_de_postventa_el_motivo_de_la_obra():
    cli = Cliente([], obra_postventa_existe=False)
    a = _a(_pf(cli, linea(es_postventa=True, **PV_0678)))
    assert a.accion == "omitir" and "no encontrada" in a.motivo


# ==================== R2 · la subfila, definida ========================== #
class ClienteVinAnota(ClienteVin):
    """`ClienteVin` que apunta el historial de los vinculados."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.historial_vin: list[int] = []
        self.presupuestos: list[int] = []

    def historial_de_vinculados(self, resides, obra_ide, desde, hasta):
        self.historial_vin.append(int(obra_ide))
        return []

    def capitulos_de_obra(self, obride):
        self.presupuestos.append(int(obride))
        return super().capitulos_de_obra(obride)


def _v(recurso=10, **kw) -> VinculadoEntrada:
    return VinculadoEntrada(recurso_ide=recurso, tipo="TF", cod=f"TF-{recurso}",
                            **kw)


def _vin_de(pf, recurso=10):
    return next(v for v in pf.vinculados if v.recurso_ide == recurso)


def _pf_vin(cli, *lineas):
    return RegistroPipeline(cliente=cli, settings=SettingsFalso()).preflight(
        obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=list(lineas))


def test_f074_r2_subfila_con_guardada_propia_sin_leer_nada():
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(**GUARDADA, vinculados=[_v(
        propuesta_paride=81001, propuesta_cod="CICO13",
        propuesta_res="TELEFONIA", propuesta_metodo="ci_tipo")]))
    v = _vin_de(pf)
    assert (v.accion, v.paride, v.partida_metodo) == ("escribir", 81001,
                                                      "ci_tipo")
    assert cli.cuentas_leidas == [] and cli.historial_vin == []
    assert cli.presupuestos == []


def test_f074_r2_subfila_sin_definida_va_al_conflicto_aunque_casaria():
    """El vinculado 10 casaría con CICO13 por su cuenta: no se busca."""
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(**GUARDADA, vinculados=[_v()]))
    v = _vin_de(pf)
    assert (v.accion, v.paride) == ("escribir", 0)
    assert POR_QUE_SIN_DEFINIDA in v.aviso
    assert clave_sin_partida_vinculado(1, 10) in [c.clave
                                                  for c in pf.conflictos]
    assert cli.cuentas_leidas == [] and cli.historial_vin == []


def test_f074_r2_subfila_guardada_de_metodo_titular_no_cuenta():
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(**GUARDADA, vinculados=[_v(
        propuesta_paride=80002, propuesta_cod="CI.1.20",
        propuesta_metodo="titular")]))
    assert _vin_de(pf).paride == 0


def test_f074_r2_subfila_va_con_su_titular_no_ci():
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(paride=81101, partida_cod="CD.1",
                            vinculados=[_v()]))
    v = _vin_de(pf)
    assert (v.paride, v.partida_metodo) == (81101, "titular")


def test_f074_r2_subfila_bajo_postventa_va_con_su_titular():
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(es_postventa=True, **PV_0678,
                            vinculados=[_v()]))
    v = _vin_de(pf)
    assert (v.destino, v.paride, v.partida_metodo) == ("postventa", 70001,
                                                       "titular")
    assert cli.presupuestos == []


def test_f074_r2_subfila_elegida_bajo_postventa_se_valida_en_la_lectura():
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(es_postventa=True, **PV_0678,
                            vinculados=[_v(paride=70002, partida_cod="0713")]))
    assert (_vin_de(pf).paride, _vin_de(pf).partida_metodo) == (70002,
                                                                "manual")
    assert cli.validadas == [[70001, 70002]] and cli.presupuestos == []


def test_f074_r4_subfila_guardada_que_no_vale_se_omite_nombrandola():
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(**GUARDADA, vinculados=[_v(
        propuesta_paride=81100, propuesta_cod="CD",
        propuesta_metodo="ci_tipo")]))
    v = _vin_de(pf)
    assert (v.accion, v.partida_no_valida) == ("omitir", "CD")
    assert v.motivo == MOTIVO_GUARDADA_VINCULADO_NO_VALIDA.format(cod="CD")


def test_f074_r4_subfila_elegida_que_no_vale_lleva_su_codigo():
    cli = ClienteVinAnota()
    pf = _pf_vin(cli, linea(**GUARDADA, vinculados=[_v(
        paride=81100, partida_cod="CD")]))
    v = _vin_de(pf)
    assert (v.accion, v.partida_no_valida) == ("omitir", "CD")
    assert v.motivo == MOTIVO_ELEGIDA_NO_VALIDA.format(cod="CD")


# ============ R2 · `partida_definida_del_vinculado`, pura ================ #
CI = PartidaTitular(destino="obra", paride=80002, cod="CI.1.20")
GUARDADA_VIN = Propuesta(81001, "CICO13", "TELEFONIA", "ci_tipo")


@pytest.mark.parametrize("titular, elegida, e_ok, guardada, g_ok, esperado", [
    (CI, PartidaElegida(7, "X"), True, GUARDADA_VIN, True,
     DefinidaVinculado(PartidaVinculado(paride=7, cod="X", metodo="manual"))),
    (CI, PartidaElegida(7, None), False, None, True, DefinidaVinculado(
        PartidaVinculado(motivo=MOTIVO_ELEGIDA_NO_VALIDA.format(cod="7"),
                         omitir=True), no_valida="7")),
    (PartidaTitular(destino="postventa", paride=5, cod="P"), None, True,
     GUARDADA_VIN, True, DefinidaVinculado(PartidaVinculado(
         paride=5, cod="P", metodo="titular"))),
    (PartidaTitular(destino="obra", paride=6, cod="CD.1"), None, True,
     GUARDADA_VIN, True, DefinidaVinculado(PartidaVinculado(
         paride=6, cod="CD.1", metodo="titular"))),
    (PartidaTitular(destino="obra", paride=0, metodo="var"), None, True,
     GUARDADA_VIN, True, DefinidaVinculado(PartidaVinculado(
         paride=0, metodo="titular"))),
    (CI, None, True, GUARDADA_VIN, True, DefinidaVinculado(PartidaVinculado(
        paride=81001, cod="CICO13", res="TELEFONIA", metodo="ci_tipo"))),
    (CI, None, True, GUARDADA_VIN, False, DefinidaVinculado(
        PartidaVinculado(motivo=MOTIVO_GUARDADA_VINCULADO_NO_VALIDA.format(
            cod="CICO13"), omitir=True), no_valida="CICO13")),
    (CI, None, True, Propuesta(81001, "CICO13", None, "titular"), True,
     DefinidaVinculado(PartidaVinculado(motivo=POR_QUE_SIN_DEFINIDA,
                                        sin_partida=True))),
    (PartidaTitular(destino="obra", paride=0), None, True, None, True,
     DefinidaVinculado(PartidaVinculado(motivo=POR_QUE_SIN_DEFINIDA,
                                        sin_partida=True))),
], ids=["elegida", "elegida_no_vale", "postventa", "no_ci", "var",
        "guardada", "guardada_no_vale", "guardada_de_titular", "nada"])
def test_f074_r2_definida_del_vinculado(titular, elegida, e_ok, guardada,
                                        g_ok, esperado):
    assert partida_definida_del_vinculado(titular, elegida, e_ok, guardada,
                                          g_ok) == esperado


# ======================== R6 · nada de la regla ========================== #
def test_f074_r6_sin_catalogos_en_la_respuesta():
    pf = _pf(Cliente([]), linea(), linea(registro_id=2, es_postventa=True,
                                         **PV_0678))
    r = _respuesta_preflight(pf)
    assert (r["partidas_obra"], r["partidas_postventa"]) == ([], [])


# ===================== R7 · el lote, como la suelta ====================== #
def test_f074_r7_lote_igual_que_suelta_con_todos_los_casos():
    lineas = [linea(registro_id=1), linea(registro_id=2, **GUARDADA),
              linea(registro_id=3, recurso_ide=400, es_postventa=True,
                    **PV_0678),
              linea(registro_id=4, recurso_ide=400, propuesta_paride=80004,
                    propuesta_cod="CI.1.8", propuesta_metodo="auto_nombre"),
              linea(registro_id=5, recurso_ide=400, es_postventa=True)]
    suelta = _pf(Cliente([]), *lineas)
    [lote] = RegistroLote(cliente=Cliente([]), settings=_ajustes()).preflight(
        [(OBRA, lineas)])
    assert _respuesta_preflight(lote) == _respuesta_preflight(suelta)


# ============================ C1 y C2 ==================================== #
def test_f074_c1_diez_obras_sin_definida_no_leen_la_regla():
    cli = ClienteObras(10)
    lote = RegistroLote(cliente=cli, settings=_ajustes()).preflight(
        [(_obra(i), [linea(registro_id=i)]) for i in range(1, 11)])
    assert all(type(r).__name__ == "Preflight" for r in lote)
    assert not LECTURAS_DE_LA_REGLA & set(cli.nombres())
    assert all(_a(r, i).paride == 0 for i, r in enumerate(lote, start=1))


def test_f074_c2_postventa_lee_su_obra_y_no_su_presupuesto():
    cli = ClienteQueAnota()
    [r] = RegistroLote(cliente=cli, settings=_ajustes()).preflight([(
        ObraEntrada(ide=555001, codigo=OBRA_ORIGEN),
        [linea(es_postventa=True, **PV_0678)])])
    assert ("obra_por_codigo", "POSTV2", 1) in cli.llamadas
    assert "capitulos_de_obra" not in cli.nombres()
    assert _a(r).paride == 70001
    assert asdict(_a(r))["partida_no_valida"] is None
