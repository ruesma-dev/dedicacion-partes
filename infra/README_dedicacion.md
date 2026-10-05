<!-- infra/README_dedicacion.md -->
# Despliegue de **dedicación** en Azure

Manual de operación de esta carpeta. Los scripts **los ejecuta una persona**,
uno detrás de otro, desde una consola de PowerShell 5.1 con `az login` hecho.
No hay CI/CD, y para un entorno de pruebas no hace falta.

> **Ningún agente ejecuta nada de aquí.** Crear recursos, gastar dinero, dar
> de alta secretos o tocar la suscripción es trabajo de una persona. Lo que
> hay en esta carpeta lo escribieron agentes; ejecutarlo, no.

---

## 0 · Antes de empezar

1. `az login` y permisos de Contributor sobre la suscripción, más permisos de
   Entra para crear grupos y App Registrations.
2. **Crea tu copia local con los valores reales.** Los ficheros versionados
   llevan `REDACTADO-VER-COPIA-LOCAL` en el sitio de la suscripción y el
   tenant, porque **esto es un repositorio git: lo que entra se queda en el
   historial aunque luego se borre** (R21):

   ```powershell
   # infra\00_vars_dedicacion.local.ps1   (lo ignora infra/.gitignore)
   $Global:SUBSCRIPTION = "<el id real>"
   $Global:TENANT       = "<el id real>"
   ```

3. En **cada consola nueva**:

   ```powershell
   cd C:\Users\pgris\PycharmProjects\porcentajes\infra
   . .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
   . .\00_capps_vars_dedicacion.ps1      # solo si ya existe la fase 1
   ```

---

## 1 · Qué se despliega

```
Internet
   │  Easy Auth (Entra, grupo dedicacion-portal-users)
   ▼
ca-dedicacion-front        ingress EXTERNO    8080    min 1 / max 1
   │  http:// interno · proxy /api/* inyectando X-Usuario
   ▼
ca-dedicacion-api          ingress INTERNO    8090    min 1 / max 1
   │                            │
   │  http:// interno           └──▶ sigrid-api   (LECTURA de maestros)
   ▼
ca-dedicacion-transfer     ingress INTERNO    8006    min 1 / MAX 1
                                └──▶ sigrid-api   (ESCRITURA, base `ruesma`)

PostgreSQL `dedicacion`  ◀── ca-dedicacion-api
   (base propia dentro del servidor COMPARTIDO psql-albaranes-rs9k2)
```

**Solo el front está expuesto.** La api no tiene autenticación propia: lee la
cabecera `X-Usuario` y se la cree. Su ingress interno **es** su control de
acceso. No se abre un atajo «temporal» para probar; los atajos temporales se
quedan.

### Se reutilizan, no se crean ni se modifican

| Recurso | Qué hacemos |
|---|---|
| `acralbaranesdev` | publicar y tirar las tres imágenes, por identidad gestionada (su usuario admin está deshabilitado) |
| `psql-albaranes-rs9k2` | base propia `dedicacion`. **Somos el quinto inquilino**; nada a nivel de servidor |
| `func-sigridapi-dev-huyke` (`sigrid-api`) | único acceso al SQL Server de Sigrid |

### No se crea, a propósito

Storage Account, colas ni contenedores de blobs: aquí no hay canal asíncrono.

---

## 2 · Orden de ejecución (primera vez)

| # | Script | Qué hace | ¿Se repite? |
|---|---|---|---|
| 1 | `fase1_infra_dedicacion.ps1` | RG, managed identity, AcrPull, Log Analytics, Key Vault, Container Apps Environment | idempotente |
| 2 | `crear_base_dedicacion.ps1` | base `dedicacion` + rol `dedicacion_app` en el servidor compartido | **una sola vez** |
| 3 | `add_secrets_dedicacion.ps1` | las tres claves del Key Vault | al rotar |
| 4 | `build_images_dedicacion.ps1` | imágenes con tag fechado + `imagenes.json` | en cada cambio de código |
| 5 | `create_transfer_dedicacion.ps1` | alta del transfer (interno, modo pruebas) | solo el alta |
| 6 | `create_api_dedicacion.ps1` | alta de la api (interna) | solo el alta |
| 7 | `create_front_dedicacion.ps1` | alta del front (**externo**) | solo el alta |
| 8 | `setup_front_easyauth.ps1` | grupo, App Registration, Easy Auth | idempotente |

**El orden 5 → 6 → 7 no es cosmético**: la api necesita el FQDN interno del
transfer y el front el de la api. Cada script aborta si le falta el anterior.

**Entre el 7 y el 8 el front está abierto a Internet sin login.** No dejes ese
hueco abierto de un día para otro.

```powershell
. .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
.\fase1_infra_dedicacion.ps1
.\crear_base_dedicacion.ps1              # muestra el PLAN
.\crear_base_dedicacion.ps1 -Confirmar   # lo ejecuta
.\add_secrets_dedicacion.ps1
. .\00_capps_vars_dedicacion.ps1         # ahora sí: la fase 1 ya existe
.\build_images_dedicacion.ps1
.\create_transfer_dedicacion.ps1
.\create_api_dedicacion.ps1
.\create_front_dedicacion.ps1
.\setup_front_easyauth.ps1
```

---

## 3 · Republicar tras un cambio de código

```powershell
. .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1 ; . .\00_capps_vars_dedicacion.ps1
.\redeploy_dedicacion.ps1 -Solo api,front
```

Reordena siempre a **transfer → api → front**, y **aborta si el Container App
no existe**: republicar no es dar de alta.

**Commitea `infra/imagenes.json` después de cada build.** Es lo que responde
«qué código está corriendo» sin abrir Azure: con tag fechado y sin `latest`,
no hay otra forma de saberlo.

### 3 bis · Despliegue de F-026 (una vez): vaciar los datos de prueba

Desde F-026 la clave del trabajador es el `res.ide` del **recurso** de Sigrid,
no el `emp.ide` de su ficha de empleado
([`#regla-recurso`](../docs/ARCHITECTURE.md#regla-recurso)). Lo que hay en la
base son pruebas y no se migra (decisión D1 del 2026-10-02): se vacía. Va
**junto con F-034** y en este orden, con autorización expresa del humano para
el paso 2:

1. Republicar **transfer y api juntos** (`.\redeploy_dedicacion.ps1 -Solo
   transfer,api`). Al arrancar, la api añade la columna `trabajador.fecha_baja`
   (la deriva `esquema.py` del ORM, sin DDL a mano).
2. Vaciado: primero el plan, luego `-SoloRecuento` (cuenta y sale, sin
   escribir nada) y por último `-Confirmar`.

   ```powershell
   $env:Path = "C:\Program Files\PostgreSQL\16\bin;$env:Path"   # si psql no está en el PATH
   . .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
   .\vaciar_datos_prueba_dedicacion.ps1                 # PLAN: no conecta
   .\vaciar_datos_prueba_dedicacion.ps1 -SoloRecuento   # lee la contraseña, cuenta y sale
   .\vaciar_datos_prueba_dedicacion.ps1 -Confirmar      # lee la contraseña y vacía
   ```

   **Hace falta `psql` también en Azure** (desde F-035): el script ya no pasa
   la contraseña a `az` (ver §6 bis), sino a `psql` por el entorno
   (`PGPASSWORD`, con `PGSSLMODE=require`). Eso exige el cliente de
   PostgreSQL en tu máquina y que el servidor admita conexiones **desde tu
   IP**. Si no conecta, el script lo dice y para: la regla de acceso de tu IP
   se revisa en el Portal (servidor compartido, Redes); el script no la crea
   ni la toca. `-SoloRecuento` es la forma de comprobar las dos cosas sin
   escribir nada: no necesita `-Confirmar` y no se combina con él.

   **En Azure la contraseña de `dedicacion_app` sale del Key Vault**: el
   script lee `PG-PASSWORD` de `$KV` con `az keyvault secret show` (solo
   lectura, como salida de `az`, nunca como argumento), la misma que usa la
   api. Hace falta el rol **Key Vault Secrets User** u **Officer** sobre
   `$KV`. Si no se puede leer (sin `$KV`, sin permiso o vacía), avisa y la
   pide a mano como respaldo. En local se pide siempre a mano. Si PostgreSQL
   la rechaza, el error lo dice; el aviso de la IP solo sale ante tiempo
   agotado o `no pg_hba.conf entry`.

   Ejecuta **una** sentencia en la base `dedicacion`: `TRUNCATE TABLE
   asignacion, evento, periodo, trabajador CONTINUE IDENTITY`. No toca `obra`
   ni `empresa`, ni otras bases, ni nada del servidor compartido. Las
   secuencias se conservan a propósito: si volvieran a 1, un `asignacion.id`
   nuevo reutilizaría la `synckey` de una línea de prueba ya escrita en Sigrid
   y el transfer la daría por registrada. En local: `-Local` (usa `psql` contra
   `localhost/dedicacion`), también con `-SoloRecuento`.
3. `GET /api/v1/sync/preview`: revisar `empleados.ventana_baja` y
   `empleados.posible_misma_persona`.
4. `POST /api/v1/sync`. Solo entonces se vuelve a capturar y registrar.

Si el paso 2 se olvida, nada se escribe mal: las filas viejas se desactivan en
el sync, sus trabajadores dejan de estar vigentes y sus líneas van a
`no_vigentes` (no se mandan al transfer ni se trazan).

---

## 4 · Las cosas que hay que saber antes de perder una tarde

**`/health` del front no responde a un `curl` anónimo.** Con Easy Auth y login
obligatorio devuelve una redirección al login. **No es una caída.** Para verlo,
navega con sesión iniciada.

**La api no es alcanzable desde fuera.** Es deliberado. Para probarla, entra
por el front autenticado: `https://<fqdn-front>/api/v1/health`.

**El transfer tampoco.** Para saber si está vivo:

```powershell
az containerapp logs show -n ca-dedicacion-transfer -g rg-dedicacion-dev --tail 60
```

**El transfer está en MODO PRUEBAS y esta feature termina así.** Todo lo que
escriba va a la obra `0404` con la marca `PRUEBA-PORC` en `tex`. Compruébalo:

```powershell
az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev `
  --query "properties.template.containers[0].env[?name=='OBRA_PRUEBAS_FORZAR'].value" -o tsv
```

Salir de ahí exige `-ModoProduccion -Confirmar` **y una decisión expresa del
humano para una acción concreta**. Que el script lo permita no lo autoriza.

**El arranque de la api no crea la base.** Si en los logs aparece «La base de
datos 'dedicacion' no existe», falta el paso 2. Es a propósito: un servicio
ajeno creando bases y roles en un servidor de producción compartido es justo
lo que el ecosistema prohíbe por escrito.

**Si `fase1` falla creando el Key Vault**, su nombre está pillado: el espacio
de nombres es **mundial**. Cambia `$SUFFIX` en `00_vars_dedicacion.ps1` y
relanza; es idempotente.

---

## 5 · Comprobación después de desplegar

```powershell
# Solo el front es externo
az containerapp list -g rg-dedicacion-dev `
  --query "[].{app:name, externo:properties.configuration.ingress.external}" -o table

# Una sola réplica como máximo en transfer y api
az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev --query "properties.template.scale"
az containerapp show -n ca-dedicacion-api      -g rg-dedicacion-dev --query "properties.template.scale"

# Todos los secretos por referencia a Key Vault, ninguno como valor
az containerapp show -n ca-dedicacion-api -g rg-dedicacion-dev `
  --query "properties.configuration.secrets[].{n:name, kv:keyVaultUrl}" -o table

# Ninguna Storage Account
az resource list -g rg-dedicacion-dev -o table
```

Esperado: `externo` en `true` **solo** en el front; `maxReplicas` = 1 en
transfer y api; `keyVaultUrl` en **todos** los secretos; y ni una Storage
Account en la lista.

---

## 6 · Secretos

| Clave en Key Vault | Quién la consume |
|---|---|
| `PG-PASSWORD` | api (rol de aplicación, **no** el admin del servidor) |
| `SIGRID-API-FUNCTION-KEY` | api (lectura) y transfer (escritura) |
| `EASYAUTH-CLIENT-SECRET` | front (lo genera `setup_front_easyauth.ps1`) |

Ninguno viaja como valor: los Container Apps declaran un secret que es una
**referencia** al Key Vault (`keyvaultref`), leída con la identidad gestionada.

**La contraseña del administrador de PostgreSQL no se guarda en ningún sitio
nuestro.** El servicio no la necesita, y lo que no se guarda no se filtra. La
usa una persona, una vez, al ejecutar `crear_base_dedicacion.ps1`.

### 6 bis · Ningún secreto por la línea de comandos de `cmd.exe` (F-035)

En Windows `az` es un `.cmd`: su línea de comandos la interpreta `cmd.exe`,
que se come o reinterpreta `"` `&` `|` `<` `>` `^` `%`, y también `)`: `az.cmd`
expande sus argumentos (`%*`) dentro de un bloque `IF … ( … )`, y un `)` en el
valor cierra ese bloque, corta el argumento o rompe la línea (añadido en el
ciclo 2 de F-035 con la aprobación del humano). Un secreto pasado como
argumento (`-p`, `--value`) llega **corrompido** y sin aviso: así falló el
vaciado contra Azure del 2026-10-02 («password authentication failed» con la
contraseña buena). Revisión de los scripts de esta carpeta:

| Script | Secreto por argumento a `az` | Resultado |
|---|---|---|
| `vaciar_datos_prueba_dedicacion.ps1` | antes, `-p` a `az … execute` | **corregido**: usa `psql` (un `.exe`) con la contraseña en `PGPASSWORD`, solo durante la llamada |
| `crear_base_dedicacion.ps1` | `-p` a `az … execute` (y la del rol dentro de la consulta) | **rechaza** las contraseñas con esos caracteres antes de llamar a `az` |
| `add_secrets_dedicacion.ps1` | `--value` a `az keyvault secret set` | **rechaza** los valores con esos caracteres antes de llamar a `az` |
| `setup_front_easyauth.ps1` | `--value` con el client secret | sin riesgo: secreto generado por Azure (`az ad app credential reset`), con un juego de caracteres sin ninguno de esos |
| `create_transfer_dedicacion.ps1` / `create_api_dedicacion.ps1` / `create_front_dedicacion.ps1`, `redeploy_dedicacion.ps1`, `fase1_infra_dedicacion.ps1` | ninguno | sin riesgo: solo referencias a Key Vault (`keyvaultref`, `secretref`), nunca valores |

Si alguna vez hace falta una contraseña con esos caracteres, el camino es el
de `vaciar_datos_prueba_dedicacion.ps1`: `psql` y la contraseña en el entorno.

---

## 7 · Ficheros de esta carpeta

| Fichero | Qué es |
|---|---|
| `00_vars_dedicacion.ps1` | nombres de recurso, tags, mapas de imagen y de apps, timeouts, réplicas |
| `00_capps_vars_dedicacion.ps1` | derivados y ayudantes (`KvRef`, `Imagen`, `Fqdn-Interno`…) |
| `fase1_infra_dedicacion.ps1` | provisión base |
| `crear_base_dedicacion.ps1` | base y rol en el servidor compartido, una vez |
| `vaciar_datos_prueba_dedicacion.ps1` | vacía los datos de prueba de `dedicacion` en el despliegue de F-026 (§3 bis), con `psql` también en Azure: plan, `-SoloRecuento` (solo lectura) y `-Confirmar` |
| `add_secrets_dedicacion.ps1` | las tres claves del Key Vault |
| `build_images_dedicacion.ps1` | build con tag fechado + `imagenes.json` |
| `create_transfer_dedicacion.ps1` / `create_api_dedicacion.ps1` / `create_front_dedicacion.ps1` | alta de cada Container App |
| `setup_front_easyauth.ps1` | Easy Auth y grupo de acceso |
| `redeploy_dedicacion.ps1` | republicación en orden |
| `imagenes.json` | **versionado**: qué tag hay publicado por servicio y cuándo |
| `.gitignore` | deja fuera `*.local.ps1`, donde viven los valores reales |

Qué expone y qué consume el proyecto: [`docs/INTEGRACION.md`](../docs/INTEGRACION.md).
Por qué cada decisión: `specs/F-008-infra-azure/`.
