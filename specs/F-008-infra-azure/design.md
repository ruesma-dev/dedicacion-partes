<!-- specs/F-008-infra-azure/design.md -->
# F-008 · Infraestructura y despliegue en Azure — Diseño

> Se diseña contra `docs/ARCHITECTURE.md` (normativo), `docs/CONVENTIONS.md`,
> `azure-apps/partes.md` (el patrón), `azure-apps/postventa_incidencias.md`
> (el precedente de meterse en el servidor PostgreSQL compartido) y
> `azure-apps/sigrid_api.md` (la pasarela que consumimos).

## 0 · Resumen en una página

Tres Container Apps en un resource group propio, **solo el front expuesto**,
la api y el transfer internos. Sin colas ni Storage Account: la comunicación
es HTTP síncrono y el volumen es un cuadrante mensual. Imágenes en el ACR
compartido con tag fechado. Secretos en Key Vault propio, leídos por
identidad gestionada. Easy Auth (Entra) en el front con grupo de seguridad.
El transfer arranca —y termina esta feature— en **modo pruebas**.

```
Internet
   │  Easy Auth (Entra, grupo dedicacion-portal-users)
   ▼
ca-dedicacion-front      ingress EXTERNO      8080   min 1 / max 1
   │  http:// interno · proxy /api/* + X-Usuario
   ▼
ca-dedicacion-api        ingress INTERNO      8090   min 1 / max 1
   │                          │
   │  http:// interno         └──▶ sigrid-api  (LECTURA de maestros)
   ▼
ca-dedicacion-transfer   ingress INTERNO      8006   min 1 / MAX 1
                              └──▶ sigrid-api  (ESCRITURA, base `ruesma`)
                                     └──▶ Sigrid (SQL Server on-prem)

PostgreSQL `dedicacion`  ◀── ca-dedicacion-api        (dónde vive: DECISIÓN D1)
```

**Límite de microservicio.** Esta feature no mueve ni una responsabilidad de
negocio entre servicios: no toca reglas, ni el front gana lógica, ni la api
gana credencial de escritura. Lo único que cambia dentro de un servicio es el
**bootstrap de la base de datos de `dedicacion-api`** (§3.3), que es
infraestructura de ese servicio y de nadie más. El resto vive en `infra/`,
que es nuevo y no pertenece a ningún servicio.

---

## 1 · Inventario de recursos

### 1.1 Se crean (resource group propio `rg-dedicacion-dev`, `spaincentral`)

| Recurso | Nombre | Para qué |
|---|---|---|
| Resource group | `rg-dedicacion-dev` | contenedor propio; nada nuestro fuera de aquí |
| Managed identity | `id-dedicacion-dev` | pull del ACR + lectura de secretos del Key Vault |
| Log Analytics | `log-dedicacion-dev` | logs de los tres Container Apps |
| Container Apps Env. | `cae-dedicacion-dev` | red interna donde se ven los tres |
| Key Vault | `kv-dedicacion-<sufijo>` | secretos (§5). RBAC, no access policies |
| Container App | `ca-dedicacion-transfer` | 8006, interno, min 1 / **max 1** |
| Container App | `ca-dedicacion-api` | 8090, interno, min 1 / max 1 |
| Container App | `ca-dedicacion-front` | 8080, **externo** + Easy Auth, min 1 / max 1 |

`<sufijo>` es un sufijo corto en minúsculas que el operador fija en
`infra/00_vars_dedicacion.ps1`; el nombre del Key Vault comparte espacio de
nombres **mundial** y puede estar pillado. Mismo mecanismo que `$SUFFIX` en
`partes/infra/00_vars_partes.ps1`.

### 1.2 Se reutilizan (no se crean, no se modifican a nivel de recurso)

| Recurso | Nombre | RG | Qué hacemos |
|---|---|---|---|
| Container Registry | `acralbaranesdev` | `rg-albaranes-dev` | publicar y tirar las tres imágenes. **Usuario admin deshabilitado**: se accede por identidad gestionada (`AcrPull` a `id-dedicacion-dev`, `--registry-identity` en cada app) |
| Function App | `func-sigridapi-dev-huyke` | `rg-sigrid-dev-data-api` | `sigrid-api`: la api lee maestros, el transfer escribe. **Nadie se conecta al SQL Server de Sigrid por su cuenta** |
| PostgreSQL Flexible | `psql-albaranes-rs9k2` | `rg-albaranes-dev` | base `dedicacion` — **solo si el humano confirma la opción A de D1** (§3) |
| Entra ID | (tenant de la casa) | — | grupo `dedicacion-portal-users` + App Registration del front |

### 1.3 Lo que NO se crea, y por qué

- **Storage Account, colas, contenedores de blobs.** `partes` los necesita
  porque su pipeline es asíncrono (cinco servicios encadenados por cola).
  Aquí la cadena es front→api→transfer por HTTP síncrono, con un cuadrante
  mensual por obra. Crear un Storage sin usarlo es superficie de ataque y
  factura sin contrapartida.
- **`AZURE_CLIENT_ID` en las variables de entorno.** `partes` lo pone porque
  su código usa `DefaultAzureCredential` para hablar con las colas. Nuestro
  código **no usa el SDK de Azure**: la identidad gestionada la consume la
  plataforma (pull del ACR y `keyvaultref`), no la aplicación. Ponerlo sería
  copiar sin entender.
- **DNS propio, certificado, blue/green, KEDA.** Fuera de alcance (§8 de
  `requirements.md`).

---

## 2 · Topología de red y exposición

### 2.1 Por qué la api va interna (y no es negociable)

`dedicacion-api` no tiene autenticación. Su único control de identidad es:

```python
# services/dedicacion-api/interface_adapters/api/deps.py:92
def obtener_usuario(request: Request) -> str:
    """Usuario para auditoría: lo inyecta el front (Easy Auth) vía cabecera."""
    return request.headers.get("x-usuario", "local").strip() or "local"
```

Se lee la cabecera y se cree. Con ingress externo, cualquiera en Internet
podría llamar a `POST /api/v1/registro/ejecutar` poniendo la cabecera que
quisiera; la api llamaría al transfer, y el transfer es la única pluma del
sistema sobre el ERP. El ingress interno es el control de acceso de la api,
igual que en `partes` lo es de `sv5`.

Consecuencia que hay que aceptar: **la api solo es alcanzable a través del
proxy del front**. Para probarla sin navegador hay que entrar por el front
autenticado (`https://<fqdn-front>/api/v1/...`) o mirar logs. No se abre un
atajo «temporal»; los atajos temporales se quedan.

### 2.2 Por qué el transfer va interno y a una réplica

Es el único servicio con credencial de escritura contra Sigrid. Su exposición
es una decisión de seguridad, no de comodidad: **interno**, y su único cliente
es la api. Y `--max-replicas 1` es restricción dura, no ajuste: la línea se
inserta con `MAX(ide)+1` bajo `UPDLOCK, HOLDLOCK`
(`docs/ARCHITECTURE.md` §9). Dos réplicas se pisan los `ide`.

### 2.3 HTTP plano hacia dentro

La api llama al transfer y el front llama a la api con `httpx` por `http://`.
`httpx` no sigue el 307 a HTTPS que devolvería el ingress, así que los dos
ingress internos se crean con `--allow-insecure true`, exactamente como
`partes/infra/create_sv5_transfer.ps1`. El tráfico no sale del entorno.

### 2.4 Cableado de URLs

Los FQDN internos no se conocen hasta que el recurso existe, así que el orden
de alta es **transfer → api → front** y cada script lee el FQDN del anterior
y lo inyecta:

| Variable | En | Valor |
|---|---|---|
| `TRANSFER_BASE_URL` | api | `http://<fqdn-interno-transfer>` |
| `API_BASE_URL` | front | `http://<fqdn-interno-api>` |

### 2.5 Timeouts encadenados (R28)

| Salto | Variable | Hoy | Desplegado |
|---|---|---|---|
| navegador → front | (balanceador de Azure) | — | **230 s, no configurable** |
| front → api | `API_TIMEOUT_S` | 120 | **200** |
| api → transfer | `TRANSFER_TIMEOUT_S` | 180 | **180** |
| transfer → sigrid-api | `SIGRID_API_TIMEOUT_S` | 60 | 60 |

Hoy el front (120 s) se rinde **antes** que la api (180 s): el usuario vería
un error de un registro que sí se estaba haciendo. Se corrige subiendo el
front a 200 s, que sigue por debajo del corte de 230 s del balanceador
(`azure-apps/sigrid_api.md` §3.4). Los valores se fijan en los scripts de
`infra/` y se dejan escritos en `docs/ARCHITECTURE.md`; **no** se escribe un
test que cruce dos servicios, porque eso es la avería que F-012 tiene abierta.

---

## 3 · La base de datos `dedicacion` — DECISIÓN D1 (la toma el humano)

Hoy `PG_HOST=localhost`. No hay decisión escrita sobre dónde vive al
desplegar, y `CLAUDE.md` prohíbe darlo por hecho. Estas son las opciones.

### 3.1 Opción A — base propia `dedicacion` en `psql-albaranes-rs9k2`

Es el patrón del ecosistema: un servidor, varias bases (`albaranes`,
`partes`, `sigrid_dm`, `postventa`). Seríamos el **quinto inquilino**.

| A favor | En contra |
|---|---|
| Coste marginal cero: el servidor ya está pagado y respaldado | El **disco son 32 GB compartidos, solo crece y nunca decrece**. El 2026-08-09 llegó al 93,4 % por el build de otro proyecto y el servidor quedó en solo-lectura diez minutos |
| Mismo vocabulario de variables (`PG_*`) que el resto: quien despliegue no aprende dos formas | El **punto de restauración es del servidor entero**: no se puede volver atrás nuestra base sin arrastrar las ajenas |
| Precedente reciente y documentado: `postventa-incidencias` entró así el 2026-08-19 y dejó escritas las reglas | Las **conexiones se reparten** entre cinco proyectos |
| Nuestro volumen es minúsculo: ~156 trabajadores × obras × 12 periodos al año son miles de filas de texto corto | Cualquier cambio a nivel de servidor nos afecta y afecta a los otros cuatro |

### 3.2 Opción B — servidor PostgreSQL propio

| A favor | En contra |
|---|---|
| Aislamiento total: disco, PITR y conexiones nuestros | **Coste mensual nuevo** por una base de kilobytes |
| Podríamos restaurar a un punto anterior sin coordinar con nadie | Otro servidor que mantener, parchear y vigilar |
| | Rompe el patrón del ecosistema por un volumen que no lo justifica |

### 3.3 Opción C — no persistir en Azure (seguir en el portátil)

Se descarta, pero conste por qué: un Container App no tiene disco
persistente, y el objetivo declarado es **probar el sistema fuera del
portátil**. Sin base en Azure no hay nada que probar.

### 3.4 Lo que recomienda esta spec

**Opción A**, con las cuatro salvaguardas que `postventa-incidencias` dejó
escritas tras ser el cuarto inquilino, porque son exactamente nuestro caso:

1. **La base y el rol los crea una persona, una vez**, con
   `infra/crear_base_dedicacion.ps1`. La aplicación **nunca** hace
   `CREATE DATABASE` ni `CREATE ROLE` (§3.5: hoy sí los hace).
2. **Rol de aplicación propio** (`dedicacion_app`), no el admin del servidor.
   `partes` desplegó con `PG_USER=$PG_ADMIN` y eso pone la contraseña del
   administrador del servidor compartido dentro de tres contenedores.
   Nosotros no repetimos eso.
3. **Nada de `ALTER SYSTEM`, `CREATE EXTENSION`, `GRANT` a nivel de servidor
   ni tocar el esquema `public` de otra base.**
4. **`PG_SSLMODE=require`** (hoy el defecto del código es `prefer`, que acepta
   sin protestar una conexión sin cifrar).

**Sub-decisión D1b — esquema `public` o esquema nominado.** `postventa` usa
un esquema propio con `search_path` sin `public`, como cinturón sobre
tirantes. Aquí se recomienda **`public` dentro de nuestra base
`dedicacion`**: la base es propia, no la comparte nadie, y es lo que hacen
`albaranes` y `partes`. Cambiar a esquema nominado obligaría a tocar el ORM y
el `search_path` de todas las sesiones, y eso **no es barato después**: si el
humano lo quiere, hay que decidirlo **ahora**, no más tarde.

### 3.5 El cambio de código que exige cualquiera de las opciones

`services/dedicacion-api/main.py` llama en cada arranque a
`asegurar_base_datos(settings)`, que conecta como **administrador del
servidor** y ejecuta `CREATE ROLE` y `CREATE DATABASE` si no existen
(`infrastructure/db/database.py`). Contra `localhost` es una comodidad; contra
un servidor de producción compartido por cuatro proyectos es justo lo que el
ecosistema prohíbe por escrito.

Diseño (R13–R16):

- `config/settings.py` gana `auto_create_database: bool = False`
  (alias `AUTO_CREATE_DATABASE`). **Por defecto `False`**: una variable
  olvidada hace lo prudente. El `.env.example` local lo trae a `true`.
- `infrastructure/db/database.py::asegurar_base_datos` empieza con un
  cortocircuito: si `not settings.auto_create_database`, registra en el log
  que el bootstrap está desactivado y **retorna sin abrir la conexión**. No
  basta con saltarse el DDL: sin conexión, el servicio desplegado no necesita
  las credenciales de administrador (y por tanto no se le dan).
- `crear_engine` / el arranque envuelven el primer fallo de conexión por base
  inexistente (`psycopg.errors.InvalidCatalogName` /
  `OperationalError` cuyo texto delate `database "..." does not exist`) en un
  error propio, `BaseDatosNoExiste`, cuyo mensaje nombra la base que falta y
  `infra/crear_base_dedicacion.ps1`. Capa: `infrastructure`; el error tipado
  vive junto a los demás del dominio de arranque.

Todo esto es **código de producción, testeable offline** con dobles: es el
grueso de la verificación automática de esta feature (§8).

---

## 4 · Autenticación y cadena de identidad

### 4.1 Easy Auth en el front

Mismo mecanismo que `partes/infra/setup_sv4_easyauth.ps1`, que a su vez copia
el de `albaranes-portal`:

1. Grupo de seguridad Entra `dedicacion-portal-users`.
2. App Registration propia (`dedicacion (front EasyAuth)`), con redirect
   `https://<fqdn-front>/.auth/login/aad/callback` y emisión de id token.
3. Client secret → Key Vault (`EASYAUTH-CLIENT-SECRET`) → secret del
   Container App por `keyvaultref`.
4. Enterprise App con **asignación requerida** y el grupo asignado: Entra
   solo emite token a los miembros (R36).
5. `--unauthenticated-client-action RedirectToLoginPage`: login obligatorio.
6. Admin-consent en mejor esfuerzo, para SSO silencioso desde el Portal.

El script es **idempotente**: relanzarlo reutiliza grupo, App, secret y
service principal. Si el paso de asignar el grupo falla por licencia
(requiere Entra ID P1), se anota y se resuelve por claim `groups`, como está
documentado en `partes`.

### 4.2 Cómo llega el usuario hasta la api

Ya está implementado y no se toca la lógica (R11):

```
Entra ──▶ Easy Auth ──▶ cabecera X-MS-CLIENT-PRINCIPAL-NAME
                            │
       services/dedicacion-front/interface_adapters/web/app.py::_usuario
                            │
                            ▼  cabecera X-Usuario
       services/dedicacion-api/.../deps.py::obtener_usuario ──▶ auditoría (tabla `evento`)
```

Un detalle que sí se cambia: `_usuario` cae en `settings.default_user` cuando
no hay cabecera, y hoy ese valor es `local`. En Azure se despliega
`DEFAULT_USER=desconocido` (R12), para que una petición sin identificar quede
registrada como tal en la auditoría y no con un nombre de aspecto legítimo.

### 4.3 La tarjeta del Portal Ruesma no se hace aquí

`front-portal` es el dueño de su catálogo (`azure-apps/portal.md` §8.2). Lo
que esta feature entrega es la **petición escrita** con lo que ese proyecto
necesita: URL del front, nombre y Object ID del grupo, categoría e icono
sugeridos. El GUID del grupo **no entra en el repositorio** (R21): se pasa
por el canal que use el humano.

---

## 5 · Secretos

Tres claves en `kv-dedicacion-<sufijo>` (RBAC, la MI con rol
`Key Vault Secrets User`, el operador con `Key Vault Secrets Officer`):

| Clave en Key Vault | Quién la consume | Como secret del Container App |
|---|---|---|
| `PG-PASSWORD` | api | `pg-password` |
| `SIGRID-API-FUNCTION-KEY` | api (lectura) y transfer (escritura) | `sigrid-key` |
| `EASYAUTH-CLIENT-SECRET` | front | `easyauth-client-secret` |

Se cargan con `infra/add_secrets_dedicacion.ps1`, que los pide por
`Read-Host -AsSecureString`: no se escriben en disco ni se imprimen.

**Lo que NO va al Key Vault:** las credenciales de administrador de
PostgreSQL. Con `AUTO_CREATE_DATABASE=false` (§3.5) el servicio no las
necesita, y lo que no se guarda no se filtra. Las usa el humano una vez, en
su sesión, al ejecutar `infra/crear_base_dedicacion.ps1`.

**Riesgo conocido, sin cerrar (D5).** La api y el transfer referencian **la
misma** function key de `sigrid-api`. Hoy lo que impide que la api escriba es
que su código no tiene rutas de escritura, no la credencial. Si `sigrid-api`
admite claves distintas por consumidor, la api debería llevar una que no
pueda escribir. Es una pregunta para el dueño de ese proyecto, no algo que se
decida aquí.

---

## 6 · Imágenes y despliegue

### 6.1 Tags fechados, no `latest`

`docs/CONVENTIONS.md` es explícito: «imágenes con tags fechados
(`rYYYYMMDD-HHmm`), nunca reescribir tags». **Nos separamos aquí de
`partes`**, que usa `latest` y por eso necesita `--revision-suffix` para
forzar el pull y no puede responder «qué código está corriendo» sin abrir
Azure. Con tag fechado:

| Repositorio en `acralbaranesdev` | Servicio |
|---|---|
| `dedicacion-api` | `services/dedicacion-api` |
| `dedicacion-front` | `services/dedicacion-front` |
| `dedicacion-transfer` | `services/dedicacion-transfer` |

`infra/build_images_dedicacion.ps1` calcula **un** tag por ejecución
(`r` + `yyyyMMdd-HHmm`), construye con `az acr build` (sin Docker local) y
**escribe el resultado en `infra/imagenes.json`**, que sí se versiona: es un
fichero de tags, no de secretos, y es lo que hace que «qué hay desplegado»
se responda desde git (R24).

El contexto de build se prepara como en `partes`: copia del servicio a un
directorio temporal excluyendo `.venv`, `.git`, `__pycache__`, `logs`,
`tests`, `*.env`, y con el `Dockerfile`/`.dockerignore` del propio servicio.
Aquí **no hace falta la carpeta `manifests/`** de `partes`: nuestros tres
servicios ya llevan (o llevarán, R26) su `Dockerfile` y su `requirements.txt`
dentro, que es donde deben estar.

### 6.2 El transfer no tiene Dockerfile

`services/dedicacion-transfer/` es el único sin `Dockerfile` ni
`.dockerignore` (`docs/ARCHITECTURE.md` §Infra ya lo avisa). Se crean, calcados
de los otros dos: `python:3.12-slim`, `requirements.txt` primero, `EXPOSE 8006`,
`CMD ["python", "main.py"]`, y `.dockerignore` excluyendo `.env`, `logs/`,
`tests/`, `__pycache__/`, `.venv/`. En el Container App se fija
`LOG_DIR=/tmp/logs` (el arranque escribe log de fichero y `/app` no tiene por
qué ser escribible).

### 6.3 Orden de despliegue y republicación

**transfer → api → front**, siempre: cada servicio antes que quien lo
consume. `infra/redeploy_dedicacion.ps1` reordena a ese orden lo que le pidan,
igual que `partes/infra/redeploy_partes.ps1`, y **aborta** si la app no existe
(republicar no es dar de alta).

---

## 7 · Ficheros

### 7.1 Ficheros a crear

**Infraestructura** (PowerShell 5.1, UTF-8 **con** BOM y CRLF salvo lo que se
diga; `docs/CONVENTIONS.md`):

| Ruta | Qué hace |
|---|---|
| `infra/README_dedicacion.md` | orden de ejecución, qué hace cada script, qué es MANUAL |
| `infra/00_vars_dedicacion.ps1` | nombres de recurso, `$TAGS`, mapa `$IMG`, marcadores `REDACTADO-VER-COPIA-LOCAL` para suscripción y tenant |
| `infra/00_capps_vars_dedicacion.ps1` | derivados: `$MI_ID`, `$KV_URI`, `$ACR_LOGIN`, `$PG_HOST` |
| `infra/fase1_infra_dedicacion.ps1` | RG, MI, roles (AcrPull, KV Secrets User), Log Analytics, Key Vault, CAE. **No** crea Storage |
| `infra/crear_base_dedicacion.ps1` | **una vez, por una persona**: base `dedicacion` + rol `dedicacion_app` + regla de firewall. Sin cambios a nivel de servidor |
| `infra/add_secrets_dedicacion.ps1` | carga las tres claves del §5 pidiéndolas de forma segura |
| `infra/build_images_dedicacion.ps1` | `az acr build` con tag fechado; actualiza `infra/imagenes.json` |
| `infra/create_transfer_dedicacion.ps1` | alta del transfer, interno, min 1/max 1, **modo pruebas por defecto** (R10) |
| `infra/create_api_dedicacion.ps1` | alta de la api, interna, cablea `TRANSFER_BASE_URL` |
| `infra/create_front_dedicacion.ps1` | alta del front, **externo**, cablea `API_BASE_URL` |
| `infra/setup_front_easyauth.ps1` | grupo, App Registration, Enterprise App, Easy Auth (§4.1) |
| `infra/redeploy_dedicacion.ps1` | rebuild + revisión nueva en orden transfer→api→front |
| `infra/imagenes.json` | **versionado**: tag publicado por servicio y fecha (R24) |
| `infra/.gitignore` | ignora `*.local.ps1` (los valores reales) |

**Código y tests:**

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/Dockerfile` | R26 |
| `services/dedicacion-transfer/.dockerignore` | R25 |
| `services/dedicacion-api/tests/test_f008_bootstrap_bbdd.py` | R13–R16 |
| `services/dedicacion-api/tests/test_f008_despliegue.py` | R8 |
| `services/dedicacion-front/tests/__init__.py` + `conftest.py` | el front no tenía suite; `harness/init.sh` lo avisa en cada ejecución |
| `services/dedicacion-front/tests/test_f008_identidad.py` | R11 |
| `tests/test_f008_infra_sin_secretos.py` | R21, R22 |
| `tests/test_f008_imagenes.py` | R24, R25, R26 |

**Documentación:**

| Ruta | Qué |
|---|---|
| `docs/INTEGRACION.md` | fuente de verdad de qué exponemos y qué consumimos (R29, R31) |
| `azure-apps/dedicacion.md` | **otro repositorio**: copia con cabecera de origen y fecha (R30) |

### 7.2 Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-api/config/settings.py` | `+ auto_create_database: bool = False` |
| `services/dedicacion-api/infrastructure/db/database.py` | cortocircuito de `asegurar_base_datos` + `BaseDatosNoExiste` |
| `services/dedicacion-api/main.py` | traducción del fallo de conexión al error con mensaje útil |
| `services/dedicacion-api/.env.example` | `+ AUTO_CREATE_DATABASE=true`, `+ TRANSFER_BASE_URL`, `+ TRANSFER_TIMEOUT_S` (hoy faltan los dos últimos, aunque el código los lee) |
| `services/dedicacion-front/.env.example` | comentario de que en Azure `DEFAULT_USER=desconocido` y `API_TIMEOUT_S=200` |
| `services/dedicacion-transfer/.env.example` | `+ LOG_DIR` |
| `docs/ARCHITECTURE.md` | §«Infra y despliegue» reescrita (R32); tabla de acceso a datos: dónde vive PostgreSQL una vez decidido D1; timeouts de §2.5 |
| `.gitignore` | nada nuevo si `infra/.gitignore` cubre `*.local.ps1`; si el humano prefiere raíz, ahí |
| `azure-apps/README.md` | **otro repositorio**: fila de `dedicacion.md` en la tabla de documentos |

### 7.3 Ficheros que NO se tocan

Los colindantes que tientan:

- `services/dedicacion-transfer/application/services/reglas_porcentajes.py`
  y `application/pipelines/registro_pipeline.py` — las reglas P1-P5 son de
  F-002, no de esta feature. Desplegar no cambia una regla.
- `services/dedicacion-api/infrastructure/db/orm_models.py` y `esquema.py` —
  el esquema es el que es; desplegar no añade columnas. (Si se eligiera
  esquema nominado en D1b **sí** habría que tocarlos: por eso hay que
  decidirlo antes, §3.4.)
- `services/dedicacion-front/static/js/app.js` — el front no gana lógica.
- `harness/features.json` y `progress/current.md` — los lleva el líder.
- `services/*/.env` — prohibido por `CLAUDE.md`, y además no versionados.
- `prueba_escritura_porcentajes.py` — el script de pruebas de escritura no
  cambia; lo que cambia es desde dónde se ejecuta.

---

## 8 · Qué es verificable automáticamente y qué no

**Esta feature es mayoritariamente scripts de infraestructura y acciones
sobre una suscripción de Azure.** Decirlo claro es parte del diseño, porque
el rigor declarado es `critico` y `CHECKPOINTS.md` no admite un N/A sin
motivo escrito.

### 8.1 Lo que sí se verifica con tests (y es donde se aplican las puertas)

El código de producción que esta feature toca de verdad es el **bootstrap de
la base de datos de `dedicacion-api`** (§3.5): un conmutador, un
cortocircuito y un error tipado con mensaje útil. Es pequeño, es peligroso
(hoy hace `CREATE DATABASE` contra un servidor ajeno) y se presta entero a
tests offline con dobles. Ahí van la **fase RED**, la **cobertura ≥ 80 % de
las líneas cambiadas** y la **campaña de mutación con cero supervivientes**.

Además hay tests que no son de adorno porque vigilan invariantes que un
descuido rompe de verdad:

| Test | Qué invariante fija |
|---|---|
| `tests/test_f008_infra_sin_secretos.py` | ningún GUID, contraseña, function key ni IP privada entra en `infra/`, `specs/` o `docs/`. Es un guardián permanente, no una comprobación de una vez; `postventa-incidencias` tiene el suyo por el mismo motivo |
| `tests/test_f008_imagenes.py` | `infra/imagenes.json` parsea, cubre los tres servicios y sus tags respetan `rAAAAMMDD-HHmm`; los tres servicios tienen `.dockerignore` y todos excluyen `.env` |
| `services/dedicacion-front/tests/test_f008_identidad.py` | la cabecera de Easy Auth se propaga como `X-Usuario` y, sin ella, se usa `DEFAULT_USER` |
| `services/dedicacion-api/tests/test_f008_despliegue.py` | `obtener_usuario` **no** valida nada: es el test que documenta por qué la api no puede tener ingress externo (R8) |

Nota sobre la puerta de mutación: `harness/alcance.py` solo considera
ficheros `.py` fuera de `tests/`, `specs/`, `progress/` y `docs/`. El alcance
de esta feature será, por tanto, **el bootstrap de la base de datos y poco
más** — que es exactamente donde se quiere la vigilancia. Los `.ps1` y los
`.md` no entran, y eso no es un hueco disimulado: es lo que la herramienta
puede medir.

### 8.2 Lo que NO se puede verificar con tests, y qué se hace en su lugar

| Qué | Por qué no | Qué se hace |
|---|---|---|
| Los scripts `.ps1` | Son PowerShell y su efecto es crear recursos de Azure. Un test que los ejecute gasta dinero y toca la suscripción | **Revisión** contra criterios escritos en `requirements.md` (R4, R7, R9, R10, R12, R17, R20, R23, R27) + ejecución MANUAL por el humano con su salida pegada |
| Que los recursos existan y estén bien configurados | Requiere la suscripción | **MANUAL (humano)**, con el comando `az` exacto en `tasks.md` y su resultado real pegado en `progress/` |
| Que Easy Auth deje pasar a los del grupo y no a los demás | Requiere Entra y dos usuarios | **MANUAL (humano)**, ventana de incógnito |
| Que los tres `/health` respondan | Requiere el despliegue vivo | **MANUAL (humano)** |
| Que el transfer siga en modo pruebas | Es una variable de entorno de un recurso | **MANUAL (humano)**, leyendo la variable y el `/health` |

Ninguna de estas casillas se marca N/A a secas: cada una tiene su comando y
su resultado esperado en `tasks.md`, y el resultado real va a
`progress/impl_F-008.md`, como exige el nivel `critico` de `CHECKPOINTS.md`.

---

## 9 · Riesgos y decisiones descartadas

| Riesgo | Consecuencia | Mitigación |
|---|---|---|
| **Escribir en Sigrid desde Azure sin querer** | Filas reales en el ERP | `OBRA_PRUEBAS_FORZAR=true` (R9), doble confirmación en el script (R10), y el transfer interno (R7) |
| **La fila de prueba viva en Sigrid** (`hmores.ide=403039`, parte `PT26/00296`, obra 0404), pendiente de que el humano la vea en el ERP | Probar desde Azure escribirá **más** líneas `PRUEBA-PORC` en la misma obra y mes, y mezclará las de F-002 con las nuevas | **No ejecutar `registro/ejecutar` desde el entorno desplegado hasta que el humano haya cerrado esa comprobación**. Consta en `tasks.md` como precondición de la fase 5 |
| Llenar el disco del servidor compartido | El servidor entero pasa a solo-lectura, y los otros cuatro proyectos con él (ya pasó el 2026-08-09) | Nuestro volumen es de kilobytes/año; queda escrito en `docs/INTEGRACION.md` con números, y no guardamos blobs ni JSON crudo |
| Desplegar con `CREATE DATABASE` al arranque | Un servicio ajeno creando bases y roles en un servidor de producción compartido | R13–R15, con tests |
| La api expuesta por descuido | Escritura en el ERP desde Internet | R7/R8, y el motivo escrito en `docs/INTEGRACION.md` para que nadie lo «arregle» abriendo el ingress |
| Nombre de Key Vault pillado (espacio mundial) | `fase1` falla a mitad | `$SUFFIX` cambiable y `fase1` idempotente: se relanza |
| El grupo Entra no se puede asignar a la Enterprise App por licencia (P1) | Easy Auth deja pasar a cualquiera del tenant | El script lo detecta y avisa; el humano decide (claim `groups` o licencia). Está documentado en `partes` |
| Cold start | Primera petición lenta y con pinta de caída | `min-replicas 1` en los tres. Es la palanca de coste si molesta (D4) |

**Alternativas descartadas**

1. **Un solo Container App con los tres servicios.** Rompe el límite de
   servicio y, sobre todo, mete la credencial de escritura de Sigrid en el
   mismo proceso que atiende a Internet.
2. **Copiar `partes` tal cual** (Storage, colas, `latest`, `PG_USER=admin`).
   Se copian las tres ideas buenas (Container Apps + MI + Key Vault; ingress
   interno para la pluma; Easy Auth con grupo) y se dejan fuera las que no
   aplican o que el propio ecosistema ya ha superado.
3. **Azure Container Instances / App Service.** El ecosistema entero está en
   Container Apps; salirse obliga a inventar el patrón de secretos, identidad
   y logs desde cero.
4. **Terraform/Bicep.** Todos los proyectos de la casa usan scripts `az` en
   PowerShell; introducir una herramienta nueva en la feature que estrena el
   despliegue de este proyecto multiplica lo que puede salir mal.
5. **Abrir la api al exterior «solo para probar».** Ver §2.1.

---

## 10 · El documento de `azure-apps`

Regla 1 de `azure-apps/README.md`: el dueño es el proyecto, la fuente de
verdad es `docs/INTEGRACION.md` **de este repositorio**, y `azure-apps` lleva
la copia. Estructura, siguiendo `postventa_incidencias.md` (el ejemplo más
reciente y mejor hecho):

1. Cabecera obligatoria: origen (repositorio + commit corto), fecha, aviso de
   que es copia y de que no lleva un solo valor de conexión, y **estado real
   al escribirlo** (qué existe ya en Azure y qué no).
2. **Qué consumimos hoy**: PostgreSQL (con quién se comparte), `sigrid-api`
   (lectura desde la api, escritura desde el transfer, base `ruesma`),
   `acralbaranesdev`, Entra ID.
3. **La base de datos**: qué pedimos, qué NO hacemos (la tabla de
   prohibiciones del §3.4) y por qué.
4. **Variables de entorno**: nombres, nunca valores.
5. **Qué le hacemos al servidor compartido, en números**: disco, volumen
   esperado, conexiones.
6. **Qué exponemos**: hoy nada hacia otros proyectos; el front para el
   Portal cuando ese proyecto ponga la tarjeta.
7. **Qué se rompe si alguien toca algo**, en las dos direcciones.
8. **Modo pruebas**: que el transfer escribe solo en la obra `0404` con marca
   `PRUEBA-PORC`, y que salir de ahí es una decisión expresa.
9. **Dónde está cada cosa**: scripts, specs, documento gemelo.

Se añade además su fila a la tabla de `azure-apps/README.md`. **El commit en
`azure-apps` lo hace el humano**: es otro repositorio.

---

## 11 · Encaje con `docs/ARCHITECTURE.md`

`docs/ARCHITECTURE.md` es normativo y dos de sus afirmaciones dejan de ser
ciertas al cerrar esta feature:

- §«Qué hace este proyecto»: «funciona en local, no hay nada desplegado en
  Azure».
- §«Infra y despliegue»: «No hay nada desplegado ni carpeta `infra/`».

Se reescriben con lo que quede desplegado, más: dónde vive PostgreSQL (una
vez cerrada D1), la tabla de timeouts de §2.5, y el recordatorio de que
`OBRA_PRUEBAS_FORZAR` sigue a `true`. Lo que **no** cambia es la sección de
semántica de dominio: esta feature no toca ni una regla.
