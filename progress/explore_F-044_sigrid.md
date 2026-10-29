<!-- progress/explore_F-044_sigrid.md -->
# F-044 · Exploración en Sigrid: recursos vinculados al trabajador

Spec-author, 2026-10-25, rama `feature/F-044-recursos-vinculados`. **Solo
lectura**: `POST /api/sql/read` de `sigrid-api` (base de la config del
transfer) con el `SigridWriteClient._read` del transfer, que lanza ante
`truncated`; todo agregado en SQL. Diccionario: `azure-apps/sigrid_tablas.md`
(`res`, `resres`, `reshor`, `hmores`, `auxrestip`, `defext`, `conext`, `auxhor`, `obrparpar`). Ni una escritura. **Sin
nombres, códigos de recurso, teléfonos, matrículas ni importes por
persona.** Los scripts viven en el scratchpad del agente, no en el repo.
Periodo medido: partes de 2026 (enero-octubre) salvo que se diga otra cosa.

## 0. Conclusión primera

1. **El vínculo es un campo extendido de Sigrid** (§6, ronda 2, a raíz de
   la respuesta del humano a D2): `defext` 46 «Recurso Asociado» (`tip = 33`,
   recursos; `cod = '5'`, `camtab = 'res'`), con su valor en `conext.valn` =
   `res.ide` del recurso principal. Lo tienen **538** recursos no persona; en
   los activos, TF 156 de 162, CO 89 de 95, VE 50 de 55, VP 55 de 56, CAJA
   112 de 119, VIAJE 18 de 22. Las otras vías están vacías: `resres` (0
   filas), `res.resconide`, `hmores.resconide`/`resrspide`, `res.cif`.
2. **El nombre fue la primera pista** (ronda 1, §2): la descripción del
   vinculado es `<CONCEPTO> <nombre del recurso persona>`, y casa con el campo
   en 153 de 156 TF, 88 de 89 CO y 50 de 50 VE. Manda el campo.
3. **Se imputan exactamente como la persona (P3).** `can` = el % del
   trabajador en ese parte, `pre` = `reshor.pre` del vinculado para su hora
   por defecto, `tot = can × pre`, `fec` = último día, en **el mismo parte**
   que la `M*` del trabajador, **una línea por cada línea `M*`** suya, y la
   cuenta analítica sale de `reshor.caaide` del vinculado (§3).
4. **Ninguna lleva `synckey`**: todas las de 2026 las metió Administración a
   mano; `partes` no escribe vinculados.

## 1. Qué recursos son (clasificación `auxrestip`, `res.cla = 0`)

| Tipo (`auxrestip.cod`) | Descripción del tipo | Hora en `reshor` (por defecto) | `pre` en `reshor` | Recursos activos |
|---|---|---|---|---|
| `TF` | CONSUMOS TELEFONO MOVIL | `OTEL` «CONSUMOS TELEFONO MOVIL» | ≠ 0 en 162 de 162 | 162 |
| `CO` | CONSUMOS GASOIL | `OGAS` «CONSUMOS GASOIL» | ≠ 0 en 95 de 95 | 95 |
| `VE` | VEHICULOS | `MESVE` «MES VEHICULO» | ≠ 0 en 55 de 55 | 55 |
| `VP` | VEHICULO PROPIO-KILOMETROS | `KM` «KILOMETROS-USO VEHICULO PROPIO» | ≠ 0 en 1 de 56 | 56 |
| `CAJA` | CAJA DE OBRA | `CO`/`CA`/`CD`/`CG` (caja) | 0 en todos | 119 |
| `VIAJE` | GASTOS VIAJES | `VI` «VIAJES AVION/BARCO/TREN» | 0 en todos | 22 |

Cada vinculado tiene **una** hora de las suyas y es su `res.horide`. `TF`,
`CO` y `VE` llevan **importe mensual fijo** en `reshor`, como un mensual;
`VP`, `CAJA` y `VIAJE` no (su importe cambia cada mes: km, tickets). Encaja
con el alcance de Juan Romero (2026-10-08): **teléfono, gasoil y vehículo**
por porcentaje; kilómetros y caja «de la manera habitual». **Ojo: `MESVE`
empieza por `M`.** No es de una persona (`cla = 0`), pero cualquier filtro
«hora `M*`» sobre líneas de **cualquier** recurso lo cuenta como mensual.

## 2. El vínculo por nombre, medido (ronda 1; sustituido por el campo de §6)

| Tipo | Casan con 1 mensual (misma empresa) | Con 0 | Con 2+ |
|---|---|---|---|
| `TF` | 154 | 8 | 0 |
| `CO` | 87 | 8 | 0 |
| `VE` | 50 | 5 | 0 |
| `VP` | 47 | 9 | 0 |

Sin exigir la misma empresa salen 2 vinculados (TF 1, CO 1) con 2 mensuales (personas
con recurso en dos empresas): la empresa los deshace. De los que no casan:
`TF` 8 y `VE` 5 no casan con ninguna persona; `CO` 2 y `VP` 7 casan con una
persona **no** mensual (va por `partes`). Hay descripciones antiguas con
otro formato (`GASOIL-<nombre>`, `<nombre>` sin concepto, una errata
`TEEFONO`): casi todas de recursos de baja. 2026: 224 líneas de vinculados
sin casar (TF 63, VE 57, VP 60, CO 41), que hoy seguirían a mano.

## 3. Cómo se imputan hoy (líneas de 2026 de vinculados casados)

| Tipo | Líneas | En el mismo parte que la `M*` de su mensual | `can` = el de su `M*` | `pre` = `reshor` | `tot = can × pre` | `fec` último día |
|---|---|---|---|---|---|---|
| `TF` | 2.629 | 2.629 | 2.622 | 2.625 | 2.629 | 2.438 |
| `CO` | 1.574 | 1.572 | 1.340 | 1.565 | 1.574 | 1.452 |
| `VE` | 979 | 978 | 788 | 968 | 979 | 922 |
| `VP` | 489 | 477 | 409 | 34 | 489 | 431 |

- **Varias obras.** Por recurso y mes, la suma de `can` del vinculado es 1
  cuando la del mensual es 1 (TF 1.262 de 1.278 meses; CO 685; VE 355) y
  menor cuando la del mensual es menor: **no se normaliza**, se copia el %.
  Por parte, el vinculado tiene **tantas líneas como `M*`** su mensual (TF
  2.257 de 2.271; CO 1.230 de 1.249; VE 752 de 761). Gasoil y vehículo se
  separan del % algo más (CO 15 %, VE 19 % de líneas con otro `can`): ajustes
  a mano de Administración; el patrón dominante es el mismo %.
- **Partida, obra normal**: casi nunca la de la persona (TF 13 de 2.076). Es
  la partida de su concepto en el presupuesto de la obra: TF `CI.4.13`
  «TELEFONO MOVIL» (1.903) y variantes (`CI.04.13`, `CI_F1.04.10`); CO
  `CI.4.1` «COMBUSTIBLES-GASOIL» (729), `CI.4.1B`, `CI.4.1.1`,
  `CI.03P.9`…; VE `CI.03P.9` «VEHICULOS» (643), `CI.03.01.09`… El código
  cambia de obra a obra; la descripción, poco.
- **Partida, postventa**: la partida de la **obra original**, como la persona
  (las «distintas» medidas son otras partidas-obra del mismo trabajador);
  `CP.7` «COSTES ESTRUCTURA. DELEGACIÓN» (138 TF, 138 CO, 96 VE) va con la
  persona en la misma `CP.7`.
- **Cuenta**: la subcuenta de `reshor.caaide` del vinculado en el 97-100 %
  (TF `CICO13` 2.540; CO `CICO01` 1.515; VE `CIMP09` 940; el resto con
  `caaide = 0`). Es la regla de `#regla-analitica` tal cual.
- **Al 0 %**: TF 21, CO 16, VE 10 líneas; todas en un parte donde su
  mensual también está a 0: las copia Administración del mes anterior.

## 4. El caso de la 0694, 2026-09

Un parte, `PT26/00319`, estado **3 (cerrado)**, 141 líneas, ninguna con
`synckey`. Vinculados: `OTEL` 7 líneas (`CI.4.13`, cuenta `…CICO13`), `OGAS`
4 (`CI.4.19_1`, `…CICO01`), `MESVE` 3 (`CI.03P.9`, `…CIMP09`), `KM` 2
(`CI.4.19_1`), todas el día 30. El trabajador del ejemplo lleva su `M*` al
95 % y su teléfono y sus kilómetros al 95 %, metidos a mano. Con F-044 el
teléfono saldría solo; los kilómetros, no (fuera de alcance). Al estar el
parte cerrado, una escritura nueva iría al complementario (`#regla-analitica`).

## 5. Octubre de 2026 (el mes que pide Juan)

Hasta hoy, en partes En registro (`est = 1`): TF 27 líneas (11 a 0), CO 16
(7 a 0), VE 13 (6 a 0), VP 11 (7 a 0), en 2-3 partes por tipo; y 41 `M*`
de mensuales (17 a 0). Son las copias del mes anterior que ya vio F-051
(0707, `PT26/00370`): **habrá vinculados al 0 % que pisar**. Septiembre:
675 líneas de vinculados en 36 partes cerrados y 122 en 3 En registro.

## 6. Ronda 2 (2026-10-25): el campo «Recurso Asociado»

- **Definición**: `defext` 46, `tip = 33`, `cod = '5'`, «Recurso Asociado»,
  `camtip = 6` (índice), `camtab = 'res'`. Valores en `conext` (`conide` = el
  vinculado, `valn` = el principal): 556 filas en recursos no persona (538 con
  valor) y 1 vacía en una persona; **una fila por vinculado**, nunca dos.
- **A quién apunta** (vinculados activos con valor): siempre a un recurso
  persona (`cla = 1`) activo y de la **misma empresa**; a un **mensual** en TF
  156/156, CO 88/89, VE 50/50, VIAJE 18/18, CAJA 104/112, VP 48/55 (el resto,
  personas que van por horas: `partes`).
- **Por principal mensual activo, como mucho uno de cada tipo**; 171
  mensuales activos tienen al menos un vinculado.
- **Tipos sin el campo**: los dos `VAR` (mensajería, F-052) y tres sueltos.

## 7. Ronda 2: la «CI de su tipo» es la cuenta del recurso

`auxrestip` no tiene partida y `auxhor.parcod` («Código partida obra») está
**vacío** en todas las horas. Lo que da la CI es la **cuenta**: la subcuenta de
`reshor.caaide` del vinculado (TF `CICO13`, CO `CICO01`, VE `CIMP09`, CAJA
`CICO15`, VIAJE `CIIN10`, VP `CIMJ09`; las mismas en `auxhor.caacod`) se
corresponde con la partida del presupuesto cuya cuenta (`obrparpar.caaide`)
tiene esa subcuenta: `CICO13` ↔ `CI.4.13`, `CICO01` ↔ `CI.4.1`, `CIMP09` ↔
`CI.03P.9`.

| Líneas 2026 con partida `CI*` (vinculados por el campo) | TF | CO | VE |
|---|---|---|---|
| La cuenta de su partida tiene la subcuenta del vinculado | 1.948 | 906 | 687 |
| Otra subcuenta | 18 | 113 | 6 |
| Partida sin cuenta | 9 | 148 | 2 |

Por obra con líneas del tipo, **hojas activas** con esa subcuenta: TF 1 en 45
obras, 0 en 1, 2+ en 4; CO 1 en 44, 0 en 2, 2+ en 5; VE 1 en 41, 0 en 2, 2+
en 4. **Cuando la partida del titular no es `CI*`**, el vinculado va a **la
misma partida que el titular**: en `POSTV2` (761 líneas) y `VAR` (37), 676 de
676 líneas TF/CO/VE en una partida-obra van a la de una `M*` de su titular; en
las `CP*` («COSTES ESTRUCTURA. DELEGACIÓN», en obras normales: 0678, 0704,
0713…), 377 de 377.

## 8. Consultas (resumen; las SQL están en el scratchpad del agente)

`res`×`auxrestip` por clase y tipo; `resres` y `res.resconide` (vacíos);
`hmores.resconide/resrspide` en 2026; casado por cola de nombre con y sin
empresa; `reshor` de los vinculados (hora, `pre`, `caaide`); líneas 2026 de
vinculados frente a las `M*` de su mensual (mismo parte, `can`, `pre`,
`tot`, `fec`, partida, subcuenta, nº de líneas por parte, suma por mes);
octubre y septiembre por estado de parte; ronda 2: `defext`, `conext` sobre
`res` (cobertura, destino, empresa, mensual, coincidencia con el nombre),
`auxhor.parcod/caacod` y subcuenta de la partida frente a la del vinculado,
por obra y por clase de partida. Ninguna respuesta `truncated`.
