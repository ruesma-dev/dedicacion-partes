# application/services/rachas.py
"""Rachas de incidencia como Administración (F-062).

Aquí se IMPLEMENTAN; la fuente normativa es
`docs/ARCHITECTURE.md#regla-incidencia`. Funciones puras, como
`reglas_incidencias.py`: sin I/O, sin `settings` y sin cliente; las fechas
son `int` AAAAMMDD.

  - `pegado` (D2) y `llega_a_fin` (D7): entre dos días solo hay sábados y
    domingos (o nada); tras el último día del tramo solo quedan sábados y
    domingos (o nada). Los festivos no cuentan (F-059).
  - `emparejar` (D5): cada `CIZ` cierra el inicio abierto más reciente de su
    recurso, por (`fec`, inicio antes que `CIZ`, `ide`); un inicio sin `CIZ`
    es una racha abierta y un `CIZ` sin inicio abierto no forma racha.
"""
from __future__ import annotations

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from domain.models.registro_models import LineaIncidenciaSigrid

#: Código de `auxhor` que cierra la racha de cualquier incidencia.
CODIGO_FIN = "CIZ"
#: Sábado y domingo en `date.weekday()`.
_FIN_DE_SEMANA = (5, 6)


def _dia(f: int) -> date:
    return date(f // 10000, f // 100 % 100, f % 100)


def _int(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def ultimo_dia(ano: int, mes: int) -> int:
    """El último día del mes, AAAAMMDD."""
    return ano * 10000 + mes * 100 + calendar.monthrange(ano, mes)[1]


def _solo_fin_de_semana(desde: date, hasta: date) -> bool:
    """¿Todos los días de [`desde`, `hasta`] son sábado o domingo? Vacío:
    sí."""
    d = desde
    while d <= hasta:
        if d.weekday() not in _FIN_DE_SEMANA:
            return False
        d += timedelta(days=1)
    return True


def pegado(c: int, d: int) -> bool:
    """D2: `d` está pegado a `c` si `c < d` y entre ambos solo hay sábados
    y domingos, o nada (también de un mes al siguiente)."""
    return c < d and _solo_fin_de_semana(_dia(c) + timedelta(days=1),
                                         _dia(d) - timedelta(days=1))


def llega_a_fin(h: int) -> bool:
    """D7: tras el día `h` solo quedan sábados y domingos de su mes, o
    nada."""
    return _solo_fin_de_semana(_dia(h) + timedelta(days=1),
                               _dia(ultimo_dia(h // 10000, h // 100 % 100)))


def codigo(linea: LineaIncidenciaSigrid) -> str:
    return (linea.hora_codigo or "").strip()


def es_inicio(linea: LineaIncidenciaSigrid) -> bool:
    cod = codigo(linea)
    return cod.startswith("CI") and cod != CODIGO_FIN


def es_fin(linea: LineaIncidenciaSigrid) -> bool:
    return codigo(linea) == CODIGO_FIN


@dataclass(frozen=True)
class Racha:
    """Un inicio `CI*` y su `CIZ` (None: abierta)."""
    codigo: str
    inicio: LineaIncidenciaSigrid
    cierre: LineaIncidenciaSigrid | None


def emparejar(lineas: Iterable[LineaIncidenciaSigrid]) -> list[Racha]:
    """D5: las rachas de las líneas, por recurso, ordenadas por inicio
    (`fec`, `ide`). Las líneas que no son `CI*` no cuentan."""
    por_recurso: dict[int, list[LineaIncidenciaSigrid]] = {}
    for ls in lineas:
        if es_inicio(ls) or es_fin(ls):
            por_recurso.setdefault(int(ls.reside), []).append(ls)
    rachas: list[Racha] = []
    for propias in por_recurso.values():
        pila: list[LineaIncidenciaSigrid] = []
        cerradas: dict[int, LineaIncidenciaSigrid] = {}
        for ls in sorted(propias, key=lambda x: (x.fecha_int,
                                                 0 if es_inicio(x) else 1,
                                                 x.ide)):
            if es_inicio(ls):
                pila.append(ls)
            elif pila:
                cerradas[pila.pop().ide] = ls
        rachas += [Racha(codigo(ls), ls, cerradas.get(ls.ide))
                   for ls in propias if es_inicio(ls)]
    return sorted(rachas, key=lambda r: (r.inicio.fecha_int, r.inicio.ide))
