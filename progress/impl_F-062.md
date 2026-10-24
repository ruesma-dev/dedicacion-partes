<!-- progress/impl_F-062.md -->
# Informe del implementer · F-062 (rachas de incidencia como Administración)

`sdd: true`, rigor **crítico**. Rama `feature/F-062-rachas-incidencias`
(copia principal). Spec `specs/F-062-rachas-incidencias/` (R1-R31, D1-D18).
Hechas T1-T18 y T5c, un commit por tarea; **T19 y T20 son MANUAL del humano**
(preparadas, sin ejecutar); T21 es del líder. Nadie escribió ni leyó en
Sigrid: todo es con dobles, sin red ni BBDD. Decisiones tarea a tarea, con
su porqué: `progress/current.md` (sección «F-062 · implementación»).

## Qué cambió

| Tarea | Commit | Qué |
|---|---|---|
| T1-T5b | `87036d9` `cdd3413` `c2f209c` `3f26331` `de267fd` `13c7519` | transfer, `rachas.py` (nuevo, puro): `pegado`, `llega_a_fin`, `emparejar`, `cadenas`, `propias`, `previa`, `decidir_cadena` (pasos 1-5), `cierres_mes_anterior` (D14 = B) y `no_coincide` |
| T6 | `542c9a3` | `reglas_incidencias.py`: `sigue_editable` con `can`/`synckey` leídos (D12), guarda por cadena |
| T7 | `366e1bf` | contrato del transfer: `incidencias_mes`, `cierres_recursos`, `quitadas` → `rachas`, `cierres_racha`, `no_coincide`, `ajena` |
| T8 | `7380221` | cliente: `incidencias_en_ventana` (M−12..M+1, `INCIDENCIAS_MESES_ATRAS`), `UPDATE` de la `fec` con el `can` leído |
| T9 | `f3567fd` | preflight: `_decidir_rachas` sustituye a `_reconciliar_incidencias` |
| T12 | `7a08782` | lote: una lectura en ventana por lote (ronda C), M−1 solo con cierres D14 |
| T10 | `88f6710` | `ejecutar`: `UPDATE` de `editar`/`devolver`, `CIZ` en el parte del inicio, cierres; ningún `DELETE` |
| T11 | `6b721fe` | tests de F-030 del pipeline reescritos (lista cerrada); fuera `incidencias_del_mes` |
| T13 | `b7cab92` | api: columna `sigrid_dia_fin_antes` (ORM, dominio, repositorio, traza) |
| T14 | `4751fbb` | api: payloads con `incidencias_mes`, `quitadas`, `cierres_recursos` (`_designar_cierres`) |
| T15 | `8c81715` | api: traza de `continua`/`abierta`, día original, `devolver`, quitadas sin líneas, cierres |
| T16 | `ac4f558` | punta a punta: `tests/contratos/f062_rachas.json` y sus dos mitades; `f030_r30.json` (lista cerrada) |
| T17 | `1484468` | front: «Rachas», «Cierres de rachas» y «No coincide con Sigrid» en el modal |
| T18 | `553709b` | script `--cierres` y salida RACHA/CIERRE/NO COINCIDE; `#regla-incidencia`, `INTEGRACION.md`, `test_f002` |
| T5c | `69c23a1` | R31 (D17): `requiere_confirmar` y `clave` `cierre:{ide}`; `pendiente` sin la clave; casilla, aviso y script |
| T22 | `30ef3b4` `3e2cee8` `6266a9f` | `current.md` sin la ruta del scratchpad (la tomaba por GUID `test_f008` R21); 19 tests nuevos (21 casos) por los supervivientes de la mutación |

Ficheros de producción (39 en total con tests y docs; `git diff --stat d900f34..HEAD`):

- transfer: `application/services/rachas.py` (nuevo, 1121 líneas),
  `reglas_incidencias.py`, `lecturas_lote.py`, `pipelines/registro_pipeline.py`,
  `pipelines/registro_lote.py`, `domain/models/registro_models.py`,
  `infrastructure/sigrid/sigrid_write_client.py`, `interface_adapters/api/app.py`,
  `config/settings.py`, `.env.example` (`INCIDENCIAS_MESES_ATRAS`),
  `prueba_escritura_porcentajes.py`.
- api: `application/registro_sigrid.py`, `application/traza_incidencias.py`,
  `domain/models.py`, `infrastructure/db/orm_models.py`, `.../repositories.py`.
- front: `static/js/app.js` (sin lógica de negocio: solo pinta lo que manda el
  transfer; la casilla de R31 usa la `clave` que trae).
- docs: `docs/ARCHITECTURE.md#regla-incidencia` (reescrita), `docs/INTEGRACION.md`
  §1, §3 y §5.
- Tests nuevos: transfer `test_f062_rachas.py`, `test_f062_pipeline_rachas.py`,
  `test_f062_cliente_ventana.py`, `test_f062_lote.py`, `test_f062_punta_a_punta.py`;
  api `test_f062_payload_rachas.py`, `test_f062_punta_a_punta.py`; front
  `test_f062_modal_rachas.py`; contrato `tests/contratos/f062_rachas.json`.
- Tests ajenos tocados, **solo los de la lista cerrada** (design §12 + D18):
  `test_f030_pipeline_incidencias.py`, `test_f030_r30_editar.py`,
  `test_f030_reglas_incidencias.py`, `test_f030_r30_punta_a_punta.py` (×2) y
  `f030_r30.json`, `test_f030_registro.py` (r23), `test_f030_incidencias.py` (D18),
  `test_f030_r30_front.py` (lista de quitadas del modal), `conftest.py` del
  transfer (dobles) y `test_f002_fuente_unica.py` (gana un test). Ninguno más.

## Decisiones de diseño y desviaciones (resumen; detalle en `current.md`)

- **Orden cambiado**: T12 antes que T10-T11 (no toca `ejecutar`; se hizo
  mientras llegaba D17). `reconciliar` se borró en T9, no en T6, para no dejar
  la suite en rojo entre commits. T5c después de T18, como ordenó el líder.
- **Rojo intermedio previsto** entre T9 y T16, solo en tests de la lista
  cerrada (37-42), reescritos en T10-T11 y T16. Hoy, cero.
- El contexto del mes (`ContextoRachas`) va en el constructor del pipeline, no
  en `ejecutar`: `test_f013_sin_partida.py` R3 fija esa firma y no está en la lista.
- La respuesta solo lleva `rachas`/`cierres_racha`/`no_coincide` si la petición
  traía alguna clave nueva: sin ellas, petición y respuesta son las de F-030.
- **Arreglo de T9 visto en T18**: la racha que abre o cierra con una línea nueva
  no llevaba parte; `_partes_de_rachas` le pone el de su línea (RED propia).
- La quitada con traza crea la petición de su obra (R24) sin líneas: el
  transfer saca la empresa también de `quitadas` (suelto y lote).
- Script: `--cierres` sin `--incidencia` manda una línea testigo al 0 % por
  recurso (P3 la omite siempre) para dar periodo y empresa a la petición.
- T5c: el cierre sin confirmar sale en `cierres_racha` con `accion`
  `pendiente` y el motivo con su clave; **no** entra en `pendientes_confirmacion`
  (corrección del líder). El aviso de `registroEjecutar` lo suma a `pend`.
- Lectura de tasks T16 «6-9 y 12-14 = una cadena»: cada caso del contrato es
  una cadena de una sola incidencia (la 7).

## Fase RED (requisitos centrales)

Desde `services/dedicacion-<servicio>`, con `.venv/Scripts/python -m pytest`.
Cada traza es la salida real guardada en el momento; donde no guardé la línea
del comando lo digo y doy la selección (fichero y tests). Tras el código, cada
selección en verde (las suites completas, abajo).

- **T1** (D2, D5, D7) `tests/test_f062_rachas.py -q` (stubs; comando no guardado):
  `E NotImplementedError` ×24 · `24 failed in 0.54s`.
- **T2** (D11, R11, R15) `pytest tests/test_f062_rachas.py -k "cadenas or propias" -q`:
  `FAILED …test_f062_d11_cadenas_pegadas_del_mismo_recurso_y_codigo` ·
  `E NotImplementedError` · `11 failed, 24 deselected in 0.89s` → `35 passed`.
- **T3** (R1, R10) `pytest tests/test_f062_rachas.py -k previa -q`:
  `FAILED …test_f062_r10_c8_previa_no_con_ciz_del_mes_anterior_y_avisa` ·
  `9 failed, 35 deselected in 0.70s` → `44 passed`.
- **T4** (R2-R5, R9, R16, R21) `pytest tests/test_f062_rachas.py -k decidir -q`:
  `FAILED …test_f062_c1_decidir_abre_y_cierra_en_el_mismo_parte` ·
  `FAILED …test_f062_r16_decidir_si_ya_no_lo_continua_devuelve_el_ciz_ajeno` ·
  `29 failed, 44 deselected in 3.01s`.
- **T5** (R12, R13) `pytest tests/test_f062_rachas.py -q -k cierres`:
  `FAILED …test_f062_c4_cierres_inicio_de_m1_sin_continuacion_cierra_en_su_parte` ·
  `FAILED …test_f062_c12_cierres_inicio_anterior_a_m1_en_el_parte_de_m1_de_su_obra`.
- **T5b** (R17, R30) `pytest tests/test_f062_rachas.py -q -k "no_coincide or de_la_previa"`:
  `FAILED …test_f062_c10_no_coincide_quitada_con_sus_lineas_en_sigrid` ·
  `FAILED …test_f062_c11_no_coincide_solo_en_sigrid_por_racha_y_solo_designados`.
- **T6** (R14, D12) `pytest tests/test_f062_rachas.py -q -k "sigue_editable or no_editar or sin_codigo"`:
  `E AssertionError: assert False is True` (`sigue_editable` de un `CIZ` ajeno
  con `can=1.0`) · `3 failed, 1 passed, 96 deselected in 2.01s`.
- **T7** (R22, R24) `pytest tests/test_f062_pipeline_rachas.py -q -k contrato`:
  `FAILED …test_f062_r22_contrato_con_las_claves_nuevas_responde_las_rachas` ·
  `6 failed, 1 passed in 3.49s`.
- **T8** (R19, D12) `pytest tests/test_f062_cliente_ventana.py -q`:
  `FAILED …test_f062_r19_ventana_de_m_menos_n_a_m_mas_1` ·
  `FAILED …test_f062_r19_truncado_es_error_y_se_mide_con_su_nombre` ·
  `FAILED …test_f062_r14_d12_update_de_la_fec_con_el_can_leido`.
- **T9** (R1-R13 en el pipeline) `pytest tests/test_f062_pipeline_rachas.py -q -k preflight`:
  `FAILED …test_f062_c6_preflight_mueve_el_ciz_de_administracion_de_otra_obra` ·
  `FAILED …test_f062_r19_preflight_si_la_lectura_falla_la_peticion_falla` ·
  `13 failed, 2 passed, 7 deselected in 4.67s`. Los tests puros de
  `decidir_peticion` se escribieron después del código (dicho aquí).
- **T10** (R5, R12, R14) los 8 de `ejecutar` de `test_f062_pipeline_rachas.py`
  (comando no guardado): `FAILED …test_f062_c2_ejecutar_el_ciz_del_9_al_16_sin_insert` ·
  `FAILED …test_f062_r14_ejecutar_ninguna_sentencia_delete` ·
  `E KeyError: 'can_leido'` · `6 failed, 2 passed, 22 deselected in 4.40s`.
- **T12** (R20) `tests/test_f062_lote.py` (comando no guardado):
  `E assert [([200], 20251001, 20261130, 828942, [51, 52])] == [([200, 400], …)]`
  (una lectura por lote con la unión de recursos) · `6 failed, 2 passed in 6.25s`.
- **T13** (R15, api) `tests/test_f062_payload_rachas.py` (esquema):
  `E KeyError: 'sigrid_dia_fin_antes'` · `E AttributeError: sigrid_dia_fin_antes` ·
  `4 failed, 1 warning in 4.45s`.
- **T14** (R24) mismo fichero: `E KeyError: 'cierres_recursos'` ·
  `4 failed, 4 passed`; transfer: `FAILED …test_f062_r17_la_peticion_solo_con_quitadas_devuelve_el_ciz_ajeno` ·
  `E AssertionError: assert [] == [('devolver', …, 20261007)]` · `2 failed in 1.83s`.
- **T15** (R15, R17, R23) mismo fichero, `-k traza`: `FAILED …test_f062_r17_traza_devolver_anula_y_borra_la_quitada_sin_ide` ·
  `E ValueError: too many values to unpack (expected 1)` · `6 failed, 1 passed, 7 deselected`.
- **T16** punta a punta: pasó a la primera (prueba T9-T15 ya hechos); sin RED
  propia. Comprobado que falla al cambiar un dato del contrato (`dia_fin_antes` 7 → 8).
- **T17** (R25) `tests/test_f062_modal_rachas.py`: `E AssertionError: no existe la función diaMes en app.js` ·
  `5 failed in 0.22s`.
- **T18** (R22, R27) script: `E SystemExit: 2` (`--cierres` desconocido) ·
  `E AssertionError: assert 'RACHA inc=990101 abre · cierra el 20261016 en el parte PT26/00251' in 'Obra destino: 0404 …'` ·
  `3 failed, 1 passed, 31 deselected`; parte de la racha:
  `E AssertionError: assert [(7, None, …)] == [(7, 'PT26/00…', 'PT26/00251')]`;
  `test_f002`: `E AssertionError: La racha. assert '**La racha.**' in '<a id="regla-incidencia"></a>**Una incidencia es un par…'`.
- **T5c** (R31) transfer `-k "r31 or c13"`: `E ImportError: cannot import name 'PREFIJO_CLAVE_CIERRE'` ·
  `E AttributeError: 'CierreRacha' object has no attribute 'requiere_confirmar'` · `2 failed, 143 deselected`;
  script: `E AssertionError: assert 'PENDIENTE cierre:51: relanza con --pisar cierre:51' in …` · `1 failed`;
  front `pytest tests/test_f062_modal_rachas.py -k r31`: `E assert (0 == 1)` (ninguna
  casilla `chk-pisar`) y `- … 3 pendient / + … 1 pendient` · `2 failed, 5 deselected in 0.40s`.
  La api (`test_f062_payload_rachas.py -k r31`) pasó a la primera: desde T15 solo
  un `escribir` toca el `fin`; sin RED propia.

## Verificaciones MANUAL pendientes (del humano; NO ejecutadas)

**T19** (solo lectura, R20). Transfer local en modo pruebas; antes
`curl -s http://localhost:8006/health` debe decir `"modo_pruebas": true` (si
no, PARAR). Medir el preflight del mes como F-055 T18, en Git Bash, en `dev`
y en la rama: `cd services/dedicacion-transfer && .venv/Scripts/python prueba_escritura_porcentajes.py medir --lote --ano 2026 --mes 9 --obra 0694 --obra 0696 --recurso 1705036`;
≤ 15 % más y **una** lectura de incidencias por lote en el log (si no, PARAR).

**T20** (escritura en modo pruebas, obra `0404`). Transfer LOCAL con
`OBRA_PRUEBAS_FORZAR=true`, desde `services/dedicacion-transfer`, `RECURSO`
con `CIV` y `CIZ` en `reshor`. Resultado en `progress/manual_F-062.md`.

1. C1 y C2: `python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9`;
   luego `python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9 --incidencia RECURSO:CIV:12:16`
   y `python prueba_escritura_porcentajes.py verificar`: el **mismo** `ide` del `CIZ`, ahora el 16, sin inicio nuevo.
2. C3: `… ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:27:31` (`CIV` el 27 sin `CIZ`) y
   `… --mes 11 --incidencia RECURSO:CIV:2:6` (`CIZ` el 6 en el parte de noviembre de la `0404`, sin inicio).
3. C4: `python prueba_escritura_porcentajes.py limpiar --confirmar`; `… --mes 10 --incidencia RECURSO:CIV:27:31`
   y `… --mes 11 --cierres RECURSO` (`CIZ` el 31 en el parte de octubre, sin `--pisar`: inicio en M−1).
   Repetir cada `ejecutar`: nada nuevo.
4. C12/C13: `limpiar --confirmar`; `… --mes 9 --incidencia RECURSO:CIV:15:30`, `… --mes 10 --incidencia RECURSO:CIV:1:31`
   (nada escrito) y `… --mes 11 --cierres RECURSO` (nada escrito y `PENDIENTE cierre:{ide}: relanza con --pisar cierre:{ide}`);
   repetir con `--pisar cierre:{ide}` (`CIZ` el 31 de octubre en el parte de octubre de la `0404`).
5. C10, navegador local (modo pruebas): registrar 5-9, quitarla del cuadrante,
   abrir Registrar: «No coincide con Sigrid» con las dos líneas; Cancelar. Al final, `limpiar --confirmar`.

## Fuera del alcance y lo que falta

- T21 (líder): `azure-apps/dedicacion.md` y el aviso a `partes` (R27). No se tocó
  ni `azure-apps` ni `partes`.
- Sin push. La feature no se marca `done` aquí (reviewer).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests (suites de `bash harness/init.sh`, 2026-10-24, tras `6266a9f`) | raíz **418 passed, 1 skipped** (45.20 s); api **1164 passed** (73.05 s); front **376 passed** (52.61 s); transfer **1415 passed** (47.31 s). Cero fallos |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.8% de 898 líneas cambiadas cubiertas (896/898, umbral 80%, nivel critico)` |
| Mutación (`python -m harness.mutacion --feature F-062`, completa, 4 workers, HEAD `30ef3b4`) | **591** generados y evaluados, **560** muertos, **31** supervivientes, 0 timeouts, 0 sin veredicto, 3322.3 s |
| Supervivientes tras el análisis (`progress/mutacion_F-062.md`) | **0 sin cubrir**: 28 caen con un test nuevo, 1 era falso (cae con los tests de antes) y **2 equivalentes justificados** (`rachas.py:113`, orden 1→2 en la clave; `rachas.py:528`, las dos de la base omiten con el mismo motivo). Reverificados uno a uno, en serie, en un worktree de `6266a9f` |
| `bash harness/init.sh` | `ENTORNO LISTO` (tras borrar `.arnes_cache/suite_*.ok`); `PUERTA TAMAÑO … impl 203/220`; ruff 277 avisos, deuda previa: los ficheros tocados tienen los mismos que en `dev` |

Notas de la campaña, para el líder:

- **Posible defecto del arnés**: el nº 1 (`traza_incidencias.py:103`, `and`→`or`)
  salió vivo en la campaña paralela y, reaplicado en serie en un worktree del
  mismo HEAD, la suite de la api cae (15 fallos). No toqué `harness/`.
- La campaña paralela exige el árbol limpio y `BACKLOG.md` estaba modificado
  (no es mío y no se commitea): lo aparté con `git stash` solo mientras se
  creaban los worktrees y lo devolví al instante (idéntico, comprobado con `cmp`).
- Los 19 tests nuevos de T22 se escribieron después del código (los pide la
  mutación): sin fase RED; su «rojo» es el mutante que matan.
