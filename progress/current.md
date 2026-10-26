<!-- progress/current.md -->
# Trabajo en curso

**En curso: F-044** (aplicar los porcentajes también a los recursos
vinculados al trabajador; `sdd: true`, rigor crítico), **`in_progress` desde
el 2026-10-26**, en el worktree `porcentajes-f044`, rama
`feature/F-044-recursos-vinculados`, con `dev` unido (F-062 incluida). Spec
APROBADA por el humano el 2026-10-25 («ok a todo»), en
`specs/F-044-recursos-vinculados/`. Implementer lanzado el 2026-10-26; su
informe irá en `progress/impl_F-044.md`. Escribe en Sigrid solo vía el
transfer y **solo en modo pruebas** (0404, `PRUEBA-PORC`); ninguna escritura
real. **Pendiente del humano (de F-062, ya desplegada el 2026-10-26):** el
**aviso a `partes`** (texto en «Riesgos para el humano», más abajo).
**Después:** F-054 (spec aprobada, worktree `porcentajes-f054`).

## F-044 · implementer (en curso, 2026-10-26)

Contraste del design con el código tras unir F-062: los puntos de enganche
siguen (`_preflight`, `ejecutar`, `proponer`, `lecturas_lote`,
`_payloads`/`_trazar`, rutas de partida). Tarea en curso y decisiones: se
anotan aquí al cerrar cada tarea; detalle en `progress/impl_F-044.md`.

- T1 hecha (`domain/vinculados.py`).
- T2 hecha (ORM + `PgVinculadoRepository` + `upsert_asignacion_vinculado`).
  **Desviación**: las columnas `empresa` y `fecha_baja` de
  `recurso_vinculado` (design §7.2) se llaman `empresa_recurso` y
  `fecha_baja_recurso`: `test_f023_r1_empresa_solo_en_trabajador_y_obra` y
  `test_f026_r8_fecha_baja_solo_en_trabajador` aseveran que ninguna otra
  tabla tiene esas columnas y no están en la lista cerrada. Se le pregunta
  al humano en el bloqueo de T7 (mantener el nombre o ampliar la lista).
- T3 hecha salvo el **cableado en `deps.py`** (`FetchVinculadosStep`,
  `UpsertVinculadosStep` y `vinculados=` del preview): cableado, rompe 11
  tests fuera de la lista cerrada, que construyen el contenedor real con un
  Sigrid falso sin `parametros` y una UoW sin `vinculados`
  (`test_f023_sync_empresa.py` ×5 `r18_*`, `test_f025_sync_postventa.py::
  test_f025_r12_el_contenedor_comparte_un_solo_transfer`,
  `test_f030_catalogo.py::test_f030_r3_el_sync_y_el_preview_reales_usan_la_consulta_de_config`,
  `test_f032_empresas_sigrid.py` ×2 `r1_el_sync_real…`/`r4_el_preview_real…`,
  `test_f039_sync_var.py::test_f039_r10_el_contenedor_pasa_el_numero…` ×2).
  Revertido; va a la pregunta del bloqueo de T7. Además: `SigridGateway.leer`
  gana `parametros` opcional (el `?` de design §7.1; antes mandaba `[]`
  siempre) y la SQL lleva `dbo.` como las demás de `config.yaml`.

## F-062 · review 1: arreglos (implementer, 2026-10-24)

Review 1 RECHAZADA (`progress/review_F-062.md`); los 6 bloqueos, arreglados:
- **B1** (`453f870`, `441e6a3`): R5 literal también para el inicio propio
  (`rachas.py`, `==` y no `<=`; test RED). El script da a la n-ésima
  `--incidencia` el id `990101 + (mes−1)·100 + n` (julio 9907xx, octubre
  9910xx): estable en el mes, distinto entre meses; `verificar` pide los
  del mes (`--mes`); `limpiar` ya borraba por marca y prefijo, de todos los
  meses. Ids esperados al día en `test_f030_pipeline_incidencias.py` (lista
  cerrada; sus `verificar` llevan `--mes 7`) y en los de F-062.
- **B2** (`441e6a3`): `medir --cierres R` designa R en la **primera** obra
  (como `_designar_cierres`), en lote y obra a obra; sin `--cierres`, las
  peticiones de siempre. **Decisión**: designar solo con `--cierres` y no
  siempre, porque `test_f055_medicion.py` (fuera de la lista cerrada) fija
  la forma `(obra, lineas)` del lote; la review admitía «o `--cierres` en
  lote». Un `--cierres` que no es `--recurso` es error de argumentos.
- **O2** (`441e6a3`; aprobada por el humano el 2026-10-24, «ok a 1 y 2»):
  `ejecutar`/`limpiar --confirmar` con `OBRA_PRUEBAS_FORZAR=false` salen con
  código 1 y sin escribir (ni leer, en `limpiar`), salvo
  `--permitir-modo-real`. Desviación aprobada. Ningún test ajeno la fijaba.
- **B3/B4**: T19 y T20 con el primer paso del modo y sus comandos exactos
  (abajo); `tasks.md` T21 `[x]` (`ff0acb4` en `azure-apps`, `fb351e0`).
  Ensayados en seco contra las funciones puras con los ids nuevos: lo
  esperado de (1)-(4) sale tal cual.
- **B5** (`743923b`): la condición de `_cierres_a_escribir`, entre paréntesis.
- **B6 y O3** (`77bf5d6`): «decidir la racha»; `#regla-incidencia` dice que
  en pruebas también la lectura por `ide` es de la 0404 y que no se mezclan
  modos sobre la misma base (una quitada se borraría en PostgreSQL).
- **Campaña 2** (RM1, HEAD `44841b8`): 609 / 598 muertos / 11 vivos. En
  serie: 5 falsos de la api (caen con tests que ya había: O1 otra vez, para
  el líder), 4 del script con test nuevo (`2f04d28`) y los 2 equivalentes
  aceptados. Detalle en `progress/mutacion_F-062.md`.

### F-062 · T19 y T20: HECHAS, cumplen (resultado en `progress/manual_F-062.md`)

Git Bash, desde `services/dedicacion-transfer`. **Primer paso de T19 y de
T20** (el modo del proceso que escribe, el del script; siempre con el
`.venv` del transfer, nunca el `python` del PATH):
`.venv/Scripts/python -c "from config.settings import get_settings as g; s=g(); print(s.obra_pruebas_forzar, s.obra_pruebas_cod)"`.
Debe dar `True 0404`; si no, **PARAR**. Ningún comando lleva
`--permitir-modo-real`.

**T19** (solo lectura, R20) — **HECHA el 2026-10-25 por el humano, cumple** (`progress/manual_F-062.md`):
1. En `dev` (allí no hay `--cierres`): `.venv/Scripts/python prueba_escritura_porcentajes.py medir --lote --ano 2026 --mes 9 --obra 0694 --obra 0696 --recurso 1705036`
2. En la rama: `.venv/Scripts/python prueba_escritura_porcentajes.py medir --lote --ano 2026 --mes 9 --obra 0694 --obra 0696 --recurso 1705036 --cierres 1705036`
3. Esperado: el `TOTAL … s en total` de la rama ≤ 1,15 × el de `dev`, y en
   la rama **una** línea `lectura incidencias_en_ventana:` en el lote (en
   seco, con los dobles: sin `--cierres`, cero lecturas; con él, una). Si
   no, **PARAR**.

**T20** (escritura en modo pruebas, obra `0404`, transfer LOCAL; `RECURSO`
con `CIV` y `CIZ` en `reshor`). Resultado real en `progress/manual_F-062.md`.
1. C1 y C2.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9`: `CIV` el 5 y `CIZ` el 9 (`porcentajes:inc:991001:ini|fin`).
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9 --incidencia RECURSO:CIV:12:16`: `fin editar` del mismo `CIZ` al 16; la 991002 `continua`; ningún inicio nuevo.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py verificar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9 --incidencia RECURSO:CIV:12:16`: `porcentajes:inc:991001:fin` con el **mismo** `hmores.ide` y `fec=20261016`.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar`
2. C3.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:27:31`: `CIV` el 27; `fin abierta`, sin `CIZ`.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 11 --incidencia RECURSO:CIV:2:6`: `ini continua`, sin inicio, y `CIZ` el 6 en el parte de **noviembre** de la `0404` (`porcentajes:inc:991101:fin`).
   - `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar`
3. C4.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:27:31`
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 11 --cierres RECURSO`: `CIERRE … escribir`, `CIZ` el 31 en el parte de octubre, sin `--pisar` (inicio en M−1), `porcentajes:inc:991001:fin`.
   - Repetir los dos: nada nuevo (`ya_registrado`). Luego `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar`
4. C12 y C13.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 9 --incidencia RECURSO:CIV:15:30`: `CIV` el 15 de septiembre, abierta.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:1:31`: `continua` y `abierta`, nada escrito.
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 11 --cierres RECURSO`: nada escrito y `PENDIENTE cierre:{ide}: relanza con --pisar cierre:{ide}` (`{ide}`, el del `CIV` del 15).
   - `.venv/Scripts/python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 11 --cierres RECURSO --pisar cierre:{ide}`: `CIZ` el 31 de octubre en el parte de octubre de la `0404` (`porcentajes:inc:990901:fin`).
   - `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar`
5. C10, navegador local. Aquí escribe el transfer servidor (otro proceso):
   antes, `curl -s http://localhost:8006/health` debe decir
   `"modo_pruebas": true`; si no, **PARAR**. Registrar 5-9, quitarla del
   cuadrante y abrir Registrar: «No coincide con Sigrid» con las dos
   líneas; Cancelar. Al final, `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar`

## F-062 · implementación (implementer, 2026-10-24)

- **Implementación terminada** (T1-T18, T5c y T22; informe en
  `progress/impl_F-062.md`). T21 la hizo el líder (`ff0acb4` en
  `azure-apps`, ver «Riesgos para el humano»).
- Historia: el bloqueo de T13 se resolvió con D18 (`ca6c4ef`).
- **Decisiones y desviaciones** (detalle en `progress/impl_F-062.md`):
  T2 adelanta de T7 los campos `obra_ide` y `dia_fin_antes` de
  `IncidenciaEntrada` (los necesita `propias`); T3, los de
  `LineaIncidenciaSigrid` (`obride`, `cenide`, `paride`, `caaide`,
  `parte_emp`), que necesita R10; T4, los de `AccionIncidencia`
  (`synckey_leida`, `can_leido`, `ajena`, `hmoide_destino`, `obride`,
  `cenide`) y las acciones `continua`/`abierta` y el rol `devolver`.
  T4: la «cubierta» es `ya_registrado` con la `fec` del `CIZ` ajeno; el
  aviso R21 deja el `fin` en `abierta`; si la guarda R9 o la base (R26)
  omiten, no hay resumen de racha.
  T5 (D14 = B; no llegó enmienda del líder, se implementa la spec): la
  empresa y la obra de pruebas del parte de M−1 se miran en el parte del
  inicio (misma obra; `ParteSigrid` no trae `emp`); una racha que una
  cadena de M continúa según `previa` no se cierra aunque la cadena omita;
  `ya_registrado` = cerrada el último día de M−1 con la `synckey` de
  cierre. `PREFIJO_CIERRE` se adelanta de T6.
  T5b: `no_coincide` da un elemento `quitada` por quitada, también sin
  líneas (`en_sigrid` vacío: la api la borra; el front no lo pinta, «sin
  aviso»); una racha con alguna línea explicada (propia, de quitada o de
  la previa) no sale entera como `solo_sigrid`; `PlanCadena.previas` da
  los `ide` de la previa que la cadena continúa.
  **Desviación T6**: `reconciliar` se borra en T9, no en T6: su único
  llamador es `_reconciliar_incidencias` del pipeline, que sustituye T9;
  borrarlo antes deja la suite del transfer en rojo entre commits. Sus
  tests ya están reescritos a F-062 (lista cerrada). `no_editar_el_par`
  ya iba «por cadena»: todas las `editar`/`devolver` de una cadena llevan
  el `id` de la dueña; cambian su docstring y `MOTIVO_INC_PAR`. La guarda
  R9 solo cuenta líneas `CI*`/`CIZ`.
  T7: el contexto del mes (`ContextoRachas`) viaja en el pipeline
  (`RegistroPipeline(contexto=…)` / `con_contexto`), no como parámetro de
  `ejecutar`: `test_f013_sin_partida.py` (R3) fija su firma y no está en
  la lista cerrada. La respuesta lleva `rachas`, `cierres_racha` y
  `no_coincide` solo si la petición traía alguna clave nueva; `ajena`
  solo cuando es cierta; los cierres, sin `synckey`, `hmoide`, `obride`,
  `cenide`, `paride` ni `caaide`.
  T8: `incidencias_del_mes` sigue hasta que T9 y T12 quiten sus
  llamadores (luego se borra con sus tests de la lista cerrada);
  `ventana(ano, mes, n)` en `rachas.py`; `INCIDENCIAS_MESES_ATRAS` también
  en `.env.example`.
  T9: `_decidir_rachas` y `_cierres_racha` sustituyen a
  `_reconciliar_incidencias`; se borran `reconciliar` y sus ayudantes
  (`MOTIVO_INC_DUPLICADA` queda hasta T11: lo importan sus tests). Un
  cierre D14 sin `CIZ` en `reshor` del recurso, solo aviso. La hora y el
  precio del `CIZ` del cierre (`hora_ide`, `pre`) no salen en la
  respuesta. `LecturasDelLote` gana `incidencias_en_ventana` y
  `partes_de_periodos` directos a Sigrid (la memoria y la ronda D, en
  T12). Las fixtures de app de la lista cerrada (y la propia) añaden
  `incidencias_meses_atras` a `AJUSTES`. **Rojo intermedio, previsto**:
  37 tests de la lista cerrada (`test_f030_pipeline_incidencias.py`,
  `test_f030_r30_editar.py`, `test_f030_r30_punta_a_punta.py`) fallan
  porque sus dobles leen con `incidencias_del_mes` o fijan la semántica
  de F-030; se reescriben en T10-T12 y T16.
  **T12 antes que T10-T11** (orden cambiado): se hizo mientras el
  spec-author escribía D17, porque el lote no toca `ejecutar`. Lo que lee
  una petición sale de `rachas.lectura_de_peticion`, el mismo en suelto y
  en lote, y así la memoria lo sirve entero. En el lote hay una lectura por
  obra de pruebas (o ninguna), con la unión de recursos, de `ide` y de
  ventanas; la memoria filtra como el SQL (recurso, ventana y `CI*`, o
  `ide`). La ronda D lee `partes_de_periodos` de M−1 solo si hay cierres
  D14. Para no pedir de más, el lote decide si lee con
  `decidir_incidencia`, que da un superconjunto de lo que lee el pipeline.
  Se quita `incidencias_del_mes` del lote. El del cliente, con sus tests,
  se va en T11, junto con los de la memoria del lote de F-030 en
  `test_f030_pipeline_incidencias.py` y `test_f030_r30_editar.py`, que
  fallan hasta entonces: ahora son 42 en rojo, todos de la lista cerrada.
  El `incidencias_en_ventana` falso de `conftest.py` devuelve en el orden
  de la consulta (`fec`, `ide`).
  T10: el `INSERT` de un `CIZ` en el parte del inicio (R5) y el de un
  cierre (R12) llevan una `ObraEntrada` con el `obride` y el `cenide` de
  la línea leída (`_obra_de_linea`), y `ano`/`mes` del día que se escribe.
  El cierre lleva `can = 0` y el `pre` de la hora `CIZ` del recurso. Se
  escriben después de los `INSERT` de la petición, con el `max_pos` de su
  parte. `_cierres_a_escribir(pf, pisar)` hoy devuelve los `escribir`;
  queda preparado para el filtro de `pisar_claves` de T5c (R31), que no
  se hace aquí. Un cierre que no se encuentra al releer se queda sin
  `hmores_ide`, igual que una incidencia (F-030).
  T11: `ClienteInc` lee con `incidencias_en_ventana` (sobre
  `existentes`) y anota `(recursos, desde, hasta, obra de pruebas)`. Las
  líneas de los dobles en pruebas llevan `obride` 828942. Se reescriben,
  citando su R de F-062, los de R27 (ahora R9 y R19), la de 1-31 (R7,
  `abierta`) y los de ejecutar y lote. Los de cliente y memoria de
  `incidencias_del_mes` se sustituyen por un puntero a
  `test_f062_cliente_ventana.py` y `test_f062_lote.py`, y la lectura se
  borra del cliente. Se hace también en `test_f030_r30_editar.py` (está
  en la lista cerrada), donde el `UPDATE` esperado lleva `can_leido`. En
  rojo solo quedan los dos de `test_f030_r30_punta_a_punta.py` (T16).
  T13: `campos_de_traza` manda `dia_fin_antes` solo si lo hay y lo lee con
  `getattr`. Sin día original, la traza es la de F-030 tal cual. Así los
  dobles `SimpleNamespace` de `test_f030_registro.py`,
  `test_f030_r30_identidad.py` y `test_f030_r30_punta_a_punta.py` no
  cambian: los dos últimos no están en la lista cerrada para eso. En la
  api, 1149 en verde.
  T14: la respuesta de la api conserva `incidencias_quitadas` (el front
  deja de pintarla en T17). La quitada con traza que crea la petición de
  su obra (R24) la deja sin líneas ni incidencias: el transfer saca la
  empresa también de `quitadas` (`_preflight` y precarga del lote), si no
  la omitiría entera y no devolvería el `CIZ` (R17; test propio). La
  condición de «tiene algún `ide`» mira la traza ya calculada
  (`hmores_ide_*`), no las columnas: `test_f003_esquema.py` R17 fija los
  `sigrid_*` que nombra `registro_sigrid.py`. Ajeno cambiado: solo
  `test_f030_r23_sin_incidencias_la_peticion_de_siempre` (+`cierres_recursos`).
  T15: `continua`/`abierta` son `registrado` sin tocar el `ide` ni el día
  de su rol (no los anulan) y sin quién/cuándo (solo `escribir`/`editar`);
  el parte, el de la primera con línea. `devolver` hecho = `editar` o
  `ya_registrado`; omitido no toca nada. La quitada con `en_sigrid` vacío
  NO se borra si le queda un `devolver` sin hacer (su traza hace falta
  para devolverlo la próxima vez). El cierre `ya_registrado` no toca la
  traza (la spec dice «escrito»). Ningún test ajeno cambia: los de la lista
  cerrada de `test_f030_registro.py` siguen en verde tal cual, y el de «la
  quitada no va al transfer» (está en `test_f030_r30_identidad.py`, fuera
  de la lista) también: sigue sin ir en `incidencias`.
  T16: `f062_rachas.json` en tres escenarios encadenados en la api (c2;
  c6 y c9; c10 y borradas a mano); el transfer ejecuta cada paso por HTTP
  sin modo pruebas, desde el Sigrid del contrato. En las `escribir`, el
  contrato fija el `hmores_ide` que traza la api y el transfer solo exige
  que no sea nulo. `f030_r30.json`: la petición gana `incidencias_mes` y
  `cierres_recursos` (la api llama a `_designar_cierres`, como `ejecutar`)
  y el doble del transfer lee la ventana; lo esperado no cambia. Lectura
  de «6-9 y 12-14 = una cadena» (tasks T16): cada caso es una cadena de
  una sola incidencia (la 7); en el contrato no hay una 8. Ambos pasan a
  la primera: prueban T9-T15 ya hechos (sin fase RED propia); comprobado
  que fallan al cambiar un dato del contrato (`dia_fin_antes` 7 → 8).
  T17: `seccionQuitadas` se borra de `app.js` (R25: la sustituye
  `pintarNoCoincide`, tras las obras, solo con elementos con líneas). En
  `test_f030_r30_front.py` salen los dos tests de esa lista (el de su
  contenido y el de su sitio en `pintarModalPreflight`) y su ayudante,
  con un puntero a los de F-062: los dos son «el de la lista de quitadas
  del modal» de la lista cerrada. `textoLineaIncidencia` aprende
  `continua`, `abierta` y el rol `devolver` («se devuelve»).
  T18: el script ya admitía varias `--incidencia`; ahora lleva el
  contexto (`--cierres`, repetible, a `cierres_recursos`) e imprime RACHA,
  CIERRE y NO COINCIDE. **Decisión**: una petición con solo
  `cierres_recursos` no tiene periodo ni empresa (`lectura_de_peticion`
  los saca de líneas e incidencias), así que `--cierres` sin
  `--incidencia` manda por recurso una línea testigo al 0 % (P3 la omite
  siempre; nunca se escribe), como las que el recurso tendría en el
  cuadrante. **Arreglo de T9** visto en el script: la racha que abre o
  cierra con una línea nueva no llevaba parte (`rachas.py` solo ve los de
  Sigrid); `_partes_de_rachas` le pone, tras el paso 5, el de su línea
  (test propio con fase RED). Docs: `#regla-incidencia` reescrita (los
  textos que fija `test_f030_r34_la_regla_dice_cambiar_los_dias_y_quitar`
  siguen, sin tocar ese test) e `INTEGRACION.md` §1 (fila de `sigrid-api` y
  parte compartido), §3 (`INCIDENCIAS_MESES_ATRAS`) y §5;
  `test_f002_fuente_unica.py` gana `test_f062_r27_…` (tarea T18).
  T5c (R31, D17): `CierreRacha` gana `requiere_confirmar` (inicio anterior
  al día 1 de M−1) y `clave` (`cierre:{ide del inicio}`); `ejecutar` deja
  `pendiente` el que no trae su clave (motivo con la clave, sin escribir,
  fuera de `pendientes_confirmacion`). La api ya no tocaba el `fin` con un
  `pendiente` desde T15 (solo `escribir`): su test r31 pasó a la primera,
  sin fase RED (dicho en el informe). Front: casilla `chk-pisar` en el
  `escribir` que pide confirmar y el aviso de `registroEjecutar` cuenta los
  `pendiente`; script: `PENDIENTE cierre:{ide}: relanza con --pisar …`.
  El comentario del front no dice «pisado»: `test_f013_r4_…` prohíbe esa
  palabra fuera de `rotuloConflicto`.

## F-062 · spec escrita (spec-author, 2026-10-24; revisada el mismo día)

Spec en `specs/F-062-rachas-incidencias/` (requirements 150/150, design
250/250, tasks T1-T22 + T5b; `python -m harness.tamano --feature F-062` en
verde). **Revisión del 2026-10-24** por la decisión del humano («si las
quite de la plataforma y al registrar me debe avisar de que no coincide con
sigrid para editarlo»): F-030 D11/R38 pasan a R17. La quitada sigue
`quitada`, pero viaja al transfer en `quitadas`, y el preflight devuelve el
bloque `no_coincide` con las líneas que siguen en Sigrid (código, día,
parte, `ide`), sin escribir nada, para que el humano las edite a mano. El
`CIZ` ajeno que movió se sigue devolviendo solo (D10), y cuando ya no queda
ninguna línea en Sigrid, la api borra la quitada. Los casos C1-C11 viven
ahora en `tasks.md` §Casos, por el tope de líneas.
El estado en `features.json` **no** se ha tocado: lo cambia el líder.
Qué hace: el transfer decide por **cadena** (incidencias pegadas del mismo
recurso y código en el mes) si abre, continúa o cierra una racha, mirando
las `CI*`/`CIZ` del recurso en todos los partes. La api le manda el
contexto del mes (`incidencias_mes`, `cierres_recursos`, `quitadas`) y el
front solo pinta. Qué de F-030 se conserva y qué se reemplaza: requirements
§1. Los casos C1-C11 son los ejemplos del humano y de la evidencia.

**Decisiones DECIDIDAS por el humano el 2026-10-24** («ok a lo demas»;
«adelante, en d14 b»; requirements §10). Todas A salvo D14 = B, ya aplicadas
en requirements, design y tasks:
- **D5**: cada `CIZ` cierra el inicio abierto más reciente.
- **D6**: ventana de 12 meses hacia atrás (configurable,
  `INCIDENCIAS_MESES_ATRAS`) y el mes siguiente solo para avisar.
- **D7**: un tramo al que solo le quedan sábados y domingos llega a fin de
  mes (27-30 de octubre queda abierta).
- **D8**: una racha pegada cuyo `CIZ` es del mes anterior: se abre otra y se
  avisa.
- **D9**: si la regla pidiera quitar una línea ya escrita, no se une y se
  avisa.
- **D10**: quitar o recortar una incidencia que movió un `CIZ` ajeno se lo
  devuelve con un `UPDATE` (columna nueva `sigrid_dia_fin_antes`).
- **D11**: incidencias pegadas en obras distintas forman una cadena, en la
  obra de la primera (sin 422 en la api).
- **D12**: un `CIZ` ajeno con `can = 1` se mueve igual.
- **D13**: una línea ajena dentro del tramo ⇒ `omitir`.
- **D14 = B**: una racha abierta desde antes del mes anterior que M no
  continúa se cierra con un `CIZ` el último día de M−1, en el parte de M−1
  de la obra del inicio (En registro, de la empresa y, en pruebas, la 0404,
  el de mayor `ide`, sin crear ninguno), con el centro, la partida y la
  cuenta del inicio y `can = tot = 0`. Sin parte válido, solo aviso (R12,
  R13, caso C12). Cuesta una lectura de partes de M−1, solo en ese caso.
  **Ojo**: también cierra los inicios viejos que nunca se cerraron (E-11: 9),
  y se ve en «Cierres de rachas» antes de ejecutar.
- **D15** (nueva): las `CI*`/`CIZ` del mes que están en Sigrid pero no en la
  plataforma también salen en `no_coincide` (`solo_sigrid`). Solo salen en la
  petición designada del recurso, sin escribir y sin lecturas nuevas.
- **D16** (nueva): al quitar una incidencia no hay más edición automática que
  el `devolver` de D10; lo demás es solo aviso. La B sería mover el inicio de
  la dueña de una cadena al día de la siguiente.

Riesgos para el humano: hay escritura nueva en partes ajenos (mover la `fec`
de un `CIZ` de Administración o de `partes`, y añadir uno en su parte),
siempre con la guarda de F-051/D16. Sale **una lectura más por lote** en el
preflight, que se mide en T19 (≤ 15 %). T19 y T20 son MANUAL del humano.
**T21 hecha por el líder** (2026-10-24): `azure-apps/dedicacion.md`
`ff0acb4` (cabecera «pendiente de despliegue», §1, §3
`INCIDENCIAS_MESES_ATRAS`, §5 contrato y columna
`incidencia.sigrid_dia_fin_antes`, §7 orden transfer → api → front y
rachas compartidas con `partes`). **Aviso a `partes`** de F-062 (lo
transmite el humano; aquí no se toca `partes`): desde F-062 dedicación
**mueve la `fec`** de `CIZ` que no son suyos (también con `synckey
partes:…`, sin cambiarla y con guarda) para continuar una racha y la
devuelve a su día si deja de continuarla; **añade** `CIZ` en sus partes
(el del inicio de la racha y, para cerrarla, uno de M−1); y deja rachas
**abiertas** a fin de mes, que el papel de sv4 verá. Nunca borra. Su
`partes.md` debería decirlo en su «qué se rompe».

## Antes de F-062

**F-061** (búsqueda predictiva en el
desplegable de incidencias; `sdd: false`, rigor estándar) **cerrada
(`done`) el 2026-10-23**, review 2 APROBADA (`3a55dfb`), rama
`feature/F-061-busqueda-predictiva-incidencias` unida a `dev`;
**desplegada el 2026-10-23** (api → front, lo lanzó el humano; ver
«Producción, hoy»); `azure-apps/dedicacion.md` `47c7c3c`. Api y front; ni
transfer ni Sigrid. **Pendiente del humano:** el MANUAL de F-061 (abajo).
**F-044** (recursos vinculados) **`spec_ready`, SPEC APROBADA por el humano el
2026-10-25** («ok a todo») en el worktree `porcentajes-f044` (rama
`feature/F-044-recursos-vinculados`): **en espera de que cierre F-062** (solo
una `in_progress`; las dos tocan `registro_pipeline.py`).

## F-044 · spec aprobada (2026-10-25): en espera de F-062

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
- **Siguiente paso:** cuando F-062 esté `done` y unida a `dev`, rebasar la
  rama de F-044 sobre `dev`, pasarla a `in_progress` y lanzar el implementer
  (empieza por T1). T21 es MANUAL del humano en modo pruebas.
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
