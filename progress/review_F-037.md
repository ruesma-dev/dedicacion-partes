<!-- progress/review_F-037.md -->
Revisión incremental desde `ac125cb` (pasada 2), delta `185d78e..af71e04`

# F-037 · Review (reviewer, 2026-10-06)

**Veredicto: APPROVED.**

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 %, cero supervivientes y las MANUAL con su comando exacto.

## Alcance de esta pasada

- **Pasada 1** (completa, `3252814..ac125cb`): sale CHANGES_REQUESTED solo por
  el rastro. El código, los tests, la mutación y los docs se dieron por buenos
  hasta `ac125cb`. El detalle está en `git show 185d78e:progress/review_F-037.md`
  e incluye:
  - las copias, idénticas a `partes` `9b202e9`;
  - el SQL igual que `partes`, con el alta D17 fuera del agregado y con `emp`;
  - el recálculo de la campaña (85 y 25 mutantes) y 4 mutantes reproducidos a
    mano (RM4);
  - las desviaciones §3, aceptadas;
  - la tabla requisito → test.
- **Delta de la pasada 2** (`af71e04`): solo `progress/current.md`,
  `progress/history.md` y `harness/features.json`. No toca código, tests,
  `docs/` ni ficheros del alcance de mutación, así que no invalida nada de lo
  aprobado. RM1 sigue valiendo: medido en `40b9feb`, y desde ahí no ha
  cambiado ningún `.py`.
- `bash harness/init.sh`: **ENTORNO LISTO**. Raíz: 418 passed y 1 skipped. Los
  tres servicios en verde. COBERTURA 100 % (219/219). TAMAÑO dentro.
- `grep -n "Ninguna feature" progress/current.md`: **vacío**.

## Los cuatro cambios de la pasada 1

1. **T13 con comandos exactos: [x].** `current.md` trae cinco pasos. La
   autorización expresa y el aviso a Administración son condición previa, y
   cada paso lleva su resultado esperado. Comprobado que lo citado existe:
   - la ruta `POST /periodos/{anio}/{mes}/registro/ejecutar` admite
     `trabajador_ide` (`dedicacion-api/.../routes.py:323`);
   - `SigridApiClient(settings).leer(sql)` y `get_settings()` existen en la api;
   - `prueba_escritura_porcentajes.py limpiar` hace dry-run sin `--confirmar`
     (`fase_limpiar`).
2. **Poda: [x].** La sección F-037 se queda en lo vigente (qué es, spec,
   implementación, reviews, T11, T14, la observación y las MANUAL). Las viñetas
   superadas pasan a `history.md` (2026-10-06). «Lo siguiente» dice «F-037 en
   curso».
3. **`acceptance`: [x].** Está alineada con D1 = A: el ANA lo genera Sigrid, el
   transfer rellena `caaide` con la regla de `partes`, el parte se elige como en
   `partes`, las copias son literales y se vigilan, y las verificaciones son T12
   y T13. `BACKLOG.md` está al día según `init.sh`.
4. **T11: [x].** Consta que `partes` ya recogió D17 (`9ea7c59`), que falta el
   aviso de `OrigenSubcuenta` y que su DA11 obligará a recopiar y mover
   `COMMIT_COPIADO`.

## Checkpoints (estado final)

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] rama `feature/F-037-…` ·
  [x] `current.md` sin restos caducados de F-037 · [x] history.
- **C3** [x] Sin cambios desde la pasada 1: hexagonal, primera línea con ruta,
  sin print, TODO ni secretos, y las tres trampas respetadas.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] Trazabilidad R1-R19 (tabla de la pasada 1) · [x] sin red ni BBDD
  (SQLite en memoria es un fixture; desviación 3, aceptada) · [x] MANUAL T12 y
  T13 con su comando exacto en `current.md`, pendientes del humano.
- **C4 bis** [x] Sin cambios desde la pasada 1:
  - fase RED con trazas reales; cobertura al 100 %;
  - 85/85 y 25/25 recalculados; campaña no reejecutada (423,1 s y 107,0 s,
    más de 60 s), con recálculo puro y RM4;
  - coste por mutante 5,0 s y 4,3 s con W=1; RM1 y RM2 coherentes;
  - **RM5 N/A**: no hay ningún equivalente declarado;
  - **RM6 N/A**: no se quitó ninguna guarda;
  - cero supervivientes; «Evidencias» completa.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1-T10, T14 y T15 `[x]` con su commit `F-037 Tn:`. T11 (aviso de
  `OrigenSubcuenta`), T12 y T13 son MANUAL del humano y del líder, listadas y
  pendientes **antes del `done`** · [x] sin artefactos · [x] `features.json`
  refleja el estado real.

## Antes de marcar `done` (no bloquea esta aprobación)

- T12 y T13 ejecutadas por el humano, con el resultado real en `current.md`.
- T11: el aviso de `OrigenSubcuenta` a `partes`.

## Observaciones no bloqueantes

- En `history.md`, el bloque movido conserva su encabezado `## F-037 · … (en
  curso)` debajo de la entrada fechada. Se puede retocar al cerrar.
- El SELECT del paso 2 de T13 filtra `LIKE 'porcentajes:%'`: con el transfer
  desplegado en real, puede traer líneas reales además de la de prueba. Al
  ejecutarlo conviene filtrar por la `synckey` concreta.
- El aviso de cuenta que queda en una acción omitida por `parte_cerrado` se
  contrasta con `partes` al recopiar por DA11 (recogido por el líder).

## Automejora propuesta (no aplicada; repetida de la pasada 1)

- `reviewer.md`: ante copias entre repositorios, mirar también si la rama
  vigilada tiene **decisiones abiertas que cambiarán las copias** (aquí, la
  DA11 de `partes`). El test anti-divergencia solo ve commits.
