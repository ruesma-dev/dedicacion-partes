# tests/test_f039_partida_fija.py
"""F-039 · R22 en el front: la partida de una línea VAR se pinta fija.

Comprobación ESTÁTICA de `static/js/app.js` (patrón de
`test_f025_catalogo_postventa.py`): quien decide que la partida es fija es
el transfer (`partida_metodo = "var"`, docs/ARCHITECTURE.md#regla-var); el
front solo lo pinta, sin saber qué es la obra VAR ni su umbral. La
apariencia la verifica el humano (M3). Sin red ni navegador.
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


def test_f039_r22_la_accion_var_pinta_la_partida_fija():
    """R22 · Con `escribir` y `partida_metodo === "var"`, la celda es un
    `span.partida-fija` con `partida_cod`, no el desplegable."""
    modal = _plano(_funcion("pintarModalPreflight"))
    rama = re.search(
        r'if \(a\.accion === "escribir" && a\.partida_metodo === "var"\) '
        r'\{ (.*?) \}', modal)
    assert rama, modal
    assert ('<span class="partida-fija">${escapeHtml(a.partida_cod || "")}'
            '</span>') in rama.group(1)
    assert "sel-partida" not in rama.group(1)


def test_f039_r22_el_resto_de_acciones_sigue_igual():
    """R22 · Las demás `escribir` siguen con el desplegable y su aviso; las
    otras acciones, con su motivo."""
    modal = _plano(_funcion("pintarModalPreflight"))
    assert ('<select class="sel-partida" data-reg="${a.registro_id}">'
            in modal)
    assert "${opcionesPartida(partidas, a.paride)}</select>" in modal
    assert '<span class="motivo">${escapeHtml(a.motivo || "")}</span>' \
        in modal
    assert modal.count('<div class="aviso">${escapeHtml(a.aviso)}</div>') == 1


def test_f039_r22_ningun_literal_de_la_obra_var_ni_del_umbral():
    """R22 · `app.js` no sabe qué obra es la VAR ni desde qué partida."""
    assert not re.search(r"""["'`]VAR[-"'`]""", JS)
    assert not re.search(r"""["'`]29["'`]""", JS)
