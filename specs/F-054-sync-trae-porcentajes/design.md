<!-- specs/F-054-sync-trae-porcentajes/design.md -->
# F-054 · Diseño

Decisiones cerradas: D1-D15 el 2026-10-24 (requirements §6; D12 revisada el 2026-11-02) y D16-D19 (§12).
**Revisado el 2026-10-29** contra `dev` con F-044, F-062-F-065, F-067 y F-068 (`ac56e96`;
`progress/spec_F-054.md`). **Aprobada**; enmiendas T23 (2026-11-02), T24-T26 (2026-11-03, D20-D21) y T27 (2026-11-05, R48).

## 1. Servicios, límite y contrato
**A: el transfer lee y traduce; la api compara y escribe; el front pinta.** El transfer tiene la lectura
`M*` con parte y estado, el casado de postventa, el universo VAR y los ajustes de su `.env`
(`POSTVENTA_OBRA_COD`, `VAR_OBRA_COD`, `OBRA_PRUEBAS_COD`): leer desde la api copiaría el casado. La
api, dueña del dato, decide **por recurso** quién es trabajador, vinculado o ajeno. **B: detecta y
escribe el transfer; la api encamina**: «cubierta» exige la partida resuelta de cada acción y los `ide`
que reconoce el preflight, que solo tiene el pipeline. **No es otro servicio.** **T24-T26 (D20-D21):**
el front pinta (presentación); la api, los de obra (su base) y trabajador; el transfer, los de partida y
obras en sus motivos (`partida_cod` de §4.1, `codigo` de la api); T26: la api, el `partida_cod` de la
línea VAR. Sin lecturas nuevas (R47).

**Contratos** (despliegue **transfer → api → front**; con el transfer viejo, A da 502 con motivo y B no
sale: ignora `completo`, sin `sobrantes`; T25-T26 cambian solo el texto de los motivos):

- `POST /api/porcentajes/existentes` (transfer, A): `{empresa, ano, mes, obras}` (las de
  `admite_postventa`) → `{ok, lineas_leidas, excluidas_pruebas, obra_postventa, motivo_postventa,
  obra_var, motivo_var, lineas: [R6 + destino, obra_origen_ide, var_paride, motivo]}`; 422/502.
- `POST /api/v1/periodos/{a}/{m}/traer-sigrid?empresa=` (api): `{aceptar: [{trabajador_ide, obra_ide,
  es_postventa}]}` (vacío = comparar) → R27 y `propuestas_en_curso`; `no_traidas[]` + `recurso_cod`,
  `recurso_nombre` (T25); 404/409/422/502.
- `POST /api/registro/preflight-lote` (B): `LoteIn.completo = false`; con `true`, la respuesta gana
  `sobrantes: [{clave = "cero:{hmores_ide}", hmores_ide, recurso_ide, vinculado (null o {tipo, cod,
  titular_ide}), obra_ide, obra_cod, parte_cod, parte_est, hora, paride, partida_cod, can, synckey,
  confirmable, motivo}]`; sin él, la respuesta de hoy.
- `POST /api/registro/poner-a-cero` (transfer, B): `{empresa, ano, mes, lineas: [{hmores_ide,
  recurso_ide, hora, vinculado, can, synckey}]}` → `{ok, puestas: [{hmores_ide, parte_cod, antes,
  despues}], omitidas}`.
- `registro/ejecutar` de la api: el cuerpo gana `sobrantes_a_cero` (esas líneas) y la respuesta, solo si
  vino alguna, `sobrantes_a_cero: {puestas, omitidas}`; el preflight, `sobrantes` solo si hay. **No**
  `a_cero`: ya es, por obra, lo que F-051 pone a 0 al pisar. El del transfer, **igual**.

## 2. Ficheros a crear
Transfer `application/services/{porcentajes_existentes,reglas_obra_cero}.py` (§4, §6.1) y
`application/pipelines/poner_a_cero.py` (§6.3); api `{domain,application}/traer_sigrid.py` (§5). Tests
`test_f054_*.py`: transfer `{lectura_mensuales,traduccion,endpoint,obra_cero,poner_a_cero}`, api
`{comparar,aceptar,rutas,registro_cero}`, front `{traer_front,modal_cero}`.

## 3. Ficheros a modificar
| Fichero | Qué cambia |
|---|---|
| transfer `sigrid_write_client.py` | `lineas_mensuales_del_periodo(empresa, ano, mes, resides=None, solo_m=True)` (§4.1) |
| transfer `registro_models.py` · `lecturas_lote.py` · `registro_lote.py` | `LineaMensualSigrid`, `Sobrante` · `precargar(…, mensuales=False)`, ronda A · `preflight_completo` → `(resultados, sobrantes)` (§6.2) |
| transfer `app.py` | `ExistentesIn`, `LoteIn.completo`, `PonerACeroIn` y rutas |
| transfer `reglas_porcentajes.py` | solo `decidir`/`omitir`: la `Postv-` omitida tras resolver su partida la lleva (§6.1, D19; `cubierta` no cambia) |
| api `domain/{models,ports,errors}.py` | `TipoEvento.SIGRID`, resultados, `PorcentajesSigridGateway`, `aceptar_entrada`, error ⇒ 502 |
| api `transfer_client.py` | `porcentajes_existentes`, `poner_a_cero`; `preflight_lote(…, completo=False)`, en el cuerpo solo si es `true` |
| api `repositories.py` · `orm_models.py` | `aceptar_entrada` (§5.3) · solo el comentario de la traza |
| api `registro_sigrid.py` · `{routes,schemas,deps}.py` | `completo`, `sobrantes`, `sobrantes_a_cero` (§6.4) · ruta A |
| front `app.js` y `static/css/styles.css` · `docs/{ARCHITECTURE,INTEGRACION}.md` | §7 (T9, T15, T23, T24, T27) · R29 (§8) |
| T25-T26: transfer `universo_var.py`, `registro_pipeline.py` (solo dos motivos, T26) · api `registro_sigrid.py`, `domain/obras.py` (T26) · api `domain/{ports,traer_sigrid}.py`, `repositories.py`, `application/traer_sigrid.py`, `schemas.py` | solo `partida_var_de(…, *, partida_cod=None, obra_cod=None)` (§4.2) · `ObraRepository.codigos`, `NoTraida`/`NoTraidaOut` con `recurso_*`, `_obras`, `_nombre_obra` (§5.4) |
| tests ajenos (lista cerrada) | `test_f002_fuente_unica.py` (`ANCLAS`); dobles `preflight_lote` de api `test_f0{22,24,55}_*.py` aceptan `completo`; front `test_f050_modal_registro.py`, el `<select` de `test_f050_r29_…` acotado a la partida (T23; el humano, «a», 2026-11-02); T26 (D21): `test_f039_preflight_var.py`, `test_f002_postventa.py` y `test_f025_universo_postventa.py`, solo el texto esperado; api `test_f039_registro_var.py` y `test_f050_partida_linea.py`, la línea VAR con `partida_cod` |

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

Con `_lectura` (F-055); `truncated` ⇒ excepción; `en_registro = parte_est == EST_PARTE_ACTIVO`. En A,
sin `resides`: la api aparta las `MESVE` (R14).

### 4.2 `porcentajes_existentes.py`
`obras_por_partida(catalogo, obras)` (casado inverso con `casar_postventa`), `traducir(linea, *,
cod_pruebas, cod_postventa, cod_var, inverso, catalogo_var, desde)` (`None` = pruebas) y
`PorcentajesExistentes.calcular (empresa, ano, mes, obras)`. Catálogos solo si alguna línea es suya.
**T25 (R46):** `MOTIVO_PV_*` con `partida_cod or paride` y el `codigo or ide` de las obras;
`partida_var_de(…, *, partida_cod=None, obra_cod=None)` pone en `{paride}` y `{obra}` el código
(`traducir` pasa los de la línea). **T26 (R47, D21):** `CatalogoVar.codigos` (`{ide: cod}` de **todo**
el presupuesto que `cargar_catalogo_var` ya lee; vacío sin obra) y `partida_var_de` con
`codigos.get(var_paride) or partida_cod or var_paride`; el preflight (`registro_pipeline.py` l. ~680)
pasa `obra_cod=origen.codigo` y a `MOTIVO_PARTIDA_PV_NO_HOJA` (l. ~694), `linea.partida_cod`, el `cod`
de `nodos_pv` o el `paride`. `MOTIVO_VAR_POSTVENTA`/`_SIN_UNIVERSO`, el `linea.partida_cod` o el `ide`.
La api (`registro_sigrid.py`) pone en la línea VAR `partida_cod = partida_de_entrada(o.cod,
o.registro_obra_cod)` (`domain/obras.py`, inversa de `codigo_entrada`; si el `cod` no es
`<obra>-<partida>`, sin clave), nunca la elegida (F-050 R19). El transfer lee el `partida_cod` de la
petición solo bajo `if linea.paride` (l. ~705-711), que la VAR no trae: no decide nada. Marcadores
iguales (`test_f050_modal_registro.py`, igual).

## 5. Api, parte A
### 5.1 Dominio puro (`domain/traer_sigrid.py`)
`entradas_por_trabajador(lineas, obras, *, empresa_obras, vinculados: set[int]) -> (entradas por
trabajador, no_traidas, contadores)`; `comparar (lineas, entradas)` (R18); `a_linea(entrada, obra) ->
Linea` (R17). `EntradaSigrid`: obra, modo, %, partida, `hmores_ide` (menor), parte, `n_lineas`. **Por
recurso** (R14): trabajador del maestro → entrada; `ide` de `recurso_vinculado` (activo o no) →
`de_vinculados`; resto → `fuera_maestro`. Ofrecible, `Linea.ofrecible`; épsilon, `domain/estados.py`.

### 5.2 `TraerDeSigrid.ejecutar(uow, anio, mes, usuario, *, filtro, aceptar)`
1. `_periodo_abierto_o_error` **antes** de llamar al transfer (R2); al transfer, las obras con
   `admite_postventa` de la empresa de las obras.
2. `entradas_por_trabajador` + `_filas_de_empresa` (visibles; vigentes por `activo`), y `comparar`.
3. Por aceptada `distinta` o `solo_sigrid`, `aceptar_entrada`; las demás, con motivo (R20). Un evento
   `SIGRID` por trabajador con el snapshot de **toda** su fila antes y después con subfilas (el de
   `PARTIDA_VINCULADO`): deshacer (`reemplazar`, que las recrea) solo revierte lo aceptado (R25).
4. Se relee el periodo (cerrado entre medias ⇒ 409); un `commit` (R22); la ruta encola propuestas (R26).

### 5.3 `aceptar_entrada(periodo_id, trabajador_ide, linea, *, hmores_ide, parte_cod, usuario)`
`UPDATE` del ORM de la asignación con esa clave (misma fila e `id`: su `synckey` y sus
`asignacion_vinculado`, con `ON DELETE CASCADE`, no cambian) o `INSERT` (subfilas automáticas);
porcentaje, partida elegida, propuesta a nulo y la traza de R23 (`sigrid_registrado_at/_by` nulos). Las
otras filas no se tocan: `reemplazar` borra y recrea sin traza. Sin ORM ni DDL nuevo.

### 5.4 Códigos en los motivos y en `no_traidas` (T25, R45-R46)
`ObraRepository.codigos(ides) -> dict[int, str]` (port y `PgObraRepository`, `SELECT ide, cod`)
sustituye a `existen` en `_obras`: su `cod`, no `str(ide)` (`existen` sigue, `use_cases.py`).
`_nombre_obra`, VAR fuera de la base: `codigo_entrada(obra_cod, partida_cod)` con los dos, si no
`VAR-<var_paride>`; postventa sin origen en la base, su `ide` (reserva). `NoTraida`/`NoTraidaOut` +
`recurso_cod`, `recurso_nombre`.

## 6. Parte B
### 6.1 Reglas puras (`reglas_obra_cero.py`)
`cubierta(linea, acciones_del_recurso, *, pv_ide, var_ide, modo_pruebas, reconocidas) -> bool`;
`sobrantes(lineas, acciones, vinculados, *, ajustes) -> list[Sobrante]`.

- **Cubierta** (R31) por **cualquier** acción del recurso, también omitida (la obra se la da la
  plataforma): normal, si alguna va a esa obra; en la de postventa, si alguna de postventa tiene esa
  partida o se omitió antes de resolverla (P5 off o sin partida: `paride` 0, cubre todas; O2); la
  omitida después (sin recurso, %, sin `M*`) lleva `destino="postventa"`, `paride` y `partida_cod` y
  cubre solo esa (D19); nunca una normal de su obra de origen. En la VAR, si alguna tiene ese
  `var_paride`. En pruebas (R32), solo la 0404: si su `ide` está en `reconocidas` (ya registrada,
  choque, `linea_cero`) o alguna acción tiene su partida. **Vinculados** (R38, D16): igual con las
  `AccionVinculado` de **ese** recurso (`Preflight.vinculados`: llevan `destino` y `paride`; la omitida
  «sigue al trabajador» copia `destino` pero no `paride` (0): cubre todas, asimetría aceptada en D19).
- `confirmable = False` con motivo si su parte no está En registro o su `synckey` es de otro sistema (no
  vacía y sin `porcentajes:`; las `porcentajes:vin:` son nuestras). Orden por `hmores_ide`. Recursos:
  los de las **líneas** del lote (D14; no los que solo traen incidencias, F-062).

### 6.2 Detección en el lote
`preflight_completo`: `precargar(…, mensuales=True)` pone en la **ronda A** (no depende de nada) la
lectura de §4.1 con `solo_m` y los trabajadores y, con vinculados (D16), la de `solo_m=False` con ellos,
en paralelo; corre los preflights de siempre (también las peticiones de 4 elementos de F-062) y calcula
`sobrantes`; con `completo = false`, nada. R36: la del parte de una petición la suma `lineas_del_parte`.

### 6.3 `PonerACero.ejecutar(empresa, ano, mes, lineas)`
1. `lineas_para_editar(ides)` (F-051 R12); en pruebas, además, la 0404.
2. Guarda previa: mismo recurso, `can`, `synckey` y hora (`M*`; la del vinculado, F-044 R24) = los
   enviados, sin enlaces, En registro, no de otro sistema, en pruebas en la 0404 (si no, `omitidas` con
   motivo).
3. `stmt_poner_a_cero` de F-051 (`hora` si es de vinculado), lotes de 15; relectura
   (`lineas_registradas`): sin el 0 ⇒ `omitidas`. Log antes/después por línea (F-051 R18); sin `DELETE`.

### 6.4 Api y orden en `ejecutar`
`RegistroSigrid.ejecutar(…, sobrantes_a_cero)`: si trae alguna, **primero** `poner_a_cero`; después las
peticiones por obra de siempre, sin cambio. El `ejecutar` del transfer repite su preflight releyendo del
cliente real: la puesta a 0 ya no suma y la omitida sí (R36). Por eso sobra el `a_cero_hechos` de la
versión del 2026-10-24 y B no toca `registro_pipeline.py`. En un parte compartido (postventa, VAR,
0404), la puesta a 0 puede ser la línea al 0 % que `_emparejar_ceros` reutiliza para otra acción del
recurso: `#regla-cero` de hoy. **Coste (R37):** una lectura más por preflight completo (dos con
vinculados, en paralelo) en la ronda A; como F-055 T18 (local, 2026-09, 3 pasadas); > 15 % ⇒ **PARA**.

## 7. Front (`app.js`)
- A: `sincronizar()` devuelve `true`/`false`; `#btn-sync` pasa a `sincronizarYTraer()`, que llama a
  `traerDeSigrid([])`. **Ventana** (T23, R39-R42): `pintarTraerSigrid` pinta el resumen, los avisos, «No
  se traen» y **una** tabla con dos filas de cabecera (títulos ordenables y filtros); `abrirTraerSigrid`
  guarda el modelo `{filas, orden, filtros}` (fila: `t`, `e`, su índice en la respuesta, los textos
  pintados y `marcada = false`, D12) y repinta solo el `<tbody>` y el botón con dos puras:
  `filasTraerVisibles(filas, filtros, orden)` («contiene» en minúsculas y estado; orden estable, la raya
  al final en los dos sentidos) y `textoAceptarTraer(n, ocultas)`. La casilla cambia su `marcada`;
  «Desmarcar todas», todas; «Marcar las visibles», las del resultado con casilla; `aceptadasMarcadas()`
  lee **el modelo**, no el DOM (la oculta no se pinta) y manda como hoy. CSS en `styles.css`. Api,
  transfer y contrato no cambian; nada se guarda al cerrar.
- A, **T24** (R43-R45): las dos tablas, `tabla-reg filterable`, con el marcado de
  `renderCabeceraTabla()`: `th.th-sort` + `span.sort-arrow` (▲/▼); `tr.filter-row` con
  `div.filtro-celda` + `input.col-filter` («Contiene…»; Estado, `<select class="col-filter">`) y
  `button.filter-clear` «Limpiar» en la última columna; sin mover ni redimensionar. «Limpiar» vacía
  filtros y campos de **esa** tabla en su sitio (sin repintar la cabecera) y repinta su `<tbody>` y el
  botón; Escape en un filtro de texto lo vacía y dispara `input` (no cierra). Fuera `.tabla-traer
  th.ordenable`, `#traer-filtros th` y `.filtro-traer`. «No se traen»: puras
  `agruparNoTraidas(no_traidas)` (clave parte, obra, `recurso_ide`, motivo; orden de la primera; `n`) y
  `noTraidasVisibles(filas, filtros, orden)` (R40-R41; Líneas numérica, «×K» si K > 1); recurso,
  `recurso_cod · recurso_nombre` o el `recurso_ide`; modelo y filtros propios.
- A, **T27** (R48; el humano, 2026-11-05: «la del modal al sincronizar sigrid»): **solo** `styles.css`,
  acotada por los `id` que ya pinta `pintarTraerSigrid`: `.modal thead:has(> #traer-titulos), .modal
  thead:has(> #no-traidas-titulos) { position: sticky; top: 0; z-index: 2; background: var(--paper); }`:
  el `thead` entero (las dos filas, sin medir la primera); cada `th` ya trae fondo (burdeos, `--paper`).
  `top: 0` es el borde del área desplazable de `.modal`, sin hueco por su padding. `:has` exige Edge o
  Chrome ≥ 105; si la MANUAL ve hueco o transparencia, **PARA**. Ni `app.js` ni el registro ni F-070.
- B: `pintarModalPreflight` gana «En Sigrid, en obras que no tiene en la plataforma» (las de vinculado
  con tipo y código): `.chk-cero` por confirmable, **desmarcada** (D17; sin `marcadaPorDefecto` ni
  `vistas` de F-064), y las demás como aviso. `registroEjecutar` manda `sobrantes_a_cero`, aparte de
  `pisar_claves`. `unirPreflight` conserva las claves de arriba (`...previo`): el repreflight de una
  obra mantiene la sección y sus casillas; uno nuevo las desmarca.

## 8. Documentación
`ARCHITECTURE.md` puntos **23** y **24** (el 22 es `#regla-vinculado`), con efecto en `#regla-capacidad`
y remisión desde `#regla-vinculado`; anclas y tabla de acceso. `INTEGRACION.md` §1 (el transfer **pone a
0** líneas ajenas sin borrar), §5, §7; al desplegar, `azure-apps/dedicacion.md` y aviso a `partes`.

## 9. Tests (sin red ni BBDD)
Transfer: `ClienteFalso` con `_read` doble y `TestClient`; A nunca `escribir` (R7); B: tres entradas y
pruebas, omitida que cubre (D19), cerrado, otro sistema, guardas, nunca `DELETE`, la `MESVE` de un
vinculado no es sobrante de su trabajador, la obra sola no lee, el completo lee **una** más (dos con
vinculados) en la ronda A. Api: dominio puro, UoW en memoria de `test_f024_cuadrante_empresa.py`,
`registro_sigrid` con transfer doble (sin sobrantes, ni clave ni llamada); aceptar conserva
`asignacion_vinculado`. Front: node con dobles. T24: cabecera estándar, «Limpiar», Escape, tabla
agrupada; T25-T26: motivos con código y reserva, `codigos`, `recurso_*`; T27: la regla CSS acotada.
Sigrid: T18-T19.

## 10. Ficheros que NO se tocan
Transfer `registro_pipeline.py` (salvo T26), `registro_vinculados.py`, `rachas.py`,
`propuesta_partida.py`, `universo_postventa.py`, `universo_var.py` (salvo T25-T26), las copias de
`partes` y `reglas_*.py` salvo `omitir` (D19); api `sync_pipeline.py`, `propuestas_mes.py`,
`reemplazar`, `esquema.py`, `traza_vinculados.py`; `test_f061_recarga.py`, `use_cases.py`.

## 11. Riesgos y alternativas descartadas
- Líder, 2026-10-23: `M*` al 100 % por recurso y mes en 730 de 756 meses con incidencia; `fec` el último
  día en el 94 %; `CI*`/`CIZ` con `can = tot = 0`.
- **B escribe en producción** líneas de Administración: solo `can`/`tot` a 0, confirmada por línea,
  guarda doble y log del antes; MANUAL en pruebas.
- **Incidencias (F-030/F-062):** `CI*`/`CIZ` no entran (`M%`, `can` ≠ 0); poner a 0 una `M*` deja en su
  parte el `CI*`/`CIZ` y las rachas intactos.
- **Obra quitada:** su línea nuestra, sobrante (R34). **Traza perdida al guardar** (R24): pisado. **Otra
  hora `M*`** (F-011) y **capacidad conservadora** en postventa, VAR y 0404 (R36): sobrecarga.
- **Aceptar con vinculados (≥ 2026-10):** cada uno, solo (F-044 R18): en la partida que propone F-068,
  pisado (marcado, F-064); en otra, sobrecarga (F-044 R23). F-068 no cambia la partida traída (la del
  titular manda si no es `CI*`, F-044 R17).
- **D21, fuera de la ventana:** el modal del registro (y la omitida «sigue al trabajador» de F-044, que
  copia el motivo) nombra la partida por código; ninguno de estos textos se compara ni entra en
  `clave_conflicto` (solo `pisado`/`sobrecarga`/`sin_partida`). Agrupar es presentación.
- **Descartado:** detectar en la api; un `ejecutar` por obra; A en `POST /sync` (D1 C); `a_cero_hechos`.

## 12. Decisiones D16-D19, cerradas (D16-D18: «estoy de acuerdo», el humano, 2026-10-29; detalle: `progress/spec_F-054.md`)
- **D16 = C** (F-044 §10): vinculados como el trabajador (R38), confirmables por línea con su hora en la
  guarda; periodos ≥ `sync.vinculados.desde`. Descartadas A) fuera (dejaba vivas las `porcentajes:vin:`,
  contra `#regla-vinculado`), B) aviso. **D17 = A:** casilla desmarcada siempre; descartada B) marcar la
  del vinculado si su titular tiene sobrante (F-064). **D18 = A:** A no trae nada de vinculados
  (`de_vinculados`); descartada B) su partida como elegida (F-068 ya la propone).
- **D19 = b. `Postv-` omitida tras resolver su partida** (review 2, O7; el humano, 2026-10-30: «b», y
  «si» al plan): cubre solo esa partida (§6.1); descartada a) que las cubra todas. En Sigrid no cambia
  lo que se escribe. Efectos aceptados el 2026-10-30 tras T22 (4): el modal (`pintarModalPreflight`,
  también sus vinculados omitidos) muestra «Postventa» en Destino; el preflight (y el `print` de
  `prueba_escritura_porcentajes.py`) publica `destino`/`paride`/`partida_cod` y `clave_conflicto` lleva
  `|<paride>` («Aceptar»). El `AccionVinculado` omitido no copia `paride`: cubre todas, dirección
  segura; `reglas_vinculados.py` no se toca («Dejarlo así»).
