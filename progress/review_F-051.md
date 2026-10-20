<!-- progress/review_F-051.md -->
Revisión incremental desde c070244 (pasada 2) hasta `3d0b738`; la pasada 1 fue completa (`2c75a1c...c070244`)

# F-051 · Review (reviewer, 2026-10-21)

**Veredicto: APROBADO.** Los cuatro cambios requeridos de la pasada 1 están
resueltos. El test nuevo mata el mutante de la frontera de R13 (lo comprobé
en una copia) y la 3.ª campaña, con **0 supervivientes**, mide exactamente
el código de HEAD.

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 %, campaña completa con 0 supervivientes, RM5 y MANUAL con
comando exacto. **Antes de `done` falta el resultado real de T15**
(humano); T16 es del líder al desplegar.

## Pasada 2 (2026-10-21)

**Delta.**
- `a06c861` fusiona `dev` (`infra/imagenes.json` y `progress/`).
- `d807cce`: el test nuevo. `7a5f801`: formato. `e51ba7b`, `d170afb`,
  `aea0bc6` y `3d0b738`: papeleo.
- Producción cambia en dos sitios sin efecto lógico: la condición del paso 6
  (`registro_pipeline.py:568-569`) partida entre paréntesis, y un docstring
  de `lecturas_lote.py`.
- Nada de lo aprobado cambia de firma, de fichero ni de alcance.

**`bash harness/init.sh`** (tras borrar `.arnes_cache/suite_*.ok`):
- **exit 0**, sin `[KO]`;
- raíz 418 passed (+1 skipped), api 949, front 310 y transfer **1076** (+1:
  el test nuevo);
- **COBERTURA 99,2 %** (253/255) y TAMAÑO dentro de los topes.

**Árbol** limpio antes y después; todo lo probado, en el scratchpad.

| Cambio requerido (pasada 1) | Estado |
|---|---|
| 1. Mutante `:1095` (ahora `:1096`) | [x] Test `test_f051_r13_editada_a_una_millonesima_de_lo_escrito_no_cuenta` (`d807cce`). **Reproducido** en una copia de HEAD del transfer: «1 passed» con el original y «1 failed» con `>=` → `>` en la línea 1096. La suite con `-x` también cae |
| 1. Campaña nueva | [x] 134 generados, 134 muertos, **0 supervivientes**, 0 timeouts, sin veredicto 0, `--workers 1`, SHA `7a5f801…`. Historial de las 3 campañas, con el equivalente reconocido como falso |
| 2. `current.md` | [x] Sin «D14-D15 abiertas» ni `[KO]` de entorno; las decisiones, como «todas cerradas». **T15 una sola vez** (líneas 64-78), con su comando exacto y «sin ejecutar». O2 y O4, en lo pendiente del humano. Ya no se pide aceptar ningún equivalente |
| 3. Línea 568 | [x] Partida; ningún fichero cambiado pasa de 99 caracteres |
| 4. `impl_F-051.md` | [x] Primera línea con la ruta. Evidencias al día: 2.753 passed, 99,2 %, 134/0, workers 1 |

**Verificación independiente de la campaña** (cálculo puro con
`harness.alcance` y `generar_mutantes`):
- **Alcance en HEAD:** 8 ficheros, **625 líneas, 134 mutantes**, igual que el
  informe. El merge-base pasa a `708236f` tras fusionar `dev`.
- **RM1:** los mutantes de `7a5f801` (el SHA medido) y los de HEAD son **el
  mismo conjunto**; después de `7a5f801` solo cambia `progress/`. La campaña
  cubre el código final.
- **Duración:** 1635,8 s, más de 60 s: **campaña no reejecutada**. Vale el
  recálculo puro, las reglas RM y la reproducción del mutante decisivo.
- **RM2:** líneas base de 47,4 s (transfer) y 86,9 s (api); media 12,2 s;
  134 × 12,2 ≈ 1635. La media es 0,26 veces la línea base del transfer, sin
  salto de orden de magnitud (lo explica `-x`). Coste por mutante: 12,2 s.
- **RM3:** el único equivalente que se declaró ya no lo es, y lo mata un test
  que sí lo distingue.
- **RM5:** no queda ningún equivalente que muestrear.
- **RM6:** no se quitó ninguna guarda.

**Observaciones.** O2 y O4 están consultadas al humano y no bloquean. O1 y O3
siguen como observaciones; O5 quedó resuelta con la fusión. Nueva: la línea
254 de `current.md` dice «F-051 (en curso: correcciones de la review 1)»;
conviene actualizarla al cerrar.

## Checkpoints (estado tras la pasada 2)

- **C1** [x] init.sh termina con exit 0; [x] están los ficheros base.
- **C2**
  - [x] una sola `in_progress`;
  - [x] la rama es la de la feature;
  - [x] `current.md` sin restos desfasados;
  - history: N/A hasta `done` (lo escribe el líder al cerrar).
- **C3**
  - [x] el dominio no importa infraestructura (O1 está en la capa de
    aplicación, con precedente);
  - [x] primera línea con la ruta;
  - [x] sin prints de debug (los `print` son la salida del script CLI), sin
    secretos ni dependencias nuevas;
  - [x] trampas: escala sobre 1, postventa intacta, solo escribe el
    transfer, con `synckey` y modo pruebas;
  - [x] estilo.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4**
  - [x] R1-R19 tienen tests `test_f051_rN_*` en verde;
  - R20 lo cubre el test R6, y `limpiar` no cambia;
  - R21: `test_f002_fuente_unica`;
  - R22 es documental, verificado leyendo;
  - R23 = T15;
  - [x] sin red ni BBDD;
  - [x] T15 en `current.md` con su comando exacto.
- **C4 bis**
  - [x] `rigor` declarado;
  - [x] fase RED con trazas reales (pasada 1);
  - [x] cobertura `[OK]`;
  - [x] totales recalculados;
  - [x] muertos: campaña de más de 60 s, comprobados por recálculo, RM y la
    reproducción del mutante decisivo;
  - [x] coste por mutante mayor de 1 s;
  - [x] sin «CAMPAÑA NO VÁLIDA»;
  - [x] RM1, RM2, RM5 (sin equivalentes) y RM6;
  - [x] 0 supervivientes;
  - [x] Evidencias con workers;
  - ningún N/A sin motivo.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5**
  - [x] T1-T14 y T17 `[x]` con commits `F-051 Tn:`;
  - T15 (humano) y T16 (líder, al desplegar) siguen abiertas, como prevé la
    spec: bloquean el `done`, no esta review;
  - [x] sin artefactos;
  - [x] `features.json` en `in_progress`.

## Pasada 1 (2026-10-20), en resumen: RECHAZADO

Revisión completa de `2c75a1c...c070244`. Todo lo que pidió el líder estaba
bien, con sus tests:
- ningún `DELETE` en el registro (`stmt_borrar_linea` solo en `limpiar`);
- guarda del `UPDATE` completa (`ide`, `reside`, `can` y `synckey` leídas,
  6 enlaces a 0, `M%`, `con.est`), con `WHERE` siempre;
- si la guarda falla, `omitidas` y sin insertar; R12 se comprueba antes de
  dar de alta partes;
- la `synckey` de otro sistema se conserva;
- idempotencia por `hmores_ide`, con respaldo por `synckey`, en una lectura;
- D14 (uno edita y los demás a 0) y D7 (postventa, misma partida);
- log de D13 con la fila entera;
- lista cerrada respetada (opciones A y B);
- front sin lógica;
- `#regla-cero` e `INTEGRACION` §1, §5 y §7.

**Motivos del rechazo:** (1) el mutante `:1095` se daba por equivalente y
moría con `can` 0 y una relectura de `1e-6`; (2) `current.md` daba D14-D15
por abiertas y traía T15 dos veces; (3) formato de la línea 568; (4) primera
línea de `impl_F-051.md`. **Observaciones:** O1, `PREFIJO_SYNCKEY` importado
de infraestructura; O2, línea `M*` al localizar por `hmores_ide` (humano);
O3, el aviso enseña el `ide` de la partida; O4, porcentaje < 0,00005 da
`can` 0 (humano); O5, `dev` había avanzado (ya fusionado).

**Automejora propuesta (sin aplicar):** que la demostración de RM5 cubra los
**extremos del dominio** (0, máximo, nulo) que admite quien construye el
dato.
