<!-- specs/F-037-asiento-analitico-obra/requirements.md -->
# F-037 · La línea del parte lleva su cuenta analítica de obra (asiento analítico)

Rigor **`critico`**: cambia lo que el transfer escribe en Sigrid, y el transfer
desplegado escribe **de verdad** desde el 2026-10-01 (`docs/INTEGRACION.md` §8).
Ninguna verificación automática lanza `registro/ejecutar`.

Servicio: **solo `dedicacion-transfer`** y documentación. Las líneas de
`CLAUDE.md` (D15, D18) las pone el líder. Api y front no se tocan. Evidencia:
`progress/explore_F-037.md` y **`progress/explore_F-037_partes_F-031.md`**
(revisión de la F-031 de `partes`).

**Base (humano):** 2026-10-05, «el parte debe generar asiento en la cuenta
analítica en Sigrid» (correo «ARBOL ANALITICO OBRAS» de Juan Romero, Dir.
Admón y Control de Costes, 2026-09-29), «la cuenta analítica sale del
recurso; mira en partes», «un parte ya contabilizado va a complementario».
2026-10-06: spec aprobada (D8, D10, D12, D14-D16 = A) y **«la f31 de partes
ya in progress, revísalo, y copia adaptándolo aquí a porcentajes (se usa el
mismo parte realmente)»**: lo que toca el parte es **idéntico** a `partes`.

## 0. Conclusión de la exploración

Sigrid ya genera el asiento analítico: «Contabiliza parte…» crea un ANA
(`con.tip = 32`) por parte con debe a `hmores.caaide` y haber a
`res.caaconide`, y pasa el parte a Imputado. El 6XX lo pone la nómina. Falta
que el transfer escriba `hmores.caaide` (hoy 0) y que no escriba en partes
cerrados. **Fuente de la copia:** rama `feature/F-031-asiento-analitico` de
`partes` (design §13).

Glosario. **Subcuenta**: texto tras el primer punto del código, sin espacios
a los lados. **Obra destino**: aquella en cuyo parte se escribe (normal,
postventa o, en pruebas, la de pruebas). **Partes del periodo**: los `hmo` de
la obra destino, `ano` y `mes`, `reside = 0`, tipo de parte, con su `con.est`.
**Cerrado**: `con.est` distinto de En registro (1): Cerrado (3), Imputado
(10) u otro (D16). **Complementario**: el parte elegido cuando el periodo
tiene alguno cerrado.

## 1. Cuenta analítica de cada línea (#regla-analitica; = `partes` F-021/F-031)

- **R1.** CUANDO el transfer inserta una línea en `hmores`, debe escribir en
  `caaide` la cuenta resuelta según R2-R5, y no un 0 fijo.
- **R2.** La subcuenta sale de `reshor.caaide` del recurso para el tipo de
  hora escrito; si no da, de la de su tipo por defecto (`res.horide`).
- **R3.** SI el recurso no da subcuenta Y la cuenta de la partida de la línea
  (`obrparpar.caaide`) tiene subcuenta que empieza por `CI` o `CD`, ENTONCES
  vale esa, con `caa_origen = "partida"` y una `caa_nota` que nombra partida
  y subcuenta. Nunca `CP` ni `INGR`, ni `res.caaide` ni `auxhor.caacod`.
- **R4.** La cuenta es la **única** `caa` con `caa.cenide` = centro de la obra
  destino, `con.emp` = empresa de esa obra y esa subcuenta.
- **R5.** Sin subcuenta: `caaide = 0` sin aviso. Obra sin esa cuenta o con
  varias: `caaide = 0` y `caa_aviso`. La línea se escribe igual y **nunca se
  elige la primera**. Los avisos no crean `Conflicto` ni retienen la línea.
- **R6.** Cada acción lleva `caa_ide`, `caa_cod`, `caa_motivo`, `caa_aviso`,
  `caa_origen` y `caa_nota` (contrato de `partes`); `caa_aviso`, `caa_nota` y
  el aviso del parte se suman además a `AccionLinea.aviso`, que es lo que
  pinta el front. `escritas[]` lleva `caa_cod`.
- **R7.** Partidas y cuentas de centro se leen **una vez por petición**;
  `reshor.caaide`, en la lectura de horas de hoy. SI una lectura falla o
  viene `truncated`, ENTONCES la petición falla sin escribir nada.
- **R8.** `hmores.cenide` sigue siendo el centro de la obra destino; `cuaide`
  no se escribe.

## 2. El parte del periodo (= `partes` F-031 R1-R16)

- **R9.** Por periodo con acciones `escribir`, el transfer lee **todos** sus
  partes con su estado en **una** consulta.
- **R10.** Las líneas van al parte En registro de **mayor `ide`**, aunque haya
  cerrados de `ide` mayor; SI no hay ninguno, a uno nuevo (complementario si
  hay cerrados). Se reutiliza el complementario que haya creado `partes`.
- **R11.** El parte nuevo se crea con el alta de hoy: `con` (empresa de la
  obra, tipo 35, En registro, `PT<AA>/NNNNN` **correlativo por empresa**,
  descripción `Parte <obra>` (D13), último día del mes) y `hmo` localizado por código,
  tipo **y empresa**. Tras crearlo se relee el periodo; SI no aparece En
  registro, ENTONCES la petición falla sin insertar líneas.
- **R12.** Una `synckey` `porcentajes:{id}` en cualquier parte, también
  cerrado, es `ya_registrado`, sin escribir ni borrar.
- **R13.** Identidad (P4) y capacidad se evalúan contra las líneas de
  **todos** los partes del periodo. CUANDO la acción choca con una línea
  ajena de un parte **cerrado**, ENTONCES pasa a `omitir` con motivo
  `parte_cerrado: …` (parte y estado) y `caa_*` vacíos; con una de un parte
  En registro, conflicto confirmable como hoy con el `parte_cod` donde vive.
  El primero prevalece.
- **R14.** `pisar_claves` solo borra líneas de partes En registro.
- **R15.** Cada parte del preflight y del resultado lleva `estado`,
  `complementario`, `cerrados`, `del_periodo` y `aviso` (texto de `partes`).
- **R16.** SI la lectura de partes o de líneas existentes falla o viene
  `truncated`, ENTONCES la petición falla sin escribir.

## 3. Lo que el transfer NO hace

- **R17.** Ninguna sentencia toca `asi`, `asa`, `apu` ni `apa`, cambia
  `con.est` o el `con`/`hmo` de un parte existente, ni inserta o borra en un
  parte cerrado. Una línea `ya_registrado` no se reescribe ni se rellena su
  cuenta. Un pisado confirmado lleva su cuenta según R1-R5.

## 4. Documentación

- **R18.** `docs/ARCHITECTURE.md`: `#regla-analitica` (R1-R17, quién genera el
  ANA, deshacer y corregir, F-033, y que la regla es la de `partes`); alcance
  «partes del periodo» en `#regla-conflicto` y `#regla-capacidad`;
  `#regla-sin-partida` sin llamar «imputación analítica» a la partida; ancla
  en el test de fuente única.
- **R19.** `docs/INTEGRACION.md` (§1, §7, fecha): lecturas nuevas, el
  complementario, «Contabiliza parte…» y que el parte se comparte con
  `partes`; copia en `azure-apps/dedicacion.md`.

## 5. Verificación con Administración (MANUAL, obra de pruebas)

- **R20.** En local, transfer de la rama con `OBRA_PRUEBAS_FORZAR=true` y
  autorización expresa del humano: una línea MENC o MJEFO en 0404 en un mes
  sin más actividad lleva `caaide` = `0404.CIMO03` o `0404.CIMO02`.
- **R21.** Administración pulsa «Contabiliza parte…» (parte a Imputado, ANA
  con debe a `0404.CIMOxx` por `tot` y haber a `CP.<persona>`) y confirma que
  la línea se ve como una tecleada; otra línea del mismo mes va a un
  complementario que se contabiliza aparte. Limpieza: `limpiar --confirmar`
  y Administración anula los ANA y el complementario.

## 6. Decisiones

**Decididas por el humano.** 2026-10-05: D1 = A (rellenar `caaide`, sin
asientos propios; descartados ANA propio y 64X); D3 y D9 = regla de `partes`;
D11 = complementario. 2026-10-06, todas A: **D8** en En registro como hoy, en
cerrado nada se borra y ajusta Administración (F-033 lo hereda; descartado
regenerar el ANA). **D10** nada que rellenar (hoy cero líneas; descartado un
script). **D12** En registro de mayor `ide` (descartado el de menor). **D14**
choque con cerrado → `omitir` (descartado mirar solo el destino). **D15**
copia de `cuenta_analitica.py` de `partes` en la lista cerrada (descartado
reescribirla). **D16** cerrado = no En registro, como `partes` (descartado
solo Imputado). D2, D4-D7: el 6XX, la contrapartida, el importe, la fecha, la
serie y la agrupación son del ANA de Administración (explore §4-§5).

**Decididas por el humano el 2026-10-06** (tras la revisión de `partes`):

- **D13 · Descripción del complementario: `Parte <obra>`**, como `partes`
  (F-031 R3) y Administración en sus 7 complementarios reales; es el mismo
  parte. **Sustituye a la decisión del 2026-10-05** (`Parte <obra>
  (complementario)`), que queda descartada.
- **D17 · Carrera entre servicios: alta protegida**, en una transacción con
  bloqueo (código libre en la empresa y ningún parte En registro del
  periodo), relectura y un reintento (design §6.5, §7); se avisa a `partes`
  (T11). Descartado: aceptarla y detectarla solo en la relectura.
- **D18 · `estado_parte.py`** entra en la lista cerrada de copias de
  `CLAUDE.md` junto a `cuenta_analitica.py` (la línea la pone el líder).
  Descartado: reescribirlo.
