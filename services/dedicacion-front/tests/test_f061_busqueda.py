# tests/test_f061_busqueda.py
"""F-061 · Búsqueda predictiva en el desplegable de incidencias (criterios 2,
3 y 5).

Cada palabra tecleada es el comienzo de alguna palabra de la letra, el
código, el nombre de Sigrid o las palabras extra, en cualquier orden y sin
tildes ni mayúsculas. Orden: letra exacta, código o letra que empieza, nombre
que empieza, palabra del nombre, palabra extra, subcadena (lo de F-030) y,
al final, una errata (OSA) por palabra tecleada de 4 o más letras. Empate:
`orden_busqueda` (de config.yaml), las nulas detrás en el orden del catálogo.

Se ejecuta el código REAL de `chipEditable` y `montarDesplegableIncidencias`
en node con el arnés de `test_f030_celda_pct.py`. Sin `node` se saltan con su
motivo; el reviewer los exige `passed`. Sin red ni BBDD.
"""
from __future__ import annotations

import json

from tests.test_f030_celda_pct import _celda_letras

#: El catálogo real de Sigrid (progress/spec_F-030.md) tal como lo sirve
#: `GET /incidencias`: por letra, con las palabras extra y el orden de
#: config.yaml aprobados (B, AT, M, FJ, F, V, H).
CATALOGO = [
    {"codigo": "CIA", "letra": "AT", "nombre": "Accidente/Enf. Profesional",
     "palabras": ["baja", "accidente de trabajo"], "orden_busqueda": 1},
    {"codigo": "CIE", "letra": "B", "nombre": "Enfermedad/Acc. no laboral",
     "palabras": ["baja", "IT", "enfermedad común"], "orden_busqueda": 0},
    {"codigo": "CIF", "letra": "F", "nombre": "Falta injustificada",
     "palabras": ["ausencia"], "orden_busqueda": 4},
    {"codigo": "CIP", "letra": "FJ", "nombre": "Falta Justificada/Permiso",
     "palabras": ["permiso", "ausencia"], "orden_busqueda": 3},
    {"codigo": "CIH", "letra": "H", "nombre": "Huelga",
     "palabras": [], "orden_busqueda": 6},
    {"codigo": "CIM", "letra": "M", "nombre": "Maternidad/Paternidad",
     "palabras": ["baja", "nacimiento", "permiso"], "orden_busqueda": 2},
    {"codigo": "CIV", "letra": "V", "nombre": "Vacaciones",
     "palabras": [], "orden_busqueda": 5},
]


def _buscar(textos: list[str], catalogo: list[dict] | None = None) -> dict:
    """Letras del desplegable, en su orden, para cada texto tecleado ([] si
    sale «Ninguna incidencia»)."""
    return _celda_letras(f"""
      state.tiposIncidencia = {json.dumps(catalogo or CATALOGO)};
      const editor = nuevoEditor();
      const l = linea(1, 0);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      resultado = {{}};
      for (const texto of {json.dumps(textos)}) {{
        teclear(pct, texto);
        resultado[texto] = panelInc().children
          .filter((c) => !c.classList.contains("vacia"))
          .map((c) => /class="cod">([^<]*)</.exec(c.innerHTML)[1]);
      }}
    """)


# ======================= criterio 2: los casos aprobados ================== #
def test_f061_r2_los_casos_de_los_criterios_con_el_catalogo_real():
    r = _buscar(["baj", "enf", "enf pro", "acc lab", "vac", "civ", "ci", "b",
                 "vacasiones", "enfremedad"])
    assert r["baj"] == ["B", "AT", "M"]             # B primero (config.yaml)
    assert r["enf"] == ["B", "AT"]
    assert r["enf pro"] == ["AT"]
    assert r["acc lab"] == ["B"]
    assert r["vac"] == ["V"]
    assert r["civ"] == ["V"]
    assert r["ci"] == ["B", "AT", "M", "FJ", "F", "V", "H"]
    assert r["b"][0] == "B"
    assert r["vacasiones"] == ["V"]
    assert r["enfremedad"] == ["B"]                 # dos letras cambiadas = 1 (OSA)


def test_f061_r2_cualquier_orden_tildes_y_mayusculas():
    r = _buscar(["pro enf", "ENF PRÓ", "VACACIÓNES", "Común", "lab  ACC",
                 "Enf.", "accidente trabajo"])
    assert r["pro enf"] == ["AT"]
    assert r["ENF PRÓ"] == ["AT"]
    assert r["VACACIÓNES"] == ["V"]
    assert r["Común"] == ["B"]
    assert r["lab  ACC"] == ["B"]
    assert r["Enf."] == ["B", "AT"]
    assert r["accidente trabajo"] == ["AT"]


def test_f061_r2_errata_solo_en_palabras_de_4_o_mas_y_solo_una():
    r = _buscar(["bja", "vca", "vacasionez", "vacasi", "huelag", "permisos",
                 "matrenidad", "vaxaxiones", "ausensia"])
    assert r["bja"] == []                           # 3 letras: sin errata
    assert r["vca"] == []
    assert r["vacasionez"] == []                    # dos erratas
    assert r["vacasi"] == ["V"]                     # predictiva con errata
    assert r["huelag"] == ["H"]                     # intercambio contiguo
    assert r["permisos"] == ["M", "FJ"]             # letra de más
    assert r["matrenidad"] == ["M"]
    assert r["vaxaxiones"] == []
    assert r["ausensia"] == ["FJ", "F"]


def test_f061_r2_errata_por_letra_que_falta():
    """Review 1: la palabra tecleada con una letra de menos casa con el
    comienzo de una letra MÁS largo que ella (`n` hasta `w.length + 1`)."""
    r = _buscar(["enfermdad", "vcaciones"])
    assert r["enfermdad"] == ["B"]
    assert r["vcaciones"] == ["V"]


def test_f061_r2_la_subcadena_va_antes_que_la_errata():
    """Review 1: «llevaca» contiene «vaca» (categoría 5) y «baca» está a una
    errata (6); el orden de config.yaml diría lo contrario."""
    catalogo = [
        {"codigo": "CI6", "letra": "R", "nombre": "Baca", "orden_busqueda": 0},
        {"codigo": "CI5", "letra": "S", "nombre": "Llevaca", "orden_busqueda": 1},
    ]
    assert _buscar(["vaca"], catalogo)["vaca"] == ["S", "R"]


# ============================ el orden, uno a uno ========================= #
#: Un catálogo de prueba en el que cada fila casa con «va» por un motivo
#: distinto, puesto al revés del orden esperado y con `orden_busqueda` que
#: diría lo contrario: la categoría manda sobre el desempate.
ESCALERA = [
    {"codigo": "CI6", "letra": "R", "nombre": "Baca", "palabras": [],
     "orden_busqueda": 0},                           # errata (con «vaca»)
    {"codigo": "CI5", "letra": "S", "nombre": "Nava", "palabras": [],
     "orden_busqueda": 1},                           # subcadena
    {"codigo": "CI4", "letra": "T", "nombre": "Otra", "palabras": ["vale"],
     "orden_busqueda": 2},                           # palabra extra
    {"codigo": "CI3", "letra": "U", "nombre": "Otra vaca", "palabras": [],
     "orden_busqueda": 3},                           # palabra del nombre
    {"codigo": "CI2", "letra": "W", "nombre": "Vaca", "palabras": [],
     "orden_busqueda": 4},                           # nombre que empieza
    {"codigo": "VACAS", "letra": "Y", "nombre": "Otra", "palabras": [],
     "orden_busqueda": 5},                           # código que empieza
    {"codigo": "CI0", "letra": "VACA", "nombre": "Otra", "palabras": [],
     "orden_busqueda": 6},                           # letra exacta
]


def test_f061_r2_orden_por_categoria_antes_que_el_desempate():
    r = _buscar(["vaca", "va"], ESCALERA)
    # «vaca»: letra exacta, código que empieza, nombre que empieza, palabra
    # del nombre, (ninguna palabra extra empieza por «vaca»), subcadena no
    # hay («nava» no la contiene) y la errata «baca».
    assert r["vaca"] == ["VACA", "Y", "W", "U", "R"]
    # «va»: código y letra que empiezan (la misma categoría: desempata
    # `orden_busqueda`, 5 antes que 6), nombre, palabra del nombre, palabra
    # extra y subcadena («nava»); sin errata (2 letras).
    assert r["va"] == ["Y", "VACA", "W", "U", "T", "S"]


def test_f061_r2_empate_por_orden_busqueda_y_las_nulas_detras_por_catalogo():
    catalogo = [
        {"codigo": "CI1", "letra": "A1", "nombre": "Baja uno", "palabras": [],
         "orden_busqueda": None},
        {"codigo": "CI2", "letra": "A2", "nombre": "Baja dos", "palabras": [],
         "orden_busqueda": 7},
        {"codigo": "CI3", "letra": "A3", "nombre": "Baja tres"},  # sin campos
        {"codigo": "CI4", "letra": "A4", "nombre": "Baja cuatro", "palabras": [],
         "orden_busqueda": 0},
    ]
    assert _buscar(["baja"], catalogo)["baja"] == ["A4", "A2", "A1", "A3"]


# ============== criterio 3: nada de lo de hoy deja de encontrarse ========= #
def test_f061_r3_toda_subcadena_de_letra_y_nombre_sigue_encontrandose():
    """Lo que encontraba F-030 (subcadena de «letra nombre» normalizados):
    toda subcadena con alguna letra de cada incidencia la sigue sacando."""
    r = _celda_letras(f"""
      state.tiposIncidencia = {json.dumps(CATALOGO)};
      const editor = nuevoEditor();
      const l = linea(1, 0);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      const perdidas = [];
      let probadas = 0;
      for (const t of state.tiposIncidencia) {{
        const texto = normalizar(t.letra + " " + t.nombre);
        for (let i = 0; i < texto.length; i++) {{
          for (let j = i + 1; j <= texto.length; j++) {{
            const sub = texto.slice(i, j);
            if (!/\\p{{L}}/u.test(sub) || !sub.trim()) continue;
            teclear(pct, sub);
            probadas++;
            const letras = panelInc().children.map((c) => c.innerHTML);
            if (!letras.some((h) => h.includes('class="cod">' + t.letra + "<")))
              perdidas.push(t.letra + ":" + sub);
          }}
        }}
      }}
      resultado = {{ probadas, perdidas }};
    """)
    assert r["probadas"] > 1000
    assert r["perdidas"] == []


# ======== criterio 5: el front solo filtra y ordena, no decide nada ======= #
def test_f061_r5_la_busqueda_no_cambia_lo_que_se_elige_ni_como_se_pinta():
    r = _celda_letras(f"""
      state.tiposIncidencia = {json.dumps(CATALOGO)};
      const editor = nuevoEditor();
      const l = linea(1, 70);
      state.edicion = [l];
      const pct = montar(l, 0, editor);
      teclear(pct, "baj");
      const filas0 = filas();
      pct.fire("keydown", "ArrowDown");
      pct.fire("keydown", "Enter");
      resultado = {{ filas0, elegida: state.incidenciasEdicion, pct: l.porcentaje }};
    """)
    assert r["filas0"][0] == ('sugerencia inc activa|<span class="cod">B</span>'
                              '<span class="desc">Enfermedad/Acc. no laboral</span>')
    assert r["elegida"] == [{"obra_ide": 1, "cod": "01", "descripcion": "Obra 1",
                             "codigo": "CIA", "letra": "AT",
                             "nombre": "Accidente/Enf. Profesional",
                             "dia_desde": None, "dia_hasta": None}]
    assert r["pct"] == 70
