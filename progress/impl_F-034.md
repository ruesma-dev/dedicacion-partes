# F-034 · Informe del implementer (relanzamiento)

> Bloqueo anterior (resumen): la lista cerrada de design §6 se quedaba corta
> en 4 tests (R17 registro, R10 cuadrante, R6 y R6/R13 rutas); el humano la
> completó en `ba55567`. Este informe sustituye al del bloqueo.

## Estado

Rama `feature/F-034-obras-siempre-ruesma`. **T1-T7 y T10-T11 hechas**, un
commit por tarea (`ef56e2d` T1 … `f516d6c` T10). **T8 y T9 sin marcar**:
T8 escribe en `progress/current.md`, que el líder me pidió no tocar (la hace
él); T9 es MANUAL del humano (abajo, con comando y resultado esperado).
`bash harness/init.sh`: **ENTORNO LISTO** (final de este informe).

## Qué cambió

| Fichero | Cambio |
|---|---|
| `api/domain/models.py` | `FiltroEmpresa.empresa_obras: int`, obligatorio, docstring de los tres campos |
| `api/domain/empresas.py` | `visible_en_empresa(empresa_trabajador, filtro)`: NULL solo en la por defecto (R3); docstrings |
| `api/application/use_cases.py` | obras con `o.empresa == filtro.empresa_obras` (R1); `_filas_de_empresa` con la firma nueva |
| `api/application/registro_sigrid.py` | `_filtro` con `empresa_obras`; `_payloads` sin `empresas_de` y `"empresa": filtro.empresa_obras` (R7, R8) |
| `api/interface_adapters/api/routes.py` | `_filtro` con `empresa_obras` (y docstring D1); `a_trabajador_out(…, filtro.empresa_obras)` en las 4 rutas |
| `api/interface_adapters/api/schemas.py` | `a_trabajador_out(fila, empresa_obras)` (R5) |
| `api/config/settings.py`, `api/.env.example` | solo comentario de `empresa_imputacion` (R10, R12; `.env.example` sin tildes) |
| `front/static/js/app.js` | aviso: « · la obra no es de la empresa de las obras: no se registrará» (R6) |
| `front/templates/index.html` | `title="Empresa de los trabajadores"` en `#selector-empresa` (R6) |
| `docs/ARCHITECTURE.md` | `#regla-empresa`: los 4 puntos de design §7 y firma F-034 |
| `docs/INTEGRACION.md` | cabecera (2026-10-02, rama F-034, anterior `fb240be`), fila §3, párrafo §9 |
| tests nuevos | `api/tests/test_f034_obras_siempre_ruesma.py`, `api/tests/test_f034_rutas.py` |
| tests adaptados | los de §6 (tabla R11) |

Sin cambios: `services/dedicacion-transfer/` (`git diff dev --stat` vacío, T6),
contrato API ↔ transfer, esquemas de entrada/salida (lo fija
`test_f034_r1_cuadrante_…` comparando los campos), sync, recurso (F-026),
`infra/`, `.env`.

## Decisiones y desviaciones

1. **Commits intermedios en rojo fuera de su tarea.** Cambiar la firma de
   `visible_en_empresa` y hacer `empresa_obras` obligatorio (T1) rompe a los
   llamantes hasta T2-T4. Cada commit pasa **su** verificación de tasks.md;
   la suite completa está en verde desde T4 (`59ee5c0`).
2. **Texto del aviso (R6).** «la obra no es de la empresa de las obras: no
   se registrará»: el front no sabe cuál es (no hay campo nuevo, design
   §4.3), así que no nombra a Ruesma.
3. **ARCHITECTURE.** La frase «trabajadores de varias empresas, obras
   (postventa incluida) siempre de una, la de `EMPRESA_IMPUTACION`» va
   dentro del punto «La empresa viaja en cada línea», no como punto nuevo:
   design §7 enumera qué puntos se reescriben.
4. **Mutantes manuales sin script versionado.** Un `.py` en `scripts/` entra
   en el alcance de producción del arnés (mutación y cobertura) y rompió la
   línea base de la campaña (`test_mutacion_prueba_de_verdad` en worktree):
   lo retiré (`1401935`). Los mutantes quedan descritos uno a uno abajo.

## R11 · Tests anteriores que cambian (lista cerrada de design §6)

| Test | Assert viejo → nuevo | Req. |
|---|---|---|
| `test_f024_visibilidad.py` `_f` y llamadas | `FiltroEmpresa(e, DEF)` → `+ empresa_obras=DEF`; `visible_en_empresa` sin argumento de obras | R3 |
| `…::test_f024_r8_trabajador_con_empresa_solo_en_la_suya` | sin columna `obras`; 7 casos → 5 (dos quedaban idénticos sin ella) | R2 |
| `…r8_null_donde_tiene_carga` + `…r8_null_sin_obras_con_empresa_en_la_por_defecto` | fundidos en `test_f034_r3_trabajador_null_solo_en_la_por_defecto` (1 → visible; 18, 28 → no) | R3 |
| `…r8_acepta_cualquier_iterable_una_sola_vez` | sustituido por `test_f034_r3_null_con_por_defecto_distinta_de_1` (por defecto 18: solo en la 18) | R3 |
| `…r8_por_defecto_sale_del_filtro_no_de_un_literal` | solo construcción `FiltroEmpresa(…, empresa_obras=28)`; asserts iguales | — |
| `test_f024_cuadrante_empresa.py` `_f` | `+ empresa_obras=DEF` | R1 |
| `…r7_cuadrante_solo_trabajadores_visibles` | 1: `[Ana, Dani, Eva, Gil]` → `[Ana, Carlos, Dani, Eva, Gil]`; 28: `[Bea, Carlos, Gil]` → `[Bea]` | R3 |
| `…r9_obras_solo_de_la_empresa…` | → `test_f034_r1_obras_siempre_de_la_empresa_de_las_obras`: E = 1, 18, 28 → `[100, 101, 102]` | R1 |
| `…r10_puede_deshacer_se_conserva` | `[T, F, F, F]` → `[T, F, F, F, F]` (entra Carlos) | R3 |
| `…r13` (`RESUMEN_1`, `RESUMEN_28`, `esperado`) | 1: total 4/falta 1 → 5/2; 28: 3/ok 2/falta 1 → 1/1/0; tras guardar: 4/3/1 → 5/3/2 | R3 |
| `test_f024_registro_empresa.py::…r16…` | → `test_f034_r7_solo_visibles_y_todas_con_la_empresa_de_las_obras`: None/1 `[(1,1),(2,1),(5,1)]` → `[(1,1),(2,1),(4,1),(5,1)]`; 28 `[(3,28),(4,28)]` → `[(3,1)]`; 18 `[]` | R7, R3 |
| `…r17…` | obra 9 `[(2, 1)]` → `[(2, 1), (4, 1)]`; traza de la omitida 2 igual | R3 |
| `…r19…` | solo docstring (D4) | — |
| `test_f024_rutas_empresa.py::…r6_sin_empresa_la_por_defecto` | `+ Carlos` | R3 |
| `…r6_con_empresa_la_elegida` (E = 28) | nombres → `[Bea]`; obras `[900]` → `[100, 101, 102]`; total 3 → 1 | R1, R3 |
| `…r6_r13_respuestas_por_fila…` | `(None,4),(1,4),(28,3)` → `(None,5),(1,5),(28,1)` | R3 |
| `…r11_otra_empresa_depende_de_la_elegida` | → `test_f034_r5_otra_empresa_no_depende_de_la_elegida`: Gil con E = None/1 `[(1, False), (28, True)]` (antes, E = 28: `[(1, True), (28, False)]`); el caso E = 28 vive en `test_f034_rutas.py` (Bea) | R5 |
| `…r15_export…` | None: `+ Carlos`; 28: `[Bea]` | R3 |
| `front/tests/test_f024_selector.py::test_f024_r12_…` | «no se registrará en esta empresa» presente → texto nuevo presente y el viejo ausente; `+ test_f034_r6_aviso_de_la_linea_y_title_del_selector` (title) | R6 |

Sin cambios (§6): F-022, R14, R18, R11 de rutas y todo el transfer.

## Fase RED (trazas reales)

Comandos desde `services/dedicacion-api` (T5 desde `services/dedicacion-front`)
con `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider <ficheros>`.

**T1 (R2, R3, R10)** — `tests/test_f034_obras_siempre_ruesma.py`, antes de tocar el dominio:
```
     12 E       TypeError: FiltroEmpresa.__init__() got an unexpected keyword argument 'empresa_obras'
      1 E       Failed: DID NOT RAISE TypeError
13 failed in 0.42s
```
**T2 (R1)** — tras adaptar solo la llamada de `_filas_de_empresa`, antes del filtro de obras:
```
>       assert [o.ide for o in cuadrante.obras] == [100, 101, 102]
E       assert [] == [100, 101, 102]          # E = 18
E       assert [900] == [100, 101, 102]       # E = 28
E       assert [100, 101, 102] == [900]       # empresa_obras = 28
5 failed, 33 passed in 1.36s
```
**T3 (R7, R8, R10)** — tras adaptar `_filtro` y la llamada, antes de `"empresa": filtro.empresa_obras`:
```
E       assert [(30, 18), (31, 18)] == [(30, 1), (31, 1)]      # trabajador de la 18
E       assert [(32, 31)] == [(32, 1)]                         # de la 31
E       assert [(30, 18), (31, 18)] == [(30, 28), (31, 28)]    # ajuste en la 28
E       assert [(31, 18)] == [(31, 1)]                         # R8, obra de la 28
E       assert [(3, 28)] == [(3, 1)]                           # R16→R7 de F-024
9 failed, 45 passed in 3.66s
```
**T4 (R5)** — tras `routes._filtro`, antes de cambiar `a_trabajador_out`:
```
E       assert [(900, 28, False)] == [(900, 28, True)]                 # E = 28
E       assert [(101, 1, Tru...00, 28, True)] == [(101, 1, Fal...00, 28, True)]   # PUT con E = 18
3 failed, 61 passed, 1 warning in 11.40s
```
**T5 (R6)** — `services/dedicacion-front`, `tests`:
```
E       assert 'la obra no es de la empresa de las obras: no se registrará' in 'function construirCelda(t, clave) {…'
FAILED tests/test_f024_selector.py::test_f024_r12_marcas_sin_empresa_y_otra_empresa
FAILED tests/test_f024_selector.py::test_f034_r6_aviso_de_la_linea_y_title_del_selector
2 failed, 19 passed, 19 warnings in 2.72s
```

**R3 contra el código anterior a F-034** (worktree temporal en `d34e4a1`
con los tests de registro finales, `-k "r7 or r10_puede or r17"`):
```
E       assert [(1, 1), (2, 1), (5, 1)] == [(1, 1), (2, ...4, 1), (5, 1)]   # el NULL no se veía en la 1
E       assert [(3, 28), (4, 28)] == [(3, 1)]                               # y sí en la 28
E       assert [(2, 1)] == [(2, 1), (4, 1)]                                 # R17
12 failed, 2 passed, 20 deselected in 4.06s
```

## Mutación (T10)

**Campaña automática** (`python -m harness.mutacion --feature F-034`, sin
tope): 72 líneas en 7 ficheros, **3 mutantes, 3 muertos, 0 supervivientes**
→ `progress/mutacion_F-034.md`.

**Anomalía de la herramienta (para el líder).** Una ejecución intermedia
(09:15, HEAD `1401935`, árbol limpio) dio **los mismos 3 mutantes como
supervivientes**. Lo reproduje a mano: con `==` → `!=` en `use_cases.py:70`
la suite de la api da **13 failed, 355 passed**: muerto. Relanzada sin
tocar nada salvo quitar el informe sin versionar: 3/3 muertos (es el
informe versionado). No lo arreglé ni lo investigué más; hipótesis: carrera
con la sesión de F-026 (`porcentajes-wt-f026`), ya vista por el
implementer anterior con `compileall`.

**Mutantes manuales** (design §10 los espera; el operador automático no
cambia atributos). Cada uno se aplicó a mano, `pytest -x tests` de la api
y se restauró:

| # | Mutación | Resultado (primer test que cae) |
|---|---|---|
| M1 | `use_cases`: `filtro.empresa_obras` → `filtro.empresa` | muerto (`test_f034_r1_obras_siempre_…[18]`) |
| M2 | ídem → `filtro.por_defecto` | muerto (`test_f034_r1_obras_leen_la_empresa_de_las_obras_no_la_elegida[18]`) |
| M3 | `registro`: `"empresa": filtro.empresa_obras` → `filtro.empresa` | muerto (`test_f034_r7_solo_visibles…[28]`) |
| M4 | ídem → `filtro.por_defecto` | **sobrevive: equivalente** (abajo) |
| M5 | `registro._filtro`: `empresa_obras=empresa or self._por_defecto` | muerto (`test_f034_r7_…[28]`) |
| M6 | `routes` cuadrante: `a_trabajador_out(f, filtro.empresa)` | muerto (`test_f034_r5_cuadrante_con_la_28_…`) |
| M7 | `routes._filtro`: `empresa_obras=empresa or empresa_imputacion` | muerto (`test_f024_r6_con_empresa_la_elegida`) |
| M8 | `routes._filtro`: `por_defecto=empresa or empresa_imputacion` | muerto (ídem) |
| M9 | `empresas`: NULL con `filtro.empresa_obras` | muerto (`test_f034_r3_null_lee_la_por_defecto_…`) |
| M10 | `empresas`: NULL con `!=` | muerto (`test_f022_r20_…`) |
| M11 | `empresas`: con empresa `== filtro.empresa_obras` | muerto (`test_f024_r7_…[28]`) |
| M12 | `schemas`: `linea_de_otra_empresa(…, 1)` | **sobrevivía** → test nuevo (abajo) → muerto |
| M13.1-3 | `routes` guardar / deshacer / copiar: `filtro.empresa` | muertos (`test_f034_r5_guardar_…`, `…deshacer_y_copiar_…`) |

- **M12, hueco real.** Todos los tests de rutas usaban
  `EMPRESA_IMPUTACION` = 1, así que un 1 cableado pasaba. Test nuevo
  `test_f034_r10_la_empresa_de_las_obras_sale_del_ajuste_en_las_rutas`
  (ajuste en la 28: obras `[900]`, Ana `[(100, 1, True), (900, 28, False)]`);
  relanzado M12: muerto (`8349775`).
Texto exacto de M1-M13 (script retirado del árbol): `git show 8349775:scripts/mutantes_manuales_f034.py`.

- **M4, equivalente.** En `RegistroSigrid` los dos campos salen del mismo
  `self._por_defecto` (`_filtro`, D1), así que `filtro.por_defecto ==
  filtro.empresa_obras` para cualquier entrada: ningún test puede
  distinguirlos sin cambiar el constructor, que la spec deja igual (§4.4).
  Si un día se separan (design §10), M5 y `test_f034_r10_la_empresa_de_las_obras_sale_del_ajuste`
  son el sitio donde el test que lo mate entra. **Justificación para el
  humano** (rigor crítico: superviviente sin test).

## Verificaciones MANUAL pendientes

- **T8 (líder).** Anotar en `progress/current.md` y copiar a
  `azure-apps/dedicacion.md`, literales, las piezas de T7: los puntos de
  `#regla-empresa` cambiados en `docs/ARCHITECTURE.md`, y de
  `docs/INTEGRACION.md` la cabecera, la fila `EMPRESA_IMPUTACION` de §3 y el
  párrafo «Una línea sin empresa no se registra» de §9 (`git diff d34e4a1 --
  docs/`). Commit en `azure-apps`.
- **T9 (humano, R13, D5).** Transfer local con `OBRA_PRUEBAS_FORZAR=true`
  (en su `.env`), api y front de esta rama (`python main.py` en cada
  servicio). En `http://localhost:8080/?empresa=18`: comprobar que las obras
  ofrecidas son las de Construcciones Ruesma y dar a un trabajador de la 18
  una línea en una de ellas en 2026-09 (solo BBDD local). Luego, desde Git Bash:
  `curl -s -X POST "http://localhost:8090/api/v1/periodos/2026/9/registro/preflight?empresa=18" -H "Content-Type: application/json" -d "{}"`.
  **Esperado:** `ok: true` por obra, `obra_origen.empresa` = 1 y la acción
  de esa línea `escribir`, no `omitir` por empresa. **No lanzar
  `registro/ejecutar`.**
- **Tras desplegar (humano, no bloquea el done).** Cuadrante de producción
  con `?empresa=18`: obras de Construcciones Ruesma, **sin pulsar Registrar**.
- **Despliegue (humano).** ¿F-034 sola o con F-026? (design §10).

**Fuera de alcance:** recurso por empresa (F-026), postventa (F-025),
rechazo al guardar (F-031), copia que descarte líneas. Sin llamadas a Sigrid.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests api | **368 passed**, 1 warning (`pytest tests`, 27.6 s; en `init.sh` 46.7 s) |
| Tests front | **21 passed** (3.6 s; en `init.sh` 7.4 s) |
| Tests transfer | **317 passed** (4.0 s, T6) |
| Suite raíz (`init.sh`) | **355 passed, 1 skipped** (109.6 s) |
| Cobertura de líneas cambiadas | **100.0 %** (6/6, umbral 80 %, nivel crítico) — `PUERTA COBERTURA` |
| Mutación automática | **3 generados, 3 muertos, 0 supervivientes** (78.6 s) |
| Mutación manual | 15 mutantes: 14 muertos (M12 tras test nuevo), 1 equivalente justificado (M4) |
| `bash harness/init.sh` | **ENTORNO LISTO**: pytest en verde en los tres servicios, cobertura 100 %, tamaño dentro de topes, ruff 193 avisos de deuda previa (no bloquea) |
