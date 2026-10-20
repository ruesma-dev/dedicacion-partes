# F-051 · Informe del implementer (2026-10-20) · BLOQUEADA en T3

Spec: `specs/F-051-pisar-lineas-cero/`. Copia `porcentajes-f051`, rama
`feature/F-051-pisar-lineas-cero`. Rigor `critico`. **Estado: `blocked`**
(motivo y opciones en `progress/current.md`, «F-051 · BLOQUEO en T3»).

## 1. Qué está hecho

| Tarea | Estado | Commit |
|---|---|---|
| T1 `es_linea_al_cero`, `pisables_al_cero`, `synckey_tras_editar` | hecha | `5f0e759` |
| T2 `emparejar_ceros` | hecha | `5f0e759` (mismo commit que T1) |
| T3 modelos | **revertida**: rompe un test fuera de la lista | — |
| T4-T17 | sin empezar | — |

Ficheros tocados (commiteados):

- `services/dedicacion-transfer/application/services/reglas_porcentajes.py`:
  bloque «Líneas al 0 %» con `es_linea_al_cero`, `pisables_al_cero`,
  `emparejar_ceros`, `repartir_choques`, `es_nuestra_de_otra`,
  `synckey_tras_editar` y los textos `AVISO_LINEA_CERO`,
  `AVISO_QUEDAN_A_CERO` y `MOTIVO_LINEA_CAMBIADA`. Importa `PREFIJO_SYNCKEY`
  del cliente de Sigrid (sin ciclo de importación; la suite entera pasa).
- `services/dedicacion-transfer/tests/test_f051_reglas_cero.py` (55 tests).

## 2. Decisiones de diseño (hasta aquí)

- **`repartir_choques(registros, choques)`** (pura, nueva): el design §6.2
  dice «`edita_ide` = el choque de menor `ide` (uno por registro del
  conflicto, por `registro_id`)». Se implementa como un reparto: registros
  por `registro_id` ↔ choques por `ide`; los choques que sobran, a 0 (D14 =
  A). Con un solo registro, `edita_ide` = el menor y el resto a 0.
- **`es_nuestra_de_otra(synckey, propia)`** (pura, nueva): la condición de
  R15 («su `synckey` no es nuestra de otra asignación»), para el paso 6.
- **`emparejar_ceros` devuelve el recuento de TODOS los recursos de las
  acciones**, también con 0 (`{200: 0}`): el aviso lee `.get(recurso, 0)`.
- **Prevista para T4** (anotada para quien retome): `lineas_registradas(claves,
  ides)` sin `ides` delega en `lineas_por_synckey` («sin `ides` = la consulta
  de hoy»), y el doble `ClienteFalso.lineas_registradas` llama a su
  `lineas_por_synckey`: así los tests de F-055 que nombran
  `lineas_por_synckey` (lecturas_lote, lote, medicion) siguen sin cambiar.

## 3. Fase RED (traza real)

Comando, desde `services/dedicacion-transfer`, con el fichero de tests
escrito y las funciones aún inexistentes:

```
.venv/Scripts/python -m pytest tests/test_f051_reglas_cero.py -q
E   ImportError: cannot import name 'emparejar_ceros' from
    'application.services.reglas_porcentajes'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.69s
```

Para ver el fallo de cada aserción, las seis funciones como stubs triviales
(`return False`, `()`, `({}, {})`, `actual`…), mismo comando:

```
FAILED tests/test_f051_reglas_cero.py::test_f051_r1_can_cero_o_nulo_es_al_cero[0]
FAILED tests/test_f051_reglas_cero.py::test_f051_r1_cualquier_m_y_partida_en_obra_normal
>       assert _pisables(existentes, _accion()) == [10, 20, 30]
E       assert [] == [10, 20, 30]
FAILED tests/test_f051_reglas_cero.py::test_f051_r1_postventa_solo_misma_partida
FAILED tests/test_f051_reglas_cero.py::test_f051_r1_r7_en_parte_cerrado_no
FAILED tests/test_f051_reglas_cero.py::test_f051_r1_de_esta_ejecucion_no
FAILED tests/test_f051_reglas_cero.py::test_f051_r2_una_por_accion_misma_partida_primero
E         At index 0 diff: {} != {1: 10}
FAILED tests/test_f051_reglas_cero.py::test_f051_r2_dos_pisables_una_accion_una_queda_a_cero_por_recurso
FAILED tests/test_f051_reglas_cero.py::test_f051_r4_r5_un_registro_edita_el_menor_y_los_demas_a_cero
E         At index 0 diff: {} != {9: 10}
FAILED tests/test_f051_reglas_cero.py::test_f051_r9_vacia_o_nuestra_pasa_a_la_nueva[None]
E         - 'porcentajes:5'
FAILED tests/test_f051_reglas_cero.py::test_f051_r15_nuestra_de_otra_asignacion[porcentajes:2-True]
29 failed, 26 passed in 1.93s
```

(Los 26 que pasan con stubs son los casos negativos: «no es al cero», «no
pisable», «se conserva», «no es de otra»; con la implementación real se
siguen cumpliendo.) Implementado: `55 passed in 3.14s`.

## 4. Por qué se para (T3)

Con los campos de T3 aplicados (`Conflicto.edita_ide`, `a_cero_ides`, más el
resto de design §3), la suite del transfer:

```
.venv/Scripts/python -m pytest tests -q
FAILED tests/test_f013_sin_partida.py::test_f013_r4_no_hace_falta_ningun_campo_nuevo
E       AssertionError: assert {'a_cero_ides...'exceso', ...} == {'ano', 'clav...'horide', ...}
E         Extra items in the left set:
E         'edita_ide'
E         'a_cero_ides'
1 failed, 986 passed, 1 warning in 101.38s
```

Ese test no está en la lista cerrada de `tasks.md` y la orden es parar. Se
ha revertido T3: el árbol queda limpio con T1-T2. Opciones y recomendación,
en `progress/current.md`.

## 5. Verificación del estado entregado

- Línea base antes de tocar nada (HEAD `1ecb9f5`): transfer 932 passed; api
  943 passed; front 305 passed; raíz 418 passed, 1 skipped.
- Tras T1-T2: transfer **987 passed** (932 + 55).
- `bash harness/init.sh` final: ver §6.

## 6. `bash harness/init.sh` (worktree, tras el bloqueo)

Sin ningún `[KO]` («ENTORNO LISTO. Puedes trabajar.»): raíz 418 passed, 1
skipped; api 943 passed; front 305 passed; transfer 987 passed. PUERTA
COBERTURA: **100,0 % de 32 líneas cambiadas** (umbral 80 %, nivel crítico).
PUERTA TAMAÑO dentro (impl 124/220). Avisos: F-051 `blocked`, `BACKLOG.md`
regenerado, ruff (deuda previa).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | transfer 987 passed (55 nuevos de F-051) |
| Cobertura de líneas cambiadas | 100,0 % (32/32), PUERTA COBERTURA de init.sh |
| Mutación | no lanzada: la feature está bloqueada en T3 (T14 no alcanzada); workers previstos: 1 |
| Tiempo de la suite del transfer | 119,94 s (dentro de init.sh) |

## Pendiente

- Decisión del humano sobre el test de F-013 (A/B/C de `current.md`).
- T3-T17; T15 (MANUAL) la ejecuta el humano; T16 (azure-apps) el líder.
