# domain/traer_sigrid.py
"""F-054, parte A: comparar lo que hay en los partes de Sigrid con el
cuadrante (R13-R18; design §5.1, docs/ARCHITECTURE.md#regla-traer-sigrid).

Puro, sin dependencias de infraestructura. Las líneas llegan ya traducidas
por el transfer (`LineaSigridTraida`: su entrada normal, de postventa o
VAR). Aquí se decide **por recurso** quién es trabajador (R14), se agrupa
por trabajador y entrada (R13), se suma (R15-R16), se propone la partida
(R17) y se compara con el cuadrante (R18). Nada se escribe: eso es del caso
de uso, y solo con lo que el usuario acepta.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from domain.empresas import linea_de_otra_empresa, visible_en_empresa
from domain.estados import _EPSILON  # la épsilon del 100 % (R18): una sola
from domain.models import (
    FiltroEmpresa,
    Linea,
    LineaSigridTraida,
    Obra,
    Trabajador,
)
from domain.obras import ide_entrada
from domain.vigencia import vigente_en

_CIEN = Decimal(100)
_CENTIMO = Decimal("0.01")

#: R14: por qué una línea de Sigrid no se trae.
MOTIVO_NO_VISIBLE = "el trabajador no se ve en la empresa {empresa}"
MOTIVO_NO_VIGENTE = "el trabajador no está vigente en {mes:02d}/{anio}"
MOTIVO_NO_EN_BASE = "la obra {obra} no está en la base"
MOTIVO_OTRA_EMPRESA = "la obra {obra} es de la empresa {emp}, no de la {empresa}"
MOTIVO_NO_OFRECIBLE = "la obra {obra} no se ofrece {modo}"
#: R15-R16: por qué una entrada es `no_traducible`.
MOTIVO_PARTIDAS_DISTINTAS = "sus líneas de Sigrid tienen partidas distintas"
MOTIVO_PORCENTAJE_FUERA = "el porcentaje de Sigrid ({pct}) no está en (0, 100]"


class EstadoEntrada(str, Enum):
    """R18: cómo está una entrada de un trabajador en los dos lados."""

    IGUAL = "igual"
    DISTINTA = "distinta"
    SOLO_SIGRID = "solo_sigrid"
    SOLO_CUADRANTE = "solo_cuadrante"
    NO_TRADUCIBLE = "no_traducible"


@dataclass(frozen=True)
class EntradaSigrid:
    """Una entrada (obra + modo) de un trabajador en Sigrid: su %, su
    partida (la de sus líneas; R17), el menor `hmores_ide` de sus líneas y
    su parte (R23), cuántas líneas suma y, si es `no_traducible`, por qué."""

    obra_ide: int
    es_postventa: bool
    porcentaje: Decimal
    partida_ide: int | None = None
    partida_cod: str | None = None
    partida_res: str | None = None
    hmores_ide: int = 0
    parte_cod: str | None = None
    n_lineas: int = 0
    motivo: str | None = None
    destino: str = "normal"

    def clave(self) -> tuple[int, bool]:
        return (self.obra_ide, self.es_postventa)


@dataclass(frozen=True)
class NoTraida:
    """R14: una línea de Sigrid que no se trae, con su motivo."""

    hmores_ide: int
    recurso_ide: int
    obra_cod: str | None
    parte_cod: str | None
    can: float
    motivo: str


@dataclass(frozen=True)
class Contadores:
    """R14, R27: las líneas que solo se cuentan."""

    fuera_maestro: int = 0
    de_vinculados: int = 0


@dataclass(frozen=True)
class Comparada:
    """R18, R27: una entrada del trabajador con su estado y los dos %."""

    obra_ide: int
    es_postventa: bool
    estado: EstadoEntrada
    pct_sigrid: Decimal | None
    pct_cuadrante: Decimal | None
    entrada: EntradaSigrid | None = None
    motivo: str | None = None


def _clave(l: LineaSigridTraida) -> tuple[int, bool] | None:
    """R13: la entrada de la línea (None si no la tiene)."""
    if l.destino == "postventa":
        return None if l.obra_origen_ide is None else (
            int(l.obra_origen_ide), True)
    if l.destino == "var":
        return None if l.var_paride is None else (
            ide_entrada(int(l.var_paride)), False)
    return (int(l.obra_ide), False)


def _nombre_obra(l: LineaSigridTraida, clave: tuple[int, bool],
                 obras: dict[int, Obra]) -> str:
    obra = obras.get(clave[0])
    if obra is not None:
        return obra.cod
    if l.destino == "var":
        return f"VAR-{l.var_paride}"
    if l.destino == "postventa":
        return str(l.obra_origen_ide)
    return l.obra_cod or str(l.obra_ide)


def _motivo_obra(l: LineaSigridTraida, clave: tuple[int, bool],
                 obras: dict[int, Obra], empresa_obras: int) -> str | None:
    """R14: la entrada no está en la base, es de otra empresa o no se
    ofrece en ese modo (`Linea.ofrecible`)."""
    nombre = _nombre_obra(l, clave, obras)
    obra = obras.get(clave[0])
    if obra is None:
        return MOTIVO_NO_EN_BASE.format(obra=nombre)
    if linea_de_otra_empresa(obra.empresa, empresa_obras):
        return MOTIVO_OTRA_EMPRESA.format(obra=nombre, emp=obra.empresa,
                                          empresa=empresa_obras)
    linea = Linea(obra_ide=obra.ide, es_postventa=clave[1],
                  porcentaje=Decimal(0), obra_activa=obra.activa,
                  obra_admite_postventa=obra.admite_postventa)
    if not linea.ofrecible:
        return MOTIVO_NO_OFRECIBLE.format(
            obra=nombre, modo="en postventa" if clave[1] else "normal")
    return None


def _entrada(clave: tuple[int, bool],
             lineas: list[LineaSigridTraida]) -> EntradaSigrid:
    """R15-R17: las líneas de un trabajador en una entrada, sumadas."""
    pct = (sum((Decimal(str(l.can)) for l in lineas), Decimal(0))
           * _CIEN).quantize(_CENTIMO, rounding=ROUND_HALF_UP)
    primera = min(lineas, key=lambda l: l.hmores_ide)
    destino = primera.destino
    parides = {int(l.paride or 0) for l in lineas}
    motivo = None
    if destino == "normal" and len(parides) > 1:
        motivo = MOTIVO_PARTIDAS_DISTINTAS
    elif not Decimal(0) < pct <= _CIEN:
        motivo = MOTIVO_PORCENTAJE_FUERA.format(pct=pct)
    elegida = destino == "normal" and primera.paride
    return EntradaSigrid(
        obra_ide=clave[0], es_postventa=clave[1], porcentaje=pct,
        partida_ide=int(primera.paride) if elegida else None,
        partida_cod=primera.partida_cod if elegida else None,
        partida_res=primera.partida_res if elegida else None,
        hmores_ide=primera.hmores_ide, parte_cod=primera.parte_cod,
        n_lineas=len(lineas), motivo=motivo, destino=destino)


def entradas_por_trabajador(
    lineas: Iterable[LineaSigridTraida], obras: dict[int, Obra], *,
    filtro: FiltroEmpresa, anio: int, mes: int,
    trabajadores: dict[int, Trabajador], vinculados: set[int],
) -> tuple[dict[int, list[EntradaSigrid]], list[NoTraida], Contadores]:
    """R13-R17: por trabajador (`recurso_ide`), sus entradas de Sigrid en
    orden de clave; las líneas que no se traen, con su motivo, por
    `hmores_ide`; y lo que solo se cuenta. Por recurso (R14): un `ide` de
    `vinculados` (todo `recurso_vinculado`) solo cuenta en
    `de_vinculados`; uno que no está en `trabajadores` (el maestro), en
    `fuera_maestro`."""
    grupos: dict[int, dict[tuple[int, bool], list[LineaSigridTraida]]] = {}
    no_traidas: list[NoTraida] = []
    fuera = vin = 0

    def no(l: LineaSigridTraida, motivo: str) -> None:
        no_traidas.append(NoTraida(
            hmores_ide=l.hmores_ide, recurso_ide=l.recurso_ide,
            obra_cod=l.obra_cod, parte_cod=l.parte_cod, can=l.can,
            motivo=motivo))

    for l in lineas:
        if l.recurso_ide in vinculados:
            vin += 1
            continue
        t = trabajadores.get(l.recurso_ide)
        if t is None:
            fuera += 1
            continue
        if not visible_en_empresa(t.empresa, filtro):
            no(l, MOTIVO_NO_VISIBLE.format(empresa=filtro.empresa))
            continue
        if not vigente_en(t.activo, t.fecha_baja, anio, mes):
            no(l, MOTIVO_NO_VIGENTE.format(mes=mes, anio=anio))
            continue
        if l.motivo:
            no(l, l.motivo)
            continue
        clave = _clave(l)
        motivo = (None if clave is None else
                  _motivo_obra(l, clave, obras, filtro.empresa_obras))
        if clave is None or motivo:
            no(l, motivo or MOTIVO_NO_EN_BASE.format(obra=l.obra_cod))
            continue
        grupos.setdefault(l.recurso_ide, {}).setdefault(clave, []).append(l)
    entradas = {r: [_entrada(c, ls) for c, ls in sorted(g.items())]
                for r, g in sorted(grupos.items())}
    no_traidas.sort(key=lambda n: n.hmores_ide)
    return entradas, no_traidas, Contadores(fuera_maestro=fuera,
                                            de_vinculados=vin)


def comparar(lineas: Iterable[Linea],
             entradas: Iterable[EntradaSigrid]) -> list[Comparada]:
    """R18: cada entrada de los dos lados, por clave, con su estado. El %
    con la épsilon de `domain/estados.py`; la partida no cuenta."""
    cuadrante = {ln.clave(): ln for ln in lineas}
    sigrid = {e.clave(): e for e in entradas}
    out: list[Comparada] = []
    for clave in sorted(set(cuadrante) | set(sigrid)):
        ln, e = cuadrante.get(clave), sigrid.get(clave)
        pct_c = ln.porcentaje if ln is not None else None
        if e is None:
            estado = EstadoEntrada.SOLO_CUADRANTE
        elif e.motivo:
            estado = EstadoEntrada.NO_TRADUCIBLE
        elif ln is None:
            estado = EstadoEntrada.SOLO_SIGRID
        elif abs(e.porcentaje - ln.porcentaje) <= _EPSILON:
            estado = EstadoEntrada.IGUAL
        else:
            estado = EstadoEntrada.DISTINTA
        out.append(Comparada(
            obra_ide=clave[0], es_postventa=clave[1], estado=estado,
            pct_sigrid=e.porcentaje if e is not None else None,
            pct_cuadrante=pct_c, entrada=e,
            motivo=e.motivo if e is not None else None))
    return out


def a_linea(entrada: EntradaSigrid, obra: Obra) -> Linea:
    """R17: la línea del cuadrante que deja la entrada aceptada: su %, la
    partida de sus líneas como elegida (normal; 0 = automática), automática
    en postventa y fija en una entrada VAR (ninguna elegida). Sin propuesta
    guardada."""
    return Linea(
        obra_ide=entrada.obra_ide, es_postventa=entrada.es_postventa,
        porcentaje=entrada.porcentaje, cod=obra.cod,
        descripcion=obra.descripcion, obra_activa=obra.activa,
        obra_empresa=obra.empresa,
        obra_admite_postventa=obra.admite_postventa,
        partida_ide=entrada.partida_ide, partida_cod=entrada.partida_cod,
        partida_res=entrada.partida_res,
        partida_fija=entrada.destino == "var")
