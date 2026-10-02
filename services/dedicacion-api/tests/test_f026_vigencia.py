# tests/test_f026_vigencia.py
"""Tests offline de F-026: identidad por recurso y vigencia por mes.

Trazabilidad con `specs/F-026-recursos-sin-ficha-empleado/requirements.md`:
R7-R9 (clave = `res.ide`, `fecha_baja` en el ORM, desactivar lo que no
llega), R12 (ventana de bajas), R14 (vigente en el mes) y R15 (cuadrante,
resumen y copia por mes).

Nada abre un socket ni una conexión: el repositorio trabaja contra sesiones
dobles (patrón de F-023/F-024) y el DDL se compila con el dialecto
PostgreSQL sin motor. Los módulos de F-026 se importan dentro de los tests
para que cada tarea de `tasks.md` se verifique con su `-k`.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pytest


def _vigencia() -> Any:
    from domain import vigencia

    return vigencia


# --- R14: vigente en el mes -------------------------------------------------


def test_f026_r14_inicio_de_mes_es_aaaamm01() -> None:
    v = _vigencia()
    assert v.inicio_de_mes(2026, 10) == 20261001
    assert v.inicio_de_mes(2027, 1) == 20270101
    assert v.inicio_de_mes(2026, 12) == 20261201


@pytest.mark.parametrize(("activo", "fecha_baja", "esperado"), [
    (True, None, True),          # sin baja
    (True, 0, True),             # 0 de Sigrid = sin baja
    (True, 20261001, True),      # baja el día 1 del mes: sigue ese mes (D3)
    (True, 20261031, True),      # baja el último día del mes
    (True, 20261115, True),      # baja posterior
    (True, 20260930, False),     # baja el último día del mes anterior
    (True, 20260901, False),     # baja del mes anterior
    (False, None, False),        # inactivo: no vigente, sin mirar la baja
    (False, 20261015, False),
])
def test_f026_r14_vigente_en_octubre(activo: bool, fecha_baja: int | None,
                                     esperado: bool) -> None:
    assert _vigencia().vigente_en(activo, fecha_baja, 2026, 10) is esperado


# --- R12: ventana de bajas --------------------------------------------------


def test_f026_r12_ventana_sin_abiertos_es_el_mes_anterior_a_hoy() -> None:
    assert _vigencia().inicio_ventana_baja([], date(2026, 10, 2)) == 20260901


def test_f026_r12_ventana_en_enero_es_diciembre_del_anio_anterior() -> None:
    assert _vigencia().inicio_ventana_baja([], date(2027, 1, 31)) == 20261201


def test_f026_r12_el_periodo_abierto_mas_antiguo_gana() -> None:
    abiertos = [(2026, 10), (2026, 6), (2026, 8)]
    assert _vigencia().inicio_ventana_baja(
        abiertos, date(2026, 10, 2)) == 20260601


def test_f026_r12_un_abierto_posterior_no_mueve_la_ventana() -> None:
    abiertos = [(2026, 10), (2026, 11)]
    assert _vigencia().inicio_ventana_baja(
        abiertos, date(2026, 10, 2)) == 20260901


def test_f026_r12_acepta_cualquier_iterable() -> None:
    abiertos = iter([(2025, 12)])
    assert _vigencia().inicio_ventana_baja(
        abiertos, date(2026, 10, 2)) == 20251201


# --- R7-R9, R13: el repositorio guarda la fecha de baja ----------------------


class _Resultado:
    def __init__(self, filas: list[Any]) -> None:
        self._filas = filas

    def all(self) -> list[Any]:
        return list(self._filas)


class _SesionRepo:
    """Sesión doble: `scalars()` devuelve las filas previas, `add` las apunta
    y cualquier `execute` (un DELETE o UPDATE masivo) queda registrado."""

    def __init__(self, previas: list[Any] | None = None) -> None:
        self.previas = list(previas or [])
        self.anadidas: list[Any] = []
        self.ejecutadas: list[Any] = []

    def scalars(self, _sentencia: Any) -> _Resultado:
        return _Resultado(self.previas)

    def add(self, orm: Any) -> None:
        self.anadidas.append(orm)

    def execute(self, sentencia: Any, *_args: Any, **_kwargs: Any) -> Any:
        self.ejecutadas.append(sentencia)
        return _Resultado([])

    def get(self, _modelo: Any, ide: int) -> Any:
        return next((o for o in self.previas if o.ide == ide), None)


def _fila(ide: int, **cambios: Any) -> dict[str, Any]:
    """Fila depurada que llega al upsert (sin auxiliares, F-026 §5.1)."""
    fila: dict[str, Any] = {"ide": ide, "cod": f"MO/{ide:04d}",
                            "nombre": f"Persona {ide}", "dni": None,
                            "empresa": 1, "categoria": "Encargado",
                            "fecha_baja": None, "cod_hora_mes": "MENC",
                            "importe_mes": 100}
    fila.update(cambios)
    return fila


def _orm(ide: int, fecha_baja: int | None = None, activo: bool = True) -> Any:
    from infrastructure.db.orm_models import TrabajadorORM

    fila = _fila(ide)
    return TrabajadorORM(ide=ide, cod=fila["cod"], nombre=fila["nombre"],
                         dni=None, categoria=fila["categoria"], activo=activo,
                         empresa=1, fecha_baja=fecha_baja)


def _repo(sesion: _SesionRepo) -> Any:
    from infrastructure.db.repositories import PgTrabajadorRepository

    return PgTrabajadorRepository(sesion)


def test_f026_r8_fecha_baja_integer_nulable_sin_default() -> None:
    from infrastructure.db.orm_models import TrabajadorORM
    from sqlalchemy.dialects import postgresql

    columna = TrabajadorORM.__table__.columns["fecha_baja"]
    assert columna.type.compile(dialect=postgresql.dialect()) == "INTEGER"
    assert columna.nullable is True
    assert columna.default is None
    assert columna.server_default is None


def test_f026_r8_alters_de_una_base_sin_la_columna_solo_la_anaden() -> None:
    from infrastructure.db.esquema import alters_faltantes
    from infrastructure.db.orm_models import Base

    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()}
    existentes["trabajador"].discard("fecha_baja")
    assert alters_faltantes(Base.metadata, existentes) == [
        "ALTER TABLE trabajador ADD COLUMN IF NOT EXISTS fecha_baja INTEGER"]


def test_f026_r8_fecha_baja_solo_en_trabajador() -> None:
    from infrastructure.db.orm_models import Base

    assert {t.name for t in Base.metadata.tables.values()
            if "fecha_baja" in t.columns} == {"trabajador"}


def test_f026_r7_alta_con_el_ide_del_recurso_y_su_baja() -> None:
    sesion = _SesionRepo()
    res = _repo(sesion).sincronizar([_fila(772), _fila(9, fecha_baja=20261015)])
    assert res.altas == 2
    assert sorted((t.ide, t.cod, t.fecha_baja, t.activo)
                  for t in sesion.anadidas) == [
        (9, "MO/0009", 20261015, True), (772, "MO/0772", None, True)]


def test_f026_r13_baja_cero_se_guarda_nula() -> None:
    sesion = _SesionRepo()
    _repo(sesion).sincronizar([_fila(1, fecha_baja=0)])
    assert sesion.anadidas[0].fecha_baja is None


@pytest.mark.parametrize(("previa", "nueva", "guardada", "actualizados"), [
    (20261015, None, None, 1),       # Sigrid le quita la baja: NULL
    (20261015, 0, None, 1),          # 0 de Sigrid = sin baja
    (None, 20261015, 20261015, 1),   # baja nueva: cuenta como actualizado
    (20261015, 20261020, 20261020, 1),
    (20261015, 20261015, 20261015, 0),
    (None, None, None, 0),
    (None, 0, None, 0),
])
def test_f026_r13_cambio_de_fecha_de_baja(previa: int | None, nueva: int | None,
                                          guardada: int | None,
                                          actualizados: int) -> None:
    existente = _orm(1, fecha_baja=previa)
    res = _repo(_SesionRepo([existente])).sincronizar([_fila(1, fecha_baja=nueva)])
    assert (res.altas, res.actualizados) == (0, actualizados)
    assert existente.fecha_baja == guardada


def test_f026_r9_fila_que_no_llega_se_desactiva_sin_tocar_lineas() -> None:
    """Una clave `emp.ide` anterior a F-026 deja de llegar: se desactiva como
    cualquier recurso y no se lanza nada sobre `asignacion` ni `evento`."""
    vieja, sigue = _orm(10), _orm(772)
    sesion = _SesionRepo([vieja, sigue])
    res = _repo(sesion).sincronizar([_fila(772)])
    assert (res.recibidos, res.altas, res.desactivados) == (1, 0, 1)
    assert vieja.activo is False and sigue.activo is True
    assert sesion.ejecutadas == []
    assert sesion.anadidas == []


def test_f026_r8_el_dominio_expone_la_fecha_de_baja() -> None:
    from domain.models import Trabajador

    assert Trabajador(ide=1, cod=None, nombre="X", dni=None,
                      categoria=None).fecha_baja is None
    trabajador = _repo(_SesionRepo([_orm(7, fecha_baja=20261015)])).obtener(7)
    assert trabajador is not None and trabajador.fecha_baja == 20261015
