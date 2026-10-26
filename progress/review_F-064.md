<!-- progress/review_F-064.md -->
Revisión completa (pasada 1), `dev` (`e9ca262`) .. `3492abe`

# F-064 · Review 1

**Veredicto: RECHAZADO (CHANGES_REQUESTED).** El código hace lo que pide la
feature y `init.sh` sale en verde. Lo que falla es la evidencia: la campaña
manual no se puede reproducir (B1), la MANUAL no está en `current.md` (B2) y
sobrevive un mutante realista porque los tests no usan la forma real del
conflicto de un trabajador (B3).

**Rigor:** `estandar`, declarado. Exige fase RED, cobertura de las líneas
cambiadas y mutación con los supervivientes analizados. Con `sdd: false` se
valida contra los 5 `acceptance` y la opción 1 que eligió el humano al
bloqueo.

## Verificación del reviewer

- Borré `.arnes_cache/suite_*.ok` y ejecuté `bash harness/init.sh` solo, en
  el worktree. Exit 0, «ENTORNO LISTO», ningún [KO]. Raíz: 418 passed y 1
  skipped. Api: 1308. Front: 414 (11 son de F-064). Transfer: 1585.
  `PUERTA COBERTURA: N/A (F-064 no cambia líneas Python de producción frente
  a dev)`. `PUERTA TAMAÑO: impl 167/220`. `git status` queda limpio.
- Diff `dev...HEAD`: `app.js` y el test nuevo del front, una sola hunk en
  `test_f013_sin_partida.py`, la nota de F-044 y el rastro. No cambian ni el
  código del transfer ni el de la api, ni ningún otro test existente.
- Mutantes propios sobre una COPIA en el scratchpad (sin `.venv` ni `.env`),
  contra `test_f064_pisado_vinculados.py`, con base de 11 passed:
  - M1, quitar `Boolean(c.vinculado) &&`: 6 failed.
  - M2, `(c.motivo || "pisado") === "pisado"` → `c.motivo === "pisado"`: 5 failed.
  - M3, `marcadaPorDefecto(c) && !registro.vistas.has(c.clave)` →
    `marcadaPorDefecto(c)`: 5 failed.
  - M5, borrar `registro.vistas = new Set();`: 1 failed.

  Los cuatro dan los mismos fallos que el informe. Además:
  - R1, `&&` → `||` en ese `if`: 9 failed.
  - **R2**, `Boolean(c.vinculado)` → `c.vinculado !== undefined`: **sobrevive**,
    tanto al fichero de F-064 como a la suite ENTERA del front (B3).
- Mutación automática: `alcance_de_feature('F-064')` da `{}`. En la prueba de
  control, `generar_mutantes` sobre `app.js` sin la exclusión da 0, porque
  solo muta Python, y sobre el test de F-013 da 2, así que el generador
  funciona. El cero es legítimo por el lenguaje y lo sustituye la campaña
  manual.

## Lo pedido en especial

1. **Solo sale marcado el pisado de un vinculado.** Lo decide
   `marcadaPorDefecto` (`app.js:3347-3353`), con el mismo criterio de «sin
   motivo = pisado» que `rotuloConflicto`. El transfer crea ese pisado con el
   motivo por defecto (`registro_vinculados.py:362-373`). Hay tests para el
   trabajador, la sobrecarga y el sin partida de los dos, el motivo
   desconocido y el cierre de racha.
2. **Al repetir el preflight**, `repreflightPartida` relee `pisar` del DOM y
   `vistas` se conserva. Lo cubren dos repeticiones seguidas, una clave nueva
   y otra obra que no se toca.
3. **Un preflight nuevo** vacía `pisar` y `vistas` (`app.js:2926-2929`).
   **`pisar_claves`:** `registroEjecutar` no cambia y lee las marcadas; dos
   tests van contra el cuerpo real de `/registro/ejecutar`.
4. **Test de F-013 R4:** solo cambia `fuera`, que excluye también el cuerpo
   de `marcadaPorDefecto` (comentario que cita F-064). Es la opción 1 al pie
   de la letra. **Enmienda** en R20 y R31, fijada por su test.
5. **Front sin lógica de negocio:** es el valor de partida de una casilla
   visible, como aceptó el humano; el transfer sigue exigiendo cada clave.
6. **Rastro:** la cabecera de `current.md` es correcta («implementada; review
   1 lanzada») y `BACKLOG.md` está al día según `init.sh`. Quedan B2 y O1.

## Checkpoints

- C1: [x] `init.sh` en exit 0. [x] Ficheros del arnés presentes.
- C2: [x] Una sola `in_progress`. [x] Rama de la feature. [x] `current.md`
  coherente con la sesión. [x] `history.md` sin pendientes (F-064 no es `done`).
- C3: [x] Hexagonal: solo cambia el front. [x] Ruta en la primera línea.
  [x] Sin prints, secretos ni dependencias nuevas. [x] Trampas del dominio:
  N/A justificado (ni escala, ni postventa, ni escritura en Sigrid).
- C3 bis: N/A justificado, no toca `docs/referencia/`.
- C4: [x] Los 5 `acceptance` tienen tests y pasan. [x] Sin red ni BBDD
  (node con DOM y api de mentira). **[ ] La MANUAL del humano no está en
  `current.md`** (B2).
- C4 bis:
  - [x] `rigor` declarado.
  - [x] Fase RED: la traza de T1 (`8 failed, 1 passed`) cuadra línea a línea
    con el fichero de `fef5ec4`.
  - [x] Cobertura: N/A, con el motivo impreso.
  - [x] Mutación automática: alcance `{}` y prueba de control, hechos.
  - N/A justificado (sin campaña automática que juzgar): 60 s, coste por
    mutante, base rota, RM1, RM2. RM5: por nivel. RM6: ninguna guarda quitada.
  - **[ ] Campaña MANUAL** (B1): las filas no traen `fichero:línea` ni el
    texto exacto original → mutado, y faltan el SHA y la línea base. Reproduje
    cuatro filas, pero tuve que adivinar el texto.
  - **[ ] Superviviente sin analizar** (B3, R2).
  - [x] «Evidencias» trae los cuatro números. Falta el nº de workers de la
    campaña manual, que se pide en B1.
- C4 ter: N/A, `init.sh` no señala rutas sensibles.
- C5: `tasks.md` es N/A justificado (`sdd: false`); los commits llevan
  `F-064 Tn:`. [x] Sin ficheros temporales. [x] `features.json` dice
  `in_progress`, que es el estado real.

## Cobertura acceptance → test (`test_f064_pisado_vinculados.py`)

| Acceptance | Tests |
|---|---|
| 1 · al abrir | `al_abrir_solo_el_pisado_de_vinculado_sale_marcado`, `sin_vinculados_el_modal_de_hoy_todo_desmarcado`, `la_casilla_marcada_lleva_checked_en_el_html`, `marcada_por_defecto_solo_el_pisado_de_vinculado`, `marcada_por_defecto_es_pura_y_la_usa_el_modal` |
| 2 · repetir / nuevo | `desmarcada_sigue_desmarcada_al_repetir_el_preflight`, `repetir_una_obra_no_toca_lo_desmarcado_en_otra`, `un_preflight_nuevo_vuelve_al_valor_por_defecto` |
| 3 · `pisar_claves` | `registrar_por_defecto_manda_los_pisados_de_vinculado`, `registrar_manda_exactamente_las_marcadas` |
| 4 · enmienda | `enmienda_anotada_en_r20_y_r31_de_f044` |
| 5 · `init.sh` | verificado por el reviewer |

## Cambios requeridos

1. **B1 · Campaña manual reproducible** (C4 bis). Escribe
   `progress/mutacion_manual_F-064.md` con el formato de
   `progress/mutacion_manual_F-042.md` y medida sobre la versión final, B3
   incluido. Tiene que traer:
   - el SHA medido, la línea base en la copia, los workers y el tiempo;
   - una fila por mutante con `app.js:línea`, el **texto exacto original →
     mutado** (único en el fichero) y el nº de fallos;
   - el bloque que la reproduce, fuera del alcance de producción.
2. **B2 · MANUAL en `current.md`** (C4). Pasa la comprobación en el navegador
   de «Pendiente (MANUAL)» del informe a «⚠ Lo que espera al humano», con sus
   pasos exactos: qué sale marcado, que lo desmarcado se mantiene tras
   cambiar una partida y que «Registrar» lo respeta.
3. **B3 · Forma real del conflicto de un trabajador.** El transfer manda
   `"vinculado": null` (`asdict`, `registro_models.py:476`), pero
   `_conflicto(..., vinculado=None)` omite la clave por su `if vinculado is
   not None`. Por eso sobrevive R2, que marcaría por defecto el pisado del
   **trabajador**, justo lo que prohíbe el criterio 1. Pon siempre la clave,
   con `null` para el trabajador, o añade el caso `{"vinculado": None}` a
   `marcada_por_defecto_solo_el_pisado_de_vinculado` y al escenario
   `al_abrir…`. R2 tiene que salir muerto en B1.

## Observaciones (no bloquean; recógelas en la misma vuelta)

1. **O1.** El título `## F-064 · BLOQUEO` de `current.md` ya no es cierto.
   Renómbralo a algo como «F-064 · bloqueo resuelto (opción 1) e
   implementación».
2. **O2.** `specs/F-044-recursos-vinculados/requirements.md` pasa a 154
   líneas, por encima del tope de 150. No bloquea porque F-044 ya está `done`;
   que lo sepa el líder.
3. **O3.** La review 2 será incremental desde `3492abe`. `app.js` y el test de
   F-013 se dan por buenos salvo que el delta los toque.
