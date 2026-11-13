# Informe · chore/arnes-1.10.1 (actualización del arnés 1.7.3 → 1.10.1)

Fecha: 2026-11-13. Rama `chore/arnes-1.10.1` (sale de `dev`). Tarea de
mantenimiento del arnés, sin feature F-XXX ni spec; plan aprobado por el humano
antes de lanzar. El instalador (`instalar_arnes.ps1 -Modo actualizar`) ya
había aplicado lo `arnes_puro` y 70 ficheros nuevos; aquí se fusionan a mano los
seis `adaptado` y se deja `init.sh` en verde.

Fuente de cada fusión: `arnes-base/arnes-base/<mismo path>` (payload 1.10.1) y
`GUIA_INSTALACION.md`, secciones «Qué hacer al actualizar» de la 1.7.4 a la
1.10.1.

## Qué se fusionó, fichero a fichero

### `CLAUDE.md`
Aceptado del arnés (edición por bloques sobre el nuestro):
- `qa-e2e` en los subagentes autorizados; la frase de la primera parada
  (resumen de la spec o PARADA 1 sin spec).
- «Ritmo de trabajo»: paradas con las plantillas de `leader.md`; la segunda
  parada dice qué queda listo para el push del humano y termina con «Tu OK es
  el permiso para integrar y desplegar; el arnés nunca despliega.»
- Protocolo: orden `blocked > human_review > in_review > in_progress >
  spec_ready > todo`, `pending` no se arranca sin compromiso, máximo una
  feature activa (`in_progress`, `in_review`, `human_review`).
- Regla «tal cual» con su segunda forma `ARNES_SIN_CACHE=1 bash harness/init.sh`.
- Ramas: «allí solo llegan merges (ver `leader.md`, «Commits, merges y push»)».
- Regla dura del push: los agentes nunca hacen push; commits y merges sí (el
  de `main` preguntando antes); PRs solo con petición explícita. Sustituye a
  nuestra «NO hacen push ni PRs; commits locales sí».
- Bloque Ruesma: protocolo del repositorio del ecosistema `azure-apps`
  (F-070: `pull --rebase`, solo el documento propio, commit aparte, push del
  humano, conflicto → `blocked`) y cuentas de GitHub `ruesma-dev`.

Conservado de lo nuestro: título del monorepo, mapa de los tres servicios,
«Documentos que llegan de fuera» con la regla de leer PDF sin `markitdown`,
reglas duras de Sigrid (solo lectura salvo transfer, base `ruesma`, modo real
desplegado / obra `0404` en local), BBDD `dedicacion` local vs compartida,
LÍMITE DE SERVICIO monorepo con la lista cerrada de duplicaciones toleradas,
front sin lógica de negocio. No se aceptaron los `[ADAPTAR]` genéricos ni el
«LÍMITE DE MICROSERVICIO» (no aplica a un monorepo).

### `CHECKPOINTS.md`
Base: el del payload completo (todo el texto nuevo es genérico): C1 con
`ARNES_SIN_CACHE=1` (F-028), tabla de niveles con `express` y C3 ter, capa
`rigor.local.json`, criterio para declarar `critico`, recorrido de `express`,
comandos con `harness.e2e`, orden de fases en `in_review`, C2 con feature
activa y orden de prioridad, C3 ter, C3 quater, dobles de test en C4, C4 bis
(«Dos pasadas», puertas informativas, ruptura deliberada al subir de carril,
mutación con regla del nivel, muerte solo con código 1 e `indeterminado`,
casilla «reproducir a mano», RM2 con selección de tests, PODADO, capa e2e).

Conservado de lo nuestro: el punto de C3 con las tres trampas de dominio
(escala del porcentaje 0-100 / sobre 1, postventa con `es_postventa` en la
clave, solo escribe el transfer en `ruesma` con `synckey`, modo pruebas e
`ide` con `MAX(ide)+1`). Sustituye al `[ADAPTAR]` del payload. No queda
ninguna marca `[ADAPTAR]`.

### `harness/init.sh`
Base: el del payload completo (secciones 3 con los ocho estados en los cuatro
validadores, 3 ter avisos de estado con `harness/estados.py`, 3b aviso CAPA
LOCAL DE RIGOR, venv del proyecto antepuesto al PATH, 7 bis caché por
`harness.cache_suites` con `SIN_CACHE` y líneas `SIEMPRE|`, cobertura
informativa, 7 quinquies puerta de carril, 7 sexies capa e2e, comentario
nuevo de `RAMA_BASE`).

Reaplicado de lo nuestro (lo único que difiere del payload, comprobado con
`diff`): cabecera «adaptada al monorepo porcentajes», `REQUIERE_ENV=0` (los
`.env` viven en cada servicio), `COMPROBACIONES_EXTRA=1` y la sección 9 entera
(ningún `.env` versionado, `config.yaml` de la api parseable, `.env.example`
en los tres servicios). `RAMA_BASE=dev` coincide con el payload. La caché vieja
por hash de árbol del servicio se sustituye por la del arnés (era nuestra
versión previa de la misma idea). `bash -n` sin errores.

### `docs/CONVENTIONS.md`
Aceptada solo la sección «Git» (quién hace cada merge y el push, F-070).
Conservado todo lo nuestro: Python, JS de `dedicacion-front`, SQL con YAML /
ORM / `esquema.py`, dobles con forma serializada real.

### `.claude/settings.json`
Base: el del payload (`model: claude-opus-5-5`, `effortLevel: high`,
`$adaptar` nuevo, permisos nuevos: `ARNES_SIN_CACHE=1 bash harness/init.sh`,
`harness.alcance|cobertura|mutacion|rigor|servicios|tamano`,
`harness/backlog.py`, `git checkout -b`). **Quitado el hook `PostToolUse`**
(`| tail -5` escondía el código de salida). Se conservan los hooks
`SessionStart`/`SessionEnd` (`despierto_hook.sh`) y `Stop`, idénticos en
ambos. La `$nota` de monorepo se reescribe: ya no habla del hook quitado y
deja constancia de por qué se quitó. No había permisos propios que conservar
(los nuestros son un subconjunto de los del payload).

### `docs/referencia/README.md`
Sin cambios: el diff solo trae el índice `[ADAPTAR]` genérico y ningún test
de guarda lo exige.

### `harness/features.json` (solo documental)
La guía (sección de F-042) dice que `rules.valid_status` y `$schema_doc` se
quedan viejos y que, si se quiere, se copian de la plantilla. Copiados
`$schema_doc`, `$rigor_doc` y `rules.valid_status` (ocho estados). **No se ha
cambiado el estado de ninguna feature.**

### `BACKLOG.md`
Regenerado por el primer `bash harness/init.sh` (orden de secciones de F-070).
Incluido en el commit.

## Un rojo fuera de la fusión, resuelto según la guía

El primer `bash harness/init.sh` dio un único [KO] en la suite de la raíz:

```
FAILED tests/test_f019_tiempos.py::test_f019_r22_ningun_test_lanza_subprocesos_con_timeout_literal
AssertionError: timeouts fijos sin escalar_timeout (R22 de F-019): ...
{'test_f008_infra_sin_secretos.py': ['línea 160: subprocess.run(timeout=30)']}
1 failed, 689 passed, 1 skipped in 610.92s (0:10:10)
```

No es un test que fije comportamiento viejo ni un fallo del payload: es un
test propio que lanza `git ls-files` con un timeout literal. La guía
(«Qué puede ponerse en rojo», 1.10.0, y la 1.10.1, R7) prescribe el arreglo
exacto: «se arreglan pasándolos por `harness.tiempos.escalar_timeout`».
Cambio en `tests/test_f008_infra_sin_secretos.py`: import de
`harness.tiempos.escalar_timeout` y `timeout=escalar_timeout(30)`. Con él,
`tests/test_f008_infra_sin_secretos.py` + `tests/test_f019_tiempos.py`:
105 passed. Suite de la raíz completa sin `-x`: **2319 passed, 47 skipped
in 1031.37s**.

## Resultado real de `bash harness/init.sh` (final)

Tras `rm -f .arnes_cache/suite_*.ok` (sin caché), ejecutado tal cual. Exit 0,
**ningún [KO]**, «ENTORNO LISTO. Puedes trabajar.»

| Sección | Resultado |
|---|---|
| Versión | Arnés v1.10.1 (2026-11-12); Python 3.12.7 |
| features.json | válido; 70 features, 29 abiertas, activa: ninguna, bloqueadas: ninguna |
| BACKLOG.md | al día |
| rigor.json | válido; niveles critico, documental, estandar, express; por defecto estandar; umbral 80 %, critico 90 % |
| compileall | sin errores |
| ruff | [AVISO] 324 avisos (deuda previa, no bloquea) |
| Suite raíz | 2319 passed, 47 skipped in 871.18s (con cobertura) |
| servicio api | 1339 passed, 1 warning in 102.97s |
| servicio front | 473 passed, 19 warnings in 82.88s |
| servicio transfer | 1737 passed, 2 warnings in 32.65s |
| Cobertura / carril / e2e | N/A (la rama no corresponde a ninguna feature) |
| Tamaño | [AVISO] N/A (no hay papeleo abierto) |
| Sección 9 | ningún `.env` versionado; `config.yaml` válido; tres `.env.example` |
| Rama | chore/arnes-1.10.1 |

## Qué no se tocó

`.env`, `progress/current.md`, `progress/history.md`, `harness/rigor.json`
(va tal cual el publicado; no se crea `rigor.local.json`), las copias
`porcentajes-f054` y `porcentajes-f069`. Sin merge a `dev`, sin push.

## Para el líder / el humano

- La duplicación de `test_f008_infra_sin_secretos.py` no existe en
  `arnes-base` (es test propio): no hay nada que portar.
- `azure-apps`: nada que actualizar (no cambia lo que el proyecto expone ni
  consume).
- Pendiente del humano: revisar el commit, merge a `dev` y push.
