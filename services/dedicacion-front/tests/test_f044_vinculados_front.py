# tests/test_f044_vinculados_front.py
"""F-044 · T7: columna «Tipo recurso», subfilas de los vinculados y su
selector de partida en el cuadrante (R6-R9).

El front solo pinta lo que manda la api (`lineas[].vinculados`): el % de la
subfila es el de su línea y no se edita (R7), su partida es la elegida o la
propuesta guardada en cursiva con su método (R9) y se cambia con el selector
de F-050 con `vinculado_ide` (R8). Código REAL de `app.js` en `node` con el
DOM de mentira de F-050 (M2) y comprobaciones estáticas. Sin `node`, los de
lógica se saltan con su motivo; el reviewer los exige `passed`. Sin red.
"""
from __future__ import annotations

import json
import re

from tests.test_f050_m2_arreglos import (
    CSS,
    DOM,
    ESCAPE,
    SELECTOR,
    _const,
    _funcion,
    _node,
    _plano,
)

TEL = {"vinculado_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
       "cod": "TF-10", "partida_ide": None, "partida_cod": None,
       "partida_res": None, "partida_fija": False,
       "propuesta_cod": "CICO13", "propuesta_res": "TELEFONIA",
       "propuesta_metodo": "ci_tipo"}
GAS = {**TEL, "vinculado_ide": 11, "tipo": "CO", "tipo_res": "GASOIL",
       "cod": "CO-11", "partida_ide": 81002, "partida_cod": "CIGA14",
       "partida_res": "GASOIL", "propuesta_cod": None, "propuesta_res": None,
       "propuesta_metodo": None}


# ============================ R6 · columna =============================== #
def test_f044_r6_columna_tipo_recurso_entre_obras_y_partida():
    columnas = _plano(_const("COLUMNAS"))
    assert ('tipo: { titulo: "Tipo recurso", ancho: 170, ordenable: false, '
            'placeholder: "Filtrar tipo…", },') in columnas
    assert _plano(_const("ORDEN_COLUMNAS_DEFECTO")).endswith(
        '["nombre", "categoria", "asignaciones", "tipo", "partida", '
        '"total"];')
    assert '"tipo"' in _const("COLUMNAS_POR_LINEA")
    assert "tipo: 110" in _const("MINIMO_COLUMNA")


def _texto_tipo(t: dict) -> str:
    return _node("\n".join([
        _funcion("fmtPct"), _funcion("textoColumna"),
        "process.stdout.write(JSON.stringify(textoColumna(" + json.dumps(t)
        + ", 'tipo')));"]))


def test_f044_r6_el_filtro_de_la_columna_ve_persona_y_cada_vinculado():
    assert _texto_tipo({"lineas": []}) == "Persona"
    assert _texto_tipo({"lineas": [{"vinculados": [TEL, GAS]},
                                   {"vinculados": [TEL]}]}) == (
        "Persona TELEFONO TF-10 GASOIL CO-11 TELEFONO TF-10")


# ======================= R6 · filas del trabajador ======================= #
#: `construirFila` y `construirFilaVinculado` REALES con celdas de mentira
#: (como F-030 y F-050 M2): cada `<tr>` apunta sus celdas y su `rowSpan`.
FILA = r"""
function clases() { const s = new Set();
  return {add: (c) => s.add(c), remove: (c) => s.delete(c),
    contains: (c) => s.has(c), lista: () => [...s]}; }
function construirCelda(t, clave, idx) { return {clave, idx, classList: clases()}; }
function construirCeldaVinculado(t, idx, v, clave) {
  return {clave, vin: v.vinculado_ide, classList: clases()}; }
const document = {createDocumentFragment: () => ({trs: [],
  appendChild(tr) { this.trs.push(tr); }}),
  createElement: () => ({dataset: {}, tds: [], _h: {}, set className(c) {
    c.split(" ").forEach((x) => this.classList.add(x)); },
    classList: clases(), appendChild(td) { this.tds.push(td); },
    querySelectorAll(sel) { return sel === "td[rowspan]"
      ? this.tds.filter((td) => td.rowSpan !== undefined) : []; },
    addEventListener(ev, fn) { this._h[ev] = fn; }})};
"""


def _filas(lineas: list, incidencias: int = 0, columnas=None) -> list:
    columnas = columnas or ["nombre", "asignaciones", "tipo", "partida",
                            "total"]
    return _node("\n".join([
        _const("COLUMNAS_POR_LINEA"), FILA, _funcion("construirFila"),
        _funcion("construirFilaVinculado"),
        ("const state = {columnas: " + json.dumps(columnas) + ","
         " seleccionIde: 7, seleccion: new Set(), editandoIde: null,"
         " resaltadas: []};"),
        "const t = {ide: 7, activo: true, lineas: " + json.dumps(lineas) +
        ", incidencias: " + json.dumps([{}] * incidencias) + "};",
        ("const frag = construirFila(t);"
         "process.stdout.write(JSON.stringify(frag.trs.map((tr) => ["
         "tr.classList.lista().sort().join(' '), tr.dataset.linea, "
         "tr.dataset.vinculado === undefined ? null : tr.dataset.vinculado, "
         "tr.tds.map((td) => [td.clave, td.vin === undefined ? td.idx : "
         "'v' + td.vin, td.rowSpan === undefined ? null : td.rowSpan])])));"),
    ]))


def test_f044_r6_una_subfila_por_vinculado_bajo_su_linea():
    filas = _filas([{"obra_ide": 1, "vinculados": [TEL, GAS]},
                    {"obra_ide": 2, "vinculados": []}], incidencias=1)
    assert [(f[0], f[1], f[2]) for f in filas] == [
        ("fila seleccionada", 0, None),
        ("fila fila-vin seleccionada subfila", 0, 10),
        ("fila fila-vin seleccionada subfila", 0, 11),
        ("fila seleccionada subfila", 1, None),
        ("fila fila-inc seleccionada subfila", 2, None)]
    # Las del trabajador abarcan todas; obra, tipo y partida, una por fila.
    assert filas[0][3] == [["nombre", 0, 5], ["asignaciones", 0, None],
                           ["tipo", 0, None], ["partida", 0, None],
                           ["total", 0, 5]]
    assert filas[1][3] == [["asignaciones", "v10", None],
                           ["tipo", "v10", None], ["partida", "v10", None]]


def test_f044_r6_sin_vinculados_las_filas_de_hoy():
    filas = _filas([{"obra_ide": 1}, {"obra_ide": 2}])
    assert [(f[0], f[2]) for f in filas] == [
        ("fila seleccionada", None), ("fila seleccionada subfila", None)]
    assert filas[0][3][0] == ["nombre", 0, 2]


def test_f044_r6_la_subfila_marca_los_bordes_y_el_cursor_como_las_demas():
    filas = _filas([{"obra_ide": 1, "vinculados": [TEL]}],
                   columnas=["asignaciones", "tipo", "partida"])
    assert filas[1][3] == [["asignaciones", "v10", None],
                           ["tipo", "v10", None], ["partida", "v10", None]]
    marcas = _node("\n".join([
        _const("COLUMNAS_POR_LINEA"), FILA, _funcion("construirFila"),
        _funcion("construirFilaVinculado"),
        ("const state = {columnas: ['asignaciones', 'tipo', 'partida'],"
         " seleccionIde: 7, seleccion: new Set(), editandoIde: null,"
         " resaltadas: [], ratonIde: null};"),
        "const t = {ide: 7, activo: true, lineas: [{obra_ide: 1, vinculados: "
        + json.dumps([TEL]) + "}]};",
        "const frag = construirFila(t); const [a, b] = frag.trs;",
        "b._h.mouseenter();",
        ("process.stdout.write(JSON.stringify([b.tds.map((td) => "
         "td.classList.lista()), [a, b].map((tr) => "
         "tr.classList.contains('resaltada')), state.ratonIde]));"),
    ]))
    assert marcas == [[["col-primera"], [], ["col-ultima"]], [True, True], 7]


# ================== R6, R7, R9 · las celdas de la subfila ================ #
CELDA = r"""
function nodoCelda() { const s = new Set(); return {dataset: {}, _h: {},
  innerHTML: "", textContent: "", className: "",
  classList: {add: (c) => s.add(c), contains: (c) => s.has(c),
    lista: () => [...s]},
  addEventListener(ev, fn) { this._h[ev] = fn; }}; }
const document = {createElement: nodoCelda};
const aperturas = [];
function abrirSelectorPartida(t, o, pv, ancla) {
  aperturas.push([t, o, pv, ancla.dataset.vinculado]); }
"""


def _celdas(linea: dict, v: dict, abierto: bool = True) -> dict:
    return _node("\n".join([
        ESCAPE, CELDA, _funcion("etiquetaObra"), _funcion("fmtPct"),
        _funcion("textoPartida"), _funcion("rotuloOrigen"),
        _funcion("htmlPartida"), _funcion("construirCeldaVinculado"),
        "const state = {periodoEstado: " + json.dumps(
            "ABIERTO" if abierto else "CERRADO") + "};",
        "const l = " + json.dumps(linea) + "; const t = {ide: 7, lineas: [l]};",
        "const v = " + json.dumps(v) + ";",
        ("const c = Object.fromEntries(['asignaciones', 'tipo', 'partida']"
         ".map((k) => [k, construirCeldaVinculado(t, 0, v, k)]));"),
        "if (c.partida._h.click) c.partida._h.click({stopPropagation() {}});",
        ("process.stdout.write(JSON.stringify({obra: c.asignaciones.innerHTML,"
         " tipo: c.tipo.innerHTML, partida: c.partida.innerHTML,"
         " clases: c.partida.classList.lista(), dataset: c.partida.dataset,"
         " aperturas}));"),
    ]))


LINEA = {"obra_ide": 694, "cod": "0694", "es_postventa": False,
         "porcentaje": 60, "partida_fija": False, "descripcion": "OBRA"}


def test_f044_r7_el_porcentaje_es_el_de_la_linea_y_no_se_edita():
    obs = _celdas(LINEA, TEL)
    assert "60%" in obs["obra"] and "pct-heredado" in obs["obra"]
    assert "<input" not in obs["obra"]
    assert "0694" in obs["obra"]


def test_f044_r6_tipo_y_codigo_del_vinculado():
    obs = _celdas(LINEA, TEL)
    assert "TELEFONO" in obs["tipo"] and "TF-10" in obs["tipo"]


def test_f044_r9_propuesta_en_cursiva_con_su_metodo_y_elegida_tal_cual():
    prop = _celdas(LINEA, TEL)["partida"]
    assert prop.startswith('<em class="partida-propuesta"')
    assert "CICO13 · TELEFONIA" in prop and "CI del tipo" in prop
    assert _celdas(LINEA, GAS)["partida"] == (
        '<span class="partida-elegida">CIGA14 · GASOIL</span>')
    titular = _celdas(LINEA, {**TEL, "propuesta_metodo": "titular"})
    assert "la del trabajador" in titular["partida"]


def test_f044_r8_el_clic_abre_el_selector_de_esa_subfila():
    obs = _celdas(LINEA, TEL)
    assert obs["aperturas"] == [[7, 694, False, 10]]
    assert "editable" in obs["clases"]
    assert (obs["dataset"]["ide"], obs["dataset"]["linea"],
            obs["dataset"]["vinculado"]) == (7, 0, 10)


def test_f044_r8_fija_en_var_y_sin_selector_con_el_periodo_cerrado():
    fija = _celdas({**LINEA, "partida_fija": True}, {**TEL,
                                                     "partida_fija": True})
    assert "partida-fija" in fija["partida"] and fija["aperturas"] == []
    cerrado = _celdas(LINEA, TEL, abierto=False)
    assert cerrado["aperturas"] == [] and "editable" not in cerrado["clases"]


def test_f044_r7_r9_el_front_no_calcula_partida_ni_porcentaje():
    cuerpo = _funcion("construirCeldaVinculado")
    for prohibido in ("categoria", "resolver", "reshor", "* ", "/ 100",
                      "subcuenta"):
        assert prohibido not in cuerpo, prohibido
    assert "fmtPct(l.porcentaje)" in cuerpo


# ======================= R8 · selector de la subfila ===================== #
def _escenario(cuerpo: str) -> dict:
    return _node("\n".join([
        DOM, ESCAPE, _const("selector"),
        *(_funcion(f) for f in SELECTOR),
        "(async () => { const obs = {};", cuerpo,
        "process.stdout.write(JSON.stringify(obs)); })();"]))


def test_f044_r8_el_selector_pide_y_guarda_la_partida_de_la_subfila():
    obs = _escenario("""
      const a = nodo("td"); a.dataset.vinculado = "10";
      abrirSelectorPartida(77, 694, false, a);
      llamadas[0].res({partidas: [{ide: 81001, cod: "CICO13", res: "T",
        mayor: "CI"}], partidas_postventa: [], ambito: "CI",
        propuesta: null}); await tick();
      const input = paneles()[0]._input;
      input._h.keydown({key: "Enter", preventDefault() {},
        stopPropagation() {}});
      await tick();
      obs.llamadas = llamadas.map((l) => [l.url,
        l.o ? JSON.parse(l.o.body) : null]);
      obs.claves = [...selector.cache.keys()];
    """)
    assert obs["llamadas"] == [
        [("/periodos/2026/9/trabajadores/77/partidas?obra_ide=694"
          "&es_postventa=false&vinculado_ide=10"), None],
        ["/periodos/2026/9/trabajadores/77/partida",
         {"obra_ide": 694, "es_postventa": False, "vinculado_ide": 10,
          "partida": {"ide": 81001, "cod": "CICO13", "res": "T"}}]]


def test_f044_r8_la_subfila_y_su_titular_son_selectores_distintos():
    obs = _escenario("""
      const a = nodo("td"); const b = nodo("td"); b.dataset.vinculado = "10";
      abrirSelectorPartida(77, 694, false, a);
      abrirSelectorPartida(77, 694, false, b);
      obs.n = llamadas.length;
      obs.abierto = selector.abierto;
    """)
    assert obs["n"] == 2 and obs["abierto"].endswith("|v10")


def test_f044_r9_cambiar_el_titular_olvida_los_selectores_de_sus_subfilas():
    obs = _escenario("""
      selector.cache.set(clavePartidas(77, 694, false) + "|v10", {});
      selector.cache.set(clavePartidas(77, 695, false) + "|v10", {});
      const a = nodo("td");
      abrirSelectorPartida(77, 694, false, a);
      llamadas[0].res({partidas: [{ide: 1, cod: "CI.1", res: "R",
        mayor: "CI"}], partidas_postventa: [], ambito: null,
        propuesta: null}); await tick();
      paneles()[0]._input._h.keydown({key: "Enter", preventDefault() {},
        stopPropagation() {}});
      await tick(); llamadas[1].res({}); await tick();
      obs.claves = [...selector.cache.keys()].map((k) => k.split("|")
        .slice(4).join("|"));
    """)
    assert obs["claves"] == ["695|false|v10"]


# ============================ R9 · en segundo plano ====================== #
def test_f044_r9_las_propuestas_de_las_subfilas_llegan_sin_recargar():
    estado = {"trabajadores": [{"ide": 7, "lineas": [
        {"obra_ide": 694, "es_postventa": False, "partida_ide": None,
         "vinculados": [{**TEL, "propuesta_cod": None}, GAS]}]}]}
    r = _node("\n".join([
        _funcion("aplicarPropuestas"),
        "const state = " + json.dumps(estado) + ";",
        ("aplicarPropuestas([], [{trabajador_ide: 7, obra_ide: 694,"
         " es_postventa: false, vinculado_ide: 10, propuesta_cod: 'CICO13',"
         " propuesta_res: 'TELEFONIA', propuesta_metodo: 'ci_tipo'},"
         " {trabajador_ide: 7, obra_ide: 694, es_postventa: false,"
         " vinculado_ide: 11, propuesta_cod: 'X', propuesta_res: 'X',"
         " propuesta_metodo: 'ci_tipo'}]);"),
        ("process.stdout.write(JSON.stringify(state.trabajadores[0].lineas[0]"
         ".vinculados.map((v) => v.propuesta_cod)));"),
    ]))
    assert r == ["CICO13", None]        # la elegida no recibe propuesta


def test_f044_r9_la_consulta_pasa_las_subfilas_y_el_repintado_las_pinta():
    consulta = _plano(_funcion("consultarPropuestas"))
    assert ("aplicarPropuestas(datos.lineas || [], datos.subfilas || []);"
            in consulta)
    repintar = _plano(_funcion("repintarCeldasPartida"))
    assert "td.dataset.vinculado" in repintar
    assert "td.innerHTML = htmlPartida(v);" in repintar


def test_f044_r6_css_de_las_subfilas_de_vinculado():
    assert re.search(r"tr\.fila-vin td\s*\{", CSS)
    assert re.search(r"\.pct-heredado\s*\{", CSS)
    assert re.search(r"td\.celda-tipo\s*\{", CSS)


def test_f044_r6_rotulos_de_los_metodos_del_vinculado():
    r = _node("\n".join([
        _funcion("rotuloOrigen"),
        ("process.stdout.write(JSON.stringify([rotuloOrigen('ci_tipo'),"
         " rotuloOrigen('titular')]));")]))
    assert r == ["CI del tipo", "la del trabajador"]
