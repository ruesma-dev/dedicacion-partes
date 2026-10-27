# tests/test_f067_ver_vinculados.py
"""F-067 · Casilla para ver u ocultar los recursos vinculados en el cuadrante
(`sdd: false`; los «R» son los `acceptance` de la feature en
`harness/features.json`, por orden).

- R1: marcada (defecto, también con preferencias guardadas antiguas sin
  ella) el cuadrante es el de hoy; desmarcada, ninguna subfila de vinculado y
  el `rowspan` de las columnas del trabajador cuadra con líneas e
  incidencias.
- R2: la preferencia se guarda y se recupera con las de la tabla; sin
  localStorage la página funciona (marcada).
- R3: desmarcada, los filtros de columna «Tipo recurso» y «Partida» deciden
  solo con el trabajador y sus líneas; marcada, como hoy.
- R4: el modal de registro no cambia con la casilla (vinculados y su pisado
  marcado por defecto, F-064, en los dos estados).
- R5: la casilla no sale en un mes sin vinculados.
- R6: tests sin red ni BBDD, en rojo con el código de antes (fase RED en
  `progress/impl_F-067.md`); los de F-044, F-063, F-064 y F-065, intactos.

Código REAL de `app.js` en `node` con el DOM de mentira de F-063 (fichas del
resumen con sus manejadores), el de F-044 (filas del trabajador) y el de
F-064 (modal de registro), más un `localStorage` de mentira. Los dobles
llevan la forma serializada de la api: `LineaOut` con `vinculados` solo si
hay alguno (`exclude_if`) y cada subfila como `SubfilaOut` (los `TEL` y `GAS`
de F-044, con todas sus claves). Sin `node`, se saltan con su motivo; el
reviewer los exige `passed`. Sin red ni BBDD.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from tests.test_f044_vinculados_front import (
    FILA,
    GAS,
    TEL,
    _accion_reg,
    _vin_reg,
)
from tests.test_f050_m2_arreglos import _node as _node_m2
from tests.test_f063_filtro_incidencia import (
    DOM,
    FUNCIONES,
    FUNCIONES_F063,
    JS,
    _const,
    _funcion,
    _inc,
    _linea,
    _trab,
)
from tests.test_f064_pisado_vinculados import (
    PIS_TRAB,
    PIS_VIN,
    TF,
    _conflicto,
    _escenario,
    _obra,
    _pf,
)

PREFS = ("cargarPrefsTabla", "guardarPrefsTabla")

#: `localStorage` de mentira (o uno que lanza, como con el almacenamiento
#: bloqueado) y la casilla de la cabecera como la ve el test.
ALMACEN = r"""
var almacen = {};
var localStorage = BLOQUEADO
  ? { getItem() { throw new Error("bloqueado"); },
      setItem() { throw new Error("bloqueado"); } }
  : { getItem: (k) => (k in almacen ? almacen[k] : null),
      setItem: (k, v) => { almacen[k] = String(v); } };
function casilla() {
  const h = $("#resumen").hijos.find((x) =>
    String(x.className || "").includes("chk-vinculados"));
  if (!h) return null;
  const input = h.hijos.find((x) => x.type === "checkbox");
  return { h, input };
}
function vistaCasilla() {
  const c = casilla();
  if (!c) return null;
  return { clase: c.h.className, titulo: c.h.title,
    texto: c.h.hijos.map((x) => x.textContent).join(""),
    marcada: c.input ? c.input.checked : null };
}
function cambiar(valor) {
  const c = casilla();
  c.input.checked = valor;
  c.input.oyentes.change();
}
function guardado() {
  return CLAVE_TABLA in almacen ? JSON.parse(almacen[CLAVE_TABLA]) : null;
}
"""


def _const_texto(nombre: str) -> str:
    m = re.search(rf'^const {nombre} = "[^"]*";$', JS, re.MULTILINE)
    assert m, f"no existe `const {nombre}` en app.js"
    return m.group(0)


def _programa(cuerpo: str, estado: dict, almacen: dict | None = None,
              bloqueado: bool = False) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-067 "
                    "no se ejecutan")
    funciones = [_funcion(f) for f in (*FUNCIONES, *PREFS)]
    assert all(funciones), "falta en app.js alguna función de hoy"
    nuevas = [c for c in (_funcion(f) for f in FUNCIONES_F063) if c]
    programa = "\n".join(
        [_const("MESES"), _const("ORDEN_ESTADO"), _const("COLUMNAS"),
         _const("ORDEN_COLUMNAS_DEFECTO"), _const_texto("CLAVE_TABLA"),
         *funciones, *nuevas, DOM,
         "var BLOQUEADO = " + json.dumps(bloqueado) + ";", ALMACEN,
         "almacen = " + json.dumps(almacen or {}, ensure_ascii=False) + ";",
         "var state = " + json.dumps(estado, ensure_ascii=False) + ";",
         "var resultado;", cuerpo,
         "process.stdout.write(JSON.stringify(resultado));"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30)
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout)


# ============================ datos de prueba ============================ #
def _con_vin(linea: dict, *vinculados: dict) -> dict:
    """`LineaOut` con sus subfilas (la clave solo sale si hay alguna)."""
    return {**linea, "vinculados": list(vinculados)}


def _trabajadores() -> list[dict]:
    benito = _linea(2, 60) | {"partida_ide": 5, "partida_cod": "CIGA14",
                              "partida_res": "GASOIL OBRA"}
    return [
        # Ana: su teléfono (propuesta, sin elegida) bajo la 0701.
        _trab(1, "Ana", "OK", [_con_vin(_linea(1, 100), TEL)], []),
        # Benito: sin vinculados; su LÍNEA tiene la partida CIGA14 elegida.
        _trab(2, "Benito", "FALTA", [benito], [_inc("CIV", 5, 9, id_=10)]),
        # Carla: el gasoil (elegida CIGA14 · GASOIL) bajo la 0701.
        _trab(3, "Carla", "OK", [_con_vin(_linea(1, 50), GAS),
                                 _linea(2, 50)], []),
    ]


def _estado(trabajadores: list[dict] | None = None, **extra) -> dict:
    estado = {"anio": 2026, "mes": 10, "periodoEstado": "ABIERTO",
              "trabajadores": _trabajadores() if trabajadores is None
              else trabajadores,
              "resumen": {"total": 3, "ok": 2, "falta": 1, "exceso": 0,
                          "sin_carga": 0},
              "filtroTexto": "", "filtroEstado": None,
              "filtroIncidencia": None, "soloPendientes": False,
              "columnas": ["nombre", "asignaciones", "tipo", "partida",
                           "total"],
              "anchos": {}, "filtrosCol": {},
              "orden": {"campo": "nombre", "dir": 1},
              "verVinculados": True}
    estado.update(extra)
    return estado


FICHAS = ["3 trabajadores", "2 OK", "0 sin carga", "1 falta", "0 exceso",
          "V Vacaciones 1"]
FOTO = ("resultado.push({fichas: $('#resumen').hijos.map((h) => "
        "h.textContent), casilla: vistaCasilla(), ver: state.verVinculados, "
        "guardado: guardado(), pintadas});")


def _escena(pasos: list[str], estado: dict | None = None, **kw) -> list:
    cuerpo = ["resultado = [];", "renderCabecera();", FOTO]
    for paso in pasos:
        cuerpo += [paso + ";", FOTO]
    return _programa("\n".join(cuerpo), estado or _estado(), **kw)


# ================== R1 · subfilas y rowspan (construirFila) ============== #
def _filas(ver: bool, incidencias: int = 0) -> list:
    """Las `<tr>` de un trabajador con dos líneas (la primera con teléfono y
    gasoil) e `incidencias`: clases, línea, vinculado y celdas con rowSpan."""
    return _node_m2("\n".join([
        _const("COLUMNAS_POR_LINEA"), FILA, _funcion("construirFila"),
        _funcion("construirFilaVinculado"),
        ("const state = {columnas: ['nombre', 'asignaciones', 'tipo', "
         "'partida', 'total'], seleccionIde: 7, seleccion: new Set(), "
         "editandoIde: null, resaltadas: [], verVinculados: "
         + json.dumps(ver) + "};"),
        "const t = {ide: 7, activo: true, lineas: " + json.dumps(
            [{"obra_ide": 1, "vinculados": [TEL, GAS]}, {"obra_ide": 2}])
        + ", incidencias: " + json.dumps([{}] * incidencias) + "};",
        ("const frag = construirFila(t);"
         "process.stdout.write(JSON.stringify(frag.trs.map((tr) => ["
         "tr.classList.lista().sort().join(' '), tr.dataset.linea, "
         "tr.dataset.vinculado === undefined ? null : tr.dataset.vinculado, "
         "tr.tds.filter((td) => td.rowSpan !== undefined).map((td) => "
         "[td.clave, td.rowSpan])])));"),
    ]))


def test_f067_r1_desmarcada_ninguna_subfila_de_vinculado_y_rowspan_cuadra():
    filas = _filas(False, incidencias=1)
    assert [(f[0], f[1], f[2]) for f in filas] == [
        ("fila seleccionada", 0, None),
        ("fila seleccionada subfila", 1, None),
        ("fila fila-inc seleccionada subfila", 2, None)]
    assert filas[0][3] == [["nombre", 3], ["total", 3]]


def test_f067_r1_desmarcada_sin_incidencias_rowspan_de_las_lineas():
    filas = _filas(False)
    assert [f[2] for f in filas] == [None, None]
    assert filas[0][3] == [["nombre", 2], ["total", 2]]


def test_f067_r1_marcada_el_cuadrante_de_hoy():
    filas = _filas(True, incidencias=1)
    assert [(f[1], f[2]) for f in filas] == [
        (0, None), (0, 10), (0, 11), (1, None), (2, None)]
    assert filas[0][3] == [["nombre", 5], ["total", 5]]


def test_f067_r1_el_estado_arranca_marcado():
    m = re.search(r"^const state = \{.*?^\};$", JS, re.DOTALL | re.MULTILINE)
    assert m and re.search(r"^\s+verVinculados: true,", m.group(0),
                           re.MULTILINE)


# ============================ R2 · preferencia =========================== #
ORDEN = ["nombre", "categoria", "asignaciones", "tipo", "partida", "total"]
CLAVE = "dedicacion:tabla:v1"


def _prefs(cuerpo: str, almacen: dict | None = None, **kw) -> object:
    return _programa(cuerpo, _estado(), almacen=almacen, **kw)


def test_f067_r2_sin_nada_guardado_o_con_prefs_antiguas_marcada():
    antiguas = {CLAVE: json.dumps({"orden": ORDEN, "anchos": {"nombre": 300}})}
    r = _prefs("cargarPrefsTabla(); resultado = [state.verVinculados, "
               "state.anchos];", antiguas)
    assert r == [True, {"nombre": 300}]
    assert _prefs("cargarPrefsTabla(); resultado = state.verVinculados;") \
        is True


def test_f067_r2_se_recupera_lo_guardado():
    for valor in (False, True):
        guardadas = {CLAVE: json.dumps({"orden": ORDEN, "anchos": {},
                                        "verVinculados": valor})}
        assert _prefs("cargarPrefsTabla(); resultado = state.verVinculados;",
                      guardadas) is valor


def test_f067_r2_se_guarda_con_las_de_la_tabla_y_vuelve():
    r = _prefs("""
      state.columnas = ['total', 'nombre']; state.anchos = {total: 200};
      state.verVinculados = false; guardarPrefsTabla();
      const escrito = guardado();
      state.verVinculados = true; cargarPrefsTabla();
      resultado = [escrito, state.verVinculados];
    """)
    assert r[0] == {"orden": ["total", "nombre"], "anchos": {"total": 200},
                    "verVinculados": False}
    assert r[1] is False


def test_f067_r2_sin_localstorage_la_pagina_funciona_marcada():
    fotos = _escena(["cargarPrefsTabla(); renderCabecera()", "cambiar(false)",
                     "cambiar(true)"], bloqueado=True)
    assert [f["ver"] for f in fotos] == [True, True, False, True]
    assert fotos[1]["casilla"]["marcada"] is True
    assert [f["pintadas"] for f in fotos] == [0, 0, 1, 2]


# ===================== R3 · filtros Tipo recurso y Partida =============== #
def _visibles(filtros: dict, ver: bool) -> list[str]:
    return _programa("resultado = trabajadoresVisibles().map((t) => t.nombre);",
                     _estado(filtrosCol=filtros, verVinculados=ver))


def test_f067_r3_tipo_recurso_desmarcada_solo_persona():
    assert _visibles({"tipo": "telefono"}, True) == ["Ana"]
    assert _visibles({"tipo": "telefono"}, False) == []
    assert _visibles({"tipo": "co-11"}, True) == ["Carla"]
    assert _visibles({"tipo": "co-11"}, False) == []
    for ver in (True, False):
        assert _visibles({"tipo": "persona"}, ver) == ["Ana", "Benito",
                                                       "Carla"]


def test_f067_r3_partida_desmarcada_solo_las_lineas():
    """«ciga14»: la línea de Benito (elegida) y la subfila de Carla."""
    assert _visibles({"partida": "ciga14"}, True) == ["Benito", "Carla"]
    assert _visibles({"partida": "ciga14"}, False) == ["Benito"]
    for ver in (True, False):
        assert _visibles({"partida": "automatica"}, ver) == ["Ana", "Carla"]


# ====================== R1, R2, R5 · la casilla ========================== #
def test_f067_r1_la_casilla_sale_marcada_junto_a_las_fichas():
    foto = _escena([])[0]
    assert foto["fichas"][:len(FICHAS)] == FICHAS
    assert len(foto["fichas"]) == len(FICHAS) + 1
    assert foto["casilla"]["marcada"] is True
    assert foto["casilla"]["texto"] == "Recursos vinculados"
    assert "check" in foto["casilla"]["clase"].split()


def test_f067_r2_desmarcar_guarda_y_repinta_la_tabla():
    fotos = _escena(["cambiar(false)", "cambiar(true)"])
    assert [f["ver"] for f in fotos] == [True, False, True]
    assert [f["pintadas"] for f in fotos] == [0, 1, 2]
    assert fotos[0]["guardado"] is None
    assert fotos[1]["guardado"]["verVinculados"] is False
    assert fotos[2]["guardado"]["verVinculados"] is True
    assert fotos[1]["guardado"]["orden"] == _estado()["columnas"]


def test_f067_r2_con_la_preferencia_desmarcada_la_casilla_sale_desmarcada():
    foto = _escena([], _estado(verVinculados=False))[0]
    assert foto["casilla"]["marcada"] is False


def test_f067_r5_basta_un_vinculado_bajo_cualquier_linea_del_mes():
    """El único vinculado del mes, bajo la SEGUNDA línea de Carla, y todos
    con líneas: la casilla sale (añadido por N9 de la campaña manual, que
    solo mataban de rebote los trabajadores sin líneas de F-063)."""
    trabajadores = [_trab(1, "Ana", "OK", [_linea(1, 100)], []),
                    _trab(3, "Carla", "OK", [_linea(1, 50),
                                             _con_vin(_linea(2, 50), GAS)],
                          [])]
    foto = _escena([], _estado(trabajadores))[0]
    assert foto["casilla"]["marcada"] is True


def test_f067_r5_sin_vinculados_en_el_mes_no_sale_la_casilla():
    sin = [_trab(1, "Ana", "OK", [_linea(1, 100)], []),
           _trab(2, "Benito", "FALTA", [_linea(2, 60)],
                 [_inc("CIV", 5, 9, id_=10)])]
    foto = _escena([], _estado(sin))[0]
    assert foto["casilla"] is None
    assert foto["fichas"] == FICHAS


# ======================= R4 · el modal no cambia ========================= #
def test_f067_r4_el_modal_es_el_mismo_marcada_o_desmarcada():
    obra = {**_obra(694, [_conflicto(PIS_VIN, vinculado=TF),
                          _conflicto(PIS_TRAB)]),
            "obra_destino": {"codigo": "0694"},
            "acciones": [_accion_reg()], "vinculados": [_vin_reg()]}
    vistas = []
    for ver in (True, False):
        vistas.append(_escenario("""
          state.verVinculados = D.ver;
          await abrir(D.pf);
          obs.html = dom.html; obs.marcadas = marcadas();
        """, {"pf": _pf(obra), "ver": ver}))
    assert vistas[0] == vistas[1]
    assert 'class="fila-vinculado-reg"' in vistas[1]["html"]
    assert "TF-10" in vistas[1]["html"]
    assert vistas[1]["marcadas"] == [PIS_VIN]


def test_f067_r4_solo_pantalla_la_preferencia_no_llega_al_registro():
    """Solo la leen o escriben la cabecera, sus preferencias, el filtrado y
    el pintado de filas; ninguna función del modal ni del registro."""
    usos = {n for n in re.findall(r"^(?:async )?function (\w+)\(", JS,
                                  re.MULTILINE)
            if "verVinculados" in (_funcion(n) or "")}
    assert usos == {"renderCabecera", "cargarPrefsTabla", "guardarPrefsTabla",
                    "trabajadoresVisibles", "construirFila"}
