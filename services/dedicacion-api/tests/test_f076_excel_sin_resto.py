# tests/test_f076_excel_sin_resto.py
"""Tests offline de F-076: «Obras» solo con obras y «Postventa» solo con
postventa, sin la línea agregada «RESTO …» de F-045.

Decisiones del humano del 2026-11-24 (specs/F-076-excel-sin-resto-de/
design.md §10): D1 = (b), Total, Desviación y Estado de cada pestaña sobre
su parte; D2 = (a), «SIN CARGA» en las dos pestañas; D3 = (a), pestaña sin
nadie con título y cabecera; D5 = (a), fuera `agregada` y `AGREGADA_EN_*`.

Dos niveles, como F-045: contenido (`grupos_pestana`) y libro (exportador
releído con openpyxl o, para la columna A combinada, con el XML de la hoja).
La muestra es la de F-045 (design §4). Sin red, sin BBDD y sin ficheros.
"""
from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import pytest
from domain.models import Periodo
from infrastructure.excel import contenido as mod_contenido
from infrastructure.excel.contenido import (
    LineaDetalle,
    grupos_detalle,
    grupos_pestana,
)
from infrastructure.excel.exporter import OpenpyxlExcelExporter
from openpyxl import load_workbook

from tests.test_f040_excel import _fila, _linea, _xml_hoja
from tests.test_f045_excel_pestanas import _muestra

_PREFIJO = "Postv-"
_OBRAS, _POSTVENTA = False, True
_PERIODO = Periodo(anio=2026, mes=9)
_BLANCO, _AZUL = "FFFFFFFF", "FFDDEBF7"
_CABECERA = ["Empleado", "Categoría", "Código", "Obra", "% dedicación",
             "Total empleado", "Desviación", "Estado", "Observaciones"]
_N_HOJA = {"Obras": 1, "Postventa": 2, "Detalle": 3}
_RAIZ_REPO = Path(__file__).resolve().parents[3]

#: (primera, última) fila de cada grupo de `_muestra()`, por hoja (design §4).
_GRUPOS = {
    "Obras": [(3, 4), (5, 6), (7, 7), (8, 8)],
    "Postventa": [(3, 3), (4, 5), (6, 6), (7, 8)],
    "Detalle": [(3, 5), (6, 7), (8, 9), (10, 10), (11, 13)],
}
#: (empleado, total, desviación, estado) de cada grupo, por hoja (design §4).
_CIFRAS = {
    "Obras": [
        ("ALFA PRUEBA UNO", Decimal(85), Decimal(-15), "FALTA 15%"),
        ("BETA PRUEBA DOS", Decimal(90), Decimal(-10), "FALTA 10%"),
        ("DELTA PRUEBA CUATRO", Decimal(0), None, "SIN CARGA"),
        ("EPSILON PRUEBA CINCO", Decimal(60), Decimal(-40), "FALTA 40%"),
    ],
    "Postventa": [
        ("ALFA PRUEBA UNO", Decimal(15), Decimal(-85), "FALTA 85%"),
        ("GAMMA PRUEBA TRES", Decimal(100), Decimal(0), "OK"),
        ("DELTA PRUEBA CUATRO", Decimal(0), None, "SIN CARGA"),
        ("EPSILON PRUEBA CINCO", Decimal(50), Decimal(-50), "FALTA 50%"),
    ],
}


def _theta():
    """33,33 + 36,37 de obra (69,70) y 10,1 + 20,2 de postventa (30,3)."""
    return _fila(6, "THETA",
                 _linea("0101", "A", "33.33"),
                 _linea("0702", "B", "10.1", postventa=True),
                 _linea("0703", "C", "20.2", postventa=True),
                 _linea("0102", "D", "36.37"))


def _por_nombre(postventa: bool, filas=None, prefijo=_PREFIJO) -> dict:
    filas = _muestra() if filas is None else filas
    return {g.empleado: g for g in grupos_pestana(filas, prefijo, postventa)}


def _exportar(filas=None, prefijo=_PREFIJO) -> bytes:
    filas = _muestra() if filas is None else filas
    return OpenpyxlExcelExporter(prefijo_postventa=prefijo).exportar(
        _PERIODO, filas)


def _libro(contenido: bytes):
    return load_workbook(io.BytesIO(contenido))


def _columna(hoja, col: int) -> list:
    return [hoja.cell(r, col).value for r in range(3, hoja.max_row + 1)]


def _empleados(contenido: bytes, nombre: str) -> list:
    """Columna A desde el XML: `load_workbook` vacía las no ancla (F-040 §5)."""
    celdas, _ = _xml_hoja(contenido, _N_HOJA[nombre])
    filas = sorted(int(ref[1:]) for ref in celdas
                   if ref.startswith("A") and ref[1:].isdigit())
    return [celdas[f"A{r}"]["v"] for r in filas if r >= 3]


def _pct(valor: Decimal | None):
    return None if valor is None else pytest.approx(float(valor) / 100)


def _fgh(celdas: dict, r: int) -> tuple:
    """(F, G, H) de la fila `r` desde el XML: con `load_workbook` las no
    ancla de las combinadas salen vacías (F-040 §5)."""
    f, g, h = (celdas[f"{c}{r}"]["v"] for c in "FGH")
    return (None if f is None else float(f),
            None if g is None else float(g), h)


# ----------------------------------------------------------------------
# R1 · Libro
# ----------------------------------------------------------------------
def test_f076_r1_tres_hojas_con_su_cabecera_y_autofiltro():
    for filas in (None, []):
        libro = _libro(_exportar(filas))
        assert libro.sheetnames == ["Obras", "Postventa", "Detalle"]
        for hoja in libro.worksheets:
            assert [c.value for c in hoja[2]] == _CABECERA, hoja.title
            assert hoja.auto_filter.ref == f"A2:I{max(hoja.max_row, 2)}"
            assert hoja.freeze_panes == "A3"


# ----------------------------------------------------------------------
# R2-R4 · Qué líneas lleva cada pestaña
# ----------------------------------------------------------------------
def test_f076_r2_obras_solo_lineas_de_obra():
    obras = _por_nombre(_OBRAS)
    assert [(ln.codigo, ln.obra, ln.porcentaje)
            for ln in obras["ALFA PRUEBA UNO"].lineas] == [
        ("0101", "Obra Ficticia Norte", Decimal(60)),
        ("0102", "Obra Ficticia Sur", Decimal(25))]
    [var] = obras["EPSILON PRUEBA CINCO"].lineas
    assert (var.codigo, var.obra, var.nombre, var.porcentaje) == (
        "VAR-29", "Varios partida 29", "Varios partida 29", Decimal(60))
    hoja = _libro(_exportar())["Obras"]
    assert _columna(hoja, 3) == ["0101", "0102", "0101", "0103", None, "VAR-29"]
    assert _columna(hoja, 4) == [
        "Obra Ficticia Norte", "Obra Ficticia Sur", "Obra Ficticia Norte",
        "Obra Ficticia Este", None, "Varios partida 29"]
    assert _columna(hoja, 5) == [0.6, 0.25, 0.5, 0.4, None, 0.6]
    assert not any(str(c or "").startswith(_PREFIJO) for c in _columna(hoja, 3))


def test_f076_r3_postventa_solo_lineas_de_postventa():
    postv = _por_nombre(_POSTVENTA)
    assert [(ln.codigo, ln.obra, ln.nombre, ln.porcentaje)
            for ln in postv["ALFA PRUEBA UNO"].lineas] == [
        ("Postv-0702", "Postv-Hotel Inventado", "Hotel Inventado", Decimal(15))]
    assert [ln.codigo for ln in postv["EPSILON PRUEBA CINCO"].lineas] == [
        "Postv-0702", "Postv-0705"]
    hoja = _libro(_exportar())["Postventa"]
    assert _columna(hoja, 3) == [
        "Postv-0702", "Postv-0702", "Postv-0704", None,
        "Postv-0702", "Postv-0705"]
    assert _columna(hoja, 5) == [0.15, 0.7, 0.3, None, 0.3, 0.2]
    for codigo, obra in zip(_columna(hoja, 3), _columna(hoja, 4), strict=True):
        if codigo is not None:
            assert codigo.startswith(_PREFIJO) and obra.startswith(_PREFIJO)


def test_f076_r4_ninguna_linea_agregada():
    for postventa in (_OBRAS, _POSTVENTA):
        for g in grupos_pestana([*_muestra(), _theta()], _PREFIJO, postventa):
            for ln in g.lineas:
                assert ln.codigo not in ("POSTVENTA", "OBRAS"), g.empleado
                assert not ln.obra.startswith("RESTO"), g.empleado
    # D5: sin el campo ni las constantes de la agregada.
    assert "agregada" not in LineaDetalle.__dataclass_fields__
    assert not hasattr(mod_contenido, "AGREGADA_EN_OBRAS")
    assert not hasattr(mod_contenido, "AGREGADA_EN_POSTVENTA")
    for contenido in (_exportar(), _exportar([_theta()])):
        libro = _libro(contenido)
        for nombre in ("Obras", "Postventa"):
            hoja = libro[nombre]
            assert not {"POSTVENTA", "OBRAS"} & set(_columna(hoja, 3)), nombre
            assert not any(str(o or "").startswith("RESTO")
                           for o in _columna(hoja, 4)), nombre


# ----------------------------------------------------------------------
# R5-R7 · Qué trabajadores salen y en qué orden
# ----------------------------------------------------------------------
def test_f076_r5_sin_nada_de_esa_parte_no_sale():
    assert "GAMMA PRUEBA TRES" not in _por_nombre(_OBRAS)
    assert "BETA PRUEBA DOS" not in _por_nombre(_POSTVENTA)
    contenido = _exportar()
    assert "GAMMA PRUEBA TRES" not in _empleados(contenido, "Obras")
    assert "BETA PRUEBA DOS" not in _empleados(contenido, "Postventa")
    # Una línea de esa parte, aunque esté al 0 %, basta para salir.
    cero = _fila(7, "IOTA",
                 _linea("0101", "A", "100"),
                 _linea("0702", "B", "0", postventa=True))
    [g] = grupos_pestana([cero], _PREFIJO, _POSTVENTA)
    assert [(ln.codigo, ln.porcentaje) for ln in g.lineas] == [
        ("Postv-0702", Decimal(0))]
    assert _empleados(_exportar([cero]), "Postventa") == ["IOTA"]


def test_f076_r6_orden_de_la_api_en_cada_pestana():
    for filas in (_muestra(), list(reversed(_muestra()))):
        nombres = [f.trabajador.nombre for f in filas]
        sin_obras = {"GAMMA PRUEBA TRES"}
        sin_postv = {"BETA PRUEBA DOS"}
        assert [g.empleado for g in grupos_pestana(filas, _PREFIJO, _OBRAS)] == [
            n for n in nombres if n not in sin_obras]
        assert [g.empleado for g in grupos_pestana(
            filas, _PREFIJO, _POSTVENTA)] == [
            n for n in nombres if n not in sin_postv]
    contenido = _exportar()
    assert _empleados(contenido, "Obras") == (
        ["ALFA PRUEBA UNO"] * 2 + ["BETA PRUEBA DOS"] * 2
        + ["DELTA PRUEBA CUATRO", "EPSILON PRUEBA CINCO"])
    assert _empleados(contenido, "Postventa") == (
        ["ALFA PRUEBA UNO"] + ["GAMMA PRUEBA TRES"] * 2
        + ["DELTA PRUEBA CUATRO"] + ["EPSILON PRUEBA CINCO"] * 2)


def test_f076_r7_sin_carga_en_las_tres_hojas():
    for postventa in (_OBRAS, _POSTVENTA):
        delta = _por_nombre(postventa)["DELTA PRUEBA CUATRO"]
        assert [(ln.codigo, ln.obra, ln.porcentaje) for ln in delta.lineas] == [
            ("", "", None)]
        assert (delta.total, delta.desviacion, delta.estado) == (
            Decimal(0), None, "SIN CARGA")
    libro = _libro(_exportar())
    for nombre, fila in (("Obras", 7), ("Postventa", 6), ("Detalle", 10)):
        hoja = libro[nombre]
        assert hoja.cell(fila, 1).value == "DELTA PRUEBA CUATRO", nombre
        assert [c.value for c in hoja[fila]][2:] == [
            None, None, None, 0, None, "SIN CARGA", None], nombre


# ----------------------------------------------------------------------
# R8 · Total, Desviación y Estado de la parte [D1 = b]
# ----------------------------------------------------------------------
def test_f076_r8_total_desviacion_estado_de_la_parte():
    for nombre, postventa in (("Obras", _OBRAS), ("Postventa", _POSTVENTA)):
        grupos = grupos_pestana(_muestra(), _PREFIJO, postventa)
        assert [(g.empleado, g.total, g.desviacion, g.estado)
                for g in grupos] == _CIFRAS[nombre]
        for g in grupos:
            assert isinstance(g.total, Decimal)
            pcts = [ln.porcentaje for ln in g.lineas if ln.porcentaje is not None]
            assert sum(pcts, Decimal(0)) == g.total, g.empleado
    # Suma exacta en Decimal (no 69,699999…).
    [obras] = grupos_pestana([_theta()], _PREFIJO, _OBRAS)
    [postv] = grupos_pestana([_theta()], _PREFIJO, _POSTVENTA)
    assert (obras.total, obras.desviacion, obras.estado) == (
        Decimal("69.70"), Decimal("-30.30"), "FALTA 30,30%")
    assert (postv.total, postv.desviacion, postv.estado) == (
        Decimal("30.3"), Decimal("-69.70"), "FALTA 69,70%")
    # Una sola línea de la parte al 0 %: FALTA 100 %, no SIN CARGA.
    cero = _fila(7, "IOTA",
                 _linea("0101", "A", "100"),
                 _linea("0702", "B", "0", postventa=True))
    [g] = grupos_pestana([cero], _PREFIJO, _POSTVENTA)
    assert (g.total, g.desviacion, g.estado) == (
        Decimal(0), Decimal("-100.00"), "FALTA 100%")
    # En el libro: F, G y H en todas las filas del grupo, y la columna E suma F.
    contenido = _exportar()
    libro = _libro(contenido)
    for nombre in ("Obras", "Postventa"):
        hoja = libro[nombre]
        celdas, _ = _xml_hoja(contenido, _N_HOJA[nombre])
        for (ini, fin), (_emp, total, desv, estado) in zip(
                _GRUPOS[nombre], _CIFRAS[nombre], strict=True):
            for r in range(ini, fin + 1):
                assert _fgh(celdas, r) == (
                    _pct(total), _pct(desv), estado), (nombre, r)
            suma = sum(hoja.cell(r, 5).value or 0 for r in range(ini, fin + 1))
            assert suma == pytest.approx(hoja.cell(ini, 6).value), (nombre, ini)


# ----------------------------------------------------------------------
# R9-R11 · Pestaña vacía y formato
# ----------------------------------------------------------------------
def test_f076_r9_pestana_sin_nadie_solo_cabecera():
    solo_obras = [_muestra()[1]]                       # BETA
    postv = _libro(_exportar(solo_obras))["Postventa"]
    assert postv["A1"].value == "POSTVENTA · Septiembre 2026"
    assert [c.value for c in postv[2]] == _CABECERA
    assert postv.max_row == 2
    assert postv.auto_filter.ref == "A2:I2"
    con_sin_carga = [_muestra()[1], _muestra()[3]]     # BETA y DELTA
    postv = _libro(_exportar(con_sin_carga))["Postventa"]
    assert postv.max_row == 3
    assert postv.auto_filter.ref == "A2:I3"
    assert (postv["A3"].value, postv["H3"].value) == (
        "DELTA PRUEBA CUATRO", "SIN CARGA")


def test_f076_r10_bandas_y_combinadas_por_pestana():
    contenido = _exportar()
    for nombre in ("Obras", "Postventa"):
        celdas, rangos = _xml_hoja(contenido, _N_HOJA[nombre])
        grupos = _GRUPOS[nombre]
        for n, (ini, fin) in enumerate(grupos):
            banda = (_BLANCO, _AZUL)[n % 2]
            for r in range(ini, fin + 1):
                for col in "ABCDEFGHI":
                    assert celdas[f"{col}{r}"]["fill"] == banda, (nombre, col, r)
                for col in "ABFGH":
                    assert celdas[f"{col}{r}"]["v"] == celdas[f"{col}{ini}"]["v"]
            for col in "ABCDEFGHI":
                assert celdas[f"{col}{fin}"]["bottom"] == (
                    "medium", "FF000000"), (nombre, col, fin)
        esperados = {f"{c}{ini}:{c}{fin}" for ini, fin in grupos if fin > ini
                     for c in "ABFGH"}
        assert set(rangos) == esperados and len(rangos) == len(esperados), nombre
    _, rangos_postv = _xml_hoja(contenido, _N_HOJA["Postventa"])
    assert {"A4:A5", "A7:A8"} <= set(rangos_postv)
    _, rangos_obras = _xml_hoja(contenido, _N_HOJA["Obras"])
    assert {"A3:A4", "A5:A6"} <= set(rangos_obras)


def test_f076_r11_ninguna_cursiva():
    for filas in (None, [_theta()]):
        for hoja in _libro(_exportar(filas)).worksheets:
            for fila in hoja.iter_rows():
                for celda in fila:
                    assert not celda.font.italic, (hoja.title, celda.coordinate)


# ----------------------------------------------------------------------
# R12-R13 · Detalle y prefijo
# ----------------------------------------------------------------------
def test_f076_r12_detalle_igual_con_el_trabajador_completo():
    contenido = _exportar()
    det = _libro(contenido)["Detalle"]
    assert det.max_row == 13
    completos = grupos_detalle(_muestra(), _PREFIJO)
    assert [g.estado for g in completos] == [
        "OK", "FALTA 10%", "OK", "SIN CARGA", "EXCESO 10%"]
    lineas = [ln for g in completos for ln in g.lineas]
    assert len(lineas) == 11
    assert _columna(det, 3) == [
        "0101", "0102", "Postv-0702", "0101", "0103", "Postv-0702",
        "Postv-0704", None, "VAR-29", "Postv-0702", "Postv-0705"]
    assert len(set(_empleados(contenido, "Detalle"))) == 5
    celdas, _ = _xml_hoja(contenido, _N_HOJA["Detalle"])
    for (ini, fin), g in zip(_GRUPOS["Detalle"], completos, strict=True):
        for r in range(ini, fin + 1):
            assert _fgh(celdas, r) == (
                _pct(g.total), _pct(g.desviacion), g.estado), r
    assert det["H3"].value == "OK" and det["H11"].value == "EXCESO 10%"


def test_f076_r13_prefijo_de_la_configuracion():
    libro = _libro(_exportar(prefijo="PV_"))
    postv, obras = libro["Postventa"], libro["Obras"]
    assert (postv["C3"].value, postv["D3"].value) == (
        "PV_0702", "PV_Hotel Inventado")
    for codigo in _columna(postv, 3):
        assert codigo is None or codigo.startswith("PV_"), codigo
    for col in (3, 4):
        assert not any(str(v or "").startswith("PV_")
                       for v in _columna(obras, col))
    assert libro["Detalle"]["C5"].value == "PV_0702"


# ----------------------------------------------------------------------
# R14 · Documentación
# ----------------------------------------------------------------------
@pytest.mark.parametrize("ruta", [
    "docs/ARCHITECTURE.md",
    "services/dedicacion-api/README.md",
])
def test_f076_r14_docs_sin_resto(ruta):
    texto = (_RAIZ_REPO / ruta).read_text(encoding="utf-8")
    assert "RESTO" not in texto
    assert "otra parte en una línea" not in texto
