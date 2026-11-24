# tests/test_f074_celda.py
"""F-074 · T10-T11: la celda Partida ya no dice «automática» (R14, R17-R20).

- R17: lo primero que aplique: elegida; fija; propuesta en cursiva con su
  método (también la de postventa, «obra de postventa»); «buscando
  partida…»; «no encuentra partida» con su motivo; «sin calcular» (periodo
  ABIERTO); «—». Nunca «automática».
- R18 (D1): «no encuentra partida» es un aviso (`partida-sin`, sin cursiva)
  con el motivo en el título; abierto, el clic abre el selector.
- R19: el estado lo dan las claves de la API; solo `periodoEstado` separa
  «sin calcular» de «—».
- R14: las marcas de las subfilas (`subfilas_pendientes`,
  `subfilas_no_encontradas`) y las no encontradas de las líneas llegan con
  la consulta de 5 s.
- R20: el filtro «Partida» y el buscador libre casan con el texto de la
  celda, línea a línea y subfila a subfila (F-067: si se ven).

El código REAL de `static/js/app.js` en `node`; lo que toca el DOM, en
estático. Sin `node`, los de lógica se saltan con su motivo (el reviewer los
exige `passed`).
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
JS = (RAIZ / "static" / "js" / "app.js").read_text(encoding="utf-8")
CSS = (RAIZ / "static" / "css" / "styles.css").read_text(encoding="utf-8")


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |"
                  rf"^const |^// ---|\Z)", JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


ESCAPE = """
function escapeHtml(t) { return String(t == null ? "" : t)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;"); }
"""
CELDA = ("textoPartida", "rotuloOrigen", "htmlPartida")
FILTRO = ("normalizar", "etiquetaObra", "textoObra", "lineaCasa", "fmtPct",
          "textoColumna", "rotuloOrigen", "trabajadoresVisibles")


def _node(funciones, cuerpo: str, estado: dict) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-074 "
                    "no se ejecutan")
    orden = re.search(r"^const ORDEN_ESTADO = \{.*?\};", JS,
                      re.MULTILINE).group(0)
    programa = "\n".join(
        [orden, ESCAPE, *(_funcion(f) for f in funciones),
         "var state = " + json.dumps(estado, ensure_ascii=False) + ";",
         "var resultado;", cuerpo,
         "process.stdout.write(JSON.stringify(resultado));"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


def _l(obra=1, **kw):
    return {"obra_ide": obra, "cod": f"0{obra}", "descripcion": "OBRA",
            "es_postventa": False, "porcentaje": 100, "partida_ide": None,
            "partida_cod": None, "partida_res": None, "partida_fija": False,
            "propuesta_cod": None, "propuesta_res": None,
            "propuesta_metodo": None, **kw}


ELEGIDA = {"partida_ide": 7, "partida_cod": "CI.1.9", "partida_res": "ADM"}
PROP = {"propuesta_cod": "CI.1.20", "propuesta_res": "JEFE DE OBRA",
        "propuesta_metodo": "auto_nombre"}
PV = {"propuesta_cod": "0656", "propuesta_res": "TOMARES",
      "propuesta_metodo": "postventa"}
MOTIVO = "ningún paso de la regla da partida"

#: (línea, periodo, html esperado): un caso por estado de R17.
ESTADOS = [
    (_l(**ELEGIDA, propuesta_pendiente=True), "ABIERTO",
     '<span class="partida-elegida">CI.1.9 · ADM</span>'),
    (_l(**PROP, propuesta_no_encontrada=True), "ABIERTO",
     '<em class="partida-propuesta" title="Propuesta: casada por nombre">'
     'CI.1.20 · JEFE DE OBRA<span class="partida-metodo"> · casada por '
     'nombre</span></em>'),
    (_l(es_postventa=True, **PV), "ABIERTO",
     '<em class="partida-propuesta" title="Propuesta: obra de postventa">'
     '0656 · TOMARES<span class="partida-metodo"> · obra de postventa'
     '</span></em>'),
    (_l(propuesta_pendiente=True), "ABIERTO",
     '<span class="partida-auto buscando">buscando partida…</span>'),
    (_l(propuesta_no_encontrada=True, propuesta_motivo=MOTIVO), "ABIERTO",
     f'<span class="partida-sin" title="{MOTIVO}">no encuentra partida'
     '</span>'),
    (_l(propuesta_no_encontrada=True), "CERRADO",
     '<span class="partida-sin" title="La regla no encuentra partida">'
     'no encuentra partida</span>'),
    (_l(), "ABIERTO", '<span class="partida-auto">sin calcular</span>'),
    (_l(), "CERRADO", '<span class="partida-auto">—</span>'),
    (_l(), None, '<span class="partida-auto">—</span>'),
]
IDS = ["elegida", "propuesta", "postventa", "buscando", "no_encuentra",
       "no_encuentra_sin_motivo", "sin_calcular", "cerrado", "sin_periodo"]


# ========================= R17-R19 · la celda ============================ #
@pytest.mark.parametrize("linea, periodo, esperado", ESTADOS, ids=IDS)
def test_f074_r17_cada_estado_de_la_celda(linea, periodo, esperado):
    r = _node(CELDA, f"resultado = htmlPartida({json.dumps(linea)});",
              {"periodoEstado": periodo})
    assert r == esperado
    assert "automática" not in r


def test_f074_r17_la_subfila_pinta_igual():
    """La subfila delega en la misma `htmlPartida` (F-044)."""
    assert "td.innerHTML = htmlPartida(v);" in _plano(
        _funcion("construirCeldaVinculado"))
    v = {"vinculado_ide": 10, "propuesta_no_encontrada": True,
         "propuesta_motivo": "sin cuenta"}
    r = _node(CELDA, f"resultado = htmlPartida({json.dumps(v)});",
              {"periodoEstado": "ABIERTO"})
    assert r == ('<span class="partida-sin" title="sin cuenta">'
                 'no encuentra partida</span>')


def test_f074_r17_la_celda_de_la_linea_delega_en_htmlpartida():
    celda = _plano(_funcion("construirCelda"))
    assert "td.innerHTML = htmlPartida(l);" in celda
    assert "automática" not in celda


def test_f074_r17_ninguna_automatica_en_el_front():
    assert "automática" not in _funcion("htmlPartida")
    assert ">automática<" not in JS
    assert "partida-auto\">automática" not in JS


def test_f074_r18_aviso_sin_cursiva():
    m = re.search(r"\.partida-sin \{([^}]*)\}", CSS)
    assert m and "font-style: normal" in m.group(1)


def test_f074_r18_abierto_el_clic_abre_el_selector():
    celda = _plano(_funcion("construirCelda"))
    assert ('if (state.periodoEstado === "ABIERTO" && !l.partida_fija) '
            '{ td.classList.add("editable");') in celda


def test_f074_r19_el_front_no_mira_la_cola_ni_el_universo():
    celda = _funcion("htmlPartida")
    for prohibido in ("propuestasEnCurso", "obra_admite_postventa",
                      "es_postventa"):
        assert prohibido not in celda


# ====================== R13-R14 · las marcas ============================= #
CONSULTA = ("textoPartida", "rotuloOrigen", "htmlPartida",
            "aplicarPropuestas", "aplicarPendientes", "aplicarNoEncontradas",
            "aplicarMarcasSubfilas", "seguirPropuestas", "consultarPropuestas")
ENTORNO = """
var INTERVALO_PROPUESTAS = 5000;
var propuestas = {generacion: 0, timer: null};
var setTimeout = () => 1; var clearTimeout = () => {};
var respuestas = [];
async function api(ruta) { const r = respuestas.shift();
                           if (r instanceof Error) throw r; return r; }
function repintarCeldasPartida() {}
"""


def _consulta(respuesta, estado: dict) -> dict:
    cuerpo = (ENTORNO + "respuestas.push(" + json.dumps(respuesta) + ");"
              "(async () => { await consultarPropuestas(0, '/x');"
              "for (let i = 0; i < 20; i++) await Promise.resolve();"
              "process.stdout.write(JSON.stringify(state.trabajadores)); })();")
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado")
    programa = "\n".join(
        [ESCAPE, *(_funcion(f) for f in CONSULTA),
         "var state = " + json.dumps(estado, ensure_ascii=False) + ";",
         cuerpo])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


def _estado_marcas():
    sub = {"vinculado_ide": 10, "partida_ide": None}
    return {"trabajadores": [{"ide": 14, "lineas": [
        _l(100, vinculados=[dict(sub)]), _l(101, es_postventa=True,
                                            propuesta_no_encontrada=True,
                                            propuesta_motivo="no casa")]}]}


def test_f074_r13_r14_la_consulta_copia_las_marcas():
    [t] = _consulta({"en_curso": False, "lineas": [], "pendientes": [],
                     "no_encontradas": [{"trabajador_ide": 14, "obra_ide": 100,
                                         "es_postventa": False,
                                         "motivo": MOTIVO}],
                     "subfilas_no_encontradas": [{
                         "trabajador_ide": 14, "obra_ide": 100,
                         "es_postventa": False, "vinculado_ide": 10,
                         "motivo": "sin cuenta"}]}, _estado_marcas())
    l100, l101 = t["lineas"]
    assert (l100["propuesta_no_encontrada"], l100["propuesta_motivo"]) == (
        True, MOTIVO)
    assert (l100["vinculados"][0]["propuesta_no_encontrada"],
            l100["vinculados"][0]["propuesta_motivo"]) == (True, "sin cuenta")
    # La de postventa la marca el cuadrante (su obra no casa): no se toca.
    assert l101["propuesta_motivo"] == "no casa"


def test_f074_r14_subfila_pendiente_y_lo_que_no_viene_deja_de_estarlo():
    estado = _estado_marcas()
    estado["trabajadores"][0]["lineas"][0].update(
        propuesta_no_encontrada=True, propuesta_motivo="viejo")
    [t] = _consulta({"en_curso": True, "lineas": [], "pendientes": [],
                     "subfilas_pendientes": [{
                         "trabajador_ide": 14, "obra_ide": 100,
                         "es_postventa": False, "vinculado_ide": 10}]}, estado)
    l100 = t["lineas"][0]
    assert "propuesta_no_encontrada" not in l100
    assert l100["vinculados"][0]["propuesta_pendiente"] is True


def test_f074_r13_si_la_api_falla_las_no_encontradas_se_quedan():
    estado = _estado_marcas()
    estado["trabajadores"][0]["lineas"][0].update(
        propuesta_no_encontrada=True, propuesta_motivo=MOTIVO)
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado")
    programa = "\n".join(
        [ESCAPE, *(_funcion(f) for f in CONSULTA),
         "var state = " + json.dumps(estado) + ";", ENTORNO,
         "respuestas.push(new Error('caída'));",
         "(async () => { await consultarPropuestas(0, '/x');"
         "process.stdout.write(JSON.stringify(state.trabajadores)); })();"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    [t] = json.loads(salida.stdout)
    assert t["lineas"][0]["propuesta_no_encontrada"] is True


# ============================ R20 · el filtro ============================ #
def _trab(ide, nombre, lineas):
    return {"ide": ide, "nombre": nombre, "categoria": "", "activo": True,
            "estado": "OK", "total": 100, "lineas": lineas}


TRABAJADORES = [
    _trab(1, "Ana", [_l(1, **ELEGIDA)]),
    _trab(2, "Benito", [_l(2, **PROP)]),
    _trab(3, "Carla", [_l(3, propuesta_pendiente=True)]),
    _trab(4, "Dani", [_l(4, propuesta_no_encontrada=True,
                         propuesta_motivo=MOTIVO)]),
    _trab(5, "Eva", [_l(5)]),
    _trab(6, "Fede", [_l(6, partida_fija=True, descripcion="VAR ARROYO")]),
    _trab(7, "Gil", [_l(7, **ELEGIDA, vinculados=[
        {"vinculado_ide": 10, "propuesta_no_encontrada": True}])]),
    _trab(8, "Hugo", [_l(8, es_postventa=True, **PV)]),
]


def _visibles(campo: str, textos: list[str], ver_vinculados=True,
              periodo="ABIERTO") -> dict:
    asignar = ("state.filtrosCol = {partida: q};" if campo == "partida"
               else "state.filtroTexto = q;")
    cuerpo = ("resultado = {};\nfor (const q of " + json.dumps(textos) +
              ") { " + asignar + " resultado[q] = "
              "trabajadoresVisibles().map((t) => t.nombre); }")
    return _node(FILTRO, cuerpo, {
        "trabajadores": TRABAJADORES, "filtroTexto": "", "filtroEstado": None,
        "soloPendientes": False, "periodoEstado": periodo,
        "verVinculados": ver_vinculados,
        "columnas": ["nombre", "asignaciones", "partida"], "filtrosCol": {},
        "orden": {"campo": "nombre", "dir": 1}})


@pytest.mark.parametrize("campo", ["partida", "libre"])
def test_f074_r20_casan_con_el_texto_de_la_celda(campo):
    r = _visibles(campo, ["automática", "no encuentra", "buscando",
                          "sin calcular", "casada por nombre",
                          "obra de postventa", "ci.1.9 · adm", "ci.1.9 adm",
                          "var arroyo"])
    assert r["automática"] == []
    assert r["no encuentra"] == ["Dani", "Gil"]
    assert r["buscando"] == ["Carla"]
    assert r["sin calcular"] == ["Eva"]
    assert r["casada por nombre"] == ["Benito"]
    assert r["obra de postventa"] == ["Hugo"]
    assert r["ci.1.9 · adm"] == ["Ana", "Gil"]
    # Sin el «·», como F-050 R28 («ci.1.9 admin»).
    assert r["ci.1.9 adm"] == ["Ana", "Gil"]
    assert r["var arroyo"] == ["Fede"]


def test_f074_r20_sin_vinculados_no_mira_las_subfilas():
    for campo in ("partida", "libre"):
        assert _visibles(campo, ["no encuentra"], ver_vinculados=False)[
            "no encuentra"] == ["Dani"]


def test_f074_r20_cerrado_el_hueco_es_la_raya():
    r = _visibles("partida", ["sin calcular", "—"], periodo="CERRADO")
    assert r["sin calcular"] == [] and r["—"] == ["Eva"]


def _texto_visible(fragmento: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragmento))


@pytest.mark.parametrize("linea, periodo, esperado", ESTADOS, ids=IDS)
def test_f074_r20_el_filtro_y_la_celda_dicen_lo_mismo(linea, periodo,
                                                      esperado):
    """El texto en línea de `trabajadoresVisibles` es el visible de
    `htmlPartida`, estado a estado: casa justo con ese texto entero."""
    texto = _texto_visible(esperado).lower()
    r = _node(FILTRO, "state.filtrosCol = {partida: " + json.dumps(texto) +
              "}; resultado = trabajadoresVisibles().map((t) => t.nombre);",
              {"trabajadores": [_trab(1, "Ana", [linea])], "filtroTexto": "",
               "filtroEstado": None, "soloPendientes": False,
               "periodoEstado": periodo, "columnas": ["nombre", "partida"],
               "filtrosCol": {}, "orden": {"campo": "nombre", "dir": 1}})
    assert r == ["Ana"]
