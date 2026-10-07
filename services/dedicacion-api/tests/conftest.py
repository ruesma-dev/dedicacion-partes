# tests/conftest.py
"""Configuración de pytest para la suite de dedicacion-api.

Inserta la raíz del servicio en `sys.path` para que los tests importen
`domain...`, `application...` o `infrastructure...` igual que lo hace
`main.py` al arrancar desde esta carpeta. Va aquí, en un único sitio, en
vez de repetir un `sys.path.insert` en la cabecera de cada fichero de test.

No hay fixtures de red ni de BBDD a propósito: los tests de este servicio
son offline (ver `docs/CONVENTIONS.md`, sección «Tests»).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]

if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))


class UniversoFalso:
    """Doble de los universos de postventa (`UniversoPostventaGateway`,
    F-025) y VAR (`UniversoVarGateway`, F-039).

    `ides`: obras que «casarían»; solo vuelven las que se le piden, como el
    transfer de verdad. `motivo`: por qué no hay universo. `fallo`: excepción
    que lanza en vez de responder. `llamadas` anota (empresa, obras).

    VAR: `var` es el `ResultadoUniversoVar` que devuelve (sin él, ni obra VAR
    ni partidas); `fallo_var`, la excepción que lanza; `llamadas_var` anota
    la empresa pedida."""

    def __init__(self, ides=(), motivo=None, fallo=None, var=None,
                 fallo_var=None) -> None:
        self.ides = frozenset(ides)
        self.motivo = motivo
        self.fallo = fallo
        self.llamadas: list[tuple[int, list[dict]]] = []
        self.var = var
        self.fallo_var = fallo_var
        self.llamadas_var: list[int] = []

    def universo_postventa(self, empresa, obras):
        from domain.models import ResultadoUniverso

        self.llamadas.append((empresa, [dict(o) for o in obras]))
        if self.fallo is not None:
            raise self.fallo
        pedidas = {o["ide"] for o in obras}
        return ResultadoUniverso(ides=self.ides & pedidas, motivo=self.motivo)

    def universo_var(self, empresa):
        from domain.models import ResultadoUniversoVar

        self.llamadas_var.append(empresa)
        if self.fallo_var is not None:
            raise self.fallo_var
        if self.var is not None:
            return self.var
        return ResultadoUniversoVar(obra_ide=None, obra_cod=None,
                                    empresa=None, partidas=(), motivo=None)
