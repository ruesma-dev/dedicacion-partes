<!-- progress/current.md -->
# Trabajo en curso

**F-050 en curso (T15f) en esta rama** (`feature/F-050-subfilas-partida`,
copia principal; T15f desbloqueada por el humano el 2026-10-14): subfilas por obra en el cuadrante con columna Partida y partida
propuesta. F-049 se desplegó el 2026-10-09 (transfer y front). El arnés es la
**1.7.3**.

## F-050 · Subfilas por obra con columna Partida (en curso)

- **Qué es** (humano, 2026-10-08): cada obra del trabajador en su subfila, con
  una columna Partida a la derecha para elegirla en el cuadrante (el modal de
  registro deja de ser donde se busca, aunque se pueda cambiar ahí); propuesta:
  1) la del parte anterior por obra y empleado, 2) la del último parte en que
  se asignó ese recurso, 3) el casamiento de `partes` (nombre y categoría).
  Absorbe F-043 (buscador predictivo, ordenado y con selector CI/CD). Toca los
  tres servicios; rigor crítico.
- **Spec aprobada por el humano el 2026-10-09** con D1-D10 = A («si») y dos
  precisiones: el modal de registro usa **el mismo selector** que la columna
  Partida (desplegable con buscador, como en `partes`), y el selector lleva
  botones **CD · CI · CP** (y «Todas») para filtrar por mayor (se añade CP).
- **Estado:** spec ajustada a las dos precisiones (2026-10-09): R8, R17,
  R26, R29, design §5 y §11 (D1-D10 DECIDIDAS, A) y MANUAL T16-T17; lista
  cerrada del front recalculada (T12, seis `c_*` de F-049 se borran). El
  mayor se toma de la **raíz** del presupuesto (leído en Sigrid: `categoria`
  de `partida_catalog` clasifica mal dos hojas bajo CD; la copia de
  `partes` tiene el mismo fallo: avisado al humano el 2026-10-09, design §5.1).
  `dev` traído a la rama. Dos bloqueos por tests fuera de la lista cerrada, los dos
  APROBADOS por el humano el 2026-10-09 y añadidos a requirements §6:
  `test_f037_r3_…` (una línea de datos, R20) y `test_f003_r8_…` (el conjunto
  de columnas suma las tres `partida_*`, R12). Hecho: T1-T5 (`686d00a`..
  `3aed309`; transfer 742 passed). **Implementer TERMINADO (2026-10-09):**
  T1-T15 (`686d00a`..`e182915`, `progress/impl_F-050.md`): mutación Python
  158/158 y JS 56/56 muertos (en copias aisladas), cobertura 341/341, `init.sh`
  en verde sin caché (api 768, front 184, transfer 750). T14 hecha por el
  líder: `azure-apps/dedicacion.md` con los endpoints, la variable y el orden
  transfer → api → front (`edaa2b7`, «sin desplegar»). **Review 1: CAMBIOS
  PEDIDOS** (`progress/review_F-050.md`): textos de 7 mutantes JS cortados con
  «…» (implementer relanzado); T19 sin marcar, F-050 duplicada en «Lo
  siguiente» y el rango de commits (corregidos por el líder). Observaciones:
  (g) en M2 para el tiempo del mes entero; una línea omitida por R20 no tiene
  botón de partida en el modal (**el humano aprueba el 2026-10-10 añadirlo:
  R29 bis; T15b hecha por el implementer en `6320474`**; **review 2 APROBADA**,
  sus observaciones recogidas: (g) en T17 y el motivo por texto llevado a
  F-048); postventa en R9 casa
  con `origen.codigo` en `proponer` y con `obra.codigo` en el preflight (hoy
  coinciden; anotado en «Hechos que no conviene volver a descubrir»).
- **MANUAL (humano, en local; transfer en modo pruebas):**
  - **M1 (T16, solo lectura):** en Git Bash,
    `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-transfer`
    y `.venv/Scripts/python prueba_escritura_porcentajes.py propuesta --ano 2026 --mes 9 --obra 0694 --recurso 1705036`
    (1705036 = GONZALEZ PANIAGUA, leído en Sigrid); lo mismo con `--obra 0696`.
    Esperado en la 0694: «Propuesta: CI.1.5», método `parte_anterior`, origen
    PT26/00319 · 09/2026; «Por mayor: CD … · CI … · CP …» con `CP.1`-`CP.12`
    en CP; botón preelegido CI; cada lectura < 30 s.
    **Resultado M1 (humano, 2026-10-11): OK.** 0694: propuesta CI.1.5
    (`parte_anterior`, PT26/00319 · 09/2026), 835 hojas (CD 727 · CI 95 · CP 13 ·
    OTRO 0), botón CI; lecturas 6,39 s / 5,26 s / 5,74 s. 0696: CI.1.5 por
    `ultimo_parte` (PT26/00319 y PT26/00350, obras 0694 y 0672), 2.636 hojas
    (CD 2562 · CI 62 · CP 12), botón CI; lecturas 4,30 s / 3,25 s / 0,80 s.
  - **M2 (T17, navegador):** transfer, api y front desde la copia principal
    (`.venv/Scripts/python main.py` en cada servicio); `curl -s http://localhost:8006/health`
    con `"modo_pruebas": true` (si no, PARAR). La api añade al arrancar las
    columnas `partida_*`. Puntos (a)-(f) de `specs/F-050-subfilas-partida/tasks.md`
    T17: subfilas y columna Partida; selector con buscador, Todas · CD · CI · CP,
    propuesta primera; postventa y VAR; regresión del teclado; el mismo
    selector en el modal (**Cancelar, sin Registrar**); tiempo en la 0696;
    **(g)** cronometrar «Registrar en Sigrid» de todo el mes hasta que sale el
    modal (dato para F-055, observación de la review 1).
  - **M3 (T18):** registro en modo pruebas, **solo con autorización del humano
    en ese momento**.
- **M2 del humano (2026-10-11): fallos; arreglos APROBADOS («ok»):** 1) tabla
  adaptable con scroll horizontal (se cortaba la derecha); 2) fila seleccionada
  igual con subfilas; 3) selector con «Cargando partidas…», sin abrirse dos veces;
  4) en el modal, selector encima del modal; 5) cambiar una partida en el modal
  repite el preflight solo de esa obra (los 502 eran el proxy del front cortando a
  los 120 s preflights del mes entero). Lentitud de fondo → F-055 rediseñada (spec
  en paralelo en `porcentajes-f041`). **Estado:** T15c TERMINADA por el implementer (`85d263f`..`5d75623`,
  `progress/impl_F-050.md`; api acepta `obra_ide` en el preflight, transfer
  sin tocar; mutación Python 160/160 y JS 46/46 en copias aisladas; init.sh
  en verde sin caché: api 774, front 218, transfer 750). `azure-apps` con
  `obra_ide` (`1037904`). **Review 3: CAMBIOS PEDIDOS:** «Registrar» se queda
  en «Analizando…» si de dos repreflights en vuelo falla el primero tras volver el
  segundo (hecho por el implementer en `2078505..2b44319`, con `obra_ide` como `int` en la ruta y el `ok`
  recalculado en `unirPreflight`, observaciones 2 y 3); T17 dice ya «(a)-(h)»
  (líder). Observación 1 (la manija de ancho con la tabla encogida) se mira en la
  M2 (h) 1. Hecho hasta `91fdb7a` (api 780, front 221, transfer 750 sin caché;
  mutación Python 164/164 y JS 7/7 en copias aisladas); el 422 de `obra_ide` ya
  en INTEGRACION y `azure-apps` (`36c894a`). **Review 4 APROBADA**; sus
  observaciones: `trabajador_ide` crudo (un 0 quitaría el filtro de `ejecutar`) →
  **F-056** nueva; «tras un error, el bloque de esa obra enseña el análisis
  anterior» y la manija de ancho, a mirar en la M2 (h) 5 y (h) 1.
- **M2 repetida por el humano (2026-10-12): dos fallos** (capturas en el Word
  `Doc1.docx` de Descargas, no versionado): (h)2 la fila seleccionada con
  subfilas sigue mal: la PRIMERA subfila sombrea todas las columnas y las demás
  solo su celda; el humano quiere el comportamiento de la primera en todas (todo
  el bloque del trabajador sombreado); (h)3 el selector se abre minúsculo (solo
  se ve el buscador; ni lista ni botones CD/CI/CP) en una fila cerca del borde
  inferior. Son defectos de T15c (dentro del plan aprobado). **Estado:**
  T15d TERMINADA por el implementer (`552fbfb`..`5bbda9e`, `progress/impl_F-050.md`; (h)2 era el *hover*, no el cursor; (h)3 pasaba en cualquier fila; solo front; mutación JS/CSS 26/26 en copia aislada; M2 (h) 2 y 3 ampliadas en T17). F-055: spec escrita en `porcentajes-f041` (D1-D8), espera al humano.
  **Review 5: CAMBIOS PEDIDOS:** la lista del selector no se puede desplazar
  (al recolocar, medir el alto natural sin `max-height` pone el `scrollTop` a 0;
  y un `scroll` dentro del panel recoloca); test que lo cace en un DOM que recorte
  el desplazamiento; M2 (h) 3 ampliada. T15e hecha por el implementer (`a738252..8fa91d1`; **review 6 APROBADA**; en la M2 mirar también ↓ junto al
  borde inferior con el ratón quieto y que con `ALTO_UTIL` se ven cinco filas; **espera
  que el humano repita la M2 (h) 2 y 3**), también con
  la observación 1 (el bloque repintado bajo el ratón quieto no sale sombreado).
  Observación 2: confirmar en la M2 que con `ALTO_UTIL` se ven cinco filas.
- **M2 repetida por el humano (2026-10-14):** «lo demás ok» salvo dos fallos de
  pantalla (captura `Captura de pantalla 2026-10-14 113142.png`, no versionada):
  1) el desplegable de obras corta en 14 (`.slice(0, 14)`, viene de F-042); 2) la
  columna Total se corta en la fila con «falta 50 %» (VINDEL DURO): T15c la deja
  en su ancho guardado aunque el contenido no quepa. **T15f APROBADA por el
  humano («ok») y lanzada al implementer.** Lo demás que pidió (propuesta en
  segundo plano en la columna con su origen, registrar sin buscar partidas) es
  F-055 (R3-R8, R27, R29-R36), ya aprobada. Tras T15f: review 7 y el humano
  repite M2 (d), (h) 1 e (i).
  **T15f TERMINADA por el implementer (2026-10-14)**: `61ede15`..(este commit),
  `progress/impl_F-050.md` § T15f; solo front; RED→verde (8 + 8 tests nuevos),
  Chrome headless antes/después, mutación JS manual 34/34 en copia aislada,
  `init.sh` en verde sin caché (front 269). Desviación anotada: en el editor la
  activa se hace visible con `offsetTop` (no `scrollIntoView`, que el DOM de
  F-042 de la lista cerrada no tiene); «Completar» sin «arriba» (aprobado).
- **Bloqueo de T15f (implementer, 2026-10-14), RESUELTO por el humano el mismo
  día («ok a todo»: 1 sí, 2 A, 3 como se propone; requirements §6 gana los dos
  tests y tasks.md T15f lo recoge). Implementer relanzado.** Lo que se consultó: No se ha escrito código de T15f (HEAD sin cambios de código).
  - **Qué rompe:** quitar el tope de 14 del desplegable de obras del editor
    rompe `services/dedicacion-front/tests/test_f042_sugerencias.py::test_f042_r3_busqueda_identica_y_luego_se_coloca`
    (F-042, NO está en requirements §6): su `BUSQUEDA_ANTES` fija literal
    `.filter((e) => !q || e.clave.includes(q)) .slice(0, 14);` («texto literal
    anterior a F-042»). Medido en una copia aislada (scratchpad, sin tocar el
    repo) quitando solo los dos `.slice(0, 14)`: suite del front **1 failed,
    241 passed**, y el único fallo es ese. No hay forma honrada de quitar el
    tope sin cambiar ese texto.
  - **Propuesta para el humano:** añadir a requirements §6 ese test, con un
    único cambio: `BUSQUEDA_ANTES` pierde `.slice(0, 14)` (el resto del
    literal, el teclado `TECLADO_ANTES` y los demás tests de F-042, sin tocar;
    las flechas siguen igual y la fila activa se hace visible dentro de
    `marcarActiva`, que ese test no fija). El de «Completar al 100 %» no lo
    fija ningún test (F-029 solo pide `candidatasDestino(input.value)`).
  - **Dos dudas más, para resolver en la misma consulta:**
    a) **Orden de encogido (punto 2).** «El sitio que falte sale primero de
    Asignaciones y Partida»: si vale para TODO estrechamiento (como dice la M2
    (i) 2, «encogen antes Asignaciones y Partida»), cambia el reparto
    proporcional de T15c y con él un test propio de F-050,
    `test_f050_m2_1_la_tabla_se_ajusta_a_su_panel` (a 1046 px pasa de
    `[203, 140, 299, 212, 190]` a `[280, 210, 196, 169, 190]`: Trabajador y
    Categoría ya no encogen hasta que Asignaciones y Partida lleguen a su
    mínimo). Si solo vale para lo que Total crece, ese test no cambia.
    Recomendado: lo primero (es lo que aprobó el humano en (i) 2), con el test
    propio actualizado y anotado.
    b) **«Completar al 100 %».** Su lista no es un panel flotante: va dentro
    del modal (`.completar-candidatas`, `max-height: 220px` y scroll propio).
    Sin tope y con la activa siempre visible, sí; «se abre arriba si no cabe
    debajo» no aplica (el modal ya cabe en la ventana). Recomendado: dejarlo
    así y decirlo en la M2 (i) 1.
  - **Ojo al tamaño:** requirements está en 150/150 e `impl_F-050.md` en
    220/220 (PUERTA TAMAÑO): añadir el test a §6 y la sección de T15f exige
    recortar antes otras líneas. `bash harness/init.sh` (sin
    `.arnes_cache/suite_*.ok`) en verde tras el bloqueo: raíz 418 + 1 skipped,
    api 780, front 253, transfer 750; avisa de F-050 `blocked`.

## Producción, hoy

- **Desplegado el 2026-10-09: F-049**, transfer `r20261009-1045` y front
  `r20261009-1046` (ambos `Running`; el transfer sigue en **modo real**,
  comprobado con `az containerapp show`): avisos del modal rotulados por tipo,
  repreflight al elegir partida y catálogo de partidas siempre. **Pendiente
  del humano:** la comprobación en producción (GONZALEZ PANIAGUA, 0694: «Sin
  partida» y «Sobrecarga»; **no confirmar la sobrecarga**, el 95 % ya está a
  mano). El texto de `redeploy_dedicacion.ps1` que dice «SIGUE en modo
  pruebas» está caducado.
- **Desplegado el 2026-10-08: F-045**, solo la api (`r20261008-1509`, revisión
  `Running` comprobada con `az containerapp show`): el Excel lleva Obras,
  Postventa y Detalle (sin Resumen) y la columna Observaciones vacía.
  **Pendiente del humano:** un Excel de producción y avisar a Juan y
  Administración de que desaparece el Resumen.
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

`BACKLOG.md` tiene el orden completo. Nuevas el 2026-10-08 (pedidas por el
humano): **F-049** (los avisos del modal de registro rotulados por tipo, con su
%; aprobada), **F-051** (pisar las líneas del parte al 0 % que ya existan),
**F-050** (subfilas por obra con columna Partida y partida propuesta; absorbe
F-043) y **F-021** redefinida (velar las etiquetas de las demás obras al
filtrar). **F-044** (recursos vinculados) sube. Del correo de Juan del
2026-10-08: **F-052** (una línea de mensajería por obra en curso y mes, con
la fecha fin de Sigrid) y **F-053** (delegados: parte único, cada línea a su
obra e imputada al CP); F-044 queda en persona, gasoil, vehículo y teléfono
(KM no). Juan quiere registrar **octubre entero desde la app**. F-045 desplegada.
F-049 desplegada. Orden: F-050 (en curso, esta rama), **F-055** (medir y acelerar la
previsualización del registro; 2026-10-08), F-051, F-044, F-052, F-053, **F-054** (el sync trae los %
que ya hay en los partes de Sigrid; 2026-10-08), F-021, F-048, F-046, F-038, F-028, F-030, F-036, F-031,
F-033 y, detrás, F-017, F-018…

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

- **F-050, postventa en la propuesta (R9):** `proponer` casa la postventa con
  `origen.codigo` (leído en Sigrid) y el preflight con `obra.codigo` (el que
  manda la api). Hoy coinciden; si alguna vez divergen, la propuesta del
  selector y la automática del registro diferirían en postventa.
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
