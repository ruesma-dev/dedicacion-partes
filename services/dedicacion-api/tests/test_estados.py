# tests/test_estados.py
"""Tests offline de la regla de control del cuadrante (`domain/estados.py`).

Trazabilidad con los criterios `acceptance` de F-001 (`harness/features.json`):

  - R1: existe la suite y no toca red ni BBDD.
  - R2: los cuatro estados y el borde de la épsilon (99,999 % y 100,001 %
        son OK), más la desviación que acompaña al estado.
  - R3: `resumir()`; un trabajador de baja y sin líneas no cuenta.

R4 («init.sh en verde con la línea 'servicio api: pytest en verde'») no es un
test: lo verifica el propio portero, y su salida consta en
`progress/impl_F-001.md`.

Todo se construye a mano con `Decimal` y entidades de dominio: sin ficheros,
sin `.env`, sin sockets y sin base de datos.
"""
from __future__ import annotations

import ast
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from domain.estados import calcular_desviacion, calcular_estado, resumir
from domain.models import (
    CuadranteTrabajador,
    EstadoTrabajador,
    Linea,
    ResumenPeriodo,
    Trabajador,
)

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]

#: Paquetes propios que el dominio sí puede importar. Cualquier otro nombre
#: que no sea de la biblioteca estándar delata una dependencia de
#: infraestructura (cliente HTTP, driver de BBDD, ORM...).
_PAQUETES_PROPIOS_PERMITIDOS = {"domain"}


# --- Constructores de entidades de dominio ----------------------------------


def _trabajador(ide: int = 1, nombre: str = "Trabajador", *,
                activo: bool = True) -> Trabajador:
    return Trabajador(ide=ide, cod=f"T{ide:03d}", nombre=nombre, dni=None,
                      categoria=None, activo=activo)


def _linea(porcentaje: str, *, obra_ide: int = 100,
           es_postventa: bool = False) -> Linea:
    return Linea(obra_ide=obra_ide, es_postventa=es_postventa,
                 porcentaje=Decimal(porcentaje))


def _fila(*porcentajes: str, ide: int = 1,
          activo: bool = True) -> CuadranteTrabajador:
    """Fila del cuadrante con una línea por porcentaje (obras distintas)."""
    lineas = [_linea(pct, obra_ide=100 + n)
              for n, pct in enumerate(porcentajes)]
    return CuadranteTrabajador(trabajador=_trabajador(ide, activo=activo),
                               lineas=lineas)


def _modulos_importados(ruta: Path) -> set[str]:
    """Nombres de primer nivel importados por un fuente Python."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level == 0 and nodo.module:
                modulos.add(nodo.module.split(".")[0])
    return modulos


# --- R1: la suite es offline ------------------------------------------------


@pytest.mark.parametrize("modulo", ["estados.py", "models.py"])
def test_f001_r1_el_dominio_bajo_prueba_no_toca_red_ni_bbdd(modulo: str) -> None:
    """El código ejercitado solo importa stdlib y `domain`.

    Es la garantía estructural de que estos tests no pueden abrir un socket
    ni una conexión a PostgreSQL: no hay por dónde.
    """
    importados = _modulos_importados(RAIZ_SERVICIO / "domain" / modulo)
    assert importados, f"no se leyó ningún import de domain/{modulo}"
    externos = {
        nombre
        for nombre in importados
        if nombre not in sys.stdlib_module_names
        and nombre not in _PAQUETES_PROPIOS_PERMITIDOS
    }
    assert externos == set(), (
        f"domain/{modulo} importa dependencias no permitidas: {sorted(externos)}"
    )
