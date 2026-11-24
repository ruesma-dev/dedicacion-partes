# tests/test_f074_no_valida_api.py
"""F-074 · T9: la propuesta guardada que el preflight omite por no válida se
borra para que la cola la recalcule (R16, D4).

- La línea o subfila que viajó con propuesta guardada y vuelve omitida con
  `partida_no_valida` pierde la guardada (`propuesta_*` a NULL) si sigue sin
  elegida (`WHERE … partida_ide IS NULL`); sin evento ni `sigrid_*`.
- La elegida no se toca; la de postventa (la de su obra, no guardada), no.
- Al volver del preflight ya no se guarda ninguna propuesta (F-055 R14): el
  preflight ya no propone.

Sesión y transfer falsos de F-024 / F-055. Sin red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace

from application.registro_sigrid import RegistroSigrid
from sqlalchemy.dialects import postgresql

from tests.test_f024_registro_empresa import _Sesion
from tests.test_f055_registro_lote import PR, _fila, _registro, _TransferLote

NULOS = dict.fromkeys(("propuesta_ide", "propuesta_cod", "propuesta_res",
                       "propuesta_metodo", "propuesta_origen"))


def _omitida(rid, cod="CI.1.20", **kw):
    return {"registro_id": rid, "accion": "omitir", "paride": 0,
            "motivo": f"la partida {cod} propuesta no es …",
            "partida_no_valida": cod, **kw}


def test_f074_r16_la_guardada_no_valida_se_borra():
    t = _TransferLote(por_obra={678: {"ok": True, "acciones": [
        _omitida(1)]}})
    reg, updates = _registro([_fila(1, **PR)], t)
    r = reg.preflight(2026, 8)
    assert r["obras"][0]["acciones"] == [_omitida(1)]   # respuesta, igual
    assert updates == [{**NULOS, "id_1": 1}, {"commit": True}]


def test_f074_r16_solo_si_sigue_sin_elegida():
    sentencias = []

    class _S(_Sesion):
        def execute(self, sentencia):
            sentencias.append(sentencia)
            return super().execute(sentencia)

    t = _TransferLote(por_obra={678: {"ok": True, "acciones": [
        _omitida(1)]}})
    RegistroSigrid(lambda: _S([_fila(1, **PR)], []), t, 1).preflight(2026, 8)
    sql = str(sentencias[-1].compile(dialect=postgresql.dialect()))
    assert "WHERE asignacion.id = %(id_1)s AND asignacion.partida_ide IS " \
           "NULL" in sql


def test_f074_r16_la_elegida_que_no_vale_no_se_toca():
    """La elegida viaja como `paride`, sin propuesta: aunque vuelva omitida
    con `partida_no_valida`, no hay guardada que borrar."""
    t = _TransferLote(por_obra={678: {"ok": True, "acciones": [
        _omitida(1, "CI.1.9")]}})
    reg, updates = _registro([_fila(1, partida_ide=80004, **PR)], t)
    reg.preflight(2026, 8)
    assert updates == []


def test_f074_r16_la_de_postventa_no_se_borra():
    a, tr, o = _fila(1, pv=True)
    o = SimpleNamespace(**vars(o), postventa_partida_ide=70001,
                        postventa_partida_cod="0656",
                        postventa_partida_res="TOMARES")
    t = _TransferLote(por_obra={678: {"ok": True, "acciones": [
        _omitida(1, "0656")]}})
    reg, updates = _registro([(a, tr, o)], t)
    reg.preflight(2026, 8)
    assert updates == []


def test_f074_r16_sin_partida_no_valida_nada_ni_se_guarda_propuesta():
    """Ya no se guarda lo que vuelve del preflight (F-055 R14 retirado)."""
    acciones = [{"registro_id": 1, "accion": "escribir", "paride": 80002,
                 "partida_cod": "CI.1.20", "partida_metodo": "auto_nombre"},
                {"registro_id": 2, "accion": "omitir", "paride": 0,
                 "motivo": "otra cosa", "partida_no_valida": None}]
    t = _TransferLote(por_obra={678: {"ok": True, "acciones": acciones}})
    reg, updates = _registro([_fila(1), _fila(2, **PR)], t)
    reg.preflight(2026, 8)
    assert updates == []


def test_f074_r16_obra_que_falla_no_borra():
    t = _TransferLote(por_obra={678: {"ok": False, "error": "x",
                                      "acciones": [_omitida(1)]}})
    reg, updates = _registro([_fila(1, **PR)], t)
    reg.preflight(2026, 8)
    assert updates == []


def test_f074_r16_la_subfila_que_no_vale_se_borra_si_viajo_con_guardada():
    sentencias = []

    class _S(_Sesion):
        def execute(self, sentencia):
            sentencias.append(sentencia)
            return super().execute(sentencia)

    reg = RegistroSigrid(lambda: _S([], []), _TransferLote(), 1)
    payloads = [{"obra": {"ide": 678}, "lineas": [
        {"registro_id": 1, "vinculados": [
            {"recurso_ide": 10, "propuesta_paride": 81001},
            {"recurso_ide": 11, "paride": 81002},
            {"recurso_ide": 12}]}]}]
    resultados = [{"ok": True, "acciones": [], "vinculados": [
        {"registro_id": 1, "recurso_ide": 10, "accion": "omitir",
         "partida_no_valida": "CICO13"},
        {"registro_id": 1, "recurso_ide": 11, "accion": "omitir",
         "partida_no_valida": "CIGA14"},
        {"registro_id": 1, "recurso_ide": 12, "accion": "escribir",
         "partida_no_valida": None}]}]
    reg._borrar_no_validas(payloads, resultados)
    [upd] = [s for s in sentencias if getattr(s, "is_update", False)]
    sql = str(upd.compile(dialect=postgresql.dialect()))
    assert "UPDATE asignacion_vinculado SET propuesta_ide=" in sql
    assert ("asignacion_vinculado.asignacion_id = %(asignacion_id_1)s AND "
            "asignacion_vinculado.vinculado_ide = %(vinculado_ide_1)s AND "
            "asignacion_vinculado.partida_ide IS NULL") in sql
    params = upd.compile().params
    assert (params["asignacion_id_1"], params["vinculado_ide_1"]) == (1, 10)
    assert all(params[k] is None for k in NULOS)
