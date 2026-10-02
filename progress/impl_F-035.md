# F-035 · Informe del implementer

Rama `feature/F-035-vaciado-psql-azure`, rigor **estándar**, sin spec (contra
los `acceptance` de `harness/features.json`). Commits: `fc57b7f` T1 (vaciado
con `psql` + `-SoloRecuento`), `33b5e9b` T2 (control de caracteres),
`b8189d3` T3 (README), `30c28c7` T4 (tests reforzados tras mutación manual).

**Ningún script se ha ejecutado**: ni contra Azure ni contra la base local, ni
con `-Confirmar` ni con `-SoloRecuento`. Lo único ejecutado sobre ellos: el
analizador de PowerShell (`Parser]::ParseFile`, 0 errores de sintaxis en los
tres) y la función de control extraída por AST con cadenas inventadas.

## Qué cambió

**`infra/vaciar_datos_prueba_dedicacion.ps1`**
- Azure usa `psql -h $PG_FQDN -d $PG_DB -U $PG_APP_USER -v ON_ERROR_STOP=1 -c
  $sql`; FQDN por `az postgres flexible-server show … --query
  fullyQualifiedDomainName -o tsv` (solo lectura; vacío ⇒ para). Fuera
  `rdbms-connect` y `az … execute`; queda `az account set`. Solo esas dos `az`.
- `PGPASSWORD` (los dos modos) y `PGSSLMODE=require` (solo Azure) dentro del
  `try` de `Ejecutar-Sql`, borrados en su `finally`.
- Comprobación de `psql` al primer nivel (los dos modos) y, como el FQDN,
  **antes** de pedir la contraseña.
- `-SoloRecuento`: plan propio, pide la contraseña, cuenta y `return` antes del
  vaciado. Con y sin `-Local`.
- Error de `psql` en Azure: «tu IP no tenga acceso… revisa en el Portal
  (servidor $PG, Redes) la regla de firewall de tu IP. Este script NO la crea
  ni la toca» (sin el literal que prohíbe F-026).
- Cabecera con los seis modos y el `$env:Path` de psql. BOM/CRLF/ASCII.

**`crear_base_dedicacion.ps1` / `add_secrets_dedicacion.ps1`** — solo
añadidos: función `Rechazar-CaracteresDeCmd` (`-match '["&|<>^%]'` → `throw`
con el porqué, sin imprimir el valor), llamada tras leer cada secreto
(`$PGADMIN_PWD`, `$APP_PWD`; `$val`). Ejecutada aislada (extraída por AST):
rechaza `a"b a&b a|b a<b a>b a^b a%b`, acepta `Abc123.x-y_z~`,
`comilla'simple`, `x!y=z+/`. Mensaje real:

```
ABORTADO: El valor de 'PG-PASSWORD' contiene alguno de estos caracteres: " & | < > ^ %. En Windows az es un .cmd y su linea de comandos pasa por cmd.exe, que los interpreta y corromperia el valor sin avisar (F-035). Si es una contrasena que eliges tu, usa una sin ellos.
```

**`README_dedicacion.md`** — §3 bis: `$env:Path`, `-SoloRecuento`, «`psql`
también en Azure» y acceso desde tu IP. §6 bis nueva: `cmd.exe` y la tabla de
la revisión. §7: fila del vaciado. El resto de scripts, **sin tocar**.

## Decisiones de diseño

1. **`-SoloRecuento` conecta sin `-Confirmar`**: es de solo lectura. La
   invariante se mantiene: sin `-Confirmar` **ni** `-SoloRecuento`, el script
   imprime el plan y sale sin conectar (`if (-not $Confirmar -and -not
   $SoloRecuento) { … return }`).
2. **`-Confirmar` y `-SoloRecuento` juntos → `throw`**, antes de imprimir el
   plan y de conectar a nada. Uno escribe y el otro solo lee: que gane uno en
   silencio es peor que decirlo.
3. **`PGSSLMODE` se borra en el `finally` aunque el usuario lo tuviera puesto
   de antes**, igual que ya pasaba con `PGPASSWORD` en local. Es lo que pide
   el plan; restaurar el valor previo sería más código para un caso que no se
   da en este flujo.
4. **`add_secrets` controla los tres valores**, no solo `PG-PASSWORD`: los tres
   van por `--value` a `az.cmd`. Las function keys y el client secret de Azure
   no usan esos caracteres, así que no se rechaza nada legítimo. Si un valor se
   rechaza, el `throw` corta el bucle; lo guardado antes en esa misma
   ejecución queda guardado.
5. **En `crear_base` el control va tras leer cada contraseña**, sin mover nada
   más («no cambies nada más»): antes de la primera llamada a `az` que la
   lleva, pero los pasos 1-2 (comprobar el servidor y la regla de servicios de
   Azure si falta) siguen ejecutándose antes de pedir credenciales, como hasta
   hoy. Observación para el líder, no la toco: adelantar la lectura de
   credenciales evitaría ese paso si luego la contraseña se rechaza.

## Tests anteriores que cambian (declarados)

Los tres en `tests/test_f026_vaciado.py`. **El plan de `current.md` solo
declaraba el tercero**: los otros dos cambian porque `-SoloRecuento` cambia la
estructura que fijan. Ninguno pierde exigencia.

| Test | Antes | Ahora | Motivo |
|---|---|---|---|
| `test_f026_r10_parametros_confirmar_y_local` | `param` con exactamente `$Confirmar, $Local` | `$Confirmar, $Local, $SoloRecuento` | tercer conmutador |
| `test_f026_r10_sin_confirmar_sale_antes_de_conectar` | busca `if (-not $Confirmar) {` | busca `if (-not $Confirmar -and -not $SoloRecuento) {`; el resto igual (`return` al primer nivel y antes de cualquier `az`/`psql`/`Read-Host`) | `-SoloRecuento` también conecta, sin `-Confirmar` |
| `test_f026_r10_solo_en_la_base_dedicacion` | `az … execute` con `-d $PG_DB` y `-u $PG_APP_USER`; todo `psql` con `-h localhost -d dedicacion` | ningún `flexible-server execute`; exactamente 2 `psql`: local con `-h localhost -d dedicacion`, Azure con `-h $PG_FQDN -d $PG_DB -U $PG_APP_USER`; sigue sin `PG_ADMIN` | Azure pasa a psql (R1) |

`test_f026_r10_formato_de_los_ps1_del_repositorio`, `…una_sola_sentencia…`
(sigue habiendo **un** `TRUNCATE`) y `…nada_fuera_de_las_cuatro_tablas`
(incluido `firewall-rule`) pasan **sin tocarlos**.

## Tests nuevos: `tests/test_f035_secretos_sin_cmd.py` (28)

R1 (7) psql contra el FQDN, solo `account set` + `show`, PATH, `PGSSLMODE`
solo en Azure, `finally`; R2 (5) `-SoloRecuento`; R3 (2) mensaje de IP y nada
de servidor; R4 (8) clase de caracteres evaluada con datos, mensaje, orden
lectura < control < primera `az` (3 casos) y **barrido** de `infra/*.ps1` (sin
`*.local.ps1`): todo `-p $x`/`--value $x`/`--password $x` debe ser uno de los
tres admitidos (crear_base, add_secrets, setup_front_easyauth); formato de los
3 `.ps1` (3); R5 (3) README.

## Fase RED

Tests escritos antes que el código en cada tarea. Comandos y salida real:

**T1** — `python -m pytest tests/test_f035_secretos_sin_cmd.py -q -p no:cacheprovider`
(script de vaciado aún sin tocar):

```
>       assert "flexible-server execute" not in texto
E         'flexible-server execute' is contained here:
E            postgres flexible-server execute -n $PG -u $PG_APP_USER -p $CLAVE -d $PG_DB --querytext $sql --only-show-errors 2>&1 | Out-String
>       assert len(azure) == 1, psql
E       AssertionError: ['$salida = psql -h localhost -d dedicacion -U $USUARIO -v ON_ERROR_STOP=1 -c $sql 2>&1 | Out-String']
>       assert _nivel(codigo, comprobacion) == 0, codigo[comprobacion]
E       AssertionError: if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
E       assert 1 == 0
E       AssertionError: falta la salida sin -Confirmar ni -SoloRecuento
E       AssertionError: falta el rechazo de -Confirmar con -SoloRecuento
E       AssertionError: ['throw "Falta `$PG. Haz primero: ...', 'throw "No encuentro psql en el PATH: ...', 'throw "Sin contrasena no se conecta." }', 'throw "Fallo ejecutando SQL en ${DESTINO}:`n$salida" }']
13 failed, 1 passed in 0.55s
```

(El que pasaba: `test_f035_r3_sin_tocar_nada_del_servidor`, que fija algo que
el script ya cumplía.) Tras el código: `14 passed`.

**T2** — mismo comando, con los tests de R4 añadidos y los scripts sin tocar:

```
E       AssertionError: falta la funcion Rechazar-CaracteresDeCmd en crear_base_dedicacion.ps1
E       AssertionError: falta la funcion Rechazar-CaracteresDeCmd en add_secrets_dedicacion.ps1
E       AssertionError: assert 'cmd.exe' in ''
E       AssertionError: (27, 75, 41)      # crear_base, la del admin (lectura, control ausente, primera az)
E       AssertionError: (30, 75, 35)      # crear_base, la del rol
E       AssertionError: (17, 30, 21)      # add_secrets, el valor
7 failed, 18 passed in 0.52s
```

(El barrido ya pasaba: hoy solo había esos tres usos; es guardián a futuro.)
Tras el código: `25 passed`.

**T3** — `python -m pytest tests/test_f035_secretos_sin_cmd.py -q -p no:cacheprovider -k r5`:

```
E       AssertionError: assert '-SoloRecuento' in '### 3 bis · Despliegue de F-026 (una vez): vaciar los datos de prueba ...'
E       AssertionError: cmd.exe        # no existe la sección de cmd.exe
E       AssertionError: ['| `vaciar_datos_prueba_dedicacion.ps1` | ... plan y `-Confirmar` |']
3 failed, 25 deselected in 0.27s
```

Tras el README: `3 passed` (con el filtro de §7 acotado: cogía también la
tabla nueva de §6 bis).

## Resultado real de `bash harness/init.sh` (final, con este informe)

```
402 passed, 1 skipped in 171.51s (0:02:51)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)
[OK] PUERTA TAMAÑO: F-035 dentro de los topes (impl 219/220)
ENTORNO LISTO. Puedes trabajar.
```

`ruff` del test nuevo: limpio. Una pasada previa salió en rojo por el propio
informe (254 líneas y un `PWD:` que el guardián de F-008 leyó como credencial).

## MANUAL (la hace el humano; NO escribe nada)

Desde una consola de PowerShell **nueva** (con `az login` hecho para la de
Azure). Los dos comandos piden una contraseña y solo leen.

```powershell
cd C:\Users\pgris\PycharmProjects\porcentajes\infra
$env:Path = "C:\Program Files\PostgreSQL\16\bin;$env:Path"
. .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1

# 1) Local: pide la contrasena de 'postgres' (o de $env:PGUSER) en localhost
.\vaciar_datos_prueba_dedicacion.ps1 -Local -SoloRecuento

# 2) Azure: pide la contrasena de 'dedicacion_app' (la de PG-PASSWORD)
.\vaciar_datos_prueba_dedicacion.ps1 -SoloRecuento

# 3) Despues de cada uno, el entorno queda limpio (esperado: False False)
Test-Path Env:PGPASSWORD ; Test-Path Env:PGSSLMODE
```

**Esperado en 1)**: plan «-SoloRecuento: SOLO LECTURA», `=== 1) Conexion ===`,
contraseña, `=== 3) Filas antes del vaciado ===` con una fila de `psql`
(asignacion, evento, periodo, trabajador) y `=== SOLO RECUENTO: hecho, no se ha
escrito nada ===`. Ninguna sección «4) Vaciado».

**Esperado en 2)**: igual, más `Servidor: <fqdn> (psql con PGSSLMODE=require)`
antes de la contraseña. Tras el sync del 2026-10-02, `trabajador` ≈ 196 y el
resto lo que se haya capturado desde entonces (0 si nadie ha capturado). **Lo
que valida F-035**: que conecta con la contraseña del Key Vault sin «password
authentication failed». Si sale tiempo agotado o `no pg_hba.conf entry`, el
mensaje pide revisar la regla de firewall de tu IP: es el acceso desde tu
máquina, no el script, y el script no la toca.

Opcional, sin conectar: `-SoloRecuento -Confirmar` → «se excluyen», sin pedir nada.

## Fuera del alcance / pendiente

- Fuera: volver a vaciar producción, la contraseña de `dedicacion_app`, el
  servidor y su firewall, `azure-apps` (no cambia lo que exponemos/consumimos).
- `current.md` y `features.json` sin tocar. **Para el líder**: `current.md`
  declara un test cambiado y son **tres**; y la observación de la decisión 5.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (suite de `init.sh`) | **402 passed, 1 skipped**; los 28 de `test_f035_secretos_sin_cmd.py` en verde |
| Tests de F-035 + F-026 + F-008 | 111 passed en 2.58 s (`pytest` de esos cuatro ficheros, con `test_f004_readme.py`) |
| Cobertura de líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. Lo cambiado es PowerShell y Markdown |
| Mutantes (`python -m harness.mutacion --feature F-035`) | **N/A**: «ALCANCE VACÍO en F-035: ni una línea de producción que mutar… No se escribe informe». La herramienta solo muta Python |
| Mutación manual de los `.ps1` (sustituto, script en el scratchpad de la sesión) | **19 mutantes, 0 supervivientes** tras T4. En la primera pasada sobrevivieron 2: M8 (`if ($Local -and -not (Get-Command psql…`): **hueco real**, el test solo miraba el nivel de llaves; M10 (quitar «tu IP no tenga acceso»): casi equivalente, el mensaje seguía citando «la regla de firewall de tu IP», pero el test aceptaba cualquier `throw` con «IP». Los dos tests se ajustaron en `30c28c7` |
| Tiempo de la suite | 171.51 s en la pasada final de `init.sh` (75.94 s en la anterior, mismo árbol de código: varía con la carga de la máquina) |

Mutantes: quitar del `finally` cada variable; `PGSSLMODE` en local / fuera de
Azure; sin `return` de `-SoloRecuento`; salida solo sin `-Confirmar`; sin
exclusión; psql solo en local; `az … execute -p`; mensaje sin IP / sin
firewall; FQDN sin comprobar; `rdbms-connect`; sin cada control (3); clase sin
`%` / sin `"`; control tras `az`.
