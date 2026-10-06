# domain/errors.py
"""Errores de negocio, mapeados a HTTP en interface_adapters/api."""
from __future__ import annotations


class ErrorDominio(Exception):
    """Base de los errores de negocio."""


class PeriodoNoEncontrado(ErrorDominio):
    pass


class PeriodoCerrado(ErrorDominio):
    pass


class TrabajadorNoEncontrado(ErrorDominio):
    pass


class ObraNoValida(ErrorDominio):
    pass


class LineasInvalidas(ErrorDominio):
    pass


class NadaQueDeshacer(ErrorDominio):
    pass


class DeshacerAjeno(ErrorDominio):
    """El último cambio pendiente del trabajador es de otro usuario: solo
    puede deshacerlo quien lo hizo (F-027, decisión A). Mismo HTTP que
    `NadaQueDeshacer`."""


class SigridNoConfigurado(ErrorDominio):
    pass


class SigridError(ErrorDominio):
    pass


class UniversoPostventaNoDisponible(ErrorDominio):
    """El transfer no ha dado el universo de postventa (caído, `ok` que no es
    `true` o sin `obras`): el sync falla entero (F-025, R15, D3)."""


class UniversoVarNoDisponible(ErrorDominio):
    """El transfer no ha dado el universo VAR (caído, `ok` que no es `true` o
    sin `partidas`): el sync y el preview fallan enteros (F-039, R16)."""
