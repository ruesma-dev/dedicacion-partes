<!-- progress/review_F-054.md -->
Revisión incremental desde 5c42b61 (pasada 8), HEAD `d347554`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 8 (segunda enmienda T24-T26)

**Veredicto: APROBADO (APPROVED).** T24-T26 cumplen R43-R47 y D20-D21. Ningún motivo pasa a decidir
nada, el `partida_cod` de la línea VAR solo cambia el texto y todos los tests ajenos tocados están en
la lista cerrada. Sin bloqueos; cuatro observaciones (O11-O14), no bloqueantes.

**Rigor:** `critico` (`features.json`): RED, cobertura, mutación con 0 supervivientes, RM5 y MANUAL.
Anteriores: 7, 6 y 2 APROBADAS; 5, 4 y 3 CAMBIOS solo por `current.md`; 1 RECHAZADA (`git show <sha>:…`).

## Delta revisado (`git diff 5c42b61..HEAD`, 38 ficheros)

- **Motivos: nunca clave ni decisión.** Transfer: `partida_var_de` decide igual que antes
  (`catalogo.obra`, `obra_ide != catalogo.obra.ide`, `catalogo.partidas.get(var_paride)`: todo por
  `ide`); el código solo entra en el `format`. `traducir` y `registro_pipeline.py` (l. 673-704) siguen
  las mismas ramas; cambia solo el argumento del texto. Api: `_obras` cambia `existen` por `codigos`
  (mismo conjunto de claves; el `cod` solo va al `Obra` de reserva, que se pinta); `_nombre_obra` es
  texto. Ningún motivo entra en `clave_conflicto`. Front: `agruparNoTraidas` mete el motivo en la clave
  de **agrupar para pintar**, como manda R44; no decide qué se acepta. El único lector previo que
  decide por texto es `pintarModalPreflight` (regex R20 de F-050, `app.js:3774`: «la partida (.+)
  elegida no es una partida hoja activa…»), y no casa con ningún texto nuevo
  (`MOTIVO_PARTIDA_PV_NO_HOJA` dice «indicada a mano»; los VAR empiezan por «partida VAR»):
  `test_f050_r29_las_demas_omitidas_*` en verde.
- **El `partida_cod` VAR no decide nada en el transfer.** Lectores de `linea.partida_cod` (grep): en la
  rama `var_paride` (l. 669-691), solo los dos `format`, y `a.partida_cod = nodo.cod` lo pisa con el del
  catálogo; los demás lo leen bajo `if linea.paride` (l. 692-718), y la VAR no trae `paride`.
  `reglas_porcentajes.decidir` no lo lee (usa `self._partida`); `lecturas_lote.py` tampoco, y
  `registro_vinculados.py` lee el de la acción. Lo fija
  `test_f054_r47_el_partida_cod_de_la_var_no_decide_nada` (con `"OTRA"`, misma acción, `paride`,
  código `"29"` y método). Api: la clave va solo si `partida_de_entrada` no es `None`, nunca la elegida
  (`test_f054_r47_nunca_la_elegida_de_la_fila`, `test_f050_r19_*`); normales y postventa, idénticas.
  `propuesta_*` de la api lee el `partida_cod` de la **respuesta** y solo con método de propuesta, que
  la VAR no tiene.
- **Preflight y `ejecutar`, igual salvo el texto:** mismas acciones, conflictos y escrituras; los
  tests de F-039/F-044/F-062/F-064/F-068 en verde y sin tocar, salvo los de la lista cerrada.
- **La cabecera es de verdad la estándar:** mismas clases que `renderCabeceraTabla()`
  (`app.js:663-735`): `th-sort`, `sort-arrow`, `filter-row`, `filtro-celda`, `col-filter`
  `type="text"` y `filter-clear` «Limpiar» en la última celda; tabla `tabla-reg filterable`; las
  reglas estándar de `styles.css` (l. 515-562), sin tocar; fuera `ordenable`, `filtro-traer` y
  `tabla-traer` (grep vacío en JS y CSS). «Limpiar» vacía también el `<select>` (es `.col-filter`, y el
  valor `""` es «Todos»). Escape actúa solo en `INPUT`.
- **`test_f050_r29` sigue protegiendo la elección de partida:** sin tocar; `JS.count("<select") == 2`
  y los dos están en `pintarTraerSigrid` (el de Estado); ninguno en las cuatro funciones de partida.
- **Tests ajenos tocados:** todos en la lista cerrada (tasks.md l. 6), y solo cambia el esperado:
  `test_f039_preflight_var.py` (FUERA/OTRA_OBRA), `test_f002_postventa.py` (`"11"`),
  `test_f025_universo_postventa.py` (`"0713"`), api `test_f039_registro_var.py`
  (`"partida_cod": "29"`) y `test_f050_partida_linea.py` (`== "29"`). Los demás son de F-054.
  `test_f050_modal_registro.py`, intacto.
- **Docs:** `ARCHITECTURE.md` punto 23 y `#regla-var`; `INTEGRACION.md` §5 (VAR con `partida_cod`).
  `INTEGRACION.md` no describe campo a campo la respuesta de `traer-sigrid`: lo de `no_traidas` no aplica.
- **Convenciones:** primera línea con ruta en los `.py` nuevos; sin `print`/`console`/`debugger` en lo
  añadido; sin secretos; todo lo pintado, escapado (`test_f054_r44_parte_y_obra_escapadas`).

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados, sin pipes): código 0, sin `[KO]`, «ENTORNO LISTO»;
  raíz 418 (+1 skipped), api 1502, front 527, transfer 1886 · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` · [x] rama `feature/F-054-sync-trae-porcentajes` (`git -C`) · [x]
  `current.md` coherente (relectura entera, ver «Rastro») · [x] history.
- **C3** [x] hexagonal (`codigos` en el port y en `PgObraRepository`; `partida_de_entrada`, pura, en
  `domain/obras.py`) · [x] primera línea · [x] sin debug ni secretos · [x] front sin negocio.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R43-R47 con tests (tabla abajo) · [x] sin red ni BBDD (`codigos` compila contra el ORM sin
  base; front con node y dobles) · [x] MANUAL: T18 pasos 2-4 (con 01/2026 y T26), T19 y T20, con comando.
- **C4 bis** [x] rigor declarado · [x] RED real de T24 (`52 failed, 4 passed`), T25 (`6 failed` y
  `31 failed`, con los `AssertionError`/`TypeError`) y T26 (`19 failed`, `ImportError`) · [x] cobertura
  `[OK]` 99,5 % (786/790; JS N/A por lenguaje) · [x] mutación Python: **recalculé** el alcance (25
  ficheros, 1727 líneas) y **287 mutantes** con `generar_mutantes`: coincide. Campaña no reejecutada:
  2676 s según el informe · [x] RM1: SHA `086983a`; desde él solo han cambiado tests del front,
  `progress/` y tasks, ningún `.py` de producción · [x] RM2: 287 × 9,3 s ≈ 2676 s. Los 9,3 s son
  tiempo de pared con 4 workers (≈ 37 s por mutante y worker, frente a bases de 42-83 s, con `-x`):
  coherente · [x] sin «CAMPAÑA NO VÁLIDA», «Sin veredicto» 0, línea base declarada · [x] RM3: ningún
  equivalente · [x] RM5 N/A: esta campaña no declara ningún equivalente (ni Python ni `app.js`) · [x]
  RM6 N/A: no se quitó ninguna guarda (`existen`→`codigos` es otra lectura con el mismo conjunto, y T26
  **añade** `if nodo_pv`) · [x] `app.js` manual: campañas 7 (90 mutantes, 85 muertos, 5 huecos) y 8
  (5/5), una fila por mutante con texto exacto y nº de fallos. **Reproducidas en copias `git archive`
  del SHA declarado** (mismos 5 ficheros de test): c7 `0fc94fb`, base `99 passed` (tabla 99), **E60**
  → `1 failed` (tabla 1), **E46** → `99 passed` (tabla: SUPERVIVIENTE, 0); c8 `4e5ac80`, base
  `103 passed` (tabla 103), **E6** → `1 failed` (tabla 1), **E46** → `1 failed` (tabla 1) · [x]
  «Evidencias» con los cuatro números · ningún N/A sin motivo.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T1-T17 y T21-T26 `[x]`, con commits `F-054 T24/T25/T26: …` · T18-T20 `[ ]` por ser
  MANUAL, legítimo · [x] árbol limpio · [x] `features.json` en `in_progress`.

## Rastro: relectura entera de `progress/current.md` (788 líneas)

Coherente en lo pedido: cabecera «en REVIEW 8» (l. 4); «Siguiente» (l. 74) y «Hoy» (l. 572) en
review 8; rangos **T1-T26, R1-R47, D1-D21** (l. 79-80, D20-D21 con sus citas); **T18**: paso 1 hecho,
con comando y resultado, y **pasos 2-4** con la ventana de T24 (01/2026), T25 y T26 (l. 136-157),
igual que en tasks.md; **T19** con comando (l. 158-170); **T20** con el orden, `git -C … azure-apps log`
y la nota para `azure-apps` (`partida_cod` VAR, motivos, `no_traidas`; l. 171-178); «`azure-apps`
pendiente: T20» (l. 35-36). **Ninguna incoherencia bloquea.** Lista completa de las menores:

- **O13** `current.md:116-120`: dice «no afectan a F-054 (ninguno de sus 266 mutantes)», y la campaña
  vigente es de 287. Propuesta: «(ninguno de sus mutantes: 266 entonces, 287 en `086983a`)».
- **O14** `progress/manual_F-054.md`: «Pasos 2 a 4 · pendientes (humano, sobre la ventana de T23)»
  debería decir «de T23-T26»; y le falta la primera línea `<!-- progress/manual_F-054.md -->` que
  llevan los demás ficheros de `progress/`.

## Observaciones de código y spec (no bloquean; para el humano o el próximo toque)

- **O11** (texto, para el humano) `porcentajes_existentes.py:93-95`: en «Sincronizar Sigrid»,
  `traducir` solo llama a `partida_var_de` con una línea cuyo código **es** el de la obra VAR. Por eso
  `OTRA_OBRA` (una ficha con el código VAR que no es la obra VAR, p. ej. de otra empresa) dice
  «partida VAR 29: la obra VAR no es la obra VAR VAR»; antes el `ide` las distinguía. Es lo que pide
  R46 al pie de la letra, y lo fija `test_f054_r46_var_de_otra_obra_*`. Si el humano lo quiere
  legible: `obra_cod` solo cuando difiera del de la VAR (o «VAR (ide N)»). Caso raro; en el preflight
  no pasa (usa `origen.codigo`).
- **O12** (spec) `tasks.md` l. 6 dice «**No se tocan** … `registro_pipeline.py`» y T25 dice «no se
  toca», pero T26 lo autoriza (y design §10, l. 209, dice «salvo T26»): añadir «(salvo los motivos de T26)».

## Cambios requeridos

Ninguno. Para cerrar faltan T18 (pasos 2-4) y T19, del humano, con resultado en
`progress/manual_F-054.md`, y T20 al desplegar. R37 queda sin cifra final hasta T19 (≤ 11,89 s).

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R27 | como en la review 7 (`test_f054_*` de los tres servicios) |
| R28, R39-R42 | `test_f054_traer_front.py` `r28_*`, `r39_*`-`r42_*` (en verde tras T24) |
| R43 | `r43_las_dos_tablas_*`, `r43_fuera_los_selectores_de_t23`, `r43_el_clic_en_la_flecha_*`, `r43_limpiar_*` (×3), `r43_escape_*` |
| R44 | `r44_agrupar_*`, `r44_el_recurso_distingue_*`, `r44_no_se_traen_*`, `r44_dos_iguales_*`, `r44_sin_no_traidas_*`, `r44_ordena_*`, `r44_la_columna_ordenada_*`, `r44_filtros_*`, `r44_cada_clave_*`, `r44_ordenar_texto_*`, `r44_el_filtro_de_recurso_*`, `r44_parte_y_obra_*` |
| R45 | front `r45_recurso_con_codigo_*`; api `test_f054_comparar` `r45_no_traidas_*`, `test_f054_rutas` |
| R46 | transfer `test_f054_traduccion` `r46_*` (6); api `test_f054_comparar` `r46_var_fuera_*`, `test_f054_aceptar` `r46_repositorio_codigos_*` (2) |
| R47 | transfer `test_f054_motivos_preflight` (13), `test_f039_preflight_var`, `test_f002_r16`, `test_f025_r9`; api `test_f054_partida_var` (6), `test_f039_r20`, `test_f050_r19` |
| R29 | `ARCHITECTURE.md` 23 y `#regla-var`, `INTEGRACION.md` §5; `azure-apps`, en T20 |
| R30, R37 | MANUAL T10 (hecha), T18, T19 |
| R31-R36, R38 | como en la review 7 (`test_f054_obra_cero`, `poner_a_cero`, `registro_cero`, `modal_cero`) |

## Automejora (propuesta, no aplicada; para `reviewer.md` y `arnes-base`)

El protocolo pide cazar «textos de motivo usados para decidir», pero no dice dónde mirar; aquí el
único lector que decide por texto ya existía (regex R20 de `pintarModalPreflight`). Propuesta: cuando
una feature cambie un texto de motivo, el reviewer hace `grep` de `exec(`/`match(`/`startsWith(`/
`includes(` sobre `motivo` en el front, y de `.motivo ==`/`in a.motivo` en los `.py`, y lo deja escrito.
