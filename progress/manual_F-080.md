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

## M1 (T9), justo antes de desplegar (2026-11-26): **NO da 0, PARADA**

Hecha por el **líder** a petición del humano («haz m1»), solo lecturas, desde la
sesión del navegador del humano en producción: `GET /api/v1/periodos` y `GET
/api/v1/periodos/{anio}/{mes}/cuadrante?empresa={1,18,25,31}`.

| Qué se mira | Resultado |
|---|---|
| Periodos | 2026/03 a 2026/12; todos ABIERTOS salvo 2026/10 (CERRADO), como ayer |
| Subfilas de caja por obra | 639: 2026/08 (211), 09 (206), 10 (217) y 11 (5), solo empresa 1 |
| **Con importe** | **4**, todas en 2026/11, del mismo trabajador (ide 1372198): obras 0678 (40 %) 160 €, 0692 (30 %) 120 €, 0704 (15 %) 60 € y 0713 (15 %) 60 €; comentario «26-11» en las cuatro; sin copiar |
| Caja del mes (por %) | 0 (aún no existe el tipo) |

- Las cuatro suman 400 € y son exactamente 400 € × el % de cada obra: tecleadas
  ya como si la caja fuera por %. Con F-080, 400 € en su casilla del mes dan
  `tot` 160/120/60/60, lo mismo.
- El trabajador está en estado `OK` y `puede_deshacer: false`: según el
  cuadrante, sin registro en Sigrid que deshacer.
- **(2) Lectura de Sigrid por `sigrid-api`: no hecha.** Pide la function key de
  `sigrid-api` (un secreto) y el datamart no guarda el `synckey`. T9 admite la
  confirmación del humano.
- Por T9, PARA y decide el humano. Sin la pasada de restos (D2), al desplegar
  esas 4 cantidades dejan de verse y no se mandan: el trabajador saldría «falta
  el importe del mes» hasta teclear 400 € en su casilla de caja.
