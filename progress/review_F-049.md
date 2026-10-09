Revisión incremental desde 2eda667 (pasada 5) · HEAD `bd4f88f` — pasadas 1 a 4 resumidas abajo

# F-049 · Review — Los avisos del modal de registro rotulados por tipo

**Veredicto vigente (pasada 5): APROBADO** (APPROVED): el cambio 1 de la
pasada 4 está resuelto, el merge de `dev` (O7) no pierde nada de F-049 ni
trae restos caducados, el código de F-049 no cambia desde `2eda667` e
init.sh sale en verde con las tres suites de servicio ejecutadas sin caché.

**Nivel de rigor:** `estandar` (declarado): tests trazables, RED real,
cobertura y mutación con supervivientes analizados. `sdd: false`: contra los
`acceptance` y el plan aprobado (descripción y `current.md`).

## Pasadas 1 a 4 (resumen)

Texto íntegro: pasadas 1-2 en `git show cbc0451:progress/review_F-049.md`;
pasada 3 en `git show 2eda667:…`; pasada 4 en `git show ac0f495:…`.

- **Pasada 1** (completa): CAMBIOS PEDIDOS (nº de fallos por mutante); manual
  33/33 reejecutada por mí; O1–O4 (O4 a F-048). **Pasada 2**: APROBADA.
- **Corrección:** ambas marcaron C1/C4 `[x]` con `test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos`
  (transfer) **en rojo desde `3ad478b`**, oculto por la caché de init.sh.
- **Pasada 3** (desde `cbc0451`, ampliación a)–e)): CAMBIOS PEDIDOS. Código
  correcto; mutación Python 7/7 (74,6 s > 60 s: no reejecutada, recálculo
  puro + RM4); manual A11/A19/A27 reproducidas. Pidió endurecer
  `test_f013_r4`, los `acceptance` a)–e) y la cabecera de `current.md`. O5
  (doble registro concurrente) a F-048; O6 aceptada.
- **Pasada 4** (desde `31b8f95`): los tres cambios resueltos; `test_f013_r4`
  mata R1 y R4 (reproducidos, 1 fallo cada uno); transfer sin caché 658
  passed. CAMBIOS PEDIDOS solo por `current.md:188` «F-045 (en curso)». O7:
  traer `dev` antes de cerrar.

## Pasada 5 · lo que se ejecutó (resultado real)

- **Delta** `git log 2eda667..HEAD`: `ac0f495` (mi review 4) y `bd4f88f`
  (merge de `dev` = `06b88df`, padres `ac0f495` y `06b88df`;
  `git merge-base --is-ancestor dev HEAD` → sí).
- **Código de F-049 intacto.** Fichero a fichero del delta (20): todo el
  código (`services/dedicacion-api/…/excel/contenido.py`, `exporter.py`,
  `tests/test_f039_registro_var.py`, `test_f040_excel.py`,
  `test_f045_excel_pestanas.py`, `README.md`), `specs/F-045-…`, docs,
  `infra/imagenes.json`, `history.md` y los informes de F-045 son
  **idénticos a `dev`**. Ninguno de los 15 ficheros de F-049
  (`git diff merge-base..2eda667`: front, transfer y su rastro) está en el
  delta. Solo difieren de `dev` `current.md`, `features.json`, `BACKLOG.md`
  y este informe, y lo que difiere es exactamente lo de F-049.
- **`features.json`** frente a `dev`: solo F-048 (O4 y O5 recogidas) y F-049
  (`in_progress`, descripción y `acceptance` a)–e) + despliegue); frente a
  `2eda667`, la entrada de F-049 no cambia. F-045 `done`, «CERRADA… DESPLEGADA
  el 2026-10-08 (api r20261008-1509)»; F-052/F-053/F-054 nuevas de `dev`.
- **`current.md`** (282 líneas, leído entero): frente a `dev` solo se pierde
  la cabecera «Ninguna feature en ejecución…», sustituida por la de la rama
  con el mismo dato (principal en `dev`, F-045 cerrada y desplegada); frente a
  `2eda667`, la sección de F-049 y su MANUAL completa se conservan y añade
  «Review 4… Review 5 lanzada». `grep F-045`: líneas 7, 50, 52, 114 y 200,
  todas como cerrada/desplegada; «Lo siguiente» empieza por «F-049 (en
  curso, en `porcentajes-f041`)». Sin marcadores de conflicto (`git grep`).
- **`BACKLOG.md`**: «En curso: F-049»; F-045 «terminada»; init.sh «al día».
- **`bash harness/init.sh`**, tal cual y solo, tras borrar
  `.arnes_cache/suite_*.ok` (caché ignorada por git): **«ENTORNO LISTO»**, sin
  `[KO]`; raíz `418 passed, 1 skipped`; **api 715 passed**, **front 142
  passed**, **transfer 658 passed**, las tres ejecutadas (ninguna «caché»);
  `PUERTA COBERTURA [OK] 100.0% (2/2)`; `PUERTA TAMAÑO` impl 220/220;
  `ruff` `[AVISO]` 237 (deuda previa). Árbol limpio después.
- **RM1:** la campaña de `mutacion_F-049.md` mide `registro_pipeline.py`
  (transfer), que el merge no toca: sigue valiendo.

## Pasada 5 · checkpoints (`CHECKPOINTS.md` no cambia en el delta)

**C1** [x] init.sh exit 0, «ENTORNO LISTO» · [x] api, front y transfer
ejecutadas sin caché (715/142/658) · [x] ficheros base. **C2** [x] una
`in_progress` (F-049) · [x] rama `feature/F-049-avisos-registro-por-tipo` ·
[x] `current.md` sin restos: cambio 1 de la pasada 4 resuelto y releído
entero (`grep F-045` sin afirmaciones falsas) · [x] `done` con `history.md`
(F-045, entrada del 2026-10-08 traída de `dev`). **C3** [x] hexagonal (el
delta no trae código de F-049; el de F-045 es el aprobado en su review) ·
[x] primera línea con ruta · [x] sin prints, TODOs ni secretos (el merge no
añade nada que no esté en `dev`). **C3 bis** N/A: el delta no toca
`docs/referencia/`. **C4** [x] a)–e) y R4 con test (tabla) · [x] sin red ni
BBDD · [x] MANUAL con comandos, _pendiente_ del humano. **C4 bis** [x]
`rigor: estandar` · [x] RED y manual §4 como en la pasada 4 (sin cambios) ·
[x] cobertura `[OK]` 100 % · [x] `mutacion_F-049.md` 7/7 sin
supervivientes; RM1 arriba · [x] RM2/RM3 como en la pasada 3 · N/A RM5
(rigor `estandar`) · N/A RM6 (ninguna guarda quitada) · [x] «Evidencias» con
los cuatro números. **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
**C5** N/A `tasks.md` (`sdd: false`); commits `F-049 …` y el merge · [x]
árbol limpio · [x] `acceptance` recogen la ampliación.

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

## Pasada 5 · cambios requeridos

Ninguno.

**Para cerrar (no es de esta review):** la MANUAL del humano (pasos 1-9 de
`current.md`, sin pulsar «Registrar») y el despliegue de transfer y front
(acceptance). Si el humano encuentra algo en la MANUAL que cambie código, la
review siguiente será incremental desde `bd4f88f`.

**Observaciones (no bloquean):**
- **O5** sigue abierta en F-048 (doble registro concurrente).
- **O8** Al fusionar la rama en `dev`, `current.md` tendrá el conflicto
  inverso: conservar la sección de F-049 movida a `history.md`, no
  reescribir a ciegas, y volver a ejecutar init.sh solo.

## Automejora (propuesta, no aplicada)

1. `.claude/agents/reviewer.md`, paso 2 (de la pasada 3, se mantiene): «Si
   `init.sh` da una suite de servicio por caché, ejecútala sin caché
   (`harness.servicios --shell` + `pytest -p no:cacheprovider`) y anota los
   números». Encargo 1.7.12 de `arnes-base` (`7b6701a`).
2. `CHECKPOINTS.md` C2 (de la pasada 4, se mantiene): «Si la review pide
   corregir una afirmación de `current.md`, el reviewer busca el mismo dato
   en todo el fichero (`grep` del identificador) antes de darlo por resuelto».
3. Nueva, `reviewer.md` («Revisión incremental»): «Si el delta es un merge de
   `dev`, comprueba fichero a fichero que lo no propio de la feature es
   idéntico a `dev` (`git diff --quiet dev HEAD -- <f>`) y que ningún fichero
   de la feature entra en el delta». Barato y deja medido lo que trae el
   merge sin releer otra feature ya aprobada.
