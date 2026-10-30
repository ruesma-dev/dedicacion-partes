# tests/test_f054_aceptar.py
"""F-054 · T6 y T7: aceptar entradas traídas de Sigrid (R19-R25; design
§5.2 y §5.3).

T6 (`-k repositorio`): `PgAsignacionRepository.aceptar_entrada` es UNA
sentencia `INSERT … ON CONFLICT (uq_asignacion_linea) DO UPDATE` de la
línea de esa clave: si existe, se actualiza EN SU SITIO (mismo `id`; sus
filas de `asignacion_vinculado`, que cuelgan de él con `ON DELETE CASCADE`,
no se tocan); si no, se crea. Ninguna otra fila del trabajador: ni `DELETE`
ni `UPDATE` fuera de esa clave. Lleva la traza de R23 (`sigrid_hmores_ide`,
`sigrid_parte_cod`, `sigrid_estado = registrado`, el motivo «traída de
Sigrid», sin fecha ni autor de registro) y la propuesta a nulo. Compila con
las columnas del ORM, sin base.

Sin red ni BBDD.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from domain.models import Linea
from infrastructure.db.orm_models import AsignacionORM
from infrastructure.db.repositories import (
    MOTIVO_TRAIDA_DE_SIGRID,
    PgAsignacionRepository,
)
from sqlalchemy.dialects import postgresql


class _Sesion:
    """Sesión falsa: anota cada sentencia ejecutada."""

    def __init__(self) -> None:
        self.sentencias: list[Any] = []

    def execute(self, stmt: Any) -> Any:
        self.sentencias.append(stmt)
        return None


def _aceptar(linea: Linea, **kw):
    s = _Sesion()
    PgAsignacionRepository(s).aceptar_entrada(
        7, 4321, linea, hmores_ide=kw.get("hmores_ide", 9001),
        parte_cod=kw.get("parte_cod", "PT26/00319"),
        usuario=kw.get("usuario", "ana@ruesma.es"))
    return s.sentencias


def _compilada(stmt):
    return stmt.compile(dialect=postgresql.dialect())


LINEA = Linea(obra_ide=694, es_postventa=False, porcentaje=Decimal("95.00"),
              partida_ide=2105, partida_cod="CI.1.5", partida_res="JEFE")


def test_f054_r19_repositorio_una_sentencia_upsert_de_esa_clave():
    [stmt] = _aceptar(LINEA)
    sql = " ".join(str(_compilada(stmt)).split())
    assert sql.startswith("INSERT INTO asignacion (")
    assert "ON CONFLICT ON CONSTRAINT uq_asignacion_linea DO UPDATE SET" in sql
    assert "DELETE" not in sql
    p = _compilada(stmt).params
    assert (p["periodo_id"], p["trabajador_ide"], p["obra_ide"],
            p["es_postventa"]) == (7, 4321, 694, False)


def test_f054_r19_repositorio_el_update_conserva_id_y_clave():
    """El `SET` del conflicto no toca `id` ni la clave: la fila sigue
    siendo la misma (y sus subfilas, que cuelgan de su `id`)."""
    [stmt] = _aceptar(LINEA)
    sql = " ".join(str(_compilada(stmt)).split())
    puesto = sql.split("DO UPDATE SET", 1)[1]
    columnas = {t.split(" = ")[0].strip() for t in puesto.split(", ")}
    assert columnas == {
        "porcentaje", "partida_ide", "partida_cod", "partida_res",
        "propuesta_ide", "propuesta_cod", "propuesta_res",
        "propuesta_metodo", "propuesta_origen", "actualizado_en",
        "actualizado_por", "sigrid_estado", "sigrid_parte_cod",
        "sigrid_hmores_ide", "sigrid_motivo", "sigrid_registrado_at_utc",
        "sigrid_registrado_by"}
    assert not {"id", "periodo_id", "trabajador_ide", "obra_ide",
                "es_postventa"} & columnas
    orm = {c.name for c in AsignacionORM.__table__.columns}
    assert columnas <= orm


def test_f054_r23_repositorio_traza_y_valores():
    [stmt] = _aceptar(LINEA, hmores_ide=9001, parte_cod="PT26/00319",
                      usuario="ana@ruesma.es")
    p = _compilada(stmt).params
    assert p["porcentaje"] == Decimal("95.00")
    assert (p["partida_ide"], p["partida_cod"], p["partida_res"]) == (
        2105, "CI.1.5", "JEFE")
    assert (p["sigrid_estado"], p["sigrid_hmores_ide"],
            p["sigrid_parte_cod"], p["sigrid_motivo"]) == (
        "registrado", 9001, "PT26/00319", MOTIVO_TRAIDA_DE_SIGRID)
    assert MOTIVO_TRAIDA_DE_SIGRID == "traída de Sigrid"
    assert p["sigrid_registrado_at_utc"] is None
    assert p["sigrid_registrado_by"] is None
    assert p["actualizado_por"] == "ana@ruesma.es"
    assert all(p[c] is None for c in (
        "propuesta_ide", "propuesta_cod", "propuesta_res",
        "propuesta_metodo", "propuesta_origen"))


def test_f054_r17_repositorio_postventa_automatica_y_cortes():
    linea = Linea(obra_ide=678, es_postventa=True, porcentaje=Decimal("10"))
    [stmt] = _aceptar(linea, parte_cod="P" * 40, usuario="u" * 90)
    p = _compilada(stmt).params
    assert p["es_postventa"] is True and p["partida_ide"] is None
    assert p["sigrid_parte_cod"] == "P" * 24
    assert p["actualizado_por"] == "u" * 90
