# interface_adapters/api/schemas.py
"""Schemas Pydantic v2 (contratos de entrada/salida de la API REST)."""
from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from application.estado_partida import Marcas, estado_de_linea, estado_de_subfila
from domain.empresas import linea_de_otra_empresa
from domain.estados import calcular_desviacion, calcular_estado
from domain.importes import TipoCantidad, importes_del_mes, tipo_de
from domain.models import (
    CuadranteTrabajador,
    Incidencia,
    Obra,
    Periodo,
    ResultadoCompletarTrabajador,
    ResultadoCopia,
    ResultadoSync,
    ResumenPeriodo,
)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------- Entrada ----------------------------------
class LineaIn(_Base):
    obra_ide: int
    es_postventa: bool = False
    porcentaje: Decimal = Field(gt=0, le=100, max_digits=6, decimal_places=2)
    # F-069 (R9): el comentario de la línea; sin la clave, se conserva.
    comentario: str | None = None


class ImporteIn(_Base):
    """F-069 (R4): la cantidad y el comentario de un vinculado de cantidad;
    `obra_ide`/`es_postventa`, solo en los por obra (caja). `cantidad` como
    número o texto (la valida `domain/importes.py`, R5); `null`, sin
    cantidad (D19: el comentario se guarda igual). `revisado: true` es
    «Revisado» (D18): quita el `copiado` aunque la cantidad no cambie."""

    vinculado_ide: Any
    obra_ide: Any = None
    es_postventa: Any = False
    cantidad: Any = None
    comentario: Any = None
    revisado: Any = None


class ImportesIn(_Base):
    importes: list[ImporteIn] = Field(max_length=500)


class AsignacionesIn(_Base):
    lineas: list[LineaIn]


class IncidenciaIn(_Base):
    """Una incidencia tal como la teclea el usuario (F-030, R17): días
    vacíos = mes entero (los completa la api). `id`, el de una ya guardada
    (R36, R37); sin él, es nueva."""

    id: int | None = None
    obra_ide: int
    codigo: str
    dia_desde: int | None = None
    dia_hasta: int | None = None


class IncidenciasIn(_Base):
    incidencias: list[IncidenciaIn]


class PeriodoIn(_Base):
    anio: int = Field(ge=2020, le=2100)
    mes: int = Field(ge=1, le=12)


class PartidaElegidaIn(_Base):
    """Partida elegida en el selector (F-050, R13): la de Sigrid."""

    ide: int = Field(gt=0)
    cod: str | None = None
    res: str | None = None


class PartidaIn(_Base):
    """`PUT …/partida` (F-050, R13): la línea (obra + modo) y su partida;
    `partida` nula = automática."""

    obra_ide: int
    es_postventa: bool = False
    partida: PartidaElegidaIn | None
    # F-044 (R8): la subfila de ese vinculado bajo la línea; sin él, la
    # partida del titular (F-050, como hoy).
    vinculado_ide: int | None = Field(default=None, gt=0)


class CompletarIn(_Base):
    """Lote «completar al 100 %» (F-029, R14). Sin porcentajes: lo que
    falta lo calcula la API (R12)."""

    trabajadores: list[int] = Field(min_length=1, max_length=500)
    obra_ide: int
    es_postventa: bool = False


class AceptarSigridIn(_Base):
    """Una entrada de Sigrid que el usuario acepta (F-054, R19)."""

    trabajador_ide: int
    obra_ide: int
    es_postventa: bool = False


class TraerSigridIn(_Base):
    """`POST …/traer-sigrid` (F-054, R18-R19): sin `aceptar`, solo
    compara."""

    aceptar: list[AceptarSigridIn] = Field(default_factory=list,
                                           max_length=5000)


# --------------------------- Salida -----------------------------------
class SubfilaOut(_Base):
    """La subfila de un vinculado bajo una línea (F-044, R6, R7): tipo y
    código del recurso, su partida elegida (las tres nulas = automática),
    si es fija (la de la línea VAR) y su propuesta guardada. Sin %: es el
    de la línea (R7)."""

    vinculado_ide: int
    tipo: str | None
    tipo_res: str | None
    cod: str | None
    partida_ide: int | None
    partida_cod: str | None
    partida_res: str | None
    partida_fija: bool
    propuesta_cod: str | None = None
    propuesta_res: str | None = None
    propuesta_metodo: str | None = None
    # F-074 (R14): en su cola («buscando partida…») o en su memoria de «sin
    # propuesta» («no encuentra partida», con el motivo del transfer). Las
    # claves solo salen con valor (`application/estado_partida.py`).
    propuesta_pendiente: bool | None = Field(default=None,
                                             exclude_if=lambda v: v is None)
    propuesta_no_encontrada: bool | None = Field(
        default=None, exclude_if=lambda v: v is None)
    propuesta_motivo: str | None = Field(default=None,
                                         exclude_if=lambda v: v is None)
    # F-069 (R10): si el vinculado es de cantidad, su reparto y su unidad y,
    # si es por obra, su cantidad aquí, si es copiada y su comentario. Las
    # claves solo salen con valor (sin cantidad, la subfila de siempre).
    reparto: str | None = Field(default=None, exclude_if=lambda v: v is None)
    unidad: str | None = Field(default=None, exclude_if=lambda v: v is None)
    cantidad: float | None = Field(default=None,
                                   exclude_if=lambda v: v is None)
    copiado: bool | None = Field(default=None, exclude_if=lambda v: v is None)
    comentario: str | None = Field(default=None,
                                   exclude_if=lambda v: v is None)


class ImporteOut(_Base):
    """F-069 (R10): la cantidad DEL MES de un vinculado por %."""

    vinculado_ide: int
    tipo: str | None
    cod: str | None
    unidad: str | None
    cantidad: float | None
    copiado: bool
    comentario: str | None


class LineaOut(_Base):
    obra_ide: int
    cod: str
    descripcion: str
    es_postventa: bool
    porcentaje: float
    obra_activa: bool
    obra_empresa: int | None
    otra_empresa: bool
    # F-025 (R18): la marca de la obra y si la línea se ofrece hoy en su modo
    # (`Linea.ofrecible`). El front no lo calcula: lo pinta.
    obra_admite_postventa: bool
    ofrecible: bool
    # F-050 (R18): la partida elegida (las tres nulas = automática) y si es
    # fija (entrada VAR, sin selector).
    partida_ide: int | None
    partida_cod: str | None
    partida_res: str | None
    partida_fija: bool
    # F-055 (R27): la propuesta guardada (la celda Partida la enseña en
    # cursiva con su método); las tres nulas = sin propuesta.
    propuesta_cod: str | None = None
    propuesta_res: str | None = None
    propuesta_metodo: str | None = None
    # F-057: la línea está en la cola de las propuestas del mes (en cola o
    # calculándose): el front dice «buscando partida…» solo en estas.
    propuesta_pendiente: bool = False
    # F-074 (R12, R13): en la memoria de «sin propuesta» (o, en postventa,
    # su obra no casa): «no encuentra partida», con el motivo del transfer.
    # Solo con valor. La de postventa publica como propuesta la de su obra
    # (método `postventa`).
    propuesta_no_encontrada: bool | None = Field(
        default=None, exclude_if=lambda v: v is None)
    propuesta_motivo: str | None = Field(default=None,
                                         exclude_if=lambda v: v is None)
    # F-044 (R6): las subfilas de los vinculados del trabajador; la clave
    # solo sale si hay alguna (sin vinculados, la línea de siempre).
    vinculados: list[SubfilaOut] = Field(default_factory=list,
                                         exclude_if=lambda v: not v)
    # F-069 (R9, R13): el comentario del titular; sin él, sin la clave.
    comentario: str | None = Field(default=None,
                                   exclude_if=lambda v: v is None)


class IncidenciaOut(_Base):
    """Incidencia de un trabajador (F-030, R21): obra, código con su letra y
    nombre, días, si está `quitada` (R38) y la traza del registro en Sigrid."""

    id: int | None
    obra_ide: int
    obra_cod: str
    obra_descripcion: str
    codigo: str
    letra: str
    nombre: str
    dia_desde: int
    dia_hasta: int
    sigrid_estado: str | None
    sigrid_parte_cod: str | None
    sigrid_motivo: str | None
    quitada: bool = False


class TipoIncidenciaOut(_Base):
    codigo: str
    letra: str
    nombre: str
    # F-061: palabras extra del buscador y posición de su entrada en
    # `config.yaml` (desempate del desplegable); sin entrada, [] y None.
    palabras: list[str] = []
    orden_busqueda: int | None = None


class TiposIncidenciaOut(_Base):
    incidencias: list[TipoIncidenciaOut]


class TrabajadorOut(_Base):
    ide: int
    nombre: str
    categoria: str | None
    activo: bool
    empresa: int | None
    lineas: list[LineaOut]
    total: float
    desviacion: float
    estado: str
    puede_deshacer: bool
    # F-030 (R21): las incidencias del trabajador; no cuentan en `total`.
    incidencias: list[IncidenciaOut] = []
    # F-069 (R10): las cantidades del mes de sus vinculados por %; sin
    # ninguno, sin la clave.
    importes: list[ImporteOut] = Field(default_factory=list,
                                       exclude_if=lambda v: not v)


class ObraOut(_Base):
    ide: int
    cod: str
    descripcion: str
    activa: bool
    estado_sigrid: str | None
    # F-025 (R17): se ofrece como `Postv-` (normal, si `activa`).
    admite_postventa: bool


class PeriodoOut(_Base):
    anio: int
    mes: int
    estado: str


class ResumenOut(_Base):
    total: int
    ok: int
    falta: int
    exceso: int
    sin_carga: int


class CuadranteOut(_Base):
    periodo: PeriodoOut
    empresa: int
    obras: list[ObraOut]
    trabajadores: list[TrabajadorOut]
    resumen: ResumenOut
    # F-055 (R30): alguna línea del periodo en la cola de propuestas.
    propuestas_en_curso: bool = False


class PropuestaLineaOut(_Base):
    """Una automática con propuesta guardada (F-055, R35)."""

    trabajador_ide: int
    obra_ide: int
    es_postventa: bool
    propuesta_cod: str | None
    propuesta_res: str | None
    propuesta_metodo: str | None


class PendienteOut(_Base):
    """Una línea en la cola de las propuestas del mes (F-057)."""

    trabajador_ide: int
    obra_ide: int
    es_postventa: bool


class PropuestaSubfilaOut(_Base):
    """Una subfila de vinculado automática con propuesta guardada (F-044,
    R9)."""

    trabajador_ide: int
    obra_ide: int
    es_postventa: bool
    vinculado_ide: int
    propuesta_cod: str | None
    propuesta_res: str | None
    propuesta_metodo: str | None


class NoEncontradaOut(_Base):
    """Una línea en la memoria de «sin propuesta», con el motivo del
    transfer (F-074, R13)."""

    trabajador_ide: int
    obra_ide: int
    es_postventa: bool
    motivo: str | None = None


class SubfilaPendienteOut(_Base):
    """Una subfila en la cola de las propuestas del mes (F-074, R14)."""

    trabajador_ide: int
    obra_ide: int
    es_postventa: bool
    vinculado_ide: int


class SubfilaNoEncontradaOut(SubfilaPendienteOut):
    """Una subfila en su memoria de «sin propuesta» (F-074, R14)."""

    motivo: str | None = None


class PropuestasOut(_Base):
    """`GET …/propuestas` (F-055, R35; F-057 `pendientes`; F-044 R9
    `subfilas`). Sin declarar `subfilas`, `extra="forbid"` daba 500 en
    cuanto una subfila tenía propuesta (hotfix del 2026-11-03). F-074 (R13,
    R14): `no_encontradas`, `subfilas_pendientes` y
    `subfilas_no_encontradas`, solo si hay alguna (la ruta excluye lo no
    puesto)."""

    en_curso: bool
    lineas: list[PropuestaLineaOut]
    pendientes: list[PendienteOut]
    subfilas: list[PropuestaSubfilaOut] = []
    no_encontradas: list[NoEncontradaOut] = []
    subfilas_pendientes: list[SubfilaPendienteOut] = []
    subfilas_no_encontradas: list[SubfilaNoEncontradaOut] = []


class EmpresaOut(_Base):
    empresa: int
    nombre: str
    # De baja o desactivada en Sigrid (F-032): el front la marca, la API decide.
    de_baja: bool


class EmpresasOut(_Base):
    por_defecto: int
    empresas: list[EmpresaOut]


class FilaOut(_Base):
    trabajador: TrabajadorOut
    resumen: ResumenOut
    # F-055 (R37): alguna línea del periodo en la cola de propuestas.
    propuestas_en_curso: bool = False


class CopiaTrabajadorOut(FilaOut):
    periodo_origen: PeriodoOut | None
    lineas_omitidas_obra_inactiva: int


class CopiaPeriodoOut(_Base):
    periodo_origen: PeriodoOut | None
    trabajadores_copiados: int
    con_carga_previa: int
    sin_datos_origen: int
    lineas_omitidas_obra_inactiva: int
    propuestas_en_curso: bool = False       # F-055 (R37)


class ResultadoCompletarOut(_Base):
    trabajador_ide: int
    resultado: str
    anadido: float  # escala 0-100; 0 si no se tocó


class CompletarOut(_Base):
    """Respuesta del lote (F-029, R25): sin filas; el front recarga el
    cuadrante, que ya trae `puede_deshacer` por usuario."""

    resultados: list[ResultadoCompletarOut]
    resumen: ResumenOut
    propuestas_en_curso: bool = False       # F-055 (R37)


class SyncMaestroOut(_Base):
    recibidos: int
    altas: int
    actualizados: int
    desactivados: int


class SyncOut(_Base):
    empleados: SyncMaestroOut
    obras: SyncMaestroOut
    duracion_s: float
    empresas: SyncMaestroOut  # catálogo auxemp (F-032)
    incidencias: SyncMaestroOut  # catálogo auxhor (F-030)


class PeriodoCreadoOut(PeriodoOut):
    creado: bool


class ErrorOut(_Base):
    error: str


# --------------------------- Mapeos -----------------------------------
def a_periodo_out(periodo: Periodo) -> PeriodoOut:
    return PeriodoOut(anio=periodo.anio, mes=periodo.mes, estado=periodo.estado.value)


def a_obra_out(obra: Obra) -> ObraOut:
    return ObraOut(
        ide=obra.ide,
        cod=obra.cod,
        descripcion=obra.descripcion,
        activa=obra.activa,
        estado_sigrid=obra.estado_sigrid,
        admite_postventa=obra.admite_postventa,
    )


def a_trabajador_out(
    fila: CuadranteTrabajador, empresa_obras: int,
    pendientes: AbstractSet[tuple[int, int, bool]] = frozenset(),
    tipos: Mapping[str, TipoCantidad] | None = None,
    *, marcas: Marcas | None = None,
) -> TrabajadorOut:
    """`empresa_obras` es la empresa de las obras (`EMPRESA_IMPUTACION`), no
    la elegida: decide `otra_empresa` de cada línea (F-034, R5).
    `pendientes` son las líneas `(trabajador, obra, es_postventa)` en la cola
    de propuestas (F-057): marcan `propuesta_pendiente` por identidad.
    F-074 (R12-R14): `marcas`, la foto entera de la cola (si viene, manda
    sobre `pendientes`); las claves de la propuesta de cada línea y subfila
    las decide `application/estado_partida.py`."""
    tipos = tipos or {}
    marcas = marcas if marcas is not None else Marcas(
        pendientes=frozenset(pendientes))
    ide = fila.trabajador.ide
    total = fila.total
    estado = calcular_estado(total, len(fila.lineas))
    desviacion = calcular_desviacion(total, len(fila.lineas))
    return TrabajadorOut(
        ide=fila.trabajador.ide,
        nombre=fila.trabajador.nombre,
        categoria=fila.trabajador.categoria,
        activo=fila.trabajador.activo,
        empresa=fila.trabajador.empresa,
        lineas=[
            LineaOut(
                obra_ide=ln.obra_ide,
                cod=ln.cod,
                descripcion=ln.descripcion,
                es_postventa=ln.es_postventa,
                porcentaje=float(ln.porcentaje),
                obra_activa=ln.obra_activa,
                obra_empresa=ln.obra_empresa,
                otra_empresa=linea_de_otra_empresa(ln.obra_empresa,
                                                   empresa_obras),
                obra_admite_postventa=ln.obra_admite_postventa,
                ofrecible=ln.ofrecible,
                partida_ide=ln.partida_ide,
                partida_cod=ln.partida_cod,
                partida_res=ln.partida_res,
                partida_fija=ln.partida_fija,
                **estado_de_linea(ide, ln, marcas),
                vinculados=[
                    SubfilaOut(
                        vinculado_ide=v.vinculado_ide, tipo=v.tipo,
                        tipo_res=v.tipo_res, cod=v.cod,
                        partida_ide=v.partida_ide, partida_cod=v.partida_cod,
                        partida_res=v.partida_res,
                        partida_fija=ln.partida_fija,
                        **estado_de_subfila(ide, ln, v, marcas),
                        **_cantidad_out(v, tipo_de(v.tipo, tipos)))
                    for v in ln.vinculados],
                comentario=ln.comentario,
            )
            for ln in fila.lineas
        ],
        importes=[
            ImporteOut(vinculado_ide=i.vinculado_ide, tipo=i.tipo, cod=i.cod,
                       unidad=i.unidad,
                       cantidad=None if i.cantidad is None
                       else float(i.cantidad),
                       copiado=i.copiado, comentario=i.comentario)
            for i in importes_del_mes(
                fila.lineas, {i.vinculado_ide: i for i in fila.importes},
                tipos)],
        total=float(total),
        desviacion=float(desviacion),
        estado=estado.value,
        puede_deshacer=fila.puede_deshacer,
        incidencias=[a_incidencia_out(i) for i in fila.incidencias],
    )


def _cantidad_out(v: Any, tipo: TipoCantidad | None) -> dict[str, Any]:
    """F-069 (R10): lo de cantidad de una subfila; {} si no es de cantidad.
    En los por % la cantidad es la del mes (`importes`), no la de aquí."""
    if tipo is None:
        return {}
    out: dict[str, Any] = {"reparto": tipo.reparto, "unidad": tipo.unidad}
    if tipo.reparto == "obra":
        out["cantidad"] = None if v.cantidad is None else float(v.cantidad)
        out["copiado"] = bool(v.copiado) if v.cantidad is not None else None
        out["comentario"] = v.comentario
    return out


def a_incidencia_out(inc: Incidencia) -> IncidenciaOut:
    return IncidenciaOut(
        id=inc.id, obra_ide=inc.obra_ide, obra_cod=inc.obra_cod,
        obra_descripcion=inc.obra_descripcion, codigo=inc.codigo,
        letra=inc.letra, nombre=inc.nombre, dia_desde=inc.dia_desde,
        dia_hasta=inc.dia_hasta, sigrid_estado=inc.sigrid_estado,
        sigrid_parte_cod=inc.sigrid_parte_cod, sigrid_motivo=inc.sigrid_motivo,
        quitada=inc.quitada)


def a_resumen_out(resumen: ResumenPeriodo) -> ResumenOut:
    return ResumenOut(
        total=resumen.total,
        ok=resumen.ok,
        falta=resumen.falta,
        exceso=resumen.exceso,
        sin_carga=resumen.sin_carga,
    )


def a_sync_out(resultado: ResultadoSync) -> SyncOut:
    return SyncOut(
        empleados=SyncMaestroOut(**resultado.empleados.__dict__),
        obras=SyncMaestroOut(**resultado.obras.__dict__),
        duracion_s=resultado.duracion_s,
        empresas=SyncMaestroOut(**resultado.empresas.__dict__),
        incidencias=SyncMaestroOut(**resultado.incidencias.__dict__),
    )


def a_copia_periodo_out(resultado: ResultadoCopia) -> CopiaPeriodoOut:
    return CopiaPeriodoOut(
        periodo_origen=(
            a_periodo_out(resultado.periodo_origen)
            if resultado.periodo_origen
            else None
        ),
        trabajadores_copiados=resultado.trabajadores_copiados,
        con_carga_previa=resultado.con_carga_previa,
        sin_datos_origen=resultado.sin_datos_origen,
        lineas_omitidas_obra_inactiva=resultado.lineas_omitidas_obra_inactiva,
    )


def a_completar_out(
    resultados: list[ResultadoCompletarTrabajador], resumen: ResumenPeriodo
) -> CompletarOut:
    return CompletarOut(
        resultados=[
            ResultadoCompletarOut(
                trabajador_ide=r.trabajador_ide,
                resultado=r.resultado.value,
                anadido=float(r.anadido),
            )
            for r in resultados
        ],
        resumen=a_resumen_out(resumen),
    )


def lineas_a_dicts(payload: AsignacionesIn) -> list[dict[str, Any]]:
    """F-069 (R9): la clave `comentario` solo si llegó (sin ella, el caso
    de uso conserva el guardado)."""
    return [
        {
            "obra_ide": ln.obra_ide,
            "es_postventa": ln.es_postventa,
            "porcentaje": str(ln.porcentaje),
            **({"comentario": ln.comentario}
               if "comentario" in ln.model_fields_set else {}),
        }
        for ln in payload.lineas
    ]


# ------------------- F-054 · traer de Sigrid (R27) --------------------
class EntradaSigridOut(_Base):
    """Una entrada del trabajador: estado, los dos %, la partida y el parte
    de Sigrid, cuántas líneas suma y, si no se puede traer, por qué."""

    obra_ide: int
    cod: str
    descripcion: str
    es_postventa: bool
    estado: str
    pct_sigrid: float | None
    pct_cuadrante: float | None
    partida_cod: str | None
    partida_res: str | None
    parte_cod: str | None
    n_lineas: int
    motivo: str | None


class ClaveEntradaOut(_Base):
    obra_ide: int
    es_postventa: bool


class RechazadaOut(_Base):
    trabajador_ide: int
    obra_ide: int
    es_postventa: bool
    motivo: str


class TrabajadorSigridOut(_Base):
    trabajador_ide: int
    cod: str | None
    nombre: str
    entradas: list[EntradaSigridOut]
    aceptadas: list[ClaveEntradaOut]


class NoTraidaOut(_Base):
    hmores_ide: int
    recurso_ide: int
    obra_cod: str | None
    parte_cod: str | None
    can: float
    motivo: str
    # F-054 T25 (R45): el trabajador del maestro, para pintarlo `cod · nombre`.
    recurso_cod: str | None
    recurso_nombre: str


class TraerSigridOut(_Base):
    trabajadores: list[TrabajadorSigridOut]
    aceptadas: int
    rechazadas: list[RechazadaOut]
    no_traidas: list[NoTraidaOut]
    fuera_maestro: int
    de_vinculados: int
    lineas_leidas: int
    excluidas_pruebas: int
    motivo_postventa: str | None
    motivo_var: str | None
    propuestas_en_curso: bool = False       # F-055 (R37), R26


def _pct(valor: Decimal | None) -> float | None:
    return None if valor is None else float(valor)


def a_traer_sigrid_out(r: Any) -> TraerSigridOut:
    """`ResultadoTraer` (application/traer_sigrid.py) a la salida (R27)."""
    def entrada(c: Any) -> EntradaSigridOut:
        obra = r.obras.get(c.obra_ide)
        e = c.entrada
        return EntradaSigridOut(
            obra_ide=c.obra_ide, cod=obra.cod if obra else str(c.obra_ide),
            descripcion=obra.descripcion if obra else "",
            es_postventa=c.es_postventa, estado=c.estado.value,
            pct_sigrid=_pct(c.pct_sigrid), pct_cuadrante=_pct(c.pct_cuadrante),
            partida_cod=e.partida_cod if e else None,
            partida_res=e.partida_res if e else None,
            parte_cod=e.parte_cod if e else None,
            n_lineas=e.n_lineas if e else 0, motivo=c.motivo)

    return TraerSigridOut(
        trabajadores=[TrabajadorSigridOut(
            trabajador_ide=t.trabajador.ide, cod=t.trabajador.cod,
            nombre=t.trabajador.nombre,
            entradas=[entrada(c) for c in t.comparadas],
            aceptadas=[ClaveEntradaOut(obra_ide=o, es_postventa=pv)
                       for o, pv in t.aceptadas])
            for t in r.trabajadores],
        aceptadas=sum(len(t.aceptadas) for t in r.trabajadores),
        rechazadas=[RechazadaOut(trabajador_ide=t, obra_ide=o,
                                 es_postventa=pv, motivo=m)
                    for (t, o, pv), m in r.rechazadas],
        no_traidas=[NoTraidaOut(
            hmores_ide=n.hmores_ide, recurso_ide=n.recurso_ide,
            obra_cod=n.obra_cod, parte_cod=n.parte_cod, can=n.can,
            motivo=n.motivo, recurso_cod=n.recurso_cod,
            recurso_nombre=n.recurso_nombre) for n in r.no_traidas],
        fuera_maestro=r.contadores.fuera_maestro,
        de_vinculados=r.contadores.de_vinculados,
        lineas_leidas=r.lineas_leidas,
        excluidas_pruebas=r.excluidas_pruebas,
        motivo_postventa=r.motivo_postventa, motivo_var=r.motivo_var)
