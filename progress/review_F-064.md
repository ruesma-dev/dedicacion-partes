<!-- progress/review_F-064.md -->
Revisión incremental desde 3492abe (pasada 2): delta `3492abe..f60aea1`

# F-064 · Review 2 · **APROBADO** (APPROVED)

La pasada 1 (`0d08c91`, en el historial de este fichero) revisó la feature
entera (`e9ca262..3492abe`) y la rechazó por B1 (campaña manual
irreproducible), B2 (MANUAL fuera de `current.md`) y B3 (superviviente R2 por
un doble de datos sin la forma real). Lo que aprobó entonces queda dado por
bueno: `app.js`, el cambio del test de F-013 R4, los acceptance 1-3 con sus
tests y la fase RED.

**Nivel de rigor:** `estandar`, declarado. Exige fase RED, cobertura de las
líneas cambiadas y mutación con los supervivientes analizados. Con `sdd:
false` se valida contra los 5 `acceptance`.

## Alcance del delta

- `git diff 3492abe..HEAD -- services specs`: solo
  `services/dedicacion-front/tests/test_f064_pisado_vinculados.py` y
  `specs/F-044-recursos-vinculados/requirements.md`. **`app.js` y
  `test_f013_sin_partida.py` no cambian**, y tampoco el código del transfer ni
  el de la api.
- El resto es rastro: `progress/current.md`, `progress/impl_F-064.md` y
  `progress/mutacion_manual_F-064.md` (nuevo).
- Lo aprobado sigue en pie: no cambian firmas ni código de producción y no se
  mueve ningún fichero. `git diff d54bd3f..HEAD -- services specs` sale
  vacío, así que la campaña, medida en `d54bd3f`, mide el HEAD revisado
  (RM1).

## Verificación del reviewer

- Borré `.arnes_cache/suite_*.ok` y ejecuté `bash harness/init.sh` solo, en
  el worktree. Exit 0, «ENTORNO LISTO», ningún [KO]. Raíz: 418 passed y
  1 skipped. Api: 1308. Front: 414. Transfer: 1585. `PUERTA COBERTURA: N/A
  (F-064 no cambia líneas Python de producción frente a dev)`. `PUERTA
  TAMAÑO: impl 184/220`. Cuadra con «Evidencias». `git status` queda limpio.
- **Campaña manual entera reproducida.** Copié el bloque del informe tal cual
  a mi scratchpad y lo lancé desde la raíz del worktree. Línea base: `38
  passed`. **Las 15 filas salen idénticas byte a byte** a las del informe
  (`diff` vacío): línea, texto original → mutado, resultado, nº de fallos y
  tests que lo matan. Tardó 145,8 s, frente a los 214,6 s declarados, y es
  coherente con su base de 9,09 s frente a mi 6,84 s.
- **R2, de forma independiente** (copia propia sin `.venv` ni `.env`;
  sustitución hecha por mí y no por el script):
  - `Boolean(c.vinculado)` → `c.vinculado !== undefined` contra la **suite
    entera del front**: **6 failed** y 408 passed. Los 6 son los de la fila
    M3.
  - El mismo mutante con el test de `3492abe`: los 10 tests de comportamiento
    **pasan**, y solo cae el de la enmienda, por el cambio de la nota. Así que
    lo que mata R2 es el arreglo B3, no otra cosa.
- El doble imita ya el `asdict` de `Conflicto.vinculado = None`
  (`registro_models.py:476`); el unitario cubre además `{"clave": "z"}`.
- **MANUAL (B2).** Los comandos citan nombres reales: `/health` publica
  `modo_pruebas`, `obra_pruebas` y `database` (`app.py:372-374`);
  `obra_pruebas_forzar`, `obra_pruebas_cod` y `transfer_base_url` existen en
  sus `settings`; `prueba_escritura_porcentajes.py` acepta `estado`,
  `limpiar`, `--ano`, `--mes`, `--confirmar` y `--permitir-modo-real`. El
  paso de cerrar y reabrir el modal es un preflight nuevo: el botón llama a
  `registroPreflight(null)` (`app.js:3388`).

## Bloqueos y observaciones de la pasada 1

| | Pedido | Estado |
|---|---|---|
| **B1** | Campaña manual reproducible | **Resuelto.** Hecho en `progress/mutacion_manual_F-064.md` con el formato de F-042: SHA, base, 1 worker y tiempo; una fila por mutante con `app.js:línea` y el texto exacto (único, el script aborta si no lo es); el bloque fuera del alcance de producción. Reproducido entero |
| **B2** | MANUAL en `current.md` | **Resuelto.** Está en «⚠ Lo que espera al humano». (A) es en local en modo pruebas, con 4 comprobaciones previas con PARAR y 4 pasos (marcado, desmarcado tras cambiar partida, `pisar_claves` y limpiar). (B) es tras desplegar: solo mirar y Cancelar |
| **B3** | Forma real del conflicto del trabajador | **Resuelto.** `_conflicto` pone siempre `"vinculado"`, con `null` para el trabajador. R2 (M3) muere con 6 fallos |
| **O1** | Título del bloqueo | **Resuelto.** «F-064 · bloqueo resuelto (opción 1) e implementación», y la cabecera lo cita |
| **O2** | Requirements de F-044 por encima del tope | **Resuelto**, con el matiz de la O1 nueva: 150/150 según `harness.tamano --feature F-044` |
| **O3** | Review 2 incremental | Aplicada |

## Checkpoints (sobre el delta)

- C1: [x] `init.sh` en exit 0. [x] Ficheros del arnés presentes.
- C2: [x] Una sola `in_progress`. [x] Rama de la feature. [x] `current.md` coherente: la cabecera dice «review 1 rechazada; arreglos
  hechos, pendiente de review 2», que es el estado real hasta este informe.
  [x] `history.md` sin pendientes (F-064 no es `done`).
- C3: [x] Hexagonal (el delta no toca producción). [x] Ruta en la primera
  línea de los ficheros tocados. [x] Sin prints, secretos ni dependencias.
  Las trampas del dominio son N/A justificado: ni escala, ni postventa, ni
  escritura en Sigrid.
- C3 bis: N/A justificado, no toca `docs/referencia/`.
- C4: [x] Los 5 `acceptance` tienen tests y pasan (tabla abajo). [x] Sin red
  ni BBDD. [x] La MANUAL está en `current.md` con sus comandos exactos y
  pendiente del humano.
- C4 bis:
  - [x] `rigor` declarado.
  - [x] Fase RED (aprobada en la pasada 1; el delta no la toca).
  - [x] Cobertura: N/A con el motivo impreso.
  - [x] Mutación automática: alcance `{}` y prueba de control (pasada 1).
  - [x] Campaña MANUAL con fila, línea y texto exacto. **Reproducidas las 15
    filas**, más R2 por separado.
  - [x] Cero supervivientes. M15 no se declara equivalente: lo mata un test
    de F-044, con análisis escrito.
  - [x] «Evidencias» trae los cuatro números, con workers y tiempo de la
    campaña.
  - RM1 [x]: `d54bd3f` mide lo mismo que HEAD. RM2 [x]: base frente a total,
    coherente. RM3 [x]: ningún equivalente sale muerto. RM5: N/A, por nivel
    (`estandar`). RM6: N/A, no se quita ninguna guarda.
  - N/A justificado: los 60 s, el coste por mutante y la base rota son de la
    campaña automática, que no aplica (no hay Python de producción).
- C4 ter: N/A, `init.sh` no señala rutas sensibles.
- C5: `tasks.md` es N/A justificado (`sdd: false`); los commits de tarea
  llevan `F-064 Tn:` y los de arreglo citan la review. [x] Sin temporales.
  [x] `features.json` dice `in_progress`, el estado real.

## Cobertura acceptance → test (`test_f064_pisado_vinculados.py`)

| Acceptance | Tests |
|---|---|
| 1 · al abrir | `al_abrir_solo_el_pisado_de_vinculado_sale_marcado`, `sin_vinculados_el_modal_de_hoy_todo_desmarcado`, `la_casilla_marcada_lleva_checked_en_el_html`, `marcada_por_defecto_solo_el_pisado_de_vinculado` (11 casos, `null` y sin clave incluidos), `marcada_por_defecto_es_pura_y_la_usa_el_modal` |
| 2 · repetir / nuevo | `desmarcada_sigue_desmarcada_al_repetir_el_preflight`, `repetir_una_obra_no_toca_lo_desmarcado_en_otra`, `un_preflight_nuevo_vuelve_al_valor_por_defecto` |
| 3 · `pisar_claves` | `registrar_por_defecto_manda_los_pisados_de_vinculado`, `registrar_manda_exactamente_las_marcadas` |
| 4 · enmienda | `enmienda_anotada_en_r20_y_r31_de_f044` (ver O1) |
| 5 · `init.sh` | verificado por el reviewer |

## Observaciones nuevas (no bloquean; recogerlas al cerrar)

1. **O1 · El acceptance 4, leído con holgura.** Dice «nota de enmienda en R20
   y R31». Para cumplir el tope de F-044, ahora hay **una** nota bajo R31 que
   cita R20 y R31. Quien lea R20 solo ya no ve la enmienda, y el test sigue
   llamándose `…anotada_en_r20_y_r31…`. En el fondo es defendible: R20 no
   cambia (cada vinculado sigue pidiendo su clave) y lo enmendado es el modal
   (R31). **Que el líder se lo diga al humano en la PARADA 2** como
   desviación literal del acceptance. Si no la acepta, habría que dejar una
   referencia en R20 sin pasar de las 150 líneas.
2. **O2 · Podar `current.md` al cerrar.** La sección de F-064 conserva en
   presente «Qué se rompe: init.sh en [KO]…» y las tres opciones del
   bloqueo. Hoy se lee como crónica, pero al cerrar debe pasar a
   `history.md` y no quedarse en `current.md`.

## Automejora (propuesta, no aplicada)

- En `docs/CONVENTIONS.md`, sección de tests: «**Un doble de datos que imita
  una respuesta de otro servicio lleva su forma serializada real**,
  opcionales a `null` incluidos, no un dict al que le faltan claves». Lo
  cazó B3: `c.vinculado !== undefined` sobrevivía porque el doble omitía la
  clave que `asdict` siempre manda. Vale para cualquier proyecto con
  front y backend separados, así que iría también a `arnes-base`.
