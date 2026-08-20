<!-- progress/review_F-002_cierre.md -->
# F-002 · Review de CIERRE

**Veredicto: CHANGES_REQUESTED**

> No se rechaza el código. El código de F-002 está **bien y sigue vivo**: sus
> 184 tests pasan sobre el árbol actual, ya con F-013 mergeado encima, y las
> dos reviews previas (`review_F-002_fase1.md`, `review_F-002_fase2.md`)
> siguen siendo válidas y no se han revuelto.
>
> Se rechaza el **cierre** por una sola clase de motivo: **el rastro
> documental no dice la verdad**. `tasks.md` afirma que T13 y T14 están
> pendientes cuando se ejecutaron ayer —incluida la primera escritura real de
> este sistema en un ERP de producción—, no dice que T6 se haya movido a
> F-014, y el volcado de T13 que la propia tarea exige no existe en ningún
> sitio. Son cuatro correcciones de documento, ninguna de código.

- **Fecha:** 2026-08-20
- **Revisor:** subagente `reviewer`
- **Rama evaluada:** `dev` (`392ed0a`), que ya contiene F-002, F-013 y F-008
- **Alcance:** cierre de la feature completa, no re-review del código

> **Nota sobre el árbol.** El encargo decía que la rama activa era
> `feature/F-013-linea-sin-partida-confirma`. No lo era: al empezar, el
> repositorio estaba en `dev` **con un merge de F-013 a medias y cuatro
> ficheros en conflicto** (`BACKLOG.md`, `harness/features.json`,
> `progress/current.md`, `progress/history.md`), y `harness/init.sh` en rojo
> con 3 fallos. Durante la review el líder terminó ese merge (`4af48e0`) y
> encadenó el de F-008 (`392ed0a`). **Las conclusiones de abajo están tomadas
> sobre el árbol final, limpio y en verde**, y se han vuelto a comprobar
> después de que dejara de moverse. Se deja constancia porque revisar sobre
> un árbol que cambia bajo los pies no es una situación sana y conviene que
> no se repita.

---

## 1 · Nivel de rigor y puertas que exige

`harness/features.json` declara para F-002: `"rigor": "critico"`, `sdd: true`,
`status: in_progress`, prioridad 2.

Nivel **crítico** ⇒ exige C1–C3, C3 bis, C5, más tests trazables (C4), **fase
RED**, **cobertura** de las líneas cambiadas, **campaña de mutación con cero
supervivientes** salvo justificación escrita aceptada por el humano, y las
verificaciones **`MANUAL (humano)` listadas con su comando exacto y su
resultado real**.

**Las puertas de C4 bis (RED, cobertura, mutación) no se reabren aquí.** Las
verificaron y aprobaron `review_F-002_fase1.md` (T1–T5) y
`review_F-002_fase2.md` (T7–T12, T15–T17), incluido el recálculo
independiente de la campaña de mutación y la aceptación del único
superviviente equivalente. Esta review de cierre **hereda** ese veredicto y
se ocupa solo de lo que queda abierto.

Lo que sí es competencia de esta review, y es donde falla, es la última línea
del nivel crítico: **las verificaciones `MANUAL (humano)` con su resultado
real**. T13 y T14 se ejecutaron; el documento que debe recogerlas no lo hace.

---

## 2 · Verificación punto por punto del encargo

### 2.1 · `tasks.md` NO refleja la realidad — **FALLA**

`specs/F-002-reglas-postventa-conflicto/tasks.md` está **sin modificar desde
la Fase 2** (`git status` limpio sobre él). Estado que declara frente a la
realidad del 2026-08-20:

| Tarea | `tasks.md` dice | Realidad | ¿Cuadra? |
|---|---|---|---|
| T1–T5 | `[x]` | hechas y aprobadas (Fase 1) | sí |
| **T6** | **`[ ]`** línea 77 | **movida a F-014** por decisión del humano | **NO** |
| T7–T12 | `[x]` | hechas y aprobadas (Fase 2) | sí |
| **T13** | **`[ ]`** línea 233 | **ejecutada** el 2026-08-20 (preflight real de julio) | **NO** |
| **T14** | **`[ ]`** línea 248 | **ejecutada** el 2026-08-20 (`hmores.ide = 403039`) | **NO** |
| T15–T17 | `[x]` | hechas y aprobadas (Fase 2) | sí |

Y además, tres textos que ahora son falsos:

1. **Cabecera, líneas 8–14.** «Lo único que sigue exigiendo al humano son las
   verificaciones marcadas **MANUAL (humano)** (T6, T13, T14).» De esas tres,
   dos están hechas y la tercera se fue a otra feature. Quien lea la spec
   dentro de seis meses concluirá que F-002 se cerró sin verificación real
   contra Sigrid, que es justo lo contrario de lo que pasó.
2. **T14, líneas 248–259.** La tarea incluye la limpieza
   (`prueba_escritura_porcentajes.py limpiar --confirmar`) como parte de sí
   misma. La escritura se hizo; **la limpieza no**, deliberadamente, porque el
   humano quiere ver la fila en la pantalla del ERP, y por eso se movió a
   F-014. Marcar T14 `[x]` sin decir esto dejaría enterrada una fila viva en
   producción. Hay que marcarla y **acotar qué parte se hizo**.
3. **T13 y T14 dicen `--ano 2026 --mes 8`.** Lo que se ejecutó fue **julio**
   (`--mes 7`): así consta en `progress/sigrid_F-002.md` §T14 (`fec=20260731`)
   y en el comando de limpieza que hereda F-014 (`--mes 7`). El comando
   escrito en la spec no reproduce lo que se hizo.

C5 exige `tasks.md` con **todas** las tareas `[x]`. Hoy hay tres `[ ]`, y dos
de ellas están hechas de verdad. Esto solo es checkbox vacío: **es un checkbox
vacío que además miente en la dirección peligrosa** (dice «no verificado» de
algo que sí se verificó, y «pendiente» de una limpieza que efectivamente sigue
pendiente pero en otra feature).

### 2.2 · `progress/sigrid_F-002.md` documenta T14 pero **NO T13** — **FALLA**

El documento tiene hoy tres secciones: `C2`, `C6` y **`T14 · La primera
escritura real de este sistema en Sigrid`**.

**T14 está bien documentada y es reproducible.** La sección trae la
autorización expresa, el alcance mínimo y por qué se eligió esa línea
(la obra origen **es** la obra de pruebas, así que la partida casada le
pertenece de verdad y el modo pruebas no falsea el resultado), la respuesta
del servicio y —lo que le da valor— una **verificación independiente leyendo
Sigrid**, no fiándose de lo que contestó el transfer:

```
ide=403039  hmoide=2820419  parte=PT26/00296  reside=1140343
fec=20260731  can=0.5  pre=4500.0  tot=2250.0  paride=94178 (CI.1.8)
hora=MCAP  tex='PRUEBA-PORC'  synckey='porcentajes:77'
```

Trae además las dos secciones que más se agradecen: **qué queda demostrado**
(`sql/write` habilitado, `ortide = 0` y `caaide = 0` aceptados, creación del
parte, mapeo al último día del mes) y **qué NO** (la imputación a partidas en
producción, que Sigrid lo pinte bien, y el comportamiento con conflictos, que
en esta prueba eran 0). Eso es honesto y es exactamente lo que hay que
escribir. **Sin objeciones a T14.**

**T13, en cambio, no está.** `grep -n "T13\|preflight" progress/sigrid_F-002.md`
no devuelve nada. Y `tasks.md` T13 pide literalmente «**Volcado a
`progress/sigrid_F-002.md`**».

Lo que existe del preflight de julio está **disperso y de segunda mano**,
siempre citado como justificación de otra cosa (la Regla C de F-013), nunca
como el volcado de la verificación:

- `docs/ARCHITECTURE.md:278-282` — el caso de la jefa de obra, `2.132,28 €`,
  `can = 0,385`, como procedencia de `#regla-sin-partida`.
- `progress/history.md:270-272` — el mismo caso, con el nombre (Arriaza
  García).
- `BACKLOG.md` / `harness/features.json` — dentro de la descripción de F-013.
- `progress/review_F-013.md:384` — citado por la review de F-013.

**Ninguno responde lo que T13 iba a comprobar**, que no era el caso de la
jefa de obra sino otra cosa: que **la partida resuelta es una hoja**, y que si
el trabajador ya tiene líneas `M*` en el parte **el conflicto de sobrecarga
aparece con sus cifras**. Es decir, la validación en real de las Reglas A, B y
P5 que F-002 acababa de escribir. Ese resultado no consta en ningún sitio.

Tampoco constan las cifras que el propio encargo de esta review da por
registradas: «13 obras, 4 líneas a escribir, 0 conflictos». No aparecen en el
árbol (`grep` sobre todos los `.md`).

> **Dónde estuvo.** El commit `01bf62a` («F-008: arranca la feature; T14
> ejecutada y su evidencia registrada»), de la rama
> `feature/F-008-infra-azure`, añadió a `progress/current.md` una sección
> titulada **«Lo que enseñó el preflight real de julio 2026 (T13)»**. Al
> resolver el merge de F-008 y reescribir `current.md`, **esa sección se
> perdió**. La de T14 sobrevivió porque iba en `sigrid_F-002.md`, que es
> donde le tocaba. Es un argumento a favor de la regla que ya está escrita en
> `tasks.md`: la evidencia contra Sigrid va a `sigrid_F-002.md`, no a
> `current.md`, que es un documento de sesión y se reescribe.

### 2.3 · La regla de F-002 sigue viva y coherente tras F-013 — **OK**

Comprobado sobre el árbol actual, con F-013 y F-008 ya encima.

**Suites ejecutadas a mano** (las tres líneas de `init.sh` venían de caché, así
que no me fío de ellas):

| Servicio | Resultado |
|---|---|
| `dedicacion-api` | **112 passed** |
| `dedicacion-front` | **11 passed** |
| `dedicacion-transfer` | **232 passed** |

De esos 232, **184 son de F-002** y pasan todos:

| Fichero | Tests | Qué ata |
|---|---|---|
| `test_f002_fuente_unica.py` | 60 | R1–R5: fuente única, anclas, frases prohibidas, procedencia |
| `test_f002_capacidad.py` | 35 | R23–R33: **Regla B**, capacidad del 100 % |
| `test_f002_reglas.py` | 25 | R6–R9, R12: P1, P2, P3 |
| `test_f002_postventa.py` | 23 | R15–R19: **P5**, postventa por código exacto sobre hoja activa |
| `test_f002_conflicto.py` | 21 | R14, R20–R22: **Regla A**, identidad con partida |
| `test_f002_pipeline.py` | 20 | R10, R11, R13: idempotencia, modo pruebas, deduplicación |

**F-013 no degradó nada.** Revisado el diff `985054e..HEAD` sobre el transfer:

- El único fichero de test de F-002 que F-013 tocó es
  `test_f002_fuente_unica.py`, y el cambio es de **una línea**:
  `@pytest.mark.parametrize("numero", range(1, 11))` →  `range(1, 12)`. Es
  **refuerzo**, no relajación: pasa a comprobar dos puntos más del documento
  contra la marca `PENDIENTE`.
- En `reglas_porcentajes.py` F-013 es **puramente aditivo**
  (`PREFIJO_CLAVE_SIN_PARTIDA`, `MOTIVO_SIN_PARTIDA`, `AVISO_SIN_PARTIDA`,
  `sin_partida()`, `clave_sin_partida()`). No toca `campos_identidad`,
  `criterio_choque`, `clave_conflicto`, `evaluar_capacidad` ni
  `es_linea_mensual`.
- En `registro_pipeline.py` las líneas eliminadas son la **generalización del
  despacho de dos motivos a tres** (donde había `if c.motivo != "sobrecarga"`
  ahora hay un reparto por motivo). El comportamiento de F-002 queda atado por
  sus propios tests, y R28 —la sobrecarga sin confirmar deja rastro en
  `omitidas`— sigue en verde, que es la prueba de que la generalización no se
  llevó nada por delante.
- `Conflicto` gana el motivo nuevo manteniendo defectos en todos los campos:
  la degradación elegante que F-002 diseñó sigue funcionando.

**Regla A, Regla B y postventa por código exacto: intactas y con sus tests
pasando.**

### 2.4 · Fuente única y procedencia — **OK con una corrección**

**Fuente única: correcta.** `docs/ARCHITECTURE.md` § «Semántica de dominio
imprescindible» es la única fuente normativa, con las anclas `#regla-p1`,
`#regla-p2`, `#regla-p3`, `#regla-p4` / `#regla-conflicto`,
`#regla-capacidad`, `#regla-sin-partida`, `#regla-p5` y `#regla-pruebas`. El
`README.md` del transfer **remite** con una tabla de enlaces (líneas 15–22) y
no reenuncia nada. Lo vigila `test_f002_fuente_unica.py`, en verde.

**Procedencia: correcta y sin atribuciones falsas.** Cuatro líneas, todas con
**quién · cuándo · con qué respaldo**:

| Ancla | Línea |
|---|---|
| `#regla-p5` (:182) | Pablo Gris (responsable del proyecto) · 2026-08-19 · verificado contra Sigrid, `progress/sigrid_F-002.md` |
| `#regla-p4` (:212) | Pablo Gris · 2026-08-19 · decisión D2, `requirements.md` §2 |
| `#regla-capacidad` (:242) | Pablo Gris · 2026-08-19 · decisión D2, `requirements.md` §2 |
| `#regla-sin-partida` (:277) | Pablo Gris · 2026-08-20 · preflight real del periodo 2026-07 |

**Nada se atribuye a Administración.** La única mención a Administración en el
documento (línea 17) habla de la plantilla Excel que mantenía a mano, que es
un hecho histórico y no una procedencia. Correcto: esa conversación no ha
existido y escribirla sería peor que no tener procedencia.

**La corrección.** `docs/ARCHITECTURE.md:188`, dentro de la línea de
procedencia de `#regla-p5`, dice:

```
las 84 partidas de obra todas hojas colgando de `CD`
```

Dos datos mal, y contradicen al documento al que esa misma línea remite:

1. **«84»** → son **86**. Lo corrigió expresamente la review de la Fase 2
   (§9.5) y está anotado en `progress/sigrid_F-002.md:51-57`: el 84 salió de
   un conteo que exigía límite de palabra tras los dígitos y dejaba fuera
   códigos como `0613-B`. Se arregló allí y **se quedó sin arreglar aquí**.
2. **«todas … colgando de `CD`»** → no todas. `sigrid_F-002.md:31` dice «salvo
   cuatro», y son precisamente las cuatro duplicadas sin cero inicial (`656`,
   `664`, `680`, `693`) que cuelgan de la **raíz** — las mismas cuya
   comunicación a Administración se ha movido a F-014.

Es la línea que respalda una regla normativa, y contradice su propia fuente en
el dato que la fuente corrigió a propósito. Pequeño, pero hay que arreglarlo.

**Además, una nota obsoleta.** `docs/ARCHITECTURE.md:127-128`:

```
OBRA_PRUEBAS_FORZAR se queda a `true` hasta que la verificación real
contra Sigrid (F-002, T13 y T14) la haga el humano.
```

La conclusión sigue siendo la buena —`OBRA_PRUEBAS_FORZAR` **debe** seguir en
`true`—, pero el motivo que da es falso desde el 2026-08-20: T13 y T14 ya se
hicieron. Conviene reformularlo para que la razón de seguir en modo pruebas
sea la verdadera (no se ha validado la imputación a partidas en producción,
que es justo lo que la propia sección «Qué NO queda demostrado» de
`sigrid_F-002.md` deja escrito), y no una condición ya cumplida.

### 2.5 · `bash harness/init.sh` — **OK (en verde, ejecutado por mí)**

Ejecutado tal cual, sin pipes ni decoración. **Exit code 0.**

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] servicio api (services/dedicacion-api): pytest en verde
[OK] servicio front (services/dedicacion-front): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
[OK] PUERTA COBERTURA: N/A (rama dev: solo aplica en ramas de feature)
[OK] Ningún .env versionado
[OK] Rama actual: dev
```

Dos avisos, ninguno bloqueante: `ruff` con 178 avisos (deuda previa declarada)
y «hay features en estado `blocked`».

**Las tres líneas de servicio venían de caché**, así que, como manda el
protocolo, ejecuté las tres suites a mano: 112 + 11 + 232 = **355 tests en
verde**. La caché no mentía.

**Cobertura N/A justificada por `init.sh`** con su motivo impreso: estamos en
`dev`, y la puerta solo aplica en ramas de feature. La cobertura de F-002 la
midió y aprobó `review_F-002_fase2.md` sobre su rama.

> Al empezar esta review `init.sh` estaba en **rojo con 3 fallos**
> (`features.json` inválido por marcadores de conflicto sin resolver, `pytest`
> de la raíz en rojo por `test_backlog_md`, y `rigor.py` reventando). Se
> resolvió solo, al terminar el líder los merges. Queda anotado: **no se
> pueden lanzar reviews sobre un árbol con un merge a medias**.

### 2.6 · F-014 recoge fielmente lo movido — **OK**

Revisada su entrada en `harness/features.json` (prioridad 20, `rigor:
documental`, `sdd: false`). Es de las entradas mejor escritas del backlog:
quien la coja dentro de seis meses tiene lo que necesita.

| Dato que hace falta | ¿Está? |
|---|---|
| `hmores.ide = 403039` | sí |
| `synckey 'porcentajes:77'` | sí |
| Marca `PRUEBA-PORC` | sí |
| Parte `PT26/00296` y `hmo.ide = 2820419` | sí |
| Obra de pruebas `0404` y fecha (2026-08-20) | sí |
| Comando de limpieza, con el mes correcto (`--mes 7`) | sí |
| Que solo toca lo marcado `PRUEBA-PORC` | sí |
| Que la cabecera del parte quedaría creada y vacía, y hay que decidir | sí |
| **Aviso de que probar desde Azure escribirá más líneas indistinguibles** | sí, con la recomendación de limpiar antes o distinguir por `ide` |
| Las cuatro partidas duplicadas de POSTV2 (`656`, `664`, `680`, `693`) | sí, con puntero a `progress/sigrid_F-002.md` |
| Quién firma la procedencia de P4/P5 | sí, y anota que el test no clava el interlocutor, así que cambiarlo no rompe nada |
| Por qué se movió | sí: «dejan de bloquear F-002 y la fase 7 de F-008» |

Los cinco criterios `acceptance` son verificables y no dan nada por sabido.
Está además duplicado en `progress/current.md` §«2 · F-014, cuando toque», con
el comando listo para copiar y el aviso del orden respecto al despliegue.
**Nada se ha perdido en el traslado.**

---

## 3 · Recorrido de CHECKPOINTS.md

| Checkpoint | Estado | Razón |
|---|---|---|
| **C1** · `init.sh` exit 0 y ficheros del arnés | `[x]` | Verde, ejecutado por mí. Suites reejecutadas a mano por venir de caché |
| **C2** · Estado coherente | `[x]` | `features.json` marca F-002 `in_progress`, que es lo correcto durante su review de cierre. `current.md` la declara «en review de cierre» y dice la verdad sobre T14 y sobre lo que se fue a F-014 |
| **C3** · Arquitectura y convenciones | `[x]` | Heredado de las dos reviews aprobadas. No se reabre |
| **C3 bis** · Documentos de fuera | **N/A** | **Justificado**: F-002 no incorporó ningún PDF ni documento ofimático. `docs/referencia/` no se tocó |
| **C4** · Verificación real | `[ ]` | Los dos primeros puntos, en verde: cada requisito tiene su test trazable `test_f002_rN_*` y los 184 pasan; ninguno toca red ni BBDD. **Falla el tercero**: las verificaciones `MANUAL (humano)` no están al día. `tasks.md` sigue dando T13 y T14 por pendientes, y el volcado de T13 que la tarea exige en `sigrid_F-002.md` no existe |
| **C4 bis** · Rigor declarado | `[x]` | **Heredado**, no reabierto. `rigor: critico` declarado; fase RED, cobertura, campaña de mutación (con su recálculo independiente) y sección «Evidencias» los validaron y aprobaron `review_F-002_fase1.md` y `review_F-002_fase2.md`. El único superviviente quedó justificado como equivalente y aceptado. **Campaña no reejecutada en esta review de cierre: es una review de cierre documental, no un re-review del código, y la campaña ya tuvo su verificación independiente en la Fase 2** |
| **C4 ter** · Rutas sensibles | **N/A** | **Justificado**: no existe `harness/rutas_sensibles.json` en el repositorio. Sin declaración, el bloque es N/A por diseño |
| **C5** · Sesión cerrada | `[ ]` | **Falla el primer punto**: `tasks.md` tiene **tres tareas `[ ]`** (T6, T13, T14), dos de ellas ejecutadas de verdad. Los otros dos puntos sí están: árbol limpio sin artefactos sospechosos, y `features.json` coherente |

**Dos checkboxes vacíos en C1–C5 ⇒ CHANGES_REQUESTED.**

---

## 4 · Trazabilidad requisito → test (subconjunto vivo tras F-013)

Comprobada la que importa para el cierre: que las reglas de F-002 siguen
atadas después de que F-013 tocara los mismos ficheros. La tabla completa
requisito a requisito está en `review_F-002_fase1.md` y
`review_F-002_fase2.md` y no se repite.

| Requisito | Test que lo cubre | Estado |
|---|---|---|
| R1–R5 · fuente única, anclas, procedencia con quién·cuándo·respaldo | `test_f002_fuente_unica.py` (60) | verde |
| R6–R9, R12 · P1 recursos `M*`, P2 último día del mes, P3 escala sobre 1 | `test_f002_reglas.py` (25) | verde |
| R10, R11, R13 · idempotencia por `synckey`, modo pruebas, un solo `DELETE` | `test_f002_pipeline.py` (20) | verde |
| R14, R20–R22 · **Regla A**: la partida entra en la identidad | `test_f002_conflicto.py` (21) | verde |
| R15–R19 · **P5**: postventa a hoja activa por código exacto | `test_f002_postventa.py` (23) | verde |
| R23–R33 · **Regla B**: capacidad del 100 %, tolerancia, alcance | `test_f002_capacidad.py` (35) | verde |
| T13 · casado real contra Sigrid, sin escribir | **MANUAL (humano)** — ejecutado, **sin volcado** | **falta** |
| T14 · escritura real en obra de pruebas | **MANUAL (humano)** — ejecutado y volcado en `sigrid_F-002.md` §T14 | verde |

---

## 5 · Cambios requeridos

Seis, todos de documento (el 6 no es bloqueante). **Ninguno toca código y
ninguno debería costar más de una sesión corta.**

1. **`specs/F-002-reglas-postventa-conflicto/tasks.md`, línea 233 — marcar T13
   `[x]`.** Se ejecutó el 2026-08-20. Corregir de paso el mes del comando:
   dice `--ano 2026 --mes 8` y lo ejecutado fue **julio** (`--mes 7`).

2. **`specs/F-002-reglas-postventa-conflicto/tasks.md`, línea 248 — marcar T14
   `[x]`, acotando qué parte se hizo.** Se ejecutaron `ejecutar --confirmar` y
   `verificar`; **`limpiar --confirmar` NO**, a propósito, y se movió a F-014.
   La tarea no puede quedar marcada como si la limpieza estuviera hecha: hay
   una fila viva en Sigrid. Añadir la remisión a `progress/sigrid_F-002.md`
   §T14 y a F-014, y corregir también aquí `--mes 8` → `--mes 7`.

3. **`specs/F-002-reglas-postventa-conflicto/tasks.md`, línea 77 y cabecera
   (líneas 8–14) — cerrar T6 como movida a F-014.** Marcarla `[x]` o `N/A` con
   la nota de que su contenido (aviso a Administración de las cuatro partidas
   duplicadas de POSTV2 y firma de la procedencia) pasó a F-014 por decisión
   del humano del 2026-08-20. Y reescribir la cabecera, que hoy afirma que
   «lo único que sigue exigiendo al humano son T6, T13 y T14»: de las tres, dos
   están hechas y una se fue a otra feature.

4. **`progress/sigrid_F-002.md` — añadir la sección `## T13`.** Es lo que la
   propia tarea exige («Volcado a `progress/sigrid_F-002.md`») y hoy no
   existe: la sección que la contenía vivía en `progress/current.md` de la
   rama de F-008 y **se perdió al resolver el merge**. Debe recoger, con las
   cifras reales del preflight de julio de 2026:
   - qué se lanzó y con qué parámetros (`capitulos`, `estado`, `preflight`);
   - los totales (las «13 obras, 4 líneas a escribir, 0 conflictos» que cita
     el encargo y que no constan en ningún fichero del repositorio);
   - **las dos comprobaciones que T13 existía para hacer**: que la partida
     resuelta es una **hoja**, y si apareció —o no, y por qué— el conflicto de
     **sobrecarga** con sus cifras;
   - el caso de la jefa de obra sin partida (`2.132,28 €`, `can = 0,385`) que
     originó F-013, hoy citado de segunda mano en `ARCHITECTURE.md:278-282` y
     `history.md:270-272`.

5. **`docs/ARCHITECTURE.md:188` — corregir la línea de procedencia de
   `#regla-p5`.** Dice «las **84** partidas de obra **todas** hojas colgando
   de `CD`». Son **86**, y **cuatro cuelgan de la raíz**, no de `CD`
   (`progress/sigrid_F-002.md:31` y :51-57, corregido ya por la review de la
   Fase 2 en aquel documento pero no en este).

6. **`docs/ARCHITECTURE.md:127-128` — reformular la nota de
   `OBRA_PRUEBAS_FORZAR`.** *(No bloqueante, pero conviene hacerlo en el mismo
   paso.)* Dice que se queda en `true` «hasta que la verificación real contra
   Sigrid (F-002, T13 y T14) la haga el humano», y ya se hizo. La conclusión
   es correcta y debe mantenerse; lo que hay que cambiar es el motivo, que
   ahora es el de verdad: **no se ha validado la imputación a partidas en
   producción**, tal y como deja escrito la sección «Qué NO queda demostrado»
   de `progress/sigrid_F-002.md`.

**Qué NO hay que hacer:** tocar código, reabrir las Fases 1 y 2, relanzar la
campaña de mutación ni cambiar un solo test. F-002 está bien construida.

---

## 6 · Automejora del protocolo (propuesta, no aplicada)

Tres cosas que este cierre ha dejado a la vista. **Se proponen para que las
apruebe el humano**; ninguna se ha aplicado.

1. **La evidencia de una verificación `MANUAL (humano)` no puede vivir en
   `progress/current.md`.** Es lo que pasó con T13: `current.md` es un
   documento de sesión, se reescribe entero y en el siguiente merge se llevó
   por delante la sección. Sugerencia para `.claude/agents/implementer.md` y
   `CHECKPOINTS.md` (C4): el volcado de una verificación manual va **siempre**
   a un fichero propio y permanente (aquí, `progress/sigrid_F-XXX.md`);
   `current.md` como mucho lo **enlaza**. *Vale para cualquier proyecto ⇒
   portar a `arnes-base`.*

2. **Ejecutar una tarea `MANUAL (humano)` y no marcarla en `tasks.md` es el
   punto ciego que ha provocado este rechazo.** Se hizo el trabajo de verdad
   —incluida la primera escritura de este sistema en un ERP— y el documento
   siguió diciendo «pendiente». Sugerencia para `CHECKPOINTS.md` C4: añadir un
   checkbox explícito, «**toda verificación `MANUAL (humano)` ejecutada está
   marcada en `tasks.md` y su volcado enlazado**», para que el reviewer tenga
   que mirarlo y no dependa de que se le ocurra. *Genérico ⇒ `arnes-base`.*

3. **Mover tareas de una feature a otra necesita dejar rastro en el origen.**
   T6 se fue a F-014 y `tasks.md` de F-002 no se enteró. F-014 está
   ejemplarmente escrita, pero el rastro solo va en un sentido. Sugerencia:
   cuando el líder mueva una tarea, la tarea original se marca en el origen
   con «movida a F-YYY» **en el mismo commit** que crea la feature destino.
   *Genérico ⇒ `arnes-base`.*

4. **Un reviewer no debe arrancar sobre un árbol con un merge a medias.** Esta
   review empezó con `init.sh` en rojo por marcadores de conflicto sin
   resolver y el árbol cambió tres veces bajo los pies. Sugerencia para
   `.claude/agents/reviewer.md`, paso 1: si `git status` muestra ficheros en
   estado `UU` o existe `.git/MERGE_HEAD`, **parar y devolver el control al
   líder** en vez de intentar revisar. *Genérico ⇒ `arnes-base`.*
