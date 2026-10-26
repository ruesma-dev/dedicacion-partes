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
> El **2026-10-09**, transfer y front con F-049 (`dedicacion-transfer:r20261009-1045` y `dedicacion-front:r20261009-1046`; el preflight publica
> `partidas_obra` aunque todas las líneas lleven partida manual; sin cambios de contrato).
> El **2026-10-14**, los tres con F-050 (`dedicacion-transfer:r20261014-1740`, `dedicacion-api:r20261014-1743` y `dedicacion-front:r20261014-1746`, en el orden
> transfer → api → front; `POST /api/partidas/propuesta` del transfer, `GET …/partidas` y `PUT …/partida` de la api,
> `obra_ide` en el preflight y las columnas `partida_*` de `asignacion`, que la api añade al arrancar).
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
| `sigrid-api` (`func-sigridapi-dev-huyke`) | todo el ecosistema | **Lectura** de maestros desde la api (empleados, obras y, desde F-032, el catálogo de empresas `auxemp`); **escritura** de líneas de parte desde el transfer, siempre contra la base `ruesma`. Desde F-037 el transfer lee además los partes del periodo con su estado (`hmo` + `con.est`), las cuentas analíticas del centro de la obra (`caa` + `con`), la cuenta de la plantilla del recurso (`reshor.caaide`) y la de la partida (`obrparpar.caaide`); un `truncated` es error y no se escribe nada. Desde F-051 el transfer **edita en su sitio** (`UPDATE` con guarda) líneas `M*` del parte —las al 0 % que copia Administración y las pisadas confirmadas, también de otros sistemas, sin cambiar su `synckey`— y **no borra ninguna**. Desde F-030 la api lee en cada sync el catálogo de incidencias (`auxhor`, códigos `CI*`), y el transfer **escribe** por cada incidencia un par de líneas `CI*`/`CIZ` con `can = 0` y `synckey` `porcentajes:inc:{id}:ini|fin`, tras **una** lectura de las líneas `CI*` del mes de esos recursos en cualquier parte (`hmores` + `auxhor` + `hmo` + `con`) para no duplicar; si la incidencia ya registrada cambia de días, **edita la `fec`** de su par (`UPDATE` con guarda, anexo R30). Desde F-062 las incidencias son **rachas** como las de Administración: esa lectura es **una** por petición o lote **en ventana** (de 12 meses antes, `INCIDENCIAS_MESES_ATRAS`, al mes siguiente, en cualquier parte y también por `ide` de las trazas), el transfer continúa la racha de quien sea, **mueve la `fec`** de `CIZ` ajenos (de Administración o de `partes`, con su `can` y sin cambiar su `synckey`) y la devuelve a su día si deja de continuarla, escribe un `CIZ` en el parte del inicio (también ajeno) y cierra el último día del mes anterior las rachas que quedaron abiertas, en un parte de ese mes; nunca borra. Desde F-044 la api lee en cada sync los recursos no persona con el campo extendido «Recurso Asociado» (`sync.vinculados` de `config.yaml`, el código del campo como parámetro), y el transfer lee **una** vez por obra las cuentas de las partidas del presupuesto (`obrparpar` + `con`) si algún vinculado necesita la CI de su tipo y **escribe o edita**, en el parte de su trabajador, una línea por recurso vinculado con **su** hora y `synckey` `porcentajes:vin:{registro_id}:{recurso_ide}`; nunca borra | F-001, F-002, F-037, F-051, F-030, F-062, F-044 |
| `acralbaranesdev` | `albaranes`, `partes` | Publicar y tirar las tres imágenes, por identidad gestionada | **F-008** |
| Entra ID | todo el ecosistema | Autenticación del front (Easy Auth) y grupo de acceso | **F-008** |

**El parte de Sigrid se comparte con `partes`** (F-037): los dos servicios
escriben líneas en el **mismo** parte de obra y mes, y eligen igual en cuál
(el En registro de mayor `ide`; si todos están cerrados, un complementario
`Parte <obra>` que cualquiera de los dos reutiliza). Las reglas son copia
literal de las de `partes` (`estado_parte.py`, `cuenta_analitica.py`). El
asiento analítico (`ANA`) **no** lo escribe el transfer: lo genera Sigrid
cuando Administración pulsa «Contabiliza parte…», que deja el parte en
Imputado; desde entonces el transfer no escribe en él. Desde F-051 el
transfer **edita** líneas `M*` de ese parte compartido en vez de borrarlas
e insertar: las al 0 % del recurso sin confirmar y las de un pisado
confirmado, conservando su `ide` y, si es de otro sistema (`partes:…`), su
`synckey`; las localiza después por `hmores.ide`
(`docs/ARCHITECTURE.md#regla-cero`). `partes` nunca ha escrito líneas `M*`.
Desde F-030 este proyecto escribe además en ese parte compartido líneas de
**incidencia** (`CI*`/`CIZ`, `can = 0`), las mismas que escribe `partes`:
antes de escribir mira las de ese recurso, código y día en todos los partes
del mes, y lo que ya está (de `partes` o de Administración) no se duplica
(`docs/ARCHITECTURE.md#regla-incidencia`). Desde F-062, además, **mueve la
`fec`** de `CIZ` que no son suyos (también con `synckey` `partes:…`) para
continuar una racha, **añade** `CIZ` en partes de otros (el del inicio de la
racha, y en el mes anterior para cerrarla) y deja rachas **abiertas** a fin
de mes; nunca borra. Desde F-044 escribe además en ese parte compartido
líneas de **recursos no persona** vinculados a sus trabajadores (teléfono,
gasoil, vehículo…), con su hora (no `M*`, salvo `MESVE`) y `synckey`
`porcentajes:vin:…`, y edita las de esos recursos al 0 % o pisadas
confirmadas con la guarda de su hora; nunca borra
(`docs/ARCHITECTURE.md#regla-vinculado`). `azure-apps/partes.md` debería
decirlo en su «qué se rompe»; es de `partes`.

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
| `SIGRID_LECTURAS_PARALELAS` | Lecturas a la vez contra `sigrid-api` en un lote (F-055): **4 por defecto en el código**, de 1 a 8 (fuera de ese rango el transfer no arranca); 1 = en serie, como antes de F-055. El límite es **por lote** (por llamada a `…/preflight-lote` o `…/propuesta-lote`), **no por proceso**: dos lotes a la vez —p. ej. un preflight y las propuestas del mes en segundo plano— suman sus lecturas contra `sigrid-api` |
| `PROPUESTA_MESES_ATRAS` | Meses hacia atrás, desde el del cuadrante incluido, en los que se busca la partida propuesta (F-050, `docs/ARCHITECTURE.md#regla-partida`). Con defecto en el código (`24`): no hace falta declararla al desplegar |
| `INCIDENCIAS_MESES_ATRAS` | Meses hacia atrás de la lectura en ventana de las rachas de incidencia (F-062, `docs/ARCHITECTURE.md#regla-incidencia`): del día 1 de esos meses antes al último del mes siguiente. Con defecto en el código (`12`, mínimo 1): no hace falta declararla al desplegar |
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

Desde F-050 el transfer expone además, **solo para la api**, `POST
/api/partidas/propuesta` (`{empresa, obra: {ide, codigo, nombre}, ano, mes,
lineas: [{clave, recurso_ide, nombre, categoria, es_postventa}]}` → el
catálogo de la obra, y el de postventa si hay líneas de postventa, cada
partida con su `mayor` (CD, CI, CP u OTRO) y en orden natural, y por `clave`
la partida propuesta `{paride, cod, res, metodo, origen}` o nula y el
`mayor_inicial`; 422 sin empresa válida o con la obra en otra empresa, 502
si falla una lectura; nunca escribe). Lee el presupuesto de la obra y, si
hay líneas de obra normal, el historial de partidas de sus recursos en
**una** lectura (más el de postventa si hace falta). La api sirve a su vez,
**solo para el front**, `GET /api/v1/periodos/{anio}/{mes}/trabajadores/
{ide}/partidas?obra_ide=&es_postventa=` (catálogos, propuesta, elegida,
`ambito` = botón preelegido y `fija` para una entrada VAR, que no llama al
transfer; **502** con motivo si el transfer no responde, y el cuadrante
sigue funcionando) y `PUT /api/v1/periodos/{anio}/{mes}/trabajadores/{ide}/
partida` (`{obra_ide, es_postventa, partida: {ide, cod, res} | null}` →
cambia solo la partida elegida de esa línea, con evento `PARTIDA`
deshacible; 404 / 409 / 422). Cada línea del cuadrante publica
`partida_ide`, `partida_cod`, `partida_res` y `partida_fija`, y al registrar
la elegida viaja como `paride`. El preflight ya no recibe `overrides` del
front y admite `obra_ide` en el cuerpo (entero; 422 si no lo es): analiza solo la petición de esa
obra (la del grupo; en las entradas VAR, la de registro). Es lo que repite
el modal al cambiar una partida, en vez del mes entero (F-050 T15c);
`ejecutar` no se acota. La regla está en `docs/ARCHITECTURE.md#regla-partida`.
Desde F-056, `trabajador_ide` en el cuerpo de `registro/preflight` y
`registro/ejecutar` se valida igual: entero (también `"11"` o `11.0`) o
`null`/ausente (el mes entero); cualquier otro valor (`""`, `false`, texto,
decimal) es **422** sin analizar ni escribir. Un `0` o un negativo son
enteros: filtran y no casan con nadie, nunca registran el mes entero.

Desde F-055 (registro sin búsquedas de partidas; orden de la propuesta
parte anterior → casamiento → último parte):

- El transfer expone, **solo para la api**, `POST
  /api/registro/preflight-lote` (`{peticiones: [la petición de
  /api/registro/preflight]}` → `{ok, obras}`: por petición y en su orden,
  la respuesta del preflight de hoy o `{ok: false, error}`; 502 si falla una
  lectura agrupada) y `POST /api/partidas/propuesta-lote` (`{peticiones:
  [la de /api/partidas/propuesta]}`, todas del mismo `ano` y `mes` o 422 →
  `{ok, obras}`: por petición `{ok: true, propuestas}` o `{ok: false,
  error}`; 502 si falla una lectura compartida). Los dos solo leen, son
  síncronos y leen agrupado y en paralelo (`SIGRID_LECTURAS_PARALELAS`).
- Las líneas del registro ganan cinco campos opcionales, `propuesta_paride`,
  `propuesta_cod`, `propuesta_res`, `propuesta_metodo` y
  `propuesta_origen` (la propuesta guardada de una línea sin elegida), y
  cada acción del preflight publica `partida_res`.
- La api pide el preflight del periodo en **una** llamada al lote y guarda
  en `asignacion.propuesta_*` (cinco columnas nulables nuevas, que pone al
  día al arrancar) las propuestas que vuelven; el selector también la
  guarda. Calcula las del mes en **segundo plano** (un hilo) con el lote de
  propuestas, por trozos de 10 obras.
- La api sirve **al front** `GET /api/v1/periodos/{anio}/{mes}/propuestas`
  (`{en_curso, lineas: [{trabajador_ide, obra_ide, es_postventa,
  propuesta_cod, propuesta_res, propuesta_metodo}]}`, solo lee). El
  cuadrante y las seis escrituras (`PUT …/asignaciones`, `PUT …/partida`,
  `POST …/deshacer`, `POST …/trabajadores/{ide}/copiar-anterior`, `POST
  …/completar` y `POST …/copiar-anterior`) ganan `propuestas_en_curso`
  (`bool`); cada línea del cuadrante, `propuesta_cod`, `propuesta_res` y
  `propuesta_metodo`. El front consulta `…/propuestas` cada 5 s mientras
  `propuestas_en_curso`.
- Desde F-057, cada línea del cuadrante y de las escrituras que devuelven
  la fila (`PUT …/asignaciones`, `PUT …/partida`, `POST …/deshacer` y `POST
  …/trabajadores/{ide}/copiar-anterior`) lleva `propuesta_pendiente`
  (`bool`): la línea está en la cola de las propuestas del mes (en cola o
  calculándose), leída **después** de encolar. `GET …/propuestas` añade
  `pendientes: [{trabajador_ide, obra_ide, es_postventa}]` (las de todo el
  periodo que siguen en la cola, de la misma foto que `en_curso`). La regla
  es la de encolar (`application/propuestas_mes.py`): una línea de
  postventa, con partida fija o elegida, con propuesta guardada o en la
  memoria «sin propuesta» nunca está pendiente. El front dice «buscando
  partida…» solo en las marcadas y, en cada consulta, reemplaza las marcas
  con `pendientes`; `propuestas_en_curso` / `en_curso` siguen gobernando
  solo la consulta.

Desde F-051 (editar, nunca borrar; `docs/ARCHITECTURE.md#regla-cero`):

- Las líneas de `registro/preflight` y `registro/ejecutar` ganan
  `hmores_ide` (opcional): la api manda el `asignacion.sigrid_hmores_ide`
  que tenga la asignación, y el transfer da la línea por ya registrada si
  esa fila sigue siendo suya (su recurso, código de hora `M*` y sin
  `synckey` nuestra de otra asignación).
- Cada acción del preflight publica `linea_cero` (la línea al 0 % que se
  editaría, o nulo) y cada conflicto, `edita_ide` y `a_cero_ides`.
- La respuesta de `registro/ejecutar` gana `editadas` y `a_cero` (cada
  línea tocada con su `antes` y su `despues`), `ya_registradas_ide`
  (`{registro_id: hmores.ide}`) y `escritas[].editada`; `borradas` sigue y
  vale siempre 0. La api guarda en `sigrid_hmores_ide` el `ide` de cada
  escrita y de cada ya registrada (columna existente, sin DDL).

Desde F-030 (incidencias en el cuadrante;
`docs/ARCHITECTURE.md#regla-incidencia`):

- La api sirve **al front** `GET /api/v1/incidencias` (`{incidencias:
  [{codigo, letra, nombre}]}`, el catálogo activo por letra, solo lee) y
  `PUT /api/v1/periodos/{anio}/{mes}/trabajadores/{ide}/incidencias`
  (`{incidencias: [{id, obra_ide, codigo, dia_desde, dia_hasta}]}`, días
  vacíos = mes entero; `id` opcional: con él se conserva la incidencia
  guardada, sin él es nueva; sustituye las del trabajador con evento
  deshacible y responde como el `PUT …/asignaciones`). Cada fila del
  cuadrante gana `incidencias` (`id`, obra, código, letra, nombre, días,
  `quitada` y la traza del registro). Dos tablas nuevas, `tipo_incidencia`
  e `incidencia`, que la api crea al arrancar (y completa con
  `alters_faltantes`: `quitada`, `sigrid_dia_ini`, `sigrid_dia_fin`);
  `asignacion` no cambia.
- `registro/preflight`, `registro/preflight-lote` y `registro/ejecutar` del
  transfer aceptan en cada petición una lista opcional `incidencias`
  (`{id, recurso_ide, empresa, codigo, ano, mes, desde, hasta, paride}`,
  y la traza de una registrada: `hmores_ide_ini`, `hmores_ide_fin`,
  `dia_ini`, `dia_fin`, que solo viajan si hay alguna) y, solo si la trae,
  responden `incidencias` (por línea: `id`, `rol` `ini`/`fin`, `accion`,
  `fecha_int`, `hora_codigo`, `paride`, `parte_cod`, `hmores_ide` y
  `motivo`; con `accion` `editar`, también `fec_antes`). Sin ella, petición
  y respuesta son las de antes. La api la manda por obra y guarda la traza
  en `incidencia`; las quitadas no viajan y su `POST …/preflight` las
  devuelve en `incidencias_quitadas` (trabajador, obra, letra, días, parte
  e `ide`s) para retirarlas a mano.
- Cambiar los días de una registrada (anexo R30) es, en Sigrid, un
  `UPDATE` de **solo** la `fec` de cada línea del par, con la guarda de
  F-051, su código (`a.cod = ?`) y la `fec` leída (`fec = ?`, D16): ni
  `INSERT`, ni `DELETE`, ni parte
  nuevo. La lectura de las líneas `CI*` del mes trae además `h.can`,
  `h.hmoide` y `con.est`, y busca también por `h.ide` las de la traza.

Desde F-062 (rachas de incidencia como Administración;
`docs/ARCHITECTURE.md#regla-incidencia`):

- Cada petición de `registro/preflight`, `registro/preflight-lote` y
  `registro/ejecutar` puede llevar además, si no están vacías,
  `incidencias_mes` (las del mes de sus recursos en cualquier obra:
  `{id, obra_ide, recurso_ide, empresa, codigo, ano, mes, desde, hasta,
  paride}` y la traza, con `dia_fin_antes`, el día original del `CIZ` ajeno
  que movió), `quitadas` (las quitadas de la obra con algún `ide` en su
  traza, mismo elemento) y `cierres_recursos` (los recursos cuya primera
  petición es esa: se les cierran las rachas del mes anterior). La api crea
  la petición de una obra que solo tiene quitadas. Con alguna de las tres,
  la respuesta gana `rachas` (por incidencia: `papel` `abre`|`continua`,
  inicio, `cierre` `cierra`|`abierta`|`cubierta`|`cadena` con día y parte,
  dueña y avisos), `cierres_racha` (recurso, código, inicio, `accion`
  `escribir`|`ya_registrado`|`aviso`|`pendiente`, `fecha_int`, parte,
  `incidencia_id`, `hmores_ide`, `requiere_confirmar` y `clave`: la racha
  con inicio anterior a M−1 solo se cierra con `cierre:{ide del inicio}` en
  `pisar_claves`; sin ella, `ejecutar` la devuelve `pendiente`, sin
  escribir y fuera de `pendientes_confirmacion`) y `no_coincide` (`tipo`
  `quitada`|`solo_sigrid`, recurso,
  incidencia, líneas con `ide`, código, día y parte, motivo y `en_sigrid`);
  las de `incidencias` ganan el rol `devolver`, las acciones `continua` y
  `abierta` y `ajena`. Sin ninguna, petición y respuesta son las de F-030.
- La api guarda `sigrid_dia_fin_antes` en `incidencia` (columna nueva, por
  `alters_faltantes`), traza la que solo continúa o queda abierta como
  registrada sin `ide`, anula la del `fin` al devolver el `CIZ` y borra la
  quitada que ya no tiene líneas en Sigrid. `incidencias_quitadas` sigue en
  la respuesta del preflight, pero el modal pinta «No coincide con Sigrid».
- En Sigrid: la lectura es en ventana (arriba, §1) y mover un `CIZ` ajeno es
  el mismo `UPDATE` de solo la `fec`, con su `can` leído en la guarda.

Desde F-044 (recursos vinculados; `docs/ARCHITECTURE.md#regla-vinculado`):

- Cada línea de `registro/preflight`, `registro/preflight-lote` y
  `registro/ejecutar` de un periodo ≥ `sync.vinculados.desde` puede llevar
  `vinculados`: `[{recurso_ide, tipo, tipo_res, cod, paride?, partida_cod?,
  propuesta_*?, hmores_ide?}]` (la elegida de la subfila o su propuesta
  guardada y la línea del último registro). Con alguno, la respuesta gana
  `vinculados` (por vinculado de cada línea: `registro_id`, recurso, tipo,
  código, acción, hora, `can`, `pre`, `tot`, partida y método, parte,
  `linea_cero`, `hmores_ide`, aviso y motivo) y sus avisos van en
  `conflictos` con `vinculado: {tipo, cod}` y su propia clave; en
  `ejecutar`, la entrada de `omitidas` de un vinculado lleva
  `vinculado_ide`. Sin vinculados, petición y respuesta son las de antes
  (ni `vinculados` ni `vinculado`).
- `partidas/propuesta(-lote)` admite los mismos `vinculados` por línea y
  devuelve la propuesta de cada subfila (`vinculados: {clave: {recurso:
  {paride, cod, res, metodo, origen}}}`).
- La api sirve al front las subfilas en el cuadrante (`lineas[].vinculados`)
  y `GET …/partidas` y `PUT …/partida` con `vinculado_ide`; guarda la
  elegida, la propuesta y la traza de cada subfila en
  `asignacion_vinculado` y el vínculo en `recurso_vinculado` (tablas
  nuevas, por `create_all`). El preview del sync cuenta los vinculados sin
  campo o hacia quien no es trabajador.

Desde F-061 (búsqueda predictiva en el desplegable de incidencias), cada
incidencia de `GET /api/v1/incidencias` trae dos campos más, compatibles
hacia atrás: `{codigo, letra, nombre, palabras, orden_busqueda}`.
`palabras` son las palabras extra del buscador (lista, vacía si no tiene) y
`orden_busqueda` la posición de su entrada en `config.yaml`
(`sync.incidencias.palabras_extra`; 0 = la primera, `null` sin entrada),
con la que el front desempata el desplegable. La lista sigue por letra. Es
dato de la api, no de Sigrid: no cambia ninguna lectura ni escritura. El
front vuelve a pedir el catálogo tras cada `POST /sync` con éxito.

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
| api → transfer (registro —desde F-055 el preflight en una llamada al lote—, universo de postventa en el sync y, desde F-055, las propuestas del mes por trozos de 10 obras, en segundo plano) | `TRANSFER_TIMEOUT_S` | **180 s** |
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
| Parar el transfer, o que no responda a `POST /api/partidas/propuesta` | El selector de partida no se abre (502 con el motivo); el cuadrante, guardar y registrar siguen funcionando (F-050) |
| Publicar la api de F-050 antes que el transfer | El selector de partida da 502 hasta publicar el transfer: el transfer viejo no tiene `POST /api/partidas/propuesta`. **Orden de despliegue: transfer → api → front** (F-050); la api pone al día la tabla `asignacion` al arrancar (`partida_*`, nulables) |
| Publicar la api de F-055 antes que el transfer | El preflight del registro y las propuestas en segundo plano fallan (404 en `POST /api/registro/preflight-lote` y `/api/partidas/propuesta-lote`): el modal enseña el error en cada obra y las celdas Partida siguen en «automática». **Orden de despliegue: transfer → api → front** (F-055); la api pone al día la tabla `asignacion` al arrancar (`propuesta_*`, nulables) |
| Subir `SIGRID_LECTURAS_PARALELAS` del transfer | Más lecturas a la vez contra `sigrid-api` (tope 8 **por lote**, no por proceso; dos lotes simultáneos suman las suyas); `sigrid-api` no documenta un tope de concurrencia (`azure-apps/sigrid_api.md` §3.4). 1 vuelve al serie de antes de F-055 |
| Cambiar `PROPUESTA_MESES_ATRAS` del transfer | Cambia hasta dónde se mira atrás para proponer la partida del parte anterior y del último parte; cuantos más meses, más filas lee el historial (F-050) |
| Publicar la api o el front de F-051 antes que el transfer | El transfer viejo ignora `hmores_ide` y sigue **borrando** al pisar mientras el front nuevo dice «se edita»: **orden de despliegue transfer → api → front** (F-051) |
| Publicar la api o el front de F-044 antes que el transfer | El transfer viejo ignora `vinculados`: el registro sigue como antes pero **no escribe ningún vinculado**, y el modal no los enseña. **Orden de despliegue: transfer → api → front** (F-044) |
| Cambiar `sync.vinculados` de `config.yaml` (`campo`, `desde`, `tipos_excluidos`, `sql`) | Mal escrito, la api no arranca. `desde` decide desde qué periodo viajan los vinculados; un tipo que sale de `tipos_excluidos` se vincula en el siguiente sync (F-044) |
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
| Que Administración contabilice un parte («Contabiliza parte…») | Pasa a Imputado: el transfer ya no escribe ni edita en él; lo nuevo va a un complementario y lo que choque con sus líneas se omite (`parte_cerrado`). Corregirlo es de Administración (F-037) |
| Que Administración o `partes` cambie una línea entre el preflight y el registro | El transfer relee lo que va a editar justo antes de escribir y cada `UPDATE` lleva guarda (`can` y `synckey` leídos, recurso, `M*`, sin enlaces, parte En registro): esa línea no se toca y su asignación sale omitida pidiendo volver a registrar (F-051) |
| Cambiar `res` o `con` de Sigrid en lo que lee el sync de trabajadores (`res.cla`, `res.conide`, `res.cif`, `con.fecbaj`) | El sync parte de `res` (F-026): con `res.cla` cambiada entran o salen recursos del cuadrante; `res.conide` es lo único que une la ficha de empleado (solo da el DNI); `res.cif` es el documento del aviso de posible misma persona cuando no hay ficha; y `con.fecbaj` decide en qué meses está vigente cada trabajador |
| Cambiar o vaciar en Sigrid el campo extendido «Recurso Asociado» de un recurso no persona, o su `reshor` | Sin campo (o hacia quien no es trabajador de dedicación) deja de vincularse en el siguiente sync y su línea no se escribe; sin su hora en `reshor` o con `pre` 0, se omite «sin importe mensual». Renombrar la cuenta de la partida CI de su tipo (`obrparpar.caaide`) le quita la propuesta: «sin partida» a confirmar (F-044) |
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
