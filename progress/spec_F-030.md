<!-- progress/spec_F-030.md -->
# F-030 · Informe del spec-author (2026-10-20; anexo R30, 2026-10-21)

Rama `feature/F-030-dias-bajas-incidencias`, copia
`C:\Users\pgris\PycharmProjects\porcentajes-f030`. Spec en
`specs/F-030-dias-bajas-incidencias/`: requirements (R1-R35, 150/150 líneas),
design (250/250), tasks (T1-T21; bloque A captura T1-T9, bloque B registro
T10-T18, docs T19, MANUAL T20, init T21). `python -m harness.tamano --feature
F-030`: dentro de los topes.

## Anexo R30 (spec-author, 2026-10-21)

Encargo del líder tras la review 1 (RECHAZADO, obs. 1) y la opción **C** del
humano («c», 2026-10-21): al cambiar los días de una incidencia ya registrada
se **editan en Sigrid las fechas de sus dos líneas**, como F-051 con los %;
nunca un segundo par. Copia `porcentajes-f030`, rama
`feature/F-030-dias-bajas-incidencias`, base `90d83eb`. **No se ha tocado
código** ni leído Sigrid (no hacía falta: las columnas y el patrón ya están
en el cliente de F-051).

### Qué cambia en la spec

- **requirements.md**: R30 reescrito («edita sus líneas, nunca escribe otro
  par»); **§8 nuevo con R36-R49**; §7 con **D11-D15 abiertas**; R17, R20,
  R21, R23, R27, R31, R33-R35 remiten a lo nuevo. Para caber en 150 líneas se
  ha **apretado la redacción** de R1-R35 sin quitar ningún requisito ni
  cambiar su sentido (la lista de D1-D10 queda en una línea: su texto está
  más abajo, §«D1-D10»).
- **design.md**: §13 nuevo (api, transfer, front, docs, SQL, punta a punta,
  lista cerrada); §11 = D11-D15; §12 riesgos al día; §4 con lo que el anexo
  no toca; §6 con los campos nuevos del contrato. **§2, §3, §5 y §10-§11 de
  antes (ya implementados o decididos) se han movido sin cambios** a este
  informe (secciones del final) y el design guarda su resumen con los mismos
  números de sección.
- **tasks.md**: **T22-T37** (tests primero; T37 = `init.sh` + mutación nueva
  en serie) y **T20 ampliada** con el cambio de días (mismo `ide`).
- Topes: `python -m harness.tamano --feature F-030` → requirements 150/150,
  design 243/250.

### Cómo queda (en una línea por servicio)

- **api**: el `id` viaja en el PUT y la fila se conserva al cambiar días
  (R36); quitar una registrada la deja `quitada` (R38, D11); la traza guarda
  por rol `ide` y día registrados y los manda al transfer (R39); deshacer
  repone `id` y traza (R47).
- **transfer**: localiza lo nuestro por `hmores.ide` o `synckey` en la misma
  lectura de R33 (R40); `editar` = `UPDATE hmores SET fec` con la guarda de
  F-051 cambiando `LIKE 'M%'` por el código exacto (R41); omite si la línea
  está cambiada a mano, en un parte cerrado o el día nuevo ya está ocupado
  (R42-R44); relectura única antes y después, nunca un par a medias (R45);
  log con lo que tenía (R46).
- **front**: manda `id` y recoge los de las nuevas (R37); pinta la quitada y
  dice «se cambia del d al d» (R38, R46).

### Decisiones abiertas para el humano (requirements §7, design §11)

- **D11 · Quitar una registrada** (nunca se borra). A: 422 hasta F-033.
  **B (rec.)**: queda `quitada` en la api (no se borra la fila), sale tachada
  «quitada · sigue en Sigrid» y el modal de registro la lista para retirarla
  a mano; deshacer la repone. C: se borra en la api con un aviso único.
  *Por qué B*: una línea `CI*` ya está a `can` 0, así que no hay forma
  «neutra» de dejarla: retirarla es borrarla, y el registro no borra. Con A
  el usuario queda bloqueado (unas vacaciones anuladas) y, si Administración
  borra el par a mano, el siguiente registro lo reescribe (R42, como F-051
  R17): no hay salida hasta F-033. Con C las líneas quedan huérfanas sin
  rastro tras el aviso. B cuesta un booleano, una subfila tachada y una lista
  en el modal.
- **D12 · Cambiar el tipo** (CIV → CIE). **A (rec.)**: quitar + nueva, que
  es lo que ya hace el chip (✕ y elegir otra). B: editar `horide` y `pre` del
  inicio en su sitio (F-051 edita la hora de las `M*`), pero pide un gesto
  nuevo en el chip; si se quiere, feature aparte.
- **D13 · Pasarla a otra obra.** **A (rec.)**: quitar + nueva. B: mover sus
  líneas de parte, que [`#regla-cero`] no permite (no cambia parte, obra ni
  centro) sin borrar. Con A y los mismos código y días, R27 omite la nueva
  («ya está en el parte X») hasta que se retire la vieja: no hay duplicado.
- **D14 · Línea nuestra cambiada a mano en Sigrid** (otra `fec`, código o
  `can`). **A (rec.)**: Sigrid manda: no se toca y el motivo lo dice; para
  igualar, se ponen en el cuadrante los días de Sigrid (pasa a
  `ya_registrado` y la traza se iguala). Es lo que hace F-051, que da por
  registrada la línea nuestra aunque Administración le cambie el `can`. B:
  el cuadrante manda (se edita igual; el log guarda lo que tenía). En las
  dos, una línea **borrada** a mano se vuelve a escribir (F-051 R17).
- **D15 · El día nuevo ya tiene una línea ajena igual** (mismo recurso,
  código y `fec`). **A (rec.)**: esa línea no se edita y se avisa (R27: nunca
  dos iguales en el mes). B: se edita igual.

Mientras no se decidan, **no se empieza T22** (tasks.md lo dice); las tareas
siguen la recomendada.

### Mes partido (D3)

Una incidencia no cambia de mes: sus días están siempre dentro de su periodo
(R19). Un tramo que cruza meses son dos incidencias, una por periodo, cada
una con su `CIZ`. Cambiar el tramo es, por tanto: editar el par de cada mes
afectado (R41); alargarlo a un mes nuevo, una incidencia nueva allí; y
acortarlo hasta dejar vacío un mes, quitar la de ese mes (R38, D11). Ni
`ano` ni `mes` de `hmores` se tocan (R48).

### El test de punta a punta (obligatorio, T22 y T33)

Los servicios no comparten intérprete (cada uno su `.venv` y sus paquetes
`application`/`domain`), así que el test va en **dos mitades unidas por un
contrato**: `tests/contratos/f030_r30.json`. La mitad de la api genera el
payload con el código real (`reemplazar`, `trazar_incidencias`, `_payloads`)
tras registrar la 7 del 5 al 9 y cambiarla (6-9 y 12-14), y debe salir el
JSON; la del transfer ejecuta ese JSON contra el `ClienteFalso` con el par y
debe emitir solo `UPDATE` de `fec`. Se escriben primero con
`xfail(strict=True)` (rojo demostrado: hoy la api manda la 8 sin `ide` y el
transfer inserta) y T33 quita la marca. Descartado: un test raíz que lance
los dos intérpretes por subproceso (depende de los `.venv`, que en esta
copia son uniones de directorio).

### Observaciones no bloqueantes de la review 1

Obs. 3 → T30 (`lecturas_lote.py:351`); obs. 4 → T36 (ruff de
`test_f030_incidencias.py` y la frase «293, deuda previa»); obs. 5 → T26
(docstring; el import se acepta); obs. 6 → T29 (desaparece al reescribir
`deduplicar` como `reconciliar`); obs. 7 → T30 y R33. La obs. 2
(`current.md`) es del líder.

### Tests que cambian (lista CERRADA, design §13.7)

Ajenos, solo dobles: `EdicionesFalsas`/`ClienteFalso` de
`services/dedicacion-transfer/tests/conftest.py` y los dobles de la lista de
T4 que lean `incidencia`. **Ninguna aserción ajena cambia** y
`test_f051_sql_cero.py` no se toca (la guarda de F-051 conserva su texto
byte a byte). Propios que fijan el R30 viejo y se reescriben: los
`test_f030_r30_*`, `test_f030_r17_guardar_repo_reemplazar_*`, los
`test_f030_r20_*` del snapshot, los de `trazar_incidencias` y los
`r33_cliente_*`.

### Avisos para el líder

- **D11-D15 al humano** antes de lanzar al implementer. Si elige otra
  alternativa, la spec se ajusta (R36, R38, R42 o R44 llevan su etiqueta).
- **T20 ampliada**: sigue siendo MANUAL con autorización expresa; ahora
  incluye cambiar 5-9 a 6-12 y comprobar con `verificar` los mismos dos `ide`.
  Es la primera vez que el transfer hace `UPDATE` sobre líneas `CI*`/`CIZ`.
- **`azure-apps/dedicacion.md`** (al desplegar) debe decir además que el
  transfer **edita la `fec`** de sus propias líneas `CI*`/`CIZ`; y el aviso a
  `partes` (`partes.md` es suyo) también.
- El texto movido del design está en este informe, sin cambios: si el
  reviewer quiere el diseño completo de T1-T19, está aquí abajo.

## Qué propone, en una línea por servicio

- **front**: en la celda del %, valor con al menos una letra ⇒ panel de F-042
  con las incidencias; con cifras, el código de hoy (R1, fijado por T1 antes
  de tocar nada). Chip «obra · letra · del/al» y subfila en la tabla.
- **api**: catálogo `tipo_incidencia` desde `auxhor` por el sync (como
  `empresa`, F-032), tabla nueva `incidencia` (por `create_all`; `asignacion`
  no cambia y su `CHECK porcentaje > 0` sigue), `PUT …/incidencias` con
  evento `INCIDENCIAS` y deshacer por tipo; no cuenta para el 100 %.
- **transfer**: cada incidencia = `CI*` el día desde + `CIZ` el día hasta,
  `can = 0`, `synckey porcentajes:inc:{id}:ini|fin`, en el parte del periodo
  de su obra; fuera de pisados, sobrecarga y sin partida; deduplica contra
  cualquier parte del mes (R27).

## Decisiones D1-D10 (decididas el 2026-10-20; alternativas en §«D1-D10», al final)

D1 fuente (rec. `auxhor`), D2 fechas (rec. tramo obligatorio), D3 cruce de
mes (rec. cada mes con su `CIZ`), D4 100 % (rec. no cuenta), D5 qué se
escribe (rec. par `CI*`/`CIZ`), D6 partida (rec. la de la línea de % o 0), D7
duplicados (rec. cualquier obra del mes; solo obra normal), D8 alcance (rec.
todo en F-030; alternativa: partir tras T9), D9 línea recién añadida (rec. se
convierte en incidencia), D10 % por días, calendario de convenio y bandeja de
`partes` (rec. fuera).

## Exploración en Sigrid (solo lectura)

Script en el scratchpad de la sesión, ejecutado con el intérprete y desde
`porcentajes\services\dedicacion-transfer` (su `.env`, sin imprimirlo); solo
`POST /api/sql/read`, base `ruesma`, `SELECT` parametrizados. Consultas:

1. `auxhor WHERE cod LIKE 'CI%'`: 8 filas (7 incidencias + `CIZ`), la letra
   entre paréntesis en `res`, `numemp = 0`, `pre = 0`, `tipincnom = 0` en
   todas (ese campo no sirve para clasificar).
2. `reshor` × `auxhor`: 711 recursos con los 8 códigos; 451 de 658 mensuales;
   169 de 229 mensuales activos (`con.fecbaj = 0`). Los 60 restantes darán
   «el recurso no tiene el código» (R26).
3. `hmores` desde 2025 con `CI*`: casi todas sin `synckey` (Administración a
   mano); de mensuales, 784 `CIV`, 1.000 `CIZ`; con `synckey partes:`, 2.
4. Muestra 2026 de mensuales (solo `ide` internos, sin nombres): inicio y fin
   en el parte de la obra donde está su `M*`, partida la de esa línea o 0;
   un día = `CIV` y `CIZ` el mismo día; bajas largas repetidas el día 1 de
   cada mes con un único `CIZ` final.

Ni nombres, ni DNI, ni importes en la spec ni aquí. Nada escrito en Sigrid.

## Avisos para el líder

- `azure-apps/partes.md` lo mantiene `partes`: avisar al humano de que
  `porcentajes` escribiría `CI*`/`CIZ` en los mismos partes.
- El interruptor `MENSUALES_A_DEDICACION` de `partes` (su F-019) debe seguir
  apagado: nadie lee aún `dedicacion_bandeja` (D10).
- `bash harness/init.sh` en el worktree (2026-10-20): pytest 418 passed, 1
  skipped; tamaño 150/150 y 250/250; cobertura N/A (sin código). Un único
  `[KO]`, el conocido: `services/dedicacion-api/.venv` no existe en el
  worktree (`harness/servicios.json`). No se ha tocado.

## D1-D10: evidencia y razones (movidas del design el 2026-10-21)

Eran el §10 y el §11 de `specs/F-030-dias-bajas-incidencias/design.md`;
se movieron aquí, sin cambios, para que el anexo R30 cupiera en el tope de
250 líneas. D1-D10 están **decididas** (todas la recomendada, 2026-10-20).

### Evidencia leída en Sigrid (2026-10-20, solo `/api/sql/read`, `ruesma`)

- `auxhor`: `CIA` «Accidente/Enf. Profesional(AT)», `CIE` «Enfermedad/Acc. no
  laboral(B)», `CIF` «Falta injustificada(F)», `CIH` «Huelga(H)», `CIM`
  «Maternidad/Paternidad(M)», `CIP` «Falta Justificada/Permiso(FJ)», `CIV`
  «Vacaciones(V)», `CIZ` «Fin de Incidencia». `numemp = 0` (todas las
  empresas), `pre = 0`, `tipincnom = 0` en todas: `cod LIKE 'CI%'` es el
  criterio. Las 7 letras son las de `partes/config/incidencias.yaml`.
- `reshor`: 711 recursos con los 8 códigos; de los 658 mensuales, 451 los
  tienen; de los 229 mensuales activos, 169.
- `hmores` desde 2025, recursos mensuales: 784 `CIV`, 1.000 `CIZ`, 65 `CIP`,
  58 `CIE`, 11 `CIA`, 11 `CIM`, 3 `CIF`; **todas menos 2 sin `synckey`**
  (las mete Administración a mano), `tot = 0` y casi siempre `can = 0`.
- Muestra 2026: inicio y fin en el **mismo parte de la obra** donde está su
  línea `M*`, con la partida de esa línea o 0, `hordes`/`horhas` vacíos; un
  día suelto = `CIV` y `CIZ` el mismo día; una baja larga se repite el día 1
  de cada mes con un único `CIZ` al final (base de D3).

### Decisiones: alternativas y por qué se recomienda cada una

- **D1.** A (`auxhor`) es la fuente que ya usan Administración y `partes`
  (sus `sigrid:` son estos códigos); B duplicaría datos entre repositorios
  (ampliar la lista cerrada); pedírsela a `partes` crearía una dependencia
  que hoy no existe. La «clase» de `partes` (día completo/parcial) no aplica:
  un mensual no tiene horas por día.
- **D2.** Sin días no hay nada que escribir (Sigrid pinta el tramo con
  inicio y fin): B solo anotaría; C dejaría un tramo abierto.
- **D3.** A es determinista y cada periodo se registra solo; B imita a
  Administración pero deja tramos abiertos si nadie captura el mes siguiente.
- **D4.** A respeta «el comportamiento no debe cambiar»; B exige calendario.
- **D5.** A es lo que hacen `partes` y Administración.
- **D6.** A es lo que se ve en la muestra; B es más simple y, con `tot = 0`,
  no mueve importes.
- **D7.** Comparar solo la obra destino dejaría duplicar una incidencia que
  Administración puso en otra obra; `Postv-` y VAR no son partes «de» la
  persona.
- **D8.** A cierra la petición («funciona igual que partes»); B entrega antes
  una captura que nadie registra. Las tareas van en dos bloques (T1-T9
  captura, T10-T18 registro) por si el humano elige B.
- **D9.** A evita la línea de % sobrante en una obra que solo lleva la
  incidencia; B obliga a borrarla a mano.
- **D10.** % por días y calendario de convenio son otra regla del 100 %;
  la bandeja de `partes` es otra frontera. Cada una, feature propia.

## Diseño de T1-T19 (movido del design el 2026-10-21)

Eran el §2, el §3 y el §5 de `specs/F-030-dias-bajas-incidencias/design.md`,
ya implementados (T1-T19); se movieron aquí sin cambios para que el anexo R30
cupiera en el tope. El design conserva su resumen con los mismos números.

### 2. Ficheros a crear

- `services/dedicacion-api/domain/incidencias.py` — puras:
  `letra_y_nombre(res, cod) -> tuple[str, str]` (R4);
  `completar_dias(desde, hasta, anio, mes) -> tuple[int, int]` (R17);
  `validar_incidencias(lista, anio, mes) -> None` (lanza `IncidenciaInvalida`:
  día fuera del mes, `desde > hasta`, solape entre dos, R19).
- `services/dedicacion-transfer/application/services/reglas_incidencias.py` —
  puras: `decidir_incidencia(inc, horas) -> list[AccionIncidencia]` (R24,
  R26), `deduplicar(acciones, existentes) -> None` (R27),
  `synckey_incidencia(id, rol) -> str` (`porcentajes:inc:{id}:ini|fin`).
- Tests (todos sin red ni BBDD): `services/dedicacion-api/tests/
  test_f030_catalogo.py`, `test_f030_incidencias.py`,
  `test_f030_registro.py`; `services/dedicacion-transfer/tests/
  test_f030_reglas_incidencias.py`, `test_f030_pipeline_incidencias.py`;
  `services/dedicacion-front/tests/test_f030_celda_pct.py`,
  `test_f030_tabla_incidencias.py`.

### 3. Ficheros a modificar

**api**
- `infrastructure/db/orm_models.py`: `TipoIncidenciaORM` (`tipo_incidencia`:
  `ide` BigInteger PK sin autoincremento = `auxhor.ide`, `codigo`, `letra`,
  `nombre` Text, `activa` Boolean) e `IncidenciaORM` (`incidencia`: `id` PK,
  `periodo_id` FK con CASCADE, `trabajador_ide` FK, `obra_ide` FK, `codigo`
  Text, `dia_desde`, `dia_hasta` SmallInteger, `actualizado_en`/`_por`, y la
  traza nulable `sigrid_estado` String(16), `sigrid_parte_cod` String(24),
  `sigrid_ide_ini`, `sigrid_ide_fin` Integer, `sigrid_motivo` String(300),
  `sigrid_registrado_at_utc`, `sigrid_registrado_by` String(64); `CHECK`
  `dia_desde BETWEEN 1 AND 31 AND dia_hasta BETWEEN dia_desde AND 31`; índice
  `(periodo_id, trabajador_ide)`). Dos tablas **nuevas**: las crea
  `create_all` al arrancar, como `empresa` en F-032; `asignacion` no cambia.
- `config/config.yaml`: `sync.incidencias.sql` = `SELECT ide, cod, res,
  fecbaj FROM dbo.auxhor WHERE cod LIKE 'CI%' AND cod <> 'CIZ' ORDER BY cod`
  (solo literales: no hay parámetros que concatenar).
- `application/sync_pipeline.py`: pasos `FetchTiposIncidencia` y
  `UpsertTiposIncidencia`, calcados de los de empresas (R3, R5, R7).
- `domain/models.py`: `TipoIncidencia`, `Incidencia`;
  `TipoEvento.INCIDENCIAS`; `CuadranteTrabajador.incidencias` (tupla vacía
  por defecto, para no tocar a quien lo construye hoy).
- `domain/ports.py` y `infrastructure/db/repositories.py`: repos
  `tipos_incidencia` (`sincronizar`, `activos`) e `incidencias`
  (`de_periodo`, `de_trabajador`, `reemplazar`, `trazar`).
- `application/use_cases.py`: `GuardarIncidencias` (R17-R19: periodo
  abierto, trabajador, `_validar_obra_incidencia` = obra activa de la empresa
  de las obras y sin `registro_obra_ide`, código activo, `completar_dias`,
  `validar_incidencias`, evento con snapshot de incidencias);
  `DeshacerUltimaModificacion` despacha por `pendiente.tipo`: `INCIDENCIAS`
  → `incidencias.reemplazar(snapshot_antes)`; el resto, como hoy (R20);
  `ObtenerCuadrante` y `ObtenerFilaTrabajador` añaden `incidencias` (R21).
  `GuardarAsignaciones`, `Completar*` y `Copiar*` no se tocan (R2, R21).
- `interface_adapters/api/schemas.py` y `routes.py`: `IncidenciaIn`
  (`obra_ide`, `codigo`, `dia_desde`/`dia_hasta` opcionales), `IncidenciaOut`,
  `GET /incidencias`, `PUT …/trabajadores/{ide}/incidencias`; `TrabajadorOut`
  gana `incidencias: list[IncidenciaOut] = []`.
- `application/registro_sigrid.py`: `_payloads` añade por obra la lista
  `incidencias` (R23, R25: `paride` = `partida_ide` o `propuesta_ide` de la
  asignación `(trabajador, obra, es_postventa=False)` si existe); al volver,
  `_trazar_incidencias` (R31). Las obras con solo incidencias entran en la
  agrupación por obra.

**transfer**
- `domain/models/registro_models.py`: `IncidenciaEntrada` (id, recurso_ide,
  empresa, codigo, ano, mes, desde, hasta, paride) y `AccionIncidencia` (id,
  rol, accion, fecha_int, hora_ide, hora_codigo, pre, paride, motivo,
  parte_cod, hmores_ide, caa_ide); `ResultadoPreflight` gana `incidencias`.
- `infrastructure/sigrid/sigrid_write_client.py`: `incidencias_del_mes(resides,
  ano, mes, hmoides=None)` (R27, R33): `SELECT h.ide, h.reside, h.fec,
  a.cod, h.synckey, c.cod AS parte FROM hmores h JOIN auxhor a ON a.ide =
  h.horide JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide WHERE
  h.reside IN (…) AND h.fec BETWEEN ? AND ? AND a.cod LIKE ?` (+ `AND
  h.hmoide IN (…)` en modo pruebas), en trozos de 500, lanza ante
  `truncated`. Las inserciones reutilizan `stmt_insert_linea` (con `can = 0`
  da `tot = 0`).
- `application/pipelines/registro_pipeline.py`: tras el paso de reglas,
  `reglas_incidencias.decidir_incidencia` por incidencia; comparten con las
  líneas el paso «parte del periodo», el alta protegida, la cuenta analítica
  y el modo pruebas; **no** entran en los pasos de pisados, sobrecarga ni sin
  partida (R28). Idempotencia por su `synckey` y R27 con
  `incidencias_del_mes`. `ejecutar` inserta sus líneas en los mismos lotes.
- `application/pipelines/registro_lote.py`: la lectura de R33, una por lote.
- `interface_adapters/api/app.py`: `PeticionIn` y `LoteIn` aceptan
  `incidencias` (por defecto `[]`: una petición de hoy es idéntica);
  `_respuesta_preflight` las publica (R31).
- `prueba_escritura_porcentajes.py`: `--incidencia RECURSO:COD:DESDE:HASTA` en
  `preflight`, `ejecutar` y `verificar` (R35); `limpiar` ya borra por marca.

**front** (`services/dedicacion-front/static/`)
- `js/app.js`: `chipEditable` (rama de letras, R8-R13), `chipIncidencia` y
  `montarDesplegableIncidencias` (nuevas), `guardarAhora` (PUT de
  incidencias si cambiaron, mismo diferido), `construirFila` (subfilas de
  incidencia, R16), `textoColumna` (Obra encuentra la incidencia),
  `pintarModalPreflight` (sección Incidencias, R32), `init` (carga
  `GET /incidencias` una vez).
- `css/styles.css`: `.chip-inc`, `.sugerencia.inc` y la subfila `.fila-inc`.

**docs**: `docs/ARCHITECTURE.md` (§regla nueva 20 `#regla-incidencia`, una
línea en P2, P3 y P4 que remite a ella, tabla de §Capas), `docs/INTEGRACION.md`
§1 y §5, `services/dedicacion-transfer/tests/test_f002_fuente_unica.py` (el
ancla nueva) y `azure-apps/dedicacion.md` (otro repositorio, su propio commit).

### 5. UX exacta con teclado (front)

Estado nuevo por línea de % en edición: `previo` (valor de la celda antes de
la primera letra) y `nueva` (true desde `elegir` del buscador de obra hasta
el primer blur del %). Lista nueva `state.incidenciasEdicion`, aparte de
`state.edicion` (así `totalEdicion` y `restanteSin` no cambian).

1. Celda del % con foco. `input`: si `/\p{L}/u` no casa → rama de hoy, el
   mismo código (R1). Si casa → no se toca `linea.porcentaje` ni se programa
   guardado; se abre/refresca el panel (R8, R9).
2. Panel: el `.sugerencias` de F-042 (cuelga de `<body>`, `position: fixed`,
   `posicionSugerencias`/`colocarSugerencias`/`retirarSugerencias`: uno solo a
   la vez). Filas «**V** · Vacaciones». ↓/↑ mueven; Enter/Tab eligen; Escape
   cierra y repone `previo` (R10, R11). Se cierra al borrar las letras (R12).
3. Elegir: si `nueva`, se quita la línea de `state.edicion` (y su guardado
   diferido la borra en la api); si no, la celda repone `previo`. Se añade
   `{obra_ide, codigo, desde: null, hasta: null}` a `incidenciasEdicion`, se
   repinta el editor y el foco va a «del» (R13, R14).
4. «del»/«al»: `input` numérico de 2 cifras con placeholder `1` y último día.
   Enter en «del» → «al»; Enter en «al» → buscador de obra; Escape → buscador.
   Vacío viaja como `null` y la api lo completa (R17). Lo que la api rechace
   (422) sale en el `toast` de error de guardado de hoy.
5. Atajos del editor (F7, F8, Ctrl+Z, Esc para cerrar) no cambian; con el
   panel de incidencias abierto, Escape solo lo cierra (como F-042).
