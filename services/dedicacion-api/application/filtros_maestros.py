# application/filtros_maestros.py
"""Depuración de los maestros descargados de Sigrid antes del upsert.

Empleados (F-026: una fila por RECURSO persona,
`docs/ARCHITECTURE.md#regla-recurso`), en este orden:
  0. Descarte FILA A FILA del recurso inactivo según
     `CriterioActivoRecurso`: literal de estado o fecha de baja ANTERIOR a
     la ventana de bajas (`baja_desde`). El de baja en la ventana entra con
     su `fecha_baja` y el cuadrante y el registro deciden por mes.
  1. Filtro por CÓDIGO DE HORA MENSUAL: solo los recursos que se
     registran por porcentaje (regla P1 de porcentajes-transfer).
  2. Filtro por categoría (opcional, normalmente desactivado).
  3. Recuentos informativos de los incluidos con baja laboral y con fecha
     de baja (no excluyen).
Sin dedupes ni descarte por empresa (F-026 D2): dos recursos de la misma
persona son dos trabajadores, cada uno en su empresa. Si comparten
documento dentro de la misma empresa, se avisa en `posible_misma_persona`.

Obras (F-025): cada obra sale con dos marcas independientes, `activa`
(su estado no case con la lista de estados excluidos: terminada, cerrada,
...) y `admite_postventa` (está en el universo de postventa que calcula el
transfer, docs/ARCHITECTURE.md#regla-p5). Solo se descarta la que no tiene
ninguna de las dos. Antes, fuera las de código con N+ dígitos seguidos
(F-039, #regla-seis-digitos); después, la obra VAR no se ofrece como normal
y sus partidas entran como filas propias (`entradas_var`, #regla-var).

Empresas (F-032): no se depuran; `resumir_empresas` solo las cuenta para
el preview.

Las comparaciones son normalizadas (minúsculas, sin acentos).
"""
from __future__ import annotations

import re

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from domain.empresas import empresa_de_baja
from domain.models import ResultadoUniversoVar
from domain.normalizacion import entero_o_none as _entero
from domain.normalizacion import normalizar
from domain.obras import codigo_entrada, ide_entrada, tiene_digitos_seguidos


#: Clave con la que se cuentan los descartes por fecha de baja del recurso
#: anterior a la ventana de bajas (F-026 R13).
MOTIVO_BAJA_ANTERIOR = "(baja anterior a la ventana)"

#: Columnas que la consulta de empleados trae solo para depurar: no se
#: persisten, así que no llegan al upsert. `empresa` y `fecha_baja` sí.
_AUXILIARES = ("cif", "estado_recurso", "baja_laboral")


@dataclass(frozen=True)
class CriterioActivoRecurso:
    """Cuándo un recurso cuenta como inactivo (config.yaml, sync.empleados).

    `estados_excluidos`: literales de `conest.res` del recurso que lo dejan
    fuera (subcadena normalizada, como en obras).
    `excluir_baja_anterior_a_ventana`: descartar el recurso con fecha de
    baja anterior a la ventana (F-026 R13). `activo` es el interruptor
    general (`filtro_estado_recurso`). Vacío = nadie queda fuera por estado
    (F-023 R16).
    """

    estados_excluidos: tuple[str, ...] = ()
    excluir_baja_anterior_a_ventana: bool = False
    activo: bool = True


#: Criterio vacío, compartido como valor por defecto (es inmutable).
CRITERIO_VACIO = CriterioActivoRecurso()


@dataclass
class ResultadoDepuracion:
    filas: list[dict[str, Any]]
    brutos: int = 0
    excluidos_filtro: int = 0
    excluidos_sin_codigo_mes: int = 0
    excluidos_detalle: Counter = field(default_factory=Counter)
    excluidos_estado_recurso: Counter = field(default_factory=Counter)
    con_baja_laboral: int = 0
    incluidos_con_baja: int = 0
    posible_misma_persona: list[list[str]] = field(default_factory=list)
    # Obras (F-025): en el universo de postventa, y de esas, las excluidas
    # por estado que solo se ofrecen como postventa.
    admiten_postventa: int = 0
    solo_postventa: int = 0


# ----------------------------------------------------------------------
# Empleados
# ----------------------------------------------------------------------
def depurar_empleados(
    filas: list[dict[str, Any]],
    categorias_incluidas: list[str],
    filtro_activo: bool,
    exigir_codigo_mes: bool = True,
    criterio: CriterioActivoRecurso = CRITERIO_VACIO,
    baja_desde: int | None = None,
) -> ResultadoDepuracion:
    """Depura las filas de `sync.empleados.sql` (una por recurso).

    `baja_desde` es la ventana de bajas (`AAAAMMDD`,
    `domain.vigencia.inicio_ventana_baja`); sin ella no se descarta a nadie
    por su fecha de baja.
    """
    resultado = ResultadoDepuracion(filas=[], brutos=len(filas))
    incluidas = {normalizar(c) for c in categorias_incluidas}
    # Filas brutas incluidas: el aviso de R4 necesita el `cif`, que no se
    # persiste.
    incluidas_brutas: list[dict[str, Any]] = []
    for fila in filas:
        # 0) Recurso inactivo según el criterio configurado.
        motivo = _motivo_recurso_inactivo(fila, criterio, baja_desde)
        if motivo:
            resultado.excluidos_estado_recurso[motivo] += 1
            continue
        # 1) Código de hora mensual (criterio principal).
        if exigir_codigo_mes and not _cod_mes(fila):
            resultado.excluidos_sin_codigo_mes += 1
            resultado.excluidos_detalle["(sin código de hora mensual)"] += 1
            continue
        # 2) Categorías incluidas (opcional).
        categoria = fila.get("categoria")
        if filtro_activo and normalizar(categoria) not in incluidas:
            resultado.excluidos_filtro += 1
            resultado.excluidos_detalle[str(categoria or "(sin categoría)")] += 1
            continue
        # 3) Recuentos informativos: el activo lo decide el recurso.
        if (_entero(fila.get("baja_laboral")) or 0) > 0:
            resultado.con_baja_laboral += 1
        if (_entero(fila.get("fecha_baja")) or 0) > 0:
            resultado.incluidos_con_baja += 1
        incluidas_brutas.append(fila)
        limpia = dict(fila)
        for columna in _AUXILIARES:
            limpia.pop(columna, None)
        resultado.filas.append(limpia)

    resultado.posible_misma_persona = _posible_misma_persona(incluidas_brutas)
    resultado.filas.sort(key=lambda f: normalizar(str(f.get("nombre"))))
    return resultado


def _motivo_recurso_inactivo(
    fila: dict[str, Any],
    criterio: CriterioActivoRecurso,
    baja_desde: int | None,
) -> str | None:
    """Clave del recuento si el recurso está inactivo; None si no lo está."""
    if not criterio.activo:
        return None
    estado = normalizar(str(fila.get("estado_recurso") or ""))
    excluidos = [normalizar(e) for e in criterio.estados_excluidos]
    if any(patron and patron in estado for patron in excluidos):
        return str(fila.get("estado_recurso"))
    fecha_baja = _entero(fila.get("fecha_baja")) or 0
    if (criterio.excluir_baja_anterior_a_ventana and baja_desde is not None
            and 0 < fecha_baja < baja_desde):
        return MOTIVO_BAJA_ANTERIOR
    return None


def _documento(fila: dict[str, Any]) -> str:
    """DNI de la ficha o, sin él, documento del recurso (`cif`), sin
    espacios, guiones ni puntos y en mayúsculas. Vacío si no hay ninguno."""
    for columna in ("dni", "cif"):
        valor = re.sub(r"[\s\-.]", "", str(fila.get(columna) or "")).upper()
        if valor:
            return valor
    return ""


def _posible_misma_persona(incluidas: list[dict[str, Any]]) -> list[list[str]]:
    """Grupos (≥ 2) de códigos incluidos con la misma empresa y el mismo
    documento (F-026 R4). Solo avisa, no excluye; nunca agrupa por nombre
    (homónimos) ni a quien no trae documento."""
    grupos: dict[tuple[int | None, str], list[str]] = {}
    for fila in incluidas:
        documento = _documento(fila)
        if documento:
            clave = (_entero(fila.get("empresa")), documento)
            grupos.setdefault(clave, []).append(str(fila.get("cod")))
    return sorted(sorted(cods) for cods in grupos.values() if len(cods) > 1)


def _cod_mes(fila: dict[str, Any]) -> str:
    """Código de hora mensual del recurso (M*), vacío si no tiene."""
    valor = str(fila.get("cod_hora_mes") or "").strip()
    return valor if valor.upper().startswith("M") else ""


# ----------------------------------------------------------------------
# Obras
# ----------------------------------------------------------------------
def descartar_por_codigo(
    filas: list[dict[str, Any]], n: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(quedan, descartadas): fuera toda obra cuyo `cod`, tal como llega,
    contiene `n` o más dígitos seguidos (F-039,
    docs/ARCHITECTURE.md#regla-seis-digitos). Con `n <= 0`, ninguna."""
    quedan: list[dict[str, Any]] = []
    descartadas: list[dict[str, Any]] = []
    for fila in filas:
        cae = tiene_digitos_seguidos(str(fila.get("cod")), n)
        (descartadas if cae else quedan).append(fila)
    return quedan, descartadas


def depurar_obras(
    filas: list[dict[str, Any]],
    estados_excluidos: list[str],
    filtro_activo: bool,
    universo: frozenset[int],
    no_normales: frozenset[int] = frozenset(),
) -> ResultadoDepuracion:
    """Marca cada obra con `activa` (por estado) y `admite_postventa` (su
    `ide` está en `universo`); descarta solo la que no tiene ninguna, y la
    cuenta como excluida por estado, como antes de F-025 (R13-R14).

    La obra de `no_normales` (la obra VAR, F-039 D1) sale siempre, con
    `activa = False` sea cual sea su estado: no se ofrece como obra normal."""
    resultado = ResultadoDepuracion(filas=[], brutos=len(filas))
    excluidos = [normalizar(e) for e in estados_excluidos if normalizar(e)]

    for fila in filas:
        # `int` como en `sincronizar`: un `ide` en texto no puede quedarse
        # fuera del universo sin que nada falle (review 1 de F-025).
        ide = int(fila["ide"])
        normal = ide not in no_normales
        estado = normalizar(str(fila.get("estado_sigrid") or ""))
        activa = normal and not (
            filtro_activo and any(p in estado for p in excluidos))
        admite = ide in universo
        if normal and not (activa or admite):
            resultado.excluidos_filtro += 1
            resultado.excluidos_detalle[str(fila.get("estado_sigrid"))] += 1
            continue
        resultado.admiten_postventa += admite
        resultado.solo_postventa += admite and not activa
        resultado.filas.append({**fila, "activa": activa,
                                "admite_postventa": admite})
    return resultado


def entradas_var(uvar: ResultadoUniversoVar) -> list[dict[str, Any]]:
    """Una fila de `obra` por partida del universo VAR, con las claves que
    guarda `sincronizar` (F-039, R13, docs/ARCHITECTURE.md#regla-var). Sin
    obra VAR, ninguna."""
    if uvar.obra_ide is None:
        return []
    return [
        {
            "ide": ide_entrada(p.ide),
            "cod": codigo_entrada(str(uvar.obra_cod), p.cod),
            "descripcion": p.res,
            "empresa": uvar.empresa,
            "estado_sigrid": None,
            "activa": True,
            "admite_postventa": False,
            "registro_obra_ide": uvar.obra_ide,
            "registro_obra_cod": uvar.obra_cod,
            "registro_paride": p.ide,
        }
        for p in uvar.partidas
    ]


def resumir_empresas(filas: list[dict[str, Any]]) -> dict[str, Any]:
    """Lo que el preview enseña del catálogo `auxemp` (F-032).

    `leidas` son todas las filas; las que no traen `numemp` no se guardan
    (`sin_numero`). `de_baja` lista los números de las de baja o
    desactivadas, que el selector enseñará marcadas. `nombres` va con la
    clave en texto, como el resto de desgloses del preview.
    """
    nombres: dict[str, Any] = {}
    de_baja: list[int] = []
    sin_numero = 0
    for fila in filas:
        numemp = _entero(fila.get("numemp"))
        if numemp is None:
            sin_numero += 1
            continue
        nombres[str(numemp)] = fila.get("nombre")
        if empresa_de_baja(_entero(fila.get("fecbaj")),
                           _entero(fila.get("desact"))):
            de_baja.append(numemp)
    return {
        "leidas": len(filas),
        "sin_numero": sin_numero,
        "de_baja": sorted(de_baja),
        "nombres": nombres,
    }
