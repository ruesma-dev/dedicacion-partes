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

Línea: `{registro_id, ano, mes, porcentaje (sobre 1), empleado_ide,
recurso_ide?, dni?, nombre?, es_postventa}`. El servicio resuelve el
recurso del empleado (`res.conide`) eligiendo el que tenga `M*`.

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
