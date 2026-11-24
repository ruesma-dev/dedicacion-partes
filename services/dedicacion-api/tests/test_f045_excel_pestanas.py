# tests/test_f045_excel_pestanas.py
"""Tests offline de F-045: el Excel desglosado en «Obras» y «Postventa».

El libro lleva «Obras», «Postventa» y «Detalle» (la hoja de F-040, la
tercera) y no lleva Resumen (D1 y D2 de la MANUAL T6). Desde D11 las tres
acaban en la columna I «Observaciones», vacía, una celda por fila de datos
para escribir en el Excel (R20, R21).

Desde F-076 «Obras» lleva solo obras y «Postventa» solo postventa, sin la
línea agregada «RESTO …», y su Total, Desviación y Estado son los de esa
parte: los requisitos de F-045 que eso sustituye (R4, R7-R9, R11, la primera
mitad de R12, R15 y R16) se prueban en `test_f076_excel_sin_resto.py`
(specs/F-076-excel-sin-resto-de/design.md §6.1). Aquí quedan los vigentes.

Dos niveles (specs/F-045-excel-obras-postventa/design.md §7):

  - Contenido (`grupos_pestana` de `infrastructure/excel/contenido.py`):
    qué líneas lleva el grupo de cada trabajador en cada pestaña
    (R5, R6, R10, R12, R18).
  - Libro (`infrastructure/excel/exporter.py`): hojas, formato, combinadas,
    bandas, «Detalle» como en F-040 más la columna I, y la columna
    «Observaciones» de las tres hojas (R1-R3, R12-R14, R17, R18, R20, R21).

Los cinco trabajadores son los del prototipo (design §5), con nombres y
obras inventados. Sin red, sin BBDD y sin ficheros: el libro vive en memoria.
"""
from __future__ import annotations

import io
from decimal import Decimal

import pytest
from domain.models import CuadranteTrabajador, Periodo
from infrastructure.excel.contenido import (
    grupos_detalle,
    grupos_pestana,
)
from infrastructure.excel.exporter import OpenpyxlExcelExporter
from openpyxl import load_workbook

from tests.test_f040_excel import _fila, _linea, _rgb, _xml_hoja

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
    return [(ln.codigo, ln.obra, ln.porcentaje) for ln in grupo.lineas]


# ----------------------------------------------------------------------
# Contenido
# ----------------------------------------------------------------------

def test_f045_r5_obras_lleva_sus_lineas_en_orden_con_var_como_obra():
    obras = _por_nombre(_OBRAS)
    assert _filas(obras["BETA PRUEBA DOS"]) == [
        ("0101", "Obra Ficticia Norte", Decimal(50)),
        ("0103", "Obra Ficticia Este", Decimal(40))]
    var = obras["EPSILON PRUEBA CINCO"].lineas[0]
    assert (var.codigo, var.obra, var.nombre, var.porcentaje) == (
        "VAR-29", "Varios partida 29", "Varios partida 29", Decimal(60))
    # Postventa intercalada: las obras conservan su orden relativo, sin reordenar.
    omega = _fila(9, "OMEGA",
                  _linea("0200", "B", "40"),
                  _linea("0100", "Pv", "20", postventa=True),
                  _linea("0150", "A", "40"))
    [g] = grupos_pestana([omega], _PREFIJO, _OBRAS)
    assert [ln.codigo for ln in g.lineas] == ["0200", "0150"]


def test_f045_r6_postventa_lleva_sus_lineas_en_orden_con_prefijo():
    postv = _por_nombre(_POSTVENTA)
    gamma = postv["GAMMA PRUEBA TRES"]
    assert _filas(gamma) == [
        ("Postv-0702", "Postv-Hotel Inventado", Decimal(70)),
        ("Postv-0704", "Postv-Residencia Inventada", Decimal(30))]
    assert gamma.lineas[0].nombre == "Hotel Inventado"
    assert [ln.codigo for ln in postv["EPSILON PRUEBA CINCO"].lineas] == [
        "Postv-0702", "Postv-0705"]






def test_f045_r10_sin_carga_una_fila_vacia_en_cada_pestana():
    for postventa in (_OBRAS, _POSTVENTA):
        delta = _por_nombre(postventa)["DELTA PRUEBA CUATRO"]
        assert _filas(delta) == [("", "", None)]
        assert delta.lineas[0].nombre == ""
        assert delta.total == Decimal(0)
        assert delta.desviacion is None
        assert delta.estado == "SIN CARGA"



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



def test_f045_r5_d5_var_en_obras_y_nunca_en_postventa():
    obras, postv = _por_nombre(_OBRAS), _por_nombre(_POSTVENTA)
    assert "VAR-29" in [ln.codigo for ln in obras["EPSILON PRUEBA CINCO"].lineas]
    codigos_pv = [ln.codigo for g in postv.values() for ln in g.lineas]
    assert not any("VAR" in c for c in codigos_pv)


def test_f045_r18_el_prefijo_sale_de_la_configuracion():
    postv = _por_nombre(_POSTVENTA, prefijo="PV_")
    assert _filas(postv["ALFA PRUEBA UNO"]) == [
        ("PV_0702", "PV_Hotel Inventado", Decimal(15))]
    obras = _por_nombre(_OBRAS, prefijo="PV_")
    assert _filas(obras["ALFA PRUEBA UNO"])[-1] == (
        "0102", "Obra Ficticia Sur", Decimal(25))


# ----------------------------------------------------------------------
# Libro
# ----------------------------------------------------------------------
_PERIODO = Periodo(anio=2026, mes=9)
_BLANCO, _AZUL = "FFFFFFFF", "FFDDEBF7"
_CABECERA = ["Empleado", "Categoría", "Código", "Obra", "% dedicación",
             "Total empleado", "Desviación", "Estado", "Observaciones"]

#: (primera, última) fila de cada grupo de `_muestra()`, por hoja.
_GRUPOS = {
    "Obras": [(3, 4), (5, 6), (7, 7), (8, 8)],
    "Postventa": [(3, 3), (4, 5), (6, 6), (7, 8)],
}
#: Número de `sheet<n>.xml` de cada hoja.
_N_HOJA = {"Obras": 1, "Postventa": 2, "Detalle": 3}
#: (primera, última) fila de cada grupo de `_muestra()` en «Detalle».
_GRUPOS_DETALLE = [(3, 5), (6, 7), (8, 9), (10, 10), (11, 13)]


def _exportar(filas=None, prefijo=_PREFIJO, periodo=_PERIODO) -> bytes:
    filas = _muestra() if filas is None else filas
    return OpenpyxlExcelExporter(prefijo_postventa=prefijo).exportar(periodo, filas)


def _libro(contenido: bytes):
    return load_workbook(io.BytesIO(contenido))


def _columna(hoja, col: int) -> list:
    return [hoja.cell(r, col).value for r in range(3, hoja.max_row + 1)]



def test_f045_r1_tres_hojas_obras_postventa_y_detalle():
    assert _libro(_exportar()).sheetnames == ["Obras", "Postventa", "Detalle"]
    assert _libro(_exportar([])).sheetnames == ["Obras", "Postventa", "Detalle"]


def test_f045_r2_titulos_cabecera_en_2_y_datos_desde_3():
    libro = _libro(_exportar())
    assert libro["Obras"]["A1"].value == "OBRAS · Septiembre 2026"
    assert libro["Postventa"]["A1"].value == "POSTVENTA · Septiembre 2026"
    assert libro["Detalle"]["A1"].value == (
        "DETALLE DE DEDICACIÓN · Septiembre 2026")
    for hoja in libro.worksheets:
        assert hoja["A1"].font.bold and hoja["A1"].font.size == 13
        assert hoja["A2"].value == "Empleado"
        assert hoja["A3"].value == "ALFA PRUEBA UNO"
    enero = _libro(_exportar([], periodo=Periodo(2027, 1)))
    assert enero["Obras"]["A1"].value == "OBRAS · Enero 2027"
    assert enero["Postventa"]["A1"].value == "POSTVENTA · Enero 2027"
    assert enero["Detalle"]["A1"].value == "DETALLE DE DEDICACIÓN · Enero 2027"


@pytest.mark.parametrize("nombre", ["Obras", "Postventa"])
def test_f045_r3_cabecera_autofiltro_paneles_anchos_e_impresion(nombre):
    hoja = _libro(_exportar())[nombre]
    assert [c.value for c in hoja[2]] == _CABECERA
    for celda in hoja[2]:
        assert _rgb(celda.fill.fgColor.rgb) == "FF1F3864"
        assert celda.font.bold and _rgb(celda.font.color.rgb) == "FFFFFFFF"
    assert hoja.max_row == 8
    assert hoja.auto_filter.ref == "A2:I8"
    assert hoja.freeze_panes == "A3"
    assert tuple(hoja.column_dimensions[c].width for c in "ABCDEFGHI") == (
        34, 22, 12, 44, 13, 15, 12, 16, 50)
    assert hoja.page_setup.orientation == "landscape"
    assert hoja.sheet_properties.pageSetUpPr.fitToPage is True
    assert hoja.page_setup.fitToWidth == 1
    assert hoja.page_setup.fitToHeight == 0
    assert hoja.print_title_rows == "$1:$2"
    assert _libro(_exportar([]))[nombre].auto_filter.ref == "A2:I2"





def test_f045_r12_la_columna_pct_de_cada_grupo_suma_su_total_en_el_libro():
    libro = _libro(_exportar())
    for nombre, grupos in _GRUPOS.items():
        hoja = libro[nombre]
        for ini, fin in grupos:
            pcts = [hoja.cell(r, 5).value or 0 for r in range(ini, fin + 1)]
            assert sum(pcts) == pytest.approx(hoja.cell(ini, 6).value), (
                nombre, ini)


def test_f045_r13_valor_en_todas_las_filas_y_combinadas_por_grupo():
    contenido = _exportar()
    for nombre, grupos in _GRUPOS.items():
        celdas, rangos = _xml_hoja(contenido, _N_HOJA[nombre])
        for ini, fin in grupos:
            for col in "ABFGH":
                valores = {celdas[f"{col}{r}"]["v"] for r in range(ini, fin + 1)}
                assert len(valores) == 1, (nombre, col, ini, valores)
                # Empleado, Total y Estado nunca vacíos.
                assert None not in valores or col in "BG", (nombre, col, ini)
        esperados = {f"{c}{ini}:{c}{fin}" for ini, fin in grupos if fin > ini
                     for c in "ABFGH"}
        assert set(rangos) == esperados and len(rangos) == len(esperados), nombre
        hoja = _libro(contenido)[nombre]
        for ini, fin in grupos:
            if fin > ini:
                for c in "ABFGH":
                    assert hoja[f"{c}{ini}"].alignment.vertical == "center"
    # ALFA en Obras (A3:A4) y GAMMA en Postventa (A4:A5).
    assert "A3:A4" in _xml_hoja(contenido, 1)[1]
    assert "A4:A5" in _xml_hoja(contenido, 2)[1]
    # «Detalle», como en F-040: las combinadas de sus grupos.
    _, rangos_det = _xml_hoja(contenido, _N_HOJA["Detalle"])
    esperados_det = {f"{c}{ini}:{c}{fin}" for ini, fin in _GRUPOS_DETALLE
                     if fin > ini for c in "ABFGH"}
    assert set(rangos_det) == esperados_det
    assert len(rangos_det) == len(esperados_det)


def test_f045_r14_bandas_por_hoja_y_linea_gruesa_bajo_cada_trabajador():
    contenido = _exportar()
    for nombre, grupos in _GRUPOS.items():
        celdas, _ = _xml_hoja(contenido, _N_HOJA[nombre])
        for n, (ini, fin) in enumerate(grupos):
            banda = (_BLANCO, _AZUL)[n % 2]
            for r in range(ini, fin + 1):
                for col in "ABCDEFGH":
                    assert celdas[f"{col}{r}"]["fill"] == banda, (nombre, col, r)
            for col in "ABCDEFGH":
                assert celdas[f"{col}{fin}"]["bottom"] == (
                    "medium", "FF000000"), (nombre, col)
            for r in range(ini, fin):
                for col in "CDE":
                    assert celdas[f"{col}{r}"]["bottom"] == ("thin", "FFBFBFBF")




def test_f045_r17_detalle_igual_que_en_f040():
    contenido = _exportar()
    det = _libro(contenido)["Detalle"]
    grupos = grupos_detalle(_muestra(), _PREFIJO)
    assert det["A1"].value == "DETALLE DE DEDICACIÓN · Septiembre 2026"
    assert [c.value for c in det[2]] == _CABECERA
    assert det.max_row == 13
    assert det.auto_filter.ref == "A2:I13"
    lineas = [ln for g in grupos for ln in g.lineas]
    assert len(lineas) == 11
    for r, ln in zip(range(3, 14), lineas, strict=True):
        assert (det.cell(r, 3).value or "") == ln.codigo, r
        assert (det.cell(r, 4).value or "") == ln.obra, r
        esperado = None if ln.porcentaje is None else float(ln.porcentaje) / 100
        assert det.cell(r, 5).value == pytest.approx(esperado), r
    # Postventa intercalada con su prefijo, y ninguna línea agregada.
    assert [det.cell(r, 3).value for r in (3, 4, 5)] == [
        "0101", "0102", "Postv-0702"]
    assert det["D5"].value == "Postv-Hotel Inventado"
    codigos = [det.cell(r, 3).value for r in range(3, 14)]
    obras = [det.cell(r, 4).value or "" for r in range(3, 14)]
    assert "POSTVENTA" not in codigos and "OBRAS" not in codigos
    assert not any(o.startswith("RESTO") for o in obras)
    celdas, _ = _xml_hoja(contenido, _N_HOJA["Detalle"])
    for n, ((ini, fin), g) in enumerate(zip(_GRUPOS_DETALLE, grupos, strict=True)):
        assert det.cell(ini, 1).value == g.empleado
        assert det.cell(ini, 6).value == pytest.approx(float(g.total) / 100)
        assert det.cell(ini, 8).value == g.estado
        banda = (_BLANCO, _AZUL)[n % 2]
        for r in range(ini, fin + 1):
            for col in "ABCDEFGH":
                assert celdas[f"{col}{r}"]["fill"] == banda, (col, r)
        for col in "ABCDEFGH":
            assert celdas[f"{col}{fin}"]["bottom"] == ("medium", "FF000000"), col


def test_f045_r18_el_prefijo_de_la_configuracion_llega_al_libro():
    libro = _libro(_exportar(prefijo="PV_"))
    postv = libro["Postventa"]
    assert (postv["C3"].value, postv["D3"].value) == (
        "PV_0702", "PV_Hotel Inventado")
    assert (postv["C4"].value, postv["D4"].value) == (
        "PV_0702", "PV_Hotel Inventado")
    assert libro["Obras"]["C5"].value == "0101"
    assert libro["Detalle"]["C5"].value == "PV_0702"


# ----------------------------------------------------------------------
# Columna Observaciones (D11, D12)
# ----------------------------------------------------------------------
def test_f045_r20_observaciones_a_la_derecha_en_las_tres_hojas():
    libro = _libro(_exportar())
    vacio = _libro(_exportar([]))
    for hoja in libro.worksheets:
        i2 = hoja["I2"]
        assert i2.value == "Observaciones", hoja.title
        assert _rgb(i2.fill.fgColor.rgb) == "FF1F3864"
        assert i2.font.bold and _rgb(i2.font.color.rgb) == "FFFFFFFF"
        assert hoja.column_dimensions["I"].width == 50
        assert hoja.auto_filter.ref == f"A2:I{hoja.max_row}", hoja.title
        assert hoja.max_column == 9
        assert hoja.page_setup.fitToWidth == 1
        assert vacio[hoja.title].auto_filter.ref == "A2:I2"
        assert vacio[hoja.title]["I2"].value == "Observaciones"


def test_f045_r21_celda_de_observaciones_vacia_por_linea():
    contenido = _exportar()
    libro = _libro(contenido)
    grupos_por_hoja = {**_GRUPOS, "Detalle": _GRUPOS_DETALLE}
    for nombre, grupos in grupos_por_hoja.items():
        celdas, rangos = _xml_hoja(contenido, _N_HOJA[nombre])
        hoja = libro[nombre]
        assert not any(r.startswith("I") for r in rangos), nombre
        assert grupos[-1][1] == hoja.max_row
        for n, (ini, fin) in enumerate(grupos):
            banda = (_BLANCO, _AZUL)[n % 2]
            for r in range(ini, fin + 1):
                # Existe en el XML (con estilo), pero sin valor ni fórmula,
                # también en la «SIN CARGA» (D12 = A).
                assert f"I{r}" in celdas, (nombre, r)
                celda = celdas[f"I{r}"]
                assert celda["v"] is None, (nombre, r)
                assert celda["fill"] == banda, (nombre, r)
                assert celda["bottom"] == (
                    ("medium", "FF000000") if r == fin
                    else ("thin", "FFBFBFBF")), (nombre, r)
                i = hoja.cell(r, 9)
                assert i.value is None and i.data_type != "f", (nombre, r)
                assert i.alignment.wrap_text is True, (nombre, r)
                assert i.alignment.vertical == "top", (nombre, r)
                assert not i.font.italic, (nombre, r)
                assert i.border.left.style == "thin", (nombre, r)
                assert i.border.right.style == "thin", (nombre, r)
                assert i.border.top.style == "thin", (nombre, r)
