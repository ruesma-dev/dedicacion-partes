<!-- specs/F-029-seleccion-multiple-completar-100/design.md -->
# F-029 · Diseño

Requisitos en `requirements.md`; decisiones D1-D6 en su §6, decididas por el
humano el 2026-10-05 (las seis, A). Este diseño las aplica.

## 1. Límite de servicio

| Servicio | Toca | Por qué |
|---|---|---|
| `dedicacion-api` | sí | «Lo que falta» es regla de negocio (el 100 %): vive en el dominio, y el lote es un caso de uso con su transacción y sus eventos, como guardar y copiar |
| `dedicacion-front` | sí, solo `static/` y `templates/` | Selección, diálogo, botón y atajo: presentación. Su proxy `/api/*` es genérico (`api_route` con POST), así que su Python no cambia |
| `dedicacion-transfer` | **no** | El lote no registra en Sigrid; registrar sigue siendo el botón de siempre |

Nada nuevo cruza la frontera del proyecto: ni Sigrid ni otro servicio. La
consulta a Sesame es de F-021 y vivirá en la api; aquí solo se deja la puerta
del front (`fijarSeleccion`). No hay responsabilidad que pida otro servicio.

## 2. Encaje en la arquitectura

- **Dominio** (`domain/estados.py`): `completar_hasta_100`, función pura junto a
  `calcular_estado`, porque ARCHITECTURE sitúa ahí la regla del 100 % y así usa
  la misma épsilon sin exportar constantes privadas.
- **Aplicación** (`use_cases.py`): `CompletarHasta100`, mismo patrón que
  `CopiarPeriodoAnterior` (visibles en E con `_filas_de_empresa`, un evento por
  trabajador, un solo `commit`) y que `GuardarAsignaciones` (periodo ABIERTO,
  snapshots con `_snapshot`).
- **Interfaz** (`routes.py`, `schemas.py`): ruta nueva del periodo, mismo
  `_filtro` y mismo mapeo de errores (`app.py` no cambia).
- **Sin puertos nuevos**: basta con `trabajadores.listar_para_periodo` (vía
  `_filas_de_empresa`), `asignaciones.lineas_del_periodo`, `obras.
  listar_para_periodo`, `asignaciones.reemplazar` y `eventos.registrar`. Así
  ningún doble de UnitOfWork existente tiene que cambiar.

## 3. Ficheros a crear

- `services/dedicacion-api/tests/test_f029_completar.py` — dominio, caso de uso
  y rutas (R14-R26).
- `services/dedicacion-front/tests/test_f029_seleccion.py` — comprobación
  estática de `app.js`, `index.html` y `styles.css` (R1-R13), con el patrón de
  `test_f025_catalogo_postventa.py` (`_funcion`, `_plano`).

## 4. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/dedicacion-api/domain/models.py` | `TipoEvento.COMPLETAR`; enum `ResultadoCompletado`; dataclasses `Completado` y `ResultadoCompletarTrabajador` |
| `services/dedicacion-api/domain/estados.py` | `completar_hasta_100` |
| `services/dedicacion-api/application/use_cases.py` | `CompletarHasta100` y helper `_obra_destino_o_error` |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | `CompletarIn`, `ResultadoCompletarOut`, `CompletarOut`, `a_completar_out` |
| `services/dedicacion-api/interface_adapters/api/routes.py` | `POST /periodos/{anio}/{mes}/completar` |
| `services/dedicacion-front/static/js/app.js` | estado, clics, atajo, diálogo y resultado (§5.4) |
| `services/dedicacion-front/templates/index.html` | botón `#btn-completar` en `.toolbar`; pie de ayuda con Ctrl/Shift+clic y C |
| `services/dedicacion-front/static/css/styles.css` | `.fila.multi` y lo mínimo del diálogo |
| `docs/ARCHITECTURE.md` | punto 15 `#regla-completar`; `completar` en la lista de endpoints |
| `docs/INTEGRACION.md` | §5: la ruta nueva, solo para el front, como la de F-024 |
| `services/dedicacion-api/README.md` | fila de la ruta en la tabla de endpoints |

## 5. Clases y funciones

### 5.1 Dominio

```python
class TipoEvento(str, Enum):        # + COMPLETAR = "COMPLETAR"
class ResultadoCompletado(str, Enum):
    COMPLETADO, YA_AL_100, EXCESO, NO_VIGENTE, NO_VISIBLE   # valor = nombre
@dataclass(frozen=True)
class Completado:                   # lo que devuelve la regla pura
    lineas: list[Linea]; anadido: Decimal
@dataclass(frozen=True)
class ResultadoCompletarTrabajador:
    trabajador_ide: int; resultado: ResultadoCompletado
    anadido: Decimal = Decimal("0")

def completar_hasta_100(lineas: list[Linea], obra_ide: int,
                        es_postventa: bool) -> Completado | None:
```

- `None` si `calcular_estado(total, n)` es `OK` o `EXCESO` (R17).
- `falta = (_CIEN - total).quantize(Decimal("0.01"))` (D5): con dos decimales
  es exacta; el `quantize` solo blinda la escala de la columna.
- Recorre las líneas en su orden: la de clave `(obra_ide, es_postventa)` sale
  con `porcentaje + falta`; las demás, **idénticas** (mismo objeto). Sin esa
  clave, añade `Linea(obra_ide, es_postventa, falta)` al final (R15, R18).
- No mira ni empresa ni vigencia ni si la obra se ofrece: eso es del caso de
  uso. `ResultadoCompletado.YA_AL_100`/`EXCESO` los decide el caso de uso con
  el mismo `calcular_estado`, no un segundo criterio.

### 5.2 Aplicación (`use_cases.py`)

```python
class CompletarHasta100:
    def ejecutar(self, uow, anio, mes, trabajadores: list[int], obra_ide: int,
                 es_postventa: bool, usuario: str, *, filtro: FiltroEmpresa
                 ) -> tuple[list[ResultadoCompletarTrabajador], ResumenPeriodo]:
```

1. `_periodo_abierto_o_error` (R21).
2. `_obra_destino_o_error(uow, periodo_id, obra_ide, es_postventa, filtro)`:
   busca la obra en `uow.obras.listar_para_periodo(periodo_id)` con
   `o.empresa == filtro.empresa_obras` (la misma lista que ofrece el
   cuadrante). Sin ella: `ObraNoValida` «no existe o no es de la empresa de
   las obras». Con ella, la ofrecibilidad sale de la **única** definición:
   `Linea(obra_ide, es_postventa, Decimal("0"), obra_activa=o.activa,
   obra_admite_postventa=o.admite_postventa).ofrecible`; si es falsa,
   `ObraNoValida` «no se ofrece como normal / como Postv-» (R22). Va **antes**
   de tocar a nadie: un 422 no deja nada a medias (R20).
3. `filas = {f.trabajador.ide: f for f in _filas_de_empresa(uow, periodo_id,
   filtro)}`; `activo` ahí ya es «vigente en el mes» (`listar_para_periodo`).
4. Por cada `ide` de `dict.fromkeys(trabajadores)` (R14): sin fila →
   `NO_VISIBLE` (R23); `not activo` → `NO_VIGENTE` (R24); si no,
   `completar_hasta_100`. `None` → `YA_AL_100` u `EXCESO` según
   `calcular_estado`. Con resultado: `reemplazar(periodo_id, ide, lineas,
   usuario)` y `eventos.registrar(periodo_id, ide, TipoEvento.COMPLETAR,
   usuario, _snapshot(fila.lineas), _snapshot(lineas))` (R19) → `COMPLETADO`
   con `anadido`.
5. Un solo `uow.commit()` al final; devuelve resultados y
   `_resumen_periodo(uow, periodo_id, filtro)` (R25).

Excepciones: las de dominio de siempre, mapeadas en `app.py` (404, 409, 422).

### 5.3 Interfaz

```python
class CompletarIn(_Base):           # extra="forbid" → 422 (R14)
    trabajadores: list[int] = Field(min_length=1, max_length=500)
    obra_ide: int
    es_postventa: bool = False
class ResultadoCompletarOut(_Base):
    trabajador_ide: int; resultado: str; anadido: float
class CompletarOut(_Base):
    resultados: list[ResultadoCompletarOut]; resumen: ResumenOut
```

Ruta `POST /periodos/{anio}/{mes}/completar`, `response_model=CompletarOut`,
`tags=["cuadrante"]`, con `payload: CompletarIn`, `Usuario` y `EmpresaQ` como
`guardar_asignaciones`. **No** devuelve filas: el front recarga el cuadrante,
que ya calcula `puede_deshacer` por usuario (F-027) sin duplicar ese cálculo.

### 5.4 Front (`app.js`)

- `state`: `seleccion: new Set()` y `ancla: null`. `seleccionIde` sigue siendo
  el cursor y nada que lo use cambia (R5).
- `construirFila`: clase `multi` si `state.seleccion.has(t.ide)`; `mousedown`
  con `shiftKey` → `preventDefault()` (sin selección de texto); en `click`,
  con `ctrlKey || metaKey || shiftKey` → `marcarSeleccion(t.ide,
  ev.shiftKey)` y `return`; sin modificadores, `state.seleccion.clear()`,
  `state.ancla = t.ide` y lo de hoy (R4).
- `marcarSeleccion(ide, rango)` (R1, R2) y `fijarSeleccion(ides)` (R7): las
  dos únicas que escriben en `state.seleccion`; repintan con `renderTabla`.
- `seleccionEfectiva()`: `trabajadoresVisibles()` filtradas por la selección,
  o por el cursor si está vacía (R9, D6).
- `candidatasDestino(texto)`: `state.catalogoObras` con
  `normalizar` + `clave.includes`, como `montarAutocompletado`; la de `cod`
  normalizado igual al texto, primero (R10). Sin literales de obra ni
  `.filter(` con «empresa» (los vigilan F-024 y F-025).
- `abrirCompletar()`: si ABIERTO, editor cerrado y selección efectiva no vacía,
  abre el diálogo en `#modal-registro` (`abrirModal`/`cerrarModal`): campo de
  obra precargado con `state.filtrosCol.asignaciones`, lista de candidatas,
  nombres y ocultos (R9-R11). El `keydown` del campo hace `stopPropagation()`
  de todo, así F7/F8/Enter no llegan a `teclas`.
- `lanzarCompletar(entrada, filas)`: `api(.../completar, POST)` con `{
  trabajadores, obra_ide: entrada.obra.ide, es_postventa: entrada.pv }`, sin
  porcentajes (R12). Pinta resultados con nombres de `trabajadorPorIde` (R13),
  `fijarSeleccion([])` y `cargarPeriodo`. En error, `toast(err.message, true)`.
- `teclas`: con el editor cerrado y fuera de campo, `c`/`C` sin Ctrl, Meta ni
  Alt → `abrirCompletar()` si ABIERTO; `Escape` con selección → vaciarla.
  Ninguna rama existente cambia de orden ni de condición (R5).
- `cambiarEmpresa` y `moverMes`: `fijarSeleccion([])` (R6). `renderTabla`: el
  contador añade «· N seleccionados» (R3). `renderCabecera`: `#btn-completar`
  desactivado si CERRADO (R8).

## 6. Tests y dobles

- Dominio, puro: FALTA, SIN_CARGA, OK, EXCESO, suma a línea existente, línea
  nueva al final, otras líneas idénticas, falta 0,01 (D5), postventa (R18).
- Caso de uso: `_Uow` de `test_f024_cuadrante_empresa.py` **sin editarlo**.
  Ana (10, 60 % + 40 % → 100) sale `YA_AL_100`, Eva (14, sin carga) → 100 en
  101, Bea (11, de la 28) `NO_VISIBLE` con E = 1, Gil (16, `activo` falso)
  `NO_VIGENTE`. Lo que falta se amplía **dentro** de `test_f029`:
  `monkeypatch.setitem(OBRAS, …)` para una obra con `admite_postventa`, y una
  subclase del doble cuyo `reemplazar` conserva `es_postventa` (el de F-024 lo
  reconstruye con `_ln`, que lo pierde).
- Deshacer tras el lote (R19): `DeshacerUltimaModificacion` con el mismo
  usuario restaura; con otro, `DeshacerAjeno`; `puede_deshacer` por usuario.
- R20: con obra no ofrecible, `uow.reemplazados == []` y ningún evento.
- Rutas: fixture `api` de `test_f024_rutas_empresa.py`: 200 y forma de la
  respuesta; `empresa` inválida, lista vacía, 501 `ide` y campo extra → 422
  con `contenedor.uows == []`; obra 102 (inactiva), 900 (de la 28) e
  inexistente → 422; periodo inexistente → 404. R26: el `_Registro` falso del
  contenedor sigue sin llamadas.
- Front, estático: `marcarSeleccion` mira `ctrlKey`/`metaKey`/`shiftKey`; solo
  `marcarSeleccion` y `fijarSeleccion` escriben en `state.seleccion`;
  `lanzarCompletar` no contiene `porcentaje`; las ramas de `teclas` existentes
  siguen literalmente; botón, pie de ayuda y `.fila.multi` existen.
- Nombres `test_f029_rN_…`. Ningún test toca red ni BBDD.

## 7. SQL y esquema

Ninguno. `evento.tipo` es `Text`: `COMPLETAR` entra sin DDL. No cambia
`orm_models.py` ni `esquema.py`.

## 8. Documentación (R27)

- `ARCHITECTURE.md`, punto 15 `<a id="regla-completar"></a>`: qué completa
  (lo que falta sobre todas las líneas, a la clave obra+modo), cuándo no
  (OK/EXCESO por la misma épsilon, no vigente, no visible), todo o nada ante
  obra no ofrecible o periodo cerrado, un evento `COMPLETAR` por trabajador
  deshacible con `#regla-deshacer`, y que no registra en Sigrid. Con su línea
  de procedencia (D1-D6, decididas por el humano el 2026-10-05). No va a
  `ANCLAS` de `test_f002_fuente_unica.py` (tampoco `regla-deshacer`).
- `INTEGRACION.md` §5: un párrafo como el de F-024. La copia literal a
  `azure-apps/dedicacion.md` la hace el líder (T7).

## 9. Fuera de alcance

- La preselección desde Sesame y el chip único del filtro (F-021).
- Deshacer el lote entero de una vez: se deshace trabajador a trabajador.
- Vista previa de cifras antes de confirmar (exigiría un modo «simular» en la
  api; el front no puede calcularlas, R12).
- Shift+flechas para extender la selección con el teclado.
- Registrar en Sigrid tras completar.

## 10. Ficheros que NO se tocan

`services/dedicacion-transfer/**`; `infrastructure/db/repositories.py`,
`orm_models.py` y `esquema.py`; `domain/ports.py`; `interface_adapters/api/
app.py` y `deps.py`; `application/registro_sigrid.py`; el Python del front
(`interface_adapters/web/app.py`); los tests existentes (incluidos los dobles
de `test_f024_cuadrante_empresa.py` y `test_f024_rutas_empresa.py`).

## 11. Riesgos y decisiones

- **Tipo de evento propio (`COMPLETAR`) y no `GUARDAR`.** Deshacer no filtra
  por tipo, así que se comporta igual, y la auditoría distingue el lote de una
  edición a mano. Descartado reutilizar `GUARDAR`: borra esa diferencia gratis.
- **Recargar el cuadrante en vez de devolver filas.** Una petición más (~200
  trabajadores) a cambio de no duplicar `puede_deshacer` ni el mapeo de filas.
- **Concurrencia.** Como guardar: una réplica y una transacción; entre dos
  usuarios a la vez gana el último `reemplazar`, como hoy.
- **Postventa.** El riesgo de C3 (tratar `Postv-X` como X) lo cierran la clave
  `(obra_ide, es_postventa)` en la regla pura y el test de R18 con un doble
  que conserva el modo.
- **Teclado.** El riesgo real es que «C» o Esc se disparen dentro del editor o
  de un campo: van en la rama de «editor cerrado y fuera de campo», detrás de
  los `return` que ya existen, y el campo del diálogo corta la propagación.
- **Mutación.** Alcance Python pequeño; el JS no lo mide la herramienta: lo
  cubren los tests estáticos y T9.
