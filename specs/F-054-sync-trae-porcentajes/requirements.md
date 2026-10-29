<!-- specs/F-054-sync-trae-porcentajes/requirements.md -->
# F-054 · Traer de Sigrid los % que se elijan; al registrar, obra sin nada = 0 %

Rigor **`critico`**, los tres servicios (design §1). **A** (§1-§3): al
sincronizar, el transfer lee y traduce y la api escribe en `dedicacion`
**solo lo que el usuario acepta**; en Sigrid, solo lectura. **B** (§5): al
registrar, una obra que la plataforma no le da es un 0 % y, si Sigrid tiene
ahí una línea suya, se pregunta si se pone a 0, **editándola**. Pedida el
2026-10-08, precisada el 2026-10-24, **revisada el 2026-10-29** contra F-044,
F-062 y F-068 (D16-D18). Caso: la 0694, 2026-09 (`MADM` al 95 % a mano, sin
`synckey`: sobrecarga). Fuera: incidencias `CI*`/`CIZ` (D9) y `partes`.

Lecturas del líder (2026-10-23): design §11. **Línea mensual**: `hmores`
`M*` con `can` ≠ 0 en un parte de trabajo de obra. **Entrada**: obra + modo
(normal, `Postv-X`, `VAR-NN`). **Sobrante**: línea de un recurso del registro
en una entrada que la plataforma no le da. **Vinculado** y **titular**: los
de F-044 (`#regla-vinculado`); una `MESVE` empieza por `M` y es de vinculado.

## 1. Disparador y lectura (A) `[D1, D2, D6, D7]`

- **R1.** CUANDO el sync de maestros termina con éxito, el front pide `POST
  /api/v1/periodos/{anio}/{mes}/traer-sigrid` del periodo abierto, con la
  empresa elegida y sin `aceptar`; SI el sync falla, no se pide.
- **R2.** Periodo inexistente ⇒ 404; `CERRADO` ⇒ 409; sin llamar al transfer.
- **R3.** SI una lectura de Sigrid falla o viene `truncated`, ENTONCES
  transfer y api responden 502 con el motivo, sin tocar la base.
- **R4.** **Una** lectura de las líneas mensuales de los partes de trabajo
  de obra (`con.tip` del ajuste, `hmo.reside` 0) del periodo en obras de la
  empresa pedida; cualquier `fec`, `synckey`, estado y recurso: quién es
  trabajador lo decide la api **por recurso** (R14).
- **R5.** Las de la obra de pruebas (`OBRA_PRUEBAS_COD`) solo se cuentan.
- **R6.** Cada línea publica `hmores_ide`, recurso, obra, parte (`ide`,
  código, estado, `en_registro`), hora, `can`, `fec`, partida y `synckey`.
  **R7.** El endpoint de la parte A nunca escribe en Sigrid.

## 2. Traducción (transfer) y comparación (api) `[D3, D10, D11, D18]`

- **R8.** Obra normal: `destino = normal`. **R9.** Obra de postventa:
  `destino = postventa` y la **única** obra, de las que manda la api, cuyo
  `casar_postventa` (`#regla-p5`) da su partida; ninguna o varias ⇒ motivo.
- **R10.** Obra VAR: `var_paride` si `partida_var_de` (`#regla-var`) la
  acepta; si no, motivo. **R11.** Los catálogos de postventa y VAR se leen
  solo si alguna línea es de esa obra. **R12.** Son las funciones del
  preflight: lo traído se registra en la partida de la que vino.
- **R13.** La api agrupa por trabajador (`recurso_ide`) y entrada: normal =
  la obra; postventa = (obra de origen, postventa); VAR = `obra.ide` −`var_paride`.
- **R14.** Va a `no_traidas`, con su motivo, la línea de un trabajador no
  visible en la empresa o no vigente, la de una entrada que no está en la
  base, es de otra empresa o no es ofrecible, y la que el transfer devolvió
  con motivo. La de un recurso de `recurso_vinculado` (una `MESVE`) solo
  cuenta en `de_vinculados`: nunca es asignación ni subfila `[D18]`. Las
  demás de recursos fuera del maestro, solo `fuera_maestro`.
- **R15.** Las líneas de un trabajador en una entrada se suman; con partidas
  distintas (normal), la entrada es `no_traducible`.
- **R16.** % = suma de `can` × 100 a centésimas; ≤ 0 o > 100 ⇒ `no_traducible`.
- **R17.** Partida: normal, la de sus líneas como **elegida** (0 ⇒
  automática); postventa, automática; VAR, la fija. Sin propuesta guardada.
- **R18.** Cada entrada sale con su estado: `igual` (% con la épsilon 0,005
  de `domain/estados.py`; la partida no cuenta), `distinta`, `solo_sigrid`,
  `solo_cuadrante` o `no_traducible`. Sin `aceptar`, nada se escribe.

## 3. Aceptar línea a línea (A) `[D4, D5, D8, D12]`

- **R19.** CUANDO la petición trae `aceptar: [{trabajador_ide, obra_ide,
  es_postventa}]`, cada aceptada `distinta` o `solo_sigrid` pisa **solo esa**
  línea (en su sitio, con su `id` y sus subfilas de vinculado, o la crea);
  las otras, sus subfilas y su traza no cambian.
- **R20.** SI la aceptada está en otro estado, ENTONCES no se toca y vuelve
  con su motivo. Las `solo_cuadrante` no se aceptan: las escribe el registro.
- **R21.** `[D12]` Las `solo_sigrid`, también las de un trabajador sin
  líneas, se eligen igual: nada entra sin pasar por «Aceptar las marcadas».
- **R22.** Una transacción; aceptar dos veces lo mismo no cambia nada.
- **R23.** `[D5]` La aceptada guarda `sigrid_hmores_ide` (el menor `ide` de
  sus líneas), `sigrid_parte_cod`, `sigrid_estado = registrado` y el motivo
  «traída de Sigrid»: al registrar es **ya registrada** (`#regla-cero`).
- **R24.** Si luego se guarda la fila, pierde la traza y el registro pide un
  pisado que **edita** la línea de Sigrid (regla de hoy): nunca un duplicado.
- **R25.** `[D8]` Cada trabajador con alguna aceptada deja **un** evento
  `SIGRID` por petición, con su `X-Usuario` y el snapshot de líneas con sus
  subfilas (como `PARTIDA_VINCULADO`); deshacerlo (`#regla-deshacer`)
  devuelve solo las entradas que esa aceptación cambió.
- **R26.** Tras aceptar, se encolan las propuestas de los escritos.

## 4. Resultado, front y documentación

- **R27.** Por trabajador, sus entradas con estado, % de los dos lados, parte
  y motivo; y `aceptadas`, `no_traidas`, `fuera_maestro`, `de_vinculados`,
  `lineas_leidas`, `excluidas_pruebas` y motivos de catálogo.
- **R28.** El front enseña el resumen y una ventana por trabajador con una
  casilla por entrada `distinta` (sale desmarcada) o `solo_sigrid` (sale
  **marcada**, desmarcable) y «Aceptar las marcadas», que repite la petición
  con `aceptar` y recarga. No compara ni decide.
- **R29.** `ARCHITECTURE.md` puntos 23 `#regla-traer-sigrid` y 24
  `#regla-obra-cero` (remitidos desde `#regla-vinculado`), tabla de acceso,
  `ANCLAS`; `INTEGRACION.md` §1, §5, §7; `azure-apps` al desplegar.
- **R30.** MANUAL: A en local, 2026-09, solo lectura (T18); B en pruebas (T19).

## 5. Parte B · Al registrar, obra sin nada = 0 % `[D13-D17]`

- **R31.** CUANDO se pide el preflight del periodo o de un trabajador (no el
  de una obra sola), el transfer lee en **una** lectura más, en la ronda A
  de `precargar`, las líneas mensuales del periodo de los trabajadores del
  lote (R4 por recurso: la `MESVE` de un vinculado no entra); **sobrante**,
  la que no cubre ninguna acción de su recurso en cualquier estado: normal,
  sin esa obra; postventa, si ningún `Postv-` suyo casa con esa partida;
  VAR, si ninguna entrada suya es esa partida. `[D14]` Solo trabajadores
  con alguna línea de %.
- **R32.** En pruebas solo cuentan las de la obra de pruebas: cubierta si una
  acción del recurso la reconoce (ya registrada, choque, al 0) o es su partida.
- **R33.** Cada sobrante es un conflicto `a_cero`, **uno por línea**
  (`hmores_ide`, obra, parte, hora, partida, `can`, `synckey`), que se
  confirma por línea, aparte; sin confirmar no se toca. `[D17]` Desmarcada.
- **R34.** SI está en un parte cerrado o su `synckey` es de otro sistema
  `[D15]`, ENTONCES es un aviso sin escritura. Una nuestra huérfana, sobrante.
- **R35.** CUANDO se confirma, la api pide al transfer ponerla a 0 **antes**
  de las escrituras por obra, en su sitio (`can` y `tot` a 0), con la
  relectura y la guarda de `#regla-cero` (recurso, hora, `can` y `synckey`
  del preflight, sin enlaces, En registro, en pruebas solo la 0404); la que
  no cumple, omitida con motivo. Sin `DELETE`; log antes/después; aparte
  del `a_cero` por obra de F-051.
- **R36.** `#regla-capacidad`: en el preflight una sobrante suma como otra
  línea del parte (postventa, VAR o pruebas); `ejecutar` relee tras ponerlas
  a 0: la puesta a 0 no suma y la omitida sí. El 100 % no cambia.
- **R37.** Coste: el preflight del mes no sube más de un 15 % sobre el
  medido antes de B (método de F-055 T18). Sync y propuestas, sin lecturas.
- **R38.** `[D16]` *(si D16 = C)* Con vinculados en la petición, otra
  lectura en la ronda A: sus líneas de **cualquier** hora con `can` ≠ 0 del
  periodo; sobrante si ninguna acción de **ese** vinculado la cubre
  (R31-R32), y R33-R35 con **su** hora en la guarda (F-044 R24).

## 6. Decisiones

**Cerradas por el humano el 2026-10-24**: «al sincronizar, puedo querer
trarme algunas laineas(obras) de sigrid y otras no. si acepto en la
plataforma piso solo esas lineas del trabjador. al registrar, si el
trabajador no tiene nada en una obra es como un 0%. si en sigrid si tiene
debe preguntar si lo pisa (y lo deja a 0) o no» ⇒ **D4** por entrada y
**parte B**; **D9** = A; «d12, con la casilla marcada por defecto, aunque se
puede desmarcar. d13, metelo aqui. ok a lo demas» ⇒ **D12** (`solo_sigrid`
marcadas, `distinta` desmarcadas), **D13 = B** (T19) y **D1-D3, D5-D8, D10,
D11, D14, D15 = A**.

**NUEVAS, pendientes del humano (2026-10-29)**; motivos en design §12:

- **D16.** Líneas de los vinculados en una obra sobrante: A) fuera; B) aviso
  sin escritura; **C) como las del trabajador (R38)**. *Recomendada C.*
- **D17.** Casilla de la sobrante: **A) desmarcada siempre** (R33); B) la de
  un vinculado, marcada si su titular tiene sobrante ahí. *Recomendada A.*
- **D18.** Parte A y vinculados: **A) no se trae nada de ellos** (R14); B)
  la partida de su línea, como elegida de su subfila. *Recomendada A.*
