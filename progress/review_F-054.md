<!-- progress/review_F-054.md -->
Revisión incremental desde 398312c (pasada 9; la 8 aprobó `f9be667`, más `398312c` con O12-O14), HEAD `276593b`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 9 (merge de `dev` y O11)

**Veredicto: APROBADO (APPROVED).** El merge de `dev` trae exactamente los dos hotfixes y no toca nada
de F-054; O11 solo cambia texto y ningún consumidor decide por él. Sin bloqueos; una observación (O15).

**Rigor:** `critico` (`features.json`): RED, cobertura, mutación con 0 supervivientes, RM5 y MANUAL.
Anteriores: 8, 7, 6 y 2 APROBADAS; 5, 4 y 3 CAMBIOS solo por `current.md`; 1 RECHAZADA.

## Delta revisado (`git diff 398312c..HEAD`, 16 ficheros)

- **Merge `a2ad52a`.** Lo que añade en `services/` es exactamente `29b969b` (`tipos_excluidos: []`,
  comentario de `config.yaml` y `test_f044_r1_config_versionada`) más `23160d0` (`PropuestaSubfilaOut`,
  `PropuestasOut.subfilas = []`, `response_model_exclude_unset=True` en `GET …/propuestas` y
  `test_hotfix_propuestas_subfilas.py`). En `schemas.py`/`routes.py` las líneas de F-054 (124 y 58 en
  alcance) siguen intactas: el delta solo añade la clase y el parámetro de la ruta. `exclude_unset`
  actúa sobre los modelos anidados, pero `PropuestaLineaOut` y `PendienteOut` no tienen campos con
  defecto y F-054 no toca esa ruta: la respuesta no pierde claves (los dos tests del hotfix lo fijan).
  `specs/F-044` (D1b, R3), `ARCHITECTURE.md`, `features.json` (F-069, F-070) y `BACKLOG.md` vienen de dev.
- **`current.md` tras el conflicto.** Comparé los dos lados contra la base del merge (`1ed18be`): los
  dos párrafos HOTFIX de dev están completos (l. 39-57), más una línea (l. 59) que dice que se trajeron
  a la rama; el resto del lado F-054 sigue. No se pierde nada.
- **O11 (`353d290`).** `_nombre_otra_obra` (`universo_var.py:134-143`) es puro texto: la decisión sigue
  siendo `obra_ide != catalogo.obra.ide` (l. 123), igual que antes. Sin código, el `ide` (como antes);
  con el código de la VAR, sin contar espacios, «COD (ide N)» (`OBRA_HOMONIMA_VAR`); si no, el código.
  `test_f054_o11_otra_obra_con_el_codigo_var_lleva_su_ide` cubre los seis casos (igual, espacios en
  cualquiera de los dos lados, distinto, `None`, `""`), y `test_f054_r46_var_de_otra_obra_*` cambia
  solo el esperado (es de F-054). RED real en `impl_F-054.md` (`2 failed`, con el texto esperado).
- **Consumidores del texto.** Grep de `MOTIVO_VAR_OTRA_OBRA`, `OBRA_HOMONIMA_VAR`, «no es la obra» y
  «(ide » en los tres servicios, sin tests: solo la definición y el `format`. Grep de comparaciones
  (`motivo ==`/`!=`/`in`, `startswith`, `includes`, `indexOf`, `match`, `exec` sobre `motivo`): ninguna
  con este texto. El regex R20 de `pintarModalPreflight` no casa con «partida VAR …» (ver review 8).
- **Convenciones:** primera línea con ruta; sin `print` ni secretos. `ruff` sobre lo cambiado: solo
  `I001` en `schemas.py:3`, que es el bloque de imports y no cambia en el delta (deuda previa).
- **`276593b`**: solo la primera línea de `current.md`, con review 9 lanzada.

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados, sin pipes): código 0, sin `[KO]`, «ENTORNO LISTO»;
  raíz 418 (+1 skipped), api 1504 (+2 del hotfix), front 527, transfer 1887 (+1 de O11) · [x] ficheros
  del arnés.
- **C2** [x] una sola `in_progress` (F-054) · [x] rama `feature/F-054-sync-trae-porcentajes` · [x]
  `current.md` coherente (cabecera con review 9; ver O15) · [x] history.
- **C3** [x] hexagonal (`_nombre_otra_obra` en `application/services`, pura) · [x] primera línea · [x]
  sin debug ni secretos · [x] front sin negocio (el delta no toca el front).
- **C3 bis** N/A: el delta no toca `docs/referencia/`.
- **C4** [x] requisitos con tests (tabla abajo) · [x] sin red ni BBDD (los tests nuevos usan el
  `ClienteVar` de prueba y la fixture `api` con dobles) · [x] MANUAL: T18 pasos 2-4, T19 y T20 siguen
  con su comando en `current.md`.
- **C4 bis** [x] rigor declarado · [x] RED real de O11 · [x] cobertura `[OK]` 99,5 % (793/797) · [x]
  mutación: **recalculé** con `alcance_de_feature("F-054")` + `generar_mutantes`: base `d317edb`, 25
  ficheros, **1744 líneas, 289 mutantes** (5 en `universo_var.py`): coincide con el informe. Campaña no
  reejecutada: 2936 s según el informe · [x] RM1: SHA medido `353d290`; después solo `e37cea5` y
  `276593b`, que tocan `progress/` y `tasks.md`, ningún fichero del alcance · [x] RM2: 2936,3 / 289 =
  10,2 s de pared con 4 workers (≈ 41 s por mutante y worker frente a bases de 37-90 s, con `-x`):
  coherente, como en la 8 · [x] sin «CAMPAÑA NO VÁLIDA», «Sin veredicto» 0, línea base declarada ·
  [x] RM3: ningún equivalente · [x] RM5 N/A: la campaña no declara equivalentes · [x] RM6 N/A: no se
  quita ninguna guarda (O11 añade ramas) · [x] `app.js` sin cambios en el delta: las campañas manuales
  7-8 de la review 8 siguen valiendo · [x] «Evidencias» con los cuatro números (fila Mutación al día).
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T1-T17 y T21-T26 `[x]`; O11 anotada en T26 y commits `F-054 O11: …` · T18-T20 `[ ]` por
  ser MANUAL, legítimo · [x] árbol limpio antes del informe · [x] `features.json` en `in_progress`.

## Rastro (`progress/current.md`, 810 líneas, relectura de los sitios de estado)

Cabecera (l. 4) con merge, O11 y review 9; l. 142 con O11-O14 recogidas y el SHA; hotfixes en l.
39-59; MANUAL pendientes con comando (l. 144 y ss.). Una incoherencia menor, no bloquea:

- **O15** `current.md:96` («**Siguiente:** F-054, review 8 APROBADA…»), l. 99 (título «review 8
  APROBADA») y l. 594 («**Hoy (2026-11-03):** … review 8 APROBADA») no nombran el merge, O11 ni la
  review 9. Lo pendiente que dicen (T18 pasos 2-4, T19, T20) sigue siendo cierto. Propuesta al
  actualizar tras esta review: «review 9 APROBADA (O11 y `dev` traído, 2026-11-04)» en los tres.
  Además, en l. 4 el «:» de «review 9 de O11 lanzada:» cuelga ahora la frase de T18 paso 2 de la
  review 9; mejor «…lanzada. Origen de la segunda enmienda: al probar…».

## Cambios requeridos

Ninguno. Para cerrar faltan T18 (pasos 2-4) y T19, del humano, con resultado en
`progress/manual_F-054.md`, y T20 al desplegar (el despliegue de la api arrastrará ya los dos
hotfixes). R37 sin cifra final hasta T19 (≤ 11,89 s).

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R27, R31-R36, R38 | como en la review 7 (`test_f054_*` de los tres servicios) |
| R28, R39-R42 | `test_f054_traer_front.py` `r28_*`, `r39_*`-`r42_*` |
| R43-R45 | como en la review 8 (`test_f054_traer_front.py` `r43_*`-`r45_*`; api `test_f054_comparar`, `test_f054_rutas`) |
| R46 (+O11) | transfer `test_f054_traduccion` `r46_*` y `o11_otra_obra_con_el_codigo_var_lleva_su_ide`; api `test_f054_comparar` `r46_*`, `test_f054_aceptar` `r46_*` |
| R47 | transfer `test_f054_motivos_preflight`, `test_f039_preflight_var`, `test_f002_r16`, `test_f025_r9`; api `test_f054_partida_var`, `test_f039_r20`, `test_f050_r19` |
| R29 | `ARCHITECTURE.md` 23 y `#regla-var`, `INTEGRACION.md` §5; `azure-apps`, en T20 |
| R30, R37 | MANUAL T10 (hecha), T18, T19 |
| Hotfixes de dev | `test_f044_r1_config_versionada`, `test_hotfix_propuestas_subfilas` (2) |

## Automejora (propuesta, no aplicada; para `reviewer.md` y `arnes-base`)

Cuando el delta incremental es un merge de `dev`, el protocolo no dice cómo comprobarlo. Propuesta:
«comparar `git diff <aprobado> <merge> -- services/` con la suma de los commits de dev entrados, y los
ficheros en conflicto contra la base del merge (`git merge-base`) por los dos lados». Es lo que se hizo
aquí y cuesta dos comandos.
