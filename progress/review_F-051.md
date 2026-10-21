<!-- progress/review_F-051.md -->
Revisión incremental desde 7c668bc (pasada 3) hasta `ef9881a`. La pasada 2 fue incremental desde `c070244`; la pasada 1, completa sobre `2c75a1c...c070244`.

# F-051 · Review (reviewer, 2026-10-21)

**Veredicto: APROBADO.** T18 (la O2, aceptada por el humano) cumple lo que
pide `tasks.md`, trae su RED y la campaña de 136 mutantes y 0 supervivientes
mide exactamente el código de HEAD.

**Rigor:** `critico`, declarado en `features.json` (fase RED, cobertura
≥ 80 %, campaña completa con 0 supervivientes, RM5, MANUAL). **Para `done`
falta T15**; T16 es del líder al desplegar.

## Pasada 3 (2026-10-21): T18

**Delta.**
- Producción: solo `d5d61ac`. En el paso 6 (`registro_pipeline.py:570`) se
  añade `or not es_linea_mensual(hit)` y se actualiza el comentario.
- Tests: tres casos parametrizados (`H*`, `C*` y sin hora) y uno que sigue
  por `synckey`.
- Documentación: `#regla-cero` y `INTEGRACION` §5 lo dicen.
- Además: `features.json`/`BACKLOG.md` con F-058 (la O4, `pending`),
  `tasks.md` T18 `[x]`, el informe y `current.md`.
- Nada de lo aprobado cambia de firma, de fichero ni de alcance.

**`bash harness/init.sh`** (tras borrar `.arnes_cache/suite_*.ok`):
- **exit 0**, sin `[KO]`;
- raíz 418 (+1 skipped), api 949, front 310 y transfer **1080** (+4);
- **COBERTURA 99,2 %** y TAMAÑO dentro de los topes.

**Árbol** limpio; lo probado, en el scratchpad.

| Punto | Resultado |
|---|---|
| T18 cumple `tasks.md` | [x] Solo se aplica al localizar por `hmores_ide`. Si el `ide` apunta a una línea `H*`, `C*` o sin hora, no cuenta como ya registrada y se sigue por `synckey` (`…r15_ide_de_una_linea_no_mensual_no_cuenta` ×3, `…r15_ide_no_mensual_pero_synckey_propia_por_synckey`). Usa `es_linea_mensual`, la misma función de toda la regla, sobre `hora_codigo`, que `lineas_registradas` lee de `auxhor.cod` (también en el lote, que delega en la misma consulta) |
| Coherencia con la relectura de R13 | [x] `_comprobar_escrito` no localiza por el `hmores_ide` guardado: relee el `ide` que se acaba de editar (sale de la traza). Esa línea es `M*` por construcción: la guarda SQL exige `LIKE 'M%'` antes de cambiarla y el `SET` pone la hora `M*` de la acción. Así que exigir `M*` ahí no añadiría nada, y no se tocó. Las insertadas se releen por `synckey`, que el criterio nuevo no toca |
| RED con traza | [x] impl §3: «4 failed, 61 deselected», con `'ya_registrado' == 'escribir'` (×3) y `('ya_registrado', 410931) == ('ya_registrado', 9001)`. Lo reproduje en una copia de HEAD **quitando la línea 570**: «4 failed, 7 passed» en `-k r15` |
| La campaña cubre el código final | [x] Recálculo puro: **627 líneas, 136 mutantes** en HEAD y en `d5d61ac` (el SHA medido), **mismo conjunto**; después de `d5d61ac` solo cambian `progress/` y `tasks.md`. Los dos mutantes nuevos de la línea 570 (`or` → `and` y quitar `not`), aplicados a mano en la copia, dan **«6 failed»** cada uno |

**Mutación.**
- Totales: 136 generados, 136 muertos, 0 supervivientes, 0 timeouts, sin
  veredicto 0, `--workers 1`.
- Duración: 946,3 s, más de 60 s, así que **no se reejecutó la campaña
  entera**; basta el recálculo y la reproducción de los dos mutantes nuevos.
- RM2: media de 7,0 s con una línea base del transfer de 22,9 s (0,31), y
  136 × 7,0 ≈ 946. Sin salto de orden de magnitud; coste por mutante de 7 s.
- RM3, RM5 y RM6: sin equivalentes declarados y sin guardas quitadas (T18
  añade una).

**Observación O6** (la corrige el líder **antes del `done`**, no bloquea
esta review): `current.md` se contradice sobre **quién ejecuta T15**.
- Dice «del humano» en la línea 15 («Falta T15 (MANUAL del humano)»), en
  la 26, en la 79 y en la 269.
- Dice «la hace el líder» en la línea 33, que además deja la preparación
  (escribir en Sigrid fuera del transfer) consultada al humano.
- La cabecera sigue en «Review pasada 2: APROBADO».

Cuando el humano conteste, hay que unificar los cinco sitios y la cabecera,
y anotar en T15 su resultado real.

## Checkpoints (estado tras la pasada 3)

- **C1** [x] init.sh con exit 0; [x] existen los ficheros base.
- **C2** [x] una sola `in_progress` (F-058 está en `pending`); [x] la rama
  es la de la feature; [x] `current.md` describe la sesión activa (ver O6);
  history: N/A hasta `done`.
- **C3** [x] Hexagonal (O1 en la capa de aplicación, con precedente).
  [x] Primera línea con la ruta. [x] Sin prints de debug, secretos ni
  dependencias. [x] Trampas: escala sobre 1, postventa intacta, solo
  escribe el transfer, con `synckey` y modo pruebas. [x] Estilo.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1-R19, con T18 dentro de R15, tienen tests `test_f051_rN_*` en
  verde. R20 lo cubre el test R6; R21, `test_f002_fuente_unica`; R22 es
  documental; R23 = T15. [x] Sin red ni BBDD. [x] T15 con su comando exacto.
- **C4 bis**
  - [x] rigor declarado;
  - [x] RED de T18 con traza, reproducida;
  - [x] cobertura `[OK]`;
  - [x] totales recalculados;
  - [x] muertos comprobados por recálculo y por los dos mutantes nuevos;
  - [x] coste por mutante mayor de 1 s;
  - [x] sin «CAMPAÑA NO VÁLIDA»;
  - [x] RM1, RM2, RM5 y RM6;
  - [x] 0 supervivientes;
  - [x] Evidencias con workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T1-T14, T17 y T18 `[x]` con commits `F-051 Tn:`. T15 y T16
  siguen abiertas, como prevé la spec: bloquean el `done`, no esta review.
  [x] Sin artefactos. [x] `features.json` en `in_progress`.

## Pasada 2 (2026-10-21), en resumen: APROBADO

Incremental desde `c070244`. Los cuatro cambios de la pasada 1 quedaron
resueltos:
- test de la frontera de R13 (`d807cce`), reproducido: «1 passed» con el
  original y «1 failed» con el mutante `>=` → `>`;
- 3.ª campaña sobre `7a5f801`: 134 mutantes y 0 supervivientes, con el
  conjunto idéntico al de HEAD;
- `current.md` podado y T15 una sola vez;
- formato de la línea 568 y primera línea de `impl_F-051.md`.

## Pasada 1 (2026-10-20), en resumen: RECHAZADO

Completa sobre `2c75a1c...c070244`. Todo lo pedido estaba bien, con sus
tests:
- ningún `DELETE` en el registro (`stmt_borrar_linea` solo en `limpiar`);
- la guarda del `UPDATE` completa (`ide`, `reside`, `can` y `synckey`
  leídas, 6 enlaces, `M%`, `con.est`), con `WHERE` siempre;
- si la guarda falla, `omitidas` y sin insertar;
- la `synckey` de otro sistema se conserva;
- idempotencia por `hmores_ide` con respaldo por `synckey`;
- D14 y D7;
- el log de D13 con la fila entera;
- la lista cerrada respetada;
- el front sin lógica;
- la documentación.

**Motivos del rechazo:**
1. El mutante `:1095`, declarado equivalente, moría con `can` 0 y una
   relectura de `1e-6`.
2. `current.md` desfasado.
3. Formato de la línea 568.
4. Primera línea del informe.

**Observaciones:**
- **O1:** `PREFIJO_SYNCKEY` importado de infraestructura (abierta).
- **O2:** pasó a ser T18 (hecha).
- **O3:** el aviso enseña el `ide` de la partida (abierta).
- **O4:** pasó a ser F-058.
- **O5:** resuelta al fusionar `dev`.

**Automejora propuesta (sin aplicar):** que la demostración de RM5 cubra
los **extremos del dominio** (0, máximo, nulo) que admite quien construye el
dato.
