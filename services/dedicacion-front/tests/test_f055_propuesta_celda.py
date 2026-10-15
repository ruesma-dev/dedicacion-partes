# tests/test_f055_propuesta_celda.py
"""F-055 · T13 y T13b: la celda Partida con la propuesta guardada y la
consulta mientras se buscan (R27, R36; D7, D9).

- R27: sin elegida y con `propuesta_cod`, la celda enseña «código ·
  descripción» en cursiva con su método; sin ella, «buscando partida…» si
  hay propuestas en curso y, si no, «automática».
- R36: mientras `propuestas_en_curso`, UN solo temporizador consulta
  `GET …/propuestas` cada 5 s, copia la propuesta a las líneas aún sin
  elegida, repinta solo las celdas Partida y para con `en_curso` falso o al
  cambiar de mes o empresa. Tras escribir (D9), `aplicarFila` y los
  manejadores de Completar y Copiar mes lo arrancan con el `bool` de la
  respuesta, sin recargar.

El código REAL de `static/js/app.js` en `node`, con temporizador y `api`
falsos; lo que toca el DOM, comprobado en estático. Sin `node`, los de
lógica se saltan con su motivo (el reviewer los exige `passed`).
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from tests.test_f050_subfilas import CSS, JS, _const, _funcion, _plano

FUNCIONES = ["textoPartida", "rotuloOrigen", "htmlPartida",
             "aplicarPropuestas", "marcarPropuestas", "reiniciarPropuestas",
             "seguirPropuestas", "consultarPropuestas"]
CONSTS = ("INTERVALO_PROPUESTAS", "propuestas")

#: Dobles del entorno: temporizadores que se disparan a mano, `api` que
#: contesta en orden y anota las rutas, el repintado anotado y `escapeHtml`.
ENTORNO = """
var temporizadores = [];
var setTimeout = (fn, ms) => { temporizadores.push({fn, ms, vivo: true});
                               return temporizadores.length; };
var clearTimeout = (id) => { if (temporizadores[id - 1])
                               temporizadores[id - 1].vivo = false; };
var vivos = () => temporizadores.filter((t) => t.vivo).length;
async function disparar() {
  const t = temporizadores.find((x) => x.vivo);
  t.vivo = false; t.fn();
  for (let i = 0; i < 20; i++) await Promise.resolve();
}
var rutas = []; var respuestas = [];
async function api(ruta) { rutas.push(ruta); const r = respuestas.shift();
                           if (r instanceof Error) throw r; return r; }
var repintadas = 0;
function repintarCeldasPartida() { repintadas += 1; }
function escapeHtml(t) { return String(t == null ? "" : t)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
"""


def _node(cuerpo: str, estado: dict) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-055 "
                    "no se ejecutan")
    programa = "\n".join(
        [*(_const(c) for c in CONSTS), *(_funcion(f) for f in FUNCIONES),
         ENTORNO, "var state = " + json.dumps(estado, ensure_ascii=False)
         + ";", "(async () => { var resultado;", cuerpo,
         "process.stdout.write(JSON.stringify(resultado)); })();"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


def _l(obra, **kw):
    return {"obra_ide": obra, "es_postventa": False, "partida_ide": None,
            "partida_cod": None, "partida_res": None, "partida_fija": False,
            "propuesta_cod": None, "propuesta_res": None,
            "propuesta_metodo": None, **kw}


PROP = {"propuesta_cod": "CI.1.20", "propuesta_res": "JEFE DE OBRA",
        "propuesta_metodo": "parte_anterior"}


# ============================ R27 · la celda ============================= #
@pytest.mark.parametrize("linea, en_curso, esperado", [
    (_l(1, **PROP), False,
     '<em class="partida-propuesta" title="Propuesta: parte anterior">'
     'CI.1.20 · JEFE DE OBRA<span class="partida-metodo"> · parte anterior'
     '</span></em>'),
    (_l(1, **PROP), True,
     '<em class="partida-propuesta" title="Propuesta: parte anterior">'
     'CI.1.20 · JEFE DE OBRA<span class="partida-metodo"> · parte anterior'
     '</span></em>'),
    (_l(1), True, '<span class="partida-auto buscando">buscando partida…'
                  '</span>'),
    (_l(1), False, '<span class="partida-auto">automática</span>'),
    (_l(1, partida_ide=7, partida_cod="CI.1.9", partida_res="ADM", **PROP),
     True, '<span class="partida-elegida">CI.1.9 · ADM</span>'),
    (_l(1, propuesta_cod="X<1", propuesta_metodo="auto_nombre"), False,
     '<em class="partida-propuesta" title="Propuesta: casada por nombre">'
     'X&lt;1<span class="partida-metodo"> · casada por nombre</span></em>'),
], ids=["propuesta", "propuesta_en_curso", "buscando", "automatica",
        "elegida_manda", "escapa"])
def test_f055_r27_html_de_la_celda(linea, en_curso, esperado):
    assert _node(f"resultado = htmlPartida({json.dumps(linea)}, "
                 f"{json.dumps(en_curso)});", {}) == esperado


def test_f055_r27_construir_celda_usa_html_partida():
    celda = _plano(_funcion("construirCelda"))
    assert "td.innerHTML = htmlPartida(l, state.propuestasEnCurso);" in celda
    assert "td.dataset.ide = t.ide;" in celda
    assert "td.dataset.linea = idx;" in celda
    assert "else if (l.propuesta_cod || state.propuestasEnCurso) {" in celda
    assert ".partida-propuesta {" in CSS and "font-style: italic" in \
        CSS.split(".partida-propuesta {")[1].split("}")[0]


# ===================== R36 · la consulta cada 5 s ======================== #
def _trab(ide, *lineas):
    return {"ide": ide, "lineas": list(lineas)}


ESTADO = {"anio": 2026, "mes": 9, "editandoIde": None,
          "propuestasEnCurso": False,
          "trabajadores": [_trab(14, _l(100), _l(101, partida_ide=7)),
                           _trab(10, _l(100))]}
LINEAS = [{"trabajador_ide": 14, "obra_ide": 100, "es_postventa": False,
           **PROP},
          {"trabajador_ide": 14, "obra_ide": 101, "es_postventa": False,
           **PROP},
          {"trabajador_ide": 99, "obra_ide": 100, "es_postventa": False,
           **PROP}]


def test_f055_r36_consulta_a_los_5_s_copia_y_repinta():
    r = _node("""
      marcarPropuestas(true);
      const antes = rutas.length;
      respuestas.push({en_curso: true, lineas: %s});
      await disparar();
      resultado = {ms: temporizadores[0].ms, antes, rutas, repintadas,
                   vivos: vivos(), en_curso: state.propuestasEnCurso,
                   lineas: state.trabajadores.map((t) => t.lineas)};
    """ % json.dumps(LINEAS), ESTADO)
    assert r["ms"] == 5000 and r["antes"] == 0
    assert r["rutas"] == ["/periodos/2026/9/propuestas"]
    assert r["repintadas"] == 1 and r["vivos"] == 1 and r["en_curso"]
    [[a, b], [c]] = r["lineas"]
    assert a["propuesta_cod"] == "CI.1.20"           # sin elegida: se copia
    assert b["propuesta_cod"] is None                # con elegida: no
    assert c["propuesta_cod"] is None                # otro trabajador: no


def test_f055_r36_para_con_en_curso_falso():
    r = _node("""
      marcarPropuestas(true);
      respuestas.push({en_curso: false, lineas: []});
      await disparar();
      resultado = {vivos: vivos(), en_curso: state.propuestasEnCurso,
                   repintadas};
    """, ESTADO)
    assert r == {"vivos": 0, "en_curso": False, "repintadas": 1}


def test_f055_r36_un_error_de_la_api_para_sin_romper():
    r = _node("""
      marcarPropuestas(true);
      respuestas.push(new Error("caída"));
      await disparar();
      resultado = {vivos: vivos(), en_curso: state.propuestasEnCurso};
    """, ESTADO)
    assert r == {"vivos": 0, "en_curso": False}


def test_f055_r36_un_solo_temporizador_vivo():
    r = _node("""
      marcarPropuestas(true); marcarPropuestas(true); seguirPropuestas();
      resultado = vivos();
    """, ESTADO)
    assert r == 1


def test_f055_r36_sin_en_curso_no_consulta():
    r = _node("""
      marcarPropuestas(false);
      resultado = {vivos: vivos(), en_curso: state.propuestasEnCurso};
    """, ESTADO)
    assert r == {"vivos": 0, "en_curso": False}


def test_f055_r36_cambiar_de_mes_o_empresa_corta_la_consulta():
    r = _node("""
      marcarPropuestas(true);
      const t = temporizadores[0];
      reiniciarPropuestas();
      const tras = vivos();
      respuestas.push({en_curso: true, lineas: %s});
      t.fn();                                // uno que ya iba a dispararse
      for (let i = 0; i < 20; i++) await Promise.resolve();
      resultado = {tras, vivos: vivos(), repintadas,
                   cod: state.trabajadores[0].lineas[0].propuesta_cod};
    """ % json.dumps(LINEAS), ESTADO)
    assert r == {"tras": 0, "vivos": 0, "repintadas": 0, "cod": None}


def test_f055_r36_la_fila_en_edicion_tambien_guarda_pero_no_se_repinta():
    """`aplicarPropuestas` actualiza los datos; el repintado (DOM) se salta
    la fila en edición: lo fija la comprobación estática de abajo."""
    estado = dict(ESTADO, editandoIde=14)
    r = _node("""
      aplicarPropuestas(%s);
      resultado = state.trabajadores[0].lineas[0].propuesta_cod;
    """ % json.dumps(LINEAS), estado)
    assert r == "CI.1.20"
    repintar = _plano(_funcion("repintarCeldasPartida"))
    assert "state.editandoIde" in repintar
    assert "td.celda-partida" in repintar
    assert "htmlPartida(l, state.propuestasEnCurso)" in repintar
    assert "partida_fija" in repintar


def test_f055_r36_el_cuadrante_reinicia_y_arranca():
    aplicar = _plano(_funcion("aplicarCuadrante"))
    assert "reiniciarPropuestas();" in aplicar
    assert "marcarPropuestas(datos.propuestas_en_curso);" in aplicar
    assert aplicar.index("reiniciarPropuestas();") < aplicar.index(
        "marcarPropuestas(datos.propuestas_en_curso);")
    assert aplicar.index("marcarPropuestas(") < aplicar.index("renderTabla()")


# ======================= R36 tras escribir (T13b) ======================== #
def test_f055_r36_aplicar_fila_marca_y_arranca_sin_recargar():
    fila = _plano(_funcion("aplicarFila"))
    assert "marcarPropuestas(datos.propuestas_en_curso);" in fila
    assert fila.index("marcarPropuestas(") < fila.index("renderTabla()")
    assert "cargarPeriodo" not in fila


@pytest.mark.parametrize("funcion", ["lanzarCompletar", "copiarMesAnterior"])
def test_f055_r36_completar_y_copiar_mes_marcan(funcion):
    cuerpo = _plano(_funcion(funcion))
    assert "marcarPropuestas(datos.propuestas_en_curso);" in cuerpo
    assert cuerpo.index("marcarPropuestas(") < cuerpo.index("cargarPeriodo(")


def test_f055_r36_guardar_con_en_curso_consulta_a_los_5_s_y_pinta():
    """El ciclo tras guardar: la respuesta trae `propuestas_en_curso`
    verdadero, a los 5 s se consulta y la línea nueva recibe su propuesta;
    dos escrituras seguidas, un solo temporizador; con falso, nada."""
    r = _node("""
      marcarPropuestas(true);                // guardar la fila
      marcarPropuestas(true);                // F7 enseguida
      const dos = vivos();
      respuestas.push({en_curso: false, lineas: %s});
      await disparar();
      const cod = state.trabajadores[1].lineas[0].propuesta_cod;
      marcarPropuestas(false);               // otra escritura sin cola
      resultado = {dos, cod, rutas: rutas.length, vivos: vivos()};
    """ % json.dumps([{"trabajador_ide": 10, "obra_ide": 100,
                       "es_postventa": False, **PROP}]), ESTADO)
    assert r == {"dos": 1, "cod": "CI.1.20", "rutas": 1, "vivos": 0}


def test_f055_r36_constantes():
    assert _plano(_const("INTERVALO_PROPUESTAS")) == \
        "const INTERVALO_PROPUESTAS = 5000;"
    assert "propuestasEnCurso: false," in _plano(_const("state"))
    assert "buscando" in CSS
    assert JS.count("function seguirPropuestas(") == 1


# ============ T16 · huecos que dejó la campaña de mutación del JS ========== #
def test_f055_r36_la_propuesta_va_a_su_modo_y_con_sus_tres_campos():
    """J07, J10, J35: la propuesta de la línea normal no va a la de
    postventa de la misma obra, y se copian código, descripción y método."""
    estado = dict(ESTADO, trabajadores=[_trab(14, _l(100, es_postventa=True),
                                              _l(100))])
    r = _node("""
      aplicarPropuestas(%s);
      resultado = state.trabajadores[0].lineas;
    """ % json.dumps(LINEAS[:1]), estado)
    [pv, normal] = r
    assert pv["propuesta_cod"] is None
    assert (normal["propuesta_cod"], normal["propuesta_res"],
            normal["propuesta_metodo"]) == ("CI.1.20", "JEFE DE OBRA",
                                            "parte_anterior")


def test_f055_r36_tras_reiniciar_se_puede_volver_a_consultar():
    """J15: al cambiar de mes el temporizador queda libre y el cuadrante
    nuevo arranca el suyo."""
    r = _node("""
      marcarPropuestas(true);
      reiniciarPropuestas();
      marcarPropuestas(true);
      resultado = {vivos: vivos(), timer: propuestas.timer !== null};
    """, ESTADO)
    assert r == {"vivos": 1, "timer": True}
