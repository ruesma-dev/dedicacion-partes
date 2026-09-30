<!-- progress/current.md -->
# Trabajo en curso

**F-022 con review APROBADA** (pasada 2, rigor crítico; `progress/review_F-022.md`).
T10 cumplida el 2026-09-30. No pasa a `done` hasta el commit del humano en `azure-apps`. El
arnés es la **1.7.3**; lo de su actualización está en `history.md`.

## F-022 · El transfer busca cada obra por código y empresa

- Rama `feature/F-022-transfer-obra-por-empresa`. Spec aprobada por el humano
  el 2026-09-29 (D1-D4; la D5 pasa a F-026). Implementer terminado
  (`progress/impl_F-022.md`); T1-T9 y T11 hechas, **T10 es MANUAL del humano**
  y está pendiente (abajo).
- **Para pasar a `done` falta solo el commit del humano en `azure-apps`.**
  T10 está cumplida (abajo) y la review está aprobada.
- **Al cerrar**: pasar a `history.md` la sección «Revisión de negocio del
  2026-09-29» (observación 3 de la pasada 2) y anotar ruff 185 → 193.
- Observaciones de la review 1, **recogidas**:
  - En los cortes R3/R11 `obra_destino` publica la obra de entrada con
    `empresa: null`. Queda como criterio en **F-024** (`features.json`).
  - Esta rama toca en `features.json` las entradas de F-018, F-023 y F-026.
    **Al mergear F-023 después**, resolver el conflicto de `features.json`
    fusionando las entradas, sin reescribir el fichero (ver «Hechos»).
  - Automejoras del arnés (C5 contra MANUAL; falsos supervivientes con
    caché previa): por decisión del humano van al **backlog de `arnes-base`**
    como `ENCARGO_pendiente_*.md` (commit `357522c` en `arnes-base`, sin
    push). No se tocan en este repositorio.

Detalle del implementer (desviaciones, todas aceptadas por la review 1):

- Desviación menor (orden, no alcance): `empresa=1` en las LÍNEAS de los
  dobles (`conftest.linea()`, `test_pipeline_offline.lineas_entrada()`) entra
  en el commit de T3 y no en el de T4. Con las reglas nuevas, una línea sin
  empresa se omite, y sin ese dato la suite quedaba en rojo (91 fallos) entre
  T3 y T4. Ningún assert cambia.
- T4: el doble de `conftest.py` conoce ahora la obra `0001` (constante
  `OBRA_SIN_PARTIDA_PV`). `test_f013_la_postventa_sin_partida_se_sigue_omitiendo`
  la usa como origen y, desde F-022, el origen se resuelve también en pruebas
  (R10; design §8, riesgo asumido). Es dato del doble; el test no cambia.
- T6: `RegistroSigrid` exige `empresa_imputacion` (design §4.8, sin valor
  por defecto), así que las tres construcciones de `test_f003_esquema.py`
  pasan `empresa_imputacion=1`. Solo el argumento; ningún assert cambia.
- **T8, desviación que decide el humano.** La copia
  `azure-apps/dedicacion.md` ya divergía del cuerpo de `docs/INTEGRACION.md`
  ANTES de F-022, en 4 bloques ajenos a esta feature: (1) §1, `ruesma_rep`
  «no es una réplica, es la base documental» — corrección hecha en la copia
  por `sigrid-api` (commit `a40684f` de azure-apps, 2026-09-05) que
  `INTEGRACION.md` no tiene; (2) §5, tarjeta del Portal y (3) «Quién puede
  entrar», redactados distinto desde la copia inicial (`08676ac`); (4) §6,
  filas de FQDN que la copia no lleva. Copiar el cuerpo entero habría
  BORRADO la corrección (1). Se hizo lo no destructivo: cabecera (commit
  `f9b3a46`, fecha 2026-09-29) y las tres piezas de F-022 copiadas LITERALES
  de `INTEGRACION.md` (fila `EMPRESA_IMPUTACION`, fila del transfer sin
  `SIGRID_EMPRESA`, párrafo §9). El `diff` del cuerpo ya no tiene ninguna
  diferencia de F-022, pero conserva esos 4 bloques. **Pendiente del humano**:
  revisar y hacer el commit en `azure-apps` (sin commit por el agente), y
  decidir si la corrección de `ruesma_rep` se porta a `INTEGRACION.md` (fuera
  del alcance de F-022).
- T9: campaña completa en serie (`--workers 1`: el fichero sin versionar
  `progress/explore_grafico_parte.md` impide la paralela y no es nuestro).
  Primera pasada (SHA `c4d9c3e`): 29 mutantes, 5 supervivientes; dos de
  ellos (`registro_pipeline.py:109` y `:116`) resultaron FALSOS: aplicados a
  mano en el árbol, los mata `test_f002_r11_modo_pruebas_destino_y_partida`.
  Esa pasada se DESCARTA. Se arreglaron los otros tres (mensaje de obra
  ambigua con el código pedido; test de los datos del script manual), se
  borraron `__pycache__`/`.pytest_cache` y se relanzó: **28/28 muertos, 0
  supervivientes** (SHA `dfe079d`, `progress/mutacion_F-022.md`).

## F-022 · verificación MANUAL pendiente (humano) — T10 / M1

Preflight real, **solo lectura**, con el transfer en modo pruebas (API 8090 y
transfer 8006 en local), sobre un periodo con al menos una línea de
postventa:

    curl -s -X POST http://127.0.0.1:8090/api/v1/periodos/AAAA/MM/registro/preflight -H "Content-Type: application/json" -H "X-Usuario: <usuario>" -d "{}"

Comprobar, en la obra con postventa: `obra_postventa.empresa == 1`,
`obra_destino.codigo == "0404"` y `obra_destino.empresa == 1`. **NO** se lanza
`registro/ejecutar`.

**Resultado real (2026-09-30, lanzado por el humano con
`t10_preflight_f022.ps1`, API y transfer de la rama F-022 en local, transfer
con `modo_pruebas=true`, `obra_pruebas=0404`, base `ruesma`): CUMPLIDA.**

- **2026-07, obra 0658:** línea de postventa con `obra_postventa` = `0404`
  empresa 1 (en modo pruebas la postventa también se desvía) y `obra_destino`
  = `0404` empresa 1. Es la única obra de julio cuya postventa casó con una
  partida de POSTV2.
- **2026-07, obras 0009 y 0025 (fichas de Porsan del maestro local):** sus
  líneas salen **omitidas** con «la obra … es de la empresa 28 y la línea se
  imputa a la empresa 1: no se escribe». Es R11 con datos reales. Antes de
  F-022 esas líneas iban contra la ficha de Porsan. Hasta que F-023 y F-024
  arreglen el maestro, **el usuario verá estas omisiones en el preflight**.
- **2026-08, obras 0455 y 0465:** POSTV2 se resuelve en la empresa 1 **sin
  ambigüedad** (se leen sus partidas), pero las obras no casan con ninguna
  partida («no casa con ninguna partida de POSTV2»). No es de F-022: es el
  universo de postventa de F-025.
- Primera ejecución de agosto: el script dio `OK` **sin haber comprobado
  nada**, porque ninguna línea tuvo destino de postventa. Se corrigió el
  script (ahora dice «NO CONCLUYENTE») y se repitió en julio.
- Hallazgo menor, anterior a F-022: el preflight publica
  `partidas_postventa` también en obras sin líneas de postventa (el catálogo
  `_nodos_pv` se queda en la instancia del pipeline entre llamadas).
  Inofensivo; pendiente de ficha.

## F-023 · spec aprobada, esperando turno

Rama `feature/F-023-sync-empresa-y-estado-recurso`: `spec_ready` **en su rama** (`988f79e`); en `dev` y aquí figura `pending` hasta que se mergee. Aprobada
por el humano el 2026-09-29 (decisiones en `features.json`). Espera porque
solo puede haber una feature en curso. **No se despliega sin F-024**
(D4: sin selector, una persona con fichas en dos empresas sale dos veces).
Antes de verificarla faltan dos datos del humano: el resultado de la consulta
Q1 (design §4, solo lectura), que dice qué estado de recurso es «inactivo», y
la lista de recursos inactivos que señaló negocio.

## Revisión de negocio del 2026-09-29: F-022 a F-031 entran al backlog

Negocio revisó la app en uso y salieron fallos y peticiones. Se dan de alta
en la rama `chore/backlog-f022-f031`, ya mergeada en `dev` (`01671a9`, sin push):

- **Fallos de maestros**, diagnosticados con evidencia en
  `progress/explore_maestros_sync.md` y `progress/explore_eusebio.md`:
  - F-022: el transfer busca la obra sin empresa. POSTV2 existe en las
    empresas 1 y 28. **Bloquea F-018.** (F-022 es la feature en review, arriba; F-018 sigue `pending`.)
  - F-023: el sync no lee la empresa y no usa el estado del recurso.
  - F-025: las obras de postventa están CERRADAS y el filtro de estado las
    quita.
  - F-026: el recurso de Eusebio Vindel Duro tiene vacío «Empleado
    asociado» (`res.conide`).
- **Peticiones**:
  - F-024: selector de empresa.
  - F-027: deshacer solo lo propio.
  - F-028: borrar lo que está en pantalla.
  - F-029: selección múltiple y completar hasta el 100 %.
  - F-030: dedicación por días, bajas e incidencias.
  - F-031: MCP para IA.
  - Se amplían F-020 (quitar la columna E del Excel) y F-021 (el filtro
    por obra marca a los asignados en Sesame).
- Las decisiones del humano de ese día están escritas en la descripción de
  cada entrada.
- **Pendiente de negocio:**
  - Si encargados y gruistas se dan de alta sin ficha de empleado a
    propósito (decide cómo se arregla F-026).
  - Objeción, si la hay, a que una obra cerrada se ofrezca solo como
    «Postv-» (F-025).
- **Por lanzar contra Sigrid (solo SELECT):** las tres consultas de
  `progress/explore_eusebio.md`, que confirman la causa de F-026.

## Lo siguiente, por prioridad

El backlog completo está en `BACKLOG.md` (29 features). Por orden:

| # | Feature | Qué es |
|---|---|---|
| — | **F-022** | en review (arriba) |
| 1 | **F-017** | probar con Administración sobre la obra de pruebas `0404` |
| 2 | **F-023** | sync de maestros con empresa y estado del recurso (spec aprobada) |
| 2 | **F-018** | pasar a escritura real. Requiere F-017 firmada, **F-022 y F-026** cerradas y autorización expresa |
| 3 | **F-025**, **F-026** | obras de postventa desde POSTV2; recursos sin ficha de empleado |
| 4 | **F-024**, **F-027**, F-020 | selector de empresa; deshacer solo lo propio; Excel |

## ⚠ Lo que espera al humano

1. **F-022**: T10 cumplida; falta solo el commit en `azure-apps` (punto 2).
2. **`azure-apps/dedicacion.md`**: revisar y hacer el commit; decidir si la
   corrección de `ruesma_rep` se lleva a `docs/INTEGRACION.md`.
3. **`git push origin dev`**: `dev` lleva 4 commits sin subir (el alta del
   backlog F-022-F-031 y la exploración del gráfico del parte, ya versionada).
4. **Datos para F-023 y F-026**: la consulta Q1 de F-023, la lista de
   recursos inactivos, las tres consultas de `progress/explore_eusebio.md`, y
   si encargados y gruistas se dan de alta sin ficha de empleado a propósito.
5. **F-014** y **F-016**, cuando quiera: aviso a Administración de las cuatro
   partidas duplicadas de POSTV2 y quién firma P4/P5; pedir a `sigrid-api`
   una clave de solo lectura para la api.

> **`azure-apps` no tiene remoto configurado** (`git remote -v` vacío): vive
> solo en local. No es de este proyecto, pero ahí está la documentación de todo
> el ecosistema y no está respaldada en ningún sitio.

## Lo que el sistema sabe hacer, comprobado

- **Corre en local y en Azure.** En local: transfer 8006 → api 8090 →
  front 8080, cada uno desde su carpeta con su venv (`README.md`).
- **Escribe en Sigrid de verdad**: crea el parte si no existe e inserta la
  línea con su `synckey` (T14). Ahora mismo **no tiene ninguna fila propia** en
  el ERP: la prueba se limpió.
- **Avisa y espera confirmación** en tres casos, cada uno con su clave: pisar
  una línea existente, pasarse del 100 % de un trabajador (F-002) y escribir
  sin partida casada (F-013).
- **El transfer sigue en modo pruebas.** El motivo real está en
  `docs/ARCHITECTURE.md`: **la imputación a partidas en producción no está
  validada**. Salir de ahí exige autorización expresa para una acción concreta.

## Lo que NO está verificado, y consta

- **R34**: el `/health` del transfer con `modo_pruebas` y `database` no se ha
  comprobado en caliente — su ingress es interno y no es alcanzable desde
  fuera, que es lo que la decisión D2 buscaba.
- **T29**: la prueba funcional de extremo a extremo se apoya en la
  confirmación del humano, **sin volcado**.
- **La Regla B nunca se ha ejercitado contra Sigrid real** (F-014).

## Hechos que no conviene volver a descubrir

- El api expone su salud en **`/api/v1/health`**, no en `/health`. El front,
  con Easy Auth, responde **401** a un `curl` anónimo, y el Portal **302**:
  no son caídas.
- `ruff` **no está instalado** en el venv de `dedicacion-api`.
- **Dos defectos del arnés**, anotados para `arnes-base`: `init.sh` confunde
  «no hay tests» (pytest código 5) con «los tests fallan» —desde la 1.7.2 es
  defecto CONOCIDO con ficha (F-041 en `albaranes`), aún sin arreglar—, y **la
  caché de suites cruza ramas**, que sigue sin ficha.
- **Los scripts de `infra/` solo se prueban ejecutándolos contra Azure**: cinco
  bugs salieron así, ninguno lo habría cazado un test offline.
- **Un fichero de rastro puede contener información única.** Resolver su
  conflicto de merge reescribiéndolo la destruye en silencio: pasó con el
  volcado de T13 y se recuperó del historial.
