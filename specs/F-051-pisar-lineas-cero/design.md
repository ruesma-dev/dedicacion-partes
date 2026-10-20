<!-- specs/F-051-pisar-lineas-cero/design.md -->
# F-051 · Diseño

Requisitos en `requirements.md`; exploración en `progress/spec_F-051.md`.
D1-D9 **decididas** el 2026-10-20 (D1 = C y D5 por el humano; el resto, las
recomendadas). **D10-D13 abiertas** (§9): el diseño sigue la recomendación.

## 1. Servicios y límite

- **Solo `dedicacion-transfer`**, la única pluma contra Sigrid (`CLAUDE.md`).
  Saber qué línea de un parte se puede editar exige leerlo, y eso solo lo
  hace el transfer. Estrena una sentencia `UPDATE` sobre `hmores`; hasta hoy
  solo hace `INSERT` y `DELETE`. `sigrid-api` la admite (`/api/sql/write`,
  `WHERE` obligatorio; `partes` F-046 ya hace `UPDATE hmores`).
- **api y front, sin cambios** (R18): el front pinta `a.aviso` (F-049); la
  api reenvía `acciones` y de `ejecutar` lee `escritas`, `omitidas` y
  `ya_registradas`. Una línea editada sale en `escritas` con su `hmoide` y,
  tras la relectura, su `hmores_ide`: la api la traza como una insertada.
- **`partes` no se toca** (otro repositorio); ver §8. Nada pide otro servicio.

## 2. Ficheros a crear

- `services/dedicacion-transfer/tests/test_f051_reglas_cero.py` — funciones
  puras (R1-R3, R6-R9).
- `services/dedicacion-transfer/tests/test_f051_pipeline_cero.py` —
  preflight y ejecutar con el `ClienteFalso` (R4, R5, R8-R11, R13-R17) y el
  lote (`RegistroLote.preflight` da lo mismo).
- `services/dedicacion-transfer/tests/test_f051_sql_cero.py` — texto y
  parámetros del `UPDATE` con guarda (R10-R12) y `pisadas_cero` en la
  respuesta de `POST /api/registro/ejecutar` (R15, `TestClient`).

## 3. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/services/reglas_porcentajes.py` | `es_linea_al_cero`, `pisables_al_cero`, `emparejar_ceros`, `AVISO_LINEA_CERO`, `AVISO_CEROS_QUEDAN`, `MOTIVO_CERO_CAMBIADA` (§5) |
| `domain/models/registro_models.py` | `AccionLinea.linea_cero: dict | None` y `ResultadoRegistro.pisadas_cero: list[dict]` |
| `application/pipelines/registro_pipeline.py` | paso 7: emparejado y choques sin pisables; paso 10: `UPDATE` en vez de `INSERT`; comprobación tras escribir (§6) |
| `infrastructure/sigrid/sigrid_write_client.py` | `stmt_actualizar_linea_cero` (§7) |
| `interface_adapters/api/app.py` | la respuesta de `ejecutar` gana `pisadas_cero` |
| `prueba_escritura_porcentajes.py` | `preflight` imprime `linea_cero`; `ejecutar`, `pisadas_cero` (solo salida) |
| `tests/test_f002_fuente_unica.py` | `ANCLAS` gana `"regla-cero"` (única aserción anterior que cambia) |
| `docs/ARCHITECTURE.md` | regla `#regla-cero`; remisión desde `#regla-conflicto` y el índice de anclas (R19) |
| `docs/INTEGRACION.md` | §1 (qué escribimos: el primer `UPDATE`) y §7 (qué se rompe) (R20) |

Rutas relativas a `services/dedicacion-transfer/` salvo las de `docs/`.

## 4. Ficheros que NO se tocan

- `criterio_choque`, `campos_identidad`, `CAMPOS_CLAVE`, `clave_conflicto`:
  la identidad no cambia; las pisables se **apartan** antes de buscar
  choques (§6). `evaluar_capacidad`: las recibe en `pisadas`.
- `stmt_borrar_linea`, `stmt_insert_linea` y el pisado confirmado: siguen
  borrando e insertando hasta que se decida D12.
- `lineas_del_parte` / `lineas_de_partes`: ya traen recurso, hora, partida,
  `can`, `fec` y `synckey`; **ninguna lectura nueva** (R17). Los enlaces y el
  estado del parte solo se miran en la guarda (§7).
- `estado_parte.py`, `cuenta_analitica.py` (copias de `partes`),
  `propuesta_partida.py`, `lecturas_lote.py`, `registro_lote.py`; todo
  `dedicacion-api` y `dedicacion-front`.

## 5. Funciones nuevas (application, puras)

En `reglas_porcentajes.py`, junto al bloque de identidad, leyendo recurso,
hora y partida con los lectores de `criterio_choque` (`_DE_LINEA`,
`_DE_ACCION`):

```python
def es_linea_al_cero(ls: LineaSigrid) -> bool:
    """Hora M* (`es_linea_mensual`), `can` 0 o nulo (exacto, D4) y con
    recurso. ARCHITECTURE.md#regla-cero."""

def pisables_al_cero(existentes, accion, *, en_cerrado: set[int],
                     mias: set[str]) -> tuple[LineaSigrid, ...]:
    """R1: al cero, mismo recurso, `ide` fuera de `en_cerrado`, `synckey`
    fuera de `mias` y sin prefijo `partes:` (D11), y en postventa misma
    partida (D7). Por `ide`. Una acción no `escribir` no pisa nada."""

def emparejar_ceros(acciones, existentes, *, en_cerrado, mias
                    ) -> tuple[dict[int, LineaSigrid], dict[int, int]]:
    """R2: por recurso y `registro_id`, a cada acción la pisable libre con
    clave (partida distinta, hora distinta, ide). Devuelve
    {registro_id: línea} y {recurso: pisables que se quedan a 0}."""
```

`can` se compara **exacto** con 0 (`_can(ls.can) == 0.0`), igual que la
guarda SQL (`ISNULL(can, 0) = 0`). El prefijo `partes:` vive en una
constante de este módulo, al lado de la de `PREFIJO_SYNCKEY`.

## 6. Pipeline

**Preflight, paso 7** (por destino + periodo, con `existentes` de todos los
partes del periodo y `donde[ide]` ya leídos):

1. `en_cerrado = {ls.ide for ls in existentes if donde[ls.ide].cod in
   parte.cerrados}`; `ceros` = unión de `pisables_al_cero` de las acciones
   del grupo.
2. Choques de cada acción **sin** los `ide` de `ceros` (R5). Si uno está en
   un cerrado, la acción se omite como hoy (R8). El `contexto` de un
   conflicto excluye `ceros`.
3. Con las acciones que siguen en `escribir`: `emparejar_ceros`. A cada
   emparejada, `a.linea_cero = {ide, hmoide, parte_cod, horide, hora_codigo,
   paride, fecha_int, synckey}` (lo **leído**) y el aviso de R4 (con la
   partida que tenía la línea: el usuario puede elegirla si prefiere esa);
   si al recurso le quedan, el aviso de que quedan N a 0.
4. Paso 7 bis: `pisadas[recurso]` gana los `ceros` del recurso (suman 0; el
   `contexto` de la sobrecarga ya no los lista).

**Ejecutar, paso 10.** Orden de `statements`: borrados de pisados
confirmados (como hoy), después un `stmt_actualizar_linea_cero` por cada
acción de `a_escribir` con `linea_cero`, después las inserciones de las
demás (solo ellas consumen `pos`). La entrada de `escritas` de una editada
lleva `hmoide` y `parte_cod` de **su** parte (puede no ser el elegido para
insertar) y `hmores_ide` = su `ide`. `a_escribir` ya excluye las retenidas
(R14).

**Tras escribir** (la relectura por `synckey` de hoy, sin lectura nueva): una
editada cuya `synckey` no aparece, o aparece en otro `ide`, sale de
`escritas` y va a `omitidas` con `MOTIVO_CERO_CAMBIADA` (R13); las demás van
a `pisadas_cero` con `registro_id` y lo que tenía la línea (R15), y al log.

`ejecutar` rehace el preflight antes de escribir: la ventana entre lo leído y
el `UPDATE` es de segundos y la guarda cubre lo que cambie en ella.

## 7. SQL (Sigrid, base `ruesma`, solo el transfer)

Sin SQL de PostgreSQL. Sentencia nueva junto a `stmt_insert_linea`, con los
mismos redondeos (`can` a 4, `tot = round(can × pre, 2)`):

```sql
UPDATE hmores SET can = ?, pre = ?, tot = ?, horide = ?, paride = ?,
  caaide = ?, fec = ?, synckey = ? [, tex = ?]     -- tex solo en pruebas
WHERE ide = ? AND reside = ? AND ISNULL(can, 0) = 0
  AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ?          -- la leída
  AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0
  AND ISNULL(hdereside, 0) = 0 AND ISNULL(empdpreide, 0) = 0
  AND ISNULL(empabside, 0) = 0 AND ISNULL(emprccide, 0) = 0
  AND EXISTS (SELECT 1 FROM auxhor a WHERE a.ide = hmores.horide
              AND a.cod LIKE 'M%')
  AND EXISTS (SELECT 1 FROM con c WHERE c.ide = hmores.hmoide
              AND c.est = ?)                         -- En registro
```

- **No cambian** `hmoide`, `pos`, `cenide`, `obride`, `ano`, `mes`, `fac`,
  `ortide` ni el resto: la línea sigue en su parte, de la misma obra y mes
  (en pruebas, la 0404). Los `EXISTS` y la guarda ven la fila **antes** del
  cambio (semántica de `UPDATE` en SQL Server).
- **Lote:** `escribir` manda las sentencias en lotes de 15, cada uno una
  transacción; el `UPDATE` es una sola sentencia y no reserva `ide`. Si un
  lote posterior falla, las editadas ya llevan nuestra `synckey` y reejecutar
  las da por registradas y completa el resto (R16).
- `escribir` devuelve filas afectadas por lote, no por sentencia: por eso R13
  se decide con la relectura por `synckey`, no con ese número.
- Los enlaces son los de `azure-apps/sigrid_tablas.md` (`hmores`) y los que
  `partes` F-046 se niega a editar; en 2025-2026 ninguna línea `M*` los tiene.

## 8. Coordinación con `partes` y con F-044

- **Mismo parte.** `partes` escribe `H*` y `C*` con `synckey partes:…`; nunca
  ha escrito `M*` (exploración). Con D3 y D11 (C) ninguna línea suya se edita.
  Su comprobación (F-024) busca sus líneas por `synckey` y, sin ella, por
  `ide`; su reajuste (F-046) solo edita las suyas con el `can` esperado. Si
  un día una línea suya fuera pisable y se editara, la daría por borrada
  (`borrado_sigrid`) y al reaprobar la **reinsertaría**: por eso D11.
- **Qué cambia para ellos:** el transfer edita, sin confirmar, líneas `M*`
  de Administración en partes que también usan. Se les avisa al desplegar
  (T12), sin tocar su repositorio.
- **F-044:** las líneas al 0 % de teléfono, gasoil, KM y vehículo **siguen a
  0** tras F-051 (R6). F-044 debería reutilizar `emparejar_ceros` con su
  propia definición de «al 0 %» (hora no `M*`).

## 9. Decisiones

**Decididas el 2026-10-20.** D1 = **C** (editar en su sitio, nunca borrar);
D2 = A (sin confirmar, con aviso); D3 = A (cualquier `M*` al 0 % del recurso
en la obra); D4 (`can` exacto 0 o nulo); D5: **cualquier** línea al 0 %, con
o sin `synckey` (matiz en D11); D6 = A (cerrados como hoy); D7 = B (en
postventa, solo misma partida); D8 fuera; D9 = A (las líneas al 0 % de la
prueba, a mano en Sigrid).

**Abiertas (D1 = C y D5 las abren):**

- **D10 · Qué campos se editan.** (A) solo el valor: `can` y `tot = can ×
  pre` de la línea, conservando hora, partida, cuenta, `pre` y `fec` de
  Administración. Deja incoherente: la partida de Sigrid no es la elegida o
  propuesta que enseñan el cuadrante y el modal (rompe «lo que se ve es lo
  que se registra», `#regla-partida`); la hora puede no ser el `M*` que elige
  P1 y su `pre` es el copiado del mes anterior (`tot` distinto del que vio el
  usuario); `escritas.partida_cod` (y lo que la api traza) no casa con
  Sigrid; la cuenta sí queda coherente con su partida. (B) todo lo que
  insertaríamos (`can`, `pre`, `tot`, hora, partida, cuenta, `fec`,
  `synckey`): la línea queda idéntica a una insertada salvo `ide` y `pos`; se
  pierde la partida de Administración, que era copia del mes anterior y que
  la propuesta «parte anterior» suele dar igual (en la 0707, sí). Una línea
  confirmada «sin partida» dejaría `paride = 0` donde había partida: el aviso
  de R4 enseña esa partida para elegirla antes. **Recomiendo B.**
- **D11 · `synckey`, `tex` y líneas de `partes`.** La `synckey` pasa a ser la
  nuestra (`porcentajes:{id}`): sin ella no hay idempotencia (la siguiente
  pasada no la reconocería, la vería con `can` ≠ 0 y pediría pisado). `tex`:
  en pruebas, la marca (`limpiar` y la traza la necesitan); en real, el que
  tenía (comentario de Administración). Líneas de `partes`: (A) editarlas
  también, con nuestra `synckey` (D5 al pie de la letra; `partes` la daría por
  borrada y podría reinsertarla: doble imputación); (B) editarlas conservando
  la suya (rompe nuestra idempotencia); (C) excluirlas. Hoy hay **0** casos.
  **Recomiendo C** (es una excepción a D5: la confirma el humano). Una con
  nuestra `synckey` de otra asignación (D5) sí se edita: esa asignación, si
  sigue viva, se volverá a insertar al registrarla.
- **D12 · ¿«Nunca borramos» alcanza a lo de hoy?** Hoy borran: el pisado
  confirmado (línea distinta de 0 con la misma identidad, `#regla-conflicto`:
  `DELETE` + `INSERT`) y `limpiar` del script (solo lo nuestro marcado
  `PRUEBA-PORC`). **Recomiendo** dejarlo fuera de F-051 y abrir una feature
  que convierta el pisado confirmado en `UPDATE` (reutilizando esta sentencia
  con guarda por el `can` leído); `limpiar`, como herramienta de pruebas, se
  queda. Hasta entonces el pisado confirmado sigue borrando.
- **D13 · Cómo se deshace un `UPDATE`.** Borrar por `synckey` (F-033, hoy
  `limpiar`) eliminaría la línea de Administración, que existía antes. (A) el
  transfer publica y registra en el log lo que tenía (R15: hora, partida,
  `fec`, `synckey`; `pre`, cuenta y `tex` no se leen hoy) y F-033 decide; mi
  recomendación para F-033: devolverla a 0 con `UPDATE` guardado por nuestra
  `synckey`, sin borrar. (B) guardar el estado anterior en la api (columna
  nueva en `asignacion`): sale de «solo transfer» y amplía las lecturas.
  **Recomiendo A.**

## 10. Riesgos y alternativas descartadas

- **Editar sin confirmar en producción** (D2). Acotado por R1 (recurso propio,
  `M*`, al 0 %, En registro), la guarda (R12) y R14. Lo peor: que una línea
  que imputaba 0 pase a llevar nuestro %, que es lo pedido.
- **Quedan líneas a 0** si el recurso tiene más pisables que acciones (R4 lo
  avisa): con D1 = C no se borran. En la 0707, una por persona.
- **La propuesta de partida ve las líneas al 0 %** (F-050, «parte anterior»
  cuenta el mes en curso, con suma 0): con una, propone su partida; con dos de
  partidas distintas, empate. F-051 no lo cambia (R17).
- **Descartado: si la guarda falla, insertar** (`INSERT … WHERE NOT EXISTS`
  por `synckey`, como `partes` F-046). Si falló porque Administración acaba de
  poner un valor, sumaríamos encima; mejor omitir y que se vuelva a registrar.
- **Descartado: cambiar `criterio_choque`** para que una línea al 0 % choque
  con cualquier partida: mezcla dos reglas, cambia la clave de los
  conflictos y obligaría a confirmar.
