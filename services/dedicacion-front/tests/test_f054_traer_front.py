# tests/test_f054_traer_front.py
"""F-054 · T9 y T23: el front de «traer de Sigrid» (R1, R28, R39-R42; §7).

Tras un sync con éxito, `sincronizarYTraer` pide comparar (`traerDeSigrid`
con `aceptar` vacío); tras uno fallido, no (R1). La ventana pinta lo que
manda la API en **una sola tabla** (T23, R39): una fila por entrada con
estado y los dos %, y una casilla solo en las `distinta` y las
`solo_sigrid`, las dos **desmarcadas** (D12 revisada el 2026-11-02). Se
ordena por cabecera (R40) y se filtra (R41) sin tocar las casillas;
«Desmarcar todas», «Marcar las visibles» y «Aceptar N marcadas (K ocultas
por el filtro)» (R42). Aceptar manda exactamente las marcadas, también las
ocultas, y recarga; sin pulsarlo no se manda nada; un error se avisa (R28).
El front no compara ni decide.

Se ejecutan las funciones REALES de `app.js` en node con dobles de `api`,
`toast`, `$`, `document` y `cargarPeriodo`; sin `node` se saltan con su
motivo. `test_f061_recarga.py` no cambia: `sincronizar` sigue igual y solo
gana su `true` / `false`. Sin red ni BBDD.
"""
from __future__ import annotations

import html
import json
import re

import pytest

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


#: Índice de cada entrada en la respuesta (el `data-fila` de su casilla):
#: Ana 0-5, Bea 6-7. Casilla en 1, 2, 3, 6 y 7.
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
                             "(0, 100]")]},
        {"trabajador_ide": 20, "cod": "7", "nombre": "Bea <B>",
         "aceptadas": [], "entradas": [
             _entrada(694, "solo_sigrid", sig=30),
             _entrada(801, "distinta", sig=50, cua=10, motivo="ojo <m>")]}],
    "aceptadas": 0, "rechazadas": [],
    "no_traidas": [{"hmores_ide": 1, "recurso_ide": 30, "obra_cod": "0694",
                    "parte_cod": "PT26/1", "can": 0.5,
                    "motivo": "el trabajador no está vigente en 09/2026",
                    "recurso_cod": "30", "recurso_nombre": "Carla"}],
    "fuera_maestro": 2, "de_vinculados": 3, "lineas_leidas": 12,
    "excluidas_pruebas": 1, "motivo_postventa": "pv sin catálogo",
    "motivo_var": None, "propuestas_en_curso": False}

#: Dobles comunes: lo que se pide a la api, los avisos, el modal y sus
#: elementos (con sus escuchas y lo que se repinta en ellos). `ordenar`,
#: `filtrar`, `casilla` y `pulsar` mandan los eventos que daría el
#: navegador (también los que la ventana debe ignorar); `anota` guarda el
#: texto del botón de aceptar.
DOBLES = r"""
var state = { anio: 2026, mes: 9 };
var pedidas = []; var avisos = []; var modal = { abierto: false, html: "" };
var boton = { disabled: false, textContent: "" };
var botones = {}; var textos = [];
function El() {
  this.escuchas = {}; this.innerHTML = null; this.textContent = null;
  this.campos = [{ value: "x" }, { value: "distinta" }]; this.consulta = null;
}
El.prototype.addEventListener = function (t, f) { this.escuchas[t] = f; };
El.prototype.querySelectorAll = function (sel) {
  this.consulta = sel; return this.campos;
};
function evento(sel, tipo, target, extra) {
  botones[sel].escuchas[tipo](Object.assign({ target }, extra));
}
// T24: el título lleva su flecha en un `span`: el clic se busca en su `th`.
function ordenarEn(tabla, col) {
  evento(tabla + "-titulos", "click", { closest: (s) =>
    (col && s === "[data-orden]" ? { dataset: { orden: col } } : null) });
}
function ordenar(col) { ordenarEn("#traer", col); }
function filtrarEn(tabla, k, v) {
  evento(tabla + "-filtros", "input", { dataset: { filtro: k }, value: v });
}
function filtrar(k, v) { filtrarEn("#traer", k, v); }
// T24 (R43): una tecla en un filtro; devuelve cómo queda su valor.
function teclear(tabla, key, k, v, tag) {
  const t = { dataset: { filtro: k }, value: v, tagName: tag || "INPUT" };
  evento(tabla + "-filtros", "keydown", t, { key });
  return t.value;
}
function casilla(i, v) {
  evento("#traer-cuerpo", "change", { dataset: { fila: String(i) }, checked: v });
}
function pulsar(sel) { return botones[sel].escuchas.click(); }
function anota() { textos.push(botones["#btn-traer-aceptar"].textContent); }
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
function fmtPct(v) { return String(v).replace(".", ",") + "%"; }
"""

FUNCIONES = ("escapeHtml", "sincronizar", "sincronizarYTraer",
             "traerDeSigrid", "textoEstadoSigrid", "modeloTraerSigrid",
             "filasTraerVisibles", "textoAceptarTraer", "textoBotonTraer",
             "filaEntradaSigrid", "cuerpoTraerSigrid", "titulosOrdenables",
             "titulosTraerSigrid", "titulosNoTraidas", "celdaFiltroTraer",
             "agruparNoTraidas", "noTraidasVisibles", "filaNoTraida",
             "cuerpoNoTraidas", "enlazarCabeceraTraer",
             "pintarTraerSigrid", "aceptadasMarcadas", "abrirTraerSigrid")


def _programa(api: str, cuerpo: str) -> object:
    return _node("\n".join([
        DOM_TEXTO, DOBLES, api, *[_funcion(f) for f in FUNCIONES],
        "(async () => {", cuerpo,
        "process.stdout.write(JSON.stringify({ pedidas, avisos, modal,",
        "  textos, escuchas: Object.fromEntries(Object.entries(botones)",
        "    .filter(([k, v]) => Object.keys(v.escuchas).length)",
        "    .map(([k, v]) => [k, Object.keys(v.escuchas)])),",
        "  els: Object.fromEntries(Object.entries(botones).map(([k, v]) =>",
        "    [k, { innerHTML: v.innerHTML, textContent: v.textContent,",
        "      campos: v.campos.map((c) => c.value), consulta: v.consulta }]))",
        "}));",
        "})();"]))


def _api(sync="ok", traer="ok", datos=DATOS, estado=0) -> str:
    return "\n".join([
        "async function api(ruta, op) {",
        "  pedidas.push([ruta, op && op.body ? JSON.parse(op.body) : null]);",
        (f"  if (ruta === '/sync') {{ if ('{sync}' === 'falla') "
         "throw new Error('sin sigrid');"),
        f"    return {SYNC_OK}; }}",
        f"  if ('{traer}' === 'falla') throw new Error('transfer caido');",
        f"  if ({estado}) throw Object.assign(new Error('periodo'),",
        f"    {{ status: {estado} }});",
        "  const d = " + json.dumps(datos, ensure_ascii=False) + ";",
        "  return op && JSON.parse(op.body).aceptar.length ? Object.assign(d,",
        "    { aceptadas: 1, rechazadas: [{ trabajador_ide: 10, obra_ide: 678,",
        "      es_postventa: false, motivo: 'solo en el cuadrante' }],",
        "      propuestas_en_curso: true }) : d;",
        "}"])


RUTA = "/periodos/2026/9/traer-sigrid"

#: T24 (R43): las escuchas de la cabecera de cada tabla de la ventana.
ESCUCHAS_TABLA = {"#traer-titulos": ["click"],
                  "#traer-filtros": ["input", "keydown"],
                  "#traer-limpiar": ["click"]}
ESCUCHAS_NO_TRAIDAS = {"#no-traidas-titulos": ["click"],
                       "#no-traidas-filtros": ["input", "keydown"],
                       "#no-traidas-limpiar": ["click"]}


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


def _casillas(html: str) -> list[tuple[str, bool]]:
    return [(m.group(1), m.group(2) is not None)
            for m in re.finditer(
                r'<input type="checkbox" class="chk-traer" '
                r'data-fila="(\d+)"( checked)?>', html)]


def test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid():
    """T9 cambiado por T23 (D12 revisada el 2026-11-02): la `solo_sigrid`
    sale desmarcada, como la `distinta`; ninguna `checked` al abrir."""
    r = _programa(_api(), "await traerDeSigrid([]);")
    html = r["modal"]["html"]
    assert _casillas(html) == [("1", False), ("2", False), ("3", False),
                               ("6", False), ("7", False)]
    assert html.count('class="chk-traer"') == 5
    assert "checked" not in html
    assert ">Aceptar 0 marcadas</button>" in html


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
    # T24 cambia este test de T9/T23: los filtros ganan Escape y las dos
    # tablas, su «Limpiar»; «No se traen» es una tabla con sus escuchas.
    assert r["escuchas"] == {"#btn-traer-aceptar": ["click"],
                             "#btn-traer-desmarcar": ["click"],
                             "#btn-traer-marcar": ["click"],
                             **ESCUCHAS_TABLA, **ESCUCHAS_NO_TRAIDAS,
                             "#traer-cuerpo": ["change"],
                             "#btn-traer-cerrar": ["click"]}


def test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar():
    datos = {**DATOS, "trabajadores": [{**DATOS["trabajadores"][0],
                                        "entradas": [_entrada(720, "igual",
                                                              sig=20,
                                                              cua=20)]}]}
    r = _programa(_api(datos=datos), "await traerDeSigrid([]);")
    html = r["modal"]["html"]
    assert "chk-traer" not in html
    for boton in ("btn-traer-aceptar", "btn-traer-desmarcar",
                  "btn-traer-marcar"):
        assert boton not in html, boton
    assert "Aceptar" not in html and "Marcar" not in html
    assert r["escuchas"] == {**ESCUCHAS_TABLA, **ESCUCHAS_NO_TRAIDAS,
                             "#traer-cuerpo": ["change"],
                             "#btn-traer-cerrar": ["click"]}


def test_f054_r28_sin_pulsar_no_se_manda_nada():
    """Ni al abrir ni al marcar, filtrar, ordenar o (des)marcar en bloque."""
    r = _programa(_api(), """
        await traerDeSigrid([]);
        casilla(2, true); filtrar("obra", "07"); ordenar("obra");
        pulsar("#btn-traer-marcar"); pulsar("#btn-traer-desmarcar");""")
    assert r["pedidas"] == [[RUTA, {"aceptar": []}]]
    assert r["avisos"] == []


def test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga():
    """T9 cambiado por T23: se manda lo marcado en el modelo, en el orden
    de la respuesta y con el cuerpo de hoy, también lo oculto por el
    filtro (la 678 postventa y la 801 de Bea) y sin lo desmarcado."""
    r = _programa(_api(), """
        await traerDeSigrid([]);
        casilla(2, true); casilla(7, true); casilla(3, true);
        casilla(1, true); casilla(1, false);
        filtrar("obra", "0713"); ordenar("sigrid");
        await pulsar("#btn-traer-aceptar");
        await new Promise((ok) => setTimeout(ok, 0));""")
    assert r["pedidas"] == [
        [RUTA, {"aceptar": []}],
        [RUTA, {"aceptar": [
            {"trabajador_ide": 10, "obra_ide": 713, "es_postventa": False},
            {"trabajador_ide": 10, "obra_ide": 678, "es_postventa": True},
            {"trabajador_ide": 20, "obra_ide": 801, "es_postventa": False}]}],
        "cerrarModal", ["propuestas", True], "cargarPeriodo"]
    assert r["avisos"] == [
        ["Traídas de Sigrid: 1 · 1 sin traer: solo en el cuadrante", True]]


def test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda():
    r = _programa(_api(), """
        await traerDeSigrid([]);
        await botones['#btn-traer-aceptar'].escuchas.click();""")
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
    """El estado sale de la API: ninguna función de F-054 mira los % (solo
    `filasTraerVisibles` los ordena, R40)."""
    for f in ("pintarTraerSigrid", "filaEntradaSigrid", "traerDeSigrid",
              "modeloTraerSigrid", "cuerpoTraerSigrid", "filasTraerVisibles",
              "abrirTraerSigrid"):
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


# ---- O5 (review 1): mes cerrado o sin periodo, sin aviso rojo ---- #
@pytest.mark.parametrize("estado", [404, 409])
def test_f054_o5_comparar_en_mes_cerrado_o_sin_periodo_no_avisa(estado):
    r = _programa(_api(estado=estado), "await traerDeSigrid([]);")
    assert r["avisos"] == []
    assert r["modal"]["abierto"] is False


@pytest.mark.parametrize("estado", [404, 409, 502])
def test_f054_o5_aceptar_si_avisa_del_error(estado):
    """El 409 al aceptar es un cierre entre medias: no se ha guardado."""
    r = _programa(_api(estado=estado), """
        await traerDeSigrid([{ trabajador_ide: 10, obra_ide: 713,
                               es_postventa: false }]);""")
    assert r["avisos"] == [["No se pudo comparar con Sigrid: periodo", True]]


def test_f054_o5_comparar_con_otro_error_si_avisa():
    r = _programa(_api(estado=502), "await traerDeSigrid([]);")
    assert r["avisos"] == [["No se pudo comparar con Sigrid: periodo", True]]


def test_f054_o5_api_deja_el_codigo_http_en_el_error():
    programa = "\n".join([
        "function conEmpresa(r) { return r; }",
        "async function fetch() { return { ok: false, status: 409,",
        "  json: async () => ({ error: 'cerrado' }) }; }",
        _funcion("api"),
        "api('/x').catch((e) => process.stdout.write(JSON.stringify(",
        "  [e.message, e.status])));"])
    assert _node(programa) == ["cerrado", 409]


# ---- T23: una sola tabla, orden, filtros y marcado en bloque ---- #
ESTADOS = {"igual": "igual", "distinta": "distinta",
           "solo_sigrid": "solo en Sigrid",
           "solo_cuadrante": "solo en el cuadrante",
           "no_traducible": "no se puede traer"}


def _cuerpo(r: dict) -> str:
    """El `<tbody>` repintado o, si no se ha repintado, el de la ventana."""
    el = r["els"].get("#traer-cuerpo")
    if el and el["innerHTML"] is not None:
        return el["innerHTML"]
    return (r["modal"]["html"].split('<tbody id="traer-cuerpo">')[1]
            .split("</tbody>")[0])


def _filas(r: dict) -> list[list[str]]:
    return [re.findall(r"<td[^>]*>(.*?)</td>", f)
            for f in re.findall(r"<tr>(.*?)</tr>", _cuerpo(r))]


def _ides(r: dict, datos: dict = DATOS) -> list[int]:
    """Cada fila pintada, por su índice en la respuesta (por Trabajador,
    Obra y Estado, que no se repiten en los datos de prueba)."""
    claves = {}
    for t in datos["trabajadores"]:
        for e in t["entradas"]:
            obra = (f"{e['cod']} {e['descripcion']}"
                    f"{' (postventa)' if e['es_postventa'] else ''}")
            claves[(html.escape(f"{t['cod']} · {t['nombre']}", quote=False),
                    html.escape(obra, quote=False),
                    ESTADOS[e["estado"]])] = len(claves)
    return [claves[tuple(f[1:4])] for f in _filas(r) if len(f) == 7]


def _orden(cuerpo: str, datos: dict = DATOS) -> list[int]:
    r = _programa(_api(datos=datos), "await traerDeSigrid([]);\n" + cuerpo)
    return _ides(r, datos)


def _marcadas(r: dict) -> list[str]:
    return [i for i, marcada in _casillas(_cuerpo(r)) if marcada]


def test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos():
    """T24 cambia este test de T23: la cabecera estándar (`th-sort`) y, con
    `no_traidas`, la segunda tabla, la de «No se traen» (R44)."""
    r = _programa(_api(), "await traerDeSigrid([]);")
    pagina = r["modal"]["html"]
    assert pagina.count("<table") == 2
    assert pagina.count('<tbody id="traer-cuerpo">') == 1
    entradas = pagina.split('<tbody id="traer-cuerpo">')[0].rsplit("<table", 1)[1]
    assert entradas.startswith(' class="tabla-reg filterable"')
    assert re.findall(r'<th class="th-sort" data-orden="(\w+)">([^<]*)<span',
                      entradas) == [
        ("trabajador", "Trabajador"), ("obra", "Obra"), ("estado", "Estado"),
        ("cuadrante", "Cuadrante"), ("sigrid", "Sigrid"),
        ("detalle", "Detalle")]
    assert not re.search(r"<h3>[^<]*(Ana|Bea)", pagina)
    assert _ides(r) == list(range(8))
    filas = _filas(r)
    assert filas[0] == ["", "10 · Ana", "0678 OBRA &lt;X&gt;",
                        "solo en el cuadrante", "40%", "—", ""]
    assert filas[3][2] == "0678 OBRA &lt;X&gt; (postventa)"
    assert filas[7][1:] == ["7 · Bea &lt;B&gt;", "0801 OBRA &lt;X&gt;",
                            "distinta", "10%", "50%",
                            "parte PT26/9 · partida CI.1.5 · ojo &lt;m&gt;"]
    assert "<B>" not in pagina and "<m>" not in pagina


def test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte():
    assert _orden('ordenar("obra");') == [0, 3, 1, 6, 2, 4, 5, 7]
    # descendente; el empate de la 0694 (1 y 6) sigue en el de la respuesta
    assert _orden('ordenar("obra"); ordenar("obra");') == [
        7, 5, 4, 2, 1, 6, 3, 0]
    assert _orden('ordenar("obra"); ordenar("obra"); ordenar("obra");') == [
        0, 3, 1, 6, 2, 4, 5, 7]
    # otra columna empieza siempre ascendente
    assert _orden('ordenar("obra"); ordenar("trabajador");') == list(range(8))
    assert _orden('ordenar("trabajador"); ordenar("trabajador");') == [
        6, 7, 0, 1, 2, 3, 4, 5]


def test_f054_r40_la_cabecera_de_la_casilla_no_ordena():
    assert _orden('ordenar("sigrid"); ordenar();') == [2, 3, 4, 6, 7, 1, 5, 0]


def test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final():
    assert _orden('ordenar("sigrid");') == [2, 3, 4, 6, 7, 1, 5, 0]
    assert _orden('ordenar("sigrid"); ordenar("sigrid");') == [
        5, 1, 7, 6, 4, 3, 2, 0]
    assert _orden('ordenar("cuadrante");') == [7, 4, 0, 1, 2, 3, 5, 6]
    assert _orden('ordenar("cuadrante"); ordenar("cuadrante");') == [
        1, 0, 4, 7, 2, 3, 5, 6]
    # el orden anterior no se queda en el modelo: el empate, el de la respuesta
    assert _orden('ordenar("sigrid"); ordenar("sigrid"); '
                  'ordenar("cuadrante");') == [7, 4, 0, 1, 2, 3, 5, 6]


def test_f054_r40_la_raya_tambien_si_falta_el_porcentaje():
    sin_clave = _entrada(740, "solo_sigrid", sig=7)
    del sin_clave["pct_sigrid"]
    datos = {**DATOS, "trabajadores": [{**DATOS["trabajadores"][0],
                                        "entradas": [
                                            sin_clave,
                                            _entrada(713, "solo_sigrid",
                                                     sig=5),
                                            _entrada(720, "igual", sig=20,
                                                     cua=20)]}]}
    assert _orden('ordenar("sigrid");', datos) == [1, 2, 0]
    assert _orden('ordenar("sigrid"); ordenar("sigrid");', datos) == [2, 1, 0]


def test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable():
    datos = {**DATOS, "trabajadores": [{**DATOS["trabajadores"][0],
                                        "entradas": [
                                            _entrada(901, "no_traducible",
                                                     motivo="Zeta"),
                                            _entrada(902, "no_traducible",
                                                     motivo="ALFA"),
                                            _entrada(903, "no_traducible",
                                                     motivo="alfa")]}]}
    assert _orden('ordenar("detalle");', datos) == [1, 2, 0]
    assert _orden('ordenar("detalle"); ordenar("detalle");', datos) == [
        0, 1, 2]


def test_f054_r40_la_columna_ordenada_lleva_su_marca():
    r = _programa(_api(), """
        await traerDeSigrid([]);
        ordenar("obra"); textos.push(botones["#traer-titulos"].innerHTML);
        ordenar("obra"); textos.push(botones["#traer-titulos"].innerHTML);
        ordenar("estado"); textos.push(botones["#traer-titulos"].innerHTML);""")
    assert "▲" not in r["modal"]["html"] and "▼" not in r["modal"]["html"]
    asc, desc, estado = r["textos"]
    flecha = '<span class="sort-arrow">{}</span></th>'
    assert 'data-orden="obra">Obra' + flecha.format(" ▲") in asc
    assert "▼" not in asc
    assert 'data-orden="obra">Obra' + flecha.format(" ▼") in desc
    assert "▲" not in desc
    assert 'data-orden="estado">Estado' + flecha.format(" ▲") in estado
    assert 'data-orden="obra">Obra' + flecha.format("") in estado
    assert asc.startswith("<th></th>")


def test_f054_r41_filtro_de_obra_deja_solo_esa_obra():
    r = _programa(_api(), """
        await traerDeSigrid([]); filtrar("obra", "0694"); anota();""")
    assert _ides(r) == [1, 6]
    assert r["textos"] == ["Aceptar 0 marcadas"]


def test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado():
    assert _orden('filtrar("trabajador", "7 · bEA");') == [6, 7]
    assert _orden('filtrar("obra", "(POSTVENTA)");') == [3]
    assert _orden('filtrar("detalle", "NO ESTÁ EN");') == [5]
    assert _orden('filtrar("detalle", "PT26/9 · PARTIDA");') == [
        1, 2, 3, 4, 5, 6, 7]


def test_f054_r41_desplegable_de_estado_y_filtros_combinados():
    pagina = _programa(_api(), "await traerDeSigrid([]);")["modal"]["html"]
    filtros = pagina.split('id="traer-filtros"')[1].split("</tr>")[0]
    assert re.findall(r'<input class="col-filter" type="text" '
                      r'data-filtro="(\w+)"', filtros) == [
        "trabajador", "obra", "detalle"]
    assert '<select class="col-filter" data-filtro="estado">' in filtros
    assert re.findall(r'<option value="(\w*)">([^<]*)</option>', pagina) == [
        ("", "Todos"), ("distinta", "distinta"),
        ("solo_sigrid", "solo en Sigrid"), ("igual", "igual"),
        ("solo_cuadrante", "solo en el cuadrante"),
        ("no_traducible", "no se puede traer")]
    assert _orden('filtrar("estado", "solo_sigrid");') == [2, 3, 6]
    assert _orden('filtrar("estado", "solo_sigrid"); '
                  'filtrar("trabajador", "ana");') == [2, 3]
    assert _orden('filtrar("estado", "solo_sigrid"); '
                  'filtrar("trabajador", "ana"); filtrar("estado", "");') == [
        0, 1, 2, 3, 4, 5]
    assert _orden('filtrar("estado", "distinta"); filtrar("obra", "08"); '
                  'filtrar("detalle", "ojo");') == [7]


def test_f054_r41_sin_filas_visibles_lo_dice():
    r = _programa(_api(), 'await traerDeSigrid([]); filtrar("obra", "9999");')
    assert _cuerpo(r) == ('<tr><td colspan="7" class="motivo">Ninguna '
                          'entrada con estos filtros.</td></tr>')
    assert "Ninguna entrada" not in r["modal"]["html"]


def test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas():
    r = _programa(_api(), """
        await traerDeSigrid([]);
        casilla(1, true); casilla(6, true);
        filtrar("obra", "0713"); ordenar("sigrid"); filtrar("obra", "");
        casilla(2, true); casilla(2, false); anota();""")
    assert _ides(r) == [2, 3, 4, 6, 7, 1, 5, 0]
    assert _marcadas(r) == ["6", "1"]
    assert r["textos"] == ["Aceptar 2 marcadas"]


def test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas():
    r = _programa(_api(), """
        await traerDeSigrid([]);
        casilla(1, true); casilla(7, true); filtrar("obra", "0694"); anota();
        pulsar("#btn-traer-desmarcar"); anota();
        filtrar("obra", ""); anota();
        await pulsar("#btn-traer-aceptar");""")
    assert r["textos"] == ["Aceptar 2 marcadas (1 ocultas por el filtro)",
                           "Aceptar 0 marcadas", "Aceptar 0 marcadas"]
    assert len(_casillas(_cuerpo(r))) == 5 and _marcadas(r) == []
    assert r["avisos"] == [["No hay ninguna entrada marcada", True]]
    assert [p for p in r["pedidas"] if p and p[0] == RUTA] == [
        [RUTA, {"aceptar": []}]]


def test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla():
    r = _programa(_api(), """
        await traerDeSigrid([]);
        filtrar("trabajador", "ana"); pulsar("#btn-traer-marcar"); anota();
        filtrar("trabajador", ""); anota();
        await pulsar("#btn-traer-aceptar");
        await new Promise((ok) => setTimeout(ok, 0));""")
    assert r["textos"] == ["Aceptar 3 marcadas", "Aceptar 3 marcadas"]
    assert _marcadas(r) == ["1", "2", "3"]
    assert r["pedidas"][1] == [RUTA, {"aceptar": [
        {"trabajador_ide": 10, "obra_ide": 694, "es_postventa": False},
        {"trabajador_ide": 10, "obra_ide": 713, "es_postventa": False},
        {"trabajador_ide": 10, "obra_ide": 678, "es_postventa": True}]}]


def test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas():
    r = _programa(_api(), """
        await traerDeSigrid([]);
        casilla(1, true); anota(); casilla(7, true); anota();
        filtrar("obra", "0694"); anota();
        casilla(6, true); anota(); casilla(1, false); anota();
        ordenar("obra"); anota(); filtrar("obra", ""); anota();""")
    assert r["textos"] == [
        "Aceptar 1 marcadas", "Aceptar 2 marcadas",
        "Aceptar 2 marcadas (1 ocultas por el filtro)",
        "Aceptar 3 marcadas (1 ocultas por el filtro)",
        "Aceptar 2 marcadas (1 ocultas por el filtro)",
        "Aceptar 2 marcadas (1 ocultas por el filtro)",
        "Aceptar 2 marcadas"]


def test_f054_r42_texto_del_boton_de_aceptar():
    programa = "\n".join([
        _funcion("textoAceptarTraer"),
        "process.stdout.write(JSON.stringify([textoAceptarTraer(0, 0),",
        "  textoAceptarTraer(4, 0), textoAceptarTraer(4, 1),",
        "  textoAceptarTraer(4, 4)]));"])
    assert _node(programa) == [
        "Aceptar 0 marcadas", "Aceptar 4 marcadas",
        "Aceptar 4 marcadas (1 ocultas por el filtro)",
        "Aceptar 4 marcadas (4 ocultas por el filtro)"]


# ---- T23, campaña 5 de mutación manual: D11 y D51 vivos ---- #
def test_f054_r41_al_abrir_ningun_filtro_esta_puesto():
    """Ningún filtro viene puesto: tras ordenar se ven todas las filas
    (descripciones sin letras comunes, para que ningún texto inicial las
    deje pasar por casualidad) y los campos de filtro salen vacíos."""
    datos = {**DATOS, "trabajadores": [{**DATOS["trabajadores"][0],
                                        "entradas": [
                                            {**_entrada(713, "solo_sigrid",
                                                        sig=5),
                                             "descripcion": "1"},
                                            {**_entrada(720, "igual", sig=20,
                                                        cua=20),
                                             "descripcion": "2"}]}]}
    r = _programa(_api(datos=datos), 'await traerDeSigrid([]); ordenar("obra");')
    assert _ides(r, datos) == [0, 1]
    assert "value=" not in r["modal"]["html"].split('id="traer-filtros"')[1]         .split("</tr>")[0].replace('<option value="', "")


def test_f054_r39_sin_entradas_no_hay_tabla():
    """T24 cambia este test de T23: «No se traen» es una tabla aparte."""
    r = _programa(_api(datos={**DATOS, "trabajadores": [], "no_traidas": []}),
                  "await traerDeSigrid([]);")
    assert "<table" not in r["modal"]["html"]
    assert r["escuchas"] == {"#btn-traer-cerrar": ["click"]}
    r = _programa(_api(datos={**DATOS, "trabajadores": []}),
                  "await traerDeSigrid([]);")
    assert r["modal"]["html"].count("<table") == 1
    assert "traer-cuerpo" not in r["modal"]["html"]
    assert r["escuchas"] == {**ESCUCHAS_NO_TRAIDAS,
                             "#btn-traer-cerrar": ["click"]}


# ---- T24 (R43-R45, D20-D21): cabecera estándar y «No se traen» en tabla ---- #
def _no_traida(hmores, recurso, obra, parte, motivo, *, cod="", nombre=""):
    """La forma de `NoTraidaOut` (api, T25): `recurso_cod` y
    `recurso_nombre` nulos si el recurso no está en el maestro."""
    return {"hmores_ide": hmores, "recurso_ide": recurso, "obra_cod": obra,
            "parte_cod": parte, "can": 0.5, "motivo": motivo,
            "recurso_cod": cod or None, "recurso_nombre": nombre or None}


#: Tres líneas iguales (parte, obra, recurso y motivo) y otras que difieren
#: en una sola de esas claves cada una, más una sin parte ni obra.
NO_TRAIDAS = [
    _no_traida(1, 1671338, "POSTV2", "PT26/00028",
               "la partida 11 casa con 0708 y 0713", cod="1671", nombre="Pía"),
    _no_traida(2, 30, "0708", "PT26/00030", "la obra 0708 no se ofrece normal",
               cod="30", nombre="Carla <C>"),
    _no_traida(3, 1671338, "POSTV2", "PT26/00028",
               "la partida 11 casa con 0708 y 0713", cod="1671", nombre="Pía"),
    _no_traida(4, 1671338, "POSTV2", "PT26/00029",
               "la partida 11 casa con 0708 y 0713", cod="1671", nombre="Pía"),
    _no_traida(5, 77, None, None, "Zeta <z>"),
    _no_traida(6, 1671338, "POSTV2", "PT26/00028",
               "la partida 11 casa con 0708 y 0713", cod="1671", nombre="Pía"),
    _no_traida(7, 1671338, "POSTV2", "PT26/00028", "otro motivo",
               cod="1671", nombre="Pía"),
]
DATOS_NT = {**DATOS, "no_traidas": NO_TRAIDAS}


def _cuerpo_nt(r: dict) -> str:
    el = r["els"].get("#no-traidas-cuerpo")
    if el and el["innerHTML"] is not None:
        return el["innerHTML"]
    return (r["modal"]["html"].split('<tbody id="no-traidas-cuerpo">')[1]
            .split("</tbody>")[0])


def _filas_nt(r: dict) -> list[list[str]]:
    return [re.findall(r"<td[^>]*>(.*?)</td>", f)
            for f in re.findall(r"<tr>(.*?)</tr>", _cuerpo_nt(r))]


def _partes_nt(cuerpo: str) -> list[tuple[str, str]]:
    """(Parte, Motivo) de cada fila, en el orden pintado."""
    r = _programa(_api(datos=DATOS_NT), "await traerDeSigrid([]);\n" + cuerpo)
    return [(f[0], f[4]) for f in _filas_nt(r) if len(f) == 5]


def _tabla(pagina: str, cuerpo: str) -> str:
    """La `<table>` cuyo `<tbody>` tiene ese `id`."""
    antes, despues = pagina.split(f'<tbody id="{cuerpo}">')
    return ("<table" + antes.rsplit("<table", 1)[1] + f'<tbody id="{cuerpo}">'
            + despues.split("</table>")[0])


def test_f054_r43_las_dos_tablas_con_la_cabecera_estandar():
    pagina = _programa(_api(), "await traerDeSigrid([]);")["modal"]["html"]
    entradas = _tabla(pagina, "traer-cuerpo")
    no_traidas = _tabla(pagina, "no-traidas-cuerpo")
    for tabla, titulos, ids in (
            (entradas, [("trabajador", "Trabajador"), ("obra", "Obra"),
                        ("estado", "Estado"), ("cuadrante", "Cuadrante"),
                        ("sigrid", "Sigrid"), ("detalle", "Detalle")],
             "traer"),
            (no_traidas, [("parte", "Parte"), ("obra", "Obra"),
                          ("recurso", "Recurso"), ("lineas", "Líneas"),
                          ("motivo", "Motivo")], "no-traidas")):
        assert tabla.startswith('<table class="tabla-reg filterable"><thead>')
        assert re.findall(r'<th class="th-sort" data-orden="(\w+)">([^<]*)'
                          r'<span class="sort-arrow"></span></th>',
                          tabla) == titulos
        assert tabla.count("th-sort") == len(titulos)
        assert f'<tr id="{ids}-titulos">' in tabla
        filtros = (tabla.split(f'<tr id="{ids}-filtros" class="filter-row">')[1]
                   .split("</tr>")[0])
        assert filtros.count("<th") == len(titulos) + (ids == "traer")
        assert filtros.count('<div class="filtro-celda">') == (
            filtros.count('class="col-filter"'))
        assert filtros.count('<button type="button" class="filter-clear" '
                             f'id="{ids}-limpiar">Limpiar</button>') == 1
        assert filtros.count("filter-clear") == 1
        # «Limpiar», en la última columna, junto a su filtro
        ultima = filtros.split("<th")[-1]
        assert 'class="col-filter"' in ultima and "Limpiar" in ultima
    # la casilla no ordena: su título va vacío, sin `th-sort`
    assert entradas.split('<tr id="traer-titulos">')[1].startswith("<th></th>")
    filtros = entradas.split('class="filter-row">')[1].split("</tr>")[0]
    assert re.findall(r'<th>(<div class="filtro-celda">)<(input|select) '
                      r'class="col-filter"(?: type="text")? '
                      r'data-filtro="(\w+)"', filtros) == [
        ('<div class="filtro-celda">', "input", "trabajador"),
        ('<div class="filtro-celda">', "input", "obra"),
        ('<div class="filtro-celda">', "select", "estado"),
        ('<div class="filtro-celda">', "input", "detalle")]
    assert filtros.count("<th></th>") == 3
    assert re.findall(r'<input class="col-filter" type="text" '
                      r'data-filtro="(\w+)" placeholder="Contiene…">',
                      no_traidas) == ["parte", "obra", "recurso", "motivo"]
    filtros_nt = no_traidas.split('class="filter-row">')[1].split("</tr>")[0]
    assert filtros_nt.split("<th")[4] == "></th>"   # Líneas, sin filtro


def test_f054_r43_fuera_los_selectores_de_t23():
    """Ni las clases de T23 en `app.js` ni sus reglas en `styles.css`
    (`ordenable` sigue en `COLUMNAS`: es la propiedad de la tabla principal,
    no una clase); las reglas estándar, intactas."""
    from tests.test_f042_sugerencias import CSS
    for viejo in ("filtro-traer", 'class="ordenable"', 'type="search"',
                  "tabla-traer"):
        assert viejo not in JS, viejo
    for viejo in (".ordenable", ".filtro-traer", "#traer-filtros",
                  ".tabla-traer"):
        assert viejo not in CSS, viejo
    for estandar in (".filterable thead tr:first-child th.th-sort",
                     ".filterable thead tr:first-child th .sort-arrow",
                     ".filter-row .col-filter {", ".filtro-celda {",
                     ".filter-clear {", ".modal .acciones-traer {"):
        assert estandar in CSS, estandar


def test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna():
    """El clic se busca con `closest("[data-orden]")`: en el `span` de la
    flecha ordena por su `th`; en la casilla (sin `data-orden`), nada."""
    assert 'ev.target.closest("[data-orden]")' in _funcion(
        "enlazarCabeceraTraer")
    assert _orden('ordenar("sigrid"); ordenar();') == [2, 3, 4, 6, 7, 1, 5, 0]


def test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla():
    r = _programa(_api(datos=DATOS_NT), """
        await traerDeSigrid([]);
        casilla(1, true); casilla(7, true); ordenar("sigrid");
        filtrar("obra", "0694"); filtrar("estado", "distinta");
        filtrarEn("#no-traidas", "parte", "00028"); anota();
        pulsar("#traer-limpiar"); anota();""")
    assert r["textos"] == ["Aceptar 2 marcadas (1 ocultas por el filtro)",
                           "Aceptar 2 marcadas"]
    # todas las filas, con el orden de antes y las casillas como estaban
    assert _ides(r) == [2, 3, 4, 6, 7, 1, 5, 0]
    assert _marcadas(r) == ["7", "1"]
    assert r["els"]["#traer-titulos"]["innerHTML"].count(" ▲") == 1
    # los campos de esa fila de filtros, vacíos (Estado, «Todos»)
    assert r["els"]["#traer-filtros"]["consulta"] == ".col-filter"
    assert r["els"]["#traer-filtros"]["campos"] == ["", ""]
    # la otra tabla, ni tocada
    assert r["els"]["#no-traidas-filtros"]["campos"] == ["x", "distinta"]
    assert r["els"]["#no-traidas-filtros"]["consulta"] is None
    assert len(_filas_nt(r)) == 2
    assert r["pedidas"] == [[RUTA, {"aceptar": []}]]


def test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla():
    """Cada filtro de la tabla, también los que no se han tocado."""
    r = _programa(_api(datos=DATOS_NT), """
        await traerDeSigrid([]);
        filtrar("trabajador", "ana"); filtrar("detalle", "zz");
        pulsar("#traer-limpiar");""")
    assert _ides(r) == list(range(8))
    r = _programa(_api(datos=DATOS_NT), """
        await traerDeSigrid([]);
        filtrarEn("#no-traidas", "obra", "zz");
        filtrarEn("#no-traidas", "recurso", "zz");
        pulsar("#no-traidas-limpiar");""")
    assert len(_filas_nt(r)) == 5


def test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra():
    r = _programa(_api(datos=DATOS_NT), """
        await traerDeSigrid([]);
        filtrar("obra", "0694"); ordenarEn("#no-traidas", "parte");
        filtrarEn("#no-traidas", "parte", "00028");
        filtrarEn("#no-traidas", "motivo", "OTRO"); anota();
        pulsar("#no-traidas-limpiar");""")
    assert [f[0] for f in _filas_nt(r)] == [
        "—", "PT26/00028", "PT26/00028", "PT26/00029", "PT26/00030"]
    assert r["els"]["#no-traidas-filtros"]["campos"] == ["", ""]
    assert r["els"]["#no-traidas-filtros"]["consulta"] == ".col-filter"
    assert r["els"]["#traer-filtros"]["consulta"] is None
    assert _ides(r) == [1, 6]
    assert r["textos"] == ["Aceptar 0 marcadas"]


def test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta():
    r = _programa(_api(datos=DATOS_NT), """
        await traerDeSigrid([]);
        filtrar("obra", "0694"); casilla(1, true); casilla(7, true); anota();
        textos.push(teclear("#traer", "Enter", "obra", "0694"));
        textos.push(teclear("#traer", "Escape", "estado", "distinta", "SELECT"));
        anota();
        textos.push(teclear("#traer", "Escape", "obra", "0694")); anota();
        filtrarEn("#no-traidas", "motivo", "otro");
        textos.push(teclear("#no-traidas", "Escape", "motivo", "otro"));""")
    assert r["textos"] == [
        "Aceptar 2 marcadas (1 ocultas por el filtro)", "0694", "distinta",
        "Aceptar 2 marcadas (1 ocultas por el filtro)", "",
        "Aceptar 2 marcadas", ""]
    assert _ides(r) == list(range(8))
    assert len(_filas_nt(r)) == 5
    assert r["modal"]["abierto"] is True
    assert "cerrarModal" not in r["pedidas"]


def test_f054_r44_agrupar_no_traidas():
    programa = "\n".join([
        DOM_TEXTO, _funcion("agruparNoTraidas"),
        "process.stdout.write(JSON.stringify(agruparNoTraidas(" +
        json.dumps(NO_TRAIDAS, ensure_ascii=False) + ")));"])
    assert _node(programa) == [
        {"i": 0, "n": 3, "textos": {
            "parte": "PT26/00028", "obra": "POSTV2", "recurso": "1671 · Pía",
            "motivo": "la partida 11 casa con 0708 y 0713"}},
        {"i": 1, "n": 1, "textos": {
            "parte": "PT26/00030", "obra": "0708", "recurso": "30 · Carla <C>",
            "motivo": "la obra 0708 no se ofrece normal"}},
        {"i": 2, "n": 1, "textos": {
            "parte": "PT26/00029", "obra": "POSTV2", "recurso": "1671 · Pía",
            "motivo": "la partida 11 casa con 0708 y 0713"}},
        {"i": 3, "n": 1, "textos": {
            "parte": "—", "obra": "—", "recurso": "77", "motivo": "Zeta <z>"}},
        {"i": 4, "n": 1, "textos": {
            "parte": "PT26/00028", "obra": "POSTV2", "recurso": "1671 · Pía",
            "motivo": "otro motivo"}}]


def test_f054_r44_el_recurso_distingue_por_su_ide():
    """Mismo parte, obra y motivo, y otro recurso con el mismo código: dos
    filas (la clave es el `recurso_ide`, no lo pintado)."""
    nt = [_no_traida(1, 5, "0708", "P", "m", cod="9", nombre="X"),
          _no_traida(2, 6, "0708", "P", "m", cod="9", nombre="X"),
          _no_traida(3, 5, "0708", "P", "m", cod="9", nombre="X")]
    r = _programa(_api(datos={**DATOS, "no_traidas": nt}),
                  "await traerDeSigrid([]);")
    assert [f[3] for f in _filas_nt(r)] == ["×2", ""]
    assert "<h3>No se traen (2)</h3>" in r["modal"]["html"]


def test_f054_r44_no_se_traen_en_una_tabla_agrupada():
    r = _programa(_api(datos=DATOS_NT), "await traerDeSigrid([]);")
    pagina = r["modal"]["html"]
    assert "<h3>No se traen (5)</h3>" in pagina
    assert "<ul>" not in pagina and "<li>" not in pagina
    assert _filas_nt(r) == [
        ["PT26/00028", "POSTV2", "1671 · Pía", "×3",
         "la partida 11 casa con 0708 y 0713"],
        ["PT26/00030", "0708", "30 · Carla &lt;C&gt;", "",
         "la obra 0708 no se ofrece normal"],
        ["PT26/00029", "POSTV2", "1671 · Pía", "",
         "la partida 11 casa con 0708 y 0713"],
        ["—", "—", "77", "", "Zeta &lt;z&gt;"],
        ["PT26/00028", "POSTV2", "1671 · Pía", "", "otro motivo"]]
    tabla = _tabla(pagina, "no-traidas-cuerpo")
    assert "checkbox" not in tabla and "<C>" not in pagina
    assert "<z>" not in pagina


def test_f054_r44_dos_iguales_y_una_distinta_dos_filas():
    nt = [_no_traida(1, 30, "0708", "P1", "m", cod="30", nombre="C"),
          _no_traida(2, 30, "0708", "P1", "m", cod="30", nombre="C"),
          _no_traida(3, 30, "0708", "P1", "n", cod="30", nombre="C")]
    r = _programa(_api(datos={**DATOS, "no_traidas": nt}),
                  "await traerDeSigrid([]);")
    assert "<h3>No se traen (2)</h3>" in r["modal"]["html"]
    assert [(f[3], f[4]) for f in _filas_nt(r)] == [("×2", "m"), ("", "n")]


def test_f054_r44_sin_no_traidas_ni_la_seccion():
    for datos in ({**DATOS, "no_traidas": []},
                  {k: v for k, v in DATOS.items() if k != "no_traidas"}):
        pagina = _programa(_api(datos=datos),
                           "await traerDeSigrid([]);")["modal"]["html"]
        assert "No se traen" not in pagina
        assert "no-traidas" not in pagina
        assert pagina.count("<table") == 1


def test_f054_r44_ordena_cada_columna_y_la_segunda_invierte():
    ab = [("PT26/00028", "la partida 11 casa con 0708 y 0713"),
          ("PT26/00030", "la obra 0708 no se ofrece normal"),
          ("PT26/00029", "la partida 11 casa con 0708 y 0713"),
          ("—", "Zeta &lt;z&gt;"), ("PT26/00028", "otro motivo")]
    g0, g1, g2, g3, g4 = ab
    o = 'ordenarEn("#no-traidas", "{}"); '
    assert _partes_nt("") == ab
    assert _partes_nt(o.format("parte")) == [g3, g0, g4, g2, g1]
    assert _partes_nt(o.format("parte") * 2) == [g1, g2, g0, g4, g3]
    assert _partes_nt(o.format("obra")) == [g3, g1, g0, g2, g4]
    assert _partes_nt(o.format("recurso")) == [g0, g2, g4, g1, g3]
    # Motivo sin distinguir mayúsculas: «Zeta» al final
    assert _partes_nt(o.format("motivo")) == [g1, g0, g2, g4, g3]
    assert _partes_nt(o.format("motivo") * 2) == [g3, g4, g0, g2, g1]
    # Líneas, numérica; el empate, en el orden de la primera línea
    assert _partes_nt(o.format("lineas")) == [g1, g2, g3, g4, g0]
    assert _partes_nt(o.format("lineas") * 2) == [g0, g1, g2, g3, g4]
    # otra columna empieza ascendente; el orden no toca la otra tabla
    assert _partes_nt(o.format("lineas") * 2 + o.format("parte")) == [
        g3, g0, g4, g2, g1]
    assert _orden(o.format("parte")) == list(range(8))


def test_f054_r44_la_columna_ordenada_lleva_su_marca():
    r = _programa(_api(datos=DATOS_NT), """
        await traerDeSigrid([]); ordenarEn("#no-traidas", "lineas");
        textos.push(botones["#no-traidas-titulos"].innerHTML);
        ordenarEn("#no-traidas", "lineas");
        textos.push(botones["#no-traidas-titulos"].innerHTML);""")
    asc, desc = r["textos"]
    assert ('data-orden="lineas">Líneas<span class="sort-arrow"> ▲</span>'
            in asc) and "▼" not in asc
    assert ('data-orden="lineas">Líneas<span class="sort-arrow"> ▼</span>'
            in desc) and "▲" not in desc
    assert asc.startswith('<th class="th-sort" data-orden="parte">')
    assert r["els"]["#traer-titulos"]["innerHTML"] is None


def test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados():
    def partes(cuerpo):
        return [p for p, _ in _partes_nt(cuerpo)]
    f = 'filtrarEn("#no-traidas", '
    assert partes(f + '"parte", "pt26/0002");') == [
        "PT26/00028", "PT26/00029", "PT26/00028"]
    assert partes(f + '"obra", "postv");') == [
        "PT26/00028", "PT26/00029", "PT26/00028"]
    assert partes(f + '"recurso", "CARLA <c");') == ["PT26/00030"]
    assert partes(f + '"motivo", "ZETA");') == ["—"]
    assert partes(f + '"parte", "00028"); ' + f + '"motivo", "OTRO");') == [
        "PT26/00028"]
    assert partes(f + '"parte", "00028"); ' + f + '"motivo", "OTRO"); ' +
                  f + '"parte", "");') == ["PT26/00028"]
    assert partes(f + '"obra", "99");') == []
    r = _programa(_api(datos=DATOS_NT), "await traerDeSigrid([]);\n" +
                  f + '"obra", "99");')
    assert _cuerpo_nt(r) == ('<tr><td colspan="5" class="motivo">Ninguna '
                             'línea con estos filtros.</td></tr>')
    # filtrar «No se traen» no toca la tabla de entradas ni su botón
    r = _programa(_api(datos=DATOS_NT), "await traerDeSigrid([]);\n" +
                  'casilla(1, true); ' + f + '"obra", "99"); anota();')
    assert _ides(r) == list(range(8)) and r["textos"] == ["Aceptar 1 marcadas"]


def test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide():
    nt = [_no_traida(1, 30, "0708", "P", "m", cod="30", nombre="Carla <C>"),
          _no_traida(2, 1671338, "0708", "P", "m")]
    r = _programa(_api(datos={**DATOS, "no_traidas": nt}),
                  "await traerDeSigrid([]);")
    assert [f[2] for f in _filas_nt(r)] == ["30 · Carla &lt;C&gt;", "1671338"]


# ---- T24, campaña 7 de mutación manual: E4, E6 y E28 vivos ---- #
def test_f054_r44_cada_clave_del_grupo_distingue():
    """Igual parte, recurso y motivo y otra obra: dos filas (E6); y así con
    cada clave por separado."""
    base = dict(hmores=1, recurso=30, obra="0708", parte="P", motivo="m")
    variantes = [{}, {"obra": "0713"}, {"parte": "Q"}, {"recurso": 31},
                 {"motivo": "n"}, {}]
    nt = [_no_traida(**{**base, **v, "hmores": i}) for i, v in
          enumerate(variantes)]
    r = _programa(_api(datos={**DATOS, "no_traidas": nt}),
                  "await traerDeSigrid([]);")
    assert [(f[0], f[1], f[2], f[3], f[4]) for f in _filas_nt(r)] == [
        ("P", "0708", "30", "×2", "m"), ("P", "0713", "30", "", "m"),
        ("Q", "0708", "30", "", "m"), ("P", "0708", "31", "", "m"),
        ("P", "0708", "30", "", "n")]


def test_f054_r44_ordenar_texto_sin_distinguir_mayusculas_empate_estable():
    """«ALFA» y «alfa» empatan (E28): en los dos sentidos, el de la
    respuesta."""
    nt = [_no_traida(1, 30, "0708", "P", "Zeta"),
          _no_traida(2, 30, "0708", "P", "ALFA"),
          _no_traida(3, 30, "0708", "P", "alfa")]
    datos = {**DATOS, "no_traidas": nt}
    o = 'ordenarEn("#no-traidas", "motivo"); '
    asc = _programa(_api(datos=datos), "await traerDeSigrid([]);\n" + o)
    desc = _programa(_api(datos=datos), "await traerDeSigrid([]);\n" + o * 2)
    assert [f[4] for f in _filas_nt(asc)] == ["ALFA", "alfa", "Zeta"]
    assert [f[4] for f in _filas_nt(desc)] == ["Zeta", "ALFA", "alfa"]


def test_f054_r44_el_filtro_de_recurso_existe_desde_el_principio():
    """Los cuatro filtros de «No se traen» están en el modelo al abrir
    (E4): filtrar por otro no falla y «Limpiar» los recorre todos."""
    r = _programa(_api(datos=DATOS_NT), """
        await traerDeSigrid([]); filtrarEn("#no-traidas", "parte", "00028");""")
    assert len(_filas_nt(r)) == 2
    programa = "\n".join([
        DOM_TEXTO, _funcion("escapeHtml"), _funcion("textoEstadoSigrid"),
        _funcion("agruparNoTraidas"), _funcion("modeloTraerSigrid"),
        "process.stdout.write(JSON.stringify(modeloTraerSigrid({ "
        "trabajadores: [], no_traidas: [] }).noTraidas.filtros));"])
    assert _node(programa) == {"parte": "", "obra": "", "recurso": "",
                               "motivo": ""}


def test_f054_r44_parte_y_obra_escapadas():
    """E46 y E49: todos los textos de la fila se escapan."""
    nt = [_no_traida(1, 30, "O<b>", "P<a>", "m", cod="30", nombre="C")]
    r = _programa(_api(datos={**DATOS, "no_traidas": nt}),
                  "await traerDeSigrid([]);")
    assert _filas_nt(r)[0][:2] == ["P&lt;a&gt;", "O&lt;b&gt;"]
    assert "<a>" not in r["modal"]["html"] and "<b>" not in r["modal"]["html"]


# ---- T27 (R48, rehecha el 2026-11-06): la ventana en tres zonas ---- #
# Arriba, quieto y opaco: título, resumen, avisos y botones de marcado (el
# fondo de `.modal`, que deja de desplazarse). En medio, `.zona-traer`, lo
# único que se desplaza: las dos tablas enteras, con su `thead` fijo en
# `top: 0` (arranca en su sitio, bajo los botones, y comparte columnas con
# el cuerpo). Abajo, el pie. La primera versión (`c9611c3`, `thead` sticky
# dentro de `.modal` con `top` negativo) no gustó: se subía al borde.
SELECTORES_R48 = {
    "columna": [".modal:has(> .zona-traer)"],
    "hijos": [".modal:has(> .zona-traer) > *"],
    "zona": [".modal:has(> .zona-traer) > .zona-traer"],
    "cabecera": [".zona-traer thead"],
    "bordes": [".zona-traer .tabla-reg"],
}
DECLARACIONES_R48 = {
    "columna": {"display": "flex", "flex-direction": "column",
                "overflow": "hidden"},
    "hijos": {"flex": "none"},
    "zona": {"flex": "0 1 auto", "min-height": "0", "overflow": "auto"},
    "cabecera": {"position": "sticky", "top": "0", "z-index": "2",
                 "background": "var(--paper)"},
    # Retoque del 2026-11-06 (MANUAL T18 paso 2): con bordes colapsados,
    # el borde es de la rejilla y no viaja con el `thead` fijo; entre
    # títulos y filtros quedaba 1 px por el que se veían pasar las filas.
    "bordes": {"border-collapse": "separate", "border-spacing": "0"},
}


def _reglas_css() -> list[tuple[list[str], dict[str, str]]]:
    """Las reglas de `styles.css` (sin comentarios ni `@media`), como
    (selectores, {propiedad: valor})."""
    from tests.test_f042_sugerencias import CSS
    css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.DOTALL)
    reglas = []
    for sel, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        sel = sel.rsplit("{", 1)[-1]
        decl = dict((p.strip(), v.strip()) for p, v in (
            d.split(":", 1) for d in cuerpo.split(";") if ":" in d))
        reglas.append(([" ".join(s.split()) for s in sel.split(",")], decl))
    return reglas


@pytest.mark.parametrize("zona", list(SELECTORES_R48))
def test_f054_r48_las_reglas_de_las_tres_zonas(zona):
    """(a)-(d) de T27, con exactamente esos selectores y declaraciones."""
    reglas = [d for s, d in _reglas_css() if s == SELECTORES_R48[zona]]
    assert len(reglas) == 1, f"falta (o sobra) la regla «{zona}» de T27"
    assert reglas[0] == DECLARACIONES_R48[zona]


def test_f054_r48_ninguna_otra_regla_toca_la_zona():
    """Solo esas cinco reglas nombran `.zona-traer`."""
    con_zona = [s for s, _ in _reglas_css()
                if any("zona-traer" in x for x in s)]
    assert sorted(map(tuple, con_zona)) == sorted(
        tuple(s) for s in SELECTORES_R48.values())


def test_f054_r48_los_bordes_viajan_con_la_cabecera_sin_dobles():
    """Bordes separados: cada celda lleva el suyo y viaja con el `thead`
    fijo (sin franja entre títulos y filtros). La regla va después de
    `.modal .tabla-reg` (misma especificidad: si fuera antes, perdería) y
    ninguna regla de `th`/`td` de esas tablas pone borde arriba ni a la
    izquierda: con `separate` los bordes no se funden y saldrían dobles."""
    reglas = _reglas_css()
    selectores = [s for s, _ in reglas]
    assert selectores.index(SELECTORES_R48["bordes"]) > selectores.index(
        [".modal .tabla-reg"])
    for sel, decl in reglas:
        for s in sel:
            ultimo = s.split()[-1] if s.split() else ""
            if (any(c in s for c in (".tabla-reg", ".filterable", ".filter-row"))
                    and re.match(r"(th|td)([.:\[]|$)", ultimo)):
                assert not {"border", "border-top", "border-left",
                            "border-width"} & set(decl), (s, decl)


def test_f054_r48_el_modal_vuelve_a_su_padding_y_fuera_la_primera_version():
    from tests.test_f042_sugerencias import CSS
    modal = [d for s, d in _reglas_css() if s == [".modal"]]
    assert modal, "falta la regla `.modal`"
    assert modal[0]["padding"] == "22px 26px"
    assert modal[0]["max-height"] == "86vh" and modal[0]["overflow"] == "auto"
    assert all("padding" not in d and "padding-top" not in d
               for d in modal[1:]), "otra regla `.modal` redefine el padding"
    for texto in (CSS, JS):
        assert "--modal-pad-top" not in texto
        assert "thead:has(" not in texto


def test_f054_r48_solo_dos_reglas_sticky():
    """La `.topbar` de siempre y el `thead` de la zona; ninguna sobre
    `.modal`, `thead`, `.filterable` o `.filter-row` en general."""
    fijas = [(s, d) for s, d in _reglas_css()
             if "sticky" in d.get("position", "")]
    assert [s for s, _ in fijas] == [[".topbar"], SELECTORES_R48["cabecera"]]
    assert {k: fijas[0][1][k] for k in ("position", "top", "z-index")} == {
        "position": "sticky", "top": "0", "z-index": "20"}


def test_f054_r48_cada_th_de_las_dos_filas_trae_fondo_opaco():
    """El `thead` fijo es opaco, pero también cada celda: los títulos (con
    la casilla vacía) por `.filterable thead tr:first-child th` y los
    filtros (con las vacías y la de «Limpiar») por `.filter-row th`."""
    reglas = _reglas_css()
    fondos = {s[0]: d.get("background") for s, d in reglas if len(s) == 1}
    assert fondos[".filterable thead tr:first-child th"] == "var(--brand)"
    assert fondos[".filter-row th"] == "var(--paper)"
    pagina = _programa(_api(datos=DATOS_NT),
                       "await traerDeSigrid([]);")["modal"]["html"]
    for tabla in ("traer", "no-traidas"):
        thead = re.search(rf'<thead><tr id="{tabla}-titulos">.*?</thead>',
                          pagina, re.DOTALL).group(0)
        filas = re.findall(r"<tr[^>]*>", thead)
        assert filas == [f'<tr id="{tabla}-titulos">',
                         f'<tr id="{tabla}-filtros" class="filter-row">']


ZONA = '<div class="zona-traer" id="traer-zona">'


def _zonas(pagina: str) -> tuple[str, str, str]:
    """(antes, dentro, después) de la zona; `dentro` hasta el `</div>` que
    la cierra (el pie empieza justo después)."""
    assert pagina.count(ZONA) == 1, "la zona, una vez"
    antes, resto = pagina.split(ZONA)
    i = resto.rindex('<div class="pie-modal">')
    dentro, despues = resto[:i], resto[i:]
    assert dentro.endswith("</div>"), "el pie, justo después de la zona"
    return antes, dentro[:-len("</div>")], despues


def test_f054_r48_las_tablas_dentro_de_la_zona_y_lo_demas_fuera():
    datos = {**DATOS_NT, "motivo_var": "var sin catálogo"}
    pagina = _programa(_api(datos=datos),
                       "await traerDeSigrid([]);")["modal"]["html"]
    antes, dentro, despues = _zonas(pagina)
    assert dentro.count("<table") == 2 and "<h3>No se traen (" in dentro
    assert dentro.index('id="traer-cuerpo"') < dentro.index("<h3>No se traen")
    assert dentro.startswith('<table class="tabla-reg filterable">')
    for fuera in ("<h2>", '<p class="aviso">pv sin catálogo</p>',
                  '<p class="aviso">var sin catálogo</p>',
                  '<div class="acciones-traer">', 'id="btn-traer-marcar"'):
        assert fuera in antes and fuera not in dentro + despues, fuera
    assert "<table" not in antes + despues
    assert despues.startswith('<div class="pie-modal">')
    assert 'id="btn-traer-aceptar"' in despues
    assert "pie-modal" not in antes + dentro
    assert (pagina.index("acciones-traer") < pagina.index(ZONA)
            < pagina.index("pie-modal"))


def test_f054_r48_sin_no_se_traen_la_zona_con_la_tabla_principal():
    pagina = _programa(_api(datos={**DATOS, "no_traidas": []}),
                       "await traerDeSigrid([]);")["modal"]["html"]
    _, dentro, _ = _zonas(pagina)
    assert dentro.count("<table") == 1 and 'id="traer-cuerpo"' in dentro
    assert "No se traen" not in dentro


def test_f054_r48_sin_entradas_la_zona_con_no_se_traen():
    pagina = _programa(_api(datos={**DATOS_NT, "trabajadores": []}),
                       "await traerDeSigrid([]);")["modal"]["html"]
    antes, dentro, _ = _zonas(pagina)
    assert dentro.startswith("<h3>No se traen (")
    assert dentro.count("<table") == 1
    assert "Ningún trabajador del cuadrante" in antes


def test_f054_r48_sin_nada_la_zona_vacia_y_el_pie():
    pagina = _programa(_api(datos={**DATOS, "trabajadores": [],
                                   "no_traidas": []}),
                       "await traerDeSigrid([]);")["modal"]["html"]
    _, dentro, despues = _zonas(pagina)
    assert dentro == ""
    assert despues.startswith('<div class="pie-modal">')


def test_f054_r48_la_zona_es_hija_directa_del_modal():
    """`.modal:has(> .zona-traer)`: lo que pinta `pintarTraerSigrid` va tal
    cual dentro de `.modal` (`abrirModal`), así que la zona no puede ir
    anidada en otro `div`: antes de ella, todo `<div>` está cerrado."""
    pagina = _programa(_api(datos=DATOS_NT),
                       "await traerDeSigrid([]);")["modal"]["html"]
    antes, _, _ = _zonas(pagina)
    assert antes.count("<div") == antes.count("</div>")
    assert '<div class="modal">${html}</div>' in _funcion("abrirModal")


def test_f054_r48_los_id_van_en_la_primera_fila_hija_del_thead():
    """Cada `id` de cabecera, una vez y en su `thead` (las escuchas)."""
    pagina = _programa(_api(datos=DATOS_NT),
                       "await traerDeSigrid([]);")["modal"]["html"]
    for ids in ("traer-titulos", "no-traidas-titulos"):
        assert pagina.count(f'id="{ids}"') == 1
        assert f'<thead><tr id="{ids}">' in pagina


def test_f054_r48_el_modal_del_registro_no_lleva_la_zona():
    from tests.test_f054_modal_cero import _escenario, _pf
    html = _escenario("await abrir(D.pf); obs.html = dom.html;",
                      {"pf": _pf()})["html"]
    assert "<thead>" in html and "pie-modal" in html
    assert "zona-traer" not in html
    assert "traer-titulos" not in html and "no-traidas-titulos" not in html
    assert "zona-traer" not in _funcion("pintarModalPreflight")
