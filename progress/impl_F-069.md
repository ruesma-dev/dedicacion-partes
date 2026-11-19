<!-- progress/impl_F-069.md -->
# F-069 · Informe del implementer (`critico`, pasadas 1 y 2)

Rama `feature/F-069-importe-caja-km` (copia `porcentajes-f069`). Pasada 1 sobre
`dev` `5381243` (spec del 2026-11-12); pasada 2 desde `adf6040` con la
enmienda D17-D21 y la review 1 (2026-11-19).

## Qué cambió

- **Pasada 1.** Los vinculados `CAJA`, `VIAJE` y `VP` llevan cantidad tecleada
  y comentario y llegan a Sigrid: por % (km, viaje) una cantidad del mes en
  `importe_vinculado`, repartida con el % del titular (km × `precio_km` 0,20);
  por obra (caja) una por línea en `asignacion_vinculado`, entera a su obra
  (`can` 1). Cada línea del titular y cada vinculado tienen su comentario, que
  viaja como `tex` (`PRUEBA-PORC` delante en pruebas). Copiar el mes marca
  `copiado` y no se registra sin revisar. Sin cantidades ni comentarios, el
  payload y las respuestas son los de hoy.
- **Pasada 2 (enmienda + review 1).**
  - **D17 (T19, T21):** el transfer quita la marca en `existentes`
    (`comentario_de_tex`); la api ya no conoce `MARCA_PRUEBAS`.
  - **D20 (T20, T24):** en una línea nuestra ya registrada cuyo comentario
    cambia, preflight y ejecutar anuncian `tex_nuevo` («… se actualiza el
    comentario» o por qué no); el ejecutar, **al final**, relee, hace
    `UPDATE hmores SET tex` con la guarda de F-051 (+ `AND obride = ?` en
    pruebas), lo comprueba releyendo y lo devuelve en `tex_actualizadas`. El
    modal enseña «comentario nuevo: «…»».
  - **D18/D19 (T22, T23, review cambio 1):** `revisado: true` en el `PUT`
    quita `copiado`; la misma cantidad o solo el comentario, no. El front
    manda **solo las casillas que cambiaron** (antes, todas: «Revisado» en
    una revisaba las demás). Un comentario sin cantidad se guarda
    (`cantidad` nulable) y se copia sin la marca.
  - **R30 (T9):** test nuevo; **T25:** RED de R15, R8, R32 y D21 por ruptura;
    **T26:** docs.

## Commits

Pasada 1: `eca0f8f` · `59583d4` T1 · `be4dc10` T2 · `a308d4c` T3+T4 ·
`4069ed3` T14 · `6f4c753` T5 · `adebb98` T6 · `9c27ce2` T7 · `5529256` T8 ·
`47a1f82` T9 · `7924b42` T15 · `917f392` T10+T11 · `de6de26` T12.
Pasada 2: `c6462f2` T19 · `35cc51a` T20 · `337e88a` T21 · `0a28649` T22 ·
`c9bc72e` T23 · `6d553c7` T24 · `cddede9` T25 · `96381ab` T9 · `8907e1e` T26;
informe en commit propio.

## Ficheros principales

- **Transfer:** `registro_models.py`, `reglas_vinculados.py`, `texto_linea.py`
  (`tex_de`, `comentario_de_tex`, `tex_a_actualizar`), `registro_pipeline.py`
  (`_actualizar_tex`), `registro_vinculados.py`, `lecturas_lote.py`,
  `porcentajes_existentes.py`, `sigrid_write_client.py` (`con_tex`,
  `stmt_editar_tex`), `app.py`.
- **Api:** `domain/importes.py`, `orm_models.py`, `repositories.py`,
  `use_cases.py`, `registro_sigrid.py`, `traer_sigrid.py`, `schemas.py`,
  `routes.py`. **Front:** `app.js` (`cuerpoImportes` filtrado, `chipImporte`,
  `htmlTexNuevo`, `guardarAhora`).
- **Docs:** `ARCHITECTURE.md` (`#regla-vinculado` con D17-D21, cita y fecha;
  `#regla-traer-sigrid`); `INTEGRACION.md` §1, §5 y §7.
- **Tests:** transfer `test_f069_{reglas_importe,pipeline_importe,existentes_tex,tex_registrada}.py`;
  api `test_f069_{importes_dominio,importes_api,traer_comentarios}.py`; front
  `test_f069_importes_front.py`. Adaptados (con comentario F-069): fakes y
  listas cerradas de F-003, F-024, F-044, F-050, F-054 y F-055.

## Decisiones y desviaciones (justificadas)

1. `tex_de(comentario, marca)`: quien llama sabe si está en pruebas.
2. `obra` entra en `decidir_vinculados` (motivo «falta la caja del mes», D13).
3. Las casillas por % salen de las subfilas: sin %, nada que repartir.
4. Caja y comentarios se guardan con upserts dirigidos, no con `reemplazar`,
   para no perder la traza de ya registrada (F-054).
5. **D21** (era la desviación 6 de la pasada 1, ya en la spec): el comentario
   de una cantidad del mes traído de Sigrid va en un evento `IMPORTES`.
6. En modo pruebas no vuelve el comentario del **titular** (F-054 no trae esas
   líneas en pruebas); el de los vinculados sí. Recogido en T16.
7. En el front, un texto no numérico se manda tal cual: la api da 422.
8. **D20, relectura y lote propios al final** (`_actualizar_tex`), no los de
   paso 10: el `tex` va después de todas las demás escrituras, con relectura
   fresca, `_tex_sigue_valiendo` (nuestra, misma `reside`, parte activo, M* o
   la hora del vinculado) y comprobación posterior. Una lectura más solo si
   hay algo que actualizar; `con_tex` (que añade `tex`, `obride` y `con.est`
   a la lectura de registradas) solo si alguna línea trae comentario: sin
   comentarios, SQL y lecturas idénticas a las de hoy.
9. **Tests de la pasada 1 reescritos por la enmienda** (manda la enmienda):
   api `r4_una_cantidad_tecleada_quita_el_copiado` (D18: la misma cantidad
   ya no revisa) y front `r11`/`r12` (sin `fotoImportes`: cada casilla guarda
   su `guardada`; «Revisado» manda `revisado: true`).
10. **Front, marca de copiado**: teclear la cantidad guardada vuelve a
    enseñar la marca; es solo presentación y espeja la regla de la api (la
    decide la api).

## Fase RED (trazas reales; pasada 1 resumida)

**Pasada 1.** T1-T2 (`test_f069_reglas_importe.py`):
`TypeError: decidir_vinculados() got an unexpected keyword argument 'obra'`,
2 failed. T3 (`-k r23`): `assert None == 'mes con visita'`, 4 failed, 2 passed.
T14: `ImportError` de `LineaVinculadoSigrid`/`PREFIJO_VINCULADOS`. T5:
`ImportError: cannot import name 'ImporteInvalido'`. T6-T11 y T15 sin RED
(test tras el código); los de R15, R8 y R32 se cubren ahora en T25.

**T19** · `pytest tests/test_f069_existentes_tex.py -q -k r31` (transfer)
```
E       ImportError: cannot import name 'comentario_de_tex' from 'application.services.texto_linea'
E       AssertionError: assert ['PRUEBA-PORC...'PRUEBA-PORC'] == ['visita', None]
E       AssertionError: assert 'OTRA-MARCA visita' == 'visita'
3 failed, 6 passed in 0.41s
```
**T20** · `pytest tests/test_f069_tex_registrada.py -q`; sin `texto_linea`:
`ImportError: cannot import name 'MOTIVO_TEX_CERRADO'` (1 error). Con
`texto_linea`, modelos y dobles, sin pipeline ni cliente:
```
E       AssertionError: assert ('ya_registrado', 5301, None) == ('ya_registra...A-PORC nuevo')
E       AssertionError: assert set() == {'editar_tex'}
E       TypeError: SigridWriteClient.lineas_registradas() got an unexpected keyword argument 'con_tex'
E       AttributeError: 'SigridWriteClient' object has no attribute 'stmt_editar_tex'
14 failed, 6 passed, 1 warning in 2.92s
```
**T21** · api `pytest tests/test_f069_traer_comentarios.py tests/test_f069_importes_dominio.py -q -k r32`
```
E       AssertionError: assert 'x' == 'PRUEBA-PORC x'
E       TypeError: comentario_de_sigrid() missing 1 required positional argument: 'marca'   (x7)
E       AssertionError: assert not True  (+ where True = hasattr(<module 'domain.importes'>, 'MARCA_PRUEBAS'))
9 failed, 11 passed, 43 deselected, 1 warning in 5.64s
```
**T22** · api `pytest tests/test_f069_importes_api.py -q -k "r3 or r4 or r5 or r8"`
```
E  At index 4 diff: 'cantidad NUMERIC(12, 2) NOT NULL' != 'cantidad NUMERIC(12, 2)'
E  AssertionError: assert (False, 'visita') == (True, 'visita')        (D18: solo el comentario)
E  AssertionError: assert False is True  (SubfilaVinculado(... CAJA ... copiado=False).copiado)
E  KeyError: 20   (x2: D19, km null con comentario no deja fila; deshacer)  · 422 en la ruta con `revisado`
E  Failed: DID NOT RAISE ImporteInvalido   (x3: revisado "si", 1, "true")
11 failed, 33 passed, 20 deselected, 1 warning in 4.73s
```
**T23 (review cambio 1)** · el test nuevo de dos casillas copiadas contra el
`app.js` de la rama aún sin el cambio (`PYTHONPATH=. pytest <scratchpad>/test_red_d18.py`):
```
E  At index 0 diff: ['importes', 'PUT', {'importes': [{'vinculado_ide': 20, 'cantidad': 100, 'comentario': None}, {'vinculado_ide': 30, 'obra_ide': 1, 'es_postventa': False, 'cantidad': 80, 'comentario': 'caja'}]}] != ['importes', 'PUT', {'importes': [{'vinculado_ide': 20, 'cantidad': 100, 'comentario': None, 'revisado': True}]}]
1 failed in 10.49s
```
y `pytest tests/test_f069_importes_front.py -q -k "r11 or r12"`: `no existe
la función elementoImporte en app.js` (x8), `KeyError: 'revisado'`; 9 failed,
2 passed.
**T24** · `pytest tests/test_f069_importes_front.py -q -k r29`
```
E  assert 'class="tex-nuevo">comentario nuevo: «PRUEBA-PORC visita»' in '<tr>…<span class="motivo">ya registrada en Sigrid (línea 5301); no se duplica; se actualiza el comentario</span></td></tr>'
1 failed, 1 passed, 12 deselected in 0.31s
```
**T25 (review cambio 2), ruptura deliberada** · api `pytest tests -q -k "f069 and rNN"`,
cada ruptura con `sed` y descartada con `git checkout -- application`
(`git status` final: sin cambios de código).
- R15, `_cantidad_al_transfer` con `copiado` siempre `False`:
  `assert ('obra', 80.0, False, 'caja') == ('obra', 80.0, True, 'caja')`, 1 failed;
  con la cantidad por % tomada de la subfila: `{'cantidad': None} != {'cantidad': 724.5}`, 1 failed.
- R8, `_copiar_importes` con `copiado=False`: `ImporteMes(... cantidad=Decimal('100.00'), copiado=False, comentario='km')} != {... copiado=True ...}`;
  FAILED `test_f069_r8_copia_cantidades_y_comentarios_con_copiado[_copiar_trabajador]` y `[<lambda>]`.
- R8, `_sin_propuesta` con la subfila `copiado=None`: `At index 1 diff: None != True`;
  2 failed, 6 passed.
- R32, `TraerDeSigrid._tex` sin `comentario_de_sigrid`:
  `assert ' mes con visita ' == 'mes con visita'`; 1 failed, 19 passed.
- R32, sin la toma por `hmores_ide`: `assert None == 'mes con visita'`,
  `assert ['IMPORTES'] == ['SIGRID', 'IMPORTES']`, `assert None == 'primera'`.
- D21, evento `SIGRID` en vez de `IMPORTES`:
  `assert ['SIGRID', 'SIGRID'] == ['SIGRID', 'IMPORTES']`, `assert 'SIGRID' == 'IMPORTES'`.

**T9 / R30** · rompiendo `trazar_vinculados` para que copie `cantidad`,
`copiado` y `comentario` del payload (`pytest tests -q -k "f069 and r30"`):
```
E  AssertionError: ({'asignacion_id', 'cantidad', 'comentario', 'copiado', 'sigrid_estado', 'sigrid_hmores_ide', ...}, {'cantidad', 'comentario', 'copiado', 'sigrid_estado', 'sigrid_hmores_ide', 'sigrid_motivo', ...})
FAILED tests/test_f069_importes_api.py::test_f069_r30_la_traza_de_una_caja_conserva_cantidad_copiado_y_comentario
1 failed, 1631 deselected, 1 warning in 3.35s
```
Ruptura descartada; con el código de verdad, 1 passed. R30 ya se cumplía (la
traza solo nombra `sigrid_*`): faltaba el test.

## Verificaciones por tarea (resultado real)

- Transfer: 1956 passed tras T20. Api: 1631 tras T22 y 1632 tras T9;
  `-k "r10 or r15 or r16 or r30"`, 10 passed. Front: 572 tras T23 y 573 tras
  T24 (suite entera).
- T26: `test_f002_fuente_unica.py`, 86 passed; el grep da aciertos en
  `ARCHITECTURE.md` (1115, 1128, 1137, 1141) e `INTEGRACION.md` (416, 430, 431).

## Salida de `bash harness/init.sh` (2026-11-19, rama F-069, tras T26)

Tal cual, sin pipes: código de salida **0**, ningún `[KO]` (ruff: 406 avisos de deuda previa).
```
2319 passed, 47 skipped in 560.54s · api 1632 passed in 52.40s · front 573 passed in 71.05s · transfer 1956 passed in 30.24s
[OK] PUERTA COBERTURA: 99.6% de 690 líneas cambiadas cubiertas (687/690, umbral 90% (del nivel critico)…)
[OK] PUERTA TAMAÑO: F-069 dentro de los topes (requirements 149/150, design 249/250, impl 213/220, review 139/140)
[OK] PUERTA CARRIL: N/A (nivel critico) · [OK] CAPA E2E: N/A (ningún servicio declara el bloque e2e)
```

## Pendiente (fuera de mi alcance)

- **T13 / T18 (mutación):** para la pasada de campaña, tras el APPROVED.
- **T16, MANUAL (humano o líder), escribe en la 0404 de pruebas; no la he
  ejecutado.** Pasos completos en `tasks.md` T16 (D19, D20, «Revisado» solo en
  el km, D17). Antes: servicios de la rama con `OBRA_PRUEBAS_FORZAR=true`,
  `curl -s http://127.0.0.1:8006/health` ⇒ `modo_pruebas: true` y `0404`, y en
  la BBDD **local** con la tabla de la pasada 1
  `ALTER TABLE importe_vinculado ALTER COLUMN cantidad DROP NOT NULL`
  (design §7.2). Desde `services/dedicacion-transfer`:
  `.venv/Scripts/python prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`;
  limpieza `… limpiar --ano 2026 --mes 11 --confirmar` (y `--mes 12`).
  Resultado en `progress/manual_F-069.md`.
- **T17 (humano, al desplegar):** transfer → api → front; luego
  `azure-apps/dedicacion.md` (`revisado`, `tex_nuevo`/`tex_actualizadas`,
  `tex` sin marca, `UPDATE` de `tex`) en commit aparte tras `pull --rebase`;
  aviso a `partes` y apunte F-071 en `current.md`. Documento del ecosistema:
  no lo he tocado (la spec lo deja en T17).
- **Review:** cambio 3 resuelto por D17 (T19, T21); el 4 ya está en T16; el 6
  (`current.md`) y el 7 (spec) no son del implementer.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz 2319 passed / 47 skipped · api 1632 · front 573 · transfer 1956; 0 failed |
| Cobertura de líneas cambiadas | **99,6 %** (687/690; umbral 90 %, `critico`) |
| Mutantes generados / supervivientes | **PENDIENTE de la pasada de campaña** (tras el APPROVED: `python -m harness.mutacion --feature F-069`) |
| Tiempo de la suite | raíz 560,54 s · api 52,40 s · front 71,05 s · transfer 30,24 s |
| Capa e2e | `CAPA E2E: N/A` (ningún servicio declara el bloque e2e) |
