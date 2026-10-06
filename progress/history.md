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

## 2026-08-21 · F-015 · Alta en el Portal Ruesma: tarjeta y usuarios del grupo

`sdd: true` · rigor `documental` · **APROBADO** en la 2ª pasada de la review de
cierre · trabajada en `dev` (ver «Nota de método» abajo).

**El problema.** El sistema llevaba un día desplegado y funcionando en Azure,
pero **nadie podía llegar a él**: no había tarjeta en el Portal Ruesma desde la
que entrar, y la Enterprise App tiene **asignación requerida**, así que quien
no estuviera en el grupo `dedicacion-portal-users` no obtenía token **aunque
tuviera cuenta de Ruesma**. Solo estaba dado de alta el humano.

**El hallazgo de la spec, que cambió el trabajo.** No había que pedirle la
tarjeta a nadie: `front-portal` es un repositorio del propio humano y dar de
alta una app es **editar `public/assets/js/catalog.js` y desplegar**. La spec
salió en **104 líneas** porque el humano la pidió corta para hacerla juntos.

**Qué se hizo.** Entrada añadida al catálogo en la categoría *Obra*, icono
`chart` —`compare` ya lo usa «Comparativos» y confundiría un cuadrante de
porcentajes con una comparativa—, apuntando al FQDN del front y restringida
por el grupo. El humano la commiteó (`4d7cfa8` en `front-portal`), la desplegó
y dio de alta a **8 personas**. `docs/INTEGRACION.md` §5 y su copia
`azure-apps/dedicacion.md` explican cómo se llega, quién puede entrar y cómo
dar acceso a alguien nuevo, **sin listar a nadie**: son datos personales y
cambian, así que queda el comando para consultarlos.

**Una duda cerrada con evidencia en vez de con fe.** La spec advertía de que,
sin licencia Entra ID P1, la «asignación requerida» se ignora **en silencio** y
entraría cualquiera del tenant. Se comprobó: `appRoleAssignmentRequired = True`.
Era una duda buena — de haber sido falsa, se habría dado por protegido algo que
no lo estaba.

**El objectId del grupo no está en este repositorio.** Vive solo en el catálogo
de `front-portal`, que es donde el mecanismo del portal lo exige. Verificado con
`git grep` y con el guardián de secretos (53 tests).

**Los cuatro remates que costaron un rechazo, todos del líder.** El que más
daño hacía: la **cabecera** de `azure-apps/dedicacion.md` seguía diciendo que
la tarjeta y el alta «están pendientes» cuando llevaban un día en producción.
El cuerpo estaba bien, pero quien abre ese documento lee el recuadro, y sacaba
la conclusión contraria a la verdad. Los otros tres: `current.md` describiendo
una sesión ya pasada, `features.json` apuntando a una **rama inexistente**, y
una tarea sin marcar.

**Nota de método.** F-015 se trabajó **directamente en `dev`**, contra la regla
de una rama por feature. Se decidió a conciencia —no toca una línea de código
de este repositorio y se hizo intercalada con el despliegue en vivo, donde el
árbol tenía que estar en `dev` para corregir los scripts sobre la marcha— y
`features.json` lo **declara** en vez de mentir. El reviewer señaló que un
commit de F-008 (`a59b1b5`) está igual: es **deriva de método**, no un descuido
puntual. No es la norma y no debe volverse costumbre.

Informes: `progress/spec_F-015.md`, `progress/review_F-015.md`.

## 2026-08-21 · F-008 · Infraestructura y despliegue en Azure

`sdd: true` · rigor `critico` · **APROBADO** en la 3ª pasada de la review de
cierre (las fases 1–6 ya tenían la suya, `progress/review_F-008.md`).

**Qué se consiguió.** El sistema pasó de correr solo en un portátil a estar
**desplegado y en uso**: tres Container Apps en `rg-dedicacion-dev`, base
propia `dedicacion` en el servidor compartido, secretos en Key Vault por
identidad gestionada, Easy Auth con grupo de asignación requerida, y tarjeta en
el Portal Ruesma (esto último, F-015). El transfer **sigue en modo pruebas**.

**Tres hallazgos que salieron de escribir la spec, no de desplegar.** Los tres
eran defectos reales del código que nadie buscaba:

1. **`dedicacion-api` creaba la base de datos y el rol en cada arranque**,
   conectándose como **administrador del servidor**. Contra
   `psql-albaranes-rs9k2`, compartido con otros cuatro proyectos, eso es
   exactamente lo que el ecosistema prohíbe por escrito. Ahora
   `AUTO_CREATE_DATABASE` está apagado por defecto y **ni siquiera abre esa
   conexión** — se vio funcionar en el log del primer arranque en Azure.
2. **Los timeouts encadenados estaban al revés**: el front esperaba 120 s y la
   api 180 s, así que el front se rendía **antes** y el usuario habría visto un
   error de un registro que sí se estaba completando.
3. **El transfer no tenía `Dockerfile`.** Era el único de los tres.

**Cinco bugs más, que solo aparecieron desplegando de verdad.** Ninguno lo
habría cazado un test offline, porque todos son de la interacción real con `az`
y con PowerShell 5.1: el flag `-d` frente a `-n`; **`az ... show` devolviendo
error cuando el recurso no existe** —que con `ErrorActionPreference = "Stop"`
aborta el script, y afectaba a cuatro sitios—; el bloque `DO $rol$` troceado
por `--querytext`; `az keyvault create` no idempotente pese a prometerlo; y el
fallo al escribir `imagenes.json` **después** de haber publicado las tres
imágenes, que dejó el despliegue creyendo que no existían.

**Lo que costó tres pasadas de review, y no fue el código.**

- **Una explicación falsa mía.** Escribí en el script que en PS 5.1 un
  `New-Object` anidado como argumento de un método estático «no resuelve». El
  reviewer lo **reprodujo** y demostró que es falso, con un contraejemplo del
  propio repositorio (`setup_front_easyauth.ps1`, que usa ese constructo y
  funcionó). El arreglo era correcto pero la causa raíz **quedó sin
  identificar**, y ahora el script lo dice así en vez de enseñar una causa
  inventada que alguien copiaría a otro proyecto.
- **El digest del inventario no tenía portero**, justo el campo que se tecleó
  a mano tras el fallo del script. Se podía borrar y la suite seguía verde.
- **La decisión D5 no tenía dueño: nadie.** Viajaba dentro de T30, T30 se movió
  a F-015 y F-015 solo se llevó la mitad. Ahora es **F-016**. Lo que está en
  juego: api y transfer **comparten function key**, así que lo único que impide
  que la api escriba en el ERP es que su código no tiene rutas de escritura.
- **La fuente de verdad contradecía a su propia copia.** `docs/INTEGRACION.md`
  seguía diciendo que faltaba la tarjeta mientras `azure-apps/dedicacion.md` ya
  decía que estaba en uso: **la copia bien y la fuente mal**, al revés de la
  regla que el documento se impone. El reviewer lo había avisado una pasada
  antes y F-015 cerró sin recogerlo.

**Lo que se declara NO verificado, a propósito.** El nivel `critico` exige
decir la verdad, no aparentarla: **R34** (el `/health` del transfer con
`modo_pruebas` y `database`) no se comprobó porque el servicio tiene ingress
interno y no es alcanzable desde fuera — que es justo lo que la decisión D2
buscaba; y **T29** se apoya en la **confirmación del humano, sin volcado**.
Ambas cosas constan en el texto de sus propias tareas, no en una nota al pie.

**Y no se llamó a `registro/ejecutar` desde el entorno desplegado**, por
acuerdo: habría escrito más líneas `PRUEBA-PORC` indistinguibles de la de T14,
que entonces seguía viva.

Informes: `progress/impl_F-008.md`, `progress/review_F-008.md`,
`progress/review_F-008_cierre.md`, `progress/spec_F-008.md`.

## 2026-08-22 · Arnés actualizado a 1.7.3

De **1.5.2** a **1.7.2** y, con el correctivo de abajo, a la **1.7.3** que
nació aquí. Todo en la rama `chore/arnes-1.7.2`. El instalador aplicó
lo genérico (agentes, `harness/*.py`, `rigor.json`, `SPECS.md`, 15 tests
nuevos) y conservó los seis ficheros adaptados; `CHECKPOINTS.md` y
`harness/init.sh` se fusionaron a mano para quedarse con las mejoras genéricas
sin perder lo del monorepo. Portero en verde: **354 tests, 1 skipped**.

Lo que cambia para trabajar aquí:

- **Puerta nueva de tamaño del papeleo** (`init.sh` sección 7 quater, topes en
  el bloque `tamano` de `harness/rigor.json`): requirements 150, design 250,
  `impl_F-XXX.md` 220, `review_F-XXX.md` 140 líneas. Mide **solo la feature en
  curso**: lo viejo queda amnistiado, lo que se retome y edite pasará a
  medirse. Pasarse pone el portero en **rojo**.
- **`nivel_por_defecto` pasa de `critico` a `estandar`.** No afecta hoy: las 14
  features declaran su `rigor` explícitamente. A partir de ahora, `critico` se
  declara, no se hereda.
- **Campañas `estandar` muestreadas a 20 mutantes** con semilla fija; sus
  números **no** son comparables con los de campañas anteriores. Campaña
  entera: `--max-mutantes 0`.
- **El reviewer reejecuta la campaña por debajo de 60 segundos** (antes 5
  minutos) y revisa **incremental** desde el último SHA aprobado, declarándolo
  en la primera línea de su informe. Reglas **RM1–RM6** en `CHECKPOINTS.md` C4
  bis y en `.claude/agents/reviewer.md`.
- **Timeout y workers de mutación se calculan solos**: el timeout se deriva de
  la línea base medida (`timeout_por_mutante_s` es ahora un **suelo**) y los
  workers por defecto bajan a `min(max(1,(núcleos-2)//2),4)`.
- **Códigos de salida nuevos de `harness.mutacion`**: `2` alcance vacío, `3`
  cero mutantes generados (sin informe). Un guion que encadene campañas debe
  tratarlos como fallo.
- **Uno de los dos defectos del arnés que anotamos ya tiene ficha**: pytest
  código 5 («ningún test recogido») contado como verde es el defecto CONOCIDO
  que la 1.7.2 declara **sin arreglar** (F-041 en `albaranes`, rigor
  `critico`). Mientras viva, una campaña de una sola pasada no vale como
  evidencia: contrástala con otra (`--workers 1`). El segundo —la caché de
  suites cruza ramas— sigue sin ficha.
- **Defecto de la 1.7.2 encontrado y corregido aquí**: la puerta de tamaño
  medía también las features `done`, y F-015 declara `branch: "dev"` (se hizo
  en la rama base), así que su review de 546 líneas dejaba `dev` en **rojo
  permanente**. La sección 7 quater descarta ahora el papeleo cerrado, con test
  en `tests/test_tamano.py`. **Portado a `arnes-base` como 1.7.3** por la regla
  de propagación, y reinstalado desde ahí: este repo lleva ya la 1.7.3. El
  commit de `arnes-base` (`a695c32`) está **pusheado** a
  `ruesma-dev/harness-ruesma`.
- `ruff` pasa de 179 a 185 avisos: los seis nuevos son del código del arnés que
  acaba de entrar. Deuda previa, no bloquea.

> Pasado aquí desde `current.md` el 2026-09-30, al pedirlo la review de
> F-022 (C2): `current.md` debe describir solo la sesión activa.

## 2026-09-30 · F-022 · El transfer busca cada obra por código y empresa

Rama `feature/F-022-transfer-obra-por-empresa` · `sdd: true` · rigor `critico` ·
**APROBADO** por el reviewer en la pasada 2 (la pasada 1 pidió cambios solo por
el rastro de `current.md`, no por el código). Spec aprobada por el humano el
2026-09-29 con D1-D4; la D5 (el recurso tampoco mira la empresa) pasó a F-026,
que queda como requisito de F-018.

**Qué cambió.** El transfer busca cada obra por código **y** empresa
(`con.emp`), en SQL y en Python, y falla en vez de elegir si hay dos fichas en
la misma empresa. La empresa viaja en cada línea; la pone la api con
`EMPRESA_IMPUTACION` (1 por defecto) hasta que la elija el usuario (F-024).
Una línea sin empresa o de obra de otra empresa se **omite con motivo**; una
petición que mezcla empresas es **422**. Fuera `SIGRID_EMPRESA`. Regla nueva
`docs/ARCHITECTURE.md#regla-empresa`; `azure-apps/dedicacion.md` refrescada.

**Verificado.** `init.sh` en verde (355 passed, 1 skipped); cobertura de líneas
cambiadas 97,4 %; mutación **28/28 muertos**, reejecutada por el reviewer; RED
de T2 reproducida por el reviewer en un worktree aislado; POSTV2 en empresas 1
y 28 en los dos órdenes; ningún assert anterior cambia. **T10 (MANUAL) cumplida
el 2026-09-30** con un preflight real de solo lectura: obra 0658, postventa y
destino `0404` en la empresa 1; y las obras 0009 y 0025 del maestro local, que
son fichas de Porsan, salen omitidas por R11 con datos reales.

**Lo que dejó para después.** ruff pasa de 185 a 193 avisos (estilo de los tests
nuevos, deuda previa). La primera campaña dio dos falsos supervivientes que no
se reproducían con la caché limpia: van como encargo a `arnes-base`, junto con
la contradicción C5/MANUAL (`357522c` en `arnes-base`). El preflight publica
`partidas_postventa` también en obras sin postventa: recogido en F-025.

Informes: `progress/impl_F-022.md`, `progress/review_F-022.md`,
`progress/mutacion_F-022.md`. Detalle de sesión que se retiró de `current.md`:

## F-022 · El transfer busca cada obra por código y empresa

- Rama `feature/F-022-transfer-obra-por-empresa`. Spec aprobada por el humano
  el 2026-09-29 (D1-D4; la D5 pasa a F-026). Implementer terminado
  (`progress/impl_F-022.md`); T1-T9 y T11 hechas, **T10 es MANUAL del humano**
  y está pendiente (abajo).
- **Para pasar a `done` falta solo el commit del humano en `azure-apps`.**
  T10 está cumplida (abajo) y la review está aprobada.
- **Al cerrar**: pasar a `history.md` la sección «Revisión de negocio del
  2026-09-29» (observación 3 de la pasada 2) y anotar ruff 185 → 193.
- Observaciones de la review 1, **recogidas**:
  - En los cortes R3/R11 `obra_destino` publica la obra de entrada con
    `empresa: null`. Queda como criterio en **F-024** (`features.json`).
  - Esta rama toca en `features.json` las entradas de F-018, F-023 y F-026.
    **Al mergear F-023 después**, resolver el conflicto de `features.json`
    fusionando las entradas, sin reescribir el fichero (ver «Hechos»).
  - Automejoras del arnés (C5 contra MANUAL; falsos supervivientes con
    caché previa): por decisión del humano van al **backlog de `arnes-base`**
    como `ENCARGO_pendiente_*.md` (commit `357522c` en `arnes-base`, sin
    push). No se tocan en este repositorio.

Detalle del implementer (desviaciones, todas aceptadas por la review 1):

- Desviación menor (orden, no alcance): `empresa=1` en las LÍNEAS de los
  dobles (`conftest.linea()`, `test_pipeline_offline.lineas_entrada()`) entra
  en el commit de T3 y no en el de T4. Con las reglas nuevas, una línea sin
  empresa se omite, y sin ese dato la suite quedaba en rojo (91 fallos) entre
  T3 y T4. Ningún assert cambia.
- T4: el doble de `conftest.py` conoce ahora la obra `0001` (constante
  `OBRA_SIN_PARTIDA_PV`). `test_f013_la_postventa_sin_partida_se_sigue_omitiendo`
  la usa como origen y, desde F-022, el origen se resuelve también en pruebas
  (R10; design §8, riesgo asumido). Es dato del doble; el test no cambia.
- T6: `RegistroSigrid` exige `empresa_imputacion` (design §4.8, sin valor
  por defecto), así que las tres construcciones de `test_f003_esquema.py`
  pasan `empresa_imputacion=1`. Solo el argumento; ningún assert cambia.
- **T8, desviación que decide el humano.** La copia
  `azure-apps/dedicacion.md` ya divergía del cuerpo de `docs/INTEGRACION.md`
  ANTES de F-022, en 4 bloques ajenos a esta feature: (1) §1, `ruesma_rep`
  «no es una réplica, es la base documental» — corrección hecha en la copia
  por `sigrid-api` (commit `a40684f` de azure-apps, 2026-09-05) que
  `INTEGRACION.md` no tiene; (2) §5, tarjeta del Portal y (3) «Quién puede
  entrar», redactados distinto desde la copia inicial (`08676ac`); (4) §6,
  filas de FQDN que la copia no lleva. Copiar el cuerpo entero habría
  BORRADO la corrección (1). Se hizo lo no destructivo: cabecera (commit
  `f9b3a46`, fecha 2026-09-29) y las tres piezas de F-022 copiadas LITERALES
  de `INTEGRACION.md` (fila `EMPRESA_IMPUTACION`, fila del transfer sin
  `SIGRID_EMPRESA`, párrafo §9). El `diff` del cuerpo ya no tiene ninguna
  diferencia de F-022, pero conserva esos 4 bloques. **Pendiente del humano**:
  revisar y hacer el commit en `azure-apps` (sin commit por el agente), y
  decidir si la corrección de `ruesma_rep` se porta a `INTEGRACION.md` (fuera
  del alcance de F-022).
- T9: campaña completa en serie (`--workers 1`: el fichero sin versionar
  `progress/explore_grafico_parte.md` impide la paralela y no es nuestro).
  Primera pasada (SHA `c4d9c3e`): 29 mutantes, 5 supervivientes; dos de
  ellos (`registro_pipeline.py:109` y `:116`) resultaron FALSOS: aplicados a
  mano en el árbol, los mata `test_f002_r11_modo_pruebas_destino_y_partida`.
  Esa pasada se DESCARTA. Se arreglaron los otros tres (mensaje de obra
  ambigua con el código pedido; test de los datos del script manual), se
  borraron `__pycache__`/`.pytest_cache` y se relanzó: **28/28 muertos, 0
  supervivientes** (SHA `dfe079d`, `progress/mutacion_F-022.md`).

### F-022 · verificación MANUAL pendiente (humano) — T10 / M1

Preflight real, **solo lectura**, con el transfer en modo pruebas (API 8090 y
transfer 8006 en local), sobre un periodo con al menos una línea de
postventa:

    curl -s -X POST http://127.0.0.1:8090/api/v1/periodos/AAAA/MM/registro/preflight -H "Content-Type: application/json" -H "X-Usuario: <usuario>" -d "{}"

Comprobar, en la obra con postventa: `obra_postventa.empresa == 1`,
`obra_destino.codigo == "0404"` y `obra_destino.empresa == 1`. **NO** se lanza
`registro/ejecutar`.

**Resultado real (2026-09-30, lanzado por el humano con
`t10_preflight_f022.ps1`, API y transfer de la rama F-022 en local, transfer
con `modo_pruebas=true`, `obra_pruebas=0404`, base `ruesma`): CUMPLIDA.**

- **2026-07, obra 0658:** línea de postventa con `obra_postventa` = `0404`
  empresa 1 (en modo pruebas la postventa también se desvía) y `obra_destino`
  = `0404` empresa 1. Es la única obra de julio cuya postventa casó con una
  partida de POSTV2.
- **2026-07, obras 0009 y 0025 (fichas de Porsan del maestro local):** sus
  líneas salen **omitidas** con «la obra … es de la empresa 28 y la línea se
  imputa a la empresa 1: no se escribe». Es R11 con datos reales. Antes de
  F-022 esas líneas iban contra la ficha de Porsan. Hasta que F-023 y F-024
  arreglen el maestro, **el usuario verá estas omisiones en el preflight**.
- **2026-08, obras 0455 y 0465:** POSTV2 se resuelve en la empresa 1 **sin
  ambigüedad** (se leen sus partidas), pero las obras no casan con ninguna
  partida («no casa con ninguna partida de POSTV2»). No es de F-022: es el
  universo de postventa de F-025.
- Primera ejecución de agosto: el script dio `OK` **sin haber comprobado
  nada**, porque ninguna línea tuvo destino de postventa. Se corrigió el
  script (ahora dice «NO CONCLUYENTE») y se repitió en julio.
- Hallazgo menor, anterior a F-022: el preflight publica
  `partidas_postventa` también en obras sin líneas de postventa (el catálogo
  `_nodos_pv` se queda en la instancia del pipeline entre llamadas).
  Inofensivo; pendiente de ficha.


## 2026-09-29 · Revisión de negocio: F-022 a F-031 entran al backlog

Negocio revisó la app en uso y salieron fallos y peticiones. Se dan de alta
en la rama `chore/backlog-f022-f031`, ya mergeada en `dev` (`01671a9`, sin push):

- **Fallos de maestros**, diagnosticados con evidencia en
  `progress/explore_maestros_sync.md` y `progress/explore_eusebio.md`:
  - F-022: el transfer busca la obra sin empresa. POSTV2 existe en las
    empresas 1 y 28. **Bloquea F-018.** (F-022 es la feature en review, arriba; F-018 sigue `pending`.)
  - F-023: el sync no lee la empresa y no usa el estado del recurso.
  - F-025: las obras de postventa están CERRADAS y el filtro de estado las
    quita.
  - F-026: el recurso de Eusebio Vindel Duro tiene vacío «Empleado
    asociado» (`res.conide`).
- **Peticiones**:
  - F-024: selector de empresa.
  - F-027: deshacer solo lo propio.
  - F-028: borrar lo que está en pantalla.
  - F-029: selección múltiple y completar hasta el 100 %.
  - F-030: dedicación por días, bajas e incidencias.
  - F-031: MCP para IA.
  - Se amplían F-020 (quitar la columna E del Excel) y F-021 (el filtro
    por obra marca a los asignados en Sesame).
- Las decisiones del humano de ese día están escritas en la descripción de
  cada entrada.
- **Pendiente de negocio:**
  - Si encargados y gruistas se dan de alta sin ficha de empleado a
    propósito (decide cómo se arregla F-026).
  - Objeción, si la hay, a que una obra cerrada se ofrezca solo como
    «Postv-» (F-025).
- **Por lanzar contra Sigrid (solo SELECT):** las tres consultas de
  `progress/explore_eusebio.md`, que confirman la causa de F-026.

## 2026-10-01 · F-023 · Sync de maestros: todas las empresas y activo según el estado del recurso

Rama `feature/F-023-sync-empresa-y-estado-recurso` · `sdd: true` · rigor
`critico` · **APROBADO** por el reviewer en la pasada 3. La pasada 1 aprobó el
código; la 2 aprobó T9 pero pidió cambios porque la D1 seguía abierta en el
rastro (error del líder: la cerró en 2 de sus 4 sitios); la 3, documental.

**Qué cambió (solo `dedicacion-api`).** Obras y trabajadores guardan su
empresa (`con.emp`), con la columna en el ORM y sin DDL a mano. El sync trae
**todas las empresas**; el dedupe por persona no las mezcla y descarta los
recursos de otra empresa que la ficha. **Inactivo = fecha de baja del
concepto del recurso** (`con.fecbaj > 0`, D1 cerrada por el humano con
`progress/explore_estado_recurso.md`, sin lanzar Q1): el tipo 33 no tiene
estados en `conest`, así que la lista de estados queda vacía a propósito. Se
quita el filtro de `emphis`. Preview y sync aplican el mismo criterio.

**Verificado.** 53 tests nuevos offline; cobertura de líneas cambiadas 100 %;
mutación **33/33**, reejecutada por el reviewer; RED real en T1 y en T9.
**T11 (MANUAL) cumplida**: sync real contra la BBDD local, 0 filas activas sin
empresa. **T10 (MANUAL) cumplida con evidencia alternativa, por decisión del
humano (D5)**: no se contrastó la lista de inactivos de negocio; el preview
real excluye **535** recursos por fecha de baja, la misma cifra que midió el
data mart por otra vía. Es más débil que la lista y consta así.

**Pendiente y avisos.** **No se despliega sin F-024**: sin selector, el
cuadrante mezcla empresas (la BBDD local ya las tiene mezcladas tras T11). Las
filas desactivadas conservan `empresa` NULL; su efecto en el filtro va en
F-024. Automejoras al backlog de `arnes-base` (`5724ad4`, `c94c072`,
`9cd66b3`).

Informes: `progress/impl_F-023.md`, `progress/review_F-023.md`,
`progress/mutacion_F-023.md`, `progress/explore_estado_recurso.md`. Detalle de
sesión retirado de `current.md`:

## F-023 · Sync de maestros: todas las empresas y activo según el estado del recurso

- Rama `feature/F-023-sync-empresa-y-estado-recurso`, con `dev` traído
  (`792870f`, incluye F-022). Estado `in_progress`. Spec aprobada el
  2026-09-29; decisiones en `features.json`.
- **Implementer terminado**: T1-T8 y T12 hechas, un commit por tarea más dos
  de ajuste (`5ae53d1` … `19d4f40`); informe `progress/impl_F-023.md`, con
  mutación 33/33 y dos desviaciones menores, aceptadas. **Review APROBADA**:
  campaña reejecutada 33/33, cobertura 100 % (67/67), 0 avisos de ruff nuevos.
- Observaciones de la review, **recogidas**:
  1. R12 y el JOIN a `conest` del recurso quedan inertes (el tipo 33 no tiene
     estados) y la comparación es por subcadena: un `"1"` casaría `"10"`. **Al
     cerrar T9**, el líder corrige el comentario de `config.yaml` (para
     recursos no hay literales; el criterio es la fecha de baja). Simplificar
     R12 sería otra feature, si el humano la quiere.
  2. T11 corregida abajo: las filas **desactivadas** conservan `empresa` NULL
     (el upsert solo escribe las recibidas). Aviso llevado a F-024.
  3. **T9 antes del merge a `dev`**, no solo antes del despliegue: sin el
     criterio, esta rama mete en el maestro ~535 personas de baja como recurso
     que hoy filtra `emphis`.
  - Automejora (C4: comprobar que el resultado esperado de una MANUAL es
    alcanzable) → encargo en el backlog de `arnes-base`.
- **Explorador (D1)** → `progress/explore_estado_recurso.md`: el «rojo» de
  Administración es la **fecha de baja del concepto del recurso**
  (`con.fecbaj > 0`); el tipo 33 no tiene estados en `conest`. **Aceptado por
  el humano el 2026-10-01 y aplicado en T9** (`9b9c1d9`).
- **No se despliega sin F-024** (D4: sin selector, una persona con fichas en
  dos empresas sale dos veces). Mergear a `dev` no despliega.

#### Verificaciones MANUAL (humano) de F-023

- **T9 · D1 — CUMPLIDA (2026-10-01)**: decidida por el humano, sin lanzar Q1:
  inactivo = fecha de baja del recurso. Implementada en `9b9c1d9`:
  `excluir_recurso_con_fecha_baja: true`, lista de estados vacía con
  comentario corregido (observación 1 de la review), `r5` y `r18` adaptados
  con fase RED real, mutación 33/33, `init.sh` en verde. Review pasada 2:
  código y tests **aprobados**; CHANGES_REQUESTED solo porque la D1 seguía
  abierta en otros sitios del rastro (corregido). Pasada 3 (documental):
  APPROVED; sus dos observaciones, recogidas. Automejora → encargo `c94c072` en `arnes-base`.
- **T10 · R19 y D6**: con la API local apuntando a Sigrid,
  `GET http://localhost:8090/api/v1/sync/preview`. Comprobar que no llega
  truncada, que los recursos inactivos que señaló negocio (lista D5, **aún no
  entregada**) salen en `excluidos_por_estado_recurso`, y revisar
  `por_empresa`. Resultado: _pendiente_.
- **T11**: API contra la BBDD local `dedicacion`; comprobar que el esquema
  añade `empresa` a `trabajador` y `obra`; `POST /api/v1/sync` y
  `SELECT empresa, COUNT(*) FROM obra WHERE activa GROUP BY empresa` y
  `SELECT empresa, COUNT(*) FROM trabajador WHERE activo GROUP BY empresa`,
  sin NULL. Las filas desactivadas **sí** pueden quedar con NULL, y es
  correcto (observación 2 de la review). **Resultado real (2026-10-01,
  humano, `t11_sync_f023.ps1`, API de `dev` contra la BBDD local): CUMPLIDA.**
  La columna `empresa` existe en `obra` y `trabajador`; **0 activas con
  empresa NULL** en las dos (obras activas 453 en 19 empresas, 313 de la 1;
  trabajadores activos 179: 171 de la 1, 4 de la 18 y 4 de la 31). Las
  desactivadas (469 obras, 427 trabajadores) quedan con NULL. Sync:
  empleados 179 recibidos, 32 altas, 147 actualizados, 28 desactivados;
  obras 453 recibidas, 6 altas, 447 actualizadas, 167 desactivadas; 6,0 s.
  Preview: 1.358 brutos, **535 excluidos por fecha de baja del recurso**
  (la misma cifra que midió el explorador en el data mart: cruce
  independiente del criterio), 642 sin código M*, 0 por recurso de otra
  empresa, 29 con baja laboral (informativo); no llegó truncado.

## 2026-10-01 · F-024 · Selector de empresa arriba a la derecha, Ruesma por defecto

Rama `feature/F-024-selector-empresa` · `sdd: true` · rigor `estandar` ·
**APROBADO** por el reviewer a la primera. Prioridad subida a 2 por el humano:
sin ella no se despliegan F-022 ni F-023.

**Qué cambió (tres servicios).** API: regla de visibilidad por empresa en el
dominio, un único punto de filtro para cuadrante, fila, guardar, deshacer, las
dos copias, resumen, export y registro; `GET /api/v1/empresas`; parámetro
`empresa` (entero > 0) en las rutas del periodo; cada línea se imputa a la
empresa **elegida** y `EMPRESA_IMPUTACION` pasa a ser la por defecto (D6).
Transfer: el corte por obra de otra empresa publica la obra de origen
resuelta (recogido de la review 1 de F-022); contrato intacto. Front: selector
en la barra superior, empresa en la URL y en cada llamada, marcas «sin
empresa» y «otra empresa», sin lógica de negocio.

**Verificado.** Cobertura 100 % (105/105); mutación 17/17; único assert
anterior cambiado, el de F-022 previsto en el design. **T11** (copia en
`azure-apps`, `f6ef278`) y **T13** (prueba en local: parte visual confirmada
por el humano; parte de API ejecutada por el líder y repetida por el humano
con el mismo resultado) cumplidas. Sin ejercitar con datos reales: el
preflight con la 18 (R19), porque no tiene líneas en julio; lo cubren tests.

**Decisiones de cierre.** **T12 sustituida por F-032**: el humano decide que
los nombres de empresa salgan de Sigrid (`auxemp`) y no de `config.yaml`.
Observación O1 de la review (guardar/deshacer/copiar no comprueban
visibilidad) → criterio de F-031; O2 y O3, descartadas por cosméticas.
Automejora → `arnes-base` (`2182089`). **F-022, F-023, F-024 y F-032 se
despliegan juntas.**

Informes: `progress/impl_F-024.md`, `progress/review_F-024.md`,
`progress/mutacion_F-024.md`, `progress/explore_nombres_empresas.md`. Detalle
de sesión retirado de `current.md`:

## F-024 · Selector de empresa arriba a la derecha, Ruesma por defecto

- Rama `feature/F-024-selector-empresa`. Spec aprobada por el humano el
  2026-10-01 con D1-D7 (`features.json`). Plan confirmado.
- **Implementer terminado**: T1-T10 y T14, un commit por tarea más dos de
  estilo (`1b0bc40` … `2cbe55c`); informe `progress/impl_F-024.md`. Toca los
  tres servicios; contrato API ↔ transfer intacto; único assert anterior
  cambiado, el de F-022 que declara design §7. Mutación 17/17. **Review APROBADA** a
  la primera (`progress/review_F-024.md`): cobertura 100 % (105/105), las ocho
  rutas del periodo con filtro, front sin lógica, contrato intacto.
- Observaciones de la review, **recogidas o descartadas por escrito**:
  - O1 (guardar/deshacer/copiar no comprueban visibilidad) → criterio nuevo
    de **F-031**: un MCP que escriba es un segundo cliente.
  - O2 (`?empresa=99` queda en la URL) y O3 (`cerrar`/`reabrir` ignoran
    `?empresa=`): **descartadas**, cosméticas e inocuas.
  - O4 (el cambio del transfer no genera mutantes): sostenido por la RED de
    T7 y los tests de R20; nada que hacer.
  - Automejora de C4 bis → encargo en `arnes-base`.
- **Mergeada a `dev`** tras la review (T11-T13 bloquean el `done`, no el
  merge).
- **Explorador (T12), terminado**: nombres de las 19 empresas desde tres
  vistas del data mart que coinciden (18 = RUESMA SERVICIOS SL, 31 = UTE
  RUESMA-INESCO TOLEDO; 1 y 28 confirmadas). Informe en el scratchpad del
  líder; se versiona como `progress/explore_nombres_empresas.md` al cerrar
  T12. **Propuesta al humano, pendiente de su respuesta**: poner los 19 en
  `config.yaml` tal cual y dar T12 por cumplida sin consultar sigrid-api.

#### Verificaciones MANUAL (humano) de F-024

- **T11 — CUMPLIDA (2026-10-01)**: el líder, con autorización del humano,
  copió a `azure-apps/dedicacion.md` las cuatro piezas de T10 literales
  (cabecera, fila de `EMPRESA_IMPUTACION`, párrafo de `GET /api/v1/empresas`
  y §9) sin reescribir el resto; commit `f6ef278` en `azure-apps`.
- **T12**: nombres de las empresas con trabajadores activos (18 y 31) en
  `config.yaml` `empresas.nombres`. Hoy lleva solo 1 y 28 (D1). El
  explorador tiene los nombres (arriba), pendiente de que el humano los
  acepte; la alternativa es `SELECT numemp, res FROM dbo.auxemp WHERE numemp
  IN (1, 18, 28, 31)` por sigrid-api. Resultado: _pendiente_.
- **T13 — CUMPLIDA (2026-10-01)**, con un punto sin ejercitar. Parte
  visual: confirmada por el humano en `http://localhost:8080` (selector con
  Ruesma por defecto, cambio a la 18 con `?empresa=18` que sobrevive al
  recargar, marcas de otra empresa). Parte de API: `t13_selector_f024.ps1`
  (solo lectura, sin `ejecutar`), API y transfer de `dev` con modo pruebas:
  `/empresas` da por defecto la 1 y la lista 1, 18, 31; julio 2026 con la 1,
  180 trabajadores (igual sin `?empresa`), líneas de 0009 y 0025 marcadas
  `otra_empresa` (empresa 28) y omitidas en el preflight con
  `obra_destino.empresa == 28`, nada escrito; con la 18, 4 trabajadores y 8
  obras (313 con la 1); 9 trabajadores visibles «sin empresa». **Sin
  ejercitar con datos reales**: el preflight con la 18 (R19, D3), porque la
  18 no tiene líneas en julio; lo cubren los tests de `test_f024_registro_empresa.py`.

> **Aviso de despliegue:** F-022 y F-023 están en `dev` pero **no se
> despliegan sin F-024** (sin selector, el cuadrante mezcla empresas). La
> BBDD local ya tiene maestros de todas las empresas desde T11 de F-023.

## 2026-10-01 · F-032 · Nombres de empresa sincronizados desde Sigrid

Rama `feature/F-032-empresas-desde-sigrid` · `sdd: false` · rigor `estandar` ·
**APROBADO** por el reviewer en la pasada 3. La pasada 1 aprobó código, tests y
campaña; la 1 y la 2 se rechazaron **solo por el rastro del líder** (manual sin
comando exacto ni `azure-apps` pendiente; después, el script citado desde el
scratchpad de la sesión, cuya ruta con UUID dejó `init.sh` en rojo).

**Qué cambió.** Nace de la T12 de F-024: el humano decidió que los nombres del
selector salgan de Sigrid y no de `config.yaml`. El sync de maestros lee el
catálogo `auxemp` (solo lectura) y lo guarda en la tabla `empresa` (ORM, clave
`numemp`, upsert idempotente); el preview informa de las empresas leídas;
`GET /api/v1/empresas` da nombre y `de_baja` de la tabla; fuera
`empresas.nombres`. Una empresa de baja o desactivada con trabajadores activos
se enseña marcada «(de baja)», nunca oculta (decisión del humano). El front
solo pinta la marca. El script de la manual queda versionado en
`scripts/verif_f032_empresas.ps1`.

**Verificado.** 32 tests nuevos; mutación con muestreo estándar, 2
supervivientes reproducidos a mano y cazados con tests; tests de F-024 que
fijaban `empresas.nombres` sustituidos por equivalentes sin cambiar valores
esperados. **Resultado real (2026-10-01, humano, `scripts/verif_f032_empresas.ps1`, api de `dev` con F-032 contra la BBDD local): CUMPLIDA.** Preview: 38 empresas leídas, 0 sin número, ninguna de baja. Sync: empresas 38 recibidas y 38 altas; empleados y obras sin cambios (179 y 453 recibidos). `/empresas`: por defecto 1; 1 = CONSTRUCCIONES RUESMA, 18 = RUESMA SERVICIOS SL, 31 = UTE RUESMA-INESCO TOLEDO; ninguna «Empresa N»; las mismas 3. Selector en el navegador confirmado por el humano. Copia a `azure-apps` hecha (`a16a4e0`).

**Aviso.** El literal de la empresa 1 pasa de «Construcciones Ruesma» a
**«CONSTRUCCIONES RUESMA»** (el de Sigrid). Si cambia `auxemp` en Sigrid, el
sync de maestros falla entero (consta en `azure-apps/dedicacion.md`).
Automejoras → `arnes-base` (`620b83d`, `e964f10`).

**Con F-032 cerrada, F-022, F-023, F-024 y F-032 quedan listas para
desplegarse juntas.**

Informes: `progress/impl_F-032.md`, `progress/review_F-032.md`,
`progress/mutacion_F-032.md`. Detalle de sesión retirado de `current.md`:

## F-032 · Nombres de empresa sincronizados desde Sigrid

- Rama `feature/F-032-empresas-desde-sigrid`. Plan confirmado por el humano
  el 2026-10-01, con la decisión abierta cerrada: una empresa de baja o
  desactivada con trabajadores activos se enseña marcada «(de baja)», nunca
  oculta (`features.json`).
- **Implementer terminado**: 11 commits (`4e4f070` … `106e345`), tabla
  `empresa` desde `auxemp`, preview con las empresas leídas, `/empresas` con
  nombre y `de_baja` de la tabla, fuera `empresas.nombres`; el front solo
  pinta «(de baja)». Mutación con muestreo estándar: 2 supervivientes
  reproducidos a mano y cazados con tests nuevos. Desviación declarada: tests
  de F-024 que fijaban `empresas.nombres` sustituidos por su equivalente
  sobre la tabla, sin cambiar valores esperados. Review pasada 1
  (`progress/review_F-032.md`): código, tests y campaña **bien**;
  CHANGES_REQUESTED solo por el rastro (faltaban aquí el comando exacto de la
  manual y la copia pendiente a `azure-apps`; corregido). Observaciones:
  `resumir_empresas` del preview no hace `strip` del nombre y `sync_en` solo
  se fija al alta, **descartadas por escrito**: el preview es diagnóstico y la
  tabla guarda el nombre limpio; `sync_en` se comporta igual que en
  `trabajador` y `obra`. El cambio de literal de la empresa 1 se avisa al
  humano. Automejora → encargo `620b83d` en `arnes-base`. Pasada 2: rechazada porque el comando de la
  manual apuntaba al scratchpad de la sesión (ruta con UUID: `init.sh` en
  rojo). El script pasa a `scripts/verif_f032_empresas.ps1`. **Pasada 3:
  APPROVED**; su automejora ya estaba en `arnes-base` (`e964f10`).
  **Mergeada a `dev`**; faltan la MANUAL y la copia a `azure-apps` para `done`.

#### Verificación MANUAL (humano) de F-032

1. **Sync real en local.** Arrancar la api de esta rama con `python main.py`
   desde `services/dedicacion-api` (así `create_all` crea la tabla `empresa`).
   Lanzar el script versionado (solo lectura de Sigrid; el sync escribe solo
   en la BBDD local):
   `powershell -ExecutionPolicy Bypass -File scripts/verif_f032_empresas.ps1`
   desde la raíz del repo.
   Hace `GET http://localhost:8090/api/v1/sync/preview` (esperado:
   `empresas.leidas` ≥ 19), `POST http://localhost:8090/api/v1/sync`
   (esperado: bloque `empresas` en la respuesta) y
   `GET http://localhost:8090/api/v1/empresas` (esperado: por defecto 1;
   18 = `RUESMA SERVICIOS SL`; 31 = `UTE RUESMA-INESCO TOLEDO`; ninguna
   «Empresa N»; las mismas 3 empresas que antes). Contraste:
   `progress/explore_nombres_empresas.md`. Resultado: _pendiente_.
2. **Selector en `http://localhost:8080`**: enseña 18 = RUESMA SERVICIOS SL,
   31 = UTE RUESMA-INESCO TOLEDO y **1 = CONSTRUCCIONES RUESMA** (el literal
   cambia al de Sigrid: antes «Construcciones Ruesma» de `config.yaml`). Si
   alguna con trabajadores activos está de baja, sale «(de baja)».
   Resultado: _pendiente_.

#### Pendiente antes del `done` (líder, con autorización del humano)

- **Copia a `azure-apps/dedicacion.md`**, como en F-022 y F-024: cabecera,
  fila de `sigrid-api` de §1, árbol de §2 (tabla `empresa`), párrafo de
  `GET /api/v1/empresas` (`de_baja`) y fila nueva de `auxemp` en «qué se
  rompe». Commit en `azure-apps`. Resultado: _pendiente_.

## 2026-10-02 · Detalle de sesión retirado de `current.md` (F-034, F-026, despliegue)

> Se reescribió `current.md` entero a petición de la review 2 de F-026: había
> crecido a base de parches y se contradecía. Este es el texto retirado, tal cual.

**F-034 en curso** (review APROBADA; faltan T8, T9 y la aceptación de M4 para
`done`). F-032 se cerró el 2026-10-01 (resumen en `history.md`). El arnés es la **1.7.3**.

> **2026-10-01, en curso:** el humano aclara que las OBRAS (incluida la
> postventa) son siempre de Construcciones Ruesma; los trabajadores, de varias
> empresas. F-024 se desplegó con la regla contraria y **los trabajadores de
> la 18 y la 31 no pueden registrar en producción**. Entra **F-034** con
> prioridad 1; spec **aprobada** por el humano con D1-D5 (`edab7d9`);
> plan confirmado. **BLOCKED (2026-10-01)**: el implementer
> paró antes de escribir código porque la lista cerrada de tests que cambian
> (design §6) se quedó corta: 4 tests de F-024 (R17 registro, R10 cuadrante,
> R6 y R6/R13 rutas) cambian como consecuencia directa de R1/R3 y no estaban
> en la lista (`progress/impl_F-034.md`, «Motivo del bloqueo»). El humano acepta
> (2026-10-02): `in_progress` de nuevo; §6 completado (`ba55567`).
> **Implementer terminado** (`ef56e2d` … `573ee1e`, `progress/impl_F-034.md`);
> **review APROBADA** (`progress/review_F-034.md`). Manuales, copia a
> `azure-apps` y aceptación de M4: sección «F-034 · pendiente» más abajo.
> **F-034 está en `dev` pero NO se despliega sola**: va con F-026.
> Se despliega **junto con F-026**.
> **F-026**: decisión del humano 2026-10-01, «no debe buscar por empleado sino
> por recurso»: el sync parte de los RECURSOS activos (sin fecha de baja) con
> código de hora mes; la ficha de empleado es opcional (solo DNI); la api
> manda al transfer el recurso exacto. Spec aprobada por el
> humano el 2026-10-02 con la enmienda (`56cfd3e`): clave = `res.ide` sin
> migración (vaciado de los datos de prueba al desplegar, con autorización
> expresa), vigencia por mes con ventana de bajas, D2 y D4-D7. `dev` (con
> F-034) traído a su rama; **BLOCKED (2026-10-02) en T2**: la lista cerrada de
> tests que cambian (design §7) se queda corta, como pasó en F-034. T1 hecha
> (`3627a6b`); T2 hecha pero guardada en `stash@{0}` para no dejar la rama en
> rojo. El implementer listó de antemano lo que tocarán T2-T9 (A1-A8 en F-023,
> B1 en F-024, C1-C3 dobles): `progress/impl_F-026.md`. **El humano aprueba
> (2026-10-02)** la ampliación y un cambio de método para el resto de F-026
> (cambios de test consecuencia directa de un requisito, declarados en tabla y
> verificados uno a uno por el reviewer; ver `features.json`). `in_progress`
> de nuevo. **Implementer terminado** (`75271a3` … `1bdb08b`,
> `progress/impl_F-026.md`): mutación 50/56 con 6 equivalentes justificados.
> Review pasada 1: **CHANGES_REQUESTED** por un solo punto de evidencia: 5 de
> los 6 supervivientes de `prueba_escritura_porcentajes.py` no son equivalentes
> (duplican `registro_id`/`synckey` o quitan el centinela `recurso_ide: 0`).
> Ciclo 2 hecho (`df7e94c` … `bc4cf86`): test R20 que fija
> `registro_id` únicos y `recurso_ide` 0 en el script; campaña 55/56; queda el
> nº 5 (`900003→900004`, identificador arbitrario) como equivalente, **pendiente
> de aceptación del humano**. **Reviewer, pasada 2, lanzado.** Manuales en «F-026 · pendiente» más abajo. F-034 queda `blocked` solo por su T9, que el
> humano hará junto con las manuales de F-026 (el líder le guía).
> **F-025** tiene la spec aprobada (con D4 cambiada por esta regla) y espera
> turno en su rama. Orden: F-034 + F-026 (un solo despliegue) → F-025.
> **Aviso a usuarios hasta F-025:** no registrar postventa en las obras CP ni
> OT (la cascada vigente de P5 las casa con partidas ajenas y se escribiría en
> real).
> **Pendiente de respuesta del humano:** el plan de correcciones de la review
> del despliegue (`progress/review_despliegue_20261001.md`) y si F-017 se hace
> en real con Administración delante.

### ⚠ DESPLEGADO EN MODO REAL (2026-10-01)

- **Despliegue** de F-022, F-023, F-024 y F-032 lanzado por el humano con
  `infra/redeploy_dedicacion.ps1` (el permiso del entorno no dejó lanzarlo al
  líder). Imágenes `transfer:r20261001-1805`, `api:r20261001-1807`,
  `front:r20261001-1808`; las tres revisiones `…--r20261001180529` activas y
  listas. La api aplicó el esquema al arrancar (`ALTER … ADD COLUMN empresa`
  en `trabajador` y `obra`; tabla `empresa` por `create_all`). Ya se ha hecho
  un sync en producción: 536 recursos fuera por fecha de baja, 38 empresas.
- **El transfer escribe DE VERDAD** (`OBRA_PRUEBAS_FORZAR=false`) por orden
  expresa del humano, a sabiendas de F-017, F-026 y F-011 (anotado en F-018).
  **Incidente durante el despliegue:** el humano cambió a real ANTES de
  desplegar y durante un rato corrió el transfer VIEJO en real (revisión
  `--0000001`, sin F-022). Comprobado en los logs: en ese tiempo y después
  solo hubo **preflights**, **ningún `ejecutar`**; no se escribió nada en
  Sigrid.
- **El primer despliegue falló** al escribir `infra/imagenes.json`: causa raíz
  encontrada (en PowerShell `$inventario` pisaba `$INVENTARIO`, la ruta; es la
  misma del fallo del 2026-08-20). Hotfix del líder con autorización del
  humano en `d449a58` (rama `chore/despliegue-20261001`). **Pendiente: review
  de ese hotfix.**
- Documentación al día con el modo real: `CLAUDE.md`, `README.md`,
  `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` (§8 con el comando para volver
  a pruebas) y su copia en `azure-apps`.

### F-034 · pendiente antes del `done`

- **T8 — CUMPLIDA. Copia a `azure-apps/dedicacion.md`**,
  literal, de las piezas de T7: los puntos de `#regla-empresa` cambiados en
  `docs/ARCHITECTURE.md` y, de `docs/INTEGRACION.md`, la cabecera, la fila
  `EMPRESA_IMPUTACION` de §3 y el párrafo «Una línea sin empresa no se
  registra» de §9 (`git diff d34e4a1 -- docs/`). Commit en `azure-apps`.
  **Resultado: HECHA (2026-10-02)**, commit `b4d5340` en `azure-apps`, marcada
  «aún NO desplegado». (ARCHITECTURE no tiene copia en `azure-apps`.)
- **T9 (humano, R13, D5): preflight en local, solo lectura. Se hará JUNTO con
  las verificaciones de F-026 (decisión del humano 2026-10-02); el líder le
  guía cuando esté listo.** Transfer local
  con `OBRA_PRUEBAS_FORZAR=true` en su `.env`; api y front de esta rama
  (`python main.py` en cada servicio). En `http://localhost:8080/?empresa=18`:
  las obras ofrecidas son las de Construcciones Ruesma; dar a un trabajador
  de la 18 una línea en una de ellas en 2026-09 (solo BBDD local). Después,
  desde Git Bash:
  `curl -s -X POST "http://localhost:8090/api/v1/periodos/2026/9/registro/preflight?empresa=18" -H "Content-Type: application/json" -d "{}"`.
  **Esperado:** `ok: true` por obra, `obra_origen.empresa` = 1 y la acción de
  esa línea `escribir`, no `omitir` por empresa. **No lanzar
  `registro/ejecutar`.** Resultado: _pendiente_.
- **Tras desplegar (humano, no bloquea el `done`):** cuadrante de producción
  con `?empresa=18`: obras de Construcciones Ruesma, **sin pulsar Registrar**.
- **M4 — ACEPTADO. Mutante equivalente.** En
  `RegistroSigrid` `filtro.por_defecto` y `filtro.empresa_obras` salen del
  mismo ajuste (D1), así que cambiar uno por otro no lo distingue ningún test;
  reproducido por el reviewer (RM5). **ACEPTADO por el humano el 2026-10-02.**
- **Despliegue:** junto con F-026 (decisión del humano). No se despliega sola.
- Observación de la review: una corrida de la campaña dio 3 supervivientes
  que no se reprodujeron en copia aislada. Si vuelve a pasar, encargo en
  `arnes-base` (es la misma familia que el de la caché previa de F-022).

### F-026 · pendiente antes del `done`

El humano las hará **junto con la T9 de F-034** (el líder le guía con un
script versionado cuando la review apruebe).

- **T14 (R24), local, vaciado con autorización del humano + sync.**
  `cd infra; .\vaciar_datos_prueba_dedicacion.ps1 -Local` (esperado: solo el
  plan) y `.\vaciar_datos_prueba_dedicacion.ps1 -Local -Confirmar` (pide la
  contraseña de `$env:PGUSER` o `postgres`; esperado: recuento antes, la
  sentencia, recuento 0/0/0/0). API de la rama
  (`cd services\dedicacion-api; .venv\Scripts\python main.py`);
  `GET http://localhost:8090/api/v1/sync/preview` (esperado:
  `empleados.ventana_baja` = día 1 del mes anterior o del ABIERTO más antiguo;
  `posible_misma_persona` con `MO/0061` y `MO/0736`) y
  `POST http://localhost:8090/api/v1/sync`. En la base:
  `SELECT ide, cod, empresa, activo, fecha_baja FROM trabajador WHERE cod IN ('MO/0772','MO/0759','MO/0760','MO/0762','MO/0774','MO/0775','MO/0776','MO/0777','MO/0779','MO/0496') AND empresa = 1`
  (esperado: diez activos, `ide` = su `res.ide`) y
  `SELECT COUNT(*) FROM trabajador WHERE fecha_baja < <ventana_baja>` (0).
  Un recurso con `fecha_baja` en el mes en curso sale en ese mes y no en el
  siguiente. Resultado: _pendiente_.
- **T15 (R25), preflight de SOLO LECTURA** con el transfer local en modo
  pruebas (`OBRA_PRUEBAS_FORZAR=true`; `cd services\dedicacion-transfer;
  .venv\Scripts\python main.py`): dar a Eusebio (`1-MO/0772`) una línea en un
  periodo local y
  `curl -X POST http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight -H "Content-Type: application/json" -d "{}"`.
  Esperado: su acción `escribir` con `recurso_ide` = su `res.ide`; ninguna
  omitida por «la línea no trae el recurso del trabajador»; `no_vigentes: []`.
  **NO lanzar `registro/ejecutar`.** Resultado: _pendiente_.
- **T16 (líder, con autorización del humano): copia a `azure-apps/dedicacion.md`**
  de las piezas de T12 de `docs/INTEGRACION.md` (cabecera, avisos, vaciado en
  §2, contrato de la línea en §9, dos filas en cada tabla de §7). Commit en
  `azure-apps`. Resultado: _pendiente_.
- **Despliegue conjunto F-034 + F-026 (D7)**, `infra/README_dedicacion.md` §3
  bis: republicar transfer y api juntos → vaciado en Azure (plan y
  `-Confirmar`, **autorización expresa del humano**) → `sync/preview` → `sync`.
  El transfer desplegado escribe de verdad: **nada de `registro/ejecutar`
  hasta terminar**.
- **Superviviente nº 5 (humano): aceptar por escrito el equivalente**
  `prueba_escritura_porcentajes.py:53` `900003→900004` (ver
  `progress/mutacion_F-026.md`). Resultado: _pendiente_.
- **Observaciones del implementer, propuestas al humano como features
  aparte:** (a) la fila que devuelven guardar y deshacer no conoce el mes: un
  trabajador no vigente con líneas vuelve con el `activo` del ORM hasta
  recargar; (b) el front no enseña `no_vigentes`: esas líneas no se
  registran y el usuario no ve el motivo. (c) Arnés: la mutación con
  `workers > 1` volvió a dar falsos supervivientes (tercera vez: F-022, F-034,
  F-026) → se añade al encargo de `arnes-base` de la caché previa.

## 2026-10-02 · F-034 · Las obras son siempre de Construcciones Ruesma

Rama `feature/F-034-obras-siempre-ruesma` · `sdd: true` · rigor `critico` ·
**APROBADO** por el reviewer a la primera. Nace de la aclaración del humano del
2026-10-01: los trabajadores son de varias empresas, pero las obras (postventa
incluida) son siempre de Construcciones Ruesma; F-024 se había desplegado con la
regla contraria y los trabajadores de la 18 y la 31 no podían registrar.

**Qué cambió.** El selector de empresa filtra solo trabajadores; las obras
ofrecidas son siempre las de la empresa de las obras (`EMPRESA_IMPUTACION`, D1);
cada línea del registro viaja con esa empresa, no con la elegida. El transfer no
cambia. Un primer implementer se bloqueó porque la lista cerrada de tests que
cambian se quedó corta (4 casos); el humano la amplió.

**Verificado.** Suites relanzadas sin caché por el reviewer (api 368, front 21,
transfer 317); cobertura 100 %; mutación con 15 mutantes manuales (14 muertos y
**M4 equivalente, aceptado por el humano**). **T8** (copia a `azure-apps`,
`b4d5340`) y **T9** cumplidas: preflight local con la 18 elegida, la línea de
MO/0003 en una obra de Ruesma sale para escribir; parte visual confirmada.

**Pendiente.** En `dev`, sin desplegar: va con F-026. Tras desplegar, mirar el
cuadrante de producción con `?empresa=18` sin pulsar Registrar.

Informes: `progress/impl_F-034.md`, `progress/review_F-034.md`,
`progress/mutacion_F-034.md`. Sección retirada de `current.md`:

## F-034 · Obras siempre de Construcciones Ruesma (`blocked` solo por T9)

- En `dev` (`d6656ad`). Review APROBADA; T8 (copia a `azure-apps`, `b4d5340`)
  hecha; M4 aceptado por el humano el 2026-10-02.
- **T9 (humano), se hace junto con T14/T15 de F-026.** Transfer local con
  `OBRA_PRUEBAS_FORZAR=true`; api y front de la rama (`python main.py` en
  cada servicio). En `http://localhost:8080/?empresa=18` las obras ofrecidas
  son las de Construcciones Ruesma; dar a un trabajador de la 18 una línea en
  una de ellas y, desde Git Bash,
  `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight?empresa=18" -H "Content-Type: application/json" -d "{}"`.
  **Esperado:** `ok: true`, `obra_origen.empresa` = 1 y la acción de esa línea
  `escribir`, no `omitir` por empresa. **No lanzar `registro/ejecutar`.**
  Resultado: _pendiente_.
- **Tras desplegar (humano, no bloquea el `done`):** cuadrante de producción
  con `?empresa=18`: obras de Construcciones Ruesma, **sin pulsar Registrar**.

## 2026-10-02 · F-026 · El sync parte del recurso (el caso Eusebio Vindel Duro)

Rama `feature/F-026-recursos-sin-ficha-empleado` · `sdd: true` · rigor
`critico` · **APROBADO** por el reviewer en la pasada 3 (la 1 pidió evidencia:
5 «equivalentes» que no lo eran; la 2, solo el rastro de `current.md`, que se
reescribió entero).

**Decisiones del humano.** «No debe buscar por empleado sino por recurso»;
«solo deben aparecer empleados que no estén inactivos y que tengan código hora
mes»; sin migración (lo de producción son pruebas: se vacía al desplegar);
un recurso dado de baja en el mes sigue visible ese mes. Y un cambio de método
para los tests anteriores (consecuencia directa de un requisito, declarados en
tabla y verificados fila a fila por el reviewer), tras un segundo bloqueo por
la lista cerrada de tests.

**Qué cambió.** El sync parte de `res` (persona, código M*, vigente según la
ventana de bajas); la ficha de empleado solo aporta el DNI; la clave del
trabajador es el `res.ide`; vigencia por mes en cuadrante y registro
(`no_vigentes`); la api manda `recurso_ide` y el transfer ya no lo elige por
`res.conide`. Script `infra/vaciar_datos_prueba_dedicacion.ps1` (plan por
defecto, `-Confirmar`, una sola `TRUNCATE … CONTINUE IDENTITY`, solo la base
`dedicacion`).

**Verificado.** Suites sin caché (api 440, transfer 329/330, front 21);
mutación 55/56 con el **nº 5 equivalente, aceptado por el humano**. MANUAL con
`scripts/verif_f034_f026.ps1` tras el vaciado local: los diez recursos del
diagnóstico activos; Eusebio (MO/0772) sale para escribir con su recurso
2798037; activos por empresa 183/8/1/4. Copia a `azure-apps`: `67d0364`.

**Pendiente.** Desplegar con F-034 y vaciar los datos de prueba en Azure con
autorización expresa. Propuestas al humano como features aparte: la fila de
guardar/deshacer no conoce el mes, y el front no enseña `no_vigentes`.

Informes: `progress/impl_F-026.md`, `progress/review_F-026.md`,
`progress/mutacion_F-026.md`. Sección retirada de `current.md`:

## F-026 · El sync parte del recurso (en curso)

- Rama `feature/F-026-recursos-sin-ficha-empleado` (lleva `dev` con F-034).
  Spec aprobada con la enmienda del humano del 2026-10-02 (clave = `res.ide`
  sin migración; vaciado de los datos de prueba al desplegar; vigencia por
  mes) y con el cambio de método para los tests anteriores (`features.json`).
- Implementer: `progress/impl_F-026.md`. Review: `progress/review_F-026.md`
  (pasada 1, un punto de evidencia resuelto en el ciclo 2; pasada 2, código y
  campaña 55/56 correctos, cambios solo en este fichero; **pasada 3, APROBADA**).
- **Script versionado para T9 + T14 + T15 juntas:**
  `powershell -ExecutionPolicy Bypass -File scripts/verif_f034_f026.ps1`
  (desde la raíz; antes, el vaciado local con autorización y transfer + api
  locales; el script crea un periodo y dos asignaciones de prueba SOLO en la
  BBDD local y lanza dos preflight; nunca `ejecutar`). Esperado:
  `RESULTADO: OK`.
- **Pendiente antes del `done`:**
  - **Superviviente nº 5 (humano):** aceptar por escrito el equivalente
    `prueba_escritura_porcentajes.py:53` `900003→900004`
    (`progress/mutacion_F-026.md`). Resultado: _pendiente_.
  - **T14 (R24) — CUMPLIDA.** **Resultado real (2026-10-02, humano, `scripts/verif_f034_f026.ps1`, transfer
  local en modo pruebas, api y front de `dev` con F-034 y F-026, tras el vaciado
  local): CUMPLIDA.** Vaciado local: 35/60/12/606 → 0/0/0/0.
    Los 10 recursos del diagnóstico activos en la 1; activos por empresa 183 / 8 / 1 / 4
    (1 / 18 / 25 / 31). Texto original:
    `cd infra; .\vaciar_datos_prueba_dedicacion.ps1 -Local` (esperado: solo el
    plan) y `.\vaciar_datos_prueba_dedicacion.ps1 -Local -Confirmar` (pide la
    contraseña de `$env:PGUSER` o `postgres`; esperado: recuento antes, la
    sentencia, recuento 0/0/0/0). API de la rama
    (`cd services\dedicacion-api; .venv\Scripts\python main.py`);
    `GET http://localhost:8090/api/v1/sync/preview` (esperado:
    `empleados.ventana_baja` = día 1 del mes anterior o del ABIERTO más
    antiguo; `posible_misma_persona` con `MO/0061` y `MO/0736`) y
    `POST http://localhost:8090/api/v1/sync`. En la base:
    `SELECT ide, cod, empresa, activo, fecha_baja FROM trabajador WHERE cod IN ('MO/0772','MO/0759','MO/0760','MO/0762','MO/0774','MO/0775','MO/0776','MO/0777','MO/0779','MO/0496') AND empresa = 1`
    (esperado: diez activos, `ide` = su `res.ide`) y
    `SELECT COUNT(*) FROM trabajador WHERE fecha_baja < <ventana_baja>` (0). Un
    recurso con `fecha_baja` en el mes en curso sale en ese mes y no en el
    siguiente. Resultado: _pendiente_.
  - **T15 (R25) — CUMPLIDA.** Eusebio (MO/0772) sale `escribir` con
    `recurso_ide` 2798037 (su `res.ide`); `no_vigentes: []`. Texto original:
    **preflight de SOLO LECTURA** con el transfer local en modo
    pruebas (`OBRA_PRUEBAS_FORZAR=true`;
    `cd services\dedicacion-transfer; .venv\Scripts\python main.py`): dar a
    Eusebio (`1-MO/0772`) una línea en un periodo local y
    `curl -X POST http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight -H "Content-Type: application/json" -d "{}"`.
    Esperado: su acción `escribir` con `recurso_ide` = su `res.ide`; ninguna
    omitida por «la línea no trae el recurso del trabajador»;
    `no_vigentes: []`. **NO lanzar `registro/ejecutar`.** Resultado: _pendiente_.
  - **T16 (líder, con autorización del humano): copia a
    `azure-apps/dedicacion.md`** de las piezas de T12 de `docs/INTEGRACION.md`
    (cabecera, avisos, vaciado en §2, contrato de la línea en §9, dos filas en
    cada tabla de §7). Commit en `azure-apps`. **HECHA**: `67d0364` en `azure-apps`.
- **Observaciones de las reviews, recogidas o descartadas por escrito:**
  - Frase de `infra/README_dedicacion.md` §3 bis («sus líneas llevarían un
    `emp.ide`… que el transfer omite (P1)»): **corregida** (tras el sync esas
    líneas son de trabajadores no vigentes y van a `no_vigentes`).
  - `ruff I001` (orden de imports) en 4 ficheros de test nuevos:
    **descartada** como deuda de estilo; `ruff` no bloquea (193 avisos previos)
    y tocar los tests ahora obligaría a otra pasada de review. Entra en F-006
    (sanear suites).
  - Fila tras guardar/deshacer sin conocer el mes, y el front sin enseñar
    `no_vigentes`: **propuestas al humano como features pequeñas**, pendientes
    de su decisión.
  - Automejoras (RM5: «que la suite pase con el mutante prueba que sobrevive,
    no que sea equivalente»; `init.sh` compruebe que la cabecera de
    `current.md` nombra la `in_progress`) → encargo `69df67b` en `arnes-base`.
  - Falsos supervivientes con `workers > 1` (tercera feature seguida) →
    añadido al encargo de `arnes-base` (`affff93`).

## 2026-10-02 · Despliegue de F-034 y F-026

Lanzado por el humano con `infra/redeploy_dedicacion.ps1` (los tres servicios):
`transfer:r20261002-1705`, `api:r20261002-1706`, `front:r20261002-1708`; la api
añadió `trabajador.fecha_baja` al arrancar; el transfer conserva el modo real.
**Vaciado de los datos de prueba** de la base `dedicacion` con autorización
expresa del humano: el script falló contra Azure (`az … -p` en Windows pasa por
`cmd.exe` y corrompe la contraseña; el reintento sin cifrar lo rechaza
`pg_hba`, como debe) y se hizo a mano con `psql` (`PGPASSWORD`,
`PGSSLMODE=require`) con las mismas tres sentencias: 312/376/7/207 → 0/0/0/0.
**Sync**: preview con 196 trabajadores, ventana de bajas 2026-09-01, 1.034
excluidos por baja anterior, un posible duplicado avisado (MO/0061 y MO/0736),
38 empresas. El humano confirma que Eusebio Vindel Duro aparece. Corrección del
script: F-035.

## ⚠ Despliegue conjunto F-034 + F-026 (pendiente; lo lanza el humano)

`infra/README_dedicacion.md` §3 bis: republicar transfer y api juntos →
vaciado de los datos de prueba en Azure (`infra/vaciar_datos_prueba_dedicacion.ps1`,
plan y `-Confirmar`, **autorización expresa del humano**) →
`GET /api/v1/sync/preview` → `POST /api/v1/sync`. El transfer desplegado
escribe de verdad: **nada de `registro/ejecutar` hasta terminar**. Lo lanza
el humano (el permiso del entorno no deja desplegar al líder).

## 2026-10-03 · F-035 · El vaciado contra Azure sin pasar la contraseña por `cmd.exe`

Rama `feature/F-035-vaciado-psql-azure` · `sdd: false` · rigor `estandar` ·
**APROBADO** por el reviewer en la pasada 3. Nace del despliegue del
2026-10-02: `az … -p <clave>` pasa por `cmd.exe` (`az` es un `.cmd`) y
corrompe la contraseña.

**Qué cambió.** `vaciar_datos_prueba_dedicacion.ps1` usa `psql` también en
Azure (FQDN por `az … show`, `PGPASSWORD` y `PGSSLMODE=require` solo durante la
llamada), lee la contraseña de `PG-PASSWORD` del Key Vault (salida de `az`,
nunca argumento; `Read-Host` de respaldo) y tiene `-SoloRecuento`, que cuenta
sin escribir. Los avisos son condicionales: contraseña que no coincide frente a
regla de firewall de la IP. `crear_base` y `add_secrets` rechazan contraseñas
con `" & | < > ^ % )` antes de llamar a `az`. Revisión del resto de `infra/` en
`infra/README_dedicacion.md` §6 bis.

**Ciclos.** Review 1: cambios pedidos solo por la tabla reproducible de la
campaña manual; el humano añadió `)` a la clase (hallazgo del reviewer). MANUAL
1 fallida por la contraseña tecleada (10 caracteres frente a 14 en el Key
Vault), no por el script: el humano aprobó leerla del Key Vault (ciclo 3).

**Verificado.** 418 passed; mutación del arnés N/A (solo muta Python): campaña
manual de 31 mutantes sobre los `.ps1`, 0 supervivientes, reproducida por el
reviewer (`progress/mutacion_manual_F-035.md`). **MANUAL 2 cumplida**
(2026-10-03): contra Azure, sin pedir contraseña, recuento 0/0/1/196 y entorno
limpio. Cinco tests anteriores cambiados, todos declarados.

Informes: `progress/impl_F-035.md`, `progress/review_F-035.md`,
`progress/mutacion_manual_F-035.md`. Sección retirada de `current.md`:

## F-035 · El vaciado contra Azure sin pasar la contraseña por `cmd.exe`

- **Plan aprobado por el humano el 2026-10-02** (PARADA 1). Criterios en
  `harness/features.json`. Resumen: el vaciado usa `psql` también en Azure
  (FQDN por `az … show`, `PGPASSWORD` + `PGSSLMODE=require` solo durante la
  llamada); conmutador nuevo `-SoloRecuento` (cuenta y sale, sin escribir);
  `crear_base` y `add_secrets` rechazan contraseñas con `" & | < > ^ %` y
  `)` (este último aprobado por el humano tras la review 1)
  antes de llamar a `az`; resultado de la revisión de `infra/` en
  `infra/README_dedicacion.md`.
- **Fuera:** volver a vaciar producción, cambiar la contraseña de
  `dedicacion_app`, firewall o cualquier cosa del servidor, `azure-apps`.
- **Tests anteriores que cambian (declarados, tabla en `impl_F-035.md`):**
  tres de `tests/test_f026_vaciado.py`: `…solo_en_la_base_dedicacion` (Azure
  pasa a psql) y, por el conmutador nuevo `-SoloRecuento` aprobado en el plan,
  `…parametros_confirmar_y_local` y `…sin_confirmar_sale_antes_de_conectar`.
  El plan solo nombraba el primero; los otros dos son consecuencia directa de
  `-SoloRecuento` (método aprobado por el humano: declarados y verificados
  fila a fila por el reviewer).
- **Estado:** review 1 → **CAMBIOS PEDIDOS** (`progress/review_F-035.md`):
  código y tests correctos; bloquea solo C4 bis, la campaña manual de 19
  mutantes no está como tabla reproducible. **Ciclo 2 hecho** (`301dfed`,
  `cffd850`, `eb224b5`): `)` en la clase de caracteres, con test y README;
  tabla en `progress/mutacion_manual_F-035.md` (21 mutantes, 0
  supervivientes, script incrustado). **Review 2: APROBADO** (tabla
  reproducida 23/23 por el reviewer) y **mergeada en `dev`**.
- **MANUAL 1 (2026-10-03, humano): FALLA** con `password authentication
  failed`, pero **no por el script**: comparadas en memoria, la contraseña
  tecleada (10 caracteres) no es la del Key Vault (14). El servidor y el FQDN
  responden; el aviso de firewall salió aunque el error era de contraseña.
- **Ciclo 3 aprobado por el humano (2026-10-03):** en Azure la contraseña se
  lee de `PG-PASSWORD` del Key Vault (salida de `az`, nunca argumento), con
  `Read-Host` de respaldo; el aviso de firewall solo ante tiempo agotado o
  `no pg_hba.conf entry`. **Ciclo 3 hecho** (`5a1eb13`…`89f1dac`, 418 passed;
  mutación manual 31 mutantes, 0 supervivientes). Cambian además dos tests
  propios de F-035 (`…r1_fqdn_por_show_de_solo_lectura`,
  `…r3_el_error_de_azure_apunta_a_la_ip_propia`), declarados en la tabla de
  `impl_F-035.md` con los tres de F-026. **Review 3: APROBADO** (33/33
  mutantes reproducidos) y mergeada en `dev`. Observación recogida: si
  PG-PASSWORD llevara caracteres no ASCII, PS 5.1 podría decodificar mal la
  salida de `az`; la MANUAL 2 lo comprueba con la contraseña real. **Para el
  `done` solo falta la MANUAL 2.**
- **Observaciones de la review 1, recogidas:** `)` → aprobado y en el ciclo 2;
  criterio 6 de `features.json` → ya dice «tres tests»; automejora (tabla
  manual en fichero propio) → `arnes-base`, encargo de mutantes manuales
  declarativos, commit `e9bc34a`.
- **Observación del implementer, no aplicada (fuera del plan):** en
  `crear_base_dedicacion.ps1` los pasos 1-2 corren antes de pedir las
  contraseñas, así que una contraseña rechazada llega tras ellos. **Propuesta
  al humano el 2026-10-02**, pendiente de su decisión (sería otra feature).
- **MANUAL (humano, NO escribe nada):** desde una consola nueva con `az login`:
  ```powershell
  cd C:\Users\pgris\PycharmProjects\porcentajes\infra
  $env:Path = "C:\Program Files\PostgreSQL\16\bin;$env:Path"
  . .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
  .\vaciar_datos_prueba_dedicacion.ps1 -Local -SoloRecuento
  .\vaciar_datos_prueba_dedicacion.ps1 -SoloRecuento
  Test-Path Env:PGPASSWORD ; Test-Path Env:PGSSLMODE
  ```
  Esperado: las dos cuentan filas sin «password authentication failed» y
  terminan en «SOLO RECUENTO: hecho, no se ha escrito nada»; el último
  comando da `False False`. Tras el ciclo 3, la de Azure ya no pide contraseña.
  Resultado: MANUAL 1 fallida (ver arriba); repetición _pendiente_.

## 2026-10-03 · F-025 · Obras de postventa sacadas de los capítulos de POSTV2

Rama `feature/F-025-obras-postventa-postv2` · `sdd: true` · rigor `critico` ·
**APROBADO** por el reviewer en la pasada 2 (la 1 pidió cambios solo en el
rastro de `current.md`: cabecera, «Lo siguiente» y condiciones de despliegue).

**Decisiones del humano.** D2 = B (la cascada de P5 no imputa a partidas
ajenas: fuera CP→CP.1, OT→CI.7.5); D4: solo la POSTV2 de Construcciones Ruesma
(las obras son siempre de la empresa de las obras, F-034); D6: la POSTV antigua
fuera; D8 = A (2026-10-03, tras revisar la spec contra F-034/F-026: la
obra-capítulo queda fuera; ocho tests de F-002 cambian).

**Qué cambió.** El transfer calcula el universo de postventa por petición
(`POST /api/postventa/universo`, sin arrastrar el catálogo entre llamadas) y P5
casa solo por código exacto o prefijo + letras. La api lo pide en el sync y
guarda `obra.admite_postventa`; una obra cerrada se ofrece solo como `Postv-`.
El cuadrante publica `ofrecible` y guardar rechaza líneas nuevas no ofrecibles.
El front pinta el catálogo con esas marcas.

**Verificado.** Transfer 379, api 509, front 28, raíz 418; cobertura 164/164;
mutación en serie 57/57 (la campaña en paralelo dio tres falsos supervivientes:
encargo de `arnes-base`). MANUAL del humano: **M1** 83/73, `0656` `0660` `0669`
`0689` solo `Postv-`, `CP` `OT` `191105` fuera, cuadrante igual con la 1 y la 18;
**M2** `Postv-0656` casa con el capítulo 0656 (`ide` 381828), sin partidas en la
obra sin postventa, `no_vigentes` vacío. `azure-apps`: `897587f`.

**Pendiente.** Desplegar (transfer antes o con la api, sync, retirar el aviso
de CP/OT). Detalle menor: el script de verificación muestra mal las tildes de
los nombres en la consola de PowerShell 5.1 (solo salida, no datos).

Informes: `progress/impl_F-025.md`, `progress/review_F-025.md`,
`progress/mutacion_F-025.md`, `progress/spec_F-025_revision.md`. Sección
retirada de `current.md`:

## F-025 · Obras de postventa desde los capítulos de POSTV2 (en curso)

- **Spec** (`specs/F-025-obras-postventa-postv2/`): aprobada el 2026-10-01
  (`d49348c`; D2 = B, la cascada de P5 no imputa a partidas ajenas; D4: solo la
  POSTV2 de Construcciones Ruesma; D6: la POSTV antigua fuera), revisada tras
  F-034/F-026 (`progress/spec_F-025_revision.md`) y reaprobada el 2026-10-03
  con **D8 = A** (la obra-capítulo queda fuera; `0e005fe`).
- **Implementación** (`progress/impl_F-025.md`): T1-T12 hechas. Tras el
  ciclo 2: transfer 379, api 509, front 28, raíz 418 en verde; cobertura
  164/164; mutación en serie 57/57 muertos (`progress/mutacion_F-025.md`). Tests anteriores cambiados: solo los
  de design §7.1 (tabla en el informe, §3). Falsos supervivientes de la
  campaña en paralelo → encargo de `arnes-base` (`0ecafc2`).
- **Review 1 (2026-10-03) → CAMBIOS PEDIDOS solo por este fichero**
  (`progress/review_F-025.md`): código, tests, `#regla-p5` y mutación bien.
  Corregido aquí: cabecera, «Lo siguiente» y condiciones de despliegue.
- **Observaciones de la review 1, recogidas en el ciclo 2** (implementer):
  `depurar_obras` compara el `ide` sin convertir (con `_entero`, más test);
  `_entero` deja de ser privado si lo usa otro módulo; y los 15 avisos nuevos
  de ruff de las líneas de F-025 se corrigen. **Hecho** (`c588879`,
  `e640f67`, `89f0d30`, `7fda87a`): test nuevo del `ide` en texto;
  `entero_o_none` público en `domain/normalizacion.py`; ruff 215 → 198;
  campaña en serie 57/57 muertos. **Review 2: APROBADO** (`a7779aa`).
- **Quedan para el `done`:** T10 (commit en `azure-apps`), T13 y T14, con su
  resultado real aquí. Después, desplegar con las tres condiciones de abajo.
- **MANUAL (humano, NUNCA `registro/ejecutar`)**, con api y transfer LOCALES
  desde esta rama y la api contra la BBDD local; desde la raíz:
  - **T10**: `git -C C:\Users\pgris\PycharmProjects\azure-apps diff dedicacion.md`,
    revisar y hacer el commit en `azure-apps` (**pendiente en `azure-apps`**).
  - **T13 (M1)**: `powershell -ExecutionPolicy Bypass -File scripts/verif_f025_postventa.ps1 -Paso M1`
    → esperado `RESULTADO M1: OK` (83/73, `0656` `0660` `0669` `0689` solo
    postventa, `CP` `OT` `191105` fuera). Resultado: _pendiente_.
  - **T14 (M2)**: `powershell -ExecutionPolicy Bypass -File scripts/verif_f025_postventa.ps1 -Paso M2 -Anio AAAA -Mes MM`
    → esperado `RESULTADO M2: OK`. Resultado: _pendiente_.
- **Condiciones de despliegue** (D3, `docs/INTEGRACION.md` §7, impl §7):
  1. El **transfer antes o junto con la api**: la api nueva pide el universo
     al transfer en el sync y, con el transfer viejo, el sync da 502.
  2. **Sync justo después**: la api añade `obra.admite_postventa` (DEFAULT
     false) al arrancar y, hasta el primer sync, ninguna obra ofrece `Postv-`
     y las líneas de postventa guardadas salen como no ofrecibles.
  3. Con ese despliegue **se retira el aviso de CP/OT** de «Producción, hoy».

## 2026-10-03 · Despliegue de F-025

Lanzado por el humano con `infra/redeploy_dedicacion.ps1` (los tres servicios,
orden fijo transfer → api → front, que es el que exige F-025):
`transfer:r20261003-1444`, `api:r20261003-1446`, `front:r20261003-1447`; la api
añade `obra.admite_postventa` al arrancar; el transfer conserva el modo real.
Preview de producción (2026-10-04): 526 obras, `admiten_postventa` 83,
`solo_postventa` 73, `motivo_postventa` nulo; 196 trabajadores. `azure-apps`
actualizado en el mismo trabajo.

## 2026-10-04 · F-027 · Deshacer solo lo propio

Rama `feature/F-027-deshacer-por-usuario` · `sdd: false` · rigor `estandar` ·
**APROBADO** por el reviewer a la primera.

**Decisión del humano (A).** Solo se deshace si el último cambio pendiente del
trabajador en el mes es del usuario actual; si es de otro, se bloquea (deshacer
restaura la fila entera: deshacer uno anterior borraría en silencio lo del
otro).

**Qué cambió.** `DeshacerUltimaModificacion` rechaza con `DeshacerAjeno` (409,
motivo con el nombre del otro); `puede_deshacer` por usuario en cuadrante y
filas (SQL: autor del `max(id)` pendiente por trabajador); normalización del
usuario en `domain/deshacer.py`; `#regla-deshacer` en ARCHITECTURE; cadena de
identidad en INTEGRACION (y `azure-apps`, `e4a304c`). Front sin cambios: el
botón depende de `puede_deshacer` y Ctrl+Z llama a la API, cuyo 409 enseña el
motivo. **El criterio 5 se reescribió tras la PARADA 1** para reflejar ese
comportamiento de Ctrl+Z (antes decía que Ctrl+Z dependía de `puede_deshacer`).

**Verificado.** api en verde con 25+ tests nuevos de dos usuarios; cobertura
33/33; mutación en serie 8/8 (el superviviente `frozen` se mató con un test,
como en F-025). Observación fuera de alcance, previa a F-027: no hay bloqueo de
fila entre leer el último pendiente y restaurarlo (dos peticiones simultáneas).

Informes: `progress/impl_F-027.md`, `progress/review_F-027.md`,
`progress/mutacion_F-027.md`. Sección retirada de `current.md`:

## F-027 · Deshacer solo lo propio

- **Plan aprobado por el humano el 2026-10-04 con la decisión A**: solo se
  deshace si el último cambio pendiente del trabajador en el mes es del
  usuario actual; si es de otro, se bloquea con mensaje que lo nombra.
  `puede_deshacer` por usuario. Solo api. Criterios en `features.json`.
- **Fuera:** deshacer un cambio que no sea el último, deshacer por línea,
  historial visible.
- **Estado:** implementación terminada (`progress/impl_F-027.md`): regla A
  en `DeshacerUltimaModificacion` (409 `DeshacerAjeno`, como «nada que
  deshacer»), `puede_deshacer` por usuario, normalización en
  `domain/deshacer.py`, `#regla-deshacer` en ARCHITECTURE e INTEGRACION
  (`X-Usuario` decide quién deshace). 25+ tests con dos usuarios; mutación en
  serie 8/8 muertos (`progress/mutacion_F-027.md`). Tests anteriores
  cambiados solo por firma o doble (tabla en el informe). Front sin cambios:
  Ctrl+Z llama a la API y el 409 enseña el motivo (criterio 5 reescrito con
  ese comportamiento). **Review lanzada** → `progress/review_F-027.md`.
- **`azure-apps`:** copia de la cadena de identidad en `dedicacion.md`,
  confirmada por el líder (`e4a304c`, «pendiente de desplegar»).
- **MANUAL:** ninguna antes del `done` (lo cubren los tests con dos
  usuarios). Tras desplegar, se puede mirar con dos personas.
 El arnés es la **1.7.3**.

## 2026-10-05 · Despliegue de F-027

Lanzado por el humano con `infra/redeploy_dedicacion.ps1 -Solo api`:
`api:r20261005-0915` (transfer y front sin cambios: `r20261003-1444` y
`r20261003-1447`). Sin columnas nuevas ni sync. `azure-apps` actualizado en el
mismo trabajo. Comprobación con dos personas: pendiente (en `current.md`).

## 2026-10-05 · F-025 confirmada en producción

El humano confirma que, tras el sync («Actualizar Sigrid»), el cuadrante de
producción ofrece `Postv-0656`. Se retira el aviso a usuarios de no registrar
postventa en las obras CP ni OT: con D2 = B la cascada de P5 ya no las casa con
partidas ajenas.

## 2026-10-05 · F-029 · Selección múltiple y completar hasta el 100 %

Rama `feature/F-029-seleccion-multiple-completar-100` · `sdd: true` · rigor
`estandar` · **APROBADO** por el reviewer en la pasada 2 (la 1 pidió solo
rastro: T7 sin marcar y «Lo siguiente» desfasado). Adelantada por el humano por
delante de F-021: usa el filtro «Filtrar obra…» de hoy; Sesame queda para F-021.

**Decisiones del humano (D1-D6 = A).** Destino elegido en un diálogo entre las
entradas del catálogo que casan con el filtro; normal o `Postv-` según la
entrada; el no vigente no se toca y la obra no ofrecible da 422 para todo el
lote; botón «Completar al 100 %» y tecla C; lo que falta a 0,01 con la épsilon
compartida; solo se tocan los seleccionados visibles.

**Qué cambió.** api: `POST /api/v1/periodos/{anio}/{mes}/completar`, una
transacción, un evento `COMPLETAR` deshacible por trabajador (regla F-027),
`#regla-completar`. Front: Ctrl/Shift+clic, Esc, contador, diálogo, tecla C.
Teclado anterior intacto. Nada en Sigrid.

**Verificado.** Cobertura 84/84; mutación en serie 20/20 (dos `frozen` muertos
con un test; un falso superviviente también en serie → encargo de
`arnes-base` `58403df`); ningún test anterior cambiado; `azure-apps`
`a593bd4`. **T9 cumplida por el humano** en local: «está todo ok, podemos
desplegarlo». Aclarado al humano: el deshacer tiene historial completo por
trabajador y mes (solo lo propio, sin rehacer).

Informes: `progress/impl_F-029.md`, `progress/review_F-029.md`,
`progress/mutacion_F-029.md`. Sección retirada de `current.md`:

## F-029 · Selección múltiple y completar hasta el 100 % (en curso)

- **Elegida por el humano el 2026-10-05** por delante de F-021, de la que
  dependía. La spec trabaja con el filtro de obra que YA existe en el front;
  la selección automática desde Sesame sigue siendo de F-021.
- **Estado:** spec entregada (`631273c`, `specs/F-029-seleccion-multiple-completar-100/`):
  api `POST /periodos/{a}/{m}/completar` por lote (un evento `COMPLETAR`
  deshacible por trabajador) + front con Ctrl/Shift, diálogo y botón. Lista
  cerrada de tests anteriores que cambian: **ninguno** (comprobado con un
  prototipo desechable). **Aprobada por el humano el 2026-10-05 con D1-D6 =
  A**, cerradas en todos sus sitios (`8d5172d`).
- **Implementación terminada** (`progress/impl_F-029.md`): T1-T6, T8, T10
  (`b09e333`…). Cobertura 84/84; mutación en serie 20/20 muertos tras matar
  dos `frozen` con un test (`progress/mutacion_F-029.md`); un falso
  superviviente en serie → encargo de `arnes-base` (`58403df`). Ningún test
  anterior cambiado. **Review 1: CAMBIOS PEDIDOS solo por el rastro** (T7
  sin marcar en `tasks.md` y «Lo siguiente» desfasado), corregidos por el
  líder; código, tests, mutación y docs revisados y bien. **Review 2:
  APROBADO.** Para el `done` solo falta la T9 del humano; la rama NO se
  mergea a `dev` hasta entonces (puede traer ajustes de usabilidad).
- **Condición del humano: NO se despliega hasta que pruebe la usabilidad en
  local** (T9, `tasks.md`: api y front locales desde la rama, BBDD local, sin
  Sigrid; clics, diálogo, tecla C, Ctrl+Z y regresión del teclado).
- **T7 (líder): hecha**, párrafo de §5 copiado literal a
  `azure-apps/dedicacion.md`, commit `a593bd4` («sin desplegar»).
- **T9 MANUAL (humano), pendiente:** pasos (a)-(e) en `tasks.md` T9 y
  arranque en `progress/impl_F-029.md` § «Cómo probarlo en local»: en Git
  Bash, `cd services/dedicacion-api && .venv/Scripts/python main.py` y, en
  otra, `cd services/dedicacion-front && .venv/Scripts/python main.py`;
  abrir `http://localhost:8080`. NO pulsar «Registrar en Sigrid».
  Mirar además (observación de la review 1): Ctrl/Shift+clic con el editor
  abierto repinta la tabla y el foco puede saltar. Resultado: _pendiente_.

## 2026-10-06 · F-037 · Rastro de spec retirado de `current.md` (review 1)

## F-037 · El registro genera el asiento analítico de la obra (en curso)

- **Pedida por el humano el 2026-10-05** a partir del correo de Juan Romero
  «ARBOL ANALITICO OBRAS» (2026-09-29): cuentas analíticas por centro de
  coste de la obra; ejemplo, asiento con 6XX desglosado al 100 % en
  `0702.CP0004`. Escritura en Sigrid: rigor crítico, solo el transfer.
- **Exploración** (`progress/explore_F-037.md`): Sigrid YA genera el asiento
  analítico de cada parte (documento `ANA`, uno por obra y mes, lo lanza
  Administración por lotes): debe a `hmores.caaide` de cada línea, haber a
  `res.caaconide`; el 6XX lo pone la nómina. **El transfer escribe hoy
  `caaide = 0`**, así que sus líneas no entrarían en el ANA. Cero líneas
  `porcentajes:` en Sigrid a día de hoy.
- **Spec entregada** (`5dd3d75`), recomendada D1 = A: el transfer rellena
  `caaide` (`<obra>.CIMOxx` del tipo de hora) y no escribe asientos.
  **Espera al humano / Juan Romero** con D1-D11 abiertas
  (requirements §6).
- **Ajustada con la respuesta de Juan del 2026-10-05** (`4c3d7d1`): la
  cuenta analítica sale del TIPO DE HORA del recurso (540 de 540 líneas
  manuales), no de la partida; el centro (`hmores.cenide`) ya lo escribe
  bien el transfer; «Contabiliza parte…» deja el parte en `con.est = 10`
  (502 partes con ANA desde 2025). T0 bloquea: preguntas a Juan sobre el
  botón, MPRL (`CIMO16` o `CIMO04`) y escribir en un parte contabilizado.
- **Decisiones del humano (2026-10-05) aplicadas** (`52e1c02`): la cuenta
  sale del recurso con la regla de `partes` F-021 (`reshor.caaide`,
  subcuenta en el centro de la obra destino); un parte contabilizado va a
  un **complementario** (en Sigrid no hay convención: 9 casos de dos partes
  por obra y mes, sin enlace). **Abiertas para el humano:** D8, D10, D12,
  D13, D14 y **D15** (copiar `cuenta_analitica.py` de `partes` = ampliar la
  lista cerrada de `CLAUDE.md`, decisión expresa).
- **2026-10-06: aprobada por el humano con A en D8, D10 y D12-D15**
  (`3e6c7c4`); `CLAUDE.md` amplía la lista cerrada con `cuenta_analitica.py`
  (`b7ef1e6`). «Lo aprendido en partes» en design §13: la F-031 de `partes`
  (`feature/F-031-asiento-analitico`, en curso allí) añade el respaldo de la
  partida (R3) y entiende «cerrado» como estado ≠ 1. **Pendiente del humano:**
  D16 (qué estado manda al complementario) y si se espera a que la F-031 de
  `partes` llegue a su `dev` antes de copiar (sin ella, R3 queda `blocked`).
- **Riesgo vivo:** el transfer desplegado escribe en real; lo que se
  registre antes de F-037 queda con `caaide = 0` y fuera del ANA.
- **Fuera del proyecto (aviso al humano):** `partes-persistencia` también
  escribe `caaide = 0` en sus líneas `partes:`.

- **2026-10-06, nueva instrucción del humano:** no esperar a que la F-031 de
  `partes` llegue a su `dev`: revisarla en su rama y copiarla ADAPTADA, porque
  porcentajes y partes escriben en el MISMO parte. La condición de entrada de
  `tasks.md` (`655dbdc`) queda anulada.
- **Spec reescrita como copia adaptada de la F-031 de `partes`** (`497f224`;
  revisión de su rama en `progress/explore_F-037_partes_F-031.md`): copia
  literal de `estado_parte.py` y `cuenta_analitica.py` (rama `9b202e9`, sin
  cambios hasta `5ff4d91`) con test anti-divergencia; elección del parte,
  complementario, relectura, conflictos y avisos idénticos; corrige
  `siguiente_cod_pt` y el alta de `hmo` sin `emp`. **Pendiente del humano:**
  D13 reabierta (título `Parte <obra>` como partes), D17 (carrera entre
  servicios al crear el parte) y D18 (`estado_parte.py` a la lista cerrada).
- **2026-10-06: el humano aprueba D13 = `Parte <obra>`, D17 y D18**
  (`3fe200a`); `CLAUDE.md` con `estado_parte.py` en la lista (`32c33ad`).
- **Implementación terminada** (`progress/impl_F-037.md`, T1-T10 y T15,
  `6f97dc2`…`40b9feb`): copia literal de `partes` `9b202e9` con test
  anti-divergencia; mutación en serie 85/85 (y 25/25 en las copias sin el
  test de copias; 13 huecos reales cerrados con tests). Tests anteriores:
  solo los dobles y la ancla de la lista cerrada. Desviaciones declaradas en
  el informe §3 (p. ej. `partes_existentes` se queda porque la usa el script
  de prueba). **Review lanzada** → `progress/review_F-037.md`.
- **T14 (líder): hecha**, piezas de INTEGRACION copiadas a `azure-apps`
  (`5416cd1`, «sin desplegar»).
- **T11 (humano): pendiente.** Pasar a la sesión de `partes` el aviso de la
  carrera al crear el parte (D17) y del hueco de `OrigenSubcuenta` sin test
  de inmutabilidad. INTEGRACION §7 ya dice «`partes` está avisado»: será
  cierto antes del `done`.
- **Observación del implementer para el humano:** preexistente, la capacidad
  no se evalúa en un periodo sin ningún parte (dos líneas nuevas del mismo
  recurso que sumen > 1 no avisan). Se le propone abrirla como feature.
- **MANUAL (humano):**
  - **T12, solo lectura:** transfer de la rama con `OBRA_PRUEBAS_FORZAR=true`
    y api local; en un periodo de prueba con un MENC o MJEFO y un MPRL:
    `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight" -H "Content-Type: application/json" -d "{}"`.
    Esperado: MENC/MJEFO `escribir` con `caa_cod` `0404.CIMO03`/`CIMO02` y
    `caa_origen` `recurso`; MPRL con `caa_ide` 0 y aviso de `.CIMO16`; en
    `partes[]` el `estado`, `complementario` y `aviso`. NO `ejecutar`.
    Resultado: _pendiente_.
  - **T13:** escritura en modo pruebas en la 0404 con autorización expresa
    y Administración avisada (pasos en `tasks.md`). Resultado: _pendiente_.

## 2026-10-06 · Despliegue de F-029

Lanzado por el humano con `infra/redeploy_dedicacion.ps1 -Solo api,front` desde
una copia de trabajo de `dev` (`porcentajes-despliegue`, para no subir F-037,
en curso en su rama): `api:r20261006-1140`, `front:r20261006-1141`; transfer
sin cambios (`r20261003-1444`, modo real). Sin DDL ni sync. `azure-apps`
actualizado en el mismo trabajo.

## 2026-10-06 · F-037 · El registro rellena la cuenta analítica de la obra

Rama `feature/F-037-asiento-analitico-obra` · `sdd: true` · rigor `critico` ·
**APROBADO** por el reviewer en la pasada 2 (la 1 pidió solo rastro).

**Qué se descubrió.** Sigrid ya genera el asiento analítico de cada parte
(`ANA`, botón «Contabiliza parte…», que deja el parte en Imputado) desde
`hmores.caaide` de cada línea; el 6XX lo pone la nómina. El transfer escribía
`caaide = 0`, así que sus líneas no entraban en el `ANA`.

**Qué cambió.** El transfer rellena `caaide` con la regla de `partes` (cuenta de
la ficha de horas del recurso o, si no, de la partida C[ID], en el centro de la
obra destino) y NO escribe asientos. Copia adaptada de la F-031 de `partes`
(mismo parte): copia literal de `estado_parte.py` y `cuenta_analitica.py`
(`9b202e9`, lista cerrada de `CLAUDE.md`) con test anti-divergencia; elige el
parte igual que `partes` (cerrado = estado ≠ En registro), crea o reutiliza el
complementario `Parte <obra>` con alta protegida (D17) y evalúa duplicados y
conflictos contra todos los partes del periodo. Corrige de paso
`siguiente_cod_pt` y el alta de `hmo`, que no filtraban por empresa.

**Decisiones del humano.** D1-D18 (2026-10-05 y 2026-10-06): sin asientos; la
cuenta sale del recurso («mira en partes»); parte cerrado → complementario;
copiar adaptada la F-031 de `partes` en curso («se usa el mismo parte
realmente»); D13 `Parte <obra>`; D17 alta protegida; D15/D18 copias.

**Verificado.** Cobertura 219/219; mutación en serie 85/85 (y 25/25 en las
copias sin el test de copias). T12 (preflight local) cumplida. T13 en modo
pruebas, autorizada: `PT26/00343` creado con dos líneas en `0404.CIMO03`,
contabilizado por Administración («ha funcionado perfectamente») y borrado por
el humano. **Aplazado por el humano:** probar el complementario en real.
`azure-apps`: `5416cd1`.

Informes: `progress/impl_F-037.md`, `progress/review_F-037.md`,
`progress/mutacion_F-037.md`, `progress/mutacion_F-037_copias.md`,
`progress/explore_F-037.md`, `progress/explore_F-037_partes_F-031.md`.
Sección retirada de `current.md`:

## F-037 · El registro genera el asiento analítico de la obra (en curso)

- **Qué es** (pedida el 2026-10-05; correo de Juan Romero «ARBOL ANALITICO
  OBRAS»): Sigrid YA genera el asiento analítico de cada parte (`ANA`, botón
  «Contabiliza parte…», que deja el parte en Imputado); el 6XX lo pone la
  nómina. El transfer escribía `hmores.caaide = 0` y sus líneas no entraban en
  el `ANA`. **F-037 rellena `caaide` y no escribe asientos** (D1 = A).
- **Spec aprobada** (D1-D18 decididas el 2026-10-05 y 2026-10-06; resumen en
  `history.md` al cerrar): copia ADAPTADA de la F-031 de `partes`, porque los
  dos escriben en el MISMO parte. Copia literal de `estado_parte.py` y
  `cuenta_analitica.py` (rama de `partes` `9b202e9`; lista cerrada de
  `CLAUDE.md` ampliada, `b7ef1e6` y `32c33ad`); complementario `Parte <obra>`
  (D13); alta protegida (D17); cualquier estado ≠ En registro es cerrado (D16).
- **Implementación** (`progress/impl_F-037.md`, `6f97dc2`…`40b9feb`): cobertura
  219/219; mutación en serie 85/85 (y 25/25 en las copias sin el test de
  copias). Tests anteriores: solo dobles y la ancla de la lista cerrada.
- **Review 1 (2026-10-06): CAMBIOS PEDIDOS solo por el rastro** (este fichero y
  la `acceptance` de `features.json`), corregidos por el líder; código, tests,
  mutación y docs dados por buenos hasta `ac125cb`. **Review 2: APROBADO.**
  NO se mergea a `dev` hasta cumplir T12 y T13 (para que un despliegue
  desde `dev` no lleve F-037 sin verificar en Sigrid).
- **T14 (líder): hecha**, copia a `azure-apps` `5416cd1` («sin desplegar»).
- **T11 (aviso a `partes`):** `partes` YA recogió la carrera y el alta
  protegida de D17 (su commit `9ea7c59`). **Falta avisarles** del hueco de
  `OrigenSubcuenta` sin test de inmutabilidad (lo pasa el humano). Además su
  DA11 cambiará la cabecera de las copias: pondrá en rojo
  `test_f037_copias_partes.py::…ref_vigilada` y habrá que **recopiar** y mover
  `COMMIT_COPIADO` (design §12: «texto, se recopia»).
- **Observación del implementer, propuesta al humano como feature:** la
  capacidad no se evalúa en un periodo sin ningún parte (dos líneas nuevas del
  mismo recurso que sumen > 1 no avisan). Preexistente.
- **MANUAL (humano), API y transfer LOCALES desde esta rama:**
  - **T12, solo lectura.** Transfer con `OBRA_PRUEBAS_FORZAR=true` y api con
    `TRANSFER_BASE_URL=http://127.0.0.1:8006`; periodo de prueba local con un
    MENC o MJEFO y un MPRL:
    `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight" -H "Content-Type: application/json" -d "{}"`.
    Esperado: MENC/MJEFO `escribir` con `caa_cod` `0404.CIMO03`/`CIMO02` y
    `caa_origen` `recurso`; MPRL con `caa_ide` 0 y aviso de `.CIMO16`; en
    `partes[]` `estado`, `complementario` y `aviso`. **NO `ejecutar`.**
    **Resultado (2026-10-06, humano, octubre 2026, 7 obras forzadas a 0404):
    CUMPLIDA.** 11 acciones `escribir`: MENC → `0404.CIMO03` y MJEFO →
    `0404.CIMO02`, `caa_origen` `recurso`; MPRL → sin cuenta,
    `caa_motivo` `obra_sin_cuenta` y aviso «la obra 0404 no tiene la cuenta
    analitica .CIMO16». Parte de 0404 2026-10 inexistente: se crearía
    `PT26/00343`, `complementario` falso, sin cerrados (el camino del
    complementario se ejercita en T13). La MPRL trae además el conflicto
    `sin_partida` de F-013 (preexistente, no de F-037).
  - **T13 — AUTORIZADA por el humano el 2026-10-06 («autorizo»).** Paso 1
    hecho por el humano (`ejecutar` con `trabajador_ide` 2750167): creado
    `PT26/00343` (con.ide 2848891, est 1, «Parte CUBIERTA NAVE 14 - JOHN
    DEERE (PRUEBA-PORC)», fec 20261031, obra 828942, centro 828943); 2 líneas
    (`porcentajes:124` y `:125`, hmores 408963-408964, MENC 0,5 × 6.000 =
    3.000 cada una) con `cenide` 828943 y `caaide` 829178 = `0404.CIMO03`,
    `tex` PRUEBA-PORC. Leído por el líder (solo lectura). Siguiente: paso 3
    (Administración contabiliza `PT26/00343`).
  - **T13, ESCRITURA en modo pruebas (0404).** Condición previa: autorización
    expresa del humano para esta acción y Administración avisada. Pasos:
    1. `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/ejecutar" -H "Content-Type: application/json" -d "{\"trabajador_ide\": <ide>}"`
       (mes sin actividad en 0404). Esperado: la línea `registrado`.
    2. Lectura, desde `services/dedicacion-api` con `PYTHONPATH=.`:
       `.venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.sigrid.sigrid_client import SigridApiClient as C; print(C(get_settings()).leer(\"SELECT hmores.caaide, cc.cod AS cuenta, pt.cod AS parte, pt.est, hmores.cenide, hmores.tot FROM hmores JOIN con pt ON pt.ide = hmores.hmoide LEFT JOIN con cc ON cc.ide = hmores.caaide WHERE hmores.synckey = 'porcentajes:<id>'\"))"` (Git Bash; `<id>` = el `registro_id` de la línea: el transfer desplegado escribe en real y `LIKE` traería líneas reales).
       Esperado: `caaide` ≠ 0, `cuenta` `0404.CIMOxx`, `cenide` el de 0404,
       parte `est` 1.
    3. Administración pulsa «Contabiliza parte…»: parte en `est` 10 y `ANA` con
       debe a `0404.CIMOxx` por `tot` y haber a `CP.<persona>`; confirma que la
       línea se ve como una tecleada.
    4. Otra línea del mismo mes (paso 1 con otro trabajador): va a un
       complementario `Parte 0404 …` nuevo, que se contabiliza aparte.
    5. Limpieza, desde `services/dedicacion-transfer`:
       `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar` (dry-run)
       y luego `… limpiar --confirmar`; Administración anula los `ANA` y el
       complementario.
    Resultado: _pendiente_.


## 2026-10-06 · Recopia de las copias de `partes` (e85ef0e)

La F-031 de `partes` añadió a `estado_parte.py` y `cuenta_analitica.py` una
cabecera de dependencia con porcentajes (su commit `e85ef0e`, «T28», solo
docstring; su DA11, prevista en nuestro design §12: «texto, se recopia»).
`test_f037_copias_partes.py::…ref_vigilada` lo detectó y dejó `dev` en rojo.
Se recopiaron los dos ficheros y `COMMIT_COPIADO` pasa a `e85ef0e`; la regla
no cambia. Suite del transfer en verde.

## 2026-10-06 · Aviso de `partes` (F-031): confluencia con F-037

Recibido del humano: `partes` cambió la cabecera de `estado_parte.py` y
`cuenta_analitica.py` (solo docstring, `e85ef0e`; ya recopiado en `c906219`),
su F-031 está mergeada en su `dev`, y su `stmts_crear_parte` es ahora idéntico
en texto y parámetros al nuestro (`40b9feb`). Se cambia `REF_VIGILADA` de
`test_f037_copias_partes.py` a `dev` (la rama de la F-031 ya no existe), se
anota la confluencia del alta en su docstring y en INTEGRACION §7 (y su copia
en `azure-apps`): si se cambia el alta, se avisa a `partes`.
