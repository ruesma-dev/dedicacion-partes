# application/services/texto_linea.py
"""F-069 (R23, D14; ARCHITECTURE.md#regla-vinculado): el `tex` de una línea
que se escribe en Sigrid (la del titular o la de un vinculado).

Puro: no lee ni escribe nada. El comentario de la línea (`asignacion.
comentario` del titular, el del vinculado) va al `tex`; en modo pruebas, la
marca (`PRUEBA-PORC`) seguida del comentario, para que `limpiar` la siga
encontrando como prefijo. Sin comentario, como antes de F-069: la marca en
pruebas y, en real, `None`, que el cliente convierte en `""` al insertar y
en «no tocar el `tex`» al editar.
"""
from __future__ import annotations


def tex_de(comentario: str | None, marca: str | None) -> str | None:
    """El `tex` de la línea: comentario (sin espacios a los lados), marca +
    espacio + comentario, la marca sola o `None` si no hay ninguno."""
    texto = (comentario or "").strip()
    if not texto:
        return marca or None
    return f"{marca} {texto}" if marca else texto
