<!-- specs/F-055-preflight-rapido/requirements.md -->
# F-055 · El registro sin búsquedas de partidas (medir y acelerar)

Rigor **`critico`** (decide qué se escribe en Sigrid). Toca **transfer, api y
front** (design §1). Pedida el 2026-10-08; **rediseñada por el humano el
2026-10-11**: «al darle a registrar […] solo debería comprobar si los partes
están o no, pero no las partidas». Se apoya en la partida por línea de F-050
y se implementa **tras fusionar F-050** (con su T15c). **D1-D8: ABIERTAS**
(design §11); los R marcados `[Dn]` van escritos con la recomendada (A).

Glosario: **elegida** = la partida que guarda el usuario (F-050);
**propuesta guardada** = la que calcula el transfer y guarda la api (nuevo);
**automática** = línea de obra normal sin elegida; **lote** = todas las obras
de un preflight de la api; **lectura** = una llamada a `sigrid-api`.
Fuera de alcance: cambiar reglas de registro, `ejecutar` en lote (D6),
F-048, F-051, F-044.

## 1. Medición

- **R1.** Cada lectura del transfer debe dejar un log con su nombre (el del
  método del cliente), filas y segundos; cada preflight, uno con su obra,
  lecturas, segundos leyendo y segundos totales. Sin SQL ni parámetros.
- **R2.** `prueba_escritura_porcentajes.py` debe tener la fase de solo
  lectura `medir` (`--ano`, `--mes`, `--obra` y `--recurso` repetibles,
  `--partida OBRA:PARIDE`, `--lote`) que ejecuta el preflight y enseña
  segundos por lectura, por obra y en total, sin `escribir` ni `ejecutar`.

## 2. El registro no busca partidas (transfer)

- **R3.** `[D3]` CUANDO una línea de obra normal llega con partida (elegida o
  propuesta guardada), el preflight NO debe leer para ella el presupuesto
  (`capitulos_de_obra`) ni el historial: la valida con `validar_partidas`,
  **una** lectura por petición, por `ide` (obra, si tiene hijas, baja).
- **R4.** El veredicto de R3 debe ser el de hoy: vale solo la hoja activa del
  presupuesto de la obra de origen (capítulo, baja, otra obra o inexistente
  no valen), igual que `construir_catalogo`, también en modo pruebas.
- **R5.** SI la **elegida** no vale, ENTONCES se omite con
  `MOTIVO_PARTIDA_NO_HOJA`, como hoy (R20 de F-050).
- **R6.** `[D3]` SI la **propuesta guardada** no vale, ENTONCES la línea se
  trata como automática sin propuesta (R7), sin omitirla.
- **R7.** `[D1]` Una automática sin propuesta guardada sigue el camino de hoy:
  presupuesto de su obra, una lectura de historial por petición o lote, y
  `proponer_partida`.
- **R8.** Una línea con propuesta guardada válida se escribe con ella; su
  acción publica el `partida_metodo` y `partida_origen` guardados.
- **R9.** Toda acción con partida publica también `partida_res`.
- **R10.** `partidas_obra` solo lleva catálogo si el preflight leyó el
  presupuesto (R7); si no, `[]` sin lectura (se retira la lectura forzada de
  F-049 ampliación d; el front no lo lee desde F-050 R29).
- **R11.** Postventa y VAR siguen con sus reglas y lecturas (el casado P5
  necesita el presupuesto de postventa; VAR, su catálogo); en un lote, una
  vez (R20).
- **R12.** Partes y su estado, pisados, sobrecarga, idempotencia, sin
  partida, cuenta analítica (F-037) y modo pruebas: mismas reglas, con lo
  leído **en esa misma petición**.

## 3. La propuesta guardada (api)

- **R13.** `[D2]` `asignacion` gana `propuesta_ide` (BigInteger),
  `propuesta_cod`, `propuesta_res`, `propuesta_metodo` y `propuesta_origen`
  (Text), nulables, en el ORM (`esquema.py` deriva el DDL).
- **R14.** `[D2]` CUANDO un preflight devuelve, para una línea de obra normal
  sin elegida, una partida con método de propuesta (`parte_anterior`,
  `ultimo_parte`, `auto_*`), la api debe guardarla **si sigue sin
  elegida**, sin evento, sin tocar `sigrid_*` ni la respuesta al front.
- **R15.** `[D2]` CUANDO se abre el selector (R17 de F-050) y el transfer
  devuelve propuesta, la api debe guardarla igual.
- **R16.** Al registrar, la línea sin elegida con propuesta guardada viaja con
  `propuesta_paride`, `_cod`, `_res`, `_metodo` y `_origen`; la elegida, como
  hoy (`paride`, manda); VAR, como hoy.
- **R17.** Guardar la fila conserva la propuesta de cada línea cuya clave ya
  existía; la nueva entra sin ella. Copiar el mes, Completar y F7 no la
  copian; deshacer no la restaura; cambiar la elegida no la borra.
- **R18.** `[D8]` La propuesta guardada no caduca: se reescribe al abrir el
  selector (R15) y cuando el transfer la recalcula (R6).

## 4. Lote, agrupación y paralelo

- **R19.** `[D6]` El transfer debe exponer `POST /api/registro/preflight-lote`
  (`{peticiones: [PeticionIn]}` → `{ok, obras}`): una entrada por petición,
  en su orden, con la forma del preflight de hoy o `{ok: false, error}`.
- **R20.** `[D5]` En un lote, obras por `ide`, horas, `synckey`, validación y
  cuentas de partida, historial, partes del periodo y sus líneas se leen
  **agrupados** (una lectura por tipo, en trozos de ≤ 500 parámetros); obra
  de pruebas, postventa y VAR con su presupuesto, presupuesto de cada obra y
  siguiente código PT, **una vez** por lote.
- **R21.** El resultado de cada obra en un lote debe ser **idéntico** al de
  su preflight suelto con los mismos datos de Sigrid.
- **R22.** `[D4]` Lo leído vale solo para esa petición; lo no precargado va a
  `sigrid-api`: nunca vacío ni datos de otra petición.
- **R23.** `[D5]` Lecturas independientes y decisiones por obra corren en
  paralelo hasta `SIGRID_LECTURAS_PARALELAS` (defecto 4; 1 = en serie). SI
  vale < 1 o > 8, ENTONCES el transfer no arranca.
- **R24.** SI una lectura agrupada o compartida falla o viene `truncated`,
  ENTONCES fallan las obras que dependen de ella; un fallo propio de una obra
  (no encontrada, ambigua) solo marca esa obra.
- **R25.** La ruta de R19 es síncrona (threadpool): no bloquea el bucle.
- **R26.** `[D6]` La api pide el preflight con **una** llamada a R19 y
  devuelve al front la forma de hoy (`ok`, `obras`, `no_vigentes`).
  `ejecutar` sigue por obra y en serie, con R3-R12.

## 5. Front y documentación

- **R27.** `[D7]` La celda Partida de una línea sin elegida con propuesta
  guardada la enseña en cursiva (código · descripción y método); sin ella,
  «automática». `LineaOut` publica `propuesta_cod`, `_res` y `_metodo`.
- **R28.** `ARCHITECTURE.md#regla-partida` gana la propuesta guardada y la
  validación por `ide`; «Acceso a datos», el lote; `INTEGRACION.md`, R19, la
  variable y las columnas; el líder, `azure-apps/dedicacion.md`.

## 6. Criterio de éxito (antes = T2, después = T16)

- **C1** (test): un lote de 1, 2 y 10 obras con partida en todas las líneas
  hace el mismo número de lecturas salvo `cuentas_de_centro` (una por centro
  destino); ninguna de presupuesto ni historial de obra normal.
- **C2** (test): una obra con partidas elegidas, hoy 8-9 lecturas en serie
  (T1 lo fija); después ≤ 6 en ≤ 4 rondas.
- **C3** (MANUAL local, modo pruebas): GONZALEZ PANIAGUA (0694 + 0696),
  09/2026, con partida: de «⇪ Sigrid» al modal **≤ 30 s y ≤ 40 % del antes**
  (estimado hoy: 70-100 s).
- **C4** (MANUAL local): el mes entero **≤ 60 s y sin 502**.
- **C5** (MANUAL local): repreflight al cambiar una partida **≤ 20 s**.
- **C6** (MANUAL producción, solo preflight y Cancelar): C3 y C4 antes de
  desplegar y después.
- SI C3-C5 no se cumplen, ENTONCES **PARA** y se repropone con lo medido.

## 7. Tests anteriores que cambian: lista CERRADA (con D1-D8 = A)

- Transfer: `conftest.py` (el `ClienteFalso` gana `validar_partidas` y los
  métodos agrupados, derivados de sus datos); en `test_f049_partidas_obra`,
  `test_f049_d_todas_manuales_publica_el_catalogo_de_origen` y
  `test_f049_d_varias_manuales_una_sola_lectura` esperan `partidas_obra ==
  []` y ninguna lectura del presupuesto (R10).
- Api: `test_f003_r8_la_tabla_queda_con_las_previas_mas_las_seis` (+5
  `propuesta_*`); `CAMPOS_LINEA` de
  `test_f034_rutas` (+3, R27); `_fila` de `test_f022_empresa_en_linea`,
  `test_f024_registro_empresa`, `test_f026_registro_recurso` y
  `test_f039_registro_var` (`propuesta_*` nulos) y sus transfer falsos
  (`preflight_lote` que delega en su `preflight`); el `_Uow` de
  `test_f050_rutas_partida` (R15). Sin tocar otras aserciones.
- Cualquier otro test que cambie: **PARA** y se pregunta al humano.

## 8. Verificación MANUAL (humano)

T2 (antes) y T16-T17 (después y regresión): `tasks.md`. Ningún agente
escribe en Sigrid; en producción, solo preflight y Cancelar.
