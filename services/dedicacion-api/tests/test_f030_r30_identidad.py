# tests/test_f030_r30_identidad.py
"""F-030 · Anexo R30 en la api: la incidencia conserva su identidad.

Cambiar los días de una ya registrada no es otra incidencia: el PUT manda su
`id` (R36, R37), la fila y su traza se conservan, la que se quita estando
registrada queda `quitada` (R38, D11), la traza guarda por rol el `ide` y el
día de Sigrid (R39) y deshacer repone `id` y traza (R47).

Offline: metadatos del ORM, dobles en memoria de la sesión y de la unidad de
trabajo. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

import dataclasses

import pytest
from domain.models import Incidencia


# ============================ esquema (T23) ============================= #
def test_f030_r30_esquema_alters_anade_las_tres_columnas_de_incidencia():
    """Sobre una base con la tabla de T1-T19, `alters_faltantes` emite los
    tres `ADD COLUMN` (R38, R39) y nada para `asignacion` ni otra tabla."""
    from infrastructure.db.esquema import alters_faltantes
    from infrastructure.db.orm_models import Base

    al_dia = {t.name: {c.name for c in t.columns}
              for t in Base.metadata.tables.values()}
    vieja = dict(al_dia)
    vieja["incidencia"] = al_dia["incidencia"] - {
        "quitada", "sigrid_dia_ini", "sigrid_dia_fin"}
    assert alters_faltantes(Base.metadata, vieja) == [
        ("ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS "
         "quitada BOOLEAN DEFAULT false NOT NULL"),
        "ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS sigrid_dia_ini SMALLINT",
        "ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS sigrid_dia_fin SMALLINT"]
    assert alters_faltantes(Base.metadata, al_dia) == []


def test_f030_r30_esquema_quitada_por_defecto_falsa_en_python_y_servidor():
    from infrastructure.db.orm_models import IncidenciaORM

    col = IncidenciaORM.__table__.columns["quitada"]
    assert (col.nullable, col.default.arg) == (False, False)
    for nombre in ("sigrid_dia_ini", "sigrid_dia_fin"):
        c = IncidenciaORM.__table__.columns[nombre]
        assert (c.nullable, c.default, c.server_default) == (True, None, None)


def test_f030_r30_esquema_modelo_de_dominio_con_identidad_y_traza():
    inc = Incidencia(obra_ide=100, codigo="CIV", dia_desde=5, dia_hasta=9)
    assert (inc.quitada, inc.sigrid_ide_ini, inc.sigrid_ide_fin,
            inc.sigrid_dia_ini, inc.sigrid_dia_fin) == (False, None, None,
                                                        None, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        inc.quitada = True  # type: ignore[misc]


def test_f030_r30_esquema_entrada_con_id_opcional_y_salida_con_quitada():
    from interface_adapters.api.schemas import (
        IncidenciaIn,
        IncidenciasIn,
        a_incidencia_out,
    )
    from pydantic import ValidationError

    assert IncidenciaIn(obra_ide=1, codigo="CIV").id is None
    cuerpo = IncidenciasIn.model_validate({"incidencias": [
        {"id": 7, "obra_ide": 1, "codigo": "CIV", "dia_desde": 6,
         "dia_hasta": 9}]})
    assert cuerpo.incidencias[0].id == 7
    with pytest.raises(ValidationError):
        IncidenciaIn.model_validate({"obra_ide": 1, "codigo": "CIV",
                                     "quitada": True})   # la decide la api
    inc = Incidencia(obra_ide=1, codigo="CIV", dia_desde=5, dia_hasta=9,
                     id=7, quitada=True, sigrid_ide_ini=9001)
    out = a_incidencia_out(inc).model_dump()
    assert (out["id"], out["quitada"]) == (7, True)
    assert "sigrid_ide_ini" not in out          # la traza no viaja al front
    assert a_incidencia_out(dataclasses.replace(inc, quitada=False)
                            ).quitada is False


def test_f030_r30_esquema_el_repo_mapea_quitada_e_ides_y_dias_de_sigrid():
    from infrastructure.db.orm_models import IncidenciaORM
    from infrastructure.db.repositories import _a_incidencia

    orm = IncidenciaORM(id=7, periodo_id=3, trabajador_ide=14, obra_ide=100,
                        codigo="CIV", dia_desde=6, dia_hasta=9, quitada=True,
                        sigrid_ide_ini=9001, sigrid_ide_fin=9002,
                        sigrid_dia_ini=5, sigrid_dia_fin=9,
                        sigrid_estado="registrado")
    inc = _a_incidencia(orm, "0100", "OBRA 100", "V", "Vacaciones")
    assert (inc.id, inc.quitada, inc.sigrid_ide_ini, inc.sigrid_ide_fin,
            inc.sigrid_dia_ini, inc.sigrid_dia_fin) == (7, True, 9001, 9002,
                                                        5, 9)
    orm.quitada = None                  # fila aún sin `flush`: no es quitada
    assert _a_incidencia(orm, "0100", "OBRA", "V", "V").quitada is False
