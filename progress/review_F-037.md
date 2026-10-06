<!-- progress/review_F-037.md -->
Revisión completa (pasada 1), `3252814..ac125cb`

# F-037 · Review (reviewer, 2026-10-06)

**Veredicto: CHANGES_REQUESTED.** El código, los tests, la mutación y los docs
técnicos están bien y quedan **dados por buenos hasta `ac125cb`**. Lo que
falla es el rastro: `current.md` (a T13 le falta el comando exacto, hay líneas
caducadas y T11 no está al día) y la `acceptance` de `features.json`. La
pasada 2 solo tiene que mirar esos dos ficheros.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige RED,
cobertura ≥ 80 %, cero supervivientes y las MANUAL con su comando exacto.

## Lo que verificó el reviewer

- **init.sh**: ENTORNO LISTO (418 passed, 1 skipped; servicios verdes; 100 %).
- **Copias (1).** `git -C partes show 9b202e9:…` + `cmp` da los dos ficheros
  **idénticos**. La rama de `partes` avanzó hasta `9ea7c59`, pero
  `git log 9b202e9..rama -- <copias>` sale vacío y su árbol está limpio. El
  test anti-divergencia es útil: compara con el commit (ve ediciones aquí) y con
  la rama (ve cambios allí), y hace `skip` con motivo si falta el repo.
  **Aviso:** la DA11 de `partes` v5 cambiará la cabecera de las copias; eso
  pone en rojo `…ref_vigilada` y habrá que recopiar (design §12).
- **SQL = `partes` (2).** `horas_de_recursos`, `cuentas_de_centro`,
  `partidas_de_lineas`, `partes_del_periodo` y `siguiente_cod_pt` son
  literalmente los de `partes` F-031.
  Alta D17: condiciones **fuera del agregado** (`(SELECT ISNULL(MAX(ide),0)+1
  AS n …) x WHERE NOT EXISTS …`), seis primeros parámetros en su orden, `hmo`
  por `cod`+`tip`+`emp` con `NOT EXISTS`; SQLite prueba trampa, código ocupado,
  En registro previo y `emp`. Lectura y escritura en `ruesma`; el alta es un
  solo lote = una transacción (`sigrid_api.md` §7.3).
- **Pipeline (2, 3).** Cerrado = `cod in cerrados` de `elegir_parte` (copia);
  `Parte <obra>`; relectura, un reintento y `RuntimeError` antes de insertar;
  duplicados y conflictos contra todo el periodo, el cerrado prevalece con
  `caa_*` vacíos y `pisar` nunca borra en él (se omite antes de ser
  conflicto); `ejecutar` repite `preflight`; cuenta recurso > defecto >
  partida `CI`/`CD`, 0 y aviso según R5; nada toca `asi/asa/apu/apa` ni
  `UPDATE con`.
- **Tests anteriores (4).** `git diff 3252814..HEAD -- '*tests*'` solo trae los
  dobles de `conftest.py`/`test_pipeline_offline.py` y la ancla de `test_f002`.
  **Ningún `assert` tocado.**
- **Mutación (6).** El recálculo puro (`harness.alcance` + `generar_mutantes`)
  da 576 líneas y **85 mutantes**; en las copias, 209 líneas y **25**: coincide
  con los informes. **Campaña no reejecutada** (423,1 s y 107,0 s, más de
  60 s). RM4 en copia del scratchpad (base `test_f037_*` 152/152, copias en
  `skip`): 4 mutantes reproducidos, todos con fallos nuevos en `test_f037_*`:
  `cuenta_analitica:96 frozen=True→False`, `pipeline:280 intento == 0→== 1`,
  `estado_parte:29 reverse=True→False`, `cliente:432 caaide: int = 0→1`.
  `git status` limpio.
- **Docs (7).** ARCHITECTURE §16 y los alcances de conflicto, capacidad y
  sin partida, correctos. INTEGRACION está **literal** en `azure-apps`
  `5416cd1`. «`partes` está avisado» (D17) **ya es cierto**: `partes`
  `9ea7c59` (spec v5, R40-R49) adopta nuestro SQL y lo anota en su
  `current.md`. **No bloquea.** Antes del `done` falta avisarles del hueco de
  `OrigenSubcuenta`.

## Desviaciones del informe §3 (5): las tres, correctas

1. **`partes_existentes` se queda.** La usa `prueba_escritura_porcentajes.py:119`
   y design §4 prohíbe tocar ese script; §3 contradecía a §4. El implementer se
   quedó con el lado que no cambia comportamiento y lo declaró: no hacía falta
   parar.
2. **Se retira `sin_partida` al omitir por `parte_cerrado`.** Es una
   consecuencia de R13: no se confirma lo que no se escribe, y evita el doble
   UPDATE en `omitidas`. Tiene test (`r13_sin_partida_que_choca…`).
3. **SQLite en memoria** (stdlib): es un fixture, no red ni BBDD del sistema
   (CONVENTIONS l. 60). Solo se quitan las pistas de bloqueo y `ISNULL` pasa a
   `IFNULL`.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] rama · **[ ] `current.md` con restos
  caducados** (cambio 2) · [x] history.
- **C3** [x] hexagonal (la infra usa `indexar_cuentas`, igual que `partes`; el
  dominio no importa nada nuevo) · [x] primera línea con ruta en los 13 `.py` ·
  [x] sin print, TODO, secretos ni dependencias nuevas · [x] trampas: escala
  sobre 1 intacta, postventa con su centro (r4), solo escribe el transfer, con
  `synckey` y `MAX(ide)+1` bajo bloqueo.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad (tabla) · [x] sin red ni BBDD (ver desviación 3; el
  test de copias lee un repo local) · **[ ] MANUAL con comando exacto**: T12
  sí lo tiene, **T13 no** (cambio 1).
- **C4 bis** [x] rigor · [x] RED con trazas reales (T1, T2, T4-T8) ·
  [x] cobertura 100 % · [x] totales recalculados · [x] muertos: >60 s, recálculo
  y RM4 · [x] coste por mutante 5,0 s y 4,3 s, W=1 · [x] sin «CAMPAÑA NO
  VÁLIDA» y 0 base rota · [x] **RM1**: medido en `40b9feb`, y de ahí a HEAD
  solo cambian `progress/` y `tasks.md` · [x] **RM2**: 85×5,0≈423,1 y
  25×4,3≈107,0, media ≥ base/10 · RM3: ningún equivalente entre los 85 ·
  **RM5 N/A**: no hay equivalentes declarados · **RM6 N/A**: T10 solo añade
  tests y dos anotaciones de tipo, no quita ninguna guarda · campaña manual
  N/A · [x] 0 supervivientes · [x] «Evidencias» completa, W=1.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1-T10, T14 y T15 `[x]` con commit; T11-T13 son MANUAL,
  pendientes antes del `done` · [x] sin artefactos · **[ ] `features.json`**:
  la `acceptance` contradice la spec (cambio 3).

## Cobertura requisito → test (`test_f037_…`)

| Req. | Tests |
|---|---|
| R1-R8 | `r1_*` (4), `r2_*`/`r3_*` (+ reglas), `r4_*` (5), `r5_*` (3), `r6_*` (3), `r7_*` (4), `r8_…sin_cuaide` |
| R9-R14 | `r9_*` (2), `r10_*` (4, + reglas), `r11_d17_*` y `d17_*` (SQLite), `r12_…cerrado`, `r13_*` (6; R14 en `…prevalece` y `…en_registro_es_conflicto`) |
| R15-R19 | `r15_el_contrato_http…`, `r16_*`, `r17_*` (2), `test_f002_fuente_unica.py`, `test_f008_infra_sin_secretos.py` + diff |
| R20-R21 | MANUAL T12 y T13 (pendientes) |

## Cambios requeridos

1. **`progress/current.md`, MANUAL T13** (hoy «pasos en `tasks.md`»): comandos
   exactos con su resultado esperado y la autorización como condición previa:
   el `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/ejecutar"
   -H "Content-Type: application/json" -d "{\"trabajador_ide\": <ide>}"` (o la vía
   que se use), el `SELECT … WHERE hmores.synckey = 'porcentajes:<id>'` por
   `/api/sql/read` y `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar`.
2. **`progress/current.md`, poda.** En «Lo siguiente» sigue poniendo «Ahora
   **F-037** (…, en spec)». En la sección F-037 hay viñetas superadas que se
   leen como vigentes: «Espera al humano / Juan Romero con D1-D11 abiertas»,
   «Abiertas para el humano: D8…D15» y «Pendiente del humano: D16…»
   (l. ~51-81). Hay que resumirlas o marcarlas como resueltas.
3. **`harness/features.json`, `acceptance` de F-037.** Dice «El transfer genera
   el asiento con su desglose analítico» y «decididas … la 6XX, la
   contrapartida…», y eso contradice D1 = A (solo se rellena `hmores.caaide`;
   el ANA lo genera Sigrid). Hay que alinearla con la spec y regenerar
   `BACKLOG.md`.
4. **`progress/current.md`, T11.** Anotar tres cosas: `partes` ya recogió D17
   (`9ea7c59`); falta avisarles de `OrigenSubcuenta`; y su DA11 pondrá en rojo
   `test_f037_copias_partes.py::…ref_vigilada`, así que habrá que recopiar y
   mover `COMMIT_COPIADO`.

## Observaciones no bloqueantes

- La acción omitida por `parte_cerrado` conserva en `aviso` el texto de cuenta
  del paso 4 bis aunque vacía `caa_*` (cosmético; contrastar con `partes`).

## Automejora propuesta (no aplicada)

- `reviewer.md`: ante copias entre repositorios, mirar también si la rama
  vigilada tiene **decisiones abiertas que cambiarán las copias** (aquí, la
  DA11 de `partes`). El test solo ve commits.
