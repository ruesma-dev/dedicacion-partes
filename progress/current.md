<!-- progress/current.md -->
# Trabajo en curso

**F-041 en curso en esta rama** (filtro de obra con el texto visible, `Postv-`),
rama `feature/F-041-filtro-obra-postventa`, en la copia
`PycharmProjects/porcentajes-f041`. En la copia principal no hay ninguna feature
en ejecución: F-037, F-039 y F-040 se **desplegaron el 2026-10-07** (sección
«Producción, hoy»). El arnés es la **1.7.3**.

## F-041 · Filtro de obra con el texto visible (en curso)

- **Qué es** (pedida el 2026-10-06): el filtro de obra, el buscador global y las
  candidatas de «Completar al 100 %» casan con el texto tal como sale en el
  chip (`Postv-…`), por línea y sin mayúsculas ni tildes. Causa real: el
  buscador global no casaba con `Postv-` y la columna mezclaba chips. Spec
  `specs/F-041-filtro-obra-postventa/`, aprobada con D1-D4 = A (`9b5fc46`).
- **Implementación terminada** (`progress/impl_F-041.md`, `a448ffc`…`e57675f`):
  solo front; ningún test anterior cambiado; la herramienta de mutación no muta
  JavaScript → campaña manual de 20 mutantes, 0 supervivientes
  (`progress/mutacion_manual_F-041.md`). **Review 1: CAMBIOS PEDIDOS solo por
  este fichero** (MANUAL incompleta y restos caducados), corregidos por el líder
  trayendo `dev` a la rama; código, tests y campaña sin objeciones hasta
  `d2bc7f9`. **Review 2 lanzada.**
- **MANUAL (humano, T6, en local, nada contra Azure):**
  1. Api local de siempre: `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-api`
     y `.venv/Scripts/python main.py` (8090).
  2. Parar cualquier otro front en el 8080 y arrancar el de esta copia:
     `cd C:/Users/pgris/PycharmProjects/porcentajes-f041/services/dedicacion-front`
     y `.venv/Scripts/python main.py`.
  3. Abrir `http://127.0.0.1:8080`, **Ctrl+F5**, y un periodo con líneas `Postv-`.
  4. En «Filtrar obra…», letra a letra: `p`, `po`, `pos`, `post`, `postv`,
     `postv-`, `postv-0656`. Esperado: con `pos` salen los que tienen alguna
     `Postv-` (y quien tenga «pos» en el nombre de una obra); desde `post`, solo
     postventa; con cada letra, la lista igual o más corta.
  5. Esc, y lo mismo en el buscador global (tecla `/`): el mismo comportamiento.
  6. `postventa` en «Filtrar obra…»: nadie (D1 = A).
  7. Un trozo del nombre de una obra con tilde, sin ella y en mayúsculas
     (`DEPOSITO`): casa igual.
  8. Alguien con una obra normal y una `Postv-` de otra: `<nombre de la normal>
     postv` (p. ej. `naves postv`) ya NO sale en la columna (D2), sí en el
     buscador global.
  9. Con `postv` en «Filtrar obra…», Ctrl+clic en dos filas y **C**: el diálogo
     sale precargado con `postv` y solo ofrece entradas `Postv-`. **Cerrar con
     Esc, SIN completar** (es el único paso que abre un diálogo que escribe).
  10. «Limpiar»: la tabla queda como antes de filtrar (mismas filas y orden).
  Resultado: _pendiente_.

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

`BACKLOG.md` tiene el orden completo. Ahora **F-041** (en curso, esta rama);
después **F-038** (cuadro de mando = el Excel de F-040 navegable), F-028 (plan
aprobado), F-021, F-030, F-036 (solo spec de momento), F-031, F-033 y, detrás,
F-017, F-018… F-037, F-039 y F-040 están cerradas y desplegadas (2026-10-07).

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
