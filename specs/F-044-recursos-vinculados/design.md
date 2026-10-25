<!-- specs/F-044-recursos-vinculados/design.md -->
# F-044 · Diseño: recursos vinculados con el % del trabajador

Evidencia en `progress/explore_F-044_sigrid.md`; decisiones en §9.

## 1. Servicios y límite

| Servicio | Qué hace en F-044 | Por qué ahí |
|---|---|---|
| `dedicacion-api` | El sync trae el vínculo (lectura de maestros por `sigrid-api`), lo guarda, guarda la partida elegida y la propuesta de cada subfila, manda los vinculados en el registro y guarda su traza | El vínculo es un **maestro**; `#regla-recurso`: la api manda el recurso y el transfer no lo elige; la elegida vive en la api (`#regla-partida`) |
| `dedicacion-transfer` | Propone la partida (la misma función en selector y preflight), decide y escribe: hora, importe, cuenta, parte, identidad, pisables, capacidad | **Única pluma** contra Sigrid; ya tiene parte del periodo, cuentas, propuesta y guardas |
| `dedicacion-front` | Columna «Tipo recurso», subfilas, selector de partida, sección del modal | Solo pinta lo que devuelve la api |

Sin microservicio nuevo (más líneas del mismo parte); `partes` no se toca (§10).

## 2. Encaje en el flujo

Sync: `conext` (campo «Recurso Asociado») + `res` + `auxrestip` →
`domain/vinculados.vincular` → `recurso_vinculado`. Cuadrante: por línea, una
subfila por vinculado con su elegida o su propuesta (que calcula el transfer,
como F-055). Registro: `_payloads` manda cada línea con sus `vinculados` → el
transfer decide los titulares **igual que hoy** (R11) y `PasoVinculados` crea
una `AccionVinculado` por (titular, vinculado) → `ejecutar` la escribe tras su
titular → `_trazar` guarda en `asignacion_vinculado`.

## 3. Ficheros a crear

- `services/dedicacion-api/domain/vinculados.py` — dominio puro (§6.1).
- `services/dedicacion-transfer/application/services/reglas_vinculados.py` —
  reglas puras: partida CI del tipo, línea del vinculado (§6.2).
- `services/dedicacion-transfer/application/pipelines/registro_vinculados.py`
  — `PasoVinculados` (§6.3), aparte para no engordar `registro_pipeline.py`.
- Tests `test_f044_*.py` en los tres servicios, sin red ni BBDD (`tasks.md`).

## 4. Ficheros a modificar

**api**
- `config/config.yaml` — `sync.vinculados`: `campo: "5"`, `desde: "2026-10"`,
  `tipos_excluidos: []` (D1b) y la SQL de §7.1.
- `domain/models.py` — `RecursoVinculado`; `Linea` gana sus subfilas.
- `infrastructure/db/orm_models.py` — `RecursoVinculadoORM`,
  `AsignacionVinculadoORM` (§7.2); `create_all` crea las tablas nuevas.
- `infrastructure/db/repositories.py` — upsert de vinculados, subfilas del
  periodo, elegida, propuesta guardada y traza.
- `application/sync_pipeline.py` — `FetchVinculadosStep` y
  `UpsertVinculadosStep` tras los trabajadores; bloque `vinculados` del
  preview (vinculados, sin campo, hacia un no trabajador).
- `application/use_cases.py` — cuadrante con subfilas (R6), cambiar la
  partida de una subfila con evento `PARTIDA_VINCULADO` (R8), deshacer y
  copiar mes la incluyen; propuestas en segundo plano también para subfilas
  (R9, la cola de F-055/F-057).
- `application/registro_sigrid.py` — `_payloads` añade `vinculados` (R10) y
  `_trazar` los guarda (R30); `_guardar_propuestas` las de subfila.
- `interface_adapters/api/routes.py` y `schemas.py` — `GET …/trabajadores/{ide}/partidas`
  y `PUT …/partida` aceptan `vinculado_ide` (opcional: sin él, como hoy).

**transfer**
- `domain/models/registro_models.py` — `VinculadoEntrada`,
  `LineaEntrada.vinculados` (`default_factory=list`), `AccionVinculado`,
  `Preflight.vinculados`, `ResultadoRegistro.vinculados`, `Conflicto.vinculado`.
- `application/services/reglas_porcentajes.py` — parámetros nuevos **con el
  valor de hoy por defecto**: `evaluar_capacidad(..., es_jornada=es_linea_mensual)`,
  `pisables_al_cero(..., hora=None)`; `criterio_choque` y `clave_conflicto`
  aceptan cualquier objeto con los campos de `campos_identidad()` (Protocol).
- `application/pipelines/registro_pipeline.py` — llama a `PasoVinculados` al
  final del preflight, tras los titulares en `ejecutar` y en `proponer`; las
  lecturas de horas y líneas incluyen los recursos de los vinculados.
- `application/services/lecturas_lote.py` — la precarga del lote incluye
  esos recursos y las cuentas del presupuesto (R29).
- `infrastructure/sigrid/sigrid_write_client.py` — `cuentas_del_presupuesto(obra_ide)`
  (§7.1); `stmt_editar_linea` y `stmt_poner_a_cero` pasan `hora` a `_guarda`,
  que ya la admite (anexo R30 de F-030).
- `interface_adapters/api/app.py` — `LineaIn.vinculados`, la salida y
  `partidas/propuesta(-lote)` con vinculados.
- `prueba_escritura_porcentajes.py` — `estado` lista las `porcentajes:vin:`;
  `limpiar` ya cubre el prefijo `porcentajes:` (comprobar en T17).

**front**: `static/js/app.js` (columna, subfilas, selector reutilizado de
F-050 con `vinculado_ide`, sección del modal en `pintarModalPreflight`) y
`static/css/styles.css`.

**docs**: `docs/ARCHITECTURE.md` (`#regla-vinculado` y remisiones),
`docs/INTEGRACION.md` §1/§5/§7, `ANCLAS` de `test_f002_fuente_unica.py`.

## 5. Ficheros que NO se tocan

`estado_parte.py` y `cuenta_analitica.py` (copias literales de `partes`: el
vinculado usa `resolver_cuenta` tal cual); `partida_catalog.py`,
`partida_matcher.py`, `text_match.py` (copias de `partes-persistencia`: la CI
del tipo va por cuenta, no por nombre); `propuesta_partida.py` (la propuesta
del titular no cambia); `reglas_incidencias.py` (D12); `universo_postventa.py`,
`universo_var.py`; el exportador Excel (D14); `domain/estados.py` de la api
(el 100 % no cambia); los `.env`; el repositorio `partes`.

## 6. Clases y funciones

### 6.1 api · `domain/vinculados.py` (domain, sin dependencias)

- `vincular(candidatos: list[RecursoVinculado], trabajadores: set[int]) ->
  ResultadoVinculos` — R2-R3: vínculo = valor del campo; devuelve `vinculos`,
  `sin_campo` y `hacia_no_trabajador` (con códigos, sin nombres).
  Determinista; un trabajador se queda con **todos** los suyos.
- Vigencia: `domain/vigencia.vigente_en` tal cual (R4).

### 6.2 transfer · `application/services/reglas_vinculados.py` (puro)

- `synckey_vinculado(registro_id: int, recurso_ide: int) -> str` — R13.
- `hora_del_vinculado(horas: list[HoraRecurso]) -> HoraRecurso | None` — la
  marcada `defecto` (`res.horide`); sin ella o con `pre` 0, `None` (R14).
- `partida_ci_del_tipo(hojas: dict[int, PartidaNodo], cuentas: dict[int, str],
  subcuenta: str) -> tuple[int | None, str]` — R15-R16: la única hoja activa
  con esa subcuenta; 0 o varias ⇒ `None` y el motivo (`sin_ci`, `varias_ci`).
- `partida_del_vinculado(titular: AccionLinea, vinculado: VinculadoEntrada,
  ci: tuple) -> (paride, metodo)` — orden: elegida válida → titular en
  postventa, VAR o partida no `CI*` ⇒ la del titular (R17) → la CI del tipo
  (R15) → sin partida (R16). Métodos: `manual`, `titular`, `ci_tipo`.
- `decidir_vinculados(titular, linea, horas) -> list[AccionVinculado]` — R12,
  R14, R18: `can`, `fec`, destino y parte del titular; `tot` redondeado como
  `stmt_insert_linea`.
- `es_linea_de(hora_codigo) -> Callable[[LineaSigrid], bool]` — predicado de
  jornada del vinculado para capacidad (R23) y pisables (R21);
  `es_linea_mensual` sigue siendo el del trabajador (R19).

### 6.3 transfer · `PasoVinculados` (application)

`preflight(pf, lineas, horas, ctx)` rellena `pf.vinculados` y añade sus
conflictos: (1) `decidir_vinculados`; (2) partida con `partida_del_vinculado`,
leyendo `cuentas_del_presupuesto` **una vez** por petición y solo si alguno
necesita la CI; (3) cuenta con `resolver_cuenta` y la hora del vinculado (R12);
(4) ya registrado por `hmores_ide`/`synckey` (R13, R30), identidad con
`criterio_choque` en todos los partes del periodo (R20, R22), pisables con
`hora` (R21), capacidad con `es_linea_de` (R23). `proponer(...)` devuelve la
propuesta y el catálogo de cada subfila con la misma función (R9, R29).
`ejecutar(res, pf)` escribe tras los titulares, en el mismo parte, con
`stmt_insert_linea`, `stmt_editar_linea(hora=…)` y `stmt_poner_a_cero(hora=…)`,
en lotes de 15, y omite el de un titular que no quedó escrito (R28).

## 7. SQL

### 7.1 Sigrid (lecturas nuevas; la escritura es la de siempre)

`config.yaml` de la api, `sync.vinculados.sql`, parámetros (`?` = el código
del campo), alias exactos:

```sql
SELECT r.ide AS ide, x.valn AS principal_ide, c.cod AS cod, CAST(c.res AS NVARCHAR(255)) AS descripcion,
       c.emp AS empresa, c.fecbaj AS fecbaj, t.cod AS tipo, CAST(t.res AS NVARCHAR(80)) AS tipo_res, r.horide AS horide
FROM conext x JOIN res r ON r.ide = x.conide JOIN con c ON c.ide = r.ide LEFT JOIN auxrestip t ON t.ide = r.restipide
WHERE RTRIM(x.cod) = ? AND RTRIM(x.camtab) = 'res' AND r.cla <> 1
```

Unas 560 filas: sin paginar, `truncated` es error. Transfer,
`cuentas_del_presupuesto(obra_ide)`: `SELECT p.ide, cc.cod FROM obrparpar p
JOIN con cc ON cc.ide = p.caaide WHERE p.obride = ? AND ISNULL(p.caaide,0) <> 0`
(hojas y alta las da el presupuesto que ya se lee); `horas_de_recursos` y
`lineas_de_partes` reciben más `recurso_ide`.

### 7.2 PostgreSQL `dedicacion` (ORM, única verdad)

- `recurso_vinculado`: `ide` (PK = `res.ide`), `trabajador_ide` (FK nula), `tipo`,
  `tipo_res`, `cod`, `descripcion`, `empresa`, `fecha_baja`, `horide`, `activo`,
  `estado_vinculo` (`vinculado`/`sin_campo`/`no_trabajador`), `sincronizado_en`.
- `asignacion_vinculado`: `id`, `asignacion_id` (FK), `vinculado_ide` (únicos
  los dos); elegida `partida_ide/cod/res`; `propuesta_*` como `asignacion`;
  traza `sigrid_estado`, `sigrid_motivo` (300), `sigrid_parte`,
  `sigrid_hmores_ide`. Fila solo cuando hay algo que guardar.

## 8. Contrato (api ↔ transfer)

Entrada, por línea: `vinculados: [{recurso_ide, tipo, categoria, paride?,
propuesta_*?, hmores_ide?}]`, opcional. Salida: `vinculados` (R25) si los trae;
sus conflictos, en `conflictos` con `vinculado: {tipo, cod}`. La api nueva con
un transfer viejo no rompe (campo ignorado) pero **no registra vinculados**:
se despliega transfer → api → front.

## 9. Decisiones

### 9.1 Decididas por el humano (2026-10-25)

- **D1 · Tipos**: «cualquier tipo vinculado al principal, pero casi siempre
  los que dices».
- **D2 · Vínculo**: «hay un campo personalizado que se ha añadido donde se
  vincula los recursos secundarios con el recurso principal»; «al sincronizar
  debe traer también esta info». Es `defext` 46 «Recurso Asociado». **Sin
  casado por nombre ni como aviso** (decisión del spec-author): el campo cubre
  el 96 % de los activos y coincide con el nombre donde se puede comparar; un
  segundo criterio solo produciría discrepancias que nadie atendería. Lo útil
  es lo que el preview ya lista: vinculados sin campo y campo hacia quien no es
  trabajador de dedicación, para que Administración los corrija.
- **D4 · Partida y %**: «hay una partida en CI para estas cosas, cada recurso
  de este tipo con un tipo de ci»; el %: «es la a.» — el mismo % del titular
  en cada obra, también postventa y VAR, sin normalizar (60 % normal + 40 %
  postventa ⇒ el vinculado, 60 % y 40 %). La CI del tipo es la hoja cuya
  cuenta tiene la subcuenta del vinculado (evidencia §7).
- **D7 · Varias obras**: resuelta con D4.
- **D8 · Vista**: «hay que mostrar en subfila el tipo para enseñar a que
  partida se vincula y poder cambiarlo. habra que añadir columna tipo
  recurso. no todos los trabajadores lo tiene».
- **Funcionamiento**: «al indicar porcentaje de aplicacion en una obra dicho
  porcentaje aplica tanto al recurso persona como a todos los asociados»; «si
  se pisa indicarlo igualmente, funciona como el porcentaje normal».

### 9.2 Abiertas (recomendada en negrita)

- **D1b · Tipos sin importe mensual** (KM, caja, viaje tienen `pre` 0 en
  `reshor`; un `VP` sí lo tiene). **A) se omiten con motivo visible «sin
  importe mensual» y `tipos_excluidos: [VP]`** (Juan: los km «de la manera
  habitual»); B) sin exclusión: solo cuenta el `pre`.
- **D3 · Importe.** **A) `reshor.pre`** (99 % en 2026); B) el `pre` de su
  línea del mes anterior.
- **D4b · Sin CI y fuera de obra normal.** **A) postventa, VAR y partida no
  `CI*` del titular ⇒ la partida del titular** (676/676 y 377/377 en 2026);
  **sin CI o con varias ⇒ «sin partida» a confirmar, elegible en la subfila**;
  B) postventa: la CI del tipo en el presupuesto de la obra de postventa; C)
  sin CI ⇒ la del titular sin preguntar.
- **D5 · Cuenta.** **A) `#regla-analitica`** con su hora (97-100 %).
- **D6 · Ya metido a mano.** **A) como el % normal**: pisado a confirmar por
  vinculado, al 0 % se edita sin confirmar, cerrado omitido; B) confirmar el
  del titular confirma los de sus vinculados.
- **D9 · `synckey`.** **A) `porcentajes:vin:{registro_id}:{recurso_ide}`**.
- **D10 · Titular omitido o ya registrado.** **A) omitido ⇒ también;
  ya registrado ⇒ se decide solo**; B) solo si el titular se escribe ahora.
- **D11 · Capacidad del vinculado.** **A) sí, sobrecarga a confirmar**; B) no.
- **D12 · Incidencias.** **A) no cambian a los vinculados.** **D13 · Desde
  cuándo.** **A) desde 2026-10**; B) cualquier periodo.
- **D14 · Excel.** **A) sin vinculados**; B) una fila por vinculado.
- **D15 · Tamaño.** **A) dos bloques en una feature** (T1-T8 vínculo y
  cuadrante, sin escribir en Sigrid; T9-T24 registro); B) partirla en dos.

## 10. Riesgos, relaciones y avisos

- **`MESVE` empieza por `M`**: todo filtro `LIKE 'M%'` que no vaya por el
  recurso del trabajador lo cuenta (capacidad, pisables, propuesta, F-051 O2,
  F-054). Tests de R19 con una `MESVE` en el parte del trabajador.
- **F-054** (traer los % de Sigrid al sincronizar): trae solo las `M*` de
  **trabajadores** (filtrando por su recurso, no por el prefijo); las líneas
  de vinculados no son asignaciones, porque su % es el del titular (R7). Lo
  que F-054 puede aprovechar de aquí, sin duplicarlo: la partida de la línea
  del vinculado en Sigrid como **elegida** de su subfila
  (`asignacion_vinculado`) y su `hmores.ide` para reconocerla al registrar.
  Lo diseña F-054.
- **F-062** está `in_progress` sobre `registro_pipeline.py`: implementar sobre
  `dev` **después** de unirse F-062, o rebasar antes de T9.
- Se reutilizan sin cambio F-050/F-055/F-057 (selector, propuesta guardada,
  cola, con `vinculado_ide`), F-051 (guardas) y F-058 (titular a 0 ⇒ vinculados
  omitidos). F-052 (mensajería, sin campo) es otra cosa; F-033, el deshacer.
- **Aviso a `partes`** (lo transmite el humano): desde F-044 dedicación escribe
  y edita en los partes compartidos líneas de recursos no persona con
  `synckey porcentajes:vin:…`, sin borrar nunca.
- **Volumen**: unas 600 líneas más al mes; `ejecutar` sigue por obra y en serie.
