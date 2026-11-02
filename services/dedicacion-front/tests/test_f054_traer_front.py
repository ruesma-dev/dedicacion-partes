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
                    "motivo": "el trabajador no está vigente en 09/2026"}],
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
function El() { this.escuchas = {}; this.innerHTML = null; this.textContent = null; }
El.prototype.addEventListener = function (t, f) { this.escuchas[t] = f; };
function evento(sel, tipo, target) { botones[sel].escuchas[tipo]({ target }); }
function ordenar(col) {
  evento("#traer-titulos", "click", { dataset: col ? { orden: col } : {} });
}
function filtrar(k, v) {
  evento("#traer-filtros", "input", { dataset: { filtro: k }, value: v });
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
             "filaEntradaSigrid", "cuerpoTraerSigrid", "titulosTraerSigrid",
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
        "    [k, { innerHTML: v.innerHTML, textContent: v.textContent }])) }));",
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
    assert r["escuchas"] == {"#btn-traer-aceptar": ["click"],
                             "#btn-traer-desmarcar": ["click"],
                             "#btn-traer-marcar": ["click"],
                             "#traer-titulos": ["click"],
                             "#traer-filtros": ["input"],
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
    assert r["escuchas"] == {"#traer-titulos": ["click"],
                             "#traer-filtros": ["input"],
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
    r = _programa(_api(), "await traerDeSigrid([]);")
    pagina = r["modal"]["html"]
    assert pagina.count("<table") == 1
    assert '<table class="tabla-reg tabla-traer"' in pagina
    assert re.findall(r'<th class="ordenable" data-orden="(\w+)">([^<]*)</th>',
                      pagina) == [
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
    assert 'data-orden="obra">Obra ▲</th>' in asc and "▼" not in asc
    assert 'data-orden="obra">Obra ▼</th>' in desc and "▲" not in desc
    assert 'data-orden="estado">Estado ▲</th>' in estado
    assert 'data-orden="obra">Obra</th>' in estado
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
    assert re.findall(r'<input type="search" class="filtro-traer" '
                      r'data-filtro="(\w+)"', pagina) == [
        "trabajador", "obra", "detalle"]
    assert '<select class="filtro-traer" data-filtro="estado">' in pagina
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
