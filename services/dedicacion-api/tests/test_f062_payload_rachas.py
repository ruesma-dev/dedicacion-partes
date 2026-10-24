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


# ============================== payload (T14) ============================ #
from tests.test_f024_registro_empresa import _fila, _Transfer
from tests.test_f030_r30_identidad import _inc_traza, _registro_tipos


def _incs():
    """El 10 tiene la 7 en la 678 (con su línea) y la 8 en la 694; el 11,
    la 9 en la 694. La 5 del 10, quitada con traza en la 678; la 4 del 11,
    quitada sin traza; la 3 del 12, quitada con traza en la 700 (sin
    nada más ahí)."""
    return [_inc_traza(7, (10, 1), (678, 1), ini=9001, fin=9002, dia_ini=5,
                       dia_fin=9),
            _inc_traza(5, (10, 1), (678, 1), desde=20, hasta=22, ini=9101,
                       fin=None, dia_ini=20, quitada=True),
            _inc_traza(8, (10, 1), (694, 1), desde=12, hasta=16),
            _inc_traza(9, (11, 1), (694, 1), codigo="CIE", desde=1,
                       hasta=3),
            _inc_traza(4, (11, 1), (694, 1), desde=27, hasta=28,
                       quitada=True),
            _inc_traza(3, (12, 1), (700, 1), desde=6, hasta=7, fin=9301,
                       dia_fin=7, quitada=True)]


def _elem(inc_id, recurso, obra, codigo="CIV", desde=5, hasta=9, **traza):
    return {"id": inc_id, "obra_ide": obra, "recurso_ide": recurso,
            "empresa": 1, "codigo": codigo, "ano": 2026, "mes": 7,
            "desde": desde, "hasta": hasta, "paride": 0, **traza}


I7 = _elem(7, 10, 678, hmores_ide_ini=9001, hmores_ide_fin=9002, dia_ini=5,
           dia_fin=9)
I8 = _elem(8, 10, 694, desde=12, hasta=16)
I9 = _elem(9, 11, 694, "CIE", 1, 3)


def test_f062_r24_payload_incidencias_mes_quitadas_y_cierres():
    transfer = _Transfer()
    _registro_tipos(transfer, [_fila(1, (10, 1), (678, 1))],
                    _incs()).preflight(2026, 7)
    p678, p694, p700 = transfer.payloads
    # R24: las del mes de SUS recursos en cualquier obra, sin quitadas.
    assert p678["incidencias_mes"] == [I7, I8]
    assert p694["incidencias_mes"] == [I7, I8, I9]
    # R17: las quitadas con algún `ide`, en la petición de su obra (si no
    # la hay, se crea); sin traza, no viajan.
    assert p678["quitadas"] == [_elem(5, 10, 678, desde=20, hasta=22,
                                      hmores_ide_ini=9101,
                                      hmores_ide_fin=None, dia_ini=20,
                                      dia_fin=None)]
    assert "quitadas" not in p694
    assert (p700["lineas"], p700["quitadas"]) == ([], [_elem(
        3, 12, 700, desde=6, hasta=7, hmores_ide_ini=None,
        hmores_ide_fin=9301, dia_ini=None, dia_fin=7)])
    # R24: cada recurso, designado en la primera petición donde sale.
    assert (p678["cierres_recursos"], p694["cierres_recursos"]) == ([10], [11])
    assert "cierres_recursos" not in p700 and "incidencias_mes" not in p700
    # Las suyas, como en F-030 (sin `obra_ide`).
    assert [i["id"] for i in p678["incidencias"]] == [7]
    assert "obra_ide" not in p678["incidencias"][0]


def test_f062_r24_payload_tras_el_filtro_de_obra_se_designa_en_ella():
    transfer = _Transfer()
    _registro_tipos(transfer, [_fila(1, (10, 1), (678, 1))],
                    _incs()).preflight(2026, 7, obra_ide=694)
    [p694] = transfer.payloads
    assert p694["cierres_recursos"] == [10, 11]
    assert p694["incidencias_mes"] == [I7, I8, I9]


def test_f062_r24_payload_ejecutar_lleva_lo_mismo():
    transfer = _Transfer()
    _registro_tipos(transfer, [_fila(1, (10, 1), (678, 1))],
                    _incs()).ejecutar(2026, 7, pisar_claves=[])
    p678, p694, p700 = transfer.payloads
    assert p678["incidencias_mes"] == [I7, I8]
    assert (p678["cierres_recursos"], p694["cierres_recursos"]) == ([10], [11])
    assert [q["id"] for q in p700["quitadas"]] == [3]


def test_f062_r24_payload_sin_incidencias_solo_los_designados():
    transfer = _Transfer()
    _registro_tipos(transfer, [_fila(1, (10, 1), (678, 1)),
                               _fila(2, (10, 1), (694, 1)),
                               _fila(3, (11, 1), (694, 1))]).preflight(2026, 7)
    assert [set(p) for p in transfer.payloads] == [
        {"obra", "lineas", "pisar_claves", "cierres_recursos"}] * 2
    assert [p["cierres_recursos"] for p in transfer.payloads] == [[10], [11]]
