<!-- progress/impl_F-002_fase2.md -->
# F-002 · Informe de implementación — Fase 2 (T7–T12, T15–T17)

> Rama `feature/F-002-reglas-postventa-conflicto`. Rigor **`critico`**.
> Spec v2: `specs/F-002-reglas-postventa-conflicto/` (los tres ficheros).
> La Fase 1 (T1–T5) está en `progress/impl_F-002.md` y no se ha tocado.
>
> **T6, T13 y T14 no se han ejecutado**: son `MANUAL (humano)` y ningún
> agente las hace. T14 exige además autorización expresa del humano para esa
> acción concreta. Siguen marcadas `[ ]` en `tasks.md`. Detalle en §7.

---

## 1. Qué se ha hecho, en tres frases

1. **La postventa solo puede acabar en una partida hoja activa**, casada por
   código exacto y elegida de forma determinista. El defecto que lo permitía
   —una variable llamada `hojas` que no filtraba por hoja— está cerrado, y
   con él la otra puerta de entrada: el override manual del front.
2. **La partida entra en la identidad de la línea** (Regla A), también en la
   obra normal. Una línea previa con otra partida deja de chocar y deja de
   borrarse.
3. **Aparece la Regla B**, que no existía en el repositorio: por trabajador y
   parte, la jornada no pasa de 1. Si se pasa, se avisa con sus cifras y no
   se escribe hasta que el humano confirma. Y, de propina, se cierra la vía
   por la que se podía **borrar un apunte de Administración sin escribir el
   sustituto** (R32).

Las tres cosas viven **solo en `dedicacion-transfer`**. Ni `dedicacion-api`
ni `dedicacion-front` se han tocado: la sobrecarga viaja como un `Conflicto`
más, con campos nuevos que tienen valor por defecto.

---

## 2. Tarea a tarea

### T7 — `ARCHITECTURE.md` punto 5 definitivo (D1)

Se escribe la decisión D1 completa: obra de `POSTVENTA_OBRA_COD`, **partida
hoja activa**, casado por **código exacto** (`0656` y `656` son códigos
distintos), cascadas solo sobre hojas activas y deterministas, y omisión con
motivo si no casa. Se retira la marca `PENDIENTE` de ese punto.

**Desviación deliberada, ordenada por el líder: la línea de procedencia.**
La spec pedía el literal `Confirmado por Administración el AAAA-MM-DD ·
<interlocutor>` (R4), y el test de T5 lo exigía con esa expresión regular.
**No consta que se haya hablado con Administración**: D1 y D2 las decidió el
humano del proyecto el 2026-08-19, respaldándolas con lecturas reales contra
Sigrid. Escribir «Administración» habría sido una **procedencia falsa** para
poner un test en verde, que es exactamente lo contrario de lo que R4
persigue. Lo escrito es:

```
Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
verificado contra Sigrid, ver `progress/sigrid_F-002.md`
```

**Y se adaptó el test, no la verdad.** `PATRON_PROCEDENCIA` ya no clava el
interlocutor: exige **quién**, **cuándo** y **el respaldo** tras el `·`. El
test quedó además **más fuerte** que el original, que contaba apariciones en
el documento entero (dos líneas de procedencia en la misma regla habrían
hecho pasar por confirmada a la de al lado): ahora se comprueba **bloque a
bloque**, una por ancla. Se añadió `test_f002_r4_la_procedencia_no_es_anonima`
como control de que «Confirmado el 2026-08-19» a secas no vale.

### T8 — fuente única de P4 y P5, y la Regla B por escrito

- **Punto 6** (`#regla-p4` / `#regla-conflicto`): solo la Regla A, con sus
  tres consecuencias enunciadas y su procedencia.
- **Punto 7 nuevo** (`#regla-capacidad`): la Regla B, su límite, su
  tolerancia, su alcance y por qué no detecta sobrecargas preexistentes.
- **Punto 4**: referencia cruzada hacia `#regla-capacidad`, para que quien
  toque la épsilon de `dedicacion-api/domain/estados.py` sepa que hay otra
  atada a ella.
- Cabecera: se retira la nota de «puntos sin validar».
- Los enunciados salen del `README.md` del transfer y de los docstrings de
  `reglas_porcentajes.py`, `registro_pipeline.py`, `partida_resolver.py` y
  `registro_models.py`, que pasan a **remitir**.

Los **cinco `xfail(strict=True)`** de la Fase 1 desaparecen (uno en T7,
cuatro aquí). La lista de frases prohibidas pasa de 2 ficheros a **5**, y se
añade `test_f002_r2_todo_el_que_pierde_su_enunciado_remite`: retirar el
enunciado sin dejar el enlace no es cerrar la fuente única, es borrar la
regla de la vista de quien lee ese fichero.

Los dos tests que vigilaban qué puntos seguían marcados como pendientes se
sustituyen por uno que recorre **los diez** y exige que ninguno lo esté, más
otro sobre la cabecera. Entre T8 y T12 el documento describe una conducta
que el código todavía no cumple: es deliberado (`design.md` §9).

### T9 — el destino de la postventa (D1)

- `partida_resolver.resolver_postventa`: `hojas = [n for n in nodos.values()
  if n.activa]` → `candidatos = partidas_hoja(nodos)`. Cierra tres cosas de
  golpe: la cascada ya no puede devolver un capítulo (R16), el universo pasa
  a ser **el mismo** que publica `partidas_postventa` para el desplegable
  (R17) y el desempate deja de depender del orden en que Sigrid devuelva las
  filas (R19).
- **`MOTIVO_PARTIDA_PV_NO_HOJA` se aplica al override manual del front**, no
  como guarda en `_destino_postventa`. `tasks.md` T9 lo dice así («caso del
  override manual») y `design.md` §3.5 sugería lo segundo; se ha seguido el
  primero **a propósito**: tras arreglar el resolver, una guarda en
  `_destino_postventa` sería código inalcanzable, que ningún test puede
  ejercitar y que la campaña de mutación no puede matar. El override sí es
  alcanzable —el usuario manda el `paride` que quiera— y está probado por los
  dos lados.
- `ReglasPorcentajes`: `capitulo_postventa` → `partida_postventa`,
  `self._capitulo` → `self._partida`. **El atributo `capitulo_postventa` del
  preflight conserva el nombre**: es contrato HTTP que lee el front. El
  desajuste queda documentado en el propio código.
- `conftest.py`: cuatro presupuestos de postventa (`hojas`, `capitulos`,
  `hojas_inactivas`, `orden_invertido`) y las trampas del presupuesto real
  —capítulo de código numérico `11`, `0656` frente a `656`, y partidas cuya
  descripción empieza por el código de otra obra—.

**No se ha añadido el ayudante `linea_previa_m(cod, can, paride)`** que
proponía `design.md` §2.1: `linea_previa(**kw)` ya admite esos tres campos y
los tests no lo necesitaron. Un ayudante de fixture que nadie llama es peso
muerto.

### T10 — Regla A

`campos_identidad()` devuelve `CAMPOS_CLAVE` **siempre** y **pierde el
parámetro `destino`**, como autoriza `design.md` §3.3: un parámetro que ya no
decide es una mentira en la firma y una rama que ningún test puede matar.

**Tests de la Fase 1 que hubo que tocar, y por qué** (§4 los lista uno a uno).

### T11 — Regla B, detección

- En `reglas_porcentajes.py`: `LIMITE_CAPACIDAD`, `EPSILON_CAPACIDAD`,
  `PREFIJO_CLAVE_SOBRECARGA`, `MOTIVO_SOBRECARGA`, `Capacidad`,
  `es_linea_mensual`, `evaluar_capacidad`, `clave_sobrecarga`. Todo funciones
  puras: sin I/O, sin `settings`, sin cliente.
- `es_linea_mensual` **sustituye además** al `(ls.hora_codigo or
  "").upper().startswith("M")` que el pipeline tenía escrito a mano para el
  `contexto`: eran la misma regla en dos sitios.
- En `registro_models.py`: `Conflicto` gana `motivo`, `suma_existente`,
  `suma_total` y `exceso`, **todos con defecto**.
- En `registro_pipeline.preflight`: paso 7 bis, dentro del mismo bucle por
  parte, **después** de los conflictos de pisado (R30).

**La tolerancia `0,00005` tiene test propio que lee el fichero de la API.**
`test_f002_r26_la_tolerancia_es_la_del_cuadrante` abre
`services/dedicacion-api/domain/estados.py` y falla si `_EPSILON` deja de ser
`Decimal("0.005")`. Es la única forma de que las dos no se separen sin que
nadie se entere; no toca la API, solo la lee.

### T12 — Regla B, escritura y salvaguardas

- **R28**: una sobrecarga sin confirmar bloquea sus registros y los lista en
  `omitidas` con `MOTIVO_SOBRECARGA`. Esto cambia, **sin tocar la API**, el
  estado que `dedicacion-api` persiste en `asignacion.sigrid_estado`: pasa de
  quedarse con el estado anterior (que miente) a `omitido` con el motivo
  real. Los pisados sin confirmar **no** entran ahí, y hay test de control.
- **R29**: confirmar una sobrecarga escribe y no borra nada. Sale gratis
  porque su `lineas` está vacío, y se prueba.
- **R32**: un conflicto confirmado solo emite sus borrados si **al menos uno**
  de sus registros llega a escribirse. Es el requisito más importante de la
  feature después de la propia Regla A, y su RED (§3.6) enseña el fallo real.
- **R13** conserva la deduplicación por `ide` y su test se reexpresa (§4).

`conftest.py` gana un **segundo trabajador con código `M*`** (emp 12 →
recurso 400). Sin él, el escenario de R32 no se puede montar: al bloquearse
la única línea, el pipeline sale por el atajo `if not a_escribir: return` y
nunca llega al paso del borrado, con lo que el test pasaría por el motivo
equivocado.

---

## 3. Fase RED (obligatoria en `critico`)

Todas las trazas son **RED real contra el árbol**, no roturas simuladas en
copia aislada: cada tarea de la Fase 2 entrega conducta nueva, así que sus
tests fallan de verdad antes de escribir el código. Comando siempre desde
`services/dedicacion-transfer`.

### 3.1 · T7 / R4 — no había procedencia en ninguna regla

```
$ .venv/Scripts/python.exe -m pytest tests/test_f002_fuente_unica.py -q --no-header -k test_f002_r4
...
E       assert 0 >= 2
E        +  where 0 = len([])
E        +    where [] = <function findall>('Confirmado por [^\n·]+ el \d{4}-\d{2}-\d{2} · [^\n]+', '<!-- docs/ARCHITECTURE.md -->…')
tests\test_f002_fuente_unica.py:194: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f002_fuente_unica.py::test_f002_r4_procedencia_fechada
1 failed, 1 passed, 38 deselected in 0.12s
```

Tras escribir el punto 5: `92 passed, 4 xfailed`.

### 3.2 · T8 — la fuente única de P4/P5 no estaba cerrada

```
$ .venv/Scripts/python.exe -m pytest tests/test_f002_fuente_unica.py -q --no-header -rf
...
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-capacidad]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_el_ancla_no_esta_repetida[regla-capacidad]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_ningun_punto_sigue_pendiente[6]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_ningun_punto_sigue_pendiente[10]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_la_cabecera_ya_no_avisa_de_puntos_sin_validar
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_los_docstrings_remiten_p4_p5
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_todo_el_que_pierde_su_enunciado_remite[reglas_porcentajes.py]
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_todo_el_que_pierde_su_enunciado_remite[registro_pipeline.py]
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_todo_el_que_pierde_su_enunciado_remite[partida_resolver.py]
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_todo_el_que_pierde_su_enunciado_remite[registro_models.py]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta3-aunque tenga otra partida]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta4-la partida es la del C\xd3DIGO DE LA OBRA original]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta6-la misma partida en ese parte]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta7-imputando al CAP\xcdTULO]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta9-el CAP\xcdTULO (obrparpar) que corresponde a la obra original]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta10-l\xednea(s) M* del recurso con el mismo c\xf3digo Y la misma partida]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta11-la partida cuyo c\xf3digo ES el c\xf3digo de la obra original]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas[ruta12-La identidad de la l\xednea en el parte es recurso + mes + c\xf3digo]
FAILED tests/test_f002_fuente_unica.py::test_f002_r4_procedencia_fechada[regla-conflicto]
FAILED tests/test_f002_fuente_unica.py::test_f002_r4_procedencia_fechada[regla-capacidad]
20 failed, 39 passed in 2.45s
```

Tras aplicar T8: `115 passed`, sin un solo `xfail`.

### 3.3 · T9 — el resolver devolvía capítulos y dependía del orden de las filas

```
$ .venv/Scripts/python.exe -m pytest tests/test_f002_postventa.py -q --no-header -rf
...
        assert nodo.cod == min(candidatos), (nodo.cod, candidatos)
E       AssertionError: ('0678', ['0656', '0664', '0678'])
E       assert '0678' == '0656'
=========================== short test summary info ===========================
FAILED tests/test_f002_postventa.py::test_f002_r16_un_capitulo_no_es_destino[0678]
FAILED tests/test_f002_postventa.py::test_f002_r16_un_capitulo_no_es_destino[11]
FAILED tests/test_f002_postventa.py::test_f002_r16_el_capitulo_no_llega_al_paride_de_la_linea
FAILED tests/test_f002_postventa.py::test_f002_r16_un_override_manual_a_un_capitulo_se_omite
FAILED tests/test_f002_postventa.py::test_f002_r17_el_automatico_y_el_desplegable_comparten_universo[capitulos]
FAILED tests/test_f002_postventa.py::test_f002_r19_la_eleccion_no_depende_del_orden_de_las_filas
FAILED tests/test_f002_postventa.py::test_f002_r19_el_desempate_es_por_codigo
7 failed, 14 passed in 0.42s
```

Los dos de R19 son los que enseñan el defecto silencioso: **con las mismas
filas en orden inverso, la partida elegida cambiaba**. Tras T9:
`136 passed`.

### 3.4 · T10 — en la obra normal la partida no distinguía

```
$ .venv/Scripts/python.exe -m pytest tests/test_f002_conflicto.py -q --no-header -rf
_________________ test_f002_r21_otra_partida_no_es_conflicto __________________
>       assert criterio_choque(linea_previa(paride=0), accion(paride=80001),
                               mias=set()) is False
E       AssertionError: assert True is False
E        +  where True = criterio_choque(LineaSigrid(ide=5001, reside=200, …, paride=0),
                                          AccionLinea(…, destino='obra', paride=80001), mias=set())
tests\test_f002_conflicto.py:189: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f002_conflicto.py::test_f002_r14_la_identidad_es_subconjunto_de_la_clave
FAILED tests/test_f002_conflicto.py::test_f002_r14_todo_campo_comparado_sabe_leerse_de_las_dos_partes
FAILED tests/test_f002_conflicto.py::test_f002_r14_cambiar_la_tupla_cambia_la_clave_y_el_criterio
FAILED tests/test_f002_conflicto.py::test_f002_r20_la_partida_entra_en_la_identidad[obra-80001]
FAILED tests/test_f002_conflicto.py::test_f002_r20_los_cuatro_campos_deciden
FAILED tests/test_f002_conflicto.py::test_f002_r21_otra_partida_no_es_conflicto
6 failed, 15 passed in 0.30s
```

Ese `assert True is False` **es la avería**: la línea previa sin partida se
daba por «la misma línea» que la nuestra, y confirmar el pisado la borraba.

### 3.5 · T11 — la Regla B no existía

Dos REDs, porque el entregable tiene dos mitades. Primero, la regla no
existe ni como concepto:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f002_capacidad.py -q --no-header
E   ImportError: cannot import name 'EPSILON_CAPACIDAD' from
    'application.services.reglas_porcentajes'
1 error in 1.10s
```

Y después, con las funciones puras ya escritas pero **sin cablear el paso
7 bis**, la RED de conducta (el preflight no emite nada):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f002_capacidad.py -q --no-header -rf
>       c = _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos[0]
E       IndexError: list index out of range
=========================== short test summary info ===========================
FAILED tests/test_f002_capacidad.py::test_f002_r25_sobrecarga_emite_conflicto
FAILED tests/test_f002_capacidad.py::test_f002_r25_con_su_detalle_numerico
FAILED tests/test_f002_capacidad.py::test_f002_r27_el_motivo_distingue
FAILED tests/test_f002_capacidad.py::test_f002_r30_pisado_y_sobrecarga_a_la_vez
FAILED tests/test_f002_capacidad.py::test_f002_r30_el_orden_es_pisado_primero
FAILED tests/test_f002_capacidad.py::test_f002_r31_la_suma_supone_los_pisados_confirmados
FAILED tests/test_f002_capacidad.py::test_f002_r33_el_conflicto_serializa_los_campos_de_siempre
7 failed, 25 passed in 0.52s
```

Tras cablear el paso 7 bis: `174 passed`.

### 3.6 · T12 / R32 — se borraba la línea de Administración sin escribir nada

**Esta es la RED que más importa.** Contra el árbol tal como quedó tras T11:
el humano confirma el pisado y **no** confirma la sobrecarga; el borrado se
emite por conflicto confirmado y la escritura se bloquea por registro.

```
$ .venv/Scripts/python.exe -m pytest tests/test_f002_pipeline.py -q --no-header -rf
______________________ test_f002_r32_no_se_borra_si_no_se_escribe ______________________
        res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                      pisar_claves={clave_pisado})

>       assert cli.borrados() == [], cli.borrados()
E       AssertionError: [5001]
E       assert [5001] == []
E         Left contains one more item: 5001

tests\test_f002_pipeline.py:364: AssertionError
------------------------------ Captured log call ------------------------------
WARNING  registro_pipeline:334 [registro] sobrecarga recurso=200 parte=PT26/00251 existente=0.9 nueva=0.4 total=1.3
=========================== short test summary info ===========================
FAILED tests/test_f002_pipeline.py::test_f002_r28_queda_listada_en_omitidas_con_motivo
FAILED tests/test_f002_pipeline.py::test_f002_r32_no_se_borra_si_no_se_escribe
2 failed, 16 passed in 0.52s
```

La línea 5001 de Administración se borraba y **su sustituta no se escribía**:
pérdida de dato neta y silenciosa. Tras la guarda: `181 passed`.

---

## 4. Tests de la Fase 1 que hubo que ajustar, uno a uno

La spec avisaba de que varios tests de T4 estaban escritos **a propósito**
para fijar la conducta contraria y tener que tocarlos. Aquí está cada uno.

### 4.1 · `tests/test_f002_conflicto.py`

| Test de la Fase 1 | Qué se hizo | Por qué |
|---|---|---|
| `test_f002_r14_en_obra_normal_la_partida_no_distingue` | **Se da la vuelta** como `test_f002_r20_la_partida_entra_en_la_identidad[obra]` | Fijaba la conducta que D2 invalida. No se borra: se invierte, que es para lo que se escribió. |
| `test_f002_r14_en_postventa_la_partida_si_distingue` | **Se conserva** como el caso `[postventa]` del mismo test parametrizado | La conducta no cambia en postventa; lo que cambia es que ahora es **la misma** que en la obra normal, y parametrizar lo deja escrito. |
| `test_f002_r14_lo_nuestro_no_choca_con_nosotros_mismos` | **Se renombra** a `test_f002_r22_...` | Es R22, no R14. Solo cambia el nombre y el `paride` de la línea previa (ver abajo). |
| `test_f002_r14_una_synckey_ajena_si_choca`, `..._una_linea_sin_synckey_choca` | Renombrados a `r22`, y la línea previa pasa a `paride=80001` | Con `paride=0` habrían pasado **por el motivo equivocado**: no chocarían por la partida, no por la `synckey`. Un test que pasa por la razón que no es, no prueba nada. |
| `test_f002_r14_choca_el_mismo_recurso_y_codigo_en_otro_dia`, `..._no_choca_otro_recurso`, `..._no_choca_otro_codigo_de_hora` | La línea previa pasa a `paride=80001` | Mismo motivo: aislar el campo que cada uno vigila. |
| `test_f002_r14_la_identidad_es_subconjunto_de_la_clave`, `..._todo_campo_comparado_sabe_leerse_de_las_dos_partes`, `..._cambiar_la_tupla_cambia_la_clave_y_el_criterio` | Llaman a `campos_identidad()` sin argumento | Consecuencia mecánica de quitarle el parámetro. Ninguna aserción cambia de sentido. |

### 4.2 · `tests/test_f002_pipeline.py` — el bloque de R13

El escenario original de R13 (dos pendientes con partidas distintas chocando
con la misma línea previa) **deja de ser alcanzable**: con la partida dentro
de la identidad, una línea existente casa como mucho con una identidad.

- `test_f002_r13_las_dos_lineas_chocan_con_la_misma` (la premisa) y el
  helper `_dos_lineas_contra_la_misma` **se reconvierten** en los tests de
  R21 (`design.md` §5.6): esas dos líneas ahora **no** chocan y ese apunte de
  Administración **no** se borra. Sus cantidades se bajan a 0,3 + 0,4 sobre
  una previa de 0,2 para que la Regla B no meta por medio un conflicto de
  otro tipo; el mismo escenario pasado de 1 está en
  `test_f002_r25_el_escenario_viejo_de_r13_ahora_es_una_sobrecarga`.
- `test_f002_r13_borrado_unico_por_ide` **se reexpresa**: inyecta dos
  `Conflicto` que comparten `hmores.ide` (uno es `dataclasses.replace` del
  otro con otra clave) y comprueba que sale un solo `DELETE`. La salvaguarda
  se queda; lo que ya no existe es la ruta que la disparaba.
- `test_f002_r13_dos_lineas_distintas_se_borran_las_dos` y
  `..._sin_confirmar_no_se_borra_nada` **conservan sus aserciones**; solo
  cambia el `paride` de las líneas previas, para que sigan siendo la misma
  identidad que la nuestra.

### 4.3 · `tests/test_pipeline_offline.py` — la red de seguridad de T3

**Ninguna aserción cambia.** Cambia **un dato de entrada**: el `paride` de la
línea previa del `ClienteFalso`, de 0 a 80001, con el motivo escrito en el
propio fichero. Sin ese dato, este fichero dejaría de ejercitar el camino del
pisado de punta a punta —que es a lo que vino— y pasaría a probar dos veces
el caso «no hay conflicto». El caso nuevo (previa con otra partida) tiene sus
propios tests en `test_f002_pipeline.py`.

`design.md` §3.8 anticipaba que la aserción `c.clave == "200|202607|5|80001"`
podía quedarse sin conflicto que la llevara. Con el ajuste del dato, sigue
habiendo conflicto y la aserción sigue siendo cierta **por el motivo bueno**.

### 4.4 · `tests/test_f002_reglas.py`

`CAPITULO_PV` → `PARTIDA_PV` y `capitulo_postventa=` → `partida_postventa=`
en dos llamadas. Renombrado mecánico, sin cambio de aserciones.

---

## 5. Campaña de mutación: de 8 supervivientes a 1 equivalente

Informe completo: `progress/mutacion_F-002.md`.

Primera pasada: **40 mutantes, 32 muertos, 8 supervivientes**. Rigor
`critico` exige cero o justificación escrita por cada uno, así que se
atacaron los ocho:

| # | Superviviente | Qué se hizo |
|---|---|---|
| 1 | `registro_pipeline:293` `and es_linea_mensual(ls)` → `or` | **Test nuevo.** Con `or`, el `contexto` de un conflicto colaba líneas mensuales **de otro trabajador**: un aviso que acusa al empleado equivocado. Dos tests: el negativo y su control positivo. |
| 2, 3 | `int(a.recurso_ide or 0)` → `or 1` (dos sitios) | **Código más simple.** `grupo` solo tiene acciones «escribir», y P1 omite toda línea sin recurso: el `or 0` era una guarda que ningún test puede ejercitar. Se quita, y el mutante desaparece en vez de justificarse. |
| 4 | `int(ls.reside or 0)` → `or 1` | Ídem: `existentes` viene filtrado por el cliente a los recursos del grupo. |
| 5, 6, 7 | `round(cap.…, 4)` → `round(…, 5)` (tres sitios) | **Test nuevo** con un `can` previo de seis decimales (0,123456): ningún test ejercitaba el cuarto decimal, así que redondear a 4 o a 5 daba lo mismo. |
| 8 | `exceso > EPSILON` → `>=` | **Equivalente, y se demuestra.** |

Segunda pasada: **34 mutantes, 33 muertos, 1 superviviente.**

**El superviviente que queda es demostrablemente equivalente.** `>` y `>=`
solo difieren si `exceso == EPSILON_CAPACIDAD` exactamente, y ese caso **no
existe** en coma flotante de doble precisión: para `total` en `[1, 2)` la
resta `total - 1.0` es exacta, así que solo puede dar múltiplos del ULP de esa
franja (`2⁻⁵²` ≈ 2,2e-16), y el `double` más cercano a 0,00005 no lo es. Se
comprueba de un tirón: `(1.0 + 0.00005) - 1.0` vale `5.0000000000105516e-05`,
que no es `0.00005`.

En vez de dejar eso en un comentario que nadie ejecuta, la demostración es un
test: `test_f002_r26_el_borde_exacto_de_la_tolerancia_no_existe`. Y la
conducta del borde sí está probada por los dos lados
(`test_f002_r26_la_tolerancia_decide_el_borde[...]`: media épsilon no avisa,
el doble sí).

---

## 6. Evidencias

Números **medidos**, no estimados, con el árbol tal como queda al cerrar.

| Evidencia | Valor | Cómo se obtiene |
|---|---|---|
| **Tests ejecutados** (transfer) | **187 pasan**, 0 fallan, 0 `xfail` | `python -m pytest tests -q` en `services/dedicacion-transfer` |
| Tests ejecutados (api) | 21 pasan | `python -m pytest -q` en `services/dedicacion-api` |
| Tests ejecutados (raíz) | 11 pasan | `python -m pytest tests -q` |
| **Cobertura de las líneas cambiadas** | **99,1 %** (107/108, umbral 80 %) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados / supervivientes** | **34 / 1** (33 muertos, 0 timeouts) | `python -m harness.mutacion --feature F-002 --workers 1` |
| **Tiempo de la suite** | **0,52 s** (transfer), 0,09 s (api), 0,16 s (raíz) | lo imprime la propia suite |
| Tiempo de la campaña de mutación | 35,3 s | lo imprime la campaña |
| Lint (`ruff`) | 180 avisos (eran 174) | no bloquea; ver abajo |

### 6.1 · La línea cambiada que no está cubierta

Es **la misma que en la Fase 1**, y no es de esta fase: el `import` de
`clave_conflicto` en `services/dedicacion-transfer/interface_adapters/api/
app.py`, que T3 añadió. Ese módulo no lo importa ningún test —levantarlo
exige `fastapi` y un `settings` real— así que `coverage` no tiene datos suyos
y la puerta cuenta su línea ejecutable como no cubierta. **No hay ninguna
línea de producción de la Fase 2 sin cubrir**; se ha comprobado cruzando el
alcance del arnés con `coverage.json`.

De hecho, la única que había (`partida_resolver.py:83`, el cuarto escalón de
la cascada: casado por **nombre** de obra) se cubrió con dos tests nuevos.

### 6.2 · Los seis avisos nuevos de `ruff`

De 174 a 180. Los seis son **el mismo patrón que ya usaba toda la suite**:
`I001` por el bloque `from tests.conftest import …` que va después de los
imports de la aplicación (lo tienen los seis ficheros de test del servicio),
`C408` por el `dict(...)` del ayudante `accion()` (copiado del que ya existía
en `test_f002_conflicto.py`) y tres `B009` por los `getattr(pf, "…")` de los
atributos que el preflight adjunta con `setattr` —acceder a ellos por punto
sería peor, no mejor—. Se limpiaron los que sí eran deuda evitable (`RUF059`,
`RUF015`). `LINT_BLOQUEA=0`: informativo.

### 6.3 · Portero

```
$ bash harness/init.sh
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/dedicacion-api): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
[OK] PUERTA COBERTURA: 99.1% de 108 líneas cambiadas cubiertas (107/108, umbral 80%, nivel critico)
[OK] Ningún .env versionado
[OK] Rama actual: feature/F-002-reglas-postventa-conflicto
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

---

## 7. Verificaciones `MANUAL (humano)` pendientes

Ninguna la puede hacer un agente. Las tres siguen en `[ ]` en `tasks.md`.

### T6 — los dos cabos de Administración · **PENDIENTE**

1. **Trasladar el aviso de las cuatro partidas duplicadas** sin cero inicial
   del presupuesto de postventa (`656`, `664`, `680`, `693`, colgando de la
   raíz en vez de `CD`; tabla en `requirements.md` §2 · D1 y volcado en
   `progress/sigrid_F-002.md`). No rompen nada hoy: `normalize_code` no quita
   ceros a la izquierda y hay test que lo fija (R18). Son ruido de
   presupuesto y alguien de Administración debe saberlo.
2. **La procedencia de R4** se resolvió sin Administración, por instrucción
   expresa del líder y para no escribir una procedencia falsa (§2, T7). Si
   más adelante Administración confirma o corrige D1/D2, **la línea de
   `ARCHITECTURE.md` se actualiza y el test sigue pasando**: el patrón no
   clava el interlocutor.

**Opcional, no bloqueante:** las consultas de solo lectura **C3** y **C5**
(`requirements.md` §3) miden cuánta sobrecarga real va a aflorar el primer
día. Ahora tienen más valor que antes de esta fase, porque la Regla B ya está
implementada y esas cifras dicen cuántos avisos verá el humano. **C1 y C4 ya
no tienen motivo.**

### T13 — casado contra Sigrid, sin escribir · **PENDIENTE**

```
cd services/dedicacion-transfer
python prueba_escritura_porcentajes.py capitulos
python prueba_escritura_porcentajes.py estado --ano 2026 --mes 8
python prueba_escritura_porcentajes.py preflight --ano 2026 --mes 8
```

(previa edición de `LINEAS_PRUEBA` y `OBRA_ORIGEN_PRUEBA` con empleados
reales con código `M*`). Qué mirar, ahora con más razón que en la v1 de la
spec: que **la partida resuelta sea una hoja** y que, si el trabajador ya
tiene líneas `M*` en el parte, **aparezca el conflicto de sobrecarga con sus
cuatro cifras**. Solo lectura, pero exige el `.env` con la function key:
**ningún agente lo toca.** Volcado a `progress/sigrid_F-002.md`.

### T14 — escritura real en la obra de pruebas · **PENDIENTE**

```
python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 8
python prueba_escritura_porcentajes.py verificar
python prueba_escritura_porcentajes.py limpiar --confirmar
```

Exige `OBRA_PRUEBAS_FORZAR=true` y **autorización expresa del humano para
esta acción concreta** (`CLAUDE.md`, reglas duras). **Ningún agente la lanza
por su cuenta**, ni siquiera con la feature aprobada.

---

## 8. Qué queda fuera del alcance, y qué hay que saber antes de producción

- **`OBRA_PRUEBAS_FORZAR` sigue a `true`** y no se ha tocado ningún `.env`.
  Las reglas están escritas e implementadas, pero **nadie las ha visto
  funcionar contra Sigrid**: eso es T13/T14.
- **El front no lee los campos nuevos**, y esto tiene un coste medido que
  `design.md` §8 detalla y que conviene repetir aquí porque el humano lo va a
  ver en pantalla: una sobrecarga se pinta con el texto de un pisado («se
  borran ␣ y se escribe 40 %»), la casilla dice **Pisar** cuando confirmar no
  pisa nada, las cuatro cifras que justifican el aviso viajan pero no se
  enseñan, y el resumen suma pisados y sobrecargas juntos. **La seguridad no
  se pierde** (sin confirmar no se escribe, confirmar una sobrecarga no borra
  nada, confirmar un pisado que no llega a escribirse tampoco), pero el
  modelo mental que induce es el equivocado. La feature de front que lo
  arregla es pequeña —una rama en `pintarModalPreflight`— y **no está en
  F-002**: va al backlog.
- **La Regla B no detecta sobrecargas preexistentes** en las que no
  participamos. Si un parte ya tiene 1,4 de un trabajador y no escribimos
  nada suyo, no avisa. Consciente, documentado en `ARCHITECTURE.md` y
  diagnosticable con C3.
- **El atributo `capitulo_postventa` del preflight sigue llamándose así**
  aunque lo que lleva es una partida. Es contrato HTTP; renombrarlo toca los
  tres servicios a la vez y es una feature aparte.
- **`test_pipeline_offline.py` arrastra un aviso de pytest** heredado
  (`test_preflight` devuelve el `Preflight` en vez de aserciones). No es de
  esta feature y no se ha tocado para no mezclar; es candidato a limpieza.

---

## 9. Ficheros tocados en la Fase 2

**Producción (5):**

- `docs/ARCHITECTURE.md` — puntos 4, 5, 6, 7 (nuevo) y cabecera; renumerado
  de 7-9 a 8-10.
- `services/dedicacion-transfer/README.md` — tabla de remisión.
- `services/dedicacion-transfer/application/services/reglas_porcentajes.py` —
  docstring, `campos_identidad()`, `MOTIVO_PARTIDA_PV_NO_HOJA`, toda la Regla
  B, `partida_postventa`.
- `services/dedicacion-transfer/application/services/partida_resolver.py` —
  `partidas_hoja(nodos)` y docstrings.
- `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` —
  docstring, `_nueva`, `_es_hoja_activa_pv`, validación del override, paso
  7 bis, R28 y R32.
- `services/dedicacion-transfer/domain/models/registro_models.py` — docstring
  y los cuatro campos nuevos de `Conflicto`.

**Tests (6):**

- `tests/conftest.py` — cuatro presupuestos, `tipdes` en `_fila`, recurso 400.
- `tests/test_f002_postventa.py` — **nuevo** (R15–R19).
- `tests/test_f002_capacidad.py` — **nuevo** (R23–R27, R30, R31, R33).
- `tests/test_f002_conflicto.py` — R20, R21, R22.
- `tests/test_f002_pipeline.py` — R21, R13 reexpresado, R28, R29, R32.
- `tests/test_f002_fuente_unica.py` — R1–R4 sin `xfail`.
- `tests/test_f002_reglas.py` y `tests/test_pipeline_offline.py` — renombrado
  y un dato de entrada.

**Progreso:** `progress/mutacion_F-002.md` (regenerado, con el análisis del
superviviente completo) y este informe.

**Commits** (uno por tarea, más dos de cierre):

```
F-002 T7:  punto 5 de ARCHITECTURE definitivo (D1) con su procedencia
F-002 T8:  cierra la fuente única de P4 y P5, y escribe la Regla B
F-002 T9:  la partida de postventa solo puede ser una hoja activa (D1)
F-002 T10: Regla A, la partida entra en la identidad de la línea
F-002 T11: Regla B (capacidad), detección
F-002 T12: Regla B en la escritura, y la guarda que evita perder datos
F-002 T15: campaña de mutación, de 8 supervivientes a 1 equivalente
F-002:     aseo de lint en los tests nuevos
```

Ningún `git push`, ningún PR, ningún commit en `dev` ni en `main`.
