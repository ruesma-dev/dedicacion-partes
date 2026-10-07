<!-- progress/impl_F-039.md -->
# F-039 · Informe del implementer (rigor `critico`)

**Estado: T1-T8, T10 y T11 hechas, cada una con su commit; T9 (azure-apps) es
del líder; T12-T14 MANUAL pendientes del humano; T15: `bash harness/init.sh`
en verde.** Rama `feature/F-039-obras-var-y-seis-digitos`. Nadie llamó a
`registro/ejecutar` ni a Sigrid/`sigrid-api`; ningún `.env`, ni
`estado_parte.py`/`cuenta_analitica.py`, ni `current.md`/`features.json`
tocados.

## 1. Qué cambió (un commit por tarea)

| T | Commit | Cambio |
|---|---|---|
| T1 | `66e8418` | transfer: `universo_var.py` (`CatalogoVar`, `numero_inicial`, `es_partida_var`, `cargar_catalogo_var`, `partida_var_de`, `UniversoVar.calcular`, motivos `MOTIVO_VAR_*`); ajustes `var_obra_cod` (`VAR_OBRA_COD`, `"VAR"`) y `var_partida_desde` (`VAR_PARTIDA_DESDE`, 29) + `.env.example` |
| T2 | `b6800a9` | transfer: `UniversoVarIn` y `POST /api/var/universo` (422 con `empresa_valida` sin leer; 502 ante excepción) |
| T3 | `f8749a2` | transfer: `LineaEntrada.var_paride`/`LineaIn.var_paride`; rama VAR del bucle de partidas ANTES del override (postventa → omitir sin leer; catálogo lazy una vez por petición; `partida_var_de`; si vale, `paride`/`partida_cod`/`partida_metodo="var"` y `continue`); docstring del paso 4 → `#regla-var` |
| T4 | `5b24ee1` | api: `domain/obras.py` (`tiene_digitos_seguidos`, `codigo_entrada`, `ide_entrada`), `PartidaVar`, `ResultadoUniversoVar`, `UniversoVarGateway`, `UniversosGateway`, `UniversoVarNoDisponible` → 502; `ObraORM.registro_obra_ide`/`registro_obra_cod`/`registro_paride` (nulables, sin default; ALTER derivado) |
| T5 | `d7efced` | api: `TransferClient.universo_var`; `descartar_por_codigo`, `entradas_var`, `depurar_obras(..., no_normales)`; `preparar_obras` + `ObrasPreparadas` en `FetchObrasStep` y `PreviewSync` (`digitos_excluidos=0` por defecto) con las claves de R17; `sincronizar` guarda y compara las tres columnas; `deps.py`; `config.yaml` `digitos_seguidos_excluidos: 6`; doble `UniversoFalso.universo_var` |
| T6 | `829e43e` | api: `_payloads` agrupa por `registro_obra_ide or ide`, obra del grupo = la de registro (`nombre` `None`), la entrada manda `var_paride` y nunca `paride`; dobles `_fila` de §7.1 |
| T7 | `5c7293d` | front `app.js` `pintarModalPreflight`: `escribir` + `partida_metodo === "var"` → `<span class="partida-fija">` con `partida_cod` (y su aviso); el resto igual |
| T8 | `adf9254` | `ARCHITECTURE.md`: reglas 17 `#regla-var` y 18 `#regla-seis-digitos`, lista de anclas y tabla `obra`; `ANCLAS` de `test_f002`; README del transfer (endpoint, `var_paride`, fila de la tabla); `INTEGRACION.md` cabecera/fecha, §3 (dos ajustes), §5 (endpoint) y §7 (cinco + una filas) |
| T10 | `36419ed` | `scripts/verif_f039_var.ps1` (BOM, CRLF, ASCII), pasos M1 y M2 |
| T11 | `6ab6588` | dos tests que matan los supervivientes reales; campaña final en serie → `progress/mutacion_F-039.md` (va en el commit de este informe) |

Sin SQL nueva contra Sigrid ni DDL a mano.

## 2. Decisiones de diseño (y desviaciones, justificadas)

1. **`partida_var_de(...)`** en `universo_var.py` (no listada en design
   §4.1): la consulta común del catálogo en el preflight; los `MOTIVO_VAR_*`
   viven ahí porque `reglas_porcentajes.py` está en «no se tocan» (§10).
2. **Postventa antes que el catálogo**: la línea de postventa con
   `var_paride` se omite sin leer la obra VAR (R6, con test).
3. **`var_paride is not None`**: un `0` se omite (fuera del universo) en vez
   de caer al casado por categoría contra los `CI.*` de VAR (lo que D1 veta).
4. **`VAR_OBRA_COD` con espacios = vacío** (`.strip()`), sin leer Sigrid.
5. **La obra VAR nunca se descarta** en `depurar_obras` (R14 «se guarda»):
   `activa=False` y su `admite_postventa`; `solo_postventa` cuenta `admite
   and not activa` (igual que antes para el resto; la VAR no cuenta).
6. **`brutas` del preview** = todas las leídas (`depurado.brutos =
   len(brutas)`); `ObrasPreparadas` gana `entradas` (no en design) para que
   `entradas_var` cuente las filas realmente añadidas.
7. **`ResultadoUniversoVar.empresa`** = la de `obra_var` (R13).
8. **`deps.py` con `.get("digitos_seguidos_excluidos", 0)`**: los `config` de
   prueba de F-023 no traen la clave; sin clave, sin filtro (test).
9. **Grupo de registro mixto** (obra VAR + entradas): la obra del grupo la
   pone la primera fila por `cod` (`VAR` < `VAR-29`); el transfer resuelve
   por `ide`. 10. **Front**: sin regla CSS para `.partida-fija` («Nada más»).

**Fuera de alcance (para el humano):** la hoja Resumen del Excel
(`exporter.py`, «no se tocan») usa `Decimal.normalize()` y un porcentaje
redondo sale en notación científica (`1E+2%` para 100 %, `7E+1%` para 70 %),
en cualquier obra. Visto al escribir el test de R21. Merece feature propia.

## 3. Tests anteriores cambiados (lista CERRADA de design §7.1)

Al cambiar `_payloads` (T6) cayeron **32**, los previstos, todos
`AttributeError: … no attribute 'registro_obra_ide'` (4 f022, 9 f024, 8 f026,
11 f034, que importa la `_fila` de f024). Ninguno fuera de la lista.

| Fichero | Antes → ahora | Por qué |
|---|---|---|
| api `tests/conftest.py` `UniversoFalso` | + `var=None, fallo_var=None`, `llamadas_var` y `universo_var(empresa)` (sin obra VAR por defecto) | doble; `llamadas` (postventa) no cambia |
| api `test_f022_empresa_en_linea._fila` | obra `SimpleNamespace` + `registro_obra_ide=None, registro_obra_cod=None, registro_paride=None` | doble; ningún assert |
| api `test_f024_registro_empresa._fila` | ídem | doble; ningún assert |
| api `test_f026_registro_recurso._fila` | ídem | doble; ningún assert |
| transfer `test_f002_fuente_unica.ANCLAS` | + `"regla-var"`, `"regla-seis-digitos"` | R23, ampliación deliberada |

Transfer (T1-T3), front y raíz: ningún test anterior tocado.

## 4. Fase RED (salida real, pegada; comando desde cada servicio)

Trazas recortadas a las líneas `E`/`FAILED`/resumen; comando exacto desde
cada servicio con su `.venv`.

**T1** · transfer `python -m pytest tests/test_f039_universo_var.py -q -k "r1 or r2 or r3"`:
```
E       ModuleNotFoundError: No module named 'application.services.universo_var'
41 failed in 2.56s
```
**T2** · transfer `python -m pytest tests/test_f039_universo_var.py -q`:
```
E       AssertionError: {"detail":"Not Found"}
E       assert 404 == 200
E       assert 404 == 422
E       assert 404 == 502
FAILED tests/test_f039_universo_var.py::test_f039_r1_ruta_devuelve_el_contrato
FAILED tests/test_f039_universo_var.py::test_f039_r4_fallo_de_sigrid_502 - As...
7 failed, 41 passed in 7.26s
```
**T3** · transfer `python -m pytest tests/test_f039_preflight_var.py -q`. Sin el
campo: `TypeError: LineaEntrada.__init__() got an unexpected keyword argument
'var_paride'` (50 failed). Con el campo y SIN la rama del pipeline, la línea
VAR caía al casado por categoría contra `CI.1.3` de la obra VAR (lo que D1
prohíbe):
```
E       AssertionError: assert (60001, 'CI.1...to_categoria') == (417055, '29', 'var')
E       AssertionError: assert (60001, 'CI.1.3', 'manual') == (417055, '29', 'var')
E           assert ('escribir', ...to_categoria') == ('escribir', 417055, 'var')
E           assert 'escribir' == 'omitir'
E       AssertionError: assert ['sobrecarga'] == ['pisado']
FAILED tests/test_f039_preflight_var.py::test_f039_cruce_universo_y_preflight[417002-real]
FAILED tests/test_f039_preflight_var.py::test_f039_r5_en_real_la_linea_va_a_la_obra_var_con_su_partida
FAILED tests/test_f039_preflight_var.py::test_f039_r7_el_paride_manual_no_cambia_la_partida_var
46 failed, 10 passed in 7.62s
```
**T4** · api `python -m pytest tests/test_f039_sync_var.py -q -k "r10 or r13 or r16 or r18"`:
```
E       ModuleNotFoundError: No module named 'domain.obras'
E       ImportError: cannot import name 'PartidaVar' from 'domain.models'
E       ImportError: cannot import name 'UniversoVarNoDisponible' from 'domain.errors'
E       AssertionError: assert [] == ['ALTER TABLE...aride BIGINT']
28 failed in 5.66s
```
**T5** · api `python -m pytest tests/test_f039_sync_var.py -q`:
```
E       TypeError: FetchObrasStep.__init__() got an unexpected keyword argument 'digitos_excluidos'
E       AttributeError: 'TransferClient' object has no attribute 'universo_var'
E       ImportError: cannot import name 'entradas_var' from 'application.filtros_maestros'
E       AssertionError: assert ('VAR-29', Tr...e, None, None) == ('VAR-29', Tr...'VAR', 417055)
E       KeyError: 'digitos_seguidos_excluidos'
30 failed, 29 passed, 1 warning in 12.76s
```
**T6** · api `python -m pytest tests/test_f039_registro_var.py -q`:
```
E         At index 0 diff: {'ide': -417055, 'codigo': 'VAR-29', 'nombre': 'NAVE'} != {'ide': 683806, 'codigo': 'VAR', 'nombre': None}
E       AssertionError: assert ('paride' not in {'registro_id': 1, 'ano': 2026, 'mes': 8, 'porcentaje': 0.4, ...})
E       AssertionError: assert 2 == 1
E       KeyError: 'var_paride'
7 failed, 3 passed, 1 warning in 23.61s
```
**T7** · front `python -m pytest tests/test_f039_partida_fija.py -q`:
```
E       AssertionError: function pintarModalPreflight(pf) { … const sel = a.accion === "escribir" ? `<select class="sel-partida" …
E       assert None
FAILED tests/test_f039_partida_fija.py::test_f039_r22_la_accion_var_pinta_la_partida_fija
1 failed, 2 passed in 0.87s
```
**T8** · transfer `python -m pytest tests/test_f002_fuente_unica.py -q` (con `ANCLAS` ampliado):
```
E       AssertionError: regla-var
E       AssertionError: regla-seis-digitos
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-var]
4 failed, 66 passed in 1.32s
```
**T11** · los dos tests nuevos contra los mutantes #14 y #22 aplicados a mano
(`PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_f039_sync_var.py -q --tb=no`, api):
```
FAILED tests/test_f039_sync_var.py::test_f039_r10_el_umbral_es_el_que_se_pasa
FAILED tests/test_f039_sync_var.py::test_f039_r17_lo_preparado_es_inmutable
2 failed, 58 passed, 1 warning in 11.45s
```

## 5. Verificaciones MANUAL pendientes (humano; nada escribe en Sigrid)

Ninguna la ha lanzado el implementer. Ninguna llama a `registro/ejecutar`.

- **T9 · azure-apps (líder + commit del humano).** Copiar LITERALES a
  `C:\Users\pgris\PycharmProjects\azure-apps\dedicacion.md` la cabecera con
  fecha de `docs/INTEGRACION.md`, la fila `VAR_OBRA_COD`/`VAR_PARTIDA_DESDE`
  de §3, el párrafo «Desde F-039…» de §5 y las seis filas nuevas de §7
  (commit `adf9254`). Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps diff`
  enseña solo esas piezas; el commit lo hace el humano.
- **T12 · M1 (preview, sync y cuadrante; BBDD local).** En
  `services/dedicacion-transfer` y en `services/dedicacion-api` (cada uno con
  su `.venv`, la api con `PG_HOST=localhost`): `python main.py`. Desde la
  raíz: `powershell -ExecutionPolicy Bypass -File scripts/verif_f039_var.ps1 -Paso M1`.
  Esperado: `excluidas_por_codigo = 240`, `entradas_var = 1`,
  `obra_var = VAR`, `motivo_var` y `motivo_postventa` nulos; tras el sync,
  `VAR-29` (`ide -417055`, activa) en el cuadrante, sin `VAR` normal, sin
  `150414` y ninguna obra activa con 6+ dígitos seguidos; `RESULTADO M1: OK`.
- **T13 · M2 (preflight de SOLO LECTURA).** Mismo arranque y
  `powershell -ExecutionPolicy Bypass -File scripts/verif_f039_var.ps1 -Paso M2 -Anio AAAA -Mes MM`
  con un periodo de prueba LOCAL. Esperado: grupo de la obra `VAR` con acción
  `escribir`, `paride = 417055`, `partida_cod = "29"`,
  `partida_metodo = "var"`, `caa_cod` `VAR.CIMO…` (real) o de la obra de
  pruebas (`0404.…`); `no_vigentes = []`; `RESULTADO M2: OK`. Respuesta
  completa en `%TEMP%\verif_f039_m2.json`.
- **T14 · M3 (usabilidad, navegador).** Además `python main.py` en
  `services/dedicacion-front` y abrir `http://127.0.0.1:8080`: buscar «29» y
  «arroyo» → sale `VAR-29`; no salen `VAR` ni `150414`; añadirla a un
  trabajador; PV avisa «no admite postventa»; Completar al 100 % hacia
  `VAR-29`; export Excel con `VAR-29`; «Registrar en Sigrid» enseña la
  partida fija «29» (sin desplegable) — cerrar el modal **sin** registrar.
- **Despliegue** (fuera de esta tarea): transfer → api → front (§7 de
  `INTEGRACION.md`); el transfer desplegado está en modo real.

## 6. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests | transfer **643 passed, 2 skipped**; api **656 passed**; front **56 passed**; raíz **418 passed, 1 skipped** |
| Tests nuevos de F-039 | transfer 104 (`test_f039_universo_var` 48 + `test_f039_preflight_var` 56); api 70 (`test_f039_sync_var` 60 + `test_f039_registro_var` 10); front 3 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 181 líneas cambiadas cubiertas (181/181, umbral 80%, nivel critico)` |
| Mutación (final, `--workers 1`) | **60 generados, 60 muertos, 0 supervivientes, 0 timeouts**, 1274,4 s, SHA `6ab6588` → `progress/mutacion_F-039.md` |
| Tiempo de las suites | transfer 7,8 s; api 26,7 s; front 3,1 s; raíz 130,6 s |

**Mutación: dos campañas, las dos en serie y sin tocar el árbol mientras
corrían.** La 1.ª (SHA `36419ed`, línea base de la api 77 s) dio 56/60, con
4 supervivientes:

| # | Mutante | Análisis | Qué se hizo |
|---|---|---|---|
| 14 | `sync_pipeline.py:96` `ObrasPreparadas` `frozen=True→False` | **Hueco real**: nada comprobaba la inmutabilidad | test `test_f039_r17_lo_preparado_es_inmutable` (`6ab6588`) |
| 22 | `domain/obras.py:19` `n <= 0 → n <= 1` | **Hueco real**: ningún test con N = 1 | `test_f039_r10_el_umbral_es_el_que_se_pasa` gana `("A1", 1)` y `("VAR", 1)` |
| 2 | `filtros_maestros.py:236` `normal and not (` → `normal or not (` | **No sobrevive**: aplicado a mano en el árbol principal y en una copia, con el comando exacto de la herramienta (`PYTHONDONTWRITEBYTECODE=1 python -m pytest -x -q --tb=no -p no:cacheprovider`), cae en `test_f023_r17_preview_publica_claves_nuevas_y_antiguas` (y en 7 de f025/f039) | ninguno |
| 17 | `use_cases.py:530` `digitos_excluidos = 0 → 1` | **No sobrevive**: a mano cae en `test_f023_r17_…` (y lo vigila `test_f039_r10_sin_filtro_…`) | ninguno |

La 2.ª campaña (SHA `6ab6588`; solo dos tests más, ninguna línea de
producción cambiada) dio **60/60 muertos**, #2 y #17 incluidos sin tocar
nada: esos dos veredictos de la 1.ª fueron un artefacto de medida. Causa no
demostrada; indicio: la línea base de la api midió 77 s en la 1.ª y 37,8 s en
la 2.ª (máquina cargada; en paralelo trabaja otro agente en
`porcentajes-f040`). Queda anotado para quien mantenga `harness/mutacion.py`.

**`bash harness/init.sh` (final): `ENTORNO LISTO`, exit 0**: raíz 418 passed
/1 skipped, api 656, transfer 643, front en verde; `PUERTA COBERTURA` 100 %
(181/181); `PUERTA TAMAÑO` dentro. Ruff: +2 `UP045` (`Optional[int]` en
`var_paride`, como sus campos vecinos).
