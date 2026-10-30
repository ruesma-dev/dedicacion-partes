# tests/test_f054_traer_front.py
"""F-054 · T9: el front de «traer de Sigrid» (R1, R28; design §7).

Tras un sync con éxito, `sincronizarYTraer` pide comparar (`traerDeSigrid`
con `aceptar` vacío); tras uno fallido, no (R1). La ventana pinta lo que
manda la API: por trabajador, sus entradas con estado y los dos %, y una
casilla solo en las `distinta` (desmarcada) y las `solo_sigrid` (marcada,
D12). «Aceptar las marcadas» manda justo las marcadas y recarga; sin
pulsarlo no se manda nada; un error se avisa (R28). El front no compara ni
decide.

Se ejecutan las funciones REALES de `app.js` en node con dobles de `api`,
`toast`, `$`, `document` y `cargarPeriodo`; sin `node` se saltan con su
motivo. `test_f061_recarga.py` no cambia: `sincronizar` sigue igual y solo
gana su `true` / `false`. Sin red ni BBDD.
"""
from __future__ import annotations

import json
import re

from tests.test_f030_tabla_incidencias import DOM_TEXTO
from tests.test_f042_sugerencias import JS, _funcion, _node

SYNC_OK = ("{ duracion_s: 1, empleados: { recibidos: 1, altas: 0, "
           "desactivados: 0 }, obras: { recibidos: 1, altas: 0, "
           "desactivados: 0 } }")


def _entrada(obra, estado, *, pv=False, sig=None, cua=None, motivo=None):
    return {"obra_ide": obra, "cod": f"{obra:04d}", "descripcion": "OBRA <X>",
            "es_postventa": pv, "estado": estado, "pct_sigrid": sig,
            "pct_cuadrante": cua, "partida_cod": "CI.1.5" if sig else None,
            "partida_res": None, "parte_cod": "PT26/9" if sig else None,
            "n_lineas": 1 if sig else 0, "motivo": motivo}


DATOS = {
    "trabajadores": [
        {"trabajador_ide": 10, "cod": "10", "nombre": "Ana", "aceptadas": [],
         "entradas": [
             _entrada(678, "solo_cuadrante", cua=40),
             _entrada(694, "distinta", sig=95, cua=60),
             _entrada(713, "solo_sigrid", sig=5),
             _entrada(678, "solo_sigrid", pv=True, sig=10),
             _entrada(720, "igual", sig=20, cua=20),
             _entrada(730, "no_traducible", sig=120,
                      motivo="el porcentaje de Sigrid (120.00) no está en "
                             "(0, 100]")]}],
    "aceptadas": 0, "rechazadas": [],
    "no_traidas": [{"hmores_ide": 1, "recurso_ide": 30, "obra_cod": "0694",
                    "parte_cod": "PT26/1", "can": 0.5,
                    "motivo": "el trabajador no está vigente en 09/2026"}],
    "fuera_maestro": 2, "de_vinculados": 3, "lineas_leidas": 12,
    "excluidas_pruebas": 1, "motivo_postventa": "pv sin catálogo",
    "motivo_var": None, "propuestas_en_curso": False}

#: Dobles comunes: lo que se pide a la api, los avisos, el modal y sus
#: botones (con sus escuchas) y las casillas marcadas.
DOBLES = r"""
var state = { anio: 2026, mes: 9 };
var pedidas = []; var avisos = []; var modal = { abierto: false, html: "" };
var boton = { disabled: false, textContent: "" };
var botones = {};
function El() { this.escuchas = {}; }
El.prototype.addEventListener = function (t, f) { this.escuchas[t] = f; };
function $(sel) {
  if (sel === "#btn-sync") return boton;
  if (!modal.abierto || !modal.html.includes(sel.slice(1))) return null;
  return botones[sel] = botones[sel] || new El();
}
function toast(m, e) { avisos.push([m, !!e]); }
async function cargarPeriodo(a, m) { pedidas.push("cargarPeriodo"); }
async function cargarTiposIncidencia() { pedidas.push("tipos"); }
function marcarPropuestas(x) { pedidas.push(["propuestas", !!x]); }
function abrirModal(html) { modal.abierto = true; modal.html = html; }
function cerrarModal() { modal.abierto = false; pedidas.push("cerrarModal"); }
var marcadas = [];
document.querySelectorAll = function (sel) {
  pedidas.push(["querySelectorAll", sel]);
  return marcadas.map((d) => ({ dataset: d }));
};
function fmtPct(v) { return String(v).replace(".", ",") + "%"; }
"""

FUNCIONES = ("escapeHtml", "sincronizar", "sincronizarYTraer",
             "traerDeSigrid", "textoEstadoSigrid", "filaEntradaSigrid",
             "pintarTraerSigrid", "aceptadasMarcadas", "abrirTraerSigrid")


def _programa(api: str, cuerpo: str) -> object:
    return _node("\n".join([
        DOM_TEXTO, DOBLES, api, *[_funcion(f) for f in FUNCIONES],
        "(async () => {", cuerpo,
        "process.stdout.write(JSON.stringify({ pedidas, avisos, modal,",
        "  escuchas: Object.fromEntries(Object.entries(botones).map(",
        "    ([k, v]) => [k, Object.keys(v.escuchas)])) }));",
        "})();"]))


def _api(sync="ok", traer="ok", datos=DATOS) -> str:
    return "\n".join([
        "async function api(ruta, op) {",
        "  pedidas.push([ruta, op && op.body ? JSON.parse(op.body) : null]);",
        f"  if (ruta === '/sync') {{ if ('{sync}' === 'falla') "
        "throw new Error('sin sigrid');",
        f"    return {SYNC_OK}; }}",
        f"  if ('{traer}' === 'falla') throw new Error('transfer caido');",
        "  const d = " + json.dumps(datos, ensure_ascii=False) + ";",
        "  return op && JSON.parse(op.body).aceptar.length ? Object.assign(d,",
        "    { aceptadas: 1, rechazadas: [{ trabajador_ide: 10, obra_ide: 678,",
        "      es_postventa: false, motivo: 'solo en el cuadrante' }],",
        "      propuestas_en_curso: true }) : d;",
        "}"])


RUTA = "/periodos/2026/9/traer-sigrid"


def test_f054_r1_tras_un_sync_con_exito_se_pide_comparar():
    r = _programa(_api(), "await sincronizarYTraer();")
    assert r["pedidas"] == [["/sync", None], "cargarPeriodo", "tipos",
                            [RUTA, {"aceptar": []}]]
    assert r["modal"]["abierto"] is True


def test_f054_r1_tras_un_sync_fallido_no_se_compara():
    r = _programa(_api(sync="falla"), "await sincronizarYTraer();")
    assert r["pedidas"] == [["/sync", None]]
    assert r["modal"]["abierto"] is False


def test_f054_r1_sincronizar_devuelve_si_fue_bien():
    ok = _programa(_api(), "pedidas.push(await sincronizar());")
    ko = _programa(_api(sync="falla"), "pedidas.push(await sincronizar());")
    assert ok["pedidas"][-1] is True and ko["pedidas"][-1] is False


def test_f054_r1_el_boton_de_sync_llama_a_sincronizar_y_traer():
    cuerpo = _funcion("enlazarEventos")
    assert ('$("#btn-sync").addEventListener("click", () => '
            'sincronizarYTraer());' in cuerpo)


def _casillas(html: str) -> list[tuple[str, str, str, bool]]:
    return [(m.group(1), m.group(2), m.group(3), m.group(4) is not None)
            for m in re.finditer(
                r'<input type="checkbox" class="chk-traer" '
                r'data-trabajador="(\d+)" data-obra="(\d+)" '
                r'data-postventa="([01])"( checked)?>', html)]


def test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid():
    r = _programa(_api(), "await traerDeSigrid([]);")
    html = r["modal"]["html"]
    assert _casillas(html) == [("10", "694", "0", False),
                               ("10", "713", "0", True),
                               ("10", "678", "1", True)]
    assert html.count('class="chk-traer"') == 3
    assert "Aceptar las marcadas" in html


def test_f054_r28_la_ventana_pinta_lo_que_manda_la_api():
    r = _programa(_api(), "await traerDeSigrid([]);")
    html = r["modal"]["html"]
    assert "10 · Ana" in html
    assert "0694 OBRA &lt;X&gt;" in html and "<X>" not in html
    assert "0678 OBRA &lt;X&gt; (postventa)" in html
    for texto in ("distinta", "solo en Sigrid", "solo en el cuadrante",
                  "igual", "no se puede traer", "95%", "60%",
                  "parte PT26/9", "partida CI.1.5",
                  "el porcentaje de Sigrid (120.00) no está en (0, 100]",
                  "12 líneas leídas", "1 de la obra de pruebas",
                  "3 de recursos vinculados", "2 de recursos fuera del maestro",
                  "pv sin catálogo",
                  "el trabajador no está vigente en 09/2026"):
        assert texto in html, texto
    assert r["escuchas"] == {"#btn-traer-aceptar": ["click"],
                             "#btn-traer-cerrar": ["click"]}


def test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar():
    datos = {**DATOS, "trabajadores": [{**DATOS["trabajadores"][0],
                                        "entradas": [_entrada(720, "igual",
                                                              sig=20,
                                                              cua=20)]}]}
    r = _programa(_api(datos=datos), "await traerDeSigrid([]);")
    assert "chk-traer" not in r["modal"]["html"]
    assert "btn-traer-aceptar" not in r["modal"]["html"]
    assert r["escuchas"] == {"#btn-traer-cerrar": ["click"]}


def test_f054_r28_sin_pulsar_no_se_manda_nada():
    r = _programa(_api(), "await traerDeSigrid([]);")
    assert r["pedidas"] == [[RUTA, {"aceptar": []}]]
    assert r["avisos"] == []


def test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga():
    r = _programa(_api(), "\n".join([
        "await traerDeSigrid([]);",
        "marcadas = [{ trabajador: '10', obra: '713', postventa: '0' },",
        "            { trabajador: '10', obra: '678', postventa: '1' }];",
        "await botones['#btn-traer-aceptar'].escuchas.click();",
        "await new Promise((ok) => setTimeout(ok, 0));"]))
    assert r["pedidas"] == [
        [RUTA, {"aceptar": []}],
        ["querySelectorAll", "#modal-registro .chk-traer:checked"],
        [RUTA, {"aceptar": [
            {"trabajador_ide": 10, "obra_ide": 713, "es_postventa": False},
            {"trabajador_ide": 10, "obra_ide": 678, "es_postventa": True}]}],
        "cerrarModal", ["propuestas", True], "cargarPeriodo"]
    assert r["avisos"] == [
        ["Traídas de Sigrid: 1 · 1 sin traer: solo en el cuadrante", True]]


def test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda():
    r = _programa(_api(), "\n".join([
        "await traerDeSigrid([]);",
        "await botones['#btn-traer-aceptar'].escuchas.click();"]))
    assert [p for p in r["pedidas"] if p and p[0] == RUTA] == [
        [RUTA, {"aceptar": []}]]
    assert r["avisos"] == [["No hay ninguna entrada marcada", True]]
    assert r["modal"]["abierto"] is True


def test_f054_r28_un_error_se_avisa_sin_recargar():
    r = _programa(_api(traer="falla"), "await traerDeSigrid([{a: 1}]);")
    assert r["avisos"] == [
        ["No se pudo comparar con Sigrid: transfer caido", True]]
    assert "cargarPeriodo" not in r["pedidas"]
    assert r["modal"]["abierto"] is False


def test_f054_r28_el_front_no_compara():
    """El estado sale de la API: ninguna función de F-054 mira los %."""
    for f in ("pintarTraerSigrid", "filaEntradaSigrid", "traerDeSigrid"):
        assert not re.search(r"pct_\w+\s*[<>=!-]", _funcion(f)), f
    assert "function compararSigrid" not in JS


# ---- T17: lo que la campaña de mutación de `app.js` dejó vivo ---- #
def test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya():
    """Sin % (null en el JSON o la clave ausente), «—»; nunca `null` ni
    `undefined` en la celda."""
    sin_clave = _entrada(740, "solo_sigrid", sig=7)
    del sin_clave["pct_cuadrante"]
    datos = {**DATOS, "trabajadores": [{**DATOS["trabajadores"][0],
                                        "entradas": [
                                            _entrada(713, "solo_sigrid",
                                                     sig=5),
                                            sin_clave]}]}
    r = _programa(_api(datos=datos), "await traerDeSigrid([]);")
    html = r["modal"]["html"]
    assert html.count("<td>—</td>") == 2
    assert "null" not in html and "undefined" not in html


def test_f054_r28_los_avisos_de_postventa_y_de_var():
    datos = {**DATOS, "motivo_postventa": "pv sin catálogo",
             "motivo_var": "var sin catálogo"}
    r = _programa(_api(datos=datos), "await traerDeSigrid([]);")
    html = r["modal"]["html"]
    assert '<p class="aviso">pv sin catálogo</p>' in html
    assert '<p class="aviso">var sin catálogo</p>' in html


def test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores():
    vacio = _programa(_api(datos={**DATOS, "trabajadores": []}),
                      "await traerDeSigrid([]);")["modal"]["html"]
    lleno = _programa(_api(), "await traerDeSigrid([]);")["modal"]["html"]
    texto = "Ningún trabajador del cuadrante tiene porcentajes en Sigrid"
    assert texto in vacio and texto not in lleno
