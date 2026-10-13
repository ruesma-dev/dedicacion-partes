<!-- specs/F-055-preflight-rapido/requirements.md -->
# F-055 · El registro sin búsquedas de partidas (medir y acelerar)

Rigor **`critico`**. Toca **transfer, api y front** (design §1). Rediseñada
por el humano el 2026-10-11 («solo debería comprobar si los partes están o
no, pero no las partidas»); va **tras fusionar F-050** (con T15c). **D1-D8:
DECIDIDAS por el humano el 2026-10-13** (A; **D2 = A + C**; design §11): «la
partida debe venir preseleccionada, la del último parte del trabajador en esa
obra, o si no hay, eligiendo una en CI como hacemos en partes».

Glosario: **elegida** = la del usuario (F-050); **propuesta guardada** = la
que calcula el transfer y guarda la api; **automática** = obra normal sin
elegida; **pendiente** = automática sin propuesta guardada; **lote** = varias
obras en una petición al transfer; **lectura** = una llamada a `sigrid-api`.
Fuera: reglas de registro y pasos de la propuesta (los de F-050; el 2 se
queda), `ejecutar` en lote, F-048, F-051, F-044.

## 1. Medición

- **R1.** Cada lectura del transfer debe dejar un log con su nombre (el del
  método del cliente), filas y segundos; cada preflight, uno con su obra,
  lecturas, segundos leyendo y totales. Sin SQL ni parámetros.
- **R2.** `prueba_escritura_porcentajes.py medir` (`--ano`, `--mes`, `--obra`
  y `--recurso` repetibles, `--partida OBRA:PARIDE`, `--lote`) enseña segundos
  por lectura, obra y total, sin llamar a `escribir` ni a `ejecutar`.

## 2. El registro no busca partidas (transfer)

- **R3.** `[D3]` CUANDO una línea de obra normal llega con partida (elegida o
  propuesta guardada), el preflight NO debe leer para ella presupuesto ni
  historial: la valida con `validar_partidas`, **una** lectura por petición,
  por `ide` (obra, si tiene hijas, baja). **R4.** Vale, como hoy, solo la
  hoja activa del presupuesto de la obra de origen (`construir_catalogo`).
- **R5.** SI la **elegida** no vale, ENTONCES se omite con
  `MOTIVO_PARTIDA_NO_HOJA` (R20 de F-050). **R6.** `[D3]` SI la **propuesta
  guardada** no vale, ENTONCES la línea se trata como pendiente (R7).
- **R7.** `[D1]` Una pendiente sigue el camino de hoy: presupuesto de su obra,
  una lectura de historial por petición o lote, y `proponer_partida`.
- **R8.** Una línea con propuesta guardada válida se escribe con ella y su
  acción publica el `partida_metodo` y `partida_origen` guardados. **R9.**
  Toda acción con partida publica también `partida_res`.
- **R10.** `partidas_obra` solo lleva catálogo si el preflight leyó el
  presupuesto (R7); si no, `[]` sin lectura (sale la lectura forzada de F-049
  ampliación d; el front no lo lee desde F-050 R29).
- **R11.** Postventa y VAR, con sus reglas y lecturas (una vez por lote).
  **R12.** Partes, estado, pisados, sobrecarga, idempotencia, sin partida,
  cuenta analítica y modo pruebas: mismas reglas, con lo leído en la petición.

## 3. La propuesta guardada (api)

- **R13.** `[D2]` `asignacion` gana, nulables y en el ORM, `propuesta_ide`
  (BigInteger) y `propuesta_cod`, `_res`, `_metodo`, `_origen` (Text).
- **R14.** `[D2]` CUANDO un preflight devuelve para una automática una partida
  con método de propuesta (`parte_anterior`, `ultimo_parte`, `auto_*`), la
  api la guarda **si sigue sin elegida**, sin evento, sin tocar `sigrid_*` ni
  la respuesta al front. **R15.** `[D2]` Igual al abrir el selector (R17 de
  F-050) si el transfer devuelve propuesta.
- **R16.** Al registrar, la automática con propuesta guardada viaja con
  `propuesta_paride`, `_cod`, `_res`, `_metodo` y `_origen`; la elegida, como
  hoy (`paride`, manda); VAR, como hoy.
- **R17.** Guardar la fila conserva la propuesta de cada línea cuya clave ya
  existía; la nueva entra sin ella. Copiar el mes, Completar y F7 no la
  copian; deshacer no la restaura; cambiar la elegida no la borra.
- **R18.** `[D8]` La propuesta guardada no caduca: solo se reescribe al abrir
  el selector (R15) y cuando el preflight la recalcula (R6); el cálculo del
  mes (R29) **nunca** pisa una ya guardada.

## 4. Lotes, agrupación y paralelo (transfer)

- **R19.** `[D6]` `POST /api/registro/preflight-lote` (`{peticiones:
  [PeticionIn]}` → `{ok, obras}`): una entrada por petición, en su orden, con
  la forma del preflight de hoy o `{ok: false, error}`.
- **R20.** `[D5]` En ese lote, obras por `ide`, horas, `synckey`, validación y
  cuentas de partida, historial, partes del periodo y sus líneas se leen
  **agrupados** (una lectura por tipo, trozos de ≤ 500 parámetros); obra de
  pruebas, postventa y VAR con su presupuesto, presupuesto de cada obra y
  siguiente código PT, **una vez** por lote.
- **R21.** El resultado de cada obra en un lote (R19 o R34) debe ser
  **idéntico** al de su petición suelta con los mismos datos de Sigrid.
- **R22.** `[D4]` Lo leído vale solo para esa petición; lo no precargado va a
  `sigrid-api`: nunca vacío ni datos de otra petición.
- **R23.** `[D5]` Lecturas independientes y decisiones por obra corren en
  paralelo hasta `SIGRID_LECTURAS_PARALELAS` (defecto 4; 1 = en serie). SI
  vale < 1 o > 8, ENTONCES el transfer no arranca.
- **R24.** SI una lectura agrupada o compartida falla o viene `truncated`,
  ENTONCES fallan las obras que dependen de ella (502 si son todas); un fallo
  propio de una obra (no encontrada, otra empresa) solo marca esa obra.
- **R25.** R19 y R34 son rutas síncronas (threadpool). **R26.** `[D6]` La api
  pide el preflight con **una** llamada a R19 y devuelve la forma de hoy;
  `ejecutar` sigue por obra y en serie.

## 5. Front y documentación

- **R27.** `[D7]` La celda Partida de una automática con propuesta la enseña
  en cursiva (código · descripción y método); sin ella, «automática».
  `LineaOut` publica `propuesta_cod`, `_res` y `_metodo`.
- **R28.** `ARCHITECTURE.md#regla-partida`: propuesta guardada, cuándo se
  calcula, validación por `ide`; «Acceso a datos»: lotes; `INTEGRACION.md`:
  R19, R34, R35, variable y columnas; el líder, `azure-apps/dedicacion.md`.

## 6. Propuestas del mes en lote (D2 C)

- **R29.** `[D2]` CUANDO se pide el cuadrante de un periodo **ABIERTO**, o
  termina con éxito un `POST /sync` (para cada periodo abierto), la api lanza
  el cálculo de las **pendientes** del periodo (todas las empresas): obra
  normal, sin `partida_fija`, sin elegida, sin propuesta guardada y fuera de
  la memoria de R32. Ni en periodo cerrado ni al guardar una fila.
- **R30.** Corre **en segundo plano** (un hilo en la api, en cola): el
  cuadrante responde sin esperarlo, con `propuestas_en_curso` (verdadero si
  el periodo está en cola o en marcha). Un periodo así no se relanza.
- **R31.** La api agrupa las pendientes por obra y llama **una** vez a R34
  por trozo de ≤ 10 obras; tras cada uno guarda y confirma cada propuesta
  **solo si** la línea sigue sin elegida ni propuesta (sin evento).
- **R32.** Una línea sin propuesta posible, o cuya obra vuelve `{ok: false}`,
  entra en una memoria del proceso y no se repite hasta el próximo sync con
  éxito (que la vacía) o un reinicio.
- **R33.** SI el transfer no responde, falla o pasa su timeout, ENTONCES el
  cálculo se para con un log, sin guardar el trozo ni tocar R32 (el próximo
  `GET` lo relanza).
- **R34.** `[D6]` `POST /api/partidas/propuesta-lote` (`{peticiones:
  [PropuestaIn]}`, mismo `ano`/`mes` o 422) → `{ok, obras}`: por petición y en
  su orden, `{ok: true, propuestas}` (las de `POST /api/partidas/propuesta`,
  R21) o `{ok: false, error}`. Obras e historial, **una** lectura por lote;
  presupuestos, uno por obra en paralelo (R23); fallo compartido, 502 (R24).
- **R35.** `GET …/propuestas` (solo lee) devuelve `{en_curso, lineas}`: las
  automáticas con propuesta guardada (trabajador, obra, `_cod/_res/_metodo`).
- **R36.** MIENTRAS `propuestas_en_curso`, el front pone «buscando partida…»
  en las pendientes y consulta R35 cada 5 s; pinta solo celdas Partida de
  líneas aún sin elegida, sin tocar la fila en edición, y para con `en_curso`
  falso o al cambiar de mes o empresa. No decide nada.

## 7. Criterio de éxito, lista cerrada y MANUAL (antes = T2, después = T18)

- **C1** (test): R19 con 1, 2 y 10 obras con partida: mismas lecturas salvo
  `cuentas_de_centro` (una por centro); ninguna de presupuesto ni historial.
  **C2** (test): una obra con elegidas, hoy 8-9 lecturas en serie (T1 lo
  fija); después ≤ 6 en ≤ 4 rondas.
- **C3** (MANUAL local, modo pruebas): GONZALEZ PANIAGUA (0694 + 0696),
  09/2026, con partida: de «⇪ Sigrid» al modal **≤ 30 s y ≤ 40 % del antes**.
  **C4**: el mes entero **≤ 60 s y sin 502**. **C5**: repreflight al cambiar
  una partida **≤ 20 s**. **C6** (producción, solo preflight y Cancelar): C3
  y C4 antes y después de desplegar.
- **C7** (test): R34 con 10 obras: 1 lectura de obras, 1 de historial y 10
  de presupuesto, en ≤ 4 rondas con límite 4. **C8** (MANUAL local): 09/2026
  sin propuestas: el cuadrante sale como hoy y la Partida se llena **≤ 3 min**.
- SI C3-C5 o C8 no se cumplen, ENTONCES **PARA** y se repropone con lo medido.

- Tests anteriores que cambian: **lista CERRADA** en la cabecera de
  `tasks.md`; cualquier otro, **PARA** y se pregunta al humano. MANUAL: T2,
  T18-T19; ningún agente escribe en Sigrid.
