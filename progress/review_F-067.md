<!-- progress/review_F-067.md -->
Revisión completa (pasada 1) · `dev...3fb851e` (`3fb851ee066860b404e191c3def997943c47de82`)

# F-067 · Review 1

- **Veredicto: APROBADO** (APPROVED). Sin bloqueos; cuatro observaciones no
  bloqueantes al final.
- **Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
  fase RED, cobertura de lo cambiado y campaña de mutación con supervivientes
  analizados (justificación escrita basta; RM5 solo en `critico`).
- **Alcance:** solo front (`app.js` +61/−10, `styles.css` +3, un test nuevo)
  más el papeleo. Ningún test existente cambia (`git diff --name-status`:
  solo `A tests/test_f067_ver_vinculados.py`).

## Verificación propia

- `rm -f .arnes_cache/suite_*.ok` y `bash harness/init.sh` tal cual, solo:
  «ENTORNO LISTO», **sin ningún [KO]**. Raíz 418 passed / 1 skipped; api 1308
  passed; front **451 passed** (los 17 de F-067 `passed`, ninguno saltado);
  transfer 1585 passed. `PUERTA COBERTURA: N/A (F-067 no cambia líneas Python
  de producción frente a dev)`; `PUERTA TAMAÑO` en topes. ruff 309 avisos
  (deuda previa, [AVISO]).
- **RED reproducida**: en una copia del scratchpad con el `app.js` de `dev` y
  los tests de HEAD, `13 failed, 88 passed` en F-067+F-041+F-044+F-063+F-064+
  F-065 (los 12 de T1 más el de T3; los cuatro «como hoy» pasan, como dice el
  informe). Las suites ajenas pasan igual con el código viejo y el nuevo.
- **Mutación manual reproducida al pie de la letra** (script del informe
  sobre copia temporal, filtrado a cuatro filas): N9 MUERTO 7 fallos, N18
  SUPERVIVIENTE 0, N19 MUERTO 1, N24 MUERTO 2; mismos tests que la tabla.
  Línea base `101 passed in 18.72s`; 103 s en total. `git status` limpio.
- **Recálculo puro**: `harness.alcance.alcance_de_feature('F-067')` →
  `lineas={}` (0 mutantes automáticos). Control: `generar_mutantes` sobre el
  único `.py` del diff (el test) sin la exclusión da 211; el cero es
  exclusión por diseño, y el JS lo cubre la campaña manual.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
**C2** [x] una sola `in_progress` (F-067) · [x] rama `feature/F-067-ver-vinculados`
· [x] `current.md`: la cabecera dice «En curso: F-067», implementación
terminada y review 1 lanzada; «Siguiente» corregido (F-054 tras F-067); la
MANUAL de F-067 en «⚠ Lo que espera al humano»; el resto son pendientes del
humano vigentes (F-063/F-064/F-065, avisos a `partes`), no restos ·
[x] las `done` tienen resumen en `history.md` (sin cambios aquí).
**C3** [x] hexagonal: el front sigue sin lógica de negocio; la casilla es
pantalla y la preferencia solo la leen `renderCabecera`, `cargarPrefsTabla`,
`guardarPrefsTabla`, `trabajadoresVisibles` y `construirFila` (lo fija un
estático); nada del modal ni del registro · [x] primera línea con ruta en
los tres ficheros · [x] sin `console.log`/`print`/TODO/secretos ni
dependencias nuevas · [x] las tres trampas: no toca porcentajes, postventa
ni escritura en Sigrid.
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] cada `acceptance` con tests `test_f067_rN_*` en verde (tabla) ·
[x] sin red ni BBDD (node + DOM y `localStorage` de mentira) · [x] MANUAL en
`current.md` con pasos exactos; el paso 5 avisa de Cancelar porque el
transfer desplegado escribe de verdad.
**C4 bis** [x] `rigor` declarado · [x] RED con salida real en el informe
(y reproducida) · [x] cobertura N/A con motivo impreso por init.sh; el JS no
tiene medidor, motivo de lenguaje · [x] mutación: `harness.mutacion` no
aplica (0 Python de producción, control hecho); la sustituye la campaña
manual `progress/mutacion_manual_F-067.md` · [x] muertos comprobados: cuatro
filas reproducidas; la campaña declara 917,7 s (>60 s), no se reejecutó
entera · [x] coste por mutante 917,7×1/27 ≈ 34 s, ≈ línea base 26,4 s ·
[x] sin «CAMPAÑA NO VÁLIDA»; base en verde y la aborta si no · [x] RM1: SHA
completo `7016870ad9b6…`; desde ahí solo cambia `check=False` en el test y
el papeleo: el alcance medido es el revisado · [x] RM2: coherente (28
ejecuciones × ~33 s ≈ 917 s; la mía, 5 × ~20 s ≈ 103 s) · RM5 N/A: rigor
`estandar`, basta la justificación escrita · RM6 N/A: no se quitó ninguna
guarda para matar mutantes (T3 añade un test) · [x] manual con una fila por
mutante, fichero:línea, texto exacto original→mutado y nº de fallos; ≥2
filas reproducidas · [x] superviviente N18 analizado (abajo) · [x]
«Evidencias» con tests, cobertura, mutantes/supervivientes, tiempos y 1
worker · [x] ningún N/A sin motivo.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** N/A `tasks.md` (`sdd: false`); commits `F-067 T1..T4: …` presentes ·
[x] sin temporales sin trackear (solo `.coverage`/`coverage.json`
ignorados) · [x] `features.json`: `in_progress`, coherente.

## Cobertura (acceptance → tests)

| # | Criterio | Tests |
|---|---|---|
| R1 | marcada = hoy; desmarcada sin subfilas y `rowspan` cuadra | `r1_desmarcada_ninguna_subfila…_rowspan_cuadra` (3 = 2 líneas + 1 inc.), `r1_desmarcada_sin_incidencias_rowspan…` (2), `r1_marcada_el_cuadrante_de_hoy` (5), `r1_el_estado_arranca_marcado`, `r1_la_casilla_sale_marcada…`; prefs antiguas en `r2_sin_nada_guardado_o_con_prefs_antiguas…` |
| R2 | se guarda y recupera; sin localStorage, marcada | `r2_se_recupera_lo_guardado`, `r2_se_guarda_con_las_de_la_tabla_y_vuelve`, `r2_desmarcar_guarda_y_repinta…`, `r2_con_la_preferencia_desmarcada…`, `r2_sin_localstorage_la_pagina_funciona_marcada` |
| R3 | Tipo recurso y Partida sin vinculados si desmarcada | `r3_tipo_recurso_desmarcada_solo_persona`, `r3_partida_desmarcada_solo_las_lineas` |
| R4 | el modal no cambia (vinculados y pisado F-064) | `r4_el_modal_es_el_mismo_marcada_o_desmarcada` (HTML y marcadas idénticos, `fila-vinculado-reg`, `[PIS_VIN]` marcado), `r4_solo_pantalla…` (estático) |
| R5 | sin vinculados no hay casilla | `r5_sin_vinculados_en_el_mes_no_sale_la_casilla`, `r5_basta_un_vinculado_bajo_cualquier_linea…` |
| R6 | RED, ajenos intactos, init.sh verde | RED reproducida; F-044/F-063/F-064/F-065 sin cambios y en verde; init.sh verde |

## Ojo especial del líder

- **Modal (F-044 R31 / F-064 `marcadaPorDefecto`)**: `pintarModalPreflight`
  no se toca y no lee la preferencia; el test R4 compara el HTML entero y las
  marcadas con la casilla en los dos estados. Correcto.
- **`rowspan` desmarcada**: `construirFila` deja `vinculados = []` y el
  `rowSpan` ya contaba `trs.length`; verificado 3 y 2. Correcto.
- **Aserciones ajenas**: ninguna cambiada; la casilla va en línea en
  `renderCabecera` y «Tipo recurso» desmarcado tiene rama propia justo para
  no tocar los arneses de F-063 ni el estático de F-041 R4.
- **Dobles**: `_linea`/`_trab` de F-063 son `LineaOut`/`TrabajadorOut` sin la
  clave `vinculados` (`exclude_if`); `TEL`/`GAS` llevan todas las claves de
  `SubfilaOut` (`schemas.py:91`). Ver observación 2.

## N18 (superviviente) · juicio

`!== false` → `=== true` en `trabajadoresVisibles`: solo difieren con un
valor no booleano. Comprobado: `verVinculados` solo se escribe en
`const state` (`true`), `cargarPrefsTabla` (booleano `!== false`) y el
`change` de la casilla (`input.checked`); no hay `Object.assign`,
`state[...]` ni spread sobre `state`. **Equivalente a nivel de aplicación:
aceptado** (rigor `estandar`). Que N24, el gemelo en `construirFila`, muera
no viola RM3: lo matan arneses de F-044 cuyo `state` no trae la clave, un
estado que esos tests ejercitan de verdad (muerte real, reproducida).

## Observaciones (no bloqueantes)

1. **Asimetría N18/N24.** El `!== false` existe solo por los `state` sin la
   clave de los arneses ajenos. Si en el futuro se toca el filtrado, bastaría
   un test de `trabajadoresVisibles` con `state` sin la clave para matar N18;
   hoy no aporta nada a la aplicación.
2. **`_filas` (R1) usa líneas mínimas** (`{"obra_ide", "vinculados"}`), el
   arnés `FILA` de F-044, no un `LineaOut` completo. Vale para lo que mide
   (subfilas y `rowSpan`); R3/R5 sí usan la forma serializada completa.
3. **MANUAL, paso 3**: «el código de la partida de una subfila de vinculado
   que no tenga ninguna línea» se entiende mejor como «una partida elegida en
   una subfila y en ninguna línea de ese trabajador». Se puede pulir al
   cerrar; no cambia el comportamiento.
4. **Foco tras pulsar la casilla**: ↑↓/Enter no mueven el cursor hasta salir
   de ella, como «Solo pendientes» (lo anota el informe). Comportamiento
   existente; si molesta, es otra feature.

## Propuesta de automejora (para el humano, no aplicada)

`CHECKPOINTS.md` C4 bis pide «existe `progress/mutacion_F-XXX.md`, generado
por la herramienta». En features solo-JS la evidencia vive en
`progress/mutacion_manual_F-XXX.md` (ya es el patrón de F-065 y F-067).
Propuesta: decir en ese checkbox que, con 0 mutantes automáticos y campaña
manual, el fichero válido es `mutacion_manual_F-XXX.md` con su SHA completo,
línea base y workers, para que no tenga que interpretarse en cada review.
