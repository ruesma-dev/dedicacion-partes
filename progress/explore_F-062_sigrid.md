<!-- progress/explore_F-062_sigrid.md -->
# F-062 · evidencia de Sigrid: cómo se han registrado las incidencias de los mensuales

Lecturas del líder del 2026-10-23, **solo lectura** (`POST /api/sql/read`
de `sigrid-api`, base `ruesma`, con el cliente del transfer). **Solo
agregados**: ni nombres, ni recursos, ni importes por persona.

## Alcance

- **Universo:** líneas de `hmores` desde 2025.
- **Líneas `M*`:** `auxhor.cod LIKE 'M%'`.
- **Líneas de incidencia:** `auxhor.cod LIKE 'CI%'`. El inicio es `CIE`,
  `CIA`, `CIM`, `CIP`, `CIF`, `CIV` o `CIH`; el cierre, `CIZ`.
- **Mensual:** recurso con al menos una línea `M*` ese mes.
- **Racha:** un inicio y su `CIZ`.
- **Hueco:** días entre el `CIZ` anterior del recurso y el inicio nuevo.
- **Días de la semana:** calculados con `DATEDIFF(day, '19000101', fecha) % 7`
  (0 = lunes).
- **Festivos:** no comprobados, porque no hay calendario.

## Resultados

| # | Pregunta | Resultado |
|---|---|---|
| 1 | Líneas `CI*` de mensuales | 1.895; `tot = 0` en todas menos 1; `can = 0` en el 95 %, el resto `can = 1` |
| 2 | ¿En un parte con su `M*`? | 96 % |
| 3 | Suma de los `M*` en meses con incidencia | 100 % en 730 de 756 meses (con `CIV`: 643 de 661). Las vacaciones no restan % |
| 4 | Fecha del `M*` | Último día del mes en el 94 %, haya incidencia o no |
| 5 | Partida de la `CI*` | 0 en el 57 %; la de su `M*` en el 41 % |
| 6 | Inicio y su `CIZ` en el mismo mes: ¿mismo parte? | Mismo parte 741; otra obra 7 |
| 7 | Rachas de 1 día (`CIZ` el mismo día) | 173 |
| 8 | Rachas cerradas en su mes que abarcan sábado o domingo | 292 de 744; 129 cierran en domingo, 252 en viernes |
| 9 | Inicio con hueco de 1 día desde el `CIZ` anterior | Mismo código 5; otro código 25 |
| 10 | Inicio con hueco de 3 días, de viernes a lunes | Mismo código 19; otro código 8 |
| 11 | Inicio sin `CIZ` en su mes: ¿cuándo llega el primer `CIZ` posterior? | 163 casos: al mes siguiente 137; a 2 meses 12; a 3 o más 5; ninguno 9 |
| 12 | Inicio sin `CIZ` en su mes: ¿qué es lo primero del mes siguiente? | El `CIZ`, sin repetir el inicio: 134; repite el inicio el día 1: 9 |
| 13 | `CIZ` del mes siguiente: ¿en qué parte? | En un parte con su `M*`: 134 de 137. De la misma obra del inicio 94, de otra 40 (ese mes estaba en otra obra) |
| 14 | Rachas de 2 o más meses | 17: los meses de en medio vacíos en 11, con alguna línea en 6 |
| 15 | `CIZ` el último día del mes: ¿qué pasa el día 1 siguiente? | Nada 52; un inicio 4 |
| 16 | Meses de mensuales con 2 o más obras e incidencia | En 1 obra 131 (no siempre la de mayor %); repetida en todas 59; en varias, no todas, 20 |

## Lo que se concluye

- **Inicio y cierre:** la práctica de Administración es la regla del humano.
  Una racha por tramo seguido del mismo código, con inicio y `CIZ` en el
  mismo parte (fila 6).
- **Fines de semana:** la racha los cruza sin cortarse (filas 8 y 10).
- **Fin de mes:** la racha sigue abierta y se cierra en el parte del mes en
  que acaba, sin repetir el inicio (filas 11 a 14).
- **F-030 hoy (D3) no coincide:** cierra cada mes con `CIZ` el último día y
  abre otra racha el día 1. Administración lo hace solo en unos 13 casos
  (filas 12 y 15).
- **Excepciones:** las filas 9 y 10 (5 + 19, mismo código, cortadas en dos)
  serían una sola racha con la regla nueva.
- **Vacaciones que acaban justo el último día:** Administración cierra ese
  día (fila 15) porque ya sabe que la racha no sigue. F-062 lo resuelve con
  su D4.

Scripts de las lecturas: fuera del repositorio, en el scratchpad de la
sesión del líder. No se versionan porque leen la configuración del `.env`
del transfer.
