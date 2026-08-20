<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## 2026-08-19 · F-001 · Primera suite de tests de `dedicacion-api`: la regla del 100 %

Rama `feature/F-001-tests-estados-api` · `sdd: false` · rigor `estandar` ·
**APROBADO** por el reviewer · 5 commits locales (`5a1b54d` … `12be01e`).

**Qué cambió.** Tres ficheros nuevos bajo `services/dedicacion-api/tests/`
(`__init__.py`, `conftest.py` con el `sys.path.insert` en un único sitio, y
`test_estados.py` con 21 tests). **Cero ficheros de producción modificados**:
`domain/estados.py` se leyó, no se tocó.

**Qué se verificó (salida real).** `bash harness/init.sh` → ENTORNO LISTO,
exit 0, con `[OK] servicio api (services/dedicacion-api): pytest en verde` —
antes de F-001 esa línea era un AVISO de «sin directorio de tests». Suite: 21
passed en 0,10 s; `domain/estados.py` al 100 % (26/26 sentencias). Fase RED:
7 roturas deliberadas de `estados.py` en copia aislada, 7 cazadas; el
reviewer la reprodujo con los mutantes del generador real (16 muertos de 17,
y el único superviviente es el mutante equivalente que el implementer ya
había identificado y justificado por escrito). ruff sigue en los mismos 164
avisos de deuda previa; los ficheros nuevos salen limpios.

**Las dos puertas nuevas, verificadas de forma independiente.** Era la
primera vez que se ejercían en este repositorio. La puerta de cobertura salió
`N/A (F-001 no cambia líneas Python de producción frente a dev)` y la campaña
de mutación generó 0 mutantes. El reviewer no se fio del informe: leyó
`harness/alcance.py` (`DIRECTORIOS_EXCLUIDOS` incluye `tests` **como segmento
de ruta a cualquier profundidad**, pensado para monorepos) y
`harness/cobertura.py` (el `N/A` es una rama declarada que imprime su motivo,
distinta de aprobar en silencio), recalculó el alcance y añadió una prueba de
control. Conclusión: comportamiento correcto por diseño, no una puerta
esquivada. **La puerta de cobertura sigue sin estrenarse con datos reales**:
lo hará la primera feature que toque producción (F-002 o F-003).

**Decisiones tomadas.** `conftest.py` en vez de repetir el `sys.path.insert`
en cada test como hace el transfer. Dos casos de épsilon de más (99,995 % y
100,005 %) además de los que pedía el criterio: son los únicos que distinguen
`<=` de `<`, y así quedó demostrado al romper el código. Se cubrió también
`calcular_desviacion`, que el criterio no nombraba. Los 11 avisos de ruff que
introdujeron los ficheros nuevos se corrigieron en el acto (`7760080`), para
que la deuda previa no creciera con esta feature.

**Deuda que deja apuntada (declarada por ambos subagentes, no corregida).**
F-001 amplía de 4 a 6 los ficheros de cobertura versionados: añade
`services/dedicacion-api/.coverage` y `coverage.json`, siguiendo el
precedente de la raíz y del transfer. Ninguno está en `.gitignore`, así que
el portero ensucia `git status` cada vez que se ejecuta. Lo correcto es lo
contrario: ignorarlos y sacarlos del índice con `git rm --cached`. Como el
`.gitignore` lo deja el instalador del arnés, por la regla de propagación el
arreglo va también a `arnes-base`. Convertido en **F-009**.

**Propuestas de automejora del reviewer, pendientes de decisión del humano.**
(1) `CHECKPOINTS.md` C4 bis no dice qué hacer cuando *toda* la feature cae en
`DIRECTORIOS_EXCLUIDOS` (cobertura N/A y mutación 0 a la vez): propone hacer
regla explícita la mutación sobre el fichero que los tests nuevos cubren.
(2) `.claude/agents/reviewer.md`: cuando el alcance salga vacío, añadir como
paso el control positivo (generar mutantes del fichero de producción cubierto
y ejecutarlos contra la suite). (3) La caché del portero puede enseñar un
`[OK]` de un servicio sin que la suite se haya ejecutado en esa sesión: el
protocolo del reviewer debería obligar a lanzarla a mano. Las tres valen para
cualquier proyecto ⇒ van a `arnes-base`. Convertidas en **F-010**.

**Corrección menor anotada.** El «Cómo reproducirlo» del informe del
implementer manda `ruff` con el intérprete del venv del api, donde ruff no
está instalado. Con el de la raíz funciona.

Informes: `progress/impl_F-001.md`, `progress/review_F-001.md`,
`progress/mutacion_F-001.md`.

## 2026-08-19 · F-009 · Higiene: los artefactos de cobertura no se versionan

Rama `feature/F-009-higiene-coverage-gitignore` · `sdd: false` · rigor
`estandar` · **APROBADO** por el reviewer · 3 commits (`0aa68ed` … `d9d3e68`),
más `c5b258d` en el repositorio `arnes-base`.

**Qué cambió.** Los seis artefactos de cobertura versionados (`.coverage` y
`coverage.json` de la raíz, de `dedicacion-api` y de `dedicacion-transfer`)
salen del índice y entran en `.gitignore`. Ni una línea de Python tocada.

**Qué se verificó (salida real).** `git ls-files | grep coverage` no devuelve
nada. `bash harness/init.sh` ejecutado **dos veces seguidas** deja
`git status --porcelain` **vacío**, que era el criterio de aceptación central.
El portero sigue en verde y ni la puerta de cobertura ni la caché de suites se
resienten: las dos leen esos ficheros **del disco**, no de git, y los ficheros
se siguen generando.

**Por qué se hizo ahora.** Había estorbado tres veces en una sola tarde: en
F-001 se acabaron añadiendo dos artefactos más «por seguir el precedente»; en
F-002 y F-003 la campaña de mutación paralela —que exige árbol limpio— tuvo
que lanzarse con `--workers 1`; y el reviewer de F-003 llegó a interpretar el
árbol sucio como un posible rojo del portero.

**La propagación a `arnes-base`, que es lo más valioso.** El implementer no
copió la regla: encontró la causa. `GUIA_INSTALACION.md` ya mandaba añadir
`coverage.json` y `.coverage` al `.gitignore`, pero **como paso manual**, en
dos sitios distintos (al actualizar desde 1.1.0 y desde 1.2.x). En
`porcentajes` nadie lo hizo, que es exactamente lo que le pasa a un paso
manual. El commit `c5b258d` de `arnes-base` lo convierte en **mecanismo**: la
regla pasa al bloque gestionado por el instalador (`harness/gitignore.arnes`),
con patrones sin anclar para que cubran la raíz y cualquier servicio de un
monorepo. Ningún proyecto nuevo heredará el problema.

**Puertas.** Cobertura y mutación salieron **N/A justificado** (cero líneas de
Python de producción en el alcance), verificado por el reviewer leyendo
`harness/alcance.py:112-124` y recalculando, con prueba de control incluida.
La fase RED no podía ser un test unitario: fue la traza real de
`init.sh` + `git status` ensuciándose antes y saliendo limpio después, y el
reviewer la **reprodujo**.

**Aviso vivo para el líder.** Las ramas de F-002 y F-003 todavía tienen esos
seis ficheros trackeados y los modifican. Al mergearlas, git puede
**reintroducirlos**: hay que comprobar `git ls-files | grep coverage` después
de cada merge.

Informes: `progress/impl_F-009.md`, `progress/review_F-009.md`.

## 2026-08-20 · F-003 · Las columnas `sigrid_*` de `asignacion` no están en el ORM

Rama `feature/F-003-orm-columnas-sigrid` · `sdd: true` · rigor `critico` ·
**APROBADO** por el reviewer (2ª pasada) · mergeada a `dev` en `0499153`.

**Qué cambió.** `_ALTERS` —la lista de `ALTER TABLE` escrita a mano en
`application/registro_sigrid.py`— desaparece. Las seis columnas `sigrid_*`
pasan al ORM, que queda como **única fuente de verdad**, y el DDL
complementario se **deriva** de él en `infrastructure/db/esquema.py`,
ejecutado desde `main.py` junto a `create_all` y **fuera de `build_app`**.

**Efecto colateral deliberado y valioso:** construir la app ya no abre
conexión a PostgreSQL. Antes, el constructor de `RegistroSigrid` lanzaba el
DDL, así que importar la aplicación exigía base de datos: por eso el servicio
no podía tener tests de API. Ahora puede.

**Verificado (salida real).** 84 tests en el api (63 de F-003 + 21 de F-001),
cobertura de líneas cambiadas **94,4 %** (51/54), **14 mutantes y 0
supervivientes**. La primera campaña dejó **2 supervivientes reales** y el
implementer escribió los tests que faltaban hasta matarlos, en vez de
justificarlos. Fase RED real: **41 failed + 20 errors** antes de existir
`esquema.py`. ruff: 164 → 162.

**T8 · verificación MANUAL contra la base real, EJECUTADA el 2026-08-20.**
Es la que de verdad cerraba la feature, porque la base local tiene datos y las
seis columnas ya creadas a mano: el resultado correcto era que no pasara nada.

| Paso | Resultado real |
|---|---|
| Fotografía previa | 14 columnas, **30 filas** en `asignacion` |
| Primer arranque (`python main.py`) | `Esquema verificado en BBDD 'dedicacion': 0 sentencias DDL aplicadas` |
| Segundo arranque | `0 sentencias DDL aplicadas` ⇒ **idempotente** |
| Fotografía posterior | 14 columnas, **30 filas** — idénticas |

Ningún `EsquemaNoDerivable`, ningún dato tocado.

**Queda fuera (T8 bis):** la traza de extremo a extremo —que un registro real
deje `sigrid_estado='registrado'` con su `sigrid_parte_cod`— exige escribir en
Sigrid vía `dedicacion-transfer`. Los `UPDATE` están verificados
**compilados** contra el dialecto PostgreSQL, no ejecutados.

**Nota de proceso.** La 1ª review fue CHANGES_REQUESTED **por el rastro del
líder**, no por el código: `progress/current.md` describía la sesión anterior
y no listaba T8 con su comando, que es donde `CHECKPOINTS.md` C4 la exige. El
reviewer lo argumentó bien: si la feature se cierra con `current.md` diciendo
que no hay nada en curso, T8 es exactamente la verificación que nadie ejecuta
nunca.

Informes: `progress/impl_F-003.md`, `progress/review_F-003.md`,
`progress/mutacion_F-003.md`.

## 2026-08-20 · Retiradas F-007 y F-010 (se hacen en `arnes-base`)

Decisión del humano. Las dos eran mejoras del **arnés genérico**, no de este
proyecto, y se abordan directamente en el repositorio `arnes-base`:

- **F-007** · dos defectos del instalador: arrastra su propio `.pytest_cache/`
  y los `__pycache__/` del payload, y no copia el `.gitattributes`.
- **F-010** · cinco automejoras del protocolo detectadas revisando F-001 y
  F-002: `CHECKPOINTS.md` no contempla la review de una fase; el reviewer
  debería hacer control positivo cuando el alcance de mutación salga vacío;
  la caché del portero puede enseñar un `[OK]` sin ejecutar la suite; un
  superviviente declarado «equivalente» debería traer demostración
  **ejecutable** y el reviewer reproducirla; y quitar código defensivo para
  matar un mutante obliga a verificar el invariante **en quien construye el
  dato**.

**No se pierden**: quedan escritas aquí y en los informes de review que las
originaron (`progress/review_F-001.md` §10, `progress/review_F-002_fase1.md`
§10, `progress/review_F-002_fase2.md` §11). Quien las implemente en
`arnes-base` tiene ahí el razonamiento completo y el caso real que las motivó.

**Reordenado el backlog** en la misma decisión: **F-008 (despliegue en Azure)
sube a prioridad 3**, justo detrás de F-002, para poder hacer pruebas en un
entorno desplegado.

## 2026-08-20 · Dos defectos del arnés detectados al cerrar F-004 (van a `arnes-base`)

Salieron al quedar F-004 en `blocked` por un rojo de `harness/init.sh` que
**no tenía nada que ver con la feature**. El diagnóstico es del implementer de
F-004 (`progress/impl_F-004.md`) y lo confirmó el líder.

**1. `init.sh` confunde «no hay tests» con «los tests fallan».** Si el
directorio `tests/` de un servicio existe pero no contiene ningún test,
`pytest` termina con **código 5** («no tests ran»), y la sección 7 bis trata
cualquier salida distinta de 0 como rojo. El caso real: al cambiar de rama,
git se llevó los `.py` de `services/dedicacion-front/tests/` —que solo
existen en la rama de F-008— pero dejó el directorio con `__pycache__`
dentro, así que el árbol tenía un `tests/` **vacío de tests pero existente**.
Arreglo propuesto: tratar el código 5 como el aviso que ya existe («sin
directorio de tests»), no como fallo.

**2. La caché de suites cruza ramas, y eso es más grave.**
`.arnes_cache/suite_front.ok` guardaba el hash del árbol del front **de la
rama de F-008**, donde sí hay tests, y por eso el rojo estuvo camuflado un
tiempo dando un `[OK]` heredado de otra rama. Es exactamente el riesgo que ya
había señalado el reviewer de F-001 («la caché puede enseñar un `[OK]` sin
que la suite se haya ejecutado»), ahora con un caso real: **el portero puede
dar verde por una suite que se ejecutó en otro sitio.**

**Desbloqueo aplicado aquí** (no toca el arnés): borrar el residuo
`services/dedicacion-front/tests/` con solo `__pycache__` dentro, su
`.pytest_cache` y la entrada de caché `suite_front.ok`. `init.sh` vuelve a
**ENTORNO LISTO** y el front recupera su aviso legítimo de «sin directorio de
tests» —legítimo porque su suite vive en la rama de F-008, sin mergear—.

**El arreglo de fondo va a `arnes-base`**, junto a lo que se retiró con F-007
y F-010: los dos defectos son del arnés genérico y los sufrirá cualquier
proyecto que trabaje con varias ramas.

## 2026-08-20 · F-004 · README del monorepo y arranque local en orden

Rama `feature/F-004-readme-monorepo` · `sdd: false` · rigor `documental` ·
**APROBADO** por el reviewer · commits `605c2d9` (README + test) y `fed6f9b`
(informe).

**Qué cambió.** `README.md` en la raíz (177 líneas), que no existía: qué es el
sistema y su flujo, los tres servicios con su puerto y **enlace** a su README
(sin duplicarlos), el arranque local en el orden que funciona, cómo comprobar
que va, qué NO hacer, el mapa del repositorio y el estado real del proyecto.
Más `tests/test_f004_readme.py`, que ata el README al código para que no se
pudra en silencio — no lo exigía el nivel `documental`, y el implementer lo
entregó igual.

**Se escribió con hechos, no con suposiciones**: el 2026-08-20 se levantó el
sistema entero en local por primera vez y se verificó cada paso antes de
documentarlo. El reviewer comprobó **una por una** todas las afirmaciones
verificables contra el código, no contra el informe, y no encontró ni una
discrepancia. La trampa conocida —el api expone su salud en
**`/api/v1/health`**, no en `/health`— quedó documentada con aviso propio y
con un test que impide que se degrade.

**El bloqueo que hubo, y que no era de la feature.** El implementer entregó su
trabajo commiteado pero marcó `blocked` por un rojo de `harness/init.sh`
ajeno: `services/dedicacion-front/tests/` existía con **solo `__pycache__`
dentro** —restos de la rama de F-008, donde sí hay tests—, así que `pytest`
devolvía código 5 («no tests ran») y el portero lo trataba como fallo. **Hizo
lo correcto al no arreglar `init.sh` por su cuenta**: el defecto es del arnés
genérico y arrastra propagación a `arnes-base`, así que paró y preguntó. El
líder borró el residuo y el portero volvió a ENTORNO LISTO. Los dos defectos
del arnés que esto destapó están anotados arriba, en la entrada del mismo día.
## 2026-08-20 · F-013 · Una línea sin partida no se escribe en silencio

Rama `feature/F-013-linea-sin-partida-confirma` · `sdd: false` · rigor
`critico` · **APROBADO** por el reviewer · 8 commits sobre `dev`.

**Qué cambió y por qué.** Cuando el casado de partida fallaba en obra normal,
el pipeline ponía `paride = 0`, dejaba un aviso informativo y **escribía la
línea igual**. En el preflight real del periodo 2026-07, ejecutado el
2026-08-20, eso eran **2.132,28 €** de una jefa de obra (Arriaza García,
Raquel · obra `0025` · `MJEFO` · `can=0.385` · `pre=5538.39`) colgando de la
obra **sin imputar a ninguna partida**, y nadie se enteraba. Por decisión del
humano, ahora **avisa y espera confirmación**, igual que la sobrecarga del
100 % que introdujo F-002.

**No se inventó mecanismo**: se reutilizó el `Conflicto` con motivo propio de
la Regla B de F-002, así que **F-013 no toca `dedicacion-api` ni
`dedicacion-front`** — verificado en el diff: 12 ficheros, ninguno de esos dos
servicios.

**Verificado (salida real, reproducida por el reviewer).** Cobertura de las
líneas cambiadas **100 % (24/24)**; **7 mutantes, 7 muertos, 0
supervivientes**, campaña reejecutada; **232 tests** en el transfer; portero
en verde. Fase RED auténtica: **26 tests fallando** antes de tocar el código,
con las líneas de las trazas contrastadas una a una por el reviewer.

**La interacción entre avisos, que era lo delicado.** Una misma línea puede
caer a la vez en «sin partida», «sobrecarga del 100 %» y pisado. Se decidió
enseñar **todos** los avisos, cada uno con su clave, porque cada uno es una
decisión distinta del usuario. Cubierto con 6 tests de interacción con la
sobrecarga, 3 con el pisado, 2 de postventa (uno de control positivo) y dos
de premisa que impiden que un escenario pase por el motivo equivocado.

**La guarda muerta de T5, con la lección de F-002 aplicada.** El commit
`89e0d29` quitó dos guardas defensivas para matar mutantes. Siguiendo la
recomendación §11.2 de la review de la Fase 2 de F-002, el reviewer **no** se
conformó con ver el mutante muerto: verificó el invariante **en quien
construye el dato** y confirmó que las dos guardas eran genuinamente
inalcanzables.

Informes: `progress/impl_F-013.md`, `progress/review_F-013.md`,
`progress/mutacion_F-013.md`.

## 2026-08-20 · F-002 · Fijar las reglas P4 y P5: postventa y conflicto

Rama `feature/F-002-reglas-postventa-conflicto` · `sdd: true` · rigor
`critico` · **tres reviews aprobadas**: fase 1, fase 2 y **cierre**
(`review_F-002_fase1.md`, `review_F-002_fase2.md`, `review_F-002_cierre.md`).
Mergeada a `dev` en `985054e`.

**El problema que resolvía.** El repositorio se contradecía sobre dos reglas
que deciden qué se escribe en Sigrid, con el README diciendo una cosa y los
docstrings otra. Ninguna de las dos versiones podía darse por buena sin
preguntar.

**Cómo se cerraron las dos decisiones.**
- **D1 (postventa)**: el humano confirmó obra `POSTV2` fija y partida por
  obra, y **se verificó con una lectura real** (consulta C2): 86 partidas de
  obra en el presupuesto, todas hojas, con `cod` y `res` en campos separados,
  así que el emparejamiento por **código exacto** que ya hacía el código era
  el correcto. El `'postventa-2'` de los docstrings era **falso**.
- **D2 (conflicto)**: el humano contestó con una **tercera opción** que no
  existía en el repositorio —varias partidas por trabajador sí, pero la suma
  del mes no pasa de 1—, lo que obligó a **volver a la PARADA 1** y rediseñar.
  La vieja P4 se partió en dos reglas: **identidad** (recurso + mes + código
  de hora + **partida**) y **capacidad** (el 100 % del trabajador), esta
  última avisando y esperando confirmación, y viajando como un `Conflicto`
  más para **no tocar `dedicacion-api` ni `dedicacion-front`**.

**Lo que se verificó, con salida real.** Fase 1: cobertura 96,8 %, 9 mutantes
y 0 supervivientes. Fase 2: **187 tests** en el transfer (eran 90), cobertura
**99,1 %**, 34 mutantes y **1 superviviente demostrado equivalente** con una
prueba ejecutable —la primera campaña dejó **8** y se atacaron los ocho, uno
de ellos destapando un fallo real: el `contexto` de un conflicto mostraba
líneas de **otro trabajador**—. Y **dos defectos reales corregidos**: el doble
`DELETE` del mismo `hmores.ide` (R13) y el filtro de `resolver_postventa` que
decía quedarse con las hojas y no lo hacía.

**T13 y T14, ejecutadas contra Sigrid real el 2026-08-20.** El preflight de
julio (13 obras, 4 líneas a escribir, 0 conflictos) y **la primera escritura
real de este sistema en el ERP**: `hmores.ide = 403039`, parte `PT26/00296`
creado, obra de pruebas `0404`. Volcados en `progress/sigrid_F-002.md`.

**Dos avisos que sobreviven al cierre, ambos con dueño en F-014.** Sigue viva
la fila de prueba en Sigrid; y **la Regla B nunca se ha ejercitado contra
Sigrid real**, porque el parte de la obra destino no existía y no había líneas
`M*` previas con las que chocar. Está probada offline, pero conviene que
alguien mire con atención el primer preflight real que sí tenga líneas previas.

**Lo que costó dos rechazos, y no fue el código.** Las reviews de la fase 1 y
del cierre se rechazaron por el **rastro documental**, siempre del líder: un
`current.md` que decía «no se ha tocado ni una línea de código» con siete
commits hechos, y —lo más grave— **el volcado de T13 perdido al resolver un
merge**, porque el líder reescribió `progress/current.md` entero sin darse
cuenta de que llevaba dentro evidencia que no estaba en ningún otro sitio. Se
recuperó del commit `01bf62a`. Lección: **un fichero de rastro puede contener
información única; resolver su conflicto reescribiéndolo la destruye en
silencio.**
