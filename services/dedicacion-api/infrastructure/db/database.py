# infrastructure/db/database.py
"""Motor SQLAlchemy + bootstrap de la BBDD.

Patrón idéntico al de partes-sv3: en el arranque, con las credenciales
de administración, se crea la base de datos si no existe; después se
abre el engine de aplicación y se ejecuta create_all (idempotente).
"""
from __future__ import annotations

import logging
from urllib.parse import quote_plus

import psycopg
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import Settings

logger = logging.getLogger(__name__)


def asegurar_base_datos(settings: Settings) -> None:
    """Bootstrap idempotente con credenciales de administración.

    1. Crea el rol de aplicación `PG_USER` (LOGIN) si no existe.
    2. Crea la BBDD `PG_DB` con ese rol como OWNER si no existe
       (necesario para que create_all tenga permisos sobre el esquema
       public en PostgreSQL 15+).
    """
    dsn = (
        f"host={settings.pg_host} port={settings.pg_port} "
        f"dbname={settings.pg_admin_db} user={settings.pg_admin_user} "
        f"password={settings.pg_admin_password} sslmode={settings.pg_sslmode}"
    )
    with psycopg.connect(dsn, autocommit=True) as conn:
        _asegurar_rol(conn, settings)
        existe = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (settings.pg_db,)
        ).fetchone()
        if existe:
            logger.info("BBDD '%s' ya existe", settings.pg_db)
            return
        # CREATE DATABASE no admite parámetros: composición segura con sql.*
        conn.execute(
            sql.SQL("CREATE DATABASE {db} OWNER {owner}").format(
                db=sql.Identifier(settings.pg_db),
                owner=sql.Identifier(settings.pg_user),
            )
        )
        logger.info(
            "BBDD '%s' creada (owner %s)", settings.pg_db, settings.pg_user
        )


def _asegurar_rol(conn: psycopg.Connection, settings: Settings) -> None:
    """Crea el rol de aplicación si no existe (no toca roles existentes)."""
    if settings.pg_user == settings.pg_admin_user:
        return
    existe = conn.execute(
        "SELECT 1 FROM pg_roles WHERE rolname = %s", (settings.pg_user,)
    ).fetchone()
    if existe:
        return
    conn.execute(
        sql.SQL("CREATE ROLE {rol} LOGIN PASSWORD {pwd}").format(
            rol=sql.Identifier(settings.pg_user),
            pwd=sql.Literal(settings.pg_password),
        )
    )
    logger.info("Rol de aplicación '%s' creado", settings.pg_user)


def crear_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        future=True,
    )


def crear_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def _url_admin(settings: Settings) -> str:
    return (
        f"postgresql+psycopg://{quote_plus(settings.pg_admin_user)}:"
        f"{quote_plus(settings.pg_admin_password)}@{settings.pg_host}:"
        f"{settings.pg_port}/{settings.pg_db}?sslmode={settings.pg_sslmode}"
    )