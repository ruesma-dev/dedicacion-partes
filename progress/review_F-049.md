Revisión incremental desde 5d6b267 (pasada 2) · HEAD `48ca3fa` — la pasada 1 (completa, `git diff dev...5d6b267`, base `2ebc061`) sigue debajo, resumida

# F-049 · Review — Los avisos del modal de registro rotulados por tipo

**Veredicto vigente (pasada 2): APROBADO** (APPROVED). Pasada 1: CAMBIOS
PEDIDOS por un único `[ ]` de papeleo (nº de fallos por mutante en la tabla
manual), ya recogido. Detalle de la pasada 2 al final.

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
tests trazables, fase RED, cobertura (o N/A con motivo impreso) y campaña de
mutación con supervivientes analizados. `sdd: false`: se valida contra los 5
`acceptance` y el plan aprobado (descripción de la feature y `current.md`).

## Pasada 1 · lo que se ejecutó (resultado real)

- `bash harness/init.sh` desde la copia aparte: «ENTORNO LISTO», sin `[KO]`;
  raíz `418 passed, 1 skipped`; front `118 passed` (sin caché);
  `PUERTA COBERTURA: N/A` con motivo impreso.
- `harness.alcance.alcance_de_feature('F-049')`: alcance **vacío**; el diff es
  `app.js` (52 líneas), el test nuevo y papeleo: cero por lenguaje.
- **Campaña manual reejecutada entera** con el script del informe, en una
  copia en mi scratchpad y **sin `-x`**: 33/33 aplican, **33 MUERTOS**,
  3 min 29 s. Todas las filas reproducidas, no solo dos.
- El `pintarModalPreflight({...})` de la MANUAL, ejecutado en node con las
  funciones reales de `app.js`: salen las tres casillas como dice `current.md`
  paso 5, con las `value` = claves del snippet.

## Pasada 1 · lo que pidió el líder, contrastado con el código

1. **Campos = los que manda el transfer.** `Conflicto`
   (`registro_models.py:193-237`) lleva `motivo` (defecto `"pisado"`),
   `nuevas`, `lineas`, `contexto` y las tres sumas; `asdict` (`app.py:151`) no
   serializa la propiedad `nueva_can` (causa del 0 % confirmada). Los tres
   constructores (`registro_pipeline.py:454`, `:512`, `:546`) rellenan lo que
   el front lee; la api reenvía tal cual (`registro_sigrid.py:129-131`,
   `routes.py:307-319`). Escala sobre 1 → `× 100` antes de `fmtPct`: correcto.
2. **Mismas claves a ejecutar.** La casilla sigue con `value=c.clave` y
   `registroEjecutar` (`app.js:1809-1831`) no cambia; lo fijan dos tests r3
   (mutantes M28, M32, M33).
3. **Sin lógica de negocio en el front.** `pctNuevas` solo suma para mostrar;
   no compara, no filtra, no decide (`test_f049_r3_el_rotulo_no_decide_nada`).
   El texto «sin partida» casa con `AVISO_SIN_PARTIDA` (`reglas_porcentajes.py:313`).
4. **Ningún test anterior modificado**: en `tests/` solo el fichero nuevo.
5. **MANUAL seguible** (front sin `.env` → api `127.0.0.1:8090`; `app.js`
   script clásico, funciones globales en consola). Ver O2 y O3.

## Pasada 1 · checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base. **C2** [x] una `in_progress` ·
[x] rama `feature/F-049-…` · [x] `current.md` abre con F-049 · [x] `done` con
resumen en `history.md`. **C3** [x] solo front, sin lógica de negocio · [x]
primera línea con ruta · [x] sin `console.log`/`print`/TODO, sin secretos ni
dependencias · [x] trampas: escala sobre 1; postventa y Sigrid intactos.
**C3 bis** N/A: no toca `docs/referencia/`. **C4** [x] cada `acceptance` con
test en verde · [x] sin red ni BBDD · [x] MANUAL con comandos, _pendiente_.
**C4 bis** [x] `rigor: estandar` declarado · [x] fase RED real (`16 failed,
1 passed` antes del código) · [x] cobertura N/A con motivo impreso (solo JS) ·
N/A `mutacion_F-049.md`, regla de 60 s, cabecera «NO VÁLIDA», RM1, RM2:
`harness.mutacion` solo muta Python y el alcance es vacío; los sustituye la
campaña manual, reejecutada por mí · RM3 revisado: ningún equivalente muerto ·
N/A RM5 (rigor `estandar`), N/A RM6 (ninguna guarda quitada) · **[ ] campaña
manual: sin nº de fallos por mutante** → Cambio 1 · [x] supervivientes: M19,
cerrado con test en T2 · [x] «Evidencias» (workers no declarados → O1).
**C4 ter** N/A: no hay `harness/rutas_sensibles.json`. **C5** N/A `tasks.md`
(`sdd: false`); commits `F-049 Tn:`/`F-049:` · [x] árbol limpio · [x]
`features.json` coherente.

## Cobertura acceptance → tests (`services/dedicacion-front/tests/test_f049_avisos_registro.py`)

| Acceptance | Tests |
|---|---|
| 1 · rótulo por `motivo` | `r1_sin_partida_…`, `r1_sobrecarga_ensena_…`, `r1_pisado_ensena_…`, `r1_motivo_vacio_es_pisado[,None]`, `r1_motivo_desconocido_…`, `r1_cada_tipo_con_su_texto_…`, `r3_el_modal_pinta_el_rotulo_por_tipo` |
| 2 · % de `nuevas`; sobrecarga con existente, total, exceso | `r2_el_porcentaje_sale_de_nuevas_no_cero`, `r2_decimales_y_sin_nuevas`, `r2_el_front_no_lee_nueva_can`, `r1_sobrecarga_…`, `r2_sobrecarga_sin_contexto_…` |
| 3 · mismas claves a ejecutar | `r3_las_casillas_llevan_la_clave_…`, `r3_ejecutar_manda_las_mismas_claves`, `r3_el_rotulo_se_escapa`, `r3_el_rotulo_no_decide_nada` |
| 4 · test en node + prueba humana | 18 tests en node v24 (0 skipped); MANUAL pendiente en `current.md` |
| 5 · review + init.sh | este informe; init.sh en verde |

## Pasada 1 · cambios requeridos y observaciones

1. `mutacion_manual_F-049.md` §2: columna «Fallos (sin `-x`)» con mis valores
   (M01 2, M02 2, M03 11, M04 4, M05–M07 1, M08–M10 9, M11–M12 1, M13 4,
   M14–M15 3, M16–M17 1, M18 2, M19 1, M20 2, M21–M25 1, M26 3, M27–M31 1,
   M32 3, M33 1), medidos por el implementer; y aclarar que «Mutación» resume.
- **O1** `impl_F-049.md`: «campaña en serie, 1 worker» y su tiempo total.
- **O2** MANUAL: (a) precondición del paso 4 (base local con septiembre 2026 y
  GONZALEZ PANIAGUA); (b) paso 1: si `modo_pruebas` no es True, PARAR.
- **O3** Paso 5: avisar del `allow pasting` de Chrome.
- **O4** (fuera del plan) el toast de `registroEjecutar` dice «(repite y marca
  pisar)» para todo aviso: a F-048 o aparte.

## Pasada 2 · revisión incremental `5d6b267..48ca3fa`

**Alcance del delta** (`git diff 5d6b267 --stat`): `BACKLOG.md`,
`harness/features.json`, `progress/current.md`, `progress/impl_F-049.md`,
`progress/mutacion_manual_F-049.md` y este informe. **Cero cambios en código
y tests** (ni `app.js` ni `tests/`): lo aprobado en la pasada 1 sigue en pie y
la campaña manual sigue midiendo el mismo `app.js`. `CHECKPOINTS.md` no cambia.

**Ejecutado:** `bash harness/init.sh`, tal cual y solo, desde la copia aparte:
**«ENTORNO LISTO»**, sin `[KO]`; raíz `418 passed, 1 skipped` (99 s); api,
front y transfer en verde por caché (árbol de servicios sin cambios desde el
último verde, coherente con un delta solo de papeleo); `PUERTA COBERTURA: N/A`
con motivo; `PUERTA TAMAÑO` dentro de topes. `git status` limpio.

**Cambio 1 — recogido [x].** La tabla de §2 trae «Fallos (sin `-x`)» en los
33 mutantes y los comparé fila a fila con mi reejecución de la pasada 1:
**33/33 idénticos**. El método aclara que «Mutación» resume y que el texto
exacto es el de la lista `M`. La medida del implementer es independiente de
la mía: declara 299 s en serie sobre un `git archive` de `12627f7`, y la mía
fueron 209 s; mismos fallos con tiempos distintos.

**Observaciones:** **O1** [x] «Evidencias» declara «campaña en serie,
1 worker», 299 s sin `-x`, y que la pasada con `-x` no se cronometró. **O2**
[x] paso 1 «Si no es True, PARAR y no seguir»; paso 4 con la precondición de
la base local y «si no, vale solo el paso 5». **O3** [x] paso 5 avisa del
`allow pasting`. **O4** [x] recogido en la descripción de F-048
(`features.json` y `BACKLOG.md` regenerado, `BACKLOG.md al día` en init.sh).

**Checkpoints que cambian:** C4 bis «campaña manual sustitutiva» pasa a
**[x]** (fila por mutante, `fichero:línea`, texto exacto en la lista `M`,
resultado y nº de fallos; reproducidas las 33). C2 [x]: `current.md` sigue
abriendo con F-049 y su estado dice «Review 2 lanzada», al día. El resto, sin
cambios respecto de la pasada 1.

**Nota menor (no bloquea, no vuelve como bloqueo):** en `impl_F-049.md` y en
el método de `mutacion_manual_F-049.md`, «medido/medida en la review 1» puede
leerse como medido por el reviewer. Si se toca el papeleo al cerrar, mejor
«medido por el implementer en la vuelta de la review 1».

**Pendiente para cerrar (no es de esta review):** la MANUAL del humano en
`current.md` (resultado _pendiente_) y el paso a `done` con `history.md`.
