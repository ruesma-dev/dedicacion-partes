# interface_adapters/api/app.py
"""Factoría de la aplicación FastAPI del dedicacion-api."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config.settings import Settings, get_settings
from domain.errors import (
    ErrorDominio,
    LineasInvalidas,
    NadaQueDeshacer,
    ObraNoValida,
    PeriodoCerrado,
    PeriodoNoEncontrado,
    SigridError,
    SigridNoConfigurado,
    TrabajadorNoEncontrado,
)
from infrastructure.db.database import crear_engine, crear_session_factory
from interface_adapters.api.deps import construir_contenedor
from interface_adapters.api.routes import router

logger = logging.getLogger(__name__)

_HTTP_POR_ERROR: list[tuple[type[ErrorDominio], int]] = [
    (PeriodoNoEncontrado, 404),
    (TrabajadorNoEncontrado, 404),
    (PeriodoCerrado, 409),
    (NadaQueDeshacer, 409),
    (ObraNoValida, 422),
    (LineasInvalidas, 422),
    (SigridNoConfigurado, 503),
    (SigridError, 502),
]


def build_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version,
        docs_url="/docs",
    )

    engine = crear_engine(settings)
    session_factory = crear_session_factory(engine)
    app.state.contenedor = construir_contenedor(settings, session_factory)

    app.include_router(router)

    @app.exception_handler(ErrorDominio)
    async def manejar_error_dominio(
        request: Request, exc: ErrorDominio
    ) -> JSONResponse:
        codigo = 400
        for tipo, http in _HTTP_POR_ERROR:
            if isinstance(exc, tipo):
                codigo = http
                break
        logger.warning("%s: %s", type(exc).__name__, exc)
        return JSONResponse(status_code=codigo, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def manejar_error_generico(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Error no controlado")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error interno: {type(exc).__name__}"},
        )

    return app
