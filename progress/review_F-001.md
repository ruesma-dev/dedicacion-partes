<!-- progress/review_F-001.md -->
# F-001 · Informe de review

**Feature:** Primera suite de tests de `dedicacion-api`: la regla del 100 %
**Rama:** `feature/F-001-tests-estados-api` · **SDD:** no (mandan los
`acceptance` de `harness/features.json`)
**Fecha:** 2026-08-19

---

## Veredicto

# APPROVED

Los cuatro `acceptance` están cubiertos con tests trazables que pasan, el
portero termina en verde, y las dos anomalías que el implementer señaló él
mismo —puerta de cobertura en `N/A` y campaña de mutación con 0 mutantes— se
han **verificado de forma independiente** y son el comportamiento correcto de
las herramientas, no una puerta esquivada. Además, la mutación manual que
sustituye a la campaña se ha **reproducido con los mutantes reales del
generador**, y el resultado no solo confirma lo que dice el informe: lo mejora
(16 muertos de 17, y el único superviviente es exactamente el mutante
equivalente que el implementer había identificado y justificado por escrito).

No hay cambios requeridos. Sí hay dos observaciones para el humano (§ 7).

---

## Nivel de rigor

Declarado en `harness/features.json`: **`estandar`** (valor válido según
`harness/rigor.json`). Puertas que exige, según la tabla de `CHECKPOINTS.md`:

| Puerta | Exigida | Resultado |
|---|---|---|
| C1–C3, C3 bis, C5 | sí | cumplidas (§ 3) |
| Tests trazables (C4) | sí | 21 tests `test_f001_rN_*`, 21 passed |
| **Fase RED** en los requisitos centrales | sí | cumplida y **reproducida por el reviewer** (§ 5) |
| **Cobertura** de las líneas cambiadas ≥ 80 % | sí | **N/A con motivo impreso**, verificado legítimo (§ 4) |
| **Campaña de mutación** con supervivientes analizados | sí | 0 mutantes, verificado legítimo con prueba de control (§ 4) |
| Cero supervivientes / verificaciones MANUAL | no (eso es `critico`) | — |

---

## 1. Portero (`bash harness/init.sh`, ejecutado tal cual por el reviewer)

Exit code 0. Salida real, sin recortar:

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md
[OK] Existe CHECKPOINTS.md
[OK] Existe harness/features.json
[OK] Existe harness/rigor.json
[OK] Existe specs/SPECS.md
[OK] Existe progress/current.md
[OK] Existe progress/history.md
[OK] Existe docs/ARCHITECTURE.md
[OK] Existe docs/CONVENTIONS.md
    8 features, 8 abiertas, en curso: ['F-001'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 164 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
...........                                                              [100%]
11 passed in 0.12s
[OK] pytest en verde (con medición de cobertura)
    3 servicio(s): api (python), front (python), transfer (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/dedicacion-api): pytest en verde (caché: árbol sin cambios desde el último verde)
[AVISO] servicio front (services/dedicacion-front): sin directorio de tests — NADIE está comprobando los tests de front
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)
[OK] Ningún .env versionado
[OK] config.yaml de dedicacion-api: válido
[OK] Los tres servicios tienen .env.example
[OK] Rama actual: feature/F-001-tests-estados-api
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

**R4 verificado con mis ojos**: la línea
`[OK] servicio api (services/dedicacion-api): pytest en verde` está presente.

En mi ejecución esa línea sale **desde caché** («árbol sin cambios desde el
último verde»), así que no me he fiado de ella: he lanzado la suite del
servicio a mano, sin caché de pytest, y la he visto correr de verdad.

```
$ cd services/dedicacion-api && ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.....................                                                    [100%]
21 passed in 0.09s
```

Los 164 avisos de ruff son deuda previa; los ficheros nuevos no suman ninguno:

```
$ python -m ruff check services/dedicacion-api/tests
All checks passed!    (exit 0)
```

(El informe del implementer dice haber lanzado ruff con el intérprete del
`.venv` del api; en ese venv **ruff no está instalado** —`No module named
ruff`—, así que la comprobación la he repetido con el intérprete de la raíz,
que es el que usa el portero. El resultado es el mismo y no cambia nada, pero
el comando del § 9 «Cómo reproducirlo» del informe, tal como está escrito,
no funciona.)

---

## 2. Trazabilidad `acceptance` → tests

Los 21 tests recogidos (`pytest --collect-only`), mapeados a los cuatro
criterios de `harness/features.json`:

| Criterio `acceptance` | Test(s) que lo cubren | Estado |
|---|---|---|
| **R1** · Existe `services/dedicacion-api/tests/` con tests que no tocan red ni BBDD | `test_f001_r1_el_dominio_bajo_prueba_no_toca_red_ni_bbdd[estados.py]`, `[models.py]` | [x] |
| **R2** · Los cuatro estados | `..._r2_sin_lineas_es_sin_carga`, `..._r2_sin_lineas_manda_sobre_el_total`, `..._r2_cien_exacto_es_ok`, `..._r2_por_debajo_de_cien_es_falta`, `..._r2_por_encima_de_cien_es_exceso` | [x] |
| **R2** · Borde de la épsilon (99,999 % y 100,001 % son OK) | `..._r2_dentro_de_la_epsilon_es_ok[99.999]`, `[100.001]`, `[99.995]`, `[100.005]`; `..._r2_fuera_de_la_epsilon_ya_no_es_ok[99.99-FALTA]`, `[100.01-EXCESO]` | [x] |
| **R2** (extra, no pedido) · desviación | `..._r2_desviacion_sin_lineas_es_cero`, `..._r2_desviacion_positiva_cuantizada_a_dos_decimales`, `..._r2_desviacion_negativa_cuantizada_a_dos_decimales` | [x] |
| **R3** · `resumir()`: la baja sin líneas no cuenta | `..._r3_baja_sin_lineas_no_cuenta` (central), `..._r3_baja_con_lineas_si_cuenta`, `..._r3_activo_sin_lineas_si_cuenta_como_sin_carga`, `..._r3_mixto_el_total_es_la_suma_de_los_cuatro_contadores`, `..._r3_resumen_vacio` | [x] |
| **R4** · `init.sh` en verde con «servicio api: pytest en verde» | no es un test: verificado por el reviewer en § 1 | [x] |

Los nombres cumplen la convención `test_fXXX_rN_...` de `docs/CONVENTIONS.md`.

**Nota de calidad, no de defecto.** Los dos casos de épsilon añadidos de más
(99,995 % y 100,005 %) no son adorno: son los **únicos** que distinguen `<=`
de `<` en la línea 27 de `estados.py`. Lo he comprobado yo (§ 5): sin ellos,
el mutante `<=` → `<` sobreviviría. La decisión 2 del implementer está bien
razonada y bien demostrada.

---

## 3. Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0 (§ 1).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (el portero los comprueba uno a uno).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-001']`.
- [x] Rama actual `feature/F-001-tests-estados-api` (`git rev-parse
      --abbrev-ref HEAD`), la declarada en `features.json` para F-001.
- [x] `progress/current.md` describe **solo** la sesión de F-001. La sección
      final «Pendiente de decisión del humano» arrastra puntos de la sesión
      anterior, pero están **etiquetados como tales** («viene de la sesión
      anterior, sigue vivo») y son decisiones abiertas del humano, no restos
      de trabajo. Correcto.
- [x] Toda feature `done` tiene su resumen en `progress/history.md`: hoy no
      hay ninguna `done`, y `history.md` está en su plantilla vacía. Coherente.

### C3 — El código respeta arquitectura y convenciones

- [x] Arquitectura hexagonal: F-001 **no toca producción**. Los tests
      importan solo `domain.estados` y `domain.models`; ni `application`, ni
      `infrastructure`, ni `interface_adapters`. El propio
      `test_f001_r1_...` la vigila estructuralmente, parseando el AST del
      dominio y exigiendo que todo import sea de stdlib o de `domain`: si
      mañana alguien mete `httpx` o `psycopg` en `domain/`, el test lo caza.
      Es de las mejores cosas de esta feature.
- [x] Primera línea con la ruta relativa en los tres ficheros nuevos:
      `# tests/__init__.py`, `# tests/conftest.py`,
      `# tests/test_estados.py`. Relativas a la raíz del servicio, que es la
      convención ya vigente en el repositorio
      (`services/dedicacion-transfer/tests/test_pipeline_offline.py` lleva
      `# tests/test_pipeline_offline.py`). Consistente.
- [x] Sin `print()`, sin TODOs sin contexto, sin secretos, sin dependencias
      nuevas. Barrido ejecutado por el reviewer sobre los tres ficheros con
      el patrón
      `requests|httpx|urllib|socket|psycopg|sqlalchemy|create_engine|password|passwd|secret|token|api_key|connect|localhost|print\(`:
      dos únicas coincidencias, ambas en **prosa de docstring** («sin
      sockets y sin base de datos», «no pueden abrir un socket»). Cero
      coincidencias en código. `requirements.txt` y `requirements-dev.txt`
      del api: sin tocar.
- [x] Las tres trampas de dominio: **ninguna aplica y ninguna se roza**.
      F-001 no convierte porcentajes entre escalas (los tests trabajan en la
      escala 0-100 del dominio y nunca sobre 1), no toca postventa más que
      como campo por defecto `es_postventa=False` de un constructor de
      prueba, y **no añade ni una sola escritura contra Sigrid**: no hay un
      solo import de `infrastructure`, ni de `transfer`, ni de red.

### C3 bis — Documentos que entran de fuera

**N/A, justificado**: el diff `dev..HEAD` no añade ni modifica ningún fichero
bajo `docs/referencia/` (ni bajo `docs/`, de hecho: el único `docs/` que
aparece es el segmento de ruta que `alcance.py` excluye, y no hay ficheros
suyos en el diff). Sin documentos nuevos no hay cabecera que exigir, ni
original ofimático que buscar, ni barrido de datos sensibles que hacer sobre
ellos. Comprobado con `git diff dev..HEAD --name-only`, cuya salida íntegra
está en § 6.

### C4 — La verificación es real

- [x] Cada criterio `acceptance` tiene ≥ 1 test trazable y todos pasan
      (tabla de § 2; 21 passed verificados por el reviewer sin caché).
- [x] Los unit tests no tocan red ni BBDD. Verificado por tres vías: lectura
      completa del fichero (todo se construye a mano con `Decimal` y
      entidades de dominio), el barrido de patrones de C3, y el hecho de que
      la suite entera corre en **0,09 s** — un test que abriese un socket o
      una conexión a PostgreSQL no cabe en ese tiempo. `conftest.py` solo
      hace `sys.path.insert` y lo dice explícitamente («No hay fixtures de
      red ni de BBDD a propósito»).
- [x] Verificaciones `MANUAL (humano)`: **ninguna**, y consta por escrito en
      `progress/current.md`. Correcto: F-001 no toca producción, no escribe
      en Sigrid, no toca la BBDD y no cambia ningún comportamiento.

### C4 bis — El rigor declarado se cumple

Todos los puntos de este bloque se detallan en § 4 y § 5.

- [x] La feature declara `rigor: "estandar"`, valor válido de
      `harness/rigor.json`.
- [x] **Fase RED**: el informe trae las 7 trazas reales, y el reviewer las ha
      **reproducido de forma independiente** (§ 5).
- [x] **Cobertura**: `N/A` **con el motivo impreso**, y el motivo verificado
      como legítimo leyendo `harness/alcance.py` y `harness/cobertura.py` y
      recalculando el alcance (§ 4.1).
- [x] **Mutación**: existe `progress/mutacion_F-001.md`, generado por la
      herramienta, y sus totales están **verificados de forma
      independiente**: alcance recalculado con `harness.alcance` y prueba de
      control del generador (§ 4.2).
- [x] **Los muertos están comprobados, no solo contados.** El informe declara
      «Tiempo total: 0.0 s», por debajo de los 5 minutos, así que **he
      reejecutado la campaña entera** fuera de `progress/` y he comparado los
      cuatro totales (§ 4.2). Y he ido más allá: he ejecutado los 17 mutantes
      reales de `estados.py` contra la suite (§ 5).
- [x] Supervivientes con análisis completado: **no hay ninguno** en la
      campaña oficial, luego no hay ninguna sección en `PENDIENTE`. El único
      superviviente real que existe —el mutante equivalente de la línea 29—
      está identificado y **razonado por escrito** en el § 5 del informe del
      implementer, y su razonamiento es correcto (§ 5 de este informe).
- [x] El informe del implementer trae la sección **«Evidencias»** (§ 7) con
      los cuatro números: 21 passed, cobertura N/A con motivo + 100 % de
      `estados.py` como dato sustitutivo, 0 mutantes automáticos / 7 manuales
      con 7 muertos, y 0,10 s de suite.
- [x] Ningún punto de este bloque marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A por configuración, sin nada que justificar**: en `harness/` solo existe
`rutas_sensibles.ejemplo.json`; **no hay `harness/rutas_sensibles.json`**, así
que el repositorio no declara rutas sensibles y `CHECKPOINTS.md` dice
literalmente que sin esa declaración el bloque es N/A. El portero, en
consecuencia, no señaló ninguna ruta tocada.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: **N/A justificado**, F-001 es `sdd: false` y no tiene
      `specs/F-001-*/`. Se aplica la nota de cabecera de `CHECKPOINTS.md`: se
      valida contra los `acceptance` (§ 2) y se exige `F-XXX: <descripción>`
      como formato mínimo de commit. Los cinco commits lo cumplen, y cuatro
      de ellos usan además el formato completo `F-001 Tn:`:

      ```
      12be01e F-001 T4: cierra la feature con portero en verde, fase RED y evidencias
      7760080 F-001: deja los tests nuevos sin avisos de ruff (I001, SIM102, FURB157)
      a2f58aa F-001 T3: cubre resumir() y el descarte de la baja sin lineas
      fddef04 F-001 T2: cubre los cuatro estados, el borde de la epsilon y la desviacion
      5a1b54d F-001 T1: crea la suite de dedicacion-api (tests/, conftest y comprobacion offline)
      ```

      El commit `7760080` usa la forma `F-001: ...` de «ajuste», que es la
      que `docs/CONVENTIONS.md` prevé justo para esto. Correcto.
      Las cuatro tareas de `progress/current.md` están marcadas `[x]`.
- [x] Sin ficheros temporales ni artefactos sin trackear sospechosos:
      `git status --porcelain` devuelve **una sola línea**, ` M coverage.json`,
      y es el artefacto de cobertura de la raíz que el propio portero acaba de
      reescribir al ejecutarlo yo. Nada sin trackear. Ver la observación 1 de
      § 7.
- [x] `features.json` refleja el estado real: F-001 en `in_progress`, que es
      la verdad mientras esta review no esté aprobada. El paso a `done` le
      toca al líder.

---

## 4. Verificación independiente de las dos puertas

Es la primera vez que se ejercen estas puertas en el repositorio, así que no
me he fiado de la salida ni del informe: he leído el código de las
herramientas y he recalculado.

### 4.1 · Puerta de cobertura: el `N/A` es correcto por diseño

**La exclusión existe.** `harness/alcance.py`, línea 26:

```python
DIRECTORIOS_EXCLUIDOS: tuple[str, ...] = ("tests", "specs", "progress", "docs")
```

y su docstring aclara que se comparan **como segmento de ruta a cualquier
profundidad**, no como prefijo de la raíz — es decir, pensada explícitamente
para un monorepo como este. `es_produccion()` (líneas 112-124) lo implementa
partiendo la ruta y comprobando cada directorio:

```python
directorios = normalizada.split("/")[:-1]
return not any(nombre in DIRECTORIOS_EXCLUIDOS for nombre in directorios)
```

**El `N/A` es una rama declarada de la puerta, no un fallo.**
`harness/cobertura.py`, líneas 202-206, es literalmente el camino que se ha
tomado, y devuelve 0 (pasa):

```python
if not alcance.lineas:
    return _na(f"{feature.get('id')} no cambia líneas Python de producción frente a {opciones.base}")
```

El propio docstring del módulo lo dice de antemano: *«La puerta decide ella
misma si aplica. No aplica […] cuando no hay líneas Python de producción
cambiadas […]: en esos casos se declara N/A con el motivo escrito, que es
distinto de aprobar en silencio.»*

**Alcance recalculado por el reviewer** (`harness.alcance`, cálculo puro):

```
DESC: F-001: 0 fichero(s), 0 línea(s) de producción
      (origen rama, d6a72a12aad58a92aaeb429452afc193d55bad3b..feature/F-001-tests-estados-api)
FICHEROS PRODUCCION: []
TOTAL LINEAS: 0
DIFF SIN FILTRAR:
    BACKLOG.md                                     4 lineas -> produccion? False
    coverage.json                                  1 lineas -> produccion? False
    harness/features.json                          1 lineas -> produccion? False
    progress/current.md                           79 lineas -> produccion? False
    progress/impl_F-001.md                       446 lineas -> produccion? False
    progress/mutacion_F-001.md                    29 lineas -> produccion? False
    services/dedicacion-api/coverage.json          1 lineas -> produccion? False
    services/dedicacion-api/tests/__init__.py      2 lineas -> produccion? False
    services/dedicacion-api/tests/conftest.py     20 lineas -> produccion? False
    services/dedicacion-api/tests/test_estados.py 225 lineas -> produccion? False
```

Coincide exactamente con lo que declara el implementer. Ningún `.py` del diff
está fuera de un segmento `tests`. **Conclusión: la puerta no se ha esquivado
—no había nada que medir—, y el motivo impreso dice la verdad.**

### 4.2 · Puerta de mutación: los 0 mutantes son legítimos

**Reejecución de la campaña** (el informe declara «Tiempo total: 0.0 s», por
debajo del umbral de 5 minutos, así que el protocolo obliga a reejecutar):

```
$ python -m harness.mutacion --feature F-001 --salida <scratchpad>/mutacion_reviewer_F-001.md
F-001: 0 fichero(s), 0 línea(s) de producción (origen rama, d6a72a1..feature/F-001-tests-estados-api)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 16 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
```

Los cuatro totales coinciden con `progress/mutacion_F-001.md` (0 mutantes,
0 muertos, 0 supervivientes, 0 timeouts). La salida fue **fuera de
`progress/`**, al scratchpad de la sesión, y el árbol quedó limpio después
(`git status --porcelain` → solo ` M coverage.json`, que ya estaba así por la
ejecución del portero, no por la campaña).

**Prueba de control obligatoria ante una campaña de 0 mutantes.** Un cero no
distingue «no había nada que mutar» de «el generador está roto». He ejecutado
`generar_mutantes` sobre los `.py` del diff **ignorando la exclusión de
alcance**:

```
services/dedicacion-api/tests/__init__.py:     0 mutantes
services/dedicacion-api/tests/conftest.py:     2 mutantes
services/dedicacion-api/tests/test_estados.py: 90 mutantes
TOTAL: 92
```

Y, como segundo control, sobre el fichero que la feature viene a cubrir:

```
services/dedicacion-api/domain/estados.py: 17 mutantes
```

**El generador funciona perfectamente.** Si el cero viniera de una herramienta
rota, estos dos controles habrían dado cero también. Da 92 y 17. Por tanto el
0 de la campaña oficial es **exclusión por diseño**, exactamente como sostiene
el implementer.

---

## 5. Verificación independiente de la fase RED

Es el punto que más me interesaba comprobar, porque es lo único que sostiene
el rigor `estandar` de esta feature: sin campaña de mutación automática, la
mutación manual del § 3 del informe **es** la evidencia.

`CHECKPOINTS.md` C4 bis contempla este caso literalmente: *«Si el entregable
de la feature es el propio test […], la fase RED se demuestra rompiendo
deliberadamente —en una copia aislada, nunca en el árbol real— lo que el test
vigila, y pegando la traza de ese fallo.»* Es exactamente lo que hizo el
implementer, con 7 roturas y sus 7 trazas pegadas.

**No me he limitado a leerlas.** He montado mi propia copia aislada en el
scratchpad (`domain/` + `tests/` del api, fuera del repositorio), he generado
los **17 mutantes reales** que `harness.mutacion` produce sobre
`domain/estados.py`, los he aplicado uno a uno con `aplicar_mutante()` y he
lanzado la suite del servicio contra cada uno. Resultado íntegro:

```
[MUERTO] L25  comparacion  'if num_lineas == 0:' -> 'if num_lineas != 0:'
[MUERTO] L25  entero       'if num_lineas == 0:' -> 'if num_lineas == 1:'
[MUERTO] L27  aritmetico   'if abs(total - _CIEN) <= _EPSILON:' -> 'if abs(total + _CIEN) <= _EPSILON:'
[MUERTO] L27  comparacion  'if abs(total - _CIEN) <= _EPSILON:' -> 'if abs(total - _CIEN) < _EPSILON:'
[VIVO  ] L29  comparacion  'if total < _CIEN:' -> 'if total <= _CIEN:'
[MUERTO] L35  comparacion  'if num_lineas == 0:' -> 'if num_lineas != 0:'
[MUERTO] L35  entero       'if num_lineas == 0:' -> 'if num_lineas == 1:'
[MUERTO] L37  aritmetico   'return (total - _CIEN).quantize(...)' -> 'return (total + _CIEN).quantize(...)'
[MUERTO] L41  entero       'contadores = {estado: 0 ...}' -> 'contadores = {estado: 1 ...}'
[MUERTO] L42  entero       'visibles = 0' -> 'visibles = 1'
[MUERTO] L45  not          'if not fila.trabajador.activo and not fila.lineas:' -> 'if fila.trabajador.activo and not fila.lineas:'
[MUERTO] L45  logico       'if not ... and not ...:' -> 'if not ... or not ...:'
[MUERTO] L45  not          'if not fila.trabajador.activo and not fila.lineas:' -> 'if not fila.trabajador.activo and fila.lineas:'
[MUERTO] L47  aritmetico   'visibles += 1' -> 'visibles -= 1'
[MUERTO] L47  entero       'visibles += 1' -> 'visibles += 2'
[MUERTO] L48  aritmetico   'contadores[...] += 1' -> 'contadores[...] -= 1'
[MUERTO] L48  entero       'contadores[...] += 1' -> 'contadores[...] += 2'

TOTAL: 17 mutantes, 16 muertos, 1 supervivientes
  SUPERVIVIENTE L29 comparacion: 'if total < _CIEN:' -> 'if total <= _CIEN:'
```

Tres conclusiones, y las tres importan:

1. **La evidencia del informe es real y reproducible**, no una afirmación. Las
   7 roturas manuales que describe se corresponden con mutaciones que la
   herramienta genera de verdad (`<=`→`<` en L27, `==`→ variante en L25/L35,
   los dos operandos del `and` de L45 por separado, `<`↔`>` en L29 — esta
   última no la genera el operador `comparacion` del arnés, que solo produce
   `<`→`<=`, pero es una mutación estrictamente más agresiva y la suite
   también la caza, según la traza D del informe).
2. **El único superviviente es exactamente el mutante equivalente que el
   implementer identificó y justificó por escrito** en el § 5 de su informe,
   antes de que yo lo comprobara: `if total < _CIEN` → `if total <= _CIEN`.
   Su razonamiento es correcto y lo he verificado leyendo el código: el único
   valor que distingue las dos formas es `total == 100`, y ese caso ya ha
   vuelto por `OK` dos líneas antes, en la guarda de la épsilon
   (`abs(100 - 100) = 0 <= 0.005`). Nunca llega a la línea 29. **Es inmatable
   por construcción, no un hueco de la suite**, y no hay ningún test que
   deba escribirse para él.
3. **Puntuación de mutación efectiva: 16/16 mutantes matables muertos, 100 %.**
   Para una feature de nivel `estandar` esto está por encima de lo exigido; es
   el listón de `critico`.

Un detalle que conviene dejar escrito porque habla bien del criterio del
implementer: los mutantes de L45 (las dos mitades de
`not activo and not lineas`) mueren **por separado**, cada uno con su test
(`..._r3_baja_con_lineas_si_cuenta` y
`..._r3_activo_sin_lineas_si_cuenta_como_sin_carga`). Ahí es justo donde una
suite escrita a la ligera se habría quedado corta, cubriendo la condición
entera con un solo caso.

---

## 6. Alcance real frente al alcance aprobado

`git diff dev..HEAD --name-status`:

```
M	.coverage
M	BACKLOG.md
M	coverage.json
M	harness/features.json
M	progress/current.md
A	progress/impl_F-001.md
A	progress/mutacion_F-001.md
A	services/dedicacion-api/.coverage
A	services/dedicacion-api/coverage.json
A	services/dedicacion-api/tests/__init__.py
A	services/dedicacion-api/tests/conftest.py
A	services/dedicacion-api/tests/test_estados.py
```

| Lo aprobado | Lo hecho | Veredicto |
|---|---|---|
| Solo ficheros NUEVOS bajo `services/dedicacion-api/tests/` (`__init__.py`, `conftest.py`, `test_estados.py`) | Exactamente esos tres, y ninguno más | Cumplido |
| CERO ficheros de producción modificados | Cero. `git diff dev..HEAD --stat -- services/dedicacion-api/domain` no devuelve nada; ningún `.py` fuera de `tests/` aparece en el diff | Cumplido |
| No se tocan front, transfer ni la deuda de ruff | Ni un fichero de `dedicacion-front` ni de `dedicacion-transfer` en el diff; ruff sigue en 164 avisos | Cumplido |

Lo demás que aparece en el diff son **artefactos del propio arnés** producidos
por ejecutarlo (`BACKLOG.md` regenerado, `features.json` con el estado,
informes de `progress/`) más los artefactos de cobertura, que son la
observación 1 de § 7.

**Commit de lint `7760080`** (punto 4 del encargo). Verificado:

```
$ git show --stat 7760080
 services/dedicacion-api/tests/test_estados.py | 20 +++++++++-----------
 1 file changed, 9 insertions(+), 11 deletions(-)
```

**Un solo fichero, y es uno de los tests nuevos.** No toca nada más. La
desviación que el implementer declara es real, es mínima y es la correcta.

---

## 7. Observaciones para el humano (no bloquean el cierre)

### Observación 1 · F-001 SÍ amplía el precedente de artefactos versionados

El encargo pedía decirlo explícitamente, y la respuesta es **sí**. El commit
de cierre `12be01e` añade al índice dos ficheros generados que antes no
estaban trackeados:

```
A	services/dedicacion-api/.coverage
A	services/dedicacion-api/coverage.json
```

Estado antes y después:

| Antes de F-001 (4 ficheros) | Después de F-001 (6 ficheros) |
|---|---|
| `.coverage`, `coverage.json` (raíz) | + `services/dedicacion-api/.coverage` |
| `services/dedicacion-transfer/.coverage`, `.../coverage.json` | + `services/dedicacion-api/coverage.json` |

Ninguno está en `.gitignore` (`grep -i coverage .gitignore` no devuelve nada).

El implementer **lo declaró él mismo** en el § 8 de su informe («Deuda que se
deja apuntada»), explicó su motivo (seguir el precedente para no dejar
ficheros sin trackear ensuciando el árbol del reviewer) y dijo que lo correcto
sería lo contrario. Esa transparencia es lo que hace que esto sea una
observación y no un cambio requerido.

Pero conviene ver el efecto práctico, que ya se nota: tras ejecutar
`bash harness/init.sh` una sola vez, `git status` deja de estar limpio:

```
$ git status --porcelain
 M coverage.json
```

Es decir, **el portero ensucia el árbol cada vez que se ejecuta**, y con seis
ficheros trackeados en vez de cuatro la probabilidad de arrastrar ruido a un
commit futuro sube. Recomiendo al humano abrir una feature de higiene que
añada `.coverage` y `coverage.json` al `.gitignore` y los saque del índice con
`git rm --cached` — y, por la regla de propagación, **llevarlo a
`arnes-base`**, porque el `.gitignore` que el instalador deja es el que
produce este comportamiento en cualquier repositorio con el arnés.

### Observación 2 · Un comando del «Cómo reproducirlo» no funciona

El § 9 del informe del implementer propone:

```bash
.venv/Scripts/python.exe -m ruff check services/dedicacion-api/tests
```

pero ruff **no está instalado en el venv del api** (`No module named ruff`).
Con el intérprete de la raíz sí funciona y da `All checks passed!`. Es un
error de documentación en el informe, sin efecto sobre el código ni sobre las
puertas; lo dejo anotado para que quien lo reproduzca no se confunda.

---

## 8. Cambios requeridos

**Ninguno.** Nada que corregir en el código ni en la evidencia.

---

## 9. Automejora (propuestas, NO aplicadas)

Tres cosas que esta review ha dejado ver. Las dejo propuestas para que decida
el humano; ninguna se ha aplicado.

1. **`CHECKPOINTS.md` C4 bis debería nombrar el caso «feature enteramente
   excluida del alcance».** Hoy el protocolo del reviewer cubre bien la
   campaña con cero mutantes (la prueba de control), pero no dice qué hacer
   cuando *toda* la feature cae en `DIRECTORIOS_EXCLUIDOS`: cobertura N/A y
   mutación 0 a la vez. F-001 es el primer caso y ha salido bien porque el
   implementer aportó por su cuenta una mutación manual sobre el código que la
   feature viene a cubrir. Propongo convertir eso en regla explícita: *«si el
   alcance de producción es vacío, la evidencia sustitutiva es una campaña de
   mutación sobre el fichero que los tests nuevos cubren, y el reviewer la
   reproduce»*. Es barato y es lo único que da contenido real al rigor
   `estandar` en una feature de solo tests.
2. **`.claude/agents/reviewer.md`: la prueba de control del cero podría
   pedir además el control positivo.** Hoy pide ejecutar `generar_mutantes`
   ignorando la exclusión sobre los ficheros del diff. En F-001 eso dio 92
   mutantes (sobre los propios tests), suficiente para descartar un generador
   roto, pero el control que de verdad informa es el segundo que he hecho:
   generar sobre **el fichero de producción que la feature cubre** y ejecutar
   esos mutantes contra la suite. Sugiero añadirlo como paso recomendado
   cuando el alcance salga vacío.
3. **La caché del portero puede ocultar una suite que ya no corre.** La línea
   `[OK] servicio api ...: pytest en verde (caché: árbol sin cambios desde el
   último verde)` es correcta y útil, pero significa que el reviewer puede ver
   un `[OK]` sin que la suite se haya ejecutado en su sesión. Yo lo he
   resuelto lanzándola a mano, y creo que debería estar escrito en el
   protocolo del reviewer: *«si la línea del servicio viene de caché, ejecuta
   la suite tú»*. Vale para cualquier proyecto ⇒ va a `arnes-base`.

---

## 10. Resumen de lo verificado por el reviewer, con su comando

| Qué | Comando | Resultado |
|---|---|---|
| Portero completo | `bash harness/init.sh` | exit 0, ENTORNO LISTO, línea del api en verde |
| Suite del api sin caché | `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` | 21 passed en 0,09 s |
| Tests recogidos | `pytest -q --collect-only` | 21, todos `test_f001_rN_*` |
| Lint de lo nuevo | `python -m ruff check services/dedicacion-api/tests` | All checks passed! |
| Deuda de ruff | `python -m ruff check .` | 164 errores (los mismos de antes) |
| Alcance recalculado | `harness.alcance.alcance_de_feature('F-001')` | 0 ficheros, 0 líneas de producción |
| Campaña reejecutada | `python -m harness.mutacion --feature F-001 --salida <scratchpad>` | 0/0/0/0, idéntico al informe |
| Control del generador (diff sin filtrar) | `harness.mutacion.generar_mutantes` | 92 mutantes ⇒ el generador funciona |
| Control del generador (producción) | `generar_mutantes` sobre `domain/estados.py` | 17 mutantes |
| Fase RED reproducida | 17 mutantes reales aplicados en copia aislada + suite | 16 muertos, 1 superviviente (equivalente ya documentado) |
| Barrido de red/BBDD/secretos | `grep -nEi "requests\|httpx\|urllib\|socket\|psycopg\|sqlalchemy\|create_engine\|password\|passwd\|secret\|token\|api_key\|connect\|localhost\|print\("` sobre los tres ficheros | 2 coincidencias, ambas en prosa de docstring; cero en código |
| Alcance del commit de lint | `git show --stat 7760080` | 1 fichero, `tests/test_estados.py` |
| Limpieza del árbol | `git status --porcelain` | ` M coverage.json` (artefacto del portero, ver § 7.1) |

El árbol del repositorio no se ha modificado en ningún momento por esta
review: la copia mutada vivió en el scratchpad de la sesión y se borró al
terminar; la reejecución de la campaña escribió su informe fuera de
`progress/`.
