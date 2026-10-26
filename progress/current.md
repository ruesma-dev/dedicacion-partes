<!-- progress/current.md -->
# Trabajo en curso

**En curso: F-044** (aplicar los porcentajes también a los recursos
vinculados al trabajador; `sdd: true`, rigor crítico), **`in_progress`**
(bloqueada antes de T7 el 2026-10-26 y **desbloqueada el mismo día**: el
humano contestó «si a todo» a las tres preguntas, ver «F-044 · decisiones
del humano al bloqueo de T7», justo debajo). T1-T20, T22 y T24
hechas por el implementer (2026-10-26; informe en `progress/impl_F-044.md`);
**T21 MANUAL pendiente del humano** (comandos abajo, «F-044 · T21»);
**7 mutantes equivalentes pendientes de que el humano los acepte**
(`progress/mutacion_F-044.md`); T23 es del líder al desplegar. Worktree `porcentajes-f044`, rama
`feature/F-044-recursos-vinculados`, con `dev` unido (F-062 incluida). Spec
APROBADA por el humano el 2026-10-25 («ok a todo»), en
`specs/F-044-recursos-vinculados/`. Informe del implementer:
`progress/impl_F-044.md`. Escribe en Sigrid solo vía el
transfer y **solo en modo pruebas** (0404, `PRUEBA-PORC`); ninguna escritura
real. **Pendiente del humano (de F-062, ya desplegada el 2026-10-26):** el
**aviso a `partes`** (texto en «Riesgos para el humano», más abajo).
**Después:** F-063 (filtro por tipo de incidencia, dada de alta en `dev` el 2026-10-26, solo front) y F-054 (spec aprobada, worktree `porcentajes-f054`).

## F-044 · decisiones del humano al bloqueo de T7 (2026-10-26, «si a todo»)

1. **Sí:** lista cerrada del front ampliada para T7 con
   `test_f050_subfilas.py`, `test_f050_m2_arreglos.py`,
   `test_f050_t15f_total.py`, `test_f050_t15d_sombreado.py`,
   `test_f050_t15e_sombreado.py`, `test_f030_tabla_incidencias.py` y
   `test_f041_filtro_obra.py`. Cambio permitido: **solo** añadir la columna
   «Tipo recurso» donde aparezcan las columnas; nada más de lo que aseveran.
2. **Sí:** cablear el sync de vinculados en `deps.py`. Lista cerrada de la
   api ampliada con los 11 tests: `test_f023_sync_empresa.py` ×5 `r18_*`,
   `test_f025_sync_postventa.py::test_f025_r12_el_contenedor_comparte_un_solo_transfer`,
   `test_f030_catalogo.py::test_f030_r3_el_sync_y_el_preview_reales_usan_la_consulta_de_config`,
   `test_f032_empresas_sigrid.py` ×2 (`r1_el_sync_real…`, `r4_el_preview_real…`),
   `test_f039_sync_var.py::test_f039_r10_el_contenedor_pasa_el_numero…` ×2.
   Cambio permitido: **solo** sus dobles (Sigrid falso que acepte
   `parametros`, UoW con `vinculados`); ninguna aserción cambia.
3. **Nombres del design §7.2:** `recurso_vinculado` usa `empresa` y
   `fecha_baja`; se deshace la desviación `empresa_recurso`/`fecha_baja_recurso`.
   Lista cerrada ampliada con
   `test_f023_r1_empresa_solo_en_trabajador_y_obra` y
   `test_f026_r8_fecha_baja_solo_en_trabajador`: cambio permitido, **solo**
   admitir `recurso_vinculado` de forma explícita en su regla.
## F-044 · implementer (T1-T6 hechas, retomado en T7, 2026-10-26)

Contraste del design con el código tras unir F-062: los puntos de enganche
siguen (`_preflight`, `ejecutar`, `proponer`, `lecturas_lote`,
`_payloads`/`_trazar`, rutas de partida). Tarea en curso y decisiones: se
anotan aquí al cerrar cada tarea; detalle en `progress/impl_F-044.md`.

- T1 hecha (`domain/vinculados.py`).
- T2 hecha (ORM + `PgVinculadoRepository` + `upsert_asignacion_vinculado`).
  `recurso_vinculado` con `empresa` y `fecha_baja` del design §7.2
  (decisión 3 del humano; `01827e2`): `test_f023_r1…` y `test_f026_r8…`
  admiten `recurso_vinculado` de forma explícita (lista cerrada).
- T3 hecha, con el sync de vinculados **cableado en `deps.py`** (decisión 2
  del humano): pasos `FetchVinculadosStep`/`UpsertVinculadosStep` y
  `vinculados=` del preview; test nuevo del contenedor real. Los 11 tests de
  la lista cerrada solo cambian sus dobles: Sigrid falso con `parametros` y
  que devuelve [] a la SQL de `dbo.conext`, UoW con un `vinculados` vacío
  y, en `_config_prueba` de f023 (el doble de `cargar_config`), la sección
  `vinculados`, como hicieron F-030 y F-032 con las suyas. Además:
  `SigridGateway.leer` gana `parametros` opcional (el `?` de design §7.1) y
  la SQL lleva `dbo.` como las demás de `config.yaml`.
- T4 hecha: `VinculadoEntrada`, `LineaEntrada.vinculados`,
  `reglas_vinculados.py` (`partida_ci_del_tipo`, `partida_del_vinculado`
  con la CI como función perezosa y la validez de la elegida como dato) y
  `cuentas_del_presupuesto`. «`CI*`» del titular = el código empieza por
  `CI` (no `clasifica_categoria`, que da `OTRO` a `CICO13`).
- T5 hecha: `PasoVinculados.proponer` (`registro_vinculados.py`), salida
  `vinculados` solo si la petición los trae; `LineaPropuestaIn` gana
  `paride` y `vinculados` y `para_pipeline()` deja la línea de siempre sin
  ellos; el lote precarga las horas de los vinculados y comparte
  `cuentas_del_presupuesto` por obra. Titular con elegida que no es hoja
  activa ⇒ subfilas sin propuesta (en el preflight se omitiría con él).
- T6 hecha: `SubfilaVinculado` y `Linea.vinculados` (tras `partida_fija`:
  `test_f055_r13` fija los 5 últimos campos); el repositorio lee las
  subfilas de los vinculados activos y vigentes en el mes (2 lecturas más,
  ninguna sin vinculados) y `reemplazar` guarda las que tienen elegida o
  propuesta (la traza, como la del titular, no sobrevive a guardar).
  `CambiarPartida(vinculado_ide)` con evento `PARTIDA_VINCULADO`; cambiar la
  partida del titular borra las propuestas de sus subfilas (dependen de
  ella). Selector, preflight (`_guardar_propuestas` lee `vinculados` del
  preflight con `{registro_id, recurso_ide, paride, partida_*}`: **T13 debe
  devolver esa forma**) y cola del mes (cola aparte para subfilas, también
  bajo líneas de postventa; `estado` gana `subfilas` solo si hay). Salida:
  `LineaOut.vinculados` con `exclude_if` vacío (la línea de siempre sin
  vinculados: `CAMPOS_LINEA` de `test_f034_rutas` intacto).
- T7 hecha: columna «Tipo recurso» (`tipo`, entre Asignaciones y Partida;
  «Persona» en la fila de la línea) y una subfila por vinculado bajo su línea
  (`construirFilaVinculado`/`construirCeldaVinculado`: obra con el % de la
  línea sin editar, tipo y código, partida con `htmlPartida`). El selector de
  F-050 sirve a la subfila sin cambiar su firma: el ancla lleva
  `data-vinculado` y con él la clave, la consulta y el `PUT` llevan
  `vinculado_ide`. La cola del mes pasa `subfilas` a `aplicarPropuestas`.
  De la lista cerrada del front solo cambian `test_f050_subfilas.py` y
  `test_f050_m2_arreglos.py` (la columna nueva); los otros cinco no lo
  necesitaron.
- T8: las tres suites enteras en verde al cerrar el bloque 1 (api 1274,
  front 394, transfer 1478). La revisión intermedia es opcional (D15) y la
  decide el líder: el implementer no la lanza; sigue con el bloque 2.
- T9-T20 hechas (bloque 2, el registro). Decisiones y desviaciones:
  - **`omitidas` con `vinculado_ide`**: la entrada de un vinculado omitido
    lleva su recurso; la api (T18) no la aplica a la asignación del titular.
    Los vinculados escritos NO van a `escritas` ni `ya_registradas` (son por
    asignación): solo en `vinculados`.
  - **`PasoVinculados` en varios puntos del preflight** (R27: sus lecturas
    con las de los titulares): `decidir` tras la partida del paso 4,
    `_cuentas` del 4 bis, parte del 5, `registradas`/`idempotencia` en la
    lectura del 6, `sin_partida` en el 6 bis, `conflictos_del_parte` dentro
    del bucle del 7 (misma `lineas_del_parte`) y `cerrar` al final.
    `ejecutar`: `EscrituraVinculados` tras los titulares y su relectura.
  - **El titular no toma como suyo el pisado de un vinculado**
    (`_planear_ediciones` salta `c.vinculado`): hallado en GREEN de T14.
  - **Generalizados con el valor de hoy por defecto** (T11):
    `evaluar_capacidad(es_jornada)`, `pisables_al_cero(hora)`,
    `emparejar_ceros(clave, hora)`; `stmt_editar_linea`/`stmt_poner_a_cero`
    con `hora` (T12: sin ella, el SQL de hoy carácter a carácter).
  - **T12 → T15**: la precarga del lote para los vinculados se hizo en T15
    (horas, líneas, `synckey`/`hmores.ide`, partidas válidas, también VAR).
  - **Dobles cambiados (lista cerrada)**: `tests/conftest.py`
    (`_aplicar_ediciones` respeta `hora`; `EdicionesFalsas` con
    `cuentas_del_presupuesto` vacío), `test_f013_sin_partida.py::…r4…`
    (admite el campo `vinculado`), ANCLAS de `test_f002_fuente_unica.py`.
  - **T16**: desde T9 `asdict(Conflicto)` publicaba `"vinculado": null`;
    `_conflicto` lo quita (sin vinculados, la respuesta de siempre).
  - **T18**: la traza va en `application/traza_vinculados.py` (como
    `traza_incidencias.py`: `test_f003` vigila los `sigrid_*` de
    `registro_sigrid.py`); `subfilas_de` pasa a nivel de módulo
    (cuadrante y registro); la asignación va por subconsulta (sin línea, no
    inserta); en VAR la subfila no manda partida. `RegistroSigrid` gana
    `vinculados_desde` (de `config.yaml`, cableado en `deps.py`).
  - **T19**: `rotuloConflicto` sin `.filter(` (lo vigila `test_f049_r3`).
  - **T22**: 1.ª campaña (`bd38dc5`) con 81 supervivientes; 74 eran huecos
    reales y los matan los tests nuevos `tests/test_f044_mutacion.py` (api
    y transfer; comprobados uno a uno, anexo en
    `progress/mutacion_F-044_pasada1.md`). Campaña final (`38a53d0`):
    415/422, los 7 restantes equivalentes (tres `strict` de `zip`, una
    condición redundante, dos valores que no se leen con `elegida=None` y
    el invariante `existe` ⇔ `ide` de `ParteDestino`). La spec pide que el
    humano acepte cada justificación: **pendiente, lo lleva el líder**.
  - **T24**: `bash harness/init.sh` sin `[KO]` (cobertura 99,3 % de 1108
    líneas cambiadas; api 1308, front 403, transfer 1585).

### F-044 · T21: MANUAL del humano (ningún agente lo ejecuta)

Git Bash, desde `services/dedicacion-transfer` y con su `.venv`. **Primer
paso** (el modo del proceso que escribe):
`.venv/Scripts/python -c "from config.settings import get_settings as g; s=g(); print(s.obra_pruebas_forzar, s.obra_pruebas_cod)"`.
Debe dar `True 0404`; si no, **PARAR**. Transfer, api y front locales con
`OBRA_PRUEBAS_FORZAR=true`. Luego, el guion de `tasks.md` T21; los comandos
del script, ensayados en seco (argumentos aceptados, sin leer ajustes ni
Sigrid): `.venv/Scripts/python prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`
(solo lectura; ahora resume «Líneas de vinculados (porcentajes:vin:)») y,
para limpiar, `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar`
(en seco) y después `... limpiar --confirmar`. Ninguno lleva
`--permitir-modo-real`. Resultado real en `progress/manual_F-044.md`.

## F-062 · CERRADA y DESPLEGADA (2026-10-26): aviso a `partes` pendiente

Detalle de la implementación, las reviews y el MANUAL: `progress/history.md`,
`progress/impl_F-062.md`, `progress/review_F-062.md` y
`progress/manual_F-062.md` (secciones de F-062 retiradas de aquí al lanzar
la review de F-044). `azure-apps/dedicacion.md` `ff0acb4` y `64486fc`.

**Riesgos para el humano · aviso a `partes`** de F-062 (lo transmite el
humano; aquí no se toca `partes`): desde F-062 dedicación **mueve la `fec`**
de `CIZ` que no son suyos (también con `synckey partes:…`, sin cambiarla y
con guarda) para continuar una racha y la devuelve a su día si deja de
continuarla; **añade** `CIZ` en sus partes (el del inicio de la racha y,
para cerrarla, uno de M−1); y deja rachas **abiertas** a fin de mes, que el
papel de sv4 verá. Nunca borra. Su `partes.md` debería decirlo en su «qué
se rompe».

## F-044 · spec aprobada (2026-10-25)

- **Spec:** `specs/F-044-recursos-vinculados/` (requirements 149 líneas,
  design 248, tasks T1-T24). Rigor `critico`; toca **api** (vínculo en el sync,
  subfilas, elegida, contrato, traza), **transfer** (propone, decide y escribe)
  y **front** (columna, subfilas, selector, modal). Evidencia de Sigrid, solo
  lectura y solo agregados, rondas 1 y 2: `progress/explore_F-044_sigrid.md`.
- **Vínculo:** campo extendido «Recurso Asociado» (`conext.cod = '5'`, `valn`
  = `res.ide` del principal). **Partida:** la hoja CI cuya cuenta tiene la
  subcuenta del vinculado; en postventa, VAR y `CP*`, la del titular.
- **Todas las decisiones cerradas** (design §9.1 y §9.2): D1, D2, D4 («es la
  a.»), D7 y D8 con sus citas; D1b, D3, D4b, D5, D6 y D9-D15 con la opción A
  («ok a todo»). D1b se aplica en el sync: `tipos_excluidos: [VP]` no se
  vincula y el preview lo cuenta (R3); con `pre` 0, omitido con motivo (R14).
- **Hecho el 2026-10-26:** `dev` (con F-062) unido a la rama, `in_progress`
  e implementer lanzado; bloqueo antes de T7 resuelto («si a todo»); T1-T20, T22 y T24 hechas. T21 es MANUAL
  del humano en modo pruebas.
- **F-054:** trae solo las `M*` de trabajadores (por recurso, no por prefijo);
  los vinculados no son asignaciones; F-054 puede traer la partida de la línea
  del vinculado como elegida de su subfila (design §10). Lo diseña F-054.
- **Riesgos:** `MESVE` empieza por `M` (R19 y sus tests); la columna nueva
  puede tocar tests del front (el implementer PARA y pide ampliar la lista
  cerrada); **F-062 toca `registro_pipeline.py`**: implementar F-044 sobre
  `dev` con F-062 ya unida.
- **Aviso a `partes`** (lo transmite el humano, no se toca `partes`): desde
  F-044 dedicación escribe y edita en los partes compartidos líneas de
  recursos no persona (`synckey porcentajes:vin:…`), sin borrar nunca.

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

## F-061 · CERRADA y DESPLEGADA (2026-10-23): MANUAL pendiente

- **Propuesta de la review para `arnes-base`** (pendiente de PARADA 1 con
  el humano, no aplicada): en `CHECKPOINTS.md` C4 bis, si la lógica vive en
  JS u otro lenguaje sin puerta de mutación, una mini-campaña manual
  documentada (original → mutado, resultado).

- **Desplegada el 2026-10-23** (api → front; ver «Producción, hoy»).
  `azure-apps/dedicacion.md` `47c7c3c` (cabecera, §5 y §7: `palabras` y
  `orden_busqueda` en `GET /incidencias`, orden api → front, editar la
  lista exige redesplegar la api).
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

- **Desplegado el 2026-10-26: F-062**, los tres servicios en orden, uno a
  uno, lanzados por el humano con `infra/d.local.ps1 transfer|api|front`
  (envoltorio no versionado, `*.local.ps1`, que carga las variables y llama
  a `redeploy_dedicacion.ps1 -Solo …`): transfer `r20261026-0950`, api
  `r20261026-0955` y front `r20261026-1000`; revisiones
  `ca-dedicacion-transfer--r20261026095009`, `ca-dedicacion-api--r20261026095513`
  y `ca-dedicacion-front--r20261026100012`, las tres `RunningAtMaxScale`,
  `Healthy` y con el 100 % del tráfico. Transfer y api arrancaron sin
  errores; la api aplicó `ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS
  sigrid_dia_fin_antes SMALLINT` (1 sentencia DDL). El transfer sigue en
  **modo real** (`OBRA_PRUEBAS_FORZAR=false`). `infra/imagenes.json` al día
  en este commit. **Pendiente del humano:** Ctrl+F5 en el front; lanzar un
  «Sincronizar Sigrid» si el desplegable de incidencias sale vacío; y el
  **aviso a `partes`** (texto en «Riesgos para el humano»).
- **Desplegado el 2026-10-23: F-061**, api y front en ese orden con
  `redeploy_dedicacion.ps1 -Solo api,front` (lo lanzó el humano): api
  `r20261023-1235` y front `r20261023-1236`, revisiones
  `…--r20261023123457`, las dos `RunningAtMaxScale`, `Healthy` y con el
  100 % del tráfico (`az containerapp revision list`). La api arrancó sin
  errores (`containerapp logs`: «Application startup complete», o sea, la
  lista `palabras_extra` es válida). `infra/imagenes.json` al día en este
  commit. **Ojo:** el script actualiza `tag` y `publicado` pero no el
  `digest` de `imagenes.json` (el front publicado es `sha256:87f7b709…`, el
  fichero sigue con el anterior); deuda de `infra/`, no de F-061.
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
2026-10-20. F-051 cerrada y desplegada el 2026-10-21. F-030 cerrada y desplegada el 2026-10-22. F-061 cerrada y desplegada el 2026-10-23. Orden: **F-058** (un % que redondea a 0 no se registra), F-044, F-052, F-053, **F-054** (el sync trae los %
que ya hay en los partes de Sigrid; 2026-10-08), F-021, F-048, F-046, F-038, F-028, F-036, F-031, F-059, F-060,
F-033 y, detrás, F-017, F-018…

## ⚠ Lo que espera al humano

- **F-062: T19 y T20, MANUAL**, con sus comandos exactos en «F-062 · T19 y
  T20» (arriba), primer paso incluido (`True 0404` o PARAR).
  **Equivalentes de la mutación nº 14 (`rachas.py:113`) y nº 23
  (`rachas.py:528`): ACEPTADOS** por el humano el 2026-10-24 («ok a 1 y
  2»), con la condición de que la campaña nueva los repita y sigan siendo
  equivalentes: **se cumple** (campaña 2 sobre `44841b8`: los mismos dos, aquí
  nº 6 y 7, vivos en serie y con demostración ejecutable original == mutado;
  ningún equivalente nuevo; `progress/mutacion_F-062.md`).

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
  la herramienta, vale para cualquier proyecto ⇒ `arnes-base`. **Se repite
  en F-062** (O1 de su review 1): el nº 1 de la campaña 1 y 5 de la api en la
  campaña 2 sobreviven en paralelo y mueren en serie; causa sin localizar,
  podría dar también muertos falsos. Hasta arreglarlo, en `critico` los
  supervivientes se reproducen en serie. Y la automejora de la review 1 de
  F-062 para `reviewer.md`/C4: ejecutar en seco los MANUAL contra las
  funciones puras o leer el script que invocan, y comprobar el modo en el
  proceso que escribe, no en un `/health`. Y la
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
