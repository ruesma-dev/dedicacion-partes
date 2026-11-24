# application/services/partida_definida.py
"""F-074 · La partida DEFINIDA al registrar y el motivo del «no encuentra».

Al registrar ya no se casan partidas (`docs/ARCHITECTURE.md#regla-partida`):
cada línea y cada subfila llegan con su partida DEFINIDA (la elegida, la
fija VAR, la propuesta guardada o, en postventa, la de su obra) y el
preflight solo la valida por `ide`. La regla de la propuesta
(`propuesta_partida`, `reglas_vinculados.partida_del_vinculado`,
`universo_postventa.casar_postventa`) corre en segundo plano y NO se toca
aquí: este módulo solo decide con lo que ya viene.

Módulo PURO: sin I/O, sin cliente y sin ajustes.

- `partida_definida_del_vinculado` (R2, R4, R5): la de una subfila.
- `motivo_sin_propuesta` (R9): por qué una línea de obra normal no tiene
  propuesta, con el presupuesto ya leído por la propia propuesta.
- Los motivos de omisión nuevos de F-074, que el humano lee en el modal y
  en `asignacion.sigrid_motivo` (todos caben en sus 300 caracteres).

Vive aparte de `propuesta_partida.py` y `reglas_porcentajes.py` porque esos
dos módulos son la regla y sus motivos de siempre, y F-074 no los cambia
(design §6).
"""
from __future__ import annotations

from dataclasses import dataclass

from application.services.partida_catalog import PartidaNodo
from application.services.propuesta_partida import Propuesta
from application.services.reglas_vinculados import (
    METODO_MANUAL,
    METODO_TITULAR,
    METODOS_PROPUESTA_PROPIA,
    MOTIVO_ELEGIDA_NO_VALIDA,
    PartidaElegida,
    PartidaTitular,
    PartidaVinculado,
    va_con_el_titular,
)

#: R4 (D4): la propuesta guardada de una línea de obra normal que ya no es
#: hoja activa del presupuesto de su obra. Se formatea con `cod` y `obra`.
MOTIVO_PROPUESTA_NO_VALIDA = (
    "la partida {cod} propuesta no es una partida hoja activa del "
    "presupuesto de la obra {obra}: no se escribe; elige otra partida")
#: R4 (D4): la partida de postventa de la obra (la del universo, guardada en
#: el sync) que ya no es hoja activa del presupuesto de la obra de
#: postventa. Se formatea con `cod`.
MOTIVO_PROPUESTA_PV_NO_VALIDA = (
    "la partida de postventa {cod} de la obra no es una partida hoja activa "
    "del presupuesto de la obra de postventa: no se escribe; elige otra "
    "partida o sincroniza Sigrid")
#: R5 (`#regla-p5`): línea de postventa sin partida definida (ni elegida ni
#: la de su obra: la obra no casa o aún no se ha sincronizado).
MOTIVO_PV_SIN_DEFINIDA = (
    "línea de postventa sin partida: ni elegida ni la de su obra en el "
    "universo de postventa (no casa o falta sincronizar Sigrid): no se "
    "escribe; elige una partida")
#: R4 (D4): la propuesta guardada de una subfila que ya no vale.
MOTIVO_GUARDADA_VINCULADO_NO_VALIDA = (
    "la partida {cod} propuesta para el recurso vinculado no es una partida "
    "hoja activa del presupuesto: no se escribe; elige otra partida")
#: R5: por qué una subfila no tiene partida definida (va al aviso de «sin
#: partida» del vinculado, `AVISO_SIN_PARTIDA_VINCULADO`).
POR_QUE_SIN_DEFINIDA = "ni elegida ni propuesta"

#: R9 (D6 b): por qué una línea de obra normal no tiene propuesta.
MOTIVO_SIN_HOJAS = ("el presupuesto de la obra no tiene ninguna partida "
                    "hoja activa")
MOTIVO_NINGUN_PASO = ("ningún paso de la regla da partida: ni el parte "
                      "anterior en la obra, ni la categoría o el nombre, ni "
                      "el último parte en otra obra")
#: R9: por qué una subfila no tiene propuesta cuando va con su titular.
MOTIVO_TITULAR_SIN_PARTIDA = ("la subfila va con la partida del trabajador "
                              "y la línea del trabajador no tiene")
MOTIVO_TITULAR_NO_VALIDA = ("la partida elegida del trabajador no es hoja "
                            "activa del presupuesto: la subfila sigue al "
                            "trabajador")


@dataclass(frozen=True)
class DefinidaVinculado:
    """La partida definida de una subfila (`partida`, la misma forma que la
    de la regla) y, si se omite porque la definida no vale, su código
    (`no_valida`, R4)."""
    partida: PartidaVinculado
    no_valida: str | None = None


def _codigo(cod: str | None, paride: int) -> str:
    """El código con el que se nombra una partida: el suyo o su `ide`."""
    return cod or str(int(paride))


def partida_definida_del_vinculado(
    titular: PartidaTitular,
    elegida: PartidaElegida | None,
    elegida_valida: bool,
    guardada: Propuesta | None,
    guardada_valida: bool,
) -> DefinidaVinculado:
    """R2, R4, R5 en este orden: la elegida (si no vale, omitida con su
    código); la del titular si va a postventa, VAR o partida no `CI*`
    (F-044 R17: una derivación, no una búsqueda); la propuesta guardada de
    método PROPIO (F-068 R16; la de método `titular` no cuenta: o va con el
    titular o no hay definida), omitida con su código si no vale; si no,
    sin partida. Nunca propone otra."""
    if elegida is not None:
        if not elegida_valida:
            cod = _codigo(elegida.cod, elegida.paride)
            return DefinidaVinculado(
                PartidaVinculado(
                    motivo=MOTIVO_ELEGIDA_NO_VALIDA.format(cod=cod),
                    omitir=True),
                no_valida=cod)
        return DefinidaVinculado(PartidaVinculado(
            paride=int(elegida.paride), cod=elegida.cod, res=elegida.res,
            metodo=METODO_MANUAL))
    if va_con_el_titular(titular):
        return DefinidaVinculado(PartidaVinculado(
            paride=int(titular.paride or 0), cod=titular.cod,
            res=titular.res, metodo=METODO_TITULAR))
    if guardada is not None and guardada.metodo in METODOS_PROPUESTA_PROPIA:
        if not guardada_valida:
            cod = _codigo(guardada.cod, guardada.paride)
            return DefinidaVinculado(
                PartidaVinculado(
                    motivo=MOTIVO_GUARDADA_VINCULADO_NO_VALIDA.format(
                        cod=cod),
                    omitir=True),
                no_valida=cod)
        return DefinidaVinculado(PartidaVinculado(
            paride=int(guardada.paride), cod=guardada.cod, res=guardada.res,
            metodo=guardada.metodo, origen=guardada.origen))
    return DefinidaVinculado(PartidaVinculado(motivo=POR_QUE_SIN_DEFINIDA,
                                              sin_partida=True))


def motivo_sin_propuesta(nodos: dict[int, PartidaNodo]) -> str:
    """R9 (D6 b): por qué `proponer_partida` no dio propuesta con este
    presupuesto: sin hojas activas, o ningún paso de la regla la da."""
    if not any(n.es_hoja and n.activa for n in nodos.values()):
        return MOTIVO_SIN_HOJAS
    return MOTIVO_NINGUN_PASO
