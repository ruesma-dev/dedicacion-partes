<!-- progress/review_F-055.md -->
Revisión incremental desde 4c8d3f0 (pasada 3) · `4c8d3f0..9f5530f` (correcciones de la pasada 2 sobre T17b)

# F-055 · Review

## Pasada 3 — **Veredicto: APROBADO** (APPROVED)

**init.sh** (cachés `suite_*.ok` borradas, ejecutado solo): `ENTORNO LISTO`, exit 0, ningún `[KO]`; raíz 418 + 1 s, api 874,
front 291, transfer 932; `PUERTA COBERTURA` 100 % de 809 líneas; tamaño OK.
**Lista cerrada:** solo cambian `test_f055_propuestas_mes.py` y `test_f055_cliente_agrupado.py` (un test nuevo cada uno, de
F-055); ningún test anterior tocado. [x] `6867360..4c8d3f0` es solo `current.md` del líder.
1. **Pos nulo** [x]: `test_f055_r20_lineas_de_partes_pos_nulo_primero_como_sql_server` (nulo del 2.º trozo antes que `pos = 1`
   del 1.º). Mata `or 0` → `or 1` (1 fallo, reproducido); no es equivalente (RM3).
2. **Campaña reproducible** [x]: `progress/mutacion_T17b_F-055.md`, 9 filas con texto exacto y fallos. Reproducidas en una
   copia de `9f5530f` en el scratchpad **las 7** que puedo regenerar: los 5 del generador del arnés sobre
   `b3e5373..9f5530f` (fallos 1, 1, 2, 1, 3, como la tabla) y las manuales `self._parada.set()` → `pass` y `break` → `pass`
   (1 fallo cada una). Las del `lifespan` las cubre `test_f055_r30_la_api_cierra_la_cola_al_pararse`. 0 vivos. RM6: nada
   defensivo quitado.
3. **`cerrar()`** [x]: `threading.Event` que `_calcular` mira **entre trozos** (`break` dentro del `try`: las claves salen
   de la cola en el `finally`, como R33); docstring e informe dicen ya lo que pasa (el trozo en marcha acaba y Python lo
   espera al salir; el siguiente no empieza). Test `test_f055_r30_cerrar_deja_acabar_el_trozo_y_no_empieza_otro`
   (1 llamada, guarda la 1.ª obra y no la 2.ª, `en_curso` falso).
Rastro: `impl_F-055.md` §T17b y «Evidencias», `current.md` («en review 3») al día. Pendiente de cierre, como antes: T2
(navegador), T18-T20 MANUAL y T15 (azure-apps, líder); O2 y O4 según lo decidido por el humano.

---

## Pasada 2 · T17b — **Veredicto: RECHAZADO** (CHANGES_REQUESTED)

Lo aprobado en la pasada 1 (hasta `101f5d7`; `101f5d7..b3e5373` solo es rastro del líder) queda dado por bueno. Rigor
`critico`: cero supervivientes sin justificación aceptada por el humano y campaña manual reproducible.

**init.sh** (cachés `suite_*.ok` borradas, ejecutado solo): `ENTORNO LISTO`, exit 0, ningún `[KO]`: raíz 418 + 1 skipped,
api 873, front 291, transfer 931; `PUERTA COBERTURA` 100 % de 804 líneas; tamaño OK; ruff 258 avisos (no bloquea).

**Lista cerrada.** T17b solo toca tests de F-055 (`test_f055_*` y el plugin `f055_equivalencia_lote.py`); ninguna aserción
cambia salvo los dos tests nuevos. Ningún test anterior fuera de la lista. [x]

**Producción revisada.**
- **O3** `sigrid_write_client.py:589-626`: lee `hmores.pos` y ordena cada parte por `pos` al juntar trozos (estable). Bien, con
  test (`test_f055_r20_lineas_de_partes_en_varios_trozos_en_orden_pos`). Ver cambio 1: un mutante sobrevive.
- **O5** `propuestas_mes.py:62-67` `cerrar()` = `shutdown(wait=False, cancel_futures=True)` y `app.py` `lifespan` que la llama;
  dos tests. Cancela lo encolado, pero **el docstring dice «no espera al trozo en marcha» y no es cierto**: comprobado en el
  scratchpad (Python 3.12) que el `atexit` de `concurrent.futures` hace `join` del hilo, y la tarea en marcha (`_calcular`)
  sigue con **todos** sus trozos: proceso con una tarea de 3 × 1 s y otra encolada → el script acaba a 0,2 s, el proceso a
  3,4 s (la encolada sí se cancela). Ver cambio 3.
- **O7-O9**: continuación rota corregida, `noqa`/imports en tests nuevos, línea en `mutacion_F-055_pasada1.md`, cabecera
  del informe. [x]

**Mutación de T17b.** El informe dice «mutación manual … 9 mutantes: orden, `pos`, `shutdown`, `lifespan`: 9/9 muertos» sin
tabla: ni fichero:línea, ni texto exacto original → mutado, ni nº de fallos. **No es reproducible** (C4 bis: «sin ese texto
exacto el punto NO se marca»). Verificación propia (RM4, en una copia de `dd38610` en el scratchpad, nunca en el árbol):
`generar_mutantes` del arnés sobre las líneas de producción de `b3e5373..dd38610` da **5 mutantes**; corridos contra
`test_f055_propuestas_mes`, `…_tras_escribir` y `test_f024_rutas_empresa` (api) o `test_f055_cliente_agrupado`,
`…_lecturas_lote` y `test_f055_lote` (transfer):

| Fichero:línea | Original → mutado | Resultado |
|---|---|---|
| `propuestas_mes.py:66` | `shutdown(wait=False, …)` → `wait=True` | muerto (1 fallo) |
| `propuestas_mes.py:66` | `cancel_futures=True` → `False` | muerto (1 fallo) |
| `sigrid_write_client.py:623` | `int(f["pos"] or 0)` → `int(f["pos"] and 0)` | muerto (1 fallo) |
| `sigrid_write_client.py:623` | `int(f["pos"] or 0)` → `int(f["pos"] or 1)` | **VIVO** (79 passed) |
| `sigrid_write_client.py:625` | `key=lambda x: x[0]` → `x[1]` | muerto (2 fallos) |

`app.py` (lifespan) no genera mutantes del arnés; lo cubre `test_f055_r30_la_api_cierra_la_cola_al_pararse`.
**RM6:** T17b no quita ninguna guarda. **RM3:** el vivo **no** es equivalente: la suelta ordena en SQL Server, donde
`ORDER BY hmores.pos` pone los `NULL` **primero**; con `or 0` un `pos` nulo va antes que `pos = 1`, con `or 1` empata con él
y el orden depende del trozo. Hueco de test real en la línea que arregla O3.

### Cambios requeridos

1. **`sigrid_write_client.py:623` (vivo `or 0` → `or 1`).** Test nuevo en `test_f055_cliente_agrupado.py`: una línea con
   `pos = None` en el **segundo** trozo de recursos y otra con `pos = 1` en el primero, esperando la de `pos` nulo primero,
   como la suelta (`NULL` primero en SQL Server). Si se prefiere, clave `(-1 if pos is None else pos)` o `(pos is not None,
   pos or 0)` para que el criterio quede explícito; el test, en cualquier caso.
2. **Campaña de T17b reproducible.** Sustituir el «9/9» por una tabla con una fila por mutante (fichero:línea, texto exacto
   original → mutado, nº de fallos), que incluya **como mínimo los 5 del arnés de arriba** además de los manuales que se
   quieran (`lifespan`…), o pasar `python -m harness.mutacion --feature F-055 --ficheros <los 2 .py de producción con mutantes>`
   y enlazar su informe (fuera de `mutacion_F-055.md`, que es la pasada final de T16).
3. **`propuestas_mes.py:62-65` y `impl_F-055.md` §T17b: no afirmar lo que no pasa.** O se corrige el docstring («cancela lo
   encolado; la tarea en marcha termina sus trozos y Python la espera al salir del proceso») **o** se cumple de verdad: una
   bandera que `cerrar()` levanta y `_calcular` mira entre trozos (deja de pedir más; sus claves salen de la cola en el
   `finally`, como R33), con su test. La segunda opción acota la espera a un trozo (≤ 180 s); cualquiera de las dos vale.

Nada más: el resto de T17b es correcto. La pasada 3 mirará solo `dd38610..HEAD` (y repetirá init.sh entero).

---

## Pasada 1 · completa sobre `83c2d8d` (`git diff dev...HEAD`) — APROBADO, sin bloqueos

**init.sh** en verde (raíz 418 + 1 s, api 871, front 291, transfer 930; cobertura 100 % de 795 líneas; tamaño OK).

**Lista CERRADA:** leído el diff de los 15 tests anteriores que cambian. Aserciones cambiadas, todas listadas
(`test_f003_r8_…`, `CAMPOS_LINEA`/`CAMPOS_CUADRANTE`, los dos `test_f049_d_*`, `test_f050_r1_sin_paso1_va_al_paso2`,
`test_f029_r25_…`); el resto, solo dobles (`conftest.py`, `ClienteFalso` de `test_pipeline_offline.py`, `SIN_PROPUESTA` de
`test_f050_partida_linea.py`, `_fila`/`_Transfer` de f022/f024/f026/f039, fixture `api` de f024, `_Uow`/`_cliente` de f050).

**Puntos del líder, comprobados en el código:**
- D9/R29/R37: `_encolar` tras cerrar la UoW en las seis escrituras; `[ide]`, `payload.trabajadores` o todo el periodo (Copiar
  mes); `_lanzar` no encola a otros trabajadores. D10/R38: `previa_en_obra` → `resolver_normal` → `ultima_de_recurso`, mismo
  módulo en selector, preflight y R34; `#regla-partida` al día.
- R3-R12: una `validar_partidas` por petición; presupuesto e historial solo con pendientes; guardada válida se escribe tal cual
  (R8), inválida → pendiente (R6); elegida inválida → `MOTIVO_PARTIDA_NO_HOJA` (R5); fuera la lectura forzada de F-049 d.
- Concurrencia: un hilo en la api, cola por `(periodo, trabajador, obra)` bajo `Lock`; un solo vuelo (`Lock` + `Future`) y
  `copy_context` en el transfer; R31 por `UPDATE … partida_ide IS NULL AND propuesta_ide IS NULL`.
- Front: solo pinta; un `setTimeout` vivo, generación por mes/empresa, no repinta la fila en edición.
- Desviación de T1 en design §5.1 (ampliación `c59bcd6`); `SIN_COMPARAR` del plugin y C2 por estructura, aceptados.
- Rastro: `current.md`, `features.json` (`in_progress`, `critico`), `INTEGRACION.md`, README; T15 listada para el líder.

**Checkpoints:** C1 [x]; C2 [x]; C3 [x] (ORM en `application` como `_trazar`, `medir_lecturas` desde `infrastructure` como el
previo `synckey_de`); C3 bis N/A (no toca `docs/referencia/`); C4 [x]; C4 bis [x] (RM5 N/A: ningún equivalente; RM6 N/A en
pasada 1); C4 ter N/A (sin `harness/rutas_sensibles.json`); C5 [x] (MANUAL T2, T18-T20 pendientes, no bloquean la review).

**Mutación T16, verificada:** recálculo puro 21 ficheros, 1604 líneas, **284 mutantes** = informe. Campaña no reejecutada
(3666 s según el informe). RM1: medida en `9d9ebb1`, después solo cambian `progress/*` y `tasks.md`. RM2: 284 × 12,9 = total;
media × 4 workers = 51,6 s frente a bases de 94,7-126,4 s, 100 % muertos con `-x`: coherente. RM3: los 39 vivos de la primera
pasada no eran equivalentes. RM4: re-aplicados `lecturas_lote.py:197`, `sigrid_write_client.py:95` y
`prueba_escritura_porcentajes.py:314`: mueren. JS manual: J24, J30 y J08 reproducidas al pie de la letra (1 fallo cada una).

**Cobertura requisito → test:** R1-R2 `test_f055_medicion`; R3-R10, R12 `test_f055_pipeline_partidas`, `…_validar_partidas`;
R11 sin número propio (`r9_*`, `r20_compartidas_…`, plugin sobre f039/f037); R13-R18, R27 `test_f055_propuesta_guardada`;
R14, R16, R26 `test_f055_registro_lote`; R19-R25, C1, C2 `test_f055_lote`, `…_lecturas_lote`, `…_cliente_agrupado`; R21
plugin; R34, C7 `test_f055_propuesta_lote`; R29-R33, R35 `test_f055_propuestas_mes`; R36 `test_f055_propuesta_celda`; R37
`…_tras_escribir`; R38 `test_f055_orden_propuesta`; R28 `test_f002_fuente_unica`, `test_f004_readme` y lectura de los docs.

**Observaciones de la pasada 1** (aprobadas por el humano el 2026-10-16): O1 trazar R11/R28 por nombre (arnés, aparte); O2
«buscando partida…» también en líneas que no se encolan (lo juzga el humano en T18); O3 orden `pos` en `lineas_de_partes`
con > 500 recursos (T17b); O4 concurrencia por lote, no por proceso (al copiar a azure-apps, T15); O5 cerrar el ejecutor en el
`shutdown` (T17b); O6 desviaciones T6 (ronda B) y T12 (`EMPRESA_IMPUTACION`), aprobadas; O7 estilo; O8 nota en
`mutacion_F-055_pasada1.md`; O9 cabecera de `impl_F-055.md` (T17b).

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4: aclarar cómo se traza un requisito «como hoy» (R11) o documental (R28) sin test con su número.
- `reviewer.md`/C4 bis: una mutación **manual de código Python** (no solo JS) también exige la tabla de texto exacto, y si el
  generador del arnés da mutantes en esas líneas, el reviewer los corre (aquí cazó un vivo que el «9/9» no tenía).
