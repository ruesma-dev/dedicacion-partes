<!-- specs/F-025-obras-postventa-postv2/design.md -->
# F-025 · Obras de postventa sacadas de POSTV2 — diseño

Requisitos: `requirements.md` (R1-R26, D1-D7). Normativa: `docs/ARCHITECTURE.md`
(`#regla-p5`, `#regla-empresa`) y `docs/CONVENTIONS.md`. Escrito con D1-D7 en su
opción **propuesta**; si el humano elige otra, se ajusta esta spec antes de implementar.

## 1. Encaje y límite de servicio

```
sync (api) ── lee obras de Sigrid (todas, también cerradas) ──┐
     │                                                         │
     └── POST /api/postventa/universo {obras} ──▶ transfer ── obra POSTVENTA_OBRA_COD de
                                                   cada empresa + su presupuesto (lectura)
     ◀── {obras: [{ide, partida}], empresas: {E: {obra_postventa, motivo}}}
api guarda obra.activa (estado) y obra.admite_postventa (universo) ──▶ front pinta
preflight (transfer) ── usa las MISMAS dos funciones para casar la línea de postventa
```

- **Transfer** es el único que conoce `POSTVENTA_OBRA_COD` y P5 (D1). El universo y el
  preflight llaman a las mismas dos funciones de `universo_postventa.py`; ninguna lógica
  de casado se copia a la api.
- **API** no lee POSTV2 ni conoce su código: recibe ides y los guarda como marca. Su
  filtro de estado (`estados_excluidos`) sigue decidiendo solo `activa`.
- **Front**: sin lógica nueva; lee `activa`, `admite_postventa`, `ofrecible`.
- Sin responsabilidad nueva fuera de los tres servicios. Contra Sigrid, solo lecturas
  que ya existían (`obra_por_codigo`, `capitulos_de_obra`): **ninguna SQL nueva**.
- Divergencia temporal aceptada: el universo es una foto del último sync; si POSTV2
  cambia después, el preflight sigue mandando (omite con motivo lo que ya no casa).

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/application/services/universo_postventa.py` | Carga del catálogo de postventa, casado de una obra y cálculo del universo (§4.1) |
| `services/dedicacion-transfer/tests/test_f025_universo_postventa.py` | R1-R9 y el cruce universo ⇔ preflight (R2) |
| `services/dedicacion-transfer/tests/test_f025_casado_p5.py` | R10-R11 (solo con D2 = B) |
| `services/dedicacion-api/tests/test_f025_sync_postventa.py` | R12-R16, R21 |
| `services/dedicacion-api/tests/test_f025_cuadrante_postventa.py` | R17-R20 |
| `services/dedicacion-front/tests/test_f025_catalogo_postventa.py` | R22-R24, estático sobre `app.js` (patrón de `test_f032_selector_de_baja.py`) |
| `scripts/verif_f025_postventa.ps1` | Verificación MANUAL M1/M2, solo lecturas y sin `ejecutar` (§8) |

## 3. Ficheros a modificar

**Transfer**
- `application/pipelines/registro_pipeline.py`: `_destino_postventa` delega en
  `universo_postventa` y **devuelve** el catálogo; fuera `self._nodos_pv`;
  `_es_hoja_activa_pv(nodos, paride)` recibe el catálogo de la petición; `partidas_postventa`
  se publica desde la variable local (vacía si no hubo postventa) (R8, R9).
- `application/services/partida_resolver.py` [D2]: `resolver_postventa` según R10; el
  docstring remite a `#regla-p5`, sin reenunciar.
- `interface_adapters/api/app.py`: `ObraUniversoIn`, `UniversoIn`, ruta
  `POST /api/postventa/universo` (§5); `RuntimeError`/`SigridError` → 502 (R6).
- `tests/test_f002_postventa.py` [D2]: solo los cuatro tests que nombra D2. Ningún otro
  assert de F-002, F-013, F-022 ni F-024 cambia; si alguno depende de una cascada
  retirada, **PARA** y se anota (no se reescribe en silencio).
- `tests/conftest.py`: `ClienteFalso` cuenta las llamadas a `capitulos_de_obra` y a
  `obra_por_codigo` (R7) y admite POSTV2 por empresa (R3, D4).
- `README.md` del transfer: el endpoint, en una línea que remite a `#regla-p5`.

**API**
- `domain/models.py`: `Obra.admite_postventa: bool = False`; `Linea.obra_admite_postventa:
  bool = False` y propiedad `Linea.ofrecible` (§4.2).
- `domain/ports.py`: `UniversoPostventaGateway` (Protocol, §4.2).
- `domain/errors.py`: `UniversoPostventaNoDisponible(ErrorDominio)`.
- `interface_adapters/api/app.py`: mapea ese error a 502 (R15).
- `infrastructure/transfer/transfer_client.py`: `universo_postventa(obras)` (§4.2).
- `application/filtros_maestros.py`: `depurar_obras` deja de descartar: marca (§4.2).
- `application/sync_pipeline.py`: `FetchObrasStep` recibe el gateway y combina (R12-R15).
- `application/use_cases.py`: `PreviewSync` igual que el sync (R16); copias con
  `ln.ofrecible` (R19); `_validar_lineas` + `GuardarAsignaciones` (R20).
- `infrastructure/db/orm_models.py`: columna `ObraORM.admite_postventa` (R21).
- `infrastructure/db/repositories.py`: `sincronizar` guarda las dos marcas;
  `listar_para_periodo` con `admite_postventa`; `_a_obra`/`_a_linea` las llevan;
  `modos_ofrecibles(ides)` nuevo (R20).
- `interface_adapters/api/schemas.py`: `ObraOut.admite_postventa`;
  `LineaOut.obra_admite_postventa` y `LineaOut.ofrecible` (R17, R18).
- `interface_adapters/api/deps.py`: pasa `TransferClient` al step y al preview.
- `config/config.yaml`: solo el comentario de `obras` (el filtro decide `activa`, no
  la presencia); los literales de `estados_excluidos` no cambian.
- Tests existentes de la api que construyan `FetchObrasStep`/`PreviewSync` o dobles de
  `ObraRepository`: solo se les añade el doble del gateway o el método nuevo, sin
  cambiar valores esperados.

**Front** — `static/js/app.js`: `construirCatalogoObras` (normal si `o.activa`,
`Postv-` si `o.admite_postventa`); botón PV (R23); copia de fila y marca `obra-baja` con
`l.ofrecible` (R24); las líneas añadidas desde el catálogo llevan `obra_activa` y
`obra_admite_postventa` de la obra elegida.

**Docs** — `docs/ARCHITECTURE.md` (`#regla-p5`, descripción de la tabla `obra`),
`docs/INTEGRACION.md` (endpoint del transfer; la api lo consume; tabla de «qué se
rompe»: transfer caído ⇒ sync en 502), y copia a `azure-apps/dedicacion.md` (R26).

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
    def calcular(self, obras: list[ObraEntrada]) -> dict   # contrato de §5
```

- `cargar_catalogo_postventa` es el cuerpo actual de `_destino_postventa` hasta
  `construir_catalogo` (ambigua → motivo; no encontrada → motivo, mismos textos).
  Con `settings.postventa_registrar` a `false` devuelve `motivo = MOTIVO_POSTVENTA_OFF`
  sin leer nada (R5). Cita el ajuste, nunca el literal (R25).
- `casar_postventa` envuelve `resolver_postventa` y devuelve el motivo «no casa» que hoy
  construye `_destino_postventa` (mismo texto: los tests de F-002/F-022 no cambian).
- `UniversoPostventa.calcular`: agrupa por `empresa` válida (`empresa_valida` de
  `reglas_porcentajes`; R4), un `cargar_catalogo_postventa` por empresa (R7) y un
  `casar_postventa` por obra. Excepciones de Sigrid suben (R6): no hay resultado parcial.
- El pipeline: `_destino_postventa` = `cargar_catalogo_postventa` + `casar_postventa` +
  destino (pruebas/real, sin cambio), y devuelve además `catalogo.nodos`.

### 4.2 API

- `Linea.ofrecible` (domain, propiedad): `obra_admite_postventa if es_postventa else
  obra_activa`. Es la **única** definición (R18); la usan copias, validación y schema.
- `UniversoPostventaGateway.universo(obras: list[dict]) -> dict[int, dict]`: ide → partida.
  `TransferClient.universo_postventa` hace el POST y, si `ok` no es `true` o falta `obras`,
  lanza `UniversoPostventaNoDisponible` con el error recibido (R15). Guarda además
  `empresas` para el preview.
- `depurar_obras(filas, estados_excluidos, filtro_activo, universo: set[int])`: cada fila
  sale con `activa` y `admite_postventa`; se descarta solo si las dos son `false`
  (`excluidos_filtro` cuenta esas). `ResultadoDepuracion` gana `solo_postventa: int`.
- `FetchObrasStep.ejecutar`: leer → validar columnas → gateway con **todas** las brutas
  (`ide`, `codigo=cod`, `nombre=descripcion`, `empresa`) → `depurar_obras`. Lo que se manda
  es lo que se guarda (R12): el preflight recibirá después ese mismo `cod`/`descripcion`.
- `PgObraRepository.sincronizar`: escribe `activa = fila["activa"]` y
  `admite_postventa = fila["admite_postventa"]`; `cambio` las compara; las no recibidas
  pasan a `false` las dos (R14).
- `PgObraRepository.modos_ofrecibles(ides) -> dict[int, tuple[bool, bool]]`
  (`activa`, `admite_postventa`). `_validar_lineas(..., previas)` rechaza con
  `ObraNoValida` la línea cuyo par (obra, modo) no está en `previas` y no es ofrecible
  (R20); `DeshacerUltimaModificacion` sigue con `permitir_inactivas=True`.

## 5. Contrato `POST /api/postventa/universo` (transfer, interno)

Entrada: `{"obras": [{"ide": 1, "codigo": "0656", "nombre": "…", "empresa": 1}]}`.
Salida 200:

```json
{"ok": true,
 "empresas": {"1": {"obra_postventa": {"ide": 1659588, "codigo": "…", "nombre": "…",
                                       "empresa": 1}, "motivo": null, "casadas": 83}},
 "obras": [{"ide": 1, "partida": {"ide": 359825, "cod": "0656", "res": "…"}}]}
```

Error: 502 `{"ok": false, "error": "…"}`. Lista vacía de obras → `obras: []`, sin leer
Sigrid. No escribe nunca; el modo pruebas no lo afecta (P5 casa contra la obra de
postventa real también en pruebas, `#regla-pruebas`).

## 6. SQL y esquema

- **Sigrid**: ninguna consulta nueva ni cambiada.
- **PostgreSQL**: `ObraORM.admite_postventa = mapped_column(Boolean, nullable=False,
  default=False, server_default=false())`. `esquema.alters_faltantes` deriva el
  `ALTER TABLE obra ADD COLUMN IF NOT EXISTS admite_postventa BOOLEAN DEFAULT false NOT
  NULL` (test puro como los de `test_f003_esquema.py`). Nada de DDL a mano. Desplegado,
  lo aplica el arranque de la api (sin migración: solo añade columna).

## 7. Tests (sin red ni BBDD)

- Transfer, con `ClienteFalso` de `conftest.py`: universo por empresa (POSTV2 en 1 y 28;
  ausente en 18), ambigua, sin empresa, `POSTVENTA_REGISTRAR=false`, fallo de Sigrid →
  502 vía `TestClient`, una carga por empresa, y **cruce R2 parametrizado** sobre las
  mismas obras: exacta, sufijo de letra, `CP`, solo descripción, solo nombre, sin casado,
  otra empresa. Para cada una, «en el universo con X» ⇔ «el preflight le asigna X».
  `_nodos_pv`: dos preflights seguidos en la misma instancia (con y sin postventa) y un
  override validado tras un catálogo de otra empresa (R8, R9).
- API: gateway falso; sync y preview con obras CERRADA+universo, CERRADA sin universo,
  EN CURSO con y sin universo; transfer caído → 502 sin persistir (UoW falso que registra
  `commit`); `ofrecible` en los cuatro casos; copias; guardar 422 y guardar con línea ya
  guardada; `ObraOut`/`LineaOut`; ALTER derivado.
- Front estático: la entrada `Postv-` depende de `o.admite_postventa` y la normal de
  `o.activa`; ningún literal `POSTV`; copia y marca usan `l.ofrecible`.
- Nombres `test_f025_rN_…`. Rigor crítico: RED antes de cada tarea, cobertura y mutación
  completa con cero supervivientes (`harness/rigor.json`).

## 8. Verificación MANUAL (humano; nada se escribe en Sigrid)

`scripts/verif_f025_postventa.ps1`, API (8090) y transfer (8006) **locales** contra la
BBDD local. Aviso: aunque el `.env` local del transfer esté en modo real, el script **no
llama nunca a `registro/ejecutar`**; solo `sync/preview`, `sync` (escribe en la BBDD
**local**), `cuadrante` y `registro/preflight`.
- **M1**: preview → `admiten_postventa` y `solo_postventa` de la empresa 1 (esperado con
  D2 = B: 83 y 73) y `CP`/`OT`/`191105` fuera; sync; cuadrante de la 1: 0656, 0660, 0669 y
  0689 con `activa=false` y `admite_postventa=true`.
- **M2**: en un periodo de prueba local, una línea `Postv-0656` y otra normal sin
  postventa; preflight → la de postventa con `capitulo_postventa.cod = "0656"` y
  `partidas_postventa` vacío en la obra sin postventa (R8).

## 9. Riesgos y decisiones

- **Escritura real**: el único efecto sobre Sigrid es qué líneas de postventa llegan a
  escribirse; R10-R11 (D2) evita imputar a `CP.1`/`CI.7.5`/`0611`. Con D2 = A sigue el
  riesgo de hoy (`CP`, `OT`) y entra `191105`.
- **Sync más lento y dependiente del transfer** (D3): ~20 empresas × una lectura de obra
  + dos presupuestos; muy por debajo de `TRANSFER_TIMEOUT_S` (180 s) y de los 200 s del
  front. Si el transfer cae, el sync falla entero y lo dice.
- **Universo reducido** (D4, D5): obras abiertas sin partida y empresas sin POSTV2 dejan
  de ofrecer `Postv-`. Las líneas ya guardadas no se tocan: salen marcadas y el registro
  las sigue mandando (el transfer decide, como hoy).
- **Descartado**: que la api calcule el universo (D1); guardar la partida en la api (no
  hace falta: el preflight la resuelve otra vez y el desplegable sigue saliendo del
  preflight); quitar «cerrada» de `estados_excluidos` (metería ~467 obras como normales).

## 10. Ficheros que NO se tocan

`reglas_porcentajes.py` (P1-P4, capacidad, sin partida; solo se importan sus
constantes), contrato `preflight`/`ejecutar`, `registro_sigrid.py` (payload igual),
`sigrid_write_client.py`, `partida_catalog.py`/`partida_matcher.py`/`text_match.py`
(copias de `partes`), export a Excel, `domain/empresas.py`, sync de empleados y
empresas, `infra/`, `.env` de ningún servicio.
