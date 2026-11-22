<!-- specs/F-074-partida-sin-automatica/design.md -->
# F-074 · Diseño: la partida no se queda en «automática»

**Rigor: `critico`.** Disparador 2 de «Niveles de rigor» (`CHECKPOINTS.md`):
lo que enseña la celda es la partida que el transfer **escribe en Sigrid de
producción** (`hmores.paride`, `registro_pipeline._preflight`); si el
cuadrante y el registro divergen, se imputa a una partida que nadie vio. Lo
mismo que declararon F-050, F-055 y F-068.

## 1. Servicios y límite

| Servicio | Qué cambia | Por qué ahí |
|---|---|---|
| transfer | `propuesta_descartada` en `AccionLinea` y `AccionVinculado` (R14) | solo él sabe que la guardada no vale (valida por `ide`) |
| api | estados por línea y subfila (R6-R10), partida de postventa del sync (R11-R13), borrar la guardada descartada (R16) | dueña del dato, de la cola y de la memoria |
| front | textos y clases de la celda, filtro, rótulo del selector, aviso del modal (R1-R5, R15) | solo pinta lo que manda la api |

**La regla no se toca ni se copia.** La partida que se enseña sale siempre
de funciones del transfer: `proponer_partida`/`PasoVinculados.proponer`
(cola, selector) y `casar_postventa` (universo del sync, el mismo casado que
el preflight: docstring de `universo_postventa.py`). La api solo **guarda y
marca**; el front no calcula nada. Ninguna responsabilidad nueva fuera de los
tres servicios; ninguna copia nueva entre servicios.

## 2. Diagnóstico: cuándo queda hoy «automática» y por qué

| # | Caso | Hoy en la celda | Al registrar | Con F-074 |
|---|---|---|---|---|
| a | Obra normal, la regla no da partida (los tres pasos fallan) | memoria R32 de F-055, sin marca → «automática» | conflicto «sin partida» (Regla C) | «no encuentra partida» (R6) |
| b | Obra normal, su obra vuelve `{ok: false}` (otra empresa, no encontrada) | igual que a | omitida con motivo de empresa | «no encuentra partida» |
| c | El transfer no responde o pasa su timeout (F-055 R33) | se desencola sin memoria → «automática» | — | «sin calcular»; el próximo cuadrante o escritura la reencola |
| d | Línea de **postventa** | nunca se encola (F-055 R29: solo obra normal) → «automática» | casado `#regla-p5` por obra, siempre | la partida del universo, «obra de postventa» (R11-R12) |
| e | Subfila de vinculado **en la cola** | sin marca de pendiente (F-057 es solo de líneas) → «automática» | — | «buscando partida…» (R9) |
| f | Subfila sin propuesta (titular sin partida; `sin_ci`, `varias_ci`, `empate_nombre`) | memoria de subfilas → «automática» | aviso «sin partida» del vinculado | «no encuentra partida» (R9) |
| g | Subfila en memoria cuyo titular **gana** partida | no se reencola hasta el próximo sync (fallo latente) | el preflight sí la recalcula | sale de la memoria y se recalcula (R10) |
| h | Periodo no ABIERTO | no se encola → «automática» | no se registra | «—» |
| i | Propuesta guardada que **deja de valer** | sigue enseñándola | el preflight recalcula (F-055 R6) | aviso en el modal y se borra si no hay otra (R14-R16) |

Sin cambio: la elegida, la fija VAR (también en sus subfilas, que ya pintan
la de la línea) y la propuesta guardada que vale (se escribe tal cual, F-055
R8: lo que se ve es lo que se registra).

## 3. Estados y precedencia (R1)

elegida → fija → propuesta (guardada, o la de postventa de la obra) →
`propuesta_pendiente` «buscando partida…» → `propuesta_no_encontrada` «no
encuentra partida» → ABIERTO «sin calcular» → «—». La api nunca manda a la
vez pendiente y no encontrada (la memoria y la cola son excluyentes:
`_lanzar` no encola lo que está en memoria). «sin calcular» no lo marca la
api: es lo que queda en un periodo ABIERTO cuando no hay nada (caso c, o el
de R12 sin sync), y cubre por construcción cualquier hueco.

## 4. Ficheros a crear

- `services/dedicacion-api/application/estado_partida.py` — funciones puras
  `estado_de_linea(ln, marcas) -> dict` y `estado_de_subfila(ln, v, marcas)
  -> dict`: las claves `propuesta_*`, `propuesta_pendiente` y
  `propuesta_no_encontrada` de §3 (solo con valor). Sin E/S.
- Tests: `services/dedicacion-transfer/tests/test_f074_descartada.py`;
  api `test_f074_estados.py`, `test_f074_postventa.py`,
  `test_f074_memoria_subfilas.py`, `test_f074_descartada_api.py`; front
  `test_f074_celda.py`, `test_f074_selector_modal.py`.

## 5. Ficheros a modificar

**Transfer**
- `domain/models/registro_models.py`: `AccionLinea.propuesta_descartada:
  str | None = None` y lo mismo en `AccionVinculado`.
- `application/pipelines/registro_pipeline.py` (`_preflight`): en la normal
  sin elegida con `propuesta_paride` que no `vale(...)`, rellena
  `a.propuesta_descartada = linea.propuesta_cod or f"partida {paride}"`
  antes de proponer. Sin lecturas nuevas.
- `application/pipelines/registro_vinculados.py` (`_partida`): igual cuando
  la guardada con método de `METODOS_PROPUESTA_PROPIA` no `_valida`.

**Api**
- `domain/models.py`: `ResultadoUniverso.partidas: Mapping[int, dict]`
  (`{ide_obra: {ide, cod, res}}`, por defecto vacío); `Obra` y `Linea` ganan
  `postventa_partida_ide/_cod/_res` (`Linea`: `obra_pv_partida_*`).
- `infrastructure/transfer/transfer_client.py` (`universo_postventa`): llena
  `partidas` con `obras[].partida` de la respuesta que ya recibe.
- `application/filtros_maestros.py` (`depurar_obras`) y
  `application/sync_pipeline.py`: la fila de cada obra lleva su partida de
  postventa (o nulas) junto a `admite_postventa`.
- `infrastructure/db/orm_models.py` (`ObraORM`): tres columnas nulables
  (§7); `infrastructure/db/repositories.py`: el upsert de obras las guarda (y
  cuenta el cambio), la desactivación las anula, y `_a_obra`, `_a_linea` y
  los demás constructores de `Linea` las copian.
- `application/propuestas_mes.py`: `_foto` devuelve, de la misma lectura bajo
  el lock, una `Marcas` (frozen: `pendientes`, `no_encontradas`,
  `sub_pendientes`, `sub_no_encontradas`) del periodo; nuevo
  `encolar_marcas(anio, mes, trabajadores) -> (en_curso, Marcas)`, y
  `encolar` queda como envoltorio que devuelve `(en_curso,
  marcas.pendientes)` (firma de hoy). `olvidar_subfilas(periodo_id,
  trabajador, obra, es_postventa)` (R10). `estado()` gana las listas de R6 y
  R9, solo con alguna.
- `application/use_cases.py` (`CambiarPartida`): donde borra la propuesta de
  las subfilas (F-044 R9) llama a un `al_borrar_subfilas` inyectado (el
  `olvidar_subfilas` de la cola, cableado en `interface_adapters/api/deps.py`;
  `None` en los tests de siempre).
- `application/registro_sigrid.py` (`_guardar_propuestas`): la acción o
  subfila con `propuesta_descartada` y sin propuesta nueva → `propuesta_* =
  NULL` donde `partida_ide IS NULL` (R16).
- `interface_adapters/api/schemas.py`: `LineaOut` y `SubfilaOut` ganan
  `propuesta_no_encontrada: bool` (`exclude_if=lambda v: not v`, como F-069);
  `SubfilaOut`, `propuesta_pendiente` igual; `PropuestasOut`, las tres listas
  nuevas con defecto `[]` y fuera si vacías; `a_trabajador_out` gana `marcas:
  Marcas | None = None` (con ella manda sobre `pendientes`) y usa
  `estado_partida`.
- `interface_adapters/api/routes.py` (`_encolar`): usa `encolar_marcas` y pasa
  `marcas` a cada `a_trabajador_out`; la forma de `propuestas_en_curso` no
  cambia.

**Front** (`static/js/app.js`, `static/css/styles.css`)
- `htmlPartida(l)`: las ramas de §3; `construirCelda` y la celda de subfila
  delegan en ella (la rama «automática» desaparece). `.partida-sin` (aviso).
- `aplicarNoEncontradas(lineas, subfilas)` (como `aplicarPendientes`) y las
  marcas de subfila en `consultarPropuestas`, antes de
  `repintarCeldasPartida`.
- `trabajadoresVisibles`: el filtro «Partida» usa `textoCeldaPartida(l)`, el
  texto plano de `htmlPartida` (una sola fuente para celda y filtro, R4).
- `montarSelectorPartida`: rótulo de la opción según `resp.propuesta` (R5).
- `pintarModalPreflight`: `<div class="propuesta-descartada">` en acciones y
  vinculados con `propuesta_descartada` (R15).

**Docs**: `docs/ARCHITECTURE.md#regla-partida` y `#regla-p5` (una línea),
`docs/INTEGRACION.md` §5 (R19).

## 6. Ficheros que NO se tocan

`propuesta_partida.py`, `reglas_porcentajes.py`, `reglas_vinculados.py`,
`partida_matcher.py`, `partida_catalog.py`, `text_match.py` (copias de
`partes`), `universo_postventa.py`, `lecturas_lote.py`, `registro_lote.py`;
los endpoints `partidas/propuesta(-lote)` y `postventa/universo` (su forma no
cambia); la Regla C y sus conflictos; `config.yaml` (sin SQL nuevo);
`partidas_linea.py` (el selector ya guarda lo que propone).

## 7. Esquema (PostgreSQL `dedicacion`, api)

`obra.postventa_partida_ide` (BigInteger), `postventa_partida_cod` y
`postventa_partida_res` (Text): nulables y sin default en `ObraORM`; el
`ADD COLUMN IF NOT EXISTS` lo deriva `esquema.alters_faltantes` al arrancar
(`docs/CONVENTIONS.md` §SQL). Sin DDL a mano, sin SQL contra Sigrid.

## 8. Cuándo se calcula y qué cuesta (topes: `azure-apps/sigrid_api.md` §4.1)

| Momento | Lecturas de Sigrid | Cambio |
|---|---|---|
| Cuadrante, escrituras, `…/propuestas` | 0 (lee PostgreSQL y la memoria) | ninguno |
| Cola en segundo plano (F-055 R29-R31) | por trozo de 10 obras: obras, historial y un presupuesto por obra (F-055 C7) | ninguno; solo R10 reencola las subfilas de una línea: un trozo de una obra |
| Sync (universo de postventa) | la misma llamada de hoy | la api guarda lo que ya recibía y tiraba |
| Preflight | las de F-055 (validación por `ide`) | ninguno: `propuesta_descartada` sale de lo ya leído |

Lejos de los topes: ninguna lectura nueva, filas y tiempos de F-055 (C1-C8).
El historial es el único que crece con los recursos y ya va en una lectura
por lote, con `truncated` como error (F-050 R7).

## 9. Si la propuesta deja de valer antes de registrar (R14-R16)

La guardada no caduca (F-055 D8): vale lo que enseña el cuadrante mientras
sea hoja activa. Si al registrar ya no lo es: el transfer la descarta y
propone de nuevo con la regla (como hoy), marca `propuesta_descartada`, y el
modal lo dice antes de escribir. La api guarda la nueva (F-055 R14) o, sin
ella, borra la vieja: la línea vuelve a pendiente, la cola la recalcula y
acaba en «no encuentra partida» o con la nueva. Nada se escribe sin pasar
por el modal; la Regla C sigue pidiendo confirmar la que va sin partida.

## 10. Riesgos y alternativas descartadas

- **Postventa por la cola** (alternativa de D2): uniforme, pero +2 lecturas
  por trozo con postventa y una propuesta guardada que el registro ignora.
- **Postventa calculada al pedir el cuadrante**: lecturas en cada carga.
- **«sin calcular» marcado por la api** (una memoria de fallos): más estado
  sin ganar nada; el hueco del front lo cubre (§3).
- **La api infiere la descartada** comparando lo enviado con la acción:
  posible, pero la causa la sabe el transfer y la api la deduciría.
- Riesgo: tras desplegar, las postventa dicen «sin calcular» hasta el primer
  sync (MANUAL T14 lo pide). Riesgo: una obra cuyo presupuesto de postventa
  cambia entre dos syncs enseña la partida vieja; el modal enseña la que se
  escribe (F-050 R29), como hoy pasa con `admite_postventa`.
- Riesgo: la memoria es de una réplica (`max 1`, ARCHITECTURE «Topología»);
  tras un reinicio, las no encontradas pasan un rato por «buscando…».
- Orden de despliegue: transfer → api → front (el front tolera la api vieja:
  sin las claves nuevas pinta «sin calcular»; la api tolera el transfer
  viejo: sin `propuesta_descartada`, no borra nada).

## 11. Frontera

**¿Cruza la frontera del proyecto? Sí, solo en lo documentado.** No hay
llamada nueva a otro servicio ni lectura nueva a `sigrid-api`; la base
`dedicacion` (en el servidor compartido `psql-albaranes-rs9k2` al desplegar)
gana tres columnas propias, sin tocar nada del servidor. Cambia el contrato
interno que `azure-apps/dedicacion.md` §5 describe: el cuadrante y las
escrituras (`propuesta_no_encontrada`, subfilas con `propuesta_pendiente`),
`GET …/propuestas` (tres listas), el preflight del transfer
(`propuesta_descartada`) y §2 (columnas de `obra`). El líder lo pone al día en
un commit aparte en `azure-apps` (protocolo de `CLAUDE.md`).

## 12. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Cómo se enseña «no la encuentra» | (a) «no encuentra partida» como aviso en la celda, clic al selector; la Regla C sigue al registrar; (b) además, no deja registrar esas líneas hasta elegir | (a): la Regla C ya pide confirmar; (b) bloquea a quien quiere escribir sin partida | |
| D2 Partida de postventa | (a) la del universo, guardada en el sync: 0 lecturas, necesita un sync tras desplegar; (b) por la cola como las normales: +2 lecturas por trozo | (a) | |
| D3 Reintento de las no encontradas | (a) como hoy: hasta el próximo sync o reinicio, y el preflight vuelve a buscar; (b) reencolarlas al abrir el cuadrante si han pasado N minutos | (a): (b) relee historial y presupuestos en cada carga | |
| D4 Propuesta que deja de valer | (a) aviso en el modal y la api borra la guardada sin sustituta; (b) solo borrarla, sin aviso | (a) | |
| D5 Opción «automática» del selector | (a) renombrarla «sin elegir · usar la propuesta / no encuentra partida»; (b) quitarla (una elegida solo se deshace con Ctrl+Z) | (a) | |
| D6 Motivo del «no encuentra» | (a) sin motivo, texto fijo; (b) con el motivo del transfer (`sin_ci`, empresa…): cambia `propuesta-lote` | (a); (b) como feature aparte si negocio lo pide | |
