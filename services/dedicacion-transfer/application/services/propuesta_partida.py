# application/services/propuesta_partida.py
"""Partida PROPUESTA de una línea de obra normal sin partida elegida.

Implementa `docs/ARCHITECTURE.md#regla-partida` (F-050); la regla se enuncia
allí, no aquí. Módulo PURO: recibe el presupuesto de la obra (los nodos de
`partida_catalog`) y el historial de líneas `M*` del recurso ya leídos.

La propuesta es la del primer paso que dé una, en el orden a → c → b
(F-055 R38, D10 del 2026-10-14; en F-050 era a → b → c):

  a. PARTE ANTERIOR (`parte_anterior`): el mes más reciente con líneas del
     recurso en ESTA obra; gana la partida con más `can` sumado.
  c. CASAMIENTO por nombre y categoría (`resolver_normal`, `auto_*`).
  b. ÚLTIMO PARTE (`ultimo_parte`): el mes más reciente con líneas del
     recurso en OTRA obra; gana el par (código, descripción) con más `can`,
     trasladado a esta obra si casa con UNA sola hoja activa. Como el
     casamiento casi siempre da algo, (b) solo actúa cuando no casa nada.

Un empate, o un traslado con cero o varias hojas, hace que ese paso no
proponga: nunca «la primera». Toda propuesta es hoja activa del presupuesto.

El MAYOR (CD, CI, CP u OTRO) de una partida se toma de la RAÍZ de la que
cuelga, no de `categoria` (que mira antes la descripción de la propia hoja y
falla bajo `CD`: design §5.1 de F-050). `categoria` no se toca: es de la
copia cerrada de `partes`.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from application.services import text_match as tm
from application.services.partida_catalog import (
    PartidaNodo,
    clasifica_categoria,
)
from application.services.partida_matcher import ambito_categoria
from application.services.partida_resolver import resolver_normal

#: R20: una partida elegida que ya no es hoja activa del presupuesto de la
#: obra de origen no se escribe. Cabe en los 300 caracteres de
#: `asignacion.sigrid_motivo`.
MOTIVO_PARTIDA_NO_HOJA = (
    "la partida {cod} elegida no es una partida hoja activa del presupuesto "
    "de la obra {obra}: no se escribe; elige otra partida")

_TROZOS = re.compile(r"[0-9]+|[^0-9]+")


@dataclass(frozen=True)
class LineaHistorial:
    """Una línea `M*` con partida de un parte de trabajo (`hmores`)."""
    reside: int
    obride: int
    obra_cod: str | None
    parte_cod: str | None
    ano: int
    mes: int
    can: float
    paride: int
    par_cod: str | None
    par_res: str | None


@dataclass(frozen=True)
class Propuesta:
    paride: int
    cod: str | None
    res: str | None
    metodo: str            # parte_anterior | ultimo_parte | auto_* | postventa
    origen: str | None = None


def clave_orden_codigo(cod: str | None) -> tuple:
    """Orden natural de un código: los grupos de dígitos como enteros y el
    resto en mayúsculas (`CI.1.9` antes que `CI.1.10`). Cada trozo lleva
    delante si es texto (`True`) o número (`False`): así nunca se compara un
    número con un texto, y los números van antes."""
    return tuple((False, int(t)) if t.isascii() and t.isdigit()
                 else (True, t.upper())
                 for t in _TROZOS.findall((cod or "").strip()))


def ventana(ano: int, mes: int, meses_atras: int) -> tuple[int, int]:
    """(desde, hasta) en AAAAMM: del periodo, incluido, hacia atrás."""
    total = int(ano) * 12 + int(mes) - 1 - int(meses_atras)
    return (total // 12) * 100 + total % 12 + 1, int(ano) * 100 + int(mes)


def _maximo_unico(sumas: dict) -> object:
    """La clave con más suma si es la única; con empate, None."""
    redondeadas = {k: round(v, 6) for k, v in sumas.items()}
    mejor = max(redondeadas.values())
    ganadoras = [k for k, v in redondeadas.items() if v == mejor]
    return ganadoras[0] if len(ganadoras) == 1 else None


def _del_ultimo_mes(lineas: list[LineaHistorial]) -> list[LineaHistorial]:
    ultimo = max(l.ano * 100 + l.mes for l in lineas)
    return [l for l in lineas if l.ano * 100 + l.mes == ultimo]


def _origen(lineas: list[LineaHistorial]) -> str:
    """«parte P1, P2 · MM/AAAA · obra O1, O2» de las líneas ganadoras."""
    partes = ", ".join(sorted({l.parte_cod or "?" for l in lineas}))
    obras = ", ".join(sorted({l.obra_cod or "?" for l in lineas}))
    l = lineas[0]
    return f"parte {partes} · {l.mes:02d}/{l.ano} · obra {obras}"


def previa_en_obra(historial: Iterable[LineaHistorial], recurso: int | None,
                   obra_ide: int,
                   hojas: dict[int, PartidaNodo]) -> Propuesta | None:
    """Paso (a), parte anterior: el recurso en esta obra."""
    propias = [l for l in historial
               if l.reside == recurso and l.obride == obra_ide and l.paride]
    if not propias:
        return None
    del_mes = _del_ultimo_mes(propias)
    sumas: dict[int, float] = {}
    for l in del_mes:
        sumas[l.paride] = sumas.get(l.paride, 0.0) + float(l.can or 0)
    ganadora = _maximo_unico(sumas)
    nodo = hojas.get(ganadora)
    if nodo is None:
        return None
    return Propuesta(nodo.ide, nodo.cod, nodo.res, "parte_anterior",
                     _origen([l for l in del_mes if l.paride == ganadora]))


def _clave_traslado(cod: str | None, res: str | None) -> tuple:
    return tm.normalize_code(cod), tm.normalize(res)


def ultima_de_recurso(historial: Iterable[LineaHistorial],
                      recurso: int | None, obra_ide: int,
                      hojas: dict[int, PartidaNodo]) -> Propuesta | None:
    """Paso (b), último parte: el recurso en otra obra, trasladado a esta
    por código y descripción iguales. Va DESPUÉS del casamiento (R38)."""
    ajenas = [l for l in historial
              if l.reside == recurso and l.obride != obra_ide and l.paride]
    if not ajenas:
        return None
    del_mes = _del_ultimo_mes(ajenas)
    sumas: dict[tuple, float] = {}
    for l in del_mes:
        k = _clave_traslado(l.par_cod, l.par_res)
        sumas[k] = sumas.get(k, 0.0) + float(l.can or 0)
    ganadora = _maximo_unico(sumas)
    if ganadora is None or not any(ganadora):
        return None
    destino = [n for n in hojas.values()
               if _clave_traslado(n.cod, n.res) == ganadora]
    if len(destino) != 1:
        return None
    nodo = destino[0]
    return Propuesta(nodo.ide, nodo.cod, nodo.res, "ultimo_parte", _origen(
        [l for l in del_mes
         if _clave_traslado(l.par_cod, l.par_res) == ganadora]))


def _hojas_activas(nodos: dict[int, PartidaNodo]) -> dict[int, PartidaNodo]:
    return {i: n for i, n in nodos.items() if n.es_hoja and n.activa}


def proponer_partida(nodos: dict[int, PartidaNodo],
                     historial: Iterable[LineaHistorial],
                     recurso: int | None, obra_ide: int,
                     categoria: str | None,
                     nombre: str | None) -> Propuesta | None:
    """La propuesta de la línea: parte anterior (a), casamiento (c) o
    último parte (b), en ese orden (F-055 R38); o None."""
    historial = list(historial)
    hojas = _hojas_activas(nodos)
    p = previa_en_obra(historial, recurso, obra_ide, hojas)
    if p is not None:
        return p
    m = resolver_normal(nodos, categoria, nombre)
    if m is not None:
        paride, cod, metodo = m
        return Propuesta(paride, cod, nodos[paride].res, metodo)
    return ultima_de_recurso(historial, recurso, obra_ide, hojas)


def mayor_de(nodos: dict[int, PartidaNodo], nodo: PartidaNodo) -> str:
    """CD, CI, CP u OTRO de la raíz de la que cuelga `nodo` (la que no tiene
    padre en el presupuesto; un ciclo se corta en el último no repetido).
    Si la raíz no lo dice, la `categoria` de la propia hoja."""
    actual = nodo
    vistos = {nodo.ide}
    while True:
        padre = nodos.get(actual.padide or 0)
        if padre is None or padre.ide in vistos:
            break
        vistos.add(padre.ide)
        actual = padre
    mayor = clasifica_categoria(actual.cod, actual.res)
    return mayor if mayor != "OTRO" else nodo.categoria


def catalogo(nodos: dict[int, PartidaNodo]) -> list[dict]:
    """Hojas activas `{ide, cod, res, categoria, mayor}` en orden natural
    del código (y por `ide` si empatan)."""
    hojas = sorted(_hojas_activas(nodos).values(),
                   key=lambda n: (clave_orden_codigo(n.cod), n.ide))
    return [{"ide": n.ide, "cod": n.cod, "res": n.res,
             "categoria": n.categoria, "mayor": mayor_de(nodos, n)}
            for n in hojas]


def mayor_inicial(propuesta: Propuesta | None,
                  nodos: dict[int, PartidaNodo],
                  categoria: str | None) -> str | None:
    """Botón del selector que sale elegido: el mayor de la propuesta; sin
    ella, CI si la categoría es de mando (`ambito_categoria` solo CI); si
    no, None (= Todas)."""
    nodo = nodos.get(propuesta.paride) if propuesta is not None else None
    if nodo is not None:
        return mayor_de(nodos, nodo)
    return "CI" if ambito_categoria(categoria) == {"CI"} else None
