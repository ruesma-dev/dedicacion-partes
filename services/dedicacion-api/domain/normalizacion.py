# domain/normalizacion.py
"""Normalización de texto para comparaciones tolerantes.

Se usa al filtrar maestros de Sigrid (categorías de empleados, estados
de obra), donde los literales pueden variar en mayúsculas, acentos o
espaciado ("Técnico de Prevención" / "Tecnico de prevencion").
"""
from __future__ import annotations

import re
import unicodedata


def texto_o_none(valor: object) -> str | None:
    """Texto de Sigrid tal y como se guarda: sin espacios en los bordes y
    `None` si queda vacío. Única definición: la usan el repositorio al
    guardar y el sync al pedir el universo de postventa (F-025, R12), que
    tiene que mandar lo mismo que se guarda."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def normalizar(texto: str | None) -> str:
    """minúsculas + sin acentos + espacios colapsados + sin bordes."""
    if not texto:
        return ""
    plano = unicodedata.normalize("NFD", texto)
    sin_acentos = "".join(c for c in plano if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sin_acentos).strip().lower()
