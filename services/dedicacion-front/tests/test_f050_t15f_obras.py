# tests/test_f050_t15f_obras.py
"""F-050 · T15f, punto 1 (M2 del humano, 2026-10-14).

Los dos desplegables de obras cortaban en 14 (`.slice(0, 14)`, de F-042 y
F-029): el del editor («Añadir obra o Postv-…») y el de «Completar al
100 %». Ahora salen TODAS las que casan, con su alto máximo y scroll propio,
y ↑ ↓ mantienen visible la activa. Lección de T15e: al recolocar el panel
del editor no se pierde su desplazamiento (medir sin `max-height` lo
recorta) y el `scroll` de la propia lista (la rueda) no lo recoloca. El de
«Completar» va dentro de su modal (sin «arriba»): al repintar conserva el
desplazamiento y la activa se ve.

El código REAL de `montarAutocompletado` (con `colocarSugerencias`) y de
`montarDialogoCompletar` (con `candidatasDestino`) en `node`, con un DOM
mínimo de mentira que, como el navegador, recorta el `scrollTop` al alto
que la lista tenga en ese momento. Sin `node` se saltan con su motivo; el
reviewer los exige `passed`. Sin red.
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


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=False)
    assert salida.returncode == 0, next(
        (ln for ln in salida.stderr.splitlines() if "Error" in ln), salida.stderr)
    return json.loads(salida.stdout)


#: DOM de mentira. Cada fila mide 36 px; una lista enseña
#: min(tope del CSS, filas × 36, su `max-height` en línea). Como el
#: navegador, el `scrollTop` se recorta a lo que la lista puede desplazarse
#: AHORA (al ponerlo, al leerlo y al medir su alto) y lo recortado no vuelve.
DOM = r"""
const FILA = 36;
class El {
  constructor(tag) {
    this.tag = tag; this.className = ""; this.children = []; this.parent = null;
    this.style = {}; this.listeners = {}; this.value = ""; this.rect = null;
    this._html = ""; this._scroll = 0; this.tope = 0; this.medidas = 0;
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
    if (v === "") {
      this.children.forEach((c) => { c.parent = null; });
      this.children = [];
      this._recortar();
    }
  }
  get innerHTML() { return this._html; }
  appendChild(c) { if (c.parent) c.remove(); c.parent = this; this.children.push(c); return c; }
  remove() {
    if (this.parent) {
      this.parent.children = this.parent.children.filter((x) => x !== this);
      this.parent = null;
    }
  }
  contains(n) { for (let x = n; x; x = x.parent) if (x === this) return true; return false; }
  addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); }
  fire(t, key) {
    const ev = { type: t, key, target: this, preventDefault() {}, stopPropagation() {} };
    (this.listeners[t] || []).forEach((fn) => fn(ev));
  }
  focus() {}
  querySelectorAll(sel) { return this.children.filter((x) => x.classList.contains(sel.slice(1))); }
  getBoundingClientRect() { this.medidas += 1; return this.rect; }
  // Alto visible de una lista (las filas, 36 px).
  _vista() {
    if (!this.tope) return FILA;
    return Math.min(this.tope, this.children.length * FILA,
                    parseFloat(this.style.maxHeight) || Infinity);
  }
  _recortar() {
    const max = Math.max(0, this.children.length * FILA - this._vista());
    this._scroll = Math.max(0, Math.min(this._scroll, max));
  }
  get offsetHeight() { if (this.tope) this._recortar(); return this._vista(); }
  get clientHeight() { return this.offsetHeight; }
  get offsetTop() { return this.parent ? this.parent.children.indexOf(this) * FILA : 0; }
  get scrollTop() { this._recortar(); return this._scroll; }
  set scrollTop(v) { this._scroll = v; this._recortar(); }
  // Solo el modal de «Completar» lo usa (el editor, no: el DOM de F-042 no
  // lo tiene).
  scrollIntoView(opc) {
    const p = this.parent, top = this.offsetTop, vista = p.offsetHeight;
    if (!opc || opc.block !== "nearest") throw new Error("scrollIntoView sin nearest");
    if (top < p.scrollTop) p.scrollTop = top;
    else if (top + FILA > p.scrollTop + vista) p.scrollTop = top + FILA - vista;
  }
}
var escuchas = [];
var window = {
  addEventListener(t, fn, cap) { escuchas.push({ t, fn, cap: !!cap }); },
  removeEventListener(t, fn, cap) {
    const i = escuchas.findIndex((e) => e.t === t && e.fn === fn && e.cap === !!cap);
    if (i >= 0) escuchas.splice(i, 1);
  },
  fire(t, target) { escuchas.filter((e) => e.t === t).forEach((e) => e.fn({ type: t, target })); },
};
var document = {
  body: new El("body"),
  documentElement: { clientWidth: 1200, clientHeight: 800 },
  createElement: (t) => new El(t),
};
function escapeHtml(t) { return String(t); }
var llamadas = [];
function pintarEditor() { llamadas.push("pintarEditor"); }
function enfocarPct() { llamadas.push("enfocarPct"); }
function programarGuardado() { llamadas.push("programarGuardado"); }
function cerrarEditor() { llamadas.push("cerrarEditor"); }
function cerrarModal() { llamadas.push("cerrarModal"); }
function lanzarCompletar(e) { llamadas.push("lanzarCompletar " + e.cod); return Promise.resolve(); }
function totalEdicion() { return { suma: 0 }; }
// 40 obras que casan con «0» (0600-0639) y una que no.
var state = { edicion: [], filtrosCol: {}, catalogoObras: [] };
for (let i = 0; i < 40; i++) {
  const cod = "06" + String(i).padStart(2, "0");
  state.catalogoObras.push({ obra: { ide: i + 1, cod, descripcion: "Obra " + i,
    activa: true, admite_postventa: false }, pv: false, cod, clave: cod + " obra " + i });
}
state.catalogoObras.push({ obra: { ide: 99, cod: "VAR-29", descripcion: "Varios",
  activa: true, admite_postventa: false }, pv: false, cod: "VAR-29", clave: "var-29 varios" });
"""

#: Editor: panel con el tope de 280 px del CSS de `.sugerencias`.
EDITOR = r"""
function campo(rect) { const i = new El("input"); i.rect = rect; return i; }
function panelObras() { const p = new El("div"); p.className = "sugerencias oculto"; p.tope = 280; return p; }
function escribir(input, texto) { input.value = texto; input.fire("input"); }
function activa(panel) { return panel.children.findIndex((c) => c.classList.contains("activa")); }
function seVe(panel) {
  const i = activa(panel), top = i * FILA;
  return top >= panel.scrollTop && top + FILA <= panel.scrollTop + panel.offsetHeight;
}
"""


def _editor(cuerpo: str) -> object:
    funciones = [_funcion(f) for f in (
        "normalizar", "posicionSugerencias", "colocarSugerencias",
        "retirarSugerencias", "montarAutocompletado")]
    return _node("\n".join([DOM, EDITOR, "let desmontarSugerencias = null;",
                            *funciones, "var resultado;", cuerpo,
                            "process.stdout.write(JSON.stringify(resultado));"]))


#: Campo a media ventana (800 px): debajo caben los 280 px.
MEDIA = {"top": 300, "bottom": 336, "left": 300}
#: Campo con poco sitio (ventana de 450 px): debajo 202 px, encima 188.
BAJA = {"top": 200, "bottom": 236, "left": 300}
#: Campo en la última fila de una ventana de 800 px.
ULTIMA = {"top": 752, "bottom": 788, "left": 300}


def test_f050_t15f_1_editor_salen_todas_las_obras_que_casan():
    res = _editor(f"""
      var c = campo({json.dumps(MEDIA)});
      var q = panelObras();
      montarAutocompletado(c, q, {{}});
      escribir(c, "0");
      resultado = [q.children.length, q.style.maxHeight, q.classList.contains("oculto")];
    """)
    assert res == [40, "280px", False]


def test_f050_t15f_1_editor_flechas_mantienen_visible_la_activa():
    res = _editor(f"""
      var c = campo({json.dumps(MEDIA)}), p = panelObras();
      montarAutocompletado(c, p, {{}});
      escribir(c, "0");
      for (let i = 0; i < 25; i++) c.fire("keydown", "ArrowDown");
      var bajando = [activa(p), seVe(p), p.scrollTop];
      for (let i = 0; i < 10; i++) c.fire("keydown", "ArrowUp");
      var subiendo = [activa(p), seVe(p), p.scrollTop];
      c.fire("keydown", "Enter");
      resultado = {{ bajando, subiendo, elegida: state.edicion.map((l) => l.cod) }};
    """)
    # Fila 25: 900-936 px; vista de 280 -> scrollTop 656. Fila 15: 540.
    assert res == {"bajando": [25, True, 656], "subiendo": [15, True, 540],
                   "elegida": ["0615"]}


def test_f050_t15f_1_editor_la_rueda_no_recoloca_ni_pierde_el_sitio():
    res = _editor(f"""
      document.documentElement.clientHeight = 450;
      var c = campo({json.dumps(BAJA)}), p = panelObras();
      montarAutocompletado(c, p, {{}});
      escribir(c, "0");
      var antes = [p.style.top, p.style.maxHeight, c.medidas];
      p.scrollTop = 99999;                 // la rueda, hasta abajo
      window.fire("scroll", p.children[3]);
      resultado = {{ antes, despues: [p.style.top, p.style.maxHeight, c.medidas],
                    scrollTop: p.scrollTop }};
    """)
    # Debajo: 450 - 236 - 4 - 8 = 202 px; 40 x 36 - 202 = 1238.
    assert res["antes"][:2] == ["240px", "202px"]
    assert res["despues"] == res["antes"]
    assert res["scrollTop"] == 1238


def test_f050_t15f_1_editor_recolocar_conserva_el_desplazamiento():
    res = _editor(f"""
      document.documentElement.clientHeight = 450;
      var c = campo({json.dumps(BAJA)}), p = panelObras();
      montarAutocompletado(c, p, {{}});
      escribir(c, "0");
      p.scrollTop = 99999;
      window.fire("resize");
      var trasResize = [p.scrollTop, p.style.maxHeight];
      p.scrollTop = 700;
      window.fire("scroll", document);     // scroll de la página
      resultado = {{ trasResize, trasPagina: [p.scrollTop, c.medidas > 2] }};
    """)
    assert res == {"trasResize": [1238, "202px"], "trasPagina": [700, True]}


def test_f050_t15f_1_editor_se_abre_arriba_si_no_cabe_debajo():
    res = _editor(f"""
      var c = campo({json.dumps(ULTIMA)}), p = panelObras();
      montarAutocompletado(c, p, {{}});
      escribir(c, "0");
      c.fire("keydown", "ArrowUp");
      resultado = [p.style.top, p.style.maxHeight, p.children.length, activa(p), seVe(p)];
    """)
    # Encima: 752 - 4 - 280 = 468.
    assert res == ["468px", "280px", 40, 0, True]


# ====================== «Completar al 100 %» (F-029) ====================== #
COMPLETAR = r"""
var nodos = {};
["#modal-registro .modal", "#completar-obra", "#completar-candidatas",
 "#completar-elegida", "#btn-completar-cancelar", "#btn-completar-confirmar"]
  .forEach((s) => { nodos[s] = new El("div"); });
nodos["#completar-candidatas"].tope = 220;      // max-height del CSS
function $(s) { return nodos[s] || null; }
var input = nodos["#completar-obra"], lista = nodos["#completar-candidatas"];
function activa() { return lista.children.findIndex((c) => c.classList.contains("activa")); }
function seVe() {
  const i = activa(), top = i * FILA;
  return top >= lista.scrollTop && top + FILA <= lista.scrollTop + lista.offsetHeight;
}
function escribir(texto) { input.value = texto; input.fire("input"); }
"""


def _completar(cuerpo: str) -> object:
    funciones = [_funcion(f) for f in (
        "normalizar", "candidatasDestino", "montarDialogoCompletar")]
    return _node("\n".join([DOM, COMPLETAR, *funciones, "var resultado;",
                            "montarDialogoCompletar([{ide: 1}]);", cuerpo,
                            "process.stdout.write(JSON.stringify(resultado));"]))


def test_f050_t15f_1_completar_salen_todas_las_obras_que_casan():
    res = _completar("""
      escribir("0");
      resultado = [lista.children.length, activa(), lista.scrollTop];
    """)
    assert res == [40, 0, 0]


def test_f050_t15f_1_completar_flechas_mantienen_visible_la_activa():
    res = _completar("""
      escribir("0");
      for (let i = 0; i < 25; i++) input.fire("keydown", "ArrowDown");
      var bajando = [activa(), seVe(), lista.scrollTop];
      for (let i = 0; i < 10; i++) input.fire("keydown", "ArrowUp");
      resultado = { bajando, subiendo: [activa(), seVe(), lista.scrollTop],
                    elegida: nodos["#completar-elegida"].innerHTML };
    """)
    # Fila 25: 900-936 px; vista de 220 -> scrollTop 716. Fila 15: 540.
    assert res == {"bajando": [25, True, 716], "subiendo": [15, True, 540],
                   "elegida": "Destino: <strong>0615</strong> · Obra 15"}


def test_f050_t15f_1_completar_clic_conserva_el_desplazamiento():
    res = _completar("""
      escribir("0");
      lista.scrollTop = 600;                // la rueda
      lista.children[20].fire("mousedown");
      var clic = [activa(), seVe(), lista.scrollTop];
      escribir("06");                       // otra búsqueda: arriba del todo
      resultado = { clic, otra: [activa(), lista.scrollTop] };
    """)
    # La fila 20 (720-756) ya se ve entre 600 y 820: no se mueve nada.
    assert res == {"clic": [20, True, 600], "otra": [0, 0]}
