<!-- progress/review_F-069.md -->
Revisión incremental desde 18bd3f1 (pasada 5), sobre `032d794` (`git diff 18bd3f1..032d794`, 4 commits).

# F-069 · Review 5 (incremental, tras la PARADA 2)

**Veredicto: APPROVED.** El test nuevo fija de verdad el orden de D20 (lo he roto en una copia y cae
solo él). El delta no toca producción. La MANUAL T16 cubre los pasos de T16 y lo que declara se
sostiene con los ficheros de la prueba. Quedan observaciones de rastro (O1-O3) que el líder debe
recoger antes de la PARADA 2. Ninguna afecta al código ni a la evidencia de la feature.

## Reviews anteriores, en pocas líneas

- **1 y 2:** CAMBIOS REQUERIDOS. Los 1-7 de la review 1 y el papeleo de la review 2, resueltos. El código
  quedó aprobado en `3f9b5ff`. **3:** APPROVED (código; O1-O3 corregidas en `6b6d637`).
- **4 (evidencias):** APPROVED sobre `46e7835`. La campaña T13 es real: 473 mutantes, 159 en la muestra,
  142 muertos y 17 equivalentes juzgados uno a uno. RM1-RM7 cumplidas. Se le dejaron O1 (el «al final» de
  D20 sin test) y O2 (`current.md`).
- Detalle completo: `git show 46e7835:progress/review_F-069.md` (4), `6b6d637:` (3) y `909a5e2:` (2,
  con la tabla requisito → test y C1-C5).

**Rigor:** `critico` (`features.json`). Exige fase RED, cobertura ≥ 90 %, mutación sin supervivientes
sin justificar en la muestra, RM1-RM7 y MANUAL con su resultado real. La capa e2e es N/A.

## El delta

- `git diff --name-only 18bd3f1..032d794 -- services`: solo
  `dedicacion-transfer/tests/test_f069_tex_registrada.py`. **Sin código de producción.** Lo aprobado en
  `3f9b5ff` y medido en la campaña sigue valiendo (RM1: no cambia nada del alcance).
- El resto es papeleo: `current.md`, `features.json`/`BACKLOG.md` (`in_review`), `tasks.md` T16 `[x]`,
  `impl_F-069.md` (decisión 8 con su RED) y `manual_F-069.md` (nuevo).

## El test del orden de D20 (`5cf50a8`, O1 de la review 4)

`test_f069_r26_el_lote_del_tex_es_el_ultimo_del_ejecutar` compara los lotes de `escribir` en orden:
`[insert porcentajes:2]`, `[insert porcentajes:vin:2:20]` y `[editar_tex]`. Además mira las acciones de
los vinculados y `tex_actualizadas == [5301]`.

Lo he comprobado en una copia (`git archive 032d794`) de mi scratchpad, nunca en la rama:

| Ruptura en `registro_pipeline.py` | Suite del transfer |
|---|---|
| Ninguna (base de la copia) | 1953 passed, 4 skipped |
| **A.** `_actualizar_tex` justo **antes** de `EscrituraVinculados` (l. 1463), sin la llamada final | **1 failed** (solo este test), 1952 passed; `At index 1 diff: [('editar_tex', None)] != [('insert', 'porcentajes:vin:2:20')]`, el mismo texto que trae el informe |
| **B.** `_actualizar_tex` antes del `escribir` de los titulares | 8 failed (este y 7 de R26/R28) |

Con A, el hueco que vi en la review 4 queda cerrado: antes del test, esa ruptura dejaba la suite entera
en verde. **No es frágil.** No depende del orden de un dict ni de la hora. Mira las etiquetas `sql` del
doble (`insert`/`editar_tex`) y las `synckey`, que es justo el contrato del orden. Las lecturas no entran
en `llamadas`. Si algún día cambia el troceo en lotes de `EscrituraVinculados`, caerá y habrá que
mirarlo: eso es lo que se quiere. Pasa en la rama (21/21 del fichero) y dentro de `init.sh` (1957).

**RM7**, aplicada a este orden: [x] la puerta, bajada un paso por cada colaborador que precede
(vinculados, titulares), pone la suite en rojo, y en los dos casos cae un test de F-069.

## La MANUAL T16 (`progress/manual_F-069.md`)

No la he repetido (escribe en Sigrid). Contrasté lo declarado con los ficheros de la prueba, que están en
el scratchpad de la sesión (`t16_*.json`, `t16_transfer.log`, `t16_api.log`, `t16_estado1.txt`):

- [x] **Cobertura de los pasos de T16:** comprobaciones previas (`/health`, `transfer_base_url`, `ALTER`
  no necesario), D19, preflight (12 € y 8 € de 20 €; caja 80 € solo en la 0696 y la 0722 «caja 0»),
  registrar, registrar otra vez, D20, copia (D11), «Revisado» solo en el km, D18, «Revisado» en la caja,
  D17 y limpieza. El mes (2032-03/04 en lugar de 2026-11/12) y que la hiciera el líder los autorizó el
  humano («2 mes sin uso y hazlo tu»; T16 dice «o el líder si él lo autoriza»).
- [x] **Se sostiene:** `t16_estado1.txt` trae las 7 líneas, con el `tex` del km «PRUEBA-PORC visita a
  proveedor» y la caja con `can` 1, `pre` 80 y `tot` 80. `t16_pf3`/`t16_ej2` traen «se actualiza el
  comentario» y `tex_actualizadas` con 416122 y 416125. En el log del transfer hay dos `UPDATE hmores SET
  tex` con la guarda de F-051, **0 `DELETE`** y escrituras en la obra 828942 (0404). `t16_pf4b`/`t16_pf5b`
  traen «copiado del mes anterior sin revisar». `t16_traer.json` da `excluidas_pruebas` 2.
- [x] **Desviaciones declaradas:**
  1. **Modal no mirado:** sin front arrancado, no se ven los rótulos «100 km × 0,20 €/km» ni «MODO
     PRUEBAS». Lo acepto: los datos que pinta el modal son los mismos, y `test_f069_importes_front.py`
     cubre el pintado. La comprobación del modo la hicieron el `/health` y los logs del proceso que
     escribe.
  2. **D18 rehecho como lo manda el front:** `elementoImporte` (`app.js` l. 1805) siempre manda
     `cantidad` y `comentario` juntos, así que es correcto. El primer `PUT` sin `cantidad` (`t16_pf4b`:
     «falta la caja del mes… 0696») explica la segunda copia. R8 explica por qué el km no se marcó otra
     vez y la caja sí.
  3. **`limpiar`:** ver O2.
- [~] **Sin fichero:** el `estado` tras D20 (lo dice el log: `UPDATE` solo de `tex`, «tex actualizados=1») y el `limpiar` (O2).

## Observaciones (no bloquean; el líder las recoge antes de la PARADA 2)

- **O1 · `current.md`, restos falsos que ya estaban (lista completa tras releerlo entero):**
  1. **l. 405-409**: «Las dos líneas de Bas Leal en la 0404 (`porcentajes:148` y `:149`…): **pendiente que
     el humano las borre**». Y **l. 617-620**: «Borrar en la 0404 las líneas de las pruebas locales…
     Bas Leal… y la de la M3 de F-050 (… 410599, `porcentajes:180`)». Las dos son falsas desde el
     2026-10-21: las borró el `limpiar` de F-051 (`progress/manual_F-051.md` l. 14-15;
     `history.md` l. 2773-2774). Hay que quitarlas o marcarlas como hechas.
  2. **l. 485**: «**Hoy (2026-11-19):** F-069 en `in_review`». La fecha está desfasada (hoy es
     2026-11-20, y entretanto pasó por `human_review`). Basta actualizar la fecha.
  3. **l. 85**: «Hallazgo: … no se limita a `--ano/--mes` (borra toda la marca **de la 0404**)». Ver O2:
     no es un hallazgo, y el alcance es mayor que la 0404.
  El resto lo he contrastado y es coherente: l. 4, 6, 72-86, 88-92, 252 y 663, así como
  `features.json`/`BACKLOG.md` en `in_review`.
- **O2 · El `limpiar` y la decisión del humano.** `fase_limpiar` (`prueba_escritura_porcentajes.py`
  l. 407-424) **dice en su docstring** «de todos los meses», y su `SELECT` filtra solo por
  `tex LIKE 'PRUEBA-PORC%'` y `synckey LIKE 'porcentajes:%'`: **sin mes y sin obra**. No es una sorpresa.
  Ya pasó en F-051, y la nota del F-064 en `current.md` (l. 563-565) lo avisa. Lo que estaba mal era el
  texto de T16 en `tasks.md` (`limpiar --ano 2026 --mes 11`, «y `--mes 12`»), que sugiere un alcance que
  el script no tiene. Tres cosas para el líder:
  1. En `manual_F-069.md`, cambiar «la sorpresa» y «de la 0404» por lo que es: el `limpiar` borra todas
     las líneas marcadas de este hilo, de cualquier mes y obra. Pegar el recuento y los `ide` que imprimió
     el `limpiar`, si se guardaron. Si no, sirve un `limpiar` **en seco** (solo lectura), que debe dar
     0 líneas.
  2. **En la PARADA 2, decirlo al humano en claro:** se borraron 414543-414545 (T19 de F-054), cuya
     limpieza estaba «pendiente de decisión del humano». Fue un borrado en la 0404 de pruebas, sin
     `DELETE` sobre nada real, pero se tomó sin esa decisión.
  3. Para próximas MANUAL (`spec-author`): no escribir `limpiar --ano/--mes` como si filtrara.
- **O3 · Automejora (propuesta, no aplicada; vale para `arnes-base`) en `CHECKPOINTS.md` C4:** el paso
  **destructivo** de una MANUAL cita su salida real, y el reviewer contrasta su alcance con el script.

## Checkpoints (pasada 5, incremental)

- **C1** [x] `ARNES_SIN_CACHE=1 bash harness/init.sh` entero sobre `032d794`, sin pipes: código 0,
  ningún `[KO]`, «ENTORNO LISTO». [x] `git status` limpio después: las rupturas, solo en el scratchpad.
- **C2** [x] Una sola feature activa (`in_review`). [x] Rama `feature/F-069-importe-caja-km`. [x]
  `current.md` al día en lo de F-069; los restos ajenos van en O1.
- **C3 / C3 bis / C3 ter** [x] Sin producción, `docs/` ni `docs/referencia/` en el delta. **C3 quater**:
  pendiente de T17 al desplegar (listada en `current.md` l. 86), como en las reviews 3 y 4.
- **C4** [x] El test nuevo, trazable (`test_f069_r26_*`) y en verde. [x] R1-R34 con test, sin cambios, y
  R35-R36 MANUAL. [x] T16, MANUAL ejecutada con su resultado real en `progress/manual_F-069.md`.
  [x] Los unit tests no tocan red ni BBDD (el test nuevo usa `ClienteCant`).
- **C4 bis** [x] Nivel declarado. [x] RED del test nuevo en el informe (decisión 8), reproducida por mí.
  [x] Cobertura `[OK]` 99,6 % (687/690). [x] Mutación: sin cambios en el alcance, la campaña de la
  review 4 sigue valiendo (RM1). [x] RM6 N/A: no se ha quitado ninguna guarda. [x] RM7, arriba. [x]
  Capa e2e N/A: ningún servicio declara el bloque e2e.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`. **C5** [x] Commits `F-069:` / `F-069 T16:`.
  [x] Todas las tareas `[x]` salvo T17, que va al desplegar.

## Cambios requeridos

Ninguno. **Para el líder, antes de la PARADA 2:** O1 (tres puntos de `current.md`) y O2.1-O2.2.

## Resultado de `ARNES_SIN_CACHE=1 bash harness/init.sh` (`032d794`, sin pipes)

Código 0, ningún `[KO]`. Raíz 2319 passed / 47 skipped (17 min 12 s, con la máquina cargada por mis
rupturas en paralelo). Api 1640, front 573 y transfer 1957. `[OK]` en PUERTA COBERTURA (99,6 %), TAMAÑO
(este informe lo mido aparte con `python -m harness.tamano --feature F-069`), CARRIL N/A y CAPA E2E N/A.
