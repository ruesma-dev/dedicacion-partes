# tests/test_f032_selector_de_baja.py
"""F-032 · R5 en el front: la empresa de baja sale marcada, nunca oculta.

Comprobación ESTÁTICA de `static/js/app.js` (patrón de
`test_f024_selector.py`): quien decide si una empresa está de baja es la API
(campo `de_baja` de `GET /api/v1/empresas`); el front solo lo pinta. La
apariencia la verifica el humano (verificación MANUAL de F-032). Sin red ni
navegador.
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


def test_f032_r5_el_selector_marca_de_baja_con_el_campo_de_la_api():
    pintar = _funcion("pintarSelectorEmpresa")
    assert "e.de_baja" in pintar
    assert "(de baja)" in pintar
    # Cada empresa que manda la API es una opción: se pinta antes de mirar
    # si está de baja, y no hay salida temprana que la salte.
    assert "state.empresas.forEach(" in pintar
    assert "return" not in pintar.split("state.empresas.forEach(")[1].split("});")[0]


def test_f032_r5_el_front_no_oculta_ni_decide_la_baja():
    """Nada en `app.js` filtra la lista por `de_baja` ni mira `fecbaj` /
    `desact`: la regla vive en la API."""
    assert not re.search(r"empresas\s*\.\s*filter\(", JS)
    for campo in ("fecbaj", "desact"):
        assert not re.search(rf"{campo}", JS), campo
