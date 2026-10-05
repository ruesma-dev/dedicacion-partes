# tests/conftest.py
"""Configuración de pytest para la suite de dedicacion-front.

Inserta la raíz del servicio en `sys.path` para que los tests importen
`config...` o `interface_adapters...` igual que lo hace `main.py` al arrancar
desde esta carpeta. Va aquí, en un único sitio, en vez de repetir un
`sys.path.insert` en la cabecera de cada fichero de test. Es el mismo
`conftest.py` que ya tenía `dedicacion-api`.

No hay fixtures de red a propósito: los tests de este servicio son offline
(`docs/CONVENTIONS.md`, sección «Tests»). El backend `dedicacion-api` se
sustituye por un transporte de prueba de `httpx`, que responde en memoria.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]

if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))
