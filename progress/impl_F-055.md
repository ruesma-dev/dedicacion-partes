# F-055 · Informe del implementer

Rama `feature/F-055-preflight-rapido` (copia `porcentajes-f041`). Rigor
`critico`. Spec aprobada por el humano el 2026-10-13. Este informe crece por
tareas; hoy solo **T1**. T2 es MANUAL del humano y va antes de T3.

## T1 · Medición (R1, R2, C2 «antes»)

### Qué cambió

| Fichero | Cambio |
|---|---|
| transfer `infrastructure/sigrid/sigrid_write_client.py` | `Lectura`, `MedicionLecturas`, `medir_lecturas()` (contextvar, anidable, con `Lock`) y `apuntar_lectura(nombre, filas, segundos)`: log `[sigrid-read] <método> filas=<n\|error> segundos=<s>`, sin SQL ni parámetros. `_lectura(nombre, sql, params)` mide y llama a `_read`; los 14 métodos de lectura pasan por ella con su nombre. |
| transfer `application/pipelines/registro_pipeline.py` | `preflight` abre una medición y, también si falla (`finally`), loguea `[registro] lecturas preflight obra=<cod o ide> lecturas=<n> segundos_leyendo=<s> segundos_totales=<s>`. El cuerpo de antes pasa, sin cambios, a `_preflight`. |
| transfer `prueba_escritura_porcentajes.py` | Fase `medir` (R2): `--obra` y `--recurso` repetibles, `--partida OBRA:PARIDE` (repetible, la obra tiene que estar entre las `--obra`), `--lote` (aceptado, aún sin efecto: lo avisa). La fase `propuesta` exige ahora un solo `--obra` y un solo `--recurso` (antes ganaba el último). |
| transfer `tests/test_f055_medicion.py` | Nuevo: 35 tests (R1, R2, C2). |

Ningún test anterior cambia (lista cerrada intacta: `conftest.py` sin tocar).

### Decisiones y desviación de la spec

- **Desviación de design §5.1** («`_read(sql, params, nombre=…)`»): con ese
  `nombre` en `_read` se rompían **35 tests anteriores** de F-022, F-024,
  F-037 y F-050, que sustituyen `_read` por dobles de dos argumentos
  (`(sql, params)`), y ninguno está en la lista cerrada. Se cumple R1 sin
  tocarlos: `_read` conserva su firma exacta y la medición va en un envoltorio,
  `_lectura(nombre, sql, params)`. Mismo efecto (cada lectura de un método
  sale con su nombre); lo fija
  `test_f055_r1_read_conserva_su_contrato_y_sus_dobles`.
- Las llamadas directas a `cli._read(...)` de las fases `inspeccionar`,
  `estado` y `limpiar` del script no se miden: no son lecturas del servicio.
- La medición es un `ContextVar` con las mediciones abiertas, de fuera a
  dentro: cada lectura se apunta en todas. Así la fase `medir` (fuera) y el
  resumen del preflight (dentro) cuentan lo mismo sin pisarse. Para el pool de
  hilos de T6 hará falta propagar el contexto (`contextvars.copy_context`);
  `MedicionLecturas.apuntar` ya lleva `Lock`.
- El reloj es `_ahora = time.perf_counter` en cada módulo, para poder fijarlo
  en los tests y comprobar las cifras exactas del log.
- `segundos_totales` = el preflight entero, lecturas incluidas.
- **C2 «antes»** lo fijan dos tests con un `ClienteFalso` que cuenta
  (subclase en el propio test, sin tocar `conftest.py`): una obra con las dos
  partidas elegidas hace **8 lecturas en serie** (`obra_por_codigo` ×2,
  `horas_de_recursos`, `capitulos_de_obra`, `cuentas_de_centro`,
  `partes_del_periodo`, `lineas_por_synckey`, `lineas_del_parte`), y **9** si
  un recurso no tiene subcuenta (+`partidas_de_lineas`). **T4 cambiará a
  propósito** `test_f055_c2_antes_*` (`capitulos_de_obra` pasa a
  `validar_partidas`): son tests de F-055, no de la lista cerrada.

### Fase RED (tests antes que el código)

1. Con solo el fichero de tests escrito:

```
$ cd services/dedicacion-transfer && .venv/Scripts/python -m pytest tests/test_f055_medicion.py -q --tb=line
tests\test_f055_medicion.py:27: in <module>
    from infrastructure.sigrid.sigrid_write_client import (
E   ImportError: cannot import name 'apuntar_lectura' from 'infrastructure.sigrid.sigrid_write_client'
ERROR tests/test_f055_medicion.py
1 error in 2.61s
```

2. Con el esqueleto de la medición (`medir_lecturas` y un `apuntar_lectura`
   vacío), sin cablear `_read`, el resumen ni la fase `medir` (mismo comando):

```
E   AssertionError: assert [] == ['[sigrid-rea...egundos=1.50']        (test_f055_medicion.py:97)
E   AssertionError: assert '[sigrid-read]' in ''                        (:110)
E   AssertionError: assert [] == [('obra_por_codigo', 0)]               (:136, y así los 14 métodos)
E   AssertionError: assert [] == [('capitulos_..., None, 0.25)]         (:159, lectura que falla, x3)
E   AssertionError: assert [] == ['a', 'b', 'c']                        (:173, mediciones anidadas)
E   AttributeError: <module 'application.pipelines.registro_pipeline'> has no attribute '_ahora'   (resumen del preflight, x2)
E   ValueError: not enough values to unpack (expected 1, got 0)        (:245, resumen por ide)
E   AssertionError: assert [] == ['obra_por_co...periodo', ...]         (:259, C2 8 lecturas)
E   assert 0 == 9                                                       (:280, C2 9 lecturas)
E   argparse.ArgumentError: argument fase: invalid choice: 'medir' (choose from 'inspeccionar', ..., 'propuesta')   (R2, x4)
30 failed, 5 passed in 7.96s
```

Los dos de C2 fallaban solo porque `apuntar_lectura` estaba vacío: describen
el comportamiento de hoy (son la cifra «antes»), no un cambio. Los 5 que
pasaban: los argumentos incompletos de `medir` (argparse ya los rechazaba).

3. Verde (mismo comando): `35 passed in 4.27s`.

### Verificación de T1

- `pytest services/dedicacion-transfer/tests/test_f055_medicion.py`:
  **35 passed**. Sin SQL ni parámetros en el log
  (`test_f055_r1_el_log_no_lleva_sql_ni_parametros`: ni el parámetro, ni
  `SELECT`/`FROM`/`WHERE`/`?`); `medir` no llama a `escribir` ni a `ejecutar`
  (los dos lanzan `AssertionError` en los tests de R2 y `escritos == []`).
- Suite entera del transfer: **785 passed in 16.55 s**.
- `ruff` sobre los cuatro ficheros: 21 avisos, **los mismos 21 que había antes**
  en los tres de producción (deuda previa); ninguno nuevo.
- `bash harness/init.sh`: ver «Evidencias».

## T2 · Lo que tiene que hacer el humano (MANUAL, solo lectura, antes de T3)

1. **Script** (Git Bash, con el `.env` local del transfer):

```
cd services/dedicacion-transfer && .venv/Scripts/python prueba_escritura_porcentajes.py medir --ano 2026 --mes 9 --obra 0694 --obra 0696 --recurso 1705036
```

   Opcional, con la partida elegida (el caso de C2/C3; 384155 = CI.1.5 de la
   0694, la de la M3 de F-050): añadir `--partida 0694:384155`.

   **Qué copiar** a este informe: de cada bloque `== Obra X ==`, las líneas
   `  lectura <método>: <n> filas · <s> s`, la línea
   `Obra X: N lecturas · S s leyendo · T s en total` y la final `TOTAL: …`.
   Solo lee: no llama a `escribir` ni a `ejecutar`.

2. **Navegador** (local, modo pruebas; **Cancelar, nunca Registrar**):
   cronometrar «⇪ Sigrid» → modal de GONZALEZ PANIAGUA; el mes entero; un
   cambio de partida en el modal (repreflight); la apertura de un selector de
   partida. En **producción**, lo mismo solo hasta el modal y Cancelar.
   Si hay acceso al log del transfer local, copiar también las líneas
   `[registro] lecturas preflight …` de cada preflight.

3. **Criterio de parada**: si la lectura que más pesa **no** es una de las que
   este diseño quita o agrupa (presupuesto, historial, lecturas por obra en
   serie), **PARA** y se repropone (tasks.md, T2).

### Cifras de T2

_(pendiente del humano)_

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (transfer) | 785 passed, 0 failed (16.55 s) |
| Tests de T1 | 35 passed (4.27 s) |
| Cobertura de las líneas cambiadas | ver salida de `bash harness/init.sh` abajo |
| Mutantes | no aplica todavía: la campaña completa es T16, al final |
| `bash harness/init.sh` | ver abajo |
