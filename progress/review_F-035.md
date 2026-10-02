Revisión completa (pasada 1), `git diff dev...HEAD` con HEAD = `469cb2c0d0614b178c10bbc9b104b4c17f45a395`

# F-035 · Review del vaciado contra Azure sin `cmd.exe`

## Veredicto: CHANGES_REQUESTED (CAMBIOS PEDIDOS)

Código y tests correctos (verificado abajo). Bloquea **un solo punto de C4
bis**: la campaña manual no está en el repo como tabla reproducible. Es
papeleo, sin tocar código.

## Nivel de rigor

`estandar`, **declarado**: fase RED, cobertura y mutación con supervivientes analizados.

## Verificación propia (resultado real)

- `bash harness/init.sh`: **ENTORNO LISTO**, `402 passed, 1 skipped`;
  `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a
  dev)`; `PUERTA TAMAÑO … impl 219/220`.
- **Contraseña fuera de `az`**: en `vaciar_datos_prueba_dedicacion.ps1` las
  únicas `az` son `account set` y `postgres flexible-server show` (solo
  lectura). Azure: `psql -h $PG_FQDN -d $PG_DB -U $PG_APP_USER -v
  ON_ERROR_STOP=1 -c $sql`. `PGPASSWORD`/`PGSSLMODE` se ponen dentro del `try`
  de `Ejecutar-Sql` y se borran en su `finally`. Sin `rdbms-connect`.
- **`-SoloRecuento` no llega al TRUNCATE**: `if ($SoloRecuento) { … return }`
  al primer nivel, entre el recuento y `Ejecutar-Sql $SENTENCIA`; además
  `-Confirmar -SoloRecuento` → `throw` antes del plan. Combinando ambas,
  el TRUNCATE solo es alcanzable con `-Confirmar`.
- **Sin `-Confirmar` ni `-SoloRecuento` no conecta**: el `return` del plan va
  antes del `Get-Command psql`, de toda `az` y del `Read-Host`.
- **Nada de servidor**: sin `firewall-rule`/`update`/`restart`/`parameter`.
- **Control de caracteres antes de `az`** (`crear_base`, `add_secrets`):
  leído en el código. `Rechazar-CaracteresDeCmd` va justo tras leer cada
  secreto y antes de `-p $PGADMIN_PWD` (l. 143), de `$APP_PWD_SQL` (l. 128) y
  de `--value $val` (l. 91). Los pasos 1-2 de `crear_base` no llevan secreto.
- **No he ejecutado ningún `.ps1`** contra Azure ni contra la BBDD.

## Tests anteriores cambiados, fila a fila

`git diff dev...HEAD -- tests/`: solo `test_f026_vaciado.py` (los tres
declarados) y el nuevo `test_f035_secretos_sin_cmd.py`. Ninguno más.

| Test | ¿Pierde exigencia? |
|---|---|
| `…parametros_confirmar_y_local` | **No.** Sigue fijando la lista EXACTA y ordenada del `param(...)` hasta `)`; solo crece en `$SoloRecuento` |
| `…sin_confirmar_sale_antes_de_conectar` | **No.** Mismas tres comprobaciones (bloque, `return` al primer nivel, antes de `az`/`psql`/`Read-Host`). La invariante «sin `-Confirmar` no escribe» la completan `test_f035_r2_solo_recuento_sale_antes_del_vaciado` y `…_se_excluyen` |
| `…solo_en_la_base_dedicacion` | **No; gana.** Antes: «todo `psql` es localhost/dedicacion». Ahora: exactamente 2 `psql`, local `-d dedicacion`, Azure `-d $PG_DB -U $PG_APP_USER`, sin `flexible-server execute`, sin `PG_ADMIN`. `$PG_DB = "dedicacion"` (`00_vars`, l. 55) |

## Mutación

- **Herramienta**: alcance recalculado con `harness.alcance` → `lineas={}`
  (diff de `862d925` a la rama). **Prueba de control** (cero sospechoso):
  `generar_mutantes` sin la exclusión da 12 mutantes en `test_f026_vaciado.py`
  y 111 en `test_f035_…py`, ambos `es_produccion=False`: el cero es legítimo
  (solo cambian tests en Python; lo de producción es PowerShell).
- **Campaña manual del implementer** (19 mutantes, 0 supervivientes): su
  script (`mutps1.py`, scratchpad de la sesión, fuera del repo) existe y lo he
  **reejecutado entero sobre una copia** (`infra/` + `tests/` en el
  scratchpad): **19/19 MUERTOS**, cada uno por el test esperado. Ninguno es
  equivalente (RM3 ok): todos cambian comportamiento observable.
- **Mutantes propios** (copia, sin `-x`, todos muertos): `-and`→`-or` en la
  exclusión (1 fallo); `PGPASSWORD` antes del `try` (1); `PGSSLMODE=disable`
  (1); `-and`→`-or` en la salida del plan (2); sin control del admin (1);
  psql de Azure sin `-U` (2). `git status` limpio tras todo.
- **RM6**: M8 y M10 se mataron reforzando tests (`30c28c7` solo toca el test).
- **RM1**: medida en `30c28c7`; lo posterior solo toca `progress/`.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
**C2** [x] una sola `in_progress` (F-035) · [x] rama `feature/F-035-…` ·
[x] `current.md` coherente con el estado real (impl terminada, review lanzada,
tres tests declarados, MANUAL con comando exacto) · [x] F-026/F-034 en `history.md`.
**C3** N/A hexagonal: sin Python de producción (`.ps1`, README, tests) ·
[x] primera línea con ruta · [x] sin prints/TODOs/secretos/dependencias ·
[x] trampas de dominio: ninguna aplica (ni porcentajes, postventa ni Sigrid).
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] cada `acceptance` con test (tabla abajo) y en verde · [x] los tests
leen texto, sin red ni BBDD · [x] MANUAL en `current.md` con comando exacto,
_pendiente_ del humano.
**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] Fase RED: trazas reales de T1 (13 failed), T2 (7 failed), T3 (3 failed).
- [x] Cobertura: N/A **con motivo impreso** por `init.sh`.
- [x] Mutación automática: N/A justificado (alcance vacío, prueba de control hecha).
- N/A muertos/60 s, coste por mutante, «NO VÁLIDA», RM2: no hay informe de la herramienta (la manual, reejecutada 19/19).
- [x] RM1 · [x] RM6 · N/A RM5 (nivel `estandar`).
- **[ ] Campaña MANUAL con tabla reproducible.** El informe solo la describe
  con palabras («quitar del `finally` cada variable; …»). CHECKPOINTS: «Sin
  ese texto exacto el punto NO se marca». El texto exacto vive solo en un
  script del scratchpad de la sesión, que no es del repo y se borra: hoy lo he
  podido repetir yo; mañana no podría nadie.
- [x] Supervivientes analizados (0 al final; M8 y M10 explicados).
- [x] «Evidencias» con los cuatro números (mutación manual en serie, workers 1).
**C4 ter** N/A: sin `harness/rutas_sensibles.json`. **C5** N/A `tasks.md` (sdd=false) ·
[x] commits `F-035 Tn:` · [x] sin temporales · [x] `features.json` en `in_progress`.

## Cobertura de los `acceptance`

| Criterio | Tests |
|---|---|
| 1 psql en Azure, env en `finally`, FQDN por `show`, sin rdbms-connect | `test_f035_r1_*` (7) + `test_f026_r10_solo_en_la_base_dedicacion` |
| 2 `-SoloRecuento` | `test_f035_r2_*` (5) + `test_f026_r10_parametros_…`, `…sin_confirmar_…` |
| 3 mensaje de IP, nada de servidor | `test_f035_r3_*` (2) + `test_f026_r10_nada_fuera_…` |
| 4 rechazo antes de `az` | `test_f035_r4_*` (8: clase, mensaje, orden ×3, barrido) |
| 5 revisión en el README | `test_f035_r5_*` (3) |
| 6 test offline + declarados | este fichero de tests + tabla de arriba |
| 7 MANUAL | `current.md`, sección F-035 (pendiente del humano) |
| 8 review + init.sh | este informe |

## Cambios requeridos

1. Crear `progress/mutacion_manual_F-035.md` con **una fila por mutante**
   (M1–M19): fichero y línea en `30c28c7`, **texto exacto original → mutado**
   (el de `mutps1.py`), resultado y **número de fallos** (relanzar sin `-x`
   para contarlos), más las dos filas de la primera pasada (M8, M10) con su
   análisis. Incluir el comando o el script, y lanzarlo **sobre una copia**,
   no sobre `infra/` del árbol de trabajo.
2. En `progress/impl_F-035.md`, fila «Mutación manual» de «Evidencias»:
   enlazar ese fichero y sustituir el párrafo final «Mutantes: …» por el
   enlace (así el informe sigue dentro del tope de 220).

## Observaciones no bloqueantes (para el humano)

- **`)` también rompe `az.cmd`.** `az.cmd` expande `%*` dentro de un bloque
  `IF … ( … )`. Probado con un `.cmd` de estructura idéntica que solo imprime
  `argv` (sin Azure): `ab)cd` → «No se esperaba cd en este momento», no se
  ejecuta nada; `abc)` como último argumento → llega `abc` **truncado** y
  además corre la rama `ELSE` (exit 1). En estos scripts el secreto nunca es
  el último argumento, así que hoy da un fallo ruidoso con mensaje engañoso,
  no corrupción silenciosa. Propuesta: añadir `)` a la clase y al README §6 bis.
  Cambia la lista aprobada en el plan: decide el humano.
- El criterio 6 de `features.json` nombra un test y son tres (`current.md`
  ya lo explica): alinear ese texto al cerrar.

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md`, campaña MANUAL: que su tabla viva en
`progress/mutacion_manual_F-XXX.md`, fuera del tope del impl (219/220 aquí:
no cabía y acabó en prosa, justo lo que el punto prohíbe).
