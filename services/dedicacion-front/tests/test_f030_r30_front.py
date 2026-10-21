# tests/test_f030_r30_front.py
"""F-030 · Anexo R30 en el front: la incidencia guardada viaja con su `id`
(R37), la quitada se pinta tachada y queda fuera del editor (R38) y el modal
de registro dice «se cambia del d al d» y lista las quitadas (R38, R46).

Solo formatea y lleva la identidad: qué se edita, qué se quita y qué se
escribe lo deciden la api y el transfer. Se ejecuta el código REAL de
`app.js` en node con los arneses de `test_f030_tabla_incidencias.py`. Sin
`node` se saltan con su motivo; el reviewer los exige `passed`. Sin red ni
BBDD.
"""
from __future__ import annotations

import json
import re

from tests.test_f030_tabla_incidencias import (
    ANA,
    CELDA,
    DOBLES_GUARDAR,
    DOM_TEXTO,
    GUARDAR,
    _accion,
    _asincrono,
    _celdas,
    _editor,
)
from tests.test_f042_sugerencias import CSS, _funcion, _node, _regla_css


# ================================ R37 ==================================== #
def test_f030_r37_cargar_edicion_guarda_el_id_y_deja_fuera_las_quitadas():
    r = _editor(("cargarEdicion", "cuerpoLineas", "cuerpoIncidencias"), """
      const base = { obra_ide: 3, obra_cod: "0003", obra_descripcion: "Tres",
                     codigo: "CIV", letra: "V", nombre: "Vacaciones" };
      cargarEdicion({ lineas: [], incidencias: [
        { ...base, id: 7, dia_desde: 5, dia_hasta: 9, quitada: false },
        { ...base, id: 8, dia_desde: 20, dia_hasta: 22, quitada: true },
        { ...base, id: 9, dia_desde: 25, dia_hasta: 26 }] });
      resultado = { inc: state.incidenciasEdicion.map((i) => [i.id, i.dia_desde]),
                    foto: state.incidenciasGuardadas };
    """)
    assert r["inc"] == [[7, 5], [9, 25]]
    assert r["foto"] == json.dumps([
        {"id": 7, "obra_ide": 3, "codigo": "CIV", "dia_desde": 5, "dia_hasta": 9},
        {"id": 9, "obra_ide": 3, "codigo": "CIV", "dia_desde": 25, "dia_hasta": 26}],
        separators=(",", ":"))


def test_f030_r37_cuerpo_manda_el_id_solo_si_lo_tiene():
    r = _editor(("cuerpoIncidencias",), """
      resultado = JSON.stringify(cuerpoIncidencias([
        { id: 7, obra_ide: 3, codigo: "CIV", dia_desde: 6, dia_hasta: 9, letra: "V" },
        { id: null, obra_ide: 3, codigo: "CIE", dia_desde: 12, dia_hasta: null },
        inc(4, "CIV", "V", "Vacaciones", 1, 2)]));
    """)
    assert json.loads(r) == [
        {"id": 7, "obra_ide": 3, "codigo": "CIV", "dia_desde": 6, "dia_hasta": 9},
        {"obra_ide": 3, "codigo": "CIE", "dia_desde": 12, "dia_hasta": None},
        {"obra_ide": 4, "codigo": "CIV", "dia_desde": 1, "dia_hasta": 2}]
    assert r.startswith('[{"id":7,"obra_ide":3,')


#: El PUT de incidencias devuelve la fila con sus `id` (y las quitadas).
DOBLES_IDS = DOBLES_GUARDAR + """
  var respuestaInc = [];
  const apiBase = api;
  api = async function (ruta, op) {
    const d = await apiBase(ruta, op);
    if (ruta.endsWith("incidencias")) d.trabajador.incidencias = respuestaInc;
    return d;
  };
"""


def test_f030_r37_tras_el_put_las_nuevas_toman_el_id_de_la_respuesta():
    r = _asincrono(GUARDAR + ("idsDeLaRespuesta",), DOBLES_IDS, """
      const guardada = { ...inc(3, "CIV", "V", "Vacaciones", 6, 9), id: 7 };
      state.incidenciasEdicion = [guardada,
        inc(3, "CIV", "V", "Vacaciones", 12, 14), inc(5, "CIE", "B", "Enfermedad", 20, null),
        inc(6, "CIV", "V", "Vacaciones", 1, 1)];
      respuestaInc = [
        { id: 7, obra_ide: 3, codigo: "CIV", quitada: false },
        { id: 9, obra_ide: 3, codigo: "CIV", quitada: true },      // quitada: no
        { id: 11, obra_ide: 3, codigo: "CIV", quitada: false },
        { id: 12, obra_ide: 5, codigo: "CIE" },
        { id: 13, obra_ide: 6, codigo: "CIE", quitada: false }];   // otro código
      state.guardadoPendiente = true;
      await guardarAhora();
      const ids = state.incidenciasEdicion.map((i) => i.id === undefined ? "sin" : i.id);
      const foto = JSON.parse(state.incidenciasGuardadas);
      state.guardadoPendiente = true;              // sin cambios: no hay otro PUT
      await guardarAhora();
      resultado = { ids, foto, p: peticiones.map((x) => x[0]),
                    cuerpo: peticiones[0][2].incidencias };
    """)
    assert r["ids"] == [7, 11, 12, "sin"]
    assert r["cuerpo"][0]["id"] == 7 and "id" not in r["cuerpo"][1]
    assert r["foto"] == [
        {"id": 7, "obra_ide": 3, "codigo": "CIV", "dia_desde": 6, "dia_hasta": 9},
        {"id": 11, "obra_ide": 3, "codigo": "CIV", "dia_desde": 12, "dia_hasta": 14},
        {"id": 12, "obra_ide": 5, "codigo": "CIE", "dia_desde": 20, "dia_hasta": None},
        {"obra_ide": 6, "codigo": "CIV", "dia_desde": 1, "dia_hasta": 1}]
    assert r["p"] == ["incidencias", "asignaciones"]


def test_f030_r37_dos_nuevas_iguales_toman_ids_distintos_en_orden():
    r = _editor(("idsDeLaRespuesta",), """
      const a = inc(3, "CIV", "V", "Vacaciones", 1, 2), b = inc(3, "CIV", "V", "Vacaciones", 5, 6);
      idsDeLaRespuesta([a, b], [{ id: 20, obra_ide: 3, codigo: "CIV" },
                                { id: 21, obra_ide: 3, codigo: "CIV" }]);
      const c = inc(3, "CIV", "V", "Vacaciones", 1, 2);
      idsDeLaRespuesta([c], []);
      resultado = [a.id, b.id, c.id === undefined];
    """)
    assert r == [20, 21, True]


# ================================ R38 ==================================== #
def test_f030_r38_la_quitada_en_la_tabla_tachada_y_sigue_en_sigrid():
    r = _editor(CELDA, """
      const i = { obra_ide: 3, obra_cod: "0003", obra_descripcion: "Tres", codigo: "CIV",
                  letra: "V", nombre: "Vacaciones", dia_desde: 5, dia_hasta: 9 };
      const t = { ide: 7, total: 0, estado: "OK", lineas: [],
                  incidencias: [{ ...i, quitada: true }, { ...i, quitada: false }] };
      state.periodoEstado = "ABIERTO";
      const q = construirCelda(t, "asignaciones", 1).children[0].children[0];
      const n = construirCelda(t, "asignaciones", 2).children[0].children[0];
      resultado = [[q.className, q.innerHTML, q.title], [n.className, n.innerHTML]];
    """)
    assert r[0] == [
        "chip-linea chip-inc inc-quitada",
        ('<span class="cod">0003</span><span class="inc">V del 5 al 9</span>'
         '<span class="quitada">quitada · sigue en Sigrid</span>'),
        "Tres · Vacaciones · quitada del cuadrante: sigue en Sigrid hasta retirarla a mano"]
    assert r[1] == ["chip-linea chip-inc",
                    '<span class="cod">0003</span><span class="inc">V del 5 al 9</span>']
    assert "line-through" in _regla_css(".inc-quitada .inc")


def _quitadas(pf: dict) -> str:
    programa = "\n".join([
        DOM_TEXTO, *[_funcion(f) for f in ("escapeHtml", "seccionQuitadas")],
        "process.stdout.write(JSON.stringify(seccionQuitadas(" +
        json.dumps(pf, ensure_ascii=False) + ")));"])
    return _node(programa)


QUITADA = {"id": 8, "trabajador_ide": 10, "trabajador": "Ana Ruiz", "obra_ide": 678,
           "obra_cod": "0678", "obra_nombre": "OBRA", "codigo": "CIV", "letra": "V",
           "desde": 5, "hasta": 9, "parte_cod": "PT26/00251",
           "hmores_ide_ini": 9001, "hmores_ide_fin": 9002}


def test_f030_r38_el_modal_lista_las_quitadas_para_retirarlas_a_mano():
    html = _quitadas({"obras": [], "incidencias_quitadas": [
        QUITADA, {**QUITADA, "id": 9, "trabajador": "<Benito>", "parte_cod": None,
                  "hmores_ide_ini": None, "desde": 12, "hasta": 12}]})
    assert html.startswith("<h4>Quitadas del cuadrante: siguen en Sigrid</h4>")
    assert ("<th>Trabajador</th><th>Obra</th><th>Incidencia</th><th>Días</th>"
            "<th>Retirar a mano en Sigrid</th>") in html
    assert _celdas(html) == [
        ["Ana Ruiz", "0678", "V (CIV)", "del 5 al 9",
         "parte PT26/00251 · líneas 9001 y 9002"],
        ["&lt;Benito&gt;", "0678", "V (CIV)", "del 12 al 12", "línea 9002"]]
    assert "checkbox" not in html
    assert _quitadas({"obras": []}) == ""
    assert _quitadas({"incidencias_quitadas": []}) == ""


def test_f030_r38_pintar_modal_pinta_las_quitadas_tras_las_obras():
    cuerpo = _funcion("pintarModalPreflight")
    assert ("if ((pf.incidencias_quitadas || []).length) html += seccionQuitadas(pf);"
            in cuerpo)
    assert cuerpo.index("seccionQuitadas(pf)") > cuerpo.index("seccionIncidencias(o)")
    assert cuerpo.index("seccionQuitadas(pf)") < cuerpo.index("pie-modal")


# ================================ R46 ==================================== #
def _modal(acciones: list) -> str:
    programa = "\n".join([
        DOM_TEXTO,
        *[_funcion(f) for f in ("escapeHtml", "datosIncidencia",
                                "textoLineaIncidencia", "seccionIncidencias")],
        "var state = " + json.dumps({"trabajadores": [ANA]}, ensure_ascii=False) + ";",
        "process.stdout.write(JSON.stringify(seccionIncidencias(" +
        json.dumps({"incidencias": acciones}, ensure_ascii=False) + ")));"])
    return _node(programa)


def test_f030_r46_el_modal_dice_se_cambia_del_al():
    editar = {**_accion(7, "ini", "editar", 20260706, "CIV", "PT26/00251"),
              "fec_antes": 20260705, "hmores_ide": 9001}
    fin = {**_accion(7, "fin", "editar", 20260712, "CIZ", "PT26/00251"),
           "fec_antes": 20260709, "hmores_ide": 9002}
    assert _celdas(_modal([editar, fin]))[0][4] == (
        "inicio CIV 06/07: se cambia del 5 al 6 en el parte PT26/00251 · "
        "fin CIZ 12/07: se cambia del 9 al 12 en el parte PT26/00251")
    sin_parte = {**editar, "parte_cod": None}
    assert _celdas(_modal([sin_parte]))[0][4] == "inicio CIV 06/07: se cambia del 5 al 6"
    # Lo de antes, igual.
    ya = _accion(7, "fin", "ya_registrado", 20260709, "CIZ")
    assert _celdas(_modal([ya]))[0][4] == "fin CIZ 09/07: ya registrada"


def test_f030_r38_css_de_la_quitada():
    assert re.search(r"\.inc-quitada \.quitada\s*\{", CSS)
