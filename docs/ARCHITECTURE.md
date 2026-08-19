<!-- docs/ARCHITECTURE.md -->
# Arquitectura · dedicación (monorepo `porcentajes`)

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
>
> **Escrito el 2026-08-19 leyendo el código migrado al monorepo.** La
> sección «Semántica de dominio imprescindible» está PENDIENTE DE VALIDAR
> por el humano: sale del código y de los README, no de una conversación con
> Administración, y dos de sus puntos tienen contradicciones señaladas.

## Qué hace este proyecto

Registra el **porcentaje de dedicación mensual de cada trabajador a cada
obra** y lo lleva a los partes de trabajo de Sigrid. Sustituye a la hoja
`Plantilla_Dedicacion_Ruesma_vXX.xlsx` que Administración mantenía a mano.

Solo entra el personal que en Sigrid cobra **por mes** (código de hora `M*`
en su ficha `reshor`): jefes de obra, encargados, técnicos, administración.
El personal que va por horas se registra en el otro sistema, `partes`, con
sus partes diarios. Los dos escriben en las **mismas tablas** de Sigrid
(`hmo` / `hmores`), cada uno con su propio espacio de `synckey`.

Estado a 2026-08-19: **funciona en local, no hay nada desplegado en Azure**.

## Decisiones tomadas (2026-08-19)

- **El nombre de dominio es «dedicación».** Los tres servicios se llaman
  `dedicacion-api`, `dedicacion-front` y `dedicacion-transfer`, y la BBDD
  `dedicacion`. Lo que aún diga «porcentajes» dentro del código se alinea en
  su feature.
- **La carpeta del monorepo se queda como `porcentajes`.** Renombrarla no
  aporta nada y rompe rutas y sesiones abiertas. Que el contenedor se llame
  distinto que su contenido es deliberado, no un descuido.
- **La `synckey` se congela en `porcentajes:{asignacion_id}`.** Es un
  identificador funcional que viaja escrito en Sigrid: cambiarlo dejaría
  huérfano lo ya registrado y rompería la idempotencia. No se toca aunque el
  resto del proyecto se llame «dedicación».

## Capas y estructura

Monorepo de tres servicios independientes; cada uno arranca por su
`main.py`, con su `config/` (pydantic-settings sobre su propio `.env`) y su
`requirements.txt`. No hay `.env` ni dependencias en la raíz.

```
navegador
    │
    ▼
services/dedicacion-front   (8080)  SPA Jinja2 + JS vanilla
    │  proxy /api/*  (+ cabecera X-Usuario desde Easy Auth)
    ▼
services/dedicacion-api     (8090)  FastAPI + PostgreSQL `dedicacion`
    │                                  │
    │  HTTP preflight / ejecutar       └──▶ sigrid-api  (LECTURA de maestros)
    ▼
services/dedicacion-transfer (8006) ──────▶ sigrid-api  (ESCRITURA, base `ruesma`)
                                                └──▶ Sigrid (SQL Server on-prem)
```

### `dedicacion-api` — el dueño del dato

Hexagonal estricto:

- `domain/` — entidades (`models.py`), la regla del 100 % (`estados.py`:
  `SIN_CARGA` / `OK` / `FALTA` / `EXCESO`), errores tipados y puertos
  (`ports.py`: `UnitOfWork`, `SigridGateway`).
- `application/` — casos de uso (`use_cases.py`), sincronización de maestros
  (`sync_pipeline.py`, `filtros_maestros.py`) y orquestación del registro
  (`registro_sigrid.py`, que agrupa por obra y llama al transfer).
- `infrastructure/` — `db/` (SQLAlchemy 2, `orm_models.py` como única verdad
  del esquema + `esquema.py`, que deriva de él el DDL del arranque, +
  repositorios),
  `sigrid/` (cliente de `sigrid-api`), `excel/` (export compatible con la
  plantilla), `transfer/` (cliente HTTP del transfer).
- `interface_adapters/api/` — FastAPI: `routes.py`, `schemas.py`, `deps.py`
  (contenedor de dependencias), `app.py`.

Endpoints bajo `/api/v1`: `health`, `sync` y `sync/preview`, CRUD de
`periodos` (crear/cerrar/reabrir/copiar-anterior), `cuadrante`, sustitución
atómica de asignaciones por trabajador, `deshacer`, `export.xlsx` y
`registro/preflight` + `registro/ejecutar`.

Tablas de PostgreSQL: `trabajador`, `obra` (copias sincronizadas de Sigrid,
PK = el `ide` de Sigrid), `periodo` (año+mes único, `ABIERTO`/`CERRADO`),
`asignacion` (periodo × trabajador × obra × `es_postventa`, `porcentaje` en
0-100) y `evento` (auditoría con `snapshot_antes` / `snapshot_despues` en
JSONB, que es lo que permite deshacer multinivel).

### `dedicacion-front` — captura, nada más

FastAPI que sirve `templates/index.html` y hace de proxy hacia la API,
traduciendo `X-MS-CLIENT-PRINCIPAL-NAME` (Easy Auth) a `X-Usuario`. Toda la
interacción vive en `static/js/app.js`: lista de trabajadores, editor con
autocompletado de obra, autoguardado con debounce, atajos de teclado y chips
de filtro por estado. **No decide nada de negocio.**

### `dedicacion-transfer` — la única pluma

Réplica del patrón validado en `partes-transfer`. Contrato de dos fases:

- `POST /api/registro/preflight` — pasos 1-8: resolver destinos, resolver el
  recurso de cada empleado, cargar sus tipos de hora, aplicar las reglas,
  localizar el parte del mes, comprobar idempotencia y detectar conflictos.
  No escribe nada.
- `POST /api/registro/ejecutar` — pasos 9-10: crear los partes que falten
  (`con` + `hmo`, releyendo el `ide`) y borrar las pisadas confirmadas +
  insertar las líneas nuevas, por lotes.

`application/services/reglas_porcentajes.py` concentra las reglas P1-P5;
`application/pipelines/registro_pipeline.py` las orquesta;
`infrastructure/sigrid/sigrid_write_client.py` es lo único que habla con
`sigrid-api` en modo escritura.

## Semántica de dominio imprescindible

> PENDIENTE DE VALIDACIÓN POR EL HUMANO. Los puntos marcados ⚠ tienen
> versiones contradictorias en el propio repositorio.

1. **Solo recursos mensuales (P1).** Se registra únicamente el recurso que
   tenga un código de hora `M*` (`MENC`, `MCAP`, `MJEFO`…) en `reshor`. Es
   el mismo filtro que aplica la sincronización de empleados de la API, y
   por eso lo que se captura y lo que se registra coinciden. Un recurso sin
   `M*` se omite con motivo; no es un error.
2. **La línea va al último día del mes (P2).** El parte de Sigrid es por
   obra y mes natural; la fecha (`fec`) de la línea es siempre el último día
   de ese mes, no el día en que se trabajó ni el de captura.
3. **El porcentaje viaja sobre 1 (P3).** En PostgreSQL se guarda 0-100
   (`asignacion.porcentaje`, `Numeric(6,2)`); al transfer se manda **dividido
   entre 100** (40 % → `0.4`). En Sigrid, `can` = ese valor sobre 1, `pre` =
   importe mensual del recurso en `reshor`, `tot = can × pre`. Confundir las
   dos escalas escribe importes 100 veces mayores o menores.
4. **El total de un trabajador debe ser 100 %.** `FALTA` (<100), `EXCESO`
   (>100) y `SIN_CARGA` (sin líneas) son estados visibles, no bloqueos: se
   puede guardar un cuadrante incompleto. La comparación usa una épsilon de
   0,005 para no pelearse con los decimales.
5. **Postventa es una obra, no una marca (P5).** Una asignación con
   `es_postventa` no se escribe en su obra: se escribe en la obra de
   postventa (`POSTVENTA_OBRA_COD`, hoy `POSTV2`) imputando a la partida que
   corresponde a la **obra original** (`0707` → partida `0707 · …`). Sin
   casado, la línea se omite con motivo. Por eso la clave única de
   `asignacion` incluye `es_postventa`: un trabajador puede tener la misma
   obra dos veces, una normal y otra de postventa. ⚠ El README del transfer
   dice obra `POSTV2` y habla de *partida*; el docstring de
   `reglas_porcentajes.py` dice `postventa-2` y habla de *capítulo*. Manda
   el `.env` (`POSTV2`), pero conviene confirmarlo contra Sigrid.
6. **Conflicto e idempotencia.** `synckey = "porcentajes:{asignacion_id}"`
   (no se cruza con los partes diarios, que usan otro prefijo): reejecutar no
   duplica. Si el recurso ya tiene una línea `M*` en ese parte —**aunque sea
   en otro día**— es conflicto y hay que confirmar el pisado, que sustituye
   la línea y de paso corrige la fecha. ⚠ El README dice que en obra normal
   choca aunque la partida sea distinta; el docstring de P4 exige «la misma
   partida». Hay que fijar cuál es la regla buena antes de escribir en
   producción.
7. **Modo pruebas por defecto.** `OBRA_PRUEBAS_FORZAR=true` desvía TODA
   escritura a la obra `0404` con la marca `PRUEBA-PORC` en `tex`. El
   capítulo de postventa se sigue resolviendo contra la obra de postventa
   real, para que la prueba valide el casado.
8. **`ide` reservado a mano.** Las líneas se insertan con `MAX(ide)+1` bajo
   `UPDLOCK, HOLDLOCK`: el transfer va a **una sola instancia**. Dos procesos
   escribiendo a la vez se pisan los `ide`.
9. **Trampas de Sigrid heredadas de partes.** Lotes de 15 sentencias como
   máximo; solo base `ruesma`; `tex` es TEXT, hay que comparar con
   `CAST(tex AS NVARCHAR(200)) = ?`; el parte se localiza por `cod` **y**
   `tip`; tras crear la cabecera hay que releer su `ide` antes de insertar
   líneas.

## Acceso a datos y sistemas externos

| Sistema | Quién | Modo | Notas |
|---|---|---|---|
| `sigrid-api` (Function App) | api | **solo lectura** (`POST /api/sql/read`) | maestros de empleados y obras; consultas parametrizadas en `config/config.yaml` |
| `sigrid-api` | transfer | **escritura** | único punto de escritura del sistema; base `ruesma` siempre (`ruesma_rep` es réplica de solo lectura) |
| PostgreSQL `dedicacion` | api | lectura y escritura | hoy `localhost`; el servidor de destino al desplegar está sin decidir |
| `dedicacion-transfer` | api | HTTP interno | `TRANSFER_BASE_URL`, timeout 180 s |

Reglas duras:

- Nadie más que el transfer escribe en Sigrid. La API no tiene credencial de
  escritura y no debe tenerla.
- **Topes de `sigrid-api`** (valores efectivos de la instancia `dev`
  comprobados el 2026-08-18, en `azure-apps/sigrid_api.md` §4.1): el tope de
  filas por petición es **500.000** (el 1.000 de la tabla de defectos es el
  del código, no el de la instancia), y `max_rows` por defecto es **200** si
  el cliente no lo pide. `SIGRID_MAX_ROWS=5000` está holgadamente dentro.
  Lo que manda de verdad es el **corte del balanceador a los 230 s**: una
  respuesta grande se lo come antes de llegar al tope de filas, así que
  paginar (`OFFSET / FETCH` con `ORDER BY ide`) sigue siendo obligatorio para
  cualquier extracción seria, y el campo `truncated` de la respuesta **no se
  ignora nunca**: significa respuesta incompleta, sin error. El cliente de la API ya lo
  trata así: si `truncated` viene a `true`, lanza `SigridError` en vez de
  seguir con datos a medias. No pagina —hoy no le hace falta con `max_rows`
  a 5.000 y unos 156 empleados—, así que si el volumen crece, lo que hay que
  añadir es paginación, no subir el tope.
- Documentación del sistema origen: `azure-apps/sigrid_api.md` (la pasarela)
  y `azure-apps/sigrid_tablas.md` (diccionario de tablas). No se duplican
  aquí, se enlazan.
- Los tests unitarios no tocan ni Sigrid ni PostgreSQL
  (`services/dedicacion-transfer/tests/test_pipeline_offline.py` es el
  ejemplo a seguir).

## Infra y despliegue

**No hay nada desplegado ni carpeta `infra/`.** Los tres servicios se
ejecutan en local: transfer (8006) → api (8090) → front (8080), en ese orden.
`dedicacion-api` y `dedicacion-front` traen `Dockerfile`; el transfer no.

Cuando toque desplegar, el patrón de referencia es el monorepo `partes`
(`infra/` con scripts PowerShell 5.1, `az acr build` sobre `acralbaranesdev`,
Container Apps, secretos en Key Vault por `keyvaultref` con identidad
gestionada) y las reglas del entorno: imágenes con tag fechado
`rYYYYMMDD-HHmm` sin reescribir, secretos como secrets del recurso, `.env`
nunca viaja en la imagen, tags obligatorios de Azure Policy. Ese trabajo es
una feature, con su documento en `azure-apps/` cuando exista despliegue.
