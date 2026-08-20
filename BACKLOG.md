<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **10 features**, 7 abiertas, 3 terminadas.

En curso: **F-004**.

Bloqueadas: **F-002, F-008**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-002 | Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones | 2 | bloqueada | critico | `feature/F-002-reglas-postventa-conflicto` |
| F-008 | Infraestructura y despliegue en Azure | 3 | bloqueada | critico | `feature/F-008-infra-azure` |
| F-004 | README del monorepo y arranque local en orden | 4 | en curso | documental | `feature/F-004-readme-monorepo` |
| F-005 | Alinear los literales internos con el nombre «dedicación» | 5 | pendiente | estandar | `feature/F-005-nomenclatura-dedicacion` |
| F-006 | Sanear la suite del transfer | 6 | pendiente | estandar | `feature/F-006-sanear-suite-transfer` |
| F-011 | Un solo codigo de hora mes por trabajador | 7 | pendiente | estandar | `feature/F-011-codigo-hora-mes-unico` |
| F-012 | El test de la epsilon compartida ata el transfer al monorepo | 8 | pendiente | estandar | `feature/F-012-epsilon-compartida-entre-servicios` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Primera suite de tests de dedicacion-api: la regla del 100 % | 1 | estandar |
| F-003 | Las columnas sigrid_* de asignacion no están en el ORM | 3 | critico |
| F-009 | Higiene: los artefactos de cobertura no se versionan | 9 | estandar |

## Detalle

### F-002 · Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones

estado **bloqueada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-reglas-postventa-conflicto`

El repositorio se contradice sobre dos reglas que deciden qué se escribe en Sigrid. P5: el README del transfer dice obra POSTV2 e imputación por PARTIDA; el docstring de reglas_porcentajes.py dice 'postventa-2' y CAPÍTULO. P4: el README dice que en obra normal una línea M* previa del recurso choca aunque tenga otra partida; el docstring exige que la partida sea la misma. Hay que confirmar la regla buena con Administración y con datos reales de Sigrid, dejarla en una sola fuente de verdad (docs/ARCHITECTURE.md) y alinear código, docstrings y README. Sin esto, no se debe escribir en producción.

### F-008 · Infraestructura y despliegue en Azure

estado **bloqueada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-008-infra-azure`

Hoy no hay nada desplegado ni carpeta infra/. Provisionar los recursos siguiendo el patrón de partes (Container Apps, imágenes en acralbaranesdev con tag fechado, secretos en Key Vault por identidad gestionada, Easy Auth en el front), decidir dónde vive la BBDD dedicacion, y escribir el documento del proyecto en azure-apps. El transfer arranca en modo pruebas y solo sale de él con decisión expresa.

### F-004 · README del monorepo y arranque local en orden

estado **en curso** · prioridad 4 · rigor `documental` · SDD no · rama `feature/F-004-readme-monorepo`

El monorepo no tiene README. Hace falta uno que explique los tres servicios, el flujo, y cómo se levanta el sistema en local en el orden que funciona (transfer 8006 -> api 8090 -> front 8080), con la copia de cada .env.example. Hoy esa información está repartida en tres README de servicio y en la cabeza de quien lo escribió.

### F-005 · Alinear los literales internos con el nombre «dedicación»

estado **pendiente** · prioridad 5 · rigor `estandar` · SDD sí · rama `feature/F-005-nomenclatura-dedicacion`

El proyecto se llama de dos maneras y el humano decidió el 2026-08-19 el reparto: el nombre de dominio y de los servicios es «dedicación» (las carpetas ya son dedicacion-*), la carpeta del monorepo se queda como «porcentajes», y la synckey 'porcentajes:{id}' NO se toca, porque es un identificador funcional escrito en Sigrid y cambiarlo invalidaría la idempotencia de lo ya registrado. Queda alinear lo que aún dice otra cosa: service_name del transfer, sus README y los literales internos, y dejar las dos decisiones escritas donde se busquen.

### F-006 · Sanear la suite del transfer

estado **pendiente** · prioridad 6 · rigor `estandar` · SDD no · rama `feature/F-006-sanear-suite-transfer`

tests/test_pipeline_offline.py tiene un test que devuelve un objeto Preflight en vez de comprobarlo con assert: pytest lo avisa y ese test no verifica nada. Se revisa la suite entera con el mismo criterio.

### F-011 · Un solo codigo de hora mes por trabajador

estado **pendiente** · prioridad 7 · rigor `estandar` · SDD no · rama `feature/F-011-codigo-hora-mes-unico`

Detectado el 2026-08-19 al revisar el original porcentajes-transfer. Cuando un recurso tiene varios codigos de hora mensual (MENC, MJEFO...), reglas_porcentajes.py:105 elige el PRIMERO POR ORDEN ALFABETICO y de ahi sale el importe mensual (pre) que se escribe en Sigrid. Es una heuristica que nadie ha confirmado y que puede escribir un importe distinto del correcto. Decision del humano: de momento se deja el primero, y se abre esta feature para que la situacion no se de. Dos partes: que el sistema avise en el preflight cuando un recurso tenga mas de un codigo M* vigente (hoy solo lo escribe en el log, donde nadie lo ve), y llevar a Administracion la peticion de que en Sigrid un trabajador solo pueda tener un codigo de hora mes.

### F-012 · El test de la epsilon compartida ata el transfer al monorepo

estado **pendiente** · prioridad 8 · rigor `estandar` · SDD no · rama `feature/F-012-epsilon-compartida-entre-servicios`

Detectado por la review de la Fase 2 de F-002 (observacion 9.4). El test test_f002_r26_la_tolerancia_es_la_del_cuadrante navega con Path(__file__).resolve().parents[3] hasta services/dedicacion-api/domain/estados.py para comprobar que la tolerancia del transfer (0.00005) sigue siendo el equivalente exacto del _EPSILON del cuadrante (0.005 en escala 0-100). La decision es la correcta y NO viola el limite de servicio: no importa codigo ni duplica logica, y sin ese test las dos epsilon se separarian sin que nadie se entere. Pero ata la suite del transfer a la disposicion del monorepo: si algun dia el servicio se extrae a su propio repositorio, el test se cae con un error de ruta en vez de con el mensaje de negocio que lleva escrito. Hay que decidir como se vigila esa invariante entre servicios sin depender de rutas relativas.

### F-001 · Primera suite de tests de dedicacion-api: la regla del 100 %

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-tests-estados-api`

Calentamiento del circuito. dedicacion-api no tiene un solo test: se crea services/dedicacion-api/tests/ y se cubre domain/estados.py, que es donde vive la regla de control del cuadrante (OK / FALTA / EXCESO / SIN_CARGA). Sirve para validar rama, acceptance, implementer, reviewer y cierre sobre algo pequeño y sin riesgo, y para que el portero empiece a ejecutar de verdad la suite del servicio api.

### F-003 · Las columnas sigrid_* de asignacion no están en el ORM

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-orm-columnas-sigrid`

application/registro_sigrid.py añade seis columnas (sigrid_estado, sigrid_parte_cod, sigrid_hmores_ide, sigrid_motivo, sigrid_registrado_at_utc, sigrid_registrado_by) con una lista de ALTER TABLE escrita a mano, y orm_models.py no las declara. Es exactamente la avería que en el proyecto partes costó una corrección entera (F-010): dos verdades del esquema que divergen. Las columnas van al ORM y el DDL complementario se deriva de él.

### F-009 · Higiene: los artefactos de cobertura no se versionan

estado **terminada** · prioridad 9 · rigor `estandar` · SDD no · rama `feature/F-009-higiene-coverage-gitignore`

Detectado al cerrar F-001. El repositorio versiona seis ficheros generados (.coverage y coverage.json de la raiz, del transfer y del api) que harness/init.sh reescribe en cada ejecucion: el portero ensucia git status cada vez que corre y sube la probabilidad de arrastrar ruido a un commit. Hay que anadirlos a .gitignore y sacarlos del indice con git rm --cached. Como el .gitignore lo deja el instalador del arnes, por la regla de propagacion el mismo arreglo va a arnes-base.
