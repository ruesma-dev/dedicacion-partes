<!-- progress/review_F-068.md -->
Revisión completa (pasada 1): `dev` (`d95b3ab`) `...` HEAD `265ca23`

# F-068 · Review 1 · **APROBADO** (APPROVED)

Sin bloqueos. Condición de cierre ajena al código: el visto bueno del humano
al único superviviente equivalente (crítico: 0), ya en `current.md` («⚠ Lo
que espera al humano»); sin él, no hay `done`. Aparte de eso, nada bloquea.

**Rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, campaña entera con
0 supervivientes salvo aceptados por el humano, MANUAL con comandos exactos.

## Verificación ejecutada por el reviewer

- Sin `.arnes_cache/suite_*.ok`, `bash harness/init.sh` solo: **exit 0**, «ENTORNO LISTO», **0 `[KO]`**. Un único `[AVISO]`:
  ruff, 309 de deuda previa. Raíz 418 passed y 1 skipped, api 1337, front
  458, transfer 1737. `PUERTA COBERTURA` 100,0 % (126/126); `PUERTA TAMAÑO`
  dentro de los topes. Árbol limpio después. Ni Sigrid, ni Azure, ni `.env`.

## Orden y una sola regla

`partida_del_vinculado`: elegida → titular (R17) → `historial()` → `ci()` →
sin partida. `ci()` = `partida_por_cuenta_o_nombre`: una hoja con su cuenta ⇒
`ci_tipo`; varias ⇒ `puntuar` (las que no casan, a 0); ninguna ⇒ entre las
hojas activas `CI*`, solo las que casan; máximo único (`_maximo_unico`) ⇒
método del casador; empate ⇒ `desempate_ci4` entre las del máximo (6
decimales); si no, `varias_ci`, `sin_ci` o `empate_nombre`.

El historial filtra las líneas `CI*` (D2) y llama a `previa_en_obra`,
importada y no copiada (R3; un test lo comprueba con `is`). La ventana es la
del trabajador con el periodo incluido (D3). Preflight (`_partida`), selector
y cola (`proponer`) y lote llaman a las **mismas** dos funciones. Las
lecturas son perezosas con `_UnaVez` (R12, R14).

RM4: el mutante `:263` (`round(v, 7)`) en una copia de mi scratchpad hace
caer `test_f068_r7_el_empate_es_el_del_maximo_unico_a_6_decimales`.

## Compatibilidad del payload

Api (`_vinculado`, `_vinculado_a_proponer`) y transfer (`para_pipeline`)
solo añaden `descripcion`/`tipo_res` con valor: sin ellos, el payload es el
de F-044 (tests R18 «la entrada de hoy»). Pydantic del transfer sin
`extra="forbid"`: uno viejo ignora los campos. Orden transfer → api → front.

## Desvíos declarados: los tres aceptados

1. **Cuatro tests de F-044 cambiados.** Tres de la api (payload con
   `tipo_res`; `auto_nombre` se guarda) fijaban el **contrato** viejo, que
   R17 y R18 cambian a propósito; uno del transfer, el texto de `sin_ci`
   (R9). Mínimos y comentados con su requisito (design §10). Los que §10
   preveía pasan sin tocarlos (historial vacío; `CIVE20`/`CIVE21` no son
   CI.4). R22 lo admite: «intactos» cede ante R17 y R18.
2. **T8 en el commit de T6.** Solo proceso, motivo real (el lote de F-044
   usa la memoria como cliente); RED de T8 en copia aislada, traza pegada.
3. **Clave `(obra, desde, hasta, recursos)`.** La api manda **una** petición
   por obra: `propuestas_mes._trozo` agrupa por `obra.ide` y el preflight
   del mes arma un payload por obra. En postventa y VAR el vinculado va con
   su titular y no lee historial. Queda «una vez por obra» (R15), y lo fija
   `test_f068_r15_propuesta_lote_igual_que_suelta`.

## Mutación (C4 bis)

- **Recálculo propio** (`alcance_de_feature` + `generar_mutantes`): 359
  líneas y **54 mutantes**, como el informe; el `:202` existe tal cual.
  **Campaña no reejecutada: 1405,8 s según el informe**; recálculo + RM1-RM6.
- **RM1** [x] SHA `cd8f0be7…` completo. Desde él solo cambian `progress/` y
  `tasks.md`, nada del alcance.
- **RM2** [x] con 4 workers, 26,0 × 4 ≈ 104 s por mutante, frente a líneas
  base de 75 a 133 s, con 53 de 54 muertos. 54 × 26,0 ≈ 1405,8 s.
- **RM3** [x] ningún equivalente muerto (campaña 1 incluida).
- **RM5** [x] reproducido ejecutándolo: `partida_del_vinculado(t, None,
  True|False, ci, h)` da lo mismo en 45 combinaciones (titular sin partida,
  `CI*`, `CP`, postventa, VAR × 3 `ci` × 3 `historial`); control: con
  elegida, el argumento **sí** cambia el resultado. **Equivalente
  confirmado**; fuera del visto bueno, **no bloquea**.
- **RM6** N/A justificado: no se quitó ninguna guarda. La ventana perezosa
  elimina dos equivalentes sin perder ninguna defensa.
- Sin cabecera de no válida; «Sin veredicto» 0; análisis completo.
- **JS manual** (SHA `e28dbd2…` completo; entre ese commit y HEAD el front no
  cambia). Reproduje **dos filas** al pie de la letra, sobre
  `git show e28dbd2` en una copia temporal: base `67 passed`; **N2**
  (→ `""`) y **N5** (→ `"CI del tipo"`) MUERTOS con 3 fallos, los tres
  tests de R20 de la tabla.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una `in_progress` · [x] rama `feature/F-068-…` · [x]
  `current.md` con cabecera «En curso: F-068» y su sección · [x] `history.md`.
- **C3** [x] hexagonal: regla en `application`, SQL en
  `infrastructure/sigrid`, el dominio solo gana un campo · [x] primera línea
  con la ruta (21 ficheros) · [x] sin `print`, TODO, secretos ni
  dependencias nuevas · [x] trampas: no toca la escala, postventa va con el
  titular, la única lectura nueva es un SELECT y la escritura es la de F-044.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad en la tabla de abajo, todo en verde · [x] sin red
  ni BBDD · [x] T13 y T14 en «⚠ Lo que espera al humano»: (a), (b) y (c)
  con PARAR, Cancelar y nunca «Registrar»; avisa de que el selector guarda
  en la BBDD **local**.
- **C4 bis** [x] rigor declarado · [x] RED real de T1-T8, T10, T11 y del caso
  0678 · [x] cobertura 100 % · [x] mutación verificada · [x] coste por
  mutante coherente · [x] análisis completo; el cero en `critico` queda
  **condicionado** al visto bueno ya anotado · [x] «Evidencias» con los
  workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T1-T12 y T15 `[x]` con commit `F-068 Tn:` (T13-T14, MANUAL,
  `[ ]` como deben) · [x] sin temporales · [x] `features.json` `in_progress`.

## Cobertura de requisitos (tests `test_f068_*`)

| R | Tests |
|---|---|
| R1-R3 | `reglas::r1_*` (6), `r2_*` (10, D2 y D3), `r3_la_misma_funcion…`; `pipeline::r1_preflight_el_caso_de_la_0678`, `r2_*` |
| R4-R10 | `reglas::r4_*`, `r5_*` (8), `r6_*` (5), `r7_*` (7), `r8_*` (sí/no), `r9_*` (5, ≤ 300 caracteres), `r10_*` (2) |
| R11-R14 | `sql::*` (`m.obride = ?`, sin `LIKE 'M%'`, lotes, `truncated`), `pipeline::r11_*`, `r12_*`, `r13_*`, `r14_*` (2) |
| R15-R16 | `pipeline::r15_*` (selector, lote, propuesta-lote, ruta), `r16_*` (con 5 métodos) |
| R17-R18 | `api::r17_*` (preflight y cola), `api::r18_*`, `pipeline::r18_*` |
| R19 | `pipeline::r16_guardada_con_metodo_propio…[ci_tipo]` (D4-A: se escribe tal cual) |
| R20 | `front::r20_*` (4) |
| R21 | revisión: `ARCHITECTURE` §regla-vinculado, `INTEGRACION` §5 y la nota bajo F-044 R16 |
| R22 | los 4 de F-044 (desvío 1); el resto, intactos y en verde |
| R23 | MANUAL T13, pendiente del humano |

## Bloqueos: ninguno.

## Observaciones (no bloquean; recogerlas, no dejarlas en «anotado»)

1. **Visto bueno del humano al equivalente `:202` antes de `done`.** Si no,
   se quita de raíz: `elegida_valida` por defecto, sin pasarlo en `proponer`.
2. **RM5:** en rigor crítico, el informe del implementer debe traer la
   demostración **ejecutable** del equivalente, no solo el texto. Vale la de
   este informe; queda para la próxima feature crítica.
3. **design §8 e `INTEGRACION.md`** dicen que con una api vieja «el nombre no
   casa». Pero en `registro/*` `tipo_res` ya viaja desde F-044, así que el
   preflight puede casar por categoría (`auto_categoria`). Es benigno: es
   una propuesta visible en el modal durante el hueco del despliegue.
   Precisar la frase al cerrar.
4. **T13 no nombra al trabajador.** Poner su código (`MO/0601`, que ya está
   en `features.json`) para que la MANUAL sea exacta.
