<!-- progress/current.md -->
# Trabajo en curso

**F-049 en curso en esta rama** (`feature/F-049-avisos-registro-por-tipo`,
copia `PycharmProjects/porcentajes-f041`): los avisos del modal de registro,
rotulados por tipo. La copia principal está en `dev`, sin feature en
ejecución: F-045 se cerró y se desplegó el 2026-10-08 (solo la api). El arnés
es la **1.7.3**.

## F-049 · Avisos del modal de registro por tipo (en curso)

- **Causa** (líder, lectura del código y de Sigrid): `app.js` ~1739-1747 pinta
  todos los conflictos como «Pisar … se borran … y se escribe <%>» sin mirar
  `motivo`, y el % sale de `nueva_can`, que el transfer ya no manda (siempre
  0 %). Caso del humano: GONZALEZ PANIAGUA, 2026-09: en la 0672 era «sin
  partida»; en la 0694, «sin partida» y una sobrecarga (MADM 95 % a mano en
  PT26/00319).
- **Plan aprobado por el humano el 2026-10-08** («si»): solo front, `sdd:
  false`, rigor estándar. Texto por tipo y % de `nuevas`; mismas claves a
  ejecutar.
- **Estado:** implementada (`3ad478b`..`d6d8658`, `progress/impl_F-049.md`):
  rotulado en una función pura con tests en node, campaña manual 33/33
  mutantes muertos (`progress/mutacion_manual_F-049.md`), init.sh en verde.
  **Review 1: CAMBIOS PEDIDOS** (`progress/review_F-049.md`): falta el nº de
  fallos por mutante en la tabla manual (implementer relanzado); O1 al
  informe; O2 y O3 ya en la MANUAL; O4 (el aviso final dice «repite y marca
  pisar» para todo) llevado a F-048. Cambio 1 y O1 recogidos por el
  implementer (`81dbbd8`: nº de fallos de los 33 mutantes, iguales a los del
  reviewer; campaña en serie, 1 worker, 299 s). **Review 2 APROBADA**
  (`progress/review_F-049.md`).
- **Ampliación aprobada por el humano el 2026-10-08** («si»), tras su MANUAL:
  a) al elegir partida se repite el preflight (conservando casillas); b) abrir
  el registro empieza sin partidas elegidas de antes; c) la partida elegida se
  enseña aunque no esté en la lista; d) transfer: `partidas_obra` siempre que
  haya líneas de obra, aunque todas lleven partida manual (hoy sale vacío y el
  desplegable dice «— sin partida —» mientras se escribiría la elegida antes);
  e) el aviso amarillo no se sale del recuadro. Despliegue: transfer y front.
  **Estado:** ampliación implementada (T4-T7, `24bef2f`..`ae7d467`,
  `progress/impl_F-049.md`): RED→verde en transfer y front, mutación 7/7
  (Python) y 32/32 (manual JS/CSS), init.sh en verde. `test_f013_r4` del
  transfer (lee `app.js`) llevaba en rojo desde T1, oculto por la caché de
  init.sh (las reviews 1 y 2 aprobaron sobre ese rojo); ajustado con
  justificación (informe, decisión 3); anotado en el encargo 1.7.12 de
  `arnes-base` (`7b6701a`). Lo que se salía era sobre todo el rótulo de la
  casilla (decisión 2). **Review 3: CAMBIOS PEDIDOS** (`progress/review_F-049.md`):
  `test_f013_r4` debe prohibir los tres motivos fuera de `rotuloConflicto`
  (implementer relanzado); los `acceptance` a)-e) y la cabecera de este fichero,
  corregidos por el líder; O5 (doble registro concurrente) llevado a F-048; O6
  aceptada. Después, review 4 y la MANUAL.
- **MANUAL (humano, en local, sin pulsar «Registrar»):** tres consolas. El
  **transfer con el código de esta copia**, arrancado desde la carpeta del
  transfer de la principal (su `.env` se lee de la carpeta de arranque); la api
  desde la principal; el front desde esta copia.
  1. Transfer: `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-transfer`
     y `.venv/Scripts/python C:/Users/pgris/PycharmProjects/porcentajes-f041/services/dedicacion-transfer/main.py`;
     en otra consola `Invoke-RestMethod http://localhost:8006/health`:
     `modo_pruebas` = True. **Si no es True, PARAR y no seguir.**
  2. Api: `cd C:/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-api`
     y `.venv/Scripts/python main.py` (8090).
  3. Front: parar cualquier otro en el 8080;
     `cd C:/Users/pgris/PycharmProjects/porcentajes-f041/services/dedicacion-front`
     y `.venv/Scripts/python main.py`.
  4. (Necesita la base local con septiembre 2026 y GONZALEZ PANIAGUA asignada;
     si no, solo los pasos 8 y 9.) `http://127.0.0.1:8080`, **Ctrl+F5**,
     septiembre 2026, «⇪ Sigrid» en su fila: cada aviso empieza por **Sin
     partida**, **Sobrecarga** o **Pisar**, con su %, ninguno «se escribe 0%».
     En modo pruebas mira la 0404: la sobrecarga de la 0694 no sale en local.
     Marca una casilla que no sea la «Sin partida» de la línea del paso 5.
  5. **a)** En una línea con aviso amarillo «partida no localizada…», elige
     una partida: «Registrar» pasa a «Analizando…» y el modal se repinta sin
     ese aviso ni su casilla «Sin partida»; la partida sigue elegida y la
     casilla del paso 4, marcada.
  6. **d)** Con todas las líneas de esa obra con partida elegida, el desplegable
     enseña la partida con su descripción y la lista entera; F12 → Red → último
     `preflight` → Respuesta: `partidas_obra` de esa obra no está vacío.
  7. **b)** **Cancelar** y abrir otra vez con «⇪ Sigrid» y con «Registrar en
     Sigrid»: vuelve la propuesta automática con su aviso, no la partida del
     paso 5. **Cancelar.**
  8. Los tres tipos: F12 → consola (Chrome pide `allow pasting` antes del
     primer pegado), pegar:

```js
pintarModalPreflight({obras: [{obra: {codigo: "0694", nombre: "Prueba F-049"}, ok: true, partes: [], acciones: [], conflictos: [
 {clave: "sin_partida:1", motivo: "sin_partida", nombre: "GONZALEZ PANIAGUA", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.05}], lineas: [], contexto: []},
 {clave: "sobrecarga:1|2026-09", motivo: "sobrecarga", nombre: "GONZALEZ PANIAGUA", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.1}], lineas: [], contexto: [{hora_codigo: "MADM", can: 0.95}], suma_existente: 0.95, suma_total: 1.05, exceso: 0.05},
 {clave: "1|2026|9|5|0", motivo: "pisado", nombre: "GONZALEZ PANIAGUA", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.6}], lineas: [{ide: 8001, hora_codigo: "MADM", can: 0.4, fecha_int: 20260930}], contexto: []}]}]})
```

     Salen «Sin partida» (5 %), «Sobrecarga» (ya tiene 95 %, sumaría 105 %, un
     5 % por encima) y «Pisar» (se borra la línea 8001, se escribe 60 %).
     **NO tocar «Registrar»; Cancelar.**
  9. **c) y e)** En la consola, pegar:

```js
pintarModalPreflight({obras: [{obra: {codigo: "0694", nombre: "Prueba F-049 c/e"}, ok: true, partes: [], partidas_obra: [], partidas_postventa: [], acciones: [
 {registro_id: 999999, nombre: "PRUEBA", destino: "obra", accion: "escribir", can: 0.5, hora_codigo: "MADM", paride: 99999, partida_cod: "CI.9.99",
  aviso: "partida no localizada para la categoría/nombre: no se escribe sin confirmarlo — elige una partida o marca la confirmación · palabra_larga_sin_espacios_para_ver_que_el_texto_no_se_sale_del_recuadro_xxxxxxxxxxxxxxxxxxxx"}],
 conflictos: [{clave: "x", motivo: "sin_partida", nombre: "GONZALEZ PANIAGUA, MILAGROS", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.5}], lineas: [], contexto: []}]}]})
```

     El desplegable enseña «CI.9.99 · (no está en la lista)» elegida, no «—
     sin partida —»; el aviso amarillo y la casilla «Sin partida» se parten en
     varias líneas dentro de su recuadro. **No tocar el desplegable ni
     «Registrar»** (lanzaría el registro del periodo contra la 0404).
     **Cancelar.**
  Resultado: _pendiente_.

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

`BACKLOG.md` tiene el orden completo. Nuevas el 2026-10-08 (pedidas por el
humano): **F-049** (los avisos del modal de registro rotulados por tipo, con su
%; aprobada), **F-051** (pisar las líneas del parte al 0 % que ya existan),
**F-050** (subfilas por obra con columna Partida y partida propuesta; absorbe
F-043) y **F-021** redefinida (velar las etiquetas de las demás obras al
filtrar). **F-044** (recursos vinculados) sube. Orden: F-045 (en curso), F-049,
F-051, F-044, F-050, F-021, F-048, F-046, F-038, F-028, F-030, F-036, F-031,
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
