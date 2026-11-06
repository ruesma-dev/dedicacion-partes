<!-- progress/review_F-054.md -->
Revisión incremental desde f1a5efb (pasada 11; código aprobado hasta `5ca4838` en la 10), HEAD `e7e8bff`.

# F-054 · Review 11 (los dos cambios requeridos de la review 10)

**Veredicto: APROBADO (APPROVED).** Los dos «Cambios requeridos» de la review 10 están corregidos y
el delta no toca ni código ni tests. `init.sh` entero, sin `[KO]` (al pie).

**Rigor:** `critico` (`features.json`): RED, cobertura, mutación con 0 supervivientes, RM5 y MANUAL.
Todo eso quedó comprobado en la review 10 sobre `5ca4838` (C4 bis entero, campañas 11 y 12, dos
mutantes reproducidos según RM4). El delta es solo documentación, así que no cambia nada de eso.
Anteriores: 10 CAMBIOS solo por el rastro; 9, 8, 7, 6 y 2 APROBADAS; 5, 4 y 3 CAMBIOS solo por
`current.md`; 1 RECHAZADA.

## Delta revisado (`git diff f1a5efb..HEAD`, 3 commits, 4 ficheros)

`af14e6c`, `1b96b6f` y `e7e8bff` tocan solo `progress/current.md`, `progress/impl_F-054.md`,
`specs/F-054-sync-trae-porcentajes/design.md` y `.../tasks.md` (+14 −14).
`git diff --name-only f1a5efb..HEAD` fuera de `progress/` y `specs/`: **vacío**. No hay código ni
tests en el delta, así que lo aprobado hasta `5ca4838` sigue valiendo y no hay que repetir la campaña (RM1).

### Punto 1 (spec con la quinta regla de R48): corregido

- `tasks.md:34` (T27) añade la regla **(e)** `.zona-traer .tabla-reg { border-collapse: separate;
  border-spacing: 0; }`. Trae su motivo (retoque `083076c`: la franja de 1 px de la MANUAL del
  2026-11-06, porque con `collapse` el borde es de la rejilla y no viaja con el `thead` fijo), la
  posición (después de `.modal .tabla-reg`, misma especificidad) y por qué no hay bordes dobles.
  Coincide con `styles.css:628`.
- La lista cerrada de tests nombra `test_f054_r48_los_bordes_viajan_con_la_cabecera_sin_dobles`. La
  verificación (1) dice «reglas (a)-(e) con **exactamente** esos selectores». La (8) suma la
  «campaña 12, 12/12».
- `design.md:191-192` (§7) recoge la quinta regla en una línea.
- `impl_F-054.md:199`: «las cuatro reglas exactas (…; el retoque `083076c`, abajo, suma la quinta)».

### Punto 2 (`current.md` coherente con `manual_F-054.md`): corregido

- l. 4: cola reescrita y la historia de T27 resumida en una frase con enlace a `impl_F-054.md` §T27.
  Dice «**MANUAL de R48 HECHA el 2026-11-06 sobre `083076c`**» y «review 11 lanzada».
- l. 173 y 181: R48 dentro de T18 paso 2 consta como «**HECHO el 2026-11-06 sobre `083076c`**», y
  «Pendiente del paso 2: todo lo anterior a R48 y lo que sigue». Es lo mismo que dice `manual_F-054.md`.
- `tasks.md:25` (T18): igual, «**HECHA el 2026-11-06 sobre `083076c`** … el resto del paso 2 y los
  pasos 3 y 4 siguen pendientes».
- l. 96 («Siguiente:»), 99 (título) y 602 («Hoy (2026-11-06):») nombran «T27/R48 hecha y
  comprobada por el humano».

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados, sin pipes): ver el pie · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` (F-054) · [x] rama `feature/F-054-sync-trae-porcentajes` ·
  [x] `current.md` coherente (punto 2) · [x] history.
- **C3** [x] como en la review 10: el delta no toca código.
- **C3 bis** N/A: el delta no toca `docs/referencia/`.
- **C4** [x] R48 con tests y MANUAL hecha (review 10, sin cambios en el delta).
- **C4 bis** [x] todo como en la review 10 (RED, cobertura, campañas 11 y 12, RM1-RM6). El delta no
  cambia código, así que no hay nada nuevo que medir.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T27 describe lo que hay (punto 1) · T18-T20 `[ ]` por ser MANUAL, legítimo.

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R47 | como en las reviews 7-9 (`test_f054_*` de los tres servicios) |
| R48 | `test_f054_traer_front.py` `r48_*` · campañas manuales 11 y 12 · MANUAL (`manual_F-054.md:24`) |
| R29 | `ARCHITECTURE.md` 23, `INTEGRACION.md` §5; `azure-apps`, en T20 |
| R30, R37 | MANUAL T10 (hecha), T18 (paso 1 y la parte de R48 del paso 2, hechos), T19 |

## Pendiente para cerrar la feature (no bloquea esta review)

T18 (el resto del paso 2 y los pasos 3 y 4) y T19, del humano. T20 al desplegar (`azure-apps`).

## Automejora (propuesta de la review 10, sigue abierta)

Para `implementer.md` (y `arnes-base`): «un cambio posterior a la spec, aunque lo pida el humano en
la MANUAL, actualiza primero la tarea en `tasks.md` (qué regla, qué test, qué verificación) y
después el código». Lo que costó la review 10 fue justo eso.

## Resultado de `init.sh`

INIT_PLACEHOLDER
