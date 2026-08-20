<!-- progress/review_F-004.md -->
# F-004 · README del monorepo y arranque local en orden — informe de review

Rama `feature/F-004-readme-monorepo` · `sdd: false` (mandan los `acceptance`)
· commits de la feature: `605c2d9` (README + test) y `fed6f9b` (informe).

## Veredicto: **APPROVED**

El README dice la verdad. He comprobado **una por una** todas sus afirmaciones
verificables contra el código de esta rama, no contra el informe del
implementer, y no he encontrado ni una discrepancia. La trampa que el encargo
señalaba —`/api/v1/health` frente a `/health`— está bien documentada, con
párrafo de aviso propio y con un test que impide que se degrade.

## Nivel de rigor

**`documental`**, declarado en `harness/features.json` (no por omisión). Según
la tabla de `CHECKPOINTS.md`, exige **C1–C3, C3 bis y C5**, y **no** exige fase
RED, ni puerta de cobertura, ni campaña de mutación. No las he reclamado, y su
ausencia no cuenta contra la feature: es lo que el nivel prescribe para un
cambio que solo aporta documentación. `init.sh` lo confirma por su cuenta:
`PUERTA COBERTURA: N/A (F-004 es de nivel documental: no exige cobertura)`.

C4 (tests trazables) tampoco es exigible en este nivel, pero el implementer
entregó suite igualmente, así que la he evaluado como valor añadido (§ Los
tests).

## El rojo previo del portero: no cuenta contra F-004

El líder ya lo resolvió antes de esta review, y lo he verificado por mi cuenta:
`services/dedicacion-front/tests/` contenía **solo `__pycache__`** —residuo de
la rama de F-008—, así que `pytest` devolvía código 5 («no tests ran») e
`init.sh` lo trataba como fallo. Retirado el residuo, el portero vuelve a
verde con el aviso legítimo de que el front no tiene tests en esta rama. Nada
de eso lo causó F-004: el diff del implementer toca **dos ficheros**, `README.md`
y `tests/test_f004_readme.py`, y ninguno es del front.

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en `ENTORNO LISTO. Puedes trabajar.`
      (exit 0). Ejecutado tal cual, sin pipes ni decoración.
- [x] Existen los nueve ficheros obligatorios (`CLAUDE.md`,
      `harness/features.json`, `specs/SPECS.md`, `progress/current.md`,
      `progress/history.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`,
      `CHECKPOINTS.md`, `harness/rigor.json`). Comprobado por el portero y a
      mano.

**Suites de servicio verificadas a mano, no por caché.** El portero dio `[OK]`
a api y transfer «por caché: árbol sin cambios desde el último verde», y ese
mecanismo acaba de demostrar que puede heredar un verde de otra rama. Las he
reejecutado:

| Servicio | Comando | Resultado real |
|---|---|---|
| api | `.venv/Scripts/python -m pytest -q` | **84 passed** en 1,02 s, exit 0 |
| transfer | `.venv/Scripts/python -m pytest -q` | **187 passed**, 1 warning, en 0,41 s, exit 0 |
| raíz | `python -m pytest -q` | **22 passed** en 0,22 s |
| front | — | sin directorio de tests: **aviso**, no fallo (su suite está en la rama de F-008, sin mergear) |

El warning del transfer (`PytestReturnNotNoneWarning` en
`test_pipeline_offline.py::test_preflight`) es **deuda previa ajena a F-004**;
lo anoto para que no se pierda, no como reproche a esta feature.

## C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `F-004`. Las otras dos abiertas
      (`F-002`, `F-008`) están `blocked`, que es su estado real y consta en
      `current.md`.
- [x] Rama actual `feature/F-004-readme-monorepo`, la de la feature. Nunca
      `main` ni `dev`.
- [x] `progress/current.md` describe la sesión activa y solo ella, con las
      otras features vivas identificadas como tales y la acción pendiente en
      Sigrid separada en su apartado.
- [x] Las tres features `done` (`F-001`, `F-003`, `F-009`) tienen su resumen en
      `progress/history.md`. Comprobado programáticamente, no de vista.

## C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal:** la feature no añade código de producción. Un documento
      Markdown y un test de la raíz que **no importa nada de los servicios**
      (lee el texto fuente con `pathlib`), precisamente para no acoplar la
      suite de la raíz a tres venv distintos. Decisión correcta y explicada en
      el docstring del propio test.
- [x] **Primera línea con la ruta:** `README.md` abre con `<!-- README.md -->`;
      `tests/test_f004_readme.py`, con `# tests/test_f004_readme.py`.
- [x] **Sin `print()`, sin TODOs huérfanos, sin dependencias nuevas** (solo
      `re`, `pathlib` y `pytest`, ya presentes). `python -m ruff check
      tests/test_f004_readme.py` con el intérprete de la raíz: `All checks
      passed!`.
- [x] **Las tres trampas de dominio, vigiladas aunque la feature no toque
      código:**
      - *Escala del porcentaje*: el README **no reenuncia** la conversión
        0-100 ↔ sobre 1. Remite a `docs/ARCHITECTURE.md` § Semántica de
        dominio imprescindible (sección verificada: existe, línea 116). No
        introduce una segunda verdad, que era el riesgo real de un README.
      - *Postventa*: no se menciona ni se simplifica. Correcto: enunciarla a
        medias en un README de arranque habría sido peor que callarla.
      - *Solo escribe el transfer*: el README lo dice tres veces y bien —en el
        diagrama, en la tabla de servicios («la única pluma») y en «Qué NO
        hacer», con `OBRA_PRUEBAS_FORZAR`, la obra `0404`, la marca
        `PRUEBA-PORC` y la exigencia de autorización expresa del humano.
        Verificado contra `services/dedicacion-transfer/config/settings.py:29-32`
        y su `.env.example`: los tres valores coinciden. La afirmación de que
        la escritura va contra `ruesma` y de que `ruesma_rep` no la admite
        coincide con `settings.py:21-22`.

## C3 bis — Documentos que entran de fuera

**N/A justificado:** la feature **no añade ni modifica ningún fichero de
`docs/referencia/`** (diff: `README.md` y `tests/test_f004_readme.py`, nada
más). No hay original en PDF ni ofimática de por medio, y `git log
--diff-filter=A` no aporta nada al caso porque no entró ningún documento
externo.

Aun así he ejecutado el **barrido de datos sensibles** sobre los dos ficheros
nuevos, porque el `acceptance` A3 lo exige explícitamente y porque el barrido
del implementer no vale como prueba de sí mismo:

| Patrón | Resultado |
|---|---|
| `password[ :=]`, `secret[ :=]`, `api[_-]?key[ :=]`, `function_key[ :=]`, `token[ :=]`, `pwd[ :=]`, `AccountKey` | **0 coincidencias** |
| `BEGIN … PRIVATE KEY` | **0** |
| GUID (suscripción / tenant) `[0-9a-f]{8}-…-[0-9a-f]{12}` | **0** |
| IPs no loopback `\b\d{1,3}(\.\d{1,3}){3}\b` menos `127.0.0.1` | **0** |
| Cadenas base64 de 40+ caracteres | **0** |
| Todas las URLs del documento | 6, **todas loopback**: `127.0.0.1:8006`, `127.0.0.1:8090`, `localhost:8080` |

El README nombra `SIGRID_API_FUNCTION_KEY`, `PG_PASSWORD` y
`PG_ADMIN_PASSWORD` **como variables a rellenar**, sin un solo valor, y añade
que se copian del gestor de secretos. Es exactamente la línea correcta.
**A3 cumplido.**

## C4 — La verificación es real

Recuerdo que en nivel `documental` este bloque no es exigible; lo evalúo
porque hay entrega.

- [x] Los tres criterios `acceptance` tienen test trazable y **los 11 pasan**
      (`11 passed in 0,03 s`, ejecutados por mí).
- [x] Los tests no tocan red ni BBDD: leen ficheros del árbol y aplican
      expresiones regulares. Cero I/O externo.
- [x] **Verificaciones `MANUAL (humano)`: ninguna.** Es documentación; no toca
      Sigrid, ni PostgreSQL, ni `.env`, ni ejecuta nada contra producción.
      `current.md` lo declara así explícitamente. La sugerencia del implementer
      de que el humano lea el apartado «Estado del proyecto» me parece bien
      planteada, pero no es una verificación MANUAL en el sentido del
      checkpoint: es una revisión de criterio, no un comando pendiente.

### Trazabilidad `acceptance` → test

| # | Criterio `acceptance` | Test que lo cubre | Comprobado |
|---|---|---|---|
| A1 | README en la raíz con mapa de servicios, flujo y arranque en orden | `test_f004_a1_existe_readme_en_la_raiz`, `..._documenta_los_tres_servicios_con_su_puerto`, `..._arranque_en_el_orden_que_funciona`, `..._los_puertos_del_readme_son_los_reales` (×3 parametrizado), `..._toda_url_de_la_api_lleva_su_prefijo_real`, `..._los_env_example_que_manda_copiar_existen` | **cumplido** |
| A2 | Enlaza a `docs/ARCHITECTURE.md` y a `azure-apps` en vez de duplicarlos | `test_f004_a2_los_enlaces_relativos_resuelven`, `test_f004_a2_remite_a_la_arquitectura_y_a_azure_apps` | **cumplido** |
| A3 | Ningún secreto ni valor de credencial | `test_f004_a3_sin_secretos_ni_valores_de_credencial` + mi barrido independiente | **cumplido** |

Sobre A2: `azure-apps` se cita **por nombre**, no como enlace Markdown. Es lo
correcto y no un incumplimiento: vive fuera del repositorio, y un
`../azure-apps/sigrid_api.md` se rompería en cualquier checkout que no tenga
los dos repos hermanos. El README dirige bien (`sigrid_api.md` para la pasarela
y sus topes, `sigrid_tablas.md` para el diccionario) y dice expresamente que no
se duplican aquí.

## Verificación independiente de lo que afirma el README

Esto es el núcleo de la review: un README que miente es peor que no tenerlo.
He comprobado cada afirmación **contra el código de esta rama**.

| Afirmación del README | Contrastada con | Resultado |
|---|---|---|
| transfer = 8006 | `settings.py:48` `Field(8006, alias="API_PORT")` + `.env.example:17` | **coincide** |
| api = 8090 | `settings.py:33` `api_port: int = 8090` + `.env.example:5` | **coincide** |
| front = 8080 | `settings.py:22` `front_port: int = 8080` + `.env.example:3` | **coincide** |
| «La api busca al transfer en `http://127.0.0.1:8006`, `settings.py:59`» | leído `settings.py` líneas 55-63 | **exacto, línea 59 incluida** |
| «el front busca a la api en `http://127.0.0.1:8090` (`API_BASE_URL`)» | `dedicacion-front/.env.example:7` | **coincide** |
| **Salud api = `/api/v1/health`, no `/health`** | `routes.py:46` `APIRouter(prefix="/api/v1")` + `routes.py:53` `@router.get("/health")` + `app.py:56` `include_router(router)` sin prefijo extra | **correcto; `/health` a secas es 404, como avisa** |
| Salud transfer = `/health` | `interface_adapters/api/app.py:77` | **correcto** |
| Salud front = `/health` | `interface_adapters/web/app.py:66` | **correcto** |
| «arrancar siempre por `main.py`, el esquema se pone al día ahí» | `dedicacion-api/main.py:34` `asegurar_base_datos(settings)` + README del api líneas 16-23 | **correcto y bien enlazado** |
| «La api crea la base `dedicacion` al arrancar si no existe» | `main.py:19,34` | **correcto** |
| Los tres `.venv/Scripts/python.exe` y los tres `main.py` existen | comprobados uno a uno | **los seis existen** |
| Los tres `.env.example` que manda copiar existen | comprobados | **los tres** |
| «el front hace proxy de `/api/*` inyectando `X-Usuario` desde Easy Auth» | `web/app.py:76,84` (`"x-usuario": _usuario(...)`) y `:121` (`x-ms-client-principal-name`) | **correcto** |
| «solo el personal que cobra por mes, código de hora `M*`» | `docs/ARCHITECTURE.md:19,130` | **correcto** |
| `OBRA_PRUEBAS_FORZAR=true`, obra `0404`, marca `PRUEBA-PORC` | `transfer/config/settings.py:29-32` + `.env.example:8-10` | **los tres coinciden** |
| «la escritura va contra `ruesma`; `ruesma_rep` no la admite» | `transfer/config/settings.py:21-22` + `.env.example:4` | **correcto** |
| «`infra/` y los documentos de despliegue **no existen en esta rama**» | `ls -d infra` → no existe; `docs/INTEGRACION.md` → no existe | **correcto: no da por hecho nada de F-008** |
| Rutas de «Dónde está cada cosa» (`services/`, `docs/`, `docs/referencia/`, `specs/`, `progress/`, `harness/`, `scripts/`, `tests/`) | comprobadas una a una | **las ocho existen** |
| Enlaces relativos | script propio, independiente del test del implementer | **13 enlaces, 0 rotos** |
| Comandos para Windows con venv por servicio | `.venv/Scripts/python` (no `bin/`) | **correcto para este entorno** |

Dos aciertos que merecen mención porque son los que distinguen un README
escrito con hechos de uno escrito de memoria:

1. **No cita ningún número de topes de `sigrid-api`.** Remite a
   `azure-apps/sigrid_api.md` para «sus topes reales». Es lo correcto: los
   números que circulan por el código (`sigrid_max_rows: int = 5000`) y por la
   documentación global no concuerdan entre sí, y un README que hubiera elegido
   uno habría creado una tercera versión de la verdad.
2. **El párrafo de `/api/v1/health` no se limita a dar la URL buena**: explica
   que confundirla «devuelve un 404 que parece un servicio caído y no lo es».
   Eso es lo que ahorra la próxima hora perdida.

### Honestidad del apartado «Estado del proyecto»

Comprobado contra `progress/current.md` y `progress/history.md`, y es fiel:

- «Funciona en local, entero», con la fecha (2026-08-20) y el detalle de que el
  front sirvió el cuadrante real leído de PostgreSQL. Coincide con
  `current.md`.
- «La escritura en Sigrid está probada de verdad, **una sola vez**», en obra de
  pruebas `0404` y marcada `PRUEBA-PORC`, «antes de esa fecha el sistema nunca
  había escrito en el ERP». Coincide con el hecho registrado en `current.md`
  (T14 de F-002). No infla el logro ni lo esconde.
- «No hay nada desplegado en Azure», con la infraestructura descrita como
  trabajo en curso en su propia rama, sin integrar. **Exactamente el registro
  que pedía el encargo**: F-008 está aprobada pero no mergeada, y el README no
  la da por existente.
- «La base PostgreSQL es hoy local; el servidor de destino está sin decidir por
  escrito». Coincide con la regla dura de `CLAUDE.md`, que prohíbe dar por
  hecho ninguno de los dos.

## Los tests: ¿reales o decorativos?

**Reales.** El encargo pedía juicio sobre esto, y mi valoración es que la suite
gana su sitio, con una salvedad de forma.

Lo que la hace real es que **ata el documento al código**, no a sí misma:

- `..._los_puertos_del_readme_son_los_reales` lee el `.env.example` de cada
  servicio y compara el número declarado con el documentado. Si mañana el
  transfer se mueve al 8007, la suite se pone roja y el README no miente ni un
  día.
- `..._toda_url_de_la_api_lleva_su_prefijo_real` **extrae el prefijo del propio
  `routes.py`** con una regex sobre `APIRouter(prefix=...)` y exige que
  *ninguna* URL del puerto 8090 aparezca sin él. No comprueba que se mencione
  la cadena correcta en algún sitio —eso sería decorativo—, comprueba que no
  aparezca la incorrecta en ninguno. El implementer documenta que su primera
  versión **sí era decorativa** (pasaba con el README roto) y que la afinó; el
  test que hay en el árbol es el afinado, lo he leído.
- `..._los_env_example_que_manda_copiar_existen` extrae los `cp` del propio
  README y comprueba que los orígenes existen: valida el comando que el lector
  va a copiar, no una constante escrita a mano.
- `..._los_enlaces_relativos_resuelven` recorre los 13 enlaces reales.
- El de secretos excluye `127.0.0.1` **de forma explícita y comentada** antes
  de aplicar el patrón de IPs, en vez de bajar el listón del patrón.

Sobre la fragilidad, que era la otra mitad de la pregunta: **no me preocupa**.
Ninguno de los once falla por un cambio inocente de redacción. Lo que los
rompe es cambiar un puerto, mover un fichero, romper un enlace, invertir el
orden de arranque o colar un secreto: exactamente los cambios ante los que uno
*quiere* que salte una alarma. Dos matices menores, ninguno bloqueante, en las
propuestas de más abajo.

## C4 bis — El rigor declarado se cumple

- [x] La feature **declara** `rigor: "documental"` en `harness/features.json`,
      con valor válido según `harness/rigor.json` (validado por `init.sh`). No
      se aplica el `critico` por omisión.
- [x] **Fase RED: N/A justificado por el nivel.** `documental` no la exige, y
      `CHECKPOINTS.md` admite ese motivo por escrito. Lo hago constar aunque
      no fuera necesario: el implementer aportó de todos modos evidencia de
      no-vacuidad, rompiendo el README a propósito tres veces (enlace,
      `/health`, orden invertido) y pegando las tres trazas de fallo. No es
      fase RED formal, pero es la misma disciplina aplicada a un entregable
      documental, y es más de lo que el nivel pedía.
- [x] **Cobertura: N/A con motivo impreso por la herramienta**, no alegado por
      nadie: `[OK] PUERTA COBERTURA: N/A (F-004 es de nivel documental: no
      exige cobertura)`.
- [x] **Mutación: N/A justificado por el nivel.** `documental` no la exige, y
      sobre lo cambiado —Markdown y aserciones de texto— no hay lógica que
      mutar. **No he reejecutado ninguna campaña ni recalculado alcance**: no
      existe `progress/mutacion_F-004.md` y no debe existir. La regla de los
      5 minutos y la verificación independiente de totales no aplican aquí por
      la misma razón.
- [x] Supervivientes: N/A, no hay campaña (mismo motivo).
- [x] El informe del implementer trae la sección **«Evidencias»** con sus
      números: 22 tests en verde (11 previos + 11 nuevos), 0,16 s de suite,
      cobertura N/A con su motivo, mutación N/A con su motivo, 13 enlaces
      comprobados y 0 secretos. **He reejecutado los números y coinciden**
      (22 en la raíz, 11 aislados).
- [x] Ningún punto marcado N/A sin justificación escrita: los cuatro N/A de
      arriba llevan su motivo y el motivo es el nivel declarado, no la
      omisión de una herramienta.

## C4 ter — Rutas sensibles

**N/A sin nada que justificar:** este repositorio **no declara**
`harness/rutas_sensibles.json` (comprobado: no existe). Es el caso
mayoritario que el propio checkpoint contempla, y `init.sh` no señaló ninguna
ruta tocada.

## C5 — La sesión se cerró bien

- [x] **`tasks.md`: N/A justificado.** F-004 es `sdd: false` y no tiene
      `specs/F-004-*/`; según la nota de cabecera de `CHECKPOINTS.md`, lo que
      dependa de `tasks.md` es N/A y el formato mínimo de commit pasa a ser
      `F-XXX: <descripción>`. Los dos commits de la feature lo cumplen:
      `F-004: README del monorepo con el arranque local en orden` (`605c2d9`)
      y `F-004: informe de implementación` (`fed6f9b`).
- [x] **Sin ficheros temporales ni artefactos sospechosos:** `git status
      --porcelain` vacío, árbol limpio.
- [x] **`features.json` refleja el estado real:** `in_progress`, que es lo
      correcto para una feature en revisión. Pasarla a `done` es del líder,
      tras este veredicto; yo no la he tocado.

**Autoría del diff, comprobada.** El implementer avisaba de que `BACKLOG.md`,
`harness/features.json`, `progress/current.md` y `progress/history.md` los
movió el líder, no él. Verificado con `git log` por fichero: sus dos ficheros
(`README.md`, `tests/test_f004_readme.py`) entran **solo** en `605c2d9`, y los
otros cuatro vienen de `f887388` y `d83ae68`, ambos del líder. Hizo `git add`
por nombre y no `git add -A`, como manda el protocolo.

## Cambios requeridos

**Ninguno.** La feature se aprueba tal cual está.

## Propuestas de mejora (no bloqueantes, no aplicadas)

Ninguna condiciona el veredicto. Las dejo escritas para que no se pierdan.

1. **`tests/test_f004_readme.py:50`** —
   `texto.index(f"cd services/dedicacion-{s} ")` lanza `ValueError: substring
   not found` en vez del `AssertionError` con mensaje que el propio test
   preparó. Si alguien reescribe el bloque de arranque, el fallo llega como
   excepción críptica en lugar de como «el README documenta el arranque en un
   orden distinto». Un `find()` con comprobación de `-1`, o un
   `pytest.fail()` previo, daría el mensaje bueno. Cosmético.
2. **`tests/test_f004_readme.py:33-41`** — `..._documenta_los_tres_servicios_con_su_puerto`
   solo exige que el literal del puerto aparezca *en algún sitio* del texto,
   lo que por sí solo es débil. Queda compensado por
   `..._los_puertos_del_readme_son_los_reales`, que sí lo ata al
   `.env.example`; la observación es que el primero, aislado, no probaría gran
   cosa.
3. **Deuda ajena a F-004, anotada para que no se pierda:**
   `services/dedicacion-transfer/tests/test_pipeline_offline.py::test_preflight`
   devuelve un objeto en vez de usar `assert`
   (`PytestReturnNotNoneWarning`). Pytest lo tolera hoy y ha anunciado que
   dejará de hacerlo. No es de esta feature.
4. **Cuando F-008 entre en `dev`**, hay que actualizar en el README la frase
   «el trabajo de infraestructura está en curso en su propia rama, sin
   integrar» y la línea de que `infra/` no existe. El implementer ya lo dejó
   señalado; lo repito aquí porque es la única parte del documento con fecha
   de caducidad conocida, y quien mergee F-008 debería llevarla en su lista.

## Automejora del protocolo (propuesta, no aplicada)

**`docs/CONVENTIONS.md` § Tests** exige nombres trazables con la forma
`test_fXXX_rN_...`, pensada para requisitos EARS. En features `sdd: false` no
hay requisitos EARS sino criterios `acceptance`, y el implementer usó
`test_f004_a1_...` / `a2` / `a3`, mapeando la *a* a *acceptance*. Me parece
**mejor** que fingir una `r` que no existe, y he decidido no penalizarlo: el
criterio de fondo —que el nombre diga a qué criterio responde— se cumple
mejor así que con la letra de la norma.

Propongo (no aplico) que `docs/CONVENTIONS.md` y `CHECKPOINTS.md` § C4 admitan
explícitamente `test_fXXX_aN_...` para criterios `acceptance`, dejando `rN`
para requisitos EARS. Es una mejora **genérica del arnés**, no específica de
este proyecto: la nota de cabecera de `CHECKPOINTS.md` ya traduce «requisito
EARS → acceptance» y «`F-XXX Tn:` → `F-XXX:`» para features `sdd=false`, pero
se dejó fuera la convención de nombres de test, que es el tercer sitio donde
la traducción hacía falta. Si el humano la aprueba, hay que portarla a
`arnes-base` en el mismo trabajo, según la regla de propagación de
`CLAUDE.md`.
