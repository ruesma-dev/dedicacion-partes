<!-- specs/F-003-orm-columnas-sigrid/design.md -->
# F-003 · Diseño técnico

## 0. Cómo se crea hoy el esquema (lo que decide el diseño entero)

Leído en el código, no supuesto:

1. `services/dedicacion-api/main.py` (única vía de arranque: el `README` dice
   `python main.py` y el `Dockerfile` termina en `CMD ["python", "main.py"]`)
   hace tres cosas en orden:
   `asegurar_base_datos(settings)` → `crear_engine(settings)` →
   **`Base.metadata.create_all(engine)`** → `build_app(settings)` → `uvicorn`.
2. `infrastructure/db/database.py::asegurar_base_datos` crea, con credenciales
   de administración y de forma idempotente, el **rol** de aplicación y la
   **base de datos** `PG_DB` si no existen. No crea ni toca tablas.
3. `Base.metadata.create_all(engine)` crea **las tablas que faltan**. Es la
   pieza clave: `create_all` **nunca modifica una tabla que ya existe**. Si
   `asignacion` está creada, añadir una columna al ORM no tiene ningún efecto
   sobre esa base. De ahí que `_ALTERS` exista.
4. **No hay Alembic, ni carpeta de migraciones, ni ficheros `.sql`
   versionados** en todo el servicio (`requirements.txt` no incluye ninguna
   herramienta de migración; no existe `alembic.ini` ni `migrations/`). El
   único DDL fuera del ORM son las seis sentencias de
   `application/registro_sigrid.py::_ALTERS`, ejecutadas en el **constructor**
   de `RegistroSigrid`, que `interface_adapters/api/deps.py::construir_
   contenedor` instancia dentro de `build_app`. Es decir: hoy el DDL
   complementario se dispara al **construir la app**, no al arrancar, y
   cualquier test que importase y construyese la app abriría una conexión a
   PostgreSQL para ejecutar DDL.

Conclusión de diseño: hace falta **conservar** un paso de DDL complementario
(sin él, una base ya existente nunca recibiría las columnas), pero ese paso
debe (a) derivarse del ORM, (b) vivir en `infrastructure/db/`, y (c)
ejecutarse en `main.py`, junto a `create_all` y no dentro de la aplicación.

## 1. Ficheros a crear

### `services/dedicacion-api/infrastructure/db/esquema.py`

Capa: **infrastructure** (adaptador de persistencia; es DDL). Sin
dependencias nuevas: `sqlalchemy` ya está en `requirements.txt`.

```python
# infrastructure/db/esquema.py

class EsquemaNoDerivable(RuntimeError):
    """Falta una columna que no puede añadirse sin decidir un valor."""


def ddl_add_column(tabla: Table, columna: Column) -> str:
    """Sentencia ADD COLUMN IF NOT EXISTS para UNA columna del ORM.

    Compila el tipo con el dialecto PostgreSQL. Función PURA: no toca BBDD.
    """


def alters_faltantes(
    metadata: MetaData, existentes: Mapping[str, set[str]]
) -> list[str]:
    """DDL complementario para poner al día tablas que YA existen.

    `existentes` = {nombre_tabla: {columnas que la BBDD tiene}}. Función
    PURA: recibe el estado de la base como dato, no lo consulta.
    Reglas:
      - tabla ausente de `existentes` -> se ignora (la crea create_all);
      - columna presente -> nada;
      - columna ausente y nulable o con server_default -> un ADD COLUMN;
      - columna ausente, NOT NULL y sin server_default -> EsquemaNoDerivable.
    Orden estable: el de declaración en el ORM.
    """


def columnas_existentes(engine: Engine) -> dict[str, set[str]]:
    """Radiografía de la base con `sqlalchemy.inspect`. Impura, sin lógica."""


def sincronizar_esquema(engine: Engine) -> list[str]:
    """create_all + los ALTER derivados. Devuelve lo ejecutado (para log)."""
```

`sincronizar_esquema` es la única función impura con lógica de orquestación:
llama a `Base.metadata.create_all(engine)`, luego a `columnas_existentes`,
luego a `alters_faltantes`, ejecuta las sentencias en una transacción y
devuelve la lista para que `main.py` la registre en el log. Toda la decisión
—qué se emite y con qué texto— vive en las dos funciones puras, que son las
que se testean sin BBDD.

Detalle de implementación relevante: el texto del tipo se obtiene compilando
la columna, no escribiéndolo a mano —
`CreateColumn(columna).compile(dialect=postgresql.dialect()).string` produce
`sigrid_estado VARCHAR(16)`—, que es literalmente lo que exige R3.

### `services/dedicacion-api/tests/test_f003_esquema.py`

Suite offline (ver §5). Reutiliza `tests/conftest.py`, que ya inserta la raíz
del servicio en `sys.path`; no se añaden fixtures de BBDD ni de red.

## 2. Ficheros a modificar

### `services/dedicacion-api/infrastructure/db/orm_models.py`

- Añadir `String` a la lista de imports de `sqlalchemy`.
- Añadir a `AsignacionORM`, después de `actualizado_por` y antes de
  `__table_args__`, las seis columnas de la tabla de R5, bajo un comentario
  que diga qué son: traza del registro en Sigrid, escrita por
  `application/registro_sigrid.py`.
- **No** se toca ninguna otra clase ni ninguna restricción existente.

Nota sobre `String(N)` frente a `Text`: el resto del ORM usa `Text` para las
cadenas, pero aquí se usa `String(N)` **a propósito**, porque es lo que la
base local ya tiene por obra de `_ALTERS`. Declarar `Text` haría que una base
limpia y la base actual tuvieran tipos distintos para la misma columna: la
divergencia que la feature elimina, reintroducida por la puerta de atrás. La
coherencia estilística con el resto del ORM es un precio menor que pagar por
eso, y queda anotada como D2 de `requirements.md`.

### `services/dedicacion-api/application/registro_sigrid.py`

- **Eliminar** la constante `_ALTERS` entera y el bucle que la ejecuta en
  `__init__`. El constructor se queda en asignar `self._sf` y
  `self._transfer`: wiring puro, sin efectos.
- **Eliminar** el import de `text` de `sqlalchemy` (deja de usarse).
- Reescribir `_trazar` con `sqlalchemy.update(AsignacionORM)` y `.values(...)`
  en lugar de las tres cadenas SQL. Con el ORM como fuente, un nombre de
  columna mal escrito deja de ser un error en tiempo de ejecución contra la
  base y pasa a ser un `AttributeError` inmediato. Equivalencias:
  - `escritas` → `update(AsignacionORM).where(AsignacionORM.id == rid)
    .values(sigrid_estado="registrado", sigrid_parte_cod=..., 
    sigrid_hmores_ide=..., sigrid_motivo=None,
    sigrid_registrado_at_utc=ahora, sigrid_registrado_by=usuario_trunc)`.
  - `ya_registradas` → `.where(AsignacionORM.id == rid,
    AsignacionORM.sigrid_estado.is_distinct_from("registrado"))
    .values(sigrid_estado="registrado")` (`is_distinct_from` es el
    equivalente exacto de `IS DISTINCT FROM` en SQLAlchemy 2.0).
  - `omitidas` → `.values(sigrid_estado="omitido",
    sigrid_motivo=(motivo or "")[:300])`.
- Truncar el usuario a 64 (`(usuario or "")[:64]`) una sola vez al principio
  de `_trazar`, junto al `datetime.now(timezone.utc)` (R7).
- El resto del fichero —`_payloads`, `preflight`, `ejecutar`, la división
  entre 100 del porcentaje— **no se toca**. En particular, la escala del
  porcentaje sobre 1 se queda exactamente como está.

### `services/dedicacion-api/main.py`

- Sustituir `Base.metadata.create_all(engine)` por
  `aplicadas = sincronizar_esquema(engine)` y registrar en el log cuántas
  sentencias se aplicaron (0 en el caso normal). Cambia el import de
  `Base` por el de `sincronizar_esquema`.

### `docs/CONVENTIONS.md`

La sección «SQL» cita hoy `_ALTERS` como el contraejemplo vigente («que hoy es
justo lo contrario y está en el backlog»). Al desaparecer `_ALTERS`, esa frase
queda mintiendo. Se reescribe para que apunte al mecanismo bueno:
`infrastructure/db/esquema.py`.

## 3. Ficheros que NO se tocan

Los colindantes que tientan y quedan fuera:

- `infrastructure/db/repositories.py` — no necesita cambios: `reemplazar()`
  construye `AsignacionORM(...)` con kwargs explícitos y las seis columnas son
  nulables (R16), y `_a_linea` mapea campo a campo, sin `SELECT *`. Se
  comprobó por búsqueda que en todo el servicio no hay ningún `SELECT *` ni
  ningún `insert()`/`.values()` construido a mano sobre `asignacion`: el único
  SQL crudo del servicio son los tres `UPDATE` de `_trazar` y los `_ALTERS`,
  y ambos desaparecen en esta feature.
- `infrastructure/db/database.py` — el bootstrap de rol y base de datos sigue
  igual; esta feature actúa **después**, sobre tablas.
- `interface_adapters/api/{routes,schemas,deps,app}.py` — la traza no se
  expone (R15). `deps.py` sigue instanciando `RegistroSigrid` igual; lo único
  que cambia es que esa instanciación ya no ejecuta DDL.
- `domain/` — el dominio no conoce el esquema físico.
- `services/dedicacion-front/`, `services/dedicacion-transfer/` — ni se
  enteran. Ningún contrato HTTP cambia.
- `harness/features.json`, `progress/current.md` — los lleva el líder.

## 4. SQL

No hay ficheros `.sql` en este proyecto y esta feature **no introduce
ninguno**: la convención `NN_nombre.sql` de `specs/SPECS.md` no aplica aquí.
Todo el SQL de esquema es DDL generado por SQLAlchemy a partir de
`orm_models.py`.

Objeto afectado: la tabla **`asignacion`** de la BBDD PostgreSQL `dedicacion`,
seis columnas nuevas para el ORM (ya presentes en la base local). No se toca
`trabajador`, `obra`, `periodo` ni `evento`. **Contra Sigrid no se ejecuta
absolutamente nada**: esta feature no abre ni una lectura.

### Comportamiento por estado de la base

| Estado de partida | `create_all` | DDL derivado | Efecto sobre los datos |
|---|---|---|---|
| Base limpia (sin `asignacion`) | crea la tabla con las 16 columnas | 0 sentencias | ninguno |
| Base local de hoy (tabla + las 6 columnas creadas por `_ALTERS`) | no toca nada | 0 sentencias | **ninguno**: el arranque no emite DDL |
| Base con la tabla pero sin las 6 columnas | no toca nada | 6 `ADD COLUMN IF NOT EXISTS` | ninguno: columnas nulables sin default, PostgreSQL no reescribe la tabla |
| Base con una columna del mismo nombre y **otro tipo** | no toca nada | 0 sentencias (la ve presente) | **límite conocido**, ver §6 |

La segunda fila es la importante y es la que se verifica a mano (T8): el
entorno actual del humano tiene las columnas y ya tiene datos, así que el
resultado correcto de esta feature en su máquina es que **no pase nada**.

## 5. Estrategia de tests

Todo en `services/dedicacion-api/tests/test_f003_esquema.py`, offline, con
nombres trazables `test_f003_rN_*`. Tres piezas:

1. **El ORM declara lo que debe** (R1, R5, R6). Parametrizado por columna:
   existe en `AsignacionORM.__table__.columns`, `nullable is True`, y el tipo
   compilado con `postgresql.dialect()` es la cadena exacta esperada
   (`VARCHAR(16)`, `VARCHAR(24)`, `INTEGER`, `VARCHAR(300)`,
   `TIMESTAMP WITH TIME ZONE`, `VARCHAR(64)`).

2. **El DDL derivado contra lo que el código espera** (R17, la pieza central).
   Un `COLUMNAS_TRAZA` de referencia en el test enumera los seis nombres; el
   test afirma que el conjunto de columnas `sigrid_*` de `AsignacionORM`
   **es igual** a ese conjunto (ni una de más, ni una de menos), y que
   `alters_faltantes` sobre una base simulada sin ellas devuelve exactamente
   seis sentencias cuyo texto completo se compara **carácter a carácter** con
   el esperado. Comparar cadenas exactas (no `in`) es lo que hace que la
   campaña de mutación no deje supervivientes en la construcción del DDL.

3. **El mecanismo** (R8-R13, R2, R4): tabla ausente → sin ALTER; todas las
   columnas presentes → lista vacía (idempotencia, R11); columna `NOT NULL`
   sin `server_default` ausente → `EsquemaNoDerivable` con el nombre de tabla
   y columna en el mensaje (R12); `alters_faltantes` no emite `DROP`, ni
   `ALTER COLUMN`, ni `ADD CONSTRAINT` (R13); el fuente de
   `application/registro_sigrid.py` no contiene `ALTER TABLE` ni `_ALTERS`
   (R2, guardia anti-regresión de la avería F-010); construir
   `RegistroSigrid` con una `session_factory` de mentira **no ejecuta ninguna
   sentencia** (R4).

4. **La traza** (R7, R14): un doble de sesión captura las sentencias que
   `_trazar` ejecuta y el test las compila con el dialecto PostgreSQL para
   comprobar qué columnas fija cada rama, que el motivo se trunca a 300, que
   el usuario se trunca a 64 y que `sigrid_registrado_at_utc` recibe un
   `datetime` con `tzinfo` UTC (R6).

Nada de esto necesita PostgreSQL: SQLAlchemy compila DDL y DML contra un
dialecto sin conexión. Lo que sí la necesita —que una base real acepte el
arranque dos veces— es la verificación **MANUAL (humano)** T8 de `tasks.md`.

## 6. Riesgos y decisiones

- **Alternativa descartada: Alembic (o cualquier herramienta de migración).**
  Añadiría una dependencia, un directorio `migrations/`, un `alembic.ini` y la
  disciplina de generar y revisar una revisión por cambio, para un servicio
  que hoy tiene **una sola base, en local, con un único desfase conocido y
  ningún despliegue**. Es sobreingeniería hoy. El criterio objetivo por el que
  dejaría de serlo, escrito para no tener que volver a discutirlo: **el primer
  cambio de esquema que no sea "añadir una columna nulable"** —cambiar un
  tipo, renombrar, borrar, o mover datos existentes— o **el día que haya más
  de un entorno con la base** (el despliegue sobre `psql-albaranes-rs9k2` u
  otro servidor). En ese momento entra Alembic y `esquema.py` se retira. Hasta
  entonces, `esquema.py` cubre lo único que hace falta y lo cubre derivándolo
  del ORM.
- **Riesgo: `create_all` da falsa sensación de migración.** Ya es el estado
  actual; esta feature lo reduce (el desfase por columna se cierra
  automáticamente) pero no lo elimina (R13). El límite queda escrito en el
  docstring de `esquema.py` para que el siguiente que lo lea no crea que
  tiene un motor de migraciones.
- **Riesgo: una columna del mismo nombre con otro tipo pasa desapercibida.**
  `alters_faltantes` compara **nombres**, no tipos. Comparar tipos exigiría
  traducir los tipos reflejados de PostgreSQL a los de SQLAlchemy —una fuente
  de falsos positivos conocida (`VARCHAR` vs `TEXT`, `TIMESTAMPTZ` vs
  `TIMESTAMP WITH TIME ZONE`)— y, sobre todo, el sistema no podría **corregir**
  lo que detectase sin una migración. Se declara como límite (R13) y no se
  implementa a medias.
- **Riesgo: alguien arranca con `uvicorn` apuntando a `build_app` en vez de
  `python main.py`.** Hoy el DDL se ejecutaba dentro de `build_app`, así que
  esa ruta quedaba cubierta por accidente; tras esta feature, no. Es
  deliberado: `main.py` es la única vía de arranque documentada (`README`) y
  la del `Dockerfile`, y un `build_app` sin efectos sobre la BBDD es lo que
  permite importar la app en tests. Queda escrito en el `README` del servicio
  como parte de T6.
- **Riesgo: el orden de las sentencias.** `alters_faltantes` respeta el orden
  de declaración del ORM para que la salida sea determinista y el test pueda
  compararla como lista. Un `set` haría el test dependiente del hash.
- **Límite de microservicio.** Todo lo que toca esta feature pertenece a
  `dedicacion-api`: es su base de datos, su ORM y su arranque. No hay
  responsabilidad que pertenezca a otro servicio ni nada que extraer.
  `dedicacion-transfer` tiene su propio problema de esquema (escribe en
  SQL Server, no en PostgreSQL) y no comparte nada con esto. `esquema.py`
  **no** es lógica que deba copiarse al transfer ni al front: ninguno de los
  dos tiene base de datos propia.
