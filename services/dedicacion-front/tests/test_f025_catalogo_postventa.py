# tests/test_f025_catalogo_postventa.py
"""F-025 · R22-R24 en el front: el catálogo, el botón PV y la marca de
línea salen de los campos de la API, sin lógica propia.

Comprobación ESTÁTICA de `static/js/app.js` (patrón de
`test_f032_selector_de_baja.py`): quien decide qué obra se ofrece como normal
(`activa`), cuál como `Postv-` (`admite_postventa`) y qué línea se puede usar
(`ofrecible`) es la API; el front solo lo pinta. La apariencia la verifica el
humano. Sin red ni navegador.
"""
from __future__ import annotations

import re
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "static" / "js" / "app.js"
      ).read_text(encoding="utf-8")


def _funcion(nombre: str) -> str:
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


# ------------------------------- R22 ------------------------------------ #

def test_f025_r22_la_entrada_normal_depende_de_activa():
    """R22 · La entrada normal de una obra se ofrece si y solo si `activa`."""
    construir = _plano(_funcion("construirCatalogoObras"))
    assert re.search(r"if \(o\.activa\) \{ state\.catalogoObras\.push\(\{ "
                     r"obra: o, pv: false,", construir), construir


def test_f025_r22_la_entrada_postv_depende_de_admite_postventa():
    """R22 · La `Postv-` se ofrece si y solo si `admite_postventa`."""
    construir = _plano(_funcion("construirCatalogoObras"))
    assert re.search(r"if \(o\.admite_postventa\) \{ state\.catalogoObras"
                     r"\.push\(\{ obra: o, pv: true,", construir), construir


def test_f025_r22_ninguna_otra_fuente_decide_el_catalogo():
    """R22 · Ni el filtro viejo por `activa` para las dos entradas, ni
    literales del código de postventa o de una obra concreta."""
    construir = _plano(_funcion("construirCatalogoObras"))
    assert ".filter(" not in construir
    assert "POSTV" not in JS
    assert not re.search(r"\.cod\s*===?\s*[\"']", JS)


# ------------------------------- R23 ------------------------------------ #

def test_f025_r23_el_boton_pv_solo_pasa_a_un_modo_ofrecido():
    """R23 · Antes de cambiar de modo, el botón PV mira si la API marca la
    obra con el modo destino: `obra_admite_postventa` para pasar a postventa
    y `obra_activa` para pasar a normal; si no, avisa y no cambia."""
    chip = _plano(_funcion("chipEditable"))
    pv = chip.split('btnPv.addEventListener("click", () => {')[1]
    pv = pv.split("linea.es_postventa = !linea.es_postventa;")[0]
    assert re.search(r"const ofrecido = linea\.es_postventa \? "
                     r"linea\.obra_activa : linea\.obra_admite_postventa;",
                     pv), pv
    assert re.search(r"if \(!ofrecido\) \{ toast\([^;]*, true\); return; \}",
                     pv), pv


def test_f025_r23_la_linea_nueva_lleva_las_marcas_de_su_obra():
    """R23 · La línea añadida desde el catálogo lleva las dos marcas de la
    obra (las que mira el botón PV) y es ofrecible: el catálogo solo ofrece
    entradas ofrecibles. Ya no hay `obra_activa: true` fijo."""
    elegir = _plano(_funcion("montarAutocompletado").split(
        "const elegir = (entrada) => {")[1].split("};")[0])
    for campo in ("obra_activa: entrada.obra.activa,",
                  "obra_admite_postventa: entrada.obra.admite_postventa,",
                  "ofrecible: true,"):
        assert campo in elegir, campo
    assert "obra_activa: true" not in JS


# ------------------------------- R24 ------------------------------------ #

def test_f025_r24_copiar_de_arriba_usa_ofrecible():
    """R24 · «Copiar de la fila superior» copia solo las líneas que la API
    marca `ofrecible`."""
    copiar = _plano(_funcion("copiarDeArriba"))
    assert ".filter((l) => l.ofrecible)" in copiar
    assert "obra_activa" not in copiar


def test_f025_r24_la_marca_de_linea_no_utilizable_usa_ofrecible():
    """R24 · La marca `obra-baja` del chip sale de `ofrecible`; la de otra
    empresa (F-034) no cambia."""
    js = _plano(JS)
    assert '(l.ofrecible ? "" : " obra-baja")' in js
    assert '(l.otra_empresa ? " chip-otra-empresa" : "")' in js
    assert '(l.obra_activa ? "" : " obra-baja")' not in js
