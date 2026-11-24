<!-- specs/F-076-excel-sin-resto-de/requirements.md -->
# F-076 · Excel: «Obras» solo con obras y «Postventa» solo con postventa

Rigor **`estandar`**. **Solo `dedicacion-api`** (`infrastructure/excel/`); no
cambian front, transfer, esquema, ruta, puerto ni `config.yaml` (design §1).

Negocio, transmitido por el humano el 2026-11-22 (punto 4): «en el excel
quitar los recursos que tengan solo resto de, y las líneas resto de».
Aclarado el mismo día: «en el excel en la pestaña de postventa las obras
normales salen como resto, y viceversa. Con este nuevo enfoque, en postventa
sale solo postventa, y en obra solo obra».

**Sustituye** de F-045 (`specs/F-045-excel-obras-postventa/`): D3 (todos los
trabajadores en las dos pestañas), D4, D6 y D7 (la línea agregada «RESTO …»)
y sus R4, R7, R8, R9, R12, R15 y R16. **Siguen**: R1-R3, R5, R6, R10 (según
D2), R11 (según D1), R13, R14, R17-R21. La hoja «Detalle» no cambia.
Decisiones `[Dn]`: design §9.

## Lo que hay hoy (leído el 2026-11-24)

- `contenido.grupos_pestana` añade al final de cada grupo una
  `LineaDetalle(agregada=True)` con la suma de la otra parte; si el
  trabajador solo tiene la otra parte, su grupo es esa línea sola.
  `exporter._hoja_grupos` la pinta con Código, Obra y % en cursiva.
- Total, Desviación y Estado de las pestañas son los del trabajador
  completo (F-045 D9), así que hoy la columna % de cada grupo suma su Total.
- La parte se decide **solo** por `Linea.es_postventa`; `VAR-NN` es obra
  normal (F-039 R21, F-045 D5).

## Libro

R1. El export debe seguir generando «Obras», «Postventa» y «Detalle», en
ese orden, con los títulos, la cabecera de nueve columnas (Observaciones
incluida), los anchos, los paneles en `A3`, la impresión y el autofiltro
`A2:I<última fila>` de F-045 R1-R3 y R20 en las tres. (capa: unit)

## Pestañas Obras y Postventa

R2. En «Obras», el grupo de cada trabajador debe llevar solo sus líneas con
`es_postventa` falso, en su orden, con el Código y la Obra de F-040 R8;
`VAR-NN` incluida. (capa: unit)

R3. En «Postventa», el grupo de cada trabajador debe llevar solo sus líneas
con `es_postventa` verdadero, en su orden y con el prefijo de
`export.prefijo_postventa` en Código y Obra. (capa: unit)

R4. Ninguna fila de «Obras» ni de «Postventa» debe ser una línea agregada de
la otra parte: ningún Código «POSTVENTA» u «OBRAS» que no venga de una línea
real y ninguna Obra «RESTO POSTVENTA» o «RESTO OBRAS». (capa: unit)

R5. SI un trabajador con líneas no tiene ninguna de la parte de una pestaña,
ENTONCES no debe salir en esa pestaña: ni grupo, ni fila, ni Empleado. Basta
una línea de esa parte, aunque esté al 0 %, para que salga. (capa: unit)

R6. Cada pestaña debe llevar sus trabajadores en el orden en que los entrega
la API (F-040 R7), sin reordenar: es el orden de entrada con los de R5
quitados. Las dos pestañas pueden tener trabajadores distintos. (capa: unit)

R7. [D2] Un trabajador sin ninguna línea debe tener una sola fila «SIN
CARGA» (F-040 R9) en «Obras» y en «Detalle», y no salir en «Postventa».
(capa: unit)

R8. [D1] Total empleado, Desviación y Estado de cada grupo, en las dos
pestañas, deben ser los del trabajador completo (F-040 R16 y R19), los
mismos que en «Detalle». La columna % del grupo suma solo la parte de esa
pestaña, que en un trabajador repartido es menos que su Total. (capa: unit)

R9. [D3] SI ningún trabajador tiene nada de la parte de una pestaña (un mes
sin postventa, o un periodo vacío), ENTONCES la hoja debe salir igual, con
título y cabecera y sin filas de datos, con el autofiltro `A2:I2`.
(capa: unit)

R10. Cada pestaña debe alternar las bandas por trabajador **de esa pestaña**
(el primero en blanco), poner la línea `medium` bajo el último de cada grupo
y combinar A, B, F, G y H en los grupos de más de una fila, con el valor en
todas (F-045 R13 y R14); la columna I, nunca combinada. (capa: unit)

R11. Ninguna celda de ninguna de las tres hojas debe ir en cursiva.
(capa: unit)

R12. «Detalle» no debe cambiar: todos los trabajadores del cuadrante,
también los que faltan en una pestaña, con todas sus líneas, la postventa
intercalada con su prefijo y su formato de F-045 R17. (capa: unit)

R13. El prefijo de postventa debe seguir saliendo de la configuración
(F-045 R18), probado con «PV_» hasta el libro. Ruta `export.xlsx`, filtro
por empresa, nombre del fichero y puerto `ExcelExporter` no cambian: los
tests de F-024 siguen en verde sin tocarlos. (capa: unit)

## Documentación

R14. La línea de `excel/` en `docs/ARCHITECTURE.md` y la fila de
`export.xlsx` en `services/dedicacion-api/README.md` deben decir que «Obras»
lleva solo obras y «Postventa» solo postventa, sin línea agregada, y no
mencionar «RESTO» ni «la otra parte en una línea». (capa: unit)

## Verificación manual (humano)

M1. Excel de octubre de 2026 (el mes con postventa) generado con la api
local y abierto en Excel (design §7): sin aviso de reparación; ninguna fila
«RESTO …»; quien solo tiene postventa no sale en «Obras» y quien solo tiene
obras no sale en «Postventa»; «Detalle» con todos; y visto bueno a cómo se
leen Total, Desviación y Estado según D1.
