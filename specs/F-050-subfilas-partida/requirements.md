<!-- specs/F-050-subfilas-partida/requirements.md -->
# F-050 · Subfilas por obra con columna Partida y partida propuesta

Rigor **`critico`**: la partida decide qué se escribe en Sigrid. Toca los
**tres servicios** (design §1). **Absorbe F-043** (selector predictivo,
ordenado, CI/CD). Pedida por el humano el 2026-10-08 (`features.json`).

**Decisiones D1-D10: ABIERTAS** (design §11, cada una con recomendada,
alternativas y efecto en tests). Los R marcados `[Dn]` están escritos con la
recomendada; si el humano elige otra, se reescriben antes de implementar.

Fuera de alcance: pisar las líneas al 0 % (F-051), recursos vinculados
(F-044), traer los % de Sigrid (F-054), velar las otras obras (F-021), el
Excel (D8) y dos partidas para la misma obra y trabajador (una línea = una
partida). Glosario: **elegida** = la guardada en la asignación; **propuesta**
= la que calcula el transfer; **automática** = línea sin elegida.

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
  `auto_nombre`, `auto_categoria`) y, en (1) y (2), su origen (parte, mes y,
  en (2), obra).
- **R7.** El historial se lee en **una** lectura por petición. SI falla o
  viene `truncated`, ENTONCES la petición falla sin proponer ni escribir.
- **R8.** El transfer debe exponer `POST /api/partidas/propuesta`, de solo
  lectura: empresa, obra, año, mes y líneas (`clave`, `recurso_ide`,
  `nombre`, `categoria`, `es_postventa`) → catálogo de la obra (y de
  postventa si hay líneas de postventa), y por clave la propuesta (o nula) y
  el ámbito CI/CD de `ambito_categoria`. Empresa no válida → 422; obra de
  otra empresa → 422 con motivo; fallo de lectura → 502.
- **R9.** El preflight debe proponer con **la misma función** que R8: la
  propuesta del selector y la automática del registro no pueden diferir.
- **R10.** Los catálogos (`partidas_obra`, `partidas_postventa` y los de R8)
  salen ordenados por código en orden natural (`CI.1.9` antes que
  `CI.1.10`), con su categoría.
- **R11.** `[D5]` En postventa la propuesta es el casado de
  `#regla-p5` (sin pasos 1-2) sobre `partidas_postventa`; las entradas VAR
  no se proponen: su partida es fija (`#regla-var`).

## 2. La partida elegida (api)

- **R12.** `[D4]` La asignación debe guardar la partida elegida (ide, código
  y descripción); las tres nulas = automática. Columnas nulables derivadas
  del ORM, sin migración.
- **R13.** `PUT /api/v1/periodos/{a}/{m}/trabajadores/{ide}/partida` con
  `obra_ide`, `es_postventa` y `partida` (`{ide, cod, res}` o `null`) debe
  cambiar solo la partida de esa línea, dejar un evento `PARTIDA` con su
  `X-Usuario` y devolver la fila y el resumen como el guardado. Periodo
  inexistente 404, cerrado 409, trabajador o línea inexistente 404, entrada
  VAR 422, `ide` ≤ 0 422; en error no se toca nada.
- **R14.** `[D4]` Guardar la fila (sustitución atómica) debe conservar la
  partida de cada línea cuya clave (obra, postventa) ya existía; una línea
  nueva entra automática. Solo R13 y deshacer cambian una partida.
- **R15.** Deshacer (`#regla-deshacer`) debe devolver también la partida. El
  snapshot del evento lleva la partida solo si la línea la tiene.
- **R16.** `[D4]` Copiar el mes anterior (trabajador y periodo) copia la
  partida; Completar conserva la de la línea existente y la nueva entra
  automática. F7 (fila superior) manda líneas sin partida (R14).
- **R17.** `GET /api/v1/periodos/{a}/{m}/trabajadores/{ide}/partidas?
  obra_ide=&es_postventa=` debe devolver el catálogo (R10), el ámbito, la
  propuesta (R1-R11) y la elegida. Entrada VAR: su partida fija, sin llamar
  al transfer. Transfer caído → 502 con motivo; el cuadrante sigue igual.
- **R18.** Cada línea del cuadrante debe publicar `partida_ide`,
  `partida_cod`, `partida_res` y `partida_fija` (entrada VAR).
- **R19.** Al registrar, cada línea con partida elegida viaja con ella como
  `paride`; un `overrides` del cuerpo manda sobre ella; VAR como hoy.

## 3. Al registrar (transfer)

- **R20.** `[D9]` SI la partida que llega no es hoja activa del presupuesto
  de la obra de origen, ENTONCES la línea se omite con un motivo que nombra
  la partida, sin aviso de «sin partida» (hoy solo se valida en postventa).
- **R21.** Cada acción del preflight lleva `partida_metodo` (`manual` =
  elegida) y `partida_origen` (R6).

## 4. Cuadrante y selector (front)

- **R22.** `[D6]` Cada línea del trabajador debe verse en su **subfila**;
  nombre, categoría, total y botones, una vez por trabajador. Sin líneas,
  una sola fila «sin carga».
- **R23.** Una columna «Partida» debe salir a la derecha de la de obras. Con
  preferencias guardadas sin ella, entra justo a su derecha.
- **R24.** La celda enseña la elegida (código · descripción), la fija de VAR
  sin selector, o «automática» en cursiva si no hay elegida.
- **R25.** CUANDO se hace clic en la celda Partida (periodo ABIERTO), el
  sistema debe abrir el selector sin abrir el editor ni tocar la selección
  múltiple; si el editor de ese trabajador tiene cambios, los guarda antes.
- **R26.** El selector debe tener: campo que filtra en vivo por código y
  descripción sin mayúsculas ni tildes (todas las palabras tecleadas);
  botones Todas / CI / CD con el ámbito de R17 preelegido; la lista en el
  orden de la API con la propuesta **primera** y su origen rotulado; la
  opción «automática» (borra la elegida); ↑ ↓ Enter Esc y ratón; panel
  colgado de `<body>` como el de F-042.
- **R27.** Elegir debe llamar a R13 y repintar la fila con la respuesta. El
  front no calcula ni decide la propuesta.
- **R28.** `[D6]` ↑ ↓ (por trabajador), Enter, R, F7, F8, C, «/», Ctrl+Z
  (deshace también un cambio de partida), la selección múltiple, el editor
  y «% Enter obra Enter» deben actuar como hoy. El filtro de obras filtra
  trabajadores y enseña todas sus subfilas; el filtro «Partida» casa línea a
  línea; el buscador libre incluye la partida.
- **R29.** `[D7]` El modal de registro debe enseñar la partida de cada
  acción y su origen; cambiarla en su desplegable la guarda (R13) y repite
  el preflight (F-049). El front deja de mandar `overrides`.

## 5. Documentación

- **R30.** `ARCHITECTURE.md` gana `#regla-partida` (fuente única de R1-R4
  y R20); `INTEGRACION.md`, los endpoints de R8, R13 y R17; el líder pone
  al día `azure-apps/dedicacion.md` en el mismo trabajo.

## 6. Tests anteriores que cambian: lista CERRADA (con las recomendadas)

- Dobles de cliente del transfer, que ganan la lectura del historial
  (vacía), sin tocar aserciones: `conftest.py`, `test_f022_obra_por_empresa`,
  `test_f047_tope_filas`, `test_f049_partidas_obra`, `test_pipeline_offline`.
- `test_f002_fuente_unica`: `ANCLAS` gana `regla-partida`.
- api: `_fila` de `test_f022_empresa_en_linea`, `test_f024_registro_empresa`,
  `test_f026_registro_recurso` y `test_f039_registro_var` ganan
  `partida_ide=None, partida_cod=None`; `CAMPOS_LINEA` de `test_f034_rutas`
  gana los cuatro campos de R18.
- front, `test_f049_ampliacion_registro` (D7): `a_repreflight_manda_las_
  elegidas_y_el_trabajador`, `b_abrir_desde_un_boton_empieza_sin_partidas_
  elegidas`, `b_abrir_de_nuevo_descarta_un_repreflight_en_vuelo`,
  `a_cambiar_la_partida_la_apunta_y_repite_el_preflight` y
  `a_el_preflight_repetido_lleva_la_partida_recien_elegida`.

Cualquier otro test que cambie: **PARA** y se pregunta al humano.

## 7. Verificación MANUAL (humano)

M1 (script, solo lectura), M2 (navegador, transfer en **modo pruebas**) y
M3 (registro en pruebas, 0404): comandos exactos en `tasks.md` T16-T18.
