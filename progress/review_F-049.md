Revisión incremental desde 31b8f95 (pasada 4) · HEAD `2eda667` — pasadas 1 a 3 resumidas abajo

# F-049 · Review — Los avisos del modal de registro rotulados por tipo

**Veredicto vigente (pasada 4): CAMBIOS PEDIDOS** (CHANGES_REQUESTED): los
tres cambios de la pasada 3 están resueltos y la suite está en verde sin
caché; queda **una línea falsa en `progress/current.md`** (C2), del mismo tipo
que el cambio 3 y que yo no vi en la pasada 3.

**Nivel de rigor:** `estandar` (declarado): tests trazables, RED real,
cobertura y mutación con supervivientes analizados. `sdd: false`: contra los
`acceptance` y el plan aprobado (descripción y `current.md`).

## Pasadas 1 a 3 (resumen)

Texto íntegro: pasadas 1-2 en `git show cbc0451:progress/review_F-049.md`;
pasada 3 en `git show 2eda667:progress/review_F-049.md`.

- **Pasada 1** (completa): CAMBIOS PEDIDOS (nº de fallos por mutante); manual
  33/33 reejecutada por mí; O1–O4 (O4 a F-048). **Pasada 2**: APROBADA.
- **Corrección:** ambas marcaron C1/C4 `[x]` con `test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos`
  (transfer) **en rojo desde `3ad478b`**, oculto por la caché de init.sh
  (no mira `app.js`). Ver «Automejora».
- **Pasada 3** (incremental desde `cbc0451`, ampliación a)–e)): CAMBIOS
  PEDIDOS. Código de a)–e) correcto (d no cambia lo que se escribe, una
  lectura por petición; b no rompe a; decisión 1 segura; MANUAL seguible).
  Mutación Python 7/7 (74,6 s > 60 s: no reejecutada, recálculo puro + RM4);
  manual A11/A19/A27 reproducidas. Pidió: 1) `test_f013_r4` prohíba los tres
  motivos fuera de `rotuloConflicto`; 2) `acceptance` a)–e) y despliegue;
  3) cabecera de `current.md` (F-045 «en su rama» era falso). O5 (doble
  registro concurrente) a F-048 o aparte; O6 aceptada.

## Pasada 4 · lo que se ejecutó (resultado real)

- `git diff 31b8f95 --stat`: 7 ficheros; código solo
  `services/dedicacion-transfer/tests/test_f013_sin_partida.py` (+6/−2);
  `app.js` intacto. Commits `4e54a8b` (líder), `f32e4d3` (implementer),
  `2eda667` (estado).
- `bash harness/init.sh`, tal cual y solo, desde la copia aparte: **«ENTORNO
  LISTO»**, sin `[KO]`; raíz `418 passed, 1 skipped` (112,5 s); api y front
  por caché; **transfer ejecutado: 658 passed** (18,4 s); `PUERTA COBERTURA
  [OK] 100.0% (2/2)`; `PUERTA TAMAÑO` impl 220/220, review 140/140; `ruff`
  `[AVISO]` 237 (deuda previa).
- **Suite del transfer SIN caché** (intérprete de `harness.servicios --shell`,
  `-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`, sin `-x`, desde la
  carpeta del transfer de la copia): **658 passed, 1 warning** (previa,
  `test_pipeline_offline.py::test_preflight` devuelve valor) en 8,06 s. El
  módulo cargado es el de la copia (`porcentajes-f041\…\registro_pipeline.py`
  por `__file__`). En `-rA`: las 6 `test_f013_r4_*` y las 5 `test_f049_d_*`
  PASSED.
- **Mutantes del cambio 1 reproducidos** (§4 de `mutacion_manual_F-049.md`)
  sobre un `git archive HEAD` de los tres servicios en mi scratchpad, solo
  `test_f013_sin_partida.py`: control R0 = 4 failed / 38 passed (las 4
  `test_f013_r6_*` leen ficheros fuera de `services/`, que mi archivo no
  trae; ajenos al cambio). **R1** (`else if (a.motivo === "pisado")`) y **R4**
  (`a.motivo !== undefined ? …`), texto exacto de la tabla: **5 failed**, el
  único nuevo `test_f013_r4_el_front_rotula_por_motivo_y_degrada` = **1
  fallo**, como dice la tabla (R4, solo por la regex). Árbol limpio.

## Pasada 4 · cambios de la pasada 3, contrastados

1. **Resuelto.** `test_f013_sin_partida.py:419-424`: fuera de
   `rotuloConflicto` prohíbe los tres motivos y `motivo\s*[!=]==?` (cubre
   `==`, `===`, `!=`, `!==`; no casa una asignación). `import re` ya existía
   (`:27`). Hoy los tres literales y `motivo ===` solo están en
   `app.js:1762-1779`, dentro de la función. El test viejo dejaba vivos
   R1-R4 (por lectura: solo buscaba `"sobrecarga"`).
2. **Resuelto.** `features.json` F-049 `acceptance`: a)–e) con el texto del
   plan aprobado y «Despliegue: transfer y front»; `BACKLOG.md` al día
   (init.sh).
3. **Resuelto en la cabecera** (`current.md:3-8`): principal en `dev`, F-045
   cerrada y desplegada (comprobado: la principal está en `dev`, `06b88df`).
   **Pero** `current.md:188` sigue diciendo «Orden: **F-045 (en curso)**,
   F-049, …»: el mismo resto falso, ahora contradiciendo a la cabecera →
   Cambio 1 de esta pasada. Se me pasó en la pasada 3.
- **O5** llevada a la descripción de F-048 (`features.json` y `BACKLOG.md`),
  con el texto de la review: recogida. **O6** aceptada.

## Pasada 4 · checkpoints (`CHECKPOINTS.md` no cambia en el delta)

**C1** [x] init.sh exit 0, «ENTORNO LISTO» · [x] transfer sin caché 658
passed; api y front sin cambios de código desde la pasada 3 (las forcé
entonces: 689 y 142) · [x] ficheros base. **C2** [x] una `in_progress`
(F-049) · [x] rama `feature/F-049-avisos-registro-por-tipo` · **[ ]**
`current.md` sin restos: línea 188 «F-045 (en curso)» es falsa → Cambio 1 ·
[x] `done` con `history.md`. **C3** [x] hexagonal (el delta es un test) ·
[x] primera línea con ruta · [x] sin prints, TODOs ni secretos; `ruff` del
fichero: 2 avisos, 3 antes del cambio (no añade). **C3 bis** N/A: no toca
`docs/referencia/`. **C4** [x] a)–e) y R4 con test (tabla) · [x]
`test_f013_r4` vuelve a proteger los tres motivos (R1-R4 mueren) · [x] sin
red ni BBDD · [x] MANUAL con comandos, _pendiente_ del humano. **C4 bis** [x]
`rigor: estandar` · [x] RED: el endurecimiento trae su evidencia como
mutantes vivos con el test viejo y muertos con el nuevo (§4, 2 reproducidos)
· [x] cobertura `[OK]` 100 % · [x] `mutacion_F-049.md` 7/7 sin
supervivientes; RM1: `e7b660f..HEAD` sigue sin tocar `registro_pipeline.py`
· [x] RM2/RM3 como en la pasada 3 · N/A RM5 (rigor `estandar`) · N/A RM6
(ninguna guarda quitada) · [x] manual §4: fila por mutante con texto exacto y
nº de fallos; R1 y R4 reproducidos · [x] «Evidencias» con los cuatro números
y la suite sin caché tras la review 3. **C4 ter** N/A: no hay
`harness/rutas_sensibles.json`. **C5** N/A `tasks.md` (`sdd: false`); commits
`F-049 …` · [x] árbol limpio · [x] `acceptance` recogen la ampliación.

## Cobertura · requisito → test

| Punto | Tests |
|---|---|
| Rotulado por tipo y % de `nuevas` | `test_f049_avisos_registro.py` (node); `test_f013_r4_el_front_rotula_por_motivo_y_degrada` |
| Mismas claves a ejecutar | `test_f013_r4_el_conflicto_serializa_…`, `…_no_hace_falta_ningun_campo_nuevo`, `…_ni_la_api_ni_el_front_enumeran_…` (api) |
| a) repreflight, casillas, «Registrar» bloqueado | `test_f049_ampliacion_registro.py`: `a_*` (11) |
| b) abrir empieza sin partidas | `b_abrir_desde_un_boton_…`, `b_abrir_de_nuevo_descarta_…`, `b_una_apertura_vieja_…` |
| c) partida fuera de la lista | `c_*` (7, escapado incluido); `test_f039_r22` |
| d) `partidas_obra` con todo manual | `test_f049_partidas_obra.py` (5) |
| e) CSS | `e_el_aviso_amarillo_…`, `e_el_texto_de_la_casilla_…`; visual en la MANUAL paso 9 |
| Despliegue transfer y front | al cerrar (líder), tras la MANUAL |

## Pasada 4 · cambios requeridos

1. `progress/current.md:188` (sección «Lo siguiente, por prioridad»): quitar
   «F-045 (en curso)» del orden; F-045 está cerrada y desplegada, como ya dice
   la cabecera. Releer el fichero entero por si queda otro resto de F-045.
   Al relanzar, poner el resultado de esta review 4 en el estado de F-049.

**Observaciones (no bloquean):**
- **O7** La rama no lleva lo de `dev` desde `2ebc061` (cierre y despliegue de
  F-045: `features.json`, `current.md`, `BACKLOG.md`, `history.md`…). Antes de
  cerrar, fusionar `dev` en la rama, resolver el rastro sin reescribirlo a
  ciegas y ejecutar `bash harness/init.sh` solo, sin grep, con las suites de
  los servicios sin caché.
- **O5** sigue abierta en F-048 (doble registro concurrente).

## Automejora (propuesta, no aplicada)

1. `.claude/agents/reviewer.md`, paso 2 (de la pasada 3, se mantiene): «Si
   `init.sh` da una suite de servicio por caché, ejecútala sin caché
   (`harness.servicios --shell` + `pytest -p no:cacheprovider`) y anota los
   números». Encargo 1.7.12 de `arnes-base` (`7b6701a`).
2. Nueva, para `CHECKPOINTS.md` C2: «Si la review pide corregir una
   afirmación de `current.md`, el reviewer busca el mismo dato en todo el
   fichero (`grep` del identificador) antes de dar el cambio por resuelto».
   Es lo que me faltó en la pasada 3 con F-045.
