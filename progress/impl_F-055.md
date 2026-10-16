# F-055 · Informe del implementer

Rama `feature/F-055-preflight-rapido` (copia `porcentajes-f041`). Rigor
`critico`. Spec aprobada el 2026-10-13 (D9-D10 el 2026-10-14). Hechas por el
implementer: **T1, T2b, T2c, T3-T17**. T2 (cifras de navegador), T18-T20,
MANUAL o del líder: no son mías. T15 = solo la anotación en `current.md`.

Decisiones del humano durante la implementación (2026-10-15, en `tasks.md`):
bloqueo de T4 → `test_pipeline_offline.py` a la lista cerrada (solo su doble);
bloqueo de T9 («si a todo») → filas falsas de `test_f050_partida_linea.py`,
permiso general para ampliar dobles sin tocar aserciones y C2 contado como C1.

## Por tareas (qué cambió, RED y verde)

**T1 · Medición (R1, R2).** `medir_lecturas()`, `apuntar_lectura` (log
`[sigrid-read] <método> filas=<n|error> segundos=<s>`, sin SQL ni
parámetros), `_lectura(nombre, sql, params)`; resumen `[registro] lecturas
preflight …`; fase `medir`. **Desviación de design §5.1:** `_read` conserva
su firma (con `nombre` caían 35 tests anteriores con dobles de dos
argumentos). RED: `ImportError: cannot import name 'apuntar_lectura'`, luego
`30 failed, 5 passed`; verde 35.

**T2 · Cifras «antes» (script del humano).** 0694 **8 lecturas · 32.24 s**;
0696 **9 · 21.92 s**; `TOTAL: 2 obras · 17 lecturas · 54.15 s leyendo`; la
mayor, `horas_de_recursos` (7.99 s). Navegador: pendiente del humano.

**T2b · Orden a → c → b (R38).** `proponer_partida`: `previa_en_obra` →
`resolver_normal` → `ultima_de_recurso`. Lista cerrada:
`test_f050_r1_sin_paso1_va_al_paso2` → `(2108, "auto_nombre")`.
`test_f055_orden_propuesta.py` (8). RED:
```
E   AssertionError: assert (2110, 'ultimo_parte') == (2108, 'auto_nombre')
E   AssertionError: assert (80003, 'ulti... · obra 0678') == (80001, 'auto_nombre', None)
3 failed, 5 passed in 3.04s
```
**T2c.** `#regla-partida` con el orden nuevo y D10; `test_f002_fuente_unica`
72 passed.

**T3 · `validar_partidas` (R3, R4).** `PartidaValida(…).vale_en(obra)`, SQL
de design §6, trozos de 500, `truncated` → error; doble de `conftest.py`.
R4 con Sigrid emulada: mismo veredicto que `construir_catalogo` en 8 casos.
RED: `ImportError: cannot import name 'PartidaValida'`; verde 18.

**T4 · Preflight sin búsquedas (R3-R12).** `LineaEntrada`/`LineaIn`
`propuesta_*`, `AccionLinea.partida_res`; una lectura `validar_partidas` por
petición; elegida que no vale → `MOTIVO_PARTIDA_NO_HOJA`; guardada que vale
→ sus `partida_*` tal cual (design §10); si no, pendiente (presupuesto e
historial solo de pendientes); `partidas_obra` `[]` sin pendientes (sale
F-049 d). Lista cerrada: los dos `test_f049_d_*`. RED:
```
E   assert ([555001] == []        (la elegida aún leía el presupuesto)
E   TypeError: LineaEntrada.__init__() got an unexpected keyword argument 'propuesta_paride'
E   AttributeError: 'AccionLinea' object has no attribute 'partida_res'.
21 failed, 2 passed in 3.90s
```
verde 23.

**T5 · Lecturas agrupadas (R20).** `obras_por_ide`, `partes_de_periodos`,
`lineas_de_partes` (SQL de la suelta con `IN`, clave en la salida, mismo
orden, trozos de 500) y `horas_de_recursos` en trozos. RED: `17 failed`
(`no attribute 'obras_por_ide'`…, `assert [1101] == [500, 500, 101]`); verde 17.

**T6 · `LecturasDelLote` (R20, R22-R24).** Precarga en rondas A (obras por
`ide` y por código —origen, pruebas, postventa, VAR—, horas, `synckey`), B
(partes, `validar_partidas`, historial, presupuestos, `partidas_de_lineas`
solo de recursos sin subcuenta) y C (`lineas_de_partes`). **Desviación de
design §2:** validación e historial van en B, no en A, para que una obra con
elegidas quepa en una tanda de 4 por ronda (C2); no dependen de A. Memoria
solo si la consulta está dentro; si no, cliente real + `fallos_de_memoria` +
log; un solo vuelo por clave; `escribir` lanza; `copy_context` por hilo;
`SIGRID_LECTURAS_PARALELAS` (4, 1-8). **RED honesta:** el borrador se
escribió antes que sus tests; la RED se tomó apartándolo
(`ModuleNotFoundError: … 'application.services.lecturas_lote'`). Verde 35.

**T7 · `POST /api/registro/preflight-lote` (R19, R21, R24, R25; C1, C2).**
`RegistroLote.preflight`, `_respuesta_preflight` extraída, `def
preflight_lote`. R21 con el plugin `tests/f055_equivalencia_lote.py`: un
pytest aparte repite **cada preflight** de `test_f037_pipeline`,
`test_f050_pipeline`, `test_f002_pipeline` y `test_f039_preflight_var` en un
lote sobre una copia del doble (≥ 100 iguales, errores iguales). No compara,
con nombre, `test_f037_r17_…` (su doble da otro código en cada
`siguiente_cod_pt`; el lote lo lee una vez: lo cubre
`test_f055_r21_siguiente_cod_pt_una_vez_y_lo_mismo`). C2 (decisión del
humano): 8 lecturas en pruebas, 7 en real; contadas como C1, **6**; rondas
medidas **por estructura** (tandas `ceil(tareas/límite)` de cada `_ronda` +
la de `cuentas_de_centro`), **4**. RED: `ModuleNotFoundError: …
'application.pipelines.registro_lote'` (borrador apartado) e `ImportError:
cannot import name '_respuesta_preflight'`; verde 17.

**T8 · `POST /api/partidas/propuesta-lote` (R34; C7).**
`precargar_propuestas` (A obras + historial; B presupuestos), 
`RegistroLote.proponer`, `def propuesta_lote` (periodos distintos 422;
empresa no válida, otra empresa o no encontrada, solo su entrada; fallo
compartido 502). El plugin compara cada `proponer` de
`test_f050_endpoint_propuesta` y `test_f055_orden_propuesta`; no compara los
`test_f050_script_propuesta_*` (el script envuelve el doble con cierres
sobre el original). C7: 1 + 1 + 10 lecturas, tandas `[(2, 1), (10, 3)]`.
RED: `15 failed` (`'RegistroLote' object has no attribute 'proponer'`, 404).

**T9 · Propuesta guardada en la api (R13, R17).** ORM y `Linea`
`propuesta_*`; `guardar_propuesta(…, solo_si_vacia)` (`UPDATE` del ORM con
`partida_ide IS NULL` y, si se pide, `propuesta_ide IS NULL`);
`_conservar_partidas` la copia; copiar el mes y F8 la quitan; eventos sin
ella. Lista cerrada: `test_f003_r8_…`. RED: `20 failed` (`unexpected keyword
argument 'propuesta_ide'`, `KeyError: 'propuesta_cod'`).

**T10 · Registro (R14, R16, R26).** Payload con `propuesta_*` si no hay
elegida ni override; preflight en **una** llamada a
`TransferClient.preflight_lote` (si el lote falla o viene incompleto, cada
obra lleva el error); `_guardar_propuestas` (`es_metodo_de_propuesta`, solo
sin elegida, sin evento ni `sigrid_*`, sesión solo si hay algo). Lista
cerrada: `_fila` y `_Transfer.preflight_lote` de f022/f024/f026/f039. RED:
`ImportError: cannot import name 'es_metodo_de_propuesta'`; verde 17.

**T11 · Selector y `LineaOut` (R15, R18, R27).** El selector guarda (y
reescribe) la propuesta de una línea sin elegida; `LineaOut.propuesta_cod/
res/metodo`. Lista cerrada: `_Uow` de `test_f050_rutas_partida`,
`CAMPOS_LINEA`. RED: `3 failed` (`(1, 'auto_nombre') == (80002, …)`,
`KeyError: 'propuesta_cod'`); verde 27.

**T12 · `PropuestasDelMes` (R29-R33, R35).** Cola por línea `(periodo,
trabajador, obra)`, `en_curso`, `lanzar` (nunca lanza), `_calcular` en
trozos de 10, `olvidar`, `tras_sync`, `estado`; `propuesta_lote` del
cliente; `Contenedor.propuestas_mes` con `ThreadPoolExecutor(max_workers=1)`;
cuadrante, `/sync` y `GET …/propuestas`. **Desviación de design §5.5:** la
`empresa` de cada petición es la de las obras (`EMPRESA_IMPUTACION`), como en
el selector y el registro, no `obra_empresa` (una obra sin empresa no
tendría nunca propuesta). Lista cerrada: fixture `api` (f024), `_cliente`
(f050), `CAMPOS_CUADRANTE`. RED: `ModuleNotFoundError: …
'application.propuestas_mes'`, luego `8 failed`; verde 24.

**T12b · Tras escribir (D9; R37).** `_encolar` (nunca rompe la respuesta)
en las seis escrituras; `propuestas_en_curso` en `FilaOut`,
`CopiaPeriodoOut`, `CompletarOut` (y `CopiaTrabajadorOut`). Lista cerrada:
`test_f029_r25_…`. RED: `19 failed` (`KeyError: 'propuestas_en_curso'`);
verde 20.

**T13 y T13b · Front (R27, R36).** `htmlPartida` (propuesta en cursiva con
método, «buscando partida…», «automática»), `aplicarPropuestas`,
`marcarPropuestas`, `reiniciarPropuestas`, `seguirPropuestas` (un solo
temporizador, 5 s), `consultarPropuestas`, `repintarCeldasPartida` (solo
celdas Partida, no la fila en edición); `aplicarFila`, Completar y Copiar mes
lo arrancan. `construirCelda` conserva las ramas literales que fija
`test_f050_r24_…` (no está en la lista). Un commit para las dos tareas
(código entrelazado). RED: `20 failed` (`no existe const
INTERVALO_PROPUESTAS`…); verde 22.

**T14 · Documentación.** `#regla-partida` (propuesta guardada, cuándo se
calcula, validación por `ide`), «Acceso a datos», «Timeouts encadenados»,
`INTEGRACION.md` (lotes, `GET …/propuestas`, `propuestas_en_curso`,
columnas, variable, orden de despliegue) y READMEs. `test_f002_fuente_unica`
72 y `tests/test_f004_readme.py` 11 passed.

## Dobles ampliados (para el reviewer)

Campos nulos o métodos derivados de sus datos, sin tocar aserciones:
`conftest.py` (`validar_partidas`, `obras_por_ide`, `partes_de_periodos`,
`lineas_de_partes`); `test_pipeline_offline.py` (`validar_partidas`);
`test_f050_partida_linea.py` (`SIN_PROPUESTA`); `_fila`/`_Transfer` de
f022/f024/f026/f039; `_AsignacionesR15` y `_PropuestasFalsas` (f050 rutas,
f024 rutas). Ninguna otra aserción anterior cambia salvo la lista cerrada.

## T16 · Mutación

- **Arnés, primera pasada** (HEAD `68a5c6b`): 281 mutantes, 242 muertos,
  **39 supervivientes** (`progress/mutacion_F-055_pasada1.md`). Ninguno
  equivalente: todos eran huecos de test (valores por defecto de esquemas y
  firmas, `exc_info`, la memoria que precarga de más o de menos sin cambiar
  el resultado, el mapeo de nulos de `_linea_del_parte`, `"ok"` de
  `_respuesta_preflight`, `Lectura` inmutable y la fase `medir`). `9d9ebb1`
  añade un test para cada uno, comprobado re-aplicando los 39 uno a uno
  contra los `test_f055_*` del servicio (todos mueren). Un intento anterior
  se cortó a medias con la sesión (se restauró con `--restaurar`).
- **Arnés, pasada final** (HEAD `9d9ebb1`): **284 generados, 284 muertos,
  0 supervivientes**, 0 timeouts, 3666 s con 4 workers
  (`progress/mutacion_F-055.md`).
- **JS** (manual, `progress/mutacion_manual_F-055.md`): 36 mutantes de T13 y
  T13b; primera pasada 4 vivos (huecos reales, tests en `68a5c6b`); segunda
  pasada **36/36 muertos**.
- Además: la fase `medir --lote` del script mide ya el preflight en lote (lo
  pide T18; en T1 solo avisaba); `test_f055_r2_medir_con_lote_aun_mide_…`,
  test propio de F-055, pasa a `…_mide_el_lote_entero`.
- La campaña encontró en su primera línea base un test de C2 que medía
  rondas **por reloj** y fallaba con 4 suites a la vez: rondas medidas ahora
  por estructura (`3cbaba4`).

## Evidencias

Medidas con `bash harness/init.sh` sobre `807dd32`, con
`.arnes_cache/suite_*.ok` borrados antes (las cuatro suites enteras):
**ENTORNO LISTO**, exit 0, **ningún `[KO]`**.

| Evidencia | Valor |
|---|---|
| Tests transfer | **930 passed** (48.88 s) |
| Tests api | **871 passed** (101.63 s) |
| Tests front | **291 passed** (62.22 s) |
| Tests raíz | **418 passed, 1 skipped** (105.61 s) |
| Tests de F-055 | transfer `test_f055_*` + el plugin de equivalencia (que repite ≥ 100 preflights y ≥ 11 propuestas en lote); api 4 ficheros; front 22 |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 795 líneas cambiadas cubiertas (795/795, umbral 80%, nivel critico)` |
| Mutantes (arnés) | **284 generados, 284 muertos, 0 supervivientes** (pasada final, `progress/mutacion_F-055.md`); primera pasada 39 vivos con test cada uno (`…_pasada1.md`) |
| Mutantes (JS, manual) | **36/36 muertos** en la segunda pasada (`progress/mutacion_manual_F-055.md`) |
| Tamaño | `PUERTA TAMAÑO`: impl dentro del tope |
| `ruff` | aviso no bloqueante: 287 (237 antes de F-055); lo nuevo sigue el estilo de cada fichero (`Optional`, `noqa: BLE001`, imports) |

**Verificaciones MANUAL pendientes (no mías):** T2 (cifras de navegador),
T18 (`medir --lote`, C3-C5, C8 en local), T19 (registro en modo pruebas) y
T20; T15: copiar lo nuevo de `docs/INTEGRACION.md` a `azure-apps`
(líder). Fuera de alcance, como dice la spec: `ejecutar` en lote, F-048,
F-051, F-044.
