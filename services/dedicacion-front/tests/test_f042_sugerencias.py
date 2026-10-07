# tests/test_f042_sugerencias.py
"""F-042 · El desplegable de obras se ve también en la última fila.

Causa (`progress/impl_F-042.md`): el panel `.sugerencias` era `position:
absolute` dentro de la fila del editor, y `.panel { overflow: hidden }` /
`.panel-tabla { overflow-x: auto }` lo recortaban cuando debajo no había más
filas. Plan A (aprobado por el humano el 2026-10-07): el panel cuelga de
`<body>`, es `position: fixed` y se coloca con `getBoundingClientRect()` del
campo; se abre hacia arriba si debajo no cabe.

Tres familias (patrón de `test_f041_filtro_obra.py`):

- **Estáticos** sobre `app.js` y `styles.css`: el panel ya no vive dentro de
  la tabla, y el teclado y la búsqueda no cambian (texto literal de antes).
- **Lógica en node** de `posicionSugerencias` (función pura): abajo/arriba,
  alto, ancho y `left`.
- **Ciclo de vida en node** con un DOM mínimo de prueba: el código REAL de
  `montarAutocompletado`, `colocarSugerencias` y `retirarSugerencias` en la
  última fila (busca, se ve encima del campo y se elige con el teclado), uno
  solo a la vez y sin escuchas ni paneles huérfanos.

Sin `node` se saltan con su motivo; el reviewer los exige `passed`. Sin red ni
BBDD.
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


def _plano(texto: str) -> str:
    return " ".join(texto.split())


def _regla_css(selector: str) -> str:
    m = re.search(rf"^{re.escape(selector)}\s*\{{(.*?)\}}", CSS,
                  re.DOTALL | re.MULTILINE)
    assert m, f"no existe la regla {selector} en styles.css"
    return _plano(m.group(1))


# ============================ ayudante node ============================== #
def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-042 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


def _posicion(campo: dict, alto: float, ventana: dict) -> dict:
    programa = "\n".join([
        _funcion("posicionSugerencias"),
        ("process.stdout.write(JSON.stringify(posicionSugerencias("
         f"{json.dumps(campo)}, {json.dumps(alto)}, {json.dumps(ventana)})));")])
    return _node(programa)


#: DOM mínimo de prueba: lo justo que usan `montarAutocompletado`,
#: `colocarSugerencias` y `retirarSugerencias`. `removeEventListener` solo
#: quita la escucha si coinciden tipo, función y fase (captura), como el
#: navegador.
DOM_DE_PRUEBA = r"""
class El {
  constructor(tag) {
    this.tag = tag; this.className = ""; this.children = []; this.parent = null;
    this.style = {}; this.listeners = {}; this.value = ""; this.rect = null;
    this._html = "";
  }
  get classList() {
    const el = this;
    const lista = () => el.className.split(/\s+/).filter(Boolean);
    const poner = (c, si) => {
      const resto = lista().filter((x) => x !== c);
      el.className = (si ? [...resto, c] : resto).join(" ");
    };
    return {
      contains: (c) => lista().includes(c),
      add: (c) => poner(c, true),
      remove: (c) => poner(c, false),
      toggle: (c, f) => poner(c, f === undefined ? !lista().includes(c) : !!f),
    };
  }
  set innerHTML(v) {
    this._html = v;
    if (v === "") { this.children.forEach((c) => { c.parent = null; }); this.children = []; }
  }
  get innerHTML() { return this._html; }
  appendChild(c) { if (c.parent) c.remove(); c.parent = this; this.children.push(c); return c; }
  remove() {
    if (this.parent) {
      this.parent.children = this.parent.children.filter((x) => x !== this);
      this.parent = null;
    }
  }
  addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); }
  fire(t, key) {
    const ev = { key, preventDefault() {}, stopPropagation() {} };
    (this.listeners[t] || []).forEach((fn) => fn(ev));
  }
  querySelectorAll(sel) { return this.children.filter((x) => x.classList.contains(sel.slice(1))); }
  getBoundingClientRect() { return this.rect; }
  // Alto: 36 px por sugerencia, con el tope de 280 px del CSS y, como en el
  // navegador, el `max-height` que lleve puesto en línea.
  get offsetHeight() {
    return Math.min(280, this.children.length * 36,
                    parseFloat(this.style.maxHeight) || Infinity);
  }
}
var escuchas = [];
var window = {
  addEventListener(t, fn, cap) { escuchas.push({ t, fn, cap: !!cap }); },
  removeEventListener(t, fn, cap) {
    const i = escuchas.findIndex((e) => e.t === t && e.fn === fn && e.cap === !!cap);
    if (i >= 0) escuchas.splice(i, 1);
  },
  fire(t) { escuchas.filter((e) => e.t === t).forEach((e) => e.fn({})); },
};
var document = {
  body: new El("body"),
  documentElement: { clientWidth: 1200, clientHeight: 800 },
  createElement: (t) => new El(t),
};
// Lo que el autocompletado llama fuera de sí mismo: dobles de prueba.
var llamadas = [];
function escapeHtml(t) { return String(t); }
function pintarEditor() { llamadas.push("pintarEditor"); }
function enfocarPct() { llamadas.push("enfocarPct"); }
function programarGuardado() { llamadas.push("programarGuardado"); }
function cerrarEditor() { llamadas.push("cerrarEditor"); }
function totalEdicion() { return { suma: 0 }; }
function obra(ide, cod, descripcion) {
  return { ide, cod, descripcion, activa: true, admite_postventa: false };
}
var state = {
  edicion: [],
  catalogoObras: [
    { obra: obra(1, "0656", "Edificio Arroyo"), pv: false, cod: "0656",
      clave: "0656 edificio arroyo" },
    { obra: obra(2, "0700", "Deposito agua"), pv: false, cod: "0700",
      clave: "0700 deposito agua" },
    { obra: obra(3, "VAR-29", "Arroyo varios"), pv: false, cod: "VAR-29",
      clave: "var-29 arroyo varios" },
    { obra: obra(4, "0701", "Naves Arroyo"), pv: false, cod: "0701",
      clave: "0701 naves arroyo" },
  ],
};
function nuevoCampo(rect) { const i = new El("input"); i.className = "obra-input"; i.rect = rect; return i; }
function nuevoPanel() { const p = new El("div"); p.className = "sugerencias oculto"; return p; }
function escribir(input, texto) { input.value = texto; input.fire("input"); }
function foto(panel) {
  return {
    enBody: panel.parent === document.body,
    oculto: panel.classList.contains("oculto"),
    top: panel.style.top, left: panel.style.left, width: panel.style.width,
    maxHeight: panel.style.maxHeight,
    filas: panel.children.map((c) => c.className),
  };
}
"""

#: Rectángulo del campo de obra en la ÚLTIMA fila: pegado al borde inferior
#: de una ventana de 800 px (el caso del fallo).
ULTIMA = {"top": 752, "bottom": 788, "left": 300}
#: Rectángulo del campo en una fila intermedia: sobra sitio debajo.
INTERMEDIA = {"top": 300, "bottom": 336, "left": 300}


def _ciclo(cuerpo: str) -> object:
    funciones = [_funcion(f) for f in (
        "normalizar", "posicionSugerencias", "colocarSugerencias",
        "retirarSugerencias", "montarAutocompletado")]
    m = re.search(r"^let desmontarSugerencias = null;", JS, re.MULTILINE)
    assert m, "no existe `let desmontarSugerencias = null;` en app.js"
    programa = "\n".join([DOM_DE_PRUEBA, m.group(0), *funciones,
                          "var resultado;", cuerpo,
                          "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


# ================================ R1 ===================================== #
# Reproducido y explicada la causa: el panel ya no depende de un contenedor
# que lo recorte.

def test_f042_r1_el_panel_es_fixed_y_no_absolute():
    regla = _regla_css(".sugerencias")
    assert "position: fixed;" in regla, regla
    assert "position: absolute" not in regla, regla
    # El `top: 40px` relativo a `.anadir` era el que lo dejaba bajo la tabla.
    assert "top: 40px" not in regla, regla


def test_f042_r1_el_panel_no_vive_dentro_de_la_fila():
    editor = _plano(_funcion("pintarEditor"))
    assert "anadir.appendChild(sugerencias)" not in editor
    # Se sigue creando en el editor y se le pasa al autocompletado.
    assert 'sugerencias.className = "sugerencias oculto";' in editor
    assert "montarAutocompletado(inputObra, sugerencias, editor);" in editor
    montar = _plano(_funcion("montarAutocompletado"))
    assert "document.body.appendChild(panel);" in montar
    assert montar.index("retirarSugerencias();") < montar.index(
        "document.body.appendChild(panel);")


def test_f042_r1_cada_repintado_de_la_tabla_retira_el_panel():
    """Cerrar el editor, cambiar de fila o repintar la tabla destruyen el
    campo de obra: su panel (que ya no está dentro) se retira con él."""
    tabla = _plano(_funcion("renderTabla"))
    assert tabla.startswith("function renderTabla() { retirarSugerencias();"), \
        tabla[:80]


# ================================ R2 ===================================== #
# En la última fila (y en cualquiera) se abre, busca y deja elegir.

def test_f042_r2_cabe_debajo():
    assert _posicion({"top": 300, "bottom": 336, "left": 100}, 280,
                     {"alto": 800, "ancho": 1200}) == {
        "top": 340, "left": 100, "ancho": 430, "altoMax": 280,
        "haciaArriba": False}


def test_f042_r2_ultima_fila_se_abre_hacia_arriba():
    # Debajo quedan 800 - 776 - 4 - 8 = 12 px; encima, 740 - 4 - 8 = 728.
    assert _posicion({"top": 740, "bottom": 776, "left": 100}, 280,
                     {"alto": 800, "ancho": 1200}) == {
        "top": 456, "left": 100, "ancho": 430, "altoMax": 280,
        "haciaArriba": True}


def test_f042_r2_si_cabe_justo_sigue_debajo():
    # Debajo quedan exactamente 280 px: cabe, no se da la vuelta.
    pos = _posicion({"top": 472, "bottom": 508, "left": 100}, 280,
                    {"alto": 800, "ancho": 1200})
    assert pos["haciaArriba"] is False
    assert (pos["top"], pos["altoMax"]) == (512, 280)


def test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio():
    ventana = {"alto": 300, "ancho": 1200}
    # Más sitio debajo (152 frente a 88): debajo, con el alto recortado.
    assert _posicion({"top": 100, "bottom": 136, "left": 0}, 280, ventana) == {
        "top": 140, "left": 8, "ancho": 430, "altoMax": 152,
        "haciaArriba": False}
    # Más sitio encima (188 frente a 52): encima, pegado al margen superior.
    assert _posicion({"top": 200, "bottom": 236, "left": 0}, 280, ventana) == {
        "top": 8, "left": 8, "ancho": 430, "altoMax": 188,
        "haciaArriba": True}
    # Empate (120 y 120): se queda debajo.
    pos = _posicion({"top": 132, "bottom": 168, "left": 0}, 280, ventana)
    assert (pos["haciaArriba"], pos["altoMax"]) == (False, 120)


def test_f042_r2_el_alto_nunca_es_negativo():
    pos = _posicion({"top": 0, "bottom": 36, "left": 0}, 280,
                    {"alto": 10, "ancho": 1200})
    assert pos["altoMax"] == 0


def test_f042_r2_ancho_y_left_dentro_de_la_ventana():
    grande = {"alto": 800, "ancho": 1200}
    # Campo cerca del borde derecho: el panel se corre a la izquierda.
    assert _posicion({"top": 300, "bottom": 336, "left": 1000}, 100,
                     grande)["left"] == 1200 - 8 - 430
    # Campo medio oculto por la izquierda (scroll horizontal de la tabla).
    assert _posicion({"top": 300, "bottom": 336, "left": -50}, 100,
                     grande)["left"] == 8
    # Ventana estrecha: el ancho se ajusta a ella, con su margen.
    estrecha = _posicion({"top": 300, "bottom": 336, "left": 50}, 100,
                         {"alto": 800, "ancho": 400})
    assert (estrecha["ancho"], estrecha["left"]) == (384, 8)


def test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado():
    """El caso del fallo, con el código real: en la última fila el panel se
    ve (en `<body>`, encima del campo) y flechas + Enter eligen."""
    res = _ciclo(f"""
      var campo = nuevoCampo({json.dumps(ULTIMA)});
      var panel = nuevoPanel();
      montarAutocompletado(campo, panel, {{}});
      escribir(campo, "ARROYO");
      var abierto = foto(panel);
      campo.fire("keydown", "ArrowDown");
      campo.fire("keydown", "Enter");
      resultado = {{ abierto, elegida: state.edicion.map((l) => l.cod),
                    tras: foto(panel), llamadas }};
    """)
    # 3 sugerencias x 36 px = 108; encima: 752 - 4 - 108 = 640.
    assert res["abierto"] == {
        "enBody": True, "oculto": False, "top": "640px", "left": "300px",
        "width": "430px", "maxHeight": "108px",
        "filas": ["sugerencia activa", "sugerencia", "sugerencia"]}
    assert res["elegida"] == ["VAR-29"]
    assert res["tras"]["oculto"] is True
    assert res["llamadas"] == ["pintarEditor", "enfocarPct", "programarGuardado"]


def test_f042_r2_fila_intermedia_se_ve_debajo():
    res = _ciclo(f"""
      var campo = nuevoCampo({json.dumps(INTERMEDIA)});
      var panel = nuevoPanel();
      montarAutocompletado(campo, panel, {{}});
      escribir(campo, "arroyo");
      resultado = foto(panel);
    """)
    assert (res["enBody"], res["oculto"], res["top"], res["maxHeight"]) == (
        True, False, "340px", "108px")


def test_f042_r2_acompana_al_campo_con_scroll_y_resize():
    res = _ciclo(f"""
      var campo = nuevoCampo({json.dumps(INTERMEDIA)});
      var panel = nuevoPanel();
      montarAutocompletado(campo, panel, {{}});
      escribir(campo, "arroyo");
      campo.rect = {{ top: 100, bottom: 136, left: 250 }};
      window.fire("scroll");
      var trasScroll = foto(panel);
      campo.rect = {{ top: 752, bottom: 788, left: 250 }};
      window.fire("resize");
      var trasResize = foto(panel);
      // Cerrado (Esc), el scroll ya no lo mueve.
      campo.fire("keydown", "Escape");
      campo.rect = {{ top: 10, bottom: 46, left: 0 }};
      window.fire("scroll");
      resultado = {{ trasScroll, trasResize, cerrado: foto(panel) }};
    """)
    assert (res["trasScroll"]["top"], res["trasScroll"]["left"]) == (
        "140px", "250px")
    assert res["trasResize"]["top"] == "640px"
    assert res["cerrado"]["oculto"] is True
    assert res["cerrado"]["top"] == "640px"


def test_f042_r2_al_agrandar_la_ventana_recupera_el_alto():
    """Con la ventana baja el panel se recorta; al agrandarla vuelve a su
    alto natural (se mide sin el `max-height` de la vez anterior).
    Añadido por la campaña de mutación (M18)."""
    res = _ciclo("""
      document.documentElement.clientHeight = 150;
      var campo = nuevoCampo({ top: 40, bottom: 76, left: 300 });
      var panel = nuevoPanel();
      montarAutocompletado(campo, panel, {});
      escribir(campo, "arroyo");
      var baja = foto(panel).maxHeight;
      document.documentElement.clientHeight = 800;
      window.fire("resize");
      resultado = { baja, alta: foto(panel).maxHeight };
    """)
    # Baja: debajo quedan 150 - 76 - 4 - 8 = 62 px. Alta: 3 x 36 = 108.
    assert res == {"baja": "62px", "alta": "108px"}


def test_f042_r2_scroll_en_captura_para_el_de_la_tabla():
    """El scroll de `.panel-tabla` no burbujea: solo llega a `window` en
    fase de captura."""
    res = _ciclo(f"""
      montarAutocompletado(nuevoCampo({json.dumps(INTERMEDIA)}), nuevoPanel(), {{}});
      resultado = escuchas.map((e) => [e.t, e.cap]);
    """)
    assert sorted(res) == [["resize", False], ["scroll", True]]


def test_f042_r2_un_solo_panel_y_sin_huerfanos():
    """Repintar el editor monta un panel nuevo y retira el anterior;
    `retirarSugerencias` (renderTabla, cerrar el editor) no deja ni panel ni
    escuchas."""
    res = _ciclo(f"""
      var p1 = nuevoPanel(), p2 = nuevoPanel();
      montarAutocompletado(nuevoCampo({json.dumps(INTERMEDIA)}), p1, {{}});
      var trasUno = [document.body.children.length, escuchas.length];
      montarAutocompletado(nuevoCampo({json.dumps(ULTIMA)}), p2, {{}});
      var trasDos = [document.body.children.length, escuchas.length,
                     document.body.children[0] === p2, p1.parent === null];
      retirarSugerencias();
      var trasRetirar = [document.body.children.length, escuchas.length];
      retirarSugerencias();
      resultado = {{ trasUno, trasDos, trasRetirar,
                    otraVez: [document.body.children.length, escuchas.length] }};
    """)
    assert res == {"trasUno": [1, 2], "trasDos": [1, 2, True, True],
                   "trasRetirar": [0, 0], "otraVez": [0, 0]}


# ================================ R3 ===================================== #
# Sin cambios en el teclado ni en la búsqueda (texto literal anterior a F-042).

#: Teclado y blur de `montarAutocompletado` antes de F-042: idénticos.
TECLADO_ANTES = (
    'input.addEventListener("input", refrescar); '
    'input.addEventListener("focus", refrescar); '
    'input.addEventListener("keydown", (ev) => { '
    'const abierto = !panel.classList.contains("oculto"); '
    'if (ev.key === "ArrowDown" && abierto) { ev.preventDefault(); '
    "activa = Math.min(activa + 1, candidatas.length - 1); marcarActiva(); } "
    'else if (ev.key === "ArrowUp" && abierto) { ev.preventDefault(); '
    "activa = Math.max(activa - 1, 0); marcarActiva(); } "
    'else if (ev.key === "Enter") { ev.preventDefault(); '
    "if (abierto && activa >= 0) elegir(candidatas[activa]); } "
    'else if (ev.key === "Escape") { if (abierto) { '
    'panel.classList.add("oculto"); ev.stopPropagation(); } '
    "else { cerrarEditor(); } } }); "
    'input.addEventListener("blur", () => { '
    'setTimeout(() => panel.classList.add("oculto"), 150); }); }')

#: Búsqueda de `refrescar` antes de F-042, hasta mostrar u ocultar el panel.
BUSQUEDA_ANTES = (
    "const refrescar = () => { const q = normalizar(input.value); "
    "candidatas = state.catalogoObras .filter((e) => !q || "
    "e.clave.includes(q)) .slice(0, 14); "
    "activa = candidatas.length ? 0 : -1; panel.innerHTML = \"\"; "
    "candidatas.forEach((e, i) => { const fila = "
    'document.createElement("div"); fila.className = "sugerencia" + '
    '(i === activa ? " activa" : "") + (e.pv ? " es-pv" : ""); '
    "fila.innerHTML = `<span class=\"cod\">${escapeHtml(e.cod)}</span>` + "
    "`<span class=\"desc\">${escapeHtml(e.obra.descripcion)}</span>`; "
    'fila.addEventListener("mousedown", (ev) => { ev.preventDefault(); '
    "elegir(e); }); panel.appendChild(fila); }); "
    'panel.classList.toggle("oculto", !q || candidatas.length === 0); ')


def test_f042_r3_teclado_identico():
    assert _plano(_funcion("montarAutocompletado")).endswith(TECLADO_ANTES)


def test_f042_r3_busqueda_identica_y_luego_se_coloca():
    montar = _plano(_funcion("montarAutocompletado"))
    assert BUSQUEDA_ANTES + "colocarSugerencias(input, panel); };" in montar


def test_f042_r3_la_secuencia_pct_enter_obra_no_cambia():
    """«% Enter obra Enter»: Enter en el porcentaje sigue llevando al campo
    de obra (no se tocó `chipEditable`)."""
    chip = _plano(_funcion("chipEditable"))
    assert ('pct.addEventListener("keydown", (ev) => { if (ev.key === "Enter") '
            "{ ev.preventDefault(); pct.blur(); const inputObra = "
            'editor.querySelector(".obra-input"); if (inputObra) '
            "inputObra.focus(); } });") in chip
