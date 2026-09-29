<!-- progress/current.md -->
# Trabajo en curso

**F-022 en ejecución** (implementer lanzado, rigor crítico). El arnés es la
**1.7.3**.

## F-022 · implementer en marcha

- Rama `feature/F-022-transfer-obra-por-empresa`. Implementer TERMINADO (informe `progress/impl_F-022.md`); pendiente: T10 MANUAL del humano (abajo), review.
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
`registro/ejecutar`. Resultado real: _pendiente, a anotar aquí_.

> **2026-09-29: el humano aprueba las specs de F-022 y F-023.** F-022 pasa
> a **`in_progress`** en `feature/F-022-transfer-obra-por-empresa`. F-023 sigue en `spec_ready` en su rama, ya
> aprobada, esperando turno porque solo puede haber una feature en curso.
> Las decisiones quedan escritas en la descripción de cada feature; la D5 de
> F-022 pasa a F-026. Antes de verificar F-023 faltan dos cosas: el
> resultado de la consulta Q1 (design §4), que dice qué estado de recurso
> cuenta como inactivo, y la lista de recursos inactivos que señaló negocio.
> T10 de F-022 es una verificación MANUAL del humano: un preflight real de
> solo lectura, cuyo resultado se anota aquí.

## Revisión de negocio del 2026-09-29: F-022 a F-031 entran al backlog

Negocio revisó la app en uso y salieron fallos y peticiones. Se dan de alta
en la rama `chore/backlog-f022-f031` (commit local, sin merge ni push):

- **Fallos de maestros**, diagnosticados con evidencia en
  `progress/explore_maestros_sync.md` y `progress/explore_eusebio.md`:
  - F-022: el transfer busca la obra sin empresa. POSTV2 existe en las
    empresas 1 y 28. **Bloquea F-018.**
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

## Arnés actualizado a 1.7.3 (2026-08-22)

De **1.5.2** a **1.7.2** y, con el correctivo de abajo, a la **1.7.3** que
nació aquí. Todo en la rama `chore/arnes-1.7.2`. El instalador aplicó
lo genérico (agentes, `harness/*.py`, `rigor.json`, `SPECS.md`, 15 tests
nuevos) y conservó los seis ficheros adaptados; `CHECKPOINTS.md` y
`harness/init.sh` se fusionaron a mano para quedarse con las mejoras genéricas
sin perder lo del monorepo. Portero en verde: **354 tests, 1 skipped**.

Lo que cambia para trabajar aquí:

- **Puerta nueva de tamaño del papeleo** (`init.sh` sección 7 quater, topes en
  el bloque `tamano` de `harness/rigor.json`): requirements 150, design 250,
  `impl_F-XXX.md` 220, `review_F-XXX.md` 140 líneas. Mide **solo la feature en
  curso**: lo viejo queda amnistiado, lo que se retome y edite pasará a
  medirse. Pasarse pone el portero en **rojo**.
- **`nivel_por_defecto` pasa de `critico` a `estandar`.** No afecta hoy: las 14
  features declaran su `rigor` explícitamente. A partir de ahora, `critico` se
  declara, no se hereda.
- **Campañas `estandar` muestreadas a 20 mutantes** con semilla fija; sus
  números **no** son comparables con los de campañas anteriores. Campaña
  entera: `--max-mutantes 0`.
- **El reviewer reejecuta la campaña por debajo de 60 segundos** (antes 5
  minutos) y revisa **incremental** desde el último SHA aprobado, declarándolo
  en la primera línea de su informe. Reglas **RM1–RM6** en `CHECKPOINTS.md` C4
  bis y en `.claude/agents/reviewer.md`.
- **Timeout y workers de mutación se calculan solos**: el timeout se deriva de
  la línea base medida (`timeout_por_mutante_s` es ahora un **suelo**) y los
  workers por defecto bajan a `min(max(1,(núcleos-2)//2),4)`.
- **Códigos de salida nuevos de `harness.mutacion`**: `2` alcance vacío, `3`
  cero mutantes generados (sin informe). Un guion que encadene campañas debe
  tratarlos como fallo.
- **Uno de los dos defectos del arnés que anotamos ya tiene ficha**: pytest
  código 5 («ningún test recogido») contado como verde es el defecto CONOCIDO
  que la 1.7.2 declara **sin arreglar** (F-041 en `albaranes`, rigor
  `critico`). Mientras viva, una campaña de una sola pasada no vale como
  evidencia: contrástala con otra (`--workers 1`). El segundo —la caché de
  suites cruza ramas— sigue sin ficha.
- **Defecto de la 1.7.2 encontrado y corregido aquí**: la puerta de tamaño
  medía también las features `done`, y F-015 declara `branch: "dev"` (se hizo
  en la rama base), así que su review de 546 líneas dejaba `dev` en **rojo
  permanente**. La sección 7 quater descarta ahora el papeleo cerrado, con test
  en `tests/test_tamano.py`. **Portado a `arnes-base` como 1.7.3** por la regla
  de propagación, y reinstalado desde ahí: este repo lleva ya la 1.7.3. El
  commit de `arnes-base` (`a695c32`) está **pusheado** a
  `ruesma-dev/harness-ruesma`.
- `ruff` pasa de 179 a 185 avisos: los seis nuevos son del código del arnés que
  acaba de entrar. Deuda previa, no bloquea.

El sistema está **desplegado y en uso**: se entra por la tarjeta «Dedicación»
del Portal Ruesma y hay 8 personas con acceso.

## Estado del backlog (16 features)

| Estado | Features |
|---|---|
| `done` | F-001, F-002, F-003, F-004, **F-008**, F-009, F-013, F-015 |
| `pending` | **F-017**, **F-018**, F-005, F-006, F-011, F-012, F-014, F-016 |

**F-017 y F-018, añadidas el 2026-08-25 por el humano**, marcan el camino que
falta: que Administración valide contra la obra `0404` lo que el sistema
escribe (F-017) y, solo con esa firma y con autorización expresa para esa
acción concreta, salir del modo pruebas (F-018). Comprobado en caliente ese
día: el transfer desplegado sigue con `OBRA_PRUEBAS_FORZAR=true`,
`OBRA_PRUEBAS_COD=0404` y `MARCA_PRUEBAS=PRUEBA-PORC`.

Retiradas el 2026-08-20 por decisión del humano: **F-007** y **F-010**, que se
hacen en `arnes-base`. Su razonamiento sigue en `progress/history.md`.

## Lo siguiente, por prioridad

| # | Feature | Qué es |
|---|---|---|
| 1 | **F-017** | probar con Administración sobre la obra de pruebas `0404` |
| 2 | **F-018** | pasar a escritura real, solo si F-017 se firma |
| 5 | **F-005** | alinear los literales internos con el nombre «dedicación» |
| 6 | **F-006** | sanear la suite del transfer (un test que devuelve en vez de asertar) |
| 7 | **F-011** | que un trabajador no pueda tener dos códigos `M*` |
| 8 | **F-012** | el test de la épsilon compartida ata el transfer al monorepo |
| 9 | **F-016** | pedir a `sigrid-api` una function key de **solo lectura** para la api |
| 20 | **F-014** | los cabos de Sigrid y Administración |

## ⚠ Lo que espera al humano

1. **`git push origin dev`**: hay commits locales sin subir.
2. **F-014**, cuando quiera: avisar a Administración de las cuatro partidas
   duplicadas de POSTV2 (`656`, `664`, `680`, `693`), decidir quién firma la
   procedencia de las reglas P4/P5, y **mirar el primer preflight real que
   tenga líneas `M*` previas** — es la única forma de ver la Regla B
   (sobrecarga del 100 %) ejercitada contra datos de verdad.
3. **F-016**: preguntar al dueño de `sigrid-api` si puede emitir una clave de
   solo lectura. Hoy api y transfer comparten la misma, y lo único que impide
   que la api escriba en el ERP es que su código no tiene rutas de escritura.

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
