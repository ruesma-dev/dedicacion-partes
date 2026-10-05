# domain/errores.py
"""Errores de dominio de la regla de empresa (ARCHITECTURE.md#regla-empresa).

Heredan de excepciones estándar a propósito: `EmpresasMezcladas` es un dato
de entrada inválido (la app lo traduce a 422) y `ObraAmbigua` un fallo al
leer Sigrid (cae en el 502 genérico de la app).
"""
from __future__ import annotations


class EmpresasMezcladas(ValueError):
    """Las líneas de una misma petición traen más de una empresa válida."""


class ObraAmbigua(RuntimeError):
    """Hay más de una ficha de la obra dentro de la empresa pedida."""
