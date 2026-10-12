<!-- progress/review_F-050.md -->
Revisión incremental desde c496af2 (pasada 5) · `c496af2..728c3f0` (T15d)

# F-050 · Review

**Veredicto (pasada 5): CHANGES_REQUESTED** (CAMBIOS PEDIDOS). El punto 1
(sombreado del bloque) está bien. El punto 2 arregla el panel minúsculo, pero
**introduce una regresión**: la lista del selector ya no se puede desplazar.
Con ↓ más allá de las filas visibles la fila activa desaparece, y con la rueda
la lista vuelve arriba. Reproducido en Chrome (abajo).

**Rigor:** `critico`, declarado: RED, cobertura ≥ 80 %, mutación con cero
supervivientes sin justificación aceptada y MANUAL con comando exacto.

## Pasadas anteriores (resumen)

Íntegras con `git show <commit>:progress/review_F-050.md`. **1** (completa):
CAMBIOS PEDIDOS, papeleo (`493bf35`). **2**: APROBADA, T15b (`8e9e8de`).
**3**: CAMBIOS PEDIDOS, T15c («Registrar» atascado; T17 «(a)-(g)»; `49a9003`).
**4**: APROBADA; obs.: `trabajador_ide` crudo (→ F-056), análisis anterior
tras un error (M2 (h) 5), manija (M2 (h) 1) (`c496af2`).

## Pasada 5 · lo ejecutado por el reviewer

- Borrados `.arnes_cache/suite_*.ok`; `bash harness/init.sh` tal cual y solo:
  **ENTORNO LISTO**, ningún `[KO]` (`ruff` 237, el aviso de siempre). Raíz
  **418 passed, 1 skipped** (43,9 s), api **780** (34,4 s), front **241**
  (23,5 s, con node, 0 skipped), transfer **750** (8,0 s). `PUERTA COBERTURA`
  **100,0 % (353/353)**; `PUERTA TAMAÑO` en verde.
- **Copia aislada** en el scratchpad (front + transfer, sin `.venv`, con el
  `.venv` del front del repo): base **241 passed**. Reproducidas al pie de la
  letra cuatro filas de la campaña manual: **S04 → 1 fallo, S07 → 4, C01 → 2,
  U04 → 3**, las del informe.
- **Chrome headless** (`chrome.exe --headless=new --dump-dom`, página local en
  el scratchpad con el `styles.css` real, el `posicionSugerencias` de HEAD
  extraído de `app.js`, el `recolocar` de HEAD y el de `c496af2`, y 95 filas
  como la CI de la 0694). Resultado:

  | Acción | `recolocar` de HEAD | `recolocar` de `c496af2` |
  |---|---|---|
  | ↓ hasta la fila 40 (`scrollIntoView` y luego `recolocar`, como `pintar`) | `scrollTop` 790 → **0** | 790 → 790 |
  | Rueda: `scrollTop = 300` y evento `scroll` de la lista (llega a la escucha de captura de `window`) | 300 → **0** | 300 → 300 |

  Causa: `panel.style.maxHeight = ""` (`app.js:1556`) y la lectura de
  `offsetHeight` fuerzan un *layout* en el que `.lista-partidas` ya no
  desborda (el panel no tiene `max-height` en el CSS, a diferencia de
  `.sugerencias` de F-042), y el navegador recorta su `scrollTop` a 0. Pasa
  en cada `pintar` (`app.js:1643-1644`) y en cada `scroll` de la propia lista
  (`window.addEventListener("scroll", recolocar, true)`, `app.js:1573`).
  Afecta al cuadrante y al modal (mismo código), y rompe la M2 (b) «↑ ↓
  Enter» en cuanto la lista pasa de lo visible (95 CI, 727 CD en la 0694).
  Los tests de node no lo ven: su DOM de mentira no modela `scrollTop`.

## Lo pedido por el líder

- **Captura 1 (RAFAEL), cubierta.** El *hover* pone `resaltada` en todas las
  `<tr>` del bloque (`mouseenter`/`mouseleave`, que no se disparan al pasar de
  celda en celda; la salida va antes que la entrada al cambiar de subfila). Las
  celdas con `rowSpan` cuelgan de la primera `<tr>`: también se sombrean.
  `tr.fila:hover` desaparece. `.resaltada` tiene la misma especificidad que
  `.seleccionada`, `.editando` y `.multi` y va antes: cursor (con sus barras de
  T15c), editor y selección múltiple siguen mandando. El cursor y la selección
  ya iban por bloque desde T15c (`construirFila` marca todas las subfilas). La
  fila del editor (`tr.fila-editor`) no lleva `fila`: no cambia.
- **Alto mínimo, cubierto en la geometría.** Revisado `posicionSugerencias` a
  mano: el panel queda ≥ `min(240, alto − 16)`, arriba si debajo no cabe y
  arriba hay más, o dentro de la ventana tapando el ancla; cuadrante y modal
  usan el mismo `montarSelectorPartida`. Pero ver el cambio 1.
- **F-042 intacto.** Con `minimo = 0`, `suelo = 0`: `quiere = alto`,
  `altoMax` y `top` dan lo mismo que antes (`min(alto, altoMax) = altoMax`) y
  no entra la rama nueva. `colocarSugerencias` no cambia; `test_f042_*` sin
  tocar y en verde; el test de control compara con y sin el 4.º argumento.
- **Tests previos:** el delta solo **añade** dos ficheros; ninguno cambia.
- **M2 (h) 2 y 3:** se pueden seguir (trabajadores con nombre, alturas de
  ventana y modal). Les falta desplazar la lista (cambio 2).

## Checkpoints (lo que toca el delta)

- **C1** [x] init.sh sin caché, ENTORNO LISTO · [x] ficheros base. **C2** [x]
  una `in_progress` · [x] rama · [x] `current.md` al día · `history.md` N/A: no `done`.
- **C3** [x] límite de servicio: solo front · [x] el front no decide nada de
  negocio (colocación y sombreado) · [x] primera línea con ruta en los dos
  tests · [x] sin `console.log` ni secretos.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: sin `rutas_sensibles.json`.
- **C4** [ ] **sin regresiones de comportamiento: la lista del selector no se
  desplaza** (cambio 1) · [x] tests sin red ni BBDD (node local) · [ ] MANUAL
  (h) 3 no comprueba el desplazamiento de la lista (cambio 2).
- **C4 bis**
  - [x] `rigor` · [x] RED real (impl §T15d: 6 y 11 fallos con su salida; los 2
    que pasan, controles) · [x] cobertura 100 % · [x] Python sin cambios (164/164).
  - [x] MANUAL JS/CSS T15d: 26 filas con texto exacto, línea y nº de fallos;
    1.ª pasada 23/25 con S02 y S04 vivos, cerrados con test; cuatro filas
    reproducidas · [x] cero supervivientes.
  - [x] RM1: medido en `5bbda9e`; `728c3f0` solo toca `progress/` y `tasks.md`.
  - [x] RM2: 26 × ~22 s ≈ 570 s frente a 526,7 s (suite entera, sin `-x`): coherente.
  - [x] RM3: ningún equivalente muerto (S16 `240`→`200` cambia la geometría;
    C03, la cascada) · RM5 N/A: ninguno declarado · RM6 N/A: no se quita
    ninguna guarda · [x] Evidencias, 4 números.
- **C5** [x] commits `F-050 T15d: …` (`975bd67`, del líder, solo docs) · [x]
  T15d `[x]`; T17-T18 MANUAL pendientes · [x] sin artefactos (todo en el scratchpad).

## Cobertura requisito → test (`test_f050_*`)

| R | Test |
|---|---|
| R1-R29, T15c, rev. 3 | sin cambios desde la pasada 4 |
| T15d 1 | `t15d_sombreado` (6): bloque, cambio de subfila, otro trabajador, sin carga, CSS y orden de la cascada |
| T15d 2 | `t15d_selector` (14): geometría (borde, poco sitio, lleno, debajo, ventana 300 y 200, F-042) y panel real en cuadrante y modal |

## Cambios requeridos

1. **La lista del selector debe poder desplazarse** (`app.js:1555-1566`,
   `recolocar`). Medir el alto natural sin perder el `scrollTop` de
   `.lista-partidas`: p. ej., guardarlo antes de `maxHeight = ""` y
   reponerlo tras fijar el nuevo `maxHeight`; y no recolocar por los `scroll`
   que nacen dentro del propio panel (`ev.target` dentro de `panel`,
   `app.js:1573`). Comprobar que en `pintar` la fila activa sigue visible tras
   `recolocar` (`app.js:1643-1644`).
2. **Test RED que lo cace**: el DOM de mentira de `t15d_selector` debe
   modelar lo que hace el navegador (sin `max-height`, leer `offsetHeight`
   recorta el `scrollTop` de la lista a 0) y comprobar que tras ↓ ×N y tras un
   `scroll` de la lista el `scrollTop` se conserva. RED real en el informe y
   su mutante en la campaña manual (quitar la reposición).
3. **M2 (h) 3 en `tasks.md`**: añadir «con la lista abierta (CI de la 0694),
   rueda del ratón hasta abajo y ↓ más allá de lo visible: la lista baja y la
   fila activa se ve», en el cuadrante y en el modal.

## Observaciones (no bloquean; que el líder las recoja)

1. Con el ratón quieto sobre un bloque que se repinta, el nuevo no sale
   sombreado hasta moverlo (el `:hover` se recalculaba solo). M2 (h) 2.
2. `ALTO_UTIL = 240` es estimado: confirmar en la M2 que se ven cinco filas.

## Automejora (propuesta, no aplicada)

Casilla MANUAL con texto exacto y SHA (pasada 2); test por orden de llegada en
peticiones concurrentes (pasada 3); y **en C4, para el front: un cambio de
medición o de `max-height` de un panel con lista exige comprobar en navegador
real (o en un DOM que lo modele) que su `scrollTop` sobrevive**: los dobles
de node no recortan el desplazamiento y aquí dieron 26/26 sin verlo.
