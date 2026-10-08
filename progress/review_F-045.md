<!-- progress/review_F-045.md -->
Revisión completa (pasada 1), `dev...6959c91`

# F-045 · Review

**Veredicto: CHANGES_REQUESTED** (CAMBIOS PEDIDOS). El código, los tests y la
campaña están bien y se aprobarían tal cual; lo único que falla es el rastro:
la MANUAL T6 de `progress/current.md` apunta a un mes que **no tiene postventa**
en la base local, así que no se puede seguir (C4, tercer punto). Arreglo de una
línea; la pasada 2 será incremental sobre `6959c91`.

**Rigor:** `estandar` (declarado): fase RED, cobertura ≥ 80 % y mutación.

## Lo comprobado

- `bash harness/init.sh` (tal cual, solo): **ENTORNO LISTO**, raíz 418 passed
  / 1 skipped, cobertura 100 % (30/30), tamaño OK. La api salió de caché: la
  ejecuté aparte, **717 passed** en 10.1 s.
- **Solo la api** (design §2): producción en `infrastructure/excel/contenido.py`
  y `exporter.py`; diff vacío en `domain/`, `application/`,
  `interface_adapters/`, `config/`, `requirements.txt`, front y transfer; docs
  solo en las dos líneas de R19.
- **Lista cerrada de design §7.** `git diff dev...HEAD` de `test_f040_excel.py`
  y `test_f039_registro_var.py` cambia exactamente 12 tests: f040 r1, r2, r3,
  r4, r6, r7_r8, r9, r11, r13, r16_99996, r17 y f039 r21, más el docstring.
  Solo nombre/índice de hoja y C10/D10 de GAMMA. **Ninguna aserción relajada**:
  r4 queda más estricto (comprueba también Postventa); `max_row == 12`, los
  `_GRUPOS` y los valores de r10/r12/r14_r15 siguen idénticos.
- **R11-R12.** `_grupo` calcula total, desviación y estado sobre
  `fila.lineas` completas (GAMMA sale OK en Obras, no SIN CARGA); la agregada
  suma en `Decimal` desde `Decimal(0)` (30.3 y 69.70 exactos). Tests abajo.
- **Trampas de C3.** La agregada va en 0-100 y `_celda_pct` la pasa a
  fracción (r16: 0.15, 0.85, 0.303). Solo presentación: ninguna escritura.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base. **C2** [x] una `in_progress`
  · [x] rama `feature/F-045-…` · [x] `current.md` centrado en F-045 (mismo
  formato aceptado antes) · [x] F-045 no cierra nada.
- **C3** [x] hexagonal (`contenido.py` solo importa `domain`) · [x] ruta en
  primera línea · [x] sin `print`, secretos ni dependencias nuevas · [x] trampas.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1-R18 con test trazable `test_f045_rN_*` (tabla abajo) y en
  verde; R19 es documental y se verifica por el diff · [x] sin red ni BBDD ·
  **[ ] MANUAL con comando exacto: el comando apunta a `2026/09`, que en la
  base local no tiene ninguna línea de postventa** (ver Cambios 1).
- **C4 bis**
  - [x] `rigor: estandar` declarado.
  - [x] Fase RED: trazas reales de T1 (`ImportError … AGREGADA_EN_OBRAS`) y T3
    (26 failed = 14 nuevos + 12 de la lista cerrada), en impl §4.
  - [x] Cobertura `[OK]` 100 % (30/30).
  - [x] Mutación verificada de forma independiente: `alcance_de_feature` da
    99 líneas (70 + 29) y `generar_mutantes` 14 (8 + 6), igual que el informe.
  - [x] Muertos comprobados. Tiempo total 160.9 s (> 60 s): bastaría el
    recálculo, pero dado el aviso de impl §5 **reejecuté la campaña entera**
    (`--workers 1`, salida en el scratchpad): **14 evaluados, 14 muertos,
    0 supervivientes, 0 timeouts, en 147.5 s**, mutante a mutante iguales.
    `git status` limpio después.
  - [x] Coste por mutante 160.9 × 1 ÷ 14 = 11.5 s · [x] sin «⚠ CAMPAÑA NO
    VÁLIDA», «Sin veredicto» 0, línea base en verde.
  - [x] RM1: SHA medido `77e124b`; `git diff 77e124b..HEAD` solo toca
    `progress/` y `tasks.md`: el alcance medido es el revisado.
  - [x] RM2: base 12.1 s, media 11.5 s, 14 × 11.5 ≈ 161 s = total. Coherente.
  - [x] RM3: los 14 mutantes cambian comportamiento observable (revisados uno
    a uno: default `agregada=True`, `==`/`!=` de la partición, `Decimal(1)`,
    `agregada=False`, `or`→`and` en categoría y líneas, `is not SIN_CARGA`,
    `italic=False`, `postventa` invertido en las dos hojas y las tres
    columnas de la cursiva). Ningún equivalente muerto.
  - N/A RM5: rigor `estandar` y sin equivalentes · [x] RM6: no se quitó
    defensa (`or ""`, `or [_LINEA_VACIA]` siguen) · N/A campaña manual (la
    automática generó 14) · [x] sin supervivientes · [x] «Evidencias»
    completas, con `--workers 1` · [x] ningún N/A sin motivo.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1-T5 y T7 `[x]` con su commit `F-045 Tn:`; T6 es MANUAL
  (humano), pendiente por diseño y listada en `current.md` · [x] árbol limpio
  · [x] `features.json` en `in_progress`, coherente.

## Valoración del superviviente que no se reproduce (impl §5)

**La campaña definitiva es fiable; no hay que repetirla.** Tres razones:

1. **Tres ejecuciones, dos limpias e iguales.** La mía (con
   `contenido.cpython-312.pyc` presente en `__pycache__`, es decir, la misma
   condición que el implementer culpa de la primera) da 14/14 muertos, igual
   que la definitiva. El mutante `contenido.py:98 agregada=True→False` lo
   matan r7, r9, r15 y r18 (reproducido también a mano por el implementer).
2. **El fallo va en la dirección segura.** Con `PYTHONDONTWRITEBYTECODE=1` la
   campaña no escribe `.pyc` mutados; el único bytecode que puede colarse es
   el del código original, que pasa la suite. Un `.pyc` viejo solo fabrica
   **supervivientes falsos**, nunca **muertos falsos**: un 0 de supervivientes
   no se infla por esa vía.
3. **La hipótesis del `.pyc` no explica el caso tal cual.** Ese mutante añade
   un byte (5784 → 5785) y CPython invalida el `.pyc` por tamaño, así que el
   `.pyc` previo no debería cargarse. Sea cual sea la causa (bloqueo de
   ficheros en Windows, un proceso o IDE que reescribe el fichero durante la
   campaña…), es un defecto de la herramienta y está bien que esté en el
   encargo de `arnes-base` (`5370838`). Conviene añadir allí este dato del
   tamaño y que con el `.pyc` presente no se reproduce.

## Cobertura requisito → test (`test_f045_*` salvo indicación)

R1 `r1_tres_hojas…` (+ f040 r1) · R2 `r2_titulos…` · R3 `r3_cabecera_autofiltro…`
×2 · R4 `r4_mismos_trabajadores…`, `r4_r10_filas…` ×2 · R5 `r5_obras_lleva…`,
`r5_d5_var_en_obras…` · R6 `r6_postventa_lleva…` · R7 `r7_agregada_unica…`,
`r7_suma_exacta_en_decimal` · R8 `r8_sin_la_otra_parte…` · R9 `r9_solo_la_otra…`
· R10 `r10_sin_carga…`, `r4_r10_…` · R11 `r11_total_desviacion…` (contenido) y
`r11_…_iguales_en_las_tres_hojas` (libro) · R12 `r12_la_columna_pct…`,
`r12_la_suma_coincide…`, `r12_…_en_el_libro` · R13 `r13_valor_en_todas…` · R14
`r14_bandas_por_hoja…` · R15 `r15_cursiva_solo…` · R16 `r16_pct_de_la_agregada…`
· R17 `r17_resumen_igual…` (+ f040 r13, r14_r15) · R18 `r18_el_prefijo…` ×2 y
F-024 en verde sin tocar · R19 documental, por el diff (`ARCHITECTURE.md:79`,
`services/dedicacion-api/README.md:41`).

## Cambios requeridos

1. **`progress/current.md`, MANUAL paso 2: cambiar `periodos/2026/09` por
   `periodos/2026/10`.** Consulta de solo lectura a la base local (la que usa
   la api local del paso 1): `2026/09` tiene 2 líneas y **0 de postventa**
   (un solo trabajador, dos obras); `2026/10` tiene 12 líneas y 1 de
   postventa, de un trabajador de la empresa 1 (`ide 1140584`) que además
   tiene una obra. Con `2026/09` no hay agregadas, y los pasos 4, 5 y 7 no se
   pueden hacer. design §6 ya decía `2026/10`.
2. **`progress/current.md`, resumen de la spec: «en cursiva, solo si no es
   0»** no es lo que dice D4/R8. La agregada sale cuando el trabajador tiene
   **alguna línea de la otra parte**, valga lo que valga; no depende de que la
   suma sea 0. Dejarlo como «solo si tiene líneas de la otra parte».

El resto de la MANUAL casa con el código: puerto 8090 (`settings.py:34`),
ruta `/api/v1/periodos/{anio}/{mes}/export.xlsx` (`routes.py:53,281`) y
`x-usuario` cae a «local» (`deps.py:131`): el `curl.exe` anónimo funciona.

Observación (no bloquea): `test_f040_r1_dos_hojas_detalle_y_resumen` ya no
describe lo que comprueba; se conservó adrede por trazabilidad (impl §3).

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4, tercer punto: «… con su comando exacto **y apuntando a
  datos que existen y permiten ver lo verificado**». Un comando exacto contra
  un mes vacío cumple la letra y no verifica nada. Candidato a `arnes-base`.
