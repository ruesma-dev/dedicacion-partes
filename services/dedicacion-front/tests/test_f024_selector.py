# tests/test_f024_selector.py
"""F-024 · Selector de empresa en el front (R3, R4, R5, R12), con los textos
de F-034 (R6): el aviso de la línea y el `title` del selector.

Comprobación ESTÁTICA de `templates/index.html` y `static/js/app.js`: el
front no tiene lógica de negocio, así que lo que se fija es que pinta el
selector donde toca, que pasa la empresa elegida a la API y que no filtra
nada por su cuenta. La apariencia la verifica el humano (T13 de F-024).
Sin red ni navegador.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
HTML = (RAIZ / "templates" / "index.html").read_text(encoding="utf-8")
JS = (RAIZ / "static" / "js" / "app.js").read_text(encoding="utf-8")
CSS = (RAIZ / "static" / "css" / "styles.css").read_text(encoding="utf-8")


class _Hijos(HTMLParser):
    """Anota la ruta de clases/ids de cada etiqueta abierta."""

    def __init__(self) -> None:
        super().__init__()
        self.pila: list[str] = []
        self.vistos: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag, attrs) -> None:
        datos = dict(attrs)
        marca = "#" + datos["id"] if datos.get("id") else \
            "." + (datos.get("class") or "").split(" ")[0]
        self.vistos.append((f"{tag}{marca}", list(self.pila)))
        if tag not in ("img", "link", "meta", "input", "br"):
            self.pila.append(f"{tag}{marca}")

    def handle_endtag(self, tag) -> None:
        while self.pila:
            if self.pila.pop().startswith(tag):
                break


def _funcion(nombre: str) -> str:
    """Cuerpo (aproximado) de una función de `app.js`, hasta la siguiente
    declaración de primer nivel."""
    m = re.search(rf"^(async )?function {nombre}\(.*?(?=^(async )?function |\Z)",
                  JS, re.DOTALL | re.MULTILINE)
    assert m, f"no existe la función {nombre} en app.js"
    return m.group(0)


# --------------------------------- R3 --------------------------------- #
def test_f024_r3_selector_es_el_primer_hijo_de_topbar_meta():
    p = _Hijos()
    p.feed(HTML)
    [(_etiqueta, padres)] = [v for v in p.vistos
                            if v[0] == "select#selector-empresa"]
    assert padres[-1] == "div.topbar__meta"
    hijos_meta = [v[0] for v in p.vistos if v[1] and v[1][-1] ==
                  "div.topbar__meta"]
    assert hijos_meta[0] == "select#selector-empresa"


def test_f024_r3_r4_al_entrar_pide_empresas_y_usa_la_por_defecto():
    init = _funcion("init")
    assert "cargarEmpresas()" in init
    assert init.index("cargarEmpresas()") < init.index("cargarPeriodo(")
    cargar = _funcion("cargarEmpresas")
    assert 'api("/empresas")' in cargar
    assert "por_defecto" in cargar
    assert "URLSearchParams" in cargar


def test_f024_r4_cambiar_de_empresa_recarga_y_deja_la_url():
    cambio = _funcion("cambiarEmpresa")
    assert "history.replaceState" in cambio
    assert 'searchParams.set("empresa"' in cambio
    assert "cargarPeriodo(state.anio, state.mes)" in cambio
    assert re.search(r'#selector-empresa"\)\.addEventListener\(\s*"change"',
                     JS)


# --------------------------------- R5 --------------------------------- #
def test_f024_r5_con_empresa_en_api_para_toda_ruta_de_periodo():
    con = _funcion("conEmpresa")
    assert "empresa=" in con and "state.empresa" in con
    api = _funcion("api")
    assert 'startsWith("/periodos/")' in api and "conEmpresa(" in api


def test_f024_r5_el_export_lleva_la_empresa():
    assert re.search(r'"/api/v1"\s*\+\s*conEmpresa\(\s*`/periodos/\$\{state'
                     r'\.anio\}/\$\{state\.mes\}/export\.xlsx`', JS)


def test_f024_r5_el_front_no_filtra_por_empresa():
    """Ni compara la empresa de filas u obras con la elegida, ni deduce
    `otra_empresa` de `obra_empresa`: eso lo decide la API."""
    assert "obra_empresa" not in JS
    assert not re.search(r"\.empresa\s*[!=]==?\s*state\.empresa", JS)
    assert not re.search(r"state\.empresa\s*[!=]==?\s*\w+\.empresa", JS)
    for linea in JS.splitlines():
        if ".filter(" in linea:
            assert "empresa" not in linea, linea


# --------------------------------- R12 -------------------------------- #
def test_f024_r12_marcas_sin_empresa_y_otra_empresa():
    celda = _funcion("construirCelda")
    assert "t.empresa === null" in celda and "sin empresa" in celda
    assert "l.otra_empresa" in celda and "chip-otra-empresa" in celda
    # F-034 (R6): el aviso dice que la obra no es de la empresa de las obras
    # y ya no lleva la coletilla «en esta empresa».
    assert AVISO_OTRA_EMPRESA in celda
    assert "no se registrará en esta empresa" not in celda
    for clase in (".selector-empresa", ".tag-sin-empresa",
                  ".chip-linea.chip-otra-empresa"):
        assert clase in CSS, clase


# ------------------------------- F-034 R6 ------------------------------ #
#: Texto del aviso de una línea con `otra_empresa` (F-034, R6).
AVISO_OTRA_EMPRESA = "la obra no es de la empresa de las obras: no se registrará"


def test_f034_r6_aviso_de_la_linea_y_title_del_selector():
    """El aviso no dice «en esta empresa» en ningún sitio del front, y el
    selector se presenta como la empresa de los trabajadores. Presentación
    pura: el front no compara empresas (lo fija R5 de F-024)."""
    assert AVISO_OTRA_EMPRESA in _funcion("construirCelda")
    assert "en esta empresa" not in JS
    p = _Atributos("selector-empresa")
    p.feed(HTML)
    assert p.atributos["title"] == "Empresa de los trabajadores"


class _Atributos(HTMLParser):
    """Atributos de la etiqueta con el id dado."""

    def __init__(self, ide: str) -> None:
        super().__init__()
        self.ide = ide
        self.atributos: dict[str, str | None] = {}

    def handle_starttag(self, tag, attrs) -> None:
        datos = dict(attrs)
        if datos.get("id") == self.ide:
            self.atributos = datos
