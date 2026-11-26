# F-081 · Diseño: operaciones matemáticas en las celdas numéricas

**Rigor: `estandar`** (propuesto por el líder; confirmado aquí, D8). No cumple
ningún disparador de `critico` (`CHECKPOINTS.md`, «Niveles de rigor»):

1. **Dinero** — no calcula, mueve ni registra importes: el precio, el reparto
   por % y el `tot` siguen en el transfer (`reglas_vinculados`). El evaluador
   traduce lo tecleado al número que el usuario habría tecleado a mano, igual
   que hoy `parsearPct` traduce `33,5`; el resultado se ve en la celda antes de
   registrar y la api lo valida como siempre (R13). Es el punto más discutible
   (las casillas de € y km acaban en el parte): por eso D8.
2. **Escritura en producción o compartido** — no: el front no escribe en
   Sigrid; el `PUT` a la api es el de siempre.
3. **Seguridad** — no hay credenciales ni datos personales; el evaluador no
   ejecuta código (R5), solo lee lo que teclea el propio usuario.
4. **Contrato público** — no cambia ningún endpoint, esquema ni formato.

## 1. Servicio y límite

| Servicio | Qué cambia | Por qué ahí |
|---|---|---|
| front | `app.js` (evaluador y dos celdas), `title`, tests, doc | es interpretar lo tecleado |
| api | **nada** | recibe el número de siempre |
| transfer | **nada** | — |

Por qué cabe en el front sin ser lógica de negocio (`docs/CONVENTIONS.md`,
«El front no calcula reglas de negocio»): la operación es una forma de
**teclear** un número, no una regla que decida qué se registra. Lo que se
registra lo sigue validando la api, leído en el código el 2026-11-26:

- `LineaIn.porcentaje`: `Decimal`, `gt=0, le=100, max_digits=6,
  decimal_places=2` (`interface_adapters/api/schemas.py`, l. 36).
- `ImporteIn.cantidad`: `Any`, validada por `domain/importes.validar_cantidad`
  (no número, no finito, negativo, más de dos decimales o por encima de
  `TOPES[unidad]` ⇒ `ImporteInvalido`, 422).

Por eso el front **no** repite los topes de cantidad (R13). Sí decide el rango
del %, porque hoy ya lo hace en silencio (`parsearPct` recorta a 100 y lleva
≤ 0 a 0, que borra la línea al guardar, `cuerpoLineas`): para una operación
eso escondería un error de cuenta (R9, D4).

## 2. Lo que hay hoy (leído el 2026-11-26)

| Celda | Dónde | Parseo | Cuándo se guarda |
|---|---|---|---|
| % de la línea | `chipEditable`, l. ~2072 | `parsearPct` en `input` (parseFloat; `30+10` ⇒ 30 en silencio) | diferido 700 ms en cada tecla |
| cantidad km / € | `chipImporte`, l. ~1919 | `cantidadTecleada` en `input` (`30+10` va como texto ⇒ 422) | diferido en cada tecla |
| días «del»/«al» | `chipIncidencia`, l. ~2259 | `parsearDia` (1-2 cifras; `maxLength = 2`) | diferido |

No hay otras celdas numéricas tecleables: los demás `input` son filtros de
columna, buscadores, comentarios y casillas de marcar. No hay escucha de
`paste` en ninguna celda (pegar dispara `input`, el mismo camino). El atajo
global `teclas` (l. ~3651) vuelve antes de mirar `/` mientras el editor está
abierto; F7/F8 actúan siempre y repintan el editor.

## 3. Ficheros a crear

- `services/dedicacion-front/tests/test_f081_operaciones.py` — tests de R1-R22
  con el arnés node de siempre (`_funcion`, `_node` de `test_f042_sugerencias`,
  `DOM_CELDA` de `test_f030_celda_pct`, `_editor` de
  `test_f030_tabla_incidencias`). Sin red ni BBDD; sin `node`, se saltan con su
  motivo y el reviewer los exige `passed`.

## 4. Ficheros a modificar

- `services/dedicacion-front/static/js/app.js`:
  - funciones nuevas de primer nivel (para que `_funcion` las cargue), junto a
    `parsearPct`: `esExpresion`, `evaluarExpresion`, `redondear2`,
    `textoNumero`, `confirmarExpresion` (§5);
  - `chipEditable`: rama de expresión en la escucha `input` (R7), una escucha
    `blur` que confirma (R8-R10) y el `title` (R21); el Enter de hoy ya hace
    `pct.blur()`, así que R11 sale solo;
  - `chipImporte`: la lógica de hoy de la escucha `input` pasa a una función
    local `aplicarCantidad()` (mismo cuerpo); rama de expresión (R12); `blur`
    y Enter confirman (R13, R14); `title` (R21).
- Tests existentes que cargan `chipEditable` o `chipImporte` con una **lista
  cerrada** de funciones: se añaden a esa lista los nombres nuevos y **nada
  más** (ninguna aserción cambia, R16): `test_f030_celda_pct.py`
  (`FUNCIONES_HOY`), `test_f069_importes_front.py`, y los que el implementer
  encuentre con `grep -l "chipEditable\|chipImporte" services/dedicacion-front/tests`
  (hoy además: `test_f025_catalogo_postventa.py`, `test_f029_seleccion.py`,
  `test_f030_tabla_incidencias.py`, `test_f041_filtro_obra.py`,
  `test_f042_sugerencias.py`, `test_f061_busqueda.py`). Si alguno necesita
  cambiar una aserción, **PARA** y `blocked`.
- `services/dedicacion-front/static/css/styles.css`: la clase `expresion`
  (§5, «Estilo»).
- `docs/ARCHITECTURE.md`, sección «`dedicacion-front` — captura, nada más»:
  un párrafo (R22).

## 5. Funciones (front, `app.js`)

- `esExpresion(texto) -> bool` — R6. Solo decide el camino; no valida.
- `evaluarExpresion(texto) -> {ok: true, valor} | {ok: false, motivo}` — R1-R4.
  Descenso recursivo sobre una lista de fichas, sin `eval` (D6):
  ```
  expr   := term (("+" | "-") term)*
  term   := factor (("*" | "/") factor)*
  factor := ("+" | "-") factor | numero | "(" expr ")"
  numero := cifras [("," | ".") cifras] | ("," | ".") cifras
  ```
  Antes de nada: `trim`, quitar un `=` inicial y los espacios; más de 100
  caracteres ⇒ «demasiado larga». Profundidad de `(` > 20 ⇒ «demasiado larga».
  Fichas que sobran al final o carácter desconocido ⇒ «no válida». Divisor 0 ⇒
  «división por cero». Resultado no finito ⇒ «no válida». Nunca lanza: los
  errores internos se recogen y salen como `{ok: false}`.
- `redondear2(n) -> number` — R15: mitad hacia arriba en decimal, desplazando
  el exponente en la cadena (`Number(Math.round(Number(abs + "e2")) + "e-2")`
  con el signo aparte), no `Math.round(n * 100) / 100` (daría 1,005 ⇒ 1).
  Para |n| < 1e-6 da 0. No sustituye al redondeo de `parsearPct`, que no cambia.
- `textoNumero(n) -> string` — `String(n).replace(".", ",")`, como el resto de
  la celda (`33.33` ⇒ `33,33`).
- `confirmarExpresion(texto, rango) -> {ok: true, valor} | {ok: false,
  mensaje}` — evalúa, redondea y, si `rango` es `"pct"`, exige (0, 100]
  (R9); con `"cantidad"` no mira el rango (R13). Arma el texto del aviso
  (R9, R10). Pura: los `chip*` la llaman y hacen el DOM.

### La celda de % (`chipEditable`)

- `input`: la comprobación de letras de hoy va **primero** (R17); después, si
  `esExpresion(pct.value)`, la celda se marca con la clase `expresion` y se
  sale sin tocar `linea.porcentaje`, `previo`, el total ni el guardado (R7).
  Si no, quita la clase y sigue lo de hoy (R16).
- `blur` (nueva, registrada **antes** que la de «en blanco rellena»): si la
  celda tiene expresión y no tiene letras, `confirmarExpresion(…, "pct")`;
  válida ⇒ `pct.value = textoNumero(valor)`, `previo = pct.value`,
  `linea.porcentaje = valor`, `refrescarTotalVivo`, `programarGuardado` (R8);
  no válida ⇒ `toast(mensaje, true)` y `pct.value` = el % de la línea con
  coma (vacío si 0), sin guardar (R9, R10). La escucha de «en blanco» de hoy
  ve entonces un número o un vacío, como siempre.
- La escucha `blur` de F-030 que corta con `stopImmediatePropagation` cuando se
  eligió una incidencia sigue la primera: con letras no hay expresión.

### La casilla de cantidad (`chipImporte`)

- `input`: si `esExpresion`, clase `expresion` y nada más (R12); si no,
  `aplicarCantidad()` (lo de hoy, R16).
- `blur` y `keydown` Enter (Enter con `preventDefault`, el foco no se mueve):
  si hay expresión, `confirmarExpresion(…, "cantidad")`; válida ⇒
  `cantidad.value = textoNumero(valor)` y `aplicarCantidad()` (R13); no
  válida ⇒ `toast` y `cantidad.value = casilla.cantidad` (R14).

### Estilo

- `styles.css`: `.pct-input.expresion, .importe-cantidad.expresion` con letra
  en cursiva para que se vea que aún no cuenta. Sin colores nuevos: los de
  `:root`.

## 6. Datos

Nada nuevo: ni columnas, ni esquema, ni `config.yaml`. La operación no se
guarda (D3); al recargar el mes la celda enseña el número.

## 7. Ficheros que NO se tocan

- `services/dedicacion-api/**` y `services/dedicacion-transfer/**`.
- `parsearPct`, `cantidadTecleada`, `parsearDia`, `cuerpoLineas`,
  `cuerpoImportes`, `elementoImporte`: el camino del número llano es el de hoy.
- `chipIncidencia` (días, D1), `teclas` (R19 se cumple ya; solo test de
  regresión), los filtros de columna y el buscador.
- `inputMode = "decimal"` de las dos celdas (ver §9).

## 8. Verificación MANUAL (humano)

M1, en local o tras desplegar el front (Ctrl+F5), en un mes abierto, sin
registrar: en la celda de % de una línea teclear `100/3` y Tab ⇒ `33,33` y el
total en vivo lo suma; `=50+60` y Tab ⇒ aviso de rango y la celda vuelve a
`33,33`; `30+` y Enter ⇒ aviso «no válida» y foco en el buscador de obra; en
una casilla de km `120*2` y Enter ⇒ `240` y el «●» de guardando; recargar el
mes ⇒ `33,33` y `240` siguen. Resultado en `progress/manual_F-081.md`.

## 9. Riesgos y alternativas descartadas

- **Rango del %** recortado en silencio como hoy (D4 b): descartado como
  recomendado; esconde un error de cuenta y ≤ 0 borra la línea al guardar.
- **Evaluar en cada tecla** (D3 b): guardaría resultados intermedios
  (`100` de `100/3`) y cambiaría el total mientras se escribe; el diferido de
  700 ms puede mandar uno de ellos.
- **Guardar la operación** (D3 c): columna nueva en la api y contrato nuevo;
  otra feature.
- **Librería** (math.js) o `eval`/`Function` (D6): sin dependencias de front
  por convención; `eval` ejecutaría lo que se pegue en la celda.
- **`x` o `×` como multiplicar**: `x` es letra y abre la búsqueda de
  incidencia (F-030); se admite solo `*` (D2).
- **Móvil**: el teclado `decimal` no trae `+ * /`; cambiar `inputMode` quitaría
  el teclado numérico a todos. Fuera de alcance.
- **F7/F8 con una expresión a medias**: repintan el editor y la expresión sin
  confirmar se pierde (no contaba). Se acepta.
- **Copias de `partes`**: ninguna de las cinco de la lista cerrada se toca.

## 10. Frontera

¿Cruza la frontera del proyecto? **No.** No cambia ningún endpoint, tabla,
variable de entorno ni recurso compartido; `azure-apps/dedicacion.md` no se
toca. Despliegue: solo el front.

## 11. Encaje en la arquitectura

El front sigue siendo «captura, nada más» (`docs/ARCHITECTURE.md`): una forma
más de teclear un número. Todo en `app.js`, JS vanilla, sin bundler
(`docs/CONVENTIONS.md`).

## 12. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 · Qué celdas | (a) el % de cada línea y las casillas de cantidad (km y €); (b) solo el %; (c) también los días de incidencia (exige quitar `maxLength = 2`) | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D2 · Sintaxis | (a) `=` opcional delante; `+ - * /`, paréntesis, signo delante, coma o punto decimal, espacios libres; sin separador de miles ni `x`/`×`/`%`; (b) igual pero con `=` obligatorio (como Excel; sin `=` todo es número llano); (c) solo `+` y `-` | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D3 · Cuándo y qué se ve | (a) se evalúa al confirmar (salir, Enter, Tab); la celda se queda con el resultado; la operación no se guarda; mientras se escribe, en cursiva y sin contar; (b) se evalúa en cada tecla y guarda lo intermedio válido; (c) como (a) y además se guarda la operación (cambio en la api) | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D4 · Errores y rango | (a) no válida o división por cero ⇒ aviso de error y la celda vuelve a lo último válido; en el %, fuera de (0, 100] ⇒ igual; en cantidad, el resultado va como si se tecleara y la api valida (negativo, tope); (b) en el %, recortar como hoy (>100 ⇒ 100, ≤ 0 ⇒ 0); (c) dejar el texto en rojo sin reponer hasta corregirlo | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D5 · Redondeo | (a) dos decimales, mitad hacia arriba, en las dos celdas (los que admite la api en ambas); (b) error si el resultado tiene más de dos decimales | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D6 · Evaluador | (a) propio, descenso recursivo, sin `eval`/`Function`, con tope de 100 caracteres y 20 paréntesis; (b) una librería (math.js), nueva dependencia de front | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D7 · Descubrirlo | (a) `title` en las dos celdas con un ejemplo; (b) nada visible | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D8 · Rigor | (a) `estandar` (cabecera: no calcula dinero, traduce lo tecleado, la api valida); (b) `critico` por el disparador 1, porque las cantidades de € y km acaban en el parte (mutación exigida y cero supervivientes) | (a) || (a), OK del humano el 2026-11-26 («ok») |
| D9 · Atajos y pegado | (a) nada especial: pegar dispara `input` (mismo camino que teclear); con el editor abierto `/` ya no salta al buscador; F7/F8 repintan y descartan una expresión sin confirmar; (b) como (a), pero F7/F8 confirman antes la expresión pendiente | (a) || (a), OK del humano el 2026-11-26 («ok») |
