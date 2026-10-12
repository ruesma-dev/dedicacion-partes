# tests/test_f050_t15e_sombreado.py
"""F-050 · T15e, observación 1 de la review 5 (2026-10-12).

Con el ratón quieto sobre un bloque que se repinta (↑ ↓, guardar, editar),
el bloque nuevo no salía sombreado hasta mover el ratón: el sombreado de
T15d lo ponen `mouseenter`/`mouseleave`, y el navegador no los manda a una
`<tr>` recién puesta bajo un ratón quieto (el `:hover` de antes sí se
recalculaba solo).

Ahora `construirFila` apunta en `state` el bloque bajo el ratón
(`ratonIde`, `resaltadas`): si se repinta ese trabajador, sale ya sombreado;
al entrar en otro bloque se apaga el que hubiera (el repintado puede no
recibir nunca su `mouseleave`), al salir se apaga el que haya y, al salir
de la tabla (`#cuerpo`), también.

El código REAL de `construirFila` y `enlazarEventos` en `node` con un DOM
mínimo de mentira (patrón de T15d). Sin `node` se saltan con su motivo; el
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


def _const(nombre: str) -> str:
    m = re.search(rf"^const {nombre} = .*?;$", JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe `const {nombre}` en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30)
    assert salida.returncode == 0, next(
        (ln for ln in salida.stderr.splitlines() if "Error" in ln), salida.stderr)
    return json.loads(salida.stdout)


#: `construirFila` REAL con `construirCelda` de mentira; cada `<tr>` apunta
#: sus escuchas (`disparar(tr, "mouseenter")`). `state` con los campos de
#: verdad (`ratonIde`, `resaltadas`), sacados del `state` de `app.js`.
FILA = r"""
function clases() { const s = new Set();
  return {add: (c) => s.add(c), remove: (c) => s.delete(c),
          contains: (c) => s.has(c)}; }
function construirCelda(t, clave, idx) {
  return {clave, idx, rowSpan: 1, classList: clases()}; }
const document = {createDocumentFragment: () => ({trs: [],
  appendChild(tr) { this.trs.push(tr); }}),
  createElement: () => ({dataset: {}, tds: [], _h: {}, set className(c) {
    c.split(" ").forEach((x) => this.classList.add(x)); },
    classList: clases(), appendChild(td) { this.tds.push(td); },
    addEventListener(ev, fn) { this._h[ev] = fn; }}),
  addEventListener() {}};
const disparar = (tr, ev) => tr._h[ev] && tr._h[ev]({target: tr});
const bloque = (ide, n) => construirFila({ide, activo: true,
  lineas: Array.from({length: n}, (_, i) => ({obra_ide: i}))}).trs;
const marcadas = (trs) => trs.map((tr) => tr.classList.contains("resaltada"));
"""

#: Los campos del `state` de `app.js` que usa el sombreado, tal cual.
CAMPOS = ("columnas", "seleccionIde", "seleccion", "editandoIde", "ratonIde",
          "resaltadas")


def _estado() -> str:
    m = re.search(r"^const state = \{(.*?)^\};", JS, re.DOTALL | re.MULTILINE)
    assert m, "no existe `const state` en app.js"
    lineas = [ln for ln in m.group(1).splitlines()
              if re.match(rf"\s*({'|'.join(CAMPOS)}):", ln)]
    return "const state = {" + "\n".join(lineas) + "};"


def _escenario(cuerpo: str, extra: str = "") -> dict:
    return _node("\n".join([
        _const("COLUMNAS_POR_LINEA"), _const("ORDEN_COLUMNAS_DEFECTO"),
        _estado(), FILA, extra, _funcion("construirFila"),
        "const obs = {};", cuerpo,
        "process.stdout.write(JSON.stringify(obs));"]))


def test_f050_t15e_el_estado_trae_el_bloque_bajo_el_raton():
    """`state` arranca sin bloque bajo el ratón."""
    obs = _escenario("obs.r = [state.ratonIde, state.resaltadas];")
    assert obs == {"r": [None, []]}


def test_f050_t15e_repintado_con_el_raton_quieto_sale_sombreado():
    """Ratón en la 2.ª subfila del 7 y el 7 se repinta (sin moverlo): el
    bloque nuevo sale sombreado entero; el de otro trabajador, no."""
    obs = _escenario("""
      const a = bloque(7, 3); disparar(a[1], "mouseenter");
      const b = bloque(7, 2), c = bloque(8, 2);
      obs.nuevo = marcadas(b); obs.otro = marcadas(c);
    """)
    assert obs == {"nuevo": [True, True], "otro": [False, False]}


def test_f050_t15e_repintado_y_luego_otro_bloque_apaga_el_repintado():
    """Tras el repintado el navegador puede no mandar `mouseleave` al bloque
    nuevo: al entrar el ratón en otro trabajador, el repintado se apaga."""
    obs = _escenario("""
      const a = bloque(7, 3); disparar(a[0], "mouseenter");
      const b = bloque(7, 3), c = bloque(8, 2);
      disparar(c[1], "mouseenter");
      obs.b = marcadas(b); obs.c = marcadas(c); obs.ide = state.ratonIde;
    """)
    assert obs == {"b": [False, False, False], "c": [True, True], "ide": 8}


def test_f050_t15e_salir_de_la_fila_vieja_apaga_la_repintada():
    """Si el navegador manda el `mouseleave` a la `<tr>` vieja (ya fuera del
    DOM), se apaga el bloque repintado y otro repintado ya no lo sombrea."""
    obs = _escenario("""
      const a = bloque(7, 3); disparar(a[2], "mouseenter");
      const b = bloque(7, 3); disparar(a[2], "mouseleave");
      obs.b = marcadas(b); obs.estado = [state.ratonIde, state.resaltadas.length];
      obs.otra = marcadas(bloque(7, 3));
    """)
    assert obs == {"b": [False, False, False], "estado": [None, 0],
                   "otra": [False, False, False]}


def test_f050_t15e_sin_repintar_lo_de_t15d_sigue_igual():
    """Entrar, cambiar de subfila y de trabajador, salir: como en T15d, y al
    salir no queda ningún bloque apuntado."""
    obs = _escenario("""
      const a = bloque(7, 2), c = bloque(8, 2);
      disparar(a[0], "mouseenter"); disparar(a[0], "mouseleave");
      disparar(a[1], "mouseenter"); obs.a = marcadas(a);
      disparar(a[1], "mouseleave"); disparar(c[0], "mouseenter");
      obs.a2 = marcadas(a); obs.c = marcadas(c);
      disparar(c[0], "mouseleave");
      obs.fin = [marcadas(c), state.ratonIde, state.resaltadas.length];
    """)
    assert obs == {"a": [True, True], "a2": [False, False], "c": [True, True],
                   "fin": [[False, False], None, 0]}


#: `enlazarEventos` REAL con `$` de mentira que apunta sus escuchas.
EVENTOS = r"""
const escuchas = {};
const $ = (s) => ({addEventListener(ev, fn) { escuchas[s + " " + ev] = fn; },
  parentElement: {}});
const window = {addEventListener() {}};
class ResizeObserver { observe() {} }
function teclas() {} function sincronizar() {}
function copiarMesAnterior() {} function abrirCompletar() {}
"""


def test_f050_t15e_salir_de_la_tabla_apaga_el_bloque():
    """El ratón sale de la tabla desde un bloque repintado que nunca recibió
    `mouseenter` (ni recibirá su `mouseleave`): `#cuerpo` lo apaga."""
    obs = _escenario("""
      enlazarEventos();
      const a = bloque(7, 3); disparar(a[1], "mouseenter");
      const b = bloque(7, 3);
      escuchas["#cuerpo mouseleave"]({});
      obs.b = marcadas(b); obs.estado = [state.ratonIde, state.resaltadas.length];
    """, extra=EVENTOS + _funcion("enlazarEventos"))
    assert obs == {"b": [False, False, False], "estado": [None, 0]}
