<!-- progress/review_F-026.md -->
Revisión incremental desde `38da924` (pasada 2) hasta HEAD `c8bf04c`

# F-026 · Review: el trabajador es el recurso

**Veredicto pasada 2: CHANGES_REQUESTED.** El cambio de la pasada 1 está
resuelto y verificado: test R20 real, campaña 55/56 válida, superviviente nº 5
equivalente de verdad. Falla el **rastro**: `progress/current.md` arranca
diciendo que F-034 está en curso con T8 y M4 pendientes, contra `features.json`
y contra su propio cuerpo (C2). Lo arregla el líder; no toca código ni campaña.

**Rigor: `critico`** (declarado). Exige fase RED, cobertura ≥ 80 %, mutación con
cero supervivientes salvo justificación aceptada por el humano, RM5 con muestra
de uno y MANUAL con comando exacto.

## Pasada 2 · verificación propia (resultados reales)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**. Raíz `374 passed, 1
  skipped`, `PUERTA COBERTURA 100.0% (92/92)`, `PUERTA TAMAÑO` en verde. Rama
  correcta, árbol limpio antes y después.
- **Delta**: 4 ficheros. Código, solo `transfer/tests/test_f026_recurso_dado.py`
  (+26, un test). **Ni una línea de producción**, ni `specs/`, `docs/`,
  `infra/` ni `harness/`; el resto es `progress/`.
- **Test R20** (`test_f026_r20_lineas_de_ejemplo_sin_editar_no_escriben`):
  fija lo pedido y más. `registro_id` únicos, synckey únicas (`synckey_de`),
  todo `recurso_ide == 0` y el preflight real omitiendo las tres por
  `MOTIVO_SIN_RECURSO` con un doble que revienta si se elige recurso. Sin red
  ni BBDD; primera línea con ruta.
- **RED reproducida (RM4)** en una copia `git archive HEAD` en el scratchpad:
  base `330 passed`, suite entera del transfer, texto exacto del generador.
  - nº 1 (`:47` `900001→900002`): `AssertionError: [900002, 900002, 900003]`,
    `assert 2 == 3` → `1 failed, 329 passed`.
  - nº 4 (`:50` `recurso_ide 0→1`): `assert [0, 1, 0] == [0, 0, 0]` →
    `1 failed, 329 passed`.
  - nº 5 (`:53` `900003→900004`): `330 passed`. Coincide con §5 bis del impl.
- **Campaña del ciclo 2, recálculo puro** (`alcance_de_feature` y
  `generar_mutantes`): 14 ficheros, **262 líneas, 56 mutantes**, como el
  informe. Los 6 del script, en el mismo orden y texto que en la pasada 1; el
  superviviente existe con operador `entero` y el mismo texto.
  - **Campaña no reejecutada: 576,9 s según el informe** (> 60 s).
  - Sin «CAMPAÑA NO VÁLIDA»; `Sin veredicto (base rota)` 0; base por servicio.
  - RM1: SHA medido `df7e94c`; desde él solo cambia `progress/`. Mismo alcance.
  - RM2: base api 14,5 s y transfer 4,5 s, media 10,3 s, 56 × 10,3 ≈ 577 s =
    total; `--workers 1`. Sin saltos de orden de magnitud.
  - RM3: los 5 muertos nuevos son los no equivalentes probados en la pasada 1;
    los otros 50 ya estaban muertos y revisados. Ningún equivalente muerto.
  - RM5 (muestra de uno: nº 5, el único declarado). **Equivalente**: el valor
    solo construye la `LineaEntrada` y su synckey. `verificar` (l. 181) deriva
    las claves de la propia `LINEAS_PRUEBA`; `limpiar` (l. 193-195) busca por
    marca y prefijo. Ningún otro fichero lee `9000xx`, y unicidad y centinela
    siguen intactos (900001, 900002, 900004). **Necesita aceptación escrita
    del humano antes del `done`**: está en `current.md` l. 151-153.
  - RM6 `N/A`: no se quitó ninguna guarda; los mata un test añadido.
- **Informe del implementer**: §5 bis con salida real y Evidencias al día
  (transfer 330, 55/56, 576,9 s, workers 1). Cuadra con lo medido.

## Pasada 2 · `progress/current.md` (leído entero)

Bien: F-026 `in_progress`, F-034 `blocked` solo por T9, F-025 `pending`;
T14-T16, despliegue y nº 5 con comando y resultado esperado. **Mal**:

- l. 4-5, la cabecera: «**F-034 en curso** (…; faltan T8, T9 y la aceptación
  de M4)». En `features.json` la que está en curso es F-026 y F-034 está
  `blocked`; T8 está CUMPLIDA (l. 84-90) y M4, ACEPTADO (l. 105-108). Una
  sesión nueva que lea la cabecera (paso 2 del protocolo) retomaría la feature
  equivocada. **Ya estaba en la pasada 1 y lo dejé pasar**; lo corrijo aquí.
- l. 31-33: «T2 hecha pero guardada en `stash@{0}`». `git stash list` está
  vacío y T2 ya está commiteada: es resto de una sesión anterior.
- l. 21-22: «va con F-026.» y «Se despliega **junto con F-026**.», repetido.
- Las observaciones de la pasada 1 (`ruff I001` en 4 ficheros, la frase de
  `infra/README_dedicacion.md` l. 159 y la automejora de RM5) ni se recogen ni
  se descartan por escrito. Solo la de `workers > 1` está recogida (l. 158-160).

## Checkpoints (tras la pasada 2)

- C1 `[x]`.
- C2: `[x]` una sola `in_progress`, rama correcta, `history.md`. **`[ ]`
  `current.md` solo con la sesión activa**: ver arriba.
- C3 `[x]`: sin cambios de producción desde la pasada 1; el test nuevo cumple
  convenciones. C3 bis `N/A`: no entra ningún documento de fuera.
- C4 `[x]`: trazabilidad completa (tabla), sin red ni BBDD, MANUAL listadas.
- C4 bis `[x]`: rigor resuelto, RED con salida real (reproducida), cobertura,
  recálculo, regla de 60 s, coste por mutante, sin «CAMPAÑA NO VÁLIDA», RM1-RM5
  y Evidencias. Supervivientes en `critico`: uno, equivalente demostrado y
  reproducido; la **aceptación del humano bloquea el `done`, no la review**
  (mismo trato que M4 en F-034). RM6 y campaña manual `N/A` (motivos arriba).
- C4 ter `N/A`: no existe `harness/rutas_sensibles.json`. C5 `[x]`: T0-T13 y
  T17 con su commit `F-026 Tn`; los del ciclo 2 son de review, no de tarea;
  T14-T16 son MANUAL.

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1-R3 | `test_f026_r1_*` (6), f023 `r4`/`r5`, `r2_recurso_sin_ficha…`, `r3_*` (3) |
| R4-R6 | `r4_*` (7), `r17_preview_publica_posible…`, `r5_sync…`/`r5_preview…` (×3), `r6_*` (2) |
| R7-R9 | `r7_alta…`, `r8_*` (4), `r9_fila_que_no_llega…` |
| R10, R11 | `tests/test_f026_vaciado.py` |
| R12-R15 | `r12_*` (5+3), `r13_*` (8), `r14_*` (9 casos), `r15_*` (6) |
| R16-R18 | `test_f026_registro_recurso.py` (`r16_*` ×5, `r18_*`), `r17_*` (5) |
| R19-R22 | `transfer/tests/test_f026_recurso_dado.py` (+ `r20_lineas_de_ejemplo…`), f002/f022 |
| R23 | `test_f002_fuente_unica` (`ANCLAS` con `regla-recurso`), `r10_el_readme…` |
| R24, R25 | MANUAL T14 y T15 |

## Cambios requeridos (pasada 2; todos del líder, en `progress/current.md`)

1. **l. 4-5**: reescribir la cabecera para que diga lo que dice
   `features.json`: F-026 en curso (review pasada 2, pendiente el nº 5 y las
   MANUAL), F-034 `blocked` solo por T9. Sin T8 ni M4 como pendientes.
2. **l. 31-33**: quitar la mención a `stash@{0}` o pasarla a pasado («T2 se
   guardó en un stash y se recuperó en su commit»).
3. **l. 21-22**: dejar una sola vez «se despliega junto con F-026».
4. **Observaciones de la pasada 1**: recoger o descartar por escrito
   `ruff I001`, la frase de `README_dedicacion.md` l. 159 (después del sync
   esas líneas van a `no_vigentes`) y la automejora de RM5.

La pasada 3 será incremental y le basta `current.md` más `init.sh`: si no
cambia código, ni test nuevo ni campaña.

## Pasada 1 (resumen; completa desde `5a02ddb` hasta `e91874a`)

CHANGES_REQUESTED por un solo punto de evidencia. Verificado entonces:

- `init.sh` en verde; sin caché: api `440 passed`, transfer `329 passed`, front
  `21 passed`. Tabla §3 de tests cambiados, fila a fila: nada se afloja.
- Recálculo 14 ficheros, 262 líneas, 56 mutantes (base `5f498cb`, solo spec y
  rastro respecto a `5a02ddb`). Campaña de 506,4 s no reejecutada; RM1-RM3 bien.
- Comprobaciones del líder, correctas: sync desde `res` (`cla = 1`, ficha
  opcional); clave `res.ide` sin DDL; `vigencia.vigente_en` única; contrato
  sin `empleado_ide`; despliegue seguro; vaciado con `-Confirmar` y una sola
  `TRUNCATE`; F-034, F-025 y `azure-apps/` intactas.
- Pedido: 5 de 6 «equivalentes» no lo eran. **Resuelto en el ciclo 2.**

**Observación (no bloquea):** `current.md` l. 180-182 aún pide «datos para
F-026» con la spec implementada: confirmar o retirar.

**Automejora (propuesta):** en RM5, «que la suite pase con el mutante demuestra
que sobrevive, no que sea equivalente»; y que `init.sh` compruebe que la
cabecera de `current.md` nombra la `in_progress` de `features.json`. Ambas
valen para `arnes-base`.
