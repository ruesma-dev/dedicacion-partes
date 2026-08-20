<!-- specs/F-002-reglas-postventa-conflicto/tasks.md -->
# F-002 · Tareas

Rama: `feature/F-002-reglas-postventa-conflicto` (ya creada y activa).
Un commit por tarea: `F-002 Tn: descripción`.

> **Estado (2026-08-20).** **Fases 1 y 2 hechas y APROBADAS**
> (`review_F-002_fase1.md`, `review_F-002_fase2.md`). **D1 y D2 cerradas**
> (`requirements.md` §2): la ⛔ PARADA de la v1 ya no existe.
>
> De las tres verificaciones **MANUAL (humano)** que quedaban: **T13 y T14 se
> ejecutaron el 2026-08-20** contra Sigrid real (volcados en
> `progress/sigrid_F-002.md`), y **T6 se movió a F-014**. Lo único que sigue
> pendiente de T14 es `limpiar --confirmar`, que también está en F-014: hay
> una fila de prueba viva en Sigrid (`hmores.ide = 403039`).
>
> **T1–T5 no se tocan.** Están hechas, revisadas y commiteadas.

---

## Fase 1 — Hecha y aprobada

- [x] **T1**: Crear `services/dedicacion-transfer/tests/conftest.py` con el
  `ClienteFalso` parametrizable (presupuesto de postventa `hojas` |
  `capitulos`, líneas previas del parte configurables, `synckeys`
  precargadas) y `SettingsFalso`. Sin red, sin BBDD, sin `.env`.
  **Verificación:** `python -m pytest services/dedicacion-transfer/tests -q`
  sigue en verde (la fixture aún no la usa nadie, pero importa limpio).

- [x] **T2**: Añadir `tests/test_f002_reglas.py` con R6–R9 y R12 sobre
  `ReglasPorcentajes` directamente (sin pipeline): sin `M*` se omite, fecha
  al último día del mes, `can`/`pre`/`tot`, porcentaje fuera de `(0,1]`,
  `POSTVENTA_REGISTRAR=false`.
  **Verificación:** `pytest -q -k test_f002_r6 or test_f002_r7 or
  test_f002_r8 or test_f002_r9 or test_f002_r12` en verde; **fase RED**
  pegada en `progress/impl_F-002.md` rompiendo en copia aislada la línea que
  cada test vigila.

- [x] **T3**: Extraer a `application/services/reglas_porcentajes.py` las
  funciones puras `campos_identidad(destino)`, `clave_conflicto(accion)` y
  `criterio_choque(existente, accion, *, mias)`, **replicando exactamente la
  conducta actual** (obra normal: no compara `paride`; postventa: sí).
  Sustituir el filtro de `registro_pipeline.py:246-253` por la llamada y
  eliminar la property `AccionLinea.clave_conflicto` en favor de la función.
  **Verificación:** `tests/test_pipeline_offline.py` pasa **sin tocarlo**
  (incluida la aserción `c.clave == "200|202607|5|80001"`). Si cambia algo
  ahí, el refactor está mal.

- [x] **T4**: Añadir `tests/test_f002_conflicto.py` con R14
  (`clave_conflicto` y `criterio_choque` derivan de `campos_identidad`: al
  cambiar la tupla cambian las dos) y `tests/test_f002_pipeline.py` con R10
  (idempotencia por `synckey`), R11 (modo pruebas: destino `0404` pero
  imputación resuelta contra la obra de postventa real) y R13 (dos líneas
  pendientes que chocan con la misma línea existente ⇒ **un solo** `DELETE`
  y `borradas == 1`).
  **Verificación:** `pytest -q -k "test_f002_r10 or test_f002_r11 or
  test_f002_r13 or test_f002_r14"` en verde; fase RED de R13 y R14 pegada en
  el informe (R13 falla contra el código actual: es un defecto real).

- [x] **T5**: Añadir `tests/test_f002_fuente_unica.py` (R1–R5) y aplicar la
  parte no bloqueada de la fuente única:
  - anclas `#regla-p1` … `#regla-p5`, `#regla-conflicto`, `#regla-pruebas` en
    `docs/ARCHITECTURE.md`;
  - sustituir en `services/dedicacion-transfer/README.md` los enunciados de
    **P1, P2 y P3** por la remisión (los de P4 y P5 esperan a T9);
  - retirar el literal `'postventa-2'` del docstring de
    `reglas_porcentajes.py:15` dejando solo el nombre del ajuste
    `POSTVENTA_OBRA_COD` (R5), sin decidir todavía su valor;
  - dejar en `docs/ARCHITECTURE.md` los puntos 5 y 6 marcados
    explícitamente `PENDIENTE · decisión D1/D2 de F-002` en vez de con la ⚠.
  **Verificación:** `pytest -q -k test_f002_r1 or test_f002_r3 or
  test_f002_r5` en verde; los tests de R2/R4 referidos a P4/P5 quedan
  marcados `xfail(strict=True)` hasta T9-T10. Fase RED: el test falla contra
  el árbol actual antes de aplicar el cambio.

---

## Fase 2 — Escribir las decisiones y alinear el código

- [~] **T6 · MOVIDA A F-014** por decisión del humano del 2026-08-20: deja de
  bloquear el cierre de F-002 y se hará con prioridad baja. Contenido, que se
  conserva íntegro en la descripción de F-014: trasladar a Administración el **aviso de las cuatro partidas
  duplicadas** sin cero inicial del presupuesto de `POSTV2` (`656`, `664`,
  `680`, `693`, colgando de la raíz en vez de `CD`; tabla en
  `requirements.md` §2 · D1 y volcado en `progress/sigrid_F-002.md`). No
  rompen nada hoy —`normalize_code` no quita ceros a la izquierda, y eso lo
  fija R18—, pero son ruido de presupuesto y alguien debe saberlo. **Sin
  tocar código.**

  > **Lo que esta tarea pedía además, ya está hecho.** La v1 y la v2 de esta
  > spec reservaban aquí «confirmar el interlocutor de la línea de
  > procedencia», dando por hecho que D1 y D2 las contestaría Administración.
  > No hubo tal conversación: las decidió **Pablo Gris (responsable del
  > proyecto) el 2026-08-19**, respaldándolas con lecturas reales contra
  > Sigrid (C2 y C6), y eso es lo que T7 y T8 escribieron en
  > `docs/ARCHITECTURE.md`. R4 exige **quién · cuándo · respaldo**, no un
  > interlocutor concreto: no queda nada que confirmar. Si algún día
  > Administración revisa estas reglas, se **añade** su procedencia, no se
  > sustituye la que hay.

  **Opcional, no bloqueante:** si el humano quiere calibrar cuánta sobrecarga
  real va a aflorar, puede lanzar las consultas **C3** y **C5** de solo
  lectura (`requirements.md` §3) y pegar el volcado en
  `progress/sigrid_F-002.md`. **C1 y C4 ya no tienen motivo** y no se lanzan.
  **Verificación: MANUAL (humano).**

- [x] **T7**: Escribir en `docs/ARCHITECTURE.md` el **punto 5 definitivo**
  (D1): obra `POSTVENTA_OBRA_COD`, **partida hoja activa**, casado por
  **código exacto**, omisión con motivo si no casa. Retirar la marca
  `PENDIENTE · decisión D1/D2 de F-002` de ese punto y poner la línea de
  procedencia que exige R4 —**quién decidió · cuándo · con qué respaldo**—
  con la referencia a `progress/sigrid_F-002.md`. La real, y la que se
  escribió, es:

  ```
  Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
  verificado contra Sigrid, ver progress/sigrid_F-002.md
  ```

  **No** se escribe «Administración» si Administración no lo dijo: una
  procedencia falsa es peor que ninguna (`requirements.md` R4).
  **Verificación:** `pytest -q -k test_f002_r4` en verde (procedencia fechada
  presente y con formato). Fase RED: el test está hoy en `xfail(strict=True)`;
  al pasar, quitar la marca.

- [x] **T8**: Cerrar la fuente única de P4 y P5. En `docs/ARCHITECTURE.md`:
  - **punto 6** (`#regla-p4` / `#regla-conflicto`) definitivo con **solo la
    Regla A** (identidad = recurso + mes + código de hora + partida, en obra
    normal y en postventa) más la idempotencia por `synckey`, con su línea de
    procedencia;
  - **punto nuevo** con ancla `#regla-capacidad`: la **Regla B**, su límite,
    su tolerancia `0,00005`, su alcance (un parte = una obra) y la remisión
    al punto 4;
  - **punto 4**: frase cruzada hacia `#regla-capacidad` para que quien toque
    la épsilon de `dedicacion-api/domain/estados.py` sepa que hay otra atada
    a ella;
  - retirar de la cabecera la nota «PENDIENTE DE VALIDAR» y anotar la fecha.

  Y retirar los enunciados que quedan fuera de la fuente:
  `README.md` del transfer (bloque de P4/P5 marcado no normativo en T5),
  `reglas_porcentajes.py`, `registro_pipeline.py`, `partida_resolver.py` y
  `registro_models.py`, dejando la remisión a las anclas. Añadir
  `#regla-capacidad` a la lista de anclas del test de R1 y quitar los cinco
  `xfail(strict=True)` de T5.
  **Verificación:** `pytest -q -k "test_f002_r1 or test_f002_r2 or
  test_f002_r3 or test_f002_r4"` en verde, con la lista de frases prohibidas
  completa (incluidas «aunque tenga otra partida», «la misma partida en ese
  parte», «postventa-2», «imputando al CAPÍTULO»).

  > Durante T9–T12 el documento describe una conducta que el código todavía
  > no cumple. Es deliberado: `design.md` §9, última decisión.

- [x] **T9**: Alinear el código con **D1 (postventa)**:
  - `partida_resolver.resolver_postventa`: sustituir
    `hojas = [n for n in nodos.values() if n.activa]` por
    `candidatos = partidas_hoja(nodos)` (hojas **activas**, ordenadas por
    código); renombrar la variable y decir en el docstring qué universo es;
  - `registro_pipeline._destino_postventa`: docstring y variables sin la
    palabra «capítulo»; motivo nuevo `MOTIVO_PARTIDA_PV_NO_HOJA` cuando el
    nodo de destino no sea hoja activa (caso del override manual);
  - `ReglasPorcentajes`: `capitulo_postventa` → `partida_postventa`,
    `self._capitulo` → `self._partida`, y su llamada en el pipeline;
  - **no** renombrar el atributo `capitulo_postventa` del preflight: es
    contrato HTTP que lee el front (`design.md` §3.5);
  - añadir `tests/test_f002_postventa.py` con **R15, R16, R17, R18 y R19**,
    y a `conftest.py` los presupuestos `"hojas_inactivas"` y
    `"orden_invertido"` más las partidas `0656` / `656` y un capítulo de
    código numérico (`design.md` §2.1).
  **Verificación:** `pytest -q -k "test_f002_r15 or test_f002_r16 or
  test_f002_r17 or test_f002_r18 or test_f002_r19"` en verde, con el caso
  «presupuesto con capítulos» y el caso «con hojas» de la fixture; fase RED
  pegada en `progress/impl_F-002.md` (R16 y R17 fallan contra el código
  actual: el filtro que falta es un defecto real).

- [x] **T10**: Aplicar la **Regla A** (identidad):
  - `campos_identidad()` devuelve `CAMPOS_CLAVE` **siempre**; se le quita el
    parámetro `destino` y se actualiza `criterio_choque` y los tests que la
    llaman;
  - reescribir los dos tests de T4 que fijan la conducta contraria
    (`test_f002_r14_en_obra_normal_la_partida_no_distingue` pasa a ser
    `test_f002_r20_la_partida_entra_en_la_identidad[obra]`;
    `..._en_postventa_la_partida_si_distingue` se conserva como el caso
    `[postventa]`), y mover
    `test_f002_r14_lo_nuestro_no_choca_con_nosotros_mismos` a R22;
  - añadir R20, R21 y R22 a `tests/test_f002_conflicto.py` y el control de
    R21 sobre el pipeline (una línea con otra partida **no** se borra);
  - revisar `tests/test_pipeline_offline.py` (`design.md` §3.8) y
    **justificar por escrito, una a una**, las aserciones que cambien.
  **Verificación:** `pytest -q -k "test_f002_r20 or test_f002_r21 or
  test_f002_r22"` en verde y **suite completa del transfer en verde**; fase
  RED pegada.

- [x] **T11**: Implementar la **Regla B — detección** (`design.md` §4.2–4.4):
  - en `reglas_porcentajes.py`: `LIMITE_CAPACIDAD`, `EPSILON_CAPACIDAD`
    (con el comentario que justifica el número), `PREFIJO_CLAVE_SOBRECARGA`,
    `MOTIVO_SOBRECARGA`, `Capacidad`, `es_linea_mensual`,
    `evaluar_capacidad`, `clave_sobrecarga`;
  - en `registro_models.py`: campos `motivo`, `suma_existente`, `suma_total`
    y `exceso` de `Conflicto`, **todos con defecto**, y el docstring que deja
    escrito que una sobrecarga **nunca** lleva `lineas`;
  - en `registro_pipeline.preflight`: paso 7 bis, agrupando por recurso y
    añadiendo los conflictos de sobrecarga **después** de los de pisado;
  - `tests/test_f002_capacidad.py` con **R23, R24, R25, R26, R27, R30, R31 y
    R33**, incluidos los controles positivos (una jornada de exactamente
    `1,0` repartida entre partidas **no** avisa) y el caso de la línea
    pisada, la `synckey` propia y la `ya_registrado`.
  **Verificación:** `pytest -q -k "test_f002_r23 or test_f002_r24 or
  test_f002_r25 or test_f002_r26 or test_f002_r27 or test_f002_r30 or
  test_f002_r31 or test_f002_r33"` en verde; fase RED pegada (toda la regla
  es nueva: la RED es real contra el código de producción).

- [x] **T12**: Implementar la **Regla B — escritura y salvaguardas** en
  `registro_pipeline.ejecutar`:
  - una sobrecarga sin confirmar bloquea sus registros y los lista en
    `omitidas` con `MOTIVO_SOBRECARGA` (R28);
  - una sobrecarga confirmada escribe y **no borra nada** (R29): sale gratis
    porque su `lineas` está vacío, y se prueba;
  - **R32**: un conflicto confirmado solo emite sus borrados si al menos uno
    de sus `registros` llega a `a_escribir`. Es el requisito que impide
    borrar la línea de Administración sin escribir el sustituto;
  - **R13** se conserva (deduplicación por `ide`) y su test se reexpresa
    inyectando dos conflictos que comparten `hmores.ide`, porque el escenario
    original ya no es alcanzable con la Regla A (`design.md` §5.6); el
    control positivo «dos líneas distintas se borran las dos» se mantiene tal
    cual.
  **Verificación:** `pytest -q -k "test_f002_r13 or test_f002_r28 or
  test_f002_r29 or test_f002_r32"` en verde y **suite completa del transfer
  en verde**; fase RED de R32 pegada. Esa RED es real **contra el árbol tal
  como queda tras T11**: el bloqueo genérico de conflictos sin confirmar ya
  funciona (`bloqueadas.update(c.registros)`), así que confirmar el pisado y
  denegar la sobrecarga **borra la línea de Administración sin escribir el
  sustituto**. Hay que enseñarlo fallando antes de poner la guarda.

---

## Fase 3 — Verificación real y cierre

- [x] **T13** · **EJECUTADA el 2026-08-20** sobre el periodo **julio de 2026**
  (no agosto: el mes con datos reales era el 7). Volcado completo en
  `progress/sigrid_F-002.md` § T13. Resultado: **13 obras, 25 acciones —
  4 escribir, 21 omitir, 0 conflictos**. La partida resuelta **es una hoja**
  (`CI.1.8`, por categoría); el conflicto de sobrecarga **no llegó a
  ejercitarse** porque el parte de julio de la obra destino no existía, y eso
  queda dicho en el volcado para no confundirlo con «funciona».
  ```
  cd services/dedicacion-transfer
  python prueba_escritura_porcentajes.py capitulos
  python prueba_escritura_porcentajes.py estado --ano 2026 --mes 7
  python prueba_escritura_porcentajes.py preflight --ano 2026 --mes 7
  ```
  (previa edición de `LINEAS_PRUEBA` y `OBRA_ORIGEN_PRUEBA` con empleados
  reales con código `M*`). Comprobar en el `preflight` que **la partida
  resuelta es una hoja** y que, si el trabajador ya tiene líneas `M*` en el
  parte, el conflicto de sobrecarga aparece con sus cifras. Volcado a
  `progress/sigrid_F-002.md`.
  **Verificación: MANUAL (humano).** Solo lectura. Requiere `.env` con la
  function key: **ningún agente lo toca**.

- [x] **T14** · **EJECUTADA EN PARTE el 2026-08-20**, sobre **julio de 2026**.
  Se hicieron `ejecutar --confirmar` y la verificación (leyendo Sigrid por
  `synckey`, no fiándose de la respuesta del servicio): fue **la primera
  escritura real de este sistema en el ERP** — `hmores.ide = 403039`, parte
  `PT26/00296` creado, obra de pruebas `0404`. Volcado en
  `progress/sigrid_F-002.md` § T14.
  **`limpiar --confirmar` NO se ejecutó, a propósito**: el humano quiso ver la
  fila en la pantalla del ERP antes de borrarla, así que **sigue viva** y la
  limpieza se movió a **F-014** (prioridad 20).
  ```
  python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 7
  python prueba_escritura_porcentajes.py verificar --ano 2026 --mes 7
  python prueba_escritura_porcentajes.py limpiar --confirmar --ano 2026 --mes 7   # PENDIENTE → F-014
  ```
  **Verificación: MANUAL (humano).** Exige `OBRA_PRUEBAS_FORZAR=true` y
  **autorización expresa del humano para esta acción concreta**
  (`CLAUDE.md`, reglas duras). **Ningún agente la lanza por su cuenta**, ni
  siquiera con la feature aprobada.

- [x] **T15**: Campaña de mutación con cero supervivientes:
  `python -m harness.mutacion --feature F-002 --workers 1`.
  **Verificación:** `progress/mutacion_F-002.md` con 0 supervivientes, o cada
  superviviente con justificación escrita para que la acepte el humano
  (rigor `critico`).

- [x] **T16**: Escribir la sección **«Evidencias»** en
  `progress/impl_F-002.md` con los cuatro números: tests ejecutados y
  resultado, cobertura de las líneas cambiadas, mutantes y supervivientes,
  tiempo de la suite. Listar las verificaciones `MANUAL (humano)` (T6, T13,
  T14) con su comando exacto y su resultado real.
  **Verificación:** el reviewer las encuentra sin preguntar.

- [x] **T17**: Ejecutar `bash harness/init.sh` en verde (incluida la puerta
  de cobertura de las líneas cambiadas ≥ 80 %).
  **Verificación:** exit code 0 y `[OK]` en la puerta de cobertura.
</content>
</invoke>
