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
- «RESTO POSTVENTA» **no existe en el sistema**: es el rótulo del modelo de Juan (F-040 D6).

## Decisiones (D1-D9 DECIDIDAS por el humano el 2026-10-08; D10 abierta)

Los R marcan con `[Dn]` de cuál dependen. D3-D9 son la A aprobada («todo A»); D1 y D2, lo que
el humano eligió en la MANUAL T6 al ver el libro, que sustituye a su A. D10 no cambia ningún R.

**D1 · Hojas.** DECIDIDA por el humano el 2026-10-08, en la MANUAL T6: Obras y Postventa «está
bien», pero «quiero que la hoja resumen sea la primera pestaña original que tenía todas las
obras, postventa y normales juntas, no la de resumen». El libro queda con **«Obras»,
«Postventa» y «Detalle»**, en ese orden. «Detalle» es la hoja de F-040 **sin cambios**: nombre,
título «DETALLE DE DEDICACIÓN · <Mes> <Año>», todas las líneas juntas (obras y postventa
intercalada), bandas, combinadas y autofiltro. Antes era la A («Obras» sustituía a «Detalle»).

**D2 · Resumen.** DECIDIDA por el humano el 2026-10-08: **desaparece** («si», tras avisarle de
que Juan pidió el Resumen en F-040). Antes era la A, «como está». *Tests:* se borran los que
leen la hoja Resumen o prueban `filas_resumen` (design §7).

**D3 · Qué trabajadores salen en cada pestaña.** A: **todos en las dos**, en el mismo orden.
Quien no tiene nada de esa parte sale solo con su línea agregada, y el que no tiene carga sale
«SIN CARGA» en las dos. B: en «Postventa», solo los que tienen alguna línea de postventa. C:
cada pestaña, solo los que tienen alguna línea suya. *Tests:* R4.

**D4 · Línea agregada vacía.** A: si el trabajador no tiene nada de la otra parte, **no**
hay agregada (nada de «RESTO POSTVENTA 0%»). B: siempre hay una, aunque sea al 0 %. *Tests:* R8.

**D5 · VAR.** A: `VAR-NN` va en «Obras» como obra normal (F-039) y suma en «RESTO OBRAS» de
«Postventa». B: en «Postventa», «VAR» como segunda agregada. *Tests:* R5.

**D6 · Texto de la línea agregada.** Siempre va la **última** del grupo. A: Código «POSTVENTA»
u «OBRAS» y Obra «RESTO POSTVENTA» o «RESTO OBRAS», como el modelo de Juan pero con código.
B: el Código vacío, como el modelo; filtrar Código «(Vacías)» mezcla las agregadas con los
«SIN CARGA» (design §5). C: Código vacío y Obra «TOTAL POSTVENTA» o «TOTAL OBRAS». *Tests:* R7.

**D7 · Formato de la línea agregada.** A: con la banda y los bordes de su grupo, y Código,
Obra y % en **cursiva**. B: en negrita. C: relleno gris `F2F2F2`, que corta la banda. *Tests:* R15.

**D8 · Combinadas y autofiltro.** A: **como F-040** en las dos pestañas. A, B, F, G y H van
combinadas con el valor en todas las filas, también en la agregada, y el autofiltro es
`A2:H<n>`. B: sin combinar en las pestañas nuevas. *Tests:* R13.

**D9 · Total, Desviación y Estado.** A: los del **trabajador completo** (obras más postventa),
iguales en las dos pestañas y en «Detalle». La columna % del grupo suma ese Total. B: el total
de la parte de la pestaña, sin Desviación ni Estado, que solo tienen sentido sobre el 100 %.
*Tests:* R11 y R12.

**D10 · `LineaDetalle.nombre` (ABIERTA, técnica).** Sin el Resumen nadie lo lee. **A
(recomendada):** se conserva, sin más tests tocados. B: se borra, y cambian seis tests de
contenido que lo comprueban (design §8).

## Libro

R1. [D1, D2] El export debe generar un libro con tres hojas, en este orden: «Obras»,
«Postventa» y «Detalle». No hay hoja «Resumen», tampoco con el periodo vacío.

R2. [D1] Las hojas deben llevar en la fila 1 los títulos «OBRAS · <Mes> <Año>», «POSTVENTA ·
<Mes> <Año>» y «DETALLE DE DEDICACIÓN · <Mes> <Año>», con el formato de F-040 R2: negrita a
13 pt, la cabecera en la fila 2 y los datos desde la 3.

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
completo (F-040 R16 y R19), los mismos en «Obras», «Postventa» y «Detalle».

R12. [D9] Para cada trabajador con líneas, la suma de la columna % de su grupo debe ser igual
en «Obras» y en «Postventa», e igual a su Total empleado.

R13. [D8] Empleado, Categoría, Total, Desviación y Estado deben ir en todas las filas del grupo,
la agregada incluida (F-040 R10). En los grupos de más de una fila, A, B, F, G y H van
combinadas como en F-040 R11.

R14. Cada pestaña debe alternar las bandas por trabajador y poner la línea `medium` bajo el
último, como F-040 R12. La cuenta va por pestaña, con el primer grupo en blanco, y la agregada
lleva la banda de su grupo.

R15. [D7] En la línea agregada, Código, Obra y % deben ir en cursiva. Ninguna otra fila lleva
cursiva, en ninguna hoja, y el resto del formato es el de su grupo.

R16. El % de la agregada debe guardar la fracción con el formato de F-040 R17 (`0%` si es
entero y `0.00%` si no) y ser un valor, nunca una fórmula.

## Detalle y lo que no cambia

R17. [D1] «Detalle» debe ser la hoja de F-040 sin cambios (sus R2-R12 y R16-R19): un grupo
por trabajador con todas sus líneas en el orden de la API, la postventa intercalada con el
prefijo y **sin** línea agregada, con sus combinadas, bandas, línea gruesa y autofiltro
`A2:H<n>`. Va la tercera, con los mismos trabajadores y en el mismo orden que las pestañas.

R18. Ruta `export.xlsx`, filtro por empresa, nombre del fichero, puerto `ExcelExporter` y
`config.yaml` no cambian (los tests de F-024, en verde sin tocarlos). El prefijo de postventa
sale de la configuración, no de un literal: un test lo comprueba con «PV_».

## Documentación

R19. La línea de `excel/` en `docs/ARCHITECTURE.md` y la fila de `export.xlsx` en el README de
la api deben describir las tres hojas (Obras, Postventa y Detalle) y no mencionar el Resumen.
`azure-apps/` no cambia: no describe el Excel.

## Verificación manual (humano)

M1. Excel real de un mes generado en local y abierto en Excel, sin aviso de reparación. Se
recorren los filtros de design §6 (Empleado, Código de la agregada y Estado) y el humano da el
visto bueno al aspecto.
