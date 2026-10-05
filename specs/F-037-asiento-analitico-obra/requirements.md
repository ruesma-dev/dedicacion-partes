<!-- specs/F-037-asiento-analitico-obra/requirements.md -->
# F-037 · La línea del parte lleva su cuenta analítica de obra (asiento analítico)

Rigor **`critico`**: cambia lo que el transfer escribe en Sigrid, y el transfer
desplegado escribe **de verdad** desde el 2026-10-01 (`docs/INTEGRACION.md` §8).
Ninguna verificación automática lanza `registro/ejecutar`.

Servicio: **solo `dedicacion-transfer`**, más documentación (`docs/`,
`azure-apps/dedicacion.md`). La línea nueva de `CLAUDE.md` (D15) la pone el
líder. Api y front no se tocan: los campos nuevos son aditivos y el front ya
pinta `AccionLinea.aviso`. Evidencia: **`progress/explore_F-037.md`**.

**Base:** el humano, 2026-10-05: «el parte debe generar asiento en la cuenta
analítica en Sigrid» (correo «ARBOL ANALITICO OBRAS» de Juan Romero, Dir.
Admón y Control de Costes, 2026-09-29); «la cuenta analítica sale del
recurso; mira en partes»; «un parte ya contabilizado va a complementario».
**Spec aprobada el 2026-10-06** con A en D8, D10 y D12-D16, y «para lo de la
cuenta analítica recoge lo que estamos aprendiendo en partes, funciona igual».

## 0. Conclusión de la exploración

El asiento analítico del parte **ya lo genera Sigrid**: «Contabiliza parte…»
crea un `ANA<aa>/nnnnn` (`con.tip = 32`) por parte, debe a `hmores.caaide` de
cada línea y haber a `res.caaconide`, y pasa el parte a Imputado. El 6XX lo
pone la nómina. **Falta que el transfer escriba `hmores.caaide`** (hoy 0).
La regla es la de `partes` (F-021, desplegada, y su F-031, aprobada sin
mergear): design §13.

Glosario. **Subcuenta**: texto tras el primer punto del código, sin espacios
a los lados; sin punto o vacío, no hay. **Obra destino**: la obra en cuyo
parte se escribe (normal, postventa o, en pruebas, la de pruebas). **Partes
del mes**: los `hmo` de la obra destino, `ano` y `mes`, `reside = 0`, tipo
de parte, con su `con.est` (`conest`: 1 En registro, 3 Cerrado, 10
Imputado). **Parte cerrado**: Cerrado o Imputado (D16).
**Complementario**: el parte elegido cuando el mes tiene alguno cerrado.

## 1. Cuenta analítica de cada línea (#regla-analitica)

- **R1.** CUANDO el transfer inserta una línea en `hmores`, debe escribir en
  `caaide` la cuenta resuelta según R2-R5, y no un 0 fijo.
- **R2.** La subcuenta debe salir de `reshor.caaide` del recurso para el tipo
  de hora que se escribe; si no da, de la del tipo por defecto (`res.horide`).
- **R3.** SI el recurso no da subcuenta Y la partida de la línea tiene cuenta
  cuya subcuenta empieza por `CI` o `CD`, ENTONCES vale esa subcuenta (respaldo
  de `partes` F-031). Ni `res.caaide` ni `auxhor.caacod` intervienen.
- **R4.** La cuenta debe ser la **única** `caa` con `caa.cenide` = centro de
  la obra destino, `con.emp` = empresa de esa obra y esa subcuenta.
- **R5.** Sin subcuenta por R2 ni R3: `caaide = 0` sin aviso. Obra sin esa
  cuenta o con varias: `caaide = 0` con aviso que nombra obra y subcuenta.
  La línea se escribe igual y **nunca se elige la primera**.
- **R6.** Los avisos de R5 y R12 no crean `Conflicto` ni retienen la línea, y
  se suman al de «sin partida» si lo hay.
- **R7.** El preflight debe publicar en cada acción `escribir` `caa_ide`,
  `caa_cod` y `caa_origen` (`recurso`, `partida` o nulo); `ejecutar` añade
  `caa_cod` a cada `escritas`. Las acciones no `escribir` van con `caa_ide = 0`.
- **R8.** Las cuentas de los centros y las partidas del respaldo deben leerse
  **una vez por petición**, y `reshor.caaide` en la misma lectura de horas que
  hoy. SI una lectura falla o viene `truncated`, ENTONCES falla la petición.
- **R9.** `hmores.cenide` sigue siendo el centro de la obra destino, y
  `cuaide` no se escribe.

## 2. Parte cerrado: complementario

- **R10.** El transfer debe leer **todos** los partes del mes con su estado en
  la misma lectura que hoy localiza el parte.
- **R11.** Las líneas deben ir al parte En registro de **mayor `ide`** del mes;
  SI todos están cerrados, a uno nuevo creado con `stmts_crear_parte` (último
  día del mes, En registro, empresa de la obra, `Parte <obra>
  (complementario)`); SI tras crearlo la relectura no lo da, la petición
  falla sin insertar líneas. El original no se toca.
- **R12.** El preflight debe publicar por parte `estado`, `complementario` y
  los códigos de los cerrados, y avisar en cada acción `escribir` del parte
  complementario al que va.
- **R13.** Identidad (P4) y capacidad deben evaluarse contra las líneas de
  **todos** los partes del mes. SI la línea que se pisaría está en un parte
  cerrado, ENTONCES no se borra: la acción pasa a `omitir` con un motivo que
  nombra el parte y su estado, y sin cuenta.
- **R14.** La `synckey` `porcentajes:{id}` se busca en **cualquier** parte:
  una línea ya escrita en un parte cerrado es `ya_registrado`.

## 3. Lo que el transfer NO hace

- **R15.** Ninguna sentencia de `registro/ejecutar` toca `asi`, `asa`, `apu`
  ni `apa`, cambia `con.est`, inserta un `con` de otro tipo que el parte ni
  borra o inserta en un parte cerrado.
- **R16.** Una línea `ya_registrado` no se reescribe ni se rellena su cuenta.
- **R17.** CUANDO se confirma un pisado (solo en partes En registro), la línea
  nueva lleva su cuenta según R1-R5.

## 4. Documentación

- **R18.** `docs/ARCHITECTURE.md`: `#regla-analitica` (R1-R17, quién genera el
  ANA, deshacer y corregir, que hereda F-033, y que la regla es común con
  `partes`); alcance «los partes del mes» en `#regla-conflicto` y
  `#regla-capacidad`; `#regla-sin-partida` sin llamar «imputación analítica» a
  la partida; ancla exigida por el test de fuente única.
- **R19.** `docs/INTEGRACION.md` (§1, §7, fecha): lecturas nuevas (`caa`,
  `con.est`, `reshor.caaide`, `res.horide`, `obrparpar.caaide`), el
  complementario y la dependencia de «Contabiliza parte…»; copia en
  `azure-apps/dedicacion.md`.

## 5. Verificación con Administración (MANUAL, obra de pruebas)

- **R20.** En local, transfer de la rama con `OBRA_PRUEBAS_FORZAR=true` y
  autorización expresa del humano: una línea MENC o MJEFO en 0404 en un mes
  sin más actividad lleva `caaide` = `0404.CIMO03` o `0404.CIMO02` y `cenide`
  = centro de 0404.
- **R21.** Administración pulsa «Contabiliza parte…» (parte a Imputado; ANA
  con debe a `0404.CIMOxx` por `tot` y haber a `CP.<persona>`) y **confirma
  que la línea se ve como una tecleada**; otra línea del mismo mes va a un
  complementario que se contabiliza aparte. Limpieza: `limpiar --confirmar`
  y Administración anula los ANA y el complementario.

## 6. Decisiones

**Decididas por el humano el 2026-10-05:** D1 = A (rellenar `caaide`; el
transfer no escribe asientos; descartados ANA propio y asiento 64X). D3 y D9
= la regla de `partes` (R2-R5). D11 = complementario.

**Decididas por el humano el 2026-10-06** (todas A):

- **D8 · Deshacer o corregir.** En un parte En registro, como hoy; en uno
  cerrado nada se borra (R13, R15) y Administración ajusta; F-033 lo hereda.
  Descartado: que el transfer regenere el ANA.
- **D10 · Líneas anteriores a F-037** (hoy **cero**): nada. Descartado: script
  de relleno.
- **D12 · Parte reutilizado**: el En registro de mayor `ide`, como hoy.
  Descartado: el de menor.
- **D13 · Complementario**: `Parte <obra> (complementario)`, sin enlace.
  Descartado: el texto del original (lo que hace `partes`, design §13).
- **D14 · Pisado contra un cerrado**: `omitir` con motivo. Descartado: mirar
  solo el parte destino.
- **D15 · `cuenta_analitica.py`**: copia literal de la de `partes` tras su F-031,
  en la lista cerrada de `CLAUDE.md` (la línea la pone el líder), con un test
  que compara las dos. Descartado: reescribirla.
- **D16 · Qué estado manda al complementario**: cualquiera distinto de En
  registro (Cerrado o Imputado), igual que `partes` F-031. Descartado: solo
  Imputado. Consecuencia: de marzo a agosto de 2026, casi todo Cerrado sin
  contabilizar, las líneas van a complementarios (explore §11).

| D | Pregunta | Respuesta | Evidencia (explore) |
|---|---|---|---|
| D2 | 6XX | Ninguna desde el transfer: la nómina | §5 |
| D4 | Contrapartida | `res.caaconide`, la pone el ANA | §4 |
| D5-D7 | Importe, fecha, serie, agrupación | `hmores.tot`; fecha del parte; `ANA<aa>`; uno por parte | §4 |

**Implementación (humano, 2026-10-06):** espera a que la F-031 de `partes`
llegue a su `dev` y se copia su versión final, con el respaldo de R3
(condición de entrada en `tasks.md`).
