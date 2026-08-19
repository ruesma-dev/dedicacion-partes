# infrastructure/db/esquema.py
"""Puesta al día del esquema de PostgreSQL DERIVADA del ORM.

`Base.metadata.create_all()` crea las tablas que faltan, pero **nunca modifica
una tabla que ya existe**: añadir una columna al ORM no tiene ningún efecto
sobre una base ya creada. Este módulo cubre ese hueco generando el DDL
complementario a partir de los propios metadatos del ORM, para que
`orm_models.py` siga siendo la única verdad del esquema y no haga falta
mantener en paralelo una lista de `ALTER TABLE` escrita a mano.

**Esto no es un motor de migraciones y no pretende serlo.** Solo sabe AÑADIR
columnas que faltan. No cambia tipos, no renombra, no borra columnas
sobrantes y no toca restricciones ni índices de tablas que ya existen. Una
columna con el mismo nombre y otro tipo pasa desapercibida a propósito: el
sistema no podría corregirla sin una migración de verdad. El primer cambio de
esquema que no sea «añadir una columna nulable», o el día que haya más de un
entorno con la base, es cuando entra una herramienta de migración (Alembic) y
este módulo se retira; el criterio está escrito en
`specs/F-003-orm-columnas-sigrid/design.md` §6.

Las funciones de decisión (`ddl_add_column`, `alters_faltantes`) son PURAS:
reciben el estado de la base como dato y no abren ninguna conexión, que es lo
que permite comprobarlas sin PostgreSQL.
"""
from __future__ import annotations

import logging
from collections.abc import Mapping

from sqlalchemy import Column, MetaData, Table, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateColumn

from infrastructure.db.orm_models import Base

logger = logging.getLogger(__name__)

#: Dialecto con el que se compila el DDL. Es el del motor real, así que el
#: texto emitido es el que PostgreSQL va a recibir.
_DIALECTO = postgresql.dialect()


class EsquemaNoDerivable(RuntimeError):
    """Falta una columna que no puede añadirse sin decidir un valor.

    Le pasa a una columna `NOT NULL` sin `server_default`: sobre una tabla con
    filas, el `ADD COLUMN` fallaría, y rellenarla exige una decisión humana.
    """


def ddl_add_column(tabla: Table, columna: Column) -> str:
    """Sentencia `ADD COLUMN IF NOT EXISTS` para UNA columna del ORM.

    El texto del tipo se obtiene COMPILANDO la columna con el dialecto de
    PostgreSQL (`sigrid_estado VARCHAR(16)`), no escribiéndolo a mano: de ahí
    que el ORM sea la única fuente. Función pura: no toca la BBDD.
    """
    definicion = CreateColumn(columna).compile(dialect=_DIALECTO).string
    return f"ALTER TABLE {tabla.name} ADD COLUMN IF NOT EXISTS {definicion}"


def alters_faltantes(
    metadata: MetaData, existentes: Mapping[str, set[str]]
) -> list[str]:
    """DDL complementario para poner al día las tablas que YA existen.

    `existentes` es la radiografía de la base: `{tabla: {columnas que tiene}}`.
    Entra como dato, no se consulta aquí, para que la decisión sea comprobable
    sin PostgreSQL. Reglas:

      - tabla ausente de `existentes`: se ignora, la crea `create_all`;
      - columna ya presente: nada;
      - columna ausente, nulable o con `server_default`: un `ADD COLUMN`;
      - columna ausente, `NOT NULL` y sin `server_default`: `EsquemaNoDerivable`.

    El orden es el de declaración en el ORM, para que la salida sea
    determinista y se pueda comparar como lista.
    """
    sentencias: list[str] = []
    for tabla in metadata.tables.values():
        columnas_en_bbdd = existentes.get(tabla.name)
        if columnas_en_bbdd is None:
            continue
        for columna in tabla.columns:
            if columna.name in columnas_en_bbdd:
                continue
            if not columna.nullable and columna.server_default is None:
                raise EsquemaNoDerivable(
                    f"a la tabla '{tabla.name}' le falta la columna "
                    f"'{columna.name}', declarada NOT NULL y sin valor por "
                    "defecto: añadirla sobre una tabla con filas exige una "
                    "migración escrita por una persona"
                )
            sentencias.append(ddl_add_column(tabla, columna))
    return sentencias


def columnas_existentes(engine: Engine) -> dict[str, set[str]]:
    """Radiografía de la base: qué columnas tiene hoy cada tabla.

    Único punto que consulta el estado real. Sin lógica: lo que se decide con
    esto vive en `alters_faltantes`.
    """
    inspector = inspect(engine)
    return {
        nombre: {columna["name"] for columna in inspector.get_columns(nombre)}
        for nombre in inspector.get_table_names()
    }


def sincronizar_esquema(engine: Engine) -> list[str]:
    """Deja el esquema al día y devuelve las sentencias DDL aplicadas.

    Crea las tablas que faltan y, sobre las que ya existían, añade las
    columnas que el ORM declara y la base no tiene. Es idempotente: contra una
    base ya al día devuelve la lista vacía y no emite nada. La lista se
    devuelve para que el arranque la registre en el log.
    """
    Base.metadata.create_all(engine)
    sentencias = alters_faltantes(Base.metadata, columnas_existentes(engine))
    with engine.begin() as conexion:
        for sentencia in sentencias:
            logger.info("DDL complementario: %s", sentencia)
            conexion.execute(text(sentencia))
    return sentencias
