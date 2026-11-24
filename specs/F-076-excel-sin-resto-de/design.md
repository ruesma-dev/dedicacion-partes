<!-- specs/F-076-excel-sin-resto-de/design.md -->
# F-076 · Diseño: pestañas Obras y Postventa sin «RESTO …»

**Rigor: `estandar`.** No cumple ningún disparador de `critico` de «Niveles
de rigor» (`CHECKPOINTS.md`): no escribe en Sigrid ni en la base, no cambia
contratos ni esquema; solo cambia qué filas y qué totales pinta el Excel.

**Decisiones del humano del 2026-11-24** («d1 b, lo demas a»): D1 = (b),
D2-D5 = (a) (§10). Parte del libro de F-045
(`specs/F-045-excel-obras-postventa/design.md` §3): cambian **qué grupos,
qué líneas y qué totales** llevan «Obras» y «Postventa»; «Detalle», el
formato, la columna I y el contrato del exportador, no.

## 1. Encaje en la arquitectura y límite de servicio

- **Solo `dedicacion-api`, capa `infrastructure/excel/`.** La ruta
  `export.xlsx` sigue llamando a `ObtenerCuadrante` y pasando `periodo` y
  `filas` al exportador. Cada `Linea` trae ya `es_postventa` y `porcentaje`:
  ni dato nuevo, ni ORM, ni SQL, ni `config.yaml`.
- Es **presentación**. El Estado de cada pestaña se calcula con
  `domain.estados.calcular_estado` / `calcular_desviacion` (la misma regla y
  la misma épsilon que el cuadrante), aplicada a la parte: no hay umbral
  propio en `excel/`. El front solo descarga el fichero; el transfer no
  interviene. Ninguna responsabilidad nueva fuera de la api.
- **F-038** (cuadro de mando «que sea el Excel», sin empezar) pensaba
  reutilizar `grupos_pestana`: heredará el comportamiento nuevo.

## 2. Ficheros

**Crear**

| Ruta | Qué |
|---|---|
| `services/dedicacion-api/tests/test_f076_excel_sin_resto.py` | Tests de R1-R14 (§5) |

**Modificar**

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | `grupos_pestana` sin agregada, sin los trabajadores de R5 y con el total de la parte (§3.1); `_grupo` recibe total y número de líneas; fuera `LineaDetalle.agregada` y `AGREGADA_EN_*` [D5]; docstrings |
| `services/dedicacion-api/infrastructure/excel/exporter.py` | Fuera `_CURSIVA` y el bloque `if linea.agregada` [D5]; docstring del módulo (§3.2) |
| `services/dedicacion-api/tests/test_f045_excel_pestanas.py` | Lista cerrada de §6.1 |
| `services/dedicacion-api/tests/test_f040_excel.py` | Lista cerrada de §6.2 |
| `docs/ARCHITECTURE.md` | Línea 79, `excel/`: «Obras y Postventa agrupadas por trabajador, cada una solo con sus líneas y con el total y el estado de esa parte (sin línea agregada de la otra)» (R14) |
| `services/dedicacion-api/README.md` | Fila `export.xlsx` (línea 45): ídem, sin «RESTO» (R14) |
| `specs/F-045-excel-obras-postventa/requirements.md` | Una nota bajo el título: «D3 (salvo la SIN CARGA), D4, D6, D7, D9 y R4, R7-R9, R11, R12 (su primera mitad), R15 y R16 sustituidos por F-076» |

**No se tocan**: `domain/` (`estados.py`, `models.py`, `ports.py`),
`application/`, `interface_adapters/api/` (`routes.py`, `deps.py`),
`config/config.yaml`, `orm_models.py`, `repositories.py`,
`requirements.txt`, `_linea_detalle`, `texto_estado` y `texto_pct` de
`contenido.py`, `_hoja_grupos` salvo la cursiva, `_rematar`,
`_titulo_y_cabecera`, `tests/test_f024_rutas_empresa.py` (exportador falso),
`tests/test_f039_registro_var.py` (su trabajador solo tiene obra: sigue en
la fila 3 de «Obras»), el front, el transfer, `infra/` y `azure-apps/`.
Sin SQL. La cabecera «Total empleado» no cambia de texto (§8).

## 3. Clases y funciones

### 3.1 `infrastructure/excel/contenido.py` (infrastructure, puro)

```python
@dataclass(frozen=True)
class LineaDetalle:               # sin el campo `agregada` [D5]
    codigo: str
    obra: str
    nombre: str
    porcentaje: Decimal | None

def grupos_detalle(filas, prefijo) -> list[GrupoTrabajador]                   # firma igual
def grupos_pestana(filas, prefijo, postventa: bool) -> list[GrupoTrabajador]  # firma igual
def _grupo(fila, lineas: list[LineaDetalle], total: Decimal, num: int) -> GrupoTrabajador
```

- `_grupo` deja de leer `fila.total` y `len(fila.lineas)`: recibe `total` y
  `num` y con ellos llama a `calcular_estado` y `calcular_desviacion`; el
  resto igual (empleado, categoría, `lineas or [_LINEA_VACIA]`, desviación
  `None` si SIN CARGA, `texto_estado`).
- `grupos_detalle` llama `_grupo(fila, …, fila.total, len(fila.lineas))`:
  «Detalle» sale idéntico (R12).
- `grupos_pestana`, por trabajador y en el orden de entrada (R6):
  1. `propias` = sus `Linea` con `ln.es_postventa == postventa` (R2, R3).
  2. Si `propias` está vacía y el trabajador **tiene** líneas (todas de la
     otra parte) → no sale en esta pestaña (R5).
  3. Si no: `_grupo(fila, [_linea_detalle(ln, prefijo) for ln in propias],
     sum((ln.porcentaje for ln in propias), Decimal(0)), len(propias))`
     (R8). Sin líneas, `num = 0` → «SIN CARGA» con total 0 en las dos
     pestañas [D2] (R7). Nada de suma de la otra parte ni línea agregada (R4).

El criterio de R5 es **por línea**: una línea de esa parte al 0 % hace salir
al trabajador, con total 0 y «FALTA 100%» (`num` = 1), igual que lo trataría
la regla del 100 % en el cuadrante.

### 3.2 `infrastructure/excel/exporter.py`

- Se borran `_CURSIVA` y, en `_hoja_grupos`, las tres líneas
  `if linea.agregada: … font = _CURSIVA` (R11). Nada más cambia en el
  pintado: F, G y H ya salen de `grupo.total`, `grupo.desviacion` y
  `grupo.estado`; bandas por índice `n` del grupo **en esa hoja** (R10);
  combinadas `_COMBINADAS` en grupos de más de una fila; columna I igual.
- Con cero grupos, `_hoja_grupos` ya deja título y cabecera y `_rematar`
  pone `A2:I2` (`max(ultima, 2)`): lo que hoy sale con `exportar([])` (R9,
  D3). No hace falta código.
- Docstring del módulo: «Obras» y «Postventa» llevan solo las líneas de su
  parte, solo los trabajadores con alguna (más los «SIN CARGA») y el Total,
  la Desviación y el Estado de esa parte; «Detalle», los del trabajador.

## 4. Qué sale con la muestra de `test_f045`

`_muestra()`: ALFA (0101 60, 0102 25, Postv-0702 15), BETA (0101 50, 0103
40), GAMMA (Postv 70 y 30), DELTA (sin carga), EPSILON (VAR-29 60, Postv 30
y 20). Total / Estado por hoja:

| Hoja | Grupos (filas) · Total · Estado | Última |
|---|---|---|
| Obras | ALFA 3-4 · 85 · FALTA 15%; BETA 5-6 · 90 · FALTA 10%; DELTA 7 · 0 · SIN CARGA; EPSILON 8 · 60 · FALTA 40% | 8 |
| Postventa | ALFA 3 · 15 · FALTA 85%; GAMMA 4-5 · 100 · OK; DELTA 6 · 0 · SIN CARGA; EPSILON 7-8 · 50 · FALTA 50% | 8 |
| Detalle | sin cambios: 3-5 OK, 6-7 FALTA 10%, 8-9 OK, 10 SIN CARGA, 11-13 EXCESO 10% | 13 |

## 5. Tests nuevos: `tests/test_f076_excel_sin_resto.py` (sin red ni BBDD)

Reutiliza `_fila`, `_linea`, `_rgb` y `_xml_hoja` de `test_f040_excel` y
`_muestra` de `test_f045_excel_pestanas` (importados, no copiados).

| Test | Qué fija |
|---|---|
| `test_f076_r1_tres_hojas_con_su_cabecera_y_autofiltro` | Nombres y orden; fila 2 = las 9 cabeceras; `A2:I<max_row>` en las tres |
| `test_f076_r2_obras_solo_lineas_de_obra` | Contenido y libro: ALFA `0101`, `0102`; EPSILON solo `VAR-29`; ningún Código con prefijo |
| `test_f076_r3_postventa_solo_lineas_de_postventa` | ALFA solo `Postv-0702`; todo Código no vacío empieza por el prefijo |
| `test_f076_r4_ninguna_linea_agregada` | En Obras y Postventa ningún Código «POSTVENTA»/«OBRAS» ni Obra que empiece por «RESTO»; contenido y libro |
| `test_f076_r5_sin_nada_de_esa_parte_no_sale` | GAMMA no está en Obras, BETA no está en Postventa (columna A por XML); una línea de postventa al 0 % sí lo hace salir |
| `test_f076_r6_orden_de_la_api_en_cada_pestana` | Con la muestra y con ella invertida: orden de entrada menos los de R5 |
| `test_f076_r7_sin_carga_en_las_tres_hojas` | DELTA: una fila «SIN CARGA», F = 0, G vacía, en Obras (7), Postventa (6) y Detalle [D2] |
| `test_f076_r8_total_desviacion_estado_de_la_parte` | Tabla de §4 en contenido (`Decimal`) y en libro (F, G, H); THETA 33,33 + 36,37 = 69,70 exacto; línea única al 0 % → «FALTA 100%»; en cada grupo la suma de E es F [D1] |
| `test_f076_r9_pestana_sin_nadie_solo_cabecera` | Sin postventa ni sin carga: Postventa con título, cabecera, `max_row == 2`, `A2:I2`; con un sin carga, solo su fila |
| `test_f076_r10_bandas_y_combinadas_por_pestana` | Postventa: ALFA blanco, GAMMA azul, DELTA blanco, EPSILON azul; `medium` bajo cada grupo; rangos combinados exactos |
| `test_f076_r11_ninguna_cursiva` | Ninguna celda de las tres hojas con `font.italic` |
| `test_f076_r12_detalle_igual_con_el_trabajador_completo` | Detalle: las 11 filas de F-045 R17 y F/G/H del completo (ALFA OK, EPSILON EXCESO 10%) |
| `test_f076_r13_prefijo_de_la_configuracion` | Con «PV_»: Postventa `PV_0702`; Obras sin «PV_» |
| `test_f076_r14_docs_sin_resto` | `docs/ARCHITECTURE.md` y el README de la api no contienen «RESTO» ni «otra parte en una línea» |

## 6. Lista CERRADA de tests anteriores que cambian [D4] = (a)

**Medida el 2026-11-24** aplicando el cambio de §3 (D1 b, D2 a, D5 a) a una
copia de la api fuera del repositorio y pasando `test_f040`, `test_f045`,
`test_f039` y `test_f024`: sin quitar los imports `AGREGADA_EN_*`,
`test_f045` no colecciona; quitados, fallan **25** items (24 de F-045 y 1 de
F-040) y pasan 100; F-039 y F-024, en verde. Criterio: **se borra** el test
cuyo requisito de F-045 muere (su cobertura pasa a `test_f076`); **se
adapta** el que sigue vigente y falla por los datos o por `agregada`. Fuera
de esta lista o de este criterio: **PARA**.

### 6.1 `tests/test_f045_excel_pestanas.py` (28 funciones)

Comunes: fuera los imports `AGREGADA_EN_*`; `_filas` sin `ln.agregada`
(tuplas de 3); `_GRUPOS` = Obras `[(3,4),(5,6),(7,7),(8,8)]`, Postventa
`[(3,3),(4,5),(6,6),(7,8)]`; fuera `_AGREGADAS` y `_empleados` (sin
consumidor tras borrar los `r4_r10`); docstring del módulo.

| Test (prefijo `test_f045_`) | Destino |
|---|---|
| `r4_mismos_trabajadores_y_orden_en_las_dos_pestanas` | Borrar (R4 → F-076 R6) |
| `r7_agregada_unica_al_final_con_rotulos_y_suma`, `r7_suma_exacta_en_decimal` | Borrar (R7) |
| `r8_sin_la_otra_parte_no_hay_agregada` | Borrar (R8 → F-076 R4) |
| `r9_solo_la_otra_parte_una_fila_agregada` | Borrar (R9 → F-076 R5) |
| `r11_total_desviacion_y_estado_del_trabajador_completo` | Borrar (R11 → F-076 R8) |
| `r12_la_suma_coincide_en_obras_y_en_postventa` | Borrar (primera mitad de R12) |
| `r4_r10_filas_de_la_pestana_obras`, `r4_r10_filas_de_la_pestana_postventa` | Borrar (R4 → F-076 R2, R3, R6, R7) |
| `r11_total_desviacion_y_estado_iguales_en_las_tres_hojas` | Borrar (R11 → F-076 R8, R12) |
| `r15_cursiva_solo_en_codigo_obra_y_pct_de_la_agregada` | Borrar (R15 → F-076 R11) |
| `r16_pct_de_la_agregada_fraccion_formato_y_sin_formulas` | Borrar (R16; «sin fórmulas» sigue en `test_f040_r16_sin_formulas`, que recorre las tres hojas) |
| `r5_obras_lleva_sus_lineas_en_orden_con_var_como_obra` | Adaptar: tuplas de 3, sin `var.agregada`; OMEGA → `["0200", "0150"]` |
| `r6_postventa_lleva_sus_lineas_en_orden_con_prefijo` | Adaptar: tuplas de 3; EPSILON → `["Postv-0702", "Postv-0705"]` |
| `r10_sin_carga_una_fila_vacia_en_cada_pestana` | Adaptar: `[("", "", None)]` (solo por `_filas`) |
| `r5_d5_var_en_obras_y_sumado_en_resto_obras` | Adaptar y renombrar `…_var_en_obras_y_nunca_en_postventa`: fuera la aserción RESTO OBRAS = 60 |
| `r18_el_prefijo_sale_de_la_configuracion` | Adaptar: ALFA Postventa = solo `("PV_0702", "PV_Hotel Inventado", 15)`; ALFA Obras acaba en `0102` |
| `r3_cabecera_autofiltro_paneles_anchos_e_impresion` (×2) | Adaptar: `max_row == 8` y `A2:I8` en las dos |
| `r13_valor_en_todas_las_filas_y_combinadas_con_la_agregada` | Adaptar y renombrar `…_y_combinadas_por_grupo`: `A3:A4` en Obras y `A4:A5` en Postventa |
| `r18_el_prefijo_de_la_configuracion_llega_al_libro` | Adaptar: Postventa C4/D4 = `PV_0702` / `PV_Hotel Inventado`; Obras C5 = `0101` |
| `r12_la_columna_pct_de_cada_grupo_suma_su_total_en_el_libro`, `r14_bandas_…`, `r21_celda_de_observaciones_…` | Cuerpo sin cambios: pasan con `_GRUPOS` nuevo; en r21 se quita el comentario «también en la agregada» |

Siguen **sin tocar**: `r1`, `r2`, `r12_la_columna_pct_del_grupo_suma_el_total`
(×2: con D1 = b la suma del grupo es su Total por construcción), `r17` y
`r20`. Recuento: 12 borradas, 8 adaptadas, 3 solo por los comunes, 5 sin
tocar. Ninguna aserción sobre «Detalle» se relaja.

### 6.2 `tests/test_f040_excel.py`

| Test | Destino |
|---|---|
| `test_f040_r2_titulo_en_fila_1_cabecera_en_2_datos_desde_3` | Adaptar: A3 esperado por hoja, Obras y Detalle «ALFA PRUEBA UNO», Postventa «GAMMA PRUEBA TRES» (el único con postventa en su muestra; DELTA va detrás) |

Docstring del módulo: «Obras» y «Postventa» solo con su parte. El resto del
fichero no cambia (Detalle intacto: r16-r19 siguen con el completo).

## 7. Verificación manual (humano, M1)

```powershell
curl.exe -o "$env:TEMP\f076.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"
start "$env:TEMP\f076.xlsx"
```

Con la api local (`python main.py` en `services/dedicacion-api`). Mirar:
sin aviso de reparación; en Obras y Postventa ninguna fila «RESTO …»; un
trabajador solo de postventa no está en Obras y viceversa; «SIN CARGA» en
las tres; un repartido con «FALTA» en cada pestaña y «OK» en Detalle; la
suma de lo filtrado por Empleado en una pestaña es su Total; Detalle con
todos. El resultado se anota en `progress/`.

## 8. Riesgos y alternativas descartadas

- **El filtro Estado ≠ OK de una pestaña ya no es la regla del 100 %**
  (D1 = b): todo trabajador repartido sale «FALTA» en las dos pestañas
  aunque esté al 100 %. Quien quiera los problemas reales filtra en
  «Detalle». El humano lo eligió así; se mira en M1.
- **La cabecera sigue diciendo «Total empleado»** en las pestañas, aunque es
  el total de esa parte. Cambiar el texto no se pidió (y F-040 R6 y los
  tests de cabecera lo fijan); si en M1 el humano quiere otro rótulo, es un
  cambio de una constante más sus tests, en otra iteración.
- **Contar trabajadores por pestaña** no da la plantilla: la completa está
  en «Detalle».
- **Quien leía el libro por posición o por nombre** de hoja no se rompe:
  siguen las tres hojas, también vacías (D3).
- **Total del completo en las pestañas (D1 a)**: descartado por el humano;
  dejaba la columna % del grupo por debajo de su Total.
- **Conservar `agregada` y `AGREGADA_EN_*` sin uso**: descartado (D5), como
  `filas_resumen` en F-045 §8: código sin consumidor; git lo guarda.
- **Filtrar por % (> 0) en vez de por línea**: descartado; una línea al 0 %
  existe en el cuadrante y en «Detalle», y esconderla aquí haría que las
  hojas discreparan sin que nadie lo pidiera.

## 9. Frontera

**¿Cruza la frontera del proyecto? No.** Ninguna llamada nueva, ningún
recurso compartido, ninguna ruta ni contrato nuevo: el Excel lo descarga el
usuario y `azure-apps/dedicacion.md` solo lo cita en el historial de
despliegues, sin describir su contenido. Ese historial lo actualiza el líder
al desplegar, como siempre; esta feature no toca `azure-apps`.

## 10. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Total empleado, Desviación y Estado en Obras y Postventa | (a) los del trabajador completo, como hoy (F-045 D9): iguales en las tres hojas; la columna % del grupo suma solo su parte; (b) los de la pestaña: Total = suma de la parte y Estado recalculado sobre él: un repartido al 100 % sale «FALTA»; (c) Total de la pestaña, Desviación y Estado del completo: Desviación ≠ Total − 100; (d) columna nueva «Total pestaña» junto a los del completo: diez columnas, Observaciones pasa a J | (a): el Estado sigue siendo la regla del 100 % y el filtro Estado ≠ OK no da falsos avisos; lo de la otra parte está en su hoja y en Detalle | (b) — humano, 2026-11-24 |
| D2 Trabajador sin carga | (a) «SIN CARGA» en las dos pestañas, como hoy (F-045 D3): un mes sin postventa saldría una Postventa solo con «SIN CARGA»; (b) en Obras y Detalle, no en Postventa; (c) solo en Detalle | (b): Postventa queda solo con postventa y el aviso de «sin cargar» sigue en la primera hoja | (a) — humano, 2026-11-24 |
| D3 Pestaña sin nadie (mes sin postventa) | (a) la hoja sale con título y cabecera, vacía; (b) ese mes no se crea | (a): el libro siempre tiene las mismas tres hojas, como ya pasa con un periodo vacío | (a) — humano, 2026-11-24 |
| D4 Criterio con los tests de F-045 | (a) borrar los de los R que mueren y adaptar los vigentes que fallan por datos; lo nuevo, en `test_f076` (§6); (b) adaptarlos todos en sitio, también los de R7-R9 reescritos al revés, sin fichero nuevo | (a): un `test_f045_r7_*` que comprueba lo contrario de R7 engaña la traza | (a) — humano, 2026-11-24 |
| D5 `LineaDetalle.agregada`, `AGREGADA_EN_*` y `_CURSIVA` | (a) se borran; (b) se conservan sin uso | (a): sin consumidor; git lo guarda (precedente F-045 §8) | (a) — humano, 2026-11-24 |
