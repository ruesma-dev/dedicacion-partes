Revisión incremental desde 7f6ddc8 (pasada 2)
<!-- progress/review_F-074.md -->
# F-074 · Review, pasada 2 (incremental): APPROVED

**Veredicto: APPROVED** sobre `526fbf9`, el SHA del que parte la pasada de evidencias.

- El delta `git diff 7f6ddc8..526fbf9` son 4 commits.
- En producción solo cambian **docstrings de módulo** (3 ficheros del transfer); en tests, **solo tres nombres**.
- Lo ya aprobado no queda invalidado: no cambia ninguna firma, ningún fichero se mueve y el alcance de la cobertura es el mismo.
- La pasada 1 (CHANGES_REQUESTED) está resumida al final. Su texto íntegro está en `git show 17514ee:progress/review_F-074.md`: con las dos pasadas enteras, el fichero supera el tope de 140 líneas de la puerta de tamaño y el portero se pondría en `[KO]`.

**Nivel `critico`:** fase RED, cobertura ≥ 90 %, mutación (uno por línea, el 60 % de los candidatos acotado a [100, 300], 0 supervivientes) y MANUAL con su comando. No hay `rigor.local.json`.

## Pasada 2

**Portero:** `bash harness/init.sh` (tal cual, sobre `526fbf9`) sale con exit 0, **0 `[KO]`** y «ENTORNO LISTO».

- Suites: raíz 2319 passed y 47 skipped.
- Puertas: `PUERTA COBERTURA` 100 % (310/310) y `PUERTA TAMAÑO` dentro de los topes (impl 203/220, review 112/140); `CAPA E2E` N/A.
- El portero dio los tres servicios por buenos **desde la caché**. Por eso he ejecutado a mano, sin caché, la suite del transfer, el único servicio que cambia en el delta: **2009 passed** (`pytest -p no:cacheprovider`). La api y el front no cambian desde `7f6ddc8`, donde los ejecuté sin caché (pasada 1).

### Los siete cambios requeridos en la pasada 1

1. [x] **`registro_pipeline.py`**, paso 1: la obra de postventa como destino, «SIN casar su partida». Paso 4: la partida **definida** (elegida, fija VAR o `propuesta_*`; en postventa, la de su obra), validada por `ide`; si no vale, omitida con `partida_no_valida`; sin ella, Regla C o la postventa omitida con su motivo; sin lecturas de presupuesto, historial ni cuentas. Es fiel al código.
2. [x] **`registro_vinculados.py`**: `proponer` dice «SOLO corre en segundo plano»; `decidir` dice «con la partida DEFINIDA (`partida_definida_del_vinculado`), sin lecturas de la regla»; las cuentas y el historial dicen «SOLO de `proponer`».
3. [x] **`lecturas_lote.py`** l. 20-21: «las cuentas del presupuesto ya no se precargan».
4. [x] **`current.md`** l. 678-683: el hecho está reescrito con los dos casados (selector y sync) y «el registro ya no casa».
5. [x] **`ARCHITECTURE.md`** l. 108, 769 y 1220 dicen «sin elegida». Solo queda «automática» en l. 753, en la frase «Nunca «automática»», que es la correcta.
6. [x] **Tests renombrados** sin tocar ninguna aserción: en el diff solo cambian las líneas `def` (`test_f055_pipeline_partidas.py:121`, `test_f068_pipeline.py:315` y `:348`). Están anotados con su criterio en `impl_F-074.md` l. 92-104, y ningún otro fichero cita los nombres viejos (grep).
7. [x] **Rastro de la vuelta:** `current.md` l. 4 está en pasada 2; `impl_F-074.md` trae la sección «Vuelta de la review, pasada 1» con `7b2df8b`; H6 está corregido (las cuatro secciones de `azure-apps`, l. 189-193). `features.json` y `BACKLOG.md` dicen `in_review`.

### Rastro: `progress/current.md` releído entero (lista completa, no bloquea)

El rastro no rompe ningún checkpoint (C2 y C5 [x]). Estas tres incoherencias hay que corregirlas **antes de la pasada de evidencias**, que lo comprobará:

- **R1 · l. 4, «H1 cabeceras, H3, H4 y H6 en `7b2df8b`»:** H6 no está en `7b2df8b` (código, docs y tests) sino en `c241cba`, el informe. Debe decir «H1, H3 y H4 en `7b2df8b`; H6 e informe en `c241cba`».
- **R2 · l. 4, «tamaño impl 180/220»:** es un dato viejo. Hoy el informe mide 203/220 (`impl_F-074.md` l. 106 y la puerta).
- **R3 · Las automejoras de la pasada 1 no constan.** Son estas dos, y van con las demás, como la l. 77 de F-069, «para `arnes-base`»:
  - C3: la cabecera de módulo y los nombres de test dicen el comportamiento nuevo.
  - C4 promete una puerta automática de dobles que el `init.sh` 1.10.1 de aquí no imprime.

  Si no se apuntan, se pierden al cerrar.

Nota para el cierre, que hoy no es una incoherencia: l. 659-661, «escribir sin partida casada (F-013)», describe la producción de hoy. Al desplegar F-074 pasa a ser «sin partida definida».

### Checkpoints (pasada 2, sobre el delta)

- **C1 [x]**: el portero, arriba.
- **C2 [x]**: una sola activa (F-074, `in_review`), en su rama; R1-R3 no rompen nada.
- **C3 [x]**: el delta son docstrings en español con ruta en la primera línea, sin `print`, TODO ni secretos; la hexagonal no cambia.
- **C3 bis, C3 ter y C4 ter:** como en la pasada 1 (N/A, [x] y N/A).
- **C3 quater:** sigue pendiente del líder (`current.md` l. 486, las cuatro secciones).
- **C4 [x]**: la trazabilidad no cambia (los renombrados conservan el prefijo `test_fXXX_rN_`); sin red ni BBDD; las MANUAL constan con su comando (l. 481-485).
- **C4 bis**: [x] RED y Evidencias como en la pasada 1; [x] cobertura en el portero; mutación, RM1-RM7 y supervivientes: **pendiente, pasada de evidencias**.
- **C5 [x]**: commit del arreglo `7b2df8b`; `tasks.md` igual (T15-T18 MANUAL); `git status` limpio salvo este informe.

### Lo que necesita la pasada de evidencias (mutación `critico`)

1. **Antes de lanzarla:** R1-R3 corregidos. Después, nadie toca código: por RM1, cualquier cambio en un fichero del alcance obliga a repetir la campaña.
2. **Comando**, desde la raíz y sobre el HEAD que se vaya a revisar: `python -m harness.mutacion --feature F-074`. Escribe `progress/mutacion_F-074.md` con muestra de `critico`, semilla 20261030, uno por línea y el 60 % acotado a [100, 300].
   - El informe trae la fila «SHA de HEAD medido» con el SHA completo, «Línea base», «Media por mutante» y «Tiempo total».
   - **0 supervivientes.** Cada uno se mata con un test nuevo o se justifica por escrito con la aceptación del humano. Los supervivientes se reproducen **en serie** (aviso de F-057 y F-062 sobre `mutacion_paralela`).
   - Ni «⚠ CAMPAÑA NO VÁLIDA» ni «Sin veredicto (base rota)» ≠ 0.
3. **Fuera de la mutación por lenguaje:** `app.js` y `styles.css` (N/A justificado; la regla del front la fijan `test_f074_celda` y `test_f074_selector_modal`).
4. **Para el reviewer de evidencias:**
   - RM1: SHA = HEAD.
   - RM2: la media contra la línea base.
   - RM5: reproducir uno de los equivalentes.
   - RM6: la guarda «si sigue sin elegida» de `_borrar_no_validas` no se quita para matar un mutante.
   - RM7: el orden de R15, `olvidar_subfilas` **antes** de `encolar` (`routes.py` l. ~458-470). En una copia del scratchpad, bajar el olvido por debajo del encolado tiene que poner en rojo `test_f074_r15_la_ruta_lo_cablea_antes_de_encolar`.
   - Además, recalcular el alcance y el número de mutantes con `harness.alcance` y `generar_mutantes`.

## Pasada 1 (CHANGES_REQUESTED sobre `7f6ddc8`), resumida

Texto íntegro: `git show 17514ee:progress/review_F-074.md`.

**Portero:** `ARNES_SIN_CACHE=1 bash harness/init.sh` salió con exit 0 y 0 `[KO]`: raíz 2319 passed y 47 skipped; api 1690, front 611 y transfer 2009; cobertura 100 % (310/310); `CAPA E2E` N/A.

**Lo que pidió el líder (1-7), todo [x]:**

1. El preflight no corre `proponer_partida`, `casar_postventa` ni `PasoVinculados.proponer`. La partida definida se valida por `ide`; la que no vale se omite con `partida_no_valida`; sin ella, Regla C o la postventa omitida. Las lecturas se cuentan en los dobles (`c1`, `c2`, `r6`).
2. Lista cerrada: los 39 ficheros de test cambiados están en los candidatos, cada uno con su criterio. Los que prueban otra cosa reciben la definida y conservan sus aserciones. Solo se retiran los del casado en el preflight, y la regla sigue cubierta en el selector.
3. Los ficheros prohibidos están intactos.
4. `app.js` no tiene lógica de negocio. Se acepta la desviación de tener el texto en dos sitios (lo ata `r20_el_filtro_y_la_celda_dicen_lo_mismo`).
5. Se aceptan los `getattr` de `routes.py` y `repositories.py`: en producción `deps.py` cablea siempre `PropuestasDelMes`, y el camino real está probado.
6. Compatibilidad y orden api → sync → transfer → front: [x].
7. Rastro: [x], salvo H2.

**Checkpoints:** C1-C5 [x]. C3 bis y C4 ter N/A; C3 ter [x]; C3 quater pendiente del líder. C4 bis: RED [x] (transfer 41/19, api 41/10, front 30/8); cobertura [x]; Evidencias [x]; e2e N/A; mutación pendiente. Dobles cruzados a mano, porque no hay puerta automática.

**Cobertura requisito → test:**

| R | Tests |
|---|---|
| R1-R7 | `test_f074_r1_*` a `r7_*`, `c1_*`, `c2_*` (`test_f074_preflight_definida.py`; R4 también `test_f074_no_valida_api.py`) |
| R8 | `c1_*` y las mitades del selector de `test_f050_r9_*`, `test_f055_r38_*` y `test_f068_r15_selector_*` |
| R9-R10 | `r9_*` (10) y `r10_*` (4) (`test_f074_motivos.py`) |
| R11-R16 | `r11_*`, `r12_*`, `r13_*` (15), `r14_*`, `r15_*`, `r16_*` (api) |
| R17-R22 | `r17_*` a `r22_*` (front) |
| R23 | `c1_*`, `c2_*` y `r6_*` (design §8) |
| R24 | Documental (revisado; H3) |

**Hallazgos:**

- **H1 (bloqueante):** las cabeceras de módulo decían que el preflight propone. Corregido en `7b2df8b`.
- **H2:** el hecho de `current.md`. Corregido en `17514ee`.
- **H3:** «automática» en `ARCHITECTURE.md`. Corregido.
- **H4:** tres nombres de test. Corregido.
- **H5 (observación, se mantiene):** una subfila con la guardada de método `titular` puede enseñarse y, al registrar, ir a «sin partida». Es seguro: no escribe en otra.
- **H6:** `azure-apps` tenía cuatro secciones y no tres. Corregido en `c241cba`.
- **H7:** pasa a «Lo que necesita la pasada de evidencias».

**Automejora (propuesta, sin aplicar):**

- C3: «si la feature cambia el comportamiento de un módulo, su docstring de cabecera y los nombres de los tests que lo describen dicen el comportamiento nuevo».
- Revisar en `arnes-base` por qué C4 promete una puerta automática de dobles que el `init.sh` 1.10.1 no tiene.
