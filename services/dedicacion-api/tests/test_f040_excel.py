# tests/test_f040_excel.py
"""Tests offline de F-040: el Excel de exportación como el modelo de negocio.

Dos niveles (specs/F-040-excel-modelo-juan/design.md §7):

  - Contenido (`infrastructure/excel/contenido.py`): grupos del Detalle,
    filas del Resumen y textos de porcentaje y de estado (R7-R9, R14-R16,
    R18, R19).
  - Libro (`infrastructure/excel/exporter.py`): se exporta y se relee con
    openpyxl o, para las celdas combinadas, con `zipfile` sobre el XML de la
    hoja, porque `load_workbook` limpia las celdas no ancla al leer (§5).

Todos los nombres son inventados. Sin red, sin BBDD y sin ficheros: el libro
vive en memoria.
"""
from __future__ import annotations

import io
import itertools
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal

import pytest
from domain.models import (
    CuadranteTrabajador,
    EstadoTrabajador,
    Linea,
    Periodo,
    Trabajador,
)
from infrastructure.excel.contenido import (
    es_entero,
    filas_resumen,
    grupos_detalle,
    texto_estado,
    texto_pct,
)
from infrastructure.excel.exporter import OpenpyxlExcelExporter
from openpyxl import load_workbook

_PREFIJO = "Postv-"


# ----------------------------------------------------------------------
# Fábricas de datos inventados
# ----------------------------------------------------------------------
def _trabajador(ide: int, nombre: str, categoria: str | None = "OFICIAL 1ª"):
    return Trabajador(ide=ide, cod=str(ide), nombre=nombre, dni=None,
                      categoria=categoria)


#: `obra_ide` deterministas: el exportador no los usa, pero un `hash()`
#: cambiaría de un proceso a otro.
_OBRA_IDES = itertools.count(1)


def _linea(cod: str, descripcion: str, pct: str, postventa: bool = False):
    return Linea(obra_ide=next(_OBRA_IDES), es_postventa=postventa,
                 porcentaje=Decimal(pct), cod=cod, descripcion=descripcion)


def _fila(ide: int, nombre: str, *lineas: Linea, categoria="OFICIAL 1ª"):
    return CuadranteTrabajador(trabajador=_trabajador(ide, nombre, categoria),
                               lineas=list(lineas))


def _cuadrante_muestra() -> list[CuadranteTrabajador]:
    """Cinco trabajadores inventados: 4 líneas al 100 %, 2 líneas en FALTA,
    VAR + postventa en EXCESO, uno sin carga y uno de una línea."""
    return [
        _fila(1, "ALFA PRUEBA UNO",
              _linea("0101", "Obra Ficticia Norte", "55"),
              _linea("0102", "Obra Ficticia Sur", "20"),
              _linea("0103", "Obra Ficticia Este", "20"),
              _linea("0104", "Obra Ficticia Oeste", "5")),
        _fila(2, "BETA PRUEBA DOS",
              _linea("0101", "Obra Ficticia Norte", "33.33"),
              _linea("0102", "Obra Ficticia Sur", "56.67")),
        _fila(3, "GAMMA PRUEBA TRES",
              _linea("VAR-29", "Varios partida 29", "80"),
              _linea("0702", "Hotel Inventado", "30", postventa=True),
              categoria=None),
        _fila(4, "DELTA PRUEBA CUATRO"),
        _fila(5, "EPSILON PRUEBA CINCO",
              _linea("0105", "Obra Ficticia Centro", "100")),
    ]


# ----------------------------------------------------------------------
# Contenido
# ----------------------------------------------------------------------
def test_f040_r7_conserva_el_orden_de_trabajadores_y_lineas():
    filas = list(reversed(_cuadrante_muestra()))
    grupos = grupos_detalle(filas, _PREFIJO)
    assert [g.empleado for g in grupos] == [f.trabajador.nombre for f in filas]
    beta = next(g for g in grupos if g.empleado == "BETA PRUEBA DOS")
    assert [ln.codigo for ln in beta.lineas] == ["0101", "0102"]
    # Las líneas tampoco se reordenan: el orden lo pone el repositorio.
    al_reves = _fila(9, "OMEGA", _linea("0200", "B", "50"), _linea("0100", "A", "50"))
    [omega] = grupos_detalle([al_reves], _PREFIJO)
    assert [ln.codigo for ln in omega.lineas] == ["0200", "0100"]


def test_f040_r8_postventa_con_prefijo_y_var_como_obra_normal():
    [gamma] = grupos_detalle([_cuadrante_muestra()[2]], _PREFIJO)
    var, postv = gamma.lineas
    assert (var.codigo, var.obra, var.nombre) == (
        "VAR-29", "Varios partida 29", "Varios partida 29")
    assert (postv.codigo, postv.obra, postv.nombre) == (
        "Postv-0702", "Postv-Hotel Inventado", "Hotel Inventado")
    assert postv.porcentaje == Decimal(30)
    # El prefijo sale de la configuración, no de un literal del código.
    [otro] = grupos_detalle([_cuadrante_muestra()[2]], "PV_")
    assert otro.lineas[1].codigo == "PV_0702"


def test_f040_r8_categoria_nula_sale_vacia():
    [gamma] = grupos_detalle([_cuadrante_muestra()[2]], _PREFIJO)
    assert gamma.categoria == ""
    assert gamma.empleado == "GAMMA PRUEBA TRES"


def test_f040_r9_trabajador_sin_lineas_una_fila_sin_carga():
    [delta] = grupos_detalle([_cuadrante_muestra()[3]], _PREFIJO)
    assert len(delta.lineas) == 1
    vacia = delta.lineas[0]
    assert (vacia.codigo, vacia.obra, vacia.nombre, vacia.porcentaje) == (
        "", "", "", None)
    assert delta.total == Decimal(0)
    assert delta.desviacion is None
    assert delta.estado == "SIN CARGA"


def test_f040_r14_obras_con_codigo_nombre_y_mas():
    resumen = filas_resumen(grupos_detalle(_cuadrante_muestra(), _PREFIJO))
    por_nombre = {f.empleado: f for f in resumen}
    assert por_nombre["BETA PRUEBA DOS"].obras == (
        "0101 Obra Ficticia Norte = 33,33% + 0102 Obra Ficticia Sur = 56,67%")
    assert por_nombre["GAMMA PRUEBA TRES"].obras == (
        "VAR-29 Varios partida 29 = 80% + Postv-0702 Hotel Inventado = 30%")
    assert por_nombre["EPSILON PRUEBA CINCO"].obras == (
        "0105 Obra Ficticia Centro = 100%")
    assert por_nombre["DELTA PRUEBA CUATRO"].obras == ""


def test_f040_r15_resumen_con_total_y_el_mismo_estado_que_el_detalle():
    grupos = grupos_detalle(_cuadrante_muestra(), _PREFIJO)
    resumen = filas_resumen(grupos)
    assert [f.empleado for f in resumen] == [g.empleado for g in grupos]
    assert [f.categoria for f in resumen] == [g.categoria for g in grupos]
    assert [f.estado for f in resumen] == [g.estado for g in grupos]
    assert [f.total for f in resumen] == [g.total for g in grupos]
    assert [f.estado for f in resumen] == [
        "OK", "FALTA 10%", "EXCESO 10%", "SIN CARGA", "OK"]
    assert [f.total for f in resumen] == [
        Decimal(100), Decimal(90), Decimal(110), Decimal(0), Decimal(100)]


def test_f040_r16_las_cifras_son_las_de_la_regla_del_100():
    """99,996 % es OK por la épsilon de `domain.estados`, no por una propia."""
    fila = _fila(7, "ZETA", _linea("0101", "A", "33.332"),
                 _linea("0102", "B", "33.332"), _linea("0103", "C", "33.332"))
    [zeta] = grupos_detalle([fila], _PREFIJO)
    assert zeta.total == Decimal("99.996")
    assert zeta.estado == "OK"
    assert zeta.desviacion == 0
    # Y una centésima más lejos ya es FALTA, con la desviación del dominio.
    fila2 = _fila(8, "ETA", _linea("0101", "A", "99.99"))
    [eta] = grupos_detalle([fila2], _PREFIJO)
    assert eta.estado == "FALTA 0,01%"
    assert eta.desviacion == Decimal("-0.01")


@pytest.mark.parametrize(
    ("valor", "texto"),
    [("100", "100"), ("10", "10"), ("100.00", "100"), ("33.33", "33,33"),
     ("0.5", "0,50"), ("0", "0"), ("-10", "-10")],
)
def test_f040_r18_texto_pct_sin_notacion_cientifica(valor, texto):
    resultado = texto_pct(Decimal(valor))
    assert resultado == texto
    assert "E" not in resultado


def test_f040_r17_es_entero_decide_el_formato():
    assert es_entero(Decimal("100.00"))
    assert es_entero(Decimal(55))
    assert not es_entero(Decimal("33.33"))
    assert not es_entero(Decimal("0.5"))


def test_f040_r19_textos_de_estado():
    assert texto_estado(EstadoTrabajador.OK, Decimal(0)) == "OK"
    assert texto_estado(EstadoTrabajador.SIN_CARGA, Decimal(0)) == "SIN CARGA"
    assert texto_estado(EstadoTrabajador.FALTA, Decimal("-10.00")) == "FALTA 10%"
    assert texto_estado(EstadoTrabajador.EXCESO, Decimal("10.00")) == "EXCESO 10%"
    assert texto_estado(EstadoTrabajador.FALTA, Decimal("-0.50")) == "FALTA 0,50%"
    assert texto_estado(EstadoTrabajador.EXCESO, Decimal("33.33")) == "EXCESO 33,33%"


# ----------------------------------------------------------------------
# Libro
# ----------------------------------------------------------------------
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_T = f"{{{_NS['m']}}}t"
_PERIODO = Periodo(anio=2026, mes=9)
_BLANCO, _AZUL = "FFFFFFFF", "FFDDEBF7"

#: Filas del Detalle de `_cuadrante_muestra()`: (primera, última) por grupo.
_GRUPOS = [(3, 6), (7, 8), (9, 10), (11, 11), (12, 12)]


def _exportar(filas=None, prefijo=_PREFIJO) -> bytes:
    filas = _cuadrante_muestra() if filas is None else filas
    return OpenpyxlExcelExporter(prefijo_postventa=prefijo).exportar(_PERIODO, filas)


def _libro(contenido: bytes):
    return load_workbook(io.BytesIO(contenido))


def _rgb(valor):
    """openpyxl escribe «00RRGGBB»; Excel lee el alfa como opaco."""
    return "FF" + valor[2:] if isinstance(valor, str) and len(valor) == 8 else valor


def _xml_hoja(contenido: bytes, n: int) -> tuple[dict, list[str]]:
    """Lee `sheet<n>.xml` sin openpyxl, que limpia las combinadas al leer.

    Devuelve ({"A3": {"v", "fill", "bottom"}}, [rangos <mergeCell>])."""
    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        hoja = ET.fromstring(z.read(f"xl/worksheets/sheet{n}.xml"))
        estilos = ET.fromstring(z.read("xl/styles.xml"))
        nombres = z.namelist()
        compartidas = (ET.fromstring(z.read("xl/sharedStrings.xml"))
                       if "xl/sharedStrings.xml" in nombres else None)
    textos = [] if compartidas is None else [
        "".join(t.text or "" for t in si.iter(_T))
        for si in compartidas.findall("m:si", _NS)]
    rellenos = []
    for fill in estilos.find("m:fills", _NS).findall("m:fill", _NS):
        patron = fill.find("m:patternFill", _NS)
        fg = fill.find("m:patternFill/m:fgColor", _NS)
        solido = patron is not None and patron.get("patternType") == "solid"
        rellenos.append(_rgb(fg.get("rgb")) if solido and fg is not None else None)
    bordes = []
    for borde in estilos.find("m:borders", _NS).findall("m:border", _NS):
        abajo = borde.find("m:bottom", _NS)
        color = abajo.find("m:color", _NS) if abajo is not None else None
        bordes.append((abajo.get("style") if abajo is not None else None,
                       _rgb(color.get("rgb")) if color is not None else None))
    xfs = estilos.find("m:cellXfs", _NS).findall("m:xf", _NS)
    celdas = {}
    for c in hoja.iter(f"{{{_NS['m']}}}c"):
        xf = xfs[int(c.get("s", "0"))]
        v = c.find("m:v", _NS)
        valor = None if v is None else v.text
        if c.get("t") == "s":
            valor = textos[int(valor)]
        elif c.get("t") == "inlineStr":
            valor = "".join(t.text or "" for t in c.iter(_T))
        celdas[c.get("r")] = {
            "v": valor,
            "fill": rellenos[int(xf.get("fillId", "0"))],
            "bottom": bordes[int(xf.get("borderId", "0"))],
        }
    rangos = [m.get("ref") for m in hoja.iter(f"{{{_NS['m']}}}mergeCell")]
    return celdas, rangos


def test_f040_r1_dos_hojas_detalle_y_resumen():
    assert _libro(_exportar()).sheetnames == ["Detalle", "Resumen"]


def test_f040_r2_titulo_en_fila_1_cabecera_en_2_datos_desde_3():
    libro = _libro(_exportar())
    det, res = libro["Detalle"], libro["Resumen"]
    assert det["A1"].value == "DETALLE DE DEDICACIÓN · Septiembre 2026"
    assert res["A1"].value == "RESUMEN · Septiembre 2026"
    for hoja in (det, res):
        assert hoja["A1"].font.bold and hoja["A1"].font.size == 13
        assert hoja["A2"].value == "Empleado"
        assert hoja["A3"].value == "ALFA PRUEBA UNO"
    assert det.max_row == 12 and res.max_row == 7
    enero = _libro(OpenpyxlExcelExporter().exportar(Periodo(2027, 1), []))
    assert enero["Detalle"]["A1"].value == "DETALLE DE DEDICACIÓN · Enero 2027"
    assert enero["Resumen"]["A1"].value == "RESUMEN · Enero 2027"


def test_f040_r3_autofiltro_y_paneles():
    libro = _libro(_exportar())
    assert libro["Detalle"].auto_filter.ref == "A2:H12"
    assert libro["Resumen"].auto_filter.ref == "A2:E7"
    for hoja in libro.worksheets:
        assert hoja.freeze_panes == "A3"
    vacio = _libro(_exportar([]))
    assert vacio["Detalle"].auto_filter.ref == "A2:H2"
    assert vacio["Resumen"].auto_filter.ref == "A2:E2"


def test_f040_r4_impresion_y_anchos():
    libro = _libro(_exportar())
    anchos = {"Detalle": (34, 22, 12, 44, 13, 15, 12, 16),
              "Resumen": (34, 22, 90, 10, 16)}
    for hoja in libro.worksheets:
        assert hoja.page_setup.orientation == "landscape"
        assert hoja.sheet_properties.pageSetUpPr.fitToPage is True
        assert hoja.page_setup.fitToWidth == 1
        assert hoja.page_setup.fitToHeight == 0
        assert hoja.print_title_rows == "$1:$2"
        letras = "ABCDEFGH"[: len(anchos[hoja.title])]
        assert tuple(hoja.column_dimensions[c].width for c in letras) == (
            anchos[hoja.title])


def test_f040_r5_cabecera_azul_con_texto_blanco_en_negrita():
    libro = _libro(_exportar())
    for hoja in libro.worksheets:
        for celda in hoja[2]:
            assert _rgb(celda.fill.fgColor.rgb) == "FF1F3864"
            assert celda.font.bold
            assert _rgb(celda.font.color.rgb) == "FFFFFFFF"


def test_f040_r6_cabecera_del_detalle_sin_obra_codigo():
    det = _libro(_exportar())["Detalle"]
    assert [c.value for c in det[2]] == [
        "Empleado", "Categoría", "Código", "Obra", "% dedicación",
        "Total empleado", "Desviación", "Estado"]


def test_f040_r7_r8_filas_del_detalle_en_orden_y_con_su_codigo():
    det = _libro(_exportar())["Detalle"]
    assert [det.cell(r, 3).value for r in range(3, 13)] == [
        "0101", "0102", "0103", "0104", "0101", "0102", "VAR-29", "Postv-0702",
        None, "0105"]
    assert det["D10"].value == "Postv-Hotel Inventado"
    assert det["D9"].value == "Varios partida 29"
    assert det["D12"].value == "Obra Ficticia Centro"


def test_f040_r9_sin_carga_en_el_libro():
    det = _libro(_exportar())["Detalle"]
    fila = [c.value for c in det[11]]
    assert fila[0] == "DELTA PRUEBA CUATRO"
    assert fila[2:] == [None, None, None, 0, None, "SIN CARGA"]


def test_f040_r10_valor_en_todas_las_filas_del_grupo():
    celdas, _ = _xml_hoja(_exportar(), 1)
    for ini, fin in _GRUPOS:
        for col in "ABFGH":
            valores = {celdas[f"{col}{r}"]["v"] for r in range(ini, fin + 1)}
            assert len(valores) == 1, (col, ini, valores)
    assert [celdas[f"A{r}"]["v"] for r in range(3, 7)] == ["ALFA PRUEBA UNO"] * 4
    assert [celdas[f"B{r}"]["v"] for r in range(3, 7)] == ["OFICIAL 1ª"] * 4
    assert [celdas[f"H{r}"]["v"] for r in (7, 8)] == ["FALTA 10%"] * 2
    assert [celdas[f"F{r}"]["v"] for r in (9, 10)] == ["1.1"] * 2
    assert [celdas[f"G{r}"]["v"] for r in (9, 10)] == ["0.1"] * 2


def test_f040_r11_combinadas_solo_en_grupos_de_varias_filas():
    contenido = _exportar()
    _, rangos = _xml_hoja(contenido, 1)
    esperados = {f"{c}{ini}:{c}{fin}" for ini, fin in _GRUPOS if fin > ini
                 for c in "ABFGH"}
    assert set(rangos) == esperados and len(rangos) == len(esperados)
    det = _libro(contenido)["Detalle"]
    for ini, fin in _GRUPOS:
        if fin > ini:
            for c in "ABFGH":
                assert det[f"{c}{ini}"].alignment.vertical == "center"
    assert _xml_hoja(contenido, 2)[1] == []


def test_f040_r12_bandas_alternas_y_linea_gruesa_bajo_cada_trabajador():
    celdas, _ = _xml_hoja(_exportar(), 1)
    for n, (ini, fin) in enumerate(_GRUPOS):
        banda = (_BLANCO, _AZUL)[n % 2]
        for r in range(ini, fin + 1):
            for col in "ABCDEFGH":
                assert celdas[f"{col}{r}"]["fill"] == banda, (col, r)
        for col in "ABCDEFGH":
            assert celdas[f"{col}{fin}"]["bottom"] == ("medium", "FF000000"), col
        for r in range(ini, fin):
            for col in "CDE":
                assert celdas[f"{col}{r}"]["bottom"] == ("thin", "FFBFBFBF")


def test_f040_r13_resumen_una_fila_por_trabajador_sin_bandas():
    contenido = _exportar()
    res = _libro(contenido)["Resumen"]
    assert [c.value for c in res[2]] == [
        "Empleado", "Categoría", "Obras", "Total %", "Estado"]
    assert [res.cell(r, 1).value for r in range(3, 8)] == [
        "ALFA PRUEBA UNO", "BETA PRUEBA DOS", "GAMMA PRUEBA TRES",
        "DELTA PRUEBA CUATRO", "EPSILON PRUEBA CINCO"]
    celdas, _ = _xml_hoja(contenido, 2)
    for r in range(3, 8):
        for col in "ABCDE":
            assert celdas[f"{col}{r}"]["fill"] is None, (col, r)


def test_f040_r14_r15_obras_total_y_estado_en_el_resumen():
    res = _libro(_exportar())["Resumen"]
    assert res["C5"].value == (
        "VAR-29 Varios partida 29 = 80% + Postv-0702 Hotel Inventado = 30%")
    assert res["C7"].value == "0105 Obra Ficticia Centro = 100%"
    assert res["C6"].value is None
    assert res["C3"].alignment.wrap_text is True
    assert res["C3"].alignment.vertical == "top"
    assert [res.cell(r, 4).value for r in range(3, 8)] == [1, 0.9, 1.1, 0, 1]
    assert [res.cell(r, 5).value for r in range(3, 8)] == [
        "OK", "FALTA 10%", "EXCESO 10%", "SIN CARGA", "OK"]


def test_f040_r16_sin_formulas():
    libro = _libro(_exportar())
    for hoja in libro.worksheets:
        for fila in hoja.iter_rows():
            for celda in fila:
                assert celda.data_type != "f", celda.coordinate


def test_f040_r16_99996_sale_ok_y_desviacion_cero_en_el_libro():
    fila = _fila(7, "ZETA", _linea("0101", "A", "33.332"),
                 _linea("0102", "B", "33.332"), _linea("0103", "C", "33.332"))
    contenido = _exportar([fila])
    det = _libro(contenido)["Detalle"]
    assert det["H3"].value == "OK"
    assert det["G3"].value == 0
    # En el XML, «0» y no «-0»: vigila el `+ 0.0` de `_celda_pct`.
    assert _xml_hoja(contenido, 1)[0]["G3"]["v"] == "0"
    assert det["F3"].value == pytest.approx(0.99996)
    assert det["F3"].number_format == "0.00%"


def test_f040_r17_fraccion_y_formato_segun_sea_entero():
    libro = _libro(_exportar())
    det, res = libro["Detalle"], libro["Resumen"]
    assert (det["E3"].value, det["E3"].number_format) == (0.55, "0%")
    assert (det["E7"].value, det["E7"].number_format) == (
        pytest.approx(0.3333), "0.00%")
    assert (det["F7"].value, det["F7"].number_format) == (0.9, "0%")
    assert (det["G7"].value, det["G7"].number_format) == (-0.1, "0%")
    assert (det["G3"].value, det["G3"].number_format) == (0, "0%")
    assert (det["F11"].value, det["F11"].number_format) == (0, "0%")
    assert det["E11"].value is None and det["G11"].value is None
    assert (res["D4"].value, res["D4"].number_format) == (0.9, "0%")
    medio = _exportar([_fila(6, "THETA", _linea("0101", "A", "50.5"))])
    res2, det2 = _libro(medio)["Resumen"], _libro(medio)["Detalle"]
    assert (res2["D3"].value, res2["D3"].number_format) == (0.505, "0.00%")
    assert (det2["G3"].value, det2["G3"].number_format) == (-0.495, "0.00%")
    assert (det2["E3"].value, det2["E3"].number_format) == (0.505, "0.00%")


def test_f040_r18_ningun_texto_en_notacion_cientifica():
    libro = _libro(_exportar())
    textos = [c.value for h in libro.worksheets for f in h.iter_rows(min_row=3)
              for c in f if isinstance(c.value, str)]
    assert "0105 Obra Ficticia Centro = 100%" in textos
    assert all("E+" not in t for t in textos)
