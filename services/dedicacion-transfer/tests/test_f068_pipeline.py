# tests/test_f068_pipeline.py
"""F-068 · el pipeline con la partida del vinculado como la del trabajador
(design §2, §6.2; requirements R11-R18).

- R18 (T1): el contrato de entrada gana `descripcion` (registro y
  propuesta) y `tipo_res` (propuesta), opcionales; sin ellos, la entrada de
  hoy.
- R1, R11-R14, R16 (T6): el preflight decide la partida del vinculado con
  el historial en la obra (UNA lectura por petición, con todos sus
  vinculados, solo si alguno llega a ese paso), las cuentas solo si alguno
  llega al de la cuenta, y escribe tal cual la propuesta guardada con un
  método propio.

Fixture «de la 0678» con `ide` inventados: el teléfono 20 (`CICO13`), el
gasoil 21 (`CICO01`) y el vehículo 22 (`CIMP09`) tienen su cuenta en DOS
hojas, una del `CI.0` (o `CI.03P`) y otra del `CI.4`; su historial en la
obra dice `CI.4.13` y `CI.4.1`; el vehículo no tiene historial.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.propuesta_partida import LineaHistorial
from application.services.reglas_vinculados import (
    AVISO_SIN_PARTIDA_VINCULADO,
    MOTIVO_VARIAS_CI,
    por_que_sin_ci,
)
from domain.models.registro_models import HoraRecurso, VinculadoEntrada
from interface_adapters.api.app import (
    LineaPropuestaIn,
    VinculadoIn,
    VinculadoPropuestaIn,
)

from tests.test_f044_pipeline_vinculados import api  # noqa: F401
from tests.conftest import OBRA_ORIGEN, _fila, linea
from tests.test_f044_pipeline_vinculados import (
    CUENTAS_VIN,
    HORAS_VIN,
    PRESUPUESTO_VIN,
    ClientePre,
    ClienteVin,
    _cuerpo,
    _linea,
    _pf,
    _por,
)
from tests.test_f044_sql_vinculados import (  # noqa: F401
    _cuerpo_registro,
    ruta_espiada,
)


# ================================ R18 ==================================== #
def test_f068_r18_vinculado_de_registro_con_descripcion():
    v = VinculadoIn(recurso_ide=10, tipo="TF", tipo_res="TELEFONO",
                    descripcion="MOVIL 600")
    assert v.descripcion == "MOVIL 600"
    assert VinculadoEntrada(**v.model_dump()).descripcion == "MOVIL 600"


def test_f068_r18_sin_descripcion_la_entrada_de_hoy():
    assert VinculadoIn(recurso_ide=10).descripcion is None
    assert VinculadoEntrada(recurso_ide=10).descripcion is None


def test_f068_r18_la_ruta_de_registro_pasa_la_descripcion(ruta_espiada):
    cliente, recibidas = ruta_espiada
    r = cliente.post("/api/registro/preflight", json=_cuerpo_registro(
        vinculados=[{"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
                     "cod": "TF-10", "descripcion": "MOVIL 600"}]))
    assert r.status_code == 200
    [[l]] = recibidas
    assert l.vinculados == [VinculadoEntrada(
        recurso_ide=10, tipo="TF", tipo_res="TELEFONO", cod="TF-10",
        descripcion="MOVIL 600")]


def test_f068_r18_vinculado_de_propuesta_con_tipo_res_y_descripcion():
    l = LineaPropuestaIn(clave="a", recurso_ide=200, vinculados=[
        VinculadoPropuestaIn(recurso_ide=10, tipo="TF", cod="TF-10",
                             tipo_res="TELEFONO", descripcion="MOVIL 600")])
    assert l.para_pipeline()["vinculados"] == [{
        "recurso_ide": 10, "tipo": "TF", "categoria": None, "cod": "TF-10",
        "tipo_res": "TELEFONO", "descripcion": "MOVIL 600"}]


@pytest.mark.parametrize("extra, esperado", [
    ({}, {}),
    ({"tipo_res": "TELEFONO"}, {"tipo_res": "TELEFONO"}),
    ({"descripcion": "MOVIL"}, {"descripcion": "MOVIL"}),
])
def test_f068_r18_sin_ellos_la_entrada_de_propuesta_de_hoy(extra, esperado):
    """Lo que no llega no viaja: el dict del pipeline es el de F-044 más
    solo lo que la api mandó."""
    l = LineaPropuestaIn(clave="a", recurso_ide=200, vinculados=[
        VinculadoPropuestaIn(recurso_ide=10, tipo="TF", cod="TF-10",
                             **extra)])
    assert l.para_pipeline()["vinculados"] == [{
        "recurso_ide": 10, "tipo": "TF", "categoria": None, "cod": "TF-10",
        **esperado}]


def test_f068_r18_la_ruta_de_propuesta_pasa_tipo_res_y_descripcion(
        api, monkeypatch):  # noqa: F811
    recibidas: list[list[dict]] = []
    original = RegistroPipeline.proponer

    def espia(self, **kw):
        recibidas.append(kw["lineas"])
        return original(self, **kw)

    monkeypatch.setattr(RegistroPipeline, "proponer", espia)
    vin = [{"recurso_ide": 10, "tipo": "TF", "categoria": None,
            "cod": "TF-10", "tipo_res": "TELEFONO",
            "descripcion": "MOVIL 600"}]
    r = api(ClienteVin()).post("/api/partidas/propuesta", json=_cuerpo(
        _linea(vinculados=vin)))
    assert r.status_code == 200
    assert recibidas == [[{**_linea(), "vinculados": vin}]]


# ============================ fixture 0678 =============================== #
PRESUPUESTO_68 = [
    *PRESUPUESTO_VIN,
    _fila(82000, 80000, 20, "CI.0", "CAPITULO 0"),
    _fila(82013, 82000, 1, "CI.0.13", "TELEFONIA"),
    _fila(82001, 82000, 2, "CI.0.01", "COMBUSTIBLE"),
    _fila(82006, 82000, 3, "CI.0.06", "VEHICULOS"),
    _fila(82400, 80000, 21, "CI.4", "CAPITULO 4"),
    _fila(82413, 82400, 1, "CI.4.13", "TELEFONIA"),
    _fila(82401, 82400, 2, "CI.4.1", "COMBUSTIBLE"),
    _fila(82300, 80000, 22, "CI.03P", "CAPITULO 3P"),
    _fila(82309, 82300, 1, "CI.03P.9", "VEHICULOS"),
    _fila(82500, 80000, 23, "CI.5", "PERSONAL"),
    _fila(82502, 82500, 1, "CI.5.2", "TELEFONO MOVIL ENCARGADO"),
]
CUENTAS_68 = {**CUENTAS_VIN,
              82013: "0678.CICO13", 82413: "0678.CICO13",
              82001: "0678.CICO01", 82401: "0678.CICO01",
              82006: "0678.CIMP09", 82309: "0678.CIMP09"}
#: 20 teléfono, 21 gasoil, 22 vehículo; 23, un teléfono sin cuenta en el
#: presupuesto (`CIZZ99`).
HORAS_68 = {
    20: [HoraRecurso(41, "OTEL", None, 30.0, caa_cod="RES.CICO13",
                     defecto=True)],
    21: [HoraRecurso(42, "OGAS", None, 120.0, caa_cod="RES.CICO01",
                     defecto=True)],
    22: [HoraRecurso(43, "MESVE", None, 300.0, caa_cod="RES.CIMP09",
                     defecto=True)],
    23: [HoraRecurso(44, "OTEL", None, 30.0, caa_cod="RES.CIZZ99",
                     defecto=True)],
}
OBRA_IDE = 555001
VENTANA = (202407, 202607)


def _h(recurso: int, paride: int, mes: int = 6, can: float = 1.0, *,
       ano: int = 2026, obra: int = OBRA_IDE,
       parte: str = "PT26/00300") -> LineaHistorial:
    """Una línea de `historial_de_vinculados` con su forma real (los alias
    de la SQL pasados por `_linea_historial`)."""
    n = {f["ide"]: f for f in PRESUPUESTO_68}[paride]
    return LineaHistorial(reside=recurso, obride=obra, obra_cod=OBRA_ORIGEN,
                          parte_cod=parte, ano=ano, mes=mes, can=can,
                          paride=paride, par_cod=n["cod"], par_res=n["res"])


#: El historial del caso: el teléfono en `CI.4.13` (y antes en `CI.0.13`),
#: el gasoil en `CI.4.1`; el vehículo, nada.
HISTORIAL_0678 = [_h(20, 82413, 6), _h(20, 82013, 5), _h(21, 82401, 6)]


class Cliente68(ClientePre):
    """`ClientePre` con el presupuesto y las cuentas de la 0678 y el
    historial de los vinculados (cada lectura, apuntada). Como la SQL: solo
    los recursos pedidos, en la obra pedida y en la ventana."""

    def __init__(self, *, historial=HISTORIAL_0678, falla=None,
                 **kw) -> None:
        super().__init__(**kw)
        self.partidas_origen = PRESUPUESTO_68
        self.horas = {**self.horas, **HORAS_68}
        self.historial = list(historial)
        self.falla = falla
        self.historial_leido: list[tuple] = []

    def cuentas_del_presupuesto(self, obra_ide):
        self.cuentas_leidas.append(int(obra_ide))
        return dict(CUENTAS_68) if obra_ide == self.obra_origen.ide else {}

    def historial_de_vinculados(self, resides, obra_ide, desde, hasta):
        self.historial_leido.append((sorted(resides), int(obra_ide),
                                     int(desde), int(hasta)))
        if self.falla is not None:
            raise self.falla
        return [l for l in self.historial
                if l.reside in set(resides) and l.obride == int(obra_ide)
                and desde <= l.ano * 100 + l.mes <= hasta]


def _v68(*ides: int, **kw) -> list[VinculadoEntrada]:
    tipos = {20: "TF", 21: "CO", 22: "VE", 23: "TF"}
    return [VinculadoEntrada(recurso_ide=i, tipo=tipos[i],
                             tipo_res={"TF": "TELEFONO", "CO": "GASOIL",
                                       "VE": "VEHICULO"}[tipos[i]],
                             cod=f"{tipos[i]}-{i}", **kw) for i in ides]


def _partidas(pf) -> dict:
    return {r: (v.paride, v.partida_cod, v.partida_metodo, v.partida_origen)
            for (_, r), v in _por(pf).items()}


ORIGEN = f"parte PT26/00300 · 06/2026 · obra {OBRA_ORIGEN}"


# ============================ R1 · preflight ============================= #
def test_f068_r1_preflight_el_caso_de_la_0678():
    """El caso pedido: el teléfono y el gasoil, a la partida de su
    historial con «parte anterior» y su origen; el vehículo (sin historial,
    ninguna del CI.4), sin partida."""
    cli = Cliente68()
    pf = _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                        vinculados=_v68(20, 21, 22)))
    assert _partidas(pf) == {
        20: (82413, "CI.4.13", "parte_anterior", ORIGEN),
        21: (82401, "CI.4.1", "parte_anterior", ORIGEN),
        22: (0, None, None, None)}
    v = _por(pf)
    assert v[(1, 20)].partida_res == "TELEFONIA"
    assert v[(1, 22)].aviso == AVISO_SIN_PARTIDA_VINCULADO.format(
        tipo="VE", cod="VE-22", por_que=por_que_sin_ci(MOTIVO_VARIAS_CI))
    assert [c.clave for c in pf.conflictos
            if c.motivo == "sin_partida"] == ["sin_partida:1:22"]


def test_f068_r7_preflight_sin_historial_decide_el_ci4():
    cli = Cliente68(historial=[])
    pf = _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                        vinculados=_v68(20, 21, 22)))
    assert _partidas(pf) == {
        20: (82413, "CI.4.13", "capitulo_ci4", None),
        21: (82401, "CI.4.1", "capitulo_ci4", None),
        22: (0, None, None, None)}


def test_f068_r18_preflight_casa_con_tipo_res_y_descripcion():
    """Sin su cuenta en el presupuesto: el nombre entre las `CI*`, con la
    descripción del tipo y la del recurso que manda la api."""
    pf = _pf(Cliente68(historial=[]), linea(
        paride=80001, partida_cod="CI.1.10",
        vinculados=_v68(23, descripcion="TELEFONO MOVIL ENCARGADO")))
    assert _partidas(pf) == {23: (82502, "CI.5.2", "auto_nombre", None)}
    sin = _pf(Cliente68(historial=[]), linea(
        paride=80001, partida_cod="CI.1.10",
        vinculados=[VinculadoEntrada(recurso_ide=23, tipo="TF",
                                     cod="TF-23")]))
    assert _partidas(sin) == {23: (0, None, None, None)}


def test_f068_r1_preflight_titular_automatico_tambien():
    """El titular sin elegida (su propuesta, en `CI*`): igual."""
    pf = _pf(Cliente68(), linea(vinculados=_v68(20)))
    assert pf.acciones[0].partida_cod == "CI.1.10"
    assert _partidas(pf)[20] == (82413, "CI.4.13", "parte_anterior", ORIGEN)


# ======================= R11-R14 · las lecturas ========================== #
def test_f068_r11_una_lectura_de_historial_con_todos_los_vinculados():
    cli = Cliente68()
    _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                   vinculados=_v68(22, 20)),
        linea(registro_id=2, recurso_ide=201, paride=80001,
              partida_cod="CI.1.10", vinculados=_v68(21)))
    assert cli.historial_leido == [([20, 21, 22], OBRA_IDE, *VENTANA)]


def test_f068_r2_d3_la_ventana_incluye_el_periodo():
    """D3-A: la del trabajador, con el periodo que se registra (julio)."""
    cli = Cliente68(historial=[*HISTORIAL_0678, _h(20, 82013, 7)])
    pf = _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                        vinculados=_v68(20)))
    assert _partidas(pf)[20][:3] == (82013, "CI.0.13", "parte_anterior")
    fuera = Cliente68(historial=[_h(20, 82013, 6, ano=2024),
                                 _h(20, 82401, 7, ano=2024)])
    pf = _pf(fuera, linea(paride=80001, partida_cod="CI.1.10",
                          vinculados=_v68(20)))
    assert _partidas(pf)[20][:3] == (82401, "CI.4.1", "parte_anterior")


def test_f068_r11_solo_la_obra_de_origen():
    cli = Cliente68(historial=[_h(20, 82013, 6, obra=999)])
    pf = _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                        vinculados=_v68(20)))
    assert _partidas(pf)[20][2] == "capitulo_ci4"


def test_f068_r12_cuentas_solo_si_alguno_llega_a_la_cuenta():
    cli = Cliente68()
    _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                   vinculados=_v68(20, 21)))
    assert cli.cuentas_leidas == []
    cli = Cliente68()
    _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                   vinculados=_v68(20, 21, 22)))
    assert cli.cuentas_leidas == [OBRA_IDE]
    assert len(cli.historial_leido) == 1


def test_f068_r14_sin_vinculados_ni_historial_ni_cuentas():
    cli = Cliente68()
    _pf(cli, linea(paride=80001, partida_cod="CI.1.10"))
    assert (cli.historial_leido, cli.cuentas_leidas) == ([], [])


def test_f068_r14_todos_resueltos_antes_las_lecturas_de_hoy():
    """Elegida, propuesta guardada válida o titular en una `CD`: ni
    historial ni cuentas."""
    cli = Cliente68()
    cli.horas[201] = cli.horas[200]
    pf = _pf(cli, linea(paride=80001, partida_cod="CI.1.10", vinculados=[
        *_v68(20, paride=82013, partida_cod="CI.0.13"),
        *_v68(21, propuesta_paride=82001, propuesta_cod="CI.0.01",
              propuesta_res="COMBUSTIBLE", propuesta_metodo="ci_tipo")]),
        linea(registro_id=2, recurso_ide=201, paride=81101,
              partida_cod="CD.1", vinculados=_v68(22)))
    assert (cli.historial_leido, cli.cuentas_leidas) == ([], [])
    assert _partidas(pf) == {
        20: (82013, "CI.0.13", "manual", None),
        21: (82001, "CI.0.01", "ci_tipo", None),
        22: (81101, "CD.1", "titular", None)}


def test_f068_r13_si_el_historial_falla_el_preflight_falla():
    cli = Cliente68(falla=RuntimeError(
        "sigrid-api devolvio una respuesta truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                       vinculados=_v68(20)))
    assert cli.escritos == []


# ==================== R16 · la propuesta guardada ======================== #
@pytest.mark.parametrize("metodo", [
    "parte_anterior", "ci_tipo", "auto_nombre", "auto_categoria",
    "capitulo_ci4"])
def test_f068_r16_guardada_con_metodo_propio_se_escribe_tal_cual(metodo):
    """F-055 R8: lo que enseña el cuadrante, sin leer historial ni
    cuentas, aunque el historial dijera otra."""
    cli = Cliente68()
    pf = _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                        vinculados=_v68(20, propuesta_paride=82013,
                                        propuesta_cod="CI.0.13",
                                        propuesta_res="TELEFONIA",
                                        propuesta_metodo=metodo,
                                        propuesta_origen="guardado")))
    assert _partidas(pf)[20] == (82013, "CI.0.13", metodo, "guardado")
    assert _por(pf)[(1, 20)].partida_res == "TELEFONIA"
    assert (cli.historial_leido, cli.cuentas_leidas) == ([], [])


@pytest.mark.parametrize("metodo, paride", [
    ("titular", 82013), ("manual", 82013), (None, 82013),
    ("parte_anterior", 82000), ("parte_anterior", 99999)])
def test_f068_r16_la_que_no_vale_o_de_titular_se_recalcula(metodo, paride):
    cli = Cliente68()
    pf = _pf(cli, linea(paride=80001, partida_cod="CI.1.10",
                        vinculados=_v68(20, propuesta_paride=paride,
                                        propuesta_cod="X",
                                        propuesta_metodo=metodo)))
    assert _partidas(pf)[20] == (82413, "CI.4.13", "parte_anterior", ORIGEN)
    assert len(cli.historial_leido) == 1


def test_f068_r16_con_el_titular_la_guardada_no_cuenta():
    pf = _pf(Cliente68(), linea(paride=81101, partida_cod="CD.1",
                                vinculados=_v68(20, propuesta_paride=82013,
                                                propuesta_cod="CI.0.13",
                                                propuesta_metodo="parte_anterior")))
    assert _partidas(pf)[20] == (81101, "CD.1", "titular", None)


def test_f068_r16_sin_res_guardado_usa_el_validado():
    pf = _pf(Cliente68(), linea(paride=80001, partida_cod="CI.1.10",
                                vinculados=_v68(20, propuesta_paride=82013,
                                                propuesta_cod="CI.0.13",
                                                propuesta_metodo="auto_nombre")))
    assert _por(pf)[(1, 20)].partida_res == "TELEFONIA"
