# F-062 · Rachas de incidencia como Administración

Rigor **`critico`**; transfer (decide y escribe), api (contexto y traza),
front (solo pinta): design §1. **Decididas** por el humano: D1-D4 (2026-10-23,
«sí a las cuatro», `features.json`) y el aviso de las quitadas (2026-10-24,
R17). **D5-D16 abiertas** (§10, rec. A). Evidencia: `progress/explore_F-062_
sigrid.md` (fila n = E-n). 2026: 1-oct jueves, 31-oct sábado, 1-nov domingo.
## 1. Qué se conserva de F-030 y qué se reemplaza («→», números de esta spec)
- **Se conservan de F-030**: catálogo y captura (R3-R16; el chip «del al» no
  cambia), PUT y validación (R17-R19), fuera del 100 % (R22), la línea (R24:
  `can = tot = 0`, `pre`, cuenta, `synckey porcentajes:inc:{id}:ini|fin`),
  R25, R26, R28, R29, R39, R48, D12-D14, D16 y **ningún `DELETE`**.
- **Se reemplazan de F-030**: D3 y el «un `CIZ` por mes» de R24 → R1-R11; R27,
  R44 y D15 → R1, R9; «nunca un inicio sin su fin» → R7; R30 y R40-R42, que
  se amplían a `CIZ` ajenos → R14-R16; R33 → R19 (ventana); D11 y R38 (la
  quitada se lista con lo que guarda la api) → R17 (aviso contra Sigrid).
## 2. Definiciones
- **Propia** de una incidencia: la línea de su `synckey` o del `hmores.ide` de
  su traza (F-030 R39; R15). **Ajena**: otra `CI*`/`CIZ` del recurso
  (Administración, `partes` u otra incidencia nuestra), en cualquier parte.
- **Racha** `[D5]`: un inicio `CI*` y su `CIZ`; por (`fec`, inicio antes que
  `CIZ`, `ide`), cada `CIZ` cierra el inicio abierto más reciente; sin él,
  **abierta**. **Pegado** `[D2]`: `d` a `c < d` si entre ambos solo hay
  sábados y domingos (o nada; festivos no, F-059). **Llega a fin de mes**
  `[D7]`: tras su último día solo quedan sábados y domingos, o nada.
- **Cadena**: incidencias del recurso y código en el mes, cada una pegada a
  la anterior, también de obras distintas `[D11]`; **dueña**, la primera. Una
  con línea propia no se une a la anterior (R11). Una suelta es una cadena.
## 3. Decidir la racha (transfer)
- **R1.** CUANDO se registra una cadena del `d` al `h` del mes M, el transfer
  busca en lo leído (R19), sin las propias de la cadena y con sus `CIZ`
  ajenos movidos en su día original (R15), una **previa** del mismo código
  con inicio ≤ `d`: (a) abierta con inicio en M; (b) abierta con inicio
  anterior a M y `d` pegado al último día de M−1 (D4); o (c) con su `CIZ` en
  M, en `d` o después o pegado a `d`. De varias, la de inicio más reciente.
- **R2.** SI no hay previa, ENTONCES **abre**: inicio en `d` en el parte del
  periodo de la obra de la dueña (`[D3]`, [`#regla-analitica`]). **R3.** SI
  hay previa, ENTONCES la **continúa** sin inicio, sea de quien sea (`[D1]`).
- **R4.** MIENTRAS no llega a fin de mes, se cierra en `h`: con previa (c), su
  `CIZ` se **mueve** a `h` (R14), salvo un ajeno ya en `h` o después (una
  ajena nunca se acorta: «cubierta»); si no, se escribe un `CIZ` en `h`.
- **R5.** El `CIZ` escrito va al parte del inicio si es de M, En registro, de
  la empresa y (pruebas) de la obra de pruebas, con la obra, centro, partida
  y cuenta del inicio (E-6, E-13); si no, al de la obra de la dueña, como R2.
- **R6.** Lo escrito lleva la `synckey` de la dueña; un `CIZ` ajeno movido,
  la suya (`[D1]`, [`#regla-cero`]). **R7.** CUANDO la cadena llega a fin de
  mes (`[D4]`, `[D7]`), no hay `CIZ`: queda **abierta** hasta R1 b o R12.
- **R8.** Códigos distintos, rachas distintas; las no dueñas de una cadena
  no escriben: «continúa (cadena de la incidencia N)».
- **R9.** `[D13]` SI en [`d`, `h`] hay una línea ajena que no es de la previa
  (otro código u otro inicio del mismo), ENTONCES la cadena no escribe ni
  mueve nada: `omitir` «en el tramo ya está la línea X (código, día) de Y».
- **R10.** `[D8]` SI el `CIZ` de la racha pegada es de M−1 o no se puede mover
  (parte no En registro, enlaces, fuera de la obra de pruebas), ENTONCES no es
  previa: la cadena abre otra (R2) y avisa con el parte y día de ese `CIZ`.
- **R11.** `[D9]` SI continuar o unir exigiría quitar una línea escrita,
  ENTONCES no se quita ni se une: una con inicio propio sigue abriendo su
  racha (F-030 R30); un `CIZ` de la racha ya en M (propio o de la previa), si
  ahora llega a fin de mes, va al último día; aviso «no se une: X ya está».
## 4. Cierre del mes anterior (D4)
- **R12.** CUANDO se registra el mes M de un recurso designado (R24), por cada
  racha suya abierta con inicio en M−1 que ninguna incidencia de M continúa
  (R1 b), se escribe un `CIZ` el último día de M−1 en el parte del inicio
  (como R5), con `synckey` `porcentajes:inc:{id}:fin` si el inicio es nuestro
  y `porcentajes:inc:cierre:{ide del inicio}` si es ajeno.
- **R13.** SI ese parte no está En registro, es de otra empresa o (pruebas) de
  otra obra, o `[D14]` la racha empieza antes de M−1 (un `CIZ` de M−1 no cabe
  en un parte de otro mes), ENTONCES nada se escribe y el preflight avisa.
## 5. Cambiar, quitar, idempotencia y «no coincide con Sigrid»
- **R14.** Mover un `CIZ` o editar una propia es el `UPDATE` de solo la `fec`
  de F-030 (R41, D16): mismo `ide` y recurso, su código, `can` y `synckey`
  leídos, sin enlaces, parte En registro y `fec` leída; nunca `DELETE` ni
  `INSERT` en su lugar. `[D12]` Un ajeno, con su `can` (0 o 1, E-1); uno
  propio, con 0 (F-030 D14). `ejecutar` relee lo que mueve; SI una de una
  cadena ya no cumple, ENTONCES no se mueve ninguna de ella (F-030 R45).
- **R15.** La primera vez que mueve un `CIZ` ajeno, la api guarda en la dueña
  su `ide` y su día original (`sigrid_dia_fin_antes`) y los manda con ella.
- **R16.** CUANDO cambian los días de una cadena, se decide de nuevo (R1-R11):
  lo propio se edita (F-030 R30), el ajeno va a su día nuevo y, si ya no lo
  continúa, **se devuelve** al original (rol `devolver`, `[D10]`).
- **R17.** (humano, 2026-10-24) La quitada en la plataforma queda `quitada`
  (tachada) y viaja con su traza en `quitadas`, en la petición de su obra.
  CUANDO se registra, el transfer busca sus líneas por `ide` (R19): `[D10]` el
  `CIZ` ajeno que movió se devuelve con R14; cada línea propia que sigue en
  Sigrid sale en `no_coincide` («quitada en la plataforma; sigue en Sigrid»:
  código, día, parte, `ide`) para editarla a mano, sin escribir `[D16]`. Sin
  ninguna en Sigrid, la api la borra.
- **R18.** Repetir sin cambios no escribe ni mueve nada (`ya_registrado` o
  «cubierta»), sin depender de la `synckey` de un `CIZ` ajeno.
- **R30.** `[D15]` CUANDO se registra un recurso designado, sus `CI*`/`CIZ` de
  M que no son propias de ninguna incidencia ni quitada del mes, ni de una
  previa que continúa una cadena, salen en `no_coincide` («en Sigrid y no en
  la plataforma»), agrupadas por racha, sin escribir ni leer nada más (R19).
## 6. Lecturas y coste
- **R19.** `[D6]` Las `CI*`/`CIZ` se leen en **una** lectura por petición o por
  lote (trozos de 500 recursos), del día 1 de M−12 (`INCIDENCIAS_MESES_ATRAS`)
  al último de M+1, de los recursos de las incidencias y de los designados,
  más las de las trazas (también de las quitadas) por `ide`; en pruebas,
  solo de la obra de pruebas. SI falla o viene `truncated`, ENTONCES nada.
- **R20.** En el lote (F-055) va en la ronda C; el preflight del mes hace como
  mucho **una** lectura más que hoy y, medido como F-055 T18, no sube > 15 %.
- **R21.** SI la racha tiene `CIZ` en M+1 y la cadena ya no llega a fin de
  mes, ENTONCES no se escribe el `CIZ` y se avisa «la racha sigue en MM».
## 7. Contrato, api y front
- **R22.** Preflight y `ejecutar` devuelven `rachas` (por incidencia: id,
  `papel` `abre`|`continua`, inicio, `cierre` `cierra`|`abierta`|`cubierta`|
  `cadena` con día y parte, dueña, avisos), `cierres_racha` (R12-R13) y
  `no_coincide` (R17, R30: tipo `quitada`|`solo_sigrid`, recurso, incidencia
  o nulo, líneas, motivo). Las líneas, en `incidencias` (F-030 R31), con
  `rol` `ini`|`fin`|`devolver` y las acciones nuevas `continua`, `abierta`.
- **R23.** Traza: la que solo continúa o queda abierta es `registrado` sin
  `ide`; un `cierres_racha` con incidencia va al rol `fin` de esa (de M−1).
- **R24.** La api añade a cada petición `incidencias_mes` (las del mes de sus
  recursos en cualquier obra, con obra y traza, sin quitadas), `quitadas`
  (R17) y `cierres_recursos` (los recursos cuya primera petición, en el
  orden de hoy y tras el filtro `obra_ide`, es esa). Vacías, no van.
- **R25.** El modal pinta por incidencia «abre», «continúa la del dd/mm (parte
  X)», «cierra el dd/mm en Y» o «queda abierta», «Cierres de rachas» y el
  bloque «No coincide con Sigrid» (sustituye a la lista de quitadas de F-030
  R38), sin confirmar; el front lo toma de la respuesta, sin calcular.
- **R26.** Las líneas de % se deciden como hoy (F-030 R2): las `M*` no cambian.
## 8. Documentación y verificación
- **R27.** [`#regla-incidencia`] se reescribe con R1-R26 y R30 (fuente única,
  `test_f002`) e `INTEGRACION.md` §5 y su tabla; el líder actualiza
  `azure-apps/dedicacion.md` y prepara el aviso a `partes` (lo da el humano).
- **R28.** Tests sin red ni BBDD con §9. **R29.** MANUAL en la `0404` (T20).
## 9. Casos de test
C1-C11, uno por línea en `tasks.md` §«Casos», cada uno con el R que fija: los
ejemplos del humano (5-9 oct; 5-9 y 13-16; 27-oct a 6-nov; 27-31 sin
continuación; baja 15-sep a 10-nov; dos obras 40/60), E-12 y E-15, quitar
(C9, C10) y lo que solo está en Sigrid (C11). En todos, las `M*` igual (R26).
## 10. Preguntas al humano (D5-D16; recomendada A)
- **D5 · Emparejar `CIZ`** (sin código). **A**: el inicio abierto más
  reciente. B: el más antiguo. **D6 · Ventana.** **A**: 12 meses atrás,
  configurable, y M+1 para avisar (R21). B: 6 meses. C: sin tope.
- **D7 · Fin de mes en fin de semana.** **A**: cuenta (C4). B: solo el último
  día. **D8 · Pegada con `CIZ` de M−1.** **A**: abre otra, avisa (E-12). B: no.
- **D9 · Habría que quitar una escrita.** **A**: no se une, avisa (R11). B:
  omitirla. **D10 · Quitar o recortar una que movió un `CIZ` ajeno.** **A**:
  se le devuelve su día con `UPDATE` (R16, R17). B: solo el aviso.
- **D11 · Pegadas del mismo código en obras distintas.** **A**: una cadena en
  la obra de la primera (R24, sin copiar D2 en la api). B: 422 en el PUT.
- **D12 · `CIZ` ajeno con `can = 1`.** **A**: se mueve (solo `fec`). B: no.
  **D13 · Ajena en el tramo.** **A**: `omitir` (R9). B: se escribe.
- **D14 · Abierta desde antes de M−1, sin continuar.** **A**: solo aviso
  (R13). B: `CIZ` en un parte de M−1 de la obra del inicio.
- **D15 · `CI*` en Sigrid y no en la plataforma.** **A**: también en
  `no_coincide`, solo de los designados y sin escribir (R30). B: no se avisa.
- **D16 · Más edición al quitar.** **A**: solo `devolver` (R17) y aviso. B:
  quitada la dueña de una cadena, su inicio pasa al día de la siguiente.
