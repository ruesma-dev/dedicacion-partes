<!-- progress/review_F-040.md -->
Revisión completa (pasada 1), `31132a4..431ca39`

# F-040 · Review (reviewer, 2026-10-06)

**Veredicto: CHANGES_REQUESTED.** Un solo cambio, pequeño: un test que el
informe dice que fija el «sin -0» y no lo fija (su mutante sobrevive a la
suite entera de la api). El resto queda dado por bueno para la pasada 2.

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 % y campaña de mutación con supervivientes analizados.

## Lo verificado

- **`bash harness/init.sh`** desde `porcentajes-f040`: `ENTORNO LISTO`. Raíz
  418 passed y 1 skipped; api, front y transfer en verde; `PUERTA COBERTURA`
  100 % (132/132); `PUERTA TAMAÑO` dentro (impl 219/220).
- **Tests anteriores cambiados: ninguno.** `git diff --stat 31132a4..HEAD --
  '*tests*'` solo trae `test_f040_excel.py` (nuevo, +454), y
  `--diff-filter=M` sale vacío. `test_f024_rutas_empresa.py` sin tocar (R20).
- **Cifras (R16).** `grupos_detalle` toma `fila.total` y llama a
  `calcular_estado`/`calcular_desviacion` de `domain/estados.py`; sin épsilon,
  umbral ni fórmulas propios.
- **Combinadas (R10-R11).** `_combinar_con_valor` usa
  `hoja.merged_cells.add(MergedCellRange(...))`, nunca `merge_cells()`. En el
  XML de la muestra, las no ancla `A4` y `H8` llevan valor; 15 `<mergeCell>`
  (A, B, F, G, H de los 3 grupos de varias filas), ninguno en los de una fila.
- **Formato (R1-R6, R12, R13).** Hojas `Detalle` y `Resumen`. Título en la
  fila 1 y cabecera en la 2, sin «Obra(código)». Autofiltro `A2:H12` y
  `A2:E7`, paneles en `A3`, horizontal, `fitToWidth` 1 y `fitToHeight` 0,
  títulos `$1:$2`. Bandas `FFFFFF`/`DDEBF7` y línea `medium` negra bajo cada
  grupo. Resumen sin bandas ni combinadas.
- **Resumen (R14) y convenio (R8, D6).** «VAR-29 Varios partida 29 = 80% +
  Postv-0702 Hotel Inventado = 30%»: prefijo de `export.prefijo_postventa` en
  Código y Obra, nombre sin prefijo en el Resumen, `VAR-29` como obra normal.
- **Notación científica (R18).** No queda ningún `normalize()` en `excel/`.
  `texto_pct` usa formato fijo, y no sale ningún «E+» en la muestra.
- **Muestra.** Abierta `%TEMP%\f040\f040_muestra.xlsx` con openpyxl y por XML,
  y regenerada en mi scratchpad con el comando del informe §6: el zip, salvo
  `docProps`, sale **byte a byte igual**.
- **Docs (R21).** Solo la línea de `excel/` en `ARCHITECTURE.md` y la fila de
  `export.xlsx` del README de la api. `azure-apps/dedicacion.md` no menciona
  el Excel; árbol limpio, último commit el de F-039 (`f01156f`).
- **Rastro.** `grep -n "Ninguna feature" progress/current.md`: vacío (exit 1).
  La M1 está en `current.md` con arranque, `curl.exe`, apertura y los 7
  puntos; `AAAA/MM` es el periodo con carga que elige el humano.

## Mutación (RM1-RM6)

- **Recalculado** con `harness.alcance` y `generar_mutantes` en HEAD:
  2 ficheros, **250 líneas, 77 mutantes**, igual que el informe. Con
  `random.Random(20260820).sample(…, 20)` salen 20 mutantes concretos; he
  repasado los 20 y ninguno es equivalente (RM3 ok).
- **Campaña no reejecutada:** 439,9 s según el informe (> 60 s); vale el
  recálculo puro más RM1-RM6 y RM4.
- **RM1.** Medida en `2b14802`; hasta HEAD el alcance solo cambia el orden de
  un import de `exporter.py` (ruff), sin líneas mutadas. Vale.
- **RM2.** 20 × 22,0 = 440 ≈ 439,9 s con 1 worker; media 22,0 y base 20,8.
- **RM4: reproducidos a mano** en una copia de la api en mi scratchpad:

  | Mutante | Resultado |
  |---|---|
  | `range(1, 9)` → `range(1, 10)` (exporter 96) | MUERTO: 3 fallos (r5, r6, r9) |
  | `range(desde, hasta + 1)` → `hasta - 1` (exporter 141) | MUERTO: 1 fallo (r11) |
  | `lineas or [...]` → `lineas and [...]` (contenido 83) | MUERTO: 14 fallos |

- **Superviviente fuera de la muestra** (motivo del cambio 1): el aritmético
  de `exporter.py:149`, `float(valor) / 100 + 0.0` → `float(valor) / 100 - 0.0`,
  es uno de los 77 generados. Aplicado en la copia, la **suite entera de la api
  pasa: 619 passed**. Con el mutante, el XML de `G3` para 99,996 es
  `<v>-0</v>`, y sin él es `<v>0</v>`.

## Checkpoints

- **C1** [x] `init.sh` con exit 0 · [x] están los ficheros base.
- **C2** [x] una `in_progress` · [x] rama de F-040 · [x] `current.md`
  coherente con el paralelo decidido por el humano · [x] `done` en `history.md`.
- **C3** [x] Hexagonal: `contenido.py` y `exporter.py` en `infrastructure/`,
  y el dominio sin tocar · [x] primera línea con la ruta · [x] sin prints, sin
  secretos y sin dependencias nuevas · [x] trampas: la escala 0-100 → fracción
  solo en la celda, y la postventa con su prefijo y sin mezclarse; sin Sigrid.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4**
  - [ ] **Trazabilidad: R16 cubierto a medias.** «Desviación 0» se comprueba
    con `det["G3"].value == 0`, que también aceptan -0.0 y el `<v>-0</v>` (al
    leer, openpyxl lo convierte en `int` 0). Ver el cambio 1.
  - [x] Sin red ni BBDD · [x] la M1 en `current.md` con su comando.
- **C4 bis**
  - [x] Rigor declarado · [x] RED real (T1 y T3) · [x] cobertura OK.
  - [x] Informe de la herramienta, totales recalculados · [x] > 60 s, no
    reejecutada (dicho) · [x] coste 22 s/mutante · [x] sin base rota.
  - [x] RM1 · [x] RM2 · N/A RM5 (estándar) · N/A RM6 (sin guardas quitadas)
    · N/A campaña manual (hubo automática) · [x] sin supervivientes en la
    muestra, nada pendiente.
  - [ ] **«Evidencias»**: los números están, pero §2.3 afirma que
    `test_f040_r16_99996_…` «lo fija», y no es verdad (cambio 1).
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5**
  - [x] T1-T5 y T7 `[x]`, con su commit `F-040 Tn:`. T6 es la MANUAL M1 del
    humano y está listada en `current.md`, igual que en F-039.
  - [x] Sin temporales (`coverage.json`, `.coverage`: ignorados) · [x]
    `features.json` en `in_progress`, que es lo real.

## Cobertura requisito → test (`services/dedicacion-api/tests/test_f040_excel.py`)

| R | Test(s) `test_f040_…` |
|---|---|
| R1-R2 | `r1_dos_hojas_detalle_y_resumen`, `r2_titulo_en_fila_1_cabecera_en_2_datos_desde_3` |
| R3-R6 | `r3_autofiltro_y_paneles`, `r4_impresion_y_anchos`, `r5_cabecera_azul_…`, `r6_cabecera_del_detalle_sin_obra_codigo` |
| R7-R9 | `r7_conserva_el_orden…`, `r8_postventa…`, `r8_categoria_nula…`, `r9_…` (×2), `r7_r8_filas_del_detalle…` |
| R10-R13 | `r10_valor_en_todas…`, `r11_combinadas…`, `r12_bandas…`, `r13_resumen…` |
| R14-R15 | `r14_obras_con_codigo_nombre_y_mas`, `r15_…`, `r14_r15_obras_total_y_estado…` |
| R16 | `r16_las_cifras…`, `r16_sin_formulas`, `r16_99996…` (débil en el «-0», cambio 1) |
| R17-R19 | `r17_es_entero…`, `r17_fraccion…`, `r18_texto_pct…` (×7), `r18_ningun_texto…`, `r19_textos_de_estado` |
| R20 / R21 / M1 | `test_f024_rutas_empresa.py` sin tocar y en verde / diff de docs / MANUAL pendiente |

## Cambios requeridos

1. **`services/dedicacion-api/tests/test_f040_excel.py:425`**
   (`test_f040_r16_99996_sale_ok_y_desviacion_cero_en_el_libro`): además del
   valor leído con openpyxl, comprueba el XML con el helper que ya existe,
   `_xml_hoja(contenido, 1)[0]["G3"]["v"] == "0"`. El `+ 0.0` de
   `exporter.py:149` queda así vigilado. Para demostrarlo, aplica en una copia
   el mutante `/ 100 + 0.0` → `/ 100 - 0.0`, comprueba que el test cae y pega la
   traza en `progress/impl_F-040.md` §2.3, que hoy dice «lo fija» sin serlo.
   Ese informe está a 219/220: resume para hacer sitio. Como el cambio no toca
   ningún fichero de producción, no hay que repetir la campaña de mutación.

## Observaciones (no bloquean; recoger en `current.md` o descartar por escrito)

- `test_f040_excel.py:53`: `obra_ide` usa `hash((cod, …))`, que cambia por
  proceso. Nada depende de él, pero un literal lo haría determinista.
- M1: openpyxl enseña vacías las combinadas al releer (design §5); el XML sí
  las tiene. Que el humano mire la muestra en Excel.

## Automejora (propuesta, no aplicada)

- `reviewer.md` / C4 bis: con campaña muestreada, aplicar además **un mutante
  no muestreado** a la línea que el informe dice que «fija un test» (así salió
  este caso).
