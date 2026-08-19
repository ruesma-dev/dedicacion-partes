# application/services/partida_resolver.py
"""Resolución de la PARTIDA de imputación de cada línea porcentual.

- OBRA NORMAL: la partida asignada al recurso, como en el proyecto de
  partes: se busca en el presupuesto de la obra (capítulos CI, o CI+CD
  según la categoría) la partida cuyo rol casa con la CATEGORÍA del
  trabajador y, si la descripción incluye su NOMBRE, esa gana
  (partida_matcher, copiado de partes-persistencia).
- POSTVENTA: el destino (la obra del ajuste `POSTVENTA_OBRA_COD`) y el
  criterio de casado los fija `docs/ARCHITECTURE.md#regla-p5`; aquí solo se
  implementan.

La aplicación propone; el usuario puede editar la partida en el front
(override `paride` en la línea de entrada).
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Optional

from application.services import text_match as tm
from application.services.partida_catalog import (
    PartidaNodo, build_arbol_partidas, partidas_hoja,
)
from application.services.partida_matcher import (
    ambito_categoria, match_partida,
)


def construir_catalogo(filas: list[dict]) -> dict[int, PartidaNodo]:
    """Adapta las filas dict del cliente al builder de partes."""
    objetos = [SimpleNamespace(**f) for f in filas]
    return build_arbol_partidas(objetos)


def resolver_normal(
    nodos: dict[int, PartidaNodo], categoria: Optional[str],
    nombre: Optional[str],
) -> Optional[tuple[int, Optional[str], str]]:
    """(paride, cod, metodo) de la partida del recurso, o None."""
    hojas = partidas_hoja(nodos, categorias=ambito_categoria(categoria))
    m = match_partida(categoria, nombre, hojas)
    if m is None:
        return None
    return int(m.partida.ide), m.partida.cod, m.metodo


def resolver_postventa(
    nodos: dict[int, PartidaNodo], obra_cod: Optional[str],
    obra_nombre: Optional[str],
) -> Optional[PartidaNodo]:
    """Partida de la obra de postventa que corresponde a la obra original.

    Cascada: código exacto > empieza por > código en la descripción >
    nombre. Ver `docs/ARCHITECTURE.md#regla-p5`.

    El universo de búsqueda son las **hojas activas** ordenadas por código,
    que es EXACTAMENTE el mismo que el preflight publica en
    `partidas_postventa` para el desplegable del front. Dos consecuencias
    que antes no se cumplían: la cascada no puede devolver un capítulo (que
    nunca es destino válido), y el desempate de cada escalón deja de
    depender del orden en que Sigrid haya devuelto las filas.
    """
    cod = tm.normalize_code(obra_cod)
    candidatos = partidas_hoja(nodos)
    if cod:
        exactas = [n for n in candidatos if tm.normalize_code(n.cod) == cod]
        if exactas:
            return exactas[0]
        empieza = [n for n in candidatos
                   if tm.normalize_code(n.cod).startswith(cod)]
        if empieza:
            return sorted(empieza,
                          key=lambda n: len(tm.normalize_code(n.cod)))[0]
        en_res = [n for n in candidatos
                  if tm.normalize(n.res or "").startswith(cod.lower())
                  or f" {cod.lower()} " in f" {tm.normalize(n.res or '')} "
                  or tm.normalize(n.res or "").split(" ")[:1] == [cod.lower()]]
        if en_res:
            return en_res[0]
    nombre_n = tm.normalize(obra_nombre)
    if nombre_n:
        en_res = [n for n in candidatos
                  if nombre_n in tm.normalize(n.res or "")]
        if en_res:
            return en_res[0]
    return None
