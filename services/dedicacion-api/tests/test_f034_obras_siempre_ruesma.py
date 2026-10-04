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
from application.registro_sigrid import RegistroSigrid
from application.use_cases import ObtenerCuadrante
from domain.empresas import visible_en_empresa
from domain.models import FiltroEmpresa

from tests.test_f024_cuadrante_empresa import ANIO, MES, _uow
from tests.test_f024_registro_empresa import _fila, _lineas, _Sesion, _Transfer

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


# ================================== R1 ================================== #
@pytest.mark.parametrize("elegida", [1, 18, 28])
def test_f034_r1_obras_leen_la_empresa_de_las_obras_no_la_elegida(elegida):
    """Las obras ofrecidas salen de `empresa_obras`, no de E ni de la por
    defecto: con la por defecto = E y la empresa de las obras en la 1, se
    ofrecen las de la 1 (activas o inactivas con líneas), nunca la 900 de la
    28 ni la 500 sin empresa."""
    filtro = _f(elegida, por_defecto=elegida)
    cuadrante = ObtenerCuadrante().ejecutar(_uow(), ANIO, MES, filtro,
                                            usuario="u")
    assert [o.ide for o in cuadrante.obras] == [100, 101, 102]
    assert cuadrante.empresa == elegida


def test_f034_r1_obras_de_la_28_si_la_empresa_de_las_obras_fuera_la_28():
    """La empresa de las obras sale del filtro, no de un 1 fijo."""
    cuadrante = ObtenerCuadrante().ejecutar(_uow(), ANIO, MES,
                                            _f(1, empresa_obras=28),
                                            usuario="u")
    assert [o.ide for o in cuadrante.obras] == [900]


# ================================== R4 ================================== #
@pytest.mark.parametrize("elegida, nombres, total", [
    (1, ["Ana", "Carlos", "Dani", "Eva", "Gil"], 5),
    (28, ["Bea"], 1),
    (18, ["Fran"], 1),
])
def test_f034_r4_filas_y_resumen_con_la_visibilidad_nueva(elegida, nombres,
                                                         total):
    """El cuadrante y su resumen cuentan solo los visibles en E con R2-R3;
    cada fila lleva todas sus líneas (Gil, NULL, con su línea de la 28)."""
    cuadrante = ObtenerCuadrante().ejecutar(_uow(), ANIO, MES, _f(elegida),
                                            usuario="u")
    assert [f.trabajador.nombre for f in cuadrante.filas] == nombres
    assert cuadrante.resumen.total == total
    if elegida == 1:
        gil = cuadrante.filas[-1]
        assert [ln.obra_empresa for ln in gil.lineas] == [1, 28]


# ============================ R7 / R8 / R10 ============================= #
#: Trabajador 20 de la 18 con una línea en una obra de Ruesma (678) y otra
#: en una obra de la 28 (9); 21 de la 31 en una obra de Ruesma; 22 sin
#: empresa en una obra de Ruesma.
FILAS_18 = [
    _fila(30, (20, 18), (678, 1)),
    _fila(31, (20, 18), (9, 28)),
    _fila(32, (21, 31), (678, 1)),
    _fila(33, (22, None), (678, 1)),
]


def _registro_18(transfer: _Transfer, updates: list[dict] | None = None,
                 empresa_imputacion: int = RUESMA) -> RegistroSigrid:
    anotadas = updates if updates is not None else []
    return RegistroSigrid(lambda: _Sesion(FILAS_18, anotadas), transfer,
                          empresa_imputacion)


def _llamar(registro: RegistroSigrid, fase: str, empresa: int | None) -> dict:
    if fase == "preflight":
        return registro.preflight(2026, 9, empresa=empresa)
    return registro.ejecutar(2026, 9, pisar_claves=[], empresa=empresa)


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
@pytest.mark.parametrize("empresa, esperadas", [
    (18, [(30, 1), (31, 1)]),     # el de la 18, con la empresa de las obras
    (31, [(32, 1)]),
    (1, [(33, 1)]),               # el NULL, solo en la por defecto
    (None, [(33, 1)]),
    (28, []),
])
def test_f034_r7_lineas_de_los_visibles_con_la_empresa_de_las_obras(
        fase, empresa, esperadas):
    """Un trabajador de la 18 registra en una obra de Ruesma: su línea viaja
    con `empresa` = 1, no con la elegida."""
    transfer = _Transfer()
    r = _llamar(_registro_18(transfer), fase, empresa)
    assert sorted(_lineas(transfer)) == esperadas
    assert r["ok"] is True


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f034_r10_la_empresa_de_las_obras_sale_del_ajuste(fase):
    """La empresa de cada línea es EMPRESA_IMPUTACION, no un 1 fijo ni la
    elegida: con el ajuste en la 28 y E = 18, las líneas viajan con la 28."""
    transfer = _Transfer()
    _llamar(_registro_18(transfer, empresa_imputacion=28), fase, 18)
    assert sorted(_lineas(transfer)) == [(30, 28), (31, 28)]


def test_f034_r8_obra_de_otra_empresa_se_manda_y_su_omision_se_traza():
    """La línea 31 (obra 9, de la 28) de un trabajador de la 18 se manda con
    `empresa` = 1; el transfer la omite con motivo y queda trazada."""
    motivo = ("la obra 09 es de la empresa 28 y la línea se imputa a la "
              "empresa 1: no se escribe")
    transfer = _Transfer({"ok": True, "escritas": [], "ya_registradas": [],
                          "omitidas": [{"registro_id": 31,
                                        "motivo": motivo}]})
    updates: list[dict] = []
    _registro_18(transfer, updates).ejecutar(2026, 9, pisar_claves=[],
                                             empresa=18)
    obra_9 = [p for p in transfer.payloads if p["obra"]["ide"] == 9]
    assert [(lin["registro_id"], lin["empresa"])
            for lin in obra_9[0]["lineas"]] == [(31, 1)]
    # El transfer falso contesta lo mismo a cada obra: la 31 se traza una
    # vez por obra mandada; lo que importa es qué y con qué motivo.
    omitidos = [u for u in updates if u.get("sigrid_estado") == "omitido"]
    assert {(u["id_1"], u["sigrid_motivo"]) for u in omitidos} == {
        (31, motivo)}
