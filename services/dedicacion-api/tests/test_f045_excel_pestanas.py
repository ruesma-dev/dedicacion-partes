# tests/test_f045_excel_pestanas.py
"""Tests offline de F-045: el Excel desglosado en «Obras» y «Postventa».

Dos niveles (specs/F-045-excel-obras-postventa/design.md §7):

  - Contenido (`grupos_pestana` de `infrastructure/excel/contenido.py`):
    qué líneas lleva el grupo de cada trabajador en cada pestaña y la línea
    agregada con la otra parte (R4-R12, R18).
  - Libro (`infrastructure/excel/exporter.py`): hojas, formato, combinadas,
    bandas y cursiva de la agregada (R1-R3, R13-R17).

Los cinco trabajadores son los del prototipo (design §5), con nombres y
obras inventados. Sin red, sin BBDD y sin ficheros: el libro vive en memoria.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from domain.models import CuadranteTrabajador
from infrastructure.excel.contenido import (
    AGREGADA_EN_OBRAS,
    AGREGADA_EN_POSTVENTA,
    grupos_detalle,
    grupos_pestana,
)

from tests.test_f040_excel import _fila, _linea

_PREFIJO = "Postv-"
_OBRAS, _POSTVENTA = False, True


def _muestra() -> list[CuadranteTrabajador]:
    """ALFA obras y postventa (OK), BETA solo obras (FALTA 10 %), GAMMA solo
    postventa (OK), DELTA sin carga y EPSILON VAR + dos postventas (EXCESO)."""
    return [
        _fila(1, "ALFA PRUEBA UNO",
              _linea("0101", "Obra Ficticia Norte", "60"),
              _linea("0102", "Obra Ficticia Sur", "25"),
              _linea("0702", "Hotel Inventado", "15", postventa=True)),
        _fila(2, "BETA PRUEBA DOS",
              _linea("0101", "Obra Ficticia Norte", "50"),
              _linea("0103", "Obra Ficticia Este", "40")),
        _fila(3, "GAMMA PRUEBA TRES",
              _linea("0702", "Hotel Inventado", "70", postventa=True),
              _linea("0704", "Residencia Inventada", "30", postventa=True),
              categoria=None),
        _fila(4, "DELTA PRUEBA CUATRO"),
        _fila(5, "EPSILON PRUEBA CINCO",
              _linea("VAR-29", "Varios partida 29", "60"),
              _linea("0702", "Hotel Inventado", "30", postventa=True),
              _linea("0705", "Nave Inventada", "20", postventa=True)),
    ]


def _por_nombre(postventa: bool, filas=None, prefijo=_PREFIJO) -> dict:
    filas = _muestra() if filas is None else filas
    return {g.empleado: g for g in grupos_pestana(filas, prefijo, postventa)}


def _filas(grupo) -> list[tuple]:
    return [(ln.codigo, ln.obra, ln.porcentaje, ln.agregada)
            for ln in grupo.lineas]


# ----------------------------------------------------------------------
# Contenido
# ----------------------------------------------------------------------
def test_f045_r4_mismos_trabajadores_y_orden_en_las_dos_pestanas():
    for filas in (_muestra(), list(reversed(_muestra()))):
        esperado = [f.trabajador.nombre for f in filas]
        obras = grupos_pestana(filas, _PREFIJO, _OBRAS)
        postv = grupos_pestana(filas, _PREFIJO, _POSTVENTA)
        assert [g.empleado for g in obras] == esperado
        assert [g.empleado for g in postv] == esperado
        assert [g.categoria for g in obras] == [g.categoria for g in postv]


def test_f045_r5_obras_lleva_sus_lineas_en_orden_con_var_como_obra():
    obras = _por_nombre(_OBRAS)
    assert _filas(obras["BETA PRUEBA DOS"]) == [
        ("0101", "Obra Ficticia Norte", Decimal(50), False),
        ("0103", "Obra Ficticia Este", Decimal(40), False)]
    var = obras["EPSILON PRUEBA CINCO"].lineas[0]
    assert (var.codigo, var.obra, var.nombre, var.porcentaje, var.agregada) == (
        "VAR-29", "Varios partida 29", "Varios partida 29", Decimal(60), False)
    # Postventa intercalada: las obras conservan su orden relativo, sin reordenar.
    omega = _fila(9, "OMEGA",
                  _linea("0200", "B", "40"),
                  _linea("0100", "Pv", "20", postventa=True),
                  _linea("0150", "A", "40"))
    [g] = grupos_pestana([omega], _PREFIJO, _OBRAS)
    assert [ln.codigo for ln in g.lineas] == ["0200", "0150", "POSTVENTA"]


def test_f045_r6_postventa_lleva_sus_lineas_en_orden_con_prefijo():
    postv = _por_nombre(_POSTVENTA)
    gamma = postv["GAMMA PRUEBA TRES"]
    assert _filas(gamma) == [
        ("Postv-0702", "Postv-Hotel Inventado", Decimal(70), False),
        ("Postv-0704", "Postv-Residencia Inventada", Decimal(30), False)]
    assert gamma.lineas[0].nombre == "Hotel Inventado"
    assert [ln.codigo for ln in postv["EPSILON PRUEBA CINCO"].lineas] == [
        "Postv-0702", "Postv-0705", "OBRAS"]


def test_f045_r7_agregada_unica_al_final_con_rotulos_y_suma():
    assert AGREGADA_EN_OBRAS == ("POSTVENTA", "RESTO POSTVENTA")
    assert AGREGADA_EN_POSTVENTA == ("OBRAS", "RESTO OBRAS")
    obras, postv = _por_nombre(_OBRAS), _por_nombre(_POSTVENTA)
    alfa_o, alfa_p = obras["ALFA PRUEBA UNO"], postv["ALFA PRUEBA UNO"]
    assert _filas(alfa_o) == [
        ("0101", "Obra Ficticia Norte", Decimal(60), False),
        ("0102", "Obra Ficticia Sur", Decimal(25), False),
        ("POSTVENTA", "RESTO POSTVENTA", Decimal(15), True)]
    assert _filas(alfa_p) == [
        ("Postv-0702", "Postv-Hotel Inventado", Decimal(15), False),
        ("OBRAS", "RESTO OBRAS", Decimal(85), True)]
    assert alfa_o.lineas[-1].nombre == "" and alfa_p.lineas[-1].nombre == ""
    # La suma es de TODAS las líneas de la otra parte.
    eps_o = obras["EPSILON PRUEBA CINCO"]
    assert _filas(eps_o)[-1] == ("POSTVENTA", "RESTO POSTVENTA", Decimal(50), True)
    assert _filas(postv["EPSILON PRUEBA CINCO"])[-1] == (
        "OBRAS", "RESTO OBRAS", Decimal(60), True)
    # Una sola agregada por grupo, y siempre la última.
    for grupos in (obras, postv):
        for g in grupos.values():
            marcas = [ln.agregada for ln in g.lineas]
            assert sum(marcas) <= 1
            assert True not in marcas[:-1]


def test_f045_r7_suma_exacta_en_decimal():
    fila = _fila(6, "THETA",
                 _linea("0101", "A", "33.33"),
                 _linea("0702", "B", "10.1", postventa=True),
                 _linea("0703", "C", "20.2", postventa=True),
                 _linea("0102", "D", "36.37"))
    [obras] = grupos_pestana([fila], _PREFIJO, _OBRAS)
    [postv] = grupos_pestana([fila], _PREFIJO, _POSTVENTA)
    resto_pv, resto_ob = obras.lineas[-1], postv.lineas[-1]
    assert isinstance(resto_pv.porcentaje, Decimal)
    assert resto_pv.porcentaje == Decimal("30.3")      # no 30.299999…
    assert isinstance(resto_ob.porcentaje, Decimal)
    assert resto_ob.porcentaje == Decimal("69.70")


def test_f045_r8_sin_la_otra_parte_no_hay_agregada():
    obras, postv = _por_nombre(_OBRAS), _por_nombre(_POSTVENTA)
    beta, gamma = obras["BETA PRUEBA DOS"], postv["GAMMA PRUEBA TRES"]
    for g in (beta, gamma):
        assert not any(ln.agregada for ln in g.lineas)
        assert len(g.lineas) == 2
    assert "POSTVENTA" not in [ln.codigo for ln in beta.lineas]
    assert "OBRAS" not in [ln.codigo for ln in gamma.lineas]


def test_f045_r9_solo_la_otra_parte_una_fila_agregada():
    obras, postv = _por_nombre(_OBRAS), _por_nombre(_POSTVENTA)
    assert _filas(obras["GAMMA PRUEBA TRES"]) == [
        ("POSTVENTA", "RESTO POSTVENTA", Decimal(100), True)]
    assert _filas(postv["BETA PRUEBA DOS"]) == [
        ("OBRAS", "RESTO OBRAS", Decimal(90), True)]


def test_f045_r10_sin_carga_una_fila_vacia_en_cada_pestana():
    for postventa in (_OBRAS, _POSTVENTA):
        delta = _por_nombre(postventa)["DELTA PRUEBA CUATRO"]
        assert _filas(delta) == [("", "", None, False)]
        assert delta.lineas[0].nombre == ""
        assert delta.total == Decimal(0)
        assert delta.desviacion is None
        assert delta.estado == "SIN CARGA"


def test_f045_r11_total_desviacion_y_estado_del_trabajador_completo():
    completos = grupos_detalle(_muestra(), _PREFIJO)
    for postventa in (_OBRAS, _POSTVENTA):
        grupos = grupos_pestana(_muestra(), _PREFIJO, postventa)
        assert [(g.empleado, g.categoria, g.total, g.desviacion, g.estado)
                for g in grupos] == [
            (g.empleado, g.categoria, g.total, g.desviacion, g.estado)
            for g in completos]
    assert [g.estado for g in completos] == [
        "OK", "FALTA 10%", "OK", "SIN CARGA", "EXCESO 10%"]
    assert completos[2].categoria == ""


@pytest.mark.parametrize("postventa", [_OBRAS, _POSTVENTA])
def test_f045_r12_la_columna_pct_del_grupo_suma_el_total(postventa):
    theta = _fila(6, "THETA",
                  _linea("0101", "A", "33.33"),
                  _linea("0702", "B", "10.1", postventa=True),
                  _linea("0703", "C", "20.2", postventa=True),
                  _linea("0102", "D", "36.36"))
    for g in grupos_pestana([*_muestra(), theta], _PREFIJO, postventa):
        pcts = [ln.porcentaje for ln in g.lineas if ln.porcentaje is not None]
        if g.estado == "SIN CARGA":
            assert pcts == []
            continue
        assert sum(pcts, Decimal(0)) == g.total, g.empleado


def test_f045_r12_la_suma_coincide_en_obras_y_en_postventa():
    obras, postv = _por_nombre(_OBRAS), _por_nombre(_POSTVENTA)
    for nombre in obras:
        suma_o = sum((ln.porcentaje for ln in obras[nombre].lineas
                      if ln.porcentaje is not None), Decimal(0))
        suma_p = sum((ln.porcentaje for ln in postv[nombre].lineas
                      if ln.porcentaje is not None), Decimal(0))
        assert suma_o == suma_p, nombre


def test_f045_r5_d5_var_en_obras_y_sumado_en_resto_obras():
    obras, postv = _por_nombre(_OBRAS), _por_nombre(_POSTVENTA)
    assert "VAR-29" in [ln.codigo for ln in obras["EPSILON PRUEBA CINCO"].lineas]
    codigos_pv = [ln.codigo for g in postv.values() for ln in g.lineas]
    assert not any("VAR" in c for c in codigos_pv)
    # RESTO OBRAS de EPSILON es exactamente su VAR-29 (60).
    assert postv["EPSILON PRUEBA CINCO"].lineas[-1].porcentaje == Decimal(60)


def test_f045_r18_el_prefijo_sale_de_la_configuracion():
    postv = _por_nombre(_POSTVENTA, prefijo="PV_")
    assert _filas(postv["ALFA PRUEBA UNO"]) == [
        ("PV_0702", "PV_Hotel Inventado", Decimal(15), False),
        ("OBRAS", "RESTO OBRAS", Decimal(85), True)]
    obras = _por_nombre(_OBRAS, prefijo="PV_")
    assert _filas(obras["ALFA PRUEBA UNO"])[-1] == (
        "POSTVENTA", "RESTO POSTVENTA", Decimal(15), True)
