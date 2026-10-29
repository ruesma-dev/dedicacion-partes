# tests/test_f063_filtro_incidencia.py
"""F-063 · Filtrar trabajadores por tipo de incidencia con fichas como las de
estado (`sdd: false`; los «R» de abajo son los `acceptance` de la feature en
`harness/features.json`, por orden).

- R1: con incidencias en el mes, una ficha por tipo presente (letra, nombre y
  nº de trabajadores con ese tipo, sin contar las quitadas); sin incidencias,
  ninguna ficha nueva.
- R2: un clic filtra y marca la ficha activa; otro clic, o «N trabajadores»,
  quita el filtro; elegir otra sustituye a la anterior.
- R3: se combina (Y) con la ficha de estado, el buscador y los filtros de
  columna.

Se ejecuta el código REAL de `app.js` en `node` (patrón de
`test_f041_filtro_obra.py`) con un DOM de mentira mínimo: `#resumen` guarda
sus fichas y cada ficha su manejador de clic, así que el test pulsa la ficha
como el usuario y mira qué trabajadores quedan visibles. Los dobles llevan la
forma que serializa la api (`TrabajadorOut` / `IncidenciaOut` de
`dedicacion-api/interface_adapters/api/schemas.py`), con las claves opcionales
a `null` y `quitada` siempre presente. Sin `node`, se saltan con su motivo; el
reviewer los exige `passed`. Sin red ni BBDD.
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


def _funcion(nombre: str) -> str | None:
    """El código de la función `nombre` de `app.js` (hasta la siguiente
    función o el siguiente rótulo de sección), o None si no existe."""
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |^// -+|\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    return m.group(0) if m else None


def _const(nombre: str) -> str:
    m = re.search(rf"^const {nombre} = (\[.*?\]|\{{.*?\}});", JS,
                  re.DOTALL | re.MULTILINE)
    assert m, f"no existe `const {nombre}` en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


#: Las de hoy (F-030, F-041, F-050): el filtrado y la cabecera.
FUNCIONES = ("normalizar", "etiquetaObra", "textoObra", "lineaCasa", "fmtPct",
             "textoColumna", "trabajadoresVisibles", "textoIncidencia",
             "incidenciaCasa", "renderCabecera")
#: Las de F-063. En la fase RED aún no existen: el arnés carga las que haya y
#: los tests fallan por lo que la pantalla hace, no por un nombre que falta.
FUNCIONES_F063 = ("tieneIncidencia", "tiposIncidenciaDelMes")

#: DOM de mentira: lo justo para `renderCabecera` (los `$` que toca, `#resumen`
#: con sus hijos y el clic de cada ficha). `renderTabla` cuenta sus llamadas.
DOM = r"""
function nodo() {
  return { className: "", textContent: "", title: "", disabled: false,
    hijos: [], oyentes: {}, classList: { toggle() {} },
    set innerHTML(v) { this.hijos = []; },
    appendChild(h) { this.hijos.push(h); return h; },
    addEventListener(ev, f) { this.oyentes[ev] = f; } };
}
const nodos = {};
var $ = (sel) => (nodos[sel] = nodos[sel] || nodo());
var document = { createElement: () => nodo() };
var pintadas = 0;
function renderTabla() { pintadas += 1; }
function fichas() {
  return $("#resumen").hijos.map((h) => ({ texto: h.textContent,
    clase: h.className, titulo: h.title }));
}
function pulsar(texto) {
  const h = $("#resumen").hijos.find((x) => x.textContent === texto);
  if (!h) throw new Error("no hay ficha «" + texto + "»: " +
    JSON.stringify(fichas().map((f) => f.texto)));
  h.oyentes.click();
}
function visibles() { return trabajadoresVisibles().map((t) => t.nombre); }
function activas() {
  return fichas().filter((f) => f.clase.includes("filtro-activo")).map((f) => f.texto);
}
"""


def _node(cuerpo: str, estado: dict) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-063 "
                    "no se ejecutan")
    funciones = [_funcion(f) for f in FUNCIONES]
    assert all(funciones), "falta en app.js alguna función de hoy"
    nuevas = [c for c in (_funcion(f) for f in FUNCIONES_F063) if c]
    programa = "\n".join(
        [_const("MESES"), _const("ORDEN_ESTADO"), *funciones, *nuevas, DOM,
         "var state = " + json.dumps(estado, ensure_ascii=False) + ";",
         "var resultado;", cuerpo,
         "process.stdout.write(JSON.stringify(resultado));"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30)
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout)


# ============================ datos de prueba ============================ #
TIPOS = {"CIV": ("V", "Vacaciones"), "CIE": ("B", "Enfermedad"),
         "CIP": ("P", "Permiso")}
#: El filtro activo: el tipo elegido, con lo que pinta su ficha.
FILTRO_V = {"codigo": "CIV", "letra": "V", "nombre": "Vacaciones"}


def _inc(codigo: str, desde: int, hasta: int, quitada: bool = False,
         id_: int | None = None, obra: int = 3) -> dict:
    """Una incidencia como la serializa `IncidenciaOut` (todas las claves)."""
    letra, nombre = TIPOS[codigo]
    return {"id": id_, "obra_ide": obra, "obra_cod": f"070{obra}",
            "obra_descripcion": f"Obra {obra}", "codigo": codigo,
            "letra": letra, "nombre": nombre, "dia_desde": desde,
            "dia_hasta": hasta, "sigrid_estado": None,
            "sigrid_parte_cod": None, "sigrid_motivo": None,
            "quitada": quitada}


def _linea(obra: int, porcentaje: float) -> dict:
    """Una línea como la serializa `LineaOut` (sin vinculados: la clave no
    sale, F-044 R6)."""
    return {"obra_ide": obra, "cod": f"070{obra}",
            "descripcion": f"Obra {obra}", "es_postventa": False,
            "porcentaje": porcentaje, "obra_activa": True, "obra_empresa": 1,
            "otra_empresa": False, "obra_admite_postventa": False,
            "ofrecible": True, "partida_ide": None, "partida_cod": None,
            "partida_res": None, "partida_fija": False,
            "propuesta_cod": None, "propuesta_res": None,
            "propuesta_metodo": None, "propuesta_pendiente": False}


def _trab(ide: int, nombre: str, estado: str, lineas: list, incidencias: list,
          activo: bool = True) -> dict:
    """Un trabajador como lo serializa `TrabajadorOut`."""
    total = sum(l["porcentaje"] for l in lineas)
    return {"ide": ide, "nombre": nombre, "categoria": None, "activo": activo,
            "empresa": 1, "lineas": lineas, "total": total,
            "desviacion": total - 100, "estado": estado,
            "puede_deshacer": False, "incidencias": incidencias}


def _trabajadores() -> list[dict]:
    return [
        # Una enfermedad quitada (no cuenta) DELANTE de dos vacaciones (cuentan
        # UNA vez): el orden no cambia el conteo.
        _trab(1, "Ana", "OK", [_linea(1, 100)],
              [_inc("CIE", 1, 2, quitada=True, id_=12),
               _inc("CIV", 5, 9, id_=10), _inc("CIV", 20, 22, id_=11)]),
        _trab(2, "Benito", "FALTA", [_linea(2, 60)], [_inc("CIE", 1, 3, id_=13)]),
        # Su única vacación está quitada: no cuenta ni filtra.
        _trab(3, "Carla", "OK", [_linea(1, 100)],
              [_inc("CIV", 7, 8, quitada=True, id_=14)]),
        _trab(4, "Dani", "SIN_CARGA", [], [_inc("CIV", 1, 31, id_=15)]),
        _trab(5, "Eva", "OK", [_linea(2, 100)], []),
        # Recién añadida en el editor: sin `id` todavía.
        _trab(6, "Fede", "EXCESO", [_linea(1, 80), _linea(2, 40)],
              [_inc("CIP", 12, 12)]),
        # Baja sin carga: la tabla no la enseña; su vacación no cuenta.
        _trab(7, "Gil", "SIN_CARGA", [], [_inc("CIV", 1, 31, id_=16)],
              activo=False),
    ]


def _estado(trabajadores: list[dict] | None = None, **extra) -> dict:
    estado = {"anio": 2026, "mes": 10, "periodoEstado": "ABIERTO",
              "trabajadores": _trabajadores() if trabajadores is None
              else trabajadores,
              "resumen": {"total": 6, "ok": 3, "falta": 1, "exceso": 1,
                          "sin_carga": 1},
              "filtroTexto": "", "filtroEstado": None, "filtroIncidencia": None,
              "soloPendientes": False,
              "columnas": ["nombre", "categoria", "asignaciones", "total"],
              "filtrosCol": {}, "orden": {"campo": "nombre", "dir": 1}}
    estado.update(extra)
    return estado


FICHAS_ESTADO = ["6 trabajadores", "3 OK", "1 sin carga", "1 falta",
                 "1 exceso"]
TODOS = ["Ana", "Benito", "Carla", "Dani", "Eva", "Fede"]


def _escena(pasos: list[str], estado: dict | None = None) -> list[dict]:
    """Pinta la cabecera y, tras cada paso (`pulsar(...)` o cualquier JS),
    fotografía fichas, activas, visibles y repintados de la tabla."""
    cuerpo = ["renderCabecera();",
              "resultado = [{fichas: fichas(), activas: activas(), "
              "visibles: visibles(), pintadas}];"]
    for paso in pasos:
        cuerpo.append(paso + ";")
        cuerpo.append("resultado.push({fichas: fichas(), activas: activas(), "
                      "visibles: visibles(), pintadas});")
    return _node("\n".join(cuerpo), estado or _estado())


def _textos(foto: dict) -> list[str]:
    return [f["texto"] for f in foto["fichas"]]


# ================================== R1 ================================== #
def test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores():
    """V: Ana (dos vacaciones, cuenta una) y Dani; no Carla (quitada) ni Gil
    (baja sin carga, fuera de la tabla). B: Benito, no Ana (quitada). P: Fede,
    aunque su incidencia aún no tenga `id`."""
    foto = _escena([])[0]
    assert _textos(foto) == [*FICHAS_ESTADO, "B Enfermedad 1", "P Permiso 1",
                             "V Vacaciones 2"]
    nuevas = foto["fichas"][len(FICHAS_ESTADO):]
    assert {f["clase"] for f in nuevas} == {"badge chip-inc"}
    assert {f["titulo"] for f in nuevas} == {"Filtrar por incidencia"}
    assert foto["activas"] == [] and foto["visibles"] == TODOS


def test_f063_r1_sin_incidencias_en_el_mes_ninguna_ficha_nueva():
    sin = [{**t, "incidencias": []} for t in _trabajadores()]
    assert _textos(_escena([], _estado(sin))[0]) == FICHAS_ESTADO


def test_f063_r1_las_quitadas_solas_no_sacan_ficha():
    """Un mes cuyas únicas incidencias están quitadas («quitada · sigue en
    Sigrid»): ninguna ficha nueva."""
    quitadas = [{**t, "incidencias": [{**i, "quitada": True}
                                      for i in t["incidencias"]]}
                for t in _trabajadores()]
    assert _textos(_escena([], _estado(quitadas))[0]) == FICHAS_ESTADO


def test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo():
    """La función que alimenta las fichas: un tipo por `codigo`, ordenados por
    letra, con los trabajadores (no las incidencias) que lo tienen."""
    r = _node("resultado = typeof tiposIncidenciaDelMes === 'function' ? "
              "tiposIncidenciaDelMes(state.trabajadores) : 'no existe';",
              _estado())
    assert r == [
        {"codigo": "CIE", "letra": "B", "nombre": "Enfermedad", "n": 1},
        {"codigo": "CIP", "letra": "P", "nombre": "Permiso", "n": 1},
        {"codigo": "CIV", "letra": "V", "nombre": "Vacaciones", "n": 2},
    ]


def test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre():
    """Dos códigos con la misma letra: dos fichas, por `codigo`, ordenadas por
    nombre (desempate; añadido por el superviviente M14 de la campaña manual),
    y cada una filtra lo suyo, no lo de la letra."""
    otra = {**_inc("CIV", 1, 2, id_=20), "codigo": "CVA",
            "nombre": "Vacaciones año anterior"}
    trabajadores = [
        _trab(1, "Ana", "OK", [_linea(1, 100)], [otra]),
        _trab(2, "Benito", "OK", [_linea(1, 100)], [_inc("CIV", 3, 4, id_=21)]),
    ]
    fotos = _escena(['pulsar("V Vacaciones 1")'], _estado(trabajadores))
    assert _textos(fotos[0])[len(FICHAS_ESTADO):] == [
        "V Vacaciones 1", "V Vacaciones año anterior 1"]
    assert fotos[1]["visibles"] == ["Benito"]
    assert fotos[1]["activas"] == ["V Vacaciones 1"]


# ================================== R2 ================================== #
def test_f063_r2_un_clic_filtra_y_marca_la_ficha():
    antes, despues = _escena(['pulsar("V Vacaciones 2")'])
    assert despues["visibles"] == ["Ana", "Dani"]
    assert despues["activas"] == ["V Vacaciones 2"]
    assert despues["pintadas"] == antes["pintadas"] + 1
    # Las fichas no cambian de número al filtrar: cuentan el mes entero.
    assert _textos(despues) == _textos(antes)


def test_f063_r2_una_quitada_no_filtra():
    """Ana tiene una enfermedad quitada: «B» deja solo a Benito."""
    assert _escena(['pulsar("B Enfermedad 1")'])[1]["visibles"] == ["Benito"]


def test_f063_r2_otro_clic_quita_el_filtro():
    fotos = _escena(['pulsar("V Vacaciones 2")', 'pulsar("V Vacaciones 2")'])
    assert fotos[2]["visibles"] == TODOS
    assert fotos[2]["activas"] == []


def test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado():
    fotos = _escena(['pulsar("V Vacaciones 2")', 'pulsar("3 OK")',
                     'pulsar("6 trabajadores")'])
    assert fotos[3]["visibles"] == TODOS
    assert fotos[3]["activas"] == []


def test_f063_r2_elegir_otra_sustituye_a_la_anterior():
    fotos = _escena(['pulsar("V Vacaciones 2")', 'pulsar("P Permiso 1")'])
    assert fotos[2]["visibles"] == ["Fede"]
    assert fotos[2]["activas"] == ["P Permiso 1"]


def test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo():
    """Si el tipo filtrado se queda sin trabajadores (p. ej. se quitó en el
    editor la única incidencia), su ficha sigue, activa y con 0, para poder
    quitar el filtro con otro clic, como «0 falta» con la de estado: la tabla
    no se queda vacía sin una ficha que lo explique."""
    sin = [{**t, "incidencias": []} for t in _trabajadores()]
    fotos = _escena(['pulsar("V Vacaciones 0")'],
                    _estado(sin, filtroIncidencia=FILTRO_V))
    assert _textos(fotos[0]) == [*FICHAS_ESTADO, "V Vacaciones 0"]
    assert fotos[0]["activas"] == ["V Vacaciones 0"]
    assert fotos[0]["visibles"] == []
    assert _textos(fotos[1]) == FICHAS_ESTADO
    assert fotos[1]["visibles"] == TODOS


def test_f063_r2_cambiar_de_mes_quita_el_filtro_de_incidencia():
    """Como la ficha de estado: otro mes trae otros tipos."""
    mover = _plano(_funcion("moverMes") or "")
    assert "state.filtroIncidencia = null;" in mover
    assert mover.index("state.filtroIncidencia = null;") < \
        mover.index("cargarPeriodo(")


# ================================== R3 ================================== #
def test_f063_r3_se_combina_con_la_ficha_de_estado():
    """V (Ana, Dani) y OK (Ana, Carla, Eva): solo Ana; las dos activas, y
    quitar la de estado no quita la de incidencia."""
    fotos = _escena(['pulsar("V Vacaciones 2")', 'pulsar("3 OK")',
                     'pulsar("3 OK")'])
    assert fotos[2]["visibles"] == ["Ana"]
    assert fotos[2]["activas"] == ["3 OK", "V Vacaciones 2"]
    assert fotos[3]["visibles"] == ["Ana", "Dani"]
    assert fotos[3]["activas"] == ["V Vacaciones 2"]


def test_f063_r3_se_combina_con_el_buscador():
    fotos = _escena(['pulsar("V Vacaciones 2")', 'state.filtroTexto = "dani"',
                     'state.filtroTexto = "eva"'])
    assert fotos[2]["visibles"] == ["Dani"]
    assert fotos[3]["visibles"] == []


def test_f063_r3_se_combina_con_los_filtros_de_columna():
    """Obra «0701» (Ana, Carla y Fede tienen línea en ella) y V: solo Ana.
    Nombre «a» (Ana, Carla, Dani, Eva) y V: Ana y Dani."""
    fotos = _escena(['pulsar("V Vacaciones 2")',
                     'state.filtrosCol = {asignaciones: "0701"}',
                     'state.filtrosCol = {nombre: "a"}'])
    assert fotos[2]["visibles"] == ["Ana"]
    assert fotos[3]["visibles"] == ["Ana", "Dani"]


# ======================= solo pantalla (límite) ========================= #
def test_f063_el_filtro_solo_vive_en_la_cabecera_y_el_filtrado():
    """Es un filtro de pantalla: no decide nada de lo que se registra. Solo lo
    escriben la cabecera y el cambio de mes, y solo lo lee el filtrado."""
    usos = {n for n in re.findall(r"^(?:async )?function (\w+)\(", JS,
                                  re.MULTILINE)
            if "filtroIncidencia" in (_funcion(n) or "")}
    assert usos == {"renderCabecera", "trabajadoresVisibles", "moverMes"}
    for nombre in FUNCIONES_F063:
        cuerpo = _funcion(nombre)
        assert cuerpo, f"no existe la función {nombre} en app.js"
        assert "api(" not in cuerpo and "state." not in cuerpo, nombre
