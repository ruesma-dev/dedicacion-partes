<!-- specs/F-039-obras-var-y-seis-digitos/design.md -->
# F-039 · Obras VAR por partidas y fuera las de 6 dígitos — diseño

Requisitos: `requirements.md` (R1-R24; D1-D6 decididas por el humano el 2026-10-06). Normativa:
`docs/ARCHITECTURE.md` (`#regla-p5`, `#regla-empresa`, `#regla-recurso`, `#regla-analitica`,
`#regla-completar`), `docs/CONVENTIONS.md`. Patrón: F-025 (universo de postventa).

## 1. Encaje y límite de servicio

```
sync (api) ── lee obras ── descarta las de N+ dígitos (R10) ─┬─ POST /api/postventa/universo (como hoy)
                                                              └─ POST /api/var/universo {empresa} ──▶ transfer
   ◀── {obra_var, desde, motivo, partidas: [{ide, cod, res}]}       lee obra VAR + presupuesto
api: VAR no activa (D1) + una fila `obra` por partida (VAR-29, ide = −417055) ──▶ front pinta
registro (api) ── líneas de VAR-29 en la petición de la obra VAR, con var_paride = 417055
preflight (transfer) ── var_paride ∈ universo VAR (mismas funciones) ⇒ paride fijo, metodo "var"
```

- **Transfer**, único que conoce `VAR_OBRA_COD`, el umbral y el presupuesto, y el que fija la
  partida al escribir: el universo y la validación del preflight llaman a las **mismas**
  funciones de `universo_var.py` (como `universo_postventa.py` en F-025). La api no lee
  presupuestos ni conoce «VAR» ni «29».
- **API**: el filtro de código es de maestros (como `estados_excluidos`): vive en el sync, con
  el número en `config.yaml`. Convierte el universo en filas de `obra` y agrupa el registro.
- **Front**: el catálogo ya pinta cualquier `obra` `activa`; solo cambia el modal de registro.
- Sin responsabilidad nueva fuera de los tres servicios. **Ninguna SQL nueva contra Sigrid**:
  `obra_por_codigo` y `capitulos_de_obra` ya existen. La VAR de la empresa 28 no se lee nunca.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/application/services/universo_var.py` | Catálogo VAR, criterio de partida y universo (§4.1) |
| `services/dedicacion-transfer/tests/test_f039_universo_var.py` | R1-R4, R2 parametrizado, endpoint (`TestClient`) |
| `services/dedicacion-transfer/tests/test_f039_preflight_var.py` | R5-R9 y cruce universo ⇔ preflight |
| `services/dedicacion-api/domain/obras.py` | Reglas puras de código de obra (§4.2) |
| `services/dedicacion-api/tests/test_f039_sync_var.py` | R10-R18 |
| `services/dedicacion-api/tests/test_f039_registro_var.py` | R19-R21 (registro, ofrecible, Completar, Excel) |
| `services/dedicacion-front/tests/test_f039_partida_fija.py` | R22, estático sobre `app.js` |
| `scripts/verif_f039_var.ps1` | Verificación MANUAL M1/M2, solo lecturas de Sigrid, sin `ejecutar` (§8) |

## 3. Ficheros a modificar

**Transfer** (`services/dedicacion-transfer/`)
- `config/settings.py`: `var_obra_cod: str = "VAR"` (`VAR_OBRA_COD`; vacío = sin VAR) y
  `var_partida_desde: int = 29` (`VAR_PARTIDA_DESDE`); `.env.example`, las dos líneas.
- `domain/models/registro_models.py`: `LineaEntrada.var_paride: Optional[int] = None`.
- `interface_adapters/api/app.py`: `LineaIn.var_paride`; `UniversoVarIn(empresa: int | None)`
  y `POST /api/var/universo` (422 con `empresa_valida`, 502 ante excepción), como el de F-025.
- `application/pipelines/registro_pipeline.py`: rama VAR en el bucle de partidas (§4.1),
  **antes** del override manual; docstring del paso 4 remite a `#regla-var`.
- `README.md`: el endpoint, en una línea que remite a `#regla-var`.

**API** (`services/dedicacion-api/`)
- `domain/models.py`: `PartidaVar(ide, cod, res)` y `ResultadoUniversoVar(obra_ide, obra_cod,
  empresa, partidas: tuple[PartidaVar, ...], motivo)`, frozen.
- `domain/ports.py`: `UniversoVarGateway.universo_var(empresa) -> ResultadoUniversoVar` y
  `UniversosGateway(UniversoPostventaGateway, UniversoVarGateway, Protocol)`, tipo del kwarg
  `universo` del step y del preview (el nombre no cambia); `domain/errors.py`:
  `UniversoVarNoDisponible(ErrorDominio)`, en `_HTTP_POR_ERROR` de `app.py` como 502 (R16).
- `infrastructure/transfer/transfer_client.py`: `universo_var(empresa)` (§5).
- `application/filtros_maestros.py`: `descartar_por_codigo`, `entradas_var` y el parámetro
  `no_normales` de `depurar_obras` (§4.2).
- `application/sync_pipeline.py`: `preparar_obras` (§4.2), que usan `FetchObrasStep` y
  `PreviewSync`; los dos ganan `digitos_excluidos: int = 0`.
- `application/use_cases.py`: `PreviewSync` vía `preparar_obras` y las claves de R17.
- `infrastructure/db/orm_models.py`: `ObraORM.registro_obra_ide` (`BigInteger`),
  `registro_obra_cod` (`Text`), `registro_paride` (`BigInteger`), nulables, sin default (R18).
- `infrastructure/db/repositories.py`: `PgObraRepository.sincronizar` guarda y compara las
  tres (`fila.get(...)`, `None` en las normales); nada más cambia.
- `application/registro_sigrid.py`: `_payloads` agrupa por `o.registro_obra_ide or o.ide`;
  la entrada manda `var_paride` y nunca `paride` (R20); la `obra` del grupo es la de registro
  (`ide`, `codigo` = `registro_obra_cod`, `nombre` `None`).
- `interface_adapters/api/deps.py`: `digitos_excluidos` de `cfg_obr` al step y al preview; el
  mismo `TransferClient` hace de `universo` (sigue habiendo **uno**).
- `config/config.yaml`: `sync.obras.digitos_seguidos_excluidos: 6` con su comentario (D4).

**Front** — `static/js/app.js`, `pintarModalPreflight`: si `a.accion === "escribir" &&
a.partida_metodo === "var"`, celda `<span class="partida-fija">` con `partida_cod` en vez del
`<select class="sel-partida">` (R22). Nada más.

**Docs** — `ARCHITECTURE.md`: reglas 17 `#regla-var` y 18 `#regla-seis-digitos` (§6), la
lista de anclas de la cabecera de «Semántica» y la tabla `obra`. `INTEGRACION.md`: §3, §5 y
§7 (R24), y fecha del documento. `azure-apps/dedicacion.md`: copia literal (commit humano).

## 4. Clases y funciones

### 4.1 Transfer (`application/services/universo_var.py`, capa application)

```python
@dataclass(frozen=True)
class CatalogoVar:
    obra: ObraEntrada | None              # obra VAR resuelta en la empresa
    partidas: dict[int, PartidaNodo]      # SOLO las partidas VAR (R2), por ide
    motivo: str | None                    # por qué no hay universo (R3)

def numero_inicial(cod: str | None) -> int | None        # dígitos iniciales, tras strip
def es_partida_var(nodo: PartidaNodo, desde: int) -> bool  # hoja + activa + número ≥ desde
def cargar_catalogo_var(cliente, settings, empresa: int) -> CatalogoVar
class UniversoVar:
    def __init__(self, *, cliente, settings) -> None
    def calcular(self, empresa: int) -> dict                 # contrato §5
```

- `cargar_catalogo_var`: `var_obra_cod` vacío → motivo sin leer; `obra_por_codigo(cod,
  empresa)` (`ObraAmbigua` y `None` → motivo, mismos textos que postventa con «VAR»);
  `construir_catalogo(capitulos_de_obra(ide))` filtrado con `es_partida_var`. Cita los ajustes,
  nunca el literal (test como `test_f025_r25_…`).
- **Pipeline**, en el bucle de partidas, para la acción `escribir` cuya línea trae
  `var_paride`: carga el catálogo **una** vez por petición (lazy, con la `empresa` del paso 0);
  si `catalogo.obra` es `None`, si su `ide` no es el de `origen`, si `var_paride` no está en
  `catalogo.partidas` o si `a.destino == "postventa"` → `omitir` con `MOTIVO_VAR_*` (R6);
  si no, `paride`, `partida_cod` del nodo y `partida_metodo = "var"`, y `continue` (R5, R7).
  Lo demás no cambia: cuenta (paso 4 bis), parte, synckey y avisos ya funcionan con un `paride`
  fijo; en pruebas, `obra_de(a)` es la de pruebas (R8). `partidas_obra` no cambia.

### 4.2 API

- `domain/obras.py` (domain, puro): `tiene_digitos_seguidos(cod: str | None, n: int) -> bool`
  (`n <= 0` → `False`), `codigo_entrada(obra_cod: str, partida_cod: str) -> str` (`VAR-29`,
  D2) e `ide_entrada(paride: int) -> int` (= `-paride`, D6). Única definición de cada una.
- `descartar_por_codigo(filas, n) -> tuple[list, list]` (quedan, descartadas), con
  `tiene_digitos_seguidos` sobre `cod` tal cual llega (`"160310 "` también cae).
- `depurar_obras(..., universo, no_normales: frozenset[int] = frozenset())`: la obra de
  `no_normales` sale con `activa = False` (D1); el resto, igual.
- `entradas_var(uvar: ResultadoUniversoVar) -> list[dict]`: una fila por partida con las claves
  que guarda `sincronizar` (R13); `estado_sigrid` `None`; vacía si `uvar.obra_ide is None`.
- `preparar_obras(brutas, universo, empresa_obras, estados, filtro, digitos) ->
  ObrasPreparadas(depurado, universo_pv, universo_var, descartadas)` (application): descartar
  → `pedir_universo` con las que quedan → `universo.universo_var(empresa_obras)` →
  `depurar_obras(..., no_normales={obra VAR})` → `depurado.filas += entradas_var(...)`.
  **Una** función para el step y el preview: lo que enseña el preview es lo que se guarda.
- `TransferClient.universo_var`: POST; si `ok` no es `true` o falta `partidas` →
  `UniversoVarNoDisponible` con el error (R16).

## 5. Contrato `POST /api/var/universo` (transfer, interno, solo para la api)

Entrada `{"empresa": 1}`. Salida 200:

```json
{"ok": true, "empresa": 1, "desde": 29, "motivo": null,
 "obra_var": {"ide": 683806, "codigo": "VAR", "nombre": "OBRAS VARIAS", "empresa": 1},
 "partidas": [{"ide": 417055, "cod": "29", "res": "ACOND. NAVE MODUL-A, ARROYOMOLINOS"}]}
```

Errores 422 y 502 con `{"ok": false, "error": …}`. Nunca escribe; el modo pruebas no lo afecta.
Contrato de línea api → transfer: gana `var_paride` opcional; nada más cambia.

## 6. SQL, esquema y documentación normativa

- **Sigrid**: ninguna consulta nueva ni cambiada.
- **PostgreSQL**: tres `ADD COLUMN IF NOT EXISTS` sobre `obra`, derivados por
  `esquema.alters_faltantes` y aplicados al arrancar (como F-025). `obra.ide` negativo para
  las entradas: `con.ide` y `obrparpar.ide` son positivos, no pueden chocar con una obra
  real; el FK de `asignacion.obra_ide` las acepta sin cambio.
- **`#regla-var`** (texto nuevo de ARCHITECTURE, la única fuente): qué es partida VAR (R2), el
  universo en el transfer, la entrada en la api (R13-R15), que VAR no se ofrece como normal
  (D1), cómo se registra (R5-R8, R20) y la procedencia (humano 2026-10-06, D1-D6).
  **`#regla-seis-digitos`**: R10-R11, R19 y D4-D5. `test_f002_fuente_unica.ANCLAS` gana las dos.

## 7. Tests (sin red ni BBDD)

- Transfer: `ClienteVar` (subclase de `ClienteFalso` **en el fichero nuevo**, con la obra VAR
  683806/centro 683807 y un presupuesto `CD`, `05`, `28`, `29`, `29.1`, `30`, `100`, `029`,
  `29A`, capítulo `31` con hija, `32` de baja, `CI.1.3`) y ajustes `var_*` puestos en la
  instancia de `SettingsFalso`; obra VAR ausente y ambigua; `VAR_OBRA_COD` vacío sin lecturas;
  422/502 por `TestClient`; una carga por petición. **Cruce parametrizado**: «en el universo»
  ⇔ «el preflight la escribe con `partida_metodo = "var"`», en real y en pruebas.
- API: `UniversoFalso.universo_var` configurable; sync y preview con `150414`, `0902051`,
  `090205A`, `150301-1` (caen), `12345` (se queda) y la VAR; 502 sin `commit`; ALTER derivado; `_payloads` con una
  entrada y una normal de la misma obra (una petición) y con override ignorado; `ofrecible`
  tras R11/R15; Completar y export con `VAR-29` (dobles existentes de F-029 y del exporter).
- Front estático: rama `partida_metodo === "var"` y ningún literal `VAR`/`"29"` en `app.js`.
- Nombres `test_f039_rN_…`. Rigor crítico: RED antes de cada tarea, cobertura de líneas
  cambiadas y mutación completa con cero supervivientes (`harness/rigor.json`).

### 7.1 Tests existentes que cambian (lista CERRADA)

Comprobada el 2026-10-06 aplicando la forma mínima de este diseño en un worktree desechable y
ejecutando las cuatro suites (antes: transfer 533, api 586, front 53, raíz 418 verdes).
Con el prototipo: **transfer, front y raíz verdes sin tocar ningún test**; la **api, 32
fallos**, todos `AttributeError` de `SimpleNamespace` sin las columnas nuevas en `_payloads`,
y verde (586) tras cambiar solo los dobles de abajo. Se declaran en `progress/impl_F-039.md`
(fichero, línea vieja y nueva); si falla cualquier otro, el implementer **para y avisa**.

- `services/dedicacion-api/tests/conftest.py`: `UniversoFalso` gana `universo_var(empresa)`
  (por defecto, sin obra VAR ni partidas). Doble; ningún assert.
- `_fila` de `tests/test_f022_empresa_en_linea.py`, `tests/test_f024_registro_empresa.py`
  (la importa `test_f034_obras_siempre_ruesma.py`) y `tests/test_f026_registro_recurso.py`: la
  obra `SimpleNamespace` gana `registro_obra_ide=None, registro_obra_cod=None,
  registro_paride=None`. Dobles; ningún assert.
- `services/dedicacion-transfer/tests/test_f002_fuente_unica.py`: `ANCLAS` gana
  `"regla-var"` y `"regla-seis-digitos"` (R23, ampliación deliberada).
- Ninguno más: ni `test_f025_*` (el `TransferClient` sigue siendo uno), ni `test_f003_*`, ni
  el front, ni la raíz.

## 8. Verificación MANUAL (humano; nada se escribe en Sigrid)

`scripts/verif_f039_var.ps1` (patrón de `verif_f025_postventa.ps1`), api y transfer
**locales** desde la rama, api contra la BBDD **local**. Nunca llama a `registro/ejecutar`.
- **M1** (preview, sync y cuadrante): `excluidas_por_codigo = 240`, `entradas_var = 1`,
  `obra_var = "VAR"`, `motivo_var = null`, `motivo_postventa = null`; tras el sync, en el
  cuadrante `VAR-29` (`ide = -417055`, `activa`), sin `VAR` normal ni `150414`.
- **M2** (preflight de solo lectura): a un trabajador **vigente**, en un periodo de prueba
  local, una línea en `VAR-29` y otra en una obra normal: el grupo de la obra `VAR` trae la
  acción `escribir` con `paride = 417055`, `partida_cod = "29"`, `partida_metodo = "var"` y
  `caa_cod` `VAR.CIMO…` (real) o de `0404` (pruebas); `no_vigentes = []`.
- **M3** (usabilidad, en el navegador, front local 8080): buscar «29» y «arroyo» → sale
  `VAR-29`; ni `VAR` ni `150414`; añadirla, PV avisa «no admite postventa», Completar al 100 %
  hacia `VAR-29`, Excel con `VAR-29`, y el modal «Registrar en Sigrid» con la partida fija
  «29» **sin pulsar Ejecutar**.

## 9. Riesgos y decisiones

- **Escritura real**: la línea VAR va a la obra VAR real con la partida de la entrada. En
  2026-08 la 29 ya tiene MESVE/MPRL de Administración: un registro de ese mes para esos
  recursos dará un **pisado** a confirmar (`#regla-conflicto`), no un duplicado.
- **Orden de despliegue**: transfer → api → front. Una api nueva con un transfer viejo deja el
  sync en 502 (R16) hasta publicar el transfer.
- **VAR cerrada en Sigrid**: sus entradas siguen ofreciéndose mientras haya partidas (el
  universo manda); hoy está EN CURSO.
- **Descartadas**: el universo VAR en la api (no conoce el presupuesto y el transfer es quien
  fija la partida); ampliar `/api/postventa/universo` (mezcla dos reglas en un contrato); una
  regla genérica de «obras por partidas» configurable (nadie la ha pedido); D6 B.

## 10. Ficheros que NO se tocan

`reglas_porcentajes.py`, `partida_resolver.py`, `universo_postventa.py`,
`sigrid_write_client.py`, las copias de `partes` (`partida_catalog.py`, `partida_matcher.py`,
`text_match.py`, `estado_parte.py`, `cuenta_analitica.py`), `routes.py`, `schemas.py`,
`domain/estados.py`, `domain/vigencia.py`, `domain/empresas.py`, `exporter.py`, el catálogo
del front, `infra/` (los ajustes nuevos tienen defecto) y el `.env` de ningún servicio.
