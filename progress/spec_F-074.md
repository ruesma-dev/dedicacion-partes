<!-- progress/spec_F-074.md -->
# F-074 · Resumen de la spec (spec-author; revisada el 2026-11-23)

Spec: `specs/F-074-partida-sin-automatica/` (requirements 136/150, design
217/250, tasks T1-T19). Rigor `critico` (disparador 2). Transfer, api y front.

## Revisión 2 (2026-11-23): cambio de enfoque del humano

«d6 la b» y «cuando se le da a registrar ya no hay que casar partidas, ya
vienen definidas». La primera versión (commit `1e808fa`) mantenía el
preflight proponiendo como red y añadía `propuesta_descartada` («se propuso
otra»). Eso desaparece: la regla corre **solo en segundo plano** (cola,
selector, universo del sync) y el registro escribe la **definida** (elegida,
fija VAR, propuesta guardada o, en postventa, la de su obra), validada por
`ide`, sin proponer otra.

## Qué se decide

- **Registro** (R1-R7): sin proponer ni casar; la definida que no vale se
  omite nombrándola (`partida_no_valida`); sin definida, Regla C (obra
  normal, subfila) u omitida (postventa).
- **Motivos** (D6 b, R9-R10): `partidas/propuesta(-lote)` y
  `postventa/universo` devuelven el motivo de lo que no encuentran; la api lo
  guarda en su memoria o en la obra y lo publica.
- **Celda** (R17): elegida → fija → propuesta → «buscando partida…» → «no
  encuentra partida» + motivo → «sin calcular» / «—». Nunca «automática».
- **Postventa** (D2 a): la partida del universo se guarda en el sync y
  **viaja al registro**.
- **Ahorro de lecturas del preflight** (design §8, contado del código): con
  la cola al día, 1 lectura por lote con postventa (su presupuesto); en el
  peor caso (mes recién abierto, tras sync, transfer caído), N presupuestos
  de origen + el historial de 24 meses (la más pesada) + la de postventa + 2
  por obra con vinculados. Medición real: MANUAL T16 (`medir`, antes y
  después).

## Decisiones abiertas (design §12), con recomendación

| D | Pregunta | Recomendado |
|---|---|---|
| D1 | Cómo se enseña «no la encuentra» | (a) aviso en la celda con motivo y selector |
| D2 | Partida de postventa | (a) la del universo, guardada en el sync y mandada al registro |
| D3 | Reintento de las no encontradas | (a) como hoy (sync o reinicio); el selector ya recalcula |
| D4 | Definida que ya no vale al registrar | (a) omitida con motivo y selector; la api borra la guardada y la cola recalcula |
| D5 | Opción «automática» del selector | (a) renombrarla |
| D6 | Motivo del «no encuentra» | **Decidida: (b)**, humano 2026-11-23 |
| D7 | Registrar con líneas sin definida | (a) esa línea no se escribe; el modal la lista con selector; el resto sí |
| D8 | Qué queda de la Regla C | (a) se queda el conflicto con su casilla (`paride = 0`), ahora para «sin definida»; (b) si negocio no quiere partes sin partida |

## Riesgos

- **Las de postventa no se registran hasta el primer sync** tras desplegar:
  orden obligatorio api → sync → transfer → front (T18).
- Una línea aún «buscando…» al registrar sale sin definida (D7).
- Cambian muchos tests del preflight: lista cerrada **por criterio** con
  ficheros candidatos (requirements §6, tasks); el implementer anota cada uno
  antes de tocarlo.
- Memoria de una réplica: tras un reinicio, las no encontradas pasan por
  «buscando…».
