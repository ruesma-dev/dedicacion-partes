<!-- progress/spec_F-003.md -->
# F-003 · Nota de cierre del spec-author

Fecha: 2026-08-19. Rama de trabajo durante la redacción:
`feature/F-002-reglas-postventa-conflicto` (**no se cambió de rama**, no se
hizo ningún commit y no se tocaron `harness/features.json` ni
`progress/current.md`, según las restricciones del encargo).

## Qué se ha escrito

`specs/F-003-orm-columnas-sigrid/` con los tres ficheros:

- `requirements.md` — 18 requisitos EARS (R1-R18) y 5 decisiones abiertas.
- `design.md` — cómo se crea hoy el esquema, los ficheros a crear/modificar,
  la matriz de comportamiento por estado de la base, la estrategia de tests
  y los riesgos.
- `tasks.md` — T1-T9, con T1 como fase RED y T8 como verificación
  MANUAL (humano) con sus comandos exactos.

Solo se escribió dentro de esa carpeta y en este fichero.

## Lo que se leyó para decidir

- `services/dedicacion-api/main.py`, `infrastructure/db/database.py`,
  `orm_models.py`, `repositories.py`, `interface_adapters/api/{app,deps}.py`,
  `application/registro_sigrid.py`, `tests/conftest.py`, `Dockerfile`,
  `requirements.txt`.
- Búsqueda de las seis columnas y de `_ALTERS` / `create_all` / `SELECT *` /
  `insert(` en todo el servicio.

Hallazgos que condicionan el diseño y conviene que el humano conozca:

1. **No hay ninguna herramienta de migración** en el servicio: ni Alembic, ni
   `migrations/`, ni ficheros `.sql`. El esquema se crea con
   `Base.metadata.create_all`, que **no modifica tablas existentes**. Por eso
   `_ALTERS` existe, y por eso no basta con «meter las columnas en el ORM»:
   sin un paso complementario, una base ya creada nunca las recibiría.
2. **El DDL se ejecuta hoy al construir la app**, no al arrancar: está en el
   constructor de `RegistroSigrid`, que `deps.construir_contenedor` instancia
   dentro de `build_app`. El diseño lo mueve a `main.py`, que es la única vía
   de arranque documentada (`README`) y la del `Dockerfile`.
3. **Nadie lee las seis columnas** fuera de los tres `UPDATE` de `_trazar`:
   ningún endpoint, ningún esquema Pydantic, ningún repositorio. La traza es
   hoy solo de escritura. No hay `SELECT *` ni `insert()` a mano sobre
   `asignacion` en todo el servicio, así que la compatibilidad hacia atrás es
   holgada siempre que las seis columnas se declaren **nulables**.

## Decisiones abiertas que necesitan al humano

Están completas en `requirements.md` §2; en corto:

- **D1.** `sigrid_hmores_ide` se queda `INTEGER` (el resto de `ide` del ORM
  son `BigInteger`) porque cambiarlo exige una migración de tipo.
  ¿Se acepta la inconsistencia o se abre feature aparte?
- **D2.** Se conservan `VARCHAR(16)` y `VARCHAR(24)` heredados de `_ALTERS`,
  sin comprobar contra el diccionario de Sigrid que `con.cod` quepa siempre
  en 24, y **sin truncar** al escribir (se prefiere error ruidoso a dato
  mutilado). ¿De acuerdo?
- **D3.** `sigrid_estado` **sin** `CheckConstraint`, porque el mecanismo
  derivado solo añade columnas y un CHECK declarado no se aplicaría sobre la
  base existente: sería la segunda verdad de vuelta.
- **D4.** Avería preexistente y **fuera de alcance**:
  `PgAsignacionRepository.reemplazar()` borra y reinserta las asignaciones del
  trabajador, así que **editar el cuadrante después de registrar borra la
  traza `sigrid_*` y cambia los `id`** —y con ellos la `synckey`
  `porcentajes:{asignacion_id}`, que viaja escrita en Sigrid. Merece decidir
  si entra en el backlog como feature propia.
- **D5.** Se descarta Alembic hoy, con el criterio objetivo escrito de cuándo
  dejaría de estar descartado (`design.md` §6): el primer cambio de esquema
  que no sea «añadir columna nulable», o el día que haya más de un entorno
  con la base.

## Nada bloqueado

No hay ambigüedad que impida implementar: las cinco decisiones son de
confirmación, no de bloqueo. La opción por defecto de cada una está escrita
en la spec y es la que el implementer debe seguir si el humano no dice otra
cosa. Sí conviene que D4 se anote en el backlog antes de cerrar la sesión,
porque no se arregla en F-003.
