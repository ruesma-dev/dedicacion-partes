# tests/test_f050_t15d_sombreado.py
"""F-050 · T15d, punto 1 (M2 repetida por el humano, 2026-10-12).

Con subfilas, el sombreado de la fila bajo el ratón cubre TODO el bloque del
trabajador: todas sus subfilas y todas sus columnas, también las celdas con
`rowSpan`. Antes, con `tr.fila:hover td`, solo se sombreaba la `<tr>` bajo el
ratón: en la primera subfila salían todas las columnas (las de `rowSpan`
cuelgan de ella) y en las demás solo Obras y Partida (captura `image1`, color
medido en píxel: `#f8f4f5`, el del hover; la selección `#f7eaee` ya cubría el
bloque desde T15c y no cambia).

El código REAL de `construirFila` en `node` con un DOM mínimo de mentira
(patrón de T15c); el CSS, estático. Sin `node` se saltan con su motivo; el
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


#: `construirFila` REAL con `construirCelda` de mentira y un DOM mínimo que
#: apunta las escuchas de cada `<tr>` (`disparar(tr, "mouseenter")`) y cuyas
#: clases se pueden quitar.
FILA = r"""
function clases() { const s = new Set();
  return {add: (c) => s.add(c), remove: (c) => s.delete(c),
          contains: (c) => s.has(c), lista: () => [...s]}; }
function construirCelda(t, clave, idx) {
  return {clave, idx, rowSpan: 1, classList: clases()}; }
const document = {createDocumentFragment: () => ({trs: [],
  appendChild(tr) { this.trs.push(tr); }}),
  createElement: () => ({dataset: {}, tds: [], _h: {}, set className(c) {
    c.split(" ").forEach((x) => this.classList.add(x)); },
    classList: clases(), appendChild(td) { this.tds.push(td); },
    addEventListener(ev, fn) { this._h[ev] = fn; }})};
const disparar = (tr, ev) => tr._h[ev] && tr._h[ev]({target: tr});
const state = {columnas: ["nombre", "categoria", "asignaciones", "partida",
  "total"], seleccionIde: null, seleccion: new Set(), editandoIde: null};
const bloque = (ide, n) => construirFila({ide, activo: true,
  lineas: Array.from({length: n}, (_, i) => ({obra_ide: i}))}).trs;
const marcadas = (trs) => trs.map((tr) => tr.classList.contains("resaltada"));
"""


def _escenario(cuerpo: str) -> dict:
    return _node("\n".join([
        _const("COLUMNAS_POR_LINEA"), FILA, _funcion("construirFila"),
        "const obs = {};", cuerpo,
        "process.stdout.write(JSON.stringify(obs));"]))


def test_f050_t15d_1_el_raton_en_cualquier_subfila_sombrea_el_bloque():
    """Ratón en la tercera subfila (la captura: Obras y Partida solas):
    se marcan las tres; al salir, ninguna."""
    obs = _escenario("""
      const a = bloque(7, 3);
      disparar(a[2], "mouseenter"); obs.dentro = marcadas(a);
      disparar(a[2], "mouseleave"); obs.fuera = marcadas(a);
    """)
    assert obs == {"dentro": [True, True, True],
                   "fuera": [False, False, False]}


def test_f050_t15d_1_de_una_subfila_a_otra_sigue_el_bloque_entero():
    """Bajar de la primera a la segunda subfila (sale de una, entra en otra):
    el bloque sigue sombreado entero."""
    obs = _escenario("""
      const a = bloque(7, 3);
      disparar(a[0], "mouseenter"); disparar(a[0], "mouseleave");
      disparar(a[1], "mouseenter"); obs.segunda = marcadas(a);
      disparar(a[1], "mouseleave"); disparar(a[2], "mouseenter");
      obs.tercera = marcadas(a);
    """)
    assert obs == {"segunda": [True, True, True],
                   "tercera": [True, True, True]}


def test_f050_t15d_1_solo_su_bloque_no_el_de_otro_trabajador():
    obs = _escenario("""
      const a = bloque(7, 2), b = bloque(8, 3);
      disparar(b[1], "mouseenter"); obs.a = marcadas(a); obs.b = marcadas(b);
      disparar(b[1], "mouseleave"); disparar(a[0], "mouseenter");
      obs.a2 = marcadas(a); obs.b2 = marcadas(b);
    """)
    assert obs == {"a": [False, False], "b": [True, True, True],
                   "a2": [True, True], "b2": [False, False, False]}


def test_f050_t15d_1_sin_carga_la_fila_sola():
    obs = _escenario("""
      const a = bloque(7, 0);
      disparar(a[0], "mouseenter"); obs.dentro = marcadas(a);
      disparar(a[0], "mouseleave"); obs.fuera = marcadas(a);
    """)
    assert obs == {"dentro": [True], "fuera": [False]}


def test_f050_t15d_1_css_el_sombreado_es_del_bloque_no_de_la_tr():
    """El color del hover va con la clase del bloque; `tr.fila:hover td`
    (una `<tr>` sola) desaparece."""
    assert _regla("tr.fila.resaltada td") == "background: #f8f4f5;"
    assert "tr.fila:hover" not in CSS


def test_f050_t15d_1_css_cursor_y_seleccion_multiple_siguen_mandando():
    """Misma especificidad que `.seleccionada`, `.editando` y `.multi`: va
    ANTES, así que el cursor (con sus barras de T15c), el editor y la
    selección múltiple se siguen viendo con el ratón encima."""
    pos = CSS.index("tr.fila.resaltada td")
    for despues in ("tr.fila.seleccionada td {", "tr.fila.editando td {",
                    "tr.fila.multi td {"):
        assert pos < CSS.index(despues), despues
    assert _regla("tr.fila.seleccionada td") == \
        "background: var(--brand-soft);"
    assert _regla("tr.fila.multi td") == "background: var(--pv-soft);"
