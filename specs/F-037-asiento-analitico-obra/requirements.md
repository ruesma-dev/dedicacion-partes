<!-- specs/F-037-asiento-analitico-obra/requirements.md -->
# F-037 · La línea del parte lleva su cuenta analítica de obra (asiento analítico)

Rigor **`critico`**: cambia lo que el transfer escribe en Sigrid, y el transfer
desplegado escribe **de verdad** desde el 2026-10-01 (`docs/INTEGRACION.md` §8).
Ninguna verificación automática lanza `registro/ejecutar`.

Servicio: **solo `dedicacion-transfer`**, más documentación (`docs/`,
`azure-apps/dedicacion.md`). `dedicacion-api` y `dedicacion-front` no se
tocan: los campos nuevos de la respuesta son aditivos y el front ya pinta
`AccionLinea.aviso`. Evidencia: **`progress/explore_F-037.md`**.

**Base:** el humano, 2026-10-05: «el parte debe generar asiento en la cuenta
analítica en Sigrid», a partir del correo «ARBOL ANALITICO OBRAS» de Juan
Romero (Dir. Admón y Control de Costes), 2026-09-29.

## 0. Primera conclusión de la exploración

**El asiento analítico del parte ya lo genera Sigrid**: un documento
`ANA<aa>/nnnnn` (`con.tip = 32`, `asa` + `apa` sin apunte financiero) por
parte (obra y mes) con **debe** a la cuenta analítica de cada línea
(`hmores.caaide`, p. ej. `0702.CIMO02 JEFE DE OBRA`) y **haber** a la del
recurso (`res.caaconide`, centro `CP` de personal), con el botón «Contabiliza
parte…» del parte, que lo deja en `con.est = 10`. En 2025 casa con 438 de
440 partes al céntimo. El 6XX ya lo pone la nómina (640/642 a `CP`).
**Lo que falta es que el transfer escriba `hmores.caaide`**: hoy escribe 0, y
una línea sin cuenta no entra en ningún ANA. El centro (`hmores.cenide`) ya
lo escribe bien. Esta spec **no** hace que el transfer escriba asientos (D1).

Glosario. **Hoja analítica**: lo que va tras el primer punto del código de una
cuenta (`00000.CIMO02` → `CIMO02`; `CIMO05` sin punto → `CIMO05`), sin
espacios y en mayúsculas. **Obra destino**: la obra en cuyo parte se escribe
la línea (la normal, la de postventa o, en modo pruebas, la de pruebas).
**Centro de la obra**: `obr.cenide`. **Parte contabilizado**: parte con
`con.est = 10`, el que ya tiene su ANA (explore §9).

## 1. Cuenta analítica de cada línea (#regla-analitica)

- **R1.** CUANDO el transfer inserta una línea en `hmores`, debe escribir en
  `caaide` la cuenta analítica resuelta según R2-R4, y no un 0 fijo.
- **R2.** La hoja de la línea debe ser la de la cuenta `reshor.caaide` del
  recurso para el tipo de hora elegido por P1; SI esa ficha no tiene cuenta,
  la de `auxhor.caacod` de ese tipo de hora.
- **R3.** La cuenta debe ser la **única** `caa` del centro de la obra destino
  cuya hoja sea la de la línea, **sin mirar la partida** (D3). En postventa,
  la del centro de la obra de postventa; en modo pruebas, la del centro de la
  obra de pruebas.
- **R4.** SI la línea no tiene hoja, la obra destino no tiene centro, el
  centro no tiene cuenta con esa hoja o tiene más de una, ENTONCES el sistema
  debe escribir la línea con `caaide = 0` y dejar en su acción un aviso que
  nombre la causa (hoja, obra y, si las hay, cuántas cuentas). **Nunca se
  elige la primera.** (D9)
- **R5.** El aviso de R4 no debe crear un `Conflicto` ni retener la línea, y
  debe sumarse al de «sin partida» si la línea tiene los dos, sin sustituirlo.
- **R6.** El preflight debe publicar en cada acción `escribir` su `caaide` y
  su `cuenta_analitica` (código completo, o nulo), y `ejecutar` debe añadir
  `cuenta_analitica` a cada entrada de `escritas`.
- **R7.** El transfer debe leer las cuentas de cada centro **una sola vez por
  petición**, y la hoja en la **misma** lectura de `reshor` que ya hace. SI
  una lectura viene `truncated`, ENTONCES debe fallar, no seguir con media.
- **R8.** `hmores.cenide` debe seguir siendo el centro de la obra destino
  (como hoy), y `cuaide` no se escribe (0 en las 30.075 líneas de 2026).

## 2. El parte ya contabilizado (D11)

- **R9.** CUANDO el parte destino ya existe y está contabilizado, el
  preflight debe publicar `ParteDestino.contabilizado = true` y sumar a cada
  acción `escribir` de ese parte un aviso: la línea no entrará en su asiento
  analítico hasta que Administración lo regenere.
- **R10.** Ese aviso no debe crear un `Conflicto` ni retener la línea, y el
  estado debe salir de la misma lectura que localiza el parte (sin otra).

## 3. Lo que el transfer NO hace

- **R11.** Ninguna sentencia de `registro/ejecutar` debe tocar `asi`, `asa`,
  `apu` ni `apa`, ni insertar un `con` de tipo distinto del parte (35).
- **R12.** La idempotencia sigue siendo la `synckey` `porcentajes:{id}` de
  `hmores`: una línea `ya_registrado` no se reescribe ni se actualiza para
  rellenarle la cuenta. (D10)
- **R13.** CUANDO se confirma un pisado, la línea nueva debe llevar su cuenta
  según R1-R4; lo borrado se borra como hoy, sin tocar ningún ANA. (D8)

## 4. Documentación

- **R14.** `docs/ARCHITECTURE.md` debe tener la regla nueva con ancla
  `regla-analitica` (R1-R13, de dónde sale cada cuenta, quién genera el ANA y
  qué pasa al deshacer o corregir, que hereda F-033), y el test de fuente
  única debe exigir esa ancla.
- **R15.** `#regla-sin-partida` no debe llamar «imputación analítica» a la
  partida: la analítica es `hmores.caaide`.
- **R16.** `docs/INTEGRACION.md` (§1, §7 y fecha) debe recoger las lecturas
  nuevas (`caa`, `con.est` del parte, `reshor.caaide`, `auxhor.caacod`), qué se
  rompe si cambian y la dependencia del ANA de Administración; la copia en
  `azure-apps/dedicacion.md` se refresca en el mismo trabajo.

## 5. Verificación con Administración (MANUAL, obra de pruebas)

- **R17.** En local, transfer de la rama con `OBRA_PRUEBAS_FORZAR=true`,
  preflight y `ejecutar` de una línea MENC o MJEFO en 0404 en un mes **sin
  más actividad en 0404**: la línea `PRUEBA-PORC` lleva `caaide` =
  `0404.CIMO03` u `0404.CIMO02` y `cenide` = centro de 0404. Exige
  autorización expresa del humano para esa escritura.
- **R18.** Administración pulsa «Contabiliza parte…» en ese parte: debe a `0404.CIMOxx` por `hmores.tot`, haber a `CP.<persona>` del
  recurso. Después, limpieza: `prueba_escritura_porcentajes.py limpiar
  --confirmar` borra la línea y Administración anula ese ANA.

## 6. Decisiones abiertas (las valida Juan Romero o el humano)

**D1 · Alcance.** A) el transfer rellena `hmores.caaide` y el ANA lo sigue
generando Administración; B) el transfer genera su propio ANA (`con` tipo 32
+ `asa` + `apa`); C) asiento financiero 64X con desglose, como XRT26/05432.
**Recomendada A.** B duplica el traspaso (el ANA es por parte y nuestras
líneas viven en el parte de las manuales) y no tiene `synckey` donde
apoyarse; C duplica el 640/642 de la nómina. **La herramienta que genera el
ANA parece ser el botón «Contabiliza parte…»** del parte (captura de Juan
Romero, 2026-10-05; `con.est = 10` en los 502 partes con ANA, explore §9):
confirmar con él que lee `hmores.caaide` y qué hace al repetirlo.

Con D1 = A, lo que la consulta del líder pedía decidir queda así:

| D | Pregunta | Con A (recomendada) | Evidencia (explore) |
|---|---|---|---|
| D2 | Cuenta 6XX | Ninguna desde el transfer: la pone la nómina | §5: 640 7,66 M€ y 642 2,52 M€ a `CP` en 2025 |
| D3 | Cuenta analítica | `<obra>.CIMOxx` del tipo de hora del recurso (CI > mano de obra indirecta), no de la partida | §3 y §9: cuando partida y tipo difieren, 540 de 540 líneas M\* siguen al tipo |
| D4 | Contrapartida | `res.caaconide` (`CP.<persona>`), la pone el ANA | §4: 11 haberes de ANA26/00056; 8 recursos sin ella |
| D5 | Importe | `hmores.tot` = dedicación × importe mensual (P3) | §4: debe = total del parte en 438/440 |
| D6 | Fecha / serie | Fecha del parte (P2), serie `ANA<aa>` de Administración | §4 |
| D7 | Agrupación | Un ANA por parte (obra y mes) | §4: sin duplicados desde 2020 |

**D8 · Deshacer o corregir una línea registrada.** A) antes del ANA no hay
nada que hacer; después, el aviso de R9 y Administración regenera o ajusta el
ANA; F-033 hereda esta regla; B) el transfer regenera el ANA. **Recomendada
A** (con B el transfer escribiría asientos).

**D9 · Línea sin cuenta.** A) se escribe con `caaide = 0` y aviso (R4); B)
conflicto confirmable como «sin partida» (toca api y front: fuera del límite
de esta feature); C) se omite. **Recomendada A**: no empeora lo de hoy y
avisa. Caso real: 0404 no tiene `CIMO16` (MPRL). El MPRL → `CIMO04` de la
captura de 0711 no es un respaldo: 0711 sí tiene `CIMO16`; es un cambio a
mano en una línea de 0 € (explore §9). Preguntar si MPRL debe ir a `CIMO04`.

**D10 · Líneas escritas antes de desplegar F-037.** Hoy hay **cero**
`porcentajes:` en Sigrid. A) nada; B) script de relleno de `caaide` (es una
escritura: feature aparte). **Recomendada A** (y no registrar en real antes).

**D11 · Parte ya contabilizado (R9-R10).** A) se escribe con aviso; B) no se
avisa; C) se omite la línea. **Recomendada A**: `con.est = 10` ⇔ ANA en los
784 partes desde 2025, sin lectura extra. Preguntar si se puede escribir en
un parte contabilizado (Sigrid a mano quizá no lo deja).
