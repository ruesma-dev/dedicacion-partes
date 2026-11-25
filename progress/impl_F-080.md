<!-- progress/impl_F-080.md -->
# F-080 · Informe del implementer (`critico`)

Rama `feature/F-080-caja-por-trabajador`. Spec aprobada por el humano el
2026-11-25 (D1, D3, D4, D5 y D7 la (a); D2 sin pasada de restos; D6
retirada). Solo cambia la api. Del transfer y del front solo hay tests
nuevos.

## Hecho

- **La caja se reparte por %, como los km** (R1). `config.yaml` pasa a
  `CAJA: {unidad: eur, reparto: pct}` y el comentario de `importes` cita
  F-080. El reparto `obra` sigue siendo válido, aunque ningún tipo lo usa
  (D1 a).
- **Con esa config, lo demás ya salía como km** (design §2), y ahora está
  probado con los tipos de la config real:
  - el cuadrante da una casilla de caja por trabajador y subfilas
    `reparto: pct` sin cantidad, aunque la subfila guarde un resto (R2);
  - `PUT …/importes` la guarda como caja del mes aunque llegue con
    `obra_ide`, y dos elementos de la misma caja dan 422 «repetido» (R4);
  - el payload lleva en cada línea la caja con `reparto: pct` y la cantidad
    del mes, en una sola lectura (R5).
- **Copiar el mes no propaga los restos por obra** (R11). `_sin_propuesta(lineas,
  tipos)`: en la subfila de un tipo por %, `cantidad`, `copiado` y
  `comentario` llegan a `None`. La partida elegida se conserva. Los tipos
  por obra, los vinculados que no son de cantidad y las llamadas sin
  `tipos` se comportan como antes. `CopiarPeriodoAnterior` y
  `CopiarTrabajadorAnterior` reciben `tipos` en `__init__`, y las dos rutas
  les pasan `_tipos(contenedor)`.
- **Docs** (R12): en `docs/ARCHITECTURE.md`, `#regla-vinculado`, bloque
  «Cantidad y comentario»:
  - la caja aparece como `pct`, con el ejemplo 300 € → 180/120;
  - se explica que no hay ajuste de céntimos;
  - el reparto «por obra» queda sin tipo («Hoy ningún tipo lo usa»);
  - «Se omite» ya no trae el motivo de la caja por obra;
  - los restos por obra no se copian (R11) ni se pasan al mes (D2);
  - se cita la decisión del humano del 2026-11-25.
- **Transfer y front, sin tocar** (R3, R6-R9): tests de regresión.

## Tareas y commits

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `5532000` | `config.yaml`; `test_f080_caja_api.py` (R1, R2, R4, R5) en rojo antes del cambio; los dos tests de requirements §5 |
| T2 | `f854d02` | `dedicacion-transfer/tests/test_f080_reglas_caja.py` (R6-R8), 10 tests |
| T3 | `c774908` | `dedicacion-front/tests/test_f080_caja_front.py` (R3, R9), 3 tests |
| T4 | `f7b8889` | `use_cases.py` (`_sin_propuesta` + `_subfila_copiada`, `tipos` en las dos copias), `routes.py`; tests de R11 en rojo antes del código |
| T5 | `1f36e48` | `docs/ARCHITECTURE.md`; tests de R12 |
| T6 | (este informe) | lista de tests cambiados y trazas RED |
| T7, T9, T10 | — | MANUAL del humano (M3, M1, M4): pendientes, abajo |
| T8 | — | `azure-apps/dedicacion.md`: le toca al líder (design §12); no lo he tocado |
| T11 | (este informe) | `bash harness/init.sh`, abajo |

## Ficheros

- Código (api): `services/dedicacion-api/config/config.yaml`,
  `application/use_cases.py` y `interface_adapters/api/routes.py`.
- Tests nuevos:
  - `services/dedicacion-api/tests/test_f080_caja_api.py` (20 items);
  - `services/dedicacion-transfer/tests/test_f080_reglas_caja.py` (10);
  - `services/dedicacion-front/tests/test_f080_caja_front.py` (3).
- Tests cambiados: los dos de la lista cerrada (abajo).
- Documentación: `docs/ARCHITECTURE.md`.
- Rastro: `specs/F-080-caja-por-trabajador/tasks.md` (casillas T1-T6 y T11)
  y `progress/current.md`.
- Sin tocar (design §5):
  - el transfer entero y `static/js/app.js`;
  - de la api: `main.py`, `domain/importes.py`, `registro_sigrid.py`,
    `traer_sigrid.py`, `schemas.py`, `orm_models.py` y `esquema.py`;
  - `docs/INTEGRACION.md` y `azure-apps`.

## Decisiones de diseño y desviaciones

- **`_subfila_copiada(v, tipos)`** es una función auxiliar privada de
  `_sin_propuesta`, para que cada rama se lea por separado. El
  comportamiento es exactamente el de design §6. No es una desviación.
- **`tipos` vacío (`{}`) equivale a sin tipos** (`if tipos`). Es lo que
  devuelve `_tipos(contenedor)` cuando el contenedor no trae importes (los
  dobles de antes), y el test de las rutas lo comprueba.
- **Sin desviaciones respecto a la spec.**

## Tests anteriores que cambian (lista CERRADA, requirements §5): medida

Con la config nueva y los tests aún sin tocar (`git stash` de los dos
ficheros), en la suite de la api fallaron **exactamente estos dos**:

```
FAILED tests/test_f069_importes_dominio.py::test_f069_r1_config_versionada - ...
FAILED tests/test_f069_importes_api.py::test_f069_r15_el_contenedor_pasa_tipos_y_precio
2 failed in 6.53s
```

- `test_f069_r1_config_versionada`: `CAJA` pasa a `TipoCantidad("eur",
  "pct")`. `VIAJE` y `VP` no cambian.
- `test_f069_r15_el_contenedor_pasa_tipos_y_precio`: compara con
  `{**TIPOS, "CAJA": TipoCantidad("eur", "pct")}`, los tipos de la config.
  `TIPOS`, con la caja por obra, sigue siendo el doble de los tests del
  mecanismo `obra`.

Con los dos ajustados, la suite entera de la api quedó en verde (`1704
passed`): no falló ningún otro test.

## Fase RED

**T1 (R1, R2, R4, R5)**, antes de cambiar `config.yaml`:

```
$ cd services/dedicacion-api && .venv/Scripts/python.exe -m pytest tests/test_f080_caja_api.py -k "r1 or r2 or r4 or r5" -q --tb=line -p no:cacheprovider -W ignore
F.FFFFFFF                                                                [100%]
E   AssertionError: assert {'CAJA': Tipo...eparto='pct')} == {'CAJA': Tipo...eparto='pct')}
      {'CAJA': TipoCantidad(unidad='eur', reparto='obra')} != {'CAJA': TipoCantidad(unidad='eur', reparto='pct')}
test_f080_caja_api.py:53: AssertionError
E   AssertionError: assert [] == [{'vinculado_...: 'eur', ...}]
test_f080_caja_api.py:81: AssertionError
E   KeyError: 'importes'
test_f080_caja_api.py:95: KeyError: 'importes'
E   domain.errors.ImporteInvalido: El vinculado 30 no tiene línea en la obra None (postventa=False)
application\use_cases.py:1458: domain.errors.ImporteInvalido
E   KeyError: 30
test_f080_caja_api.py:113: KeyError: 30
E   Failed: DID NOT RAISE ImporteInvalido
test_f080_caja_api.py:127: Failed: DID NOT RAISE ImporteInvalido
E   AssertionError: assert (True, 'eur',...True, 'resto') == (True, 'eur',...False, 'caja')
      At index 2 diff: 'obra' != 'pct'
test_f080_caja_api.py:148: AssertionError
E   AssertionError: assert ('obra', None, False, None) == ('pct', None, False, None)
test_f080_caja_api.py:159: AssertionError
8 failed, 1 passed, 1 warning in 6.32s
```

El que pasa es `test_f080_r1_el_reparto_obra_sigue_siendo_valido`, que por
diseño no cambia (D1 a). Después del cambio pasaron los 9.

**T4 (R11)**, antes de tocar `use_cases.py` y `routes.py`:

```
$ cd services/dedicacion-api && .venv/Scripts/python.exe -m pytest tests/test_f080_caja_api.py -k r11 -q --tb=line -p no:cacheprovider -W ignore
FFFFFFF                                                                  [100%]
E   TypeError: CopiarTrabajadorAnterior() takes no arguments
E   TypeError: CopiarPeriodoAnterior() takes no arguments
E   TypeError: CopiarTrabajadorAnterior() takes no arguments
E   TypeError: CopiarPeriodoAnterior() takes no arguments
E   TypeError: _sin_propuesta() takes 1 positional argument but 2 were given
E   TypeError: object.__init__() takes exactly one argument (the instance to initialize)
  File "...\interface_adapters\api\routes.py", line 267, in copiar_periodo_anterior
    resultado = CopiarPeriodoAnterior().ejecutar(
E   TypeError: object.__init__() takes exactly one argument (the instance to initialize)
  File "...\interface_adapters\api\routes.py", line 514, in copiar_trabajador_anterior
7 failed, 9 deselected in 6.11s
```

Este rojo es de firma: sin `tipos` no había forma de probar la guarda.
Después del código pasaron los 7, y también `test_f069_importes_api.py -k
r8`, sin tocarlo (`7 passed`).

**T5 (R12).** Con el `ARCHITECTURE.md` de antes (`git stash` del fichero),
`test_f080_r12_la_doc_dice_caja_por_pct_y_sin_restos` falla:
`assert 'Hoy `CAJA` (€, `pct`), …' in '**Cantidad y comentario (F-069).**
…'`.

**T2 y T3 (transfer, front): no hay RED**, como prevé tasks.md: el código
es el de F-069. Para comprobar que los tests sí distinguen, se pasaron con
la caja en `reparto: "obra"` (una copia temporal del fichero, ya borrada):

- transfer: `10 failed in 0.49s`;
- front: `3 failed in 0.95s`.

Fallan todos, así que los tests distinguen la caja por % de la caja por
obra.

## Salida de `init.sh`

`bash harness/init.sh` (2026-11-25, sobre `95227f3`), salida real:

- `ENTORNO LISTO`, código 0, sin `[KO]`.
- Raíz: `2319 passed, 47 skipped in 855.83s`.
- Servicios:
  - api: `1713 passed`;
  - front y transfer: en verde, servidos de la caché del árbol en HEAD.
- `PUERTA COBERTURA: 100.0% de 13 líneas cambiadas cubiertas (13/13,
  umbral 90% (del nivel critico)…)`.
- `PUERTA TAMAÑO … impl 214/220` y `PUERTA CARRIL: N/A (… critico …)`.
- `CAPA E2E: N/A`.
- ruff, 442 avisos (439 antes). Los 3 nuevos eran de mis tests y ya están
  corregidos (`4e297a0` y el siguiente). Resultado de la repetición
  posterior (sobre `0ea4d30`): `ENTORNO LISTO`, sin `[KO]`, ruff 439, raíz `2319 passed`, api `1713`, front `614` (ejecutada), transfer de caché; cobertura 13/13.

## Verificaciones MANUAL pendientes (humano)

- **M1 (T9), justo antes de desplegar, solo lectura en producción.** La
  lectura de `progress/manual_F-080.md` (`GET /api/v1/periodos` y `GET
  /api/v1/periodos/{anio}/{mes}/cuadrante?empresa={1,18,25,31}`). Esperado:
  **0** subfilas de caja por obra con `cantidad`; si hay alguna, PARA (D2, D3).
- **M3 (T7), en local con `OBRA_PRUEBAS_FORZAR=true`.** 300 en «CAJA …» de un
  trabajador al 60/40 (o con postventa) y «⇪ Sigrid»: el modal dice «180,00 €
  de 300,00 €» y «120,00 € de 300,00 €». **Cancelar** (solo preflight).
- **M4 (T10), en producción.** Desplegar **solo la api**, sin «Sincronizar
  Sigrid»; Ctrl+F5; una casilla de caja por trabajador y ninguna «Caja ·
  obra». Si se abre el modal, solo preflight y **Cancelar**.
- **T8, del líder.** `azure-apps/dedicacion.md` en commit aparte (design §12):
  nota del redespliegue y, en «Desde F-069», la caja por % (F-080). No lo he
  tocado, ni el aviso a `partes` (las `CO` de caja ya no llevan `can` 1).

## Fuera de alcance

Retirar el reparto `obra` (D1 b), la pasada de restos (D2) y el corte por
periodo (D3 b). La nota en F-071 («la caja ya no tiene `can` 1») es del líder.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | api 1713, front 614, transfer 2021, raíz 2319 (+47 skipped): todos en verde. F-080 aporta 18 + 10 + 3 |
| Cobertura de las líneas cambiadas | 100,0 % (13/13), umbral 90 % (`PUERTA COBERTURA`) |
| Mutantes generados / supervivientes | sin medir todavía: la campaña (`python -m harness.mutacion --feature F-080`) va en la pasada de campaña, tras el APPROVED (`implementer.md`) |
| Tiempo de la suite | api 61 s (con cobertura, en `init.sh`), front 67 s, transfer 27 s, raíz 856 s |
| Capa e2e | `CAPA E2E: N/A` (ningún servicio declara el bloque e2e) |
