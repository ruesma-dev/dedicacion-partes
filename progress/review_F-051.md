<!-- progress/review_F-051.md -->
Revisión completa (pasada 1): `git diff 2c75a1c...c070244` (merge-base con `dev`; `dev` está en `708236f`)

# F-051 · Review (reviewer, 2026-10-20)

**Veredicto: RECHAZADO (CHANGES_REQUESTED).** El código es sólido y cumple la
spec: no queda ningún `DELETE`, la guarda es completa, la `synckey` ajena se
conserva y la idempotencia va por `hmores_ide`. Se rechaza por **un mutante
declarado equivalente que no lo es** (lo maté con un test en una copia, §4) y
por el rastro desfasado de `current.md`. Los arreglos son pequeños.

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 %, campaña completa con **0 supervivientes** salvo
justificación aceptada por el humano, RM5 y MANUAL con comando exacto.

## 1. Verificación ejecutada

`bash harness/init.sh` (sin cachés): **exit 0**, sin `[KO]`. Raíz 418 (+1
skipped), api 949, front 310, transfer 1075. **COBERTURA 99,2 %** (253/255);
TAMAÑO dentro. Árbol limpio; lo probado, en el scratchpad del reviewer.

## 2. Puntos pedidos por el líder

| Punto | Resultado |
|---|---|
| Ningún `DELETE` en el registro | [x] El paso 10 solo emite editar, poner a 0 e insertar. `stmt_borrar_linea` solo lo llama `limpiar`. Lo cubren `…r6_ningun_delete_en_ningun_escenario`, `_sin_delete` en cuatro tests más y `…r6_ninguna_sentencia_de_edicion_borra_ni_concatena` |
| Guarda del `UPDATE` | [x] `_guarda` (`sigrid_write_client.py:836-851`): `ide`, `reside` leído, `ABS(can − leído) < 1e-6`, `synckey` leída recortada, 6 enlaces a 0, `LIKE 'M%'` y `con.est`. Parametrizada y con `WHERE` siempre (un test compara la cadena entera). Si la guarda falla: `omitidas` y sin insertar (`…r13_guarda_fallida_…`). R12 hace caer la acción o el pisado entero antes de dar de alta partes |
| `synckey` de otro sistema | [x] `synckey_tras_editar` conserva toda la que no esté vacía y no sea `porcentajes:`; a las vacías, la nuestra (`…r9_…` ×4) |
| Idempotencia por `hmores_ide` | [x] Paso 6: `ide` + mismo recurso + no ser nuestra de otra asignación; si no, `synckey`. Una sola lectura, también en el lote. La api manda y guarda (`test_f051_hmores_ide.py`, 6 tests) |
| D14 / D7 | [x] `repartir_choques`: uno por `registro_id` (el de menor `ide`) y el resto a 0, solo `can`/`tot`. En postventa, solo la misma partida (`…r5_tres_choques…`, `…r1_postventa…` ×2) |
| Log de D13 | [x] `_traza`: `antes` con la fila entera (`can`, `pre`, `tot`, hora, partida, cuenta, `fec`, `synckey`, `tex`) y `despues`, escrito antes de enviar (`…r18_…`) |
| Lista cerrada | [x] Solo cambian los listados, más `test_f013_r4…` (opción A). Los dos `test_f049_r2_…` intactos (opción B). Los dobles ganan `EdicionesFalsas` sin cambiar ninguna aserción |
| Front sin lógica | [x] `rotuloConflicto` solo da formato a `edita_ide` y `a_cero_ides` |
| Documentación | [x] `#regla-cero` (regla 20, en `ANCLAS`), «editar» en `#regla-conflicto`, `#regla-analitica`, el transfer y la tabla de sigrid-api. `INTEGRACION.md` §1, §5 y §7, con el orden transfer → api → front |

## 3. Checkpoints

- **C1** [x] init.sh con exit 0; [x] existen los ficheros base.
- **C2** [x] una sola `in_progress`; [x] la rama es la de la feature;
  **[ ] `current.md` con restos** (cambio requerido 2); history: N/A hasta
  `done`.
- **C3** [x] El dominio no importa infraestructura (ver O1). [x] Primera
  línea con la ruta en el código y los tests nuevos. [x] Sin prints de debug
  (los `print` son la salida del script CLI), sin secretos ni dependencias
  nuevas. [x] Trampas: la escala no cambia (`can` sobre 1, redondeado a 4),
  postventa intacta, solo escribe el transfer con `synckey` y modo pruebas.
  Estilo: cambio requerido 3.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1-R19 con tests `test_f051_rN_*` en verde. R20: lo cubre el
  test R6, y `limpiar` no cambia. R21: `test_f002_fuente_unica`. R22:
  documental, verificado leyendo. R23 = T15. [x] Sin red ni BBDD. [x] T15 en
  `current.md` con su comando exacto (`--ano`/`--mes` existen).
- **C4 bis** [x] rigor declarado. [x] RED con trazas reales (T1-T2, T4-T9,
  T11, T12; T3, T10 y T13 sin RED, justificado). [x] Cobertura `[OK]`.
  [x] Totales verificados (§4). [x] Campaña de 1791,9 s (> 60 s): **no
  reejecutada**; recálculo puro + RM. [x] Coste por mutante 13,4 s (> 1 s).
  [x] Sin «CAMPAÑA NO VÁLIDA» ni «sin veredicto». [x] RM1. [x] RM2.
  **[ ] RM5** y **[ ] cero supervivientes**: §4. [x] RM6. [x] Evidencias con
  workers.
- **C4 ter** N/A: sin `harness/rutas_sensibles.json`.
- **C5** [x] T1-T14 y T17 `[x]` con commits `F-051 Tn:`. T15 (humano) y T16
  (líder, al desplegar) abiertas, como prevé la spec. [x] Sin artefactos.
  [x] `features.json` en `in_progress`.

## 4. Mutación: verificación independiente

- **Recálculo** (`alcance_de_feature` + `generar_mutantes`, puro): 8
  ficheros, **622 líneas, 134 mutantes**, igual que el informe.
- **RM1.** Se midió en `4dea061`; luego `abb5638` toca
  `sigrid_write_client.py` (paréntesis). Los mutantes de `4dea061` y de HEAD
  son **idénticos** (diferencia vacía): la campaña vale para HEAD.
- **RM2.** Líneas base de 23,6 s (transfer) y 57,5 s (api), media 13,4 s;
  134 × 13,4 ≈ 1791,9. No hay salto de orden de magnitud: lo explica `-x`.
- **RM6.** `usadas` vacío no quita defensa: el paso 7 saca las pisables de
  los choques (`ls.ide not in suyas`), y la guarda y R13 cubren dos acciones
  sobre la misma línea.
- **RM5 (muestra de UNO): la equivalencia es FALSA.** Mutante
  `registro_pipeline.py:1095` `>= 0.000001` → `>`. La búsqueda del
  implementer recorre `k = 1…9999`, pero **`despues.can` puede valer 0,0**:
  P3 admite `0 < porcentaje ≤ 1` y `round(0.00004, 4) == 0.0`. Con una
  relectura de `can = 1e-6`, `abs(1e-6 − 0) == 1e-6` exacto: el original
  omite la línea y el mutante la da por escrita. Mi búsqueda exacta con
  `Fraction` (k = 0…20000) da **solo ese caso**. En una copia del transfer,
  este test pasa con el original y **falla con el mutante** («1 failed»):
  ```python
  class Otra(ClienteFalso):
      def _aplicar_ediciones(self, statements):
          super()._aplicar_ediciones(statements)
          self.lineas_parte[0].can = 0.000001
  cli = Otra(lineas_parte=[_cero(410600)])
  res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea(porcentaje=0.00001)])
  assert res.escritas == [] and res.omitidas[0]["registro_id"] == 1
  ```
  No se puede pedir al humano que acepte «no existe entrada que lo mate».

## 5. MANUAL T15

Está listada con su comando exacto (`tasks.md` T15, `current.md`, impl §6).
Sin ella solo queda sin probar lo que no alcanza un test unitario: que SQL
Server evalúe la guarda (`hmores.*` correlado dentro del `UPDATE`, `SET tex`,
`LIKE 'M%'`), que sigrid-api admita el `UPDATE` y que `pos` no se mueva. Qué
se edita lo cubren tests con un doble que aplica la misma guarda. **No pasa
a `done` sin el resultado real de T15** (rigor crítico).

## 6. Cambios requeridos

1. **Mutante `registro_pipeline.py:1095`.** Añadir el test de §4
   (`test_f051_r13_…`), comprobar que lo mata, relanzar
   `python -m harness.mutacion --feature F-051` hasta 0 supervivientes y
   corregir el análisis, impl §4 y Evidencias y `current.md` (líneas 14-15
   y 68-69, donde se pide al humano aceptar el equivalente).
2. **`progress/current.md`.** Dan D14-D15 por abiertas o el entorno en
   `[KO]`: la cabecera de la línea 93, las líneas 114-118, la 296 y las
   142-144 (sin `.venv`). Reescribirlas y dejar **una sola** entrada de T15
   (hoy hay dos, 79-85 y 119-125, con detalle distinto).
3. **`registro_pipeline.py:568`.** La condición del paso 6 ocupa 121
   caracteres con 21 espacios en medio (se perdió una continuación de
   línea). Partirla.
4. **`progress/impl_F-051.md`.** Le falta la primera línea
   `<!-- progress/impl_F-051.md -->`, como en `mutacion_F-051.md`.

## 7. Observaciones (no bloquean)

- **O1.** `reglas_porcentajes.py`, que eran funciones puras, importa ahora
  `PREFIJO_SYNCKEY` de infraestructura. Hay precedente en el pipeline y en
  el lote, pero mejor que la constante viva en el dominio.
- **O2.** Riesgo de `ide` reutilizado (design §10). Exigir además
  `es_linea_mensual(hit)` en el paso 6 cerraría el caso de `partes`, que
  escribe `H*`/`C*`. Lo decide el humano.
- **O3.** Con otra partida, `AVISO_LINEA_CERO` enseña un `ide`, no un código.
- **O4.** Hueco anterior a F-051: con porcentaje < 0,00005 sale una acción
  `escribir` con `can` 0, que ahora editaría una línea al 0 % dejándola a 0
  con nuestra `synckey`. Para el humano.
- **O5.** `dev` avanzó a `708236f` (despliegue de F-057). Al fusionar,
  `current.md` chocará: aquí F-057 sigue «pendiente de desplegar».

## 8. Automejora (propuesta, no aplicada)

`reviewer.md` RM5: la demostración cubre los **extremos del dominio** (0,
máximo, nulo) que admite quien construye el dato. Aquí falló `k = 0`.
