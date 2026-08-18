# interface_adapters/api/deps.py
"""Composición de dependencias (wiring) del servicio."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from application.sync_pipeline import (
    FetchEmpleadosStep,
    FetchObrasStep,
    SyncMaestrosPipeline,
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
    categorias = cfg_emp.get("categorias_incluidas", [])
    filtro_cat = bool(cfg_emp.get("filtro_categorias", False))
    exigir_mes = bool(cfg_emp.get("filtro_codigo_mes", True))
    estados_exc = cfg_obr.get("estados_excluidos", [])
    filtro_est = bool(cfg_obr.get("filtro_estados", True))

    sigrid = SigridApiClient(settings)
    pipeline = SyncMaestrosPipeline(
        [
            FetchEmpleadosStep(sigrid, sql_empleados, categorias, filtro_cat,
                               exigir_codigo_mes=exigir_mes),
            FetchObrasStep(sigrid, sql_obras, estados_exc, filtro_est),
            UpsertTrabajadoresStep(),
            UpsertObrasStep(),
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
        ),
        exporter=exporter,
        registro_sigrid=RegistroSigrid(session_factory,
                                       TransferClient(settings)),
    )


def obtener_contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


def obtener_usuario(request: Request) -> str:
    """Usuario para auditoría: lo inyecta el front (Easy Auth) vía cabecera."""
    return request.headers.get("x-usuario", "local").strip() or "local"
