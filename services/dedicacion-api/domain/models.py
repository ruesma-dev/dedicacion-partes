# domain/models.py
"""Entidades de dominio del servicio de dedicación.

Sin dependencias de infraestructura: dataclasses puras que circulan entre
casos de uso, repositorios y adaptadores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class EstadoPeriodo(str, Enum):
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"


class EstadoTrabajador(str, Enum):
    OK = "OK"
    FALTA = "FALTA"
    EXCESO = "EXCESO"
    SIN_CARGA = "SIN_CARGA"


class TipoEvento(str, Enum):
    GUARDAR = "GUARDAR"
    COPIA = "COPIA"


@dataclass(frozen=True)
class Trabajador:
    ide: int
    cod: str | None
    nombre: str
    dni: str | None
    categoria: str | None
    activo: bool = True
    empresa: int | None = None  # con.emp de su recurso (F-023, F-026)
    # Fecha de baja del recurso, AAAAMMDD o None (F-026): la vigencia por mes
    # la decide `domain.vigencia.vigente_en`.
    fecha_baja: int | None = None


@dataclass(frozen=True)
class Obra:
    ide: int
    cod: str
    descripcion: str
    estado_sigrid: str | None
    # `activa`: no excluida por estado; `admite_postventa`: en el universo de
    # postventa del transfer (F-025, docs/ARCHITECTURE.md#regla-p5).
    # Independientes: una obra cerrada puede admitir solo postventa.
    activa: bool = True
    empresa: int | None = None  # con.emp de su ficha (F-023)
    admite_postventa: bool = False


@dataclass(frozen=True)
class Periodo:
    anio: int
    mes: int
    estado: EstadoPeriodo = EstadoPeriodo.ABIERTO

    @property
    def clave(self) -> tuple[int, int]:
        return (self.anio, self.mes)


@dataclass(frozen=True)
class Linea:
    """Asignación de un trabajador a una obra dentro de un periodo."""

    obra_ide: int
    es_postventa: bool
    porcentaje: Decimal
    cod: str = ""
    descripcion: str = ""
    obra_activa: bool = True
    obra_empresa: int | None = None  # empresa de la obra (F-024, R11)
    obra_admite_postventa: bool = False  # F-025

    def clave(self) -> tuple[int, bool]:
        return (self.obra_ide, self.es_postventa)

    @property
    def ofrecible(self) -> bool:
        """¿Se ofrece hoy esta línea? La de postventa, si su obra admite
        postventa; la normal, si su obra está activa (F-025, R18).

        ÚNICA definición: la usan las copias, la validación al guardar y el
        cuadrante. No mira la empresa: la línea en obra de otra empresa
        conserva su propia marca (`otra_empresa`, F-034)."""
        if self.es_postventa:
            return self.obra_admite_postventa
        return self.obra_activa


@dataclass(frozen=True)
class FiltroEmpresa:
    """Empresa elegida en la petición, la por defecto y la de las obras
    (F-024, F-034).

    - `empresa`: la elegida en el selector; filtra solo TRABAJADORES.
    - `por_defecto`: la que se usa cuando la petición no trae empresa y la
      única en la que se ven los trabajadores sin empresa.
    - `empresa_obras`: la de las obras ofrecidas y la que viaja en cada línea
      al registrar, sea cual sea la elegida.

    Hoy `por_defecto` y `empresa_obras` salen del mismo ajuste,
    `EMPRESA_IMPUTACION` (D1 de F-034); van separadas para que partirlo
    mañana sea solo un ajuste (docs/ARCHITECTURE.md#regla-empresa).
    """

    empresa: int
    por_defecto: int
    empresa_obras: int


@dataclass(frozen=True)
class Empresa:
    """Empresa de Sigrid (`auxemp`, F-032), por su número (`con.emp`).

    `nombre` puede faltar (sin `res` en Sigrid); `de_baja` lo decide
    `domain.empresas.empresa_de_baja`.
    """

    numero: int
    nombre: str | None
    de_baja: bool = False


@dataclass
class CuadranteTrabajador:
    """Fila del cuadrante: trabajador + sus líneas + estado calculado."""

    trabajador: Trabajador
    lineas: list[Linea] = field(default_factory=list)
    puede_deshacer: bool = False

    @property
    def total(self) -> Decimal:
        return sum((ln.porcentaje for ln in self.lineas), Decimal("0"))


@dataclass(frozen=True)
class ResumenPeriodo:
    total: int = 0
    ok: int = 0
    falta: int = 0
    exceso: int = 0
    sin_carga: int = 0


@dataclass(frozen=True)
class ResultadoUniverso:
    """Universo de postventa que devuelve el transfer (F-025): los `ide` de
    las obras que admiten postventa y, si no hay universo, por qué."""

    ides: frozenset[int]
    motivo: str | None


@dataclass(frozen=True)
class ResultadoSyncMaestro:
    recibidos: int = 0
    altas: int = 0
    actualizados: int = 0
    desactivados: int = 0


@dataclass(frozen=True)
class ResultadoSync:
    empleados: ResultadoSyncMaestro
    obras: ResultadoSyncMaestro
    duracion_s: float
    # Catálogo `auxemp` (F-032). Al final y con valor por defecto para no
    # romper a quien construye el resultado por posición.
    empresas: ResultadoSyncMaestro = field(default_factory=ResultadoSyncMaestro)


@dataclass(frozen=True)
class ResultadoCopia:
    """Resultado de copiar asignaciones desde el periodo anterior."""

    periodo_origen: Periodo | None
    trabajadores_copiados: int = 0
    con_carga_previa: int = 0
    sin_datos_origen: int = 0
    lineas_omitidas_obra_inactiva: int = 0
