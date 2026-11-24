Revisión completa (pasada 1)
<!-- progress/review_F-074.md -->
# F-074 · Review, pasada principal: CHANGES_REQUESTED

**Veredicto: CHANGES_REQUESTED** sobre `7f6ddc8`. El código cumple R1-R24 y las puertas salen en verde. Se rechaza por **un hallazgo bloqueante**, documental y barato (H1): las cabeceras de módulo del transfer siguen diciendo que el preflight propone y lee el historial. Hay que corregirlo **antes** de la campaña de mutación, porque por RM1 cambiar después ficheros del alcance obliga a repetirla. H2-H4 no bloquean por sí solos, pero se recogen en la misma vuelta (la lista completa está al final).

**Nivel `critico`** (declarado en `features.json`). Exige fase RED, cobertura ≥ 90 % de lo cambiado, mutación (uno por línea, el 60 % de los candidatos acotado a [100, 300], 0 supervivientes) y las MANUAL listadas con su comando. La capa e2e es informativa. `harness/rigor.local.json` no existe y no se toca.

**Portero:** `ARNES_SIN_CACHE=1 bash harness/init.sh` sale con exit 0 y **ningún `[KO]`**. Suites en verde: raíz 2319 passed y 47 skipped; api 1690, front 611 y transfer 2009. `PUERTA COBERTURA` 100 % (310/310), `PUERTA TAMAÑO` dentro de los topes (impl 183/220) y `CAPA E2E` N/A.
Solo hay dos `[AVISO]`: la deuda previa de ruff y el aviso propio de `ARNES_SIN_CACHE`.

## Lo que pidió el líder (1-7)

1. **El preflight no casa: [x].**
   - `_preflight` (`registro_pipeline.py` l. ~615-775) usa la definida: `_definida_pv` para la postventa; para las demás, `vale` / `vale_pv` sobre la elegida o la `propuesta_*`.
   - Ninguna ruta del preflight (normal, lote, vinculados, postventa) llama a `proponer_partida`, `casar_postventa` ni `PasoVinculados.proponer`. `decidir` resuelve con `partida_definida_del_vinculado`, sin lecturas.
   - `lecturas_lote.precargar` no lee presupuestos de origen ni de postventa, historial ni cuentas.
   - Las lecturas se cuentan en los dobles: `test_f074_c1_*`, `c2_*`, `r6_*` y `r1_sin_definida_*` (`sin_lecturas_de_la_regla`).
   - La partida que no vale sale como `omitir` con `partida_no_valida` (`r4_*`). Sin definida, la normal y la subfila van a `paride 0` con el aviso de Regla C, que hay que confirmar; la postventa se omite con su motivo (`r5_*`).
   - Lo que se escribe es lo que publica la api como `propuesta_*`, también en postventa (`test_f074_r12_postventa_publica_la_de_su_obra`).
2. **Lista cerrada: [x].**
   - Los 39 ficheros de test anteriores que cambian están todos en los candidatos de `tasks.md`, contando la enmienda del 2026-11-24. Cada uno está anotado con su criterio en `impl_F-074.md` (§«Tests anteriores cambiados»).
   - Los tests que prueban otra cosa reciben la definida de `conftest.py` (`linea_definida` / `DEFINIDA_*`) y conservan sus aserciones.
   - Solo se retiran tests que probaban el casado o los catálogos en el preflight: f050 r7 (×2), f068 r7, r18, r2-D3, r11 y r12, f002 r17 «desplegable», f050 r10 postventa y f055 r14 «solo si sigue sin elegida». La regla sigue cubierta en el selector (`test_f068_r15_selector_*`, `r18_selector_*`, `test_f068_reglas.py` r2 y r7), y la guarda de la elegida en `test_f074_no_valida_api.py`.
   - Las mitades del selector de `test_f050_r9_misma_propuesta…` y `test_f055_r38_…` conservan el `esperado` de antes. No he encontrado ningún test debilitado.
3. **Ficheros prohibidos intactos: [x].** `git diff --stat dev...` sale vacío para `propuesta_partida.py`, `reglas_porcentajes.py`, `reglas_vinculados.py`, `partida_matcher.py`, `partida_catalog.py` y `text_match.py`, y también para `cuenta_analitica.py` y `estado_parte.py`.
4. **`app.js` sin lógica de negocio: [x].**
   - El front solo pinta las marcas de la api (`propuesta_pendiente`, `propuesta_no_encontrada`, `propuesta_motivo`); el orden de los estados es presentación.
   - La desviación de tener el texto en dos sitios se acepta. design §5 ya preveía una `textoCeldaPartida` para el filtro, y las dos quedan atadas por `test_f074_r20_el_filtro_y_la_celda_dicen_lo_mismo`, que comparte la fixture `ESTADOS` con `r17`.
5. **Los `getattr`: aceptados, no ocultan un fallo.**
   - Están en `routes.py` l. 119 y l. 462, `repositories.py` l. 1163-1167 (y `_a_linea`) y `registro_sigrid.py` l. 300.
   - En producción, `deps.py` cablea siempre `PropuestasDelMes`, que tiene `encolar_marcas` y `olvidar_subfilas`. El `getattr` solo cubre dobles anteriores, como el precedente de F-069 (`registro_sigrid.py` l. 315-322).
   - El camino real está probado: `test_f074_memoria_subfilas` usa la `PropuestasDelMes` real, `r15_la_ruta_lo_cablea_antes_de_encolar` comprueba el cableado por identidad, y `r11_el_repositorio_*` va contra el ORM.
6. **Compatibilidad y orden: [x].**
   - api nueva con transfer viejo: el transfer viejo ignora la `propuesta_*` de la postventa y sigue casando, y la api no borra nada sin `partida_no_valida`.
   - transfer nuevo sin sync: la postventa se omite con su motivo y nunca se escribe en otro sitio.
   - Las columnas son nulables y sin default (`r11_columnas_nulables_sin_default`) y el `ALTER` se deriva solo (`r11_el_alter_lo_deriva_esquema`).
   - El orden api → sync → transfer → front consta en `INTEGRACION.md` §5, en `#regla-p5`, en T18 y en `current.md` l. 485.
7. **Rastro: [x], salvo H2.**
   - `current.md` l. 4 dice `in_review`; las MANUAL T15-T18 tienen su comando (l. 481-485) y `azure-apps` consta como pendiente con §2, §4, §5 y §7 (l. 486).
   - `features.json` dice `in_review`; `tasks.md` tiene T1-T14 y T19 `[x]` y T15-T18 MANUAL `[ ]`; `BACKLOG.md` está al día.

## Checkpoints

- **C1 [x]** El portero va entero y sin caché (arriba). Existen todos los ficheros del arnés.
- **C2 [x]** Hay una sola activa, F-074, que es la prioridad 1 de `todo`, y estamos en su rama. `current.md` describe la sesión (H2 está en la sección permanente de «Hechos»). No hay ninguna `done` nueva.
- **C3 [x]**
  - Hexagonal: `estado_partida.py` (api, application) y `partida_definida.py` (transfer, servicio puro) no importan infraestructura; `domain/models` gana solo campos.
  - Los 10 ficheros nuevos llevan la ruta en la primera línea.
  - El diff no trae `print`, TODO ni secretos (grep). `ruff --select F` está limpio en el transfer; en la api, el único F841 (`use_cases.py:173`) es anterior a la rama.
  - Las tres trampas: la escala no se toca. La postventa va a la obra de postventa con la partida de la obra original, casada en el sync por el código de la obra y validada contra la obra de postventa (`r3_la_de_postventa_se_valida_contra_…`); `es_postventa` está en todas las claves de `Marcas`. Solo escribe el transfer: escritura, `synckey` y modo pruebas siguen igual.
- **C3 bis N/A:** el diff no trae nada en `docs/referencia/`.
- **C3 ter [x]:** lo atribuido al humano lleva fecha y origen («si», 2026-11-24, en `current.md` l. 4 y en la spec).
- **C3 quater, pendiente del líder:** la frontera es «Sí» (design §11) y `azure-apps/dedicacion.md` lo actualiza el líder en un commit aparte (R24). Está listado en `current.md` l. 486 con las cuatro secciones. Todavía no hay commit que revisar, como en F-069.
- **C4 [x]**
  - Trazabilidad: tabla de abajo.
  - Los tests nuevos usan dobles, sin red ni BBDD.
  - Las MANUAL constan con su comando.
  - Dobles, cruzados a mano porque este `init.sh` no tiene puerta de dobles: los métodos de los dobles de `PropuestasDelMes` (l. 140, 172, 183), de `transfer_client.py` (l. 93, 136, 159) y los espías del cliente de Sigrid existen en su original y tienen la misma aridad.
- **C4 bis**
  - [x] El rigor está declarado.
  - [x] RED: `impl_F-074.md` §«Fase RED» trae la salida real contra `9fb1092`: transfer 41 failed / 19 passed, api 41/10, front 30/8.
  - [x] Cobertura: `PUERTA COBERTURA` da [OK], 100 % (310/310, umbral 90 %).
  - [x] La sección «Evidencias» tiene los cuatro números y la fila «Capa e2e».
  - Capa e2e N/A: `CAPA E2E: N/A` en el portero y ningún requisito `(capa: e2e)`.
  - Mutación, RM1-RM7 y supervivientes: **pendiente: pasada de evidencias** (ver H7).
- **C4 ter N/A:** no existe `harness/rutas_sensibles.json`.
- **C5 [x]**
  - `tasks.md` está al día.
  - Los commits van agrupados por servicio con el rango de tareas en el mensaje (`F-074 T1-T4`, `T5-T9`, `T10-T12`, `T13`, `T14, T19`); el motivo está en `impl` l. 27 y hay precedente en `dev` (`F-054 T24-T26`).
  - `git status` está limpio y `features.json` coincide con el estado.

## Cobertura requisito → test

| R | Tests (`services/*/tests/test_f074_*.py`) |
|---|---|
| R1-R5 | `r1_*` (6), `r2_*` (7), `r3_*` (2), `r4_*` (9), `r5_*` (4): `test_f074_preflight_definida.py`, y R4 también `test_f074_no_valida_api.py` |
| R6, R7, R23 | `r6_sin_catalogos_en_la_respuesta`, `r7_lote_igual_que_suelta_con_todos_los_casos`, `c1_diez_obras_sin_definida_no_leen_la_regla`, `c2_postventa_lee_su_obra_y_no_su_presupuesto` (R23 = C1 y C2 de design §8) |
| R8 | `c1_*` (el preflight no la corre) y las mitades del selector, que no cambian: `test_f050_r9_misma_propuesta…`, `test_f055_r38_…` y `test_f068_r15_selector_*` (T1, por diseño) |
| R9, R10 | `r9_*` (10), `r10_*` (4), con HTTP y lote incluidos: `test_f074_motivos.py` |
| R11-R16 | `r11_*`, `r12_*` (`postventa`), `r13_*` (15), `r14_*` (`estados`), `r15_*` (`memoria_subfilas`), `r16_*` (`no_valida_api`) |
| R17-R22 | `r17_*`, `r18_*`, `r19_*`, `r20_*` (`celda`), `r21_*`, `r22_*` (`selector_modal`) |
| R24 | Documental: diff de `ARCHITECTURE.md` (las cuatro anclas) e `INTEGRACION.md` §5 revisado; H3 |

## Hallazgos

- **H1 · BLOQUEANTE · las cabeceras de módulo contradicen R1, R6 y R23.** Los comentarios dentro de las funciones ya están al día; las cabeceras de tres módulos, no:
  - `services/dedicacion-transfer/application/pipelines/registro_pipeline.py`, l. 12-14: el paso 1 dice «la obra de postventa con su PARTIDA».
  - Ese mismo fichero, l. 22-25: el paso 4 dice «la que no trae partida lleva la PROPUESTA, con una sola lectura del historial por petición».
  - `registro_vinculados.py`, l. 7-12: «con la misma regla que el preflight».
  - `registro_vinculados.py`, l. 20-25: lecturas de cuentas e historial «por petición» como si las hiciera el preflight; hoy solo las hace `proponer`.
  - `application/services/lecturas_lote.py`, l. 19-21: «las cuentas del presupuesto, una vez por obra» en la viñeta de `precargar`, que ya no las lee.

  Es la descripción del módulo central del cambio en una feature `critico`. Quien la lea en un incidente entenderá que el registro propone.
- **H2 · no bloqueante (rastro) · `progress/current.md` l. 678-681** («Hechos que no conviene volver a descubrir», F-050 postventa). Sigue diciendo que el preflight casa con `obra.codigo` y habla de «la automática del registro», y eso ya es falso.
- **H3 · no bloqueante (R24) · `docs/ARCHITECTURE.md`** usa todavía «automática» como sinónimo de «sin elegida»:
  - l. 108: «nulas = automática».
  - l. 769, dentro de `#regla-partida`, que ahora dice «Nunca «automática»»: «la nueva entra automática».
  - l. 1220: «postventa, automática».
- **H4 · no bloqueante · nombres de test que dicen lo contrario de lo que ahora comprueban.** El implementer ya renombró `f002_r17`, `f050_r9` y `f050_r10`, pero no estos tres:
  - `test_f055_r6_propuesta_que_no_vale_se_recalcula` (`test_f055_pipeline_partidas.py:121`)
  - `test_f068_r13_si_el_historial_falla_el_preflight_falla` (`test_f068_pipeline.py:315`)
  - `test_f068_r16_la_que_no_vale_o_de_titular_se_recalcula` (`test_f068_pipeline.py:348`)

  Su docstring F-074 lo aclara. Renombrarlos no cambia ninguna aserción y queda dentro de su criterio (i).
- **H5 · observación.** Una subfila con la propuesta guardada de método `titular` (cuando la partida del titular cambió sin pasar por `CambiarPartida`, por ejemplo tras un borrado por R16) puede enseñarse y, al registrar, ir a «sin partida». Es seguro: se confirma y nunca escribe en otra partida. No pido cambio.
- **H6 · observación.** `impl_F-074.md` l. 173 habla de «tres puntos» de contrato para `azure-apps`, pero design §11 nombra cuatro secciones. La lista completa es la de `current.md` l. 486.
- **H7 · para la pasada de evidencias.**
  - `app.js` y `styles.css` quedan fuera de la mutación por lenguaje.
  - RM7: el único orden entre colaboradores es R15 (olvidar antes de encolar) y ya lo prueba un espía que anota los dos (`r15_la_ruta_lo_cablea_antes_de_encolar`). Basta una mutación que baje `olvidar` por debajo de `encolar`.
  - RM6: vigilar la guarda «si sigue sin elegida» de `_borrar_no_validas`.

## Cambios requeridos (lista completa, de una vez)

1. **(H1) `registro_pipeline.py`, l. 12-14 y 22-25.**
   - Paso 1: la obra de postventa como destino, sin casar.
   - Paso 4: la partida **definida** (elegida, fija VAR o `propuesta_*`; en postventa, la de su obra), validada por `ide`. Si no vale, se omite con `partida_no_valida`. Sin definida, Regla C para la normal; la postventa se omite con su motivo. Sin lecturas de presupuesto, historial ni cuentas.
2. **(H1) `registro_vinculados.py`, l. 7-25.**
   - `proponer` lleva la regla de `reglas_vinculados` y solo corre en segundo plano.
   - `decidir` usa `partida_definida_del_vinculado`, sin lecturas.
   - Las lecturas de cuentas e historial son solo de `proponer`.
3. **(H1) `lecturas_lote.py`, l. 19-21:** las cuentas del presupuesto ya no se precargan en el preflight.
4. **(H2) `current.md`, l. 678-681:** reescribir el hecho. El selector (`proponer`) casa con `origen.codigo` y el universo del sync con `obra.codigo` (el que manda la api). Si alguna vez divergen, la propuesta del selector y la partida de su obra que enseña la celda (y que se registra) serían distintas.
5. **(H3) `ARCHITECTURE.md`, l. 108, 769 y 1220:** cambiar «automática» por «sin elegida».
6. **(H4)** Renombrar los tres tests sin tocar sus aserciones, y anotarlo en `impl_F-074.md` junto a su criterio.
7. **Rastro de la vuelta:**
   - `current.md` l. 4 con el estado tras este rechazo.
   - `impl_F-074.md` con el commit de la corrección.
   - La pasada 2 será incremental desde `7f6ddc8`.

## Automejora (propuesta, no aplicada)

Propongo añadir a C3 de `CHECKPOINTS.md` (vale para `arnes-base`): «Si la feature cambia el comportamiento de un módulo, su docstring de cabecera y los nombres de los tests que lo describen dicen el comportamiento nuevo». H1 y H4 se escaparon porque nada lo pide: el implementer actualizó los comentarios que tocaba y no las cabeceras.

Además, C4 dice que la comparación de dobles es una comprobación automática, pero el `init.sh` de este repositorio (arnés v1.10.1) no imprime ninguna puerta de dobles. Hay que mirar en `arnes-base` si falta instalarla o si el checkpoint describe algo que no existe.
