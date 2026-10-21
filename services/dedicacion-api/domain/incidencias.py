# domain/incidencias.py
"""Incidencias del cuadrante (F-030, docs/ARCHITECTURE.md#regla-incidencia).

Puras y sin dependencias: la letra y el nombre de cada código de `auxhor`
(R4), los días por defecto de un tramo (R17, D2) y la validación de las
incidencias de un trabajador en un mes (R19). Única fuente de esas reglas:
el front no las repite y el transfer trabaja con códigos.
"""
from __future__ import annotations

import calendar
import re
from collections.abc import Sequence

from domain.errors import IncidenciaInvalida
from domain.models import Incidencia

#: Texto entre paréntesis al FINAL de `auxhor.res` («Vacaciones(V)»).
_LETRA_AL_FINAL = re.compile(r"^(?P<nombre>.*?)\s*\((?P<letra>[^()]*)\)$")


def letra_y_nombre(res: str | None, cod: str) -> tuple[str, str]:
    """Letra y nombre de un código de `auxhor` (R4): la letra es el texto
    entre paréntesis al final de `res` y el nombre, lo que va delante
    (`Vacaciones(V)` → `V`, `Vacaciones`). Sin paréntesis al final (o
    vacíos), la letra es el código sin el prefijo `CI` y el nombre, `res`
    entero."""
    texto = (res or "").strip()
    m = _LETRA_AL_FINAL.match(texto)
    if m and m.group("letra").strip():
        return m.group("letra").strip(), m.group("nombre").strip()
    codigo = cod.strip()
    return (codigo[2:] if codigo.startswith("CI") else codigo), texto


def ultimo_dia(anio: int, mes: int) -> int:
    """Último día del mes (28 a 31)."""
    return calendar.monthrange(anio, mes)[1]


def completar_dias(desde: int | None, hasta: int | None,
                   anio: int, mes: int) -> tuple[int, int]:
    """Días de un tramo con los vacíos completados (R17, D2): `desde`
    vacío = 1; `hasta` vacío = último día del mes. No valida: eso es
    `validar_incidencias`."""
    return (1 if desde is None else desde,
            ultimo_dia(anio, mes) if hasta is None else hasta)


def validar_incidencias(lista: Sequence[Incidencia], anio: int,
                        mes: int) -> None:
    """Lanza `IncidenciaInvalida` con el motivo si un día cae fuera del mes,
    `desde` es posterior a `hasta` o dos incidencias del trabajador comparten
    algún día (R19), sean de la obra o el código que sean."""
    ultimo = ultimo_dia(anio, mes)
    for inc in lista:
        for dia in (inc.dia_desde, inc.dia_hasta):
            if not 1 <= dia <= ultimo:
                raise IncidenciaInvalida(
                    f"El día {dia} cae fuera del mes {mes:02d}/{anio} "
                    f"(1 a {ultimo})")
        if inc.dia_desde > inc.dia_hasta:
            raise IncidenciaInvalida(
                f"El día desde ({inc.dia_desde}) es posterior al día hasta "
                f"({inc.dia_hasta})")
    ordenadas = sorted(lista, key=lambda i: (i.dia_desde, i.dia_hasta))
    for previa, siguiente in zip(ordenadas, ordenadas[1:]):
        if siguiente.dia_desde <= previa.dia_hasta:
            raise IncidenciaInvalida(
                f"Dos incidencias comparten días: del {previa.dia_desde} al "
                f"{previa.dia_hasta} y del {siguiente.dia_desde} al "
                f"{siguiente.dia_hasta}")
