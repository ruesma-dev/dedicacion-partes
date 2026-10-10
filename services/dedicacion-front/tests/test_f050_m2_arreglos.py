# tests/test_f050_m2_arreglos.py
"""F-050 · T15c: los arreglos de la MANUAL M2 (humano, 2026-10-11).

1. La tabla cabe en la ventana (las columnas se encogen hasta su mínimo; si
   ni así cabe, scroll horizontal) sin tocar las preferencias de anchos.
2. El cursor se marca igual en todas las subfilas: fondo en todas y una sola
   barra a cada lado del bloque del trabajador.
3. El selector de partida se abre al instante con «Cargando partidas…», un
   segundo clic no abre otro y solo pinta la respuesta del último pedido.
4. En el modal, el selector sale encima del modal y anclado a su línea; abrir
   (o repintar) el modal cierra cualquier selector, también uno cargando.
5. Cambiar una partida en el modal repite el preflight SOLO de la obra de esa
   línea y la sustituye en el modal; las demás obras se quedan como estaban.

El código REAL de `app.js` en `node` con un DOM mínimo de mentira (patrón de
F-042 y F-049); lo demás, estático sobre `app.js` y `styles.css`. Sin `node`
se saltan con su motivo; el reviewer los exige `passed`. Sin red.
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


def _regla(selector: str) -> str:
    m = re.search(rf"(?:^|\}})\s*{re.escape(selector)}\s*\{{([^}}]*)\}}", CSS,
                  re.MULTILINE)
    assert m, f"no está la regla `{selector}` en styles.css"
    return _plano(m.group(1))


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


# ================== 1 · la tabla cabe en la ventana ===================== #
PREFERIDOS = [280, 210, 560, 320, 190]      # los de COLUMNAS, en su orden
MINIMOS = [160, 100, 150, 150, 190]


def _ajustados(preferidos, minimos, disponible) -> list:
    return _node("\n".join([
        _funcion("anchosAjustados"),
        "process.stdout.write(JSON.stringify(anchosAjustados(" +
        ", ".join(json.dumps(x) for x in (preferidos, minimos, disponible)) +
        ")));"]))


def test_f050_m2_1_si_cabe_los_anchos_preferidos():
    assert _ajustados(PREFERIDOS, MINIMOS, 1600) == PREFERIDOS
    assert _ajustados(PREFERIDOS, MINIMOS, 1560) == PREFERIDOS


def test_f050_m2_1_si_no_cabe_se_encogen_hasta_caber():
    """1046 px (la ventana de la captura): lo que sobra de cada columna
    sobre su mínimo se reparte en proporción; Total no encoge."""
    anchos = _ajustados(PREFERIDOS, MINIMOS, 1046)
    assert anchos == [203, 140, 299, 212, 190]
    assert sum(anchos) <= 1046


def test_f050_m2_1_nunca_bajo_el_minimo_y_entonces_scroll():
    assert _ajustados(PREFERIDOS, MINIMOS, 500) == MINIMOS
    assert _ajustados(PREFERIDOS, MINIMOS, 0) == MINIMOS


def test_f050_m2_1_una_preferencia_bajo_el_minimo_se_respeta():
    """El usuario puede dejar una columna en 70 px (la manija): no crece."""
    assert _ajustados([80, 210, 560, 320, 190], MINIMOS, 1000) == [
        80, 152, 346, 231, 190]
    assert _ajustados([80, 100, 150, 150, 190], MINIMOS, 300) == [
        80, 100, 150, 150, 190]


def test_f050_m2_1_cada_columna_tiene_su_minimo():
    assert _node("\n".join([
        _const("COLUMNAS"), _const("MINIMO_COLUMNA"),
        "process.stdout.write(JSON.stringify([Object.keys(COLUMNAS), "
        "Object.keys(MINIMO_COLUMNA), Object.keys(COLUMNAS).map((c) => "
        "MINIMO_COLUMNA[c] <= COLUMNAS[c].ancho)]));"])) == [
        ["nombre", "categoria", "asignaciones", "partida", "total"],
        ["nombre", "categoria", "asignaciones", "partida", "total"],
        [True] * 5]


def _sincronizar(anchos: dict, disponible: int, columnas=None) -> dict:
    columnas = columnas or ["nombre", "categoria", "asignaciones", "partida",
                            "total"]
    return _node("\n".join([
        _const("COLUMNAS"), _const("MINIMO_COLUMNA"),
        _funcion("anchosAjustados"), _funcion("sincronizarAnchoTabla"),
        "const state = {columnas: " + json.dumps(columnas) + ", anchos: " +
        json.dumps(anchos) + "};",
        "const ths = state.columnas.map(() => ({style: {}}));",
        "const tabla = {style: {}, parentElement: {clientWidth: " +
        str(disponible) + "}};",
        "const $ = (s) => s === '#tabla' ? tabla : null;",
        ("const document = {querySelectorAll: (s) => s === "
         "'#cabecera-tabla tr:first-child th' ? ths : []};"),
        "sincronizarAnchoTabla();",
        ("process.stdout.write(JSON.stringify({ths: ths.map((t) => "
         "t.style.width), tabla: tabla.style, anchos: state.anchos}));")]))


def test_f050_m2_1_la_tabla_se_ajusta_a_su_panel():
    obs = _sincronizar({}, 1046)
    assert obs["ths"] == ["203px", "140px", "299px", "212px", "190px"]
    assert obs["tabla"] == {"tableLayout": "fixed", "minWidth": "100%",
                            "width": "1044px"}


def test_f050_m2_1_las_preferencias_no_se_tocan():
    """Se ajusta lo que se pinta, no lo guardado: con la ventana ancha
    vuelven los anchos del usuario."""
    obs = _sincronizar({"nombre": 400, "partida": 250}, 1046,
                       ["partida", "nombre", "categoria", "asignaciones",
                        "total"])
    assert obs["anchos"] == {"nombre": 400, "partida": 250}
    assert sum(int(w[:-2]) for w in obs["ths"]) <= 1046
    ancha = _sincronizar({"nombre": 400, "partida": 250}, 3000,
                         ["partida", "nombre", "categoria", "asignaciones",
                          "total"])
    assert ancha["ths"] == ["250px", "400px", "210px", "560px", "190px"]


def test_f050_m2_1_se_reajusta_cuando_cambia_el_panel():
    enlazar = _plano(_funcion("enlazarEventos"))
    assert ("new ResizeObserver(() => sincronizarAnchoTabla())"
            '.observe($("#tabla").parentElement);') in enlazar
