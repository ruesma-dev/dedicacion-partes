<!-- progress/impl_F-003.md -->
# F-003 · Informe de implementación

**Feature:** Las columnas `sigrid_*` de `asignacion` no están en el ORM.
**Rama:** `feature/F-003-orm-columnas-sigrid` · **Rigor:** `critico`.
**Spec:** `specs/F-003-orm-columnas-sigrid/` (implementada entera, T1-T9).
**Servicio tocado:** `dedicacion-api`, y solo él. Ni `dedicacion-front` ni
`dedicacion-transfer` se enteran; ningún contrato HTTP cambia; **contra Sigrid
no se ejecutó ni una lectura**.

---

## 1. Qué cambió

Había dos verdades del esquema de `asignacion`: la del ORM y una lista de seis
`ALTER TABLE` escritos a mano (`_ALTERS`) que se ejecutaban **en el constructor**
de `RegistroSigrid`. Ahora hay una sola: el ORM. El DDL que pone al día una base
ya creada se **deriva** de los metadatos del ORM y se ejecuta **al arrancar**.

| Fichero | Qué se hizo |
|---|---|
| `services/dedicacion-api/infrastructure/db/orm_models.py` | **Modificado.** Las seis columnas `sigrid_*` entran en `AsignacionORM` con los tipos y la nulabilidad de R5 (`String(16/24/300/64)`, `Integer`, `DateTime(timezone=True)`), más el import de `String`. Nada más. |
| `services/dedicacion-api/infrastructure/db/esquema.py` | **Nuevo.** `EsquemaNoDerivable`, `ddl_add_column`, `alters_faltantes` (las tres puras), `columnas_existentes` y `sincronizar_esquema`. El docstring del módulo declara el límite de R13. |
| `services/dedicacion-api/main.py` | **Modificado.** `Base.metadata.create_all(engine)` → `aplicadas = sincronizar_esquema(engine)`, y el log dice cuántas sentencias DDL se aplicaron. |
| `services/dedicacion-api/application/registro_sigrid.py` | **Modificado.** Fuera `_ALTERS`, fuera el bucle DDL del constructor y fuera el import de `text`. `_trazar` reescrito con `update(AsignacionORM)`; el usuario se trunca a 64 (R7). `_payloads`, `preflight`, `ejecutar` y la división entre 100 del porcentaje, intactos. |
| `services/dedicacion-api/tests/test_f003_esquema.py` | **Nuevo.** 63 tests offline con nombres `test_f003_rN_*`. |
| `docs/CONVENTIONS.md` | **Modificado.** La sección «SQL» citaba `_ALTERS` como contraejemplo «que está en el backlog»; ahora apunta a `infrastructure/db/esquema.py` y escribe el límite (solo añade columnas). |
| `services/dedicacion-api/README.md` | **Modificado.** Nota de que el esquema se pone al día **solo** al arrancar por `python main.py`, no al construir la app. |
| `docs/ARCHITECTURE.md` | **Modificado (1 línea).** El inventario de `infrastructure/db/` no mencionaba `esquema.py`. |
| `services/dedicacion-api/infrastructure/db/database.py` | **Modificado (docstring).** Decía «se ejecuta create_all»; era falso tras T4. Solo el docstring: el bootstrap de rol y base no se toca. |

### El efecto secundario que era el objetivo real

Hasta hoy, `interface_adapters/api/deps.py` instanciaba `RegistroSigrid` dentro
de `build_app()`, y ese constructor abría una sesión y ejecutaba DDL: **importar
y construir la aplicación abría una conexión a PostgreSQL**. Ya no. El
constructor es wiring puro (`self._sf`, `self._transfer`) y hay un test que lo
sujeta (`test_f003_r4_construir_registro_sigrid_no_ejecuta_nada`). Es lo que
abre la puerta a tests de la API.

Su contrapartida, deliberada y ya escrita en el `README`: arrancar con `uvicorn`
apuntando a la app en vez de `python main.py` **se salta la puesta al día del
esquema**. `main.py` es la única vía documentada y la del `Dockerfile`.

### Un commit por tarea

```
e8bd45e F-003 T1: suite offline del esquema derivado del ORM (fase RED)
b4ff052 F-003 T2: las seis columnas sigrid_* pasan al ORM
b3cfbc5 F-003 T3: DDL complementario derivado del ORM en infrastructure/db/esquema.py
99a2206 F-003 T4: el arranque sincroniza el esquema en vez de create_all
a460214 F-003 T5: retira _ALTERS y reescribe la traza con update(AsignacionORM)
4a27175 F-003 T6: la documentacion apunta al DDL derivado del ORM
f83832d F-003 T7: los tests comprueban el WHERE de las tres ramas de la traza
```

Ningún `git push`, ningún PR, ningún commit fuera de la rama. `harness/features.json`
y `progress/current.md` no se han tocado: los lleva el líder.

---

## 2. Fase RED (obligatoria en nivel `critico`)

Los tests se escribieron **enteros** en T1, antes de que existiera
`esquema.py` y antes de que el ORM declarase ninguna columna. Comando exacto:

```
cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f003_esquema.py -q
```

Resultado de esa primera ejecución (salida real, recortada por brevedad en la
parte repetitiva):

```
FFFFFFFFFFFFFFFFFFFFF.EEEEEEEEEEEEEEEEFFEEEFFF.FFFFFFFFFFFFFFFE          [100%]
=================================== ERRORS ====================================
_ ERROR at setup of test_f003_r17_el_ddl_derivado_es_el_esperado_caracter_a_caracter _

    @pytest.fixture()
    def esquema():
        """El módulo bajo prueba.
        ...
        """
>       from infrastructure.db import esquema as modulo
E       ImportError: cannot import name 'esquema' from 'infrastructure.db' (C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api\infrastructure\db\__init__.py)

tests\test_f003_esquema.py:75: ImportError
...
41 failed, 2 passed, 20 errors in 5.07s
```

Y las trazas de los tres requisitos centrales, una a una:

```
_______ test_f003_r1_la_columna_esta_declarada_en_el_orm[sigrid_estado] _______
>       assert hasattr(AsignacionORM, nombre), (
E       AssertionError: AsignacionORM no declara sigrid_estado: sigue habiendo
E       dos verdades del esquema (ORM y DDL escrito a mano)
E       assert False
E        +  where False = hasattr(AsignacionORM, 'sigrid_estado')

___________ test_f003_r4_construir_registro_sigrid_no_ejecuta_nada ____________
        fabrica = _FabricaSesiones()
        RegistroSigrid(fabrica, transfer=object())
>       assert fabrica.aperturas == 0
E       assert 1 == 0
E        +  where 1 = <tests.test_f003_esquema._FabricaSesiones object ...>.aperturas

_____________ test_f003_r14_rama_escritas_fija_las_seis_columnas ______________
>       assert len(sentencias) == 1
E       assert 7 == 1
E        +  where 7 = len([<sqlalchemy.sql.elements.TextClause object at ...>, ...])

_________________ test_f003_r7_el_usuario_se_trunca_a_64[64] __________________
>       escrito = _valores(sentencias[0])["sigrid_registrado_by"]
E       KeyError: 'sigrid_registrado_by'
```

Léase el `7 == 1`: en RED, construir `RegistroSigrid` emitía las **seis**
sentencias de `_ALTERS` antes de la única de la traza. Es la avería, medida.

Los 2 tests que ya pasaban en RED no son ruido y conviene decir por qué:
`test_f003_r16_el_servicio_no_tiene_select_estrella` (no había `SELECT *` antes
ni ahora) y `test_f003_r17_la_traza_escribe_exactamente_esas_columnas` (los seis
nombres ya se mencionaban en `registro_sigrid.py`, en las cadenas de `_ALTERS`).
Son guardias anti-regresión, no comprobaciones de código nuevo.

Después de T2 (ORM) y T3 (`esquema.py`), verde progresivo:

```
# tras T2 (el ORM ya declara las seis; el mecanismo sigue rojo)
$ .venv/Scripts/python -m pytest tests/test_f003_esquema.py -q -k "r1_la_columna or r5_el_tipo or r5_la_columna or r6_la_marca or r8_la_tabla or r17_el_orm"
21 passed, 42 deselected in 1.99s

# tras T3 (todo menos lo que T5 tiene que arreglar)
$ .venv/Scripts/python -m pytest tests/test_f003_esquema.py -q -k "not r14 and not r7 and not r2_el_registro and not r4_construir and not r4_main and not r5_el_parte and not r5_los_recortes"
43 passed, 20 deselected in 1.95s

# tras T5, la suite entera del servicio
$ .venv/Scripts/python -m pytest tests -q
84 passed in 2.27s
```

(El `-k "r1 or r5 or r6"` literal de `tasks.md` T2 no sirve: `-k` casa por
subcadena, así que «r1» arrastra r10-r17 y «r5» arrastra r5 del mecanismo. De
ahí la selección explícita de arriba.)

---

## 3. Decisiones de diseño (y las que se dejaron quietas)

1. **`esquema.py` separa lo puro de lo impuro.** `ddl_add_column` y
   `alters_faltantes` reciben el estado de la base **como dato**
   (`{tabla: {columnas}}`) y no abren nada; `columnas_existentes` lo consulta y
   no decide nada. Toda la decisión es comprobable sin PostgreSQL, que es lo que
   pedía R18.
2. **El tipo se compila, no se escribe.**
   `CreateColumn(columna).compile(dialect=postgresql.dialect()).string` produce
   `sigrid_estado VARCHAR(16)`. Un `server_default` y un `NOT NULL` se arrastran
   solos (hay test). Es R3 al pie de la letra.
3. **Orden de emisión: el de declaración del ORM** (`metadata.tables.values()` y
   `tabla.columns`, ambos en orden de declaración). Un `set` haría la salida
   dependiente del hash y el test no podría compararla como lista.
4. **Los cortes de `_trazar` dejan de ser números sueltos.** Se declararon
   `_MAX_MOTIVO = 300` y `_MAX_USUARIO = 64` y hay un test que los compara
   contra `AsignacionORM.__table__.columns[...].type.length`: cambiar el
   `VARCHAR` sin cambiar el corte (o al revés) rompe la suite. Esto sustituye al
   `grep` de `"[:300]"` sobre el fuente que traía la spec, que comprobaba menos.
5. **`sincronizar_esquema` devuelve la lista de sentencias** en vez de
   registrarlas y callar: `main.py` la usa para el log y el test la usa para
   afirmar qué se ejecutó, sin capturar logs.
6. **No se tocó `repositories.py`.** Se confirmó lo que decía el diseño:
   `reemplazar()` construye `AsignacionORM(...)` con kwargs explícitos (las seis
   nuevas son nulables) y `_a_linea` mapea campo a campo. Hay un test que barre
   `domain/`, `application/`, `infrastructure/` e `interface_adapters/` buscando
   `SELECT *` (R16).

---

## 4. Desviaciones respecto a la spec (todas menores, ninguna de diseño)

1. **`requirements.md` R8 y `design.md` §4 dicen «dieciséis columnas» y «las
   diez actuales más las seis».** Contadas en `orm_models.py`, `asignacion`
   tenía **ocho** columnas, no diez: el total queda en **catorce**. Es un desliz
   aritmético de la prosa; la tabla normativa de R5 (seis columnas) es correcta
   y el diseño no depende del número. Queda anotado en el propio test
   (`COLUMNAS_PREVIAS`) y **aquí**, para que el reviewer no lo lea como un
   descuadre de la implementación. Merece una corrección de la spec.
2. **El orden de tareas de `tasks.md` no cuadra del todo.** T1 pide escribir los
   tests de R1/R5/R6/R8-R13/R17, y T3 pide que «`pytest tests/test_f003_esquema.py`
   entero» quede en verde; pero los tests de R2/R4/R7/R14 (que T5 exige que
   existan) no pueden estar verdes antes de T5. Se escribieron **todos** los
   tests en T1 —más RED, no menos— y la verificación de T3 se ejecutó
   deseleccionando los que T5 tenía que arreglar. Se deja constancia del comando
   exacto en §2.
3. **Un test del límite R13 hubo que rehacerlo.** El escenario que proponía el
   diseño («a la base le falta todo menos las claves primarias») hace saltar
   `EsquemaNoDerivable` por `trabajador.nombre`, que es `NOT NULL` sin
   `server_default`: probaba R12, no R13. Se sustituyó por dos tablas ad-hoc
   cuyas columnas ausentes son todas añadibles, más las seis de `asignacion`.
   El requisito comprobado es el mismo.
4. **Dos tests de más sobre lo que la spec dejaba sin cubrir.**
   `test_f003_r4_sincronizar_esquema_crea_tablas_antes_de_inspeccionar` y
   `test_f003_r8_columnas_existentes_radiografia_la_base` ejercitan las dos
   funciones impuras con un motor y un inspector de mentira (`monkeypatch`).
   Siguen sin tocar red ni BBDD y cubren dos cosas que ningún test comprobaba:
   que `create_all` va **antes** de la inspección (si no, una tabla recién creada
   se vería como inexistente) y que cada sentencia se ejecuta dentro de la
   transacción. Gracias a ellos `esquema.py` queda al 100 % de cobertura.
5. **Se tocaron dos ficheros que `design.md` §3 daba por intocables**, y solo en
   documentación: el docstring de `database.py` (decía «se ejecuta create_all»,
   falso tras T4) y una línea de `docs/ARCHITECTURE.md` (el inventario de
   `infrastructure/db/` no mencionaba `esquema.py`). Cero cambios de
   comportamiento. Es el mismo motivo por el que T6 existe: documentación que
   quedaba mintiendo.

---

## 5. Evidencias

| Evidencia | Valor real |
|---|---|
| **Tests ejecutados** (servicio `api`) | **84 passed, 0 failed** (`pytest tests -q` desde `services/dedicacion-api`). De ellos, **63** son de F-003 (`tests/test_f003_esquema.py`) y 21 de F-001 (`tests/test_estados.py`). |
| **Tests del resto del portero** | raíz: 11 passed · `transfer`: verde (caché, árbol sin cambios) · `front`: sin directorio de tests (aviso preexistente, no lo introduce F-003) |
| **Tiempo de ejecución de la suite** | `api`: **2,28 s** (medias de 1,50 s a 2,75 s entre pasadas) · raíz: 0,16 s · campaña de mutación completa: 31,4 s |
| **Cobertura de las líneas cambiadas** | **94,4 % — 51 de 54 líneas** (umbral 80 %, nivel `critico`). Línea literal: `[OK] PUERTA COBERTURA: 94.4% de 54 líneas cambiadas cubiertas (51/54, umbral 80%, nivel critico)` |
| Detalle de lo no cubierto | Las **3** líneas son las de `main.py`: el `import` de `sincronizar_esquema`, la llamada y el `logger.info`. Ningún test importa `main` bajo medición porque arrancar el servicio exige PostgreSQL; el wiring se comprueba leyendo el fuente (`test_f003_r4_main_sincroniza_el_esquema_al_arrancar`) y de verdad en la verificación MANUAL T8. `esquema.py`, `orm_models.py` y `registro_sigrid.py` no tienen **ninguna** línea cambiada sin cubrir. |
| **Mutantes generados y supervivientes** | **14 generados, 14 evaluados, 14 muertos, 0 supervivientes, 0 timeouts.** Informe: `progress/mutacion_F-003.md`. |
| Lint (`ruff`, no bloqueante) | **164 → 162** avisos en el repositorio. Los cinco ficheros de F-003 están limpios (`All checks passed!`); los dos avisos que desaparecen son los `ISC004` de `_ALTERS`. |
| **`bash harness/init.sh`** | **exit 0 · `ENTORNO LISTO. Puedes trabajar.`** |

### La campaña de mutación, con su historia

La **primera** campaña dejó **2 supervivientes**, y eran de verdad:

```
[5/14] superviviente registro_sigrid.py:130 [comparacion] .where(AsignacionORM.id == rid, -> .where(AsignacionORM.id != rid,
[6/14] superviviente registro_sigrid.py:137 [comparacion] .where(AsignacionORM.id == o["registro_id"]) -> .where(AsignacionORM.id != o["registro_id"])
```

Ningún test miraba el `WHERE` de las ramas `ya_registradas` y `omitidas`: con
`!=`, la traza habría marcado como registradas o como omitidas **todas las
asignaciones menos la suya**, y la suite habría seguido en verde. No es un
mutante equivalente: es un fallo que se habría escapado a producción. Se añadió
el helper `_condicion_de_id` y las tres ramas comprueban ahora el filtro
compilado y el valor del bind (commit `f83832d`). Segunda campaña, **0
supervivientes**. No hay ningún superviviente que justificar.

Comando exacto de las dos campañas (`--workers 1` porque los artefactos de
cobertura versionados dejan el árbol sucio tras `init.sh` y la campaña paralela
se niega a crear worktrees sobre un árbol sucio — es la avería F-009 del
backlog, no de esta feature):

```
python -m harness.mutacion --feature F-003 --workers 1
```

---

## 6. Verificaciones MANUAL (humano) pendientes

### T8 · Arranque contra la base real — LA IMPORTANTE

**Ningún agente la ejecuta.** La base local ya tiene las seis columnas (las creó
`_ALTERS` en su día) y **tiene datos**, así que el resultado correcto de esta
feature en tu máquina es que **no pase absolutamente nada**: cero sentencias DDL
emitidas, mismas columnas, mismas filas.

Desde `services/dedicacion-api`, con el `.env` local (`PG_HOST=localhost`):

```bash
# 1. Fotografía previa de las columnas de asignacion y del número de filas
.venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.db.database import crear_engine; from sqlalchemy import inspect, text; e=crear_engine(get_settings()); print(sorted(c['name'] for c in inspect(e).get_columns('asignacion'))); print(e.connect().execute(text('SELECT count(*) FROM asignacion')).scalar())"

# 2. Primer arranque (Ctrl+C en cuanto uvicorn diga 'Application startup complete')
.venv/Scripts/python main.py

# 3. Segundo arranque: debe comportarse igual, sin error (idempotencia, R11)
.venv/Scripts/python main.py

# 4. Misma fotografía que en el paso 1
.venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.db.database import crear_engine; from sqlalchemy import inspect, text; e=crear_engine(get_settings()); print(sorted(c['name'] for c in inspect(e).get_columns('asignacion'))); print(e.connect().execute(text('SELECT count(*) FROM asignacion')).scalar())"
```

**Qué tiene que salir:**

- Pasos 1 y 4: **la misma lista de columnas** (las 14) y **el mismo recuento de
  filas**. Si el recuento cambia, para y avisa.
- Pasos 2 y 3: en el log, la línea
  `Esquema verificado en BBDD 'dedicacion': 0 sentencias DDL aplicadas`.
  **El número tiene que ser 0 en los dos arranques.** Si el primero dijera un
  número mayor que cero, significaría que a la base le faltaba alguna columna
  (mira cuál: cada `ALTER` se registra en el log con nivel INFO, línea
  `DDL complementario: ALTER TABLE ...`); si el **segundo** dijera algo distinto
  de 0, la idempotencia estaría rota y eso sí es un fallo de esta feature.
- Ninguno de los dos arranques debe emitir `EsquemaNoDerivable`. Si lo hiciera,
  nombraría la tabla y la columna: sería una columna `NOT NULL` sin default que
  falta en tu base, y exige una migración escrita a mano (R12).

El resultado real se anota en `progress/current.md`.

### T8 bis · Lo que esta feature NO puede comprobar sola

Una comprobación de la traza de extremo a extremo (que un registro real deje
`sigrid_estado='registrado'` con su `sigrid_parte_cod`) exigiría **escribir en
Sigrid** a través de `dedicacion-transfer`. Fuera del alcance de F-003 y fuera
de lo que ningún agente hace por su cuenta. Los `UPDATE` se han verificado
compilados contra el dialecto PostgreSQL, columna a columna y valor a valor,
pero **nadie los ha ejecutado contra la base**.

---

## 7. Qué queda fuera (y por qué)

- **Alembic y las migraciones de verdad.** Descartado hoy con criterio escrito
  (`design.md` §6): entra el día del primer cambio de esquema que no sea «añadir
  una columna nulable» —cambiar un tipo, renombrar, borrar, mover datos— o el
  día que haya más de un entorno con la base (el despliegue sobre
  `psql-albaranes-rs9k2` u otro servidor, hoy sin decidir). Ese día `esquema.py`
  se retira. El criterio está también en `docs/CONVENTIONS.md`.
- **Detectar una columna con el mismo nombre y otro tipo.** `alters_faltantes`
  compara **nombres**, no tipos, y está declarado como límite en R13 y en el
  docstring del módulo. Comparar tipos daría falsos positivos conocidos
  (`VARCHAR` vs `TEXT`, `TIMESTAMPTZ` vs `TIMESTAMP WITH TIME ZONE`) y, sobre
  todo, el sistema no podría **corregir** lo que detectase sin una migración.
- **Borrar columnas sobrantes, cambiar restricciones o índices de tablas
  existentes.** Mismo límite; hay un test que confirma que el DDL emitido nunca
  contiene `DROP`, `ALTER COLUMN` ni `ADD CONSTRAINT`.
- **Las decisiones abiertas D1-D5 de `requirements.md`.** Siguen abiertas: son
  del humano, no del implementer. Recordatorio de las dos que más pican:
  - **D1**: `sigrid_hmores_ide` se queda en `INTEGER` mientras el resto de `ide`
    del ORM son `BigInteger`. Es lo que la base ya tiene; unificarlo es una
    migración de tipo.
  - **D4**: `PgAsignacionRepository.reemplazar()` **borra y reinserta** las
    asignaciones del trabajador, así que cualquier edición del cuadrante
    posterior al registro vacía las seis columnas y cambia los `id` (y con ellos
    la `synckey`, que es `porcentajes:{asignacion_id}`). Es una avería real y
    preexistente, **fuera del alcance de F-003**, y merece su propia entrada en
    el backlog.
- **La suite del front.** `init.sh` sigue avisando de que `dedicacion-front` no
  tiene tests. Preexistente, no lo introduce ni lo agrava esta feature.
- **Los artefactos de cobertura versionados** (`coverage.json`, `.coverage`, y
  sus gemelos en `services/dedicacion-api/`) quedan modificados en el árbol
  porque `init.sh` los reescribe. **No se han commiteado**: no son trabajo de
  esta feature. Es la avería F-009 del backlog.
- **Ojo, líder: el árbol trae más cambios sin commitear que no son míos.**
  Durante esta sesión aparecieron, de otra mano, una feature **F-011** nueva en
  `harness/features.json` y el fichero `progress/sigrid_F-002.md`; `BACKLOG.md`
  quedó modificado porque `init.sh` lo regenera desde ese JSON. Los he dejado
  **sin tocar y sin commitear**: `tasks.md` me prohíbe expresamente tocar
  `harness/features.json` y `progress/current.md`. También sigue ahí, de antes,
  `progress/explore_transfer_original.md` sin versionar. Al cerrar la feature,
  revísalos aparte del diff de F-003.
