<!-- progress/impl_F-004.md -->
# F-004 · README del monorepo y arranque local en orden — informe de implementación

Rama `feature/F-004-readme-monorepo` · `sdd: false` (mandan los `acceptance`)
· rigor **`documental`** · commit `e62ee32`.

> **Veredicto: `blocked`.** El trabajo de la feature está **terminado y
> commiteado**, y todo lo que depende de F-004 está en verde. Lo que impide
> cerrarla es un rojo de `harness/init.sh` **anterior a esta feature y ajeno a
> ella**, que también afecta a `dev`. Diagnóstico completo y arreglo propuesto
> en la sección «El bloqueo». No lo he tocado por mi cuenta: el arreglo está
> en `harness/init.sh`, que es arnés genérico y arrastra propagación a
> `arnes-base`. Eso lo decide el líder, no el implementer.

## Ficheros tocados

| Fichero | Qué es |
|---|---|
| `README.md` (nuevo, 177 líneas) | El README del monorepo. |
| `tests/test_f004_readme.py` (nuevo, 139 líneas) | Ata el README al código para que no se pudra en silencio. |

**No he tocado** `.env`, `harness/features.json` ni `progress/current.md`.
Aviso: al terminar, `git status` muestra `harness/features.json` y
`BACKLOG.md` modificados (10 → 11 features). **No son míos** — los cambió el
líder mientras yo trabajaba. Los he dejado fuera del commit a propósito
(`git add` de mis dos ficheros por nombre, nunca `git add -A`).

## Contenido del README y por qué

Cubre los seis puntos del encargo, en este orden: qué es el sistema y el flujo
en dos párrafos + diagrama; tabla de los tres servicios con su puerto y
**enlace** a su README; arranque local (requisitos previos, copia de los tres
`.env.example`, el orden y por qué importa); cómo comprobar que funciona; qué
NO hacer; dónde está cada cosa; y el estado real del proyecto.

Decisiones de redacción que conviene conocer:

- **Enlaza, no duplica.** Las reglas de negocio no se reenuncian: el README
  remite a `docs/ARCHITECTURE.md` como única fuente normativa, igual que hace
  el README del transfer. Reenunciarlas habría creado una segunda verdad, que
  es justo lo que vigila `test_f002_fuente_unica.py`.
- **`infra/` y los documentos de despliegue no se mencionan como existentes.**
  En esta rama no están (son de F-008, aprobada pero sin mergear). El README
  dice que el trabajo de infraestructura «está en curso en su propia rama, sin
  integrar». Cuando F-008 entre en `dev`, esa frase es lo único que hay que
  actualizar.
- **La trampa de `/api/v1/health`** tiene párrafo propio y test propio. Es el
  tropiezo caro que cita el encargo.
- **Variables sí, valores nunca.** Se dice qué hay que rellenar
  (`SIGRID_API_FUNCTION_KEY`, `PG_PASSWORD`…) y que los valores se copian del
  gestor de secretos. Ningún valor en el documento.
- **El estado del proyecto se escribe sin adornos**, incluida la frase de que
  la escritura en Sigrid está probada **una sola vez** y en obra de pruebas.

## Qué verifiqué y con qué resultado

Todo comprobado contra el código antes de escribirlo, no supuesto:

| Afirmación del README | Cómo la comprobé | Resultado |
|---|---|---|
| Puertos 8006 / 8090 / 8080 | `API_PORT` y `FRONT_PORT` de los tres `.env.example` y `config/settings.py` | coinciden |
| La api llama al transfer en `127.0.0.1:8006` | `services/dedicacion-api/config/settings.py:59` | `transfer_base_url = "http://127.0.0.1:8006"`, línea 59 exacta |
| Salud de la api = `/api/v1/health` | `routes.py:46` (`APIRouter(prefix="/api/v1")`) + `routes.py:53` (`@router.get("/health")`) | confirmado; `/health` a secas es 404 |
| Salud del transfer = `/health` | `interface_adapters/api/app.py:77` | confirmado |
| Salud del front = `/health` | `interface_adapters/web/app.py:66` | confirmado |
| Los tres `.venv/Scripts/python.exe` existen | comprobado uno a uno | los tres |
| Los tres `main.py` existen | `ls services/*/main.py` | los tres |
| `infra/` NO existe en esta rama | `ls -d infra` | `No such file or directory`, como avisaba el encargo |
| Los 13 enlaces relativos resuelven | script de comprobación + test permanente | 0 rotos |
| Ningún secreto | barrido por patrones (password/secret/base64/GUID/IP/clave privada) | única coincidencia `127.0.0.1`, que es loopback y sí puede aparecer |

### La suite del README no es de adorno

El rigor `documental` no exige tests, y **no he inventado ninguno para
rellenar expediente**. Los 11 que hay comprueban exactamente lo que el encargo
señala como verificable sin forzar: «que los comandos y rutas que cita el
README existan de verdad». Además atan el documento al código, así que un
cambio de puerto o un fichero movido rompe la suite en lugar de dejar el
README mintiendo.

Para no quedarme en «pasan», **rompí el README a propósito tres veces** y
comprobé que la suite lo caza (después restauré y volví a verde):

```
$ sed -i 's|(docs/ARCHITECTURE.md)|(docs/ARQUITECTURA_QUE_NO_EXISTE.md)|' README.md
$ python -m pytest tests/test_f004_readme.py -q
FAILED tests/test_f004_readme.py::test_f004_a2_los_enlaces_relativos_resuelven
E   AssertionError: enlaces rotos en el README: ['docs/ARQUITECTURA_QUE_NO_EXISTE.md', ...]
1 failed, 10 passed

$ sed -i 's|8090/api/v1/health|8090/health|' README.md
$ python -m pytest tests/test_f004_readme.py -q
FAILED tests/test_f004_readme.py::test_f004_a1_toda_url_de_la_api_lleva_su_prefijo_real
E   AssertionError: el README cita urls de la api sin el prefijo /api/v1: ['/health']
1 failed, 10 passed

$ (invertido el orden de arranque: front antes que transfer)
$ python -m pytest tests/test_f004_readme.py -q
FAILED tests/test_f004_readme.py::test_f004_a1_arranque_en_el_orden_que_funciona
E   AssertionError: el README documenta el arranque en un orden distinto de transfer -> api -> front
1 failed, 10 passed
```

La primera versión del test de la salud **pasaba con el README roto**, porque
el texto cita `/api/v1/health` en otro párrafo y le bastaba con encontrarlo en
algún sitio. Lo afiné: ahora exige que **ninguna** url del puerto 8090
aparezca sin el prefijo que declara el router. La traza de arriba es la del
test ya afinado.

## El bloqueo: `init.sh` está en rojo por algo que no es F-004

```
[KO] servicio front (services/dedicacion-front): pytest en rojo
```

**No lo he causado yo y no puedo arreglarlo desde esta feature.** Qué pasa:

1. `services/dedicacion-front` **no tiene ningún test en esta rama ni en
   `dev`**. Los únicos que existieron se crearon en el commit `38235d7`
   («F-008 T6: primera suite de dedicacion-front»), en la rama
   `feature/F-008-infra-azure`, **sin mergear**.
2. Sin tests, `pytest` termina con **código 5** («no tests ran»), no 0.
   Comprobado directamente:
   ```
   $ cd services/dedicacion-front && .venv/Scripts/python -m pytest -q --tb=short -x
   no tests ran in 0.01s
   EXIT=5
   ```
3. La sección 7 bis de `harness/init.sh` trata cualquier salida distinta de 0
   como rojo, así que **confunde «no hay tests» con «los tests fallan»**.
4. Estaba camuflado por la caché de suites: `.arnes_cache/suite_front.ok`
   guarda el hash del árbol del front **de la rama de F-008**
   (`6ed4c75…`), que no casa con el de esta rama (`de7ba2c…`). Al no valer la
   caché, la suite se ejecuta y sale el rojo. **En `dev` pasa exactamente lo
   mismo**: no es un problema de esta rama.

Lo que **no** he hecho, y por qué:

- **Escribir tests para el front.** Sería inventar tests de adorno para tapar
  un rojo ajeno, justo lo que el encargo prohíbe.
- **Borrar el `__pycache__` huérfano** que F-008 dejó en
  `services/dedicacion-front/tests/`. No arregla nada: aunque desaparezca,
  `pytest` sigue sin recolectar nada y sigue devolviendo 5.
- **`ARNES_SALTAR_SUITES=1`.** El propio `init.sh` avisa de que ese modo «NO
  vale para cerrar una feature».
- **Parchear `harness/init.sh`.** Es el arreglo bueno, pero es arnés genérico:
  tocarlo obliga a portar la mejora a `arnes-base` en el mismo trabajo (regla
  de propagación de `CLAUDE.md`) y afecta a los tres servicios y a todas las
  features. Eso es decisión del líder.

**Arreglo propuesto** (una línea de criterio, en la sección 7 bis): distinguir
el código 5 del resto, y tratar «servicio sin tests» como **aviso**, no como
fallo — con el mismo tono que ya usa `[AVISO] … NADIE está comprobando los
tests de X`. Un servicio sin tests merece un aviso ruidoso; no merece bloquear
el repositorio entero. Si el líder prefiere lo contrario (que un servicio sin
tests bloquee), entonces el rojo es legítimo y lo que falta es la suite del
front, que es trabajo de F-008 y no de F-004.

## Estado de `bash harness/init.sh`

Todo en verde **salvo** ese punto:

```
[OK] features.json válido · BACKLOG.md al día · rigor.json válido
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 176 avisos (deuda previa, no bloquea)
22 passed in 0.16s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/dedicacion-api): pytest en verde
[KO] servicio front (services/dedicacion-front): pytest en rojo   <-- ajeno a F-004
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
[OK] PUERTA COBERTURA: N/A (F-004 es de nivel documental: no exige cobertura)
[OK] Ningún .env versionado
[OK] Rama actual: feature/F-004-readme-monorepo
1 comprobaciones fallidas.
```

La suite de la raíz pasa de **11 a 22 tests**: los 11 previos siguen verdes y
los 11 nuevos son los del README.

`ruff check tests/test_f004_readme.py` → `All checks passed!`. No he aplicado
`ruff format`: el repositorio no lo sigue (2 de los 3 ficheros de `tests/` se
reformatearían) e `init.sh` solo ejecuta `ruff check`.

## Qué dejé fuera, a propósito

- **Guía de instalación de PostgreSQL, de Python o de los venv.** El README
  dice qué hace falta y no cómo instalarlo: envejece mal y no es lo que pedía
  el encargo.
- **Documentación de despliegue.** No existe en esta rama; se menciona como
  trabajo en curso y nada más.
- **Detalle de endpoints, atajos de teclado y reglas P1-P5.** Ya están en los
  README de servicio y en `ARCHITECTURE.md`. El README de la raíz enlaza.
- **Traducir el README del transfer**, que aún se titula `porcentajes-transfer`
  en vez de `dedicacion-transfer`. Es la deuda de nombres que `ARCHITECTURE.md`
  manda alinear «en su feature»; no es esta.

## Evidencias

Nivel **`documental`** (`harness/rigor.json`): **no exige fase RED, ni puerta
de cobertura, ni campaña de mutación**. No están «pendientes»: no aplican, y
forzarlas sobre un documento sería expediente vacío. Lo que sí hay:

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite de la raíz) | **22 pasan, 0 fallan** (11 previos + 11 de F-004) |
| Tiempo de la suite de la raíz | **0,16 s** |
| Tests nuevos de F-004, aislados | **11 pasan** en **0,02 s** |
| ¿Los tests nuevos son vacuos? | **No**: 3 roturas provocadas, 3 detectadas (trazas arriba) |
| Cobertura de líneas cambiadas | **N/A** — nivel documental; `init.sh` lo confirma: `PUERTA COBERTURA: N/A` |
| Mutación | **N/A** — nivel documental. Además, lo cambiado es Markdown y aserciones sobre texto: no hay lógica que mutar |
| Enlaces relativos del README | **13 comprobados, 0 rotos** |
| Secretos detectados | **0** (barrido por patrones; `127.0.0.1` es loopback) |

## Verificaciones MANUAL (humano) pendientes

**Ninguna de F-004.** Es documentación: no toca Sigrid, ni la BBDD, ni `.env`,
ni ejecuta nada contra producción.

Sí conviene que el humano **lea el apartado «Estado del proyecto»** del README
y confirme que la foto le parece justa, porque es la única parte que no se
puede verificar contra el código: es un juicio sobre en qué punto está el
proyecto.

## Qué falta para cerrar

1. Que el líder decida sobre el rojo del front (arreglo en `init.sh` + su
   propagación a `arnes-base`, o asumir que falta la suite del front).
2. `bash harness/init.sh` en verde.
3. Revisión del reviewer contra `CHECKPOINTS.md` y los tres `acceptance`.
4. Cuando F-008 se integre en `dev`: actualizar en el README la frase sobre
   infraestructura «en curso en su propia rama, sin integrar».
