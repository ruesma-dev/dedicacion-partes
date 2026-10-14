<!-- progress/review_F-050.md -->
Revisión incremental desde 2e2ae97 (pasada 7) · `2e2ae97..be48d1a` (T15f y rastro del líder)

# F-050 · Review

**Veredicto (pasada 7): APPROVED** (APROBADO). T15f hace lo aprobado el
2026-10-14 y nada más; los dos tests de la lista cerrada cambian exactamente lo
aprobado; RED reproducido, Chrome lo confirma, cero supervivientes.

**Rigor:** `critico`, declarado: RED, cobertura ≥ 80 %, mutación con cero
supervivientes sin justificación aceptada y MANUAL con comando exacto.

## Pasadas anteriores (resumen)

Íntegras con `git show <commit>:progress/review_F-050.md`. **1** (completa):
CAMBIOS PEDIDOS, papeleo (`493bf35`). **2**: APROBADA, T15b (`8e9e8de`).
**3**: CAMBIOS PEDIDOS, T15c («Registrar» atascado; `49a9003`). **4**:
APROBADA (`c496af2`). **5**: CAMBIOS PEDIDOS (`a663a0a`, `scrollTop` a 0).
**6**: APROBADA (`2e2ae97`), T15e; dos observaciones para la M2.

## Pasada 7 · lo ejecutado por el reviewer

- Borrados `.arnes_cache/suite_*.ok`; `bash harness/init.sh` tal cual y solo:
  **ENTORNO LISTO**, código 0, **cero `[KO]`** (`ruff` 237, el aviso de
  siempre). Raíz **418 passed, 1 skipped** (50,5 s), api **780** (66,0 s),
  front **269** (46,5 s, con node, 0 skipped), transfer **750** (21,5 s).
  `PUERTA COBERTURA` **100,0 % (353/353)**; `PUERTA TAMAÑO` en verde
  (requirements 150/150, impl 218/220). `ruff` limpio en los 4 tests tocados.
  `git status` limpio al acabar.
- **Tests ajenos:** `git diff 2e2ae97..be48d1a` toca solo dos tests previos:
  `test_f042_sugerencias.py` (UNA línea: `BUSQUEDA_ANTES` pierde
  `.slice(0, 14)`) y `test_f050_m2_arreglos.py` (solo los valores esperados de
  `…_m2_1_la_tabla_se_ajusta_a_su_panel`: `[280, 210, 196, 169, 190]` y
  `1045px`, la opción A). Lo que dice requirements §6; ninguno más.
- **RED reproducido** (copia aislada en el scratchpad, `git archive` de HEAD
  con el `app.js` de `68e80b4`): los 16 tests nuevos + `m2_1` + `f042_r3` →
  **18 failed**, con las mismas aserciones del informe (`'203px' != '280px'`,
  `BUSQUEDA_ANTES` con `.slice`…).
- **Chrome headless** (scratchpad `rev7chrome/gen.py`: `sincronizarAnchoTabla`,
  `anchosAjustados` y `badgeTotal` REALES, `styles.css` real, tres filas: la
  de VINDEL con falta 50 %, «⇪ Sigrid» y «↩», una OK y una que sobra):

  | Panel | HEAD (ths) | Total entero | Scroll | Antes (`68e80b4`) |
  |---|---|---|---|---|
  | 1600 | 280 · 210 · 537 · 310 · **260** | sí ×3 | no | Total 195, cortado ×2 |
  | 1100 | 280 · 210 · **183 · 164** · 260 | sí ×3 | no | 190, cortado |
  | 900 | **200 · 137** · 150 · 150 · 260 | sí ×3 | no | 190, cortado |
  | 600 | 160 · 100 · 150 · 150 · 260 | sí ×3 | **sí** | 190, cortado |
  | 1600, `anchos.total = 150` | Total 260, `state.anchos` intacto | sí | no | 158, cortado |
  | 1600, sin filas | sin error | — | no | igual |

  Lo pedido, en el navegador real: Asignaciones y Partida ceden primero;
  Trabajador y Categoría solo con ellas en 150; Total nunca baja; lo guardado
  no se toca. El DOM de mentira de `t15f_total` (el `Range` devuelve lo que
  mide el contenido) se comporta como Chrome: `white-space: nowrap` en
  `.celda-total` hace que el `Range` mida el contenido entero aunque desborde.
- **Mutantes** (misma copia, suite ENTERA del front, base **269 en verde**):
  - Del informe, al pie de la letra: **X02 → 1 fallo, C06 → 2, T01 → 1,
    T15 → 4**; los del informe, en los tests que tocan.
  - Míos, fuera de la campaña: `if (celdas.length)` → `if (true)` **muerto**
    (2); sin `if (viva)` en «Completar» **muerto** (3); `Math.ceil` →
    `Math.round` **muerto** (3); `minimos` sin filtrar en la primera pasada
    **muerto** (6); segunda pasada sin el suelo de Total **muerto** (1).
  - Dos vivos, **equivalentes** (no bloquean): quitar `ev &&` en `recolocar`
    del editor (solo se usa como escucha: siempre llega un evento); y `>` →
    `>=` en `marcarActiva` (en la igualdad repone el mismo `scrollTop`).

## Lo pedido por el líder

- **Punto 1, editor** (`app.js:1402-1458`): sin `.slice`; `marcarActiva` hace
  el «nearest» a mano (el DOM de F-042 no tiene `scrollIntoView`; desviación
  anotada); `colocarSugerencias` guarda y repone el `scrollTop` (lección de
  T15e); el `scroll` de la propia lista no recoloca. Arriba si no cabe: lo de
  F-042, intacto. **«Completar»** (`app.js:906-946`): sin tope, conserva el
  desplazamiento al repintar y la activa a la vista, sin «arriba».
- **Punto 2, medición de Total** (`app.js:496-536`): `Range` sobre cada
  `td.celda-total`, el mayor, + relleno + 2 px. Se vuelve a medir al final de
  `renderTabla` (↑ ↓ y el cursor repintan entera la tabla) y en
  `refrescarCeldasFila` (guardar en el editor). Las filas solo se construyen en
  esos dos sitios (`construirFila`, `app.js:713` y `1818`).
- **T15c-T15e intactos:** `state.anchos`, la manija (`app.js:545-570`, que
  sigue llamando a `sincronizarAnchoTabla`) y mover columnas, sin cambios; el
  selector de partidas y su `recolocar` de T15e, sin tocar; sus tests en verde.

## Checkpoints (lo que toca el delta)

- **C1** [x] init.sh sin caché, ENTORNO LISTO · [x] ficheros base. **C2** [x]
  una `in_progress` · [x] rama · [x] `current.md` al día (cabecera «T15f
  terminada, en review 7», M2 (a)-(i)) · `history.md` N/A: no `done`.
- **C3** [x] límite de servicio: solo front · [x] el front no decide nada de
  negocio (anchos y desplazamiento) · [x] primera línea con ruta en los tests
  nuevos · [x] sin `console.log` ni secretos.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: sin `rutas_sensibles.json`.
- **C4** [x] sin regresiones (suite y Chrome) · [x] tests sin red ni BBDD
  (node local) · [x] MANUAL: T17 (i) 1 y 2 con comando y lo que hay que ver.
- **C4 bis**
  - [x] `rigor` · [x] RED real (impl §T15f; reproducido: 18 failed) · [x]
    cobertura 100 % · [x] Python sin cambios (164/164 de `ee4c70d`).
  - [x] MANUAL JS T15f: 34 filas con texto exacto, línea y nº de fallos;
    cuatro reproducidas · [x] cero supervivientes.
  - [x] RM1: medido en `a23a373`; después solo un `ruff ISC` en un test (sin
    efecto, comprobado) y documentos; `app.js` sin cambios desde entonces.
  - [x] RM2: 34 × 37,5 s = 1275,5 s con la suite del front en 30-87 s según la
    carga (mis mutantes: 30-64 s): coherente.
  - [x] RM3: ningún equivalente muerto (los dos equivalentes que encontré,
    vivos) · RM5 N/A: ninguno declarado · RM6 N/A: no se quita ninguna guarda.
  - [x] Evidencias, 4 números.
- **C5** [x] commits `F-050 T15f …` · [x] T15f `[x]`; T16-T18 MANUAL `[ ]`
  · [x] sin artefactos (todo en el scratchpad).

## Cobertura requisito → test (`test_f050_*`)

| R | Test |
|---|---|
| R1-R29, T15c-T15e | sin cambios desde la pasada 6 |
| T15f 1 (editor) | `t15f_obras` (5): todas las que casan; ↑ ↓ con la activa visible; la rueda no recoloca; scroll/resize conservan el sitio; arriba si no cabe |
| T15f 1 («Completar») | `t15f_obras` (3): todas; ↑ ↓ visible; clic conserva el desplazamiento |
| T15f 2 (Total) | `t15f_total` (8): orden de encogido, por columna, contenido más ancho, scroll, lo guardado, repintado y `refrescarCeldasFila`; `m2_1` |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean; que el líder las recoja)

1. Fuentes web: Total se mide con la fuente que haya al pintar (`Archivo`
   llega con `display=swap`); si llega después, el ancho se corrige en el
   siguiente repintado (↑ ↓). Mirarlo en la M2 (i) 2 con Ctrl+F5; si se ve,
   `document.fonts.ready.then(sincronizarAnchoTabla)`.
2. `renderTabla` añade una medición por repintado (cada ↑ ↓): en la M2 (d),
   con el mes entero, ver que ↑ ↓ siguen fluidos.
3. Las dos observaciones de la pasada 6 (↓ junto al borde con el ratón quieto;
   cinco filas con `ALTO_UTIL`) están en `current.md` pero no en T17: que el
   humano las vea al repetir la M2.

## Automejora (propuesta, no aplicada)

Las anteriores, más: **el reviewer suma a la muestra mutantes propios sobre
las guardas nuevas** (aquí `if (celdas.length)`, `if (viva)`): son los que
omite una campaña escrita por quien implementa.
