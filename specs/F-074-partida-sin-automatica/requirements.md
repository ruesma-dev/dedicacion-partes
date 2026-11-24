<!-- specs/F-074-partida-sin-automatica/requirements.md -->
# F-074 · La partida no se queda en «automática»: al registrar ya viene definida

Rigor **`critico`**; transfer, api y front (design §1). Negocio, 2026-11-22:
«O sale la que se va a encontrar después o sale que no encuentra y que se
ponga, pero dejarlo para luego no tiene sentido». Humano, 2026-11-23: «d6 la
b» y «cuando se le da a registrar ya no hay que casar partidas, ya vienen
definidas». Decisiones `[Dn]`: design §12 (D6 decidida). Casos de hoy:
design §2.

**Enmienda** lo que hacía el preflight al registrar: F-050 R9, F-055 R3-R8 y
R14, F-044 R15-R16 y F-068 R1-R16 (en el preflight), y el casado de
`#regla-p5`. La **regla** de la propuesta no cambia: solo deja de correr al
registrar. Fuera: la regla VAR, el Excel, los triggers de la cola (F-055
R29-R33), un contador de líneas sin partida.

Glosario: **definida** = la elegida, la fija VAR, la propuesta guardada o, en
postventa, la de su obra; **memoria «sin propuesta»** = la de F-055 R32;
**no encontrada** = sin definida y en esa memoria (o postventa fuera del
universo).

## 1. Al registrar, la partida ya viene definida (transfer)

- **R1.** El preflight (suelto y en lote) no debe proponer ni casar: cada
  línea usa su elegida (`paride`) o, sin ella, su propuesta guardada
  (`propuesta_*`), también en postventa (la de su obra, método `postventa`,
  R12); VAR, su fija (`#regla-var`, sin cambio). (capa: unit)
- **R2.** Cada subfila usa su elegida; si su titular va a postventa, VAR o
  partida no `CI*`, la del titular (F-044 R17, sin leer nada); si no, su
  propuesta guardada de método propio (F-068 R16). (capa: unit)
- **R3.** Toda partida definida se valida por `ide` en la lectura única de
  hoy (`validar_partidas`, F-055 R3): hoja activa del presupuesto de la obra
  de origen o, en postventa, de la obra de postventa, que se sigue
  resolviendo por código como destino. (capa: unit)
- **R4.** `[D4]` SI la partida definida no vale, ENTONCES la línea o subfila
  se omite con un motivo que la nombra (como F-050 R20) y su acción lleva
  `partida_no_valida` con su código; nunca se propone otra. (capa: unit)
- **R5.** `[D7][D8]` SI una línea o subfila llega sin partida definida,
  ENTONCES no se propone: la de obra normal y la subfila van al conflicto
  «sin partida» de `#regla-sin-partida` (con la casilla de escribirla sin
  partida solo si D8 = a); la de postventa se omite con motivo (`#regla-p5`).
  (capa: unit)
- **R6.** El preflight no debe leer el presupuesto de la obra de origen ni el
  de la obra de postventa, el historial del trabajador, el de los vinculados
  ni las cuentas del presupuesto; `partidas_obra` y `partidas_postventa`
  salen `[]`. El catálogo VAR, como hoy. (capa: unit)
- **R7.** El resultado de cada obra en un lote sigue idéntico al de su
  petición suelta (F-055 R21). (capa: unit)

## 2. La regla, solo en segundo plano (transfer)

- **R8.** La regla (`proponer_partida`, `PasoVinculados.proponer`,
  `casar_postventa`) solo debe correr en `partidas/propuesta(-lote)` y
  `postventa/universo`, con el mismo orden y resultado de hoy. (capa: unit)
- **R9.** `[D6]` `partidas/propuesta(-lote)` gana, por petición, `motivos:
  {clave: texto}` de cada línea sin propuesta y `motivos_vinculados: {clave:
  {recurso: texto}}` de cada subfila sin propuesta (titular sin partida,
  `sin_ci`, `varias_ci`, `empate_nombre`), solo con alguno. (capa: unit)
- **R10.** `[D6]` `postventa/universo` gana `motivos: {ide: texto}` de las
  obras pedidas que no casan (el texto de `casar_postventa`). (capa: unit)

## 3. La api guarda, marca y manda la definida

- **R11.** `[D2]` El sync debe guardar en cada obra su partida de postventa
  del universo (`ide`, `cod`, `res`) o, si no casa, nulas y su motivo (R10);
  con la misma llamada de hoy. (capa: unit)
- **R12.** Una línea de postventa sin elegida debe publicar como propuesta la
  de su obra (método `postventa`) y mandarla al registro como `propuesta_*`.
  SI la obra no casa, ENTONCES no encontrada con su motivo; SI aún no tiene
  partida guardada (sync pendiente), ENTONCES ninguna marca. (capa: unit)
- **R13.** Una línea de obra normal sin elegida ni propuesta guardada en la
  memoria «sin propuesta» debe publicar `propuesta_no_encontrada: true` y
  `propuesta_motivo` (el de R9 o el error de su obra `{ok: false}`) en el
  cuadrante, en cada escritura que hoy publica `propuesta_pendiente` y en
  `GET …/propuestas` (`no_encontradas`, con motivo). Misma lectura de la
  cola que `pendientes`; las claves, solo con valor. (capa: unit)
- **R14.** Una subfila sin elegida ni propuesta debe publicar
  `propuesta_pendiente` si está en su cola y `propuesta_no_encontrada` con
  `propuesta_motivo` si está en su memoria; `GET …/propuestas` gana
  `subfilas_pendientes` y `subfilas_no_encontradas`, solo con alguna.
  (capa: unit)
- **R15.** CUANDO `CambiarPartida` borra la propuesta de las subfilas de una
  línea (cambia la del titular, F-044 R9), la api debe sacarlas de su
  memoria antes de encolar, para recalcularlas. (capa: unit)
- **R16.** `[D4]` CUANDO el preflight devuelve `partida_no_valida` en una
  línea o subfila que viajó con propuesta guardada, la api debe borrarla si
  sigue sin elegida (sin evento), para que la cola la recalcule; la elegida
  no se toca. Deja de guardar propuestas al volver del preflight (F-055
  R14): ya no propone. (capa: unit)

## 4. Front (pinta lo que manda la api)

- **R17.** La celda Partida de una línea o subfila debe enseñar lo primero
  que aplique: elegida; fija; propuesta en cursiva con su método; «buscando
  partida…» (pendiente); «no encuentra partida» con su motivo (no
  encontrada); «sin calcular» (periodo ABIERTO); «—». Nunca «automática».
  (capa: unit)
- **R18.** `[D1]` «no encuentra partida» va como aviso (`partida-sin`, sin
  cursiva), con el motivo en el título; abierto, el clic abre el selector
  (F-050 R25). (capa: unit)
- **R19.** El front no decide el estado: lo toma de las claves de la api;
  solo `periodoEstado` separa «sin calcular» de «—». (capa: unit)
- **R20.** El filtro «Partida» y el buscador libre casan con el texto de la
  celda, línea a línea y subfila a subfila (F-067). (capa: unit)
- **R21.** `[D5]` La opción «automática (la propone el registro)» pasa a
  «sin elegir · usar la propuesta» o, sin propuesta, «sin elegir · no
  encuentra partida»; sigue borrando la elegida. (capa: unit)
- **R22.** El modal debe enseñar el selector (F-050 R29) también en la
  omitida por R4, con el motivo del transfer. (capa: unit)

## 5. Coste, documentación y criterio

- **R23.** El preflight debe leer menos o lo mismo que hoy y nada de lo de
  R6 (contado en los dobles: C1 y C2 de design §8); cuadrante, cola y sync,
  lo mismo, salvo el recálculo de R15. (capa: unit)
- **R24.** `ARCHITECTURE.md` (`#regla-partida`, `#regla-sin-partida`,
  `#regla-p5`, `#regla-vinculado`) dice que el registro usa la definida; la
  regla, solo en segundo plano. `INTEGRACION.md` §5: campos nuevos; el líder,
  `azure-apps/dedicacion.md`.

## 6. Tests anteriores que cambian: lista CERRADA por criterio

Solo pueden cambiar los tests que cumplan uno de estos criterios, y solo en
eso: (i) esperan que el **preflight** proponga o case (acción con método de
propuesta o `postventa` sin partida en la entrada); (ii) cuentan lecturas de
presupuesto, historial o cuentas en el preflight; (iii) esperan
`partidas_postventa` no vacío del preflight; (iv) pintan o filtran
«automática»; (v) comparan `ResultadoUniverso`; (vi) comparan la respuesta
exacta de `partidas/propuesta(-lote)` sin `motivos` (R9); (vii) esperan que
la validación por `ide` excluya las líneas de postventa (R3). **Cómo**: si
el test prueba otra cosa (cero, capacidad, incidencias, rachas…) y solo
cae en (i) porque su línea no trae partida, se le da una partida
**definida** y conserva lo que esperaba; solo los que prueban el casado en
el preflight cambian de expectativa o se retiran (enmienda del 2026-11-24,
OK del humano). El implementer anota en
`progress/impl_F-074.md` cada uno, con su criterio, antes de tocarlo
(ficheros candidatos: `tasks.md`). Otro test: **PARA** y se pregunta.

## 7. Verificación MANUAL (humano)

M1 (local, modo pruebas, solo preflight y Cancelar), M2 (medición `medir`
antes y después), M3 (base `dedicacion` local) y M4 (producción, tras un
sync): `tasks.md` T15-T18.
