# tests/test_f030_celda_pct.py
"""F-030 · La celda del % del editor: lo de hoy (R1) y las letras (R8-R13).

T1 fija lo de HOY antes de tocar `app.js`: con un valor sin ninguna letra la
celda hace exactamente lo que hacía (el % de la línea, el total en vivo, el
guardado diferido, Enter al buscador de obra y, al salir en blanco, lo que
falta hasta el 100 %; también al aceptar el % sugerido). Estos tests se
escribieron en verde sobre el `app.js` previo a F-030 y no cambian después.

Se ejecuta el código REAL de `chipEditable` en node con el DOM mínimo de
`test_f042_sugerencias.py`, al que se le añade lo justo que usa la celda
(foco, `blur`, `querySelector`, `replaceWith`). Sin `node` se saltan con su
motivo; el reviewer los exige `passed`. Sin red ni BBDD.
"""
from __future__ import annotations

import re

from tests.test_f042_sugerencias import DOM_DE_PRUEBA, JS, _funcion, _node

#: Lo que la celda usa del DOM y el DOM de F-042 no trae. `blur()` dispara la
#: escucha `blur` como el navegador; `foco` es el elemento con el foco.
DOM_CELDA = r"""
var foco = null;
El.prototype.focus = function () { foco = this; this.fire("focus"); };
El.prototype.select = function () {};
El.prototype.blur = function () {
  if (foco === this) foco = null;
  this.fire("blur");
};
El.prototype.querySelector = function (sel) {
  const clase = sel.slice(1);
  for (const c of this.children) {
    if (c.classList.contains(clase)) return c;
    const dentro = c.querySelector(sel);
    if (dentro) return dentro;
  }
  return null;
};
El.prototype.replaceWith = function (nuevo) {
  const padre = this.parent;
  const i = padre.children.indexOf(this);
  padre.children[i] = nuevo;
  nuevo.parent = padre;
  this.parent = null;
};
function toast(m) { llamadas.push("toast:" + m); }
// Editor de prueba: el buscador de obra y el total en vivo, como pintarEditor.
function nuevoEditor() {
  const editor = new El("div");
  editor.className = "editor";
  const anadir = new El("div");
  anadir.className = "anadir";
  const obraInput = new El("input");
  obraInput.className = "obra-input";
  anadir.appendChild(obraInput);
  editor.appendChild(anadir);
  const badge = new El("span");
  badge.className = "total-badge total-vivo";
  editor.appendChild(badge);
  return editor;
}
function linea(obra_ide, porcentaje) {
  return { obra_ide, cod: "0" + obra_ide, descripcion: "Obra " + obra_ide,
           es_postventa: false, porcentaje, obra_activa: true,
           obra_admite_postventa: false, ofrecible: true };
}
function celda(chip) { return chip.children.find((c) => c.classList.contains("pct-input")); }
function totalVivo(editor) { return editor.querySelector(".total-vivo").innerHTML; }
"""

#: Funciones REALES de `app.js` que se cargan (la celda y lo que llama).
FUNCIONES_HOY = ("etiquetaObra", "fmtPct", "badgeTotal", "parsearPct",
                 "totalEdicion", "restanteSin", "refrescarTotalVivo",
                 "chipEditable")


def _celda_hoy(cuerpo: str) -> object:
    programa = "\n".join([DOM_DE_PRUEBA, DOM_CELDA,
                          *[_funcion(f) for f in FUNCIONES_HOY],
                          "var resultado;", cuerpo,
                          "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


# ================================ R1 ===================================== #
def test_f030_r1_hoy_cifras_ponen_el_pct_el_total_y_el_guardado():
    """«40» y «40,5»: el % de la línea, el total en vivo y el guardado
    diferido; ningún panel colgado de <body>."""
    r = _celda_hoy("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 0);
      state.edicion = [otra, l];
      const pct = celda(chipEditable(l, 1, editor));
      pct.value = "40"; pct.fire("input");
      const a = { pct: l.porcentaje, total: totalVivo(editor),
                  guardados: llamadas.filter((x) => x === "programarGuardado").length };
      pct.value = "40,5"; pct.fire("input");
      const b = { pct: l.porcentaje, total: totalVivo(editor) };
      pct.value = "40.5 %"; pct.fire("input");
      resultado = { a, b, c: l.porcentaje, paneles: document.body.children.length,
                    guardados: llamadas.filter((x) => x === "programarGuardado").length };
    """)
    assert r["a"]["pct"] == 40
    assert "70%" in r["a"]["total"] and "falta 30%" in r["a"]["total"]
    assert r["a"]["guardados"] == 1
    assert r["b"]["pct"] == 40.5 and "70,5%" in r["b"]["total"]
    assert r["c"] == 40.5
    assert r["guardados"] == 3
    assert r["paneles"] == 0


def test_f030_r1_hoy_en_blanco_al_salir_pone_lo_que_falta():
    r = _celda_hoy("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 50);
      state.edicion = [otra, l];
      const pct = celda(chipEditable(l, 1, editor));
      pct.value = "  "; pct.fire("input");
      const vacia = l.porcentaje;
      pct.blur();
      resultado = { vacia, pct: l.porcentaje, valor: pct.value,
                    total: totalVivo(editor),
                    guardados: llamadas.filter((x) => x === "programarGuardado").length };
    """)
    assert r["vacia"] == 0
    assert r["pct"] == 70 and r["valor"] == "70"
    assert "100%" in r["total"]
    assert r["guardados"] == 2


def test_f030_r1_hoy_enter_va_al_buscador_de_obra():
    r = _celda_hoy("""
      const editor = nuevoEditor();
      const l = linea(1, 0);
      state.edicion = [l];
      const pct = celda(chipEditable(l, 0, editor));
      pct.focus();
      pct.value = "40"; pct.fire("input");
      pct.fire("keydown", "Enter");
      resultado = { foco: foco && foco.className, pct: l.porcentaje };
    """)
    assert r == {"foco": "obra-input", "pct": 40}


def test_f030_r1_hoy_aceptar_el_sugerido_lo_deja_y_no_guarda_de_mas():
    """El buscador de obra deja en la línea nueva lo que falta (aquí 70) y
    el foco en su %: Enter lo acepta tal cual, sin otro guardado."""
    r = _celda_hoy("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 70);
      state.edicion = [otra, l];
      const pct = celda(chipEditable(l, 1, editor));
      pct.focus();
      const valor = pct.value;
      pct.fire("keydown", "Enter");
      resultado = { valor, pct: l.porcentaje, foco: foco && foco.className,
                    guardados: llamadas.filter((x) => x === "programarGuardado").length };
    """)
    assert r == {"valor": "70", "pct": 70, "foco": "obra-input", "guardados": 0}


def test_f030_r1_hoy_la_rama_de_hoy_sigue_en_la_escucha_input():
    """El código de hoy de la escucha `input` sigue estando (literal)."""
    cuerpo = " ".join(_funcion("chipEditable").split())
    assert "linea.porcentaje = parsearPct(pct.value); refrescarTotalVivo(editor); " \
        "programarGuardado();" in cuerpo
    assert re.search(r"^function parsearPct\(", JS, re.MULTILINE)


# ============================ R8-R13 (T8) ================================ #
#: Lo que añade la rama de letras al DOM de la celda: un `fire` que, como el
#: navegador, para en `stopImmediatePropagation` y deja ver qué se llamó; el
#: catálogo de incidencias (el de `GET /incidencias`, por letra) y las
#: incidencias del editor. `enfocarDiaIncidencia` es un doble: el chip de la
#: incidencia es de T9.
DOM_LETRAS = r"""
El.prototype.fire = function (t, key) {
  const ev = { key, type: t, previsto: false, burbuja: true, parado: false,
               preventDefault() { this.previsto = true; },
               stopPropagation() { this.burbuja = false; },
               stopImmediatePropagation() { this.parado = true; this.burbuja = false; } };
  for (const fn of (this.listeners[t] || [])) { fn(ev); if (ev.parado) break; }
  return ev;
};
function enfocarDiaIncidencia(editor, idx) { llamadas.push("enfocarDia:" + idx); }
state.tiposIncidencia = [
  { codigo: "CIA", letra: "AT", nombre: "Accidente de trabajo" },
  { codigo: "CIE", letra: "B", nombre: "Enfermedad/Acc. no laboral" },
  { codigo: "CIP", letra: "FJ", nombre: "Falta justificada" },
  { codigo: "CIV", letra: "V", nombre: "Vacaciones" },
];
state.incidenciasEdicion = [];
function montar(l, idx, editor) {
  const pct = celda(chipEditable(l, idx, editor));
  pct.rect = { top: 300, bottom: 336, left: 300 };
  pct.focus();
  return pct;
}
function teclear(pct, texto) { pct.value = texto; pct.fire("input"); }
function panelInc() {
  return document.body.children.find((c) => c.classList.contains("incidencias")) || null;
}
function filas() {
  const p = panelInc();
  return p ? p.children.map((c) => c.className + "|" + c.innerHTML) : null;
}
function guardados() { return llamadas.filter((x) => x === "programarGuardado").length; }
"""

FUNCIONES_LETRAS = (*FUNCIONES_HOY, "normalizar", "posicionSugerencias",
                    "colocarSugerencias", "retirarSugerencias",
                    "montarDesplegableIncidencias")


def _celda_letras(cuerpo: str) -> object:
    # `let desmontarSugerencias = null;` viaja con `chipEditable`: `_funcion`
    # corta en la siguiente `function` y la variable va entre las dos.
    funciones = [_funcion(f) for f in FUNCIONES_LETRAS]
    assert "let desmontarSugerencias = null;" in "".join(funciones)
    programa = "\n".join([DOM_DE_PRUEBA, DOM_CELDA, DOM_LETRAS, *funciones,
                          "var resultado;", cuerpo,
                          "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


def _fila(clase: str, letra: str, nombre: str) -> str:
    return (f"{clase}|<span class=\"cod\">{letra}</span>"
            f"<span class=\"desc\">{nombre}</span>")


def test_f030_r8_r9_letras_abren_el_panel_sin_tocar_pct_total_ni_guardado():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 70);
      state.edicion = [otra, l];
      const pct = montar(l, 1, editor);
      refrescarTotalVivo(editor);
      const total = totalVivo(editor);
      teclear(pct, "b");
      const b = filas();
      teclear(pct, "Vaca");
      const vaca = filas();
      teclear(pct, "ENFERMÉDAD");
      const tilde = filas();
      resultado = { b, vaca, tilde, pct: l.porcentaje, total: totalVivo(editor) === total,
                    guardados: guardados(), enBody: panelInc().parent === document.body,
                    top: panelInc().style.top, oculto: panelInc().classList.contains("oculto") };
    """)
    # «b»: antes la de letra idéntica (B) y luego las que lo contienen
    # (tr«a»«b»ajo), por orden del catálogo.
    assert r["b"] == [_fila("sugerencia inc activa", "B", "Enfermedad/Acc. no laboral"),
                      _fila("sugerencia inc", "AT", "Accidente de trabajo")]
    assert r["vaca"] == [_fila("sugerencia inc activa", "V", "Vacaciones")]
    assert r["tilde"] == [_fila("sugerencia inc activa", "B", "Enfermedad/Acc. no laboral")]
    assert (r["pct"], r["total"], r["guardados"]) == (70, True, 0)
    assert (r["enBody"], r["top"], r["oculto"]) == (True, "340px", False)


def test_f030_r8_letras_mas_cifras_y_letra_identica_primero():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const l = linea(1, 0);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      teclear(pct, "a");
      const a = filas().map((f) => f.split("|")[1]);
      teclear(pct, " fj ");
      const fj = filas().map((f) => f.split("|")[1]);
      teclear(pct, "40x");
      const x = filas();
      resultado = { a, fj, x, pct: l.porcentaje };
    """)
    assert [f.split("</span>")[0] for f in r["a"]] == [
        '<span class="cod">AT', '<span class="cod">B', '<span class="cod">FJ',
        '<span class="cod">V']
    assert r["fj"] == ['<span class="cod">FJ</span><span class="desc">Falta justificada</span>']
    assert r["x"] == ["sugerencia vacia|Ninguna incidencia con «40x»"]
    assert r["pct"] == 0


def test_f030_r10_letras_flechas_enter_y_tab_eligen_la_activa():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const l = linea(1, 70);
      state.edicion = [l];
      let pct = montar(l, 0, editor);
      teclear(pct, "a");
      pct.fire("keydown", "ArrowDown"); pct.fire("keydown", "ArrowDown");
      pct.fire("keydown", "ArrowUp");
      const activa = filas().map((f) => f.split("|")[0]);
      const enter = pct.fire("keydown", "Enter");
      const tras = state.incidenciasEdicion.map((i) => i.codigo);
      pct = montar(l, 0, editor);
      teclear(pct, "a");
      pct.fire("keydown", "ArrowUp");
      for (let i = 0; i < 9; i++) pct.fire("keydown", "ArrowDown");
      const tab = pct.fire("keydown", "Tab");
      resultado = { activa, enter: [enter.previsto, enter.parado], tras,
                    tab: [tab.previsto, tab.parado],
                    elegidas: state.incidenciasEdicion.map((i) => i.codigo),
                    foco: foco && foco.className, paneles: document.body.children.length,
                    llamadas };
    """)
    assert r["activa"] == ["sugerencia inc", "sugerencia inc activa",
                           "sugerencia inc", "sugerencia inc"]
    # Enter elige y NO llega a la escucha de hoy (que iría al buscador).
    assert r["enter"] == [True, True]
    assert r["tras"] == ["CIE"]
    assert r["tab"] == [True, True]
    assert r["elegidas"] == ["CIE", "CIV"]          # ↓ se queda en la última
    assert r["foco"] == "pct-input"                 # el buscador no recibió foco
    assert r["paneles"] == 0
    assert r["llamadas"] == ["pintarEditor", "enfocarDia:0", "programarGuardado",
                             "pintarEditor", "enfocarDia:1", "programarGuardado"]


def test_f030_r10_letras_sin_coincidencias_enter_no_hace_nada():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const l = linea(1, 70);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      teclear(pct, "zz");
      const enter = pct.fire("keydown", "Enter");
      const tab = pct.fire("keydown", "Tab");
      resultado = { enter: [enter.previsto, enter.parado], tab: [tab.previsto, tab.parado],
                    elegidas: state.incidenciasEdicion.length, foco: foco && foco.className,
                    filas: filas(), llamadas };
    """)
    assert r["enter"] == [True, True]
    assert r["tab"] == [False, False]               # Tab sigue su camino
    assert r["elegidas"] == 0
    assert r["foco"] == "pct-input"
    assert r["filas"] == ["sugerencia vacia|Ninguna incidencia con «zz»"]
    assert r["llamadas"] == []


def test_f030_r10_letras_el_raton_elige_como_en_f042():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const l = linea(1, 70);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      teclear(pct, "a");
      const ev = panelInc().children[3].fire("mousedown");
      resultado = { previsto: ev.previsto, elegidas: state.incidenciasEdicion,
                    paneles: document.body.children.length };
    """)
    assert r["previsto"] is True                    # no quita el foco
    assert r["elegidas"] == [{"obra_ide": 1, "cod": "01", "descripcion": "Obra 1",
                              "codigo": "CIV", "letra": "V", "nombre": "Vacaciones",
                              "dia_desde": None, "dia_hasta": None}]
    assert r["paneles"] == 0


def test_f030_r11_letras_escape_cierra_y_repone_sin_guardar():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const l = linea(1, 0);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      teclear(pct, "45");
      teclear(pct, "45v");
      teclear(pct, "45va");
      const esc = pct.fire("keydown", "Escape");
      resultado = { valor: pct.value, pct: l.porcentaje, guardados: guardados(),
                    burbuja: esc.burbuja, paneles: document.body.children.length,
                    elegidas: state.incidenciasEdicion.length };
    """)
    assert r == {"valor": "45", "pct": 45, "guardados": 1, "burbuja": False,
                 "paneles": 0, "elegidas": 0}


def test_f030_r12_letras_borradas_cierran_y_sigue_lo_de_hoy():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 70);
      state.edicion = [otra, l];
      const pct = montar(l, 1, editor);
      teclear(pct, "v");
      const abierto = document.body.children.length;
      teclear(pct, "");
      const cerrado = document.body.children.length;
      const vacia = [l.porcentaje, guardados()];
      teclear(pct, "50");
      resultado = { abierto, cerrado, vacia, pct: l.porcentaje, guardados: guardados(),
                    total: totalVivo(editor) };
    """)
    assert (r["abierto"], r["cerrado"]) == (1, 0)
    assert r["vacia"] == [0, 1]
    assert r["pct"] == 50 and r["guardados"] == 2
    assert "80%" in r["total"]


def test_f030_r13_letras_en_linea_nueva_la_quitan_y_queda_la_incidencia():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = { ...linea(1, 70), nueva: true };
      state.edicion = [otra, l];
      const pct = montar(l, 1, editor);
      teclear(pct, "v");
      pct.fire("keydown", "Enter");
      pct.blur();                         // el navegador quita la celda
      resultado = { edicion: state.edicion.map((x) => x.obra_ide),
                    inc: state.incidenciasEdicion.map((i) => [i.obra_ide, i.codigo]),
                    pct: l.porcentaje, llamadas };
    """)
    assert r["edicion"] == [2]
    assert r["inc"] == [[1, "CIV"]]
    assert r["pct"] == 70
    assert r["llamadas"] == ["pintarEditor", "enfocarDia:0", "programarGuardado"]


def test_f030_r13_letras_en_linea_existente_no_cambian_su_pct():
    """Ya existía (o el foco salió de su % y volvió): su % y su celda se
    quedan como antes de la primera letra; ni el blur de después la rellena."""
    r = _celda_letras("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = { ...linea(1, 0), nueva: true };
      state.edicion = [otra, l];
      let pct = montar(l, 1, editor);
      pct.blur();                         // sale del %: ya no es nueva
      const nueva = l.nueva;
      pct.value = ""; pct = montar(l, 1, editor);
      teclear(pct, "b");
      pct.fire("keydown", "Enter");
      pct.blur();
      resultado = { nueva, edicion: state.edicion.map((x) => [x.obra_ide, x.porcentaje]),
                    valor: pct.value, inc: state.incidenciasEdicion.map((i) => i.codigo),
                    llamadas };
    """)
    assert r["nueva"] is False
    # El primer blur (en blanco) es lo de hoy: rellena lo que falta (70).
    assert r["edicion"] == [[2, 30], [1, 70]]
    assert r["inc"] == ["CIE"]
    assert r["llamadas"][-3:] == ["pintarEditor", "enfocarDia:0", "programarGuardado"]


def test_f030_r13_letras_existente_en_blanco_no_rellena_al_elegir():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 0);
      state.edicion = [otra, l];
      const pct = montar(l, 1, editor);
      pct.value = "";
      teclear(pct, "v");
      pct.fire("keydown", "Enter");
      pct.blur();
      resultado = { pct: l.porcentaje, valor: pct.value, guardados: guardados() };
    """)
    assert r == {"pct": 0, "valor": "", "guardados": 1}


def test_f030_r11_letras_salir_sin_elegir_repone_y_cierra():
    r = _celda_letras("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 40);
      state.edicion = [otra, l];
      const pct = montar(l, 1, editor);
      teclear(pct, "va");
      pct.blur();
      resultado = { valor: pct.value, pct: l.porcentaje, paneles: document.body.children.length,
                    guardados: guardados(), inc: state.incidenciasEdicion.length };
    """)
    assert r == {"valor": "40", "pct": 40, "paneles": 0, "guardados": 0, "inc": 0}


def test_f030_r8_letras_un_solo_panel_y_retirar_lo_quita_todo():
    """El panel de incidencias se encadena al de F-042: `retirarSugerencias`
    (renderTabla, repintar el editor) quita los dos y sus escuchas."""
    r = _celda_letras("""
      const obraPanel = new El("div");
      document.body.appendChild(obraPanel);
      desmontarSugerencias = () => { obraPanel.remove(); llamadas.push("retiraObra"); };
      const editor = nuevoEditor();
      const l = linea(1, 40);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      teclear(pct, "v");
      const abierto = [document.body.children.length, escuchas.length];
      window.fire("resize");
      retirarSugerencias();
      const retirado = [document.body.children.length, escuchas.length];
      teclear(pct, "va");                // la celda sigue viva: lo vuelve a montar
      const otra = [document.body.children.length, escuchas.length];
      pct.fire("keydown", "Escape");
      resultado = { abierto, retirado, otra,
                    fin: [document.body.children.length, escuchas.length,
                          desmontarSugerencias === null], llamadas };
    """)
    assert r["abierto"] == [2, 2]
    assert r["retirado"] == [0, 0]
    assert r["otra"] == [1, 2]
    assert r["fin"] == [0, 0, True]
    assert r["llamadas"] == ["retiraObra"]


def test_f030_r13_letras_el_buscador_marca_la_linea_nueva():
    elegir = " ".join(_funcion("montarAutocompletado").split(
        "const elegir = (entrada) => {")[1].split("input.addEventListener")[0].split())
    push = elegir.split("state.edicion.push({")[1].split("});")[0]
    assert "nueva: true," in push
    assert "nueva" not in elegir.split("state.edicion.push({")[0]


def test_f030_r8_letras_el_catalogo_se_carga_una_vez_al_arrancar():
    r = _node("\n".join([
        "var state = { tiposIncidencia: [] }; var pedidas = []; var avisos = [];",
        "async function api(ruta) { pedidas.push(ruta); return { incidencias: [{ codigo: 'CIV', letra: 'V', nombre: 'Vacaciones' }] }; }",
        "function toast(m, e) { avisos.push([m, e]); }",
        _funcion("cargarTiposIncidencia"),
        "cargarTiposIncidencia().then(() => { const ok = state.tiposIncidencia;",
        "  api = async () => { throw new Error('caida'); };",
        "  return cargarTiposIncidencia().then(() => process.stdout.write(JSON.stringify(",
        "    { ok, pedidas, avisos, tras: state.tiposIncidencia }))); });"]))
    assert r["ok"] == [{"codigo": "CIV", "letra": "V", "nombre": "Vacaciones"}]
    assert r["pedidas"] == ["/incidencias"]
    assert r["avisos"] == [["No se pudo cargar el catálogo de incidencias: caida", True]]
    assert r["tras"] == r["ok"]                     # un fallo no lo vacía
    assert "await cargarTiposIncidencia();" in " ".join(_funcion("init").split())
