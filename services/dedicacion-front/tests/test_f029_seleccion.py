# tests/test_f029_seleccion.py
"""F-029 · Selección múltiple con Ctrl/Shift y «Completar al 100 %» en el
front (R1-R13).

Comprobación ESTÁTICA de `static/js/app.js`, `templates/index.html` y
`static/css/styles.css` (patrón de `test_f025_catalogo_postventa.py`): el
front solo selecciona, pregunta y pinta; lo que falta hasta el 100 % lo
calcula la API. El comportamiento en el navegador lo verifica el humano
(T9). Sin red ni navegador.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JS = (RAIZ / "static" / "js" / "app.js").read_text(encoding="utf-8")
HTML = (RAIZ / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (RAIZ / "static" / "css" / "styles.css").read_text(encoding="utf-8")


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


#: Escrituras en la selección múltiple: asignarla o mutarla.
ESCRITURA_SELECCION = re.compile(
    r"state\.seleccion\s*=[^=]|state\.seleccion\.(add|delete|clear)\(")


# ================================ T4 ==================================== #
# --------------------------------- R1 ---------------------------------- #
def test_f029_r1_ctrl_o_shift_clic_marca_sin_abrir_el_editor():
    """Con Ctrl, Cmd o Shift el clic va a `marcarSeleccion` y vuelve antes
    de llegar al editor."""
    fila = _plano(_funcion("construirFila"))
    clic = fila.split('tr.addEventListener("click", (ev) => {')[1].strip()
    assert clic.startswith("if (ev.ctrlKey || ev.metaKey || ev.shiftKey) { "
                           "marcarSeleccion(t.ide, ev.shiftKey); return; }"), clic
    assert clic.index("return;") < clic.index("abrirEditor(t.ide)")


def test_f029_r1_ctrl_clic_alterna_y_el_cursor_entra_si_estaba_vacia():
    marcar = _plano(_funcion("marcarSeleccion"))
    # «estaba» se mira ANTES de que entre el cursor.
    assert marcar.index("const estaba = state.seleccion.has(ide);") < \
        marcar.index("state.seleccion.add(state.seleccionIde)")
    assert ("if (state.seleccion.size === 0 && state.seleccionIde !== null) "
            "state.seleccion.add(state.seleccionIde);") in marcar
    assert ("if (estaba) state.seleccion.delete(ide); "
            "else state.seleccion.add(ide);") in marcar
    alterna = marcar.split("const estaba")[1]
    assert "state.seleccionIde = ide;" in alterna
    assert "state.ancla = ide;" in alterna


# --------------------------------- R2 ---------------------------------- #
def test_f029_r2_shift_clic_rango_de_visibles_entre_ancla_y_fila():
    marcar = _plano(_funcion("marcarSeleccion"))
    rango = marcar.split("if (rango")[1].split("const estaba")[0]
    assert "trabajadoresVisibles().map((t) => t.ide)" in rango
    assert "visibles.slice(desde, hasta + 1)" in rango
    assert "const [desde, hasta] = a <= b ? [a, b] : [b, a];" in rango
    # El ancla no se mueve con Shift: así se puede rehacer el rango.
    assert "state.ancla =" not in rango


def test_f029_r2_shift_clic_no_selecciona_texto():
    fila = _plano(_funcion("construirFila"))
    assert ('tr.addEventListener("mousedown", (ev) => { '
            "if (ev.shiftKey) ev.preventDefault(); });") in fila


# --------------------------------- R3 ---------------------------------- #
def test_f029_r3_clase_propia_y_contador():
    fila = _plano(_funcion("construirFila"))
    assert 'if (state.seleccion.has(t.ide)) tr.classList.add("multi");' in fila
    # La del cursor no cambia.
    assert ('if (t.ide === state.seleccionIde) '
            'tr.classList.add("seleccionada");') in fila
    tabla = _plano(_funcion("renderTabla"))
    assert "seleccionados" in tabla and "state.seleccion.size" in tabla
    assert re.search(r"tr\.fila\.multi td\s*\{", CSS)


# --------------------------------- R4 ---------------------------------- #
def test_f029_r4_clic_simple_vacia_y_hace_lo_de_hoy():
    fila = _plano(_funcion("construirFila"))
    clic = fila.split('tr.addEventListener("click", (ev) => {')[1].strip()
    sin_mod = clic.split("return; }", 1)[1].strip()
    assert sin_mod.startswith(
        "state.seleccionIde = t.ide; state.ancla = t.ide; fijarSeleccion([]); "
        'if (state.periodoEstado === "ABIERTO") abrirEditor(t.ide); '
        "else renderTabla(); });"), sin_mod


# --------------------------------- R5 ---------------------------------- #
#: `teclas` de antes de F-029, hasta el final de su última rama. Debe seguir
#: idéntica: lo nuevo (C y Esc) va DETRÁS, en la rama de «editor cerrado y
#: fuera de campo».
TECLAS_ANTES = (
    'function teclas(ev) { const abierto = state.periodoEstado === "ABIERTO"; '
    "const objetivo = state.editandoIde !== null ? state.editandoIde : "
    "state.seleccionIde; // F7 / F8 funcionan siempre (también dentro de "
    'inputs del editor). if (ev.key === "F7" && abierto && objetivo !== null) '
    "{ ev.preventDefault(); copiarDeArriba(objetivo); return; } if (ev.key === "
    '"F8" && abierto && objetivo !== null) { ev.preventDefault(); '
    'copiarTrabajador(objetivo); return; } const enInput = ["INPUT", '
    '"TEXTAREA", "SELECT"].includes( document.activeElement.tagName ); if '
    '(state.editandoIde !== null) { if (ev.key === "Escape" && !enInput) '
    'cerrarEditor(); if (ev.key === "z" && (ev.ctrlKey || ev.metaKey)) { '
    "ev.preventDefault(); deshacer(state.editandoIde); } return; } if "
    '(enInput) return; if (ev.key === "/") { ev.preventDefault(); '
    '$("#buscador").focus(); } else if (ev.key === "ArrowDown") { '
    "ev.preventDefault(); moverSeleccion(1); } else if (ev.key === "
    '"ArrowUp") { ev.preventDefault(); moverSeleccion(-1); } else if '
    '(ev.key === "Enter" && state.seleccionIde !== null) { if (abierto) '
    'abrirEditor(state.seleccionIde); } else if ((ev.key === "r" || ev.key '
    '=== "R") && state.seleccionIde !== null) { if (abierto) '
    'copiarTrabajador(state.seleccionIde); } else if (ev.key === "z" && '
    "(ev.ctrlKey || ev.metaKey)) { if (state.seleccionIde !== null && "
    "abierto) { ev.preventDefault(); deshacer(state.seleccionIde); } }"
)


def test_f029_r5_las_ramas_de_teclas_de_antes_siguen_literalmente():
    teclas = _plano(_funcion("teclas"))
    assert teclas.startswith(TECLAS_ANTES), teclas


def test_f029_r5_esc_con_el_editor_cerrado_vacia_la_seleccion():
    nuevo = _plano(_funcion("teclas"))[len(TECLAS_ANTES):]
    assert ('else if (ev.key === "Escape" && state.seleccion.size) { '
            "fijarSeleccion([]); }") in nuevo


def test_f029_r5_la_seleccion_no_mueve_el_cursor_de_las_teclas():
    """↑ ↓, Enter, R, F7, F8 y Ctrl+Z siguen sobre `state.seleccionIde`:
    `moverSeleccion` no mira la selección múltiple."""
    assert "state.seleccion." not in _funcion("moverSeleccion")
    assert "state.seleccion." not in _funcion("abrirEditor")


# --------------------------------- R6 ---------------------------------- #
def test_f029_r6_cambiar_mes_o_empresa_vacia_la_seleccion():
    for nombre in ("cambiarEmpresa", "moverMes"):
        cuerpo = _funcion(nombre)
        assert "fijarSeleccion([]);" in cuerpo, nombre
        assert cuerpo.index("fijarSeleccion([]);") < \
            cuerpo.index("cargarPeriodo("), nombre


# --------------------------------- R7 ---------------------------------- #
def test_f029_r7_solo_dos_funciones_escriben_en_la_seleccion():
    total = len(ESCRITURA_SELECCION.findall(JS))
    propias = sum(len(ESCRITURA_SELECCION.findall(_funcion(n)))
                  for n in ("marcarSeleccion", "fijarSeleccion"))
    assert total == propias and total > 0
    assert "seleccion: new Set()," in _plano(JS)


def test_f029_r7_fijar_seleccion_es_la_puerta_de_f021():
    fijar = _plano(_funcion("fijarSeleccion"))
    assert fijar.startswith("function fijarSeleccion(ides) {")
    assert "state.seleccion = new Set(ides);" in fijar
    assert "renderTabla();" in fijar
    # Independiente de los filtros: no mira los visibles.
    assert "trabajadoresVisibles" not in fijar
