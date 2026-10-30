# tests/test_f054_registro_cero.py
"""F-054 · T14: la api encamina la parte B (R31, R33, R35; design §6.4).

- El preflight del periodo o de un trabajador pide al lote del transfer el
  preflight `completo`; el de una obra sola (`obra_ide`, el repreflight del
  modal) no. La respuesta lleva `sobrantes` solo si hay alguna.
- `ejecutar(…, sobrantes_a_cero)`: si trae alguna, PRIMERO
  `poner_a_cero` y después las peticiones por obra de siempre; la
  respuesta gana `sobrantes_a_cero: {puestas, omitidas}` solo si vino
  alguna. Sin ellas, las peticiones y la respuesta de hoy (y el `a_cero`
  por obra de F-051 no cambia: viaja en `pisar_claves`, como hoy).
- `TransferClient.poner_a_cero` y `preflight_lote(…, completo)`.

Sesión y transfer falsos de `test_f022_empresa_en_linea.py` y filas de
`test_f051_hmores_ide.py`. Sin red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from application.registro_sigrid import RegistroSigrid

from tests.test_f022_empresa_en_linea import _Sesion, _Transfer
from tests.test_f051_hmores_ide import _fila

SOBRANTE = {"clave": "cero:7001", "hmores_ide": 7001, "recurso_ide": 201,
            "vinculado": None, "obra_ide": 694, "obra_cod": "0694",
            "parte_cod": "PT26/1", "parte_est": 1, "hora": "MENC",
            "paride": 9, "partida_cod": None, "can": 0.3, "synckey": None,
            "confirmable": True, "motivo": None}


class _TransferCero(_Transfer):
    def __init__(self, sobrantes=None, falla_cero=False) -> None:
        super().__init__()
        self.llamadas: list = []
        self.sobrantes = sobrantes
        self.falla_cero = falla_cero

    def preflight_lote(self, peticiones, completo=False):
        self.llamadas.append(("preflight_lote", completo))
        r = super().preflight_lote(peticiones)
        if completo and self.sobrantes is not None:
            r["sobrantes"] = list(self.sobrantes)
        return r

    def poner_a_cero(self, empresa, ano, mes, lineas):
        self.llamadas.append(("poner_a_cero", empresa, ano, mes, lineas))
        if self.falla_cero:
            raise RuntimeError("transfer caido")
        return {"ok": True, "puestas": [{"hmores_ide": 7001}],
                "omitidas": []}

    def ejecutar(self, payload):
        self.llamadas.append(("ejecutar", payload["obra"]["ide"]))
        return super().ejecutar(payload)


def _registro(transfer, filas=None):
    filas = filas or [_fila(1)]
    return RegistroSigrid(lambda: _Sesion(filas), transfer, 1)


@pytest.mark.parametrize("sobrantes, sale", [
    (None, False), ([], False), ([SOBRANTE], True)])
def test_f054_r33_preflight_completo_y_sobrantes_solo_si_hay(sobrantes,
                                                             sale):
    t = _TransferCero(sobrantes)
    r = _registro(t).preflight(2026, 10)
    assert t.llamadas == [("preflight_lote", True)]
    assert ("sobrantes" in r) is sale
    if sale:
        assert r["sobrantes"] == [SOBRANTE]


def test_f054_r31_preflight_de_un_trabajador_tambien_completo():
    t = _TransferCero([SOBRANTE])
    r = _registro(t).preflight(2026, 10, trabajador_ide=201)
    assert t.llamadas == [("preflight_lote", True)]
    assert r["sobrantes"] == [SOBRANTE]


def test_f054_r31_preflight_de_una_obra_no_es_completo():
    t = _TransferCero([SOBRANTE])
    r = _registro(t).preflight(2026, 10, obra_ide=678)
    assert t.llamadas == [("preflight_lote", False)]
    assert "sobrantes" not in r


def test_f054_r35_ejecutar_pone_a_cero_primero():
    t = _TransferCero()
    r = _registro(t).ejecutar(2026, 10, pisar_claves=["k"],
                              sobrantes_a_cero=[SOBRANTE])
    assert t.llamadas == [
        ("poner_a_cero", 1, 2026, 10, [{
            "hmores_ide": 7001, "recurso_ide": 201, "hora": "MENC",
            "vinculado": None, "can": 0.3, "synckey": None}]),
        ("ejecutar", 678)]
    assert r["sobrantes_a_cero"] == {"puestas": [{"hmores_ide": 7001}],
                                     "omitidas": []}
    assert t.payloads[-1]["pisar_claves"] == ["k"]


@pytest.mark.parametrize("sobrantes", [None, []])
def test_f054_r35_sin_sobrantes_como_hoy(sobrantes):
    hoy, t = _TransferCero(), _TransferCero()
    antes = _registro(hoy).ejecutar(2026, 10, pisar_claves=["k"])
    ahora = _registro(t).ejecutar(2026, 10, pisar_claves=["k"],
                                  sobrantes_a_cero=sobrantes)
    assert ahora == antes and "sobrantes_a_cero" not in ahora
    assert t.llamadas == [("ejecutar", 678)]
    assert t.payloads == hoy.payloads


def test_f054_r35_si_poner_a_cero_falla_no_se_escribe_por_obra():
    t = _TransferCero(falla_cero=True)
    with pytest.raises(RuntimeError, match="caido"):
        _registro(t).ejecutar(2026, 10, pisar_claves=[],
                              sobrantes_a_cero=[SOBRANTE])
    assert [x[0] for x in t.llamadas] == ["poner_a_cero"]


# ------------------------------ el cliente -------------------------------- #
def _cliente(monkeypatch, respuesta):
    from infrastructure.transfer import transfer_client as mod
    llamadas = []

    def post(url, json, timeout):
        llamadas.append((url, json))
        return SimpleNamespace(status_code=200, text="", json=lambda: respuesta)

    monkeypatch.setattr(mod.httpx, "post", post)
    return mod.TransferClient(SimpleNamespace(
        transfer_base_url="http://t.invalid", transfer_timeout_s=1.0)), llamadas


def test_f054_cliente_preflight_lote_completo_solo_si_es_true(monkeypatch):
    cli, llamadas = _cliente(monkeypatch, {"ok": True, "obras": []})
    cli.preflight_lote([{"obra": {"ide": 1}}])
    cli.preflight_lote([{"obra": {"ide": 1}}], completo=False)
    cli.preflight_lote([{"obra": {"ide": 1}}], completo=True)
    assert [j for _, j in llamadas] == [
        {"peticiones": [{"obra": {"ide": 1}}]},
        {"peticiones": [{"obra": {"ide": 1}}]},
        {"peticiones": [{"obra": {"ide": 1}}], "completo": True}]


def test_f054_cliente_poner_a_cero(monkeypatch):
    cli, llamadas = _cliente(monkeypatch, {"ok": True, "puestas": [],
                                           "omitidas": []})
    lineas = [{"hmores_ide": 7001}]
    assert cli.poner_a_cero(1, 2026, 10, lineas)["ok"] is True
    assert llamadas == [("http://t.invalid/api/registro/poner-a-cero",
                         {"empresa": 1, "ano": 2026, "mes": 10,
                          "lineas": lineas})]


def test_f054_cliente_poner_a_cero_sin_ok_es_error(monkeypatch):
    cli, _ = _cliente(monkeypatch, {"ok": False, "error": "truncada"})
    with pytest.raises(RuntimeError, match="truncada"):
        cli.poner_a_cero(1, 2026, 10, [{"hmores_ide": 7001}])
