<!-- progress/review_F-041.md -->
Revisión completa (pasada 1), `62695e7..d2bc7f9` sin los merges de dev

# F-041 · Review — El filtro de obra casa con el texto visible (incluido Postv-)

**Veredicto: CHANGES_REQUESTED.** Solo por el **rastro de `progress/current.md`**
(C2 y C4). Código, tests y campaña: **sin objeciones**; la pasada 2 puede ser
incremental desde `d2bc7f9` si el ciclo no toca `app.js` ni los tests.

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`: fase RED,
cobertura de lo cambiado (o N/A con motivo impreso) y mutación con
supervivientes analizados.

## Lo comprobado (con resultado real)

- `bash harness/init.sh` desde `porcentajes-f041`: **exit 0**, `418 passed,
  1 skipped`, «ENTORNO LISTO». El front salió de caché, así que lo pasé aparte:
  front `79 passed`; `test_f041_filtro_obra.py` `26 passed`, **0 skipped** (node
  v24.14.1); transfer `test_f013_sin_partida.py` (lee `app.js`) `44 passed`.
- **Sin node** (`PATH=/c/Windows/System32`): `14 passed, 12 skipped`, motivo
  impreso «node no está instalado: los tests de lógica de F-041 no se ejecutan».
- **Tests anteriores cambiados por F-041: NINGUNO.** `git diff 62695e7..HEAD --
  '*tests*'` da el test nuevo y `test_f037_copias_partes.py`, que es de
  `6f7182d` (chore/partes-confluencia, ya en `dev`), igual que
  `sigrid_write_client.py`, `docs/INTEGRACION.md` y `history.md`.
- **Producción: solo `static/js/app.js`** (+36/−20). Hunks en `normalizar` (tres
  funciones nuevas), `construirCatalogoObras`, `textoColumna`,
  `trabajadoresVisibles`, `construirCelda` y `chipEditable`: ningún manejador de
  teclado («% Enter obra Enter», F-029) tocado; F-027 es solo api. Sin lógica de
  negocio: decide filas visibles y candidatas, no qué se guarda.
- **Una sola fuente** (punto 1): `etiquetaObra` → `textoObra` → `lineaCasa`. La
  columna usa `lineaCasa` por línea (`some`), el buscador mete `textoObra` de
  cada línea en el `pajar`, y candidatas de Completar y autocompletado casan con
  `e.clave = normalizar(textoObra(…))`. `"Postv-"` entre comillas: **una vez**,
  en `etiquetaObra`. `textoColumna` tiene un solo llamador y sin rama
  `asignaciones`. Sin literal `VAR`.
- **Casado** (punto 2): normalizado en los dos lados, `includes`; `pos` → Ana,
  Benito (Depósito), Carla; desde `post`, solo `Postv-`, cada prefijo ⊆ el
  anterior; `postventa`/`postve` → nadie y ninguna candidata (D1).
- **Merge de prueba con dev, sin tocar el árbol** (`git merge-tree`): `app.js` se
  fusiona solo con F-039; conflictos solo en `BACKLOG.md`, `features.json` y
  `current.md`. Árbol fusionado en mi scratchpad: front `82 passed`,
  `node --check` OK, `test_f013_sin_partida.py` `44 passed`.
- `ruff check` del test nuevo: «All checks passed!». `git status` limpio.

## Mutación (C4 bis)

- **Herramienta**: `alcance_de_feature("F-041")` → `lineas={}`. **Control del
  cero**: `generar_mutantes` sin exclusión da 106 sobre el test `.py` y 0 sobre
  `app.js` → cero legítimo (no muta JS). Sin `mutacion_F-041.md`, con motivo.
- **Campaña manual** (`progress/mutacion_manual_F-041.md`): 20/20 muertos, una
  fila por mutante con fichero:línea, **texto exacto original → mutado**,
  resultado y nº de fallos sin `-x`; incluye los ocho mínimos de design §7.
- **Reproducida al pie de la letra sobre una copia en mi scratchpad** (base
  `26 passed`): **M4** 8 fallos, **M13** 4, **M20** 2, con los mismos tests que
  la tabla. Dos mutantes **míos**: candidatas con `startsWith` → 4 fallos;
  `if (!casa)` → `if (casa)` → 8. Muertos.
- **RM1**: mide sobre `1a0019c`/`93c1a0e`; desde ahí ningún commit toca `app.js`
  ni el test. SHAs abreviados: aviso, no bloqueo (ninguna herramienta lo imprime
  en una manual). **RM2**: base 5,9 s, ~7,2 s/mutante sin `-x`, 1 worker, 2 min
  31 s: coherente; > 60 s, verificada por muestra.
- **RM3**: M14/M15 se dicen «equivalentes en comportamiento» y salen MUERTOS. No
  invalida: los matan solo los estáticos de R3, requisito estructural («ninguna
  otra concatenación de `Postv-`»). Frente a la spec no son equivalentes; lo que
  pinta el chip lo cubre T6. **RM5** N/A por nivel; **RM6** N/A, sin guardas
  quitadas. Supervivientes: 0.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] rama `feature/F-041-filtro-obra-postventa`
  · **[ ] `current.md` sin restos** (cambio 2) · [x] history (sin `done` nuevos).
- **C3** [x] hexagonal: N/A de fondo (JS de presentación, sin capas) · [x] primera
  línea con ruta (patrón del front) · [x] sin prints, TODOs, secretos ni
  dependencias · [x] trampas: ni porcentajes ni escrituras; postventa sigue
  como entrada aparte (`pv`) en catálogo y candidatas.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad (tabla), todo pasa · [x] sin red ni BBDD (node local,
  datos en memoria) · **[ ] MANUAL en `current.md` con su comando exacto**
  (cambio 1).
- **C4 bis** [x] rigor declarado · [x] fase RED: traza de T1 (`25 failed,
  1 passed`) y tras T2 (`14 failed`: R9 `[] == ['Ana','Carla']`, D2 `['Carla']`,
  D1, R10, R11) · [x] cobertura N/A con motivo impreso («F-041 no cambia líneas
  Python de producción frente a dev») · [x] manual reproducible, filas
  reproducidas · [x] muertos comprobados · [x] coste coherente · [x] sin
  «⚠ CAMPAÑA NO VÁLIDA» (base verde) · [x] RM1 (aviso) · [x] RM2 · N/A RM5,
  RM6 (motivos arriba) · [x] sin `PENDIENTE` · [x] «Evidencias» con los cuatro
  números y workers = 1.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1-T5 y T7 `[x]` con commit `F-041 Tn:`; T6 es MANUAL del humano,
  pendiente por definición (N/A justificado) · [x] sin temporales ·
  [x] `features.json` en `in_progress`.

## Cobertura requisito → test (`services/dedicacion-front/tests/test_f041_filtro_obra.py`)

| Req. | Tests (`test_f041_…`) |
|---|---|
| R1, R2 | `r1_etiqueta_en_una_sola_funcion`, `r2_texto_visible_usa_la_etiqueta`, `r2_linea_casa_con_su_texto_visible`, `r1_r2_etiqueta_y_texto_en_node` |
| R3 | `r3_postv_literal_solo_en_etiqueta_obra`, `r3_los_chips_y_el_catalogo_usan_etiqueta_obra` (×4) |
| R4, D2 | `r4_la_columna_casa_por_linea`, `r4_texto_columna_sin_rama_asignaciones`, `r4_d2_naves_postv_no_casa_a_caballo` |
| R5 / R6 | `r5_pos_y_completando_acota_letra_a_letra` / `r6_ignora_mayusculas_y_tildes` |
| R7 / R8 | `r7_casa_con_cualquier_parte_del_texto_visible` / `r8_sin_filtro_las_mismas_filas_y_orden` |
| R9 | `r9_buscador_global_usa_el_texto_visible`, `r9_buscador_global_encuentra_postventa` |
| R10, D1 | `r10_la_clave_del_catalogo_es_el_texto_visible`, `r10_catalogo_en_node`, `r10_d1_postventa_no_casa` |
| R11 | `r11_columna_y_completar_parten_del_mismo_texto` (dos direcciones, 15 textos) |
| R12 | `r12_etiqueta_exacta_primero`, `r12_dialogo_sigue_precargado_con_filtrar_obra` (+ `test_f029_r10_*`) |
| R13 | `r13_sin_literal_var_ni_ramas_por_prefijo`, `r13_var_29_casa_como_cualquier_obra` |

## Cambios requeridos

1. **`progress/current.md` líneas 22-30, MANUAL T6 incompleta.** Dice «seguir
   los pasos 4-8 del informe», pero el informe tiene 4-10 y la T6 de `tasks.md`
   incluye el Completar y el «Limpiar». Faltan justo los de R12 y requirements
   §8: con `postv` en «Filtrar obra…», Ctrl+clic en dos filas, **C**: el diálogo
   sale precargado con `postv` y solo ofrece `Postv-` — **cerrar con Esc sin
   completar** (el único paso que abre un diálogo que escribe); y «Limpiar» deja
   la tabla como antes. Copiarlos con su texto, o remitir a «pasos 4-10» y
   repetir el aviso de Esc.
2. **`progress/current.md`, restos que contradicen la cabecera** (reescrita en
   F-041: F-039 «aprobada en review»):
   - líneas 32-42, sección «F-039 … (spec lista)»: «Espera al humano con D1-D6»
     y «**No hay F-041**» (42), falso en esta misma rama;
   - «Lo siguiente»: «**F-039** (spec lista)» (107) y «F-029 espera a que el
     humano decida desplegar» (105), contra «Desplegado el 2026-10-06: F-029» (56).
   Podarlos o ponerlos al día. Lo más barato: **mergear `dev` en la rama** (el
   código se fusiona solo, comprobado arriba) y resolver `current.md` con el
   estado de `dev` más la sección F-041.

## Observaciones no bloqueantes

- R11 «viceversa» se cumple porque línea y obra traen la misma `descripcion`
  (las dos salen de la obra en la api); si divergieran, el test lo cazaría.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 bis, punto de la campaña MANUAL: añadir «declara el SHA
  completo sobre el que se midió», como RM1 para la automática.
