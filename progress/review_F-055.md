<!-- progress/review_F-055.md -->
Revisión incremental desde c872e87 (pasada 5, cierre) · `c872e87..9d46cb0`: solo rastro y docs (5 ficheros, 0 de código)

# F-055 · Review

## Pasada 5 (cierre) — **Veredicto: APROBADO** (APPROVED)

**Nivel de rigor:** `critico` (declarado en `features.json`): RED, cobertura, mutación con 0 vivos sin justificar y MANUAL
listadas. Lo aprobado hasta `c872e87` queda dado por bueno; el delta no toca código, firmas ni el alcance de la campaña.
Rama `feature/F-055-preflight-rapido` comprobada; árbol limpio antes y después.

**init.sh** (cachés `suite_*.ok` borradas, ejecutado solo, salida a un log del scratchpad): exit 0, `ENTORNO LISTO`,
**0 `[KO]`**; raíz 418 + 1 skipped, api 874, front 291, transfer 932; `PUERTA COBERTURA` 100 % de 809 líneas;
`PUERTA TAMAÑO` requirements 149/150, design 250/250, impl 220/220.

**Los cuatro cambios de la pasada 4:**
1. **T2 / «antes» de C6** [x]: salida b). `tasks.md:17` T2 a `[x]` con la renuncia, cita («lo desplegamos y despues
   mido») y fecha; `requirements.md:143` C6 = C3 y C4 **después** de desplegar con sus umbrales absolutos. Grep de «C6»,
   «antes y después», «antes de desplegar» y «producción» en spec, `current.md` e informe: ningún sitio pide ya el «antes».
2. **`current.md`** [x]: cabecera (l. 7-8) y bloque T2 (l. 56-58) dicen «hecha en local, sin “antes” de producción por
   renuncia» con la cita; la MANUAL de producción (l. 58 y 60-62): preflight de GONZALEZ PANIAGUA y del mes, Cancelar,
   ≤ 30 s y mes ≤ 60 s sin 502; pantalla del modal y O2, al humano en real (l. 27-28).
3. **`impl_F-055.md:28`** [x]: en pasado («se paró y se repropuso; el humano subió C8 a ≤ 60 s», con cita y fecha).
4. **`docs/INTEGRACION.md:202` y `:501`** [x]: «por lote, no por proceso», igual que `azure-apps/dedicacion.md` (O4).

**Barrido de datos sensibles** (diff `c872e87..HEAD`; correo, IPv4, GUID, `password|passwd|secret|token|apikey|api_key|
AccountKey|sig=|Bearer`): 0 coincidencias. `grep "^- \[ \]" tasks.md`: vacío. Commits `F-055: …` (rastro del líder).

**Checkpoints:** C1 [x]; C2 [x] (una sola `in_progress`, rama correcta, `current.md` de la sesión activa); C3 [x] (sin
código nuevo; lo de las pasadas 1-3); C3 bis N/A (no toca `docs/referencia/`); C4 [x] (requisitos trazados, abajo;
MANUAL C6 en `current.md`); C4 bis [x] (sin cambios de código desde la pasada 3: RED, cobertura 100 %, mutación 284/284 +
T17b 9/9, RM1-RM6 como allí; RM5 N/A, ningún equivalente declarado); C4 ter N/A (sin `harness/rutas_sensibles.json`);
C5 [x] (todas las tareas `[x]`).

**Para el cierre (líder, en el mismo commit que pone `done`):** el `acceptance` 1 de `features.json` sigue diciendo
«medición … (local y producción)»; anotar en la descripción de F-055 la renuncia del humano del 2026-10-17 al «antes» de
producción y que la medición de producción es el «después» de C6, y decir en la MANUAL de `current.md` dónde se anota su
resultado (`impl_F-055.md` o «Producción, hoy»). No bloquea: la renuncia ya consta en spec, tareas y rastro.

---

## Pasada 4 (`3a87726..d9569d5`, cierre) — RECHAZADO

init.sh en verde sin cachés (mismas cifras). C8 a ≤ 60 s, T19 sustituida, T20 y T15 (`azure-apps` `b6e35fa`) correctos.
Cuatro cambios, resueltos en la pasada 5: 1) T2 en `[ ]` sin su parte de producción (el «antes» de C6, irrecuperable tras
desplegar): medir antes o renuncia escrita del humano; 2) `current.md` decía «T1-T20 hechas» y «T2: hecha»; 3)
`impl_F-055.md:28` acababa en «PARA»; 4) `docs/INTEGRACION.md:202`/`:501` sin «por lote, no por proceso» (O4).

---

## Pasada 3 (`4c8d3f0..9f5530f`, correcciones de la pasada 2) — APROBADO

init.sh en verde sin cachés (raíz 418 + 1 s, api 874, front 291, transfer 932; cobertura 100 % de 809). Lista cerrada: solo
cambian `test_f055_propuestas_mes.py` y `test_f055_cliente_agrupado.py` (un test nuevo cada uno).
1. **Pos nulo** [x]: `test_f055_r20_lineas_de_partes_pos_nulo_primero_como_sql_server` mata `or 0` → `or 1` (1 fallo,
   reproducido); no es equivalente (RM3).
2. **Campaña reproducible** [x]: `progress/mutacion_T17b_F-055.md`, 9 filas con texto exacto. Reproducidas en copia de
   `9f5530f` en el scratchpad 7: los 5 del generador (fallos 1, 1, 2, 1, 3) y las manuales `self._parada.set()` → `pass` y
   `break` → `pass` (1 fallo cada una). Las del `lifespan`, `test_f055_r30_la_api_cierra_la_cola_al_pararse`. RM6: nada
   defensivo quitado.
3. **`cerrar()`** [x]: `threading.Event` mirado **entre trozos** (claves fuera de la cola en el `finally`, R33); docstring
   e informe ya dicen lo que pasa. Test `test_f055_r30_cerrar_deja_acabar_el_trozo_y_no_empieza_otro`.

## Pasada 2 (T17b, `101f5d7..dd38610`) — RECHAZADO

init.sh en verde (api 873, transfer 931; cobertura 100 % de 804). O3 (`sigrid_write_client.py:589-626`, orden `pos` al
juntar trozos), O5 (`cerrar()` + `lifespan`) y O7-O9 correctos salvo:
1. Vivo `sigrid_write_client.py:623` `int(f["pos"] or 0)` → `or 1` (79 passed): no equivalente, SQL Server pone `NULL`
   primero. Generador del arnés sobre `b3e5373..dd38610`: 5 mutantes (`propuestas_mes.py:66` ×2, `:623` ×2, `:625`), 4
   muertos.
2. Campaña manual «9/9» sin tabla de texto exacto: irreproducible (C4 bis).
3. Docstring de `cerrar()` falso: el `atexit` de `concurrent.futures` hace `join` y la tarea en marcha seguía con todos
   sus trozos (comprobado en el scratchpad: script 0,2 s, proceso 3,4 s).
Los tres, resueltos en la pasada 3.

## Pasada 1 · completa sobre `83c2d8d` (`git diff dev...HEAD`) — APROBADO, sin bloqueos

init.sh en verde (raíz 418 + 1 s, api 871, front 291, transfer 930; cobertura 100 % de 795 líneas).

**Lista CERRADA:** leído el diff de los 15 tests anteriores que cambian; aserciones cambiadas todas listadas
(`test_f003_r8_…`, `CAMPOS_LINEA`/`CAMPOS_CUADRANTE`, los dos `test_f049_d_*`, `test_f050_r1_sin_paso1_va_al_paso2`,
`test_f029_r25_…`); el resto, solo dobles (`conftest.py`, `ClienteFalso` de `test_pipeline_offline.py`, `SIN_PROPUESTA` de
`test_f050_partida_linea.py`, `_fila`/`_Transfer` de f022/f024/f026/f039, fixture `api` de f024, `_Uow`/`_cliente` de f050).

**Comprobado en el código:** D9/R29/R37 (`_encolar` tras cerrar la UoW en las seis escrituras; no encola a otros
trabajadores); D10/R38 (`previa_en_obra` → `resolver_normal` → `ultima_de_recurso`, mismo módulo en selector, preflight y
R34); R3-R12 (una `validar_partidas` por petición; presupuesto e historial solo con pendientes; R5, R6, R8); concurrencia
(un hilo en la api, cola por `(periodo, trabajador, obra)` bajo `Lock`; un solo vuelo y `copy_context` en el transfer; R31
por `UPDATE … partida_ide IS NULL AND propuesta_ide IS NULL`); front solo pinta. Desviación de T1 en design §5.1, aceptada.

**Checkpoints (pasada 1):** C1 [x]; C2 [x]; C3 [x] (ORM en `application` como `_trazar`); C3 bis N/A; C4 [x]; C4 bis [x]
(RM5 N/A: ningún equivalente); C4 ter N/A; C5 [x] (MANUAL pendientes, no bloqueaban entonces).

**Mutación T16, verificada:** recálculo puro 21 ficheros, 1604 líneas, **284 mutantes** = informe. Campaña no reejecutada
(3666 s según el informe). RM1: medida en `9d9ebb1`, después solo `progress/*` y `tasks.md`. RM2: 284 × 12,9 = total; media
× 4 workers = 51,6 s frente a bases de 94,7-126,4 s, 100 % muertos con `-x`: coherente. RM3: los 39 vivos de la primera
pasada no eran equivalentes. RM4: `lecturas_lote.py:197`, `sigrid_write_client.py:95`, `prueba_escritura_porcentajes.py:314`
re-aplicados: mueren. JS manual: J24, J30 y J08 reproducidas al pie de la letra (1 fallo cada una).

**Cobertura requisito → test:** R1-R2 `test_f055_medicion`; R3-R10, R12 `test_f055_pipeline_partidas`, `…_validar_partidas`;
R11 sin número propio (`r9_*`, `r20_compartidas_…`, plugin sobre f039/f037); R13-R18, R27 `test_f055_propuesta_guardada`;
R14, R16, R26 `test_f055_registro_lote`; R19-R25, C1, C2 `test_f055_lote`, `…_lecturas_lote`, `…_cliente_agrupado`; R21
plugin; R34, C7 `test_f055_propuesta_lote`; R29-R33, R35 `test_f055_propuestas_mes`; R36 `test_f055_propuesta_celda`; R37
`…_tras_escribir`; R38 `test_f055_orden_propuesta`; R28 `test_f002_fuente_unica`, `test_f004_readme` y lectura de los docs.
C3-C5, C8: MANUAL (T18, `impl_F-055.md`); C6: producción (cambio 1 de la pasada 4).

**Observaciones** (aprobadas por el humano el 2026-10-16): O1 trazar R11/R28 por nombre (arnés, aparte); O2 «buscando
partida…» en líneas que no se encolan (lo juzga el humano en real); O3 y O5 (T17b, hechas); O4 por lote, no por proceso
(azure-apps hecho; INTEGRACION.md, cambio 4); O6 desviaciones T6 y T12, aprobadas; O7-O9 (T17b, hechas).

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4: aclarar cómo se traza un requisito «como hoy» (R11) o documental (R28) sin test con su número.
- `reviewer.md`/C4 bis: una mutación **manual de código Python** también exige la tabla de texto exacto, y si el generador
  del arnés da mutantes en esas líneas, el reviewer los corre (aquí cazó un vivo que el «9/9» no tenía).
- `CHECKPOINTS.md` C5 (nuevo, pasada 4): antes del cierre, `grep -n "^- \[ \]" specs/F-XXX*/tasks.md` debe salir vacío y
  toda MANUAL «antes/después de desplegar» debe tener su «antes» hecho **o** renunciado por escrito antes de la review de
  cierre. Aquí T2 llegó a la pasada 4 en `[ ]` con `current.md` diciendo «T1-T20 hechas».
