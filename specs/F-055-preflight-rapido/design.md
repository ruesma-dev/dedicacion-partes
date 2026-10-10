<!-- specs/F-055-preflight-rapido/design.md -->
# F-055 · Diseño

**D1-D8: ABIERTAS** (§11, recomendada A en todas). Rigor `critico`. Se
implementa sobre `dev` con F-050 fusionada (incluida T15c: repreflight de la
obra de la línea), rebasando esta rama.

## 1. Límite de servicio

- **Transfer** (lee Sigrid y decide): validación por `ide`, propuesta (como
  hoy, F-050 §1), lote agrupado y paralelo. Ninguna escritura nueva.
- **Api** (dueña del cuadrante): guarda la propuesta en `asignacion` (dato
  del cuadrante, como la elegida), la manda al registrar y pide el preflight
  en lote. No propone ni valida.
- **Front**: pinta la propuesta guardada (R27). Nada más.
- Nada es de otro microservicio. `sigrid-api` recibe **menos** peticiones
  pero hasta 4 a la vez (D5): `azure-apps/sigrid_api.md` §3.4 no documenta
  un tope de concurrencia (Flex Consumption, SQL on-premise compartido);
  por eso es ajustable y 1 vuelve al serie de hoy.

## 2. Lecturas de hoy por obra (`registro_pipeline.py`) y qué pasa con ellas

| Lectura (método) | Cuándo, hoy | ¿Imprescindible al registrar? | Tras F-055 |
|---|---|---|---|
| `obra_por_ide`/`_por_codigo` | siempre | sí: empresa, centro, destino | agrupada (`obras_por_ide`) |
| `obra_por_codigo(0404)` | modo pruebas | sí: destino | 1 por lote |
| `obra_por_codigo(POSTV2)` + su presupuesto | hay postventa | sí: casado P5 | 1 por lote |
| `obra_por_codigo(VAR)` + su presupuesto | hay VAR | sí: `#regla-var` | 1 por lote |
| `horas_de_recursos` | siempre | sí: P1, hora, subcuenta | agrupada |
| `capitulos_de_obra(origen)` | manual (R20), automática y F-049 d | **solo** automáticas sin propuesta | sale: `validar_partidas` |
| `historial_partidas` | automáticas | **solo** automáticas sin propuesta | 1 por lote, si hace falta |
| `partidas_de_lineas` | recurso sin subcuenta | sí: cuenta F-037 | agrupada |
| `cuentas_de_centro` | por centro destino | sí: cuenta F-037 | por centro, en paralelo |
| `partes_del_periodo` | por destino y mes | sí: parte, estado, cerrados | agrupada |
| `siguiente_cod_pt` | parte nuevo | sí (código del preview) | 1 por lote |
| `lineas_por_synckey` | siempre | sí: idempotencia | agrupada |
| `lineas_del_parte` | por parte del periodo | sí: pisado, sobrecarga, cerrado | agrupada |

Una obra con partidas elegidas hace hoy **8-9 lecturas en serie** (10 en
pruebas con parte nuevo); con 4-6 s cada una (M1 de F-050), 35-50 s por obra
y la api las encadena obra a obra. La latencia por llamada pesa más que el
volumen: lo que más rinde es **no leer** (presupuesto, historial) y
**agrupar** (N obras → 1 lectura por tipo) con **rondas en paralelo**:

- Ronda A (en paralelo): `obras_por_ide`, obras por código (pruebas,
  postventa, VAR), `horas_de_recursos`, `lineas_por_synckey`,
  `validar_partidas`, `partidas_de_lineas` y, si hay automáticas sin
  propuesta, `historial_partidas`.
- Ronda B: `partes_de_periodos` de todos los destinos y presupuestos de
  postventa, VAR y obras con automáticas sin propuesta.
- Ronda C: `lineas_de_partes` de todos los partes leídos.
- Decisiones por obra en paralelo; lo no precargado (`cuentas_de_centro`,
  `siguiente_cod_pt`) va a `sigrid-api` con memoria de un solo vuelo.

`cuentas_de_centro` no se agrupa: su filtro por subcuenta lo hace SQL Server
con su collation y repetirlo en memoria no es exacto (§10).

## 3. Ficheros a crear

- transfer `application/services/lecturas_lote.py`
- transfer `application/pipelines/registro_lote.py`
- Tests `test_f055_*.py` en `tests/` de transfer, api y front (§7).

## 4. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `infrastructure/sigrid/sigrid_write_client.py` | tiempo y log en `_read` (R1); `validar_partidas`, `obras_por_ide`, `partes_de_periodos`, `lineas_de_partes`; `horas_de_recursos` en trozos de 500 |
| transfer `domain/models/registro_models.py` | `LineaEntrada.propuesta_*` (5), `AccionLinea.partida_res` |
| transfer `application/pipelines/registro_pipeline.py` | rama manual con `validar_partidas`; rama de propuesta guardada; `partida_res`; sin la lectura forzada de F-049 d; log de resumen |
| transfer `interface_adapters/api/app.py` | `LineaIn.propuesta_*`, `LoteIn`, `def preflight_lote` |
| transfer `config/settings.py` | `sigrid_lecturas_paralelas` (`SIGRID_LECTURAS_PARALELAS`, 4, 1-8) |
| transfer `prueba_escritura_porcentajes.py` | fase `medir` (R2) |
| api `infrastructure/db/orm_models.py` | `AsignacionORM.propuesta_*` (R13) |
| api `domain/models.py` | `Linea.propuesta_ide/cod/res/metodo/origen` (None, al final) |
| api `infrastructure/db/repositories.py` | `_a_linea`/`reemplazar` con propuesta; `guardar_propuesta` |
| api `domain/ports.py` | `AsignacionRepository.guardar_propuesta` |
| api `application/use_cases.py` | `_conservar_partidas` conserva también la propuesta (R17) |
| api `application/registro_sigrid.py` | payload con propuesta (R16); preflight por lote (R26); `_guardar_propuestas` (R14) |
| api `application/partidas_linea.py` | guarda la propuesta devuelta (R15) |
| api `infrastructure/transfer/transfer_client.py` | `preflight_lote(peticiones)` |
| api `interface_adapters/api/schemas.py` | `LineaOut.propuesta_cod/res/metodo` (R27) |
| front `static/js/app.js`, `static/css/styles.css` | celda Partida con la propuesta (R27) |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`, READMEs de api y transfer | §8 |

## 5. Clases y funciones

### 5.1 Transfer · cliente (infrastructure)

- `validar_partidas(parides) -> dict[int, PartidaValida]`
  (`PartidaValida(ide, obride, cod, res, es_hoja, activa)`), SQL §6.
- `obras_por_ide(ides) -> dict[int, ObraEntrada | None]`: agrupa por `ide`
  y aplica el mismo `_obra` a las filas de cada uno.
- `partes_de_periodos(obrides, periodos) -> dict[(obride, ano, mes),
  list[ParteSigrid]]`: mismo SQL que `partes_del_periodo` con `IN`, mismo
  orden (`ide` descendente) por clave.
- `lineas_de_partes(hmoides, resides) -> dict[hmoide, list[LineaSigrid]]`:
  mismo SQL que `lineas_del_parte` con `IN`, por `pos` dentro de cada parte.
- `_read(sql, params, nombre=…)`: mide y loguea (R1); el contrato no cambia.

### 5.2 Transfer · `lecturas_lote.py` (application)

- `LecturasDelLote(cliente, limite)`: implementa los métodos de lectura que
  usa el pipeline. Cada uno responde de lo precargado **solo si la consulta
  está entera dentro** (p. ej. `horas_de_recursos(ides)` con `ides` ⊆
  precargados: el subconjunto, en el orden del SQL); si no, llama al
  cliente real y apunta un `fallo_de_memoria` (log + contador para tests).
  Memoria de un solo vuelo por clave (`threading.Lock` + `Future`): dos
  hilos que piden lo mismo esperan la misma lectura (y la misma excepción).
  `escribir` lanza `RuntimeError`: un lote nunca escribe.
- `precargar(peticiones)`: rondas A, B y C de §2 con
  `ThreadPoolExecutor(max_workers=limite)`; la primera excepción de una
  ronda sube (R24).
- Vive solo dentro de una petición HTTP (R22, D4 = A): no hay estado global.

### 5.3 Transfer · pipeline y lote

- `RegistroPipeline.preflight` (rama `paride` de obra normal):
  `self._validas(lineas)` lee una vez `validar_partidas` de todos los
  `paride` y `propuesta_paride` de la petición; vale si `obride ==
  origen.ide and es_hoja and activa` (R4); si no, R5 tal cual.
- Rama nueva antes de la automática: con `propuesta_paride` válida, `paride`,
  `partida_cod`, `partida_res`, `partida_metodo`, `partida_origen` de la
  línea (R8); si no vale, cae a la automática (R6).
- El presupuesto de origen se lee **solo** en la automática sin propuesta;
  `partidas_obra` es su catálogo o `[]` (R10). Postventa y VAR, sin cambios.
- `RegistroLote(cliente, settings).preflight(peticiones) -> list[Preflight |
  Exception]`: `precargar`, luego un `RegistroPipeline(cliente=memoria,
  settings)` por obra en el pool. El pipeline no tiene estado entre llamadas
  (F-025 R9): compartirlo entre hilos es seguro; un test lo fija.
- `ejecutar` no cambia de forma: preflight con el cliente real y escritura;
  gana R3-R9 por ser el mismo `preflight`.
- Endpoint `def preflight_lote(p: LoteIn)` (R25): cada entrada, la forma de
  `preflight` (función común `_respuesta_preflight(pf)` extraída de la ruta
  de hoy, sin cambiar su salida) o `{ok: false, error}`; la excepción de una
  ronda compartida → 502 del lote entero.

### 5.4 Api

- `_payloads`: tras `paride`/elegida, si no hay elegida y
  `a.propuesta_ide`, añade los cinco `propuesta_*` (R16).
- `preflight`: una llamada `transfer.preflight_lote([{**p, "pisar_claves":
  []} …])`; `resultados` se arma igual que hoy (obra + respuesta). Después
  `_guardar_propuestas(resultados)`: por acción con método de propuesta y
  `registro_id`, `UPDATE asignacion SET propuesta_* … WHERE id = :rid AND
  partida_ide IS NULL` (ORM, como `_trazar`) (R14).
- `PartidasDeLinea.ejecutar`: si `r["propuestas"]["linea"]`, llama a
  `uow.asignaciones.guardar_propuesta(periodo_id, trabajador_ide, clave,
  propuesta)` y `uow.commit()` (R15). La ruta sigue siendo `GET`: el efecto
  es una caché del cuadrante, sin evento (D2).
- `_conservar_partidas` copia también `propuesta_*` de la línea de antes;
  `_snapshot` y `_validar_lineas` **no** las llevan (R17).

### 5.5 Front

- `textoPartida`/`construirCelda` (`partida`): sin elegida y con
  `linea.propuesta_cod`, `<em>` con «código · descripción» y el rótulo de
  `rotuloOrigen(propuesta_metodo)`; si no, «automática» (R27).

## 6. SQL

**PostgreSQL** (`dedicacion`, `public`): solo ORM; `esquema.py` deriva
`ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS propuesta_ide BIGINT` (y
`propuesta_cod`, `_res`, `_metodo`, `_origen TEXT`). Sin `NN_*.sql`.

**Sigrid** (lecturas parametrizadas, en el cliente del transfer):

```sql
-- validar_partidas
SELECT p.ide, p.obride, p.cod, p.res, ISNULL(p.tipdes,0) AS tipdes,
       CASE WHEN EXISTS (SELECT 1 FROM obrparpar h WHERE h.padide = p.ide
                         AND h.obride = p.obride) THEN 0 ELSE 1 END AS hoja
FROM obrparpar p WHERE p.ide IN (?…)
```

`obras_por_ide`, `partes_de_periodos` y `lineas_de_partes`: el SQL de su
método suelto con `= ?` → `IN (?…)` y el `obride`/`hmoide` en la salida.
Equivalencia de `hoja`: `build_arbol_partidas` marca capítulo al nodo con un
hijo **de la misma obra** (`padide` en `nodos`); el `EXISTS` filtra por
`obride` igual. `activa` = `tipdes = 0`, como allí.

## 7. Tests y dobles

- Transfer: `validar_partidas` con `_read` falso (SQL, trozos) y su
  **equivalencia** con `construir_catalogo` en hoja activa, capítulo, baja,
  otra obra e inexistente (R4); pipeline con `ClienteFalso` (R3, R5-R10);
  `LecturasDelLote`: subconjuntos, fallo de memoria al cliente real, un solo
  vuelo con dos hilos, `escribir` prohibido, R24; **equivalencia del lote**:
  cada escenario de `test_f037_pipeline`, `test_f050_pipeline`,
  `test_f002_pipeline` y `test_f039_preflight_var`, suelto y en lote, da el
  mismo `asdict(Preflight)` (R21); conteo de lecturas C1-C2 con un
  `ClienteFalso` que cuenta; límite 1 = serie; ajuste fuera de 1-8 (R23);
  endpoint con `TestClient` (R19, R24, R25); fase `medir` sin escrituras.
- Api: `_Uow` de F-024/F-050 ampliado dentro de `test_f055_*` (R13-R18,
  R26); rutas con transfer falso (R15, R27).
- Front: node sobre la celda (R27) como `test_f050_*`.
- Lista cerrada de tests anteriores: requirements §7.

## 8. Documentación (R28)

`ARCHITECTURE.md`: `#regla-partida` (propuesta guardada, validación por
`ide`, cuándo se recalcula), «Acceso a datos» (lote y paralelo), «Timeouts
encadenados» (nota). `INTEGRACION.md`: R19, `SIGRID_LECTURAS_PARALELAS`,
columnas `propuesta_*`, orden de despliegue **transfer → api → front**.

## 9. Ficheros que NO se tocan

Copias cerradas de `partes` (`partida_matcher`, `partida_catalog`,
`text_match`, `cuenta_analitica`, `estado_parte`), `reglas_porcentajes`,
`propuesta_partida`, `universo_*`, `excel/*`, `sync_pipeline`, `.env`,
`infra/`, el `ejecutar` de la api.

## 10. Riesgos

- **Equivalencia del lote**: un dato servido de memoria distinto del real
  cambiaría lo que se escribe. Mitigación: solo se sirve una consulta
  contenida en la precargada, con el mismo SQL y orden; el resto va a
  Sigrid; test de equivalencia sobre todos los escenarios; mutación completa.
- **Propuesta guardada vieja** (D8): se escribe lo que el cuadrante enseña
  (R27); un parte nuevo en Sigrid no la cambia hasta abrir el selector.
- **Concurrencia en `sigrid-api` y el SQL compartido** (D5): tope 4,
  ajustable; T16 mide.
- **`ejecutar` del mes entero** sigue en serie por obra (D6): ya sin
  presupuesto ni historial, pero con N obras puede pasar de 120 s en local.
  T16 lo mide; si pasa, se propone feature aparte (no se cambia aquí).
- **Despliegue**: la api nueva sin el transfer nuevo da 404 en el lote →
  orden transfer → api → front.
- Una automática sin propuesta posible (sin partida) se recalcula en cada
  preflight: es la excepción, no el caso.

## 11. Decisiones ABIERTAS (las decide el humano)

| D | Recomendada (A) | Alternativas | Efecto en tests |
|---|---|---|---|
| D1 · Automática sin propuesta guardada al registrar | Camino de hoy solo para ella (presupuesto + historial, una vez por lote) y la api la guarda | B la api pide antes las propuestas al transfer y luego preflight ligero; C omitir «elige partida» (cambia una regla) | A: los `test_f050_r9_*` no cambian; C: cambian `test_f050_r9_*` y `test_f013_*` |
| D2 · Dónde y cuándo se guarda la propuesta | `asignacion.propuesta_*`; al volver de un preflight y al abrir el selector. **Cambia D3 de F-050** (se guardaba solo la elegida) | B A + en segundo plano al guardar la fila (al añadir la obra); C en el sync o al abrir el mes, en lote | A: `test_f003_r8`, `_Uow` de `test_f050_rutas_partida`; B suma tests de tarea en segundo plano |
| D3 · Validar la partida al registrar | Por `ide` (`validar_partidas`): elegida que no vale → omitir (R20 F-050); propuesta que no vale → recalcular | B no validar (confiar en el cuadrante); C presupuesto entero (hoy) | A: R20 de F-050 sin cambiar aserciones (el doble gana el método) |
| D4 · Caché del transfer entre peticiones | No: memoria solo de la petición | B TTL 120 s de presupuestos y catálogos de postventa/VAR en preflight y selector, `ejecutar` sin ella; C solo en el selector | A: ninguno; B: tests de caducidad y de que `ejecutar` la salta |
| D5 · Agrupar y paralelizar | Agrupar por tipo + 4 a la vez (`SIGRID_LECTURAS_PARALELAS`, 1-8) | B solo paralelo por obra (N veces más peticiones); C solo agrupar, en serie | C1 vale en A y C; en B cambia el conteo |
| D6 · Qué servicio hace qué | Lote en el transfer (R19), la api lo llama una vez; `ejecutar` por obra y en serie (el alta de partes usa el correlativo `PT` de la empresa) | B la api lanza en paralelo los preflight por obra (sin ruta nueva); C también `ejecutar` en lote | A: dobles de transfer de la api ganan `preflight_lote` |
| D7 · La celda enseña la propuesta guardada | Sí, en cursiva con su método | B no («automática» como hoy) | A: `CAMPOS_LINEA` de `test_f034_rutas` |
| D8 · Caducidad de la propuesta guardada | No caduca; se reescribe al abrir el selector y si deja de valer | B se recalcula si se guardó otro día; C botón «Recalcular propuestas» del mes | A: ninguno; B: test de fecha (`propuesta_at_utc`) |
