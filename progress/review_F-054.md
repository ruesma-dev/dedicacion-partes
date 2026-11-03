<!-- progress/review_F-054.md -->
Revisión incremental desde 838b390 (pasada 7), HEAD `84faa05`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 7 (enmienda T23)

**Veredicto: APROBADO (APPROVED).** La ventana de una tabla cumple R28 y R39-R42, D12
revisada está reescrita en todos sus sitios y el test de F-050 acotado sigue protegiendo lo
que protegía. Sin bloqueos; tres observaciones del rastro (O8-O10), no bloqueantes.

**Rigor:** `critico` (`features.json`): RED, cobertura, mutación con 0 supervivientes, RM5
(muestra de un equivalente) y MANUAL con comando exacto.

## Delta revisado (`git diff 838b390..HEAD`, 12 ficheros)

- **Aceptar manda exactamente las marcadas** (`app.js:3020-3026`): `aceptadasMarcadas(modelo)`
  lee `modelo.filas` (no el DOM), así que las ocultas por el filtro van y las desmarcadas no.
  Cuerpo `{trabajador_ide, obra_ide, es_postventa}` como hoy: antes `Number(dataset…)` y
  `postventa === "1"`; ahora el valor de la respuesta, que el esquema fija como `int`/`bool`
  obligatorios (`schemas.py` `TrabajadorSigridOut`, `EntradaSigridOut`): mismo JSON. Lo fija
  `test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga` (marcadas ocultas tras filtrar y
  ordenar, orden de la respuesta, la desmarcada fuera) y `r42_marcar_las_visibles_*`.
- **El front no decide qué se registra**: solo filtra, ordena y cuenta para presentar; qué
  entradas son aceptables (`distinta`/`solo_sigrid`) sigue viniendo del estado que calcula la
  api, y la api rechaza con motivo cualquier otra (R20). `filasTraerVisibles` no muta `filas`
  ni `marcada` (`filter` devuelve copia y el `sort` es sobre ella).
- **D12** desmarcada: `marcada: false` en `modeloTraerSigrid`; `test_f054_r28_casilla_*`
  cambiado (no borrado) a «ninguna `checked`». Reescrita en requirements (cabecera, R21, R28,
  §4 `[D12]`, §6 con la cita antigua como sustituida), design (cabecera y §7), tasks (T9
  anotado, T18 paso 2, T23), `ARCHITECTURE.md` punto 23 (texto y cita de decisión) y
  `spec_F-054.md`. `grep` de «marcada por defecto», «(marcada», «Aceptar las marcadas»,
  «ventana por trabajador» en specs, docs, servicios y `current.md`: solo la cita sustituida
  y referencias históricas de T9/T23; los demás «sale marcada» son de F-032/F-064, ajenos.
- **Test de F-050 acotado** (`test_f050_modal_registro.py:199-205`): ningún `<select` en
  `pintarModalPreflight`, `montarSelectorPartida`, `listaSelector` ni `htmlPartida` (y
  `_funcion` falla si alguna desaparece), y el total de `app.js` igual al de
  `pintarTraerSigrid` (hoy 1, l. 2998). Cualquier `<select` nuevo fuera de esa función tumba
  el test: protege lo de antes salvo el filtro de Estado. En la lista cerrada de tasks.md.
  **Reproducido** en copia: `<select>` en `htmlPartida` → `1 failed`; en
  `textoAceptarTraer` (lo caza el recuento global) → `1 failed`; base `1 passed`.
- **Spec**: R39 una tabla con las seis columnas; R40 orden con segunda pulsación, raya al
  final en los dos sentidos, empate estable (`Array.sort` estable en ES2019+); R41 «contiene»
  sin mayúsculas sobre el texto pintado y estado exacto, combinados; R42 «Desmarcar todas»
  (también ocultas), «Marcar las visibles» (solo con casilla), contador con «(K ocultas…)»
  solo con K > 0; N = 0 → aviso y nada mandado. Sin casillas, ni aceptar ni los dos botones.
  Desviación menor y anotada en el propio código: además del `<tbody>` y el botón se repintan
  los títulos (para ▲/▼); los filtros no, y no pierden el foco. Sin efecto en contrato.
- **Convenciones**: primera línea con ruta en `app.js` y `styles.css` (sin cambio de
  cabecera), sin `console.*`/`debugger`/`print` en lo añadido, sin secretos, todo escapado
  con `escapeHtml` (D42-D44 lo prueban). CSS acotado a `.modal .tabla-traer`.
- **Api, transfer, contrato**: ningún `.py` de producción tocado desde `a781d25` (solo los
  dos tests del front): la campaña Python 266/266 sigue valiendo (RM1).

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados, sin pipes) código 0, sin `[KO]`, «ENTORNO
  LISTO», cobertura `[OK]` 99,5 %, tamaño `[OK]` · [x] ficheros del arnés.
- **C2** [x] una `in_progress` · [x] rama `feature/F-054-sync-trae-porcentajes` (`git -C`) ·
  [x] `current.md` coherente con F-054 (relectura entera, ver «Rastro») · [x] history.
- **C3** [x] hexagonal (solo presentación en el front; la regla de qué es aceptable vive en la
  api) · [x] primera línea · [x] sin debug ni secretos · [x] el front sin lógica de negocio.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R28, R39-R42 con `test_f054_r28_*`, `r39_*`, `r40_*`, `r41_*`, `r42_*` (40 en el
  fichero) · [x] sin red ni BBDD (node con dobles) · [x] MANUAL T18 (pasos 2-4 sobre la
  ventana nueva, paso 1 hecho), T19 y T20 con comando exacto en `current.md`.
- **C4 bis** [x] rigor declarado · [x] RED real de T23 (`36 failed, 2 passed in 2.77s`, con
  el `AssertionError` de `modeloTraerSigrid`) · [x] cobertura `[OK]` 99,5 % (755/759; no mide
  JS, N/A justificado por lenguaje para `app.js`) · [x] mutación Python: recalculé alcance (22
  ficheros, 1651 líneas) y **266 mutantes**, coincide; campaña no reejecutada: 3696 s según el
  informe; RM1 sin `.py` de producción desde `a781d25`; RM2 como en la pasada 3 · [x] `app.js`
  manual, campañas 5 (81, 78 muertos, base `81 passed in 20.60s`, 1613 s) y 6 (3 muertos), una
  fila por mutante con texto exacto y nº de fallos. **Reproducidas al pie de la letra** en
  copia `git archive` (base `40 passed`): **D1** `marcada: false`→`true` → `8 failed` (tabla:
  8); **D58** `filter(f.marcada)`→`filter(f.casilla)` → `4 failed` (tabla: 4) · [x] RM3: ningún
  equivalente sale muerto; D63 (sin guarda del botón) muere por `TypeError` real con datos sin
  casillas, D49/D44 cambian el HTML · [x] **RM5**, muestra de uno: D10 (`asc` inicial)
  reproducido sobre HEAD (`orden: { col: null, asc: false }`) → `40 passed`: equivalente, y el
  campo se quitó del código en vez de pedir aceptación; D10b en su línea muere (5) · [x] RM6
  N/A: no se quitó ninguna guarda (D10 quita un campo que nadie lee, no una defensa) · [x]
  «Evidencias» con los cuatro números y workers (Python 4; manual en serie) · sin N/A sin motivo.
- **C4 ter** N/A: sin `harness/rutas_sensibles.json`.
- **C5** [x] T1-T9, T11-T17, T21-T23 `[x]` con commits `F-054 T23: …` · T10 `[x]` (MANUAL hecha)
  · T18-T20 `[ ]` por MANUAL, legítimo · [x] árbol limpio (`git status` vacío) · [x] `in_progress`.

## Rastro: relectura entera de `progress/current.md` (775 líneas)

Coherente en lo pedido: cabecera «EN CURSO … en REVIEW 7»; rangos **T1-T23, R1-R42, D1-D19**
(l. 77-78, con D12 revisada); MANUAL **T18** con el comando exacto del paso 1 (hecho, con
resultado) y los **pasos 2-4** sobre la ventana nueva (l. 134-147), igual que tasks.md; **T19**
y **T20** listadas con comando (l. 148-165); **`azure-apps` pendiente: T20** (l. 35-36);
«Siguiente» (l. 72) y «Hoy» (l. 559) en review 7. Nada que bloquee. Observaciones (para recoger
en el siguiente toque del fichero, no en esta pasada):

- **O8** `current.md:56-57`, párrafo de F-044/F-064: «T23 hecha: `azure-apps/dedicacion.md` al
  día (`29321e1`)» es la T23 **de F-044**; ahora que F-054 tiene su propia T23 se lee mal.
  Propuesta: «F-044 T23 hecha: …».
- **O9** T18 paso 1 consta «HECHO» con resultado solo en `current.md` (l. 136-139), y T18 dice
  «Resultado en `progress/manual_F-054.md`», que aún no existe. Al crear ese fichero con los
  pasos 2-4, copiar ahí el resultado del paso 1 (PowerShell, 429 líneas, `MADM` 0694 al 95 %).
- **O10** `impl_F-054.md` «MANUAL pendientes», T18: lista el paso 1 como pendiente (`curl`);
  `current.md` lo da por hecho. Anotar «paso 1 hecho el 2026-11-02» al cerrar.

## Cambios requeridos

Ninguno. Para cerrar faltan T18 (pasos 2-4) y T19 del humano, con resultado en
`progress/manual_F-054.md`, y T20 al desplegar (`azure-apps/dedicacion.md` y aviso a
`partes`). **R37 sin cifra final** hasta T19 (≤ 11,89 s; si pasa, PARA). El singular del
botón («Aceptar 1 marcadas») sigue la spec y no está decidido por el humano: no es bloqueo.

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R3 | `test_f054_r1_*` (front), `r2`, `r3`; O5: `test_f054_o5_*` |
| R4-R12 | `test_f054_lectura_mensuales`, `endpoint`, `traduccion` |
| R13-R18 | `test_f054_comparar` (R16 con `0.50` y `1.00`) |
| R19-R27 | `test_f054_aceptar`, `rutas` |
| R28 (D12) | `test_f054_traer_front.py` `r28_*` (ninguna marcada, manda las marcadas, ocultas incluidas) |
| R39 | `r39_una_sola_tabla_*`, `r39_sin_entradas_no_hay_tabla` |
| R40 | `r40_ordena_*`, `r40_cuadrante_y_sigrid_*`, `r40_la_raya_*`, `r40_texto_*_empate_estable`, `r40_la_cabecera_de_la_casilla_*`, `r40_la_columna_ordenada_*` |
| R41 | `r41_filtro_de_obra_*`, `r41_texto_*`, `r41_desplegable_*`, `r41_sin_filas_*`, `r41_filtrar_u_ordenar_*`, `r41_al_abrir_*` |
| R42 | `r42_desmarcar_todas_*`, `r42_marcar_las_visibles_*`, `r42_el_boton_cuenta_*`, `r42_texto_del_boton_*` |
| R29 | `test_f002_fuente_unica` y grep; `azure-apps`, T20 |
| R30, R37 | MANUAL T10 (hecha), T18, T19 |
| R31 (D19), R32-R34, R38 | `test_f054_obra_cero` (`r31_o2_*`, `d19_*`), `modal_cero` (`d19_*`) |
| R35-R36 | `test_f054_poner_a_cero`, `registro_cero`, `modal_cero` (`r35_o5_*`) |

Suites (esta pasada, `init.sh`): api 1469, transfer 1865, front 507, raíz 418 (1 skipped).

## Reviews anteriores, resumen

Review 6 (`90c3e4f`) y 2 (`0ddba84`) **APROBADAS**; 5, 4 y 3 **CAMBIOS REQUERIDOS** solo por
`current.md` (la 3 aprobó el código de T22/D19, 266 recalculados, RM4 8/8; sus automejoras son
los encargos `e7a172b` y `de161b4` de `arnes-base`); 1 **RECHAZADA** solo por el rastro.
Detalle: `git show <sha>:progress/review_F-054.md`.

## Automejora (propuesta, no aplicada; para `CHECKPOINTS.md` y `arnes-base`)

La regla de reproducir dos filas de una campaña manual no dice sobre qué SHA: la campaña 5 es de
`488d423` y HEAD ya no tiene el texto de D10. Que el reviewer reproduzca sobre el SHA declarado
por la campaña, o sobre HEAD solo si el texto original sigue igual (aquí D1 y D58 lo cumplen).
