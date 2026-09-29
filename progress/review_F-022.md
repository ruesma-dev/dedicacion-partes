Revisión completa (pasada 1) · `git diff dev..HEAD`, HEAD `ec2b0fa`
<!-- progress/review_F-022.md -->
# F-022 · Review · El transfer busca cada obra por código y empresa

- **Veredicto: CHANGES_REQUESTED**, solo por el rastro (`progress/current.md`,
  C2). El **código, los tests, la mutación y la documentación quedan
  aprobados**: basta con que la pasada 2 mire `current.md`.
- **Nivel de rigor:** `critico`, **declarado** en `features.json`. Exige
  C1–C5, C3 bis, tests trazables, RED con traza real, cobertura ≥ 80 %,
  mutación sin supervivientes y las `MANUAL (humano)` con su comando exacto
  (y con su resultado real antes de `done`).
- **Mutación REEJECUTADA** aunque declara 174 s (> 60 s): la 1.ª pasada del implementer dio falsos supervivientes.

## Verificado ejecutando, no leyendo

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` tal cual | **ENTORNO LISTO**; 355 passed, 1 skipped; api/front/transfer verdes |
| PUERTA COBERTURA / TAMAÑO | **[OK] 97,4 %** (76/78, umbral 80 %) / [OK] |
| Alcance recalculado (`harness.alcance`) | 10 ficheros, **226 líneas**, igual que el informe |
| Mutantes recalculados (`generar_mutantes`) | **28**, igual que el informe: mismos ficheros, líneas, operadores y textos |
| Campaña reejecutada (`--workers 1 --max-mutantes 0`, salida en el scratchpad) | **28 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 96,2 s**: coincide |
| Árbol tras la campaña | limpio: solo el `current.md` que editó el líder y el `explore_grafico_parte.md` ajeno |
| RED de T2 reproducida en un worktree aislado (código `3f4972d` + tests `147fd60`) | **14 failed, 2 passed**, con los 4 casos R7 de `POSTV2`. El informe dice 13: un test entró en el mismo commit después de la traza. Es auténtica |

## Checkpoints

**C1** — [x] `init.sh` sale con código 0 · [x] están los ficheros base.

**C2** — [x] una sola feature `in_progress` · [x] rama `feature/F-022-…` ·
[x] ninguna `done` nueva · **[ ] `current.md` describe solo la sesión
activa**: ver el cambio 1.

**C3** — [x] hexagonal: `domain/errores.py` no importa nada; reglas y
pipeline solo importan del dominio; el SQL vive en el cliente · [x] los
ficheros nuevos llevan su ruta en la primera línea · [x] ningún `print` salvo
en el script manual (permitido), ningún TODO, ningún secreto, ninguna
dependencia nueva · [x] trampas de dominio: la escala del porcentaje no se
toca; la postventa sigue imputando a la partida de la obra ORIGINAL (design
§4.4); no hay escrituras nuevas; `synckey`, `MAX(ide)+1` y el modo pruebas
siguen igual. Solo cambia el primer parámetro de la cabecera `con`.

**C3 bis** — N/A: no se toca `docs/referencia/`.
**C4 ter** — N/A: no existe `harness/rutas_sensibles.json`.

**C4** — [x] cada requisito de R1 a R23 tiene su `test_f022_rN_*` (tabla de
abajo), todos en verde · [x] offline: `_read` sustituido y `escribir` lanza si
se le llama; en la API, sesión y transfer falsos · [x] T10/M1 está en
`current.md` con su `curl` exacto.

**C4 bis** — [x] rigor declarado · [x] RED real de T1 a T7 (la de T2, además,
reproducida) · [x] cobertura [OK] · [x] totales verificados · [x] muertos
comprobados reejecutando · [x] coste por mutante = 174 × 1 ÷ 28 = 6,2 s,
por encima de 1 s · [x] ni «CAMPAÑA NO VÁLIDA» ni mutantes sin veredicto ·
[x] **RM1**: se midió sobre `dfe079d`; desde ahí solo cambian `progress/` y
`tasks.md`, nada del alcance · [x] **RM2**: 28 × 6,2 = 173,6 s ≈ 174 s; la
media (6,2 s) frente a las líneas base (16,0 y 9,0 s) no da un salto de orden
de magnitud (con -x y 28/28 muertos es lo esperable); 1 worker · [x] **RM3**:
revisados los 28, ninguno equivalente (el `or 1` de `:135` y `:144` lo cazan
los tests de ficha con `con.emp` nulo; el `> 2` de `:138`, el de dos fichas
en la misma empresa) · RM5: N/A, no se declara ningún equivalente · [x]
**RM6**: no se quitó ninguna guarda · campaña manual: N/A · [x] cero
supervivientes · [x] «Evidencias» trae los cuatro números y los workers ·
[x] ningún N/A sin motivo.

**C5** — [x] T1–T9 y T11 en `[x]`, con un commit `F-022 Tn:` cada una. **T10
sigue en `[ ]` y así debe estar**: es `MANUAL (humano)` y aún no se ha
ejecutado (mismo criterio que con T6 en `review_F-002_fase1.md`) · [x] no hay
artefactos sospechosos · [x] `features.json` dice `in_progress`, que es lo real.

## Lo que pedía el encargo

- **Ninguna obra se busca solo por código.** `obra_por_codigo` exige `empresa`,
  sin valor por defecto, y filtra `con.cod = ? AND con.emp = ?` con parámetros
  y además en Python. Sus 5 llamadas (origen, pruebas, postventa y dos del
  script) pasan la empresa. `obra_por_ide` lee `con.emp` y el pipeline la compara.
- **`POSTV2` en las empresas 1 y 28, en los dos órdenes**: `r7_cliente_…`, 2×2,
  con un doble que ignora el WHERE; en el pipeline, `r15_…`.
- **Ningún assert anterior cambia**: en `conftest.py`, `test_pipeline_offline.py`,
  `test_f002_fuente_unica.py` (solo `ANCLAS`) y `test_f003_esquema.py` (solo el
  argumento) no se toca ningún `assert`.
- **Ningún `.env`** (solo los `.env.example`), ni red ni escrituras en Sigrid
  en los tests. **Límite de servicio**: el front, `partida_*`, `text_match` y
  `recursos_de_empleados` no se tocan; **D5 no está implementada**.
- **`azure-apps/dedicacion.md`**: modificado y **sin commit** (` M`). El `diff`
  de los cuerpos no muestra ninguna diferencia de F-022, solo los 4 bloques
  que ya divergían (`ruesma_rep`, §5 ×2, §6 FQDN). Se acepta la desviación 3:
  copiar el fichero entero habría borrado la corrección de `ruesma_rep`
  (`a40684f`). Esa decisión es del humano.
- **Desviaciones 1 y 2** (datos de los dobles, design §7-§8): aceptadas.

## Cobertura requisito → test (`tests/test_f022_obra_por_empresa.py` del transfer, salvo R20–R21)

| R | Test(s) `test_f022_…` |
|---|---|
| R1 | `r1_dominio_…`, `r1_app_la_empresa_llega_al_dominio` |
| R2–R3 | `r2_reglas_*` ×5, `r2_pipeline_…_no_frena_a_las_demas`, `r3_reglas_…`, `r3_pipeline_ninguna_empresa_no_lee_ninguna_obra` (en los 2 modos) |
| R4 | `r4_reglas_…`, `r4_pipeline_…_no_lee_nada`, `r4_app_…_es_422_sin_leer` (en preflight y en ejecutar) |
| R5–R6 | `r5_cliente_sin_empresa_por_defecto`, `r5_app_ajustes_…`, `r6_cliente_busca_por_codigo_y_empresa`, `r6_pipeline_sin_literales_…` |
| R7–R9 | `r7_cliente_postv2_…` ×4, `r8_cliente_*` ×4, `r8_app_obra_ambigua_es_502`, `r9_*` ×4 |
| R10–R14 | `r10_r11_pipeline_obra_de_otra_empresa_se_omite` (2 modos), `r10_…`, `r11_reglas_…`, `r12_*` ×3, `r13_*` ×3, `r14_…` (2 modos) |
| R15–R19 | `r15_…` (empresas 1 y 28), `r16_…` (inexistente y ambigua), `r17_*` ×6, `r18_app_*` ×2, `r19_…` y la suite anterior en verde |
| R20–R21 | `services/dedicacion-api/tests/test_f022_empresa_en_linea.py`: `r20_*` ×2, `r21_*` ×4 |
| R22–R23 | `r22_la_regla_se_remite_no_se_reenuncia`, `r23_infra_sin_sigrid_empresa`, ancla en `test_f002_fuente_unica.py` |
| M1 | T10 MANUAL (humano), pendiente |

## Cambios requeridos

1. **`progress/current.md` (es del líder, no del implementer)** mezcla la
   sesión activa con estado antiguo que contradice a `features.json`. Es el
   mismo defecto que bloqueó `review_F-015.md` (cambio 2):
   - l. 7 `## F-022 · implementer en marcha`, cuando la l. 4 ya dice «en review».
   - l. 155 `## Estado del backlog (16 features)`: hay **29** (lo imprime
     `init.sh`) y la tabla no nombra ninguna de F-022 a F-031.
   - l. 172–176, «Lo siguiente»: pone F-017 y F-018 como n.º 1 y n.º 2, sin
     decir que F-018 depende ahora de F-022 **y** de F-026.
   Hay que actualizar esas secciones o pasarlas a `history.md`, sin que dejen
   de verse T10 y lo que el humano tiene pendiente de F-022 (el commit en
   `azure-apps` y la decisión sobre `ruesma_rep`).

## Observaciones no bloqueantes (a recoger, no solo a anotar)

- En los dos cortes tempranos (R3 y R11), `obra_destino` es la obra de ENTRADA,
  con `empresa: null`. Así lo fija design §2, pero en R11 se leería mejor si
  publicara el origen resuelto (empresa 28). Propuesta: hacerlo en F-024.
- La rama toca en `features.json` las entradas de F-018, F-023 y F-026: ojo
  al merge con la rama de F-023.
- Antes de `done`: T10 ejecutada, con su resultado real en `current.md`, y el
  commit del humano en `azure-apps`. ruff: 8 avisos más, del estilo que ya había.

## Automejora (propuesta, no aplicada)

- **`CHECKPOINTS.md`**: C5 pide todas las tareas en `[x]` y C4, que las
  `MANUAL (humano)` sigan pendientes. Se contradicen. Propuesta: C5 admite
  `[ ]` en una `MANUAL` que esté en `current.md` con su comando, y el paso a
  `done` exige su resultado.
- **`arnes-base`**: la primera campaña dio 2 falsos supervivientes que no se
  reproducen con la caché limpia. Propuesta: que `harness.mutacion` purgue
  `__pycache__` y `.pytest_cache` antes de la línea base y lo diga en el informe.
