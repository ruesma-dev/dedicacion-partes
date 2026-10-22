# interface_adapters/api/routes.py
"""Endpoints REST del servicio dedicacion-api."""
from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query, Response

from application.use_cases import (
    CambiarEstadoPeriodo,
    CambiarPartida,
    CompletarHasta100,
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    CrearObtenerPeriodo,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    GuardarIncidencias,
    ListarEmpresas,
    ListarPeriodos,
    ListarTiposIncidencia,
    ObtenerCuadrante,
    ObtenerFilaTrabajador,
)
from config.settings import cargar_config
from domain.errors import ErrorDominio, ObraNoValida, TrabajadorNoValido
from domain.models import EstadoPeriodo, FiltroEmpresa
from interface_adapters.api.deps import (
    Contenedor,
    obtener_contenedor,
    obtener_usuario,
)
from interface_adapters.api.schemas import (
    AsignacionesIn,
    CompletarIn,
    CompletarOut,
    CopiaPeriodoOut,
    CopiaTrabajadorOut,
    CuadranteOut,
    EmpresaOut,
    EmpresasOut,
    FilaOut,
    IncidenciasIn,
    PartidaIn,
    PeriodoCreadoOut,
    PeriodoIn,
    PeriodoOut,
    PropuestasOut,
    SyncOut,
    TipoIncidenciaOut,
    TiposIncidenciaOut,
    a_completar_out,
    a_copia_periodo_out,
    a_obra_out,
    a_periodo_out,
    a_resumen_out,
    a_sync_out,
    a_trabajador_out,
    lineas_a_dicts,
)

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)

Cont = Annotated[Contenedor, Depends(obtener_contenedor)]
Usuario = Annotated[str, Depends(obtener_usuario)]
#: Empresa elegida en el selector (F-024, R6). Sin ella, la por defecto
#: (`EMPRESA_IMPUTACION`); si no es un entero > 0, 422 sin tocar nada.
EmpresaQ = Annotated[int | None, Query(gt=0)]


def _filtro(contenedor: Contenedor, empresa: int | None) -> FiltroEmpresa:
    """Filtro de la petición. `EMPRESA_IMPUTACION` es a la vez la por
    defecto y la empresa de las obras (D1 de F-034); separarlas mañana es
    cambiar solo esta función y `RegistroSigrid._filtro`."""
    empresa_imputacion = contenedor.settings.empresa_imputacion
    return FiltroEmpresa(empresa=empresa or empresa_imputacion,
                         por_defecto=empresa_imputacion,
                         empresa_obras=empresa_imputacion)


def _encolar(contenedor: Contenedor, anio: int, mes: int,
             trabajadores: Iterable[int] | None = None,
             ) -> tuple[bool, frozenset[tuple[int, int, bool]]]:
    """F-055 (R29, R30, R37): encola las propuestas pendientes del periodo
    (o de `trabajadores`) y devuelve `propuestas_en_curso` y (F-057) las
    líneas del periodo que siguen en la cola, leídas DESPUÉS de encolar.
    Siempre tras cerrar la UoW de la ruta; si encolar falla, `(False, ∅)` y
    un log: la respuesta no cambia por ello."""
    try:
        return contenedor.propuestas_mes.encolar(
            anio, mes, None if trabajadores is None else list(trabajadores))
    except Exception:                               # noqa: BLE001
        logger.warning("[propuestas] no se pudieron encolar las de %02d/%s",
                       mes, anio, exc_info=True)
        return False, frozenset()


def _entero_opcional(valor: Any, campo: str,
                     error: type[ErrorDominio]) -> int | None:
    """Un campo opcional del cuerpo como entero (F-050, review 3; F-056): un
    `"694"` de texto o un `694.0` valen como `694`, y `0` o un negativo son
    enteros. Lo que no es un entero (texto, decimales, booleano, lista,
    infinito) lanza `error`, que es 422 sin analizar ni escribir."""
    if valor is None:
        return None
    try:
        if isinstance(valor, bool) or (isinstance(valor, float)
                                       and not valor.is_integer()):
            raise ValueError
        return int(valor)
    except (TypeError, ValueError):
        raise error(f"{campo} no es un entero: {valor!r}") from None


def _obra_ide(valor: Any) -> int | None:
    """`obra_ide` del cuerpo del preflight (F-050, M2 punto 5)."""
    return _entero_opcional(valor, "obra_ide", ObraNoValida)


def _trabajador_ide(valor: Any) -> int | None:
    """`trabajador_ide` del cuerpo del registro (F-056): sin validar, un `0`,
    `""` o `false` quitaba el filtro y `ejecutar` registraba el mes entero."""
    return _entero_opcional(valor, "trabajador_ide", TrabajadorNoValido)


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
    # F-055 (R29, R32): tras el éxito, olvida «sin propuesta» y lanza las
    # propuestas de cada periodo ABIERTO (no se espera).
    contenedor.propuestas_mes.tras_sync()
    return a_sync_out(resultado)


@router.get("/sync/preview", tags=["sync"])
def preview_sync(contenedor: Cont) -> dict[str, Any]:
    return contenedor.preview_sync.ejecutar()


# --------------------------- Empresas ---------------------------------
@router.get("/empresas", response_model=EmpresasOut, tags=["empresas"])
def listar_empresas(contenedor: Cont) -> EmpresasOut:
    """Empresas del selector y la por defecto (F-024 R1); nombre y baja del
    catálogo de Sigrid sincronizado (F-032)."""
    caso = ListarEmpresas(contenedor.settings.empresa_imputacion)
    with contenedor.uow() as uow:
        por_defecto, empresas = caso.ejecutar(uow)
    return EmpresasOut(
        por_defecto=por_defecto,
        empresas=[EmpresaOut(empresa=e.numero, nombre=e.nombre, de_baja=e.de_baja)
                  for e in empresas],
    )


# --------------------------- Incidencias ------------------------------
@router.get("/incidencias", response_model=TiposIncidenciaOut,
            tags=["incidencias"])
def listar_incidencias(contenedor: Cont) -> TiposIncidenciaOut:
    """Catálogo del desplegable de incidencias (F-030, R6): las activas por
    orden de letra, sincronizadas de `auxhor`."""
    with contenedor.uow() as uow:
        tipos = ListarTiposIncidencia().ejecutar(uow)
    return TiposIncidenciaOut(incidencias=[
        TipoIncidenciaOut(codigo=t.codigo, letra=t.letra, nombre=t.nombre)
        for t in tipos])


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
    anio: int, mes: int, contenedor: Cont, usuario: Usuario,
    empresa: EmpresaQ = None,
) -> CopiaPeriodoOut:
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        resultado = CopiarPeriodoAnterior().ejecutar(
            uow, anio, mes, usuario, filtro=filtro
        )
    return a_copia_periodo_out(resultado).model_copy(
        update={"propuestas_en_curso": _encolar(contenedor, anio, mes)[0]})


# --------------------------- Cuadrante --------------------------------
@router.get("/periodos/{anio}/{mes}/cuadrante", response_model=CuadranteOut,
            tags=["cuadrante"])
def obtener_cuadrante(
    anio: int, mes: int, contenedor: Cont, usuario: Usuario,
    empresa: EmpresaQ = None,
) -> CuadranteOut:
    """`puede_deshacer` de cada fila es el del usuario que pregunta (F-027).
    Un periodo ABIERTO encola sus propuestas pendientes (F-055, R29) y
    publica `propuestas_en_curso`; no las espera (R30)."""
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        cuadrante = ObtenerCuadrante().ejecutar(uow, anio, mes, filtro,
                                                usuario=usuario)
    en_curso, pendientes = _encolar(contenedor, anio, mes)
    return CuadranteOut(
        propuestas_en_curso=en_curso,
        periodo=a_periodo_out(cuadrante.periodo),
        empresa=cuadrante.empresa,
        obras=[a_obra_out(o) for o in cuadrante.obras],
        trabajadores=[
            a_trabajador_out(f, filtro.empresa_obras, pendientes)
            for f in cuadrante.filas
        ],
        resumen=a_resumen_out(cuadrante.resumen),
    )


@router.get("/periodos/{anio}/{mes}/propuestas", response_model=PropuestasOut,
            tags=["cuadrante"])
def propuestas_del_mes(anio: int, mes: int,
                       contenedor: Cont) -> PropuestasOut:
    """F-055 (R35): si hay propuestas en curso y las automáticas con
    propuesta guardada del periodo; F-057: las líneas que siguen en la cola
    (`pendientes`). Solo lee."""
    with contenedor.uow() as uow:
        return PropuestasOut(**contenedor.propuestas_mes.estado(uow, anio,
                                                                mes))


@router.put(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/incidencias",
    response_model=FilaOut,
    tags=["cuadrante"],
)
def guardar_incidencias(
    anio: int,
    mes: int,
    trabajador_ide: int,
    payload: IncidenciasIn,
    contenedor: Cont,
    usuario: Usuario,
    empresa: EmpresaQ = None,
) -> FilaOut:
    """F-030 (R17-R19): sustituye las incidencias del trabajador; responde
    como el PUT de asignaciones."""
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        fila, resumen = GuardarIncidencias().ejecutar(
            uow, anio, mes, trabajador_ide,
            [i.model_dump() for i in payload.incidencias], usuario,
            filtro=filtro,
        )
    en_curso, pendientes = _encolar(contenedor, anio, mes, [trabajador_ide])
    return FilaOut(
        trabajador=a_trabajador_out(fila, filtro.empresa_obras, pendientes),
        resumen=a_resumen_out(resumen),
        propuestas_en_curso=en_curso,
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
    empresa: EmpresaQ = None,
) -> FilaOut:
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        fila, resumen = GuardarAsignaciones().ejecutar(
            uow, anio, mes, trabajador_ide, lineas_a_dicts(payload), usuario,
            filtro=filtro,
        )
    en_curso, pendientes = _encolar(contenedor, anio, mes, [trabajador_ide])
    return FilaOut(
        trabajador=a_trabajador_out(fila, filtro.empresa_obras, pendientes),
        resumen=a_resumen_out(resumen),
        propuestas_en_curso=en_curso,
    )


@router.get(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/partidas",
    tags=["cuadrante"],
)
def partidas_de_linea(
    anio: int,
    mes: int,
    trabajador_ide: int,
    obra_ide: int,
    contenedor: Cont,
    es_postventa: bool = False,
    empresa: EmpresaQ = None,
) -> dict[str, Any]:
    """Catálogo con el mayor de cada partida, propuesta, elegida y botón
    preelegido (`ambito`) de UNA línea (F-050, R17). Lo calcula el
    transfer; si no responde, 502 y el cuadrante sigue igual."""
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        return contenedor.partidas_linea.ejecutar(
            uow, anio, mes, trabajador_ide, obra_ide, es_postventa,
            empresa_obras=filtro.empresa_obras,
        )


@router.put(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/partida",
    response_model=FilaOut,
    tags=["cuadrante"],
)
def cambiar_partida(
    anio: int,
    mes: int,
    trabajador_ide: int,
    payload: PartidaIn,
    contenedor: Cont,
    usuario: Usuario,
    empresa: EmpresaQ = None,
) -> FilaOut:
    """Cambia la partida elegida de UNA línea y deja un evento `PARTIDA`
    (F-050, R13). `partida` nula = automática."""
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        fila, resumen = CambiarPartida().ejecutar(
            uow, anio, mes, trabajador_ide, payload.obra_ide,
            payload.es_postventa,
            payload.partida.model_dump() if payload.partida else None,
            usuario, filtro=filtro,
        )
    en_curso, pendientes = _encolar(contenedor, anio, mes, [trabajador_ide])
    return FilaOut(
        trabajador=a_trabajador_out(fila, filtro.empresa_obras, pendientes),
        resumen=a_resumen_out(resumen),
        propuestas_en_curso=en_curso,
    )


@router.post(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/deshacer",
    response_model=FilaOut,
    tags=["cuadrante"],
)
def deshacer(
    anio: int, mes: int, trabajador_ide: int, contenedor: Cont, usuario: Usuario,
    empresa: EmpresaQ = None,
) -> FilaOut:
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        fila, resumen = DeshacerUltimaModificacion().ejecutar(
            uow, anio, mes, trabajador_ide, usuario, filtro=filtro
        )
    en_curso, pendientes = _encolar(contenedor, anio, mes, [trabajador_ide])
    return FilaOut(
        trabajador=a_trabajador_out(fila, filtro.empresa_obras, pendientes),
        resumen=a_resumen_out(resumen),
        propuestas_en_curso=en_curso,
    )


@router.post(
    "/periodos/{anio}/{mes}/trabajadores/{trabajador_ide}/copiar-anterior",
    response_model=CopiaTrabajadorOut,
    tags=["cuadrante"],
)
def copiar_trabajador_anterior(
    anio: int, mes: int, trabajador_ide: int, contenedor: Cont, usuario: Usuario,
    empresa: EmpresaQ = None,
) -> CopiaTrabajadorOut:
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        fila, resumen, origen, omitidas = CopiarTrabajadorAnterior().ejecutar(
            uow, anio, mes, trabajador_ide, usuario, filtro=filtro
        )
    en_curso, pendientes = _encolar(contenedor, anio, mes, [trabajador_ide])
    return CopiaTrabajadorOut(
        trabajador=a_trabajador_out(fila, filtro.empresa_obras, pendientes),
        resumen=a_resumen_out(resumen),
        periodo_origen=a_periodo_out(origen) if origen else None,
        lineas_omitidas_obra_inactiva=omitidas,
        propuestas_en_curso=en_curso,
    )


@router.post(
    "/periodos/{anio}/{mes}/completar",
    response_model=CompletarOut,
    tags=["cuadrante"],
)
def completar_lote(
    anio: int,
    mes: int,
    payload: CompletarIn,
    contenedor: Cont,
    usuario: Usuario,
    empresa: EmpresaQ = None,
) -> CompletarOut:
    """Completa hasta el 100 % en la obra destino a los trabajadores del
    lote, en una transacción (F-029, docs/ARCHITECTURE.md#regla-completar).
    No registra en Sigrid ni llama al transfer."""
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        resultados, resumen = CompletarHasta100().ejecutar(
            uow, anio, mes, payload.trabajadores, payload.obra_ide,
            payload.es_postventa, usuario, filtro=filtro,
        )
    return a_completar_out(resultados, resumen).model_copy(update={
        "propuestas_en_curso": _encolar(contenedor, anio, mes,
                                        payload.trabajadores)[0]})


# --------------------------- Export -----------------------------------
@router.get("/periodos/{anio}/{mes}/export.xlsx", tags=["export"])
def exportar(
    anio: int, mes: int, contenedor: Cont, usuario: Usuario,
    empresa: EmpresaQ = None,
) -> Response:
    filtro = _filtro(contenedor, empresa)
    with contenedor.uow() as uow:
        cuadrante = ObtenerCuadrante().ejecutar(uow, anio, mes, filtro,
                                                usuario=usuario)
    contenido = contenedor.exporter.exportar(cuadrante.periodo, cuadrante.filas)
    plantilla = cargar_config()["export"]["nombre_fichero"]
    nombre = plantilla.format(anio=anio, mes=mes, empresa=cuadrante.empresa)
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
                       payload: dict = Body(default={}),
                       empresa: EmpresaQ = None) -> dict[str, Any]:
    """Analiza qué se registraría (no escribe). Admite `trabajador_ide`
    para el registro de una sola línea, `obra_ide` para analizar solo esa
    obra (F-050: el modal tras cambiar una partida) y `overrides` de
    partida. La empresa llega por query, como en el resto de rutas del
    periodo (F-024). `trabajador_ide` se valida antes de nada (F-056)."""
    trabajador_ide = _trabajador_ide(payload.get("trabajador_ide"))
    filtro = _filtro(contenedor, empresa)
    overrides = {int(k): int(v) for k, v in
                 (payload.get("overrides") or {}).items()}
    return contenedor.registro_sigrid.preflight(
        anio, mes, overrides,
        trabajador_ide=trabajador_ide,
        empresa=filtro.empresa, obra_ide=_obra_ide(payload.get("obra_ide")))


@router.post("/periodos/{anio}/{mes}/registro/ejecutar", tags=["sigrid"])
def registro_ejecutar(anio: int, mes: int, contenedor: Cont,
                      payload: dict = Body(default={}),
                      empresa: EmpresaQ = None) -> dict[str, Any]:
    """Escribe en Sigrid vía porcentajes-transfer y deja la traza, con la
    empresa elegida (F-024). `trabajador_ide` se valida antes de nada
    (F-056): un valor que no es entero es 422 y no se escribe."""
    trabajador_ide = _trabajador_ide(payload.get("trabajador_ide"))
    filtro = _filtro(contenedor, empresa)
    overrides = {int(k): int(v) for k, v in
                 (payload.get("overrides") or {}).items()}
    return contenedor.registro_sigrid.ejecutar(
        anio, mes, pisar_claves=list(payload.get("pisar_claves") or []),
        overrides=overrides, usuario=str(payload.get("usuario") or "local"),
        trabajador_ide=trabajador_ide,
        empresa=filtro.empresa)
