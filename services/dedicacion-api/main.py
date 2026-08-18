# main.py
"""Arranque del microservicio dedicacion-api.

1. Crea la BBDD PostgreSQL si no existe (credenciales admin).
2. create_all idempotente del esquema.
3. Arranca uvicorn con la app FastAPI.
"""
from __future__ import annotations

import logging

import uvicorn

from config.settings import get_settings
from infrastructure.db.database import asegurar_base_datos, crear_engine
from infrastructure.db.orm_models import Base
from interface_adapters.api.app import build_app

logger = logging.getLogger("dedicacion-api")


def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Arrancando %s v%s", settings.service_name, settings.service_version)

    asegurar_base_datos(settings)
    engine = crear_engine(settings)
    Base.metadata.create_all(engine)
    logger.info("Esquema verificado en BBDD '%s'", settings.pg_db)

    app = build_app(settings)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level="info")


if __name__ == "__main__":
    main()
