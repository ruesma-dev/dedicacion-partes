# tests/test_f024_cuadrante_empresa.py
"""F-024 · Cuadrante, resumen, copia y lista de empresas con la empresa
elegida (R1, R2, R7, R9, R10, R13, R14).

Offline: el repositorio se prueba con una sesión falsa que captura la
sentencia, y los casos de uso con una UnitOfWork en memoria. Ni red, ni BBDD,
ni `.env`. La regla está en `docs/ARCHITECTURE.md#regla-empresa`.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from application.use_cases import (
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    ObtenerCuadrante,
    ObtenerFilaTrabajador,
)
from domain.models import (
    FiltroEmpresa,
    Linea,
    Obra,
    Periodo,
    ResumenPeriodo,
    Trabajador,
)
from infrastructure.db.repositories import PgTrabajadorRepository, _a_linea
from sqlalchemy.dialects import postgresql


# ============================ repositorio (T2) ========================== #
class _Escalares:
    def __init__(self, valores: list[Any]) -> None:
        self._valores = valores

    def all(self) -> list[Any]:
        return list(self._valores)


class _SesionCaptura:
    """Sesión falsa: guarda la sentencia y devuelve los valores fijados."""

    def __init__(self, valores: list[Any]) -> None:
        self.valores = valores
        self.sentencias: list[Any] = []

    def scalars(self, stmt: Any) -> _Escalares:
        self.sentencias.append(stmt)
        return _Escalares(self.valores)


def _sql(stmt: Any) -> str:
    return " ".join(str(stmt.compile(dialect=postgresql.dialect())).split())


def test_f024_r1_empresas_activas_solo_activos_y_sin_null():
    """R1 · La consulta pide empresas DISTINTAS de trabajadores activos y
    con empresa; el repositorio devuelve un conjunto."""
    sesion = _SesionCaptura([31, 1, 18])
    empresas = PgTrabajadorRepository(sesion).empresas_activas()  # type: ignore[arg-type]
    assert empresas == {1, 18, 31}
    [stmt] = sesion.sentencias
    sql = _sql(stmt)
    assert sql.startswith("SELECT DISTINCT trabajador.empresa FROM trabajador")
    assert "trabajador.activo IS true" in sql
    assert "trabajador.empresa IS NOT NULL" in sql


def test_f024_r11_a_linea_mapea_la_empresa_de_la_obra():
    """R11 · La línea lleva la empresa de su obra (NULL incluido)."""
    asignacion = SimpleNamespace(obra_ide=7, es_postventa=False,
                                 porcentaje=Decimal("40.00"))
    for empresa in (28, None):
        obra = SimpleNamespace(cod="0009", descripcion="OBRA", activa=True,
                               empresa=empresa)
        assert _a_linea(asignacion, obra).obra_empresa == empresa  # type: ignore[arg-type]


# ========================= casos de uso (T3) ============================ #
#: Empresa por defecto de los tests (EMPRESA_IMPUTACION).
DEF = 1
ANIO, MES = 2026, 7
#: Periodo en curso (id 2) y el anterior con datos (id 1).
P_ACT, P_ANT = 2, 1


def _t(ide: int, nombre: str, empresa: int | None,
       activo: bool = True) -> Trabajador:
    return Trabajador(ide=ide, cod=str(ide), nombre=nombre, dni=None,
                      categoria="Encargado", activo=activo, empresa=empresa)


def _o(ide: int, empresa: int | None, activa: bool = True) -> Obra:
    return Obra(ide=ide, cod=f"{ide:04d}", descripcion=f"OBRA {ide}",
                estado_sigrid=None, activa=activa, empresa=empresa)


OBRAS = {o.ide: o for o in [
    _o(100, 1), _o(101, 1), _o(102, 1, activa=False),   # de la 1
    _o(900, 28),                                        # de la 28
    _o(500, None, activa=False),                        # sin empresa
]}

TRABAJADORES = {t.ide: t for t in [
    _t(10, "Ana", 1),                    # 1, con una línea en obra de la 28
    _t(11, "Bea", 28),
    _t(12, "Carlos", None, False),       # NULL, carga solo en la 28
    _t(13, "Dani", None, False),         # NULL, carga solo en obra NULL
    _t(14, "Eva", 1),                    # 1, sin carga
    _t(15, "Fran", 18),                  # 18, sin carga
    _t(16, "Gil", None, False),          # NULL, carga en la 1 y en la 28
]}


def _ln(obra_ide: int, pct: str) -> Linea:
    o = OBRAS[obra_ide]
    return Linea(obra_ide=obra_ide, es_postventa=False,
                 porcentaje=Decimal(pct), cod=o.cod,
                 descripcion=o.descripcion, obra_activa=o.activa,
                 obra_empresa=o.empresa)


def _lineas_actuales() -> dict[int, list[Linea]]:
    return {
        10: [_ln(100, "60"), _ln(900, "40")],
        11: [_ln(900, "100")],
        12: [_ln(900, "50")],
        13: [_ln(500, "30")],
        16: [_ln(100, "50"), _ln(900, "50")],
    }


class _Trabajadores:
    def __init__(self, uow: _Uow) -> None:
        self._uow = uow

    def listar_para_periodo(self, periodo_id: int) -> list[Trabajador]:
        con_lineas = self._uow.lineas.get(periodo_id, {})
        return sorted((t for t in TRABAJADORES.values()
                       if t.activo or con_lineas.get(t.ide)),
                      key=lambda t: t.nombre)

    def obtener(self, ide: int) -> Trabajador | None:
        return TRABAJADORES.get(ide)

    def empresas_activas(self) -> set[int]:
        return {t.empresa for t in TRABAJADORES.values()
                if t.activo and t.empresa is not None}


class _Obras:
    def listar_para_periodo(self, periodo_id: int) -> list[Obra]:
        return sorted(OBRAS.values(), key=lambda o: o.cod)

    def existen(self, ides: set[int]) -> set[int]:
        return ides & set(OBRAS)


class _Periodos:
    def obtener(self, anio: int, mes: int) -> tuple[int, Periodo] | None:
        if (anio, mes) == (ANIO, MES):
            return P_ACT, Periodo(anio, mes)
        return None

    def anterior_con_datos(self, anio: int, mes: int) -> tuple[int, Periodo]:
        return P_ANT, Periodo(ANIO, MES - 1)


class _Asignaciones:
    def __init__(self, uow: _Uow) -> None:
        self._uow = uow

    def lineas_de_trabajador(self, periodo_id: int, ide: int) -> list[Linea]:
        return list(self._uow.lineas.get(periodo_id, {}).get(ide, []))

    def lineas_del_periodo(self, periodo_id: int) -> dict[int, list[Linea]]:
        return {k: list(v) for k, v in
                self._uow.lineas.get(periodo_id, {}).items() if v}

    def reemplazar(self, periodo_id: int, ide: int, lineas: list[Linea],
                   usuario: str) -> None:
        self._uow.lineas.setdefault(periodo_id, {})[ide] = [
            _ln(ln.obra_ide, str(ln.porcentaje)) for ln in lineas]
        self._uow.reemplazados.append(ide)


class _Eventos:
    def __init__(self) -> None:
        self.pendientes: dict[int, list[dict[str, Any]]] = {}

    def registrar(self, periodo_id, ide, tipo, usuario, antes, despues):
        self.pendientes[ide] = antes

    def ultimo_pendiente(self, periodo_id: int, ide: int):
        return (1, self.pendientes[ide]) if ide in self.pendientes else None

    def marcar_deshecho(self, evento_id: int) -> None:
        self.pendientes.clear()

    def trabajadores_con_pendientes(self, periodo_id: int) -> set[int]:
        return set(self.pendientes)


class _Uow:
    """UnitOfWork en memoria con los repositorios que usan los casos."""

    def __init__(self, lineas: dict[int, dict[int, list[Linea]]]) -> None:
        self.lineas = lineas
        self.reemplazados: list[int] = []
        self.trabajadores = _Trabajadores(self)
        self.obras = _Obras()
        self.periodos = _Periodos()
        self.asignaciones = _Asignaciones(self)
        self.eventos = _Eventos()

    def commit(self) -> None:
        return None


def _uow() -> _Uow:
    return _Uow({P_ACT: _lineas_actuales()})


def _f(empresa: int) -> FiltroEmpresa:
    return FiltroEmpresa(empresa=empresa, por_defecto=DEF)


def _nombres(filas) -> list[str]:
    return [f.trabajador.nombre for f in filas]


# ------------------------------ R7 / R8 ------------------------------- #
@pytest.mark.parametrize("empresa, nombres", [
    (1, ["Ana", "Dani", "Eva", "Gil"]),
    (28, ["Bea", "Carlos", "Gil"]),
    (18, ["Fran"]),
    (31, []),
])
def test_f024_r7_cuadrante_solo_trabajadores_visibles(empresa, nombres):
    cuadrante = ObtenerCuadrante().ejecutar(_uow(), ANIO, MES, _f(empresa))
    assert _nombres(cuadrante.filas) == nombres
    assert cuadrante.empresa == empresa


# --------------------------------- R9 --------------------------------- #
@pytest.mark.parametrize("empresa, obras", [
    (1, [100, 101, 102]), (28, [900]), (18, []),
])
def test_f024_r9_obras_solo_de_la_empresa_y_nunca_las_null(empresa, obras):
    cuadrante = ObtenerCuadrante().ejecutar(_uow(), ANIO, MES, _f(empresa))
    assert [o.ide for o in cuadrante.obras] == obras


# --------------------------------- R10 -------------------------------- #
def test_f024_r10_fila_con_todas_sus_lineas_y_total_sobre_todas():
    cuadrante = ObtenerCuadrante().ejecutar(_uow(), ANIO, MES, _f(1))
    ana = cuadrante.filas[0]
    assert [(ln.obra_ide, ln.obra_empresa) for ln in ana.lineas] == [
        (100, 1), (900, 28)]
    assert ana.total == Decimal("100")


def test_f024_r10_puede_deshacer_se_conserva():
    uow = _uow()
    uow.eventos.pendientes[10] = []
    cuadrante = ObtenerCuadrante().ejecutar(uow, ANIO, MES, _f(1))
    assert [f.puede_deshacer for f in cuadrante.filas] == [
        True, False, False, False]


# --------------------------------- R13 -------------------------------- #
RESUMEN_1 = ResumenPeriodo(total=4, ok=2, falta=1, exceso=0, sin_carga=1)
RESUMEN_28 = ResumenPeriodo(total=3, ok=2, falta=1, exceso=0, sin_carga=0)


@pytest.mark.parametrize("empresa, resumen", [(1, RESUMEN_1),
                                              (28, RESUMEN_28)])
def test_f024_r13_resumen_del_cuadrante_solo_visibles(empresa, resumen):
    cuadrante = ObtenerCuadrante().ejecutar(_uow(), ANIO, MES, _f(empresa))
    assert cuadrante.resumen == resumen


@pytest.mark.parametrize("empresa, resumen", [(1, RESUMEN_1),
                                              (28, RESUMEN_28)])
def test_f024_r13_resumen_de_las_respuestas_por_fila(empresa, resumen):
    """Fila, guardar, deshacer y copiar trabajador devuelven el resumen de
    la empresa elegida; la fila lleva todas sus líneas (R10)."""
    fila, res = ObtenerFilaTrabajador().ejecutar(
        _uow(), ANIO, MES, 16, filtro=_f(empresa))
    assert res == resumen and len(fila.lineas) == 2

    uow = _uow()
    fila, res = GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14, [{"obra_ide": 101, "porcentaje": "100"}],
        "u", filtro=_f(empresa))
    assert fila.total == Decimal("100")
    # Eva (14) pasa de SIN_CARGA a OK en la 1; en la 28 no cuenta.
    esperado = (ResumenPeriodo(total=4, ok=3, falta=1, sin_carga=0)
                if empresa == 1 else resumen)
    assert res == esperado

    fila, res = DeshacerUltimaModificacion().ejecutar(
        uow, ANIO, MES, 14, "u", filtro=_f(empresa))
    assert fila.lineas == [] and res == resumen

    uow = _uow()
    uow.lineas[P_ANT] = {14: [_ln(101, "100")]}
    fila, res, origen, omitidas = CopiarTrabajadorAnterior().ejecutar(
        uow, ANIO, MES, 14, "u", filtro=_f(empresa))
    assert res == esperado and omitidas == 0


# --------------------------------- R14 -------------------------------- #
@pytest.mark.parametrize("empresa, copiados, sin_datos", [
    (1, [10, 14], 0),       # Ana y Eva (activas de la 1)
    (28, [11], 0),          # Bea
    (18, [], 1),            # Fran: activo de la 18 sin datos de origen
])
def test_f024_r14_copiar_mes_solo_activos_visibles(empresa, copiados,
                                                   sin_datos):
    uow = _Uow({P_ACT: {}, P_ANT: {10: [_ln(100, "100")],
                                   11: [_ln(900, "100")],
                                   14: [_ln(101, "100")],
                                   12: [_ln(900, "100")]}})
    resultado = CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, "u",
                                                 filtro=_f(empresa))
    assert uow.reemplazados == copiados
    assert resultado.trabajadores_copiados == len(copiados)
    assert resultado.sin_datos_origen == sin_datos
    assert resultado.con_carga_previa == 0


def test_f024_r14_copiar_mes_cuenta_con_carga_solo_de_la_empresa():
    """Con carga previa en el destino: solo cuentan los visibles en E."""
    uow = _Uow({P_ACT: {10: [_ln(100, "100")], 11: [_ln(900, "100")]},
                P_ANT: {14: [_ln(101, "100")]}})
    resultado = CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, "u",
                                                 filtro=_f(1))
    assert resultado.con_carga_previa == 1          # Ana; Bea es de la 28
    assert uow.reemplazados == [14]
