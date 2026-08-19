# application/services/reglas_porcentajes.py
"""Reglas de negocio del registro de porcentajes en Sigrid.

Definidas por Administración (hilo de porcentajes, 25/07/2026):

  P1. Se registran SOLO los recursos que tienen código de hora MENSUAL
      ('M%': MENC, MCAP, MJEFO…) en su ficha (reshor). Nadie más.
  P2. La línea se escribe SIEMPRE en el ÚLTIMO día del mes (fec).
  P3. can = el PORCENTAJE SOBRE 1 (40 % -> 0.4). pre = importe mensual del
      recurso en reshor para ese código; tot = can × pre.
  P4. Si el mismo recurso ya tiene un registro con código M* y la misma
      partida en ese parte —aunque sea en OTRO día— es un conflicto: pisar
      lo sustituye (y de paso corrige la fecha).
  P5. La POSTVENTA se registra en la OBRA DE POSTVENTA (config
      POSTVENTA_OBRA_COD, hoy 'postventa-2'), imputando al CAPÍTULO
      (obrparpar) que corresponde a la obra original. Sin capítulo casado
      no se escribe (motivo claro en el preflight).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Optional

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


def campos_identidad(destino: str) -> tuple[str, ...]:
    """Campos que deciden si dos líneas del parte son la MISMA línea.

    Subconjunto de `CAMPOS_CLAVE`, según el destino de la línea. Es el único
    punto donde vive la decisión D2 de F-002: cuando Administración conteste
    qué cuenta como conflicto en la obra normal, se cambia aquí y en ningún
    otro sitio.
    """
    if destino == "postventa":
        return CAMPOS_CLAVE
    return tuple(campo for campo in CAMPOS_CLAVE if campo != "paride")


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

    Se compara campo a campo con `campos_identidad(accion.destino)`: no
    reimplementa el criterio, lo deriva.
    """
    if existente.synckey and existente.synckey in mias:
        return False
    for campo in campos_identidad(accion.destino):
        if campo in IMPLICITOS_DEL_PARTE:
            continue
        if _DE_LINEA[campo](existente) != _DE_ACCION[campo](accion):
            return False
    return True


class ReglasPorcentajes:
    """Decide, para cada línea, si se escribe y con qué código/importe.

    ``capitulo_postventa``: capítulo de la obra original dentro de la obra
    de postventa (dict con ide/cod/res), o None si no aplica/no se casó.
    ``motivo_postventa``: por qué no hay capítulo (obra postventa no
    encontrada, capítulo sin casar…) — se usa como motivo de omisión.
    """

    def __init__(
        self,
        horas_por_recurso: dict[int, list[HoraRecurso]],
        *,
        postventa_registrar: bool = True,
        capitulo_postventa: Optional[dict] = None,
        motivo_postventa: Optional[str] = None,
    ) -> None:
        self._horas = horas_por_recurso
        self._postventa = bool(postventa_registrar)
        self._capitulo = capitulo_postventa
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
            # P5: destino obra de postventa + capítulo de la obra original.
            if not self._postventa:
                return omitir(MOTIVO_POSTVENTA_OFF)
            if self._capitulo is None:
                return omitir(self._motivo_pv
                              or "capítulo de postventa sin resolver")
            destino = "postventa"
            paride = int(self._capitulo["ide"])
            partida_cod = self._capitulo.get("cod")

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
