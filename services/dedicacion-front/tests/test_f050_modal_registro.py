# tests/test_f050_modal_registro.py
"""F-050 · R29: el modal de registro enseña la partida de cada acción y la
cambia con EL MISMO selector que la columna Partida (sin `<select>`): lo
elegido se guarda (`PUT …/partida`) y se repite el análisis.

Recoge la intención de los `test_f049_c_*` que se borran con el
`<select>` (requirements §6): la partida de la acción se ve aunque no esté
en el catálogo, «partida N» sin código, «sin partida» y escapada; ahora
sobre `textoPartidaAccion` y el botón del modal.

El código REAL de `app.js` en `node` con un DOM mínimo de mentira (patrón de
F-049). Sin `node` se saltan con su motivo; el reviewer los exige `passed`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
JS = (RAIZ / "static" / "js" / "app.js").read_text(encoding="utf-8")
CSS = (RAIZ / "static" / "css" / "styles.css").read_text(encoding="utf-8")


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _registro() -> str:
    m = re.search(r"^const registro = \{.*?\};$", JS, re.MULTILINE)
    assert m, "no está `const registro = {...};` en app.js"
    return m.group(0)


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


ESCAPE = ("function escapeHtml(t) { return (t == null ? '' : String(t))"
          ".replace(/&/g,'&amp;').replace(/</g,'&lt;')"
          ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }")


# ===================== textoPartidaAccion (antes c_*) ===================== #
def _textos(acciones: list[dict]) -> list[str]:
    return _node("\n".join([
        _funcion("textoPartidaAccion"),
        "process.stdout.write(JSON.stringify(" + json.dumps(acciones) +
        ".map(textoPartidaAccion)));"]))


def test_f050_r29_la_partida_de_la_accion_aunque_no_este_en_el_catalogo():
    assert _textos([{"paride": 80002, "partida_cod": "CI.1.20"},
                    {"paride": 99999, "partida_cod": "CI.9.99"}]) == [
        "CI.1.20", "CI.9.99"]


def test_f050_r29_sin_codigo_partida_n_y_sin_partida():
    assert _textos([{"paride": 80002, "partida_cod": None},
                    {"paride": 0, "partida_cod": "CI.1.20"},
                    {"paride": None}]) == [
        "partida 80002", "sin partida", "sin partida"]


# ========================= el modal (código real) ========================= #
MODAL = ("fmtPct", "pctNuevas", "rotuloConflicto", "textoPartidaAccion",
         "rotuloOrigen", "pintarModalPreflight")


def _modal(obras: list[dict], escenario: str = "") -> dict:
    programa = "\n".join([
        "const MESES = ['ene','feb','mar','abr','may','jun','jul','ago',"
        "'sep','oct','nov','dic'];",
        "const state = {anio: 2026, mes: 9};", _registro(), ESCAPE,
        "let html = null; function abrirModal(h) { html = h; }",
        "function registroEjecutar() {} function repreflightPartida() {}",
        "const botones = []; const aperturas = [];",
        ("function abrirSelectorPartida(t, o, pv, ancla, despues) {"
         " aperturas.push([t, o, pv, ancla.dataset.reg,"
         " despues === repreflightPartida]); }"),
        ("const document = {querySelectorAll: (s) =>"
         " s === '.sel-partida' ? botones : []};"),
        "const $ = () => ({addEventListener() {}});",
        *(_funcion(f) for f in MODAL),
        "function pinta(pf) {",
        "  botones.length = 0;",
        "  [...JSON.stringify(pf).matchAll(/\"registro_id\":(\\d+)/g)]"
        ".forEach((m) => botones.push({dataset: {reg: m[1]}, _h: {},",
        "    addEventListener(ev, fn) { this._h[ev] = fn; }}));",
        "  pintarModalPreflight(pf);",
        "}",
        "pinta(" + json.dumps({"obras": obras}, ensure_ascii=False) + ");",
        "const obs = {};", escenario,
        "obs.html = html; obs.lineas = registro.lineas;",
        "process.stdout.write(JSON.stringify(obs));"])
    return _node(programa)


def _accion(**cambios) -> dict:
    base = {"registro_id": 3001, "nombre": "GONZALEZ PANIAGUA",
            "recurso_ide": 77, "destino": "obra", "es_postventa": False,
            "accion": "escribir", "can": 0.5, "hora_codigo": "MADM",
            "paride": 80002, "partida_cod": "CI.1.20",
            "partida_metodo": "parte_anterior",
            "partida_origen": "parte PT26/00319 · 09/2026 · obra 0694",
            "aviso": None}
    return base | cambios


def _obra(acciones, ide=694, codigo="0694") -> dict:
    return {"obra": {"ide": ide, "codigo": codigo, "nombre": "Obra"},
            "ok": True, "forzada_pruebas": True,
            "obra_destino": {"codigo": "0404"}, "partes": [],
            "acciones": acciones, "partidas_obra": [],
            "partidas_postventa": [], "conflictos": []}


def _boton(html: str, reg: int) -> str:
    m = re.search(r'<button type="button" class="sel-partida" '
                  rf'data-reg="{reg}">([^<]*)</button>', html)
    assert m, html
    return m.group(1)


def test_f050_r29_boton_con_la_partida_y_su_origen_sin_select():
    obs = _modal([_obra([_accion()])])
    assert "<select" not in obs["html"]
    assert _boton(obs["html"], 3001) == "CI.1.20"
    assert ('<div class="origen-partida">parte anterior: parte PT26/00319 '
            '· 09/2026 · obra 0694</div>') in obs["html"]
    assert "MODO PRUEBAS" in obs["html"]


def test_f050_r29_sin_partida_y_escapada():
    obs = _modal([_obra([_accion(paride=0, partida_cod=None,
                                 partida_metodo=None, partida_origen=None,
                                 aviso="sin partida: elige"),
                         _accion(registro_id=3002, partida_cod="A<b>&C",
                                 partida_metodo="manual",
                                 partida_origen=None)])])
    assert _boton(obs["html"], 3001) == "sin partida"
    assert _boton(obs["html"], 3002) == "A&lt;b&gt;&amp;C"
    assert '<div class="origen-partida">elegida</div>' in obs["html"]
    assert '<div class="aviso">sin partida: elige</div>' in obs["html"]
    assert obs["html"].count('class="origen-partida"') == 1


def test_f050_r29_var_sigue_fija_sin_boton():
    obs = _modal([_obra([_accion(partida_metodo="var", partida_cod="29",
                                 partida_origen=None)])])
    assert '<span class="partida-fija">29</span>' in obs["html"]
    assert "sel-partida" not in obs["html"]
    assert obs["lineas"] == {}


def test_f050_r29_clic_abre_el_mismo_selector_para_esa_linea():
    obs = _modal([_obra([_accion(), _accion(registro_id=3002,
                                            recurso_ide=78)]),
                  _obra([_accion(registro_id=3003, recurso_ide=79,
                                 destino="postventa", es_postventa=True)],
                        ide=678, codigo="0678")], """
      botones[1]._h.click(); botones[2]._h.click();
      obs.aperturas = aperturas;
    """)
    assert obs["lineas"] == {
        "3001": {"trabajador": 77, "obra_ide": 694, "es_postventa": False},
        "3002": {"trabajador": 78, "obra_ide": 694, "es_postventa": False},
        "3003": {"trabajador": 79, "obra_ide": 678, "es_postventa": True}}
    assert obs["aperturas"] == [[78, 694, False, "3002", True],
                                [79, 678, True, "3003", True]]


def test_f050_r29_omitidas_sin_boton_y_lineas_de_cero():
    obs = _modal([_obra([_accion(accion="omitir", motivo="la partida X")])])
    assert "sel-partida" not in obs["html"] and obs["lineas"] == {}
    assert '<span class="motivo">la partida X</span>' in obs["html"]


def test_f050_r29_el_front_ya_no_manda_overrides_ni_lee_catalogos():
    assert "overrides" not in JS
    assert "opcionesPartida" not in JS
    assert "partidas_obra" not in JS
    assert "partidas_postventa" not in _funcion("pintarModalPreflight")
    assert "<select" not in JS


def test_f050_r29_pedir_y_ejecutar_mandan_el_trabajador():
    pedir = " ".join(_funcion("pedirPreflight").split())
    assert "JSON.stringify({ trabajador_ide: registro.trabajadorIde })" \
        in pedir
    ejecutar = " ".join(_funcion("registroEjecutar").split())
    assert ("pisar_claves: pisar, trabajador_ide: registro.trabajadorIde,"
            in ejecutar)


def test_f050_r29_css_del_boton_de_partida():
    assert re.search(r"\.modal button\.sel-partida\s*\{", CSS)
    assert re.search(r"\.modal \.origen-partida\s*\{", CSS)
    assert "select.sel-partida" not in CSS


# ============ de punta a punta: elegir → PUT → repetir análisis =========== #
#: DOM de mentira suficiente para `montarSelectorPartida`: el panel, su
#: campo (con sus manejadores), su lista y los botones de mayor.
DOM_SELECTOR = r"""
function nodo(tag) {
  const n = {tag, className: "", innerHTML: "", style: {}, dataset: {},
    hijos: [], _h: {}, classList: {toggle() {}, add() {}},
    addEventListener(ev, fn) { this._h[ev] = fn; },
    appendChild(h) { this.hijos.push(h); return h; },
    querySelector(s) {
      if (s === ".buscar-partida") return this._input || (this._input = nodo("input"));
      if (s === ".lista-partidas") return this._lista || (this._lista = nodo("div"));
      return null;
    },
    querySelectorAll() { return []; },
    contains() { return true; }, remove() { this.quitado = true; },
    focus() {}, scrollIntoView() {}, offsetHeight: 100, value: "",
    isConnected: true,
    getBoundingClientRect() { return {top: 10, bottom: 30, left: 10}; }};
  return n;
}
const paneles = [];
const document = {
  createElement: (t) => { const n = nodo(t); if (t === "div" && !paneles.length) paneles.push(n); return n; },
  body: {appendChild() {}},
  addEventListener() {}, removeEventListener() {},
  documentElement: {clientHeight: 800, clientWidth: 1200},
  querySelectorAll: () => [],
};
const window = {addEventListener() {}, removeEventListener() {}};
"""


def test_f050_r27_r29_elegir_en_el_modal_guarda_y_repite_el_preflight():
    programa = "\n".join([
        "const state = {anio: 2026, mes: 9, empresa: 1, editandoIde: null};",
        _registro(), DOM_SELECTOR, ESCAPE,
        "const selector = { cache: new Map(), cerrar: null };",
        "const llamadas = []; const filas = [];",
        ("function api(url, o) { llamadas.push([url, o ? o.method || 'POST'"
         " : 'GET', o && o.body ? JSON.parse(o.body) : null]);"
         " if (url.includes('/partidas?')) return Promise.resolve({"
         "partidas: [{ide: 80001, cod: 'CI.1.10', res: 'ENC', mayor: 'CI'},"
         " {ide: 80002, cod: 'CI.1.20', res: 'JEFE', mayor: 'CI'}],"
         " partidas_postventa: [], ambito: 'CI', elegida: null, fija: null,"
         " propuesta: {paride: 80002, cod: 'CI.1.20', res: 'JEFE',"
         " metodo: 'parte_anterior', origen: 'x'}});"
         " if (o && o.method === 'PUT') return Promise.resolve({trabajador:"
         " {ide: 77}, resumen: {}});"
         " return new Promise(() => {}); }"),
        "function toast(m) { llamadas.push(['toast', m]); }",
        "function aplicarFila(d) { filas.push(d.trabajador.ide); }",
        "async function guardarAhora() {}",
        ("const $ = (s) => s === '#modal-registro'"
         " ? {classList: {contains: () => false}}"
         " : {addEventListener() {}, disabled: false, textContent: ''};"),
        *(_funcion(f) for f in (
            "normalizar", "filtrarPartidas", "listaSelector", "rotuloOrigen",
            "posicionSugerencias", "clavePartidas", "cerrarSelectorPartida",
            "abrirSelectorPartida", "montarSelectorPartida", "pedirPreflight",
            "repreflightPartida")),
        "registro.trabajadorIde = 77;",
        "(async () => {",
        "  const boton = nodo('button');",
        "  await abrirSelectorPartida(77, 694, false, boton, repreflightPartida);",
        "  const input = paneles[0]._input;",
        "  input._h.keydown({key: 'Enter', preventDefault() {},"
        " stopPropagation() {}});",
        "  await new Promise((r) => setTimeout(r, 0));",
        "  process.stdout.write(JSON.stringify({llamadas, filas,"
        " cache: [...selector.cache.keys()]}));",
        "})();"])
    obs = _node(programa)
    assert obs["llamadas"] == [
        ["/periodos/2026/9/trabajadores/77/partidas?obra_ide=694"
         "&es_postventa=false", "GET", None],
        ["/periodos/2026/9/trabajadores/77/partida", "PUT",
         {"obra_ide": 694, "es_postventa": False,
          "partida": {"ide": 80002, "cod": "CI.1.20", "res": "JEFE"}}],
        ["/periodos/2026/9/registro/preflight", "POST",
         {"trabajador_ide": 77}]]
    assert obs["filas"] == [77]
    assert obs["cache"] == []
