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
