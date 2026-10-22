<!-- specs/F-030-dias-bajas-incidencias/design.md -->
# F-030 · Diseño técnico

D1-D10 (requirements §7) **aceptadas por el humano el 2026-10-20 («si»):
spec aprobada**. **Anexo R30** (2026-10-21): §13; D11-D15 decididas el 2026-10-21 (§11).

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

## 2. Ficheros a crear (hechos en T1-T19)

Detalle en `progress/spec_F-030.md` §«Diseño de T1-T19»; los del anexo, §13.

- api `domain/incidencias.py` (puras: `letra_y_nombre`, `completar_dias`,
  `validar_incidencias`) y `application/traza_incidencias.py`; transfer
  `application/services/reglas_incidencias.py` (`decidir_incidencia`,
  `deduplicar`, `synckey_incidencia`).
- Tests sin red ni BBDD: api `test_f030_catalogo.py`, `test_f030_incidencias.py`,
  `test_f030_registro.py`; transfer `test_f030_reglas_incidencias.py`,
  `test_f030_pipeline_incidencias.py`; front `test_f030_celda_pct.py`,
  `test_f030_tabla_incidencias.py`.

## 3. Ficheros a modificar (hechos en T1-T19; resumen)

- **api**: `orm_models.py` (`TipoIncidenciaORM`, `IncidenciaORM` con la traza
  `sigrid_*`; por `create_all`), `config.yaml` (`sync.incidencias.sql`, solo
  literales), `sync_pipeline.py`, `domain/models.py`, `ports.py`,
  `repositories.py` (repos `tipos_incidencia` e `incidencias`),
  `use_cases.py` (`GuardarIncidencias`, deshacer por tipo, cuadrante y fila),
  `schemas.py`/`routes.py` (`GET /incidencias`, `PUT …/incidencias`) y
  `registro_sigrid.py` (`_sumar_incidencias`, traza).
- **transfer**: `registro_models.py` (`IncidenciaEntrada`, `AccionIncidencia`,
  `LineaIncidenciaSigrid`), `sigrid_write_client.py` (`incidencias_del_mes`;
  se inserta con `stmt_insert_linea`), `registro_pipeline.py` (fuera de
  pisados, sobrecarga y sin partida), `registro_lote.py`, `app.py` y
  `prueba_escritura_porcentajes.py --incidencia`.
- **front**: `app.js` (`chipEditable`, `chipIncidencia`,
  `montarDesplegableIncidencias`, `guardarAhora`, `construirFila`,
  `textoColumna`, `pintarModalPreflight`, `init`) y `styles.css`.
- **docs**: `ARCHITECTURE.md` (`#regla-incidencia`, remisiones de P2-P4),
  `INTEGRACION.md`, `test_f002_fuente_unica.py` y `azure-apps/dedicacion.md`.

## 4. Ficheros que NO se tocan

`domain/estados.py` (R22), `reglas_porcentajes.py` (identidad, capacidad y
sin partida de las líneas de %: R2, R28), `estado_parte.py` y
`cuenta_analitica.py` (copias de `partes`: se **llaman**, no se editan),
`propuesta_partida.py`, `partida_*`, `universo_*`, `infrastructure/excel/`
(D10), el esquema de `asignacion`, `evento` (el tipo es `Text` sin `CHECK`),
el repositorio de `partes` y `azure-apps/partes.md` (lo actualiza `partes`;
el líder se lo avisa al humano, §12).
**Anexo:** `stmt_editar_linea`, `stmt_poner_a_cero`, `lineas_para_editar`,
`lineas_registradas`, `emparejar_ceros` y el texto SQL de la guarda de F-051
(solo gana un parámetro opcional); `stmt_borrar_linea` sigue solo para
`limpiar`; las asignaciones y su `reemplazar`; `decidir_incidencia` (R26).

## 5. UX exacta con teclado (front, hecha en T8-T9)

Texto completo en `progress/spec_F-030.md` §«Diseño de T1-T19». Resumen:
`previo` y `nueva` por línea de %; `state.incidenciasEdicion` aparte de
`state.edicion` (`totalEdicion` no cambia); con letras no se toca el % ni se
guarda; panel `.sugerencias` de F-042; elegir en una `nueva` la quita;
«del»/«al» numéricos, vacíos viajan `null`; con el panel, Escape solo cierra.

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

`partes` escribe incidencias de mensuales solo por sus partes diarios (2 desde
2025 con `synckey partes:`): R27 evita duplicarlas, y las de Administración, en
cualquier obra. Su `MENSUALES_A_DEDICACION` (su F-019) sigue apagado mientras
nadie lea `dedicacion_bandeja` (D10). El anexo solo edita líneas nuestras.

## 9. SQL

Lecturas nuevas (`config.yaml` de la api, cliente del transfer), las `INSERT`
de siempre y, con el anexo, un `UPDATE` de la `fec` (§13.5). Sin DDL a mano:
tablas por `create_all`, columnas nuevas por `alters_faltantes`.

## 10. Evidencia de Sigrid y razones de D1-D10

Movidas sin cambios a `progress/spec_F-030.md` §«D1-D10» (2026-10-21), para
que cupiera el anexo. El anexo no ha necesitado leer Sigrid.

## 11. Decisiones del anexo (humano, 2026-10-21: D11 B, D12-D15 A)

- **D11 · Quitar una registrada.** Una línea `CI*` ya va a `can` 0: no tiene
  forma neutra y retirarla es borrarla, que el registro no hace. A: 422 hasta
  F-033 (bloquea unas vacaciones anuladas y, si Administración borra el par,
  R42 lo reescribe: sin salida). **B (rec.)**: `quitada`, a la vista hasta que
  se retire a mano o con F-033; deshacer la repone. C: borrar en la api con
  un aviso único (huérfanas sin rastro).
- **D12 · Tipo.** El chip no cambia de tipo: es ✕ + otra. **A (rec.)**: quitar
  + nueva, sin UX nueva. B: `UPDATE` de `horide` y `pre` del inicio, con un
  gesto nuevo en el chip (feature aparte si se quiere).
- **D13 · Obra.** [`#regla-cero`] no cambia parte, obra ni centro de una
  línea: B (moverla) exige borrar. **A (rec.)**: quitar + nueva; con mismo
  código y días, R27 omite la nueva hasta que se retire la vieja.
- **D14 · Cambiada a mano.** **A (rec.)**, como F-051 (da por registrada la
  nuestra aunque le cambien el `can`): no se pisa una corrección; para
  igualar, el cuadrante toma los días de Sigrid. B: el cuadrante manda.
  Borrada a mano: se reescribe (F-051 R17) en A y en B.
- **D15 · Día ocupado.** **A (rec.)** mantiene R27: nunca dos iguales.
- **D16 · `fec` en la guarda** (review 2, obs. 5). **A**, del humano el
  2026-10-22: la guarda exige además `fec = fec_antes`; cierra la ventana de
  §12 (una `fec` cambiada a mano tras leer no se pisa, como D14). T38.

## 12. Riesgos

- **Rigor crítico, escritura nueva** (`INSERT` de `CI*`/`CIZ` y el primer
  `UPDATE` de su `fec`). Sin T20 en la `0404` no se cierra ni se despliega:
  el transfer desplegado está en modo real.
- **Rendimiento**: R33 es una lectura por lote (el anexo le suma `OR ide IN`);
  `ejecutar`, la de F-051 R12. Se mide con `prueba_escritura_porcentajes.py`.
- **Par a medias**: si la guarda de una falla entre la relectura y el
  `UPDATE` (ventana mínima), la relectura lo saca a `omitir` y el log lo dice.
- **Un `id` que no vuelve del front** (R37): la registrada queda `quitada` y
  la nueva no duplica (R27 si los días coinciden; si no, el modal lo enseña).
- **Tests estáticos de F-042/F-050** que fijen texto de `chipEditable`: se
  adaptan sin perder lo que vigilan (lista cerrada, tasks).
- **`azure-apps/partes.md`** es de `partes`: avisar de que escribimos y
  editamos `CI*`/`CIZ` en sus partes. **Deshacer** despacha por tipo (R20).

## 13. Anexo R30: editar en su sitio la `fec` de una registrada (R36-R49)

El patrón de F-051 ([`#regla-cero`]), sin inventar otro: localizar por
`hmores.ide`, releer una vez antes de escribir, `UPDATE` con guarda,
relectura y log con lo que tenía. Los tres servicios, como en §1; ningún
`DELETE`; nada de otro microservicio.

**13.1 api.** `orm_models.py`: `IncidenciaORM` + `quitada` (Boolean, `NOT
NULL`, `server_default false`), `sigrid_dia_ini`/`_fin` (SmallInteger nulos).
`domain/models.py`: `Incidencia` + `quitada`, `sigrid_ide_*`, `sigrid_dia_*`.
`schemas.py`: `IncidenciaIn.id: int | None`, `IncidenciaOut.quitada`.
`use_cases.py`: `_parsear_incidencia` lee `id`; `GuardarIncidencias` valida
R36 y pasa a `validar_incidencias` solo las no quitadas;
`_snapshot_incidencias` + `id`, `quitada` (sin `id` = nueva; R47).
`repositories.py`, `PgIncidenciaRepository.reemplazar(…)` (misma firma): con
`id`, actualiza obra, código y días y `quitada = false`; sin `id`, añade;
previa ausente, `quitada = true` si es registrada y `delete` si no.
`registro_sigrid.py`: `_sumar_incidencias` salta las quitadas y añade los
cuatro campos de §6; `preflight` devuelve `incidencias_quitadas`
(trabajador, obra, letra, días, parte, `ide`s). `traza_incidencias.py`:
R39 por rol (`sigrid_dia_<rol>` = `fecha_int % 100`); `omitido` solo si no
queda ningún `ide`. Obs. 5: su import de ORM se queda (precedente
`registro_sigrid.py`) y lo dice su docstring.

**13.2 transfer.** `registro_models.py`: `IncidenciaEntrada` + los cuatro
campos (None por defecto); `AccionIncidencia` + `editar`, `fec_antes`,
`hmoide`; `LineaIncidenciaSigrid` + `can`, `hmoide`, `parte_est`. `app.py`:
`IncidenciaIn` igual y `fec_antes` en la respuesta. `reglas_incidencias.py`:
`deduplicar` → `reconciliar(acciones, entradas, existentes, *, est)`, pura:
nuestra por `ide` (del recurso y con su `synckey`) o por `synckey`; misma
`fec` → `ya_registrado`; otra → `editar` u `omitir` (R41-R43); R44 contra lo
existente con las ediciones de la petición aplicadas; sin nuestra, R27 como
hoy (obs. 6: fuera la rama inalcanzable). Motivos `MOTIVO_INC_CAMBIADA`,
`MOTIVO_INC_CERRADO`, `MOTIVO_INC_PAR`. `sigrid_write_client.py`:
`incidencias_del_mes(…, ides=())` (§13.5); `_guarda(…, hora=None)`: con
`hora`, `a.cod = ?`; sin ella, el texto de F-051 **idéntico**;
`stmt_editar_fecha_incidencia(*, ide, reside, hora_codigo, synckey_leida,
fecha_int, fec_leida)` (D16). `registro_pipeline.py`: `reconciliar` antes del paso 5 (obs.
7: solo las `escribir` piden parte; `editar` usa el de su línea); en
`ejecutar`, sus `ide` entran en la lectura de `_planear_ediciones` (R45),
sus `UPDATE` van juntos en el mismo lote, log (R46) y `_comprobar_escrito`
los relee. `lecturas_lote.py`: los `ide` en la misma ronda (y obs. 3, su
línea 351). `prueba_escritura_porcentajes.py`: imprime `editar` y
`fec_antes`; `verificar`, `ide` y `fec` de cada línea.

**13.3 front** (`app.js`). `cargarEdicion` guarda `id` y deja fuera las
quitadas; `cuerpoIncidencias` manda `id`; tras el PUT, cada una sin `id`
toma el de la respuesta con su obra y código aún no usado, en orden (R37);
`construirFila` tacha la quitada; `pintarModalPreflight`, «se cambia del d
al d» y la lista de quitadas.

**13.4 docs.** `#regla-incidencia`: «no se reescribe» pasa a «Cambiar los
días» y «Quitar»; `INTEGRACION.md` §5, campos y el `UPDATE`;
`azure-apps/dedicacion.md`, el líder al desplegar.

**13.5 SQL** (Sigrid, `ruesma`; ni `ano`/`mes`, hora, `pre`, partida, cuenta,
`synckey`, `tex`, `pos` ni parte cambian):

```sql
-- incidencias_del_mes: + h.can, h.hmoide, c.est AS est
WHERE (h.reside IN (…) AND h.fec BETWEEN ? AND ? AND a.cod LIKE ?
       OR h.ide IN (…)) [AND h.hmoide IN (…)]            -- en pruebas
-- stmt_editar_fecha_incidencia: la guarda de F-051 con su código
UPDATE hmores SET fec = ? WHERE ide = ? AND reside = ?
  AND ABS(ISNULL(can, 0) - 0) < 0.000001 AND LTRIM(RTRIM(ISNULL(synckey,
  ''))) = ? AND <sin enlaces> AND EXISTS (SELECT 1 FROM auxhor a WHERE
  a.ide = hmores.horide AND a.cod = ?) AND EXISTS (SELECT 1 FROM con c
  WHERE c.ide = hmores.hmoide AND c.est = ?) AND fec = ?    -- D16: la leída
```

**13.6 Punta a punta (obligatorio).** `tests/contratos/f030_r30.json`, el
contrato entre dos mitades sin red ni BBDD (los servicios no comparten
intérprete): la api (`test_f030_r30_punta_a_punta.py`, con `reemplazar`,
`trazar_incidencias` y `_payloads` reales sobre sesión en memoria) registra
la 7 del 5 al 9, la cambia (6-9 y 12-14) y su payload debe ser el del JSON;
el transfer (`test_f030_r30_punta_a_punta.py`) ejecuta ese JSON contra el
`ClienteFalso` con el par: solo `UPDATE` de `fec`, sin `INSERT`. Hoy, rojo
en las dos (la api manda la 8 sin `ide`; el transfer, `INSERT`).

**13.7 Tests que cambian (lista CERRADA; si cambia otro, PARA).** Ajenos,
solo dobles y sin tocar ninguna aserción: `EdicionesFalsas`/`ClienteFalso`
de `services/dedicacion-transfer/tests/conftest.py` aplican también
`stmt_editar_fecha_incidencia` y aceptan `ides` en `incidencias_del_mes`;
los dobles de la lista de T4 (tasks) que lean `incidencia` aceptan las
columnas nuevas. `test_f051_sql_cero.py` **no** cambia. Propios de F-030
que fijan el R30 viejo y se reescriben al nuevo, citándolo:
`test_f030_r30_deduplicar_la_nuestra_aunque_cambien_los_dias`,
`test_f030_r30_ejecutar_no_reescribe_la_ya_registrada`,
`test_f030_r17_guardar_repo_reemplazar_*`, los `test_f030_r20_*` del
snapshot, los de `trazar_incidencias` en `test_f030_registro.py` y los
`r33_cliente_*` (SQL con las columnas nuevas; sin `ides`, el `WHERE` de hoy).
