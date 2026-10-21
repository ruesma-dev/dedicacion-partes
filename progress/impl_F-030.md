<!-- progress/impl_F-030.md -->
# F-030 · Informe del implementer (incidencias en el cuadrante)

Rama `feature/F-030-dias-bajas-incidencias` (copia `porcentajes-f030`),
rigor **crítico**, código cerrado en `8b17e85`. T1-T19 y T21 hechas, cada
una con su commit `F-030 Tn`; **T20 (MANUAL) es del líder** (§6). Nada
escrito en Sigrid, ningún `push`, ningún `.env` tocado.

## 1. Qué cambió (por servicio)

- **api** (T2-T7, T16):
  - `domain/incidencias.py`, tablas `tipo_incidencia` e `incidencia`
    (`create_all`) y sync/preview del catálogo `auxhor`
    (`sync.incidencias.sql`; falla entero ante error o `truncated`).
  - `GET /api/v1/incidencias` y `PUT …/trabajadores/{ide}/incidencias`
    (evento `INCIDENCIAS` deshacible); cuadrante y fila con `incidencias`.
  - Deshacer despacha por `evento.tipo`. F7, F8, copiar y completar no las
    tocan, y el 100 % no las cuenta.
  - Registro: `_payloads` manda `incidencias` por obra (visibles, vigentes,
    `paride` = elegida, propuesta o 0) y `traza_incidencias.py` guarda su
    traza.
- **front** (T1, T8, T9, T17):
  - Letras en la celda del % abren el desplegable; con número, lo de hoy
    (T1).
  - Chip «del/al» en el mismo diferido, subfilas, filtro de Obra y sección
    «Incidencias» del modal (`seccionIncidencias`), sin confirmaciones.
- **transfer** (T10-T15, T18):
  - `reglas_incidencias.py` (`decidir_incidencia`, `deduplicar`,
    `synckey_incidencia`) y `incidencias_del_mes` (en trozos; `truncated` =
    error).
  - `preflight`/`ejecutar`: par con `can = 0` tras las líneas, y la
    relectura es la de F-051.
  - Lote: tuplas de 2 o 3, R27 una vez en la ronda C.
  - `app.py`: `IncidenciaIn` y `_con_incidencias`.
  - El script admite `--incidencia`.
- **docs** (T19): regla 21 `#regla-incidencia` en `ARCHITECTURE.md` (P2, P3
  y P4 remiten; §Capas), `INTEGRACION.md` §1 y §5, y `test_f002` con el ancla.

## 2. Decisiones de diseño y desviaciones (justificadas)

- **D-a. La traza va en `application/traza_incidencias.py`**, no en
  `registro_sigrid.py` (design §3). `test_f003_r17` fija que los `sigrid_*`
  de `registro_sigrid.py` son las columnas de `asignacion`, e `incidencia`
  tiene otras (`sigrid_ide_ini`/`_fin`). Separado, f003 no se toca, y
  `test_f030_r31_la_traza_escribe_columnas_de_incidencia` vigila el módulo
  nuevo igual.
- **D-b. R2 literal.** Sin incidencias, el kwarg `incidencias` no se pasa
  (api, lote, `ejecutar`→`preflight`) y ni la petición ni la respuesta ganan
  la clave. Los dobles que fijan la llamada (`f055_equivalencia_lote`)
  siguen intactos.
- **D-c. Viajan aparte** (`Preflight.incidencias`,
  `ResultadoRegistro.incidencias`), nunca en `acciones`. Conflictos,
  capacidad, sin partida y la línea al 0 % de F-051 no las ven (R28).
- **D-d.** El `paride` se valida en la **misma** lectura `validar_partidas`;
  si no vale, pasa a 0 sin aviso (R25). El parte es el del periodo de la
  obra destino (`_parte_nuevo_o_del_periodo`) y se crea en el paso 9.
- **D-e. Script.** Con `--incidencia` manda solo las incidencias (ids desde
  `990101`). `verificar` relee también sus synckeys y `limpiar` ya las borra
  (`PRUEBA-PORC` + prefijo).
- **D-f. Modal.** `seccionIncidencias(o)` solo se llama si la obra trae
  incidencias: los arneses de F-049/F-050 siguen sin cambios.
- **D-g. Mutación.** `lecturas_lote` decidía mirando solo la 1.ª línea del
  par; ahora mira las dos (`{acciones} != {"escribir"}`), mismo
  comportamiento.

## 3. Lista cerrada de tests ajenos (opción A del humano, 2026-10-21)

Solo dobles, cada uno con la marca «F-030 (lista cerrada)»; **una sola
aserción** cambió, la de f013, por decisión expresa del humano:

| Tarea | Fichero | Cambio |
|---|---|---|
| T4 | `api/tests/test_f023_sync_empresa.py` | `_SigridFalso.leer` → `[]` a `auxhor`; `_UowEspia.tipos_incidencia`; `_config_prueba` con `sync.incidencias.sql` (arregla por herencia f025, f039) |
| T4 | `api/tests/test_f032_empresas_sigrid.py` | ídem (`_SigridFalso`, `_UowEspia`) |
| T5 | `api/tests/test_f024_cuadrante_empresa.py` | `_Uow.incidencias` vacío (heredan f024, f027, f029, f034, f050, f055, f057) |
| T5 | `api/tests/test_f025_cuadrante_postventa.py` | `_Uow.incidencias` vacío |
| T7 | `api/tests/test_f027_deshacer_propio.py` | el `SimpleNamespace` del evento gana `tipo="GUARDAR"` |
| T14 | `transfer/tests/test_f013_sin_partida.py` | **aserción**: la firma de `ejecutar` acepta `incidencias` al final, con una línea de que no es un canal de confirmación (opción A, «a») |
| T16 | `api/tests/test_f024_registro_empresa.py` | `_Sesion.execute` → `[]` a la lectura de `incidencia` (heredan f026, f034, f039, f050, f051 y el `_S` de f055) |
| T16 | `api/tests/test_f022_empresa_en_linea.py` | ídem |
| T16 | `api/tests/test_f056_trabajador_ide.py` | `_SesionQueFiltra.execute`, ídem |

Ningún test del front cambió; `test_f002_fuente_unica.py` está en la spec (T19).

## 4. Fusión de `dev` (F-051) antes de T15

`git merge dev` (`20a8e06`), commit `46cf116`, conservando los dos
comportamientos; no hizo falta ninguna decisión nueva.

- `sigrid_write_client.py`: `incidencias_del_mes` junto a `lineas_registradas`.
- `ejecutar`:
  - `ResultadoRegistro` lleva `ya_registradas_ide` e `incidencias`.
  - El paso 9 crea partes para `a_insertar` + `inc_escribir`.
  - Las incidencias se insertan tras las de F-051.
  - Una sola relectura (`_comprobar_escrito(res, inc_escribir)`).
  - «Nada que escribir» cuenta las incidencias.
- `current.md`: la cabecera de F-030 y una sección con el estado de F-051.
- Test nuevo `test_f030_r28_…linea_al_cero…`.
- `init.sh` en verde tras la fusión (raíz 418, api 1069, front 346, transfer
  1136; cobertura 99,4 %).

## 5. Fase RED (trazas reales)

`.venv/Scripts/python -m pytest <fichero> -q -p no:cacheprovider [-k …]`
desde cada servicio, con el test escrito y sin código; aquí van las líneas
`E` y el resumen (completas en `red/T*.txt` del scratchpad). T1 no tiene RED:
fija lo de hoy, en verde antes de tocar `app.js`.

```
T2  api test_f030_incidencias.py
E   ImportError: cannot import name 'IncidenciaInvalida' from 'domain.errors'
1 error in 0.31s
T3  api -k esquema
FAILED …::test_f030_r3_esquema_tabla_tipo_incidencia / …r17_esquema_tabla_incidencia (ImportError)
2 failed, 1 passed, 40 deselected in 1.39s
T4  api test_f030_catalogo.py          (ImportError del repositorio y del paso del sync)
26 failed in 17.48s
T5  api -k ruta / -k cuadrante: 1 failed, 26 deselected · 6 failed, 1 passed, 43 deselected
T6  api -k guardar: 33 failed, 1 passed, 50 deselected in 13.34s
T7  api -k "deshacer or copias"
E   domain.errors.LineasInvalidas: Línea inválida: {'obra_ide': 100, 'codigo': 'CIV', 'dia_desde': 5, 'dia_hasta': 9}
E   AssertionError: assert (Incidencia(o...motivo=None),) == ()
E     tipo: 'GUARDAR' != 'INCIDENCIAS'
4 failed, 5 passed, 84 deselected in 8.23s
T8  front test_f030_celda_pct.py
E   AssertionError: no existe la función montarDesplegableIncidencias en app.js
E   AssertionError: no existe la función cargarTiposIncidencia en app.js
14 failed, 5 passed in 3.80s
T9  front test_f030_tabla_incidencias.py
E   AssertionError: no existe la función chipIncidencia en app.js
E   AssertionError: assert ['fila seleccionada'] == ['fila selecc...nada subfila']
17 failed in 1.81s
T10 transfer test_f030_reglas_incidencias.py -k decidir
E   ModuleNotFoundError: No module named 'application.services.reglas_incidencias'
1 error in 0.36s
T11 transfer -k deduplicar
E   ImportError: cannot import name 'deduplicar' from 'application.services.reglas_incidencias'
5 failed, 20 deselected in 0.31s
T12 transfer test_f030_pipeline_incidencias.py -k cliente
E   AttributeError: 'SigridWriteClient' object has no attribute 'incidencias_del_mes'
6 failed in 0.98s
T13 transfer -k preflight
E   TypeError: RegistroPipeline.preflight() got an unexpected keyword argument 'incidencias'   (x14)
14 failed, 6 deselected in 0.89s
T14 transfer -k ejecutar
E   TypeError: RegistroPipeline.ejecutar() got an unexpected keyword argument 'incidencias'    (x8)
9 failed, 20 deselected in 0.89s
T15 transfer -k "lote or contrato"
E   ValueError: too many values to unpack (expected 2)   (x7)
E   KeyError: 'incidencias'   (x4)
E   assert 200 == 422
12 failed, 1 passed, 30 deselected in 2.81s
T16 api test_f030_registro.py
E   KeyError: 'incidencias'
E   ValueError: not enough values to unpack (expected 2, got 1)
E   assert [] == [8]
7 failed, 2 passed in 2.35s
T17 front test_f030_tabla_incidencias.py -k modal
E   AssertionError: no existe la función datosIncidencia en app.js
E   assert 'html += seccionIncidencias(o);' in 'function pintarModalPreflight(pf) {…'
4 failed, 17 deselected in 0.24s
T18 transfer -k script (re-ejecutado con el script anterior a T18, `9a4cdee`)
E   SystemExit: 2   (x3)
prueba_escritura_porcentajes.py: error: unrecognized arguments: --incidencia 200:CIV:5:9
3 failed, 5 passed, 49 deselected in 1.93s   (los 5 eran los de formato mal escrito)
T19 transfer test_f002_fuente_unica.py (con el ARCHITECTURE.md anterior)
FAILED …test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-incidencia]
FAILED …test_f030_r34_p2_p3_p4_remiten_a_la_incidencia[2] / [3] / [6]
5 failed, 74 passed in 0.38s
```

## 5 bis. `bash harness/init.sh` y mutación (T21)

`init.sh` sobre `8b17e85`, con `.arnes_cache/suite_*.ok` borrados: **ENTORNO
LISTO** y ningún `[KO]` (ruff: 293 avisos frente a 277 en `dev`; los 16 de más eran de `test_f030_incidencias.py` de la api, corregidos en T36). PUERTA COBERTURA:
99,5 % (634/637). PUERTA TAMAÑO: 150/150 y 250/250. Mutación en serie y sin
muestreo: 31 supervivientes en la 1.ª campaña (251 mutantes), 1 en la 2.ª
(250) y **0 en la 3.ª** (250). Ninguno se dio por equivalente; el análisis
de cada uno está en `progress/mutacion_F-030.md` § «Historial».

## 6. Verificación MANUAL pendiente (T20, del líder)

Requiere autorización expresa del humano para esta acción. Transfer **local**
con `OBRA_PRUEBAS_FORZAR=true`, desde `services/dedicacion-transfer`, y con
`RECURSO` = un `res.ide` que tenga `CIV` y `CIZ` en `reshor`:

```
python prueba_escritura_porcentajes.py preflight --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9
python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9
python prueba_escritura_porcentajes.py verificar --incidencia RECURSO:CIV:5:9
python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9
python prueba_escritura_porcentajes.py limpiar --confirmar
```

Resultado esperado: `verificar` encuentra dos líneas en la `0404` (`CIV` el
5 y `CIZ` el 9, `can = 0`, `PRUEBA-PORC`); la 2.ª `ejecutar` las da por
`ya_registrado`; `limpiar` las borra. Anotar aquí el resultado real.

## 7. Fuera del alcance y pendiente

- **`azure-apps/dedicacion.md`** (R34) es del líder al desplegar. Debe decir:
  - leemos `auxhor` (`CI*`);
  - escribimos `CI*`/`CIZ` con `can = 0` y `synckey porcentajes:inc:`, tras
    una lectura de las `CI*` del mes;
  - las rutas nuevas.

  Avisar a `partes` de que su `partes.md` debería decirlo también.
- Por D10 quedan fuera el % por días con el calendario y la bandeja de
  `partes` (features nuevas). Corregir lo ya escrito es de F-033 (R30).
- Los tests de node corren aquí (`passed`, no `skipped`). Los avisos de
  ruff del script son previos: de 4 se queda en 3.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 3.019 passed, 1 skipped, 0 failed: raíz 418 (+1 skipped), api 1.083, front 350 (los de node `passed`), transfer 1.168 |
| Cobertura de líneas cambiadas | 99,5 % (634/637), PUERTA COBERTURA de `init.sh` |
| Mutación | 3.ª campaña: 250 generados, 250 muertos, **0 supervivientes**, 0 timeouts; `--workers 1`; 1.888,2 s (HEAD `8b17e85`). Antes: 31 y 1 supervivientes, todos cerrados con tests o código |
| Tiempo de la suite | raíz 50,38 s; api 60,54 s; front 40,06 s; transfer 19,04 s (pytest, en `init.sh`) |
