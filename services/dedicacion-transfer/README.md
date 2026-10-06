# porcentajes-transfer

Registro de la **dedicación mensual (porcentajes)** en los **partes de
trabajo de Sigrid**. Réplica del patrón validado en `partes-transfer`:
único servicio con la credencial de escritura, contrato
`preflight` / `ejecutar`, idempotencia por `synckey` y modo pruebas.

## Reglas de negocio

**Las reglas de negocio no se enuncian aquí.** Su única fuente normativa es
`docs/ARCHITECTURE.md` § Semántica de dominio imprescindible:

| Regla | Qué decide | Ancla |
|---|---|---|
| P1 | qué recursos entran | [`#regla-p1`](../../docs/ARCHITECTURE.md#regla-p1) |
| P2 | qué fecha lleva la línea | [`#regla-p2`](../../docs/ARCHITECTURE.md#regla-p2) |
| P3 | en qué escala viaja el porcentaje | [`#regla-p3`](../../docs/ARCHITECTURE.md#regla-p3) |
| P4 · Regla A | qué es «la misma línea» del parte | [`#regla-p4`](../../docs/ARCHITECTURE.md#regla-p4) · [`#regla-conflicto`](../../docs/ARCHITECTURE.md#regla-conflicto) |
| Regla B | cuánta jornada cabe en un parte | [`#regla-capacidad`](../../docs/ARCHITECTURE.md#regla-capacidad) |
| Regla C | qué pasa con una línea que no casa partida | [`#regla-sin-partida`](../../docs/ARCHITECTURE.md#regla-sin-partida) |
| P5 | dónde y contra qué se imputa la postventa | [`#regla-p5`](../../docs/ARCHITECTURE.md#regla-p5) |
| — | modo pruebas | [`#regla-pruebas`](../../docs/ARCHITECTURE.md#regla-pruebas) |
| — | a qué empresa se imputa y cómo se busca la obra | [`#regla-empresa`](../../docs/ARCHITECTURE.md#regla-empresa) |
| — | las partidas de obras varias como obras propias | [`#regla-var`](../../docs/ARCHITECTURE.md#regla-var) |

Dónde se implementan: la identidad, la capacidad y el «sin partida», en
`application/services/reglas_porcentajes.py` (funciones puras, sin I/O); la
orquestación, en `application/pipelines/registro_pipeline.py`.

Lo que sí es de este servicio, y por eso se cuenta aquí:

- **Resolución automática de la partida** (`partida_resolver.py`). En la
  obra normal se casa por CATEGORÍA (rol) y NOMBRE contra las hojas de CI
  (o CI+CD según categoría) del presupuesto de la obra origen
  (`partida_matcher` / `partida_catalog`, copiados de
  `partes-persistencia`). Qué pasa cuando no casa lo dice
  [`#regla-sin-partida`](../../docs/ARCHITECTURE.md#regla-sin-partida).
- **Override manual del front**: si la línea de entrada trae `paride`,
  manda sobre el automático (`partida_metodo=manual`). En postventa el
  override se valida contra las hojas activas del presupuesto; si apunta a
  otra cosa, la línea se omite con motivo.
- **Catálogos para el desplegable**: el preflight devuelve `partidas_obra` y
  `partidas_postventa` (hojas activas, `ide`/`cod`/`res`).
- **`synckey = "porcentajes:{asignacion_id}"`**, que no se cruza con el
  espacio de los partes diarios.

## Arranque

    copy .env.example .env    (y completar la function key)
    pip install -r requirements.txt
    python main.py            (puerto 8006)

## API

    GET  /health
    POST /api/registro/preflight   {obra, lineas[], usuario}
    POST /api/registro/ejecutar    {obra, lineas[], pisar_claves[], usuario}
    POST /api/postventa/universo   {empresa, obras[]}   (solo lee; F-025)
    POST /api/var/universo         {empresa}            (solo lee; F-039)

`/api/postventa/universo` devuelve las obras que admiten postventa en esa
empresa, con su partida, calculadas con las mismas funciones que el
preflight ([`#regla-p5`](../../docs/ARCHITECTURE.md#regla-p5)).
`/api/var/universo` devuelve la obra VAR de esa empresa y sus partidas VAR,
con las mismas funciones que validan `var_paride` en el preflight
([`#regla-var`](../../docs/ARCHITECTURE.md#regla-var)).

Línea: `{registro_id, ano, mes, porcentaje (sobre 1), recurso_ide, dni?,
nombre?, es_postventa, empresa, var_paride?}`. `empresa` es la `con.emp` a la que se
imputa: sin ella la línea se omite con motivo, y con líneas de dos empresas
la petición se rechaza con 422
([`#regla-empresa`](../../docs/ARCHITECTURE.md#regla-empresa)).
`recurso_ide` es el `res.ide` del trabajador y lo manda la API: el servicio
lo usa tal cual, no lo elige ni consulta `res.conide`; sin él, la línea se
omite «sin recurso» ([`#regla-recurso`](../../docs/ARCHITECTURE.md#regla-recurso),
F-026). El ide de la ficha de empleado ya no forma parte del contrato: si
llega, se ignora.

## Antes de escribir nada

    python prueba_escritura_porcentajes.py inspeccionar

Volcado de líneas `M*` reales (`can/canres/pre/tot/paride/caaide`) y de
`hderes`: confirma el mapeo (sobre todo si `paride`/`caaide` deben ir
rellenos — hoy se escriben a 0). Después: `estado` → editar
`LINEAS_PRUEBA` → `preflight` → `ejecutar --confirmar` → `verificar` →
pantalla de Sigrid → `limpiar --confirmar`.

## Pitfalls heredados (ya pagados en diarios)

Lotes de máx. 15 sentencias; solo BBDD `ruesma`; `tex` es TEXT
(`CAST(tex AS NVARCHAR(200)) = ?`); `ide` por `MAX(ide)+1` con
`UPDLOCK, HOLDLOCK`; localizar el parte por `cod` **y** `tip`; crear
cabecera y releer el `ide` antes de insertar líneas.
