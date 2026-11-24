<!-- specs/F-076-excel-sin-resto-de/requirements.md -->
# F-076 · Excel: «Obras» solo con obras y «Postventa» solo con postventa

Rigor **`estandar`**. **Solo `dedicacion-api`** (`infrastructure/excel/`); no
cambian front, transfer, esquema, ruta, puerto ni `config.yaml` (design §1).

Negocio, transmitido por el humano el 2026-11-22 (punto 4): «en el excel
quitar los recursos que tengan solo resto de, y las líneas resto de».
Aclarado el mismo día: «en el excel en la pestaña de postventa las obras
normales salen como resto, y viceversa. Con este nuevo enfoque, en postventa
sale solo postventa, y en obra solo obra».

**Decisiones DECIDIDAS por el humano el 2026-11-24** («d1 b, lo demas a»):
D1 = (b), Total, Desviación y Estado de cada pestaña sobre su parte; D2-D5 =
(a), «SIN CARGA» en las dos pestañas, pestaña vacía con cabecera, criterio de
tests de design §6 y fuera el código de la agregada. Tabla: design §10.

**Sustituye** de F-045 (`specs/F-045-excel-obras-postventa/`): D3 (salvo la
«SIN CARGA» en las dos, que sigue), D4, D6, D7 (la línea agregada «RESTO …»)
y D9 (Total de las pestañas), y sus R4, R7, R8, R9, R11, la primera mitad de
R12 (igual en las dos pestañas), R15 y R16. **Siguen**: R1-R3, R5, R6, R10,
la segunda mitad de R12 (la columna % del grupo suma su Total), R13, R14 y
R17-R21. La hoja «Detalle» no cambia.

## Lo que hay hoy (leído el 2026-11-24)

- `contenido.grupos_pestana` añade al final de cada grupo una
  `LineaDetalle(agregada=True)` con la suma de la otra parte; si el
  trabajador solo tiene la otra parte, su grupo es esa línea sola.
  `exporter._hoja_grupos` la pinta con Código, Obra y % en cursiva.
- Total, Desviación y Estado de las pestañas son los del trabajador
  completo (F-045 D9); con la agregada, la columna % de cada grupo suma ese
  Total. Salen de `contenido._grupo` con `fila.total` y `len(fila.lineas)`.
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
CARGA» (F-040 R9: total 0 %, Desviación vacía) en «Obras», en «Postventa» y
en «Detalle», como hoy (F-045 R10). (capa: unit)

R8. [D1] En «Obras» y en «Postventa», el Total empleado de cada grupo debe
ser la suma exacta (`Decimal`) de los % de sus líneas de esa parte, y su
Desviación y su Estado deben salir de ese total y de ese número de líneas
con la regla del 100 % de `domain.estados` (F-040 R16 y R19), sin umbral
propio. Así la columna % del grupo suma su Total (F-045 R12). Un trabajador
al 100 % repartido 85/15 sale «FALTA 15%» en «Obras» y «FALTA 85%» en
«Postventa»; una sola línea de la parte al 0 % da «FALTA 100%», no «SIN
CARGA». (capa: unit)

R9. [D3] SI ningún trabajador tiene líneas de la parte de una pestaña ni
está sin carga (un mes sin postventa y sin nadie sin cargar, o un periodo
vacío), ENTONCES la hoja debe salir igual, con título y cabecera y sin filas
de datos, con el autofiltro `A2:I2`. Con algún «SIN CARGA», lleva solo esas
filas (R7). (capa: unit)

R10. Cada pestaña debe alternar las bandas por trabajador **de esa pestaña**
(el primero en blanco), poner la línea `medium` bajo el último de cada grupo
y combinar A, B, F, G y H en los grupos de más de una fila, con el valor en
todas (F-045 R13 y R14); la columna I, nunca combinada. (capa: unit)

R11. Ninguna celda de ninguna de las tres hojas debe ir en cursiva.
(capa: unit)

R12. «Detalle» no debe cambiar: todos los trabajadores del cuadrante,
también los que faltan en una pestaña, con todas sus líneas, la postventa
intercalada con su prefijo y su formato de F-045 R17, y el Total empleado,
la Desviación y el Estado del trabajador completo (F-040 R16), aunque no
coincidan con los de las pestañas (R8). (capa: unit)

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
obras no sale en «Postventa»; «SIN CARGA» en las dos; «Detalle» con todos;
un trabajador repartido con «FALTA» en cada pestaña y «OK» en «Detalle»; y
visto bueno a que la cabecera «Total empleado» se lea bien en las pestañas
(design §8).
