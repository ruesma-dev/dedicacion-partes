# main.py
"""Arranque del microservicio dedicacion-api.

1. Crea la BBDD PostgreSQL si no existe, SOLO con `AUTO_CREATE_DATABASE=true`
   (en local). Desplegado va apagado: la base vive en un servidor compartido
   y la crea una persona (F-008, R13-R15).
2. Comprueba que la base existe, traduciendo el error crudo del driver a uno
   que dice qué base falta y qué script la crea (R16).
3. Pone al día el esquema (idempotente), derivándolo del ORM.
4. Arranca uvicorn con la app FastAPI.

El paso 3 vive AQUÍ y solo aquí: construir la app (`build_app`) no toca la
base de datos. Arrancar el servicio apuntando `uvicorn` directamente a la app,
en vez de por `python main.py`, se salta la puesta al día del esquema.
"""
from __future__ import annotations

import logging

import uvicorn

from config.settings import get_settings
from infrastructure.db.database import (
    asegurar_base_datos,
    comprobar_base_datos,
    crear_engine,
)
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
    comprobar_base_datos(engine, settings)
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
