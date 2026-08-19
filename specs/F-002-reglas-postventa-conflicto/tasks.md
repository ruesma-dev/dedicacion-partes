<!-- specs/F-002-reglas-postventa-conflicto/tasks.md -->
# F-002 · Tareas

Rama: `feature/F-002-reglas-postventa-conflicto` (ya creada y activa).
Un commit por tarea: `F-002 Tn: descripción`.

> **Cómo está ordenado esto.** Las tareas **T1–T5 no dependen de
> Administración** y se pueden hacer ya. A partir de T6 hay una **PARADA**:
> nada por debajo se implementa hasta que el humano vuelva con las respuestas
> a D1 y D2 de `requirements.md` §2. Si el implementer llega a la parada y no
> hay respuesta, marca la feature `blocked` en `harness/features.json`, lo
> anota en `progress/current.md` y para.

---

## Fase 1 — Independiente de Administración

- [ ] **T1**: Crear `services/dedicacion-transfer/tests/conftest.py` con el
  `ClienteFalso` parametrizable (presupuesto de postventa `hojas` |
  `capitulos`, líneas previas del parte configurables, `synckeys`
  precargadas) y `SettingsFalso`. Sin red, sin BBDD, sin `.env`.
  **Verificación:** `python -m pytest services/dedicacion-transfer/tests -q`
  sigue en verde (la fixture aún no la usa nadie, pero importa limpio).

- [ ] **T2**: Añadir `tests/test_f002_reglas.py` con R6–R9 y R12 sobre
  `ReglasPorcentajes` directamente (sin pipeline): sin `M*` se omite, fecha
  al último día del mes, `can`/`pre`/`tot`, porcentaje fuera de `(0,1]`,
  `POSTVENTA_REGISTRAR=false`.
  **Verificación:** `pytest -q -k test_f002_r6 or test_f002_r7 or
  test_f002_r8 or test_f002_r9 or test_f002_r12` en verde; **fase RED**
  pegada en `progress/impl_F-002.md` rompiendo en copia aislada la línea que
  cada test vigila.

- [ ] **T3**: Extraer a `application/services/reglas_porcentajes.py` las
  funciones puras `campos_identidad(destino)`, `clave_conflicto(accion)` y
  `criterio_choque(existente, accion, *, mias)`, **replicando exactamente la
  conducta actual** (obra normal: no compara `paride`; postventa: sí).
  Sustituir el filtro de `registro_pipeline.py:246-253` por la llamada y
  eliminar la property `AccionLinea.clave_conflicto` en favor de la función.
  **Verificación:** `tests/test_pipeline_offline.py` pasa **sin tocarlo**
  (incluida la aserción `c.clave == "200|202607|5|80001"`). Si cambia algo
  ahí, el refactor está mal.

- [ ] **T4**: Añadir `tests/test_f002_conflicto.py` con R14
  (`clave_conflicto` y `criterio_choque` derivan de `campos_identidad`: al
  cambiar la tupla cambian las dos) y `tests/test_f002_pipeline.py` con R10
  (idempotencia por `synckey`), R11 (modo pruebas: destino `0404` pero
  imputación resuelta contra la obra de postventa real) y R13 (dos líneas
  pendientes que chocan con la misma línea existente ⇒ **un solo** `DELETE`
  y `borradas == 1`).
  **Verificación:** `pytest -q -k "test_f002_r10 or test_f002_r11 or
  test_f002_r13 or test_f002_r14"` en verde; fase RED de R13 y R14 pegada en
  el informe (R13 falla contra el código actual: es un defecto real).

- [ ] **T5**: Añadir `tests/test_f002_fuente_unica.py` (R1–R5) y aplicar la
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

- [ ] **T6**: Volcar en `progress/current.md` las **dos preguntas cerradas**
  (D1.1, D1.2, D2) y las **cinco consultas C1–C5** listas para copiar y
  pegar, con la advertencia de `max_rows`, `truncated` y el corte de 230 s.
  **Verificación:** el humano confirma que puede llevárselas a Administración
  tal cual. **MANUAL (humano).**

---

## ⛔ PARADA — todo lo que sigue depende de la respuesta de Administración

No abrir ninguna tarea de aquí abajo sin las respuestas a D1 y D2 por
escrito. Si la respuesta contradice el diseño de `design.md`, **parar y
volver a proponer** (ritmo de trabajo de `CLAUDE.md`), no improvisar.

---

## Fase 2 — Cerrar D1 (postventa) y D2 (conflicto)

- [ ] **T7**: Ejecutar contra `sigrid-api` las consultas **C1–C5** de
  `requirements.md` §2 (`POST /api/sql/read`, base `ruesma`, **solo
  lectura**) y pegar el volcado íntegro en `progress/sigrid_F-002.md` con
  fecha y quién la lanzó. Si alguna respuesta trae `truncated: true`,
  paginar y repetir.
  **Verificación: MANUAL (humano).** Comando exacto (PowerShell, con la
  function key fuera del repositorio):
  ```powershell
  $body = Get-Content .\consulta_C2.json -Raw
  Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post `
    -Headers $headers -ContentType "application/json" -Body $body |
    ConvertTo-Json -Depth 8
  ```

- [ ] **T8**: Escribir en `docs/ARCHITECTURE.md` el **punto 5** definitivo
  (D1.1 + D1.2), sin la ⚠, con `Confirmado por Administración el AAAA-MM-DD ·
  <interlocutor>` y la referencia a `progress/sigrid_F-002.md`.
  **Verificación:** `pytest -q -k test_f002_r4` en verde (procedencia fechada
  presente y con formato).

- [ ] **T9**: Escribir en `docs/ARCHITECTURE.md` el **punto 6** definitivo
  (D2), con la misma línea de procedencia. Retirar la nota «PENDIENTE DE
  VALIDAR» de la cabecera del documento si ya no queda nada pendiente.
  **Verificación:** `pytest -q -k test_f002_r4` en verde.

- [ ] **T10**: Alinear el código con **D1**: `resolver_postventa`
  (`partida_resolver.py:54`, universo de candidatos hoja **o** capítulo, y la
  variable deja de llamarse `hojas` si no lo son), `_destino_postventa`
  (`registro_pipeline.py:79-108`), el filtro de `_cat`
  (`registro_pipeline.py:296`) para que publique el mismo universo (R17), el
  motivo de omisión nuevo y, si D1.2 sale «partida», el renombrado
  `capitulo_postventa` → `partida_postventa` en `reglas_porcentajes.py` y su
  llamada en `registro_pipeline.py:156`. Añadir
  `tests/test_f002_postventa.py` con R15–R17.
  **Verificación:** `pytest -q -k "test_f002_r15 or test_f002_r16 or
  test_f002_r17"` en verde, con el caso «presupuesto de postventa con
  capítulos» y el caso «con hojas» de la fixture; fase RED pegada.

- [ ] **T11**: Alinear el código con **D2**: ajustar `campos_identidad` (y
  solo eso) para el destino `obra`; añadir R18 y R19 a
  `tests/test_f002_conflicto.py`. Si la conducta cambia respecto a T3,
  actualizar `tests/test_pipeline_offline.py` y **justificar por escrito** en
  el informe cada aserción tocada.
  **Verificación:** `pytest -q -k "test_f002_r18 or test_f002_r19"` en verde
  y suite completa del transfer en verde; fase RED pegada.

- [ ] **T12**: Retirar los enunciados restantes de P4 y P5 de README,
  docstrings y comentarios (`README.md:8-35`,
  `reglas_porcentajes.py:1-18` y `:43-49` y `:77`,
  `registro_pipeline.py:1-21` y `:83` y `:227` y `:243-245`,
  `partida_resolver.py:1-14` y `:51`,
  `registro_models.py:7` y `:131-140`) y dejar la remisión a las anclas.
  Quitar los `xfail` de T5.
  **Verificación:** `pytest -q -k test_f002_r2 or test_f002_r3` en verde con
  la lista de frases prohibidas completa (incluidas «aunque tenga otra
  partida», «la misma partida en ese parte», «postventa-2», «imputando al
  CAPÍTULO»).

---

## Fase 3 — Verificación real y cierre

- [ ] **T13**: Verificar el casado contra Sigrid **sin escribir**:
  ```
  cd services/dedicacion-transfer
  python prueba_escritura_porcentajes.py capitulos
  python prueba_escritura_porcentajes.py estado --ano 2026 --mes 8
  python prueba_escritura_porcentajes.py preflight --ano 2026 --mes 8
  ```
  (previa edición de `LINEAS_PRUEBA` y `OBRA_ORIGEN_PRUEBA` con empleados
  reales con código `M*`). Volcado a `progress/sigrid_F-002.md`.
  **Verificación: MANUAL (humano).** Requiere `.env` con la function key:
  ningún agente lo toca.

- [ ] **T14**: Escritura real **en la obra de pruebas** `0404` con la marca
  `PRUEBA-PORC`, y limpieza posterior:
  ```
  python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 8
  python prueba_escritura_porcentajes.py verificar
  python prueba_escritura_porcentajes.py limpiar --confirmar
  ```
  **Verificación: MANUAL (humano).** Exige `OBRA_PRUEBAS_FORZAR=true` y
  **autorización expresa del humano para esta acción concreta**
  (`CLAUDE.md`, reglas duras). Ningún agente la lanza por su cuenta.

- [ ] **T15**: Campaña de mutación con cero supervivientes:
  `python -m harness.mutacion --feature F-002`.
  **Verificación:** `progress/mutacion_F-002.md` con 0 supervivientes, o cada
  superviviente con justificación escrita para que la acepte el humano
  (rigor `critico`).

- [ ] **T16**: Escribir la sección **«Evidencias»** en
  `progress/impl_F-002.md` con los cuatro números: tests ejecutados y
  resultado, cobertura de las líneas cambiadas, mutantes y supervivientes,
  tiempo de la suite. Listar en `progress/current.md` las verificaciones
  `MANUAL (humano)` (T7, T13, T14) con su comando exacto y su resultado real.
  **Verificación:** el reviewer las encuentra sin preguntar.

- [ ] **T17**: Ejecutar `bash harness/init.sh` en verde (incluida la puerta
  de cobertura de las líneas cambiadas ≥ 80 %).
  **Verificación:** exit code 0 y `[OK]` en la puerta de cobertura.
