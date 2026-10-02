<!-- specs/F-026-recursos-sin-ficha-empleado/requirements.md -->
# F-026 · El trabajador es el recurso: recursos sin ficha de empleado (caso Eusebio Vindel Duro)

Rigor **`critico`**: cambia qué recurso se escribe en Sigrid y el transfer
desplegado escribe **de verdad** desde el 2026-10-01 (`docs/INTEGRACION.md` §8).
Ninguna verificación de esta feature lanza `registro/ejecutar`.

Servicios: **`dedicacion-api`** (sync de trabajadores, identidad, vigencia por
mes, líneas que manda al transfer), **`dedicacion-transfer`** (deja de elegir
el recurso) e **`infra/`** (script de vaciado de los datos de prueba, D1).
**`dedicacion-front` no se toca.** Diagnóstico: `progress/explore_eusebio.md`
y `progress/explore_maestros_sync.md`.

**Base: decisión del humano del 2026-10-01**, literal: «no debe buscar por
empleado sino por recurso» y «aquí SOLO deben aparecer empleados que no estén
inactivos y que tengan código hora mes»; **D1 y D3 reescritas por él el
2026-10-02** (§7). **Depende de F-034** (obras siempre de la empresa 1).

Glosario. **Recurso persona M\***: fila de `res` de clase persona
(`res.cla = 1`) con código de hora mensual `M*` en `reshor`. **Fecha de baja**:
`con.fecbaj` del recurso, entero `AAAAMMDD` (0 = sin baja,
`azure-apps/sigrid_api.md`). **Vigente en el mes M**: sin fecha de baja o con
fecha de baja igual o posterior al primer día de M (D3). **Ventana de bajas**:
primer día del más antiguo entre el mes anterior al del sync y cada periodo
`ABIERTO` (design §5.2).

Medido en el data mart (build `personal` 2026-10-01): **195** recursos persona
M\* sin baja (182 en la 1, 8 en la 18, 1 en la 25, 4 en la 31) frente a los
**179** trabajadores activos de hoy; detalle en design §2.

## 1. Sync de trabajadores: parte del recurso

- **R1.** La consulta `sync.empleados.sql` debe partir de `dbo.res` unido a su
  `con`, filtrar `res.cla = 1`, devolver una fila por recurso de **todas** las
  empresas y unir `dbo.emp` solo con `LEFT JOIN` por `res.conide`. Alias: `ide`
  (`res.ide`), `cod` y `nombre` (del concepto del recurso), `dni` (de `emp`,
  NULL sin ficha), `cif` (`res.cif`), `empresa` (`con.emp` del recurso),
  `categoria`, `estado_recurso`, `fecha_baja` (`NULLIF(con.fecbaj, 0)`),
  `baja_laboral`, `cod_hora_mes`, `importe_mes`. Sin `WHERE` de actividad.
- **R2.** El sync y el preview deben incluir los recursos persona M\* vigentes
  en algún mes desde la ventana de bajas (R12-R13). Un recurso sin ficha de
  empleado (`dni` NULL) debe incluirse igual.
- **R3.** El sistema debe producir **una fila por recurso**: dos recursos de la
  misma persona —mismo empleado, mismo documento, misma o distinta empresa—
  son dos trabajadores, cada uno con la empresa de su recurso. (D2)
- **R4.** CUANDO dos recursos incluidos de la misma empresa comparten
  documento normalizado (`dni` o, sin él, `cif`), el preview debe listar sus
  códigos en `empleados.posible_misma_persona`, sin excluir a ninguno.
- **R5.** SI la consulta no devuelve `ide`, `nombre` o `empresa`, ENTONCES el
  sync y el preview deben fallar sin persistir nada.
- **R6.** El preview no debe publicar `excluidos_recurso_otra_empresa`,
  `duplicados_recurso` ni `duplicados_persona` (design §5.1).

## 2. Identidad del trabajador: el recurso, sin migración (D1)

- **R7.** La clave del trabajador debe ser el `ide` del recurso
  (`trabajador.ide` = `res.ide`); el sistema no debe persistir `emp.ide` ni
  tener columna puente. El sync da de alta y actualiza por esa clave.
- **R8.** `TrabajadorORM` debe declarar `fecha_baja` (`Integer`, nulable, sin
  default). Es el único cambio de esquema: la columna la añade a una base
  existente el `ALTER` que deriva `esquema.py`; nada de DDL a mano.
- **R9.** CUANDO la tabla tiene filas cuyo `ide` no llega en el sync (por
  ejemplo, claves `emp.ide` anteriores a F-026), el sync debe desactivarlas
  como a cualquier recurso que deja de llegar, sin lógica de adopción ni de
  convivencia y sin tocar `asignacion` ni `evento`.
- **R10.** `infra/vaciar_datos_prueba_dedicacion.ps1` sin `-Confirmar` debe
  solo imprimir el plan, sin conectar; con `-Confirmar` debe ejecutar una única
  sentencia `TRUNCATE TABLE asignacion, evento, periodo, trabajador CONTINUE
  IDENTITY` en la base `dedicacion` y nada más: ni `obra` ni `empresa`, ni
  `DROP`, `CASCADE`, `RESTART IDENTITY`, ni nada a nivel de servidor.
- **R11.** El vaciado debe conservar las secuencias (`CONTINUE IDENTITY`): un
  `asignacion.id` nuevo nunca reutiliza una `synckey` `porcentajes:{id}` ya
  escrita en Sigrid (obra de pruebas).

## 3. Baja en el mes: vigencia por periodo (D3)

- **R12.** El sync y el preview deben calcular la ventana de bajas con una
  función pura que recibe los periodos `ABIERTO` y la fecha del día.
- **R13.** CUANDO un recurso persona M\* trae fecha de baja anterior a la
  ventana, el sync debe excluirlo y contarlo en
  `excluidos_por_estado_recurso["(baja anterior a la ventana)"]`; con baja en
  la ventana o sin baja, debe incluirlo y guardar su `fecha_baja` (NULL sin
  baja, también si Sigrid se la quita).
- **R14.** Un trabajador debe ser vigente en el mes M si y solo si `activo` y
  (`fecha_baja` NULL o ≥ `AAAAMM01` de M); una sola función de dominio.
- **R15.** CUANDO se piden el cuadrante, el resumen, la copia del mes o el
  export del mes M, el `activo` de cada trabajador debe valer «vigente en M»;
  uno no vigente solo aparece si tiene líneas en M (como hoy un inactivo).
- **R16.** CUANDO se pide preflight o ejecutar del mes M, la API no debe
  mandar ni trazar las líneas de un trabajador no vigente en M, y la respuesta
  debe listar sus `registro_id` en `no_vigentes`.
- **R17.** El preview debe publicar `empleados.ventana_baja` (`AAAAMMDD`) y
  `empleados.incluidos_con_baja` (incluidos con fecha de baja).

## 4. Registro: la API manda el recurso, el transfer no lo elige

- **R18.** CUANDO se pide preflight o ejecutar, cada línea que la API manda al
  transfer debe llevar `recurso_ide` = `trabajador.ide`, y no `empleado_ide`.
- **R19.** El transfer debe usar el `recurso_ide` de la línea tal cual y no
  debe consultar `res.conide` ni elegir recurso (sin `recursos_de_empleados`).
- **R20.** SI una línea llega al transfer sin `recurso_ide`, ENTONCES debe
  omitirse con el motivo de «sin recurso», traiga o no `empleado_ide`.
- **R21.** El transfer no debe exigir que la empresa del recurso sea la de la
  línea (con F-034, un trabajador de la 18 imputa a obras de la 1).
- **R22.** P1-P5 y `#regla-empresa` no cambian: un recurso sin `M*` sigue
  omitiéndose por P1 (`test_f002_*` y `test_f022_*` en verde).

## 5. Documentación

- **R23.** `docs/ARCHITECTURE.md` debe tener la regla nueva `#regla-recurso`
  (con la vigencia por mes; en `ANCLAS` de `test_f002_fuente_unica.py`) y
  retirar los avisos «recurso elegido sin mirar la empresa (F-026)»;
  `docs/INTEGRACION.md`, el README del transfer, `infra/README_dedicacion.md`
  (el vaciado) y los comentarios de `config.yaml` deben decir lo nuevo. La
  copia a `azure-apps/dedicacion.md` la hace el líder.

## 6. Verificación con datos reales (MANUAL del humano)

- **R24.** En local: vaciado con `-Local -Confirmar` y sync real con la API de
  la rama. Eusebio (`1-MO/0772`) y los otros nueve, vigentes; `trabajador.ide`
  = su `res.ide`; ninguna baja anterior a la ventana; un recurso con baja en el
  mes en curso, vigente en el cuadrante de ese mes y no en el siguiente.
- **R25.** Preflight real de **solo lectura** con transfer local en modo
  pruebas: una línea de Eusebio sale `escribir` con su `recurso_ide`; ninguna
  omitida por «sin recurso». Nadie lanza `registro/ejecutar`.

Fuera de alcance y riesgos: [`design.md` §9-§10](design.md#9-fuera-de-alcance).

## 7. Decisiones (validadas por el humano el 2026-10-02)

- **D1 · Sin migración.** Literal: «lo que hay ahora mismo en la app son
  pruebas, no hace falta migrarlo». `trabajador.ide` = `res.ide` (R7, design
  §10); los datos de `dedicacion` se vacían al desplegar (R10-R11), sin
  columnas puente ni convivencia. El cambio de clave no cambia el tipo de la
  columna: no hay que recrear tablas.
- **D2 · Misma persona.** No fusionar nunca (R3), avisar (R4).
- **D3 · Baja en el mes.** Literal: «si el recurso se ha dado de baja en el
  mes, debe salir todavía accesible». Vigencia por periodo (R12-R16): visible
  en M si no tiene baja o la tiene en M o después; el sync trae las bajas desde
  la ventana y el cuadrante y el registro filtran por mes.
- **D4 · Contrato.** `empleado_ide` sale del contrato API ↔ transfer (si
  llega, se ignora y la línea se omite por R20).
- **D5 · Criterio 4 de `features.json`** («el recurso es el de la empresa de
  la línea»): se lee como «el recurso es el del trabajador, el que manda la
  API, nunca uno elegido por el transfer» (R18-R21).
- **D6 · Nombre y código.** `cod` y `nombre` del recurso; `dni` de la ficha.
- **D7 · Despliegue.** Con F-034; el vaciado de D1 se hace en ese despliegue,
  antes del primer sync, con autorización expresa del humano (design §8).
