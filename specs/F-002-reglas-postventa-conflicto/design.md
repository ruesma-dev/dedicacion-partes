<!-- specs/F-002-reglas-postventa-conflicto/design.md -->
# F-002 · Diseño técnico — Fijar las reglas P4 y P5

> **Versión 2 (2026-08-19).** D1 y D2 están cerradas (`requirements.md` §2) y
> la Fase 1 (T1–T5) está implementada y aprobada. Lo que la v1 dejaba
> condicionado («según lo que conteste Administración») aquí está decidido.
> El §7 Riesgo 2 de la v1 —«la respuesta puede invalidar este diseño»— ya no
> es un riesgo: **es el diseño**, y está en §5.

## 0. Idea del diseño en cuatro líneas

1. **Una sola fuente de verdad**: las reglas P1–P5 se enuncian solo en
   `docs/ARCHITECTURE.md`, con ancla por regla. Todo lo demás remite.
2. **Un solo punto de decisión por regla**: la identidad de una línea sale de
   una tupla (`CAMPOS_CLAVE`) y la capacidad de una función pura; ninguna de
   las dos se reimplementa en el pipeline.
3. **P4 se parte en dos**: *identidad* (qué es la misma línea) y *capacidad*
   (cuánta jornada cabe). Son reglas distintas y se prueban por separado.
4. **La capacidad avisa, no decide**: emite un conflicto más, y sin
   confirmación del humano no se escribe nada.

## 1. Límite de servicio

Las reglas P1–P5 viven en `dedicacion-transfer` y **ahí se quedan**, incluida
la Regla B. Esta feature no mueve responsabilidad a ningún otro servicio.

**Por qué la Regla B no va a `dedicacion-api`, que es quien ve el cuadrante
completo.** Porque son dos reglas distintas sobre dos realidades distintas:

| | Regla del cuadrante (API) | Regla B · capacidad (transfer) |
|---|---|---|
| Qué vigila | que las asignaciones de un trabajador sumen 100 % **entre todas sus obras** | que un **parte de Sigrid** no acabe con más de una jornada del trabajador |
| Sobre qué datos | PostgreSQL `asignacion`, que es todo lo nuestro | `hmores` del parte, que incluye **líneas que metió Administración a mano** y que la API no ve ni verá |
| Dónde vive | `dedicacion-api/domain/estados.py` | `dedicacion-transfer/application/services/reglas_porcentajes.py` |
| Qué comparte | la **tolerancia** | la misma, convertida de escala (§4.3) |

La API no puede evaluar la Regla B porque no conoce las líneas previas del
parte; el transfer no puede evaluar la del cuadrante porque se le invoca
**por obra**. Ponerlas juntas obligaría a uno de los dos a leer datos del
otro, que es exactamente el acoplamiento que la arquitectura evita.

- `dedicacion-api` no evalúa reglas de registro: agrupa por obra y llama al
  transfer (`application/registro_sigrid.py`). **No se toca.**
- `dedicacion-front` pinta lo que devuelve el preflight. **No se toca.** El
  coste de esa decisión está medido en §8.
- `docs/ARCHITECTURE.md` está en la raíz porque es documentación normativa
  del monorepo, no de un servicio.

**No procede extraer nada a otro microservicio.** No aparece ninguna
responsabilidad nueva de sistema: aparece una regla nueva **dentro** de la
responsabilidad que el transfer ya tiene (decidir qué se escribe en un parte).

### 1.1. Un efecto que cruza la frontera sin cambiar código ajeno

R28 hace que las líneas bloqueadas por una sobrecarga sin confirmar entren en
`ResultadoRegistro.omitidas`. La API consume ese campo en
`dedicacion-api/application/registro_sigrid.py` (`for o in
r.get("omitidas", [])`) y escribe en PostgreSQL
`asignacion.sigrid_estado = 'omitido'` con el motivo recortado a 300
caracteres. Es decir: **sin tocar una línea de la API, esta feature cambia el
estado que la API persiste** para esas asignaciones.

Es deliberado y es lo correcto: hoy una línea bloqueada por un conflicto no
aparece en ninguna parte del resultado salvo en `pendientes_confirmacion`, y
en la base se queda con su estado anterior, que miente. Con esto queda
`omitido` con el motivo real («sobrecarga: …»), y pasa a `registrado` en
cuanto el humano confirme y reejecute.

Dos consecuencias que hay que aceptar por escrito:

- El motivo debe caber **con sentido en 300 caracteres**, porque la API lo
  trunca. El texto del motivo se diseña corto (§4.4).
- El *toast* del front suma `omitidas` y `pendientes_confirmacion` por
  separado, así que una línea bloqueada por sobrecarga se cuenta en las dos
  cifras. Es un resumen, no un libro de cuentas; se documenta y no se corrige
  aquí (tocaría el front, y §1 dice que no).

**No se aplica lo mismo a los pisados sin confirmar**, que siguen viajando
solo en `pendientes_confirmacion`. Motivo: un pisado sin confirmar es un paso
normal del flujo («repite y marca pisar»), mientras que una sobrecarga es una
**anomalía entre el cuadrante y Sigrid** que tiene que dejar rastro aunque
nadie vuelva a ejecutar.

## 2. Ficheros a crear

| Ruta | Qué es | Estado |
|---|---|---|
| `services/dedicacion-transfer/tests/conftest.py` | Fixtures compartidas parametrizables. | **creado en T1** |
| `services/dedicacion-transfer/tests/test_f002_reglas.py` | R6–R9, R12 sobre `ReglasPorcentajes`. | **creado en T2** |
| `services/dedicacion-transfer/tests/test_f002_conflicto.py` | R14, y en T10 R20–R22. | **creado en T4** |
| `services/dedicacion-transfer/tests/test_f002_pipeline.py` | R10, R11, R13, y en T12 R28/R29/R32. | **creado en T4** |
| `services/dedicacion-transfer/tests/test_f002_fuente_unica.py` | R1–R5. | **creado en T5** |
| `services/dedicacion-transfer/tests/test_f002_postventa.py` | R15–R19. | **T9** |
| `services/dedicacion-transfer/tests/test_f002_capacidad.py` | R23–R27, R30, R31, R33. | **T11** |

No hace falta ningún fichero de producción nuevo: las dos reglas caben en
módulos que ya existen, y meterlas en uno nuevo partiría la fuente única que
la feature viene a construir.

### 2.1. Qué hace falta añadir a `conftest.py`

Las fixtures de T1 sirven tal cual (`ClienteFalso(presupuesto_postventa=…,
lineas_parte=…, synckeys=…, parte_existe=…, obra_postventa_existe=…)`,
`linea()`, `linea_previa()`, `inserts()`, `borrados()`). Se les añade:

- un tercer presupuesto de postventa, `"hojas_inactivas"`, con la partida de
  la obra original marcada `tipdes = 1` (R16);
- un cuarto, `"orden_invertido"`, con las mismas filas de `"hojas"` en orden
  inverso, para R19;
- que `PRESUPUESTO_PV_HOJAS` incluya un capítulo con **código numérico**
  (`_fila(69100, 69000, 3, "11", "OBRAS VARIAS")`) y las partidas `0656` y
  `656` a la vez, que es la trampa real que documenta `sigrid_F-002.md`
  (R18);
- un ayudante `linea_previa_m(cod, can, paride)` para poblar partes con
  varias líneas `M*` del mismo recurso sin repetir el diccionario.

Sigue sin red, sin BBDD y sin `.env`.

## 3. Ficheros a modificar

### 3.1. `docs/ARCHITECTURE.md` — la fuente de verdad

- **Punto 5 (`#regla-p5`)**: se sustituye la marca `PENDIENTE · decisión
  D1/D2 de F-002` por la redacción definitiva de D1: obra
  `POSTVENTA_OBRA_COD`, **partida hoja activa**, casado por **código
  exacto**, y omisión con motivo si no casa. Con la línea de procedencia
  (R4) y la referencia a `progress/sigrid_F-002.md`.
- **Punto 6 (`#regla-p4` / `#regla-conflicto`)**: pasa a enunciar **solo la
  Regla A**: la identidad de una línea del parte es recurso + mes + código de
  hora + partida, en obra normal y en postventa; y la idempotencia por
  `synckey`. Con su línea de procedencia.
- **Punto nuevo (`#regla-capacidad`)**: la Regla B, con su límite, su
  tolerancia, su alcance (un parte = una obra) y la remisión explícita al
  punto 4 (el 100 % del cuadrante) para que quede escrito que **las dos
  tolerancias son la misma**.
- **Punto 4 (el 100 % del cuadrante)**: se le añade una frase cruzada hacia
  `#regla-capacidad`, para que quien cambie la épsilon de `estados.py` vea
  que hay otra que depende de ella.
- **Cabecera**: la nota «PENDIENTE DE VALIDAR» se retira, porque ya no queda
  ningún punto sin validar; se anota la fecha de validación.

**Qué NO cambia.** El resto del documento (capas, endpoints, tabla de acceso
a datos, topes de `sigrid-api`, infra).

### 3.2. `services/dedicacion-transfer/README.md`

Se sustituye el bloque de P4 y P5 que T5 dejó marcado como **no normativo**
por la remisión a `#regla-p4`, `#regla-p5` y `#regla-capacidad`. Desaparecen
las frases prohibidas «aunque tenga otra partida», «la misma partida en ese
parte» e «imputando al CAPÍTULO».

Lo que sí es de este servicio y se queda: la resolución automática de la
partida, el override manual del front, y que el preflight devuelva
`partidas_obra` / `partidas_postventa`.

### 3.3. `application/services/reglas_porcentajes.py`

- **`campos_identidad`**: hoy devuelve `CAMPOS_CLAVE` completos solo en
  postventa y quita `paride` en obra normal. Pasa a devolver `CAMPOS_CLAVE`
  **siempre** (R20). Con eso el parámetro `destino` deja de decidir nada, así
  que **se elimina de la firma** y `criterio_choque` la llama sin argumentos.
  Es una desviación consciente respecto a «cambia solo el cuerpo»: un
  parámetro que ya no decide es una mentira en la firma, un aviso de `ruff`
  y una rama muerta que la campaña de mutación no puede matar. La función
  sigue siendo el punto único de decisión, que es lo que importaba.
- **Constantes nuevas de la Regla B** (§4.3): `LIMITE_CAPACIDAD`,
  `EPSILON_CAPACIDAD`, `PREFIJO_CLAVE_SOBRECARGA`, `MOTIVO_SOBRECARGA`.
- **Funciones nuevas de la Regla B** (§4.2): `es_linea_mensual`,
  `evaluar_capacidad`, `clave_sobrecarga`.
- **Motivo nuevo de postventa**: `MOTIVO_PARTIDA_PV_NO_HOJA`, para R16.
- **`ReglasPorcentajes`**: el parámetro `capitulo_postventa` y el atributo
  `self._capitulo` pasan a `partida_postventa` / `self._partida`, y el
  docstring deja de decir «capítulo» (D1.2 dice partida). Se actualiza su
  única llamada, en `registro_pipeline.py`.
- **Comentario `# P5: destino obra de postventa + capítulo…`**: pasa a
  `# P5 (ver ARCHITECTURE #regla-p5)`.

### 3.4. `application/services/partida_resolver.py`

El defecto de D1: la variable `hojas` no filtra por hoja.

```python
# antes
hojas = [n for n in nodos.values() if n.activa]
# después
candidatos = partidas_hoja(nodos)      # hojas activas, ordenadas por código
```

`partidas_hoja` ya está importada en el módulo y ya se usa en
`resolver_normal`; llamada sin `categoria`/`categorias` devuelve **todas las
hojas activas ordenadas por código**. Con eso:

- se cierra R16 (la resolución automática no puede devolver un capítulo);
- se cierra R17 (es exactamente el universo que publica `_cat`);
- se cierra R19 **de propina**: `partidas_hoja` ordena por `cod`, mientras
  que hoy el orden es el de inserción del `dict`, es decir, el orden en que
  Sigrid devolvió las filas. Los desempates de las cascadas (`exactas[0]`,
  `en_res[0]`) pasan a ser deterministas. **Es un cambio de conducta
  observable** en presupuestos con varias hojas candidatas: se hace a
  propósito, se prueba (R19) y se anota en el informe.

El docstring de `resolver_postventa` pasa a decir «partida **hoja activa**» y
remite a `#regla-p5`. La cascada (exacto → empieza por → código en la
descripción → nombre) **se conserva**: R18 solo exige que el paso exacto
mande y que ninguna etapa mire nodos que no sean hojas activas.

`application/services/partida_catalog.py` **no se toca** (es copia cerrada de
`partes-persistencia`): se usa su `partidas_hoja`, no se modifica.

### 3.5. `application/pipelines/registro_pipeline.py`

- **Docstring de módulo**: el paso 1 deja de decir «CAPÍTULO» y dice
  «partida»; el paso 7 remite a `#regla-conflicto`; se añade un **paso 7 bis**
  para la capacidad, con remisión a `#regla-capacidad`.
- **`_destino_postventa`**: el docstring pierde la palabra «capítulo»; la
  variable local `capitulo` pasa a `partida`; si `resolver_postventa` no
  devuelve nada, el motivo sigue siendo el de «no casa con ninguna partida
  de …» (texto adaptado). Como el resolver ya solo mira hojas activas, el
  motivo de R16 se emite aquí: si el nodo devuelto **no** es hoja activa
  —que tras T9 solo puede ocurrir por un override manual del front—, se
  devuelve `MOTIVO_PARTIDA_PV_NO_HOJA`.
- **`setattr(pf, "capitulo_postventa", …)`**: el nombre del atributo del
  preflight **se conserva** aunque ya no sea un capítulo. Cambiarlo rompería
  el contrato HTTP que el front lee (`capitulo_postventa` en la respuesta de
  `/api/registro/preflight`) y §1 dice que el front no se toca. Se documenta
  el desajuste de nombre en el propio código y se propone su renombrado
  coordinado como feature aparte.
- **Paso 7 (conflictos de pisado)**: no cambia su forma. Cambia lo que
  `criterio_choque` responde, y eso ya vive en `reglas_porcentajes.py`.
- **Paso 7 bis (capacidad), nuevo**: dentro del mismo bucle por parte, tras
  construir `por_clave`, se agrupan las acciones pendientes por
  `recurso_ide`, se llama a `evaluar_capacidad` y, si hay sobrecarga, se
  añade un `Conflicto` con `motivo="sobrecarga"`. Se añaden **después** de
  los de pisado del mismo parte (R30: pisado primero).
- **Paso 10 (borrado)**: la deduplicación por `ide` de R13 **se queda**
  (defensiva) y se le añade la salvaguarda de R32: un conflicto confirmado
  solo emite sus borrados si **al menos uno** de sus `registros` sobrevive a
  `bloqueadas`, es decir, si de verdad se va a escribir el sustituto.

  ```python
  escribibles = {a.registro_id for a in a_escribir}
  for c in pf.conflictos:
      if c.clave not in pisar:
          continue
      if not (set(c.registros) & escribibles):
          continue          # R32: no se borra sin escribir el sustituto
      for ls in c.lineas:   # vacío en los conflictos de sobrecarga (R29)
          ...
  ```

  Nótese que el bucle de borrado se ejecuta **después** de calcular
  `a_escribir`, que es donde ya está hoy: no hace falta mover nada.
- **`_cat`**: su filtro (`n.es_hoja and n.activa`) ya es el universo bueno.
  No cambia; lo que se alinea con él es el resolver (§3.4). R17 se prueba
  comparando los dos conjuntos, no reescribiendo `_cat`.
- **`omitidas` de `ejecutar`**: se le añaden los registros bloqueados por un
  conflicto de sobrecarga sin confirmar, con su motivo (R28, §1.1).

### 3.6. `domain/models/registro_models.py`

- **Docstring de módulo**: la frase «La identidad de la línea en el parte es
  recurso + mes + código» remite a `#regla-conflicto` (hoy además es falsa:
  falta la partida).
- **`Conflicto`**: campos nuevos, **todos con valor por defecto** para que un
  cliente que los ignore siga funcionando (R33):

  ```python
  motivo: str = "pisado"          # pisado | sobrecarga
  suma_existente: float = 0.0     # jornada ya ocupada que se ha contado
  suma_total: float = 0.0         # suma_existente + nueva_can
  exceso: float = 0.0             # suma_total - 1, redondeado a 4 decimales
  ```

  Su docstring explica los dos tipos y deja escrito que **un conflicto de
  sobrecarga nunca lleva `lineas`**: `lineas` es «lo que se borraría», y una
  sobrecarga no borra nada. Las líneas que sí ha contado viajan en
  `contexto`, que ya existe y ya es informativo.
- No se añade ningún dataclass nuevo al dominio: el detalle numérico lo
  produce una función pura de `application` (§4.2) y el pipeline lo copia a
  estos cuatro campos.

### 3.7. `interface_adapters/api/app.py` del transfer

**No cambia.** Serializa los conflictos con `asdict(c)`, así que los campos
nuevos viajan solos. Es la razón por la que el mecanismo de conflicto era la
vía barata: el contrato no se toca (R33).

### 3.8. `tests/test_pipeline_offline.py`

Es la red de seguridad de T3 y hasta ahora no se ha tocado. **Con la Regla A
sí cambia de resultado** y hay que revisarlo en T10:

- `test_preflight_detecta_conflicto` construye una línea previa con
  `paride = 0` y una acción cuya partida se resuelve a `80001`: con la
  partida dentro de la identidad **deja de haber conflicto**.
- La aserción `c.clave == "200|202607|5|80001"` sigue siendo válida como
  clave, pero puede dejar de haber conflicto que la lleve.

Cada aserción que se toque **se justifica por escrito** en
`progress/impl_F-002.md`, una a una: es una feature de rigor crítico y ese
fichero es la prueba de que T3 no cambió conducta.

## 4. Clases y funciones — firmas y capa

### 4.1. Identidad (Regla A) — capa **application**

`services/dedicacion-transfer/application/services/reglas_porcentajes.py`

```python
CAMPOS_CLAVE: tuple[str, ...] = ("recurso", "periodo", "hora", "paride")
IMPLICITOS_DEL_PARTE: frozenset[str] = frozenset({"periodo"})

def campos_identidad() -> tuple[str, ...]:
    """Campos que deciden si dos líneas del parte son la MISMA línea.
    Los cuatro, siempre (D2, 2026-08-19). Ver ARCHITECTURE #regla-conflicto."""

def clave_conflicto(accion: AccionLinea) -> str: ...
def criterio_choque(existente: LineaSigrid, accion: AccionLinea, *,
                    mias: set[str]) -> bool: ...
```

Sin I/O, sin `settings`, sin cliente. La clave y el criterio siguen saliendo
de `CAMPOS_CLAVE`, así que R14 se mantiene tal cual: tocar la tupla mueve las
dos cosas. Y ahora, además, **coinciden**: la asimetría que la v1 tuvo que
aceptar (clave con `paride`, criterio sin él) desaparece, y con ella el hueco
por donde entraba R13.

### 4.2. Capacidad (Regla B) — capa **application**, mismo módulo

```python
class Capacidad(NamedTuple):
    existente: float      # jornada ya ocupada que cuenta
    nueva: float          # jornada que vamos a añadir
    total: float          # existente + nueva
    exceso: float         # total - LIMITE_CAPACIDAD (puede ser negativo)
    sobrecarga: bool      # exceso > EPSILON_CAPACIDAD
    contadas: tuple[LineaSigrid, ...]   # las existentes que ha sumado

def es_linea_mensual(linea: LineaSigrid) -> bool:
    """True si el código de hora empieza por M, sea cual sea (R24)."""

def evaluar_capacidad(
    existentes: list[LineaSigrid],
    nuevas: list[AccionLinea],
    *, mias: set[str], pisadas: set[int],
) -> Capacidad:
    """Jornada del recurso en un parte. NO decide qué se escribe: informa."""

def clave_sobrecarga(accion: AccionLinea) -> str:
    """`sobrecarga:{recurso}|{periodo}`, derivada de los mismos lectores
    que `clave_conflicto`, para que no puedan divergir (R27)."""
```

`evaluar_capacidad` suma de `existentes` las líneas que cumplen **las tres**
condiciones: son mensuales (`es_linea_mensual`), su `ide` **no** está en
`pisadas`, y su `synckey` **no** está en `mias`. De `nuevas` suma los `can`.
`can` a `None` vale 0, como en el resto del módulo.

**Por qué una `NamedTuple` de `application` y no un dataclass del dominio.**
Es un cálculo intermedio, no un concepto que el dominio tenga que conocer: lo
que el dominio publica es el `Conflicto`. Meterlo en `domain/` obligaría a
que el dominio conociera el concepto de «línea que se va a pisar», que es del
proceso de registro, no del parte.

**Por qué no es un método de `ReglasPorcentajes`.** `ReglasPorcentajes`
decide **línea a línea**; la capacidad es una propiedad **del conjunto** de
líneas de un recurso en un parte, y necesita datos que la clase no tiene
(las líneas previas de Sigrid). Mezclarlas obligaría a inyectar el cliente en
las reglas, que hoy son puras.

### 4.3. La tolerancia, y por qué ese número

```python
LIMITE_CAPACIDAD: float = 1.0

#: Tolerancia de la comparación de jornada. Es la MISMA que usa el cuadrante
#: en dedicacion-api/domain/estados.py (_EPSILON = Decimal("0.005") sobre
#: escala 0-100), convertida a la escala 0-1 de Sigrid: 0.005 / 100.
#: NO es un número redondo por elección: si se cambia, el front y Sigrid
#: discrepan en el último decimal y un cuadrante que la API da por OK se
#: convierte aquí en una sobrecarga fantasma.
EPSILON_CAPACIDAD: float = 0.00005
```

Sobre el uso de `float` y no `Decimal`: toda la escala del transfer es
`float` (P3: `can = round(porcentaje, 4)`) y meter `Decimal` aquí sola sería
una isla. No hace falta: `asignacion.porcentaje` es `Numeric(6,2)` sobre
0–100, así que dividido entre 100 tiene **como mucho cuatro decimales** y
`round(x, 4)` es exacto. La épsilon no está absorbiendo error de redondeo de
negocio —no lo hay—, sino la representación binaria (~1e-16) y la alineación
con la regla del cuadrante.

### 4.4. El motivo, corto a propósito

```python
MOTIVO_SOBRECARGA = (
    "sobrecarga: el trabajador sumaría {total:.2%} en el parte "
    "(ya tiene {existente:.2%} en {n} línea(s) M*, se añade {nueva:.2%}); "
    "confirma para escribirlo igualmente"
)
```

Cabe holgadamente en los 300 caracteres a los que la API trunca
`sigrid_motivo` (§1.1) y dice las cuatro cifras que el humano necesita.

## 5. Cómo interactúan la Regla A y la Regla B

Esto es lo delicado de la feature y por eso va en su propia sección.

**5.1. Una línea que pisa no se cuenta dos veces.** Si nuestra línea sustituye
a una existente (misma identidad), la existente sale del cómputo y entra la
nueva. Por eso `evaluar_capacidad` recibe `pisadas`: el conjunto de `ide` de
las líneas que aparecen en algún `Conflicto` de pisado de ese recurso.

**5.2. La suma se calcula suponiendo que todos los pisados se confirman**
(R31). Es la única hipótesis segura: cualquier otra combinación escribe
**estrictamente menos**, porque una confirmación denegada bloquea la línea
pendiente y deja la existente intacta. Si con todos los pisados confirmados
no hay sobrecarga, no puede haberla con menos. Y al revés, si el humano
deniega el pisado, la línea no se escribe: no podemos estar causando una
sobrecarga con algo que no escribimos.

> Corolario que conviene tener escrito: **la Regla B no detecta sobrecargas
> preexistentes** en las que no participamos. Si un parte ya tiene 1,4 de un
> trabajador y nosotros no escribimos nada suyo, no avisa. Es correcto —no
> somos un auditor del parte— y es diagnosticable con la consulta C3.

**5.3. Las líneas nuestras de esta ejecución no distorsionan la suma.** Ya se
excluyen del choque por `synckey in mias`; se excluyen igual del sumatorio.
Y una línea nuestra de una ejecución **anterior** (`ya_registrado`, paso 6)
sí cuenta como ocupación existente, y **solo una vez**: su acción ya no está
entre las pendientes, así que no entra por el otro lado.

**5.4. Un recurso puede tener pisado y sobrecarga a la vez.** Se le enseñan
**los dos conflictos**, el de pisado primero (R30), porque es el que explica
qué se borra; el de sobrecarga después, porque su cifra ya presupone que el
pisado ocurre. Sus claves no colisionan: la de pisado es
`{recurso}|{periodo}|{hora}|{paride}` y la de sobrecarga
`sobrecarga:{recurso}|{periodo}`, y ninguna clave de pisado puede empezar por
`sobrecarga:` porque su primer campo es un entero. Confirmar uno **no**
confirma el otro, y para escribir hacen falta los dos.

**5.5. Y por ahí es por donde se podía perder dato.** Si el humano confirma
el pisado pero no la sobrecarga, hoy el pipeline **borraría** la línea vieja y
**no escribiría** la nueva, porque el borrado se emite por conflicto
confirmado y la escritura se bloquea por registro. Eso es pérdida de dato de
Administración, y es la vía por la que la Regla B podía reabrir el defecto de
R13 por otro lado. Se cierra con R32: un conflicto confirmado solo emite sus
borrados si alguno de sus registros llega a escribirse. **Este es el
requisito más importante de la feature después de la propia Regla A.**

**5.6. R13 en sí deja de ser alcanzable por su ruta original.** Dos líneas
pendientes con partidas distintas ya no pueden chocar con la misma línea
existente, porque la partida entra en la identidad. La deduplicación por
`ide` se queda como salvaguarda y su test se reexpresa en T12: en lugar de
construir el escenario imposible, se inyectan dos conflictos que comparten
`hmores.ide` y se comprueba que solo sale un `DELETE`. El test que sí se
conserva tal cual es el control positivo («dos líneas distintas se borran las
dos»). El escenario viejo se reconvierte en el test de R21 + R25: esas dos
líneas ahora **no** chocan y, si su suma pasa de 1, producen **una
sobrecarga**.

## 6. SQL

**Esta feature no añade SQL de producción.** Ni consultas nuevas al cliente
de escritura, ni entradas en `services/dedicacion-api/config/config.yaml`, ni
DDL de PostgreSQL, ni ficheros `NN_nombre.sql`.

La Regla B se calcula sobre datos que el pipeline **ya lee**:
`lineas_del_parte(hmoide, resides)` devuelve hoy todas las líneas del parte
de esos recursos, con cualquier código de hora, y ya se usa para los
conflictos. No hay ni una lectura más contra Sigrid.

Las consultas C1–C5 de `requirements.md` §3 son de un solo uso, de solo
lectura, y las lanza el humano. No se versionan como consultas del servicio.

## 7. Ficheros que NO se tocan (y por qué tientan)

| Fichero | Por qué no |
|---|---|
| `application/services/partida_catalog.py` | **Copia de `partes-persistencia`** (lista cerrada de `CLAUDE.md`). Ya expone `partidas_hoja()` y `es_hoja`: se usa, no se modifica. Tocarlo obligaría a avisar de lo mismo en el repositorio `partes`. |
| `application/services/partida_matcher.py`, `text_match.py` | Ídem. `normalize_code` **no** quita ceros a la izquierda y así debe seguir: es lo que hace que `0656` y `656` sean códigos distintos (R18). |
| `infrastructure/sigrid/sigrid_write_client.py` | El SQL y el mapeo de campos son correctos. Las dos reglas cambian **qué** se escribe y qué se borra, no cómo. `lineas_del_parte` ya devuelve lo que la Regla B necesita. |
| `interface_adapters/api/app.py` del transfer | El contrato HTTP no cambia (R33). |
| `services/dedicacion-api/**` | No evalúa reglas de registro. El efecto de §1.1 se produce **sin** tocarlo. |
| `services/dedicacion-front/**` | Sin lógica de negocio. El coste está en §8. |
| `harness/**`, `CHECKPOINTS.md` | Esta feature no mejora el arnés. |
| `.env` de cualquier servicio | Prohibido por `CLAUDE.md`. `OBRA_PRUEBAS_FORZAR` sigue a `true`. |

## 8. Qué se pierde por no darle un tipo propio al conflicto

La decisión del humano es reutilizar el mecanismo de conflicto. Es la
correcta —evita tocar dos servicios más para una regla que aún no ha visto
datos reales—, pero no es gratis, y quien la revise tiene derecho a saber qué
paga:

1. **El texto que ve el humano está escrito para un pisado.** El front pinta
   `Pisar {código} de {nombre}: se borran {lista} y se escribe {n} %`. En una
   sobrecarga la lista está vacía, así que se lee «se borran  y se escribe
   40 %», y la casilla dice **Pisar** cuando confirmar no pisa nada. Es feo y
   es engañoso en el peor sitio posible.
2. **Las cifras que justifican el aviso no se enseñan.** `suma_existente`,
   `suma_total` y `exceso` viajan en la respuesta, pero el front no los lee;
   tampoco pinta `contexto`. El humano ve que hay algo que confirmar, no
   *por qué*.
3. **El resumen mezcla los dos tipos.** `resumen.conflictos` cuenta pisados y
   sobrecargas juntos, así que nadie puede decir cuántos de cada.
4. **El modelo mental que induce es el equivocado.** Alguien que confirme
   pensando que «pisa» creerá que está sustituyendo una línea cuando está
   aceptando pasar del 100 %.

Lo que **no** se pierde: la seguridad. Sin confirmación no se escribe nada
(R28), confirmar una sobrecarga no borra nada (R29), y confirmar un pisado
que no llega a escribirse no borra nada (R32). El contrato degrada con
elegancia: un front que ignore los campos nuevos sigue funcionando exactamente
igual que hoy (R33).

**Propuesta para el humano, no incluida en F-002:** una feature de front
—`dedicacion-front/static/js/app.js`, función `pintarModalPreflight`— que lea
`c.motivo` y pinte un bloque distinto para la sobrecarga, con sus cuatro
cifras y las líneas de `contexto`. Es pequeña (una rama en un `forEach`) y
convierte los cuatro puntos de arriba en cero. Va al backlog, no aquí.

## 9. Riesgos y decisiones

**Riesgo 1 — la feature cambia lo que se BORRA en Sigrid.** Sigue siendo el
riesgo principal, y ahora en los dos sentidos: la Regla A hace que se borre
**menos** (una línea con otra partida deja de ser candidata) y R32 hace que
se borre menos aún. Mitigación: `OBRA_PRUEBAS_FORZAR` a `true` durante toda
la feature; ninguna tarea escribe en producción; la verificación real va
contra la obra `0404` con la marca `PRUEBA-PORC` y **requiere autorización
expresa del humano para esa acción concreta** (T14).

**Riesgo 2 — el efecto de la Regla A el primer día.** Al dejar de chocar las
líneas con otra partida, un parte que hoy produciría un conflicto pasará a
producir una escritura directa. Si la partida que resuelve el automático no
es la que Administración usó a mano, aparecerán dos líneas donde antes había
una sustitución. **Ese es justamente el caso que la Regla B tiene que
cazar**, y por eso las dos van en la misma feature y no en dos. La medida de
cuánto va a pasar la da la consulta C3 (`requirements.md` §3), que el humano
puede lanzar antes de T14.

**Riesgo 3 — la sobrecarga preexistente.** §5.2: no se detecta lo que ya
estaba mal si no participamos. Consciente y documentado; no se amplía el
alcance para arreglarlo.

**Riesgo 4 — cobertura y mutación.** La carga lógica nueva se concentra a
propósito en `reglas_porcentajes.py` (funciones puras, sin I/O), donde
matarla es barato; en `registro_pipeline.py` quedan la llamada, el bucle de
agrupación y dos guardas. Es la misma decisión que en la Fase 1, y ahí dio
9/9 mutantes muertos.

**Riesgo 5 — `test_pipeline_offline.py` cambia de resultado.** Era la red de
seguridad de T3 y ahora hay que tocarlo (§3.8). Mitigación: se toca **en
T10**, después de que los tests nuevos de R20/R21 fijen la conducta buena, y
cada aserción modificada se justifica por escrito.

**Decisión — la Regla B se queda en el transfer.** §1. La alternativa
(llevarla a la API, que ve el cuadrante completo) se descarta porque la API
no ve las líneas que Administración mete a mano en el parte, que son
exactamente las que provocan la sobrecarga.

**Decisión — un conflicto de sobrecarga nunca lleva `lineas`.** Es lo que
hace que R29 sea cierto *por construcción* y no por una comprobación que
alguien pueda quitar: el bucle de borrado itera `c.lineas`, y si está vacío
no hay nada que borrar. Las líneas contadas van a `contexto`.

**Decisión — se retiran los enunciados de P4/P5 (T8) antes de implementar la
conducta (T9–T12).** Durante esas tres tareas, `ARCHITECTURE.md` describe una
regla que el código todavía no cumple. Es aceptable y deliberado:
`ARCHITECTURE.md` es normativo (dice lo que **debe** ser), los tests que
fijan la conducta nueva llegan con su código, y `init.sh` se mantiene en
verde en todo momento. La alternativa —retirar los enunciados al final—
dejaría el repositorio con cinco versiones de la regla durante más tiempo,
que es justo lo que la feature viene a matar.

**Alternativa descartada — un tipo propio de aviso (`Sobrecarga`) en el
contrato.** Es lo técnicamente limpio y lo que evita los cuatro costes de §8,
pero obliga a tocar `dedicacion-transfer`, `dedicacion-api` y
`dedicacion-front` a la vez, con una regla que todavía no ha visto un dato
real. Se descarta por decisión expresa del humano y se propone como feature
posterior de front (§8).

**Alternativa descartada — omitir en silencio las líneas que sobrecargan.**
Sería la opción segura, pero convierte un aviso en una desaparición: el
cuadrante diría 100 % y Sigrid no tendría la línea. La decisión del humano es
avisar y dejar confirmar, que es lo que se diseña.

**Alternativa descartada — dejar `campos_identidad(destino)` con el
parámetro.** §3.3.
</content>
</invoke>
