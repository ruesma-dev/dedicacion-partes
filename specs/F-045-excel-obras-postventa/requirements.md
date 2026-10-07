# F-045 · Excel desglosado: pestaña de obras y pestaña de postventa

Pedida por el humano el 2026-10-07: «desglosar excel, la postventa va [en] una pestaña
independiente, y se crea otra [de] obra donde sale una línea agregada de postventa en el
recurso. En la postventa sale la línea agregada de obras xxx en el recurso, de forma que en
ambas pestañas sale detallado en una postventa y en otra obra».

**Lectura (a confirmar con D1-D9):** sobre el Excel de F-040, dos pestañas agrupadas por
trabajador. «Obras» lleva el detalle de sus obras y UNA línea con la suma de toda su postventa.
«Postventa» lleva el detalle de sus líneas `Postv-` y UNA línea con la suma de todas sus obras.
Cada trabajador suma lo mismo en las dos. **Servicio: solo `dedicacion-api`**
(`infrastructure/excel/`). El agregado lo calcula la api; no cambian front, transfer, esquema,
ruta, puerto ni `config.yaml`.

## Lo que hay hoy (leído el 2026-10-07)

- F-040: «Detalle» con todas las líneas y la postventa intercalada (el repositorio ordena por
  `ObraORM.cod, es_postventa`: `0702` y luego `Postv-0702`), y «Resumen».
- La postventa se distingue **solo** por `Linea.es_postventa`. Código y Obra llevan el prefijo
  `export.prefijo_postventa` (F-040 R8). `VAR-NN` es una obra normal en el Excel (F-039 R21,
  F-040 D6), y una entrada VAR no admite postventa.
- «RESTO POSTVENTA» **no existe en el sistema**. Es el rótulo del modelo de Juan que F-040 D6
  descartó para el detalle. Aquí vuelve como línea agregada de la pestaña Obras (D6).

## Decisiones abiertas (las decide el humano; recomendada = A)

Los R están escritos con todas en A y marcan con `[Dn]` de cuál dependen; otra opción obliga
a reescribir esos R antes de implementar.

**D1 · Hojas.** A: «Obras» **sustituye** a «Detalle». El libro queda con «Obras», «Postventa»
y «Resumen», titulados «OBRAS · <Mes> <Año>» y «POSTVENTA · <Mes> <Año>». B: se **añaden**,
y el libro queda con «Detalle», «Obras», «Postventa» y «Resumen»; repite cada línea dos veces.
*Tests:* A adapta 11 tests de F-040 y uno de F-039 (design §7); B, solo r1, r4, r11 y r13.

**D2 · Resumen.** A: **como está** (F-040 R13-R15), una fila por trabajador con todas sus
líneas, `Postv-` incluidas. B: partir «Obras» en dos columnas, «Obras» y «Postventa». C:
quitarlo. *Tests:* A, ninguno; B cambia r3, r4, r13, r14, r14_r15 y test_f039_r21; C, todos los que
leen la hoja Resumen.

**D3 · Qué trabajadores salen en cada pestaña.** A: **todos en las dos**, en el mismo orden.
Quien no tiene nada de esa parte sale solo con su línea agregada, y el que no tiene carga sale
«SIN CARGA» en las dos. B: en «Postventa», solo los que tienen alguna línea de postventa. C:
cada pestaña, solo los que tienen alguna línea suya. *Tests:* con A, un test exige el mismo
conjunto y orden en las dos; con B o C se prueban las ausencias, y la suma igual solo vale para
los que salen en ambas.

**D4 · Línea agregada vacía.** A: si el trabajador no tiene nada de la otra parte, **no**
hay agregada (nada de «RESTO POSTVENTA 0%»). B: siempre hay una, aunque sea al 0 %. *Tests:*
R8, en un sentido o en el otro.

**D5 · VAR.** A: `VAR-NN` va en «Obras» como obra normal (F-039) y suma en la agregada
«RESTO OBRAS» de «Postventa». B: en «Postventa», «VAR» como segunda agregada, aparte de «RESTO
OBRAS». *Tests:* con A, un test pone `VAR-29` en Obras y sumado en RESTO OBRAS; con B, dos agregadas.

**D6 · Texto de la línea agregada.** Siempre va la **última** del grupo. A: Código «POSTVENTA»
u «OBRAS» y Obra «RESTO POSTVENTA» o «RESTO OBRAS», como el modelo de Juan pero con código.
B: el Código vacío, como el modelo. Con B, filtrar Código «(Vacías)» mezcla las agregadas con
los «SIN CARGA», como se vio en el prototipo (design §5). C: Código vacío y Obra «TOTAL
POSTVENTA» o «TOTAL OBRAS». *Tests:* los literales de R7.

**D7 · Formato de la línea agregada.** A: con la banda y los bordes de su grupo, y Código,
Obra y % en **cursiva**. B: en negrita. C: con relleno gris `F2F2F2` propio, que corta la banda
del trabajador. *Tests:* R15.

**D8 · Combinadas y autofiltro.** A: **como F-040** en las dos pestañas. A, B, F, G y H van
combinadas con el valor en todas las filas, también en la agregada, y el autofiltro es
`A2:H<n>`. B: sin combinar en las pestañas nuevas. *Tests:* A reutiliza las comprobaciones de
F-040 R10-R11 sobre las dos hojas.

**D9 · Total, Desviación y Estado.** A: los del **trabajador completo** (obras más postventa),
iguales en las dos pestañas y en el Resumen. La columna % del grupo suma ese Total. B: el total
de la parte de la pestaña, sin Desviación ni Estado, que solo tienen sentido sobre el 100 %.
*Tests:* R11 y R12.

## Libro

R1. [D1] El export debe generar un libro con tres hojas, en este orden: «Obras», «Postventa» y
«Resumen». No hay hoja «Detalle».

R2. [D1] Las hojas deben llevar en la fila 1 los títulos «OBRAS · <Mes> <Año>», «POSTVENTA ·
<Mes> <Año>» y «RESUMEN · <Mes> <Año>», con el formato de F-040 R2: negrita a 13 pt, la
cabecera en la fila 2 y los datos desde la 3.

R3. «Obras» y «Postventa» deben tener la cabecera del Detalle de F-040 R6, sus anchos, el
autofiltro `A2:H<n>`, los paneles en `A3` y la impresión de F-040 R3-R5. Sin trabajadores, el
autofiltro cubre solo la cabecera.

## Pestañas Obras y Postventa

R4. [D3] Cada pestaña debe tener un grupo por trabajador del cuadrante, en el orden en que los
entrega la API (F-040 R7), y los mismos trabajadores en el mismo orden en las dos.

R5. [D5] En «Obras», el grupo debe llevar las líneas con `es_postventa` falso, en su orden, con
el Código y la Obra de F-040 R8. `VAR-NN` sale aquí, como cualquier obra.

R6. En «Postventa», el grupo debe llevar las líneas con `es_postventa` verdadero, en su orden y
con el prefijo de `export.prefijo_postventa` en Código y Obra (F-040 R8).

R7. [D6] CUANDO el trabajador tiene alguna línea de la otra parte, su grupo debe acabar con
UNA línea agregada. En «Obras» lleva Código «POSTVENTA» y Obra «RESTO POSTVENTA»; en
«Postventa», Código «OBRAS» y Obra «RESTO OBRAS». Su % es la suma exacta (`Decimal`) de los %
de todas las líneas de la otra parte.

R8. [D4] SI el trabajador no tiene ninguna línea de la otra parte, ENTONCES su grupo no lleva
línea agregada.

R9. SI el trabajador solo tiene líneas de la otra parte, ENTONCES su grupo en esa pestaña debe
ser una sola fila: la agregada.

R10. Un trabajador sin líneas debe tener en cada pestaña una sola fila «SIN CARGA» (F-040 R9).

R11. [D9] En las dos pestañas, Total empleado, Desviación y Estado deben ser los del trabajador
completo (F-040 R16 y R19), los mismos en «Obras», «Postventa» y «Resumen».

R12. [D9] Para cada trabajador con líneas, la suma de la columna % de su grupo debe ser igual
en «Obras» y en «Postventa», e igual a su Total empleado.

R13. [D8] Empleado, Categoría, Total, Desviación y Estado deben ir en todas las filas del grupo,
la agregada incluida (F-040 R10). En los grupos de más de una fila, A, B, F, G y H van
combinadas como en F-040 R11.

R14. Cada pestaña debe alternar las bandas por trabajador y poner la línea `medium` bajo el
último, como F-040 R12. La cuenta va por pestaña, con el primer grupo en blanco, y la agregada
lleva la banda de su grupo.

R15. [D7] En la línea agregada, Código, Obra y % deben ir en cursiva. Ninguna otra fila lleva
cursiva, y el resto del formato es el de su grupo.

R16. El % de la agregada debe guardar la fracción con el formato de F-040 R17 (`0%` si es
entero y `0.00%` si no) y ser un valor, nunca una fórmula.

## Resumen y lo que no cambia

R17. [D2] El «Resumen» debe seguir como en F-040 R13-R15, con las mismas filas, la columna
«Obras» con las líneas `Postv-` y el mismo Total y Estado.

R18. Ruta `export.xlsx`, filtro por empresa, nombre del fichero, puerto `ExcelExporter` y
`config.yaml` no cambian (los tests de F-024, en verde sin tocarlos). El prefijo de postventa
sale de la configuración, no de un literal: un test lo comprueba con «PV_».

## Documentación

R19. La línea de `excel/` en `docs/ARCHITECTURE.md` y la fila de `export.xlsx` en el README de
la api deben describir las tres hojas. `azure-apps/` no cambia: no describe el Excel.

## Verificación manual (humano)

M1. Excel real de un mes generado en local y abierto en Excel, sin aviso de reparación. Se
recorren los filtros de design §6 (Empleado, Código de la agregada y Estado) y el humano da el
visto bueno al aspecto.
