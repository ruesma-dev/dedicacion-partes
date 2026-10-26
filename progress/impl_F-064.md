<!-- progress/impl_F-064.md -->
# F-064 · informe del implementer (BORRADOR: feature `blocked`)

> La feature está **bloqueada**: motivo y opciones en `progress/current.md`
> («F-064 · BLOQUEO»). Este borrador guarda lo hecho y la fase RED para
> retomarla; se completa (sección «Evidencias» con `init.sh` en verde) al
> desbloquear.

## Qué cambió (rama `feature/F-064-pisado-vinculados-marcado`)

- `services/dedicacion-front/static/js/app.js` (T1, `fef5ec4`):
  - `registro` gana `vistas: new Set()` (claves de pisado de vinculado ya
    enseñadas en este modal).
  - `registroPreflight`: con el preflight nuevo vacía `pisar` **y** `vistas`.
  - `pintarModalPreflight`, en el bucle de conflictos: si `c.vinculado` y el
    motivo es «pisado» (o falta, como en `rotuloConflicto`) y la clave no
    está en `vistas`, se añade a `vistas` y a `pisar` (sale `checked`).
  - `repreflightPartida` **no cambia**: sigue releyendo del DOM las marcadas
    antes de repintar; una desmarcada ya está en `vistas` y no se vuelve a
    marcar; una clave nueva sale marcada.
  - `registroEjecutar` **no cambia**: `pisar_claves` = casillas marcadas.
- `services/dedicacion-front/tests/test_f064_pisado_vinculados.py` (T1,
  nuevo, 9 tests): código real en node con DOM y api de mentira.
- `specs/F-044-recursos-vinculados/requirements.md` (T2, `9062a9b`): nota
  «Enmienda F-064 (2026-10-26): …» en R20 y R31.
- Transfer y api: sin cambios.

## Decisiones

- **Sin motivo = pisado**, igual que `rotuloConflicto` (que lo rotula
  «Pisar»): lo que el humano ve como «Pisar» de un vinculado sale marcado.
- Un motivo que el front no conoce (rotulado «Confirmar») **no** se marca.
- `vistas` solo guarda claves de pisado de vinculado: los arneses de tests
  antiguos que montan su propio `registro` sin `vistas` (p. ej.
  `test_f049_avisos_registro.py`) no tienen vinculados y siguen igual.
- Una clave de vinculado que desaparece y reaparece al repetir el preflight
  ya está vista: sale como la dejó el humano la última vez (desmarcada si
  la desmarcó), no se vuelve a marcar.

## Fase RED (antes del cambio en `app.js`)

Comando (desde `services/dedicacion-front`):
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

(El que pasa en RED es `test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado`:
fija que sin vinculados nada cambia.)

GREEN tras el cambio: `9 passed in 2.61s`; suite del front `412 passed`.

## Mutación manual del cambio en JS (la herramienta solo cubre Python)

Seis mutantes aplicados a `app.js` y revertidos, contra el fichero de F-064:

| Mutante | Resultado |
|---|---|
| M1 quitar `c.vinculado &&` | 5 failed |
| M2 sin motivo deja de contar como pisado | 4 failed |
| M3 no mirar `vistas` | 4 failed |
| M4 no anotar en `vistas` | 4 failed |
| M5 el preflight nuevo no vacía `vistas` | 1 failed |
| M6 no marcar | 7 failed |

Ningún superviviente.

## `bash harness/init.sh` (tras borrar `.arnes_cache/suite_*.ok`)

**[KO]**: raíz 418 passed / 1 skipped; api 1308 passed; front 412 passed;
transfer **1 failed** (`test_f013_sin_partida.py::test_f013_r4_el_front_rotula_por_motivo_y_degrada`;
sin `-x`: 1 failed, 1584 passed). Motivo y opciones: `progress/current.md`.
