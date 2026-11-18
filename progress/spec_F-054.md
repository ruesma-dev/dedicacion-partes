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

## 2026-11-03 · Segunda enmienda tras la MANUAL T18: cabecera estándar, «No se traen» en tabla y motivos con códigos (T24-T25, D20)

Pedida por el humano vía el líder al probar T18 paso 2 (mes 01/2026): tres cosas, y «hazlo
todo dentro de la feature» (D20). Solo lectura de código; ninguna lectura contra Sigrid. Sin
tocar `progress/current.md`, `harness/features.json` ni los `.env`.

**Qué cambia en la spec**

- **requirements**: R43 (cabecera estándar `.filterable` en las dos tablas, «Limpiar» por
  tabla, Escape vacía el filtro de texto; R40-R42 igual), R44 («No se traen (N)», N = líneas,
  tabla Parte/Obra/Recurso/Líneas/Motivo con orden y filtros; iguales agrupadas con «×K»), R45
  (`no_traidas` gana `recurso_cod`/`recurso_nombre`; sin ellos, el `recurso_ide`), R46 (motivos
  con códigos, `ide` de reserva), R47 (el preflight del registro y su contrato no cambian). §6:
  D20 con la cita. R29 remite a R39-R46.
- **design**: §1 límite de T24-T25; contratos (`motivo` con códigos; `no_traidas` + `recurso_*`);
  §3 fila T25; §4.2 (motivos de postventa y argumentos opcionales de `partida_var_de`); §5.4
  nuevo (`ObraRepository.codigos`, `_obras`, `_nombre_obra`, `NoTraida`); §7 bullet T24; §9, §10
  (`universo_var.py` solo `partida_var_de`; `use_cases.py` y `test_f039_*` no se tocan), §11.
- **tasks**: T24 (front) y T25 (api y transfer), tests primero; T18 paso 2 al día (cabecera
  estándar, Escape, «Limpiar», tabla «No se traen» con «×K» y códigos, con los casos de
  01/2026); T20 con la nota de contrato; cabecera de la lista cerrada (no crece).

**Límite de servicio.** Front: presentación (cabecera, agrupar idénticas, pintar el código del
trabajador): no decide qué se registra. Api: el `cod` de las obras de su base (hoy pone
`str(ide)` en `_obras` a las que existen sin salir en el periodo: de ahí «la obra 2565541 no se
ofrece normal»), `<obra>-<partida>` para la VAR fuera de la base y el código y nombre del
trabajador (toda `no_traida` tiene uno del maestro: R14). Transfer: los códigos de partida
(`partida_cod`, ya en la lectura de §4.1) y de obras (`codigo`, ya en el cuerpo que manda la
api) en los motivos que construye. Ninguna lectura nueva en ningún servicio.

**Consumidores revisados** (grep en los tres servicios):

- `MOTIVO_NO_OFRECIBLE`, `MOTIVO_NO_EN_BASE`, `MOTIVO_OTRA_EMPRESA`, `_nombre_obra`, `NoTraida`:
  solo `domain/traer_sigrid.py` y tests de F-054 (`test_f054_comparar.py`). Los textos «no se
  ofrece como normal» de `test_f029_completar.py` son de otro mensaje (F-029), no cambian.
- `ObraRepository.existen`: también `use_cases.py` (l. ~1002) ⇒ no se cambia; se añade
  `codigos`. Dobles afectados: solo los `SimpleNamespace` de `test_f054_aceptar.py` (l. ~293 y
  ~599) y `test_f054_mutacion.py` (l. ~89); los `_Obras` de `test_f024`/`test_f025` no pasan por
  `TraerDeSigrid`.
- `MOTIVO_PV_NINGUNA`/`_VARIAS`: solo `porcentajes_existentes.py` y tests de F-054
  (`test_f054_traduccion.py`, `test_f054_mutacion.py` del transfer).
- `partida_var_de` y `MOTIVO_VAR_*`: también **`registro_pipeline.py` l. ~680 (preflight VAR,
  F-039 R6)**, que llega al **modal del registro**, y `test_f039_preflight_var.py` (cuatro
  asserts con `MOTIVO_VAR_*.format(paride=<ide>, obra=<ide>…)`). Por eso los argumentos nuevos
  son **opcionales**: sin ellos, el texto de hoy; el preflight no los pasa (R47) y
  `test_f039_preflight_var.py` no cambia. `test_f054_mutacion.py` espía `partida_var_de`: si el
  espía no acepta los `kwargs` nuevos, se ajusta (es de F-054).
- Front: `no_traidas` solo lo pinta `pintarTraerSigrid`. Los selectores de T23 (`ordenable`,
  `filtro-traer`, `type="search"`, `#traer-titulos`/`#traer-filtros`) solo los fija
  `test_f054_traer_front.py`. **Ojo**: `test_f050_r29_…` exige que todos los `<select` de
  `app.js` estén en `pintarTraerSigrid`: el de Estado no se puede sacar a una función auxiliar
  (anotado en T24 y en la cabecera de tasks).
- Contrato: `/api/porcentajes/existentes` mismos campos (solo cambia el texto de `motivo`);
  `traer-sigrid` gana dos campos en `no_traidas`, consumidos solo por el front. `azure-apps/
  dedicacion.md` hoy no describe ninguno de los dos (grep sin resultados): T20 lo deja anotado.

**Tamaños.** requirements 150/150, design 250/250. Para caber, sin quitar contenido normativo:
reenvuelto a ~102-104 columnas; requisitos cortos unidos en el mismo punto (R3, R5, R14, R16,
R17, R20, R22, R24, R26, R30, R32, R34, R37, R45, R47, como ya estaban R7, R9, R11, R12);
historia de la cabecera de requirements remitida a §6 (las fechas siguen allí); en design, sin
línea en blanco tras los `###`, §12 D16-D18 en un párrafo con las razones largas resumidas
(detalle: la sección del 2026-10-29 de este fichero) y frases acortadas en §5.2, §6.2-§6.4, §9-§11.
En R30 se quitó «2026-09» (el mes de la prueba lo fija T18, que ahora admite el de la prueba).

**Puntos para el humano / el líder**

1. **Motivos del preflight del registro (fuera de la ventana).** Con R47 el modal del registro
   sigue diciendo «partida VAR 417002 …» (el `ide`). Llevar los códigos también ahí es pasar
   `partida_cod`/`obra_cod` desde `registro_pipeline.py` (el código de la partida VAR no está en
   `CatalogoVar` si queda fuera del universo: habría que guardar los códigos de todo el
   presupuesto ya leído) y cambiaría `test_f039_preflight_var.py`. No se ha diseñado: si el
   humano lo quiere, es otra enmienda (o feature) y ese test entra en la lista cerrada.
2. **N de «No se traen (N)».** Se ha mantenido N = líneas de Sigrid (como hoy); las filas son
   grupos. Si el humano prefiere N = filas, es un cambio de una palabra en R44 y en T24.
3. **Columna «Líneas».** «×K» va en una columna propia (vacía si K = 1, ordenable, sin filtro),
   antes de Motivo, para que «Limpiar» quede junto al filtro de Motivo. Alternativa: pegarlo al
   final del motivo; se descartó porque mezclaría el «×K» con el filtro de texto.
4. **Mutación.** T24 es JS: como en T23, mutación manual de `app.js`; T25 entra en la campaña de
   `harness.mutacion` (api y transfer). El líder decide si la acota.
5. Lo ya aceptado en local el 2026-11-02 sigue con «déjalo así»; T18 paso 2 admite el mes de
   la prueba (01/2026) y cita sus casos (`PT26/00028`, `POSTV2`, `0708`/`2565541`).

### 2026-11-03 bis · Decisiones del humano sobre los puntos 1-3 (D21) y T26

Citas (vía el líder): punto 1 «trasladalo a codigos legibles, no numeros internos»; punto 2
«filas de tabla»; punto 3 «ok». Recogidas como **D21** (requirements §6).

**Qué cambia**

- **R47** reescrito: el preflight del registro también nombra por código (`MOTIVO_VAR_*`, F-039
  R6, y la partida de postventa no hoja, F-002 R16), sin lecturas nuevas; ningún contrato cambia
  de campos, solo el texto. **R44**: N = filas (grupos). Columna «Líneas»: se queda.
- **design**: §1 (T24-T26, D20-D21; nota de contrato en la entrada de «Contratos»), §3 (fila
  T25-T26 con `registro_pipeline.py`, solo dos motivos; tests ajenos de T26), §4.2 (T26), §6.4
  («B no toca `registro_pipeline.py`»), §10 (`registro_pipeline.py` y `universo_var.py` salvo
  T25-T26; `test_f039_*` ya no está entre los intocables), §11 (D21 fuera de la ventana).
- **tasks**: **T26** nueva (transfer, preflight); lista CERRADA con `test_f039_preflight_var.py`
  citando D21; T24 con «No se traen (2)»; T25 (2) y (5) remiten el preflight a T26; T18 paso 3
  (el modal con motivos por código); T20 (ningún contrato cambia de campos).

**Diseño del código de la partida VAR, sin lectura nueva.** `cargar_catalogo_var` ya lee el
presupuesto entero de la obra VAR (`capitulos_de_obra` → `construir_catalogo`) y se queda solo
con las partidas VAR. T26 guarda además `CatalogoVar.codigos = {ide: cod}` de **todos** los nodos
de esa misma lectura, así `MOTIVO_VAR_FUERA` (y `_OTRA_OBRA`) nombran la partida aunque esté
fuera del universo. La obra, con `origen.codigo`, que el preflight ya tiene.

**Consumidores revisados (preflight)**

- Front: `pintarModalPreflight` pinta el `motivo` tal cual. `app.js` solo compara motivos de
  **conflicto** (`sin_partida`, `sobrecarga`, `pisado`, l. ~3385-3401), que son tipos, no estos
  textos.
- Transfer: `registro_pipeline.py` l. ~1005, ~1189, ~1195 y `registro_vinculados.py` l. ~507-509
  comparan solo esos tipos de conflicto. `clave_conflicto` se construye con `CAMPOS_CLAVE`
  (campos de la acción), **no** con el motivo. **Ningún texto de motivo se usa como clave ni se
  compara.** `MOTIVO_SIGUE_AL_TRABAJADOR.format(motivo=t.motivo)` (F-044, l. ~491) copia el
  motivo del titular al vinculado omitido: el modal lo verá también con código; los tests de
  F-044 (`test_f044_pipeline_vinculados.py` l. ~478, ~544, ~608; `test_f044_reglas_vinculados.py`
  l. ~402) comparan contra `t.motivo` y no cambian.
- Api: guarda el motivo en `sigrid_motivo` (recortado a 300); los códigos no alargan el texto de
  forma relevante.
- Tests: `MOTIVO_VAR_*` solo en `test_f039_preflight_var.py` (cambian los de `FUERA` y
  `OTRA_OBRA`; `SIN_UNIVERSO`, `POSTVENTA` y `OFF` no) y `test_f039_universo_var.py` l. ~253
  (`MOTIVO_VAR_OFF`, sin cambio). `MOTIVO_PARTIDA_PV_NO_HOJA`: `test_f002_postventa.py` l. ~157 y
  `test_f025_universo_postventa.py` l. ~88 (mandan `partida_cod` `11` y `0713`: su texto
  esperado cambia) y `test_f050_modal_registro.py` l. ~379/414 (formatea la constante con
  `paride=…` y la pinta: **no cambia** porque los marcadores se mantienen). F-062, F-064 y F-068:
  ningún test usa estos motivos (grep sin resultados).
- Otros motivos del preflight con `ide`: `MOTIVO_LINEA_CAMBIADA` y `MOTIVO_INC_CAMBIADA`
  («línea {ide}») nombran una línea de Sigrid, que no tiene código: fuera. `MOTIVO_PARTIDA_NO_HOJA`
  y `MOTIVO_ELEGIDA_NO_VALIDA` ya usan código; `MOTIVO_EMPRESA_OBRA`, el `cod` de la obra.

**Tamaños.** requirements 150/150, design 250/250 (compactado: notas de contrato juntas en la
entrada de «Contratos», frases de §1, §5.4, §6.3, §9-§11 acortadas; sin quitar requisitos).

**Puntos para el humano / el líder**

1. **Dos motivos VAR siguen con `ide`** en el preflight: `MOTIVO_VAR_POSTVENTA` (línea de
   postventa con `var_paride`: el preflight la omite sin leer la obra VAR, y `test_f039` exige que
   no la lea) y `MOTIVO_VAR_SIN_UNIVERSO` (no hay obra VAR ni presupuesto). Sin lectura nueva, la
   única vía sería que la api rellene el `partida_cod` (campo que ya existe en la línea de la
   petición) en las líneas VAR, sacándolo del `cod` de la entrada (`VAR-29` → `29`): no cambia
   campos, pero sí lo que manda la api. No se ha diseñado; si se quiere, se añade a T26.
2. **`MOTIVO_PARTIDA_PV_NO_HOJA` dentro de T26**: lo he metido por «códigos legibles» (nombra la
   partida por `ide`) y por eso entran en la lista cerrada `test_f002_postventa.py` y
   `test_f025_universo_postventa.py`. Si el humano lo quiere limitado a los `MOTIVO_VAR_*`, se
   quita de T26 y esos dos tests salen de la lista.

### 2026-11-03 ter · «si» a los dos puntos: `partida_cod` en la línea VAR y la postventa no hoja en T26

Cita (vía el líder): «si» a los puntos 1 y 2 de la subsección «bis». Recogido en D21
(requirements §6) y en R47.

**Qué cambia**

- **R47**: el preflight también nombra por código las de `MOTIVO_VAR_POSTVENTA` y
  `MOTIVO_VAR_SIN_UNIVERSO`, porque la api manda en la línea VAR el `partida_cod` (campo que ya
  existe en la línea de la petición) sacado del `cod` de la entrada; sin lecturas ni campos nuevos.
- **design** §1 (T26: la api, el `partida_cod` de la línea VAR), §3 (fila T25-T26 con api
  `registro_sigrid.py` y `domain/obras.py`; tests ajenos de la api), §4.2 (fórmula
  `codigos.get(var_paride) or partida_cod or var_paride`; `partida_de_entrada`; lectores).
- **tasks**: T26 pasa a **api y transfer** con su límite de servicio; lista CERRADA con los dos
  tests de la api y la cita; T20 con la nota para `azure-apps/dedicacion.md` (la api manda algo
  que antes no mandaba).

**Casos de la derivación** (`partida_de_entrada(cod, obra_cod)`, pura, en `domain/obras.py`,
inversa de `codigo_entrada`): `VAR-29` con obra `VAR` → `29`; si el `cod` no empieza por
`<obra>-`, queda vacío o falta `registro_obra_cod` → `None` y la línea va **sin** la clave
(reserva: el transfer nombra el `ide`). La línea VAR hoy **nunca** lleva `partida_cod` (la rama
`o.registro_paride` va antes que la de la elegida en `registro_sigrid.py` l. ~236): el de la
entrada no compite con nada y la elegida de la fila sigue sin mandarse (F-050 R19). En el
transfer, si llegasen los dos, manda el código del presupuesto (`codigos`) y el `partida_cod` es
la reserva.

**Lectores del `partida_cod` de la petición en el transfer** (grep en `application/`,
`interface_adapters/`, `domain/`): solo `registro_pipeline.py` l. ~705 (motivo de
`MOTIVO_PARTIDA_NO_HOJA`) y l. ~711 (`a.partida_cod = linea.partida_cod`), los dos **bajo `if
linea.paride`**, que se evalúa después del `continue` de la rama VAR (l. ~669-688) y que una
línea VAR no trae. El modelo `LineaIn` de `app.py` solo declara el campo opcional, sin
validación cruzada. Los demás `partida_cod` del transfer son de acciones, vinculados
(`registro_vinculados.py`), del catálogo (`reglas_porcentajes.py` l. ~551) o de las líneas
leídas de Sigrid (`reglas_obra_cero.py` l. ~154). **Nada que hoy lo ignore lo usaría para
decidir**: no hay motivo para parar.

**Tests ajenos que cambian** (añadidos a la lista cerrada con la cita «si»):
`services/dedicacion-api/tests/test_f039_registro_var.py::test_f039_r20_la_entrada_lleva_lo_mismo_que_una_linea_normal`
(dict exacto de la línea VAR) y
`services/dedicacion-api/tests/test_f050_partida_linea.py::test_f050_r19_var_igual_aunque_tenga_elegida`
(`"partida_cod" not in ln`). Revisados sin cambio: `test_f055_registro_lote.py::test_f055_r16_var_como_hoy`
(solo `var_paride` y ninguna `propuesta_*`), los asserts de `test_f039_registro_var.py` l. ~82-104
y ~142 (presencia de `var_paride`/`paride`), los de `test_f044_cuadrante_vinculados.py` con dict
exacto (líneas no VAR, de `propuestas_mes`), y los de F-022, F-024, F-026, F-030, F-051 que usan
entradas VAR sin comparar la línea entera. En el transfer, `test_f039_preflight_var.py` ya
estaba en la lista; sus asserts de `SIN_UNIVERSO` y `POSTVENTA` no cambian porque sus líneas no
traen `partida_cod` (los casos con él son tests nuevos).

**Tamaños.** requirements 149/150, design 243/250 (para caber se quitó la línea en blanco tras
los `##`, como ya se hizo con los `###`; R43 y R47 reescritos más cortos, sin quitar contenido).

**Puntos para el humano / el líder**: ninguno nuevo. Recordatorio para T20: la api manda desde
T26 `partida_cod` en las líneas VAR al transfer; contrato de campos igual.

## 2026-11-05 · Tercera enmienda tras la MANUAL T18 paso 2: cabecera fija (T27, R48, D20)

Petición del humano: «el problema que queda es que la cabcera no se mantiene al bajar»; «es la del
modal al sincronizar sigrid»; enmienda dentro de F-054 (D20, «hazlo todo dentro de la feature»).
- **R48** (requirements §4), **T27** (tasks), design §7: solo `styles.css`, `position: sticky` sobre el
  `thead` entero de las dos tablas, acotado con `.modal thead:has(> #traer-titulos)` y
  `#no-traidas-titulos` (los `id` que ya pinta `pintarTraerSigrid`): sin tocar `app.js`, `.filterable`,
  el modal del registro ni el cuadrante (F-070, fuera). T18 paso 2 gana la comprobación al bajar.
- Riesgos: `:has` exige Edge/Chrome ≥ 105; hueco por el padding de `.modal` o transparencia, solo se ven
  en la MANUAL (si salen, el implementer PARA). R29/ARCHITECTURE no cambia: es presentación.
- Tamaños: requirements 150/150 (R48 en una línea; cabecera y §6 recompuestas, sin quitar contenido),
  design 250/250. **Puntos para el humano**: ninguno nuevo.

## 2026-11-06 · T27/R48 rehecha: la ventana en tres zonas (D20)

La primera versión (`ff3d1ac`, `c9611c3`: `thead` sticky dentro de `.modal`) no gustó al probarla: «que
no se quedara tan arriba la cabcera … sino que siga como estaba sin moverse y sea opaca». Propuesta del
líder aprobada el 2026-11-06 («si hazlo asi»), pie fijo incluido.
- **R48** reescrita; **design §7** T27: `pintarTraerSigrid` mete las dos tablas y «No se traen» en
  `div.zona-traer`; `.modal:has(> .zona-traer)` columna flex sin desplazarse, la zona `flex: 0 1 auto;
  min-height: 0; overflow: auto` y `.zona-traer thead` sticky en `top: 0`. Fuera `--modal-pad-top`.
- **Decisión**: la tabla entera dentro de la zona (no su cabecera fuera): el `thead` arranca en su sitio
  y las columnas son las del cuerpo; fuera habría que igualar anchos. Detalle, tests (lista cerrada: los
  `test_f054_r48_*`) y riesgos en **T27** (reabierta, `[ ]`); T18 paso 2 gana la comprobación nueva.
- Tamaños: requirements 150/150 (R27 y §6 recompuestos sin quitar nada), design 250/250.
  **Puntos para el humano**: ninguno nuevo (los márgenes en flex, a ver en la MANUAL).
