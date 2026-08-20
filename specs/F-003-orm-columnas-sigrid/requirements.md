<!-- specs/F-003-orm-columnas-sigrid/requirements.md -->
# F-003 · Requisitos — Las columnas `sigrid_*` van al ORM

> **Rigor `critico`.** Se toca la definición del esquema de la BBDD
> `dedicacion`, sobre una base que **hoy ya existe y tiene datos** en local.
> Un error aquí no rompe un test: rompe el arranque del servicio o, peor,
> deja dos verdades del esquema convivendo sin que nada falle.

## Contexto

`services/dedicacion-api/application/registro_sigrid.py` mantiene, en la capa
`application`, una lista `_ALTERS` de seis sentencias `ALTER TABLE asignacion
ADD COLUMN IF NOT EXISTS ...` escritas a mano, que se ejecutan **en el
constructor** de `RegistroSigrid` (es decir, cada vez que `build_app()` monta
el contenedor de dependencias). Esas seis columnas —`sigrid_estado`,
`sigrid_parte_cod`, `sigrid_hmores_ide`, `sigrid_motivo`,
`sigrid_registrado_at_utc`, `sigrid_registrado_by`— **no están declaradas** en
`infrastructure/db/orm_models.py`.

Hay por tanto dos definiciones del esquema de `asignacion`: la del ORM (que
`main.py` aplica con `Base.metadata.create_all`) y la de `_ALTERS`. Nada
garantiza que coincidan y nada avisa cuando divergen, porque
`create_all` **no modifica tablas que ya existen**: solo crea las que faltan.
Es la avería que en el proyecto `partes` costó la corrección entera F-010.

Los tres consumidores actuales de esas columnas son los tres `UPDATE` en SQL
crudo de `RegistroSigrid._trazar`. Ningún endpoint, ningún esquema Pydantic y
ningún repositorio las lee (comprobado por búsqueda en todo el servicio): la
traza es hoy **solo de escritura**.

Servicio afectado: **`dedicacion-api`**, y solo él. Esta feature no habla con
Sigrid, no toca `dedicacion-transfer` ni `dedicacion-front`, y no cambia
ningún contrato HTTP.

---

## 1. Requisitos EARS

### 1.1. Una sola fuente de verdad del esquema

- **R1.** El sistema debe declarar las seis columnas `sigrid_estado`,
  `sigrid_parte_cod`, `sigrid_hmores_ide`, `sigrid_motivo`,
  `sigrid_registrado_at_utc` y `sigrid_registrado_by` como atributos de
  `AsignacionORM` en `infrastructure/db/orm_models.py`, con los tipos y la
  nulabilidad de la tabla del §1.2.

- **R2.** El sistema **no debe** contener ninguna sentencia DDL escrita a mano
  sobre la tabla `asignacion` fuera de `orm_models.py`. En particular,
  `application/registro_sigrid.py` no debe contener la cadena `ALTER TABLE`
  ni ninguna lista equivalente a `_ALTERS`.

- **R3.** El sistema debe derivar el DDL complementario (el que pone al día
  una tabla que ya existe) **de los metadatos del ORM**, y no de una lista
  paralela de nombres o de tipos escrita por una persona.

- **R4.** El sistema debe ejecutar ese DDL complementario **en el arranque**
  (`main.py`), no dentro de un constructor de la capa `application`.
  MIENTRAS se construye la aplicación FastAPI (`build_app`), el sistema no
  debe emitir ninguna sentencia DDL ni abrir ninguna conexión para hacerlo.

### 1.2. Tipos y nulabilidad exactos

- **R5.** El sistema debe declarar las seis columnas exactamente así:

  | Columna | Declaración ORM | Tipo PostgreSQL emitido | Nulable |
  |---|---|---|---|
  | `sigrid_estado` | `Mapped[str \| None] = mapped_column(String(16))` | `VARCHAR(16)` | sí |
  | `sigrid_parte_cod` | `Mapped[str \| None] = mapped_column(String(24))` | `VARCHAR(24)` | sí |
  | `sigrid_hmores_ide` | `Mapped[int \| None] = mapped_column(Integer)` | `INTEGER` | sí |
  | `sigrid_motivo` | `Mapped[str \| None] = mapped_column(String(300))` | `VARCHAR(300)` | sí |
  | `sigrid_registrado_at_utc` | `Mapped[datetime \| None] = mapped_column(DateTime(timezone=True))` | `TIMESTAMP WITH TIME ZONE` | sí |
  | `sigrid_registrado_by` | `Mapped[str \| None] = mapped_column(String(64))` | `VARCHAR(64)` | sí |

  Ninguna de las seis lleva `nullable=False`, ni `default`, ni
  `server_default`: una asignación recién creada no está registrada en Sigrid,
  y la ausencia de valor es el estado inicial legítimo.

- **R6.** El sistema debe escribir en `sigrid_registrado_at_utc` un
  `datetime` **consciente de zona horaria** en UTC
  (`datetime.now(timezone.utc)`, como hoy). La columna es
  `TIMESTAMP WITH TIME ZONE`: PostgreSQL normaliza a UTC y devuelve un
  `datetime` con `tzinfo`. Queda prohibido escribir ahí un `datetime` naíf.

- **R7.** SI el usuario que registra excede los 64 caracteres que admite
  `sigrid_registrado_by`, ENTONCES el sistema debe truncarlo a 64 antes de
  escribirlo, igual que ya hace con el motivo a 300, en lugar de dejar que
  PostgreSQL aborte la transacción de traza con un error de longitud.

### 1.3. Bases existentes y bases limpias

- **R8.** CUANDO el servicio arranca contra una base **limpia** (la tabla
  `asignacion` no existe), el sistema debe crearla con las dieciséis columnas
  —las diez actuales más las seis `sigrid_*`— sin emitir ningún `ALTER TABLE`.

- **R9.** CUANDO el servicio arranca contra una base **que ya tiene** la tabla
  `asignacion` con las seis columnas (el caso del entorno local de hoy), el
  sistema no debe emitir ninguna sentencia DDL sobre ella.

- **R10.** CUANDO el servicio arranca contra una base que ya tiene la tabla
  `asignacion` pero le faltan `N` de las columnas declaradas en el ORM, el
  sistema debe emitir exactamente `N` sentencias
  `ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS <columna> <tipo>`, una por
  columna faltante, con el tipo compilado a partir del ORM.

- **R11.** El sistema debe ser idempotente en el arranque: arrancar dos veces
  seguidas contra la misma base no debe fallar, ni duplicar columnas, ni
  alterar los datos existentes.

- **R12.** SI a una tabla existente le falta una columna declarada en el ORM
  como `NOT NULL` y **sin** `server_default`, ENTONCES el sistema debe abortar
  el arranque con un error explícito que nombre la tabla y la columna, en
  lugar de emitir un `ADD COLUMN ... NOT NULL` que fallaría sobre una tabla
  con filas o, peor, adivinar un valor de relleno. Ese caso exige una
  migración escrita por una persona.

- **R13.** El sistema debe limitar el DDL derivado a **añadir columnas que
  faltan**. No debe cambiar tipos, no debe borrar columnas sobrantes y no debe
  crear ni modificar restricciones sobre tablas que ya existen. Lo que quede
  fuera de ese límite debe estar escrito como límite conocido en `design.md`,
  no resuelto a medias.

### 1.4. Compatibilidad hacia atrás

- **R14.** El sistema debe seguir escribiendo la traza con la misma semántica
  que hoy: para cada entrada de `escritas`, `sigrid_estado='registrado'` con
  `sigrid_parte_cod`, `sigrid_hmores_ide`, `sigrid_registrado_at_utc`,
  `sigrid_registrado_by` y `sigrid_motivo` a `NULL`; para cada `registro_id`
  de `ya_registradas`, solo `sigrid_estado='registrado'` y solo si aún no lo
  era (`IS DISTINCT FROM`); para cada entrada de `omitidas`,
  `sigrid_estado='omitido'` y el motivo truncado a 300.

- **R15.** El sistema debe mantener sin cambios la respuesta de todos los
  endpoints: ni `interface_adapters/api/schemas.py` ni el mapeo
  `_a_linea` de `infrastructure/db/repositories.py` exponen las columnas
  nuevas, y esta feature no las expone.

- **R16.** El sistema debe seguir insertando asignaciones con
  `AsignacionORM(...)` sin pasar las seis columnas nuevas
  (`repositories.PgAsignacionRepository.reemplazar`), lo que exige que las
  seis sean nulables (R5). Ningún `SELECT *` ni `insert()` construido a mano
  sobre `asignacion` debe quedar en el servicio.

### 1.5. Verificación

- **R17.** El sistema debe traer un test que compare **el DDL derivado del
  ORM** con el conjunto de columnas `sigrid_*` que el código de traza espera,
  y que falle si alguien añade una columna a un lado y no al otro.

- **R18.** Los tests de esta feature deben ejecutarse **sin red y sin
  PostgreSQL**: el DDL se compila con el dialecto `postgresql` de SQLAlchemy
  sin conexión, y el estado de la base se pasa como dato de entrada. Lo que
  exija una base real queda como verificación `MANUAL (humano)`.

---

## 2. Decisiones abiertas para el humano

- **D1. `sigrid_hmores_ide` es `INTEGER` y el resto de `ide` del ORM son
  `BigInteger`.** Se mantiene `INTEGER` porque es lo que la base local ya
  tiene y cambiarlo exigiría un `ALTER TABLE ... ALTER COLUMN ... TYPE`, es
  decir, una migración de verdad, que es justo lo que esta feature dice no
  hacer. ¿Se acepta la inconsistencia, o se abre una feature aparte para
  unificar a `BIGINT` cuando entre una herramienta de migración?

- **D2. Longitudes `VARCHAR` heredadas.** `sigrid_parte_cod VARCHAR(24)` y
  `sigrid_estado VARCHAR(16)` vienen de `_ALTERS`; nadie ha comprobado contra
  el diccionario de Sigrid (`azure-apps/sigrid_tablas.md`) que `con.cod` quepa
  siempre en 24. Se conservan tal cual —cambiarlas es una migración de tipo—,
  y **no** se truncan al escribir: si un día no cupiera, preferimos un error
  ruidoso a un código de parte mutilado en la traza. ¿De acuerdo?

- **D3. `sigrid_estado` sin `CheckConstraint`.** Los valores reales son
  `'registrado'`, `'omitido'` y `NULL`. No se declara `CheckConstraint`
  porque el mecanismo derivado solo añade **columnas**: un CHECK declarado en
  el ORM no se aplicaría sobre la base que ya existe y crearía exactamente la
  segunda verdad que esta feature viene a eliminar. ¿Se acepta, o se prefiere
  el CHECK con su `ALTER TABLE ... ADD CONSTRAINT` manual documentado?

- **D4. La traza se pierde al editar el cuadrante.**
  `PgAsignacionRepository.reemplazar()` **borra** todas las asignaciones del
  trabajador y las reinserta, así que cualquier edición posterior al registro
  vacía las seis columnas y cambia los `id` (y con ellos la `synckey`, que es
  `porcentajes:{asignacion_id}`). Es una avería real, preexistente y
  **fuera del alcance de F-003**, que esta spec deja anotada para que alguien
  decida si merece su propia entrada en el backlog.

- **D5. Sin herramienta de migración, por ahora.** Ver `design.md` §6: se
  descarta Alembic hoy y se escribe el criterio objetivo por el que dejaría de
  estar descartado.
