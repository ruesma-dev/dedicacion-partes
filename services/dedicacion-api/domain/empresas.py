# domain/empresas.py
"""Visibilidad por empresa del cuadrante y del registro (F-024, F-034).

Una sola regla, pura y sin dependencias, que usan el cuadrante, el resumen,
la copia, el export y el registro en Sigrid. Desde F-034 el selector filtra
solo trabajadores: las obras son siempre las de la empresa de las obras. La
regla de negocio está en `docs/ARCHITECTURE.md#regla-empresa`; aquí solo se
implementa. Desde F-032, también la regla de empresa «de baja» del catálogo
`auxemp`.
"""
from __future__ import annotations

from domain.models import FiltroEmpresa


def visible_en_empresa(empresa_trabajador: int | None,
                       filtro: FiltroEmpresa) -> bool:
    """¿Se ve este trabajador con la empresa elegida en el filtro?

    Con empresa, solo en la suya. Sin empresa (filas desactivadas antes de
    F-023), solo en la por defecto, tenga o no líneas y sean de la obra que
    sean (F-034, R3): las obras son siempre de la empresa de las obras, así
    que no dicen nada de la empresa del trabajador.
    """
    if empresa_trabajador is not None:
        return empresa_trabajador == filtro.empresa
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
    """La línea va a una obra con empresa conocida y distinta de `empresa`
    (el transfer la omitirá al registrar). Desde F-034 quien la llama pasa
    la empresa de las obras, nunca la elegida en el selector (R5)."""
    return obra_empresa is not None and obra_empresa != empresa
