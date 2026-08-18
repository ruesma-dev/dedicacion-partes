# application/filtros_maestros.py
"""Depuración de los maestros descargados de Sigrid antes del upsert.

Empleados, en este orden:
  1. Dedupe por RECURSO: la consulta une emp → res → auxrestip/reshor, lo
     que duplica filas cuando un empleado tiene varios recursos
     (históricos). Prevalece la fila con CÓDIGO DE HORA MENSUAL (M*);
     luego la que tenga categoría; a igualdad, el recurso más reciente.
  2. Dedupe por PERSONA: misma persona con varias fichas emp
     (recontrataciones). Clave: DNI normalizado o, sin DNI, nombre.
  3. Filtro por CÓDIGO DE HORA MENSUAL: solo los recursos que se
     registran por porcentaje (regla P1 de porcentajes-transfer).
  4. Filtro por categoría (opcional, normalmente desactivado).

Obras: se excluyen las obras cuyo estado (conest.res) case con la lista
de estados excluidos (terminada, cerrada, ...).

Las comparaciones son normalizadas (minúsculas, sin acentos).
"""
from __future__ import annotations

import re

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from domain.normalizacion import normalizar


@dataclass
class ResultadoDepuracion:
    filas: list[dict[str, Any]]
    brutos: int = 0
    duplicados_recurso: int = 0
    duplicados_persona: int = 0
    excluidos_filtro: int = 0
    excluidos_sin_codigo_mes: int = 0
    excluidos_detalle: Counter = field(default_factory=Counter)


# ----------------------------------------------------------------------
# Empleados
# ----------------------------------------------------------------------
def depurar_empleados(
    filas: list[dict[str, Any]],
    categorias_incluidas: list[str],
    filtro_activo: bool,
    exigir_codigo_mes: bool = True,
) -> ResultadoDepuracion:
    resultado = ResultadoDepuracion(filas=[], brutos=len(filas))

    # 1) Dedupe por empleado (ide): prevalece la fila con categoría; a
    #    igualdad, el recurso_ide más alto (recurso más reciente).
    por_ide: dict[int, dict[str, Any]] = {}
    for fila in filas:
        ide = int(fila["ide"])
        previa = por_ide.get(ide)
        if previa is None:
            por_ide[ide] = fila
            continue
        resultado.duplicados_recurso += 1
        if _mejor_que(fila, previa):
            por_ide[ide] = fila

    # 2) Dedupe por PERSONA: la misma persona puede tener varias fichas
    #    emp (recontrataciones). Clave: DNI normalizado; si no hay DNI,
    #    nombre normalizado. Prevalece la ficha con categoría y, a
    #    igualdad, la de ide más alto (la más reciente).
    por_persona: dict[str, dict[str, Any]] = {}
    for fila in por_ide.values():
        clave = _clave_persona(fila)
        previa = por_persona.get(clave)
        if previa is None:
            por_persona[clave] = fila
            continue
        resultado.duplicados_persona += 1
        if _mejor_ficha(fila, previa):
            por_persona[clave] = fila

    # 3) Filtro por CÓDIGO DE HORA MENSUAL (criterio principal) y
    #    4) filtro por categorías incluidas (opcional).
    incluidas = {normalizar(c) for c in categorias_incluidas}
    for fila in por_persona.values():
        if exigir_codigo_mes and not _cod_mes(fila):
            resultado.excluidos_sin_codigo_mes += 1
            resultado.excluidos_detalle["(sin código de hora mensual)"] += 1
            continue
        categoria = fila.get("categoria")
        if filtro_activo and normalizar(categoria) not in incluidas:
            resultado.excluidos_filtro += 1
            resultado.excluidos_detalle[str(categoria or "(sin categoría)")] += 1
            continue
        limpia = dict(fila)
        limpia.pop("recurso_ide", None)
        resultado.filas.append(limpia)

    resultado.filas.sort(key=lambda f: normalizar(str(f.get("nombre"))))
    return resultado


def _clave_persona(fila: dict[str, Any]) -> str:
    dni = re.sub(r"[\s\-.]", "", str(fila.get("dni") or "")).upper()
    if dni:
        return "dni:" + dni
    return "nom:" + normalizar(str(fila.get("nombre")))


def _mejor_ficha(nueva: dict[str, Any], previa: dict[str, Any]) -> bool:
    mes_nueva, mes_previa = bool(_cod_mes(nueva)), bool(_cod_mes(previa))
    if mes_nueva != mes_previa:
        return mes_nueva
    con_cat_nueva = bool(nueva.get("categoria"))
    con_cat_previa = bool(previa.get("categoria"))
    if con_cat_nueva != con_cat_previa:
        return con_cat_nueva
    return int(nueva["ide"]) > int(previa["ide"])


def _cod_mes(fila: dict[str, Any]) -> str:
    """Código de hora mensual del recurso (M*), vacío si no tiene."""
    valor = str(fila.get("cod_hora_mes") or "").strip()
    return valor if valor.upper().startswith("M") else ""


def _mejor_que(nueva: dict[str, Any], previa: dict[str, Any]) -> bool:
    """Entre dos recursos del mismo empleado: manda tener código mensual,
    luego tener categoría, luego el recurso más reciente."""
    mes_nueva, mes_previa = bool(_cod_mes(nueva)), bool(_cod_mes(previa))
    if mes_nueva != mes_previa:
        return mes_nueva
    con_cat_nueva = bool(nueva.get("categoria"))
    con_cat_previa = bool(previa.get("categoria"))
    if con_cat_nueva != con_cat_previa:
        return con_cat_nueva
    return _recurso(nueva) > _recurso(previa)


def _recurso(fila: dict[str, Any]) -> int:
    valor = fila.get("recurso_ide")
    return int(valor) if valor is not None else -1


# ----------------------------------------------------------------------
# Obras
# ----------------------------------------------------------------------
def depurar_obras(
    filas: list[dict[str, Any]],
    estados_excluidos: list[str],
    filtro_activo: bool,
) -> ResultadoDepuracion:
    resultado = ResultadoDepuracion(filas=[], brutos=len(filas))
    excluidos = [normalizar(e) for e in estados_excluidos if normalizar(e)]

    for fila in filas:
        estado = normalizar(str(fila.get("estado_sigrid") or ""))
        if filtro_activo and any(patron in estado for patron in excluidos):
            resultado.excluidos_filtro += 1
            resultado.excluidos_detalle[str(fila.get("estado_sigrid"))] += 1
            continue
        resultado.filas.append(fila)
    return resultado
