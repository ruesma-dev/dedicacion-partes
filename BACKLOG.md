<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **8 features**, 8 abiertas, 0 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-001 | Primera suite de tests de dedicacion-api: la regla del 100 % | 1 | pendiente | estandar | `feature/F-001-tests-estados-api` |
| F-002 | Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones | 2 | pendiente | critico | `feature/F-002-reglas-postventa-conflicto` |
| F-003 | Las columnas sigrid_* de asignacion no están en el ORM | 3 | pendiente | critico | `feature/F-003-orm-columnas-sigrid` |
| F-004 | Paginación real contra sigrid-api: el tope son 1.000 filas | 4 | pendiente | estandar | `feature/F-004-paginacion-sigrid` |
| F-005 | README del monorepo y arranque local en orden | 5 | pendiente | documental | `feature/F-005-readme-monorepo` |
| F-006 | Unificar la nomenclatura a «dedicación» | 6 | pendiente | estandar | `feature/F-006-nomenclatura-dedicacion` |
| F-007 | Sanear la suite del transfer | 7 | pendiente | estandar | `feature/F-007-sanear-suite-transfer` |
| F-008 | Infraestructura y despliegue en Azure | 8 | pendiente | critico | `feature/F-008-infra-azure` |

## Terminadas

_Todavía no hay features terminadas._

## Detalle

### F-001 · Primera suite de tests de dedicacion-api: la regla del 100 %

estado **pendiente** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-tests-estados-api`

Calentamiento del circuito. dedicacion-api no tiene un solo test: se crea services/dedicacion-api/tests/ y se cubre domain/estados.py, que es donde vive la regla de control del cuadrante (OK / FALTA / EXCESO / SIN_CARGA). Sirve para validar rama, acceptance, implementer, reviewer y cierre sobre algo pequeño y sin riesgo, y para que el portero empiece a ejecutar de verdad la suite del servicio api.

### F-002 · Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones

estado **pendiente** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-reglas-postventa-conflicto`

El repositorio se contradice sobre dos reglas que deciden qué se escribe en Sigrid. P5: el README del transfer dice obra POSTV2 e imputación por PARTIDA; el docstring de reglas_porcentajes.py dice 'postventa-2' y CAPÍTULO. P4: el README dice que en obra normal una línea M* previa del recurso choca aunque tenga otra partida; el docstring exige que la partida sea la misma. Hay que confirmar la regla buena con Administración y con datos reales de Sigrid, dejarla en una sola fuente de verdad (docs/ARCHITECTURE.md) y alinear código, docstrings y README. Sin esto, no se debe escribir en producción.

### F-003 · Las columnas sigrid_* de asignacion no están en el ORM

estado **pendiente** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-orm-columnas-sigrid`

application/registro_sigrid.py añade seis columnas (sigrid_estado, sigrid_parte_cod, sigrid_hmores_ide, sigrid_motivo, sigrid_registrado_at_utc, sigrid_registrado_by) con una lista de ALTER TABLE escrita a mano, y orm_models.py no las declara. Es exactamente la avería que en el proyecto partes costó una corrección entera (F-010): dos verdades del esquema que divergen. Las columnas van al ORM y el DDL complementario se deriva de él.

### F-004 · Paginación real contra sigrid-api: el tope son 1.000 filas

estado **pendiente** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-004-paginacion-sigrid`

config/settings.py de la API declara SIGRID_MAX_ROWS=5000, pero sigrid-api sirve como máximo 1.000 filas por petición y avisa con el campo 'truncated'. Si la consulta de empleados o de obras crece, el sync se queda con parte de los maestros sin que nada falle. Hay que paginar según el patrón obligatorio de azure-apps/sigrid_api.md y tratar 'truncated' como error, no como aviso silencioso.

### F-005 · README del monorepo y arranque local en orden

estado **pendiente** · prioridad 5 · rigor `documental` · SDD no · rama `feature/F-005-readme-monorepo`

El monorepo no tiene README. Hace falta uno que explique los tres servicios, el flujo, y cómo se levanta el sistema en local en el orden que funciona (transfer 8006 -> api 8090 -> front 8080), con la copia de cada .env.example. Hoy esa información está repartida en tres README de servicio y en la cabeza de quien lo escribió.

### F-006 · Unificar la nomenclatura a «dedicación»

estado **pendiente** · prioridad 6 · rigor `estandar` · SDD sí · rama `feature/F-006-nomenclatura-dedicacion`

El proyecto se llama de dos maneras. Las carpetas ya son dedicacion-*; quedan por decidir y alinear el nombre del repositorio, el service_name del transfer, sus README y los literales internos. Caso aparte: la synckey es 'porcentajes:{id}' y es un identificador funcional escrito en Sigrid — cambiarla invalidaría la idempotencia de lo ya registrado, así que se decide expresamente si se toca o se congela con un comentario que explique por qué.

### F-007 · Sanear la suite del transfer

estado **pendiente** · prioridad 7 · rigor `estandar` · SDD no · rama `feature/F-007-sanear-suite-transfer`

tests/test_pipeline_offline.py tiene un test que devuelve un objeto Preflight en vez de comprobarlo con assert: pytest lo avisa y ese test no verifica nada. Se revisa la suite entera con el mismo criterio.

### F-008 · Infraestructura y despliegue en Azure

estado **pendiente** · prioridad 8 · rigor `critico` · SDD sí · rama `feature/F-008-infra-azure`

Hoy no hay nada desplegado ni carpeta infra/. Provisionar los recursos siguiendo el patrón de partes (Container Apps, imágenes en acralbaranesdev con tag fechado, secretos en Key Vault por identidad gestionada, Easy Auth en el front), decidir dónde vive la BBDD dedicacion, y escribir el documento del proyecto en azure-apps. El transfer arranca en modo pruebas y solo sale de él con decisión expresa.
