# tests/test_f049_ampliacion_registro.py
"""F-049 (ampliación aprobada por el humano el 2026-10-08) · El modal de
registro se vuelve a pedir al elegir partida y no arrastra partidas viejas.

Lo que encontró el humano en la MANUAL de F-049:

1. Al elegir partida el aviso «sin partida» no desaparece: el modal no se
   vuelve a pedir (la partida sí viaja al ejecutar).
2. Al volver a abrir el registro, el desplegable sale «— sin partida —» y
   sin aviso: las partidas elegidas se quedaban en `registro.overrides` para
   siempre, y si la partida no estaba en `partidas_obra` no había opción que
   marcar (lo de `partidas_obra` vacío se arregla en el transfer, punto d).

Lo que se fija aquí (letras de la ampliación en `harness/features.json`):

- **a)** al cambiar una partida se repite el preflight con las partidas
  elegidas y el trabajador de la petición; las casillas marcadas se
  conservan por su clave; mientras tanto «Registrar» no se puede pulsar; una
  respuesta vieja (otra petición detrás, modal cerrado) no pinta nada.
- **b)** abrir el registro desde un botón empieza sin partidas elegidas.
- **c)** la partida de la acción se enseña aunque no esté en la lista.
- **e)** el texto de los avisos se ajusta a su recuadro (CSS).

Patrón de `test_f049_avisos_registro.py`: el código REAL de `app.js` en
`node`, con un DOM mínimo de mentira. Sin `node` se saltan con su motivo; el
reviewer los exige `passed`. Sin red ni BBDD.
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
    """La declaración REAL del estado del registro."""
    m = re.search(r"^const registro = \{.*?\};$", JS, re.MULTILINE)
    assert m, "no está `const registro = {...};` en app.js"
    return m.group(0)


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-049 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


MESES_JS = ("const MESES = ['ene','feb','mar','abr','may','jun','jul',"
            "'ago','sep','oct','nov','dic'];")
ESCAPE = ("function escapeHtml(t) { return (t == null ? '' : String(t))"
          ".replace(/&/g,'&amp;').replace(/</g,'&lt;')"
          ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }")


# ===================== a) y b): el flujo de peticiones ==================== #
#: DOM y api de mentira para `pedirPreflight`, `registroPreflight` y
#: `repreflightPartida`: cada `api()` queda pendiente en `llamadas` hasta que
#: el escenario la resuelve (`res`) o la rechaza (`rej`), así se puede
#: probar el orden en que llegan las respuestas.
FLUJO = r"""
const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const state = {anio: 2026, mes: 9};
const llamadas = [];
function api(url, opts) {
  return new Promise((res, rej) => llamadas.push(
    {url, body: JSON.parse(opts.body), res, rej}));
}
const toasts = [];
function toast(m, e) { toasts.push([m, !!e]); }
const pintados = [];
function pintarModalPreflight(pf) {
  pintados.push({pf, pisar: [...registro.pisar].sort()});
}
const dom = {oculto: false, marcadas: [], botones: {}};
function boton(id) {
  return dom.botones[id] || (dom.botones[id] = {disabled: false, textContent: ""});
}
function $(sel) {
  if (sel === "#modal-registro") {
    return {classList: {contains: (c) => c === "oculto" && dom.oculto}};
  }
  return boton(sel);
}
const document = {querySelectorAll: (s) => s === ".chk-pisar:checked"
  ? dom.marcadas.map((v) => ({value: v})) : []};
const tick = () => new Promise((r) => setTimeout(r, 0));
const cuerpos = () => llamadas.map((l) => l.body);
const ejecutar = () => ({...boton("#btn-ejecutar-registro")});
"""


def _flujo(escenario: str) -> dict:
    programa = "\n".join([
        _registro(), FLUJO,
        *(_funcion(f) for f in ("pedirPreflight", "registroPreflight",
                                 "repreflightPartida")),
        "(async () => { const obs = {};", escenario,
        "process.stdout.write(JSON.stringify(obs)); })();"])
    return _node(programa)


def test_f049_a_repreflight_manda_las_elegidas_y_el_trabajador():
    obs = _flujo("""
      registro.overrides = {"3001": 80002}; registro.trabajadorIde = 42;
      repreflightPartida(); await tick();
      obs.llamadas = llamadas.map((l) => [l.url, l.body]);
    """)
    assert obs["llamadas"] == [[
        "/periodos/2026/9/registro/preflight",
        {"overrides": {"3001": 80002}, "trabajador_ide": 42}]]


def test_f049_a_registrar_bloqueado_mientras_se_analiza():
    obs = _flujo("""
      boton("#btn-ejecutar-registro").textContent = "Registrar";
      repreflightPartida(); await tick();
      obs.durante = ejecutar(); obs.pintados_durante = pintados.length;
      llamadas[0].res({obras: ["nuevo"]}); await tick();
      obs.pintados = pintados.map((p) => p.pf);
    """)
    assert obs["durante"] == {"disabled": True, "textContent": "Analizando…"}
    assert obs["pintados_durante"] == 0
    assert obs["pintados"] == [{"obras": ["nuevo"]}]


def test_f049_a_conserva_las_casillas_marcadas_por_su_clave():
    """Se leen al llegar la respuesta (lo marcado mientras se analizaba
    también cuenta) y `pintarModalPreflight` las vuelve a marcar."""
    obs = _flujo("""
      dom.marcadas = ["sobrecarga:77|2026-09"];
      repreflightPartida(); await tick();
      dom.marcadas = ["sobrecarga:77|2026-09", "77|2026|9|5|0"];
      llamadas[0].res({obras: []}); await tick();
      obs.pisar = pintados[0].pisar;
    """)
    assert obs["pisar"] == ["77|2026|9|5|0", "sobrecarga:77|2026-09"]


def test_f049_a_solo_pinta_la_ultima_peticion():
    """Dos cambios seguidos: la primera respuesta no pinta, llegue antes o
    después que la segunda."""
    obs = _flujo("""
      repreflightPartida(); repreflightPartida(); await tick();
      llamadas[0].res({obras: ["vieja"]}); await tick();
      obs.tras_vieja = pintados.length; obs.bloqueado = ejecutar().disabled;
      llamadas[1].res({obras: ["nueva"]}); await tick();
      obs.pintados = pintados.map((p) => p.pf);

      pintados.length = 0;
      repreflightPartida(); repreflightPartida(); await tick();
      llamadas[3].res({obras: ["nueva2"]}); await tick();
      llamadas[2].res({obras: ["vieja2"]}); await tick();
      obs.pintados2 = pintados.map((p) => p.pf);
    """)
    assert obs["tras_vieja"] == 0 and obs["bloqueado"] is True
    assert obs["pintados"] == [{"obras": ["nueva"]}]
    assert obs["pintados2"] == [{"obras": ["nueva2"]}]


def test_f049_a_modal_cerrado_no_se_reabre():
    obs = _flujo("""
      repreflightPartida(); await tick();
      dom.oculto = true;
      llamadas[0].res({obras: []}); await tick();
      obs.pintados = pintados.length;
    """)
    assert obs["pintados"] == 0


def test_f049_a_error_avisa_y_devuelve_el_boton():
    obs = _flujo("""
      boton("#btn-ejecutar-registro").textContent = "Registrar";
      repreflightPartida(); await tick();
      llamadas[0].rej(new Error("api caída")); await tick();
      obs.toasts = toasts; obs.boton = ejecutar(); obs.pintados = pintados.length;
    """)
    assert obs["toasts"] == [["api caída", True]]
    assert obs["boton"] == {"disabled": False, "textContent": "Registrar"}
    assert obs["pintados"] == 0


def test_f049_a_el_error_de_una_peticion_vieja_no_desbloquea():
    obs = _flujo("""
      repreflightPartida(); repreflightPartida(); await tick();
      llamadas[0].rej(new Error("vieja")); await tick();
      obs.toasts = toasts; obs.bloqueado = ejecutar().disabled;
    """)
    assert obs["toasts"] == [] and obs["bloqueado"] is True


def test_f049_b_abrir_desde_un_boton_empieza_sin_partidas_elegidas():
    obs = _flujo("""
      registro.overrides = {"3001": 80002};
      registro.pisar = new Set(["vieja"]);
      registroPreflight(42); await tick();
      obs.cuerpos = cuerpos();
      llamadas[0].res({obras: []}); await tick();
      obs.pisar = pintados[0].pisar; obs.overrides = registro.overrides;
      obs.boton = boton("#btn-registro");
    """)
    assert obs["cuerpos"] == [{"overrides": {}, "trabajador_ide": 42}]
    assert obs["pisar"] == [] and obs["overrides"] == {}
    assert obs["boton"] == {"disabled": False,
                            "textContent": "Registrar en Sigrid"}


def test_f049_b_abrir_de_nuevo_descarta_un_repreflight_en_vuelo():
    obs = _flujo("""
      registro.trabajadorIde = 7; registro.overrides = {"1": 5};
      repreflightPartida(); await tick();
      registroPreflight(null); await tick();
      llamadas[1].res({obras: ["abierto"]}); await tick();
      llamadas[0].res({obras: ["viejo"]}); await tick();
      obs.pintados = pintados.map((p) => p.pf);
      obs.cuerpos = cuerpos();
    """)
    assert obs["pintados"] == [{"obras": ["abierto"]}]
    assert obs["cuerpos"] == [{"overrides": {"1": 5}, "trabajador_ide": 7},
                              {"overrides": {}, "trabajador_ide": None}]


def test_f049_b_una_apertura_vieja_no_pinta_encima_de_otra():
    obs = _flujo("""
      registroPreflight(1); registroPreflight(2); await tick();
      llamadas[1].res({obras: ["dos"]}); await tick();
      llamadas[0].res({obras: ["uno"]}); await tick();
      obs.pintados = pintados.map((p) => p.pf);
    """)
    assert obs["pintados"] == [{"obras": ["dos"]}]


# ============ a) y c): lo que pinta el modal (código real) =============== #
#: Funciones que `pintarModalPreflight` necesita de verdad.
FUNCIONES_MODAL = ("fmtPct", "pctNuevas", "rotuloConflicto",
                   "opcionesPartida", "pintarModalPreflight")


def _modal(obras: list[dict], escenario: str = "",
           pisar: list[str] | None = None) -> dict:
    """Pinta con el código REAL y devuelve el HTML y lo que haya apuntado
    el escenario (con el `change` del desplegable a mano)."""
    programa = "\n".join([
        MESES_JS,
        "const state = {anio: 2026, mes: 9};",
        _registro(),
        "registro.pisar = new Set(" + json.dumps(pisar or []) + ");",
        "let html = null; function abrirModal(h) { html = h; }",
        ESCAPE,
        "const sels = []; let repreflights = 0;",
        "function repreflightPartida() { repreflights += 1; }",
        "function registroEjecutar() {}",
        "const document = {querySelectorAll: (s) => s === '.sel-partida' ? sels : []};",
        "const $ = () => ({addEventListener() {}});",
        *(_funcion(f) for f in FUNCIONES_MODAL),
        # Un `select` de mentira por cada `.sel-partida` pintado.
        "const _pintar = pintarModalPreflight;",
        "function pinta(pf) {",
        "  sels.length = 0;",
        "  const regs = [...JSON.stringify(pf).matchAll(/\"registro_id\":(\\d+)/g)];",
        "  regs.forEach((m) => sels.push({dataset: {reg: m[1]}, value: '0',",
        "    _h: null, addEventListener(ev, fn) { if (ev === 'change') this._h = fn; }}));",
        "  _pintar(pf);",
        "}",
        "pinta(" + json.dumps({"obras": obras}, ensure_ascii=False) + ");",
        "const obs = {};",
        escenario,
        "obs.html = html;",
        "process.stdout.write(JSON.stringify(obs));"])
    return _node(programa)


def _accion(**cambios) -> dict:
    base = {"registro_id": 3001, "nombre": "GONZALEZ PANIAGUA",
            "destino": "obra", "accion": "escribir", "can": 0.5,
            "hora_codigo": "MADM", "paride": 0, "partida_cod": None,
            "partida_metodo": None, "aviso": None}
    return base | cambios


def _obra(acciones: list[dict], partidas: list[dict] | None = None,
          conflictos: list[dict] | None = None) -> dict:
    return {"obra": {"codigo": "0694", "nombre": "Obra 0694"}, "ok": True,
            "forzada_pruebas": False, "partes": [], "acciones": acciones,
            "partidas_obra": partidas or [], "partidas_postventa": [],
            "conflictos": conflictos or []}


PARTIDAS = [{"ide": 80001, "cod": "CI.1.10", "res": "ENCARGADO"},
            {"ide": 80002, "cod": "CI.1.20", "res": "JEFE DE OBRA"}]


def _conflicto(clave: str, motivo: str = "pisado") -> dict:
    return {"clave": clave, "motivo": motivo, "nombre": "GONZALEZ PANIAGUA",
            "recurso_ide": 77, "hora_codigo": "MADM", "parte_cod": None,
            "nuevas": [{"can": 0.5}], "lineas": [], "contexto": []}


def test_f049_a_cambiar_la_partida_la_apunta_y_repite_el_preflight():
    obs = _modal([_obra([_accion(registro_id=3001),
                         _accion(registro_id=3002)], PARTIDAS)], """
      sels[1].value = "80002"; sels[1]._h();
      obs.tras_uno = {...registro.overrides}; obs.n1 = repreflights;
      sels[0].value = "0"; sels[0]._h();
      obs.overrides = registro.overrides; obs.n2 = repreflights;
    """)
    assert obs["tras_uno"] == {"3002": 80002} and obs["n1"] == 1
    assert obs["overrides"] == {"3002": 80002, "3001": 0}
    assert obs["n2"] == 2


def test_f049_a_el_preflight_repetido_lleva_la_partida_recien_elegida():
    """De punta a punta con el código real (modal, `change`, repreflight y
    petición): lo que viaja es la partida que se acaba de elegir. Mutante
    A27 de la campaña manual: con el orden al revés (repreflight antes de
    apuntar la partida) solo lo cazaba la comprobación estática."""
    programa = "\n".join([
        MESES_JS,
        "const state = {anio: 2026, mes: 9};",
        _registro(), ESCAPE,
        "const llamadas = [];",
        ("function api(url, o) { llamadas.push(JSON.parse(o.body));"
         " return new Promise(() => {}); }"),
        "function toast() {} function registroEjecutar() {}",
        "function abrirModal(h) {}",
        ("const sel = {dataset: {reg: '3001'}, value: '0', _h: null,"
         " addEventListener(ev, fn) { this._h = fn; }};"),
        ("const document = {querySelectorAll: (s) =>"
         " s === '.sel-partida' ? [sel] : []};"),
        ("const $ = (s) => s === '#modal-registro'"
         " ? {classList: {contains: () => false}}"
         " : {addEventListener() {}, disabled: false, textContent: ''};"),
        *(_funcion(f) for f in (*FUNCIONES_MODAL, "pedirPreflight",
                                 "repreflightPartida")),
        "registro.trabajadorIde = 42;",
        "pintarModalPreflight(" + json.dumps(
            {"obras": [_obra([_accion()], PARTIDAS)]}) + ");",
        "sel.value = '80002'; sel._h();",
        "process.stdout.write(JSON.stringify(llamadas));"])
    assert _node(programa) == [{"overrides": {"3001": 80002},
                                "trabajador_ide": 42}]


def test_f049_a_las_casillas_de_registro_pisar_salen_marcadas():
    obs = _modal([_obra([], conflictos=[_conflicto("sin_partida:3001",
                                                   "sin_partida"),
                                        _conflicto("77|2026|9|5|0")])],
                 pisar=["77|2026|9|5|0", "otra-que-ya-no-esta"])
    casillas = re.findall(r'<input type="checkbox" class="chk-pisar" '
                          r'value="([^"]*)"( checked)?>', obs["html"])
    assert casillas == [("sin_partida:3001", ""),
                        ("77|2026|9|5|0", " checked")]


def test_f049_a_solo_el_desplegable_repite_el_preflight():
    """`repreflightPartida` se llama en un único sitio: el `change` del
    desplegable de partida (abrir desde un botón sigue siendo
    `registroPreflight`, que empieza de cero)."""
    assert len(re.findall(r"(?<!function )\brepreflightPartida\(\)", JS)) == 1
    modal = " ".join(_funcion("pintarModalPreflight").split())
    assert ("registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) "
            "|| 0; repreflightPartida();") in modal
    assert len(re.findall(r"\bregistroPreflight\(", JS)) == 4  # def + 3 botones


# ================ c) la partida se enseña aunque no esté ================ #
def _opciones(partidas: list[dict], sel, cod=None) -> str:
    programa = "\n".join([
        ESCAPE, _funcion("opcionesPartida"),
        "process.stdout.write(JSON.stringify(opcionesPartida(" +
        ", ".join(json.dumps(x, ensure_ascii=False)
                  for x in (partidas, sel, cod)) + ")));"])
    return _node(programa)


def _elegida(html: str) -> list[tuple[str, str]]:
    return re.findall(r'<option value="([^"]*)" selected>([^<]*)</option>',
                      html)


def test_f049_c_partida_de_la_lista_se_marca_sin_opcion_extra():
    html = _opciones(PARTIDAS, 80002, "CI.1.20")
    assert _elegida(html) == [("80002", "CI.1.20 · JEFE DE OBRA")]
    assert html.count("<option") == 3


def test_f049_c_partida_fuera_de_la_lista_se_ensena_igual():
    """El caso del humano: la partida elegida antes no estaba en
    `partidas_obra` (que salía vacío) y el desplegable decía «— sin
    partida —» mientras se iba a escribir otra cosa."""
    html = _opciones([], 80002, "CI.1.20")
    assert _elegida(html) == [("80002", "CI.1.20 · (no está en la lista)")]
    assert html.startswith('<option value="0">— sin partida —</option>')
    assert html.count(" selected") == 1


def test_f049_c_fuera_de_la_lista_y_con_otras_partidas():
    html = _opciones(PARTIDAS, 99999, "CI.9.99")
    assert _elegida(html) == [("99999", "CI.9.99 · (no está en la lista)")]
    assert html.count("<option") == 4 and html.count(" selected") == 1


def test_f049_c_fuera_de_la_lista_sin_codigo():
    html = _opciones([], 80002, None)
    assert _elegida(html) == [("80002", "partida 80002 · (no está en la lista)")]


@pytest.mark.parametrize("sel", [0, None])
def test_f049_c_sin_partida_no_inventa_ninguna(sel):
    html = _opciones(PARTIDAS, sel, "CI.1.20")
    assert " selected" not in html and html.count("<option") == 3


def test_f049_c_el_codigo_se_escapa():
    html = _opciones([], 5, "A<b>&C")
    assert "A&lt;b&gt;&amp;C · (no está en la lista)" in html
    assert "A<b>" not in html


def test_f049_c_el_modal_pinta_la_partida_de_la_accion():
    obs = _modal([_obra([_accion(paride=80002, partida_cod="CI.1.20",
                                 partida_metodo="manual")])])
    select = re.search(r'<select class="sel-partida" data-reg="3001">(.*?)'
                       r"</select>", obs["html"]).group(1)
    assert _elegida(select) == [("80002", "CI.1.20 · (no está en la lista)")]


# ====================== e) el texto cabe en su recuadro ================== #
def _regla(selector: str) -> str:
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert m, f"no hay regla {selector} en styles.css"
    return " ".join(m.group(1).split())


def test_f049_e_el_aviso_amarillo_ajusta_el_texto():
    regla = _regla(".modal .aviso")
    assert "white-space: normal;" in regla
    assert "overflow-wrap: anywhere;" in regla


def test_f049_e_el_texto_de_la_casilla_no_se_sale_del_recuadro():
    """`.check` (genérico) lleva `white-space: nowrap`: dentro de un
    conflicto, el rótulo largo de F-049 se salía de su recuadro."""
    regla = _regla(".modal .conflicto .check")
    assert "white-space: normal;" in regla
    assert "overflow-wrap: anywhere;" in regla
    assert "display: block;" in regla
