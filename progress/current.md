<!-- progress/current.md -->
# Trabajo en curso

**F-002 · «Fijar las reglas P4 y P5: postventa y conflicto tienen dos
versiones»** (`rigor: critico`, `sdd: true`), rama
`feature/F-002-reglas-postventa-conflicto`.

Estado: **spec escrita, pendiente de aprobación del humano y de la respuesta
de Administración.** No se ha tocado ni una línea de código.

## Lo que se ha escrito

`specs/F-002-reglas-postventa-conflicto/` con los tres ficheros:

- `requirements.md` — 19 requisitos EARS (R1–R14 independientes de
  Administración; R15–R19 bloqueados) y la sección **«Decisiones abiertas que
  solo puede cerrar Administración»** con las preguntas cerradas y las cinco
  consultas de lectura contra Sigrid.
- `design.md` — fuente única en `docs/ARCHITECTURE.md` con ancla por regla,
  extracción del criterio de choque a una función pura, y la lista exacta de
  qué texto se sustituye en cada fichero. Sin SQL de producción.
- `tasks.md` — T1–T6 **se pueden hacer ya**; T7–T17 quedan tras una PARADA
  explícita hasta que vuelva la respuesta de Administración.

## Pendiente de decisión del humano

### 1. Aprobar la spec

Antes de lanzar al implementer. En particular, dos decisiones de diseño que
conviene mirar:

- `clave_conflicto` deja de ser property de `AccionLinea` (domain) y pasa a
  función de `application/services/reglas_porcentajes.py`, para que la clave
  y el filtro de choque no puedan divergir (es lo que hoy pasa).
- La fase 1 retira duplicación de P1–P3 **antes** de tener la respuesta de
  Administración, para que no aparezca una sexta versión mientras se espera.

### 2. Llevar a Administración estas preguntas (son el nudo de F-002)

**D1.1 — Código de la obra de postventa.** El README, el `.env.example` y
`settings.py` dicen `POSTV2`; el docstring de `reglas_porcentajes.py:15` dice
`postventa-2`.

> ¿Cuál es el **código exacto** —campo *Código* de la ficha de obra— de la
> obra donde queréis ver imputada la dedicación de postventa? ¿Hay una sola o
> varias?

Si el código está mal, **todas** las líneas de postventa se omiten en
silencio: el registro termina «OK» con la postventa fuera.

**D1.2 — ¿Partida (hoja) o capítulo (nodo con hijos)?** README y
`partida_resolver.py` dicen *partida*; `reglas_porcentajes.py:15-17` y
`registro_pipeline.py:6-8` dicen *capítulo*. El código de hoy **no elige**:
`partida_resolver.py:54` llama `hojas` a una lista que no filtra `es_hoja`,
mientras `registro_pipeline.py:296` sí filtra para el desplegable del front.
Automático y manual pueden apuntar a universos distintos.

> La dedicación por postventa de la obra **0707**, ¿va al **capítulo** «0707»
> o a una **partida concreta** colgada de él? Si es partida, ¿cuál, con su
> código exacto? Y si una obra original no tiene línea en el presupuesto de
> postventa, ¿no se escribe, o se escribe sin imputar (`paride = 0`)?

**D2 — Qué cuenta como conflicto en la obra normal.** El README (`:14-15`,
`:31-33`) y **el código** (`registro_pipeline.py:246-253`) dicen que choca
aunque la partida sea distinta; los docstrings
(`reglas_porcentajes.py:11-13`, `registro_pipeline.py:16-17`) exigen la misma
partida.

> En el parte mensual de una obra, ¿puede un mismo trabajador tener más de
> una línea `M*` en el mismo mes con partidas distintas?
> (a) No, como mucho una: si ya hay, se sustituye.
> (b) Sí, sin límite.
> (c) Sí, pero la suma de sus cantidades no puede pasar de 1.

Consecuencia con números: encargado a 9.000 €/mes con una línea previa de
9.000 € puesta a mano y un 40 % nuestro de 3.600 €. Con la versión del código
se **borra** el apunte manual; con la de los docstrings el parte queda con
**12.600 €** de un trabajador que cuesta 9.000. Los dos riesgos son reales y
de signo opuesto: por eso no se decide desde el código.

**Si la respuesta a D2 es (c)**, ninguna de las dos versiones sirve y hay que
volver a proponer diseño: sería una regla nueva (validar la suma), posible
candidata a vivir en la API, que es quien ve el cuadrante completo.

### 3. Consultas de lectura contra Sigrid — NO ejecutadas

Cinco consultas listas en `requirements.md` §2 (C1–C5), para
`POST /api/sql/read`, base `ruesma`, con tablas y campos reales de
`azure-apps/sigrid_tablas.md`:

- **C1** — qué obra existe con `POSTV2` / `postventa-2` / «POSTVENT».
- **C2** — árbol de `obrparpar` de la obra de postventa con `n_hijos`:
  distingue capítulo de partida.
- **C3** — últimas líneas `M*` reales del parte de postventa con su `paride`
  y si esa partida tiene hijos. **Es la corroboración más fuerte de D1.2**:
  dice lo que Administración hace de verdad.
- **C4** — agregado: casos reales de un recurso con más de una línea `M*` en
  el mismo parte, con `n_partidas` y `suma_can`. Cierra D2 con datos.
- **C5** — detalle de los partes que salgan de C4.

Las lanza el humano cuando decida. Recordatorios: `max_rows` explícito (el
defecto son 200 y trunca en silencio), `truncated: true` significa respuesta
incompleta, y el balanceador corta a los **230 s**. El volcado va a
`progress/sigrid_F-002.md`.

## Estado del repositorio

- Rama activa: `feature/F-002-reglas-postventa-conflicto`, creada desde
  `dev`. Sin commits todavía de esta sesión.
- `bash harness/init.sh` → ENTORNO LISTO en la última ejecución conocida.
  Avisos vivos: 164 de ruff (deuda previa) y `dedicacion-front` sin
  directorio de tests.
- F-001 cerrada y mergeada a `dev` (`c1faf05`). Sin PR abierto.

## Lo que sabemos y no conviene volver a descubrir

- **La puerta de cobertura sigue sin estrenarse con datos reales.** F-002 es
  la primera feature que toca producción: será la que la pruebe de verdad.
- **`ruff` no está instalado en el venv de `dedicacion-api`**: para lintar ese
  servicio hay que usar el intérprete de la raíz.
- El portero ensucia `git status` en cada ejecución porque los ficheros de
  cobertura están versionados. Es F-009.
- **Contradicción número tres, derivada** (la encontró el spec-author, no
  estaba en el backlog): hoy `clave_conflicto` incluye `paride` siempre
  (versión B) mientras el filtro de choque no lo compara en obra normal
  (versión A). Dos líneas pendientes con distinta partida chocando contra la
  misma línea existente generan **dos `DELETE` del mismo `hmores.ide`**. Es
  R13/R14 de la spec y hay que arreglarlo vaya como vaya D2.
