# tests/test_f062_payload_rachas.py
"""F-062 · Las rachas en la api: esquema, payloads y traza (R15, R17, R23,
R24; ARCHITECTURE.md#regla-incidencia).

Offline: la sesión y el transfer falsos de los tests de F-030; ni red ni
BBDD. Los `ide` son inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

from types import SimpleNamespace


# ============================== esquema (T13) ============================ #
def test_f062_r15_esquema_columna_dia_fin_antes():
    from infrastructure.db.orm_models import IncidenciaORM
    from sqlalchemy.dialects import postgresql

    c = IncidenciaORM.__table__.c.sigrid_dia_fin_antes
    assert c.type.compile(dialect=postgresql.dialect()) == "SMALLINT"
    assert c.nullable and c.default is None and c.server_default is None


def test_f062_r15_esquema_alters_de_una_base_sin_la_columna():
    from infrastructure.db.esquema import alters_faltantes
    from infrastructure.db.orm_models import Base

    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()}
    existentes["incidencia"].discard("sigrid_dia_fin_antes")
    assert alters_faltantes(Base.metadata, existentes) == [
        ("ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS "
         "sigrid_dia_fin_antes SMALLINT")]
    assert {t.name for t in Base.metadata.tables.values()
            if "sigrid_dia_fin_antes" in t.columns} == {"incidencia"}


def test_f062_r15_esquema_el_dominio_y_el_repositorio_lo_llevan():
    from domain.models import Incidencia
    from infrastructure.db.repositories import _a_incidencia

    from tests.test_f030_incidencias import _orm_inc

    assert Incidencia(obra_ide=1, codigo="CIV", dia_desde=5,
                      dia_hasta=9).sigrid_dia_fin_antes is None
    orm = _orm_inc(3, 10, 100, "CIV", 5, 9, sigrid_ide_fin=62,
                   sigrid_dia_fin=9, sigrid_dia_fin_antes=7)
    inc = _a_incidencia(orm, "0100", "OBRA 100", "V", "Vacaciones")
    assert (inc.sigrid_ide_fin, inc.sigrid_dia_fin,
            inc.sigrid_dia_fin_antes) == (62, 9, 7)


def test_f062_r15_esquema_la_traza_al_transfer_lleva_el_dia_original():
    from application.traza_incidencias import campos_de_traza

    def inc(**kw):
        base = {"sigrid_ide_ini": None, "sigrid_ide_fin": None,
                "sigrid_dia_ini": None, "sigrid_dia_fin": None,
                "sigrid_dia_fin_antes": None}
        return SimpleNamespace(**{**base, **kw})

    assert campos_de_traza(inc()) == {}
    assert campos_de_traza(inc(sigrid_ide_fin=62, sigrid_dia_fin=9,
                               sigrid_dia_fin_antes=7)) == {
        "hmores_ide_ini": None, "hmores_ide_fin": 62, "dia_ini": None,
        "dia_fin": 9, "dia_fin_antes": 7}
    # Sin día original, la traza de F-030 tal cual (sin la clave).
    assert campos_de_traza(inc(sigrid_ide_ini=51, sigrid_dia_ini=5)) == {
        "hmores_ide_ini": 51, "hmores_ide_fin": None, "dia_ini": 5,
        "dia_fin": None}
    assert campos_de_traza(inc(sigrid_dia_fin_antes=7)) == {
        "hmores_ide_ini": None, "hmores_ide_fin": None, "dia_ini": None,
        "dia_fin": None, "dia_fin_antes": 7}
