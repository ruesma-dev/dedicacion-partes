<!-- progress/review_F-056.md -->
Revisión incremental desde 8d30881 (pasada 2) · `8d30881..f99e39d`: solo `progress/` (3 ficheros, 0 de código)

# F-056 · Review

## Pasada 2 — **Veredicto: APROBADO** (APPROVED)

**Nivel de rigor:** `critico` (declarado). Lo aprobado en la pasada 1 hasta `8d30881` queda dado por bueno: el delta
(`191926f` esta review, `c61c351` informe, `f99e39d` `current.md`) no toca código, tests, firmas ni el alcance de la
campaña (35 líneas, 2 mutantes, SHA medido `42ddad8`), así que la mutación y su verificación siguen valiendo.
Rama `feature/F-056-validar-trabajador-ide` comprobada; árbol limpio antes y después.

**init.sh** (cachés `suite_*.ok` borradas, solo, sin pipes): exit 0, `ENTORNO LISTO`, **0 `[KO]`**; raíz 418 + 1
skipped, api 924, front 291, transfer 932; `PUERTA COBERTURA` 100 % (10/10); `PUERTA TAMAÑO` impl 197/220.

1. **B1** [x] `impl_F-056.md` «Evidencias» lleva «Workers de la campaña | 2 … coste por mutante ≈ 161 s», igual que la
   fila «Workers» de `mutacion_F-056.md`. C4 bis queda entero en [x] / N/A justificado.
2. **O2** [x] la tabla de mutantes manuales lleva fichero y línea: `routes.py:100`, `:103`, `:104`, `:107`, `:445`/`:462`;
   comprobadas contra el código (son las líneas exactas de cada texto).
3. **O1** [x] sumada a la O1 del implementer en «Lo que espera al humano»; **O3** ya en el plan (`azure-apps` al
   desplegar); la automejora, en la lista del trabajo del arnés. `current.md` describe la pasada 2 en curso.

**Checkpoints:** C1 [x]; C2 [x]; C3 [x]; C3 bis N/A (no toca `docs/referencia/`); C4 [x]; C4 bis [x] (B1 cerrado);
C4 ter N/A (sin `harness/rutas_sensibles.json`); C5 [x] (`tasks.md` N/A por `sdd: false`). Detalle en la pasada 1.

---
Pasada 1: revisión completa · `git diff dev...HEAD` (`9ff3e54..8d30881`, 11 ficheros, 5 de código)

## Pasada 1 — **Veredicto: RECHAZADO** (CHANGES_REQUESTED)

Un único bloqueo, de papeleo (B1): el código, los tests y la campaña están bien y verificados de forma independiente.
La pasada 2 será incremental desde `8d30881` y, si el delta solo toca `progress/`, no hay que repetir nada de código.

**Nivel de rigor:** `critico` (declarado en `features.json`, no por defecto): fase RED, cobertura ≥ 80 % de lo cambiado,
mutación completa con **0 supervivientes** sin justificación aceptada por el humano y MANUAL listadas con su comando.

**init.sh** (cachés `.arnes_cache/suite_*.ok` borradas, ejecutado solo, sin pipes): exit 0, `ENTORNO LISTO`, **0 `[KO]`**.
Raíz 418 passed + 1 skipped, api 924, front 291, transfer 932. `PUERTA COBERTURA: 100.0% de 10 líneas cambiadas (10/10,
umbral 80%, nivel critico)`. `PUERTA TAMAÑO: impl 196/220`. ruff 258 avisos = deuda previa: en los 5 ficheros tocados
hay 11 avisos y los mismos 11 había en `dev` (4+0+1+6); el test nuevo, «All checks passed». Árbol limpio antes y después.

## Bloqueos

1. **B1 · `progress/impl_F-056.md`, sección «Evidencias» (l. ~185-195): falta el nº de workers de la campaña.**
   `CHECKPOINTS.md` C4 bis, último punto: «Con la campaña de mutación, además, **el nº de workers** con que se lanzó».
   El informe no menciona workers en ningún sitio (`grep -i worker`: 0). Añadir a la tabla una fila del tipo
   «Workers de la campaña | 2 (por defecto) → coste por mutante 161,3 × 2 ÷ 2 = 161 s». El dato correcto está en la fila
   «Workers» de `progress/mutacion_F-056.md` (2); solo falta declararlo donde el checkpoint lo exige.
   Al corregirlo, actualizar la línea de la review lanzada en `progress/current.md` si cambia algo del estado.

## Observaciones (no bloquean; recoger o descartar por escrito)

1. **O1 · Enteros enormes.** `_entero_opcional` acepta `10**30` (o `"99999999999999999999"`): pasa como entero y
   PostgreSQL lo rechaza (`integer out of range`) ⇒ 500, no 422. No escribe nada (falla al leer), y `obra_ide` (F-050)
   tiene lo mismo. Candidato a sumarse a la O1 del implementer (validar el resto del cuerpo del registro).
2. **O2 · Tabla de mutantes manuales sin fichero:línea.** Es suplementaria (la automática dio 2, no 0), así que no le
   aplica el punto «campaña MANUAL»; aun así, para que sea reproducible al pie de la letra conviene poner
   `routes.py:100`, `:103`, `:104`, `:107` y las rutas `:445`/`:462`. La he reproducido (abajo) por el texto, que es único.
3. **O3 · `azure-apps/dedicacion.md`** (O2 del implementer): bien diferida al despliegue porque describe lo desplegado;
   ya está en `current.md`. Que no se cierre el despliegue de la api sin ella.

## Checkpoints

- **C1** [x] init.sh exit 0; existen los 7 ficheros (init.sh los lista en `[OK]`).
- **C2** [x] una sola `in_progress` (F-056); rama `feature/F-056-validar-trabajador-ide` (comprobada con `git -C . branch
  --show-current`); `current.md` abre con «En curso: F-056 … review lanzada» y el plan aprobado; «Producción, hoy» y «Lo
  que espera al humano» son las secciones permanentes de siempre, con la O1 añadida; F-055 `done` está en `history.md`.
- **C3** [x] hexagonal: `TrabajadorNoValido` en `domain/errors.py` (sin imports), mapeo HTTP en `app.py`, validación en
  `routes.py` (adaptador), filtro en `application/`; mismo patrón que `ObraNoValida`. Primera línea con ruta en el test
  nuevo; los demás ya la tenían. Sin `print`, sin TODO, sin secretos, sin dependencias nuevas (el test usa `sqlalchemy`,
  ya presente). Las tres trampas: no toca escala del porcentaje ni postventa; no añade escrituras a Sigrid (al contrario,
  impide que `ejecutar` mande el mes entero); `OBRA_PRUEBAS_FORZAR` intacto.
- **C3 bis** N/A: el diff no toca `docs/referencia/`. Barrido igualmente sobre el diff (correo, IPv4, GUID,
  `password|passwd|secret|token|apikey|api_key|AccountKey|sig=|Bearer`): 0 coincidencias reales (solo `@pytest`).
- **C4** [x] cada `acceptance` trazado (tabla abajo), 50/50 en verde; sin red ni BBDD (`TestClient` con contenedor falso
  `Settings(_env_file=None)`, `_SesionQueFiltra` en memoria, `_Transfer` falso). MANUAL: «ninguna para cerrar»; la
  comprobación opcional tras desplegar está en `current.md` con su `fetch` exacto, **solo preflight**, nunca `ejecutar`.
- **C4 bis**
  - [x] `rigor: "critico"` declarado.
  - [x] Fase RED: trazas reales pegadas (ImportError; 34 failed/16 passed; detalle de 4 centrales, entre ellas
    `ejecutar` con `0` mandando las dos obras al transfer: el fallo de la feature reproducido); luego 4 failed tras T1.
  - [x] Cobertura `[OK]` 100 % (10/10).
  - [x] Mutación verificada de forma independiente: `harness.alcance` + `generar_mutantes` (cálculo puro) dan **35
    líneas** (2+5+2+26) y **2 mutantes**: `registro_sigrid.py:96` `is not None`→`is None` y `app.py:44` `422`→`423`,
    los mismos del informe. `routes.py` da 0 porque el cuerpo de `_entero_opcional` (l. 100-107) es el de F-050 movido,
    fuera del diff; por eso los manuales.
  - [x] Muertos comprobados: «Tiempo total» 161,3 s > 60 s ⇒ **campaña no reejecutada (2,7 min según el informe)**;
    recálculo puro + RM1-RM6 + RM4 sobre los manuales (abajo).
  - [x] Coste por mutante 161,3 × 2 ÷ 2 = 161 s ≫ 1 s.
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base medida (56,2 / 56,3 s).
  - [x] RM1: SHA medido `42ddad8…`; desde él (`42ddad8..HEAD`) solo cambian `progress/` y el test (`__enter__ -> Self`):
    ningún fichero del alcance. Vale.
  - [x] RM2: media 80,7 × W 2 = 161 s frente a base 56 s: mismo orden de magnitud; total = 2 × 80,7. Coherente.
  - N/A RM5: cero supervivientes, ningún «equivalente» declarado. RM3: ningún muerto es equivalente (los dos cambian el
    código HTTP o invierten el filtro).
  - N/A RM6: no se quitó código defensivo; la guarda se endurece (`is not None`) y se añade la validación.
  - N/A «campaña MANUAL que sustituye a una de 0»: la automática dio 2; la manual es suplementaria (ver O2).
  - [x] Ningún superviviente ⇒ ninguna sección `PENDIENTE`.
  - [ ] **«Evidencias» con el nº de workers: falta (B1).** Los cuatro números sí están: tests 50/50 (+ suites), cobertura
    100 %, 2/2 muertos y 0 vivos (+6/6 manuales), tiempos de suite.
  - [x] Ningún N/A de este bloque sin justificar.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] `tasks.md` N/A (`sdd: false`, nota de cabecera de `CHECKPOINTS.md`); commits `F-056 T1/T2/T3: …` y
  `F-056: …`; `git status` limpio, sin temporales; `features.json` en `in_progress`, que es el estado real.

## RM4 · Reproducción de los mutantes manuales (copia en el scratchpad, sin `.env`, venv de la api)

Base de la copia: `test_f056` + `test_f050` → 62 passed. Cada mutante aplicado y revertido de uno en uno:

| Mutante (texto exacto) | Informe | Reproducido |
|---|---|---|
| `if isinstance(valor, bool) or (` → `if False or (` | 7 failed | **7 failed** |
| `and not valor.is_integer()` → `and valor.is_integer()` | 9 failed | **9 failed** |
| `except (TypeError, ValueError):` → `except (TypeError,):` | 27 failed | **27 failed** |
| `if valor is None:` → `if valor is not None:` | 47 failed | **47 failed** |
| (mío) `ejecutar` con `payload.get("trabajador_ide")` crudo | — | 15 failed |
| (mío) `preflight` con el valor crudo | — | 15 failed |
| (mío) `registro_sigrid.py:96` vuelto a `if trabajador_ide` | — | 4 failed |

Cada ruta queda vigilada por separado (no basta con que una valide), y el filtro antiguo lo cazan los 4 tests del `0`.

## Cobertura de los `acceptance`

| Acceptance | Tests |
|---|---|
| a1 · entero o null; otro valor → 422 sin analizar ni escribir, en las dos rutas | `test_f056_a1_no_entero_422_sin_analizar_ni_escribir` (×2×9), `…_se_valida_antes_que_los_overrides`, `…_entero_o_null_llega_al_registro` (×2×6, valor y tipo), `…_sin_trabajador_es_el_mes_entero`, `…_obra_no_valida_sigue_siendo_de_obra`, `test_f056_trabajador_no_valido_es_error_de_dominio_propio` |
| a2 · filtro `is not None`: un 0 nunca quita el filtro | `test_f056_a2_cero_filtra_y_no_manda_nada`, `…_un_trabajador_solo_sus_lineas`, `…_sin_trabajador_el_mes_entero` (×2 fases) |
| a3 · tests de las dos rutas con 0, "", false, texto, decimal y null | todos los anteriores parametrizados por `preflight`/`ejecutar`; de punta a punta con `RegistroSigrid` real: `test_f056_a1_a2_ruta_con_registro_real_no_escribe` (×2×4: ni una línea al transfer) |
| a4 · APROBADO + init.sh verde | init.sh verde (arriba); veredicto pendiente de B1 |

`docs/INTEGRACION.md` (contrato) documenta el 422, el `"11"`/`11.0` aceptados y que `0` filtra. Límite de servicio:
solo `dedicacion-api`; el front ya manda número o `null` (`app.js:2262`, `:2473`) y no se toca.

## Cambios requeridos (pasada 1)

1. `progress/impl_F-056.md`, «Evidencias»: añadir el nº de workers de la campaña (2). Sin tocar código.

**Automejora (propuesta, no aplicada):** que el último punto de C4 bis acepte el nº de workers de `mutacion_F-XXX.md`
(la herramienta lo imprime desde la 1.7.2) o que init.sh compruebe que «Evidencias» lo lleva; portar a `arnes-base`.
