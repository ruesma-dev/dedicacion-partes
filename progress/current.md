<!-- progress/current.md -->
# Trabajo en curso

**En curso: F-061** (búsqueda predictiva en el desplegable de incidencias;
`sdd: false`, rigor estándar), `in_progress` desde el 2026-10-22, rama
`feature/F-061-busqueda-predictiva-incidencias` en la copia principal.
**Implementación hecha el 2026-10-23** (T1-T4, `d9061e0`..`a4aeaae`;
informe `progress/impl_F-061.md`, mutación `progress/mutacion_F-061.md`
10/10 muertos); **review 1 RECHAZADA el 2026-10-23** (`progress/review_F-061.md`,
`c517600`: dos mutantes de JS sobreviven a los tests de node y falta el nº de
workers en «Evidencias»; solo tests y papeleo, más la O1); **implementer
retomado para corregirlo**. Api y front; ni
transfer ni Sigrid. Pedida por el humano tras desplegar F-030 (`baj` no
encontraba B: su nombre en Sigrid es «Enfermedad/Acc. no laboral(B)»);
propuesta aprobada el 2026-10-22 («me parece bien»). Criterios y las
decisiones del humano, en el `description` de F-061 (`features.json`).

## F-061 · decisiones del humano a los dos bloqueos del implementer

Bloqueada dos veces antes de escribir código; resueltas las dos (el
detalle de las opciones, en el historial de git de este fichero,
`9110c80` y `ecf6ed8`):

- **2026-10-22, «yes»:** cambio MÍNIMO de la aserción de
  `test_f030_catalogo.py::test_f030_r6_ruta_incidencias_activas_por_letra`
  (lista cerrada de tests ajenos: solo ese); empate por el ORDEN DE LAS
  ENTRADAS de `config.yaml` (B, AT, M, FJ, F, V, H); código y letra que
  empieza, justo detrás de «letra exacta»; errata medida con OSA.
- **2026-10-23, «continua» a la recomendada:** ese orden llega al front
  como campo `orden_busqueda` por incidencia en `GET /api/v1/incidencias`
  (posición en `config.yaml`, `null` sin entrada); la lista sigue por letra
  (F-030 R6 intacta). El cambio autorizado de `test_f030_r6_…` es añadir
  `"palabras"` y `"orden_busqueda"` a cada dict esperado, nada más.

## F-061 · al desplegar y MANUAL

- **Propuesta de la review para `arnes-base`** (pendiente de PARADA 1 con
  el humano, no aplicada): en `CHECKPOINTS.md` C4 bis, si la lógica vive en
  JS u otro lenguaje sin puerta de mutación, una mini-campaña manual
  documentada (original → mutado, resultado).

- **Despliegue** (con permiso del humano; el script lo lanza el humano):
  `redeploy_dedicacion.ps1 -Solo api,front`, **api antes que front** (el
  front nuevo sin la api nueva no tiene `palabras` ni `orden_busqueda`:
  busca solo por letra, código y nombre).
- **`azure-apps/dedicacion.md`** (líder, al desplegar): §5, `GET
  /api/v1/incidencias` gana `palabras` (lista) y `orden_busqueda` (entero o
  `null`) por incidencia; las palabras extra viven en
  `config/config.yaml` de la api (`sync.incidencias.palabras_extra`).
- **MANUAL tras desplegar** (humano): Ctrl+F5 en el front; en la celda del
  % de una línea teclear `baj` ⇒ B, AT y M, con B arriba; `civ` ⇒ V;
  `vacasiones` ⇒ V; después «Sincronizar Sigrid» y comprobar que el
  desplegable sigue saliendo sin recargar la página.

**F-030** (incidencias en el cuadrante)
**cerrada (`done`) y desplegada el 2026-10-22** (permiso del humano, «3
si»; el script lo lanzó el humano, ver «Producción, hoy»);
`azure-apps/dedicacion.md` `3d5c80b`. El arnés es la **1.7.3**.

**Pendiente del humano:** la comprobación de F-051 en producción (Ctrl+F5;
un registro con una línea `M*` al 0 % en el parte la edita en su sitio y el
modal lo avisa; un pisado dice «se edita la línea X (…) y se escribe N%»).
**Aviso a `partes`** (lo transmite el humano; aquí no se toca `partes`):
desde F-051 el transfer de dedicación **edita en su sitio** líneas `M*` de
los partes compartidos (también las que tengan `synckey partes:…`, sin
cambiarla) y no borra ninguna; su `partes.md` debería decirlo.
**F-030 en producción:** lanzar un sync (el desplegable de incidencias sale
vacío hasta que el sync llene el catálogo de `auxhor`) y comprobarla
(Ctrl+F5; texto en la celda del % ⇒ desplegable; registrar ⇒ el par
`CI*`/`CIZ` en el parte). **Aviso a `partes`** de F-030: dedicación escribe
líneas de incidencia `CI*`/`CIZ` (`can = 0`, `synckey porcentajes:inc:`) en
los mismos partes, no duplica las suyas y, si cambian los días, edita la
`fec` de las nuestras; nunca borra.

## F-030 · CERRADA y DESPLEGADA (2026-10-22)

- Review 3 **APROBADO** (`progress/review_F-030.md`); `init.sh` en verde;
  6.ª campaña de mutación con 0 supervivientes; cobertura 99,9 %. Resumen
  en `progress/history.md`; el detalle de la implementación, los bloqueos
  de T4 y T14 y el anexo R30, en `progress/impl_F-030.md`,
  `progress/impl_F-030_anexo.md` y `progress/spec_F-030.md`.
- **T20 hecha por el líder** en la 0404 con autorización del humano («1
  si»): cambio de días 5-9 → 6-12 sobre los mismos dos `ide`, ninguna línea
  nueva, `ya_registrado` y 0404 limpia (`progress/manual_F-030.md`).
- **El par a medias** (design §12) lo aceptó el humano el 2026-10-22
  («2ok»): sin D17.
- **Desplegada el 2026-10-22** (ver «Producción, hoy»);
  `azure-apps/dedicacion.md` `3d5c80b` (§1, §5 y §7: `auxhor`, el par
  `CI*`/`CIZ`, la edición de su `fec`, las tablas y los campos nuevos).

## F-051 · CERRADA y DESPLEGADA (2026-10-21)

**F-051** (pisar las líneas del parte
editándolas, nunca borrando) cerrada el 2026-10-21 y **desplegada el
2026-10-21** por el líder con permiso del humano («autorizo … despliegue de
f51»), transfer → api → front (ver «Producción, hoy»); T16 hecho
(`azure-apps/dedicacion.md` `223490c`).
Altas nuevas del 2026-10-21: **F-058** (un % que redondea a 0 no se
registra), **F-059** (% por días con el calendario de convenio) y **F-060**
(leer la bandeja de `partes`). El arnés es la **1.7.3**.
## Producción, hoy

- **Desplegado el 2026-10-22: F-030**, los tres servicios en orden con
  `redeploy_dedicacion.ps1 -Solo transfer,api,front` (lo lanzó el humano:
  el permiso de la sesión no dejó al líder): transfer `r20261022-1513`,
  api `r20261022-1514` y front `r20261022-1516`, revisiones
  `…--r20261022151217`, las tres `RunningAtMaxScale`, `Healthy` y con el
  100 % del tráfico (`az containerapp revision list`). El transfer sigue en
  **modo real** (`OBRA_PRUEBAS_FORZAR=false`) y transfer y api arrancaron sin
  errores (`containerapp logs`; la api crea `tipo_incidencia` e `incidencia`
  al arrancar). `infra/imagenes.json` al día en este commit.
- **Desplegado el 2026-10-21: F-051**, los tres servicios en orden, por el
  líder con `redeploy_dedicacion.ps1 -Solo transfer|api|front` (permiso del
  humano): transfer `r20261021-1611` (revisión
  `ca-dedicacion-transfer--r20261021161055`), api `r20261021-1613`
  (`…--r20261021161322`) y front `r20261021-1615` (`…--r20261021161520`), las
  tres `RunningAtMaxScale`, `Healthy` y con el 100 % del tráfico (`az
  containerapp revision list`). El transfer sigue en **modo real**
  (`OBRA_PRUEBAS_FORZAR=false`, `az containerapp show`) y arrancó sin errores
  (`containerapp logs`). El script volvió a cortarse tras cada `containerapp
  update` (el `Run-Az` de «Lo que espera al humano»). `infra/imagenes.json`
  al día en este commit; `azure-apps/dedicacion.md` `223490c`.
- **Desplegado el 2026-10-20: F-057**, api y front, en ese orden, lanzado por
  el humano con `redeploy_dedicacion.ps1 -Solo api` y `-Solo front` (esta vez
  sin cortarse): api `r20261020-1342` (revisión
  `ca-dedicacion-api--r20261020134227`) y front `r20261020-1351` (revisión
  `ca-dedicacion-front--r20261020135103`), las dos `RunningAtMaxScale`,
  `Healthy` y con el 100 % del tráfico (comprobado por el líder con `az
  containerapp revision list`). Transfer sin cambios.
  `azure-apps/dedicacion.md` al día (`a4c046c`). **Comprobado por el humano
  en producción el 2026-10-20:** «he revisado en real y funciona todo
  perfectamente».
- **Desplegado el 2026-10-19: F-056**, solo la api: `r20261019-1020`
  (revisión `ca-dedicacion-api--r20261019102033`, `RunningAtMaxScale`,
  `Healthy`, 100 % del tráfico; transfer y front sin cambios). El script volvió
  a cortarse tras el `containerapp update` (el `Run-Az` de «Lo que espera al
  humano»); la revisión se comprobó con `az containerapp revision list`.
  Comprobado por el líder en el navegador (solo preflight): `trabajador_ide`
  `""`, `false` y `"abc"` ⇒ 422 `trabajador_ide no es un entero: …`; `/health`
  200. `azure-apps/dedicacion.md` al día (`16dfece`).
- **Desplegado el 2026-10-17: F-055**, los tres servicios en orden: transfer
  `r20261017-1306`, api `r20261017-1310` y front `r20261017-1314` (revisiones
  `…--r20261017130616`, `…131025` y `…131348`, las tres `RunningAtMaxScale` con
  el 100 % del tráfico; el transfer sigue en **modo real**,
  `OBRA_PRUEBAS_FORZAR=false`, comprobado con `az containerapp show`). La api
  aplicó al arrancar las 5 columnas `asignacion.propuesta_*` («5 sentencias DDL
  aplicadas», sin errores). **C6 CUMPLIDA** (líder en el navegador, a petición
  del humano, «intenta hacerlo tu», 2026-10-18; septiembre 2026, solo preflight
  y **Cancelar**): GONZALEZ PANIAGUA 1,05 y 0,80 s (≤ 30 s; 0672 y 0694 por
  `parte_anterior`, mismas partidas que en local; el modal enseña la 0672 ya
  registrada, línea 409559, y la 0694 omitida por parte PT26/00319 cerrado);
  mes entero 8,37 s, 59 obras, 304 líneas, sin 502 ni obras con error (≤ 60 s);
  repreflight de la 0694 0,81 s. Las propuestas del mes ya estaban calculadas
  al abrirlo (`propuestas_en_curso: false`), así que no se vio «buscando
  partida…». O2 comprobada después pintando el mes en curso en la pestaña del
  líder (sin llamar a la api): 62 líneas dirían «buscando partida…» sin
  encolarse nunca (53 de postventa y 9 de GG) ⇒ **F-057** (humano,
  2026-10-19).
- **Desplegado el 2026-10-14: F-050**, los tres servicios: transfer
  `r20261014-1740`, api `r20261014-1743` y front `r20261014-1746` (revisiones
  `…--r20261014173903`, las tres `Running`; el transfer sigue en **modo real**,
  comprobado con `az containerapp show`): subfilas por obra con columna Partida,
  selector con Todas · CD · CI · CP y partida propuesta. **Pendiente del humano:**
  la comprobación en producción (Ctrl+F5, septiembre 2026; Partida de GONZALEZ
  PANIAGUA en la 0694: selector con CI preelegido; «⇪ Sigrid»: partida y origen
  en cada línea; **Cancelar**). Los `digest` de `infra/imagenes.json` siguen sin
  actualizarse al publicar (punto 2 de «Lo que espera al humano»).
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
%; desplegada), **F-051** (pisar las líneas del parte al 0 % que ya existan),
**F-050** (subfilas por obra con columna Partida y partida propuesta; absorbe
F-043) y **F-021** redefinida (velar las etiquetas de las demás obras al
filtrar). **F-044** (recursos vinculados) sube. Del correo de Juan del
2026-10-08: **F-052** (una línea de mensajería por obra en curso y mes, con
la fecha fin de Sigrid) y **F-053** (delegados: parte único, cada línea a su
obra e imputada al CP); F-044 queda en persona, gasoil, vehículo y teléfono
(KM no). Juan quiere registrar **octubre entero desde la app**. F-045 desplegada.
F-049 desplegada. F-050 desplegada. F-055 cerrada y desplegada el 2026-10-17. F-056 cerrada y
desplegada el 2026-10-19. F-057 cerrada el 2026-10-19 y desplegada el
2026-10-20. F-051 cerrada y desplegada el 2026-10-21. F-030 cerrada y desplegada el 2026-10-22. Orden: **F-058** (un % que redondea a 0 no se registra), F-044, F-052, F-053, **F-054** (el sync trae los %
que ya hay en los partes de Sigrid; 2026-10-08), F-021, F-048, F-046, F-038, F-028, F-036, F-031, F-059, F-060,
F-033 y, detrás, F-017, F-018…

## ⚠ Lo que espera al humano

- **O1 de F-056: ¿feature propia para validar el resto del cuerpo del
  registro?** `overrides` no enteros dan 500 (`int(k)`, `int(v)` en
  `routes.py`, preflight y ejecutar); `pisar_claves` y `usuario` llegan crudos
  a `ejecutar` (`list()` de un texto lo trocea en caracteres). Se le suma la
  O1 de la review 1 de F-056: un entero enorme (`10**30`) en `trabajador_ide`
  u `obra_ide` pasa la validación y PostgreSQL da 500 (`integer out of
  range`), no 422; no escribe nada.

- **`Run-Az` de `infra/00_capps_vars_dedicacion.ps1` aborta tras un `update`
  que sí se aplica** (2026-10-17 las tres veces y otra el 2026-10-19 con la
  api de F-056; el 2026-10-20, api y front de F-057, NO se cortó: `az : ` vacío,
  `NativeCommandError` en PS 5.1): el `containerapp update` crea la revisión y
  PowerShell convierte lo que `az` escribe en stderr en error terminante, así que
  `redeploy` para tras el primer servicio. Se desplegó relanzando `-Solo api,front`
  y `-Solo front`, comprobando cada revisión. Propuesta a decidir: que `Run-Az`
  rebaje `ErrorActionPreference` a `Continue` alrededor de la llamada y decida solo
  por `$LASTEXITCODE`.
- **Trabajo del arnés tras F-055** (líder, a proponer): O1 y dos automejoras de
  sus reviews —`CHECKPOINTS.md` C4: trazar un R «como hoy» o documental; una
  mutación manual de Python también exige tabla con texto exacto y el reviewer
  corre los mutantes del generador sobre esas líneas—, portadas a `arnes-base`.
  Más la automejora de la review 1 de F-056: que C4 bis acepte el nº de
  workers de `mutacion_F-XXX.md` (la herramienta ya lo imprime) o que
  init.sh compruebe que «Evidencias» lo lleva (un rechazo de solo papeleo).
  Más el aviso del implementer de F-057: `harness/mutacion_paralela.py` con 4
  workers dio 4 supervivientes falsos (la 2.ª tanda de los workers; a mano y
  en serie mueren), detalle en `progress/mutacion_F-057.md`. Si es defecto de
  la herramienta, vale para cualquier proyecto ⇒ `arnes-base`. Y la
  automejora de la review de F-057: C4 dice «MANUAL … pendientes de que el
  humano las ejecute», pero aquí el líder las cumple a menudo antes de la
  review (F-055, F-056, F-057); propuesta: «listadas con su comando exacto y,
  si ya se ejecutaron, con quién, cuándo y el resultado real» ⇒ `arnes-base`.
- **Borrar en la 0404 las líneas de las pruebas locales** (modo pruebas,
  `PRUEBA-PORC`): las dos de Bas Leal (parte PT26/00344, `porcentajes:148` y
  `:149`) y la de la M3 de F-050 (parte PT26/00371, noviembre 2026, `hmores`
  410599, GONZALEZ PANIAGUA, `porcentajes:180`).
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
