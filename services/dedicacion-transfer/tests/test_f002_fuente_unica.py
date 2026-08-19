# tests/test_f002_fuente_unica.py
"""F-002 · Las reglas se enuncian en UN solo sitio (R1-R5).

Test documental: no ejecuta código del servicio, lee ficheros del
repositorio. La avería que vigila es la que dio origen a la feature — la
misma regla contada con palabras distintas en cinco sitios, dos de ellos
contradiciéndose— y no la caza ningún test de comportamiento, porque los
docstrings no se ejecutan.

Solo I/O de ficheros locales: ni red, ni BBDD.

Lo que todavía NO se puede cerrar (los enunciados de P4 y P5, y la línea de
procedencia de Administración) está aquí como `xfail(strict=True)`: si algún
día pasa sin que nadie lo espere, el test lo dice en vez de callarse.
"""
from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
README = RAIZ / "services" / "dedicacion-transfer" / "README.md"
REGLAS = (RAIZ / "services" / "dedicacion-transfer" / "application" /
          "services" / "reglas_porcentajes.py")
RESOLVER = (RAIZ / "services" / "dedicacion-transfer" / "application" /
            "services" / "partida_resolver.py")
PIPELINE = (RAIZ / "services" / "dedicacion-transfer" / "application" /
            "pipelines" / "registro_pipeline.py")

#: Anclas que el resto del repositorio puede enlazar. Son el contrato de la
#: fuente única: sin ellas, remitir obliga a copiar el texto otra vez.
ANCLAS = ("regla-p1", "regla-p2", "regla-p3", "regla-p4", "regla-p5",
          "regla-conflicto", "regla-pruebas")

#: Ficheros de producción donde vive el código de la obra de postventa como
#: literal. Fuera de aquí se cita el ajuste, no el valor (R5).
FUENTES_SIN_LITERAL = (REGLAS, RESOLVER, PIPELINE)

#: Frases que la fase 1 de F-002 retira. Fichero -> frases que ya no puede
#: contener. Las de P4 y P5 están más abajo, en el test `xfail`: se retiran
#: en T12, cuando Administración conteste.
PROHIBIDAS_HOY: dict[Path, tuple[str, ...]] = {
    README: (
        "**P1** Solo recursos con código de hora",
        "**P2** La línea va SIEMPRE al",
        "**P3** `can` = porcentaje",
    ),
    REGLAS: (
        "postventa-2",
    ),
}

#: Las que esperan a la respuesta de Administración (T12).
PROHIBIDAS_TRAS_D1_D2: dict[Path, tuple[str, ...]] = {
    README: (
        "choca aunque tenga otra partida",
    ),
    REGLAS: (
        "la misma partida en ese parte",
        "imputando al CAPÍTULO",
    ),
}


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _plano(ruta: Path) -> str:
    """El texto con los espacios colapsados.

    Las frases prohibidas se buscan aquí y no en el texto crudo: un
    docstring reajustado parte la frase en dos líneas y la haría invisible
    para el test sin haber retirado nada."""
    return " ".join(_texto(ruta).split())


def test_f002_r1_el_arbol_es_el_que_creemos():
    """Guardarraíl: si la raíz se resolviera mal, todo lo de abajo pasaría
    leyendo ficheros vacíos y nadie se enteraría."""
    assert ARQUITECTURA.is_file(), ARQUITECTURA
    assert README.is_file() and REGLAS.is_file()
    assert "Semántica de dominio imprescindible" in _texto(ARQUITECTURA)


# ------------------------- R1 · fuente única ----------------------- #

@pytest.mark.parametrize("ancla", ANCLAS)
def test_f002_r1_fuente_unica_tiene_ancla_por_regla(ancla):
    """R1 · Cada regla tiene un ancla estable en `docs/ARCHITECTURE.md`."""
    texto = _texto(ARQUITECTURA)
    assert f'<a id="{ancla}"></a>' in texto, ancla


@pytest.mark.parametrize("ancla", ANCLAS)
def test_f002_r1_fuente_unica_el_ancla_no_esta_repetida(ancla):
    """R1 · Un ancla duplicada es una regla enunciada dos veces con otro
    nombre: el navegador salta a la primera y la segunda queda muerta."""
    assert _texto(ARQUITECTURA).count(f'<a id="{ancla}"></a>') == 1, ancla


MARCA_PENDIENTE = "PENDIENTE · decisión D1/D2 de F-002"


def _punto(numero: int) -> str:
    """El texto del punto N de «Semántica de dominio imprescindible»."""
    texto = _texto(ARQUITECTURA)
    inicio = texto.index(f"\n{numero}. ")
    try:
        fin = texto.index(f"\n{numero + 1}. ", inicio)
    except ValueError:
        fin = len(texto)
    return texto[inicio:fin]


@pytest.mark.parametrize("numero", (6,))
def test_f002_r1_los_puntos_sin_cerrar_estan_marcados(numero):
    """R1 · Mientras D2 siga sin escribirse, el punto 6 lo dice con esas
    palabras. Una regla provisional que parece firme es peor que una marcada
    como pendiente. (D1 se cerró en T7: el punto 5 ya no la lleva.)"""
    assert MARCA_PENDIENTE in _punto(numero), numero


@pytest.mark.parametrize("numero", (1, 2, 3, 4, 5, 7))
def test_f002_r1_los_puntos_cerrados_no_estan_marcados(numero):
    """R1 · Y los que sí están validados NO llevan la marca: si la llevaran
    todos, la marca no diría nada."""
    assert MARCA_PENDIENTE not in _punto(numero), numero


# ---------------------- R2 · el resto remite ----------------------- #

@pytest.mark.parametrize("ancla", ("regla-p1", "regla-p2", "regla-p3"))
def test_f002_r2_el_readme_remite_a_las_anclas(ancla):
    """R2 · El README enlaza P1-P3 en vez de reenunciarlas."""
    assert f"ARCHITECTURE.md#{ancla}" in _texto(README), ancla


@pytest.mark.xfail(strict=True, reason="T12: espera a D1/D2")
def test_f002_r2_los_docstrings_remiten_p4_p5():
    """R2 · Los docstrings de P4 y P5 remitirán también. Hoy reenuncian."""
    assert "ARCHITECTURE.md#regla-p5" in _texto(REGLAS)
    assert "ARCHITECTURE.md#regla-conflicto" in _texto(REGLAS)


# ------------------- R3 · nadie reenuncia la regla ----------------- #

@pytest.mark.parametrize("ruta, frase", [
    (ruta, frase) for ruta, frases in PROHIBIDAS_HOY.items()
    for frase in frases
])
def test_f002_r3_frases_prohibidas_fase1(ruta, frase):
    """R3 · La frase se retiró de donde la duplicaba. Si vuelve, la suite
    cae: es la única forma de que una duplicación no se cuele en una
    revisión de diff."""
    assert frase not in _plano(ruta), f"{ruta.name}: {frase!r}"


@pytest.mark.xfail(strict=True, reason="T12: espera a D1/D2")
@pytest.mark.parametrize("ruta, frase", [
    (ruta, frase) for ruta, frases in PROHIBIDAS_TRAS_D1_D2.items()
    for frase in frases
])
def test_f002_r3_frases_prohibidas_p4_p5(ruta, frase):
    assert frase not in _plano(ruta), f"{ruta.name}: {frase!r}"


def test_f002_r3_la_fuente_si_puede_enunciarla():
    """R3 · Control positivo: la prohibición es «no lo repitas fuera», no
    «no lo digas». `docs/ARCHITECTURE.md` sigue enunciando las reglas."""
    texto = _texto(ARQUITECTURA)
    assert "último día del mes" in texto
    assert "código de hora" in texto


# ------------------ R4 · de quién sale y cuándo -------------------- #

#: Formato de la línea de procedencia. Lo que R4 exige es que se sepa
#: **quién** confirmó la regla y **cuándo**, más el respaldo detrás del «·».
#: El patrón NO fija el interlocutor: la v1 de la spec daba por hecho que
#: sería Administración, y D1/D2 acabó decidiéndolas el responsable del
#: proyecto con lecturas reales contra Sigrid. Clavar «Administración» en el
#: test obligaría a escribir una procedencia falsa para ponerlo en verde,
#: que es exactamente lo contrario de lo que este requisito persigue.
#: Se busca sobre el texto con los espacios colapsados (`_plano`), como las
#: frases prohibidas: una línea de procedencia partida en dos por el ajuste
#: del párrafo es la misma procedencia, y no puede hacer fallar al test.
PATRON_PROCEDENCIA = r"Confirmado por [^·]{3,120} el \d{4}-\d{2}-\d{2} · \S+"

#: Anclas de las reglas que F-002 decide y que, por tanto, tienen que llevar
#: su procedencia. Se comprueba **bloque a bloque**, no contando apariciones
#: en el documento entero: dos líneas de procedencia en la misma regla no
#: pueden hacer pasar por confirmada a la de al lado.
#: La lista crece con las reglas que se van cerrando: `regla-conflicto` y
#: `regla-capacidad` entran con T8, que es cuando D2 se escribe.
ANCLAS_CON_PROCEDENCIA = ("regla-p5",)


def _bloque(ancla: str) -> str:
    """El texto que va de un ancla a la siguiente (o al final), aplanado."""
    texto = _plano(ARQUITECTURA)
    inicio = texto.index(f'<a id="{ancla}"></a>')
    fin = texto.find('<a id="', inicio + 1)
    return texto[inicio:fin if fin != -1 else len(texto)]


@pytest.mark.parametrize("ancla", ANCLAS_CON_PROCEDENCIA)
def test_f002_r4_procedencia_fechada(ancla):
    """R4 · Cada regla confirmada dice quién la confirmó y cuándo."""
    import re
    assert re.search(PATRON_PROCEDENCIA, _bloque(ancla)), ancla


def test_f002_r4_la_procedencia_no_es_anonima():
    """R4 · Control: «Confirmado el 2026-08-19» a secas no vale. Una regla
    sin interlocutor no se le puede repreguntar a nadie."""
    import re
    assert re.search(PATRON_PROCEDENCIA, "Confirmado por  el 2026-08-19 · x") \
        is None
    assert re.search(PATRON_PROCEDENCIA,
                     "Confirmado por Fulano el 2026-08-19") is None


# ------------- R5 · el valor del ajuste vive en el .env ------------ #

@pytest.mark.parametrize("ruta", FUENTES_SIN_LITERAL,
                         ids=lambda r: r.name)
def test_f002_r5_sin_literal_de_la_obra_de_postventa(ruta):
    """R5 · Ni docstrings ni comentarios citan el código de la obra: dicen
    `POSTVENTA_OBRA_COD`. Un literal repetido por el árbol es una segunda
    configuración que nadie actualiza cuando cambia la de verdad."""
    texto = _texto(ruta)
    assert "POSTV2" not in texto, ruta.name
    assert "POSTVENTA_OBRA_COD" in texto, ruta.name


def test_f002_r5_el_valor_sigue_estando_donde_debe():
    """R5 · Control positivo: quitarlo de los docstrings no es quitarlo del
    servicio. El defecto sigue en `config/settings.py` y en `.env.example`."""
    ajustes = (RAIZ / "services" / "dedicacion-transfer" / "config" /
               "settings.py")
    ejemplo = RAIZ / "services" / "dedicacion-transfer" / ".env.example"
    assert "POSTVENTA_OBRA_COD" in _texto(ajustes)
    assert "POSTVENTA_OBRA_COD" in _texto(ejemplo)
