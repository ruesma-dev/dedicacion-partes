<!-- progress/review_F-076.md -->
Revisión completa (pasada 1), `dev...HEAD` (merge-base `2eac660`, HEAD `1d67473`)

# F-076 · Review (pasada principal, única: e2e N/A y mutación informativa)

**Veredicto: CHANGES_REQUESTED**

El código, los tests y la lista cerrada están bien y verificados de forma independiente (abajo). Se rechaza por el rastro: el comando exacto de la MANUAL M1 en `progress/current.md` l. 4 está roto (C4). Además, `test_f045` deja seis saltos de PEP8 (C3). Las dos cosas se arreglan en minutos y no tocan código de producción.

## Nivel de rigor

`estandar`, declarado en `harness/features.json` (no aplica el defecto). Exige: fase RED, cobertura de las líneas cambiadas ≥ 80 % y mutación **informativa** (`harness/rigor.json`: `informativas: ["mutacion", "e2e"]`). Sin `harness/rigor.local.json` en el diff.

## Lo verificado por mí (no copiado del informe)

- **`ARNES_SIN_CACHE=1 bash harness/init.sh`**: código de salida 0 y ningún `[KO]`. Resultados: raíz `2319 passed, 47 skipped` (590 s); api `1695 passed`; front `611 passed`; transfer `2011 passed`. Las tres suites de servicio se ejecutaron **sin caché**: no sale ninguna línea «(caché: …)». Puertas: `PUERTA COBERTURA` 100,0 % (4/4), `TAMAÑO` dentro de los topes, `CARRIL` y `CAPA E2E` N/A. `ruff`: 439 avisos, deuda previa.
- **Fase RED reproducida.** En un worktree desechable del scratchpad, en `5dae66f` (T1, código de `dev`): `pytest tests/test_f076_excel_sin_resto.py` → `13 failed, 2 passed`. Son los mismos 13 del informe y todos fallan en aserciones, ninguno en imports. Pasan `r1` y `r12`, como dice el informe (son guardas de regresión). Worktree retirado y `git worktree list` limpio.
- **Lista cerrada (design §6) medida de nuevo.** En la misma copia, con `contenido.py` de `bfdd7b6`, `exporter.py` de `97b94d7`, los tests de `dev` y solo los dos imports `AGREGADA_EN_*` quitados, se pasaron `test_f045`, `test_f040`, `test_f039` y `test_f024`: **`25 failed, 100 passed`**. Son exactamente las 24 de F-045 de §6.1 y `test_f040_r2`. F-039 y F-024, en verde sin tocar. Los «sin tocar» de §6.1 (`r1`, `r2`, `r12_…_suma_el_total` ×2, `r17` y `r20`) pasan.
- **Diff de `test_f045` contra §6.1, función a función.**
  - **Borradas las 12** que nombra la lista, con su criterio: el requisito de F-045 muere y su cobertura pasa a `test_f076`.
  - **Adaptadas las 8**, cada una con el cambio exacto que pide §6.1: OMEGA `["0200","0150"]`, EPSILON sin «OBRAS», `r5_d5` renombrada y sin RESTO = 60, `r3` con `A2:I8`, `r13` renombrada con `A3:A4`/`A4:A5`, `r18` ×2.
  - **Solo por los comunes:** `r12_…_en_el_libro`, `r14` y `r21`, este último solo con el comentario cambiado.
  - **Comunes:** se aplicaron todos.
  - **Detalle:** no se relaja ninguna aserción. «Sin fórmulas» sigue en `test_f040_r16_sin_formulas`, que recorre las tres hojas.
  - **`test_f040`:** solo cambian `r2` y el docstring (§6.2).
- **Cobertura «4/4» real.**
  - **Alcance:** lo recalculé con `harness.alcance.alcance_de_feature('F-076', 'dev')`. Lo cambiado de producción está en `contenido.py` (l. 2-18, 58-62, 70-89 y 105-109) y en `exporter.py` (l. 2-20, solo el docstring; el resto son borrados).
  - **Líneas ejecutables:** son 4, las l. 81-84 de `grupos_pestana`: `propias = …`, `if fila.lineas and not propias`, `continue` y `grupos.append(_grupo(…))`. Las demás líneas tocadas son docstrings, continuaciones de sentencias ya existentes (`return [` en l. 60, `def _grupo(` en l. 104) o parámetros.
  - **Contra el `coverage.json` de la api:** lo regeneró este mismo `init.sh` sin caché (17:17). Las l. 81, 82, 83 y 84 están en `executed_lines`, y ninguna línea entre la 55 y la 111 está en `missing_lines`. Las ramas de l. 82 también las ejercitan los tests: con R5, el trabajador que sale de la pestaña (GAMMA, BETA) y el que entra con una línea al 0 % (IOTA); con R7, el «SIN CARGA» (DELTA, `fila.lineas` vacía). **La puerta mide lo cambiado de verdad.**
- **Restos del código quitado:** `grep` de `agregada|AGREGADA_EN|_CURSIVA|RESTO OBRAS|RESTO POSTVENTA` en `services/`. Solo aparecen en docstrings que explican su ausencia. `Font` sigue en uso en `exporter.py` (cabecera y título). `Linea.porcentaje` es `Decimal` no opcional (`domain/models.py` l. 181), así que la `sum` de l. 87 no puede recibir `None`.

## Checkpoints

**C1**
- [x] `init.sh` sin caché: salida 0, ninguna suite aprobada por caché.
- [x] Existen los ficheros base.

**C2**
- [x] Solo hay una activa (F-076, `in_review`).
- [x] Se cogió por orden de prioridad: `todo`, prioridad 3, con F-074 cerrada.
- [x] La rama es `feature/F-076-excel-sin-resto-de`.
- [x] `current.md`: l. 4 describe la sesión activa, y el resto son pendientes del humano con el formato de siempre. El defecto que tiene está en C4.
- [x] `features.json` coherente.

**C3**
- [x] Hexagonal: solo `infrastructure/excel/`. `domain.estados` se usa sin umbral propio. No se tocan `domain/`, `application/` ni `interface_adapters/`.
- [x] La primera línea de cada fichero lleva su ruta, también en el test nuevo.
- [x] Sin `print`, sin secretos y sin dependencias nuevas.
- [ ] **Estilo (`docs/CONVENTIONS.md` l. 23: PEP8).** Al borrar funciones, `test_f045_excel_pestanas.py` se queda con huecos de 3 a 6 líneas en blanco (E303). Lo comprobé con `ruff check --select E3 --preview`: dan 6 avisos en la rama, en las l. 115, 126, 142, 191, 235 y 293, y 0 en la versión de `dev`. No lo ve el `ruff` del portero porque E3 es *preview*, pero es PEP8 y lo introduce esta feature. Es el cambio 2.
- [x] Trampas del dominio: no se convierte la escala; postventa se separa solo por `es_postventa` (`VAR-NN` cuenta como obra, test `r5_d5`); no se escribe en Sigrid.
- Avisos I001 de `ruff`: ya estaban en `exporter.py` y `test_f045` en `dev`, y `test_f076` copia el mismo bloque. Aceptado como deuda previa (desviación 4 del informe).

**C3 bis:** N/A. No se toca `docs/referencia/`.

**C3 ter:** N/A en lo nuevo. Las citas del humano de la spec («d1 b, lo demas a», 2026-11-22/24) llevan fecha y origen; el código no atribuye nada.

**C3 quater:** N/A. Design §9 dice «¿Cruza la frontera? No», y no hay commit en `azure-apps`.

**C4**
- [x] Cada requisito tiene su test (tabla abajo), y todos pasan.
- [x] Sin red ni BBDD: libro en memoria; R14 solo lee dos `.md` del repositorio.
- [ ] **MANUAL con su comando exacto en `current.md`: el comando está roto.** En l. 4, la ruta de salida de `curl.exe` lleva un **carácter de control `\f` (0x0C, salto de página)** en lugar de la barra invertida y la `f`. Lo confirmé con `od -c`: `T E M P \f 0 7 6 . x l s x`. En pantalla se lee `"$env:TEMP076.xlsx"`. Copiado a PowerShell, el nombre lleva un carácter que Windows no admite en un fichero, y `curl` no escribirá donde dicen el informe y design §7 (`"$env:TEMP\f076.xlsx"`). Viene del commit del líder `1d67473`. Es el cambio 1.
- [x] Los dobles se comparan con el original: sin dobles nuevos. El exportador falso de `test_f024` no se toca y el puerto no cambia.

**C4 bis** (contra `estandar`)
- [x] El nivel está declarado.
- [x] Fase RED: hay traza real en `impl_F-076.md`, y la reproduje (arriba).
- [x] Cobertura: `PUERTA COBERTURA` `[OK] 100.0% de 4 líneas cambiadas cubiertas (4/4, umbral 80% (global), nivel estandar; diff desde 2eac660ed0)`, verificada contra `coverage.json` (arriba).
- N/A por nivel (`estandar`, mutación informativa): totales de mutación, reejecución a menos de 60 s, coste por mutante, «⚠ CAMPAÑA NO VÁLIDA», RM1, RM2, RM5, RM6, campaña manual, supervivientes y PODADO. La campaña informativa corre después de este APPROVED (`leader.md`, «Orden de fases», paso 4). **Observación:** hoy no existe `progress/mutacion_F-076.md`, y es lo esperado en este punto.
- [x] «Evidencias»: tests, cobertura, mutación («no lanzada, pasada tras el APPROVED»), tiempos y capa e2e.
- N/A: capa e2e. `CAPA E2E: N/A`, porque ningún servicio declara e2e y la spec no marca requisitos `(capa: e2e)`.
- [x] Ningún N/A sin su motivo.

**C4 ter:** N/A. No hay `harness/rutas_sensibles.json`.

**C5**
- [x] `tasks.md`: T1-T6 y T8 en `[x]`, con un commit `F-076 Tn:` cada una. **T7 en `[ ]` es la MANUAL (humano) M1**: no la puede ejecutar ningún agente y queda pendiente del humano en `current.md` (con el comando que pide arreglar el cambio 1).
- [x] Sin temporales. `infra/imagenes.json` modificado es del despliegue del humano y no es de F-076: no lo toqué.
- [x] `features.json` dice `in_review`.

## Trazabilidad requisito → test (`tests/test_f076_excel_sin_resto.py`)

| R | Test(s) |
|---|---|
| R1 | `test_f076_r1_…` (+ `test_f045_r1`, `r3` ×2) |
| R2 | `test_f076_r2_…` (+ `test_f045_r5`, `r5_d5`) |
| R3 | `test_f076_r3_…` (+ `test_f045_r6`, `r18` ×2) |
| R4 | `test_f076_r4_…` (incluye D5: sin `agregada` ni `AGREGADA_EN_*`) |
| R5 | `test_f076_r5_…` (con una línea al 0 %) |
| R6 | `test_f076_r6_…` (muestra directa e invertida) |
| R7 | `test_f076_r7_…` (+ `test_f045_r10`) |
| R8 | `test_f076_r8_…` (tabla de §4, THETA exacto, una línea al 0 % → «FALTA 100%», E suma F) (+ `test_f045_r12` ×3) |
| R9 | `test_f076_r9_…` |
| R10 | `test_f076_r10_…` (+ `test_f045_r13`, `r14`, `r21`) |
| R11 | `test_f076_r11_…` |
| R12 | `test_f076_r12_…` (+ `test_f045_r17`, `test_f040_r16_*`) |
| R13 | `test_f076_r13_…`; `test_f024_*` en verde sin tocar |
| R14 | `test_f076_r14_docs_sin_resto` ×2 |
| M1 | MANUAL (humano), T7 |

## Cambios requeridos

1. **`progress/current.md` l. 4 (C4):** cambiar el carácter 0x0C por `\f`, para que quede `curl.exe -o "$env:TEMP\f076.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"`. Después, comprobar que l. 4 no tiene bytes de control: `grep -nP '[\x00-\x08\x0b\x0c\x0e-\x1f]' progress/current.md` no debe devolver nada. Origen probable: el texto se pasó por un `echo`/`printf` o un heredoc que interpreta `\f`.
2. **`services/dedicacion-api/tests/test_f045_excel_pestanas.py` (C3, PEP8):** dejar dos líneas en blanco entre funciones donde quedaron huecos de los borrados, en las l. 115, 126, 142, 191, 235 y 293. `ruff check --select E3 --preview tests/test_f045_excel_pestanas.py` debe dar 0 avisos. Es un cambio solo de espacios: no cambia la lista cerrada ni ninguna aserción. Va en un commit `F-076 T4: …` o en uno de corrección que lo diga.

## Observaciones (no bloquean, pero recógelas)

- **`current.md` l. 4, «Pendiente:».** Falta la pasada de campaña de mutación informativa (paso 4 del orden de fases), que el informe sí lista. Y la MANUAL M1 no está en «⚠ Lo que espera al humano», donde sí están las de F-074. Conviene añadirla allí con el mismo comando, ya corregido.
- **Para la pasada 2:** será incremental desde el SHA que se entregue. Si el delta solo toca `current.md` y espacios de `test_f045`, basta con reejecutar `init.sh` sin caché y comprobar los dos cambios.

## Automejora (propuesta, no aplicada)

Proponer a `arnes-base` una comprobación en `init.sh`: un aviso si `progress/current.md` contiene bytes de control (`[\x00-\x08\x0b\x0c\x0e-\x1f]`). Un `\f`, `\t` o `\b` comido en una ruta de Windows rompe en silencio el «comando exacto» de C4, y leyendo no se ve: en pantalla parece texto normal.
