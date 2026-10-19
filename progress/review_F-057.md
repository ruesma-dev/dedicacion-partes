<!-- progress/review_F-057.md -->
Revisión completa (pasada 1) · `dev...acb6a01` (base `41d2885`, primer commit `0b48c9e`)

# F-057 · Review

## Veredicto: **APROBADO** (APPROVED)

**Nivel de rigor:** `estandar` (declarado en `features.json`). Exige C1–C5, C4
con tests trazables, fase RED, cobertura de lo cambiado ≥ 80 % y campaña de
mutación con supervivientes analizados (sin la exigencia de cero). `sdd: false`:
el contrato son los 5 `acceptance` y el plan de `progress/current.md` («F-057 ·
plan aprobado»), con D1 (triples) y D2 (`encolar()` → `(en_curso, pendientes)`)
aceptadas por el líder.

`bash harness/init.sh` (caché `suite_*.ok` borrada antes): **ENTORNO LISTO**.
Raíz 418 passed / 1 skipped; api 943; front 305; transfer 932. `PUERTA
COBERTURA` [OK] 100,0 % (30/30). `PUERTA TAMAÑO` [OK] (impl 176/220). Árbol
limpio antes y después de la review.

## Lo pedido expresamente por el líder

- **La regla de «pendiente» sale de la cola que encola.** `pendientes()` lee
  `_en_cola`, la misma memoria que llena `_lanzar`; no hay segunda regla (D3).
  `en_curso` pasa a `bool(pendientes(...))` y `estado()` lee ambos de la misma
  foto. El front no replica nada: `htmlPartida` mira solo
  `l.propuesta_pendiente` y `aplicarPendientes` casa por identidad
  `(trabajador, obra, es_postventa)` sin mirar partida, fija ni propuesta
  (estáticos `test_f057_r2_*` lo fijan). [x]
- **Todas las respuestas con fila marcan tras encolar.** Grep de
  `a_trabajador_out` en producción: cuadrante, `PUT …/asignaciones`, `PUT
  …/partida`, `POST …/deshacer` y F8; las cinco llaman a `_encolar` antes de
  construir `LineaOut`. Copiar mes y completar no devuelven líneas (toman `[0]`
  y el front recarga el cuadrante). En el front, las cuatro escrituras pasan por
  `aplicarFila`, que sustituye la fila entera por la de la api. [x]
- **`docs/INTEGRACION.md`** describe `propuesta_pendiente`, las cuatro
  escrituras, `pendientes: [{trabajador_ide, obra_ide, es_postventa}]` y que
  `en_curso` solo gobierna la consulta. `ARCHITECTURE.md` alineado. [x]
- **No cambia qué se encola ni cuándo.** El cuerpo de `_lanzar` (filtro
  postventa/fija/elegida/propuesta, `_sin_propuesta`, `submit`) está intacto;
  solo cambia el retorno. `lanzar()` = `encolar()[0]`, y su único llamador de
  producción (`tras_sync`) ignora el retorno. `_calcular` guarda la propuesta
  y saca de la cola en el `finally`, así que no hay ventana «ni pendiente ni
  con propuesta» que deje una línea en «automática» con el sondeo parado. [x]

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base.
**C2** [x] una sola `in_progress` (F-057) · [x] rama `feature/F-057-…` ·
[x] `current.md` con cabecera de F-057 y secciones permanentes del proyecto ·
[x] toda `done` en `history.md` (comprobado por script).
**C3** [x] hexagonal: regla en `application/`, marcado en `interface_adapters`
(schemas), front solo pinta · [x] primera línea con ruta en los ficheros nuevos
· [x] sin `print`/`console.log`/TODO (el grep solo casa «TODO el periodo» en un
docstring), sin secretos, sin dependencias nuevas · [x] trampas de dominio: no
hay porcentajes ni escritura en Sigrid; **postventa** tratada por identidad
completa (D1) y probada (`…la_postventa_de_la_misma_obra_no_es_pendiente`).
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] cada `acceptance` con tests (tabla abajo), todos verdes · [x] sin red
ni BBDD (UoW falsa, ejecutor retenido, `TestClient` sobre contenedor falso,
`node` local) · [x] MANUAL listada con comando exacto en `current.md` y
**cumplida** por el líder con resultado real (09/2026 y 10/2026, BBDD local).
**C4 bis** — ver sección propia. Todo [x] o N/A justificado.
**C4 ter** N/A: el diff no toca rutas sensibles (init.sh no las señaló).
**C5** [x] sin `tasks.md` (`sdd=false`): commits `F-057 T1..T4` + dos de rastro
del líder · [x] sin artefactos sin trackear · [x] `features.json` en
`in_progress` (el líder lo cierra tras este veredicto).

## Cobertura acceptance → tests

| # | Criterio | Tests |
|---|---|---|
| 1 | postventa / «sin propuesta» ⇒ «automática»; encolada ⇒ «buscando» hasta su propuesta, sin recargar | front `test_f057_r1_buscando_solo_si_la_linea_es_pendiente` (5 casos), `…_cada_consulta_actualiza_las_marcas_y_repinta`, `…_la_propuesta_y_la_elegida_mandan…`; api `…_de_punta_a_punta_con_la_cola_real`; MANUAL del líder |
| 2 | la api decide con la regla de encolar; el front solo pinta | api `test_f057_r2_encolada_es_pendiente_y_las_demas_no`, `…_las_escrituras_marcan_la_fila_tras_encolar` (×4), `…_get_propuestas_publica_pendientes`; front `test_f057_r2_html_partida_no_mira_el_global…`, `…_aplicar_pendientes_solo_casa_identidades` |
| 3 | api: encolada, en cálculo, postventa, «sin propuesta», elegida, fija | `…_encolada_es_pendiente…` (encolada, postventa, elegida, fija, guardada), `…_en_calculo_sigue_pendiente…`, `…_en_la_memoria_sin_propuesta_no_es_pendiente` |
| 4 | MANUAL navegador local | Cumplida por el líder (`current.md`): 09/2026 4 «buscando» → propuesta a 5,3 s; 10/2026 postventa 3 «automática», 10 «buscando» → 0 a 3,3 s |
| 5 | APROBADO + init.sh verde | este informe; init.sh arriba |

## C4 bis — rigor estándar

- [x] `rigor: estandar` declarado.
- [x] **Fase RED** con salida real: api `19 failed` (`AttributeError … no
  attribute 'encolar'`, `KeyError: 'propuesta_pendiente'`, `extra_forbidden`) y
  front `14 failed` (`no existe la función aplicarPendientes`), más la traza del
  defecto con el `htmlPartida` de `dev` (postventa ⇒ «buscando partida…»).
- [x] **Cobertura** [OK] 100,0 % (30/30).
- [x] **Mutación, recálculo independiente** (`alcance_de_feature("F-057")` +
  `generar_mutantes`, cálculo puro): **3 ficheros, 90 líneas, 11 mutantes**
  (7 + 3 + 1), igual que el informe. El superviviente existe tal cual:
  `schemas.py:97` `booleano` `= False` → `= True`.
- [x] **Campaña no reejecutada: 407,2 s según el informe** (> 60 s); vale
  recálculo puro + RM1–RM6.
- [x] Coste por mutante: 407,2 × 1 ÷ 11 = 37 s (≫ 1 s).
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base
  declarada (51,9 s).
- [x] **RM1**: SHA medido `1258c98…`; `1258c98..HEAD` solo toca `progress/`
  (4 ficheros): el alcance medido es el revisado.
- [x] **RM2**: media 37,0 s vs base 51,9 s, W = 1 (no hay salto de orden de
  magnitud; por debajo de la base por `-x`, 10/11 muertos); 11 × 37,0 = 407 s.
- [x] **RM3**: ningún muerto es equivalente. Los diez cambian el resultado
  observable (índices de la tupla, filtro de periodo, `es_postventa`, valores de
  error) o el contrato de `lanzar()`/`encolar()` (bool frente a frozenset;
  en `routes.py:217/414` pydantic rechaza el frozenset como `bool`).
- RM4 no necesaria: ningún veredicto dudoso.
- [x] **RM5** N/A por nivel (`estandar`: basta la justificación escrita, que
  existe y es correcta: el único `LineaOut(` de producción pasa siempre el
  valor explícito).
- [x] **RM6** N/A: no se quitó ninguna guarda ni código defensivo.
- [x] **Campaña manual JS** (13 filas con texto exacto y nº de fallos):
  reproducidas **tres** al pie de la letra sobre una copia del front en el
  scratchpad (base 52 passed): **J03** 1 fallo, **J13** 1 fallo, **J07** 4
  fallos; coinciden con la tabla.
- [x] Supervivientes con análisis completo (ninguno `PENDIENTE`).
- [x] «Evidencias» con los cuatro números y `Workers: 1`.

## Observaciones (no bloqueantes; el líder las recoge, no «anotado»)

1. **`azure-apps/dedicacion.md`** describe el contrato de F-055
   (`propuestas_en_curso`, `GET …/propuestas`): al desplegar hay que añadir
   `propuesta_pendiente` y `pendientes`. Ya consta en `current.md` como
   «azure-apps pendiente»; que no se pierda al cerrar.
2. **Orden de despliegue api → front** (impl): un front nuevo contra una api
   vieja diría «automática» en todo durante la ventana. Llevarlo a la nota de
   despliegue.
3. **Defecto posible de `harness/mutacion_paralela.py`** (4 supervivientes
   falsos en la 2.ª tanda de workers). Ya en «Lo que espera al humano»; si se
   confirma, es arnés genérico ⇒ ficha y portado a `arnes-base`. Hasta entonces
   conviene `--workers 1` cuando la paralela dé supervivientes en tandas.
4. D3 aceptada: una línea cuya partida se elige durante el cálculo sigue
   `propuesta_pendiente` hasta acabar la tarea, invisible porque la elegida se
   pinta antes. Sin acción.

## Automejora propuesta (para el humano, no aplicada)

- `CHECKPOINTS.md` C4, tercer punto: dice «MANUAL … pendientes de que el humano
  las ejecute», pero en este proyecto el líder las cumple a menudo antes de la
  review (F-055, F-056, F-057). Propuesta: «listadas con su comando exacto y,
  si ya se ejecutaron, con quién, cuándo y el resultado real». Vale para
  cualquier proyecto ⇒ `arnes-base`.
