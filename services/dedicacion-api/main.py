# main.py
"""Arranque del microservicio dedicacion-api.

1. Crea la BBDD PostgreSQL si no existe (credenciales admin).
2. Pone al día el esquema (idempotente), derivándolo del ORM.
3. Arranca uvicorn con la app FastAPI.

El paso 2 vive AQUÍ y solo aquí: construir la app (`build_app`) no toca la
base de datos. Arrancar el servicio apuntando `uvicorn` directamente a la app,
en vez de por `python main.py`, se salta la puesta al día del esquema.
"""
from __future__ import annotations

import logging

import uvicorn

from config.settings import get_settings
from infrastructure.db.database import asegurar_base_datos, crear_engine
from infrastructure.db.esquema import sincronizar_esquema
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
    aplicadas = sincronizar_esquema(engine)
    logger.info(
        "Esquema verificado en BBDD '%s': %s sentencias DDL aplicadas",
        settings.pg_db,
        len(aplicadas),
    )

    app = build_app(settings)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level="info")


if __name__ == "__main__":
    main()
