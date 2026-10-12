<!-- progress/review_F-050.md -->
Revisión incremental desde a663a0a (pasada 6) · `a663a0a..c986c29` (T15e)

# F-050 · Review

**Veredicto (pasada 6): APPROVED** (APROBADO). Los tres cambios de la pasada 5
están hechos y la observación 1 recogida. El arreglo funciona en Chrome real
(abajo), el DOM de mentira reproduce lo que hace Chrome y los tests caen si se
quita la reposición. Sin regresiones en T15d ni en F-042.

**Rigor:** `critico`, declarado: RED, cobertura ≥ 80 %, mutación con cero
supervivientes sin justificación aceptada y MANUAL con comando exacto.

## Pasadas anteriores (resumen)

Íntegras con `git show <commit>:progress/review_F-050.md`. **1** (completa):
CAMBIOS PEDIDOS, papeleo (`493bf35`). **2**: APROBADA, T15b (`8e9e8de`).
**3**: CAMBIOS PEDIDOS, T15c («Registrar» atascado; T17 «(a)-(g)»; `49a9003`).
**4**: APROBADA; obs.: `trabajador_ide` crudo (→ F-056), análisis anterior
tras un error (M2 (h) 5), manija (M2 (h) 1) (`c496af2`). **5**: CAMBIOS
PEDIDOS (`a663a0a`): el sombreado de T15d bien, pero `recolocar` quitaba el
`max-height` para medir y Chrome ponía a 0 el `scrollTop` de la lista (↓ más
allá de lo visible y la rueda la devolvían arriba); pidió reponerlo, no
recolocar por el `scroll` de la propia lista, test RED con un DOM que lo
modele y la M2 (h) 3 ampliada.

## Pasada 6 · lo ejecutado por el reviewer

- Borrados `.arnes_cache/suite_*.ok`; `bash harness/init.sh` tal cual y solo:
  **ENTORNO LISTO**, ningún `[KO]` (`ruff` 237, el aviso de siempre). Raíz
  **418 passed, 1 skipped** (31,5 s), api **780** (22,0 s), front **253**
  (18,1 s, con node, 0 skipped), transfer **750** (3,9 s). `PUERTA COBERTURA`
  **100,0 % (353/353)**; `PUERTA TAMAÑO` en verde. `ruff` limpio en los dos
  tests tocados. `git status` limpio al acabar.
- **Chrome headless** (scratchpad `rev6/gen.py`: `posicionSugerencias` y el
  `recolocar` REAL de HEAD extraídos de `app.js`, `styles.css` real, 95 filas;
  variantes «sin reposición» y «sin guarda» por sustitución de texto):

  | Acción | HEAD | sin reposición (V01) | sin guarda (V02) |
  |---|---|---|---|
  | `scrollIntoView` fila 40 y `recolocar` (como `pintar`) | 790 → **790**, fila visible | 790 → 0, no visible | 790 → 790 |
  | `max-height = ""` y leer solo `scrollTop` | 0 (recorta) | 0 | 0 |
  | Rueda: `scrollTop = 600` + `scroll` de la lista | 600, panel quieto | 600 (sale por la guarda) | 600 (repuesto) |
  | `scroll` de `document` con el ancla movida 100 px | 400, top 134 → 234 | **0** | 400 |

  Conclusión: el recorte a 0 lo hace Chrome al medir **y también al leer
  `scrollTop`** sin `max-height` (lo que modela `7ecc6e3`); el DOM de mentira
  predice lo mismo en cada caso. La guarda no hace falta para la lista (la
  reposición la cubre) pero sí para que la rueda no mueva el panel: es lo que
  comprueba `…la_rueda…` (`top` sigue en 134 aunque el ancla cambie).
- **RED reproducido** (copia aislada `rev6/copia`, `git archive` de HEAD, con
  el `app.js` de `a663a0a`): `t15d_selector` + `t15e_sombreado` → **12 failed,
  14 passed**, las mismas 12 líneas `E` del informe (`[25, 0, False, '658px']`,
  `[0, '334px', '458px']`, `[0, '234px', '558px']`…). Los 14 que pasan, los de
  T15d sin cambios.
- **Mutantes reproducidos** al pie de la letra (suite entera del front, base
  253 en verde): **V01 → 4 fallos, V07 → 4, V02 → 2, W01 → 1, W10 → 1**, los
  del informe y en los tests que tocan (↓ ×25 y scroll/resize para V01/V07; la
  rueda para V02; repintado y `#cuerpo` para W01/W10).

## Lo pedido por el líder

- **Desplazamiento de la lista (cambio 1), cubierto.** `recolocar(ev)` guarda
  el `scrollTop` antes de `maxHeight = ""` y lo repone tras fijar el nuevo
  (`app.js:1576-1590`); un `scroll` nacido dentro del panel no recoloca; el
  `resize` no llega a `contains` (con `window` lanzaría `TypeError`, también
  modelado). En `pintar` (`app.js:1667-1668`) la activa sigue visible tras
  `recolocar` (test ↓ ×25 y Chrome). La reposición dispara un `scroll` de la
  lista que la guarda corta: sin bucle.
- **DOM de mentira (cambio 2), fiel.** Vista = alto del panel − cabecera,
  `scrollTop` recortado a lo que desborda, `scrollIntoView` «nearest», recorte
  a 0 sin `max-height` al leer `offsetHeight` o `scrollTop`. Contrastado arriba
  con Chrome: mismos resultados en las cuatro acciones.
- **T15d intacto.** Los 14 tests de T15d sin tocar sus asserts (el diff de
  `test_f050_t15d_selector.py` solo amplía el DOM y añade 6 tests al final) y
  en verde; `posicionSugerencias` y `ALTO_UTIL` sin cambios. **F-042 intacto**:
  `colocarSugerencias` y `test_f042_*` sin tocar, en verde.
- **Sombreado bajo el ratón quieto (obs. 1), cubierto.** `state.ratonIde` y
  `resaltadas`; `construirFila` sombrea el bloque repintado de ese trabajador;
  `mouseenter` apaga el que hubiera; `mouseleave` de la fila o de `#cuerpo`
  apaga el que haya. `moverSeleccion` → `renderTabla`: ↑ ↓ repinta de verdad,
  así que la M2 lo prueba. Límite declarado en el informe (tabla desplazada
  bajo el ratón quieto): ver observación 1.
- **Tests anteriores:** ninguno de otra feature; de F-050, solo el DOM de `t15d_selector`.
- **M2 (h) 2 y 3 en `tasks.md`:** (h) 2 añade «ratón quieto, ↑ ↓: sigue
  sombreado; al sacarlo de la tabla, ninguno»; (h) 3 añade «CI de la 0694,
  rueda hasta abajo y ↓ más allá de lo visible: la lista baja y la activa se
  ve, en el cuadrante y en el modal». Lo pedido, ejecutable por el humano.

## Checkpoints (lo que toca el delta)

- **C1** [x] init.sh sin caché, ENTORNO LISTO · [x] ficheros base. **C2** [x]
  una `in_progress` · [x] rama · [x] `current.md` al día · `history.md` N/A: no `done`.
- **C3** [x] límite de servicio: solo front · [x] el front no decide nada de
  negocio (colocación, desplazamiento y sombreado) · [x] primera línea con
  ruta en el test nuevo · [x] sin `console.log` ni secretos.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: sin `rutas_sensibles.json`.
- **C4** [x] sin regresiones (Chrome y suite) · [x] tests sin red ni BBDD
  (node local) · [x] MANUAL (h) 2 y 3 con lo de T15e.
- **C4 bis**
  - [x] `rigor` · [x] RED real (impl §T15e: 12 fallos, reproducidos) · [x]
    cobertura 100 % · [x] Python sin cambios (164/164 de `ee4c70d`).
  - [x] MANUAL JS T15e: 23 filas con texto exacto, línea y nº de fallos;
    cinco reproducidas · [x] cero supervivientes. El `|| []` sin mutar,
    justificado (defensa redundante; el `state` siempre trae el campo).
  - [x] RM1: medido en `7ecc6e3`; después solo `check=False` en un test
    (sin efecto) y documentos.
  - [x] RM2: 23 × ~17 s ≈ 398,8 s con la suite del front en 16-18 s: coherente.
  - [x] RM3: ningún equivalente muerto (V03 sin `ev.type` lanza `TypeError`
    en el `resize` en el navegador; W15 `null` rompe la salida de `#cuerpo`)
    · RM5 N/A: ninguno declarado · RM6 N/A: no se quita ninguna guarda.
  - [x] Evidencias, 4 números.
- **C5** [x] commits `F-050 T15e: …` · [x] T15e `[x]`; T16-T18 MANUAL `[ ]`
  (M1 OK según el informe) · [x] sin artefactos (todo en el scratchpad).

## Cobertura requisito → test (`test_f050_*`)

| R | Test |
|---|---|
| R1-R29, T15c, rev. 3, T15d | sin cambios desde la pasada 5 |
| T15e 1-2 | `t15d_selector` (+6): ↓ ×25 baja la lista y la activa se ve; la rueda no la devuelve arriba ni mueve el panel; scroll de fuera y `resize` recolocan conservándola (cuadrante y modal) |
| T15e obs. 1 | `t15e_sombreado` (6): estado inicial, repintado sombreado, otro bloque lo apaga, salida de la fila vieja, T15d igual, salida de `#cuerpo` |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean; que el líder las recoja)

1. En la M2 (h) 2, mirar también ↓ junto al borde inferior (la tabla se
   desplaza bajo el ratón quieto): el informe declara que el sombreado sigue
   al trabajador hasta mover el ratón. Aceptable si el humano lo ve así.
2. Sigue abierta la obs. 2 de la pasada 5: confirmar en la M2 que con
   `ALTO_UTIL = 240` se ven cinco filas.

## Automejora (propuesta, no aplicada)

Las de pasadas anteriores, más: **cuando un test modele en un DOM de mentira
un comportamiento del navegador, el reviewer contrasta ese modelo con Chrome
headless en el mismo escenario** (aquí, `rev6/gen.py`): uno infiel esconde la regresión (T15d).
