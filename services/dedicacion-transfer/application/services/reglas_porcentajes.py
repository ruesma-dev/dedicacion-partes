# application/services/reglas_porcentajes.py
"""Reglas de negocio del registro de porcentajes en Sigrid.

Aquí se IMPLEMENTAN; no se enuncian. La única fuente normativa es
`docs/ARCHITECTURE.md` § Semántica de dominio imprescindible:

  P1 -> ARCHITECTURE.md#regla-p1        qué recursos entran
  P2 -> ARCHITECTURE.md#regla-p2        qué fecha lleva la línea
  P3 -> ARCHITECTURE.md#regla-p3        en qué escala viaja el porcentaje
  P4 -> ARCHITECTURE.md#regla-conflicto Regla A: qué es «la misma línea»
     -> ARCHITECTURE.md#regla-capacidad Regla B: cuánta jornada cabe
  P5 -> ARCHITECTURE.md#regla-p5        destino de la postventa

Qué vive en este módulo, y por qué junto:

  - los MOTIVOS de omisión, que es el texto que el humano acaba leyendo;
  - la IDENTIDAD de una línea del parte (`CAMPOS_CLAVE`, `campos_identidad`,
    `clave_conflicto`, `criterio_choque`);
  - la CAPACIDAD de un recurso en un parte (`evaluar_capacidad` y
    compañía).

Las dos últimas son funciones puras: sin I/O, sin `settings` y sin cliente.
El valor del código de la obra de postventa NO se cita: vive en el ajuste
`POSTVENTA_OBRA_COD` del `.env`.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import NamedTuple, Optional

from domain.models.registro_models import (
    AccionLinea, HoraRecurso, LineaEntrada, LineaSigrid,
)

logger = logging.getLogger(__name__)

MOTIVO_SIN_RECURSO = "sin recurso en Sigrid para el empleado"
MOTIVO_SIN_MENSUAL = (
    "el recurso no tiene código de hora mensual (M*) en Sigrid: "
    "no se registra por porcentaje"
)
MOTIVO_PORCENTAJE = "porcentaje fuera de rango (debe ser > 0 y <= 1)"
#: Se formatea con `paride`. Cabe de sobra en los 300 caracteres a los que
#: `dedicacion-api` recorta `asignacion.sigrid_motivo`.
MOTIVO_PARTIDA_PV_NO_HOJA = (
    "la partida {paride} indicada a mano no es una partida hoja activa del "
    "presupuesto de la obra de postventa: no se escribe"
)
MOTIVO_POSTVENTA_OFF = (
    "línea de postventa: registro de postventa desactivado "
    "(POSTVENTA_REGISTRAR=false)"
)


# ------------------------------------------------------------------ #
#  Identidad de una línea en el parte: qué es «la misma línea»
# ------------------------------------------------------------------ #
# Este bloque es el ÚNICO sitio del código donde se decide qué cuenta como
# conflicto (ver ARCHITECTURE `#regla-conflicto`). Antes la decisión estaba
# repartida entre la clave de `AccionLinea` y el filtro del pipeline, y las
# dos versiones se habían desalineado sin que nadie lo notara.

#: Campos que componen la CLAVE del conflicto, en el orden en que se
#: serializa. La clave viaja al front y vuelve en `pisar_claves`: cambiar
#: este orden invalida las confirmaciones que estén en vuelo.
CAMPOS_CLAVE: tuple[str, ...] = (
    "recurso", "periodo", "hora", "paride",
)

#: Campos de `CAMPOS_CLAVE` que NO se comparan contra la línea que ya está
#: en Sigrid porque el propio parte ya los fija (un parte es de una obra y
#: un mes). Estar en esta lista es una decisión explícita: un campo que no
#: esté ni aquí ni en `_DE_LINEA` hace fallar a `criterio_choque` en vez de
#: dejar de compararse en silencio.
IMPLICITOS_DEL_PARTE: frozenset[str] = frozenset({"periodo"})


def _entero(valor) -> int:
    """`None` y ausencia valen lo mismo que 0: Sigrid guarda 0, no NULL."""
    return int(valor or 0)


#: Cómo se lee cada campo de la identidad en la línea que vamos a escribir.
_DE_ACCION: dict[str, Callable[[AccionLinea], object]] = {
    "recurso": lambda a: _entero(a.recurso_ide),
    "periodo": lambda a: f"{int(a.ano)}{int(a.mes):02d}",
    "hora": lambda a: _entero(a.hora_ide),
    "paride": lambda a: _entero(a.paride),
}

#: Cómo se lee cada campo en la línea que YA está en Sigrid. No tiene
#: "periodo" a propósito: ver `IMPLICITOS_DEL_PARTE`.
_DE_LINEA: dict[str, Callable[[LineaSigrid], object]] = {
    "recurso": lambda ls: _entero(ls.reside),
    "hora": lambda ls: _entero(ls.horide),
    "paride": lambda ls: _entero(ls.paride),
}


def campos_identidad() -> tuple[str, ...]:
    """Campos que deciden si dos líneas del parte son la MISMA línea.

    Los CUATRO de `CAMPOS_CLAVE`, siempre: recurso, periodo, código de hora
    y partida (D2, 2026-08-19; ver `ARCHITECTURE.md#regla-conflicto`). No
    recibe el destino porque el destino ya no decide nada — la obra normal y
    la de postventa comparten criterio—, y un parámetro que no decide es una
    mentira en la firma y una rama que ningún test puede matar.

    Es el único punto del código donde vive esa decisión: la clave del
    conflicto y el criterio de choque se derivan de aquí, no la reimplementan.
    """
    return CAMPOS_CLAVE


def clave_conflicto(accion: AccionLinea) -> str:
    """Clave estable con la que se agrupa y se confirma un conflicto.

    Se construye SIEMPRE con `CAMPOS_CLAVE` completos, sea cual sea el
    destino, porque la cadena tiene que poder compararse entre líneas de
    destinos distintos y sobrevivir a un viaje de ida y vuelta al front.
    """
    return "|".join(str(_DE_ACCION[campo](accion)) for campo in CAMPOS_CLAVE)


def criterio_choque(existente: LineaSigrid, accion: AccionLinea, *,
                    mias: set[str]) -> bool:
    """¿`existente` es la misma línea lógica que `accion`?

    `mias` son las `synckey` de las líneas de esta misma ejecución: lo que
    escribimos nosotros no choca con nosotros mismos, se reescribe.

    Se compara campo a campo con `campos_identidad()`: no reimplementa el
    criterio, lo deriva.
    """
    if existente.synckey and existente.synckey in mias:
        return False
    for campo in campos_identidad():
        if campo in IMPLICITOS_DEL_PARTE:
            continue
        if _DE_LINEA[campo](existente) != _DE_ACCION[campo](accion):
            return False
    return True


# ------------------------------------------------------------------ #
#  Capacidad de un recurso en un parte: cuánta jornada cabe
# ------------------------------------------------------------------ #
# Ver ARCHITECTURE `#regla-capacidad`. Es una propiedad DEL CONJUNTO de
# líneas de un recurso en un parte, no de una línea suelta, y por eso no es
# un método de `ReglasPorcentajes` (que decide línea a línea y no ve lo que
# ya hay en Sigrid). No decide qué se escribe: informa, y el humano confirma.

#: La jornada completa de una persona en un mes.
LIMITE_CAPACIDAD: float = 1.0

#: Tolerancia de la comparación de jornada. Es la MISMA que usa el cuadrante
#: en dedicacion-api/domain/estados.py (_EPSILON = Decimal("0.005") sobre
#: escala 0-100), convertida a la escala 0-1 de Sigrid: 0.005 / 100.
#: NO es un número redondo por elección: si se cambia, el front y Sigrid
#: discrepan en el último decimal y un cuadrante que la API da por OK se
#: convierte aquí en una sobrecarga fantasma. Cambiar una obliga a cambiar
#: la otra (lo vigila test_f002_r26_la_tolerancia_es_la_del_cuadrante).
EPSILON_CAPACIDAD: float = 0.00005

#: Prefijo de la clave con la que se confirma una sobrecarga. Ninguna clave
#: de pisado puede empezar por él: la de pisado empieza por el `ide` del
#: recurso, que es un entero.
PREFIJO_CLAVE_SOBRECARGA: str = "sobrecarga:"

#: Se formatea con total / existente / n / nueva. Corto a propósito: cabe en
#: los 300 caracteres a los que dedicacion-api recorta `sigrid_motivo`.
MOTIVO_SOBRECARGA = (
    "sobrecarga: el trabajador sumaría {total:.2%} en el parte "
    "(ya tiene {existente:.2%} en {n} línea(s) M*, se añade {nueva:.2%}); "
    "confirma para escribirlo igualmente"
)


class Capacidad(NamedTuple):
    """Jornada de un recurso en un parte, con el desglose que la justifica."""
    existente: float                    # jornada ya ocupada que cuenta
    nueva: float                        # jornada que vamos a añadir
    total: float                        # existente + nueva
    exceso: float                       # total - LIMITE (puede ser negativo)
    sobrecarga: bool                    # exceso > EPSILON_CAPACIDAD
    contadas: tuple[LineaSigrid, ...]   # las existentes que ha sumado


def es_linea_mensual(linea: LineaSigrid) -> bool:
    """¿Es una línea de jornada mensual? Cualquier código `M*` vale.

    El límite es la jornada de la PERSONA, no un concepto concreto: `MENC` y
    `MCAP` del mismo trabajador en el mismo parte compiten por el mismo mes.
    Las horas de convenio (`H*`) no cuentan: van en otra escala.
    """
    return (linea.hora_codigo or "").upper().startswith("M")


def _can(valor) -> float:
    """`can` ausente vale 0, como en el resto del módulo."""
    return float(valor or 0.0)


def evaluar_capacidad(
    existentes: list[LineaSigrid],
    nuevas: list[AccionLinea],
    *, mias: set[str], pisadas: set[int],
) -> Capacidad:
    """Jornada del recurso en un parte. NO decide qué se escribe: informa.

    De `existentes` suma las que cumplen LAS TRES condiciones: son mensuales,
    su `ide` **no** está en `pisadas` (van a ser sustituidas, así que no van
    a convivir con las nuestras) y su `synckey` **no** está en `mias` (son de
    esta misma ejecución, y ya están representadas por la acción pendiente).
    De `nuevas` suma los `can`.

    `pisadas` llega con TODOS los pisados propuestos dados por confirmados:
    es la única hipótesis segura, porque cualquier otra combinación escribe
    estrictamente menos (ARCHITECTURE `#regla-capacidad`).
    """
    contadas = tuple(
        ls for ls in existentes
        if es_linea_mensual(ls)
        and ls.ide not in pisadas
        and not (ls.synckey and ls.synckey in mias)
    )
    existente = sum(_can(ls.can) for ls in contadas)
    nueva = sum(_can(a.can) for a in nuevas)
    total = existente + nueva
    exceso = total - LIMITE_CAPACIDAD
    return Capacidad(existente=existente, nueva=nueva, total=total,
                     exceso=exceso, sobrecarga=exceso > EPSILON_CAPACIDAD,
                     contadas=contadas)


def clave_sobrecarga(accion: AccionLinea) -> str:
    """Clave con la que se confirma una sobrecarga: una por recurso y parte.

    La partida NO entra: la sobrecarga la provoca el conjunto de líneas del
    trabajador, no una en concreto. Se lee con los MISMOS lectores que
    `clave_conflicto` para que las dos no puedan divergir.
    """
    recurso = _DE_ACCION["recurso"](accion)
    periodo = _DE_ACCION["periodo"](accion)
    return f"{PREFIJO_CLAVE_SOBRECARGA}{recurso}|{periodo}"


class ReglasPorcentajes:
    """Decide, para cada línea, si se escribe y con qué código/importe.

    ``partida_postventa``: la partida HOJA de la obra de postventa que
    corresponde a la obra original (dict con ide/cod/res), o None si no
    aplica o no se casó. Se llamaba `capitulo_postventa` cuando el
    repositorio creía que el destino era un capítulo (ver
    `ARCHITECTURE.md#regla-p5`).
    ``motivo_postventa``: por qué no hay partida (obra de postventa no
    encontrada, código sin casar…) — se usa como motivo de omisión.
    """

    def __init__(
        self,
        horas_por_recurso: dict[int, list[HoraRecurso]],
        *,
        postventa_registrar: bool = True,
        partida_postventa: Optional[dict] = None,
        motivo_postventa: Optional[str] = None,
    ) -> None:
        self._horas = horas_por_recurso
        self._postventa = bool(postventa_registrar)
        self._partida = partida_postventa
        self._motivo_pv = motivo_postventa

    def decidir(self, linea: LineaEntrada) -> AccionLinea:
        base = dict(
            registro_id=linea.registro_id, ano=int(linea.ano),
            mes=int(linea.mes), fecha_int=linea.fecha_int,
            nombre=linea.nombre, empleado_ide=linea.empleado_ide,
            recurso_ide=linea.recurso_ide, es_postventa=linea.es_postventa,
        )

        def omitir(motivo: str) -> AccionLinea:
            return AccionLinea(accion="omitir", motivo=motivo, **base)

        destino, paride, partida_cod = "obra", 0, None
        if linea.es_postventa:
            # P5 (ver ARCHITECTURE.md#regla-p5).
            if not self._postventa:
                return omitir(MOTIVO_POSTVENTA_OFF)
            if self._partida is None:
                return omitir(self._motivo_pv
                              or "partida de postventa sin resolver")
            destino = "postventa"
            paride = int(self._partida["ide"])
            partida_cod = self._partida.get("cod")

        if not linea.recurso_ide:
            return omitir(MOTIVO_SIN_RECURSO)

        # P3: porcentaje sobre 1.
        try:
            porcentaje = float(linea.porcentaje)
        except (TypeError, ValueError):
            return omitir(MOTIVO_PORCENTAJE)
        if not (0.0 < porcentaje <= 1.0):
            return omitir(f"{MOTIVO_PORCENTAJE}: {linea.porcentaje!r}")

        # P1: solo recursos con código mensual.
        mensuales = [
            h for h in self._horas.get(int(linea.recurso_ide), [])
            if h.es_mensual
        ]
        if not mensuales:
            return omitir(MOTIVO_SIN_MENSUAL)
        hora = sorted(mensuales, key=lambda h: h.cod or "")[0]
        if len(mensuales) > 1:
            logger.info(
                "[reglas] recurso %s con varios códigos M*: %s -> se usa %s",
                linea.recurso_ide, [h.cod for h in mensuales], hora.cod,
            )

        can = round(porcentaje, 4)
        pre = float(hora.pre or 0.0)
        return AccionLinea(
            accion="escribir", hora_ide=hora.horide, hora_codigo=hora.cod,
            can=can, pre=pre, tot=round(can * pre, 2), destino=destino,
            paride=paride, partida_cod=partida_cod, **base,
        )
