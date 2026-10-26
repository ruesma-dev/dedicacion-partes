# tests/test_f044_reglas_vinculados.py
"""F-044 · reglas puras de los recursos vinculados
(`application/services/reglas_vinculados.py`; design §6.2).

- R15 (T4): la partida del vinculado con un titular en una partida `CI*` de
  una obra normal: la elegida si es válida (si no, omitido con motivo); sin
  elegida, la ÚNICA hoja activa del presupuesto cuya cuenta tiene la
  subcuenta del vinculado (su «CI del tipo»).
- R16 (T4): sin esa hoja o con varias ⇒ sin partida con motivo (`sin_ci`,
  `varias_ci`), nunca la primera; un capítulo o una de baja no cuentan.
- R17 (T4): titular en postventa, VAR o partida no `CI*` (`CP*`, `CD*`) ⇒ la
  partida del titular, salvo elegida válida.

Sin red ni BBDD: las reglas no leen nada (la CI del tipo llega como
función y solo se llama si hace falta).
"""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from application.services.partida_resolver import construir_catalogo
from application.services.reglas_vinculados import (
    METODO_CI_TIPO,
    METODO_MANUAL,
    METODO_TITULAR,
    MOTIVO_ELEGIDA_NO_VALIDA,
    MOTIVO_SIN_CI,
    MOTIVO_VARIAS_CI,
    PartidaElegida,
    PartidaTitular,
    PartidaVinculado,
    partida_ci_del_tipo,
    partida_del_vinculado,
    va_con_el_titular,
)
from domain.models.registro_models import LineaEntrada, VinculadoEntrada

from tests.conftest import _fila

#: Presupuesto de una obra con el capítulo CI y sus hojas (ide inventados):
#: `CICO13` (teléfono), `CIGA14` (gasoil), dos hojas con la misma cuenta
#: `.CI.4.20`, una hoja de baja con `.CI.4.30`, y un capítulo con cuenta
#: `.CI.4.40` cuya única hija no la tiene.
PRESUPUESTO = [
    _fila(70000, 0, 0, "CI", "COSTES INDIRECTOS"),
    _fila(70001, 70000, 1, "CICO13", "TELEFONIA"),
    _fila(70002, 70000, 2, "CIGA14", "GASOIL"),
    _fila(70003, 70000, 3, "CIVE20", "VEHICULO A"),
    _fila(70004, 70000, 4, "CIVE21", "VEHICULO B"),
    _fila(70005, 70000, 5, "CIXX30", "DE BAJA", tipdes=1),
    _fila(70006, 70000, 6, "CI.9", "CAPITULO"),
    _fila(70007, 70006, 1, "CI.9.1", "HIJA"),
    _fila(70100, 0, 7, "CD", "COSTES DIRECTOS"),
    _fila(70101, 70100, 1, "CD.1", "HORMIGON"),
]
#: Cuenta (`con.cod` de `obrparpar.caaide`) de cada partida que la tiene.
CUENTAS = {
    70001: "0694.CI.4.13",
    70002: "0694.CI.4.14",
    70003: "0694.CI.4.20",
    70004: "0694.CI.4.20",
    70005: "0694.CI.4.30",
    70006: "0694.CI.4.40",
    70101: "0694.CD.1.1",
}


def _hojas():
    return construir_catalogo(PRESUPUESTO)


def _titular(destino: str = "obra", paride: int = 70009,
             cod: str | None = "CIJE01", res: str | None = "JEFE",
             metodo: str | None = "auto_nombre") -> PartidaTitular:
    return PartidaTitular(destino=destino, paride=paride, cod=cod, res=res,
                          metodo=metodo)


class _Ci:
    """La CI del tipo como función: apunta si se ha pedido."""

    def __init__(self, sub: str | None = "CI.4.13") -> None:
        self.llamadas = 0
        self.sub = sub

    def __call__(self) -> tuple[PartidaElegida | None, str]:
        self.llamadas += 1
        return partida_ci_del_tipo(_hojas(), CUENTAS, self.sub)


# ================================ R15 ==================================== #
@pytest.mark.parametrize("sub, esperado", [
    ("CI.4.13", 70001), ("CI.4.14", 70002), (" ci.4.13 ", 70001)])
def test_f044_r15_la_unica_hoja_con_la_subcuenta(sub, esperado):
    partida, metodo = partida_ci_del_tipo(_hojas(), CUENTAS, sub)
    assert metodo == METODO_CI_TIPO
    assert partida == PartidaElegida(
        paride=esperado, cod=_hojas()[esperado].cod,
        res=_hojas()[esperado].res)


def test_f044_r15_compara_la_subcuenta_entera():
    """`CI.4.1` no es `CI.4.13` ni `CI.4.14` (ni por prefijo)."""
    assert partida_ci_del_tipo(_hojas(), CUENTAS, "CI.4.1") == (
        None, MOTIVO_SIN_CI)
    assert partida_ci_del_tipo(_hojas(), CUENTAS, "4.13") == (
        None, MOTIVO_SIN_CI)


def test_f044_r15_titular_en_ci_sin_elegida_va_a_la_ci_del_tipo():
    ci = _Ci("CI.4.13")
    r = partida_del_vinculado(_titular(), None, True, ci)
    assert r == PartidaVinculado(paride=70001, cod="CICO13", res="TELEFONIA",
                                 metodo=METODO_CI_TIPO)
    assert ci.llamadas == 1
    assert not r.omitir and not r.sin_partida


def test_f044_r15_elegida_valida_manda():
    ci = _Ci()
    elegida = PartidaElegida(paride=70002, cod="CIGA14", res="GASOIL")
    r = partida_del_vinculado(_titular(), elegida, True, ci)
    assert r == PartidaVinculado(paride=70002, cod="CIGA14", res="GASOIL",
                                 metodo=METODO_MANUAL)
    assert ci.llamadas == 0


def test_f044_r15_elegida_no_valida_se_omite_con_motivo():
    ci = _Ci()
    elegida = PartidaElegida(paride=70006, cod="CI.9", res="CAPITULO")
    r = partida_del_vinculado(_titular(), elegida, False, ci)
    assert r.omitir and r.paride == 0 and r.metodo is None
    assert r.motivo == MOTIVO_ELEGIDA_NO_VALIDA.format(cod="CI.9")
    assert ci.llamadas == 0


def test_f044_r15_elegida_no_valida_sin_codigo_usa_el_ide():
    r = partida_del_vinculado(_titular(), PartidaElegida(paride=5), False,
                              _Ci())
    assert r.motivo == MOTIVO_ELEGIDA_NO_VALIDA.format(cod=5)


@pytest.mark.parametrize("cod", ["CIJE01", "ci.1", "CI", " CIX "])
def test_f044_r15_titular_ci_por_codigo(cod):
    assert va_con_el_titular(_titular(cod=cod)) is False


def test_f044_r15_titular_sin_partida_va_a_la_ci_del_tipo():
    """Un titular normal sin partida (pendiente de «sin partida») no tiene
    partida que heredar: el vinculado busca la suya."""
    t = _titular(paride=0, cod=None, res=None, metodo=None)
    assert va_con_el_titular(t) is False
    r = partida_del_vinculado(t, None, True, _Ci("CI.4.14"))
    assert (r.paride, r.metodo) == (70002, METODO_CI_TIPO)


# ================================ R16 ==================================== #
def test_f044_r16_varias_hojas_con_la_subcuenta_no_elige_ninguna():
    assert partida_ci_del_tipo(_hojas(), CUENTAS, "CI.4.20") == (
        None, MOTIVO_VARIAS_CI)
    r = partida_del_vinculado(_titular(), None, True, _Ci("CI.4.20"))
    assert r == PartidaVinculado(paride=0, motivo=MOTIVO_VARIAS_CI,
                                 sin_partida=True)
    assert not r.omitir


@pytest.mark.parametrize("sub", ["CI.4.99", None, ""])
def test_f044_r16_ninguna_hoja_con_la_subcuenta(sub):
    assert partida_ci_del_tipo(_hojas(), CUENTAS, sub) == (None,
                                                          MOTIVO_SIN_CI)
    r = partida_del_vinculado(_titular(), None, True, _Ci(sub))
    assert (r.paride, r.motivo, r.sin_partida, r.metodo) == (
        0, MOTIVO_SIN_CI, True, None)


@pytest.mark.parametrize("sub", ["CI.4.30", "CI.4.40"])
def test_f044_r16_capitulo_o_de_baja_no_cuentan(sub):
    """`CI.4.30` es de una hoja de baja; `CI.4.40`, de un capítulo."""
    assert partida_ci_del_tipo(_hojas(), CUENTAS, sub) == (None,
                                                          MOTIVO_SIN_CI)


def test_f044_r16_una_activa_y_otra_de_baja_con_la_misma_cuenta():
    cuentas = {**CUENTAS, 70005: "0694.CI.4.13"}
    partida, metodo = partida_ci_del_tipo(_hojas(), cuentas, "CI.4.13")
    assert (partida.paride, metodo) == (70001, METODO_CI_TIPO)


def test_f044_r16_partida_sin_cuenta_o_cuenta_sin_subcuenta():
    cuentas = {70001: "SINPUNTO", 70002: None}
    assert partida_ci_del_tipo(_hojas(), cuentas, "SINPUNTO") == (
        None, MOTIVO_SIN_CI)


def test_f044_r16_cuenta_de_una_partida_que_no_esta_en_el_presupuesto():
    assert partida_ci_del_tipo(_hojas(), {99999: "X.CI.4.13"},
                               "CI.4.13") == (None, MOTIVO_SIN_CI)


# ================================ R17 ==================================== #
@pytest.mark.parametrize("titular", [
    _titular(destino="postventa", paride=88001, cod="0694", res="OBRA PV",
             metodo="postventa"),
    _titular(paride=77001, cod="VAR-01", res="VARIOS", metodo="var"),
    _titular(paride=70101, cod="CD.1", res="HORMIGON"),
    _titular(paride=70200, cod="CP.2", res="PROPORCIONAL"),
    _titular(paride=70300, cod="01.02", res="OTRA"),
])
def test_f044_r17_va_con_la_partida_del_titular(titular):
    ci = _Ci()
    assert va_con_el_titular(titular) is True
    r = partida_del_vinculado(titular, None, True, ci)
    assert r == PartidaVinculado(paride=titular.paride, cod=titular.cod,
                                 res=titular.res, metodo=METODO_TITULAR)
    assert ci.llamadas == 0


def test_f044_r17_elegida_valida_manda_tambien_con_el_titular():
    titular = _titular(destino="postventa", paride=88001, cod="0694",
                       metodo="postventa")
    elegida = PartidaElegida(paride=88002, cod="0695", res="OTRA PV")
    r = partida_del_vinculado(titular, elegida, True, _Ci())
    assert (r.paride, r.metodo) == (88002, METODO_MANUAL)


def test_f044_r17_titular_postventa_sin_partida_hereda_el_cero():
    """Postventa decide siempre con el titular: si no tiene partida, el
    vinculado tampoco (no se busca la CI en otra obra)."""
    ci = _Ci()
    t = _titular(destino="postventa", paride=0, cod=None, res=None,
                 metodo="postventa")
    r = partida_del_vinculado(t, None, True, ci)
    assert (r.paride, r.metodo, ci.llamadas) == (0, METODO_TITULAR, 0)


# ============================ modelos (T4) =============================== #
def test_f044_r10_linea_entrada_sin_vinculados_por_defecto():
    a = LineaEntrada(registro_id=1, ano=2026, mes=10, porcentaje=1.0)
    b = LineaEntrada(registro_id=1, ano=2026, mes=10, porcentaje=1.0)
    assert a.vinculados == [] and a.vinculados is not b.vinculados


def test_f044_r10_vinculado_entrada_solo_exige_el_recurso():
    v = VinculadoEntrada(recurso_ide=10)
    assert (v.tipo, v.tipo_res, v.cod, v.categoria, v.paride, v.partida_cod,
            v.propuesta_paride, v.propuesta_cod, v.propuesta_res,
            v.propuesta_metodo, v.propuesta_origen, v.hmores_ide) == (
        None,) * 12


def test_f044_r15_resultados_inmutables():
    with pytest.raises(FrozenInstanceError):
        PartidaVinculado().paride = 3  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        _titular().paride = 3  # type: ignore[misc]


def test_f044_r15_las_reglas_no_leen_nada():
    """Sin I/O: el módulo no importa clientes, httpx ni infraestructura."""
    import application.services.reglas_vinculados as m

    arbol = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
    importados = {n.module or "" for n in ast.walk(arbol)
                  if isinstance(n, ast.ImportFrom)}
    importados |= {a.name for n in ast.walk(arbol)
                   if isinstance(n, ast.Import) for a in n.names}
    assert not any(i.startswith(("infrastructure", "httpx", "requests"))
                   for i in importados), importados


# ========================= T10 · la línea del vinculado ================== #
from application.services.reglas_porcentajes import (  # noqa: E402
    es_linea_mensual,
)
from application.services.reglas_vinculados import (  # noqa: E402
    MOTIVO_SIGUE_AL_TRABAJADOR,
    MOTIVO_SIN_IMPORTE,
    decidir_vinculados,
    es_linea_de,
    hora_del_vinculado,
    synckey_vinculado,
)
from domain.models.registro_models import (  # noqa: E402
    AccionLinea,
    AccionVinculado,
    HoraRecurso,
    LineaSigrid,
    ObraEntrada,
)

#: Horas de los vinculados (`ide` inventados): 10 teléfono, 11 gasoil (con
#: otra hora que no es la suya), 12 vehículo `MESVE`, 13 km con `pre` 0, 14
#: sin hora por defecto.
HORAS = {
    10: [HoraRecurso(31, "OTEL", None, 30.0, caa_cod="R.CI.4.13",
                     defecto=True)],
    11: [HoraRecurso(32, "HLPE", None, 1.0),
         HoraRecurso(33, "OGAS", None, 120.0, defecto=True)],
    12: [HoraRecurso(34, "MESVE", None, 300.0, defecto=True)],
    13: [HoraRecurso(35, "OKM", None, 0.0, defecto=True)],
    14: [HoraRecurso(36, "OTEL", None, 30.0)],
}


def _accion(**kw) -> AccionLinea:
    datos = dict(registro_id=12, accion="escribir", ano=2026, mes=10,
                 fecha_int=20261031, nombre="Acuna Mera, Antonio",
                 recurso_ide=200, hora_ide=5, hora_codigo="MENC", can=0.6,
                 pre=9000.0, tot=5400.0, destino="obra", paride=80001,
                 partida_cod="CI.1.10")
    datos.update(kw)
    return AccionLinea(**datos)


def _con(*ides: int) -> LineaEntrada:
    return LineaEntrada(registro_id=12, ano=2026, mes=10, porcentaje=0.6,
                        recurso_ide=200, vinculados=[
                            VinculadoEntrada(recurso_ide=i, tipo="TF",
                                             tipo_res="TELEFONO",
                                             cod=f"TF-{i}") for i in ides])


def test_f044_r13_synckey_exacta():
    from infrastructure.sigrid.sigrid_write_client import (
        PREFIJO_SYNCKEY,
        synckey_de,
    )
    assert synckey_vinculado(12, 10) == "porcentajes:vin:12:10"
    assert synckey_vinculado("12", "10") == "porcentajes:vin:12:10"
    assert synckey_vinculado(12, 10).startswith(PREFIJO_SYNCKEY)
    assert synckey_vinculado(12, 10) != synckey_de(12)


@pytest.mark.parametrize("horas, esperada", [
    (HORAS[10], 31), (HORAS[11], 33), (HORAS[12], 34)])
def test_f044_r14_la_hora_por_defecto(horas, esperada):
    assert hora_del_vinculado(horas).horide == esperada


@pytest.mark.parametrize("horas", [HORAS[13], HORAS[14], []])
def test_f044_r14_sin_hora_por_defecto_o_pre_cero_no_hay_hora(horas):
    assert hora_del_vinculado(horas) is None


def test_f044_r12_can_y_fec_del_titular_pre_y_tot_suyos():
    [a, b, c] = decidir_vinculados(_accion(), _con(10, 11, 12), HORAS)
    assert a == AccionVinculado(
        registro_id=12, recurso_ide=10, accion="escribir", ano=2026, mes=10,
        fecha_int=20261031, tipo="TF", tipo_res="TELEFONO", cod="TF-10",
        nombre="Acuna Mera, Antonio", hora_ide=31, hora_codigo="OTEL",
        can=0.6, pre=30.0, tot=18.0, destino="obra")
    assert (b.hora_codigo, b.pre, b.tot) == ("OGAS", 120.0, 72.0)
    assert (c.hora_codigo, c.pre, c.tot) == ("MESVE", 300.0, 180.0)
    assert {x.can for x in (a, b, c)} == {0.6}


@pytest.mark.parametrize("destino, metodo", [
    ("obra", "auto_nombre"), ("postventa", "postventa"), ("obra", "var")])
def test_f044_r12_sin_normalizar_en_normal_postventa_y_var(destino, metodo):
    """60 % normal + 40 % en otra ⇒ el vinculado, 60 % y 40 %."""
    normal = decidir_vinculados(_accion(can=0.6), _con(10), HORAS)
    otra = decidir_vinculados(
        _accion(registro_id=13, can=0.4, destino=destino,
                partida_metodo=metodo), _con(10), HORAS)
    assert [(v.can, v.destino) for v in normal + otra] == [
        (0.6, "obra"), (0.4, destino)]
    assert normal[0].fecha_int == otra[0].fecha_int == 20261031


def test_f044_r12_tot_redondeado_como_stmt_insert_linea():
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
    cli = SigridWriteClient(base_url="http://x.invalid", function_key="k",
                            database="ruesma")
    [v] = decidir_vinculados(_accion(can=0.3333), _con(10), HORAS)
    st = cli.stmt_insert_linea(
        hmoide=1, obra=ObraEntrada(ide=1), reside=10, pos=1,
        fecha_int=v.fecha_int,
        horide=v.hora_ide, can=v.can, pre=v.pre, ano=2026, mes=10,
        synckey="s", tex=None)
    assert v.tot == st["parameters"][10] == 10.0       # el `tot` del INSERT


@pytest.mark.parametrize("ide, hora", [(13, "OKM"), (14, "sin hora")])
def test_f044_r14_omitido_sin_importe_mensual_con_tipo_y_hora(ide, hora):
    titular = _accion()
    [v] = decidir_vinculados(titular, _con(ide), HORAS)
    assert v.accion == "omitir"
    assert v.motivo == MOTIVO_SIN_IMPORTE.format(tipo="TF", cod=f"TF-{ide}",
                                                 hora=hora)
    assert "sin importe mensual" in v.motivo and "TF" in v.motivo
    assert hora in v.motivo
    assert titular == _accion()                     # el titular no cambia


def test_f044_r18_titular_omitido_sus_vinculados_siguen_al_trabajador():
    titular = _accion(accion="omitir", motivo="sin código mensual")
    vs = decidir_vinculados(titular, _con(10, 11), HORAS)
    assert [(v.accion, v.motivo) for v in vs] == [
        ("omitir", MOTIVO_SIGUE_AL_TRABAJADOR.format(
            motivo="sin código mensual"))] * 2
    assert "sigue al trabajador" in vs[0].motivo


def test_f044_r18_titular_ya_registrado_cada_vinculado_se_decide_solo():
    vs = decidir_vinculados(_accion(accion="ya_registrado", hmores_ide=9),
                            _con(10, 13), HORAS)
    assert [v.accion for v in vs] == ["escribir", "omitir"]
    assert vs[0].hmores_ide is None


def test_f044_r12_sin_vinculados_nada():
    assert decidir_vinculados(_accion(), _con(), HORAS) == []


def _ls(hora: str, reside: int = 12) -> LineaSigrid:
    return LineaSigrid(ide=1, reside=reside, fecha_int=20261031, horide=1,
                       hora_codigo=hora, can=0.0, tot=0.0, synckey=None)


def test_f044_r19_es_linea_de_solo_su_hora():
    assert es_linea_de("MESVE")(_ls("MESVE"))
    assert es_linea_de("mesve ")(_ls(" MESVE"))
    assert not es_linea_de("MESVE")(_ls("MENC"))
    assert not es_linea_de("OTEL")(_ls("OTELX"))
    # La trampa: una MESVE empieza por M; la jornada del trabajador
    # (`es_linea_mensual`) la contaría si no fuera por el recurso.
    assert es_linea_mensual(_ls("MESVE"))
