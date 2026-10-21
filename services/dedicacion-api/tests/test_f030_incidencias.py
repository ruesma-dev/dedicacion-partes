# tests/test_f030_incidencias.py
"""F-030 · Incidencias en el cuadrante: dominio, esquema, guardado,
deshacer y copias (R4, R5, R17-R22).

Offline: funciones puras, metadatos del ORM y casos de uso con una
UnitOfWork en memoria. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

import pytest
from domain.errors import ErrorDominio, IncidenciaInvalida
from domain.incidencias import completar_dias, letra_y_nombre, validar_incidencias
from domain.models import Incidencia


# ============================ dominio (T2) ============================== #
@pytest.mark.parametrize("res, cod, esperado", [
    ("Vacaciones(V)", "CIV", ("V", "Vacaciones")),
    ("Falta Justificada/Permiso(FJ)", "CIP", ("FJ", "Falta Justificada/Permiso")),
    ("Accidente/Enf. Profesional(AT)", "CIA", ("AT", "Accidente/Enf. Profesional")),
    ("Enfermedad/Acc. no laboral(B)", "CIE", ("B", "Enfermedad/Acc. no laboral")),
    ("  Huelga (H)  ", "CIH", ("H", "Huelga")),
    ("Maternidad/Paternidad( M )", "CIM", ("M", "Maternidad/Paternidad")),
])
def test_f030_r4_dominio_letra_entre_parentesis_al_final(res, cod, esperado):
    assert letra_y_nombre(res, cod) == esperado


@pytest.mark.parametrize("res, cod, esperado", [
    ("Fin de Incidencia", "CIZ", ("Z", "Fin de Incidencia")),
    ("Otra cosa", " CIQ ", ("Q", "Otra cosa")),
    ("Sin letra()", "CIX", ("X", "Sin letra()")),
    ("(V) delante", "CIV", ("V", "(V) delante")),
    ("Raro", "XYZ", ("XYZ", "Raro")),
    (None, "CIV", ("V", "")),
    ("   ", "CIV", ("V", "")),
])
def test_f030_r4_dominio_sin_parentesis_la_letra_es_el_codigo_sin_ci(res, cod, esperado):
    assert letra_y_nombre(res, cod) == esperado


@pytest.mark.parametrize("desde, hasta, anio, mes, esperado", [
    (None, None, 2026, 9, (1, 30)),
    (None, None, 2026, 10, (1, 31)),
    (None, None, 2026, 2, (1, 28)),
    (None, None, 2028, 2, (1, 29)),
    (5, None, 2026, 9, (5, 30)),
    (None, 9, 2026, 9, (1, 9)),
    (5, 9, 2026, 9, (5, 9)),
    (31, 31, 2026, 9, (31, 31)),   # completar no valida: lo hace validar
])
def test_f030_r17_dominio_completar_dias(desde, hasta, anio, mes, esperado):
    assert completar_dias(desde, hasta, anio, mes) == esperado


def _inc(desde: int, hasta: int, obra: int = 1, cod: str = "CIV") -> Incidencia:
    return Incidencia(obra_ide=obra, codigo=cod, dia_desde=desde, dia_hasta=hasta)


@pytest.mark.parametrize("lista", [
    [],
    [_inc(1, 30)],
    [_inc(1, 1)],
    [_inc(30, 30)],
    [_inc(1, 4), _inc(5, 9), _inc(10, 30)],
    [_inc(10, 12), _inc(1, 9)],             # el orden de llegada no importa
    [_inc(5, 9, obra=1), _inc(10, 10, obra=2, cod="CIE")],
])
def test_f030_r19_dominio_validas(lista):
    assert validar_incidencias(lista, 2026, 9) is None


@pytest.mark.parametrize("lista, motivo", [
    ([_inc(0, 3)], "fuera del mes"),
    ([_inc(3, 31)], "fuera del mes"),
    ([_inc(31, 31)], "fuera del mes"),
    ([_inc(-1, 3)], "fuera del mes"),
    ([_inc(9, 5)], "posterior"),
    ([_inc(5, 9), _inc(9, 12)], "comparten"),
    ([_inc(5, 9), _inc(1, 5)], "comparten"),
    ([_inc(1, 30), _inc(10, 12, obra=2, cod="CIE")], "comparten"),
    ([_inc(1, 3), _inc(10, 20), _inc(15, 15)], "comparten"),
    ([_inc(10, 20), _inc(1, 3), _inc(2, 2)], "comparten"),
])
def test_f030_r19_dominio_invalidas_con_motivo(lista, motivo):
    with pytest.raises(IncidenciaInvalida, match=motivo):
        validar_incidencias(lista, 2026, 9)


def test_f030_r19_dominio_febrero_bisiesto_y_no_bisiesto():
    assert validar_incidencias([_inc(29, 29)], 2028, 2) is None
    with pytest.raises(IncidenciaInvalida, match="fuera del mes"):
        validar_incidencias([_inc(29, 29)], 2026, 2)


def test_f030_r19_dominio_el_error_es_de_dominio():
    assert issubclass(IncidenciaInvalida, ErrorDominio)
