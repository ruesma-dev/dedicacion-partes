<!-- specs/F-025-obras-postventa-postv2/requirements.md -->
# F-025 · Obras de postventa sacadas de POSTV2 — requisitos

Rigor **crítico**: el transfer desplegado escribe de verdad desde el 2026-10-01
(`docs/INTEGRACION.md` §8). Servicios: **transfer** (único dueño del universo), **api**
(lo pide en el sync y lo guarda), **front** (pinta). Origen: `explore_maestros_sync.md` §A.

## Contexto (hechos, no requisitos)

- Los «capítulos de POSTV2» son, en Sigrid, **partidas hoja** de su presupuesto
  (`progress/sigrid_F-002.md` §C2), donde imputa P5: «partida hoja, nunca capítulo» sigue.
- Data mart (`build_stg` 2026-10-01 05:28 UTC, `build_maestros` 07:08 UTC): POSTV2 de
  la empresa 1 tiene **221** hojas activas. **81** obras de la empresa 1 casan por
  código exacto (71 CERRADA, 1 TERMINADA, 6 EN CURSO, 2 RECIBIDA DEF., 1 RECIBIDA
  PROV.); **72** las quita hoy `estados_excluidos`. Dos más casan por prefijo con
  sufijo de letra: 0578 (CERRADA) → `0578B`, 0654 (EN CURSO) → `0654-B`.
- **Falsos casados de la cascada vigente de P5** (aproximación SQL; la confirma M1):
  `CP` (EN CURSO) casa con `CP.1`, hoja del capítulo de costes proporcionales; `OT`
  (EN ESTUDIO) casa por descripción con `CI.7.5`; `191105` (EN ESTUDIO), por nombre
  con `0611`. `CP` y `OT` están activas y **hoy ya** se ofrecen como `Postv-`.
- POSTV2 de la empresa 28: 6 hojas sin cero inicial (`626`, `664`…); Porsan tiene
  `0664`, `0680` y `0693`. POSTV (antigua, empresa 1): 15 hojas, 14 obras solo ahí.
- El preflight publica `partidas_postventa` en obras sin líneas de postventa: el
  catálogo `_nodos_pv` vive en la instancia del pipeline, única en la app (F-022).

**Universo de postventa de la empresa E**: las obras de E a las que P5 encuentra
partida en la obra `POSTVENTA_OBRA_COD` de E. **Línea ofrecible**: la normal de una
obra `activa` o la de postventa de una obra `admite_postventa`.

## Transfer: el universo, calculado en un solo sitio

R1. CUANDO llega `POST /api/postventa/universo` con obras (`ide`, `codigo`, `nombre`,
`empresa`), el sistema debe devolver en `obras` cada una que esté en el universo de su
empresa, con la partida que le daría P5 (`ide`, `cod`, `res`), sin escribir en Sigrid.

R2. El sistema debe calcular el universo con la **misma** carga de catálogo y la
**misma** función de casado que el preflight: una obra está en el universo con la
partida X si y solo si el preflight de una línea de postventa suya le asigna X, y
está fuera si y solo si el preflight la omite por P5 (no casa, obra de postventa
ausente o ambigua, postventa desactivada).

R3. SI la obra de postventa no existe en la empresa E o es ambigua, ENTONCES el
sistema debe dejar fuera todas las obras de E y publicar en `empresas[E].motivo` el
mismo motivo que daría el preflight.

R4. SI una obra llega sin empresa válida (ausente, nula, 0 o negativa), ENTONCES el
sistema debe dejarla fuera del universo.

R5. MIENTRAS `POSTVENTA_REGISTRAR` sea `false`, el sistema debe devolver el universo
vacío, con ese motivo en cada empresa.

R6. SI falla una lectura de Sigrid, ENTONCES el sistema debe responder HTTP 502
`{"ok": false, "error": …}`, nunca un universo parcial.

R7. El sistema debe leer la obra de postventa y su presupuesto **una vez por empresa**
y petición, no una vez por obra.

R8. CUANDO un preflight no tiene líneas de postventa, el sistema debe publicar
`partidas_postventa = []`, aunque una petición anterior a la misma instancia las tuviera.

R9. El sistema debe validar el `paride` manual de postventa contra el catálogo leído
**en esa misma petición**; ningún catálogo sobrevive a la petición que lo leyó.

R10. [D2] El casado de P5 debe aceptar solo el código exacto o, si no lo hay, una
partida cuyo código normalizado empiece por el de la obra **seguido solo de letras**
(la de código más corto y, a igualdad, el menor). Fuera los escalones «código en la
descripción» y «nombre».

R11. [D2] SI una obra solo casa por un escalón retirado o por un prefijo seguido de
algo que no son letras (`CP` → `CP.1`), ENTONCES el sistema debe dejarla fuera del
universo y el preflight debe omitir su línea de postventa con el motivo de «no casa».

## API: el universo se pide en el sync y se guarda en la obra

R12. CUANDO se sincronizan los maestros, el sistema debe pedir el universo al transfer
**una vez**, con todas las obras leídas (también las excluidas por estado), cada una
con el `cod`, la `descripcion` y la `empresa` que se van a guardar.

R13. El sistema debe guardar en cada obra `activa` (no excluida por estado, criterio de
hoy) y `admite_postventa` (en el universo), independientes entre sí.

R14. SI una obra está excluida por estado y no admite postventa, ENTONCES el sistema
debe tratarla como hoy: no recibida, con `activa` y `admite_postventa` a `false`.

R15. SI el transfer no responde, responde `ok: false` o no trae `obras`, ENTONCES el
sistema debe fallar el sync entero con HTTP 502 nombrando el universo de postventa,
sin persistir nada (D3).

R16. CUANDO se pide `GET /sync/preview`, el sistema debe calcular lo mismo que el sync
y publicar en `obras`: `admiten_postventa`, `solo_postventa` (excluidas por estado y en
el universo), su desglose por empresa y el motivo de cada empresa sin universo.

R17. El sistema debe publicar `admite_postventa` en cada obra del cuadrante y ofrecer
las de la empresa elegida que estén `activa`, `admite_postventa` o usadas en el periodo.

R18. El sistema debe publicar en cada línea `obra_admite_postventa` y `ofrecible`,
calculado por **una sola** función del dominio.

R19. CUANDO se copia el periodo anterior (entero o de un trabajador), el sistema debe
copiar solo las líneas ofrecibles y contar las demás en `lineas_omitidas_obra_inactiva`.

R20. [D7] SI al guardar llega una línea no ofrecible que **no estaba ya guardada** para
ese trabajador y periodo (misma obra y modo), ENTONCES el sistema debe rechazar el
guardado entero con HTTP 422 (`ObraNoValida`). Deshacer no cambia.

R21. El sistema debe declarar `obra.admite_postventa` (booleano, no nulo, `false` por
defecto en servidor) solo en el ORM, con el `ALTER` derivado por `esquema.py`.

## Front: solo pinta

R22. El front debe ofrecer la entrada normal de una obra si y solo si `activa`, y la
`Postv-` si y solo si `admite_postventa`, sin otra fuente (ni literales de obra o POSTV).

R23. El botón PV debe permitir pasar a un modo solo si la API marca la obra con ese
modo (`obra_activa` / `obra_admite_postventa`).

R24. «Copiar de la fila superior» y la marca de línea no utilizable deben usar el campo
`ofrecible` de la API.

## Documentación

R25. `docs/ARCHITECTURE.md#regla-p5` debe decir que el universo de `Postv-` es el de
P5, calculado en el transfer y guardado por el sync; que una obra excluida por estado
solo se ofrece como `Postv-`; y (D2) el casado de R10. El módulo nuevo del transfer no
lleva el literal del código de postventa (`test_f002_fuente_unica.py`).

R26. `docs/INTEGRACION.md` debe documentar el endpoint nuevo y que la api lo consume
en el sync; `azure-apps/dedicacion.md` se refresca (commit del humano).

## Decisiones abiertas (las valida el humano antes de implementar)

- **D1 · El universo vive en el transfer (propuesta)**: es el único que conoce
  `POSTVENTA_OBRA_COD` y P5; la api le pregunta en el sync. Contras: el sync depende
  del transfer y hay un endpoint nuevo. Descartada: que la api lea POSTV2 por
  `sigrid-api`, que duplica el ajuste y la cascada y los deja divergir sin aviso.
- **D2 · Cascada de P5.** (A) P5 intacta: entran `CP`, `OT` y `191105` con partidas
  ajenas (86 obras en la 1) y se escribirían de verdad. (B, **propuesta**) R10-R11:
  83 obras; cambia el texto de P5 y **cuatro tests de F-002**
  (`r18_la_cascada_solo_actua_sin_exacto`, `r18_el_ultimo_escalon_casa_por_nombre_de_obra`
  y los dos `r19`, que pasan a un sufijo de letra). Con (A) se borran R10, R11 y T3.
- **D3 · Transfer caído en el sync: falla entero** (propuesta, como F-032). Alternativa:
  conservar las marcas viejas, que ofrece un universo caducado sin que se vea.
- **D4 · Otras empresas, por `#regla-empresa`**, cada una con su POSTV2. Hoy se ofrece
  `Postv-` en todas las obras de todas; con B la 28 no tiene ninguna (sus partidas no
  llevan el cero) y la 18 y la 31 no tienen POSTV2.
- **D5 · Obra abierta sin partida en POSTV2: sin `Postv-`** (hoy se ofrece y el preflight
  la omite; T13: siete líneas). Lo guardado se queda, marcado; entra al crear su partida.
- **D6 · POSTV antigua fuera**: el transfer solo conoce un código de postventa.
- **D7 · Guardar rechaza líneas nuevas no ofrecibles (R20)**: defensa ante un cliente
  que no sea el front (F-031). Alternativa: dejarlo a F-031 y borrar R20.
