<!-- specs/F-050-subfilas-partida/design.md -->
# F-050 · Diseño

D1-D10 **DECIDIDAS (A) por el humano el 2026-10-09** (§11) con sus dos
precisiones (mismo selector en el modal, R29; CD · CI · CP, R26). `critico`.

## 1. Límite de servicio

- **La propuesta vive en el transfer**: lee `hmores` y `obrparpar` y usa
  `partida_matcher` (copia cerrada de `partes`), que ya están allí, y el
  preflight la necesita igual (R9). En la api habría que copiar el matcher
  (prohibido) o tener dos verdades. Solo **lecturas**. El **mayor** de cada
  partida también lo calcula el transfer (§5.1): el front solo filtra.
- **La elegida vive en la api** (base `dedicacion`): es dato del cuadrante,
  se deshace con sus eventos y viaja al registro como hoy `paride`.
- **El front** pinta y filtra lo que le sirven (orden, mayor y ámbito los
  manda el transfer); no calcula propuesta ni decide qué se escribe.
- Nada es de otro microservicio; `partes` no se toca. Su selector (sv4,
  `buildPartidaPicker`: Todas/CD/CI sobre `PartidaNodo.categoria`) es la
  referencia, mejorada (CP, mayor por la raíz, tildes, teclado), sin copiarlo.

## 2. Encaje

Front → api `GET …/partidas` → transfer `POST /api/partidas/propuesta`;
front (columna o modal) → api `PUT …/partida` (asignación + evento); registro
como hoy, con `paride` = elegida y, sin elegida, `proponer_partida` (R9).

## 3. Ficheros a crear

- `services/dedicacion-transfer/application/services/propuesta_partida.py`
- `services/dedicacion-api/application/partidas_linea.py`
- Tests `test_f050_*.py` en `tests/` de cada servicio (§7).

## 4. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| transfer `infrastructure/sigrid/sigrid_write_client.py` | `historial_partidas` (§6) |
| transfer `application/pipelines/registro_pipeline.py` | `proponer_partida` en vez de `resolver_normal`; R20; `partida_origen`; `_cat` ordenado; `proponer` |
| transfer `domain/models/registro_models.py` | `AccionLinea.partida_origen` |
| transfer `interface_adapters/api/app.py` | `PropuestaIn` y `POST /api/partidas/propuesta` |
| transfer `config/settings.py` | `propuesta_meses_atras` (`PROPUESTA_MESES_ATRAS`, 24) |
| transfer `prueba_escritura_porcentajes.py` | fase de solo lectura `propuesta` (`--obra`, `--recurso`) |
| api `infrastructure/db/orm_models.py` | `AsignacionORM.partida_ide` (BigInteger), `partida_cod`, `partida_res` (Text), nulables sin default |
| api `domain/models.py`, `domain/errors.py` | `Linea.partida_ide/cod/res` y `partida_fija`; `TipoEvento.PARTIDA`; `LineaNoEncontrada`, `PropuestaNoDisponible` |
| api `infrastructure/db/repositories.py` | `reemplazar` y `_a_linea` con partida (`partida_fija` = `obra.registro_paride` no nulo); el puerto no cambia: `CambiarPartida` usa `reemplazar` |
| api `application/use_cases.py` | `CambiarPartida`; `_conservar_partidas`; `_snapshot` y `_validar_lineas` con partida |
| api `application/registro_sigrid.py` | `paride`/`partida_cod` desde la asignación (R19) |
| api `infrastructure/transfer/transfer_client.py` | `propuesta_partidas(payload)` |
| api `interface_adapters/api/{schemas,routes,deps,app}.py` | `PartidaIn`, `PartidasOut`, `LineaOut` (R18), dos rutas, contenedor, 404/502 de los errores nuevos |
| front `static/js/app.js`, `static/css/styles.css`, `templates/index.html` | subfilas, columna, selector, modal (§5.3); ayuda |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`, READMEs de api y transfer | §8 |

## 5. Clases y funciones

### 5.1 Transfer — `propuesta_partida.py` (application, **puro**)

- Dataclasses `LineaHistorial` (las columnas de §6) y `Propuesta(paride,
  cod, res, metodo, origen: str | None)`.
- `clave_orden_codigo(cod) -> tuple`: orden natural (grupos de dígitos como
  enteros, el resto en mayúsculas). La usan `_cat` y R8 (R10).
- `ventana(ano, mes, meses_atras) -> (desde_aaaamm, hasta_aaaamm)`.
- `previa_en_obra(historial, recurso, obra_ide, hojas)`: paso 1: recurso y
  obra, mes más reciente, suma de `can` por `paride`, máximo único, hoja
  activa; si no, None.
- `ultima_de_recurso(historial, recurso, obra_ide, hojas)`: paso 2: mes más
  reciente fuera de la obra, suma por (`normalize_code(cod)`,
  `normalize(res)`), máximo único, exactamente una hoja activa con ese
  código y esa descripción; si no, None.
- `proponer_partida(nodos, historial, recurso, obra_ide, categoria, nombre)
  -> Propuesta | None`: pasos 1 y 2 y `resolver_normal` (método `auto_*`).
- `mayor_de(nodos, nodo) -> "CD"|"CI"|"CP"|"OTRO"`: sube por `padide` hasta
  la raíz (sin padre en `nodos`; corta ciclos) y aplica
  `clasifica_categoria(raiz.cod, raiz.res)`; si da OTRO, `nodo.categoria`.
- `catalogo(nodos)`: hojas activas `{ide, cod, res, categoria, mayor}`, orden natural.
- `mayor_inicial(propuesta, nodos, categoria)`: mayor de la propuesta; sin
  ella, `"CI"` si `ambito_categoria(categoria) == {"CI"}`; si no, None.

**Por qué por la raíz** (Sigrid, 2026-10-09, solo lectura con el cliente
del transfer; 0694, 0696, 0678 y 0404 de la empresa 1): raíces `CD` «COSTES
DIRECTOS», `CI`/`CI0` «COSTES INDIRECTOS…» y `CP` «COSTES PROPORCIONALES»
(hojas `CP.1`-`CP.12`, 10-14 por obra); `tipdes` es 0 siempre (la baja, no
el tipo). `categoria` mira antes la descripción de la propia hoja y falla
bajo `CD`: `01.19.03.20` «…PROPORCI…» (0694) sale CP, `1.4.1.8` «…COSTES
INDIRECTOS…» (0404) sale CI. `mayor_de` no toca la copia cerrada; el
casamiento sigue con `categoria`. La copia de `partes` filtra con ese
`categoria`: **avisar al humano** (regla de las copias).

Pipeline (`preflight`): si hay líneas normales sin `paride` ni
`var_paride`, **una** `historial_partidas(resides, *ventana)`. La rama
`manual` exige hoja activa de `nodos_origen` o omite con
`MOTIVO_PARTIDA_NO_HOJA` (R20); la automática llama a `proponer_partida` y
pone `a.partida_origen`. Avisos, capacidad, cuenta analítica y modo pruebas
no cambian. `partidas_obra`/`_postventa` del preflight, como en F-049 pero
ordenados y sin `mayor`: el front deja de leerlos.

Endpoint: `PropuestaIn` (R8) → `RegistroPipeline.proponer(...)`, que
reutiliza `_obra_origen`, `_destino_postventa` y las mismas lecturas →
`{ok, partidas_obra, partidas_postventa` (de `catalogo`), `propuestas:
{clave: {paride, cod, res, metodo, origen} | null}, mayor_inicial: {clave:
"CD"|"CI"|"CP"|null}}`. `empresa_valida` → 422; obra de otra empresa → 422
con `MOTIVO_EMPRESA_OBRA`; excepción → 502. No escribe nada.

### 5.2 Api

- `Linea`: `partida_ide`, `partida_cod`, `partida_res` (None) y
  `partida_fija` (False), al final y con defecto. `clave()` no cambia.
- `_snapshot`: añade las tres claves **solo si** `partida_ide` no es None
  (los eventos sin partida y los tests de F-027/F-029 no cambian).
  `_validar_lineas` las lee si vienen: deshacer las restaura (R15).
- `_conservar_partidas(lineas, antes)`: pone a cada línea cuya clave estaba
  en `antes` su partida de antes (R14). En `GuardarAsignaciones`, **antes**
  de comparar snapshots.
- `CambiarPartida.ejecutar(uow, anio, mes, trabajador_ide, obra_ide,
  es_postventa, partida, usuario, *, filtro)`: periodo abierto,
  trabajador, línea por clave o `LineaNoEncontrada` (404); `partida_fija`
  → `ObraNoValida` (422); `reemplazar` + evento `PARTIDA` solo si cambia;
  devuelve la fila como `GuardarAsignaciones`.
- `PartidasDeLinea` (`partidas_linea.py`): VAR → fija sin transfer; si no,
  una línea `clave="linea"` (obra, empresa de las obras, `recurso_ide` =
  `ide` del trabajador, nombre, categoría) a `propuesta_partidas`; fallo →
  `PropuestaNoDisponible` (502, como `UniversoVarNoDisponible`). `ambito` =
  `mayor` de la elegida si su `ide` está en el catálogo servido; si no,
  `mayor_inicial["linea"]` (R17). Solo busca en la lista: no clasifica.
- Rutas: `GET .../trabajadores/{ide}/partidas?obra_ide=&es_postventa=` →
  `PartidasOut {partidas, partidas_postventa, ambito: "CD"|"CI"|"CP"|None,
  propuesta, elegida, fija}`; `PUT .../trabajadores/{ide}/partida` con
  `PartidaIn {obra_ide, es_postventa, partida: {ide > 0, cod, res} | null}`
  → `FilaOut`.
- `registro_sigrid._payloads`: VAR igual; `overrides.get(a.id)` como hoy (lo
  sigue aceptando aunque el front ya no lo mande); si no, `a.partida_ide` →
  `paride` y `partida_cod`.

### 5.3 Front (`app.js`)

- `COLUMNAS.partida` («Partida», «Filtrar partida…»);
  `ORDEN_COLUMNAS_DEFECTO` con `partida` tras `asignaciones`;
  `cargarPrefsTabla` la mete tras `asignaciones` si falta.
- `construirFila(t)` devuelve un `DocumentFragment` con `max(1, n)` `tr`:
  `.fila` y `.fila.subfila`, todos con `data-ide` y `data-linea`. Los
  escuchadores de F-029 se conservan **literales** sobre cada `tr` (los
  tests `test_f029_r1-r4` no cambian). Columnas del trabajador con
  `rowSpan`; `asignaciones` y `partida`, una celda por línea.
- `construirCelda(t, clave, idx)`: `asignaciones` pinta el chip de la línea
  `idx` (mismas clases y avisos de F-024/F-034); `partida` pinta R24 y, si
  ABIERTO y no fija, su clic (`stopPropagation`) llama a
  `abrirSelectorPartida(t.ide, linea.obra_ide, linea.es_postventa, td)`.
  `refrescarCeldasFila(t)` rehace todas las `tr` del trabajador.
- `trabajadoresVisibles`: rama de filtro `partida` y texto de partida en el
  pajar, **en línea** (el arnés node de F-041 no cambia) y sin tocar el
  literal `textoObra(...)` del pajar.
- Puras (node): `textoPartida(p)`, `textoPartidaAccion(a)` (`partida_cod`,
  «partida N» sin código, «sin partida» con `paride` 0), `filtrarPartidas(
  partidas, texto, mayor)` (`normalizar`, todas las palabras en `cod + " "
  + res`; `mayor` null = Todas), `listaSelector(resp, texto, mayor)`
  (propuesta primera si pasa, sin repetir) y `rotuloOrigen(metodo, origen)`.
- `abrirSelectorPartida(trabajadorIde, obraIde, esPostventa, ancla,
  despues)`: `await guardarAhora()` si es el trabajador en edición; `GET
  …/partidas` (caché por trabajador, obra y modo; se vacía al cambiar mes o
  empresa, y su clave tras cada PUT); panel `.panel-partida` en `<body>`
  (F-042, `z-index` sobre `#modal-registro`): campo, botones Todas · CD ·
  CI · CP (`mousedown` + `preventDefault`, uno `.on`, empieza en
  `resp.ambito`), lista y «automática»; sus teclas no llegan a `teclas`;
  Enter o clic → `PUT …/partida` → `aplicarFila` → `despues?.()`.
- Modal (R29): en `escribir` no VAR, `<button type="button"
  class="sel-partida" data-reg="${a.registro_id}">` con
  `textoPartidaAccion(a)`, `rotuloOrigen` y aviso; VAR igual (F-039 r22).
  `registro.lineas[registro_id] = {trabajador: a.recurso_ide, obra_ide del
  grupo, es_postventa}`; `click` → `abrirSelectorPartida(…, boton,
  repreflightPartida)`. Fuera `registro.overrides` y `opcionesPartida`:
  `pedirPreflight` y `registroEjecutar` mandan `trabajador_ide` (y `pisar_claves`).

## 6. SQL

**PostgreSQL** (`dedicacion`, `public`): solo el ORM; `esquema.py` deriva
`ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS partida_ide BIGINT` (y
`partida_cod TEXT`, `partida_res TEXT`). Sin `NN_*.sql`, sin Alembic, sin
datos que mover (`test_f003` no cambia: no son columnas `sigrid_*`).

**Sigrid**, lectura parametrizada en `sigrid_write_client.historial_partidas
(resides, desde, hasta)`, `IN` en lotes de 500:

```sql
SELECT h.reside, m.obride, co.cod AS obra_cod, c.cod AS parte_cod,
       m.ano, m.mes, h.can, h.paride, p.cod AS par_cod, p.res AS par_res
FROM hmores h JOIN hmo m ON m.ide = h.hmoide
JOIN con c ON c.ide = m.ide JOIN con co ON co.ide = m.obride
JOIN auxhor a ON a.ide = h.horide JOIN obrparpar p ON p.ide = h.paride
WHERE h.reside IN (?…) AND c.tip = ? AND a.cod LIKE 'M%'
  AND p.obride = m.obride AND (m.ano * 100 + m.mes) BETWEEN ? AND ?
```

`truncated` → excepción (R7). El mayor sale del `obrparpar` que ya se lee.

## 7. Tests y dobles

- Transfer: `propuesta_partida` en memoria (R1-R6, R10, empates, hoja de
  baja, filas barajadas; `mayor_de` con los dos casos reales de §5.1, raíz
  `CI0`, OTRO y ciclo; `mayor_inicial`); pipeline con el `ClienteFalso` de
  `conftest.py` + `historial_partidas` (R9, R20, R21); endpoint con
  `TestClient`.
- Api: `_Uow` de F-024 ampliado **dentro** de `test_f050_*` (R12-R16, R18,
  R19); rutas con la fixture `api` de F-024 y transfer falso (R13, R17).
- Front: estáticos y lógica en node (`filtrarPartidas` con los cuatro
  botones, `listaSelector`, `textoPartidaAccion`, `rotuloOrigen`, columnas
  y preferencias), como F-041 y F-049.
- **Front, lista cerrada** (requirements §6): test a test en `tasks.md` T12
  (seis `c_*` borrados; su intención pasa a `test_f050_*`, `textoPartidaAccion`).

## 8. Documentación (R30)

`ARCHITECTURE.md`: punto 19 `#regla-partida` (R1-R4, R20, mayor por la
raíz) con su ancla, `asignacion` con partida y endpoints. `INTEGRACION.md`:
los tres endpoints y el 502 de R17. READMEs de api y transfer: una fila/ruta.

## 9. Ficheros que NO se tocan

Las copias cerradas de `partes` (`partida_matcher`, `partida_catalog`,
`text_match`, `cuenta_analitica`, `estado_parte`), `reglas_porcentajes`,
`universo_*`, `excel/*` (D8), `sync_pipeline`, `deshacer`, `.env`, `infra/`.

## 10. Riesgos

- **Rendimiento del historial**: sin índice documentado en
  `hmores.reside`, puede barrer la tabla. M1 mide; si pasa de 30 s, PARA y
  se propone acotar (por obra en el paso 1).
- **Catálogo por clic** (`BD`: 26.812 partidas): caché en el front; M2.
- **Cambia lo que se escribe** en las automáticas: mutación completa y M3.
  R20 retiene overrides que hoy se escribían (D9). `rowSpan`: M2.
- **Selector sobre el modal** (foco, overlay, Esc cierra solo el selector)
  y **mayor preelegido** que esconde lo tecleado («Todas» a un clic): M2.

## 11. Decisiones DECIDIDAS por el humano el 2026-10-09 (todas A)

| D | Decidida (A) | Descartadas |
|---|---|---|
| D1 · Parte anterior | R1-R2: esa obra, periodo **incluido**, 24 meses, más `can` (0694 CI.1.5 de Administración ⇒ pisado, no sobrecarga) | B solo el mes anterior; C sin el propio periodo |
| D2 · Último parte | Otra obra, trasladada con código **y** descripción iguales | B solo código; C solo descripción; D sin paso entre obras |
| D3 · Cuándo y qué se guarda | Al abrir el selector y en el preflight; se guarda **solo la elegida** | B botón que guarda la propuesta; C al añadir la obra |
| D4 · Dónde | Columnas de `asignacion` (§6, R12-R16); F7 no copia | B tabla aparte |
| D5 · Postventa y VAR | R11: VAR fija; postventa con selector de `partidas_postventa` | B postventa fija |
| D6 · Subfilas | `tr` con `rowSpan`, cursor y selección por trabajador, sin atajo nuevo ni velar | B líneas apiladas; A2 tecla P |
| D7 · Modal | Se **guarda** (R13) y repite el preflight, con **el mismo selector** que la columna (precisión del humano), sin `overrides` | B solo para ese registro |
| D8 · Excel | Sin cambios | B columna en tres hojas; C solo Detalle |
| D9 · Elegida que ya no vale | R20: se omite y se elige otra | B automática con aviso; C escribirla |
| D10 · F-054 y F-021 | Fuera; `partida_*` y `data-*` de subfila quedan listos | B velar ya aquí |

**Precisión 2 del humano (botones):** Todas · CD · CI · CP por **mayor**
(§5.1), uno activo; preelegido el de R17. `partes` tenía Todas/CD/CI.
