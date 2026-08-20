# infrastructure/db/database.py
"""Motor SQLAlchemy + bootstrap de la BBDD.

En LOCAL, con `AUTO_CREATE_DATABASE=true`, el arranque crea el rol y la base
si no existen: es la comodidad de trabajar en el portátil.

En AZURE ese bootstrap está APAGADO y no es negociable (F-008, R13-R15). La
base `dedicacion` vive en `psql-albaranes-rs9k2`, un servidor **compartido**
con albaranes, partes, datamart y postventa; la crean una persona y una sola
vez con `infra/crear_base_dedicacion.ps1`. Con el conmutador apagado ni
siquiera se abre la conexión de administración: así el servicio desplegado no
necesita —ni puede filtrar— la contraseña del administrador del servidor.
Lo que no se guarda, no se filtra.

Después se abre el engine de aplicación, se comprueba que la base existe
(traduciendo el error crudo del driver a algo accionable) y se pone al día el
esquema, de forma idempotente, con `esquema.sincronizar_esquema` (que es
quien conoce las tablas: aquí solo se crean el rol y la base).
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

#: Script que crea la base y el rol de aplicación. Lo ejecuta una persona, una
#: sola vez. Su nombre viaja dentro del error de arranque porque es la única
#: pista útil para quien se encuentra el servicio caído en Azure.
SCRIPT_DE_ALTA = "infra/crear_base_dedicacion.ps1"


class BaseDatosNoExiste(RuntimeError):
    """La base de aplicación no existe y el bootstrap está desactivado.

    Se lanza en lugar del error crudo del driver (`InvalidCatalogName`, o el
    `OperationalError` que lo envuelve), que no dice qué hacer a continuación.
    """

    def __init__(self, base: str, host: str) -> None:
        super().__init__(
            f"La base de datos '{base}' no existe en el servidor '{host}'. "
            f"Este servicio NO crea bases ni roles (AUTO_CREATE_DATABASE está "
            f"desactivado, y en un servidor compartido debe seguir así): "
            f"créala una sola vez ejecutando {SCRIPT_DE_ALTA}."
        )
        self.base = base
        self.host = host


def es_base_inexistente(exc: BaseException, base: str) -> bool:
    """¿Este fallo de conexión dice que falta la base `base`?

    Se recorre la cadena de causas porque SQLAlchemy envuelve el error del
    driver. Se exige que el mensaje nombre NUESTRA base: el servidor es
    compartido y que falte la de otro proyecto no se traduce a «crea la tuya»,
    que mandaría a quien diagnostica en la dirección contraria.
    """
    esperado = f'database "{base}" does not exist'
    actual: BaseException | None = exc
    while actual is not None:
        if isinstance(actual, psycopg.errors.InvalidCatalogName):
            return True
        if esperado in str(actual):
            return True
        actual = actual.__cause__
    return False


def comprobar_base_datos(engine: Engine, settings: Settings) -> None:
    """Abre la primera conexión y traduce el fallo por base inexistente.

    Lo que no se entiende se deja subir tal cual: un servidor caído, una
    contraseña mala o un TLS rechazado no se disfrazan de base que falta.
    """
    try:
        with engine.connect():
            pass
    except Exception as exc:
        if es_base_inexistente(exc, settings.pg_db):
            raise BaseDatosNoExiste(settings.pg_db, settings.pg_host) from exc
        raise


def asegurar_base_datos(settings: Settings) -> None:
    """Bootstrap idempotente con credenciales de administración.

    Con `AUTO_CREATE_DATABASE` apagado (el defecto) retorna SIN abrir la
    conexión de administración. Con el conmutador encendido:

    1. Crea el rol de aplicación `PG_USER` (LOGIN) si no existe.
    2. Crea la BBDD `PG_DB` con ese rol como OWNER si no existe
       (necesario para que create_all tenga permisos sobre el esquema
       public en PostgreSQL 15+).
    """
    if not settings.auto_create_database:
        logger.info(
            "AUTO_CREATE_DATABASE desactivado: no se abre la conexión de "
            "administración ni se crean rol ni base. La base '%s' la crea una "
            "persona, una sola vez, con %s",
            settings.pg_db,
            SCRIPT_DE_ALTA,
        )
        return

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