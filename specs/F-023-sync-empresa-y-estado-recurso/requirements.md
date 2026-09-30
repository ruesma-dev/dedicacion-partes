<!-- specs/F-023-sync-empresa-y-estado-recurso/requirements.md -->
# F-023 · Requisitos — Sync de maestros: todas las empresas y activo según el estado del recurso

> **Rigor `critico`.** Cambia quién y qué obra entra en el cuadrante y añade
> columnas a una BBDD con datos. **Servicio afectado: solo `dedicacion-api`**
> (sync y preview); front y transfer no se tocan (design §5).

## Contexto

Diagnóstico: `progress/explore_maestros_sync.md` §B. La SQL de sync no lee la
empresa (`con.emp` «Empresa», `azure-apps/sigrid_tablas.md` l. 5646), el
dedupe por DNI puede elegir la ficha de otra empresa, y «activo» sale del
último `emphis` sin `fecbaj`, ignorando el estado del **recurso**.

Decisiones del humano (2026-09-29), no se reabren: se sincronizan **todas**
las empresas guardando la de cada ficha (el filtro en pantalla es **F-024**);
«inactivo» es un **estado del recurso**; una obra con el mismo código en dos
empresas son **dos obras**; el dedupe por persona **no mezcla empresas**.

### Dónde vive el estado del recurso (con cita)

`res` es «Propiedades de con» (`sigrid_tablas.md` l. 19905): **no tiene campo
de estado propio**; su estado es el de su fila de `con` (misma `ide`), con dos
candidatos: `con.est` «Estado», Entero (l. 5657), cuyo literal sale de
`conest` por `tip` + `est` → `res` (l. 6083-6089, el mismo mecanismo que ya
usa la SQL de obras), y `con.fecbaj` «Fecha baja» (l. 5658).

**El diccionario no dice qué valores de `con.est` significan inactivo** para
un recurso, ni si Administración usa `est`, `fecbaj` o ambos. El criterio va
por **configuración** (literales de estado excluidos + interruptor de fecha de
baja) y sus valores quedan en **D1**, cerrada el 2026-10-01 (design §4).

## Requisitos

### Esquema

- **R1.** El sistema debe declarar en `TrabajadorORM` y en `ObraORM` una
  columna `empresa` de tipo `Integer`, **nulable y sin default**, y en ningún
  otro sitio; el `ADD COLUMN` que pone al día una base existente debe salir de
  `infrastructure/db/esquema.py::alters_faltantes`, no de DDL escrito a mano.
- **R2.** CUANDO se derivan los `ALTER` sobre una base con `trabajador` y
  `obra` sin `empresa`, el sistema debe emitir exactamente
  `ALTER TABLE trabajador ADD COLUMN IF NOT EXISTS empresa INTEGER` y
  `ALTER TABLE obra ADD COLUMN IF NOT EXISTS empresa INTEGER`, y nada más.

### Consultas contra Sigrid (`config.yaml`)

- **R3.** La consulta `sync.obras.sql` debe devolver el alias `empresa` con el
  `con.emp` de la ficha de la obra.
- **R4.** La consulta `sync.empleados.sql` debe devolver los alias `empresa`
  (`con.emp` de la ficha de empleado), `empresa_recurso` (`con.emp` del
  recurso), `estado_recurso` (literal de `conest` del recurso o, sin literal,
  el `con.est` en texto), `baja_recurso` (`con.fecbaj` del recurso) y
  `baja_laboral` (`fecbaj` del último `emphis`).
- **R5.** La consulta `sync.empleados.sql` no debe filtrar por `emphis` (sin
  la cláusula `WHERE COALESCE(uh.fecbaj, 0) = 0`): el activo lo decide el
  estado del recurso (sujeto a **D3**).
- **R6.** SI la consulta de obras o la de empleados no devuelve la columna
  `empresa`, ENTONCES el sync y el preview deben fallar con `ValueError`
  nombrando la consulta y la columna, sin persistir nada.

### Empresa

- **R7.** CUANDO el sync recibe dos obras con el mismo `cod` y distinta
  `empresa`, el sistema debe guardar **dos** filas en `obra`, cada una con su
  `ide` y su `empresa`, sin que una pise a la otra.
- **R8.** CUANDO el sync da de alta o actualiza una obra o un trabajador, el
  sistema debe guardar su `empresa`; un cambio de `empresa` cuenta como
  `actualizado`.
- **R9.** SI una fila de empleado trae `empresa_recurso` informada y distinta
  de `empresa`, ENTONCES el sistema debe descartarla y contarla en
  `excluidos_recurso_otra_empresa` (sujeto a **D2**).
- **R10.** CUANDO dos fichas de la **misma** empresa comparten DNI
  normalizado (o, sin DNI, nombre), el sistema debe quedarse con una sola,
  con el mismo criterio de preferencia que hoy.
- **R11.** CUANDO dos fichas de **distinta** empresa comparten DNI o nombre,
  el sistema debe conservar las dos.

### Activo según el estado del recurso

- **R12.** SI el `estado_recurso` normalizado contiene alguno de los literales
  de `estados_recurso_excluidos`, ENTONCES el sistema debe descartar la fila y
  contarla en `excluidos_estado_recurso` bajo su literal original.
- **R13.** DONDE `excluir_recurso_con_fecha_baja` está activo, SI
  `baja_recurso` es mayor que 0, ENTONCES el sistema debe descartar la fila y
  contarla bajo `"(fecha de baja del recurso)"`.
- **R14.** El descarte por estado del recurso (R12, R13) y por empresa del
  recurso (R9) debe hacerse **fila a fila, antes** de los dedupes: un empleado
  con un recurso inactivo y otro activo entra con el activo.
- **R15.** CUANDO una fila supera los filtros y trae `baja_laboral` mayor que
  0, el sistema debe incluirla y contarla en `con_baja_laboral` (informativo,
  no excluye).
- **R16.** MIENTRAS `estados_recurso_excluidos` esté vacío y
  `excluir_recurso_con_fecha_baja` desactivado, el sistema no debe descartar
  ninguna fila por estado del recurso.

### Preview

- **R17.** CUANDO se llama a `GET /api/v1/sync/preview`, la respuesta debe
  incluir en `empleados`: `excluidos_por_estado_recurso` (literal → número),
  `excluidos_recurso_otra_empresa`, `con_baja_laboral` y `por_empresa`
  (empresa → número de incluidos); y en `obras`: `por_empresa`. Las claves
  que ya existen se mantienen con el mismo significado.
- **R18.** El preview y el sync deben aplicar **la misma** depuración con la
  **misma** configuración: con las mismas filas de entrada, los netos del
  preview y los que recibe el upsert coinciden.

### Verificación con datos reales (MANUAL, humano)

- **R19.** CUANDO se ejecuta el preview contra Sigrid con los valores de D1
  en `config.yaml`, los recursos inactivos que señaló negocio (lista D5) no
  deben aparecer entre los incluidos y sí en `excluidos_por_estado_recurso`.

## Fuera de alcance

- Filtro por empresa en pantalla y empresa en la línea registrada: **F-024** /
  **F-022**. La API no expone todavía `empresa` en sus respuestas.
- Obras de postventa y el filtro `estados_excluidos` de obras: **F-025**. El
  filtro de estado de obras no cambia.
- Recursos sin ficha de empleado (caso Eusebio) y cambio de eje a recurso:
  **F-026**. La SQL sigue partiendo de `dbo.emp`.
- `obra_por_codigo` del transfer sin empresa (explore §D): no se toca aquí.

## Decisiones abiertas

- **D1 · CERRADA el 2026-10-01** (humano, sin Q1): inactivo = fecha de baja
  del concepto del recurso, `excluir_recurso_con_fecha_baja: true`;
  `estados_recurso_excluidos` vacía porque el tipo 33 no tiene estados en
  `conest` (`progress/explore_estado_recurso.md`). R12 queda como gancho
  inerte. T10 (R19) solo espera la lista D5.
- **D2 · Empresa del trabajador = la de su ficha de empleado**, y se
  descartan sus recursos de otra empresa (R9). Alternativa: la del recurso.
  **Condiciona a F-026**: si allí el eje pasa a ser el recurso, la empresa
  pasará a ser la del recurso; con R9 las dos coinciden en todo lo guardado,
  así que no hará falta migrar datos.
- **D3 · Quitar el filtro de `emphis`** (R5). Si negocio quiere exigir además
  alta laboral, se repone y `con_baja_laboral` deja de tener sentido.
- **D4 · Orden de despliegue.** Sin F-024, con R11 una persona con fichas en
  dos empresas sale **dos veces** en el cuadrante y se ven trabajadores de
  UTE que hoy colapsaban con los de Ruesma. Recomendación: no desplegar F-023
  a usuarios sin F-024.
- **D5 · Lista de recursos inactivos señalados por negocio**, necesaria para
  R19. No está en el backlog ni en los informes de exploración.
- **D6 · Volumen.** Sin el filtro de `emphis`, la consulta de empleados
  devuelve más filas. Si el preview llega `truncated`, el cliente falla (no
  pierde filas); la salida es paginar, que queda **fuera** de esta feature.
