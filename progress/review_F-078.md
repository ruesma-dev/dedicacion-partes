<!-- progress/review_F-078.md -->
Revisión completa (pasada 1)

# F-078 · Review principal (`critico`; habrá pasada de evidencias por la mutación exigida)

**Veredicto: APPROVED** sobre HEAD `8ca80b57a7a0296361c3875fd56bb111a6ac40c9` (diff `dev...HEAD`; merge-base `b383f3c`
= `dev`). Mutación: «pendiente: pasada de evidencias». Recoge O1-O3 antes de esa pasada; si no, vuelven como bloqueo.

## Nivel de rigor

`critico`, declarado en `features.json`, por el disparador 2 (design, cabecera): `registro/ejecutar` decide qué
trabajadores y líneas escribe el transfer en `hmores` de `ruesma` y cuáles pone a 0. Exige fase RED, cobertura ≥ 90 %,
mutación exigida (uno por línea, el 60 % acotado a [100, 300], 0 supervivientes sin aceptación escrita del humano) y
MANUAL con comando exacto; la e2e es informativa. `harness/rigor.local.json` no existe y el diff no lo toca.

## Lo verificado por mí (no copiado del informe)

- **`ARNES_SIN_CACHE=1 bash harness/init.sh`**, sin pipes: código 0, `ENTORNO LISTO`, ningún `[KO]` ni suite de caché.
  Raíz `2319 passed, 47 skipped` (21:27), api `1848` (1:55), front `771` (2:28), transfer `2021` (31 s).
  `COBERTURA [OK] 100.0% (29/29)`, contrastada con `services/dedicacion-api/coverage.json` de esta ejecución: las 29
  ejecutables del alcance (8 de `registro_sigrid.py`, 21 de `routes.py`) están en `executed_lines`, ninguna en
  `missing_lines`. `TAMAÑO` OK; `CARRIL` y `CAPA E2E` N/A.
- **Copia `git archive` de HEAD (scratchpad):** api `185 passed` (con F-056); front `63 passed`, node v24, sin skip.
- **RED reproducida** con `routes.py`, `registro_sigrid.py`, `app.js` e `index.html` de `dev` en la copia. api:
  `121 failed, 14 passed`; 46 son `{"ok":true,"obras":[]}` (hoy `trabajador_ides: []` se ignora y la ruta pide **el
  mes entero**, la avería de design §7), 59 `TypeError` de firma, 14 `KeyError` y 2 `ValueError` (overrides rotos sin
  puerta). Front: `63 failed` por `no existe la función alcanceRegistro`, rojo de existencia. Lo completé con rupturas
  de **comportamiento** sobre HEAD, una a una, en la copia (el árbol, sin tocar):

| Ruptura (api) | Caen | Ruptura (front, `app.js`) | Caen |
|---|---|---|---|
| A1 `[]` ⇒ `None` (el mes) en la ruta | 4 | F1 `ides` = la selección entera (con ocultos) | 8 |
| A2 sin la guarda de `null` dentro | 4 | F2 `ejecutar` sin `trabajador_ides` | 2 |
| A3 sin R4 (lista + `trabajador_ide`) | 6 | F3 `registrarPaquete` sin la guarda de vacío | 2 |
| A4 sin quitar repetidos | 6 | F4 `registroPreflight` no guarda el paquete (pide el mes) | 4 |
| A5 la ruta de `ejecutar` no pasa el paquete | 7 | F5 `guardarAhora` después del preflight (R17) | 1 |
| A6 `if trabajador_ides:` (vacía ⇒ el mes) | 2 | F6 `ejecutar` recalcula el alcance (no congelado) | 1 |
| A7 incidencias sin el paquete | 44 | F7 `disabled` sin `a.bloqueado` | **0** |
| A8 `ejecutar` del registro sin el paquete | 22 | F8 sin repintar el botón tras el corte | 1 |
| A9 paquete sin `completo` | 3 | F9 el clic vuelve a `registroPreflight(null)` | 9 |
| A10 `ejecutar` sin redesignar cierres | 6 | F10 umbral de seleccionados a 1 | 9 |
| A11 asignaciones sin el paquete | 44 | A12 `poner_a_cero` después de las obras (R8) | 1 |

  F7 es **equivalente** (`bloqueado` implica `ides = []` en `alcanceRegistro`, l. 3956). T3 y T6 no tenían RED (fijan
  código de T2 y de F-054): A8-A10 y A12 demuestran que sus tests vigilan el comportamiento, no solo la firma.
- **Riesgo principal (design §7), buscado: sin hallazgos.** api: lista vacía, mal formada, con `null` dentro o junto
  a un `trabajador_ide` ⇒ 422 antes del registro (`routes.py` l. 158-185); `_filtro_trabajadores` (l. 222) usa
  `is not None` e `in_`, y `[]` por código da `IN ()` (A6). Solo pide el mes `trabajador_ides` ausente o `null` (R5).
  Front: `registro.paquete.ides` sale siempre de `alcanceRegistro` (un array); vacío no se manda (l. 4660, F3), el clic
  ya no llega a `registroPreflight(null)` (F9) y, antes de cargar el cuadrante, no pide nada.
- **Nada cambia donde no debe.** Ni `services/dedicacion-transfer/`, ni `transfer_client.py`, ni ORM ni esquema; en
  `tests/`, solo los dos nuevos. «⇪ Sigrid» de fila y editor (`app.js` l. 1727 y 2080) sigue con
  `registroPreflight(ide)` y el cuerpo de hoy (`r18_el_de_un_trabajador`). Sin paquete, la ruta pasa las claves de
  hoy (`r5_*`) y la sentencia es la `==` de F-056.
- **`azure-apps` `ce8437c`:** solo `dedicacion.md` (+14), sin secretos ni IPs, igual que `INTEGRACION.md`; sin push.

## Desviaciones declaradas (impl, «Decisiones»): las cuatro, correctas

1. **`esperarRegistroCortado` tocada:** la pide R19 y el líder corrigió design §4; solo cambia la restauración (F8).
2. **`trabajador_ides` solo si viene (`_paquete`, l. 690):** sin ella, R5 fallaría (`set(kw) == CLAVES_HOY`).
3. **`registro.enVuelo`:** la pide design §6 y la fija `r15_con_un_preflight_en_vuelo`; con «⇪ Sigrid», inocua.
4. **Orden de obras del modo trabajador:** con todos, idénticas al mes (`r6_r11_con_todos`); con uno, a
   `trabajador_ide` (`r6_paquete_de_uno…`). Las demás (pintado, `JSON.stringify`, singular, «(0)»), sin objeción.

## Checkpoints

**C1** [x] `init.sh` sin caché, código 0. [x] Existen los siete ficheros base.
**C2** [x] Una sola activa: F-078 `in_review` (F-071 está `blocked` por decisión del humano). [x] Orden: F-046 y F-077
van antes por prioridad, pero el humano comprometió este («vamos con f78 y luego 46 y 79», `c45c4b9`). [x] Rama
`feature/F-078-registrar-por-paquetes`. [x] `current.md` l. 4 describe la sesión activa y sus siguientes pasos.

**C3** [x] Hexagonal: validación en `interface_adapters`, filtro en `application` (que ya usaba el ORM). [x] Primera
línea con la ruta en los tests nuevos. [x] Sin `print`, `console.log`, TODO, secretos ni dependencias. [x] Trampas:
**escala**, sin conversión nueva; **postventa**, la `Postv-` va con su trabajador (asig. 8 de
`r1_cada_trabajador_entero`); **escritura**, ninguna nueva, el transfer no se toca y sigue en serie.

**C3 bis** N/A: no se toca `docs/referencia/`. **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C3 ter** [x] Citas con fecha y origen (D3 y D4 con su frase; «ok a todo», 2026-11-27); la lectura del agente va
en las opciones, aparte. Matiz en O1.

**C3 quater** (design §9: «Sí») [x] Solo `dedicacion.md`. [x] Commit aparte `ce8437c`, con SHA y ruta en el impl.
[x] Sin push. [x] Coincide con la Frontera: el cuerpo de las dos rutas gana `trabajador_ides`.

**C4** [x] Cada requisito tiene su test, en verde (tabla). [x] Sin red ni BBDD (sesión, transfer y DOM falsos). [x]
M1 (T9) en «⚠» de `current.md` con su comando exacto; el script y sus fases `estado` y `limpiar --confirmar`
existen. [x] Dobles, cruzados a mano (el repositorio no tiene comprobación automática): `_SesionPaquete` imita
`Session` (`execute`, `commit`, contexto); `_Registro` y `_TransferCero` son previos; las llamadas de las dos rutas
casan con las firmas reales (`inspect.signature(...).bind`, con `trabajador_ides`).

**C4 bis**
- [x] Nivel declarado. [x] Fase RED: trazas de T1, T2, T4 y T5 del impl, reproducidas, y las rupturas de arriba.
  [x] Cobertura `[OK]` 100 % (29/29), contrastada con `coverage.json`.
- **Pendiente: pasada de evidencias:** totales de `mutacion_F-078.md` (recálculo con `harness.alcance` y
  `generar_mutantes`; reejecución si < 60 s), coste por mutante, «⚠ CAMPAÑA NO VÁLIDA», RM1, RM2, RM5, RM6, campaña
  manual, supervivientes y su análisis, PODADO y las filas de mutación y workers de «Evidencias».
- **RM7, adelantado:** R8 (`poner_a_cero` antes de las obras) cae con A12 y R17 (`guardarAhora` antes del `fetch`)
  con F5. La puerta de R3 no se puede bajar por debajo del registro: su resultado es argumento de esa llamada. Si el
  delta no toca esas líneas, la pasada de evidencias puede darlo por hecho.
- [x] «Evidencias» completa salvo la mutación, que toca ahora. Capa e2e N/A: `CAPA E2E: N/A` y ningún requisito
  `(capa: e2e)`. [x] Ningún N/A sin motivo.

**C5** [x] T1-T8, T10 y T11 en `[x]`, cada una con su commit `F-078 Tn:` (T8 y T10 comparten `d316311`; T8 vive en
`azure-apps`). T9 es la MANUAL M1 del humano y consta en `current.md`. [x] `git status` limpio. [x]
`features.json` dice `in_review` y `spec_aprobada`; su descripción, en O1.

## Trazabilidad requisito → test (prefijo `test_f078_`)

| R | Test(s) |
|---|---|
| R1, R2 | api `r1_filtra_por_in_…`, `r1_cada_trabajador_entero`, `r1_r5_…`; `r2_enteros_sin_repetidos…` (×10) |
| R3, R4 | api `r3_mal_formado_422_…` (20 × 2 rutas), `r3_se_valida_antes…`; `r4_*` (×10) |
| R5, R6 | api `r5_sin_paquete…` (×8), `test_f056_*` intacto; `r6_las_del_mes…` (×10), `r6_paquete_de_uno…`, `r6_detalle…` |
| R7-R11 | api `r7_*` (×6), `r8_*` (×3), `r9_*`, `r10_*` (con `IN ()` por código), `r2_r11_sin_tope`, `r6_r11_con_todos…` |
| R12-R14 | front `r13_alcance`, `r13_nunca_un_oculto`, `r14_*`, `r12_rotulo`, `r12_title…`, `r12_r14_r15_pintar…` |
| R15-R22 | front `r15_*` (×7), `r16_r22_cuerpos…`, `r17_*`, `r18_*`, `r19_*`, `r20_*` (puras y modal real), `r21_*` |
| R23-R25 | api `r23_sin_bloqueo…`, `r24_obra_compartida…`, `r25_*` (×2) |
| R26 | MANUAL M1 (T9), del humano |

## Cambios requeridos: ninguno

## Observaciones (no bloquean ahora; la pasada de evidencias comprueba que se recogieron)

- **O1 · `features.json` l. 1286** (y `BACKLOG.md` l. 143, generado de él): la descripción de F-078 acaba en «D1,
  D2 y D5-D11 abiertas». Añadir la línea fechada del cierre: «ok a todo», 2026-11-27, design §10.
- **O2 · `azure-apps/dedicacion.md` l. 521** dice «**sin desplegar** a 2026-11-27». Anotar en la entrada F-078 de
  «⚠» de `current.md` que al desplegar se quita, en commit aparte y con push del humano.
- **O3 · ruff:** los tests nuevos suben la deuda en 4 avisos: `test_f078_paquete_api.py` l. 158 (ISC004) y
  `test_f078_paquete_front.py` l. 102 (PIE808), 323 y 423 (ISC004). `routes.py` y `registro_sigrid.py`, igual que en
  `dev` (4 y 7).
- **Sugerencias, no se exigen.** S1: `routes.py` l. 182 quita repetidos con `ide not in ides` sobre una lista,
  cuadrático y sin tope (D7); un `set` de vistos lo deja lineal. S2: R1 incluye VAR y vinculados en «entero», y
  `_filas()` no trae ninguno: lo garantiza la estructura (la misma consulta y `mandadas`), no un test.

## Para la pasada de evidencias y automejora

- **Alcance:** `registro_sigrid.py` (42 líneas) y `routes.py` (46). **`app.js` no se muta**: lo cubren los 63 tests
  node y F1-F10. **RM6:** no se mata un mutante quitando `if valor is None`, `if x is None` (l. 177) o el
  `is not None` de `_filtro_trabajadores`: son la defensa de R3 y R10 (A2, A6).
- **Automejora (propuesta para `CHECKPOINTS.md` C4 bis, no aplicada):** si una feature `critico` cambia código que
  la mutación no mide (aquí, el JS), pedir en la pasada principal una tabla de rupturas a mano como la de arriba.
