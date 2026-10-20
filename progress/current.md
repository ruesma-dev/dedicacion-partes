<!-- progress/current.md -->
# Trabajo en curso

**En curso: F-051** (pisar las líneas del parte editándolas, nunca
borrando), `in_progress`. **Review pasada 1: RECHAZADO** (2026-10-21,
`progress/review_F-051.md`): el mutante que el implementer daba por
equivalente (`registro_pipeline.py:1095`) **no lo es** (con `can = 0` y una
relectura de `1e-6` original y mutante difieren) ⇒ test que lo mate y nueva
campaña hasta cero supervivientes; más dos arreglos menores (línea 568 de
`registro_pipeline.py`, primera línea de `impl_F-051.md`). El rastro
desfasado de este fichero lo ha podado el líder. **Correcciones hechas por
el implementer** (2026-10-21: test de la frontera de R13 `d807cce`, formato
`7a5f801`, campaña en serie sobre `7a5f801` con **134 mutantes y 0
supervivientes** `e51ba7b`, informe `d170afb`). **Review pasada 2: APROBADO**
(2026-10-21, `progress/review_F-051.md`). **Falta T15** (MANUAL del humano)
para pasar a `done`. Spec aprobada por el humano el 2026-10-20 (D1-D15,
en «decisiones» abajo); bloqueos de implementación resueltos por el humano:
T3 opción A, T12 opción B. Copia
`C:\Users\pgris\PycharmProjects\porcentajes-f051`, rama
`feature/F-051-pisar-lineas-cero` (con `dev` fusionado el 2026-10-21: el
despliegue de F-057); sus `.venv` son uniones de directorio a los de la
copia principal (creadas por el líder, no versionadas). Ningún agente
escribe en Sigrid. **F-030** aprobada y a la espera en la copia
`porcentajes-f030` (va después de F-051). El arnés es la **1.7.3**.

**Pendiente del humano para cerrar F-051:** T15, MANUAL en modo pruebas en
la 0404 (pasos y comando exacto abajo, en «implementación»). Ya **no** hace
falta que acepte ningún mutante equivalente. **Pendiente del humano,
decidir (observaciones de la review):** O2 (exigir además línea mensual al
localizar por `hmores_ide`) y O4 (con un % menor de 0,00005 sale `can` 0,
que editaría una línea al 0 % dejándola a 0 con nuestra `synckey`; hueco
anterior a F-051). **Pendiente del líder:** T16 al desplegar (transfer → api
→ front): `azure-apps/dedicacion.md` y aviso a `partes`.

## F-051 · bloqueos de implementación (2026-10-20) · RESUELTOS

- **T3**: añadir `edita_ide` y `a_cero_ides` a `Conflicto` rompía
  `test_f013_r4_no_hace_falta_ningun_campo_nuevo`, fuera de la lista cerrada.
  Humano: **opción A** («a»): entra en la lista y su conjunto acepta los dos
  campos (`c5bc6e9`).
- **T12**: el texto nuevo del pisado rompía los dos `test_f049_r2_…`.
  Humano: **opción B** («La b»): el detalle termina como hoy, «se edita la
  línea X (…)[; quedan a 0: …] y se escribe N%»; esos tests no se tocan
  (`d0c1ab7`, hecho en `24ba7aa`).

## F-051 · implementación (implementer, 2026-10-20)

- **Estado:** T1-T14 y T17 `[x]`; informe en `progress/impl_F-051.md`.
  **Cambios de la review 1 hechos (2026-10-21):** test de la frontera de
  R13 que mata el mutante de `registro_pipeline.py:1095` (`d807cce`);
  formato de la línea 568 y de un docstring del lote (`7a5f801`); 3.ª
  campaña de mutación en serie (`--workers 1`) sobre `7a5f801`: **134
  mutantes, 0 supervivientes** (`e51ba7b`, `progress/mutacion_F-051.md`);
  primera línea con la ruta en el informe. Ya no hay ningún equivalente que
  aceptar. `init.sh` sin `[KO]`, cobertura 99,2 %. Listo para la pasada 2.
- **Decisiones del implementer** (detalle en el informe §2):
  `lineas_registradas(claves, ides)` sin `ides` delega en
  `lineas_por_synckey`; `repartir_choques` y `es_nuestra_de_otra` puras
  nuevas; `despues` del log usa `a.can`/`a.tot` ya redondeados; `usadas`
  arranca vacío (una línea al 0 % nunca es choque).
- **Desviaciones justificadas:** la fase `estado` del script lee además
  `pos`, `paride` y `tex` (para T15); la api usa
  `getattr(a, "sigrid_hmores_ide", None)`; el paso 9 bis va antes del alta de
  partes y solo lo que inserta crea parte o lee `max_pos`.
- **T15 (MANUAL, la ejecuta el humano, modo pruebas). Sin ejecutar a
  2026-10-21.** Antes, el humano (o Administración) crea a mano en el parte
  En registro de la 0404 de noviembre de 2026 (PT26/00371) dos líneas `M*`
  con `can = 0` y sin `synckey`: una del recurso de prueba (el de F-050) y
  otra de un segundo recurso. Transfer, api y front locales con
  `OBRA_PRUEBAS_FORZAR=true`. Lectura, en Git Bash, desde la copia que se
  pruebe (solo lectura; anotar `ide` y `pos`):
  `cd services/dedicacion-transfer && .venv/Scripts/python prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`.
  Esperado: el modal dice que edita la línea; tras **Registrar**, mismo `ide`
  y `pos`, con el %, la partida, `PRUEBA-PORC` y `porcentajes:…`, sin línea
  nueva y la otra a 0; tras cambiar el %, pisado «se edita …» y la misma
  línea con el % nuevo; tercera vez, «ya registrada»; ningún `DELETE` en el
  log del transfer. Limpieza: `limpiar --confirmar` borra la editada
  (`PRUEBA-PORC` y nuestra `synckey`, D15 = A); la del segundo recurso, a
  mano.
- **`azure-apps` pendiente (T16, líder, al desplegar transfer → api →
  front):** `azure-apps/dedicacion.md` desde `docs/INTEGRACION.md` §1, §5 y
  §7: el transfer EDITA en su sitio líneas `M*` de partes compartidos
  (`UPDATE` con guarda, sin `DELETE`); `LineaIn.hmores_ide` de ida;
  `ya_registradas_ide`, `editadas`, `a_cero` y `escritas[].editada` de
  vuelta; `borradas` siempre 0 en el registro. Avisar a `partes`.

## F-051 · decisiones del humano sobre la spec (2026-10-20, todas cerradas)

- **Pasada 2:** «d1, nunca borramos lineas, editamos el valor. d5, cualquier
  linea a 0% se puede pisar». **D1 = C** (`UPDATE` en su sitio, nunca
  `DELETE`); **D5**: cualquier línea al 0 %, también con `synckey` de
  `partes` o nuestra. D2-D4 y D6-D9, las recomendadas (D2 = A sin confirmar,
  con aviso; D3 = A; D4 `can` 0 exacto o nulo; D6 = A; D7 = B; D8 fuera;
  D9 = A).
- **Pasada 3:** D10 = B (se edita todo lo que insertaríamos) y D13 como
  recomendado («ok a lo demás»). **D11:** «y no deberia encontrarla por el
  ide de sigrid una vez que se registra la linea? es unico y no se edita
  nunca» y «d11 que ya localice»: F-051 **no cambia la `synckey` de una
  línea de otro sistema** y localiza lo editado por `hmores.ide`; a una línea
  de Administración (`synckey` vacía) se le pone la nuestra. **D12:** «que
  pase a editar»: el pisado confirmado de hoy también pasa a `UPDATE`.
- **D14 = A y D15 = A** («si me vale»): con varios choques se edita el de
  menor `ide` y los demás a 0; `limpiar` (solo el script de pruebas) sigue
  borrando lo marcado `PRUEBA-PORC`.
- **Exploración (solo lectura, 10 `SELECT` por sigrid-api, base `ruesma`):**
  en octubre, parte PT26/00370 de la 0707 (En registro), cuatro personas con
  su línea `M*` a 0 (`hmores` 410600, 410931, 410935, 410937): copia de
  septiembre por Administración, sin `synckey`. En 2026, 63 grupos con
  varios choques (PT26/00109 llega a 9 líneas `MDEL`).

## Producción, hoy

- **Desplegado el 2026-10-20: F-057**, api y front, en ese orden, lanzado por
  el humano con `redeploy_dedicacion.ps1 -Solo api` y `-Solo front` (esta vez
  sin cortarse): api `r20261020-1342` (revisión
  `ca-dedicacion-api--r20261020134227`) y front `r20261020-1351` (revisión
  `ca-dedicacion-front--r20261020135103`), las dos `RunningAtMaxScale`,
  `Healthy` y con el 100 % del tráfico (comprobado por el líder con `az
  containerapp revision list`). Transfer sin cambios.
  `azure-apps/dedicacion.md` al día (`a4c046c`). **Pendiente del humano:** la
  comprobación en producción (Ctrl+F5; con propuestas en curso, la postventa
  dice «automática» y solo las normales sin partida «buscando partida…»).
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
2026-10-20. Orden: **F-051** (review APROBADA; falta T15, MANUAL del humano), **F-030**
(spec aprobada, va detrás), F-044, F-052, F-053, **F-054** (el sync trae los %
que ya hay en los partes de Sigrid; 2026-10-08), F-021, F-048, F-046, F-038, F-028, F-036, F-031,
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
