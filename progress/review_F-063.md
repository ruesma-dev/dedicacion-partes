<!-- progress/review_F-063.md -->
Revisión completa (pasada 1): `git diff dev...HEAD` (`9cde6b1...90c3d9a`)

# F-063 · Review 1 · **APROBADO** (APPROVED)

**Nivel de rigor:** `estandar`, declarado. Exige fase RED, cobertura de las
líneas cambiadas y mutación con los supervivientes analizados. `sdd: false`:
se valida contra los 4 `acceptance` (nota de cabecera de `CHECKPOINTS.md`).

## Alcance

- Producción: solo `services/dedicacion-front/static/js/app.js` (+60, nada
  borrado) y una frase del `README.md` del front. Test nuevo:
  `services/dedicacion-front/tests/test_f063_filtro_incidencia.py` (16).
- Ningún test existente cambia (`git diff dev...HEAD --diff-filter=M` no
  lista ningún `tests/`); api, transfer y CSS intactos.
- El diff de `app.js` no nombra motivos de conflicto (`grep
  pisado|sobrecarga|sin_partida|motivo` vacío); el test F-013 R4 pasa.

## Comprobaciones pedidas

- **Fichas** (acc. 1): `tiposIncidenciaDelMes` agrupa por `codigo` (Map),
  cuenta trabajadores (un `Set` por trabajador) y `tieneIncidencia` descarta
  las `quitada`; sin incidencias, o solo quitadas, ninguna ficha nueva.
- **Clic** (2) y **Y** (3): la condición entra en el mismo `filter` de
  `trabajadoresVisibles` que estado, buscador y columnas.
- **Dobles** (`CONVENTIONS.md` § Tests): `_trab`, `_linea`, `_inc` cotejados
  campo a campo con `TrabajadorOut`, `LineaOut` (sin `vinculados`, que
  `exclude_if` omite vacía) e `IncidenciaOut`; `resumen` = `ResumenOut`.
- **Front sin lógica de negocio**: filtro de pantalla; las funciones nuevas
  no leen `state` ni llaman a la api; `filtroIncidencia` solo vive en
  `renderCabecera`, `trabajadoresVisibles` y `moverMes` (test de límite).

**Decisiones del informe, contra la descripción.** (a) *Bajas sin carga no
cuentan*: la tabla nunca las enseña; contarlas haría que la ficha dijera 3 y
el clic enseñara 2. Mismo criterio que `trabajadoresVisibles` y el contador
de `renderTabla`. (b) *La activa sigue con 0*: solo con un filtro ya activo
cuyo tipo desaparece en la misma pantalla (cambiar de mes lo quita); sin
filtro activo el criterio 1 se cumple al pie de la letra, y es la conducta de
«0 falta» de las fichas de estado, el modelo que pide la descripción. (c)
*Orden por letra*: la descripción no fija orden. Ninguna la contradice.

## Mutación (campaña manual del JS)

`harness.mutacion` no muta JS y el diff no trae Python de producción: la
manual sustituye a la automática (fila por mutante, texto exacto, nº de
fallos, script).

- **RM1**: medida sobre `b982703`; `git diff --stat b982703 HEAD` solo trae
  rastro y `CONVENTIONS.md` (unión con dev): `app.js` y tests, los medidos.
- **Reproducción** (bloque del informe, desde el scratchpad, copias
  temporales): **M3, M14, M17, M21 y M25**. Base `16 passed`; M3 MUERTO (11),
  M14 (1), M17 (1), M21 (1), M25 SUPERVIVIENTE (0); mismos tests caídos que
  la tabla; 51,8 s; `git status` limpio después.
- **RM2**: 811,1 s / 26 ejecuciones, 1 worker ≈ 31 s; base 15,8 s
  (máquina cargada; 5,1 s en mi reproducción). Coherente.
- **RM3**: ningún muerto es equivalente (M21 deja de repintar, M14 cambia el
  orden de dos tipos de igual letra, M20 impide quitar…).
- **M25 equivalente: me convence.** Solo difiere si un trabajador llega sin
  la clave `incidencias` **y** hay filtro activo (en el conteo,
  `tieneIncidencia` solo se llama dentro de `(t.incidencias || []).forEach`).
  En el origen del dato: `TrabajadorOut.incidencias: list[...] = []`, `_Base`
  sin `exclude_*`, ninguna ruta con `response_model_exclude_*`, el proxy del
  front reenvía `respuesta.content` tal cual, y `state.trabajadores` solo se
  llena con `CuadranteOut.trabajadores` y `FilaOut.trabajador`; ningún
  `t.incidencias =` en `app.js`. Matarlo pediría un doble contrario a la
  forma real.
- **RM5** N/A por nivel `estandar` (basta la justificación escrita).
  **RM6**: no se quitó ninguna guarda.

## Checkpoints

- **C1** [x] `init.sh` exit 0 (Evidencias) · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` · [x] rama de la feature · [x]
  `current.md` con cabecera «En curso: F-063» y su MANUAL (ver O2) · [x]
  `done` con resumen en `history.md`.
- **C3** [x] hexagonal (solo front, sin capas nuevas) · [x] primera línea
  con ruta en el test · [x] sin `console.log`, TODOs, secretos ni
  dependencias · [x] las tres trampas: ni porcentajes, ni postventa, ni
  escrituras.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] 4 `acceptance` con tests trazables en verde (tabla) · [x] sin
  red ni BBDD (node sobre el código real, DOM de mentira) · [x] MANUAL en
  «⚠ Lo que espera al humano» con pasos exactos.
- **C4 bis** [x] rigor declarado · [x] fase RED con traza real (13 rojos; los
  2 verdes explicados y mordidos luego por M3/M4/M8) · [x] cobertura `N/A`
  con motivo impreso (sin Python de producción; el JS no tiene medidor, lo
  suple la campaña) · [x] mutación manual, justificada por el lenguaje · [x]
  muertos comprobados (5 filas) · [x] coste por mutante coherente · [x] base
  en verde, declarada y reproducida · [x] RM1 · [x] RM2 · RM5 N/A (nivel) ·
  [x] RM6 · [x] tabla reproducible · [x] superviviente analizado · [x]
  «Evidencias» con los cuatro números y 1 worker.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** `tasks.md` N/A (`sdd: false`; commits `F-063 T1..T4:`) · [x] sin
  temporales sin trackear · [x] `features.json` en `in_progress` (a `done`
  al cerrar).

## Cobertura de los acceptance

| Acceptance | Tests (`test_f063_…`) |
|---|---|
| 1 · fichas por tipo sin quitadas; ninguna sin incidencias | `r1_una_ficha…`, `r1_sin_incidencias…`, `r1_las_quitadas_solas…`, `r1_tipos_del_mes…`, `r1_misma_letra…` |
| 2 · clic filtra y marca; otro clic / «N trabajadores» quitan; otra sustituye | `r2_un_clic…`, `r2_una_quitada_no_filtra`, `r2_otro_clic…`, `r2_n_trabajadores…`, `r2_elegir_otra…`, `r2_activo_y_sin_trabajadores…`, `r2_cambiar_de_mes…` |
| 3 · Y con estado, buscador y columnas | `r3_se_combina_con_la_ficha_de_estado`, `…_con_el_buscador`, `…_con_los_filtros_de_columna` |
| 4 · sin red ni BBDD; `init.sh` verde | la suite; `init.sh` de esta review |

## Evidencias de esta review

`.arnes_cache/suite_*.ok` borrados y `bash harness/init.sh` tal cual: raíz
418 passed, 1 skipped · api 1308 · front 430 (16 de F-063) · transfer 1585
passed; `PUERTA COBERTURA: N/A (F-063 no cambia líneas Python de producción
frente a dev)`. Su único `[KO]` fue la puerta de tamaño **de este mismo
informe** en borrador (149 > 140); recortado, la segunda pasada (servicios
desde la caché de la primera, raíz 418 passed) sale sin `[KO]`, exit 0.

## Observaciones (no bloquean)

1. **O1 · La ficha activa a 0 va al final, no en su sitio por letra**
   (`app.js:574-576`, `tipos.push` tras el `sort`): con «A» activa a 0 y «B»,
   «P» presentes sale «B… P… A… 0». Cosmético y transitorio; empujar antes
   de ordenar lo arregla. Lo decide el humano; no hace falta para cerrar.
2. **O2 · `progress/current.md` arrastra secciones de features cerradas**
   (p. ej. «F-044 · implementer», líneas 45-175). Viene de `dev`, no lo
   introduce F-063: poda del líder al cerrar.
3. **O3 · El SHA del informe manual va corto** (`b982703`): inequívoco y
   verificado (RM1); en la próxima campaña manual, el completo.
4. **O4 · La regla «baja sin carga» (`!t.activo && !t.lineas.length`) está
   ya en tres sitios** (`trabajadoresVisibles`, `renderTabla`,
   `tiposIncidenciaDelMes`). Hoy coinciden; una función común sería lo
   limpio, fuera del alcance de F-063.

## Cambios requeridos

Ninguno.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 bis, campaña MANUAL: pedir el SHA completo medido,
  como en la automática (O3).
