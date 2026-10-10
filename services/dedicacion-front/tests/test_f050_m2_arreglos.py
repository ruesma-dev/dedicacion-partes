# tests/test_f050_m2_arreglos.py
"""F-050 · T15c: los arreglos de la MANUAL M2 (humano, 2026-10-11).

1. La tabla cabe en la ventana (las columnas se encogen hasta su mínimo; si
   ni así cabe, scroll horizontal) sin tocar las preferencias de anchos.
2. El cursor se marca igual en todas las subfilas: fondo en todas y una sola
   barra a cada lado del bloque del trabajador.
3. El selector de partida se abre al instante con «Cargando partidas…», un
   segundo clic no abre otro y solo pinta la respuesta del último pedido.
4. En el modal, el selector sale encima del modal y anclado a su línea; abrir
   (o repintar) el modal cierra cualquier selector, también uno cargando.
5. Cambiar una partida en el modal repite el preflight SOLO de la obra de esa
   línea y la sustituye en el modal; las demás obras se quedan como estaban.

El código REAL de `app.js` en `node` con un DOM mínimo de mentira (patrón de
F-042 y F-049); lo demás, estático sobre `app.js` y `styles.css`. Sin `node`
se saltan con su motivo; el reviewer los exige `passed`. Sin red.
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


def _const(nombre: str) -> str:
    m = re.search(rf"^const {nombre} = .*?;$", JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe `const {nombre}` en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


def _regla(selector: str) -> str:
    m = re.search(rf"(?:^|\}})\s*{re.escape(selector)}\s*\{{([^}}]*)\}}", CSS,
                  re.MULTILINE)
    assert m, f"no está la regla `{selector}` en styles.css"
    return _plano(m.group(1))


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


# ================== 1 · la tabla cabe en la ventana ===================== #
PREFERIDOS = [280, 210, 560, 320, 190]      # los de COLUMNAS, en su orden
MINIMOS = [160, 100, 150, 150, 190]


def _ajustados(preferidos, minimos, disponible) -> list:
    return _node("\n".join([
        _funcion("anchosAjustados"),
        "process.stdout.write(JSON.stringify(anchosAjustados(" +
        ", ".join(json.dumps(x) for x in (preferidos, minimos, disponible)) +
        ")));"]))


def test_f050_m2_1_si_cabe_los_anchos_preferidos():
    assert _ajustados(PREFERIDOS, MINIMOS, 1600) == PREFERIDOS
    assert _ajustados(PREFERIDOS, MINIMOS, 1560) == PREFERIDOS


def test_f050_m2_1_si_no_cabe_se_encogen_hasta_caber():
    """1046 px (la ventana de la captura): lo que sobra de cada columna
    sobre su mínimo se reparte en proporción; Total no encoge."""
    anchos = _ajustados(PREFERIDOS, MINIMOS, 1046)
    assert anchos == [203, 140, 299, 212, 190]
    assert sum(anchos) <= 1046


def test_f050_m2_1_nunca_bajo_el_minimo_y_entonces_scroll():
    assert _ajustados(PREFERIDOS, MINIMOS, 500) == MINIMOS
    assert _ajustados(PREFERIDOS, MINIMOS, 0) == MINIMOS


def test_f050_m2_1_una_preferencia_bajo_el_minimo_se_respeta():
    """El usuario puede dejar una columna en 70 px (la manija): no crece."""
    assert _ajustados([80, 210, 560, 320, 190], MINIMOS, 1000) == [
        80, 152, 346, 231, 190]
    assert _ajustados([80, 100, 150, 150, 190], MINIMOS, 300) == [
        80, 100, 150, 150, 190]


def test_f050_m2_1_cada_columna_tiene_su_minimo():
    assert _node("\n".join([
        _const("COLUMNAS"), _const("MINIMO_COLUMNA"),
        "process.stdout.write(JSON.stringify([Object.keys(COLUMNAS), "
        "Object.keys(MINIMO_COLUMNA), Object.keys(COLUMNAS).map((c) => "
        "MINIMO_COLUMNA[c] <= COLUMNAS[c].ancho)]));"])) == [
        ["nombre", "categoria", "asignaciones", "partida", "total"],
        ["nombre", "categoria", "asignaciones", "partida", "total"],
        [True] * 5]


def _sincronizar(anchos: dict, disponible: int, columnas=None) -> dict:
    columnas = columnas or ["nombre", "categoria", "asignaciones", "partida",
                            "total"]
    return _node("\n".join([
        _const("COLUMNAS"), _const("MINIMO_COLUMNA"),
        _funcion("anchosAjustados"), _funcion("sincronizarAnchoTabla"),
        "const state = {columnas: " + json.dumps(columnas) + ", anchos: " +
        json.dumps(anchos) + "};",
        "const ths = state.columnas.map(() => ({style: {}}));",
        "const tabla = {style: {}, parentElement: {clientWidth: " +
        str(disponible) + "}};",
        "const $ = (s) => s === '#tabla' ? tabla : null;",
        ("const document = {querySelectorAll: (s) => s === "
         "'#cabecera-tabla tr:first-child th' ? ths : []};"),
        "sincronizarAnchoTabla();",
        ("process.stdout.write(JSON.stringify({ths: ths.map((t) => "
         "t.style.width), tabla: tabla.style, anchos: state.anchos}));")]))


def test_f050_m2_1_la_tabla_se_ajusta_a_su_panel():
    obs = _sincronizar({}, 1046)
    assert obs["ths"] == ["203px", "140px", "299px", "212px", "190px"]
    assert obs["tabla"] == {"tableLayout": "fixed", "minWidth": "100%",
                            "width": "1044px"}


def test_f050_m2_1_las_preferencias_no_se_tocan():
    """Se ajusta lo que se pinta, no lo guardado: con la ventana ancha
    vuelven los anchos del usuario."""
    obs = _sincronizar({"nombre": 400, "partida": 250}, 1046,
                       ["partida", "nombre", "categoria", "asignaciones",
                        "total"])
    assert obs["anchos"] == {"nombre": 400, "partida": 250}
    assert sum(int(w[:-2]) for w in obs["ths"]) <= 1046
    ancha = _sincronizar({"nombre": 400, "partida": 250}, 3000,
                         ["partida", "nombre", "categoria", "asignaciones",
                          "total"])
    assert ancha["ths"] == ["250px", "400px", "210px", "560px", "190px"]


def test_f050_m2_1_se_reajusta_cuando_cambia_el_panel():
    enlazar = _plano(_funcion("enlazarEventos"))
    assert ("new ResizeObserver(() => sincronizarAnchoTabla())"
            '.observe($("#tabla").parentElement);') in enlazar


# ============== 2 · el cursor se marca igual en las subfilas ============== #
#: `construirFila` REAL con `construirCelda` de mentira (una celda que solo
#: sabe su columna) y un DOM mínimo: lo que se mira son las clases.
FILA = r"""
function clases() { const s = new Set();
  return {add: (c) => s.add(c), contains: (c) => s.has(c), lista: () => [...s]}; }
function construirCelda(t, clave, idx) {
  return {clave, idx, rowSpan: 1, classList: clases()}; }
const document = {createDocumentFragment: () => ({trs: [],
  appendChild(tr) { this.trs.push(tr); }}),
  createElement: () => ({dataset: {}, tds: [], set className(c) {
    c.split(" ").forEach((x) => this.classList.add(x)); },
    classList: clases(), appendChild(td) { this.tds.push(td); },
    addEventListener() {}})};
"""


def _fila(columnas: list[str], n_lineas: int) -> list:
    return _node("\n".join([
        _const("COLUMNAS_POR_LINEA"), FILA, _funcion("construirFila"),
        "const state = {columnas: " + json.dumps(columnas) + ", seleccionIde:"
        " 7, seleccion: new Set(), editandoIde: null};",
        "const t = {ide: 7, activo: true, lineas: " +
        json.dumps([{"obra_ide": i} for i in range(n_lineas)]) + "};",
        ("const frag = construirFila(t);"
         "process.stdout.write(JSON.stringify(frag.trs.map((tr) => ["
         "tr.classList.contains('seleccionada'), tr.tds.map((td) => "
         "[td.clave, td.rowSpan, td.classList.lista().sort().join(' ')])])));"),
    ]))


ORDEN = ["nombre", "categoria", "asignaciones", "partida", "total"]


def test_f050_m2_2_una_barra_a_cada_lado_del_bloque():
    """Con tres obras: la primera columna y la última, una sola vez cada una
    y ocupando las tres subfilas; las tres subfilas, seleccionadas."""
    assert _fila(ORDEN, 3) == [
        [True, [["nombre", 3, "col-primera"], ["categoria", 3, ""],
                ["asignaciones", 1, ""], ["partida", 1, ""],
                ["total", 3, "col-ultima"]]],
        [True, [["asignaciones", 1, ""], ["partida", 1, ""]]],
        [True, [["asignaciones", 1, ""], ["partida", 1, ""]]]]


def test_f050_m2_2_columnas_por_linea_en_los_bordes():
    """Si el usuario pone Obras primera y Partida última, la barra va en la
    celda de cada subfila."""
    filas = _fila(["asignaciones", "nombre", "categoria", "total", "partida"],
                  2)
    assert [[c for c in tds if c[2]] for _, tds in filas] == [
        [["asignaciones", 1, "col-primera"], ["partida", 1, "col-ultima"]],
        [["asignaciones", 1, "col-primera"], ["partida", 1, "col-ultima"]]]


def test_f050_m2_2_sin_carga_una_fila_con_sus_dos_bordes():
    assert _fila(ORDEN, 0) == [[True, [
        ["nombre", 1, "col-primera"], ["categoria", 1, ""],
        ["asignaciones", 1, ""], ["partida", 1, ""],
        ["total", 1, "col-ultima"]]]]


def test_f050_m2_2_css_fondo_en_todas_y_barras_solo_en_los_bordes():
    assert _regla("tr.fila.seleccionada td") == \
        "background: var(--brand-soft);"
    assert _regla("tr.fila.seleccionada td.col-primera") == \
        "box-shadow: inset 3px 0 0 var(--brand);"
    assert _regla("tr.fila.seleccionada td.col-ultima") == \
        "box-shadow: inset -3px 0 0 var(--brand);"
    assert _regla("tr.fila.multi td.col-primera") == \
        "box-shadow: inset 3px 0 0 var(--pv);"
    assert _regla("tr.fila.multi.seleccionada td.col-primera") == \
        "box-shadow: inset 3px 0 0 var(--brand), inset 6px 0 0 var(--pv);"
    assert "td:first-child" not in CSS.split("Selección múltiple")[1].split(
        "tr.fila.inactivo")[0]


# ======== 3 · el selector: al instante, uno solo y el último pedido ======== #
ESCAPE = ("function escapeHtml(t) { return (t == null ? '' : String(t))"
          ".replace(/&/g,'&amp;').replace(/</g,'&lt;')"
          ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }")

#: DOM de mentira con árbol de verdad (`contains` sube por `padre`, `remove`
#: lo quita de su padre) y escuchas de `document` que el escenario dispara
#: con `pulsar(nodo)`; `api` deja cada petición pendiente en `llamadas`.
DOM = r"""
const escuchas = [];
function nodo(tag) {
  const n = {tag, className: "", _html: "", style: {}, dataset: {}, hijos: [],
    _h: {}, padre: null, classList: {toggle() {}, add() {}, contains: () => false},
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = v; this.hijos = []; },
    addEventListener(ev, fn) { this._h[ev] = fn; },
    appendChild(h) { this.hijos.push(h); h.padre = this; return h; },
    querySelector(s) {
      if (s === ".buscar-partida") return this._input || (this._input = nodo("input"));
      if (s === ".lista-partidas") return this._lista || (this._lista = nodo("div"));
      return null; },
    querySelectorAll() { return []; },
    contains(x) { for (let y = x; y; y = y.padre) if (y === this) return true;
      return false; },
    remove() { if (this.padre) {
      this.padre.hijos = this.padre.hijos.filter((h) => h !== this);
      this.padre = null; } },
    focus() {}, scrollIntoView() {}, offsetHeight: 100, value: "",
    isConnected: true,
    getBoundingClientRect() { return this.rect || {top: 10, bottom: 30, left: 10}; }};
  return n;
}
const body = nodo("body");
const document = {createElement: nodo, body,
  addEventListener(t, fn) { escuchas.push([t, fn]); },
  removeEventListener(t, fn) {
    const i = escuchas.findIndex((e) => e[0] === t && e[1] === fn);
    if (i >= 0) escuchas.splice(i, 1); },
  documentElement: {clientHeight: 800, clientWidth: 1200},
  querySelectorAll: () => []};
const window = {addEventListener() {}, removeEventListener() {}};
const pulsar = (target) => escuchas.filter((e) => e[0] === "mousedown")
  .forEach((e) => e[1]({target}));
const paneles = () => body.hijos.filter((h) => h.className === "panel-partida");
const texto = (p) => p.innerHTML +
  (p._lista ? p._lista.hijos.map((h) => h.innerHTML).join("") : "");
const llamadas = [];
function api(url, o) {
  return new Promise((res, rej) => llamadas.push({url, o, res, rej})); }
const toasts = []; function toast(m) { toasts.push(m); }
function aplicarFila() {} async function guardarAhora() {}
const tick = () => new Promise((r) => setTimeout(r, 0));
const resp = (cod) => ({partidas: [{ide: 1, cod, res: "R", mayor: "CI"}],
  partidas_postventa: [], ambito: null, propuesta: null});
const state = {anio: 2026, mes: 9, empresa: 1, editandoIde: null};
"""

SELECTOR = ("normalizar", "filtrarPartidas", "listaSelector", "rotuloOrigen",
            "posicionSugerencias", "clavePartidas", "cerrarSelectorPartida",
            "abrirSelectorPartida", "montarSelectorPartida")


def _escenario(cuerpo: str, extra=(), prefijo: str = "") -> dict:
    return _node("\n".join([
        DOM, prefijo, ESCAPE, _const("selector"),
        *(_funcion(f) for f in (*SELECTOR, *extra)),
        "(async () => { const obs = {};", cuerpo,
        "process.stdout.write(JSON.stringify(obs)); })();"]))


CARGANDO = "Cargando partidas…"


def test_f050_m2_3_se_abre_al_instante_con_cargando():
    """Sin esperar a la API: el panel ya está, con «Cargando partidas…»; al
    llegar la respuesta, ESE panel se llena (no sale otro)."""
    obs = _escenario("""
      const a = nodo("td");
      abrirSelectorPartida(77, 694, false, a);
      obs.al_instante = paneles().map(texto);
      const panel = paneles()[0];
      llamadas[0].res(resp("CI.1.5")); await tick();
      obs.despues = paneles().length; obs.mismo = paneles()[0] === panel;
      obs.lleno = texto(paneles()[0]);
    """)
    assert len(obs["al_instante"]) == 1
    assert CARGANDO in obs["al_instante"][0]
    assert obs["despues"] == 1 and obs["mismo"] is True
    assert "buscar-partida" in obs["lleno"] and "CI.1.5" in obs["lleno"]
    assert CARGANDO not in obs["lleno"]


def test_f050_m2_3_un_segundo_clic_mientras_carga_no_abre_otro():
    obs = _escenario("""
      const a = nodo("td");
      abrirSelectorPartida(77, 694, false, a);
      pulsar(a); abrirSelectorPartida(77, 694, false, a);
      obs.cargando = [paneles().length, llamadas.length];
      llamadas[0].res(resp("CI.1.5")); await tick();
      obs.cargado = [paneles().length, llamadas.length];
      pulsar(a); await abrirSelectorPartida(77, 694, false, a);
      obs.otra_vez = [paneles().length, llamadas.length];
    """)
    assert obs["cargando"] == [1, 1]
    assert obs["cargado"] == [1, 1]
    assert obs["otra_vez"] == [1, 1]          # de la caché, sin otro panel


@pytest.mark.parametrize("orden", ["vieja_despues", "vieja_antes"])
def test_f050_m2_3_solo_pinta_el_ultimo_pedido(orden):
    obs = _escenario("""
      const a = nodo("td"), b = nodo("td");
      abrirSelectorPartida(77, 694, false, a);
      pulsar(b); abrirSelectorPartida(78, 700, false, b);
      const [vieja, nueva] = llamadas;
      if (%s) { vieja.res(resp("VIEJA")); await tick();
                obs.entre = paneles().map(texto); }
      nueva.res(resp("NUEVA")); await tick();
      vieja.res(resp("VIEJA")); await tick();
      obs.fin = paneles().map(texto);
    """ % ("true" if orden == "vieja_antes" else "false"))
    assert len(obs["fin"]) == 1
    assert "NUEVA" in obs["fin"][0] and "VIEJA" not in obs["fin"][0]
    if orden == "vieja_antes":
        assert len(obs["entre"]) == 1 and CARGANDO in obs["entre"][0]


def test_f050_m2_3_cerrado_mientras_carga_no_se_reabre():
    obs = _escenario("""
      const a = nodo("td"), fuera = nodo("div");
      abrirSelectorPartida(77, 694, false, a);
      pulsar(fuera);
      obs.cerrado = [paneles().length, escuchas.length];
      llamadas[0].res(resp("CI.1.5")); await tick();
      obs.tras_respuesta = paneles().length;
      abrirSelectorPartida(77, 694, false, a);
      obs.se_puede_abrir = paneles().map(texto);
    """)
    assert obs["cerrado"] == [0, 0]
    assert obs["tras_respuesta"] == 0
    assert len(obs["se_puede_abrir"]) == 1


def test_f050_m2_3_un_error_cierra_el_panel_y_uno_viejo_calla():
    obs = _escenario("""
      const a = nodo("td"), b = nodo("td");
      abrirSelectorPartida(77, 694, false, a);
      llamadas[0].rej(new Error("transfer caído")); await tick();
      obs.error = [paneles().length, toasts.slice()];
      abrirSelectorPartida(77, 694, false, a);
      pulsar(b); abrirSelectorPartida(78, 700, false, b);
      llamadas[1].rej(new Error("viejo")); await tick();
      obs.viejo = [paneles().map(texto), toasts.slice()];
    """)
    assert obs["error"] == [0, ["transfer caído"]]
    paneles, toasts = obs["viejo"]
    assert len(paneles) == 1 and CARGANDO in paneles[0]
    assert toasts == ["transfer caído"]


# ============== 4 · en el modal, encima y anclado a su línea ============== #
MODAL = r"""
const ov = nodo("div");
ov.classList = {remove() { ov.visible = true; }, add() {}, contains: () => false};
const $ = (s) => s === "#modal-registro" ? ov : null;
"""


def test_f050_m2_4_abrir_el_modal_cierra_el_selector_aunque_cargue():
    """El de la columna Partida que aún cargaba no aparece luego encima del
    modal colgado del cuadrante de detrás."""
    obs = _escenario("""
      const celda = nodo("td");
      abrirSelectorPartida(77, 694, false, celda);
      abrirModal("<h2>Registrar</h2>");
      obs.tras_abrir = [paneles().length, escuchas.length, ov.visible];
      llamadas[0].res(resp("CI.1.5")); await tick();
      obs.tras_respuesta = paneles().length;
      abrirSelectorPartida(77, 694, false, celda); await tick();
      abrirModal("<h2>otra vez</h2>");
      obs.cargado_y_abrir = paneles().length;
    """, extra=("abrirModal",), prefijo=MODAL)
    assert obs["tras_abrir"] == [0, 0, True]
    assert obs["tras_respuesta"] == 0
    assert obs["cargado_y_abrir"] == 0


def test_f050_m2_4_sale_junto_al_boton_del_modal_desde_el_primer_momento():
    obs = _escenario("""
      const boton = nodo("button"); ov.appendChild(boton);
      boton.rect = {top: 400, bottom: 424, left: 300};
      abrirSelectorPartida(77, 694, false, boton, () => {});
      const p = paneles()[0];
      obs.cargando = [p.padre === body, p.style.top, p.style.left];
      llamadas[0].res(resp("CI.1.5")); await tick();
      obs.cargado = [paneles()[0] === p, p.style.top, p.style.left];
    """, prefijo=MODAL)
    assert obs["cargando"] == [True, "428px", "300px"]
    assert obs["cargado"] == [True, "428px", "300px"]


def test_f050_m2_4_el_panel_va_por_encima_del_modal():
    def z(selector):
        return int(re.search(r"z-index:\s*(\d+)", _regla(selector)).group(1))
    assert z(".panel-partida") > z(".modal-overlay")
