<!-- progress/impl_F-054.md -->
# F-054 · Informe del implementer

Rama `feature/F-054-sync-trae-porcentajes`, copia `porcentajes-f054`. Rigor
**crítico**. Spec `specs/F-054-sync-trae-porcentajes/` (T1-T21). Informe
escrito a medida que avanza (dos cortes del entorno: tras T3 y tras T7).
Sin escrituras en Sigrid ni llamadas a Azure: todo con dobles.

## Estado por tarea

| Tarea | Commit | Estado |
|---|---|---|
| T1 lectura `lineas_mensuales_del_periodo` (transfer) | `d12ec81` | hecha |
| T2 `porcentajes_existentes.py` (traducción) | `bf2361a` | hecha |
| T3 `POST /api/porcentajes/existentes` | `f99e0cd` | hecha |
| T4 dominio puro `domain/traer_sigrid.py` (api) | `3ba3f37` | hecha |
| T5 puerto, error 502, `TransferClient.porcentajes_existentes`, `TipoEvento.SIGRID` | `50f5d2e` | hecha |
| T6 `aceptar_entrada` (upsert de la clave) | `69583c9` | hecha |
| T7 caso de uso `TraerDeSigrid` | `ef06704` | hecha |
| T8 ruta `POST …/traer-sigrid` | `1c8d4a5` | hecha |
| T9 front A (`sincronizarYTraer`, ventana) | `ccad4db` | hecha |
| T10 | — | MANUAL del líder (ver abajo) |
| T11 `reglas_obra_cero.py` y `Sobrante` | `892d93f` | hecha |
| T12 `preflight_completo`, ronda A, `completo`/`sobrantes` | `eaaca4b` | hecha |
| T13 `PonerACero` y `POST /api/registro/poner-a-cero` | `60a7dab` | hecha |
| T14 api B (`preflight` completo, `ejecutar` con `sobrantes_a_cero`) | `d382ae7` | hecha |
| T15 front B (sección de sobrantes, `sobrantes_a_cero`) | `f5a9bb8` | hecha |
| T16 documentación y `ANCLAS` | `95cc089` | hecha |
| T17 cobertura y mutación (55 + 9 supervivientes matados con tests) | `e72d22c`, `c614be3`, `1c16454` | hecha |
| T18-T20 | — | MANUAL (ver abajo) |
| T21 `init.sh` en verde | ver «Evidencias» | hecha |

## Ficheros tocados

- transfer: `infrastructure/sigrid/sigrid_write_client.py`,
  `domain/models/registro_models.py` (`LineaMensualSigrid`),
  `application/services/porcentajes_existentes.py` (nuevo),
  `interface_adapters/api/app.py` (`ExistentesIn` y ruta).
- api: `domain/{models,errors,ports,traer_sigrid}.py`,
  `application/traer_sigrid.py` (nuevo),
  `infrastructure/transfer/transfer_client.py`,
  `infrastructure/db/{repositories,orm_models}.py` (`aceptar_entrada`,
  `PgVinculadoRepository.ides`, relectura del periodo; el ORM solo el
  comentario de la traza), `interface_adapters/api/{app,routes,schemas,deps}.py`.
- B, transfer: `application/services/reglas_obra_cero.py` (nuevo),
  `application/services/lecturas_lote.py` (ronda A `mensuales`),
  `application/pipelines/registro_lote.py` (`preflight_completo`),
  `application/pipelines/poner_a_cero.py` (nuevo), `app.py` (`completo`,
  `poner-a-cero`). `registro_pipeline.py` NO se toca.
- B, api: `application/registro_sigrid.py`, `transfer_client.py`, `routes.py`.
- front: `static/js/app.js` (T9 y T15).
- docs: `ARCHITECTURE.md` (puntos 23 y 24, remisión en 22, capacidad,
  tabla de acceso), `INTEGRACION.md` (§1, §5, §7).
- tests nuevos: transfer `test_f054_{lectura_mensuales,traduccion,endpoint,
  obra_cero,poner_a_cero}.py`; api `test_f054_{comparar,rutas,aceptar,
  registro_cero}.py`; front `test_f054_{traer_front,modal_cero}.py`.
- ajenos, solo la lista cerrada: `ANCLAS` de `test_f002_fuente_unica.py`;
  dobles `preflight_lote` de `test_f022_…`, `test_f024_…` y `test_f055_…`
  (aceptan `completo=False`; ninguna aserción cambia).

## Decisiones de diseño y desviaciones (justificadas)

1. **Vigencia por `vigente_en`** (activo + fecha de baja), la regla única del
   dominio, en vez de solo `activo` (design §5.2 dice «por `activo`»):
   `listar_para_periodo` ya devuelve `activo` = vigente en el mes, así que
   coincide, y para el trabajador que no sale en el listado (no vigente sin
   líneas) se lee del maestro con `obtener` para que su motivo sea «no
   vigente» y no «fuera del maestro».
2. `ExistentesIn.empresa` sin tipo: cualquier valor no válido da 422 con
   motivo `{ok:false,error}` sin leer Sigrid.
3. La obra de pruebas siempre se excluye en A (R5); `lineas_leidas` cuenta todas.
4. La comparación solo saca a trabajadores con alguna entrada de Sigrid.
5. Obra que está en la base pero no en el listado del periodo (inactiva, sin
   postventa): se completa como inactiva para que el motivo sea «no se
   ofrece», no «no está en la base».
6. **Relectura del periodo**: `PgPeriodoRepository.obtener` pasa a
   `populate_existing=True`. Sin ello, releer el periodo en la misma sesión
   devolvía el objeto del mapa de identidad y no veía un cierre hecho entre
   medias (R22 / «cerrado entre medias ⇒ 409»). Para los demás llamantes
   solo cambia que el dato es siempre el de la base.
7. Snapshot «después» del evento `SIGRID` calculado en memoria (la fila de
   antes con cada aceptada en su sitio y sus subfilas), no releído: la
   lectura ORM tras el `INSERT … ON CONFLICT` de núcleo podía devolver
   objetos del mapa de identidad sin refrescar.
8. Aceptadas repetidas en una petición cuentan una vez.
9. Ruta: sin cuerpo = comparar; `_encolar` solo si hay tocados.
10. Tests de T7 con UoW en memoria **propia**, no la de
    `test_f024_cuadrante_empresa.py` (design §9): esa no tiene transacción
    ni traza, y R19/R22/R23 no se podrían comprobar.
11. Front: `#btn-sync` se enlaza con `() => sincronizarYTraer()` (no con la
    función directa): los arneses de `enlazarEventos` de
    `test_f050_t15e_sombreado.py`, `test_f029_seleccion.py` y
    `test_f050_m2_arreglos.py` (ajenos, fuera de la lista cerrada) solo
    definen `sincronizar`, y con la referencia directa el primero fallaba
    con `ReferenceError: sincronizarYTraer is not defined`. Con la flecha
    pasan sin tocarlos.
12. La ventana usa `#modal-registro`; sin casillas, sin «Aceptar las marcadas».
13. **B, la obra especial por código**: `cubierta` reconoce la obra de
    postventa, la VAR y la de pruebas por el `obra_cod` de la línea (la
    lectura va por empresa) en vez de por `ide` (design §6.1 dice
    `pv_ide, var_ide, pruebas_ide`): el preflight no siempre las resuelve
    (sin acciones de postventa no lee esa obra) y por código no hace falta
    ninguna lectura más.
14. En pruebas, «alguna acción tiene su partida» compara también la
    partida 0 (sin partida): conservador, una omitida sin partida cubre las
    líneas sin partida de la 0404 (menos sobrantes, nunca más).
15. Los recursos de una petición del lote que falla no dan sobrantes.
16. `PonerACero` reutiliza `_fila` y `_traza` de `registro_pipeline.py`
    (importados, el fichero no cambia) para el log antes/después de F-051.
    En pruebas, «en la 0404» = el `hmoide` de la línea está entre los partes
    del periodo de la obra de pruebas (`partes_del_periodo`). Los lotes de
    15 son los de `escribir` (`SIGRID_MAX_STATEMENTS`).
17. T14: `poner_a_cero` va con la empresa por defecto de la api
    (`self._por_defecto`), la misma con que el preflight lee las líneas
    mensuales; los campos que viajan son los que relee la guarda
    (`hmores_ide, recurso_ide, hora, vinculado, can, synckey`). Un
    `sobrantes_a_cero` que no es lista de objetos con `hmores_ide` entero es
    422 sin escribir. Si poner a 0 falla, no se escribe nada por obra.
18. T15: el texto de la sección dice «la línea sigue en su parte, a 0» y no
    «no se borran»: un test ajeno prohíbe «se borran» en `app.js`.
19. T16: la remisión de `#regla-vinculado` es un párrafo tras la firma del
    punto 22, no una viñeta, para no tocar el texto de F-044.

## Fase RED (trazas reales; comando y salida)

Desde la carpeta del servicio: `.venv/Scripts/python -m pytest tests/<fichero>
-q -p no:cacheprovider`. Módulo ya escrito: apartado para la RED (error real).

- T1 `test_f054_lectura_mensuales.py`: `E AttributeError: 'SigridWriteClient'
  object has no attribute 'lineas_mensuales_del_periodo'` → `16 failed in 4.11s`.
- T2 `test_f054_traduccion.py`: `E ModuleNotFoundError: No module named
  'application.services.porcentajes_existentes'` → `1 error in 1.14s`.
- T3 `test_f054_endpoint.py`: `FAILED …test_f054_contrato_de_la_respuesta`,
  `…empresa_no_valida_422_sin_leer[None|0|-1|True|x]`,
  `…test_f054_r3_lectura_que_falla_502` → `11 failed, 1 warning in 12.56s`.
- T4 `test_f054_comparar.py`: `E ModuleNotFoundError: No module named
  'domain.traer_sigrid'` → `1 error in 1.82s`.
- T5 `test_f054_rutas.py`: `E ImportError: cannot import name
  'PorcentajesSigridNoDisponible' from 'domain.errors'` → `1 error in 1.26s`.
- T6 `test_f054_aceptar.py`: `E ImportError: cannot import name
  'MOTIVO_TRAIDA_DE_SIGRID' from 'infrastructure.db.repositories'` →
  `1 error in 6.03s`.
- T7 `test_f054_aceptar.py`: `E ModuleNotFoundError: No module named
  'application.traer_sigrid'` → `1 error in 5.39s`.
- T8 `test_f054_rutas.py`: `E AssertionError: {"detail":"Not Found"}` /
  `E assert 404 == 200` / `E AttributeError: 'Contenedor' object has no
  attribute 'traer_sigrid'` → `14 failed, 8 passed, 1 warning in 29.07s`
  (los 8 que pasan son los de T5).
- T9 front `test_f054_traer_front.py` (`.venv/Scripts/python -m pytest
  tests/test_f054_traer_front.py -q -p no:cacheprovider` desde el front):
  `E AssertionError: no existe la función sincronizarYTraer en app.js` (10),
  `… pintarTraerSigrid …` (1) y el enlace de `#btn-sync` → `12 failed in 0.84s`.
- T11 `test_f054_obra_cero.py` (transfer): `E ModuleNotFoundError: No module
  named 'application.services.reglas_obra_cero'` → `1 error in 0.49s`.
- T12 `test_f054_obra_cero.py -k lote`: `E AttributeError: 'RegistroLote'
  object has no attribute 'preflight_completo'` (7) y `E KeyError:
  'sobrantes'` (ruta) → `8 failed, 1 passed, 11 deselected`.
- T13 `test_f054_poner_a_cero.py`: `E ModuleNotFoundError: No module named
  'application.pipelines.poner_a_cero'` → `1 error in 0.37s`.
- T14 api `test_f054_registro_cero.py`: `E AssertionError: assert
  [('preflight_lote', False)] == [('preflight_lote', True)]` (4), `E
  TypeError: RegistroSigrid.ejecutar() got an unexpected keyword argument
  'sobrantes_a_cero'` (4), `E AttributeError: 'TransferClient' object has
  no attribute 'poner_a_cero'` (2), `E TypeError:
  TransferClient.preflight_lote() got an unexpected keyword argument
  'completo'` → `11 failed, 1 passed in 3.05s`.
- T15 front `test_f054_modal_cero.py`: `E AssertionError: no existe la
  función pintarSobrantes en app.js` → `5 failed in 0.33s`.

## Resultados (GREEN)

Cada tarea en verde antes de su commit; suites enteras tras T14 (api, 1432)
y T15 (front, 475). Resultado final en «Evidencias».

## MANUAL pendientes (NO ejecutadas; comando exacto en `tasks.md`)

- **T10** (líder, solo lecturas): preflight del mes 2026-09 desde el front,
  tres pasadas, método de F-055 T18, sobre un commit **anterior a B**
  (`ccad4db`, sin T11+). Anotar la mediana: no hay cifra todavía.
- **T18** (humano, local, solo lecturas): `curl -s -X POST
  http://localhost:8006/api/porcentajes/existentes -H "Content-Type:
  application/json" -d '{"empresa":1,"ano":2026,"mes":9,"obras":[]}'`; luego
  los pasos 2-4 de T18 en el front → `progress/manual_F-054.md`.
- **T19** (humano, `OBRA_PRUEBAS_FORZAR=true`): líneas a mano en la 0404;
  `cd services/dedicacion-transfer && .venv/Scripts/python
  prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`; registrar sin
  marcar y marcando; preflight ≤ 1,15 × mediana de T10. **Es la única prueba
  que escribe y no la ha lanzado ningún agente.**
- **T20** (líder, al desplegar): orden **transfer → api → front**; refrescar
  `azure-apps/dedicacion.md` desde `docs/INTEGRACION.md` (`git -C`) y avisar
  a `partes` de que el transfer pone a 0 líneas `M*` y de vinculados de
  partes compartidos, sin borrarlas.

**Fuera del alcance**: `features.json` y el cierre (líder). `registro_pipeline.py`
y los tests ajenos fuera de la lista cerrada, sin tocar.

## Evidencias

Medido en `c614be3`/`1c16454` con `bash harness/init.sh` (código 0, sin
`[KO]`, «ENTORNO LISTO»; `ruff`: 309 avisos, los de `dev`; ninguno entra con la feature (O1)):

| Evidencia | Resultado real |
|---|---|
| Tests | api `1467 passed` (179,77 s); transfer `1845 passed` (60,66 s); front `479 passed` (379,40 s, con la máquina ocupada; 49,51 s antes); raíz `418 passed, 1 skipped` (116,73 s) |
| Cobertura de líneas cambiadas | **99,5 %** (744/748, umbral 80 %). No mide JS |
| Mutación Python | 262 generados, **262 muertos, 0 supervivientes**, 0 timeouts, 4 workers, 3767 s, SHA `c614be3`: `progress/mutacion_F-054.md` |
| Mutación `app.js` | manual, **69 mutantes, 0 supervivientes**: `progress/mutacion_manual_F-054.md` |

**Análisis de supervivientes.** Ningún equivalente: nada queda para que lo
acepte el humano. La campaña 1 (`95cc089`, 207/262,
`progress/mutacion_F-054_campana1.md`) dejó 55 vivos y la de `app.js`, 9;
todos se matan con tests, **sin cambiar código de producción**:
`test_f054_mutacion.py` (api 35, transfer 20) y 4 en el front. Huecos reales:
validación de `sobrantes_a_cero` en `routes.py` (6, sin ningún test); guarda
de `can` y `_EPS` exacto; `ok: true` con todo omitido (la api lo tomaría por
fallo); 502 de la ruta; pruebas sin 0404; partida 0 frente a 1 (6); `cod_var`
y `desde`; textos de la sobrante (el test miraba todo el modal y el pisado de
F-064 los repetía). De poco riesgo: `frozen` (11) y defectos (10). La campaña
final entera no deja vivos, así que no hubo nada que reproducir en serie.
