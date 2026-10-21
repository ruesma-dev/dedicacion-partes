Revisión completa (pasada 1) · `git diff dev...HEAD`, HEAD `32d764a`, base `20a8e06`
<!-- progress/review_F-030.md -->
# F-030 · Review (pasada 1)

**Veredicto: RECHAZADO (CHANGES_REQUESTED).** Hay un defecto que llega a Sigrid
(obs. 1: R30 no se cumple de punta a punta). El resto está bien hecho y
verificado; tras corregir la obs. 1, la pasada 2 es incremental.

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura,
mutación con 0 supervivientes y MANUAL con su comando exacto y su resultado real.

## Lo que se ha ejecutado

- `bash harness/init.sh` tal cual, con `.arnes_cache/suite_*.ok` borrados:
  **ENTORNO LISTO**, ningún `[KO]`. Raíz 418 (+1 skipped), api 1083, front 350
  (node `passed`), transfer 1168. COBERTURA `[OK]` 99,5 % (634/637). TAMAÑO
  `[OK]`. Ruff: 293 `[AVISO]` frente a 277 en `dev` (obs. 4).
- **Mutación, recálculo puro** (`harness.alcance` + `generar_mutantes`): 23
  ficheros, **1487 líneas y 250 mutantes**, igual que el informe.
  - Campaña **no reejecutada**: 1888,2 s según el informe (> 60 s). Coste por
    mutante 7,55 s (× 1 worker).
  - RM2: media 7,6 s > 1/10 de las bases (33,5 y 24,9 s); 250 × 7,6 ≈ 1888.
  - RM1: SHA medido `8b17e85`; después solo cambian `progress/` y `tasks.md`.
  - Ni «⚠ CAMPAÑA NO VÁLIDA» ni base rota. RM3: ninguno de los 250 es
    equivalente. RM5: N/A (no hay equivalentes). RM6: ninguna guarda quitada.
- **RM4**, en una copia del scratchpad: `orm_models.py:253`
  `String(300)→String(301)` da 2 failed y `registro_pipeline.py:1099` `+=→-=`
  da 1 failed. Los muertos son reales.
- **Fusión de F-051** (`46cf116`): lo que se quita es refactor de F-030; los
  `test_f051_*` pasan. **Lista cerrada**: solo dobles con la marca, más la
  aserción autorizada de `test_f013_r3`.

## Checkpoints

| | Estado |
|---|---|
| C1 init.sh exit 0 · ficheros base | [x] · [x] |
| C2 una sola `in_progress` · rama | [x] · [x] |
| C2 `current.md` solo con la sesión activa | [ ] obs. 2: dato caducado en las líneas 47-49 |
| C2 cada `done` con su resumen en `history.md` | [x] F-030 no está `done` |
| C3 hexagonal | [x] `domain/incidencias.py` pura; el import de ORM en `traza_incidencias.py` tiene precedente (obs. 5) |
| C3 ruta en la primera línea · sin `print` de depuración · sin secretos · sin dependencias nuevas | [x] los `print` son del script CLI, que ya los usaba |
| C3 escala del % · postventa · solo escribe el transfer, con `synckey` | [x] `can = 0`; solo obra normal (R19); `porcentajes:inc:` |
| C3 reglas del dominio | [ ] obs. 1: `#regla-incidencia` («no se reescribe aunque cambien sus días») no se cumple |
| C3 bis | N/A: no toca `docs/referencia/` |
| C4 cada R con su test · sin red ni BBDD | [x] tabla abajo · [x] |
| C4 MANUAL en `current.md` con su comando exacto | [ ] obs. 2: comando abreviado y sin lo que queda sin probar |
| C4 bis nivel · RED · cobertura · mutación verificada | [x] · [x] trazas reales T2-T19 (T1 fija lo de hoy) · [x] · [x] |
| C4 bis muertos · coste · cabecera · RM1 · RM2 · RM5 · RM6 · manual · supervivientes | [x] recálculo + RM4 · [x] · [x] · [x] · [x] · N/A · [x] · N/A (automática) · [x] 0 |
| C4 bis «Evidencias» con los cuatro números y los workers | [x] |
| C4 ter | N/A: no hay `harness/rutas_sensibles.json` |
| C5 `tasks.md` | [x] T1-T19 y T21 con su commit `F-030 Tn`; T20 es MANUAL pendiente |
| C5 árbol limpio · `features.json` | [x] · [x] |

## Cobertura (requisito → test; detalle con `grep -n "def test_f030_rN"`)

| R | Test(s) |
|---|---|
| R1, R8-R13 | front `test_f030_celda_pct.py` (`r1_*`, `r8_r9_letras_abren_el_panel_…`, `r10`-`r13`) |
| R14-R16, R32 | front `test_f030_tabla_incidencias.py` |
| R2 | transfer `r2_preflight_…_igual_…`, `r2_ejecutar_…`; api `r2_r22_guardar_no_toca_…`, `r2_esquema_…` |
| R3-R7 | api `test_f030_catalogo.py` (`r7_sync_falla_entero_…`, `r7_el_cliente_lanza_ante_truncated`) |
| R17-R22 | api `test_f030_incidencias.py` (guardar, 404/409, 422, deshacer por tipo, copias, `r22_cuadrante_…`) |
| R23, R25, R31 | api `test_f030_registro.py`; transfer contrato `r31_*` |
| R24, R26-R30 | transfer `test_f030_reglas_incidencias.py` y `test_f030_pipeline_incidencias.py` (D3: días 31-31 y 1-31) |
| R33 | transfer `r33_cliente_*`, `r33_preflight_una_lectura_…`, `r33_lote_una_lectura_y_lo_mismo_que_suelto` |
| R34 | `test_f002` (ancla y `r34_p2_p3_p4_remiten_…`) |
| R35 | `r35_script_*`; la prueba real es T20, MANUAL |

## Puntos que el líder pidió mirar

- **Front sin lógica de negocio: cumple.** `app.js` detecta letras, filtra el
  catálogo, quita la línea recién añadida (R13) y pinta. Los días vacíos
  viajan `null` y los completa la api. Las incidencias van en
  `incidenciasEdicion`, fuera de `totalEdicion`.
- **Fuera de pisados, sobrecarga, sin partida y línea al 0 %: cumple.** Viajan
  aparte (D-c), `es_linea_mensual` exige `M*`; test `r28_…linea_al_cero`.
- **`synckey`, R27 y D3: correctos en el transfer.** R27 mira `CI%` en
  cualquier parte del mes (en pruebas, solo la `0404`); D3 sale por
  construcción. Pero la `{id}` no sobrevive a la api: obs. 1.
- **Sync de `auxhor`:** lee antes de cualquier upsert y falla entero ante error
  o `truncated`. **Lote igual a suelto:** sí, con una lectura por lote.
- **Deshacer:** despacha por tipo. **D-a…D-g:** justificadas.
- **Documentación:** `#regla-incidencia` e `INTEGRACION.md` bien; `azure-apps`
  es del líder.
- **T20:** listada con su comando exacto en `impl` §6 y en `tasks.md`. **Sin
  T20 no se despliega** (design §12). Mientras no se haga, queda sin probar:
  - la SQL real de `incidencias_del_mes` (`JOIN con c ON c.ide = m.ide`,
    `fec`, `LIKE 'CI%'`);
  - la inserción real del par `CI*`/`CIZ` (`can = 0`, `pre` de `reshor`), con
    su cuenta analítica;
  - la relectura por `synckey` y que `limpiar` lo borre;
  - el coste de la lectura nueva.

  T20 tampoco toca la SQL del sync de `auxhor`.

## Cambios requeridos

1. **[BLOQUEANTE] R30 falla de punta a punta: cambiar los días de una
   incidencia registrada vuelve a escribir en Sigrid.**
   - **Causa.** `PgIncidenciaRepository.reemplazar` (`api/.../repositories.py:585-606`)
     solo conserva `id` y traza si coinciden obra, código, desde y hasta. Si
     cambian los días, crea otra fila con `id` nuevo y el transfer recibe
     `synckey`s nuevas.
   - **Reproducido** con `decidir_incidencia` y `deduplicar` reales: la 7,
     registrada del 5 al 9, llega como la 8.
     - Del 6 al 9: `ini escribir 20260706`, `fin omitir`. Quedan dos `CIV`
       abiertos y un `CIZ`.
     - Del 12 al 14: escribe el par entero, y el del 5 al 9 sigue en Sigrid.
   - **Por qué no lo caza ningún test:** `test_f030_r30_*` del transfer dan por
     hecho que la 7 sobrevive, y no hay test api→transfer. Deshacer un
     `INCIDENCIAS` que repone una registrada la recrea igual, sin traza.
   - **Decisión del humano** (hueco de la spec):
     - a) conservar `id` y traza aunque cambien los días (el PUT trae `id`);
     - b) 422 al cambiar o quitar una ya registrada, hasta F-033;
     - c) otra.
   - **Con cualquiera:** test `test_f030_r30_*` de punta a punta en la api, y
     nueva campaña si cambia código del alcance (RM1).
2. **`progress/current.md`:**
   - Las líneas 47-49 dicen que `dedicacion.md` «se actualiza en T19»: es del
     líder al desplegar.
   - En el MANUAL de T20, poner el comando exacto de `impl` §6 (con
     `--ano`/`--mes`) y lo que queda sin probar (sección anterior).

## Observaciones no bloqueantes (recógelas o di por qué no)

3. `lecturas_lote.py:351`: 108 caracteres con 25 espacios en medio, restos de
   una unión de líneas.
4. Ruff +16, todos en `api/tests/test_f030_incidencias.py` (F811 ×6, RUF100 ×5,
   I001, RUF059, FURB157). «293, deuda previa» no es exacto.
5. `traza_incidencias.py` importa ORM desde `application/` (precedente:
   `registro_sigrid.py`). Aceptado; que conste.
6. `reglas_incidencias.py:147`: la rama `igual.synckey == synckey_incidencia(…)`
   no se alcanza (`por_synckey` la habría devuelto antes). Simplificarla.
7. Preflight: el parte de la incidencia entra antes de R27 («se creará» con el par omitido).

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 (`critico`): si la idempotencia usa un `id` de otro
  servicio, test de que sobrevive a la edición allí (aquí ambos lados, verdes).
