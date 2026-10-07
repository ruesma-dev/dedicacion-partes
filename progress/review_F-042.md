Revisión completa (pasada 1) · HEAD `322106a` (`git diff dev...HEAD`)

# F-042 · Review — El desplegable de obras en la última fila

**Veredicto: APROBADO**

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
tests trazables, fase RED, cobertura (o N/A con motivo impreso) y campaña de
mutación con los supervivientes analizados. `sdd: false`: se valida contra los
5 `acceptance` y el plan A aprobado por el humano (descripción y `current.md`).

## Lo que se ejecutó (resultado real)

- `bash harness/init.sh`, tal cual: exit 0, ningún `[KO]`, `418 passed, 1
  skipped`; api, front y transfer en verde (por caché); `PUERTA COBERTURA: N/A
  (F-042 no cambia líneas Python de producción frente a dev)`; `PUERTA TAMAÑO`
  OK; «ENTORNO LISTO». El `skipped` es ajeno (`test_mutacion_operadores.py:314`,
  no hay `rutas_sensibles.json`).
- Como el front salía por caché, su suite **sin caché** con su venv: `100
  passed`. Los 18 de F-042 corren con node v24.14.1: **0 skipped**.
- Mutación: reejecutada la campaña manual **entera** (script del informe,
  sobre copias temporales): línea base `18 passed`, **38 filas idénticas** a
  las del informe (resultado, nº de fallos y tests que matan), 2 min 7 s. Y,
  con mi propia sustitución (sed/python, no su script), M9 (1 fallo,
  `si_cabe_justo`), M11 (2 fallos, `si_no_cabe…` y `al_agrandar…`) y M26
  (sobrevive, `18 passed`). `git status` limpio después.

## Desviaciones declaradas frente al plan

1. **Panel en `document.body`.** Aceptada: el plan lo permitía y evita que un
   `transform` futuro en un ancestro lo recorte. Huérfanos revisados en todas
   las vías que destruyen el campo: `cerrarEditor`, `abrirEditor`, `moverMes`,
   `aplicarFila`, `deshacer`, filtros y orden pasan por `renderTabla`, que
   empieza por `retirarSugerencias()`; los repintados del editor (`elegir`,
   PV, ✕) pasan por `montarAutocompletado`, que retira el anterior;
   `refrescarCeldasFila` no toca el editor. El desmontaje quita las dos
   escuchas (misma fase) y el nodo; lo fijan `…_un_solo_panel_y_sin_huerfanos`
   y M25, M27, M30-M32. No hay manejador global de «clic fuera», y los estilos
   de `.sugerencia` no dependen de `.editor` (grep comprobado).
2. **Hacia arriba solo si no cabe debajo y encima hay más sitio.** Aceptada:
   refina el plan sin contradecirlo; en el caso del fallo abre siempre hacia
   arriba. Bordes fijados: empate, cabe justo, alto nunca negativo.

## Comprobaciones pedidas

- **Teclado y búsqueda sin cambios:** el diff de `montarAutocompletado` solo
  añade el montaje/desmontaje al principio y `colocarSugerencias(...)` al final
  de `refrescar`; `elegir`, el `keydown` (flechas, Enter, Esc), el `blur` de
  150 ms y `chipEditable` («% Enter obra Enter») no cambian. Lo fijan
  `test_f042_r3_*` con el texto literal anterior. Tab no tiene manejador ni
  antes ni ahora: el `blur` oculta el panel igual que antes.
- **Ningún test anterior modificado:** solo entra el fichero nuevo
  `test_f042_sugerencias.py`. **Sin lógica de negocio en el front:** solo
  geometría de un panel; no decide qué se registra ni toca la API.
- **Límite de servicio:** solo `dedicacion-front`; `azure-apps/` no aplica.

## Checkpoints

**C1** — [x] init.sh exit 0 · [x] ficheros del arnés presentes.
**C2** — [x] una sola `in_progress` (F-042) · [x] rama
`feature/F-042-ultima-fila-autocompletado` · [x] `current.md` abre con F-042 en
curso; el resto son pendientes vivos (despliegue de F-041, producción) ·
[x] features `done`: sin cambios en esta rama.
**C3** — [x] hexagonal: N/A material, cambio solo de presentación en el front,
sin lógica de negocio · [x] primera línea con ruta (test nuevo `#
tests/test_f042_sugerencias.py`, `app.js` y `styles.css` la conservan) ·
[x] sin `console.log`, `debugger`, TODOs ni secretos; sin dependencias nuevas ·
[x] las tres trampas (escala del %, postventa, solo escribe el transfer): no
se tocan.
**C3 bis** — N/A: no añade ni modifica nada en `docs/referencia/`.
**C4** — [x] cada `acceptance` con test (tabla abajo), todos en verde ·
[x] sin red ni BBDD (node por `subprocess`, DOM mínimo de prueba) · [x] MANUAL
listada en `current.md` con comandos exactos (ver observación 1).
**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] Fase RED: traza real pegada (`15 failed, 2 passed`) con la causa literal
  (`position: absolute; top: 40px`, `anadir.appendChild(sugerencias)`); los 2
  que pasan vigilan que el teclado no cambie, correcto.
- [x] Cobertura: N/A con motivo impreso por `init.sh` (no hay Python de
  producción; `coverage` no mide JS).
- [x] Mutación automática: alcance recalculado con
  `harness.alcance.alcance_de_feature('F-042')` → `lineas={}`. Prueba de
  control: `generar_mutantes` sobre `app.js` ignorando la exclusión → 0. El
  cero es legítimo por lenguaje (la herramienta solo muta Python); se sustituye
  por la manual.
- [x] Muertos comprobados: campaña manual reejecutada entera (arriba).
- [x] Coste: 1 worker, ~3,7 s/mutante (>1 s), coherente con base ~2-2,7 s
  + `node --check`, sin `-x`. [x] Sin «⚠ CAMPAÑA NO VÁLIDA» ni base rota.
- [x] RM1: medida sobre `4e502a5` (SHA corto, unívoco); `git diff
  4e502a5..HEAD -- services/` vacío: el alcance medido es el revisado.
- [x] RM2: coherente (arriba). RM3: el único equivalente (M26) sobrevive;
  M36, equivalente en comportamiento, lo mata un test **estático** que fija
  la forma a propósito (el editor no cuelga el panel de la fila), declarado
  en el análisis: no es suite roja ni informe falso.
- [x] RM5: N/A por nivel (`estandar`: basta la justificación escrita de M26,
  que la hay y es correcta: el desmontaje es idempotente).
- [x] RM6: N/A justificado, no se quitó ninguna guarda; el `if
  (desmontarSugerencias)` sigue y M25 lo cubre.
- [x] MANUAL con fila por mutante, fichero:línea, texto exacto y nº de
  fallos; tres filas reproducidas al pie de la letra. [x] M26 analizado.
- [x] «Evidencias» completa (con workers). [x] Ningún N/A sin motivo.
**C4 ter** — N/A: el repo no declara `harness/rutas_sensibles.json`.
**C5** — [x] sin `tasks.md` (`sdd: false`): commits `F-042 T1..T4` y `F-042:`
con descripción · [x] árbol limpio, sin temporales · [x] `features.json` en
`in_progress`, coherente (el cierre lo hace el líder tras la MANUAL).

## Cobertura acceptance → test

| Acceptance | Test(s) |
|---|---|
| 1 Causa reproducida y explicada | `test_f042_r1_el_panel_es_fixed_y_no_absolute`, `…_no_vive_dentro_de_la_fila`, `…_cada_repintado_de_la_tabla_retira_el_panel` + traza RED; reproducción en navegador: MANUAL paso 4 |
| 2 Última fila (y cualquiera) abre, busca y elige con teclado | `test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado`, `…_fila_intermedia_se_ve_debajo`, `…_acompana_al_campo_con_scroll_y_resize`, `…_un_solo_panel_y_sin_huerfanos` y 8 más de `posicionSugerencias` |
| 3 Teclado y «% Enter obra Enter» sin cambios | `test_f042_r3_teclado_identico`, `…_busqueda_identica_y_luego_se_coloca`, `…_la_secuencia_pct_enter_obra_no_cambia` |
| 4 Test del front del caso de la última fila; probado por el humano | el de la fila 2; la prueba humana es la MANUAL, pendiente |
| 5 APROBADO + init.sh en verde | esta review; init.sh en verde |

## Observaciones no bloqueantes (el líder las recoge antes de pasar la MANUAL)

1. **Corregir el paso 4 de la MANUAL en `current.md`.** Tal y como está no
   describe la app: (a) tras Enter sobre la fila, el foco **ya está** en el
   campo de obra (`abrirEditor` lo enfoca), así que «Enter, `%`, Enter» no
   cuadra. Propuesta: «Enter → escribir parte de una obra → sale el
   desplegable **encima** del campo → flechas + Enter → el cursor salta al % →
   teclear % y Enter → vuelve al campo de obra → escribir otra obra → vuelve a
   salir». Así se prueba de verdad «% Enter obra Enter» en la última fila.
   (b) «Esc sin guardar» es falso: `elegir` programa el guardado y
   `cerrarEditor` guarda (en la BBDD **local**, sin Sigrid). Que diga «Ctrl+Z
   para deshacerlo después».
2. **Añadir dos comprobaciones a la MANUAL:** con el desplegable abierto,
   (a) cerrar el editor (Esc dos veces, «Hecho» o clic en otra fila) y ver que
   no queda ningún panel flotando; (b) scroll **horizontal** de la tabla: el
   panel acompaña al campo (por eso la escucha va en captura).
3. Los `test_f042_r3_*` comparan texto literal (deliberado): la próxima
   feature que toque el autocompletado tendrá que actualizarlos y decirlo.

## Automejora (propuesta, no aplicada)

Añadir a C4 (y portar a `arnes-base`): «el reviewer contrasta cada paso de
la MANUAL con el código (foco, qué guarda) y señala los que no se pueden
seguir al pie de la letra». Hoy C4 solo pide «comando exacto».
