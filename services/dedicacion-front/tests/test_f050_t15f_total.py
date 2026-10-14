# tests/test_f050_t15f_total.py
"""F-050 · T15f, punto 2 (M2 del humano, 2026-10-14).

La columna Total se cortaba: en la fila del cursor de VINDEL DURO (50 %,
«falta 50 %») no se veían enteros «✗ 50 %», «falta 50 %», «⇪ Sigrid» y
«↩». `sincronizarAnchoTabla` (T15c, `table-layout: fixed`) la dejaba en su
ancho guardado o de fábrica (190 px) aunque su contenido midiera más.

Ahora Total nunca baja del ancho que mide su contenido más ancho (medido en
el DOM con un `Range` sobre cada `td.celda-total`, más su relleno); en todo
estrechamiento encogen primero Asignaciones y Partida, y Trabajador y
Categoría solo cuando ellas llegan a su mínimo (humano, 2026-10-14, opción
A); si ni así cabe, scroll horizontal del panel. `state.anchos` (lo
guardado) no cambia.

El código REAL de `sincronizarAnchoTabla` y `anchosAjustados` en `node` con
un DOM de mentira cuyas celdas de Total dicen cuánto mide su contenido. Sin
`node` se saltan con su motivo; el reviewer los exige `passed`. Sin red.
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


def _const(nombre: str) -> str:
    m = re.search(rf"^const {nombre} = .*?;$", JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe `const {nombre}` en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=False)
    assert salida.returncode == 0, next(
        (ln for ln in salida.stderr.splitlines() if "Error" in ln), salida.stderr)
    return json.loads(salida.stdout)


ORDEN = ["nombre", "categoria", "asignaciones", "partida", "total"]


def _sincronizar(anchos: dict, disponible: int, contenidos: list,
                 columnas: list | None = None) -> dict:
    """`contenidos`: lo que mide (px) el contenido de cada celda de Total;
    el relleno de la celda, 14 + 14 px como en `.table tbody td`."""
    columnas = columnas or ORDEN
    return _node("\n".join([
        _const("COLUMNAS"), _const("MINIMO_COLUMNA"),
        _funcion("anchosAjustados"), _funcion("sincronizarAnchoTabla"),
        "const state = {columnas: " + json.dumps(columnas) + ", anchos: " +
        json.dumps(anchos) + "};",
        "const ths = state.columnas.map(() => ({style: {}}));",
        "const celdas = " + json.dumps(contenidos) +
        ".map((w) => ({contenido: w}));",
        "const tabla = {style: {}, parentElement: {clientWidth: " +
        str(disponible) + "}};",
        "const $ = (s) => s === '#tabla' ? tabla : null;",
        "let estilos = 0;",
        ("function getComputedStyle(td) { estilos += 1; "
         "return {paddingLeft: '14px', paddingRight: '14px'}; }"),
        ("const document = {querySelectorAll: (s) => s === "
         "'#cabecera-tabla tr:first-child th' ? ths : "
         "(s === '#cuerpo td.celda-total' ? celdas : []), "
         "createRange: () => ({td: null, selectNodeContents(td) { this.td = td; }, "
         "getBoundingClientRect() { return {width: this.td.contenido}; }})};"),
        "sincronizarAnchoTabla();",
        ("process.stdout.write(JSON.stringify({ths: ths.map((t) => "
         "parseInt(t.style.width, 10)), tabla: tabla.style.width, "
         "anchos: state.anchos, estilos}));")]))


def test_f050_t15f_2_encogen_primero_asignaciones_y_partida():
    """1046 px (la captura de T15c): solo Asignaciones y Partida ceden."""
    obs = _sincronizar({}, 1046, [])
    assert obs["ths"] == [280, 210, 196, 169, 190]


def test_f050_t15f_2_trabajador_y_categoria_solo_con_ellas_en_su_minimo():
    obs = _sincronizar({}, 800, [])
    assert obs["ths"] == [186, 123, 150, 150, 190]
    assert sum(obs["ths"]) <= 800


def test_f050_t15f_2_la_prioridad_va_por_columna_no_por_posicion():
    obs = _sincronizar({}, 1046, [],
                       ["partida", "nombre", "categoria", "asignaciones",
                        "total"])
    assert obs["ths"] == [169, 280, 210, 196, 190]


def test_f050_t15f_2_total_mide_su_contenido_mas_ancho():
    """La fila del cursor de VINDEL DURO: «✗ 50 %», «falta 50 %», «⇪ Sigrid»
    y «↩» miden 232,4 px; con el relleno, 263 px. Lo que falta sale de
    Asignaciones y Partida."""
    obs = _sincronizar({}, 1600, [120, 232.4, 150])
    assert obs["ths"] == [280, 210, 536, 310, 263]
    assert sum(obs["ths"]) <= 1600
    assert obs["estilos"] == 1          # el relleno se lee una vez


def test_f050_t15f_2_si_no_cabe_scroll_sin_cortar_total():
    obs = _sincronizar({}, 500, [232.4])
    assert obs["ths"] == [160, 100, 150, 150, 263]
    assert obs["tabla"] == "823px"      # más que el panel: scroll horizontal


def test_f050_t15f_2_lo_guardado_no_cambia_y_manda_si_cabe_el_contenido():
    estrecha = _sincronizar({"total": 150}, 3000, [232.4])
    assert (estrecha["ths"][4], estrecha["anchos"]) == (263, {"total": 150})
    corta = _sincronizar({"total": 150}, 3000, [100])
    assert corta["ths"][4] == 150
    ancha = _sincronizar({"total": 300}, 3000, [232.4])
    assert ancha["ths"][4] == 300


def test_f050_t15f_2_cada_repintado_de_la_tabla_vuelve_a_medir():
    """↑ ↓ mueven el cursor y la tabla se repinta: Total se vuelve a medir."""
    # Sin comentarios (el patrón arrastra también el de la función siguiente):
    # lo último que hace, tras pintar todas las filas, es volver a medir.
    cuerpo = re.sub(r"//[^\n]*", "", _funcion("renderTabla"))
    assert _plano(cuerpo).endswith("}); sincronizarAnchoTabla(); }")


def test_f050_t15f_2_refrescar_la_fila_del_editor_vuelve_a_medir():
    """Al guardar en el editor solo se rehace esa fila (sale «↩», cambia
    «falta X %»): también se vuelve a medir Total."""
    cuerpo = re.sub(r"//[^\n]*", "", _funcion("refrescarCeldasFila"))
    assert _plano(cuerpo).endswith(
        "viejas.forEach((tr) => tr.remove()); sincronizarAnchoTabla(); }")
