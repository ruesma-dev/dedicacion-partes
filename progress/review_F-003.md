<!-- progress/review_F-003.md -->
# F-003 · Informe de review

**Feature:** Las columnas `sigrid_*` de `asignacion` no están en el ORM.
**Rama revisada:** `feature/F-003-orm-columnas-sigrid` (HEAD `14423c0`).
**Spec:** `specs/F-003-orm-columnas-sigrid/` (requirements + design + tasks).
**Fecha:** 2026-08-19 · **Dos pasadas** (ver «Segunda pasada» al final).

---

## Veredicto

**APPROVED**

Con una condición que no depende de ningún agente y que queda escrita abajo:
**F-003 no puede pasar a `done` hasta que el humano ejecute T8 y anote su
resultado real en `progress/current.md`.** Eso lo exige el nivel `critico`, no
yo, y el líder ya lo ha dejado listado con sus comandos.

### Cómo se llegó aquí

**Primera pasada: CHANGES_REQUESTED.** No por el código —que estaba bien desde
el principio— sino por dos checkboxes de higiene de sesión genuinamente
vacíos: `progress/current.md` describía la sesión **anterior** («Ninguna
feature en ejecución», «la siguiente tarea es F-002») mientras F-003 estaba
`in_progress` (**C2**), y la verificación MANUAL **T8 no estaba listada en ese
fichero**, que es donde C4 la exige (**C4**). Ambos eran del **líder**:
`tasks.md` prohíbe expresamente al implementer tocar `current.md`, y el
implementer lo respetó y avisó del asunto en su informe.

**Segunda pasada: los dos cambios están hechos** en el commit `14423c0`, y bien
hechos —mejor de lo que pedí—. Detalle en la sección «Segunda pasada».

### Lo que sostiene el APPROVED

La implementación no solo pasa: está verificada de forma independiente. He
recalculado el alcance y los mutantes por mi cuenta, he **reejecutado la
campaña de mutación entera** (los 14 muertos son míos, no del informe), he
comprobado **empíricamente** la afirmación central de la feature —construir la
app ya no abre una sola conexión, con `socket.connect` bloqueado— y he leído
las tres ramas de la traza contra el SQL que sustituyen. **No he encontrado ni
un defecto en el trabajo del implementer**, ni en la primera pasada ni en la
segunda.

Y el objetivo real de la feature está conseguido, que era más que añadir seis
columnas: el ORM es **la única fuente de verdad** del esquema, `_ALTERS` ha
desaparecido sin dejar ninguna lista de columnas escrita a mano en el
servicio, el DDL complementario se **deriva** de los metadatos, y se ejecuta en
`main.py` **fuera de `build_app`**.

---

## Nivel de rigor y puertas que exige

`harness/features.json` declara **`rigor: "critico"`** para F-003 (declarado,
no aplicado por omisión). Según `harness/rigor.json` y la tabla de
`CHECKPOINTS.md`, eso exige:

| Puerta | Exigencia | Resultado |
|---|---|---|
| Fase RED | traza real del fallo previo | **cumplida** |
| Cobertura de líneas cambiadas | ≥ 80 % | **94,4 % (51/54)** |
| Campaña de mutación | **cero** supervivientes | **14/14 muertos, 0 supervivientes** |
| Verificaciones `MANUAL (humano)` | listadas con comando exacto **y su resultado real** | **parcial** — ver C4 |

---

## Verificaciones ejecutadas (salida real)

### 1. `bash harness/init.sh` — exit 0

```
[OK] Arnés v1.5.2 (2026-08-18)
     10 features, 9 abiertas, en curso: ['F-003'], bloqueadas: ninguna
[OK] features.json válido
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 162 avisos (deuda previa, no bloquea)
11 passed in 0.50s
[OK] pytest en verde (con medición de cobertura)
84 passed in 3.17s
[OK] servicio api (services/dedicacion-api): pytest en verde
[AVISO] servicio front (services/dedicacion-front): sin directorio de tests
[OK] servicio transfer: pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 94.4% de 54 líneas cambiadas cubiertas (51/54, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-003-orm-columnas-sigrid
ENTORNO LISTO. Puedes trabajar.
```

El aviso del front es **preexistente** y no lo introduce F-003.

### 2. Suites ejecutadas a mano (la del transfer venía de caché)

```
$ cd services/dedicacion-transfer && .venv/Scripts/python -m pytest tests -q
4 passed, 1 warning in 0.34s

$ cd services/dedicacion-api && .venv/Scripts/python -m pytest tests -q
84 passed in 1.41s

$ cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f003_esquema.py -q
63 passed in 1.21s
```

El verde del transfer es **real**, no heredado de la caché. El único aviso
(`PytestReturnNotNoneWarning` en `test_preflight`) es preexistente del transfer
y ajeno a F-003.

### 3. Mutación — verificada de forma independiente

**Recálculo puro** (`harness.alcance` + `harness.mutacion.generar_mutantes`,
sin ejecutar la suite ni escribir en disco):

```
origen: rama | ref_diff: ('c43a12fd730805a107985e0962a8134e8cbc1678', 'feature/F-003-orm-columnas-sigrid')
services/dedicacion-api/application/registro_sigrid.py: 35
services/dedicacion-api/infrastructure/db/database.py: 3
services/dedicacion-api/infrastructure/db/esquema.py: 126
services/dedicacion-api/infrastructure/db/orm_models.py: 17
services/dedicacion-api/main.py: 12
TOTAL lineas: 193      TOTAL MUTANTES: 14
```

Alcance y número de mutantes **coinciden exactamente** con
`progress/mutacion_F-003.md` (193 líneas, 14 mutantes), y el commit base del
diff también.

**Muestreo de los dos supervivientes de la primera campaña** que el implementer
declara en su §5: existen como mutantes reales, con el mismo operador y el
mismo texto original→mutado:

```
registro_sigrid.py:130 [comparacion] .where(AsignacionORM.id == rid, -> .where(AsignacionORM.id != rid,
registro_sigrid.py:137 [comparacion] .where(AsignacionORM.id == o["registro_id"]) -> .where(AsignacionORM.id != o["registro_id"])
```

**Campaña reejecutada.** El informe declara «Tiempo total 31.4 s», por debajo
de los 5 minutos, así que el recálculo puro no bastaba y **reejecuté la campaña
entera**, con salida fuera de `progress/` (mi scratchpad) para no pisar el
informe del implementer:

```
$ python -m harness.mutacion --feature F-003 --workers 1 --salida <scratchpad>/mutacion_F-003_reviewer.md
F-003: 5 fichero(s), 193 línea(s) de producción (origen rama, c43a12fd..feature/F-003-orm-columnas-sigrid)
[1/14] muerto ... [14/14] muerto
14 mutantes evaluados, 14 muertos, 0 supervivientes, 0 timeouts en 24.6 s
```

**Los muertos están comprobados, no solo contados.** Los 14 mutantes murieron
uno a uno en mi propia ejecución. `--workers 1` porque los artefactos de
cobertura versionados dejan el árbol sucio tras `init.sh` y la campaña paralela
se niega a crear worktrees sobre árbol sucio: es la avería **F-009** del
backlog, no de esta feature, y es el mismo motivo que declara el implementer.
`git status` **queda idéntico** antes y después de mi campaña (los 4 artefactos
de cobertura modificados y el fichero sin versionar del líder, nada más).

No aplica la prueba de control de «cero mutantes»: la campaña genera 14.

### 4. La afirmación central de la feature, comprobada empíricamente

El objetivo real no era añadir columnas, sino que **construir la app dejara de
ejecutar DDL**. Lo verifiqué bloqueando `socket.connect` antes de importar nada
y construyendo la aplicación completa:

```
$ cd services/dedicacion-api && .venv/Scripts/python -c "<bloqueo de socket.connect/connect_ex>; build_app()"
OK: build_app() construido sin abrir NINGUNA conexion de red
rutas registradas: 5
registro_sigrid instanciado: RegistroSigrid
```

Es decir: se instancia el contenedor entero, incluido `RegistroSigrid`, **sin
abrir un solo socket**. Antes, el constructor hacía `with self._sf() as s:
s.execute(text(stmt))` sobre las seis sentencias de `_ALTERS`, así que importar
y construir la app abría conexión a PostgreSQL. La fase RED del implementer lo
mide desde el otro lado (`aperturas == 1`, `assert 7 == 1`). **Conseguido.**

### 5. `_ALTERS` y las listas de columnas a mano — buscado, no supuesto

```
$ grep -rn "_ALTERS" (todo el repo, sin specs/ ni progress/)
services/dedicacion-api/tests/test_f003_esquema.py:518  # el guardia que prohíbe la cadena

$ grep -rn "ALTER TABLE|ADD COLUMN|CREATE TABLE|SELECT \*" --include=*.py --include=*.yaml --include=*.sql services/ harness/   (sin .venv)
→ solo esquema.py (docstrings + la f-string que DERIVA el DDL) y el test
```

Y la comprobación que importa: **no queda ninguna lista de nombres de columna
escrita a mano en ningún sitio del servicio**. Los seis nombres `sigrid_*`
aparecen exactamente en dos ficheros de producción, y en ninguno como lista
paralela:

- `infrastructure/db/orm_models.py` — su **declaración** (la única verdad);
- `application/registro_sigrid.py` — su **uso** como atributos de
  `AsignacionORM` en los `update()`, es decir, resueltos contra el ORM.

Ni `config.yaml`, ni `repositories.py`, ni `schemas.py`, ni el front conservan
nada que pueda volver a divergir. El test `r17` cierra el círculo por los dos
lados: el conjunto `sigrid_*` del ORM debe ser **igual** (ni uno de más ni uno
de menos) al de referencia, y los nombres mencionados en el fuente de la traza
deben ser **ese mismo conjunto**.

### 6. Las seis columnas y sus tipos (R5, R6)

Declaradas en `AsignacionORM`, nulables, sin `default` ni `server_default`, con
el tipo compilado contra el dialecto PostgreSQL comprobado **como cadena
exacta** por test parametrizado:

| Columna | ORM | Compila a |
|---|---|---|
| `sigrid_estado` | `String(16)` | `VARCHAR(16)` |
| `sigrid_parte_cod` | `String(24)` | `VARCHAR(24)` |
| `sigrid_hmores_ide` | `Integer` | `INTEGER` |
| `sigrid_motivo` | `String(300)` | `VARCHAR(300)` |
| `sigrid_registrado_at_utc` | `DateTime(timezone=True)` | `TIMESTAMP WITH TIME ZONE` |
| `sigrid_registrado_by` | `String(64)` | `VARCHAR(64)` |

**Atención especial a `sigrid_registrado_at_utc`, como pedía el encargo:** el
tipo es correcto. `DateTime(timezone=True)` → `TIMESTAMP WITH TIME ZONE`, que
es el mismo tipo que el `TIMESTAMPTZ` del viejo `_ALTERS` (alias en
PostgreSQL), así que **la base existente no ve ningún cambio de tipo**. Y está
sujeto por dos sitios: `test_f003_r6_la_marca_de_tiempo_lleva_zona_horaria`
comprueba `columna.type.timezone is True`, y el test de la rama `escritas`
comprueba que el valor escrito lleva `tzinfo` y `utcoffset() == timedelta(0)`.
El mutante `DateTime(timezone=True) -> DateTime(timezone=False)` **murió**. Si
alguien la volviera naíf, la suite lo caza.

### 7. Compatibilidad con la base que ya existe (R9) — el caso real del humano

El escenario del humano es una base con las seis columnas **ya creadas a mano y
con datos**. El diseño garantiza que el arranque **no emita ni una sentencia**,
y lo garantiza por construcción, no por suerte:

1. `Base.metadata.create_all(engine)` no modifica tablas existentes → 0 DDL.
2. `columnas_existentes` radiografía la base y ve las 14 columnas.
3. `alters_faltantes` compara **por nombre**: ninguna falta → lista **vacía**.
4. `sincronizar_esquema` abre la transacción y no ejecuta nada dentro.

Cubierto por **dos** tests, y son los correctos:
`test_f003_r9_base_al_dia_no_genera_ningun_alter` (la función pura devuelve
`[]`) y `test_f003_r9_sincronizar_esquema_no_ejecuta_nada_si_no_falta_nada`,
que además afirma `ejecutadas == []` sobre un motor de mentira, es decir,
comprueba que **no se ejecuta ninguna sentencia**, no solo que la lista sea
vacía. Es exactamente el requisito.

Un matiz que dejo escrito por honestidad, **no es un defecto**:
`alters_faltantes` recorre **todas** las tablas del ORM, no solo `asignacion`.
Si la base local tuviera desfase en `trabajador`, `obra`, `periodo` o `evento`,
el arranque emitiría ALTERs para ellas o abortaría con `EsquemaNoDerivable`. Es
el comportamiento correcto y querido (R10/R12), y el implementer avisa de ello
en las instrucciones de T8. Solo conviene que el humano lo sepa al ejecutar T8.

### 8. La traza reescrita (T5/T7) — las tres ramas hacen lo mismo que antes

Comparado el SQL crudo eliminado contra el `update(AsignacionORM)` que lo
sustituye:

| Rama | Antes (SQL crudo) | Ahora (ORM) | ¿Equivalente? |
|---|---|---|---|
| `escritas` | `WHERE id=:i` | `.where(AsignacionORM.id == e["registro_id"])` | **sí** |
| `ya_registradas` | `WHERE id=:i AND sigrid_estado IS DISTINCT FROM 'registrado'` | `.where(id == rid, sigrid_estado.is_distinct_from("registrado"))` | **sí** |
| `omitidas` | `WHERE id=:i` | `.where(AsignacionORM.id == o["registro_id"])` | **sí** |

El test no se fía de la lectura: compila la sentencia con el dialecto
PostgreSQL y compara el `WHERE` **como cadena** y el valor del bind. Para
`ya_registradas`:

```
"asignacion.id = %(id_1)s AND asignacion.sigrid_estado IS DISTINCT FROM %(sigrid_estado_1)s"
```

Idéntico al original. Y los tres mutantes `==` → `!=` de esas tres ramas
**murieron** en mi campaña: sin ese helper (`_condicion_de_id`), una traza que
marcase todas las asignaciones **menos** la suya habría pasado en verde. Fue un
hallazgo real de la primera campaña del implementer, bien resuelto con test, no
con excusa.

Los `SET` también son equivalentes, con **un cambio deliberado**: el usuario se
trunca a 64 (R7), que antes no se truncaba. Es el requisito, no una regresión.

### 9. Convenciones (`docs/CONVENTIONS.md`)

- Primera línea con ruta relativa en los cinco ficheros: **correcto**
  (`# infrastructure/db/esquema.py`, `# main.py`, etc.).
- Sin `print()`, sin TODO/FIXME sin contexto, **sin secretos** (barrido del
  diff con `password|secret|api_key|token|connectionstring|pwd=`: sin
  resultados).
- Sin dependencias nuevas: `esquema.py` solo usa `sqlalchemy`, ya presente.
- Todo en español, incluidos comentarios y mensajes de commit.
- **Lint.** `ruff` no está en el venv del api, así que lo pasé con el
  intérprete de la raíz. Los cinco ficheros dan **7 avisos**; los mismos dos
  ficheros en `dev` daban **9**. Es decir: **F-003 no introduce ni un aviso
  nuevo y elimina dos** (los `ISC004` de `_ALTERS`). `esquema.py`,
  `orm_models.py` y `test_f003_esquema.py` están **limpios**; los 7 restantes
  (`I001`, `UP045`) son deuda previa de `registro_sigrid.py` y `main.py`, en
  líneas que la feature no toca.
  *Matiz menor:* el informe del implementer dice «los cinco ficheros de F-003
  están limpios (`All checks passed!`)», y eso es exacto para tres de los cinco,
  no para los cinco. El número global que da (164 → 162) sí es correcto y la
  conclusión —cero deuda nueva— también. Lo anoto por precisión, no bloquea.

---

## Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-003`).
- [x] Rama actual `feature/F-003-orm-columnas-sigrid`, nunca `main`.
- [x] **`progress/current.md` describe SOLO la sesión activa.** **Corregido en
      `14423c0`** (2ª pasada). En la 1ª pasada estaba vacío: el fichero
      describía la sesión **anterior** («Ninguna feature en ejecución», F-001
      cerrada, «la siguiente tarea por prioridad es F-002») y solo mencionaba
      F-003 como hipótesis futura. Ahora abre con F-003, su rama, su rigor y su
      estado real, y trae la tabla de las nueve tareas con su commit. La
      sección «Estado de las demás features» **no** es un resto de sesión
      anterior sino contexto deliberado y útil, así que no la cuento en contra.
- [x] Toda feature `done` tiene resumen en `history.md` (solo F-001 está
      `done`, y su resumen está).

### C3 — El código respeta arquitectura y convenciones

- [x] Hexagonal respetada. `esquema.py` va a **infrastructure/db/**, que es su
      capa (DDL es persistencia), y el `application/` se queda **sin** DDL:
      la feature *mejora* la separación en vez de erosionarla. `domain/`
      comprobado limpio: cero imports de `infrastructure`,
      `interface_adapters`, `sqlalchemy` o `fastapi`.
- [x] Primera línea con ruta relativa en todos los ficheros.
- [x] Sin `print()`, sin TODOs sin contexto, sin secretos, sin dependencias
      nuevas.
- [x] **Las tres trampas del proyecto, vigiladas:**
      - **Escala del porcentaje:** `_payloads` **no se toca**;
        `round(float(a.porcentaje) / 100.0, 4)` sigue idéntico. La feature no
        introduce ninguna conversión nueva. Verificado en el diff línea a línea.
      - **Postventa:** `es_postventa` intacto, sigue en la `UniqueConstraint`.
        Ninguna consulta nueva agrupa ni filtra por obra.
      - **Solo escribe el transfer:** F-003 **no abre ni una lectura** contra
        Sigrid, no toca `dedicacion-transfer`, no añade `synckey` ni roza
        `OBRA_PRUEBAS_FORZAR`. El DDL es contra PostgreSQL local.

### C3 bis — Documentos que entran de fuera

**N/A justificado:** el diff no añade ni modifica ningún fichero en
`docs/referencia/` (comprobado en `git diff dev..HEAD --stat`: los únicos
`docs/` tocados son `CONVENTIONS.md` y `ARCHITECTURE.md`, ambos normativos del
propio repositorio, no documentos externos). No hay original en PDF ni
ofimática en el árbol ni en el historial de la rama.

### C4 — La verificación es real

- [x] **Requisitos con test trazable y en verde.** 63 tests, nombres
      `test_f003_rN_*`, cubriendo R1-R14, R16 y R17. Tabla completa abajo.
- [x] **Los unit tests no tocan red ni BBDD.** Comprobado por construcción y de
      hecho: el DDL se compila contra `postgresql.dialect()` sin motor, el
      estado de la base entra como dato (`{tabla: {columnas}}`), las sesiones y
      el inspector son dobles, y las dos funciones impuras se ejercitan con
      `monkeypatch`. Los 63 pasan en 1,21 s sin PostgreSQL levantado.
- [x] **Las verificaciones `MANUAL (humano)` están listadas en
      `progress/current.md` con su comando exacto, pendientes de que el humano
      las ejecute.** **Corregido en `14423c0`** (2ª pasada). En la 1ª pasada T8
      no aparecía en ese fichero: los comandos existían y eran correctos, pero
      en `tasks.md` y en `progress/impl_F-003.md` §6, no donde C4 los exige.
      Ahora T8 abre `current.md` bajo un epígrafe destacado
      («⚠ VERIFICACIÓN MANUAL PENDIENTE (humano) · T8 — la importante»), con
      los cuatro comandos exactos, qué tiene que salir en cada paso y qué
      significa cada desviación posible. **Pendiente de ejecución del humano,
      que es exactamente el estado que este checkbox pide.**
      **Recordatorio de rigor `critico`:** la tabla de `CHECKPOINTS.md` exige
      además el **resultado real** anotado. Hasta que el humano ejecute T8 y lo
      escriba en `current.md`, F-003 **no pasa a `done`**. `current.md` lo dice
      con todas las letras: «El resultado real se anota aquí cuando lo
      ejecutes. Sin eso, F-003 no se cierra.»

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "critico"` en `harness/features.json`, valor
      válido.
- [x] **Fase RED.** `progress/impl_F-003.md` §2 trae la **salida real**, no una
      afirmación: el `ImportError: cannot import name 'esquema'`, el
      `41 failed, 2 passed, 20 errors in 5.07s`, y las trazas de los requisitos
      centrales una a una (`hasattr(AsignacionORM, 'sigrid_estado')` → `False`;
      `assert 1 == 0` de las aperturas de sesión; `assert 7 == 1`;
      `KeyError: 'sigrid_registrado_by'`). El `7 == 1` es especialmente buena
      evidencia: son las seis sentencias de `_ALTERS` más la de la traza, o sea
      **la avería medida**. Además explica por qué 2 tests ya pasaban en RED
      (guardias anti-regresión), que es justo lo que hay que explicar.
- [x] **Cobertura.** `[OK] PUERTA COBERTURA: 94.4% de 54 líneas cambiadas
      cubiertas (51/54, umbral 80%, nivel critico)`. Las 3 sin cubrir son de
      `main.py` (import, llamada y `logger.info`), imposibles de medir sin
      arrancar contra PostgreSQL; el wiring está sujeto por
      `test_f003_r4_main_sincroniza_el_esquema_al_arrancar` y se comprueba de
      verdad en T8. `esquema.py`, `orm_models.py` y `registro_sigrid.py` no
      tienen ninguna línea cambiada sin cubrir.
- [x] **Mutación con totales verificados de forma independiente.** Alcance (193
      líneas, 5 ficheros) y mutantes (14) **recalculados por mí** y coincidentes.
- [x] **Los muertos comprobados, no solo contados.** «Tiempo total» declarado
      31,4 s < 5 min ⇒ **campaña reejecutada** por el reviewer con `--salida`
      fuera de `progress/`: **14 evaluados, 14 muertos, 0 supervivientes, 0
      timeouts en 24,6 s**. Coincide con el informe. `git status` idéntico
      antes y después.
- [x] **Cero supervivientes** (exigencia de `critico`). Ninguna sección de
      análisis en `PENDIENTE`, porque no hay supervivientes que analizar. Los
      dos de la primera campaña se resolvieron **con tests nuevos**, no con
      justificación: la salida correcta.
- [x] **Sección «Evidencias»** presente en `impl_F-003.md` §5 con los cuatro
      números: tests (84 passed, 63 de F-003), cobertura (94,4 %, 51/54),
      mutantes/supervivientes (14/0) y tiempo de suite (2,28 s api; 24,6-31,4 s
      la campaña).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles

**N/A y sin nada que justificar:** no existe `harness/rutas_sensibles.json` en
el repositorio, que es el caso mayoritario previsto por el checkpoint.

### C5 — La sesión se cerró bien

- [x] **`tasks.md` y commits.** T1-T7 y T9 marcadas `[x]`, con **un commit por
      tarea** y el formato exacto `F-003 Tn: descripción` (`e8bd45e` T1 …
      `f83832d` T7). **T8 sigue `[ ]` y es correcto que lo siga**: es la
      verificación MANUAL que ejecuta el humano, y marcarla sería falsear el
      registro. No la cuento como trabajo faltante del implementer.
- [x] **Sin ficheros temporales ni artefactos sospechosos** atribuibles a la
      feature. Lo que hay en `git status` está identificado y **nada es del
      implementer**:
      - `.coverage`, `coverage.json` y sus gemelos en `services/dedicacion-api/`
        (4 ficheros modificados): los reescribe `init.sh`; artefactos de
        cobertura versionados, avería **F-009** del backlog.
      - `progress/explore_transfer_original.md` sin versionar: **es del líder**
        (informe de exploración del repositorio original) y se moverá a la rama
        de F-002. Por indicación expresa del encargo, **no cuenta como
        desviación de alcance**.
      - Barrí el diff buscando cualquier **otro** fichero ajeno y **no hay
        ninguno**: los 17 ficheros del diff son todos de F-003 o de su rastro
        documental.
- [x] **`features.json` refleja el estado real**: F-003 `in_progress`, que es
      exactamente lo que es (pendiente de este review y de T8).

**Tras la 2ª pasada: C1–C5 sin ningún checkbox vacío. C3 bis y C4 ter, N/A
justificados por escrito ⇒ APPROVED.**

---

## Trazabilidad: requisito → test que lo cubre

| Req. | Qué exige | Test |
|---|---|---|
| R1 | Las seis columnas en `AsignacionORM` | `test_f003_r1_la_columna_esta_declarada_en_el_orm` (×6) |
| R2 | Sin DDL a mano fuera del ORM | `test_f003_r2_el_registro_no_contiene_ddl_ni_sql_crudo` (×3: `ALTER TABLE`, `_ALTERS`, `text(`) |
| R3 | DDL **derivado** de los metadatos | `test_f003_r3_ddl_add_column_compila_una_columna` (×6), `..._arrastra_default_y_not_null`, `..._usa_el_compilador_de_sqlalchemy` |
| R4 | DDL en el arranque, no al construir | `test_f003_r4_construir_registro_sigrid_no_ejecuta_nada`, `..._main_sincroniza_el_esquema_al_arrancar`, `..._crea_tablas_antes_de_inspeccionar` |
| R5 | Tipos y nulabilidad exactos | `test_f003_r5_el_tipo_compilado_es_el_de_la_tabla` (×6), `..._la_columna_es_nulable_y_sin_default` (×6), `..._los_recortes_coinciden_con_las_longitudes_del_orm`, `..._el_parte_cod_no_se_trunca` |
| R6 | `datetime` con `tzinfo` en UTC | `test_f003_r6_la_marca_de_tiempo_lleva_zona_horaria` + aserción de `tzinfo`/`utcoffset` en la rama `escritas` |
| R7 | Usuario truncado a 64 | `test_f003_r7_el_usuario_se_trunca_a_64` (64/65/200), `..._usuario_vacio_no_revienta` |
| R8 | Base limpia: sin `ALTER` | `test_f003_r8_tabla_ausente_no_genera_ningun_alter`, `..._la_tabla_queda_con_las_previas_mas_las_seis`, `..._columnas_existentes_radiografia_la_base` |
| R9 | **Base ya al día: cero sentencias** | `test_f003_r9_base_al_dia_no_genera_ningun_alter`, `test_f003_r9_sincronizar_esquema_no_ejecuta_nada_si_no_falta_nada` |
| R10 | N faltantes ⇒ N sentencias | `test_f003_r10_se_emite_una_sentencia_por_columna_faltante` |
| R11 | Idempotencia | `test_f003_r11_aplicar_el_ddl_lo_deja_todo_al_dia` |
| R12 | `NOT NULL` sin default ⇒ aborta | `test_f003_r12_columna_not_null_sin_default_aborta`, `..._con_default_si_se_puede_anadir` |
| R13 | Solo añade columnas | `test_f003_r13_el_ddl_derivado_solo_anade_columnas`, `..._una_columna_sobrante_en_la_base_no_se_toca` |
| R14 | Misma semántica de traza | `test_f003_r14_*` (×8: las tres ramas, el `WHERE` de cada una, motivo a 300, sin motivo, las tres juntas, respuesta vacía) |
| R15 | Endpoints y mapeo sin cambios | **sin test con nombre trazable** — ver nota |
| R16 | `AsignacionORM(...)` sin las nuevas; sin `SELECT *` | `test_f003_r16_el_servicio_no_tiene_select_estrella` |
| R17 | DDL derivado ↔ columnas que la traza espera | `test_f003_r17_el_orm_tiene_exactamente_las_columnas_de_traza`, `..._la_traza_escribe_exactamente_esas_columnas`, `..._el_ddl_derivado_es_el_esperado_caracter_a_caracter` |
| R18 | Tests sin red ni PostgreSQL | meta-requisito: lo satisface la suite entera (63 tests en 1,21 s sin BBDD) |

**Nota sobre R15 — por qué NO lo cuento como checkbox vacío.** R15 es el único
requisito sin `test_f003_r15_*`, y quiero dejar escrito el razonamiento en vez
de que parezca un descuido mío:

1. **Está verificado, solo que por el diff en vez de por un test.** Lo comprobé
   yo: `schemas.py`, `repositories.py` y `routes.py` **no aparecen en
   `git diff dev..HEAD --name-only`**, y el único `sigrid_` que hay en
   `interface_adapters/` es `SigridApiClient` (un import) y
   `sigrid_configurado` (un flag de settings), ninguno de los dos relacionado
   con las columnas de traza. **Ninguna de las seis se expone.**
2. **La spec aprobada lo dejó fuera del plan de tests a propósito.** `design.md`
   §5 enumera las cuatro piezas de la suite y R15 no está en ninguna. Bloquear
   al implementer por una decisión del spec-author que el humano aprobó sería
   castigarle por cumplir el plan.

Es, aun así, una **recomendación** barata y en el estilo de la propia suite
(R2 y R16 ya son guardias por inspección del fuente). La dejo abajo como
mejora opcional, **no como cambio requerido**.

---

## Cambios requeridos en la 1ª pasada — ✅ AMBOS RESUELTOS en `14423c0`

> Se conservan tal como se pidieron, para que quede el rastro de qué se exigió
> y contra qué se comprobó la corrección. Ambos eran del **líder**; ninguno
> tocaba código, tests ni la spec, y el implementer no tuvo nada que rehacer.

1. **`progress/current.md` — reescribirlo para la sesión activa (C2).**
   Hoy dice, líneas 4-6: «**Ninguna feature en ejecución.** F-001 se cerró el
   2026-08-19 […] La siguiente tarea por prioridad es **F-002**». Es falso:
   F-003 está `in_progress` y su rama es la activa. Debe describir **solo** la
   sesión de F-003 (feature en curso, rama, qué se ha hecho, qué falta), sin
   restos de la sesión de F-001.
   Al reescribirlo, conviene **conservar** las dos notas del bloque «Lo que
   sabemos y no conviene volver a descubrir» que siguen vigentes y son útiles:
   que `ruff` no está en el venv del api, y que `init.sh` ensucia `git status`
   (F-009). La tercera («la puerta de cobertura sigue sin estrenarse con datos
   reales») **ya no es cierta**: F-003 la ha estrenado con 94,4 % de 54 líneas,
   y merece actualizarse en vez de borrarse.

2. **Listar T8 en `progress/current.md` con su comando exacto (C4).**
   No hay que redactarla de cero: los cuatro comandos están ya correctos y
   probados en `progress/impl_F-003.md` §6 —esa versión es mejor que la de
   `tasks.md` porque añade el recuento de filas a la fotografía previa—. Basta
   con traerlos a `current.md` bajo un epígrafe de verificaciones MANUAL
   pendientes, junto al resultado esperado:
   - pasos 1 y 4 devuelven **la misma lista de columnas y el mismo recuento de
     filas**;
   - los dos arranques registran
     `Esquema verificado en BBDD 'dedicacion': 0 sentencias DDL aplicadas`
     — **0 en ambos**; si el segundo no dijera 0, la idempotencia estaría rota
     y eso **sí** sería un fallo de esta feature;
   - ningún arranque debe emitir `EsquemaNoDerivable`.
   En nivel `critico` hay que **anotar después el resultado real** en ese mismo
   fichero. Hasta que el humano ejecute T8 y su resultado esté escrito, F-003
   **no puede pasar a `done`**.

Hecho esto, F-003 queda lista para APPROVED sin volver a tocar el código: mi
re-review se limitaría a releer `current.md` y el resultado de T8.

---

## Segunda pasada (commit `14423c0`)

Reviso **solo lo que cambió**: el commit toca dos ficheros
(`progress/current.md` y `progress/review_F-003.md`), ninguno de código, así
que las verificaciones de la 1ª pasada sobre el ORM, la traza, la mutación y el
`build_app` siguen siendo válidas y **no las repito**.

### 1. `progress/current.md` describe la sesión activa — ✅

Abre con F-003, su rama, `sdd: true`, rigor `critico` y el estado real
(«implementada (T1–T7, T9) y revisada. Falta la verificación MANUAL T8»). Trae
la tabla de las **nueve** tareas con su commit, y los siete commits que lista
(`e8bd45e`, `b4ff052`, `b3cfbc5`, `99a2206`, `a460214`, `4a27175`, `f83832d`)
**coinciden con el historial real** que verifiqué en la 1ª pasada. T8 figura
como `[ ]` y «del humano», que es lo correcto: marcarla sería falsear el
registro.

Las evidencias que cita son las **reales**, contrastadas contra mis propias
mediciones: 84 passed (63 de F-003 + 21 de F-001), cobertura 94,4 % (51/54),
14 mutantes / 14 muertos / 0 supervivientes, fase RED con 41 failed + 20
errors, ruff 164 → 162. **Ningún número inflado.**

Dos detalles que mejoran sobre lo que pedí: la nota de que la primera campaña
dejó 2 supervivientes reales y se mataron **con tests, no con justificación**
—que es la parte que un lector futuro debe saber—, y la «Nota de proceso» final
que convierte el fallo de esta review en una regla para la próxima sesión. Eso
es cerrar el bucle, no tapar el expediente.

### 2. T8 listada con su comando exacto — ✅

Va **la primera**, bajo un epígrafe imposible de pasar por alto, con los cuatro
comandos exactos (fotografía previa con recuento de filas, dos arranques,
fotografía posterior), el resultado esperado y **el significado de cada
desviación posible**: primer arranque con más de 0 sentencias, segundo distinto
de 0 («la idempotencia estaría rota y eso sí sería un fallo de esta feature»), y
`EsquemaNoDerivable`. Incluye T8 bis. Es más completo que lo que pedí.

### 3. Lo declarado como deliberado — comprobado y conforme

- **F-011 «pendiente de commitear en la rama de F-002»:** correcto y coherente.
  `harness/features.json` de **esta** rama no contiene F-011 y `git status` no
  lo muestra modificado, así que no hay nada a medias en la rama de F-003.
- **`progress/explore_transfer_original.md` sin versionar:** sigue siendo el
  único fichero sin trackear. Es del **líder**, va a la rama de F-002 y, por
  indicación expresa, **no cuenta como desviación de alcance**. Confirmo que no
  hay ningún **otro** fichero ajeno en el árbol ni en el diff.

### 4. Un susto en la puerta de cobertura: falso rojo, y merece quedar escrito

Al reejecutar `bash harness/init.sh` tras el commit del líder, la puerta salió
en **rojo**:

```
[KO] PUERTA COBERTURA: 0.0% de 61 líneas cambiadas cubiertas (0/61, umbral 80%, nivel critico)
1 comprobaciones fallidas. NO empieces a trabajar.
```

No aprobé sobre eso: lo diagnostiqué. **Es un falso negativo, y la causa es
F-009.** La cadena, comprobada paso a paso:

1. El árbol se limpió antes del commit, lo que **revirtió los artefactos de
   cobertura versionados** a su estado committeado, que es de la época de
   F-001.
2. La suite del api salió **de caché** («árbol sin cambios desde el último
   verde»), así que `services/dedicacion-api/coverage.json` **no se regeneró**.
3. La puerta juzgó las líneas de F-003 con datos de cobertura de F-001. Prueba
   directa, leyendo el fichero:

```
$ python -c "json.load(open('services/dedicacion-api/coverage.json'))"
ficheros en coverage.json del api: 6
   domain\estados.py, domain\models.py, tests\test_estados.py, ...
contiene esquema.py? -> False
timestamp: 2026-08-19T10:52:07
```

No conocía **ni uno** de los ficheros de F-003. De ahí el 0/61.

Forcé una medición real invalidando el marcador de caché —`.arnes_cache/` está
en `.gitignore`, es cache local puro, no contenido del repositorio— y la puerta
vuelve a su valor verdadero:

```
$ rm -f .arnes_cache/suite_api.ok && bash harness/init.sh
84 passed in 6.37s
[OK] servicio api (services/dedicacion-api): pytest en verde
[OK] PUERTA COBERTURA: 94.4% de 54 líneas cambiadas cubiertas (51/54, umbral 80%, nivel critico)
ENTORNO LISTO. Puedes trabajar.

$ bash harness/init.sh > /dev/null 2>&1; echo $?
0
```

**Exit code 0.** C1 se cumple, y el 94,4 % de la 1ª pasada era el dato bueno.

Esto no es un defecto de F-003 —el commit del líder solo tocó dos `.md`— pero
es un hallazgo que **agrava F-009** y conviene que no se pierda: hasta ahora
F-009 se describía como «ensucia `git status` y obliga a `--workers 1`». Aquí
ha hecho algo peor: **ha dado un veredicto falso sobre una puerta de rigor**.
Y la simetría es la que asusta: si puede dar un **falso rojo** con datos
rancios, puede dar un **falso verde** por el mismo camino —una feature cuyas
líneas nuevas coincidan con líneas ya cubiertas en una medición vieja—. Un
falso rojo se investiga; un falso verde se aprueba. Propuesta concreta en
«Automejora».

---

## Recomendaciones (no bloquean)

1. **Un guardia para R15**, en el estilo de los de R2/R16: afirmar que
   `interface_adapters/api/schemas.py` y el mapeo `_a_linea` de
   `repositories.py` no mencionan ninguna columna `sigrid_*`. Hoy es cierto y
   lo he verificado, pero nada impide que mañana alguien exponga la traza sin
   enterarse de que R15 lo prohibía.
2. **Corregir la aritmética de la spec.** `requirements.md` R8 y `design.md` §4
   dicen «dieciséis columnas» y «las diez actuales más las seis»; son **ocho**
   las previas y **catorce** el total. El implementer lo detectó, lo anotó en
   `COLUMNAS_PREVIAS` y en su informe §4.1, y no afecta al diseño. Merece la
   corrección en la spec para que no confunda al siguiente que la lea.
3. **Precisar la frase del lint** en `impl_F-003.md` §5: «los cinco ficheros de
   F-003 están limpios» vale para tres de los cinco. El dato global (164 → 162,
   cero deuda nueva) es correcto.
4. **Las decisiones D1-D5 siguen abiertas** y son del humano, no del arnés.
   Recuerdo las dos que más pican: **D1** (`sigrid_hmores_ide` en `INTEGER`
   mientras el resto de `ide` son `BigInteger`) y sobre todo **D4**, que no es
   una decisión de estilo sino una **avería real preexistente**:
   `PgAsignacionRepository.reemplazar()` borra y reinserta, así que editar el
   cuadrante después de registrar **vacía las seis columnas y cambia los `id`**,
   y con ellos la `synckey`. Está fuera del alcance de F-003, pero merece
   entrada propia en el backlog antes de que alguien confíe en la traza.

---

## Automejora del arnés (propuesta, no aplicada)

Someto una sola, nacida de este review, para que el humano decida:

**El protocolo del reviewer no dice qué hacer cuando el checkbox vacío es del
líder y no del implementer.** `CHECKPOINTS.md` evalúa el destino de la sesión
—correcto—, pero C2 y C4 dependen de `progress/current.md`, un fichero que
`tasks.md` **prohíbe expresamente** tocar al implementer. El resultado es que
un implementer impecable recibe un CHANGES_REQUESTED que no puede accionar, y
el veredicto binario no distingue «hay que reimplementar» de «al líder le falta
actualizar un fichero de sesión».

Propuesta mínima, sin romper el veredicto binario: que `.claude/agents/reviewer.md`
pida que el informe **atribuya cada cambio requerido a un rol** (implementer o
líder) y que, cuando **todos** los cambios requeridos sean del líder, lo diga en
una línea destacada al principio. Así el líder sabe que puede cerrarlos él mismo
en dos minutos sin relanzar al implementer. Si se acepta, vale para cualquier
proyecto ⇒ va a `arnes-base`.

---

## Qué no he verificado (dicho explícitamente)

- **T8 no la he ejecutado ni podía**: exige PostgreSQL con la base real y datos
  del humano. Es verificación MANUAL por diseño. He verificado que el
  **mecanismo** se comporta como debe con dobles de prueba y que los comandos
  que se le ofrecen al humano son correctos, pero **nadie ha arrancado esto
  contra la base real todavía**.
- **La traza de extremo a extremo tampoco**: comprobar que un registro real
  deja `sigrid_estado='registrado'` exigiría escribir en Sigrid vía
  `dedicacion-transfer`. Fuera de alcance y fuera de lo que ningún agente hace
  por su cuenta. Los `UPDATE` están verificados **compilados**, no ejecutados.
- **La suite del front** sigue sin existir (aviso preexistente de `init.sh`).
  No lo introduce ni lo agrava F-003.
- Ninguna comprobación quedó a medias por motivos técnicos: todas las que me
  propuse ejecutar se completaron.

---

**Veredicto final: APPROVED** (2ª pasada, sobre `14423c0`). Los dos puntos de
higiene de sesión de C2 y C4 —ambos del líder— quedaron corregidos en ese
commit. **El código, los tests, la cobertura, la campaña de mutación y el
diseño de F-003 estaban aprobados en sus méritos desde la primera pasada**: no
se encontró ni un defecto en la implementación.

**Condición para cerrar:** F-003 **no pasa a `done`** hasta que el humano
ejecute la verificación MANUAL **T8** contra su base real y anote el resultado
en `progress/current.md`. Lo exige el nivel `critico`.

> **Nota del líder (2026-08-19).** Este párrafo final se había quedado con el
> veredicto de la 1ª pasada: el agente reviewer actualizó la cabecera y la
> sección «Segunda pasada» a APPROVED, pero se cortó por un fallo técnico
> antes de rehacer el cierre. La corrección la ha hecho el líder para que el
> informe no se contradiga; el veredicto es el del reviewer, no del líder. El
> líder verificó además por su cuenta `bash harness/init.sh` → **exit 0,
> ENTORNO LISTO**, con 84 passed en el api y la puerta de cobertura al 94,4 %.
