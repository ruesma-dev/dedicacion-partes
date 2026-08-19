<!-- progress/current.md -->
# Trabajo en curso

**F-002 · Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones**
Rama `feature/F-002-reglas-postventa-conflicto` · `sdd: true` · rigor `critico`
Estado: **Fase 1 (T1–T5) implementada y verificada. Parada en la ⛔ barrera de
`tasks.md`, a la espera de cerrar el rediseño de P4.**

## Qué se ha hecho en esta sesión (2026-08-19)

**Sí se ha tocado código.** 8 commits en la rama, de `04fbd9b` a `2987fc0`
más el de bookkeeping de esta corrección. Informe completo:
`progress/impl_F-002.md`. Campaña de mutación: `progress/mutacion_F-002.md`.
Review de la fase: `progress/review_F-002_fase1.md`.

| Tarea | Estado | Commit |
|---|---|---|
| T1 · fixtures offline parametrizables del transfer | [x] | `04fbd9b` |
| T2 · tests de las reglas no disputadas (R6–R9, R12) | [x] | `60d5319` |
| T3 · un solo punto de decisión para el conflicto | [x] | `22328fb` |
| T4 · R14, R10, R11 y el defecto R13 | [x] | `20280c7` |
| T5 · fuente única de las reglas (lo que no depende de D1/D2) | [x] | `beba73b` |
| T6 en adelante | [ ] | bajo la PARADA |

### Verificado con salida real

- `bash harness/init.sh` → ENTORNO LISTO. Suite del transfer: **90 passed,
  5 xfailed**; raíz 11 passed; api 21 passed.
- **Puerta de cobertura: 96,8 % (30/31 líneas cambiadas)**, umbral 80 %.
- **Campaña de mutación: 9 mutantes, 9 muertos, 0 supervivientes**,
  reejecutada de forma independiente por el reviewer con los mismos totales.
- Es la **primera feature del repositorio en la que estas dos puertas miden
  código de producción**: en F-001 salieron `N/A` por diseño.
- **R13 era un defecto real**, reproducido por el reviewer: dos líneas
  pendientes del mismo recurso y mes con partidas distintas chocaban contra
  la misma línea previa y emitían **dos `DELETE` del mismo `hmores.ide`**,
  con `res.borradas` contando 2. Arreglado deduplicando por `ide`.

## Consultas de lectura contra Sigrid

- **C2 · EJECUTADA** el 2026-08-19, autorizada por el humano. Volcado íntegro
  en `progress/sigrid_F-002.md`. Cerró D1: la obra de postventa es `POSTV2`,
  se imputa a **partida hoja** y el emparejamiento por **código exacto**
  (`cod = '0610'`, `res = 'COLEGIO ALEGRA'`, campos separados) es el correcto.
  De paso encontró cuatro partidas duplicadas sin el cero inicial (`656`,
  `664`, `680`, `693`) colgando de la raíz del presupuesto en vez de `CD`.
- **C1, C3, C4 y C5 · NO ejecutadas.** Siguen escritas en
  `specs/F-002-reglas-postventa-conflicto/requirements.md` §2. C4 perdió casi
  todo su interés cuando el humano contestó D2 directamente.

## Decisiones del humano en esta sesión

1. **D1 · cerrada.** Obra de postventa `POSTV2`, siempre viva. Se imputa
   siempre a la partida de la obra original dentro de POSTV2 (`0610 COLEGIO
   ALEGRA`), **nunca** a una partida normal de ejecución. Confirmado además
   con la lectura C2.
2. **D2 · contestada con una tercera opción.** Pueden convivir varias líneas
   `M*` del mismo trabajador en el mismo parte y mes con **partidas
   distintas**, pero **la suma de sus cantidades no puede pasar de 1**
   (el 100 % del trabajador).

## ⚠ Lo que bloquea la Fase 2

**La respuesta a D2 no es ninguna de las dos versiones que se enfrentaban en
el repositorio**, así que `design.md` §7 (Riesgo 2) queda invalidado en esa
parte: la regla P4 hay que **diseñarla de cero** (validar la suma del mes
contra lo que ya existe en el parte, decidir qué ocurre cuando se pasa del
100 % y qué ve el usuario en el front). El líder debe **volver a la PARADA 1**
con esa propuesta antes de que nadie implemente T11.

## Verificaciones `MANUAL (humano)` pendientes

Ninguna de la Fase 1 lo era. Todas las que quedan están bajo la PARADA:

| Tarea | Qué es | Comando |
|---|---|---|
| T6 | llevar a Administración lo que quede abierto tras el rediseño de P4 | copiar de `requirements.md` §2 |
| T7 | ejecutar C1, C3, C4, C5 contra `sigrid-api` (**solo lectura**) | el `Invoke-RestMethod` de `tasks.md` T7, con la function key fuera del repositorio |
| T13 | casado real contra Sigrid **sin escribir** | `python prueba_escritura_porcentajes.py capitulos` / `estado` / `preflight` |
| T14 | escritura real en la obra de pruebas `0404` | `ejecutar --confirmar` → `verificar` → `limpiar --confirmar`. **Exige autorización expresa del humano para esa acción concreta**; ningún agente la lanza |

`OBRA_PRUEBAS_FORZAR` sigue en `true` y esta fase no ha tocado ningún `.env`.

## Otras features vivas

- **F-003** (`spec_ready`): spec escrita y commiteada en su propia rama
  `feature/F-003-orm-columnas-sigrid` (`e3e03ac`). **Pendiente de que el
  humano la apruebe.** Hallazgo relevante: hoy los `ALTER TABLE` a mano se
  ejecutan dentro de `build_app`, así que importar la app de la API abre
  conexión a PostgreSQL — por eso el servicio no tenía tests de API.
- **F-009** (higiene de artefactos de cobertura) ha vuelto a aparecer sola:
  `init.sh` deja el árbol sucio y eso impide al reviewer usar la campaña de
  mutación paralela, que exige árbol limpio. Ver `review_F-002_fase1.md` §10.

## Nota de proceso

Los cuatro puntos que el reviewer pidió corregir (checkboxes de `tasks.md`,
este fichero y el estado en `features.json`) los ha hecho **el líder**, no el
implementer: `current.md` y `features.json` son suyos por protocolo y al
implementer se le había prohibido tocarlos para que no chocara con el
subagente que escribía la spec de F-003 en el mismo árbol. El rastro quedó
sin actualizar por ese motivo.
