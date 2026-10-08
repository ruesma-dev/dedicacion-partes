# infrastructure/excel/contenido.py
"""Modelo de presentación del Excel de exportación (F-040, F-045).

Puro: no importa openpyxl. Convierte el cuadrante que entrega la API en lo
que pinta `exporter.py`:

  - un `GrupoTrabajador` por trabajador con todas sus líneas
    (`grupos_detalle`), del que sale el Resumen;
  - un `GrupoTrabajador` por trabajador para cada pestaña «Obras» y
    «Postventa» (`grupos_pestana`): sus líneas de esa parte y, al final, una
    línea agregada con la suma de la otra parte (F-045);
  - una `FilaResumen` por trabajador para la hoja Resumen;
  - los textos de porcentaje y de estado.

Las cifras (total, estado, desviación) son las de la regla del 100 %
(`domain.estados`): aquí no hay umbral ni épsilon propios, solo formato.
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
    nombre: str               # descripción sin prefijo, para el Resumen
    porcentaje: Decimal | None
    agregada: bool = False    # la línea «RESTO …» de la otra parte (F-045)


@dataclass(frozen=True)
class GrupoTrabajador:
    empleado: str
    categoria: str
    lineas: list[LineaDetalle]   # nunca vacía: sin líneas, una vacía (R9)
    total: Decimal
    desviacion: Decimal | None   # None si SIN CARGA (celda vacía)
    estado: str


@dataclass(frozen=True)
class FilaResumen:
    empleado: str
    categoria: str
    obras: str
    total: Decimal
    estado: str


_LINEA_VACIA = LineaDetalle(codigo="", obra="", nombre="", porcentaje=None)


#: Rótulos (Código, Obra) de la línea agregada según la pestaña (F-045 D6).
AGREGADA_EN_OBRAS = ("POSTVENTA", "RESTO POSTVENTA")
AGREGADA_EN_POSTVENTA = ("OBRAS", "RESTO OBRAS")


def grupos_detalle(
    filas: list[CuadranteTrabajador], prefijo: str
) -> list[GrupoTrabajador]:
    """Un grupo por trabajador, en el orden en que llegan (no reordena)."""
    return [
        _grupo(fila, [_linea_detalle(ln, prefijo) for ln in fila.lineas])
        for fila in filas
    ]


def grupos_pestana(
    filas: list[CuadranteTrabajador], prefijo: str, postventa: bool
) -> list[GrupoTrabajador]:
    """Grupos de la pestaña «Postventa» (`postventa`) u «Obras» (F-045).

    Cada grupo lleva las líneas de esa parte, en su orden, y al final UNA
    línea agregada con la suma exacta de las de la otra parte, si las hay.
    Total, desviación y estado son los del trabajador completo, así que la
    suma de los % del grupo es su total en las dos pestañas (R11, R12).
    """
    codigo, obra = AGREGADA_EN_POSTVENTA if postventa else AGREGADA_EN_OBRAS
    grupos: list[GrupoTrabajador] = []
    for fila in filas:
        propias = [_linea_detalle(ln, prefijo) for ln in fila.lineas
                   if ln.es_postventa == postventa]
        otras = [ln.porcentaje for ln in fila.lineas
                 if ln.es_postventa != postventa]
        if otras:
            propias.append(LineaDetalle(
                codigo=codigo, obra=obra, nombre="",
                porcentaje=sum(otras, Decimal(0)), agregada=True,
            ))
        grupos.append(_grupo(fila, propias))
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
    fila: CuadranteTrabajador, lineas: list[LineaDetalle]
) -> GrupoTrabajador:
    """Grupo con total, desviación y estado del trabajador completo."""
    total = fila.total
    num = len(fila.lineas)
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


def filas_resumen(grupos: list[GrupoTrabajador]) -> list[FilaResumen]:
    """Una fila por grupo; «Obras» une «<código> <nombre> = <pct>%»."""
    return [
        FilaResumen(
            empleado=g.empleado,
            categoria=g.categoria,
            obras=" + ".join(
                f"{ln.codigo} {ln.nombre} = {texto_pct(ln.porcentaje)}%"
                for ln in g.lineas
                if ln.porcentaje is not None
            ),
            total=g.total,
            estado=g.estado,
        )
        for g in grupos
    ]


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
