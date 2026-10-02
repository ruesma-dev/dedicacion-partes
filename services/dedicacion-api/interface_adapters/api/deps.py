# interface_adapters/api/deps.py
"""Composición de dependencias (wiring) del servicio."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from application.filtros_maestros import CriterioActivoRecurso
from application.sync_pipeline import (
    FetchEmpleadosStep,
    FetchEmpresasStep,
    FetchObrasStep,
    SyncMaestrosPipeline,
    UpsertEmpresasStep,
    UpsertObrasStep,
    UpsertTrabajadoresStep,
)
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
    categorias = cfg_emp.get("categorias_incluidas", [])
    filtro_cat = bool(cfg_emp.get("filtro_categorias", False))
    exigir_mes = bool(cfg_emp.get("filtro_codigo_mes", True))
    estados_exc = cfg_obr.get("estados_excluidos", [])
    filtro_est = bool(cfg_obr.get("filtro_estados", True))
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
    pipeline = SyncMaestrosPipeline(
        [
            FetchEmpleadosStep(sigrid, sql_empleados, categorias, filtro_cat,
                               exigir_codigo_mes=exigir_mes,
                               criterio=criterio),
            FetchObrasStep(sigrid, sql_obras, estados_exc, filtro_est),
            FetchEmpresasStep(sigrid, sql_empresas),
            UpsertTrabajadoresStep(),
            UpsertObrasStep(),
            UpsertEmpresasStep(),
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
        ),
        exporter=exporter,
        registro_sigrid=RegistroSigrid(session_factory,
                                       TransferClient(settings),
                                       settings.empresa_imputacion),
    )


def obtener_contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


def obtener_usuario(request: Request) -> str:
    """Usuario para auditoría: lo inyecta el front (Easy Auth) vía cabecera."""
    return request.headers.get("x-usuario", "local").strip() or "local"
