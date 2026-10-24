<!-- specs/F-054-sync-trae-porcentajes/requirements.md -->
# F-054 · Traer de Sigrid los % que se elijan; al registrar, obra sin nada = 0 %

Rigor **`critico`**, los tres servicios (design §1). **Parte A** (§1-§3): al
sincronizar, el transfer lee Sigrid y traduce, y la api escribe en
`dedicacion` **solo las líneas que el usuario acepta**; en Sigrid, solo
lectura. **Parte B** (§5): al registrar, una obra que la plataforma no le da
al trabajador es un 0 %; si Sigrid tiene ahí una línea suya, se pregunta si
se pone a 0, **editándola**. Pedida el 2026-10-08, precisada el 2026-10-24
(§6). Ejemplo: el caso de la 0694, 2026-09 (una `MADM` al 95 % a mano, sin
`synckey`, que salió como sobrecarga). Fuera: incidencias (D9), F-044, `partes`.

Lecturas del líder (2026-10-23, mensuales desde 2025): las `M*` suman el
100 % por recurso y mes «en 730 de 756 meses con incidencia»; la `M*` lleva
`fec` = último día del mes en el 94 %; las `CI*`/`CIZ` tienen `can = tot = 0`.
**Línea mensual**: `hmores` `M*` con `can` ≠ 0 en un parte de trabajo de obra.
**Entrada**: obra + modo (normal, `Postv-X`, `VAR-NN`). **Sobrante**: línea
mensual de un recurso del registro en una entrada que la plataforma no le da.

## 1. Disparador y lectura (A) `[D1, D2, D6, D7]`

- **R1.** CUANDO el sync de maestros termina con éxito, el front pide `POST
  /api/v1/periodos/{anio}/{mes}/traer-sigrid` del periodo abierto, con la
  empresa elegida y sin `aceptar`; SI el sync falla, no se pide.
- **R2.** Periodo inexistente ⇒ 404; `CERRADO` ⇒ 409; sin llamar al transfer.
- **R3.** SI una lectura de Sigrid falla o viene `truncated`, ENTONCES
  transfer y api responden 502 con el motivo, sin tocar la base.
- **R4.** **Una** lectura de las líneas mensuales de los partes de trabajo
  de obra (`con.tip` del ajuste, `hmo.reside` 0) del periodo (`hmo.ano`,
  `mes`) en obras de la empresa pedida; cualquier `fec`, `synckey` y estado.
- **R5.** Las de la obra de pruebas (`OBRA_PRUEBAS_COD`) solo se cuentan.
- **R6.** Cada línea publica `hmores_ide`, recurso, obra, parte (`ide`,
  código, estado, `en_registro`), hora, `can`, `fec`, partida y `synckey`.
- **R7.** El endpoint de la parte A nunca escribe en Sigrid.

## 2. Traducción (transfer) y comparación (api) `[D3, D10, D11]`

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
  con motivo. Las de recursos fuera del maestro, solo `fuera_maestro`.
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
  línea (la actualiza en su sitio o la crea); las otras y su traza no cambian.
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
  `SIGRID` por petición, con su `X-Usuario`; deshacerlo (`#regla-deshacer`)
  devuelve solo las entradas que esa aceptación cambió.
- **R26.** Tras aceptar, se encolan las propuestas de los escritos.

## 4. Resultado, front y documentación

- **R27.** La respuesta da, por trabajador, sus entradas con estado, % de
  los dos lados, parte y motivo; y `aceptadas`, `no_traidas`,
  `fuera_maestro`, `lineas_leidas`, `excluidas_pruebas` y motivos de catálogo.
- **R28.** El front enseña el resumen y una ventana por trabajador con una
  casilla por entrada `distinta` (sale desmarcada) o `solo_sigrid` (sale
  **marcada**, desmarcable) y «Aceptar las marcadas», que repite la petición
  con `aceptar` y recarga. No compara ni decide.
- **R29.** `ARCHITECTURE.md`: `#regla-traer-sigrid` (A), `#regla-obra-cero`
  (B) y la tabla de acceso; `INTEGRACION.md` §1, §5 y §7 (transfer → api →
  front); `azure-apps/dedicacion.md` al desplegar; `test_f002_fuente_unica`.
- **R30.** MANUAL (humano): A en local con septiembre 2026, solo lectura; B
  en modo pruebas sobre la 0404 (tasks T18, T19).

## 5. Parte B · Al registrar, obra sin nada = 0 % `[D13-D15]`

- **R31.** CUANDO se pide el preflight del periodo o de un trabajador (no el
  de una obra sola), el transfer lee en **una** lectura más, en la primera
  ronda paralela del lote, las líneas mensuales del periodo de los recursos
  del lote (la de R4, por recurso) y marca **sobrante** la que no cubre
  ninguna línea de su recurso: normal, si no tiene esa obra; postventa, si
  ningún `Postv-` suyo casa con esa partida; VAR, si ninguna entrada suya es
  esa partida. `[D14]` Solo recursos con alguna línea en la petición.
- **R32.** En modo pruebas solo cuentan las de la obra de pruebas, cubiertas
  si una acción del recurso la reconoce (ya registrada, choque) o tiene su partida.
- **R33.** Cada sobrante es un conflicto `a_cero`, **uno por línea**
  (`hmores_ide`, obra, parte, hora, partida, `can`, `synckey`), que se
  confirma por línea, aparte de los demás; sin confirmar no se toca.
- **R34.** SI está en un parte cerrado o su `synckey` es de otro sistema
  `[D15]`, ENTONCES es un aviso, sin confirmación ni escritura. Una nuestra
  de una asignación que ya no existe es sobrante como una de Administración.
- **R35.** CUANDO se confirma, `ejecutar` la pone a 0 **antes** de las demás
  escrituras, editándola en su sitio (`can` y `tot` a 0) con la relectura y
  la guarda de `#regla-cero` (recurso, `M*`, `can` y `synckey` del preflight,
  sin enlaces, En registro, en pruebas solo la 0404); la que ya no cumple va
  a `omitidas`. Ningún `DELETE`; log antes/después; `a_cero` en la respuesta.
- **R36.** Capacidad (`#regla-capacidad`): en el preflight una sobrante suma
  como cualquier línea del parte (solo pasa en la obra de postventa, la VAR o
  la de pruebas); en `ejecutar` no suman las ya puestas a 0. El 100 % no cambia.
- **R37.** Coste: el preflight del mes no sube más de un 15 % sobre el
  medido antes de B (método de F-055 T18). Sync y propuestas, sin lecturas.

## 6. Decisiones: todas DECIDIDAS por el humano el 2026-10-24

Primera tanda («al sincronizar, puedo querer trarme algunas laineas(obras)
de sigrid y otras no. si acepto en la plataforma piso solo esas lineas del
trabjador. al registrar, si el trabajador no tiene nada en una obra es como
un 0%. si en sigrid si tiene debe preguntar si lo pisa (y lo deja a 0) o
no»): **D4** = aceptar por entrada (R19-R22; sustituye a «solo los
trabajadores sin líneas» y a `sustituir: [ide]`) y **parte B** (R31-R36).
**D9** = A, vía el líder. Segunda tanda («d12, con la casilla marcada por
defecto, aunque se puede desmarcar. d13, metelo aqui. ok a lo demas»):

1. **D1 = A.** Tras «Sincronizar Sigrid», el periodo abierto (R1).
2. **D2 = A.** Las mensuales, nuestras y manuales (R4).
3. **D3 = A.** R8-R17: partida del parte como elegida; lo no ofrecible no.
4. **D5 = A.** La aceptada guarda el `hmores.ide` (R23).
5. **D6 = A.** Los partes cerrados cuentan, con su estado (R4, R6).
6. **D7 = A.** Mes cerrado en la app ⇒ 409 sin leer (R2).
7. **D8 = A.** Un evento por trabajador y petición (R25).
8. **D10 = A.** Se suman; con partidas distintas, `no_traducible` (R15).
9. **D11 = A.** Trabajadores visibles en la empresa y vigentes (R14).
10. **D12.** Las `solo_sigrid` se eligen con su casilla, **marcada por
    defecto** y desmarcable; las `distinta`, **desmarcadas** (el humano solo
    lo dijo de las `solo_sigrid`). Nada entra sin «Aceptar las marcadas».
11. **D13 = B.** La parte B se queda en F-054, con su MANUAL en modo pruebas
    sobre la 0404 (T19); rigor crítico.
12. **D14 = A.** Un trabajador sin líneas en la plataforma no se revisa (R31).
13. **D15 = A.** `synckey` de otro sistema ⇒ aviso sin escribir (R34).
