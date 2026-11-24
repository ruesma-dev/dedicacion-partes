# application/estado_partida.py
"""El estado de la partida de una línea o subfila del cuadrante (F-074, R12-
R14; design §3; docs/ARCHITECTURE.md#regla-partida).

La api decide y el front pinta (R19): estas funciones puras dicen qué claves
de la propuesta publica cada línea y cada subfila, a partir de lo guardado
(elegida, fija, propuesta guardada, la partida de postventa de su obra) y de
las `Marcas` de la cola de propuestas del mes (en cola o en la memoria de
«sin propuesta», con su motivo), leídas de UNA foto de la cola.

Orden (el de la celda, R17): elegida → fija → propuesta (guardada o, en
postventa, la de su obra) → pendiente → no encontrada con su motivo. Lo que
no aplica no sale: las claves nuevas, solo con valor. «sin calcular» no es
una marca: es el hueco que deja todo lo demás (lo pinta el front).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from domain.models import Linea, SubfilaVinculado

#: (trabajador_ide, obra_ide, es_postventa): una línea (F-057).
Pendiente = tuple[int, int, bool]
#: (trabajador_ide, obra_ide, es_postventa, vinculado_ide): una subfila.
PendienteSubfila = tuple[int, int, bool, int]

#: El método con el que se publica la partida de postventa de la obra.
METODO_POSTVENTA = "postventa"


@dataclass(frozen=True)
class Marcas:
    """La foto de la cola de propuestas de un periodo (F-074, R13, R14): las
    líneas y subfilas en cola o calculándose (`pendientes`) y las que están
    en la memoria de «sin propuesta», con su motivo (o None)."""

    pendientes: frozenset[Pendiente] = frozenset()
    no_encontradas: Mapping[Pendiente, str | None] = field(
        default_factory=dict)
    subfilas_pendientes: frozenset[PendienteSubfila] = frozenset()
    subfilas_no_encontradas: Mapping[PendienteSubfila, str | None] = field(
        default_factory=dict)


SIN_MARCAS = Marcas()


def _no_encontrada(motivo: str | None) -> dict[str, Any]:
    return {"propuesta_no_encontrada": True,
            **({"propuesta_motivo": motivo} if motivo else {})}


def estado_de_linea(trabajador_ide: int, ln: Linea,
                    marcas: Marcas = SIN_MARCAS) -> dict[str, Any]:
    """Las claves de la propuesta de la línea: `propuesta_cod/_res/_metodo`
    (las de siempre), `propuesta_pendiente` y, solo con valor,
    `propuesta_no_encontrada` y `propuesta_motivo`.

    - La de postventa sin elegida publica la partida de su obra con método
      `postventa` (R12); si la obra no casa, no encontrada con su motivo; si
      aún no la tiene (sync pendiente), ninguna marca.
    - La normal: la propuesta guardada; si no, pendiente (en la cola) o no
      encontrada (en la memoria), que son excluyentes (R13)."""
    clave = (trabajador_ide, ln.obra_ide, ln.es_postventa)
    out: dict[str, Any] = {"propuesta_cod": ln.propuesta_cod,
                           "propuesta_res": ln.propuesta_res,
                           "propuesta_metodo": ln.propuesta_metodo,
                           "propuesta_pendiente": clave in marcas.pendientes}
    if ln.partida_ide is not None or ln.partida_fija:
        return out
    if ln.es_postventa:
        # Nunca se encola ni guarda propuesta: la suya es la de su obra.
        tiene = ln.obra_pv_ide is not None
        out.update(propuesta_cod=ln.obra_pv_cod if tiene else None,
                   propuesta_res=ln.obra_pv_res if tiene else None,
                   propuesta_metodo=METODO_POSTVENTA if tiene else None)
        if not tiene and ln.obra_pv_motivo:
            out.update(_no_encontrada(ln.obra_pv_motivo))
        return out
    if ln.propuesta_ide is None and not out["propuesta_pendiente"] \
            and clave in marcas.no_encontradas:
        out.update(_no_encontrada(marcas.no_encontradas[clave]))
    return out


def estado_de_subfila(trabajador_ide: int, ln: Linea, v: SubfilaVinculado,
                      marcas: Marcas = SIN_MARCAS) -> dict[str, Any]:
    """Las claves de la propuesta de la subfila (R14): las de siempre y,
    solo con valor, `propuesta_pendiente` (en su cola),
    `propuesta_no_encontrada` y `propuesta_motivo` (en su memoria)."""
    out: dict[str, Any] = {"propuesta_cod": v.propuesta_cod,
                           "propuesta_res": v.propuesta_res,
                           "propuesta_metodo": v.propuesta_metodo}
    if v.partida_ide is not None or ln.partida_fija \
            or v.propuesta_ide is not None:
        return out
    clave = (trabajador_ide, ln.obra_ide, ln.es_postventa, v.vinculado_ide)
    if clave in marcas.subfilas_pendientes:
        out["propuesta_pendiente"] = True
    elif clave in marcas.subfilas_no_encontradas:
        out.update(_no_encontrada(marcas.subfilas_no_encontradas[clave]))
    return out
