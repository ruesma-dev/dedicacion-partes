<!-- progress/current.md -->
# Trabajo en curso

**F-003 · Las columnas `sigrid_*` de `asignacion` no están en el ORM**
Rama `feature/F-003-orm-columnas-sigrid` · `sdd: true` · rigor `critico`
Estado: **implementada (T1–T7, T9) y revisada. Falta la verificación MANUAL
T8, que solo puede hacer el humano.**

> Esta rama contiene únicamente F-003. El trabajo de **F-002** vive en
> `feature/F-002-reglas-postventa-conflicto` y su estado se describe en el
> `progress/current.md` de esa rama.

## ⚠ VERIFICACIÓN MANUAL PENDIENTE (humano) · T8 — la importante

**Ningún agente la ejecuta.** Es la única comprobación de que el mecanismo de
DDL derivado del ORM se comporta bien **contra tu base real, que tiene datos**.
La base local ya tiene las seis columnas (las creó `_ALTERS` en su día), así
que **el resultado correcto es que no pase absolutamente nada**.

Desde `services/dedicacion-api`, con el `.env` local (`PG_HOST=localhost`):

```bash
# 1. Fotografía previa: columnas de asignacion y número de filas
.venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.db.database import crear_engine; from sqlalchemy import inspect, text; e=crear_engine(get_settings()); print(sorted(c['name'] for c in inspect(e).get_columns('asignacion'))); print(e.connect().execute(text('SELECT count(*) FROM asignacion')).scalar())"

# 2. Primer arranque (Ctrl+C cuando uvicorn diga 'Application startup complete')
.venv/Scripts/python main.py

# 3. Segundo arranque: debe comportarse igual (idempotencia, R11)
.venv/Scripts/python main.py

# 4. Misma fotografía que el paso 1
.venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.db.database import crear_engine; from sqlalchemy import inspect, text; e=crear_engine(get_settings()); print(sorted(c['name'] for c in inspect(e).get_columns('asignacion'))); print(e.connect().execute(text('SELECT count(*) FROM asignacion')).scalar())"
```

**Qué tiene que salir:**

- Pasos 1 y 4: **la misma lista de columnas** (las 14) y **el mismo recuento
  de filas**. Si el recuento cambia, para y avisa.
- Pasos 2 y 3: en el log,
  `Esquema verificado en BBDD 'dedicacion': 0 sentencias DDL aplicadas`.
  **Cero en los dos arranques.** Si el primero diera más de cero, a la base le
  faltaba alguna columna (cada `ALTER` se registra en el log como
  `DDL complementario: ALTER TABLE ...`). Si el **segundo** diera algo
  distinto de 0, la idempotencia estaría rota y eso sí sería un fallo de esta
  feature.
- Ninguno de los dos arranques debe emitir `EsquemaNoDerivable`. Si lo hiciera
  nombraría tabla y columna: sería una columna `NOT NULL` sin default que
  falta en tu base y exigiría una migración escrita a mano (R12).

**El resultado real se anota aquí cuando lo ejecutes.** Sin eso, F-003 no se
cierra.

### T8 bis · lo que F-003 no puede comprobar sola

Ver la traza de extremo a extremo (que un registro real deje
`sigrid_estado='registrado'` con su `sigrid_parte_cod`) exigiría **escribir en
Sigrid** a través de `dedicacion-transfer`: fuera del alcance de F-003. Los
`UPDATE` están verificados compilados contra el dialecto PostgreSQL, columna a
columna, pero **nadie los ha ejecutado contra la base**.

## Qué se hizo en F-003

`_ALTERS` (la lista de `ALTER TABLE` escrita a mano en
`application/registro_sigrid.py`) **desaparece**. Las seis columnas
`sigrid_*` pasan al ORM, que queda como **única fuente de verdad**, y el DDL
complementario se **deriva** de él en `infrastructure/db/esquema.py`,
ejecutado desde `main.py` junto a `create_all` y **fuera de `build_app`**.

Efecto colateral deliberado y valioso: **construir la app ya no abre conexión
a PostgreSQL**. Antes, el constructor de `RegistroSigrid` lanzaba el DDL, así
que importar la aplicación exigía base de datos: por eso el servicio no podía
tener tests de API. Ahora puede.

| Tarea | Estado | Commit |
|---|---|---|
| T1 · suite offline del esquema derivado (fase RED) | [x] | `e8bd45e` |
| T2 · las seis columnas al ORM | [x] | `b4ff052` |
| T3 · `infrastructure/db/esquema.py` | [x] | `b3cfbc5` |
| T4 · el arranque sincroniza el esquema | [x] | `99a2206` |
| T5 · retira `_ALTERS`, traza con `update(AsignacionORM)` | [x] | `a460214` |
| T6 · documentación apuntando al DDL derivado | [x] | `4a27175` |
| T7 · tests del `WHERE` de las tres ramas | [x] | `f83832d` |
| **T8 · verificación MANUAL contra la base real** | **[ ]** | **del humano** |
| T9 · informe y campaña de mutación | [x] | `db4794b` |

### Verificado con salida real

- `bash harness/init.sh` → exit 0, ENTORNO LISTO.
- Suite del api: **84 passed** (63 de F-003 + 21 de F-001). Raíz: 11 passed.
- **Puerta de cobertura: 94,4 % (51/54 líneas cambiadas)**, umbral 80 %.
- **Mutación: 14 mutantes, 14 muertos, 0 supervivientes.** La primera campaña
  dejó **2 supervivientes reales** y el implementer escribió los tests que
  faltaban hasta matarlos, en vez de justificarlos por escrito.
- Fase RED real: **41 failed + 20 errors** antes de existir `esquema.py`.
- ruff: **164 → 162** avisos (bajan al retirar `_ALTERS`).

Informes: `progress/impl_F-003.md`, `progress/review_F-003.md`,
`progress/mutacion_F-003.md`.

## Estado de las demás features

- **F-001** · `done`, mergeada a `dev` y publicada en GitHub.
- **F-002** · `in_progress`. Fase 1 (T1–T5) **aprobada**; spec v2 escrita con
  las decisiones D1 y D2 cerradas. Falta implementar la Fase 2: la **regla de
  capacidad del 100 %** (varias partidas por trabajador sí, pero la suma del
  mes no pasa de 1; avisa y espera confirmación, viajando como un conflicto
  más para no tocar API ni front).
- **F-011** · abierta el 2026-08-19 por decisión del humano: hoy, si un
  recurso tiene varios códigos `M*`, se elige el primero por orden alfabético
  y de ahí sale el importe mensual que se escribe en Sigrid. Se deja así de
  momento y se pide a Administración un único código de hora mes por
  trabajador. **Pendiente de commitear en la rama de F-002.**

## Hechos comprobados que no conviene volver a descubrir

- **Este sistema NUNCA ha escrito en Sigrid.** Demostrado el 2026-08-19 con la
  consulta C6 (0 filas con `synckey LIKE 'porcentajes:%'` o marca
  `PRUEBA-PORC`). Lo que hubo en julio fueron cinco **preflights** en modo
  pruebas. Ver `progress/explore_transfer_original.md`.
- El original `porcentajes-transfer` y el código migrado son **byte a byte
  idénticos**: no se perdió lógica en la migración.
- `ruff` **no está instalado** en el venv de `dedicacion-api`: para lintar ese
  servicio hay que usar el intérprete de la raíz.
- **F-009 ya ha estorbado tres veces**: los artefactos de cobertura
  versionados ensucian el árbol en cada `init.sh` y obligan a lanzar la
  campaña de mutación con `--workers 1`.

## Nota de proceso (para el líder de la próxima sesión)

Dos reviews seguidas (F-002 Fase 1 y F-003) se rechazaron por **este fichero
sin actualizar**, no por el código. `progress/current.md` es del líder: hay
que actualizarlo **al lanzar** cada feature y **listar ahí** las
verificaciones MANUAL con su comando, que es donde `CHECKPOINTS.md` C4 las
exige. No basta con que estén en `tasks.md` o en el informe del implementer.
