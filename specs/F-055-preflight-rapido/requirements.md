<!-- specs/F-055-preflight-rapido/requirements.md -->
# F-055 · El registro sin búsquedas de partidas (medir y acelerar)

Rigor **`critico`**; transfer, api y front (design §1). Rediseñada el
2026-10-11 («solo debería comprobar si los partes están o no, pero no las
partidas»). **D1-D8 DECIDIDAS el 2026-10-13** (A; **D2 = A + C**); **D9-D10
el 2026-10-14** («si pero en reglas hay que cambiar el orden, a c b»): R29,
R30, R33, R36-R38. Citas y alternativas en design §11.

Glosario: **elegida** = la del usuario (F-050); **propuesta guardada** = la
calcula el transfer y la guarda la api; **automática** = obra normal sin
elegida; **pendiente** = automática sin propuesta guardada; **lote** = varias
obras por petición; **lectura** = una llamada a `sigrid-api`. Fuera: reglas
de registro, `ejecutar` en lote, F-048, F-051, F-044.

## 1. Medición y registro sin búsquedas de partidas (transfer)

- **R1.** Cada lectura del transfer deja un log con su nombre (el método del
  cliente), filas y segundos; cada preflight, uno con obra, lecturas, segundos
  leyendo y totales. Sin SQL ni parámetros. **R2.** `prueba_escritura_
  porcentajes.py medir` (`--ano`, `--mes`, `--obra` y `--recurso` repetibles,
  `--partida OBRA:PARIDE`, `--lote`) enseña segundos por lectura, obra y
  total, sin llamar a `escribir` ni a `ejecutar`.
- **R3.** `[D3]` CUANDO una línea de obra normal llega con partida (elegida o
  propuesta guardada), el preflight NO lee para ella presupuesto ni historial:
  la valida con `validar_partidas`, **una** lectura por petición, por `ide`
  (obra, si tiene hijas, baja). **R4.** Vale, como hoy, solo la hoja activa
  del presupuesto de la obra de origen (`construir_catalogo`).
- **R5.** SI la **elegida** no vale, ENTONCES se omite con
  `MOTIVO_PARTIDA_NO_HOJA` (R20 de F-050). **R6.** `[D3]` SI la **propuesta
  guardada** no vale, ENTONCES la línea se trata como pendiente (R7).
- **R7.** `[D1]` Una pendiente sigue el camino de hoy: presupuesto de su obra,
  una lectura de historial por petición o lote, y `proponer_partida`. **R8.**
  Una con propuesta guardada válida se escribe con ella y publica el
  `partida_metodo` y `partida_origen` guardados. **R9.** Toda acción con
  partida publica también `partida_res`. **R10.** `partidas_obra` solo lleva
  catálogo si se leyó el presupuesto (R7); si no, `[]` sin lectura (sale la
  lectura forzada de F-049 d; el front no lo lee desde F-050 R29).
- **R11.** Postventa y VAR, con sus reglas y lecturas (una vez por lote).
  **R12.** Partes, estado, pisados, sobrecarga, idempotencia, sin partida,
  cuenta analítica y modo pruebas: mismas reglas, con lo leído.

## 2. La propuesta guardada (api)

- **R13.** `[D2]` `asignacion` gana, nulables y en el ORM, `propuesta_ide`
  (BigInteger) y `propuesta_cod`, `_res`, `_metodo`, `_origen` (Text).
- **R14.** `[D2]` CUANDO un preflight devuelve para una automática una partida
  con método de propuesta (`parte_anterior`, `ultimo_parte`, `auto_*`), la
  api la guarda **si sigue sin elegida**, sin evento, sin tocar `sigrid_*` ni
  la respuesta al front. **R15.** `[D2]` Igual al abrir el selector (R17 de
  F-050) si el transfer devuelve propuesta. **R16.** Al registrar, la
  automática con propuesta guardada viaja con `propuesta_paride`, `_cod`,
  `_res`, `_metodo` y `_origen`; la elegida (`paride`, manda) y VAR, como hoy.
- **R17.** Guardar la fila conserva la propuesta de cada línea cuya clave ya
  existía; la nueva entra sin ella. Copiar el mes, Completar y F7 no la
  copian; deshacer no la restaura; cambiar la elegida no la borra.
- **R18.** `[D8]` La propuesta guardada no caduca: solo se reescribe al abrir
  el selector (R15) y cuando el preflight la recalcula (R6); el cálculo en
  segundo plano (R29) **nunca** pisa una ya guardada.

## 3. Lotes, agrupación y paralelo (transfer)

- **R19.** `[D6]` `POST /api/registro/preflight-lote` (`{peticiones:
  [PeticionIn]}` → `{ok, obras}`): una entrada por petición, en su orden, con
  la forma del preflight de hoy o `{ok: false, error}`.
- **R20.** `[D5]` En ese lote se leen **agrupados** (una lectura por tipo,
  trozos de ≤ 500 parámetros) obras por `ide`, horas, `synckey`, validación y
  cuentas de partida, historial, partes del periodo y sus líneas; **una vez**
  por lote, obra de pruebas, postventa, VAR, presupuestos y siguiente PT.
- **R21.** El resultado de cada obra en un lote (R19 o R34) debe ser
  **idéntico** al de su petición suelta con los mismos datos de Sigrid.
  **R22.** `[D4]` Lo leído vale solo para esa petición; lo no precargado va a
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

## 4. La propuesta: orden, segundo plano y front (D2 C, D7, D9, D10)

- **R38.** `[D10]` *(2026-10-14; cambia R1 de F-050, que era a → b → c)* La
  propuesta es la del primer paso que dé una: (a) **parte anterior** del
  recurso en esa obra; (c) **casamiento** por nombre y categoría
  (`resolver_normal`, `auto_*`); (b) **último parte** en otra obra,
  trasladado por código y descripción. Pasos, reglas (R2-R7 de F-050) y
  métodos no cambian; vale en el selector, el preflight y R34.
- **R29.** `[D2][D9]` *(cambiada el 2026-10-14 por D9; antes excluía las
  escrituras)* CUANDO se pide el cuadrante de un periodo **ABIERTO**, termina
  con éxito un `POST /sync` (cada abierto) o se escribe en el de uno ABIERTO
  (guardar la fila o F7, F8, Completar, Copiar mes, Deshacer, cambiar la
  partida), la api encola sus **pendientes** (todas las empresas; del periodo
  o solo de los trabajadores escritos): obra normal, sin `partida_fija`, sin
  elegida ni propuesta guardada, fuera de la memoria de R32 y no en cola.
- **R30.** `[D9]` *(cambiada el 2026-10-14)* Corre **en segundo plano** (un
  hilo en la api, cola por orden de llegada); el cuadrante y las escrituras
  no lo esperan y responden con `propuestas_en_curso` (verdadero si alguna
  línea del periodo está en cola o en marcha). Lo encolado no se reencola.
- **R31.** La api agrupa las pendientes por obra y llama **una** vez a R34
  por trozo de ≤ 10 obras; tras cada uno guarda y confirma cada propuesta
  **solo si** la línea sigue sin elegida ni propuesta (sin evento). **R32.**
  Una línea sin propuesta posible, o cuya obra vuelve `{ok: false}`, entra en
  una memoria del proceso y no se repite hasta el próximo sync con éxito (que
  la vacía) o un reinicio. **R33.** SI el transfer no responde, falla o pasa
  su timeout, ENTONCES esa tarea se para con un log, sin guardar el trozo ni
  tocar R32 (el próximo `GET` o escritura de R29 la relanza).
- **R34.** `[D6]` `POST /api/partidas/propuesta-lote` (`{peticiones:
  [PropuestaIn]}`, mismo `ano`/`mes` o 422) → `{ok, obras}`: por petición, en
  su orden, `{ok: true, propuestas}` (las de `POST /api/partidas/propuesta`,
  R21) o `{ok: false, error}`. Obras e historial, **una** lectura por lote;
  presupuestos, uno por obra en paralelo (R23); fallo compartido, 502 (R24).
- **R35.** `GET …/propuestas` (solo lee) devuelve `{en_curso, lineas}`: las
  automáticas con propuesta guardada (trabajador, obra, `_cod/_res/_metodo`).
- **R27.** `[D7]` La celda Partida de una automática con propuesta la enseña
  en cursiva (código · descripción y método); sin ella, «automática».
  `LineaOut` publica `propuesta_cod`, `_res` y `_metodo`.
- **R36.** `[D9]` MIENTRAS `propuestas_en_curso` (del cuadrante o de una
  escritura, R37), el front pone «buscando partida…» en las pendientes y
  consulta R35 cada 5 s con **un solo** temporizador; pinta solo celdas
  Partida de líneas aún sin elegida, no la fila en edición, y para con
  `en_curso` falso o al cambiar de mes o empresa. No decide nada.
- **R37.** `[D9]` La respuesta de cada escritura de R29 (rutas: design §5.5)
  gana `propuestas_en_curso`; el resto de su forma no cambia. SI encolar
  falla, ENTONCES responde igual, con `propuestas_en_curso` falso y un log.

## 5. Documentación y criterio de éxito (antes = T2, después = T18)

- **R28.** `ARCHITECTURE.md#regla-partida`: orden (R38), propuesta guardada,
  cuándo se calcula (R29), validación por `ide`; «Acceso a datos»: lotes;
  `INTEGRACION.md`: R19, R34, R35, R37, variable, columnas; líder: azure-apps.
- **C1** (test): R19 con 1, 2 y 10 obras con partida: mismas lecturas salvo
  `cuentas_de_centro` (una por centro); ninguna de presupuesto ni historial.
  **C2** (test): una obra con elegidas, hoy 8-9 lecturas en serie (T1);
  después ≤ 6 en ≤ 4 rondas. **C7** (test): R34 con 10 obras: 1 lectura de
  obras, 1 de historial y 10 de presupuesto, en ≤ 4 rondas con límite 4.
- **C3** (MANUAL local, modo pruebas): GONZALEZ PANIAGUA (0694 + 0696),
  09/2026, con partida: de «⇪ Sigrid» al modal **≤ 30 s y ≤ 40 % del antes**.
  **C4**: el mes entero **≤ 60 s y sin 502**. **C5**: repreflight al cambiar
  una partida **≤ 20 s**. **C6** (producción, solo preflight y Cancelar): C3
  y C4 antes y después de desplegar. **C8** (MANUAL local): 09/2026 sin
  propuestas: el cuadrante sale como hoy y la Partida se llena **≤ 3 min**;
  tras guardar una fila con una obra nueva, la suya **≤ 60 s** sin recargar (humano, 2026-10-17; era 30).
- SI C3-C5 o C8 no se cumplen, ENTONCES **PARA** y se repropone. Tests
  anteriores que cambian: **lista CERRADA** en la cabecera de `tasks.md`;
  otro, **PARA** y se pregunta. MANUAL: T2, T18-T19; nadie escribe en Sigrid.
