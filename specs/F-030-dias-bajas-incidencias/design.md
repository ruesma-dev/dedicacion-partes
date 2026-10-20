<!-- specs/F-030-dias-bajas-incidencias/design.md -->
# F-030 · Diseño técnico

Escrito con las recomendaciones de D1-D10 (requirements §7). Si el humano
elige otra, se ajustan las R marcadas `[Dn]` y las tareas que las citan.

## 1. Servicios que toca y por qué (límite de servicio)

| Servicio | Qué hace en F-030 | Por qué ahí |
|---|---|---|
| `dedicacion-front` | Abre el desplegable al teclear letras en la celda del %, pinta chips y subfilas de incidencia, manda lo tecleado | Captura y nada más: no decide qué es una incidencia, ni sus días por defecto, ni si cuenta para el 100 % |
| `dedicacion-api` | Catálogo desde Sigrid (sync), tabla de incidencias, validación, evento y deshacer, payload al transfer y traza | Dueña del dato y de la regla del 100 % |
| `dedicacion-transfer` | Decide y escribe las dos líneas de cada incidencia, deduplica contra Sigrid | Única pluma contra Sigrid |

No hace falta servicio nuevo ni nada de `partes`: el catálogo es de Sigrid
(D1) y la regla «inicio con `CI*`, fin con `CIZ`, `can = 0`» se **reimplementa**
aquí como regla propia ([`#regla-incidencia`]), no se copia código de
`partes-transfer` (no entra en la lista cerrada de duplicación de
`CLAUDE.md`). La letra de cada código la saca solo la api (R4); el transfer
trabaja con códigos.

## 2. Ficheros a crear

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

## 3. Ficheros a modificar

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

## 4. Ficheros que NO se tocan

`domain/estados.py` (R22), `reglas_porcentajes.py` (identidad, capacidad y
sin partida de las líneas de %: R2, R28), `estado_parte.py` y
`cuenta_analitica.py` (copias de `partes`: se **llaman**, no se editan),
`propuesta_partida.py`, `partida_*`, `universo_*`, `infrastructure/excel/`
(D10), el esquema de `asignacion`, `evento` (el tipo es `Text` sin `CHECK`),
el repositorio de `partes` y `azure-apps/partes.md` (lo actualiza `partes`;
el líder se lo avisa al humano, §12).

## 5. UX exacta con teclado (front)

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

## 6. Contrato api → transfer

`incidencias: [{"id", "recurso_ide", "empresa", "codigo", "ano", "mes",
"desde", "hasta", "paride"}]` en `preflight`, `preflight-lote` (por obra) y
`ejecutar`. Respuesta: `incidencias: [{"id", "rol", "accion"
("escribir"|"omitir"|"ya_registrado"), "fecha_int", "hora_codigo", "paride",
"parte_cod", "hmores_ide", "motivo"}]`. Las demás claves, idénticas.

## 7. Cómo afecta a las reglas (pregunta del líder)

| Regla | Efecto |
|---|---|
| P1 (`M*`) | Igual: solo trabajadores del cuadrante. Además el recurso debe tener el `CI*` y `CIZ` en `reshor` (R26); hoy 169 de 229 mensuales activos los tienen |
| P2 (último día) | **Excepción**: la incidencia lleva sus días reales |
| P3 (escala) | No aplica: `can = 0`, `tot = 0` |
| P4 / Regla A | Identidad propia (recurso, código, `fec`), y nunca pisa (R27, R28) |
| Regla B (capacidad) | No suma: no es `M*` (`es_linea_mensual` ya lo excluye) |
| Regla C (sin partida) | No aplica: `paride = 0` sin aviso (R25) |
| P5 (postventa) | No hay incidencia de postventa (R19) |
| Analítica, parte, pruebas, empresa | Como cualquier línea (R24, R29) |
| Regla del 100 % | No cuenta (R22) |

## 8. Convivencia con `partes`

`partes` escribe incidencias de mensuales solo si llegan por sus partes
diarios: en Sigrid hay 2 desde 2025 con `synckey partes:` (§10). R27 evita el
duplicado exacto con ellas y con las de Administración, en cualquier obra.
Si `partes` enciende su `MENSUALES_A_DEDICACION` (su F-019), sus incidencias
de mensuales dejan de ir a Sigrid y van a `dedicacion_bandeja`: leerla es la
feature espejo (D10). Mientras no exista, ese interruptor sigue apagado.

## 9. SQL

Solo lecturas nuevas (`config.yaml` de la api, cliente del transfer) y las
`INSERT` de siempre. Sin DDL a mano (las dos tablas, por `create_all`).

## 10. Evidencia leída en Sigrid (2026-10-20, solo `/api/sql/read`, `ruesma`)

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

## 11. Decisiones: alternativas y por qué se recomienda cada una

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

## 12. Riesgos

- **Rigor crítico y escritura nueva**: tipos de hora nuevos en `hmores`. Sin
  prueba en la `0404` (R35) no se cierra; el transfer desplegado está en modo
  real, así que **no se despliega** sin esa prueba.
- **Rendimiento**: R33 añade una lectura por lote filtrada por recurso y
  `fec`; se mide con `prueba_escritura_porcentajes.py medir`.
- **Tests estáticos de F-042/F-050** que fijen texto literal de
  `chipEditable`: se adaptan sin perder lo que vigilan, y se dice en el informe.
- **`azure-apps/partes.md`**: «qué se rompe» debería decir que `porcentajes`
  escribe `CI*`/`CIZ` en los mismos partes; es de `partes` y se le avisa.
- **Identificador de evento**: `evento.tipo = 'INCIDENCIAS'` con snapshot de
  otra forma; Deshacer despacha por tipo antes de leerlo (R20).
