<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **10 features**, 8 abiertas, 2 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-002 | Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones | 2 | pendiente | critico | `feature/F-002-reglas-postventa-conflicto` |
| F-003 | Las columnas sigrid_* de asignacion no están en el ORM | 3 | pendiente | critico | `feature/F-003-orm-columnas-sigrid` |
| F-004 | README del monorepo y arranque local en orden | 4 | pendiente | documental | `feature/F-004-readme-monorepo` |
| F-005 | Alinear los literales internos con el nombre «dedicación» | 5 | pendiente | estandar | `feature/F-005-nomenclatura-dedicacion` |
| F-006 | Sanear la suite del transfer | 6 | pendiente | estandar | `feature/F-006-sanear-suite-transfer` |
| F-007 | Propagar a arnes-base dos defectos del instalador | 7 | pendiente | estandar | `feature/F-007-propagar-defectos-instalador` |
| F-008 | Infraestructura y despliegue en Azure | 8 | pendiente | critico | `feature/F-008-infra-azure` |
| F-010 | Automejoras del arnes propuestas al revisar F-001 | 10 | pendiente | documental | `feature/F-010-automejoras-arnes-reviewer` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Primera suite de tests de dedicacion-api: la regla del 100 % | 1 | estandar |
| F-009 | Higiene: los artefactos de cobertura no se versionan | 9 | estandar |

## Detalle

### F-002 · Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones

estado **pendiente** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-reglas-postventa-conflicto`

El repositorio se contradice sobre dos reglas que deciden qué se escribe en Sigrid. P5: el README del transfer dice obra POSTV2 e imputación por PARTIDA; el docstring de reglas_porcentajes.py dice 'postventa-2' y CAPÍTULO. P4: el README dice que en obra normal una línea M* previa del recurso choca aunque tenga otra partida; el docstring exige que la partida sea la misma. Hay que confirmar la regla buena con Administración y con datos reales de Sigrid, dejarla en una sola fuente de verdad (docs/ARCHITECTURE.md) y alinear código, docstrings y README. Sin esto, no se debe escribir en producción.

### F-003 · Las columnas sigrid_* de asignacion no están en el ORM

estado **pendiente** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-orm-columnas-sigrid`

application/registro_sigrid.py añade seis columnas (sigrid_estado, sigrid_parte_cod, sigrid_hmores_ide, sigrid_motivo, sigrid_registrado_at_utc, sigrid_registrado_by) con una lista de ALTER TABLE escrita a mano, y orm_models.py no las declara. Es exactamente la avería que en el proyecto partes costó una corrección entera (F-010): dos verdades del esquema que divergen. Las columnas van al ORM y el DDL complementario se deriva de él.

### F-004 · README del monorepo y arranque local en orden

estado **pendiente** · prioridad 4 · rigor `documental` · SDD no · rama `feature/F-004-readme-monorepo`

El monorepo no tiene README. Hace falta uno que explique los tres servicios, el flujo, y cómo se levanta el sistema en local en el orden que funciona (transfer 8006 -> api 8090 -> front 8080), con la copia de cada .env.example. Hoy esa información está repartida en tres README de servicio y en la cabeza de quien lo escribió.

### F-005 · Alinear los literales internos con el nombre «dedicación»

estado **pendiente** · prioridad 5 · rigor `estandar` · SDD sí · rama `feature/F-005-nomenclatura-dedicacion`

El proyecto se llama de dos maneras y el humano decidió el 2026-08-19 el reparto: el nombre de dominio y de los servicios es «dedicación» (las carpetas ya son dedicacion-*), la carpeta del monorepo se queda como «porcentajes», y la synckey 'porcentajes:{id}' NO se toca, porque es un identificador funcional escrito en Sigrid y cambiarlo invalidaría la idempotencia de lo ya registrado. Queda alinear lo que aún dice otra cosa: service_name del transfer, sus README y los literales internos, y dejar las dos decisiones escritas donde se busquen.

### F-006 · Sanear la suite del transfer

estado **pendiente** · prioridad 6 · rigor `estandar` · SDD no · rama `feature/F-006-sanear-suite-transfer`

tests/test_pipeline_offline.py tiene un test que devuelve un objeto Preflight en vez de comprobarlo con assert: pytest lo avisa y ese test no verifica nada. Se revisa la suite entera con el mismo criterio.

### F-007 · Propagar a arnes-base dos defectos del instalador

estado **pendiente** · prioridad 7 · rigor `estandar` · SDD no · rama `feature/F-007-propagar-defectos-instalador`

Detectados el 2026-08-19 instalando el arnés aquí, y valen para cualquier proyecto, así que por la regla de propagación van a arnes-base. (1) El instalador copia al proyecto destino su propio .pytest_cache/ y los __pycache__/ del payload: 9 de los 44 ficheros de una instalación limpia eran basura, y hubo que borrarlos a mano. (2) No copia el .gitattributes, que sí existe en arnes-base, así que el primer commit de un repositorio nuevo sale con avisos de CRLF en cada fichero. El arreglo va en arnes-base (excluir cachés del payload o limpiarlo antes de copiar, y añadir .gitattributes a lo que se instala), no aquí.

### F-008 · Infraestructura y despliegue en Azure

estado **pendiente** · prioridad 8 · rigor `critico` · SDD sí · rama `feature/F-008-infra-azure`

Hoy no hay nada desplegado ni carpeta infra/. Provisionar los recursos siguiendo el patrón de partes (Container Apps, imágenes en acralbaranesdev con tag fechado, secretos en Key Vault por identidad gestionada, Easy Auth en el front), decidir dónde vive la BBDD dedicacion, y escribir el documento del proyecto en azure-apps. El transfer arranca en modo pruebas y solo sale de él con decisión expresa.

### F-010 · Automejoras del arnes propuestas al revisar F-001

estado **pendiente** · prioridad 10 · rigor `documental` · SDD no · rama `feature/F-010-automejoras-arnes-reviewer`

Tres huecos del protocolo que dejo ver la review de F-001, los tres validos para cualquier proyecto (van tambien a arnes-base). (1) CHECKPOINTS.md C4 bis no dice que hacer cuando TODA la feature cae en DIRECTORIOS_EXCLUIDOS y salen a la vez cobertura N/A y mutacion 0: la evidencia sustitutiva debe ser una campana de mutacion sobre el fichero de produccion que los tests nuevos cubren, y el reviewer la reproduce. (2) .claude/agents/reviewer.md: cuando el alcance salga vacio, anadir el control positivo (generar mutantes del fichero cubierto y ejecutarlos contra la suite), no solo el control de que el generador funciona. (3) La cache del portero puede ensenar un [OK] de un servicio sin que la suite se haya ejecutado en esa sesion: el protocolo del reviewer debe obligar a lanzarla a mano en ese caso.

### F-001 · Primera suite de tests de dedicacion-api: la regla del 100 %

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-tests-estados-api`

Calentamiento del circuito. dedicacion-api no tiene un solo test: se crea services/dedicacion-api/tests/ y se cubre domain/estados.py, que es donde vive la regla de control del cuadrante (OK / FALTA / EXCESO / SIN_CARGA). Sirve para validar rama, acceptance, implementer, reviewer y cierre sobre algo pequeño y sin riesgo, y para que el portero empiece a ejecutar de verdad la suite del servicio api.

### F-009 · Higiene: los artefactos de cobertura no se versionan

estado **terminada** · prioridad 9 · rigor `estandar` · SDD no · rama `feature/F-009-higiene-coverage-gitignore`

Detectado al cerrar F-001. El repositorio versiona seis ficheros generados (.coverage y coverage.json de la raiz, del transfer y del api) que harness/init.sh reescribe en cada ejecucion: el portero ensucia git status cada vez que corre y sube la probabilidad de arrastrar ruido a un commit. Hay que anadirlos a .gitignore y sacarlos del indice con git rm --cached. Como el .gitignore lo deja el instalador del arnes, por la regla de propagacion el mismo arreglo va a arnes-base.
