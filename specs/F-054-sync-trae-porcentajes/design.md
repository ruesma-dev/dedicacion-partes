<!-- specs/F-054-sync-trae-porcentajes/design.md -->
# F-054 · Diseño

Requisitos en `requirements.md`; D1-D11 **abiertas** (requirements §9),
escrito con la recomendada (A). Si el humano elige otra, este diseño se
revisa antes de implementar.

## 1. Servicios, límite y contrato

**Límite de servicio: el transfer lee Sigrid y traduce; la api escribe en
`dedicacion`; el front solo lanza y pinta.**

- **`dedicacion-transfer`, lectura nueva y traducción.** Ya tiene lo que
  hace falta y no puede copiarse: la lectura de líneas `M*` con el parte y su
  estado (`sigrid_write_client.py`, `estado_parte.py`), el casado de
  postventa (`universo_postventa.casar_postventa`) y el universo VAR
  (`universo_var.partida_var_de`), con los ajustes `POSTVENTA_OBRA_COD`,
  `VAR_OBRA_COD`, `OBRA_PRUEBAS_COD` y `TIP_PARTE_TRABAJO`, que solo viven en
  su `.env`. Si la api leyera, tendría que duplicar el casado (prohibido en
  `CLAUDE.md`: la lógica no se copia entre servicios). El endpoint es de
  **solo lectura**, como `/api/postventa/universo`: no amplía la escritura.
- **`dedicacion-api`, dueño del dato.** El transfer no tiene base. La api
  agrupa, compara con el cuadrante y escribe asignaciones, traza y eventos.
- **`dedicacion-front`, sin lógica.** Encadena la llamada tras el sync y
  pinta el resultado; «Usar lo de Sigrid» repite la petición con un `ide`.
- **No es otro microservicio.** Es una lectura más de la misma pasarela y
  datos que ya lee el transfer; no hay responsabilidad nueva.

**Contrato api → transfer:** `POST /api/porcentajes/existentes`, `{empresa,
ano, mes, obras: [{ide, codigo, nombre}]}` (las obras de la empresa de las
obras con `admite_postventa`, para el casado inverso) → `{ok, empresa, ano,
mes, lineas_leidas, excluidas_pruebas, obra_postventa, motivo_postventa,
obra_var, motivo_var, lineas: [...]}`; cada línea con los campos de R6 más
`destino` (`normal`, `postventa`, `var` o nulo), `obra_origen_ide`,
`var_paride` y `motivo`. 422 con empresa, año o mes no válidos; 502 si una
lectura falla o viene `truncated`.

**Contrato front → api:** `POST /api/v1/periodos/{anio}/{mes}/traer-sigrid?
empresa=`, cuerpo `{sustituir: [ide]}` (vacío por defecto) → R29, con
`propuestas_en_curso`. 404 / 409 (R2), 422 (`sustituir` con algo que no es
entero), 502 (R3).

**Orden de despliegue: transfer → api → front.** Api nueva con transfer
viejo: el endpoint no existe (404 del transfer) ⇒ 502 con motivo, y el sync
de maestros sigue bien. Front viejo con api nueva: no llama a nada nuevo.

## 2. Ficheros a crear

| Fichero | Qué |
|---|---|
| transfer `application/services/porcentajes_existentes.py` | §4.2 |
| api `domain/traer_sigrid.py` | funciones puras (§5.1) |
| api `application/traer_sigrid.py` | caso de uso `TraerDeSigrid` (§5.2) |
| transfer `tests/test_f054_lectura_mensuales.py` | R4-R7: SQL, parámetros, `truncated` |
| transfer `tests/test_f054_traduccion.py` | R8-R12 con `ClienteFalso` |
| transfer `tests/test_f054_endpoint.py` | contrato, 422/502, nunca escribe (R7), R31 |
| api `tests/test_f054_agrupar.py` | R13-R18, R20-R21 (dominio puro) |
| api `tests/test_f054_traer.py` | R2, R19-R28 con la UoW en memoria |
| api `tests/test_f054_rutas.py` | ruta, 404/409/422/502, R29 |
| front `tests/test_f054_traer_front.py` | R1, R30 en node, como `test_f061_recarga.py` |

## 3. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `infrastructure/sigrid/sigrid_write_client.py` | `lineas_mensuales_del_periodo(empresa, ano, mes)` (§4.1) |
| transfer `domain/models/registro_models.py` | `LineaMensualSigrid` (dataclass) |
| transfer `interface_adapters/api/app.py` | `ExistentesIn` y el endpoint (§1) |
| api `domain/models.py` | `TipoEvento.SIGRID`; `ResultadoTraer` y sus filas |
| api `domain/ports.py` | `PorcentajesSigridGateway`; `AsignacionRepository.marcar_traida` |
| api `domain/errors.py` | `PorcentajesSigridNoDisponible` (⇒ 502) |
| api `infrastructure/transfer/transfer_client.py` | `porcentajes_existentes(...)` |
| api `infrastructure/db/repositories.py` | `marcar_traida` (§5.3) |
| api `infrastructure/db/orm_models.py` | solo el comentario de la traza: también la escribe `traer_sigrid.py` |
| api `interface_adapters/api/{routes,schemas,deps}.py` | ruta, `TraerSigridIn/Out`, cableado |
| front `static/js/app.js` | §6 |
| front `templates/index.html` | la ventana del resultado, si no vale la existente |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | R32 (§7) |
| transfer `tests/test_f002_fuente_unica.py` | `ANCLAS` + `regla-traer-sigrid` (lista cerrada) |
| `azure-apps/dedicacion.md` (otro repo) | al desplegar: copia de `INTEGRACION.md` con su cabecera (T14) |

## 4. Transfer

### 4.1 La lectura (base `ruesma`, una por petición)

```sql
SELECT h.ide AS ide, h.reside AS reside, m.obride AS obride,
       co.cod AS obra_cod, m.ide AS parte_ide, c.cod AS parte_cod,
       c.est AS parte_est, a.cod AS hora, h.can AS can, h.fec AS fec,
       h.paride AS paride, p.cod AS par_cod, p.res AS par_res,
       h.synckey AS synckey
FROM hmores h JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide
JOIN con co ON co.ide = m.obride JOIN auxhor a ON a.ide = h.horide
LEFT JOIN obrparpar p ON p.ide = h.paride
WHERE c.tip = ? AND ISNULL(m.reside, 0) = 0 AND m.ano = ? AND m.mes = ?
  AND co.emp = ? AND a.cod LIKE 'M%' AND ISNULL(h.can, 0) <> 0
ORDER BY h.ide
```

- Parametrizada; `_lectura("lineas_mensuales_del_periodo", …)` (log y
  medición de F-055). `truncated` ⇒ excepción (`_read`), como todas.
- Volumen: las mensuales de un mes de la empresa de las obras (cientos de
  filas), muy por debajo de `SIGRID_MAX_ROWS`; no hace falta paginar.
- `en_registro = (parte_est == EST_PARTE_ACTIVO)`: el único predicado de
  «cerrado» es el de `estado_parte.py`, que **no se toca**.

### 4.2 `porcentajes_existentes.py`

```python
def obras_por_partida(catalogo: CatalogoPostventa, obras: list[ObraEntrada]
                      ) -> dict[int, list[ObraEntrada]]
    # casado inverso: casar_postventa de cada obra; {partida_ide: [obras]}
def traducir(linea: LineaMensualSigrid, *, cod_pruebas, cod_postventa,
             cod_var, inverso, catalogo_pv, catalogo_var, desde
             ) -> LineaTraducida | None     # None = obra de pruebas (R5)
class PorcentajesExistentes:
    def __init__(self, *, cliente, settings) -> None
    def calcular(self, empresa: int, ano: int, mes: int,
                 obras: list[ObraEntrada]) -> dict
```

- Los códigos se comparan normalizados (`strip`, mayúsculas); la lectura ya
  es de una empresa, así que el código basta (`#regla-empresa`).
- `calcular`: lee las líneas; si alguna es de la obra de postventa, carga
  `cargar_catalogo_postventa` (dos lecturas) y el inverso; si alguna es de la
  VAR, `cargar_catalogo_var` (dos lecturas). Máximo cinco lecturas, en serie.
- Motivos como constantes del módulo; ninguno nombra personas.

## 5. Api

### 5.1 Dominio puro (`domain/traer_sigrid.py`)

```python
@dataclass(frozen=True) class LineaExistente      # una línea del transfer
@dataclass(frozen=True) class EntradaSigrid       # obra_ide, es_postventa,
    # porcentaje: Decimal, partida (ide, cod, res) | None, hmores_ide,
    # parte_cod, n_lineas
def entradas_por_trabajador(lineas: list[LineaExistente],
                            obras: dict[int, Obra], *, empresa_obras: int
    ) -> tuple[dict[int, list[EntradaSigrid]], list[NoTraida]]  # R13-R17
def coinciden(lineas: list[Linea], entradas: list[EntradaSigrid]) -> bool
    # R20: mismas claves y % con EPSILON de domain/estados.py
def a_lineas(entradas: list[EntradaSigrid], obras: dict[int, Obra]
             ) -> list[Linea]                     # R17
```

`Linea.ofrecible` (única definición) decide si una entrada se ofrece; la
VAR es una obra con `registro_paride`.

### 5.2 Caso de uso `TraerDeSigrid` (`application/traer_sigrid.py`)

1. `_periodo_abierto_o_error` (R2) **antes** de llamar al transfer.
2. Obras del periodo (`uow.obras.listar_para_periodo`); al transfer, las de
   la empresa de las obras con `admite_postventa`.
3. Transfer (`PorcentajesSigridNoDisponible` ⇒ 502, R3).
4. `entradas_por_trabajador`; filas visibles y vigentes con
   `_filas_de_empresa` (R14, D11); un recurso que no esté en el maestro
   solo suma en `fuera_maestro`.
5. Por trabajador: sin líneas ⇒ traer (R19); con líneas ⇒ `coinciden` o
   `diferencias` (R20, R21), salvo si está en `sustituir` (R22).
6. Traer o sustituir: `reemplazar` con `a_lineas`, `marcar_traida` de cada
   entrada (R24) y evento `SIGRID` (R27).
7. Se relee el periodo: si se cerró entre medias, 409 sin escribir. Un solo
   `commit` (R23). La ruta encola las propuestas de los escritos (R28).

### 5.3 Repositorio

`marcar_traida(periodo_id, trabajador_ide, clave, *, hmores_ide, parte_cod)`:
`UPDATE` del ORM a esa asignación con `sigrid_hmores_ide`,
`sigrid_parte_cod`, `sigrid_estado = "registrado"` y `sigrid_motivo =
"traída de Sigrid"`; `sigrid_registrado_at/_by` quedan nulos (no la registró
nadie desde la app). Sin ORM ni DDL nuevos: las columnas ya existen.

## 6. Front (`app.js`)

- `sincronizar()` solo cambia en devolver `true` / `false`; el clic de
  `#btn-sync` pasa a `sincronizarYTraer()`, que llama a `traerDeSigrid()` si
  devolvió `true`. Así `test_f061_recarga.py` no se toca.
- `traerDeSigrid(sustituir = [])`: `POST .../traer-sigrid`, `toast` con el
  resumen, `cargarPeriodo` y, si hay `diferencias` o `no_traidas`, la
  ventana con las dos listas; «Usar lo de Sigrid» ⇒ `traerDeSigrid([ide])`.
  Un error ⇒ `toast(motivo, true)`.

## 7. Documentación

- `ARCHITECTURE.md`: punto 22, `#regla-traer-sigrid` (R4-R28 en prosa y la
  procedencia de D1-D11); la lista de anclas del encabezado de la sección;
  la tabla de acceso a datos (el transfer lee las mensuales del periodo); y
  en la descripción del transfer, el endpoint.
- `INTEGRACION.md`: §1 (la lectura nueva del transfer), §5 (las dos rutas)
  y §7 (despliegue transfer → api → front; con el transfer viejo, 502).
- `azure-apps/dedicacion.md`: al desplegar (líder, como F-051 T16), se
  refresca desde `INTEGRACION.md` con su cabecera; commit en `azure-apps`.

## 8. Tests (sin red ni BBDD)

- Transfer: `ClienteFalso` con `_read` doble, como
  `test_pipeline_offline.py`; endpoint con `TestClient`. Se comprueba que
  ninguna prueba llama a `escribir` (R7) y que un preflight con el doble no
  pide `lineas_mensuales_del_periodo` (R31).
- Api: dominio puro; caso de uso con la UoW en memoria de
  `test_f024_cuadrante_empresa.py`, ampliada en el fichero nuevo con
  `marcar_traida` (sin editar la original); ruta con la fixture `api` de
  `test_f024_rutas_empresa.py` y un transfer doble.
- R26: con el payload de `registro_sigrid._payloads`, la traída lleva
  `hmores_ide`; tras `GuardarAsignaciones`, no.
- Front: node con dobles de `api`, `toast`, `$` y `cargarPeriodo`.
- Nombres `test_f054_rN_…`. Lo único contra Sigrid real es T13 (MANUAL).

## 9. Ficheros que NO se tocan

- `registro_pipeline.py`, `registro_lote.py`, `lecturas_lote.py`,
  `reglas_porcentajes.py`, `reglas_incidencias.py`: el registro, el
  preflight (F-055) y las incidencias no cambian.
- Copias de `partes` (`estado_parte.py`, `cuenta_analitica.py`,
  `partida_catalog.py`, `partida_matcher.py`, `text_match.py`), y
  `universo_postventa.py` y `universo_var.py`: se **llaman**, no se editan.
- api: `sync_pipeline.py` (el sync de maestros sigue igual),
  `registro_sigrid.py`, `propuestas_mes.py`, `reemplazar`, el ORM salvo el
  comentario, `esquema.py`.
- `partes` (otro repositorio) y `test_f061_recarga.py` (§6).

## 10. Riesgos y alternativas descartadas

- **Traza perdida al editar** (R26): `reemplazar` recrea las asignaciones
  sin traza (F-051 §6.3); tras un cambio, la traída pasa de «ya
  registrada» a pisado a confirmar. No duplica. Conservar la traza al
  guardar queda fuera: rompería el pisado de un % cambiado.
- **Línea nuestra huérfana.** Una `synckey porcentajes:{id}` de una
  asignación ya recreada es «nuestra de otra asignación» (F-051 R15): la
  traída no es «ya registrada» y pide un pisado. Pasa igual hoy.
- **Otra hora `M*`.** Si Administración usó un código `M*` distinto del que
  el transfer escribe para el recurso (F-011), tras editar la fila no habrá
  choque y saldrá sobrecarga, que se avisa y se confirma
  (`#regla-capacidad`).
- **Partida de baja.** La elegida traída que ya no es hoja activa se omite
  al registrar con su motivo (`#regla-partida`); solo si se edita la fila.
- **Tiempo.** Hasta cinco lecturas de 4-6 s (medida de F-055), dentro de
  `TRANSFER_TIMEOUT_S`; el sync de maestros no las espera.
- **Concurrencia.** Leer el cuadrante y escribir van en la misma
  transacción, como Copiar mes.
- **Descartado:** leer desde la api con una consulta en `config.yaml`
  (duplicaría el casado); meterlo en `POST /sync` (D1 C); columna nueva de
  origen en `asignacion` (el evento `SIGRID` ya lo dice).
- **F-062** puede reutilizar la lectura de §4.1 (otro código de hora); no se
  depende de su spec. **F-044**: los vinculados (`OTEL`, `KM`…) son otros
  recursos, fuera del maestro: solo cuentan en `fuera_maestro` (R14).
