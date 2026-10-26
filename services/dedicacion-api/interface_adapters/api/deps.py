# interface_adapters/api/deps.py
"""Composición de dependencias (wiring) del servicio."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from application.filtros_maestros import CriterioActivoRecurso
from application.sync_pipeline import (
    ConfigVinculados,
    FetchEmpleadosStep,
    FetchEmpresasStep,
    FetchObrasStep,
    FetchTiposIncidenciaStep,
    FetchVinculadosStep,
    SyncMaestrosPipeline,
    UpsertEmpresasStep,
    UpsertObrasStep,
    UpsertTiposIncidenciaStep,
    UpsertTrabajadoresStep,
    UpsertVinculadosStep,
)
from application.palabras_incidencia import palabras_por_codigo
from application.partidas_linea import PartidasDeLinea
from application.propuestas_mes import PropuestasDelMes
from application.use_cases import PreviewSync
from config.settings import Settings, cargar_config
from infrastructure.db.repositories import SqlAlchemyUnitOfWork
from application.registro_sigrid import RegistroSigrid
from infrastructure.excel.exporter import OpenpyxlExcelExporter
from infrastructure.transfer.transfer_client import TransferClient
from infrastructure.sigrid.sigrid_client import SigridApiClient


@dataclass
class Contenedor:
    settings: Settings
    session_factory: sessionmaker[Session]
    sigrid: SigridApiClient
    sync_pipeline: SyncMaestrosPipeline
    preview_sync: PreviewSync
    exporter: OpenpyxlExcelExporter
    registro_sigrid: RegistroSigrid
    partidas_linea: PartidasDeLinea   # selector de partida (F-050, R17)
    # Propuestas del mes en segundo plano (F-055, R29-R33): un hilo.
    propuestas_mes: PropuestasDelMes

    def uow(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory)


def construir_contenedor(
    settings: Settings, session_factory: sessionmaker[Session]
) -> Contenedor:
    config = cargar_config()
    cfg_emp = config["sync"]["empleados"]
    cfg_obr = config["sync"]["obras"]
    sql_empleados = cfg_emp["sql"]
    sql_obras = cfg_obr["sql"]
    # Catálogo de empresas (F-032). Obligatorio, como las otras dos: sin él
    # la api no arranca, en vez de dejar de actualizar nombres en silencio.
    sql_empresas = config["sync"]["empresas"]["sql"]
    # Catálogo de incidencias (F-030, R3). Obligatorio, como el de empresas.
    sql_incidencias = config["sync"]["incidencias"]["sql"]
    # F-061: las palabras extra las lee la ruta en cada petición; aquí solo
    # se validan, para que una lista mal escrita no deje arrancar la api.
    palabras_por_codigo(config["sync"]["incidencias"].get("palabras_extra"))
    # Recursos vinculados (F-044, R1). Obligatoria, como las anteriores: mal
    # escrita, la api no arranca. La misma para el step y el preview.
    cfg_vinculados = ConfigVinculados.desde_config(config["sync"]["vinculados"])
    categorias = cfg_emp.get("categorias_incluidas", [])
    filtro_cat = bool(cfg_emp.get("filtro_categorias", False))
    exigir_mes = bool(cfg_emp.get("filtro_codigo_mes", True))
    estados_exc = cfg_obr.get("estados_excluidos", [])
    filtro_est = bool(cfg_obr.get("filtro_estados", True))
    # F-039 (docs/ARCHITECTURE.md#regla-seis-digitos): sin la clave, sin
    # filtro de código. El mismo número para el step y el preview.
    digitos_exc = int(cfg_obr.get("digitos_seguidos_excluidos", 0))
    # UN solo criterio para el step y para el preview (F-023 R18): lo que
    # enseña el preview es exactamente lo que el sync va a guardar.
    criterio = CriterioActivoRecurso(
        estados_excluidos=tuple(cfg_emp.get("estados_recurso_excluidos") or []),
        excluir_baja_anterior_a_ventana=bool(
            cfg_emp.get("excluir_baja_anterior_a_ventana", False)
        ),
        activo=bool(cfg_emp.get("filtro_estado_recurso", True)),
    )

    sigrid = SigridApiClient(settings)
    # UN cliente del transfer para los universos de postventa (F-025) y VAR
    # (F-039) del sync y del preview y para el registro; la empresa de las
    # obras es la que ya viaja en cada línea del registro
    # (EMPRESA_IMPUTACION, F-034).
    transfer = TransferClient(settings)
    empresa_obras = settings.empresa_imputacion
    pipeline = SyncMaestrosPipeline(
        [
            FetchEmpleadosStep(sigrid, sql_empleados, categorias, filtro_cat,
                               exigir_codigo_mes=exigir_mes,
                               criterio=criterio),
            FetchObrasStep(sigrid, sql_obras, estados_exc, filtro_est,
                           universo=transfer, empresa_obras=empresa_obras,
                           digitos_excluidos=digitos_exc),
            FetchTiposIncidenciaStep(sigrid, sql_incidencias),
            FetchEmpresasStep(sigrid, sql_empresas),
            # Tras los empleados: los trabajadores son los que se guardan.
            FetchVinculadosStep(sigrid, cfg_vinculados),
            UpsertTrabajadoresStep(),
            UpsertObrasStep(),
            UpsertTiposIncidenciaStep(),
            UpsertEmpresasStep(),
            # Tras los trabajadores: su clave ajena.
            UpsertVinculadosStep(),
        ]
    )
    exporter = OpenpyxlExcelExporter(
        prefijo_postventa=config["export"]["prefijo_postventa"]
    )
    return Contenedor(
        settings=settings,
        session_factory=session_factory,
        sigrid=sigrid,
        sync_pipeline=pipeline,
        preview_sync=PreviewSync(
            sigrid,
            sql_empleados,
            sql_obras,
            categorias_incluidas=categorias,
            filtro_categorias=filtro_cat,
            estados_excluidos=estados_exc,
            filtro_estados=filtro_est,
            exigir_codigo_mes=exigir_mes,
            criterio=criterio,
            sql_empresas=sql_empresas,
            # UoW solo para leer los periodos ABIERTO de la ventana de bajas
            # (F-026 R17); se resuelve al llamar, como `Contenedor.uow`.
            uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
            universo=transfer,
            empresa_obras=empresa_obras,
            digitos_excluidos=digitos_exc,
            sql_incidencias=sql_incidencias,
            vinculados=cfg_vinculados,
        ),
        exporter=exporter,
        registro_sigrid=RegistroSigrid(session_factory, transfer,
                                       settings.empresa_imputacion),
        partidas_linea=PartidasDeLinea(transfer),
        # F-055 (R30): UN hilo, cola por orden de llegada; estado de una
        # réplica (ARCHITECTURE «Topología»).
        propuestas_mes=PropuestasDelMes(
            lambda: SqlAlchemyUnitOfWork(session_factory), transfer,
            ThreadPoolExecutor(max_workers=1,
                               thread_name_prefix="propuestas"),
            empresa_obras=empresa_obras),
    )


def obtener_contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


def obtener_usuario(request: Request) -> str:
    """Usuario para auditoría: lo inyecta el front (Easy Auth) vía cabecera."""
    return request.headers.get("x-usuario", "local").strip() or "local"
