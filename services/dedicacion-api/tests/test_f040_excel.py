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

from decimal import Decimal

import pytest
from domain.models import CuadranteTrabajador, EstadoTrabajador, Linea, Trabajador
from infrastructure.excel.contenido import (
    es_entero,
    filas_resumen,
    grupos_detalle,
    texto_estado,
    texto_pct,
)

_PREFIJO = "Postv-"


# ----------------------------------------------------------------------
# Fábricas de datos inventados
# ----------------------------------------------------------------------
def _trabajador(ide: int, nombre: str, categoria: str | None = "OFICIAL 1ª"):
    return Trabajador(ide=ide, cod=str(ide), nombre=nombre, dni=None,
                      categoria=categoria)


def _linea(cod: str, descripcion: str, pct: str, postventa: bool = False):
    return Linea(obra_ide=hash((cod, postventa)) & 0xFFFF, es_postventa=postventa,
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
    assert postv.porcentaje == Decimal("30")
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
    assert delta.total == Decimal("0")
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
        Decimal("100"), Decimal("90"), Decimal("110"), Decimal("0"), Decimal("100")]


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
    assert es_entero(Decimal("55"))
    assert not es_entero(Decimal("33.33"))
    assert not es_entero(Decimal("0.5"))


def test_f040_r19_textos_de_estado():
    assert texto_estado(EstadoTrabajador.OK, Decimal("0")) == "OK"
    assert texto_estado(EstadoTrabajador.SIN_CARGA, Decimal("0")) == "SIN CARGA"
    assert texto_estado(EstadoTrabajador.FALTA, Decimal("-10.00")) == "FALTA 10%"
    assert texto_estado(EstadoTrabajador.EXCESO, Decimal("10.00")) == "EXCESO 10%"
    assert texto_estado(EstadoTrabajador.FALTA, Decimal("-0.50")) == "FALTA 0,50%"
    assert texto_estado(EstadoTrabajador.EXCESO, Decimal("33.33")) == "EXCESO 33,33%"
