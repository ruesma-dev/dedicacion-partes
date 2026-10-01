<!-- specs/F-026-recursos-sin-ficha-empleado/requirements.md -->
# F-026 · El trabajador es el recurso: recursos sin ficha de empleado (caso Eusebio Vindel Duro)

Rigor **`critico`**: cambia qué recurso se escribe en Sigrid y el transfer
desplegado escribe **de verdad** desde el 2026-10-01 (`docs/INTEGRACION.md` §8).
Ninguna verificación de esta feature lanza `registro/ejecutar`.

Servicios: **`dedicacion-api`** (sync de trabajadores, identidad del
trabajador, líneas que manda al transfer) y **`dedicacion-transfer`** (deja de
elegir el recurso; contrato de la línea). **`dedicacion-front` no se toca.**
Diagnóstico: `progress/explore_eusebio.md` y `progress/explore_maestros_sync.md`.

**Base: decisión del humano del 2026-10-01**, literal: «no debe buscar por
empleado sino por recurso» y «aquí SOLO deben aparecer empleados que no estén
inactivos y que tengan código hora mes». **Depende de F-034** (obras siempre de
la empresa 1; la línea viaja con la empresa de la obra): ver design §1.

Glosario. **Recurso válido**: fila de `res` de clase persona (`res.cla = 1`),
sin fecha de baja de su concepto (`con.fecbaj`, D1 de F-023) y con código de
hora mensual `M*` en `reshor`. **Fila legada**: fila de `trabajador` creada
antes de F-026, cuya clave `ide` es un `emp.ide` y su `recurso_ide` es NULL.

Medido en el data mart (build `personal` 2026-10-01): **195** recursos válidos
(182 en la 1, 8 en la 18, 1 en la 25, 4 en la 31) frente a los **179**
trabajadores activos de hoy; detalle y vehículos `MESVE` en design §2.

## 1. Sync de trabajadores: parte del recurso

- **R1.** La consulta `sync.empleados.sql` debe partir de `dbo.res` unido a su
  `con`, filtrar `res.cla = 1`, devolver una fila por recurso de **todas** las
  empresas y unir `dbo.emp` solo con `LEFT JOIN` por `res.conide`. Alias:
  `recurso_ide`, `empleado_ide` (`res.conide`, NULL si 0), `cod` y `nombre`
  (del concepto del recurso), `dni` (de `emp`, NULL sin ficha), `cif`
  (`res.cif`), `empresa` (`con.emp` del recurso), `categoria`,
  `estado_recurso`, `baja_recurso`, `baja_laboral`, `cod_hora_mes`,
  `importe_mes`. Sin `WHERE` de actividad (el filtro va en el servicio).
- **R2.** El sync y el preview deben incluir solo recursos válidos, con el
  mismo criterio de baja y de `M*` que hoy (F-023 R13, R18). Un recurso sin
  ficha de empleado (`empleado_ide` y `dni` NULL) debe incluirse igual.
- **R3.** El sistema debe producir **una fila por recurso**: dos recursos de la
  misma persona —mismo empleado, mismo documento, misma o distinta empresa—
  son dos trabajadores, cada uno con la empresa de su recurso. (D2; coherente
  con D7 de F-024.)
- **R4.** CUANDO dos recursos incluidos de la misma empresa comparten
  documento normalizado (`dni` o, sin él, `cif`), el preview debe listar sus
  códigos en `empleados.posible_misma_persona`, sin excluir a ninguno.
- **R5.** SI la consulta no devuelve `recurso_ide`, `nombre` o `empresa`,
  ENTONCES el sync y el preview deben fallar sin persistir nada.
- **R6.** El preview no debe publicar `excluidos_recurso_otra_empresa`,
  `duplicados_recurso` ni `duplicados_persona`: los filtros que dependían de
  la ficha de empleado desaparecen (design §5).

## 2. Identidad del trabajador y migración sin mover datos

- **R7.** `TrabajadorORM` debe declarar `recurso_ide` (`BigInteger`, nulable,
  sin default). La columna la añade a una base existente el `ALTER` que deriva
  `esquema.py`; nada de DDL a mano.
- **R8.** CUANDO el sync recibe un recurso cuyo `recurso_ide` ya tiene una
  fila, debe actualizar esa fila y no crear otra.
- **R9.** CUANDO el sync recibe un recurso que no está en ninguna fila, debe
  crear una con `ide` = `recurso_ide` = el `ide` del recurso.
- **R10.** CUANDO existen filas legadas, el sync, en la misma transacción y
  antes del alta y actualización, debe **adoptar** para cada una un recurso de
  las filas brutas (válidas o no) cuyo `empleado_ide` sea su `ide`: de su misma
  empresa si la fila la tiene; prefiriendo activo, luego con `M*`, luego el
  `recurso_ide` mayor; nunca uno ya asignado a otra fila ni elegido antes en la
  misma pasada. Adoptar solo rellena `recurso_ide`: no cambia `ide`.
- **R11.** SI una fila legada no tiene recurso adoptable, ENTONCES queda con
  `recurso_ide` NULL, se desactiva si estaba activa y se cuenta como
  `sin_recurso`.
- **R12.** La adopción debe ser idempotente: un segundo sync con los mismos
  datos no adopta nada ni cambia ninguna fila.
- **R13.** `POST /api/v1/sync` debe informar `empleados.adoptados` y
  `empleados.sin_recurso`; `GET /api/v1/sync/preview` debe informar el plan
  (`empleados.adopcion`: `legadas`, `adoptables`, `sin_recurso`,
  `sin_recurso_activas`) sin escribir.
- **R14.** Ni el sync ni la adopción deben tocar `asignacion` ni `evento`: ids,
  `trabajador_ide` y `synckey` (`porcentajes:{id}`) se conservan.

## 3. Registro: la API manda el recurso, el transfer no lo elige

- **R15.** CUANDO se pide preflight o ejecutar, cada línea que la API manda al
  transfer debe llevar `recurso_ide` = el del trabajador, y no `empleado_ide`.
- **R16.** SI un trabajador visible tiene `recurso_ide` NULL, ENTONCES la API
  no debe mandar sus líneas ni trazarlas, y la respuesta debe listar sus
  `registro_id` en `sin_recurso`.
- **R17.** El transfer debe usar el `recurso_ide` de la línea tal cual y no
  debe consultar `res.conide` ni elegir recurso (sin `recursos_de_empleados`).
- **R18.** SI una línea llega al transfer sin `recurso_ide`, ENTONCES debe
  omitirse con el motivo de «sin recurso», traiga o no `empleado_ide`.
- **R19.** El transfer no debe exigir que la empresa del recurso sea la de la
  línea (con F-034, un trabajador de la 18 imputa a obras de la 1).
- **R20.** P1-P5 y `#regla-empresa` no cambian: un recurso sin `M*` sigue
  omitiéndose por P1 (`test_f002_*` y `test_f022_*` en verde).

## 4. Recurso que deja de estar activo

- **R21.** CUANDO el recurso de un trabajador deja de ser válido, el sync debe
  desactivar la fila sin borrar sus asignaciones; el cuadrante la sigue
  enseñando en los periodos donde tiene líneas (comportamiento actual) y sus
  líneas se registran con su recurso. (D3)

## 5. Documentación

- **R22.** `docs/ARCHITECTURE.md` debe tener una regla nueva `#regla-recurso`
  (fuente única, en `ANCLAS` de `test_f002_fuente_unica.py`) y retirar los
  avisos «recurso elegido sin mirar la empresa (F-026)»; `docs/INTEGRACION.md`,
  el README del transfer y los comentarios de `config.yaml` deben decir el
  contrato nuevo. La copia a `azure-apps/dedicacion.md` la hace el líder.

## 6. Verificación con datos reales (MANUAL del humano)

- **R23.** Sync real con la API de la rama contra la BBDD local: Eusebio
  (`1-MO/0772`) y los otros nueve activos; ningún recurso con fecha de baja;
  `sin_recurso` = 0 entre las filas legadas activas; mismo número e ids de
  asignaciones antes y después.
- **R24.** Preflight real de **solo lectura** con transfer local en modo
  pruebas: una línea de Eusebio sale `escribir` con su `recurso_ide`; ninguna
  línea omitida por «sin recurso». Nadie lanza `registro/ejecutar`.

Fuera de alcance y riesgos: [`design.md` §9-§10](design.md#9-fuera-de-alcance).

## 7. Decisiones abiertas (las valida el humano antes de implementar)

- **D1 · Migración.** **Propuesta: adoptar** (R7-R14): columna nueva
  `recurso_ide`, la clave `ide` queda como identificador opaco (`emp.ide` en
  las legadas, `res.ide` en las nuevas; en Sigrid los `ide` de `con` no se
  repiten entre tipos, así que no chocan). No se mueve ni una asignación: es
  «añadir una columna nulable», lo único que `esquema.py` sabe hacer sin
  Alembic (criterio de F-003 §6). **Alternativas:** (a) reclavar `ide` al
  recurso moviendo `asignacion` y `evento` (mover datos: exige migración
  escrita y es cuando entra Alembic); (b) Alembic ya. Las dos, más riesgo en
  producción para el mismo resultado visible.
- **D2 · Misma persona.** **Propuesta:** no fusionar nunca (R3), avisar (R4).
  **Alternativa:** fundir por documento en la empresa (esconde un recurso).
- **D3 · Recurso de baja con líneas.** **Propuesta:** se registra con su
  recurso. **Alternativa:** omitir si la baja es anterior al mes (F aparte).
- **D4 · Contrato.** **Propuesta:** `empleado_ide` sale del contrato
  API ↔ transfer (si llega, se ignora y la línea se omite por R18). Ningún
  orden de despliegue escribe en un recurso equivocado (design §8).
- **D5 · Criterio 4 de `features.json`** («el recurso es el de la empresa de la
  línea»). Con F-034 la línea lleva la empresa de la obra (1); se propone
  leerlo como «el recurso es el del trabajador, el que manda la API, nunca uno
  elegido por el transfer» (R15-R19).
- **D6 · Nombre y código.** **Propuesta:** `cod` y `nombre` del recurso;
  `dni` solo de la ficha. Alternativa: el nombre de la ficha si existe.
- **D7 · Despliegue.** **Propuesta:** F-026 se implementa sobre `dev` con
  F-034 ya mergeada y se despliega con ella o justo detrás; en producción, el
  humano hace copia de la base, mira el preview (`adopcion`) y lanza el sync
  **antes** de que nadie registre (design §8).
