<!-- specs/F-002-reglas-postventa-conflicto/requirements.md -->
# F-002 · Requisitos — Fijar las reglas P4 y P5

> **Rigor `critico`.** Estas dos reglas deciden qué se BORRA y qué se ESCRIBE
> en los partes de trabajo de Sigrid. Hasta que estén cerradas no se escribe
> en producción (`OBRA_PRUEBAS_FORZAR` se queda a `true`).

## Contexto

El repositorio enuncia las reglas P1–P5 en **cinco sitios distintos**
(`docs/ARCHITECTURE.md`, el README del transfer y tres docstrings), y en dos
de ellas los enunciados **se contradicen**. Esta feature no puede decidirse
leyendo el código: las dos versiones de cada regla son defendibles y la
respuesta la tiene **Administración**. El código actual implementa una de las
dos versiones de P4 y una interpretación ambigua de P5; que esté escrito no
lo convierte en correcto.

Servicio afectado: **`dedicacion-transfer`** (las reglas P1–P5 viven ahí) más
`docs/ARCHITECTURE.md` en la raíz. Ni la API ni el front tocan estas reglas.

---

## 1. Requisitos EARS

### 1.1. Fuente única de verdad (no dependen de Administración)

- **R1.** El sistema debe declarar las reglas P1–P5 **una sola vez**, en la
  sección «Semántica de dominio imprescindible» de `docs/ARCHITECTURE.md`,
  con un ancla estable por regla (`#regla-p1` … `#regla-p5`).

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
  <interlocutor>`).

- **R5.** El sistema no debe citar el valor literal del código de la obra de
  postventa en ningún docstring ni comentario: debe referirse al ajuste
  `POSTVENTA_OBRA_COD`. El único sitio donde vive el valor es `.env` /
  `.env.example` / el defecto de `config/settings.py`.

### 1.2. Reglas NO en disputa, fijadas por test (no dependen de Administración)

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

- **R13.** SI dos o más líneas pendientes chocan con la **misma** línea
  existente de Sigrid, ENTONCES el sistema debe emitir **un único** borrado
  para ese `hmores.ide` y contarlo una sola vez en `borradas`.

- **R14.** El sistema debe derivar la clave de conflicto y el criterio de
  choque de **una sola función**, de modo que no puedan divergir.

### 1.3. Requisitos BLOQUEADOS hasta la respuesta de Administración

> No se implementan hasta que D1 y D2 (sección 2) estén cerradas por escrito.
> Su redacción final se ajusta a la respuesta; lo que queda fijo es que
> tienen que existir y tener test.

- **R15 (depende de D1.1).** CUANDO no exista en Sigrid ninguna obra con el
  código de `POSTVENTA_OBRA_COD`, el sistema debe omitir **todas** las líneas
  de postventa con el motivo exacto de la obra no encontrada, y el preflight
  debe hacerlo visible como aviso, no como silencio.

- **R16 (depende de D1.2).** CUANDO una línea de postventa se escribe, el
  sistema debe fijar `hmores.paride` al `ide` del nodo de `obrparpar` de la
  obra de postventa **del tipo que Administración confirme** (partida hoja
  *o* capítulo con hijos), y SI el nodo casado no es de ese tipo, ENTONCES
  debe omitir la línea con motivo en vez de escribirla.

- **R17 (depende de D1.2).** El sistema debe ofrecer en
  `preflight.partidas_postventa` exactamente el mismo conjunto de nodos entre
  los que elige la resolución automática, para que el desplegable del front y
  el automático no apunten a universos distintos.

- **R18 (depende de D2).** CUANDO en la obra normal ya exista una línea `M*`
  del mismo recurso en el parte del mes, el sistema debe tratarla como
  conflicto **según el criterio que Administración confirme** (con o sin
  comparación de partida), en cualquier día del mes, y no escribir nada de esa
  línea hasta que el humano confirme el pisado.

- **R19 (depende de D2).** MIENTRAS el destino sea la obra de postventa, el
  sistema debe considerar la partida parte de la identidad de la línea, de
  forma que un mismo recurso pueda tener una línea legítima por cada obra
  original.

---

## 2. Decisiones abiertas que solo puede cerrar Administración

> Esta sección es el motivo de ser de la feature. Cada decisión trae: las dos
> versiones enfrentadas con fichero y línea, qué se escribiría distinto en
> Sigrid, la pregunta cerrada que hay que hacer, y la consulta de LECTURA que
> corrobora la respuesta.
>
> **Las consultas NO se han ejecutado.** Van contra `sigrid-api`
> (`POST /api/sql/read`, base `ruesma`), son de solo lectura y las lanza el
> humano cuando lo decida.

### D1 — P5: dónde y contra qué se imputa la línea de postventa

#### D1.1 · El código de la obra de postventa

**Versión A — `POSTV2`**
- `services/dedicacion-transfer/README.md:23` — «**Postventa**: obra `POSTV2`
  (`POSTVENTA_OBRA_COD`)».
- Coincide con `services/dedicacion-transfer/.env.example` (línea
  `POSTVENTA_OBRA_COD=POSTV2`), con el defecto de
  `services/dedicacion-transfer/config/settings.py:39` y con
  `docs/ARCHITECTURE.md:137`.

**Versión B — `postventa-2`**
- `services/dedicacion-transfer/application/services/reglas_porcentajes.py:15`
  — «(config POSTVENTA_OBRA_COD, hoy `'postventa-2'`)».

**Qué se escribiría distinto en Sigrid.** El código no se escribe en ningún
campo: se usa para *localizar* la obra (`SELECT … FROM obr JOIN con ON
con.ide = obr.ide WHERE con.cod = ?`). Si el código configurado no existe:

- Con el código correcto: la línea de postventa del encargado (10 %, MENC,
  9.000 €/mes, julio 2026) se escribe en `hmores` con
  `obride = ide(obra de postventa)`, `can = 0.1`, `pre = 9000`, `tot = 900`,
  `fec = 20260731`.
- Con el código equivocado: `_destino_postventa` devuelve motivo «obra de
  postventa '<cod>' no encontrada en Sigrid» y **todas** las líneas de
  postventa se omiten. No hay error ni excepción: el registro termina «OK»
  con la postventa fuera. Es un fallo silencioso, que es el peor.

**Pregunta cerrada para Administración**

> En Sigrid, ¿cuál es el **código exacto** —el que aparece en el campo
> *Código* de la ficha de obra— de la obra donde queréis ver imputada la
> dedicación de postventa? Escríbelo tal cual, distinguiendo mayúsculas:
> `POSTV2`, `postventa-2`, u otro.
> ¿Hay **una sola** obra de postventa, o hay varias (por año, por delegación)?

**Consulta de corroboración — C1**

```jsonc
POST /api/sql/read
{
  "database": "ruesma",
  "sql": "SELECT obr.ide AS obride, con.cod AS cod, con.res AS res, obr.cenide AS cenide FROM obr JOIN con ON con.ide = obr.ide WHERE con.cod = ? OR con.cod = ? OR con.res LIKE ? ORDER BY con.cod",
  "parameters": ["POSTV2", "postventa-2", "%POSTVENT%"],
  "timeout_seconds": 60,
  "max_rows": 500
}
```

Lee: qué obras existen con esos códigos o con «POSTVENT» en la descripción.
Si devuelve **una** fila, ese es el código. Si devuelve varias, D1.1 no está
cerrada: hay que preguntar cuál.

#### D1.2 · ¿PARTIDA (hoja) o CAPÍTULO (nodo con hijos)?

**Versión A — PARTIDA**
- `services/dedicacion-transfer/README.md:23-26` — «la **partida** es la del
  CÓDIGO DE LA OBRA original (0707 → partida "0707 · …")».
- `services/dedicacion-transfer/application/services/partida_resolver.py:9-11`
  y `:51` — «la **partida** cuyo código ES el código de la obra original».

**Versión B — CAPÍTULO**
- `services/dedicacion-transfer/application/services/reglas_porcentajes.py:15-17`
  — «imputando al **CAPÍTULO** (obrparpar) que corresponde a la obra
  original. Sin capítulo casado no se escribe».
- `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:6-8`,
  `:13`, `:83` — «la OBRA DE POSTVENTA con el **CAPÍTULO** (obrparpar)».
- `docs/ARCHITECTURE.md:142-144` señala la contradicción sin resolverla.

En Sigrid **los dos son la misma tabla**, `obrparpar`: un nodo es *capítulo*
si tiene hijos (`obrparpar.padide` apuntando a él) y *partida* si es hoja.
`partida_catalog.py:15` lo dice explícitamente: «PARTIDA = HOJA del arbol
(sin hijos). Los capitulos tienen hijos».

**Y el código de hoy no elige.** En
`application/services/partida_resolver.py:54`:

```python
hojas = [n for n in nodos.values() if n.activa]
```

La variable se llama `hojas` pero **no filtra `es_hoja`**: la resolución
automática puede devolver un capítulo. En cambio
`application/pipelines/registro_pipeline.py:296` sí filtra
(`if n.es_hoja and n.activa`) para construir `partidas_postventa`, la lista
que el front enseña en el desplegable. Resultado: **lo automático y lo
manual pueden apuntar a universos distintos**, y nadie lo ha notado porque en
el test offline (`tests/test_pipeline_offline.py:38-44`) los nodos de POSTV2
son hojas.

**Qué se escribiría distinto en Sigrid.** Ejemplo: encargado con MENC,
`pre = 9.000 €/mes`, 10 % de postventa de la obra **0707**, julio 2026.

| | Versión A (partida hoja) | Versión B (capítulo) |
|---|---|---|
| `hmores.paride` | `ide` de la hoja cuyo `cod` = `0707` | `ide` del nodo `0707` que tiene partidas colgando |
| Resto de la línea | `can=0.1`, `pre=9000`, `tot=900`, `fec=20260731` | idéntico |
| Dónde cae el coste en el presupuesto | en la partida `0707` | en el capítulo, fuera de toda partida |
| Informes de Sigrid por partida | ven los 900 € | **no** los ven |
| Desplegable del front (`partidas_postventa`, solo hojas) | ofrece el mismo nodo que el automático | **nunca** ofrece ese nodo: el usuario no puede reproducir ni corregir la elección automática |

Si en POSTV2 cada obra original es un **capítulo con partidas dentro** (p. ej.
`0707` → `0707.MO`, `0707.MAT`), la versión A obliga además a decidir **a
cuál** de esas partidas va la mano de obra; hoy `resolver_postventa` cogería
la primera que empiece por `0707`, que es una elección arbitraria, no una
regla.

**Preguntas cerradas para Administración**

> 1. En el presupuesto de la obra de postventa, la dedicación de un
>    trabajador por postventa de la obra **0707**, ¿a qué línea del
>    presupuesto tiene que ir: al **capítulo** «0707» o a una **partida
>    concreta** colgada de ese capítulo?
> 2. Si es una partida concreta: dime el **código exacto** de esa partida
>    para el ejemplo 0707, tal como aparece en el presupuesto.
> 3. ¿Todas las obras originales tienen la misma estructura dentro de la obra
>    de postventa, o hay obras que son solo una línea suelta?
> 4. Si una obra original **no** tiene su línea en el presupuesto de
>    postventa, ¿qué preferís: que la línea **no se escriba** (y quede
>    listada como omitida), o que se escriba **sin imputar** (`paride = 0`)?

**Consulta de corroboración — C2 (estructura del presupuesto de postventa)**

```jsonc
POST /api/sql/read
{
  "database": "ruesma",
  "sql": "SELECT p.ide AS ide, ISNULL(p.padide,0) AS padide, p.pos AS pos, p.cod AS cod, p.res AS res, ISNULL(p.tipdes,0) AS tipdes, (SELECT COUNT(*) FROM obrparpar h WHERE h.padide = p.ide) AS n_hijos FROM obrparpar p JOIN obr ON obr.ide = p.obride JOIN con ON con.ide = obr.ide WHERE con.cod = ? ORDER BY p.pos, p.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
  "parameters": ["POSTV2", 0, 2000],
  "timeout_seconds": 120,
  "max_rows": 2000
}
```

Lee: el árbol completo del presupuesto de la obra de postventa.
`n_hijos = 0` ⇒ es **partida** (hoja); `n_hijos > 0` ⇒ es **capítulo**.
Basta mirar las filas cuyo `cod` es un código de obra (`0707`, `0678`…) y ver
si tienen hijos. Si el volcado llega con `truncated: true`, subir el `OFFSET`
en pasos de 2.000 y repetir: nunca dar por bueno un resultado truncado.

**Consulta de corroboración — C3 (lo que Administración ya hace a mano)**

```jsonc
POST /api/sql/read
{
  "database": "ruesma",
  "sql": "SELECT TOP 200 h.ide AS ide, h.hmoide AS hmoide, hmo.ano AS ano, hmo.mes AS mes, h.reside AS reside, cres.res AS recurso, h.fec AS fec, a.cod AS hora_cod, h.can AS can, h.pre AS pre, h.tot AS tot, ISNULL(h.paride,0) AS paride, par.cod AS partida_cod, par.res AS partida_res, (SELECT COUNT(*) FROM obrparpar x WHERE x.padide = par.ide) AS partida_n_hijos, CAST(h.tex AS NVARCHAR(200)) AS tex, h.synckey AS synckey FROM hmores h JOIN auxhor a ON a.ide = h.horide JOIN hmo ON hmo.ide = h.hmoide JOIN obr ON obr.ide = hmo.obride JOIN con ON con.ide = obr.ide LEFT JOIN obrparpar par ON par.ide = h.paride LEFT JOIN res ON res.ide = h.reside LEFT JOIN con cres ON cres.ide = res.ide WHERE con.cod = ? AND a.cod LIKE ? ORDER BY h.ide DESC",
  "parameters": ["POSTV2", "M%"],
  "timeout_seconds": 120,
  "max_rows": 500
}
```

Lee: las últimas 200 líneas `M*` que ya existen en los partes de la obra de
postventa, con la partida a la que están imputadas y si esa partida tiene
hijos. **Es la corroboración más fuerte de D1.2**: dice lo que Administración
hace de verdad, no lo que dice el README. Si `partida_n_hijos > 0` en las
líneas reales ⇒ versión B (capítulo). Si es `0` ⇒ versión A (partida).
Si no devuelve nada, la obra de postventa nunca ha tenido dedicación mensual
y la decisión es puramente de Administración, sin dato que la respalde.

---

### D2 — P4: qué cuenta como conflicto en la obra normal

**Versión A — choca aunque la partida sea distinta**
- `services/dedicacion-transfer/README.md:14-15` — «Si el recurso ya tiene un
  registro `M*` en ese parte —aunque sea en otro día— es conflicto» (sin
  mencionar la partida).
- `services/dedicacion-transfer/README.md:31-33` — «en la obra normal una
  línea M* previa del recurso **choca aunque tenga otra partida**».
- `services/dedicacion-transfer/domain/models/registro_models.py:7` — «La
  identidad de la línea en el parte es recurso + mes + código».
- **Es lo que hace el código hoy**, en
  `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:246-253`:
  la comparación de `paride` está condicionada a
  `a.destino != "postventa"`, es decir, en obra normal **no se compara**.

**Versión B — solo choca si además coincide la partida**
- `services/dedicacion-transfer/application/services/reglas_porcentajes.py:11-13`
  — «Si el mismo recurso ya tiene un registro con código M* y **la misma
  partida** en ese parte —aunque sea en OTRO día— es un conflicto».
- `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:16-17`
  — «CONFLICTOS: línea(s) M* del recurso con el mismo código **Y la misma
  partida** en el parte».
- `services/dedicacion-transfer/domain/models/registro_models.py:123-128` —
  `clave_conflicto` incluye `paride` **siempre**, también en obra normal.
- `docs/ARCHITECTURE.md:148-152` señala la contradicción sin resolverla.

**Qué se escribiría distinto en Sigrid.** Ejemplo real y completo:

> Obra **0678**, julio 2026, parte `PT26/00251`. El encargado Acuña (recurso
> `200`, código `MENC`, `pre = 9.000 €/mes`) **ya tiene** en ese parte una
> línea metida a mano por Administración: `fec = 20260715`, `can = 1.0`,
> `tot = 9.000 €`, imputada a la partida `CI.1.99 · MANO DE OBRA INDIRECTA`.
> Nosotros vamos a escribir su 40 % de dedicación: `can = 0.4`,
> `tot = 3.600 €`, `fec = 20260731`, partida `CI.1.10 · ENCARGADO (ACUÑA)`.

| | Versión A (código actual) | Versión B (docstrings) |
|---|---|---|
| ¿Preflight devuelve conflicto? | **Sí** | **No** |
| Si el humano **no** confirma | no se escribe nada de esa línea | se escribe igual (no había nada que confirmar) |
| Si el humano confirma el pisado | `DELETE FROM hmores WHERE ide = 5001` + INSERT de la nueva | (no aplica) |
| El parte queda con | **una** línea `M*` de Acuña: 3.600 € | **dos** líneas `M*` de Acuña: 9.000 € + 3.600 € = **12.600 €** |
| Coste mensual del recurso en la obra | 3.600 € (40 % de 9.000) | 12.600 €, un **40 % de sobrecoste** que nadie ve fallar |
| Riesgo de la elección equivocada | borra un apunte manual legítimo | infla el coste de obra y descuadra el 100 % del trabajador |

Los dos riesgos son reales y de signo opuesto: la versión A **destruye** dato
de Administración; la versión B **duplica** coste. Por eso no se puede
decidir desde el código.

**Hay una tercera incoherencia derivada**, que hay que resolver vaya como
vaya D2: hoy `clave_conflicto` incluye `paride` (versión B) mientras el filtro
de choque no lo compara en obra normal (versión A). Si un recurso tuviera dos
líneas pendientes con distinta partida chocando contra la **misma** línea
existente, se generarían **dos** conflictos distintos y, al confirmar los dos,
**dos `DELETE` del mismo `hmores.ide`** (`res.borradas` contaría 2). Es el
requisito R13/R14.

**Pregunta cerrada para Administración**

> En el parte de trabajo mensual de una obra, ¿puede un mismo trabajador
> tener **más de una línea con código de hora mensual (`M*`)** en el mismo
> mes, cada una imputada a una partida distinta del presupuesto?
> Elige una:
>
> - **(a) NO.** Como mucho una línea `M*` por trabajador, obra y mes. Si ya
>   hay una, lo correcto es **sustituirla**, tenga la partida que tenga.
> - **(b) SÍ, sin límite.** Son líneas legítimas mientras la partida sea
>   distinta, y la suma de sus cantidades puede pasar de 1.
> - **(c) SÍ, pero acotado.** Pueden convivir varias líneas con partidas
>   distintas, pero la **suma** de sus cantidades en ese mes no puede pasar
>   de 1 (el 100 % del trabajador).
>
> Y la complementaria: en el parte de la **obra de postventa**, donde cada
> partida corresponde a una obra original distinta, ¿la respuesta es la
> misma o ahí sí son varias líneas legítimas por trabajador y mes?

Si la respuesta es **(c)**, ninguna de las dos versiones del repositorio
sirve tal cual y hay que volver a proponer diseño: sería una regla nueva
(validar la suma), no una de las dos que hoy están enfrentadas.

**Consulta de corroboración — C4 (¿existe el caso en los datos?)**

```jsonc
POST /api/sql/read
{
  "database": "ruesma",
  "sql": "SELECT TOP 300 h.hmoide AS hmoide, hmo.ano AS ano, hmo.mes AS mes, cobra.cod AS obra_cod, h.reside AS reside, COUNT(*) AS n_lineas, COUNT(DISTINCT ISNULL(h.paride,0)) AS n_partidas, COUNT(DISTINCT h.horide) AS n_codigos, SUM(h.can) AS suma_can, MIN(h.fec) AS fec_min, MAX(h.fec) AS fec_max FROM hmores h JOIN auxhor a ON a.ide = h.horide JOIN hmo ON hmo.ide = h.hmoide JOIN obr ON obr.ide = hmo.obride JOIN con cobra ON cobra.ide = obr.ide WHERE a.cod LIKE ? AND hmo.ano >= ? AND ISNULL(hmo.reside,0) = 0 GROUP BY h.hmoide, hmo.ano, hmo.mes, cobra.cod, h.reside HAVING COUNT(*) > 1 ORDER BY n_partidas DESC, n_lineas DESC",
  "parameters": ["M%", 2025],
  "timeout_seconds": 180,
  "max_rows": 1000
}
```

Lee: los casos reales en los que un mismo recurso tiene **más de una** línea
`M*` en el mismo parte, desde 2025. Es un agregado, así que no necesita
paginación (`sigrid_api.md` §6.4), pero sí `max_rows` explícito.

Cómo se interpreta:

- **0 filas** ⇒ el caso no se da nunca en la práctica. Las dos versiones son
  equivalentes en producción y se puede elegir la más segura (la A, que avisa)
  sin coste. Sigue haciendo falta la respuesta de Administración para
  escribirlo como norma, pero el riesgo baja.
- **Filas con `n_partidas > 1` y `suma_can ≈ 1`** ⇒ respaldo de la versión
  **(c)**: el trabajador se reparte entre partidas dentro de la misma obra.
- **Filas con `n_partidas > 1` y `suma_can > 1`** ⇒ respaldo de la versión
  **(b)**, o duplicados históricos que Administración debería mirar.
- **Filas con `n_codigos > 1`** ⇒ ojo: el recurso tiene varios códigos `M*`
  distintos; eso es otra cosa (`reglas_porcentajes.py:105` ya elige el menor
  alfabéticamente y lo registra en el log). Anotarlo pero no mezclarlo con D2.

**Consulta de corroboración — C5 (detalle de los casos que salgan)**

```jsonc
POST /api/sql/read
{
  "database": "ruesma",
  "sql": "SELECT h.ide AS ide, h.pos AS pos, h.reside AS reside, cres.res AS recurso, h.fec AS fec, a.cod AS hora_cod, h.can AS can, h.pre AS pre, h.tot AS tot, ISNULL(h.paride,0) AS paride, par.cod AS partida_cod, par.res AS partida_res, CAST(h.tex AS NVARCHAR(200)) AS tex, h.synckey AS synckey FROM hmores h JOIN auxhor a ON a.ide = h.horide LEFT JOIN obrparpar par ON par.ide = h.paride LEFT JOIN res ON res.ide = h.reside LEFT JOIN con cres ON cres.ide = res.ide WHERE h.hmoide = ? AND a.cod LIKE ? ORDER BY h.reside, h.pos",
  "parameters": [0, "M%"],
  "timeout_seconds": 60,
  "max_rows": 500
}
```

Sustituir el primer parámetro por un `hmoide` concreto devuelto por C4. Lee:
las líneas `M*` de ese parte una a una, con partida, cantidad, importe y
`synckey`. Sirve para distinguir un reparto legítimo entre partidas de un
duplicado histórico (mismo `can`, misma partida, distinta fecha).

---

## 3. Recordatorios operativos de las consultas

- Todas son **SELECT**, base `ruesma`, con marcadores `?`: nunca concatenar
  valores (`docs/CONVENTIONS.md` § SQL, `sigrid_api.md` §5.2).
- El **corte del balanceador está en 230 s** y no se puede subir
  (`docs/ARCHITECTURE.md` § Acceso a datos). Ninguna consulta de aquí pide
  más de 180 s.
- `max_rows` va **siempre explícito**: el defecto de la pasarela son 200
  filas y truncaría en silencio.
- Si la respuesta trae `truncated: true`, **el resultado está incompleto**:
  hay que paginar con `OFFSET / FETCH` y `ORDER BY`, no dar por bueno lo que
  llegó.
- El volcado íntegro de cada consulta ejecutada se guarda en
  `progress/sigrid_F-002.md` con la fecha y quién la lanzó. Sin ese volcado,
  la decisión no es trazable.

## 4. Trazabilidad requisito → test

| Req | Test | Dónde |
|---|---|---|
| R1, R2, R3, R5 | `test_f002_r1_fuente_unica_*`, `test_f002_r3_frases_prohibidas_*` | `tests/test_f002_fuente_unica.py` |
| R4 | `test_f002_r4_procedencia_fechada` | `tests/test_f002_fuente_unica.py` |
| R6 | `test_f002_r6_sin_mensual_se_omite` | `tests/test_f002_reglas.py` |
| R7 | `test_f002_r7_fecha_ultimo_dia_mes` | `tests/test_f002_reglas.py` |
| R8 | `test_f002_r8_can_pre_tot` | `tests/test_f002_reglas.py` |
| R9 | `test_f002_r9_porcentaje_fuera_de_rango` | `tests/test_f002_reglas.py` |
| R10 | `test_f002_r10_idempotencia_synckey` | `tests/test_f002_pipeline.py` |
| R11 | `test_f002_r11_modo_pruebas_destino_y_partida` | `tests/test_f002_pipeline.py` |
| R12 | `test_f002_r12_postventa_desactivada` | `tests/test_f002_reglas.py` |
| R13 | `test_f002_r13_borrado_unico_por_ide` | `tests/test_f002_pipeline.py` |
| R14 | `test_f002_r14_clave_y_choque_misma_fuente` | `tests/test_f002_conflicto.py` |
| R15–R17 | `test_f002_r15..r17_*` | `tests/test_f002_postventa.py` (**bloqueado**) |
| R18, R19 | `test_f002_r18_*`, `test_f002_r19_*` | `tests/test_f002_conflicto.py` (**bloqueado**) |
| Verificación contra Sigrid real | **MANUAL (humano)** | ver `tasks.md` T12–T13 |

Todos los tests corren **sin red y sin BBDD**, con el cliente falso del
patrón de `services/dedicacion-transfer/tests/test_pipeline_offline.py`.
