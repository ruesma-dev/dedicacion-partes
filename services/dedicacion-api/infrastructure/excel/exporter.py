# infrastructure/excel/exporter.py
"""Exportación a Excel del periodo, con el modelo de negocio (F-040, F-045).

Tres hojas:
  - "Obras" y "Postventa": una fila por línea de esa parte, agrupadas por
    trabajador, y al final del grupo UNA línea agregada («RESTO POSTVENTA» o
    «RESTO OBRAS», en cursiva) con la suma de la otra parte. Empleado,
    Categoría, Total, Desviación y Estado son los del trabajador completo y
    van en todas las filas del grupo y combinadas (con el valor en todas,
    para que el autofiltro saque el grupo entero). Bandas blanco / azul claro
    y línea gruesa bajo cada trabajador.
  - "Detalle": la hoja de F-040, igual que antes: todas las líneas de cada
    trabajador agrupadas, la postventa intercalada con su prefijo y sin
    línea agregada. No hay hoja Resumen (F-045 D2).

Lo que se escribe sale de `contenido.py`; aquí solo se pinta.
"""
from __future__ import annotations

import io
from decimal import Decimal

from domain.models import CuadranteTrabajador, Periodo
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.merge import MergedCellRange

from infrastructure.excel.contenido import (
    GrupoTrabajador,
    es_entero,
    grupos_detalle,
    grupos_pestana,
)

_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

_CABECERA_FILL = PatternFill("solid", fgColor="1F3864")
_CABECERA_FONT = Font(color="FFFFFF", bold=True)
_BANDAS = (PatternFill("solid", fgColor="FFFFFF"),
           PatternFill("solid", fgColor="DDEBF7"))
_FINO = Side(style="thin", color="BFBFBF")
_GRUESO = Side(style="medium", color="000000")
_BORDE = Border(left=_FINO, right=_FINO, top=_FINO, bottom=_FINO)
_BORDE_ULTIMA = Border(left=_FINO, right=_FINO, top=_FINO, bottom=_GRUESO)
_CENTRADA = Alignment(vertical="center")
#: Código, Obra y % de la línea agregada (F-045 R15).
_CURSIVA = Font(italic=True)

_CABECERA_DETALLE = [
    "Empleado", "Categoría", "Código", "Obra", "% dedicación",
    "Total empleado", "Desviación", "Estado",
]
_ANCHOS_DETALLE = (34, 22, 12, 44, 13, 15, 12, 16)
#: Columnas del Detalle que se combinan por trabajador: A, B, F, G y H.
_COMBINADAS = (1, 2, 6, 7, 8)


class OpenpyxlExcelExporter:
    def __init__(self, prefijo_postventa: str = "Postv-") -> None:
        self._prefijo = prefijo_postventa

    # ------------------------------------------------------------------
    def exportar(
        self, periodo: Periodo, filas: list[CuadranteTrabajador]
    ) -> bytes:
        p = self._prefijo
        libro = Workbook()
        self._hoja_grupos(libro.active, "Obras", f"OBRAS · {_mes(periodo)}",
                          grupos_pestana(filas, p, postventa=False))
        self._hoja_grupos(libro.create_sheet(), "Postventa",
                          f"POSTVENTA · {_mes(periodo)}",
                          grupos_pestana(filas, p, postventa=True))
        self._hoja_grupos(libro.create_sheet(), "Detalle",
                          f"DETALLE DE DEDICACIÓN · {_mes(periodo)}",
                          grupos_detalle(filas, p))
        buffer = io.BytesIO()
        libro.save(buffer)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    def _hoja_grupos(
        self, hoja, nombre: str, titulo: str, grupos: list[GrupoTrabajador]
    ) -> None:
        hoja.title = nombre
        _titulo_y_cabecera(hoja, titulo, _CABECERA_DETALLE)
        fila = 3
        for n, grupo in enumerate(grupos):
            ini, fin = fila, fila + len(grupo.lineas) - 1
            for r, linea in zip(range(ini, fin + 1), grupo.lineas):
                hoja.cell(r, 1, grupo.empleado)
                hoja.cell(r, 2, grupo.categoria)
                hoja.cell(r, 3, linea.codigo)
                hoja.cell(r, 4, linea.obra)
                _celda_pct(hoja.cell(r, 5), linea.porcentaje)
                _celda_pct(hoja.cell(r, 6), grupo.total)
                _celda_pct(hoja.cell(r, 7), grupo.desviacion)
                hoja.cell(r, 8, grupo.estado)
                for col in range(1, 9):
                    celda = hoja.cell(r, col)
                    celda.fill = _BANDAS[n % 2]
                    celda.border = _BORDE_ULTIMA if r == fin else _BORDE
                if linea.agregada:
                    for col in (3, 4, 5):
                        hoja.cell(r, col).font = _CURSIVA
            if fin > ini:
                for col in _COMBINADAS:
                    _combinar_con_valor(hoja, col, ini, fin)
            fila = fin + 1
        _rematar(hoja, _ANCHOS_DETALLE, fila - 1)


def _mes(periodo: Periodo) -> str:
    return f"{_MESES[periodo.mes - 1]} {periodo.anio}"


def _titulo_y_cabecera(hoja, titulo: str, cabecera: list[str]) -> None:
    hoja.cell(1, 1, titulo).font = Font(bold=True, size=13)
    for col, texto in enumerate(cabecera, start=1):
        celda = hoja.cell(2, col, texto)
        celda.fill = _CABECERA_FILL
        celda.font = _CABECERA_FONT
        celda.alignment = _CENTRADA


def _combinar_con_valor(hoja, columna: int, desde: int, hasta: int) -> None:
    """Combina sin vaciar las celdas no ancla (design §5).

    `merge_cells()` las convertiría en `MergedCell` sin valor y el autofiltro
    perdería las filas del grupo; añadir el rango a mano conserva el valor.
    """
    letra = get_column_letter(columna)
    hoja.merged_cells.add(MergedCellRange(hoja, f"{letra}{desde}:{letra}{hasta}"))
    for r in range(desde, hasta + 1):
        hoja.cell(r, columna).alignment = _CENTRADA


def _celda_pct(celda, valor: Decimal | None) -> None:
    """La fracción (55 % → 0,55) con `0%` si es entero y `0.00%` si no."""
    if valor is None:
        return
    celda.value = float(valor) / 100 + 0.0  # + 0.0: sin «-0» en el libro
    celda.number_format = "0%" if es_entero(valor) else "0.00%"


def _rematar(hoja, anchos: tuple[int, ...], ultima: int) -> None:
    """Autofiltro, paneles, anchos e impresión (R3, R4)."""
    ultima_col = get_column_letter(len(anchos))
    hoja.auto_filter.ref = f"A2:{ultima_col}{max(ultima, 2)}"
    hoja.freeze_panes = "A3"
    for col, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(col)].width = ancho
    hoja.page_setup.orientation = "landscape"
    hoja.sheet_properties.pageSetUpPr.fitToPage = True
    hoja.page_setup.fitToWidth = 1
    hoja.page_setup.fitToHeight = 0
    hoja.print_title_rows = "1:2"
