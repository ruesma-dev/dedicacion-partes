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
