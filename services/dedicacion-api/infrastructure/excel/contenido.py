# infrastructure/excel/contenido.py
"""Modelo de presentación del Excel de exportación (F-040, F-045, F-076).

Puro: no importa openpyxl. Convierte el cuadrante que entrega la API en lo
que pinta `exporter.py`:

  - un `GrupoTrabajador` por trabajador con todas sus líneas
    (`grupos_detalle`), para la hoja «Detalle»;
  - un `GrupoTrabajador` por trabajador con alguna línea de esa parte (o
    sin ninguna línea) para cada pestaña «Obras» y «Postventa»
    (`grupos_pestana`): solo sus líneas de esa parte, sin línea agregada de
    la otra (F-076);
  - los textos de porcentaje y de estado.

Las cifras (total, estado, desviación) son las de la regla del 100 %
(`domain.estados`): aquí no hay umbral ni épsilon propios, solo formato. En
«Detalle» se aplica al trabajador completo; en las pestañas, a su parte
(F-076 D1).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from domain.estados import calcular_desviacion, calcular_estado
from domain.models import CuadranteTrabajador, EstadoTrabajador, Linea

_ESTADO_FIJO = {
    EstadoTrabajador.OK: "OK",
    EstadoTrabajador.SIN_CARGA: "SIN CARGA",
}


@dataclass(frozen=True)
class LineaDetalle:
    codigo: str               # «0702», «Postv-0702», «VAR-29»; «» sin líneas
    obra: str                 # columna Obra del Detalle (con prefijo si postventa)
    nombre: str               # descripción sin prefijo (F-045 D10: se conserva)
    porcentaje: Decimal | None


@dataclass(frozen=True)
class GrupoTrabajador:
    empleado: str
    categoria: str
    lineas: list[LineaDetalle]   # nunca vacía: sin líneas, una vacía (R9)
    total: Decimal
    desviacion: Decimal | None   # None si SIN CARGA (celda vacía)
    estado: str


_LINEA_VACIA = LineaDetalle(codigo="", obra="", nombre="", porcentaje=None)


def grupos_detalle(
    filas: list[CuadranteTrabajador], prefijo: str
) -> list[GrupoTrabajador]:
    """Un grupo por trabajador, en el orden en que llegan (no reordena),
    con el total y el estado del trabajador completo."""
    return [
        _grupo(fila, [_linea_detalle(ln, prefijo) for ln in fila.lineas],
               fila.total, len(fila.lineas))
        for fila in filas
    ]


def grupos_pestana(
    filas: list[CuadranteTrabajador], prefijo: str, postventa: bool
) -> list[GrupoTrabajador]:
    """Grupos de la pestaña «Postventa» (`postventa`) u «Obras» (F-076).

    Cada grupo lleva solo las líneas de esa parte, en su orden, sin línea
    agregada de la otra (R2-R4). El trabajador que tiene líneas pero ninguna
    de esa parte no sale (R5: basta una, aunque esté al 0 %); el que no tiene
    ninguna sale «SIN CARGA» en las dos pestañas (R7, D2). Total, desviación
    y estado son los de esa parte (R8, D1): la suma exacta de sus % y la
    regla del 100 % sobre ella, así que la columna % del grupo suma su total.
    """
    grupos: list[GrupoTrabajador] = []
    for fila in filas:
        propias = [ln for ln in fila.lineas if ln.es_postventa == postventa]
        if fila.lineas and not propias:
            continue
        grupos.append(_grupo(
            fila,
            [_linea_detalle(ln, prefijo) for ln in propias],
            sum((ln.porcentaje for ln in propias), Decimal(0)),
            len(propias),
        ))
    return grupos


def _linea_detalle(ln: Linea, prefijo: str) -> LineaDetalle:
    """Código y Obra con el prefijo si es postventa (F-040 R8)."""
    return LineaDetalle(
        codigo=f"{prefijo}{ln.cod}" if ln.es_postventa else ln.cod,
        obra=(f"{prefijo}{ln.descripcion}" if ln.es_postventa
              else ln.descripcion),
        nombre=ln.descripcion,
        porcentaje=ln.porcentaje,
    )


def _grupo(
    fila: CuadranteTrabajador, lineas: list[LineaDetalle],
    total: Decimal, num: int,
) -> GrupoTrabajador:
    """Grupo con el total dado y el estado y la desviación de la regla del
    100 % sobre ese total y ese número de líneas (`domain.estados`)."""
    estado = calcular_estado(total, num)
    desviacion = calcular_desviacion(total, num)
    return GrupoTrabajador(
        empleado=fila.trabajador.nombre,
        categoria=fila.trabajador.categoria or "",
        lineas=lineas or [_LINEA_VACIA],
        total=total,
        desviacion=(None if estado is EstadoTrabajador.SIN_CARGA
                    else desviacion),
        estado=texto_estado(estado, desviacion),
    )


def es_entero(valor: Decimal) -> bool:
    return valor == valor.to_integral_value()


def texto_pct(valor: Decimal) -> str:
    """«100», «10», «33,33». Formato fijo: nunca `normalize()` («1E+2»)."""
    if es_entero(valor):
        return str(int(valor))
    return f"{valor:.2f}".replace(".", ",")


def texto_estado(estado: EstadoTrabajador, desviacion: Decimal) -> str:
    if estado in _ESTADO_FIJO:
        return _ESTADO_FIJO[estado]
    magnitud = texto_pct(abs(desviacion))
    if estado is EstadoTrabajador.FALTA:
        return f"FALTA {magnitud}%"
    return f"EXCESO {magnitud}%"
