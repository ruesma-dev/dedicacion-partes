# tests/test_f050_selector_partida.py
"""F-050 · El selector de partida (R25-R27): desplegable con buscador y
botones Todas · CD · CI · CP, colgado de `<body>`, que guarda con
`PUT …/partida` y repinta la fila.

El filtrado, el orden de la lista y los rótulos son funciones puras que se
ejecutan en `node` con el código REAL de `app.js`; el montaje en el DOM se
comprueba de forma ESTÁTICA (patrón de F-029 y F-042). Sin `node`, los de
lógica se saltan con su motivo; el reviewer los exige `passed`. Sin red.
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
CSS = (RAIZ / "static" / "css" / "styles.css").read_text(encoding="utf-8")


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


PURAS = ("normalizar", "filtrarPartidas", "listaSelector", "rotuloOrigen")


def _node(cuerpo: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-050 "
                    "no se ejecutan")
    programa = "\n".join([*(_funcion(f) for f in PURAS), "var resultado;",
                          cuerpo,
                          "process.stdout.write(JSON.stringify(resultado));"])
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


def _p(ide, cod, res, mayor, categoria="CI"):
    return {"ide": ide, "cod": cod, "res": res, "mayor": mayor,
            "categoria": categoria}


PARTIDAS = [
    _p(1, "01.19.03.20", "Partida proporcional de medios", "CD", "CP"),
    _p(2, "1.4.1.8", "Costes indirectos de estructura", "CD", "CI"),
    _p(3, "CI.1.5", "JEFE DE OBRA", "CI"),
    _p(4, "CI.1.9", "Administrativo", "CI"),
    _p(5, "CI.1.10", "Jefe de grupo (Pérez)", "CI"),
    _p(6, "CP.1", "Seguros", "CP"),
    _p(7, "CP.12", "Seguridad y salud", "CP"),
    _p(8, "656", "33+34 VIVIENDAS", "OTRO", "OTRO"),
]


def _filtrar(casos) -> list:
    return _node("const P = " + json.dumps(PARTIDAS) + ";\nresultado = " +
                 json.dumps(casos) + ".map(([t, m]) => filtrarPartidas(P, "
                 "t, m).map((p) => p.ide));")


# ================================ R26 ==================================== #
def test_f050_r26_filtra_sin_mayusculas_ni_tildes():
    assert _filtrar([["jefe", None], ["JÉFE", None], ["jéfe de", None],
                     ["perez", None], ["ci.1.1", None]]) == [
        [3, 5], [3, 5], [3, 5], [5], [5]]


def test_f050_r26_todas_las_palabras_en_codigo_y_descripcion():
    assert _filtrar([["ci jefe", None], ["jefe obra", None],
                     ["obra grupo", None], ["  ", None], ["", None]]) == [
        [3, 5], [3], [], [1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7, 8]]


def test_f050_r26_cada_boton_filtra_por_su_mayor():
    assert _filtrar([["", "CD"], ["", "CI"], ["", "CP"], ["", None],
                     ["seg", "CP"], ["seg", "CI"]]) == [
        [1, 2], [3, 4, 5], [6, 7], [1, 2, 3, 4, 5, 6, 7, 8], [6, 7], []]


def test_f050_r26_otro_solo_en_todas():
    assert _filtrar([["656", None], ["656", "CD"], ["656", "CI"],
                     ["656", "CP"]]) == [[8], [], [], []]


def test_f050_r26_el_front_no_clasifica_por_categoria():
    """El mayor lo manda el transfer: ni `categoria` ni prefijos de código."""
    for f in ("filtrarPartidas", "listaSelector"):
        cuerpo = _funcion(f)
        assert "categoria" not in cuerpo, f
        assert not re.search(r"[\"'](CD|CI|CP)", cuerpo), f


def test_f050_r26_sin_catalogo_lista_vacia():
    assert _node("resultado = filtrarPartidas(undefined, 'x', null);") == []


def _lista(texto, mayor, propuesta) -> list:
    resp = {"partidas": PARTIDAS, "propuesta": propuesta}
    return _node("resultado = listaSelector(" + json.dumps(resp) + ", " +
                 json.dumps(texto) + ", " + json.dumps(mayor) +
                 ").map((p) => [p.ide, p.propuesta]);")


PROP = {"paride": 4, "cod": "CI.1.9", "res": "Administrativo",
        "metodo": "parte_anterior", "origen": "parte PT26/00319"}


def test_f050_r26_propuesta_primera_sin_repetir():
    assert _lista("", "CI", PROP) == [[4, True], [3, False], [5, False]]
    assert _lista("", None, PROP)[:2] == [[4, True], [1, False]]
    assert [i for i, _ in _lista("", None, PROP)].count(4) == 1


def test_f050_r26_propuesta_que_no_pasa_el_filtro_no_sale():
    assert _lista("jefe", None, PROP) == [[3, False], [5, False]]
    assert _lista("", "CP", PROP) == [[6, False], [7, False]]


def test_f050_r26_sin_propuesta_el_orden_de_la_api():
    assert _lista("", "CD", None) == [[1, False], [2, False]]


def test_f050_r6_r26_rotulo_del_origen():
    assert _node(
        "resultado = [rotuloOrigen('parte_anterior', 'parte PT26/1 · "
        "09/2026 · obra 0694'), rotuloOrigen('ultimo_parte', 'parte X'), "
        "rotuloOrigen('auto_nombre', null), rotuloOrigen('auto_categoria'),"
        " rotuloOrigen('postventa'), rotuloOrigen('var'), "
        "rotuloOrigen('manual'), rotuloOrigen(null), rotuloOrigen('otro')];"
    ) == ["parte anterior: parte PT26/1 · 09/2026 · obra 0694",
          "último parte: parte X", "casada por nombre",
          "casada por categoría", "obra de postventa", "partida fija",
          "elegida", "", "otro"]


# ============================ R25 · montaje ============================== #
def test_f050_r25_guarda_el_editor_antes_y_pide_la_api_con_cache():
    abrir = _plano(_funcion("abrirSelectorPartida"))
    assert abrir.startswith("async function abrirSelectorPartida("
                            "trabajadorIde, obraIde, esPostventa, ancla, "
                            "despues) {")
    assert ("if (state.editandoIde === trabajadorIde) await guardarAhora();"
            ) in abrir
    assert ("`/periodos/${state.anio}/${state.mes}/trabajadores/"
            "${trabajadorIde}/partidas?obra_ide=${obraIde}"
            "&es_postventa=${esPostventa}`") in abrir
    assert "let resp = selector.cache.get(clave);" in abrir
    assert "selector.cache.set(clave, resp);" in abrir
    assert "toast(err.message, true);" in abrir
    assert abrir.index("guardarAhora()") < abrir.index("api(")


def test_f050_r25_la_cache_se_vacia_al_cargar_el_cuadrante():
    assert "selector.cache.clear();" in _plano(_funcion("aplicarCuadrante"))
    clave = _plano(_funcion("clavePartidas"))
    for trozo in ("state.anio", "state.mes", "state.empresa",
                  "trabajadorIde", "obraIde", "esPostventa"):
        assert trozo in clave, trozo


def test_f050_r26_panel_colgado_de_body_y_sobre_el_modal():
    montar = _plano(_funcion("montarSelectorPartida"))
    assert "document.body.appendChild(panel);" in montar
    assert 'panel.className = "panel-partida";' in montar
    regla = re.search(r"\.panel-partida\s*\{([^}]*)\}", CSS)
    assert regla and "position: fixed;" in regla.group(1)
    z = int(re.search(r"z-index:\s*(\d+)", regla.group(1)).group(1))
    assert z > 60          # `.modal-overlay` es 60
    assert "posicionSugerencias(" in montar


def test_f050_r26_botones_todas_cd_ci_cp_y_empieza_en_el_ambito():
    montar = _plano(_funcion("montarSelectorPartida"))
    assert '["", "CD", "CI", "CP"]' in montar
    assert '${m || "Todas"}' in montar
    assert "let mayor = resp.ambito || null;" in montar
    assert ('b.addEventListener("mousedown", (ev) => { ev.preventDefault(); '
            "mayor = b.dataset.mayor || null; activa = 0; pintar(); });"
            ) in montar
    assert 'b.classList.toggle("on", (b.dataset.mayor || null) === mayor)' \
        in montar


def test_f050_r26_sin_resultados_y_opcion_automatica():
    montar = _plano(_funcion("montarSelectorPartida"))
    assert "Sin partidas con ese filtro" in montar
    assert "{ automatica: true }" in montar
    assert ("const partida = op.automatica ? null : { ide: op.ide, cod: "
            "op.cod, res: op.res };") in montar
    assert "rotuloOrigen(resp.propuesta.metodo, resp.propuesta.origen)" \
        in montar


def test_f050_r26_teclas_propias_que_no_llegan_a_teclas():
    montar = _plano(_funcion("montarSelectorPartida"))
    teclado = montar.split('input.addEventListener("keydown", (ev) => {')[1]
    assert teclado.strip().startswith("ev.stopPropagation();")
    for trozo in ('ev.key === "ArrowDown"', 'ev.key === "ArrowUp"',
                  'ev.key === "Enter"', 'ev.key === "Escape"'):
        assert trozo in teclado, trozo
    assert "elegir(opciones[activa]);" in teclado
    assert 'input.addEventListener("input", () => { activa = 0; pintar(); ' \
        '});' in montar


# ================================ R27 ==================================== #
def test_f050_r27_elegir_guarda_y_repinta_con_la_respuesta():
    montar = _plano(_funcion("montarSelectorPartida"))
    elegir = montar.split("const elegir = async (op) => {")[1]
    assert ("`/periodos/${state.anio}/${state.mes}/trabajadores/"
            "${ctx.trabajadorIde}/partida`") in elegir
    assert ('{ method: "PUT", body: JSON.stringify({ obra_ide: ctx.obraIde,'
            " es_postventa: ctx.esPostventa, partida }) }") in elegir
    assert elegir.index("selector.cache.delete(ctx.clave);") < \
        elegir.index("aplicarFila(datos);") < elegir.index(
            "if (ctx.despues) ctx.despues();")


def test_f050_r27_el_front_no_decide_la_partida():
    for f in ("abrirSelectorPartida", "montarSelectorPartida"):
        cuerpo = _funcion(f)
        assert "resolver" not in cuerpo and "categoria" not in cuerpo, f


def test_f050_r26_css_del_panel():
    for regla in (r"\.panel-partida \.mayores button\.on",
                  r"\.panel-partida \.opcion\.activa",
                  r"\.panel-partida \.opcion\.propuesta"):
        assert re.search(regla + r"\s*[,{]", CSS), regla
