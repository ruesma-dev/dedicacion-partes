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

- **`bash harness/init.sh`**: ENTORNO LISTO, exit 0.
  - Raíz: `418 passed, 1 skipped`.
  - Cobertura: `[OK]` 100 % (164/164).
  - Tamaño: dentro del tope.
  - ruff: 198 avisos.
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
- **`89f0d30`, ruff.** Solo cambia la forma:
  - `Optional[X]` pasa a `X | None`. Todo es Python 3.12, en los Dockerfile y en
    `from __future__`, y pydantic lo acepta en `UniversoIn`.
  - Se reordenan imports, sobra un `noqa` y cambian `Decimal("50")` a `Decimal(50)`, un
    `dict()` a literal y `getattr` a acceso directo.
  - Ningún assert cambia de valor esperado.
  - Contra `dev` sobre los mismos ficheros: 66 avisos antes y 64 ahora. Los 5 ficheros
    nuevos de F-025 tienen 0.
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
  [x] Las tres trampas:
  - Escala: intacta.
  - Postventa: `admite_postventa` es independiente de `activa`, con clave
    `(obra, es_postventa)`.
  - Sigrid: ninguna escritura ni SQL nueva.
- **C3 bis**: N/A, porque no toca `docs/referencia/`.
- **C4 ter**: N/A, porque no hay `harness/rutas_sensibles.json`.
- **C4** [x] R1-R25 tienen tests `test_f025_rN_*` en verde (tabla abajo), y R26 es
  documental, con la T10 · [x] sin red ni BBDD · [x] las MANUAL en `current.md`.
- **C4 bis**
  - [x] `rigor` declarado.
  - [x] Fase RED: trazas de T1-T8 y del ciclo 2, y reproduje una.
  - [x] Cobertura 100 %.
  - [x] Recálculo de la mutación (57).
  - [x] Campaña de 552 s no reejecutada, y lo digo aquí.
  - [x] Coste por mutante de 9,7 s.
  - [x] Sin «CAMPAÑA NO VÁLIDA».
  - [x] RM1, [x] RM2, [x] RM5 en N/A justificado y [x] RM6, como arriba.
  - [x] 0 supervivientes y nada en `PENDIENTE`.
  - [x] «Evidencias» trae los cuatro números y los workers (`--workers 1`).
  - [x] Ningún N/A sin motivo.
- **C5** [x] T1-T9, T11, T12 y T15 en `[x]`, con un commit `F-025 Tn:` cada una, y los del
  ciclo 2 como `F-025 C2-Tn`. T10, T13 y T14 son N/A **justificado**: son MANUAL (humano) y
  bloquean el `done`, no la review · [x] sin ficheros temporales · [x] `features.json` en
  `in_progress`.

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

- **D1**: el preflight y el universo usan las mismas `cargar_catalogo_postventa` y
  `casar_postventa`. La api no casa y el front solo pinta.
- **D2 = B y D8 = A**: casa el código exacto o un prefijo seguido solo de letras. `CP.1`,
  `0678.MO`, `CI.7.5` y `0611` quedan fuera.
- **`#regla-p5`** sigue siendo cierta, y los tests de F-002 están en verde.
- **Tests anteriores cambiados**: solo los de design §7.1, revisados fila a fila. Ninguno
  pierde exigencia.
- **`_nodos_pv`**: ha desaparecido.
- **Script de verificación**: no contiene `ejecutar` y solo llama a servicios locales.
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
