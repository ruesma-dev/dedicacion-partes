<!-- progress/review_F-054.md -->
Revisión incremental desde e005e34 (pasada 2), HEAD `e65194e`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 2

**Veredicto: APROBADO (APPROVED).** Los dos bloqueos de la review 1 están
corregidos y las observaciones recogidas lo están de verdad, cada una con test.

**Rigor:** `critico`, declarado en `features.json`. Exige RED, cobertura,
mutación completa con 0 supervivientes, RM5 y MANUAL con comando exacto.

## Delta revisado (`git diff e005e34..HEAD`, 25 ficheros)

- **Bloqueo 1 (C4)** resuelto: `current.md` §«MANUAL pendientes (comando
  exacto)» trae T10 (`worktree add … ccad4db`, `curl …/health` con
  `modo_pruebas`, tres pasadas, Cancelar), T18 (el `curl` de `existentes` y
  los pasos, con O6 en el paso 2), T19 (`prueba_escritura_porcentajes.py
  estado --ano 2026 --mes 11`, sin marcar / marcando, ≤ 1,15 × T10) y T20
  (orden, `azure-apps` con `git -C … log -1 -- dedicacion.md`, aviso a `partes`).
- **Bloqueo 2 (C2)** resuelto: la sección de F-054 es la vigente (en review,
  O1-O6 decididas, mutación nueva); la de «spec REVISADA» y el `.venv` ya no
  están. Cabecera: F-054 `in_progress`, en review 2, MANUAL y `azure-apps`
  pendiente (T20) listados.
- **O1** recogida: `noqa` sobrantes fuera, `X | None`, imports ordenados, la
  fixture `api` reexportada con nombre (F811), `PonerACero` sin usar fuera
  (F401). `init.sh`: ruff 309, igual que `dev` (la review 1 midió 363).
  `impl_F-054.md` ya no dice «deuda previa». `Decimal("0")` → `Decimal(0)`
  trajo dos mutantes; uno era hueco real (test de R16 con `0.005` y `0.01`) y
  el otro se quitó al dejar `Decimal()` en la `Linea` de sondeo (no es guarda
  defensiva: RM6 no aplica).
- **O2** recogida (`reglas_obra_cero.py:52-56, 71, 76, 110`): la cobertura de
  una `Postv-` omitida es de postventa aunque `omitir` deje `destino="obra"`,
  también la de sus vinculados; en la obra de postventa cubre si su partida es
  la de la línea o 0. Tests: `test_f054_r31_o2_*` (4), incluido el lote de
  punta a punta con `POSTVENTA_REGISTRAR=false` (sale 7002, no 7001). Design
  §6.1 y ARCHITECTURE ajustados. Ver O7.
- **O4** recogida: `cubierta` sin `cod_pruebas`, firma del design igual.
- **O5** recogida: `api()` deja `status` en el error; comparar con 404/409 no
  avisa y aceptar sí; el aviso de registrar une los motivos y sale en rojo si
  hay omitidas. Tests `test_f054_o5_*` (front) y dos nuevos en `modal_cero`.
- **O3 y O6** aceptadas sin cambio por el humano; O6 queda en el paso 2 de T18.
- Hexagonal intacta: `_destino` vive en `application/services`; sin `print`,
  sin secretos, primera línea con ruta en todo lo tocado.

## Checkpoints

- **C1** [x] `init.sh` código 0, sin `[KO]`, con `suite_*.ok` borrados antes ·
  [x] ficheros previstos (más `mutacion_manual_F-054.md`, del rastro).
- **C2** [x] una `in_progress` · [x] rama `feature/F-054-sync-trae-porcentajes`
  (comprobada con `git -C`) · [x] `current.md` (bloqueo 2) · [x] history.
- **C3** [x] hexagonal · [x] primera línea · [x] sin `print`/TODO/secretos ·
  [x] escala sin cambios · [x] postventa con `es_postventa` · [x] solo escribe
  el transfer, `UPDATE` sin `DELETE` (delta no toca `poner_a_cero` salvo imports).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazables · [x] sin red ni BBDD · [x] MANUAL con comando exacto.
- **C4 bis** [x] rigor declarado · [x] RED real de O2, O4 y O5 en
  `impl_F-054.md` · [x] cobertura `[OK]` 99,5 % (748/752) · [x] totales
  recalculados: 21 ficheros, 1639 líneas, **266 mutantes**, coinciden ·
  [x] sin «CAMPAÑA NO VÁLIDA», sin veredicto 0 · [x] **campaña no
  reejecutada: 4837 s según el informe**; recálculo puro más RM y RM4 ·
  [x] 0 supervivientes, nada PENDIENTE · [x] Evidencias con los cuatro números.
- **RM1** [x] SHA `c70eb61`; `c70eb61..HEAD` solo toca `progress/`.
  **RM2** [x] 266 × 18,2 = 4841 ≈ 4837 s; 18,2 × 4 workers = 73 s frente a
  bases de 91-137 s, coherente con `-x`. **RM3** [x] ninguno de los muestreados
  es equivalente. **RM4** usada, copia `git archive` en el scratchpad, base
  60 passed: `frozen=True→False` 1 fallo; `(0, paride)→(1, paride)` 2;
  `titular and→or` 2; `"postventa" and→or c.paride` 2; `_destino(a.destino,
  a.es_postventa)→False` 2. Todos muertos. **RM5** N/A: no hay equivalentes
  declarados (el de `Decimal("0")` se eliminó del código, no se declaró).
  **RM6** [x] no se quitó ninguna guarda.
- **Manual `app.js`** [x] tabla por fila con texto exacto (campañas 3 y 4).
  Reproducidas en copia, base 30 passed: C4 (`[404, 409]→[409]`, 1 fallo,
  declara 1), C14 (`> 0→> 1`, 1, declara 1 en la campaña 4) y C7 (sin
  `sobrantes_a_cero`, 1, declara 1).
- **C4 ter** N/A: sin `harness/rutas_sensibles.json`.
- **C5** [x] tareas no MANUAL `[x]`, commits `F-054 Tn:`/`F-054 On:` · T10,
  T18-T20 `[ ]` por MANUAL, legítimo · [x] árbol limpio · [x] `in_progress`.

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R3 | `test_f054_r1_*` (front), `r2`, `r3`; O5: `test_f054_o5_*` |
| R4-R12 | `test_f054_lectura_mensuales`, `endpoint`, `traduccion` |
| R13-R18 | `test_f054_comparar` (R16 con `0.50` y `1.00`) |
| R19-R28 | `test_f054_aceptar`, `rutas`, `traer_front` |
| R29 | `test_f002_fuente_unica` y grep; `azure-apps`, T20 |
| R30, R37 | MANUAL T10, T18, T19 |
| R31-R34, R38 | `test_f054_obra_cero` (con `r31_o2_*`), `modal_cero` |
| R35-R36 | `test_f054_poner_a_cero`, `registro_cero`, `modal_cero` (`r35_o5_*`) |

Suites: api 1469, transfer 1849, front 488, raíz 418 (1 skipped).
**R37 sigue sin cifra** hasta T10/T19; si T19 supera el 15 %, PARA (§6.4).

## Observación para decidir (no bloquea; decidir, no dejar en «anotado»)

- **O7. Alcance real de O2.** `omitir` (`reglas_porcentajes.py:528`) no lleva
  `destino` ni `paride`, así que **cualquier** `Postv-` omitida tiene `paride
  = 0`, no solo la omitida antes de resolver la partida: también la omitida
  después (porcentaje fuera de rango, sin código mensual). Esa cubre todas las
  líneas de su recurso en la obra de postventa, no solo su partida. El error
  va en la dirección segura (menos sobrantes propuestas, nunca una escritura
  de más) y el caso es raro. Pero el texto de ARCHITECTURE y design §6.1
  («omitida antes de resolverla») y la frase «en real una `Postv-` resuelta a
  0 no existe» del informe lo describen más estrecho de lo que es. Opciones:
  (a) aceptarlo y corregir esa frase en los dos documentos; (b) que la
  cobertura de una omitida use la partida de postventa resuelta, si la hay.
  Decide el humano.

## Review 1 (pasada completa, `560c10a`): RECHAZADA, resumen

Solo por el rastro: bloqueo 1 (C4, MANUAL sin comando exacto en
`current.md`) y bloqueo 2 (C2, sección obsoleta). Juzgado sin bloqueos: la
parte B (guarda doble en `poner_a_cero.py` y en el SQL, solo `UPDATE … can =
0, tot = 0`, solo lo confirmado, fallo ⇒ sin `ejecutar`) y las desviaciones
nº 1, 6, 13, 14 y 16, aceptadas. Campaña 1 de mutación 262/262 en `c614be3`
(3767 s). Observaciones O1-O6, decididas por el humano el 2026-10-30:
recoger O1, O2, O4 y O5; aceptar O3 (la 0404 en modo real es sobrante
normal) y O6 (deshacer un `SIGRID` va por `reemplazar`; mirarlo en T18). El
detalle está en el historial de git de este fichero (`git show
e005e34:progress/review_F-054.md`).

## Cambios requeridos

Ninguno. Pendiente para cerrar: MANUAL T10, T18, T19 y T20 (con
`azure-apps/dedicacion.md` y el aviso a `partes`) y la decisión sobre O7.
