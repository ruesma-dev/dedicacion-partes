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
atómica de asignaciones por trabajador, `deshacer` (solo lo propio,
[`#regla-deshacer`](#regla-deshacer)), `completar` (lote «completar al
100 %» en una obra, [`#regla-completar`](#regla-completar)), `export.xlsx`,
`registro/preflight` + `registro/ejecutar` y `empresas` (las del selector,
con su nombre de Sigrid y si están de baja).

Tablas de PostgreSQL: `trabajador`, `obra` (copias sincronizadas de Sigrid,
PK = el `ide` de Sigrid: en `trabajador`, el `res.ide` de su **recurso**,
[`#regla-recurso`](#regla-recurso); en `obra`, el de su ficha, con dos marcas
independientes que pone el sync: `activa`, que su estado no esté excluido, y
`admite_postventa`, que esté en el universo de postventa,
[`#regla-p5`](#regla-p5), F-025; además, una fila por partida VAR, con `ide`
negativo y su obra y partida de registro, [`#regla-var`](#regla-var), y
ninguna obra con 6 o más dígitos seguidos en el código,
[`#regla-seis-digitos`](#regla-seis-digitos), F-039), `empresa` (catálogo `auxemp` de Sigrid, PK =
`numemp`, que es el `con.emp` de las fichas; F-032), `periodo` (año+mes único, `ABIERTO`/`CERRADO`),
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

- `POST /api/registro/preflight` — pasos 1-8: resolver destinos, cargar los
  tipos de hora del recurso que trae cada línea (lo manda la API, el transfer
  no lo elige: [`#regla-recurso`](#regla-recurso)), aplicar las reglas,
  resolver la cuenta analítica de cada línea, elegir el parte del periodo,
  comprobar idempotencia y detectar conflictos
  ([`#regla-analitica`](#regla-analitica)). No escribe nada.
- `POST /api/registro/ejecutar` — pasos 9-10: crear los partes que falten
  (`con` + `hmo` con alta protegida, releyendo el periodo) y borrar las
  pisadas confirmadas + insertar las líneas nuevas, por lotes.

`application/services/reglas_porcentajes.py` concentra las reglas P1-P5;
`application/pipelines/registro_pipeline.py` las orquesta;
`infrastructure/sigrid/sigrid_write_client.py` es lo único que habla con
`sigrid-api` en modo escritura.

## Semántica de dominio imprescindible

> **Esta sección es la ÚNICA fuente normativa de las reglas P1-P5.** El
> README del transfer, los docstrings y las specs **remiten** a las anclas
> `#regla-p1` … `#regla-p5`, `#regla-conflicto`, `#regla-capacidad`,
> `#regla-sin-partida`, `#regla-pruebas`, `#regla-empresa`,
> `#regla-recurso`, `#regla-deshacer`, `#regla-completar`,
> `#regla-analitica`, `#regla-var` y `#regla-seis-digitos`; no vuelven a
> enunciar la regla con palabras propias. Lo vigila `services/dedicacion-transfer/tests/test_f002_fuente_unica.py`, que
> falla si alguien la reenuncia fuera de aquí.
>
> Todos los puntos están validados. Que la regla esté escrita no autoriza a
> escribir en producción: `OBRA_PRUEBAS_FORZAR` **se queda a `true`**.
>
> **Actualización 2026-10-01:** el humano dio esa autorización expresa y el
> transfer desplegado está en **modo real** (`OBRA_PRUEBAS_FORZAR=false`), con
> lo que sigue abierto a sabiendas: el motivo de abajo (F-017) y los varios
> códigos M* (F-011). Desde F-026 el recurso de cada línea lo manda la API
> ([`#regla-recurso`](#regla-recurso)).
>
> El motivo ya no es que falte verificar contra Sigrid —**T13 y T14 se
> ejecutaron el 2026-08-20** y el sistema escribe de verdad en el ERP—, sino
> el que consta en `progress/sigrid_F-002.md` § «Qué NO queda demostrado»:
> **la imputación a partidas en producción no está validada**. En modo pruebas
> toda línea se desvía a la obra `0404` conservando la partida de su obra de
> origen, así que solo la línea cuya obra original *era* la de pruebas resultó
> representativa. Salir del modo pruebas exige **autorización expresa del
> humano para una acción concreta**.

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
   - **Casado por código, sin escalones ajenos.** En `obrparpar` el código y
     la descripción son campos separados (`cod`, `res`); lo que la pantalla
     de Sigrid enseña junto es la concatenación de los dos. Se compara el
     código de la obra original contra `cod` normalizado (mayúsculas, sin
     espacios ni guiones), **entero**: `0656` y `656` son códigos
     **distintos** y no casan entre sí. Sin coincidencia exacta solo vale la
     partida cuyo código normalizado **empieza por el de la obra seguido
     solo de letras** (`0578` → `0578B`, `0654` → `0654-B`): la más corta y,
     a igualdad, la menor. Nada más: ni el prefijo seguido de otra cosa
     (`CP` → `CP.1`; una obra que en el presupuesto fuera un capítulo, con
     sus hijas), ni el código en la descripción, ni el nombre de la obra,
     que casaban obras con partidas ajenas. Siempre sobre hojas activas y de
     forma **determinista** (el orden en que Sigrid devuelva las filas no
     puede cambiar la partida elegida).
   - **Universo de postventa.** Las obras que admiten `Postv-` son las de la
     empresa de las obras a las que este casado encuentra partida en la
     obra de postventa de **esa misma** empresa. Lo calcula **solo** el
     transfer (`POST /api/postventa/universo`, con las mismas funciones que
     el preflight); la api lo pide en cada sync y lo guarda en
     `obra.admite_postventa`, independiente de `obra.activa` (el filtro de
     estado). Una obra excluida por estado (cerrada, terminada…) que esté en
     el universo **solo se ofrece como `Postv-`**; una abierta fuera de él,
     solo como obra normal. Es la foto del último sync: el preflight sigue
     mandando, y lo ya guardado se queda, marcado como no ofrecible.
   - **Sin casado no se escribe.** La línea se omite con su motivo, visible
     en el preflight. Lo mismo si la obra de postventa no existe en Sigrid.
   - **La obra de postventa es la de la empresa de la petición**: ver
     [`#regla-empresa`](#regla-empresa).

   *Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
   verificado contra Sigrid, ver `progress/sigrid_F-002.md`* (lectura del
   presupuesto completo de la obra de postventa: 225 hojas, 23 capítulos, y
   las **86** partidas de obra, todas hojas, **82 colgando de `CD` y cuatro
   sueltas en la raíz** — `656`, `664`, `680` y `693`, duplicados sin el cero
   inicial que Administración debería limpiar; ver F-014).
   *El casado sin escalones ajenos y el universo los decidió el responsable
   del proyecto el 2026-10-01 (F-025, D2 = B y D4: un único universo, el de
   la empresa de las obras) y el 2026-10-03 (D8 = A: la obra-capítulo queda
   fuera), `specs/F-025-obras-postventa-postv2/requirements.md`.*
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
   - **Alcance: todos los partes del periodo** de la obra destino, no solo
     el que recibe las líneas (F-037). Una `synckey` nuestra en cualquiera
     de ellos, también cerrado, es «ya registrada». Si la línea que choca
     está en un parte **cerrado**, la nuestra se **omite** con motivo
     `parte_cerrado` (y prevalece sobre un choque En registro): en un
     cerrado no se escribe ni se borra. Si está en uno En registro, es el
     conflicto de siempre, con el código del parte donde vive. Ver
     [`#regla-analitica`](#regla-analitica).

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
   - **Alcance: los partes del periodo de una obra.** Suma las líneas `M*`
     del trabajador en **todos** los partes de esa obra y mes, cerrados
     incluidos (F-037, [`#regla-analitica`](#regla-analitica)): un
     complementario no es una jornada nueva. El 100 % del trabajador entre
     **todas** sus obras es otra regla, la del punto 4, y vive en
     `dedicacion-api`. Esta solo ve la obra que tiene delante, y por eso
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
     que falta es la partida del presupuesto: por eso se puede escribir, y
     por eso se pregunta. La partida **no** es la cuenta analítica de la
     línea: esa sale del recurso
     ([`#regla-analitica`](#regla-analitica)).
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
   real, para que la prueba valide el casado. La obra de pruebas se busca en
   la empresa de la petición: ver [`#regla-empresa`](#regla-empresa).
10. **`ide` reservado a mano.** Las líneas se insertan con `MAX(ide)+1` bajo
    `UPDLOCK, HOLDLOCK`: el transfer va a **una sola instancia**. Dos
    procesos escribiendo a la vez se pisan los `ide`.
11. **Trampas de Sigrid heredadas de partes.** Lotes de 15 sentencias como
    máximo; solo base `ruesma`; `tex` es TEXT, hay que comparar con
    `CAST(tex AS NVARCHAR(200)) = ?`; el parte se localiza por `cod` **y**
    `tip`; tras crear la cabecera hay que releer su `ide` antes de insertar
    líneas.
12. <a id="regla-empresa"></a>**La obra se busca por código y empresa.** El código de una obra
    solo es único **dentro de su empresa** (`con.emp`): la misma obra puede
    tener ficha en Construcciones Ruesma y en Porsan, y quedarse con «la
    primera» que devuelve Sigrid es imputar a la empresa equivocada. Por eso:

    - **La empresa viaja en cada línea** del contrato API → transfer
      (`empresa`, entero > 0). La pone `dedicacion-api` y es **la empresa
      de las obras**, sea cual sea la elegida en el selector: los
      trabajadores son de varias empresas, pero las obras, **postventa
      incluida**, son siempre de una sola, la del ajuste
      `EMPRESA_IMPUTACION` (hoy la 1, Construcciones Ruesma). Ese ajuste es
      además la **empresa por defecto** del selector: la que sale elegida al
      entrar y la que se usa si una petición no trae empresa. El transfer
      **no tiene empresa por defecto**.
    - **El selector filtra trabajadores.** Con la empresa E elegida
      (parámetro `empresa` de cada ruta del periodo), un trabajador con
      empresa se ve solo en la suya; uno sin empresa (filas desactivadas
      antes de F-023), solo en la por defecto, tenga las líneas que tenga.
      Las obras ofrecidas son las de la empresa de las obras con cualquier
      E, nunca sus fichas en otras empresas; una obra sin empresa no se
      ofrece. Cada trabajador visible lleva **todas** sus líneas; las de una
      obra que no es de la empresa de las obras cuentan para su 100 % y
      salen marcadas, con cualquier E. Resumen, copia del mes y export
      cuentan solo los visibles en E. Una persona con recursos en dos
      empresas tiene una fila en cada una, cada recurso con su propio 100 %
      ([`#regla-recurso`](#regla-recurso)).
    - **Se registra en la empresa de las obras.** Al registrar, la API manda
      solo las líneas de los trabajadores visibles en E, todas con `empresa`
      = la empresa de las obras; las de una obra de otra empresa se mandan
      igual para que su omisión quede trazada en la asignación.
    - **Sin empresa, la línea no se escribe**: se omite con su motivo y el
      resto de la petición sigue. Si ninguna línea la trae, no se lee
      ninguna obra.
    - **Una petición es de una sola empresa**, porque es una obra. Líneas
      con dos empresas distintas se rechazan enteras (HTTP 422), sin leer
      nada en Sigrid.
    - **Toda obra se busca con código y empresa**: la de origen (cuando no
      llega por `ide`), la de pruebas ([`#regla-pruebas`](#regla-pruebas))
      y la de postventa ([`#regla-p5`](#regla-p5)). Sin ficha en esa
      empresa es «no encontrada»; con más de una, obra ambigua. **Nunca se
      elige la primera.** Sin obra de postventa en la empresa, se omiten
      solo las líneas de postventa; sin obra de pruebas, no se escribe
      nada.
    - **Obra de otra empresa, líneas omitidas.** La obra de origen se
      comprueba en modo normal **y** en modo pruebas: si su empresa no es la
      de sus líneas, todas se omiten con un motivo que nombra la obra y las
      dos empresas, y no se escribe nada. En ese corte, `obra_destino` y
      `obra_origen` publican la obra de origen **resuelta en Sigrid, con su
      empresa**; en el corte por línea sin empresa no hay obra resuelta y
      sale la de entrada.
    - **El parte hereda la empresa de su obra**: la cabecera (`con.emp`) de
      un parte nuevo es la de la obra destino.

    *Decidido por Pablo Gris (responsable del proyecto) el 2026-09-29 ·
    F-022, decisiones D1-D4 de
    `specs/F-022-transfer-obra-por-empresa/requirements.md`.* *Selector,
    visibilidad y empresa elegida: decidido por Pablo Gris el 2026-10-01 ·
    F-024, decisiones D1-D7 de
    `specs/F-024-selector-empresa/requirements.md`.* *Nombre de cada
    empresa del selector: el de Sigrid (`auxemp.res`), que trae el sync;
    «Empresa N» solo si no está en la tabla `empresa`. Una empresa de baja
    o desactivada con trabajadores activos sale marcada «(de baja)», nunca
    oculta: decidido por Pablo Gris el 2026-10-01 · F-032.* *Obras siempre
    de la empresa de las obras, selector que filtra solo trabajadores y
    línea con la empresa de las obras: decidido por Pablo Gris el
    2026-10-01 · F-034, decisiones D1-D5 de
    `specs/F-034-obras-siempre-ruesma/requirements.md`.*
13. <a id="regla-recurso"></a>**El trabajador es el recurso.** El maestro de
    trabajadores parte de los **recursos** de Sigrid, no de las fichas de
    empleado, y el recurso que se escribe en el parte es el del trabajador:

    - **Quién entra:** los recursos persona (`res.cla = 1`) con código de
      hora mensual `M*` ([`#regla-p1`](#regla-p1)), de todas las empresas.
      **Una fila por recurso**: la clave del trabajador en `dedicacion` es el
      `res.ide`, y `cod`, `nombre` y empresa (`con.emp`) son los del concepto
      del recurso.
    - **La ficha de empleado es opcional.** Se une por `res.conide`
      («Empleado asociado») y solo aporta el DNI y la baja laboral, que es
      informativa. Un recurso sin ficha entra igual.
    - **Varios recursos de una persona no se funden nunca.** Cada uno es un
      trabajador, en su empresa y con su propio 100 %. Si dos de la misma
      empresa comparten documento (el DNI de la ficha o, sin él, `res.cif`),
      el preview lo avisa en `empleados.posible_misma_persona`; por nombre,
      nunca (homónimos).
    - **Vigencia por mes.** La baja del recurso es `con.fecbaj` (`AAAAMMDD`,
      0 = sin baja). Un trabajador cuenta en el mes M si está activo y no
      tiene baja o la tiene el día 1 de M o después: **dado de baja en el
      mes, sigue accesible ese mes**. Una sola función,
      `dedicacion-api/domain/vigencia.vigente_en`. Cuadrante, resumen, copia
      del mes y export enseñan el `activo` de ese mes; uno no vigente solo
      aparece si tiene líneas en él.
    - **Ventana de bajas del sync.** El sync conserva los recursos con baja
      desde el primer día del más antiguo entre el mes anterior al del sync y
      cada periodo `ABIERTO`; los de baja anterior se excluyen y el preview
      los cuenta y publica la ventana (`empleados.ventana_baja`). Un periodo
      antiguo abierto después del último sync no tiene sus bajas hasta el
      siguiente: **tras abrir un periodo antiguo, sincronizar**.
    - **La API manda el recurso; el transfer no lo elige.** Cada línea del
      registro lleva `recurso_ide` = el `ide` del trabajador. El transfer lo
      usa tal cual: no consulta `res.conide`, no elige entre recursos y no
      exige que la empresa del recurso sea la de la línea (un trabajador de
      la 18 imputa a obras de la 1, [`#regla-empresa`](#regla-empresa)). Una
      línea sin `recurso_ide` se omite «sin recurso». Las de un trabajador
      no vigente en el mes **no se mandan ni se trazan**: preflight y
      ejecutar devuelven sus `registro_id` en `no_vigentes`.

    *Decidido por Pablo Gris (responsable del proyecto) el 2026-10-01 («no
    debe buscar por empleado sino por recurso») y el 2026-10-02 (D1-D7) ·
    F-026, `specs/F-026-recursos-sin-ficha-empleado/requirements.md`.*
14. <a id="regla-deshacer"></a>**Cada uno deshace solo lo suyo.** Deshacer
    devuelve la fila **entera** del trabajador al `snapshot_antes` de su
    último evento pendiente (no deshecho) del periodo; el autor del evento
    es el usuario que llega en `X-Usuario` (Easy Auth, vía el front).

    - **Solo se deshace si ese último evento es del usuario que lo pide.**
      Si es de otro, la API responde **409** —como «nada que deshacer»—
      con el motivo, que nombra al autor, y no toca nada. Nunca se deshace
      un evento que no sea el último: si después de mi cambio hay uno de
      otro, ya no puedo deshacer el mío (deshacerlo borraría en silencio el
      suyo); vuelvo a poder cuando él deshace el suyo.
    - **`puede_deshacer`** del cuadrante y de la fila que devuelven guardar,
      deshacer y copiar trabajador es esa misma regla para quien pregunta:
      el último pendiente de cada trabajador sale en SQL (`max(id)` de los no
      deshechos del periodo), no «tiene algo pendiente mío».
    - **Los usuarios se comparan sin mayúsculas ni espacios en los
      extremos.** Una sola función: `dedicacion-api/domain/deshacer.py`. El
      front no decide: el botón sigue a `puede_deshacer` y `Ctrl+Z` pregunta
      a la API, que enseña su motivo.

    *Decidido por Pablo Gris el 2026-10-04 (decisión A) · F-027, criterios
    `acceptance` en `harness/features.json`.*
15. <a id="regla-completar"></a>**Completar al 100 % en una obra, por
    lote.** `POST /api/v1/periodos/{a}/{m}/completar` recibe los
    trabajadores, la obra destino y su modo (normal o `Postv-`), y a cada
    uno le pone **lo que le falta**: 100 menos el total de **todas** sus
    líneas, a centésimas (la escala de la columna; el total queda en
    100,00).

    - **Dónde.** En la línea del trabajador con la misma clave (obra,
      `es_postventa`), sumándolo; si no la tiene, en una línea nueva. Sus
      demás líneas no cambian. `Postv-X` y X son líneas distintas
      ([`#regla-p5`](#regla-p5)): completar en una nunca suma a la otra.
    - **A quién no.** Al que ya está en `OK` o en `EXCESO` según la misma
      regla del 100 % del cuadrante (`calcular_estado` y su épsilon: no hay
      otro criterio de «al 100 %»), ni se le resta; al no vigente en el mes
      ([`#regla-recurso`](#regla-recurso)); al que no es visible en la
      empresa elegida ([`#regla-empresa`](#regla-empresa)). Cada uno sale
      con su resultado y el lote sigue con los demás.
    - **Todo o nada.** Periodo inexistente (404) o `CERRADO` (409), y obra
      que no existe, no es de la empresa de las obras o no se ofrece en ese
      modo (`Linea.ofrecible`) (422): no se toca a nadie. Es una sola
      transacción.
    - **Deshacer.** Cada trabajador cambiado deja **un** evento
      `COMPLETAR` con su `X-Usuario`, que se deshace trabajador a
      trabajador como cualquier otro ([`#regla-deshacer`](#regla-deshacer)).
    - **No registra en Sigrid** ni llama al transfer: registrar sigue
      siendo el botón de siempre. El front solo manda quiénes y el destino
      (sin porcentajes): la cifra la pone la API, `domain/estados.py`
      (`completar_hasta_100`).

    *Decidido por Pablo Gris el 2026-09-29 (completar con el cálculo en la
    API, por lote) y el 2026-10-05 (D1-D6, las seis A) · F-029,
    `specs/F-029-seleccion-multiple-completar-100/requirements.md`.*
16. <a id="regla-analitica"></a>**La línea lleva su cuenta analítica y va
    a un parte En registro.** Es la regla de `partes` (su F-021 y su F-031),
    **la misma** porque los dos servicios escriben en el mismo parte de
    Sigrid: `estado_parte.py` y `cuenta_analitica.py` del transfer son
    **copia literal** de los de `partes` (lista cerrada de `CLAUDE.md`,
    vigilada por `tests/test_f037_copias_partes.py`).

    - **El asiento lo hace Sigrid, no el transfer.** Administración pulsa
      «Contabiliza parte…»: Sigrid genera un asiento analítico (`ANA`,
      `con.tip = 32`) por parte, con debe a la cuenta de cada línea
      (`hmores.caaide`) y haber a la contrapartida del recurso
      (`res.caaconide`), y deja el parte en Imputado. El 6XX es de la
      nómina. El transfer **solo rellena `hmores.caaide`**: no escribe
      asientos (`asi`, `asa`, `apu`, `apa`), no cambia `con.est` ni toca el
      `con`/`hmo` de un parte existente.
    - **De dónde sale la cuenta.** La **subcuenta** (el texto tras el primer
      punto del código) de `reshor.caaide` del recurso para el tipo de hora
      que se escribe; si no da, la de su tipo por defecto (`res.horide`); si
      tampoco, la de la cuenta de la **partida** de la línea, solo si es de
      coste (empieza por `CI` o `CD`; nunca `CP` ni `INGR`), con una nota.
      La cuenta es la **única** `caa` del centro de la obra destino, de su
      empresa, con esa subcuenta (en pruebas, la de `0404`; en postventa, la
      de la obra de postventa). `hmores.cenide` sigue siendo ese centro.
    - **Sin cuenta se escribe igual.** Sin subcuenta, `caaide = 0` sin
      aviso; con la obra sin esa cuenta o con varias, `caaide = 0` y un
      aviso. **Nunca se elige la primera.** Los avisos no retienen la línea.
    - **El parte del periodo.** Se leen **todos** los partes de la obra y
      el mes con su estado. Cerrado es todo lo que no está En registro
      (Cerrado, Imputado u otro). Las líneas van al En registro de **mayor
      `ide`**, aunque haya cerrados de `ide` mayor; si no hay ninguno, a uno
      nuevo, **complementario** si el periodo tiene cerrados, con
      descripción `Parte <obra>` como los de Administración. Se reutiliza el
      que haya creado `partes`.
    - **Alta protegida.** El parte nuevo se crea en una transacción que solo
      inserta si su código `PT<AA>/NNNNN` (correlativo **por empresa**) está
      libre y el periodo no tiene ya uno En registro; el `hmo` se cuelga por
      código, tipo y empresa. Se relee el periodo: si hay uno En registro,
      sea el nuestro o el de `partes`, se usa; si no, **un** reintento con
      otro código y, si tampoco, la petición falla sin insertar líneas.
    - **Duplicados y conflictos** contra todos los partes del periodo:
      [`#regla-conflicto`](#regla-conflicto) y
      [`#regla-capacidad`](#regla-capacidad). En un parte cerrado **nunca**
      se inserta ni se borra.
    - **Lecturas.** Partidas y cuentas de centro, una vez por petición;
      partes y líneas, por periodo. Si una falla o viene `truncated`, la
      petición falla sin escribir nada.
    - **Deshacer y corregir.** En un parte En registro, como hasta ahora
      (`limpiar`, pisado confirmado: la línea nueva lleva su cuenta). En uno
      cerrado **no se borra nada**: lo ajusta Administración (anula el `ANA`
      o hace el complementario), y lo heredará F-033. Una línea ya
      registrada no se reescribe ni se le rellena la cuenta.

    *Decidido por Pablo Gris el 2026-10-05 (rellenar `caaide`, la regla de
    `partes`, complementario) y el 2026-10-06 (D8-D18) · F-037,
    `specs/F-037-asiento-analitico-obra/requirements.md`.*
17. <a id="regla-var"></a>**Obras varias: sus partidas se ofrecen como obras
    propias.** La obra del ajuste `VAR_OBRA_COD` del transfer (el valor vive
    en el `.env`, no aquí) agrupa en su presupuesto obras pequeñas, una por
    partida. Se trabaja con esas partidas, no con la obra.

    - **Partida VAR.** Hoja activa del presupuesto de la obra VAR de la
      empresa de las obras cuyo **número inicial** (los dígitos con que
      empieza el código) es mayor o igual que `VAR_PARTIDA_DESDE` (29 hoy):
      `29`, `30`, `100`, `029`, `29.1` y `29A` entran; `28`, `05`,
      `CI.1.1`, un capítulo o una partida de baja, no. La obra VAR de otra
      empresa no cuenta.
    - **El universo, solo en el transfer.** `POST /api/var/universo` (una
      empresa → la obra VAR y sus partidas VAR por `ide`) y la validación
      del preflight usan **las mismas** funciones (`universo_var.py`): una
      partida está en el universo si y solo si el preflight acepta una
      línea imputada a ella. Sin obra VAR en la empresa, con la obra
      ambigua o sin `VAR_OBRA_COD`: universo vacío con su motivo.
    - **La entrada, en la api.** Cada sync y cada preview piden el universo
      **una vez**, con la empresa de las obras, y guardan cada partida como
      una fila propia de `obra`: `ide` = −(`ide` de la partida), código
      `<obra VAR>-<partida>` (`VAR-29`), la descripción de la partida,
      activa, sin postventa y con `registro_obra_ide`, `registro_obra_cod`
      y `registro_paride` (obra y partida de Sigrid donde se registra; a
      `NULL` en las obras normales). La partida que sale del universo deja
      su entrada inactiva; no se borra nada. Si el transfer no da el
      universo, sync y preview fallan enteros con 502, sin persistir nada.
    - **La obra VAR no se ofrece como obra normal**, sea cual sea su
      estado: nadie imputa a sus partidas `CI.*`. Las líneas ya guardadas
      en ella o en una entrada retirada se conservan, no ofrecibles, como en
      [`#regla-p5`](#regla-p5), y se registran como hoy.
    - **Registro.** Las líneas de una entrada viajan en la petición de su
      obra de registro, junto a las demás de esa obra, con `var_paride` y
      sin `paride` manual. El transfer las imputa a esa partida, fija
      (`partida_metodo = "var"`; el front la pinta sin desplegable), si y
      solo si está en el universo VAR de la empresa de la línea y la obra
      de la petición es la obra VAR; si no, o si la línea es de postventa,
      la omite con un motivo que nombra la partida o la obra, sin aviso de
      «sin partida». Lo demás, como cualquier línea: modo pruebas
      ([`#regla-pruebas`](#regla-pruebas)), cuenta del centro de la obra
      destino ([`#regla-analitica`](#regla-analitica)), parte del periodo,
      `synckey`, identidad con su partida
      ([`#regla-conflicto`](#regla-conflicto)) y capacidad
      ([`#regla-capacidad`](#regla-capacidad)).
    - **Para el cuadrante, Completar, las copias y el Excel** una entrada es
      una obra normal, sin modo postventa.

    *Decidido por Pablo Gris el 2026-10-06 (D1, D2, D3, D5 y D6 = A) ·
    F-039, `specs/F-039-obras-var-y-seis-digitos/requirements.md`.*
18. <a id="regla-seis-digitos"></a>**Fuera las obras con 6 o más dígitos
    seguidos en el código.** En el sync y en el preview, antes de pedir
    ningún universo, se descarta toda obra cuyo código **contenga** N o más
    dígitos seguidos, lleve o no letras o sufijo (`150414`, `0902051`,
    `090205A`, `150301-1` caen; `12345` y `VAR`, no), con N =
    `sync.obras.digitos_seguidos_excluidos` de `config.yaml` (6; 0 = sin
    filtro).

    - La descartada no va al universo de postventa ni se guarda; si ya
      estaba en la base, queda con `activa` y `admite_postventa` a `false`.
      Sus líneas ya guardadas se conservan, no ofrecibles, y se registran
      como hoy.
    - El preview publica cuántas caen y una muestra de sus códigos.
    - Sin excepciones: un código así que se adjudique tampoco saldrá.

    *Decidido por Pablo Gris el 2026-10-06 (D4: «si tienen 6 números
    seguidos también ignóralas»; D5 = A) · F-039,
    `specs/F-039-obras-var-y-seis-digitos/requirements.md`.*

## Acceso a datos y sistemas externos

| Sistema | Quién | Modo | Notas |
|---|---|---|---|
| `sigrid-api` (Function App) | api | **solo lectura** (`POST /api/sql/read`) | maestros de empleados y obras y catálogo de empresas (`auxemp`, F-032); consultas parametrizadas en `config/config.yaml` |
| `sigrid-api` | transfer | **escritura** | único punto de escritura del sistema; base `ruesma` siempre (`ruesma_rep` es réplica de solo lectura). Lee además partes del periodo con su estado, cuentas analíticas del centro y cuentas de partida ([`#regla-analitica`](#regla-analitica)); un `truncated` es error |
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

### El transfer: alta en modo pruebas; producción en real desde 2026-10-01

**Desde el 2026-10-01 el transfer desplegado está en modo real** por decisión
expresa del humano (ver `docs/INTEGRACION.md` §8, con el comando para volver).
El alta de un transfer nuevo sigue arrancando así:
`OBRA_PRUEBAS_FORZAR=true`: toda escritura va a la obra `0404` marcada
`PRUEBA-PORC` ([`#regla-pruebas`](#regla-pruebas)). **El despliegue termina
así, a propósito.** Salir de ahí exige dos señales explícitas en el script y
una decisión expresa del humano para una acción concreta.
