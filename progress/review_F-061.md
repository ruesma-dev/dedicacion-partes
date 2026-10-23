<!-- progress/review_F-061.md -->
Revisión incremental desde 8be5c81 (pasada 2), delta `8be5c81`..`f688443`

# Review F-061 · búsqueda predictiva en el desplegable de incidencias

**Veredicto: APPROVED** (APROBADO).

La pasada 1 (CHANGES_REQUESTED) está en el commit `c517600`, en este mismo
fichero: allí está la revisión completa del código, los cinco puntos pedidos
y la campaña manual de 24 mutantes de JS. Lo que se aprobó en esa pasada no
se vuelve a revisar. El delta cambia `palabras_incidencia.py` (2 líneas),
`test_f061_palabras.py`, `test_f061_busqueda.py` y `progress/`. No cambia
ninguna firma pública ni ningún fichero de sitio, y `app.js` no se toca. El
alcance de la campaña sí cambia (la línea 35), así que reviso de nuevo la
mutación (ver C4 bis).

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige fase RED,
cobertura de las líneas cambiadas ≥ 80 % y mutación con los supervivientes
analizados.

## Verificación ejecutada

`bash harness/init.sh`, solo y con `.arnes_cache/suite_*.ok` borradas antes:
**ENTORNO LISTO**, ningún `[KO]`.

- Tests: raíz 418 + 1 skipped (ya estaba), api **1145** (+4), front **371**
  (+2, 0 skipped: node corrió) y transfer 1230.
- Puertas: COBERTURA `[OK]` 100 % (32/32); TAMAÑO impl 210/220.
- ruff: 277 avisos, los de antes.

`git status` queda limpio antes y después. Las pruebas de JS se hicieron sobre
una copia del front en el scratchpad.

## Los cambios requeridos de la pasada 1

1. **Dos tests de node: hecho.** Son `test_f061_r2_errata_por_letra_que_falta`
   («enfermdad» → B, «vcaciones» → V) y
   `test_f061_r2_la_subcadena_va_antes_que_la_errata` (Baca/Llevaca, «vaca» →
   S, R), los dos tal como se pidieron. **Los matan de verdad:** en una copia
   nueva de `dedicacion-front` en `HEAD` repetí los mismos 24 mutantes de la
   pasada 1 (`test_f061_*` y `test_f030_celda_pct.py`), y ahora mueren **24 de
   24**:
   - `w.length + 1` → `w.length`: 1 fallo.
   - `return 5` → `return 7`: 1 fallo.
   Los otros 22 siguen muertos. El informe trae además la traza de cada
   mutante, aplicada por el implementer.
2. **«4 workers» en «Evidencias»: hecho.** Está en la fila de la mutación
   Python.
3. **Campaña manual de JS escrita: hecho.** Tiene su fila en «Evidencias»
   (24 mutantes: 22 muertos y 2 que matan los tests nuevos) y su sección
   «Review 1: lo corregido».

## O1 (`e7a9371`): no rompe nada

`entrada.get("palabras") or []` pasa a ser `entrada.get("palabras", [])`.
Ahora solo la clave que falta cuenta como lista vacía; `""`, `0`, `false` o
`null` dan el `ValueError` de siempre.

- **Tests:** cuatro casos nuevos en el `parametrize` de config mal escrita.
  Su fase RED tiene traza real (4 failed antes del cambio).
- **Test propio cambiado:** el de lectura usaba `"palabras": None` y ahora
  usa `[]`. Es de F-061, no es ajeno, y el cambio es coherente con O1.
- **Config real:** `config.yaml` escribe `palabras: []` en CIV y CIH (no
  `palabras:` vacío), así que sigue siendo válida. Lo confirman
  `test_f061_r1_config_trae_las_palabras_aprobadas_en_su_orden` y las rutas,
  en verde.
- **Arranque:** `deps` valida con la misma función. Con la config real, la
  api arranca: los tests de contenedor (`test_f023_*`) y de rutas están en
  verde.
- **Riesgo residual:** si alguien deja `palabras:` vacío en el YAML, la api no
  arranca, con un mensaje que dice la clave y el código. Es lo que pedía O1:
  fallar, no ignorarlo.

## Checkpoints

- **C1** `[x]` init.sh con exit 0 · `[x]` los ficheros del arnés existen.
- **C2** `[x]` una sola `in_progress` (F-061) · `[x]` rama
  `feature/F-061-…` · `[x]` `current.md` encabezado por F-061, con el
  rechazo, la corrección y el relanzamiento; despliegue, MANUAL y azure-apps
  siguen listados · `[x]` las `done` están en `history.md`.
- **C3** `[x]` hexagonal sin cambios respecto a la pasada 1 · `[x]` primera
  línea con la ruta · `[x]` sin prints, secretos ni dependencias nuevas ·
  `[x]` trampas: ni %, ni postventa, ni escrituras en Sigrid.
- **C3 bis** `N/A`: no toca `docs/referencia/`.
- **C4** `[x]` cada criterio tiene su test y todos pasan; las dos reglas que
  faltaban tienen ahora el suyo · `[x]` sin red ni BBDD · `[x]` MANUAL en
  `current.md` con los pasos exactos.
- **C4 bis**
  - `[x]` rigor declarado.
  - `[x]` fase RED: trazas reales, también la de O1.
  - `[x]` cobertura `[OK]` 100 %.
  - `[x]` mutación verificada de forma independiente:
    `alcance_de_feature("F-061")` da **63** líneas (43/4/12/4) y
    `generar_mutantes` da **9**, todos en `palabras_incidencia.py`. Mismo
    alcance y mismo número que el informe. El `or` de la línea 35 ya no
    existe, de ahí los 9 frente a los 10 de antes.
  - `[x]` campaña **no reejecutada**: 205,9 s según el informe, por encima de
    60 s. Vale el recálculo puro más RM1-RM6.
  - `[x]` coste por mutante: 205,9 × 4 / 9 = 91,5 s ≥ 71,4 s de línea base.
  - `[x]` sin «CAMPAÑA NO VÁLIDA»; «Sin veredicto» 0.
  - `[x]` RM1: se midió sobre `e7a9371…`. Después solo cambia `progress/`
    (`git diff --stat e7a9371..HEAD`), así que el alcance es el mismo.
  - `[x]` RM2: 9 × 22,9 = 206 s, cuadra con el «Tiempo total».
    22,9 × 4 = 91,6 s contra 71,4 s de base: no hay salto de orden de
    magnitud.
  - RM3: ninguno de los 9 muertos es equivalente. Son las guardas de tipo y
    las de `and`/`or`, todas observables con la config mal escrita de los
    tests.
  - `N/A` RM5: el nivel es `estandar`.
  - `[x]` RM6: no se quitó ninguna guarda. O1 añade defensa: un valor
    presente que no es lista se rechaza.
  - `N/A` campaña manual de Python: la automática dio 9.
  - `N/A` análisis de supervivientes: hubo 0.
  - `[x]` «Evidencias» trae los cuatro números y los workers.
- **C4 ter** `N/A`: no existe `harness/rutas_sensibles.json`.
- **C5** `N/A` `tasks.md` (`sdd: false`); hay commits `F-061 T1..T4` y
  `F-061: …` · `[x]` sin temporales · `[x]` `features.json` dice
  `in_progress`, que es lo real hasta el cierre.

## Cobertura criterio → test

| Criterio | Test |
|---|---|
| 1 api `palabras`/`orden_busqueda`; sin entrada `[]`/`null`; sobrante ignorada | `test_f061_r1_*` (19) y `test_f030_r6_…` |
| 2 los diez casos, tildes, orden, errata | `test_f061_r2_*` (7), con los dos nuevos |
| 3 nada se pierde; con número, como hoy | `test_f061_r3_…` (>1000) y F-030 R1, R8-R13 |
| 4 recarga tras el sync | `test_f061_r4_*` (3) |
| 5 el front no decide | `test_f061_r5_…` |
| 6 INTEGRACION §5 | revisado a mano (pasada 1) |
| 7 sin red ni BBDD; init.sh verde | «Verificación ejecutada» |

## Para el líder (no bloquea)

- **Al desplegar:** api antes que front, `azure-apps/dedicacion.md` y el
  MANUAL. Todo está ya en `current.md`.
- **Para el humano** (de la pasada 1): «una errata por palabra tecleada»
  hace que «vacasiones enfremedad» tolere una errata en cada palabra.
- **Automejora para `arnes-base`:** mini-campaña manual cuando la lógica
  vive en JS. Pendiente de PARADA 1; ya está anotada en `current.md`.
