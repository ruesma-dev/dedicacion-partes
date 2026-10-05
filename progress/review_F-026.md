<!-- progress/review_F-026.md -->
Revisión incremental desde `c8bf04c` (pasada 3) hasta HEAD `9480200`

# F-026 · Review: el trabajador es el recurso

**Veredicto pasada 3: APPROVED.** Los cuatro cambios de la pasada 2 están
hechos: `current.md` reescrito y coherente con `features.json`, sin `stash`
ni frase duplicada, y las observaciones de la pasada 1 recogidas o descartadas
por escrito. Desde la pasada 2 no cambia ni una línea de código ni de test: la
campaña 55/56 sigue valiendo. **Antes del `done`** siguen pendientes, fuera de
esta review: la aceptación escrita del superviviente nº 5 y las MANUAL T14-T16
(y la T9 de F-034, que va con ellas).

**Rigor: `critico`** (declarado). Exige fase RED, cobertura ≥ 80 %, mutación con
cero supervivientes salvo justificación aceptada por el humano, RM5 con muestra
de uno y MANUAL con comando exacto.

## Pasada 3 · verificación propia (resultados reales)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**. Raíz `374 passed, 1
  skipped`; `PUERTA COBERTURA 100.0% (92/92)`; `PUERTA TAMAÑO` en verde; en
  curso `['F-026']`, bloqueadas `['F-034']`. Árbol limpio antes y después;
  `git stash list` vacío.
- **Delta** (`9480200`, un commit): `infra/README_dedicacion.md` (2 líneas),
  `progress/current.md`, `progress/history.md` y este informe.
  `git diff c8bf04c..HEAD -- services tests specs harness docs`: **vacío**, y
  `git diff df7e94c..HEAD -- services tests` (SHA medido por la campaña):
  **vacío**. RM1 sigue cumpliéndose; ni test nuevo ni campaña nueva.
- **`current.md` leído entero (168 líneas):**
  - Cabecera (l. 4-7): F-026 en curso, F-034 `blocked` solo por T9, despliegue
    conjunto, arnés 1.7.3. Cuadra con `features.json` y con `init.sh`. T8 y M4
    ya figuran como hechos (l. 83-84), no como pendientes.
  - Sin `stash@{0}` (T2 ya no se menciona como guardada); «se despliegan
    juntas» una sola vez (l. 7), más la sección de despliegue (l. 97-104).
  - MANUAL con comando exacto y resultado esperado: nº 5 (l. 34-36), T14
    (l. 37-51), T15 (l. 52-59, sin `registro/ejecutar`), T16 (l. 60-63),
    T9 de F-034 (l. 85-93). Los comandos son los mismos que vi en la pasada 2;
    T9 pasa de `2026/9` a `AAAA/MM`, igual que T15.
  - Sin rutas de sesión, scratchpad, GUID, IP, suscripción ni secretos (grep
    propio). La única «contraseña» es la que pide el `.ps1` por teclado.
  - «Lo siguiente» (l. 106-111) sigue el orden de prioridad de
    `features.json` (F-025 3, F-027 4, F-020 5, F-028 6… F-017 12).
- **`history.md`**: el bloque «2026-10-02 · Detalle de sesión retirado…»
  reproduce **literal** las l. 4-160 del `current.md` anterior (comparado con
  `diff` en el scratchpad: idéntico salvo `##`→`###` y una línea en blanco
  final). Las l. 162-185 viejas no se copian, pero no se pierde nada: la tabla
  de prioridades era obsoleta y la manda `BACKLOG.md`; el detalle de F-014 y
  F-016 está en su entrada de `features.json`; «Datos para F-026» lo deja sin
  objeto la spec (ficha opcional) y la pregunta sigue en
  `progress/explore_eusebio.md` l. 89.
- **Observaciones de la pasada 1, por escrito con motivo** (l. 64-79):
  - README §3 bis: **corregida** y verificada en el diff (l. 158-160): tras el
    sync, trabajadores no vigentes y líneas en `no_vigentes`. Es lo que dije.
  - `ruff I001`: **descartada** con motivo (estilo, `ruff` no bloquea, tocar
    tests reabriría la review). Aceptable.
  - Automejora de RM5 y cabecera de `current.md` → encargo `69df67b` en
    `arnes-base` (existe: `ENCARGO_pendiente_rm5_y_cabecera_current.md`).
    `workers > 1` → `affff93` (existe, amplía el encargo de falsos
    supervivientes).
  - Las dos observaciones del implementer (fila sin mes, `no_vigentes` sin
    mostrar): propuestas al humano, pendientes de decisión.

## Checkpoints (estado final)

- C1 `[x]`: entorno en verde, rama `feature/F-026-…`, ningún `.env`.
- C2 `[x]`: una sola `in_progress`, `current.md` solo con la sesión activa y
  coherente, `history.md` con lo retirado.
- C3 `[x]`: hexagonal, ruta en la primera línea, sin prints ni secretos; sin
  cambios de producción desde la pasada 1 salvo el test R20 (pasada 2).
- C3 bis `N/A`: no entra ningún documento de fuera.
- C4 `[x]`: trazabilidad completa (tabla), sin red ni BBDD, MANUAL listadas.
- C4 bis `[x]`: rigor resuelto, RED con salida real (reproducida en la
  pasada 2), cobertura 92/92, recálculo propio, regla de 60 s, coste por
  mutante, sin «CAMPAÑA NO VÁLIDA», RM1-RM5 y Evidencias. Un superviviente, el
  nº 5, equivalente demostrado y reproducido; su **aceptación por el humano
  bloquea el `done`, no la review** (mismo trato que M4 en F-034). RM6 `N/A`:
  no se quitó ninguna guarda. Campaña manual `N/A`: la automática dio 56.
- C4 ter `N/A`: no existe `harness/rutas_sensibles.json`.
- C5 `[x]`: T0-T13 y T17 con su commit `F-026 Tn`; T14-T16 son MANUAL; los
  commits de los ciclos 2 y 3 son de review, no de tarea.

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

## Observaciones (no bloquean y no piden acción para cerrar F-026)

- `current.md` l. 69: «193 avisos previos» de `ruff` (hoy 200) y «entra en
  F-006», que su entrada (asserts, no imports) no recoge. El descarte se
  sostiene solo con su motivo.
- El bloque de `history.md` dice «tal cual» y cubre las l. 4-160, no 162-185.
- «Lo que espera al humano» (l. 115) no nombra la autorización para T16, que
  la propia T16 exige (l. 60).

## Pasada 2 (resumen; incremental desde `38da924` hasta `c8bf04c`)

CHANGES_REQUESTED solo por el rastro; código, tests y campaña, correctos.

- Delta de código: un test, `r20_lineas_de_ejemplo…` (`registro_id` y synckey
  únicos, `recurso_ide == 0`, omitidas por `MOTIVO_SIN_RECURSO`).
- RED reproducida en copia `git archive` (RM4): base `330 passed`; nº 1
  (`:47` `900001→900002`) y nº 4 (`:50` `0→1`) → `1 failed, 329 passed`;
  nº 5 (`:53` `900003→900004`) → `330 passed`.
- Recálculo puro: 14 ficheros, **262 líneas, 56 mutantes**. Campaña **no
  reejecutada: 576,9 s** (> 60 s). SHA medido `df7e94c`. RM2: base api 14,5 s,
  transfer 4,5 s, media 10,3 s, 56 × 10,3 ≈ 577 s, `--workers 1`. RM3: ningún
  equivalente muerto. RM5: nº 5 equivalente (solo construye la `LineaEntrada`
  y su synckey; `verificar` y `limpiar` no dependen del literal).
- Pedido: cabecera de `current.md`, `stash`, frase duplicada y observaciones
  de la pasada 1. **Resuelto en la pasada 3.**

## Pasada 1 (resumen; completa desde `5a02ddb` hasta `e91874a`)

CHANGES_REQUESTED por un solo punto de evidencia. Verificado entonces:

- `init.sh` en verde; sin caché: api `440 passed`, transfer `329 passed`, front
  `21 passed`. Tabla §3 de tests cambiados, fila a fila: nada se afloja.
- Recálculo 14 ficheros, 262 líneas, 56 mutantes (base `5f498cb`). Campaña de
  506,4 s no reejecutada; RM1-RM3 bien.
- Comprobaciones del líder, correctas: sync desde `res` (`cla = 1`, ficha
  opcional); clave `res.ide` sin DDL; `vigencia.vigente_en` única; contrato
  sin `empleado_ide`; despliegue seguro en cualquier orden; vaciado con
  `-Confirmar` y una sola `TRUNCATE`; F-034, F-025 y `azure-apps/` intactas.
- Pedido: 5 de 6 «equivalentes» no lo eran. **Resuelto en el ciclo 2.**

**Automejora (propuesta, ya encargada en `arnes-base` `69df67b`):** RM5 con
criterio («que la suite pase con el mutante demuestra que sobrevive, no que
sea equivalente») y `init.sh` contrastando la cabecera de `current.md` con la
`in_progress`. Nueva: que la cabecera de un bloque retirado a `history.md`
declare el rango de líneas que copia, para que «tal cual» sea comprobable.
