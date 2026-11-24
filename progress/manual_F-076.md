<!-- progress/manual_F-076.md -->
# F-076 · Verificación MANUAL M1 (T7)

Hecha por el **líder** el 2026-11-24, a petición del humano («haz tu m1»), en
la rama `feature/F-076-excel-sin-resto-de` (HEAD `e372280`). Solo lectura: la
api local contra la base `dedicacion` LOCAL; nada toca Sigrid ni Azure.

## Cómo

1. api local: `.venv/Scripts/python.exe main.py` en `services/dedicacion-api`
   (`PG_HOST=localhost`); parada al terminar.
2. `curl -o <scratchpad>/f076.xlsx "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"`
   → `200`, 35.297 bytes.
3. Lectura con `openpyxl` (script en el scratchpad de la sesión, no
   versionado) comparando cada pestaña con «Detalle», trabajador a trabajador.
4. Apertura con Excel por COM, solo lectura y sin interfaz.

## Resultado: CUMPLE

| Qué se mira (design §7) | Resultado |
|---|---|
| Excel lo abre sin reparar | Sí: abre por COM con su nombre (`f076.xlsx`, sin «[Reparado]») y las tres hojas completas (Obras 193, Postventa 183 y Detalle 196 filas usadas). No se vio la ventana: con `DisplayAlerts` apagado, un aviso de reparación no se habría enseñado, pero el libro abrió entero |
| Tres hojas, cabecera de nueve columnas, autofiltro | `Obras`, `Postventa`, `Detalle`; cabecera con Observaciones; autofiltro `A2:I<última>` en las tres |
| Ninguna fila «RESTO …» | 0 |
| Ninguna celda en cursiva | 0 |
| Cada pestaña solo con su parte | En las tres comparaciones, las líneas de cada trabajador en «Obras» son exactamente sus líneas de obra de «Detalle», y en «Postventa» sus líneas `Postv-`: 0 discrepancias |
| Quien no tiene nada de una parte no sale en esa pestaña | Cumple: 7 trabajadores con solo obras no salen en «Postventa». El mes no tiene a nadie con solo postventa (ese caso lo cubren los tests unitarios de R5) |
| «SIN CARGA» en las dos pestañas (D2 a) | Los 178 sin carga están en «Obras» y en «Postventa» |
| Total, Desviación y Estado de la parte (D1 b) | Total = suma del % de la pestaña en todos los grupos (0 discrepancias). Los 3 repartidos reales: 65/35 → «FALTA 35%» en Obras, «FALTA 65%» en Postventa y «OK» en Detalle; 50/50 → «FALTA 50%» en las dos y «OK» en Detalle; uno con 100 + 100 → «OK» en cada pestaña y «EXCESO 100%» en Detalle |
| Orden | Cada pestaña sigue el orden de «Detalle» (la api), sin reordenar |
| «Detalle» con todos | 188 trabajadores, los mismos que «Obras» (188, por los sin carga); «Postventa», 181 |

## Notas

- Datos del mes en la base local: 10 trabajadores con obras, 3 con
  postventa (los tres también con obras) y 178 sin carga. Es una muestra
  pequeña de casos reales, pero cubre los de D1 b.
- El caso «EXCESO 100%» en Detalle con «OK» en cada pestaña es lo que pide
  D1 b: cada pestaña mira solo su parte. Para verlo hay que mirar «Detalle».
- Cabecera «Total empleado» en las pestañas: sin cambiar (design §8); el visto
  bueno al rótulo es del humano.

## Producción (2026-11-24): CUMPLE

Hecha por el **líder** a petición del humano («miralo tu en produccion»; OK
expreso a descargar el Excel). `export.xlsx` de octubre de 2026 de la api
desplegada (`r20261124-1826`), bajado desde la sesión del navegador (200,
51.990 bytes) a la carpeta temporal de la sesión, tras la sincronización de
`progress/manual_F-074.md`. Mismo script y misma apertura con Excel que la
M1.

| Qué se mira | Resultado |
|---|---|
| Excel lo abre | Sí, completo (Obras 297, Postventa 87 y Detalle 349 filas usadas) |
| Filas «RESTO …» / cursiva | 0 / 0 |
| Cada pestaña solo con su parte, comparada con «Detalle» | 0 discrepancias |
| Quien no tiene nada de una parte no sale en esa pestaña | 143 solo con obras, fuera de «Postventa»; 12 solo con postventa, fuera de «Obras» |
| «SIN CARGA» en las dos pestañas | los 33, en las dos |
| Total = suma de la pestaña (D1 b) | 0 discrepancias; los 2 repartidos: 94/6 y 27/73 salen «FALTA» en cada pestaña y «OK» en «Detalle»; los de solo postventa, «OK» |
| Recuento | Detalle 190 = 145 con obras + 14 con postventa − 2 repartidos + 33 sin carga; Obras 178; Postventa 47 |
