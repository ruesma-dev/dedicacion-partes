# tests/test_f039_sync_var.py
"""Tests offline de F-039 en la api: filtro de código de obra, universo VAR y
entradas `VAR-NN` en el sync y el preview (R10-R18).

Trazabilidad con `specs/F-039-obras-var-y-seis-digitos/requirements.md`. La
regla es `docs/ARCHITECTURE.md#regla-var` y `#regla-seis-digitos`. El
universo VAR lo calcula SOLO el transfer: aquí se sustituye por el doble
`UniversoFalso` de `tests/conftest.py`. Nada abre un socket ni una conexión.
"""
from __future__ import annotations

import dataclasses

import pytest
from infrastructure.db.orm_models import Base, ObraORM
from sqlalchemy.dialects import postgresql

DIALECTO = postgresql.dialect()


# --- R10 · reglas puras del código de obra (domain/obras.py) ------------------


@pytest.mark.parametrize(("cod", "cae"), [
    ("150414", True), ("0902051", True), ("090205A", True),
    ("150301-1", True), ("160304-LOCAL", True), ("160310 ", True),
    ("A123456", True), ("12345", False), ("VAR", False), ("0678", False),
    ("12345-12345", False), ("", False), (None, False),
])
def test_f039_r10_tiene_digitos_seguidos(cod: str | None, cae: bool) -> None:
    """R10 · Cae la obra cuyo código CONTIENE 6 o más dígitos seguidos,
    lleve o no letras o sufijo; con menos, o partidos, no."""
    from domain.obras import tiene_digitos_seguidos

    assert tiene_digitos_seguidos(cod, 6) is cae


@pytest.mark.parametrize("n", [0, -1])
def test_f039_r10_sin_filtro_con_n_cero_o_negativo(n: int) -> None:
    """R10 · `N <= 0` = sin filtro: ningún código cae."""
    from domain.obras import tiene_digitos_seguidos

    assert tiene_digitos_seguidos("150414", n) is False


def test_f039_r10_el_umbral_es_el_que_se_pasa() -> None:
    """R10 · Con N = 5, `12345` cae; con N = 7, `150414` no."""
    from domain.obras import tiene_digitos_seguidos

    assert tiene_digitos_seguidos("12345", 5) is True
    assert tiene_digitos_seguidos("1234", 5) is False
    assert tiene_digitos_seguidos("150414", 7) is False


# --- R13 · la entrada VAR: código e ide (D2, D6) -----------------------------


@pytest.mark.parametrize(("obra", "partida", "codigo"), [
    ("VAR", "29", "VAR-29"), ("VAR", "29.1", "VAR-29.1"),
    (" VAR ", " 100 ", "VAR-100"),
])
def test_f039_r13_codigo_de_la_entrada(obra: str, partida: str,
                                       codigo: str) -> None:
    """R13 · `<código de la obra VAR>-<código de la partida>`, sin
    espacios de relleno (D2)."""
    from domain.obras import codigo_entrada

    assert codigo_entrada(obra, partida) == codigo


def test_f039_r13_ide_de_la_entrada_es_el_de_la_partida_en_negativo() -> None:
    """R13 · `ide` = −(ide de la partida): no choca con ninguna obra (D6)."""
    from domain.obras import ide_entrada

    assert ide_entrada(417055) == -417055
    assert ide_entrada("417055") == -417055  # type: ignore[arg-type]


def test_f039_r13_el_resultado_del_universo_var_es_inmutable() -> None:
    """R13 · `PartidaVar` y `ResultadoUniversoVar`, inmutables."""
    from domain.models import PartidaVar, ResultadoUniversoVar

    p = PartidaVar(ide=417055, cod="29", res="NAVE")
    r = ResultadoUniversoVar(obra_ide=683806, obra_cod="VAR", empresa=1,
                             partidas=(p,), motivo=None)
    assert r.partidas[0].cod == "29" and r.motivo is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.motivo = "x"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.cod = "30"  # type: ignore[misc]


# --- R16 · el error y su 502 -------------------------------------------------


def test_f039_r16_el_error_es_de_dominio_y_se_traduce_a_502() -> None:
    """R16 · `UniversoVarNoDisponible` es un error de dominio y la tabla de
    la app lo traduce a 502."""
    from domain.errors import ErrorDominio, UniversoVarNoDisponible
    from interface_adapters.api.app import _HTTP_POR_ERROR

    assert issubclass(UniversoVarNoDisponible, ErrorDominio)
    assert (UniversoVarNoDisponible, 502) in _HTTP_POR_ERROR


def test_f039_r16_el_puerto_de_los_dos_universos() -> None:
    """R16 · `UniversosGateway` reúne los dos puertos; el transfer es UNO."""
    from domain.ports import (
        UniversoPostventaGateway,
        UniversosGateway,
        UniversoVarGateway,
    )

    assert UniversoPostventaGateway in UniversosGateway.__mro__
    assert UniversoVarGateway in UniversosGateway.__mro__
    assert hasattr(UniversoVarGateway, "universo_var")


# --- R18 · las tres columnas, solo en el ORM y con su ALTER derivado ---------

COLUMNAS_R18 = {"registro_obra_ide": "BIGINT", "registro_obra_cod": "TEXT",
                "registro_paride": "BIGINT"}


@pytest.mark.parametrize(("columna", "tipo"), sorted(COLUMNAS_R18.items()))
def test_f039_r18_columnas_nulables_sin_default(columna: str,
                                                tipo: str) -> None:
    """R18 · Nulables, sin default (las obras normales llevan `NULL`)."""
    c = ObraORM.__table__.columns[columna]
    assert c.type.compile(dialect=DIALECTO) == tipo
    assert c.nullable is True
    assert c.default is None and c.server_default is None


def test_f039_r18_el_alter_lo_deriva_esquema() -> None:
    """R18 · Sobre una base sin las columnas, `alters_faltantes` deriva los
    tres `ADD COLUMN`; con ellas, nada."""
    from infrastructure.db.esquema import alters_faltantes

    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()}
    assert alters_faltantes(Base.metadata, existentes) == []
    existentes["obra"] -= set(COLUMNAS_R18)
    assert sorted(alters_faltantes(Base.metadata, existentes)) == sorted(
        f"ALTER TABLE obra ADD COLUMN IF NOT EXISTS {c} {t}"
        for c, t in COLUMNAS_R18.items())


def test_f039_r18_solo_la_tabla_obra_las_tiene() -> None:
    """R18 · Son de la obra (la entrada), no de la asignación."""
    for columna in COLUMNAS_R18:
        con = {t.name for t in Base.metadata.tables.values()
               if columna in t.columns}
        assert con == {"obra"}, columna
