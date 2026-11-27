# tests/test_f078_paquete_front.py
"""F-078 · El botón «Registrar en Sigrid» registra un paquete.

`#btn-registro` deja de pedir el mes entero: con 2 o más seleccionados
visibles registra esos; con 0 o 1 (el cursor cuenta como 1), todos los
visibles con los filtros. Nunca un oculto. El front solo elige a quién: manda
los `ide` (`trabajador_ides`) y la api decide qué líneas van.

Dos familias, en node con el código REAL de `app.js` (sin `node` se saltan;
el reviewer los exige `passed`):

- Puras (T4): `alcanceRegistro`, `rotuloRegistro`, `tituloRegistro` y
  `cabeceraPaquete`, con tabla de casos.
- Con DOM de mentira (T5): `pintarBotonRegistro`, `registrarPaquete`,
  `registroPreflight`, `pedirPreflight`, `registroEjecutar`,
  `esperarRegistroCortado` y `pintarModalPreflight`, con dobles de `fetch`,
  `$` (con `dataset`), `toast`, `guardarAhora` y `cerrarModal`.

Sin red ni BBDD. Los `ide` y los nombres son inventados.
"""
from __future__ import annotations

import itertools
import json
import re

import pytest

from tests.test_f042_sugerencias import JS, _funcion, _node
from tests.test_f050_modal_registro import MODAL

#: `escapeHtml` sin DOM (el de `app.js` usa `document`).
ESCAPE = ("function escapeHtml(t) { return (t == null ? '' : String(t))"
          ".replace(/&/g,'&amp;').replace(/</g,'&lt;')"
          ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }")

PURAS = ("alcanceRegistro", "rotuloRegistro", "tituloRegistro",
         "cabeceraPaquete", "nTrabajadores")


def _puras(expresion: str) -> object:
    """Evalúa `expresion` con las funciones puras de F-078 cargadas."""
    return _node("\n".join([
        ESCAPE, *(_funcion(f) for f in PURAS),
        "const T = (ide, nombre) => ({ ide, nombre: nombre || `T${ide}` });",
        f"process.stdout.write(JSON.stringify({expresion}));"]))


def _alcance(visibles: list[int], seleccion: list[int]) -> dict:
    return _puras(
        f"alcanceRegistro({json.dumps(visibles)}.map((i) => T(i)), "
        f"new Set({json.dumps(seleccion)}))")


# ============================ R13: el alcance =========================== #
@pytest.mark.parametrize(("seleccion", "esperado"), [
    # 0 o 1 seleccionados (el cursor cuenta como 1): todos los visibles.
    ([], {"origen": "visibles", "ides": [3, 1, 2], "ocultos": 0,
          "bloqueado": False}),
    ([1], {"origen": "visibles", "ides": [3, 1, 2], "ocultos": 0,
           "bloqueado": False}),
    # Uno solo, oculto: también los visibles (no hay 2 seleccionados).
    ([9], {"origen": "visibles", "ides": [3, 1, 2], "ocultos": 0,
           "bloqueado": False}),
    # 2 o más visibles: esos, en el orden de la tabla.
    ([2, 3], {"origen": "seleccionados", "ides": [3, 2], "ocultos": 0,
              "bloqueado": False}),
    ([2, 1, 3], {"origen": "seleccionados", "ides": [3, 1, 2], "ocultos": 0,
                 "bloqueado": False}),
    # Con ocultos: los visibles de la selección; los otros, contados.
    ([2, 9, 3, 8], {"origen": "seleccionados", "ides": [3, 2], "ocultos": 2,
                    "bloqueado": False}),
])
def test_f078_r13_alcance(seleccion, esperado):
    assert _alcance([3, 1, 2], seleccion) == esperado


@pytest.mark.parametrize("seleccion", [[1, 9], [9, 8], [8, 9, 7], [2, 8, 9]])
def test_f078_r14_varios_seleccionados_menos_de_dos_visibles_bloquea(
        seleccion):
    a = _alcance([3, 1, 2], seleccion)
    assert a["bloqueado"] is True and a["ides"] == []
    assert a["origen"] == "seleccionados"
    assert a["ocultos"] == len([s for s in seleccion if s not in (1, 2, 3)])


def test_f078_r13_sin_filtros_ni_seleccion_todos_los_de_la_tabla():
    assert _alcance(list(range(1, 41)), [])["ides"] == list(range(1, 41))


def test_f078_r13_r15_sin_visibles_la_lista_vacia():
    assert _alcance([], []) == {"origen": "visibles", "ides": [],
                                "ocultos": 0, "bloqueado": False}
    assert _alcance([], [4, 5])["bloqueado"] is True


def test_f078_r13_nunca_un_oculto():
    """Todas las selecciones de 0 a 4 sobre 3 visibles y 2 ocultos: ningún
    `ide` fuera de los visibles, y nunca uno sin seleccionar si van los
    seleccionados."""
    visibles, universo = [5, 2, 7], [5, 2, 7, 90, 91]
    casos = [list(c) for n in range(5)
             for c in itertools.combinations(universo, n)]
    resultados = _puras(
        f"{json.dumps(casos)}.map((s) => alcanceRegistro("
        f"{json.dumps(visibles)}.map((i) => T(i)), new Set(s)))")
    for sel, a in zip(casos, resultados):
        assert set(a["ides"]) <= set(visibles), (sel, a)
        if a["origen"] == "seleccionados":
            assert set(a["ides"]) <= set(sel), (sel, a)
        # El orden, siempre el de la tabla.
        assert a["ides"] == [i for i in visibles if i in a["ides"]], (sel, a)


# ====================== R12, R14: rótulo y `title` ===================== #
@pytest.mark.parametrize(("seleccion", "rotulo"), [
    ([], "Registrar visibles (3)"),
    ([1], "Registrar visibles (3)"),
    ([1, 2], "Registrar seleccionados (2)"),
    ([1, 2, 3, 9], "Registrar seleccionados (3)"),
    ([1, 9], "Registrar seleccionados (0)"),
])
def test_f078_r12_rotulo(seleccion, rotulo):
    assert _puras(
        "rotuloRegistro(alcanceRegistro([3, 1, 2].map((i) => T(i)), "
        f"new Set({json.dumps(seleccion)})))") == rotulo


def test_f078_r12_rotulo_sin_visibles():
    assert _puras("rotuloRegistro(alcanceRegistro([], new Set()))") == \
        "Registrar visibles (0)"


def test_f078_r14_title_dice_que_la_seleccion_esta_oculta():
    titulo = _puras(
        "tituloRegistro(alcanceRegistro([3, 1, 2].map((i) => T(i)), "
        "new Set([1, 9, 8])))")
    assert "la selección está oculta por el filtro" in titulo


@pytest.mark.parametrize(("visibles", "seleccion", "trozos"), [
    ([3, 1, 2], [], ["3 trabajadores visibles"]),
    ([3, 1, 2], [1, 2], ["2 trabajadores seleccionados"]),
    ([3, 1, 2], [1, 2, 9], ["2 trabajadores seleccionados",
                            "1 seleccionado oculto por el filtro no se registra"]),
    ([3], [], ["1 trabajador visible"]),
    ([], [], ["No hay trabajadores visibles"]),
])
def test_f078_r12_title_dice_a_quien(visibles, seleccion, trozos):
    titulo = _puras(
        f"tituloRegistro(alcanceRegistro({json.dumps(visibles)}"
        f".map((i) => T(i)), new Set({json.dumps(seleccion)})))")
    for trozo in trozos:
        assert trozo in titulo, titulo
    assert "oculta por el filtro" not in titulo


# ===================== R20: la cabecera del modal ====================== #
def _cabecera(alcance: dict, nombres: list[str]) -> dict:
    return _puras(f"cabeceraPaquete({json.dumps(alcance)}, "
                  f"{json.dumps(nombres)})")


def test_f078_r20_cabecera_seleccionados_con_nombres_escapados():
    c = _cabecera({"origen": "seleccionados", "ides": [1, 2], "ocultos": 0,
                   "bloqueado": False}, ["Ana <b>López</b>", 'Luis "&"'])
    assert c["titulo"] == " · 2 trabajadores (seleccionados)"
    assert "<details" in c["detalle"] and "<summary>" in c["detalle"]
    assert "<li>Ana &lt;b&gt;López&lt;/b&gt;</li>" in c["detalle"]
    assert "<li>Luis &quot;&amp;&quot;</li>" in c["detalle"]
    assert "<b>" not in c["detalle"]
    assert "ocultos" not in c["detalle"] and "oculto" not in c["detalle"]


@pytest.mark.parametrize(("ocultos", "linea"), [
    (1, "1 seleccionado oculto por el filtro no se registra"),
    (3, "3 seleccionados ocultos por el filtro no se registran"),
])
def test_f078_r20_cabecera_con_ocultos(ocultos, linea):
    c = _cabecera({"origen": "seleccionados", "ides": [1, 2],
                   "ocultos": ocultos, "bloqueado": False}, ["A", "B"])
    assert linea in c["detalle"]


def test_f078_r20_cabecera_visibles():
    c = _cabecera({"origen": "visibles", "ides": [4, 5, 6], "ocultos": 0,
                   "bloqueado": False}, ["A", "B", "C"])
    assert c["titulo"] == " · 3 trabajadores (visibles)"
    assert c["detalle"].count("<li>") == 3


def test_f078_r20_cabecera_de_uno_en_singular():
    c = _cabecera({"origen": "visibles", "ides": [4], "ocultos": 0,
                   "bloqueado": False}, ["A"])
    assert c["titulo"] == " · 1 trabajador (visibles)"


def test_f078_puras_no_tocan_el_dom_ni_el_estado():
    for f in ("alcanceRegistro", "rotuloRegistro", "tituloRegistro",
              "cabeceraPaquete"):
        cuerpo = re.sub(r"//[^\n]*", "", _funcion(f))
        for prohibido in ("document.", "$(", "state.", "registro."):
            assert prohibido not in cuerpo, (f, prohibido)


def test_f078_js_existe():
    assert "function alcanceRegistro(" in JS


# ======================================================================= #
#              T5: el botón, el flujo y el modal (código real)            #
# ======================================================================= #
def _si_existe(trozo) -> str:
    """El código de app.js si existe; si no, nada: antes del cambio, los
    tests de comportamiento fallan por lo que hace la pantalla y no por una
    función que falta (la existencia la piden otros asserts)."""
    try:
        return trozo()
    except AssertionError:
        return ""


def _constante(nombre: str) -> str:
    m = re.search(rf"^const {nombre} = .*?;$", JS, re.MULTILINE)
    assert m, f"no existe la constante {nombre} en app.js"
    return m.group(0)


def _arranque_del_boton() -> str:
    """El `DOMContentLoaded` que conecta `#btn-registro` (el último de
    app.js)."""
    m = re.search(r'^document\.addEventListener\("DOMContentLoaded", \(\) => '
                  r'\{\n  const b = \$\("#btn-registro"\);.*?^\}\);',
                  JS, re.DOTALL | re.MULTILINE)
    assert m, "no está el arranque de #btn-registro en app.js"
    return m.group(0)


#: DOM, api y estado de mentira. `vis`: lo que devuelve
#: `trabajadoresVisibles` (la tabla con los filtros); `log`: cada `fetch`
#: (fase y cuerpo) y cada `guardarAhora`, en orden; `respuestas`: por fase,
#: `{status, cuerpo}`, `'red'` (el fetch rechaza) o `'pendiente'`.
FLUJO = r"""
const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
var state = { anio: 2026, mes: 11, empresa: null, periodoEstado: "ABIERTO",
              seleccion: new Set(), seleccionIde: null, editandoIde: null };
const T = (ide) => ({ ide, nombre: `T${ide}` });
var vis = [];
function trabajadoresVisibles() { return vis; }
var log = []; var respuestas = {}; var pendientes = [];
async function fetch(url, op) {
  const fase = url.includes("/registro/ejecutar") ? "ejecutar" : "preflight";
  log.push(["fetch", fase, JSON.parse(op.body)]);
  const r = respuestas[fase] || { status: 200, cuerpo: { ok: true, obras: [] } };
  if (r === "red") throw new TypeError("Failed to fetch");
  const responde = (x) => ({ ok: x.status >= 200 && x.status < 300,
    status: x.status, json: async () => x.cuerpo });
  if (r === "pendiente") {
    return new Promise((res) => pendientes.push(() => res(responde(
      { status: 200, cuerpo: { ok: true, obras: [] } }))));
  }
  return responde(r);
}
async function guardarAhora() { log.push(["guardar"]); }
var avisos = [];
function toast(m, e = false, fijo = false) {
  const a = { m, e: !!e, fijo: !!fijo, quitado: false };
  avisos.push(a); return { remove() { a.quitado = true; } }; }
var modal = { cerrado: false };
function cerrarModal() { modal.cerrado = true; }
async function cargarPeriodo(a, m) { log.push(["recarga", a, m]); }
var temporizadores = [];
function setTimeout(f, ms) { temporizadores.push({ f, ms }); }
function El(t) { return { disabled: false, textContent: t, title: "", dataset: {},
  _h: {}, addEventListener(ev, fn) { this._h[ev] = fn; },
  classList: { contains: () => false } }; }
var botones = { "#btn-registro": El("Registrar en Sigrid"),
                "#btn-ejecutar-registro": El("Registrar"),
                "#modal-registro": El("") };
function $(sel) { return botones[sel]; }
var pintados = [];
function pintarModalPreflight(pf) {
  pintados.push(JSON.parse(JSON.stringify({ pf, paquete: registro.paquete || null })));
}
var escuchas = {};
var document = { querySelectorAll: () => [],
  addEventListener(ev, fn) { (escuchas[ev] = escuchas[ev] || []).push(fn); },
  body: { dataset: { usuario: "u" } } };
const boton = () => { const b = botones["#btn-registro"];
  return { disabled: b.disabled, textContent: b.textContent, title: b.title,
           rotulo: b.dataset.rotulo }; };
const fetches = (fase) => log.filter((x) => x[0] === "fetch" && (!fase || x[1] === fase))
  .map((x) => x[2]);
const tick = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
"""

FUNCIONES_FLUJO = (
    "conEmpresa", "api", "esCorteDelProxy", "esperarRegistroCortado",
    "alcanceRegistro", "rotuloRegistro", "nTrabajadores", "tituloRegistro",
    "cabeceraPaquete", "pedirPreflight", "registroPreflight",
    "unirPreflight", "repreflightPartida", "registroEjecutar")


def _paquete_y_arranque() -> list[str]:
    """`registrarPaquete` y el arranque del botón, una vez cada uno (el
    extracto de la última función de app.js llega hasta el final y ya
    trae el arranque)."""
    paquete = _si_existe(lambda: _funcion("registrarPaquete"))
    arranque = _si_existe(_arranque_del_boton)
    return [paquete] if arranque and arranque in paquete else [paquete,
                                                               arranque]


def _flujo(escenario: str) -> dict:
    programa = "\n".join([
        FLUJO, ESCAPE,
        _constante("ESPERA_RECARGA_TRAS_CORTE"), _constante("registro"),
        *(_funcion(f) for f in FUNCIONES_FLUJO),
        _si_existe(lambda: _funcion("pintarBotonRegistro")),
        *_paquete_y_arranque(),
        "(async () => { const obs = {};",
        "(escuchas.DOMContentLoaded || []).forEach((f) => f());",
        ("const pulsar = () => botones['#btn-registro']._h.click"
         " ? botones['#btn-registro']._h.click() : null;"),
        escenario,
        "process.stdout.write(JSON.stringify(obs)); })();"])
    return _node(programa)


# ---------------------- R12: el clic y el rótulo ----------------------- #
def test_f078_r12_el_clic_registra_el_paquete_y_nunca_el_mes():
    obs = _flujo("""
      vis = [T(3), T(1), T(2)];
      await pulsar(); await tick();
      obs.preflight = fetches("preflight");
    """)
    assert obs["preflight"] == [{"trabajador_ide": None,
                                 "trabajador_ides": [3, 1, 2]}]


def test_f078_r12_el_arranque_no_pide_el_mes():
    arranque = _arranque_del_boton()
    assert "registrarPaquete()" in arranque
    assert "registroPreflight" not in arranque


@pytest.mark.parametrize(("vis", "seleccion", "rotulo", "desactivado"), [
    ([3, 1, 2], [], "Registrar visibles (3)", False),
    ([3, 1, 2], [1], "Registrar visibles (3)", False),
    ([3, 1, 2], [1, 2], "Registrar seleccionados (2)", False),
    ([3, 1, 2], [1, 2, 9], "Registrar seleccionados (2)", False),
    ([3, 1, 2], [1, 9], "Registrar seleccionados (0)", True),
    ([], [], "Registrar visibles (0)", True),
])
def test_f078_r12_r14_r15_pintar_el_boton(vis, seleccion, rotulo,
                                          desactivado):
    obs = _flujo(f"""
      vis = {json.dumps(vis)}.map(T); state.seleccion = new Set({json.dumps(seleccion)});
      pintarBotonRegistro(); obs.boton = boton();
    """)
    assert obs["boton"]["textContent"] == rotulo
    assert obs["boton"]["rotulo"] == rotulo
    assert obs["boton"]["disabled"] is desactivado
    if seleccion == [1, 9]:
        assert "la selección está oculta por el filtro" in obs["boton"]["title"]


def test_f078_r12_se_pinta_en_cada_render_de_la_tabla():
    tabla = re.sub(r"//[^\n]*", "", _funcion("renderTabla"))
    assert "pintarBotonRegistro(visibles);" in tabla


def test_f078_r15_periodo_no_abierto_desactiva():
    obs = _flujo("""
      vis = [T(3), T(1)]; state.periodoEstado = "CERRADO";
      pintarBotonRegistro(); obs.boton = boton();
    """)
    assert obs["boton"]["disabled"] is True
    assert obs["boton"]["textContent"] == "Registrar visibles (2)"


def test_f078_r15_tras_un_corte_ni_el_texto_ni_el_bloqueo_cambian():
    obs = _flujo("""
      vis = [T(3), T(1)]; registro.cortado = true;
      const b = botones["#btn-registro"]; b.disabled = true; b.textContent = "Registro en curso…";
      pintarBotonRegistro(); obs.boton = boton();
    """)
    assert obs["boton"]["textContent"] == "Registro en curso…"
    assert obs["boton"]["disabled"] is True
    assert obs["boton"]["rotulo"] == "Registrar visibles (2)"


def test_f078_r15_con_un_preflight_en_vuelo_no_se_toca():
    obs = _flujo("""
      vis = [T(3), T(1)]; respuestas.preflight = "pendiente";
      pulsar(); await tick();
      pintarBotonRegistro(); obs.durante = boton();
      pendientes[0](); await tick();
      obs.despues = boton();
    """)
    assert obs["durante"]["textContent"] == "Analizando…"
    assert obs["durante"]["disabled"] is True
    assert obs["despues"]["textContent"] == "Registrar visibles (2)"
    assert obs["despues"]["disabled"] is False


# ----------------------- R15: sin nada que pedir ---------------------- #
@pytest.mark.parametrize("preparar", [
    'state.periodoEstado = "CERRADO";',
    "vis = [];",
    "state.seleccion = new Set([1, 9]);",
    "registro.cortado = true;",
])
def test_f078_r15_al_pulsar_sin_alcance_no_se_pide_nada(preparar):
    obs = _flujo(f"""
      vis = [T(3), T(1), T(2)]; state.editandoIde = 3;
      {preparar}
      await pulsar(); await tick();
      obs.log = log; obs.avisos = avisos.map((a) => a.m);
    """)
    assert obs["log"] == []
    if "cortado" in preparar:
        assert obs["avisos"] == [("El registro anterior sigue en curso; "
                                  "espera a que se recargue el cuadrante.")]


# ------------------- R16, R22: el cuerpo de las peticiones ------------ #
def test_f078_r16_r22_cuerpos_con_trabajador_ides_y_nada_mas():
    obs = _flujo("""
      vis = [T(3), T(1), T(2)]; state.seleccion = new Set([2, 3]);
      await pulsar(); await tick();
      await registroEjecutar(); await tick();
      obs.preflight = fetches("preflight"); obs.ejecutar = fetches("ejecutar");
    """)
    assert obs["preflight"] == [{"trabajador_ide": None,
                                 "trabajador_ides": [3, 2]}]
    assert obs["ejecutar"] == [{"pisar_claves": [], "trabajador_ide": None,
                                "usuario": "u", "trabajador_ides": [3, 2]}]


# ------------------------ R17: el editor abierto ---------------------- #
def test_f078_r17_con_el_editor_abierto_guarda_antes():
    obs = _flujo("""
      vis = [T(3), T(1)]; state.editandoIde = 1;
      await pulsar(); await tick();
      obs.log = log.map((x) => x[0]);
    """)
    assert obs["log"] == ["guardar", "fetch"]


def test_f078_r17_sin_editor_no_guarda():
    obs = _flujo("""
      vis = [T(3), T(1)];
      await pulsar(); await tick();
      obs.log = log.map((x) => x[0]);
    """)
    assert obs["log"] == ["fetch"]


# ------------------------ R18: la lista, congelada --------------------- #
def test_f078_r18_repreflight_y_ejecutar_mandan_la_misma_lista():
    obs = _flujo("""
      vis = [T(3), T(1), T(2)]; state.seleccion = new Set([1, 2]);
      await pulsar(); await tick();
      // Cambian la selección y los filtros con el modal abierto.
      state.seleccion = new Set([3]); vis = [T(3)];
      await repreflightPartida(678); await tick();
      await registroEjecutar(); await tick();
      obs.cuerpos = fetches();
      obs.pintado = pintados[0].paquete;
    """)
    pre, re_obra, eje = obs["cuerpos"]
    assert pre["trabajador_ides"] == [1, 2]
    assert re_obra == {"trabajador_ide": None, "obra_ide": 678,
                       "trabajador_ides": [1, 2]}
    assert eje["trabajador_ides"] == [1, 2]
    assert obs["pintado"]["ides"] == [1, 2]
    assert obs["pintado"]["origen"] == "seleccionados"
    assert obs["pintado"]["nombres"] == ["T1", "T2"]


def test_f078_r18_el_de_un_trabajador_sigue_como_hoy():
    """«⇪ Sigrid» de la fila o del editor: un trabajador, sin la clave;
    también tras haber abierto antes el de un paquete."""
    obs = _flujo("""
      vis = [T(3), T(1)];
      await pulsar(); await tick();
      await registroPreflight(77); await tick();
      await registroEjecutar(); await tick();
      obs.cuerpos = fetches();
    """)
    assert obs["cuerpos"][1:] == [
        {"trabajador_ide": 77},
        {"pisar_claves": [], "trabajador_ide": 77, "usuario": "u"}]


# --------------------- R19: vuelve al rótulo del alcance -------------- #
def test_f078_r19_tras_el_preflight_el_rotulo_de_su_alcance():
    obs = _flujo("""
      vis = [T(3), T(1), T(2)]; state.seleccion = new Set([1, 2]);
      pintarBotonRegistro();
      await pulsar(); await tick();
      obs.boton = boton();
    """)
    assert obs["boton"]["textContent"] == "Registrar seleccionados (2)"
    assert obs["boton"]["disabled"] is False


def test_f078_r19_tras_el_desbloqueo_el_rotulo_de_su_alcance():
    obs = _flujo("""
      vis = [T(3), T(1)];
      await pulsar(); await tick();
      respuestas.ejecutar = { status: 502, cuerpo: { error: "Backend inaccesible" } };
      await registroEjecutar(); await tick();
      obs.cortado = boton();
      vis = [T(3), T(1), T(2), T(4)];
      await temporizadores[0].f(); await tick();
      obs.despues = boton();
    """)
    assert obs["cortado"]["textContent"] == "Registro en curso…"
    assert obs["cortado"]["disabled"] is True
    assert obs["despues"]["textContent"] == "Registrar visibles (4)"
    assert obs["despues"]["disabled"] is False


# ------------------------ R21: el aviso final -------------------------- #
def test_f078_r21_aviso_final_con_cuantos_trabajadores():
    obs = _flujo("""
      vis = [T(3), T(1)];
      respuestas.ejecutar = { status: 200, cuerpo: { ok: true, obras: [
        { ok: true, escritas: [{}, {}, {}], omitidas: [] }] } };
      await pulsar(); await tick();
      await registroEjecutar(); await tick();
      await registroPreflight(77); await tick();
      await registroEjecutar(); await tick();
      obs.avisos = avisos.map((a) => a.m);
    """)
    paquete, uno = obs["avisos"]
    assert paquete == ("2 trabajadores · Sigrid: 3 escritas · 0 omitidas · "
                       "0 pendientes de confirmar")
    assert uno == "Sigrid: 3 escritas · 0 omitidas · 0 pendientes de confirmar"


@pytest.mark.parametrize("corte", [
    '{ status: 502, cuerpo: { error: "Backend inaccesible" } }',
    '{ status: 504, cuerpo: null }', '"red"'])
def test_f078_r21_corte_del_proxy_el_camino_del_hotfix(corte):
    obs = _flujo(f"""
      vis = [T(3), T(1)];
      await pulsar(); await tick();
      respuestas.ejecutar = {corte};
      await registroEjecutar(); await tick();
      obs.cortado = registro.cortado; obs.modal = modal;
      obs.avisos = avisos.slice(); obs.esperas = temporizadores.map((t) => t.ms);
      await pulsar(); await tick();
      obs.fetches = fetches().length;
    """)
    assert obs["cortado"] is True and obs["modal"]["cerrado"] is True
    assert obs["esperas"] == [60000]
    [aviso] = obs["avisos"]
    assert aviso["fijo"] is True
    assert "El registro sigue en curso en el servidor" in aviso["m"]
    assert obs["fetches"] == 2          # el preflight y el ejecutar cortado


# ---------------------- R20: el modal del paquete ---------------------- #
def _modal_paquete(paquete: dict | None) -> str:
    programa = "\n".join([
        ("const MESES = ['ene','feb','mar','abr','may','jun','jul','ago',"
         "'sep','oct','nov','dic'];"),
        "const state = {anio: 2026, mes: 11};", _constante("registro"), ESCAPE,
        "let html = null; function abrirModal(h) { html = h; }",
        "function registroEjecutar() {} function repreflightPartida() {}",
        "function abrirSelectorPartida() {}",
        "const document = {querySelectorAll: () => []};",
        "const $ = () => ({addEventListener() {}});",
        *(_funcion(f) for f in (*MODAL, "nTrabajadores", "cabeceraPaquete")),
        f"registro.paquete = {json.dumps(paquete, ensure_ascii=False)};",
        "pintarModalPreflight({obras: []});",
        "process.stdout.write(JSON.stringify(html));"])
    return _node(programa)


def test_f078_r20_modal_de_un_paquete():
    html = _modal_paquete({"origen": "seleccionados", "ides": [1, 2],
                           "ocultos": 2, "bloqueado": False,
                           "nombres": ["Ana <i>Ruiz</i>", "Luis"]})
    assert html.startswith("<h2>Registrar en Sigrid · nov 2026 · "
                           "2 trabajadores (seleccionados)</h2>")
    assert "<li>Ana &lt;i&gt;Ruiz&lt;/i&gt;</li><li>Luis</li>" in html
    assert "2 seleccionados ocultos por el filtro no se registran" in html


def test_f078_r20_modal_de_visibles_sin_ocultos():
    html = _modal_paquete({"origen": "visibles", "ides": [4, 5, 6],
                           "ocultos": 0, "bloqueado": False,
                           "nombres": ["A", "B", "C"]})
    assert "· 3 trabajadores (visibles)</h2>" in html
    assert "ocultos" not in html


def test_f078_r20_modal_sin_paquete_como_hoy():
    html = _modal_paquete(None)
    assert html.startswith("<h2>Registrar en Sigrid · nov 2026</h2>")
    assert "<details" not in html


# ------------------------- index.html: la ayuda ------------------------ #
def test_f078_r12_ayuda_del_pie_y_el_mismo_boton():
    from tests.test_f029_seleccion import HTML

    assert HTML.count('id="btn-registro"') == 1
    assert "Registrar: seleccionados (2+) o visibles" in HTML
