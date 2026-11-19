# tests/test_f069_importes_front.py
"""F-069 · T10-T11: el front de las cantidades y los comentarios (R11-R14,
R29). Ejecuta las funciones REALES de `app.js` en node con el DOM falso de
los tests de F-030; el front no decide nada: pinta lo que llega y manda lo
que se teclea.

- R11: casillas por vinculado por % («€»/«km») y «Caja · obra» por línea,
  con comentario, la marca de copiado y «Revisado»; solo periodo abierto.
- R12: coma o punto decimal, vacía ⇒ `null`; «Revisado» manda la misma
  cantidad; sin cambios, sin PUT; un rechazo, al aviso y pendiente.
- R13: la columna «Comentario» (tras Partida) y su texto.
- R14: la subfila con cantidad y unidad, «falta importe» o «copiado».
- R29: el modal con `tot` de `pre`, km × precio y «caja de esta obra».
"""
from __future__ import annotations

from tests.test_f030_tabla_incidencias import (
    DOBLES_GUARDAR,
    _asincrono,
    _editor,
)
from tests.test_f042_sugerencias import _funcion, _node

FILA = """
  const t = {
    ide: 14,
    lineas: [
      { obra_ide: 1, es_postventa: false, porcentaje: 60, cod: "0001", comentario: "visita",
        vinculados: [
          { vinculado_ide: 20, tipo: "VP", cod: "VP-20", reparto: "pct", unidad: "km" },
          { vinculado_ide: 30, tipo: "CAJA", cod: "CJ", reparto: "obra", unidad: "eur",
            cantidad: 80.5, copiado: true, comentario: "caja" },
          { vinculado_ide: 10, tipo: "TF", cod: "TF-10" }] },
      { obra_ide: 2, es_postventa: true, porcentaje: 40, cod: "0002",
        vinculados: [
          { vinculado_ide: 20, tipo: "VP", cod: "VP-20", reparto: "pct", unidad: "km" },
          { vinculado_ide: 30, tipo: "CAJA", cod: "CJ", reparto: "obra", unidad: "eur" },
          { vinculado_ide: 10, tipo: "TF", cod: "TF-10" }] }],
    importes: [{ vinculado_ide: 20, tipo: "VP", cod: "VP-20", unidad: "km",
                 cantidad: 724.5, copiado: false, comentario: "proveedor" }],
    incidencias: [] };
"""
CARGAR = ("cargarEdicion", "cuerpoLineas", "cuerpoIncidencias", "importesDeFila",
          "cantidadTecleada", "cuerpoImportes", "fotoImportes", "etiquetaObra")


# ================================ R11 ==================================== #
def test_f069_r11_cargar_edicion_hace_una_casilla_por_pct_y_por_caja():
    r = _editor(CARGAR, FILA + """
      cargarEdicion(t);
      resultado = { casillas: state.importesEdicion,
                    foto: JSON.parse(state.importesGuardados),
                    lineas: JSON.parse(state.lineasGuardadas) };
      cargarEdicion({ lineas: [{ obra_ide: 1, es_postventa: false, porcentaje: 100 }] });
      resultado.sin = [state.importesEdicion, state.importesGuardados];
    """)
    assert [(c["vinculado_ide"], c.get("obra_ide"), c["etiqueta"], c["unidad"],
             c["cantidad"], c["comentario"], c["copiado"])
            for c in r["casillas"]] == [
        (20, None, "VP VP-20", "km", "724,5", "proveedor", False),
        (30, 1, "Caja · 0001", "eur", "80,5", "caja", True),
        (30, 2, "Caja · Postv-0002", "eur", "", "", False)]
    assert r["foto"]["copiado"] == [False, True, False]
    assert r["lineas"][0]["comentario"] == "visita"
    assert "comentario" not in r["lineas"][1]
    assert r["sin"] == [[], ""]


def test_f069_r11_chip_con_comentario_marca_y_revisado():
    r = _editor(("chipImporte",), """
      var llamadas = [];
      function programarGuardado() { llamadas.push("programar"); }
      const c = { vinculado_ide: 30, obra_ide: 1, etiqueta: "Caja · 0001", unidad: "eur",
                  cantidad: "80,5", comentario: "caja", copiado: true };
      const chip = chipImporte(c);
      const clase = chip.className;
      const partes = chip.children.map((x) => [x.className, x.textContent || x.value || "",
                                               x.placeholder || ""]);
      chip.children.find((x) => x.className.includes("btn-revisado"))
        .listeners.click.forEach((fn) => fn({}));
      resultado = { clase, ahora: chip.className, partes, copiado: c.copiado,
                    despues: chip.children.map((x) => x.className), llamadas };
    """)
    assert r["clase"] == "chip-edit chip-importe copiado"
    assert r["partes"] == [
        ["cod", "Caja · 0001", ""], ["importe-cantidad", "80,5", "€"],
        ["importe-unidad", "€", ""], ["importe-comentario", "caja", "Comentario"],
        ["marca-copiado", "copiado del mes anterior, sin revisar", ""],
        ["btn secondary small btn-revisado", "Revisado", ""]]
    assert r["copiado"] is False and r["llamadas"] == ["programar"]
    assert r["ahora"] == "chip-edit chip-importe"
    assert "marca-copiado" not in r["despues"]


def test_f069_r11_el_editor_las_pinta_tras_las_incidencias_solo_abierto():
    programa = """
      function chipEditable() { const c = new El("span"); c.className = "chip-edit"; return c; }
      function chipIncidencia() { const c = new El("span"); c.className = "chip-inc"; return c; }
      function chipImporte() { const c = new El("span"); c.className = "chip-importe"; return c; }
      function montarAutocompletado() {}
      function pinta(estado) {
        const editor = new El("div");
        state.periodoEstado = estado;
        state.edicion = [linea(1, 100)];
        state.incidenciasEdicion = [inc(3, "CIV", "V", "Vacaciones", 1, 5)];
        state.importesEdicion = [{}, {}];
        pintarEditor(editor);
        return editor.children.map((c) => c.className).slice(0, 4);
      }
      resultado = [pinta("ABIERTO"), pinta("CERRADO")];
    """
    r = _editor(("pintarEditor", "badgeTotal", "totalEdicion", "fmtPct"), programa)
    assert r[0] == ["chip-edit", "chip-inc", "chip-importe", "chip-importe"]
    assert "chip-importe" not in r[1]


# ================================ R12 ==================================== #
def test_f069_r12_coma_o_punto_vacia_null_y_lo_raro_tal_cual():
    r = _node("\n".join([_funcion("cantidadTecleada"), _funcion("cuerpoImportes"), """
      process.stdout.write(JSON.stringify([
        ["12,5", "12.5", " 7 ", "", "   ", null, "1,2,3", "abc"].map(cantidadTecleada),
        cuerpoImportes([{ vinculado_ide: 20, cantidad: "100", comentario: "  " },
                        { vinculado_ide: 30, obra_ide: 1, es_postventa: false,
                          cantidad: "", comentario: " caja " }])]));
    """]))
    assert r[0] == [12.5, 12.5, 7, None, None, None, "1,2,3", "abc"]
    assert r[1] == [
        {"vinculado_ide": 20, "cantidad": 100, "comentario": None},
        {"vinculado_ide": 30, "obra_ide": 1, "es_postventa": False,
         "cantidad": None, "comentario": "caja"}]


GUARDAR = ("guardarAhora", "cuerpoLineas", "cuerpoIncidencias", "cantidadTecleada",
           "cuerpoImportes", "fotoImportes")
CASILLAS = """
  state.importesEdicion = [{ vinculado_ide: 20, cantidad: "100", comentario: "", copiado: true }];
  state.importesGuardados = fotoImportes(state.importesEdicion);
"""


def test_f069_r12_sin_cambios_no_hay_put_de_importes():
    r = _asincrono(GUARDAR, DOBLES_GUARDAR + CASILLAS, """
      state.guardadoPendiente = true;
      await guardarAhora();
      resultado = peticiones.map((p) => p[0]);
    """)
    assert r == ["asignaciones"]          # lo de hoy: solo las líneas


def test_f069_r12_una_cantidad_y_revisado_mandan_el_put():
    r = _asincrono(GUARDAR, DOBLES_GUARDAR + CASILLAS, """
      state.importesEdicion[0].cantidad = "100,5";
      state.guardadoPendiente = true;
      await guardarAhora();
      const a = peticiones.slice();
      state.importesEdicion[0].copiado = false;   // «Revisado»: misma cantidad
      state.guardadoPendiente = true;
      await guardarAhora();
      resultado = { a, b: peticiones.slice(a.length), llamadas };
    """)
    assert r["a"] == [["importes", "PUT", {"importes": [
        {"vinculado_ide": 20, "cantidad": 100.5, "comentario": None}]}]]
    assert r["b"] == r["a"]
    assert "aplicarFila:asignaciones" not in r["llamadas"]


def test_f069_r12_un_rechazo_avisa_y_queda_pendiente():
    r = _asincrono(GUARDAR, DOBLES_GUARDAR + CASILLAS + """
  var avisos = [];
  function toast(m, e) { avisos.push(m); }
""", """
      fallar = "importes";
      state.importesEdicion[0].cantidad = "-3";
      state.guardadoPendiente = true;
      await guardarAhora();
      resultado = { pendiente: state.guardadoPendiente, avisos, llamadas,
                    foto: state.importesGuardados === fotoImportes(state.importesEdicion) };
    """)
    assert r["pendiente"] is True and r["foto"] is False
    assert r["avisos"] and r["avisos"][0].startswith("No se pudo guardar")
    assert r["llamadas"][-1] == "marca:!"


# =============================== R13, R14 ================================ #
PINTAR = "\n".join(_funcion(f) for f in (
    "cantidadVinculado", "comentarioVinculado", "fmtCantidad",
    "htmlCantidadVinculado", "textoColumna", "fmtPct"))
# `escapeHtml` de verdad usa `document`: aquí, uno que no escapa nada raro.
PINTAR += "\nfunction escapeHtml(s) { return String(s); }"


def test_f069_r13_r14_comentario_y_cantidad_de_la_subfila():
    r = _node("\n".join([PINTAR, FILA, """
      const [vp, caja, tel] = t.lineas[0].vinculados;
      const caja2 = t.lineas[1].vinculados[1];
      process.stdout.write(JSON.stringify({
        html: [vp, caja, caja2].map((v) => htmlCantidadVinculado(t, v)),
        tel: htmlCantidadVinculado(t, tel),
        comentarios: [vp, caja, caja2, tel].map((v) => comentarioVinculado(t, v) || ""),
        texto: textoColumna(t, "comentario"),
        sinVin: textoColumna(t, "comentario", false) }));
    """]))
    assert r["html"] == [
        '<span class="cantidad-vin">724,5 km</span>',
        '<span class="cantidad-vin">80,50 €</span><span class="marca-copiado">copiado</span>',
        '<span class="cantidad-vin falta">falta importe</span>']
    assert r["tel"] == ""                         # F-044 tal cual
    assert r["comentarios"] == ["proveedor", "caja", "", ""]
    assert "visita" in r["texto"] and "proveedor" in r["texto"]
    assert "proveedor" not in r["sinVin"]


# ================================ R29 ==================================== #
def test_f069_r29_el_modal_dice_el_importe_tal_cual():
    r = _node("\n".join([_funcion("fmtCantidad"), _funcion("textoImporteVinculado"), """
      process.stdout.write(JSON.stringify([
        textoImporteVinculado({ reparto: "pct", tot: 27.36, pre: 45.6 }),
        textoImporteVinculado({ reparto: "pct", tot: 86.94, pre: 144.9, km: 724.5,
                                precio_km: 0.2 }),
        textoImporteVinculado({ reparto: "obra", tot: 80, pre: 80 })]));
    """]))
    assert r == ["27,36 € de 45,60 €",
                 "724,5 km × 0,20 €/km · 86,94 € de 144,90 €",
                 "80,00 € · caja de esta obra"]
