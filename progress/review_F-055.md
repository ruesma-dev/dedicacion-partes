<!-- progress/review_F-055.md -->
Revisión incremental desde 3a87726 (pasada 4, cierre) · `3a87726..d9569d5`: solo `current.md`, `impl_F-055.md` y la spec

# F-055 · Review

## Pasada 4 (cierre) — **Veredicto: RECHAZADO** (CHANGES_REQUESTED)

**Nivel de rigor:** `critico` (declarado en `features.json`): RED, cobertura, mutación con 0 vivos sin justificar y MANUAL
listadas con su comando exacto y su resultado real. Lo aprobado hasta `3a87726` (código) queda dado por bueno:
`git diff --stat 3a87726..HEAD` = 5 ficheros, ninguno de código.

**init.sh** (cachés `suite_*.ok` borradas, ejecutado solo): `ENTORNO LISTO`, exit 0, **0 `[KO]`**; raíz 418 + 1 skipped,
api 874, front 291, transfer 932; `PUERTA COBERTURA` 100 % de 809 líneas; `PUERTA TAMAÑO` requirements 149/150, design
250/250, impl 220/220, review 136/140. Ruff 258 avisos (deuda previa, no bloquea).

**Lo pedido por el líder:**
1. **C8 a ≤ 60 s** [x]: `requirements.md:146` y `tasks.md:38` dicen ≤ 60 s con «humano, 2026-10-17; era 30»;
   `design.md:48` deja la estimación (≤ 30 s) **anotada** con lo medido (59 s) y el límite nuevo. El grep de «30 s» en la
   spec solo da C3 (≤ 30 s, que no cambia) y esa estimación anotada. Coherente.
2. **T19 sustituida** [x]: `tasks.md:39` y `current.md:58-60` con cita («eso es, probarlo en produccion») y fecha.
3. **T20** [x]: init.sh en verde, arriba.
4. **T15, azure-apps `b6e35fa`** [x] (rama `master`): cabecera «Pendiente de desplegar», §3 `SIGRID_LECTURAS_PARALELAS`
   **por lote, no por proceso** (O4 recogida), §5 contratos de `preflight-lote`, `propuesta-lote`, `…/propuestas`,
   `propuestas_en_curso`, columnas `propuesta_*` y timeouts, §7 dos filas (orden de despliegue y la variable). Coincide con
   `docs/INTEGRACION.md` y con el código (`settings.py:34`, defecto 4; trozos de 10). Ver cambio 4.
5. **current.md**: cabecera al día y despliegue autorizado anotado (líneas 10-11, «si», 2026-10-17), **pero** ver 1-2.
6. **Topes** [x]: los de arriba.

**Barrido de datos sensibles** (diff `3a87726..HEAD` + `b6e35fa`; patrones: correo, IPv4, GUID, `password|passwd|secret|
token|apikey|api_key|AccountKey|sig=|Bearer`): 0 coincidencias (fuera del `Co-Authored-By`).

**Checkpoints:** C1 [x]; C2 [x]; C3 [x]; C3 bis N/A (no toca `docs/referencia/`); C4 **[ ]** (la MANUAL de producción C6
no está descrita entera: falta su «antes», cambio 1); C4 bis [x] (sin cambios de código desde la pasada 3; RM1-RM6 como
allí); C4 ter N/A (sin `harness/rutas_sensibles.json`); C5 **[ ]**: `tasks.md:17` **T2 sigue `[ ]`**.

### Cambios requeridos

1. **T2 no está hecha: falta su parte de producción, que es el «antes» de C6.** `tasks.md:17` pide «en producción, lo
   mismo solo hasta el modal y Cancelar», y `requirements.md:143` define C6 como «C3 y C4 **antes y después** de
   desplegar». `impl_F-055.md` §T2 solo trae script y HTTP en local; ninguna cifra de producción. Es **irrecuperable tras
   desplegar**, y el plan es desplegar justo después de esta review. Dos salidas, a elegir por el humano:
   a) **Antes de desplegar**, medir en producción (F-050 desplegada): GONZALEZ PANIAGUA (0694 + 0696), 09/2026,
      «⇪ Sigrid» → modal cronometrado y el mes entero, **Cancelar**; cifras en `impl_F-055.md` §T2 y `T2` a `[x]`; o
   b) que el humano **renuncie** al «antes» de producción, con cita y fecha en `tasks.md:17` (y T2 a `[x]`) y en
      `requirements.md` C6, que pasa a medir solo el «después» contra los umbrales absolutos (≤ 30 s; mes ≤ 60 s, sin 502).
2. **`progress/current.md`**: línea 7 («T1-T20 hechas») y línea 55 («T2: hecha») no son ciertas mientras T2 esté `[ ]`.
   La MANUAL pendiente (líneas 58-60) debe describir C6 entera: si se elige 1a, el «antes» **como paso previo al
   despliegue** (líneas 10-11 y 65), y el «después» con sus umbrales (≤ 30 s y ≤ 40 % del antes; mes ≤ 60 s sin 502) y
   dónde se anotan; ahí mismo, lo que T18 dejó a esa prueba (pantalla del modal frente a T2 y O2).
3. **`impl_F-055.md:28`**: el párrafo T18 acaba en «→ **PARA**, se repropone» tras decir «OK»; quien lo lea después no
   sabe si sigue parada. Reescribir en pasado («se paró y se repropuso; el humano subió C8 a ≤ 60 s»).
4. **`docs/INTEGRACION.md:202` y `:501`**: no dicen «**por lote, no por proceso**» y `azure-apps/dedicacion.md` sí. La
   fuente es INTEGRACION.md: añadir la misma frase para que las dos no diverjan (O4).

La pasada 5 mirará solo `d9569d5..HEAD` (y repetirá init.sh entero). Si el delta solo toca rastro, es corta.

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
