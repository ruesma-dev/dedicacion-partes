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

import pytest

from tests.test_f042_sugerencias import _funcion, _node

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
