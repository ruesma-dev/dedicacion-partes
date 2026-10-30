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
| T8 ruta `POST …/traer-sigrid` | ver git log | hecha |
| T9 front A (`sincronizarYTraer`, ventana) | ver git log | hecha |
| T10 | — | MANUAL del líder (ver abajo) |
| T11-T21 | — | pendientes |

## Ficheros tocados (hasta T8)

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
- tests nuevos: transfer `test_f054_{lectura_mensuales,traduccion,endpoint}.py`;
  api `test_f054_{comparar,rutas,aceptar}.py`.

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

## Resultados (GREEN)

- T1-T3 transfer: 48 passed. T4 36 passed. T7 `test_f054_aceptar.py` 25
  passed. T8 `test_f054_rutas.py` 22 passed. T9 front 12 passed (+
  `test_f061_recarga.py` sin cambios, 3 passed); suite front entera
  `470 passed` tras el arreglo del punto 11.
- Suite api entera tras T5: `1381 passed in 140.12s`; tras T7: `1406 passed
  in 113.38s`; tras T8: `1420 passed in 108.99s`.

## MANUAL pendientes (no ejecutadas por el implementer)

(se completa al final)

## Evidencias

(se completa al final)
