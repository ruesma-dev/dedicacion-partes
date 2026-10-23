<!-- progress/review_F-061.md -->
Revisión completa (pasada 1), `dev` (`87d1733`) .. `8be5c81`

# Review F-061 · búsqueda predictiva en el desplegable de incidencias

**Veredicto: CHANGES_REQUESTED** (RECHAZADO). El código es correcto y
cumple el contrato. Lo que falla son los tests de node: dos cambios
razonables en `app.js` los pasan en verde (punto 4). Además, «Evidencias» no
da el número de workers. Los arreglos son de tests y de papeleo; no hay que
tocar código de producción.

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige fase RED,
cobertura de las líneas cambiadas ≥ 80 % y mutación con los supervivientes
analizados. `sdd: false`: el contrato son el `description` (con las dos
decisiones del humano) y los 7 `acceptance`.

## Verificación ejecutada

`bash harness/init.sh`, solo, con `.arnes_cache/suite_*.ok` borradas:
**ENTORNO LISTO**, sin `[KO]`. Raíz 418 + 1 skipped (previo), api 1141, front
369 (0 skipped: node corrió), transfer 1230; COBERTURA 100 % (32/32), ruff
277 (previos). Árbol limpio; los mutantes de JS, en una copia del scratchpad.

## Los cinco puntos pedidos

1. **Test ajeno: cumple.** Contra `dev`, el único test que ya existía y
   cambia es `test_f030_catalogo.py`. En `test_f030_r6_…` los tres dicts
   mantienen `codigo`/`letra`/`nombre` y solo ganan `"palabras"` y
   `"orden_busqueda"` (CIA 1, CIE 0, CIV 5). Hay además un comentario de 2
   líneas que cita la autorización; no cambia ninguna aserción.
2. **El front no decide: cumple.** `categoria`, `peso` y el `sort` solo
   eligen qué candidatas salen y en qué orden. Se siguen pintando `letra` y
   `nombre`, y `alElegir(t)` recibe el mismo objeto del catálogo. Las
   palabras extra ni se pintan ni viajan. Lo fija `test_f061_r5_…`.
3. **Criterios contra los tests: cumple, con los huecos del punto 4.** Los
   diez casos, uno a uno, en `test_f061_r2_los_casos_…`, con el catálogo
   real: sin «(X)», que quita `letra_y_nombre`; los comprobé también a mano.
   Las categorías, con ESCALERA (`orden_busqueda` al revés); el desempate y
   las nulas detrás, con `…_empate_…`; la recarga, con `test_f061_r4_*`. §5
   de `INTEGRACION.md` recoge los dos campos, el orden por letra y la recarga.
4. **El JS en los tests de node.** Apliqué a mano 24 mutantes razonables en
   `app.js` y corrí `test_f061_*` + `test_f030_celda_pct.py` en cada uno.
   Mueren 22: umbral 4→3 y 4→5, `<=1`→`<=2`, sin transposición OSA,
   `every`→`some` en las categorías 3, 4 y 6, intercambiar 3↔4, quitar las
   categorías 0, 1, 2 o 5, palabras extra sin trocear o sin usar, nulas
   delante, desempate quitado o invertido, trocear por espacios, sin recarga
   y recarga antes de `cargarPeriodo`. **Sobreviven 2:**
   - `Math.min(p.length, w.length + 1)` → `w.length`. La errata por **letra
     que falta** deja de funcionar («enfermdad» ya no encuentra B) y ningún
     test lo nota. Hay casos de sustitución, transposición y letra de más,
     pero ninguno de letra de menos.
   - `includes(q)) return 5;` → `return 7;`, es decir, la subcadena pasa
     detrás de la errata. Contradice el orden del contrato («subcadena … y,
     al final, … errata»). Ninguna búsqueda de los tests tiene a la vez un
     candidato por subcadena y otro por errata.
5. **Decisiones del implementer: las dos encajan.**
   - «Una errata por palabra tecleada»: el contrato dice errata «en palabras
     tecleadas de 4 o más letras»; leerlo por palabra es lo natural y ningún
     criterio lo contradice («vacasionez», dos erratas → [], está afirmado).
     Que el humano sepa que «vacasiones enfremedad» tolera una en cada una.
   - Config en cada petición: `cargar_config` va con `lru_cache` y es la
     misma fuente de `construir_contenedor`, con precedente en el export
     (`routes.py:485`); `deps` valida al arrancar. Coste: parsear 7
     entradas. Editar la lista no exige código, sí reinicio o redespliegue.

## Checkpoints

- **C1** `[x]` init.sh con exit 0 · `[x]` los ficheros del arnés existen.
- **C2** `[x]` una sola `in_progress` (F-061) · `[x]` rama correcta · `[x]`
  current.md encabezado por F-061, con despliegue, MANUAL y azure-apps (el
  resto es estado vivo de producción) · `[x]` las `done` están en history.
- **C3** `[x]` hexagonal: función pura en `application/`; el adaptador lee
  la config como ya hacía el export · `[x]` primera línea con la ruta ·
  `[x]` sin prints, secretos ni dependencias nuevas · `[x]` trampas: ni %,
  ni postventa, ni escrituras en Sigrid; solo api y front.
- **C3 bis** `N/A`: no toca `docs/referencia/`.
- **C4** `[ ]` todos los criterios tienen test y pasan, **pero** dos reglas
  del contrato no las fija ningún test: errata por letra que falta y
  subcadena antes de errata (punto 4) · `[x]` sin red ni BBDD · `[x]` MANUAL
  en current.md con los pasos exactos.
- **C4 bis**
  - `[x]` rigor declarado · `[x]` fase RED con trazas reales de las tres
    suites · `[x]` cobertura `[OK]` 100 %.
  - `[x]` mutación verificada aparte: `alcance_de_feature("F-061")` da 61
    líneas (41/4/12/4) y `generar_mutantes`, 10, todos en
    `palabras_incidencia.py`. Mismo alcance y mismo número que el informe.
  - `[x]` campaña **no reejecutada**: 259 s según el informe (más de 60 s).
    Vale el recálculo puro más RM1-RM6.
  - `[x]` coste por mutante 259 × 4 / 10 = 104 s ≥ 72 s de base; RM2 sin
    salto de orden de magnitud · `[x]` sin «CAMPAÑA NO VÁLIDA», «Sin
    veredicto» 0 · `[x]` RM1: medida sobre `54ad111`; después solo cambia
    `progress/` · RM3: ninguno de los 10 muertos es equivalente.
  - `N/A` RM5 (nivel `estandar`) · `[x]` RM6: no se quitó ninguna guarda ·
    `N/A` campaña manual (la automática dio 10) · `N/A` análisis de
    supervivientes (hubo 0).
  - `[ ]` **«Evidencias» no da el nº de workers** (4, solo en
    `mutacion_F-061.md`); el checkbox lo pide en el informe del implementer.
- **C4 ter** `N/A`: no existe `harness/rutas_sensibles.json`.
- **C5** `N/A` tasks.md (`sdd: false`); hay commits `F-061 T1..T4` y
  `F-061: …` · `[x]` sin temporales · `[x]` features.json = `in_progress`.

## Cobertura criterio → test

| Criterio | Test |
|---|---|
| 1 api `palabras`/`orden_busqueda` | `test_f061_r1_*` (15) y `test_f030_r6_…` |
| 2 los diez casos, tildes y orden | `test_f061_r2_*` (5); faltan los del cambio 1 |
| 3 nada se pierde; con número, como hoy | `test_f061_r3_…` (>1000) y F-030 R1, R8-R13 |
| 4 recarga tras el sync | `test_f061_r4_*` (3) |
| 5 el front no decide | `test_f061_r5_…` |
| 6 INTEGRACION §5 | revisado a mano |
| 7 sin red ni BBDD; init.sh verde | «Verificación ejecutada» |

## Cambios requeridos

1. `services/dedicacion-front/tests/test_f061_busqueda.py`: añadir dos
   tests:
   - (a) `_buscar(["enfermdad", "vcaciones"])` da `["B"]` y `["V"]`. Mata el
     mutante de `casiEmpieza` en `app.js` (`w.length + 1` → `w.length`).
   - (b) con el catálogo `[{codigo:"CI6", letra:"R", nombre:"Baca",
     orden_busqueda:0}, {codigo:"CI5", letra:"S", nombre:"Llevaca",
     orden_busqueda:1}]`, `"vaca"` da `["S", "R"]`. Mata el mutante
     `return 5` → `return 7`.
   Probados en la copia: pasan hoy y cada uno falla con su mutante.
2. `progress/impl_F-061.md`, «Evidencias», fila de mutación: «4 workers».
3. `progress/impl_F-061.md`: dejar constancia de los mutantes de JS de esta
   review (24: 22 muertos y 2 que matan los tests del cambio 1), para que la
   cobertura real del JS quede escrita.

## Observación no bloqueante

- O1 `palabras_incidencia.py:35`: `entrada.get("palabras") or []` acepta en
  silencio `""`, `0` o `false` como lista vacía; lo demás mal escrito falla.

## Automejora propuesta (no aplicada)

- `CHECKPOINTS.md` C4 bis: si la lógica vive en JS (u otro lenguaje sin
  puerta), una mini-campaña manual documentada (original → mutado,
  resultado). Aquí se midieron 41 líneas de Python y 0 de las ~80 de JS.
  Vale para cualquier proyecto ⇒ `arnes-base`.
