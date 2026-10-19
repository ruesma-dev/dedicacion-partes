# tests/test_f057_buscando_pendientes.py
"""F-057 · «buscando partida…» solo en las líneas que la API da por
pendientes.

- r1: la celda Partida de una línea sin elegida ni propuesta dice «buscando
  partida…» solo si `l.propuesta_pendiente` (lo pone la API); si no,
  «automática», aunque haya propuestas en curso en el mes (la de postventa,
  la de la memoria «sin propuesta»).
- r1: cada consulta de 5 s copia la lista `pendientes` de `GET
  …/propuestas` a las marcas de las líneas (por trabajador, obra y modo) y
  repinta: la que llega a tener propuesta la enseña sin recargar y la que
  sale de la cola deja de decir «buscando partida…».
- r2: el front no decide qué está pendiente: no mira el global
  `propuestasEnCurso` para pintar (ese solo gobierna el sondeo) ni la
  partida, la fija o la postventa para marcar.

El código REAL de `static/js/app.js` en `node`, con temporizador y `api`
falsos (el entorno de F-055); lo que toca el DOM, comprobado en estático.
Sin `node`, los de lógica se saltan con su motivo (el reviewer los exige
`passed`).
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from tests.test_f050_subfilas import _const, _funcion, _plano
from tests.test_f055_propuesta_celda import CONSTS, ENTORNO, FUNCIONES, PROP, _l

FUNCIONES_F057 = [*FUNCIONES, "aplicarPendientes"]

BUSCANDO = '<span class="partida-auto buscando">buscando partida…</span>'
AUTOMATICA = '<span class="partida-auto">automática</span>'


def _node(cuerpo: str, estado: dict) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-057 "
                    "no se ejecutan")
    programa = "\n".join(
        [*(_const(c) for c in CONSTS),
         *(_funcion(f) for f in FUNCIONES_F057),
         ENTORNO, "var state = " + json.dumps(estado, ensure_ascii=False)
         + ";", "(async () => { var resultado;", cuerpo,
         "process.stdout.write(JSON.stringify(resultado)); })();"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


# ============================ r1 · la celda =============================== #
@pytest.mark.parametrize("linea, en_curso, esperado", [
    (_l(1, propuesta_pendiente=True), True, BUSCANDO),
    (_l(1, propuesta_pendiente=False), True, AUTOMATICA),
    (_l(1, es_postventa=True), True, AUTOMATICA),
    (_l(1), True, AUTOMATICA),
    (_l(1, propuesta_pendiente=True), False, BUSCANDO),
], ids=["pendiente", "no_pendiente_con_cola", "postventa_con_cola",
        "sin_marca_con_cola", "pendiente_sin_global"])
def test_f057_r1_buscando_solo_si_la_linea_es_pendiente(linea, en_curso,
                                                       esperado):
    """El global `propuestasEnCurso` no cuenta: manda la marca de la línea."""
    r = _node(f"state.propuestasEnCurso = {json.dumps(en_curso)};"
              f"resultado = htmlPartida({json.dumps(linea)});", {})
    assert r == esperado


def test_f057_r1_la_propuesta_y_la_elegida_mandan_sobre_la_marca():
    r = _node(f"""
      resultado = [
        htmlPartida({json.dumps(_l(1, propuesta_pendiente=True, **PROP))}),
        htmlPartida({json.dumps(_l(1, propuesta_pendiente=True,
                                   partida_ide=7, partida_cod="CI.1.9",
                                   partida_res="ADM"))})];
    """, {})
    assert r[0].startswith('<em class="partida-propuesta"')
    assert r[1] == '<span class="partida-elegida">CI.1.9 · ADM</span>'


# =================== r1 · el sondeo actualiza las marcas ================== #
def _trab(ide, *lineas):
    return {"ide": ide, "lineas": list(lineas)}


ESTADO = {"anio": 2026, "mes": 9, "editandoIde": None,
          "propuestasEnCurso": False,
          "trabajadores": [
              _trab(14, _l(100, propuesta_pendiente=True),
                    _l(100, es_postventa=True),
                    _l(101, propuesta_pendiente=True)),
              _trab(10, _l(100, propuesta_pendiente=True))]}


def _pend(t, o, pv=False):
    return {"trabajador_ide": t, "obra_ide": o, "es_postventa": pv}


def _marcas(r):
    return [[ln.get("propuesta_pendiente") for ln in t["lineas"]]
            for t in r["trabajadores"]]


def test_f057_r1_aplicar_pendientes_marca_por_identidad():
    r = _node("""
      aplicarPendientes(__P__);
      resultado = {trabajadores: state.trabajadores};
    """.replace("__P__", json.dumps([_pend(14, 100), _pend(99, 101)])),
        ESTADO)
    # La normal de la 100 sí; la de postventa de la misma obra, no; la 101
    # sale de la cola; la del otro trabajador, también.
    assert _marcas(r) == [[True, False, False], [False]]


def test_f057_r1_cada_consulta_actualiza_las_marcas_y_repinta():
    """Primera consulta: la 101 de Eva ya tiene propuesta y sale de la cola;
    segunda: la cola se vacía y nada dice «buscando partida…»."""
    r = _node("""
      marcarPropuestas(true);
      respuestas.push({en_curso: true, pendientes: __P1__, lineas: __L__});
      await disparar();
      const primera = state.trabajadores.map((t) => t.lineas.map(
        (l) => l.propuesta_pendiente));
      const celda101 = htmlPartida(state.trabajadores[0].lineas[2]);
      respuestas.push({en_curso: false, pendientes: [], lineas: []});
      await disparar();
      resultado = {primera, celda101, repintadas, vivos: vivos(),
                   trabajadores: state.trabajadores};
    """.replace("__P1__", json.dumps([_pend(14, 100), _pend(10, 100)]))
        .replace("__L__", json.dumps([{**_pend(14, 101), **PROP}])), ESTADO)
    assert r["primera"] == [[True, False, False], [True]]
    assert r["celda101"].startswith('<em class="partida-propuesta"')
    assert _marcas(r) == [[False, False, False], [False]]
    assert r["repintadas"] == 2 and r["vivos"] == 0


def test_f057_r1_si_la_consulta_falla_nada_queda_buscando():
    """La API no contesta: el sondeo para (F-055) y ninguna línea se queda
    diciendo «buscando partida…» sin nadie que la vaya a actualizar."""
    r = _node("""
      marcarPropuestas(true);
      respuestas.push(new Error("caída"));
      await disparar();
      resultado = {trabajadores: state.trabajadores, vivos: vivos()};
    """, ESTADO)
    assert _marcas(r) == [[False, False, False], [False]] and r["vivos"] == 0


def test_f057_r1_una_respuesta_sin_lista_vacia_las_marcas():
    """Una api anterior a F-057 (sin `pendientes`): ninguna marca."""
    r = _node("""
      marcarPropuestas(true);
      respuestas.push({en_curso: true, lineas: []});
      await disparar();
      resultado = {trabajadores: state.trabajadores};
    """, ESTADO)
    assert _marcas(r) == [[False, False, False], [False]]


# ================== r2 · el front pinta, no decide ======================== #
def test_f057_r2_html_partida_no_mira_el_global_ni_decide():
    cuerpo = _plano(_funcion("htmlPartida"))
    assert cuerpo.startswith("function htmlPartida(l) {")
    assert "propuestasEnCurso" not in cuerpo
    assert "l.propuesta_pendiente" in cuerpo


def test_f057_r2_aplicar_pendientes_solo_casa_identidades():
    cuerpo = _plano(_funcion("aplicarPendientes"))
    for campo in ("partida_ide", "partida_fija", "propuesta_cod",
                  "propuestasEnCurso"):
        assert campo not in cuerpo
    assert "p.es_postventa === l.es_postventa" in cuerpo


def test_f057_r1_la_celda_y_el_repintado_usan_la_marca():
    celda = _plano(_funcion("construirCelda"))
    repintar = _plano(_funcion("repintarCeldasPartida"))
    assert "td.innerHTML = htmlPartida(l);" in celda
    assert "propuestasEnCurso" not in celda
    assert "td.innerHTML = htmlPartida(l);" in repintar
    assert "propuestasEnCurso" not in repintar


def test_f057_r1_la_consulta_aplica_pendientes_antes_de_repintar():
    consulta = _plano(_funcion("consultarPropuestas"))
    assert "aplicarPendientes((datos && datos.pendientes) || []);" in consulta
    assert consulta.index("aplicarPendientes(") < consulta.index(
        "repintarCeldasPartida()")
    # El sondeo lo sigue gobernando `en_curso`.
    assert "state.propuestasEnCurso = !!(datos && datos.en_curso);" in \
        consulta
