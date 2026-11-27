<!-- progress/manual_F-081.md -->
# F-081 · Verificaciones MANUAL

## M1 (T11), en producción tras desplegar el front (2026-11-27): **cumple**

Hecha por el **líder** a petición del humano («desplegado, pruebalo», «pruebalo
ahora»), en la sesión del navegador del humano, sobre el front
`r20261127-0913` (`ca-dedicacion-front--r20261127091315`, 100 % del tráfico;
el `app.js` servido lleva `evaluarExpresion`). Mes **2026/11, ABIERTO**, empresa
1, **sin registrar en Sigrid** (no se pulsó ningún «⇪ Sigrid»).

Trabajador de prueba: el de la fila `ALVAREZ GARCIA, IGNACIO RAFAEL` (una línea
`0678` al 100 %, casillas `CAJA CA0147` y `VP VP0090` (km) vacías, sin
comentarios). Se apuntó todo antes y se dejó igual al terminar.

| Paso | Esperado (design §8) | Resultado |
|---|---|---|
| `100/3` y Tab en el % | `33,33` y el total lo suma | **Cumple.** En cursiva mientras se escribe; al salir, `33,33`, total en vivo «33,33 % · falta 66,67 %», «●» de guardando y luego ✓ |
| `=50+60` y Tab | aviso de rango y vuelve a `33,33` | **Cumple.** Aviso de error «La operación da 110: el % tiene que estar entre 0 y 100»; la celda vuelve a `33,33`; nada guardado |
| `30+` y Enter | aviso «no válida» y foco en el buscador de obra | **Cumple.** Aviso «Operación no válida: «30+» (no válida)» y foco en «Añadir obra o Postv-…». Ver observación 1: la celda queda en `30`, no en `33,33` |
| km `120*2` y Enter | `240` | **Cumple.** En cursiva mientras se escribe; con Enter, `240` |
| Recargar el mes | los valores siguen | **Cumple.** Tras recargar, la línea `0678` en 30 (lo que dejó el paso 3) y `VP0090` con 240 km |
| `title` de ayuda (D7) | ejemplo en las dos celdas | **Cumple.** «Admite operaciones: 30+10, 100/3, (8+4)*2» en el % y en la casilla de km |

**Restaurado** y comprobado tras recargar: `0678` al 100 %, `VP0090` y
`CA0147` vacías, sin comentarios; el contador vuelve a «13 OK».

### Observaciones para el humano (no bloquean; la spec se cumple)

1. **Una operación no válida que empieza por un número deja la celda en ese
   número.** Al teclear `30+`, el `3` y el `30` son números llanos y cuentan
   en vivo como siempre (se programa su guardado); solo con el `+` la celda pasa
   a operación y deja de contar. Si la operación no vale, R10 repone «el % de la
   línea», que para entonces ya es 30. Lo mismo ocurre, sin consecuencias, con
   las válidas: `100/3` pasa por 1, 10 y 100 antes del `/`, y al confirmar queda
   el resultado. Si se prefiere que la celda vuelva al valor de antes de
   empezar a teclear, sería una feature nueva: R10 dice otra cosa.
2. **Un texto tecleado se perdió una vez.** El primer intento de `120*2` en la
   casilla de km, justo después del Enter del paso 3, quedó vacío y sin aviso.
   Lo más probable es que el guardado diferido del % (el `30`) llegara mientras
   se escribía y repintara el editor. El segundo intento, ya sin guardado
   pendiente, fue bien. Si la causa es esa, no viene de F-081, que no cambia
   el guardado ni el repintado; no se ha comprobado ni reproducido aposta.
