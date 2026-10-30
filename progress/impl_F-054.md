<!-- progress/impl_F-054.md -->
# F-054 · Informe del implementer

Rama `feature/F-054-sync-trae-porcentajes`, copia `porcentajes-f054`. Rigor
**crítico**. Spec `specs/F-054-sync-trae-porcentajes/` (T1-T21). Informe
escrito a medida que avanza (dos cortes del entorno: tras T3 y tras T7).

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
| T17 cobertura y mutación | — | en curso |
| T18-T20 | — | MANUAL (ver abajo) |
| T21 `init.sh` en verde | — | pendiente |

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
- ajenos, solo los de la lista cerrada: `ANCLAS` de
  `test_f002_fuente_unica.py`; los dobles `preflight_lote` de
  `test_f022_empresa_en_linea.py`, `test_f024_registro_empresa.py` y
  `test_f055_registro_lote.py` aceptan `completo=False` (ninguna aserción
  cambia).

## Decisiones de diseño y desviaciones (justificadas)

1. **Vigencia por `vigente_en`** (activo + fecha de baja), la regla única del
   dominio, en vez de solo `activo` (design §5.2 dice «por `activo`»):
   `listar_para_periodo` ya devuelve `activo` = vigente en el mes, así que
   coincide, y para el trabajador que no sale en el listado (no vigente sin
   líneas) se lee del maestro con `obtener` para que su motivo sea «no
   vigente» y no «fuera del maestro».
2. `ExistentesIn.empresa` sin tipo: cualquier valor no válido da 422 con
   motivo `{ok:false,error}` sin leer Sigrid.
3. Las líneas de la obra de pruebas siempre se excluyen en A (R5);
   `lineas_leidas` cuenta todas.
4. La comparación solo saca a los trabajadores con alguna entrada de Sigrid.
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
8. Aceptadas repetidas en la misma petición se cuentan una vez.
9. Ruta: sin cuerpo = comparar; `propuestas_en_curso` solo se pide
   (`_encolar`) si hay tocados; si no, `false`.
10. Tests de T7 con una UoW en memoria **propia** (con transacción por copia,
    `id` y traza por fila) en vez de la de `test_f024_cuadrante_empresa.py`
    (design §9): la de F-024 no tiene transacción ni traza, y R19/R22/R23 no
    se podrían comprobar con ella.
11. Front: `#btn-sync` se enlaza con `() => sincronizarYTraer()` (no con la
    función directa): los arneses de `enlazarEventos` de
    `test_f050_t15e_sombreado.py`, `test_f029_seleccion.py` y
    `test_f050_m2_arreglos.py` (ajenos, fuera de la lista cerrada) solo
    definen `sincronizar`, y con la referencia directa el primero fallaba
    con `ReferenceError: sincronizarYTraer is not defined`. Con la flecha
    pasan sin tocarlos.
12. La ventana usa el overlay `#modal-registro` (`abrirModal`), el único
    modal genérico; sin casillas no se pinta «Aceptar las marcadas».
13. **B, la obra especial por código**: `cubierta` reconoce la obra de
    postventa, la VAR y la de pruebas por el `obra_cod` de la línea (la
    lectura va por empresa) en vez de por `ide` (design §6.1 dice
    `pv_ide, var_ide, pruebas_ide`): el preflight no siempre las resuelve
    (sin acciones de postventa no lee esa obra) y por código no hace falta
    ninguna lectura más.
14. En pruebas, «alguna acción tiene su partida» compara también la
    partida 0 (sin partida): conservador, una omitida sin partida cubre las
    líneas sin partida de la 0404 (menos sobrantes, nunca más).
15. Los recursos de una petición del lote que falla no dan sobrantes: sin
    su preflight no se sabe qué los cubre.
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
19. T16: la remisión de `#regla-vinculado` es un párrafo al final del
    punto 22 (tras su firma), no una viñeta entre las suyas, para no tocar
    el texto aprobado de F-044.

## Fase RED (trazas reales; comando y salida)

Todas desde la carpeta del servicio: `.venv/Scripts/python -m pytest
tests/<fichero> -q -p no:cacheprovider`. Cuando el módulo ya estaba escrito
se apartó temporalmente para la RED (error de recogida real).

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

- T1-T3 transfer: 48 passed. T4 36 passed. T7 `test_f054_aceptar.py` 25
  passed. T8 `test_f054_rutas.py` 22 passed. T9 front 12 passed (+
  `test_f061_recarga.py` sin cambios, 3 passed); suite front entera
  `470 passed` tras el arreglo del punto 11.
- T11 12 passed; T12 `test_f054_obra_cero.py` 20 passed y `-k "lote or f055
  or f044 or f062 or f054"` 655 passed; T13 16 passed; suite transfer
  entera tras T13: `1821 passed in 23.66s`.
- Suite api entera tras T5: `1381 passed in 140.12s`; tras T7: `1406 passed
  in 113.38s`; tras T8: `1420 passed in 108.99s`; tras T14: `1432 passed`.
- T14 `test_f054_registro_cero.py` 12 passed. T15 `test_f054_modal_cero.py`
  5 passed; con los del modal de F-064/F-050/F-051/F-062, 45 passed; suite
  front entera `475 passed, 19 warnings in 49.51s`.
- T16 `test_f002_fuente_unica.py` (transfer): `86 passed in 0.21s`.

## MANUAL pendientes (no ejecutadas por el implementer)

(se completa al final)

## Evidencias

(se completa al final)
