<!-- progress/impl_F-037.md -->
# F-037 · Informe del implementer

Rama `feature/F-037-asiento-analitico-obra`, rigor **crítico**, SDD. Hechas
**T1-T10 y T15**; T11, T13 y T14 son del líder o del humano y T12 es MANUAL
(abajo). Sin escrituras en Sigrid, sin `registro/ejecutar`, sin tocar
`partes`, `current.md`, `features.json`, `CLAUDE.md`, `.env` ni `azure-apps`.

## 1. Copia de `partes` (T2)

- Copiados con `git -C ..\partes show feature/F-031-asiento-analitico:services/partes-transfer/application/services/<f>`
  (sin checkout): `estado_parte.py` y `cuenta_analitica.py`, **byte a byte**.
- **Commit copiado: `9b202e9f6fa3571d778bb39b27c77ff65660ee11`** (último que
  cambia los dos ficheros; `estado_parte.py` nace en `b205681`). La punta de
  la rama al copiar era **`dc5666b`** (ya no `5ff4d91`): los dos ficheros son
  idénticos a `9b202e9` (comprobado con `cmp`). Ojo para el líder: la punta de
  `partes` dice «F-031: bloqueada en T12, un test ajeno de F-002 fija el nombre
  `partes_existentes`» y su árbol tiene cambios sin commit; no los he tocado.
- `tests/test_f037_copias_partes.py` compara contra `COMMIT_COPIADO` y contra
  la rama vigilada; sin el repo o sin la ref, `skip` con motivo.

## 2. Qué cambió, por tarea (un commit cada una)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `6f97dc2` | `ParteSigrid`, `PartidaCuenta` (frozen); `HoraRecurso.caa_cod/defecto`; `AccionLinea.caa_*` (6); `ParteDestino.estado/complementario/cerrados/del_periodo/aviso`; ajustes `EST_PARTE_CERRADO=3`, `EST_PARTE_IMPUTADO=10` y `.env.example` |
| T2 | `f159924` | Copias literales + `test_f037_reglas_partes.py` (casos de `partes` renombrados) + anti-divergencia |
| T3 | `51bce18` | Dobles de `conftest.py` y `test_pipeline_offline.py` (tabla §4) |
| T4 | `9eb3d53` | Cliente: `_read` lanza con `truncated`; `horas_de_recursos` con `caacod`/`defecto`; `cuentas_de_centro`, `partidas_de_lineas`, `partes_del_periodo` (SQL de design §6); `stmt_insert_linea(..., caaide=0)`; docstring |
| T5 | `324912e` | Paso 4 bis (`_cuentas`): partidas una vez por petición, cuentas una por centro, sin `try`; avisos sumados con « · »; `caaide` en el INSERT y `caa_cod` en `escritas[]` |
| T6 | `bb667f1` | `siguiente_cod_pt(ano, empresa)` con `AND emp = ?`; alta protegida D17 (condición fuera del agregado, `UPDLOCK, HOLDLOCK`) y `hmo` por `cod`+`tip`+`emp` con `NOT EXISTS` |
| T7 | `82b0dd2` | Paso 5 (`elegir_parte`, aviso), paso 7 (líneas de **todos** los partes; choque con cerrado → `omitir`; conflicto con el `parte_cod` donde vive; capacidad sumando todos), paso 9 (`_crear_parte`: alta, relectura, un reintento, `RuntimeError`) |
| T8 | `2ba5b21` | `ARCHITECTURE.md`: punto 16 `#regla-analitica`, alcance en `#regla-conflicto` y `#regla-capacidad`, `#regla-sin-partida` sin «imputación analítica», transfer y «Acceso a datos»; ancla en `ANCLAS` |
| T9 | `43c1827` | `INTEGRACION.md`: fecha y origen, §1 (lecturas, parte compartido, «Contabiliza parte…»), §7 (4 filas) |
| T10 | `9ac9ab4`, `771c35d`, `40b9feb` | Tests que matan los 13 supervivientes (§6); estilo `ruff` de los tests nuevos y `X \| None` en los dos ayudantes nuevos del pipeline |

Ficheros de producción: `domain/models/registro_models.py`, `config/settings.py`,
`.env.example`, `application/services/{estado_parte,cuenta_analitica}.py`
(nuevos), `infrastructure/sigrid/sigrid_write_client.py`,
`application/pipelines/registro_pipeline.py`. Tests nuevos: `test_f037_*` (4).

## 3. Decisiones y desviaciones (JUSTIFICADAS; para el líder)

1. **`partes_existentes` NO se ha quitado** (design §3 decía «fuera, sin
   uso»). No es cierto que no tenga uso: `prueba_escritura_porcentajes.py`
   (fase `estado`, solo lectura) la llama, y design §4 prohíbe tocar ese
   script. Quitarla rompería esa fase sin que ningún test lo viera. Se queda,
   con docstring que dice que el pipeline ya no la usa. Si el humano la quiere
   fuera, hay que tocar el script (cambio de spec).
2. **Sin partida + choque con cerrado**: si una línea sin partida pasa a
   `omitir` por `parte_cerrado`, su conflicto `sin_partida` del paso 6 bis se
   retira; si no, saldría dos veces en `omitidas` (la api hace un UPDATE por
   entrada). Test `test_f037_r13_sin_partida_que_choca_con_cerrado_solo_se_omite`.
3. El predicado «cerrado» del paso 7 es `cod in parte.cerrados`, la lista que
   sale de `elegir_parte`: el único predicado sigue viviendo en la copia.
4. D17: tras el alta, si el En registro releído no tiene nuestro código, se usa
   igual y `creado = False` (el log dice «de otro servicio, se usa»).
5. `stmt_insert_linea(..., caaide=0)` con defecto, como dice design §5 (en
   `partes` es obligatorio); `int(caaide or 0)`.
6. Las acciones `ya_registrado` conservan los `caa_*` calculados (informativos,
   igual que `partes`); no generan ninguna sentencia (R17, test r12).
7. Los dobles de ajustes (`SettingsFalso`, `Settings` del offline) ganan
   `est_parte_*`: son dobles, dentro de la lista cerrada (§4).
8. Los tests de D17 ejecutan el SQL del alta en un **SQLite en memoria**
   (quitando las pistas `WITH (UPDLOCK, HOLDLOCK)` e `ISNULL`→`IFNULL`): es un
   fixture, no Sigrid ni ninguna BBDD del sistema. Prueban la trampa del
   agregado, el código ocupado, el En registro existente y el `emp` del `hmo`.
9. `ruff` (aviso, no bloquea): 222 avisos al empezar, 237 al acabar. Los 15
   nuevos: 12 `UP045` en `registro_models.py` (los campos nuevos usan
   `Optional[...]` como el resto del fichero, por coherencia) y 3 `I001` de
   los `test_f037_*` que solo salen con la configuración de la raíz (desde
   `services/dedicacion-transfer`, «All checks passed!»; `conftest.py` ya
   tenía el mismo `I001` en `dev`).
10. Fuera de alcance, preexistente y no tocado: la capacidad no se evalúa en
   un periodo **sin ningún parte** (antes: «parte nuevo»), así que dos líneas
   nuevas del mismo recurso que sumen > 1 no avisan. Lo dejo anotado.

## 4. Tests anteriores que cambian (lista cerrada de design §9.2)

| Test | Antes | Ahora | Requisito |
|---|---|---|---|
| `tests/conftest.py` (`ClienteFalso`, `SettingsFalso`) | sin `cenide`, MENC/MJEFO sin cuenta, `siguiente_cod_pt(ano)` | `cenide` en 4 obras; `caa_cod` `00000.CIMO03`/`CIMO02`; `partes_del_periodo` (derivado de `parte` en cada llamada), `cuentas_de_centro` (una por subcuenta), `partidas_de_lineas` (vacío); `siguiente_cod_pt(ano, empresa=None)`; `est_parte_*` | R1-R11 (dobles) |
| `tests/test_pipeline_offline.py` (doble y `Settings`) | sin los métodos nuevos | los mismos métodos y firma; `est_parte_*` | R1-R11 (dobles) |
| `tests/test_f002_fuente_unica.py` | `ANCLAS` sin la nueva | `"regla-analitica"` en `ANCLAS` | R18 |

Ningún `assert` anterior se ha tocado (`git diff dev..HEAD` de los dos dobles
sin líneas `assert`). Ningún otro test anterior ha caído en ningún momento.

## 5. Fase RED (salida real, antes del código)

Desde `services/dedicacion-transfer`, `.venv/Scripts/python -m pytest -q …`:

- **T1** `tests/test_f037_reglas_partes.py` →
  `E   ImportError: cannot import name 'ParteSigrid' from 'domain.models.registro_models'` · `1 error in 0.23s`
- **T2** `tests/test_f037_reglas_partes.py tests/test_f037_copias_partes.py` →
  `E   ModuleNotFoundError: No module named 'application.services.estado_parte'`;
  solo copias: `E  FileNotFoundError: … application\services\estado_parte.py`
  y `… cuenta_analitica.py` (4 FAILED)
- **T4** `tests/test_f037_cliente_sigrid.py` → `11 failed, 3 passed`:
  `AttributeError: 'SigridWriteClient' object has no attribute 'cuentas_de_centro'`
  (ídem `partes_del_periodo`, `partidas_de_lineas`); `Failed: DID NOT RAISE RuntimeError`
  (truncated); `TypeError: SigridWriteClient.stmt_insert_linea() got an unexpected keyword argument 'caaide'`;
  `{200: [HoraRecurso(... caa_cod=None, defecto=False) ...]} != {200: [HoraRecurso(... caa_cod='00000.CIMO03', defecto=True) ...]}`
- **T5** `tests/test_f037_pipeline.py -k "r1 or … or r8"` → `20 failed, 2 passed`:
  `KeyError: 'caaide'` (×4); `assert (0, None, Non...e, None, None) == (90001, '0404...ecurso', None)`;
  `Failed: DID NOT RAISE RuntimeError` (×2, R7); `assert [] == [([80001, 80002],)]`
- **T6** `tests/test_f037_cliente_sigrid.py` → `10 failed, 15 passed`:
  `TypeError: SigridWriteClient.siguiente_cod_pt() takes 2 positional arguments but 3 were given` (×5);
  SQLite: `assert (2,) == (1,)` (hmo duplicado), el alta crea con un En
  registro del periodo (`[(500, 1, 1, …), (901, …)] == [(500, …)]`), con código
  ocupado y sin filtrar `emp`; pipeline `-k r11`: `assert [(2026, None)] == [(2026, 28)]`
- **T7** `-k "r9 or … or r17 or d17"` → `18 failed, 4 passed`:
  `assert [] == [(828942, 2026, 7), …]` (R9); `At index 1 diff: 777 != 7` (R10);
  `assert [777] == [11]` y `[777] == [951]`; `assert 'escribir' == 'omitir'` (R13, ×4);
  `Failed: DID NOT RAISE RuntimeError` (R11, R16); `KeyError: (828942, 2026, 8)` (R17)
- **T8** `tests/test_f002_fuente_unica.py` → `2 failed, 64 passed`:
  `AssertionError: regla-analitica` (ancla ausente y no única)
- T3 y T9 no tienen código de producción (dobles y documento): su verificación
  es la suite en verde y `tests/test_f008_infra_sin_secretos.py` (53 passed).

## 6. Mutación (T10, en serie, `--workers 1`)

`python -m harness.mutacion --feature F-037 --workers 1`, alcance 6 ficheros /
576 líneas, campaña completa:

| Campaña | SHA | Mutantes | Muertos | Superv. | Tiempo |
|---|---|---|---|---|---|
| 1ª | `43c1827` | 85 | 73 | 12 | 455,7 s |
| 2ª (tras los tests de T10) | `771c35d` | 85 | 85 | 0 | 444,9 s |
| **final** → `progress/mutacion_F-037.md` | **`40b9feb`** | 85 | **85** | **0** | 423,1 s |

**Honestidad sobre las copias:** el test anti-divergencia compara bytes, así
que mata cualquier mutante de las dos copias por sí solo. Para saber si los
tests de comportamiento las vigilan, campaña aparte con ese test fuera:
`PYTEST_ADDOPTS="--ignore=tests/test_f037_copias_partes.py" python -m harness.mutacion --feature F-037 --workers 1 --ficheros <las dos copias> --salida progress/mutacion_F-037_copias.md`
→ 1ª: 25 / 24 / **1** (`OrigenSubcuenta` `frozen=True→False`); final, en
`40b9feb`: **25 / 25 / 0** (107,0 s). Que el `--ignore` surtió efecto lo
prueba ese superviviente de la 1ª: con el test de copias habría muerto.

Los 13 supervivientes, todos **huecos reales** (ninguno equivalente), muertos
con un test barato (commits `9ac9ab4`, `771c35d`; líneas de la 1ª campaña):

| Mutante | Por qué vivía | Test que lo mata |
|---|---|---|
| `pipeline:222` `paride or 0 → or 1` | ninguna partida de `ide` 1 en los datos | `r3_una_linea_sin_partida_no_hereda_la_de_otra` |
| `pipeline:224` `getattr(d,"cenide",0)→1` y `or 0→or 1` | ninguna obra sin centro | `r4_obra_sin_centro_no_lee_cuentas_y_avisa` (×2) |
| `pipeline:229/237` 5 mutantes del recuento `por_origen` | el log no se comprobaba | `r7_el_log_cuenta_las_lineas_por_origen` (caplog) |
| `pipeline:273` `p.existe = True → False` | una sola línea por parte nuevo | creación con 2 líneas: un solo `crear` y `existe` |
| `pipeline:451` `not grupo or … → and` | no se miraba qué se lee sin acciones | `r12_…`: `de("lineas") == []` |
| `cliente:415` `desc[:128] → [:129]` | sin descripción larga | `r11_la_descripcion_del_parte_se_corta_a_128` |
| `cliente:432` `paride: int = 0 → 1` | todos los tests pasaban `paride` | `r1_insert_sin_partida_escribe_cero` |
| `cuenta_analitica:73` `frozen=True → False` | solo lo mataba el test de copias | `r3_el_origen_de_la_subcuenta_es_inmutable` |

Este último hueco está igual en los tests de `partes` (allí no hay test de
inmutabilidad de `OrigenSubcuenta`): avisarles es del líder.

## 7. `bash harness/init.sh` (T15) — resultado real

Última ejecución, en `40b9feb` con este informe y los de mutación en el
árbol: **`ENTORNO LISTO`**, todo `[OK]` salvo el `[AVISO]` de `ruff` (§3.9).
Raíz: `418 passed, 1 skipped in 57.60s`; transfer: `537 passed, 1 warning in
10.26s`; api y front en verde (caché); **`PUERTA COBERTURA: 100.0% de 219
líneas cambiadas cubiertas (219/219, umbral 80%, nivel critico)`**;
`PUERTA TAMAÑO: … impl 197/220`.

## 8. MANUAL pendiente

- **T12 (humano, solo lectura).** Con el `.env` local del transfer en
  `OBRA_PRUEBAS_FORZAR=true` y la api local con `TRANSFER_BASE_URL=http://127.0.0.1:8006`:
  ```
  cd services/dedicacion-transfer && .venv/Scripts/python main.py      # 8006, rama F-037
  cd services/dedicacion-api && .venv/Scripts/python main.py           # 8090
  curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight" -H "Content-Type: application/json" -d "{}"
  ```
  (periodo de prueba con un trabajador MENC o MJEFO y otro MPRL). **Esperado:**
  la acción MENC/MJEFO en `escribir` con `caa_cod` = `0404.CIMO03` /
  `0404.CIMO02`, `caa_origen` = `recurso`, `caa_aviso` vacío; la MPRL con
  `caa_ide` 0, `caa_motivo` `obra_sin_cuenta` y `caa_aviso` «la obra 0404 no
  tiene la cuenta analitica .CIMO16: la linea ira sin cuenta» (también dentro
  de `aviso`); en `partes[]` de 0404, `estado`, `complementario`, `cerrados`,
  `del_periodo` (`ide`, `cod`, `est`) y `aviso`. **NO lanzar `registro/ejecutar`.**
- **T11** (líder): avisar a `partes` de la carrera y del alta protegida D17
  (y del hueco de `OrigenSubcuenta`, §6).
- **T13** (humano + Administración, autorización expresa): R20-R21 tal como
  los describe `tasks.md`.
- **T14** (líder): copiar a `azure-apps/dedicacion.md` las piezas de T9
  (cabecera de fecha, párrafo nuevo de §1 y fila de `sigrid-api`, 4 filas de §7).

## 9. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests del transfer | **537 passed**, 1 warning previo (`test_preflight` devuelve valor); 10,26 s en `init.sh`. De ellos, `test_f037_*`: 156 |
| Suite raíz de `init.sh` | 418 passed, 1 skipped, 57,60 s |
| Cobertura de líneas cambiadas | **100,0 %** (219/219), nivel crítico, umbral 80 % |
| Mutantes F-037 (campaña completa, en serie) | 85 generados, 85 muertos, **0 supervivientes**, 0 timeouts, 423,1 s (`progress/mutacion_F-037.md`, SHA `40b9feb`) |
| Mutantes de las copias sin el test de copias | 25 / 25 / **0**, 107,0 s (`progress/mutacion_F-037_copias.md`) |
