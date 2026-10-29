<!-- progress/impl_F-064.md -->
# F-064 · informe del implementer

El pisado de los recursos vinculados sale confirmado por defecto en el modal
de registro. `sdd: false`, rigor estándar, solo front (más un cambio en un
test del transfer, opción 1 del humano). Rama
`feature/F-064-pisado-vinculados-marcado`, worktree `porcentajes-f064`.

## Qué cambió

| Commit | Tarea | Ficheros |
|---|---|---|
| `fef5ec4` | T1 · casilla marcada por defecto + tests | `services/dedicacion-front/static/js/app.js`, `services/dedicacion-front/tests/test_f064_pisado_vinculados.py` (nuevo) |
| `9062a9b` | T2 · enmienda de F-044 | `specs/F-044-recursos-vinculados/requirements.md` (nota en R20 y R31) |
| `0360ed8` | bloqueo (choque con F-013 R4) | `harness/features.json`, `BACKLOG.md`, `progress/` |
| `3afebc1` | T3 · opción 1: `marcadaPorDefecto` | `app.js`, `test_f064_pisado_vinculados.py`, `services/dedicacion-transfer/tests/test_f013_sin_partida.py`, `features.json`, `BACKLOG.md` |
| `d54bd3f` | review 1: B3 y O2 | `test_f064_pisado_vinculados.py`, `specs/F-044-recursos-vinculados/requirements.md` |
| (este) | review 1: B1, B2, O1 | `progress/mutacion_manual_F-064.md` (nuevo), `progress/current.md`, este informe |

En `app.js`:

- `registro` gana `vistas: new Set()`, las claves que `marcadaPorDefecto`
  señala y ya se han enseñado en este modal.
- `registroPreflight`: un preflight nuevo vacía `pisar` **y** `vistas`, así
  que al abrir el modal otra vez se vuelve al valor por defecto.
- `const marcadaPorDefecto = (c) => {…}`, una función pura: devuelve
  `Boolean(c.vinculado) && (c.motivo || "pisado") === "pisado"`.
- `pintarModalPreflight`, en el bucle de conflictos: si
  `marcadaPorDefecto(c)` es cierto y la clave no está en `vistas`, la clave
  se añade a `vistas` y a `pisar`, y la casilla sale `checked`.
- `repreflightPartida` y `registroEjecutar` **no cambian**. El primero
  sigue releyendo del DOM las casillas marcadas antes de repintar, y el
  segundo manda en `pisar_claves` las casillas marcadas.

En `test_f013_sin_partida.py` (transfer) el **único** cambio es que el cuerpo
de `marcadaPorDefecto` también se excluye de lo que se comprueba «fuera»,
igual que `rotuloConflicto`. Lleva un comentario que cita F-064. Las demás
aserciones siguen igual.

El código del transfer y el de la api no cambian, y no cambia ningún otro
test existente.

## Decisiones

- **Sin motivo cuenta como pisado**, igual que en `rotuloConflicto`, que lo
  rotula «Pisar». Un motivo vacío (`""`) también cuenta como pisado. Un motivo
  que el front no conoce (rotulado «Confirmar») **no** se marca.
- **`const` en vez de `function`, justo detrás de `pintarModalPreflight`.**
  Los arneses antiguos (`test_f049_avisos_registro`,
  `test_f049_ampliacion_registro`, y `test_f044_vinculados_front` a través
  de `test_f050_modal_registro.MODAL`) extraen `pintarModalPreflight` por
  nombre hasta la siguiente `function` de primer nivel. Con una `function`
  aparte, esos arneses darían `ReferenceError` y habría que tocarlos. La
  `const` va dentro de esa extracción, así que ningún arnés cambia. Sigue
  siendo una función pura y con nombre.
- **Los comentarios no usan la palabra «pisado»** fuera de `rotuloConflicto`
  y `marcadaPorDefecto`, porque el test de F-013 R4 también lee los
  comentarios.
- `vistas` solo guarda claves de `marcadaPorDefecto`. Una clave de vinculado
  que desaparece y vuelve al repetir el preflight ya cuenta como vista: sale
  como la dejó el humano, sin volver a marcarse.
- Repetir el preflight de una obra no toca las casillas de las demás obras,
  porque su estado se relee del DOM.

## Fase RED (T1, antes de tocar `app.js`)

Comando, desde `services/dedicacion-front`:
`.venv/Scripts/python.exe -m pytest tests/test_f064_pisado_vinculados.py -q --tb=line`

```
F.FFFFFFF                                                                [100%]
E   AssertionError: assert [] == ['10|202609|3...609|31|81002']
      Right contains 2 more items, first extra item: '10|202609|31|81001'
...test_f064_pisado_vinculados.py:178: AssertionError
E   assert '<input type="checkbox" class="chk-pisar" value="10|202609|31|81001" checked>' in '<h2>Registrar en Sigrid · sep 2026</h2>...
...test_f064_pisado_vinculados.py:197
E   AssertionError: assert ['77|202609|31|80002'] == ['11|202609|3...609|31|80002']
      At index 0 diff: '77|202609|31|80002' != '11|202609|31|81002'
      Right contains 2 more items, first extra item: '14|202609|31|81004'
...test_f064_pisado_vinculados.py:219
E   AssertionError: assert [] == ['10|202609|31|81001']
...test_f064_pisado_vinculados.py:233
E   AssertionError: assert [] == ['10|202609|3...609|31|81002']
...test_f064_pisado_vinculados.py:249
E   AssertionError: assert [] == ['10|202609|3...609|31|81002']
...test_f064_pisado_vinculados.py:260
E   AssertionError: assert ['77|202609|3...a:12|2026-09'] == ['10|202609|3...a:12|2026-09']
      At index 0 diff: '77|202609|31|80002' != '10|202609|31|81001'
...test_f064_pisado_vinculados.py:275
E   AssertionError: R20
    assert 'Enmienda F-064 (2026-10-26)' in '- **R20.** `[D6]` Identidad de `#regla-conflicto` ...
...test_f064_pisado_vinculados.py:290
8 failed, 1 passed in 2.73s
```

En RED pasa `test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado`, que
fija que sin vinculados no cambia nada. En la fase RED el test de F-013 R4
daba `AssertionError: pisado` (el detalle del bloqueo está en
`progress/current.md`). Tras T3 pasa: `42 passed` en `test_f013_sin_partida.py`.

## Tests (`test_f064_pisado_vinculados.py`, 11; sin red ni BBDD)

Usan el código real en node: `registroPreflight`, `repreflightPartida`,
`pintarModalPreflight` (con `marcadaPorDefecto`), `unirPreflight` y
`registroEjecutar`, con un DOM y una api de mentira. Las casillas se leen del
HTML pintado y el escenario las marca o desmarca como lo haría el humano.

| Acceptance | Tests |
|---|---|
| 1 · al abrir, solo sale marcado el pisado de vinculado | `al_abrir_solo_el_pisado_de_vinculado_sale_marcado` (trabajador, sobrecarga y sin partida de los dos, motivo desconocido y cierre de racha F-062 desmarcados), `sin_vinculados_el_modal_de_hoy_todo_desmarcado`, `la_casilla_marcada_lleva_checked_en_el_html`, `marcada_por_defecto_solo_el_pisado_de_vinculado` (11 casos), `marcada_por_defecto_es_pura_y_la_usa_el_modal` |
| 2 · desmarcada al repetir; la nueva sale marcada; un preflight nuevo vuelve al valor por defecto | `desmarcada_sigue_desmarcada_al_repetir_el_preflight` (dos repeticiones y una clave nueva), `repetir_una_obra_no_toca_lo_desmarcado_en_otra`, `un_preflight_nuevo_vuelve_al_valor_por_defecto` |
| 3 · `pisar_claves` lleva exactamente las marcadas | `registrar_por_defecto_manda_los_pisados_de_vinculado`, `registrar_manda_exactamente_las_marcadas` (cuerpo real de `/registro/ejecutar`) |
| 4 · enmienda en R20 y R31 | `enmienda_anotada_en_r20_y_r31_de_f044` (una sola nota bajo R31 que cita R20 y R31) |
| 5 · `init.sh` en verde | ver abajo |

## Mutación manual del JS

`harness.mutacion` solo muta Python. La campaña reproducible está en
**`progress/mutacion_manual_F-064.md`**: medida sobre `d54bd3f`, con la
versión final de `app.js`, sobre copias y en serie (1 worker), con línea base
`38 passed` y 214,6 s. Trae una fila por mutante con `app.js:línea`, el texto
exacto original → mutado y el nº de fallos, más el script que la reproduce.
Resultado: **15 mutantes, 15 muertos, 0 supervivientes**, incluidos el R1 y el
R2 de la review (M9 y M3). M15 solo lo mata
`test_f044_r31_sus_avisos_en_la_lista_de_siempre_con_tipo_y_codigo`; el
análisis está en ese fichero.

## Arreglos de la review 1 (`progress/review_F-064.md`, 2026-10-27)

- **B3** (`d54bd3f`): `_conflicto` pone siempre la clave `vinculado`, con
  `null` en el conflicto de un trabajador, igual que el `asdict` real del
  transfer. Antes la omitía y sobrevivía `c.vinculado !== undefined`, que
  marcaría por defecto el pisado del trabajador. Ahora lo matan seis tests.
  En el unitario hay dos casos: el trabajador con `null` y el conflicto sin
  la clave (`{"clave": "z"}`, transfer anterior a F-044).
- **B1**: `progress/mutacion_manual_F-064.md`, en el formato de F-042 (ver
  arriba).
- **B2**: la MANUAL del navegador está en «⚠ Lo que espera al humano» de
  `progress/current.md`, con dos caminos: (A) en local y en modo pruebas,
  con las comprobaciones previas `/health`, `transfer_base_url`,
  `True 0404` y «MODO PRUEBAS», y los pasos de qué sale marcado, que lo
  desmarcado sigue así tras cambiar una partida y que `pisar_claves` lo
  respeta; (B) tras desplegar, solo mirar el modal y pulsar Cancelar.
- **O1**: la sección de `current.md` se titula ahora «F-064 · bloqueo
  resuelto (opción 1) e implementación» y la cabecera la cita.
- **O2** (`d54bd3f`): las dos notas de enmienda de F-044 pasan a una sola
  línea bajo R31 que cita R20 y R31. El texto de F-044 no cambia y su
  requirements queda en **150/150** (`python -m harness.tamano --feature
  F-044`). El test de la enmienda comprueba esa única nota.
- `app.js` y el test de F-013 no cambian en esta vuelta (O3 de la review).

## Pendiente (MANUAL)

- La comprobación en el navegador, en `progress/current.md` («⚠ Lo que
  espera al humano», F-064). Nadie la ha ejecutado.

## Fuera del alcance

- El transfer y la api (cada vinculado sigue necesitando su clave, R20; R18
  sin cambios) y `azure-apps` (no cambia lo que se expone ni lo que se
  consume).

## Entorno

El worktree no traía los `.venv` de los servicios y `init.sh` daba [KO] de
entrada. Los enlacé con *junction* a los de la copia principal, como en los
demás worktrees. No se versionan (`.gitignore`). No he leído ni copiado
ningún `.env`.

## Evidencias

`bash harness/init.sh` tal cual, tras borrar `.arnes_cache/suite_*.ok`
(2026-10-27, tras los arreglos de la review 1), termina en «ENTORNO LISTO»,
sin [KO]:

| Evidencia | Valor real |
|---|---|
| Tests de la raíz | 418 passed, 1 skipped en 67,56 s |
| Tests de la api | 1308 passed en 128,65 s |
| Tests del front | 414 passed en 74,48 s (11 de F-064) |
| Tests del transfer | 1585 passed en 43,43 s |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: N/A` (F-064 no cambia líneas Python de producción; solo JS y tests) |
| Mutantes | `harness.mutacion` no aplica: no hay Python de producción. Campaña manual del JS (`progress/mutacion_manual_F-064.md`, `d54bd3f`, 1 worker, 214,6 s): 15 generados, 0 supervivientes |
| Tamaño | `PUERTA TAMAÑO: impl 184/220` (`python -m harness.tamano --feature F-064`, con este informe) |
