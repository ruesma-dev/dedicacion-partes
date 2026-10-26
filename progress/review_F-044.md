<!-- progress/review_F-044.md -->
Revisión incremental desde e223d22 (pasada 2): delta `e223d22..9193b8e`

# F-044 · Review 2 · **APROBADO** (APPROVED)

La pasada 1 (`afec7fa`, en el historial de este fichero) revisó la feature
entera (`ba6b575..e223d22`). La rechazó solo por el guion y el rastro de
T21 (B1, B2). Lo que aprobó entonces queda dado por bueno: el código de los
tres servicios, R1-R32 con sus tests, la mutación verificada de forma
independiente (RM1-RM5) y la no regresión de F-062 y F-051.

**Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura,
mutación con cero supervivientes sin justificación aceptada y MANUAL con
su comando y su resultado real.

## Alcance del delta

- **Código:** `git diff e223d22..9193b8e -- services` sale **vacío**. La
  campaña de `38a53d0` y la cobertura siguen valiendo.
- **Ficheros cambiados:**
  - `progress/current.md`;
  - `progress/impl_F-044.md`;
  - `progress/review_F-044.md` (la pasada 1);
  - `progress/manual_F-044.md` (nuevo);
  - `specs/F-044-recursos-vinculados/tasks.md` (notas de enmienda).
- **Lo aprobado sigue en pie:** el delta no cambia firmas, no mueve
  ficheros y no toca el alcance de la campaña.

## Bloqueos y observaciones de la pasada 1

- **B1 · RESUELTO.** El guion «F-044 · T21» de `current.md` comprueba
  ahora, antes de escribir y con PARAR si algo falla:
  - (a) `curl http://127.0.0.1:8006/health` ⇒ `modo_pruebas:true`, `0404`,
    `ruesma`;
  - (b) `transfer_base_url` de la api ⇒ `http://127.0.0.1:8006`, con el
    comando exacto;
  - (c) «MODO PRUEBAS» en el modal;
  - y después `get_settings` del transfer.

  `tasks.md` T21 lo recoge en su enmienda. Ningún comando lleva
  `--permitir-modo-real`.
- **B2 · RESUELTO.** La decisión de que T21 la haga el líder a petición del
  humano («haz tu la prueba», 2026-10-26) consta ya en:
  - `current.md:10` (cabecera) y `:145` (título);
  - `impl_F-044.md:5-6` y `:156-159`, con el guion original conservado y
    rotulado;
  - `tasks.md`, como nota de enmienda en la cabecera y en T21, sin
    reescribir lo aprobado.

  También se corrigió el título de `current.md:44`. T21 sigue `[ ]`, y es
  correcto: falta la parte del humano.
- **O1 · RESUELTA.** El guion avisa de que `limpiar` filtra por marca y
  prefijo, no por obra, y de que borra también la `OTEL` y la `OGAS` hechas
  a mano.
- **O2 · RESUELTA.** `manual_F-044.md:41-61` trae las 8 líneas JSON
  completas, el mapa `paride` → código y los importes tras el 70/30.

## `progress/manual_F-044.md` (nuevo)

Cuadra con el código aprobado:

- **Importes:** `tot = round(can × pre, 2)` recalculado en las 16 cifras
  (60/40 y 70/30), p. ej. 0,6 × 280 = 168 y 0,7 × 6500 = 4550.
- **R12:** el `can` es el del titular, sin normalizar.
- **R13:** `synckey` `porcentajes:vin:{registro}:{recurso}`; reejecutar da
  `ya_registrado`.
- **R17:** en postventa, la partida del titular (360138).
- **R15 y R8:** en la 0722, la CI del tipo, salvo la `CI.4.4` elegida.
- **R20 y R24:** con el 70/30 se edita en su sitio, con las mismas `ide` y
  sin `DELETE`.
- **Limpieza:** borra exactamente las 8.

**Pendiente del humano (R33), sin contarlo como hecho:**

- las líneas ajenas hechas a mano: la `OTEL` al 0 % y el pisado de una
  `OGAS` ajena;
- la validación de Administración.

Sin Sigrid, esos caminos los cubren los tests r20, r21 y r24.

**Barrido de datos sensibles** de `manual_F-044.md` y `current.md`:

- patrones: correo, IPv4 (salvo `127.0.0.1`), GUID y
  `password|secret|api_key|function_key|code=`;
- resultado: 0 coincidencias. Solo hay `ide` y códigos de recurso, sin
  nombres.

## Checkpoints (lo que el delta puede mover)

- **C1** [x] `bash harness/init.sh` entero, con `.arnes_cache/suite_*.ok`
  borrados antes. Sale con exit 0, sin `[KO]` y con `ENTORNO LISTO`:
  - tests: harness 418 + 1 omitido, api 1308, front 403, transfer 1585;
  - puerta de cobertura `[OK]`: 99,3 % (1100/1108);
  - puerta de tamaño `[OK]`: impl 220/220, review ≤ 140;
  - único aviso: ruff 307 (deuda previa).
- **C2** [x] Una sola feature `in_progress`. [x] Rama de la feature.
  [x] `current.md` coherente (B2). [x] `history.md` sin cambios.
- **C3** [x] El delta no tiene código; vale la pasada 1.
- **C3 bis** N/A: el delta no toca `docs/referencia/` ni añade originales.
- **C4** [x] R1-R32 en verde (tabla de la pasada 1). [x] Sin red ni BBDD.
  [x] MANUAL listada con su comando exacto y su resultado real. R33 está
  parcial (falta la parte del humano); R34 se hace en T23.
- **C4 bis** [x] Igual que en la pasada 1, porque el delta no toca código.
  Campaña **no reejecutada** (3350,8 s según su informe); recálculo puro y
  RM1-RM5 ya hechos.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T1-T20, T22 y T24 `[x]` con su commit. T21 (parte del humano)
  y T23 (despliegue) siguen abiertas, como dice la spec. [x] Árbol limpio.
  [x] `features.json` dice `in_progress`.

## Observaciones nuevas (no bloquean; recogerlas al cerrar)

1. **`impl_F-044.md:8` contradice el manual.** Dice «No se ha hecho
   ninguna escritura en Sigrid, ni real ni de pruebas» justo debajo de T21
   hecha. Era cierto del implementer, pero leído hoy no cuadra con
   `manual_F-044.md`. Matizar: «el implementer no escribió en Sigrid; las
   escrituras de T21, en modo pruebas, son del líder».
2. **`manual_F-044.md:10-14` promete más de lo hecho.** El título dice
   «Modo comprobado antes de cada escritura», pero (b) `transfer_base_url`
   se comprobó **después**, con los mismos `.env`. Lo que garantizó el modo
   durante las escrituras fue (a) más (c): `forzada_pruebas: true` sale del
   mismo proceso que escribe, y las 8 líneas cayeron en la 0404 con
   `PRUEBA-PORC`. Ajustar el título.
3. **Dos huecos de visibilidad (`manual_F-044.md:72-79`).** La respuesta de
   `/sync` no trae el conteo de vinculados, y el `resumen` del preflight
   solo cuenta titulares. No incumplen la spec (R3 va al preview, R25 a
   `vinculados`); que el humano decida si merecen feature.
4. **Al desplegar (T23, transfer → api → front):** el aviso a `partes`
   (R34, design §10) y `azure-apps/dedicacion.md`.

## Automejora (propuesta, no aplicada)

Se mantiene la de la pasada 1. En `CHECKPOINTS.md` C4, para toda MANUAL que
escriba en Sigrid: comprobar **el proceso que escribe** (`/health`) y
**adónde apunta la api** (`transfer_base_url`) **antes** de la primera
escritura. La observación 2 es justo el caso que esto evitaría.
