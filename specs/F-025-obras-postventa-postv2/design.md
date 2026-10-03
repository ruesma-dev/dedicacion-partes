<!-- specs/F-025-obras-postventa-postv2/design.md -->
# F-025 · Obras de postventa sacadas de POSTV2 — diseño

Requisitos: `requirements.md` (R1-R26, D1-D8). Normativa: `docs/ARCHITECTURE.md`
(`#regla-p5`, `#regla-empresa`, `#regla-recurso`), `docs/CONVENTIONS.md`. D1-D7 aprobadas
(D4 cambiada), D8 en su opción **propuesta**; revisión: `progress/spec_F-025_revision.md`.

## 1. Encaje y límite de servicio

```
sync (api) ── lee obras de Sigrid (todas las empresas, también cerradas)
     │  separa las de la empresa de las obras (EMPRESA_IMPUTACION)
     └── POST /api/postventa/universo {empresa, obras} ──▶ transfer ── obra
                     POSTVENTA_OBRA_COD de ESA empresa + su presupuesto (lectura)
     ◀── {obra_postventa, motivo, casadas, obras: [{ide, partida}]}
api guarda obra.activa (estado) y obra.admite_postventa (universo) ──▶ front pinta
preflight (transfer) ── usa las MISMAS dos funciones para casar la línea de postventa
```

- **Transfer** es el único que conoce `POSTVENTA_OBRA_COD` y P5 (D1). El universo y el
  preflight llaman a las mismas dos funciones de `universo_postventa.py`; ninguna lógica
  de casado se copia a la api. Sigue sin empresa por defecto (`#regla-empresa`).
- **API** no lee POSTV2 ni conoce su código. Manda `EMPRESA_IMPUTACION`, la misma
  empresa de las obras que ya viaja en cada línea del registro (F-034, D4), y guarda los
  ides que vuelven como marca. Su filtro de estado sigue decidiendo solo `activa`.
- **F-026 no toca el universo** (es de obras). **Front**: lee `activa`, `admite_postventa`
  y `ofrecible`, sin lógica nueva.
- Sin responsabilidad nueva fuera de los tres servicios. Contra Sigrid, solo lecturas
  que ya existían (`obra_por_codigo`, `capitulos_de_obra`): **ninguna SQL nueva**.
- Divergencia aceptada: el universo es la foto del último sync; el preflight sigue mandando.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/application/services/universo_postventa.py` | Catálogo de postventa, casado de una obra y universo (§4.1) |
| `services/dedicacion-transfer/tests/test_f025_universo_postventa.py` | R1-R9, R25 (sin literal) y el cruce universo ⇔ preflight (R2) |
| `services/dedicacion-transfer/tests/test_f025_casado_p5.py` | R10-R11 |
| `services/dedicacion-api/tests/test_f025_sync_postventa.py` | R12-R16, R21 |
| `services/dedicacion-api/tests/test_f025_cuadrante_postventa.py` | R17-R20 |
| `services/dedicacion-front/tests/test_f025_catalogo_postventa.py` | R22-R24, estático sobre `app.js` (patrón de `test_f032_selector_de_baja.py`) |
| `scripts/verif_f025_postventa.ps1` | Verificación MANUAL M1/M2, solo lecturas y sin `ejecutar` (§8) |

## 3. Ficheros a modificar

**Transfer** (`services/dedicacion-transfer/`)
- `application/pipelines/registro_pipeline.py`: `_destino_postventa` delega en
  `universo_postventa` y **devuelve** el catálogo; fuera `self._nodos_pv`: `_es_hoja_activa_pv(nodos,
  paride)` y `partidas_postventa` usan el de la petición, vacío sin postventa (R8, R9).
- `application/services/partida_resolver.py` [D2]: `resolver_postventa` según R10; el
  docstring remite a `#regla-p5`, sin reenunciar.
- `interface_adapters/api/app.py`: `UniversoIn` (`empresa: Optional[int]`, `obras:
  list[ObraIn]`, el `ObraIn` que ya existe) y ruta `POST /api/postventa/universo` (§5):
  empresa no válida según `empresa_valida` → 422 sin leer (R4); excepción → 502 (R6).
- `tests/conftest.py`: `ClienteFalso` cuenta las llamadas a `capitulos_de_obra` y
  `obra_por_codigo` (R7); nada más (ausente y ambigua: `ClienteEmpresas` de `test_f022_…`).
- `tests/test_f002_postventa.py` [D2, D8]: los ocho tests de §7.1, y ninguno más.
- `README.md`: el endpoint, en una línea que remite a `#regla-p5`.

**API** (`services/dedicacion-api/`)
- `domain/models.py`: `Obra.admite_postventa: bool = False`; `Linea.obra_admite_postventa:
  bool = False` y propiedad `Linea.ofrecible`; `ResultadoUniverso` (§4.2).
- `domain/ports.py`: `UniversoPostventaGateway` y `ObraRepository.modos_ofrecibles`;
  `domain/errors.py`: `UniversoPostventaNoDisponible(ErrorDominio)`, que
  `interface_adapters/api/app.py` añade a `_HTTP_POR_ERROR` como 502 (R15).
- `infrastructure/transfer/transfer_client.py`: `universo_postventa(empresa, obras)`.
- `application/filtros_maestros.py`: `depurar_obras` deja de descartar: marca (§4.2).
- `application/sync_pipeline.py`: `FetchObrasStep` con gateway y empresa (R12-R15).
- `application/use_cases.py`: `PreviewSync` igual que el sync (R16); copias con
  `ln.ofrecible` (R19); `GuardarAsignaciones` rechaza la línea nueva no ofrecible (R20).
- `infrastructure/db/orm_models.py`: columna `ObraORM.admite_postventa` (R21).
- `infrastructure/db/repositories.py`: `sincronizar` guarda las dos marcas;
  `listar_para_periodo` incluye `admite_postventa`; `_a_obra`/`_a_linea`; `modos_ofrecibles`.
- `interface_adapters/api/schemas.py`: `ObraOut.admite_postventa`, `LineaOut.obra_admite_postventa`
  y `LineaOut.ofrecible`, mapeados en `a_obra_out` y `a_trabajador_out` (R17, R18).
- `interface_adapters/api/deps.py`: **un** `TransferClient` para el step, el preview y
  `RegistroSigrid`; `empresa_obras=settings.empresa_imputacion` al step y al preview.
- `config/config.yaml`: solo el comentario de `obras`; `tests/conftest.py`: doble
  `UniversoFalso` compartido. Tests anteriores que cambian: §7.1.

**Front** — `static/js/app.js`: `construirCatalogoObras` (normal si `o.activa`,
`Postv-` si `o.admite_postventa`); botón PV (R23); `copiarDeArriba` y la marca
`obra-baja` con `l.ofrecible` (R24; `chip-otra-empresa` no cambia); las líneas añadidas
desde el catálogo llevan `obra_activa`, `obra_admite_postventa` y `ofrecible` de la obra.

**Docs** — `ARCHITECTURE.md`: `#regla-p5` (universo, cerrada solo `Postv-`, casado de
R10) **conservando** su enlace `(#regla-empresa)` (`test_f022_r22_…`) y su «Confirmado
por …» (`test_f002_r4_…`), más la procedencia de F-025 (D2, D4); tabla `obra`.
`INTEGRACION.md`: §5 (endpoint interno, su consumo en el sync, timeouts) y §7 (transfer
caído ⇒ sync en 502). Copia literal a `azure-apps/dedicacion.md` (R26).

## 4. Clases y funciones

### 4.1 Transfer (`application/services/universo_postventa.py`, capa application)

```python
@dataclass(frozen=True)
class CatalogoPostventa:
    obra: ObraEntrada | None            # obra de postventa resuelta en la empresa
    nodos: dict[int, PartidaNodo]       # su presupuesto; {} si no hay obra
    motivo: str | None                  # por qué no hay catálogo (R3, R5)

def cargar_catalogo_postventa(cliente, settings, empresa: int) -> CatalogoPostventa
def casar_postventa(catalogo, codigo: str | None, nombre: str | None
                    ) -> tuple[dict | None, str | None]   # (partida, motivo)
class UniversoPostventa:
    def __init__(self, *, cliente, settings) -> None
    def calcular(self, empresa: int, obras: list[ObraEntrada]) -> dict  # §5
```

- `cargar_catalogo_postventa`: el cuerpo actual de `_destino_postventa` hasta
  `construir_catalogo` (ambigua, no encontrada: mismos textos); con `postventa_registrar
  = false`, `MOTIVO_POSTVENTA_OFF` sin leer (R5). Cita el ajuste, nunca el literal (R25).
- `casar_postventa` envuelve `resolver_postventa` y devuelve el motivo «no casa» de hoy
  (mismo texto: lo buscan `test_f002_…` y `test_f013_…`).
- `calcular`: con obras, **un** `cargar_catalogo_postventa` (R7) y un `casar_postventa`
  por obra; sin obras, no lee; las excepciones de Sigrid suben (R6). El pipeline:
  `_destino_postventa` = cargar + casar + destino (sin cambio) y devuelve los nodos.

### 4.2 API

- `Linea.ofrecible` (domain, propiedad): `obra_admite_postventa if es_postventa else
  obra_activa`. **Única** definición (R18); la usan copias, validación y schema. No mira
  la empresa: la línea en obra de otra empresa conserva su marca `otra_empresa` (F-034).
- `ResultadoUniverso` (domain, frozen): `ides: frozenset[int]`, `motivo: str | None`.
  `UniversoPostventaGateway.universo_postventa(empresa: int, obras: list[dict]) ->
  ResultadoUniverso`. `TransferClient.universo_postventa` hace el POST y, si `ok` no es
  `true` o falta `obras`, lanza `UniversoPostventaNoDisponible` con el error (R15).
- `depurar_obras(filas, estados_excluidos, filtro_activo, universo: frozenset[int])`: cada
  fila sale con `activa` y `admite_postventa`; se descarta solo si las dos son `false` (las
  cuenta `excluidos_filtro`). `ResultadoDepuracion` gana `admiten_postventa`, `solo_postventa`.
- `FetchObrasStep(sigrid, sql, estados_excluidos=None, filtro_activo=True, *, universo,
  empresa_obras: int)`: leer → validar columnas → las brutas cuya `empresa`, convertida a
  entero como en `sincronizar` (`"1"` cuenta), es `empresa_obras` → gateway **una** vez
  (`ide`, `codigo=cod`, `nombre=descripcion`) → `depurar_obras` con **todas**. Lo que se
  manda es lo que se guarda (R12) y lo que el preflight recibe (`RegistroSigrid._payloads`).
- `PreviewSync(..., *, universo, empresa_obras)`: lo mismo, y publica en `obras`
  `admiten_postventa`, `solo_postventa` y `motivo_postventa` (R16).
- `PgObraRepository.sincronizar`: `activa = fila["activa"]`, `admite_postventa =
  fila["admite_postventa"]`; `cambio` las compara; las no recibidas, las dos a `false` (R14).
- `PgObraRepository.modos_ofrecibles(ides) -> dict[int, tuple[bool, bool]]`. Con las
  líneas que ya lee (`antes`), `GuardarAsignaciones` rechaza con `ObraNoValida` la línea
  cuyo par (obra, modo) no estaba y no es ofrecible (R20); Deshacer no cambia.

## 5. Contrato `POST /api/postventa/universo` (transfer, interno)

Entrada: `{"empresa": 1, "obras": [{"ide": 1, "codigo": "0656", "nombre": "…"}]}`. Salida 200:

```json
{"ok": true, "empresa": 1,
 "obra_postventa": {"ide": 1659588, "codigo": "…", "nombre": "…", "empresa": 1},
 "motivo": null, "casadas": 83,
 "obras": [{"ide": 1, "partida": {"ide": 359825, "cod": "0656", "res": "…"}}]}
```

Errores: 422 (empresa, R4) y 502 (Sigrid, R6), con `{"ok": false, "error": "…"}`. Sin
obras → `obras: []`, sin leer Sigrid. No escribe nunca; el modo pruebas no lo afecta (P5
casa contra la obra de postventa real también en pruebas, `#regla-pruebas`).

## 6. SQL y esquema

- **Sigrid**: ninguna consulta nueva ni cambiada.
- **PostgreSQL**: `ObraORM.admite_postventa = mapped_column(Boolean, nullable=False,
  default=False, server_default=false())`; `esquema.alters_faltantes` deriva su `ALTER
  TABLE obra ADD COLUMN IF NOT EXISTS …` (test puro, como `test_f003_esquema.py`). Nada
  de DDL a mano; desplegado, lo aplica el arranque de la api (solo añade columna).

## 7. Tests (sin red ni BBDD)

- Transfer, con `ClienteFalso`: obra de postventa presente, ausente y ambigua
  (`ClienteEmpresas`), empresa no válida → 422 sin lecturas, `POSTVENTA_REGISTRAR=false`,
  fallo de Sigrid → 502 (`TestClient`), una carga por petición, y **cruce R2
  parametrizado**: exacta, sufijo de letra, `CP`, obra-capítulo (`0678.MO`, D8), solo
  descripción, solo nombre, sin casado: «en el universo con X» ⇔ «el preflight publica X
  en `capitulo_postventa`» (`conftest.linea()` ya trae `recurso_ide`). `_nodos_pv`: dos
  preflights seguidos (con y sin postventa) y un override tras otro presupuesto (R8, R9).
  R25: el módulo nuevo sin el literal y citando `POSTVENTA_OBRA_COD` (como `test_f002_r5_…`).
- API, con `UniversoFalso`: sync y preview con obras de la 1 CERRADA+universo, CERRADA
  sin universo, EN CURSO con y sin universo, y una de la 28 que **no** va al gateway y
  sale sin `admite_postventa`; transfer caído → 502 sin persistir (UoW que registra
  `commit`); `ofrecible` en los cuatro casos; copias; guardar 422 y con línea ya
  guardada; `ObraOut`/`LineaOut`; ALTER derivado.
- Front estático: `Postv-` depende de `o.admite_postventa` y la normal de `o.activa`;
  ningún literal `POSTV`; copia y marca usan `l.ofrecible`.
- Nombres `test_f025_rN_…`. Rigor crítico: RED antes de cada tarea, cobertura y mutación
  completa con cero supervivientes (`harness/rigor.json`).

### 7.1 Tests existentes que cambian (lista cerrada)

Comprobada el 2026-10-03 aplicando la forma mínima de esta spec en una copia
(`progress/spec_F-025_revision.md` §3). Se declaran en `progress/impl_F-025.md` (test,
assert viejo y nuevo, requisito); si falla otro, el implementer **para y avisa**.

- `test_f002_postventa.py`, D2 (aprobados): `r18_la_cascada_solo_actua_sin_exacto` y
  `r18_el_ultimo_escalon_casa_por_nombre_de_obra` esperan `None`; los dos `r19` usan un
  catálogo local con `0578B` y `0578C` (las fixtures de `conftest.py` no se tocan).
- `test_f002_postventa.py`, D8 (pendiente):
  `r16_el_capitulo_no_llega_al_paride_de_la_linea` (omitida «no casa», sin `paride`);
  `r17_el_automatico_y_el_desplegable_comparten_universo[capitulos]` (`elegida` es `None`,
  el resto igual); `r16_un_override_manual_a_un_capitulo_se_omite` y
  `r16_un_override_manual_a_una_hoja_si_vale` pasan al presupuesto `hojas` (override al
  capítulo `11` → `MOTIVO_PARTIDA_PV_NO_HOJA`; a la hoja `0713` → manual).
- Verdes sin tocar el assert (solo el docstring, si cita un escalón retirado):
  `r18_casado_por_codigo_exacto`, `r18_el_escalon_del_nombre_tambien_mira_solo_hojas_activas`.
- API, solo firmas y dobles (`UniversoFalso`, `empresa_obras=1`), ningún valor esperado:
  `test_f023_sync_empresa.py` (`_pipeline`, `_preview`, `_contenedor` con
  `deps.TransferClient` sustituido, `r17_preview_publica_claves_nuevas_y_antiguas`, `_obr`
  con `activa=True, admite_postventa=False`, `_obra_orm` con `admite_postventa=False`);
  `test_f026_sync_recurso.py` (`_preview`, `r17_el_reloj_del_preview_por_defecto_es_el_del_dia`);
  `test_f032_empresas_sigrid.py` (`_preview`, `_contenedor`, los dos `r1_pipeline_…`);
  `test_f024_cuadrante_empresa.py` (`_Obras.modos_ofrecibles`; el `SimpleNamespace` de
  `r11_a_linea_mapea_la_empresa_de_la_obra` con `admite_postventa=False`).
- `test_f034_rutas.py`: `CAMPOS_LINEA` gana `obra_admite_postventa` y `ofrecible` (R18).
- Front y tests de la raíz: ninguno.

## 8. Verificación MANUAL (humano; nada se escribe en Sigrid)

`scripts/verif_f025_postventa.ps1` (patrón de `verif_f034_f026.ps1`), API y transfer
**locales** contra la BBDD local. Aunque el transfer local esté en modo real, el script
**nunca llama a `registro/ejecutar`**: solo `sync/preview`, `sync` (BBDD **local**),
`cuadrante` y `registro/preflight`.
- **M1**: preview → `admiten_postventa`/`solo_postventa` (esperado con D2 = B: 83 y 73),
  `motivo_postventa: null` y `CP`/`OT`/`191105` fuera; sync; cuadrante (con cualquier
  empresa elegida): 0656, 0660, 0669 y 0689 con `activa=false` y `admite_postventa=true`.
- **M2**: en un periodo de prueba local, a un trabajador **vigente** en el mes (si no,
  va a `no_vigentes`, F-026) una línea `Postv-0656` y otra normal en una obra sin
  postventa; preflight → `capitulo_postventa.cod = "0656"` en la de postventa,
  `partidas_postventa` vacío en la otra obra (R8) y `no_vigentes: []`.

## 9. Riesgos y decisiones

- **Escritura real**: el único efecto sobre Sigrid es qué líneas de postventa llegan a
  escribirse; R10-R11 (D2) evita imputar a `CP.1`/`CI.7.5`/`0611`.
- **Sync dependiente del transfer** (D3): una lectura de la obra de postventa y una de
  su presupuesto por sync (D4), muy por debajo de `TRANSFER_TIMEOUT_S` (180 s) y de los
  timeouts encadenados (`INTEGRACION.md` §5). Si el transfer cae, el sync falla entero.
- **Universo reducido** (D5, D8): obras abiertas sin partida y obras-capítulo, sin `Postv-`.
  Lo ya guardado no se toca: sale marcado y el registro lo manda (el transfer decide).
- **Descartado**: la api calcula el universo (D1); un universo por empresa (D4 vieja);
  guardar la partida en la api; quitar «cerrada» de `estados_excluidos` (~467 obras).

## 10. Ficheros que NO se tocan

`reglas_porcentajes.py` (solo se importan constantes y `empresa_valida`), contrato
`preflight`/`ejecutar`, `registro_sigrid.py` de la api (payload igual: `recurso_ide` y
empresa de las obras), `routes.py`, `sigrid_write_client.py`, las copias de `partes`
(`partida_catalog.py`, `partida_matcher.py`, `text_match.py`), export, `domain/empresas.py`,
`domain/vigencia.py`, sync de empleados y empresas, `infra/`, `.env` de ningún servicio.
