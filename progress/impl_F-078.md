# F-078 · Informe del implementer (`critico`)

Rama `feature/F-078-registrar-por-paquetes` (worktree `porcentajes-f078`).
Spec aprobada por el humano el 2026-11-27 (D3 a, D4 d; D1, D2 y D5-D11 la (a)).

## Hecho

El botón «Registrar en Sigrid» (`#btn-registro`, el mismo, sin botón nuevo)
registra ahora un **paquete**: con 2 o más seleccionados visibles, esos; con 0
o 1 (el cursor cuenta como 1), todos los visibles con los filtros; nunca un
oculto. Su rótulo dice a quién («Registrar seleccionados (M)» / «Registrar
visibles (N)») y se recalcula en cada pintado de la tabla; se desactiva con el
periodo no abierto, sin visibles, con la selección oculta por el filtro (con
`title` que lo dice) o tras un corte. El front solo manda los `ide`
(`trabajador_ides`); la api decide qué líneas van. En la api, las dos rutas
del registro validan `trabajador_ides` (lista no vacía de enteros, sin
repetidos, en su orden; 422 si no, o si viene junto a un `trabajador_ide` no
nulo) y el registro filtra con `IN` asignaciones e incidencias: cada trabajador
entero, lote completo con sus sobrantes sin `obra_ide`. El transfer no se toca.
El «⇪ Sigrid» de fila y editor sigue igual (un trabajador, sin la clave). La
ruta del mes entero sigue en la api, sin ningún botón que la pida.

## Tareas y commits

| Tarea | Commit |
|---|---|
| T1 api, rutas: `_trabajador_ides` (R2-R5), RED | `e4db2d0` |
| T2 api, registro: `_filtro_trabajadores` con `IN` (R1, R6, R9-R11), RED | `d075e04` |
| T3 api, tests R7, R8, R24 (sin RED: el código ya era el de T2) | `bdf7ac9` |
| T4 front, puras `alcanceRegistro`, `rotuloRegistro`, `tituloRegistro`, `cabeceraPaquete` (R12-R14, R20), RED | `e879249` |
| T5 front, botón, flujo, modal y aviso (R12, R15-R22), RED | `6a12868` |
| T6 api, test R23 (sin RED: fija lo de hoy, D6) | `1e5fb35` |
| T7 docs `ARCHITECTURE.md` e `INTEGRACION.md` + test R25 | `6a7d26a` |
| T8 `azure-apps/dedicacion.md` | `azure-apps` `ce8437c` (sin push) |
| T9 MANUAL M1 (R26) | **sin marcar, del humano** |
| T10 este informe | `d316311` |
| T11 `bash harness/init.sh` en verde | este commit |

## Ficheros

- api: `routes.py` (`_trabajador_ides`, `_paquete`: la clave va al registro solo si viene,
  R5) y `registro_sigrid.py` (`_filtro_trabajadores`: `IN` / `==` / nada, en `_payloads`,
  `_sumar_incidencias`, `preflight` y `ejecutar`).
- front: `app.js` (puras de T4 y `nTrabajadores`; `pintarBotonRegistro`, `registrarPaquete`,
  `registro.paquete`/`enVuelo`; cambios en `pedirPreflight`, `registroPreflight`,
  `pintarModalPreflight`, `registroEjecutar`, `esperarRegistroCortado`) e `index.html` (ayuda).
- docs: `ARCHITECTURE.md`, `INTEGRACION.md`; `azure-apps/dedicacion.md` (commit aparte).
- Tests nuevos: `test_f078_paquete_api.py` y `test_f078_paquete_front.py`. El transfer, sin tocar.

## Decisiones y desviaciones (justificadas también en `progress/current.md`)

1. **`esperarRegistroCortado` sí se toca.** El design §4 la pone en «no se tocan», pero
   el §6 y R19 piden que al desbloquearse vuelva al rótulo de su alcance. Manda el
   requisito: solo cambia la restauración (`dataset.rotulo` o «Registrar en Sigrid») y
   la llamada a `pintarBotonRegistro` si existe; el resto, igual.
2. **La ruta pasa `trabajador_ides` solo si viene** (`_paquete`): sin paquete, el registro
   recibe exactamente las claves de hoy (test R5 lo compara).
3. **`pintarBotonRegistro` va antes del `forEach` de `renderTabla`**, no al final:
   `test_f050_t15f_total` exige que la función termine en `sincronizarAnchoTabla()`.
4. **`pedirPreflight` usa dos `JSON.stringify`** (con y sin paquete): `test_f050_modal_registro`
   exige el literal de hoy; sin paquete, el cuerpo es byte a byte el de siempre.
5. **`registro.enVuelo`** (nuevo): con un preflight del botón en curso, el repintado de la
   tabla no pisa «Analizando…» ni lo reactiva (design §6, «hay un preflight en vuelo»).
6. **Singular**: «1 trabajador» en el título del modal, el aviso final y el `title`.
7. **Rótulo bloqueado**: «Registrar seleccionados (0)», desactivado y con el `title`.
8. **Orden de obras del paquete**: el del modo trabajador (una obra donde el paquete solo
   tiene incidencias va al final, `_grupo`), no el del mes. R6 se comprueba obra a obra y
   un paquete de uno da las mismas peticiones que `trabajador_ide` (test).
9. `registrarPaquete` calcula el alcance **antes** de `guardarAhora` (lo que decía el
   rótulo al pulsar) y, tras un corte, ni guarda ni pide nada.

## Tests por requisito

La tabla requisito → test está en `progress/review_F-078.md` («Trazabilidad»),
contrastada por el reviewer; R26 es la MANUAL T9.

## Tests anteriores que cambian

**Ninguno** (lista cerrada de requirements §6): `git diff dev --stat` sobre `tests/`
solo lista los dos ficheros nuevos.

## Fase RED (trazas reales)

Cada test se escribió y ejecutó antes que su código de producción (salida
recortada de `pytest -q --tb=line`, desde la carpeta del servicio).

**T1** (rutas), `.venv/Scripts/python -m pytest tests/test_f078_paquete_api.py -q --tb=line -p no:cacheprovider -k "r2 or r3 or r4 or r5"`:

```
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF..FFFFFFFFFFFF........ [100%]
E   AssertionError: {"ok":true,"obras":[]}
    assert 200 == 422
E   KeyError: 'trabajador_ides'
62 failed, 10 passed, 1 warning in 35.02s
```
(Los 10 verdes: los 8 de R5, que fijan lo de hoy, y los 2 de
`r4_trabajador_roto…`, que fijan F-056.) En verde tras `_trabajador_ides`,
con `test_f056_trabajador_ide.py`, `test_f024_rutas_empresa.py`,
`test_f054_rutas.py` y `test_f050_preflight_obra.py`: 212 passed.

**T2** (registro), `… -k "r1 or r6 or r9 or r10 or r11"`:

```
E   TypeError: RegistroSigrid.preflight() got an unexpected keyword argument 'trabajador_ides'
E   TypeError: RegistroSigrid.ejecutar() got an unexpected keyword argument 'trabajador_ides'
38 failed, 4 passed, 70 deselected, 1 warning in 15.70s
```
(Verdes: `r2_r11_sin_tope`, de rutas, ya en T1, y `r1_r5_un_trabajador…`,
que fija F-056.) En verde: 120 passed en el fichero.

**T4** (puras), `.venv/Scripts/python -m pytest tests/test_f078_paquete_front.py -q --tb=line -p no:cacheprovider -k "r12 or r13 or r14 or r20"`:

```
E   AssertionError: no existe la función alcanceRegistro en app.js
30 failed, 2 deselected in 1.02s
```

**T5** (botón y flujo), `… tests/test_f078_paquete_front.py -q --tb=line`:

```
................................FFFFFFFFFFFFFFF.FF.F.FFF...FF.F          [100%]
E   AssertionError: assert [{'trabajador_ide': None}] == [{'trabajador...': [3, 1, 2]}]
      At index 0 diff: {'trabajador_ide': None} != {'trabajador_ide': None, 'trabajador_ides': [3, 1, 2]}
E   assert 'registrarPaquete()' in 'document.addEventListener("DOMContentLoaded", () => {\n  const b = $("#btn-registro");\n  if (b) b.addEventListener("click", () => registroPreflight(null));\n});'
E   assert 'pintarBotonRegistro(visibles);' in 'function renderTabla() { … sincronizarAnchoTabla();\n}…'
E   assert '· 3 trabajadores (visibles)</h2>' in '<h2>Registrar en Sigrid · nov 2026</h2>…'
E   assert 'Registrar: seleccionados (2+) o visibles' in '<!-- templates/index.html -->…'
24 failed, 39 passed in 34.75s
```
(La primera es la avería de la feature: el clic pedía el mes entero. Los 39
verdes: los 32 de T4 y los que fijan lo de hoy: «⇪ Sigrid» sin la clave, el
corte del hotfix y el modal sin paquete.) En verde: 63 passed.

T3, T6 y T7 no tienen RED: T3 y T6 fijan lo que ya hace el código de T2 (R7,
R8, R24; R23, D6), y T7 es documentación.

## Salida de `init.sh`

`bash harness/init.sh` una sola vez, al final (salida a un fichero del scratchpad,
sin pipes): **exit 0, ningún `[KO]` ni aviso**. Líneas clave:

```
2319 passed, 47 skipped in 1372.26s (0:22:52)
[OK] pytest en verde (con medición de cobertura)
1848 passed, 1 warning in 171.86s (0:02:51)
[OK] servicio api (services/dedicacion-api): pytest en verde
771 passed, 19 warnings in 241.59s (0:04:01)
[OK] servicio front (services/dedicacion-front): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde (caché: … sin cambios …)
[OK] PUERTA COBERTURA: 100.0% de 29 líneas cambiadas cubiertas (29/29, umbral 90% (del nivel critico), nivel critico; diff desde b383f3c4bf, merge-base con dev)
[OK] PUERTA TAMAÑO: F-078 dentro de los topes (requirements 150/150, design 233/250, impl 166/220)
[OK] PUERTA CARRIL: N/A (F-078 es de nivel critico: no declara límites)
[OK] CAPA E2E: N/A (ningún servicio declara el bloque e2e)
```

El test intermitente conocido (`test_f059_r9_timeout_mata_el_arbol_y_no_es_rojo`)
no falló: no hubo que repetir nada.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz 2319 passed / 47 skipped; api 1848 passed; front 771 passed; transfer en verde (caché) |
| Casos de test nuevos | api 135 (`test_f078_paquete_api.py`), front 63 (`test_f078_paquete_front.py`) |
| Cobertura de líneas cambiadas | 100,0 % (29/29, Python; umbral 90 % del nivel `critico`) |
| Mutantes (herramienta) | 18 generados → 9 candidatos (uno por línea), 9 evaluados, **9 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto; **4 workers**; 630,7 s |
| Mutantes (a mano, complementarios) | 8 evaluados, **8 muertos** (tabla de la pasada de campaña) |
| Tiempo de la suite | raíz 22:52; api 2:51; front 4:01 |
| Capa e2e | N/A (línea `CAPA E2E` de `init.sh`) |

La cobertura de líneas y la mutación solo miden Python: el cambio de `app.js`
(la mitad de la feature) no lo mide `init.sh`; lo cubren los 63 tests node del
front, que ejecutan el código real.

## Pendiente

- T9 (MANUAL M1, R26) del humano, en local y en modo pruebas; resultado en
  `progress/manual_F-078.md`.
- Push del humano: la rama y `azure-apps` (`ce8437c`).
- El reviewer de evidencias (pasada de campaña hecha, abajo).

## Pasada de campaña (2026-11-27, tras el APPROVED de la review principal)

**Mutación** (`python -m harness.mutacion --feature F-078`, por defecto 4
workers; informe `progress/mutacion_F-078.md` y estado `.json`). SHA medido
`b15042ab2943cfa06cba80cd4d6bd5a4f4ce3630` (HEAD tras O3; el código de
producción es el mismo que aprobó la review en `8ca80b5`). Alcance: 89 líneas
(`registro_sigrid.py` 42, `routes.py` 47), 18 mutantes generados → 9 candidatos
(uno por línea) ≤ 100: **campaña completa**, sin muestreo. **9 muertos, 0
supervivientes**, 0 timeouts, 0 indeterminados, 0 sin veredicto; sin cabecera
«⚠ CAMPAÑA NO VÁLIDA». Línea base 123,2-123,5 s por worker; media 70,1 s ×
4 workers = 280 s por mutante (coherente con la base, RM2); coste por mutante
630,7 × 4 ÷ 9 = 280 s (> 1 s). Timeout efectivo 248 s. Ningún superviviente:
no hubo nada que reproducir, justificar ni matar, y no se tocó producción ni se
quitó código defensivo (RM6).

**Mutantes a mano, complementarios.** La herramienta solo genera
comparaciones, veracidad y lógicos (9 de 89 líneas); se añadieron 8 sobre las
llamadas y argumentos que sostienen R1-R5, aplicados en el árbol, juzgados con
`test_f078_paquete_api.py` + `test_f056_trabajador_ide.py` (185 tests) y
restaurados con `git checkout` (árbol limpio después); muerto con un subconjunto, muerto con la suite.

| # | Fichero | Original → mutado | Resultado |
|---|---|---|---|
| M1 | `registro_sigrid.py` | `return [columna.in_(list(trabajador_ides))]` → `return []` | muerto, 48 fallos |
| M2 | `registro_sigrid.py` | (preflight) `trabajador_ides=trabajador_ides)` → `trabajador_ides=None)` | muerto, 26 |
| M3 | `registro_sigrid.py` | (ejecutar) `self._filtro(empresa), trabajador_ides=trabajador_ides)` → `…=None)` | muerto, 22 |
| M4 | `registro_sigrid.py` | `quitadas, trabajador_ides)` → `quitadas, None)` | muerto, 44 |
| M5 | `routes.py` | `return {"trabajador_ides": trabajador_ides}` → `return {}` | muerto, 14 |
| M6 | `routes.py` | `if x is None:` → `if x is None and False:` | muerto, 4 |
| M7 | `routes.py` | `return ides` → `return ides[:1]` | muerto, 8 |
| M8 | `routes.py` | (preflight) `_trabajador_ides(…, trabajador_ide)` → `_trabajador_ides(…, None)` | muerto, 3 |

**RM7**: lo adelantó la review (R8 con A12, R17 con F5); este delta no toca esas líneas.
**`app.js`** no se muta: lo cubren los 63 tests node y las rupturas F1-F10 de la review.

**O3 · ruff** (`b15042a`): ISC004 (api l. 158; front l. 323, 423) y PIE808 (front l. 102), con paréntesis
y `range(5)`, sin cambiar lo que comprueban: `ruff check .` da 439, como `dev` (antes, 443).
**`init.sh` de la pasada** (sobre `12a2534`): exit 0, 0 `[KO]`; raíz 2319 passed / 47 skipped (26:28), api 1848,
front 771, transfer en verde (caché); COBERTURA 100 % (29/29); TAMAÑO OK; ruff 439 (`[AVISO]`, deuda previa).
