<!-- progress/spec_F-054.md -->
# F-054 · Informes del spec-author

## 2026-10-29 · Revisión de la spec contra F-044, F-062 y F-068

Copia `porcentajes-f054`, rama `feature/F-054-sync-trae-porcentajes`, con
`dev` unido (`ac56e96`). Solo lectura de código; **ninguna lectura contra
Sigrid** (no hizo falta evidencia nueva). `features.json` sin tocar. La copia
**no tiene `.venv`** en ningún servicio (ni en la raíz): no se ha creado y no
se ha ejecutado la suite; el tope de tamaño se ha medido con `python -m
harness.tamano --feature F-054` → requirements 150/150, design 250/250.

### Qué estaba desfasado y qué cambia

1. **`a_cero_hechos` sobraba (y obligaba a tocar `registro_pipeline.py`).**
   `RegistroPipeline.ejecutar` repite su preflight y relee `lineas_del_parte`
   del cliente real (no de la memoria del lote): tras `poner-a-cero`, la
   puesta a 0 ya no suma y la omitida sí. Se quita el parámetro (R36, design
   §6.4) y `registro_pipeline.py` —que ahora lleva F-044 y F-062 dentro— pasa
   a **no se toca** (§10). El `ejecutar` del transfer no cambia de contrato.
2. **Choque de nombres con F-051.** La respuesta de `registro/ejecutar` ya
   tiene `a_cero` por obra (lo que F-051 pone a 0 al pisar). El campo de B
   en la api pasa a `sobrantes_a_cero` (cuerpo y respuesta) y la respuesta
   de `poner-a-cero`, a `puestas`/`omitidas` (design §1).
3. **Tests ajenos.** `TransferClient.preflight_lote` gana `completo`; los
   dobles de `test_f022`, `test_f024` y `test_f055` de la api entran en la
   lista cerrada (aceptan el parámetro, sin cambiar aserciones).
   `test_f055_r26_cliente_http_del_lote` y `…_sin_lineas_no_llama` comparan
   el cuerpo y la respuesta exactos: por eso `completo` solo va en el cuerpo
   si es `true`, y `sobrantes` / `sobrantes_a_cero` solo si hay alguna.
4. **Anclas.** El punto 22 de `ARCHITECTURE.md` ya es `#regla-vinculado`
   (F-044); las nuevas pasan a **23** `#regla-traer-sigrid` y **24**
   `#regla-obra-cero`. `ANCLAS` sigue siendo la única lista que cambia.
5. **«Primera ronda» del lote.** `precargar` tiene ahora rondas A-D (F-055,
   F-044, F-062). La lectura de B va en la **ronda A** (no depende de nada) y
   las peticiones de 4 elementos de F-062 (`ContextoRachas`) se aceptan igual.
6. **Cobertura con acciones omitidas.** Se fija que cualquier acción del
   recurso cubre, también omitida (otra empresa, sin partida…): la obra se la
   da la plataforma aunque hoy no se escriba (R31).
7. **Recursos de B.** Solo los de las **líneas** del lote (D14); los que
   llegan solo con incidencias (F-030) o en el contexto de F-062 no.
8. **Front.** `pintarModalPreflight`, `registroEjecutar` y `unirPreflight`
   (que ya conserva las claves de arriba con `...previo`) son los puntos de
   enganche; casilla `.chk-cero` aparte de `.chk-pisar` y fuera del
   `marcadaPorDefecto`/`vistas` de F-064.
9. **Lo de F-044 (design §10 de F-044).** Parte A: la lectura es por prefijo
   `M%` y la api decide **por recurso**: la `MESVE` de un vinculado cuenta en
   `de_vinculados` (nuevo contador en R14/R27), nunca es asignación ni cae en
   `fuera_maestro`. Parte B: la lectura de trabajadores va por `reside`, así
   que la `MESVE` del vinculado en el mismo parte no es sobrante del
   trabajador (test explícito en T11). Aceptar una entrada hace `UPDATE` en
   su sitio y conserva sus filas de `asignacion_vinculado` (`ON DELETE
   CASCADE`): otra razón para no usar `reemplazar`. El evento `SIGRID` lleva
   el snapshot con subfilas (como `PARTIDA_VINCULADO`).

### Interacciones revisadas (sin cambio de decisión)

- **Incidencias `CI*`/`CIZ` y rachas de F-062:** no entran en ninguna
  lectura (`LIKE 'M%'` y `can` ≠ 0). Poner a 0 una `M*` deja en su parte el
  `CI*`/`CIZ` y las rachas intactos; la línea no se borra. Sin conflicto.
- **F-068 y la partida traída:** F-068 solo decide la partida del
  vinculado; la traída del titular (elegida, D3) no cambia. Con un titular
  aceptado (ya registrado), cada vinculado se decide solo (F-044 R18): su
  línea manual en la partida que propone F-068 (historial **con** el periodo)
  sale como pisado marcado por defecto (F-064); en otra partida, se escribe
  la nuestra y su capacidad (F-044 R23) avisa de sobrecarga. No hay escritura
  silenciosa de más.
- **Parte compartido (postventa, VAR, 0404):** una sobrante puesta a 0 puede
  ser después la línea al 0 % que `_emparejar_ceros` reutiliza para otra
  acción del recurso en el mismo `ejecutar`: es `#regla-cero` de hoy.
- **Vinculados solo desde `sync.vinculados.desde` (2026-10):** la MANUAL A
  (T18, 2026-09) no los ve; la B (T19) usa 2026-11.

### Decisiones NUEVAS para el humano (requirements §6, design §12)

- **D16. ¿Qué pasa con las líneas de los vinculados en una obra sobrante?**
  Hoy, con B tal cual, quitar al trabajador de una obra pone a 0 su `M*` y
  deja **vivas** las líneas de su teléfono, gasoil, vehículo… en esa obra,
  incluidas las `porcentajes:vin:` que escribimos nosotros.
  - A) Fuera de F-054: B solo trata las `M*` del trabajador. Sin coste; deja
    una incoherencia que nuestro propio sistema crea.
  - B) Aviso sin escritura: se leen y se listan para corregir a mano.
  - **C) Como las del trabajador (R38)**: una lectura más (cualquier hora,
    `can` ≠ 0, de sus vinculados), cubierta según las acciones de **ese**
    vinculado, confirmable por línea con su hora en la guarda (F-044 R24).
  - *Recomendación: C.* `#regla-vinculado` dice que el % del titular se
    aplica tal cual a sus vinculados; con A, una obra quitada deja nuestras
    líneas `porcentajes:vin:` al % viejo. Riesgo: más líneas ajenas tocadas
    (solo `can`/`tot` a 0, siempre confirmadas) y una lectura más en
    paralelo.
- **D17. ¿Con qué valor sale la casilla de una sobrante?**
  - **A) Desmarcada siempre.** B) La de un vinculado, marcada si su titular
    tiene una sobrante en esa obra (lo que hizo F-064 con el pisado).
  - *Recomendación: A.* Es poner a 0 una línea que pudo poner
    Administración, no seguir un cambio nuestro, y el humano pidió «debe
    preguntar».
- **D18. ¿La parte A trae algo de los vinculados?**
  - **A) Nada**: su `MESVE` se cuenta en `de_vinculados` y el resto de horas
    ni se lee. B) Al aceptar la línea del titular, traer la partida de la
    línea del vinculado como **elegida** de su subfila.
  - *Recomendación: A.* La propuesta de F-068 ya parte de esa misma línea
    (historial en la obra con el periodo incluido) y, al registrar, su choque
    se pisa marcado por defecto; B obliga a leer horas no `M*`, escribe en
    `asignacion_vinculado` y fija una elegida que dejaría de seguir al titular.

Las tareas que dependen de D16 = C están marcadas *(D16 = C)* en `tasks.md`
(T11, T12, T13, T19, T20); con A se eliminan, con B se quedan sin la escritura.

### Riesgos

- **Topes de tamaño al límite** (150/150, 250/250): cualquier ajuste tras las
  decisiones tendrá que recortar en otro sitio.
- **B escribe en producción** líneas ajenas (más con D16 = C): solo
  `can`/`tot` a 0, confirmadas por línea, guarda doble, log del antes,
  MANUAL en modo pruebas (T19); el transfer desplegado está en modo real.
- **Coste:** con D16 = C, dos lecturas más por preflight completo (en
  paralelo en la ronda A); el tope del 15 % de R37 sigue valiendo (T10/T19).
- **Sin `.venv` en la copia:** el implementer tendrá que tenerlo para T1-T17
  y T21 (lo decide el líder; aquí no se ha creado).

## 2026-10-29 · Decisiones D16-D18 cerradas: spec APROBADA

El humano, el 2026-10-29, vía el líder: «estoy de acuerdo» con las tres
recomendadas. **D16 = C** (líneas de los vinculados en una obra sobrante,
como las del trabajador, confirmables por línea, R38), **D17 = A** (casilla
de la sobrante siempre desmarcada, R33) y **D18 = A** (la parte A no trae
nada de los vinculados, R14). Recogidas en requirements §6 y design §12 con
la cita y la fecha; R38 y las tareas T11, T12, T13, T19 y T20 quedan firmes
(sin marcadores condicionales). Tamaño: requirements 146/150, design 249/250.
**Spec APROBADA, con todas las decisiones cerradas (D1-D18).** El estado en
`features.json` lo pasa el líder.

## 2026-10-30 · Enmienda D19 (review 2, O7): la `Postv-` omitida tras resolver

El humano eligió la opción **b** de O7 el 2026-10-30 («b», y «si» al plan).
Hoy `omitir` de `ReglasPorcentajes.decidir` no lleva `destino` ni `paride`:
toda `Postv-` omitida cubre todas las partidas de postventa de su recurso,
no solo la omitida antes de resolver la partida. Con D19, la omitida
**después** (sin recurso, porcentaje, sin `M*`) lleva `destino="postventa"`,
`paride` y `partida_cod` resueltos y cubre solo esa; la omitida antes (P5
desactivada, partida sin resolver) sigue con `paride` 0 y las cubre todas.
`cubierta` y `_destino` no cambian. En Sigrid no cambia lo que se escribe.

Cambios en la spec:

- `requirements.md`: R31 nombra D19; cabecera y §6 con D19 (cita y fecha).
  148/150.
- `design.md`: §3 gana la fila de `reglas_porcentajes.py` (solo `omitir`);
  §6.1 reescrito; §10 exceptúa `omitir` de `reglas_*.py`; §12 gana D19 con
  el riesgo. Para seguir en 250/250 se condensaron §8, §9, §11 (F-068
  dentro del punto de vinculados) y §12 (la cita de D16-D18 sube al título),
  sin quitar contenido.
- `docs/ARCHITECTURE.md#regla-obra-cero`: la frase «omitida antes de
  resolverla» se amplía con las dos ramas, y la firma gana D19 (2026-10-30).
- `tasks.md`: D19 en la cabecera y **T22** (RED primero, tests de las dos
  ramas por cada motivo, efecto en `sobrantes`, mutación de lo cambiado,
  revisión de consumidores con PARA, corrección de la frase de
  `impl_F-054.md` l. 108, init.sh).

Los docstrings de `reglas_obra_cero.py` (módulo y `_destino`) siguen siendo
ciertos con D19 (hablan de la omitida antes de resolverse); no se tocan.

### Riesgos y puntos para el humano

- **Consumidores de la omitida.** Hasta hoy una omitida nunca llevaba
  partida ni `destino="postventa"`. En `registro_pipeline.py` hay lecturas
  de `a.destino` para repartir acciones entre la obra normal y la de
  postventa (`destino_pv if a.destino == "postventa"`, l. ~765 y ~1137) y
  varias de `a.paride`; si alguna no filtra por `accion`, una omitida de
  postventa cambiaría de obra en la respuesta o el modal. T22 obliga a
  comprobarlo y a PARAR si algo cambia (`registro_pipeline.py` no se toca).
- **Vinculados**: si las `AccionVinculado` omitidas «sigue al trabajador»
  copian `destino`/`paride` del titular, D19 también estrecha su cobertura.
  Es coherente con la decisión, pero T22 lo hace constar.
- **Mutación**: rigor crítico. La campaña completa tardó 4837 s; T22 pide
  reejecutarla o, si el líder la acota, RM4 a mano sobre lo cambiado. Lo
  decide el líder.
