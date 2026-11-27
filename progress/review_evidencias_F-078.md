<!-- progress/review_evidencias_F-078.md -->
Revisión de evidencias desde 8ca80b5 (delta `8ca80b5..add0a77`)

# F-078 · Review de evidencias (`critico`)

**Veredicto: APPROVED** sobre HEAD `add0a77`. La principal (`progress/review_F-078.md`, al tope de 140 líneas,
por eso este fichero aparte) aprobó `8ca80b5` con la mutación «pendiente: pasada de evidencias»; este informe
cierra esos puntos. Nivel `critico` (declarado): mutación exigida, uno por línea, 60 % acotado a [100, 300],
0 supervivientes; RED y cobertura ya verificadas en la principal.

## El delta: no toca producción

`git diff --name-only 8ca80b5..HEAD -- services` da solo los dos tests de F-078; `routes.py`, `registro_sigrid.py`,
`app.js` e `index.html` son idénticos a lo aprobado. Lo demás es papeleo (`features.json`, `BACKLOG.md`,
`current.md`, `impl_F-078.md`, `mutacion_F-078.*`, la review principal). Nada invalida lo ya aprobado; RM7
(A12 y F5 de la principal) sigue en pie porque esas líneas no cambian.

## C4 bis · Campaña de mutación

- [x] **Informe generado por la herramienta**, sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto (base rota)» = 0, línea
  base declarada en los 4 workers (123,2-123,5 s).
- [x] **RM1:** SHA medido `b15042a` (HEAD tras O3). `git diff --quiet b15042a..HEAD -- services`: sin cambios, y la
  producción de `b15042a` es la de `8ca80b5`. Midió el código aprobado y el que hay en HEAD.
- [x] **Recálculo independiente** (script propio en el scratchpad con `harness.alcance.alcance_de_feature` y
  `generar_mutantes` + `seleccionar` con la regla del nivel y la semilla `20261030`): origen `rama` `b383f3c..`,
  `registro_sigrid.py` 42 líneas / 5 mutantes, `routes.py` 47 / 13; **18 generados, 9 candidatos, tope 100**, y
  los 9 elegidos coinciden **uno a uno** (fichero, línea, columna, operador, original→mutado) con
  `mutacion_F-078.json`. Campaña completa, sin muestreo, como dice el informe. `.md` y `.json` cuadran (18/9/9/0).
- [x] **Tiempo total 630,7 s > 60 s:** campaña **no reejecutada entera**; recálculo puro + RM1-RM6 + la tercera vía.
- [x] **RM2:** media por mutante juzgado con la suite entera 98,8 s < línea base 123 s, coherente con `-x` y 9 de 9
  muertos (el caso de F-038); 9 × 98,8 s ÷ 4 workers + base + arranque de copias ≈ 630 s de pared. Sin salto de
  orden de magnitud. Ver O-E1 sobre la lectura del impl.
- [x] **RM3:** ninguno de los 9 es equivalente: l. 230 (`[]` ⇒ el mes), 166 (`[]` ⇒ `None`), 168 (`"x"` ya no es
  422), 177 (`[0]` pasa a 422; el test `(b"[0]", [0])`, l. 125, lo caza), 182 (repetidos), y las inversiones de
  171, 232, 233 y 693. Muertos legítimos.
- [x] **RM4 (tercera vía), sobre copia `git archive HEAD` en el scratchpad**, con `test_f078_paquete_api.py` +
  `test_f056_trabajador_ide.py` (base: 185 passed): l. 177 `if not x:` ⇒ **2 failed**; l. 230 `if trabajador_ides:`
  ⇒ **2 failed**. Los dos veredictos «muerto» se reproducen. Árbol de trabajo sin tocar (`git status` limpio).
- [x] **RM5:** N/A, ningún mutante declarado equivalente. **RM6:** [x] ningún superviviente que matar; no se tocó
  producción ni se quitó ninguna guarda (`if valor is None`, `if x is None` y el `is not None` del filtro, intactos).
- [x] **Supervivientes y su análisis:** ninguno; ningún fichero sin mutantes; PODADO n/d (sin mapa, no se poda).
- [x] **Mutantes a mano (complementarios, `impl_F-078.md` «Pasada de campaña»):** tabla con fichero, texto exacto
  original→mutado y número de fallos. Los textos existen en HEAD (M1 l. 231, M2 l. 503, M3 l. 605, M4 l. 348,
  M5 l. 695, M6 l. 177, M7 l. 184, M8 l. 655/675). **Reproducidas al pie de la letra en la copia: M6 ⇒ 4 failed y
  M7 ⇒ 8 failed**, los mismos números que declara el impl. Cubren lo que la herramienta no genera (llamadas y
  argumentos): R1 (M1 `IN`, M4 incidencias), R2 (M7 y el generado l. 182), R3 (M6 y los generados 166/168/177),
  R4 (M8 y el 171), R5 (M5 y el 693; M2/M3, que el paquete llegue al registro en preflight y ejecutar).
- [x] **«Evidencias» del impl:** filas de mutación (herramienta y a mano) y workers completas; capa e2e N/A.
- `app.js` no se muta (lenguaje): N/A justificado; lo cubren los 63 tests node y F1-F10 de la principal.

## O3 · ruff

- [x] Cambios de los tests puramente sintácticos: concatenaciones implícitas entre paréntesis (mismo `bytes`/`str`
  resultante) y `range(0, 5)` → `range(5)`. Ninguna aserción ni dato cambia: no se debilita nada.
- [x] `ruff check` de los dos ficheros: «All checks passed!». Repositorio entero: **438 en la rama y 438 en `dev`**
  (`b383f3c`, copia principal), con ruff 0.17.6. El impl dice 439 en ambos (otra versión de ruff, presumiblemente);
  lo que importa, delta 0 respecto a `dev`, se confirma.
- [x] `test_f078_paquete_api.py` + `test_f056`: 185 passed en la copia de HEAD.

## O1, O2 y el rastro

- [x] **O1:** `features.json` l. 1286 y `BACKLOG.md` l. 143 acaban ahora en «D1, D2 y D5-D11 decididas en la (a)
  por el humano el mismo día («ok a todo»)».
- [x] **O2:** la entrada F-078 de «⚠» (`current.md` l. 492) dice que al desplegar se quita el «sin desplegar» de
  `azure-apps/dedicacion.md` (hacia la l. 521) en commit aparte.
- [x] `current.md` l. 4: review principal aprobada, campaña hecha (9/9, 8/8), O3; pendiente MANUAL T9 con su
  comando exacto y el reviewer de evidencias. «⚠» l. 492: T9 con pasos y `azure-apps` `ce8437c` pendiente de push
  con `pull --rebase` antes.

## C1 y C5

- [x] La principal ejecutó `ARNES_SIN_CACHE=1 bash harness/init.sh` entero sobre `8ca80b5` (código 0) y el
  implementer, `init.sh` sobre `12a2534` (código 0, 0 `[KO]`). Por indicación del líder no relanzo la suite sin
  caché (~30 min): el delta no toca producción y los tests cambiados los ejecuté yo. Lancé `bash harness/init.sh`
  sobre el commit de este informe: resultado al pie.
- [x] Rama `feature/F-078-registrar-por-paquetes`, árbol limpio; T9 sigue siendo la MANUAL del humano.

## Observaciones (no bloquean; el líder las recoge al pasar a `human_review`)

- **O-E1 · `impl_F-078.md`, «Pasada de campaña»:** «media 70,1 s × 4 workers = 280 s por mutante (coherente con
  la base, RM2)» es una lectura equivocada: 70,1 s es pared ÷ evaluados, y 280 s superaría el timeout efectivo de
  248 s con 0 timeouts. La cifra por mutante es la fila «Media por mutante juzgado con la suite entera», 98,8 s.
  Los números de la herramienta son coherentes; solo la frase. Corregirla o quitarla.
- **O-E2 · `current.md` l. 4:** al pasar a `human_review`, reescribir la primera línea (ya no queda el reviewer de
  evidencias) y añadir a lo que espera al humano el **push de la rama** `feature/F-078-registrar-por-paquetes`
  (o del `dev` tras el merge), que hoy solo consta en el impl («Lo que falta»).
- **O-E3 · `review_F-078.md` l. 136:** dice `routes.py` (46); la herramienta y mi recálculo dan 47 líneas en alcance.
  Errata de la principal, sin efecto.

## Automejora (propuesta, no aplicada)

- `reviewer.md`, RM2: añadir que la fila a comparar con la línea base es «Media por mutante juzgado con la suite
  entera», no «Media por mutante evaluado» (pared ÷ evaluados, que con N workers sale N veces menor). La confusión
  de O-E1 es la que esa aclaración evita, y vale para cualquier proyecto (portar a `arnes-base`).

## init.sh sobre este commit
