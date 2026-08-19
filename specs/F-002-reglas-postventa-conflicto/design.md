<!-- specs/F-002-reglas-postventa-conflicto/design.md -->
# F-002 · Diseño técnico — Fijar las reglas P4 y P5

## 0. Idea del diseño en tres líneas

1. **Una sola fuente de verdad**: las reglas P1–P5 se enuncian solo en
   `docs/ARCHITECTURE.md`, con ancla por regla. Todo lo demás remite.
2. **Un solo punto de decisión en el código**: el criterio de choque y la
   clave de conflicto salen de **una función pura**, no de dos sitios que
   pueden divergir (que es exactamente lo que ha pasado).
3. **Dos fases de trabajo**: lo que no depende de Administración se hace ya;
   lo que sí, espera y está marcado.

## 1. Límite de servicio

Las reglas P1–P5 viven en `dedicacion-transfer` y **ahí se quedan**. Esta
feature no mueve responsabilidad a ningún otro servicio:

- `dedicacion-api` no evalúa reglas de registro: agrupa por obra y llama al
  transfer (`application/registro_sigrid.py`). No se toca.
- `dedicacion-front` pinta lo que devuelve el preflight
  (`partidas_obra` / `partidas_postventa`). Si D1.2 sale «capítulo», lo que
  cambia es **qué nodos publica el preflight**, no el front. El front sigue
  sin lógica de negocio. No se toca.
- `docs/ARCHITECTURE.md` está en la raíz porque es documentación normativa
  del monorepo, no de un servicio.

**No procede extraer nada a otro microservicio.** No aparece ninguna
responsabilidad nueva; se está retirando duplicación, no añadiéndola.

## 2. Ficheros a crear

| Ruta | Qué es |
|---|---|
| `services/dedicacion-transfer/tests/conftest.py` | Fixtures compartidas: `ClienteFalso` **parametrizable** (presupuesto de postventa con hojas *o* con capítulos, líneas previas con la misma o con otra partida, con o sin `synckey`) y un `SettingsFalso`. Sin red ni BBDD. |
| `services/dedicacion-transfer/tests/test_f002_reglas.py` | Tests unitarios de `ReglasPorcentajes` (R6–R9, R12). No usan pipeline. |
| `services/dedicacion-transfer/tests/test_f002_conflicto.py` | Tests de la función pura de choque y de la clave de conflicto (R14, R18, R19). |
| `services/dedicacion-transfer/tests/test_f002_pipeline.py` | Tests de integración offline del pipeline (R10, R11, R13). |
| `services/dedicacion-transfer/tests/test_f002_postventa.py` | Tests del destino e imputación de postventa (R15–R17). **Bloqueado hasta D1.** |
| `services/dedicacion-transfer/tests/test_f002_fuente_unica.py` | Test documental: lee ficheros del repo y verifica que la regla se enuncia una sola vez y que el resto remite (R1–R5). Solo I/O de ficheros locales. |
| `progress/sigrid_F-002.md` | Volcado de las consultas C1–C5 ejecutadas por el humano (lo crea el humano en T6, la spec solo lo reserva). |

## 3. Ficheros a modificar

### 3.1. `docs/ARCHITECTURE.md` — la fuente de verdad

**Qué cambia.**

- Sección «Semántica de dominio imprescindible»: se le añade a cada punto un
  ancla HTML estable inmediatamente antes del texto:
  `<a id="regla-p1"></a>` … `<a id="regla-p5"></a>`, más
  `<a id="regla-conflicto"></a>` para el punto 6 (idempotencia y conflicto) y
  `<a id="regla-pruebas"></a>` para el punto 7. Las anclas son el contrato:
  el resto del repositorio enlaza a ellas.
- **Punto 5 (postventa, líneas 135-144)**: se sustituye el texto actual,
  incluida la marca ⚠ y la frase «Manda el `.env` (`POSTV2`), pero conviene
  confirmarlo contra Sigrid», por la redacción que salga de **D1**, con la
  línea de procedencia `Confirmado por Administración el AAAA-MM-DD ·
  <interlocutor>` y, entre paréntesis, la referencia al volcado
  `progress/sigrid_F-002.md`.
- **Punto 6 (conflicto, líneas 145-152)**: se sustituye el texto actual,
  incluida la marca ⚠ y la frase «Hay que fijar cuál es la regla buena antes
  de escribir en producción», por la redacción que salga de **D2**, con la
  misma línea de procedencia.
- **Cabecera del documento (líneas 8-10)**: la nota «La sección "Semántica de
  dominio imprescindible" está PENDIENTE DE VALIDAR» se reduce a los puntos
  que sigan sin validar. Si tras F-002 solo quedaban las dos ⚠, la nota se
  retira entera y se anota la fecha de validación.
- **Puntos 1, 2, 3, 4, 7, 8, 9**: no cambia su contenido; solo se les añade
  el ancla. Se hace en la fase no bloqueada.

**Qué NO cambia.** El resto del documento (capas, endpoints, tabla de acceso
a datos, topes de `sigrid-api`, infra). Esta feature no toca arquitectura.

### 3.2. `services/dedicacion-transfer/README.md`

**Qué se sustituye.** El bloque completo «## Reglas (Administración,
25/07/2026)», líneas **8 a 35**, incluidos los cinco enunciados P1–P5, el
sub-bloque de partida de imputación y la frase de conflictos de las líneas
31-33. Texto de reemplazo (forma; la redacción exacta la fija el implementer):

```markdown
## Reglas de negocio

Las reglas P1–P5 —qué recursos entran, qué fecha lleva la línea, la escala
del porcentaje, qué cuenta como conflicto y dónde se imputa la postventa—
**no se enuncian aquí**. Su única fuente normativa es
[`docs/ARCHITECTURE.md` § Semántica de dominio imprescindible](../../docs/ARCHITECTURE.md#semántica-de-dominio-imprescindible):
`#regla-p1` … `#regla-p5` y `#regla-conflicto`.

Lo que sí es de este servicio: la resolución automática de la partida
(`partida_resolver.py`), el override manual del front (`paride` en la línea
de entrada, `partida_metodo=manual`), y que el preflight devuelva
`partidas_obra` / `partidas_postventa` para poblar el desplegable.

`synckey = "porcentajes:{asignacion_id}"` (no se cruza con los diarios).
```

**Qué NO cambia.** «Arranque», «API», «Antes de escribir nada» y «Pitfalls
heredados»: describen el servicio, no la regla de negocio. Sí se corrige el
título del fichero (`# porcentajes-transfer` → `# dedicacion-transfer`) solo
si no arrastra más cambios; si arrastra, se deja para la feature de renombrado
y se anota.

### 3.3. `services/dedicacion-transfer/application/services/reglas_porcentajes.py`

- **Docstring de módulo, líneas 1-18**: se sustituye la lista P1–P5 completa
  por una remisión de tres líneas a las anclas de `docs/ARCHITECTURE.md`.
  Desaparecen así los dos enunciados en conflicto (línea 11-13, «la misma
  partida»; líneas 14-17, «`postventa-2`» y «CAPÍTULO»).
- **Docstring de clase, líneas 43-49**: se retira el término «capítulo» y se
  usa el que confirme D1.2. Si D1.2 sale «partida», los parámetros
  `capitulo_postventa` / `self._capitulo` se renombran a
  `partida_postventa` / `self._partida` (y su llamada en
  `registro_pipeline.py:156`).
- **Comentario de línea 77** («P5: destino obra de postventa + capítulo…»):
  se reduce a `# P5 (ver ARCHITECTURE #regla-p5)`.
- **Función nueva** en este mismo módulo (ver §4).
- **Constantes de motivo** (`MOTIVO_*`, líneas 30-39): se añade la que exija
  R15/R16 (nodo casado del tipo equivocado). Los textos existentes no se
  tocan: viajan al preflight y el front los enseña.

### 3.4. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py`

- **Docstring de módulo, líneas 1-21**: los pasos siguen listados (es
  documentación operativa útil), pero los pasos **1**, **4** y **7** dejan de
  reenunciar la regla. El paso 7 pasa de «línea(s) M* del recurso con el
  mismo código Y la misma partida» a «aplicar el criterio de choque de
  `reglas_porcentajes.criterio_choque` (ver ARCHITECTURE `#regla-conflicto`)».
- **`_destino_postventa`, líneas 79-108**: docstring sin la palabra
  «capítulo»; el cuerpo se alinea con D1 (qué nodo es válido y qué motivo se
  devuelve cuando no lo es).
- **Comentario línea 227** y **comentario líneas 243-245**: se sustituyen por
  la remisión; el comentario de 243-245 es hoy la única explicación del
  criterio y es justo la que contradice al docstring.
- **Líneas 246-253 (el filtro de choque)**: la lista por comprensión se
  sustituye por una llamada a la función pura:
  ```python
  choques = [ls for ls in existentes
             if criterio_choque(ls, a, mias=mias)]
  ```
  En la fase no bloqueada esto es un **refactor sin cambio de conducta**: la
  función replica exactamente el comportamiento actual. En la fase bloqueada,
  D2 se aplica **dentro de la función y en ningún otro sitio**.
- **Línea 296 (`_cat`)**: el filtro de nodos publicados en
  `partidas_postventa` debe usar el mismo predicado que la resolución
  automática (R17). Se alinea en la fase bloqueada.

### 3.5. `services/dedicacion-transfer/application/services/partida_resolver.py`

- **Docstring de módulo, líneas 1-14**: la descripción de POSTVENTA (líneas
  9-12) se sustituye por remisión a `#regla-p5`. La de OBRA NORMAL se
  mantiene: describe el mecanismo de casado, no la regla de negocio.
- **`resolver_postventa`, líneas 49-72**: la variable `hojas` de la línea 54
  **miente hoy** (no filtra `es_hoja`). Se corrige en la fase bloqueada según
  D1.2:
  - si D1.2 = **partida (hoja)** → `candidatos = partidas_hoja(nodos)` de
    `partida_catalog.py`, que ya existe y hace exactamente eso;
  - si D1.2 = **capítulo** → `candidatos = [n for n in nodos.values() if
    n.activa and not n.es_hoja]`.
  En cualquiera de los dos casos la variable pasa a llamarse `candidatos` y
  el docstring dice qué universo es. Se añade el motivo de omisión cuando el
  nodo que casa no es del tipo esperado.

### 3.6. `services/dedicacion-transfer/domain/models/registro_models.py`

- **Docstring de módulo, línea 7** («La identidad de la línea en el parte es
  recurso + mes + código») → remisión a `#regla-conflicto`.
- **`AccionLinea.clave_conflicto`, líneas 122-129**: deja de construir la
  clave a mano. Pasa a delegar en la función pura para que clave y criterio
  **no puedan divergir** (R14). Como `domain/` no puede importar de
  `application/`, la dirección de la dependencia es la contraria: la función
  pura vive en `application` y **recibe** el objeto; `clave_conflicto` se
  convierte en un método que acepta el conjunto de campos que forman la
  identidad (ver §4, alternativa elegida).
- **`Conflicto`, docstring líneas 131-140**: la frase «mismo código,
  cualquier día del mes» se alinea con D2.

### 3.7. `services/dedicacion-transfer/tests/test_pipeline_offline.py`

Se mantiene tal cual **mientras el refactor no cambie la conducta** (es la
red de seguridad de T2). Al cerrar D2, si la conducta cambia, se actualiza la
aserción de la clave (`"200|202607|5|80001"`, línea 176) y la de
`test_ejecutar_pisando`, y se anota el cambio en el informe: una aserción que
se toca en una feature de rigor crítico se justifica por escrito.

## 4. Clases y funciones nuevas

### `criterio_choque` — capa **application**

`services/dedicacion-transfer/application/services/reglas_porcentajes.py`

```python
CAMPOS_IDENTIDAD_OBRA: tuple[str, ...]        # p. ej. ("recurso", "periodo", "hora")
CAMPOS_IDENTIDAD_POSTVENTA: tuple[str, ...]   # ("recurso", "periodo", "hora", "paride")

def campos_identidad(destino: str) -> tuple[str, ...]:
    """Qué campos forman la identidad de una línea en el parte, según el
    destino. ÚNICO punto donde vive la decisión D2."""

def clave_conflicto(accion: AccionLinea) -> str:
    """Clave estable del conflicto, derivada de campos_identidad()."""

def criterio_choque(existente: LineaSigrid, accion: AccionLinea, *,
                    mias: set[str]) -> bool:
    """True si `existente` es la MISMA línea lógica que `accion` y no la
    hemos escrito nosotros (synckey en `mias`). Derivado de
    campos_identidad(): no reimplementa la comparación."""
```

Responsabilidad: **decidir qué es la misma línea**. Nada más. Sin I/O, sin
`settings`, sin cliente: puro sobre dataclasses del dominio. Por eso es
barata de cubrir al 100 % y de matar en la campaña de mutación, que en el
`preflight` completo (160 líneas con seis llamadas al cliente) sería un
suplicio.

**Por qué en `application/services/` y no en `domain/`.** Es una regla de
negocio del registro, hermana de P1–P5, y `docs/ARCHITECTURE.md` sitúa las
reglas en `application/services/reglas_porcentajes.py`. Ponerla en `domain/`
partiría la fuente en dos módulos, que es el problema que la feature viene a
resolver. `clave_conflicto` deja de ser `@property` de `AccionLinea` y pasa a
función de application; el atributo del dataclass se elimina y el pipeline
llama a la función. Dependencia application → domain: correcta.

**Alternativa descartada:** dejar `clave_conflicto` como property en
`domain/` y que `criterio_choque` la use. Descartada porque obliga a que la
lista de campos de identidad viva en domain y el filtro en application: dos
sitios otra vez, y son justo los dos que hoy están desalineados.

### `ClienteFalso` parametrizable — solo tests

`services/dedicacion-transfer/tests/conftest.py`. Extiende el patrón de
`tests/test_pipeline_offline.py:26-133` con constructor por argumentos:
estructura del presupuesto de postventa (`hojas` | `capitulos`), líneas
previas del parte (lista de `LineaSigrid`) y `synckeys` precargadas. Sin
`httpx`, sin sockets, sin ficheros de configuración: cumple
`docs/CONVENTIONS.md` § Tests.

## 5. SQL

**Esta feature no añade SQL de producción.** Ni consultas nuevas al cliente
de escritura, ni entradas en `services/dedicacion-api/config/config.yaml`, ni
DDL de PostgreSQL, ni ficheros `NN_nombre.sql`.

Las consultas C1–C5 de `requirements.md` §2 son **de un solo uso**, de solo
lectura y las lanza el humano contra `POST /api/sql/read` de `sigrid-api`
(base `ruesma`). No se versionan como consultas del servicio: viven en la
spec y su resultado en `progress/sigrid_F-002.md`. La convención de
`docs/CONVENTIONS.md` § SQL («las consultas contra Sigrid van en YAML
versionado») aplica a las consultas que el código ejecuta, no a una
investigación puntual.

## 6. Ficheros que NO se tocan (y por qué tientan)

| Fichero | Por qué no |
|---|---|
| `application/services/partida_catalog.py` | **Copia de `partes-persistencia`** (lista cerrada de `CLAUDE.md`). Ya expone `partidas_hoja()` y `es_hoja`: se usa, no se modifica. Tocarlo obligaría a avisar de lo mismo en el repositorio `partes`. |
| `application/services/partida_matcher.py` | Ídem. Solo interviene en la obra normal, que no está en disputa. |
| `application/services/text_match.py` | Ídem. |
| `infrastructure/sigrid/sigrid_write_client.py` | El SQL y el mapeo de campos son correctos y están confirmados contra datos reales. D1/D2 cambian **qué** `paride` se manda, no cómo se escribe. Si D1 obligara a leer un campo nuevo de `obrparpar`, se vuelve a proponer. |
| `interface_adapters/` del transfer | El contrato HTTP `preflight`/`ejecutar` no cambia. |
| `services/dedicacion-api/**` | No evalúa reglas de registro. |
| `services/dedicacion-front/**` | Sin lógica de negocio; consume `partidas_postventa` tal cual. |
| `harness/**`, `CHECKPOINTS.md` | Esta feature no mejora el arnés. |
| `.env` de cualquier servicio | Prohibido por `CLAUDE.md`. Si D1.1 cambia el código de la obra, lo cambia **el humano** en su `.env`; el implementer solo actualiza `.env.example` y el defecto de `settings.py`. |

## 7. Riesgos y decisiones

**Riesgo 1 — la feature cambia lo que se BORRA en Sigrid.** El criterio de
choque decide qué `hmores.ide` entran en un `DELETE`. Mitigación:
`OBRA_PRUEBAS_FORZAR` se queda a `true` durante toda la feature; ninguna
tarea escribe en producción; la verificación real va contra la obra `0404`
con la marca `PRUEBA-PORC` y requiere autorización expresa del humano para
esa acción concreta (T13).

**Riesgo 2 — la respuesta de Administración puede invalidar este diseño.** Si
D2 sale «(c) varias líneas pero la suma acotada a 1», ninguna de las dos
versiones sirve: haría falta una validación de suma que hoy no existe en el
transfer (y que podría corresponder a la API, que es quien conoce el
cuadrante completo del trabajador). En ese caso el implementer **para y se
vuelve a proponer**, según la regla de ritmo de trabajo de `CLAUDE.md`. Lo
mismo si D1.2 revela que cada obra original es un capítulo con varias
partidas y hay que elegir entre ellas.

**Riesgo 3 — el refactor de T2 puede cambiar conducta sin querer.** Se hace
**antes** de cerrar D1/D2 y con `tests/test_pipeline_offline.py` intacta como
red: si ese fichero cambia de resultado en T2, el refactor está mal.

**Riesgo 4 — cobertura y mutación en `registro_pipeline.py`.** Es el fichero
más grande del servicio y el diff lo va a tocar. Por eso la decisión de
extraer la función pura: concentra las líneas cambiadas con carga lógica en
un módulo pequeño y testeable, y deja en el pipeline cambios de una línea
(llamadas y comentarios). Es la diferencia entre alcanzar cero supervivientes
y no alcanzarlo.

**Decisión — no se decide por mayoría de sitios.** Tres ficheros dicen
«capítulo» y dos «partida»; el código implementa la versión A de P4 y los
docstrings la B. Esa aritmética no vale: los enunciados coinciden entre sí
porque se copiaron, no porque se validaran. La regla la fija Administración.

**Decisión — se retira la duplicación aunque D1/D2 sigan abiertas.** La fase
1 (fuente única para P1–P3, anclas, función pura, tests de lo no disputado)
no depende de la respuesta y elimina de golpe la posibilidad de que aparezca
una sexta versión de la regla mientras se espera.

**Alternativa descartada — dejar la regla en los docstrings y que
`ARCHITECTURE.md` remita al código.** El arnés declara `ARCHITECTURE.md`
normativo («el spec-author diseña contra él y el reviewer rechaza lo que lo
incumpla») y el reviewer valida contra él, no contra un docstring. Además un
docstring no se puede citar con ancla desde un README ni desde una spec.

**Alternativa descartada — resolver solo D2 y dejar D1 para otra feature.**
Las dos comparten el mismo dato (`paride`) y el mismo punto de código
(`criterio_choque` / `resolver_postventa`): partirlas duplicaría el refactor y
dejaría una feature de rigor crítico a medio cerrar sobre la misma línea de
Sigrid.
