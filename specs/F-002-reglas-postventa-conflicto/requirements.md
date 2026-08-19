<!-- specs/F-002-reglas-postventa-conflicto/requirements.md -->
# F-002 · Requisitos — Fijar las reglas P4 y P5

> **Rigor `critico`.** Estas dos reglas deciden qué se BORRA y qué se ESCRIBE
> en los partes de trabajo de Sigrid. Hasta que estén cerradas **e
> implementadas** no se escribe en producción (`OBRA_PRUEBAS_FORZAR` se queda
> a `true`).

> **Versión 2 de esta spec (2026-08-19).** La v1 se escribió con D1 y D2
> abiertas. Las dos están **cerradas** (§2) y la Fase 1 (T1–T5) está
> implementada y aprobada (`progress/impl_F-002.md`,
> `progress/review_F-002_fase1.md`). Lo que cambia respecto a la v1 está
> resumido en `progress/spec_F-002_v2.md`.

## Contexto

El repositorio enunciaba las reglas P1–P5 en **cinco sitios distintos**, y en
dos de ellas los enunciados **se contradecían**. La feature no podía
decidirse leyendo el código: las dos versiones de cada regla eran defendibles
y la respuesta la tenía Administración.

Hoy la respuesta está dada. Y no confirma ninguna de las dos versiones de P4:
la trae una **tercera**, que parte P4 en dos reglas separadas —**identidad**
(qué es la misma línea) y **capacidad** (cuánta jornada cabe en un parte)— de
las cuales la segunda **no existe en el repositorio**.

Servicio afectado: **`dedicacion-transfer`** (las reglas P1–P5 viven ahí) más
`docs/ARCHITECTURE.md` en la raíz. Ni la API ni el front se tocan; por qué,
en `design.md` §1.

---

## 1. Requisitos EARS

### 1.1. Fuente única de verdad

- **R1.** El sistema debe declarar las reglas P1–P5 **una sola vez**, en la
  sección «Semántica de dominio imprescindible» de `docs/ARCHITECTURE.md`,
  con un ancla estable por regla (`#regla-p1` … `#regla-p5`), más
  `#regla-conflicto` (identidad) y `#regla-capacidad` (la regla nueva).

- **R2.** El sistema debe hacer que el README de `dedicacion-transfer` y los
  docstrings de `reglas_porcentajes.py`, `registro_pipeline.py`,
  `partida_resolver.py` y `registro_models.py` **remitan** a esas anclas en
  lugar de reenunciar la regla con palabras propias.

- **R3.** SI un fichero del repositorio distinto de `docs/ARCHITECTURE.md`
  vuelve a enunciar el contenido normativo de P4 o P5 (frases marcadas como
  prohibidas en el test de fuente única), ENTONCES la suite debe fallar.

- **R4.** El sistema debe registrar en `docs/ARCHITECTURE.md`, junto a cada
  regla confirmada, **la fecha y de quién sale** la confirmación, en un
  formato reconocible (`Confirmado por Administración el AAAA-MM-DD ·
  <interlocutor>`), y en el punto 5 debe además referenciar el volcado
  `progress/sigrid_F-002.md` que la corrobora.

- **R5.** El sistema no debe citar el valor literal del código de la obra de
  postventa en ningún docstring ni comentario: debe referirse al ajuste
  `POSTVENTA_OBRA_COD`. El único sitio donde vive el valor es `.env` /
  `.env.example` / el defecto de `config/settings.py`.

### 1.2. Reglas no en disputa, fijadas por test

- **R6.** CUANDO el recurso de una línea no tiene ningún código de hora `M*`
  en `reshor`, el sistema debe omitir la línea con motivo, sin error (P1).

- **R7.** CUANDO una línea se escribe, el sistema debe fijar `fec` al último
  día natural del mes del periodo, sea cual sea el día de captura (P2).

- **R8.** CUANDO una línea se escribe, el sistema debe enviar `can` = el
  porcentaje **sobre 1**, `pre` = el importe mensual del recurso en `reshor`
  y `tot = round(can × pre, 2)` (P3).

- **R9.** SI el porcentaje de una línea no está en el intervalo `(0, 1]`,
  ENTONCES el sistema debe omitirla con motivo y no escribir nada.

- **R10.** CUANDO ya existe en Sigrid una línea con la `synckey`
  `porcentajes:{registro_id}` de una línea de entrada, el sistema debe
  marcarla `ya_registrado` y no duplicarla.

- **R11.** MIENTRAS `OBRA_PRUEBAS_FORZAR` esté activo, el sistema debe
  escribir en la obra de pruebas con la marca de `MARCA_PRUEBAS` en `tex`,
  pero debe seguir resolviendo el destino de imputación de la postventa
  contra la obra de postventa **real**.

- **R12.** DONDE `POSTVENTA_REGISTRAR` esté desactivado, el sistema debe
  omitir toda línea con `es_postventa` con motivo explícito y no escribirla
  en la obra normal.

- **R13.** SI dos o más conflictos confirmados contienen la **misma** línea
  existente de Sigrid, ENTONCES el sistema debe emitir **un único** borrado
  para ese `hmores.ide` y contarlo una sola vez en `borradas`.

  > **Ojo, su escenario cambia con la Regla A.** La ruta por la que este
  > defecto se materializaba —dos líneas pendientes del mismo recurso con
  > partidas distintas chocando ambas contra la misma línea previa— **deja de
  > existir** cuando la partida entra en la identidad (R20): dos pendientes
  > con partidas distintas ya no pueden casar con la misma línea. La
  > salvaguarda se queda como tal y su test se reexpresa (ver §1.6 y
  > `design.md` §3.5).

- **R14.** El sistema debe derivar la clave de conflicto y el criterio de
  choque de **una sola declaración** (`CAMPOS_CLAVE`), de modo que no puedan
  divergir: cambiar la tupla debe cambiar las dos cosas a la vez.

### 1.3. Postventa — D1 cerrada

- **R15.** CUANDO no exista en Sigrid ninguna obra con el código de
  `POSTVENTA_OBRA_COD`, el sistema debe omitir **todas** las líneas de
  postventa con el motivo exacto de la obra no encontrada, y el preflight
  debe devolver ese motivo en la acción (visible, no silencio).

- **R16.** CUANDO una línea de postventa se escribe, el sistema debe fijar
  `hmores.paride` al `ide` de una **partida hoja activa** del presupuesto de
  la obra de postventa; SI el nodo que casa no es hoja activa, ENTONCES debe
  omitir la línea con motivo en vez de escribirla.

- **R17.** El sistema debe resolver automáticamente la partida de postventa
  dentro del **mismo universo** de nodos que publica
  `preflight.partidas_postventa` (hojas activas), de forma que el desplegable
  del front y el automático no puedan apuntar a universos distintos.

- **R18.** El sistema debe emparejar la obra original con su partida de
  postventa por **código exacto normalizado** (`cod` de `obrparpar` frente al
  código de la obra), y solo si no hay coincidencia exacta debe aplicar las
  cascadas (empieza por → código en la descripción → nombre), todas ellas
  sobre hojas activas. En particular, `0656` y `656` son códigos **distintos**
  y no deben casar entre sí.

- **R19.** El sistema debe elegir la partida de postventa de forma
  **determinista**: dos ejecuciones sobre el mismo presupuesto deben devolver
  la misma partida, sin depender del orden en que Sigrid devuelva las filas.

### 1.4. Regla A · identidad — D2 cerrada

- **R20.** El sistema debe considerar que una línea ya existente en Sigrid es
  la **misma línea** que la que va a escribir si, y solo si, coinciden
  recurso, periodo, código de hora **y partida**, sea cual sea el destino
  (obra normal o postventa).

- **R21.** SI la partida de la línea existente difiere de la de la línea que
  se va a escribir, ENTONCES el sistema no debe emitir conflicto de pisado
  para ella ni borrarla: son dos líneas legítimas distintas.

- **R22.** CUANDO la línea existente lleve una `synckey` de esta misma
  ejecución, el sistema no debe tratarla como conflicto (lo que escribimos
  nosotros no choca con nosotros mismos).

### 1.5. Regla B · capacidad — regla NUEVA

- **R23.** CUANDO el sistema prepara la escritura de un parte, debe calcular
  para cada recurso la suma de jornada del mes = Σ `can` de las líneas `M*`
  del recurso que ya están en ese parte y **no** se van a pisar y **no** son
  de esta misma ejecución, + Σ `can` de las líneas que va a escribir.

- **R24.** El sistema debe contar en esa suma **todas** las líneas cuyo
  código de hora empiece por `M`, sea cual sea el código concreto, y **no**
  debe contar las líneas con código no mensual.

- **R25.** SI la suma de un recurso supera `1` en más de la tolerancia
  `0,00005`, ENTONCES el sistema debe emitir un conflicto de **sobrecarga**
  con su detalle: las líneas ya existentes que ha contado, la suma existente,
  la suma que se añade, la suma total y el exceso.

- **R26.** SI la suma no supera `1 + 0,00005`, ENTONCES el sistema **no** debe
  emitir conflicto de sobrecarga (una jornada de exactamente `1,0` repartida
  entre varias partidas es legítima y se escribe sin preguntar).

- **R27.** El sistema debe distinguir un conflicto de sobrecarga de uno de
  pisado por un **campo propio** del conflicto y por una **clave con prefijo
  propio**, de modo que confirmar uno no confirme el otro.

- **R28.** MIENTRAS un conflicto de sobrecarga no esté confirmado, el sistema
  no debe escribir ninguna de las líneas que lo provocan, y debe listarlas en
  `omitidas` con su motivo.

- **R29.** CUANDO se confirma un conflicto de sobrecarga, el sistema debe
  escribir sus líneas y **no debe borrar ninguna** línea de Sigrid por causa
  de ese conflicto.

- **R30.** CUANDO un mismo recurso tenga a la vez conflicto de pisado y
  conflicto de sobrecarga, el preflight debe devolver **los dos**, el de
  pisado antes que el de sobrecarga, y la escritura debe exigir la
  confirmación de **ambos** para escribir la línea.

- **R31.** El sistema debe calcular la sobrecarga suponiendo que **todos** los
  pisados propuestos se confirman (la línea pisada sale del cómputo y entra la
  nueva), porque cualquier otra combinación escribe estrictamente menos.

### 1.6. Seguridad del borrado

- **R32.** SI un conflicto de pisado está confirmado pero ninguno de sus
  registros llega a escribirse —por ejemplo, porque los bloquea un conflicto
  de sobrecarga sin confirmar—, ENTONCES el sistema **no** debe emitir su
  borrado: no se borra nunca sin escribir el sustituto.

### 1.7. Compatibilidad del contrato

- **R33.** El sistema debe mantener el contrato HTTP `preflight` / `ejecutar`
  consumible por un cliente que **ignore** los campos nuevos del conflicto:
  los campos existentes de `Conflicto` conservan nombre, tipo y semántica, y
  los nuevos tienen valor por defecto. Un front que no lea el campo de motivo
  sigue pintando la casilla de confirmación y sigue pudiendo confirmar.

---

## 2. Decisiones tomadas

> Esta sección era, en la v1, la lista de preguntas abiertas. Ahora es el
> registro de lo decidido. Cada decisión trae **fecha**, **quién decide** y
> **evidencia**.

### D1 — P5: dónde y contra qué se imputa la línea de postventa

**Estado: CERRADA · 2026-08-19 · decide el humano del proyecto, corroborado
con la lectura real C2 contra Sigrid** (volcado íntegro en
`progress/sigrid_F-002.md`).

| Punto | Decisión |
|---|---|
| D1.1 · código de la obra | **`POSTV2`**, siempre, y la obra está viva siempre. El `'postventa-2'` que estaba en el docstring de `reglas_porcentajes.py` era **falso**; se retiró en T5 y hay test que impide que vuelva. |
| D1.2 · partida o capítulo | **PARTIDA HOJA**, nunca un capítulo ni una partida normal de ejecución. |
| D1.3 · cómo se empareja | Por **código exacto**. En la base los campos van separados (`cod = '0610'`, `res = 'COLEGIO ALEGRA'`); lo que se ve junto en la interfaz de Sigrid es la concatenación de los dos. `resolver_postventa` acierta hoy con su primer paso (exacto) y **no** hay que cortar por el primer espacio. |

**Evidencia (C2, 2026-08-19, `POST /api/sql/read`, base `ruesma`, 248 filas,
`truncated: false`).** El presupuesto de `POSTV2` tiene 225 hojas y 23
capítulos; las **84 partidas de obra son todas hojas** (`n_hijos = 0`) y
cuelgan de `CD · COSTES DIRECTOS`.

**Defecto confirmado que sigue abierto.**
`application/services/partida_resolver.py`, en `resolver_postventa`:

```python
hojas = [n for n in nodos.values() if n.activa]
```

La variable se llama `hojas` pero **no filtra por hoja**, así que la cascada
puede devolver un **capítulo**, que nunca es destino válido (R16) y que el
desplegable del front nunca ofrece (R17). Con los datos de hoy no se
materializa —ningún capítulo de `POSTV2` tiene código de obra—, pero hay
capítulos con código numérico (`3`, `4`, …, `11`) y el riesgo es real. Se
cierra en esta feature (T9).

**Dato para Administración, no para el código.** Cuelgan de la **raíz** del
presupuesto (no de `CD`) cuatro partidas duplicadas sin el cero inicial:

| Suelta en la raíz | Ya existe bajo `CD` | Descripción |
|---|---|---|
| `656` | `0656` | 33+34 VIVIENDAS TOMARES |
| `664` | `0664` | 76 VIVIENDAS EN LOS GUINDOS (MÁLAGA) |
| `680` | `0680` | APARTHOTEL ARGIS C/ CAVANILLES |
| `693` | `0693` | 54 VIV. «CELERE BAVIERA GOLF» EN VÉLEZ-MÁLAGA |

No rompen nada: `text_match.normalize_code` **no** quita ceros a la
izquierda, así que `0656` y `656` son códigos distintos y la obra `0656` casa
siempre con su partida bajo `CD` (eso es lo que fija R18). Son ruido de
presupuesto y conviene que Administración lo sepa (T6).

### D2 — P4: qué cuenta como conflicto y cuánta jornada cabe

**Estado: CERRADA · 2026-08-19 · decide el humano del proyecto.**

La respuesta **no es** ninguna de las dos versiones que se enfrentaban en el
repositorio. Es la tercera opción que la v1 de esta spec contemplaba como «la
que invalida el diseño»:

> Pueden convivir varias líneas `M*` del mismo trabajador en el mismo parte y
> mes con **partidas distintas**, pero la **suma** de sus cantidades no puede
> pasar de **1** (el 100 % de la persona).

Eso parte la vieja P4 en dos reglas separadas:

**Regla A · identidad (R20–R22).** La identidad de una línea en el parte es
recurso + mes + código de hora + **partida**, también en la obra normal.
Nuestra línea solo pisa una existente si coinciden los cuatro. Si la partida
difiere, no es la misma línea y no se toca.

**Regla B · capacidad (R23–R31).** Por trabajador y parte, la suma de la
jornada del mes no puede pasar de 1. Si se pasa, hay **sobrecarga**.

- **Qué hace el sistema: AVISAR Y DEJAR CONFIRMAR.** El preflight lo enseña
  con su detalle y **no se escribe** hasta que el humano confirma esa línea
  concreta. Sin confirmación, se omite y queda listada como omitida con su
  motivo.
- **Cómo viaja: REUTILIZANDO EL MECANISMO DE CONFLICTO**, con un motivo
  propio que lo distinga de un pisado. Por eso F-002 se queda dentro de
  `dedicacion-transfer` y **no toca** `dedicacion-api` ni `dedicacion-front`.
  Lo que se pierde por no tener un tipo propio está escrito, sin adornos, en
  `design.md` §8.
- **Tolerancia: `0,00005`.** No es un número redondo por elección: es el
  equivalente exacto, en escala 0–1, de la épsilon que ya usa el cuadrante en
  `services/dedicacion-api/domain/estados.py` (`_EPSILON = Decimal("0.005")`
  sobre escala 0–100). El objetivo es que el front y Sigrid **no discrepen en
  el último decimal**: un cuadrante que la API da por `OK` no puede
  convertirse aquí en una sobrecarga. Cambiarla por un número redondo rompe
  esa alineación.

**Alcance de la Regla B: un parte, es decir, una obra.** El transfer se
invoca por obra (`dedicacion-api/application/registro_sigrid.py` agrupa por
obra), así que la suma que puede comprobar es la de ese parte. El 100 % del
trabajador **entre todas sus obras** es otra regla, la del cuadrante, y vive
en la API (`domain/estados.py`, punto 4 de `docs/ARCHITECTURE.md`). Las dos
tienen que compartir tolerancia, y por eso comparten número.

---

## 3. Consultas de lectura contra Sigrid — estado

> Todas van contra `sigrid-api` (`POST /api/sql/read`, base `ruesma`), son de
> **solo lectura** y las lanza el humano.

| Consulta | Estado | Motivo |
|---|---|---|
| **C1** · qué obras existen con código de postventa | **No ejecutada. Sin motivo ya.** | Su pregunta —cuál es el código— la contestó el humano (`POSTV2`, siempre) y la corrobora C2, que devolvió el presupuesto de esa obra con HTTP 200. Ejecutarla no cambiaría ninguna decisión. |
| **C2** · árbol del presupuesto de `POSTV2` | **Ejecutada** el 2026-08-19 | Volcado en `progress/sigrid_F-002.md`. Es la evidencia de D1. |
| **C3** · líneas `M*` que ya existen en los partes de `POSTV2` | **No ejecutada. Sigue teniendo valor.** | Ya no decide D1.2, pero es la única forma de saber **cuánta sobrecarga real** va a aflorar la Regla B el primer día en la obra de postventa. Diagnóstico, no bloqueante. |
| **C4** · recursos con más de una línea `M*` en el mismo parte | **No ejecutada. Sin motivo ya.** | Era la consulta que iba a decidir D2, y **perdió su motivo cuando el humano contestó D2** con la tercera opción. Conserva un valor residual de calibración (cuántos partes históricos ya superan 1), que no condiciona ningún requisito. |
| **C5** · detalle de las líneas de un parte concreto | **No ejecutada. Sigue teniendo valor.** | Es la lupa de C3: distingue un reparto legítimo entre partidas de un duplicado histórico. Útil también para preparar la verificación manual T13. |

Ninguna de las cuatro pendientes bloquea el cierre de la feature. Si el
humano quiere lanzar C3 y C5, el volcado va a `progress/sigrid_F-002.md` con
su fecha y quién la lanzó.

### Recordatorios operativos de las consultas

- Todas son **SELECT**, base `ruesma`, con marcadores `?`: nunca concatenar
  valores (`docs/CONVENTIONS.md` § SQL, `azure-apps/sigrid_api.md` §5.2).
- El **corte del balanceador está en 230 s** y no se puede subir. Ninguna
  consulta de aquí pide más de 180 s.
- `max_rows` va **siempre explícito**: el defecto de la pasarela truncaría en
  silencio.
- Si la respuesta trae `truncated: true`, **el resultado está incompleto**:
  hay que paginar con `OFFSET / FETCH` y `ORDER BY`.
- El volcado íntegro de cada consulta ejecutada se guarda en
  `progress/sigrid_F-002.md` con la fecha y quién la lanzó. Sin ese volcado,
  la decisión no es trazable.

El SQL literal de C1, C3, C4 y C5 no se repite aquí: está en el historial de
la v1 de esta spec (`git log -p specs/F-002-reglas-postventa-conflicto/`).
Duplicarlo en un documento que ya no las necesita sería otra fuente de verdad
que mantener.

---

## 4. Trazabilidad requisito → test

Todos los ficheros son de `services/dedicacion-transfer/tests/`. Todos los
tests corren **sin red y sin BBDD**, con las fixtures parametrizables de
`conftest.py` (`ClienteFalso`, `SettingsFalso`, `linea()`, `linea_previa()`).

| Req | Test | Fichero | Estado |
|---|---|---|---|
| R1, R3, R5 | `test_f002_r1_*`, `test_f002_r3_frases_prohibidas_fase1`, `test_f002_r5_*` | `test_f002_fuente_unica.py` | **pasa** (T5) |
| R2 (P1–P3) | `test_f002_r2_el_readme_remite_a_las_anclas` | `test_f002_fuente_unica.py` | **pasa** (T5) |
| R1 (`#regla-capacidad`), R2 y R3 (P4/P5) | `test_f002_r2_los_docstrings_remiten_p4_p5`, `test_f002_r3_frases_prohibidas_p4_p5` | `test_f002_fuente_unica.py` | `xfail(strict)` → **T8** |
| R4 | `test_f002_r4_procedencia_fechada` | `test_f002_fuente_unica.py` | `xfail(strict)` → **T7/T8** |
| R6 | `test_f002_r6_*` (3) | `test_f002_reglas.py` | **pasa** (T2) |
| R7 | `test_f002_r7_*` (7) | `test_f002_reglas.py` | **pasa** (T2) |
| R8 | `test_f002_r8_*` (3) | `test_f002_reglas.py` | **pasa** (T2) |
| R9 | `test_f002_r9_*` (5) | `test_f002_reglas.py` | **pasa** (T2) |
| R10 | `test_f002_r10_*` (3) | `test_f002_pipeline.py` | **pasa** (T4) |
| R11 | `test_f002_r11_*` (3) | `test_f002_pipeline.py` | **pasa** (T4) |
| R12 | `test_f002_r12_*` (3) | `test_f002_reglas.py` | **pasa** (T2) |
| R13 | `test_f002_r13_borrado_unico_por_ide` + 3 controles | `test_f002_pipeline.py` | **pasa** (T4) · **se reexpresa en T12** |
| R14 | `test_f002_r14_*` (17) | `test_f002_conflicto.py` | **pasa** (T4) · dos se reescriben en T10 |
| R15 | `test_f002_r15_obra_postventa_no_encontrada`, `..._el_motivo_llega_al_preflight` | `test_f002_postventa.py` | **T9** |
| R16 | `test_f002_r16_solo_partida_hoja_activa`, `..._un_capitulo_no_es_destino`, `..._una_hoja_inactiva_no_es_destino` | `test_f002_postventa.py` | **T9** |
| R17 | `test_f002_r17_el_automatico_y_el_desplegable_comparten_universo` | `test_f002_postventa.py` | **T9** |
| R18 | `test_f002_r18_casado_por_codigo_exacto`, `..._0656_no_casa_con_656`, `..._la_cascada_solo_actua_sin_exacto` | `test_f002_postventa.py` | **T9** |
| R19 | `test_f002_r19_la_eleccion_no_depende_del_orden_de_las_filas` | `test_f002_postventa.py` | **T9** |
| R20 | `test_f002_r20_la_partida_entra_en_la_identidad[obra]`, `[postventa]`, `..._los_cuatro_campos_deciden` | `test_f002_conflicto.py` | **T10** |
| R21 | `test_f002_r21_otra_partida_no_es_conflicto`, `..._no_se_borra_la_linea_de_otra_partida` | `test_f002_conflicto.py`, `test_f002_pipeline.py` | **T10** |
| R22 | `test_f002_r22_lo_nuestro_no_choca_con_nosotros_mismos` (reubicado de R14) | `test_f002_conflicto.py` | **T10** |
| R23 | `test_f002_r23_suma_existentes_mas_nuevas`, `..._la_linea_pisada_no_se_cuenta_dos_veces`, `..._las_mias_no_distorsionan`, `..._una_ya_registrada_cuenta_una_vez` | `test_f002_capacidad.py` | **T11** |
| R24 | `test_f002_r24_cuenta_cualquier_codigo_mensual`, `..._no_cuenta_las_no_mensuales` | `test_f002_capacidad.py` | **T11** |
| R25 | `test_f002_r25_sobrecarga_emite_conflicto`, `..._con_su_detalle_numerico` | `test_f002_capacidad.py` | **T11** |
| R26 | `test_f002_r26_justo_uno_no_es_sobrecarga`, `..._la_tolerancia_es_la_del_cuadrante` | `test_f002_capacidad.py` | **T11** |
| R27 | `test_f002_r27_la_clave_de_sobrecarga_no_colisiona`, `..._el_motivo_distingue` | `test_f002_capacidad.py` | **T11** |
| R28 | `test_f002_r28_sin_confirmar_no_se_escribe`, `..._queda_listada_en_omitidas_con_motivo` | `test_f002_pipeline.py` | **T12** |
| R29 | `test_f002_r29_confirmada_se_escribe_y_no_borra_nada` | `test_f002_pipeline.py` | **T12** |
| R30 | `test_f002_r30_pisado_y_sobrecarga_a_la_vez`, `..._el_orden_es_pisado_primero` | `test_f002_capacidad.py` | **T11** |
| R31 | `test_f002_r31_la_suma_supone_los_pisados_confirmados` | `test_f002_capacidad.py` | **T11** |
| R32 | `test_f002_r32_no_se_borra_si_no_se_escribe` | `test_f002_pipeline.py` | **T12** |
| R33 | `test_f002_r33_el_conflicto_serializa_los_campos_de_siempre` | `test_f002_capacidad.py` | **T11** |
| Verificación contra Sigrid real | **MANUAL (humano)** | — | ver `tasks.md` **T13, T14** |
</content>
</invoke>
