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
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
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


# --- R2: los cuatro estados -------------------------------------------------


def test_f001_r2_sin_lineas_es_sin_carga() -> None:
    assert calcular_estado(Decimal(0), 0) is EstadoTrabajador.SIN_CARGA


def test_f001_r2_sin_lineas_manda_sobre_el_total() -> None:
    """Cero líneas es SIN_CARGA aunque el total valga 100.

    No es un caso imposible de laboratorio: es el orden de las guardas. Si
    alguien mueve la comprobación del total por delante del recuento de
    líneas, un trabajador sin carga pasaría por OK.
    """
    assert calcular_estado(Decimal(100), 0) is EstadoTrabajador.SIN_CARGA


def test_f001_r2_cien_exacto_es_ok() -> None:
    assert calcular_estado(Decimal(100), 2) is EstadoTrabajador.OK


def test_f001_r2_por_debajo_de_cien_es_falta() -> None:
    assert calcular_estado(Decimal(60), 1) is EstadoTrabajador.FALTA


def test_f001_r2_por_encima_de_cien_es_exceso() -> None:
    assert calcular_estado(Decimal(120), 3) is EstadoTrabajador.EXCESO


@pytest.mark.parametrize("total", ["99.999", "100.001", "99.995", "100.005"])
def test_f001_r2_dentro_de_la_epsilon_es_ok(total: str) -> None:
    """La tolerancia es 0,005 puntos porcentuales, y es cerrada.

    99,999 % y 100,001 % son OK (criterio `acceptance` de F-001); 99,995 % y
    100,005 % caen justo EN el borde y también son OK, porque la comparación
    es `<=`. Sin estos dos últimos, cambiar `<=` por `<` no lo caza nadie.
    """
    assert calcular_estado(Decimal(total), 2) is EstadoTrabajador.OK


@pytest.mark.parametrize(("total", "esperado"), [
    ("99.99", EstadoTrabajador.FALTA),
    ("100.01", EstadoTrabajador.EXCESO),
])
def test_f001_r2_fuera_de_la_epsilon_ya_no_es_ok(
    total: str, esperado: EstadoTrabajador
) -> None:
    """El primer escalón fuera de la tolerancia: 99,99 % y 100,01 %."""
    assert calcular_estado(Decimal(total), 2) is esperado


# --- R2: la desviación que acompaña al estado -------------------------------


def test_f001_r2_desviacion_sin_lineas_es_cero() -> None:
    """Sin líneas la desviación es 0, no «-100»: no hay nada que desviar."""
    assert calcular_desviacion(Decimal(100), 0) == Decimal(0)
    assert calcular_desviacion(Decimal(0), 0) == Decimal(0)


def test_f001_r2_desviacion_positiva_cuantizada_a_dos_decimales() -> None:
    desviacion = calcular_desviacion(Decimal("120.456"), 2)
    assert desviacion == Decimal("20.46")
    assert str(desviacion) == "20.46", "debe venir cuantizada, no en bruto"


def test_f001_r2_desviacion_negativa_cuantizada_a_dos_decimales() -> None:
    desviacion = calcular_desviacion(Decimal("70.123"), 1)
    assert desviacion == Decimal("-29.88")
    assert str(desviacion) == "-29.88", "debe venir cuantizada, no en bruto"


# --- R3: el resumen del periodo ---------------------------------------------


def test_f001_r3_resumen_vacio() -> None:
    assert resumir([]) == ResumenPeriodo(total=0, ok=0, falta=0, exceso=0,
                                         sin_carga=0)


def test_f001_r3_baja_sin_lineas_no_cuenta() -> None:
    """El criterio central de F-001: la baja sin carga no existe para el
    resumen. Ni suma en `total` ni aparece en `sin_carga` (tampoco se muestra
    en el front)."""
    filas = [
        _fila("100", ide=1),
        _fila(ide=2, activo=False),          # de baja y sin líneas
    ]
    assert resumir(filas) == ResumenPeriodo(total=1, ok=1, falta=0, exceso=0,
                                            sin_carga=0)


def test_f001_r3_baja_con_lineas_si_cuenta() -> None:
    """Una baja CON carga sigue contando: alguien tiene que verla y
    corregirla antes de registrar el periodo."""
    filas = [_fila("50", ide=7, activo=False)]
    assert resumir(filas) == ResumenPeriodo(total=1, ok=0, falta=1, exceso=0,
                                            sin_carga=0)


def test_f001_r3_activo_sin_lineas_si_cuenta_como_sin_carga() -> None:
    """La otra mitad de la condición: lo que descarta a la baja es la
    combinación «de baja Y sin líneas», no una de las dos por su cuenta."""
    filas = [_fila(ide=3, activo=True)]
    assert resumir(filas) == ResumenPeriodo(total=1, ok=0, falta=0, exceso=0,
                                            sin_carga=1)


def test_f001_r3_mixto_el_total_es_la_suma_de_los_cuatro_contadores() -> None:
    """Caso mixto con los cuatro estados más una baja sin carga: el `total`
    cuadra con la suma de contadores, así que nadie se cuenta dos veces ni se
    pierde por el camino."""
    filas = [
        _fila("60", "40", ide=1),            # OK
        _fila("30", ide=2),                  # FALTA
        _fila("80", "40", ide=3),            # EXCESO
        _fila(ide=4),                        # SIN_CARGA (activo)
        _fila(ide=5, activo=False),          # baja sin líneas: no cuenta
    ]
    resumen = resumir(filas)
    assert resumen == ResumenPeriodo(total=4, ok=1, falta=1, exceso=1,
                                     sin_carga=1)
    assert resumen.total == (resumen.ok + resumen.falta + resumen.exceso
                             + resumen.sin_carga)
