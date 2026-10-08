# F-045 · Excel desglosado: pestaña de obras y pestaña de postventa

Pedida por el humano el 2026-10-07: «desglosar excel, la postventa va [en] una pestaña
independiente, y se crea otra [de] obra donde sale una línea agregada de postventa en el
recurso. En la postventa sale la línea agregada de obras xxx en el recurso, de forma que en
ambas pestañas sale detallado en una postventa y en otra obra». Ampliada el 2026-10-08: «añade
una columna de observaciones a la derecha de cada tabla» (D11, R20-R21).

**Lectura:** sobre el Excel de F-040, «Obras» lleva por trabajador sus obras y UNA línea con la
suma de su postventa; «Postventa», sus líneas `Postv-` y UNA línea con la suma de sus obras.
Cada trabajador suma lo mismo en las dos. **Servicio: solo `dedicacion-api`**, que calcula el
agregado (`infrastructure/excel/`); no cambian front, transfer, esquema, ruta, puerto ni `config.yaml`.

## Lo que hay hoy (leído el 2026-10-07 y el 2026-10-08)

- F-040: «Detalle» con todas las líneas, la postventa intercalada (el repositorio ordena por
  `ObraORM.cod, es_postventa`: `0702` y luego `Postv-0702`), y «Resumen». La postventa se
  distingue **solo** por `Linea.es_postventa`; Código y Obra llevan el prefijo
  `export.prefijo_postventa` (F-040 R8). `VAR-NN` es una obra normal (F-039 R21, F-040 D6).
- «RESTO POSTVENTA» **no existe en el sistema** (rótulo del modelo de Juan, F-040 D6), y la app
  **no guarda observaciones** (ni `Linea` ni el esquema tienen ese campo).

## Decisiones (D1-D11 DECIDIDAS por el humano el 2026-10-08; D12 ABIERTA)

Los R marcan con `[Dn]` de cuál dependen. D3-D9 son la A aprobada («todo A»); D1 y D2, lo que
el humano eligió en la MANUAL T6 al ver el libro, que sustituye a su A. Las alternativas
descartadas de D1-D10 están en `git show 628b9bb:specs/F-045-excel-obras-postventa/requirements.md`.

- **D1 · Hojas.** DECIDIDA por el humano el 2026-10-08, en la MANUAL T6: Obras y Postventa «está
  bien», pero «quiero que la hoja resumen sea la primera pestaña original que tenía todas las
  obras, postventa y normales juntas, no la de resumen». El libro queda con **«Obras»,
  «Postventa» y «Detalle»**, en ese orden. «Detalle» es la hoja de F-040: nombre, título
  «DETALLE DE DEDICACIÓN · <Mes> <Año>», todas las líneas juntas, bandas, combinadas y
  autofiltro, **con una sola diferencia desde D11: la columna I «Observaciones»**.
- **D2 · Resumen.** DECIDIDA por el humano el 2026-10-08: **desaparece** («si», tras avisarle
  de que Juan pidió el Resumen en F-040).
- **D3 · Trabajadores:** todos en las dos pestañas, en el mismo orden; quien no tiene nada de
  esa parte sale solo con su agregada, y el que no tiene carga, «SIN CARGA» en las dos (R4).
- **D4 · Agregada vacía:** no la hay; nada de «RESTO POSTVENTA 0%» (R8).
- **D5 · VAR:** `VAR-NN` va en «Obras» como obra normal (F-039) y suma en «RESTO OBRAS» (R5).
- **D6 · Texto de la agregada:** la última del grupo, con Código «POSTVENTA» u «OBRAS» y Obra
  «RESTO POSTVENTA» o «RESTO OBRAS»; con el Código vacío se mezclaba con los «SIN CARGA» (R7).
- **D7 · Formato de la agregada:** banda y bordes de su grupo; Código, Obra y % en cursiva (R15).
- **D8 · Combinadas:** como F-040: A, B, F, G y H, con el valor en todas las filas (R13).
- **D9 · Total, Desviación y Estado:** los del trabajador completo, en las tres hojas (R11, R12).
- **D10 · `LineaDetalle.nombre`:** DECIDIDA por el humano el 2026-10-08: A («si»), se conserva.

**D11 · Observaciones.** DECIDIDA por el humano el 2026-10-08: «añade una columna de
observaciones a la derecha de cada tabla»; avisado de que la app no guarda observaciones,
elige **A** («a»): columna «Observaciones» **vacía**, para escribir en el Excel, una celda por
línea (sin combinar), a la derecha de las tres hojas, ancha, con ajuste de texto y dentro del
autofiltro. Lo escrito vive solo en ese fichero: un export nuevo sale vacío (design §8). R20, R21.

**D12 · Observaciones en la agregada y en «SIN CARGA».** ABIERTA. **A (recomendada):** en todas
las filas de datos, también la agregada y la «SIN CARGA» (sirve para anotar por qué no tiene
carga), con la banda y los bordes de su grupo. B: solo en las líneas reales de obra o
postventa; en las otras, I queda sin formato y corta la banda. R21.

## Libro

R1. [D1, D2] El export debe generar un libro con tres hojas, en este orden: «Obras»,
«Postventa» y «Detalle». No hay hoja «Resumen», tampoco con el periodo vacío.

R2. [D1] Las hojas deben llevar en la fila 1 los títulos «OBRAS · <Mes> <Año>», «POSTVENTA ·
<Mes> <Año>» y «DETALLE DE DEDICACIÓN · <Mes> <Año>», con el formato de F-040 R2: negrita a
13 pt, la cabecera en la fila 2 y los datos desde la 3.

R3. «Obras» y «Postventa» deben tener la cabecera, los anchos, los paneles en `A3`, la
impresión y el autofiltro del Detalle de F-040 R3-R6, con la columna I de R20 (`A2:I<n>`).

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
combinadas como en F-040 R11; la columna I, nunca (R21).

R14. Cada pestaña debe alternar las bandas por trabajador y poner la línea `medium` bajo el
último, como F-040 R12 (la columna I, según R21). La cuenta va por pestaña, con el primer grupo
en blanco, y la agregada lleva la banda de su grupo.

R15. [D7] En la línea agregada, Código, Obra y % deben ir en cursiva. Ninguna otra celda lleva
cursiva, en ninguna hoja (tampoco la I de la agregada), y el resto del formato es el de su grupo.

R16. El % de la agregada debe guardar la fracción con el formato de F-040 R17 (`0%` si es
entero y `0.00%` si no) y ser un valor, nunca una fórmula.

## Detalle, lo que no cambia y documentación

R17. [D1, D11] «Detalle» debe ser la hoja de F-040 (sus R2-R12 y R16-R19) con **una sola
diferencia**, la columna I de R20-R21, por la que deja de ser idéntica a la de F-040: un grupo
por trabajador con todas sus líneas en el orden de la API, la postventa intercalada con el
prefijo y **sin** agregada. Va la tercera, con los mismos trabajadores y orden que las pestañas.

R18. Ruta `export.xlsx`, filtro por empresa, nombre del fichero, puerto `ExcelExporter` y
`config.yaml` no cambian (los tests de F-024, en verde sin tocarlos). El prefijo de postventa
sale de la configuración, no de un literal: un test lo comprueba con «PV_».

R19. La línea de `excel/` en `docs/ARCHITECTURE.md` y la fila de `export.xlsx` en el README de
la api deben describir las tres hojas (Obras, Postventa y Detalle) con la columna Observaciones
vacía y no mencionar el Resumen. `azure-apps/` no cambia: no describe el Excel.

## Columna Observaciones (ampliación del 2026-10-08)

R20. [D11] Las tres hojas deben llevar en la columna I, a la derecha de Estado, la cabecera
«Observaciones» con el formato del resto de la cabecera (F-040 R5) y un ancho de 50. El
autofiltro de las tres debe llegar a I (`A2:I<n>`, `A2:I2` sin trabajadores) y la impresión,
horizontal a una página de ancho, la incluye.

R21. [D11, D12] Cada fila de datos de las tres hojas, también la agregada y la «SIN CARGA»,
debe tener en I una celda **vacía** (sin valor ni fórmula), sin combinar, con ajuste de texto
y alineada arriba, con la banda de su grupo, borde fino y la línea `medium` si es la última
del grupo. Ningún dato de la app se escribe en esa columna.

## Verificación manual (humano)

M1. Excel de un mes generado en local y abierto en Excel: sin aviso de reparación, filtros de
design §6 y visto bueno al aspecto. Cumplida el 2026-10-08 («todo ok», MANUAL T6).

M2. El Excel de 2026/10 con la columna Observaciones: a la derecha en las tres hojas, un texto
largo escrito a mano se ajusta en la celda, el filtro de Observaciones la incluye y la vista
previa de impresión cabe en una página de ancho (design §6).
