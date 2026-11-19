# tests/test_f069_importes_front.py
"""F-069 · T10-T11: el front de las cantidades y los comentarios (R11-R14,
R29). Ejecuta las funciones REALES de `app.js` en node con el DOM falso de
los tests de F-030; el front no decide nada: pinta lo que llega y manda lo
que se teclea.

- R11: casillas por vinculado por % («€»/«km») y «Caja · obra» por línea,
  con comentario, la marca de copiado y «Revisado»; solo periodo abierto.
- R12 (T23, D18, D19, review 1 cambio 1): coma o punto decimal, vacía ⇒
  `null`; el `PUT` lleva SOLO las casillas que cambiaron (actuar sobre una
  no toca otra); «Revisado», con `revisado: true`; solo el comentario, sin
  él; un comentario sin cantidad se manda; sin cambios, sin PUT; un
  rechazo, al aviso y pendiente.
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
          "cantidadTecleada", "cuerpoImportes", "elementoImporte", "firmaImporte",
          "etiquetaObra")


# ================================ R11 ==================================== #
def test_f069_r11_cargar_edicion_hace_una_casilla_por_pct_y_por_caja():
    r = _editor(CARGAR, FILA + """
      cargarEdicion(t);
      resultado = { casillas: state.importesEdicion,
                    guardadas: state.importesEdicion.map((c) => JSON.parse(c.guardada)),
                    cuerpo: cuerpoImportes(state.importesEdicion),
                    lineas: JSON.parse(state.lineasGuardadas) };
      cargarEdicion({ lineas: [{ obra_ide: 1, es_postventa: false, porcentaje: 100 }] });
      resultado.sin = state.importesEdicion;
    """)
    assert [(c["vinculado_ide"], c.get("obra_ide"), c["etiqueta"], c["unidad"],
             c["cantidad"], c["comentario"], c["copiado"])
            for c in r["casillas"]] == [
        (20, None, "VP VP-20", "km", "724,5", "proveedor", False),
        (30, 1, "Caja · 0001", "eur", "80,5", "caja", True),
        (30, 2, "Caja · Postv-0002", "eur", "", "", False)]
    # Cada casilla guarda lo que se mandaría de ella tal como llegó: recién
    # cargada, el `PUT` iría vacío (T23).
    assert r["guardadas"][1] == {"vinculado_ide": 30, "obra_ide": 1,
                                 "es_postventa": False, "cantidad": 80.5,
                                 "comentario": "caja"}
    assert r["cuerpo"] == []
    assert r["lineas"][0]["comentario"] == "visita"
    assert "comentario" not in r["lineas"][1]
    assert r["sin"] == []


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
                    revisado: c.revisado,
                    despues: chip.children.map((x) => x.className), llamadas };
    """)
    assert r["clase"] == "chip-edit chip-importe copiado"
    assert r["partes"] == [
        ["cod", "Caja · 0001", ""], ["importe-cantidad", "80,5", "€"],
        ["importe-unidad", "€", ""], ["importe-comentario", "caja", "Comentario"],
        ["marca-copiado", "copiado del mes anterior, sin revisar", ""],
        ["btn secondary small btn-revisado", "Revisado", ""]]
    assert r["copiado"] is False and r["llamadas"] == ["programar"]
    assert r["revisado"] is True              # D18: el PUT lo dirá
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
    r = _node("\n".join([*(_funcion(f) for f in (
        "cantidadTecleada", "cuerpoImportes", "elementoImporte", "firmaImporte")), """
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
           "cuerpoImportes", "elementoImporte", "firmaImporte")
CASILLAS = """
  state.importesEdicion = [{ vinculado_ide: 20, cantidad: "100", comentario: "", copiado: true }];
  state.importesEdicion.forEach((c) => { c.guardada = firmaImporte(c); });
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
      state.importesEdicion[0].revisado = true;
      state.guardadoPendiente = true;
      await guardarAhora();
      const b = peticiones.slice(a.length);
      state.guardadoPendiente = true;             // ya guardado: nada que mandar
      await guardarAhora();
      resultado = { a, b, c: peticiones.slice(a.length + b.length), llamadas,
                    revisado: state.importesEdicion[0].revisado };
    """)
    assert r["a"] == [["importes", "PUT", {"importes": [
        {"vinculado_ide": 20, "cantidad": 100.5, "comentario": None}]}]]
    assert r["b"] == [["importes", "PUT", {"importes": [
        {"vinculado_ide": 20, "cantidad": 100.5, "comentario": None,
         "revisado": True}]}]]
    assert r["c"] == [["asignaciones", "PUT", r["c"][0][2]]]   # lo de hoy
    assert r["revisado"] is False
    assert "aplicarFila:asignaciones" not in r["llamadas"][:4]


FILA_COPIADA = """
  const t = { ide: 14, incidencias: [],
    lineas: [{ obra_ide: 1, es_postventa: false, porcentaje: 100, cod: "0001",
               vinculados: [
                 { vinculado_ide: 20, tipo: "VP", cod: "VP-20", reparto: "pct", unidad: "km" },
                 { vinculado_ide: 30, tipo: "CAJA", cod: "CJ", reparto: "obra", unidad: "eur",
                   cantidad: 80, copiado: true, comentario: "caja" }] }],
    importes: [{ vinculado_ide: 20, tipo: "VP", cod: "VP-20", unidad: "km",
                 cantidad: 100, copiado: true, comentario: null }] };
  state.importesEdicion = importesDeFila(t);
  function programarGuardado() { state.guardadoPendiente = true; }
"""
GUARDAR_CHIP = GUARDAR + ("importesDeFila", "etiquetaObra", "chipImporte")


def test_f069_r12_d18_dos_copiadas_revisado_en_una_solo_manda_esa():
    """Review 1, cambio 1 (D11, D18): con dos casillas copiadas, «Revisado»
    en la del km manda SOLO esa, con `revisado: true`; la caja ni viaja."""
    r = _asincrono(GUARDAR_CHIP, DOBLES_GUARDAR + FILA_COPIADA, """
      const [km, caja] = state.importesEdicion;
      const chip = chipImporte(km);
      chip.children.find((x) => x.className.includes("btn-revisado"))
        .listeners.click.forEach((fn) => fn({}));
      await guardarAhora();
      resultado = { p: peticiones, caja: caja.copiado };
    """)
    assert r["p"] == [["importes", "PUT", {"importes": [
        {"vinculado_ide": 20, "cantidad": 100, "comentario": None,
         "revisado": True}]}]]
    assert r["caja"] is True


def test_f069_r12_d18_solo_el_comentario_manda_esa_sin_revisado():
    r = _asincrono(GUARDAR_CHIP, DOBLES_GUARDAR + FILA_COPIADA, """
      const caja = state.importesEdicion[1];
      const chip = chipImporte(caja);
      const com = chip.children.find((x) => x.className === "importe-comentario");
      com.value = "caja de diciembre";
      com.listeners.input.forEach((fn) => fn({}));
      await guardarAhora();
      resultado = { p: peticiones, copiado: caja.copiado,
                    marca: chip.children.some((x) => x.className === "marca-copiado") };
    """)
    assert r["p"] == [["importes", "PUT", {"importes": [
        {"vinculado_ide": 30, "obra_ide": 1, "es_postventa": False,
         "cantidad": 80, "comentario": "caja de diciembre"}]}]]
    assert r["copiado"] is True and r["marca"] is True


def test_f069_r12_d18_teclear_la_misma_cantidad_no_quita_la_marca():
    r = _editor(("importesDeFila", "etiquetaObra", "cantidadTecleada",
                 "elementoImporte", "firmaImporte", "chipImporte"), FILA_COPIADA + """
      const km = state.importesEdicion[0];
      const chip = chipImporte(km);
      const cant = chip.children.find((x) => x.className === "importe-cantidad");
      const marca = () => chip.children.some((x) => x.className === "marca-copiado");
      const pasos = [];
      for (const v of ["101", "100,0", ""]) {
        cant.value = v;
        cant.listeners.input.forEach((fn) => fn({}));
        pasos.push([km.copiado, marca(), chip.className]);
      }
      resultado = pasos;
    """)
    assert r == [[False, False, "chip-edit chip-importe"],
                 [True, True, "chip-edit chip-importe copiado"],
                 [False, False, "chip-edit chip-importe"]]


def test_f069_r12_d19_comentario_sin_cantidad_se_manda():
    r = _asincrono(GUARDAR_CHIP, DOBLES_GUARDAR + """
  state.importesEdicion = importesDeFila({ ide: 14, lineas: [], incidencias: [],
    importes: [{ vinculado_ide: 20, tipo: "VP", cod: "VP-20", unidad: "km",
                 cantidad: null, copiado: false, comentario: null }] });
""", """
      state.importesEdicion[0].comentario = "visita a proveedor";
      state.guardadoPendiente = true;
      await guardarAhora();
      resultado = peticiones;
    """)
    assert r == [["importes", "PUT", {"importes": [
        {"vinculado_ide": 20, "cantidad": None,
         "comentario": "visita a proveedor"}]}]]


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
                    queda: cuerpoImportes(state.importesEdicion) };
    """)
    assert r["pendiente"] is True
    assert r["queda"] == [{"vinculado_ide": 20, "cantidad": -3,
                           "comentario": None}]      # se reintenta
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
