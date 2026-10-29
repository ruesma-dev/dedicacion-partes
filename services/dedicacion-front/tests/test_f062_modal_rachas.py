# tests/test_f062_modal_rachas.py
"""F-062 · las rachas en el modal de registro (R25, design §10).

Por obra, una línea por elemento de `rachas` («abre», «continúa la racha del
dd/mm (parte X)», «cierra el dd/mm en el parte Y», «queda abierta», «en la
cadena de …» y sus avisos) y la sección «Cierres de rachas»
(`cierres_racha`); tras las obras, el bloque «No coincide con Sigrid»
(`no_coincide`, en vez de la lista de quitadas de F-030 R38). Solo formatea
lo que manda el transfer: ni calcula ni decide. Se ejecuta el código REAL de
`app.js` en node con los arneses de `test_f030_tabla_incidencias.py`; sin
`node` se saltan con su motivo. Sin red ni BBDD.
"""
from __future__ import annotations

import json

from tests.test_f030_tabla_incidencias import ANA, DOM_TEXTO, _accion, _celdas
from tests.test_f042_sugerencias import JS, _funcion, _node

#: Las funciones del modal que formatean las rachas, con sus ayudantes.
FUNCIONES = ("escapeHtml", "diaMes", "datosIncidencia", "nombreTrabajador",
             "textoLineaIncidencia", "seccionIncidencias", "textoRacha",
             "pintarRachas", "pintarCierresRacha", "pintarNoCoincide")


def _js(llamada: str, dato: dict) -> str:
    programa = "\n".join([
        DOM_TEXTO, *[_funcion(f) for f in FUNCIONES],
        "var state = " + json.dumps({"trabajadores": [ANA]},
                                    ensure_ascii=False) + ";",
        f"process.stdout.write(JSON.stringify({llamada}("
        + json.dumps(dato, ensure_ascii=False) + ")));"])
    return _node(programa)


def _racha(i, papel, cierre, *, ini=20261005, parte_ini="PT26/00251",
           fec=20261009, parte="PT26/00251", duena=None, avisos=()):
    return {"id": i, "papel": papel, "inicio_fec": ini,
            "inicio_parte": parte_ini, "cierre": cierre, "cierre_fec": fec,
            "cierre_parte": parte, "duena_id": duena or i,
            "avisos": list(avisos)}


def test_f062_r25_modal_una_linea_por_racha():
    html = _js("pintarRachas", {"rachas": [
        _racha(7, "abre", "cierra", fec=20261016),
        _racha(8, "continua", "cadena", duena=7, avisos=["un <aviso>"]),
        _racha(7, "continua", "abierta", ini=20260928, parte_ini=None,
               fec=None, parte=None),
        _racha(8, "abre", "cubierta", fec=20261014, parte="PT26/00040")]})
    assert html.startswith("<h4>Rachas</h4>")
    assert ("<th>Trabajador</th><th>Obra</th><th>Incidencia</th><th>Días</th>"
            "<th>Racha</th>") in html
    assert [c[4] for c in _celdas(html)] == [
        "abre · cierra el 16/10 en el parte PT26/00251",
        ("continúa la racha del 05/10 (parte PT26/00251) · en la cadena de "
         "V del 5 al 9 · aviso: un &lt;aviso&gt;"),
        "continúa la racha del 28/09 · queda abierta",
        "abre · ya cerrada el 14/10 en el parte PT26/00040"]
    assert _celdas(html)[0][:4] == ["Ana Ruiz", "0678", "V Vacaciones",
                                    "del 5 al 9"]
    # Una incidencia que el cuadrante no tiene, por su `id`; sin rachas, nada.
    html = _js("pintarRachas", {"rachas": [_racha(99, "abre", "cadena",
                                                  duena=98)]})
    assert _celdas(html) == [["incidencia 99", "", "", "",
                              "abre · en la cadena de la incidencia 98"]]
    assert _js("pintarRachas", {}) == ""
    assert _js("pintarRachas", {"rachas": []}) == ""


def _cierre(accion, **kw):
    return {"recurso_ide": 10, "codigo": "CIE", "inicio_ide": 51,
            "inicio_fec": 20260915, "inicio_parte": "PT26/00200",
            "accion": accion, "fecha_int": 20260930, "incidencia_id": None,
            "motivo": "", "parte_cod": "PT26/00200", "hmores_ide": None,
            **kw}


def test_f062_r25_modal_cierres_de_rachas():
    html = _js("pintarCierresRacha", {"cierres_racha": [
        _cierre("escribir"), _cierre("ya_registrado", hmores_ide=61),
        _cierre("aviso", recurso_ide=11, parte_cod=None,
                motivo="no hay parte <En registro>"),
        _cierre("pendiente")]})
    assert html.startswith("<h4>Cierres de rachas</h4>")
    assert ("<th>Trabajador</th><th>Incidencia</th><th>Inicio</th>"
            "<th>Qué se hará</th>") in html
    assert _celdas(html) == [
        ["Ana Ruiz", "CIE", "15/09 (parte PT26/00200)",
         "se cierra el 30/09 en el parte PT26/00200"],
        ["Ana Ruiz", "CIE", "15/09 (parte PT26/00200)",
         "ya cerrada el 30/09"],
        ["recurso 11", "CIE", "15/09 (parte PT26/00200)",
         "no se cierra: no hay parte &lt;En registro&gt;"],
        ["Ana Ruiz", "CIE", "15/09 (parte PT26/00200)",
         "pendiente de confirmar: no se ha escrito"]]
    assert _js("pintarCierresRacha", {"cierres_racha": []}) == ""


def _nc(tipo, inc, lineas, motivo="quitada en la plataforma; sigue en Sigrid"):
    return {"tipo": tipo, "recurso_ide": 10, "incidencia_id": inc,
            "lineas": [{"ide": i, "codigo": c, "fecha_int": f,
                        "parte_cod": p} for i, c, f, p in lineas],
            "motivo": motivo, "en_sigrid": [x[0] for x in lineas]}


def test_f062_r25_modal_no_coincide_con_sigrid():
    quitada = _nc("quitada", 7, [(9001, "CIV", 20261005, "PT26/00251"),
                                 (9002, "CIZ", 20261009, "PT26/00251")])
    solo = _nc("solo_sigrid", None, [(91, "CIE", 20261020, None)],
               "en Sigrid y no en la plataforma")
    html = _js("pintarNoCoincide", {"obras": [
        {"no_coincide": [quitada, _nc("quitada", 8, [])]},
        {"no_coincide": [solo]}, {}]})
    assert html.startswith("<h4>No coincide con Sigrid</h4>")
    assert ("<th>Trabajador</th><th>Incidencia</th><th>Motivo</th>"
            "<th>Editar a mano en Sigrid</th>") in html
    # La quitada sin líneas en Sigrid, sin aviso (la api la borra).
    assert _celdas(html) == [
        ["Ana Ruiz", "V del 5 al 9",
         "quitada en la plataforma; sigue en Sigrid",
         ("CIV 05/10 · parte PT26/00251 · línea 9001; "
          "CIZ 09/10 · parte PT26/00251 · línea 9002")],
        ["Ana Ruiz", "sin incidencia", "en Sigrid y no en la plataforma",
         "CIE 20/10 · línea 91"]]
    assert "checkbox" not in html
    assert _js("pintarNoCoincide", {"obras": [
        {"no_coincide": [_nc("quitada", 8, [])]}]}) == ""
    assert _js("pintarNoCoincide", {}) == ""


def _lineas_inc(acciones: list) -> list[str]:
    html = _js("seccionIncidencias", {"incidencias": acciones})
    return [c[4] for c in _celdas(html)]


def test_f062_r25_modal_las_lineas_nuevas_de_incidencia():
    assert _lineas_inc([
        _accion(7, "ini", "continua", 20261005, "CIV", "PT26/00040"),
        _accion(7, "fin", "abierta", 20261009, "CIZ")]) == [
        ("inicio CIV 05/10: continúa la racha (sin línea) · "
         "fin CIZ 09/10: queda abierta (sin CIZ este mes)")]
    devolver = {**_accion(7, "devolver", "editar", 20261007, "CIZ",
                          "PT26/00040"), "fec_antes": 20261009}
    assert _lineas_inc([devolver]) == [
        "se devuelve CIZ 07/10: se cambia del 9 al 7 en el parte PT26/00040"]


def test_f062_r25_modal_pintar_las_pinta_y_no_calcula():
    cuerpo = _funcion("pintarModalPreflight")
    i = cuerpo.index("seccionIncidencias(o)")
    assert i < cuerpo.index("pintarRachas(o)") \
        < cuerpo.index("pintarCierresRacha(o)")
    assert cuerpo.index("pintarCierresRacha(o)") \
        < cuerpo.index("pintarNoCoincide(pf)") < cuerpo.index("pie-modal")
    # R25: sustituye a la lista de quitadas de F-030 R38.
    assert "seccionQuitadas" not in JS
    assert "incidencias_quitadas" not in cuerpo
    for f in ("textoRacha", "pintarRachas", "pintarCierresRacha",
              "pintarNoCoincide"):
        assert "api(" not in _funcion(f) and "fetch(" not in _funcion(f)


# ======================= R31 (D17): confirmar el cierre ==================== #
def _cierres_con_pisar(cierres: list, pisar: list) -> str:
    programa = "\n".join([
        DOM_TEXTO, *[_funcion(f) for f in FUNCIONES],
        "var state = " + json.dumps({"trabajadores": [ANA]},
                                    ensure_ascii=False) + ";",
        "var registro = { pisar: new Set(" + json.dumps(pisar) + ") };",
        "process.stdout.write(JSON.stringify(pintarCierresRacha("
        + json.dumps({"cierres_racha": cierres}, ensure_ascii=False) + ")));"])
    return _node(programa)


def test_f062_r31_modal_la_casilla_solo_en_el_cierre_a_confirmar():
    cierres = [
        _cierre("escribir", requiere_confirmar=True, clave="cierre:51"),
        _cierre("escribir", inicio_ide=52),
        _cierre("pendiente", requiere_confirmar=True, clave="cierre:53")]
    html = _cierres_con_pisar(cierres, [])
    casilla = '<input type="checkbox" class="chk-pisar" value="cierre:51">'
    # Una sola casilla, la del `escribir` que pide confirmar; desmarcada.
    assert html.count('class="chk-pisar"') == 1 and casilla in html
    filas = html.split("<tbody>")[1].split("</tr>")
    assert casilla in filas[0] and "checkbox" not in filas[1] + filas[2]
    assert "marca la casilla para cerrarla" in filas[0]
    # Al repintar, marcada si ya se había marcado.
    html = _cierres_con_pisar(cierres, ["cierre:51"])
    assert ('<input type="checkbox" class="chk-pisar" value="cierre:51" '
            "checked>") in html
    # Sin `requiere_confirmar` no hace falta `registro` (F-062 R25, igual).
    assert "checkbox" not in _js("pintarCierresRacha", {"cierres_racha": [
        _cierre("escribir")]})


def _ejecutar(respuesta: dict) -> str:
    # El `document` va antes: el trozo de `app.js` trae detrás el
    # `addEventListener` de DOMContentLoaded.
    programa = "\n".join([
        "var document = { querySelectorAll: () => [], body: { dataset: {} },",
        "  addEventListener() {} };",
        _funcion("registroEjecutar"),
        "var registro = { trabajadorIde: null };",
        "var boton = {};",
        "function $() { return boton; }",
        "var state = { anio: 2026, mes: 11 };",
        "function cerrarModal() {}",
        "async function api() { return " + json.dumps(respuesta) + "; }",
        "function toast(m) { process.stdout.write(JSON.stringify(m)); }",
        "registroEjecutar();"])
    return _node(programa)


def test_f062_r31_ejecutar_cuenta_los_cierres_pendientes():
    msg = _ejecutar({"ok": True, "obras": [
        {"escritas": [], "omitidas": [], "pendientes_confirmacion": [{}],
         "cierres_racha": [{"accion": "pendiente"}, {"accion": "escribir"}]},
        {"cierres_racha": [{"accion": "pendiente"}]}]})
    assert msg == ("Sigrid: 0 escritas · 0 omitidas · 3 pendientes de "
                   "confirmar (repite y marca pisar)")
    assert _ejecutar({"ok": True, "obras": [{"cierres_racha": [
        {"accion": "escribir"}]}]}) == ("Sigrid: 0 escritas · 0 omitidas · "
                                        "0 pendientes de confirmar")
