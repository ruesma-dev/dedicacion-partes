<!-- specs/F-050-subfilas-partida/requirements.md -->
# F-050 · Subfilas por obra con columna Partida y partida propuesta

Rigor **`critico`** (la partida decide qué se escribe en Sigrid); toca los
**tres servicios** (design §1); **absorbe F-043**. Pedida el 2026-10-08.
**D1-D10: DECIDIDAS por el humano el 2026-10-09, todas A** (design §11; R
marcados `[Dn]`); precisiones suyas: el modal usa el mismo selector que la
columna (R29), con filtro por mayor **CD · CI · CP** (R26).

Fuera de alcance: F-051 (pisar al 0 %), F-044 (vinculados), F-054, F-021,
el Excel (D8) y dos partidas para una misma línea. Glosario: **elegida** =
la guardada en la asignación; **propuesta** = la que calcula el transfer;
**automática** = línea sin elegida; **mayor** = CD, CI, CP u OTRO, el de la
raíz del presupuesto de la que cuelga la partida (design §5.1).

## 1. Propuesta de partida (transfer)

- **R1.** `[D1][D2]` Para una línea de obra normal sin partida elegida, el
  sistema debe proponer la del primer paso que dé una: (1) **parte
  anterior**: la línea `M*` con partida más reciente de ese recurso en un
  parte de trabajo de **esa obra**, del periodo del cuadrante (incluido)
  hacia atrás, hasta `PROPUESTA_MESES_ATRAS` meses (24); (2) **último
  parte**: la más reciente del recurso en **otra** obra, trasladada a esta
  por código y descripción iguales; (3) **casamiento** por nombre y
  categoría (`resolver_normal`, el de hoy).
- **R2.** Dentro del mes elegido en (1) o (2) gana la partida con más `can`
  sumado. SI hay empate, o el traslado de (2) da cero o varias hojas,
  ENTONCES ese paso no propone y se pasa al siguiente: nunca la primera.
- **R3.** Toda partida propuesta debe ser **hoja activa** del presupuesto de
  la obra de origen (también en modo pruebas); una del historial que ya no
  lo es no se propone y se pasa al paso siguiente.
- **R4.** Solo cuentan las líneas de partes de trabajo (`con.tip` del
  ajuste) con código de hora `M*`, `paride` ≠ 0 y cuya partida es del
  presupuesto de la obra del parte (descarta las de la 0404 en pruebas).
- **R5.** El orden en que Sigrid devuelva las filas no puede cambiar la propuesta.
- **R6.** Cada propuesta lleva su método (`parte_anterior`, `ultimo_parte`,
  `auto_nombre`, `auto_categoria`) y, en (1) y (2), su origen (parte, mes, obra).
- **R7.** El historial se lee en **una** lectura por petición. SI falla o
  viene `truncated`, ENTONCES la petición falla sin proponer ni escribir.
- **R8.** El transfer debe exponer `POST /api/partidas/propuesta`, de solo
  lectura: empresa, obra, año, mes y líneas (`clave`, `recurso_ide`,
  `nombre`, `categoria`, `es_postventa`) → catálogo de la obra (y de
  postventa si hay líneas de postventa), cada partida con su **mayor**, y
  por clave la propuesta (o nula) y `mayor_inicial`: el de la propuesta; sin
  ella, `CI` si `ambito_categoria` da solo CI; si no, nulo (= Todas).
  Empresa no válida o obra de otra empresa → 422 con motivo; lectura → 502.
- **R9.** El preflight debe proponer con **la misma función** que R8: la
  propuesta del selector y la automática del registro no pueden diferir.
- **R10.** Los catálogos (`partidas_obra`, `partidas_postventa` y los de R8)
  salen ordenados por código en orden natural (`CI.1.9` antes que
  `CI.1.10`), con su categoría.
- **R11.** `[D5]` En postventa la propuesta es el casado de `#regla-p5` (sin
  pasos 1-2); las entradas VAR no se proponen: partida fija (`#regla-var`).

## 2. La partida elegida (api)

- **R12.** `[D4]` La asignación debe guardar la partida elegida (ide, código,
  descripción; las tres nulas = automática): columnas nulables del ORM.
- **R13.** `PUT /api/v1/periodos/{a}/{m}/trabajadores/{ide}/partida` con
  `obra_ide`, `es_postventa` y `partida` (`{ide, cod, res}` o `null`) debe
  cambiar solo la partida de esa línea, dejar un evento `PARTIDA` con su
  `X-Usuario` y devolver la fila y el resumen como el guardado. Periodo,
  trabajador o línea inexistente 404, cerrado 409, VAR o `ide` ≤ 0 422; en
  error no se toca nada.
- **R14.** `[D4]` Guardar la fila (sustitución atómica) debe conservar la
  partida de cada línea cuya clave (obra, postventa) ya existía; una línea
  nueva entra automática. Solo R13 y deshacer cambian una partida.
- **R15.** Deshacer (`#regla-deshacer`) debe devolver también la partida. El
  snapshot del evento lleva la partida solo si la línea la tiene.
- **R16.** `[D4]` Copiar el mes anterior (trabajador y periodo) copia la
  partida; Completar conserva la de la línea existente y la nueva entra
  automática. F7 (fila superior) manda líneas sin partida (R14).
- **R17.** `GET /api/v1/periodos/{a}/{m}/trabajadores/{ide}/partidas?
  obra_ide=&es_postventa=` debe devolver catálogo con mayor (R8, R10),
  propuesta, elegida y **ámbito preelegido**: el mayor de la elegida si está
  en el catálogo; si no, `mayor_inicial` (R8). VAR: su partida fija, sin
  llamar al transfer. Transfer caído → 502 con motivo; el cuadrante, igual.
- **R18.** Cada línea del cuadrante publica `partida_ide`, `partida_cod`, `partida_res` y `partida_fija` (VAR).
- **R19.** Al registrar, cada línea con partida elegida viaja con ella como
  `paride`; un `overrides` del cuerpo manda sobre ella; VAR como hoy.

## 3. Al registrar (transfer)

- **R20.** `[D9]` SI la partida que llega no es hoja activa del presupuesto
  de la obra de origen, ENTONCES la línea se omite con un motivo que nombra
  la partida, sin aviso de «sin partida» (hoy solo se valida en postventa).
- **R21.** Cada acción del preflight lleva `partida_metodo` (`manual`) y `partida_origen` (R6).

## 4. Cuadrante y selector (front)

- **R22.** `[D6]` Cada línea del trabajador debe verse en su **subfila**;
  nombre, categoría, total y botones, una vez. Sin líneas, fila «sin carga».
- **R23.** Una columna «Partida» debe salir a la derecha de la de obras. Con
  preferencias guardadas sin ella, entra justo a su derecha.
- **R24.** La celda enseña la elegida (código · descripción), la fija de VAR
  sin selector, o «automática» en cursiva si no hay elegida.
- **R25.** CUANDO se hace clic en la celda Partida (periodo ABIERTO), el
  sistema debe abrir el selector sin abrir el editor ni tocar la selección
  múltiple; si el editor de ese trabajador tiene cambios, los guarda antes.
- **R26.** El selector (desplegable con buscador, como en `partes`) debe
  tener: campo que filtra en vivo por código y descripción sin mayúsculas ni
  tildes (todas las palabras); botones **Todas · CD · CI · CP**, uno activo,
  que filtran por mayor (OTRO solo en Todas), con el ámbito de R17
  preelegido; la lista en el orden de la API con la propuesta **primera**
  (si pasa los filtros) y su origen; «Sin partidas con ese filtro»; la
  opción «automática» (borra la elegida); ↑ ↓ Enter Esc y ratón; panel
  colgado de `<body>` como el de F-042.
- **R27.** Elegir debe llamar a R13 y repintar la fila con la respuesta. El
  front no calcula ni decide la propuesta ni el mayor.
- **R28.** `[D6]` ↑ ↓ (por trabajador), Enter, R, F7, F8, C, «/», Ctrl+Z
  (deshace también un cambio de partida), la selección múltiple, el editor
  y «% Enter obra Enter» deben actuar como hoy. El filtro de obras filtra
  trabajadores y enseña todas sus subfilas; el filtro «Partida» casa línea a
  línea; el buscador libre incluye la partida.
- **R29.** `[D7]` El modal de registro debe enseñar en cada acción a
  escribir su partida (`partida_cod` de la acción aunque no esté en el
  catálogo, o «sin partida») y su origen. CUANDO se hace clic en ella, el
  sistema debe abrir **el mismo selector de R25-R27** para esa línea (sin
  `<select>`); lo elegido se guarda (R13), repinta la fila y repite el
  preflight (F-049). VAR, fija. El front deja de mandar `overrides` y de
  leer `partidas_obra`/`partidas_postventa` del preflight. Una omitida por R20 también lleva el selector (humano, 2026-10-10).

## 5. Documentación

- **R30.** `ARCHITECTURE.md` gana `#regla-partida` (fuente única de R1-R4,
  R20 y el mayor); `INTEGRACION.md`, los endpoints de R8, R13 y R17; el
  líder pone al día `azure-apps/dedicacion.md` en el mismo trabajo.

## 6. Tests anteriores que cambian: lista CERRADA (con D1-D10 = A)

- Transfer, dobles de cliente que ganan la lectura del historial (vacía),
  sin tocar aserciones: `conftest.py`, `test_f022_obra_por_empresa`,
  `test_f047_tope_filas`, `test_f049_partidas_obra`, `test_pipeline_offline`.
- `test_f002_fuente_unica`: `ANCLAS` gana `regla-partida`.
- Api: `_fila` de `test_f022_empresa_en_linea`, `test_f024_registro_empresa`,
  `test_f026_registro_recurso` y `test_f039_registro_var` ganan
  `partida_ide=None, partida_cod=None`; `CAMPOS_LINEA` de `test_f034_rutas`
  gana los cuatro campos de R18.
- Front (R29 quita `<select>`, `opcionesPartida` y `overrides`): los de
  `test_f039_partida_fija`, `test_f049_avisos_registro` y `test_f049_
  ampliacion_registro` que nombra `tasks.md` T12 (parte de esta lista).
- Añadidos por el humano el 2026-10-09: `test_f037_r3_una_linea_sin_partida_no_
  hereda_la_de_otra` (partida 1 en `cli.partidas_origen`, R20) y `test_f003_r8_…`
  (el conjunto esperado suma las tres `partida_*`, R12); sin otras aserciones.
  Cualquier otro test que cambie: **PARA** y se pregunta al humano.

## 7. Verificación MANUAL (humano)

M1 (solo lectura), M2 (navegador, **modo pruebas**: selector en columna y
modal, CD · CI · CP) y M3 (registro en pruebas, 0404): `tasks.md` T16-T18.
