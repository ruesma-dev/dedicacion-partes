<!-- progress/impl_F-025.md -->
# F-025 · Informe del implementer (rigor `critico`)

**Estado: T1-T9, T11 y T12 hechas; T10 refrescada SIN commit (es del humano);
T13-T14 MANUAL pendientes del humano; T15: `bash harness/init.sh` en verde.**
Rama `feature/F-025-obras-postventa-postv2`. Nadie llamó a `registro/ejecutar`,
ni a Sigrid, ni a `sigrid-api`, ni a ninguna base; ningún `.env` tocado.

## 1. Qué cambió (un commit por tarea)

| T | Commit | Cambio |
|---|---|---|
| T1 | `0835a22` | transfer: `universo_postventa.py` (`CatalogoPostventa`, `cargar_catalogo_postventa`, `casar_postventa`); `_destino_postventa` delega y devuelve el catálogo; fuera `self._nodos_pv` (`_es_hoja_activa_pv(nodos, paride)` estático; `partidas_postventa` = el de la petición, `[]` sin postventa); `ClienteFalso` cuenta `obra_por_codigo` y `capitulos_de_obra` |
| T2 | `54b6a89` | transfer: `UniversoPostventa.calcular(empresa, obras)`; `UniversoIn` y `POST /api/postventa/universo` (422 sin empresa válida sin leer, 502 ante excepción); cruce R2 parametrizado; R25 |
| T3 | `25a8338` | transfer: `resolver_postventa` = exacto o prefijo + solo letras (la más corta; a igualdad, la menor normalizada); los 8 tests de F-002 de design §7.1 (§3) |
| T4 | `f3a98de` | api: `Obra.admite_postventa`, `Linea.obra_admite_postventa`, `Linea.ofrecible` (única definición), `ResultadoUniverso`; `ObraORM.admite_postventa` (Boolean, NOT NULL, `default=False`, `server_default=false()`) |
| T5 | `c09abbd` | api: `UniversoPostventaGateway`, `TransferClient.universo_postventa`, `UniversoPostventaNoDisponible` → 502 en `_HTTP_POR_ERROR` |
| T6 | `af5703d` | api: `depurar_obras(..., universo)` marca y descarta solo sin marcas; `pedir_universo` compartido; `FetchObrasStep(..., *, universo, empresa_obras)`; `PreviewSync` publica `admiten_postventa`/`solo_postventa`/`motivo_postventa`; `sincronizar` guarda las dos marcas; `deps.py` con UN `TransferClient`; comentario de `config.yaml`; `UniversoFalso` en `tests/conftest.py`; firmas de §7.1 |
| T7 | `fab904b` | api: `listar_para_periodo` (+ `admite_postventa`), `_a_obra`/`_a_linea`, `modos_ofrecibles`, `ObraOut.admite_postventa`, `LineaOut.obra_admite_postventa`/`ofrecible`, copias con `ln.ofrecible`, `GuardarAsignaciones` rechaza línea nueva no ofrecible (422); `_Obras.modos_ofrecibles` y `CAMPOS_LINEA` de §7.1 |
| T8 | `3a44ffe` | front `app.js`: catálogo normal si `o.activa` y `Postv-` si `o.admite_postventa`; botón PV solo a un modo marcado por la API; copia y marca `obra-baja` con `l.ofrecible`; la línea añadida lleva las marcas de su obra |
| T9 | `3161be3` | `ARCHITECTURE.md` `#regla-p5` (casado de R10, universo, cerrada solo `Postv-`, procedencia F-025; conserva `(#regla-empresa)` y «Confirmado por») y tabla `obra`; `INTEGRACION.md` cabecera, §5 (endpoint, timeouts) y §7 (dos filas); README del transfer |
| T10 | — | `azure-apps/dedicacion.md`: cabecera con commit `3161be3` y fecha, párrafo del endpoint, fila de timeouts y dos filas de «qué se rompe», copiados LITERALES de T9 (22+ / 2-, CRLF conservado). **Sin commit**: es del humano |
| T11 | `850b283` | `scripts/verif_f025_postventa.ps1` (BOM, CRLF, ASCII), pasos M1 y M2 |
| T12 | `be3d3ae` | test de inmutabilidad de `CatalogoPostventa` (mata el único superviviente real) y campaña → `progress/mutacion_F-025.md` |

Sin SQL nueva contra Sigrid. Sin DDL a mano (el ALTER lo deriva `esquema.py`).
No se tocan `reglas_porcentajes.py`, `registro_sigrid.py`, `routes.py`, las
copias de `partes` ni `infra/`.

## 2. Decisiones de diseño (y desviaciones, justificadas)

1. **`texto_o_none` va a `domain/normalizacion.py`** (fichero no listado en
   design §3): R12 manda el `cod`/`descripcion` «que se guardarán», que el
   repositorio limpia con `_texto`; para no copiar esa regla en
   `application/`, pasa al dominio y `repositories.py` la importa como
   `_texto` (mismo comportamiento; `test_f025_r12_lo_que_se_manda_es_lo_que_se_guarda`).
2. **Motivo «no casa»** cita `catalogo.obra.codigo` (la obra resuelta por
   `con.cod = ?`), no el ajuste: mismo texto; lo vigilan `test_f013_…` y
   `test_f025_r11_el_preflight_omite_la_linea_por_no_casa` (texto entero).
3. **Fuera la guarda `and postventa_registrar` del preflight**: con el
   registro desactivado `cargar_catalogo_postventa` devuelve el motivo sin
   leer, y `ReglasPorcentajes` omite antes con `MOTIVO_POSTVENTA_OFF`. Mismo
   resultado; una sola comprobación (evita un mutante equivalente).
4. **`resolver_postventa` conserva `obra_nombre`** en la firma (ya no casa):
   la usan `casar_postventa` para el motivo y dos tests de F-002 que §7.1
   manda dejar «sin tocar el assert».
5. **Universo sin obras**: no lee y da `motivo: null` aunque
   `POSTVENTA_REGISTRAR=false` (no hay nada que casar).
6. **R13 «nunca de otra empresa»**: solo viajan las obras de la empresa de
   las obras (`"1"` cuenta) y el universo solo devuelve las pedidas; el test
   hace «casable» la 20 (de la 28) en `UniversoFalso` y comprueba que no sale.
7. **`desactivados`** cuenta las no recibidas con alguna marca. 8. **Front**: la línea añadida lleva `ofrecible: true` (el catálogo solo
   ofrece entradas ofrecibles); el botón PV mira las marcas de la API (R23).
9. **Script**: M1 crea el periodo local; no exige modo pruebas (design §8).

## 3. Tests anteriores cambiados (para el reviewer, fila a fila)

Todos de la lista cerrada de design §7.1; **ninguno fuera de ella** (no hizo
falta el método de la tabla adicional). Ningún assert se quita sin sustituto.

| Test | Antes → ahora | Req. |
|---|---|---|
| f002 `r16_el_capitulo_no_llega_al_paride_de_la_linea` | `capitulos`: `escribir`, `paride in hojas` → `omitir`, «no casa», `not paride`, sin inserts | D8 = A |
| f002 `r16_un_override_manual_a_un_capitulo_se_omite` | `capitulos`, `paride=70001` → `hojas`, `paride=69100` (capítulo `11`); mismo `MOTIVO_PARTIDA_PV_NO_HOJA` | D8 = A |
| f002 `r16_un_override_manual_a_una_hoja_si_vale` | `capitulos`, 70011 `0678.MO` → `hojas`, 70002 `0713`; mismo `manual` | D8 = A |
| f002 `r17_…_comparten_universo[capitulos]` | `elegida` no nula → `None` (desplegable == universo, igual; `[hojas]` igual) | D8 = A |
| f002 `r18_la_cascada_solo_actua_sin_exacto` | `0777` → 70006 (`0998`) → `None` | D2 = B |
| f002 `r18_el_ultimo_escalon_casa_por_nombre_de_obra` | `CLUB DEPORTIVO` → 70002 → `None` | D2 = B |
| f002 `r19_la_eleccion_no_depende_del_orden_de_las_filas` | `hojas`/`orden_invertido` con `06` → catálogo local `0578B`/`0578C` (directo e invertido) con `0578`; mismo assert | D2 = B |
| f002 `r19_el_desempate_es_por_codigo` | ídem; `nodo.cod == min(candidatos)` igual | D2 = B |
| f002 `r18_casado_por_codigo_exacto`, `r18_el_escalon_del_nombre_…` | solo docstring (citaban escalones retirados) | D2 |
| f023 `_pipeline`, `_preview`, `r17_preview_publica_claves_nuevas_y_antiguas` | + `universo=UniversoFalso(), empresa_obras=1`; ningún valor esperado | firma |
| f023 `_contenedor` | + `deps.TransferClient` → `UniversoFalso()` | doble |
| f023 `_obr` / `_obra_orm` | + `activa=True, admite_postventa=False` / + `admite_postventa=False` | firma |
| f026 `_preview`, `r17_el_reloj_del_preview_por_defecto_es_el_del_dia` | + `universo`, `empresa_obras=1` | firma |
| f032 `_preview`, `_contenedor`, `r1_pipeline_lee_y_guarda_las_empresas`, `r1_pipeline_sin_pasos_de_empresas_las_deja_a_cero` | + `universo`, `empresa_obras=1` / `TransferClient` sustituido | firma |
| f024 `_Obras` | + `modos_ofrecibles` (de `OBRAS`) | doble |
| f024 `r11_a_linea_mapea_la_empresa_de_la_obra` | `SimpleNamespace` + `admite_postventa=False` | doble |
| f034 `CAMPOS_LINEA` | + `obra_admite_postventa`, `ofrecible` | R18 |

Front y tests de la raíz: ninguno.

## 4. Fase RED (salida real, pegada; comando desde cada servicio)

**T1** · `.venv/Scripts/python -m pytest tests/test_f025_universo_postventa.py -q -k "r8 or r9"` (transfer):
```
E       AssertionError: assert [{'ide': 7000...': 'CD'}, ...] == []
E         Left contains 9 more items, first extra item: {'ide': 70001, 'cod': '0678', 'res': '15 VIVIENDAS Y HOSTEL', 'categoria': 'CD'}
E       AssertionError: assert {'_cli', '_nodos_pv', '_st'} == {'_cli', '_st'}
FAILED tests/test_f025_universo_postventa.py::test_f025_r8_preflight_sin_postventa_tras_otro_con_postventa
FAILED tests/test_f025_universo_postventa.py::test_f025_r9_el_pipeline_no_guarda_estado_entre_peticiones
2 failed, 2 passed in 0.41s
```
**T2** · `… -m pytest tests/test_f025_universo_postventa.py -q` (transfer):
```
E       ImportError: cannot import name 'UniversoPostventa' from 'application.services.universo_postventa'
E       AssertionError: {"detail":"Not Found"}
E       assert 404 == 422
E       assert 404 == 502
24 failed, 5 passed in 4.22s
```
**T3** · `… -m pytest tests/test_f025_casado_p5.py -q` (transfer):
```
E       AssertionError: assert '0578-C' == '0578B'
E       AssertionError: assert 'CP.1' is None
E       AssertionError: assert '0678.MO' is None
E       AssertionError: assert 'CI.7.5' is None
E       AssertionError: assert '0611' is None
E       AssertionError: AccionLinea(registro_id=9, accion='escribir', … paride=201, partida_cod='CP.1', partida_metodo='postventa' …)
12 failed, 6 passed in 1.18s
```
**T4** · `… -m pytest tests/test_f025_sync_postventa.py -q -k "r18 or r21"` (api), 10 fallos:
```
E       TypeError: Linea.__init__() got an unexpected keyword argument 'obra_admite_postventa'
E       AttributeError: 'Obra' object has no attribute 'admite_postventa'
E       ImportError: cannot import name 'ResultadoUniverso' from 'domain.models'
E               KeyError: 'admite_postventa'
E         Right contains one more item: 'ALTER TABLE obra ADD COLUMN IF NOT EXISTS admite_postventa BOOLEAN DEFAULT false NOT NULL'
```
**T5** · `… -m pytest tests/test_f025_sync_postventa.py -q -k r15` (api):
```
E       AttributeError: 'TransferClient' object has no attribute 'universo_postventa'
E       ImportError: cannot import name 'UniversoPostventaNoDisponible' from 'domain.errors'
9 failed, 10 deselected in 3.78s
```
**T6** · mismo fichero, sin `-k` (api). Traza reproducida en un worktree en
`c09abbd` (T5) con los tests de `af5703d`, agrupada con `sort | uniq -c`:
```
      8 E       TypeError: FetchObrasStep.__init__() got an unexpected keyword argument 'universo'
      3 E       TypeError: PreviewSync.__init__() got an unexpected keyword argument 'universo'
      3 E       assert (0, 0, 0) == (0, 1, 0)
      1 E       assert (False, True) == (False, False)
      1 E       assert [] == [7]
19 failed, 21 passed, 1 warning in 6.60s
```
**T7** · `… -m pytest tests/test_f025_cuadrante_postventa.py -q` (api):
```
E       AssertionError: assert 'WHERE obra.activa IS true OR obra.admite_postventa IS true OR obra.ide IN (SELECT asignacion.obra_ide' in 'SELECT obra.ide, … WHERE obra.activa IS true OR obra.ide IN (SELECT …'
E       AttributeError: 'PgObraRepository' object has no attribute 'modos_ofrecibles'
E       AttributeError: 'ObraOut' object has no attribute 'admite_postventa'
E       AttributeError: 'LineaOut' object has no attribute 'obra_admite_postventa'
E       assert 200 == 422          (test_f025_r20_el_422_por_http)
15 failed, 8 passed, 1 warning in 5.94s
```
**T8** · `… -m pytest tests/test_f025_catalogo_postventa.py -q` (front): `7 failed in 0.20s` (los 7: R22 ×3, R23 ×2, R24 ×2).

## 5. Resultado real de las verificaciones

- transfer `python -m pytest tests -q`: **379 passed** (330 antes + 49 nuevos).
- api: **503 passed** (440 antes + 63 nuevos). front: **28 passed** (21 + 7).
- raíz `python -m pytest tests -q`: **418 passed, 1 skipped**.
- T11: `Select-String -Path scripts/verif_f025_postventa.ps1 -Pattern ejecutar`
  → **0 coincidencias**; `Parser.ParseFile` → 0 errores. No se ha ejecutado.
- `bash harness/init.sh` (final): ver §8.

## 6. Campaña de mutación (T12)

Campaña final (la que queda en `progress/mutacion_F-025.md`):
`python -m harness.mutacion --feature F-025 --workers 1` sobre `be3d3ae` →
**56 generados, 56 muertos, 0 supervivientes, 0 timeouts, 649.9 s**
(17 ficheros, 458 líneas en alcance; campaña completa, sin muestreo).

Historia, para que el reviewer la pueda reproducir (RM):
1. **Campaña 1** (paralela, 4 workers, sobre `850b283`): 52 muertos y 4
   «supervivientes»: `universo_postventa.py:31` (`frozen=True` → `False`),
   `universo_postventa.py:80` (`is None` → `is not None`), `app.py:182`
   (`"ok": False` → `True`, rama 422) y `app.py:190` (`502` → `503`).
2. Tres de ellos **no eran supervivientes**: el de la línea 190 lo reproduje
   a mano (sed en el árbol, suite del transfer) y lo caza
   `test_f025_r6_fallo_de_sigrid_502` (`1 failed, 359 passed`); los tres los
   cazaron `test_f025_r6_fallo_de_sigrid_502`, `test_f025_r4_…` y el cruce R2
   en la **campaña 2** (serie, `--workers 1`, mismo `850b283`: 55 muertos, 1
   superviviente). Los cuatro de la campaña 1 salieron seguidos ([48]-[52]):
   apunta a un fallo de la campaña paralela del arnés, no a un hueco de
   tests. **Aviso para el líder**: merece una feature del arnés (no lo toco).
3. **Superviviente real**: `@dataclass(frozen=True)` → `frozen=False` en
   `CatalogoPostventa`. No era equivalente: nada impedía modificar el catálogo
   compartido por todas las obras de una petición (design §4.1 lo declara
   inmutable). Test nuevo `test_f025_r9_el_catalogo_de_una_peticion_es_inmutable`;
   con el mutante aplicado a mano: `Failed: DID NOT RAISE FrozenInstanceError`
   (`1 failed`); con el código: verde. **Campaña 3** (serie, `be3d3ae`): 0.

Ningún mutante se ha dado por «equivalente».

## 7. Verificaciones MANUAL (humano) — comandos exactos

**Nunca `registro/ejecutar`.** API y transfer LOCALES desde esta rama, api
contra la BBDD LOCAL (`PG_HOST=localhost`).

- **T10** · `git -C C:\Users\pgris\PycharmProjects\azure-apps diff dedicacion.md`
  → revisar las 4 piezas (cabecera con `3161be3`, párrafo del endpoint en §5,
  fila de timeouts, dos filas de §7) y hacer el commit en `azure-apps`.
- **T13 (M1)** · `powershell -ExecutionPolicy Bypass -File scripts/verif_f025_postventa.ps1 -Paso M1`
  desde la raíz. Esperado: preview `admiten_postventa = 83`,
  `solo_postventa = 73`, `motivo_postventa` nulo; sync OK; cuadrante con la
  1 y con la 18 idéntico; `0656`, `0660`, `0669`, `0689` con `activa=false` y
  `admite_postventa=true`; `CP`, `OT`, `191105` con `admite_postventa=false`;
  `RESULTADO M1: OK`. Resultado real → `progress/current.md`.
- **T14 (M2)** · `powershell -ExecutionPolicy Bypass -File scripts/verif_f025_postventa.ps1 -Paso M2 -Anio AAAA -Mes MM`
  (periodo de prueba local; tras M1). Esperado: en la obra `0656`,
  `capitulo_postventa.cod == "0656"`; en la obra sin postventa,
  `partidas_postventa == []`; `no_vigentes == []`; `RESULTADO M2: OK`.
- Al desplegar: la api añade `obra.admite_postventa` (DEFAULT false) al
  arrancar; hasta el primer sync ninguna obra ofrece `Postv-`.

## 8. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | transfer 379, api 503, front 28, raíz 418 (+1 skipped): **todos en verde** |
| Tests nuevos de F-025 | transfer 49 (`test_f025_universo_postventa.py` 31, `test_f025_casado_p5.py` 18), api 63 (`test_f025_sync_postventa.py` 40, `test_f025_cuadrante_postventa.py` 23), front 7 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 162 líneas cambiadas cubiertas (162/162, umbral 80%, nivel critico)` |
| Mutación | 56 generados, 56 muertos, **0 supervivientes** (§6) |
| Tiempo de la suite | raíz 71.2 s (con cobertura) en el `init.sh` final, transfer 10.8 s; api 16.8 s y front 2.2 s en su última ejecución completa |
| `bash harness/init.sh` | **ENTORNO LISTO**; `PUERTA TAMAÑO: … impl 219/220`; ruff 215 avisos (no bloquea; 200 antes: los nuevos son del estilo ya presente, `Optional`, `noqa: BLE001` como sus vecinos, orden de imports) |

Fuera del alcance (spec §9-§10): renombrar `capitulo_postventa`, la POSTV
antigua (D6), validar partidas con Administración (F-017). Lo que falta para
cerrar: review, commit del humano en `azure-apps` (T10), T13 y T14.
