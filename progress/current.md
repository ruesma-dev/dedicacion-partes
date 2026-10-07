<!-- progress/current.md -->
# Trabajo en curso

**F-042 en curso en esta rama** (`feature/F-042-ultima-fila-autocompletado`,
copia principal): la última fila del cuadrante no enseña el desplegable de
obras. F-041 está cerrada en `dev` y **pendiente de desplegar** (solo el front,
sección de despliegue). F-037, F-039 y F-040 se desplegaron el 2026-10-07. El
arnés es la **1.7.3**.

## F-042 · El desplegable de obras en la última fila (en curso)

- **Causa** (líder, solo lectura): el panel `.sugerencias` es `position:
  absolute` dentro de la tabla, y `.panel { overflow: hidden }` /
  `.panel-tabla { overflow-x: auto }` lo recortan. En las filas intermedias cae
  sobre las de abajo; en la última no hay nada debajo y no se ve (sí busca).
- **Plan A aprobado por el humano el 2026-10-07** («la A»): `sdd: false`, rigor
  estándar, solo front (`static/js/app.js` y `static/css/styles.css`). El panel
  se coloca respecto a la ventana (`position: fixed`) bajo el campo, se abre
  hacia arriba si no cabe, se recoloca con scroll y resize, y se retira al
  cerrar el editor. Sin cambios de teclado ni de búsqueda. Descartada la B.
- **Estado:** implementada (T1-T4, `12272a9`..`cca97a5`), `init.sh` en verde;
  informe en `progress/impl_F-042.md`, mutación manual en
  `progress/mutacion_manual_F-042.md` (38 mutantes, 37 muertos, 1 equivalente).
  El panel cuelga de `document.body` y, si no cabe por ningún lado, va al lado
  con más sitio y recorta su alto. `dev` traído a la rama (F-045 y F-046 en el
  backlog). **Review lanzada.** Después, la MANUAL del humano.
- **MANUAL (humano, en local, nada contra Azure):**
  1. Api local: `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-api`
     y `.venv/Scripts/python main.py` (8090).
  2. Front de esta rama: `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-front`
     y `.venv/Scripts/python main.py` (8080).
  3. `http://127.0.0.1:8080`, **Ctrl+F5**, un periodo abierto.
  4. Última fila de la tabla: Enter, `%`, Enter, escribir parte de una obra →
     sale el desplegable, flechas y Enter eligen. Esc sin guardar.
  5. Lo mismo con un filtro que deje **una sola fila**, y con la ventana
     pequeña (el desplegable se abre hacia arriba si no cabe).
  6. Una fila intermedia: igual que antes.
  7. Con el desplegable abierto, hacer scroll de la página: acompaña al campo
     o se cierra, pero no se queda flotando en otro sitio.
  Resultado: _pendiente_.

## ⚠ Despliegue de F-041 (pendiente; lo lanza el humano)

- Cambia **solo el front** (`.\redeploy_dedicacion.ps1 -Solo front`, desde
  `dev`). Sin DDL ni sync.
- **Comprobación:** Ctrl+F5 y escribir `pos` en «Filtrar obra…» y en el
  buscador global (`/`): salen los trabajadores con líneas `Postv-`.

## Producción, hoy

- **Desplegado el 2026-10-07: F-037, F-039 y F-040** (transfer
  `r20261007-0851`, api `r20261007-0852`, front `r20261007-0853`, en orden
  transfer → api → front). Desde ya, cada línea registrada lleva la cuenta
  analítica de la obra (F-037), las partidas de VAR desde la 29 se ofrecen
  como `VAR-NN` y se ignoran las obras con 6+ dígitos (F-039, **tras el
  sync**), y el Excel sale como el modelo de Juan (F-040). **Pendiente de
  confirmar por el humano:** sync («Actualizar Sigrid») y preview con
  `excluidas_por_codigo` 240 y `entradas_var` 1; un Excel de producción.
- **Desplegado el 2026-10-06: F-029** (api `r20261006-1140`, front
  `r20261006-1141`): selección múltiple con Ctrl/Shift y «Completar al
  100 %» (tecla C). **Comprobación pendiente:** un trabajador en FALTA,
  Ctrl+clic, C, confirmar la obra → 100 %; Ctrl+Z lo devuelve.
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

## F-028 · Borrar lo filtrado (plan aprobado, va después de F-037)

- Plan aprobado por el humano el 2026-10-06 con **A** (siempre todo lo
  visible). Detalle en la descripción de `features.json`.

## Recursos cerrados en bloque en Sigrid (2026-10-05)

- Correo de Miguel Ángel: recursos que salen en agosto y no en septiembre.
  Causa comprobada en Sigrid: el 2026-08-06 se cerraron en bloque 46 fichas
  de recurso de personas que se fueron en 2024-2025; por la regla de F-026
  cuentan en agosto. **Decisión del humano: opción B** (que Administración
  corrija la fecha de baja en Sigrid) y **spec de la A** como F-036, sin
  implementar de momento.

## Lo siguiente, por prioridad

`BACKLOG.md` tiene el orden completo. Nuevas el 2026-10-07 (pedidas por el
humano): **F-042** (fallo: la última fila no abre el autocompletado de obras),
**F-043** (partida del modal de registro con predictivo, ordenada y selector
CI/CD como en `partes`) y **F-044** (repartir también los recursos vinculados
al trabajador: teléfono, vehículo, gasoil…), **F-045** (Excel desglosado:
pestaña de obras con la postventa en una línea agregada y pestaña de
postventa con las obras agregadas) y **F-046** (cerrar y reabrir el periodo
solo para ciertos usuarios). Orden: F-042, F-045, F-046, F-038 (cuadro de
mando), F-043, F-044, F-028, F-021, F-030, F-036, F-031, F-033 y, detrás,
F-017, F-018… F-041 está cerrada y pendiente de desplegar (solo el front).

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

7. **F-037, complementario en real (aplazado por el humano el 2026-10-06):**
   probar con Administración que, con el parte del mes contabilizado, una
   línea nueva va a un complementario `Parte <obra>`. Los tests lo cubren;
   en Sigrid no se ha visto.
8. **F-037, aviso a `partes` (T11):** ya recogieron la carrera (D17, su
   `9ea7c59`); falta pasarles el test de inmutabilidad de `OrigenSubcuenta`.
   Su DA11 pondrá en rojo `test_f037_copias_partes.py::…ref_vigilada`:
   recopiar y mover `COMMIT_COPIADO`.
9. Decidir si se abre como feature lo que vio el implementer de F-037: la
   capacidad no se evalúa en un periodo sin ningún parte (dos líneas nuevas
   del mismo recurso que sumen más del 100 % no avisan). Preexistente.

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
