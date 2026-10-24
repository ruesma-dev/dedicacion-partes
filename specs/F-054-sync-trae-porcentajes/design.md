<!-- specs/F-054-sync-trae-porcentajes/design.md -->
# F-054 · Diseño

Requisitos en `requirements.md`. D4 y la parte B, **decididas** por el humano
el 2026-10-24; el resto (requirements §6), **abiertas** y escritas con la A.
Si el humano elige otra, el diseño se revisa antes de implementar.

## 1. Servicios, límite y contrato

**Parte A: el transfer lee y traduce; la api compara y escribe; el front pinta.**

- **Transfer.** Tiene la lectura de líneas `M*` con su parte y estado, el
  casado de postventa, el universo VAR y los ajustes (`POSTVENTA_OBRA_COD`,
  `VAR_OBRA_COD`, `OBRA_PRUEBAS_COD`) que solo viven en su `.env`: leer desde
  la api copiaría el casado (prohibido). Endpoint de **solo lectura**.
- **Api**, dueña del dato: compara y escribe asignación, traza y evento.
  **Front**: sin lógica. **No es otro microservicio**: mismos datos y pasarela.

**Parte B: detecta y escribe el transfer; la api encamina.** Saber si una
línea está «cubierta» exige la partida **resuelta** de cada acción (postventa,
VAR, pruebas) y los `ide` que reconoce el preflight: solo existen en el
pipeline, y la única pluma es el transfer. La api reenvía las confirmaciones.

**Contratos** (despliegue **transfer → api → front**; con el transfer viejo,
la api da 502 con motivo y el sync y el registro de siempre siguen):

- `POST /api/porcentajes/existentes` (transfer, A): `{empresa, ano, mes,
  obras: [{ide, codigo, nombre}]}` (las de la empresa de las obras con
  `admite_postventa`) → `{ok, lineas_leidas, excluidas_pruebas,
  obra_postventa, motivo_postventa, obra_var, motivo_var, lineas: [R6 +
  destino, obra_origen_ide, var_paride, motivo]}`; 422 / 502.
- `POST /api/v1/periodos/{a}/{m}/traer-sigrid?empresa=` (api, A): `{aceptar:
  [{trabajador_ide, obra_ide, es_postventa}]}` (vacío = solo comparar) → R27
  y `propuestas_en_curso`; 404 / 409 / 422 / 502.
- `POST /api/registro/preflight-lote` (B): el cuerpo gana `completo: bool`
  (la api lo pone sin `obra_ide`) y la respuesta, `sobrantes: [{clave =
  "cero:{hmores_ide}", hmores_ide, recurso_ide, obra_ide, obra_cod,
  parte_cod, parte_est, hora, paride, partida_cod, can, synckey,
  confirmable, motivo}]`.
- `POST /api/registro/poner-a-cero` (transfer, B): `{empresa, ano, mes,
  lineas: [{hmores_ide, recurso_ide, can, synckey}]}` → `{ok, a_cero:
  [{hmores_ide, parte_cod, antes, despues}], omitidas: [{hmores_ide,
  motivo}]}`. `registro/ejecutar` (transfer) gana `a_cero_hechos: [ide]`, y
  el de la api, `a_cero: [{hmores_ide, recurso_ide, can, synckey}]`.

## 2. Ficheros a crear

| Fichero | Qué |
|---|---|
| transfer `application/services/porcentajes_existentes.py` | A, §4 |
| transfer `application/services/reglas_obra_cero.py` | B, funciones puras (§6.1) |
| transfer `application/pipelines/poner_a_cero.py` | B, `PonerACero` (§6.3) |
| api `domain/traer_sigrid.py` · `application/traer_sigrid.py` | A, §5 |
| transfer `tests/test_f054_{lectura_mensuales,traduccion,endpoint,obra_cero,poner_a_cero}.py` | R1-R12, R31-R37 |
| api `tests/test_f054_{comparar,aceptar,rutas,registro_cero}.py`; front `tests/test_f054_{traer_front,modal_cero}.py` | R13-R28, R33, R35 |

## 3. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `sigrid_write_client.py` | `lineas_mensuales_del_periodo(empresa, ano, mes, resides=None)` (§4.1); lo de F-051 no cambia |
| transfer `registro_models.py` | `LineaMensualSigrid`, `Sobrante` |
| transfer `lecturas_lote.py` | `precargar(..., mensuales=False)`: la lectura de B en la primera ronda |
| transfer `registro_lote.py` | `preflight_completo(peticiones)` → `(resultados, sobrantes)`; `preflight` sin cambios |
| transfer `registro_pipeline.py` | `ejecutar(..., a_cero_hechos)`: esos `ide` no suman a la capacidad (R36) |
| transfer `app.py` | `ExistentesIn`, `completo`, `poner-a-cero`, `a_cero_hechos` |
| api `domain/{models,ports,errors}.py` | `TipoEvento.SIGRID`, resultados; `PorcentajesSigridGateway`; `AsignacionRepository.aceptar_entrada`; error ⇒ 502 |
| api `infrastructure/transfer/transfer_client.py` | `porcentajes_existentes`, `poner_a_cero`, `completo` |
| api `infrastructure/db/repositories.py` | `aceptar_entrada` (§5.3) |
| api `infrastructure/db/orm_models.py` | solo el comentario de la traza (también la escribe `traer_sigrid.py`) |
| api `application/registro_sigrid.py` | preflight con `completo` y `sobrantes`; `ejecutar(…, a_cero)` (§6.4) |
| api `interface_adapters/api/{routes,schemas,deps}.py` | ruta A; `a_cero` en el cuerpo de `ejecutar` |
| front `static/js/app.js` (+ `index.html` si hace falta) | §7 |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | R29 (§8) |
| transfer `tests/test_f002_fuente_unica.py` | `ANCLAS` + las dos anclas (lista cerrada) |

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
  AND co.emp = ? AND a.cod LIKE 'M%' AND ISNULL(h.can, 0) <> 0
  [AND h.reside IN (?…)]                    -- B: por recurso, en trozos
ORDER BY h.ide
```

Parametrizada, con `_lectura` (F-055); `truncated` ⇒ excepción; cientos de
filas: sin paginar. `en_registro = parte_est == EST_PARTE_ACTIVO`.

### 4.2 `porcentajes_existentes.py`

```python
def obras_por_partida(catalogo, obras) -> dict[int, list[ObraEntrada]]
    # casado inverso: casar_postventa de cada obra
def traducir(linea, *, cod_pruebas, cod_postventa, cod_var, inverso,
             catalogo_var, desde) -> LineaTraducida | None   # None = pruebas
class PorcentajesExistentes:  # calcular(empresa, ano, mes, obras) -> dict
```

Códigos normalizados (la lectura ya es de una empresa). Catálogos de
postventa y VAR solo si alguna línea es de esa obra: máximo cinco lecturas.

## 5. Api, parte A

### 5.1 Dominio puro (`domain/traer_sigrid.py`)

```python
def entradas_por_trabajador(lineas, obras: dict[int, Obra], *,
        empresa_obras) -> tuple[dict[int, list[EntradaSigrid]], list[NoTraida]]
def comparar(lineas: list[Linea], entradas: list[EntradaSigrid]
             ) -> list[EntradaComparada]     # R18: estado por entrada
def a_linea(entrada: EntradaSigrid, obra: Obra) -> Linea          # R17
```

`EntradaSigrid`: obra, modo, %, partida, `hmores_ide` (menor), parte,
`n_lineas`. Lo ofrecible, `Linea.ofrecible`; la épsilon, `domain/estados.py`.

### 5.2 `TraerDeSigrid.ejecutar(uow, anio, mes, usuario, *, filtro, aceptar)`

1. `_periodo_abierto_o_error` **antes** de llamar al transfer (R2).
2. Al transfer, las obras con `admite_postventa` de la empresa de las obras.
3. `entradas_por_trabajador` + `_filas_de_empresa` (visibles; vigentes por
   `activo`), y `comparar` por trabajador.
4. Por cada aceptada `distinta` o `solo_sigrid`: `aceptar_entrada`; las demás
   vuelven con motivo (R20). Un evento `SIGRID` por trabajador tocado, con el
   snapshot de **toda** su fila antes y después: deshacer (`reemplazar` al
   antes) solo revierte lo aceptado (R25).
5. Se relee el periodo (cerrado entre medias ⇒ 409); un `commit` (R22). La
   ruta encola las propuestas de los tocados (R26).

### 5.3 `aceptar_entrada(periodo_id, trabajador_ide, linea, *, hmores_ide, parte_cod, usuario)`

`UPDATE` del ORM de la asignación con esa clave (misma fila y `id`: su
`synckey` no cambia) o `INSERT` si no existe; porcentaje, partida elegida,
propuesta a nulo y la traza de R23 (`sigrid_registrado_at/_by` nulos). Las
otras filas del trabajador **no se tocan** (por eso no vale `reemplazar`, que
las recrea sin traza). Sin ORM ni DDL nuevos.

## 6. Parte B

### 6.1 Reglas puras (`reglas_obra_cero.py`)

```python
def cubierta(linea, acciones_del_recurso, *, pv_ide, var_ide,
             pruebas_ide, modo_pruebas, reconocidas: set[int]) -> bool
def sobrantes(lineas, acciones, *, recursos, ajustes) -> list[Sobrante]
```

- **Cubierta** (R31): normal, si alguna acción normal del recurso va a esa
  obra; en la obra de postventa, si alguna acción de postventa suya resolvió
  esa partida; en la VAR, si alguna tiene ese `var_paride`. En pruebas (R32),
  solo las de la 0404: cubierta si su `ide` está en `reconocidas` o alguna
  acción del recurso tiene su partida; las de otras obras no se miran.
- `confirmable = False` con motivo si su parte no está En registro o su
  `synckey` es de otro sistema (no vacía y sin `porcentajes:`, R34).
- Orden por `hmores_ide`: determinista. Recursos = los de las líneas del lote.

### 6.2 Detección en el lote

`preflight_completo`: `precargar(…, mensuales=True)` pone la lectura de §4.1
por recurso en la **primera ronda paralela**, corre los preflights de siempre
y calcula `sobrantes` con sus acciones; con `completo = false`, nada. R36: la
sobrante que comparte obra con una petición ya la lee `lineas_de_partes` y
suma como hoy (`evaluar_capacidad` no cambia).

### 6.3 `PonerACero.ejecutar(empresa, ano, mes, lineas)`

1. `lineas_para_editar(ides)` (F-051 R12); en pruebas, además los partes de la 0404.
2. Guarda previa: mismo recurso, `M*`, `can` y `synckey` = los enviados, sin
   enlaces, parte En registro, no de otro sistema y, en pruebas, en la 0404;
   la que no cumple ⇒ `omitidas` con motivo (pide volver a registrar).
3. `stmt_poner_a_cero` de F-051 (con su guarda en el `WHERE`), lotes de 15;
   relectura con `lineas_registradas`; la que no quedó a 0 ⇒ `omitidas`.
4. Log de antes y después por línea (como F-051 R18). Ningún `DELETE`.

### 6.4 Api y orden en `ejecutar`

`RegistroSigrid.ejecutar(…, a_cero)`: si trae alguna, **primero**
`poner_a_cero`; después las peticiones por obra de siempre, cada una con
`a_cero_hechos` = los `ide` que sí quedaron a 0 (así una omitida sigue
sumando en la capacidad, R36). El resultado gana `a_cero` y
`a_cero_omitidas`; el preflight publica `sobrantes` junto a las obras.
**Coste (R37):** una lectura más por preflight completo, en la primera ronda;
`ejecutar`, otra solo si hay confirmadas. Se mide en local como F-055 T18
(2026-09, antes y después, tres pasadas); más de un 15 % ⇒ **PARA**.

## 7. Front (`app.js`)

- A: `sincronizar()` devuelve `true`/`false`; `#btn-sync` pasa a
  `sincronizarYTraer()` (así `test_f061_recarga.py` no cambia), que llama a
  `traerDeSigrid([])`; la ventana lista por trabajador sus entradas (estado,
  los dos %), con casilla en las `distinta`/`solo_sigrid`, y «Aceptar las
  marcadas» ⇒ `traerDeSigrid(aceptar)` y `cargarPeriodo`.
- B: el modal de registro gana la sección «En Sigrid, en obras que no tiene
  en la plataforma»: una casilla «poner a 0» por `sobrante` confirmable y las
  demás como aviso con su motivo; `ejecutar` manda `a_cero` con los campos
  que publicó el preflight. El repreflight de una obra conserva la sección.

## 8. Documentación

- `ARCHITECTURE.md`: puntos 22 `#regla-traer-sigrid` y 23 `#regla-obra-cero`
  (y su efecto en `#regla-capacidad`), anclas, tabla de acceso y transfer.
- `INTEGRACION.md`: §1 (lectura nueva; el transfer **pone a 0** `M*` ajenas
  sin borrar), §5 (contratos de §1), §7 (orden). `azure-apps/dedicacion.md`
  al desplegar (líder) y aviso a `partes` (mismos partes).

## 9. Tests (sin red ni BBDD)

- Transfer: `ClienteFalso` con `_read` doble (`test_pipeline_offline.py`),
  endpoints con `TestClient`. A nunca llama a `escribir` (R7). B: cobertura
  en las tres entradas y en pruebas, cerrado y otro sistema, guardas previa
  y posterior, nunca `DELETE`, capacidad con y sin `a_cero_hechos`, el
  preflight de una obra no lee las mensuales y el completo hace **una** más.
- Api: dominio puro; UoW en memoria de `test_f024_cuadrante_empresa.py`,
  ampliada en el fichero nuevo; fixture `api` de `test_f024_rutas_empresa.py`;
  `registro_sigrid` con transfer doble (`poner_a_cero` primero). Front: node
  con dobles, como `test_f061_recarga.py`. Contra Sigrid, solo T18-T19.

## 10. Ficheros que NO se tocan

`reglas_porcentajes.py` (`criterio_choque`, `campos_identidad`,
`evaluar_capacidad`), `reglas_incidencias.py`, `propuesta_partida.py`; las
copias de `partes`; `universo_postventa.py` y `universo_var.py` (se llaman);
api `sync_pipeline.py`, `propuestas_mes.py`, `reemplazar`, `esquema.py`;
`partes` y `test_f061_recarga.py`.

## 11. Riesgos y alternativas descartadas

- **B escribe en producción** líneas de Administración: solo `can`/`tot` a
  0, confirmada por línea, con guarda doble y log del antes (para F-033).
  Por eso D13 recomienda partirla.
- **Obra quitada del cuadrante:** su línea nuestra pasa a sobrante (R34):
  es justo «una obra sin nada es un 0 %».
- **Traza perdida al guardar la fila** (R24) y **línea nuestra huérfana**:
  piden un pisado, como hoy. **Otra hora `M*`** (F-011): puede dar sobrecarga.
- **Capacidad conservadora:** una sobrante en la obra de postventa, la VAR o
  la 0404 puede dar sobrecarga en el preflight aunque se vaya a poner a 0; se
  confirman las dos. Descontarla antes escribiría de más si no se confirma.
- **Descartado:** leer o detectar desde la api (copiaría el casado y no
  tiene la partida resuelta); un `ejecutar` por obra para las sobrantes (la
  obra sin líneas no tiene petición); A dentro de `POST /sync` (D1 C).
- **F-062** puede reutilizar §4.1 con otro código; no se depende de su spec.
  **F-044**: los vinculados son otros recursos (`fuera_maestro`; fuera de B).
