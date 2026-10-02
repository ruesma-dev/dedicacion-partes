Revisión incremental desde 2cc752a (pasada 3), hasta HEAD `1b9cd09`

# F-035 · Review del vaciado contra Azure sin `cmd.exe`

## Veredicto: APPROVED (APROBADO)

El ciclo 3 cumple los dos criterios nuevos. La contraseña del Key Vault es solo
salida de `az`, el respaldo funciona y cada aviso sale solo cuando la salida de
`psql` lo respalda. Los dos tests propios que cambian están declarados y
ninguno pierde exigencia. La campaña manual sale idéntica al reproducirla.

## Nivel de rigor

`estandar`, **declarado**: fase RED, cobertura y mutación con los
supervivientes analizados.

## Pasadas anteriores (resumen; lo aprobado se da por bueno)

- **Pasada 1** (`dev...469cb2c`), CAMBIOS PEDIDOS. El código ya estaba bien:
  `psql` en Azure, `-SoloRecuento`, nada del servidor y el control de
  caracteres antes de `az`. Los tres tests cambiados de F-026 se verificaron
  fila a fila. Faltaba la tabla reproducible de la campaña manual (C4 bis).
- **Pasada 2** (`…2cc752a`), APROBADO. Tabla hecha (23/23 filas idénticas al
  reproducirla) y `)` en la clase.

## Pasada 3 · Qué se ha verificado (resultado real)

- **`bash harness/init.sh`**: ENTORNO LISTO, `418 passed, 1 skipped`;
  `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a
  dev)`; tamaños dentro de los topes.
- **Delta**: `vaciar_datos_prueba_dedicacion.ps1`, README §3 bis, el test
  propio de F-035, `features.json` (criterios 9 y 10), `current.md`,
  `impl_F-035.md` y `mutacion_manual_F-035.md`. `crear_base` y `add_secrets`
  no cambian. Está el merge `b4b8877` a `dev` tras la review 2: por eso
  `dev...HEAD` ya solo muestra el ciclo 3 (`current.md` lo dice).
- **La contraseña del KV es solo salida**:
  `$valor = az keyvault secret show --vault-name $KV --name PG-PASSWORD --query
  value -o tsv 2>$null`. Ningún `$CLAVE`, `$valor` ni `$sec` aparece en la
  línea de comandos de `az` o `psql`; va solo a `PGPASSWORD` dentro del `try`.
  No se imprime ni ella ni su longitud: los mensajes nombran `PG-PASSWORD` y
  `$KV`, nunca el valor. `$valor = $null` en el `finally`.
- **Va después de la salida del plan**: en la sección «2) Credenciales», rama
  Azure, bajo `if ($KV)`. El `return` del plan y la sección 1 (`account set`,
  FQDN) van antes. Sin `-Confirmar` ni `-SoloRecuento` sigue sin tocar `az`.
- **El respaldo funciona, ejecutado** (bloque de credenciales en PowerShell,
  con `az` y `Read-Host` falsos, sin Azure). KV correcto: usa su valor, sin
  `Read-Host`. `az` con exit 1, `$KV` vacío (sin llamar a `az`), dos líneas o
  salida vacía: los cuatro caen a `Read-Host`.
- **Los patrones de los avisos tienen sentido**. `password authentication
  failed` y `no pg_hba.conf entry` los escribe el servidor (Azure, en inglés):
  valen como literales. El tiempo agotado lo escribe el cliente y en Windows en
  español llega traducido: de ahí `tiempo`. La contraseña va en el `if` y el
  firewall en el `elseif`, así que nunca salen los dos; ante otro error no hay
  pista, pero sale la salida entera de `psql`.
- **Tests anteriores cambiados**: en el delta solo cambia
  `test_f035_secretos_sin_cmd.py`. `test_f026_vaciado.py` sigue como se aprobó
  en la pasada 1. Las dos filas nuevas de la tabla del impl:

| Test | ¿Pierde exigencia? |
|---|---|
| `test_f035_r1_fqdn_por_show_de_solo_lectura` | **No.** La lista cerrada de `az` admitidas crece solo en `keyvault secret show`, que es lectura. Su forma exacta (una sola línea, argumentos exactos, `$valor =`) la fija `test_f035_r7_lee_pg_password_del_key_vault`. El resto del test, igual |
| `test_f035_r3_el_error_de_azure_apunta_a_la_ip_propia` | **No.** Mismas frases exigidas («tu IP no tenga acceso», «regla de firewall de tu IP», «NO … toca»). Exige además que el aviso esté dentro de la rama Azure y que el mensaje base no hable de IP. Que sea condicional lo fijan los `test_f035_r8_*` |

- **Rastro**: `current.md` cuenta la MANUAL 1 fallida y su causa (10 frente a
  14 caracteres), el ciclo 3 aprobado y hecho, los dos tests declarados y la
  MANUAL que hay que repetir. Coincide con `features.json` (`in_progress`,
  criterios 9 y 10) y con el impl.

## Mutación

- **Herramienta**: alcance vacío. El cero es legítimo (prueba de control de la
  pasada 1).
- **Campaña manual** (31 mutantes, en `4e34f3b`): script extraído del `.md` y
  ejecutado sobre una copia en sus dos modos. Las **33 filas salen idénticas**:
  31/31 muertos, M22–M31 incluidos (KV, respaldo, guarda `$KV`,
  `$LASTEXITCODE`, avisos, patrones, plan, contraseña como argumento de
  `psql`), y M8/M10 sobreviven 2/2 contra los tests de `b8189d3`.
- **Mutantes míos** (copia, todos muertos): `$($CLAVE.Length)` entre comillas
  (2 fallos), `Write-Host $CLAVE.Length` (1), firewall que casa la contraseña
  (4), `--password $CLAVE` en el KV (3), sin `"Continue"` (1). `git status` limpio.
- **RM3**: ningún mutante es equivalente. **RM6**: no se quitó código
  defensivo. **RM1**: medida en `4e34f3b`; lo posterior solo toca `progress/`
  y `features.json`.

## Checkpoints

**C1** [x] init.sh termina con exit 0 · [x] están los ficheros del arnés.
**C2** [x] una sola feature `in_progress` · [x] rama `feature/F-035-…` ·
[x] `current.md` coherente · [x] F-026 y F-034 en `history.md`.
**C3** N/A hexagonal: no hay Python de producción (`.ps1`, README, tests) ·
[x] primera línea con la ruta · [x] sin prints, TODOs, secretos ni
dependencias · [x] trampas de dominio: no aplica ninguna.
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] los 10 criterios tienen test y pasan · [x] los tests leen texto,
sin red ni BBDD · [x] MANUAL en `current.md` con su comando exacto, pendiente
de repetir.
**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] Fase RED con salida real: T8 (13 failed) y T9 (1 failed), además de las
  de los ciclos 1 y 2.
- [x] Cobertura: N/A **con el motivo impreso** por `init.sh`.
- [x] Mutación automática: N/A justificado (alcance vacío, con prueba de control).
- N/A muertos/60 s, coste por mutante, «NO VÁLIDA» y RM2: no hay informe de la
  herramienta. La campaña manual la reejecuté entera (33/33 filas).
- [x] RM1 · [x] RM6 · N/A RM5 (nivel `estandar`).
- [x] Campaña MANUAL con tabla reproducible: texto exacto y nº de fallos, todas
  las filas reproducidas.
- [x] Supervivientes analizados (0 al final; M8 y M10 explicados).
- [x] «Evidencias» con los cuatro números.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** N/A `tasks.md` (sdd=false) · [x] commits `F-035 Tn:` · [x] sin
temporales · [x] `features.json` en `in_progress`, a la espera de la MANUAL.

## Cobertura de los `acceptance`

| Criterio | Tests |
|---|---|
| 1 psql en Azure, entorno en `finally`, FQDN por `show` | `test_f035_r1_*` (7) + `test_f026_r10_solo_en_la_base_dedicacion` |
| 2 `-SoloRecuento` | `test_f035_r2_*` (5) + `test_f026_r10_parametros_…` y `…sin_confirmar_…` |
| 3 aviso de IP, nada del servidor | `test_f035_r3_*` (2) + `test_f026_r10_nada_fuera_…` |
| 4 rechazo antes de `az`, con `)` | `test_f035_r4_*` (8) |
| 5 revisión en el README | `test_f035_r5_*` (3) |
| 6 test offline + tests declarados | tabla del impl (5 filas), verificada fila a fila |
| 9 contraseña del Key Vault, con respaldo | `test_f035_r7_*` (8) |
| 10 avisos condicionales | `test_f035_r8_*` (8) |
| 7 MANUAL / 8 review | `current.md` (repetición pendiente) / este informe |

## Cambios requeridos

Ninguno.

## Observaciones no bloqueantes

- Si `PG-PASSWORD` llevara caracteres no ASCII, PowerShell 5.1 podría
  decodificar mal la salida de `az`, porque la lee con la página de códigos de
  la consola. Si pasa, el error diría «la contraseña no coincide con
  PG-PASSWORD», que es la pista correcta. La MANUAL lo dirá con la contraseña
  real.
- Queda pendiente la repetición de la MANUAL antes del `done`. Es la única
  prueba de que el valor del Key Vault llega entero a `psql`.
