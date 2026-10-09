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
    """F-050 (R29): las partidas elegidas ya están guardadas en el
    cuadrante; el cuerpo solo lleva el trabajador."""
    obs = _flujo("""
      registro.trabajadorIde = 42;
      repreflightPartida(); await tick();
      obs.llamadas = llamadas.map((l) => [l.url, l.body]);
    """)
    assert obs["llamadas"] == [[
        "/periodos/2026/9/registro/preflight", {"trabajador_ide": 42}]]


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
      registro.pisar = new Set(["vieja"]);
      registroPreflight(42); await tick();
      obs.cuerpos = cuerpos();
      llamadas[0].res({obras: []}); await tick();
      obs.pisar = pintados[0].pisar;
      obs.boton = boton("#btn-registro");
    """)
    assert obs["cuerpos"] == [{"trabajador_ide": 42}]
    assert obs["pisar"] == []
    assert obs["boton"] == {"disabled": False,
                            "textContent": "Registrar en Sigrid"}


def test_f049_b_abrir_de_nuevo_descarta_un_repreflight_en_vuelo():
    obs = _flujo("""
      registro.trabajadorIde = 7;
      repreflightPartida(); await tick();
      registroPreflight(null); await tick();
      llamadas[1].res({obras: ["abierto"]}); await tick();
      llamadas[0].res({obras: ["viejo"]}); await tick();
      obs.pintados = pintados.map((p) => p.pf);
      obs.cuerpos = cuerpos();
    """)
    assert obs["pintados"] == [{"obras": ["abierto"]}]
    assert obs["cuerpos"] == [{"trabajador_ide": 7},
                              {"trabajador_ide": None}]


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
                   "textoPartidaAccion", "rotuloOrigen",
                   "pintarModalPreflight")


def _modal(obras: list[dict], escenario: str = "",
           pisar: list[str] | None = None) -> dict:
    """Pinta con el código REAL y devuelve el HTML y lo que haya apuntado
    el escenario (con el `click` del botón de partida a mano y el selector
    de F-050 de mentira: apunta con qué se abre y guarda su `despues`)."""
    programa = "\n".join([
        MESES_JS,
        "const state = {anio: 2026, mes: 9};",
        _registro(),
        "registro.pisar = new Set(" + json.dumps(pisar or []) + ");",
        "let html = null; function abrirModal(h) { html = h; }",
        ESCAPE,
        "const sels = []; let repreflights = 0; const aperturas = [];",
        "let despues = null;",
        "function repreflightPartida() { repreflights += 1; }",
        ("function abrirSelectorPartida(t, o, pv, ancla, d) {"
         " aperturas.push([t, o, pv, ancla.dataset.reg]); despues = d; }"),
        "function registroEjecutar() {}",
        "const document = {querySelectorAll: (s) => s === '.sel-partida' ? sels : []};",
        "const $ = () => ({addEventListener() {}});",
        *(_funcion(f) for f in FUNCIONES_MODAL),
        # Un botón de mentira por cada `.sel-partida` pintado.
        "const _pintar = pintarModalPreflight;",
        "function pinta(pf) {",
        "  sels.length = 0;",
        "  const regs = [...JSON.stringify(pf).matchAll(/\"registro_id\":(\\d+)/g)];",
        "  regs.forEach((m) => sels.push({dataset: {reg: m[1]},",
        "    _h: null, addEventListener(ev, fn) { if (ev === 'click') this._h = fn; }}));",
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
    """F-050 (R29): el clic abre el selector de esa línea (trabajador, obra
    del grupo y modo); el preflight se repite DESPUÉS de elegir, no al
    abrir."""
    obra = _obra([_accion(registro_id=3001, recurso_ide=77,
                          es_postventa=False),
                  _accion(registro_id=3002, recurso_ide=78,
                          es_postventa=False)], PARTIDAS)
    obra["obra"]["ide"] = 694
    obs = _modal([obra], """
      sels[1]._h();
      obs.n0 = repreflights; despues();
      obs.n1 = repreflights; sels[0]._h(); despues();
      obs.aperturas = aperturas; obs.n2 = repreflights;
    """)
    assert obs["n0"] == 0 and obs["n1"] == 1 and obs["n2"] == 2
    assert obs["aperturas"] == [[78, 694, False, "3002"],
                                [77, 694, False, "3001"]]


def test_f049_a_el_preflight_repetido_lleva_la_partida_recien_elegida():
    """De punta a punta con el código real (modal, clic, selector, PUT,
    repreflight y petición): primero se guarda la partida elegida y DESPUÉS
    se repite el análisis, que ya la lee del cuadrante. Mutante A27 de la
    campaña manual de F-049 (repreflight antes de apuntar la partida)."""
    from tests.test_f050_modal_registro import DOM_SELECTOR
    programa = "\n".join([
        MESES_JS,
        "const state = {anio: 2026, mes: 9, empresa: 1, editandoIde: null};",
        _registro(), DOM_SELECTOR, ESCAPE,
        "const selector = { cache: new Map(), cerrar: null };",
        "const llamadas = [];",
        ("function api(url, o) { llamadas.push([url, o && o.method || 'GET',"
         " o && o.body ? JSON.parse(o.body) : null]);"
         " if (url.includes('/partidas?')) return Promise.resolve({"
         "partidas: " + json.dumps([dict(p, mayor="CI") for p in PARTIDAS])
         + ", partidas_postventa: [], ambito: null, propuesta: null});"
         " if (o && o.method === 'PUT') return Promise.resolve({"
         "trabajador: {ide: 77}, resumen: {}});"
         " return new Promise(() => {}); }"),
        "function toast() {} function registroEjecutar() {}",
        "function abrirModal(h) {} function aplicarFila() {}",
        "async function guardarAhora() {}",
        "const sel = nodo('button'); sel.dataset.reg = '3001';",
        "document.querySelectorAll = (s) => s === '.sel-partida' ? [sel] : [];",
        ("const $ = (s) => s === '#modal-registro'"
         " ? {classList: {contains: () => false}}"
         " : {addEventListener() {}, disabled: false, textContent: ''};"),
        *(_funcion(f) for f in (
            *FUNCIONES_MODAL, "pedirPreflight", "repreflightPartida",
            "normalizar", "filtrarPartidas", "listaSelector",
            "posicionSugerencias", "clavePartidas", "cerrarSelectorPartida",
            "abrirSelectorPartida", "montarSelectorPartida")),
        "registro.trabajadorIde = 77;",
        "(async () => {",
        "  pintarModalPreflight(" + json.dumps({"obras": [dict(
            _obra([_accion(recurso_ide=77, es_postventa=False)], PARTIDAS),
            obra={"ide": 694, "codigo": "0694", "nombre": "Obra 0694"})]})
        + ");",
        "  sel._h.click(); await new Promise((r) => setTimeout(r, 0));",
        "  const input = paneles[0]._input; input.value = 'jefe';",
        "  input._h.input();",
        "  input._h.keydown({key: 'Enter', preventDefault() {},"
        " stopPropagation() {}});",
        "  await new Promise((r) => setTimeout(r, 0));",
        "  process.stdout.write(JSON.stringify(llamadas));",
        "})();"])
    assert _node(programa) == [
        ["/periodos/2026/9/trabajadores/77/partidas?obra_ide=694"
         "&es_postventa=false", "GET", None],
        ["/periodos/2026/9/trabajadores/77/partida", "PUT",
         {"obra_ide": 694, "es_postventa": False,
          "partida": {"ide": 80002, "cod": "CI.1.20", "res": "JEFE DE OBRA"}}],
        ["/periodos/2026/9/registro/preflight", "POST",
         {"trabajador_ide": 77}]]


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
    """`repreflightPartida` se usa en un único sitio: el `despues` del
    selector que abre el botón de partida del modal (F-050, R29; abrir
    desde un botón sigue siendo `registroPreflight`, que empieza de cero)."""
    assert len(re.findall(r"(?<!function )\brepreflightPartida\b", JS)) == 1
    modal = " ".join(_funcion("pintarModalPreflight").split())
    assert ("abrirSelectorPartida(l.trabajador, l.obra_ide, l.es_postventa, "
            "boton, repreflightPartida);") in modal
    assert len(re.findall(r"\bregistroPreflight\(", JS)) == 4  # def + 3 botones


# ================ c) la partida se enseña aunque no esté ================ #
# F-050 (R29): sin `<select>`, la intención de los `c_*` de F-049 (se ve la
# partida de la acción aunque no esté en el catálogo, «partida N» sin
# código, «sin partida», escapada) vive en `test_f050_modal_registro.py`.
def test_f049_c_el_modal_pinta_la_partida_de_la_accion():
    obs = _modal([_obra([_accion(paride=80002, partida_cod="CI.1.20",
                                 partida_metodo="manual")])])
    boton = re.search(r'<button type="button" class="sel-partida" '
                      r'data-reg="3001">([^<]*)</button>', obs["html"])
    assert boton and boton.group(1) == "CI.1.20"


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
