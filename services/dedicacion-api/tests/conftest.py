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
