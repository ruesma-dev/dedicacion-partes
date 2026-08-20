<!-- specs/F-003-orm-columnas-sigrid/tasks.md -->
# F-003 · Tareas

Rama: `feature/F-003-orm-columnas-sigrid` (la crea el líder; el spec-author
trabajó sobre el árbol de F-002 sin cambiar de rama).
Un commit por tarea: `F-003 Tn: descripción`.

> **Rigor `critico`.** T1 es la fase RED y va **antes** que el código: la
> traza real del fallo se pega en `progress/impl_F-003.md`. Los tests
> comparan **cadenas exactas**, no subcadenas: es lo que evita supervivientes
> en la campaña de mutación sobre la construcción del DDL.

> **Prohibido tocar** `harness/features.json` y `progress/current.md` durante
> las tareas de código: los lleva el líder.

---

## Fase 1 — RED

- [x] **T1**: Crear `services/dedicacion-api/tests/test_f003_esquema.py` con
  los tests de R1, R5, R6, R8-R13 y R17 escritos contra el API que todavía no
  existe (`infrastructure/db/esquema.py`) y contra las seis columnas que aún
  no están en el ORM. Nombres `test_f003_rN_*`. Sin red ni BBDD.
  **Verificación:** `cd services/dedicacion-api && .venv/Scripts/python -m
  pytest tests/test_f003_esquema.py -q` falla con `ModuleNotFoundError:
  infrastructure.db.esquema` y con los `AttributeError` de las columnas
  ausentes. **Pegar la salida real en `progress/impl_F-003.md`** (fase RED,
  C4 bis).

## Fase 2 — El ORM pasa a ser la fuente de verdad

- [x] **T2**: Declarar en `AsignacionORM` (`infrastructure/db/orm_models.py`)
  las seis columnas `sigrid_*` con los tipos y la nulabilidad de la tabla de
  `requirements.md` R5, más el import de `String`. Nada más en ese fichero.
  **Verificación:** `pytest tests/test_f003_esquema.py -q -k "r1 or r5 or r6"`
  en verde; los tests del mecanismo siguen rojos.

- [x] **T3**: Crear `infrastructure/db/esquema.py` con
  `EsquemaNoDerivable`, `ddl_add_column`, `alters_faltantes`,
  `columnas_existentes` y `sincronizar_esquema`, según `design.md` §1. Las dos
  primeras y `alters_faltantes` son puras; el docstring del módulo declara el
  límite de R13 (solo añade columnas: no cambia tipos, no borra, no toca
  restricciones).
  **Verificación:** `pytest tests/test_f003_esquema.py -q` entero en verde.

- [x] **T4**: Cambiar `main.py` para que llame a `sincronizar_esquema(engine)`
  en lugar de `Base.metadata.create_all(engine)` y registre en el log cuántas
  sentencias aplicó.
  **Verificación:** `pytest tests -q` en verde y
  `.venv/Scripts/python -c "import main"` sin error (comprueba imports; no
  arranca nada).

## Fase 3 — Retirar la segunda verdad

- [x] **T5**: En `application/registro_sigrid.py`: borrar `_ALTERS` y el bucle
  DDL del constructor, borrar el import de `text`, reescribir `_trazar` con
  `update(AsignacionORM)` (`is_distinct_from` para la rama
  `ya_registradas`) y truncar el usuario a 64 (R7). Sin tocar `_payloads`,
  `preflight` ni `ejecutar`, y sin tocar la división entre 100 del porcentaje.
  **Verificación:** `pytest tests/test_f003_esquema.py -q` en verde,
  incluidos el test de R2 (el fuente no contiene `ALTER TABLE` ni `_ALTERS`),
  el de R4 (construir `RegistroSigrid` no ejecuta ninguna sentencia) y los de
  R7/R14 sobre las tres ramas de `_trazar`.

- [x] **T6**: Actualizar la sección «SQL» de `docs/CONVENTIONS.md` (la frase
  que cita `_ALTERS` como contraejemplo «que está en el backlog» queda falsa)
  para que apunte a `infrastructure/db/esquema.py`, y añadir al `README` de
  `services/dedicacion-api` la nota de que el esquema se pone al día **solo**
  al arrancar por `python main.py`, no al construir la app.
  **Verificación:** `grep -rn "_ALTERS" docs/ services/ --include=*.md
  --include=*.py` no devuelve nada fuera de `specs/` y `progress/`.

## Fase 4 — Puertas de rigor `critico`

- [x] **T7**: Campaña de mutación.
  **Verificación:** `python -m harness.mutacion --feature F-003` con
  **cero supervivientes**, informe en `progress/mutacion_F-003.md`. Cada
  superviviente exige un test nuevo o una justificación escrita para el
  humano; los candidatos previsibles son la construcción de la cadena del
  `ALTER` y los cortes `[:300]` / `[:64]`, todos ellos con test de cadena
  exacta y de longitud límite.

- [ ] **T8** (PENDIENTE, la ejecuta el humano): **Verificación MANUAL (humano)** — arranque contra la base real.
  No la ejecuta ningún agente. Comandos exactos, desde
  `services/dedicacion-api` y con el `.env` local (`PG_HOST=localhost`):

  ```bash
  # 1. Fotografía previa de las columnas de asignacion
  .venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.db.database import crear_engine; from sqlalchemy import inspect; e=crear_engine(get_settings()); print(sorted(c['name'] for c in inspect(e).get_columns('asignacion')))"

  # 2. Primer arranque (Ctrl+C en cuanto uvicorn diga 'Application startup complete')
  .venv/Scripts/python main.py

  # 3. Segundo arranque: debe comportarse igual, sin error (idempotencia, R11)
  .venv/Scripts/python main.py

  # 4. Misma fotografía: las 16 columnas, sin duplicados, y el mismo número
  #    de filas que antes
  .venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.db.database import crear_engine; from sqlalchemy import inspect, text; e=crear_engine(get_settings()); print(sorted(c['name'] for c in inspect(e).get_columns('asignacion'))); print(e.connect().execute(text('SELECT count(*) FROM asignacion')).scalar())"
  ```

  **Resultado esperado:** los pasos 1 y 4 devuelven la **misma** lista de
  columnas (la base local ya las tiene), el log de los dos arranques dice
  `0 sentencias` de DDL aplicadas, y el recuento de filas no cambia.
  El resultado real se anota en `progress/current.md`.

- [x] **T9**: Ejecutar `bash harness/init.sh` en verde (incluye la suite de
  los tres servicios y la puerta de cobertura de las líneas cambiadas,
  umbral 80 %).
  **Verificación:** exit code 0 y `[OK]` en la puerta de cobertura.
