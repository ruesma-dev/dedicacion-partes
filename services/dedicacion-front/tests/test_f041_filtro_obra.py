# tests/test_f041_filtro_obra.py
"""F-041 · El filtro de obra casa con el texto tal como sale en la app
(incluido `Postv-`), R1-R13.

Dos familias (design §6):

- **Estáticos** sobre `static/js/app.js` (patrón de `test_f029_seleccion.py`):
  una sola fuente de la etiqueta y del texto visible, y sus usos.
- **Lógica en node** (D4 = A, decidido por el humano el 2026-10-06): se
  extrae el código REAL de las funciones de `app.js` que no tocan el DOM, se
  ejecuta en `node` con un cuadrante de prueba y se comparan las filas
  visibles y las candidatas. Sin `node`, se saltan con su motivo; el reviewer
  los exige `passed`.

Sin red ni BBDD.
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


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


# ============================ ayudante node ============================== #
#: Funciones de `app.js` que se ejecutan en node: ninguna toca el DOM.
FUNCIONES_NODE = ("normalizar", "etiquetaObra", "textoObra", "lineaCasa",
                  "fmtPct", "textoColumna", "trabajadoresVisibles",
                  "construirCatalogoObras", "candidatasDestino")


def _orden_estado() -> str:
    m = re.search(r"^const ORDEN_ESTADO = \{.*?\};", JS, re.MULTILINE)
    assert m, "no existe `const ORDEN_ESTADO = {…};` en app.js"
    return m.group(0)


def _node(cuerpo: str, estado: dict) -> object:
    """Ejecuta en node el código real de `FUNCIONES_NODE` con `state` =
    `estado` y el `cuerpo`, que deja su salida en `resultado`."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-041 "
                    "no se ejecutan")
    programa = "\n".join(
        [_orden_estado(), *(_funcion(f) for f in FUNCIONES_NODE),
         "var state = " + json.dumps(estado, ensure_ascii=False) + ";",
         "var resultado;", cuerpo,
         "process.stdout.write(JSON.stringify(resultado));"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


# ============================ datos de prueba ============================ #
OBRAS = [
    {"ide": 1, "cod": "0656", "descripcion": "Edificio Arroyo",
     "activa": True, "admite_postventa": True},
    {"ide": 2, "cod": "0700", "descripcion": "Depósito agua",
     "activa": True, "admite_postventa": False},
    {"ide": 3, "cod": "VAR-29", "descripcion": "Arroyo varios",
     "activa": True, "admite_postventa": False},
]


def _linea(obra_ide: int, cod: str, descripcion: str, pv: bool,
           porcentaje: float = 100) -> dict:
    return {"obra_ide": obra_ide, "cod": cod, "descripcion": descripcion,
            "es_postventa": pv, "porcentaje": porcentaje}


def _trab(ide: int, nombre: str, lineas: list, activo: bool = True) -> dict:
    total = sum(l["porcentaje"] for l in lineas)
    estado = "SIN_CARGA" if not lineas else ("OK" if total == 100 else "FALTA")
    return {"ide": ide, "nombre": nombre, "categoria": "Oficial",
            "activo": activo, "estado": estado, "total": total,
            "lineas": lineas}


TRABAJADORES = [
    _trab(1, "Ana", [_linea(1, "0656", "Edificio Arroyo", True)]),
    _trab(2, "Benito", [_linea(2, "0700", "Depósito agua", False)]),
    _trab(3, "Carla", [_linea(4, "0701", "Naves", False, 50),
                       _linea(1, "0656", "Edificio Arroyo", True, 50)]),
    _trab(4, "Dani", [_linea(1, "0656", "Edificio Arroyo", False)]),
    _trab(5, "Eva", [_linea(3, "VAR-29", "Arroyo varios", False)]),
    _trab(6, "Fede", []),
    _trab(7, "Gil", [], activo=False),
]


def _estado() -> dict:
    return {"trabajadores": TRABAJADORES, "obras": OBRAS,
            "catalogoObras": [], "filtroTexto": "", "filtroEstado": None,
            "soloPendientes": False,
            "columnas": ["nombre", "categoria", "asignaciones", "total"],
            "filtrosCol": {}, "orden": {"campo": "nombre", "dir": 1}}


def _columna(textos: list[str]) -> dict[str, list[str]]:
    """Filas visibles (por nombre) con cada texto en «Filtrar obra…»."""
    cuerpo = ("resultado = {};\nfor (const q of " + json.dumps(textos) +
              ") { state.filtrosCol = {asignaciones: q}; "
              "resultado[q] = trabajadoresVisibles().map((t) => t.nombre); }")
    return _node(cuerpo, _estado())


def _buscador(textos: list[str]) -> dict[str, list[str]]:
    """Filas visibles (por nombre) con cada texto en el buscador global."""
    cuerpo = ("resultado = {};\nfor (const q of " + json.dumps(textos) +
              ") { state.filtroTexto = q; "
              "resultado[q] = trabajadoresVisibles().map((t) => t.nombre); }")
    return _node(cuerpo, _estado())


def _candidatas(textos: list[str]) -> dict[str, list[str]]:
    """Etiquetas de las candidatas de «Completar al 100 %», en orden."""
    cuerpo = ("construirCatalogoObras();\nresultado = {};\nfor (const q of " +
              json.dumps(textos) + ") { resultado[q] = "
              "candidatasDestino(q).map((e) => e.cod); }")
    return _node(cuerpo, _estado())


# ================================ R1 / R2 =============================== #
def test_f041_r1_etiqueta_en_una_sola_funcion():
    etiqueta = _plano(_funcion("etiquetaObra"))
    assert etiqueta.startswith("function etiquetaObra(cod, esPostventa) {"), \
        etiqueta
    assert 'return (esPostventa ? "Postv-" : "") + cod; }' in etiqueta


def test_f041_r2_texto_visible_usa_la_etiqueta():
    texto = _plano(_funcion("textoObra"))
    assert texto.startswith("function textoObra(cod, descripcion, "
                            "esPostventa) {"), texto
    assert ('return etiquetaObra(cod, esPostventa) + " " + '
            '(descripcion || ""); }') in texto


def test_f041_r2_linea_casa_con_su_texto_visible():
    casa = _plano(_funcion("lineaCasa"))
    assert ("return normalizar(textoObra(l.cod, l.descripcion, "
            "l.es_postventa)).includes(q); }") in casa


def test_f041_r1_r2_etiqueta_y_texto_en_node():
    cuerpo = ('resultado = [etiquetaObra("0656", true), '
              'etiquetaObra("0656", false), etiquetaObra("VAR-29", false), '
              'textoObra("0656", "Edificio Arroyo", true), '
              'textoObra("0700", null, false)];')
    assert _node(cuerpo, _estado()) == [
        "Postv-0656", "0656", "VAR-29", "Postv-0656 Edificio Arroyo",
        "0700 "]


# ================================== R3 ================================== #
def test_f041_r3_postv_literal_solo_en_etiqueta_obra():
    """Ninguna otra concatenación de `Postv-` con un código en app.js. Los
    acentos graves no cuentan: en `app.js` solo aparecen en comentarios; una
    plantilla con código lleva `Postv-${`, que se vigila aparte."""
    literales = re.findall(r"[\"']Postv-[\"']", JS)
    assert len(literales) == 1, literales
    assert '"Postv-"' in _funcion("etiquetaObra")
    assert "Postv-${" not in JS


@pytest.mark.parametrize("funcion, uso", [
    ("construirCelda",
     "escapeHtml(etiquetaObra(l.cod, l.es_postventa))"),
    ("chipEditable",
     "cod.textContent = etiquetaObra(linea.cod, linea.es_postventa);"),
    ("construirCatalogoObras", "cod: etiquetaObra(o.cod, false),"),
    ("construirCatalogoObras", "cod: etiquetaObra(o.cod, true),"),
])
def test_f041_r3_los_chips_y_el_catalogo_usan_etiqueta_obra(funcion, uso):
    assert uso in _plano(_funcion(funcion))


# ================================== R4 ================================== #
def test_f041_r4_la_columna_casa_por_linea():
    visibles = _plano(_funcion("trabajadoresVisibles"))
    assert ('const casa = clave === "asignaciones" ? '
            "t.lineas.some((l) => lineaCasa(l, filtro)) : "
            "normalizar(textoColumna(t, clave)).includes(filtro);") in visibles
    assert "if (!casa) return false;" in visibles


def test_f041_r4_texto_columna_sin_rama_asignaciones():
    columna = _funcion("textoColumna")
    assert "asignaciones" not in columna
    assert not re.search(r"[\"']postv", columna)


def test_f041_r4_d2_naves_postv_no_casa_a_caballo():
    """D2 = A: `naves postv` casaba con Carla (`0701 Naves` + otra línea
    `Postv-`); por línea, con nadie."""
    assert _columna(["naves postv"]) == {"naves postv": []}


# ================================== R5 ================================== #
PREFIJOS = ["pos", "post", "postv", "postv-", "Postv-06", "Postv-0656"]


def test_f041_r5_pos_y_completando_acota_letra_a_letra():
    res = _columna(PREFIJOS)
    assert res["pos"] == ["Ana", "Benito", "Carla"]
    for q in PREFIJOS[1:]:
        assert res[q] == ["Ana", "Carla"], q
    for anterior, siguiente in zip(PREFIJOS, PREFIJOS[1:]):
        assert set(res[siguiente]) <= set(res[anterior]), siguiente


# ================================== R6 ================================== #
def test_f041_r6_ignora_mayusculas_y_tildes():
    res = _columna(["POSTV-0656 Edif", "depósito", "DEPOSITO"])
    assert res["POSTV-0656 Edif"] == ["Ana", "Carla"]
    assert res["depósito"] == res["DEPOSITO"] == ["Benito"]


# ================================== R7 ================================== #
def test_f041_r7_casa_con_cualquier_parte_del_texto_visible():
    res = _columna(["0656", "0656 edif", "Postv-0656", "edificio"])
    assert res["0656"] == ["Ana", "Carla", "Dani"]
    assert res["0656 edif"] == ["Ana", "Carla", "Dani"]
    assert res["Postv-0656"] == ["Ana", "Carla"]
    assert res["edificio"] == ["Ana", "Carla", "Dani"]


# ================================== R8 ================================== #
def test_f041_r8_sin_filtro_las_mismas_filas_y_orden():
    assert _columna([""]) == {
        "": ["Ana", "Benito", "Carla", "Dani", "Eva", "Fede"]}


# ================================== R9 ================================== #
def test_f041_r9_buscador_global_usa_el_texto_visible():
    pajar = _plano(_funcion("trabajadoresVisibles")).split("const pajar")[1]
    assert ("t.lineas.map((l) => textoObra(l.cod, l.descripcion, "
            'l.es_postventa)).join(" ")') in pajar


def test_f041_r9_buscador_global_encuentra_postventa():
    res = _buscador(["postv", "Postv-0656", "pos", "beni", "naves postv"])
    assert res["postv"] == ["Ana", "Carla"]
    assert res["Postv-0656"] == ["Ana", "Carla"]
    assert res["pos"] == ["Ana", "Benito", "Carla"]
    assert res["beni"] == ["Benito"]
    # Sigue siendo una búsqueda sobre todos los campos juntos (design §5).
    assert res["naves postv"] == ["Carla"]


# ================================= R10 ================================== #
def test_f041_r10_la_clave_del_catalogo_es_el_texto_visible():
    construir = _plano(_funcion("construirCatalogoObras"))
    assert "clave: normalizar(textoObra(o.cod, o.descripcion, false))," \
        in construir
    assert "clave: normalizar(textoObra(o.cod, o.descripcion, true))," \
        in construir
    assert not re.search(r"[\"']postv", construir)


def test_f041_r10_catalogo_en_node():
    cuerpo = ("construirCatalogoObras(); resultado = state.catalogoObras.map("
              "(e) => [e.obra.ide, e.pv, e.cod, e.clave]);")
    assert _node(cuerpo, _estado()) == [
        [1, False, "0656", "0656 edificio arroyo"],
        [1, True, "Postv-0656", "postv-0656 edificio arroyo"],
        [2, False, "0700", "0700 deposito agua"],
        [3, False, "VAR-29", "var-29 arroyo varios"],
    ]


def test_f041_r10_d1_postventa_no_casa():
    """D1 = A: `postventa` no es texto visible; ni filas ni candidatas."""
    assert _columna(["postventa", "postve"]) == {"postventa": [], "postve": []}
    assert _candidatas(["postventa"]) == {"postventa": []}


# ================================= R11 ================================== #
TEXTOS_R11 = ["pos", "post", "postv", "postv-", "Postv-0656", "0656",
              "0656 edif", "edificio", "arroyo", "depósito", "naves",
              "var-2", "29", "postventa", "agua"]


def test_f041_r11_columna_y_completar_parten_del_mismo_texto():
    cuerpo = (
        "construirCatalogoObras();\n"
        "const catalogo = state.catalogoObras.map((e) => e.obra.ide + '|' + "
        "e.pv);\nresultado = {catalogo: catalogo, textos: {}};\n"
        "for (const q of " + json.dumps(TEXTOS_R11) + ") {\n"
        "  state.filtrosCol = {asignaciones: q};\n"
        "  const visibles = trabajadoresVisibles().map((t) => t.nombre);\n"
        "  const lineas = [];\n"
        "  state.trabajadores.forEach((t) => t.lineas.forEach((l) => "
        "lineas.push({clave: l.obra_ide + '|' + l.es_postventa, "
        "nombre: t.nombre, casa: lineaCasa(l, normalizar(q))})));\n"
        "  const cands = candidatasDestino(q).map((e) => e.obra.ide + '|' + "
        "e.pv);\n"
        "  resultado.textos[q] = {visibles, lineas, cands};\n}")
    res = _node(cuerpo, _estado())
    catalogo = set(res["catalogo"])
    for q, r in res["textos"].items():
        cands = set(r["cands"])
        for l in r["lineas"]:
            if l["casa"]:
                # La línea casa ⇒ su fila se ve y su entrada es candidata.
                assert l["nombre"] in r["visibles"], (q, l)
                if l["clave"] in catalogo:
                    assert l["clave"] in cands, (q, l)
            elif l["clave"] in cands:
                # Candidata ⇒ toda línea de esa obra y modo casa.
                pytest.fail(f"{q!r}: candidata {l['clave']} sin casar {l}")
    assert res["textos"]["postv"]["cands"] == ["1|true"]
    assert res["textos"]["pos"]["cands"] == ["1|true", "2|false"]


# ================================= R12 ================================== #
def test_f041_r12_etiqueta_exacta_primero():
    res = _candidatas(["0656", "Postv-0656", "postv"])
    assert res["0656"] == ["0656", "Postv-0656"]
    assert res["Postv-0656"] == ["Postv-0656"]
    assert res["postv"] == ["Postv-0656"]


def test_f041_r12_dialogo_sigue_precargado_con_filtrar_obra():
    dialogo = _plano(_funcion("montarDialogoCompletar"))
    assert 'input.value = state.filtrosCol.asignaciones || "";' in dialogo
    assert "e.clave.includes(q)" in _plano(_funcion("candidatasDestino"))


# ================================= R13 ================================== #
def test_f041_r13_sin_literal_var_ni_ramas_por_prefijo():
    assert not re.search(r"[\"']VAR", JS)
    assert "`VAR" not in re.sub(r"//.*", "", JS)
    etiqueta = _plano(_funcion("etiquetaObra"))
    assert etiqueta.count("?") == 1, etiqueta
    assert "if" not in etiqueta.replace("function", ""), etiqueta


def test_f041_r13_var_29_casa_como_cualquier_obra():
    res = _columna(["var", "var-2", "29", "arroyo", "Arroyo varios"])
    assert res["var"] == ["Eva"]
    assert res["var-2"] == ["Eva"]
    assert res["29"] == ["Eva"]
    assert res["arroyo"] == ["Ana", "Carla", "Dani", "Eva"]
    assert res["Arroyo varios"] == ["Eva"]
    assert _candidatas(["var-2", "29"]) == {"var-2": ["VAR-29"],
                                             "29": ["VAR-29"]}
