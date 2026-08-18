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


class SigridNoConfigurado(ErrorDominio):
    pass


class SigridError(ErrorDominio):
    pass
