Revisión incremental desde 171464d (pasada 2): `git diff d388e00..HEAD` (HEAD `2790369`; `d388e00` solo añadió este informe)

# F-025 · Review · Obras de postventa sacadas de los capítulos de POSTV2

**Veredicto: APPROVED.**

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige C1-C5, fase RED,
cobertura ≥ 80 %, una campaña de mutación completa con 0 supervivientes, RM1-RM6 y las
MANUAL listadas con su comando exacto.

## Pasada 2 · Lo que se revisó

El delta trae el rastro (`3bfed65`, `2790369`) y el ciclo 2: `c588879`, `e640f67`,
`89f0d30` y `7fda87a`. Nada del delta invalida lo aprobado en la pasada 1: no cambia ninguna
firma pública y no se mueve ningún fichero. El alcance de la campaña crece en 11 líneas, y la
campaña se ha repetido.

- **`bash harness/init.sh`**: ENTORNO LISTO, exit 0 (raíz `418 passed, 1 skipped`;
  cobertura `[OK]` 100 %, 164/164; tamaño dentro del tope; ruff 198).
- **Suites sin caché**: como init.sh usó la caché por servicio, las relancé sobre una copia
  `git archive HEAD` en el scratchpad con `-p no:cacheprovider`. Api `509 passed`, transfer
  `379 passed`, front `28 passed`; coincide con impl §8.
- El árbol queda limpio.

### Rastro (los tres cambios pedidos)

1. `grep -n "Ninguna feature" progress/current.md` sale **vacío**. La cabecera dice
   «F-025 en curso … review 2 lanzada». Hecho.
2. «Lo siguiente» dice «Primero cerrar y desplegar F-025»; la frase del spec-author ha
   desaparecido. Hecho.
3. La sección F-025 trae las «Condiciones de despliegue»: transfer antes o con la api (si
   no, 502), sync justo después y retirada del aviso de CP/OT. Hecho.

La MANUAL sigue con su comando exacto: T10 (pendiente en `azure-apps`), T13 y T14.

### Ciclo 2 (las observaciones de la pasada 1, recogidas)

- **`c588879`, el `ide` a entero.** Se convierte en `pedir_universo` y en `depurar_obras`,
  igual que en `sincronizar`.
  - **RED reproducida** en la copia: devolviendo `depurar_obras` a
    `fila["ide"] in universo`, `test_f025_r13_el_ide_en_texto_admite_postventa_igual` falla
    con `{'12': (True, False)} != {'12': (True, True)}`, que es la segunda traza de impl §6 bis.
  - Un `ide` nulo ahora daría error en el preview, pero `obr.ide` es PK y `sincronizar` ya
    hacía `int()`: no hay regresión.
- **`e640f67`, `entero_o_none` público** en `domain/normalizacion.py`, junto a
  `texto_o_none`.
  - `filtros_maestros` lo importa con el alias `_entero`, así que sus 8 usos previos no
    cambian.
  - `sync_pipeline` ya no importa nombres privados, y lo vigila un test con `ast`.
- **`89f0d30`, ruff**, solo forma: `Optional[X]` → `X | None` (Python 3.12 en los
  Dockerfile, `from __future__`, pydantic lo acepta en `UniversoIn`), orden de imports, un
  `noqa` sobrante, `Decimal(50)`, literal en vez de `dict()` y `getattr` directo. Ningún
  assert cambia de valor esperado. Contra `dev`, mismos ficheros: 66 → 64 avisos; los 5
  nuevos de F-025, 0.
- **Tests anteriores**: el delta solo toca `test_f025_*`. Hay 4 tests nuevos en
  `test_f025_sync_postventa.py`, y los cambios en los tests del transfer son de estilo
  (ruff). Ningún test de otra feature se ha cambiado, declarado o no.

### Nueva campaña (`7fda87a`)

- **Recálculo independiente** con `harness.alcance` y `generar_mutantes` en HEAD: **17
  ficheros, 469 líneas, 57 mutantes**, igual que el informe. El mutante nuevo es
  `normalizacion.py:30` (`is None` → `is not None`).
- **Resultado**: 57/57 muertos, 0 timeouts, «Sin veredicto» 0 y sin la cabecera «⚠ CAMPAÑA
  NO VÁLIDA».
- **No la reejecuté**: el informe declara **552,0 s**, por encima de 60 s. Valen el recálculo
  puro y las reglas RM.
- **Coste por mutante**: 552 × 1 ÷ 57 = 9,7 s, por encima de 1 s.
- **RM1**: midió `89f0d30`. Hasta HEAD solo cambian `progress/` y el alcance no varía.
- **RM2**: bases de 16,7 s (api) y 4,6 s (transfer), media 9,7 s con W = 1.
  57 × 9,7 ≈ 552 s, sin salto de orden.
- **RM3**: el mutante nuevo no es equivalente (`entero_o_none("28")` daría `None`); lo matan
  los tests de `r12_entero_o_none_es_del_dominio`.
- **RM5**: N/A justificado, porque no hay supervivientes ni equivalentes.
- **RM6**: no se ha quitado ninguna guarda en el ciclo 2.

## Checkpoints (estado final, pasadas 1 + 2)

- **C1** [x] init.sh termina con exit 0 · [x] están los ficheros base.
- **C2** [x] una sola feature en `in_progress` · [x] rama correcta · [x] `current.md`
  coherente y solo con la sesión activa (el `[ ]` de la pasada 1 está resuelto) · [x] toda
  feature `done` está en `history.md`.
- **C3** [x] arquitectura hexagonal (`entero_o_none` y `texto_o_none` en el dominio) ·
  [x] primera línea con la ruta · [x] sin prints, secretos ni dependencias nuevas.
  [x] trampas: escala intacta; `admite_postventa` independiente de `activa`, clave
  `(obra, es_postventa)`; ninguna escritura ni SQL nueva contra Sigrid.
- **C3 bis** N/A (no toca `docs/referencia/`) · **C4 ter** N/A (no hay `rutas_sensibles.json`).
- **C4** [x] R1-R25 tienen tests `test_f025_rN_*` en verde (tabla abajo), y R26 es
  documental, con la T10 · [x] sin red ni BBDD · [x] las MANUAL en `current.md`.
- **C4 bis** [x] `rigor` · [x] RED (T1-T8 y ciclo 2; una reproducida) · [x] cobertura
  100 % · [x] recálculo (57) · [x] campaña de 552 s no reejecutada (dicho) · [x] 9,7 s por
  mutante · [x] sin «CAMPAÑA NO VÁLIDA» · [x] RM1, RM2, RM5 (N/A justificado) y RM6, como
  arriba · [x] 0 supervivientes, nada `PENDIENTE` · [x] «Evidencias» con los cuatro números
  y `--workers 1` · [x] ningún N/A sin motivo.
- **C5** [x] T1-T9, T11, T12, T15 en `[x]` con commit `F-025 Tn:` (ciclo 2: `C2-Tn`);
  T10, T13, T14 N/A **justificado** (MANUAL, bloquean el `done`, no la review) · [x] sin
  temporales · [x] `features.json` en `in_progress`.

## Cobertura requisito → test

| R | Tests |
|---|---|
| R1-R9 | `test_f025_universo_postventa.py`: `r1` (3), `r2` cruce universo ⇔ preflight (8 obras), `r3` (2), `r4` (×4), `r5`-`r8` (2 cada uno), `r9` (3) |
| R10-R11 | `test_f025_casado_p5.py` (14 + parametrizados), `r11_el_universo_del_cruce_…` |
| R12-R16 | `test_f025_sync_postventa.py`: `r12` (6 + 4 parametrizados), `r13` (5), `r14` (2), `r15` (8), `r16` (3) |
| R17-R21 | `test_f025_cuadrante_postventa.py` / `_sync_`: `r17` (4), `r18` (6), `r19` (3), `r20` (8), `r21` (3) |
| R22-R24 | `dedicacion-front/tests/test_f025_catalogo_postventa.py` (7) |
| R25 / R26 | `r25_el_modulo_nuevo_no_lleva_el_literal` y lectura de `#regla-p5` / `INTEGRACION.md` + T10 |

## Pasada 1 (resumen; completa, `8ac020b..171464d`)

CHANGES_REQUESTED **solo por el rastro**: la cabecera de `current.md` decía «Ninguna feature
en ejecución», «Lo siguiente» estaba obsoleto y faltaban las condiciones de despliegue. Todo
resuelto en la pasada 2. Ya se verificó entonces:

- **D1**: preflight y universo usan las mismas `cargar_catalogo_postventa` y
  `casar_postventa`; la api no casa y el front solo pinta. **D2 = B y D8 = A**: exacto o
  prefijo + solo letras (fuera `CP.1`, `0678.MO`, `CI.7.5`, `0611`).
- `#regla-p5` cierta y F-002 en verde; tests anteriores cambiados solo los de design §7.1,
  fila a fila, sin perder exigencia; `_nodos_pv` fuera; el script sin `ejecutar`, solo local.
- **RM4**: los 4 «supervivientes» de la campaña en paralelo mueren en serie en una copia (el
  defecto es del arnés; encargo `0ecafc2` en `arnes-base`).
- **RM6**: quitar `and postventa_registrar` está bien, porque el invariante vive en
  `cargar_catalogo_postventa`.

## Observaciones (no bloquean)

- `current.md`, punto «Implementación», sigue con los números del ciclo 1 (api 503,
  cobertura 162/162, 56/56). Los del ciclo 2 están en el punto siguiente. Conviene unificarlos
  al cerrar.
- Para el `done` faltan T10 (commit del humano en `azure-apps`), T13 y T14 con su resultado
  real en `current.md`, y desplegar con las tres condiciones anotadas. **Nunca
  `registro/ejecutar`.**

## Automejora (propuesta, no aplicada)

Que `init.sh` contraste la cabecera de `current.md` con la feature en `in_progress` (encargo
`69df67b` de `arnes-base`). En tres features seguidas la review se ha tumbado o se ha anotado
por ese motivo.
