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


def comentario_de_tex(tex: str | None, marca: str | None) -> str | None:
    """F-069 (R31, D17): el comentario que guarda el `tex` de una línea, tal
    como lo publica `existentes`: sin la `marca` de pruebas del principio
    (la de `st.marca_pruebas`, la que pone `tex_de`) ni espacios a los lados;
    vacío ⇒ `None`. Solo se quita al principio: en otro sitio es texto del
    usuario. Sin marca, el `tex` tal cual (sin espacios). La api lo guarda
    sin tocarlo: no conoce la marca (D17)."""
    texto = (tex or "").strip()
    if marca and texto.startswith(marca):
        texto = texto[len(marca):].strip()
    return texto or None


#: F-069 (D20, R26; design §6.5): lo que el motivo de una línea ya
#: registrada añade sobre su comentario.
MOTIVO_TEX_SE_ACTUALIZA = "se actualiza el comentario"
MOTIVO_TEX_NO_NUESTRA = ("el comentario no se actualiza: la línea no es de "
                         "porcentajes")
MOTIVO_TEX_CERRADO = ("el comentario no se actualiza: su parte no está En "
                      "registro")
MOTIVO_TEX_FUERA_PRUEBAS = ("el comentario no se actualiza: la línea no es "
                            "de la obra de pruebas")
#: El prefijo de `synckey` de todas nuestras líneas (titular, vinculado e
#: incidencia), como `sigrid_write_client.PREFIJO_SYNCKEY`.
PREFIJO_NUESTRAS = "porcentajes:"


def hay_comentarios(lineas) -> bool:
    """F-069 (R24): si alguna línea de la petición, o alguno de sus
    vinculados, trae comentario. Sin ninguno, ni se lee el `tex` de lo
    registrado ni se decide nada de D20: todo como antes."""
    return any((l.comentario or "").strip()
               or any((v.comentario or "").strip() for v in l.vinculados)
               for l in lineas)


def tex_a_actualizar(comentario: str | None, marca: str | None, hit, *,
                     en_registro: bool, obride_pruebas: int | None
                     ) -> tuple[str | None, str | None]:
    """F-069 (D20, R26; design §6.5): `(tex_nuevo, motivo)` de una línea YA
    registrada (`hit`, con `tex`, `synckey` y `obride` leídos en el paso 6).

    Sin comentario, nada (R23: el `tex` se queda). Si `tex_de(comentario,
    marca)` es el leído (sin espacios a los lados), nada. Si no, solo se
    cambia si la línea es nuestra (`synckey` `porcentajes:`), su parte está
    En registro (`en_registro`) y, en pruebas (`obride_pruebas`), es de la
    obra de pruebas; si no, el motivo dice por qué."""
    if not (comentario or "").strip():
        return None, None
    nuevo = tex_de(comentario, marca)
    if nuevo == (getattr(hit, "tex", None) or "").strip():
        return None, None
    if not (getattr(hit, "synckey", None) or "").strip().startswith(
            PREFIJO_NUESTRAS):
        return None, MOTIVO_TEX_NO_NUESTRA
    if not en_registro:
        return None, MOTIVO_TEX_CERRADO
    if obride_pruebas is not None and getattr(hit, "obride",
                                              None) != obride_pruebas:
        return None, MOTIVO_TEX_FUERA_PRUEBAS
    return nuevo, MOTIVO_TEX_SE_ACTUALIZA


def anotar_tex(accion, decision: tuple[str | None, str | None]) -> None:
    """F-069 (D20): pone en la acción ya registrada (titular o vinculado) su
    `tex_nuevo` y añade a su motivo lo que pasa con el comentario."""
    tex_nuevo, motivo = decision
    accion.tex_nuevo = tex_nuevo
    if motivo:
        accion.motivo = f"{accion.motivo}; {motivo}" if accion.motivo \
            else motivo
