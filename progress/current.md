<!-- progress/current.md -->
# Trabajo en curso

**F-045 en curso en esta rama** (`feature/F-045-excel-obras-postventa`, copia
principal): Excel desglosado en pestaña de obras y pestaña de postventa. El 2026-10-07 se desplegaron F-037, F-039 y F-040 por
la mañana, F-041 y F-042 (solo el front) por la tarde y F-047 (solo el transfer)
por la noche. El arnés es la **1.7.3**.

## F-045 · Excel desglosado: obras y postventa (en curso)

- **Qué es** (humano, 2026-10-07): la postventa en una pestaña propia con la
  línea agregada de obras de cada trabajador, y una pestaña de obras con la
  línea agregada de postventa; en cada una, el detalle de lo suyo.
- **Spec aprobada por el humano el 2026-10-08 con D1-D9 = A** («todo A»):
  todos los trabajadores en las dos pestañas; agregada «POSTVENTA / RESTO
  POSTVENTA» y «OBRAS / RESTO OBRAS» al final del grupo, en cursiva, solo si el
  trabajador tiene líneas de la otra parte; VAR en Obras; Total, Desviación y
  Estado del trabajador completo. Solo la api. Rigor estándar.
- **Primera implementación** (T1-T5, T7; `2017b20`..`39aae1f`): review 1
  CAMBIOS PEDIDOS solo por este fichero (MANUAL contra 2026/09 sin postventa),
  review 2 APROBADA (`progress/review_F-045.md`).
- **Cambio del humano en la MANUAL T6 (2026-10-08):** Obras y Postventa «está
  bien», pero el libro pasa a **«Obras», «Postventa» y «Detalle»** (la hoja de
  F-040 sin cambios, al final) y **«Resumen» desaparece** («si», avisado de que
  Juan pidió el Resumen en F-040). Spec revisada (`a135217`) y aprobada con
  D10 = A (se conserva `LineaDetalle.nombre`).
- **Estado:** cambio implementado (T8-T11, `24b2dae`..`020e7cd`,
  `progress/impl_F-045.md` §8): Detalle de F-040 tercera, Resumen fuera, 4
  tests del Resumen borrados (lista cerrada de design §7), 713 tests de la api
  en verde, mutación 14/14 muertos, init.sh en verde. **Review 3: CAMBIOS
  PEDIDOS solo en el rastro** (D10 seguía «abierta» en design.md; el recuento
  de octubre de la MANUAL); corregidos por el líder. MANUAL T6 cumplida.
- **Petición nueva del humano (2026-10-08):** «añade una columna de
  observaciones a la derecha de cada tabla». La app no guarda observaciones:
  el humano elige **A** («a»): columna «Observaciones» vacía, por línea, sin
  combinar, a la derecha de las tres hojas, ancha, con ajuste de texto y dentro
  del autofiltro. Spec ampliada (D11, R20-R21, T12-T16; 9 tests anteriores
  cambian, design §7.2) y **D12 = A** decidida por el humano el 2026-10-08
  («la celda va en todas, vacía»: también en la agregada y en «SIN CARGA»).
  **Estado:** ampliación implementada (T12-T15, `b7e3616`..`33b9011`,
  `progress/impl_F-045.md` §9): columna I vacía en las tres hojas, 715 tests
  de la api en verde, init.sh en verde, cobertura 38/38. Mutación inestable
  (3, 1 y 1 supervivientes distintos en tres campañas; todos mueren a mano):
  procesos ajenos importaban la copia durante la campaña; anotado en el
  encargo de `arnes-base` (`7c5983d`). **Review 4 lanzada.** Después, M2.
- **MANUAL M2 (humano, T16, en local, nada contra Azure):** la columna
  Observaciones.
  1. **Reiniciar la api local** (la arrancada a las 14:01 cargó un `exporter.py`
     mutado): Ctrl+C y `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-api`,
     `.venv/Scripts/python main.py` (8090).
  2. `curl.exe -o "$env:TEMP\f045.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"`
     y `start "$env:TEMP\f045.xlsx"`.
  3. En las tres hojas, la última columna es «Observaciones», cabecera azul y ancha.
  4. Texto largo en una celda de I de un grupo de varias filas: se ajusta, la
     fila crece y la celda es de una sola fila.
  5. Filtro de Observaciones → «(No vacías)»: solo esa fila. Quitar el filtro.
  6. Vista previa de impresión: una página de ancho, con I dentro y legible.
  Resultado: _pendiente_.
- **MANUAL T6 (humano, cumplida; libro Obras, Postventa y Detalle):**
  1. Api local: `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-api`
     y `.venv/Scripts/python main.py` (8090).
  2. En PowerShell: `curl.exe -o "$env:TEMP\f045.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"`
     y `start "$env:TEMP\f045.xlsx"`. Octubre es el mes de la base local con
     postventa: el Excel de la empresa 1 enseña 11 líneas de 8 trabajadores,
     1 de postventa (`Postv-0626`, de un trabajador que también tiene una
     obra). La base tiene 12, pero una es de otra empresa y no sale.
     Septiembre no tiene ninguna de postventa.
  3. Abre sin aviso de reparación, con las hojas Obras, Postventa y Detalle, en
     ese orden, y sin Resumen.
  4. En las tres hojas, filtrar un Empleado con obras y postventa: sale el
     grupo entero y la Suma de la columna E (barra de estado) da lo mismo.
  5. En Obras, Código = POSTVENTA; en Postventa, Código = OBRAS: solo salen las
     líneas agregadas.
  6. Estado distinto de OK: en octubre todos los que tienen líneas están OK,
     así que solo salen los «SIN CARGA», de una fila cada uno.
  7. Aspecto: bandas, línea gruesa entre trabajadores y la agregada en cursiva.
  8. «Detalle», como el de F-040: título «DETALLE DE DEDICACIÓN · Octubre
     2026», la postventa intercalada con `Postv-`, sin «RESTO …» ni cursiva.
  Resultado: **todo ok** (humano, 2026-10-08), con el libro nuevo.

## Producción, hoy

- **Desplegado el 2026-10-07 (noche): F-047**, solo el transfer
  (`r20261007-2029`): lecturas de hasta 200.000 filas, ya se registra en obras
  con más de 2.000 partidas. Comprobado por el líder (solo lectura): el
  transfer desplegado sigue en **modo real** (`OBRA_PRUEBAS_FORZAR=false`) y
  la línea de Bas Leal (`porcentajes:3599`) está en la **0696 real**, parte
  PT26/00298 (En registro), partida CI.1.8, con cuenta analítica. Las dos
  líneas de Bas Leal en la **0404** (`porcentajes:148` y `:149`, parte
  PT26/00344) son de la prueba LOCAL en modo pruebas (ids de la base local):
  **pendiente que el humano las borre**, como las de F-037.
- **Desplegado el 2026-10-07 (tarde): F-041 y F-042**, solo el front
  (`r20261007-1734`, revisión `Running` comprobada con `az containerapp show`):
  el filtro de obra casa con `Postv-` y la última fila abre el desplegable de
  obras. **Comprobación pendiente del humano** (Ctrl+F5): `pos` en «Filtrar
  obra…» y en `/`; en la última fila, Enter y escribir una obra (Esc dos veces).
  Al lanzarlo salió `The subscription of 'redactado-ver-copia-local' doesn't
  exist`: no se cargó `00_vars_dedicacion.local.ps1` y `az` siguió con la
  suscripción por defecto, que era la buena. Ver «Lo que espera al humano».
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
solo para ciertos usuarios). F-041 y F-042 desplegadas. F-047 desplegada. Nueva **F-048** (decir qué obra falló
al registrar). Orden: F-048, F-045, F-046, F-038 (cuadro de
mando), F-043, F-044, F-028, F-021, F-030, F-036, F-031, F-033 y, detrás,
F-017, F-018…

## ⚠ Lo que espera al humano

- **Cargar también la copia local de variables al desplegar.** El orden es
  `. .\00_vars_dedicacion.ps1`, `. .\00_vars_dedicacion.local.ps1` y
  `. .\00_capps_vars_dedicacion.ps1`. Si falta la local, `redeploy` sigue con
  la suscripción por defecto de `az` (el 2026-10-07 acertó por suerte).
  Propuesto al humano: que `redeploy` pare si `SUBSCRIPTION` está redactada.
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
