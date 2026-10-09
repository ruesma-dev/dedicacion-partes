# tests/test_f050_partida_linea.py
"""F-050 · La partida ELEGIDA de cada línea del cuadrante en la api
(R12, R14, R15, R16).

- R12: columnas nulables de `AsignacionORM`, campos de `Linea`, el mapeo
  del repositorio y lo que escribe `reemplazar` (sesión falsa).
- R14-R16: casos de uso con la UnitOfWork en memoria de F-024, ampliada
  AQUÍ para que `reemplazar` guarde la partida y el modo de cada línea.

Sin red ni BBDD; `ide` inventados.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal
from types import SimpleNamespace

import pytest
from application.use_cases import (
    CompletarHasta100,
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    _conservar_partidas,
    _snapshot,
    _validar_lineas,
)
from domain.models import FiltroEmpresa, Linea
from infrastructure.db.orm_models import AsignacionORM
from infrastructure.db.repositories import (
    PgAsignacionRepository,
    _a_linea_con_partida,
)
from sqlalchemy.dialects import postgresql

from tests.test_f024_cuadrante_empresa import (
    ANIO,
    DEF,
    MES,
    P_ACT,
    P_ANT,
    _Asignaciones,
    _ln,
    _Uow,
)

FILTRO = FiltroEmpresa(empresa=DEF, por_defecto=DEF, empresa_obras=DEF)
P = {"partida_ide": 80003, "partida_cod": "CI.1.9",
     "partida_res": "ADMINISTRATIVO"}


def _lp(obra_ide: int, pct: str, pv: bool = False, **partida) -> Linea:
    return dataclasses.replace(_ln(obra_ide, pct), es_postventa=pv,
                               **partida)


class _AsignacionesConPartida(_Asignaciones):
    """`reemplazar` de F-024 que además conserva modo y partida."""

    def reemplazar(self, periodo_id, ide, lineas, usuario):
        self._uow.lineas.setdefault(periodo_id, {})[ide] = [
            _lp(ln.obra_ide, str(ln.porcentaje), ln.es_postventa,
                partida_ide=ln.partida_ide, partida_cod=ln.partida_cod,
                partida_res=ln.partida_res) for ln in lineas]
        self._uow.reemplazados.append(ide)


def _uow(actual=None, anterior=None) -> _Uow:
    uow = _Uow({P_ACT: actual or {}, P_ANT: anterior or {}})
    uow.asignaciones = _AsignacionesConPartida(uow)
    return uow


def _partidas(lineas) -> list[tuple]:
    return [(ln.obra_ide, ln.porcentaje, ln.partida_ide, ln.partida_cod,
             ln.partida_res) for ln in lineas]


# ================================ R12 ==================================== #
@pytest.mark.parametrize("nombre, tipo", [
    ("partida_ide", "BIGINT"), ("partida_cod", "TEXT"),
    ("partida_res", "TEXT")])
def test_f050_r12_columnas_nulables_sin_default(nombre, tipo):
    col = AsignacionORM.__table__.columns[nombre]
    assert col.type.compile(dialect=postgresql.dialect()) == tipo
    assert col.nullable is True
    assert col.default is None and col.server_default is None


def test_f050_r12_linea_automatica_por_defecto_y_clave_igual():
    ln = Linea(obra_ide=1, es_postventa=False, porcentaje=Decimal(10))
    assert (ln.partida_ide, ln.partida_cod, ln.partida_res,
            ln.partida_fija) == (None, None, None, False)
    assert dataclasses.replace(ln, **P).clave() == (1, False)


def _orm_obra(registro_paride=None):
    return SimpleNamespace(cod="0694", descripcion="OBRA", activa=True,
                           empresa=1, admite_postventa=False,
                           registro_paride=registro_paride)


def test_f050_r12_r18_el_repositorio_mapea_la_partida():
    a = SimpleNamespace(obra_ide=7, es_postventa=False,
                        porcentaje=Decimal("40.00"), **P)
    ln = _a_linea_con_partida(a, _orm_obra())
    assert (ln.partida_ide, ln.partida_cod, ln.partida_res,
            ln.partida_fija) == (80003, "CI.1.9", "ADMINISTRATIVO", False)
    assert ln.obra_empresa == 1 and ln.cod == "0694"
    sin = SimpleNamespace(obra_ide=7, es_postventa=False,
                          porcentaje=Decimal("40.00"), partida_ide=None,
                          partida_cod=None, partida_res=None)
    var = _a_linea_con_partida(sin, _orm_obra(registro_paride=91029))
    assert (var.partida_ide, var.partida_fija) == (None, True)
    assert _a_linea_con_partida(sin, _orm_obra(registro_paride=0)) \
        .partida_fija is True


class _SesionReemplazo:
    def __init__(self) -> None:
        self.anadidos: list = []
        self.ejecutadas: list = []

    def execute(self, stmt):
        self.ejecutadas.append(stmt)

    def add(self, objeto):
        self.anadidos.append(objeto)

    def flush(self):
        return None


def test_f050_r12_reemplazar_escribe_la_partida():
    s = _SesionReemplazo()
    PgAsignacionRepository(s).reemplazar(  # type: ignore[arg-type]
        3, 10, [_lp(100, "60", **P), _lp(101, "40")], "pgris")
    assert [(o.obra_ide, o.partida_ide, o.partida_cod, o.partida_res)
            for o in s.anadidos] == [(100, 80003, "CI.1.9", "ADMINISTRATIVO"),
                                     (101, None, None, None)]


# ================================ R15 ==================================== #
def test_f050_r15_snapshot_lleva_la_partida_solo_si_la_hay():
    assert _snapshot([_lp(101, "40"), _lp(100, "60", **P)]) == [
        {"obra_ide": 100, "es_postventa": False, "porcentaje": "60",
         **P},
        {"obra_ide": 101, "es_postventa": False, "porcentaje": "40"}]


def test_f050_r15_validar_lineas_lee_la_partida_si_viene():
    uow = _uow()
    lineas = _validar_lineas(uow, [
        {"obra_ide": 100, "porcentaje": "60", **P},
        {"obra_ide": 101, "porcentaje": "40"}])
    assert _partidas(lineas) == [
        (100, Decimal("60.00"), 80003, "CI.1.9", "ADMINISTRATIVO"),
        (101, Decimal("40.00"), None, None, None)]


def test_f050_r15_deshacer_devuelve_la_partida():
    """F8 sustituye la línea con partida por la del mes anterior (sin ella);
    deshacer la devuelve con su partida."""
    uow = _uow(actual={14: [_lp(100, "100", **P)]},
               anterior={14: [_lp(101, "100")]})
    CopiarTrabajadorAnterior().ejecutar(uow, ANIO, MES, 14, "u",
                                        filtro=FILTRO)
    assert _partidas(uow.lineas[P_ACT][14]) == [
        (101, Decimal(100), None, None, None)]
    DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 14, "u",
                                          filtro=FILTRO)
    assert _partidas(uow.lineas[P_ACT][14]) == [
        (100, Decimal("100.00"), 80003, "CI.1.9", "ADMINISTRATIVO")]


# ================================ R14 ==================================== #
def test_f050_r14_conservar_partidas_por_clave():
    antes = [_lp(100, "60", **P), _lp(100, "40", pv=True, partida_ide=7,
                                      partida_cod="0678", partida_res="X")]
    nuevas = [_lp(100, "50"), _lp(100, "30", pv=True), _lp(101, "20")]
    assert _partidas(_conservar_partidas(nuevas, antes)) == [
        (100, Decimal(50), 80003, "CI.1.9", "ADMINISTRATIVO"),
        (100, Decimal(30), 7, "0678", "X"),
        (101, Decimal(20), None, None, None)]


def test_f050_r14_guardar_conserva_la_partida_de_la_linea_que_existia():
    uow = _uow(actual={14: [_lp(100, "60", **P)]})
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14,
        [{"obra_ide": 100, "porcentaje": "70"},
         {"obra_ide": 101, "porcentaje": "30"}], "u", filtro=FILTRO)
    assert _partidas(uow.lineas[P_ACT][14]) == [
        (100, Decimal("70.00"), 80003, "CI.1.9", "ADMINISTRATIVO"),
        (101, Decimal("30.00"), None, None, None)]
    [(_, evento)] = uow.eventos.eventos
    assert evento.snapshot_antes == [
        {"obra_ide": 100, "es_postventa": False, "porcentaje": "60", **P}]


def test_f050_r14_guardar_lo_mismo_no_deja_evento():
    """La partida conservada no cuenta como cambio (F7 sobre sí mismo)."""
    uow = _uow(actual={14: [_lp(100, "60.00", **P)]})
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14, [{"obra_ide": 100, "porcentaje": "60"}], "u",
        filtro=FILTRO)
    assert uow.eventos.eventos == [] and uow.reemplazados == []


def test_f050_r14_la_obra_nueva_entra_automatica():
    """Quitar la obra con partida y poner otra: la otra no la hereda."""
    uow = _uow(actual={14: [_lp(100, "100", **P)]})
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14, [{"obra_ide": 101, "porcentaje": "100"}], "u",
        filtro=FILTRO)
    assert _partidas(uow.lineas[P_ACT][14]) == [
        (101, Decimal("100.00"), None, None, None)]


# ================================ R16 ==================================== #
def test_f050_r16_copiar_trabajador_copia_la_partida():
    uow = _uow(anterior={14: [_lp(100, "100", **P)]})
    CopiarTrabajadorAnterior().ejecutar(uow, ANIO, MES, 14, "u",
                                        filtro=FILTRO)
    assert _partidas(uow.lineas[P_ACT][14]) == [
        (100, Decimal(100), 80003, "CI.1.9", "ADMINISTRATIVO")]


def test_f050_r16_copiar_periodo_copia_la_partida():
    uow = _uow(anterior={14: [_lp(100, "100", **P)]})
    CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, "u", filtro=FILTRO)
    assert _partidas(uow.lineas[P_ACT][14]) == [
        (100, Decimal(100), 80003, "CI.1.9", "ADMINISTRATIVO")]


@pytest.mark.parametrize("destino, esperado", [
    (100, [(100, Decimal("100.00"), 80003, "CI.1.9", "ADMINISTRATIVO")]),
    (101, [(100, Decimal(60), 80003, "CI.1.9", "ADMINISTRATIVO"),
           (101, Decimal("40.00"), None, None, None)]),
])
def test_f050_r16_completar_conserva_y_la_nueva_automatica(destino,
                                                          esperado):
    uow = _uow(actual={14: [_lp(100, "60", **P)]})
    CompletarHasta100().ejecutar(uow, ANIO, MES, [14], destino, False, "u",
                                 filtro=FILTRO)
    assert _partidas(uow.lineas[P_ACT][14]) == esperado
