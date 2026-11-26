<!-- progress/review_F-081.md -->
Revisión completa (pasada 1)

# F-081 · Review principal (`estandar`; la mutación, informativa, la mide después la pasada de campaña)

**Veredicto: APPROVED** sobre HEAD `0a73b99` (diff `dev...HEAD`, merge-base `ab303d5`). La mutación de C4 bis queda
«pendiente: pasada de campaña». No hace falta pasada de evidencias: e2e N/A y mutación informativa.

## Nivel de rigor

`estandar`, declarado en `features.json` y justificado en design (cabecera y D8, OK del humano el 2026-11-26). Exige
fase RED y cobertura de lo cambiado; mutación y e2e, informativas. `harness/rigor.local.json` no existe ni se toca.
Comparto D8: el evaluador traduce lo tecleado al número que se habría tecleado a mano y la api valida como siempre.

## Lo verificado por mí (no copiado del informe)

- **`ARNES_SIN_CACHE=1 bash harness/init.sh`**, sin pipes: raíz `2319 passed, 47 skipped` (978 s), api `1713`, front
  `708`, transfer `2021`, todas sin caché. `COBERTURA` N/A con motivo, `CARRIL` y `CAPA E2E` N/A. Su única `[KO]` fue
  `TAMAÑO` por **este informe** (borrador de 163 líneas escrito mientras corría); recortado, `bash harness/init.sh`
  repetido: resultado al pie.
- **Alcance:** solo `app.js`, `styles.css`, el test nuevo, dos listas de tests existentes, `ARCHITECTURE.md` y papeleo.
  **Api y transfer sin tocar** (diff vacío). `azure-apps`, nada (design §10).
- **Ninguna aserción existente cambió:** el diff de `test_f030_celda_pct.py` y `test_f069_importes_front.py` solo añade
  los cinco nombres a `FUNCIONES_HOY`, `GUARDAR_CHIP` y dos tuplas de `_editor`. `f025`, `f029`, `f030_tabla`, `f041`,
  `f042` y `f061` no aparecen en el diff.
- **R5:** evaluador leído entero. Regex fija y descenso recursivo sobre fichas, sin `eval`, `Function` ni temporizador
  con cadena. `toast` pinta con `textContent` (l. 273): un HTML pegado en la cantidad no se interpreta.
- **Fuzz propio** (scratchpad): 3.000 expresiones aleatorias de ≤ 100 caracteres contra un analizador de referencia en
  Python con `Fraction` dan **0 discrepancias**, división por cero incluida. `redondear2` contra `Decimal`
  ROUND_HALF_UP (3.436 valores) da 3 discrepancias de ruido binario (O2).
- **Los tests vigilan el comportamiento**, comprobado con rupturas en una copia `git archive` de HEAD, nunca en el
  árbol. Sin `if (operacion) return;` (%) y sin `if (!operacion)` (cantidad) caen los 5 de R7/R12. Sin el
  `stopImmediatePropagation` cae `r9_linea_sin_pct…`. Con el 0 dentro del rango caen 2 de R9. Sin reponer la cantidad
  cae R14.

## Las dos desviaciones del implementer

1. **R4 sobre el texto crudo: correcta.** R4, aprobado, dice «pasa de 100 caracteres … sin recorrer la expresión
   entera», y quitar antes los espacios ya obliga a recorrerla. Design §5 es el cómo y cede ante el qué. Solo cambia
   algo con más de 100 caracteres reales en la celda, y el corte queda en tiempo constante (test de 5 M × 1.000 < 1 s).
2. **Línea a 0 y operación fallida ⇒ celda vacía, sin «en blanco rellena»: correcta.** R9 y R10 piden «sin guardado» y
   el relleno de F-030 R1 guarda. La frase de design §5 describía el caso normal. El `stopImmediatePropagation` solo
   actúa con la celda repuesta a vacío, y no hay otra escucha `blur` detrás (l. 2161, 2192, 2212): no corta nada más.
   Salir otra vez en blanco rellena como siempre.

Las dos siguen la letra de lo aprobado. Basta con que el humano las lea en el resumen final.

## Checkpoints

**C1** [x] `init.sh` sin caché: suites en verde; la `[KO]` de tamaño era mía y está corregida (al pie). [x] Ficheros base.

**C2** [x] Una sola activa (F-081, `in_review`). [x] Orden: `todo` prioridad 1, sin `blocked` ni `human_review`.
[x] Rama `feature/F-081-operaciones-en-celdas`. [x] `current.md` l. 4 describe la sesión activa. [x] `features.json`
coherente (`spec_aprobada: 2026-11-26`).

**C3** [x] Solo el front, que sigue siendo «captura, nada más»: la operación es una forma de teclear y la api valida
(design §1). [x] Primera línea con la ruta en el test nuevo; `app.js` y `styles.css` la conservan. [x] Sin
`console.log`, `debugger`, TODO, secretos ni dependencias (D6). [x] Trampas: **escala**, sin conversión nueva (el %
viaja 0-100, `cuerpoLineas` sin tocar); **postventa**, nada; **escritura**, ninguna nueva.

**C3 bis:** N/A, no se toca `docs/referencia/`. **C3 ter** [x] Las citas del humano llevan fecha y origen
(requirements, design §12) y van separadas de las recomendaciones. **C3 quater:** N/A, la spec dice «No» a cruzar la
frontera (design §10).

**C4** [x] Cada requisito tiene test y pasa (tabla; R20, ver nota). [x] Sin red ni BBDD: `node` sobre el `app.js` real,
más dos lecturas de fichero (R5, R22). [x] M1 (T11) en «⚠» de `current.md`, con pasos, arranque y destino
`progress/manual_F-081.md`. [x] Dobles: ninguno de clases Python; los de JS (`toast`, `programarGuardado`, `$`) tienen la
firma de `app.js`.

**C4 bis**
- [x] Nivel declarado. [x] **Fase RED:** trazas reales de T1, T4 y T6 (65, 12 y 7 fallos, con aserciones de
  comportamiento) y mis rupturas en copia. T3, T8 y T9 fijan lo de hoy o leen texto, como prevé tasks.md.
- [x] **Cobertura:** N/A con el motivo impreso («no cambia líneas Python de producción»). El cambio es JS, que el arnés
  no mide. Lo suplen un test por rama nueva y las rupturas.
- **Pendiente: pasada de campaña:** totales de mutación y su fila de «Evidencias». Se espera N/A: `harness.mutacion`
  muta Python y no hay Python en el diff, así que la prueba de control del cero no tiene ficheros. RM1-RM7: N/A por
  nivel. RM7 tampoco aplica: ningún requisito protege un orden entre colaboradores.
- [x] «Evidencias»: tests 94/708/2319, cobertura N/A con motivo, tiempo de suite y fila e2e.
  Capa e2e: N/A (`CAPA E2E: N/A`). [x] Ningún N/A sin motivo.

**C4 ter:** N/A, no existe `harness/rutas_sensibles.json`.

**C5** [x] T1-T10 y T12 en `[x]`, con commit `F-081 Tn:` cada una. T11 es la M1 del humano y está en «⚠».
[x] Sin temporales. [x] `features.json` en `in_review`.

## Trazabilidad requisito → test (prefijo `test_f081_`)

| R | Test(s) |
|---|---|
| R1 | `r1_evalua_con_precedencia_y_asociatividad` ×14, `r1_tercio_sin_redondear` |
| R2 | `r2_mal_formada_es_no_valida_sin_lanzar` ×23, `r2_no_texto_tampoco_lanza` |
| R3 | `r3_division_por_cero` (5 casos), `r3_resultado_no_finito_es_no_valida` |
| R4 | `r4_mas_de_100_caracteres_o_21_parentesis`, `r4_lo_largo_no_se_recorre_entero` |
| R5 | `r5_app_js_no_evalua_texto_como_codigo` |
| R6 | `r6_es_expresion` ×18, `r6_no_texto_no_es_expresion` |
| R7 | `r7_mientras_hay_expresion…`, `r7_solo_expresion…`, `r7_volver_a_un_numero…` |
| R8 | `r8_al_salir_pone_el_resultado…`, `r8_el_cien_entra…` |
| R9 | `r9_r10_confirmar_expresion…`, `r9_el_aviso_de_rango…`, `r9_fuera_de_rango…`, `r9_linea_sin_pct…` |
| R10 | `r10_no_valida_avisa_repone_y_no_guarda`, `r10_demasiado_larga` |
| R11 | `r11_enter_confirma_y_va_al_buscador_de_obra` |
| R12 | `r12_mientras_hay_expresion…`, `r12_la_marca_de_copiado…` |
| R13 | `r13_al_salir…`, `r13_enter_confirma_sin_mover_el_foco…`, `r13_redondeo_y_negativo…` |
| R14 | `r14_no_valida_avisa_repone_lo_ultimo_valido_y_no_guarda` |
| R15 | `r15_redondea_a_dos_mitad_arriba_en_decimal`, `r15_text_numero_con_coma` |
| R16 | `r16_*` ×3 y las suites de F-030 y F-069 sin cambiar aserciones |
| R17 | `r17_con_letras_busca_incidencia…`, `r17_con_operadores_y_letras…` |
| R18, R19 | `r18_los_dias_de_incidencia…`; `r19_con_el_editor_abierto…`, `r19_pegar_sigue_el_camino…` |
| R20 | aserciones `# R20` sobre `cuerpoLineas`/`cuerpoImportes` reales en `r7_mientras…`, `r8_al_salir…`, `r12_*`, `r13_*` |
| R21, R22 | `r21_*` ×2 (% y cantidad); `r22_architecture_lo_explica…` |

**Nota sobre R20: no es un checkbox vacío.** Es el único sin `test_f081_r20_*`. Seis tests afirman, sobre el cuerpo
real del `PUT`, que viaja el número (30, 33,33, 12, 240) y nunca el texto, con la operación a medias y confirmada; y
tasks.md, aprobado, asignó R20 a esos tests (T4, T6). Mismo criterio que la review de F-003 con su R15.

## Cambios requeridos

Ninguno.

## Observaciones (informativas; ninguna pide trabajo antes del cierre)

- **O1 · Para M1 y el resumen al humano.** Sin `=` delante, el prefijo ya se guardó: `50+60` sobre 33,33 pasa por `5` y
  `50`, que son llanos y se guardan como hoy (R16). Al fallar el rango, la celda vuelve a **50** («lo último válido»,
  D4). El paso 2 de M1 usa `=50+60`, que vuelve a 33,33: está bien escrito, pero conviene que el humano sepa la diferencia.
- **O2 · `redondear2` y el ruido binario.** `1.4749999999999999` (de `1,47+0,005`) da 1,48, no 1,47: es lo que espera el
  usuario. Cumple todos los ejemplos de R15.
- **O3 · El aviso de «no válida» cita el texto entero.** Un pegado enorme sale entero en el toast (con `textContent`,
  sin riesgo). Cosmético.
- **O4 · Cantidades ≥ 1e15.** `99999999999*99999999999` sale `9,99…e+21`, que al salir parece otra operación y da un
  segundo aviso; la api lo rechaza igual por el tope. Caso de laboratorio.

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4: decidir si un requisito transversal (como R20) puede trazarse con aserciones `# Rn` dentro de los
tests de otros requisitos o si exige su propio `test_fXXX_rN_*`. Dos reviews (F-003 y F-081) lo han aceptado con nota.

## Repetición de `init.sh` tras recortar este informe

`bash harness/init.sh`, cuarta vez: **código 0, `ENTORNO LISTO`**, raíz `2319 passed, 47 skipped`, servicios por la caché de mi verde sin caché, `TAMAÑO` 138/140. Las vueltas 2 y 3 cayeron en `test_f059_r7…` y `test_f059_r9…` (falta `nieto.pid`), por carga ajena: suites de otros cinco proyectos en paralelo, test no tocado por el diff y 1 de 3 verde a solas. Ver O5.
- **O5 · `test_f059_ejecucion.py` (R7, R9) es frágil con la máquina cargada.** Su doble `con_nieto.py` no llega a escribir el pid antes del timeout de 2 s. No es de F-081; candidato a `arnes-base`.
