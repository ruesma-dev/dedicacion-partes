# domain/models.py
"""Entidades de dominio del servicio de dedicación.

Sin dependencias de infraestructura: dataclasses puras que circulan entre
casos de uso, repositorios y adaptadores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any


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
    COMPLETAR = "COMPLETAR"  # lote «completar al 100 %» (F-029)
    PARTIDA = "PARTIDA"  # cambio de la partida elegida de una línea (F-050)
    # Cambio de la partida elegida de una subfila de vinculado (F-044, R8);
    # su snapshot es el de líneas, con las elegidas de las subfilas.
    PARTIDA_VINCULADO = "PARTIDA_VINCULADO"
    # Sustitución de las incidencias del trabajador (F-030, R17); su
    # snapshot es de incidencias, no de líneas (R20).
    INCIDENCIAS = "INCIDENCIAS"


class ResultadoCompletado(str, Enum):
    """Qué le pasó a cada trabajador del lote «completar al 100 %» (F-029,
    docs/ARCHITECTURE.md#regla-completar)."""

    COMPLETADO = "COMPLETADO"
    YA_AL_100 = "YA_AL_100"
    EXCESO = "EXCESO"
    NO_VIGENTE = "NO_VIGENTE"
    NO_VISIBLE = "NO_VISIBLE"


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
class RecursoVinculado:
    """Recurso no persona de Sigrid (teléfono, gasoil, vehículo…) con el campo
    extendido «Recurso Asociado» (F-044, R1, D2): `principal_ide` es el valor
    del campo (`conext.valn`), el `res.ide` del trabajador al que se vincula,
    o None si está vacío. El vínculo lo decide `domain.vinculados.vincular`
    y la vigencia por mes, su propia `fecha_baja` (R4)."""

    ide: int
    principal_ide: int | None
    cod: str | None
    descripcion: str | None
    empresa: int | None
    fecha_baja: int | None
    tipo: str | None            # `auxrestip.cod` (TF, CO, VE…)
    tipo_res: str | None        # su descripción
    horide: int | None          # hora por defecto (`res.horide`)


@dataclass(frozen=True)
class SubfilaVinculado:
    """La subfila de un vinculado bajo una línea del cuadrante (F-044, R6):
    el vinculado vigente en el mes (`tipo`, `tipo_res`, `cod`, de
    `recurso_vinculado`) y lo suyo en esa línea (`asignacion_vinculado`):
    partida ELEGIDA (las tres None = automática, R8), propuesta GUARDADA
    (R9, como la de F-055) y traza del último registro (R21). Sin
    porcentaje: es el del titular (R7)."""

    vinculado_ide: int
    tipo: str | None = None
    tipo_res: str | None = None
    cod: str | None = None
    partida_ide: int | None = None
    partida_cod: str | None = None
    partida_res: str | None = None
    propuesta_ide: int | None = None
    propuesta_cod: str | None = None
    propuesta_res: str | None = None
    propuesta_metodo: str | None = None
    propuesta_origen: str | None = None
    sigrid_estado: str | None = None
    sigrid_motivo: str | None = None
    sigrid_parte: str | None = None
    sigrid_hmores_ide: int | None = None


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
    # Partida ELEGIDA (F-050, R12): las tres None = automática. No entra en
    # `clave()`. `partida_fija`: la línea es de una entrada VAR, cuya partida
    # es la de la entrada y no se elige (docs/ARCHITECTURE.md#regla-var).
    partida_ide: int | None = None
    partida_cod: str | None = None
    partida_res: str | None = None
    partida_fija: bool = False
    # Subfilas de los vinculados del trabajador vigentes en el mes (F-044,
    # R6); vacío = la línea de siempre. No entran en `clave()`.
    vinculados: tuple[SubfilaVinculado, ...] = ()
    # Propuesta GUARDADA (F-055, R13): la del transfer para una línea sin
    # elegida; todas None = sin propuesta. No entra en `clave()` ni en los
    # eventos (R17).
    propuesta_ide: int | None = None
    propuesta_cod: str | None = None
    propuesta_res: str | None = None
    propuesta_metodo: str | None = None
    propuesta_origen: str | None = None

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
class TipoIncidencia:
    """Tipo de incidencia del catálogo, copiado de `auxhor` de Sigrid por el
    sync (F-030, R3-R5): `ide` y código de `auxhor`, letra y nombre según
    `domain.incidencias.letra_y_nombre`. `activa` falsa = ya no se lee o
    tiene fecha de baja; no se borra."""

    ide: int
    codigo: str
    letra: str
    nombre: str
    activa: bool = True


@dataclass(frozen=True)
class Incidencia:
    """Incidencia de un trabajador en una obra durante un tramo de días del
    periodo (F-030, R17, docs/ARCHITECTURE.md#regla-incidencia). No es una
    línea de %: no cuenta para el 100 % (R22).

    `id` es nulo hasta guardarla. Obra, letra y nombre son de lectura (R21);
    `sigrid_*`, la traza del registro (R31). Anexo R30: `quitada`, la
    registrada que se quitó (R38); `sigrid_ide_*` y `sigrid_dia_*`, el `ide`
    y el día de cada línea del par en Sigrid (R39)."""

    obra_ide: int
    codigo: str
    dia_desde: int
    dia_hasta: int
    id: int | None = None
    obra_cod: str = ""
    obra_descripcion: str = ""
    letra: str = ""
    nombre: str = ""
    sigrid_estado: str | None = None
    sigrid_parte_cod: str | None = None
    sigrid_motivo: str | None = None
    quitada: bool = False
    sigrid_ide_ini: int | None = None
    sigrid_ide_fin: int | None = None
    sigrid_dia_ini: int | None = None
    sigrid_dia_fin: int | None = None
    # F-062 (R15): el día original del `CIZ` ajeno que movió su `fin`.
    sigrid_dia_fin_antes: int | None = None


@dataclass(frozen=True)
class Completado:
    """Lo que devuelve la regla pura `completar_hasta_100` (F-029): las
    líneas del trabajador tras completar y lo añadido (escala 0-100)."""

    lineas: list[Linea]
    anadido: Decimal


@dataclass(frozen=True)
class ResultadoCompletarTrabajador:
    """Resultado del lote para un trabajador (F-029, R25); `anadido` es 0
    si no se tocó."""

    trabajador_ide: int
    resultado: ResultadoCompletado
    anadido: Decimal = Decimal("0")


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


@dataclass(frozen=True)
class EventoPendiente:
    """Último evento no deshecho de un trabajador en un periodo: qué se
    restauraría al deshacer y quién lo hizo (F-027, `domain/deshacer.py`)."""

    id: int
    usuario: str
    snapshot_antes: list[dict[str, Any]]
    # Tipo del evento (F-030, R20): deshacer `INCIDENCIAS` restaura las
    # incidencias; los demás, las líneas.
    tipo: str = "GUARDAR"


@dataclass
class CuadranteTrabajador:
    """Fila del cuadrante: trabajador + sus líneas + estado calculado."""

    trabajador: Trabajador
    lineas: list[Linea] = field(default_factory=list)
    puede_deshacer: bool = False
    # Incidencias del trabajador en el periodo (F-030, R21). No entran en
    # `total` ni en el estado (R22): van aparte de las líneas.
    incidencias: tuple[Incidencia, ...] = ()

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
class PartidaVar:
    """Una partida del universo VAR (F-039, docs/ARCHITECTURE.md#regla-var):
    `ide`, `cod` y `res` de `obrparpar`."""

    ide: int
    cod: str
    res: str | None


@dataclass(frozen=True)
class ResultadoUniversoVar:
    """Universo VAR que devuelve el transfer (F-039): la obra VAR de la
    empresa y sus partidas; sin obra (`obra_ide` nulo), por qué."""

    obra_ide: int | None
    obra_cod: str | None
    empresa: int | None
    partidas: tuple[PartidaVar, ...]
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
    # Catálogo de incidencias de `auxhor` (F-030, R3), igual que empresas.
    incidencias: ResultadoSyncMaestro = field(
        default_factory=ResultadoSyncMaestro)
    # Recursos vinculados (F-044, R5), igual: sin sus pasos, a cero.
    vinculados: ResultadoSyncMaestro = field(
        default_factory=ResultadoSyncMaestro)


@dataclass(frozen=True)
class ResultadoCopia:
    """Resultado de copiar asignaciones desde el periodo anterior."""

    periodo_origen: Periodo | None
    trabajadores_copiados: int = 0
    con_carga_previa: int = 0
    sin_datos_origen: int = 0
    lineas_omitidas_obra_inactiva: int = 0
