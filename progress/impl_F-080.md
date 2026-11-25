<!-- progress/impl_F-080.md -->
# F-080 · Informe del implementer (`critico`)

Rama `feature/F-080-caja-por-trabajador`. Spec aprobada por el humano el
2026-11-25 (D1, D3, D4, D5 y D7 la (a); D2 sin pasada de restos; D6
retirada). Solo cambia la api. Del transfer y del front solo hay tests
nuevos.

## Hecho

- **R1.** `config.yaml`: `CAJA: {unidad: eur, reparto: pct}`; el comentario
  de `importes` cita F-080. `obra` sigue siendo válido, sin tipo (D1 a).
- **R2, R4, R5**, probados con los tipos de la config real: una casilla de
  caja por trabajador y subfilas `pct` sin cantidad; `PUT …/importes` la
  guarda como caja del mes aunque traiga `obra_ide` (dos de la misma, 422
  «repetido»); el payload lleva la cantidad del mes en una sola lectura.
- **R11.** `_sin_propuesta(lineas, tipos)`: la subfila de un tipo por % llega
  sin `cantidad`, `copiado` ni `comentario`; la partida elegida, por obra, no
  de cantidad y sin `tipos`, como antes. Las dos copias reciben `tipos` en
  `__init__` y sus rutas les pasan `_tipos(contenedor)`.
- **R12.** `docs/ARCHITECTURE.md` `#regla-vinculado`: caja `pct` (300 € →
  180/120), sin ajuste de céntimos, «por obra» sin tipo, «Se omite» sin el
  motivo de la caja por obra, restos no copiados (R11) ni pasados (D2), cita
  del 2026-11-25.
- **R3, R6-R9.** Transfer y front sin tocar: solo tests de regresión.

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

- Código (api): `config/config.yaml`, `application/use_cases.py`,
  `interface_adapters/api/routes.py`. Doc: `docs/ARCHITECTURE.md`.
- Tests nuevos: api `test_f080_caja_api.py` (18 items, `--collect-only`),
  transfer `test_f080_reglas_caja.py` (10), front `test_f080_caja_front.py`
  (3). Cambiados: los dos de la lista cerrada (abajo).
- Sin tocar (design §5): el transfer, `app.js`, el resto de la api y
  `azure-apps`.

## Decisiones de diseño y desviaciones

- `_subfila_copiada(v, tipos)`: función auxiliar de `_sin_propuesta`, con el
  comportamiento de design §6. `tipos` vacío (`{}`, lo que da `_tipos` sin
  importes) equivale a sin tipos. Sin desviaciones respecto a la spec.

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

`bash harness/init.sh` de esta pasada (2026-11-25, tras la campaña), salida
real: `ENTORNO LISTO`, código 0, sin `[KO]`; raíz `2319 passed, 47 skipped`;
api `1713 passed`, front `614 passed`, transfer en verde;
`PUERTA COBERTURA: 100.0% de 13 líneas cambiadas cubiertas (13/13, umbral
90% (del nivel critico)…)`; `PUERTA TAMAÑO` y `PUERTA CARRIL: N/A (…
critico …)` en `[OK]`; `CAPA E2E: N/A`; ruff 439 avisos (deuda previa: los 3
que añadían mis tests se corrigieron en `0ea4d30`).

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
| Cobertura de las líneas cambiadas | 100,0 % (13/13), umbral 90 % del nivel `critico` (`PUERTA COBERTURA`) |
| Mutantes generados / supervivientes | 9 generados, 3 candidatos (uno por línea, campaña completa: 3 ≤ tope 100), **3 muertos, 0 supervivientes**, 0 timeouts; SHA medido `eaab1f0`. Más 3 a mano (M1-M3, `routes.py` y la guarda de RM6): 3 muertos. Detalle en `progress/mutacion_F-080.md` |
| Workers de la campaña | 3 (lanzada sin `--workers`: el default de la máquina, que el informe registra como `--workers 3`); tiempo total 200,8 s ⇒ coste por mutante 200,8 × 3 ÷ 3 = 200,8 s; base 72,5 s, timeout 146 s |
| Tiempo de la suite | api 116 s y front 98 s (con cobertura, en `init.sh`), transfer 27 s, raíz 771 s |
| Capa e2e | `CAPA E2E: N/A` (ningún servicio declara el bloque e2e) |
