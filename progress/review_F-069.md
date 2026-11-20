<!-- progress/review_F-069.md -->
Revisión de evidencias desde 3f9b5ff (pasada 4), sobre `46e7835` (`git diff 6b6d637..46e7835`, 5 commits).

# F-069 · Review 4 (evidencias)

**Veredicto: APPROVED.** La campaña es real y reproducible. Los 17 supervivientes son equivalentes:
los he juzgado uno a uno contra el código. Los 12 que mataron los tests nuevos los mataban de verdad:
he reproducido 8. RM1-RM7 cumplidas. Queda una observación sobre un orden (O1) que no bloquea.

**La principal, en una línea:** reviews 1-3 (`ed7c212`, `3f9b5ff`, `789e8c4`): código APROBADO en `3f9b5ff`;
CAMBIOS REQUERIDOS 1-7 (review 1) y de papeleo (review 2) resueltos; O1-O3 de la review 3 corregidas en
`6b6d637` (comprobado: «decisión 6» en `current.md` l. 88 y en T16; los dos `warning` en l. 89; el sync
de F-030/F-044, «ya hecho»). Detalle de D20, tabla requisito → test y C1-C5: `git show 909a5e2:progress/review_F-069.md`
(review 2) y `git show 6b6d637:progress/review_F-069.md` (review 3).

**Rigor:** `critico` (`features.json`): fase RED, cobertura ≥ 90 %, mutación con 0 supervivientes sin
justificar en la muestra del nivel (uno por línea, 60 % de los candidatos, acotado a [100, 300]), RM1-RM7.
Capa e2e N/A: ningún servicio declara el bloque e2e.

## El delta: sin código de producción

`git diff --name-only 3f9b5ff..HEAD -- services` solo devuelve `tests/`: `test_f069_importes_api.py`,
`test_f069_importes_dominio.py`, `test_f069_traer_comentarios.py` y `dedicacion-transfer/tests/conftest.py`.
El resto es papeleo (`progress/`, `tasks.md`; `design.md` solo en `6b6d637`, ya revisado). Lo aprobado en
`3f9b5ff` sigue valiendo.

## C4 bis · mutación (verificada por mi cuenta)

- [x] **Informe generado por la herramienta**, sin «⚠ CAMPAÑA NO VÁLIDA» y con «Sin veredicto (base rota)»
  0. Corrió la línea base: 8 líneas base, entre 40,1 y 53,3 s. Ningún análisis ni declaración en `PENDIENTE`.
- [x] **Recálculo puro** (`harness.alcance` + `generar_mutantes` + `seleccionar` con la regla del nivel):
  1754 líneas en 25 ficheros y **473 mutantes**, fichero a fichero igual que el informe. **264 candidatos**,
  tope 159 y **159 elegidos** (semilla `20261030`). Los 17 supervivientes existen en la muestra, con el mismo
  operador y el mismo texto original → mutado.
- [x] **Ficheros sin mutantes (prueba de control)**, generando sin exclusión de alcance: `errors.py` da 0 en
  todo el fichero. `ports.py` da 1, `deps.py` 9 y `prueba_escritura_porcentajes.py` 150, todos fuera de las
  líneas en alcance, así que el cero es legítimo. `deps.py` se mutó a mano: reproduje `traer_sigrid=TraerDeSigrid(transfer, {})`
  (l. 172) y cae `test_f069_r15_el_contenedor_pasa_tipos_y_precio`.
- [x] **Campaña no reejecutada: 1752 s según el informe** (> 60 s): recálculo puro, RM1-RM7 y reproducción.
- [x] **O3 de la review 2, alcance de D20**: la muestra trae 9 mutantes de `texto_linea.py` (l. 18-93) y 11 de
  `_actualizar_tex`/`_tex_sigue_valiendo` (l. 1491-1543); los he listado con el recálculo. Sobreviven 2, la l. 1498
  y la l. 1511, las dos equivalentes (abajo).

### Los 12 que mataron los tests nuevos: 8 reproducidos

Todo en una copia (`git archive HEAD`) de mi scratchpad: aplico el mutante con `aplicar_mutante` y paso
los tests. Caen exactamente los tests que el informe nombra.

| Mutante | Cae |
|---|---|
| `repositories.py:574` `==`→`!=` | `test_f069_r32_poner_comentario_solo_en_esa_linea` |
| `repositories.py:834` `anio ==`→`!=` | `test_f069_r16_importes_del_mes_de_ese_anio_y_mes` |
| `repositories.py:819` `is None`→`not` | `test_f069_r3_una_cantidad_cero_se_lee_como_cero` |
| `traer_sigrid.py:154` `and`→`or` | `…titular_por_su_synckey_el_de_menor_ide_en_cualquier_orden` |
| `use_cases.py:1304` `kv[0][1]`→`kv[1][1]` (es el sorteado) | `test_f069_r7_el_snapshot_ordena_por_vinculado_y_obra` |
| `schemas.py:153` `is None`→`not` | `test_f069_r10_una_caja_a_cero_y_sin_copiado_sale_con_sus_claves` |
| `importes.py:36` `frozen=True`→`False` | `test_f069_r1_r3_tipo_e_importe_del_mes_son_inmutables` |
| `registro_pipeline.py:1518` `con_tex=True`→`False` | 7 de `test_f069_tex_registrada.py` (R26) |

**El `conftest.py` del transfer.** Con el de `6b6d637`, el mutante de la l. 1518 **sobrevive**; con el
nuevo, caen 7. El doble no es frágil: es fiel. El SQL real (`sigrid_write_client.py`
l. 879-883) solo lee `tex` y `obride` con `con_tex`, y el doble hace lo mismo. La suite del transfer pasa
entera con él (1956 en `init.sh`). Los tests nuevos de la api miran el SQL compilado o el valor de dominio,
sin acoplarse a detalles sueltos: los acepto.

### Los 17 supervivientes: juicio uno a uno

Todos son **equivalentes**, y he comprobado en el código la invariante de origen que cita cada análisis:

- **Valor nunca 0 ni `""`** (2, 3, 4, 10, 11, 15). Los `ide` de Sigrid son > 0. En los snapshots la
  cantidad va como `str(Decimal)` o `None` (l. 1060, 1313). `unidad` es `eur` o `km`. El comentario pasa por
  `validar_comentario` o `comentario_de_sigrid`, que dan `None` para el vacío.
- **Sin `__bool__` ni `__len__`** (12, 17): `TipoCantidad` y `HoraRecurso` (grep en `domain/` de ambos).
- **Defecto que no se usa** (1, 5, 16). En el 1, `getattr` con `fuente` `None` da `cantidad` `None`. En el 5,
  `_snapshot_importes` siempre pone `es_postventa`. En el 16, el único llamador (l. 218-219) pasa `con_tex`.
- **Rama inalcanzable** (13, 14): en pruebas, la obra sale de `obra_por_codigo`, con `obr.ide` como clave
  primaria (l. 265), o se lanza `RuntimeError`.
- **Retorno muerto** (6, 7): los dos llamadores de `_aplicar_foto` (l. 442 y 1404) descartan lo que devuelve.
  Hago mía la propuesta al humano: quitarlo o usarlo, fuera de F-069.
- **Mismo error** (8) y **mismo resultado** (9): el 8 es el de RM5, abajo. En el 9, `""` acaba en `None` por
  los dos caminos.

## RM1-RM7

- [x] **RM1.** El informe mide `a0ad1e2` y HEAD es `46e7835`. `git diff --name-only a0ad1e2..HEAD` solo da
  `progress/` y `tasks.md`, nada del alcance: no hay que repetir la campaña.
- [x] **RM2.** Media por mutante con la suite entera: 38,6 s, frente a una base de 52,9 s. Es la misma escala;
  queda por debajo por el `-x` con 142 de 159 muertos. 159 × 38,6 / 4 workers ≈ 1534 s, más las líneas
  base, ≈ 1752 s. Cuadra.
- [x] **RM3.** Ningún equivalente sale muerto: los 12 que mueren con los tests nuevos cambian el comportamiento,
  y su test lo demuestra (tabla de arriba).
- [x] **RM4.** Usado: subconjuntos de tests sobre la copia, nunca en el árbol.
- [x] **RM5.** Elijo el 8 (`importes.py:107`, `or`→`and`), el menos evidente. Demostración ejecutable:
  `validar_cantidad` original contra la mutada, con 26 entradas por unidad (52 casos: `None`, booleanos,
  enteros, flotantes, `nan`/`inf`, `Decimal`, textos válidos, vacíos y no numéricos, `"NaN"`, `"Infinity"`,
  listas, dicts, negativos, más de dos decimales, más del tope). **0 diferencias**, ni en la excepción ni en
  el mensaje.
- [x] **RM6.** N/A justificado: sin cambios de producción, ninguna guarda quitada. [x] **RM7.** El requisito central de F-069 (cantidades de caja y km) no es un orden entre colaboradores,
  y el orden de D20 no está en ningún R, solo en el design. Aun así probé a mano el único orden declarado.
  Lo cuento en O1.

## Observaciones (no bloquean; que el líder las recoja o se las lleve al humano)

- **O1 · El «al final» de D20 no lo ve ningún test.** Design §6.5 e informe (decisión 8): «el `tex` va
  después de todas las demás escrituras». En una copia moví `_actualizar_tex` al principio de
  `_ejecutar_vinculados`, **delante** de `EscrituraVinculados` (l. 1463), y la suite del transfer sigue en
  verde: 1952 passed. Daño real bajo: solo toca las `ya_registrado`, que `EscrituraVinculados` no escribe, y
  un nuevo intento es idempotente. Pero si fallan los vinculados, el `tex` ya habría cambiado. Hay dos salidas:
  un test que fije que el lote del `tex` es el último `escribir`, o que el humano acepte el hueco por escrito.
- **O2 · `current.md`, l. 4.** Dice a la vez «pasada de campaña hecha (T13/T18…)» y «Quedan T13/T18 (mutación,
  tras el APPROVED)». Hay que quitar lo segundo al cambiar de estado. Y `tasks.md` T13 dice que el análisis está
  «en `progress/impl_F-069.md`», cuando vive en `progress/mutacion_F-069.md` (el informe lo enlaza).

## Checkpoints (pasada de evidencias)

- **C1** [x] `ARNES_SIN_CACHE=1 bash harness/init.sh` entero sobre `46e7835` (pie). [x] `git status` limpio
  después: todo lo he mutado en el scratchpad.
- **C2** [x] Una sola feature activa. [x] Rama correcta. [x] `current.md` al día salvo O2.
- **C3 / C3 bis / C3 ter** [x] Sin cambios de producción ni de `docs/referencia/` desde `3f9b5ff`. **C3
  quater** pendiente de T17 al desplegar (listado en `current.md`), como en la review 3.
- **C4** [x] Los tests nuevos cubren R1, R3, R7, R10, R15, R16, R26 y R32 (tabla). [x] R1-R34 con test y
  R35-R36 MANUAL, sin cambios.
- **C4 bis** [x] Nivel declarado. [x] RED y «Evidencias» (con los totales de mutación ya puestos). [x] Cobertura
  `[OK]` 99,6 %. [x] Mutación válida: 0 supervivientes sin justificar. [x] RM1-RM7. [x] Capa e2e N/A justificada.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`. **C5** [x] Commits `F-069 T13:` / `F-069:`. [x] T13 y T18 `[x]`. T16 (MANUAL) y T17 (despliegue) siguen
  abiertas, como corresponde a esta fase.

## Cambios requeridos

Ninguno. Para el líder, antes del cierre: O1 (test o aceptación del humano) y O2.

**Automejora (propuesta para `reviewer.md`).** En RM7, añadir: «un orden que solo dice el design, y no un R, se prueba igual y su superviviente va como
observación, con dos salidas: test o aceptación del humano». Hoy el texto solo habla del requisito central.

## Resultado de `ARNES_SIN_CACHE=1 bash harness/init.sh` (`46e7835`, sin pipes)

Código 0, ningún `[KO]`, «ENTORNO LISTO». Raíz 2319 passed / 47 skipped (9 min 32 s); api 1640; front 573;
transfer 1956. `[OK]` PUERTA COBERTURA 99,6 % (687/690), TAMAÑO, CARRIL N/A y CAPA E2E N/A. Este informe, medido
con `python -m harness.tamano --feature F-069`.
