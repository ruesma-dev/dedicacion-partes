# tests/test_f025_casado_p5.py
"""F-025 · El casado de P5 sin escalones ajenos (R10-R11, D2 = B, D8 = A).

La regla es `docs/ARCHITECTURE.md#regla-p5`. Lo que se vigila: la línea de
postventa de una obra solo casa con la partida de su código EXACTO o, sin
ella, con la que empieza por ese código seguido SOLO de letras (la más corta
y, a igualdad, la menor). Fuera el código en la descripción y el nombre, que
casaban `OT` con `CI.7.5` y `191105` con `0611`; y fuera el prefijo seguido
de otra cosa, que casaba `CP` con `CP.1` (y la obra-capítulo con su hija).

Sin red ni BBDD: catálogos construidos aquí y dobles de `conftest.py`.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.partida_resolver import (
    construir_catalogo,
    resolver_postventa,
)
from domain.models.registro_models import ObraEntrada

from tests.conftest import PRESUPUESTOS_PV, ClienteFalso, SettingsFalso, _fila, linea


def _catalogo(*codigos: str, res: str = "PARTIDA"):
    """Hojas activas colgando de `CD`, una por código, con ides 1, 2…"""
    filas = [_fila(100, 0, 0, "CD", "COSTES DIRECTOS")]
    filas += [_fila(i, 100, i, cod, f"{res} {cod}")
              for i, cod in enumerate(codigos, start=1)]
    return construir_catalogo(filas)


def _cod(nodos, codigo, nombre=None):
    nodo = resolver_postventa(nodos, codigo, nombre)
    return None if nodo is None else nodo.cod


# ------------------------------ R10 ------------------------------------ #

def test_f025_r10_el_exacto_gana_al_sufijo_de_letra():
    """R10 · Con código exacto no se mira el prefijo."""
    assert _cod(_catalogo("0578B", "0578"), "0578") == "0578"


def test_f025_r10_sin_exacto_casa_el_sufijo_de_letra():
    """R10 · `0578` (CERRADA) casa con `0578B`: caso real del data mart."""
    assert _cod(_catalogo("0578B", "0656"), "0578") == "0578B"


def test_f025_r10_el_guion_no_cuenta_como_sufijo():
    """R10 · `0654` casa con `0654-B`: el código normalizado quita el guion,
    así que lo que queda detrás es solo la letra. Caso real."""
    assert _cod(_catalogo("0654-B"), "0654") == "0654-B"


def test_f025_r10_entre_sufijos_gana_el_mas_corto():
    """R10 · Dos sufijos de letra: el más corto, aunque el otro sea menor."""
    assert _cod(_catalogo("0578AB", "0578C"), "0578") == "0578C"


def test_f025_r10_a_igual_longitud_gana_el_menor_normalizado():
    """R10 · A igual longitud, el menor código NORMALIZADO, no el crudo:
    `0578-C` va antes que `0578B` en crudo (el guion es menor que la letra)
    y después normalizado (`0578C` > `0578B`)."""
    nodos = _catalogo("0578-C", "0578B")
    assert sorted(n.cod for n in nodos.values() if n.es_hoja) == [
        "0578-C", "0578B"], "control: en crudo va antes 0578-C"
    assert _cod(nodos, "0578") == "0578B"


def test_f025_r10_el_desempate_no_depende_del_orden_de_las_filas():
    """R10 · El mismo catálogo en orden inverso elige la misma."""
    directo = _catalogo("0578C", "0578B")
    inverso = _catalogo("0578B", "0578C")
    assert _cod(directo, "0578") == _cod(inverso, "0578") == "0578B"


def test_f025_r10_el_codigo_se_compara_normalizado():
    """R10 · Mayúsculas y espacios no cuentan (como el exacto de siempre)."""
    assert _cod(_catalogo("0578B"), " 0578 ") == "0578B"
    assert _cod(_catalogo("CPB"), "cp") == "CPB"


# ------------------------------ R11 ------------------------------------ #

@pytest.mark.parametrize("partida, obra", [
    ("CP.1", "CP"),           # capítulo de costes proporcionales (D2)
    ("0678.MO", "0678"),      # obra-capítulo con su hija (D8 = A)
    ("06561", "0656"),        # prefijo seguido de dígito
    ("0578B1", "0578"),       # letras y luego un dígito
    ("0578 B.", "0578"),      # letra y luego un punto
], ids=["punto", "obra-capitulo", "digito", "letra-digito", "letra-punto"])
def test_f025_r11_prefijo_seguido_de_algo_que_no_son_letras(partida, obra):
    """R11 · Prefijo seguido de cualquier cosa que no sean SOLO letras: no
    casa."""
    assert _cod(_catalogo(partida), obra) is None


def test_f025_r11_el_codigo_en_la_descripcion_no_casa():
    """R11 · `OT` (EN ESTUDIO) ya no casa con `CI.7.5` por su descripción."""
    nodos = _catalogo("CI.7.5", res="OT")
    assert "OT CI.7.5" in [n.res for n in nodos.values()]
    assert _cod(nodos, "OT") is None


def test_f025_r11_el_nombre_no_casa():
    """R11 · `191105` ya no casa con `0611` por el nombre de la obra."""
    nodos = construir_catalogo([
        _fila(100, 0, 0, "CD", "COSTES DIRECTOS"),
        _fila(1, 100, 1, "0611", "RESIDENCIA LOS OLIVOS")])
    assert _cod(nodos, "191105", "RESIDENCIA LOS OLIVOS") is None
    assert _cod(nodos, None, "RESIDENCIA LOS OLIVOS") is None


def test_f025_r11_sin_codigo_no_casa():
    """R11 · Sin código no hay casado: el nombre ya no es un escalón."""
    assert _cod(_catalogo("0578B"), None, "0578B") is None
    assert _cod(_catalogo("0578B"), "", "0578B") is None


def test_f025_r11_la_obra_capitulo_no_casa_con_el_presupuesto_capitulos():
    """R11 · D8 = A sobre la fixture `capitulos` de F-002: `0678` es un
    capítulo con `0678.MO` y `0678.MAT` debajo; no casa con ninguna."""
    nodos = construir_catalogo(PRESUPUESTOS_PV["capitulos"])
    assert _cod(nodos, "0678") is None


@pytest.mark.parametrize("codigo", ["CP", "0679"])
def test_f025_r11_el_preflight_omite_la_linea_por_no_casa(codigo):
    """R11 · Y el preflight omite su línea de postventa por «no casa»: no
    imputa a `CP.1` ni a la hija de la obra-capítulo."""
    cli = ClienteFalso()
    cli.capitulos = [
        _fila(100, 0, 0, "CD", "COSTES DIRECTOS"),
        _fila(200, 0, 1, "CP", "COSTES PROPORCIONALES"),
        _fila(201, 200, 1, "CP.1", "SEGUROS"),
        _fila(300, 100, 1, "0679", "OBRA CAPITULO"),
        _fila(301, 300, 1, "0679.MO", "MANO DE OBRA")]
    pf = RegistroPipeline(cliente=cli, settings=SettingsFalso()).preflight(
        obra=ObraEntrada(ide=1, codigo=codigo, nombre="X"),
        lineas=[linea(registro_id=9, es_postventa=True)])
    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert a.motivo == (f"la obra {codigo} no casa con ninguna partida de "
                        f"POSTV2")
    assert getattr(pf, "capitulo_postventa") is None
    assert cli.inserts() == []
