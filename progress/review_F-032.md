<!-- progress/review_F-032.md -->
Revisión incremental desde 713c8ac (pasada 3) · HEAD `075b4c8` · veredicto vigente: **APPROVED**

# F-032 · Review — Nombres de empresa sincronizados desde Sigrid

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige C1–C5, C4
con tests trazables, fase RED, cobertura ≥ 80 % de lo cambiado y campaña de
mutación con supervivientes analizados. `sdd: false`: mini-spec = descripción +
`acceptance` (R1–R7); `tasks.md` N/A.

## Pasada 1 (resumen) · completa, base `56e79f3` .. `feff7e4`

**Veredicto: CHANGES_REQUESTED** solo por el rastro; código, tests y campaña bien.
Texto íntegro: `git show 6f1fa5a:progress/review_F-032.md`.

- `init.sh` verde (raíz 355 passed, 1 skipped); suites sin caché: api 342, front 20,
  transfer 317 passed. `PUERTA COBERTURA` 100 % (106/106).
- Mutación: alcance recalculado = 11 ficheros, 258 líneas, **30 mutantes** (coincide
  con el informe); 2 supervivientes reales (`models.py:92` `frozen=True→False`,
  `orm_models.py:91` `nullable=False→True`), cazados con tests nuevos (`fe93a43`).
  Campaña no reejecutada: 118,2 s según el informe (> 60 s); recálculo + RM.
- C1, C2, C3 (hexagonal, regla «de baja» en dominio, front solo pinta), C3 bis N/A,
  C4 bis completo (RED real T1–T7, RM1 SHA `8160220…` con alcance de producción
  idéntico, RM2 coherente, RM3 sin equivalentes muertos, RM5/RM6 N/A justificados),
  C4 ter N/A, C5 `[x]`. Único `[ ]`: **C4 MANUAL sin comando exacto en `current.md`**.
- Desviación de F-024 verificada línea a línea: nada aflojado.
- Cambios pedidos: (1) comando exacto de la MANUAL con resultado esperado en
  `current.md`; (2) listar ahí la copia pendiente a `azure-apps/dedicacion.md`.
- Observaciones no bloqueantes: `resumir_empresas` sin `strip`; literal de la
  empresa 1 cambia a «CONSTRUCCIONES RUESMA»; `sync_en` solo al alta.

### Cobertura acceptance → tests (pasada 1, sin cambios)
| R | Tests (api salvo indicación) |
|---|---|
| R1 tabla ORM, lectura `auxemp` | `test_f032_r1_*` (ORM, `create_all` sin ALTER, alias de config, solo lectura, repo, pipeline, sync real) |
| R2 nombre de la tabla tras sync | `test_f032_r2_*`, `r2_r5_alta_cambio_de_nombre_y_baja_llegan_tras_el_sync`, `r2_r5_get_empresas_expone_nombre_y_baja` |
| R3 sin `empresas.nombres` | `test_f032_r3_*` (reserva «Empresa N», `config.yaml`, contenedor) |
| R4 preview | `test_f032_r4_*` |
| R5 de baja marcada, nunca oculta | `test_f032_r5_*` (dominio ×9, listado) y front `test_f032_r5_*` (×2) |
| R6 | MANUAL pendiente (no bloquea APPROVED, sí `done`) |
| R7 | esta review |

## Pasada 2 (resumen) · incremental `feff7e4` .. `713c8ac`

**Veredicto: CHANGES_REQUESTED.** Texto íntegro: `git show 075b4c8:progress/review_F-032.md`.
Delta solo en `progress/`. `init.sh` en **rojo**: el guardián de F-008
(`test_f008_r21_…`) cazó `progress/current.md:35 [guid]`, la ruta del scratchpad
de la sesión del líder con su UUID; además el script de la MANUAL vivía en un sitio
efímero. Cambios 1 y 2 de la pasada 1 hechos en contenido (comando con URL y
resultado esperado; copia pendiente a `azure-apps` listada). Observaciones de la
pasada 1 descartadas por escrito con motivo o avisadas: aceptado. Cambio pedido:
quitar la ruta con UUID y versionar el script (`scripts/verif_f032_empresas.ps1`),
con `init.sh` en verde antes de relanzar.

## Pasada 3 · incremental desde `713c8ac` hasta `075b4c8`

**Veredicto: APPROVED.** El cambio de la pasada 2 está hecho y `init.sh` queda verde.

### Qué cambió
`git diff --stat 713c8ac..HEAD`: `progress/current.md` (+8/−4),
`progress/review_F-032.md` (la pasada 2) y `scripts/verif_f032_empresas.ps1` (nuevo,
39 líneas). `git diff --stat 713c8ac..HEAD -- services tests`: **vacío**. Sin
cambios de código ni de tests de producción: campaña, cobertura y RM de la pasada 1
siguen valiendo (RM1: el alcance medido no se ha movido).

### Verificación ejecutada
- `bash harness/init.sh` tal cual: **ENTORNO LISTO**. Raíz `355 passed, 1 skipped`
  (incluye el guardián de F-008, ahora verde); api/front/transfer verdes (caché:
  árbol de servicios sin cambios desde el último verde, coherente con el diff
  vacío en `services/`); `PUERTA COBERTURA` 100 % (106/106); `PUERTA TAMAÑO` OK;
  ningún `.env` versionado; rama correcta. ruff 193 avisos, deuda previa.
- `grep` de GUID (`[0-9a-f]{8}-[0-9a-f]{4}-`) en `current.md` y en el script: **sin
  coincidencias**. La ruta del scratchpad ha desaparecido de `current.md`.
- Script leído entero. Primera línea con ruta (`# scripts/verif_f032_empresas.ps1`,
  tras el BOM UTF-8, que PowerShell 5.1 necesita para los acentos). Sin secretos,
  claves, cabeceras de autenticación ni IPs internas (solo el loopback
  `127.0.0.1:8090`). Llamadas: `GET /health`, `GET /sync/preview`, `POST /sync`,
  `GET /empresas`. **Ninguna** a `registro/ejecutar`, al transfer (8006) ni a Sigrid
  directo: Sigrid solo se lee a través de la api y `sigrid-api`; la única escritura
  es la del sync en la BBDD local. Termina con contador de fallos y resultado.
- Comando de `current.md` l. 38–39: `powershell -ExecutionPolicy Bypass -File
  scripts/verif_f032_empresas.ps1` «desde la raíz del repo». **Exacto y durable**:
  ruta relativa al repo, fichero versionado; idéntico al «Uso» de la cabecera del
  script.
- Coherencia comando ↔ script: lo que `current.md` declara (preview `empresas.leidas
  ≥ 19`; sync con bloque `empresas`; `/empresas` con por defecto 1, 18 =
  `RUESMA SERVICIOS SL`, 31 = `UTE RUESMA-INESCO TOLEDO`, ninguna «Empresa N», 3
  empresas) es exactamente lo que comprueban los siete `Ok` del script. `localhost`
  en el texto y `127.0.0.1` en el script apuntan al mismo sitio.

### `current.md` frente a `features.json` (leído entero)
F-032 `in_progress`, `estandar`, `sdd: false`, rama `feature/F-032-empresas-desde-sigrid`:
coherente con «F-032 en review» (l. 4), la fila «— F-032 en review» de la tabla y
el historial de pasadas (l. 19–30, ya con «Pasada 2: rechazada … Pasada 3 lanzada
con `init.sh` en verde»). MANUAL (pasos 1 y 2) y copia a `azure-apps` siguen
`_pendiente_`: correcto, no bloquean APPROVED, sí el `done`.

### Checkpoints (pasada 3, sobre el delta)
- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` (F-032) · [x] rama correcta · [x] `current.md` de
  la sesión activa y coherente con `features.json`.
- **C3** [x] sin código de producción nuevo · [x] script con primera línea con ruta,
  sin `print`/debug sobrante, sin secretos ni identificadores · [x] trampas de
  dominio: no escribe en Sigrid ni toca el transfer.
- **C3 bis** N/A — el delta no toca `docs/referencia/`.
- **C4** [x] tests de la pasada 1 intactos y en verde · [x] MANUAL en `current.md`
  con comando exacto, durable y resultado esperado de cada paso.
- **C4 bis** [x] sin cambios en `services/` ni `tests/` desde la pasada 1: nada nuevo
  que medir; la campaña verificada en la pasada 1 (30 mutantes, 2 supervivientes
  cazados, sin `PENDIENTE`) sigue siendo la del alcance actual.
- **C4 ter** N/A — init.sh no señala rutas sensibles en el delta.
- **C5** [x] commit `F-032:` de rastro · [x] árbol limpio (`git status` vacío) ·
  [x] `tasks.md` N/A (`sdd=false`).

### Observación no bloqueante (para recoger, no para dejar «anotado»)
- La última línea del script dice «Falta mirar el selector en http://localhost:8080
  (ver chat)». El chat no es durable: mejor «(ver paso 2 de la MANUAL en
  `progress/current.md`)». Cosmético; no afecta a lo que el script comprueba.

### Pendiente antes del `done` (no bloquea este APPROVED)
1. MANUAL pasos 1 y 2, con su resultado en `current.md`.
2. Copia a `azure-apps/dedicacion.md` y su commit allí.
3. Avisar al humano del cambio de literal de la empresa 1.

## Propuesta de automejora (no aplicada)
- `leader.md` / `implementer.md`: «antes de lanzar la review, `bash harness/init.sh`
  en verde también tras tocar solo `progress/`» (la pasada 2 se perdió por eso), y
  los scripts de verificación MANUAL van a `scripts/`, nunca al scratchpad de la
  sesión (efímero y con UUID en la ruta). Esta feature es el caso de libro.
