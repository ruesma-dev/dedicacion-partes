# tests/test_f078_paquete_front.py
"""F-078 · El botón «Registrar en Sigrid» registra un paquete.

`#btn-registro` deja de pedir el mes entero: con 2 o más seleccionados
visibles registra esos; con 0 o 1 (el cursor cuenta como 1), todos los
visibles con los filtros. Nunca un oculto. El front solo elige a quién: manda
los `ide` (`trabajador_ides`) y la api decide qué líneas van.

Dos familias, en node con el código REAL de `app.js` (sin `node` se saltan;
el reviewer los exige `passed`):

- Puras (T4): `alcanceRegistro`, `rotuloRegistro`, `tituloRegistro` y
  `cabeceraPaquete`, con tabla de casos.
- Con DOM de mentira (T5): `pintarBotonRegistro`, `registrarPaquete`,
  `registroPreflight`, `pedirPreflight`, `registroEjecutar`,
  `esperarRegistroCortado` y `pintarModalPreflight`, con dobles de `fetch`,
  `$` (con `dataset`), `toast`, `guardarAhora` y `cerrarModal`.

Sin red ni BBDD. Los `ide` y los nombres son inventados.
"""
from __future__ import annotations

import itertools
import json
import re

import pytest

from tests.test_f042_sugerencias import JS, _funcion, _node

#: `escapeHtml` sin DOM (el de `app.js` usa `document`).
ESCAPE = ("function escapeHtml(t) { return (t == null ? '' : String(t))"
          ".replace(/&/g,'&amp;').replace(/</g,'&lt;')"
          ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }")

PURAS = ("alcanceRegistro", "rotuloRegistro", "tituloRegistro",
         "cabeceraPaquete", "nTrabajadores")


def _puras(expresion: str) -> object:
    """Evalúa `expresion` con las funciones puras de F-078 cargadas."""
    return _node("\n".join([
        ESCAPE, *(_funcion(f) for f in PURAS),
        "const T = (ide, nombre) => ({ ide, nombre: nombre || `T${ide}` });",
        f"process.stdout.write(JSON.stringify({expresion}));"]))


def _alcance(visibles: list[int], seleccion: list[int]) -> dict:
    return _puras(
        f"alcanceRegistro({json.dumps(visibles)}.map((i) => T(i)), "
        f"new Set({json.dumps(seleccion)}))")


# ============================ R13: el alcance =========================== #
@pytest.mark.parametrize(("seleccion", "esperado"), [
    # 0 o 1 seleccionados (el cursor cuenta como 1): todos los visibles.
    ([], {"origen": "visibles", "ides": [3, 1, 2], "ocultos": 0,
          "bloqueado": False}),
    ([1], {"origen": "visibles", "ides": [3, 1, 2], "ocultos": 0,
           "bloqueado": False}),
    # Uno solo, oculto: también los visibles (no hay 2 seleccionados).
    ([9], {"origen": "visibles", "ides": [3, 1, 2], "ocultos": 0,
           "bloqueado": False}),
    # 2 o más visibles: esos, en el orden de la tabla.
    ([2, 3], {"origen": "seleccionados", "ides": [3, 2], "ocultos": 0,
              "bloqueado": False}),
    ([2, 1, 3], {"origen": "seleccionados", "ides": [3, 1, 2], "ocultos": 0,
                 "bloqueado": False}),
    # Con ocultos: los visibles de la selección; los otros, contados.
    ([2, 9, 3, 8], {"origen": "seleccionados", "ides": [3, 2], "ocultos": 2,
                    "bloqueado": False}),
])
def test_f078_r13_alcance(seleccion, esperado):
    assert _alcance([3, 1, 2], seleccion) == esperado


@pytest.mark.parametrize("seleccion", [[1, 9], [9, 8], [8, 9, 7], [2, 8, 9]])
def test_f078_r14_varios_seleccionados_menos_de_dos_visibles_bloquea(
        seleccion):
    a = _alcance([3, 1, 2], seleccion)
    assert a["bloqueado"] is True and a["ides"] == []
    assert a["origen"] == "seleccionados"
    assert a["ocultos"] == len([s for s in seleccion if s not in (1, 2, 3)])


def test_f078_r13_sin_filtros_ni_seleccion_todos_los_de_la_tabla():
    assert _alcance(list(range(1, 41)), [])["ides"] == list(range(1, 41))


def test_f078_r13_r15_sin_visibles_la_lista_vacia():
    assert _alcance([], []) == {"origen": "visibles", "ides": [],
                                "ocultos": 0, "bloqueado": False}
    assert _alcance([], [4, 5])["bloqueado"] is True


def test_f078_r13_nunca_un_oculto():
    """Todas las selecciones de 0 a 4 sobre 3 visibles y 2 ocultos: ningún
    `ide` fuera de los visibles, y nunca uno sin seleccionar si van los
    seleccionados."""
    visibles, universo = [5, 2, 7], [5, 2, 7, 90, 91]
    casos = [list(c) for n in range(0, 5)
             for c in itertools.combinations(universo, n)]
    resultados = _puras(
        f"{json.dumps(casos)}.map((s) => alcanceRegistro("
        f"{json.dumps(visibles)}.map((i) => T(i)), new Set(s)))")
    for sel, a in zip(casos, resultados):
        assert set(a["ides"]) <= set(visibles), (sel, a)
        if a["origen"] == "seleccionados":
            assert set(a["ides"]) <= set(sel), (sel, a)
        # El orden, siempre el de la tabla.
        assert a["ides"] == [i for i in visibles if i in a["ides"]], (sel, a)


# ====================== R12, R14: rótulo y `title` ===================== #
@pytest.mark.parametrize(("seleccion", "rotulo"), [
    ([], "Registrar visibles (3)"),
    ([1], "Registrar visibles (3)"),
    ([1, 2], "Registrar seleccionados (2)"),
    ([1, 2, 3, 9], "Registrar seleccionados (3)"),
    ([1, 9], "Registrar seleccionados (0)"),
])
def test_f078_r12_rotulo(seleccion, rotulo):
    assert _puras(
        "rotuloRegistro(alcanceRegistro([3, 1, 2].map((i) => T(i)), "
        f"new Set({json.dumps(seleccion)})))") == rotulo


def test_f078_r12_rotulo_sin_visibles():
    assert _puras("rotuloRegistro(alcanceRegistro([], new Set()))") == \
        "Registrar visibles (0)"


def test_f078_r14_title_dice_que_la_seleccion_esta_oculta():
    titulo = _puras(
        "tituloRegistro(alcanceRegistro([3, 1, 2].map((i) => T(i)), "
        "new Set([1, 9, 8])))")
    assert "la selección está oculta por el filtro" in titulo


@pytest.mark.parametrize(("visibles", "seleccion", "trozos"), [
    ([3, 1, 2], [], ["3 trabajadores visibles"]),
    ([3, 1, 2], [1, 2], ["2 trabajadores seleccionados"]),
    ([3, 1, 2], [1, 2, 9], ["2 trabajadores seleccionados",
                            "1 seleccionado oculto por el filtro no se registra"]),
    ([3], [], ["1 trabajador visible"]),
    ([], [], ["No hay trabajadores visibles"]),
])
def test_f078_r12_title_dice_a_quien(visibles, seleccion, trozos):
    titulo = _puras(
        f"tituloRegistro(alcanceRegistro({json.dumps(visibles)}"
        f".map((i) => T(i)), new Set({json.dumps(seleccion)})))")
    for trozo in trozos:
        assert trozo in titulo, titulo
    assert "oculta por el filtro" not in titulo


# ===================== R20: la cabecera del modal ====================== #
def _cabecera(alcance: dict, nombres: list[str]) -> dict:
    return _puras(f"cabeceraPaquete({json.dumps(alcance)}, "
                  f"{json.dumps(nombres)})")


def test_f078_r20_cabecera_seleccionados_con_nombres_escapados():
    c = _cabecera({"origen": "seleccionados", "ides": [1, 2], "ocultos": 0,
                   "bloqueado": False}, ["Ana <b>López</b>", 'Luis "&"'])
    assert c["titulo"] == " · 2 trabajadores (seleccionados)"
    assert "<details" in c["detalle"] and "<summary>" in c["detalle"]
    assert "<li>Ana &lt;b&gt;López&lt;/b&gt;</li>" in c["detalle"]
    assert "<li>Luis &quot;&amp;&quot;</li>" in c["detalle"]
    assert "<b>" not in c["detalle"]
    assert "ocultos" not in c["detalle"] and "oculto" not in c["detalle"]


@pytest.mark.parametrize(("ocultos", "linea"), [
    (1, "1 seleccionado oculto por el filtro no se registra"),
    (3, "3 seleccionados ocultos por el filtro no se registran"),
])
def test_f078_r20_cabecera_con_ocultos(ocultos, linea):
    c = _cabecera({"origen": "seleccionados", "ides": [1, 2],
                   "ocultos": ocultos, "bloqueado": False}, ["A", "B"])
    assert linea in c["detalle"]


def test_f078_r20_cabecera_visibles():
    c = _cabecera({"origen": "visibles", "ides": [4, 5, 6], "ocultos": 0,
                   "bloqueado": False}, ["A", "B", "C"])
    assert c["titulo"] == " · 3 trabajadores (visibles)"
    assert c["detalle"].count("<li>") == 3


def test_f078_r20_cabecera_de_uno_en_singular():
    c = _cabecera({"origen": "visibles", "ides": [4], "ocultos": 0,
                   "bloqueado": False}, ["A"])
    assert c["titulo"] == " · 1 trabajador (visibles)"


def test_f078_puras_no_tocan_el_dom_ni_el_estado():
    for f in ("alcanceRegistro", "rotuloRegistro", "tituloRegistro",
              "cabeceraPaquete"):
        cuerpo = re.sub(r"//[^\n]*", "", _funcion(f))
        for prohibido in ("document.", "$(", "state.", "registro."):
            assert prohibido not in cuerpo, (f, prohibido)


def test_f078_js_existe():
    assert "function alcanceRegistro(" in JS
