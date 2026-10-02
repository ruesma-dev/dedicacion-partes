# tests/test_f034_obras_siempre_ruesma.py
"""F-034 · Las obras son siempre de la empresa de las obras; el selector
filtra solo trabajadores (R1-R3, R5, R7, R8, R10).

La empresa de las obras es el ajuste `EMPRESA_IMPUTACION` (D1), que sigue
siendo además la por defecto del selector. En el dominio van como dos campos
de `FiltroEmpresa` (`empresa_obras` y `por_defecto`): los tests los separan a
propósito para probar que cada regla lee el suyo. La regla de negocio está en
`docs/ARCHITECTURE.md#regla-empresa`.

Offline: UnitOfWork en memoria de `test_f024_cuadrante_empresa.py` y sesión
y transfer falsos de `test_f024_registro_empresa.py`. Ni red, ni BBDD, ni
`.env`.
"""
from __future__ import annotations

import pytest
from domain.empresas import visible_en_empresa
from domain.models import FiltroEmpresa

#: Empresa de las obras y por defecto (Construcciones Ruesma).
RUESMA = 1


def _f(empresa: int, por_defecto: int = RUESMA,
       empresa_obras: int = RUESMA) -> FiltroEmpresa:
    return FiltroEmpresa(empresa=empresa, por_defecto=por_defecto,
                         empresa_obras=empresa_obras)


# ================================ R2 / R3 =============================== #
@pytest.mark.parametrize("empresa_trab, elegida, visible", [
    (1, 1, True), (1, 18, False), (1, 28, False),
    (18, 18, True), (18, 1, False), (28, 28, True), (28, 18, False),
])
def test_f034_r2_trabajador_con_empresa_solo_en_la_suya(
        empresa_trab, elegida, visible):
    assert visible_en_empresa(empresa_trab, _f(elegida)) is visible


def test_f034_r3_null_lee_la_por_defecto_no_la_empresa_de_las_obras():
    """Con la por defecto ≠ empresa de las obras, el NULL sigue a la por
    defecto: separar mañana los dos papeles de EMPRESA_IMPUTACION (D1) no
    cambia R3."""
    assert visible_en_empresa(None, _f(18, por_defecto=18)) is True
    assert visible_en_empresa(None, _f(1, por_defecto=18)) is False


def test_f034_r2_con_empresa_no_lee_la_empresa_de_las_obras():
    """Un trabajador de la 1 con E = 18 no se ve aunque la 1 sea la empresa
    de las obras: el selector filtra trabajadores por la suya."""
    assert visible_en_empresa(1, _f(18, por_defecto=18)) is False
    assert visible_en_empresa(18, _f(18, empresa_obras=18)) is True


def test_f034_r10_filtro_lleva_la_empresa_de_las_obras_sin_valor_por_defecto():
    """`empresa_obras` es obligatorio: nadie construye un filtro sin decir
    cuál es la empresa de las obras."""
    with pytest.raises(TypeError):
        FiltroEmpresa(empresa=18, por_defecto=1)  # type: ignore[call-arg]
    filtro = _f(18)
    assert (filtro.empresa, filtro.por_defecto, filtro.empresa_obras) == (
        18, 1, 1)
