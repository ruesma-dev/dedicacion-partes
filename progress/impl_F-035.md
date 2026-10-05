# F-035 · Informe del implementer

Rama `feature/F-035-vaciado-psql-azure`, rigor **estándar**, sin spec (contra
los `acceptance` de `harness/features.json`). Commits: ciclo 1 `fc57b7f` T1
(psql + `-SoloRecuento`), `33b5e9b` T2 (control de caracteres), `b8189d3` T3
(README), `30c28c7` T4 (tests reforzados); ciclo 2 `301dfed` T5 (`)`),
`cffd850` T6 (tabla de mutación); ciclo 3 `5a1eb13` T8 (Key Vault y avisos),
`5686670` + `4e34f3b` T9 (README y su test), `ced27af` T10 (mutación).

**Ningún script se ha ejecutado** contra Azure ni contra la base local. Solo el
analizador de PowerShell (`Parser]::ParseFile`: 0 errores en los tres `.ps1`),
la función de control extraída por AST y las condiciones de los avisos
evaluadas con `-match` sobre textos inventados.

## Qué cambió

**`infra/vaciar_datos_prueba_dedicacion.ps1`**
- Azure usa `psql -h $PG_FQDN -d $PG_DB -U $PG_APP_USER -v ON_ERROR_STOP=1 -c
  $sql`; FQDN por `az postgres flexible-server show … -o tsv` (solo lectura;
  vacío ⇒ para). Fuera `rdbms-connect` y `az … execute`.
- `PGPASSWORD` (los dos modos) y `PGSSLMODE=require` (solo Azure) dentro del
  `try` de `Ejecutar-Sql`, borrados en su `finally`. `psql` comprobado en los
  dos modos antes de pedir nada.
- `-SoloRecuento`: cuenta y `return` antes del vaciado, con y sin `-Local`.
- **Ciclo 3.** En Azure la contraseña se lee con `$valor = az keyvault secret
  show --vault-name $KV --name PG-PASSWORD --query value -o tsv 2>$null`
  (salida de `az`, nunca argumento), dentro de `if ($KV)`, en la sección
  «2) Credenciales»: después de la salida del plan. Se acepta solo si
  `$LASTEXITCODE -eq 0` y es una cadena; si no (sin `$KV`, sin permiso, vacía)
  avisa y vuelve al `Read-Host -AsSecureString`. No imprime ni la contraseña ni
  su longitud. El plan dice de dónde sale. En local, sin cambios.
- **Ciclo 3.** El error de `psql` en Azure construye `$mensaje` y añade una
  pista solo si la salida la respalda: `password authentication failed` ⇒ «la
  contraseña no coincide con … PG-PASSWORD en el Key Vault»; si no, `timeout|
  timed out|tiempo|pg_hba\.conf` ⇒ «tu IP no tenga acceso… regla de firewall de
  tu IP. Este script NO la crea ni la toca». Otro error: sin pista.

**`crear_base` / `add_secrets`** — solo añadidos: `Rechazar-CaracteresDeCmd`
(`-match '["&|<>^%)]'` → `throw` con el porqué, sin imprimir el valor) tras
leer cada secreto. Ejecutada aislada: rechaza `a"b a&b a|b a<b a>b a^b a%b
ab)cd abc)`, acepta `Abc123.x-y_z~ a(b comilla'simple x!y=z+/`.

**`README_dedicacion.md`** — §3 bis: `$env:Path`, `-SoloRecuento`, psql y
acceso desde tu IP en Azure y (ciclo 3) contraseña del Key Vault con el rol
Key Vault Secrets User u Officer y respaldo a mano. §6 bis: `cmd.exe`, el `)`
y la tabla de la revisión. §7: fila del vaciado.

## Decisiones de diseño

1. **`-SoloRecuento` conecta sin `-Confirmar`** (solo lee); sin ninguno de los
   dos no conecta a nada. Juntos ⇒ `throw` antes del plan.
2. **`PGSSLMODE` se borra en el `finally`** aunque estuviera puesto de antes,
   como ya pasaba con `PGPASSWORD`.
3. **`add_secrets` controla los tres valores** (los tres van por `--value`);
   un rechazo corta el bucle y lo ya guardado queda guardado.
4. **`crear_base`: control tras leer cada contraseña** sin mover nada más; sus
   pasos 1-2 siguen antes de pedir credenciales (observación ya en `current.md`).
5. **Ciclo 3, patrones de los avisos.** `password authentication failed` y
   `no pg_hba.conf entry` los escribe el **servidor** (Azure, en inglés): se
   buscan literales (`pg_hba\.conf`). El tiempo agotado lo escribe el
   **cliente**: libpq da `timeout expired` (con `connect_timeout`) o
   `Connection timed out`, y en un Windows en español el texto de Winsock
   llega traducido («…tras un periodo de tiempo…»): de ahí `timeout|timed
   out|tiempo`. La contraseña se mira **primero** (`if`), el firewall en el
   `elseif`: nunca salen los dos. `-match` no distingue mayúsculas.
6. **Ciclo 3, lectura del Key Vault.** `ErrorActionPreference = "Continue"`
   solo alrededor de la llamada (si no, en PS 5.1 un fallo de `az` cortaría el
   script en vez de caer al respaldo) y `$valor = $null` en el `finally`. Va
   tras `az account set` (sección 1), así que lee de la suscripción correcta.

## Tests anteriores que cambian (declarados)

Ninguno pierde exigencia; ninguno más cambia.

| Test | Antes → ahora | Motivo |
|---|---|---|
| `test_f026_r10_parametros_confirmar_y_local` | `param($Confirmar, $Local)` → `+ $SoloRecuento` | tercer conmutador |
| `test_f026_r10_sin_confirmar_sale_antes_de_conectar` | busca `if (-not $Confirmar) {` → `if (-not $Confirmar -and -not $SoloRecuento) {`; resto igual (`return` al primer nivel, antes de toda `az`/`psql`/`Read-Host`: la lectura del Key Vault también queda detrás) | `-SoloRecuento` conecta sin `-Confirmar` |
| `test_f026_r10_solo_en_la_base_dedicacion` | `az … execute -d $PG_DB` → exactamente 2 `psql` (local `-d dedicacion`; Azure `-d $PG_DB -U $PG_APP_USER`) | Azure pasa a psql |
| `test_f035_r1_fqdn_por_show_de_solo_lectura` (ciclo 3) | `az` admitidas: `account set`, `flexible-server show` → `+ keyvault secret show` (sus argumentos exactos los fija `test_f035_r7_lee_pg_password_del_key_vault`) | lectura de PG-PASSWORD |
| `test_f035_r3_el_error_de_azure_apunta_a_la_ip_propia` (ciclo 3) | el aviso iba en el `throw` de Azure → va en el bloque `if (-not $Local)` que suma a `$mensaje`; mismas frases | avisos condicionales |

El barrido `-p $`/`--value $` no cambia: la lectura del Key Vault no lleva
ninguno de los dos.

## Tests nuevos: `tests/test_f035_secretos_sin_cmd.py` (44)

R1 (7) psql/FQDN/`finally`; R2 (5) `-SoloRecuento`; R3 (2); R4 (8) clase,
mensaje, orden ×3, barrido; formato (3); R5 (3) README; **R7 (8)** lectura del
Key Vault exacta, tras la salida del plan y en la rama Azure bajo `if ($KV)`,
respaldo a `Read-Host`, local sin cambios, ninguna contraseña como argumento,
no se imprime, plan y §3 bis; **R8 (8)** avisos condicionales, sus patrones
evaluados sobre seis salidas de psql (tiempo, timeout, tiempo en español,
pg_hba, contraseña, otro) y orden contraseña → firewall.

## Fase RED (comando y salida real)

**T1** `python -m pytest tests/test_f035_secretos_sin_cmd.py -q -p no:cacheprovider`:

```
E            postgres flexible-server execute -n $PG -u $PG_APP_USER -p $CLAVE -d $PG_DB --querytext $sql --only-show-errors 2>&1 | Out-String
E       AssertionError: ['$salida = psql -h localhost -d dedicacion -U $USUARIO -v ON_ERROR_STOP=1 -c $sql 2>&1 | Out-String']
E       AssertionError: if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
E       AssertionError: falta la salida sin -Confirmar ni -SoloRecuento
E       AssertionError: falta el rechazo de -Confirmar con -SoloRecuento
13 failed, 1 passed in 0.55s
```

Tras el código: `14 passed`. **T2** (mismo comando, R4 añadidos):

```
E       AssertionError: falta la funcion Rechazar-CaracteresDeCmd en crear_base_dedicacion.ps1
E       AssertionError: falta la funcion Rechazar-CaracteresDeCmd en add_secrets_dedicacion.ps1
E       AssertionError: (27, 75, 41)      # crear_base, la del admin (lectura, control ausente, primera az)
7 failed, 18 passed in 0.52s
```

Tras el código: `25 passed`. **T3** (`-k r5`): `assert '-SoloRecuento' in '### 3
bis …'`, `AssertionError: cmd.exe` → `3 failed, 25 deselected`; luego `3 passed`.
**T5** (`-k r4`, ciclo 2): `AssertionError: )` en
`re.compile('["&|<>^%]').search('abc)123')` (×2) → `4 failed, 4 passed`; luego
`28 passed`.

**T8** (ciclo 3, mismo comando, script sin tocar):

```
E       AssertionError: []                                         # r7_lee_...: ninguna linea con keyvault
E       AssertionError: (112, 112, 71)                             # respaldo: no hay lectura del KV
E       AssertionError: el origen de la contrasena se anuncia en el plan, para Azure
E       AssertionError: assert set() == {'clave', 'firewall'}      # avisos sin condicion
E       KeyError: 'clave'                                          # x6, cada salida de psql
E       AssertionError: (22, 22)                                   # contrasena antes que firewall
13 failed, 30 passed in 0.53s
```

Tras el código: `43 passed`. **T9** (`-k 3_bis`): `AssertionError: assert None`
(sin Key Vault en §3 bis) → `1 failed`; tras el README, `1 passed`.

## Ciclos 2 y 3

- **Ciclo 2** (review 1): `)` en la clase y el mensaje (T5); tabla
  reproducible de la mutación manual en su propio fichero (T6).
- **Ciclo 3** (MANUAL 1 fallida por una contraseña mal tecleada, y el aviso de
  firewall salió igual): contraseña del Key Vault con respaldo, avisos
  condicionales (T8), §3 bis (T9) y 10 mutantes nuevos M22–M31 (T10).

## Resultado real de `bash harness/init.sh` (final del ciclo 3, con este informe)

```
418 passed, 1 skipped in 67.41s (0:01:07)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)
[OK] PUERTA TAMAÑO: F-035 dentro de los topes (impl 209/220, review 124/140)
ENTORNO LISTO. Puedes trabajar.
```

`ruff` del test: limpio (una pasada previa dio 201 avisos por una variable sin
usar en un test nuevo; quitada, vuelve a los 200 de deuda previa).

## MANUAL (la hace el humano; NO escribe nada)

Consola de PowerShell **nueva**, con `az login` hecho para la de Azure:

```powershell
cd C:\Users\pgris\PycharmProjects\porcentajes\infra
$env:Path = "C:\Program Files\PostgreSQL\16\bin;$env:Path"
. .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1

# 1) Local: pide la contrasena de 'postgres' (o de $env:PGUSER) en localhost
.\vaciar_datos_prueba_dedicacion.ps1 -Local -SoloRecuento

# 2) Azure: NO pide contrasena, la lee de PG-PASSWORD en el Key Vault
.\vaciar_datos_prueba_dedicacion.ps1 -SoloRecuento

# 3) Despues de cada uno, el entorno queda limpio (esperado: False False)
Test-Path Env:PGPASSWORD ; Test-Path Env:PGSSLMODE
```

**Esperado en 1)**: plan «-SoloRecuento: SOLO LECTURA», `=== 1) Conexion ===`,
contraseña, `=== 3) Filas antes del vaciado ===` con una fila de `psql`
(asignacion, evento, periodo, trabajador) y `=== SOLO RECUENTO: hecho, no se ha
escrito nada ===`. Ninguna sección «4) Vaciado».

**Esperado en 2)**: el plan dice «Contrasena: la de PG-PASSWORD en el Key
Vault…»; `Servidor: <fqdn> (psql con PGSSLMODE=require)`; en «2) Credenciales»,
`Contrasena de 'dedicacion_app': se lee de PG-PASSWORD en el Key Vault <kv> (no
se imprime).` y **ninguna petición de contraseña**; luego el recuento
(`trabajador` ≈ 196 tras el sync del 2026-10-02) y «SOLO RECUENTO: hecho».
Si sale `AVISO: no he podido leer PG-PASSWORD…`, te falta el rol Key Vault
Secrets User u Officer sobre el Key Vault y la pide a mano. Si psql falla, el
mensaje solo habla de la contraseña ante `password authentication failed` y
solo de la regla de firewall de tu IP ante tiempo agotado o `no pg_hba.conf
entry`.

## Fuera del alcance / pendiente

- Fuera: volver a vaciar producción, la contraseña de `dedicacion_app`, el
  servidor y su firewall, los permisos del Key Vault, `azure-apps`.
- `current.md` y `features.json` sin tocar (los lleva el líder).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (suite de `init.sh`) | **418 passed, 1 skipped**; los 44 de `test_f035_secretos_sin_cmd.py` en verde |
| Cobertura de líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. Lo cambiado es PowerShell y Markdown |
| Mutantes (`python -m harness.mutacion --feature F-035`) | **N/A**: «ALCANCE VACÍO en F-035… No se escribe informe». La herramienta solo muta Python |
| Mutación manual de los `.ps1` (sustituto) | **31 mutantes, 0 supervivientes** (sobre copia, sin `-x`, en `4e34f3b`). Primera pasada: M8 (hueco real) y M10 (casi equivalente) sobrevivían; tests ajustados en `30c28c7`, y reproducido contra los tests y `.ps1` de `b8189d3`. Tabla, texto exacto, fallos por mutante y script: [`progress/mutacion_manual_F-035.md`](mutacion_manual_F-035.md) |
| Tiempo de la suite | 67.41 s en la pasada final de `init.sh` (entre 69 y 172 s en las de ciclos anteriores: varía con la carga de la máquina) |
