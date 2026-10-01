# domain/empresas.py
"""Visibilidad por empresa del cuadrante y del registro (F-024).

Una sola regla, pura y sin dependencias, que usan el cuadrante, el resumen,
la copia, el export y el registro en Sigrid. La regla de negocio está en
`docs/ARCHITECTURE.md#regla-empresa`; aquí solo se implementa.
"""
from __future__ import annotations

from collections.abc import Iterable

from domain.models import FiltroEmpresa


def visible_en_empresa(empresa_trabajador: int | None,
                       empresas_obras: Iterable[int | None],
                       filtro: FiltroEmpresa) -> bool:
    """¿Se ve este trabajador con la empresa del filtro?

    Con empresa, solo en la suya. Sin empresa (filas desactivadas antes de
    F-023), en cada empresa de las obras de sus líneas del periodo; si
    ninguna de esas obras tiene empresa, o no tiene líneas, solo en la por
    defecto.
    """
    if empresa_trabajador is not None:
        return empresa_trabajador == filtro.empresa
    conocidas = {e for e in empresas_obras if e is not None}
    if conocidas:
        return filtro.empresa in conocidas
    return filtro.empresa == filtro.por_defecto


def linea_de_otra_empresa(obra_empresa: int | None, empresa: int) -> bool:
    """La línea va a una obra con empresa conocida y distinta de la elegida
    (el transfer la omitirá al registrar)."""
    return obra_empresa is not None and obra_empresa != empresa
