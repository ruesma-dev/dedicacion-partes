Revisión incremental desde 1ba7b84 (pasada 2), hasta HEAD `a7b7298`

# F-035 · Review del vaciado contra Azure sin `cmd.exe`

## Veredicto: APPROVED (APROBADO)

El único cambio pedido en la pasada 1 está cumplido y reproducido al pie de la
letra, y el `)` aprobado por el humano está en la clase, el mensaje, el test y
el README. `init.sh` en verde.

## Nivel de rigor

`estandar`, **declarado** en `harness/features.json`: fase RED, cobertura y
mutación con los supervivientes analizados.

## Pasada 1 (resumen; lo aprobado allí se da por bueno)

Revisión completa de `dev...469cb2c`. Código y tests correctos: el vaciado en
Azure usa `psql` con `PGPASSWORD`/`PGSSLMODE` puestos en el `try` y borrados en
el `finally`; `-SoloRecuento` sale antes del TRUNCATE; sin `-Confirmar` ni
`-SoloRecuento` no conecta; nada a nivel de servidor; el control de caracteres
va antes de toda `az` que lleva el secreto. Los tres tests cambiados de
`test_f026_vaciado.py` se verificaron fila a fila: ninguno pierde exigencia.
Reproduje los 19 mutantes y 6 propios: todos muertos. **Lo que bloqueaba**
(C4 bis) era que la campaña manual no estaba en el repo como tabla
reproducible. Como observación quedó que `)` también rompe `az.cmd`.

## Pasada 2 · Qué se ha verificado (resultado real)

- **`bash harness/init.sh`**: ENTORNO LISTO, `402 passed, 1 skipped`;
  `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a
  dev)`; tamaños dentro del tope.
- **Delta** `1ba7b84..HEAD`: `crear_base` y `add_secrets` (clase y mensaje),
  README §6 bis, `test_f035_secretos_sin_cmd.py`, `features.json` (criterios 4
  y 6), `current.md`, `impl_F-035.md` y el nuevo `mutacion_manual_F-035.md`.
  `vaciar_datos_prueba_dedicacion.ps1` no cambia, así que lo aprobado sobre él
  sigue en pie.
- **`)` en los dos scripts**: `-match '["&|<>^%)]'` y mensaje `" & | < > ^ % )`
  con el porqué (el bloque `IF ( … )` de `az.cmd`). Lo único que cambia es la
  función: las llamadas siguen en el mismo sitio, antes de la `az`.
  `CARACTERES_CMD` incluye `)` y el test del mensaje exige `% )` y `IF`. El
  README §6 bis lo explica. `(` sigue admitido, que es lo correcto: mi prueba
  de la pasada 1 con un `.cmd` de la misma estructura mostró que `(` no rompe
  nada.
- **Tests anteriores**: en el delta solo cambia el test propio de F-035.
  `git diff dev...HEAD -- tests/` sigue mostrando, como en la pasada 1,
  `test_f026_vaciado.py` (los tres declarados) y el nuevo de F-035. No hay
  más cambios sin declarar.
- **Rastro**: el criterio 6 de `features.json` ya nombra los tres tests y el 4
  incluye `)`. `current.md` está al día: ciclo 2, review 2 lanzada, las
  observaciones recogidas y la MANUAL con su comando exacto, pendiente. El
  commit `e9bc34a` de `arnes-base` existe.

## Mutación

- **Herramienta**: alcance vacío. En la pasada 1 hice la prueba de control:
  el cero es legítimo, porque lo único Python del diff son tests.
- **Campaña manual** (`progress/mutacion_manual_F-035.md`): tiene una fila por
  mutante con fichero:línea, **texto exacto original → mutado**, resultado,
  **nº de fallos sin `-x`** y los tests que lo matan. La tabla 2 recoge M8 y
  M10 de la primera pasada (sobreviven contra los tests de `b8189d3`), con su
  análisis. El script va incrustado y trabaja sobre una copia temporal.
- **Reproducción propia**: extraje el script del `.md` y lo lancé en sus dos
  modos (HEAD y `b8189d3`) sobre una copia en mi scratchpad. Las **23 filas
  salen idénticas byte a byte** a las del informe: 21/21 muertos (M20 y M21
  incluidos, cada uno con 1 fallo en `…rechaza_justo_los_caracteres_de_cmd`)
  y M8/M10 sobreviven 2/2 con los tests antiguos. `git status` limpio después.
- **RM3**: ningún mutante es equivalente. **RM6**: M8 y M10 se mataron
  reforzando tests, no quitando código. **RM1**: la campaña se midió en
  `301dfed`; después solo cambian `progress/` y `features.json`.

## Checkpoints

**C1** [x] init.sh termina con exit 0 · [x] están todos los ficheros del arnés.
**C2** [x] una sola feature `in_progress` · [x] rama `feature/F-035-…` ·
[x] `current.md` coherente con el estado real · [x] F-026 y F-034 en `history.md`.
**C3** N/A hexagonal: no hay Python de producción (`.ps1`, README, tests) ·
[x] primera línea con la ruta · [x] sin prints, TODOs, secretos ni
dependencias nuevas · [x] trampas de dominio: no aplica ninguna.
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] cada criterio `acceptance` tiene test y pasa · [x] los tests leen
texto, sin red ni BBDD · [x] la MANUAL está en `current.md` con su comando
exacto, pendiente del humano.
**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] Fase RED: trazas reales de T1 (13 failed), T2 (7), T3 (3) y T5 (4 failed).
- [x] Cobertura: N/A **con el motivo impreso** por `init.sh`.
- [x] Mutación automática: N/A justificado (alcance vacío, con prueba de control).
- N/A muertos/60 s, coste por mutante, «NO VÁLIDA» y RM2: no hay informe de la
  herramienta. La campaña manual la reejecuté entera (23/23 filas idénticas).
- [x] RM1 · [x] RM6 · N/A RM5 (nivel `estandar`).
- [x] **Campaña MANUAL con tabla reproducible**: texto exacto, nº de fallos y
  dos filas o más reproducidas (todas).
- [x] Supervivientes analizados (0 al final; M8 y M10 explicados).
- [x] «Evidencias» con los cuatro números y el enlace a la tabla.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** N/A `tasks.md` (sdd=false) · [x] commits `F-035 Tn:` · [x] sin
temporales · [x] `features.json` en `in_progress`, a la espera del cierre.

## Cobertura de los `acceptance`

| Criterio | Tests |
|---|---|
| 1 psql en Azure, entorno en `finally`, FQDN por `show`, sin rdbms-connect | `test_f035_r1_*` (7) + `test_f026_r10_solo_en_la_base_dedicacion` |
| 2 `-SoloRecuento` | `test_f035_r2_*` (5) + `test_f026_r10_parametros_…` y `…sin_confirmar_…` |
| 3 mensaje de IP, nada del servidor | `test_f035_r3_*` (2) + `test_f026_r10_nada_fuera_…` |
| 4 rechazo antes de `az`, con `)` | `test_f035_r4_*` (8: clase, mensaje, orden ×3, barrido) |
| 5 revisión en el README | `test_f035_r5_*` (3) |
| 6 test offline + tres declarados | `test_f035_secretos_sin_cmd.py` + la tabla de la pasada 1 |
| 7 MANUAL | `current.md`, sección F-035 (pendiente del humano) |
| 8 review + init.sh | este informe |

## Cambios requeridos

Ninguno.

## Pendiente para cerrar (lo lleva el líder, no bloquea)

- La **MANUAL** del humano (`-Local -SoloRecuento` y `-SoloRecuento` contra
  Azure) sigue pendiente. Es la única prueba de que la contraseña llega
  entera a Azure.
- Queda la observación del implementer sobre el orden de `crear_base`: los
  pasos 1 y 2 van antes de pedir las contraseñas. Hay que proponérsela al
  humano.
