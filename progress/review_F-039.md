<!-- progress/review_F-039.md -->
Revisión completa (pasada 1), diff de F-039 `f7cc4e9..3b531ac` (= `8a012d7..HEAD` sin los merges de dev)

# F-039 · Review (reviewer, 2026-10-06)

**Veredicto: CHANGES_REQUESTED** (solo por el rastro de `progress/current.md`).
El código, los tests, la mutación y los docs quedan dados por buenos hasta
`3b531ac`: la pasada 2 puede ser incremental y limitarse a `current.md`.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 %, campaña completa con cero supervivientes y las MANUAL con
comando exacto y resultado.

## Lo verificado

- **`bash harness/init.sh`**: `ENTORNO LISTO`, exit 0. Raíz 418 passed/1 skipped;
  api, front y transfer en verde; `PUERTA COBERTURA` 100 % (181/181);
  `PUERTA TAMAÑO` dentro (144/150, 232/250, 220/220).
- **Límite de servicio (punto 1).** El universo VAR solo lo calcula el transfer
  (`universo_var.py`). El endpoint y el preflight usan la misma carga
  (`cargar_catalogo_var`) y la misma consulta (`partida_var_de`). La api lo pide
  una vez en `preparar_obras`, que comparten el step y el preview. La api no
  conoce «VAR» ni «29» (el código está en el ajuste del transfer). El front solo
  pinta `partida_metodo === "var"`, sin literales (lo vigila un test).
- **Registro VAR (punto 2).** La rama VAR del pipeline va antes del override. Lo
  que se omite: postventa (sin leer la VAR), la línea sin universo, la de otra
  obra y la partida fuera del universo; cada omisión lleva su motivo y no da
  aviso de «sin partida». En cualquier otro caso queda `paride` fijo con
  `metodo var` y `continue`, sin cascada. La cuenta sale del paso 4 bis en el
  centro del destino (`caaide` 91001 en el test de ejecutar; en pruebas, `0404`).
  En la api, `_payloads` agrupa las líneas por `registro_obra_ide`, manda
  `var_paride` y no deja pasar el override.
- **6+ dígitos (punto 3).** `tiene_digitos_seguidos` (regex `[0-9]{n}`, con
  `n<=0` no hay filtro) se aplica antes de pedir ningún universo. La obra
  descartada ya guardada pierde `activa` y `admite_postventa` en
  `sincronizar` (no llega), y sus líneas se quedan como no ofrecibles y se
  registran como hoy (D5).
- **Columnas e `ide` negativo (punto 4).** Las tres columnas son nulables y sin
  default solo en el ORM, y `esquema` deriva el ALTER (test r18). He buscado
  dónde podía romper el `ide` negativo y no hay nada: ni `gt=0`, ni
  `PositiveInt`, ni `> 0` sobre el `ide` de la obra en schemas, rutas, casos de
  uso o `app.js`. En el front, las claves son `${obra_ide}|${pv}` y el
  `data-ide` es el del trabajador. El FK de `asignacion.obra_ide` no impone
  signo.
- **Tests anteriores cambiados (punto 5).** `git diff f7cc4e9..HEAD -- '*tests*'`:
  solo `conftest.UniversoFalso` (+`universo_var`), las `_fila` de f022, f024 y
  f026 (+3 atributos `None`) y `ANCLAS` de f002 (+2). Es exactamente la tabla
  de design §7.1 y la del informe §3, y ningún assert se debilita.
  `test_f037_copias_partes.py` viene de dev (`6f7182d`).
- **Docs (punto 7).** En `ARCHITECTURE` están las reglas 17 `#regla-var` y 18
  `#regla-seis-digitos`, la lista de anclas y la tabla `obra`. `INTEGRACION`
  tiene la cabecera, §3 (ajustes), §5 (endpoint) y §7 (cinco filas propias y
  una ajena, con el orden transfer → api → front). `azure-apps` `f01156f`
  copia literal esas piezas y el árbol de `azure-apps` está limpio. El README
  del transfer remite a la ancla.
- **Script MANUAL.** `scripts/verif_f039_var.ps1` no contiene «ejecutar» y solo
  apunta a `127.0.0.1`.

## Mutación (C4 bis, RM1-RM6)

- **Recálculo puro** con `harness.alcance` y `generar_mutantes`: 18 ficheros,
  495 líneas y **60 mutantes**, igual que el informe.
- **Campaña no reejecutada**: 1274,4 s según el informe (pasa de 60 s).
- **RM1.** SHA medido `6ab6588`. Desde ahí ningún fichero del alcance ha
  cambiado. `e69ff2a` solo retoca dos tests (`Decimal(30)` frente a
  `Decimal("30")`, y unos paréntesis) y `sigrid_write_client.py` viene de dev,
  fuera del alcance (merge-base `f7cc4e9`).
- **RM2.** Media 21,2 s con 1 worker. 60 × 21,2 = 1272 s, que cuadra con el
  total. Líneas base: api 37,8 s y transfer 14,0 s. Ningún salto de orden de
  magnitud.
- **RM3.** He repasado los 60 y no hay ningún equivalente dado por muerto:
  cada `or→and`, cada `frozen` y cada default es observable y tiene su test.
- **RM4.** He reproducido mutantes sobre una copia (`git archive`) en el
  scratchpad, con la `.venv` de cada servicio, y han muerto todos:
  - #47 `numero >= desde`→`>` (25 fallos);
  - #52 `!=`→`==` en la obra VAR (30 fallos);
  - #2 `normal and not`→`or not` (13 fallos);
  - #17 default `0`→`1` en `use_cases` (6 fallos).
  #2 y #17 son los dos que la 1.ª campaña dio por supervivientes.
- **Mutantes a mano en `registro_sigrid.py`**, donde el generador no produce
  ninguno: `elif overrides`→`if overrides` (1 fallo, r20 override) y la
  agrupación forzada a la obra propia (3 fallos, r20). Los dos mueren.
- **RM5:** N/A, porque no se declara ningún equivalente (0 supervivientes).
- **RM6:** N/A, porque T11 solo añade tests (`6ab6588`) y no quita ninguna
  guarda.
- El informe no trae «⚠ CAMPAÑA NO VÁLIDA» y «Sin veredicto» está a 0.
- El árbol queda limpio (`git status` vacío).

## Checkpoints

- **C1** [x] init.sh con exit 0 · [x] ficheros base.
- **C2** [x] una sola feature `in_progress` · [x] rama `feature/F-039-…` ·
  **[ ] `current.md` describe solo la sesión activa**: tiene restos y
  contradicciones (cambio 1) · [x] las `done` están en `history.md`.
- **C3** [x] hexagonal (`domain/obras.py`, `models` y `ports` puros; el
  `TransferClient` en infrastructure) · [x] primera línea con la ruta (el
  `.ps1` con BOM) · [x] sin prints, TODOs ni secretos, y sin dependencias
  nuevas · [x] las tres trampas: la escala va sobre 1 (test r20 con 0,4); la
  postventa con `var_paride` se omite y no se trata como normal; solo escribe
  el transfer, con `synckey` y en modo pruebas (R8).
- **C3 bis** N/A: la feature no toca `docs/referencia/`.
- **C4** [x] todos los requisitos tienen test (tabla abajo) · [x] sin red ni
  BBDD (dobles, `_SesionRepo`, `TestClient`) · **[ ] MANUAL con su comando
  exacto en `current.md`**: a T14 le falta el arranque y la URL (cambio 2).
- **C4 bis** [x] rigor declarado · [x] RED pegada por tarea (T1-T8, T11) ·
  [x] cobertura [OK] 100 % · [x] totales recalculados · [x] regla de los 60 s
  (no se reejecuta, ver arriba) · [x] coste por mutante 21,2 s > 1 s · [x] sin
  cabecera de campaña no válida · [x] RM1 · [x] RM2 · N/A RM5 y RM6 (ver arriba)
  · N/A campaña manual: la automática dio 60 · [x] 0 supervivientes ·
  [x] «Evidencias» con los cuatro números y los workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1-T11 y T15 `[x]`, cada una con su commit `F-039 Tn:`. T9 es del
  líder (`f01156f`). T12-T14 son MANUAL del humano, legítimamente pendientes en
  `critico` · [x] sin artefactos sin seguimiento · [x] `features.json`
  `in_progress`.

## Cobertura requisito → test

| R | Test (todos `test_f039_…`) | R | Test |
|---|---|---|---|
| R1 | `r1_*` (7), `r1_ruta_devuelve_el_contrato` | R13 | `r13_*` (8, repo incluido) |
| R2 | `r2_*` (parametrizado: 29, 30, 100, 029, 29.1, 29A / 28, 05, CI…) | R14 | `r14_la_obra_var_se_guarda_no_activa`, `r14_…conserva_su_postventa` |
| R3 | `r3_*` (6: ausente, ambigua, vacío sin leer) | R15 | `r15_la_entrada_que_sale_del_universo_queda_inactiva` |
| R4 | `r4_*` (422 sin leer, 502) | R16 | `r16_*` (8: cliente, sync sin commit, 502 HTTP) |
| R5 | `r5_*`, `cruce_universo_y_preflight` (real y pruebas) | R17 | `r17_*` (4) |
| R6 | `r6_*` (fuera, otra obra, sin universo, postventa) | R18 | `r18_*` (3) |
| R7 | `r7_el_paride_manual_no_cambia_la_partida_var` | R19 | `r19_*` (2) |
| R8 | `r8_*` (5: pruebas, ejecutar, synckey, pisado, sobrecarga) | R20 | `r20_*` (4) |
| R9 | `r9_*` (2) | R21 | `r21_*` (Completar, PV, Excel) |
| R10 | `r10_*` (7) | R22 | front `r22_*` (3) |
| R11 | `r10_r11_el_sync_descarta…`, `r11_…queda_sin_marcas` | R23 | transfer `test_f002_fuente_unica` (`ANCLAS`) |
| R12 | `r12_el_universo_var_se_pide_una_vez…` | R24 | documental: verificado leyendo `INTEGRACION` y `azure-apps` `f01156f` |

## Cambios requeridos

1. **`progress/current.md`: podar lo que contradice el estado real.**
   - l. 12, «Primera del backlog»: F-039 tiene hoy prioridad 4.
   - l. 42-43, «F-040, spec lista … espera al humano con D1-D6»: contradice
     l. 38-41, que dice «specs de F-040 y F-041 aprobadas».
   - l. 49-51, «F-039 tercera. No hay F-041.»: F-041 existe, con prioridad 3,
     y F-039 es la cuarta.
   - l. 112-117, «Lo siguiente»: dice «F-029 espera a que el humano decida
     desplegar», pero se desplegó el 2026-10-06 según «Producción, hoy»;
     «Ahora **F-037**», pero está cerrada; y «**F-039** (spec lista)», pero
     está implementada y en review.
   - Hay que reescribirlo en el orden de `BACKLOG.md`.
2. **`progress/current.md`, MANUAL T12-T14 (l. 22-35): comando exacto
   completo.**
   - T12 y T13 no dicen cómo se arrancan los servicios. Añadir: «`python
     main.py` con la `.venv` de cada servicio en `services/dedicacion-transfer`
     y `services/dedicacion-api`, la api con `PG_HOST=localhost`».
   - T14 («además el front local») necesita el comando y la URL: «`python
     main.py` en `services/dedicacion-front` y abrir `http://127.0.0.1:8080`».
     Así lo tienen `tasks.md` T14 y el informe §5.

## Observaciones (no bloquean; que el líder las recoja)

- `registro_sigrid.py` da 0 mutantes automáticos (16 líneas en el alcance, sin
  operadores mutables). Lo cubren los dos mutantes a mano de arriba. Si el
  humano lo quiere, se puede pasar a `arnes-base` como hueco del generador.
- La 1.ª campaña dio por supervivientes a #2 y #17, que estaban muertos. Ya
  consta en el informe del implementer, con el indicio de carga de la máquina,
  para quien mantenga `harness/mutacion.py`.
- El Excel en notación científica (`1E+2%`) está fuera del alcance y ya está
  recogido en `current.md` bajo F-040.
