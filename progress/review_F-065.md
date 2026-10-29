<!-- progress/review_F-065.md -->
Revisión completa (pasada 1) · `git diff c82171c...b7a57ca9da23836b95901a8e2ec896ba710733aa`

# F-065 · review 1

**Veredicto: APROBADO** (sin bloqueos; tres observaciones no bloqueantes).

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
tests trazables, fase RED de los requisitos centrales, cobertura de las líneas
cambiadas y campaña de mutación con los supervivientes analizados. `sdd: false`:
se valida contra los 2 `acceptance`.

## Lo que se ha comprobado (con resultado real)

- **`bash harness/init.sh`**, tal cual y solo, tras borrar
  `.arnes_cache/suite_{api,front,transfer}.ok`: exit 0, «ENTORNO LISTO», ningún
  `[KO]` (solo el `[AVISO]` de ruff, 309, deuda previa). Raíz 418 passed,
  1 skipped; api 1308; front 434 (430 + 4 de F-065); transfer 1585.
  `PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de producción frente a
  dev)`; `PUERTA TAMAÑO` OK.
- **Comportamiento** (`app.js:568-613`): la activa que el mes ya no tiene entra
  en el `Map` de `tiposIncidenciaDelMes` con `n: 0` **después del conteo y
  antes del único `sort`**; si sigue presente, manda la ficha contada (mismo
  contenido que F-063). `renderCabecera` solo pinta lo que devuelve. La otra
  llamada (test de F-063, un argumento) sigue valiendo con `activo` undefined.
- **El comparador vive en un solo sitio**: el de las fichas solo está en
  `tiposIncidenciaDelMes` (`app.js:612-613`); los otros `localeCompare` de
  `app.js` (924-930) son el orden de la tabla, otra cosa. Lo fija además el
  estático `test_f065_r1_el_orden_de_las_fichas_vive_en_un_solo_sitio`.
- **Ningún test existente cambia**: el diff solo añade
  `tests/test_f065_ficha_activa_en_su_sitio.py`; `test_f063_filtro_incidencia.py`
  intacto (sus 16 tests en verde sin tocar aserciones).
- **Motivos de conflicto**: el diff de `app.js` no nombra `motivo`, `pisado`,
  `sobrecarga` ni `sin_partida`; siguen solo en `rotuloConflicto` /
  `marcadaPorDefecto`. La guarda del transfer (F-013 R4) pasa en la suite.
- **RED reproducida por mí**: `app.js` y los tests de `27c36da` copiados al
  scratchpad, `pytest` de F-065 + F-063 ⇒ **3 failed, 17 passed**; fallan los
  dos de posición (índice 5 `'P Permiso 1' != 'B Enfermedad 0'`) y el estático
  (`tipos.push(` en `renderCabecera`), igual que la traza del informe.
- **Dobles**: `_inc` / `_trab` / `_linea` de F-063 con la forma serializada
  completa de `IncidenciaOut` / `TrabajadorOut` / `LineaOut`; el `otra` del
  test de desempate parte de `_inc` (todas las claves). `filtro_v` es estado
  interno con la forma que guarda el clic (`{codigo, letra, nombre}`). Ver O1.
- **F-066**: entrada bien formada (las 9 claves de las demás, `pending`,
  `sdd: false`, `estandar`, 2 `acceptance` verificables, rama propia); no se
  exige nada de ella. Ver O3.

## Campaña manual (`progress/mutacion_manual_F-065.md`)

- **RM1**: medida sobre `6abe00dc656c81da38a8ea9479e9e8dcaa9fcf13`;
  `git diff --stat 6abe00d b7a57ca -- services/` vacío: el alcance medido es el
  revisado.
- **Reejecutada ENTERA** (12 mutantes, el informe declara 76,9 s, por encima
  de 60 s, pero es barata): script extraído del bloque del informe al
  scratchpad y lanzado desde la raíz del worktree sobre `b7a57ca`. Línea base
  `20 passed`; **las 12 filas salen idénticas byte a byte** a las del informe
  (`diff` vacío), con sus fallos y tests que matan; 101,3 s de reloj, 1 worker.
  `git status` limpio después.
- **RM2**: base ~4-6 s, ~6 s por ejecución, 1 worker: coherente.
- **RM3**: ningún mutante equivalente sale muerto.
- **N10 (superviviente, `tipos.set(activo.letra, …)`): equivalente, aceptado.**
  La clave del `Map` es interna; la siembra va tras el conteo y solo si el
  `codigo` falta, y se devuelven los valores. Solo cambiaría si un tipo
  presente tuviera como `codigo` la letra de la activa. Lo he comprobado en
  **quien construye el dato**: el catálogo sale de `auxhor` con
  `WHERE aux.cod LIKE 'CI%'` (`services/dedicacion-api/config/config.yaml:227`),
  y la letra es el texto entre paréntesis de `res` o el código sin `CI`
  (`domain/incidencias.py:25-36`): ningún código es una letra («V», «B»…).
  Matarlo exigiría un doble fuera del dominio real.
- **RM5**: N/A por nivel (`estandar`: basta la justificación escrita, que está).
- **RM6**: N/A, no se quitó ninguna guarda; al contrario, N6 demuestra que la
  guarda `activo &&` muerde (16 fallos).

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base existen.
**C2** [x] una sola `in_progress` (F-065) · [x] rama
`feature/F-065-ficha-activa-en-su-sitio` · [x] `current.md`: primera línea
reescrita con F-065 en curso y review lanzada; lo demás es lo pendiente del
humano de features cerradas (práctica del proyecto) · [x] `history.md` tiene F-063.
**C3** [x] hexagonal: solo front, sin lógica de negocio nueva (orden de
presentación) · [x] primera línea con ruta (`app.js` sin cambio de cabecera;
el test nuevo la lleva) · [x] sin prints, TODOs, secretos ni dependencias ·
[x] las tres trampas: no toca porcentajes, postventa ni escrituras a Sigrid.
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] el `acceptance` 1 → los tres tests de comportamiento; el 2 → RED
reproducida + F-063 intacto + init.sh · [x] sin red ni BBDD (node con DOM de
mentira) · [x] MANUAL listada en «⚠ Lo que espera al humano» con pasos exactos,
en local (quitar una incidencia escribe en la BBDD de la app).
**C4 bis** [x] rigor declarado · [x] fase RED con salida real (y reproducida) ·
[x] cobertura `N/A` con motivo impreso por init.sh (no hay Python de
producción; el JS no tiene medidor) · [x] mutación: `harness.mutacion` solo
muta Python (0 mutantes por construcción: el diff no tiene `.py` de
producción), sustituida por la manual con una fila por mutante, texto exacto,
fallos y SHA completo; **reproducidas las 12 filas** · [x] muertos comprobados
(reejecución) · [x] coste por mutante ~8 s × 1 worker, > 1 s · [x] sin
«CAMPAÑA NO VÁLIDA» (la manual corre línea base y aborta si está en rojo) ·
[x] RM1 · [x] RM2 · [x] RM5 N/A justificado · [x] RM6 N/A justificado ·
[x] superviviente analizado · [x] «Evidencias» con tests, cobertura, mutantes
y supervivientes, tiempos y workers (1) · [x] ningún N/A sin motivo.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] `sdd: false`, sin `tasks.md`: commits `F-065 T1-T3` + alta y
lanzamiento · [x] árbol limpio · [x] `features.json` refleja `in_progress`.

## Cobertura (acceptance → test)

| Acceptance | Test |
|---|---|
| 1 · activa a 0 en su sitio por letra | `test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final` |
| 1 · … y por nombre | `test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra` |
| 1 · los demás casos no cambian | `test_f065_r1_sin_filtro_activo_la_fila_no_cambia` + los 16 de F-063 sin tocar |
| 1 · orden en un solo sitio | `test_f065_r1_el_orden_de_las_fichas_vive_en_un_solo_sitio` |
| 2 · RED, F-063 en verde, init.sh | traza del informe (reproducida), suite del front 434 passed, init.sh exit 0 |

## Observaciones (no bloqueantes)

1. **O1 · Código fuera del dominio en un doble.**
   `test_f065_ficha_activa_en_su_sitio.py:62` usa `"codigo": "CVA"`; el sync
   solo trae códigos `CI%` (`config.yaml:227`). La forma es la real, el valor
   no. Mejor `"CIVA"` (o similar) para no contradecir el propio argumento de
   N10. No cambia ningún veredicto.
2. **O2 · Citar el invariante en el análisis de N10.** El análisis de
   `mutacion_manual_F-065.md` dice «códigos de catálogo, `CIV`, `CIE`…»; la
   prueba está en `config.yaml:227` (`LIKE 'CI%'`) y `domain/incidencias.py`
   (`letra_y_nombre`). Añadir la cita deja el «equivalente» verificable sin
   repetir esta búsqueda.
3. **O3 · F-066 empata en prioridad con F-054 (8).** «Va DESPUÉS de F-054»
   solo lo dice la descripción y el orden del JSON; si el orden importa,
   prioridad 9 lo haría explícito (F-021 ya tiene 9: el líder decide).

## Cambios requeridos

Ninguno.
