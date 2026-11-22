<!-- specs/F-074-partida-sin-automatica/requirements.md -->
# F-074 · La partida no se queda en «automática»

Rigor **`critico`**; toca **transfer** (una marca en el preflight), **api**
(estados de la celda, postventa, memoria) y **front** (textos); design §1.
Petición de negocio del 2026-11-22: «O sale la que se va a encontrar después
o sale que no encuentra y que se ponga, pero dejarlo para luego no tiene
sentido». Decisiones `[Dn]`: design §12, abiertas. Diagnóstico de los casos
en que hoy queda «automática»: design §2.

Fuera de alcance: la regla de la propuesta (`#regla-partida`,
`#regla-vinculado`, `#regla-p5`, `#regla-var` no cambian), la Regla C
(`#regla-sin-partida`, sigue igual al registrar), el Excel, el orden y los
triggers de la cola (F-055 R29-R33), un contador de líneas sin partida.

Glosario (el de F-050 y F-055): **elegida**, **propuesta guardada**,
**pendiente** (en la cola de F-055/F-057), **memoria «sin propuesta»** (F-055
R32: la línea o subfila cuya petición devolvió propuesta nula o su obra
`{ok: false}`), **no encontrada** = automática en esa memoria.

## 1. Qué enseña la celda Partida (front, pinta lo que manda la api)

- **R1.** La celda Partida de una línea o de una subfila debe enseñar lo
  primero que aplique: (1) la elegida; (2) la fija (VAR); (3) la propuesta
  (guardada o, en postventa, la de su obra, R11-R12) en cursiva con su
  método; (4) «buscando partida…» si la api la marca pendiente; (5) «no
  encuentra partida» si la api la marca no encontrada; (6) «sin calcular»
  con el periodo ABIERTO; (7) «—» con el periodo no ABIERTO. Ninguna celda
  dice «automática». (capa: unit)
- **R2.** `[D1][D6]` «no encuentra partida» se pinta como aviso (clase
  `partida-sin`, color de aviso, sin cursiva) con el título «El registro no
  encuentra partida: elige una»; con el periodo ABIERTO, el clic abre el
  selector como cualquier celda (F-050 R25). (capa: unit)
- **R3.** El front no decide el estado: lo toma de `propuesta_*`,
  `propuesta_pendiente` y `propuesta_no_encontrada` de la api; solo
  `periodoEstado` separa (6) de (7). (capa: unit)
- **R4.** El filtro «Partida» y el buscador libre deben casar con el texto
  que enseña la celda (también la propuesta y los textos de R1), línea a
  línea y, si se ven (F-067), subfila a subfila. (capa: unit)
- **R5.** `[D5]` La opción «automática (la propone el registro)» del
  selector pasa a «sin elegir · usar la propuesta» si la respuesta del
  selector trae propuesta y a «sin elegir · no encuentra partida» si no;
  sigue borrando la elegida (F-050 R13). (capa: unit)

## 2. Línea de obra normal (api)

- **R6.** Una línea de obra normal sin elegida ni propuesta guardada que
  está en la memoria «sin propuesta» debe publicar `propuesta_no_encontrada:
  true` en el cuadrante, en la respuesta de cada escritura que hoy publica
  `propuesta_pendiente` (F-057) y en `GET …/propuestas` (lista
  `no_encontradas: [{trabajador_ide, obra_ide, es_postventa}]`). (capa: unit)
- **R7.** La marca sale de la **misma** lectura de la cola que `pendientes`
  y `en_curso` (F-057); una línea pendiente, con elegida o con propuesta no
  la lleva. (capa: unit)
- **R8.** Sin marca, la clave `propuesta_no_encontrada` no sale (la línea de
  siempre), y `GET …/propuestas` no gana `no_encontradas` si está vacía.
  (capa: unit)

## 3. Subfilas de vinculados (api)

- **R9.** Una subfila sin elegida ni propuesta guardada debe publicar
  `propuesta_pendiente: true` si está en la cola de subfilas y
  `propuesta_no_encontrada: true` si está en su memoria «sin propuesta» (hoy
  dice «automática» en los dos casos). `GET …/propuestas` gana
  `subfilas_pendientes` y `subfilas_no_encontradas`
  (`[{trabajador_ide, obra_ide, es_postventa, vinculado_ide}]`), solo con
  alguna; las claves de la subfila, solo con valor (R8). (capa: unit)
- **R10.** CUANDO la api borra la propuesta guardada de las subfilas de una
  línea porque cambia la partida de su titular (`CambiarPartida` sin
  `vinculado_ide`, F-044 R9), debe sacar esas subfilas de su memoria «sin
  propuesta» **antes** de encolar, para que se recalculen con la partida
  nueva del titular (hoy se quedan fuera hasta el próximo sync). (capa: unit)

## 4. Postventa (api)

- **R11.** `[D2]` El sync debe guardar en cada obra la partida de postventa
  con la que casa en el universo (`POST /api/postventa/universo`,
  `obras[].partida`: `ide`, `cod`, `res`) y dejarla nula si la obra no está
  en el universo; con **la misma** llamada de hoy, sin lecturas nuevas.
  (capa: unit)
- **R12.** Una línea de postventa sin elegida debe publicar como propuesta
  (`propuesta_cod`, `_res`, `propuesta_metodo: "postventa"`) la partida de
  postventa de su obra. SI la obra no admite postventa, ENTONCES
  `propuesta_no_encontrada: true`. SI la admite y aún no tiene partida
  guardada (sync pendiente tras desplegar), ENTONCES ninguna marca («sin
  calcular»). (capa: unit)
- **R13.** Esa partida solo se enseña: no se guarda en `asignacion.propuesta_*`
  ni viaja al registro; el preflight la vuelve a casar con `casar_postventa`
  (`#regla-p5`), la función del universo. (capa: unit)

## 5. La propuesta que deja de valer antes de registrar

- **R14.** CUANDO una línea o subfila llega al preflight con una propuesta
  guardada de método propio que no vale (F-055 R6; F-068 R16), el transfer
  debe publicar en su acción `propuesta_descartada` con el código de la
  guardada (o `partida N` sin código); en el resto, nula. La partida de la
  acción sigue la regla de hoy (nueva propuesta, o sin partida con su
  conflicto de la Regla C). (capa: unit)
- **R15.** `[D4]` El modal de registro debe enseñar, en la acción con
  `propuesta_descartada`, «la del cuadrante (X) ya no vale» junto a la
  partida que se escribiría. (capa: unit)
- **R16.** CUANDO el preflight devuelve `propuesta_descartada` y la acción
  no trae una propuesta nueva, la api debe borrar la propuesta guardada de
  esa línea o subfila si sigue sin elegida (sin evento); con propuesta
  nueva, la guarda como hoy (F-055 R14). (capa: unit)

## 6. Coste y reintento

- **R17.** F-074 no debe añadir lecturas a Sigrid: el cuadrante, la cola en
  segundo plano, el sync y el preflight leen lo mismo que hoy (se cuentan
  en los dobles del cliente), salvo el recálculo de las subfilas de R10.
  (capa: unit)
- **R18.** `[D3]` Una no encontrada no se reintenta en segundo plano hasta
  el próximo sync con éxito o un reinicio (F-055 R32, sin cambio), salvo
  R10; al registrar, el preflight la vuelve a buscar (F-055 R7) y, si la
  encuentra, se escribe y se guarda (F-055 R14). (capa: unit)

## 7. Documentación

- **R19.** `docs/ARCHITECTURE.md#regla-partida` dice los estados de la celda
  (R1), la postventa (R11-R13) y la propuesta descartada (R14-R16);
  `docs/INTEGRACION.md` §5, los campos nuevos; el líder pone al día
  `azure-apps/dedicacion.md` en el mismo trabajo (design §11).

## 8. Tests anteriores que cambian: lista CERRADA

- Front (el texto «automática» y la rama de la celda): `test_f050_subfilas::
  test_f050_r24_celda_elegida_fija_o_automatica` y `::test_f050_r28_filtro_
  partida_casa_linea_a_linea` (`auto`); `test_f055_propuesta_celda::
  test_f055_r27_html_de_la_celda` (caso `automatica`) y `::test_f055_r27_
  construir_celda_usa_html_partida`; `test_f057_buscando_pendientes::test_
  f057_r1_buscando_solo_si_la_linea_es_pendiente` (los tres `AUTOMATICA`);
  `test_f067_ver_vinculados::test_f067_r3_partida_desmarcada_solo_las_lineas`
  (`automatica`); `test_f050_selector_partida::test_f050_r26_sin_resultados_
  y_opcion_automatica` (solo si cambia la línea del rótulo).
- Api: `test_f025_sync_postventa::test_f025_r15_el_cliente_pide_el_universo_
  y_devuelve_los_ides` (lo esperado gana las partidas; el doble, su `res`).
- Otro test que cambie: **PARA** y se pregunta.

## 9. Verificación MANUAL (humano)

M1 (local, modo pruebas, solo preflight y Cancelar), M2 (local, base
`dedicacion` local, propuesta descartada) y M3 (producción, solo lectura):
`tasks.md` T13-T15.
