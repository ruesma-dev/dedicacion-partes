# domain/empresas.py
"""Visibilidad por empresa del cuadrante y del registro (F-024).

Una sola regla, pura y sin dependencias, que usan el cuadrante, el resumen,
la copia, el export y el registro en Sigrid. La regla de negocio está en
`docs/ARCHITECTURE.md#regla-empresa`; aquí solo se implementa. Desde F-032,
también la regla de empresa «de baja» del catálogo `auxemp`.
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


def empresa_de_baja(fecbaj: int | None, desact: int | None) -> bool:
    """¿Está la empresa dada de baja o desactivada en Sigrid? (F-032)

    `auxemp.fecbaj` es una fecha entera (0 o NULL = sin baja) y
    `auxemp.desact` vale 0 (no) o 1 (sí). Una empresa de baja con
    trabajadores activos se sigue enseñando, marcada: ocultarla escondería
    carga (decisión del humano del 2026-10-01).
    """
    return (fecbaj or 0) > 0 or desact == 1


def linea_de_otra_empresa(obra_empresa: int | None, empresa: int) -> bool:
    """La línea va a una obra con empresa conocida y distinta de la elegida
    (el transfer la omitirá al registrar)."""
    return obra_empresa is not None and obra_empresa != empresa
