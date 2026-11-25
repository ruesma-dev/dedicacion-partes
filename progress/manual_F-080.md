<!-- progress/manual_F-080.md -->
# F-080 · Verificaciones MANUAL

## M1 adelantada (2026-11-25, antes de decidir D1-D3): no hay cajas tecleadas

Hecha por el **líder** a petición del humano («d1 y d2, hay cajas metidas?»),
en producción y solo con lecturas: `GET /api/v1/periodos` y `GET
/api/v1/periodos/{anio}/{mes}/cuadrante?empresa={1,18,25,31}` desde la sesión
del navegador del humano. No es la `SELECT` de design §10 (sin acceso directo
a la base); mide lo mismo a través del cuadrante, que pinta la `cantidad` y el
`comentario` de cada subfila de caja por obra (`reparto: obra`).

| Qué se mira | Resultado |
|---|---|
| Periodos | 2026/03 a 2026/12; todos ABIERTOS salvo 2026/10 (CERRADO) |
| Subfilas de caja por obra | solo en la empresa 1: 2026/08 (211), 09 (206), 10 (217) y 11 (5) |
| Con importe | **0** en todos los periodos y empresas |
| Con comentario | 1: 2026/11, un trabajador, obra 0678, «26-11» (el mismo texto que su VP del mes), sin importe |
| Caja del mes (por %) | 0 (aún no existe el tipo) |

Consecuencia: la pasada de restos (D2) solo movería ese comentario; D3 no
tiene cajas con importe que volver a registrar. Si D2 se simplifica, repetir
esta lectura justo antes de desplegar.
