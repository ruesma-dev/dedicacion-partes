<!-- specs/F-051-pisar-lineas-cero/design.md -->
# F-051 · Diseño

Requisitos en `requirements.md`; exploración y pasadas en
`progress/spec_F-051.md`. D1-D15 **decididas** (§9; D14 = A y D15 = A por el humano el
2026-10-20, «si me vale»); **spec aprobada**.

## 1. Servicios, límite y contrato

- **`dedicacion-transfer`** (casi todo): única pluma contra Sigrid. Estrena
  `UPDATE hmores` (`/api/sql/write` lo admite con `WHERE` obligatorio;
  `partes` F-046 ya lo usa) y **deja de emitir `DELETE`** en el registro.
- **`dedicacion-api`**: solo el contrato. Manda `hmores_ide` en cada línea
  (`asignacion.sigrid_hmores_ide`, columna que **ya existe**: sin ORM ni DDL
  nuevos) y guarda el de las ya registradas (R16). El transfer no tiene base:
  el `ide` lo guarda la api, como ya hacía tras cada escritura.
- **`dedicacion-front`**: solo el texto del pisado en el modal (R6), que hoy
  dice «se borran …»; lo pinta con lo que publica el transfer, sin decidir.
- **Contrato api → transfer:** `LineaIn.hmores_ide: Optional[int]`. **Transfer
  → api:** `escritas[].hmores_ide` (también de las editadas) y
  `escritas[].editada`, `ya_registradas_ide: {registro_id: ide}`, `editadas`,
  `a_cero`; `borradas` sigue (0). En el preflight, `Conflicto.edita_ide` y
  `Conflicto.a_cero_ides`; en la acción, `linea_cero`.
- **Orden de despliegue: transfer → api → front.** Transfer nuevo con api
  vieja: sin `hmores_ide` localiza por `synckey` (como hoy) y la api vieja
  ignora los campos nuevos. Front viejo con transfer nuevo diría «se borran»
  al editar: el front va justo detrás.
- `partes` no se toca (otro repositorio): §8.

## 2. Ficheros a crear (tests, sin red ni BBDD)

- `services/dedicacion-transfer/tests/test_f051_reglas_cero.py` — R1, R2, R7.
- `services/dedicacion-transfer/tests/test_f051_pipeline_cero.py` — preflight
  y ejecutar con el `ClienteFalso` (R3-R6, R8-R13, R15-R19) y el lote.
- `services/dedicacion-transfer/tests/test_f051_sql_cero.py` — SQL de §7 y
  respuesta de `POST /api/registro/ejecutar` (`TestClient`).
- `services/dedicacion-api/tests/test_f051_hmores_ide.py` — R14, R16.
- `services/dedicacion-front/tests/test_f051_modal_pisado.py` — R6 (texto).

## 3. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `application/services/reglas_porcentajes.py` | `es_linea_al_cero`, `pisables_al_cero`, `emparejar_ceros`, `synckey_tras_editar`, textos de aviso y motivo (§5) |
| transfer `domain/models/registro_models.py` | `LineaEntrada.hmores_ide`; `LineaSigrid` gana `pre`, `caaide`, `tex`, `parte_est`, `enlazada` (solo los rellena `lineas_para_editar`); `AccionLinea.linea_cero`; `Conflicto.edita_ide`, `a_cero_ides`; `ResultadoRegistro.editadas`, `a_cero`, `ya_registradas_ide` |
| transfer `application/pipelines/registro_pipeline.py` | pasos 6, 7 y 10 (§6) y su docstring |
| transfer `infrastructure/sigrid/sigrid_write_client.py` | `lineas_registradas`, `lineas_para_editar`, `stmt_editar_linea`, `stmt_poner_a_cero` (§7) |
| transfer `application/services/lecturas_lote.py` | la precarga de `synckey` pasa a `lineas_registradas` (claves **e** `ide`), misma ronda |
| transfer `interface_adapters/api/app.py` | `LineaIn.hmores_ide`; respuesta de `ejecutar` con los campos de §1 |
| transfer `prueba_escritura_porcentajes.py` | imprime `linea_cero`, `edita_ide`, `editadas`, `a_cero` |
| api `application/registro_sigrid.py` | `_payloads`: `hmores_ide`; `_trazar`: `sigrid_hmores_ide` de `ya_registradas_ide` |
| front `static/js/app.js` | detalle del aviso «Pisar»: «se edita la línea X … y queda …; quedan a 0: …» |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | R21, R22 |

**Tests anteriores que cambian (lista cerrada, tasks.md):** los que esperan
un `DELETE` del pisado (`borradas` ≥ 1 o `cli.borrados()` no vacío) pasan a
esperar la edición: `test_f002_pipeline.py` (los de las líneas 180-231 y
402-421), `test_f013_sin_partida.py` (585), `test_f037_pipeline.py` (546),
`test_pipeline_offline.py` (248); `test_f024_obra_destino_otra_empresa.py`
(65, claves de la respuesta); front `test_f049_avisos_registro.py`
(`test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo`); y `ANCLAS` de
`test_f002_fuente_unica.py`.

## 4. Ficheros que NO se tocan

- `criterio_choque`, `campos_identidad`, `CAMPOS_CLAVE`, `clave_conflicto`,
  `evaluar_capacidad`: la identidad y la capacidad no cambian.
- `stmt_borrar_linea` **se queda** solo para `limpiar` (D15); el pipeline no
  la llama (test: ningún `DELETE` en `escribir`).
- `stmt_insert_linea`, `stmt_crear_parte`, `estado_parte.py`,
  `cuenta_analitica.py` (copias de `partes`), `propuesta_partida.py`.
- api: ORM, esquema, `reemplazar` y copias; front: nada más que el texto.

## 5. Funciones puras (`reglas_porcentajes.py`)

```python
def es_linea_al_cero(ls) -> bool          # M*, can 0 o nulo, con recurso
def pisables_al_cero(existentes, accion, *, en_cerrado, mias) -> tuple
    # R1 (mismo recurso, al 0 %, fuera de en_cerrado y de mias; en
    # postventa misma partida), por ide
def emparejar_ceros(acciones, existentes, *, en_cerrado, mias)
    -> tuple[dict[int, LineaSigrid], dict[int, int]]
    # R2: {registro_id: pisable} y {recurso: pisables que quedan a 0}
def synckey_tras_editar(actual: str | None, nueva: str) -> str
    # R9: la de otro sistema se conserva; vacía o «porcentajes:…», la nueva
```

Leen recurso, hora y partida con los lectores de `criterio_choque`
(`_DE_LINEA`, `_DE_ACCION`). `can` se compara exacto con 0 (D4).

## 6. Pipeline

**6.1 Paso 6, ya registradas (R15).** `lineas_registradas(claves, ides)`
sustituye a `lineas_por_synckey` (una lectura, también en el lote). Una
acción es `ya_registrado` si la fila de su `hmores_ide` existe, es de su
recurso y su `synckey` no es `porcentajes:` de **otro** `registro_id`; si no,
si hay fila con su `synckey`. El `hmores_ide` de la ya registrada va a
`ya_registradas_ide`.

**6.2 Paso 7, pisado y pisables.** Con `en_cerrado` (ides de líneas de
partes cerrados): choques como hoy, **sin** las pisables (R3); choque en un
cerrado → `parte_cerrado` como hoy. Conflicto de pisado: `edita_ide` = el
choque de menor `ide` (uno por registro del conflicto, por `registro_id`) y
`a_cero_ides` = el resto (R4, R5). Las acciones **sin** choque y aún
`escribir` pasan por `emparejar_ceros`: `linea_cero` (lo leído: `ide`,
`hmoide`, parte, hora, partida, `fec`, `synckey`) y el aviso (R3).
`pisadas[recurso]` (capacidad) gana las pisables del recurso.

**6.3 `synckey` en una línea de Administración (decisión del spec-author,
D11 la deja abierta).** Se le pone **la nuestra** (`synckey` vacía no es de
otro sistema) **y** se localiza por `ide`. Motivos: (1) si la api no llega a
guardar el `ide` (cae entre la escritura y `_trazar`, o el `ejecutar` vence
por tiempo), la siguiente pasada la reconoce por `synckey` y no la toma por un
choque ajeno; (2) guardar la fila en el cuadrante recrea las asignaciones y
**pierde `sigrid_hmores_ide`** (`reemplazar`), igual que cambia la `synckey`:
ninguna de las dos sobrevive a una edición, y con las dos el pisado de hoy
sigue funcionando (nueva asignación → choque → confirmar → editar la misma
línea); (3) `limpiar`, la idempotencia de lo registrado antes de F-051 y F-033
siguen localizando por `synckey`. Solo una línea con `synckey` de otro
sistema depende únicamente del `ide`.

**6.4 Ejecutar, paso 10.** Con las acciones de `a_escribir`:

1. Reúne qué editar: `linea_cero` de cada acción y, de cada pisado
   confirmado con algún registro escribible (la R32 de hoy), su `edita_ide`
   por registro y sus `a_cero_ides`.
2. `lineas_para_editar(ides)`: **una** lectura con todo lo que tienen (R12).
   La que ya no cumple (pisable: al 0 %, recurso, `M*`, En registro; choque:
   misma identidad) saca su acción a `omitidas` con `MOTIVO_LINEA_CAMBIADA`.
3. `statements`: `stmt_editar_linea` por cada edición, `stmt_poner_a_cero`
   por cada `a_cero`, `stmt_insert_linea` por cada acción sin línea que
   editar (solo estas consumen `pos`). Ningún `DELETE`.
4. Log de cada edición y puesta a 0: `ide`, parte, `registro_id`, **antes**
   (la fila leída en 2, entera) y después (R18).
5. Tras `escribir`, la relectura de hoy pasa a `lineas_registradas` con las
   claves y los `ide` editados: una editada que no tiene nuestra `can` (y la
   `synckey` de R9) va a `omitidas` (R13); una `a_cero` que no quedó a 0, al
   log como aviso.

## 7. SQL (Sigrid, base `ruesma`)

```sql
-- lineas_registradas: hoy WHERE synckey IN (…); ahora
WHERE hmores.synckey IN (…) OR hmores.ide IN (…)       -- mismos campos + reside
-- lineas_para_editar(ides): ide, hmoide, reside, horide, auxhor.cod, paride,
--   can, pre, tot, caaide, fec, synckey, CAST(tex AS NVARCHAR(400)),
--   con.est del parte, y enlazada = CASE WHEN alguno de los enlaces <> 0
-- stmt_editar_linea
UPDATE hmores SET can = ?, pre = ?, tot = ?, horide = ?, paride = ?,
  caaide = ?, fec = ?, synckey = ? [, tex = ?]          -- tex solo en pruebas
WHERE ide = ? AND reside = ?
  AND ABS(ISNULL(can, 0) - ?) < 0.000001                -- el leído en 6.4.2
  AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ?             -- la leída
  AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0
  AND ISNULL(hdereside, 0) = 0 AND ISNULL(empdpreide, 0) = 0
  AND ISNULL(empabside, 0) = 0 AND ISNULL(emprccide, 0) = 0
  AND EXISTS (SELECT 1 FROM auxhor a WHERE a.ide = hmores.horide
              AND a.cod LIKE 'M%')
  AND EXISTS (SELECT 1 FROM con c WHERE c.ide = hmores.hmoide AND c.est = ?)
-- stmt_poner_a_cero: SET can = 0, tot = 0, con la misma guarda
```

- Redondeos de `stmt_insert_linea` (`can` a 4, `tot = round(can × pre, 2)`).
  La guarda ve la fila **antes** del cambio (semántica de SQL Server).
- **Lote:** `escribir` va en lotes de 15, cada uno una transacción; un
  `UPDATE` es una sentencia y no reserva `ide`. Si un lote posterior falla,
  lo editado ya lleva `synckey`/`ide` y reejecutar lo da por registrado.
- `escribir` devuelve filas por lote: R13 se decide con la relectura.
- Enlaces: los de `azure-apps/sigrid_tablas.md` y los que `partes` F-046 no
  edita; ninguna línea `M*` de 2025-2026 los tiene.

## 8. `partes` y F-044

- **Ninguna línea de `partes` es editable hoy:** escribe `H*` y `C*` y nunca
  ha escrito `M*` (0 de 358), y F-051 solo edita `M*` (pisables por D3;
  choques porque la hora es la `M*` del recurso). R9 es la red por si eso
  cambia.
- **Si se editara una**, conservando su `synckey`: su comprobación (F-024,
  por `synckey`, con `ide` solo para las que no la tienen) la seguiría dando
  por **presente**, y no la reaprobaría ni la reinsertaría. Su reajuste
  (F-046) solo edita sus líneas «con `can` igual a lo esperado» y con guarda
  que falla y revierte si algo cambió: tras nuestra edición su `can` ya no es
  el esperado y el reajuste de ese día **fallaría** sin tocarla (no la pisa de
  vuelta). Para nosotros, una línea así solo se reconoce por `hmores_ide`;
  perdido ese, la siguiente pasada la ve como choque y pide confirmar.
- **Coordinación:** al desplegar se les avisa (T16) de que el transfer edita
  sin borrar líneas `M*` de partes compartidos y de lo anterior; si algún día
  escriben `M*`, se revisa con ellos. Sin tocar su repositorio.
- **F-044:** las líneas al 0 % de teléfono, gasoil, KM y vehículo siguen
  igual (R7: otro recurso); F-044 podrá reutilizar `emparejar_ceros`.

## 9. Decisiones

**Decididas por el humano el 2026-10-20.** D1 = C (editar, nunca borrar);
D2 = A (pisable sin confirmar, con aviso); D3 = A; D4 (`can` 0 exacto o
nulo); D5 (cualquier línea al 0 %); D6 = A (cerrados como hoy); D7 = B; D8
fuera; D9 = A; D10 = B (se edita todo lo que insertaríamos); D11 (no se
cambia la `synckey` de otro sistema; se localiza por `hmores.ide`: §6.1,
§6.3); D12 (el pisado confirmado también edita, dentro de F-051); D13 (el log
guarda lo que tenía; F-033 la devolverá con un `UPDATE`).

**Abiertas:**

- **D14 · Pisado con varios choques** (en 2026, 63 grupos; PT26/00109 tiene
  hasta 9 líneas `MDEL`, una por día). (A) editar el de menor `ide` y poner
  los demás a 0 (`can`, `tot`; conservan hora, partida y fecha); (B) no
  pisar: omitir la acción con motivo y que Administración los junte;
  (C) editar uno y dejar los demás como están (seguirían sumando: sobrecarga).
  **Recomiendo A**: el resultado en importes es el de hoy (solo queda nuestro
  %) sin borrar, y lo que queda a 0 lo dice el modal antes de confirmar.
  **DECIDIDA: A** (humano, 2026-10-20).
- **D15 · `limpiar`** (script de pruebas: borra lo marcado `PRUEBA-PORC`
  en `tex` con nuestra `synckey`). (A) sigue borrando: no es registro
  real, y tras F-051 también borraría las líneas al 0 % que el humano creó a
  mano para la prueba (es la limpieza que se quiere); (B) pasa a dejar a 0:
  la 0404 acumularía líneas a 0 de cada prueba. **Recomiendo A**.
  **DECIDIDA: A** (humano, 2026-10-20; aclarado que no es el botón
  «Limpiar» de la vista principal, que solo vacía los filtros).

## 10. Riesgos y alternativas descartadas

- **Editar líneas ajenas en producción.** Acotado a `M*` del recurso, partes
  En registro, guarda con lo leído justo antes, relectura después y log con
  el estado anterior completo para devolverlo (F-033).
- **`ide` reutilizado.** El alta de líneas es `MAX(ide)+1`: si se borra la
  fila de mayor `ide`, otra puede heredar su número. R15 exige mismo recurso
  y que no sea `synckey` nuestra de otra asignación.
- **Una lectura más en `ejecutar`** (R12), ninguna en el preflight: el lote
  (F-055) no cambia de número de lecturas.
- **Descartado:** guardar el `ide` en una columna nueva (ya existe
  `sigrid_hmores_ide`); conservarlo al guardar la fila (rompería el pisado de
  hoy: un % cambiado se daría por «ya registrado»); si la guarda falla,
  insertar (sumaría encima de lo que Administración acabara de poner).
