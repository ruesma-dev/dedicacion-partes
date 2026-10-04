# domain/deshacer.py
"""Quién puede deshacer (F-027, decisión A del 2026-10-04).

Deshacer restaura la fila ENTERA del trabajador al `snapshot_antes` de su
último evento pendiente en el periodo: si ese evento es de otro usuario,
deshacerlo borraría en silencio su cambio. Por eso solo se deshace cuando
el ÚLTIMO evento pendiente es del usuario que lo pide, y nunca uno que no
sea el último.

Único sitio de la regla y de cómo se comparan los usuarios: la usan el caso
de uso de deshacer y el cálculo de `puede_deshacer` del cuadrante y de la
fila (`application/use_cases.py`). La regla, en
`docs/ARCHITECTURE.md#regla-deshacer`.
"""
from __future__ import annotations


def clave_usuario(usuario: str) -> str:
    """Usuario comparable: sin espacios en los extremos y sin distinguir
    mayúsculas. El interior no se toca: dos usuarios distintos no pueden
    acabar con la misma clave por normalizar de más."""
    return usuario.strip().casefold()


def deshacer_permitido(autor_ultimo_pendiente: str | None, usuario: str) -> bool:
    """Verdadero solo si hay un evento pendiente y su autor es `usuario`."""
    if autor_ultimo_pendiente is None:
        return False
    return clave_usuario(autor_ultimo_pendiente) == clave_usuario(usuario)
