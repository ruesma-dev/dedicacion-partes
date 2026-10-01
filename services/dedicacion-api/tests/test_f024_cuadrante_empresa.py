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
