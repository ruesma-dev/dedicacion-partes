# tests/test_f002_reglas.py
"""F-002 · Reglas del registro que NO están en disputa (R6-R9, R12).

Se prueban contra `ReglasPorcentajes` directamente, sin pipeline: lo que se
vigila aquí es la decisión por línea, no la orquestación. Los enunciados
normativos viven en `docs/ARCHITECTURE.md` § Semántica de dominio
imprescindible (`#regla-p1`, `#regla-p2`, `#regla-p3`, `#regla-p5`).
"""
from __future__ import annotations

import pytest

from application.services.reglas_porcentajes import ReglasPorcentajes
from domain.models.registro_models import HoraRecurso

from tests.conftest import linea

#: Recurso 200: encargado con código mensual MENC de 9.000 €/mes.
#: Recurso 300: solo horas de convenio, ningún M*.
HORAS = {
    200: [HoraRecurso(5, "MENC", None, 9000.0),
          HoraRecurso(9, "HEGR", None, 30.0)],
    300: [HoraRecurso(1, "HLPE", None, 20.0),
          HoraRecurso(9, "HEGR", None, 30.0)],
}

PARTIDA_PV = {"ide": 70001, "cod": "0678", "res": "15 VIVIENDAS Y HOSTEL"}


def _reglas(**kw) -> ReglasPorcentajes:
    return ReglasPorcentajes(HORAS, **kw)


# ------------------------------- R6 -------------------------------- #

def test_f002_r6_sin_mensual_se_omite():
    """R6 · Sin código de hora M* la línea se omite con motivo, sin error."""
    a = _reglas().decidir(linea(recurso_ide=300, empleado_ide=None))
    assert a.accion == "omitir", a
    assert "mensual" in (a.motivo or ""), a.motivo
    # Omitir no es fallar: la línea sigue siendo trazable por su registro.
    assert a.registro_id == 1 and a.hora_ide is None


def test_f002_r6_sin_recurso_resuelto_se_omite():
    """R6 · Sin recurso en Sigrid tampoco hay nada que registrar."""
    a = _reglas().decidir(linea(recurso_ide=None, empleado_ide=10))
    assert a.accion == "omitir" and "recurso" in (a.motivo or ""), a


def test_f002_r6_con_mensual_se_escribe():
    """R6 · Control positivo: con M* la línea sí se escribe (si no, el test
    de arriba pasaría con una regla que omite siempre)."""
    a = _reglas().decidir(linea(recurso_ide=200, empleado_ide=None))
    assert a.accion == "escribir" and a.hora_codigo == "MENC", a


# ------------------------------- R7 -------------------------------- #

@pytest.mark.parametrize("ano, mes, esperado", [
    (2026, 7, 20260731),      # 31 días
    (2026, 2, 20260228),      # febrero común
    (2024, 2, 20240229),      # febrero bisiesto
    (2026, 4, 20260430),      # 30 días
    (2026, 12, 20261231),     # cierre de año
    (2026, 1, 20260131),      # mes de un solo dígito -> se rellena con cero
])
def test_f002_r7_fecha_ultimo_dia_mes(ano, mes, esperado):
    """R7 · `fec` es SIEMPRE el último día natural del mes del periodo."""
    a = _reglas().decidir(linea(ano=ano, mes=mes, recurso_ide=200,
                                empleado_ide=None))
    assert a.accion == "escribir"
    assert a.fecha_int == esperado, (ano, mes, a.fecha_int)


def test_f002_r7_la_fecha_no_depende_del_dia_de_captura():
    """R7 · Dos capturas del mismo periodo dan la misma fecha: la línea no
    lleva el día en que se trabajó ni el día en que se tecleó."""
    reglas = _reglas()
    a = reglas.decidir(linea(registro_id=1, recurso_ide=200,
                             empleado_ide=None))
    b = reglas.decidir(linea(registro_id=2, recurso_ide=200,
                             empleado_ide=None, porcentaje=0.6))
    assert a.fecha_int == b.fecha_int == 20260731


# ------------------------------- R8 -------------------------------- #

def test_f002_r8_can_pre_tot():
    """R8 · can = porcentaje sobre 1, pre = importe mensual, tot = can×pre."""
    a = _reglas().decidir(linea(porcentaje=0.4, recurso_ide=200,
                                empleado_ide=None))
    assert a.can == 0.4
    assert a.pre == 9000.0
    assert a.tot == 3600.0


def test_f002_r8_tot_se_redondea_a_dos_decimales():
    """R8 · `tot` es dinero: dos decimales, no el float crudo."""
    a = _reglas().decidir(linea(porcentaje=0.333333, recurso_ide=200,
                                empleado_ide=None))
    assert a.can == 0.3333               # el porcentaje, a cuatro decimales
    assert a.tot == 2999.70              # round(0.3333 × 9000, 2)


def test_f002_r8_el_porcentaje_no_viaja_sobre_100():
    """R8 · El 40 % viaja como 0.4. Si alguien mandara 40 no se escribe
    (R9): confundir las escalas escribiría 100 veces el importe."""
    a = _reglas().decidir(linea(porcentaje=0.4, recurso_ide=200,
                                empleado_ide=None))
    assert a.can == 0.4 and a.tot == 3600.0
    assert a.tot < 9000.0


# ------------------------------- R9 -------------------------------- #

@pytest.mark.parametrize("porcentaje", [0.0, -0.1, 1.0001, 40, 100, None,
                                        "cuarenta"])
def test_f002_r9_porcentaje_fuera_de_rango(porcentaje):
    """R9 · Fuera de (0, 1] la línea se omite con motivo y no se escribe."""
    a = _reglas().decidir(linea(porcentaje=porcentaje, recurso_ide=200,
                                empleado_ide=None))
    assert a.accion == "omitir", (porcentaje, a)
    assert "rango" in (a.motivo or ""), a.motivo
    assert a.can is None and a.tot is None


@pytest.mark.parametrize("porcentaje", [1.0, 0.0001])
def test_f002_r9_los_bordes_validos_se_escriben(porcentaje):
    """R9 · El intervalo es ABIERTO por abajo y CERRADO por arriba: el 100 %
    entra, el 0 % no."""
    a = _reglas().decidir(linea(porcentaje=porcentaje, recurso_ide=200,
                                empleado_ide=None))
    assert a.accion == "escribir", (porcentaje, a)


# ------------------------------- R12 ------------------------------- #

def test_f002_r12_postventa_desactivada():
    """R12 · Con POSTVENTA_REGISTRAR desactivado, la línea de postventa se
    omite con motivo explícito y NO cae en la obra normal."""
    a = _reglas(postventa_registrar=False,
                partida_postventa=PARTIDA_PV).decidir(
        linea(recurso_ide=200, empleado_ide=None, es_postventa=True))
    assert a.accion == "omitir", a
    assert "POSTVENTA_REGISTRAR" in (a.motivo or ""), a.motivo
    assert a.destino == "obra" and a.paride == 0    # no se escribe nada


def test_f002_r12_postventa_activada_va_a_la_obra_de_postventa():
    """R12 · Control positivo: con el ajuste activo la misma línea sí se
    escribe, y su destino es la obra de postventa."""
    a = _reglas(postventa_registrar=True,
                partida_postventa=PARTIDA_PV).decidir(
        linea(recurso_ide=200, empleado_ide=None, es_postventa=True))
    assert a.accion == "escribir" and a.destino == "postventa", a
    assert a.paride == 70001


def test_f002_r12_la_linea_normal_no_se_ve_afectada():
    """R12 · Desactivar la postventa no toca a las líneas normales."""
    a = _reglas(postventa_registrar=False).decidir(
        linea(recurso_ide=200, empleado_ide=None))
    assert a.accion == "escribir" and a.destino == "obra", a
