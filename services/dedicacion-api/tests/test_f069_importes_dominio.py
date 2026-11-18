# tests/test_f069_importes_dominio.py
"""F-069 · T5: tipos de cantidad, su validación y la config (R1, R2, R5).

- `config.yaml` (`sync.vinculados.importes` y `precio_km`): `CAJA` en € por
  obra, `VIAJE` en € por %, `VP` en km por %, 0,20 €/km (D1, D2, D10, D12).
  Unidad o reparto desconocidos, o `precio_km` ≤ 0, y la api no arranca.
- `tipo_de`: una sola función decide tipo, unidad y reparto (tipo sin
  espacios, en mayúsculas); fuera de la lista, None.
- `validar_cantidad`: ≥ 0, dos decimales como mucho, topes por unidad; un
  booleano o un texto que no es número no valen. `validar_comentario`: sin
  espacios a los lados, vacío ⇒ None, > 200 ⇒ inválido.
- `a_copiar` (R8) y `comentario_de_sigrid` (R32).

Sin red ni BBDD.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from application.sync_pipeline import ConfigVinculados
from config.settings import cargar_config
from domain.errors import ImporteInvalido
from domain.importes import (
    COMENTARIO_MAX,
    TOPES,
    TipoCantidad,
    a_copiar,
    comentario_de_sigrid,
    tipo_de,
    tipos_de_config,
    validar_cantidad,
    validar_comentario,
)

CAJA = TipoCantidad(unidad="eur", reparto="obra")
VIAJE = TipoCantidad(unidad="eur", reparto="pct")
VP = TipoCantidad(unidad="km", reparto="pct")


# ================================ R1 ===================================== #
def test_f069_r1_config_versionada():
    cfg = ConfigVinculados.desde_config(cargar_config()["sync"]["vinculados"])
    assert cfg.importes == {"CAJA": CAJA, "VIAJE": VIAJE, "VP": VP}
    assert cfg.precio_km == Decimal("0.20")


def _cfg(**kw) -> dict:
    base = {"campo": "5", "desde": "2026-10", "sql": "SELECT 1",
            "importes": {"CAJA": {"unidad": "eur", "reparto": "obra"}},
            "precio_km": 0.2}
    base.update(kw)
    return base


@pytest.mark.parametrize("importes", [
    {"CAJA": {"unidad": "usd", "reparto": "obra"}},
    {"CAJA": {"unidad": "eur", "reparto": "linea"}},
    {"CAJA": {"unidad": "eur"}},
    {"CAJA": "eur"},
    ["CAJA"],
    {" ": {"unidad": "eur", "reparto": "obra"}},
])
def test_f069_r1_mal_escrita_no_arranca(importes):
    with pytest.raises(ValueError):
        ConfigVinculados.desde_config(_cfg(importes=importes))


@pytest.mark.parametrize("precio", [0, -0.2, "x", True, "NaN"])
def test_f069_r1_precio_km_no_positivo_no_arranca(precio):
    with pytest.raises(ValueError):
        ConfigVinculados.desde_config(_cfg(precio_km=precio))


def test_f069_r1_un_tipo_en_km_sin_precio_km_no_arranca():
    with pytest.raises(ValueError, match="precio_km"):
        ConfigVinculados.desde_config(_cfg(
            importes={"VP": {"unidad": "km", "reparto": "pct"}},
            precio_km=None))


def test_f069_r1_sin_importes_ninguno_de_cantidad():
    cfg = ConfigVinculados.desde_config(_cfg(importes=None, precio_km=None))
    assert cfg.importes == {} and cfg.precio_km is None


def test_f069_r1_tipos_de_config_normaliza_la_clave():
    assert tipos_de_config({" vp ": {"unidad": "KM", "reparto": " PCT "}}) == {
        "VP": VP}


# ================================ R2 ===================================== #
@pytest.mark.parametrize("tipo, esperado", [
    ("CAJA", CAJA), ("caja", CAJA), (" VP ", VP), ("V P", VP),
    ("VIAJE", VIAJE), ("TF", None), (None, None), ("", None)])
def test_f069_r2_tipo_de(tipo, esperado):
    assert tipo_de(tipo, {"CAJA": CAJA, "VIAJE": VIAJE, "VP": VP}) == esperado


# ================================ R5 ===================================== #
@pytest.mark.parametrize("valor, esperado", [
    (0, Decimal("0.00")), (12.3, Decimal("12.30")), ("45.6", Decimal("45.60")),
    (Decimal("999999.99"), Decimal("999999.99")), (None, None)])
def test_f069_r5_cantidad_valida_en_eur(valor, esperado):
    assert validar_cantidad(valor, "eur") == esperado


@pytest.mark.parametrize("valor", [
    -0.01, 1.234, "12,5", "x", True, False, 1000000, "NaN", "Infinity",
    [], {}])
def test_f069_r5_cantidad_invalida(valor):
    with pytest.raises(ImporteInvalido):
        validar_cantidad(valor, "eur")


def test_f069_r5_topes_por_unidad():
    assert TOPES == {"eur": Decimal("999999.99"), "km": Decimal("99999.99")}
    assert validar_cantidad(99999.99, "km") == Decimal("99999.99")
    with pytest.raises(ImporteInvalido):
        validar_cantidad(100000, "km")
    assert validar_cantidad(100000, "eur") == Decimal("100000.00")


def test_f069_r5_comentario():
    assert COMENTARIO_MAX == 200
    assert validar_comentario(None) is None
    assert validar_comentario("   ") is None
    assert validar_comentario("  visita  ") == "visita"
    assert validar_comentario("x" * 200) == "x" * 200
    with pytest.raises(ImporteInvalido):
        validar_comentario("x" * 201)
    with pytest.raises(ImporteInvalido):
        validar_comentario(12)


# ============================ R8 y R32 =================================== #
def test_f069_r8_a_copiar_solo_lo_que_falta_en_el_destino():
    assert a_copiar({1: "a", 2: "b"}, {2: "x"}) == {1: "a"}
    assert a_copiar({}, {2: "x"}) == {}
    assert a_copiar({1: "a"}, {}) == {1: "a"}


@pytest.mark.parametrize("tex, esperado", [
    ("PRUEBA-PORC visita", "visita"), ("PRUEBA-PORC", None),
    ("  visita  ", "visita"), ("", None), (None, None),
    ("visita PRUEBA-PORC", "visita PRUEBA-PORC")])
def test_f069_r32_comentario_de_sigrid(tex, esperado):
    assert comentario_de_sigrid(tex, "PRUEBA-PORC") == esperado


def test_f069_r32_comentario_de_sigrid_sin_marca():
    assert comentario_de_sigrid(" PRUEBA-PORC x ", None) == "PRUEBA-PORC x"
