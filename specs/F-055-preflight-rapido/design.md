<!-- specs/F-055-preflight-rapido/design.md -->
# F-055 · Diseño

**D1-D8 DECIDIDAS por el humano el 2026-10-13** (A salvo **D2 = A + C**);
**D9-D10 el 2026-10-14** (ampliación: propuesta tras escribir y orden a → c →
b). Todo en §11. Rigor `critico`. Sobre `dev` con F-050 fusionada (T15c).

## 1. Límite de servicio

- **Transfer** (lee Sigrid y decide): validación por `ide`, propuesta (pasos
  de F-050 en el orden de R38), lotes agrupados y en paralelo. Sin escrituras.
- **Api** (dueña del cuadrante): guarda la propuesta en `asignacion`, la
  manda al registrar, pide el preflight en lote y **encola y guarda** el
  cálculo en segundo plano (R29-R33, R37). No propone ni valida.
- **Front**: pinta la propuesta (R27) y consulta R35 (R36). No decide. Nada
  es de otro microservicio. `sigrid-api` recibe **menos** peticiones pero
  hasta 4 a la vez (D5; `azure-apps/sigrid_api.md` §3.4 no documenta tope de
  concurrencia): ajustable, y 1 vuelve al serie de hoy.

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

Hoy, 8-9 lecturas en serie por obra a 4-6 s: pesa la latencia. Rondas: A
obras, horas, `synckey`, `validar_partidas`, `partidas_de_lineas` e
historial si hay pendientes; B `partes_de_periodos` y presupuestos de
postventa, VAR y obras con pendientes; C `lineas_de_partes`. Luego decisiones
por obra en paralelo; `cuentas_de_centro` (collation de SQL Server) y
`siguiente_cod_pt`, a `sigrid-api` con un solo vuelo.

### 2.1 Propuestas en segundo plano (R34) y coste esperado
A: `obras_por_ide` e `historial_partidas` de **todos** los recursos (misma
ventana). B: `capitulos_de_obra` por obra, hasta el límite a la vez. Luego
`proponer` por obra. Con lo medido (obra 4-6 s, historial 0,8-5,7 s,
presupuesto 3,3-5,3 s): 10 obras ≈ 6 s + 3 rondas ≈ **22 s** (timeout 180 s);
un mes con 40 obras ≈ 90 s (C8). **Tras una escritura** (D9), la obra nueva
del trabajador: ≈ 11 s + ≤ 5 s de la consulta del front ⇒ ≤ 30 s (C8).

## 3. Ficheros a crear

transfer `application/services/lecturas_lote.py`, `application/pipelines/
registro_lote.py`; api `application/propuestas_mes.py`; `test_f055_*.py` (§7).

## 4. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `infrastructure/sigrid/sigrid_write_client.py` | medición (T1, hecha); `validar_partidas`, `obras_por_ide`, `partes_de_periodos`, `lineas_de_partes`; `horas_de_recursos` en trozos de 500 |
| transfer `application/services/propuesta_partida.py` | **solo** el orden de `proponer_partida` y el docstring del módulo (R38, §5.7) |
| transfer `domain/models/registro_models.py` | `LineaEntrada.propuesta_*` (5), `AccionLinea.partida_res` |
| transfer `application/pipelines/registro_pipeline.py` | rama manual con `validar_partidas`; rama de propuesta guardada; `partida_res`; sin la lectura forzada de F-049 d; log de resumen (T1) |
| transfer `interface_adapters/api/app.py` | `LineaIn.propuesta_*`, `LoteIn`, `PropuestaLoteIn`, `def preflight_lote`, `def propuesta_lote` |
| transfer `config/settings.py`; `prueba_escritura_porcentajes.py` | `sigrid_lecturas_paralelas` (`SIGRID_LECTURAS_PARALELAS`, 4, 1-8); fase `medir` (R2, T1) |
| api `infrastructure/db/orm_models.py`, `domain/models.py` | `AsignacionORM.propuesta_*` (R13); `Linea.propuesta_ide/cod/res/metodo/origen` (None, al final) |
| api `infrastructure/db/repositories.py`, `domain/ports.py`, `application/use_cases.py` | `_a_linea`/`reemplazar` con propuesta; `guardar_propuesta(…, solo_si_vacia=False)`; `_conservar_partidas` conserva también la propuesta (R17) |
| api `application/registro_sigrid.py`, `application/partidas_linea.py` | payload con propuesta (R16); preflight por lote (R26); `_guardar_propuestas` (R14); el selector guarda la propuesta devuelta (R15) |
| api `infrastructure/transfer/transfer_client.py`, `interface_adapters/api/deps.py` | `preflight_lote(peticiones)`, `propuesta_lote(peticiones)`; `Contenedor.propuestas_mes` con `ThreadPoolExecutor(max_workers=1)` |
| api `interface_adapters/api/routes.py` | cuadrante, `/sync` y las seis escrituras de §5.5 encolan (R29, R37); `GET …/propuestas` (R35) |
| api `interface_adapters/api/schemas.py` | `LineaOut.propuesta_cod/res/metodo` (R27); `propuestas_en_curso: bool = False` en `CuadranteOut`, `FilaOut`, `CopiaTrabajadorOut`, `CopiaPeriodoOut`, `CompletarOut` (R30, R37); `PropuestasOut` |
| front `static/js/app.js`, `static/css/styles.css` | celda Partida con la propuesta (R27), «buscando partida…» y consulta, también tras escribir (R36) |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`, READMEs de api y transfer | §8 |

## 5. Clases y funciones

### 5.1 Transfer · cliente (infrastructure)
- `validar_partidas(parides) -> dict[int, PartidaValida]` (`PartidaValida(
  ide, obride, cod, res, es_hoja, activa)`), SQL §6. `obras_por_ide(ides)`,
  `partes_de_periodos(obrides, periodos)` (clave `(obride, ano, mes)`) y
  `lineas_de_partes(hmoides, resides)`: el SQL suelto con `IN`, mismo `_obra`
  y mismo orden por clave. Medición (R1): `_lectura(nombre, sql, params)`
  envuelve `_read`, que conserva su firma (desviación aceptada en T1).

### 5.2 Transfer · `lecturas_lote.py` (application)
- `LecturasDelLote(cliente, limite)`: los métodos de lectura del pipeline.
  Responde de lo precargado **solo si la consulta está entera dentro**
  (`horas_de_recursos` o `historial_partidas` de un subconjunto, misma
  ventana; la propuesta no depende del orden de filas); si no, llama al
  cliente real y apunta un `fallo_de_memoria` (log + contador). Un solo vuelo
  por clave (`Lock` + `Future`: dos hilos esperan la misma lectura y la misma
  excepción). `escribir` lanza `RuntimeError`.
- `precargar` (rondas de §2), `precargar_propuestas` (§2.1):
  `ThreadPoolExecutor(limite)` con `contextvars.copy_context` (medición de
  T1); la primera excepción de una ronda sube (R24). Solo una petición (R22).

### 5.3 Transfer · pipeline y lotes
- `RegistroPipeline.preflight`: `self._validas` lee una vez `validar_partidas`
  de todos los `paride` y `propuesta_paride`; vale si `obride == origen.ide
  and es_hoja and activa` (R4); si no, R5. Rama nueva antes de la automática:
  `propuesta_paride` válida → sus `partida_*` (R8); si no, pendiente (R6).
  Presupuesto de origen **solo** para pendientes; `partidas_obra`, su
  catálogo o `[]` (R10). Postventa, VAR y la forma de `ejecutar`, igual.
- `RegistroLote(cliente, settings)`: `preflight(peticiones)` y
  `proponer(peticiones)` → `list[resultado | Exception]`: precarga y luego
  un `RegistroPipeline(cliente=memoria)` por obra en el pool (sin estado
  entre llamadas, F-025 R9; un test lo fija); `proponer` devuelve solo las
  `propuestas` de `RegistroPipeline.proponer` (R21).
- `def preflight_lote(p: LoteIn)`, `def propuesta_lote(p: PropuestaLoteIn)`
  (R25): por entrada, la forma suelta (`_respuesta_preflight(pf)`, extraída
  sin cambiar la salida de hoy) o `{ok: false, error}` (empresa no válida,
  otra empresa, no encontrada); `ano`/`mes` distintos → 422; ronda
  compartida que falla → 502.

### 5.4 Api · registro y selector
- `_payloads`: sin elegida y con `a.propuesta_ide`, los cinco `propuesta_*`
  (R16). `preflight`: una llamada `transfer.preflight_lote`; `resultados`
  como hoy; luego `_guardar_propuestas`: por acción con método de propuesta,
  `UPDATE asignacion SET propuesta_* WHERE id = :rid AND partida_ide IS NULL`
  (ORM, como `_trazar`) (R14).
- `PartidasDeLinea.ejecutar`: con propuesta, `guardar_propuesta(periodo_id,
  trabajador_ide, clave, propuesta)` y `commit` (R15). `_conservar_partidas`
  copia `propuesta_*`; `_snapshot` y `_validar_lineas` **no** (R17).

### 5.5 Api · `PropuestasDelMes` (`application/propuestas_mes.py`)
- `__init__(uow_factory, transfer, ejecutor, obras_por_llamada=10)`; estado
  bajo un `threading.Lock`: `_en_cola` y `_sin_propuesta`, `set[(periodo_id,
  trabajador_ide, obra_ide)]` (R30, R32). Una réplica (ARCHITECTURE
  «Topología»). `en_curso(periodo_id)`: alguna clave suya en `_en_cola`.
- `lanzar(anio, mes, trabajadores=None) -> bool`: UoW propia; periodo
  inexistente o no ABIERTO → False; pendientes (R29) de `lineas_del_periodo`
  (solo de `trabajadores` si se pasan) y `trabajadores.obtener`, menos
  `_sin_propuesta` y `_en_cola`; si hay, entran en `_en_cola` y
  `ejecutor.submit(self._calcular, periodo_id, lineas)` (una tarea por
  llamada, en orden de llegada). Devuelve `en_curso(periodo_id)`. **Nunca
  lanza**: excepción → log y False (R37).
- `_calcular`: obras por código, trozos de `obras_por_llamada`; por obra
  `{empresa: obra_empresa, obra, ano, mes, lineas: [{clave: str(trabajador_
  ide), recurso_ide, nombre, categoria, es_postventa: False}]}`;
  `transfer.propuesta_lote`; UoW por trozo: propuesta → `guardar_propuesta(…,
  solo_si_vacia=True)` (`WHERE partida_ide IS NULL AND propuesta_ide IS
  NULL`); `None` u obra `{ok: false}` → `_sin_propuesta`; `commit`; error →
  log y fin (R33); `finally`: sus claves salen de `_en_cola`. `olvidar()`
  vacía `_sin_propuesta`; `estado(uow, anio, mes)` (R35).
- Rutas, siempre **tras cerrar** su UoW: `obtener_cuadrante` → `lanzar(a,
  m)`; `sincronizar`, tras el éxito, `olvidar()` y `lanzar` de cada ABIERTO;
  **escrituras (D9, R37)**: `PUT …/asignaciones` (guardar la fila y F7),
  `PUT …/partida`, `POST …/deshacer` y `POST …/trabajadores/{ide}/copiar-
  anterior` (F8) → `lanzar(a, m, [ide])`; `POST …/completar` → `lanzar(a, m,
  payload.trabajadores)`; `POST …/copiar-anterior` (Copiar mes) → `lanzar(a,
  m)`. El `bool` va a `propuestas_en_curso`. `GET /periodos/{a}/{m}/
  propuestas` → `estado`. `sync_pipeline`, intacto.

### 5.6 Front
- `construirCelda` (`partida`): sin elegida y con `propuesta_cod`, `<em>`
  «código · descripción» y `rotuloOrigen(propuesta_metodo)` (R27); sin ella,
  «buscando partida…» si `state.propuestasEnCurso`, si no «automática».
- `seguirPropuestas()`: `setTimeout` de 5 s a `GET …/propuestas`; copia
  `propuesta_*` a las líneas aún sin elegida y repinta solo sus celdas
  Partida (no la fila en edición); para con `en_curso` falso o si cambia la
  generación (mes o empresa). **Un solo temporizador** vivo (R36).
- Tras escribir (D9): `aplicarFila(datos)` (guardar, F7, F8, deshacer,
  partida) y los manejadores de Completar y Copiar mes, con
  `datos.propuestas_en_curso`, marcan el estado y llaman a `seguirPropuestas()`.

### 5.7 Transfer · orden de la propuesta (R38, D10)
`proponer_partida`: `previa_en_obra` (a) → `resolver_normal` (c) →
`ultima_de_recurso` (b); firmas, métodos y `origen` iguales. **Consecuencia
(aceptada por el humano al pedir el orden):** `resolver_normal` casi siempre
da algo: `match_partida` casa con que **un** token de la categoría esté a
distancia fonética ≤ 1, o sea prefijo (≥ 4 letras), del rol de **alguna**
hoja de CI (o CI + CD para oficiales, peones y desconocidas), o con que el
nombre salga en la descripción; en presupuestos reales (0694: 835 hojas;
0696: 2.636) pasa siempre que haya categoría. Así, el paso (b) **solo
actuará cuando el casamiento no encuentre nada**. Sin decisión nueva.

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

Sin red ni BBDD. Transfer: orden (R38: a gana a c, c gana a b, sin c sale b,
sin nada None; selector = preflight); `validar_partidas` ≡ `construir_
catalogo` (R4); pipeline con `ClienteFalso` (R3-R10); `LecturasDelLote`
(subconjuntos, un solo vuelo, `escribir` prohibido, R24); **equivalencia**
suelto/lote de `test_f037_pipeline`, `test_f050_pipeline`, `test_f002_
pipeline`, `test_f039_preflight_var` y la propuesta de F-050 (R21); C1, C2,
C7; R23; rutas con `TestClient`. Api: `_Uow` falsa (R13-R18, R26);
`PropuestasDelMes` con ejecutor síncrono o retenido (R29-R33, cola por
línea); rutas (R15, R27, R30, R35, R37 en las seis escrituras). Front: node
con temporizador falso (R27, R36). Lista cerrada: cabecera de `tasks.md`.

## 8. Documentación (R28)

`ARCHITECTURE.md`: `#regla-partida` (fuente única: orden a → c → b,
propuesta guardada, cuándo se calcula), «Acceso a datos», «Timeouts»;
`INTEGRACION.md`: R19, R34, R35, R37, variable, columnas, transfer → api →
front.

## 9. Ficheros que NO se tocan

Copias cerradas de `partes` (`partida_matcher`, `partida_catalog`,
`text_match`), `partida_resolver`, `reglas_porcentajes`, `universo_*`,
`excel/*`, `sync_pipeline`, `.env`, `infra/`, el `ejecutar` de la api; de
`propuesta_partida`, todo salvo `proponer_partida` y el docstring.

## 10. Riesgos

- **Equivalencia de los lotes**: memoria solo para consultas contenidas en
  la precargada, mismo SQL; el resto, a Sigrid; tests y mutación completa.
  **Propuesta guardada vieja** (D8): se escribe lo que el cuadrante enseña.
- **Concurrencia** (D5): tope 4, ajustable; T18 mide. El segundo plano va
  en **un** hilo: una línea escrita mientras corre el mes entero espera su
  turno (≈ 90 s, solo la primera vez que se abre un mes). Un reinicio pierde
  la cola (se relanza sola) y vacía R32; con dos réplicas se duplicaría.
- **Carrera**: el `UPDATE` condicional no pisa elegida ni propuesta del
  selector; un `reemplazar` en medio conserva (R17). **Orden a → c → b**
  (D10): cambia propuestas que hoy salen por `ultimo_parte` (0696 de GONZALEZ
  PANIAGUA en M1 de F-050); T18 lo separa.
- **`ejecutar` del mes** en serie (D6): si T18 pasa de 120 s, feature
  aparte. **Despliegue**: transfer → api → front (si no, 404 en los lotes).

## 11. Decisiones (DECIDIDAS por el humano: D1-D8 el 2026-10-13, D9-D10 el 2026-10-14)

| D | Decidida | Descartadas | Efecto en tests |
|---|---|---|---|
| D1 · Pendiente al registrar | **A**: camino de hoy solo para ella (presupuesto + historial, una vez por lote) y la api la guarda | B propuestas antes y preflight ligero; C omitir «elige partida» | `test_f050_r9_*` no cambian |
| D2 · Dónde y cuándo se guarda | **A + C** («la partida debe venir preseleccionada, la del último parte del trabajador en esa obra, o si no hay, eligiendo una en CI como hacemos en partes»): `asignacion.propuesta_*`; al volver de un preflight y al abrir el selector (A) **y** en lote, en segundo plano, al abrir un mes abierto o tras un sync (C). **Cambia D3 de F-050**. B (al guardar la fila) entra el 2026-10-14 con D9 | — | `test_f003_r8`, `_Uow`/`_cliente` de `test_f050_rutas_partida`, fixture `api` de `test_f024_rutas_empresa`, `CAMPOS_CUADRANTE` |
| D3 · Validar la partida al registrar | **A**: por `ide`; elegida que no vale → omitir; propuesta que no vale → recalcular | B no validar; C presupuesto entero | R20 de F-050 sin cambiar aserciones |
| D4 · Caché del transfer entre peticiones | **A**: no, memoria solo de la petición | B TTL 120 s; C solo en el selector | ninguno |
| D5 · Agrupar y paralelizar | **A**: por tipo + 4 a la vez (1-8) | B solo paralelo; C solo agrupar | C1 y C7 |
| D6 · Qué servicio hace qué | **A**: lotes en el transfer (R19, R34), la api los llama; `ejecutar` por obra y en serie | B la api paraleliza; C `ejecutar` en lote | transfer falsos con `preflight_lote` |
| D7 · La celda enseña la propuesta | **A**: sí, en cursiva con su método | B «automática» como hoy | `CAMPOS_LINEA` |
| D8 · Caducidad de la propuesta | **A**: no caduca; se reescribe al abrir el selector y si deja de valer | B por fecha; C botón «Recalcular» | ninguno |
| D9 · Propuesta tras escribir | **Sí** (en producción la línea nueva seguía «automática» hasta registrar): guardar la fila, F7, F8, Completar, Copiar mes, cambiar la partida y **Deshacer** (recomendación del líder: deshacer no restaura la propuesta, R17, y deja pendientes; **validado por el humano el 2026-10-15**: «solo se recalcula si cambias algo de ese trabajador, si es de otro no. ok a todo») encolan sus pendientes (del trabajador; del periodo en Copiar mes) en la misma cola; las respuestas publican `propuestas_en_curso` | solo al abrir el mes o sincronizar (D2 C) | `test_f029_r25_ruta_200_con_resultados_y_resumen`; fixture `api` y `_cliente`, ya listados |
| D10 · Orden de la propuesta | **a → c → b** («si pero en reglas hay que cambiar el orden, a c b»): parte anterior → casamiento → último parte. **Cambia R1 de F-050** y `#regla-partida`; consecuencia en §5.7 | a → b → c (F-050) | `test_f050_r1_sin_paso1_va_al_paso2` |
