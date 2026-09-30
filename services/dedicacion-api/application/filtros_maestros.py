# application/filtros_maestros.py
"""Depuración de los maestros descargados de Sigrid antes del upsert.

Empleados, en este orden:
  0. Descarte FILA A FILA, antes de cualquier dedupe (F-023): el recurso de
     otra empresa que la ficha de empleado y el recurso inactivo según
     `CriterioActivoRecurso` (literal de estado o fecha de baja del
     recurso). Así un recurso inactivo más reciente no tapa al activo.
  1. Dedupe por RECURSO: la consulta une emp → res → auxrestip/reshor, lo
     que duplica filas cuando un empleado tiene varios recursos
     (históricos). Prevalece la fila con CÓDIGO DE HORA MENSUAL (M*);
     luego la que tenga categoría; a igualdad, el recurso más reciente.
  2. Dedupe por PERSONA: misma persona con varias fichas emp
     (recontrataciones) DENTRO DE CADA EMPRESA. Clave: empresa + DNI
     normalizado o, sin DNI, nombre.
  3. Filtro por CÓDIGO DE HORA MENSUAL: solo los recursos que se
     registran por porcentaje (regla P1 de porcentajes-transfer).
  4. Filtro por categoría (opcional, normalmente desactivado).
  5. Recuento informativo de los incluidos con baja laboral (no excluye).

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


#: Clave con la que se cuentan los descartes por fecha de baja del recurso.
MOTIVO_FECHA_BAJA = "(fecha de baja del recurso)"

#: Columnas que la consulta de empleados trae solo para depurar: no se
#: persisten, así que no llegan al upsert. `empresa` sí se queda.
_AUXILIARES = ("recurso_ide", "empresa_recurso", "estado_recurso",
               "baja_recurso", "baja_laboral")


@dataclass(frozen=True)
class CriterioActivoRecurso:
    """Cuándo un recurso cuenta como inactivo (config.yaml, sync.empleados).

    `estados_excluidos`: literales de `conest.res` del recurso que lo dejan
    fuera (subcadena normalizada, como en obras). `excluir_con_fecha_baja`:
    descartar el recurso con `con.fecbaj` informada. `activo` es el
    interruptor general (`filtro_estado_recurso`). Vacío = nadie queda fuera
    por estado (F-023 R16).
    """

    estados_excluidos: tuple[str, ...] = ()
    excluir_con_fecha_baja: bool = False
    activo: bool = True


@dataclass
class ResultadoDepuracion:
    filas: list[dict[str, Any]]
    brutos: int = 0
    duplicados_recurso: int = 0
    duplicados_persona: int = 0
    excluidos_filtro: int = 0
    excluidos_sin_codigo_mes: int = 0
    excluidos_detalle: Counter = field(default_factory=Counter)
    excluidos_otra_empresa: int = 0
    excluidos_estado_recurso: Counter = field(default_factory=Counter)
    con_baja_laboral: int = 0


# ----------------------------------------------------------------------
# Empleados
# ----------------------------------------------------------------------
def depurar_empleados(
    filas: list[dict[str, Any]],
    categorias_incluidas: list[str],
    filtro_activo: bool,
    exigir_codigo_mes: bool = True,
    criterio: CriterioActivoRecurso = CriterioActivoRecurso(),
) -> ResultadoDepuracion:
    resultado = ResultadoDepuracion(filas=[], brutos=len(filas))

    # 0) Fila a fila, ANTES de los dedupes: recurso de otra empresa y
    #    recurso inactivo según el criterio configurado.
    validas: list[dict[str, Any]] = []
    for fila in filas:
        if _entero(fila.get("empresa_recurso")) not in (
            None, _entero(fila.get("empresa"))
        ):
            resultado.excluidos_otra_empresa += 1
            continue
        motivo = _motivo_recurso_inactivo(fila, criterio)
        if motivo:
            resultado.excluidos_estado_recurso[motivo] += 1
            continue
        validas.append(fila)

    # 1) Dedupe por empleado (ide): prevalece la fila con categoría; a
    #    igualdad, el recurso_ide más alto (recurso más reciente).
    por_ide: dict[int, dict[str, Any]] = {}
    for fila in validas:
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
        # 5) Baja laboral: informativo, el activo lo decide el recurso.
        if (_entero(fila.get("baja_laboral")) or 0) > 0:
            resultado.con_baja_laboral += 1
        limpia = dict(fila)
        for columna in _AUXILIARES:
            limpia.pop(columna, None)
        resultado.filas.append(limpia)

    resultado.filas.sort(key=lambda f: normalizar(str(f.get("nombre"))))
    return resultado


def _motivo_recurso_inactivo(
    fila: dict[str, Any], criterio: CriterioActivoRecurso
) -> str | None:
    """Clave del recuento si el recurso está inactivo; None si no lo está."""
    if not criterio.activo:
        return None
    estado = normalizar(str(fila.get("estado_recurso") or ""))
    excluidos = [normalizar(e) for e in criterio.estados_excluidos]
    if any(patron and patron in estado for patron in excluidos):
        return str(fila.get("estado_recurso"))
    if criterio.excluir_con_fecha_baja and (
        (_entero(fila.get("baja_recurso")) or 0) > 0
    ):
        return MOTIVO_FECHA_BAJA
    return None


def _entero(valor: Any) -> int | None:
    """Entero de Sigrid (empresa, fecha tipo entero) o None si viene NULL."""
    return None if valor is None else int(valor)


def _clave_persona(fila: dict[str, Any]) -> str:
    """Persona dentro de SU empresa: fichas de empresas distintas no se
    mezclan nunca (F-023 R11); empresa nula da la clave «None|...»."""
    empresa = _entero(fila.get("empresa"))
    dni = re.sub(r"[\s\-.]", "", str(fila.get("dni") or "")).upper()
    if dni:
        return f"{empresa}|dni:{dni}"
    return f"{empresa}|nom:{normalizar(str(fila.get('nombre')))}"


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
