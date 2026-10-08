<!-- progress/review_F-045.md -->
Revisión incremental desde a041301 (pasada 3) · la 1 fue completa (`dev...6959c91`), la 2 incremental desde 6959c91

# F-045 · Review

**Veredicto vigente: CHANGES_REQUESTED** (pasada 3, abajo). Código, tests,
Detalle y campaña, bien; falla solo el rastro de la spec (D10 sigue «abierta»
en `design.md`).

## Pasadas 1 y 2 (resumidas por el tope)

- **Pasada 1 · CHANGES_REQUESTED**, solo por `current.md`: la MANUAL apuntaba a
  `2026/09`, sin postventa en la base local, y D4 decía «solo si no es 0».
  Comprobado entonces: solo la api (`infrastructure/excel/`), lista cerrada de
  12 tests sin aserciones relajadas, R11-R12 con `Decimal`, trampas de C3,
  RED de T1 y T3, cobertura 100 % (30/30) y campaña reejecutada por mí:
  14/14 muertos (`77e124b`).
- **Pasada 2 · APPROVED**: los dos cambios resueltos; MANUAL seguida contra la
  base local en solo lectura (octubre, ALVAREZ SEGUIDO 50 % + 50 %).
- Encargos de automejora llevados a `arnes-base` (`5370838`, `d413189`).

## Pasada 3 · Revisión incremental desde a041301

Delta: `77d9496`..`f6a92e0` (spec reescrita y aprobada, T8-T11, `current.md`).
**Nivel de rigor: `estandar`** (declarado): fase RED, cobertura ≥ 80 % y
mutación con supervivientes analizados.

### Lo comprobado

- `bash harness/init.sh` (tal cual, solo): **ENTORNO LISTO**, raíz 418 passed /
  1 skipped, api/front/transfer en verde, cobertura 100 % (33/33), tamaño OK.
- **Detalle = F-040, comprobado contra `dev`.** Extraje la api de `dev` y de
  HEAD a mi scratchpad y pinté el mismo cuadrante (los 5 de la muestra + un
  6.º con 33,33 / 66,67 %) con los dos exportadores: la hoja «Detalle» de `dev`
  (hoja 1) y la de HEAD (hoja 3) son **idénticas** en las 120 celdas (valor,
  formato numérico, fuente, relleno, bordes, alineación), combinadas,
  autofiltro, paneles, anchos, impresión y `max_row`; con el periodo vacío,
  hasta el XML es byte a byte igual. `_hoja_grupos` con `grupos_detalle` es el
  `_hoja_detalle` de `dev` con el nombre y el título como parámetros.
- **Lista cerrada de design §7.** `git diff dev..HEAD` de `test_f040_excel.py`
  y `test_f039_registro_var.py`, y `a041301..HEAD` de `test_f045_…`: cambian
  exactamente los de §7.1 (6), §7.2 (13 adaptados + 4 borrados) y §7.3 (1).
  Solo salen aserciones que leían la hoja Resumen o `filas_resumen`. Ninguna
  relajada: f040 r2 aplica el formato a las tres hojas; f045 r11 compara además
  la columna G; r13 y r17 comprueban combinadas, bandas y línea gruesa del
  Detalle; f039 r21 añade la comprobación de VAR en Obras (D5).
- **Sin rastro del Resumen.** `grep` de `filas_resumen`, `FilaResumen`,
  `_hoja_resumen` y `_RESUMEN` en `services/`: nada. «Resumen» solo queda en
  frases que dicen que no existe y en el nombre conservado adrede de
  `test_f040_r1_dos_hojas_detalle_y_resumen` (design §7). `ARCHITECTURE.md:79`
  y `services/dedicacion-api/README.md:41` describen Obras, Postventa y Detalle
  (R19). Los demás «resumen» son el `ResumenPeriodo` del cuadrante, ajeno.
- **D10 = A**: `LineaDetalle.nombre` se conserva, comentario ajustado. Ruff de
  los ficheros tocados, limpio desde la raíz.
- **MANUAL de `current.md`, seguida en solo lectura** (`build_app` en proceso,
  sin el DDL de `main.py`; xlsx en mi scratchpad): `GET …/2026/10/export.xlsx?
  empresa=1` → 200, `dedicacion_202610_emp1.xlsx`, hojas Obras, Postventa y
  Detalle (paso 3). Obras: 1 agregada (ALVAREZ SEGUIDO, 50 %), 3 cursivas.
  Postventa: `Postv-0626` 50 % + 8 «OBRAS / RESTO OBRAS», 24 cursivas. Detalle:
  título «DETALLE DE DEDICACIÓN · Octubre 2026», `Postv-0626` intercalada,
  0 cursivas, ningún «RESTO» (paso 8). Estados: OK y SIN CARGA (paso 6).
  Puerto 8090 (`settings.py:34`). Ver Cambios 2 sobre el recuento.

### Mutación (C4 bis)

- **Recálculo independiente**: `alcance_de_feature("F-045")` → 100 líneas
  (`contenido.py` 68, `exporter.py` 32); `generar_mutantes` → 14 (8 + 6),
  igual que el informe. Son los mismos 14 de la pasada 1.
- **Campaña no reejecutada: 745,7 s según el informe** (> 60 s). Basta el
  recálculo más RM1-RM6, y además hice **RM4** sobre la copia de HEAD del
  scratchpad: `for col in (3, 4, 6)` lo mata r15 (1 failed) y `Decimal(1)` en
  la agregada lo matan 12 tests. Base de esa copia, 67 passed. Árbol limpio.
- Coste por mutante 745,7 × 1 ÷ 14 = 53,3 s (> 1 s) · sin «⚠ CAMPAÑA NO VÁLIDA»
  · «Sin veredicto» 0 · sin supervivientes.
- **RM1**: SHA medido `9d2e361…` (T10). `git diff 9d2e361..HEAD` solo toca
  `progress/` y `tasks.md`: el alcance medido es el revisado.
- **RM2**: base 62,8 s, media 53,3 s, 1 worker; 14 × 53,3 = 746 s = total.
  Coherente. La base sube desde los 12,1 s de la pasada 1 («máquina cargada»,
  impl §8); timeouts distintos (126 s), no se comparan entre campañas.
- **RM3**: los 14 cambian comportamiento observable (revisados en la pasada 1;
  las líneas de Detalle en `exportar` son llamada y literal, sin mutante).
- **RM5** N/A: rigor `estandar` y sin equivalentes · **RM6** [x]: no se quitó
  defensa (`or ""`, `or [_LINEA_VACIA]` siguen).

### Checkpoints (pasada 3)

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama `feature/F-045-…` · [x] `current.md`
  centrado en F-045 (formato ya aceptado) · [x] F-045 no cierra nada.
- **C3** [x] hexagonal (`contenido.py` solo importa `domain`) · [x] ruta en
  primera línea · [x] sin `print`, secretos ni dependencias nuevas · [x]
  trampas: escala solo en `_celda_pct` (sin cambio), postventa por
  `es_postventa`, ninguna escritura.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1-R18 con test trazable y en verde (tabla abajo); R19 por el
  diff · [x] sin red ni BBDD · [x] MANUAL con comando exacto, que funciona.
- **C4 bis** [x] rigor declarado · [x] RED real de T8 (19 failed, impl §8) ·
  [x] cobertura `[OK]` 100 % · [x] mutación verificada (arriba) · [x]
  «Evidencias» con los cuatro números y `--workers 1` · [x] ningún N/A sin
  motivo.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1-T5, T7-T11 `[x]` con commit `F-045 Tn:`; T6 MANUAL pendiente
  por diseño · [x] árbol limpio · **[ ] la spec no refleja el estado real:
  `design.md` sigue declarando D10 ABIERTA** (Cambios 1).

### Cobertura requisito → test (`test_f045_*` salvo indicación)

R1 `r1_tres_hojas_obras_postventa_y_detalle` (+ f040 r1) · R2 `r2_titulos…`
(+ f040 r2) · R3 `r3_cabecera_autofiltro…` ×2 · R4 `r4_mismos_trabajadores…`,
`r4_r10_filas…` ×2 · R5 `r5_obras_lleva…`, `r5_d5_var_en_obras…` (+ f039 r21)
· R6 `r6_postventa_lleva…` · R7 `r7_agregada_unica…`, `r7_suma_exacta…` · R8
`r8_sin_la_otra_parte…` · R9 `r9_solo_la_otra…` · R10 `r10_sin_carga…` · R11
`r11_total_desviacion…` y `r11_…_iguales_en_las_tres_hojas` · R12 `r12_…` ×4
· R13 `r13_valor_en_todas…` · R14 `r14_bandas_por_hoja…` · R15
`r15_cursiva_solo…` · R16 `r16_pct_de_la_agregada…` · R17
`r17_detalle_igual_que_en_f040` + f040 r2-r12, r16-r19 sobre la hoja 3 · R18
`r18_el_prefijo…` ×2 y F-024 sin tocar · R19 documental, por el diff.

### Cambios requeridos (pasada 3)

1. `specs/F-045-excel-obras-postventa/design.md:4`: «D10 está **abierta**
   (§8)» → D10 decidida por el humano el 2026-10-08: A. Y `design.md:220`:
   «**D10 (ABIERTA)**» → «**D10 (DECIDIDA: A)**», como ya dicen
   `requirements.md:24,68`, `features.json` e impl §8. La aprobación
   (`6d48597`) solo tocó `requirements.md`; el diseño contradice a la spec.
2. `progress/current.md:37`: «12 líneas, 1 de postventa» es el recuento de la
   base (periodo 13), pero el Excel de la empresa 1 enseña **11 líneas de 8
   trabajadores**: la de MONTAÑO MECHAN (`0000`, 100 %) no está en el
   cuadrante de la empresa 1. Que lo diga, para que el humano no busque una
   línea que no va a salir.

Ni código ni tests: la pasada 4 puede limitarse a ese diff, más init.sh.

**Automejora (propuesta, no aplicada):** en `CHECKPOINTS.md` C5, un punto
«ninguna decisión `Dn` que conste como decidida en `requirements.md` figura
como abierta en `design.md` o `tasks.md` (grep `ABIERTA`/`abierta` en la
carpeta de la spec)». Cerrar una Dn en un fichero y no en los demás es fácil
de repetir; vale para cualquier proyecto (`arnes-base`).
