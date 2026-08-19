# porcentajes-transfer

Registro de la **dedicación mensual (porcentajes)** en los **partes de
trabajo de Sigrid**. Réplica del patrón validado en `partes-transfer`:
único servicio con la credencial de escritura, contrato
`preflight` / `ejecutar`, idempotencia por `synckey` y modo pruebas.

## Reglas de negocio

Las reglas **P1, P2 y P3** —qué recursos entran, qué fecha lleva la línea y
en qué escala viaja el porcentaje— **no se enuncian aquí**. Su única fuente
normativa es `docs/ARCHITECTURE.md` § Semántica de dominio imprescindible:
[`#regla-p1`](../../docs/ARCHITECTURE.md#regla-p1),
[`#regla-p2`](../../docs/ARCHITECTURE.md#regla-p2) y
[`#regla-p3`](../../docs/ARCHITECTURE.md#regla-p3).

Lo que sí es de este servicio, y por eso se cuenta aquí: la resolución
automática de la partida (`partida_resolver.py`), el override manual del
front (`paride` en la línea de entrada, `partida_metodo=manual`) y que el
preflight devuelva `partidas_obra` / `partidas_postventa` (ide/cod/res) para
poblar el desplegable.

El criterio de conflicto y la clave que confirma el pisado salen de una sola
función, `reglas_porcentajes.campos_identidad`
([`#regla-conflicto`](../../docs/ARCHITECTURE.md#regla-conflicto)).

### P4 y P5 · PENDIENTE · decisión D1/D2 de F-002

> Lo que sigue es el enunciado **heredado**, y se contradice con el de los
> docstrings. **No es normativo**: la regla buena la fija Administración y
> se escribirá en `docs/ARCHITECTURE.md` (`#regla-p4` y `#regla-p5`).
> Hasta entonces, `OBRA_PRUEBAS_FORZAR` se queda a `true`.

- **P4** Si el recurso ya tiene un registro `M*` en ese parte — **aunque
  sea en otro día** — es conflicto; pisar lo sustituye (y corrige la fecha).
- **P5** PARTIDA de imputación:
  - **Obra normal**: la partida asignada al recurso, como en partes —
    se casa por CATEGORÍA (rol) y NOMBRE contra las hojas de CI (o
    CI+CD según categoría) del presupuesto de la obra origen
    (`partida_matcher`/`partida_catalog` copiados de
    partes-persistencia). Sin casado: se escribe con paride=0 y un
    `aviso` en el preflight (editable).
  - **Postventa**: obra `POSTV2` (`POSTVENTA_OBRA_COD`); la partida es
    la del CÓDIGO DE LA OBRA original (0707 -> partida "0707 · …";
    exacto > empieza por > descripción). Sin casado, la línea se omite
    con motivo.
  - El front puede **editar la partida**: si la línea trae `paride`
    (override), manda sobre el automático (`partida_metodo=manual`).
    El preflight devuelve `partidas_obra` y `partidas_postventa`
    (hojas ide/cod/res) para poblar el desplegable.
  - Conflictos: en postventa la partida forma parte de la identidad
    (una línea legítima por obra original); en la obra normal una línea
    M* previa del recurso choca aunque tenga otra partida.

`synckey = "porcentajes:{asignacion_id}"` (no se cruza con los diarios).

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
