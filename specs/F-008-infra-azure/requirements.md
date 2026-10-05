<!-- specs/F-008-infra-azure/requirements.md -->
# F-008 · Infraestructura y despliegue en Azure — Requisitos (EARS)

> Rama `feature/F-008-infra-azure` · `sdd: true` · rigor **crítico** ·
> prioridad 3.
>
> **Objetivo declarado por el humano el 2026-08-20**: desplegar para **poder
> hacer pruebas** en un entorno real. NO es un despliegue de producción con
> usuarios finales: es el paso que permite probar el sistema fuera del
> portátil. Todo lo que sigue está dimensionado para eso, y donde una
> decisión sería distinta en producción se dice.
>
> Patrón de referencia: `azure-apps/partes.md` §5 y los scripts de
> `partes/infra/`. Donde nos separamos de ese patrón, `design.md` dice por
> qué.

## 0 · Cómo se lee este documento

Cada requisito lleva su **verificación** al final. Hay tres clases, y la
distinción es el corazón de esta feature:

| Marca | Qué significa |
|---|---|
| **`test`** | Lo comprueba un test automático, offline, sin red ni BBDD. |
| **`revisión`** | Lo comprueba el reviewer leyendo un fichero del repositorio. No hay test posible (es un script PowerShell o un documento), pero el criterio es objetivo y está escrito. |
| **`MANUAL (humano)`** | Lo ejecuta o lo comprueba **una persona** contra Azure. **Ningún agente lo hace**: crea recursos, gasta dinero o toca la suscripción. |

El reparto no es un atajo: `design.md` §8 explica qué parte de esta feature
es verificable automáticamente y por qué el resto no lo es.

---

## 1 · Qué se despliega

**R1.** El sistema debe desplegarse como **tres Container Apps** en un
resource group propio `rg-dedicacion-dev` (región `spaincentral`):
`ca-dedicacion-transfer` (puerto 8006), `ca-dedicacion-api` (8090) y
`ca-dedicacion-front` (8080). Un servicio = un Container App; ninguno se
fusiona con otro.
*Verificación:* MANUAL (humano) ·
`az containerapp list -g rg-dedicacion-dev -o table` lista los tres.

**R2.** El sistema debe **reutilizar**, sin crearlos ni modificarlos a nivel
de recurso: el registro de contenedores `acralbaranesdev`, la pasarela
`sigrid-api` (`func-sigridapi-dev-huyke`) y —si se confirma la decisión
**D1**— el servidor PostgreSQL `psql-albaranes-rs9k2`.
*Verificación:* revisión (`infra/00_vars_dedicacion.ps1` declara los tres
como reutilizados y ningún script los crea) + MANUAL (humano).

**R3.** El sistema **no** debe crear Storage Account, colas ni contenedores
de blobs: no hay canal asíncrono en este proyecto, la comunicación
front→api→transfer es HTTP síncrono.
*Verificación:* revisión (ningún script de `infra/` ejecuta
`az storage ...`) + MANUAL (humano) ·
`az resource list -g rg-dedicacion-dev -o table`.

**R4.** CUANDO se cree el Container App del transfer, el sistema debe fijarlo
a **una sola réplica como máximo** (`--max-replicas 1`).
Motivo: la línea se inserta con `MAX(ide)+1` bajo `UPDLOCK, HOLDLOCK`
(`docs/ARCHITECTURE.md` §9); dos réplicas escribiendo a la vez se pisan los
`ide`.
*Verificación:* revisión (`infra/create_transfer_dedicacion.ps1`) + MANUAL
(humano) ·
`az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev --query "properties.template.scale"`.

**R5.** CUANDO se cree el Container App de la api, el sistema debe fijarlo
también a **una sola réplica como máximo**. Motivo: la sincronización de
maestros (`sync_pipeline`) y la sustitución atómica de asignaciones no están
diseñadas para varias réplicas concurrentes, y no hay ningún test que
demuestre lo contrario.
*Verificación:* revisión + MANUAL (humano), mismo comando que R4.

**R6.** El sistema debe llevar en los tres Container Apps y en el resource
group los cuatro tags obligatorios de Azure Policy (acens):
`acens-customer=Construcciones-Ruesma`, `acens-environment=dev`,
`acens-project=dedicacion`, `acens-responsable-so-app=pgris`.
*Verificación:* revisión (`$TAGS` en `infra/00_vars_dedicacion.ps1`, aplicado
en cada `create`) + MANUAL (humano).

---

## 2 · Exposición y seguridad

**R7.** El sistema debe exponer a Internet **únicamente** el front
(`--ingress external`). La api y el transfer deben llevar **ingress interno**
(`--ingress internal`), alcanzables solo desde dentro del Container Apps
Environment.
*Verificación:* revisión + MANUAL (humano) ·
`az containerapp show -n <app> -g rg-dedicacion-dev --query "properties.configuration.ingress.external"`
debe dar `true` solo en el front.

**R8.** SI la api tuviera ingress externo, ENTONCES cualquiera en Internet
podría escribir el cuadrante y disparar `registro/ejecutar`: la api **no
tiene autenticación propia** —`interface_adapters/api/deps.py:92`
(`obtener_usuario`) se limita a leer la cabecera `X-Usuario` y, si no viene,
usa `"local"`—, y `registro/ejecutar` llama al transfer, que es la única
pluma del sistema sobre Sigrid. Por tanto el ingress interno de la api **no
es una preferencia, es un requisito de seguridad**, y ninguna tarea de esta
feature puede relajarlo.
*Verificación:* `test` (existe un test que fija que `obtener_usuario` no
valida nada y que por tanto la api no puede quedar expuesta: es la razón
escrita del requisito) + revisión + MANUAL (humano).

**R9.** MIENTRAS el transfer esté desplegado, el sistema debe mantenerlo con
`OBRA_PRUEBAS_FORZAR=true`: toda escritura va a la obra `0404` con la marca
`PRUEBA-PORC` en `tex` (`docs/ARCHITECTURE.md`
[`#regla-pruebas`](../../docs/ARCHITECTURE.md#regla-pruebas)). Esta feature
**termina con el transfer en modo pruebas**.
*Verificación:* revisión + MANUAL (humano) ·
`az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev --query "properties.template.containers[0].env[?name=='OBRA_PRUEBAS_FORZAR'].value"`
debe devolver `true`.

**R10.** SI alguien ejecuta el script de alta del transfer con la intención
de salir del modo pruebas, ENTONCES el script debe exigir **dos** señales
explícitas (un conmutador de modo producción **y** un `-Confirmar`) e
imprimir un aviso en rojo antes de actuar. El valor por defecto del script es
**modo pruebas**.
*Nota:* esto no autoriza el cambio. Salir del modo pruebas es una decisión
del humano, posterior a esta feature y para una acción concreta
(`CLAUDE.md`, reglas duras).
*Verificación:* revisión (`infra/create_transfer_dedicacion.ps1`).

**R11.** CUANDO el front reciba una petición autenticada por Easy Auth, el
sistema debe traducir la cabecera `X-MS-CLIENT-PRINCIPAL-NAME` a `X-Usuario`
al hacer proxy hacia la api. Ese es el único camino por el que la identidad
del usuario llega al backend.
*Verificación:* `test` (ya existe el mecanismo en
`services/dedicacion-front/interface_adapters/web/app.py`; el test fija que
la cabecera de Easy Auth se propaga y que sin ella se usa el valor de
`DEFAULT_USER`).

**R12.** MIENTRAS el front esté desplegado en Azure, `DEFAULT_USER` debe
valer `desconocido` y no `local`. Motivo: si por cualquier motivo llegara una
petición sin cabecera de Easy Auth, la auditoría debe registrar que el
usuario **no se identificó**, no un nombre que parece legítimo.
*Verificación:* revisión (`infra/create_front_dedicacion.ps1`) + MANUAL
(humano).

---

## 3 · La base de datos `dedicacion`

> **Dónde vive es la decisión D1 y la toma el humano.** Las opciones y sus
> consecuencias están en `design.md` §3; las decisiones abiertas, en
> `progress/spec_F-008.md`. Los requisitos de esta sección valen para
> **cualquiera** de las opciones, porque lo que fijan es cómo se comporta
> nuestro código frente a un servidor que no es nuestro.

**R13.** El sistema **no** debe ejecutar `CREATE DATABASE` ni `CREATE ROLE`
al arrancar contra un servidor desplegado. Hoy
`services/dedicacion-api/infrastructure/db/database.py::asegurar_base_datos`
lo hace en cada arranque, con credenciales de administrador del servidor.
*Verificación:* `test`.

**R14.** El sistema debe ofrecer un conmutador de configuración
`AUTO_CREATE_DATABASE` en `dedicacion-api`. Su valor por defecto es
**`false`** (seguro por defecto): una variable olvidada al desplegar hace lo
prudente, no lo peligroso. El `.env.example` local lo trae a `true`.
*Verificación:* `test`.

**R15.** MIENTRAS `AUTO_CREATE_DATABASE` sea `false`, el arranque **no debe
abrir siquiera la conexión de administración**. No basta con no ejecutar el
DDL: si no se abre la conexión, el servicio no necesita —ni puede filtrar—
las credenciales de administrador del servidor compartido.
*Verificación:* `test` (con `psycopg.connect` sustituido por un doble que
falla si lo llaman).

**R16.** SI `AUTO_CREATE_DATABASE` es `false` y la base de datos no existe,
ENTONCES el sistema debe fallar al arrancar con un mensaje que **nombre la
base que falta y el script que la crea** (`infra/crear_base_dedicacion.ps1`),
en vez de con el error crudo del driver.
*Verificación:* `test`.

**R17.** MIENTRAS el servicio corra en Azure, `PG_SSLMODE` debe valer
`require`. Azure Database for PostgreSQL Flexible Server exige TLS y el
defecto actual del código (`prefer`) acepta silenciosamente una conexión sin
cifrar.
*Verificación:* revisión (`infra/create_api_dedicacion.ps1`) + MANUAL
(humano).

**R18.** DONDE se confirme la opción A de D1 (base propia en el servidor
compartido `psql-albaranes-rs9k2`), el sistema debe crear la base y el rol de
aplicación **una sola vez y desde un script ejecutado por una persona**
(`infra/crear_base_dedicacion.ps1`), nunca desde el arranque de un servicio,
y ese script **no** debe contener `ALTER SYSTEM`, `CREATE EXTENSION` ni
ningún cambio a nivel de servidor.
*Verificación:* revisión + MANUAL (humano). Es el mismo criterio que
`postventa-incidencias` dejó escrito en `azure-apps/postventa_incidencias.md`
§2 tras ser el cuarto inquilino de ese servidor.

---

## 4 · Secretos

**R19.** El sistema debe guardar **todos** los secretos en un Key Vault
propio (`kv-dedicacion-<sufijo>`) y consumirlos desde los Container Apps por
`keyvaultref` con la **identidad gestionada** `id-dedicacion-dev`. Ningún
secreto viaja como valor en la definición del Container App, ni en un
`.env`, ni en la imagen.
*Verificación:* revisión + MANUAL (humano) ·
`az containerapp show -n <app> -g rg-dedicacion-dev --query "properties.configuration.secrets[].{n:name,kv:keyVaultUrl}"`
muestra `keyVaultUrl` en todos.

**R20.** El sistema debe acceder a `acralbaranesdev` por **identidad
gestionada** (`--registry-identity`), nunca por usuario admin del registro:
ese usuario está deshabilitado en la suscripción.
*Verificación:* revisión + MANUAL (humano).

**R21.** El repositorio **no** debe contener ningún secreto ni identificador
de la suscripción: ni contraseñas, ni cadenas de conexión, ni function keys,
ni IDs de suscripción, tenant, aplicación, grupo u objeto, ni IPs internas.
Los valores reales viven en ficheros `infra/*.local.ps1`, **no versionados**.
*Verificación:* `test` (barrido automático del árbol `infra/` con los
patrones de GUID, `AccountKey=`, `password=`, IP privada y clave larga en
base64; falla si alguno entra). Es el mismo guardián que
`postventa-incidencias` tiene en su repositorio.

**R22.** El sistema debe nombrar los secretos por su **clave en Key Vault**
en toda la documentación y en las specs: `PG-PASSWORD`,
`SIGRID-API-FUNCTION-KEY`, `EASYAUTH-CLIENT-SECRET`. Nunca por su valor.
*Verificación:* `test` (el barrido de R21 cubre también `specs/`, `docs/` e
`infra/`).

---

## 5 · Imágenes y despliegue

**R23.** El sistema debe publicar las imágenes en `acralbaranesdev` con
**tag fechado** `rAAAAMMDD-HHmm`, y **nunca reescribir un tag ya publicado**
(`docs/CONVENTIONS.md`, bloque «Convenios del entorno de Ruesma»). No se usa
`latest`.
*Verificación:* revisión (`infra/build_images_dedicacion.ps1`) + MANUAL
(humano) ·
`az acr repository show-tags -n acralbaranesdev --repository dedicacion-api -o table`.

**R24.** CUANDO se construya una imagen, el sistema debe dejar escrito en el
repositorio, en un fichero versionado (`infra/imagenes.json`), qué tag se ha
publicado para cada servicio y cuándo. Motivo: con tag fechado, «qué código
está corriendo» tiene que poder responderse desde git, sin abrir Azure.
*Verificación:* `test` (el fichero parsea, tiene una entrada por servicio y
los tags respetan el formato `rAAAAMMDD-HHmm`).

**R25.** El sistema **no** debe incluir el `.env` de ningún servicio en la
imagen.
*Verificación:* `test` (los tres servicios tienen `.dockerignore` y todos
excluyen `.env`).

**R26.** El sistema debe dar al transfer un `Dockerfile` propio: hoy es el
único servicio que no lo tiene (`services/dedicacion-transfer/`), y sin él no
hay imagen que desplegar.
*Verificación:* `test` (existe el fichero y su `EXPOSE`/`CMD` son coherentes
con el puerto 8006 y con `python main.py`) + MANUAL (humano) (el build real).

**R27.** CUANDO se despliegue o se republique, el sistema debe hacerlo en el
orden **transfer → api → front**: cada servicio antes que quien lo consume.
*Verificación:* revisión (`infra/redeploy_dedicacion.ps1` reordena lo que le
pidan a ese orden fijo, como hace `partes/infra/redeploy_partes.ps1`).

**R28.** MIENTRAS el sistema esté desplegado, los timeouts encadenados deben
ser **crecientes hacia dentro** y todos por debajo del corte del balanceador
de Azure (**230 s**, `azure-apps/sigrid_api.md` §3.4): front→api ≥ api→transfer.
Hoy no lo son (front `API_TIMEOUT_S=120` < api `TRANSFER_TIMEOUT_S=180`): el
front se rendiría mientras la api sigue registrando en Sigrid, y el usuario
vería un error de una escritura que sí se hizo.
*Verificación:* revisión (los valores desplegados están en los scripts de
`infra/` y en `docs/ARCHITECTURE.md`) + MANUAL (humano).

---

## 6 · Documentación del ecosistema

**R29.** El sistema debe tener un documento de integración propio en este
repositorio, `docs/INTEGRACION.md`, que es la **fuente de verdad** de qué
expone y qué consume el proyecto (regla 1 de `azure-apps/README.md`).
*Verificación:* revisión.

**R30.** El sistema debe dejar una **copia** de ese documento en
`azure-apps/dedicacion.md`, con la cabecera obligatoria de origen
(repositorio y commit) y fecha, y añadir su fila a la tabla de documentos de
`azure-apps/README.md`.
*Verificación:* revisión + MANUAL (humano) (el commit en `azure-apps` es de
otro repositorio y lo hace el humano).

**R31.** El documento debe cubrir, como mínimo: **qué consumimos** (servidor
PostgreSQL, `sigrid-api`, ACR, Entra ID), **qué exponemos** (hoy: nada hacia
otros proyectos, salvo la URL del front para la tarjeta del portal), **qué le
hacemos al servidor compartido** en números (disco, conexiones), **qué se
rompe si alguien toca algo** y **dónde está cada cosa**. Sin un solo valor de
conexión (regla 3 de `azure-apps/README.md`).
*Verificación:* revisión + `test` (el barrido de R21 alcanza `docs/`).

**R32.** El sistema debe actualizar `docs/ARCHITECTURE.md` §«Infra y
despliegue», que hoy dice «No hay nada desplegado ni carpeta `infra/`».
*Verificación:* revisión.

---

## 7 · Verificación del despliegue

**R33.** CUANDO el despliegue esté hecho, los tres servicios deben responder
a su endpoint de salud:

| Servicio | Endpoint | Cómo se comprueba |
|---|---|---|
| front | `GET /health` | navegador **con sesión de Easy Auth**; anónimo redirige al login (ver R35) |
| api | `GET /api/v1/health` | a través del proxy del front: `https://<fqdn-front>/api/v1/health` |
| transfer | `GET /health` | ingress interno, no alcanzable desde fuera: por `az containerapp logs` y por la variable de entorno (R9) |

*Verificación:* MANUAL (humano). Comandos exactos en `tasks.md`.

**R34.** CUANDO se consulte la salud del transfer, la respuesta debe declarar
`modo_pruebas: true` y `database: "ruesma"`. Ya lo hace
(`services/dedicacion-transfer/interface_adapters/api/app.py`): es la prueba
más directa de R9.
*Verificación:* MANUAL (humano).

**R35.** SI se pide `/health` del front sin sesión, ENTONCES Easy Auth
redirige al login y la comprobación anónima **no** es posible. Esto debe
constar por escrito: es la clase de detalle que hace perder una tarde
creyendo que el servicio está caído.
*Verificación:* revisión (consta en `docs/INTEGRACION.md` y en `tasks.md`) +
MANUAL (humano).

**R36.** CUANDO alguien acceda al front sin pertenecer al grupo de seguridad
`dedicacion-portal-users`, Entra debe negarle el token: la Enterprise App se
crea con **asignación requerida** y el grupo asignado a ella.
*Verificación:* MANUAL (humano) (ventana de incógnito con un usuario ajeno al
grupo).

---

## 8 · Lo que esta feature NO hace

Declarado para que nadie lo dé por incluido:

| Fuera de alcance | Por qué |
|---|---|
| Poner `OBRA_PRUEBAS_FORZAR=false` | Decisión aparte, posterior y del humano, para una acción concreta (`CLAUDE.md`). |
| Añadir la tarjeta de «Dedicación» al Portal Ruesma | El dueño del catálogo es el proyecto `front-portal`. Aquí se deja **escrita la petición** (URL del front y GUID del grupo); el cambio lo hace ese proyecto (`azure-apps/portal.md` §8.2). |
| Canal asíncrono por colas | No hay volumen que lo justifique (R3). Si algún día el registro de un mes tarda más de 230 s, se abre feature propia, con el precedente de F-002 de `partes`. |
| CI/CD, pipelines, DNS propio, blue/green | Los scripts los ejecuta una persona. Un entorno de pruebas no lo necesita. |
| Health probes explícitas en los Container Apps | Se usan las de plataforma por defecto. Ajustarlas exige manifiesto YAML; no aporta nada al objetivo «poder probar». |
| Esquema PostgreSQL nominado en vez de `public` | Sub-decisión **D1b** de `design.md` §3.4; la base es propia, no compartida, y `albaranes` y `partes` usan `public` en la suya. |
| Migraciones (Alembic) | El mecanismo de esquema actual solo añade columnas y eso sigue bastando (`docs/CONVENTIONS.md`, SQL). |
| Un test que cruce los timeouts de dos servicios | Sería atar la suite de un servicio al monorepo, que es justo la avería abierta en **F-012**. Se verifica por revisión (R28). |

---

## 9 · Trazabilidad

| Requisito | Verificación | Dónde |
|---|---|---|
| R1, R2, R3, R6 | MANUAL + revisión | `tasks.md` fase 4 |
| R4, R5, R7, R9, R10, R12, R17, R20, R23, R27, R28 | revisión + MANUAL | scripts de `infra/` |
| R8 | test + revisión | `services/dedicacion-api/tests/test_f008_despliegue.py` |
| R11 | test | `services/dedicacion-front/tests/test_f008_identidad.py` |
| R13, R14, R15, R16 | test | `services/dedicacion-api/tests/test_f008_bootstrap_bbdd.py` |
| R18 | revisión + MANUAL | `infra/crear_base_dedicacion.ps1` |
| R21, R22 | test | `tests/test_f008_infra_sin_secretos.py` |
| R24, R25, R26 | test | `tests/test_f008_imagenes.py` |
| R29, R30, R31, R32 | revisión | `docs/INTEGRACION.md`, `azure-apps/dedicacion.md` |
| R33, R34, R35, R36 | MANUAL | `tasks.md` fase 5 |

> **Nota de rigor.** Nueve requisitos de este documento tienen test
> automático y el resto no puede tenerlo: son scripts de infraestructura y
> acciones sobre una suscripción de Azure. `design.md` §8 lo desarrolla y
> dice qué se hace en su lugar. No se han inventado tests de adorno para
> cuadrar el expediente.
