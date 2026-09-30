Revisión incremental desde ec2b0fa (pasada 2) · la pasada 1, completa sobre `ec2b0fa`, va resumida primero
<!-- progress/review_F-022.md -->
# F-022 · Review · El transfer busca cada obra por código y empresa

## Pasada 1 · revisión completa (`git diff dev..HEAD`, HEAD `ec2b0fa`), resumida

- **Veredicto: CHANGES_REQUESTED**, solo por el rastro (`progress/current.md`,
  C2). **Código, tests, mutación y documentación, aprobados.**
- **Rigor `critico`, declarado** en `features.json`: C1–C5, C3 bis, tests
  trazables, RED con traza real, cobertura ≥ 80 %, mutación sin
  supervivientes, `MANUAL (humano)` con comando exacto y resultado antes de `done`.

| Verificado ejecutando | Resultado real |
|---|---|
| `bash harness/init.sh` | ENTORNO LISTO; 355 passed, 1 skipped; cobertura **97,4 %** (76/78) |
| Alcance y mutantes recalculados | 10 ficheros, 226 líneas, **28 mutantes**: igual que el informe |
| Campaña reejecutada (`--workers 1 --max-mutantes 0`, en el scratchpad) | **28 muertos, 0 supervivientes, 0 timeouts**, 96,2 s |
| RED de T2 reproducida en worktree aislado | 14 failed, 2 passed, con los 4 casos R7 de `POSTV2`: auténtica |

**Checkpoints (pasada 1).** C1 [x] · C2 [x] una `in_progress`, [x] rama, [x]
ninguna `done` nueva, **[ ] `current.md` solo sesión activa** · C3 [x]
hexagonal, rutas en l. 1, sin `print`/TODO/secretos/dependencias, trampas de
dominio intactas · C3 bis N/A: no se toca `docs/referencia/` · C4 ter N/A: no
existe `harness/rutas_sensibles.json` · C4 [x] R1–R23 con test, offline, T10
con su `curl` · C4 bis [x] completo: RED real T1–T7, cobertura, totales y
muertos verificados, coste 6,2 s/mutante, **RM1** (medido en `dfe079d`) **RM2**
(28 × 6,2 ≈ 174 s) **RM3** (ninguno equivalente) **RM6** (ninguna guarda
quitada) en [x]; RM5 y campaña manual N/A (no hay equivalentes ni campaña
manual) · C5 [x] T1–T9 y T11 con commit; **T10 en `[ ]` por ser MANUAL
pendiente**, criterio de `review_F-002_fase1.md`.

**Encargo (pasada 1).** Ninguna obra se busca solo por código (`obra_por_codigo`
exige `empresa`, filtra en SQL y en Python; 5 llamadas la pasan). `POSTV2` en
empresas 1 y 28, en los dos órdenes. Ningún assert anterior cambia. Ningún
`.env`, ni red ni escrituras en tests. Límite de servicio respetado; D5 fuera.
`azure-apps/dedicacion.md` modificado **sin commit**: desviación 3 aceptada
(copiar entero borraba la corrección de `ruesma_rep`, `a40684f`). Desviaciones
1 y 2 (datos de los dobles), aceptadas.

### Cobertura requisito → test (`tests/test_f022_obra_por_empresa.py` del transfer, salvo R20–R21)

| R | Test(s) `test_f022_…` |
|---|---|
| R1 | `r1_dominio_…`, `r1_app_la_empresa_llega_al_dominio` |
| R2–R3 | `r2_reglas_*` ×5, `r2_pipeline_…_no_frena_a_las_demas`, `r3_reglas_…`, `r3_pipeline_…` (2 modos) |
| R4 | `r4_reglas_…`, `r4_pipeline_…_no_lee_nada`, `r4_app_…_es_422_sin_leer` |
| R5–R6 | `r5_cliente_sin_empresa_por_defecto`, `r5_app_ajustes_…`, `r6_cliente_…`, `r6_pipeline_sin_literales_…` |
| R7–R9 | `r7_cliente_postv2_…` ×4, `r8_cliente_*` ×4, `r8_app_obra_ambigua_es_502`, `r9_*` ×4 |
| R10–R14 | `r10_r11_pipeline_…` (2 modos), `r10_…`, `r11_reglas_…`, `r12_*` ×3, `r13_*` ×3, `r14_…` |
| R15–R19 | `r15_…` (empresas 1 y 28), `r16_…`, `r17_*` ×6, `r18_app_*` ×2, `r19_…` |
| R20–R21 | `services/dedicacion-api/tests/test_f022_empresa_en_linea.py`: `r20_*` ×2, `r21_*` ×4 |
| R22–R23 | `r22_…`, `r23_infra_sin_sigrid_empresa`, ancla en `test_f002_fuente_unica.py` |
| M1 | T10 MANUAL (humano), pendiente |

**Cambio requerido (pasada 1).** 1. `current.md` mezclaba sesiones y
contradecía a `features.json`: l. 7 «implementer en marcha», l. 155 «16
features» (hay 29), l. 172–176 «Lo siguiente» sin la dependencia de F-018 de
F-022 y F-026. Sin perder de vista T10 ni lo pendiente del humano.

**Observaciones (pasada 1).** (a) En los cortes R3/R11, `obra_destino` publica
la obra de entrada con `empresa: null`; proponía hacerlo en F-024. (b) Ojo al
merge de `features.json` con la rama de F-023. (c) Antes de `done`: T10 y el
commit en `azure-apps`; ruff +8 avisos. **Automejora propuesta**: C5 admite
`[ ]` en una MANUAL que esté en `current.md` con su comando; `harness.mutacion`
purga `__pycache__` y `.pytest_cache` antes de la línea base.

## Pasada 2 · incremental (`git diff ec2b0fa..HEAD`, HEAD `aec361e`)

- **Veredicto: APPROVED.**
- **Rigor `critico`** (declarado). Las puertas de código no se reevalúan: el
  delta no toca código (ver RM1). `init.sh` y la suite, enteros.

### Verificado ejecutando

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` tal cual | **ENTORNO LISTO**; 355 passed, 1 skipped; api/front/transfer verdes; COBERTURA [OK] 97,4 %; TAMAÑO [OK] |
| Ficheros del delta | solo `BACKLOG.md`, `harness/features.json`, `progress/{current,history,review_F-022}.md` |
| **RM1**: código desde el SHA medido (`git diff --stat dfe079d..HEAD` sobre `*.py`/`*.yaml`/…) | **vacío** |
| Alcance recalculado (`alcance_de_feature('F-022')`) | los mismos 10 ficheros de producción: la campaña 28/28 sigue valiendo |
| Estado real en `features.json` | F-022 `in_progress`; F-017 p1; F-018 y F-023 p2; F-025 y F-026 p3; F-024, F-027 y F-020 p4 |

### Cambio 1 de la pasada 1: resuelto

- Cabecera: «F-022 en review, pasada 2»; desaparece «implementer en marcha».
- «Estado del backlog (16 features)» ya no está; remite a `BACKLOG.md` con
  **29**, que es lo que imprime `init.sh`.
- «Lo siguiente»: prioridades idénticas a `features.json`; F-018 «requiere
  F-017 firmada, **F-022 y F-026** cerradas y autorización expresa».
- La sección del arnés 1.7.3 pasa **entera** a `history.md` (fechada, con nota
  de por qué se movió): no se pierde información.
- **T10 visible** con su `curl` exacto, solo lectura, lo que hay que comprobar
  y «NO se lanza `registro/ejecutar`», más «Resultado real: pendiente».
- **Pendiente del humano visible**: «Lo que espera al humano» 1 (T10) y 2
  (commit en `azure-apps` y decisión sobre `ruesma_rep`); «Para pasar a `done`
  faltan» nombra review, T10 con resultado y commit en `azure-apps`.

### Observaciones de la pasada 1: recogidas

- (a) **Recogida en F-024**: nota en su descripción y **criterio de
  aceptación nuevo** en `features.json`; `BACKLOG.md` regenerado y al día.
- (b) En `current.md`, con instrucción concreta (fusionar entradas sin
  reescribir el fichero) y puntero a «Hechos».
- (c) En «Para pasar a `done` faltan». Las dos automejoras, «propuestas al
  humano, pendientes de decisión», con la regla de propagación a `arnes-base`:
  la decisión es suya, no del líder.
- ruff +8 (185 → 193): era informativa y no pedía acción. Sugerencia: que la
  entrada de F-022 en `history.md` lo diga al cerrar.

### Checkpoints (pasada 2)

**C1** [x] `init.sh` código 0 · [x] ficheros base.
**C2** [x] una `in_progress` · [x] rama `feature/F-022-…` · [x] `current.md`
describe la sesión activa, sin contradicciones con `features.json` (ver
observación 1, no bloqueante) · [x] ninguna `done` nueva.
**C3, C3 bis, C4, C4 ter, C4 bis, C5**: sin cambios desde la pasada 1, porque
el delta no toca código, tests, specs ni `tasks.md`. Siguen en [x] con los
mismos N/A justificados (C3 bis: no se toca `docs/referencia/`; C4 ter: no
existe `harness/rutas_sensibles.json`; RM5: no hay equivalentes). T10 sigue en
`[ ]` y así debe estar.

### Observaciones nuevas (no bloqueantes; recoger al cerrar F-022)

1. `current.md` dice de F-023 «en `spec_ready`». Es cierto **en su rama**
   (`988f79e`), pero aquí y en `dev` figura `pending` en `features.json` y en
   `BACKLOG.md`. Precisarlo («`spec_ready` en su rama; en `dev`, `pending` hasta
   que se mergee»). Se resuelve en el mismo merge de la observación (b).
2. «**Bloquea F-018** (en curso, ver arriba)»: el «en curso» es de F-022, pero
   se lee como si lo fuera F-018, que está `pending`. Reescribir.
3. La sección «Revisión de negocio del 2026-09-29» es de la sesión anterior.
   Se tolera porque sus pendientes siguen vivos (y están en «Lo que espera al
   humano» 4); al cerrar F-022, pasarla a `history.md`.

### Para `done` (lo decide el líder)

T10 ejecutada por el humano con su resultado real en `current.md`, y el commit
del humano en `azure-apps`. La review ya no bloquea.
