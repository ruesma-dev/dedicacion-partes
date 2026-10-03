# tests/test_f025_sync_postventa.py
"""Tests offline de F-025 en la api: el universo de postventa se pide en el
sync y se guarda en la obra (R12-R16, R18, R21).

Trazabilidad con `specs/F-025-obras-postventa-postv2/requirements.md`. El
universo lo calcula SOLO el transfer (D1): aquí se sustituye por el doble
`UniversoFalso` de `tests/conftest.py`. Nada abre un socket ni una conexión.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest
from domain.models import Linea, Obra
from infrastructure.db.orm_models import Base, ObraORM
from sqlalchemy.dialects import postgresql

DIALECTO = postgresql.dialect()


# --- R18 · `ofrecible`, una sola definición en el dominio ---------------------


def _linea(es_postventa: bool, activa: bool, admite: bool) -> Linea:
    return Linea(obra_ide=1, es_postventa=es_postventa,
                 porcentaje=Decimal("50"), obra_activa=activa,
                 obra_admite_postventa=admite)


@pytest.mark.parametrize(("es_postventa", "activa", "admite", "ofrecible"), [
    (False, True, False, True),     # normal en obra activa
    (False, False, True, False),    # normal en obra solo de postventa
    (True, False, True, True),      # postventa en obra que la admite
    (True, True, False, False),     # postventa en obra que no la admite
])
def test_f025_r18_ofrecible_segun_el_modo_de_la_linea(
    es_postventa: bool, activa: bool, admite: bool, ofrecible: bool
) -> None:
    """R18 · La normal es ofrecible si la obra está `activa`; la de
    postventa, si la obra `admite_postventa`. Nada más."""
    assert _linea(es_postventa, activa, admite).ofrecible is ofrecible


def test_f025_r18_por_defecto_una_linea_no_admite_postventa() -> None:
    """R18 · Sin marca, una línea de postventa no es ofrecible."""
    linea = Linea(obra_ide=1, es_postventa=True, porcentaje=Decimal("1"))
    assert linea.obra_admite_postventa is False
    assert linea.ofrecible is False


def test_f025_r18_la_obra_por_defecto_no_admite_postventa() -> None:
    """R18 · `Obra.admite_postventa` existe y por defecto es `False`."""
    obra = Obra(ide=1, cod="0001", descripcion="X", estado_sigrid=None)
    assert obra.admite_postventa is False and obra.activa is True


def test_f025_r18_resultado_universo_es_inmutable() -> None:
    """R18 · `ResultadoUniverso` (lo que devuelve el puerto) es inmutable."""
    from domain.models import ResultadoUniverso

    r = ResultadoUniverso(ides=frozenset({1, 2}), motivo=None)
    assert r.ides == frozenset({1, 2}) and r.motivo is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.motivo = "x"  # type: ignore[misc]


# --- R21 · la columna, solo en el ORM y con su ALTER derivado ------------------


def test_f025_r21_columna_booleana_no_nula_false_por_defecto() -> None:
    """R21 · `obra.admite_postventa`: booleano, no nulo, `false` en servidor
    (así el ALTER sobre una tabla con filas no necesita migración)."""
    columna = ObraORM.__table__.columns["admite_postventa"]
    assert columna.type.compile(dialect=DIALECTO) == "BOOLEAN"
    assert columna.nullable is False
    assert columna.default is not None and columna.default.arg is False
    assert str(columna.server_default.arg.compile(dialect=DIALECTO)) == "false"


def test_f025_r21_el_alter_lo_deriva_esquema() -> None:
    """R21 · Sobre una base sin la columna, `alters_faltantes` deriva el
    `ADD COLUMN` (sin PostgreSQL); con ella, nada."""
    from infrastructure.db.esquema import alters_faltantes

    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()}
    assert alters_faltantes(Base.metadata, existentes) == []
    existentes["obra"].discard("admite_postventa")
    assert alters_faltantes(Base.metadata, existentes) == [
        "ALTER TABLE obra ADD COLUMN IF NOT EXISTS admite_postventa BOOLEAN "
        "DEFAULT false NOT NULL"]


def test_f025_r21_solo_la_tabla_obra_la_tiene() -> None:
    """R21 · La marca es de la obra, no de la asignación ni de otra tabla."""
    con_marca = {t.name for t in Base.metadata.tables.values()
                 if "admite_postventa" in t.columns}
    assert con_marca == {"obra"}
