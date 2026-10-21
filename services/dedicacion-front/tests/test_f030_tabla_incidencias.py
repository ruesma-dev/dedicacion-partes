# tests/test_f030_tabla_incidencias.py
"""F-030 · Las incidencias en el editor y en la tabla (R14-R16) y en el
modal de registro (R32).

Se ejecuta el código REAL de `app.js` en node con el DOM mínimo de
`test_f042_sugerencias.py` (más lo de la celda de `test_f030_celda_pct.py`).
Sin `node` se saltan con su motivo; el reviewer los exige `passed`. Sin red
ni BBDD.
"""
from __future__ import annotations

import json
import re

from tests.test_f030_celda_pct import DOM_CELDA, DOM_LETRAS
from tests.test_f041_filtro_obra import _orden_estado
from tests.test_f042_sugerencias import CSS, DOM_DE_PRUEBA, JS, _funcion, _node

#: Lo que el editor de incidencias usa y el DOM de prueba no trae: búsqueda
#: en profundidad (`querySelectorAll`) y el periodo (julio de 2026: 31 días).
DOM_EDITOR = r"""
El.prototype.querySelectorAll = function (sel) {
  const clase = sel.slice(1), fuera = [];
  for (const c of this.children) {
    if (c.classList.contains(clase)) fuera.push(c);
    fuera.push(...c.querySelectorAll(sel));
  }
  return fuera;
};
state.anio = 2026; state.mes = 7;
function hijo(el, clase) { return el.children.find((c) => c.classList.contains(clase)); }
function inc(obra_ide, codigo, letra, nombre, desde, hasta) {
  return { obra_ide, cod: "0" + obra_ide, descripcion: "Obra " + obra_ide, codigo,
           letra, nombre, dia_desde: desde, dia_hasta: hasta };
}
"""


def _editor(funciones: tuple[str, ...], cuerpo: str) -> object:
    programa = "\n".join([DOM_DE_PRUEBA, DOM_CELDA, DOM_LETRAS, DOM_EDITOR,
                          *[_funcion(f) for f in funciones],
                          "var resultado;", cuerpo,
                          "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


def _asincrono(funciones: tuple[str, ...], dobles: str, cuerpo: str) -> object:
    """Como `_editor`, con `cuerpo` dentro de una función `async` y los
    `dobles` fuera (globales, para que los vea el código de `app.js`)."""
    programa = "\n".join([DOM_DE_PRUEBA, DOM_CELDA, DOM_LETRAS, DOM_EDITOR,
                          *[_funcion(f) for f in funciones], dobles,
                          "var resultado;", "(async () => {", cuerpo, "})().then(() =>",
                          "process.stdout.write(JSON.stringify(resultado)));"])
    return _node(programa)


CHIP = ("chipIncidencia", "parsearDia")


# ================================ R14 ==================================== #
def test_f030_r14_chip_obra_letra_nombre_del_al_y_quitar():
    r = _editor(CHIP, """
      const editor = nuevoEditor();
      const i = inc(100, "CIV", "V", "Vacaciones", 5, null);
      state.incidenciasEdicion = [i];
      const chip = chipIncidencia(i, 0, editor);
      resultado = { clase: chip.className,
                    partes: chip.children.map((c) => [c.tag, c.className, c.textContent || "",
                                                      c.value || "", c.placeholder || ""]),
                    titulo: hijo(chip, "cod").title };
    """)
    assert r["clase"] == "chip-edit chip-inc"
    assert r["partes"] == [
        ["span", "cod", "0100", "", ""],
        ["span", "inc-tipo", "V Vacaciones", "", ""],
        ["span", "inc-rotulo", "del", "", ""],
        ["input", "inc-dia inc-desde", "", "5", "1"],
        ["span", "inc-rotulo", "al", "", ""],
        ["input", "inc-dia inc-hasta", "", "", "31"],
        ["button", "btn-x", "✕", "", ""]]
    assert r["titulo"] == "Obra 100"
    assert "btn-pv" not in _funcion("chipIncidencia")


def test_f030_r14_enter_del_al_y_buscador_escape_al_buscador():
    r = _editor(CHIP, """
      const editor = nuevoEditor();
      const i = inc(100, "CIV", "V", "Vacaciones", null, null);
      state.incidenciasEdicion = [i];
      const chip = chipIncidencia(i, 0, editor);
      editor.appendChild(chip);
      const del = hijo(chip, "inc-desde"), al = hijo(chip, "inc-hasta");
      del.focus();
      const e1 = del.fire("keydown", "Enter");
      const f1 = foco.className;
      const e2 = al.fire("keydown", "Enter");
      const f2 = foco.className;
      del.focus();
      del.fire("keydown", "Escape");
      const f3 = foco.className;
      al.focus();
      al.fire("keydown", "Escape");
      resultado = { f1, f2, f3, f4: foco.className, previstos: [e1.previsto, e2.previsto],
                    llamadas };
    """)
    assert r == {"f1": "inc-dia inc-hasta", "f2": "obra-input", "f3": "obra-input",
                 "f4": "obra-input", "previstos": [True, True], "llamadas": []}


def test_f030_r14_enfocar_dia_va_al_del_de_esa_incidencia():
    r = _editor(("chipIncidencia", "parsearDia", "enfocarDiaIncidencia"), """
      const editor = nuevoEditor();
      state.incidenciasEdicion = [inc(1, "CIV", "V", "Vacaciones", null, null),
                                  inc(2, "CIE", "B", "Enfermedad", null, null)];
      state.incidenciasEdicion.forEach((i, n) => editor.appendChild(chipIncidencia(i, n, editor)));
      enfocarDiaIncidencia(editor, 1);
      const segundo = foco === hijo(editor.children[3], "inc-desde");
      enfocarDiaIncidencia(editor, 5);
      resultado = { segundo, sigue: foco === hijo(editor.children[3], "inc-desde") };
    """)
    assert r == {"segundo": True, "sigue": True}


# ================================ R15 ==================================== #
def test_f030_r15_dias_y_quitar_guardan_con_el_diferido_y_no_suman():
    r = _editor((*CHIP, "totalEdicion"), """
      const editor = nuevoEditor();
      const otra = linea(2, 60);
      state.edicion = [otra];
      const i = inc(100, "CIV", "V", "Vacaciones", null, null);
      state.incidenciasEdicion = [inc(9, "CIE", "B", "Enfermedad", 1, 2), i];
      const chip = chipIncidencia(i, 1, editor);
      const del = hijo(chip, "inc-desde"), al = hijo(chip, "inc-hasta");
      del.value = " 5 "; del.fire("input");
      al.value = "09"; al.fire("input");
      const dias = [i.dia_desde, i.dia_hasta];
      al.value = ""; al.fire("input");
      del.value = "x"; del.fire("input");
      const vacios = [i.dia_desde, i.dia_hasta];
      del.value = "123"; del.fire("input");
      const largo = i.dia_desde;
      const total = totalEdicion();
      hijo(chip, "btn-x").fire("click");
      resultado = { dias, vacios, largo, total,
                    quedan: state.incidenciasEdicion.map((x) => x.codigo), llamadas };
    """)
    assert r["dias"] == [5, 9]
    assert r["vacios"] == [None, None]
    assert r["largo"] is None
    assert r["total"] == {"suma": 60, "estado": "FALTA"}
    assert r["quedan"] == ["CIE"]
    assert r["llamadas"] == ["programarGuardado"] * 5 + ["pintarEditor", "programarGuardado"]


# ============================ editor (T9) ================================ #
def test_f030_r14_el_editor_pinta_las_incidencias_tras_las_lineas():
    r = _editor(("pintarEditor", "chipIncidencia", "parsearDia", "badgeTotal",
                 "totalEdicion", "fmtPct"), """
      function chipEditable(l) { const c = new El("span"); c.className = "chip-edit"; return c; }
      function montarAutocompletado() {}
      const editor = new El("div");
      state.edicion = [linea(1, 60), linea(2, 40)];
      state.incidenciasEdicion = [inc(3, "CIV", "V", "Vacaciones", 1, 5)];
      state.guardadoPendiente = false;
      pintarEditor(editor);
      resultado = editor.children.map((c) => c.className);
    """)
    assert r[:4] == ["chip-edit", "chip-edit", "chip-edit chip-inc", "anadir"]


def test_f030_r15_cargar_edicion_parte_de_lo_guardado():
    r = _editor(("cargarEdicion", "cuerpoLineas", "cuerpoIncidencias"), """
      const t = { lineas: [{ obra_ide: 1, es_postventa: false, porcentaje: 60, cod: "01" },
                           { obra_ide: 2, es_postventa: true, porcentaje: 0, cod: "02" }],
                  incidencias: [{ id: 7, obra_ide: 3, obra_cod: "0003", obra_descripcion: "Tres",
                                  codigo: "CIV", letra: "V", nombre: "Vacaciones",
                                  dia_desde: 1, dia_hasta: 31, sigrid_estado: null }] };
      cargarEdicion(t);
      const copia = state.edicion[0] !== t.lineas[0];
      resultado = { copia, edicion: state.edicion.map((l) => l.cod), inc: state.incidenciasEdicion,
                    lineas: JSON.parse(state.lineasGuardadas),
                    incs: JSON.parse(state.incidenciasGuardadas) };
      cargarEdicion({ lineas: [] });
      resultado.vacio = [state.incidenciasEdicion, state.incidenciasGuardadas];
    """)
    assert r["copia"] is True and r["edicion"] == ["01", "02"]
    assert r["inc"] == [{"obra_ide": 3, "cod": "0003", "descripcion": "Tres", "codigo": "CIV",
                         "letra": "V", "nombre": "Vacaciones", "dia_desde": 1, "dia_hasta": 31}]
    assert r["lineas"] == [{"obra_ide": 1, "es_postventa": False, "porcentaje": 60}]
    assert r["incs"] == [{"obra_ide": 3, "codigo": "CIV", "dia_desde": 1, "dia_hasta": 31}]
    assert r["vacio"] == [[], "[]"]


GUARDAR = ("guardarAhora", "cuerpoLineas", "cuerpoIncidencias")

#: Dobles del guardado: la API apunta cada petición y devuelve la fila.
DOBLES_GUARDAR = """
  var peticiones = [], fallar = null;
  async function api(ruta, op) {
    peticiones.push([ruta.split("/").pop(), op.method, JSON.parse(op.body)]);
    if (fallar && ruta.endsWith(fallar)) throw new Error("La obra 9 no se ofrece");
    return { trabajador: { ide: 14 }, resumen: {}, ruta };
  }
  function aplicarFila(d) { llamadas.push("aplicarFila:" + d.ruta.split("/").pop()); }
  function marcarGuardando(s) { llamadas.push("marca:" + s); }
  state.editandoIde = 14;
  state.edicion = [linea(1, 60)];
  state.incidenciasEdicion = [];
  state.lineasGuardadas = JSON.stringify(cuerpoLineas(state.edicion));
  state.incidenciasGuardadas = "[]";
"""


def test_f030_r15_guardar_solo_lineas_es_lo_de_hoy():
    r = _asincrono(GUARDAR, DOBLES_GUARDAR, """
      state.edicion[0].porcentaje = 70; state.guardadoPendiente = true;
      await guardarAhora();
      const a = peticiones.slice();
      state.guardadoPendiente = true;          // sin cambios: como hoy, reenvía
      await guardarAhora();
      resultado = { a, b: peticiones.slice(a.length), pendiente: state.guardadoPendiente,
                    llamadas };
    """)
    assert r["a"] == [["asignaciones", "PUT", {"lineas": [
        {"obra_ide": 1, "es_postventa": False, "porcentaje": 70}]}]]
    assert r["b"] == r["a"]
    assert r["pendiente"] is False
    assert r["llamadas"] == ["aplicarFila:asignaciones", "marca:✓"] * 2


def test_f030_r15_guardar_solo_incidencias_no_reenvia_las_lineas():
    r = _asincrono(GUARDAR, DOBLES_GUARDAR, """
      state.incidenciasEdicion.push(inc(3, "CIV", "V", "Vacaciones", 5, null));
      state.guardadoPendiente = true;
      await guardarAhora();
      resultado = { p: peticiones, llamadas, foto: state.incidenciasGuardadas };
    """)
    assert r["p"] == [["incidencias", "PUT", {"incidencias": [
        {"obra_ide": 3, "codigo": "CIV", "dia_desde": 5, "dia_hasta": None}]}]]
    assert r["llamadas"] == ["aplicarFila:incidencias", "marca:✓"]
    assert json.loads(r["foto"]) == r["p"][0][2]["incidencias"]


def test_f030_r13_r15_guardar_las_dos_lineas_primero():
    """R13: la línea nueva se quitó y su obra lleva ahora la incidencia: un
    solo diferido manda los dos PUT y la fila que se pinta es la última."""
    r = _asincrono(GUARDAR, DOBLES_GUARDAR, """
      state.edicion = [];
      state.incidenciasEdicion.push(inc(1, "CIE", "B", "Enfermedad", null, null));
      state.guardadoPendiente = true;
      await guardarAhora();
      resultado = { p: peticiones.map((x) => x[0]), cuerpo: peticiones[0][2], llamadas };
    """)
    assert r["p"] == ["asignaciones", "incidencias"]
    assert r["cuerpo"] == {"lineas": []}
    assert r["llamadas"] == ["aplicarFila:incidencias", "marca:✓"]


def test_f030_r15_guardar_rechazo_de_la_api_avisa_y_reintenta_solo_lo_pendiente():
    r = _asincrono(GUARDAR, DOBLES_GUARDAR, """
      state.edicion[0].porcentaje = 50;
      state.incidenciasEdicion.push(inc(9, "CIV", "V", "Vacaciones", null, null));
      state.guardadoPendiente = true;
      fallar = "incidencias";
      await guardarAhora();
      const a = { p: peticiones.map((x) => x[0]), pendiente: state.guardadoPendiente,
                  llamadas: llamadas.slice() };
      fallar = null;
      await guardarAhora();
      resultado = { a, b: peticiones.slice(2).map((x) => x[0]), pendiente: state.guardadoPendiente,
                    llamadas: llamadas.slice(a.llamadas.length) };
    """)
    assert r["a"] == {"p": ["asignaciones", "incidencias"], "pendiente": True,
                      "llamadas": ["marca:!", "toast:No se pudo guardar: La obra 9 no se ofrece"]}
    assert r["b"] == ["incidencias"]
    assert r["pendiente"] is False
    assert r["llamadas"] == ["aplicarFila:incidencias", "marca:✓"]


def test_f030_r20_deshacer_con_el_editor_abierto_recarga_las_incidencias():
    r = _asincrono(("deshacer", "cargarEdicion", "cuerpoLineas", "cuerpoIncidencias"), """
      async function api() {
        return { trabajador: { ide: 14, nombre: "Ana", lineas: [linea(1, 100)],
                               incidencias: [] }, resumen: {} };
      }
      function aplicarFila() {} function renderTabla() {}
    """, """
      state.editandoIde = 14; state.guardadoPendiente = true;
      state.incidenciasEdicion = [inc(3, "CIV", "V", "Vacaciones", 1, 5)];
      await deshacer(14);
      resultado = { inc: state.incidenciasEdicion, foto: state.incidenciasGuardadas,
                    pendiente: state.guardadoPendiente };
    """)
    assert r == {"inc": [], "foto": "[]", "pendiente": False}


def test_f030_r15_abrir_y_cerrar_editor_y_copias_usan_cargar_edicion():
    for nombre in ("abrirEditor", "deshacer", "copiarTrabajador", "copiarDeArriba"):
        cuerpo = " ".join(_funcion(nombre).split())
        assert "cargarEdicion(" in cuerpo, nombre
        assert ".lineas.map((l) => ({ ...l }))" not in cuerpo, nombre
    cerrar = " ".join(_funcion("cerrarEditor").split())
    assert "state.edicion = []; state.incidenciasEdicion = [];" in cerrar


# ================================ R16 ==================================== #
#: `construirFila` REAL con una `construirCelda` de mentira, como F-050 (M2).
FILA = r"""
function clases() { const s = new Set();
  return {add: (c) => s.add(c), contains: (c) => s.has(c), lista: () => [...s]}; }
function construirCelda(t, clave, idx) { return {clave, idx, classList: clases()}; }
const document = {createDocumentFragment: () => ({trs: [],
  appendChild(tr) { this.trs.push(tr); }}),
  createElement: () => ({dataset: {}, tds: [], set className(c) {
    c.split(" ").forEach((x) => this.classList.add(x)); },
    classList: clases(), appendChild(td) { this.tds.push(td); },
    querySelectorAll(sel) { return sel === "td[rowspan]"
      ? this.tds.filter((td) => td.rowSpan !== undefined) : []; },
    addEventListener() {}})};
"""


def _fila(lineas: int, incidencias: int) -> list:
    const = re.search(r"^const COLUMNAS_POR_LINEA = .*?;", JS, re.MULTILINE).group(0)
    return _node("\n".join([
        const, FILA, _funcion("construirFila"),
        "const state = {columnas: ['nombre', 'asignaciones', 'partida', 'total'],"
        " seleccionIde: 7, seleccion: new Set(), editandoIde: null};",
        "const t = {ide: 7, activo: true, lineas: " +
        json.dumps([{"obra_ide": i} for i in range(lineas)]) + ", incidencias: " +
        json.dumps([{"obra_ide": i} for i in range(incidencias)]) + "};",
        ("const frag = construirFila(t);"
         "process.stdout.write(JSON.stringify(frag.trs.map((tr) => ["
         "tr.classList.lista().sort().join(' '), tr.dataset.linea, "
         "tr.tds.map((td) => [td.clave, td.idx, td.rowSpan === undefined ? null : td.rowSpan])])));"),
    ]))


def test_f030_r16_una_subfila_por_incidencia_tras_las_lineas():
    filas = _fila(2, 2)
    assert [f[0] for f in filas] == [
        "fila seleccionada", "fila seleccionada subfila",
        "fila fila-inc seleccionada subfila", "fila fila-inc seleccionada subfila"]
    assert [f[1] for f in filas] == [0, 1, 2, 3]
    assert filas[0][2] == [["nombre", 0, 4], ["asignaciones", 0, None],
                           ["partida", 0, None], ["total", 0, 4]]
    assert filas[3][2] == [["asignaciones", 3, None], ["partida", 3, None]]


def test_f030_r16_sin_lineas_queda_la_de_sin_carga_y_luego_las_incidencias():
    filas = _fila(0, 1)
    assert [f[0] for f in filas] == ["fila seleccionada", "fila fila-inc seleccionada subfila"]
    assert filas[0][2][0] == ["nombre", 0, 2]
    assert _fila(1, 0) == [["fila seleccionada", 0, [
        ["nombre", 0, 1], ["asignaciones", 0, None], ["partida", 0, None], ["total", 0, 1]]]]


CELDA = ("construirCelda", "incidenciaDeSubfila", "textoIncidencia", "etiquetaObra",
         "fmtPct", "badgeTotal")


def test_f030_r16_la_celda_de_obra_y_la_partida_de_una_incidencia():
    r = _editor(CELDA, """
      const t = { ide: 7, total: 100, estado: "OK", lineas: [linea(1, 100)],
                  incidencias: [{ obra_ide: 3, obra_cod: "0003", obra_descripcion: "Tres",
                                  codigo: "CIV", letra: "V", nombre: "Vacaciones",
                                  dia_desde: 5, dia_hasta: 9 }] };
      state.periodoEstado = "ABIERTO";
      const chipInc = construirCelda(t, "asignaciones", 1).children[0].children[0];
      const linea0 = construirCelda(t, "asignaciones", 0).children[0].children[0];
      const partida = construirCelda(t, "partida", 1);
      resultado = { clase: chipInc.className, html: chipInc.innerHTML, titulo: chipInc.title,
                    linea0: linea0.className, partida: [partida.className, partida.innerHTML,
                                                        partida.children.length] };
    """)
    assert r["clase"] == "chip-linea chip-inc"
    assert r["html"] == '<span class="cod">0003</span><span class="inc">V del 5 al 9</span>'
    assert r["titulo"] == "Tres · Vacaciones"
    assert r["linea0"] == "chip-linea"
    assert r["partida"] == ["celda-partida", "", 0]


def _visibles(filtros: dict) -> dict:
    trabajadores = [
        {"ide": 1, "nombre": "Ana", "categoria": "", "activo": True, "estado": "SIN_CARGA",
         "total": 0, "lineas": [],
         "incidencias": [{"obra_ide": 3, "obra_cod": "0700", "obra_descripcion": "Depósito",
                          "codigo": "CIV", "letra": "V", "nombre": "Vacaciones",
                          "dia_desde": 1, "dia_hasta": 31}]},
        {"ide": 2, "nombre": "Benito", "categoria": "", "activo": True, "estado": "OK",
         "total": 100, "lineas": [{"obra_ide": 3, "cod": "0700", "descripcion": "Depósito",
                                   "es_postventa": False, "porcentaje": 100}]},
        {"ide": 3, "nombre": "Carla", "categoria": "", "activo": True, "estado": "OK",
         "total": 100, "lineas": [{"obra_ide": 4, "cod": "0656", "descripcion": "Arroyo",
                                   "es_postventa": False, "porcentaje": 100}]},
    ]
    estado = {"trabajadores": trabajadores, "filtroTexto": "", "filtroEstado": None,
              "soloPendientes": False, "columnas": ["nombre", "asignaciones", "total"],
              "orden": {"campo": "nombre", "dir": 1}, "filtrosCol": {}}
    cuerpo = ("resultado = {}; for (const [q, v] of Object.entries(" +
              json.dumps(filtros) + ")) { state.filtrosCol = {asignaciones: v}; "
              "resultado[q] = trabajadoresVisibles().map((t) => t.nombre); }")
    programa = "\n".join([
        _orden_estado(),
        *[_funcion(f) for f in ("normalizar", "etiquetaObra", "textoObra", "lineaCasa",
                                "fmtPct", "textoColumna", "trabajadoresVisibles",
                                "textoIncidencia", "incidenciaCasa")],
        "var state = " + json.dumps(estado, ensure_ascii=False) + ";",
        "var resultado;", cuerpo, "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


def test_f030_r16_el_filtro_de_obra_encuentra_la_incidencia():
    assert _visibles({"obra": "0700", "letra": "v del 1", "nombre": "vacaciones",
                      "tilde": "deposito", "otra": "arroyo", "nada": "zz"}) == {
        "obra": ["Ana", "Benito"], "letra": ["Ana"], "nombre": ["Ana"],
        "tilde": ["Ana", "Benito"], "otra": ["Carla"], "nada": []}


def test_f030_r16_css_de_la_incidencia():
    assert re.search(r"\.chip-inc\s*[,{]", CSS)
    assert re.search(r"tr\.fila-inc\b", CSS)


# ================================ R32 ==================================== #
#: `escapeHtml` usa el DOM: un nodo de texto que se lee como HTML, como el
#: navegador (escapa `&`, `<` y `>`).
DOM_TEXTO = r"""
var document = { createElement: () => ({
  set textContent(v) { this._t = v; },
  get innerHTML() {
    return this._t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  } }) };
"""


def _modal(obra: dict, trabajadores: list) -> str:
    programa = "\n".join([
        DOM_TEXTO,
        *[_funcion(f) for f in ("escapeHtml", "datosIncidencia",
                                "textoLineaIncidencia", "seccionIncidencias")],
        "var state = " + json.dumps({"trabajadores": trabajadores},
                                    ensure_ascii=False) + ";",
        "process.stdout.write(JSON.stringify(seccionIncidencias(" +
        json.dumps(obra, ensure_ascii=False) + ")));"])
    return _node(programa)


ANA = {"ide": 10, "nombre": "Ana Ruiz", "incidencias": [
    {"id": 7, "obra_ide": 678, "obra_cod": "0678", "codigo": "CIV", "letra": "V",
     "nombre": "Vacaciones", "dia_desde": 5, "dia_hasta": 9},
    {"id": 8, "obra_ide": 678, "obra_cod": "0678", "codigo": "CIE", "letra": "B",
     "nombre": "Enfermedad", "dia_desde": 12, "dia_hasta": 12}]}


def _accion(i, rol, accion, fec, hora, parte=None, motivo=None):
    return {"id": i, "rol": rol, "accion": accion, "fecha_int": fec,
            "hora_codigo": hora, "paride": 0, "parte_cod": parte,
            "hmores_ide": None, "motivo": motivo}


def _celdas(html: str) -> list[list[str]]:
    filas = re.findall(r"<tr>(.*?)</tr>", html.split("<tbody>")[1])
    return [re.findall(r"<td>(.*?)</td>", f) for f in filas]


def test_f030_r32_modal_seccion_por_incidencia():
    html = _modal({"incidencias": [
        _accion(7, "ini", "escribir", 20260705, "CIV", "PT26/00251"),
        _accion(7, "fin", "escribir", 20260709, "CIZ", "PT26/00251"),
        _accion(8, "ini", "ya_registrado", 20260712, "CIE", "PT26/00031"),
        _accion(8, "fin", "omitir", 20260712, "CIZ", "PT26/00041",
                "ya hay una línea CIZ del recurso el 12/07 en el parte PT26/00041"),
    ]}, [ANA])
    assert html.startswith("<h4>Incidencias</h4>")
    assert "<th>Trabajador</th><th>Obra</th><th>Incidencia</th><th>Días</th>" \
           "<th>Qué se hará</th>" in html
    assert _celdas(html) == [
        ["Ana Ruiz", "0678", "V Vacaciones", "del 5 al 9",
         "inicio CIV 05/07: se escribe en el parte PT26/00251 · "
         "fin CIZ 09/07: se escribe en el parte PT26/00251"],
        ["Ana Ruiz", "0678", "B Enfermedad", "del 12 al 12",
         "inicio CIE 12/07: ya registrada · fin CIZ 12/07: no se escribe: "
         "ya hay una línea CIZ del recurso el 12/07 en el parte PT26/00041"]]
    # Sin confirmaciones (R28, R32).
    assert "checkbox" not in html and "chk-pisar" not in html


def test_f030_r32_modal_omitidas_sin_dias_y_desconocida():
    html = _modal({"incidencias": [
        _accion(9, "ini", "omitir", 0, None, None, "días <imposibles>"),
        _accion(9, "fin", "omitir", 0, None, None, "días <imposibles>")]}, [ANA])
    assert _celdas(html) == [[
        "incidencia 9", "", "", "",
        "inicio: no se escribe: días &lt;imposibles&gt; · "
        "fin: no se escribe: días &lt;imposibles&gt;"]]


def test_f030_r32_modal_sin_incidencias_nada():
    assert _modal({}, [ANA]) == ""
    assert _modal({"incidencias": []}, [ANA]) == ""


def test_f030_r32_modal_la_pinta_cada_obra():
    cuerpo = _funcion("pintarModalPreflight")
    # Sin incidencias ni se llama (los arneses del modal de F-049/F-050 no
    # la cargan y siguen igual).
    assert "if ((o.incidencias || []).length) html += seccionIncidencias(o);" \
        in cuerpo
    assert cuerpo.index("seccionIncidencias(o)") > cuerpo.index("(o.conflictos || [])")
    assert re.search(r"\.tabla-inc\b", CSS)
