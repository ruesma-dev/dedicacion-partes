<!-- progress/review_F-032.md -->
Revisión incremental desde feff7e4 (pasada 2) · HEAD `713c8ac` · veredicto vigente al final: **CHANGES_REQUESTED**

# F-032 · Review — Nombres de empresa sincronizados desde Sigrid

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige C1–C5, C4
con tests trazables, fase RED, cobertura ≥ 80 % de lo cambiado y campaña de
mutación con supervivientes analizados. `sdd: false`: mini-spec = descripción +
`acceptance` (R1–R7); `tasks.md` N/A.

## Pasada 1 (resumen) · completa, base `56e79f3` .. `feff7e4`

**Veredicto: CHANGES_REQUESTED** solo por el rastro; código, tests y campaña bien.
Resumida por el tope de 140 líneas; el texto íntegro está en
`git show 6f1fa5a:progress/review_F-032.md`.

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
- Automejora propuesta: C4 de `CHECKPOINTS.md` con las copias pendientes a `azure-apps/`.

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

## Pasada 2 · incremental desde `feff7e4` hasta `713c8ac`

**Veredicto: CHANGES_REQUESTED** — `bash harness/init.sh` en **rojo**, causado por
el propio arreglo del cambio 1.

### Qué cambió
`git diff --stat feff7e4..HEAD`: solo `progress/current.md` (+33/−7) y
`progress/review_F-032.md` (el informe de la pasada 1). **Ningún cambio de código
ni de tests**: la campaña y la cobertura de la pasada 1 siguen valiendo (RM1: el
alcance medido no se ha movido).

### Verificación ejecutada
- `bash harness/init.sh` tal cual: **1 comprobación fallida**. La suite raíz para en
  `tests/test_f008_infra_sin_secretos.py::test_f008_r21_ningun_secreto_ni_identificador_en_el_repositorio`:
  `progress/current.md:35 [guid]` (61 passed, 1 failed, `-x`). El resto en verde:
  servicios api/front/transfer (caché del último verde, sin cambios de código),
  `PUERTA COBERTURA` 100 % (106/106), `PUERTA TAMAÑO` (review 132/140).
- Origen: la línea 35 de `current.md` lleva la ruta del scratchpad de la sesión del
  líder, que contiene el UUID de sesión `5cb867d0-…`. El guardián de F-008 no
  distingue un UUID de sesión de un ID de tenant, y **no debe**: la regla es no
  versionar GUIDs. Es un fallo real del rastro, no un falso positivo a silenciar.
- Script `verif_f032_empresas.ps1` leído entero: existe hoy, sin secretos, solo
  lecturas a Sigrid vía la API y escritura en la BBDD local; sus comprobaciones
  coinciden con lo que `current.md` declara (preview `empresas.leidas ≥ 19`, sync
  con bloque `empresas`, `/empresas` con por defecto 1, 18 y 31 con su nombre,
  ninguna «Empresa N», 3 empresas). `leidas` existe en `resumir_empresas`
  (`filtros_maestros.py:273`).
- Segundo problema del mismo comando: el script vive en el **scratchpad de una
  sesión** (`%TEMP%\claude\…\<sesión>\scratchpad`), fuera del repo y efímero. Un
  «comando exacto» que apunta a un fichero que puede desaparecer al cerrar la
  sesión no cumple C4 en la práctica.

### Cambio 1 de la pasada 1 (comando exacto) — hecho en contenido, mal en forma
Pasos 1 y 2 con arranque (`python main.py` desde `services/dedicacion-api`),
llamadas con URL completa, resultado esperado de cada una y selector en
`http://localhost:8080` con el literal nuevo de la empresa 1. Correcto, salvo la
ruta del script (ver cambios requeridos).

### Cambio 2 de la pasada 1 (copia a `azure-apps`) — hecho
Sección «Pendiente antes del `done`» con los cinco puntos del informe del
implementer (cabecera, fila de `sigrid-api` §1, árbol §2, `de_baja` en
`/empresas`, fila `auxemp` en «qué se rompe») y commit en `azure-apps`. `[x]`.

### Observaciones no bloqueantes — recogidas
- `strip` en el preview y `sync_en` solo al alta: **descartadas por escrito** en
  `current.md` l. 23–26, con motivo (preview diagnóstico, tabla con nombre limpio;
  `sync_en` igual que `trabajador`/`obra`). Aceptado.
- Literal de la empresa 1: en el paso 2 de la MANUAL y «se avisa al humano». `[x]`.
- Automejora: encargo `620b83d` en `arnes-base`. `[x]`.

### `current.md` frente a `features.json` (leído entero)
F-032 `in_progress`, `estandar`, `sdd: false`, rama correcta: coherente con «F-032
en review» (l. 4) y la fila «— F-032 en review» de la tabla. Sin restos
contradictorios: «Reviewer lanzado» de `feff7e4` sustituido por el estado de la
pasada 1 y «Pasada 2 lanzada». Sin secretos salvo el GUID ya dicho.

### Checkpoints (pasada 2, sobre el delta)
- **C1** **[ ] init.sh exit 0** — rojo por `current.md:35 [guid]`.
- **C2** [x] una sola `in_progress`, rama correcta, `current.md` de la sesión activa.
- **C3** [x] sin código nuevo; **[ ] sin secretos/identificadores**: el GUID de sesión.
- **C3 bis** N/A — no toca `docs/referencia/`.
- **C4** [x] tests de la pasada 1 intactos · **[ ] MANUAL con comando exacto**: apunta
  a un fichero efímero de un scratchpad (y es lo que rompe init.sh).
- **C4 bis** [x] sin cambios desde la pasada 1 (sin código no hay nada nuevo que medir).
- **C4 ter** N/A — sin rutas sensibles señaladas por init.sh.
- **C5** [x] commits `F-032:` de rastro; árbol limpio.

## Cambios requeridos
1. **`progress/current.md:35`**: quitar la ruta con el UUID de sesión y dejar el
   script en un sitio **durable** del que el comando no dependa de la sesión.
   Recomendado: versionarlo como `scripts/verif_f032_empresas.ps1` (ya existe
   `scripts/`; el script no lleva secretos ni GUIDs, revisado) y que el paso 1 diga
   `powershell -ExecutionPolicy Bypass -File scripts\verif_f032_empresas.ps1` desde la
   raíz del repo. Si el humano prefiere no versionarlo, la alternativa es una ruta
   sin GUID fuera del repo, nombrada con su motivo. En ambos casos, comprobar que
   `bash harness/init.sh` queda en verde **antes** de relanzar la review.
2. Con eso, la pasada 3 (incremental desde `713c8ac`) puede aprobar: el resto del
   delta está bien y no hay que volver a leer código.

## Propuesta de automejora (no aplicada)
- `leader.md` / `implementer.md`: «antes de lanzar la review, `bash harness/init.sh`
  en verde también tras tocar solo `progress/`». Esta pasada se rechaza por un
  commit de rastro que nadie pasó por init.sh; el guardián lo habría cazado gratis.
- Mismo sitio: los scripts de verificación MANUAL no viven en el scratchpad de la
  sesión (efímero y con UUID en la ruta); van a `scripts/` o equivalente.
