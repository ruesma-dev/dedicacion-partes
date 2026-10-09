# tests/test_f050_subfilas.py
"""F-050 · Subfilas por obra y columna «Partida» en el cuadrante
(R22-R25, R28).

Dos familias, como F-041: comprobaciones ESTÁTICAS de `static/js/app.js` y
`static/css/styles.css` para lo que toca el DOM (subfilas, `rowSpan`, el
clic de la celda), y el código REAL de las funciones puras en `node`
(preferencias de columnas, filtros, buscador y texto de la partida). Sin
`node`, los de lógica se saltan con su motivo; el reviewer los exige
`passed`. Sin red ni BBDD.
"""
from __future__ import annotations

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
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _const(nombre: str) -> str:
    m = re.search(rf"^const {nombre} = .*?;$", JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe `const {nombre}` en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


def _node(funciones, cuerpo: str, estado: dict, consts=()) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    programa = "\n".join(
        [*(_const(c) for c in consts), *(_funcion(f) for f in funciones),
         "var state = " + json.dumps(estado, ensure_ascii=False) + ";",
         "var resultado;", cuerpo,
         "process.stdout.write(JSON.stringify(resultado));"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


# ================================ R23 ==================================== #
def test_f050_r23_columna_partida_a_la_derecha_de_obras():
    columnas = _plano(_const("COLUMNAS"))
    assert ('partida: { titulo: "Partida", ancho: 320, ordenable: false, '
            'placeholder: "Filtrar partida…", },') in columnas
    assert _plano(_const("ORDEN_COLUMNAS_DEFECTO")) == (
        'const ORDEN_COLUMNAS_DEFECTO = ["nombre", "categoria", '
        '"asignaciones", "partida", "total"];')



def _prefs(guardadas) -> list[str]:
    cuerpo = (
        "var localStorage = {getItem: () => " + json.dumps(json.dumps(
            guardadas)) + "};\ncargarPrefsTabla();\n"
        "resultado = state.columnas;")
    return _node(["cargarPrefsTabla"], cuerpo,
                 {"columnas": [], "anchos": {}},
                 consts=("COLUMNAS", "ORDEN_COLUMNAS_DEFECTO", "CLAVE_TABLA"))


@pytest.mark.parametrize("guardadas, esperado", [
    ({"orden": ["total", "asignaciones", "nombre", "categoria"]},
     ["total", "asignaciones", "partida", "nombre", "categoria"]),
    ({"orden": ["nombre", "categoria", "asignaciones", "total"]},
     ["nombre", "categoria", "asignaciones", "partida", "total"]),
    ({"orden": ["partida", "total", "nombre", "categoria", "asignaciones"]},
     ["partida", "total", "nombre", "categoria", "asignaciones"]),
    ({"orden": ["nombre", "total"]},
     ["nombre", "total", "categoria", "asignaciones", "partida"]),
])
def test_f050_r23_preferencias_viejas_meten_partida_tras_obras(guardadas,
                                                               esperado):
    assert _prefs(guardadas) == esperado


# ================================ R22 ==================================== #
def test_f050_r22_una_subfila_por_linea_con_rowspan():
    fila = _plano(_funcion("construirFila"))
    assert "const frag = document.createDocumentFragment();" in fila
    assert "const n = Math.max(1, t.lineas.length);" in fila
    assert 'tr.className = idx ? "fila subfila" : "fila";' in fila
    assert "tr.dataset.linea = idx;" in fila
    assert ("if (COLUMNAS_POR_LINEA.includes(clave)) { "
            "tr.appendChild(construirCelda(t, clave, idx)); }") in fila
    assert ("else if (!idx) { const td = construirCelda(t, clave, idx); "
            "td.rowSpan = n; tr.appendChild(td); }") in fila
    assert "return frag;" in fila
    assert _plano(_const("COLUMNAS_POR_LINEA")) == (
        'const COLUMNAS_POR_LINEA = ["asignaciones", "partida"];')


def test_f050_r22_la_celda_de_obras_pinta_solo_su_linea():
    celda = _plano(_funcion("construirCelda"))
    assert celda.startswith("function construirCelda(t, clave, idx) {")
    obras = celda.split('clave === "asignaciones"')[1].split(
        'clave === "partida"')[0]
    assert "const l = t.lineas[idx];" in obras
    assert "t.lineas.forEach" not in celda
    assert "'<span class=\"sin-carga-texto\">sin carga</span>'" in obras


def test_f050_r22_refrescar_rehace_todas_las_subfilas():
    refrescar = _plano(_funcion("refrescarCeldasFila"))
    assert ("const viejas = document.querySelectorAll( "
            "`#cuerpo tr.fila[data-ide=\"${t.ide}\"]`);") in refrescar
    assert "viejas[0].before(construirFila(t));" in refrescar
    assert "viejas.forEach((tr) => tr.remove());" in refrescar


def test_f050_r22_css_de_las_subfilas():
    assert re.search(r"tr\.fila\.subfila td\s*\{[^}]*border-top", CSS)
    assert re.search(r"td\[rowspan\]\s*\{[^}]*vertical-align: top", CSS)


# ================================ R24 ==================================== #
def test_f050_r24_texto_de_la_partida():
    cuerpo = ("resultado = [textoPartida({partida_ide: 80003, partida_cod: "
              "'CI.1.9', partida_res: 'ADMINISTRATIVO'}), textoPartida("
              "{partida_ide: 80003, partida_cod: null, partida_res: null}), "
              "textoPartida({partida_ide: 7, partida_cod: 'CI.2', "
              "partida_res: null}), textoPartida({partida_ide: null}), "
              "textoPartida(null)];")
    assert _node(["textoPartida"], cuerpo, {}) == [
        "CI.1.9 · ADMINISTRATIVO", "partida 80003", "CI.2", "", ""]


def test_f050_r24_celda_elegida_fija_o_automatica():
    celda = _plano(_funcion("construirCelda"))
    partida = celda.split('clave === "partida"')[1]
    assert "const l = t.lineas[idx];" in partida
    assert ("if (l.partida_fija) { td.classList.add(\"fija\"); "
            "td.innerHTML = `<span class=\"partida-fija\" title=\"Partida "
            "fija de la entrada\">${escapeHtml(l.descripcion)}</span>`; }"
            ) in partida
    assert ("else if (l.partida_ide != null) { td.innerHTML = "
            "`<span class=\"partida-elegida\">${escapeHtml(textoPartida(l))}"
            "</span>`; }") in partida
    assert ("else { td.innerHTML = '<span class=\"partida-auto\">"
            "automática</span>'; }") in partida
    assert re.search(r"\.partida-auto\s*\{[^}]*font-style: italic", CSS)


# ================================ R25 ==================================== #
def test_f050_r25_clic_en_la_partida_abre_el_selector_sin_el_editor():
    partida = _plano(_funcion("construirCelda")).split(
        'clave === "partida"')[1]
    assert ('if (state.periodoEstado === "ABIERTO" && !l.partida_fija) { '
            'td.classList.add("editable"); td.addEventListener("click", '
            "(ev) => { ev.stopPropagation(); abrirSelectorPartida(t.ide, "
            "l.obra_ide, l.es_postventa, td); }); }") in partida
    assert re.search(r"\.celda-partida\.editable\s*\{[^}]*cursor: pointer",
                     CSS)


# ================================ R28 ==================================== #
VISIBLES = ["normalizar", "etiquetaObra", "textoObra", "lineaCasa", "fmtPct",
            "textoColumna", "trabajadoresVisibles"]


def _linea(obra, cod, partida=None, fija=False) -> dict:
    p = partida or (None, None, None)
    return {"obra_ide": obra, "cod": cod, "descripcion": f"Obra {cod}",
            "es_postventa": False, "porcentaje": 50, "partida_ide": p[0],
            "partida_cod": p[1], "partida_res": p[2], "partida_fija": fija}


TRABAJADORES = [
    {"ide": 1, "nombre": "Ana", "categoria": "Encargado", "activo": True,
     "estado": "OK", "total": 100, "lineas": [
         _linea(1, "0694", (80003, "CI.1.9", "ADMINISTRATIVO")),
         _linea(2, "0696")]},
    {"ide": 2, "nombre": "Benito", "categoria": "Oficial", "activo": True,
     "estado": "OK", "total": 100, "lineas": [
         _linea(3, "0700", (90001, "CD.4", "Jefatura de grupo"))]},
    {"ide": 3, "nombre": "Carla", "categoria": "Peón", "activo": True,
     "estado": "OK", "total": 100, "lineas": [
         _linea(4, "VAR-29", fija=True)]},
]


def _visibles(filtros: dict) -> dict:
    estado = {"trabajadores": TRABAJADORES, "filtroTexto": "",
              "filtroEstado": None, "soloPendientes": False,
              "columnas": ["nombre", "categoria", "asignaciones", "partida",
                           "total"], "filtrosCol": {},
              "orden": {"campo": "nombre", "dir": 1}}
    cuerpo = ("resultado = {};\nfor (const [tipo, q] of " +
              json.dumps(list(filtros.items())) + ") {\n"
              "  state.filtrosCol = {}; state.filtroTexto = '';\n"
              "  if (tipo.startsWith('busca')) state.filtroTexto = q;\n"
              "  else state.filtrosCol = {partida: q};\n"
              "  resultado[tipo] = trabajadoresVisibles().map((t) => "
              "t.nombre);\n}")
    return _node(VISIBLES, "const ORDEN_ESTADO = {OK: 3};\n" + cuerpo,
                 estado)


def test_f050_r28_filtro_partida_casa_linea_a_linea():
    res = _visibles({"ci19": "ci.1.9 admin", "jef": "JEFATURA",
                     "auto": "automatica", "nada": "ci.1.9 jefatura",
                     "vacio": ""})
    assert res["ci19"] == ["Ana"]
    assert res["jef"] == ["Benito"]
    assert res["auto"] == ["Ana"]
    assert res["nada"] == []
    assert res["vacio"] == ["Ana", "Benito", "Carla"]


def test_f050_r28_buscador_libre_incluye_la_partida():
    res = _visibles({"busca1": "administrativo", "busca2": "cd.4",
                     "busca3": "0696"})
    assert res == {"busca1": ["Ana"], "busca2": ["Benito"],
                   "busca3": ["Ana"]}


def test_f050_r28_el_filtro_de_partida_va_en_linea():
    """El arnés node de F-041 solo carga sus funciones: el texto de la
    partida se calcula dentro de `trabajadoresVisibles`."""
    visibles = _plano(_funcion("trabajadoresVisibles"))
    assert "textoPartida" not in visibles
    assert 'if (clave === "partida") {' in visibles


# ============ T15 · casos que la campaña manual dejó vivos ============ #
def test_f050_r28_la_partida_fija_casa_por_su_descripcion():
    assert _visibles({"fija": "obra var-29"}) == {"fija": ["Carla"]}
