<!-- specs/F-037-asiento-analitico-obra/requirements.md -->
# F-037 · La línea del parte lleva su cuenta analítica de obra (asiento analítico)

Rigor **`critico`**: cambia lo que el transfer escribe en Sigrid, y el transfer
desplegado escribe **de verdad** desde el 2026-10-01 (`docs/INTEGRACION.md` §8).
Ninguna verificación automática lanza `registro/ejecutar`.

Servicio: **solo `dedicacion-transfer`**, más documentación (`docs/`,
`azure-apps/dedicacion.md`) y, si D15 = A, `CLAUDE.md`. Api y front no se
tocan: los campos nuevos son aditivos y el front ya pinta `AccionLinea.aviso`.
Evidencia: **`progress/explore_F-037.md`** (§9 captura de Administración,
§10 regla de `partes` y partes complementarios).

**Base:** el humano, 2026-10-05: «el parte debe generar asiento en la cuenta
analítica en Sigrid» (correo «ARBOL ANALITICO OBRAS» de Juan Romero, Dir.
Admón y Control de Costes, 2026-09-29), y ese mismo día: **«la cuenta
analítica sale del recurso; mira en partes»** y **«un parte ya contabilizado
va a complementario»**.

## 0. Conclusión de la exploración

El asiento analítico del parte **ya lo genera Sigrid**: «Contabiliza parte…»
crea un `ANA<aa>/nnnnn` (`con.tip = 32`, `asa` + `apa`) por parte, con debe a
`hmores.caaide` de cada línea y haber a `res.caaconide` del recurso, y deja el
parte en `con.est = 10`. El 6XX lo pone la nómina. **Falta que el transfer
escriba `hmores.caaide`** (hoy 0); `hmores.cenide` ya lo escribe bien. Esta
spec no hace que el transfer escriba asientos (D1).

Glosario. **Subcuenta**: el texto tras el primer punto del código de una
cuenta, sin espacios a los lados (`00000.CIMO08` → `CIMO08`); sin punto o sin
nada detrás, no hay. **Obra destino**: la obra en cuyo parte se escribe (la
normal, la de postventa o, en modo pruebas, la de pruebas). **Parte
contabilizado**: `con.est = 10`. **Parte del mes**: parte (`con.tip` de parte,
`hmo.reside = 0`) de la obra destino con ese `ano` y `mes`. **Complementario**:
un parte del mes que no es el contabilizado.

## 1. Cuenta analítica de cada línea (#regla-analitica, D3)

- **R1.** CUANDO el transfer inserta una línea en `hmores`, debe escribir en
  `caaide` la cuenta resuelta según R2-R4, y no un 0 fijo.
- **R2.** La subcuenta debe salir del código de `reshor.caaide` del recurso
  para el tipo de hora que se escribe; SI no da subcuenta, del de su tipo por
  defecto (`res.horide`). Ni `res.caaide`, ni `auxhor.caacod`, ni la partida.
- **R3.** La cuenta debe ser la **única** `caa` con `caa.cenide` = centro de
  la obra destino, `con.emp` = empresa de esa obra y esa subcuenta. En
  postventa, el centro de la obra de postventa; en pruebas, el de la de pruebas.
- **R4.** SI el recurso no da subcuenta, ENTONCES `caaide = 0` sin aviso. SI
  la obra no tiene esa cuenta o tiene varias, ENTONCES `caaide = 0` y un aviso
  en la acción que nombre obra y subcuenta. La línea se escribe igual y
  **nunca se elige la primera**. (D9)
- **R5.** El aviso de R4 no debe crear un `Conflicto` ni retener la línea, y
  debe sumarse al de «sin partida» si la línea tiene los dos.
- **R6.** El preflight debe publicar en cada acción `escribir` su `caa_ide` y
  `caa_cod` (o nulo), y `ejecutar` añadir `caa_cod` a cada `escritas`.
- **R7.** Las cuentas de un centro deben leerse **una vez por petición**, y la
  cuenta de `reshor` en la **misma** lectura de horas que hoy. SI una de esas
  lecturas falla o viene `truncated`, ENTONCES la petición debe fallar.
- **R8.** `hmores.cenide` debe seguir siendo el centro de la obra destino, y
  `cuaide` no se escribe (0 en las 30.075 líneas de 2026).

## 2. Parte contabilizado: complementario (D11)

- **R9.** El transfer debe leer **todos** los partes del mes de la obra
  destino con su estado, en la misma lectura que hoy localiza el parte.
- **R10.** MIENTRAS haya un parte del mes sin contabilizar, las líneas deben
  ir al de **mayor `ide`** de esos (el que elige hoy). (D12)
- **R11.** SI todos los partes del mes están contabilizados, ENTONCES el
  transfer debe crear uno nuevo con `stmts_crear_parte` (fecha = último día
  del mes, estado 1, empresa de la obra) y descripción `Parte <obra>
  (complementario)`, y escribir ahí. (D13)
- **R12.** El preflight debe publicar en cada parte si es complementario y los
  códigos de los partes contabilizados del mes, y sumar a cada acción
  `escribir` un aviso que nombre el parte complementario.
- **R13.** La identidad (P4) y la capacidad deben evaluarse contra las líneas
  de **todos** los partes del mes. SI la línea que se pisaría está en un
  parte contabilizado, ENTONCES no se borra: la acción se omite con un motivo
  que nombre ese parte. (D14)
- **R14.** La idempotencia sigue siendo la `synckey` `porcentajes:{id}`, que
  se busca en **cualquier** parte: una línea ya escrita en el original
  contabilizado sale `ya_registrado` y no se duplica en el complementario.

## 3. Lo que el transfer NO hace

- **R15.** Ninguna sentencia de `registro/ejecutar` debe tocar `asi`, `asa`,
  `apu` ni `apa`, ni insertar un `con` de tipo distinto del parte, ni borrar o
  modificar líneas de un parte contabilizado.
- **R16.** Una línea `ya_registrado` no se reescribe ni se actualiza para
  rellenarle la cuenta. (D10)
- **R17.** CUANDO se confirma un pisado en un parte sin contabilizar, la línea
  nueva debe llevar su cuenta según R1-R4. (D8)

## 4. Documentación

- **R18.** `docs/ARCHITECTURE.md`: regla nueva `#regla-analitica` (R1-R17,
  quién genera el ANA, qué pasa al deshacer o corregir, que hereda F-033);
  alcance de `#regla-conflicto` y `#regla-capacidad` («los partes del mes»);
  `#regla-sin-partida` sin llamar «imputación analítica» a la partida; y el
  test de fuente única exigiendo la ancla.
- **R19.** `docs/INTEGRACION.md` (§1, §7, fecha) con las lecturas nuevas
  (`caa`, `con.est`, `reshor.caaide`, `res.horide`), el parte complementario
  y la dependencia de «Contabiliza parte…»; copia en `azure-apps/dedicacion.md`.

## 5. Verificación con Administración (MANUAL, obra de pruebas)

- **R20.** En local, transfer de la rama con `OBRA_PRUEBAS_FORZAR=true` y
  autorización expresa del humano, `ejecutar` de una línea MENC o MJEFO en
  0404 en un mes sin más actividad en 0404: lleva `caaide` = `0404.CIMO03` o
  `0404.CIMO02` y `cenide` = centro de 0404.
- **R21.** Administración pulsa «Contabiliza parte…»: debe a `0404.CIMOxx`
  por `tot`, haber a `CP.<persona>`, parte en `est = 10`. Una segunda línea
  del mismo mes va a un parte `(complementario)` nuevo, que se contabiliza
  aparte. Limpieza: `prueba_escritura_porcentajes.py limpiar --confirmar` y
  Administración anula los ANA y el complementario.

## 6. Decisiones

**Decididas por el humano el 2026-10-05.** D1 = A (rellenar `caaide`, sin
asientos del transfer; Administración lo confirma en R21). D3 = la regla de
`partes` F-021 (R2-R4). D9 = la de `partes`: sin subcuenta del recurso, 0 sin
aviso; obra sin cuenta o con varias, 0 con aviso. D11 = complementario.

| D | Pregunta | Respuesta (con D1 = A) | Evidencia (explore) |
|---|---|---|---|
| D2 | Cuenta 6XX | Ninguna desde el transfer: la nómina | §5: 640 7,66 M€ y 642 2,52 M€ a `CP` en 2025 |
| D4 | Contrapartida | `res.caaconide`, la pone el ANA | §4: 8 recursos sin ella |
| D5 | Importe | `hmores.tot` (P3) | §4: debe = total en 438/440 |
| D6-D7 | Fecha, serie, agrupación | Fecha del parte, `ANA<aa>`, uno por parte | §4 |

**Abiertas** (opciones, recomendación):

- **D8 · Deshacer o corregir.** A) antes de contabilizar, como hoy; después,
  nada se borra en el contabilizado (R13, R15) y Administración ajusta;
  F-033 lo hereda. B) el transfer regenera el ANA. **A.**
- **D10 · Líneas anteriores a F-037.** Hoy hay **cero** `porcentajes:` en
  Sigrid. A) nada; B) script de relleno (escritura, feature aparte). **A.**
- **D12 · Qué parte sin contabilizar se reutiliza.** A) el de mayor `ide`,
  como hoy; B) el de menor. **A**: no cambia el comportamiento actual (explore
  §10: 0692 de 2026-09 tiene dos sin contabilizar).
- **D13 · Cómo se crea el complementario.** Sigrid no tiene convención ni
  enlace (explore §10). A) `Parte <obra> (complementario)`, sin enlace; B) el
  mismo texto que el original. **A**: se distingue y no depende de `res`.
- **D14 · Pisado contra el contabilizado.** A) se omite con motivo (R13); B)
  se evalúa solo el parte destino, como hoy (puede duplicar jornada en el
  mes). **A.**
- **D15 · `cuenta_analitica.py`.** A) copia literal de la de `partes` y entra
  en la lista cerrada de `CLAUDE.md` (decisión expresa del humano); B)
  reescribirla aquí con la misma regla. **A**: las dos escriben `hmores` y la
  regla tiene que ser la misma, y un test vigila que la copia no diverja.
