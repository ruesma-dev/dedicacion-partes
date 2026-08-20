<!-- progress/review_F-013.md -->
# F-013 · Review — Una línea sin partida no se escribe en silencio

- **Veredicto: APPROVED**
- **Rama:** `feature/F-013-linea-sin-partida-confirma` (8 commits sobre `dev`)
- **Modo:** `sdd: false` — mandan los `acceptance` de `harness/features.json`
- **Nivel de rigor:** `critico` (declarado explícitamente en `features.json`,
  no por omisión). Exige: C1–C5 + tests trazables + **fase RED** con traza
  real + **cobertura** de líneas cambiadas ≥ 80 % + **campaña de mutación**
  con **cero supervivientes** salvo justificación escrita.
- **Reejecución de la campaña de mutación: SÍ** (el informe declara 3,1 s,
  por debajo del umbral de 5 min de C4 bis).

---

## 1. Resumen del veredicto

Los cuatro criterios que el encargo pedía vigilar con más cuidado se han
comprobado **ejecutando**, no leyendo el informe del implementer. Todos
salen. Los números declarados (100 % de cobertura 24/24, 7 mutantes / 7
muertos / 0 supervivientes, 232 tests en el transfer) se han **reproducido de
forma independiente y coinciden exactamente**.

Dos verificaciones merecen mención porque son las que suelen dejar pasar un
informe fabricado, y aquí han salido limpias:

1. **La fase RED es auténtica.** Las seis líneas que el informe cita en sus
   trazas (`:122`, `:205`, `:217`, `:232`, `:253`, `:534`) se han contrastado
   contra el fichero de tests **tal como estaba en el commit T1** (`5962ae0`),
   no contra el actual. Las seis caen sobre el `assert` exacto que la traza
   reproduce. Una traza inventada no acierta seis desplazamientos de línea
   sobre una versión histórica del fichero.
2. **La campaña de mutación es real, no escrita a mano.** Reejecutada entera:
   mismos 7 mutantes, mismos ficheros, líneas, operadores y textos
   original→mutado, mismo veredicto (7 muertos, 0 supervivientes, 0 timeouts).

---

## 2. C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en verde (`ENTORNO LISTO`), ejecutado tal
      cual, sin pipes ni decoración.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`.

### 2.1 Las líneas de caché, reejecutadas a mano

`init.sh` dio `[OK]` a `api` y a `transfer` **por caché** («árbol sin cambios
desde el último verde»). Como pedía el encargo, se han lanzado las dos suites
a mano con el intérprete de cada servicio (`.venv/Scripts/python.exe`, no el
del sistema — con el del sistema fallan por `ModuleNotFoundError`, que no es
un fallo de la feature sino de intérprete):

| Suite | Resultado real |
|---|---|
| `services/dedicacion-transfer` | **232 passed**, 1 warning, 0,36 s |
| `services/dedicacion-api` | **84 passed**, 0,90 s |
| raíz | 11 passed, 0,12 s |
| `tests/test_f013_sin_partida.py` (aislado) | **44 passed**, 0,18 s |

Los 232 del transfer **no son un `[OK]` heredado de otra rama**: se han
contado ejecutando.

El único `warning` (`PytestReturnNotNoneWarning` en
`test_pipeline_offline.py::test_preflight`) es anterior a F-013.

### 2.2 El `[AVISO]` del front no es de esta feature

`[AVISO] servicio front: sin directorio de tests`. Comprobado: **no existe**
`services/dedicacion-front/tests/` en absoluto — ni siquiera el residuo de
`__pycache__` que documenta `progress/current.md`. Es deuda anterior a F-013,
es `[AVISO]` y no rojo, y F-013 tiene por criterio explícito no tocar el
front. **No bloquea.**

## 3. C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-013`); `F-002` en `blocked` por
      motivos ajenos y anteriores.
- [x] Rama actual `feature/F-013-linea-sin-partida-confirma`, nunca `dev` ni
      `main`.
- [x] `progress/current.md` describe solo la sesión activa de F-013, con sus
      verificaciones `MANUAL` y el estado de las demás features.
- [x] No hay features `done` nuevas pendientes de `history.md` (el paso a
      `done` lo hace el líder tras esta aprobación).

## 4. C3 — Arquitectura y convenciones

- [x] **Hexagonal respetada.** El predicado y las claves son **funciones
      puras sin I/O** en `application/services/reglas_porcentajes.py`; la
      orquestación en `application/pipelines/registro_pipeline.py`; en
      `domain/models/registro_models.py` **solo cambian docstrings y
      comentarios** — ni un import nuevo, ni un campo nuevo. Ningún import de
      infraestructura en dominio.
- [x] **Primera línea con ruta relativa** en todos los ficheros tocados; el
      fichero nuevo lleva `# tests/test_f013_sin_partida.py`, misma
      convención relativa al servicio que sus hermanos (`tests/conftest.py`,
      `tests/test_f002_capacidad.py`).
- [x] **Sin `print()` de debug, sin TODOs sin contexto, sin secretos.**
      Barrido sobre el `+` del diff con
      `grep -iE "print\(|TODO|password|secret|api_key|contrasen"`: solo
      coincidencias léxicas dentro de docstrings en castellano, ninguna real.
- [x] **Sin dependencias nuevas.** El diff no toca ningún `requirements.txt`.
- [x] **Las tres trampas del proyecto:**
      - *Escala del porcentaje*: F-013 **no introduce ninguna conversión**.
        `can` viaja igual que antes; lo único que se toca es `paride`, que es
        un identificador, no un importe.
      - *Postventa*: **no se ha mezclado con la obra normal** — ver §7.4, es
        uno de los puntos que más se ha mirado.
      - *Solo escribe el transfer*: F-013 no añade ninguna escritura. Al
        contrario, **quita una**: la línea sin partida deja de escribirse sin
        confirmación. `OBRA_PRUEBAS_FORZAR` intacto, `synckey` intacta,
        reserva de `ide` intacta. **Ninguna escritura real contra Sigrid en
        toda la feature.**

## 5. C3 bis — Documentos de fuera

**N/A justificado:** `git diff dev..HEAD --name-only -- docs/referencia/`
devuelve **0 ficheros**. La feature no añade ni modifica ningún documento en
`docs/referencia/`, así que no hay original ofimático que vigilar ni barrido
de datos sensibles que ejecutar.

## 6. C4 ter — Rutas sensibles

**N/A sin nada que justificar:** el repositorio **no declara**
`harness/rutas_sensibles.json` (solo existe
`harness/rutas_sensibles.ejemplo.json`). Es el caso mayoritario que
`CHECKPOINTS.md` contempla expresamente.

## 7. C4 — La verificación es real

- [x] Cada criterio `acceptance` tiene ≥ 1 test trazable y todos pasan.
- [x] **Los unit tests no tocan red ni BBDD.** Todo el fichero nuevo va sobre
      `ClienteFalso`/`SettingsFalso`/`linea`/`linea_previa` de
      `tests/conftest.py`. Ningún socket, ningún `.env`, ninguna sesión de
      SQLAlchemy.
- [x] Verificaciones `MANUAL (humano)`: **ninguna nueva de F-013**, y así
      consta en `progress/current.md`. La única viva del proyecto (la fila de
      prueba `hmores.ide = 403039`) es de F-008 y anterior.

### 7.1 Trazabilidad: criterio `acceptance` → test que lo cubre

| # | Criterio `acceptance` | Test(s) que lo fijan | Verificado |
|---|---|---|---|
| 1 | Conflicto con motivo propio, **distinguible** del pisado y de la sobrecarga | `test_f013_r1_una_linea_sin_partida_emite_conflicto`, `test_f013_r1_el_motivo_distingue_de_los_otros_dos`, `test_f013_r1_la_clave_no_colisiona_con_las_otras_dos`, `test_f013_r1_la_clave_es_por_linea_y_no_por_trabajador`, `test_f013_r1_dos_lineas_sin_partida_son_dos_conflictos`, `test_f013_r1_el_predicado_solo_mira_lo_que_se_escribe`, `test_f013_r1_tambien_avisa_con_el_parte_por_crear`, `test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe` | [x] |
| 2 | Sin confirmación: **no se escribe** y queda **omitida con su motivo** | `test_f013_r2_sin_confirmar_no_se_escribe`, `test_f013_r2_queda_listada_en_omitidas_con_motivo`, `test_f013_r2_el_motivo_es_legible_y_cabe_en_la_base`, `test_f013_r2_lo_que_si_casa_se_escribe_igual` | [x] |
| 3 | Con confirmación: se escribe con `paride = 0` | `test_f013_r3_confirmada_se_escribe_con_paride_cero`, `test_f013_r3_confirmarla_no_borra_nada`, `test_f013_r3_la_confirmacion_no_estrena_canal`, `test_f013_r3_una_clave_ajena_no_confirma_nada`, `test_f013_r3_confirmar_una_no_confirma_la_otra` | [x] |
| 4 | Degradación elegante; **no se toca `dedicacion-api` ni `dedicacion-front`** | `test_f013_r4_el_conflicto_serializa_los_campos_de_siempre`, `test_f013_r4_no_hace_falta_ningun_campo_nuevo`, `test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos` (6 casos) + diff | [x] |
| 5 | Tests offline con las fixtures de `conftest.py` | Todo el fichero (44 tests) | [x] |
| 6 | La regla en la **fuente única** con su **procedencia** | `test_f013_r6_la_regla_tiene_su_ancla_en_la_fuente_unica`, `test_f013_r6_la_regla_dice_lo_que_decide`, `test_f013_r6_la_regla_lleva_su_procedencia`, `test_f013_r6_el_respaldo_es_el_preflight_real_de_julio`, `test_f013_r6_el_codigo_remite_en_vez_de_reenunciar` (2 casos) | [x] |
| 7 | `bash harness/init.sh` en verde | §2 | [x] |

Cobertura extra que el encargo pedía y que también está fijada: interacción
con la sobrecarga (6 tests), interacción con el pisado (3 tests), postventa
(2 tests, uno de ellos control positivo) y dos tests de premisa que impiden
que el escenario pase por el motivo equivocado.

### 7.2 Criterio 4 — «No toca la API ni el front»: confirmado

`git diff dev..HEAD --stat` lista **12 ficheros y ninguno** bajo
`services/dedicacion-api/` ni `services/dedicacion-front/`. Confirmado el
hallazgo del líder.

### 7.3 Degradación elegante — comprobada en el código real, no solo por
ausencia de la palabra

El test `test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos` prueba que
ninguno de los dos servicios contiene las cadenas `"pisado"`, `"sobrecarga"`
ni `"sin_partida"`. Eso es una prueba **negativa**, así que se ha comprobado
además la positiva leyendo el código:

- **`app.js`** (`pintarModalPreflight`, l. 1314): itera
  `(o.conflictos || []).forEach(...)` **sin mirar `c.motivo` en ningún
  momento**, pinta una casilla con `value="${c.clave}"`, y
  `registroEjecutar()` recoge **todas** las casillas marcadas
  (`.chk-pisar:checked`) en `pisar_claves`. Es decir: un front que ignore el
  motivo nuevo **no solo sigue funcionando, sino que puede confirmar el
  conflicto nuevo** sin un cambio de línea.
- **`registro_sigrid.py`** (l. 134): recorre `r.get("omitidas", [])` y hace un
  `UPDATE` por entrada con `sigrid_estado="omitido"` y el motivo recortado a
  `_MAX_MOTIVO = 300`, **sin ramificar por tipo**.
- **El contrato no cambió de forma incompatible.** `asdict(Conflicto)`
  devuelve exactamente los 15 campos de F-002 — comprobado por
  `test_f013_r4_no_hace_falta_ningun_campo_nuevo`, que fija el conjunto
  **exacto**. En `registro_models.py` el diff solo toca docstrings y el
  comentario del campo `motivo`. Ni un campo añadido, ni un default cambiado,
  ni un canal de confirmación nuevo.
- **El motivo cabe en la base:** `len(MOTIVO_SIN_PARTIDA)` = **171** ≤ 300.
  Verificado ejecutando, no leyendo.

Se acepta la precisión del implementer (§7 de su informe): «degradación
elegante» significa que el front sigue funcionando sin cambios, **no** que la
línea se siga escribiendo. Que deje de escribirse es el objetivo de la
feature.

**Anotado, no bloqueante:** con `lineas` vacío, el texto que pinta el front
(«…se borran ␣ y se escribe…») queda cojo. Es cosmético, **ya le pasaba a la
sobrecarga desde F-002**, y arreglarlo exige tocar `dedicacion-front`, que es
justo lo que el criterio 4 prohíbe. El implementer lo declara fuera de
alcance en su §8 y propone feature aparte: **correcto**.

### 7.4 Postventa — los dos caminos siguen separados

Verificado **en quien construye el dato**, no solo por el test.
`ReglasPorcentajes.decidir` (`reglas_porcentajes.py`): si `linea.es_postventa`
y `self._partida is None`, devuelve `omitir(...)` **antes** de llegar a ser
acción de escritura (P5). Y en el bucle de partidas del pipeline, la rama
`if a.destino == "postventa": ... continue` sale **antes** de la asignación
`a.paride = 0`, que por tanto solo alcanza a la obra normal.

Conclusión: una postventa sin partida **nunca** llega a `sin_partida()`,
porque `sin_partida()` exige `accion == "escribir"`. Los dos caminos no se han
mezclado. Lo fijan `test_f013_la_postventa_sin_partida_se_sigue_omitiendo`
(que comprueba además `pf.conflictos == []`) y su control positivo
`test_f013_la_postventa_que_si_casa_se_escribe_sin_preguntar` — el control
positivo importa: sin él, el primero pasaría también con un pipeline que no
emitiera conflictos nunca.

### 7.5 La interacción entre los avisos: decidida, escrita y fijada

El encargo pedía que se decidiera, se escribiera y se cubriera con un test.
Las tres cosas están:

- **Decidido y razonado**: se enseñan **los dos (o los tres)** avisos, cada
  uno con su clave, porque cada uno es una decisión distinta; el orden es
  `sin_partida → pisado → sobrecarga` porque **cada aviso da por hecho el
  anterior** (la identidad del pisado usa el `paride = 0` de esa línea y la
  suma de la sobrecarga incluye su `can`). Es la extensión del criterio con el
  que F-002 puso el pisado antes que la sobrecarga.
- **Escrito** en `docs/ARCHITECTURE.md#regla-sin-partida` (tercer punto de la
  regla) y en el comentario del paso 6 bis.
- **Fijado por tests que lo comprueban de verdad**, no que lo describen:
  - `test_f013_el_orden_es_sin_partida_primero` no se limita al orden: afirma
    `suma_total == 1.3`, es decir, que la sobrecarga **sí** contó el `can` de
    la línea retenida. Eso fija la hipótesis, no solo la secuencia.
  - `test_f013_confirmar_solo_la_sobrecarga_no_escribe` **y su simétrico**
    `test_f013_confirmar_solo_la_sin_partida_tampoco_escribe`. El simétrico
    es lo que impide que el par pase con un pipeline que no escriba nunca.
  - `test_f013_confirmando_las_dos_se_escribe_una_vez` como control positivo,
    con `paride == 0` en el `INSERT`.
  - **El riesgo de verdad**, y es el test que más valor tiene de los 44:
    `test_f013_confirmar_el_pisado_sin_la_partida_no_borra`. Confirmar el
    pisado sin confirmar el «sin partida» podría **borrar la línea vieja de
    Sigrid sin escribir la que la sustituye** (el borrado se emite por
    conflicto confirmado; la escritura se bloquea por registro). La guarda R32
    de F-002 ya lo cubría, pero **no estaba probada para este tercer caso**.
    Ahora lo está, con `cli.borrados() == []` y su control positivo
    `test_f013_confirmando_las_dos_si_se_pisa` (`borrados() == [5001]`).
    Identificar y probar esto sin que nadie lo pidiera es el punto más fuerte
    de la implementación.
  - `test_f013_la_omision_no_se_duplica_con_los_dos_avisos` fija que la línea
    sale **una sola vez** en `omitidas`. La razón es correcta y verificada en
    la API: `registro_sigrid.py` hace un `UPDATE` por entrada sobre la **misma**
    asignación, así que dos entradas serían dos escrituras de las que solo
    sobrevive la última.
  - La disjunción que sostiene `omitidas_ya` se ha verificado: los conflictos
    (los tres tipos) solo agrupan acciones `escribir`, y `res.omitidas` se
    siembra con acciones `omitir`. Son disjuntos por construcción, como
    afirma el comentario.

## 8. C4 bis — El rigor declarado se cumple

- [x] **`rigor` declarado** en `harness/features.json`: `"critico"`. No hay
      que aplicar el valor por omisión.
- [x] **Fase RED — verificada como auténtica.** `progress/impl_F-013.md` §4
      trae tres ejecuciones con salida real: (4.1) el `ImportError` de
      colección porque el vocabulario no existía; (4.2) **26 failed, 18
      passed** con el vocabulario y sin la conducta, con seis trazas literales
      de los requisitos centrales; (4.3) el verde final.
      **Contraste independiente:** las seis líneas citadas se han cotejado
      contra `git show 5962ae0:...test_f013_sin_partida.py` (el fichero **como
      estaba en T1**, no el actual). Las seis caen exactamente sobre el
      `assert` que la traza reproduce:

      | Traza | Línea en T1 | `assert` en esa línea |
      |---|---|---|
      | `r1_una_linea_sin_partida_emite_conflicto` | 122 | `assert len(pf.conflictos) == 1` |
      | `r1_el_aviso_...ya_no_promete_que_se_escribe` | 205 | `assert pf.acciones[0].aviso == AVISO_SIN_PARTIDA` |
      | `r2_sin_confirmar_no_se_escribe` | 217 | `assert cli.inserts() == [] and res.escritas == []` |
      | `r2_queda_listada_en_omitidas_con_motivo` | 232 | `assert [o["registro_id"] for o in res.omitidas] == [1]` |
      | `r2_lo_que_si_casa_se_escribe_igual` | 253 | `assert [e["registro_id"] for e in res.escritas] == [2]` |
      | `confirmar_el_pisado_sin_la_partida_no_borra` | 534 | `assert cli.borrados() == []` |

      En el fichero **actual** varias de esas líneas ya no coinciden (T5 y T4
      insertaron aserciones antes). Que casen con la versión histórica y no
      con la actual es la prueba de que la traza se pegó cuando se dice.

- [x] **Cobertura.** `PUERTA COBERTURA: 100.0% de 24 líneas cambiadas
      cubiertas (24/24, umbral 80%, nivel critico)` — `[OK]`, obtenida
      ejecutando `bash harness/init.sh` en esta review, no copiada del informe.
- [x] **Mutación — totales verificados de forma independiente.**
      Existe `progress/mutacion_F-013.md`, generado por la herramienta.
      - *Alcance recalculado* con `harness.alcance.alcance_de_feature('F-013')`:
        `registro_pipeline.py` **85** + `reglas_porcentajes.py` **70** +
        `registro_models.py` **19** = **174**. Coincide con el informe línea a
        línea, incluida la ref de diff (`f594ff1e…`).
      - *Nº de mutantes recalculado* con `harness.mutacion.generar_mutantes`
        (cálculo puro, sin ejecutar la suite ni escribir en disco): **7**.
        Coincide.
      - *Muestreo de supervivientes*: **no aplica, hay cero**. En su lugar se
        han cotejado los **siete** mutantes uno a uno contra la tabla del §9.1
        del implementer: mismo fichero, misma línea, mismo operador y mismo
        texto original→mutado en los siete. Sin discrepancias.
      - *Prueba de control de «cero mutantes»*: **no procede** — la campaña
        declara 7, no 0.
- [x] **Los muertos están comprobados, no solo contados. CAMPAÑA
      REEJECUTADA.** El informe declara «Tiempo total 3.1 s», por debajo de
      los 5 minutos, así que C4 bis obliga a reejecutar. Ejecutado:

      ```
      python -m harness.mutacion --feature F-013 --salida <scratchpad>/mutacion_F-013_reviewer.md
      7 mutantes evaluados, 7 muertos, 0 supervivientes, 0 timeouts en 3.5 s
      ```

      **Totales idénticos** a los del informe (7 / 7 / 0 / 0), y los siete
      mutantes salieron en las mismas líneas y con los mismos operadores. La
      salida se escribió **fuera de `progress/`** (scratchpad de sesión), así
      que no se ha pisado el informe del implementer, y `git status --porcelain`
      queda **vacío** después: el árbol está limpio.
- [x] **Supervivientes:** ninguno, y ninguna sección en `PENDIENTE`. El nivel
      `critico` exige cero y la campaña da cero; no hay nada que justificar.
- [x] **Sección «Evidencias» completa** (§9 del informe), con los cuatro
      números: tests (327 pasan / 0 fallan), cobertura (100 %, 24/24),
      mutantes y supervivientes (7 / 0) y tiempo de suite (transfer 0,46 s ·
      api 1,34 s · raíz 0,09 s). Todos reproducidos en esta review.
- [x] Ningún punto de este bloque marcado N/A.

### 8.1 «Solo 7 mutantes para 174 líneas»: la justificación se sostiene

Recalculadas las líneas en alcance una a una, el reparto es el que el
implementer describe: de las 174, la inmensa mayoría son **docstrings,
comentarios, constantes de texto y construcción del `Conflicto`** (paso de
argumentos, sin decisiones). El mutador de este arnés ataca comparaciones,
operadores lógicos, negaciones y literales enteros, y en el diff hay
**exactamente dos puntos con decisión**:

1. el predicado `sin_partida` (`reglas_porcentajes.py:302`) — **4 mutantes**
   (comparación ×2, lógico, entero), los cuatro muertos;
2. el reparto de motivos en `ejecutar` y el filtro del paso 6 bis
   (`registro_pipeline.py:289`, `:460`, `:466`) — **3 mutantes**, los tres
   muertos.

**Es decir: los 7 mutantes caen justo donde tiene que haber vigilancia.** No
hay una decisión del diff sin mutante salvo la deduplicación
(`if r in omitidas_ya`), que el mutador no genera porque es un operador de
pertenencia, y que está cubierta directamente por
`test_f013_la_omision_no_se_duplica_con_los_dos_avisos`. El implementer lo
declara él mismo en vez de dejarlo pasar.

### 8.2 T5 — la «guarda muerta»: invariante verificado en quien construye el
dato

Aplicada la lección de la review de F-002 §11.2. T5 (`89e0d29`) sustituyó
`partes.get(...)` por `partes[...]` y quitó el `or 0` de `int(a.recurso_ide)`.
Comprobar que un test mata el mutante en el punto de la guarda **no
demuestra nada**; hay que verificar el invariante donde se construye el dato.
Hecho, y las dos guardas eran efectivamente inalcanzables:

1. **`partes[(int(obra_de(a).ide), a.ano, a.mes)]` no puede dar `KeyError`.**
   El **paso 5** construye `partes` iterando
   `escribir = [a for a in acciones if a.accion == "escribir"]` y deja una
   entrada por cada clave `(destino, año, mes)` con **el mismo `obra_de`** que
   usa el paso 6 bis. Entre medias, el **paso 6** solo puede pasar acciones de
   `escribir` a `ya_registrado`: **saca**, nunca mete. El conjunto que
   atraviesa el paso 6 bis es por tanto un **subconjunto** del que sembró
   `partes`. Invariante confirmado en el constructor.
2. **`int(a.recurso_ide)` no puede recibir `None`.** En
   `ReglasPorcentajes.decidir`, `if not linea.recurso_ide: return
   omitir(MOTIVO_SIN_RECURSO)` se evalúa **antes** de que se construya
   cualquier `AccionLinea(accion="escribir", ...)`. Y `sin_partida()` exige
   `accion == "escribir"`. Luego toda acción que llega a la guarda tiene
   `recurso_ide` truthy. Invariante confirmado en el constructor.

Ambas guardas eran código defensivo genuinamente inalcanzable. Quitarlas es
correcto y coherente con el criterio que ya aplicaba el bloque de capacidad de
F-002.

## 9. Procedencia en `docs/ARCHITECTURE.md` — correcta

- [x] **Quién, cuándo y con qué respaldo**, en el formato que el documento ya
      usa tras F-002:
      *«Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-20 ·
      preflight real del periodo 2026-07»*, con el detalle del caso (una jefa
      de obra, 2.132,28 €, `can = 0,385`, con un aviso que no retenía nada).
      Mismo patrón que el punto 7 (`#regla-capacidad`), que cita
      *«…el 2026-08-19 · decisión D2, specs/F-002…»*. El test
      `test_f013_r6_la_regla_lleva_su_procedencia` lo fija con un regex del
      patrón, no con una cadena literal.
- [x] **Nada atribuido a Administración.**
      `test_f013_r6_el_respaldo_es_el_preflight_real_de_julio` asserta
      explícitamente `"Administración" not in bloque`. Comprobado también a
      mano en el diff: el bloque cita únicamente el preflight real de julio.
      Este test es especialmente sensato — deja constancia de que clavar un
      interlocutor que no consta obliga a inventar una procedencia falsa para
      poner el test en verde.
- [x] **Fuente única, sin duplicar.** La regla se enuncia **una sola vez**
      (`test_..._tiene_su_ancla_en_la_fuente_unica` asserta
      `count('<a id="regla-sin-partida"></a>') == 1`). Todo lo demás
      **remite**: el README del transfer (fila «Regla C» → ancla),
      `reglas_porcentajes.py`, `registro_pipeline.py` y `registro_models.py`.
      Y `test_f013_r6_el_codigo_remite_en_vez_de_reenunciar` vigila que los
      dos módulos de implementación citen el ancla en vez de contar la regla
      con palabras propias.
- [x] **Se retiró una reenunciación que además ya era falsa.** El README decía
      «Sin casado: se escribe con `paride=0` y un `aviso` en el preflight,
      editable» — con F-013 eso es mentira. Sustituido por el enlace al ancla.
      Retirar la copia obsoleta en vez de actualizarla es exactamente lo que
      la regla de fuente única pide.
- [x] La renumeración 8/9/10 → 9/10/11 es coherente, y el cambio de una línea
      en `test_f002_fuente_unica.py` (`range(1, 11)` → `range(1, 12)`) es
      **necesario**: sin él, el punto nuevo del documento quedaría fuera de la
      guarda que existe justo para vigilarlo. No es aflojar un test, es
      extenderlo.

## 10. C5 — La sesión se cerró bien

- [x] **`tasks.md`: N/A justificado por `sdd: false`** — F-013 no tiene
      `specs/F-013-…/`, y `CHECKPOINTS.md` declara N/A lo que dependa de
      `tasks.md` en ese modo. El formato mínimo exigido es
      `F-XXX: <descripción>`; los commits usan el formato **más estricto**
      `F-013 Tn: …` (T1–T6) más el de arranque y el de la campaña. Ocho
      commits, uno por tarea, ninguno a `dev` ni a `main`.
- [x] **Sin ficheros temporales ni artefactos sin trackear.**
      `git status --porcelain` **vacío**, incluso después de reejecutar la
      campaña de mutación (que crea worktrees temporales).
- [x] `features.json` refleja el estado real: `F-013` en `in_progress`, a la
      espera de que el líder lo pase a `done` tras esta aprobación. **No se ha
      tocado**, como pedía el encargo, igual que `progress/current.md`.

## 11. Observaciones que NO bloquean

1. **`ruff`: 176 → 178 avisos (+2).** Verificado ejecutando: 178 en total, y
   los 2 nuevos son ambos `C408 Unnecessary dict() call` en las dos fábricas
   de fixtures del fichero de tests nuevo. Es **el mismo idioma** que ya usan
   `tests/conftest.py` (l. 259 y 268) y `tests/test_f002_capacidad.py` (l. 51).
   `ruff` es informativo en este repositorio (`[AVISO]`, no bloquea) y la
   alternativa era escribir el fichero nuevo con un estilo distinto al de sus
   vecinos. Se acepta. Los otros tres avisos que salieron en la primera pasada
   (`RUF015`) sí se corrigieron en T4.
2. **El texto de la casilla del front queda pobre** para el motivo nuevo
   («se borran ␣ y se escribe…»). Ya le pasaba a la sobrecarga desde F-002 y
   ahora afecta a dos motivos de tres. Es de `dedicacion-front`, que F-013
   tiene prohibido tocar. **Recomendación al líder: proponerlo al humano como
   feature aparte**, tal y como pide el implementer en su §8.
3. **El casado automático de partidas** que falló en el caso real de julio
   (obra `0025`) sigue fallando. Es otro problema y otra feature; queda bien
   delimitado en el §8 del informe.
4. **Deuda anterior, no de esta feature:** `services/dedicacion-front/` no
   tiene directorio de tests, así que nadie comprueba el front. Merece una
   decisión del humano en algún momento; no es de F-013.

## 12. Automejora del protocolo (propuesta, no aplicada)

`.claude/agents/reviewer.md` manda ejecutar la suite del servicio a mano
cuando la línea de `init.sh` viene de caché, pero **no advierte de que cada
servicio tiene su propio `.venv`**. Con el `python` del sistema, las suites de
`transfer` y `api` fallan con `ModuleNotFoundError` (`httpx`, `sqlalchemy`) y
un reviewer despistado podría leer eso como un rojo de la feature y rechazar
una rama sana — o, peor, dar por imposible la comprobación y fiarse de la
caché, que es justo lo que la instrucción viene a evitar.

**Propuesta (para que la apruebe el humano):** añadir a
`.claude/agents/reviewer.md`, en el protocolo de verificación de tests, una
línea del tipo: *«En repositorios multiservicio, ejecuta cada suite con el
intérprete de su propio entorno (`services/<svc>/.venv/Scripts/python.exe` en
Windows). El `python` del sistema no tiene las dependencias del servicio y su
fallo no es un fallo de la feature.»* Es genérica, así que si se aprueba
**debe portarse a `arnes-base`** en el mismo trabajo, según la regla de
propagación del `CLAUDE.md`.

---

## Veredicto final

**APPROVED.**

La feature hace exactamente lo que el encargo pedía y lo hace con el
mecanismo que ya existía, sin inventar contrato ni canal. Los cuatro criterios
se han verificado ejecutando; los invariantes que justifican la retirada de la
guarda muerta se han comprobado en el constructor y no en el punto de la
guarda; la procedencia está bien atribuida y en la fuente única; la campaña de
mutación se ha reejecutado entera con totales idénticos; y la fase RED se ha
contrastado contra el fichero histórico y es auténtica.

El trabajo de mayor valor no estaba en el encargo: identificar que confirmar
el pisado sin confirmar el «sin partida» podía borrar una línea de Sigrid sin
escribir su sustituta, comprobar que la guarda R32 de F-002 ya lo cubría, y
dejarlo probado para este tercer caso.
