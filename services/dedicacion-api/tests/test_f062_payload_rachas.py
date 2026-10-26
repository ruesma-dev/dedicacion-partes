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


# =============================== traza (T15) ============================= #
class _SesionTraza:
    """Anota cada `UPDATE`/`DELETE` como (tipo, valores, where)."""

    def __init__(self) -> None:
        self.sentencias: list[tuple[str, dict, str]] = []

    def execute(self, sentencia):
        from sqlalchemy.sql.dml import Delete, Update

        tipo = ("update" if isinstance(sentencia, Update)
                else "delete" if isinstance(sentencia, Delete) else "otra")
        self.sentencias.append((tipo, sentencia.compile().params,
                                str(sentencia.whereclause)))


def _acc(i, rol, accion, fecha=20261005, parte="PT26/00251", ide=None,
         **kw):
    return {"id": i, "rol": rol, "accion": accion, "fecha_int": fecha,
            "hora_codigo": "CIV", "paride": 0, "parte_cod": parte,
            "hmores_ide": ide, "motivo": None, **kw}


def _trazar(acciones, **kw):
    from datetime import datetime, timezone

    from application.traza_incidencias import trazar_incidencias

    s = _SesionTraza()
    trazar_incidencias(s, acciones, datetime(2026, 10, 24, tzinfo=timezone.utc),
                       "ana", **kw)
    return s.sentencias


SOLO_ID = "incidencia.id = :id_1"
SIN_IDE = ("incidencia.id = :id_1 AND incidencia.quitada IS true AND "
           "incidencia.sigrid_ide_ini IS NULL AND "
           "incidencia.sigrid_ide_fin IS NULL")


def test_f062_r23_traza_continua_y_abierta_registrado_sin_ide():
    [(tipo, v, where)] = _trazar([
        _acc(7, "ini", "continua", parte="PT26/00040"),
        _acc(7, "fin", "abierta", fecha=20261031)])
    assert (tipo, where, v) == ("update", SOLO_ID, {
        "id_1": 7, "sigrid_estado": "registrado",
        "sigrid_parte_cod": "PT26/00040", "sigrid_motivo": None})
    # Con una escrita: su `ide` y su parte; quién y cuándo, por ella.
    [(_, v, _)] = _trazar([
        _acc(9, "ini", "continua", parte="PT26/00040"),
        _acc(9, "fin", "escribir", fecha=20261016, ide=92)])
    assert (v["sigrid_parte_cod"], v["sigrid_ide_fin"], v["sigrid_dia_fin"],
            v["sigrid_registrado_by"]) == ("PT26/00251", 92, 16, "ana")
    assert "sigrid_ide_ini" not in v and "sigrid_dia_ini" not in v
    [(_, v, _)] = _trazar([_acc(8, "ini", "ya_registrado", ide=81),
                           _acc(8, "fin", "abierta", fecha=20261031)])
    assert (v["sigrid_ide_ini"], "sigrid_registrado_by" in v,
            "sigrid_ide_fin" in v) == (81, False, False)


def test_f062_r15_traza_el_primer_editar_ajeno_guarda_el_dia_original():
    fin = _acc(7, "fin", "editar", fecha=20261009, ide=62,
               fec_antes=20261007, ajena=True)
    principal, antes = _trazar([_acc(7, "ini", "ya_registrado", ide=61),
                                fin])
    assert (principal[1]["sigrid_ide_fin"], principal[1]["sigrid_dia_fin"]) \
        == (62, 9)
    assert antes == ("update", {"id_1": 7, "sigrid_dia_fin_antes": 7},
                     ("incidencia.id = :id_1 AND "
                      "incidencia.sigrid_dia_fin_antes IS NULL"))
    # Una nuestra (sin `ajena`) no lo guarda.
    sentencias = _trazar([_acc(7, "ini", "ya_registrado", ide=61),
                          {**fin, "ajena": False}])
    assert len(sentencias) == 1


def test_f062_r17_traza_devolver_anula_y_borra_la_quitada_sin_ide():
    nulos = {"sigrid_ide_fin": None, "sigrid_dia_fin": None,
             "sigrid_dia_fin_antes": None}
    assert _trazar([_acc(5, "devolver", "editar", 20261007, ide=62)]) == [
        ("update", {"id_1": 5, **nulos}, SOLO_ID),
        ("delete", {"id_1": 5}, SIN_IDE)]
    assert _trazar([_acc(5, "devolver", "ya_registrado", ide=62)])[0] == (
        "update", {"id_1": 5, **nulos}, SOLO_ID)
    # Omitida, no se toca nada (el CIZ sigue movido y su traza, también).
    assert _trazar([_acc(5, "devolver", "omitir", ide=62)]) == []
    # R16: con su `fin` nuevo, primero se anula y luego se traza.
    [anula, traza, borra] = _trazar([
        _acc(7, "devolver", "editar", 20261007, ide=62),
        _acc(7, "ini", "ya_registrado", ide=61),
        _acc(7, "fin", "escribir", 20261012, ide=72)])
    assert (anula[1], traza[1]["sigrid_ide_fin"], borra[0]) == (
        {"id_1": 7, **nulos}, 72, "delete")


def test_f062_r17_traza_la_quitada_sin_lineas_en_sigrid_se_borra():
    nc = [{"tipo": "quitada", "recurso_ide": 10, "incidencia_id": 5,
           "lineas": [], "motivo": "m", "en_sigrid": []},
          {"tipo": "quitada", "recurso_ide": 10, "incidencia_id": 6,
           "lineas": [], "motivo": "m", "en_sigrid": [81]},
          {"tipo": "solo_sigrid", "recurso_ide": 10, "incidencia_id": None,
           "lineas": [], "motivo": "m", "en_sigrid": [91]}]
    assert _trazar([], no_coincide=nc) == [
        ("delete", {"id_1": 5}, ("incidencia.id = :id_1 AND "
                                 "incidencia.quitada IS true"))]
    # Con su `devolver` sin hacer, no: su traza hace falta para devolverlo.
    assert _trazar([_acc(5, "devolver", "omitir", ide=62)],
                   no_coincide=nc) == []


def test_f062_r23_traza_el_cierre_escrito_va_al_fin_de_su_incidencia():
    cierres = [
        {"recurso_ide": 10, "accion": "escribir", "incidencia_id": 4,
         "hmores_ide": 99, "fecha_int": 20261031, "parte_cod": "PT26/00251"},
        {"recurso_ide": 10, "accion": "escribir", "incidencia_id": None,
         "hmores_ide": 98, "fecha_int": 20261031},
        {"recurso_ide": 11, "accion": "pendiente", "incidencia_id": 3,
         "hmores_ide": None, "fecha_int": 20261031},
        {"recurso_ide": 12, "accion": "aviso", "incidencia_id": 2,
         "hmores_ide": None, "fecha_int": 20261031}]
    assert _trazar([], cierres=cierres) == [
        ("update", {"id_1": 4, "sigrid_ide_fin": 99, "sigrid_dia_fin": 31},
         SOLO_ID)]


def test_f062_r23_traza_ejecutar_pasa_cierres_y_no_coincide():
    from application.registro_sigrid import RegistroSigrid
    from sqlalchemy.sql.dml import Delete

    from tests.test_f030_registro import _Sesion

    class _SesionBorra(_Sesion):
        def execute(self, sentencia):
            if isinstance(sentencia, Delete):
                self._anotado["updates"].append(
                    ("borrar", sentencia.compile().params))
                return None
            return super().execute(sentencia)

    anotado = {"updates": [], "selects": []}
    transfer = _Transfer({
        "ok": True, "escritas": [], "omitidas": [], "ya_registradas": [],
        "cierres_racha": [{"recurso_ide": 10, "accion": "escribir",
                           "incidencia_id": 4, "hmores_ide": 99,
                           "fecha_int": 20261031}],
        "no_coincide": [{"tipo": "quitada", "recurso_ide": 10,
                         "incidencia_id": 5, "lineas": [], "motivo": "m",
                         "en_sigrid": []}]})
    RegistroSigrid(lambda: _SesionBorra([_fila(1, (10, 1), (678, 1))], [],
                                        anotado), transfer, 1).ejecutar(
        2026, 7, pisar_claves=[], usuario="ana")
    assert [x for x in anotado["updates"] if x[0] in ("incidencia", "borrar")
            ] == [("incidencia", {"id_1": 4, "sigrid_ide_fin": 99,
                                  "sigrid_dia_fin": 31}),
                  ("borrar", {"id_1": 5})]


def test_f062_r31_traza_el_cierre_pendiente_no_toca_el_fin():
    # R31 (D17): sin confirmar, el cierre no se escribe: su incidencia de
    # M−1 sigue sin `fin`, aunque el elemento traiga la clave y el día.
    cierres = [{"recurso_ide": 10, "accion": "pendiente", "incidencia_id": 4,
                "hmores_ide": None, "fecha_int": 20261031,
                "parte_cod": "PT26/00251", "requiere_confirmar": True,
                "clave": "cierre:51"}]
    assert _trazar([], cierres=cierres) == []
    # Confirmado (relanzado con la clave), es un `escribir` y va al `fin`.
    cierres[0].update(accion="escribir", hmores_ide=99)
    assert _trazar([], cierres=cierres) == [
        ("update", {"id_1": 4, "sigrid_ide_fin": 99, "sigrid_dia_fin": 31},
         SOLO_ID)]


def test_f062_r17_traza_solo_sigrid_nunca_borra_aunque_traiga_incidencia():
    # Mutación (T22): solo una `quitada` con su `id` y sin líneas en Sigrid
    # se borra; un `solo_sigrid`, aunque traiga `incidencia_id`, nunca.
    nc = [{"tipo": "solo_sigrid", "recurso_ide": 10, "incidencia_id": 5,
           "lineas": [], "motivo": "m", "en_sigrid": []}]
    assert _trazar([], no_coincide=nc) == []
