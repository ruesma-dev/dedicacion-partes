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

---

## 7 · Ficheros de esta carpeta

| Fichero | Qué es |
|---|---|
| `00_vars_dedicacion.ps1` | nombres de recurso, tags, mapas de imagen y de apps, timeouts, réplicas |
| `00_capps_vars_dedicacion.ps1` | derivados y ayudantes (`KvRef`, `Imagen`, `Fqdn-Interno`…) |
| `fase1_infra_dedicacion.ps1` | provisión base |
| `crear_base_dedicacion.ps1` | base y rol en el servidor compartido, una vez |
| `add_secrets_dedicacion.ps1` | las tres claves del Key Vault |
| `build_images_dedicacion.ps1` | build con tag fechado + `imagenes.json` |
| `create_transfer_dedicacion.ps1` / `create_api_dedicacion.ps1` / `create_front_dedicacion.ps1` | alta de cada Container App |
| `setup_front_easyauth.ps1` | Easy Auth y grupo de acceso |
| `redeploy_dedicacion.ps1` | republicación en orden |
| `imagenes.json` | **versionado**: qué tag hay publicado por servicio y cuándo |
| `.gitignore` | deja fuera `*.local.ps1`, donde viven los valores reales |

Qué expone y qué consume el proyecto: [`docs/INTEGRACION.md`](../docs/INTEGRACION.md).
Por qué cada decisión: `specs/F-008-infra-azure/`.
