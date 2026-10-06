# F-040 · El Excel de exportación como el modelo de Juan Romero

Pedida por el humano el 2026-10-06: «modifique el excel que se genera para que sea como el del
email de juan último. Que se agrupen los resultados por trabajador, separando con color y línea
gruesa entre trabajadores». Modelo: «Reparto Mensual_PruebaDEF.xlsx» (correo «RV: ARCHIVO PRUEBA
DEFINITIVO», 2026-10-06; **no se versiona**, lleva nombres). Absorbe F-020 (revisar anchos,
formatos, cabeceras, autofiltro e impresión; quitar la columna E «Obra(código)»).

**Servicio: solo `dedicacion-api`** (`infrastructure/excel/`); no cambian front, transfer, esquema, ruta ni puerto.

## Lo que hay hoy (leído y ejecutado el 2026-10-06)

- Dos hojas, «Detalle» (9 columnas, con «Obra(código)») y «Resumen» (5), título en la fila 1,
  **fila 2 en blanco**, cabecera en la 3, paneles en `A4`, **sin autofiltro**, Total, Desviación y
  Estado repetidos en cada línea, sin agrupación visual, sin ajustes de impresión.
- El Resumen ya tiene las columnas del modelo, pero «Obras» lleva solo el código («0702 = 33%»).
- **Fallo**: `Decimal.normalize()` saca notación científica. Con el exportador real, 100 % sale
  «0702 = 1E+2%» y 90 %, «FALTA 1E+1%» y «Postv-0702 = 9E+1%».
- Ningún test ejecuta el exportador: con `coverage run --include="infrastructure/excel/*"` sobre
  los 586 tests de la api, `exporter.py` queda al 26 % (solo las líneas de módulo).

## Decisiones (D1-D6 = A, decididas por el humano el 2026-10-06 al aprobar la spec)

**D1 · Nombre de la obra en «Obras» del Resumen** (el modelo usa abreviaturas a mano): la
`descripcion` de la obra tal cual, sin prefijo; la celda se ajusta en varias líneas.
Descartadas: B, recortarla a N caracteres; C, un «nombre corto» editable (ORM, endpoint y
front), que sería otra feature.

**D2 · Celdas combinadas:** se combinan por trabajador Empleado, Categoría, Total, Desviación y
Estado, **con el valor en todas las celdas del grupo**, para que el autofiltro devuelva el grupo
entero como en el modelo (evidencia en design §5). Se acepta que Excel no deje ordenar la hoja.
Descartadas: B, no combinar; y la combinación normal de openpyxl, porque el filtro pierde las
filas del grupo.

**D3 · Colores:** bandas blanco / `DDEBF7` alternas por trabajador; línea `medium` negra bajo el
último de cada uno; cabecera `1F3864` con texto blanco en negrita, como hoy; el Resumen, sin
bandas. Descartadas: B, gris `F2F2F2`; y el borde `thick`.

**D4 · Filas y columnas que lee negocio:** se adopta el modelo. Es la decisión expresa que
pedía F-020. La cabecera pasa a la fila 2, sale «Obra(código)» y desde la F las columnas se
corren a la izquierda (% en E, Estado en H). Descartada: B, conservar la cabecera en la fila 3.

**D5 · Hojas:** solo «Detalle» y «Resumen». Descartada: B, una hoja «Datos» plana; si hace
falta, irá en F-038.

**D6 · Postventa y VAR en el Detalle:** el convenio del sistema, `Postv-0702` /
`Postv-<descripción>` (una por obra) y `VAR-29` con su partida (F-039 R21). Descartada: B,
imitar «RESTO POSTVENTA» / «VAR» del modelo, que pierde la obra de cada postventa.

## Libro

R1. [D5] El export debe generar un libro con dos hojas y en este orden: «Detalle» y «Resumen».

R2. [D4] Cada hoja debe llevar en la fila 1 su título, en negrita y a 13 pt:
«DETALLE DE DEDICACIÓN · <Mes> <Año>» o «RESUMEN · <Mes> <Año>», con el mes en castellano y la
mayúscula inicial. La cabecera va en la fila 2 y los datos desde la 3, sin filas en blanco.

R3. Cada hoja debe tener el autofiltro de la cabecera a la última fila de datos (`A2:H<n>` y
`A2:E<n>`) y los paneles congelados en `A3`. Sin trabajadores, el autofiltro cubre solo la
cabecera.

R4. Cada hoja debe imprimirse en horizontal, ajustada a una página de ancho y repitiendo las
filas 1-2 en cada página, con los anchos de columna de design §4.

R5. La cabecera debe ir con fondo `1F3864` y texto blanco en negrita.

## Hoja Detalle

R6. [D4] La cabecera del Detalle debe ser exactamente: Empleado | Categoría | Código | Obra |
% dedicación | Total empleado | Desviación | Estado (sin «Obra(código)»).

R7. El Detalle debe tener una fila por línea de cada trabajador, en el orden en que la API
entrega trabajadores y líneas (hoy: por nombre y por código de obra). El exportador no reordena,
y las filas de un trabajador quedan seguidas: son su **grupo**.

R8. [D6] Código y Obra deben ser `cod` y `descripcion` de la línea. En la de postventa, ambos
llevan el prefijo `export.prefijo_postventa` de `config.yaml` (`Postv-0702`).

R9. Un trabajador sin líneas debe tener una sola fila: Código, Obra y % vacíos, Total 0,
Desviación vacía y Estado «SIN CARGA».

R10. Empleado, Categoría, Total empleado, Desviación y Estado deben llevar su valor en **todas**
las filas del grupo, para que filtrar por cualquier columna devuelva filas completas.

R11. [D2] DONDE un grupo tiene más de una fila, sus columnas A, B, F, G y H deben ir combinadas
de la primera a la última fila del grupo, con alineación vertical centrada. Un grupo de una
fila no se combina, y C, D y E no se combinan nunca.

R12. [D3] Los grupos deben alternar el relleno: el primero blanco, el segundo `DDEBF7`, el
tercero blanco, y así. La última fila de cada grupo lleva borde inferior `medium` negro; los
demás bordes, finos y grises.

## Hoja Resumen

R13. La cabecera del Resumen debe ser Empleado | Categoría | Obras | Total % | Estado. Debe haber
una fila por trabajador, en el orden del Detalle, sin celdas combinadas ni bandas.

R14. [D1] «Obras» debe unir con « + » un «<código> <nombre> = <pct>%» por línea. El código es el
del Detalle (R8) y el nombre, la `descripcion` de la obra sin prefijo («Postv-0702 Hotel Virgen
Puerto = 30%»). Debe ir con ajuste de texto, y vacía si el trabajador no tiene líneas.

R15. «Total %» debe ser el total del trabajador, y «Estado», el mismo texto que en el Detalle.

## Cifras: las pone la regla del 100 %, no el exportador

R16. El total debe ser `CuadranteTrabajador.total`, y estado y desviación, los de
`domain.estados.calcular_estado` y `calcular_desviacion`. El exportador no tiene umbral ni
épsilon propios: un total de 99,996 sale «OK» y desviación 0. No escribe fórmulas.

R17. Las celdas de porcentaje (% dedicación, Total, Desviación, Total %) deben guardar la
fracción (55 % → 0,55), con formato `0%` si el porcentaje es entero y `0.00%` si no.

R18. Todo porcentaje escrito como texto («Obras» y Estado) debe salir sin decimales si es entero
(«100%», «FALTA 10%») y, si no, con dos decimales y coma decimal («33,33%»). Nunca en notación
científica.

R19. El texto de Estado debe ser «OK», «SIN CARGA», «FALTA <n>%» o «EXCESO <n>%», con n el valor
absoluto de la desviación (R18).

## Lo que no cambia

R20. La ruta `GET /api/v1/periodos/{a}/{m}/export.xlsx`, el filtro por empresa, el nombre del
fichero (`export.nombre_fichero`), el puerto `ExcelExporter.exportar(periodo, filas) -> bytes` y
`config.yaml` deben seguir como están (los tests de F-024 R6 y R15 siguen en verde sin tocarlos).

## Documentación

R21. `docs/ARCHITECTURE.md` (la línea de `excel/`) y `services/dedicacion-api/README.md` (la fila
de `export.xlsx`) deben describir el export nuevo: Detalle agrupado por trabajador y Resumen.
`azure-apps/` no cambia: no describe el Excel.

## Verificación manual (humano)

M1. Generado en local con datos reales y abierto en Excel: abre sin aviso de reparación, y
filtrar por Empleado, por Obra y por Estado deja filas completas y legibles (design §6).
El humano da el visto bueno al aspecto: colores, línea y anchos.
