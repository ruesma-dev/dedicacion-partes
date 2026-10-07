<!-- progress/review_F-041.md -->
Revisión incremental desde d2bc7f9 (pasada 2), delta `d2bc7f9..5cf69d6`

# F-041 · Review — El filtro de obra casa con el texto visible (incluido Postv-)

**Veredicto: APPROVED.**

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`: fase RED,
cobertura de lo cambiado (o N/A con motivo impreso) y mutación con
supervivientes analizados. Lo aprobado en la pasada 1 hasta `d2bc7f9` (código,
tests, fase RED, campaña manual 20/20 reproducida en M4, M13 y M20, más dos
mutantes míos) queda dado por bueno. El detalle está en la pasada 1 (`67b0a34`,
este mismo fichero).

## Qué trae el delta

- `67b0a34`: el informe de la pasada 1.
- `5cf69d6`: **merge de `dev` en la rama** y `current.md` reescrito (los dos
  cambios pedidos). Trae 55 ficheros de `dev` (F-037, F-039 y F-040, ya
  desplegadas).

## Lo comprobado (con resultado real)

- **El merge no toca lo de F-041, pero sí mete código de F-039 en `app.js`.**
  `git diff d2bc7f9..HEAD -- services/dedicacion-front` **no** sale vacío:
  `app.js` +16/−5 y `test_f039_partida_fija.py` nuevo, los dos de F-039, que
  llegan con `dev`. Lo que importa sí se cumple:
  - `test_f041_filtro_obra.py` es idéntico al de `d2bc7f9`.
  - `test_f039_partida_fija.py` es el mismo blob que en `dev` (`34feaaa`).
  - El `app.js` de HEAD es el blob `a90ce23`, **el mismo** que dio el
    `git merge-tree` que ya probé en la pasada 1 (front `82 passed`).
  - `git diff dev HEAD -- app.js` da exactamente las mismas líneas +/− que el
    diff propio de F-041 (`62695e7..d2bc7f9`): al resolver el merge no se perdió
    ni se añadió nada.
  - `git diff --stat dev HEAD` solo enseña ficheros de F-041 (spec, informes,
    `app.js` y su test) más `BACKLOG.md`, `features.json` y `current.md`.
- **No invalida lo aprobado** (regla de la revisión incremental). Las funciones
  de F-041 no cambian. F-039 toca `pintarModalPreflight`, que está fuera del
  alcance de F-041 (design §2). La campaña manual se midió sobre las mismas
  líneas de F-041 y el merge solo las desplaza, así que no se repite. «Partida
  VAR fija», de F-039, va en un comentario y R13 sigue verde.
- **Suites sobre HEAD, además de init.sh:** front `82 passed` (79 + 3 de F-039);
  `test_f041_filtro_obra.py` `26 passed`, 0 skipped (node v24.14.1); transfer
  `645 passed`; api `689 passed`; `node --check static/js/app.js` OK.
- **`bash harness/init.sh`**, desde `porcentajes-f041` y tal cual: **exit 0**,
  `418 passed, 1 skipped`. Esta vez los tres servicios corrieron **sin caché**
  (api `689`, front `82`, transfer `645`). Cobertura N/A con su motivo impreso,
  topes de tamaño OK, «ENTORNO LISTO».
- `features.json` frente a `dev`: F-041 en `in_progress`, `sdd: true`, rigor
  `estandar` y la descripción con su historia. `BACKLOG.md` está regenerado e
  init.sh lo da «al día».

## Cambios pedidos en la pasada 1: estado

1. **MANUAL T6 completa: RESUELTO.** Las líneas 24-46 de `current.md` copian los
   pasos 1-10 con su texto: el arranque de api y front con su `cd` y su comando
   exactos, el paso 9 (`postv`, Ctrl+clic, **C**, «**Cerrar con Esc, SIN
   completar**», con el motivo) y el 10 («Limpiar»). Coincide con la T6 de
   `tasks.md` y con requirements §8. El front de la copia arranca sin `.env`:
   el `config/settings.py` del front trae valores por defecto para todo
   (`api_base_url=http://127.0.0.1:8090`, `default_user=local`).
2. **Restos caducados: RESUELTO.** `grep -n "Ninguna feature"
   progress/current.md` sale vacío. Tampoco quedan «No hay F-041», «D1-D6»,
   «spec lista» ni «F-029 espera…». La cabecera dice que F-041 está en curso en
   esta rama y que F-037, F-039 y F-040 se desplegaron el 2026-10-07, igual que
   «Producción, hoy» y «Lo siguiente» (reescrito: F-041, luego F-038, F-028…).
   La sección de F-041 cita esta review y su motivo.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` (F-041) · [x] rama
  `feature/F-041-filtro-obra-postventa` · [x] `current.md` sin restos (cambio 2)
  · [x] history (F-041 no deja ningún `done` nuevo).
- **C3** [x] hexagonal: N/A de fondo (JS de presentación, sin capas; pasada 1) ·
  [x] primera línea con la ruta · [x] sin prints, TODOs, secretos ni
  dependencias nuevas · [x] trampas: ni porcentajes ni escrituras; postventa
  sigue siendo una entrada aparte (`pv`).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad R1-R13 (tabla de la pasada 1), todo pasa · [x] sin red
  ni BBDD · [x] MANUAL en `current.md` con su comando exacto (cambio 1).
- **C4 bis** [x] rigor declarado · [x] fase RED con traza real (pasada 1) ·
  [x] cobertura N/A con motivo impreso por init.sh · [x] mutación: la
  herramienta da alcance vacío por el lenguaje (control del cero hecho); la
  campaña manual es reproducible, con 3 filas reproducidas y 2 mutantes propios
  · [x] coste coherente (1 worker, ~7,2 s por mutante) · [x] sin «⚠ CAMPAÑA NO
  VÁLIDA» · [x] RM1 (SHAs abreviados: aviso; el alcance no cambió desde la
  medida, tampoco con el merge) · [x] RM2 · N/A RM5 (nivel `estandar`) · N/A
  RM6 (no se quitó ninguna guarda) · [x] 0 supervivientes, nada en
  `PENDIENTE` · [x] «Evidencias» con los cuatro números y los workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1-T5 y T7 en `[x]`, cada una con su commit `F-041 Tn:`. T6 sigue
  en `[ ]` porque es la MANUAL del humano y está pendiente por definición (N/A
  justificado: se cierra cuando el humano la haga) · [x] sin temporales
  (`git status` limpio) · [x] `features.json` refleja `in_progress`.

## Lo que falta para cerrar (no es de esta review)

- **T6, la MANUAL del humano**, en local. Su resultado va a `current.md` y la
  tarea se marca `[x]` en `tasks.md`. Hasta entonces F-041 no pasa a `done`.

## Observaciones no bloqueantes

- La sección «F-028 … (plan aprobado, va después de F-037)» de `current.md`
  (línea 89) viene de `dev`. Con F-037 desplegada, ese «después de F-037» ya no
  aporta nada. Se puede podar la próxima vez que se toque el fichero.
- El encargo decía que el merge no tocaba `app.js`, y sí lo toca (F-039). Aquí
  no tiene consecuencias, pero el próximo encargo debería decir «no toca lo de
  F-041», para no mandar a buscar un diff que no sale vacío.

## Automejora

- La propuesta de la pasada 1 (SHA completo en las campañas manuales) ya está en
  `arnes-base` según el líder (`5eb72af`). Nada nuevo.
