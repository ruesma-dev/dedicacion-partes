<!-- progress/spec_F-074.md -->
# F-074 · Resumen de la spec (spec-author, 2026-11-22)

Spec: `specs/F-074-partida-sin-automatica/` (requirements 144/150, design
208/250, tasks T1-T16). Rigor `critico` (disparador 2: la partida es lo que
se escribe en Sigrid de producción). Toca transfer, api y front (design §1).

## Qué se decide

- **Diagnóstico** (design §2): hoy queda «automática» en nueve casos. Los
  principales: (a) la regla no da partida, la línea entra en la memoria «sin
  propuesta» de F-055 y nadie la marca; (d) las líneas de **postventa** nunca
  se encolan; (e) las **subfilas** en cálculo no tienen marca de pendiente;
  (g) una subfila en memoria no se reencola cuando su titular gana partida
  (fallo latente); (i) una propuesta guardada que deja de valer se sigue
  enseñando.
- **Misma regla que el registro**: lo que se enseña sale siempre de
  funciones del transfer (`proponer_partida`, `PasoVinculados.proponer`,
  `casar_postventa`). La api solo guarda y marca; el front solo pinta.
- **Celda** (R1): elegida → fija → propuesta → «buscando partida…» → «no
  encuentra partida» (aviso, clic al selector) → «sin calcular» (ABIERTO) →
  «—». Nunca «automática». El filtro casa con el texto de la celda.
- **Postventa**: la partida que el universo de postventa ya devuelve en cada
  sync (hoy la api la tira) se guarda en `obra.postventa_partida_*` y se
  enseña con método «obra de postventa»; no viaja al registro.
- **Propuesta que deja de valer**: el transfer marca `propuesta_descartada`
  en la acción, el modal lo dice y la api borra la guardada si no hay otra.
- **Coste**: cero lecturas nuevas de Sigrid (design §8); solo R10 reencola
  las subfilas de una línea al cambiar su titular.

## Decisiones abiertas (design §12), con recomendación

| D | Pregunta | Recomendado |
|---|---|---|
| D1 | Cómo se enseña «no la encuentra» | (a) aviso en la celda + selector; la Regla C sigue al registrar (no bloquear) |
| D2 | Partida de postventa | (a) la del universo, guardada en el sync (0 lecturas; un sync tras desplegar) |
| D3 | Reintento de las no encontradas | (a) como hoy: hasta sync o reinicio; el preflight vuelve a buscar |
| D4 | Propuesta que deja de valer | (a) aviso en el modal + borrar la guardada sin sustituta |
| D5 | Opción «automática» del selector | (a) renombrarla «sin elegir · usar la propuesta / no encuentra partida» |
| D6 | Motivo del «no encuentra» | (a) texto fijo, sin motivo; con motivo, feature aparte |

## Riesgos

- Tras desplegar, las de postventa dicen «sin calcular» hasta el primer
  «Sincronizar Sigrid» (T15 lo incluye).
- La partida de postventa puede quedar vieja si su presupuesto cambia entre
  dos syncs; el modal enseña la que se escribe (como `admite_postventa`).
- Memoria de una sola réplica: tras un reinicio, las no encontradas pasan un
  rato por «buscando partida…».
- Lista cerrada de tests que cambian (requirements §8): seis del front y uno
  de la api; cualquier otro, PARA.
