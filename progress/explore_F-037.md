<!-- progress/explore_F-037.md -->
# F-037 · Exploración: asiento analítico del parte en Sigrid

Spec-author, 2026-10-05, rama `feature/F-037-asiento-analitico-obra`. **Solo
lectura**: todas las consultas por `POST /api/sql/read` de `sigrid-api` (base
`ruesma`) con `SigridApiClient` de `dedicacion-api`; diccionario en
`azure-apps/sigrid_tablas.md`. Ni una escritura. Sin nombres de personas: las
cuentas analíticas del centro de personal se citan como `CP.<persona>`.

## 0. Conclusión primera

**El asiento analítico del parte YA existe en Sigrid y no lo tiene que
construir el transfer.** Es un documento `ANA<aa>/nnnnn` (`con.tip = 32`,
extensión `asa`, apuntes `apa` sin apunte financiero) que se genera **uno por
parte de trabajo** (obra y mes), titulado `Parte <obra>`, a partir de las
líneas del parte: **debe** a la cuenta analítica de cada línea
(`hmores.caaide`, p. ej. `0702.CIMO02 JEFE DE OBRA`) y **haber** a la cuenta
analítica de contrapartida del recurso (`res.caaconide`, `CP.<persona>` del
centro `CP` «CENTRO DE PERSONAL»). Lo genera Administración, casi seguro con
el botón «Contabiliza parte…» (§9), **por lotes y con retraso** (último lote: 2026-09-02 y 2026-09-14, para enero-febrero de 2026).

El coste financiero (6XX) **ya lo contabiliza la nómina**: asientos tipo 20
con 640/642 desglosados a `CP.<persona>`. El ANA del parte solo **traspasa**
ese coste del centro de personal a la obra.

**Lo que falla hoy está en el transfer**: escribe `hmores.caaide = 0`
(`sigrid_write_client.stmt_insert_linea`, comentario «pendiente de
confirmar»). Sigrid, al grabar un parte a mano, la rellena siempre (§3), y
las líneas sin cuenta **no entran en ningún ANA** (§4: la obra `GG`, la única
con líneas sin cuenta, no tiene ningún ANA). Un asiento propio del transfer
duplicaría el traspaso (el ANA es por parte, y nuestras líneas viven en el
mismo parte que las manuales) y uno financiero 64X duplicaría la nómina.

## 1. El asiento de ejemplo (XRT26/05432)

- `con`: ide 2779446, emp 1, `tip = 20` (asiento), fec 20260603. `asi`: deb =
  hab = 4.799,08.
- `apu` (4 apuntes): 4070005341 D 2.399,54 · 5720000058 H · **6260000000 D
  2.399,54** (`cenide` = centro 0702, `info = 'A0'`) · 4070005341 H.
- `apa` (1 fila): `conide` = el asiento, `apuide` = el apunte 626,
  `cenide` = 2519527 (centro 0702), `cueide` = 2519812 = **`0702.CP0004
  AVALES`**, deb 2.399,54.

Modelo: **`con` (cabecera, tip 20 asiento / 32 asiento analítico) → `asi` o
`asa` (1-1) → `apu` (apuntes financieros, `cueide` → `cua`) → `apa`
(desglose analítico, `apuide` → `apu` o 0, `conide` → `con`, `cenide` →
`cen`, `cueide` → `caa`)**. Las cuentas analíticas (`caa`, hojas) y sus
grupos (`cag`) cuelgan de un centro de coste (`caa.cenide`).

## 2. Centro de coste y árbol analítico de una obra

`obr.cenide` es el centro de la obra: 0702 → 2519527, 0404 → 828943; los dos
con `cen.cenide` = 496688 (`00000` «OBRA MODELO»). Cuentas: `caa.cenide =
obr.cenide`, código `<obra>.<hoja>`. 0702 tiene 270 hojas y 24 grupos;
0404, 269 (le falta `CIMO16`).

| Grupo | Hojas relevantes |
|---|---|
| `C` COSTES → `CD` directos (CDMA, CDQA/QC/QR, CDSB, CDSM, CDXA/XC) | materiales, maquinaria, subcontratas |
| `C` → `CI` indirectos → **`CIMO` MANO DE OBRA INDIRECTA** | **CIMO01 jefe de grupo, CIMO02 jefe de obra, CIMO03 encargado, CIMO04 ayte. jefe de obra, CIMO05 administrativo obra, CIMO06 topógrafo**, … CIMO16 técnico PRL |
| `C` → `CI` → CICO, CIIN, CIMJ, CIMP, CIOI, CISS, CITE | consumos, infraestructura, maquinaria, … |
| `C` → `CP` proporcionales → `CP00` | CP0001-CP0010 (seguros, avales, estructura…) |
| `I` INGRESOS → `IN` → `INGR` | INGR01 producción (`obr.caaejepen`), INGR02 certificación (`obr.caaejecer`) |

De las 50 obras con líneas M\* en 2026, 49 tienen `<obra>.CIMO02`; la otra es
`GG`. Ningún centro de la empresa 1 repite el código `<x>.CIMO02`.

## 3. Qué lleva una línea de parte grabada en Sigrid

Líneas `hmores` desde 2025-01-01 por origen:

| Origen | Tipo | Líneas | Con `caaide` | Con `cuaide` | Con `cenide` |
|---|---|---|---|---|---|
| manual (sin synckey) | M\* | 7.836 | 7.572 | 0 | 7.836 |
| manual | resto | 62.297 | 51.233 | 0 | 62.297 |
| `partes:` | resto | 4 | **0** | 0 | 4 |
| `porcentajes:` | — | **0** (ninguna, en ninguna fecha) | — | — | — |

- Las M\* sin cuenta son todas de `GG` (263) salvo una (0692).
- En las 3.469 líneas M\* manuales de 2026 con cuenta: `hmores.cenide =
  obr.cenide` y `caa.cenide = hmores.cenide` en el **100 %**.
- **De dónde sale la hoja.** `reshor.caaide` (cuenta del tipo de hora en la
  ficha del recurso) apunta a la del centro modelo (`00000.CIMO02`…);
  `auxhor.caacod` trae el mismo sufijo (`00000.CIMO02` o `CIMO05` a secas).
  En las M\* manuales con cuenta desde 2025: 7.119 con las dos iguales (7.004
  casan con la línea; 115 cambiadas a mano), 6 con las dos distintas (las 6
  siguen a `reshor`) y 447 con `reshor` sin cuenta (las 447 siguen a
  `auxhor`). Regla: **hoja = sufijo de `reshor.caaide`; si no hay, de
  `auxhor.caacod`; cuenta = la de esa hoja en el centro de la obra de la
  línea.**
- Tipos M\* → hoja: MJG CIMO01, MJEFO CIMO02, MENC CIMO03, MAJO/MATP/MING/MOT
  CIMO04, MADM CIMO05, MTOP CIMO06, MCAP CIMO08, MPRL CIMO16, MESVE CIMP09,
  MESGR CIMP01, MESMQ CIMP10, MESCA CIIN02/CISS03, MLIM CIIN10, MA CICO18.
- **Postventa**: las líneas en `POSTV2` llevan `POSTV2.<hoja>` (centro de la
  obra de postventa) y sus partidas no tienen cuenta (`obrparpar.caaide`
  vacío): la cuenta no sale de la partida. En 0702 la partida suele tener la
  misma cuenta que la línea, pero cuando difieren (línea `KM`) manda el tipo
  de hora.
- `hmores.cuaide` (cuenta financiera) es 0 en las 30.075 líneas de 2026, y
  `hmo.caaide` es 0 en los partes: no se usan.

## 4. El asiento analítico del parte (ANA)

- Serie `ANA<aa>/nnnnn`, `con.tip = 32`, `asa` 1-1, `apa.apuide = 0`. Desde
  2020: 406 / 411 / 452 / 495 / 509 / 441 / 58 (2026); el 97-100 % titulados
  `Parte <obra>`. Numeración sin huecos y **ningún** par repetido (`res`,
  `fec`): uno por parte, nunca regenerado dos veces.
- **Cuadre 2025**: 454 partes de la empresa 1; 440 con su ANA (mismo
  `con.res`, `fec` y `emp` que el parte); en **438** el debe del ANA es
  **exactamente** la suma de `hmores.tot` del parte. Los 14 sin ANA: 12 de
  `GG` (todas sus líneas sin `caaide`) y dos meses sueltos de 0698 y 0686.
- **Detalle `ANA26/00056`** (0702, 2026-02-28, «Parte EDIF. HOTELERO…»,
  mismo texto que el parte `PT26/00049`): 25 apuntes. Debe a `0702.CIMO01`
  2.250, `CIMO02` 7.000, `CIMO03` 6.500, `CIMO04` 6.035, `CIMO05` 1.800,
  `CIMO10` 4.192, `CIMO16` 1.575, `CIMP09`, `CICO01/05/13/15`, `CIMJ09`:
  **cifra a cifra la suma de las líneas del parte por cuenta** (y por texto
  de línea: una con `tex` sale aparte). Haber: 11 apuntes a `CP.<persona>`,
  uno por recurso = `res.caaconide`. Debe 30.590,54 / haber 30.530,54: los
  60 € de diferencia son una línea de un recurso **sin** `caaconide`.
- **Fecha** del ANA = la del parte (último día del mes, como P2). **Cuándo**
  (`con.tiemod`): 2025-06-06 (ene-mar 2025), 2025-11-21 (abr-sep),
  2026-03-02 (oct-dic), 2026-09-02 y 2026-09-14 (ene-feb 2026 y unos pocos
  de mar-jul). De marzo de 2026 en adelante faltan casi todos (2, 2, 2, 1, 1
  frente a ~35 partes al mes).
- **Qué herramienta lo genera**: no consta en `apa`/`con` (ni `doc` ni
  `obride`; enlace por `res` + `fec` + `emp`). Por la captura de §9, casi
  seguro el botón «Contabiliza parte…», que deja el parte en `con.est = 10`.

## 5. Coste de personal: nómina y traspaso (pregunta d)

Movimientos analíticos del centro `CP` de la empresa 1 en 2025 (`apa` por
tipo de documento y cuenta financiera del apunte):

| Origen | Cuenta financiera | Apuntes | Debe | Haber |
|---|---|---|---|---|
| asiento (tip 20) | **640** | 5.125 | 7,66 M€ | — |
| asiento (tip 20) | **642** | 4.780 | 2,52 M€ | — |
| asiento (tip 20) | 628 / 629 / 621 / 627 / 600 / … | ~5.200 | ~0,57 M€ | — |
| **ANA de partes (tip 32)** | (sin apunte) | 4.389 | — | **11,60 M€** |

`nomasi.apaide` (nómina → apunte analítico) tiene 96.883 filas. Desde 2024,
las cuentas `%.CIMO%` reciben 23,2 M€ por ANA (5.887 apuntes) y solo 0,12 M€
por asientos (54). **El personal de obra llega a la obra por el ANA del
parte, no por un asiento 64X propio.** No se buscó desglose CD de personal:
la mano de obra propia mensual vive en CI > CIMO.

## 6. Campos para idempotencia (pregunta e)

`synckey` (texto 128) existe en `hmo`, `hmores`, `hgv`, `hgvres`, `dca`,
`dcf`, `dco`, `dcp`, `dcppro`, `dma`, `dmapro`. **No** en `con`, `asi`, `asa`,
`apu` ni `apa`. Un ANA propio tendría que identificarse por su `con.cod`
(serie propia), `con.doc` (24) o `apa.doc` (24): ninguno es una clave
externa de verdad. Con la recomendación de la spec (rellenar `caaide`) la
idempotencia sigue siendo la `synckey` de `hmores`, sin cambios.

## 7. Datos útiles para la verificación con Administración

- Obra de pruebas 0404 (`obr.ide` 828942, centro 828943) tiene CIMO01-CIMO15
  pero **no CIMO16**: un recurso MPRL no encontraría cuenta en ella.
- 196 recursos persona M\* activos; **188** con `res.caaconide` y **8 sin**:
  sus líneas descuadran el ANA (caso de los 60 € de §4). Lo corrige
  Administración en la ficha del recurso; fuera del alcance del transfer.
- El parte que crea el transfer se titula `Parte <obra>` (como los manuales),
  así que su ANA seguirá el mismo patrón.
- **Corregido el 2026-10-05 (ver §10):** la nota anterior decía que
  `partes-persistencia` escribe `caaide = 0`. Es falso: ese 0 fijo era del
  repositorio archivado `partes-transfer` y de `prueba_escritura_sigrid.py`.
  Las 4 líneas `partes:` sin cuenta son de hasta el 2026-09-28, anteriores a
  la F-021 de `partes` (desplegada el 2026-10-01), que ya rellena `caaide`.

## 8. Consultas (resumen)

Todas `SELECT` por `sigrid-api` con valores literales de exploración:
asiento por `con.cod`; `apu`/`apa` por `asiide`/`apuide`; `obr`+`cen`+`caa`+
`cag` por `cenide`; `auxhor`/`reshor` M\* con su `caa`; `hmores` por origen
de `synckey` y por patrón de `caaide`; `con.tip = 32` por mes, serie y
`tiemod`; cuadre parte-ANA de 2025 (CTE por `res`+`fec`+`emp`); `apa` del
centro `CP` por cuenta financiera; `res.caaconide` de recursos M\*.

## 9. Captura de Juan Romero (2026-10-05) contrastada con los datos

Respuesta a «¿Dedicación también lleva la cuenta analítica?»: «La dedicación,
entiendo que te refieres al equipo de obra, tiene también analíticas», con la
captura del parte `PT26/00316` (obra 0711, septiembre de 2026, estado «REG En
registro»), columnas **Centro** y **Cue. analítica** por línea y botón
**«Contabiliza parte…»**.

**El parte es así en los datos.** `con` ide 2832442, `tip 35`, `est 1`, fec
20260930; `hmo.cenide` = centro 0711, `hmo.caaide = 0` (la «Cuenta analítica
(opcional)» vacía de la cabecera). Todas sus líneas manuales llevan `cenide` =
centro 0711 y su `caaide`. Pares tipo de hora · partida → cuenta de la línea
(con la hoja de `reshor` del recurso):

| Tipo | Partida (su cuenta) | Línea | `reshor` |
|---|---|---|---|
| MJG / MJEFO / MENC / MAJO / MADM / MCAP | CI.1.1 / .2 / .3 / .4 / .5 / .8 (`CIMO0N`) | igual | igual |
| HLGR, HEGR | CI.1.10 (`CIMO10`) | `CIMO10` | `CIMO10` |
| **MPRL** | CI.1.16 (`0711.CIMO16`) | **`0711.CIMO04`** | `CIMO16` |
| KM (3 líneas, 2 recursos) | CI.4.1 (`CICO01`) | `CIMJ09` / `CIMP09` | `CIMJ09` / `CIMP09` |
| OGAS (1 de 8 líneas) | CI.4.1 (`CICO01`) | `CICO13` | `CICO13` |
| HLOF | 02.xx (sin cuenta o `INGR02`) | `CIMO09` | `CIMO09` |

- **MPRL → CIMO04 no es un respaldo**: 0711 tiene CIMO01-CIMO16 completos,
  `CIMO16` incluida, y la partida y `reshor` dicen `CIMO16`. Es un cambio a
  mano (línea de 0 €). Se pregunta a Administración (D9).
- **La cuenta sigue al tipo de hora del recurso, no a la partida.** En todas
  las líneas manuales con partida con cuenta desde 2025: M\* con partida y
  tipo **iguales** 4.897 (4.802 casan); con los dos **distintos 540, y las
  540 siguen al tipo, 0 a la partida**. Resto de tipos distintos: 4.208 al
  tipo y 954 a la partida. Que `CI.1.N` ↔ `CIMO0N` coincidan en la captura es
  porque Administración monta las partidas así, no porque la cuenta salga de
  ellas. Una `reshor` con prefijo de otro centro (`0165.CICO01`) da
  `0711.CICO01`: la hoja se toma por sufijo.
- **«Contabiliza parte…» y el estado.** Partes de la empresa 1 desde 2025:
  `est = 10` y con ANA **502**; `est = 1` sin ANA 42; `est = 3` sin ANA 240;
  ningún `est = 10` sin ANA ni con ANA en otro estado. El 10 es «parte
  contabilizado», y da el enlace parte ↔ ANA sin la heurística de `res` +
  `fec` (que además casa dos obras de nombre parecido: «76 VIVIENDAS…» de
  0664 y 0711 tienen dos ANA por mes con `LIKE`, uno con igualdad exacta).
- **El centro de la línea**: `hmores.cenide`. El transfer **ya** lo escribe
  con `obr.cenide` de la obra destino (`_obra` → `stmt_insert_linea`), y la
  cabecera `hmo.cenide` igual (`stmts_crear_parte`); es lo mismo que hacen
  las 3.469 líneas M\* manuales de 2026 (§3). Lo único que falta es
  `caaide`.

## 10. Decisiones del humano (2026-10-05): regla de `partes` y complementario

### 10.1 «La cuenta analítica sale del recurso; mira en partes»

`partes` lo resolvió en su F-021 (desplegada el 2026-10-01; spec en
`partes/specs/F-021-cuenta-analitica-sigrid/`, medida al 99,64 % en la
empresa 1). Código: `partes/services/partes-transfer/application/services/
cuenta_analitica.py` (l. 7-96), SQL en su `sigrid_write_client.py` (l.
231-242 y 265-270) y pipeline (l. 206-245, lectura sin `try`).

- **Origen:** código de `reshor.caaide` del recurso para el tipo de hora que
  se escribe; si no da, el del tipo por defecto (`reshor` de `res.horide`).
  Solo vale la **subcuenta** (tras el primer punto, `strip`; sin punto, nada).
  `res.caaide` vale 0 en todos; `auxhor.caacod` y la partida no intervienen.
- **Destino:** la única `caa JOIN con` con `caa.cenide = obr.cenide` de la obra
  destino, `con.emp` = empresa de la obra y esa subcuenta.
- **Sin cuenta:** recurso sin subcuenta → 0 sin aviso; obra sin esa cuenta o
  con varias → 0 con aviso. La línea se escribe igual.
- **Contraste con §3** (M\* manuales desde 2025): las 447 líneas cuyo
  `reshor` del tipo escrito no tiene cuenta y que yo atribuía a `auxhor.caacod`
  las cubre el respaldo del tipo por defecto: 349 casan con la línea y 98 dan
  otra cuenta (ninguna queda sin subcuenta). La diferencia frente a la regla
  con `auxhor` es marginal y la regla común con `partes` manda.
- **Compatible con F-026 R19**: lee `res.horide`, no `res.conide`.

### 10.2 «Un parte ya contabilizado va a complementario»

En `partes` no hay nada parecido (allí «complementario» es solo su DDL de
PostgreSQL): se diseña aquí. Partes de Sigrid con **dos o más** `hmo` de la
misma obra, año y mes, `reside = 0` y `con.tip = 35`, de 2023 a 2026: 11
grupos; 9 con obra en `con` (18 partes), que son estos:

| Obra / mes | Partes (estado) | Qué son |
|---|---|---|
| GG 2023-12, 2024-01, 2024-02 | 2 por mes (3) | «Parte GASTOS GENERALES» y «… RETENCIONES»: estructura, sin ANA |
| 0655 2024-05 | `PT24/00190` (10) y `PT24/00205` (10) | el segundo, 11 días después, «PARTE HORAS COORDINACIÓN MOBILIARIO…», fec 20240528; **cada uno con su ANA** |
| 0665 2024-06 | `PT24/00218` (10) y `PT24/00241` (10) | mismo texto, fechas 0531 y 0630; cada uno con su ANA |
| 0660 2024-09 (emp 28) | dos (1) | uno vacío, duplicado de alta |
| 0704 2025-06 | `PT25/00228` (10) y `PT25/00281` (10) | el segundo, 41 días después, «Parte COSTES PREVIOS AL INICIO DE OBRA», fec 20250630 con líneas de enero-abril; **cada uno con su ANA** |
| 0687 2026-07 | dos (3) | uno con fec del mes anterior; sin contabilizar |
| 0692 2026-09 | `PT26/00322` y `PT26/00341` (1) | el segundo creado el 2026-10-05, fec 20261031; ninguno contabilizado |

- **Ningún complementario creado después de contabilizar**: en los tres casos
  con ANA, los dos partes ya existían cuando se contabilizó el mes
  (2024-09-02 y 2025-11-21) y «Contabiliza parte…» dio **un ANA a cada
  parte**. Prueba de que un segundo parte del mes se contabiliza aparte.
- **Nombre**: ni «COMPLEMENTARIO» ni marca; los únicos `con.res` con
  «COMPLEMENT» (3, de 2011) son el nombre de una obra. Texto libre o
  `Parte <obra>`.
- **Fecha y estado**: `con.fec` normalmente el último día del mes; se crean
  en estado 1 («REG»); se contabilizan a 10; el 3 aparece en partes sin ANA.
- **Enlace con el original: ninguno.** `con.doc`, `con.obr`, `con.tex` vacíos
  y `hmo.caaide = 0`; solo comparten obra, año y mes.
- **Selección de hoy**: `partes_existentes` toma el de mayor `hmo.ide`
  (`ORDER BY hmo.ide DESC`), sin mirar el estado: con un contabilizado y uno
  nuevo funcionaría por casualidad; con el contabilizado como único parte,
  escribiría en él.
- **Idempotencia**: `lineas_por_synckey` ya busca la `synckey` en todo
  `hmores`, sea cual sea el parte. **Identidad y capacidad** miran hoy solo el
  parte destino: con un complementario, una línea M\* del mismo recurso en el
  original contabilizado no se vería (D14).

Lo no aclarado por los datos queda como D12-D14 en la spec.
