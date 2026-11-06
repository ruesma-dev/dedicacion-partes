<!-- progress/review_F-054.md -->
Revisión incremental desde 9c5e629 (pasada 10; la 9 aprobó `30b8171`, más `9c5e629` con O15), HEAD `5ca4838`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 10 (T27/R48, la ventana de «Sincronizar Sigrid» en tres zonas)

**Veredicto: CAMBIOS REQUERIDOS (CHANGES_REQUESTED).** El código y los tests están bien: el
cambio queda dentro de esa ventana, los tests de T23-T26 siguen intactos y la mutación manual es
suficiente. Bloquea el **rastro**: la spec no recoge la quinta regla CSS (el retoque de bordes) y
`current.md` sigue dando por pendiente la MANUAL de R48, que `manual_F-054.md` da por hecha
(«perfecto»). Solo hay que tocar documentación.

**Rigor:** `critico` (`features.json`): RED, cobertura, mutación con 0 supervivientes, RM5 y MANUAL.
Anteriores: 9, 8, 7, 6 y 2 APROBADAS; 5, 4 y 3 CAMBIOS solo por `current.md`; 1 RECHAZADA. La
review 10 anterior, sobre la primera versión, no dejó nada en este fichero: se sustituye la 9.

## Delta revisado (`git diff 9c5e629..HEAD`, 11 ficheros, 19 commits)

- **`app.js`, solo `pintarTraerSigrid`.** `.acciones-traer` sale del `if (modelo.filas.length)`.
  Da el mismo HTML, porque `casillas = modelo.filas.some(...)` implica que hay filas. Las dos tablas
  y el `<h3>` «No se traen» van en `<div class="zona-traer" id="traer-zona">`, que se pinta siempre y
  se cierra justo antes de `.pie-modal`. Es hija directa de `.modal` (`abrirModal`, l. 3381, sin
  cambios). Los `id` y las escuchas no cambian.
- **`styles.css` (l. 609-628).** Hay cinco reglas, todas bajo `.modal:has(> .zona-traer)` o
  `.zona-traer`, y la clase solo la pinta `pintarTraerSigrid` (grep en `static/` y `templates/`).
  Por eso no tocan el modal del registro, «Completar al 100 %» ni el cuadrante. `.modal` sigue con
  `padding: 22px 26px`, sin `--modal-pad-top` ni `thead:has(`. Solo hay dos reglas `sticky`:
  `.topbar` y `.zona-traer thead`. La primera versión (`ff3d1ac`, `c9611c3`) no deja rastro en el código.
- **Tests.** El diff de `test_f054_traer_front.py` **solo añade líneas** (+208, −0) y no cambia
  ningún otro fichero de test, así que T9 y T23-T26 no se han debilitado. Los 15 `r48_*` comprueban
  las reglas con selector y declaraciones exactas, que ninguna otra nombra `.zona-traer`, el orden
  respecto a `.modal .tabla-reg`, que no haya bordes arriba ni a la izquierda en `th` y `td`, y el
  HTML por zonas en cuatro escenarios. También comprueban que la zona es hija directa y que el
  registro no la lleva.
- **Convenciones:** primera línea con ruta; sin `console.log`, `print` ni secretos.

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados, sin pipes): ver el resultado al pie · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` (F-054) · [x] rama `feature/F-054-sync-trae-porcentajes` ·
  **[ ] `current.md` coherente** (CR2) · [x] history.
- **C3** [x] hexagonal (el delta es solo front de presentación) · [x] primera línea · [x] sin debug
  ni secretos · [x] front sin negocio (marcado y CSS).
- **C3 bis** N/A: el delta no toca `docs/referencia/`.
- **C4** [x] R48 con tests (tabla abajo) · [x] sin red ni BBDD · [x] MANUAL de R48 hecha por el
  humano (`manual_F-054.md:24`, sobre `083076c`).
- **C4 bis** [x] rigor declarado · [x] RED real (`impl_F-054.md:200`, `12 failed`, con mensajes, sobre
  `c9611c3`) · [x] cobertura `[OK]` 99,5 % (793/797; no mide JS ni CSS) · [x] mutación Python: el
  delta no toca ningún `.py` del alcance (solo un test). El informe de `353d290` sigue valiendo (RM1).
  · [x] mutación manual de `app.js`/CSS: **campaña 11, 38/38** (28 de CSS: cada declaración, valores
  vecinos, cada selector, la regla y la variable de `c9611c3`; 10 de marcado: pie, acciones, título o
  «Ningún trabajador» dentro, «No se traen» fuera, zona sin cerrar, sin `id`, con otra clase,
  condicional o anidada). **Campaña 12, 12/12** (la regla de bordes, su posición y los bordes que
  saldrían dobles). La columna de texto de la tabla va recortada (11) o falta (12), pero el script de
  cada campaña lleva los pares original → mutado **exactos**, así que se pueden reproducir. **Reproduje
  dos al pie de la letra** sobre una copia en mi scratchpad (RM4): H12 muere en `[zona]` y K8 en
  `…_los_bordes_viajan…`, como dice el informe. En la copia, `…_registro_no_lleva_la_zona` falla
  también sin mutar, porque necesita `dedicacion-transfer` al lado. Es efecto de la copia, no del
  mutante. · [x] RM2: líneas base de 22,4 s y 5,9 s, coherentes con el fichero y con `-k r48` · [x] RM3:
  ningún equivalente sale muerto · [x] RM5 N/A: ninguna campaña declara equivalentes · [x] RM6 N/A: no
  se quita ninguna guarda · [x] «Evidencias» con los cuatro números (fila `app.js`/CSS al día).
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T27 `[x]` con commits `F-054 T27: …` · T18-T20 `[ ]` por ser MANUAL, legítimo ·
  **[ ] T27 describe lo que hay** (CR1) · [x] árbol limpio antes del informe.

¿Es suficiente la mutación? Sí. Cubre cada declaración y cada selector de las cinco reglas, y cada
forma razonable de colocar mal la zona en el marcado. Lo que ninguna mutación ve (hueco,
transparencia, alineación, `:has` en el navegador) lo cubrió la MANUAL del humano.

## Cambios requeridos

1. **La spec no recoge el retoque `083076c`.** `tasks.md:34` (T27) define las reglas «(a)-(d)» y pide
   verificarlas «con **exactamente** esos selectores y declaraciones». Su lista cerrada de tests no
   nombra `test_f054_r48_los_bordes_viajan_con_la_cabecera_sin_dobles`. `design.md:188-193` tampoco
   menciona la quinta regla. En cambio, el código lleva `.zona-traer .tabla-reg { border-collapse:
   separate; border-spacing: 0; }` (`styles.css:628`) y el test dice «Solo esas **cinco** reglas»
   (`test_f054_traer_front.py:1136`). Grep de `separate` y `border-collapse` en `specs/F-054-*`: cero
   resultados. Hay que añadir a T27 la regla (e) con su motivo (la franja de 1 px de la MANUAL del
   2026-11-06; sin bordes dobles porque ninguna celda lleva borde arriba ni a la izquierda; va después
   de `.modal .tabla-reg`), el test nuevo a la lista cerrada y la campaña 12 a la verificación (8).
   Lo mismo en una línea de `design.md` §7. `impl_F-054.md:199` también dice «las cuatro reglas
   exactas»: hay que añadir que el retoque suma la quinta.
2. **`current.md` no dice lo mismo que `manual_F-054.md`.**
   - La l. 4 acaba en «falta review y repetir la MANUAL de T18 paso 2 con lo de R48», pero
     `manual_F-054.md:24` (`5ca4838`) la da por comprobada («perfecto»). Hay que reescribir esa
     cola: la MANUAL de R48 está hecha (parte visual de T18 paso 2) y queda la review 10.
   - En las l. 173-181, el bloque de R48 dentro de T18 paso 2 sigue como pendiente. Hay que marcarlo
     **HECHO el 2026-11-06 sobre `083076c`** y dejar pendiente el resto del paso 2 y los pasos 3 y 4,
     como en `manual_F-054.md`. `tasks.md:25` (T18) se trata igual.
   - Las l. 96 («**Siguiente:**»), 99 (título de la sección) y 602 («**Hoy (2026-11-04):**») no
     nombran T27 ni R48. Hay que añadir «T27/R48 hecha y comprobada por el humano (2026-11-06)» a
     las tres.

   La mención de «22 px» en la l. 4 es historia del rechazo, no describe la versión vigente, y puede
   quedarse. Aun así, esa línea ya es ilegible: se puede resumir la historia de T27 en una frase
   («primera versión rechazada dos veces; rehecha en tres zonas, `f82fd6b` + `083076c`») y enlazar
   `impl_F-054.md` §T27.

En la review 11 solo hace falta comprobar estos dos puntos (más `init.sh`). El código queda aprobado
hasta `5ca4838`.

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R47 | como en las reviews 7-9 (`test_f054_*` de los tres servicios) |
| R48 | `test_f054_traer_front.py` `r48_*` (15) · campañas manuales 11 y 12 · MANUAL del humano (`manual_F-054.md:24`) |
| R29 | `ARCHITECTURE.md` 23, `INTEGRACION.md` §5; `azure-apps`, en T20 |
| R30, R37 | MANUAL T10 (hecha), T18 (paso 1 y la parte de R48 de su paso 2, hechos), T19 |

## Automejora (propuesta, no aplicada; para `reviewer.md` y `arnes-base`)

Un retoque que nace de la MANUAL (aquí, `083076c`) tiende a entrar en código, tests y campaña sin
pasar por `tasks.md`. Propuesta para `implementer.md`: «un cambio posterior a la spec, aunque lo pida
el humano en la MANUAL, actualiza primero la tarea en `tasks.md` (qué regla, qué test, qué
verificación) y después el código».

## Resultado de `init.sh`

`bash harness/init.sh` con `suite_*.ok` borrados y sin pipes: código 0, ningún `[KO]` y «ENTORNO
LISTO». Raíz: 418 passed y 1 skipped. Api: 1504 passed. Front: 544 passed, 2 más que en
`impl_F-054.md` por el retoque. Transfer: 1887 passed. Cobertura 99,5 % (793/797). Tamaño dentro de
los topes, con esta review en 119/140.
