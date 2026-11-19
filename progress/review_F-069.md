<!-- progress/review_F-069.md -->
Revisión completa (pasada 1), principal, sobre `ed7c212` (`git diff 5381243...HEAD`, 60 ficheros).

# F-069 · Review 1 (principal)

**Veredicto: CAMBIOS REQUERIDOS (CHANGES_REQUESTED).** Defecto de producto contra D11: una casilla
«copiado, sin revisar» deja de estarlo al revisar **otra** del mismo trabajador, y se registra en
Sigrid sin revisar (cambio 1). Faltan además la RED de tres requisitos centrales y hay incoherencias
de rastro (lista completa abajo). Bien: reparto e importe del transfer, `tex`, contrato, copia,
deshacer, lectura de Sigrid y compatibilidad entre versiones.

**Rigor:** `critico` (`features.json`): RED en los centrales, cobertura ≥ 90 %, mutación con 0
supervivientes en la muestra (uno por línea, 60 %, [100, 300]) y MANUAL con su comando. Mutación y
RM1-RM7: **pendiente: pasada de evidencias** (T13/T18). Capa e2e N/A.

## Checkpoints

- **C1** [x] `ARNES_SIN_CACHE=1 bash harness/init.sh` entero, suites en verde (pie). [x] Ficheros del arnés.
- **C2** [x] Una sola activa (F-069 `in_review`), rama `feature/F-069-importe-caja-km`, orden respetado,
  history. [ ] `current.md` con afirmaciones falsas hoy (cambio 6).
- **C3** [x] Hexagonal: `domain/importes.py` puro (solo `domain.*`), repositorios en `infrastructure/`.
  [x] Ruta en la 1.ª línea de los 11 nuevos; sin `print`/`TODO`/secretos (grep del diff).
  [x] Escala: `can` sobre 1, caja `can` 1.0; `es_postventa` en la clave de la caja y del `PUT`; solo
  escribe el transfer, con `synckey`, sin `DELETE`. [ ] Límite de servicio: `MARCA_PRUEBAS` duplicada
  en la api (cambio 3). [x] **El front no decide qué se registra**: pinta `tot`/`pre`/`km` del
  transfer y solo cambia coma por punto (lo inválido, 422 de la api). Pero por el cambio 1 el front sí
  influye: manda casillas que no cambiaron.
- **C3 bis** N/A: no toca `docs/referencia/`. **C3 ter** [x] D10 (Juan Romero) y D11-D16 con fecha y cita;
  la interpretación, separada («Yo recomendaba B…»).
- **C3 quater** pendiente de T17 al desplegar (como F-054 T20), listado con contenido en `current.md` l. 83.
- **C4** [x] R1-R32 con `test_f069_rN_*` en verde, salvo R30 (cambio 5). [x] Sin red ni BBDD.
  [x] MANUAL T16 con comando y resultado esperado (`current.md` l. 76-82), le falta un paso (cambio 4).
  [x] Dobles: no hay puerta automática en este repo; cruzados a mano los métodos nuevos
  (`lineas_por_synckey_del_periodo`, `guardar_subfila_importe`, `poner_comentario`, `registradas`,
  `ImporteRepository`): existen en la clase real con la misma firma.
- **C4 bis** [x] Nivel declarado. [ ] **Fase RED**: traza en T1-T3, T5 y T14; **no** en R15 (decide la
  `cantidad` y el `copiado` que recibe el transfer), R8 (marca `copiado` al copiar) ni R32 (sobrescribe
  datos del usuario con Sigrid): en `critico` son centrales y la mutación no sustituye la RED (cambio 2).
  [x] Cobertura `[OK]` 99,7 % (578/580). [x] «Evidencias» con sus números (mutación pendiente).
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] Commit por tarea (`T3+T4` y `T10+T11` juntos, nombrados). T13, T16-T18 abiertas, legítimas
  en esta fase. [x] `features.json` coherente. Árbol: solo este informe sin trackear.

## Veredicto sobre las decisiones del implementer

- **6 (`IMPORTES` y no `SIGRID` para el comentario de una cantidad del mes): correcta técnicamente**
  (deshacer `SIGRID` repone líneas, no `importe_vinculado`), pero contradice R32 y design §6.4, que dicen
  «un evento `SIGRID`»; solo la recoge `ARCHITECTURE.md` (cambio 7).
- **7 (`MARCA_PRUEBAS` en la api): no se acepta tal cual.** `CLAUDE.md` prohíbe copiar lógica entre
  servicios sin decisión expresa, y la marca es configuración del transfer (`st.marca_pruebas`): si
  cambia allí, la api deja la marca en el comentario sin fallar (`INTEGRACION.md` §7 lo admite). Cambio 3.
- **8 (en pruebas no vuelve el comentario del titular): limitación aceptada** (F-054 excluye esas líneas
  en pruebas; en real la cubren `test_f069_r32_titular_*`). Nadie la verá de extremo a extremo antes de
  producción y T16 no lo dice (cambio 4).
- **1-5, 9 y 10: bien.** La 4, ver O1. La 9 (`getattr` por dobles viejos) es tolerable.

## Cobertura (requisito → test)

| R | Test |
|---|---|
| R1, R2, R5 | `test_f069_importes_dominio.py` |
| R3, R4, R6-R10, R15, R16 | `test_f069_importes_api.py` (`r3`… `r16`; R8: 5 tests) |
| R11-R14, R29 | `test_f069_importes_front.py` (9, en node) |
| R17-R22, R24 | `test_f069_reglas_importe.py` (25) |
| R23, R25-R28 | `test_f069_pipeline_importe.py` |
| R30 | **sin test**: T9 pide `-k r30` y no selecciona nada (cambio 5) |
| R31, R32 | `test_f069_existentes_tex.py`, `test_f069_traer_comentarios.py` (12 `r32_*`) |
| R33, R34 | `ARCHITECTURE.md` l. 506-509, 1084-1130, 1168-1174; `INTEGRACION.md` §5 y §7; el `VinculadoIn` viejo no lleva `extra="forbid"` |
| R35, R36 | MANUAL T16 y T17 (pendientes) |

## Cambios requeridos

1. **D11/R12/R4: el front manda TODAS las casillas en cada `PUT …/importes`.** `app.js`,
   `guardarAhora` → `cuerpoImportes(casillas)` con todas las de `state.importesEdicion`; la api pone
   `copiado = false` a cada elemento recibido (`use_cases.py`, `GuardarImportes._validar`:
   `out[clave] = (cantidad, False, comentario)`).
   - Efecto: tras copiar el mes, «Revisado», teclear o comentar en UNA casilla quita la marca de
     todas, y el registro siguiente las escribe en Sigrid (R21 ya no las omite).
   - Reproducido con los dobles del propio test (script en mi scratchpad, `d11/prueba_d11.py`): km y
     dos cajas copiadas, «Revisado» solo en el km, `PUT` como lo manda el front ⇒ `copiado` de
     `True True True` a `False False False`. Es el caso de T16 (km y caja copiados a 2026-12).
   - Arreglo: mandar solo las casillas cuya foto cambió. Test front con RED: dos copiadas,
     «Revisado» en una ⇒ el cuerpo lleva solo esa.
   - Al humano: con R4 tal cual, **cambiar solo el comentario** de una copiada la da por revisada;
     D11 dice «hasta teclearla o pulsar Revisado». Si no debe contar, hace falta un campo en el
     contrato (p. ej. `revisado`): enmienda de R4 y R12.
2. **RED de R15, R8 y R32 por ruptura deliberada en una copia** (C4 bis). Romper
   `_cantidad_al_transfer` (`copiado` o `cantidad`), `_sin_propuesta`/`_copiar_importes`
   (`copiado=True`) y `TraerDeSigrid._tex`, y pegar en `impl_F-069.md` la salida real de los tests que
   caen, más la del test nuevo del cambio 1.
3. **`MARCA_PRUEBAS` en la api** (`domain/importes.py:34`, usada en `traer_sigrid.py`). El líder lo
   lleva al humano antes de la pasada 2: **(A)**, recomendada: el transfer, que conoce su marca,
   publica en `existentes` el `tex` ya sin ella (enmienda de R31, R32, design §6.1 e
   `INTEGRACION.md` §7); **(B)**: excepción expresa en la lista cerrada de `CLAUDE.md`, con cita y
   fecha en `progress/`.
4. **T16 incompleta** (`tasks.md` T16 y `current.md` l. 79). Añadir: en 2026-12, «Revisado» **solo**
   en el km ⇒ el preflight escribe el km y la caja sigue omitida «copiado del mes anterior sin
   revisar». Y decir en T16 que el comentario del titular no vuelve en modo pruebas (decisión 8).
5. **R30 sin test.** Añadir `test_f069_r30_*`: la traza que `registro_sigrid` escribe en la subfila
   de una caja (`upsert_asignacion_vinculado` solo con `sigrid_*`) conserva `cantidad`, `copiado` y
   `comentario`. Si se traza a F-044, que T9 deje de apuntar a `-k r30`.
6. **`current.md`, falso hoy** (leído entero; son todas):
   - l. 30: «F-054 sigue en su copia `porcentajes-f054`»: está cerrada y unida (l. 6).
   - l. 156-158: «de los vinculados no se trae nada (D18)»: desde F-069 se trae su comentario.
   - l. 203 y 245: «El arnés es la **1.7.3**»: es la 1.10.1 (l. 8).
   - l. 653: «`azure-apps` no tiene remoto configurado»: `origin` es
     `github.com/ruesma-dev/apps-ruesma` y `CLAUDE.md` lo declara compartido.
   - l. 661-663: «**no tiene ninguna fila propia** en el ERP»: escribe en real desde el 2026-10-01 y
     quedan PT32/00001 (l. 89) y las de l. 616-619.
7. **Spec frente a lo construido.** R32 y design §6.4 recogen la decisión 6, marcada «desviación
   aceptada en review, pendiente del OK del humano». Design §4: el puerto real es `de_trabajador`,
   `del_periodo`, `guardar` y `borrar` (no `reemplazar`/`copiar_vacias`); añadir
   `guardar_subfila_importe`, `poner_comentario`, `registradas` e `importes_del_mes_de`.

## Observaciones (no bloquean; el líder las recoge, no las deja en «anotado»)

- **O1** (decisión 4): en un vinculado por %, un comentario sin cantidad se descarta en silencio (no hay
  fila sin cantidad, §7.2): quien escribe el comentario antes que los km lo pierde. Avisar o enmendar R4.
- **O2** (D15 + R26): un comentario tecleado **después** de registrar no viaja (`ya_registrado`) y el
  siguiente «Sincronizar Sigrid» lo pisa con el `tex` de Sigrid. Decírselo al humano y ponerlo en
  `#regla-traer-sigrid`.
- **O3** `CopiarTrabajadorAnterior` sobre un destino con líneas sustituye también su caja tecleada:
  coherente con «sustituyendo», pero matiza el «nunca pisa» de R8.
- **O4** `traer_sigrid._comentarios`: sin `sigrid_hmores_ide` (la traza no sobrevive al guardar),
  `orden = 0` y el comentario del mes no sale de la línea de menor `ide`. Menor.

## Automejora (propuesta para `CHECKPOINTS.md` C4 y `arnes-base`)

Con una marca de estado por elemento («sin revisar», «pendiente») y un `PUT` que la quita, comprobar
con **dos** elementos marcados que actuar sobre uno no cambia el otro: los tests de uno no lo ven.

## Resultado de `ARNES_SIN_CACHE=1 bash harness/init.sh` (2026-11-19, `ed7c212`, sin pipes)

Suites sin caché, todas en verde: raíz 2319 passed / 47 skipped (708,9 s); api 1618 passed; front 568
passed; transfer 1933 passed. `[OK]` PUERTA COBERTURA 99,7 % (578/580), CARRIL N/A, CAPA E2E N/A,
`.env`, `config.yaml`, rama. **Código 1 por un único `[KO]`: PUERTA TAMAÑO, `progress/review_F-069.md`
154 > 140**, el borrador de este informe, que existía mientras corría. Recortado a ≤ 140 y medido de
nuevo con `python -m harness.tamano --feature F-069` (resultado en la línea siguiente).
`[OK]` PUERTA TAMAÑO: «dentro de los topes (requirements 148/150, design 241/250, impl 218/220, review 138/140)», código 0.
