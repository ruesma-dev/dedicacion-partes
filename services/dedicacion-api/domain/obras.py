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


def ide_entrada(paride: int) -> int:
    """`ide` de la entrada VAR en la tabla `obra`: el de la partida en
    negativo, que no choca con ninguna obra de Sigrid (D6)."""
    return -int(paride)
