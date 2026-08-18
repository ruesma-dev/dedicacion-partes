# interface_adapters/api/routes.py
"""Endpoints REST del servicio dedicacion-api."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Response

from application.use_cases import (
    CambiarEstadoPeriodo,
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    CrearObtenerPeriodo,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    ListarPeriodos,
    ObtenerCuadrante,
    ObtenerFilaTrabajador,
)
from config.settings import cargar_config
from domain.models import EstadoPeriodo
from interface_adapters.api.deps import (
    Contenedor,
    obtener_contenedor,
    obtener_usuario,
)
from interface_adapters.api.schemas import (
    AsignacionesIn,
    CopiaPeriodoOut,
    CopiaTrabajadorOut,
    CuadranteOut,
    FilaOut,
    PeriodoCreadoOut,
    PeriodoIn,
    PeriodoOut,
    SyncOut,
    a_copia_periodo_out,
    a_obra_out,
    a_periodo_out,
    a_resumen_out,
    a_sync_out,
    a_trabajador_out,
    lineas_a_dicts,
)

router = APIRouter(prefix="/api/v1")

Cont = Annotated[Contenedor, Depends(obtener_contenedor)]
Usuario = Annotated[str, Depends(obtener_usuario)]


# --------------------------- Salud ------------------------------------
@router.get("/health", tags=["salud"])
def health(contenedor: Cont) -> dict[str, Any]:
    return {
        "ok": True,
        "service": contenedor.settings.service_name,
        "version": contenedor.settings.service_version,
        "sigrid_configurado": contenedor.settings.sigrid_configurado,
    }


# --------------------------- Sincronización ---------------------------
@router.post("/sync", response_model=SyncOut, tags=["sync"])
def sincronizar(contenedor: Cont) -> SyncOut:
    with contenedor.uow() as uow:
        resultado = contenedor.sync_pipeline.ejecutar(uow)
    return a_sync_out(resultado)


@router.get("/sync/preview", tags=["sync"])
def preview_sync(contenedor: Cont) -> dict[str, Any]:
    return contenedor.preview_sync.ejecutar()


# --------------------------- Periodos ---------------------------------
@router.get("/periodos", tags=["periodos"])
def listar_periodos(contenedor: Cont) -> dict[str, list[PeriodoOut]]:
    with contenedor.uow() as uow:
        periodos = ListarPeriodos().ejecutar(uow)
    return {"periodos": [a_periodo_out(p) for p in periodos]}


@router.post("/periodos", response_model=PeriodoCreadoOut, tags=["periodos"])
def crear_periodo(payload: PeriodoIn, contenedor: Cont) -> PeriodoCreadoOut:
    with contenedor.uow() as uow:
        periodo, creado = CrearObtenerPeriodo().ejecutar(
            uow, payload.anio, payload.mes
        )
    return PeriodoCreadoOut(
        anio=periodo.anio, mes=periodo.mes, estado=periodo.estado.value, creado=creado
    )


@router.post("/periodos/{anio}/{mes}/cerrar", response_model=PeriodoOut,
             tags=["periodos"])
def cerrar_periodo(anio: int, mes: int, contenedor: Cont) -> PeriodoOut:
    with contenedor.uow() as uow:
        periodo = CambiarEstadoPeriodo().ejecutar(
            uow, anio, mes, EstadoPeriodo.CERRADO
        )
    return a_periodo_out(periodo)


@router.post("/periodos/{anio}/{mes}/reabrir", response_model=PeriodoOut,
             tags=["periodos"])
def reabrir_periodo(anio: int, mes: int, contenedor: Cont) -> PeriodoOut:
    with contenedor.uow() as uow:
        periodo = CambiarEstadoPeriodo().ejecutar(
            uow, anio, mes, EstadoPeriodo.ABIERTO
        )
    return a_periodo_out(periodo)


@router.post("/periodos/{anio}/{mes}/copiar-anterior",
             response_model=CopiaPeriodoOut, tags=["periodos"])
def copiar_periodo_anterior(
    anio: int, mes: int, contenedor: Cont, usuario: Usuario
) -> CopiaPeriodoOut:
    with contenedor.uow() as uow:
        resultado = CopiarPeriodoAnterior().ejecutar(uow, anio, mes, usuario)
    return a_copia_periodo_out(resultado)


# --------------------------- Cuadrante --------------------------------
@router.get("/periodos/{anio}/{mes}/cuadrante", response_model=CuadranteOut,
            tags=["cuadrante"])
def obtener_cuadrante(anio: int, mes: int, contenedor: Cont) -> CuadranteOut:
    with contenedor.uow() as uow:
        cuadrante = ObtenerCuadrante().ejecutar(uow, anio, mes)
    return CuadranteOut(
        periodo=a_periodo_out(cuadrante.periodo),
        obras=[a_obra_out(o) for o in cuadrante.obras],
        trabajadores=[a_trabajador_out(f) for f in cuadrante.filas],
        resumen=a_resumen_out(cuadrante.resumen),
    )


@router.put(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/asignaciones",
    response_model=FilaOut,
    tags=["cuadrante"],
)
def guardar_asignaciones(
    anio: int,
    mes: int,
    trabajador_ide: int,
    payload: AsignacionesIn,
    contenedor: Cont,
    usuario: Usuario,
) -> FilaOut:
    with contenedor.uow() as uow:
        fila, resumen = GuardarAsignaciones().ejecutar(
            uow, anio, mes, trabajador_ide, lineas_a_dicts(payload), usuario
        )
    return FilaOut(trabajador=a_trabajador_out(fila), resumen=a_resumen_out(resumen))


@router.post(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/deshacer",
    response_model=FilaOut,
    tags=["cuadrante"],
)
def deshacer(
    anio: int, mes: int, trabajador_ide: int, contenedor: Cont, usuario: Usuario
) -> FilaOut:
    with contenedor.uow() as uow:
        fila, resumen = DeshacerUltimaModificacion().ejecutar(
            uow, anio, mes, trabajador_ide, usuario
        )
    return FilaOut(trabajador=a_trabajador_out(fila), resumen=a_resumen_out(resumen))


@router.post(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/copiar-anterior",
    response_model=CopiaTrabajadorOut,
    tags=["cuadrante"],
)
def copiar_trabajador_anterior(
    anio: int, mes: int, trabajador_ide: int, contenedor: Cont, usuario: Usuario
) -> CopiaTrabajadorOut:
    with contenedor.uow() as uow:
        fila, resumen, origen, omitidas = CopiarTrabajadorAnterior().ejecutar(
            uow, anio, mes, trabajador_ide, usuario
        )
    return CopiaTrabajadorOut(
        trabajador=a_trabajador_out(fila),
        resumen=a_resumen_out(resumen),
        periodo_origen=a_periodo_out(origen) if origen else None,
        lineas_omitidas_obra_inactiva=omitidas,
    )


# --------------------------- Export -----------------------------------
@router.get("/periodos/{anio}/{mes}/export.xlsx", tags=["export"])
def exportar(anio: int, mes: int, contenedor: Cont) -> Response:
    with contenedor.uow() as uow:
        cuadrante = ObtenerCuadrante().ejecutar(uow, anio, mes)
    contenido = contenedor.exporter.exportar(cuadrante.periodo, cuadrante.filas)
    plantilla = cargar_config()["export"]["nombre_fichero"]
    nombre = plantilla.format(anio=anio, mes=mes)
    return Response(
        content=contenido,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


# Referencia usada solo para tipado en tiempo de análisis.
_ = ObtenerFilaTrabajador


# ----------------------- Registro en Sigrid ---------------------------
@router.post("/periodos/{anio}/{mes}/registro/preflight", tags=["sigrid"])
def registro_preflight(anio: int, mes: int, contenedor: Cont,
                       payload: dict = Body(default={})) -> dict[str, Any]:
    """Analiza qué se registraría (no escribe). Admite `trabajador_ide`
    para el registro de una sola línea y `overrides` de partida."""
    overrides = {int(k): int(v) for k, v in
                 (payload.get("overrides") or {}).items()}
    return contenedor.registro_sigrid.preflight(
        anio, mes, overrides,
        trabajador_ide=payload.get("trabajador_ide"))


@router.post("/periodos/{anio}/{mes}/registro/ejecutar", tags=["sigrid"])
def registro_ejecutar(anio: int, mes: int, contenedor: Cont,
                      payload: dict = Body(default={})) -> dict[str, Any]:
    """Escribe en Sigrid vía porcentajes-transfer y deja la traza."""
    overrides = {int(k): int(v) for k, v in
                 (payload.get("overrides") or {}).items()}
    return contenedor.registro_sigrid.ejecutar(
        anio, mes, pisar_claves=list(payload.get("pisar_claves") or []),
        overrides=overrides, usuario=str(payload.get("usuario") or "local"),
        trabajador_ide=payload.get("trabajador_ide"))
