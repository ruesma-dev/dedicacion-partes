Revisión incremental desde cbc0451 (pasada 3) · HEAD `31b8f95` — pasadas 1 (completa) y 2 (incremental desde `5d6b267`) resumidas abajo

# F-049 · Review — Los avisos del modal de registro rotulados por tipo

**Veredicto vigente (pasada 3): CAMBIOS PEDIDOS** (CHANGES_REQUESTED): un
test relajado de más y dos de rastro; el código de a)–e) está bien.

**Nivel de rigor:** `estandar` (declarado): tests trazables, RED real,
cobertura y mutación con supervivientes analizados. `sdd: false`: contra los
`acceptance` y el plan aprobado (descripción y `current.md`).

## Pasadas 1 y 2 (resumen; texto íntegro en `git show cbc0451:progress/review_F-049.md`)

- **Pasada 1** (completa): CAMBIOS PEDIDOS (nº de fallos por mutante); manual
  33/33 reejecutada por mí; O1–O4 (O4 a F-048). **Pasada 2**: APROBADA.
- **Corrección:** ambas marcaron C1/C4 `[x]` con `test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos`
  (transfer) **en rojo desde `3ad478b`** (`app.js` nombra los motivos 2/1/1
  veces; 0 en `3ad478b^`, con `git show`): la caché del transfer no mira
  `app.js`, y en la pasada 1 forcé el front, no el transfer. Ver «Automejora».

## Pasada 3 · lo que se ejecutó (resultado real)

- `bash harness/init.sh`, tal cual y solo, desde la copia aparte: **«ENTORNO
  LISTO»**, sin `[KO]`; raíz `418 passed, 1 skipped`; api, front y transfer
  **por caché**; `PUERTA COBERTURA [OK] 100.0% (2/2)`; tamaño en topes.
- **Suites forzadas sin caché** (intérprete de `harness.servicios --shell`,
  `-p no:cacheprovider`, sin `-x`): transfer **658 passed** (con el código de
  la copia, por `__file__`), front **142**, api **689**. Las 6 `test_f013_r4_*`
  y las 5 `test_f049_d_*`, PASSED en `-rA`; los 24 del front, en node.
- **Mutación Python** (`mutacion_F-049.md`, 74,6 s > 60 s: **campaña no
  reejecutada**, recálculo puro + RM4): `alcance_de_feature` = 11 líneas de
  `registro_pipeline.py` (394-404), `generar_mutantes` = **7**, mismos
  operadores que el informe. RM4 sobre copia en mi scratchpad: `== "var"` y
  `is None or any(` mueren con 2 fallos cada uno en `test_f049_partidas_obra.py`.
- **Manual** §3, reproducidas en copia aparte: **A11 (1), A19 (1), A27 (2)** = tabla.
- **Fragmentos de consola** de la MANUAL, en node con las funciones reales:
  el 1 pinta «Sin partida» 5 %, «Sobrecarga» (95 % → 105 %, 5 % de exceso) y
  «Pisar» (línea 8001, 60 %); el 2, `selected` «CI.9.99 · (no está en la
  lista)». Lo que dice `current.md`. Árbol limpio (todo al scratchpad).

## Pasada 3 · lo que pidió el líder, contrastado con el código

1. **d) no cambia lo que se escribe ni las reglas de partida; una lectura por
   petición.** El bloque nuevo (`registro_pipeline.py:394-404`) va después
   del bucle, solo asigna `nodos_origen`, y `nodos_origen` solo lo usa
   `_cat` para `partidas_obra` (`:606`). Tras el bucle, una `escribir` de obra
   no-VAR sin catálogo leído solo puede ser manual: la condición es exacta.
   Tests: `d_lo_que_se_escribe_no_cambia` (inserta 80002), `d_varias_manuales_
   una_sola_lectura`, `d_manual_y_automatica_…` (sigue 1 lectura),
   `d_solo_postventa_…` (0). Nota: `ejecutar` llama a `preflight`, así que el
   registro con todo manual también hace esa lectura (O6).
2. **b) no rompe a).** `registro.overrides = {}` solo en `registroPreflight`
   (botones); `repreflightPartida` no lo toca y el `change` apunta la partida
   antes de repetir. `seq` descarta el repreflight en vuelo al reabrir. Tests:
   `b_abrir_de_nuevo_descarta_un_repreflight_en_vuelo`,
   `a_el_preflight_repetido_lleva_la_partida_recien_elegida` (A27).
3. **Decisión 1 (error → «Registrar» activo): segura.** Ese camino es el
   comportamiento previo a la ampliación (elegir y registrar sin repintar), y
   `ejecutar` reanaliza en el transfer con las elegidas: la clave del pisado
   lleva `paride` (`CAMPOS_CLAVE`, `reglas_porcentajes.py:106`), así que una
   casilla marcada con la partida vieja no casa y queda pendiente; la de
   sobrecarga no depende de la partida (`:276-281`); la de sin partida es por
   línea y desaparece al elegir. Lo no confirmado sale como «pendientes».
4. **Decisión 3, tests que cambian.** `test_f039_r22`: solo el literal de la
   llamada, el resto de R22 igual: bien. `test_f013_r4`: ahora corre y está
   en verde, la api sigue con los tres motivos, pero **relaja lo que
   protegía**: fuera de `rotuloConflicto` solo prohíbe `"sobrecarga"`; un
   `if (c.motivo === "pisado")` en cualquier otra función de `app.js` pasaría.
   Su docstring dice «ramifica por `motivo` solo para rotular» → Cambio 1.
5. **MANUAL seguible.** `main.py` del transfer pasa el objeto `app` a uvicorn
   (sin recarga): corre el código de la copia, con el `.env` de la carpeta de
   arranque (existe; no lo leí); `/health` da `modo_pruebas`. El front de la
   copia (`.venv` enlazado, sin `.env`) va a `127.0.0.1:8090`; la api reenvía
   el preflight tal cual (`registro_sigrid.py:129-131`).

## Pasada 3 · checkpoints

**C1** [x] init.sh exit 0 y las tres suites forzadas en verde · [x] ficheros
base. **C2** [x] una `in_progress` · [x] rama `feature/F-049-…` · **[ ]**
`current.md` líneas 5-6: «En la copia principal, F-045 (Excel) en su rama» es
falso al escribirlo (F-045 cerrada en `18cb6a8` 14:57 y desplegada en
`06b88df` 15:24; `31b8f95` es de las 15:30; la principal está en `dev`) →
Cambio 3 · [x] `done` con `history.md`. **C3** [x] hexagonal: el transfer usa
el puerto que ya tenía (`capitulos_de_obra`); el front repite una petición y
pinta, no decide nada · [x] primera línea con ruta · [x] sin prints, TODOs ni
secretos; `ruff` limpio en los tests nuevos · [x] reglas P5/VAR/postventa
intactas. **C3 bis** N/A: no toca `docs/referencia/`. **C4** [x] cada punto
a)–e) con test (tabla) · **[ ]** `test_f013_r4` deja de proteger dos de los
tres motivos fuera del rotulado → Cambio 1 · [x] sin red ni BBDD · [x] MANUAL
con comandos, comprobada contra el código, _pendiente_. **C4 bis** [x]
`rigor: estandar` · [x] RED real (2 failed transfer; 20 failed front) · [x]
cobertura `[OK]` 100 % · [x] `mutacion_F-049.md` 7/7, sin supervivientes ·
[x] muertos: > 60 s, recálculo puro + RM4 · [x] tiempo: 7 × 10,7 ≈ 74,6 s ·
[x] sin «NO VÁLIDA», «Sin veredicto» 0, línea base 9,0 s · [x] RM1: SHA
`e7b660f`; `e7b660f..HEAD` no toca `registro_pipeline.py` · [x] RM2: media
> línea base, coherente · [x] RM3: ninguno de los 7 es equivalente · N/A RM5
(rigor `estandar`) · N/A RM6 (ninguna guarda quitada) · [x] manual: fila por
mutante con texto exacto y fallos, 3 reproducidas · [x] hueco A27 cerrado con
test · [x] «Evidencias» con los cuatro números. **C4 ter** N/A: no hay
`harness/rutas_sensibles.json`. **C5** N/A `tasks.md` (`sdd: false`); commits
`F-049 T4..T7` · [x] árbol limpio · **[ ]** `features.json`: los `acceptance`
no recogen la ampliación aprobada → Cambio 2.

## Pasada 3 · cobertura de la ampliación → tests

| Punto | Tests |
|---|---|
| a) repreflight, casillas, «Registrar» bloqueado, solo la última | `test_f049_ampliacion_registro.py`: `a_repreflight_manda_…`, `a_registrar_bloqueado_…`, `a_conserva_las_casillas_…`, `a_solo_pinta_la_ultima_…`, `a_modal_cerrado_…`, `a_error_…` (2), `a_cambiar_la_partida_…`, `a_el_preflight_repetido_…`, `a_las_casillas_…`, `a_solo_el_desplegable_…` |
| b) abrir empieza sin partidas | `b_abrir_desde_un_boton_…`, `b_abrir_de_nuevo_descarta_…`, `b_una_apertura_vieja_…` |
| c) partida fuera de la lista | `c_…` (7 tests, escapado incluido); `test_f039_r22` |
| d) `partidas_obra` con todo manual | `test_f049_partidas_obra.py` (5) |
| e) CSS | `e_el_aviso_amarillo_…`, `e_el_texto_de_la_casilla_…` (estáticos; visual en la MANUAL paso 9) |

## Pasada 3 · cambios requeridos

1. `services/dedicacion-transfer/tests/test_f013_sin_partida.py:420`: fuera de
   `rotuloConflicto`, prohibir **los tres** motivos (y `motivo ===`), no solo
   `"sobrecarga"`. Hoy pasa: los tres solo aparecen en `app.js:1762-1779`.
2. `harness/features.json`, F-049 `acceptance`: añadir los criterios a)–e)
   aprobados (y «despliegue: transfer y front»); `BACKLOG.md` por init.sh.
3. `progress/current.md:5-6`: quitar «En la copia principal, F-045 (Excel) en
   su rama» y decir el estado real (F-045 cerrada y desplegada; principal en
   `dev`). Al relanzar, poner el resultado de esta review 3.

**Observaciones (no bloquean; el líder las deja en un sitio con nombre):**
- **O5** Doble registro concurrente: durante «Registrando…», cambiar una
  partida lanza el repreflight, que repinta con «Registrar» activo; un segundo
  clic abre otro `ejecutar` en paralelo. Ya era posible con Cancelar y
  reabrir; no hay cerrojo en api ni transfer y el `synckey` no cubre dos
  peticiones en vuelo. Propuesta: ignorar repreflight y apertura mientras se
  ejecuta, o cerrojo por periodo en la api. A F-048 o feature aparte.
- **O6** Todo manual: `ejecutar` también lee el presupuesto (una vez); si
  falla, falla antes de escribir, como con líneas automáticas. Aceptable.

## Automejora (propuesta, no aplicada)

`.claude/agents/reviewer.md`, paso 2: «Si `init.sh` da una suite de servicio
por caché, ejecútala sin caché (`harness.servicios --shell` + `pytest -p
no:cacheprovider`) y anota los números». Hasta el encargo 1.7.12 de
`arnes-base` (`7b6701a`), es lo que habría cazado el rojo de `test_f013_r4`.
