# tests/test_f050_t15d_selector.py
"""F-050 · T15d, punto 2 (M2 repetida por el humano, 2026-10-12).

El selector de partida nunca se abre minúsculo (captura `image2`: solo el
buscador, ni botones Todas · CD · CI · CP ni lista). Causa: el panel se
coloca primero con «Cargando partidas…» (unos 34 px) y `recolocar` fija
`max-height` a ese alto; al llenarlo vuelve a medir `offsetHeight`, que ya
está topado por ese `max-height`, y el panel se queda en 34 px para siempre.

Ahora: `recolocar` mide el alto natural (quita el `max-height` antes) y el
panel tiene un alto mínimo útil (`ALTO_UTIL`, buscador + botones + varias
filas): si no cabe debajo y arriba hay más sitio, se abre arriba; si no cabe
en ningún lado, se mete en la ventana (tapando su ancla). Igual en el
cuadrante y en el modal (el mismo `montarSelectorPartida`). `posicionSugerencias`
(F-042) gana un cuarto argumento, `minimo`, que por defecto es 0: sin él,
lo de F-042 no cambia (sus tests, intactos).

El código REAL de `app.js` en `node` con un DOM mínimo de mentira (patrón de
F-042 y T15c). Sin `node` se saltan con su motivo; el reviewer los exige
`passed`. Sin red.
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


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


# ================ la colocación, pura (posicionSugerencias) ================ #
def _posicion(campo: dict, alto: float, ventana: dict, minimo=None) -> dict:
    args = [campo, alto, ventana] + ([] if minimo is None else [minimo])
    return _node("\n".join([
        _funcion("posicionSugerencias"),
        "process.stdout.write(JSON.stringify(posicionSugerencias(" +
        ", ".join(json.dumps(a) for a in args) + ")));"]))


VENTANA = {"alto": 800, "ancho": 1200}


def test_f050_t15d_2_cerca_del_borde_inferior_se_abre_arriba():
    """Aún con «Cargando…» (34 px): debajo quedan 800 - 776 - 4 - 8 = 12 px
    y el mínimo útil (240) no cabe; arriba sí. Abre arriba, pegado al ancla
    por abajo con su alto de ahora, y con sitio para crecer hasta 240."""
    assert _posicion({"top": 740, "bottom": 776, "left": 100}, 34, VENTANA,
                     240) == {"top": 702, "left": 100, "ancho": 430,
                              "altoMax": 240, "haciaArriba": True}


def test_f050_t15d_2_poco_sitio_debajo_ya_cargando_se_abre_arriba():
    """Debajo quedan 100 px (800 - 688 - 4 - 8): caben los 34 de «Cargando…»
    pero no el mínimo útil. Se decide con el mínimo: arriba desde el primer
    momento, sin saltar de abajo a arriba al llenarse (mutante S04)."""
    assert _posicion({"top": 680, "bottom": 688, "left": 100}, 34, VENTANA,
                     240) == {"top": 642, "left": 100, "ancho": 430,
                              "altoMax": 240, "haciaArriba": True}


def test_f050_t15d_2_lleno_y_arriba_crece_hasta_el_sitio_que_hay():
    """Ya con la lista (natural 2000 px): arriba caben 728; ese es su tope."""
    assert _posicion({"top": 740, "bottom": 776, "left": 100}, 2000, VENTANA,
                     240) == {"top": 8, "left": 100, "ancho": 430,
                              "altoMax": 728, "haciaArriba": True}


def test_f050_t15d_2_con_sitio_debajo_sigue_debajo():
    """Debajo caben 240 justos (800 - 548 - 4 - 8): no se da la vuelta, y el
    tope es el mínimo útil aunque ahora mida 34 (para que, al llenarse,
    no se quede en 34)."""
    assert _posicion({"top": 512, "bottom": 548, "left": 100}, 34, VENTANA,
                     240) == {"top": 552, "left": 100, "ancho": 430,
                              "altoMax": 240, "haciaArriba": False}


@pytest.mark.parametrize("campo, top, arriba", [
    ({"top": 100, "bottom": 136, "left": 0}, 52, False),   # más sitio debajo
    ({"top": 200, "bottom": 236, "left": 0}, 8, True),      # más sitio arriba
])
def test_f050_t15d_2_sin_sitio_en_ningun_lado_se_mete_en_la_ventana(
        campo, top, arriba):
    """Ventana de 300 px: ni arriba ni debajo caben 240. El panel tiene sus
    240 igualmente, dentro de la ventana, aunque tape su ancla."""
    pos = _posicion(campo, 2000, {"alto": 300, "ancho": 1200}, 240)
    assert (pos["top"], pos["altoMax"], pos["haciaArriba"]) == (
        top, 240, arriba)
    assert 8 <= pos["top"] and pos["top"] + pos["altoMax"] <= 300 - 8


def test_f050_t15d_2_ventana_mas_baja_que_el_minimo():
    """Ventana de 200 px: el mínimo se queda en lo que cabe (200 - 16)."""
    pos = _posicion({"top": 80, "bottom": 116, "left": 0}, 2000,
                    {"alto": 200, "ancho": 1200}, 240)
    assert (pos["top"], pos["altoMax"]) == (8, 184)


def test_f050_t15d_2_sin_minimo_es_lo_de_f042():
    """Sin el cuarto argumento, idéntico a F-042 (sus casos, también el del
    ancla fuera de la ventana, que no se recoloca)."""
    for campo, alto, ventana in [
            ({"top": 740, "bottom": 776, "left": 100}, 280, VENTANA),
            ({"top": 100, "bottom": 136, "left": 0}, 280,
             {"alto": 300, "ancho": 1200}),
            ({"top": -100, "bottom": -64, "left": 0}, 280, VENTANA),
            ({"top": 0, "bottom": 36, "left": 0}, 280,
             {"alto": 10, "ancho": 1200})]:
        assert _posicion(campo, alto, ventana) == _posicion(
            campo, alto, ventana, 0)
    assert _posicion({"top": -100, "bottom": -64, "left": 0}, 280,
                     VENTANA)["top"] == -60
    # Ventana más baja que los dos márgenes (10 px): F-042 no recoloca
    # (mutante S02: un mínimo negativo no puede activar la recolocación).
    assert _posicion({"top": 0, "bottom": 36, "left": 0}, 280,
                     {"alto": 10, "ancho": 1200})["top"] == -4


# ============ el panel de verdad: montarSelectorPartida en node ============ #
ESCAPE = ("function escapeHtml(t) { return (t == null ? '' : String(t))"
          ".replace(/&/g,'&amp;').replace(/</g,'&lt;')"
          ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }")

#: DOM de mentira cuyo `offsetHeight` es el de un navegador: el alto natural
#: (34 px con «Cargando partidas…»; `natural` cuando ya tiene su lista)
#: TOPADO por el `max-height` que lleve puesto, como en el navegador.
DOM = r"""
const escuchas = [];
function nodo(tag) {
  const n = {tag, className: "", _html: "", style: {}, dataset: {}, hijos: [],
    _h: {}, padre: null, natural: 600,
    classList: {toggle() {}, add() {}, contains: () => false},
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = v; this.hijos = []; },
    get offsetHeight() {
      const nat = this._html.includes("lista-partidas") ? this.natural : 34;
      return Math.min(nat, parseFloat(this.style.maxHeight) || Infinity); },
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
    focus() {}, scrollIntoView() {}, value: "", isConnected: true,
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
const paneles = () => body.hijos.filter((h) => h.className === "panel-partida");
const llamadas = [];
function api(url, o) {
  return new Promise((res, rej) => llamadas.push({url, o, res, rej})); }
function toast() {} function aplicarFila() {} async function guardarAhora() {}
const tick = () => new Promise((r) => setTimeout(r, 0));
const resp = {partidas: [{ide: 1, cod: "CI.1.5", res: "R", mayor: "CI"}],
  partidas_postventa: [], ambito: "CI", propuesta: null};
const state = {anio: 2026, mes: 9, empresa: 1, editandoIde: null};
const ov = nodo("div");
const foto = (p) => [p.style.top, p.style.maxHeight, p.offsetHeight];
"""

SELECTOR = ("normalizar", "filtrarPartidas", "listaSelector", "rotuloOrigen",
            "posicionSugerencias", "clavePartidas", "cerrarSelectorPartida",
            "abrirSelectorPartida", "montarSelectorPartida")


def _escenario(cuerpo: str) -> dict:
    return _node("\n".join([
        DOM, ESCAPE, _const("selector"),
        *(_funcion(f) for f in SELECTOR),
        "(async () => { const obs = {};", cuerpo,
        "process.stdout.write(JSON.stringify(obs)); })();"]))


#: Dónde está el ancla: una celda Partida del cuadrante o el botón de la
#: partida de una línea del modal (cuelga del overlay `ov`).
ANCLA = {
    "cuadrante": 'const ancla = nodo("td");',
    "modal": 'const ancla = nodo("button"); ov.appendChild(ancla);',
}


@pytest.mark.parametrize("donde", ["cuadrante", "modal"])
def test_f050_t15d_2_al_llenarse_no_se_queda_con_el_alto_de_cargando(donde):
    """Con sitio debajo: «Cargando…» mide 34, lleno mide 600 (y caben
    800 - 130 - 4 - 8 = 658). El panel lleno tiene sus 600, no 34."""
    obs = _escenario(ANCLA[donde] + """
      ancla.rect = {top: 100, bottom: 130, left: 50};
      abrirSelectorPartida(77, 694, false, ancla);
      const p = paneles()[0]; obs.cargando = foto(p);
      llamadas[0].res(resp); await tick();
      obs.lleno = foto(p);
    """)
    assert obs["cargando"] == ["134px", "240px", 34]
    assert obs["lleno"] == ["134px", "600px", 600]


@pytest.mark.parametrize("donde", ["cuadrante", "modal"])
def test_f050_t15d_2_cerca_del_borde_inferior_abre_arriba_con_alto_util(donde):
    """La captura: ancla a 30 px del borde inferior. Se abre arriba desde el
    principio y, lleno, con su alto natural (600 caben arriba)."""
    obs = _escenario(ANCLA[donde] + """
      ancla.rect = {top: 740, bottom: 770, left: 50};
      abrirSelectorPartida(77, 694, false, ancla);
      const p = paneles()[0]; obs.cargando = foto(p);
      llamadas[0].res(resp); await tick();
      obs.lleno = foto(p);
    """)
    assert obs["cargando"] == ["702px", "240px", 34]
    assert obs["lleno"] == ["136px", "600px", 600]


def test_f050_t15d_2_lista_larga_en_ventana_baja_al_menos_el_minimo():
    """Ventana de 514 px (la de la captura) y ancla en la última fila: la
    lista larga (2000) se queda en lo que cabe arriba, nunca por debajo del
    mínimo útil."""
    obs = _escenario("""
      document.documentElement.clientHeight = 514;
      const ancla = nodo("td"); ancla.rect = {top: 421, bottom: 467, left: 50};
      abrirSelectorPartida(77, 694, false, ancla);
      const p = paneles()[0]; p.natural = 2000;
      llamadas[0].res(resp); await tick();
      obs.lleno = foto(p);
    """)
    assert obs["lleno"] == ["8px", "409px", 409]


def test_f050_t15d_2_el_alto_util_del_selector():
    """240 px: buscador (≈47), botones (≈31) y unas cinco filas (≈30 cada
    una). Va en `montarSelectorPartida` y llega a `posicionSugerencias`."""
    montar = " ".join(_funcion("montarSelectorPartida").split())
    assert "const ALTO_UTIL = 240;" in montar
    assert 'panel.style.maxHeight = "";' in montar
    assert montar.index('panel.style.maxHeight = "";') < montar.index(
        "panel.offsetHeight")
    assert "}, ALTO_UTIL);" in montar
