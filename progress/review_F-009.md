<!-- progress/review_F-009.md -->
# F-009 · Review

**Veredicto: APPROVED**

Feature `sdd: false`, rigor **`estandar`** declarado en `harness/features.json`.
Rama revisada: `feature/F-009-higiene-coverage-gitignore` (HEAD `d9d3e68`).
Todo lo que sigue lo ha ejecutado el reviewer; nada se da por bueno leyendo el
informe del implementer.

---

## 1. Nivel de rigor y puertas que exige

`rigor: "estandar"` → C1–C3, C3 bis, C5, tests trazables (C4), **fase RED**,
**cobertura de las líneas cambiadas** y **campaña de mutación**.

Resolución de las tres puertas de C4 bis, **verificada leyendo el código**, no
el informe:

| Puerta | Resultado | Verificación independiente |
|---|---|---|
| Fase RED | **[x] cumplida** | Reproducida por el reviewer (§3) |
| Cobertura | **N/A justificado** | `harness/alcance.py:112-124` + recálculo (§2) |
| Mutación | **N/A justificado, 0 mutantes legítimos** | Recálculo + campaña reejecutada + prueba de control (§2) |

---

## 2. Verificación independiente del alcance, la cobertura y la mutación

### 2.1 El alcance es genuinamente cero

`harness/alcance.py` decide el alcance con `es_produccion(ruta)` (líneas
112-124): exige que la ruta **termine en `.py`** y que ningún segmento sea
`tests`, `specs`, `progress` ni `docs`. El diff de F-009 (`git diff dev..HEAD
--name-status`) son doce entradas y **ni una sola es `.py`**:

```
D  .coverage            M  .gitignore              M  BACKLOG.md
D  coverage.json        M  harness/features.json   M  progress/current.md
A  progress/impl_F-009.md    A  progress/mutacion_F-009.md
D  services/dedicacion-api/.coverage       D  services/dedicacion-api/coverage.json
D  services/dedicacion-transfer/.coverage  D  services/dedicacion-transfer/coverage.json
```

`git diff dev..HEAD --name-only | grep '\.py$'` → **vacío**.

Recálculo con la herramienta, no con el informe:

```
$ python -c "from harness.alcance import alcance_de_feature; a=alcance_de_feature('F-009'); print(a.descripcion())"
F-009: 0 fichero(s), 0 línea(s) de producción
       (origen rama, c43a12fd730805a107985e0962a8134e8cbc1678..feature/F-009-higiene-coverage-gitignore)
```

Las referencias (`c43a12f..rama`) coinciden **exactamente** con las declaradas
en `progress/mutacion_F-009.md`. Alcance 0 confirmado.

### 2.2 El N/A de cobertura es el que produce el código

`harness/cobertura.py:202-206` corta con `if not alcance.lineas: return _na(...)`
y el texto impreso es literalmente el que sale del portero:
`PUERTA COBERTURA: N/A (F-009 no cambia líneas Python de producción frente a
dev)`. No es una etiqueta escrita a mano: es la rama `_na` del código.

### 2.3 Campaña de mutación: reejecutada, no creída

El informe declara «Tiempo total 0.0 s», **inferior a 5 minutos**, así que
CHECKPOINTS C4 bis obliga a reejecutar. Hecho, con salida fuera de `progress/`:

```
$ python -m harness.mutacion --feature F-009 --salida <scratchpad>/mutacion_F-009_reviewer.md
F-009: 0 fichero(s), 0 línea(s) de producción (origen rama, c43a12f..feature/F-009-...)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
EXIT=0
```

Totales idénticos a `progress/mutacion_F-009.md` (0/0/0/0). `git status`
después: **vacío** — el árbol quedó limpio y no se pisó el informe del
implementer.

### 2.4 Prueba de control del cero (el generador no está roto)

Un «0 mutantes» puede significar dos cosas y el recálculo no las distingue.
`reviewer.md` manda ejecutar `generar_mutantes` **ignorando la exclusión de
alcance**; aquí esa prueba sale vacua, porque el diff no contiene **ningún**
`.py` que mutar (ni excluido ni incluido). Se hizo por tanto el control
equivalente: lanzar el generador sobre un `.py` real del repositorio.

```
$ python -c "... generar_mutantes(fuente, todas_las_lineas, 'harness/alcance.py') ..."
CONTROL: mutantes generables en harness/alcance.py = 32
ejemplos: [(47,'booleano'), (48,'booleano'), (51,'booleano')]
```

El generador **funciona**. El cero de F-009 es legítimo: no hay Python que
mutar, no que la herramienta esté muda. (Ver la propuesta de automejora §9.2.)

---

## 3. Fase RED: reproducida por el reviewer

El entregable de F-009 no es código, así que la RED no es un test unitario sino
la traza del comportamiento defectuoso. El informe la trae (§3, ANTES/DESPUÉS).
El reviewer la ha **reproducido en su mitad verde**, que es la comprobable hoy:

```
$ bash harness/init.sh          # ejecución 1 → EXIT=0
$ git status --porcelain        → vacío
$ bash harness/init.sh          # ejecución 2 → EXIT=0
$ git status --porcelain        → vacío
```

Y, lo que de verdad prueba el arreglo, con la **caché de suites invalidada**
para forzar que las tres suites se ejecuten de verdad y reescriban los seis
artefactos:

```
$ rm -f .arnes_cache/suite_api.ok .arnes_cache/suite_transfer.ok
$ bash harness/init.sh
  11 passed in 0.16s                                    (raíz)
  21 passed in 0.12s   [OK] servicio api: pytest en verde
   4 passed in 0.36s   [OK] servicio transfer: pytest en verde
  [OK] PUERTA COBERTURA: N/A (...)
  ENTORNO LISTO. Puedes trabajar.        EXIT=0
$ git status --porcelain        → vacío
```

Antes de F-009 esta misma ejecución dejaba cuatro ficheros modificados. **El
árbol ya no se ensucia solo ni cuando las suites corren de verdad.**

Se comprobó además que la parte ANTES sigue siendo cierta estructuralmente:
`git ls-tree` sobre las ramas de F-002 y F-003 muestra los seis ficheros
**todavía trackeados** allí (§7), que es el estado del que se partía.

---

## 4. Que no se ha roto nada (punto 1 del encargo)

### 4.1 La puerta de cobertura sigue midiendo, y lee del disco

Lectura del código: `harness/cobertura.py:124-131` (`_leer_cobertura`) usa
`ruta.is_file()` / `ruta.read_text()`, y `coberturas_de_servicios` (134-149)
compone `Path(raiz)/servicio.ruta/nombre_informe`. **Ni una llamada a git** en
ese camino: git solo interviene para calcular el alcance.

Comprobado en ejecución, con los seis ficheros ya fuera del índice, y con una
prueba de contraste que el informe del implementer no hacía:

```
A) $ python -m harness.cobertura --base 1f3e837
   PUERTA COBERTURA: 28.9% de 2562 líneas cambiadas cubiertas (741/2562, umbral 80%)

B) $ mv services/dedicacion-api/coverage.json ...bak     # escondido del DISCO
   $ python -m harness.cobertura --base 1f3e837
   PUERTA COBERTURA: 24.9% de 2556 líneas cambiadas cubiertas (636/2556, umbral 80%)

C) $ (restaurado)  → 28.9% de 2562 (741/2562)     # vuelve al valor de A
```

El número **cambia al esconder el fichero del disco y vuelve al restaurarlo**:
la puerta lee del árbol de trabajo, fusiona raíz + servicios y calcula. El
28,9 % del implementer es reproducible al dígito. El `EXIT=1` de esa medición
es correcto (28,9 % < 80 %) y es artificial —base forzada al commit inicial—:
la puerta real de F-009 es el N/A de §2.2, en verde. Además, mover esos
ficheros **no ensució `git status`**, prueba lateral de que están ignorados.

### 4.2 La caché de suites sigue funcionando, en sus dos direcciones

`init.sh` §7 bis (líneas 358-375) valida la caché contra el disco: hash del
árbol + `git status` limpio en la ruta + `[ -f "$RUTA/coverage.json" ]`. Se
observaron los dos estados en ejecuciones reales:

- **Caché fría** (`.ok` borrados): las dos suites se ejecutan de verdad
  (`21 passed`, `4 passed`) y los `.ok` se regeneran.
- **Caché caliente** (ejecución siguiente): `pytest en verde (caché: árbol sin
  cambios desde el último verde)` para api y transfer.

El ciclo frío→caliente **se cierra ahora, y antes no podía cerrarse nunca**:
la propia ejecución ensuciaba la ruta del servicio y `SUCIO_SRV` invalidaba la
caché en la siguiente pasada. Mejora colateral real, confirmada.

### 4.3 Suites ejecutadas a mano, con el intérprete de cada servicio

Porque en las ejecuciones de portero con caché caliente esas líneas venían de
caché:

```
services/dedicacion-api    .venv/Scripts/python -m pytest -q  → 21 passed in 0.14s
services/dedicacion-transfer .venv/Scripts/python -m pytest -q →  4 passed in 0.37s
raíz                        python -m pytest tests -q         → 11 passed in 6.98s
```

**36 tests, todos en verde**, exactamente los números de la sección
«Evidencias». `ruff` sobre `dedicacion-api` con el intérprete de la raíz: 34
avisos, subconjunto de los 164 de deuda previa; F-009 no toca ningún `.py`, así
que ninguno es suyo.

---

## 5. Dónde se colocaron las reglas en `.gitignore` (punto 2 del encargo)

Las dos reglas van **dentro del bloque `# >>> ARNES-BASE ... >>>`**, junto a
`.arnes_cache/`, no en «Propias del proyecto». **La elección es la correcta**,
y no por estética: es lo que hace que la propagación funcione.

Verificado ejecutando el instalador contra un repositorio de juguete en el
scratchpad (instalación limpia, caso A):

```
[GITIGNORE] 11 regla(s) anadida(s): .env, .arnes_cache/, .coverage, coverage.json,
            *.pdf, *.docx, *.xlsx, *.pptx, *.doc, *.xls, *.ppt
```

y el `.gitignore` producido es **idéntico línea a línea, y en el mismo orden**,
al que tiene hoy `porcentajes`. Local y plantilla no divergen: es la condición
para que la siguiente actualización del arnés no genere ruido ni duplique
reglas.

Si hubieran ido en «Propias del proyecto», el instalador —que compara reglas ya
presentes en `$yaTiene` (`instalar_arnes.ps1:194-195`)— no las duplicaría, pero
el bloque gestionado local quedaría **por debajo** de la plantilla y cada
repositorio tendría que redescubrir el arreglo. El criterio aplicado («lo
produce el arnés → bloque del arnés») es el correcto: `.coverage` y
`coverage.json` los fabrica `init.sh` §7 y §7 bis, igual que `.arnes_cache/`.

Dos decisiones menores, también verificadas:

- **Patrones sin anclar.** `git check-ignore -v` sobre los ocho caminos
  posibles: los seis reales y los dos de `dedicacion-front`, todos resueltos
  por `.gitignore:4` y `.gitignore:5`. Un servicio nuevo queda cubierto de
  antemano.
- **Bloque local sin comentarios.** Correcto y deliberado:
  `instalar_arnes.ps1:200-203` descarta del cálculo de `$faltan` toda línea que
  empiece por `#`, de modo que una instalación real nunca escribe los
  comentarios del fragmento. El bloque local es fiel a la salida del
  instalador.

---

## 6. Propagación a `arnes-base` (punto 3 del encargo, criterio 4)

**Hecha y correcta.** Commit local `c5b258d` en
`C:\Users\pgris\PycharmProjects\arnes-base`, sin push y sin PR. Toca **dos
ficheros y solo dos**:

- `arnes-base/harness/gitignore.arnes` (+10): las dos reglas con su comentario.
- `.gitignore` del propio `arnes-base` (+1): tenía `.coverage` pero **no**
  `coverage.json` — el mismo agujero en el repositorio que publica la regla.

Verificado que `harness/gitignore.arnes` **no se copia** al proyecto destino
(`instalar_arnes.ps1:32`, `$Excluidos`): es plantilla del instalador, no
payload. Coherente con que `porcentajes` no lo tenga.

### ¿Es suficiente para que un proyecto nuevo no herede el problema?

**Sí**, y está comprobado ejecutando el instalador, no leído: el caso A de §5
demuestra que una instalación limpia inserta ya las dos reglas.

### ¿Rompe algo del instalador? No — y su límite está bien documentado

Caso B ejecutado por el reviewer: proyecto que **ya tiene** el bloque (con las
reglas antiguas), `-Modo actualizar`:

```
[GITIGNORE] el bloque del arnes ya estaba
--- .gitignore resultante: SIN las dos reglas nuevas ---
```

Confirma al pie de la letra el límite que el informe describe en §6 y que el
mensaje de `c5b258d` deja escrito: `instalar_arnes.ps1:205` trata el bloque
como **todo-o-nada** en cuanto encuentra la marca, ni siquiera en modo
actualizar. La mejora llega sola a instalaciones nuevas; **los repositorios ya
instalados necesitan las dos líneas a mano**, como se ha hecho aquí. Diagnóstico
correcto, honesto y fuera del alcance de F-009: se recomienda como feature
propia de `arnes-base` (§9.1).

### El trabajo ajeno de la otra sesión: intacto

`c5b258d` incluye únicamente esos dos ficheros. Al empezar la review,
`arnes-base` mostraba `M arnes-base/harness/mutacion.py` y
`?? arnes-base/tests/test_mutacion_prueba_de_verdad.py`, ambos **fuera** del
commit. Durante la review esa otra sesión avanzó por su cuenta y su HEAD pasó a
`b7dce9d` («1.6.0 (2/4)»), commiteando su test; `c5b258d` **sigue en la
historia**, sin reescribir, y el fragmento conserva sus dos reglas (líneas 15 y
16 de `gitignore.arnes`). Nada suyo se tocó, se commiteó ni se revisó. No se
hizo push en ninguno de los dos repositorios.

---

## 7. El aviso del merge (punto 4 del encargo)

**El informe lo deja escrito y el comando es correcto.** `progress/impl_F-009.md`
§7 da al líder:

```bash
git ls-files | grep -E '(^|/)(\.coverage|coverage\.json)$'
```

Ejecutado ahora en la rama: **sale vacío**, como debe. La regex está anclada
(`(^|/)` y `$`), así que no produce falsos positivos con rutas que contengan la
palabra «coverage».

Reproducidas por el reviewer las dos comprobaciones que lo motivan:

- `git ls-tree -r --name-only` sobre `feature/F-002-...` y `feature/F-003-...`:
  ambas siguen con **los seis ficheros trackeados**.
- `git merge-tree --write-tree` (solo lectura, sin cambiar de rama):
  - con **F-002**: `CONFLICT (modify/delete): coverage.json deleted in F-009 and
    modified in F-002. Version F-002 left in tree.` → **el fichero volvería** si
    nadie interviene.
  - con **F-003**: los seis borrados se aplican limpios; los conflictos son de
    `BACKLOG.md` y `progress/current.md`, gestión normal del arnés.

El informe explica también la resolución correcta del `modify/delete`
(`git rm coverage.json`, nunca `git checkout --theirs`) y recomienda bajar `dev`
a las ramas de F-002 y F-003 en cuanto F-009 esté integrada. Suficiente para el
líder.

Observación menor: `progress/current.md` §«Aviso para el merge» cita la versión
corta `git ls-files | grep coverage` (sin anclar). Conviene que el líder lo
alinee con la regex del informe al cerrar la sesión. No bloquea.

---

## 8. CHECKPOINTS

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con **exit 0**. Ejecutado cuatro veces por
      el reviewer (dos consecutivas, una con caché invalidada, una final).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`. El portero lo confirma línea a línea.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-009']` (validado por `init.sh`).
- [x] Rama actual `feature/F-009-higiene-coverage-gitignore`, nunca `main`.
- [x] `progress/current.md` describe solo la sesión activa de F-009. Su línea 6
      («Implementer en marcha») va un paso por detrás del estado real, pero ese
      fichero lo mantiene el líder y no afecta al trabajo revisado.
- [x] No hay features pasadas a `done` en esta rama; `history.md` sin deuda.

### C3 — El código respeta arquitectura y convenciones

- [x] Arquitectura hexagonal: **N/A justificado — la feature no toca ni una
      línea de código.** El diff son un `.gitignore`, seis borrados del índice y
      documentos de `progress/`. No hay dominio, aplicación ni infraestructura
      que evaluar, y por tanto ninguna frontera que pueda violarse.
- [x] Primera línea con la ruta relativa: los dos ficheros nuevos la llevan
      (`<!-- progress/impl_F-009.md -->`, `<!-- progress/mutacion_F-009.md -->`).
- [x] Sin `print()`, sin TODOs, sin secretos, sin dependencias nuevas. Barrido
      del reviewer sobre el diff textual con los patrones `password|passwd|
      contrase|secret|api[_-]?key|token|BEGIN (RSA|PRIVATE)|Server=|Data Source=|
      pwd=`, IPv4 y GUID: **cero coincidencias**. Ninguna dependencia añadida.
- [x] Las tres trampas de dominio: **N/A justificado**. No hay conversión de
      escala de porcentajes, ni consulta que agrupe postventa, ni escritura
      nueva contra Sigrid: el diff no contiene código ejecutable. `.env`
      intacto (`[OK] Ningún .env versionado`).

### C3 bis — Documentos que entran de fuera

**N/A justificado**: la feature no añade ni modifica ningún fichero de
`docs/referencia/` (`git diff dev..HEAD --name-status` no incluye ninguna ruta
bajo `docs/`). No hay PDF ni ofimática en el diff. El barrido de datos
sensibles se ejecutó igualmente sobre todo el diff textual (C3), con resultado
limpio.

### C4 — La verificación es real

- [x] Cada criterio `acceptance` tiene su evidencia y **todas se comprobaron de
      nuevo por el reviewer** (tabla del §8 bis). No hay tests `test_f009_rN_*`
      y **no debe haberlos**: N/A justificado — los cuatro criterios son
      propiedades del repositorio (índice de git, limpieza del árbol, exit code
      del portero, commit en otro repositorio), verificables con comandos
      reproducibles, no con aserciones de una suite. Escribir un test unitario
      que hiciera `git ls-files` sería un test del repositorio, no del código.
- [x] Los unit tests no tocan red ni BBDD: las 36 pruebas existentes siguen en
      verde y no se ha añadido ni modificado ninguna.
- [x] Verificaciones `MANUAL (humano)`: **ninguna pendiente**, y así consta en
      `current.md` y en §8 del informe. Correcto: F-009 no toca Sigrid, ni la
      BBDD, ni ningún `.env`.

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "estandar"`, valor válido de `harness/rigor.json`.
- [x] **Fase RED**: presente con traza real en §3 del informe y **reproducida
      por el reviewer** (§3 de este documento), incluida la ejecución con caché
      invalidada que es donde el fallo se manifestaba en toda su extensión.
- [x] **Cobertura**: `N/A` **con motivo impreso** por el propio `init.sh`, y el
      motivo verificado en el código (`alcance.py:112-124` +
      `cobertura.py:202-206`), no aceptado de palabra.
- [x] **Mutación**: existe `progress/mutacion_F-009.md` generado por la
      herramienta; alcance y nº de mutantes **recalculados** por el reviewer
      (0 y 0), referencias del diff coincidentes.
- [x] **Los muertos están comprobados**: «Tiempo total 0.0 s» < 5 min, así que
      la campaña se **reejecutó** con `--salida` al scratchpad. Totales
      idénticos y árbol limpio después. Añadida la prueba de control del cero
      (§2.4): el generador produce 32 mutantes sobre un `.py` real, luego el
      cero de F-009 es ausencia de Python, no herramienta rota.
- [x] Supervivientes: **ninguno**, trivialmente. Ninguna sección `PENDIENTE`.
- [x] Sección **«Evidencias»** presente con los cuatro números. Todos
      contrastados: 36 tests (21+4+11, reejecutados a mano), cobertura N/A con
      motivo, 0 mutantes / 0 supervivientes, tiempos de suite.
- [x] Ningún punto marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A sin nada que justificar**: el repositorio no declara
`harness/rutas_sensibles.json` (solo existe `rutas_sensibles.ejemplo.json`),
que es el caso mayoritario previsto por CHECKPOINTS. El portero no señaló
ninguna ruta sensible tocada.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: **N/A justificado por `sdd: false`** (nota de cabecera de
      CHECKPOINTS). El formato mínimo exigido sí se cumple: `0aa68ed F-009:
      arranca la feature`, `44a04e3 F-009 T1: los artefactos de cobertura dejan
      de versionarse`, `d9d3e68 F-009 T2: informe de implementacion y campana de
      mutacion`.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status
      --porcelain` **vacío** tras cada una de las cuatro ejecuciones del portero
      y al terminar la review. Los repositorios de juguete del reviewer viven en
      el scratchpad, fuera del proyecto.
- [x] `features.json` refleja el estado real: `F-009` en `in_progress`, como
      corresponde hasta que el líder aplique este veredicto. `BACKLOG.md` al día
      (validado por `init.sh`).

## 8 bis — Trazabilidad: criterio `acceptance` → evidencia verificada

| # | Criterio `acceptance` | Cómo lo verificó el reviewer | Resultado |
|---|---|---|---|
| 1 | `.coverage` y `coverage.json` (raíz y los tres servicios) en `.gitignore` y fuera del índice | `git check-ignore -v` sobre los 8 caminos (incluido `dedicacion-front`) + `git ls-files \| grep -E '(^\|/)(\.coverage\|coverage\.json)$'` | Los 8 ignorados por `.gitignore:4-5`; `git ls-files` **vacío**; los 6 ficheros **siguen en disco** |
| 2 | Dos `init.sh` seguidos → `git status --porcelain` vacío | Dos ejecuciones consecutivas **y** una tercera con la caché invalidada (peor caso: las 3 suites corren de verdad) | **Vacío las tres veces** |
| 3 | `bash harness/init.sh` en verde | Ejecutado 4 veces tal cual | **EXIT=0** siempre; único aviso, la deuda previa de `ruff` (164) y `front` sin tests |
| 4 | Portado a `arnes-base`, o escrito por qué no | Inspección de `c5b258d` + instalador ejecutado contra 2 repos de juguete (casos A y B) | Portado; instalación limpia produce el bloque **idéntico**; límite del modo actualizar reproducido y documentado |

---

## 9. Automejora y recomendaciones (propuestas, no aplicadas)

### 9.1 Para `arnes-base` — dos features propias, ninguna de F-009

1. **El bloque del `.gitignore` debe ser reconciliable.** Confirmado por el
   reviewer: `instalar_arnes.ps1:205` es todo-o-nada y ningún repositorio ya
   instalado recibirá jamás una regla nueva del bloque, ni con `-Modo
   actualizar`. Afecta por igual a cualquier regla futura, no solo a esta. El
   arreglo (releer el bloque, calcular las reglas de plantilla que faltan y
   añadirlas respetando lo escrito a mano) es un cambio de comportamiento del
   instalador y merece su feature con pruebas.
2. **El payload arrastra basura al proyecto destino.** Verificado en la
   instalación de juguete: se copian `harness/__pycache__/*.pyc`,
   `tests/__pycache__/*.pyc`, `.pytest_cache/` y `.ruff_cache/` — 13 de los 56
   ficheros «nuevos». Un proyecto recién instalado nace con basura de la máquina
   del instalador. Sugerencia: añadir esos patrones a `$Excluidos`.

Ambas quedaron ya anotadas por el implementer; el reviewer las confirma de
forma independiente y respalda que **no** se hicieran dentro de F-009.

### 9.2 Para `.claude/agents/reviewer.md` (portable a `arnes-base`)

La prueba de control del «cero mutantes» está redactada suponiendo que el diff
contiene algún `.py` que la exclusión de alcance pudo descartar: *«ejecuta
`generar_mutantes` sobre los ficheros del diff ignorando la exclusión de
alcance»*. Cuando el diff **no contiene ningún `.py`** —como aquí— esa prueba es
vacua: ignorar la exclusión sigue dando 0 y no distingue el cero legítimo del
generador roto. Propuesta de redacción añadida:

> Si el diff no contiene ningún fichero `.py`, la prueba de control se hace
> sobre un `.py` cualquiera del repositorio: si el generador produce mutantes
> ahí, el cero de la feature es legítimo.

### 9.3 Para `CHECKPOINTS.md` (portable a `arnes-base`)

C4 bis contempla dos formas de fase RED: la traza del test que falla, y romper
en copia aislada lo que el test vigila. Falta la tercera, que es la que aplica a
las features de higiene de repositorio o de entorno, donde el defecto no vive en
el código. Propuesta:

> Si la feature corrige un comportamiento del repositorio o del entorno y no del
> código, la fase RED se demuestra con la **traza reproducible del
> comportamiento defectuoso antes del arreglo y de su ausencia después**,
> ejecutada en las condiciones donde se manifiesta (aquí: con la caché de
> suites invalidada).

---

## 10. Cambios requeridos

**Ninguno.** Los cuatro criterios `acceptance` se cumplen y están verificados de
forma independiente. Los dos apuntes menores —`current.md` con el estado un paso
por detrás y con la versión sin anclar del comando de comprobación— son del
ámbito del líder al cerrar la sesión, no del implementer, y no condicionan el
veredicto.
