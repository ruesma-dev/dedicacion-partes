Revisión de evidencias desde 4aa8d7b
<!-- progress/review_F-074.md -->
# F-074 · Review, pasada de evidencias: APPROVED

**Veredicto: APPROVED** sobre `64bc0c2` (HEAD). La aceptación de los 12 equivalentes es del humano y queda como condición para pasar a `done` (H-E1).

Principal: **APPROVED en la pasada 2 sobre `4aa8d7b`** (la pasada 1 dio CHANGES_REQUESTED sobre `7f6ddc8`). Texto íntegro de las dos en `git show 64bc0c2:progress/review_F-074.md`. Se rehace el fichero entero para no pasar del tope de 140 líneas.

**Nivel `critico`** (declarado en `features.json`): fase RED, cobertura ≥ 90 %, mutación exigida (uno por línea, el 60 % de los candidatos acotado a [100, 300], 0 supervivientes sin justificación aceptada por el humano), RM1-RM7 y MANUAL con su comando. No hay `rigor.local.json`.

## Delta `4aa8d7b..64bc0c2`

- Cinco commits: `66d91e3` y `532b994` (dos ficheros de test nuevos) y tres de `progress/`.
- **Ni una línea de producción**: `git diff --stat` sobre `application/`, `domain/`, `infrastructure/`, `interface_adapters/` y `static/` sale vacío. Lo aprobado en la principal sigue valiendo.

## Portero

`ARNES_SIN_CACHE=1 bash harness/init.sh` en HEAD: **exit 0, 0 `[KO]`**, «ENTORNO LISTO». Raíz 2319 passed y 47 skipped; api 1692, front 611 y transfer 2011 (con los 4 nuevos). `PUERTA COBERTURA` 100 % (310/310), `PUERTA TAMAÑO` dentro de los topes (impl 203/220, review 99/140), `CAPA E2E` N/A. Medido sobre HEAD con este informe ya reescrito; no cambia código.

## C4 bis · mutación

- [x] **Informe generado por la herramienta**, sin «⚠ CAMPAÑA NO VÁLIDA» y con «Sin veredicto (base rota)» = 0, 0 timeouts y 0 indeterminados.
- [x] **Recalculado de forma independiente** con `harness.alcance.alcance_de_feature` y `generar_mutantes`:
  - 19 ficheros, 948 líneas y 202 mutantes, fichero a fichero igual que la tabla «Alcance».
  - Con `seleccionar` (regla del nivel, semilla 20261030) salen 133 candidatos, tope 100 y 100 elegidos. Los 100 coinciden uno a uno (fichero, línea, operador, texto) con los `evaluados` del `.json`: 88 muertos y 12 supervivientes.
- [x] **Incremental bien hecho:** `4aa8d7b` es antepasado de `671ac43` (`merge-base --is-ancestor`).
  - Entre los dos solo entran los dos ficheros de test. Añadir tests no resucita un muerto, así que los 75 reutilizados siguen valiendo.
  - La muestra de control (9) salió muerta: si un muerto de control revive, `harness/mutacion.py` (l. 4093-4103) descarta lo reutilizado y repite la campaña completa, y el informe saldría con «Modo» completo, no incremental.
- [x] **RM1:** se midió `671ac43…`. HEAD es `64bc0c2`, y `671ac43..HEAD` solo toca `progress/` (`current.md`, `impl_F-074.md` y los dos informes de mutación). Ningún fichero del alcance ni de las suites cambia. **Vale; no hay que volver a medir.**
- [x] **RM2:**
  - Las líneas base son 65,2-65,5 s (api) y 41,8-42,2 s (transfer). La media con la suite entera es de 63,2 s por mutante, del orden de la base.
  - La «Media por mutante evaluado» (26,6 s) es reloj de pared con 4 workers: 25 × 26,6 = 665 s, igual que el «Tiempo total» (665,6 s). No hay salto de orden de magnitud.
  - La campaña 1 (1321,7 s, 84/16) también cuadra.
  - Tiempo total > 60 s: **campaña no reejecutada entera** (11 min según el informe). En su lugar, reproducción en serie dirigida (abajo).
- [x] **RM3:** ningún equivalente sale muerto. Los 12 que declaro equivalentes son exactamente los 12 supervivientes.
- [x] **RM4 / RM5 (reproducción en serie):**
  - Hecha en una copia `git archive HEAD` en el scratchpad, con el venv de cada servicio, `PYTHONDONTWRITEBYTECODE=1` y `__pycache__` purgado.
  - Ojo: un mutante que no cambia el tamaño del fichero (`or 0` → `or 1`) deja un `.pyc` rancio al restaurar en el mismo segundo. Lo repetí todo limpio.
  - Suite entera del servicio con `-x`. **Los seis pasan enteros**, es decir, sobreviven:
    - transfer (2007 passed, 4 skipped): #6 `registro_pipeline.py:686`, #7 `:687`, #10 `registro_vinculados.py:289` y #11 `partida_definida.py:108`;
    - api (1692 passed): #1 `estado_partida.py:75` y #3 `schemas.py:486`.
  - Supera la muestra de uno que pide RM5.
- [x] **RM6:** la guarda «si sigue sin elegida» de `_borrar_no_validas` está intacta (`registro_sigrid.py` l. 553 `AsignacionORM.partida_ide.is_(None)` y l. 559 la de `AsignacionVinculadoORM`). El delta no toca producción. Además, neutralizada en la copia, cada una pone en rojo su test:
  - la de línea, `test_f074_r16_solo_si_sigue_sin_elegida`;
  - la de subfila, `test_f074_r16_la_subfila_que_no_vale_se_borra_si_viajo_con_guardada`.
  Ningún mutante se mató quitando código defensivo.
- [x] **RM7:** el orden de R15 (`routes.py` l. 458-470), probado en la copia con dos mutaciones, ambas en **rojo** con el propio test de F-074:
  - (a) **`_encolar` subido por encima del bloque `CambiarPartida`**: el olvido queda después del encolado. Falla `test_f074_r15_la_ruta_lo_cablea_antes_de_encolar`: `At index 0 diff: ('encolar', [10]) != ('olvidar', …)`.
  - (b) **el olvido diferido hasta después de `_encolar`**: falla el mismo test, primero por la identidad del callback.
  - El que cae es de F-074, no de una suite vecina.
- [x] **Los 4 tests nuevos** matan cada uno su mutante, aplicado en la copia y probado contra su fichero:

| Mutante | Test | Resultado |
|---|---|---|
| `partida_definida.py:81` `frozen=True→False` | `test_f074_mut_definida_del_vinculado_es_inmutable` | DID NOT RAISE FrozenInstanceError |
| `registro_pipeline.py:220` `"ide": 0→1` | `test_f074_mut_postventa_con_var_se_omite_sin_partida` | `('omitir', 1, None) != ('omitir', 0, None)` |
| `estado_partida.py:33` `frozen=True→False` | `test_f074_mut_las_marcas_son_inmutables` | DID NOT RAISE FrozenInstanceError |
| `schemas.py:154` `v is None→not v` | `test_f074_mut_subfila_solo_excluye_none` | `KeyError: 'propuesta_no_encontrada'` |

  No debilitan nada: son ficheros nuevos, sin cambios en tests existentes ni en producción, con ruta en la primera línea y en español. Los dos de inmutabilidad prueban una propiedad declarada del diseño (la foto de la cola y la decisión de la subfila no se retocan). El de `:220` fija una regla de negocio real (F-039 R6).
- [x] **Ficheros sin mutantes (4):** las declaraciones se sostienen (solo campos, columnas nulables y argumentos con nombre). Ninguna está en `PENDIENTE`.

## Los 12 supervivientes declarados equivalentes

«Puro» quiere decir que ninguna entrada los distingue. «Por dominio» quiere decir que solo los distingue una entrada que producción no puede generar: matarlos exigiría un test con un valor imposible, y eso no es un test razonable.

| # | Fichero:línea | ¿Equivalente? | Motivo (verificado en el código) |
|---|---|---|---|
| 1 | `api/application/estado_partida.py:75` | Sí, **por dominio** | `tiene` solo cambia con `obra_pv_ide == 0`. El valor sale del `ide` de una hoja de `obrparpar` (identidad de Sigrid, > 0), casada en `universo_postventa`. Lo mataría un test con `obra_pv_ide=0`, un valor imposible. Reproducido: sobrevive |
| 2 | `api/application/use_cases.py:405` | Sí, puro | `_al_borrar_subfilas` es None o un método ligado (siempre verdadero) |
| 3 | `api/interface_adapters/api/schemas.py:486` | Sí, puro | `Marcas` es una `@dataclass(frozen=True)` sin `__bool__` ni `__len__` (grep: ninguno en el alcance). Reproducido: sobrevive |
| 4 | `transfer/.../registro_pipeline.py:217` | Sí, puro | `ObraEntrada` es una dataclass sin `__bool__` ni `__len__`. Viene de `obra_de_postventa` (None u `ObraEntrada`) |
| 5 | `transfer/.../registro_pipeline.py:637` | Sí, puro | Ídem (#4) |
| 6 | `transfer/.../registro_pipeline.py:686` | Sí, **por dominio** | `vale_pv` solo se llama en l. 727, tras `int(a.paride)` (l. 724). `_definida_pv` solo deja `escribir` con `l.paride` o `propuesta_paride` verdaderos, y la VAR (ide 0) sale antes (l. 698-706). Además haría falta una partida de `ide` 1 en `validas`. El `or 0` es código defensivo muerto. Reproducido: sobrevive |
| 7 | `transfer/.../registro_pipeline.py:687` | Sí, puro | `PartidaValida` es congelada y siempre verdadera. Con None el mutante devuelve None en vez de False, y el único uso (l. 727) es `if not vale_pv(...)`. Reproducido: sobrevive |
| 8 | `transfer/.../registro_pipeline.py:781` | Sí, puro | Ídem (#4) |
| 9 | `transfer/.../registro_pipeline.py:1137` | Sí, puro | `Propuesta` es congelada y la devuelve `proponer_partida` (None o instancia). La l. 1135 ya usa `if p` |
| 10 | `transfer/.../registro_vinculados.py:289` | Sí, puro | Asignación muerta: con `guardada` None, `partida_definida_del_vinculado` (l. 123) no lee `guardada_valida`; con ella, se reasigna en l. 291. Reproducido: sobrevive |
| 11 | `transfer/.../partida_definida.py:108` | Sí, puro | `PartidaElegida` es congelada y siempre verdadera. Reproducido: sobrevive |
| 12 | `transfer/.../universo_postventa.py:59` | Sí, puro | `obra_por_codigo` está tipada `-> ObraEntrada \| None` (`sigrid_write_client.py:260`) |

**Juicio:** las 12 justificaciones se sostienen. Diez son equivalentes puros (#2-5 y #7-12) y dos lo son por dominio (#1 y #6). Ninguna se mataría con un test razonable. Para #6 hay una alternativa, que no pido: quitar el `or 0` de `vale_pv`, que hace desaparecer el mutante. Por RM6 no lo recomiendo sin verificar el invariante en el origen; ya está verificado arriba, pero es un cambio de producción con la feature ya medida.

## Rastro

- [x] `features.json`: F-074 `in_review`, rigor `critico`; `BACKLOG.md` igual.
- [x] La fila «Mutación» de la tabla «Evidencias» de `impl_F-074.md` coincide con los informes: 202/133/100; campaña 1 de 84/16 en 1321,7 s; incremental de 88/12 en 665,6 s, con 0 timeouts y 0 sin veredicto.
- [x] Los R1-R3 de la pasada 2 están corregidos en `current.md` l. 4: H6 en `c241cba`, «tamaño impl 203/220» y las automejoras.

## Hallazgos (ninguno bloquea; los dos primeros se corrigen antes de `human_review`)

1. **H-E1 · Los 12 equivalentes no están en «⚠ Lo que espera al humano»** (`current.md` l. 479 y siguientes): allí solo constan las MANUAL T15-T18 y `azure-apps`. En `critico`, sin la aceptación escrita del humano no se cierra la feature. Hay que añadir la entrada, con el enlace a esta tabla.
2. **H-E2 · `current.md` l. 4, «Pendiente:» está desfasado.** Dice «review contra `CHECKPOINTS.md`; tras el APPROVED, pasada de campaña de mutación». Las dos están hechas. Debe decir: aceptación de los 12 equivalentes, MANUAL T15-T18 y `azure-apps/dedicacion.md`.
3. **H-E3 (observación):** `harness/mutacion.py` evita el `.pyc` rancio con `_purgar_bytecode`. Un reviewer que reproduce mutantes a mano no lo tiene, y me pasó en esta pasada: el `or 0` → `or 1` restaurado en el mismo segundo dejó en rojo un test sano.

## Automejora (propuesta, sin aplicar)

- `reviewer.md`, RM4/RM5: «al reproducir mutantes a mano, `PYTHONDONTWRITEBYTECODE=1` y `__pycache__` purgado. Un mutante del mismo tamaño restaurado en el mismo segundo deja el `.pyc` del mutante». Vale para `arnes-base`.
- `CHECKPOINTS.md` C4 bis: distinguir en el análisis de supervivientes entre equivalente «puro» y «por dominio» (entrada imposible), para que el humano sepa qué acepta.
