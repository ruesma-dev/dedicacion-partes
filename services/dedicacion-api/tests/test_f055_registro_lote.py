# tests/test_f055_registro_lote.py
"""F-055 · T10: el registro de la api con la propuesta guardada y el
preflight en lote (R14, R16, R26).

- R16: la automática con propuesta guardada viaja con `propuesta_paride`,
  `_cod`, `_res`, `_metodo` y `_origen`; la elegida (`paride`) y el
  override del modal mandan; VAR, como hoy.
- R26: el preflight es UNA llamada a `preflight_lote` y devuelve la forma de
  hoy (`{ok, obras: [{obra, …}], no_vigentes}`); `ejecutar`, por obra y en
  serie.
- R14: tras el preflight, cada acción con método de propuesta guarda su
  partida en la asignación si sigue sin elegida (`UPDATE … WHERE id AND
  partida_ide IS NULL`), sin evento, sin `sigrid_*` y sin tocar la
  respuesta.

Sesión y transfer falsos de F-024 (lista cerrada). Sin red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from application.registro_sigrid import RegistroSigrid, es_metodo_de_propuesta
from sqlalchemy.dialects import postgresql

from tests.test_f024_registro_empresa import _Sesion, _Transfer
from tests.test_f039_registro_var import VAR_29
from tests.test_f039_registro_var import _fila as _fila_var

PR = {"propuesta_ide": 80002, "propuesta_cod": "CI.1.20",
      "propuesta_res": "JEFE DE OBRA", "propuesta_metodo": "parte_anterior",
      "propuesta_origen": "parte PT26/00050 · 05/2026 · obra 0678"}
NADA = dict.fromkeys(PR)


def _fila(asig_id, obra_ide=678, *, partida_ide=None, pv=False, **prop):
    asignacion = SimpleNamespace(id=asig_id, porcentaje=40, es_postventa=pv,
                                 partida_ide=partida_ide,
                                 partida_cod="CI.1.9" if partida_ide else None,
                                 **{**NADA, **prop})
    trabajador = SimpleNamespace(ide=10, dni=None, nombre="T10",
                                 categoria="Encargado", empresa=1,
                                 activo=True, fecha_baja=None)
    obra = SimpleNamespace(ide=obra_ide, cod=f"0{obra_ide}",
                           descripcion="OBRA", empresa=1,
                           registro_obra_ide=None, registro_obra_cod=None,
                           registro_paride=None)
    return asignacion, trabajador, obra


class _TransferLote(_Transfer):
    """Anota las llamadas al lote y contesta lo fijado por obra."""

    def __init__(self, por_obra=None, lote=None) -> None:
        super().__init__()
        self.lotes: list[list[dict]] = []
        self.por_obra = por_obra or {}
        self.lote = lote

    def preflight(self, payload):
        raise AssertionError("el preflight va en lote (R26)")

    def preflight_lote(self, peticiones):
        self.lotes.append(peticiones)
        if self.lote is not None:
            return self.lote
        return {"ok": True, "obras": [
            self.por_obra.get(p["obra"]["ide"], {"ok": True})
            for p in peticiones]}


def _registro(filas, transfer, updates=None):
    anotadas = updates if updates is not None else []
    return RegistroSigrid(lambda: _Sesion(filas, anotadas), transfer, 1), \
        anotadas


def _lineas(transfer):
    return [ln for lote in transfer.lotes for p in lote for ln in p["lineas"]]


# ================================ R16 ==================================== #
def test_f055_r16_la_automatica_viaja_con_su_propuesta():
    t = _TransferLote()
    _registro([_fila(1, **PR), _fila(2, 713)], t)[0].preflight(2026, 8)
    [l1, l2] = _lineas(t)
    assert {k: l1[k] for k in l1 if k.startswith("propuesta_")} == {
        "propuesta_paride": 80002, "propuesta_cod": "CI.1.20",
        "propuesta_res": "JEFE DE OBRA", "propuesta_metodo": "parte_anterior",
        "propuesta_origen": "parte PT26/00050 · 05/2026 · obra 0678"}
    assert "paride" not in l1
    assert not any(k.startswith("propuesta_") for k in l2)


def test_f055_r16_la_elegida_y_el_override_mandan():
    t = _TransferLote()
    _registro([_fila(1, partida_ide=80003, **PR), _fila(2, 713, **PR)],
              t)[0].preflight(2026, 8, overrides={2: 80001})
    [l1, l2] = _lineas(t)
    assert (l1["paride"], l2["paride"]) == (80003, 80001)
    assert not any(k.startswith("propuesta_") for k in {**l1, **l2})


def test_f055_r16_ejecutar_tambien_la_manda():
    t = _TransferLote()
    _registro([_fila(1, **PR)], t)[0].ejecutar(2026, 8, pisar_claves=[])
    [p] = t.payloads
    assert p["lineas"][0]["propuesta_paride"] == 80002


def test_f055_r16_var_como_hoy():
    t = _TransferLote()
    fila = _fila_var(1, 10, VAR_29)
    _registro([fila], t)[0].preflight(2026, 8)
    [ln] = _lineas(t)
    assert ln["var_paride"] == 417055
    assert not any(k.startswith("propuesta_") for k in ln)


# ================================ R26 ==================================== #
def test_f055_r26_una_llamada_y_la_forma_de_hoy():
    t = _TransferLote(por_obra={678: {"ok": True, "acciones": []},
                                713: {"ok": False, "error": "x"}})
    r = _registro([_fila(1), _fila(2, 713)], t)[0].preflight(2026, 8)
    assert len(t.lotes) == 1 and len(t.lotes[0]) == 2
    assert all(p["pisar_claves"] == [] for p in t.lotes[0])
    assert r == {"ok": False, "no_vigentes": [], "obras": [
        {"obra": {"ide": 678, "codigo": "0678", "nombre": "OBRA"},
         "ok": True, "acciones": []},
        {"obra": {"ide": 713, "codigo": "0713", "nombre": "OBRA"},
         "ok": False, "error": "x"}]}


def test_f055_r26_sin_lineas_no_llama():
    t = _TransferLote()
    r = _registro([], t)[0].preflight(2026, 8)
    assert t.lotes == [] and r == {"ok": True, "obras": [],
                                   "no_vigentes": []}


@pytest.mark.parametrize("lote", [
    {"ok": False, "error": "transfer inaccesible: x"},
    {"ok": True, "obras": [{"ok": True}]},          # le falta una obra
    {"ok": True},
], ids=["caido", "incompleto", "sin_obras"])
def test_f055_r26_lote_que_falla_cada_obra_con_su_error(lote):
    t = _TransferLote(lote=lote)
    r = _registro([_fila(1), _fila(2, 713)], t)[0].preflight(2026, 8)
    assert r["ok"] is False
    assert [o["ok"] for o in r["obras"]] == [False, False]
    assert all(o["error"] for o in r["obras"])
    if "error" in lote:
        assert r["obras"][0]["error"] == "transfer inaccesible: x"


def test_f055_r26_solo_la_obra_pedida_en_el_lote():
    t = _TransferLote()
    _registro([_fila(1), _fila(2, 713)], t)[0].preflight(2026, 8,
                                                         obra_ide=713)
    assert [p["obra"]["ide"] for p in t.lotes[0]] == [713]


def test_f055_r26_ejecutar_por_obra_y_en_serie():
    t = _TransferLote()
    _registro([_fila(1), _fila(2, 713)], t)[0].ejecutar(2026, 8,
                                                        pisar_claves=[])
    assert [p["obra"]["ide"] for p in t.payloads] == [678, 713]
    assert t.lotes == []


def test_f055_r26_cliente_http_del_lote(monkeypatch):
    from infrastructure.transfer import transfer_client as mod
    llamadas = []

    def post(url, json, timeout):
        llamadas.append((url, json, timeout))
        return SimpleNamespace(status_code=200,
                               json=lambda: {"ok": True, "obras": []})

    monkeypatch.setattr(mod.httpx, "post", post)
    cli = mod.TransferClient(SimpleNamespace(
        transfer_base_url="http://transfer.invalid/", transfer_timeout_s=7.0))
    assert cli.preflight_lote([{"obra": {"ide": 1}}]) == {"ok": True,
                                                         "obras": []}
    assert llamadas == [("http://transfer.invalid/api/registro/"
                         + "preflight-lote",
                         {"peticiones": [{"obra": {"ide": 1}}]}, 7.0)]


# ================================ R14 ==================================== #
def _accion(rid, metodo, paride=80002, **kw):
    return {"registro_id": rid, "accion": "escribir", "paride": paride,
            "partida_cod": "CI.1.20", "partida_res": "JEFE DE OBRA",
            "partida_metodo": metodo, "partida_origen": kw.get("origen")}


def test_f055_r14_guarda_las_propuestas_sin_tocar_nada_mas():
    acciones = [_accion(1, "parte_anterior", origen="parte P · 05/2026"),
                _accion(2, "ultimo_parte"), _accion(3, "auto_nombre"),
                _accion(4, "auto_categoria"), _accion(5, "manual"),
                _accion(6, "postventa"), _accion(7, "var"),
                _accion(8, None, paride=0)]
    respuesta = {"ok": True, "acciones": acciones}
    t = _TransferLote(por_obra={678: dict(respuesta)})
    reg, updates = _registro([_fila(1)], t)
    r = reg.preflight(2026, 8)
    assert r["obras"][0]["acciones"] == acciones           # la respuesta, igual
    guardadas = [u for u in updates if "commit" not in u]
    assert [u["id_1"] for u in guardadas] == [1, 2, 3, 4]
    assert guardadas[0] == {
        "propuesta_ide": 80002, "propuesta_cod": "CI.1.20",
        "propuesta_res": "JEFE DE OBRA",
        "propuesta_metodo": "parte_anterior",
        "propuesta_origen": "parte P · 05/2026", "id_1": 1}
    assert updates[-1] == {"commit": True}
    assert not any(k.startswith("sigrid_") for u in updates for k in u)


def test_f055_r14_solo_si_sigue_sin_elegida():
    from application import registro_sigrid as mod
    sentencias = []

    class _S(_Sesion):
        def execute(self, sentencia):
            sentencias.append(sentencia)
            return super().execute(sentencia)

    t = _TransferLote(por_obra={678: {"ok": True, "acciones": [
        _accion(1, "auto_nombre")]}})
    RegistroSigrid(lambda: _S([_fila(1)], []), t, 1).preflight(2026, 8)
    sql = str(sentencias[-1].compile(dialect=postgresql.dialect()))
    assert "WHERE asignacion.id = %(id_1)s AND asignacion.partida_ide IS " \
           "NULL" in sql
    assert sentencias[-1].is_update and mod.es_metodo_de_propuesta


def test_f055_r14_sin_propuestas_ni_sesion_ni_commit():
    t = _TransferLote(por_obra={678: {"ok": True, "acciones": [
        _accion(1, "manual")]}, 713: {"ok": False, "error": "x"}})
    reg, updates = _registro([_fila(1), _fila(2, 713)], t)
    reg.preflight(2026, 8)
    assert updates == []


def test_f055_r14_cualquier_accion_con_propuesta_y_sin_partida_no():
    acciones = [dict(_accion(1, "auto_nombre"), accion="omitir"),
                dict(_accion(2, "auto_nombre"), accion="ya_registrado"),
                _accion(3, "auto_nombre", paride=0)]
    t = _TransferLote(por_obra={678: {"ok": True, "acciones": acciones}})
    reg, updates = _registro([_fila(1)], t)
    reg.preflight(2026, 8)
    assert [u.get("id_1") for u in updates if "commit" not in u] == [1, 2]


def test_f055_r14_metodos_de_propuesta():
    assert es_metodo_de_propuesta("parte_anterior") and \
        es_metodo_de_propuesta("ultimo_parte") and \
        es_metodo_de_propuesta("auto_nombre") and \
        es_metodo_de_propuesta("auto_categoria")
    for otro in ("manual", "postventa", "var", None, "", "auto"):
        assert not es_metodo_de_propuesta(otro)
