# F-081 · Informe del implementer (`estandar`)

Rama `feature/F-081-operaciones-en-celdas`. Spec aprobada el 2026-11-26 (D1-D9 la (a)).

## Hecho

La celda de % de cada línea y la casilla de cantidad (km y €) admiten
operaciones (`30+10`, `=100/3`, `(8+4)*2`). Mientras se escribe una operación
no cuenta: la celda se ve en cursiva y no se tocan el %, el total, la marca de
copiado ni el guardado. Al confirmar se evalúa con un evaluador propio que no
usa `eval`. En el % se confirma al salir de la celda, con Tab o con Enter (y
el foco sigue yendo al buscador de obra); en la cantidad, al salir o con Enter
(el foco no se mueve). La celda se queda con el resultado redondeado a dos
decimales, con coma, y sigue el camino del número tecleado. Si la operación no
es válida, o en el % da ≤ 0 o > 100, sale un aviso de error, la celda vuelve a
lo último válido y no se guarda. A la api solo llega el número. La api y el
transfer no cambian, y `azure-apps` tampoco (design §10).

## Tareas y commits

| Tarea | Commit |
|---|---|
| T1 tests del evaluador (RED) | `87e59df` |
| T2 evaluador en `app.js` | `7ef5131` |
| T3 test estático R5 | `883f221` |
| T4 tests de la celda de % (RED) | `190a8ca` |
| T5 `chipEditable`, CSS, lista de `test_f030_celda_pct` | `a72a909` |
| T6 tests de la casilla de cantidad (RED) | `affa5ee` |
| T7 `chipImporte`, listas de `test_f069_importes_front` | `6a3235e` |
| T8 regresión R16, R18, R19 (sin RED: fijan lo de hoy) | `972d16d` |
| T9 `docs/ARCHITECTURE.md` + test R22 | `d2e240e` |
| T10 suite del front + este informe | `186687f` |
| T11 MANUAL M1 | **sin marcar, del humano** |
| T12 imports del test + `bash harness/init.sh` en verde | `11a2139` + este commit |

## Ficheros

- `services/dedicacion-front/static/js/app.js`: funciones nuevas de primer nivel tras `parsearPct`
  (`esExpresion`, `evaluarExpresion`, `redondear2`, `textoNumero`, `confirmarExpresion`);
  `chipEditable` (rama de operación en `input`, nueva escucha `blur` antes de la de «en blanco»,
  `title`); `chipImporte` (el cuerpo de hoy de `input` pasa tal cual a `aplicarCantidad()`, rama
  de operación, `blur` y Enter que confirman, `title`).
- `services/dedicacion-front/static/css/styles.css`: `.pct-input.expresion, .importe-cantidad.expresion { font-style: italic; }`.
- `services/dedicacion-front/tests/test_f081_operaciones.py` (nuevo, 94 tests).
- `docs/ARCHITECTURE.md`: un párrafo en «`dedicacion-front` — captura, nada más» (R22).
- `progress/current.md`: nota del implementer bajo F-081.

No se han tocado `parsearPct`, `cantidadTecleada`, `parsearDia`, `cuerpoLineas`,
`cuerpoImportes`, `elementoImporte`, `chipIncidencia` ni `teclas`.

## Tests existentes tocados (solo nombres en listas cerradas, ninguna aserción)

- `tests/test_f030_celda_pct.py`: `FUNCIONES_HOY` + los cinco nombres nuevos. De ahí los heredan
  `FUNCIONES_LETRAS` y los tests de F-030 R8-R13 y de F-061.
- `tests/test_f069_importes_front.py`: los cinco nombres en las tres listas que cargan
  `chipImporte` (`test_f069_r11_chip_con_comentario_marca_y_revisado`, `GUARDAR_CHIP`,
  `test_f069_r12_d18_teclear_la_misma_cantidad_no_quita_la_marca`). Antes de añadirlos,
  `test_f069_r12_d18_teclear_la_misma_cantidad_no_quita_la_marca` fallaba con ReferenceError
  (`esExpresion` no estaba cargada), no por una aserción. Después, 14/14 en verde.
- `test_f025`, `test_f030_tabla_incidencias`, `test_f041`, `test_f042` y `test_f061` no necesitaron
  cambios: leen el texto de `chipEditable` (y los literales que miran no han cambiado), usan un doble
  de la función, o la cargan a través de `FUNCIONES_HOY`.

## Desviaciones (y por qué)

1. **R4, el tope de 100 caracteres se mide sobre el texto tal cual llega.** Design §5 dice que se
   quitan antes el `=` y los espacios. R4 dice «SI el texto pasa de 100 caracteres … sin recorrer la
   expresión entera», y quitar los espacios ya obliga a recorrerla. Manda el requisito: `" "*98 + "1+1"`
   da «demasiado larga». Un texto de 5 millones de caracteres se corta en tiempo constante
   (test `r4_lo_largo_no_se_recorre_entero`).
2. **R9/R10 cuando la línea estaba a 0.** Si la operación falla, la celda vuelve vacía. Design §5
   dice que la escucha de «en blanco» «ve entonces un número o un vacío, como siempre», pero esa
   escucha rellenaría lo que falta hasta 100 y guardaría, y eso contradice el «sin guardado» de R9 y
   R10. Solo en ese caso, la escucha nueva hace `stopImmediatePropagation()`
   (test `r9_linea_sin_pct_vuelve_vacia_y_no_rellena_ni_guarda`). Con un % distinto de 0 no cambia
   nada.
3. Detalles, no son desviaciones: `3 4` da 34, porque se quitan los espacios (design §5). En la
   casilla de cantidad, Enter hace `preventDefault` también con un número llano: no hay formulario y
   antes no tenía escucha de teclado. `1+vac` busca incidencia como hoy y no casa con nada (R17).

## Fase RED (trazas reales)

**T1**: `python -m pytest tests/test_f081_operaciones.py -k "r1 or r2 or r3 or r4 or r6 or r15" -q`
(desde `services/dedicacion-front`, antes de T2):
```
E       AssertionError: no existe la función esExpresion en app.js
E       assert None
tests\test_f042_sugerencias.py:43: AssertionError
65 failed, 1 deselected in 3.02s
```
Tras T2: `66 passed in 8.39s`.

**T4**: `python -m pytest tests/test_f081_operaciones.py -q -k "r7 or r8 or r9 or r10 or r11 or r17 or r21"` (antes de T5):
```
FAILED tests/test_f081_operaciones.py::test_f081_r7_mientras_hay_expresion_no_cuenta_ni_guarda
FAILED tests/test_f081_operaciones.py::test_f081_r7_solo_expresion_no_toca_el_total
FAILED tests/test_f081_operaciones.py::test_f081_r7_volver_a_un_numero_quita_la_marca_y_cuenta
FAILED tests/test_f081_operaciones.py::test_f081_r8_al_salir_pone_el_resultado_cuenta_y_guarda_una_vez
FAILED tests/test_f081_operaciones.py::test_f081_r8_el_cien_entra_y_un_numero_llano_al_salir_no_se_toca
FAILED tests/test_f081_operaciones.py::test_f081_r9_fuera_de_rango_avisa_repone_y_no_guarda
FAILED tests/test_f081_operaciones.py::test_f081_r9_linea_sin_pct_vuelve_vacia_y_no_rellena_ni_guarda
FAILED tests/test_f081_operaciones.py::test_f081_r10_no_valida_avisa_repone_y_no_guarda
FAILED tests/test_f081_operaciones.py::test_f081_r10_demasiado_larga - Assert...
FAILED tests/test_f081_operaciones.py::test_f081_r11_enter_confirma_y_va_al_buscador_de_obra
FAILED tests/test_f081_operaciones.py::test_f081_r17_con_letras_busca_incidencia_aunque_lleve_operadores
FAILED tests/test_f081_operaciones.py::test_f081_r21_la_celda_de_pct_dice_que_admite_operaciones
12 failed, 3 passed, 65 deselected in 5.79s
```
Ejemplos de fallo: `At index 2 diff: ['30+', 30, False] != ['30+', 30, True]` (R7) y
`assert ('100/3' == '33,33')` (R8). Los 3 que ya pasaban fijan lo de F-030: `1+vac` sin
coincidencias y `30+10` sin tocar el total.

**T6**: `python -m pytest tests/test_f081_operaciones.py -q -k "r12 or r13 or r14 or r21_la_casilla"` (antes de T7):
```
FAILED tests/test_f081_operaciones.py::test_f081_r12_mientras_hay_expresion_no_cambia_cantidad_marca_ni_guarda
FAILED tests/test_f081_operaciones.py::test_f081_r12_la_marca_de_copiado_no_se_va_con_una_expresion
FAILED tests/test_f081_operaciones.py::test_f081_r13_al_salir_pone_el_resultado_y_sigue_como_tecleado
FAILED tests/test_f081_operaciones.py::test_f081_r13_enter_confirma_sin_mover_el_foco_y_la_misma_cantidad_deja_la_marca
FAILED tests/test_f081_operaciones.py::test_f081_r13_redondeo_y_negativo_van_como_tecleados
FAILED tests/test_f081_operaciones.py::test_f081_r14_no_valida_avisa_repone_lo_ultimo_valido_y_no_guarda
FAILED tests/test_f081_operaciones.py::test_f081_r21_la_casilla_de_cantidad_dice_que_admite_operaciones
7 failed, 80 deselected in 2.45s
```
Ejemplo: `{'cantidad': '50+50'} != {'cantidad': '100'}`: hoy el texto de la operación se guardaba tal cual.
Tras T7: `101 passed` (`test_f069_importes_front.py` + `test_f081_operaciones.py`).

T8 (R16, R18, R19), T3 (R5) y T9 (R22) no tienen fase RED: fijan lo de hoy o comprueban texto, y se escribieron en verde.

## Tests por requisito

R1-R4, R6 y R15: `test_f081_r1_*` … `test_f081_r15_*`, más `r9_r10_confirmar_expresion_*`. R5:
`r5_app_js_no_evalua_texto_como_codigo`. R7-R11, R17 y R21 (%): tests en node sobre el
`chipEditable` real. R12-R14 y R21 (cantidad): sobre el `chipImporte` real. R20: se comprueba con
`cuerpoLineas` y `cuerpoImportes` dentro de los tests de R7, R8, R12 y R13. R16:
`r16_*` y las suites de F-030 y F-069 sin cambiar ninguna aserción. R18: `r18_*`. R19: `r19_*`,
con `teclas` real y el editor abierto. R22: `r22_*`.

## Salida de `init.sh`

`bash harness/init.sh` (final, tras `11a2139`): **ENTORNO LISTO**, exit 0, sin `[KO]`.
- raíz: `2319 passed, 47 skipped in 1171.36s`; front: `708 passed in 129.74s` (sin caché);
  api y transfer en verde (caché: sin cambios).
- ruff: 439 avisos, igual que antes (ninguno nuevo; `test_f081_operaciones.py`: «All checks passed!»).
- `[OK] PUERTA COBERTURA: N/A (F-081 no cambia líneas Python de producción frente a dev)`
- `[OK] PUERTA CARRIL: N/A (F-081 es de nivel estandar: no declara límites)`
- `[OK] PUERTA TAMAÑO: … impl 161/220` · `[OK] CAPA E2E: N/A (ningún servicio declara el bloque e2e)`

## MANUAL pendiente (T11, humano)

M1 (design §8), en local o tras desplegar el front (Ctrl+F5), en un mes abierto y sin registrar en Sigrid:
1. En la celda de % de una línea, teclear `100/3` y Tab ⇒ `33,33`, y el total en vivo lo suma.
2. `=50+60` y Tab ⇒ aviso de rango, y la celda vuelve a `33,33`.
3. `30+` y Enter ⇒ aviso «no válida», y el foco pasa al buscador de obra.
4. En una casilla de km, `120*2` y Enter ⇒ `240`, y aparece el «●» de guardando.
5. Recargar el mes ⇒ `33,33` y `240` siguen ahí.
Resultado en `progress/manual_F-081.md`. Para cerrar faltan además la review y desplegar solo el front.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests de F-081 | 94 passed (`test_f081_operaciones.py`) |
| Suite del front (`services/dedicacion-front`, su `.venv`) | **708 passed**, 0 failed, en 172,34 s |
| Suite de la raíz (dentro de `init.sh`) | 2319 passed, 47 skipped, en 1171,36 s |
| Cobertura de las líneas cambiadas | N/A según `init.sh` («no cambia líneas Python de producción»): el cambio es JS y no hay herramienta de cobertura para JS en este arnés. Lo compensa que cada rama nueva (operación válida, fuera de rango, no válida, vacía tras el fallo, con letras, Enter y blur) tiene su test en node sobre el código real. |
| Mutación | **N/A (informativa en `estandar`)**. Pasada de campaña sobre `8868538`, tras el APPROVED: `python -m harness.mutacion --feature F-081` sale con código 3 e imprime «ALCANCE VACÍO en F-081: ni una línea de producción que mutar … 0 fichero(s), 0 línea(s) de producción (origen rama)». Motivo: el código cambiado es JS (`app.js`) y la herramienta muta solo Python. No genera `progress/mutacion_F-081.md` a propósito (no escribe un cero no medido). 0 mutantes, 0 supervivientes. |
| Capa e2e | Ningún requisito lleva `(capa: e2e)`, todos son `unit`. Ver la línea `CAPA E2E` de `init.sh`. |
