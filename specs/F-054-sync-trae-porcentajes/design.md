<!-- specs/F-054-sync-trae-porcentajes/design.md -->
# F-054 · Diseño

Decisiones del 2026-10-24 **cerradas** (requirements §6). **Revisado el
2026-10-29** contra `dev` con F-044, F-062-F-065, F-067 y F-068 (merge
`ac56e96`; cambios en `progress/spec_F-054.md`); **D16-D18 pendientes** (§12).

## 1. Servicios, límite y contrato

**A: el transfer lee y traduce; la api compara y escribe; el front pinta.**
El transfer tiene la lectura `M*` con parte y estado, el casado de postventa,
el universo VAR y los ajustes de su `.env` (`POSTVENTA_OBRA_COD`,
`VAR_OBRA_COD`, `OBRA_PRUEBAS_COD`): leer desde la api copiaría el casado. La
api, dueña del dato, decide **por recurso** quién es trabajador, vinculado o
ajeno. **B: detecta y escribe el transfer; la api encamina**: «cubierta»
exige la partida resuelta de cada acción y los `ide` que reconoce el
preflight, que solo existen en el pipeline. **No es otro microservicio.**

**Contratos** (despliegue **transfer → api → front**; con el transfer viejo,
A da 502 con motivo y B no sale: ignora `completo`, sin `sobrantes`):

- `POST /api/porcentajes/existentes` (transfer, A): `{empresa, ano, mes,
  obras}` (las de `admite_postventa`) → `{ok, lineas_leidas,
  excluidas_pruebas, obra_postventa, motivo_postventa, obra_var, motivo_var,
  lineas: [R6 + destino, obra_origen_ide, var_paride, motivo]}`; 422 / 502.
- `POST /api/v1/periodos/{a}/{m}/traer-sigrid?empresa=` (api, A): `{aceptar:
  [{trabajador_ide, obra_ide, es_postventa}]}` (vacío = comparar) → R27 y
  `propuestas_en_curso`; 404 / 409 / 422 / 502.
- `POST /api/registro/preflight-lote` (B): `LoteIn.completo = false`; con
  `true`, la respuesta gana `sobrantes: [{clave = "cero:{hmores_ide}",
  hmores_ide, recurso_ide, vinculado (null o {tipo, cod, titular_ide}),
  obra_ide, obra_cod, parte_cod, parte_est, hora, paride, partida_cod, can,
  synckey, confirmable, motivo}]`; sin él, la respuesta de hoy.
- `POST /api/registro/poner-a-cero` (transfer, B): `{empresa, ano, mes,
  lineas: [{hmores_ide, recurso_ide, hora, vinculado, can, synckey}]}` →
  `{ok, puestas: [{hmores_ide, parte_cod, antes, despues}], omitidas}`.
- `registro/ejecutar` de la api: el cuerpo gana `sobrantes_a_cero` (esas
  líneas) y la respuesta, solo si vino alguna, `sobrantes_a_cero: {puestas,
  omitidas}`; el preflight, `sobrantes` solo si hay. **No** `a_cero`: ya es,
  por obra, lo que F-051 pone a 0 al pisar. El del transfer **no cambia**.

## 2. Ficheros a crear

Transfer `application/services/{porcentajes_existentes,reglas_obra_cero}.py`
(§4, §6.1) y `application/pipelines/poner_a_cero.py` (§6.3); api
`{domain,application}/traer_sigrid.py` (§5). Tests `test_f054_*.py`: transfer
`{lectura_mensuales,traduccion,endpoint,obra_cero,poner_a_cero}`, api
`{comparar,aceptar,rutas,registro_cero}`, front `{traer_front,modal_cero}`.

## 3. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `sigrid_write_client.py` | `lineas_mensuales_del_periodo(empresa, ano, mes, resides=None, solo_m=True)` (§4.1) |
| transfer `registro_models.py` · `lecturas_lote.py` · `registro_lote.py` | `LineaMensualSigrid`, `Sobrante` · `precargar(…, mensuales=False)`, ronda A · `preflight_completo` → `(resultados, sobrantes)` (§6.2) |
| transfer `app.py` | `ExistentesIn`, `LoteIn.completo`, `PonerACeroIn` y rutas |
| api `domain/{models,ports,errors}.py` | `TipoEvento.SIGRID`, resultados, `PorcentajesSigridGateway`, `aceptar_entrada`, error ⇒ 502 |
| api `transfer_client.py` | `porcentajes_existentes`, `poner_a_cero`; `preflight_lote(…, completo=False)`, en el cuerpo solo si es `true` |
| api `repositories.py` · `orm_models.py` | `aceptar_entrada` (§5.3) · solo el comentario de la traza |
| api `registro_sigrid.py` · `{routes,schemas,deps}.py` | `completo`, `sobrantes`, `sobrantes_a_cero` (§6.4) · ruta A |
| front `app.js` · `docs/{ARCHITECTURE,INTEGRACION}.md` | §7 · R29 (§8) |
| tests ajenos (lista cerrada) | `test_f002_fuente_unica.py` (`ANCLAS`); dobles `preflight_lote` de api `test_f0{22,24,55}_*.py` aceptan `completo` |

## 4. Transfer, parte A

### 4.1 La lectura (base `ruesma`)

```sql
SELECT h.ide, h.reside, m.obride, co.cod AS obra_cod, m.ide AS parte_ide,
       c.cod AS parte_cod, c.est AS parte_est, a.cod AS hora, h.can, h.fec,
       h.paride, p.cod AS par_cod, p.res AS par_res, h.synckey
FROM hmores h JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide
JOIN con co ON co.ide = m.obride JOIN auxhor a ON a.ide = h.horide
LEFT JOIN obrparpar p ON p.ide = h.paride
WHERE c.tip = ? AND ISNULL(m.reside, 0) = 0 AND m.ano = ? AND m.mes = ?
  AND co.emp = ? AND ISNULL(h.can, 0) <> 0
  [AND a.cod LIKE 'M%']                     -- solo_m (A y trabajadores de B)
  [AND h.reside IN (?…)]                    -- B: por recurso, en trozos
ORDER BY h.ide
```

Con `_lectura` (F-055); `truncated` ⇒ excepción; `en_registro = parte_est
== EST_PARTE_ACTIVO`. En A, sin `resides`: la api aparta las `MESVE` (R14).

### 4.2 `porcentajes_existentes.py`

`obras_por_partida(catalogo, obras)` (casado inverso con `casar_postventa`),
`traducir(linea, *, cod_pruebas, cod_postventa, cod_var, inverso,
catalogo_var, desde)` (`None` = pruebas) y `PorcentajesExistentes.calcular
(empresa, ano, mes, obras)`. Catálogos solo si alguna línea es de esa obra.

## 5. Api, parte A

### 5.1 Dominio puro (`domain/traer_sigrid.py`)

`entradas_por_trabajador(lineas, obras, *, empresa_obras, vinculados:
set[int]) -> (entradas por trabajador, no_traidas, contadores)`; `comparar
(lineas, entradas)` (R18); `a_linea(entrada, obra) -> Linea` (R17).
`EntradaSigrid`: obra, modo, %, partida, `hmores_ide` (menor), parte,
`n_lineas`. **Por recurso** (R14): trabajador del maestro → entrada; `ide`
de `recurso_vinculado` (activo o no) → `de_vinculados`; resto →
`fuera_maestro`. Ofrecible, `Linea.ofrecible`; épsilon, `domain/estados.py`.

### 5.2 `TraerDeSigrid.ejecutar(uow, anio, mes, usuario, *, filtro, aceptar)`

1. `_periodo_abierto_o_error` **antes** de llamar al transfer (R2); al
   transfer, las obras con `admite_postventa` de la empresa de las obras.
2. `entradas_por_trabajador` + `_filas_de_empresa` (visibles; vigentes por
   `activo`), y `comparar` por trabajador.
3. Por aceptada `distinta` o `solo_sigrid`, `aceptar_entrada`; las demás,
   con motivo (R20). Un evento `SIGRID` por trabajador con el snapshot de
   **toda** su fila antes y después con subfilas (el de `PARTIDA_VINCULADO`):
   deshacer (`reemplazar`, que las recrea) solo revierte lo aceptado (R25).
4. Se relee el periodo (cerrado entre medias ⇒ 409); un `commit` (R22). La
   ruta encola las propuestas de los tocados (R26).

### 5.3 `aceptar_entrada(periodo_id, trabajador_ide, linea, *, hmores_ide, parte_cod, usuario)`

`UPDATE` del ORM de la asignación con esa clave (misma fila e `id`: su
`synckey` y sus `asignacion_vinculado`, con `ON DELETE CASCADE`, no cambian)
o `INSERT` (subfilas automáticas); porcentaje, partida elegida, propuesta a
nulo y la traza de R23 (`sigrid_registrado_at/_by` nulos). Las otras filas
no se tocan: `reemplazar` borra y recrea sin traza. Sin ORM ni DDL nuevos.

## 6. Parte B

### 6.1 Reglas puras (`reglas_obra_cero.py`)

`cubierta(linea, acciones_del_recurso, *, pv_ide, var_ide, pruebas_ide,
modo_pruebas, reconocidas) -> bool`; `sobrantes(lineas, acciones,
vinculados, *, ajustes) -> list[Sobrante]`.

- **Cubierta** (R31) por **cualquier** acción del recurso, también omitida
  (la obra se la da la plataforma): normal, si alguna va a esa obra; en la
  de postventa, si alguna de postventa resolvió esa partida; en la VAR, si
  alguna tiene ese `var_paride`. En pruebas (R32), solo la 0404: si su `ide`
  está en `reconocidas` (ya registrada, choque, `linea_cero`) o alguna
  acción tiene su partida. **Vinculados** (R38, D16 = C): igual con las
  `AccionVinculado` de **ese** recurso (`Preflight.vinculados`: llevan
  `destino` y `paride`, también las omitidas «sigue al trabajador»).
- `confirmable = False` con motivo si su parte no está En registro o su
  `synckey` es de otro sistema (no vacía y sin `porcentajes:`; las
  `porcentajes:vin:` son nuestras). Orden por `hmores_ide`. Recursos: los de
  las **líneas** del lote (D14; no los que solo traen incidencias, F-062).

### 6.2 Detección en el lote

`preflight_completo`: `precargar(…, mensuales=True)` pone en la **ronda A**
(no depende de nada) la lectura de §4.1 con `solo_m` y los trabajadores y,
con D16 = C y vinculados, la de `solo_m=False` con ellos, en paralelo; corre
los preflights de siempre (también las peticiones de 4 elementos de F-062) y
calcula `sobrantes`; con `completo = false`, nada. R36: la sobrante que
comparte parte con una petición ya la lee `lineas_del_parte` y suma.

### 6.3 `PonerACero.ejecutar(empresa, ano, mes, lineas)`

1. `lineas_para_editar(ides)` (F-051 R12); en pruebas, además, la 0404.
2. Guarda previa: mismo recurso, `can`, `synckey` y hora (`M*`; la del
   vinculado, F-044 R24) = los enviados, sin enlaces, En registro, no de
   otro sistema y, en pruebas, en la 0404; si no ⇒ `omitidas` con motivo.
3. `stmt_poner_a_cero` de F-051 (`hora` si es de vinculado), lotes de 15;
   relectura (`lineas_registradas`): sin el 0 ⇒ `omitidas`. Log antes y
   después por línea (F-051 R18). Ningún `DELETE`.

### 6.4 Api y orden en `ejecutar`

`RegistroSigrid.ejecutar(…, sobrantes_a_cero)`: si trae alguna, **primero**
`poner_a_cero`; después las peticiones por obra de siempre, sin cambio. El
`ejecutar` del transfer repite su preflight releyendo del cliente real: la
puesta a 0 ya no suma y la omitida sí (R36). Por eso sobra el `a_cero_hechos`
de la versión del 2026-10-24 y `registro_pipeline.py` (con F-044 y F-062) no
se toca. En un parte compartido (postventa, VAR, 0404), la puesta a 0 puede
ser la línea al 0 % que `_emparejar_ceros` reutiliza para otra acción del
recurso: `#regla-cero` de hoy. **Coste (R37):** una lectura más por
preflight completo (dos con vinculados, en paralelo) en la ronda A; se mide
en local como F-055 T18 (2026-09, tres pasadas); más de un 15 % ⇒ **PARA**.

## 7. Front (`app.js`)

- A: `sincronizar()` devuelve `true`/`false`; `#btn-sync` pasa a
  `sincronizarYTraer()` (`test_f061_recarga.py` no cambia), que llama a
  `traerDeSigrid([])`; la ventana lista por trabajador sus entradas (estado,
  los dos %), con casilla en las `distinta` (desmarcada) y `solo_sigrid`
  (marcada, D12), y «Aceptar las marcadas» ⇒ `traerDeSigrid(aceptar)`.
- B: `pintarModalPreflight` gana «En Sigrid, en obras que no tiene en la
  plataforma» (las de vinculado con tipo y código): `.chk-cero` por
  confirmable, **desmarcada** (D17 A; sin `marcadaPorDefecto` ni `vistas` de
  F-064), y las demás como aviso. `registroEjecutar` manda
  `sobrantes_a_cero`, aparte de `pisar_claves`. `unirPreflight` conserva las
  claves de arriba (`...previo`): el repreflight de una obra mantiene la
  sección y sus casillas; un preflight nuevo las desmarca.

## 8. Documentación

`ARCHITECTURE.md` puntos **23** y **24** (el 22 es `#regla-vinculado`), con
efecto en `#regla-capacidad` y remisión desde `#regla-vinculado`; anclas y
tabla de acceso. `INTEGRACION.md` §1 (el transfer **pone a 0** líneas ajenas
sin borrar), §5, §7. Al desplegar, `azure-apps/dedicacion.md` y aviso a `partes`.

## 9. Tests (sin red ni BBDD)

Transfer: `ClienteFalso` con `_read` doble y `TestClient`; A nunca
`escribir` (R7); B: tres entradas y pruebas, omitida que cubre, cerrado,
otro sistema, guardas, nunca `DELETE`, la `MESVE` de un vinculado en el
parte del trabajador **no** es su sobrante, la obra sola no lee y el
completo lee **una** más (dos con D16 = C) en la ronda A. Api: dominio puro,
UoW en memoria de `test_f024_cuadrante_empresa.py`, `registro_sigrid` con
transfer doble (sin sobrantes, ni clave ni llamada); aceptar conserva
`asignacion_vinculado`. Front: node con dobles. Sigrid: solo T18-T19.

## 10. Ficheros que NO se tocan

Transfer `registro_pipeline.py`, `registro_vinculados.py`, `reglas_*.py`,
`rachas.py`, `propuesta_partida.py`, `universo_{postventa,var}.py` y las
copias de `partes`; api `sync_pipeline.py`, `propuestas_mes.py`,
`reemplazar`, `esquema.py`, `traza_vinculados.py`; `test_f061_recarga.py`.

## 11. Riesgos y alternativas descartadas

- Líder, 2026-10-23: `M*` al 100 % por recurso y mes en 730 de 756 meses con
  incidencia; `fec` el último día en el 94 %; `CI*`/`CIZ` con `can = tot = 0`.
- **B escribe en producción** líneas de Administración: solo `can`/`tot` a
  0, confirmada por línea, guarda doble y log del antes; MANUAL en pruebas.
- **Incidencias (F-030/F-062):** `CI*`/`CIZ` no entran (`M%`, `can` ≠ 0);
  poner a 0 una `M*` deja en su parte el `CI*`/`CIZ` y las rachas intactos.
- **Obra quitada:** su línea nuestra, sobrante (R34). **Traza perdida al
  guardar** (R24): pisado. **Otra hora `M*`** (F-011) y **capacidad
  conservadora** en postventa, VAR y 0404 (R36): sobrecarga a confirmar.
- **Aceptar con vinculados (≥ 2026-10):** cada vinculado se decide solo
  (F-044 R18): su línea en la partida que propone F-068 es un pisado
  (marcado, F-064); en otra, la suya avisa de sobrecarga (F-044 R23).
- **F-068** no cambia la partida traída (decide la del vinculado; la del
  titular manda si no es `CI*`, F-044 R17).
- **Descartado:** detectar desde la api; un `ejecutar` por obra para las
  sobrantes; A dentro de `POST /sync` (D1 C); `a_cero_hechos` (§6.4).

## 12. Decisiones nuevas (2026-10-29), pendientes (detalle: `progress/spec_F-054.md`)

- **D16. Vinculados en una obra sobrante** (lo dejó aquí F-044 §10). A)
  fuera: B solo `M*` del trabajador; quitar una obra deja vivas nuestras
  `porcentajes:vin:` y las manuales, contra `#regla-vinculado`. B) aviso sin
  escritura (la lectura de C). **C) como el trabajador (R38)**, con su hora
  en la guarda. *Recomendada C*; solo periodos ≥ `sync.vinculados.desde`.
- **D17. Casilla.** **A) desmarcada siempre**; B) la de un vinculado, marcada
  si su titular tiene sobrante en esa obra (como F-064). *Recomendada A*:
  poner a 0 una línea de otro no es seguir un cambio nuestro.
- **D18. A y vinculados.** **A) no traer nada** (`de_vinculados`); B) su
  partida como elegida de la subfila. *Recomendada A*: F-068 ya la propone
  (historial con el periodo) y su choque se pisa; B lee horas no `M*` y
  fija una elegida que ya no sigue al titular.
