<!-- specs/F-044-recursos-vinculados/design.md -->
# F-044 · Diseño: recursos vinculados con el % del trabajador

Evidencia en `progress/explore_F-044_sigrid.md`. Decisiones abiertas en §9;
el diseño sigue la recomendada de cada una.

## 1. Servicios y límite

| Servicio | Qué hace en F-044 | Por qué ahí |
|---|---|---|
| `dedicacion-api` | Lee los vinculados en el sync (lectura de maestros por `sigrid-api`), los casa con el trabajador, los guarda, los manda en cada línea del registro y guarda su traza | El vínculo es un **maestro** como el trabajador, y `#regla-recurso` dice que la api manda el recurso y el transfer no lo elige |
| `dedicacion-transfer` | Decide y escribe las líneas de los vinculados: hora, importe, partida, cuenta, parte, identidad, pisables, capacidad | Es la **única pluma** contra Sigrid y ya tiene el parte del periodo, las cuentas, la propuesta de partida y las guardas |
| `dedicacion-front` | Marca en el cuadrante y sección en el modal | Solo pinta lo que devuelve la api |

Sin microservicio nuevo: son más líneas del mismo parte. `partes` no se toca
(hoy no escribe vinculados), pero comparte el parte (§10).

## 2. Encaje en el flujo

Sync (api): `res` + `auxrestip` → `casar_vinculados` → `recurso_vinculado`.
Registro: `_payloads` manda cada línea de % con sus `vinculados` → el
transfer decide los titulares **exactamente igual que hoy** (R7) y después
`PasoVinculados` crea una `AccionVinculado` por (titular, vinculado): partida,
cuenta, identidad, pisables y capacidad; `ejecutar` la escribe tras su
titular → `_trazar` guarda `registro_vinculado`.

## 3. Ficheros a crear

- `services/dedicacion-api/domain/vinculados.py` — dominio puro (§6.1).
- `services/dedicacion-transfer/application/services/reglas_vinculados.py` —
  reglas puras de las líneas de vinculado (§6.2).
- `services/dedicacion-transfer/application/pipelines/registro_vinculados.py`
  — `PasoVinculados`, la orquestación que usa `RegistroPipeline` (§6.3).
  Separado para no engordar `registro_pipeline.py` (1.302 líneas).
- Tests `test_f044_*.py` en los `tests/` de los tres servicios, sin red ni
  BBDD (nombres en `tasks.md`); fixture del caso de la 0694 con `ide` inventados.

## 4. Ficheros a modificar

**api**
- `config/config.yaml` — bloque `sync.vinculados`: `tipos: [TF, CO, VE]`,
  `desde: "2026-10"` y la SQL de §7 (alias exactos).
- `domain/models.py` — `RecursoVinculado` (dataclass).
- `infrastructure/db/orm_models.py` — `RecursoVinculadoORM` y
  `RegistroVinculadoORM` (§7.2); `esquema.py` no cambia (`create_all` crea
  tablas nuevas).
- `infrastructure/db/repositories.py` — upsert de vinculados, lectura por
  trabajador y mes, traza.
- `application/sync_pipeline.py` — `FetchVinculadosStep` y
  `UpsertVinculadosStep` (después de trabajadores); el preview publica el
  bloque `vinculados` (casados, sin trabajador, ambiguos, duplicados).
- `application/registro_sigrid.py` — `_payloads` añade `vinculados` (R6,
  con `hmores_ide` de la traza, R26); `_trazar` guarda `registro_vinculado`.
- `application/use_cases.py` + `interface_adapters/api/schemas.py` — el
  cuadrante devuelve por trabajador `vinculados` (tipo, código) del mes (R27).

**transfer**
- `domain/models/registro_models.py` — `VinculadoEntrada` (`recurso_ide`,
  `tipo`, `categoria`, `hmores_ide`), `LineaEntrada.vinculados`
  (`default_factory=list`), `AccionVinculado`, `Preflight.vinculados`,
  `ResultadoRegistro.vinculados`.
- `application/services/reglas_porcentajes.py` — parámetros nuevos **con el
  valor de hoy por defecto**: `evaluar_capacidad(..., es_jornada=es_linea_mensual)`
  y `pisables_al_cero(..., hora=None)`; `criterio_choque` y `clave_conflicto`
  aceptan cualquier objeto con los campos de `campos_identidad()` (Protocol),
  sin cambiar la identidad.
- `application/services/propuesta_partida.py` — sin cambio de lógica: se
  llama con el recurso del vinculado y su historial.
- `application/pipelines/registro_pipeline.py` — llama a `PasoVinculados` al
  final del preflight y tras escribir los titulares en `ejecutar`; las
  lecturas de horas y de líneas incluyen los `recurso_ide` de los vinculados.
- `application/services/lecturas_lote.py` — la precarga del lote incluye
  esos recursos y el historial de vinculados (R25).
- `infrastructure/sigrid/sigrid_write_client.py` —
  `historial_partidas(..., horas=None)` (`None` = `LIKE 'M%'`, el texto de
  hoy; lista = `a.cod IN (?, …)`); `stmt_editar_linea` y `stmt_poner_a_cero`
  pasan `hora` a `_guarda`, que ya la admite (anexo R30 de F-030).
- `interface_adapters/api/app.py` — `LineaIn.vinculados` y la salida.
- `prueba_escritura_porcentajes.py` — `estado` lista las `porcentajes:vin:`;
  `limpiar` ya cubre el prefijo `porcentajes:` (comprobar en T15).

**front**: `static/js/app.js` (marca de la fila y sección del modal en
`pintarModalPreflight`), `static/css/styles.css` (estilo de la marca).

**docs**: `docs/ARCHITECTURE.md` (`#regla-vinculado` y remisiones),
`docs/INTEGRACION.md` §1/§5/§7, `services/dedicacion-transfer/tests/test_f002_fuente_unica.py`
(`ANCLAS`).

## 5. Ficheros que NO se tocan

`estado_parte.py` y `cuenta_analitica.py` (copias literales de `partes`: el
vinculado usa `resolver_cuenta` tal cual); `partida_catalog.py`,
`partida_matcher.py`, `text_match.py` (copias de `partes-persistencia`);
`reglas_incidencias.py` y su paso (D12); `universo_postventa.py`,
`universo_var.py`; el exportador Excel (D14); `domain/estados.py` de la api
(el 100 % no cambia); los `.env`; el repositorio `partes`.

## 6. Clases y funciones

### 6.1 api · `domain/vinculados.py` (domain, sin dependencias)

- `casar_vinculados(candidatos: list[RecursoVinculado], trabajadores:
  list[Trabajador]) -> ResultadoVinculos` — R2-R3: normaliza espacios
  extremos, exige `descripcion.endswith(" " + nombre)` y misma empresa;
  devuelve `vinculos` (vinculado → trabajador), `sin_trabajador`, `ambiguos`
  y `duplicados_por_tipo`. Determinista: el orden de entrada no cambia nada.
- La vigencia del vinculado reutiliza `domain/vigencia.vigente_en` (R4).

### 6.2 transfer · `application/services/reglas_vinculados.py` (puro)

- `synckey_vinculado(registro_id: int, recurso_ide: int) -> str` — R10.
- `hora_del_vinculado(horas: list[HoraRecurso]) -> HoraRecurso | None` — la
  marcada `defecto` (`res.horide`); sin ella, `None` (R11).
- `decidir_vinculados(titular: AccionLinea, linea: LineaEntrada,
  horas: dict[int, list[HoraRecurso]]) -> list[AccionVinculado]` — R8, R11,
  R12: copia `can`, `fec`, destino y parte del titular; `pre` de la hora;
  `tot = round(can × pre, 2)` como `stmt_insert_linea`.
- `partida_heredada(titular: AccionLinea) -> int | None` — R14 (postventa y
  VAR); en obra normal devuelve `None` y la pone la propuesta (R13).
- `es_linea_de(hora_codigo: str) -> Callable[[LineaSigrid], bool]` — el
  predicado de jornada del vinculado para `evaluar_capacidad` (R19) y para
  pisables (R17); `es_linea_mensual` sigue siendo el del trabajador (R15).
- Motivos como constantes (`MOTIVO_SIGUE_AL_TITULAR`, `MOTIVO_SIN_HORA`).

### 6.3 transfer · `PasoVinculados` (application)

`PasoVinculados(cliente, settings).preflight(pf, lineas, horas, contexto) ->
None` rellena `pf.vinculados` y añade sus conflictos a `pf.conflictos`:

1. `decidir_vinculados` por cada titular `escribir`/`ya_registrado`.
2. Partida: `partida_heredada` o, en obra normal, `proponer_partida` con el
   historial **del vinculado** (una lectura `historial_partidas(horas=[…])`
   solo si alguno la necesita) y `categoria` = descripción del tipo; sin
   propuesta, conflicto `sin_partida` por línea (R13).
3. Cuenta: `resolver_cuenta` con la hora del vinculado (R9).
4. Ya registrado por `hmores_ide` o `synckey` (R10, R26); identidad con
   `criterio_choque` sobre todos los partes del periodo (R16, R18); pisables
   al 0 % con `hora` (R17); capacidad con `es_linea_de` (R19).

`ejecutar_vinculados(res, pf_confirmado)` escribe tras los titulares, en el
mismo parte, con las sentencias de siempre (`stmt_insert_linea`,
`stmt_editar_linea(hora=…)`, `stmt_poner_a_cero(hora=…)`), en lotes de 15,
y omite el vinculado de un titular que no quedó escrito (R24).

## 7. SQL

### 7.1 Sigrid (solo lectura nueva; la escritura es la de siempre)

`config.yaml` de la api, `sync.vinculados.sql`, parametrizada (`IN` con un
`?` por tipo, nada concatenado), alias exactos:

```sql
SELECT r.ide AS ide, c.cod AS cod, CAST(c.res AS NVARCHAR(255)) AS descripcion, c.emp AS empresa,
       c.fecbaj AS fecbaj, t.cod AS tipo, CAST(t.res AS NVARCHAR(80)) AS tipo_res, r.horide AS horide
FROM res r JOIN con c ON c.ide = r.ide JOIN auxrestip t ON t.ide = r.restipide
WHERE r.cla = 0 AND t.cod IN (?, ?, ?)
```

Unas 750 filas (TF 398, CO 186, VE 160, con las de baja): sin paginar, con
`truncated` como error (como los empleados). En el transfer, solo cambia el
filtro de `historial_partidas` (§4); `horas_de_recursos` y
`lineas_de_partes` reciben más `recurso_ide`.

### 7.2 PostgreSQL `dedicacion` (ORM, única verdad)

- `recurso_vinculado`: `ide` (PK = `res.ide`), `trabajador_ide` (FK nula), `tipo`,
  `tipo_res`, `cod`, `descripcion`, `empresa`, `fecha_baja`, `horide`, `activo`,
  `estado_vinculo` (`casado`/`sin_trabajador`/`ambiguo`/`duplicado`), `sincronizado_en`.
- `registro_vinculado`: `id`, `asignacion_id` (FK), `vinculado_ide` (únicos los dos),
  `estado`, `motivo` (300), `parte_cod`, `sigrid_hmores_ide`, `actualizado_en`.

## 8. Contrato (api ↔ transfer)

Entrada, por línea: `vinculados: [{recurso_ide, tipo, categoria, hmores_ide?}]`,
opcional. Salida: `vinculados` (R21) si la petición trae alguno; sus conflictos,
en `conflictos` con `vinculado: {tipo, cod}`. La api nueva con un transfer viejo
no rompe (campo ignorado) pero **no registra vinculados**: se despliega
transfer → api → front.

## 9. Decisiones abiertas (las decide el humano; recomendada en negrita)

- **D1 · Tipos.** **A) TF, CO, VE** (lo que dijo Juan; los tres con importe
  mensual fijo); B) + `VIAJE` (lo nombró el humano el 2026-10-08; sin `pre`);
  C) + `VP`/`KM` (Juan lo excluye). Confirmar con Juan que «vehículo» es `VE`
  (`MESVE`) y no `VP`.
- **D2 · Vínculo.** **A) por nombre (cola) y empresa** (cada vinculado activo
  casado da un solo mensual; los no casados se ven en el preview para que
  Administración corrija la descripción); B) que Administración rellene
  `resres` en Sigrid (nativo y con fechas; hoy vacía, unas 300 altas); C)
  tabla editable en la app. B puede llegar después sin cambiar el contrato.
- **D3 · Importe.** **A) `reshor.pre`** (coincide en el 99 % de 2026); B) el
  `pre` de su línea del mes anterior; C) tecleado en la app.
- **D4 · Partida.** **A) obra normal: la propuesta de `#regla-partida` para el
  vinculado; postventa y VAR: la del titular**; B) código fijo por tipo en
  `config.yaml` (`CI.4.13`, `CI.4.1`, `CI.03P.9`) validado como hoja activa y,
  si no, A; C) siempre la del titular (en obra normal no es la práctica: 13
  de 2.076). En F-044 el vinculado **no** tiene selector propio de partida.
- **D5 · Cuenta.** **A) `#regla-analitica` tal cual** con su hora (97-100 %);
  B) cuenta fija por tipo.
- **D6 · Ya metido a mano.** **A) las reglas del titular**: pisado a confirmar
  por vinculado, al 0 % se edita sin confirmar, cerrado se omite; B) si el
  vinculado ya tiene cualquier línea en el periodo de la obra, se omite «metido
  a mano» y no se toca; C) A, pero su pisado se confirma con el del titular.
- **D7 · Varias obras y total ≠ 100.** **A) el mismo % en cada obra, una
  línea por titular, sin normalizar** (la práctica medida); B) solo en la obra
  de mayor %; C) normalizar al 100 % entre obras.
- **D8 · Vista.** **A) marca en el cuadrante y sección en el modal, sin
  edición**; B) solo el modal; C) subfilas editables (otra feature).
- **D9 · `synckey`.** **A) `porcentajes:vin:{registro_id}:{recurso_ide}`**;
  B) `porcentajes:{registro_id}:{tipo}` (se reutiliza si cambia el vinculado).
- **D10 · Titular omitido o ya registrado.** **A) omitido ⇒ el vinculado
  también; ya registrado ⇒ el vinculado se decide solo** (completa meses
  registrados antes de F-044); B) solo si el titular se escribe ahora.
- **D11 · Capacidad del vinculado.** **A) sí, sobrecarga a confirmar** (pilla
  la línea a mano con otra partida, que duplicaría el cargo); B) no.
- **D12 · Incidencias.** **A) no cambian a los vinculados** (unas vacaciones
  no rebajan el teléfono); B) otra regla, a definir con Juan.
- **D13 · Desde cuándo.** **A) desde 2026-10** (`sync.vinculados.desde`): los
  meses anteriores ya los cerró Administración a mano; B) cualquier periodo,
  con R18-R19 de red.
- **D14 · Excel.** **A) sin vinculados** (el modelo de Juan, F-040); B)
  añadirlos.
- **D15 · Tamaño.** **A) una feature en dos bloques**: T1-T6 (vínculo y vista,
  sin escritura) se pueden revisar antes que T7-T16; B) partirla en dos.

## 10. Riesgos, relaciones y avisos

- **`MESVE` empieza por `M`.** Todo filtro `LIKE 'M%'` que no vaya por el
  recurso del trabajador lo cuenta: capacidad, pisables, propuesta, la
  localización por `hmores_ide` (F-051 O2) y F-054. Tests de R15 con una
  línea `MESVE` en el parte del trabajador.
- **Nombre como vínculo.** Un renombrado en Sigrid lo deshace en el siguiente
  sync (el preview lo cuenta); nunca se casa por aproximación.
- **F-062** está `in_progress` sobre `registro_pipeline.py`: implementar F-044
  sobre `dev` **después** de unirse F-062, o rebasar antes de T7.
- **F-051**: se reutilizan sus guardas y su emparejado con la hora del
  vinculado; nada de su comportamiento con titulares cambia (R7).
- **F-058**: un titular con `can` 0 por redondeo se omite y arrastra a sus
  vinculados (R12). **F-052** (mensajería, hora `OTRO`) es una línea por obra,
  no por trabajador: no se mezcla aquí; podrá reutilizar `reglas_vinculados`
  para hora, `pre` y cuenta. **F-054** debe ignorar las líneas de vinculados
  (y `MESVE`) al traer porcentajes. **F-033** heredará el deshacer.
- **Aviso a `partes`** (lo transmite el humano): desde F-044 dedicación
  escribe y edita, en los partes compartidos, líneas `OTEL`, `OGAS` y
  `MESVE` de recursos no persona con `synckey porcentajes:vin:…`; nunca las
  borra; su `partes.md` debería decirlo.
- **Volumen**: unas 600 líneas más por mes (septiembre: TF 301, CO 182, VE
  129); `ejecutar` sigue por obra y en serie.
