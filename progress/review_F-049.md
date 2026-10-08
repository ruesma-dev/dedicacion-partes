Revisión completa (pasada 1) · HEAD `5d6b267` (`git diff dev...HEAD`, base `2ebc061`)

# F-049 · Review — Los avisos del modal de registro rotulados por tipo

**Veredicto: CAMBIOS PEDIDOS** (CHANGES_REQUESTED). Un único `[ ]`, de papeleo:
la tabla de la campaña manual sustitutiva no trae el **nº de fallos** por
mutante (C4 bis). El código, los tests y la MANUAL están bien; la próxima
pasada será incremental y solo mirará eso y las observaciones.

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
tests trazables, fase RED, cobertura (o N/A con motivo impreso) y campaña de
mutación con supervivientes analizados. `sdd: false`: se valida contra los 5
`acceptance` y el plan aprobado (descripción de la feature y `current.md`).

## Lo que se ejecutó (resultado real)

- `bash harness/init.sh`, tal cual, desde la copia aparte: «ENTORNO LISTO», sin
  `[KO]`; raíz `418 passed, 1 skipped`; front `118 passed` (sin caché, `.venv`
  enlazado al de la principal pero con el `app.js` de la copia); api y transfer
  por caché (no se tocan); `PUERTA COBERTURA: N/A` con motivo impreso.
- `harness.alcance.alcance_de_feature('F-049')`: alcance **vacío**; el diff sin
  filtrar es `app.js` (52 líneas), el test nuevo y papeleo: cero por lenguaje.
- **Campaña manual reejecutada entera**, con el script del informe, sobre una
  copia en mi scratchpad (no se tocó el árbol) y **sin `-x`** para contar
  fallos: 33/33 aplican (ningún `NO_APLICA`), **33 MUERTOS**, 3 min 29 s. Así
  quedan reproducidas al pie de la letra todas las filas, no solo dos. Números
  de fallos en «Cambios requeridos».
- El `pintarModalPreflight({...})` de la MANUAL, extraído de `impl_F-049.md` y
  ejecutado en node con las funciones REALES de `app.js`: salen las tres
  casillas exactamente como dice `current.md` paso 5 (Sin partida 5 %;
  Sobrecarga «ya tiene 95% (MADM 95%), se añade 10% y sumaría 105%, un 5%»;
  Pisar «línea 8001 (MADM 40%, fec 20260930) y se escribe 60%»), con las
  `value` = claves del snippet.

## Lo que pidió el líder, contrastado con el código

1. **Campos que usa el rotulado = los que manda el transfer.** `Conflicto`
   (`dedicacion-transfer/domain/models/registro_models.py:193-237`) tiene
   `motivo` (defecto `"pisado"`), `nuevas`, `lineas`, `contexto`,
   `suma_existente`, `suma_total`, `exceso`; se publica con `asdict`
   (`interface_adapters/api/app.py:151`), que **no** serializa la propiedad
   `nueva_can` (causa del 0 % confirmada). `nuevas` sale de `_nueva()`
   (`registro_pipeline.py:99-107`, `can` sobre 1); `lineas`/`contexto` son
   `LineaSigrid` con `ide`, `hora_codigo`, `can`, `fecha_int`
   (`registro_models.py:130-141`). Los tres sitios que construyen conflictos
   (`registro_pipeline.py:454`, `:512`, `:546`) rellenan lo que el front lee
   (sobrecarga: `contexto=cap.contadas` y las tres sumas redondeadas). La api
   reenvía tal cual: `registro_sigrid.py:129-131` (`{"obra": …, **r}`) y la
   ruta `routes.py:307-319` devuelve el dict sin `response_model`. Escala:
   todo sobre 1 → `× 100` antes de `fmtPct`, correcto (trampa de C3 revisada).
2. **Mismas claves a ejecutar.** La casilla sigue siendo
   `class="chk-pisar" value="${escapeHtml(c.clave)}"` y `registroEjecutar`
   (`app.js:1809-1831`) no cambia en el diff; lo fijan
   `test_f049_r3_las_casillas_llevan_la_clave_de_cada_conflicto` y
   `…_ejecutar_manda_las_mismas_claves` (mutantes M28, M32, M33).
3. **Sin lógica de negocio en el front.** `pctNuevas` replica para mostrar la
   suma que el transfer ya hace en `nueva_can`; no compara con la jornada, no
   filtra ni decide qué se confirma (`test_f049_r3_el_rotulo_no_decide_nada`).
   Dentro del plan aprobado («% nuevo de `nuevas`»). El texto del «sin partida»
   casa con `AVISO_SIN_PARTIDA` del transfer (`reglas_porcentajes.py:313`).
4. **Ningún test anterior modificado**: el diff de `tests/` es solo el fichero
   nuevo `test_f049_avisos_registro.py` (290 líneas).
5. **MANUAL seguible**: front de la copia aparte sin `.env` va a la api en
   `127.0.0.1:8090` por defecto (`config/settings.py`); `app.js` se carga como
   script clásico (`templates/index.html:104`), así que `pintarModalPreflight`,
   `state`, `MESES` y `registro` son globales en la consola; el botón «⇪
   Sigrid» de fila existe (`app.js:892`). Ver O2 y O3.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base presentes.
**C2** [x] una `in_progress` · [x] rama `feature/F-049-…` · [x] `current.md`
abre con F-049, estado al día · [x] `done` con resumen en `history.md`.
**C3** [x] hexagonal: solo front, sin lógica de negocio · [x] primera línea
con ruta (`app.js`, test, informes) · [x] sin `console.log`/`print`/TODO,
sin secretos, sin dependencias nuevas · [x] tres trampas: escala sobre 1 bien
convertida; postventa y escritura en Sigrid no se tocan.
**C3 bis** N/A: no toca `docs/referencia/`. **C4** [x] cada `acceptance` con test trazable y en verde (tabla abajo) ·
[x] sin red ni BBDD (node local, sin `fetch`) · [x] MANUAL en `current.md`
con comandos exactos, resultado _pendiente_.
**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] Fase RED: salida real del fallo (el modal viejo pinta tres «Pisar … 0%»)
  y `16 failed, 1 passed` antes del código; el que pasaba fija lo invariante.
- [x] Cobertura: `N/A` con motivo impreso por init.sh (cambio solo en JS).
- N/A `mutacion_F-049.md` de la herramienta, regla de 60 s, coste por mutante,
  cabecera «CAMPAÑA NO VÁLIDA», RM1, RM2: `harness.mutacion` solo muta Python
  y el alcance recalculado es vacío; los sustituye la campaña manual,
  reejecutada entera por mí (arriba).
- RM3 revisado: ningún mutante equivalente salió muerto (M01: motivo vacío
  pasa a «Confirmar», cambio observable; el resto alteran texto visible).
- N/A RM5: rigor `estandar`. N/A RM6: no se quitó ninguna guarda.
- [ ] **Campaña manual sustitutiva**: hay fila por mutante con `fichero:línea`
  (comprobadas 17 líneas contra `app.js`, correctas) y el texto exacto
  canónico en la lista `M` del script (reproducible: lo reproduje), pero **la
  tabla no trae el nº de fallos** de cada mutante, que C4 bis exige
  expresamente. Ya se pidió en F-047 (O1) y F-042 lo traía («Fallos (sin
  `-x`)»). → Cambio 1.
- [x] Supervivientes analizados: M19 de la primera pasada, hueco real, cerrado
  con test en T2; ninguno `PENDIENTE`.
- [x] «Evidencias» con tests, cobertura, mutantes/supervivientes y tiempo de
  suite. Workers: no declarado, pero el script es un bucle en serie (W = 1
  evidente en el código) → O1.
**C4 ter** N/A: no hay `harness/rutas_sensibles.json`. **C5** N/A `tasks.md` (`sdd: false`); commits `F-049 Tn:` / `F-049:` ·
[x] árbol limpio (`.coverage`/`coverage.json` ignorados) · [x] `features.json`
en `in_progress`, coherente.

## Cobertura acceptance → tests (`services/dedicacion-front/tests/test_f049_avisos_registro.py`)

| Acceptance | Tests |
|---|---|
| 1 · rótulo por `motivo` | `r1_sin_partida_…`, `r1_sobrecarga_ensena_…`, `r1_pisado_ensena_…`, `r1_motivo_vacio_es_pisado[,None]`, `r1_motivo_desconocido_…`, `r1_cada_tipo_con_su_texto_…`, `r3_el_modal_pinta_el_rotulo_por_tipo` |
| 2 · % de `nuevas`; sobrecarga con existente, total, exceso | `r2_el_porcentaje_sale_de_nuevas_no_cero`, `r2_decimales_y_sin_nuevas`, `r2_el_front_no_lee_nueva_can`, `r1_sobrecarga_…`, `r2_sobrecarga_sin_contexto_…` |
| 3 · mismas claves a ejecutar | `r3_las_casillas_llevan_la_clave_…`, `r3_ejecutar_manda_las_mismas_claves`, `r3_el_rotulo_se_escapa`, `r3_el_rotulo_no_decide_nada` |
| 4 · test en node + prueba humana | 18 tests en node v24 (0 skipped); MANUAL pendiente en `current.md` |
| 5 · review + init.sh | este informe; init.sh en verde |

## Cambios requeridos

1. `progress/mutacion_manual_F-049.md`, tabla de §2: añadir la columna
   «Fallos (sin `-x`)» como en F-042. Valores de mi reejecución (script del
   informe sin `-x`, 18 tests): M01 2, M02 2, M03 11, M04 4, M05 1, M06 1,
   M07 1, M08 9, M09 9, M10 9, M11 1, M12 1, M13 4, M14 3, M15 3, M16 1,
   M17 1, M18 2, M19 1, M20 2, M21–M25 1, M26 3, M27–M31 1, M32 3, M33 1.
   Que el implementer los mida (script sin `-x`) y diga si coinciden; y que el
   método aclare que «Mutación» resume y el texto exacto es el de la lista `M`.

## Observaciones (recoger en esta misma vuelta, no dejar en «anotado»)

- **O1** `impl_F-049.md` «Evidencias»: declarar «campaña en serie, 1 worker»
  y su tiempo total (el C4 bis lo pide para el coste por mutante).
- **O2** MANUAL de `current.md`: (a) precondición del paso 4 —la base local
  `dedicacion` con septiembre 2026 y GONZALEZ PANIAGUA asignado—; si no está,
  vale solo el paso 5; (b) en el paso 1, «si `modo_pruebas` no es True, PARAR
  y no seguir».
- **O3** Paso 5: Chrome bloquea el primer pegado en consola hasta teclear
  `allow pasting`; avisarlo para que no parezca un fallo.
- **O4** (líder/humano, fuera del plan) el toast de `registroEjecutar` sigue
  diciendo «(repite y marca pisar)» para todo aviso: llevarlo a F-051 o aparte.
