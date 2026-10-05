# tests/test_f029_completar.py
"""F-029 · Completar hasta el 100 % en una obra, por lote (R14-R26).

Tres bloques, uno por capa: la regla pura del dominio
(`domain.estados.completar_hasta_100`), el caso de uso `CompletarHasta100`
con la UnitOfWork en memoria de `test_f024_cuadrante_empresa.py` (sin
editarla: lo que falta se amplía aquí) y la ruta
`POST /periodos/{anio}/{mes}/completar` con la fixture `api` de
`test_f024_rutas_empresa.py`. Ni red, ni BBDD, ni `.env`. La regla, en
`docs/ARCHITECTURE.md#regla-completar`.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from domain.estados import calcular_estado, completar_hasta_100
from domain.models import (
    Completado,
    EstadoTrabajador,
    Linea,
    ResultadoCompletado,
    ResultadoCompletarTrabajador,
    TipoEvento,
)


# ============================== dominio (T1) ============================ #
def _l(obra_ide: int, pct: str, pv: bool = False, cod: str = "") -> Linea:
    return Linea(obra_ide=obra_ide, es_postventa=pv, porcentaje=Decimal(pct),
                 cod=cod)


def _total(lineas: list[Linea]) -> Decimal:
    return sum((ln.porcentaje for ln in lineas), Decimal("0"))


def test_f029_r15_dominio_falta_suma_a_la_linea_existente():
    """R15 · En FALTA con línea en el destino: lo que falta se suma a esa
    línea, en su sitio; las demás salen idénticas (el mismo objeto)."""
    otra = _l(100, "30.00", cod="0100")
    destino = _l(101, "20.50", cod="0101")
    resultado = completar_hasta_100([otra, destino], 101, False)
    assert resultado == Completado(
        lineas=[otra, _l(101, "70.00", cod="0101")], anadido=Decimal("49.50"))
    assert resultado.lineas[0] is otra
    # La sumada conserva el resto de sus datos (código incluido).
    assert resultado.lineas[1].cod == "0101"


def test_f029_r15_dominio_falta_sin_linea_anade_una_al_final():
    """R15 · En FALTA sin línea en el destino: línea nueva al final con lo
    que falta; las demás, idénticas y en su orden."""
    a, b = _l(100, "30"), _l(900, "25.25")
    resultado = completar_hasta_100([a, b], 101, False)
    assert resultado is not None
    assert resultado.lineas[:2] == [a, b]
    assert resultado.lineas[0] is a and resultado.lineas[1] is b
    nueva = resultado.lineas[2]
    assert (nueva.obra_ide, nueva.es_postventa, nueva.porcentaje) == (
        101, False, Decimal("44.75"))
    assert resultado.anadido == Decimal("44.75")
    assert len(resultado.lineas) == 3


def test_f029_r15_dominio_sin_carga_crea_la_linea_del_100():
    """R15 · SIN_CARGA: una sola línea nueva con el 100 %."""
    resultado = completar_hasta_100([], 101, False)
    assert resultado == Completado(
        lineas=[Linea(obra_ide=101, es_postventa=False,
                      porcentaje=Decimal("100.00"))],
        anadido=Decimal("100.00"))


@pytest.mark.parametrize("lineas", [
    [_l(100, "60"), _l(101, "40")],          # exacto
    [_l(100, "99.995")],                      # dentro de la épsilon (OK)
    [_l(100, "100.005")],                     # dentro de la épsilon (OK)
])
def test_f029_r17_dominio_ok_no_se_toca(lineas):
    """R17 · OK (con la misma épsilon que `calcular_estado`): nada."""
    assert calcular_estado(_total(lineas), len(lineas)) is EstadoTrabajador.OK
    assert completar_hasta_100(lineas, 101, False) is None


@pytest.mark.parametrize("lineas", [
    [_l(100, "60"), _l(101, "40.01")],
    [_l(101, "150")],
])
def test_f029_r17_dominio_exceso_no_se_toca(lineas):
    """R17 · EXCESO: nada (ni se resta)."""
    assert calcular_estado(_total(lineas),
                           len(lineas)) is EstadoTrabajador.EXCESO
    assert completar_hasta_100(lineas, 101, False) is None


def test_f029_r16_dominio_falta_0_01_se_completa_y_queda_en_100_00():
    """D5 · Falta 0,01 (fuera de la épsilon de 0,005): se completa y el
    total queda exactamente en 100,00, estado OK."""
    resultado = completar_hasta_100([_l(100, "99.99")], 100, False)
    assert resultado is not None
    assert resultado.anadido == Decimal("0.01")
    assert _total(resultado.lineas) == Decimal("100.00")
    assert calcular_estado(_total(resultado.lineas),
                           len(resultado.lineas)) is EstadoTrabajador.OK


@pytest.mark.parametrize("lineas, obra, pv", [
    ([_l(100, "33.33"), _l(900, "33.33")], 101, False),
    ([_l(100, "12.34", pv=True)], 100, False),
    ([_l(100, "0.01")], 100, True),
])
def test_f029_r16_dominio_el_total_queda_exactamente_en_100(lineas, obra, pv):
    """R16 · Tras completar, total = 100,00 exacto y estado OK."""
    resultado = completar_hasta_100(lineas, obra, pv)
    assert resultado is not None
    assert _total(resultado.lineas) == Decimal("100.00")
    assert resultado.anadido == Decimal("100.00") - _total(lineas)


def test_f029_r16_dominio_lo_que_falta_va_a_escala_de_centesimas():
    """D5 · La escala de la columna (`Numeric(6,2)`): lo añadido sale con
    dos decimales aunque el total llegue con más."""
    resultado = completar_hasta_100([_l(100, "50.004")], 101, False)
    assert resultado is not None
    assert resultado.anadido == Decimal("50.00")
    assert resultado.anadido.as_tuple().exponent == -2


def test_f029_r18_dominio_postventa_no_suma_a_la_normal_ni_al_reves():
    """R18 · `es_postventa` es parte de la clave (`#regla-p5`)."""
    normal = _l(100, "40")
    resultado = completar_hasta_100([normal], 100, True)
    assert resultado is not None
    assert resultado.lineas[0] is normal
    assert resultado.lineas[1].clave() == (100, True)
    assert resultado.lineas[1].porcentaje == Decimal("60.00")

    postv = _l(100, "40", pv=True)
    resultado = completar_hasta_100([postv], 100, False)
    assert resultado is not None
    assert resultado.lineas[0] is postv
    assert resultado.lineas[1].clave() == (100, False)

    resultado = completar_hasta_100([normal, postv], 100, True)
    assert resultado is not None
    assert resultado.lineas == [normal, _l(100, "60.00", pv=True)]


def test_f029_r19_dominio_tipos_nuevos():
    """R19, R25 · El evento `COMPLETAR` y los resultados posibles, con el
    valor igual al nombre; el resultado por trabajador lleva 0 por defecto."""
    assert TipoEvento.COMPLETAR.value == "COMPLETAR"
    assert [r.value for r in ResultadoCompletado] == [
        "COMPLETADO", "YA_AL_100", "EXCESO", "NO_VIGENTE", "NO_VISIBLE"]
    r = ResultadoCompletarTrabajador(trabajador_ide=7,
                                     resultado=ResultadoCompletado.NO_VISIBLE)
    assert r.anadido == Decimal("0")
