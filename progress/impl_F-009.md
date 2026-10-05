<!-- progress/impl_F-009.md -->
# F-009 · Higiene: los artefactos de cobertura no se versionan

Implementación de la feature `F-009` (sdd=false, rigor `estandar`) contra sus
cuatro criterios `acceptance` de `harness/features.json`.

Rama: `feature/F-009-higiene-coverage-gitignore`.
Commits: `44a04e3` (este repositorio) y `c5b258d` (en `arnes-base`).
Veredicto propio: **los cuatro criterios se cumplen**, con la salvedad
documentada en §6 sobre el alcance real de la propagación.

---

## 1. Qué cambió

### En `porcentajes` (commit `44a04e3`)

| Fichero | Cambio |
|---|---|
| `.gitignore` | +2 líneas: `.coverage` y `coverage.json`, dentro del bloque `ARNES-BASE` |
| `.coverage` | fuera del índice (`git rm --cached`), sigue en disco |
| `coverage.json` | fuera del índice, sigue en disco |
| `services/dedicacion-api/.coverage` | fuera del índice, sigue en disco |
| `services/dedicacion-api/coverage.json` | fuera del índice, sigue en disco |
| `services/dedicacion-transfer/.coverage` | fuera del índice, sigue en disco |
| `services/dedicacion-transfer/coverage.json` | fuera del índice, sigue en disco |

**Ni una línea de código de producción.** No se tocó `.env`, ni
`harness/features.json`, ni `progress/current.md` (los lleva el líder).

### En `arnes-base` (commit `c5b258d`, repositorio aparte)

| Fichero | Cambio |
|---|---|
| `arnes-base/harness/gitignore.arnes` | +10 líneas: las dos reglas más el comentario que las explica |
| `.gitignore` (el del propio repositorio) | +1 línea: `coverage.json` |

Detalle y justificación en §6.

---

## 2. Decisión de diseño: en qué sección del `.gitignore` va la regla

Las reglas van en el **bloque `ARNES-BASE`**, no en «Propias del proyecto».
El criterio es *quién produce el fichero*:

- `.coverage` y `coverage.json` los genera **el propio arnés**:
  `harness/init.sh` §7 ejecuta `coverage run` / `coverage json` en la raíz, y
  §7 bis lo repite dentro de cada servicio. Sin arnés instalado, estos
  ficheros no existen. Son de la misma familia que `.arnes_cache/`, que ya
  estaba en ese bloque: artefacto que el portero fabrica al arrancar.
- «Propias del proyecto» es para lo que trae este monorepo por su cuenta
  (`.venv/`, `.idea/`, `__pycache__/`, `.pytest_cache/`).

**Consecuencia para la propagación**, que es lo que hacía que la elección
importara: si la regla viviera en la sección propia, el arreglo se quedaría
aquí y cada repositorio con arnés tendría que redescubrir el mismo fallo, y
además el bloque local divergiría del fragmento `gitignore.arnes` de
`arnes-base`, que es la plantilla. Puestas en el bloque gestionado, local y
plantilla dicen exactamente lo mismo — verificado en §6: el bloque que produce
hoy una instalación limpia es **idéntico**, línea a línea, al que tiene este
repositorio.

Dos decisiones menores:

- **Patrones sin anclar** (`coverage.json`, no `/coverage.json` ni
  `services/*/coverage.json`): así dos líneas cubren la raíz y los tres
  servicios sin enumerar rutas, y un servicio nuevo queda cubierto el día que
  se cree. Comprobado con `git check-ignore -v` sobre los ocho caminos
  posibles, incluidos los de `dedicacion-front` (que hoy no tiene tests y por
  tanto no genera nada, pero queda cubierto de antemano).
- **El bloque local se deja sin comentarios**, aunque el fragmento de
  `arnes-base` sí los lleve. No es un descuido: el instalador filtra las
  líneas de comentario al construir el bloque (`instalar_arnes.ps1`, el
  cálculo de `$faltan` descarta lo que empieza por `#`), así que un bloque con
  comentarios no es lo que produce una instalación real. Se mantiene fiel a la
  salida del instalador para que ambos coincidan.

---

## 3. Fase RED — el árbol se ensuciaba solo

El comportamiento a corregir no es un requisito funcional, así que no se
demuestra con un test unitario sino con la pareja de comandos que define el
criterio 2. Lo que sigue es salida real, no resumida.

### ANTES del arreglo

Primera ejecución del portero, recién empezada la sesión:

```
$ bash harness/init.sh
[OK] ENTORNO LISTO. Puedes trabajar.        (exit 0)

$ git status --porcelain
 M .coverage
 M coverage.json
```

Solo aparecen los dos de la raíz porque la caché de suites evitó ejecutar las
de los servicios. Para que se vea el alcance completo se invalidó la caché
(`rm -f .arnes_cache/suite_api.ok .arnes_cache/suite_transfer.ok`) y se
ejecutó de nuevo:

```
$ bash harness/init.sh
[OK] servicio api (services/dedicacion-api): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
[OK] ENTORNO LISTO. Puedes trabajar.        (exit 0)

$ git status --porcelain
 M .coverage
 M coverage.json
 M services/dedicacion-api/coverage.json
 M services/dedicacion-transfer/coverage.json
```

**El criterio 2 fallaba de forma reproducible**: tras dos ejecuciones
seguidas, `git status --porcelain` devolvía cuatro ficheros modificados.

Un efecto secundario que conviene dejar escrito porque agravaba el problema:
al terminar sucio el árbol de cada servicio, la **caché de suites se
invalidaba a sí misma**. `init.sh` §7 bis solo da por buena la caché si
`git status --porcelain -- <ruta>` sale vacío, y la propia ejecución anterior
lo ensuciaba. El arnés se estaba pagando ejecuciones de suite que su caché
tenía derecho a ahorrarse.

### DESPUÉS del arreglo

Dos ejecuciones seguidas, sin tocar nada entre medias:

```
$ bash harness/init.sh          # ejecución 1
[OK] PUERTA COBERTURA: N/A (F-009 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-009-higiene-coverage-gitignore
ENTORNO LISTO. Puedes trabajar.
EXIT=0

$ git status --porcelain
                                 <- vacío

$ bash harness/init.sh          # ejecución 2, inmediatamente después
[OK] servicio api (services/dedicacion-api): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde (caché: árbol sin cambios desde el último verde)
ENTORNO LISTO. Puedes trabajar.
EXIT=0

$ git status --porcelain
                                 <- vacío
```

Criterios 2 y 3 cumplidos. Y de propina se ve la mejora colateral: en la
ejecución 2 la caché de suites **sí** actúa para los dos servicios, cosa que
antes no llegaba a ocurrir nunca dos veces seguidas.

---

## 4. Que no se ha roto nada: comprobado, no supuesto

Los dos mecanismos que consumen estos ficheros siguen funcionando porque los
ficheros **se siguen generando en disco**; lo único que cambia es que git ya
no los sigue. Ambos se verificaron ejecutándolos.

### 4.1 La puerta de cobertura lee del disco

Lectura del código primero: `harness/cobertura.py` obtiene los informes con
`_leer_cobertura(ruta)` → `ruta.is_file()` / `ruta.read_text()`, sobre
`Path(opciones.cov)` para la raíz y `Path(raiz)/servicio.ruta/nombre_informe`
para cada servicio (líneas 124-149 y 211-215). No hay ni una llamada a git en
ese camino: git solo se usa para calcular el *alcance* (qué líneas cambiaron),
nunca para leer la cobertura.

Y comprobado en ejecución. Como en F-009 la puerta sale `N/A` (no hay líneas
de producción, ver §5), se la forzó a producir un número real apuntándola a
una base antigua, con los ficheros **ya fuera del índice**:

```
$ python -m harness.cobertura --base 1f3e837 --config harness/rigor.json
PUERTA COBERTURA: 28.9% de 2562 líneas cambiadas cubiertas (741/2562, umbral 80%, nivel estandar)
EXIT=1
```

La puerta lee, fusiona los informes de la raíz y de los dos servicios, y
calcula. El `EXIT=1` es lo correcto aquí (28,9 % < 80 %) y **no afecta al
veredicto de F-009**: es una medición forzada contra una base artificial
—el commit inicial del repositorio— cuyo único fin es demostrar que la lectura
de disco sigue viva. La puerta real de la feature es la de §3, en verde.

### 4.2 La caché de suites sigue validando `coverage.json` en el árbol

`init.sh` §7 bis solo aprovecha la caché si, además de coincidir el hash del
árbol, existe `[ -f "$RUTA/coverage.json" ]`. Se probó borrando ese fichero de
**un solo** servicio, para tener el contraste dentro de la misma ejecución:

```
$ rm -f services/dedicacion-api/coverage.json
$ git status --porcelain
                                 <- vacío: el fichero está ignorado, borrarlo no ensucia nada

$ bash harness/init.sh
[OK] servicio api (services/dedicacion-api): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde (caché: árbol sin cambios desde el último verde)

$ ls -la services/dedicacion-api/coverage.json
-rw-r--r-- 1 pgris 197121 22271 Aug 19 15:42 services/dedicacion-api/coverage.json
$ git status --porcelain
                                 <- vacío
```

El servicio al que le faltaba el informe **reejecutó su suite** y el otro usó
la caché: la condición se sigue evaluando contra el disco y sigue haciendo su
trabajo. El fichero se regeneró y el árbol siguió limpio.

---

## 5. Las dos puertas de rigor `estandar`, y por qué salen a cero

El nivel `estandar` de `harness/rigor.json` exige fase RED, cobertura de
líneas cambiadas y campaña de mutación. Las dos últimas salen **`N/A` /
vacías, y es legítimo**, no un atajo. El motivo está en el código:

`harness/alcance.py` decide qué entra en el alcance de una feature con
`es_produccion(ruta)`, que exige **dos** cosas: que la ruta termine en `.py`
y que ningún segmento sea `tests`, `specs`, `progress` ni `docs`
(`DIRECTORIOS_EXCLUIDOS`). El diff de F-009 frente a `dev` son un `.gitignore`
y seis borrados del índice: **ningún `.py`**. Por tanto
`filtrar_produccion()` devuelve el mapa vacío, y:

- `harness/cobertura.py` (línea 202) corta con
  `if not alcance.lineas: return _na(...)` → `PUERTA COBERTURA: N/A (F-009 no
  cambia líneas Python de producción frente a dev)`.
- `harness/mutacion.py` (línea 736) corta con
  `Sin líneas de producción en el alcance: nada que mutar.`

Es el mismo `N/A` que se documentó en F-001 y por la misma razón de diseño: el
arnés mide Python de producción, y esta feature no toca ninguno. Medir la
cobertura de un `.gitignore` no significa nada.

La campaña se lanzó igualmente, para dejar el informe generado y no un hueco:

```
$ python -m harness.mutacion --feature F-009
F-009: 0 fichero(s), 0 línea(s) de producción (origen rama, c43a12f..feature/F-009-higiene-coverage-gitignore)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-009.md
EXIT=0
```

**Supervivientes: ninguno**, trivialmente, porque no hubo mutantes que
generar. No hay ningún superviviente que analizar y ninguna sección queda
`PENDIENTE`.

La fase RED sí aplica y sí está demostrada, por la vía que tiene sentido para
esta feature: la traza reproducible de §3.

---

## 6. Propagación a `arnes-base` (criterio 4)

**Sí procede, y está hecha**: commit local `c5b258d` en
`C:\Users\pgris\PycharmProjects\arnes-base`. Sin `git push` y sin PR.

### Qué se cambió allí

1. `arnes-base/harness/gitignore.arnes` — el fragmento que el instalador
   inserta en el `.gitignore` de cada proyecto. Se añaden `.coverage` y
   `coverage.json` junto a `.arnes_cache/`, con el comentario que explica por
   qué.
2. `.gitignore` del propio repositorio `arnes-base` — tenía `.coverage` pero
   **no** `coverage.json`: el mismo agujero, en el repositorio que publica la
   regla. Una línea.

### El hallazgo de fondo: la regla existía, pero como paso manual

`GUIA_INSTALACION.md` ya lo pedía, dos veces:

- línea 329, «Qué hacer al actualizar desde 1.1.0»: *«Añade `coverage.json` y
  `.coverage` a `.gitignore`»*.
- línea 452, «Qué hacer al actualizar desde 1.2.x»: *«añade los
  `coverage.json` de los servicios a `.gitignore` (`services/*/coverage.json`)»*.

Es decir: `arnes-base` conocía el problema desde la 1.2.0 y lo resolvió
pidiéndoselo a un humano. En este repositorio ese paso no se dio, que es
exactamente lo que le pasa a un paso manual. El arreglo lo convierte en
mecanismo, y de paso los patrones sin anclar hacen innecesario el
`services/*/coverage.json` que pedía la guía.

No se editó `GUIA_INSTALACION.md`: `arnes-base` tiene ahora mismo un trabajo
en curso de otra sesión (`ENCARGO_1.5.3_mutacion_fiable.md`, con
`harness/mutacion.py` modificado y un test sin trackear en el árbol) y la guía
se organiza por versiones. Redactar una entrada de versión ahí es decisión del
mantenedor de la 1.5.3, no mía. **El trabajo ajeno se dejó intacto**: se
añadieron al commit los dos ficheros uno a uno y `git status` sigue mostrando
`M arnes-base/harness/mutacion.py` y el test sin trackear, sin tocar.

### Verificación del instalador (ejecutado, no supuesto)

Se ejecutó `instalar_arnes.ps1` contra dos repositorios de juguete en el
scratchpad, ya borrados.

**Caso A — proyecto sin bloque (instalación limpia):**

```
[GITIGNORE] 11 regla(s) anadida(s): .env, .arnes_cache/, .coverage, coverage.json, *.pdf, *.docx, *.xlsx, *.pptx, *.doc, *.xls, *.ppt
```

y el `.gitignore` resultante es **idéntico** al bloque que ahora tiene este
repositorio, en el mismo orden. La decisión de §2 queda confirmada: local y
plantilla no divergen.

**Caso B — proyecto que YA tiene el bloque, en modo actualizar:**

```
[GITIGNORE] el bloque del arnes ya estaba
```

y el `.gitignore` sale **sin cambios**: las dos reglas nuevas no entran.

### Límite conocido, y es importante para el líder

`instalar_arnes.ps1` (~línea 205) trata el bloque del `.gitignore` como
**una sola decisión de todo-o-nada**: en cuanto encuentra la marca
`>>> ARNES-BASE`, imprime «el bloque del arnes ya estaba» y no añade nada,
**ni siquiera con `-Modo actualizar`**. Es aditivo e idempotente, pero no
reconciliable.

Consecuencia práctica: la mejora del fragmento llegará sola a las
**instalaciones nuevas**, pero **ningún repositorio ya instalado la recibirá
al actualizar** — tendrá que añadir las dos líneas a mano, igual que ha hecho
esta feature aquí. Ése es el «el instalador arrastra el problema por otra
vía» que había que detectar: el canal de propagación del `.gitignore` está
roto para todo lo que no sea una instalación desde cero, y afectará por igual
a cualquier regla futura que se añada al bloque.

Arreglarlo (hacer el bloque reconciliable: releerlo, detectar qué reglas de la
plantilla faltan y añadirlas respetando lo que el proyecto haya escrito a
mano) es un cambio de comportamiento del instalador que merece su propia
feature en `arnes-base`, con sus pruebas. **No se hizo aquí** por dos motivos:
excede el «cambio mínimo» del encargo, y tocar el instalador mientras otra
sesión trabaja en la 1.5.3 es pedir un conflicto. Queda escrito en el mensaje
del commit `c5b258d` y recomendado como feature aparte.

Segundo hallazgo menor, del mismo tipo, visible en las trazas del instalador:
el payload arrastra basura al proyecto destino
(`[NUEVO] harness/__pycache__/*.pyc`, `.pytest_cache/`, `.ruff_cache/`). No se
tocó: no es F-009, pero conviene que el líder lo sepa.

---

## 7. AVISO PARA EL LÍDER: el merge puede reintroducir los ficheros

**Esto no es una precaución teórica: está comprobado.** Las ramas
`feature/F-002-reglas-postventa-conflicto` y
`feature/F-003-orm-columnas-sigrid` siguen teniendo los seis ficheros
trackeados, y F-002 además tiene `coverage.json` modificado respecto a `dev`.

Simulación de los merges con `git merge-tree` (solo lectura, sin cambiar de
rama):

```
$ git merge-tree --write-tree --name-only feature/F-009-... feature/F-002-...
CONFLICT (modify/delete): coverage.json deleted in feature/F-009-higiene-coverage-gitignore
  and modified in feature/F-002-reglas-postventa-conflicto.
  Version feature/F-002-reglas-postventa-conflicto of coverage.json left in tree.
CONFLICT (content): Merge conflict in progress/current.md
```

Traducido: **si nadie interviene, `coverage.json` vuelve al árbol** — git
resuelve el `modify/delete` conservando la versión de F-002. Con F-003, en
cambio, los seis borrados se aplican limpiamente (sus conflictos son de
`BACKLOG.md` y `progress/current.md`, gestión normal del arnés).

### Qué debe ejecutar el líder tras CADA merge a `dev`

```bash
git ls-files | grep -E '(^|/)(\.coverage|coverage\.json)$'
```

**Debe salir vacío.** Si devuelve algo, el merge los ha reintroducido; se
corrige, fichero a fichero:

```bash
git rm --cached <cada fichero que haya salido>
git commit -m "Saca de nuevo del indice los artefactos de cobertura (F-009)"
```

Y en el conflicto `modify/delete` de F-002, cuando aparezca, la resolución es
`git rm coverage.json` (quedarse con el borrado de F-009), nunca
`git checkout --theirs`.

**Recomendación operativa**: en cuanto F-009 esté integrada en `dev`, traer
`dev` a las ramas de F-002 y F-003 antes de seguir trabajando en ellas. Así
heredan el `.gitignore` y el desversionado cuanto antes; si no, cada
`init.sh` que ejecuten sus implementers volverá a modificar los seis ficheros
y a fabricar conflictos nuevos.

---

## 8. Verificaciones MANUAL pendientes

Ninguna. Los cuatro criterios `acceptance` se comprueban con comandos
reproducibles, todos ejecutados y con su salida pegada arriba.

---

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **36, todos en verde**: 11 en la suite de la raíz, 21 en `dedicacion-api`, 4 en `dedicacion-transfer`. `dedicacion-front` no tiene suite (aviso conocido del portero, ajeno a esta feature). |
| **Cobertura de las líneas cambiadas** | **N/A legítimo**: `PUERTA COBERTURA: N/A (F-009 no cambia líneas Python de producción frente a dev)`. La feature no modifica ni una línea de Python; ver §5 con la lectura de `harness/alcance.py` que lo explica. Que la puerta sigue midiendo se demostró aparte: 28,9 % (741/2562) forzándola contra el commit inicial (§4.1). |
| **Mutantes generados y supervivientes** | **0 generados, 0 supervivientes**, por la misma razón: sin líneas de producción en el alcance no hay nada que mutar. Informe en `progress/mutacion_F-009.md`. Ningún superviviente que analizar. |
| **Tiempo de ejecución de la suite** | raíz 0,12–0,17 s · `dedicacion-api` 0,14–0,15 s · `dedicacion-transfer` 0,46–0,49 s (**≈0,8 s** las tres). |
| **Portero completo** | `bash harness/init.sh` → `ENTORNO LISTO. Puedes trabajar.`, **exit 0**, dos veces seguidas y con `git status --porcelain` vacío tras cada una. |

Avisos del portero no atribuibles a esta feature, sin cambios respecto al
inicio de la sesión: 164 de `ruff` (deuda previa, no bloquea) y `dedicacion-front`
sin directorio de tests.
