# application/services/reglas_vinculados.py
"""F-044 · reglas puras de los recursos vinculados (design §6.2;
ARCHITECTURE.md#regla-vinculado).

Un vinculado (teléfono, gasoil, vehículo… con el campo «Recurso Asociado»
hacia el trabajador) se registra con el % de su titular en cada obra. Aquí
se decide su PARTIDA, sin leer nada:

  - `partida_ci_del_tipo` (R15, R16): la única hoja activa del presupuesto
    de la obra cuya cuenta analítica tiene la subcuenta de la cuenta del
    vinculado (`CICO13` ↔ `.CI.4.13`). Ninguna o varias ⇒ sin partida con
    su motivo; nunca la primera.
  - `partida_del_vinculado` (R15-R17): la elegida en su subfila si vale; si
    el titular va a postventa, a una entrada VAR o a una partida que no es
    `CI*`, la del titular; si no, la CI del tipo, que llega como función
    para leer las cuentas solo si hace falta (R27).

Las lecturas (presupuesto, cuentas, validez de la elegida) son del
pipeline; este módulo no importa ningún cliente.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from application.services.cuenta_analitica import subcuenta
from application.services.partida_catalog import PartidaNodo

#: Métodos de la partida de un vinculado (`partida_metodo`).
METODO_MANUAL = "manual"        # la elegida en su subfila
METODO_TITULAR = "titular"      # la de su titular (R17)
METODO_CI_TIPO = "ci_tipo"      # la CI de su tipo (R15)

#: Sin partida (R16): ninguna hoja activa con la subcuenta, o varias.
MOTIVO_SIN_CI = "sin_ci"
MOTIVO_VARIAS_CI = "varias_ci"
#: R15: la elegida que no es hoja activa del presupuesto (como F-050).
MOTIVO_ELEGIDA_NO_VALIDA = (
    "la partida {cod} elegida para el recurso vinculado no es una partida "
    "hoja activa del presupuesto: no se escribe; elige otra partida")

#: Destinos y métodos del titular con los que el vinculado va a su partida.
_DESTINO_POSTVENTA = "postventa"
_METODO_VAR = "var"


@dataclass(frozen=True)
class PartidaElegida:
    """Una partida concreta: la elegida en la subfila o la CI del tipo."""
    paride: int
    cod: str | None = None
    res: str | None = None


@dataclass(frozen=True)
class PartidaTitular:
    """Lo que el vinculado necesita de la partida de su titular: destino
    (`obra` | `postventa`), partida (0 = sin partida) y método (`var` en
    una entrada VAR)."""
    destino: str
    paride: int
    cod: str | None = None
    res: str | None = None
    metodo: str | None = None


@dataclass(frozen=True)
class PartidaVinculado:
    """La partida decidida para un vinculado. `paride = 0` con
    `sin_partida` es «sin partida» a confirmar (R16, motivo `sin_ci` o
    `varias_ci`); con `omitir`, la elegida no vale y no se escribe (R15)."""
    paride: int = 0
    cod: str | None = None
    res: str | None = None
    metodo: str | None = None
    motivo: str | None = None
    sin_partida: bool = False
    omitir: bool = False


def _es_ci(cod: str | None) -> bool:
    return (cod or "").strip().upper().startswith("CI")


def va_con_el_titular(titular: PartidaTitular) -> bool:
    """R17: postventa, entrada VAR o una partida que no es `CI*` (`CP*`,
    `CD*`…). Un titular normal sin partida no tiene partida que dar."""
    if titular.destino == _DESTINO_POSTVENTA or titular.metodo == _METODO_VAR:
        return True
    return bool(titular.paride) and not _es_ci(titular.cod)


def partida_ci_del_tipo(hojas: dict[int, PartidaNodo],
                        cuentas: dict[int, str | None],
                        sub: str | None) -> tuple[PartidaElegida | None, str]:
    """R15-R16: la ÚNICA hoja activa de `hojas` (el presupuesto de la obra)
    cuya cuenta (`cuentas`, por `ide` de partida) tiene la subcuenta `sub`
    (comparada entera, sin espacios ni mayúsculas). Devuelve la partida y
    `ci_tipo`, o None y el motivo: `sin_ci` (ninguna) o `varias_ci`."""
    buscada = (sub or "").strip().upper()
    if not buscada:
        return None, MOTIVO_SIN_CI
    candidatas = [
        n for ide, cod in sorted(cuentas.items())
        for n in [hojas.get(ide)]
        if n is not None and n.es_hoja and n.activa
        and (subcuenta(cod) or "").upper() == buscada]
    if not candidatas:
        return None, MOTIVO_SIN_CI
    if len(candidatas) > 1:
        return None, MOTIVO_VARIAS_CI
    n = candidatas[0]
    return PartidaElegida(paride=int(n.ide), cod=n.cod, res=n.res), \
        METODO_CI_TIPO


def partida_del_vinculado(
    titular: PartidaTitular,
    elegida: PartidaElegida | None,
    elegida_valida: bool,
    ci: Callable[[], tuple[PartidaElegida | None, str]],
) -> PartidaVinculado:
    """R15-R17, en este orden: la elegida (si no vale, se omite); la del
    titular en postventa, VAR o partida no `CI*`; la CI del tipo (`ci`, que
    solo se llama aquí); sin ella, sin partida con su motivo."""
    if elegida is not None:
        if not elegida_valida:
            return PartidaVinculado(
                motivo=MOTIVO_ELEGIDA_NO_VALIDA.format(
                    cod=elegida.cod or elegida.paride),
                omitir=True)
        return PartidaVinculado(paride=int(elegida.paride), cod=elegida.cod,
                                res=elegida.res, metodo=METODO_MANUAL)
    if va_con_el_titular(titular):
        return PartidaVinculado(paride=int(titular.paride or 0),
                                cod=titular.cod, res=titular.res,
                                metodo=METODO_TITULAR)
    partida, motivo = ci()
    if partida is None:
        return PartidaVinculado(motivo=motivo, sin_partida=True)
    return PartidaVinculado(paride=partida.paride, cod=partida.cod,
                            res=partida.res, metodo=METODO_CI_TIPO)
