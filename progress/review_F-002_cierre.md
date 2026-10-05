<!-- progress/review_F-002_cierre.md -->
# F-002 · Review de CIERRE

**Veredicto: APPROVED** (segunda pasada, 2026-08-20)

> F-002 queda **cerrada**. El código estaba bien desde la Fase 2 y sigue
> intacto tras F-013 y F-008; lo que faltaba era el rastro documental, y en la
> segunda pasada está completo y **dice la verdad**, incluido lo que no salió
> bien y lo que sigue vivo en Sigrid.
>
> Primera pasada: **CHANGES_REQUESTED** por seis puntos, todos de documento.
> Segunda pasada: **los seis corregidos y verificados uno a uno contra los
> ficheros**, no contra el resumen de quien los hizo. F-002 puede pasar a
> `done`.

- **Feature:** F-002 · Fijar las reglas P4 y P5
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`)
- **Rama evaluada:** `dev` — 1ª pasada sobre `392ed0a`, 2ª sobre **`afeeaa0`**
- **Alcance:** cierre de la feature completa, **no** re-review del código
- **Revisor:** subagente `reviewer`

---

## 0 · Resultado de la segunda pasada

`afeeaa0` — «F-002: recupera el volcado de T13 perdido en un merge y pone el
rastro al día». **Cuatro ficheros, ni una línea de código ni de test:**

```
docs/ARCHITECTURE.md                            |  16 +-
progress/review_F-002_cierre.md                 | 458 +++++++++++++++++
progress/sigrid_F-002.md                        |  72 ++++
specs/F-002-reglas-postventa-conflicto/tasks.md |  48 ++-
```

Comprobado con `git show --name-only`: **no toca ningún `.py`**, ni las Fases 1
y 2, ni la campaña de mutación. Es exactamente lo que pedía la primera pasada.

| # | Cambio requerido | Estado | Comprobado en |
|---|---|---|---|
| 1 | T13 `[x]`, mes real y resultado | **HECHO** | `tasks.md:238-257` |
| 2 | T14 `[x]` acotando que `limpiar` NO se ejecutó | **HECHO** | `tasks.md:259-276` |
| 3 | T6 cerrada como movida a F-014 + cabecera reescrita | **HECHO** | `tasks.md:7-17`, `:80-105` |
| 4 | `sigrid_F-002.md` § T13 | **HECHO, y mejor de lo pedido** | `sigrid_F-002.md:249-320` |
| 5 | Recuento de POSTV2 en la procedencia de `#regla-p5` | **HECHO** | `ARCHITECTURE.md:193-198` |
| 6 | Nota de `OBRA_PRUEBAS_FORZAR` con el motivo verdadero | **HECHO** | `ARCHITECTURE.md:129-137` |

### 0.1 · Punto 1 — T13

`tasks.md:238`: `- [x] **T13** · **EJECUTADA el 2026-08-20** sobre el periodo
**julio de 2026** (no agosto: el mes con datos reales era el 7)`. Los tres
comandos del bloque llevan ya `--mes 7`. Trae el resultado resumido (13 obras,
4 escribir, 21 omitir, 0 conflictos), que la partida resuelta **es hoja**
(`CI.1.8`) y —lo que importa— que el conflicto de sobrecarga **no llegó a
ejercitarse**, con remisión al volcado. **Correcto.**

### 0.2 · Punto 2 — T14

`tasks.md:259`: `- [x] **T14** · **EJECUTADA EN PARTE el 2026-08-20**`. Dice
qué se hizo (`ejecutar --confirmar` y la verificación leyendo Sigrid por
`synckey`, no fiándose de la respuesta del servicio) y, en negrita,
**«`limpiar --confirmar` NO se ejecutó, a propósito»**, con el motivo (el
humano quiso ver la fila en el ERP), el hecho de que **sigue viva** y el
traslado a F-014. En el bloque de comandos, la tercera línea queda marcada
`# PENDIENTE → F-014`. Es justo la acotación que pedía la primera pasada:
**nadie puede leer esta tarea y concluir que la limpieza está hecha.**
**Correcto.**

### 0.3 · Punto 3 — T6 y cabecera

`tasks.md:80`: `- [~] **T6 · MOVIDA A F-014** por decisión del humano del
2026-08-20`. El contenido original se conserva íntegro debajo (el aviso de las
cuatro partidas duplicadas, la nota sobre R18 y `normalize_code`, y el bloque
que explica que la procedencia ya no espera a nadie), así que no se pierde
contexto al moverla.

La cabecera está reescrita y ya no miente: dice que las Fases 1 y 2 están
aprobadas, que **T13 y T14 se ejecutaron el 2026-08-20**, que **T6 se movió a
F-014**, y que lo único pendiente de T14 es `limpiar --confirmar`, «que también
está en F-014: hay una fila de prueba viva en Sigrid (`hmores.ide = 403039`)».
**Correcto.**

> **Sobre el marcador `[~]`.** No es `[x]`, y C5 pide todas las tareas `[x]`.
> Se acepta como **N/A justificado por escrito**, que es lo que
> `CHECKPOINTS.md` admite expresamente: la tarea no se abandonó, se trasladó
> por decisión del humano, el destino está identificado (F-014, prioridad 20),
> el contenido viaja completo y el origen deja rastro. Marcarla `[x]` habría
> sido peor: diría que el aviso a Administración está dado, y no lo está.

### 0.4 · Punto 4 — el volcado de T13

Era el hallazgo grave de la primera pasada y **está resuelto por encima de lo
que se pidió**. `progress/sigrid_F-002.md:249-320` trae la sección
`## T13 · Casado real contra Sigrid, sin escribir` con:

- **Nota de trazabilidad** que dice de dónde se recuperó (`current.md` del
  commit `01bf62a`), que se había perdido al resolver el merge de F-008, quién
  lo detectó, y que **las cifras son de la ejecución real, no reconstruidas de
  memoria**. Esto último es lo que hace la sección creíble.
- **Qué se lanzó**: `capitulos` (obra `POSTV2 · POSTVENTA 2`, `ide = 1659588`),
  `estado --ano 2026 --mes 7` (obra `0404`, `ide = 828942`, **parte de julio
  inexistente**) y el `preflight` del periodo completo por el camino real
  front → api → transfer → `sigrid-api`.
- **Totales**: 13 obras · 25 acciones — 4 escribir, 21 omitir, 0 conflictos.
- **Las cuatro líneas** con obra, trabajador, `can`, código, `paride`, `pre` y
  `tot`, más dos controles que salieron bien: los importes cuadran al céntimo
  (`tot = can × pre`) y **Arriaza suma 0,385 + 0,18 + 0,435 = 1,0 exacto**, el
  100 % de la persona repartido entre tres obras.
- **Las dos comprobaciones para las que existía T13**, que es lo que la
  primera pasada echaba en falta:
  1. *¿La partida resuelta es hoja?* **Sí** — `paride = 94178`, `partida_cod =
     CI.1.8`, `partida_metodo = auto_categoria`.
  2. *¿Apareció el conflicto de sobrecarga?* **No, y con motivo**: el parte de
     julio de la obra destino no existía, así que **la Regla B no llegó a
     ejercitarse contra datos reales**. Está probada offline, no contra
     Sigrid, «y queda dicho para no confundir *no saltó* con *no funciona*».
- **Las 21 omisiones desglosadas** (10 sin código `M*`, 4 sin recurso, 7 sin
  partida en POSTV2), con la lectura de que **14 de 21 son datos de Sigrid y
  no lógica nuestra**, y el puntero a F-011.
- **El hallazgo que originó F-013**: los 2.132,28 € de Arriaza en la obra
  `0025` con `paride = 0`.

El segundo punto es el que más valor tiene y el que un informe complaciente
habría omitido: **declarar que una de las dos cosas que T13 iba a verificar no
se verificó**. Eso es lo que convierte el volcado en evidencia y no en
propaganda.

*(Observación menor, sin consecuencias: la sección T13 queda **después** de la
de T14 en el fichero, invertida respecto al orden cronológico. Es consecuencia
de haberse recuperado más tarde, la nota de trazabilidad lo explica, y no
merece otro commit.)*

### 0.5 · Punto 5 — el recuento de POSTV2

`ARCHITECTURE.md:193-198`, en la línea de procedencia de `#regla-p5`:

```
las **86** partidas de obra, todas hojas, **82 colgando de `CD` y cuatro
sueltas en la raíz** — `656`, `664`, `680` y `693`, duplicados sin el cero
inicial que Administración debería limpiar; ver F-014
```

Corrige los dos errores: 84 → **86**, y «todas colgando de `CD`» → **82 + 4 en
la raíz**. Cuadra (82 + 4 = 86) y concuerda con `sigrid_F-002.md:31` («cuelgan
de `CD`, salvo cuatro») y con la tabla de :49-147. Además nombra las cuatro y
remite a F-014, con lo que la corrección **conecta con la tarea que va a
resolverlo** en vez de quedarse en un dato suelto. **Correcto.**

### 0.6 · Punto 6 — la nota de `OBRA_PRUEBAS_FORZAR`

`ARCHITECTURE.md:129-137` mantiene la conclusión (`se queda a **true**`) y
cambia el motivo por el verdadero:

> El motivo ya no es que falte verificar contra Sigrid —**T13 y T14 se
> ejecutaron el 2026-08-20** y el sistema escribe de verdad en el ERP—, sino
> el que consta en `progress/sigrid_F-002.md` § «Qué NO queda demostrado»:
> **la imputación a partidas en producción no está validada**.

Y explica el porqué: en modo pruebas toda línea se desvía a `0404` conservando
la partida de su obra de origen. **Correcto**, y coherente con `#regla-pruebas`
(:295-298) y con la sección de despliegue (:414-419), que sigue diciendo que
salir del modo pruebas exige dos señales explícitas y decisión del humano.

---

## 1 · Nivel de rigor y puertas que exige

`harness/features.json` declara `"rigor": "critico"`, `sdd: true`, prioridad 2.

Nivel **crítico** ⇒ C1–C3, C3 bis, C5, tests trazables (C4), **fase RED**,
**cobertura** de las líneas cambiadas, **campaña de mutación con cero
supervivientes** salvo justificación escrita aceptada por el humano, y las
verificaciones **`MANUAL (humano)` listadas con su comando exacto y su
resultado real**.

**Las puertas de C4 bis (RED, cobertura, mutación) no se reabren aquí.** Las
verificaron y aprobaron `review_F-002_fase1.md` (T1–T5) y
`review_F-002_fase2.md` (T7–T12, T15–T17), incluido el recálculo independiente
de la campaña de mutación y la aceptación del único superviviente equivalente.
Esta review hereda ese veredicto.

Lo que sí era competencia de esta review —y era lo que fallaba— es la última
línea del nivel crítico: **las verificaciones `MANUAL (humano)` con su
resultado real**. En la segunda pasada, T13 y T14 están marcadas, fechadas,
acotadas y volcadas. **Cumple.**

---

## 2 · Verificación del estado final

### 2.1 · `bash harness/init.sh` — **verde, ejecutado por mí**

Ejecutado tal cual, sin pipes ni decoración. **Exit code 0 · `ENTORNO LISTO`.**

```
[OK] features.json válido        [OK] BACKLOG.md al día
[OK] harness/rigor.json y niveles declarados: válidos
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api / front / transfer: pytest en verde
[OK] PUERTA COBERTURA: N/A (rama dev: solo aplica en ramas de feature)
[OK] Ningún .env versionado      [OK] Rama actual: dev
```

Dos avisos, ninguno bloqueante: `ruff` con 178 avisos (deuda previa declarada)
y «hay features en estado `blocked`».

**Las tres líneas de servicio venían de caché**, así que, como manda el
protocolo, **reejecuté las tres suites a mano**:

| Servicio | Resultado |
|---|---|
| `dedicacion-api` | **112 passed** |
| `dedicacion-front` | **11 passed** |
| `dedicacion-transfer` | **232 passed** |
| **Total** | **355 passed** |

De esos 232, **184 son de F-002** y pasan todos. La caché no mentía.

**Cobertura N/A justificada por `init.sh`** con su motivo impreso: estamos en
`dev` y la puerta solo aplica en ramas de feature. La cobertura de F-002 la
midió y aprobó `review_F-002_fase2.md` sobre su rama.

### 2.2 · La regla de F-002 sigue viva tras F-013 y F-008 — **OK**

Revisado el diff `985054e..HEAD` sobre el transfer:

- El único test de F-002 que F-013 tocó es `test_f002_fuente_unica.py`, y el
  cambio es de **una línea**: `range(1, 11)` → `range(1, 12)`. Es **refuerzo**,
  no relajación: comprueba dos puntos más del documento contra la marca
  `PENDIENTE`.
- En `reglas_porcentajes.py` F-013 es **puramente aditivo**
  (`PREFIJO_CLAVE_SIN_PARTIDA`, `MOTIVO_SIN_PARTIDA`, `AVISO_SIN_PARTIDA`,
  `sin_partida()`, `clave_sin_partida()`). No toca `campos_identidad`,
  `criterio_choque`, `clave_conflicto`, `evaluar_capacidad` ni
  `es_linea_mensual`.
- En `registro_pipeline.py` las líneas retiradas son la **generalización del
  despacho de dos motivos a tres**. R28 —la sobrecarga sin confirmar deja
  rastro en `omitidas`— sigue en verde, que es la prueba de que no se llevó
  nada por delante.
- `Conflicto` gana el motivo nuevo manteniendo defectos en todos los campos:
  la degradación elegante que diseñó F-002 sigue funcionando.
- `afeeaa0` no toca código en absoluto.

**Regla A, Regla B y postventa por código exacto: intactas y con sus tests
pasando.**

### 2.3 · Fuente única y procedencia — **OK**

`docs/ARCHITECTURE.md` § «Semántica de dominio imprescindible» es la única
fuente normativa, con las anclas `#regla-p1`, `#regla-p2`, `#regla-p3`,
`#regla-p4` / `#regla-conflicto`, `#regla-capacidad`, `#regla-sin-partida`,
`#regla-p5` y `#regla-pruebas`. El `README.md` del transfer **remite** con una
tabla de enlaces (líneas 15–22) y no reenuncia nada. Lo vigila
`test_f002_fuente_unica.py`, 60 tests en verde.

Cuatro líneas de procedencia, todas con **quién · cuándo · con qué respaldo**:

| Ancla | Procedencia |
|---|---|
| `#regla-p5` | Pablo Gris (responsable del proyecto) · 2026-08-19 · verificado contra Sigrid, `progress/sigrid_F-002.md` (86 partidas, 82 en `CD` + 4 en la raíz) |
| `#regla-p4` | Pablo Gris · 2026-08-19 · decisión D2, `requirements.md` §2 |
| `#regla-capacidad` | Pablo Gris · 2026-08-19 · decisión D2, `requirements.md` §2 |
| `#regla-sin-partida` | Pablo Gris · 2026-08-20 · preflight real del periodo 2026-07 |

**Nada se atribuye a Administración.** La única mención (línea 17) habla de la
plantilla Excel que mantenía a mano: hecho histórico, no procedencia. Correcto:
esa conversación no ha existido, y escribirla sería peor que no tener
procedencia.

### 2.4 · F-014 recoge fielmente lo movido — **OK**

Revisada su entrada en `harness/features.json` (prioridad 20, `rigor:
documental`, `sdd: false`). Quien la coja dentro de seis meses tiene todo:

| Dato | ¿Está? |
|---|---|
| `hmores.ide = 403039`, `synckey 'porcentajes:77'`, marca `PRUEBA-PORC` | sí |
| Parte `PT26/00296` (`hmo.ide = 2820419`), obra `0404`, fecha 2026-08-20 | sí |
| Comando de limpieza con el mes correcto (`--mes 7`) y que solo toca lo marcado | sí |
| Que la cabecera del parte quedaría creada y vacía, y hay que decidir | sí |
| **Aviso de que probar desde Azure escribirá más líneas indistinguibles** | sí, con la recomendación de limpiar antes o distinguir por `ide` |
| Las cuatro partidas duplicadas de POSTV2, con puntero al volcado | sí |
| Quién firma la procedencia de P4/P5, y que el test no clava el interlocutor | sí |
| Por qué se movió | sí |

Duplicado además en `progress/current.md` §«2 · F-014, cuando toque», con el
comando listo y el aviso del orden respecto al despliegue. **Nada se perdió.**

---

## 3 · Recorrido de CHECKPOINTS.md

| Checkpoint | Estado | Razón |
|---|---|---|
| **C1** · `init.sh` exit 0 y ficheros del arnés | `[x]` | Exit 0, `ENTORNO LISTO`. Suites reejecutadas a mano por venir de caché: 355 en verde |
| **C2** · Estado coherente | `[x]` | `current.md` y `tasks.md` dicen lo mismo que el mundo real: T13 y T14 ejecutadas, T6 en F-014, fila de prueba viva en Sigrid |
| **C3** · Arquitectura y convenciones | `[x]` | Heredado de las dos reviews aprobadas. `afeeaa0` no toca código |
| **C3 bis** · Documentos de fuera | **N/A** | **Justificado**: F-002 no incorporó ningún PDF ni documento ofimático; `docs/referencia/` no se tocó |
| **C4** · Verificación real | `[x]` | Cada requisito con su test trazable `test_f002_rN_*`, 184 en verde, ninguno toca red ni BBDD. Las `MANUAL (humano)` están al día: T13 y T14 marcadas, fechadas y volcadas en `sigrid_F-002.md`; lo que sigue pendiente (`limpiar --confirmar`) consta con su comando exacto en `current.md` y en F-014 |
| **C4 bis** · Rigor declarado | `[x]` | **Heredado**, no reabierto: `rigor: critico` declarado; fase RED, cobertura, campaña de mutación con recálculo independiente y sección «Evidencias» los validaron y aprobaron las reviews de Fase 1 y Fase 2; el único superviviente quedó justificado como equivalente. **Campaña no reejecutada en esta review**: es un cierre documental, no un re-review del código, `afeeaa0` no toca ni un `.py`, y la verificación independiente ya se hizo en la Fase 2 |
| **C4 ter** · Rutas sensibles | **N/A** | **Justificado**: no existe `harness/rutas_sensibles.json`. Sin declaración, el bloque es N/A por diseño |
| **C5** · Sesión cerrada | `[x]` | T1–T5 y T7–T17 en `[x]` con su commit `F-002 Tn:`; **T6 en `[~]` como N/A justificado por escrito** (movida a F-014, contenido conservado, destino identificado). Árbol limpio, sin artefactos sospechosos. `features.json` coherente |

**Ningún checkbox vacío en C1–C5. Los tres N/A están justificados por escrito.**

---

## 4 · Trazabilidad requisito → test

Comprobada la que importa para el cierre: que las reglas de F-002 siguen
atadas después de que F-013 tocara los mismos ficheros. La tabla completa
requisito a requisito está en `review_F-002_fase1.md` y
`review_F-002_fase2.md` y no se repite.

| Requisito | Test que lo cubre | Estado |
|---|---|---|
| R1–R5 · fuente única, anclas, procedencia con quién·cuándo·respaldo | `test_f002_fuente_unica.py` (60) | verde |
| R6–R9, R12 · P1 recursos `M*`, P2 último día del mes, P3 escala sobre 1 | `test_f002_reglas.py` (25) | verde |
| R10, R11, R13 · idempotencia por `synckey`, modo pruebas, un solo `DELETE` | `test_f002_pipeline.py` (20) | verde |
| R14, R20–R22 · **Regla A**: la partida entra en la identidad | `test_f002_conflicto.py` (21) | verde |
| R15–R19 · **P5**: postventa a hoja activa por código exacto | `test_f002_postventa.py` (23) | verde |
| R23–R33 · **Regla B**: capacidad del 100 %, tolerancia, alcance | `test_f002_capacidad.py` (35) | verde |
| T13 · casado real contra Sigrid, sin escribir | **MANUAL** — ejecutada, volcada en `sigrid_F-002.md` § T13 | verde |
| T14 · escritura real en obra de pruebas | **MANUAL** — ejecutada en parte, volcada en § T14; `limpiar` → F-014 | verde |

---

## 5 · Lo que queda vivo al cerrar (no bloquea, pero no se pierde de vista)

F-002 se cierra **con dos cosas abiertas, ambas conscientes y con dueño**:

1. **Una fila de prueba viva en Sigrid**: `hmores.ide = 403039`, parte
   `PT26/00296`, obra `0404`, marca `PRUEBA-PORC`. Está en F-014 con su
   comando y con el aviso de que probar desde Azure escribirá más líneas
   indistinguibles salvo por su `ide`.
2. **La Regla B nunca se ha ejercitado contra Sigrid real.** Está probada
   offline (35 tests, cobertura y mutación), pero el preflight de julio no
   llegó a dispararla porque el parte de la obra destino no existía. Consta
   escrito en `sigrid_F-002.md` § T13. **No es un defecto de F-002** —la regla
   está implementada y probada— pero conviene que la primera vez que un parte
   real tenga líneas `M*` previas alguien mire ese preflight con atención.

Y el modo pruebas sigue puesto: `OBRA_PRUEBAS_FORZAR=true`, con el motivo
verdadero escrito en `ARCHITECTURE.md:129-137`.

---

## 6 · Registro de la primera pasada (2026-08-20)

Se conserva porque el rastro de qué se rechazó y por qué es parte del valor de
la review.

**Veredicto: CHANGES_REQUESTED.** Dos checkboxes vacíos en C1–C5 (C4 y C5).
El código estaba bien; el rastro documental no decía la verdad.

Los seis puntos, todos de documento y ninguno de código:

1. **T13 marcada `[ ]`** cuando se ejecutó el 2026-08-20; el comando decía
   `--mes 8` y lo ejecutado fue julio.
2. **T14 marcada `[ ]`** cuando se ejecutó —incluida la primera escritura real
   de este sistema en un ERP—, y sin acotar que `limpiar --confirmar` no se
   hizo y que hay una fila viva.
3. **T6 marcada `[ ]`** sin decir que se había movido a F-014, y cabecera de
   `tasks.md` afirmando que T6, T13 y T14 seguían exigiendo trabajo al humano.
4. **`sigrid_F-002.md` sin sección T13**, que la propia tarea exige. Se
   diagnosticó la causa: el volcado vivía en `progress/current.md` de la rama
   de F-008 y **se perdió al resolver ese merge reescribiendo el fichero**. Lo
   que quedaba del preflight de julio estaba disperso y de segunda mano
   (`ARCHITECTURE.md`, `history.md`, `BACKLOG.md`), y **ninguna de esas
   menciones respondía lo que T13 iba a comprobar**.
5. **`ARCHITECTURE.md`** decía «las **84** partidas de obra **todas** hojas
   colgando de `CD`», contradiciendo a su propia fuente (86, con cuatro en la
   raíz) en el dato que la review de la Fase 2 había corregido a propósito.
6. **La nota de `OBRA_PRUEBAS_FORZAR`** daba como motivo una condición ya
   cumplida (que faltaran T13 y T14). *(No bloqueante.)*

> **Nota sobre el árbol, que motivó la propuesta 4 del §7.** La primera pasada
> arrancó con el repositorio en `dev` **con un merge de F-013 a medias y
> cuatro ficheros en conflicto**, `harness/init.sh` en rojo con 3 fallos, y el
> árbol cambiando tres veces bajo los pies mientras el líder encadenaba los
> merges de F-013 y F-008. Las conclusiones se tomaron sobre el árbol final ya
> estable, pero no es una situación en la que se deba revisar.

---

## 7 · Automejora del protocolo (propuesta, no aplicada)

Cuatro cosas que este cierre dejó a la vista. **Se proponen para que las
apruebe el humano**; ninguna se ha aplicado. Las cuatro son genéricas ⇒
**portar a `arnes-base`**.

1. **La evidencia de una verificación `MANUAL (humano)` no puede vivir en
   `progress/current.md`.** Es exactamente lo que pasó con T13: `current.md` es
   un documento de sesión, se reescribe entero, y el siguiente merge se llevó
   la sección por delante. La de T14 sobrevivió por estar donde le tocaba.
   Sugerencia para `.claude/agents/implementer.md` y `CHECKPOINTS.md` (C4): el
   volcado de una verificación manual va **siempre** a un fichero propio y
   permanente (aquí, `progress/sigrid_F-XXX.md`); `current.md` como mucho lo
   **enlaza**.

2. **Ejecutar una tarea `MANUAL (humano)` y no marcarla en `tasks.md` es el
   punto ciego que provocó el rechazo.** Se hizo el trabajo de verdad y el
   documento siguió diciendo «pendiente». Sugerencia para `CHECKPOINTS.md` C4:
   un checkbox explícito, «**toda verificación `MANUAL (humano)` ejecutada está
   marcada en `tasks.md` y su volcado enlazado**», para que el reviewer tenga
   que mirarlo y no dependa de que se le ocurra.

3. **Mover tareas de una feature a otra necesita dejar rastro en el origen.**
   T6 se fue a F-014 y `tasks.md` de F-002 no se enteró. F-014 estaba
   ejemplarmente escrita, pero el rastro solo iba en un sentido. Sugerencia:
   cuando el líder mueva una tarea, la marca en el origen con «movida a F-YYY»
   **en el mismo commit** que crea la feature destino. El marcador `[~]` que se
   ha usado aquí funciona bien y podría estandarizarse.

4. **Un reviewer no debe arrancar sobre un árbol con un merge a medias.**
   Sugerencia para `.claude/agents/reviewer.md`, paso 1: si `git status`
   muestra ficheros en estado `UU` o existe `.git/MERGE_HEAD`, **parar y
   devolver el control al líder** en vez de intentar revisar. Un `init.sh` en
   rojo por marcadores de conflicto no es un veredicto sobre la feature.

---

## 8 · Cierre

F-002 cumple C1–C5 con los tres N/A justificados. **Puede pasar a `done`.**

Queda dicho, para que conste en el historial: el volcado de T13 estuvo perdido
y se recuperó porque alguien fue a buscarlo al commit donde vivía en vez de
reescribirlo de memoria. La nota de trazabilidad que lo explica, y la línea que
admite que la Regla B no llegó a ejercitarse contra datos reales, son las dos
partes de este cierre que más van a valer dentro de un año.
