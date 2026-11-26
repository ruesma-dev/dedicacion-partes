# F-081 · Operaciones matemáticas en las celdas numéricas del cuadrante

Rigor propuesto **`estandar`** (design, cabecera y D8). Petición del humano del
2026-11-26: «añade feature en primer lugar para que las celdas numericas
permitan operaciones matematicas» (literal). Toca **solo el front**
(`services/dedicacion-front/static/js/app.js`): la api recibe el mismo número
de siempre (design §1). Los requisitos marcados `[Dn]` siguen la opción
**recomendada** de la tabla de decisiones (design §12); si el humano elige otra,
el líder reescribe el requisito antes de aprobar la spec.

## 0. Glosario

- **Celda de %**: el `input.pct-input` de cada línea del editor
  (`chipEditable`). Hoy: `parsearPct` en cada tecla, total en vivo, guardado
  diferido (700 ms), Enter al buscador de obra, en blanco al salir rellena lo
  que falta hasta 100 (F-030 R1) y con letras busca incidencia (F-030 R8-R13).
- **Casilla de cantidad**: el `input.importe-cantidad` de cada vinculado de
  cantidad (`chipImporte`, F-069 R11/R12; km o €). Hoy: `cantidadTecleada` en
  cada tecla, marca de «copiado», guardado diferido; lo que no es número va tal
  cual y la api lo rechaza (422, aviso de siempre).
- **Expresión**: lo tecleado que `esExpresion` reconoce (R6). **Número llano**:
  todo lo demás; sigue el camino de hoy sin cambios (R16).
- **Confirmar**: salir de la celda (`blur`, también el que provoca Enter o
  Tab) o, en la casilla de cantidad, pulsar Enter.

## 1. El evaluador (función pura, sin DOM)

- **R1.** `[D2]` `evaluarExpresion(texto)` debe devolver `{ok: true, valor}`
  para una expresión con números, `+ - * /`, paréntesis, signo `+`/`-` delante
  de un número o paréntesis, coma o punto decimal y espacios en cualquier
  sitio, con un `=` opcional al principio; con la precedencia habitual (`*` y
  `/` antes que `+` y `-`) y asociatividad por la izquierda: `30+10` ⇒ 40,
  `=100/3` ⇒ 33,333…, `10+2*3` ⇒ 16, `(10+2)*3` ⇒ 36, `20-5-5` ⇒ 10,
  `100/2/5` ⇒ 10, `-5+10` ⇒ 5, `5*-2` ⇒ -10, `12,5 + 0.5` ⇒ 13. (capa: unit)
- **R2.** SI el texto no es una expresión bien formada (carácter no admitido,
  número con dos separadores decimales como `1.234,5`, paréntesis sin cerrar
  o sin abrir, `()`, dos operadores binarios seguidos como `3*/2`, operador al
  final, vacío o solo `=`), ENTONCES `evaluarExpresion` debe devolver
  `{ok: false, motivo: "no válida"}` sin lanzar. (capa: unit)
- **R3.** SI la expresión divide por cero o su resultado no es finito,
  ENTONCES debe devolver `{ok: false, motivo: "división por cero"}` o
  `{ok: false, motivo: "no válida"}` respectivamente. (capa: unit)
- **R4.** SI el texto pasa de 100 caracteres o anida más de 20 paréntesis,
  ENTONCES debe devolver `{ok: false, motivo: "demasiado larga"}` sin recorrer
  la expresión entera. (capa: unit)
- **R5.** `[D6]` `app.js` no debe evaluar texto como código: ni `eval(`, ni
  `new Function`, ni `Function(`, ni `setTimeout`/`setInterval` con una cadena.
  (capa: unit, comprobación estática sobre el fichero)
- **R6.** `[D2]` `esExpresion(texto)` debe ser `true` si, quitados los
  espacios, el texto empieza por `=` o contiene `+`, `*`, `/`, `(`, `)` o un
  `-` que no sea su primer carácter; y `false` en otro caso: `40`, `40,5`,
  `-5`, `50%`, vacío ⇒ `false`; `30+10`, `=40`, `5-2`, `(40)` ⇒ `true`.
  (capa: unit)
- **R15.** `[D5]` `redondear2(n)` debe redondear a dos decimales, mitad hacia
  arriba sobre la escritura decimal y no sobre el binario: `0,1+0,2` ⇒ 0,3;
  `100/3` ⇒ 33,33; `200/3` ⇒ 66,67; `1,005*1` ⇒ 1,01; `-2,5/1` ⇒ -2,5.
  (capa: unit)

## 2. La celda de %

- **R7.** MIENTRAS la celda de % contenga una expresión (y ninguna letra), el
  sistema no debe cambiar `linea.porcentaje`, ni el total en vivo, ni
  programar el guardado. (capa: unit)
- **R8.** `[D3]` CUANDO se confirme la celda de % con una expresión válida cuyo
  resultado redondeado (R15) esté en (0, 100], el sistema debe poner en la
  celda ese resultado con coma decimal (`100/3` ⇒ `33,33`), dejarlo en
  `linea.porcentaje`, refrescar el total en vivo y programar el guardado una
  vez; la operación no se guarda en ningún sitio. (capa: unit)
- **R9.** `[D4]` SI el resultado redondeado de la celda de % es ≤ 0 o > 100,
  ENTONCES el sistema no debe aplicarlo: aviso de error (`toast(…, true)`)
  «La operación da X: el % tiene que estar entre 0 y 100», celda repuesta al %
  que tenía la línea y sin guardado. (capa: unit)
- **R10.** `[D4]` SI la expresión de la celda de % no es válida (R2-R4),
  ENTONCES el sistema debe avisar con `toast(…, true)` «Operación no válida:
  «texto» (motivo)», reponer la celda al % de la línea y no guardar. (capa:
  unit)
- **R11.** CUANDO se pulse Enter en la celda de % con una expresión, el sistema
  debe confirmarla (R8-R10) y después ir al buscador de obra, como hoy.
  (capa: unit)
- **R17.** MIENTRAS la celda de % tenga alguna letra, el sistema debe seguir
  buscando incidencia como hoy (F-030 R8-R13), lleve o no operadores. (capa:
  unit)

## 3. La casilla de cantidad (km y €)

- **R12.** MIENTRAS la casilla de cantidad contenga una expresión, el sistema
  no debe cambiar `casilla.cantidad`, ni la marca de copiado, ni programar el
  guardado. (capa: unit)
- **R13.** `[D3, D4]` CUANDO se confirme la casilla de cantidad con una
  expresión válida, el sistema debe poner en ella el resultado redondeado (R15)
  con coma decimal y seguir exactamente como si se hubiera tecleado ese número
  (`casilla.cantidad`, marca de copiado según F-069 D18, guardado diferido).
  Un resultado negativo o por encima del tope de su unidad lo rechaza la api
  como hoy (422 y el aviso de siempre): el front no repite sus topes. (capa:
  unit)
- **R14.** SI la expresión de la casilla de cantidad no es válida (R2-R4),
  ENTONCES el sistema debe avisar como R10, reponer la casilla a
  `casilla.cantidad` (lo último válido) y no guardar. (capa: unit)

## 4. Lo que no cambia

- **R16.** Con un número llano, la celda de % y la casilla de cantidad deben
  hacer exactamente lo de hoy: los tests de F-030 R1 y de F-069 R11/R12 pasan
  **sin cambiar ninguna aserción** (solo se añaden a sus listas cerradas los
  nombres de las funciones nuevas, design §4). (capa: unit)
- **R18.** `[D1]` Los días «del»/«al» de una incidencia no deben admitir
  operaciones: `parsearDia` y su casilla, como hoy (`1+2` ⇒ `null`). (capa:
  unit)
- **R19.** `[D9]` CUANDO se teclee `/`, `*`, `+`, `-` o `=` en una celda del editor
  abierto, el atajo global (`teclas`) no debe actuar: `/` no va al buscador ni
  se cancela la tecla; y pegar una expresión sigue el mismo camino que
  teclearla (R7, R12). (capa: unit)
- **R20.** El `PUT` de asignaciones y el de importes deben llevar siempre un
  número (`porcentaje`, `cantidad`) o `null`, nunca el texto de una
  expresión. (capa: unit)

## 5. Descubrirlo

- **R21.** `[D7]` La celda de % y la casilla de cantidad deben llevar un
  `title` que diga que admiten operaciones, con un ejemplo («Admite
  operaciones: 30+10, 100/3, (8+4)*2»). (capa: unit)
- **R22.** `docs/ARCHITECTURE.md` (sección `dedicacion-front`) debe decir qué
  celdas admiten operaciones, que el evaluador es propio y que a la api solo
  llega el resultado. (capa: unit, test sobre el documento)
