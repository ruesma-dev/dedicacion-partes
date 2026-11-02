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

## 2026-10-30 · D19 ampliada tras la parada del implementer en T22 (4)

El humano, vía el líder, el 2026-10-30:

1. **Aceptado** como parte de D19 («Aceptar»): con una `Postv-` omitida tras
   resolver su partida, el modal (`pintarModalPreflight`, también sus
   vinculados omitidos «sigue al trabajador») muestra «Postventa» en
   Destino; la respuesta del preflight (`asdict(a)`) publica `destino`,
   `paride` y `partida_cod`, y `clave_conflicto` lleva `|<paride>` en vez de
   `|0`; también cambia el `print` de `prueba_escritura_porcentajes.py`.
2. **Asimetría aceptada** sin cambio de código («Dejarlo así»): el
   `AccionVinculado` omitido copia `destino` del titular pero no `paride`
   (0), así que sigue cubriendo todas las partidas de postventa (dirección
   segura). `reglas_vinculados.py` no se toca.

Recogido en design §6.1 (vinculados) y §12 D19 (efectos y citas),
requirements §6 (D19), `ARCHITECTURE.md#regla-obra-cero` (vinculado omitido)
y T22: en el punto (4) esos lectores ya no paran (cualquier otro sí) y el
nuevo (4 bis) pide un test que fije «Postventa» para la omitida tras
resolver y «Obra» para la omitida antes. Para seguir en 250/250 se
reenvolvieron §6.2, §6.4, §7 y §12 D19 a líneas más largas, sin quitar
texto. Tamaños: requirements 149/150, design 250/250.

## 2026-11-02 · Enmienda tras la MANUAL T18: ventana de una tabla y D12 revisada

Pedida y aprobada por el humano vía el líder (MANUAL T18, ventana «Sincronizar Sigrid»: aceptó
de más porque `solo_sigrid` salía marcada y quitarlas de una en una era inviable).

**Qué cambia en la spec**

- **D12 revisada** («2, ok», 2026-11-02): `solo_sigrid` sale **desmarcada**, como `distinta`;
  las dos se pueden marcar. Reescrita en todos sus sitios: requirements R21, R28, §4 (`[D12]`)
  y §6 (párrafo propio, con la cita antigua «d12, con la casilla marcada por defecto, aunque se
  puede desmarcar» como sustituida); design cabecera y §7; tasks T9 (anotado que T23 la cambia)
  y T18. El «déjalo así» sobre lo ya aceptado en el cuadrante local de 2026-09 consta en §6.
- **R39-R42 nuevos** (requirements §4): una sola tabla (casilla, Trabajador, Obra, Estado,
  Cuadrante, Sigrid, Detalle); orden por cabecera con segunda pulsación que invierte (texto sin
  mayúsculas, numérico con la raya al final, empate estable); filtros de texto en Trabajador,
  Obra y Detalle y desplegable en Estado, combinados, que no tocan casillas; «Desmarcar todas»
  (también las ocultas), «Marcar las visibles» y el botón «Aceptar N marcadas (K ocultas por
  el filtro)». R28: aceptar manda **exactamente** las marcadas, visibles u ocultas, con el
  cuerpo de hoy. Fuera: guardar los filtros al cerrar (cabecera de requirements).
- **design §7 A**: modelo `{filas, orden, filtros}` con `marcada` por fila; se repinta solo el
  `<tbody>` y el botón con dos funciones puras (`filasTraerVisibles`, `textoAceptarTraer`);
  `aceptadasMarcadas()` lee el modelo y no el DOM, porque una fila oculta no se pinta. §3 suma
  `static/css/styles.css`. Api, transfer y contrato no cambian: es presentación (sin cálculo
  de qué se registra en el front).
- **tasks**: **T23** nueva (front, tests primero en `test_f054_traer_front.py`, siete puntos de
  verificación, y `ARCHITECTURE.md` punto 23, que hoy dice «ventana por trabajador» y
  «`solo_sigrid` (marcada, desmarcable)»). **T18** paso 2 rehecho para después de T23: ninguna
  casilla marcada, filtro `0694`, «Marcar las visibles», contador con ocultas, «Desmarcar
  todas», orden invertido y, luego, aceptar solo la entrada de la `MADM`.

**Tamaños.** requirements 150/150, design 250/250. Para caber se reenvolvieron los párrafos a
~96 columnas (sin cambiar texto) y se compactó redacción: en requirements §6, la D19 remite sus
efectos (modal, vinculado omitido) a design §12, donde siguen enteros; en design se acortaron
expresiones sin contenido normativo («No es otro servicio», «> 15 % ⇒ PARA», etc.).

**Puntos para el humano / el líder**

1. **T18 con lo ya aceptado.** Si la entrada de la `MADM` de la 0694 sale `igual` por lo
   aceptado el 2026-11-02 («déjalo así»), el paso de aceptar y «Deshacer» de T18 no se puede
   hacer con ella: T18 dice usar otra `distinta` o `solo_sigrid` y anotarlo. Si el humano
   prefiere deshacer antes ese evento `SIGRID`, que lo diga.
2. **Mutación en rigor crítico.** T23 es solo JS del front; si la campaña de
   `harness.mutacion` no cubre JS, el líder decide si basta con los tests de las dos puras.
3. Detalles que la spec deja al implementer y no cambian el comportamiento: dónde vive el
   modelo (`state` o cierre de `abrirTraerSigrid`) y el marcador visual del orden (▲/▼).
