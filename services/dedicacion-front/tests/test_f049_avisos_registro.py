# tests/test_f049_avisos_registro.py
"""F-049 · Los avisos del modal de registro se rotulan según su tipo.

Causa (`progress/impl_F-049.md`): `pintarModalPreflight` pintaba TODOS los
conflictos del preflight con la plantilla «Pisar <hora> de <nombre>: se
borran <líneas> y se escribe <%>», sin mirar `motivo`, y el % salía de
`nueva_can`, que el transfer no publica (`asdict` no serializa la propiedad;
publica `nuevas`), así que siempre decía 0 %.

Lo que manda el transfer en cada conflicto (`Conflicto` de
`dedicacion-transfer/domain/models/registro_models.py`, serializado con
`asdict` y reenviado tal cual por la api): `motivo` (`pisado`, `sobrecarga`
o `sin_partida`), `lineas` (las que se borran, solo en el pisado),
`contexto` (en la sobrecarga, las líneas que ha contado), `nuevas` (lo que
se escribiría, con `can` en escala 0-1), `suma_existente`, `suma_total` y
`exceso` (solo en la sobrecarga, escala 0-1).

Familias (patrón de `test_f041_filtro_obra.py` / `test_f042_sugerencias.py`):

- **Lógica en node** de `rotuloConflicto` (pura, sin DOM): texto por tipo.
- **Modal en node**: el código REAL de `pintarModalPreflight` con un DOM
  mínimo; las casillas siguen llevando la `clave` de cada conflicto.
- **Estáticos** sobre `app.js`: `nueva_can` desaparece y `registroEjecutar`
  manda lo mismo que antes.

Sin `node` se saltan con su motivo; el reviewer los exige `passed`. Sin red ni
BBDD.
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


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


# ============================ ayudante node ============================== #
#: Funciones de `app.js` del rotulado: ninguna toca el DOM.
FUNCIONES_ROTULO = ("fmtPct", "pctNuevas", "rotuloConflicto")


def _node(programa: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no está instalado: los tests de lógica de F-049 "
                    "no se ejecutan")
    salida = subprocess.run([node, "-"], input=programa, capture_output=True,
                            text=True, encoding="utf-8", timeout=30,
                            check=True)
    return json.loads(salida.stdout)


def _rotulos(conflictos: list[dict]) -> list[dict]:
    """`rotuloConflicto` (código real) de cada conflicto."""
    programa = "\n".join(
        [*(_funcion(f) for f in FUNCIONES_ROTULO),
         "const cs = " + json.dumps(conflictos, ensure_ascii=False) + ";",
         "process.stdout.write(JSON.stringify(cs.map(rotuloConflicto)));"])
    return _node(programa)


# ============================ datos de prueba ============================ #
# El caso de la captura del humano (GONZALEZ PANIAGUA, 2026-09): en la 0672
# un aviso «sin partida»; en la 0694, «sin partida» y una sobrecarga (ya
# tiene MADM 95 % metida a mano en PT26/00319). Cifras de prueba, no reales.
def _nueva(rid: int, can: float, hora: str = "MADM") -> dict:
    return {"registro_id": rid, "can": can, "tot": None, "hora_codigo": hora,
            "fecha_int": 20260930, "partida_cod": None}


def _linea(ide: int, can: float, hora: str = "MADM",
           fecha: int = 20260930) -> dict:
    return {"ide": ide, "reside": 77, "fecha_int": fecha, "horide": 5,
            "hora_codigo": hora, "can": can, "tot": None, "synckey": None,
            "nuestra": False, "paride": 0}


def _conflicto(**cambios) -> dict:
    base = {"clave": "77|2026|9|5|0", "recurso_ide": 77,
            "nombre": "GONZALEZ PANIAGUA", "ano": 2026, "mes": 9,
            "parte_cod": "PT26/00319", "horide": 5, "hora_codigo": "MADM",
            "lineas": [], "contexto": [], "nuevas": [], "registros": [],
            "motivo": "pisado", "suma_existente": 0.0, "suma_total": 0.0,
            "exceso": 0.0}
    return base | cambios


SIN_PARTIDA = _conflicto(clave="sin_partida:3001", motivo="sin_partida",
                         nuevas=[_nueva(3001, 0.5)], registros=[3001])
SOBRECARGA = _conflicto(clave="sobrecarga:77|2026-09", motivo="sobrecarga",
                        contexto=[_linea(9001, 0.95)],
                        nuevas=[_nueva(3002, 0.3), _nueva(3003, 0.2)],
                        registros=[3002, 3003], suma_existente=0.95,
                        suma_total=1.45, exceso=0.45)
PISADO = _conflicto(clave="77|2026|9|5|0", motivo="pisado",
                    lineas=[_linea(8001, 0.4), _linea(8002, 0.25,
                                                      fecha=20260915)],
                    nuevas=[_nueva(3004, 0.6)], registros=[3004])


# ================================ R1 ==================================== #
def test_f049_r1_sin_partida_se_rotula_como_sin_partida():
    [r] = _rotulos([SIN_PARTIDA])
    assert r == {
        "tipo": "sin_partida", "titulo": "Sin partida",
        "detalle": ("GONZALEZ PANIAGUA, MADM 50% en el parte PT26/00319: "
                    "se escribiría sin partida de imputación. Elige una "
                    "partida en la tabla o marca la casilla para "
                    "escribirlo sin partida")}


def test_f049_r1_sobrecarga_ensena_existente_total_y_exceso():
    [r] = _rotulos([SOBRECARGA])
    assert r == {
        "tipo": "sobrecarga", "titulo": "Sobrecarga",
        "detalle": ("GONZALEZ PANIAGUA en el parte PT26/00319: ya tiene 95% "
                    "(MADM 95%), se añade 50% y sumaría 145%, un 45% por "
                    "encima de la jornada. Marca la casilla para escribirlo "
                    "igualmente")}


def test_f049_r1_sobrecarga_con_varias_lineas_contadas():
    """Mutante M19 de la campaña manual: con una sola línea contada el
    separador no se veía."""
    [r] = _rotulos([SOBRECARGA | {"contexto": [
        _linea(9001, 0.6), _linea(9002, 0.35, hora="MENC")]}])
    assert "ya tiene 95% (MADM 60%, MENC 35%), se añade 50%" in r["detalle"]


def test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo():
    [r] = _rotulos([PISADO])
    assert r == {
        "tipo": "pisado", "titulo": "Pisar",
        "detalle": ("MADM de GONZALEZ PANIAGUA en el parte PT26/00319: se "
                    "borran línea 8001 (MADM 40%, fec 20260930), línea 8002 "
                    "(MADM 25%, fec 20260915) y se escribe 60%")}


@pytest.mark.parametrize("motivo", ["", None])
def test_f049_r1_motivo_vacio_es_pisado(motivo):
    [r, ausente] = _rotulos([PISADO | {"motivo": motivo},
                             {k: v for k, v in PISADO.items()
                              if k != "motivo"}])
    assert r == ausente == _rotulos([PISADO])[0]


def test_f049_r1_motivo_desconocido_no_se_disfraza_de_pisado():
    """Un motivo nuevo del transfer no se pinta como «Pisar» (que diría que
    se borra algo): se enseña tal cual, con lo que se escribiría."""
    [r] = _rotulos([SIN_PARTIDA | {"motivo": "otro_aviso"}])
    assert r == {"tipo": "otro_aviso", "titulo": "Confirmar",
                 "detalle": ("GONZALEZ PANIAGUA, MADM 50% en el parte "
                             "PT26/00319: otro_aviso")}


def test_f049_r1_cada_tipo_con_su_texto_y_sin_el_de_los_otros():
    sp, so, pi = _rotulos([SIN_PARTIDA, SOBRECARGA, PISADO])
    assert "se borran" not in sp["detalle"] + so["detalle"]
    assert "sin partida" not in so["detalle"] + pi["detalle"]
    assert "jornada" not in sp["detalle"] + pi["detalle"]
    assert len({sp["titulo"], so["titulo"], pi["titulo"]}) == 3


def test_f049_r1_sin_nombre_ni_parte():
    """Sin `nombre` sale el `recurso_ide`; sin `parte_cod` (parte que se
    creará) no se inventa ninguno."""
    [r] = _rotulos([SIN_PARTIDA | {"nombre": None, "parte_cod": None}])
    assert r["detalle"].startswith("77, MADM 50%: se escribiría sin partida")


# ================================ R2 ==================================== #
def test_f049_r2_el_porcentaje_sale_de_nuevas_no_cero():
    """El caso de la captura: con `nuevas` de 50 % el modal decía 0 %."""
    sp, so, pi = _rotulos([SIN_PARTIDA, SOBRECARGA, PISADO])
    for r in (sp, so, pi):
        assert not re.search(r"(?<![\d,])0%", r["detalle"]), r
    assert "MADM 50%" in sp["detalle"]
    assert "se añade 50%" in so["detalle"]          # 30 % + 20 %
    assert pi["detalle"].endswith("se escribe 60%")


def test_f049_r2_decimales_y_sin_nuevas():
    con_decimales = PISADO | {"nuevas": [_nueva(1, 0.333), _nueva(2, 0.1)]}
    sin_nuevas = PISADO | {"nuevas": []}
    can_nula = PISADO | {"nuevas": [_nueva(1, None)]}
    a, b, c = _rotulos([con_decimales, sin_nuevas, can_nula])
    assert a["detalle"].endswith("se escribe 43,3%")
    assert b["detalle"].endswith("se escribe 0%")
    assert c["detalle"].endswith("se escribe 0%")


def test_f049_r2_sobrecarga_sin_contexto_no_pinta_parentesis():
    [r] = _rotulos([SOBRECARGA | {"contexto": []}])
    assert "ya tiene 95%, se añade 50%" in r["detalle"]


def test_f049_r2_el_front_no_lee_nueva_can():
    """Ningún acceso `x.nueva_can`: el campo no viaja (solo se nombra en
    el comentario que explica por qué)."""
    assert not re.search(r"\.nueva_can\b", JS)


# ================================ R3 ==================================== #
def _modal(obras: list[dict]) -> str:
    """HTML que pinta el código REAL de `pintarModalPreflight`."""
    programa = "\n".join([
        ("const MESES = ['ene','feb','mar','abr','may','jun','jul','ago',"
         "'sep','oct','nov','dic'];"),
        "const state = {anio: 2026, mes: 9};",
        ("const registro = {overrides: {}, pisar: new Set(), "
         "trabajadorIde: null};"),
        "let resultado = null;",
        "function abrirModal(html) { resultado = html; }",
        ("function escapeHtml(t) { return (t == null ? '' : String(t))"
         ".replace(/&/g,'&amp;').replace(/</g,'&lt;')"
         ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }"),
        "const document = {querySelectorAll: () => []};",
        "const $ = () => ({addEventListener() {}});",
        "function registroEjecutar() {}",
        *(_funcion(f) for f in (*FUNCIONES_ROTULO, "opcionesPartida",
                                 "pintarModalPreflight")),
        "pintarModalPreflight(" + json.dumps({"obras": obras},
                                             ensure_ascii=False) + ");",
        "process.stdout.write(JSON.stringify(resultado));"])
    return _node(programa)


def _obra(codigo: str, conflictos: list[dict]) -> dict:
    return {"obra": {"codigo": codigo, "nombre": "Obra " + codigo}, "ok": True,
            "forzada_pruebas": False, "partes": [], "acciones": [],
            "partidas_obra": [], "partidas_postventa": [],
            "conflictos": conflictos}


def test_f049_r3_las_casillas_llevan_la_clave_de_cada_conflicto():
    html = _modal([_obra("0672", [SIN_PARTIDA]),
                   _obra("0694", [SIN_PARTIDA | {"clave": "sin_partida:3005"},
                                  SOBRECARGA, PISADO])])
    valores = re.findall(r'<input type="checkbox" class="chk-pisar" '
                         r'value="([^"]*)">', html)
    assert valores == ["sin_partida:3001", "sin_partida:3005",
                       "sobrecarga:77|2026-09", "77|2026|9|5|0"]


def test_f049_r3_el_modal_pinta_el_rotulo_por_tipo():
    html = _modal([_obra("0694", [SIN_PARTIDA, SOBRECARGA, PISADO])])
    rotulos = re.findall(r'class="chk-pisar" value="[^"]*"> '
                         r"<strong>([^<]*)</strong> · ([^<]*)</label>", html)
    esperados = _rotulos([SIN_PARTIDA, SOBRECARGA, PISADO])
    assert rotulos == [(r["titulo"], r["detalle"]) for r in esperados]
    assert html.count("Pisar") == 1


def test_f049_r3_el_rotulo_se_escapa():
    html = _modal([_obra("0694", [SIN_PARTIDA | {"nombre": "A<b>&C"}])])
    assert "A&lt;b&gt;&amp;C" in html
    assert "A<b>" not in html


def test_f049_r3_ejecutar_manda_las_mismas_claves():
    """`registroEjecutar` no cambia: recoge el `value` de las casillas
    marcadas y lo manda como `pisar_claves`."""
    ejecutar = _plano(_funcion("registroEjecutar"))
    assert ('const pisar = [...document.querySelectorAll(".chk-pisar:checked")]'
            " .map((c) => c.value);") in ejecutar
    assert "pisar_claves: pisar, overrides: registro.overrides," in ejecutar


def test_f049_r3_el_rotulo_no_decide_nada():
    """El rotulado solo formatea lo que manda el preflight: ni compara con la
    jornada ni filtra conflictos."""
    rotulo = _plano(_funcion("rotuloConflicto") + _funcion("pctNuevas"))
    assert not re.search(r"[<>]=?\s*1\b|LIMITE|filter\(", rotulo), rotulo
