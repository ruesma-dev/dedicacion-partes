# tests/test_hotfix_registro_corte_proxy.py
"""Hotfix 2026-11-11 · El registro cortado por el proxy no se da por fallido.

Producción, 10/11/2026: el registro de octubre (56 obras) tardó ~3,5 min; el
proxy del front cortó a los 200 s con 502 «Backend dedicacion-api
inaccesible» y la pantalla solo enseñó el error, aunque el servidor terminó
todo. El usuario podía relanzarlo.

Arreglo (solo front, sin lógica de negocio):

- `api()` lanza el `Error` con `status` (código HTTP; 0 si el `fetch` rechaza,
  fallo de red). El mensaje no cambia.
- `registroEjecutar()` ante 502, 504 o fallo de red: cierra el modal, aviso
  fijo «sigue en curso… no lo relances», el registro queda bloqueado y a los
  `ESPERA_RECARGA_TRAS_CORTE` ms se recarga el cuadrante del mes registrado.
- Cualquier otro error: el aviso de siempre y el botón «Registrar» vuelve a
  estar disponible (antes se quedaba en «Registrando…»).

Se ejecuta el código REAL de `api`, `conEmpresa`, `registroEjecutar`,
`registroPreflight` y sus ayudantes en node con dobles de `fetch`, `$`,
`toast`, `cerrarModal`, `cargarPeriodo` y `setTimeout`. Sin red ni BBDD; sin
`node` se saltan (el reviewer los exige `passed`).
"""
from __future__ import annotations

import json
import re

import pytest

from tests.test_f042_sugerencias import JS, _funcion, _node

PROXY_502 = {"error": "Backend dedicacion-api inaccesible"}


def _constante(nombre: str) -> str:
    m = re.search(rf"^const {nombre} = .*?;$", JS, re.MULTILINE)
    assert m, f"no existe la constante {nombre} en app.js"
    return m.group(0)


def _si_existe(trozo) -> str:
    """El código de app.js si existe; si no, nada. Así, antes del arreglo,
    los tests de comportamiento fallan por lo que hace la pantalla y no por
    una función que falta (la existencia la piden otros asserts)."""
    try:
        return trozo()
    except AssertionError:
        return ""


def _fetch(respuesta: dict | None) -> str:
    """Doble de `fetch`: `None` rechaza (fallo de red); si no, responde con
    `status` y `cuerpo` (`None`: cuerpo que no es JSON, como el HTML del
    balanceador)."""
    if respuesta is None:
        return ("async function fetch(url, op) { pedidas.push(url);"
                " throw new TypeError('Failed to fetch'); }")
    status, cuerpo = respuesta["status"], respuesta["cuerpo"]
    return ("async function fetch(url, op) { pedidas.push(url); return {"
            f" ok: {json.dumps(200 <= status < 300)}, status: {status},"
            f" json: async () => {{ const c = {json.dumps(cuerpo)};"
            " if (c === null) throw new SyntaxError('no json'); return c; } }; }")


def _programa(respuesta: dict | None, cuerpo_js: str) -> dict:
    return _node("\n".join([
        "var state = { anio: 2026, mes: 10, empresa: null };",
        "var pedidas = []; var avisos = []; var recargas = []; var temporizadores = [];",
        "var modal = { cerrado: false };",
        "function El(t) { return { disabled: false, textContent: t }; }",
        "var botones = { '#btn-ejecutar-registro': El('Registrar'),",
        "                '#btn-registro': El('Registrar en Sigrid') };",
        "function $(sel) { return botones[sel]; }",
        "var document = { querySelectorAll: () => [], addEventListener() {}, body: { dataset: { usuario: 'u' } } };",
        "function toast(m, e = false, fijo = false) {",
        "  const a = { m, e: !!e, fijo: !!fijo, quitado: false };",
        "  avisos.push(a); return { remove() { a.quitado = true; } }; }",
        "function cerrarModal() { modal.cerrado = true; }",
        "async function cargarPeriodo(a, m) { recargas.push([a, m]); }",
        "function setTimeout(f, ms) { temporizadores.push({ f, ms }); }",
        "async function pedirPreflight() { pedidas.push('preflight'); return { obras: [] }; }",
        "function pintarModalPreflight() {}",
        _fetch(respuesta),
        _si_existe(lambda: _constante("ESPERA_RECARGA_TRAS_CORTE")),
        _constante("registro"),
        _funcion("conEmpresa"),
        _funcion("api"),
        _si_existe(lambda: _funcion("esCorteDelProxy")),
        _si_existe(lambda: _funcion("esperarRegistroCortado")),
        _funcion("registroPreflight"),
        _funcion("registroEjecutar"),
        "function foto() { return JSON.parse(JSON.stringify({ pedidas, avisos,",
        "  recargas, modal, botones, cortado: registro.cortado,",
        "  esperas: temporizadores.map((t) => t.ms) })); }",
        "(async () => {", cuerpo_js, "})();",
    ]))


# ----------------------------- api() y status ----------------------------- #
@pytest.mark.parametrize("respuesta, mensaje, status", [
    ({"status": 502, "cuerpo": PROXY_502}, "Backend dedicacion-api inaccesible", 502),
    ({"status": 504, "cuerpo": None}, "Error HTTP 504", 504),
    ({"status": 422, "cuerpo": {"error": "líneas inválidas"}}, "líneas inválidas", 422),
    (None, "Failed to fetch", 0),
])
def test_hotfix_corte_api_lanza_el_error_con_su_status(respuesta, mensaje, status):
    r = _programa(respuesta, "\n".join([
        "try { await api('/periodos/2026/10/cuadrante'); process.stdout.write('null'); }",
        "catch (e) { process.stdout.write(JSON.stringify(",
        "  { mensaje: e.message, status: e.status, esError: e instanceof Error })); }",
    ]))
    assert r == {"mensaje": mensaje, "status": status, "esError": True}


def test_hotfix_corte_api_con_exito_devuelve_el_cuerpo():
    r = _programa({"status": 200, "cuerpo": {"ok": True}}, "\n".join([
        "process.stdout.write(JSON.stringify(await api('/periodos/2026/10/cuadrante')));",
    ]))
    assert r == {"ok": True}


def test_hotfix_corte_la_espera_es_de_60_s():
    assert "ESPERA_RECARGA_TRAS_CORTE)" in _funcion("esperarRegistroCortado")
    assert _constante("ESPERA_RECARGA_TRAS_CORTE") == \
        "const ESPERA_RECARGA_TRAS_CORTE = 60000;"


# ------------------------- registroEjecutar: corte ------------------------ #
CORTES = [
    pytest.param({"status": 502, "cuerpo": PROXY_502}, id="502-proxy"),
    pytest.param({"status": 504, "cuerpo": None}, id="504-balanceador"),
    pytest.param(None, id="red"),
]


@pytest.mark.parametrize("respuesta", CORTES)
def test_hotfix_corte_avisa_bloquea_y_programa_la_recarga(respuesta):
    r = _programa(respuesta, "\n".join([
        "await registroEjecutar();",
        "const antes = foto();",
        # Durante la espera, ni el general ni el de un trabajador relanzan.
        "await registroPreflight(null); await registroPreflight(77);",
        "const bloqueado = foto();",
        "await temporizadores[0].f();",
        "process.stdout.write(JSON.stringify({ antes, bloqueado, despues: foto() }));",
    ]))
    antes = r["antes"]
    assert antes["modal"]["cerrado"] is True
    assert antes["esperas"] == [60000]
    assert antes["recargas"] == []
    assert antes["cortado"] is True
    assert antes["botones"]["#btn-registro"] == {
        "disabled": True, "textContent": "Registro en curso…"}
    [aviso] = antes["avisos"]
    assert aviso["fijo"] is True and aviso["quitado"] is False
    assert "El registro sigue en curso en el servidor" in aviso["m"]
    assert "Recargo el cuadrante en 60 s; no lo relances." in aviso["m"]

    bloqueado = r["bloqueado"]
    assert "preflight" not in bloqueado["pedidas"]
    assert bloqueado["botones"]["#btn-registro"]["disabled"] is True
    assert [a["m"] for a in bloqueado["avisos"][1:]] == [
        "El registro anterior sigue en curso; espera a que se recargue el cuadrante."] * 2

    despues = r["despues"]
    assert despues["recargas"] == [[2026, 10]]
    assert despues["cortado"] is False
    assert despues["avisos"][0]["quitado"] is True
    assert despues["avisos"][-1] == {
        "m": "Cuadrante recargado; revisa el resultado del registro.",
        "e": False, "fijo": False, "quitado": False}
    assert despues["botones"]["#btn-registro"] == {
        "disabled": False, "textContent": "Registrar en Sigrid"}


def test_hotfix_corte_recarga_el_mes_registrado_aunque_se_cambie():
    r = _programa({"status": 502, "cuerpo": PROXY_502}, "\n".join([
        "await registroEjecutar();",
        "state.anio = 2026; state.mes = 11;",
        "await temporizadores[0].f();",
        "process.stdout.write(JSON.stringify(foto()));",
    ]))
    assert r["recargas"] == [[2026, 10]]


# ---------------------- registroEjecutar: error normal -------------------- #
@pytest.mark.parametrize("status", [409, 422, 500, 503])
def test_hotfix_corte_otro_error_como_siempre_y_el_boton_vuelve(status):
    r = _programa({"status": status, "cuerpo": {"error": "fallo concreto"}}, "\n".join([
        "await registroEjecutar();",
        "process.stdout.write(JSON.stringify(foto()));",
    ]))
    assert r["avisos"] == [{"m": "fallo concreto", "e": True, "fijo": False,
                            "quitado": False}]
    assert r["modal"]["cerrado"] is False
    assert r["esperas"] == [] and r["recargas"] == []
    assert not r.get("cortado")
    assert r["botones"]["#btn-ejecutar-registro"] == {
        "disabled": False, "textContent": "Registrar"}
    assert r["botones"]["#btn-registro"] == {
        "disabled": False, "textContent": "Registrar en Sigrid"}


def test_hotfix_corte_sin_corte_el_preflight_va_como_siempre():
    r = _programa({"status": 200, "cuerpo": {}}, "\n".join([
        "await registroPreflight(null);",
        "process.stdout.write(JSON.stringify(foto()));",
    ]))
    assert r["pedidas"] == ["preflight"]
    assert r["avisos"] == []
