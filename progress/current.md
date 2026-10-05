<!-- progress/current.md -->
# Trabajo en curso

**F-029 en curso** (selección múltiple y completar hasta el 100 %, rigor
estándar, `sdd: true`), rama `feature/F-029-seleccion-multiple-completar-100`.
F-027 se cerró el 2026-10-04 y se **desplegó el 2026-10-05**; F-025 se desplegó el 2026-10-03 (resúmenes en
`history.md`). El arnés es la **1.7.3**.

## F-029 · Selección múltiple y completar hasta el 100 % (en curso)

- **Elegida por el humano el 2026-10-05** por delante de F-021, de la que
  dependía. La spec trabaja con el filtro de obra que YA existe en el front;
  la selección automática desde Sesame sigue siendo de F-021.
- **Estado:** spec entregada (`631273c`, `specs/F-029-seleccion-multiple-completar-100/`):
  api `POST /periodos/{a}/{m}/completar` por lote (un evento `COMPLETAR`
  deshacible por trabajador) + front con Ctrl/Shift, diálogo y botón. Lista
  cerrada de tests anteriores que cambian: **ninguno** (comprobado con un
  prototipo desechable). **Aprobada por el humano el 2026-10-05 con D1-D6 =
  A**, cerradas en todos sus sitios (`8d5172d`).
- **Implementación terminada** (`progress/impl_F-029.md`): T1-T6, T8, T10
  (`b09e333`…). Cobertura 84/84; mutación en serie 20/20 muertos tras matar
  dos `frozen` con un test (`progress/mutacion_F-029.md`); un falso
  superviviente en serie → encargo de `arnes-base` (`58403df`). Ningún test
  anterior cambiado. **Review 1: CAMBIOS PEDIDOS solo por el rastro** (T7
  sin marcar en `tasks.md` y «Lo siguiente» desfasado), corregidos por el
  líder; código, tests, mutación y docs revisados y bien. **Review 2:
  APROBADO.** Para el `done` solo falta la T9 del humano; la rama NO se
  mergea a `dev` hasta entonces (puede traer ajustes de usabilidad).
- **Condición del humano: NO se despliega hasta que pruebe la usabilidad en
  local** (T9, `tasks.md`: api y front locales desde la rama, BBDD local, sin
  Sigrid; clics, diálogo, tecla C, Ctrl+Z y regresión del teclado).
- **T7 (líder): hecha**, párrafo de §5 copiado literal a
  `azure-apps/dedicacion.md`, commit `a593bd4` («sin desplegar»).
- **T9 MANUAL (humano), pendiente:** pasos (a)-(e) en `tasks.md` T9 y
  arranque en `progress/impl_F-029.md` § «Cómo probarlo en local»: en Git
  Bash, `cd services/dedicacion-api && .venv/Scripts/python main.py` y, en
  otra, `cd services/dedicacion-front && .venv/Scripts/python main.py`;
  abrir `http://localhost:8080`. NO pulsar «Registrar en Sigrid».
  Mirar además (observación de la review 1): Ctrl/Shift+clic con el editor
  abierto repinta la tabla y el foco puede saltar. Resultado: _pendiente_.

## Producción, hoy

- **Desplegado el 2026-10-05: F-027** (solo la api, `r20261005-0915`): cada
  usuario solo deshace lo suyo. **Comprobación pendiente, con dos personas
  (A y B) en el mismo mes y trabajador:** A guarda → B no ve el botón y su
  Ctrl+Z enseña «La última modificación de este trabajador es de A…»; A
  deshace bien; si B guarda después de A, A ya no puede.
- **Desplegado el 2026-10-03: F-025** (transfer `r20261003-1444`, api
  `r20261003-1446`, front `r20261003-1447`, en orden transfer → api → front).
  Preview de producción: `admiten_postventa` 83, `solo_postventa` 73,
  `motivo_postventa` nulo. **Sync hecho y `Postv-0656` visible en el
  cuadrante** (confirmado por el humano el 2026-10-05): ya se puede
  registrar postventa con normalidad.
- **Desplegado el 2026-10-02: F-034 y F-026**, sobre lo del 2026-10-01 (F-022,
  F-023, F-024, F-032). Imágenes `transfer:r20261002-1705`,
  `api:r20261002-1706`, `front:r20261002-1708`; la api añadió
  `trabajador.fecha_baja` al arrancar. **Datos de prueba vaciados** (312
  asignaciones, 376 eventos, 7 periodos, 207 trabajadores → 0) y **sync
  hecho**: 196 trabajadores (183 / 8 / 4 / 1 en las empresas 1 / 18 / 31 /
  25), ventana de bajas desde el 2026-09-01, 38 empresas. **Eusebio Vindel
  Duro aparece** (confirmado por el humano).
- **El transfer desplegado escribe DE VERDAD** (`OBRA_PRUEBAS_FORZAR=false`)
  por orden expresa del humano (`docs/INTEGRACION.md` §8). Siguen abiertos
  F-017 (partidas sin validar por Administración) y F-011 (varios códigos M*).
- **El script de vaciado ya funciona contra Azure** (F-035, 2026-10-03): usa
  `psql` y lee la contraseña de `PG-PASSWORD` del Key Vault. `-SoloRecuento`
  cuenta sin escribir: el 2026-10-03 dio 0 asignaciones, 0 eventos, 1
  periodo y 196 trabajadores.

## Lo siguiente, por prioridad

`BACKLOG.md` tiene el orden completo (reordenado por el humano el
2026-10-05: F-028, F-021, F-029 y F-030 delante de F-020). Ahora, **F-029**
(en curso, sección de arriba, adelantada por el humano). Después de F-029:
**F-028**, F-021, F-030, F-020, F-031, F-033 y, detrás, F-017, F-018…

## ⚠ Lo que espera al humano

1. Decidir si se abren como features las dos observaciones de F-026: la fila
   de guardar/deshacer no conoce el mes, y el front no enseña `no_vigentes`.
2. **Correcciones de la review del despliegue del 2026-10-01**
   (`progress/review_despliegue_20261001.md`: digests de `imagenes.json`,
   textos de scripts que aún dicen «modo pruebas», F-017/F-018) y si **F-017**
   se hace en real con Administración delante. Plan propuesto, **sin
   respuesta**.
3. **`git push`** de `dev` en `porcentajes` y de `main` en `arnes-base`.
4. Decidir si la corrección de `ruesma_rep` de `azure-apps/dedicacion.md` se
   lleva a `docs/INTEGRACION.md`.
5. **F-014** y **F-016**, cuando quiera.
6. Decidir si se abre una feature para que `crear_base_dedicacion.ps1` pida
   las contraseñas antes de sus pasos 1-2 (observación del implementer de
   F-035): hoy, una contraseña rechazada llega después de comprobar el
   servidor y, si faltaba, crear la regla de servicios de Azure.

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
- **El transfer desplegado escribe DE VERDAD desde el 2026-10-01**, por
  decisión expresa del humano (`docs/INTEGRACION.md` §8, con el comando para
  volver a pruebas). Sigue sin validar la imputación a partidas en producción
  (`docs/ARCHITECTURE.md`, F-017).

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
