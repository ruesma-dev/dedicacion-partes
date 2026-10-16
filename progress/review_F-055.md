<!-- progress/review_F-055.md -->
Revisión completa (pasada 1), `git diff dev...HEAD` sobre `83c2d8d` (rama `feature/F-055-preflight-rapido`, copia `porcentajes-f041`).

# F-055 · Review

**Veredicto: APROBADO** (APPROVED). Sin bloqueos. Observaciones no bloqueantes al final, **para recoger** (O1-O9).
La feature **no se cierra** hasta tener T2 (navegador), T18-T20 MANUAL y T15 (azure-apps, líder): no bloquean esta review.

**Rigor: `critico`** (declarado en `features.json`). Exige fase RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes sin
justificación aceptada, RM1-RM6 y MANUAL con comando exacto y resultado real (los resultados de T18-T19 llegan después).

## init.sh (cachés `suite_*.ok` borradas antes, ejecutado solo)

`ENTORNO LISTO`, exit 0, ningún `[KO]`: raíz 418 + 1 skipped; api 871; front 291; transfer 930 (las cifras del informe).
`PUERTA COBERTURA: 100.0% de 795 líneas cambiadas (umbral 80%, critico)`; `PUERTA TAMAÑO` OK (req 149/150, design 250/250, impl 210/220).
`ruff`: 287 avisos (aviso, no bloquea). Árbol limpio antes y después de la review (`git status`).

## Lista CERRADA de tests anteriores (`tasks.md`)

Leído el diff de los 15 ficheros de test anteriores que cambian. Todo encaja en la lista o en el permiso de dobles:
- **Aserciones cambiadas, todas listadas:** `test_f003_r8_…` (+5 columnas), `CAMPOS_LINEA`/`CAMPOS_CUADRANTE` de `test_f034_rutas`,
  los dos `test_f049_d_*` (R10), `test_f050_r1_sin_paso1_va_al_paso2` (D10) y `test_f029_r25_…` (`propuestas_en_curso: False`).
- **Solo dobles** (campos nulos o métodos derivados de sus datos, sin tocar aserciones): `conftest.py`, `test_pipeline_offline.py`
  (solo su `ClienteFalso`), `test_f050_partida_linea.py` (solo `SIN_PROPUESTA` en sus filas falsas), `_fila`/`_Transfer` de
  f022/f024/f026/f039, fixture `api` de f024 (`_PropuestasFalsas`), `_Uow`/`_cliente` de `test_f050_rutas_partida`.
- Ningún otro test anterior cambia (front y raíz: solo ficheros nuevos). Coincide con «Dobles ampliados» del informe.

## Puntos pedidos por el líder

- **D9/R29/R37.** `_encolar` (nunca rompe la respuesta) en las seis escrituras, siempre tras cerrar la UoW: guardar fila/F7,
  partida, deshacer y F8 → `[ide]`; Completar → `payload.trabajadores`; Copiar mes → todo el periodo. `_lanzar` filtra por
  `trabajadores` (no encola los de otros). Tests: `test_f055_r37_cada_escritura_…` (5 rutas × en_curso), `…_deshacer_…`,
  `…_si_encolar_falla_…`, `test_f055_r29_con_trabajadores_solo_los_suyos`, `…_guardar_una_obra_nueva_encola_esa_linea_y_no_la_otra`.
- **D10/R38.** `proponer_partida`: `previa_en_obra` → `resolver_normal` → `ultima_de_recurso`; mismo módulo en selector, preflight
  y R34. `#regla-partida` reescrito con el orden y la consecuencia de §5.7. `test_f055_orden_propuesta.py` (8).
- **R3-R12, «se escribe lo que enseña el cuadrante».** Una lectura `validar_partidas` por petición (elegida o, sin ella, la
  guardada); presupuesto e historial solo si hay pendientes (`por_proponer`); guardada válida → sus cinco `propuesta_*` tal cual
  (R8); inválida → pendiente (R6); elegida inválida → `MOTIVO_PARTIDA_NO_HOJA` (R5); sale la lectura forzada de F-049 d (R10).
- **Concurrencia.** Api: `ThreadPoolExecutor(max_workers=1)`, cola por línea `(periodo, trabajador, obra)` bajo `Lock`; las claves
  salen en `finally`. Transfer: `_una_vez` (`Lock` + `Future`, misma excepción a todos), `copy_context` en cada hilo de ronda y de
  obra; sin anidar pools desde las tareas (sin interbloqueo). **R31:** `guardar_propuesta(…, solo_si_vacia=True)` es un `UPDATE`
  con `partida_ide IS NULL AND propuesta_ide IS NULL` por `(periodo, trabajador, obra, postventa)`: sobrevive a un `reemplazar`.
- **Front sin lógica.** `htmlPartida` solo pinta lo que manda la api; `seguirPropuestas` con un solo `setTimeout` vivo, generación
  que corta al cambiar de mes/empresa, no repinta la fila en edición. Decide «buscando…» como dice design §5.6 (ver O2).
- **Desviación de T1** (`_lectura`, `_read` con su firma): ya escrita en design §5.1 con la ampliación aprobada (`c59bcd6`).
  **Decisiones para el reviewer de T7/T8:** `SIN_COMPARAR` del plugin (f037_r17 por su doble con iterador, cubierto por
  `test_f055_r21_siguiente_cod_pt_…`; los `test_f050_script_propuesta_*`) y C2 medido por estructura: aceptadas. Ver O6.
- **Rastro.** `current.md`: cabecera «F-055 en curso … En review», MANUAL T18/T19 con comando exacto, T15 pendiente del líder con
  la lista de contratos. `features.json` `in_progress`/`critico`. `INTEGRACION.md`: R19, R34, R35, R37, variable, columnas,
  timeouts y orden transfer → api → front. README de api y transfer al día.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés.
**C2** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md` de la sesión activa (cabecera y F-055 coherentes) ·
[x] features `done` con history (F-055 no lo es).
**C3** [x] hexagonal: dominios sin infraestructura; `PartidaValida` pura; `_guardar_propuestas` usa el ORM en `application` como
`_trazar` (design §5.4; patrón previo); `medir_lecturas` importado de `infrastructure` como ya lo estaba `synckey_de` (previo) ·
[x] primera línea con ruta en todo fichero de código nuevo · [x] sin prints de debug, TODOs ni secretos; sin dependencias nuevas ·
[x] trampas: escala (solo `round(1/len(obras),4)` del script, sobre 1), postventa (clave con `es_postventa`, no se encola, no se
guarda), solo escribe el transfer (`LecturasDelLote.escribir` lanza; `ejecutar` por obra y en serie).
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] trazabilidad (tabla abajo; R11 y R28 sin test con su número, O1) · [x] sin red ni BBDD · [x] MANUAL en `current.md` con
comando exacto (T18, T19; T2 a medias).
**C4 bis** [x] rigor declarado · [x] fase RED con salida real por tarea (T6 y T7 con el borrador apartado, declarado) ·
[x] cobertura 100 % · [x] informe de mutación generado, totales recalculados (abajo) · [x] muertos comprobados (abajo) ·
[x] coste por mutante 3666,2 × 4 / 284 = 51,6 s > 1 s · [x] sin «CAMPAÑA NO VÁLIDA», base rota 0 · [x] RM1 · [x] RM2 ·
N/A RM5: ningún superviviente declarado equivalente (284/284 muertos) · N/A RM6: entre pasadas no cambió código de producción
salvo `fase_medir --lote` (añade, no quita guardas) · [x] campaña manual JS con texto exacto y fallos por fila, 3 filas reproducidas
· [x] sin análisis `PENDIENTE` en el informe vigente (O8) · [x] «Evidencias» con los cuatro números y 4 workers · [x] ningún N/A sin motivo.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] tareas del implementer `[x]` con su commit (T13+T13b en uno, declarado; T2, T18-T20 MANUAL/finales, no bloquean) ·
[x] sin temporales · [x] `features.json` refleja el estado.

## Mutación: verificación independiente

- **Recalculado** con `harness.alcance.alcance_de_feature` + `harness.mutacion.generar_mutantes` (cálculo puro): 21 ficheros,
  **1604 líneas, 284 mutantes**: igual que el informe, fichero a fichero.
- **Campaña no reejecutada: 3666 s (61 min) según el informe**; vale recálculo + RM1-RM6.
- **RM1:** SHA medido `9d9ebb1`; de ahí a `83c2d8d` solo cambian `progress/*` y `tasks.md`: el alcance medido es el revisado.
- **RM2:** total = 284 × 12,9 ✓; coste real media × W = 51,6 s frente a bases de 94,7-126,4 s, con 100 % muertos y `-x`: coherente.
- **RM3:** muestreados los 39 vivos de la primera pasada: ninguno es equivalente (cada uno cambia algo observable). 
- **RM4** (copia en el scratchpad, no en el árbol): re-aplicados 3 vivos de la primera pasada y corridos sus tests: mueren
  `lecturas_lote.py:197` `and`→`or` (`test_f055_r20_real_sin_obra_de_postventa_la_precarga_sigue`), `sigrid_write_client.py:95`
  `frozen=True`→`False` (`test_f055_r1_la_lectura_medida_es_inmutable`) y `prueba_escritura_porcentajes.py:314` `4`→`5`
  (`test_f055_r2_medir_lineas_porcentaje_tiempos_y_errores`).
- **JS manual:** reproducidas al pie de la letra J24, J30 y J08: **1 fallo cada una**, como dice la tabla.

## Cobertura requisito → test

| R | Tests |
|---|---|
| R1, R2 | `test_f055_medicion.py` (`r1_*`, `r2_*`), `test_f055_lecturas_lote.py::r1_la_medicion_sigue_a_los_hilos` |
| R3-R10, R12 | `test_f055_pipeline_partidas.py` (`r3`…`r10`, `r12`), `test_f055_validar_partidas.py` (`r3`, `r4`) |
| R11 | sin número propio: `r9_*` (postventa y VAR), `r20_compartidas_una_vez_por_lote`, `r20_postventa_y_real_…` y el plugin sobre `test_f039_preflight_var`/`test_f037_pipeline` (O1) |
| R13-R18, R27 | `test_f055_propuesta_guardada.py`; R14, R16, R26 en `test_f055_registro_lote.py` |
| R19-R25, C1, C2 | `test_f055_lote.py`, `test_f055_lecturas_lote.py`, `test_f055_cliente_agrupado.py` |
| R21 | plugin `f055_equivalencia_lote.py` (≥ 100 preflights y las propuestas) + lotes de varias obras |
| R34, C7 | `test_f055_propuesta_lote.py` |
| R29-R33, R35 | `test_f055_propuestas_mes.py` |
| R36, R27 (front) | `test_f055_propuesta_celda.py` (22) |
| R37 | `test_f055_propuestas_tras_escribir.py` |
| R38 | `test_f055_orden_propuesta.py` + `test_f050_r1_sin_paso1_va_al_paso2` |
| R28 | `test_f002_fuente_unica.py`, `tests/test_f004_readme.py` y lectura del diff de los docs (O1) |

## Observaciones no bloqueantes (para recoger, no para dejar en «anotado»)

1. **O1 · Trazabilidad por nombre.** R11 y R28 no tienen `test_f055_r11_*`/`r28_*`; están cubiertos (tabla). En la próxima
   feature, nombrar al menos un test por R aunque sea de «como hoy».
2. **O2 · «buscando partida…» de más.** Siguiendo design §5.6, mientras hay cola también lo enseñan líneas que nunca se encolan
   (postventa sin elegida, las de la memoria R32, obras de otra empresa) y vuelven a «automática» al acabar. R36 dice «en las
   pendientes». Cosmético; si molesta en T18, que la api publique qué línea está pendiente (el front no debe deducirlo).
3. **O3 · `lineas_de_partes` con > 500 recursos** (`sigrid_write_client.py`, trozos por recurso): dentro de un parte el orden
   deja de ser `pos` global, y el pipeline usa ese orden (`next(...)` de `cerrado`, orden de conflictos). Hoy hay ~196
   trabajadores: no se da; conviene ordenar al juntar o dejarlo anotado en ARCHITECTURE.
4. **O4 · Concurrencia real contra `sigrid-api`.** `SIGRID_LECTURAS_PARALELAS` acota **por lote**, no por proceso: un preflight
   del usuario y las propuestas en segundo plano a la vez llegan a 8. `INTEGRACION.md` §3 dice «a la vez contra `sigrid-api`»:
   precisar «por lote» al copiarlo a azure-apps (T15).
5. **O5 · Parada de la api.** El `ThreadPoolExecutor` de `propuestas_mes` no se cierra; al salir, Python espera al trozo en
   marcha (≤ 180 s). Aceptable en Azure; anotarlo en «Topología» o cerrar el ejecutor en el `shutdown`.
6. **O6 · Desviaciones de diseño a enseñar al humano** (rigor `critico`), escritas en el informe y no en `design.md`: T6
   validación e historial en la ronda B (no A), y T12 `empresa` = `EMPRESA_IMPUTACION` en vez de `obra_empresa` (coherente con
   el selector y el registro). Las doy por buenas; el líder debe decírselas al humano en el resumen de cierre.
7. **O7 · Estilo.** `tests/f055_equivalencia_lote.py` (`_propuesta_en_lote`): `limite=4)             .proponer(` es una
   continuación de línea rota (válido, feo). Avisos nuevos de ruff en tests nuevos (ISC004, RUF059, PLW1510).
8. **O8 · `progress/mutacion_F-055_pasada1.md`** conserva 39 secciones «Análisis (PENDIENTE del implementer)». Su cabecera dice que
   es la primera pasada y el informe las resuelve, pero una línea bajo la cabecera («resueltos en `9d9ebb1`, ver impl §T16»)
   evitaría que un lector o una herramienta lo tome por pendiente.
9. **O9 · `impl_F-055.md`** sin la primera línea `<!-- progress/impl_F-055.md -->` (sí la llevaba `impl_F-050.md`; cabe: 210/220).

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4: aclarar si un requisito «como hoy» (R11) o documental (R28) puede trazarse a tests sin su número
cuando los cubren suites sin cambios; hoy cada reviewer lo decide a su manera.
