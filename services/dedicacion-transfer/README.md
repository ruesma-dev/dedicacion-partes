# porcentajes-transfer

Registro de la **dedicación mensual (porcentajes)** en los **partes de
trabajo de Sigrid**. Réplica del patrón validado en `partes-transfer`:
único servicio con la credencial de escritura, contrato
`preflight` / `ejecutar`, idempotencia por `synckey` y modo pruebas.

## Reglas (Administración, 25/07/2026)

- **P1** Solo recursos con código de hora **mensual** (`M*`) en `reshor`.
- **P2** La línea va SIEMPRE al **último día del mes** (`fec`).
- **P3** `can` = porcentaje **sobre 1** (40 % -> 0.4); `pre` = importe
  mensual del recurso; `tot = can × pre`.
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
