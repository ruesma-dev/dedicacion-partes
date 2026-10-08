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
> **Fecha del documento: 2026-10-06** (F-039: las partidas de la obra de
> obras varias desde la 29 se ofrecen como obras propias `VAR-NN`; el
> transfer expone, solo hacia la api, `POST /api/var/universo`, y la api lo
> llama en cada sync y en el preview: si el transfer no responde, el sync
> falla entero con 502; las columnas `obra.registro_obra_ide`,
> `registro_obra_cod` y `registro_paride` las añade la api al arrancar; y
> fuera las obras con 6 o más dígitos seguidos en el código; §3, §5 y §7).
> **Origen:** rama `feature/F-039-obras-var-y-seis-digitos`, pendiente de
> merge a `dev`. Versión anterior: 2026-10-06 (F-037: el transfer rellena la
> cuenta analítica de cada línea, `hmores.caaide`, y no escribe nunca en un
> parte cerrado: las líneas van a un parte complementario; lee además los
> partes del periodo con su estado, las cuentas del centro y las de las
> partidas; §1 y §7; rama `feature/F-037-asiento-analitico-obra`).
> Versión anterior: 2026-10-04 (F-027:
> `X-Usuario` decide además quién puede deshacer; §5, «La cadena de
> identidad»; rama `feature/F-027-deshacer-por-usuario`).
> Versión anterior: 2026-10-03 (F-025: las obras de postventa salen
> de las partidas de la obra de postventa; el transfer expone, solo hacia la
> api, `POST /api/postventa/universo`, y la api lo llama en cada sync y en
> el preview: si el transfer no responde, el sync falla entero con 502, §5 y
> §7; la columna `obra.admite_postventa` la añade la api al arrancar).
> **Origen:** rama `feature/F-025-obras-postventa-postv2`, pendiente de
> merge a `dev`. Versión anterior: 2026-10-02, F-026 (el trabajador es el
> **recurso** de Sigrid; cada línea del registro lleva `recurso_ide`).
>
> **Estado: DESPLEGADO.** El 2026-08-20 se ejecutó la fase 7 y los tres
> servicios están arriba en `rg-dedicacion-dev`, con Easy Auth activo. El
> **2026-10-01** se republicaron con F-022, F-023, F-024 y F-032: imágenes
> `dedicacion-transfer:r20261001-1805`, `dedicacion-api:r20261001-1807` y
> `dedicacion-front:r20261001-1808`. El **2026-10-02** se republicaron con
> F-034 y F-026 (`dedicacion-transfer:r20261002-1705`, `dedicacion-api:r20261002-1706` y
> `dedicacion-front:r20261002-1708`, `infra/imagenes.json`), con el vaciado de los
> datos de prueba de `dedicacion` (§2) y un sync inmediato. El **2026-10-03** se
> republicaron con F-025 (`dedicacion-transfer:r20261003-1444`, `dedicacion-api:r20261003-1446` y `dedicacion-front:r20261003-1447`,
> en el orden transfer → api → front que exige §7). El **2026-10-05** se
> republicó solo la api con F-027 (`dedicacion-api:r20261005-0915`). El
> **2026-10-06** se republicaron la api y el front con F-029 (`dedicacion-api:r20261006-1140` y `dedicacion-front:r20261006-1141`).
> El **2026-10-07** se republicaron los tres con F-037, F-039 y F-040 (`dedicacion-transfer:r20261007-0851`, `dedicacion-api:r20261007-0852` y `dedicacion-front:r20261007-0853`,
> en el orden transfer → api → front que exige §7). Ese mismo día, por la tarde, se
> republicó solo el front con F-041 y F-042 (`dedicacion-front:r20261007-1734`; sin cambios de contrato).
> Esa noche, solo el transfer con F-047 (`dedicacion-transfer:r20261007-2029`; `SIGRID_MAX_ROWS` con su defecto, 200.000).
> El **2026-10-08**, solo la api con F-045 (`dedicacion-api:r20261008-1509`; el Excel pasa a Obras, Postventa y Detalle, sin Resumen, con
> la columna Observaciones; sin cambios de contrato).
>
> **Desde el 2026-10-01 el transfer desplegado escribe DE VERDAD**
> (`OBRA_PRUEBAS_FORZAR=false`), por decisión expresa del humano, tomada a
> sabiendas de lo que sigue abierto: la imputación a partidas no la ha
> validado Administración (F-017) y un trabajador con varios códigos M* toma
> el primero alfabético (F-011). Desde F-026 el recurso de cada línea lo
> manda la api (`docs/ARCHITECTURE.md#regla-recurso`).
> Detalle y cómo volver a modo pruebas: §8.
>
> **URL del front:**
> `https://ca-dedicacion-front.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io`
>
> **En uso desde el 2026-08-21.** Se entra por la tarjeta **«Dedicación»** del
> Portal Ruesma (categoría *Obra*), y el permiso lo da la pertenencia al grupo
> `dedicacion-portal-users`, con **asignación requerida**: tener cuenta de
> Ruesma **no** basta. Para dar acceso a alguien nuevo, ver §5.

---

## 1 · Qué consumimos hoy

| Recurso | Compartido con | Qué hacemos | Desde |
|---|---|---|---|
| PostgreSQL `psql-albaranes-rs9k2` | `albaranes`, `partes`, `datamart-seg-anual`, `postventa-incidencias` | Base propia `dedicacion`: periodos, cuadrante, asignaciones y auditoría | **F-008** |
| `sigrid-api` (`func-sigridapi-dev-huyke`) | todo el ecosistema | **Lectura** de maestros desde la api (empleados, obras y, desde F-032, el catálogo de empresas `auxemp`); **escritura** de líneas de parte desde el transfer, siempre contra la base `ruesma`. Desde F-037 el transfer lee además los partes del periodo con su estado (`hmo` + `con.est`), las cuentas analíticas del centro de la obra (`caa` + `con`), la cuenta de la plantilla del recurso (`reshor.caaide`) y la de la partida (`obrparpar.caaide`); un `truncated` es error y no se escribe nada | F-001, F-002, F-037 |
| `acralbaranesdev` | `albaranes`, `partes` | Publicar y tirar las tres imágenes, por identidad gestionada | **F-008** |
| Entra ID | todo el ecosistema | Autenticación del front (Easy Auth) y grupo de acceso | **F-008** |

**El parte de Sigrid se comparte con `partes`** (F-037): los dos servicios
escriben líneas en el **mismo** parte de obra y mes, y eligen igual en cuál
(el En registro de mayor `ide`; si todos están cerrados, un complementario
`Parte <obra>` que cualquiera de los dos reutiliza). Las reglas son copia
literal de las de `partes` (`estado_parte.py`, `cuenta_analitica.py`). El
asiento analítico (`ANA`) **no** lo escribe el transfer: lo genera Sigrid
cuando Administración pulsa «Contabiliza parte…», que deja el parte en
Imputado; desde entonces el transfer no escribe en él.

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
               ├── empresa              catálogo `auxemp` sincronizado desde Sigrid (solo lectura, F-032)
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

**Vaciado de los datos de prueba (F-026, una vez).** Al desplegar F-026 la
clave del trabajador pasa a ser el `res.ide` del recurso y lo que hay en la
base son pruebas que no se migran: lo vacía una persona, con autorización
expresa, con `infra/vaciar_datos_prueba_dedicacion.ps1` (plan por defecto,
`-Confirmar` para ejecutar; contraseña del rol de aplicación, no la del
administrador). Ejecuta **una** sentencia dentro de nuestra base,
`TRUNCATE TABLE asignacion, evento, periodo, trabajador CONTINUE IDENTITY`:
ni `obra` ni `empresa`, ni otras bases, ni nada del servidor. Orden y
motivo: `infra/README_dedicacion.md` §3 bis.

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
| `EMPRESA_IMPUTACION` | **Empresa de las obras** (`con.emp` de Sigrid): la de las obras que se ofrecen, postventa incluida, y la que viaja en cada línea del registro, sea cual sea la elegida en el selector (F-034). Es además la **empresa por defecto** del selector: la que sale elegida al entrar y la que se usa si una petición no trae empresa. `1` por defecto; entero > 0 o la api no arranca |

### `dedicacion-front`

| Variable | Notas |
|---|---|
| `API_BASE_URL` | FQDN **interno** de la api, por `http://` |
| `API_TIMEOUT_S` | `200` en Azure (§5) |
| `DEFAULT_USER` | **`desconocido` en Azure.** Si llegara una petición sin cabecera de Easy Auth, la auditoría debe registrar que el usuario no se identificó, y no un nombre de aspecto legítimo |

### `dedicacion-transfer`

| Variable | Notas |
|---|---|
| `SIGRID_API_BASE_URL`, `SIGRID_API_DATABASE` | La base es **siempre** `ruesma`. **No hay `SIGRID_EMPRESA`** desde F-022: la empresa llega en cada línea, y una variable que quede en un despliegue viejo se ignora |
| `SIGRID_API_FUNCTION_KEY` | **Secreto**. Es la credencial de **escritura** sobre el ERP |
| `SIGRID_MAX_ROWS` | Filas por lectura (`max_rows`) que el transfer pide a `sigrid-api`. **200.000 por defecto en el código** (F-047): no hace falta declararla al desplegar. Tiene que caber en el `MAX_ALLOWED_ROWS` de `sigrid-api` (500.000 en la instancia desplegada). Hasta F-047 era 2.000 fijo y las obras con más partidas no se podían registrar (la 0696 tiene 3.024). Una respuesta `truncated` sigue siendo un error: nunca se decide con filas parciales |
| `OBRA_PRUEBAS_FORZAR`, `OBRA_PRUEBAS_COD`, `MARCA_PRUEBAS` | Modo pruebas (§8) |
| `VAR_OBRA_COD`, `VAR_PARTIDA_DESDE` | Obra de obras varias y número inicial desde el que sus partidas se ofrecen como obras propias (F-039, `docs/ARCHITECTURE.md#regla-var`). Con defecto en el código (`VAR`, `29`): no hace falta declararlas al desplegar. `VAR_OBRA_COD` vacío = sin entradas VAR |
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

**Cómo se llega**: por la tarjeta **«Dedicación»** del Portal Ruesma
(categoría *Obra*), que apunta al FQDN del front. La tarjeta vive en
`front-portal/public/assets/js/catalog.js` y solo la ven quienes están en el
grupo. También se puede entrar por la URL directa: el control de acceso no es
la tarjeta, es Easy Auth.

Lo único que se expone a Internet es el **front**, y para personas:

| Servicio | Ingress | Quién lo alcanza |
|---|---|---|
| `ca-dedicacion-front` | **externo** | Personas, con Easy Auth y pertenencia al grupo `dedicacion-portal-users` |
| `ca-dedicacion-api` | interno | Solo el front, desde dentro del Container Apps Environment |
| `ca-dedicacion-transfer` | interno | Solo la api |

Desde F-024 la api sirve además, **solo para el front**, `GET
/api/v1/empresas` (empresas del selector y la por defecto; desde F-032,
con el nombre de Sigrid y `de_baja`) y acepta el
parámetro `empresa` (entero > 0, si no 422) en las rutas de
`/api/v1/periodos/...`. Siguen siendo internas: no se exponen a otros
proyectos.

Desde F-029 la api sirve además, **solo para el front**, `POST
/api/v1/periodos/{anio}/{mes}/completar` (`{trabajadores: [ide], obra_ide,
es_postventa}`, con el mismo parámetro `empresa`): pone a cada trabajador lo
que le falta hasta el 100 % en esa obra, en una transacción, y devuelve el
resultado de cada uno y el resumen. Escribe solo en la base `dedicacion`:
**no llama al transfer ni a `sigrid-api`**. Interna como las demás. La regla
está en `docs/ARCHITECTURE.md#regla-completar`.

Desde F-025 el transfer expone, **solo para la api**, `POST
/api/postventa/universo` (`{empresa, obras: [{ide, codigo, nombre}]}` →
las obras que admiten postventa, con su partida; 422 sin empresa válida,
502 si falla la lectura de Sigrid; nunca escribe). La api lo llama **una
vez** en cada `POST /api/v1/sync` y en cada `GET /api/v1/sync/preview`, con
la empresa de las obras (`EMPRESA_IMPUTACION`): son dos lecturas de Sigrid
(la obra de postventa y su presupuesto), dentro de `TRANSFER_TIMEOUT_S`. La
regla está en `docs/ARCHITECTURE.md#regla-p5`.

Desde F-039 el transfer expone además, **solo para la api**, `POST
/api/var/universo` (`{empresa}` → la obra VAR de esa empresa y sus partidas
VAR, `{ide, cod, res}` por `ide`, con el umbral y el motivo si no hay obra;
422 sin empresa válida, 502 si falla la lectura de Sigrid; nunca escribe).
La api lo llama **una vez** en cada `POST /api/v1/sync` y en cada `GET
/api/v1/sync/preview`, con la empresa de las obras: dos lecturas de Sigrid
(la obra VAR y su presupuesto). Las líneas del registro ganan un campo
opcional, `var_paride`. En el mismo sync la api descarta las obras cuyo
código contiene 6 o más dígitos seguidos (`sync.obras.digitos_seguidos_excluidos`
de `config.yaml`). Las reglas están en `docs/ARCHITECTURE.md#regla-var` y
`#regla-seis-digitos`.

### Quién puede entrar, y cómo se da acceso a alguien nuevo

El acceso lo decide la pertenencia al grupo de Entra
**`dedicacion-portal-users`**, con **asignación requerida** en la Enterprise
App: tener cuenta de Ruesma **no basta**, y quien no esté en el grupo no
obtiene token. Comprobado el 2026-08-20 (`appRoleAssignmentRequired = True`);
sin licencia Entra ID P1 esa restricción se ignoraría en silencio, así que no
se da por hecha: se verifica.

**La lista de miembros no se escribe aquí**, porque son datos personales y
cambian. Se consulta:

```powershell
az ad group member list --group 'dedicacion-portal-users' --query "[].userPrincipalName" -o tsv
```

**Dar acceso a alguien nuevo** (desde `infra/`, con `az login` hecho):

```powershell
.\setup_front_easyauth.ps1 -Miembros "persona@ruesma.es"
```

El script es idempotente y admite varios correos. Quien entra por primera vez
puede necesitar cerrar sesión y volver a abrirla para que el token recoja la
pertenencia nueva.

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
                                       └──▶ quién puede deshacer (F-027)
```

El `X-Usuario` que llegue **de fuera** se descarta: el proxy lo escribe él, no
lo reenvía. Si lo reenviara, cualquiera con sesión podría firmar la auditoría
con el nombre de otro.

**Desde F-027, `X-Usuario` no sirve solo para la auditoría: decide quién puede
deshacer.** Solo se deshace el último cambio pendiente de un trabajador en el
mes si lo hizo ese mismo usuario, comparado sin mayúsculas ni espacios en los
extremos; si es de otro, la api responde 409 con su nombre
([`docs/ARCHITECTURE.md#regla-deshacer`](ARCHITECTURE.md#regla-deshacer)).
Dos consecuencias:

- **Sin cabecera, todos son `local` y cuentan como el mismo usuario.** La api
  pone `local` cuando no llega `X-Usuario`, y el front sin Easy Auth manda
  su `DEFAULT_USER` (`local` en desarrollo, `desconocido` en Azure, §3).
  Todas las peticiones sin identidad comparten ese nombre: cualquiera de
  ellas puede deshacer lo de las demás.
- **Los eventos guardados como `local` no los podrá deshacer nadie que entre
  con Easy Auth**: su autor no coincide con ningún usuario real. Es lo
  correcto —no se sabe de quién son—, no una avería. Lo mismo vale para los
  guardados como `desconocido`.

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
| api → transfer (registro y, desde F-025, universo de postventa en el sync) | `TRANSFER_TIMEOUT_S` | **180 s** |
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
| Key Vault | `kv-dedicacion-dd7k2` |
| Logs | `log-dedicacion-dev` |
| Grupo de acceso | `dedicacion-portal-users` (asignación requerida: quien no esté, no entra) |
| FQDN del front (público) | `ca-dedicacion-front.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io` |
| FQDN de la api (interno) | `ca-dedicacion-api.internal.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io` |
| FQDN del transfer (interno) | `ca-dedicacion-transfer.internal.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io` |

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
| Vaciar `dedicacion` reiniciando las secuencias (`RESTART IDENTITY`) | Un `asignacion.id` nuevo reutiliza la `synckey` `porcentajes:{id}` de una línea ya escrita en Sigrid y el transfer la da por registrada sin escribirla. Por eso el vaciado de F-026 usa `CONTINUE IDENTITY` |
| Volver a mandar al transfer el `ide` de la ficha de empleado en vez de `recurso_ide` | El transfer lo ignora y omite la línea «sin recurso»: no se registra nada (F-026) |
| Parar el transfer, o que no responda a `POST /api/postventa/universo` | El sync de maestros (y su preview) falla entero con **502** nombrando el universo de postventa, sin persistir nada: no hay obras nuevas ni marcas al día hasta que vuelva (F-025, D3) |
| Cambiar `POSTVENTA_OBRA_COD` del transfer | Cambia qué obras se ofrecen como `Postv-` en el **siguiente** sync, no antes; hasta entonces el cuadrante enseña la foto vieja y el preflight manda (F-025) |
| Parar el transfer, o que no responda a `POST /api/var/universo` | El sync de maestros (y su preview) falla entero con **502** nombrando el universo VAR, sin persistir nada (F-039, como F-025 D3) |
| Publicar la api de F-039 antes que el transfer | La api nueva llama a `POST /api/var/universo`, que el transfer viejo no tiene: el sync queda en 502 hasta publicar el transfer. **Orden de despliegue: transfer → api → front** (F-039) |
| Cambiar `VAR_OBRA_COD` o `VAR_PARTIDA_DESDE` del transfer | Cambia qué entradas `VAR-NN` se ofrecen en el **siguiente** sync; las que salen quedan inactivas y sus líneas ya guardadas, no ofrecibles. El preflight manda: una línea en una partida que ya no está en el universo se omite con motivo (F-039) |
| Cambiar `sync.obras.digitos_seguidos_excluidos` de `config.yaml` | Cambia qué obras se ignoran por su código en el siguiente sync; con `0`, vuelven todas (F-039) |
| Cambiar en el transfer la elección del parte o la regla de la cuenta (`estado_parte.py`, `cuenta_analitica.py`) sin cambiarla en `partes` | Los dos servicios dejan de caer en el mismo parte o de poner la misma cuenta: dos complementarios en un mes, o un asiento analítico (`ANA`) con cuentas distintas para la misma persona. Las copias se vigilan con `tests/test_f037_copias_partes.py` (F-037) |

### Si tocan algo de otros

| Cambio ajeno | Qué nos rompe |
|---|---|
| Parámetros, autenticación o almacenamiento de `psql-albaranes-rs9k2` | Nos afecta igual que a los otros cuatro inquilinos. **Nosotros no los tocamos, y pedimos lo mismo** |
| Llenar el disco del servidor compartido | Pasa a solo-lectura y nos caemos con él (ya pasó el 2026-08-09) |
| Restaurar el servidor a un punto anterior | Arrastra **todas** las bases, la nuestra incluida |
| Rotar la function key de `sigrid-api` | Se caen la lectura de maestros **y** la escritura en el ERP. Hay que actualizar `SIGRID-API-FUNCTION-KEY` en el Key Vault y crear revisión nueva de api y transfer |
| Cambiar el contrato de `sigrid-api` (`/api/sql/read`, `/api/sql/write`) | Se cae todo: es nuestro único acceso a Sigrid |
| Bajar el `MAX_ALLOWED_ROWS` de `sigrid-api` por debajo de lo que ocupa el presupuesto de una obra | El transfer lee el presupuesto entero de la obra (`obrparpar`) para resolver la partida: esa obra deja de poder registrarse con «sigrid-api devolvio una respuesta truncada» (F-047). Hoy pedimos 200.000 (`SIGRID_MAX_ROWS`); la obra mayor (`BD`) tiene 26.812 partidas |
| Borrar o renombrar `acralbaranesdev` | No se puede publicar ni tirar ninguna imagen |
| Cambiar tablas o campos de Sigrid (`hmo`, `hmores`, `reshor`) | El mapeo del transfer deja de casar |
| Renumerar o dar de baja partidas de la obra de obras varias en Sigrid | Cambian las entradas `VAR-NN` del siguiente sync; las que desaparecen quedan inactivas y el preflight omite sus líneas con motivo. Una obra nueva con código de 6 o más dígitos seguidos no sale en el cuadrante (F-039) |
| Cambiar los estados del parte (`con.est`: 1 En registro, 3 Cerrado, 10 Imputado) o las cuentas analíticas (`caa`, `reshor.caaide`, `obrparpar.caaide`) | Con otro código de «En registro», el transfer da todos los partes por cerrados y crea complementarios; sin cuenta del centro, las líneas van con `caaide = 0` y no entran en el asiento analítico del parte (F-037) |
| Que `partes` cree un parte del mismo periodo a la vez que nosotros | El alta del transfer es condicional (código libre en la empresa y ningún parte En registro del periodo) y relee el periodo: usa el que haya. `partes` recogió la misma protección en su F-031 (`9ea7c59`) y su alta (`stmts_crear_parte`) es hoy idéntica a la nuestra (F-037, D17) |
| Cambiar en el transfer el alta del parte (`stmts_crear_parte`) | Deja de ser idéntica a la de `partes` (aviso de su F-031, 2026-10-06) y los dos servicios podrían crear partes distintos para el mismo periodo: avisar a `partes` en el mismo trabajo, igual que con `estado_parte.py` y `cuenta_analitica.py` |
| Que Administración contabilice un parte («Contabiliza parte…») | Pasa a Imputado: el transfer ya no escribe ni borra en él; lo nuevo va a un complementario y lo que choque con sus líneas se omite (`parte_cerrado`). Corregirlo es de Administración (F-037) |
| Cambiar `res` o `con` de Sigrid en lo que lee el sync de trabajadores (`res.cla`, `res.conide`, `res.cif`, `con.fecbaj`) | El sync parte de `res` (F-026): con `res.cla` cambiada entran o salen recursos del cuadrante; `res.conide` es lo único que une la ficha de empleado (solo da el DNI); `res.cif` es el documento del aviso de posible misma persona cuando no hay ficha; y `con.fecbaj` decide en qué meses está vigente cada trabajador |
| Cambiar `auxemp` de Sigrid (`numemp`, `res`, `fecbaj`, `desact`) | El sync de maestros falla entero (columnas obligatorias `numemp` y `nombre`) y el selector se queda con los nombres del último sync bueno |

**Petición abierta al proyecto `sigrid-api`:** hoy la api y el transfer
referencian **la misma** function key. Lo único que impide que la api escriba
en el ERP es que su código no tiene rutas de escritura, **no la credencial**.
Si `sigrid-api` admite claves distintas por consumidor, la api debería llevar
una que no pueda escribir.

---

## 8 · Modo pruebas: el transfer no escribe donde parece

> **ESTADO ACTUAL (2026-10-01): MODO REAL.** El humano ordenó salir del modo
> pruebas al republicar con F-022, F-023, F-024 y F-032: el transfer está con
> `OBRA_PRUEBAS_FORZAR=false` y **cada registro escribe en la obra real** de
> Sigrid. Quedan abiertos F-017 (Administración no ha validado la imputación
> a partidas) y F-011 (varios códigos M*); el recurso de cada línea lo manda
> la api desde F-026. Volver a pruebas es un comando:
> `az containerapp update -n ca-dedicacion-transfer -g rg-dedicacion-dev --set-env-vars OBRA_PRUEBAS_FORZAR=true`.
> Lo que sigue describe el modo pruebas, que es como **arranca** un alta nueva.

`dedicacion-transfer` se dio de alta con **`OBRA_PRUEBAS_FORZAR=true`**. Eso
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

**Una línea sin empresa no se registra.** El código de obra solo es único
dentro de su empresa, así que el transfer busca cada obra por código **y**
empresa, y la empresa llega en cada línea (la pone la api: es la **empresa
de las obras**, `EMPRESA_IMPUTACION`, sea cual sea la elegida en el
selector). Una línea que llegue sin ella sale **omitida con motivo**, no con
error; una petición que mezcle dos empresas se rechaza con **422**; y si la
obra es de otra empresa que sus líneas, todas se omiten. En modo pruebas,
una empresa sin obra de pruebas no escribe nada y el preflight enseña ese
error por obra. La regla completa: `docs/ARCHITECTURE.md#regla-empresa`.

**La línea lleva el recurso, no el empleado (F-026).** Contrato api →
transfer, por línea: `{registro_id, ano, mes, porcentaje (sobre 1),
recurso_ide, dni?, nombre?, categoria?, es_postventa, empresa, paride?}`.
`recurso_ide` es el `res.ide` del trabajador y el transfer lo usa tal cual:
ya no consulta `res.conide` ni elige el recurso. El antiguo identificador
de la ficha de empleado salió del contrato: si un cliente viejo lo manda, se
ignora y la línea sale omitida «sin recurso». La respuesta de la api a
`registro/preflight` y `registro/ejecutar` añade `no_vigentes`: los
`registro_id` de trabajadores no vigentes en el mes, que no se mandan ni se
trazan. La regla completa: `docs/ARCHITECTURE.md#regla-recurso`.

**Si la api arranca y dice que la base no existe**, es que falta ejecutar
`infra/crear_base_dedicacion.ps1`. El servicio ya no la crea solo, a
propósito, y el mensaje de error nombra la base que falta y el script que la
crea.
