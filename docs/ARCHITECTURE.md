<!-- docs/ARCHITECTURE.md -->
# Arquitectura · dedicación (monorepo `porcentajes`)

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
>
> **Escrito el 2026-08-19 leyendo el código migrado al monorepo y validado
> ese mismo día.** Los dos puntos que quedaban en el aire —el 5 (postventa)
> y el 6 (conflicto)— se cerraron con las decisiones D1 y D2 de F-002, y de
> la segunda salió una regla que el repositorio no tenía: la 7 (capacidad).
> Cada uno lleva su línea de procedencia.

## Qué hace este proyecto

Registra el **porcentaje de dedicación mensual de cada trabajador a cada
obra** y lo lleva a los partes de trabajo de Sigrid. Sustituye a la hoja
`Plantilla_Dedicacion_Ruesma_vXX.xlsx` que Administración mantenía a mano.

Solo entra el personal que en Sigrid cobra **por mes** (código de hora `M*`
en su ficha `reshor`): jefes de obra, encargados, técnicos, administración.
El personal que va por horas se registra en el otro sistema, `partes`, con
sus partes diarios. Los dos escriben en las **mismas tablas** de Sigrid
(`hmo` / `hmores`), cada uno con su propio espacio de `synckey`.

Estado a 2026-08-20: **funciona en local**. El despliegue en Azure está
**escrito y sin ejecutar**: los scripts viven en `infra/` y los ejecuta una
persona (F-008). Qué exponemos y qué consumimos, en
[`docs/INTEGRACION.md`](INTEGRACION.md).

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

> **Esta sección es la ÚNICA fuente normativa de las reglas P1-P5.** El
> README del transfer, los docstrings y las specs **remiten** a las anclas
> `#regla-p1` … `#regla-p5`, `#regla-conflicto`, `#regla-capacidad`,
> `#regla-sin-partida` y
> `#regla-pruebas`; no vuelven a enunciar la regla con palabras propias. Lo
> vigila `services/dedicacion-transfer/tests/test_f002_fuente_unica.py`, que
> falla si alguien la reenuncia fuera de aquí.
>
> Todos los puntos están validados. Que la regla esté escrita no autoriza a
> escribir en producción: `OBRA_PRUEBAS_FORZAR` se queda a `true` hasta que
> la verificación real contra Sigrid (F-002, T13 y T14) la haga el humano.

1. <a id="regla-p1"></a>**Solo recursos mensuales (P1).** Se registra únicamente el recurso que
   tenga un código de hora `M*` (`MENC`, `MCAP`, `MJEFO`…) en `reshor`. Es
   el mismo filtro que aplica la sincronización de empleados de la API, y
   por eso lo que se captura y lo que se registra coinciden. Un recurso sin
   `M*` se omite con motivo; no es un error.
2. <a id="regla-p2"></a>**La línea va al último día del mes (P2).** El parte de Sigrid es por
   obra y mes natural; la fecha (`fec`) de la línea es siempre el último día
   de ese mes, no el día en que se trabajó ni el de captura.
3. <a id="regla-p3"></a>**El porcentaje viaja sobre 1 (P3).** En PostgreSQL se guarda 0-100
   (`asignacion.porcentaje`, `Numeric(6,2)`); al transfer se manda **dividido
   entre 100** (40 % → `0.4`). En Sigrid, `can` = ese valor sobre 1, `pre` =
   importe mensual del recurso en `reshor`, `tot = can × pre`. Confundir las
   dos escalas escribe importes 100 veces mayores o menores.
4. **El total de un trabajador debe ser 100 %.** `FALTA` (<100), `EXCESO`
   (>100) y `SIN_CARGA` (sin líneas) son estados visibles, no bloqueos: se
   puede guardar un cuadrante incompleto. La comparación usa una épsilon de
   0,005 (`dedicacion-api/domain/estados.py`) para no pelearse con los
   decimales.

   **Esa épsilon no está sola.** `dedicacion-transfer` usa la misma,
   convertida a la escala 0-1 de Sigrid (0,00005), para decidir si una
   jornada se pasa del 100 % en un parte:
   [`#regla-capacidad`](#regla-capacidad). Quien cambie una tiene que
   cambiar la otra, o el front dará por `OK` cuadrantes que el transfer
   marcará como sobrecarga.
5. <a id="regla-p5"></a>**Postventa es una obra, no una marca (P5).** Una asignación con
   `es_postventa` no se escribe en su obra: se escribe en la obra de
   postventa que declare `POSTVENTA_OBRA_COD` (el valor vive en el `.env`,
   no aquí), imputando a una **partida hoja activa** del presupuesto de esa
   obra: la que corresponde a la **obra original**. Por eso la clave única
   de `asignacion` incluye `es_postventa`: un trabajador puede tener la
   misma obra dos veces, una normal y otra de postventa.

   Tres precisiones que deciden qué se escribe:

   - **Partida hoja, nunca un capítulo.** El destino (`hmores.paride`) es
     siempre una hoja del árbol del presupuesto y activa (`tipdes = 0`). Es
     el mismo universo que el preflight publica en `partidas_postventa` para
     el desplegable del front: el automático y el desplegable **no pueden
     apuntar a sitios distintos**.
   - **Casado por código exacto.** En `obrparpar` el código y la
     descripción son campos separados (`cod`, `res`); lo que la pantalla de
     Sigrid enseña junto es la concatenación de los dos. Se compara el
     código de la obra original contra `cod` normalizado, **entero**: `0656`
     y `656` son códigos **distintos** y no casan entre sí. Solo si no hay
     coincidencia exacta se aplican las cascadas (empieza por → código en la
     descripción → nombre), siempre sobre hojas activas y de forma
     **determinista** (el orden en que Sigrid devuelva las filas no puede
     cambiar la partida elegida).
   - **Sin casado no se escribe.** La línea se omite con su motivo, visible
     en el preflight. Lo mismo si la obra de postventa no existe en Sigrid.

   *Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
   verificado contra Sigrid, ver `progress/sigrid_F-002.md`* (lectura del
   presupuesto completo de la obra de postventa: 225 hojas, 23 capítulos, y
   las 84 partidas de obra todas hojas colgando de `CD`).
6. <a id="regla-p4"></a><a id="regla-conflicto"></a>**Identidad de la línea e idempotencia (P4 · Regla A).**
   `synckey = "porcentajes:{asignacion_id}"` (no se cruza con los partes
   diarios, que usan otro prefijo): reejecutar no duplica.

   Dos líneas del parte son **la misma línea** si, y solo si, coinciden los
   **cuatro** campos: recurso, mes, código de hora y **partida**. En la obra
   normal y en la de postventa, con el mismo criterio. Consecuencias:

   - Una línea `M*` previa del recurso con **otra partida** es una línea
     legítima distinta: no es conflicto y **no se toca**. Un mismo
     trabajador puede tener varias líneas en el mismo parte repartidas
     entre partidas — cuánto puede sumar entre todas lo dice
     [`#regla-capacidad`](#regla-capacidad).
   - Cuando los cuatro campos sí coinciden es **conflicto**, aunque la línea
     previa esté en **otro día** del mes: hay que confirmar el pisado, que
     la sustituye y de paso corrige la fecha.
   - Una línea que lleve una `synckey` de la ejecución en curso no choca:
     lo que escribimos nosotros no compite con nosotros mismos.
   - Hay un tercer caso que también se confirma antes de escribir y que no
     mira lo que ya hay en el parte, sino dónde se imputa lo que vamos a
     escribir: [`#regla-sin-partida`](#regla-sin-partida).

   El criterio de choque y la clave del conflicto salen de **una sola
   función**, `application/services/reglas_porcentajes.campos_identidad`:
   ahí y en ningún otro sitio se decide qué es «la misma línea».

   *Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
   decisión D2, `specs/F-002-reglas-postventa-conflicto/requirements.md` §2.*
   Ninguna de las dos versiones que el repositorio enfrentaba era la buena:
   la vieja P4 se parte en dos reglas, esta (identidad) y la siguiente
   (capacidad).
7. <a id="regla-capacidad"></a>**La jornada de un trabajador en un parte no pasa de 1 (Regla B).**
   Por trabajador y parte, la suma de `can` de sus líneas `M*` no puede
   pasar de **1** (el 100 % de la persona). Cuentan **todas** las líneas
   cuyo código de hora empiece por `M`, sea cual sea el código concreto: el
   límite es la jornada, no el concepto.

   - **Qué entra en la suma:** las líneas `M*` que ya están en el parte y no
     se van a pisar ni son de la ejecución en curso, más las que se van a
     escribir. Se calcula **suponiendo que todos los pisados propuestos se
     confirman**, que es la única hipótesis segura: cualquier otra
     combinación escribe estrictamente menos.
   - **Tolerancia 0,00005.** Es la épsilon del punto 4 (0,005 sobre escala
     0-100) convertida a la escala 0-1 de Sigrid. **Las dos son la misma**:
     un cuadrante que la API da por `OK` no puede convertirse aquí en una
     sobrecarga. Cambiar una obliga a cambiar la otra.
   - **Al pasarse se avisa, no se decide.** El preflight devuelve un
     conflicto de **sobrecarga**, con las cifras que lo justifican; sin
     confirmación **no se escribe** ninguna de las líneas que lo provocan, y
     quedan listadas como omitidas con su motivo. Confirmar una sobrecarga
     escribe **y no borra nada**.
   - **Alcance: un parte, es decir, una obra.** El 100 % del trabajador
     entre **todas** sus obras es otra regla, la del punto 4, y vive en
     `dedicacion-api`. Esta solo ve el parte que tiene delante, y por eso
     tampoco detecta sobrecargas previas en las que no participa.

   *Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
   decisión D2, `specs/F-002-reglas-postventa-conflicto/requirements.md` §2.*
8. <a id="regla-sin-partida"></a>**Una línea sin partida no se escribe en silencio (Regla C).**
   En la obra normal, si el casado de partida falla, la línea se escribiría
   con `hmores.paride = 0`: colgada de la obra, sin imputar a ninguna
   partida del presupuesto. Eso **no se escribe sin confirmación
   explícita**.

   - **Al no casar se avisa, no se decide.** El preflight devuelve un
     conflicto de **sin partida**, uno por línea. Sin confirmación **no se
     escribe**, y la línea queda listada como **omitida** con su motivo.
     Confirmarla la escribe con `paride = 0` —el comportamiento anterior— y
     **no borra nada**.
   - **La decisión es por LÍNEA.** A diferencia de la sobrecarga, que es
     propiedad del conjunto de líneas del trabajador, que el casado falle lo
     es de una línea concreta: su categoría y su nombre. Confirmar una no
     puede arrastrar a otra que el humano no ha mirado.
   - **Los tres avisos se enseñan a la vez y en orden**: sin partida,
     pisado, sobrecarga. Una misma línea puede caer en varios, y cada uno se
     confirma por separado, porque cada uno es una decisión distinta. El
     orden no es estético: cada aviso **da por hecho** el anterior (la
     identidad del pisado usa el `paride` de la línea, y la suma de la
     sobrecarga incluye su `can`). Retenida por varios, la línea sale **una
     sola vez** en `omitidas`, con el motivo del primero.
   - **Alcance: la obra normal.** La **postventa** no llega hasta aquí: sin
     partida casada no tiene destino posible en un presupuesto ajeno al de
     su obra, así que [`#regla-p5`](#regla-p5) la **omite** y no hay nada que
     confirmar. En la obra normal sí hay destino —la propia obra— y lo único
     que falta es la imputación analítica: por eso se puede escribir, y por
     eso se pregunta.
   - **La elección alternativa sigue existiendo:** el preflight publica las
     partidas de la obra en `partidas_obra` y el front las ofrece en un
     desplegable. Confirmar «sin partida» es lo que se hace cuando ninguna
     vale, no el único camino.

   *Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-20 ·
   preflight real del periodo 2026-07*, donde una jefa de obra iba a
   escribirse con 2.132,28 € (`can = 0,385`) colgados de la obra sin partida,
   con un aviso informativo que no retenía nada y que nadie tenía que
   atender.
9. <a id="regla-pruebas"></a>**Modo pruebas por defecto.** `OBRA_PRUEBAS_FORZAR=true` desvía TODA
   escritura a la obra `0404` con la marca `PRUEBA-PORC` en `tex`. La
   partida de postventa se sigue resolviendo contra la obra de postventa
   real, para que la prueba valide el casado.
10. **`ide` reservado a mano.** Las líneas se insertan con `MAX(ide)+1` bajo
    `UPDLOCK, HOLDLOCK`: el transfer va a **una sola instancia**. Dos
    procesos escribiendo a la vez se pisan los `ide`.
11. **Trampas de Sigrid heredadas de partes.** Lotes de 15 sentencias como
    máximo; solo base `ruesma`; `tex` es TEXT, hay que comparar con
    `CAST(tex AS NVARCHAR(200)) = ?`; el parte se localiza por `cod` **y**
    `tip`; tras crear la cabecera hay que releer su `ide` antes de insertar
    líneas.

## Acceso a datos y sistemas externos

| Sistema | Quién | Modo | Notas |
|---|---|---|---|
| `sigrid-api` (Function App) | api | **solo lectura** (`POST /api/sql/read`) | maestros de empleados y obras; consultas parametrizadas en `config/config.yaml` |
| `sigrid-api` | transfer | **escritura** | único punto de escritura del sistema; base `ruesma` siempre (`ruesma_rep` es réplica de solo lectura) |
| PostgreSQL `dedicacion` | api | lectura y escritura | en local, `localhost`. Desplegado, **base propia dentro del servidor compartido `psql-albaranes-rs9k2`** (decisión del humano, 2026-08-20), esquema `public`, rol de aplicación propio y `PG_SSLMODE=require` |
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

**El despliegue está escrito y todavía sin ejecutar** (F-008, 2026-08-20).
Los scripts viven en `infra/`, los ejecuta **una persona** —no hay CI/CD— y
su manual es [`infra/README_dedicacion.md`](../infra/README_dedicacion.md).
Los tres servicios siguen corriendo en local: transfer (8006) → api (8090) →
front (8080), en ese orden. Los tres traen ya `Dockerfile` y `.dockerignore`.

**Qué expone y qué consume el proyecto:
[`docs/INTEGRACION.md`](INTEGRACION.md)**, que es la fuente de verdad y de la
que se copia `azure-apps/dedicacion.md`.

### Topología

Tres Container Apps en `rg-dedicacion-dev` (`spaincentral`), **solo el front
expuesto**:

| Container App | Puerto | Ingress | Réplicas |
|---|---|---|---|
| `ca-dedicacion-front` | 8080 | **externo** + Easy Auth (Entra) | min 1 / max 1 |
| `ca-dedicacion-api` | 8090 | interno | min 1 / **max 1** |
| `ca-dedicacion-transfer` | 8006 | interno | min 1 / **max 1** |

Los dos `max 1` no son ajuste de coste: el transfer inserta con `MAX(ide)+1`
bajo `UPDLOCK, HOLDLOCK` (§9) y dos réplicas se pisarían los `ide`; la
sincronización de maestros de la api no está diseñada para concurrencia.

**El ingress interno de la api es su control de acceso**, no una preferencia:
la api no tiene autenticación propia (`deps.py::obtener_usuario` lee la
cabecera `X-Usuario` y se la cree). El razonamiento completo, y por qué nadie
debe «arreglarlo» abriendo el ingress, está en `docs/INTEGRACION.md` §5.

### Se reutiliza, no se crea

`acralbaranesdev` (imágenes, por identidad gestionada; su usuario admin está
deshabilitado), `psql-albaranes-rs9k2` (base propia; somos el **quinto
inquilino** y no tocamos nada a nivel de servidor) y `sigrid-api`. **No se
crea Storage Account ni colas**: aquí no hay canal asíncrono.

### La base de datos ya no la crea el servicio

`dedicacion-api` arranca con `AUTO_CREATE_DATABASE=false` y **ni siquiera
abre la conexión de administración**: la base y el rol los crea una persona,
una vez, con `infra/crear_base_dedicacion.ps1`. Así la contraseña del
administrador de un servidor compartido por cinco proyectos no viaja a ningún
contenedor. Si la base falta, el arranque falla nombrándola y nombrando el
script que la crea.

### Timeouts encadenados

Cada salto espera **más** que el siguiente, y todos por debajo del corte del
balanceador de Azure:

| Salto | Variable | Local | Desplegado |
|---|---|---|---|
| navegador → front | (balanceador de Azure) | — | **230 s, no configurable** |
| front → api | `API_TIMEOUT_S` | 120 | **200** |
| api → transfer | `TRANSFER_TIMEOUT_S` | 180 | **180** |
| transfer → `sigrid-api` | `SIGRID_API_TIMEOUT_S` | 60 | 60 |

En local están al revés (el front se rinde antes que la api): el usuario
vería un error de un registro que sí se estaba haciendo. Se corrige al
desplegar, subiendo el front a 200 s.

### Imágenes y secretos

Tag fechado `rAAAAMMDD-HHmm`, **nunca `latest`** y nunca reescribiendo un tag
publicado. Qué tag hay publicado por servicio consta en `infra/imagenes.json`,
versionado: es lo que responde «qué código está corriendo» sin abrir Azure.
Los secretos van en un Key Vault propio y se consumen por `keyvaultref` con
la identidad gestionada; ninguno viaja como valor ni entra en la imagen.

### El transfer sigue en modo pruebas

`OBRA_PRUEBAS_FORZAR=true`: toda escritura va a la obra `0404` marcada
`PRUEBA-PORC` ([`#regla-pruebas`](#regla-pruebas)). **El despliegue termina
así, a propósito.** Salir de ahí exige dos señales explícitas en el script y
una decisión expresa del humano para una acción concreta.
