<!-- docs/INTEGRACION.md -->
# dedicación · integración con el ecosistema

> **Fuente de verdad** de qué expone y qué consume este proyecto (regla 1 de
> `azure-apps/README.md`). La copia de `azure-apps/dedicacion.md` se refresca
> desde aquí, no al revés.
>
> **Ni un valor de conexión** (regla 3): nombres de recurso y nombres de
> variable de entorno, nunca hosts, usuarios, contraseñas ni identificadores
> de suscripción, tenant u objeto. Lo vigila un test que falla si alguno
> entra: `tests/test_f008_infra_sin_secretos.py`.
>
> **Fecha del documento: 2026-08-20.**
>
> **Estado al escribirlo:** los scripts de despliegue existen y están
> revisados; **en Azure no hay nada creado todavía**. La ejecución es manual
> y la hace una persona (fase 7 de `specs/F-008-infra-azure/tasks.md`). Hasta
> entonces el sistema corre en local. Cuando el despliegue se haga, hay que
> volver aquí y actualizar esta cabecera y la §6 con el FQDN del front.

---

## 1 · Qué consumimos hoy

| Recurso | Compartido con | Qué hacemos | Desde |
|---|---|---|---|
| PostgreSQL `psql-albaranes-rs9k2` | `albaranes`, `partes`, `datamart-seg-anual`, `postventa-incidencias` | Base propia `dedicacion`: periodos, cuadrante, asignaciones y auditoría | **F-008** |
| `sigrid-api` (`func-sigridapi-dev-huyke`) | todo el ecosistema | **Lectura** de maestros desde la api; **escritura** de líneas de parte desde el transfer, siempre contra la base `ruesma` | F-001, F-002 |
| `acralbaranesdev` | `albaranes`, `partes` | Publicar y tirar las tres imágenes, por identidad gestionada | **F-008** |
| Entra ID | todo el ecosistema | Autenticación del front (Easy Auth) y grupo de acceso | **F-008** |

**Lo nuevo de F-008 son tres de esas cuatro filas.** La primera es la que
convierte a este proyecto en **quinto inquilino** de un servidor que ya usaban
otros cuatro, y por eso la §2 va entera sobre eso.

### Lo que NO consumimos, y consta para que nadie lo dé por hecho

- **El SQL Server de Sigrid directamente.** Nadie se conecta por SQL. Todo
  pasa por `sigrid-api`.
- **Storage Account, colas ni blobs.** No hay canal asíncrono: la cadena
  front → api → transfer es HTTP síncrono y el volumen es un cuadrante
  mensual por obra. `partes` los necesita porque su pipeline encadena cinco
  servicios por cola; aquí serían superficie de ataque y factura sin
  contrapartida.
- **La réplica `ruesma_rep`.** No admite escritura y no la usamos.

---

## 2 · La base de datos: qué pedimos y qué no tocamos

```
Servidor  psql-albaranes-rs9k2      COMPARTIDO — no tocamos nada suyo
   └── Base  dedicacion             propia; la crea una persona, una vez
         └── Esquema  public        (como albaranes y partes)
               ├── periodo              un mes, con su estado
               ├── asignacion           trabajador × obra × periodo, con % y traza a Sigrid
               ├── trabajador           maestro sincronizado desde Sigrid (solo lectura)
               ├── obra                 maestro sincronizado desde Sigrid (solo lectura)
               └── evento               auditoría: quién hizo qué y cuándo
```

**Base propia, esquema `public`.** La base propia es cómo aísla el ecosistema
(`albaranes`, `partes`, `sigrid_dm`, `postventa`: un servidor, varias bases).
El esquema es `public` **dentro de nuestra base**, como `albaranes` y
`partes`: la base no la comparte nadie, así que el esquema nominado que usa
`postventa` sería cinturón sobre tirantes a cambio de tocar el ORM y el
`search_path` de todas las sesiones. Se decidió **antes** de que hubiera
datos, que es cuando salía barato decidirlo.

### Lo que este proyecto NO hace, y consta por escrito

| No hacemos | Por qué |
|---|---|
| `CREATE DATABASE` ni `CREATE ROLE` desde la aplicación | Hasta F-008, `dedicacion-api` los ejecutaba **en cada arranque**, conectándose como administrador del servidor. Contra un servidor de producción compartido eso es justo lo que `CLAUDE.md` prohíbe. Ahora arranca con `AUTO_CREATE_DATABASE=false` y **ni siquiera abre esa conexión** |
| Desplegar credenciales de administrador del servidor | El servicio no las necesita, así que no se le dan: no están en el Key Vault, ni en la definición del Container App, ni en el repositorio. Las usa una persona, una vez, al crear la base. **`partes` desplegó con `PG_USER=<admin>` y eso puso la contraseña del administrador dentro de tres contenedores; aquí no se repite** |
| `ALTER SYSTEM`, `CREATE EXTENSION`, `GRANT` a nivel de servidor | Son cambios que afectan a los otros cuatro proyectos |
| Tocar el esquema `public` de ninguna otra base | Es donde trabajan `albaranes` y `partes` |
| Guardar ficheros, blobs o JSON crudo | El disco es compartido, **solo crece** y ya se llenó una vez (§4). En la base van filas de texto corto y números |
| Migraciones destructivas automáticas | El mecanismo de esquema solo **añade columnas**, derivadas del ORM. Cambiar un tipo, renombrar o mover datos exige una migración escrita por una persona |

La base y el rol de aplicación los crea `infra/crear_base_dedicacion.ps1`,
que por defecto **imprime el plan y no toca nada**: hace falta `-Confirmar`.
El rol se crea `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION`, y el
script **aborta** si se le intenta dar la contraseña del administrador.

---

## 3 · Variables de entorno (nombres, nunca valores)

Los nombres son deliberadamente los que ya usa el ecosistema, para que quien
despliegue no tenga que aprender dos vocabularios.

### `dedicacion-api`

| Variable | Notas |
|---|---|
| `PG_HOST`, `PG_PORT`, `PG_DB` | La base propia dentro del servidor compartido |
| `PG_USER` | **Rol de aplicación propio**, nunca el administrador del servidor |
| `PG_PASSWORD` | **Secreto**. Por referencia a Key Vault; jamás como valor |
| `PG_SSLMODE` | `require` en Azure. El defecto del código (`prefer`) acepta sin protestar una conexión sin cifrar |
| `AUTO_CREATE_DATABASE` | **`false` en Azure**, y `false` también por defecto en el código: una variable olvidada al desplegar tiene que hacer lo prudente |
| `PG_ADMIN_USER`, `PG_ADMIN_PASSWORD`, `PG_ADMIN_DB` | **No se despliegan.** Solo existen para el arranque en local |
| `SIGRID_API_BASE_URL`, `SIGRID_API_DATABASE`, `SIGRID_API_TIMEOUT_S`, `SIGRID_MAX_ROWS` | Lectura de maestros |
| `SIGRID_API_FUNCTION_KEY` | **Secreto**. Por referencia a Key Vault |
| `TRANSFER_BASE_URL`, `TRANSFER_TIMEOUT_S` | El registro en Sigrid, por HTTP interno |

### `dedicacion-front`

| Variable | Notas |
|---|---|
| `API_BASE_URL` | FQDN **interno** de la api, por `http://` |
| `API_TIMEOUT_S` | `200` en Azure (§5) |
| `DEFAULT_USER` | **`desconocido` en Azure.** Si llegara una petición sin cabecera de Easy Auth, la auditoría debe registrar que el usuario no se identificó, y no un nombre de aspecto legítimo |

### `dedicacion-transfer`

| Variable | Notas |
|---|---|
| `SIGRID_API_BASE_URL`, `SIGRID_API_DATABASE`, `SIGRID_EMPRESA` | La base es **siempre** `ruesma` |
| `SIGRID_API_FUNCTION_KEY` | **Secreto**. Es la credencial de **escritura** sobre el ERP |
| `OBRA_PRUEBAS_FORZAR`, `OBRA_PRUEBAS_COD`, `MARCA_PRUEBAS` | Modo pruebas (§8) |
| `LOG_DIR` | `/tmp/logs` en el contenedor: `/app` no tiene por qué ser escribible |

Secretos en el Key Vault propio, por su clave: `PG-PASSWORD`,
`SIGRID-API-FUNCTION-KEY`, `EASYAUTH-CLIENT-SECRET`.

---

## 4 · Qué le hacemos al servidor compartido, en números

**Disco.** 32 GB compartidos, el almacenamiento **solo crece, nunca decrece**,
y el punto de restauración es del **servidor entero**: no se puede volver
atrás nuestra base sin arrastrar las ajenas. El 2026-08-09 el disco llegó al
93,4 % y el servidor quedó en solo-lectura diez minutos por el build de otro
proyecto. Ese precedente es el motivo de que aquí no entre ni un fichero.

**Nuestro volumen es minúsculo, y se puede calcular.** Unos **156
trabajadores** con código de hora mensual, repartidos entre las obras en las
que participan, **doce periodos al año**. Aunque cada trabajador tocara cinco
obras, son del orden de **10.000 filas de asignación al año**, de unos cientos
de bytes cada una: **megabytes al año, no gigabytes**. Si algún día deja de
ser así, lo primero que crecerá es `asignacion`, y el primer sitio donde mirar
es esta sección.

**Conexiones.** Un solo servicio habla con la base (`dedicacion-api`), con un
pool de **5 conexiones + 5 de desbordamiento**, y **una sola réplica**
(`max-replicas 1`). El techo real es 10 conexiones, no una función que escale
sola.

**CPU y memoria.** No hay analítica, ni `VACUUM FULL`, ni cargas masivas: son
inserciones y actualizaciones de filas cortas con índices por periodo.

---

## 5 · Qué exponemos

**Hoy, hacia otros proyectos: nada.** Ni una API pública, ni una cola, ni una
tabla que nadie más lea. Este sistema es consumidor puro.

Lo único que se expone a Internet es el **front**, y para personas:

| Servicio | Ingress | Quién lo alcanza |
|---|---|---|
| `ca-dedicacion-front` | **externo** | Personas, con Easy Auth y pertenencia al grupo `dedicacion-portal-users` |
| `ca-dedicacion-api` | interno | Solo el front, desde dentro del Container Apps Environment |
| `ca-dedicacion-transfer` | interno | Solo la api |

### Por qué la api va interna, y por qué nadie debe «arreglarlo»

**La api no tiene autenticación propia.** Su único control de identidad es
`interface_adapters/api/deps.py::obtener_usuario`, que lee la cabecera
`X-Usuario` y se la cree; si no viene, usa `local` y **no rechaza la
petición**. Con ingress externo, cualquiera en Internet podría llamar a
`POST /api/v1/registro/ejecutar` poniendo la cabecera que quisiera; la api
llamaría al transfer, y el transfer es **la única pluma del sistema sobre el
ERP**.

Por tanto el ingress interno de la api **no es una preferencia de despliegue:
es su control de acceso**. La consecuencia que hay que aceptar es que la api
solo se alcanza a través del proxy del front autenticado
(`https://<fqdn-front>/api/v1/...`). No se abre un atajo «temporal» para
probar: los atajos temporales se quedan.

Hay un test que fija esa carencia y explica por qué existe
(`services/dedicacion-api/tests/test_f008_despliegue.py`). Si alguien añade
autenticación de verdad a la api, ese test falla, y ese fallo es la señal de
que la decisión de exposición se puede reabrir —a conciencia, no de pasada.

### La cadena de identidad

```
Entra ──▶ Easy Auth ──▶ X-MS-CLIENT-PRINCIPAL-NAME
                            │  (proxy del front)
                            ▼  X-Usuario
                        dedicacion-api ──▶ auditoría (tabla `evento`)
```

El `X-Usuario` que llegue **de fuera** se descarta: el proxy lo escribe él, no
lo reenvía. Si lo reenviara, cualquiera con sesión podría firmar la auditoría
con el nombre de otro.

### La tarjeta del Portal Ruesma

La añade el proyecto `front-portal`, que es el dueño de su catálogo. Lo que
este proyecto entrega es la petición: URL del front, nombre y Object ID del
grupo, categoría e icono. **El Object ID no entra en este repositorio.**

### Timeouts encadenados

Cada salto espera **más** que el siguiente, y todos por debajo del corte del
balanceador de Azure:

| Salto | Variable | Desplegado |
|---|---|---|
| navegador → front | (balanceador de Azure) | **230 s, no configurable** |
| front → api | `API_TIMEOUT_S` | **200 s** |
| api → transfer | `TRANSFER_TIMEOUT_S` | **180 s** |
| transfer → `sigrid-api` | `SIGRID_API_TIMEOUT_S` | 60 s |

Al revés, el de fuera se rinde antes y el usuario ve un error de una escritura
que sí se estaba haciendo. En local el front venía con 120 s y la api con
180 s: exactamente el caso malo.

---

## 6 · Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Scripts de despliegue y su manual | `infra/`, empezando por `infra/README_dedicacion.md` |
| Qué imagen hay publicada y cuándo | `infra/imagenes.json` (**versionado**) |
| Por qué cada decisión de infraestructura | `specs/F-008-infra-azure/` |
| Arquitectura y semántica de dominio | `docs/ARCHITECTURE.md` |
| La pasarela de Sigrid | `azure-apps/sigrid_api.md` |
| El diccionario de tablas de Sigrid | `azure-apps/sigrid_tablas.md` |
| Copia de este documento para el ecosistema | `azure-apps/dedicacion.md` |

| Recurso en Azure | Nombre |
|---|---|
| Resource group | `rg-dedicacion-dev` (`spaincentral`) |
| Container Apps | `ca-dedicacion-transfer`, `ca-dedicacion-api`, `ca-dedicacion-front` |
| Entorno | `cae-dedicacion-dev` |
| Identidad gestionada | `id-dedicacion-dev` |
| Key Vault | `kv-dedicacion-<sufijo>` |
| Logs | `log-dedicacion-dev` |
| Grupo de acceso | `dedicacion-portal-users` |

---

## 7 · Qué se rompe si alguien toca algo

### Si tocan algo nuestro

| Cambio | Qué se rompe |
|---|---|
| Abrir el ingress de la api | Cualquiera en Internet puede escribir el cuadrante y disparar el registro en el ERP suplantando a quien quiera (§5) |
| Subir `max-replicas` del transfer | La línea se inserta con `MAX(ide)+1` bajo `UPDLOCK, HOLDLOCK`: dos réplicas se pisan los `ide` |
| Subir `max-replicas` de la api | La sincronización de maestros y la sustitución atómica de asignaciones no están diseñadas para réplicas concurrentes |
| Poner `AUTO_CREATE_DATABASE=true` en Azure | El servicio volvería a intentar `CREATE ROLE` / `CREATE DATABASE` en un servidor de producción compartido, y necesitaría credenciales de administrador que hoy no se le dan |
| Bajar `API_TIMEOUT_S` por debajo de `TRANSFER_TIMEOUT_S` | El usuario ve un error de un registro que sí se está haciendo |
| Poner `OBRA_PRUEBAS_FORZAR=false` | Se escribe **de verdad** en las obras reales de Sigrid (§8) |
| Reescribir un tag de imagen ya publicado | Deja de poder saberse qué código está corriendo |

### Si tocan algo de otros

| Cambio ajeno | Qué nos rompe |
|---|---|
| Parámetros, autenticación o almacenamiento de `psql-albaranes-rs9k2` | Nos afecta igual que a los otros cuatro inquilinos. **Nosotros no los tocamos, y pedimos lo mismo** |
| Llenar el disco del servidor compartido | Pasa a solo-lectura y nos caemos con él (ya pasó el 2026-08-09) |
| Restaurar el servidor a un punto anterior | Arrastra **todas** las bases, la nuestra incluida |
| Rotar la function key de `sigrid-api` | Se caen la lectura de maestros **y** la escritura en el ERP. Hay que actualizar `SIGRID-API-FUNCTION-KEY` en el Key Vault y crear revisión nueva de api y transfer |
| Cambiar el contrato de `sigrid-api` (`/api/sql/read`, `/api/sql/write`) | Se cae todo: es nuestro único acceso a Sigrid |
| Borrar o renombrar `acralbaranesdev` | No se puede publicar ni tirar ninguna imagen |
| Cambiar tablas o campos de Sigrid (`hmo`, `hmores`, `reshor`) | El mapeo del transfer deja de casar |

**Petición abierta al proyecto `sigrid-api`:** hoy la api y el transfer
referencian **la misma** function key. Lo único que impide que la api escriba
en el ERP es que su código no tiene rutas de escritura, **no la credencial**.
Si `sigrid-api` admite claves distintas por consumidor, la api debería llevar
una que no pueda escribir.

---

## 8 · Modo pruebas: el transfer no escribe donde parece

`dedicacion-transfer` está desplegado con **`OBRA_PRUEBAS_FORZAR=true`**. Eso
significa que **toda** escritura, venga de donde venga, se desvía a la obra de
pruebas `0404` y se marca con `PRUEBA-PORC` en el campo `tex`, para poder
limpiarla después. Las obras reales no reciben nada.

Es el estado en el que **termina** la feature de despliegue, no un descuido.
Salir de ahí exige dos señales explícitas en el script de alta
(`-ModoProduccion -Confirmar`) **y una decisión expresa del humano para una
acción concreta**. Que el script lo permita no lo autoriza.

Comprobarlo desde fuera:

```powershell
az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev `
  --query "properties.template.containers[0].env[?name=='OBRA_PRUEBAS_FORZAR'].value" -o tsv
```

---

## 9 · Detalles que hacen perder una tarde

**`/health` del front no responde a un `curl` anónimo.** Con Easy Auth y login
obligatorio devuelve una **redirección al login**. No está caído: hay que
navegar con sesión iniciada. Es la clase de detalle que parece una caída
durante media mañana.

**La api y el transfer no son alcanzables desde fuera.** Es deliberado (§5).
Para probar la api, `https://<fqdn-front>/api/v1/health`, autenticado. Para el
transfer, `az containerapp logs show`.

**El endpoint de salud de la api es `/api/v1/health`, no `/health`.**

**Si la api arranca y dice que la base no existe**, es que falta ejecutar
`infra/crear_base_dedicacion.ps1`. El servicio ya no la crea solo, a
propósito, y el mensaje de error nombra la base que falta y el script que la
crea.
