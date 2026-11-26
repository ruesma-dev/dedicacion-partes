# tests/test_f081_operaciones.py
"""F-081 · Operaciones matemáticas en las celdas numéricas del cuadrante.

La celda de % de cada línea y la casilla de cantidad (km y €) admiten
operaciones (`30+10`, `=100/3`, `(8+4)*2`): se evalúan al confirmar (salir de
la celda, Enter o Tab), la celda se queda con el resultado redondeado a dos
decimales y a la API solo llega ese número (design §5). El evaluador es
propio, de descenso recursivo, sin `eval` ni `Function` (D6).

Se ejecuta el código REAL de `app.js` en node con el arnés de los tests del
front (`_funcion` y `_node` de `test_f042_sugerencias`, `DOM_CELDA` y
`DOM_LETRAS` de `test_f030_celda_pct`, `_editor` de
`test_f030_tabla_incidencias`). Sin `node` se saltan con su motivo; el
reviewer los exige `passed`. Sin red ni BBDD.
"""
from __future__ import annotations

import json
import re

import pytest

from tests.test_f042_sugerencias import JS, _funcion, _node

#: Las funciones puras del evaluador (design §5).
EVALUADOR = ("esExpresion", "evaluarExpresion", "redondear2", "textoNumero",
             "confirmarExpresion")


def _puro(cuerpo: str) -> object:
    programa = "\n".join([*[_funcion(f) for f in EVALUADOR],
                          "var resultado;", cuerpo,
                          "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


def _evaluar(textos: list[str]) -> list:
    return _puro(f"resultado = {json.dumps(textos)}.map((t) => evaluarExpresion(t));")


#: Casos de R1, R2 y R6: se evalúan todos en UNA sola llamada a node (al
#: cargar el módulo, si hay node) para no lanzar un proceso por caso.
R1 = [
    ("30+10", 40), ("10+2*3", 16), ("(10+2)*3", 36), ("20-5-5", 10),
    ("100/2/5", 10), ("-5+10", 5), ("5*-2", -10), ("12,5 + 0.5", 13),
    ("= 8 + 4", 12), ("((1+2))*-(3)", -9), ("+5", 5), (",5+.5", 1),
    ("  2 * ( 3 + 4 ) ", 14), ("10-+2", 8),
]
R2 = [
    "1.234,5", "1,2,3", "3*/2", "3+", "(3+2", "3+2)", "()", "", "=", "  = ",
    "3 x 2", "50%", "2(3)", "(2)(3)", "3,4 5,6", "*3", "1e3", "abc", "3++",
    "=3=", "--", ".", ",",
]
R6 = [
    ("40", False), ("40,5", False), ("-5", False), ("50%", False), ("", False),
    ("   ", False), (" -5 ", False), ("40.5 %", False),
    ("30+10", True), ("=40", True), ("5-2", True), ("(40)", True),
    (" = 40", True), ("3*2", True), ("9/3", True), ("- 5", False),
    ("-5-2", True), ("+5", True),
]


class _Casos(dict):
    """Los resultados de R1, R2 y R6, calculados en node la primera vez."""

    def __missing__(self, clave):
        textos = {"r1": [t for t, _ in R1], "r2": R2, "r6": [t for t, _ in R6]}
        r = _puro(f"""
          const t = {json.dumps(textos)};
          resultado = {{
            r1: t.r1.map((x) => [x, evaluarExpresion(x)]),
            r2: t.r2.map((x) => [x, evaluarExpresion(x)]),
            r6: t.r6.map((x) => [x, esExpresion(x)]) }};
        """)
        for k, pares in r.items():
            self[k] = dict(pares)
        return self[clave]


_CASOS = _Casos()


# ================================ R1 ===================================== #
@pytest.mark.parametrize("texto, valor", R1)
def test_f081_r1_evalua_con_precedencia_y_asociatividad(texto, valor):
    assert _CASOS["r1"][texto] == {"ok": True, "valor": valor}


def test_f081_r1_tercio_sin_redondear():
    r = _evaluar(["=100/3"])[0]
    assert r["ok"] is True
    assert abs(r["valor"] - 100 / 3) < 1e-12


# ================================ R2 ===================================== #
@pytest.mark.parametrize("texto", R2)
def test_f081_r2_mal_formada_es_no_valida_sin_lanzar(texto):
    assert _CASOS["r2"][texto] == {"ok": False, "motivo": "no válida"}


def test_f081_r2_no_texto_tampoco_lanza():
    r = _puro("resultado = [null, undefined, 42].map((t) => evaluarExpresion(t));")
    assert r[0] == {"ok": False, "motivo": "no válida"}
    assert r[1] == {"ok": False, "motivo": "no válida"}
    # Un número de JS se lee como su texto: «42».
    assert r[2] == {"ok": True, "valor": 42}


# ================================ R3 ===================================== #
def test_f081_r3_division_por_cero():
    r = _evaluar(["5/0", "5/(2-2)", "0/0", "5/0,0", "1+2/(3-3)*4"])
    assert r == [{"ok": False, "motivo": "división por cero"}] * 5


def test_f081_r3_resultado_no_finito_es_no_valida():
    """Con 100 caracteres no se llega a Infinity tecleando (sin `e`): el
    camino se comprueba con el valor más grande que cabe, que sigue finito,
    y con un doble de `Number.isFinite` que dice que no lo es."""
    r = _puro("""
      const t = "9".repeat(50) + "*" + "9".repeat(49);
      const finito = evaluarExpresion(t);
      const real = Number.isFinite;
      Number.isFinite = () => false;
      const noFinito = evaluarExpresion("2*3");
      Number.isFinite = real;
      resultado = [t.length, finito.ok, noFinito];
    """)
    assert r[0] == 100 and r[1] is True
    assert r[2] == {"ok": False, "motivo": "no válida"}


# ================================ R4 ===================================== #
def test_f081_r4_mas_de_100_caracteres_o_21_parentesis():
    r = _puro("""
      const largo = "1+".repeat(50) + "1";              // 101 caracteres
      const justo = "1+".repeat(49) + "11";             // 100 caracteres
      const hondo = "(".repeat(21) + "1" + ")".repeat(21);
      const veinte = "(".repeat(20) + "1" + ")".repeat(20);
      const malHondo = "(".repeat(30) + "1+";           // sin cerrar y hondo
      resultado = [largo.length, evaluarExpresion(largo), justo.length,
                   evaluarExpresion(justo), evaluarExpresion(hondo),
                   evaluarExpresion(veinte), evaluarExpresion(malHondo),
                   evaluarExpresion(" ".repeat(98) + "1+1")];
    """)
    assert r[0] == 101 and r[1] == {"ok": False, "motivo": "demasiado larga"}
    assert r[2] == 100 and r[3] == {"ok": True, "valor": 60}
    assert r[4] == {"ok": False, "motivo": "demasiado larga"}
    assert r[5] == {"ok": True, "valor": 1}
    assert r[6] == {"ok": False, "motivo": "demasiado larga"}
    # R4 cuenta el texto tal cual llega, espacios incluidos (101 aquí).
    assert r[7] == {"ok": False, "motivo": "demasiado larga"}


def test_f081_r4_lo_largo_no_se_recorre_entero():
    """Un texto enorme se corta antes de leerlo: sale en el acto."""
    r = _puro("""
      const enorme = "(".repeat(5000000) + "1";
      const t0 = Date.now();
      let r;
      for (let i = 0; i < 1000; i++) r = evaluarExpresion(enorme);
      resultado = { r, ms: Date.now() - t0 };
    """)
    assert r["r"] == {"ok": False, "motivo": "demasiado larga"}
    assert r["ms"] < 1000


# ================================ R6 ===================================== #
@pytest.mark.parametrize("texto, es", R6)
def test_f081_r6_es_expresion(texto, es):
    assert _CASOS["r6"][texto] is es


def test_f081_r6_no_texto_no_es_expresion():
    assert _puro("resultado = [esExpresion(null), esExpresion(undefined)];") \
        == [False, False]


# ================================ R15 ==================================== #
def test_f081_r15_redondea_a_dos_mitad_arriba_en_decimal():
    r = _puro("""
      const casos = ["0,1+0,2", "100/3", "200/3", "1,005*1", "-2,5/1",
                     "-1,005*1", "2,675*1", "0,000001/1", "-0,0000001*1"];
      resultado = casos.map((t) => redondear2(evaluarExpresion(t).valor));
    """)
    assert r[:5] == [0.3, 33.33, 66.67, 1.01, -2.5]
    assert r[5] == -1.01          # el signo aparte: mitad «hacia fuera»
    assert r[6] == 2.68
    assert r[7] == 0 and r[8] == 0


def test_f081_r15_text_numero_con_coma():
    r = _puro("resultado = [textoNumero(33.33), textoNumero(240), textoNumero(-2.5)];")
    assert r == ["33,33", "240", "-2,5"]


def test_f081_r9_r10_confirmar_expresion_rango_y_mensajes():
    r = _puro("""
      resultado = [
        confirmarExpresion("100/3", "pct"),
        confirmarExpresion("=50+60", "pct"),
        confirmarExpresion("5-5", "pct"),
        confirmarExpresion("50+50", "pct"),
        confirmarExpresion("30+", "pct"),
        confirmarExpresion("5/0", "cantidad"),
        confirmarExpresion("120*2", "cantidad"),
        confirmarExpresion("10-20", "cantidad"),
        confirmarExpresion("100,004+0", "pct"),
        confirmarExpresion("0,001+0", "pct"),
        confirmarExpresion("-0,001*1", "cantidad"),
      ];
    """)
    assert r[0] == {"ok": True, "valor": 33.33}
    assert r[1] == {"ok": False, "mensaje":
                    "La operación da 110: el % tiene que estar entre 0 y 100"}
    assert r[2] == {"ok": False, "mensaje":
                    "La operación da 0: el % tiene que estar entre 0 y 100"}
    assert r[3] == {"ok": True, "valor": 100}
    assert r[4] == {"ok": False, "mensaje": "Operación no válida: «30+» (no válida)"}
    assert r[5] == {"ok": False,
                    "mensaje": "Operación no válida: «5/0» (división por cero)"}
    assert r[6] == {"ok": True, "valor": 240}
    assert r[7] == {"ok": True, "valor": -10}       # la API lo rechaza (R13)
    assert r[8] == {"ok": True, "valor": 100}       # redondeado, dentro
    assert r[9] == {"ok": False, "mensaje":
                    "La operación da 0: el % tiene que estar entre 0 y 100"}
    assert r[10] == {"ok": True, "valor": 0}


def test_f081_r9_el_aviso_de_rango_lleva_coma_decimal():
    r = _puro('resultado = confirmarExpresion("200/3+50", "pct");')
    assert r == {"ok": False, "mensaje":
                 "La operación da 116,67: el % tiene que estar entre 0 y 100"}


# ================================ R5 ===================================== #
def test_f081_r5_app_js_no_evalua_texto_como_codigo():
    """D6: ni `eval(`, ni `new Function`, ni `Function(`, ni `setTimeout` /
    `setInterval` con una cadena en todo `app.js`."""
    prohibidos = [r"\beval\s*\(", r"\bnew\s+Function\b", r"\bFunction\s*\(",
                  r"\bset(Timeout|Interval)\s*\(\s*[\"'`]"]
    encontrados = [p for p in prohibidos if re.search(p, JS)]
    assert encontrados == []
    # El evaluador existe y es propio: descenso recursivo sobre fichas.
    cuerpo = _funcion("evaluarExpresion")
    assert "const factor = () =>" in cuerpo and "const expr = () =>" in cuerpo


# ========================= la celda de % (T4) ============================ #
from tests.test_f030_celda_pct import (  # noqa: E402
    DOM_CELDA,
    DOM_LETRAS,
    FUNCIONES_LETRAS,
)
from tests.test_f042_sugerencias import DOM_DE_PRUEBA  # noqa: E402

#: `toast` que apunta también si es de error (R9, R10: `toast(…, true)`).
DOM_F081 = r"""
function toast(m, error) { llamadas.push("toast:" + m + (error ? "|error" : "")); }
function avisos() { return llamadas.filter((x) => x.startsWith("toast:")); }
"""


def _celda(cuerpo: str) -> object:
    """La celda de % REAL (`chipEditable` y lo que llama, con la rama de
    letras de F-030) más el evaluador."""
    nombres = list(dict.fromkeys([*FUNCIONES_LETRAS, *EVALUADOR, "cuerpoLineas"]))
    funciones = [_funcion(f) for f in nombres]
    variable = "let desmontarSugerencias = null;"
    if variable not in "".join(funciones):
        funciones.insert(0, variable)
    programa = "\n".join([DOM_DE_PRUEBA, DOM_CELDA, DOM_LETRAS, DOM_F081,
                          *funciones, "var resultado;", cuerpo,
                          "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


#: Editor con dos líneas: la otra al 30 % y la de la celda al 50 %.
DOS_LINEAS = """
  const editor = nuevoEditor();
  const otra = linea(2, 30), l = linea(1, 50);
  state.edicion = [otra, l];
  const pct = montar(l, 1, editor);
  const badge = editor.querySelector(".total-vivo");
"""


# ================================ R7 ===================================== #
def test_f081_r7_mientras_hay_expresion_no_cuenta_ni_guarda():
    r = _celda(DOS_LINEAS + """
      const pasos = [];
      for (const v of ["3", "30", "30+", "30+1", "(30+10", "=4"]) {
        teclear(pct, v);
        pasos.push([v, l.porcentaje, pct.classList.contains("expresion")]);
      }
      resultado = { pasos, guardados: guardados(),
                    total: editor.querySelector(".total-vivo").innerHTML,
                    cuerpo: cuerpoLineas(state.edicion) };
    """)
    # «3» y «30» son números llanos: cuentan y guardan, como hoy (R16).
    assert r["pasos"] == [["3", 3, False], ["30", 30, False], ["30+", 30, True],
                          ["30+1", 30, True], ["(30+10", 30, True], ["=4", 30, True]]
    assert r["guardados"] == 2
    assert "60%" in r["total"]
    # R20: el PUT lleva el último número, nunca el texto.
    assert r["cuerpo"][1]["porcentaje"] == 30


def test_f081_r7_solo_expresion_no_toca_el_total():
    r = _celda(DOS_LINEAS + """
      teclear(pct, "30+10");
      resultado = { mismoBadge: editor.querySelector(".total-vivo") === badge,
                    pct: l.porcentaje, guardados: guardados() };
    """)
    assert r == {"mismoBadge": True, "pct": 50, "guardados": 0}


def test_f081_r7_volver_a_un_numero_quita_la_marca_y_cuenta():
    r = _celda(DOS_LINEAS + """
      teclear(pct, "30+");
      const antes = pct.classList.contains("expresion");
      teclear(pct, "40");
      resultado = { antes, despues: pct.classList.contains("expresion"),
                    pct: l.porcentaje, guardados: guardados() };
    """)
    assert r == {"antes": True, "despues": False, "pct": 40, "guardados": 1}


# ================================ R8 ===================================== #
def test_f081_r8_al_salir_pone_el_resultado_cuenta_y_guarda_una_vez():
    r = _celda(DOS_LINEAS + """
      teclear(pct, "100/3");
      pct.blur();
      resultado = { valor: pct.value, pct: l.porcentaje, guardados: guardados(),
                    marca: pct.classList.contains("expresion"), avisos: avisos(),
                    total: editor.querySelector(".total-vivo").innerHTML,
                    cuerpo: cuerpoLineas(state.edicion) };
    """)
    assert r["valor"] == "33,33" and r["pct"] == 33.33
    assert r["guardados"] == 1
    assert r["marca"] is False and r["avisos"] == []
    assert "63,33%" in r["total"]
    assert r["cuerpo"][1] == {"obra_ide": 1, "es_postventa": False,
                              "porcentaje": 33.33}


def test_f081_r8_el_cien_entra_y_un_numero_llano_al_salir_no_se_toca():
    r = _celda(DOS_LINEAS + """
      teclear(pct, "=50+50");
      pct.blur();
      const a = [pct.value, l.porcentaje, guardados()];
      teclear(pct, "45");
      pct.blur();
      resultado = { a, b: [pct.value, l.porcentaje, guardados()], avisos: avisos() };
    """)
    assert r["a"] == ["100", 100, 1]
    assert r["b"] == ["45", 45, 2]       # el blur no añade guardado (R16)
    assert r["avisos"] == []


# ================================ R9 ===================================== #
def test_f081_r9_fuera_de_rango_avisa_repone_y_no_guarda():
    r = _celda(DOS_LINEAS + """
      const casos = [];
      for (const v of ["=50+60", "10-10", "5-20"]) {
        teclear(pct, v);
        pct.blur();
        casos.push([pct.value, l.porcentaje, pct.classList.contains("expresion")]);
      }
      resultado = { casos, avisos: avisos(), guardados: guardados() };
    """)
    assert r["casos"] == [["50", 50, False]] * 3
    assert r["avisos"] == [
        "toast:La operación da 110: el % tiene que estar entre 0 y 100|error",
        "toast:La operación da 0: el % tiene que estar entre 0 y 100|error",
        "toast:La operación da -15: el % tiene que estar entre 0 y 100|error"]
    assert r["guardados"] == 0


def test_f081_r9_linea_sin_pct_vuelve_vacia_y_no_rellena_ni_guarda():
    """La línea estaba a 0: la celda vuelve vacía y el «en blanco rellena»
    de F-030 R1 no actúa tras un aviso (R9, R10: sin guardado)."""
    r = _celda("""
      const editor = nuevoEditor();
      const otra = linea(2, 30), l = linea(1, 0);
      state.edicion = [otra, l];
      const pct = montar(l, 1, editor);
      teclear(pct, "200*2");
      pct.blur();
      resultado = { valor: pct.value, pct: l.porcentaje, guardados: guardados(),
                    avisos: avisos().length };
    """)
    assert r == {"valor": "", "pct": 0, "guardados": 0, "avisos": 1}


# ================================ R10 ==================================== #
def test_f081_r10_no_valida_avisa_repone_y_no_guarda():
    r = _celda(DOS_LINEAS + """
      const casos = [];
      for (const v of ["30+", "5/0", "(3", "1.234,5+1"]) {
        teclear(pct, v);
        pct.blur();
        casos.push(pct.value);
      }
      resultado = { casos, pct: l.porcentaje, avisos: avisos(), guardados: guardados() };
    """)
    assert r["casos"] == ["50"] * 4 and r["pct"] == 50
    assert r["avisos"] == [
        "toast:Operación no válida: «30+» (no válida)|error",
        "toast:Operación no válida: «5/0» (división por cero)|error",
        "toast:Operación no válida: «(3» (no válida)|error",
        "toast:Operación no válida: «1.234,5+1» (no válida)|error"]
    assert r["guardados"] == 0


def test_f081_r10_demasiado_larga():
    r = _celda(DOS_LINEAS + """
      teclear(pct, "1+".repeat(60) + "1");
      pct.blur();
      resultado = { valor: pct.value, aviso: avisos()[0] };
    """)
    assert r["valor"] == "50"
    assert r["aviso"].endswith("(demasiado larga)|error")


# ================================ R11 ==================================== #
def test_f081_r11_enter_confirma_y_va_al_buscador_de_obra():
    r = _celda(DOS_LINEAS + """
      teclear(pct, "100/3");
      const ev = pct.fire("keydown", "Enter");
      const a = { valor: pct.value, pct: l.porcentaje, foco: foco && foco.className,
                  previsto: ev.previsto, guardados: guardados() };
      pct.focus();
      teclear(pct, "30+");
      pct.fire("keydown", "Enter");
      resultado = { a, b: { valor: pct.value, pct: l.porcentaje,
                            foco: foco && foco.className, avisos: avisos() } };
    """)
    assert r["a"] == {"valor": "33,33", "pct": 33.33, "foco": "obra-input",
                      "previsto": True, "guardados": 1}
    assert r["b"] == {"valor": "33,33", "pct": 33.33, "foco": "obra-input",
                      "avisos": ["toast:Operación no válida: «30+» (no válida)|error"]}


# ================================ R17 ==================================== #
def test_f081_r17_con_letras_busca_incidencia_aunque_lleve_operadores():
    r = _celda(DOS_LINEAS + """
      teclear(pct, "30+");
      teclear(pct, "30+v");
      const abierto = panelInc() !== null;
      pct.blur();
      resultado = { abierto, cerrado: panelInc() === null, valor: pct.value,
                    pct: l.porcentaje, avisos: avisos(), guardados: guardados() };
    """)
    assert r["abierto"] is True
    assert r["cerrado"] is True and r["valor"] == "50" and r["pct"] == 50
    assert r["avisos"] == [] and r["guardados"] == 0


def test_f081_r17_con_operadores_y_letras_es_la_busqueda_de_f030():
    """Lo de hoy: el panel busca el texto tal cual (`1+vac` no casa con
    nada), Enter sin coincidencias no hace nada y salir repone la celda; ni
    se evalúa ni se avisa."""
    r = _celda(DOS_LINEAS + """
      teclear(pct, "1+vac");
      const panel = filas();
      pct.fire("keydown", "Enter");
      pct.blur();
      resultado = { panel, inc: state.incidenciasEdicion.length, valor: pct.value,
                    pct: l.porcentaje, avisos: avisos(), guardados: guardados() };
    """)
    assert r == {"panel": ["sugerencia vacia|Ninguna incidencia con «1+vac»"],
                 "inc": 0, "valor": "50", "pct": 50, "avisos": [], "guardados": 0}


# ================================ R21 ==================================== #
def test_f081_r21_la_celda_de_pct_dice_que_admite_operaciones():
    r = _celda(DOS_LINEAS + "resultado = pct.title;")
    assert r == "Admite operaciones: 30+10, 100/3, (8+4)*2"


# ===================== la casilla de cantidad (T6) ======================= #
from tests.test_f030_tabla_incidencias import _editor  # noqa: E402
from tests.test_f069_importes_front import FILA_COPIADA  # noqa: E402

#: La casilla REAL (`chipImporte` y lo que usa) más el evaluador.
CASILLA = ("importesDeFila", "etiquetaObra", "cantidadTecleada", "elementoImporte",
           "firmaImporte", "cuerpoImportes", "chipImporte", *EVALUADOR)

#: El km copiado del mes anterior (cantidad 100) de F-069, con un
#: `programarGuardado` que cuenta y el `toast` que apunta si es de error.
KM = FILA_COPIADA + DOM_F081 + """
  function programarGuardado() { llamadas.push("programarGuardado"); }
  function guardados() { return llamadas.filter((x) => x === "programarGuardado").length; }
  const km = state.importesEdicion[0];
  const chip = chipImporte(km);
  const cant = chip.children.find((x) => x.classList.contains("importe-cantidad"));
  const marca = () => chip.children.some((x) => x.className === "marca-copiado");
  function teclearCant(v) { cant.value = v; return cant.fire("input"); }
"""


# ================================ R12 ==================================== #
def test_f081_r12_mientras_hay_expresion_no_cambia_cantidad_marca_ni_guarda():
    r = _editor(CASILLA, KM + """
      const pasos = [];
      for (const v of ["1", "12", "120*", "120*2", "=5"]) {
        teclearCant(v);
        pasos.push([v, km.cantidad, km.copiado, marca(), cant.classList.contains("expresion")]);
      }
      resultado = { pasos, guardados: guardados(), cuerpo: cuerpoImportes(state.importesEdicion) };
    """)
    assert r["pasos"] == [["1", "1", False, False, False],
                          ["12", "12", False, False, False],
                          ["120*", "12", False, False, True],
                          ["120*2", "12", False, False, True],
                          ["=5", "12", False, False, True]]
    assert r["guardados"] == 2
    # R20: lo que viajaría es el último número, nunca el texto.
    assert r["cuerpo"] == [{"vinculado_ide": 20, "cantidad": 12, "comentario": None}]


def test_f081_r12_la_marca_de_copiado_no_se_va_con_una_expresion():
    r = _editor(CASILLA, KM + """
      teclearCant("50+50");
      resultado = { cantidad: km.cantidad, copiado: km.copiado, marca: marca(),
                    guardados: guardados(), cuerpo: cuerpoImportes(state.importesEdicion) };
    """)
    assert r == {"cantidad": "100", "copiado": True, "marca": True, "guardados": 0,
                 "cuerpo": []}


# ================================ R13 ==================================== #
def test_f081_r13_al_salir_pone_el_resultado_y_sigue_como_tecleado():
    r = _editor(CASILLA, KM + """
      teclearCant("120*2");
      cant.blur();
      resultado = { valor: cant.value, cantidad: km.cantidad, copiado: km.copiado,
                    marca: marca(), clase: cant.classList.contains("expresion"),
                    guardados: guardados(), avisos: avisos(),
                    cuerpo: cuerpoImportes(state.importesEdicion) };
    """)
    assert r["valor"] == "240" and r["cantidad"] == "240"
    assert r["copiado"] is False and r["marca"] is False and r["clase"] is False
    assert r["guardados"] == 1 and r["avisos"] == []
    assert r["cuerpo"] == [{"vinculado_ide": 20, "cantidad": 240, "comentario": None}]


def test_f081_r13_enter_confirma_sin_mover_el_foco_y_la_misma_cantidad_deja_la_marca():
    r = _editor(CASILLA, KM + """
      cant.focus();
      teclearCant("50+50");
      const ev = cant.fire("keydown", "Enter");
      const a = { valor: cant.value, cantidad: km.cantidad, copiado: km.copiado,
                  marca: marca(), previsto: ev.previsto, foco: foco === cant,
                  guardados: guardados() };
      cant.blur();                        // ya es un número: nada más
      resultado = { a, guardados: guardados(), cuerpo: cuerpoImportes(state.importesEdicion) };
    """)
    # D18: la misma cantidad que la guardada no quita la marca.
    assert r["a"] == {"valor": "100", "cantidad": "100", "copiado": True,
                      "marca": True, "previsto": True, "foco": True, "guardados": 1}
    assert r["guardados"] == 1
    assert r["cuerpo"] == []


def test_f081_r13_redondeo_y_negativo_van_como_tecleados():
    """El front no repite los topes de la API: un negativo va tal cual y la
    API lo rechaza (422, el aviso de siempre)."""
    r = _editor(CASILLA, KM + """
      const casos = [];
      for (const v of ["100/3", "10-20", "0,1+0,2"]) {
        teclearCant(v);
        cant.fire("keydown", "Enter");
        casos.push([cant.value, km.cantidad, elementoImporte(km).cantidad]);
      }
      resultado = { casos, avisos: avisos(), guardados: guardados() };
    """)
    assert r["casos"] == [["33,33", "33,33", 33.33], ["-10", "-10", -10],
                          ["0,3", "0,3", 0.3]]
    assert r["avisos"] == [] and r["guardados"] == 3


# ================================ R14 ==================================== #
def test_f081_r14_no_valida_avisa_repone_lo_ultimo_valido_y_no_guarda():
    r = _editor(CASILLA, KM + """
      teclearCant("150");
      const casos = [];
      for (const v of ["150+", "5/0", "(2"]) {
        teclearCant(v);
        cant.blur();
        casos.push([cant.value, km.cantidad, cant.classList.contains("expresion")]);
      }
      teclearCant("3*/2");
      cant.fire("keydown", "Enter");
      casos.push([cant.value, km.cantidad]);
      resultado = { casos, avisos: avisos(), guardados: guardados() };
    """)
    assert r["casos"] == [["150", "150", False]] * 3 + [["150", "150"]]
    assert r["avisos"] == [
        "toast:Operación no válida: «150+» (no válida)|error",
        "toast:Operación no válida: «5/0» (división por cero)|error",
        "toast:Operación no válida: «(2» (no válida)|error",
        "toast:Operación no válida: «3*/2» (no válida)|error"]
    assert r["guardados"] == 1               # solo el «150» tecleado


# ================================ R21 ==================================== #
def test_f081_r21_la_casilla_de_cantidad_dice_que_admite_operaciones():
    r = _editor(CASILLA, KM + "resultado = cant.title;")
    assert r == "Admite operaciones: 30+10, 100/3, (8+4)*2"
