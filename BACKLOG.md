<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **29 features**, 21 abiertas, 8 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-017 | Probar con Administracion sobre la obra de pruebas 0404 | 1 | pendiente | documental | `feature/F-017-prueba-administracion` |
| F-018 | Pasar a escritura real cuando Administracion apruebe | 2 | pendiente | critico | `feature/F-018-paso-a-escritura-real` |
| F-022 | El transfer busca cada obra por código y empresa | 2 | pendiente | critico | `feature/F-022-transfer-obra-por-empresa` |
| F-023 | Sync de maestros: todas las empresas y activo según el estado del recurso | 2 | spec lista | critico | `feature/F-023-sync-empresa-y-estado-recurso` |
| F-019 | Excel de importacion en formato Carmen | 3 | pendiente | estandar | `feature/F-019-excel-formato-carmen` |
| F-025 | Obras de postventa sacadas de los capítulos de POSTV2 | 3 | pendiente | critico | `feature/F-025-obras-postventa-postv2` |
| F-026 | Recursos sin ficha de empleado no salen: el caso Eusebio Vindel Duro | 3 | pendiente | critico | `feature/F-026-recursos-sin-ficha-empleado` |
| F-020 | Revisar y mejorar el formato del Excel de exportacion actual | 4 | pendiente | estandar | `feature/F-020-mejorar-excel-exportacion` |
| F-024 | Selector de empresa arriba a la derecha, Construcciones Ruesma por defecto | 4 | pendiente | estandar | `feature/F-024-selector-empresa` |
| F-027 | Deshacer solo lo propio: nadie deshace lo de otro usuario | 4 | pendiente | estandar | `feature/F-027-deshacer-por-usuario` |
| F-005 | Alinear los literales internos con el nombre «dedicación» | 5 | pendiente | estandar | `feature/F-005-nomenclatura-dedicacion` |
| F-028 | Borrar todo lo que está en pantalla | 5 | pendiente | estandar | `feature/F-028-borrar-todo-filtrado` |
| F-006 | Sanear la suite del transfer | 6 | pendiente | estandar | `feature/F-006-sanear-suite-transfer` |
| F-029 | Selección múltiple con Ctrl/Shift y completar hasta el 100 % en la obra filtrada | 6 | pendiente | estandar | `feature/F-029-seleccion-multiple-completar-100` |
| F-030 | Dedicación por días, bajas e incidencias con calendario del trabajador | 6 | pendiente | critico | `feature/F-030-dias-bajas-incidencias` |
| F-011 | Un solo codigo de hora mes por trabajador | 7 | pendiente | estandar | `feature/F-011-codigo-hora-mes-unico` |
| F-012 | El test de la epsilon compartida ata el transfer al monorepo | 8 | pendiente | estandar | `feature/F-012-epsilon-compartida-entre-servicios` |
| F-016 | Una function key de solo lectura para dedicacion-api | 9 | pendiente | estandar | `feature/F-016-sigrid-key-solo-lectura` |
| F-021 | Filtro por obra: solo su chip y los recursos asignados en Sesame | 10 | pendiente | estandar | `feature/F-021-filtro-obra-chip-unico` |
| F-031 | MCP para que una IA haga el trabajo del usuario | 11 | pendiente | critico | `feature/F-031-mcp-ia` |
| F-014 | Cerrar los cabos de Sigrid y Administracion que quedaron de F-002 y T14 | 20 | pendiente | documental | `feature/F-014-cabos-sigrid-administracion` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Primera suite de tests de dedicacion-api: la regla del 100 % | 1 | estandar |
| F-002 | Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones | 2 | critico |
| F-003 | Las columnas sigrid_* de asignacion no están en el ORM | 3 | critico |
| F-008 | Infraestructura y despliegue en Azure | 3 | critico |
| F-004 | README del monorepo y arranque local en orden | 4 | documental |
| F-013 | Una linea sin partida no se escribe en silencio | 4 | critico |
| F-015 | Alta en el Portal Ruesma: tarjeta y usuarios del grupo | 4 | documental |
| F-009 | Higiene: los artefactos de cobertura no se versionan | 9 | estandar |

## Detalle

### F-017 · Probar con Administracion sobre la obra de pruebas 0404

estado **pendiente** · prioridad 1 · rigor `documental` · SDD no · rama `feature/F-017-prueba-administracion`

Pedida por el humano el 2026-08-25. El sistema esta desplegado, en uso por 8 personas y escribiendo de verdad en Sigrid, pero TODO se desvia a la obra de pruebas 0404 marcada PRUEBA-PORC. Falta la validacion que nadie ha hecho todavia: que Administracion mire lo que el sistema escribe y diga si es correcto. No toca codigo; si sale un defecto se abre su propia feature en vez de parchearlo aqui. Es la puerta de entrada de F-018 (pasar a real): sin la firma de Administracion, F-018 no arranca.

### F-018 · Pasar a escritura real cuando Administracion apruebe

estado **pendiente** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-018-paso-a-escritura-real`

Pedida por el humano el 2026-08-25, condicionada a F-017. Hoy OBRA_PRUEBAS_FORZAR=true desvia toda escritura a la obra 0404: las obras reales no reciben nada. Quitar ese modo es la accion de mas riesgo de todo el proyecto -escribe en el ERP de produccion, en la base ruesma, y de ahi salen importes- y por eso el repositorio la tiene prohibida sin autorizacion expresa del humano para esa accion concreta. El bloqueador de fondo no es la bandera sino lo que consta en docs/ARCHITECTURE.md: la imputacion a partidas EN PRODUCCION no esta validada. Esta feature cubre resolver eso, el cambio de modo, el primer registro real acotado y la documentacion que deja de ser cierta el dia que se haga. AÑADIDO 2026-09-29: también depende de F-022. El transfer resuelve la obra por código sin empresa y POSTV2 existe en las empresas 1 y 28; sin F-022 la primera escritura real podría caer en la ficha de Porsan.

### F-022 · El transfer busca cada obra por código y empresa

estado **pendiente** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-022-transfer-obra-por-empresa`

Salida de la revisión de negocio del 2026-09-29. Diagnóstico con evidencia en progress/explore_maestros_sync.md. Hallazgo colateral del diagnóstico de maestros (sección D): obra_por_codigo (services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py ~105-126) busca WHERE con.cod = ? sin empresa ni ORDER BY y se queda con la primera fila. POSTV2 tiene dos fichas (empresa 1 Construcciones Ruesma y 28 Porsan), así que el destino de postventa puede caer en la de Porsan según el orden que devuelva SQL Server; lo mismo cualquier obra con copia en otra empresa (81 códigos repetidos). Hoy no hace daño porque OBRA_PRUEBAS_FORZAR desvía todo a la 0404, pero BLOQUEA F-018. Decisión del humano 2026-09-29: se imputa a la empresa filtrada en el cuadrante, así que la empresa viaja en la línea (contrato API -> transfer) y el transfer la usa para resolver la obra. Si una línea llega sin empresa, no se adivina: se rechaza con motivo.

### F-023 · Sync de maestros: todas las empresas y activo según el estado del recurso

estado **spec lista** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-023-sync-empresa-y-estado-recurso`

Salida de la revisión de negocio del 2026-09-29. Diagnóstico con evidencia en progress/explore_maestros_sync.md. Negocio ve recursos inactivos en el cuadrante. Dos causas: (1) la SQL de sync (services/dedicacion-api/config/config.yaml) no lee la empresa (con.emp; Construcciones Ruesma = 1) y mezcla fichas de todas; en obras entran ~140 de otras empresas y 81 códigos salen duplicados; el dedupe por DNI puede quedarse con la ficha de otra empresa. (2) activo se decide por el último emphis sin fecbaj; un emp sin emphis cuenta como activo y se ignora el estado del recurso. Decisión del humano 2026-09-29: inactivo es un ESTADO del recurso en Sigrid; la spec localiza el campo exacto y sus valores en azure-apps/sigrid_tablas.md. Se sincronizan TODAS las empresas guardando la empresa de cada ficha (el filtro lo hace F-024); el dedupe por persona pasa a ser dentro de cada empresa.

### F-019 · Excel de importacion en formato Carmen

estado **pendiente** · prioridad 3 · rigor `estandar` · SDD sí · rama `feature/F-019-excel-formato-carmen`

Pedida por el humano el 2026-09-03. Hoy la API exporta un unico Excel (services/dedicacion-api/infrastructure/excel/exporter.py: hojas Detalle y Resumen, declaradas compatibles con la plantilla v14), pensado para leerlo, no para que otro sistema lo importe. Hace falta poder generar ADEMAS un segundo Excel con otro formato, el que usa Carmen para la importacion adicion. PENDIENTE DE DATOS (la feature no arranca sin esto): el humano tiene que pasar el fichero de ejemplo del formato Carmen -se convierte con markitdown y se guarda en docs/referencia/, el original no se versiona- y explicar que es la importacion adicion y en que sistema entra ese Excel. Sin las dos cosas no hay criterio de aceptacion verificable y lo que se escriba sera una adivinanza.

### F-025 · Obras de postventa sacadas de los capítulos de POSTV2

estado **pendiente** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-025-obras-postventa-postv2`

Salida de la revisión de negocio del 2026-09-29. Diagnóstico con evidencia en progress/explore_maestros_sync.md. Negocio echa en falta obras de postventa. Causa: las obras en postventa están CERRADAS en Sigrid y el filtro estados_excluidos de config.yaml las quita; sin la obra en el maestro el front no ofrece su Postv-XXXX (app.js ~175-191). 69 de 78 obras con postventa en POSTV2 no llegan. Decisión del humano 2026-09-29: la lista de obras de postventa sale de los CAPÍTULOS del proyecto POSTV2, sea cual sea el estado de la obra. Propuesta del líder pendiente de objeción: una obra cerrada se ofrece solo como Postv-, no como obra normal. RIESGOS para la spec: (a) F-002 dejó escrito en docs/ARCHITECTURE.md que P5 imputa por PARTIDA en POSTV2; hay que conciliar capítulos y partidas sin romper esa regla; (b) límite de servicio: POSTVENTA_OBRA_COD vive hoy solo en el transfer; decidir si la API lo lee o pregunta al transfer, pero el universo de postventa del front y el del transfer no pueden divergir.

### F-026 · Recursos sin ficha de empleado no salen: el caso Eusebio Vindel Duro

estado **pendiente** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-026-recursos-sin-ficha-empleado`

Salida de la revisión de negocio del 2026-09-29. Diagnóstico con evidencia en progress/explore_maestros_sync.md. El recurso MO/0772 (Eusebio Vindel Duro, activo, empresa 1, hora MENC) no tiene ficha de empleado enlazada en el data mart, y la SQL de sync parte de dbo.emp enlazando res.conide = emp.ide: un recurso sin empleado no aparece nunca. Hay otros 9 recursos de la empresa 1 en la misma situación, casi todos altas recientes. Aunque entraran, hoy no se registrarían: la API manda empleado_ide y el transfer resuelve el recurso por res.conide. CAUSA RAÍZ (progress/explore_eusebio.md): el recurso tiene vacío «Empleado asociado» (res.conide) y no existe ficha de empleado con su NIF en ninguna empresa del data mart. Es un patrón de alta: ningún ENCARGADO DE OBRA, capataz ni gruista dado de alta recientemente en la empresa 1 lo tiene, y aun así Sigrid les imputa partes (MO/0496 lleva 1.201 líneas desde 2020 sin empleado). MO/0496 es un caso aparte: su ficha de empleado existe pero solo está enlazada a su recurso de la UTE 18, así que probablemente entra en el cuadrante con el recurso de la UTE. Dos salidas: de DATOS (Administración rellena «Empleado asociado» en el recurso; rellenar solo «Recurso relacionado» en el empleado no basta) o de MODELO (el sync parte del recurso, el trabajador se identifica por recurso_ide y se envía recurso_ide al transfer, que ya lo admite). Pregunta abierta para negocio: si encargados y gruistas se dan de alta sin ficha de empleado A PROPÓSITO, el arreglo tiene que ser el de modelo. Quedan tres SELECT por lanzar contra Sigrid para confirmar, escritos en el informe.

### F-020 · Revisar y mejorar el formato del Excel de exportacion actual

estado **pendiente** · prioridad 4 · rigor `estandar` · SDD no · rama `feature/F-020-mejorar-excel-exportacion`

Pedida por el humano el 2026-09-03 junto con F-019, pero separada de ella a proposito: esta se puede hacer ya, sin esperar al formato Carmen. El exportador de hoy (services/dedicacion-api/infrastructure/excel/exporter.py, 172 lineas) nacio para replicar la plantilla v14 y desde entonces nadie ha revisado si el resultado se lee bien: anchos de columna, formato de numero y de porcentaje, cabeceras congeladas, autofiltro, totales y que se ve al imprimir. Hay que revisarlo con el humano delante y mejorarlo. RESTRICCION: hay consumidores externos de la plantilla v14, asi que mover o renombrar columnas de la hoja Detalle puede romper a quien la lee. AÑADIDO 2026-09-29 (revisión de negocio): quitar la columna E de la hoja Detalle, «Obra(código)». El humano confirma que la plantilla solo la lee negocio, así que la restricción de consumidores externos no bloquea este cambio.

### F-024 · Selector de empresa arriba a la derecha, Construcciones Ruesma por defecto

estado **pendiente** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-024-selector-empresa`

Salida de la revisión de negocio del 2026-09-29. Botón/selector de empresa en la esquina superior derecha del cuadrante. Por defecto, Construcciones Ruesma (empresa 1). Filtra obras y recursos que se ven y en qué empresa se imputa: decisión del humano 2026-09-29, se imputa a la empresa filtrada. Depende de F-023 (empresa en los maestros) y alimenta F-022 (la empresa viaja en la línea). El filtrado lo sirve la API; el front no decide nada.

### F-027 · Deshacer solo lo propio: nadie deshace lo de otro usuario

estado **pendiente** · prioridad 4 · rigor `estandar` · SDD no · rama `feature/F-027-deshacer-por-usuario`

Salida de la revisión de negocio del 2026-09-29. Hoy el deshacer es por trabajador y deshace su última modificación (DeshacerUltimaModificacion, ruta /periodos/{anio}/{mes}/trabajadores/{ide}/deshacer; botón y Ctrl+Z en app.js ~563 y ~975) sin mirar quién la hizo. Se pide que un usuario solo pueda deshacer sus propios cambios. La regla vive en la API con el usuario que inyecta el front desde Easy Auth; el front solo oculta el botón.

### F-005 · Alinear los literales internos con el nombre «dedicación»

estado **pendiente** · prioridad 5 · rigor `estandar` · SDD sí · rama `feature/F-005-nomenclatura-dedicacion`

El proyecto se llama de dos maneras y el humano decidió el 2026-08-19 el reparto: el nombre de dominio y de los servicios es «dedicación» (las carpetas ya son dedicacion-*), la carpeta del monorepo se queda como «porcentajes», y la synckey 'porcentajes:{id}' NO se toca, porque es un identificador funcional escrito en Sigrid y cambiarlo invalidaría la idempotencia de lo ya registrado. Queda alinear lo que aún dice otra cosa: service_name del transfer, sus README y los literales internos, y dejar las dos decisiones escritas donde se busquen.

### F-028 · Borrar todo lo que está en pantalla

estado **pendiente** · prioridad 5 · rigor `estandar` · SDD no · rama `feature/F-028-borrar-todo-filtrado`

Salida de la revisión de negocio del 2026-09-29. Botón «Borrar todo». Decisión del humano 2026-09-29: borra SOLO lo filtrado que aparece en pantalla en ese momento, no el mes entero. El borrado lo hace la API sobre la lista de trabajadores que le pasa el front.

### F-006 · Sanear la suite del transfer

estado **pendiente** · prioridad 6 · rigor `estandar` · SDD no · rama `feature/F-006-sanear-suite-transfer`

tests/test_pipeline_offline.py tiene un test que devuelve un objeto Preflight en vez de comprobarlo con assert: pytest lo avisa y ese test no verifica nada. Se revisa la suite entera con el mismo criterio.

### F-029 · Selección múltiple con Ctrl/Shift y completar hasta el 100 % en la obra filtrada

estado **pendiente** · prioridad 6 · rigor `estandar` · SDD sí · rama `feature/F-029-seleccion-multiple-completar-100`

Salida de la revisión de negocio del 2026-09-29. Poder seleccionar varias filas con Ctrl (sueltas) y Shift (rango) y aplicarles una acción que asigna a la obra filtrada. Decisión del humano 2026-09-29: COMPLETA HASTA EL 100 %, es decir, a cada trabajador le pone en la obra filtrada lo que le falte para llegar al 100 %, sin tocar sus otras obras. Depende del filtro por obra (F-021). El cálculo de lo que falta vive en la API, no en app.js.

### F-030 · Dedicación por días, bajas e incidencias con calendario del trabajador

estado **pendiente** · prioridad 6 · rigor `critico` · SDD sí · rama `feature/F-030-dias-bajas-incidencias`

Salida de la revisión de negocio del 2026-09-29. Dos peticiones que se resuelven con el mismo mecanismo: (1) en vez de teclear el %, indicar un rango de fechas y que el % salga de los días laborables; (2) poder indicar bajas y otras incidencias como en partes (V/B/AT/FJ/F/H/M, ver azure-apps/partes.md), con el % calculado por días. Decisiones del humano 2026-09-29: el calendario es el mismo que usa nominas-extras, cada trabajador con el suyo (allí: convenio por CCC, festivos por convenio y año, fines de semana no laborables; application/services/convenio_calendar.py). UX: una tecla especial (por ejemplo +) sobre la obra del recurso despliega una subfila debajo para fechas y tipo; NO debe interferir ni ralentizar la secuencia actual % Enter obra Enter, que funciona bien. A DECIDIR EN LA SPEC: de dónde sale el convenio de cada trabajador aquí; dónde viven los festivos sin copiar lógica ni datos entre proyectos (regla de límite de servicio); si las incidencias se escriben en Sigrid como en partes o solo descuentan días del 100 %; cómo afecta a P1-P5 del transfer.

### F-011 · Un solo codigo de hora mes por trabajador

estado **pendiente** · prioridad 7 · rigor `estandar` · SDD no · rama `feature/F-011-codigo-hora-mes-unico`

Detectado el 2026-08-19 al revisar el original porcentajes-transfer. Cuando un recurso tiene varios codigos de hora mensual (MENC, MJEFO...), reglas_porcentajes.py:105 elige el PRIMERO POR ORDEN ALFABETICO y de ahi sale el importe mensual (pre) que se escribe en Sigrid. Es una heuristica que nadie ha confirmado y que puede escribir un importe distinto del correcto. Decision del humano: de momento se deja el primero, y se abre esta feature para que la situacion no se de. Dos partes: que el sistema avise en el preflight cuando un recurso tenga mas de un codigo M* vigente (hoy solo lo escribe en el log, donde nadie lo ve), y llevar a Administracion la peticion de que en Sigrid un trabajador solo pueda tener un codigo de hora mes.

### F-012 · El test de la epsilon compartida ata el transfer al monorepo

estado **pendiente** · prioridad 8 · rigor `estandar` · SDD no · rama `feature/F-012-epsilon-compartida-entre-servicios`

Detectado por la review de la Fase 2 de F-002 (observacion 9.4). El test test_f002_r26_la_tolerancia_es_la_del_cuadrante navega con Path(__file__).resolve().parents[3] hasta services/dedicacion-api/domain/estados.py para comprobar que la tolerancia del transfer (0.00005) sigue siendo el equivalente exacto del _EPSILON del cuadrante (0.005 en escala 0-100). La decision es la correcta y NO viola el limite de servicio: no importa codigo ni duplica logica, y sin ese test las dos epsilon se separarian sin que nadie se entere. Pero ata la suite del transfer a la disposicion del monorepo: si algun dia el servicio se extrae a su propio repositorio, el test se cae con un error de ruta en vez de con el mensaje de negocio que lleva escrito. Hay que decidir como se vigila esa invariante entre servicios sin depender de rutas relativas.

### F-016 · Una function key de solo lectura para dedicacion-api

estado **pendiente** · prioridad 9 · rigor `estandar` · SDD no · rama `feature/F-016-sigrid-key-solo-lectura`

Decision D5 de F-008, que se estaba cayendo por la rendija: viajaba dentro de T30, T30 se movio a F-015 y F-015 solo se llevo la mitad del Portal. La review de cierre de F-008 la busco en las trece entradas del backlog y no aparecia en ninguna. El problema: la api y el transfer comparten HOY la misma function key de sigrid-api, y lo unico que impide que la api escriba en el ERP es que su codigo no tiene rutas de escritura, NO la credencial. Es decir, la separacion es por disciplina, no por permisos: cualquiera que anada por error una llamada de escritura a la api tendria credencial para ejecutarla. Hay que preguntar al dueno de sigrid-api si puede emitir una clave de SOLO LECTURA y, si puede, desplegarla en la api. Si no puede, hay que dejar escrito que la separacion depende del codigo y que eso es un riesgo aceptado a conciencia.

### F-021 · Filtro por obra: solo su chip y los recursos asignados en Sesame

estado **pendiente** · prioridad 10 · rigor `estandar` · SDD sí · rama `feature/F-021-filtro-obra-chip-unico`

Pedida por el humano el 2026-09-03. En la tabla del cuadrante, la columna asignaciones pinta un chip por cada obra del trabajador (dedicacion-front/static/js/app.js, construirCelda ~530-545). El filtro 'Filtrar obra...' de esa columna (trabajadoresVisibles ~439) decide que FILAS se ven, pero cada fila sigue pintando TODOS sus chips: filtras por una obra y ves al trabajador con las otras cuatro al lado. Se pide que, con el filtro activo, cada fila muestre solo el chip que coincide. A DECIDIR EN LA SPEC: la columna total y el estado (OK/FALTA/EXCESO) seguirian refiriendose al 100 % de TODAS las obras, asi que la fila se contradice a simple vista; hay que decidir si se recalcula sobre lo filtrado -y entonces el estado deja de significar lo que significa- o si se avisa de que hay chips ocultos. Es presentacion pura: no toca dedicacion-api ni el transfer y no cambia nada de lo que se registra en Sigrid. AMPLIADA 2026-09-29 (revisión de negocio): el filtro por obra debe además SELECCIONAR los recursos asignados a esa obra en Sesame (el humano confirma que Sesame guarda la obra de cada persona). Eso deja de ser presentación pura: cruza la frontera del proyecto (sesame-api, ver azure-apps/partes.md 5.3 bis) y la consulta la hace la API, no el front. Pendiente en la spec: si sesame-api expone la obra asignada y si está desplegado; cómo se casa la persona (DNI) y la obra de Sesame con las de Sigrid. La selección que produce es la que usa F-029.

### F-031 · MCP para que una IA haga el trabajo del usuario

estado **pendiente** · prioridad 11 · rigor `critico` · SDD sí · rama `feature/F-031-mcp-ia`

Salida de la revisión de negocio del 2026-09-29. Servidor MCP para que una IA responda sobre la información de la BBDD de la app y, sobre todo, pueda ESCRIBIR: hacer el trabajo del usuario en el cuadrante. Límites propuestos por el líder para la spec: escribe SIEMPRE a través de dedicacion-api con la identidad del usuario, nunca directo a PostgreSQL, para que valgan las mismas reglas (100 %, periodo abierto, deshacer propio de F-027); NO puede lanzar el registro en Sigrid, ese paso sigue siendo humano desde el front. A decidir: dónde vive (dentro de la API o servicio aparte), autenticación, y si toma como referencia mcp-bbdd (azure-apps/mcp_bbdd.md). Cambia lo que el proyecto expone: azure-apps/dedicacion.md se actualiza en el mismo trabajo.

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

### F-008 · Infraestructura y despliegue en Azure

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-008-infra-azure`

Hoy no hay nada desplegado ni carpeta infra/. Provisionar los recursos siguiendo el patrón de partes (Container Apps, imágenes en acralbaranesdev con tag fechado, secretos en Key Vault por identidad gestionada, Easy Auth en el front), decidir dónde vive la BBDD dedicacion, y escribir el documento del proyecto en azure-apps. El transfer arranca en modo pruebas y solo sale de él con decisión expresa.

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
