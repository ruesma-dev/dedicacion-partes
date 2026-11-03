# domain/obras.py
"""Reglas puras sobre el código de una obra (F-039).

- Qué obra se ignora por su código: docs/ARCHITECTURE.md#regla-seis-digitos.
- Cómo se nombra e identifica la entrada de una partida VAR en el cuadrante:
  docs/ARCHITECTURE.md#regla-var.

Única definición de cada una: el sync, el preview y los tests las importan
de aquí.
"""
from __future__ import annotations

import re


def tiene_digitos_seguidos(cod: str | None, n: int) -> bool:
    """¿El código CONTIENE `n` o más dígitos seguidos, lleve o no letras o
    sufijo? Con `n <= 0` no hay filtro: nunca."""
    if n <= 0:
        return False
    return re.search(f"[0-9]{{{n}}}", cod or "") is not None


def codigo_entrada(obra_cod: str, partida_cod: str) -> str:
    """Código de la entrada VAR: `<obra>-<partida>`, sin relleno (D2)."""
    return f"{obra_cod.strip()}-{partida_cod.strip()}"


def partida_de_entrada(cod: str | None, obra_cod: str | None) -> str | None:
    """La inversa de `codigo_entrada` (F-054 T26, R47): `VAR-29` con obra
    `VAR` da `29`. `None` si falta el código de la obra, si `cod` no empieza
    por `<obra>-` o si no queda partida."""
    obra = (obra_cod or "").strip()
    texto = (cod or "").strip()
    if not obra or not texto.startswith(f"{obra}-"):
        return None
    return texto[len(obra) + 1:].strip() or None


def ide_entrada(paride: int) -> int:
    """`ide` de la entrada VAR en la tabla `obra`: el de la partida en
    negativo, que no choca con ninguna obra de Sigrid (D6)."""
    return -int(paride)
