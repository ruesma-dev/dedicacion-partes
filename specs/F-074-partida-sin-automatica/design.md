<!-- specs/F-074-partida-sin-automatica/design.md -->
# F-074 · Diseño: la partida, definida antes de registrar

**Rigor: `critico`.** Disparador 2 de «Niveles de rigor» (`CHECKPOINTS.md`):
la partida definida es la que el transfer **escribe en Sigrid de producción**
(`hmores.paride`, `registro_pipeline._preflight`); F-074 cambia de dónde sale.

**Enfoque (humano, 2026-11-23).** La regla de la propuesta corre **solo en
segundo plano** (cola, selector, universo del sync); el cuadrante enseña su
resultado y el registro **escribe eso**, sin volver a casar. Lo que se ve es
lo que se registra por construcción, no por coincidencia de dos cálculos.

## 1. Servicios y límite

| Servicio | Qué cambia | Por qué ahí |
|---|---|---|
| transfer | el preflight deja de proponer y casar (R1-R7); motivos en la propuesta y el universo (R9-R10); `partida_no_valida` | la regla y la validación por `ide` viven aquí |
| api | partida de postventa del sync y al registro (R11-R12); estados y motivos (R13-R14); memoria (R15); borrar la guardada que no vale (R16) | dueña del dato, la cola y la memoria |
| front | textos, filtro, selector y modal (R17-R22) | solo pinta |

La regla no se copia ni se mueve: sigue en `propuesta_partida.py`,
`reglas_vinculados.py` y `universo_postventa.py`. Ninguna responsabilidad
nueva fuera de los tres servicios; ninguna copia nueva entre servicios.

## 2. Diagnóstico: cuándo queda hoy «automática»

| # | Caso | Hoy | Con F-074 (celda → registro) |
|---|---|---|---|
| a | Obra normal, la regla no da partida | memoria F-055 R32, sin marca; el preflight vuelve a proponer y acaba en «sin partida» | «no encuentra partida» + motivo → conflicto «sin partida» (D8) |
| b | Su obra vuelve `{ok: false}` | igual que a; el registro la omite por empresa | igual, motivo = el error |
| c | El transfer no responde (F-055 R33) | «automática»; el preflight propone | «sin calcular» → sin partida definida (D7) |
| d | Postventa | nunca se encola; el preflight casa por obra | la del universo, «obra de postventa» → se escribe esa |
| e | Subfila en la cola | sin marca (F-057 es de líneas) | «buscando partida…» → sin definida (D7) |
| f | Subfila sin propuesta | memoria de subfilas, sin marca | «no encuentra partida» + motivo |
| g | Subfila en memoria cuyo titular gana partida | no se reencola hasta el sync | sale de la memoria y se recalcula (R15) |
| h | Periodo no ABIERTO | «automática» | «—» |
| i | Guardada que deja de valer | sigue enseñándola; el preflight propone otra | se omite nombrándola; la api la borra y la cola la recalcula (D4) |

Sin cambio: elegida, fija VAR (y sus subfilas) y guardada que vale.

## 3. La partida al registrar y los estados de la celda

**Línea** (`_preflight`): VAR → su fija (`partida_var_de`, como hoy);
elegida → validada (R20 de F-050 si no vale); si no, `propuesta_paride`
(también la de postventa) → validada; si no vale, omitida con
`partida_no_valida`; sin ninguna, sin partida (R5). **Subfila**
(`PasoVinculados._partida`): elegida; con titular de postventa, VAR o no
`CI*`, la del titular (derivación, no búsqueda: no lee); guardada de método
propio; si no, sin partida. Una guardada de método `titular` no se usa: o va
con el titular o no tiene definida.

**Celda** (R17), en este orden: elegida → fija → propuesta (guardada o de
postventa) → «buscando partida…» → «no encuentra partida» + motivo → ABIERTO
«sin calcular» → «—». Pendiente y no encontrada son excluyentes (`_lanzar` no
encola lo que está en memoria). «sin calcular» no lo marca la api: es el
hueco (caso c, postventa sin sync).

## 4. Ficheros a crear

- `services/dedicacion-api/application/estado_partida.py`: puras
  `estado_de_linea(ln, marcas)` y `estado_de_subfila(ln, v, marcas)` (claves
  `propuesta_*`, `propuesta_pendiente`, `propuesta_no_encontrada`,
  `propuesta_motivo`, solo con valor).
- `services/dedicacion-transfer/application/services/partida_definida.py`:
  pura `partida_definida_del_vinculado(titular, elegida, elegida_valida,
  guardada, guardada_valida)`; la línea se decide en `_preflight` (§5).
- Tests: transfer `test_f074_preflight_definida.py`, `test_f074_motivos.py`;
  api `test_f074_estados.py`, `test_f074_postventa.py`,
  `test_f074_memoria_subfilas.py`, `test_f074_no_valida_api.py`; front
  `test_f074_celda.py`, `test_f074_selector_modal.py`.

## 5. Ficheros a modificar

**Transfer**
- `domain/models/registro_models.py`: `partida_no_valida: str | None = None`
  en `AccionLinea` y `AccionVinculado`.
- `application/pipelines/registro_pipeline.py`: `_preflight` sin
  `por_proponer`, `nodos_origen`, `_historial` ni `proponer_partida`; el
  destino de postventa sigue (`obra_por_codigo`), sin cargar su presupuesto:
  elegida y guardada de postventa se validan en `_validas` contra la obra de
  postventa; `ReglasPorcentajes` recibe la partida de cada línea de
  postventa en vez de la global. `proponer` (endpoint) gana `motivos`.
- `application/pipelines/registro_vinculados.py`: `decidir` deja de leer
  historial, cuentas y presupuesto y usa `partida_definida_del_vinculado`;
  `proponer` gana `motivos_vinculados` (el motivo que hoy calcula
  `partida_del_vinculado` y tira).
- `application/services/reglas_porcentajes.py`: P5 con la partida de la
  línea (sin ella, omitida con su motivo).
- `application/services/lecturas_lote.py` (`precargar`): fuera
  `presupuestos` de origen y de postventa, `_ventanas` del historial; las
  guardadas de postventa entran en `_cargar_validas`. `precargar_propuestas`,
  sin cambio.
- `application/services/universo_postventa.py` (`calcular`): `motivos`.
- `application/services/propuesta_partida.py`: `motivo_sin_propuesta(nodos)`
  (sin hojas activas o «ningún paso da partida»), sin tocar la regla.
- `interface_adapters/api/app.py`: las salidas de R9-R10.

**Api**
- `domain/models.py`: `ResultadoUniverso.partidas` y `.motivos`; `Obra` y
  `Linea` ganan `postventa_partida_ide/_cod/_res/_motivo` (`Linea`:
  `obra_pv_*`).
- `infrastructure/transfer/transfer_client.py`, `application/filtros_maestros.py`
  (`depurar_obras`), `application/sync_pipeline.py`: la partida y el motivo
  de cada obra junto a `admite_postventa`.
- `infrastructure/db/orm_models.py` (§7) y `repositories.py`: upsert,
  desactivación (las anula) y constructores de `Obra`/`Linea`.
- `application/registro_sigrid.py`: `_payloads` manda la de postventa como
  `propuesta_*` (método `postventa`); `_guardar_propuestas` se sustituye por
  el borrado de R16.
- `application/propuestas_mes.py`: memorias con motivo (`dict` clave →
  motivo); `_foto` → `Marcas` (pendientes, no encontradas con motivo, y lo
  mismo de subfilas) de la misma lectura; `encolar_marcas`; `encolar` como
  envoltorio de hoy; `olvidar_subfilas` (R15); `estado()` con las listas.
- `application/use_cases.py` (`CambiarPartida`): llama a un
  `al_borrar_subfilas` inyectado (cableado en `interface_adapters/api/deps.py`).
- `interface_adapters/api/schemas.py` y `routes.py`: `LineaOut`/`SubfilaOut`
  con las claves nuevas (`exclude_if`, como F-069), `PropuestasOut` con las
  listas (fuera si vacías), `a_trabajador_out(marcas=…)`.

**Front** (`app.js`, `styles.css`): `htmlPartida` con §3 y una
`textoCeldaPartida` para el filtro; celda de línea y subfila delegan en ella;
`aplicarNoEncontradas` y marcas de subfila en `consultarPropuestas`; rótulo
de la opción del selector; selector en la omitida por `partida_no_valida`.

**Docs**: `ARCHITECTURE.md` (R24), `INTEGRACION.md` §5.

## 6. Ficheros que NO se tocan

La regla: `proponer_partida`, `previa_en_obra`, `resolver_normal`,
`partida_del_vinculado`, `casar_postventa`; `partida_matcher.py`,
`partida_catalog.py`, `text_match.py`, `cuenta_analitica.py`,
`estado_parte.py` (copias); `partidas_linea.py` (el selector); la regla VAR
(`universo_var.py`, `partida_var_de`); `config.yaml` (sin SQL nuevo); cuenta
analítica, partes, pisados, sobrecarga, idempotencia y rachas.

## 7. Esquema (PostgreSQL `dedicacion`, api)

`obra.postventa_partida_ide` (BigInteger), `_cod`, `_res` y
`postventa_motivo` (Text): nulables, sin default, en `ObraORM`; el `ADD
COLUMN` lo deriva `esquema.alters_faltantes`. Sin DDL a mano.

## 8. Cuándo se calcula y qué cuesta (topes: `azure-apps/sigrid_api.md` §4.1)

Cuadrante y escrituras: 0 lecturas de Sigrid. Cola y selector: lo de F-055
(C7), más un trozo de una obra por R15. Sync: la misma llamada al universo.
**Preflight, lo que deja de leer** (contado del código, `lecturas_lote.py` y
`_preflight`):

| Caso del lote | Hoy | Con F-074 |
|---|---|---|
| Líneas normales con guardada válida | `validar_partidas` | igual (0 de ahorro) |
| Obras con alguna pendiente | + 1 presupuesto por obra + 1 historial (24 meses, la más pesada) | 0 |
| Alguna línea de postventa | + presupuesto de la obra de postventa | 0 (sigue la obra por código) |
| Subfilas sin guardada propia | + historial de vinculados y cuentas por obra (y presupuesto) | 0 |
| Guardada que no vale | + presupuesto e historial perezosos | 0 |
| VAR | catálogo VAR | igual |

Hoy, con la cola al día, el ahorro es poco (1 lectura por lote con
postventa); en el peor caso (mes recién abierto, tras un sync o con el
transfer caído), N + 1 (+1) (+2 por obra con vinculados). **C1** (test): un
lote de 10 obras sin ninguna partida definida no lee presupuesto, historial
ni cuentas. **C2** (test): uno con postventa lee la obra de postventa y no su
presupuesto. **Medición real**: MANUAL M2 (`medir`, antes y después).

## 9. Si la definida deja de valer antes de registrar

La guardada no caduca (F-055 D8). Si al registrar ya no es hoja activa, el
transfer la omite nombrándola (`partida_no_valida`) y no busca otra; el modal
ofrece el selector; la api borra la guardada (no la elegida) y la cola la
recalcula: acaba en una nueva o en «no encuentra partida». Nada se escribe en
una partida no válida ni en una que nadie vio.

## 10. Riesgos y alternativas descartadas

- **Seguir proponiendo en el preflight como red** (lo de hoy): descartado
  por el humano; dos cálculos pueden divergir y cuesta lecturas.
- **Postventa por la cola** (D2 b): +2 lecturas por trozo.
- Riesgo: tras desplegar, **las de postventa no se registran** hasta el
  primer sync (sin definida → omitidas). Orden obligatorio: **api → sync →
  transfer → front** (la api nueva manda la de postventa, que el transfer
  viejo ignora; el transfer nuevo ya la encuentra). T18 lo fija.
- Riesgo: una línea guardada en el editor justo antes de registrar puede
  estar aún «buscando…»: sale sin definida (D7); se repite el preflight al
  acabar la cola.
- Riesgo: presupuesto de postventa que cambia entre dos syncs: se omite por
  R4 con el motivo, hasta el siguiente sync.
- Riesgo: memoria de una réplica (`max 1`): tras un reinicio, las no
  encontradas pasan por «buscando…».
- Compatibilidad: sin `motivos`, la api publica el motivo nulo; sin
  `partida_no_valida`, no borra; sin las claves nuevas, el front pinta «sin
  calcular».

## 11. Frontera

**¿Cruza la frontera del proyecto? Sí, solo en lo documentado.** Ninguna
llamada nueva a otro servicio y menos lecturas a `sigrid-api`. La base
`dedicacion` (servidor compartido `psql-albaranes-rs9k2` al desplegar) gana
cuatro columnas propias, sin tocar el servidor. Cambian contratos que
`azure-apps/dedicacion.md` describe: §5 (preflight sin propuesta y con
`partida_no_valida`; `partidas/propuesta(-lote)` y `postventa/universo` con
motivos; cuadrante, escrituras y `…/propuestas` con las claves y listas
nuevas), §2 (columnas de `obra`), §4 (menos lecturas) y §7 (postventa sin
sync no se registra; orden de despliegue). El líder lo actualiza en un commit
aparte en `azure-apps` (protocolo de `CLAUDE.md`).

## 12. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Cómo se enseña «no la encuentra» | (a) aviso en la celda con el motivo y clic al selector; (b) además, un aviso en la cabecera del mes | (a) | |
| D2 Partida de postventa | (a) la del universo, guardada en el sync y mandada al registro: 0 lecturas, exige sync tras desplegar; (b) por la cola: +2 lecturas por trozo | (a) | |
| D3 Reintento de las no encontradas | (a) como hoy: tras el sync o un reinicio; abrir el selector ya la recalcula; (b) reencolarlas al abrir el cuadrante cada N min | (a): el registro ya no las busca, pero (b) relee historial y presupuestos en cada carga | |
| D4 La definida que ya no vale al registrar | (a) omitida con motivo y selector; la api borra la guardada y la cola la recalcula; (b) tratarla como sin partida (D7-D8) | (a): nunca escribe donde no vale y no confunde «no vale» con «no hay» | |
| D5 Opción «automática» del selector | (a) «sin elegir · usar la propuesta / no encuentra partida»; (b) quitarla | (a) | |
| D6 Motivo del «no encuentra» | (a) texto fijo; (b) el motivo del transfer, en esta feature | (b) | (b), humano 2026-11-23 |
| D7 Registrar con líneas sin definida («buscando…», «sin calcular», «no encuentra») | (a) esa línea o subfila no se escribe; el modal la lista con el selector y el resto se registra; (b) no deja registrar nada hasta que todas la tengan; (c) bloquea solo a ese trabajador | (a): «que se ponga» se cumple en el mismo modal sin parar a los demás | |
| D8 Qué queda de la Regla C | (a) el conflicto «sin partida» se queda, con su casilla para escribirla con `paride = 0`, ahora para la línea sin definida; (b) desaparece la casilla: sin definida nunca se escribe | (a): única salida si el presupuesto no tiene una partida que sirva; es explícita y por línea. (b) si negocio no quiere partes sin partida | |
