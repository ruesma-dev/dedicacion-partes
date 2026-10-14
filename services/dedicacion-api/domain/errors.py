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


class LineaNoEncontrada(ErrorDominio):
    """El trabajador no tiene línea con esa obra y ese modo en el periodo
    (F-050, R13): 404."""


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


class PropuestaNoDisponible(ErrorDominio):
    """El transfer no ha dado la propuesta de partidas (caído, `ok` que no
    es `true` o sin `propuestas`): el selector no se abre; el cuadrante sigue
    funcionando (F-050, R17)."""


class UniversoVarNoDisponible(ErrorDominio):
    """El transfer no ha dado el universo VAR (caído, `ok` que no es `true` o
    sin `partidas`): el sync y el preview fallan enteros (F-039, R16)."""
