<!-- progress/review_F-039.md -->
Revisión incremental desde `a3565af` (pasada 2), delta `a3565af..a977b03`

# F-039 · Review (reviewer, 2026-10-06)

**Veredicto: APPROVED.**

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 %, cero supervivientes y las MANUAL con su comando exacto.

## Alcance de esta pasada

- **Pasada 1** (completa, `f7cc4e9..3b531ac`): salió CHANGES_REQUESTED **solo
  por el rastro** de `progress/current.md`. Dejó dados por buenos el código,
  los tests, la mutación y los docs. El detalle está en
  `git show a3565af:progress/review_F-039.md`. Incluye:
  - el límite de servicio y el registro VAR;
  - el filtro de 6+ dígitos y el `ide` negativo;
  - los tests anteriores cambiados, que son solo los de design §7.1;
  - el recálculo de la campaña: 18 ficheros, 495 líneas, 60 mutantes;
  - RM1-RM6, con 4 mutantes reproducidos a mano (#47, #52, #2, #17) y 2
    mutantes manuales en `registro_sigrid.py`, todos muertos;
  - la copia literal en `azure-apps` (`f01156f`);
  - la tabla requisito → test (R1-R24).
- **Delta de la pasada 2** (`a977b03`): toca solo `progress/current.md` y
  `progress/history.md`. `git diff --stat a3565af..HEAD -- services docs
  specs harness scripts` sale vacío. No cambia código, tests, docs ni ningún
  fichero del alcance de mutación, así que no invalida nada de lo aprobado y
  la campaña medida en `6ab6588` sigue valiendo (RM1).

## Verificación del delta

- **`bash harness/init.sh`**: `ENTORNO LISTO`, exit 0.
  - Raíz: 418 passed, 1 skipped.
  - api, front y transfer en verde. La caché es válida porque el delta no toca
    `services/`.
  - `PUERTA COBERTURA`: 100 % (181/181).
  - `PUERTA TAMAÑO`: dentro.
- `grep -n "Ninguna feature" progress/current.md` no devuelve nada (exit 1).
- **Cambio 1 (poda): corregido.**
  - La cabecera y la sección F-039 reflejan el estado real: implementada, la
    review 1 rechazada solo por el rastro y la review 2 lanzada.
  - Han desaparecido «Primera del backlog», «F-039 tercera. No hay F-041.»,
    «F-040 … espera al humano con D1-D6», «F-029 espera a desplegar» y
    «Ahora F-037».
  - Hay una sección nueva con F-040 (`c16af41`) y F-041 (`9b5fc46`)
    aprobadas. He comprobado que los dos commits existen en sus copias
    (`git log`, solo lectura).
  - «Lo siguiente» sigue el orden de `BACKLOG.md`: F-040, F-038, F-041,
    F-039, F-028, F-021, F-030, F-036, F-031, F-033, F-017, F-018. F-037
    consta como cerrada y pendiente de desplegar.
  - Lo retirado se ha pasado entero a `history.md`, bajo un encabezado que lo
    marca como rastro retirado. No se pierde información, y lo que ahí parece
    vigente está fechado como histórico.
- **Cambio 2 (MANUAL): corregido.**
  - Arranque: «`python main.py` con la `.venv` de cada servicio en
    `services/dedicacion-transfer` y `services/dedicacion-api` (la api con
    `PG_HOST=localhost`)».
  - T12 y T13 llevan su comando `powershell … verif_f039_var.ps1 -Paso M1|M2`
    y el resultado esperado.
  - T14 lleva «`python main.py` en `services/dedicacion-front` y abrir
    `http://127.0.0.1:8080`» y los pasos de usabilidad, cerrando el modal sin
    registrar.
  - Ninguna llama a `registro/ejecutar`.
- **Observaciones de la pasada 1**: están recogidas en `current.md`, con el
  encargo para `arnes-base` (0 mutantes en `registro_sigrid.py` y los falsos
  supervivientes #2 y #17).

## Checkpoints

- **C1** [x] `init.sh` con exit 0 · [x] están los ficheros base.
- **C2**
  - [x] Una sola feature `in_progress` (F-039).
  - [x] La rama es `feature/F-039-obras-var-y-seis-digitos`.
  - [x] `current.md` describe solo la sesión activa. Las secciones de
    despliegue, producción y pendientes del humano siguen vigentes, y ya no
    hay contradicciones.
  - [x] Todas las features `done` tienen resumen en `history.md`.
- **C3**
  - [x] Arquitectura hexagonal respetada.
  - [x] Primera línea con la ruta.
  - [x] Sin prints, TODOs, secretos ni dependencias nuevas.
  - [x] Las tres trampas: la escala viaja sobre 1, la postventa con
    `var_paride` se omite y solo escribe el transfer, con `synckey` y en modo
    pruebas. Aprobado en la pasada 1 y sin cambios desde entonces.
- **C3 bis** N/A: la feature no toca `docs/referencia/`.
- **C4**
  - [x] Cada requisito R1-R24 tiene al menos un test (R24 es documental y se
    verificó leyendo; tabla en la pasada 1).
  - [x] Sin red ni BBDD.
  - [x] Las MANUAL T12-T14 están en `current.md` con su comando exacto, a la
    espera del humano.
- **C4 bis**
  - [x] Rigor declarado y fase RED pegada (T1-T8 y T11).
  - [x] Cobertura al 100 %.
  - [x] Totales de la campaña recalculados: 60 mutantes.
  - [x] No se reejecuta: la campaña tardó 1274,4 s, más de 60 s.
  - [x] Coste por mutante: 21,2 s.
  - [x] Sin cabecera de campaña no válida y con «Sin veredicto» a 0.
  - [x] RM1: la medición es de `6ab6588` y el alcance no ha cambiado desde
    entonces.
  - [x] RM2: 60 × 21,2 = 1272 s, que cuadra con el total; líneas base de
    37,8 s y 14,0 s.
  - N/A RM5: no hay equivalentes.
  - N/A RM6: no se quitó ninguna guarda.
  - N/A campaña manual: la automática generó 60 mutantes.
  - [x] Cero supervivientes.
  - [x] La sección «Evidencias» trae los workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5**
  - [x] T1-T11 y T15 están `[x]`, cada una con su commit `F-039 Tn:`.
  - T9 la hizo el líder (`f01156f`).
  - T12-T14 son MANUAL del humano, listadas con su comando: en `critico`
    pueden quedar pendientes al cerrar la review.
  - [x] Sin artefactos sueltos (`git status` limpio).
  - [x] `features.json` refleja `in_progress` hasta el cierre.

## Lo que queda para cerrar (no bloquea esta review)

1. El humano lanza las MANUAL **T12 (M1), T13 (M2) y T14 (M3)** contra lo local
   y anota el resultado real en `current.md`. Ninguna escribe en Sigrid.
2. **Despliegue en orden transfer → api → front.** Una api nueva con un
   transfer viejo deja el sync en 502 (`INTEGRACION` §7). La 29 ya tiene
   MESVE/MPRL de 2026-08: el registro de ese mes para esos recursos dará un
   **pisado** que hay que confirmar, no un duplicado (design §9).
3. `azure-apps` `f01156f` dice «sin desplegar». Hay que actualizarlo cuando
   se despliegue.
