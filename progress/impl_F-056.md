<!-- progress/impl_F-056.md -->
# F-056 · Informe del implementer

Validar `trabajador_ide` en `POST …/registro/preflight` y `…/registro/ejecutar`
(un valor falso registraba el mes entero). Rigor **crítico**, `sdd: false`.
Rama `feature/F-056-validar-trabajador-ide`, copia principal. Plan seguido: «F-056,
plan aprobado (2026-10-19)» de `progress/current.md`, sin desviaciones.

## Qué cambió (solo `services/dedicacion-api`; el front no se toca)

| Fichero | Cambio |
|---|---|
| `domain/errors.py` | Nuevo `TrabajadorNoValido(ErrorDominio)` (no hereda de `ObraNoValida`). |
| `interface_adapters/api/app.py` | `(TrabajadorNoValido, 422)` en `_HTTP_POR_ERROR`, junto a `ObraNoValida`. |
| `interface_adapters/api/routes.py` | El `_obra_ide` de F-050 se generaliza en `_entero_opcional(valor, campo, error)` (mismo cuerpo; el mensaje es `"{campo} no es un entero: {valor!r}"`). `_obra_ide` y el nuevo `_trabajador_ide` son envoltorios de una línea. `registro_preflight` y `registro_ejecutar` validan `trabajador_ide` **como primera sentencia**, antes del filtro de empresa, de los `overrides` y de llamar al registro. |
| `application/registro_sigrid.py` (~96) | Filtro `if trabajador_ide is not None` (antes `if trabajador_ide`). |
| `tests/test_f056_trabajador_ide.py` | Nuevo: 50 casos (ver abajo). |
| `docs/INTEGRACION.md` | Párrafo del preflight de F-050: `trabajador_ide` entero o `null`, 422 en otro caso, `0` filtra. |

Commits (todos en la rama, comprobada con `git -C . branch --show-current`):

- `c0f6e30` F-056 T1: validación en las dos rutas + 422 + tests.
- `09c61c8` F-056 T2: filtro `is not None`.
- `42ddad8` F-056 T3: `docs/INTEGRACION.md`.
- `48b63f2` F-056: test sin aviso de ruff (`__enter__ -> Self`).

## Decisiones de diseño

1. **Validar lo primero.** El 422 sale antes de leer `overrides`: unos
   `overrides` rotos (que hoy dan 500, fuera de alcance) no tapan el error de
   `trabajador_ide`. Lo fija `test_f056_a1_se_valida_antes_que_los_overrides`.
2. **Mismo criterio que `obra_ide`** (decisiones del líder aceptadas por el
   humano): `"11"` y `11.0` → `11`; `0` y `-3` son enteros (200); `""`,
   `false`, `true`, `"abc"`, `1.5`, `"1.5"`, `[11]`, `{"a": 11}`, `Infinity`
   → 422. `null` o ausente → `None` (el mes entero, como antes).
3. **Error propio** (`TrabajadorNoValido`) y no reutilizar `ObraNoValida`: el
   mensaje nombra el campo y el test comprueba que una obra rota con
   trabajador válido sigue diciendo `obra_ide`.
4. **Doble que aplica el filtro de verdad.** `_SesionQueFiltra` recorre el
   `WHERE` de la sentencia SQLAlchemy (`sqlalchemy.sql.visitors.iterate`),
   busca `asignacion.trabajador_ide == X` y filtra las filas por él; si la
   sentencia no lo lleva, devuelve el mes entero, como la base. Así el test
   distingue «filtro con 0» de «sin filtro» sin BBDD.

## Tests (`tests/test_f056_trabajador_ide.py`, 50 casos)

- `test_f056_trabajador_no_valido_es_error_de_dominio_propio`.
- `test_f056_a1_no_entero_422_sin_analizar_ni_escribir` × 2 rutas × 9 valores:
  422, mensaje `trabajador_ide no es un entero…`, el registro falso **no recibe
  ninguna llamada**.
- `test_f056_a1_se_valida_antes_que_los_overrides` × 2 rutas.
- `test_f056_a1_entero_o_null_llega_al_registro` × 2 rutas × (`0`, `11`,
  `"11"`, `11.0`, `-3`, `null`): 200 y llega con valor y **tipo** exactos.
- `test_f056_a1_sin_trabajador_es_el_mes_entero` × 2 rutas (cuerpo `{}`).
- `test_f056_a1_obra_no_valida_sigue_siendo_de_obra`.
- `test_f056_a2_cero_filtra_y_no_manda_nada` × 2 fases: con `0` la sentencia
  lleva el filtro `[0]`, el transfer no recibe nada y la respuesta es
  `{"ok": true, "obras": [], "no_vigentes": []}`.
- `test_f056_a2_un_trabajador_solo_sus_lineas` y
  `test_f056_a2_sin_trabajador_el_mes_entero` × 2 fases.
- `test_f056_a1_a2_ruta_con_registro_real_no_escribe` × 2 rutas × (`""`,
  `false`, `"abc"` → 422; `0` → 200): de punta a punta con el
  `RegistroSigrid` real, la sesión que filtra y el transfer falso:
  **ni una línea llega al transfer**.

Los de `obra_ide` de F-050 (`tests/test_f050_preflight_obra.py`) siguen en
verde sin tocarlos (62 passed juntos, ver abajo).

## Fase RED (trazas reales)

**1) Antes de tocar producción** (comando desde `services/dedicacion-api`):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f056_trabajador_ide.py -q
tests\test_f056_trabajador_ide.py:28: in <module>
    from domain.errors import ErrorDominio, ObraNoValida, TrabajadorNoValido
E   ImportError: cannot import name 'TrabajadorNoValido' from 'domain.errors'
ERROR tests/test_f056_trabajador_ide.py
1 error in 4.06s
```

**2) Solo con la clase `TrabajadorNoValido` añadida** (sin el 422, sin
validar en las rutas, sin tocar el filtro):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f056_trabajador_ide.py -q -p no:cacheprovider
FAILED …test_f056_a1_no_entero_422_sin_analizar_ni_escribir[preflight-""] … [ejecutar-Infinity]   (18)
FAILED …test_f056_a1_se_valida_antes_que_los_overrides[preflight|ejecutar]                         (2)
FAILED …test_f056_a1_entero_o_null_llega_al_registro[preflight|ejecutar-"11"-11|11.0-11]           (4)
FAILED …test_f056_a2_cero_filtra_y_no_manda_nada[preflight|ejecutar]                              (2)
FAILED …test_f056_a1_a2_ruta_con_registro_real_no_escribe[…-""|false|"abc"-422, …-0-200]           (8)
34 failed, 16 passed, 1 warning in 12.51s
```

Detalle de los cuatro centrales (`--tb=short`, salida pegada):

```
_____________ test_f056_a2_cero_filtra_y_no_manda_nada[ejecutar] ______________
tests\test_f056_trabajador_ide.py:170: in test_f056_a2_cero_filtra_y_no_manda_nada
    assert sesion.filtros == [0]
E   assert [] == [0]
E     Right contains one more item: 0
_____ test_f056_a1_no_entero_422_sin_analizar_ni_escribir[ejecutar-false] _____
tests\test_f056_trabajador_ide.py:112: in test_f056_a1_no_entero_422_sin_analizar_ni_escribir
    assert r.status_code == 422, r.text
E   AssertionError: {"ok":true,"obras":[]}
E   assert 200 == 422
______ test_f056_a1_a2_ruta_con_registro_real_no_escribe[ejecutar-0-200] ______
tests\test_f056_trabajador_ide.py:205: in test_f056_a1_a2_ruta_con_registro_real_no_escribe
    assert transfer.payloads == []
E   AssertionError: assert [{'obra': {'i...io': 'local'}] == []
E     Left contains 2 more items, first extra item: {'obra': {'ide': 678, 'codigo': '0678', 'nombre': 'OBRA'}, 'lineas': [{'registro_id': 1, 'ano': 2026, 'mes': 7, 'porce... 0.4, ...}, {'registro_id': 2, 'ano': 2026, 'mes': 7, 'porcentaje': 0.4, ...}], 'pisar_claves': [], 'usuario': 'local'}
____ test_f056_a1_no_entero_422_sin_analizar_ni_escribir[preflight-"abc"] _____
tests\test_f056_trabajador_ide.py:112: in test_f056_a1_no_entero_422_sin_analizar_ni_escribir
    assert r.status_code == 422, r.text
E   AssertionError: {"ok":true,"obras":[]}
E   assert 200 == 422
5 failed, 1 warning in 3.83s
```

La tercera es el fallo de la feature, reproducido: `ejecutar` con
`trabajador_ide: 0` mandaba al transfer **las dos obras del mes** (trabajadores
10 y 11) en vez de nada.

**3) Tras T1** (rutas + 422): `4 failed, 58 passed` (f056 + f050): solo los
cuatro casos del filtro con `0`. **Tras T2** (filtro): `62 passed, 1 warning
in 13.66s`; suite entera de la api `924 passed, 1 warning in 36.34s`.

## Mutación

`python -m harness.mutacion --feature F-056` (campaña completa, sin muestreo,
nivel crítico) → `progress/mutacion_F-056.md`:

- Alcance: 4 ficheros, 35 líneas de producción frente a `dev` (`9ff3e54`).
- **2 mutantes generados, 2 muertos, 0 supervivientes**, 0 timeouts, 161.3 s:
  - `app.py:44` `(TrabajadorNoValido, 422)` → `423`: muerto.
  - `registro_sigrid.py:96` `is not None` → `is None`: muerto.

El operador del arnés no genera mutantes sobre las líneas de
`_entero_opcional` que no cambiaron (el cuerpo es el de F-050 movido). Como el
nivel es crítico y ahora esas líneas deciden si `ejecutar` escribe, se
aplicaron **a mano** seis mutantes sobre `routes.py`, cada uno contra
`test_f056_trabajador_ide.py` + `test_f050_preflight_obra.py`, restaurando con
`git checkout` tras cada uno (árbol limpio al acabar):

| Mutante manual | Resultado |
|---|---|
| `if valor is None` → `is not None` | 47 failed: muerto |
| `isinstance(valor, bool) or (…float…)` → `and` | 13 failed: muerto |
| `and not valor.is_integer()` → `and valor.is_integer()` | 9 failed: muerto |
| `isinstance(valor, bool) or` → `False or` | 7 failed: muerto |
| `except (TypeError, ValueError)` → `except (TypeError,)` | 27 failed: muerto |
| rutas sin `_trabajador_ide(...)` (valor crudo, como antes) | 30 failed: muerto |

Cero vivos, ni en la campaña ni a mano.

## Verificaciones

- `bash harness/init.sh` (tras borrar `.arnes_cache/suite_*.ok`): **ENTORNO
  LISTO**, sin `[KO]`. Raíz `418 passed, 1 skipped`; api `924 passed`; front
  `291 passed`; transfer `932 passed`. `PUERTA COBERTURA: 100.0% de 10 líneas
  cambiadas cubiertas (10/10, umbral 80%, nivel critico)`. ruff: aviso de deuda
  previa; el único aviso que añadía el test nuevo (PYI034) se corrigió en
  `48b63f2` y `ruff check` del test desde la raíz da «All checks passed!». Se
  repite init.sh tras escribir este informe (ver «Evidencias»).
- MANUAL pendiente: ninguna para cerrar. Tras desplegar la api (lo propone el
  líder al cerrar; aquí no se despliega nada), comprobación opcional de solo
  lectura: `POST /api/v1/periodos/2026/9/registro/preflight` con cuerpo
  `{"trabajador_ide": ""}` → 422 `trabajador_ide no es un entero: ''`. **Nunca
  con `ejecutar`**: el transfer desplegado está en modo real.

## Fuera de alcance y observaciones

- **O1 (no se arregla aquí, como dice el plan):** `overrides` no enteros dan
  500 en las dos rutas (`int(k)`, `int(v)` en `routes.py`, ~447 y ~464).
  También `pisar_claves` y `usuario` llegan crudos a `ejecutar` (`list(...)` de
  un texto lo trocea en caracteres; `str(...)` de cualquier cosa). Candidatos a
  una feature propia si el humano lo quiere.
- **O2, `azure-apps/dedicacion.md`:** repite el párrafo del preflight de F-050
  (~línea 333) y no menciona `trabajador_ide`. Describe lo desplegado, así que
  se actualiza **al desplegar** la api con F-056 (pendiente del líder; no se ha
  tocado el otro repositorio).
- El front no cambia: ya manda un número o `null`.
- Nada desplegado, nada escrito en Sigrid, `.env` sin tocar, sin `git push`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la feature | 50 nuevos, 50 passed (`test_f056_trabajador_ide.py`, 8.51 s) |
| Suite api / front / transfer / raíz | 924 / 291 / 932 / 418 passed (+1 skipped en raíz) |
| Cobertura de líneas cambiadas | **100.0 %** (10/10), umbral 80 %, `PUERTA COBERTURA` |
| Mutantes (campaña del arnés) | 2 generados, 2 muertos, **0 supervivientes** |
| Mutantes manuales sobre el helper | 6 aplicados, 6 muertos |
| Tiempo de la suite | api 56.02 s, front 32.46 s, transfer 17.13 s, raíz 52.28 s (init.sh) |
