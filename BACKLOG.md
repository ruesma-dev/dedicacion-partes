<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **14 features**, 7 abiertas, 7 terminadas.

En curso: **F-008**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-008 | Infraestructura y despliegue en Azure | 3 | en curso | critico | `feature/F-008-infra-azure` |
| F-005 | Alinear los literales internos con el nombre «dedicación» | 5 | pendiente | estandar | `feature/F-005-nomenclatura-dedicacion` |
| F-006 | Sanear la suite del transfer | 6 | pendiente | estandar | `feature/F-006-sanear-suite-transfer` |
| F-011 | Un solo codigo de hora mes por trabajador | 7 | pendiente | estandar | `feature/F-011-codigo-hora-mes-unico` |
| F-012 | El test de la epsilon compartida ata el transfer al monorepo | 8 | pendiente | estandar | `feature/F-012-epsilon-compartida-entre-servicios` |
| F-016 | Una function key de solo lectura para dedicacion-api | 9 | pendiente | estandar | `feature/F-016-sigrid-key-solo-lectura` |
| F-014 | Cerrar los cabos de Sigrid y Administracion que quedaron de F-002 y T14 | 20 | pendiente | documental | `feature/F-014-cabos-sigrid-administracion` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Primera suite de tests de dedicacion-api: la regla del 100 % | 1 | estandar |
| F-002 | Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones | 2 | critico |
| F-003 | Las columnas sigrid_* de asignacion no están en el ORM | 3 | critico |
| F-004 | README del monorepo y arranque local en orden | 4 | documental |
| F-013 | Una linea sin partida no se escribe en silencio | 4 | critico |
| F-015 | Alta en el Portal Ruesma: tarjeta y usuarios del grupo | 4 | documental |
| F-009 | Higiene: los artefactos de cobertura no se versionan | 9 | estandar |

## Detalle

### F-008 · Infraestructura y despliegue en Azure

estado **en curso** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-008-infra-azure`

Hoy no hay nada desplegado ni carpeta infra/. Provisionar los recursos siguiendo el patrón de partes (Container Apps, imágenes en acralbaranesdev con tag fechado, secretos en Key Vault por identidad gestionada, Easy Auth en el front), decidir dónde vive la BBDD dedicacion, y escribir el documento del proyecto en azure-apps. El transfer arranca en modo pruebas y solo sale de él con decisión expresa.

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

### F-016 · Una function key de solo lectura para dedicacion-api

estado **pendiente** · prioridad 9 · rigor `estandar` · SDD no · rama `feature/F-016-sigrid-key-solo-lectura`

Decision D5 de F-008, que se estaba cayendo por la rendija: viajaba dentro de T30, T30 se movio a F-015 y F-015 solo se llevo la mitad del Portal. La review de cierre de F-008 la busco en las trece entradas del backlog y no aparecia en ninguna. El problema: la api y el transfer comparten HOY la misma function key de sigrid-api, y lo unico que impide que la api escriba en el ERP es que su codigo no tiene rutas de escritura, NO la credencial. Es decir, la separacion es por disciplina, no por permisos: cualquiera que anada por error una llamada de escritura a la api tendria credencial para ejecutarla. Hay que preguntar al dueno de sigrid-api si puede emitir una clave de SOLO LECTURA y, si puede, desplegarla en la api. Si no puede, hay que dejar escrito que la separacion depende del codigo y que eso es un riesgo aceptado a conciencia.

### F-014 · Cerrar los cabos de Sigrid y Administracion que quedaron de F-002 y T14

estado **pendiente** · prioridad 20 · rigor `documental` · SDD no · rama `feature/F-014-cabos-sigrid-administracion`

Decision del humano el 2026-08-20: estas dos cosas dejan de bloquear F-002 y la fase 7 de F-008, y se agrupan aqui con prioridad baja. (1) LIMPIEZA EN SIGRID: quedo viva la fila de la primera escritura real del sistema, hmores.ide=403039, synckey 'porcentajes:77', marca PRUEBA-PORC, en el parte PT26/00296 (hmo.ide=2820419) de la obra de pruebas 0404, escrita el 2026-08-20. El humano queria verla en la pantalla del ERP antes de borrarla. Se borra con 'prueba_escritura_porcentajes.py limpiar --confirmar --ano 2026 --mes 7', que solo toca lo marcado PRUEBA-PORC; la cabecera del parte quedaria creada y vacia y hay que decidir si se borra tambien. OJO: cuando se pruebe el registro desde Azure se escribiran MAS lineas PRUEBA-PORC en la misma obra y mes, indistinguibles de esa, asi que conviene hacerlo antes o asumir que habra que distinguirlas por ide. (2) ADMINISTRACION: avisar de las cuatro partidas duplicadas sin cero inicial en el presupuesto de POSTV2 (656, 664, 680, 693, colgando de la raiz en vez de CD; tabla en progress/sigrid_F-002.md), y decidir si la procedencia de las reglas P4/P5 la firma el responsable del proyecto (como hoy) o pasa por Administracion. El test de procedencia no clava el interlocutor, asi que cambiar esa linea no rompe nada. ANADIDO al cerrar F-002 (review de cierre, seccion 5): la Regla B de capacidad del 100 % esta implementada y probada offline (35 tests, cobertura y mutacion), pero NUNCA se ha ejercitado contra Sigrid real, porque el preflight de julio no llego a dispararla: el parte de la obra destino no existia y por tanto no habia lineas M* previas con las que chocar. No es un defecto de F-002. Conviene que la primera vez que un parte real tenga lineas M* previas alguien mire ese preflight con atencion. ESTADO 2026-08-20: los dos puntos de Sigrid (limpieza y cabecera del parte) estan CERRADOS. Queda solo lo de Administracion: el aviso de las cuatro partidas duplicadas, quien firma la procedencia, y mirar el primer preflight real que tenga lineas M* previas para ver la Regla B ejercitada.

### F-001 · Primera suite de tests de dedicacion-api: la regla del 100 %

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-tests-estados-api`

Calentamiento del circuito. dedicacion-api no tiene un solo test: se crea services/dedicacion-api/tests/ y se cubre domain/estados.py, que es donde vive la regla de control del cuadrante (OK / FALTA / EXCESO / SIN_CARGA). Sirve para validar rama, acceptance, implementer, reviewer y cierre sobre algo pequeño y sin riesgo, y para que el portero empiece a ejecutar de verdad la suite del servicio api.

### F-002 · Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-reglas-postventa-conflicto`

El repositorio se contradice sobre dos reglas que deciden qué se escribe en Sigrid. P5: el README del transfer dice obra POSTV2 e imputación por PARTIDA; el docstring de reglas_porcentajes.py dice 'postventa-2' y CAPÍTULO. P4: el README dice que en obra normal una línea M* previa del recurso choca aunque tenga otra partida; el docstring exige que la partida sea la misma. Hay que confirmar la regla buena con Administración y con datos reales de Sigrid, dejarla en una sola fuente de verdad (docs/ARCHITECTURE.md) y alinear código, docstrings y README. Sin esto, no se debe escribir en producción.

### F-003 · Las columnas sigrid_* de asignacion no están en el ORM

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-orm-columnas-sigrid`

application/registro_sigrid.py añade seis columnas (sigrid_estado, sigrid_parte_cod, sigrid_hmores_ide, sigrid_motivo, sigrid_registrado_at_utc, sigrid_registrado_by) con una lista de ALTER TABLE escrita a mano, y orm_models.py no las declara. Es exactamente la avería que en el proyecto partes costó una corrección entera (F-010): dos verdades del esquema que divergen. Las columnas van al ORM y el DDL complementario se deriva de él.

### F-004 · README del monorepo y arranque local en orden

estado **terminada** · prioridad 4 · rigor `documental` · SDD no · rama `feature/F-004-readme-monorepo`

El monorepo no tiene README. Hace falta uno que explique los tres servicios, el flujo, y cómo se levanta el sistema en local en el orden que funciona (transfer 8006 -> api 8090 -> front 8080), con la copia de cada .env.example. Hoy esa información está repartida en tres README de servicio y en la cabeza de quien lo escribió.

### F-013 · Una linea sin partida no se escribe en silencio

estado **terminada** · prioridad 4 · rigor `critico` · SDD no · rama `feature/F-013-linea-sin-partida-confirma`

Decision del humano el 2026-08-20, al ver el preflight real de julio: hoy, cuando el casado de partida falla en obra normal, registro_pipeline.py pone paride=0 y deja un aviso informativo, pero LA LINEA SE ESCRIBE IGUAL. En el preflight de julio eso eran 2.132 EUR de una jefa de obra colgando de la obra sin imputar a ninguna partida. La regla nueva: debe AVISAR Y ESPERAR CONFIRMACION, igual que la sobrecarga del 100 % que introdujo F-002. El mecanismo ya existe y no hay que inventarlo: la Regla B de F-002 emite un Conflicto con motivo propio que viaja al front sin tocar dedicacion-api ni dedicacion-front. Esto es aplicar ese mismo patron a un tercer caso. Sale de F-002 y no dentro, porque F-002 esta blocked por motivos ajenos (Administracion) y sus fases 1 y 2 ya estan aprobadas y mergeadas.

### F-015 · Alta en el Portal Ruesma: tarjeta y usuarios del grupo

estado **terminada** · prioridad 4 · rigor `documental` · SDD sí · rama `dev`

Pedida por el humano el 2026-08-20, con el sistema ya desplegado. Sin esto el sistema esta vivo pero nadie puede llegar a el: no hay tarjeta en el Portal Ruesma desde la que entrar, y solo tiene acceso quien ya este en el grupo de Entra. Dos partes. (1) TARJETA: pasar al proyecto front-portal la URL publica del front (ca-dedicacion-front.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io) y el objectId del grupo 'dedicacion-portal-users' para que anada la tarjeta. El objectId NO se escribe en este repositorio: se saca con 'az ad group show --group dedicacion-portal-users --query id -o tsv' y se pasa por el canal que se use con ese proyecto. Es trabajo que cruza la frontera del proyecto, asi que hay que mirar antes el documento de front-portal en azure-apps/. (2) USUARIOS: decidir quien entra (la decision D3 de F-008, que quedo abierta) y darles de alta con 'infra/setup_front_easyauth.ps1 -Miembros persona@ruesma.es'. La Enterprise App tiene asignacion requerida, asi que quien no este en el grupo no obtiene token: no basta con tener cuenta de Ruesma. Sale de F-008 (era su T30) para que aquella pueda cerrarse. DECISIONES DEL HUMANO 2026-08-20: el icono lo elige el lider ('chart', por ser un cuadrante de porcentajes y no una comparativa); y la tarjeta se deja PUESTA CON EL GRUPO CONFIGURADO pero SIN dar de alta usuarios: el humano los mete a mano cuando decida quien entra. Con eso D3 deja de bloquear la feature. NOTA DE METODO: esta feature se trabajo directamente en 'dev', sin rama propia, y el campo branch lo dice. El CLAUDE.md exige rama por feature; la excepcion se toma a conciencia y se deja escrita: F-015 no toca una linea de codigo de este repositorio (su unico cambio real vive en front-portal, otro repo), y se hizo intercalada con el despliegue en vivo de F-008, donde el arbol tenia que estar en dev para arreglar los scripts sobre la marcha. Rehacer la historia ahora seria peor que el problema: los commits estan en origin/dev.

### F-009 · Higiene: los artefactos de cobertura no se versionan

estado **terminada** · prioridad 9 · rigor `estandar` · SDD no · rama `feature/F-009-higiene-coverage-gitignore`

Detectado al cerrar F-001. El repositorio versiona seis ficheros generados (.coverage y coverage.json de la raiz, del transfer y del api) que harness/init.sh reescribe en cada ejecucion: el portero ensucia git status cada vez que corre y sube la probabilidad de arrastrar ruido a un commit. Hay que anadirlos a .gitignore y sacarlos del indice con git rm --cached. Como el .gitignore lo deja el instalador del arnes, por la regla de propagacion el mismo arreglo va a arnes-base.
