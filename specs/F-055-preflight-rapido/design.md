<!-- specs/F-055-preflight-rapido/design.md -->
# F-055 · Diseño

**D1-D8: DECIDIDAS por el humano el 2026-10-13** (§11: A en todas salvo
**D2 = A + C**). Rigor `critico`. Se implementa sobre `dev` con F-050
fusionada (incluida T15c), rebasando esta rama.

## 1. Límite de servicio

- **Transfer** (lee Sigrid y decide): validación por `ide`, propuesta (la de
  F-050, mismos pasos), lotes agrupados y en paralelo. Sin escrituras nuevas.
- **Api** (dueña del cuadrante): guarda la propuesta en `asignacion` (dato
  del cuadrante, como la elegida), la manda al registrar, pide el preflight
  en lote y **lanza y guarda** el cálculo del mes en segundo plano (R29-R33).
  No propone ni valida: decide solo **qué líneas** pide y si la guarda.
- **Front**: pinta la propuesta (R27) y consulta R35 (R36). No decide.
- Nada es de otro microservicio. `sigrid-api` recibe **menos** peticiones
  pero hasta 4 a la vez (D5; `azure-apps/sigrid_api.md` §3.4 no documenta
  tope de concurrencia): ajustable, y 1 vuelve al serie de hoy.

## 2. Lecturas del preflight por obra (`registro_pipeline.py`)

| Lectura (método) | Hoy | Tras F-055 |
|---|---|---|
| `obra_por_ide`/`_por_codigo` | siempre | agrupada (`obras_por_ide`) |
| `obra_por_codigo` de 0404 / POSTV2 / VAR (+ presupuesto) | modo pruebas / postventa / VAR | 1 por lote |
| `horas_de_recursos` | siempre | agrupada |
| `capitulos_de_obra(origen)` | manual (R20), automática, F-049 d | **solo** pendientes; el resto, `validar_partidas` |
| `historial_partidas` | automáticas | 1 por lote, solo si hay pendientes |
| `partidas_de_lineas` | recurso sin subcuenta | agrupada |
| `cuentas_de_centro` | por centro destino | por centro, en paralelo |
| `partes_del_periodo` | por destino y mes | agrupada |
| `siguiente_cod_pt` | parte nuevo | 1 por lote |
| `lineas_por_synckey` / `lineas_del_parte` | siempre / por parte | agrupadas |

Hoy, 8-9 lecturas en serie por obra a 4-6 s (M1 de F-050): 35-50 s por
obra, encadenadas. Pesa la latencia, no el volumen: **no leer**, **agrupar**
y **rondas en paralelo**. A: obras (por `ide` y por código), horas,
`synckey`, `validar_partidas`, `partidas_de_lineas` e historial si hay
pendientes. B: `partes_de_periodos` y presupuestos de postventa, VAR y obras
con pendientes. C: `lineas_de_partes`. Luego decisiones por obra en
paralelo; `cuentas_de_centro` (su filtro por subcuenta usa la collation de
SQL Server) y `siguiente_cod_pt` van a `sigrid-api` con un solo vuelo.

### 2.1 Propuestas del mes (R34) y coste esperado

A: `obras_por_ide` e `historial_partidas` de **todos** los recursos (misma
ventana). B: `capitulos_de_obra` de cada obra, hasta el límite a la vez.
Luego `proponer` por obra con la memoria. Con lo medido (obra 4-6 s,
historial 0,8-5,7 s, presupuesto 3,3-5,3 s), un trozo de 10 obras: A ≈ 6 s
+ B 3 rondas ≈ 16 s ≈ **22 s** (lejos de los 180 s de `TRANSFER_TIMEOUT_S`).
Un mes con 40 obras pendientes, ≈ 90 s en segundo plano, de 10 en 10 (C8);
después, solo las líneas nuevas (0-1 trozos). Hoy, selector a selector.

## 3. Ficheros a crear

- transfer `application/services/lecturas_lote.py`,
  `application/pipelines/registro_lote.py`
- api `application/propuestas_mes.py`
- Tests `test_f055_*.py` en `tests/` de transfer, api y front (§7).

## 4. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `infrastructure/sigrid/sigrid_write_client.py` | tiempo y log en `_read` (R1); `validar_partidas`, `obras_por_ide`, `partes_de_periodos`, `lineas_de_partes`; `horas_de_recursos` en trozos de 500 |
| transfer `domain/models/registro_models.py` | `LineaEntrada.propuesta_*` (5), `AccionLinea.partida_res` |
| transfer `application/pipelines/registro_pipeline.py` | rama manual con `validar_partidas`; rama de propuesta guardada; `partida_res`; sin la lectura forzada de F-049 d; log de resumen |
| transfer `interface_adapters/api/app.py` | `LineaIn.propuesta_*`, `LoteIn`, `PropuestaLoteIn`, `def preflight_lote`, `def propuesta_lote` |
| transfer `config/settings.py` | `sigrid_lecturas_paralelas` (`SIGRID_LECTURAS_PARALELAS`, 4, 1-8) |
| transfer `prueba_escritura_porcentajes.py` | fase `medir` (R2) |
| api `infrastructure/db/orm_models.py` | `AsignacionORM.propuesta_*` (R13) |
| api `domain/models.py` | `Linea.propuesta_ide/cod/res/metodo/origen` (None, al final) |
| api `infrastructure/db/repositories.py`, `domain/ports.py` | `_a_linea`/`reemplazar` con propuesta; `guardar_propuesta(…, solo_si_vacia=False)` |
| api `application/use_cases.py` | `_conservar_partidas` conserva también la propuesta (R17) |
| api `application/registro_sigrid.py` | payload con propuesta (R16); preflight por lote (R26); `_guardar_propuestas` (R14) |
| api `application/partidas_linea.py` | guarda la propuesta devuelta (R15) |
| api `infrastructure/transfer/transfer_client.py` | `preflight_lote(peticiones)`, `propuesta_lote(peticiones)` |
| api `interface_adapters/api/deps.py` | `Contenedor.propuestas_mes` con `ThreadPoolExecutor(max_workers=1)` |
| api `interface_adapters/api/routes.py` | cuadrante y `/sync` lanzan (R29); `GET …/propuestas` (R35) |
| api `interface_adapters/api/schemas.py` | `LineaOut.propuesta_cod/res/metodo` (R27), `CuadranteOut.propuestas_en_curso` (R30), `PropuestasOut` |
| front `static/js/app.js`, `static/css/styles.css` | celda Partida con la propuesta (R27), «buscando partida…» y consulta (R36) |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`, READMEs de api y transfer | §8 |

## 5. Clases y funciones

### 5.1 Transfer · cliente (infrastructure)

- `validar_partidas(parides) -> dict[int, PartidaValida]`
  (`PartidaValida(ide, obride, cod, res, es_hoja, activa)`), SQL §6.
- `obras_por_ide(ides)`, `partes_de_periodos(obrides, periodos)` (clave
  `(obride, ano, mes)`) y `lineas_de_partes(hmoides, resides)`: el SQL suelto
  con `IN`, mismo `_obra` y mismo orden por clave.
- `_read(sql, params, nombre=…)`: mide y loguea (R1); el contrato no cambia.

### 5.2 Transfer · `lecturas_lote.py` (application)

- `LecturasDelLote(cliente, limite)`: los métodos de lectura del pipeline.
  Responde de lo precargado **solo si la consulta está entera dentro**
  (`horas_de_recursos` o `historial_partidas` de un subconjunto, misma
  ventana: filtrado por recurso; la propuesta no depende del orden de
  filas, `#regla-partida`); si no, llama al cliente real y apunta un
  `fallo_de_memoria` (log + contador). Un solo vuelo por clave (`Lock` +
  `Future`): dos hilos esperan la misma lectura (y la misma excepción).
  `escribir` lanza `RuntimeError`.
- `precargar` (rondas de §2) y `precargar_propuestas` (§2.1) con
  `ThreadPoolExecutor(limite)`; la primera excepción de una ronda sube
  (R24). Vive solo en una petición HTTP (R22, D4).

### 5.3 Transfer · pipeline y lotes

- `RegistroPipeline.preflight` (`paride` de obra normal): `self._validas`
  lee una vez `validar_partidas` de todos los `paride` y `propuesta_paride`;
  vale si `obride == origen.ide and es_hoja and activa` (R4); si no, R5.
- Rama nueva antes de la automática: con `propuesta_paride` válida, sus
  `partida_*` (R8); si no vale, cae a la pendiente (R6). El presupuesto de
  origen se lee **solo** para pendientes; `partidas_obra`, su catálogo o
  `[]` (R10). Postventa y VAR, sin cambios.
- `RegistroLote(cliente, settings)`: `preflight(peticiones)` y
  `proponer(peticiones)` → `list[resultado | Exception]`: precarga y luego
  un `RegistroPipeline(cliente=memoria)` por obra en el pool (sin estado
  entre llamadas, F-025 R9; un test lo fija). `proponer` devuelve de cada
  obra solo `propuestas` de `RegistroPipeline.proponer` (R21).
- `ejecutar` no cambia de forma (cliente real); gana R3-R9.
- `def preflight_lote(p: LoteIn)` y `def propuesta_lote(p: PropuestaLoteIn)`
  (R25): por entrada, la forma suelta (`_respuesta_preflight(pf)`, extraída
  de la ruta de hoy sin cambiar su salida) o `{ok: false, error}` (empresa
  no válida, otra empresa, no encontrada); `ano`/`mes` distintos → 422;
  fallo de una ronda compartida → 502 entero.

### 5.4 Api · registro y selector

- `_payloads`: sin elegida y con `a.propuesta_ide`, añade los cinco
  `propuesta_*` (R16). `preflight`: una llamada `transfer.preflight_lote`;
  `resultados` como hoy; luego `_guardar_propuestas`: por acción con método
  de propuesta, `UPDATE asignacion SET propuesta_* WHERE id = :rid AND
  partida_ide IS NULL` (ORM, como `_trazar`) (R14).
- `PartidasDeLinea.ejecutar`: con propuesta, `guardar_propuesta(periodo_id,
  trabajador_ide, clave, propuesta)` y `commit` (R15): caché del cuadrante.
- `_conservar_partidas` copia `propuesta_*`; `_snapshot` y
  `_validar_lineas` **no** (R17).

### 5.5 Api · `PropuestasDelMes` (`application/propuestas_mes.py`)

- `__init__(uow_factory, transfer, ejecutor, obras_por_llamada=10)`;
  estado en memoria bajo un `threading.Lock`: `_en_curso: set[periodo_id]`
  y `_sin_propuesta: set[(periodo_id, trabajador_ide, obra_ide)]` (R32).
  La api tiene **una réplica** (ARCHITECTURE «Topología»).
- `lanzar(anio, mes) -> bool`: UoW propia; periodo inexistente o no
  ABIERTO → False; en `_en_curso` → True; pendientes (R29) de
  `lineas_del_periodo` y `trabajadores.obtener`, menos `_sin_propuesta`;
  ninguna → False; si no, entra en `_en_curso`, `ejecutor.submit(
  self._calcular, …)` y True. **Nunca lanza**: excepción → log y False.
- `_calcular`: obras por código, trozos de `obras_por_llamada`; por obra
  `{empresa: obra_empresa, obra, ano, mes, lineas: [{clave:
  str(trabajador_ide), recurso_ide, nombre, categoria, es_postventa:
  False}]}`; `transfer.propuesta_lote`; UoW por trozo: propuesta →
  `guardar_propuesta(…, solo_si_vacia=True)` (`WHERE partida_ide IS NULL
  AND propuesta_ide IS NULL`), `None` u obra `{ok: false}` → `_sin_
  propuesta`; `commit`. `PropuestaNoDisponible` u otra → log y fin (R33).
  `finally`: sale de `_en_curso`.
- `olvidar()` (vacía `_sin_propuesta`); `estado(uow, anio, mes)` (R35).
- Rutas: `obtener_cuadrante` llama a `lanzar` **fuera** de su UoW y pone
  `propuestas_en_curso`; `sincronizar`, tras el éxito, `olvidar()` y
  `lanzar` de cada ABIERTO; `GET /periodos/{a}/{m}/propuestas` → `estado`. El
  `sync_pipeline` no se toca.

### 5.6 Front

- `construirCelda` (`partida`): sin elegida y con `propuesta_cod`, `<em>`
  «código · descripción» y `rotuloOrigen(propuesta_metodo)` (R27); sin ella,
  «buscando partida…» si `state.propuestasEnCurso`, si no «automática».
- `seguirPropuestas()`: con `propuestas_en_curso`, `setTimeout` de 5 s a
  `GET …/propuestas`; copia `propuesta_*` a las líneas aún sin elegida y
  repinta solo sus celdas Partida (no la fila en edición); para con
  `en_curso` falso o si cambia la generación (mes o empresa) (R36).

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

Los agrupados: el SQL suelto con `= ?` → `IN (?…)` y la clave en la salida.
`hoja`: como `build_arbol_partidas`, capítulo es el nodo con un hijo de la
misma obra; `activa` = `tipdes = 0`, como allí.

## 7. Tests y dobles

Sin red ni BBDD. Transfer: `validar_partidas` ≡ `construir_catalogo` (R4);
pipeline con `ClienteFalso` (R3-R10); `LecturasDelLote` (subconjuntos, un
solo vuelo, `escribir` prohibido, R24); **equivalencia** suelto/lote de los
escenarios de `test_f037_pipeline`, `test_f050_pipeline`,
`test_f002_pipeline`, `test_f039_preflight_var` y de la propuesta de F-050
(R21); conteos C1, C2, C7; R23; rutas con `TestClient`. Api: `_Uow` falsa
(R13-R18, R26); `PropuestasDelMes` con ejecutor **síncrono**, transfer y UoW
falsos (R29-R33); rutas (R15, R27, R30, R35). Front: node con temporizador
falso (R27, R36). Lista cerrada de tests anteriores: cabecera de `tasks.md`.

## 8. Documentación (R28)

`ARCHITECTURE.md`: `#regla-partida`, «Acceso a datos», «Timeouts
encadenados». `INTEGRACION.md`: R19, R34, R35, la variable,
`propuestas_en_curso`, `propuesta_*` y el orden **transfer → api → front**.

## 9. Ficheros que NO se tocan

Copias cerradas de `partes`, `reglas_porcentajes`, `propuesta_partida`,
`universo_*`, `excel/*`, `sync_pipeline`, `.env`, `infra/`, el `ejecutar` de
la api.

## 10. Riesgos

- **Equivalencia de los lotes**: memoria solo para consultas contenidas en
  la precargada, mismo SQL; el resto, a Sigrid; tests y mutación completa.
- **Propuesta guardada vieja** (D8): se escribe lo que el cuadrante enseña
  (R27); un parte nuevo en Sigrid no la cambia hasta abrir el selector.
- **Concurrencia en `sigrid-api`** (D5): tope 4, ajustable; T18 mide. El
  cálculo del mes va en **un** hilo: nunca dos lotes a la vez.
- **Cálculo en memoria de la api**: un reinicio lo pierde (el próximo `GET`
  lo relanza) y vacía R32; con dos réplicas se duplicaría (hoy `max 1`).
- **Carrera con el usuario**: el `UPDATE` condicional no pisa una elegida ni
  una propuesta del selector puestas mientras tanto; un `reemplazar` en medio
  conserva lo guardado (R17) o deja la línea pendiente para el próximo `GET`.
- **`ejecutar` del mes** sigue en serie (D6): si T18 pasa de 120 s, feature
  aparte. **Despliegue**: transfer → api → front (si no, 404 en los lotes).

## 11. Decisiones (DECIDIDAS por el humano el 2026-10-13)

| D | Decidida | Descartadas | Efecto en tests |
|---|---|---|---|
| D1 · Pendiente al registrar | **A**: camino de hoy solo para ella (presupuesto + historial, una vez por lote) y la api la guarda | B propuestas antes y preflight ligero; C omitir «elige partida» | `test_f050_r9_*` no cambian |
| D2 · Dónde y cuándo se guarda la propuesta | **A + C**: `asignacion.propuesta_*`; al volver de un preflight y al abrir el selector (A) **y** en lote, en segundo plano, de todas las pendientes al abrir un mes abierto o tras un sync (C, R29-R36), para que salga preseleccionada. **Cambia D3 de F-050** | B en segundo plano al guardar la fila | `test_f003_r8`, `_Uow`/`_cliente` de `test_f050_rutas_partida`, fixture `api` de `test_f024_rutas_empresa`, `CAMPOS_CUADRANTE` |
| D3 · Validar la partida al registrar | **A**: por `ide`; elegida que no vale → omitir; propuesta que no vale → recalcular | B no validar; C presupuesto entero | R20 de F-050 sin cambiar aserciones |
| D4 · Caché del transfer entre peticiones | **A**: no, memoria solo de la petición | B TTL 120 s; C solo en el selector | ninguno |
| D5 · Agrupar y paralelizar | **A**: por tipo + 4 a la vez (1-8) | B solo paralelo; C solo agrupar | C1 y C7 |
| D6 · Qué servicio hace qué | **A**: lotes en el transfer (R19, R34), la api los llama; `ejecutar` por obra y en serie | B la api paraleliza; C `ejecutar` en lote | transfer falsos con `preflight_lote` |
| D7 · La celda enseña la propuesta | **A**: sí, en cursiva con su método | B «automática» como hoy | `CAMPOS_LINEA` |
| D8 · Caducidad de la propuesta | **A**: no caduca; se reescribe al abrir el selector y si deja de valer | B por fecha; C botón «Recalcular» | ninguno |
