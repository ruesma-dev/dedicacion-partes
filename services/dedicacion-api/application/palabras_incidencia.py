# application/palabras_incidencia.py
"""Palabras extra de las incidencias para el buscador del desplegable (F-061).

Viven en `config/config.yaml`, en `sync.incidencias.palabras_extra`: una
lista ordenada de entradas `codigo` + `palabras`. Son datos, no lógica: el
front las usa para encontrar la incidencia («baj» → B) y, en un empate, el
orden de las entradas decide cuál va antes. Nada de esto viaja a Sigrid.
"""
from __future__ import annotations

from typing import Any

_CLAVE = "sync.incidencias.palabras_extra"


def palabras_por_codigo(entradas: Any) -> dict[str, tuple[int, list[str]]]:
    """`{codigo: (posición de su entrada, palabras)}` de lo leído de la config.

    Sin la clave (o vacía), ninguna incidencia tiene palabras. Una entrada
    mal escrita lanza `ValueError` con la clave y el motivo: la api no debe
    arrancar con ella, como con una consulta mal escrita."""
    if entradas is None:
        return {}
    if not isinstance(entradas, list):
        # ValueError, no TypeError: es config mal escrita, como el resto.
        raise ValueError(f"{_CLAVE}: tiene que ser una lista de entradas")  # noqa: TRY004
    leidas: dict[str, tuple[int, list[str]]] = {}
    for posicion, entrada in enumerate(entradas):
        codigo = entrada.get("codigo") if isinstance(entrada, dict) else None
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError(f"{_CLAVE}: la entrada {posicion} no tiene codigo")
        codigo = codigo.strip()
        if codigo in leidas:
            raise ValueError(f"{_CLAVE}: codigo repetido, {codigo}")
        # Sin la clave, ninguna palabra; un valor presente tiene que ser una
        # lista (`""`, `0`, `false` o vacío en el YAML son error, no «nada»).
        palabras = entrada.get("palabras", [])
        if not isinstance(palabras, list) or not all(
                isinstance(p, str) and p.strip() for p in palabras):
            raise ValueError(
                f"{_CLAVE}: las palabras de {codigo} tienen que ser una lista de textos")
        leidas[codigo] = (posicion, [p.strip() for p in palabras])
    return leidas
