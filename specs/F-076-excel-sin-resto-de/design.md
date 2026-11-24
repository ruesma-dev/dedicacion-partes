<!-- specs/F-076-excel-sin-resto-de/design.md -->
# F-076 · Diseño: pestañas Obras y Postventa sin «RESTO …»

**Rigor: `estandar`.** No cumple ningún disparador de `critico` de «Niveles
de rigor» (`CHECKPOINTS.md`): no escribe en Sigrid ni en la base, no cambia
contratos ni esquema; solo cambia qué filas pinta el Excel descargado.

Parte del libro de F-045 (`specs/F-045-excel-obras-postventa/design.md`
§3): cambia **qué grupos y qué líneas** llevan «Obras» y «Postventa»;
«Detalle», el formato, la columna I y el contrato del exportador, no.

## 1. Encaje en la arquitectura y límite de servicio

- **Solo `dedicacion-api`, capa `infrastructure/excel/`.** La ruta
  `export.xlsx` sigue llamando a `ObtenerCuadrante` y pasando `periodo` y
  `filas` al exportador. Cada `Linea` trae ya `es_postventa`: no hace falta
  dato nuevo, ni ORM, ni SQL, ni `config.yaml`.
- Es **presentación**: el total del trabajador sigue siendo
  `CuadranteTrabajador.total` y el estado sigue saliendo de `domain.estados`.
  El front solo descarga el fichero; el transfer no interviene. Ninguna
  responsabilidad nueva fuera de la api; ninguna copia entre servicios.
- **F-038** (cuadro de mando «que sea el Excel», sin empezar) pensaba
  reutilizar `grupos_pestana`: heredará el comportamiento nuevo, que es el
  que quiere negocio.

## 2. Ficheros

**Crear**

| Ruta | Qué |
|---|---|
| `services/dedicacion-api/tests/test_f076_excel_sin_resto.py` | Tests de R1-R14 (§5) |

**Modificar**

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | `grupos_pestana` sin agregada y filtrando trabajadores (§3.1); fuera `LineaDetalle.agregada` y `AGREGADA_EN_*` [D5]; docstrings |
| `services/dedicacion-api/infrastructure/excel/exporter.py` | Fuera `_CURSIVA` y el bloque `if linea.agregada` [D5]; docstring del módulo (§3.2) |
| `services/dedicacion-api/tests/test_f045_excel_pestanas.py` | Lista cerrada de §6.1 |
| `services/dedicacion-api/tests/test_f040_excel.py` | Lista cerrada de §6.2 |
| `docs/ARCHITECTURE.md` | Línea 79, `excel/`: «Obras y Postventa agrupadas por trabajador, cada una solo con sus líneas (sin línea agregada de la otra parte)» (R14) |
| `services/dedicacion-api/README.md` | Fila `export.xlsx` (línea 45): ídem, sin «RESTO» (R14) |
| `specs/F-045-excel-obras-postventa/requirements.md` | Una nota bajo el título: «D3, D4, D6, D7 y R4, R7-R9, R12, R15, R16 sustituidos por F-076» |

**No se tocan**: `domain/` (`estados.py`, `models.py`, `ports.py`),
`application/`, `interface_adapters/api/` (`routes.py`, `deps.py`),
`config/config.yaml`, `orm_models.py`, `repositories.py`,
`requirements.txt`, `grupos_detalle` y `_grupo` de `contenido.py`,
`_hoja_grupos` salvo la cursiva, `_rematar`, `_titulo_y_cabecera`,
`tests/test_f024_rutas_empresa.py` (exportador falso),
`tests/test_f039_registro_var.py` (su trabajador solo tiene obra: sigue en
la fila 3 de «Obras»), el front, el transfer, `infra/` y `azure-apps/`.
Sin SQL.

## 3. Clases y funciones

### 3.1 `infrastructure/excel/contenido.py` (infrastructure, puro)

```python
@dataclass(frozen=True)
class LineaDetalle:               # sin el campo `agregada` [D5]
    codigo: str
    obra: str
    nombre: str
    porcentaje: Decimal | None

def grupos_pestana(filas, prefijo, postventa: bool) -> list[GrupoTrabajador]  # firma igual
```

`grupos_pestana`, por trabajador, en el orden de entrada (R6):

1. `propias` = sus líneas con `ln.es_postventa == postventa`, pasadas por
   `_linea_detalle` (prefijo de F-040 R8) (R2, R3). Nada más: ni suma ni
   línea agregada (R4).
2. Si `propias` no está vacía → `_grupo(fila, propias)`.
3. Si está vacía y el trabajador **tiene** líneas (todas de la otra parte)
   → no sale en esta pestaña (R5).
4. Si no tiene líneas (sin carga) → `[D2]`: con (b), `_grupo(fila, [])`
   (la `_LINEA_VACIA` de F-040 R9) solo si `not postventa` (R7). Con (a),
   en las dos; con (c), en ninguna.
5. Total, desviación y estado salen de `_grupo`, sin cambios: los del
   trabajador completo `[D1]` = (a) (R8). `_grupo` usa `fila.total` y
   `len(fila.lineas)`, no las líneas del grupo, así que no hay que tocarlo.

El criterio de R5 es **por línea**: una línea de esa parte al 0 % hace salir
al trabajador (con ese 0 %), igual que hoy en «Detalle».

### 3.2 `infrastructure/excel/exporter.py`

- Se borran `_CURSIVA` y, en `_hoja_grupos`, las tres líneas
  `if linea.agregada: … font = _CURSIVA` (R11). Nada más cambia en el
  pintado: bandas por índice `n` del grupo **en esa hoja** (R10), combinadas
  `_COMBINADAS` en grupos de más de una fila, columna I igual.
- Con cero grupos, `_hoja_grupos` ya deja título y cabecera y `_rematar`
  pone `A2:I2` (`max(ultima, 2)`): es lo que hoy sale con `exportar([])`
  (R9, [D3] = (a)). No hace falta código.
- Docstring del módulo: «Obras» y «Postventa» llevan solo las líneas de su
  parte y solo los trabajadores que tienen alguna; Total, Desviación y
  Estado, los del trabajador completo; sin línea agregada.

## 4. Qué sale con la muestra de `test_f045` (D1 = a, D2 = b)

`_muestra()`: ALFA (0101 60, 0102 25, Postv-0702 15; OK), BETA (0101 50,
0103 40; FALTA 10 %), GAMMA (Postv 70 y 30; OK), DELTA (sin carga),
EPSILON (VAR-29 60, Postv 30 y 20; EXCESO 10 %).

| Hoja | Grupos (filas) | Última fila |
|---|---|---|
| Obras | ALFA 3-4, BETA 5-6, DELTA 7 («SIN CARGA»), EPSILON 8 | 8 |
| Postventa | ALFA 3, GAMMA 4-5, EPSILON 6-7 | 7 |
| Detalle | sin cambios: 3-5, 6-7, 8-9, 10, 11-13 | 13 |

En «Obras», ALFA suma 85 % en la columna % y lleva Total 100 % y Estado OK;
en «Postventa», 15 % con Total 100 % y OK (R8). Con D2 = (a), DELTA va
también en la fila 6 de Postventa y EPSILON pasa a 7-8; con (c), DELTA no
está en Obras y EPSILON pasa a 7.

## 5. Tests nuevos: `tests/test_f076_excel_sin_resto.py` (sin red ni BBDD)

Reutiliza `_fila`, `_linea`, `_rgb` y `_xml_hoja` de `test_f040_excel` y
`_muestra` de `test_f045_excel_pestanas` (importados, no copiados).

| Test | Qué fija |
|---|---|
| `test_f076_r1_tres_hojas_con_su_cabecera_y_autofiltro` | Nombres y orden; fila 2 = las 9 cabeceras; `A2:I<max_row>` en las tres |
| `test_f076_r2_obras_solo_lineas_de_obra` | Contenido y libro: ALFA `0101`, `0102`; EPSILON solo `VAR-29`; ningún Código con prefijo |
| `test_f076_r3_postventa_solo_lineas_de_postventa` | ALFA solo `Postv-0702`; todo Código empieza por el prefijo |
| `test_f076_r4_ninguna_linea_agregada` | En Obras y Postventa ningún Código «POSTVENTA»/«OBRAS» ni Obra que empiece por «RESTO»; contenido y libro |
| `test_f076_r5_sin_nada_de_esa_parte_no_sale` | GAMMA no está en Obras, BETA no está en Postventa (columna A por XML); una línea de postventa al 0 % sí lo hace salir |
| `test_f076_r6_orden_de_la_api_en_cada_pestana` | Con la muestra y con ella invertida: orden de entrada menos los de R5 |
| `test_f076_r7_sin_carga_en_obras_y_detalle_no_en_postventa` | DELTA: una fila «SIN CARGA» en Obras y Detalle; ausente en Postventa [D2] |
| `test_f076_r8_total_desviacion_estado_del_trabajador_completo` | Por Empleado, F, G y H iguales a Detalle en las dos pestañas; ALFA en Obras: % suma 0,85 y Total 1 [D1] |
| `test_f076_r9_pestana_sin_nadie_solo_cabecera` | Mes sin postventa: Postventa con título, cabecera, `max_row == 2`, `A2:I2`; Obras con sus filas |
| `test_f076_r10_bandas_y_combinadas_por_pestana` | Postventa: ALFA blanco, GAMMA azul (cuenta propia de la hoja), `medium` bajo cada grupo, rangos combinados exactos |
| `test_f076_r11_ninguna_cursiva` | Ninguna celda de las tres hojas con `font.italic` |
| `test_f076_r12_detalle_con_todos` | Detalle: los cinco trabajadores y las 11 filas de F-045 R17, también GAMMA y BETA |
| `test_f076_r13_prefijo_de_la_configuracion` | Con «PV_»: Postventa `PV_0702`; Obras sin «PV_» |
| `test_f076_r14_docs_sin_resto` | `docs/ARCHITECTURE.md` y el README de la api no contienen «RESTO» ni «otra parte en una línea» |

## 6. Lista CERRADA de tests anteriores que cambian [D4] = (a)

Medida el 2026-11-24 simulando `grupos_pestana` nuevo (D2 = b) sobre la
rama: fallan **26** tests (25 de F-045 y 1 de F-040); los de F-039 y F-024
quedan en verde. Criterio: **se borra** el test cuyo requisito de F-045
muere (su cobertura pasa a `test_f076`); **se adapta** el que sigue vigente
y solo falla por los datos. Fuera de esta lista o de este criterio: **PARA**.

### 6.1 `tests/test_f045_excel_pestanas.py`

Comunes: fuera los imports `AGREGADA_EN_*`; `_filas` sin `ln.agregada`;
`_GRUPOS` = los de §4; fuera `_AGREGADAS`; `_empleados` hasta la última fila
de `_GRUPOS[nombre]` (no `range(3, 12)`); docstring del módulo.

| Test | Destino |
|---|---|
| `r4_mismos_trabajadores_y_orden_en_las_dos_pestanas` | Borrar (R4 → F-076 R6) |
| `r7_agregada_unica_al_final_con_rotulos_y_suma`, `r7_suma_exacta_en_decimal` | Borrar (R7) |
| `r8_sin_la_otra_parte_no_hay_agregada` | Borrar (R8 → F-076 R4; hoy pasa, rompe al quitar `agregada`) |
| `r9_solo_la_otra_parte_una_fila_agregada` | Borrar (R9 → F-076 R5) |
| `r12_la_columna_pct_del_grupo_suma_el_total` (×2), `r12_la_suma_coincide_en_obras_y_en_postventa`, `r12_…_suma_su_total_en_el_libro` | Borrar (R12) |
| `r4_r10_filas_de_la_pestana_obras`, `r4_r10_filas_de_la_pestana_postventa` | Borrar (R4 → F-076 R2, R3, R6, R7) |
| `r15_cursiva_solo_en_codigo_obra_y_pct_de_la_agregada` | Borrar (R15 → F-076 R11) |
| `r16_pct_de_la_agregada_fraccion_formato_y_sin_formulas` | Borrar (R16; «sin fórmulas» sigue en `test_f040_r16_sin_formulas`, que recorre las tres hojas) |
| `r5_obras_lleva_sus_lineas_en_orden_con_var_como_obra` | Adaptar: OMEGA → `["0200", "0150"]` |
| `r6_postventa_lleva_sus_lineas_en_orden_con_prefijo` | Adaptar: EPSILON → `["Postv-0702", "Postv-0705"]` |
| `r10_sin_carga_una_fila_vacia_en_cada_pestana` | Adaptar [D2]: en Obras la fila vacía; en Postventa, DELTA ausente |
| `r11_total_desviacion_y_estado_del_trabajador_completo` | Adaptar: emparejar por Empleado, no por posición |
| `r5_d5_var_en_obras_y_sumado_en_resto_obras` | Adaptar y renombrar `…_var_en_obras_y_nunca_en_postventa`: fuera la aserción de RESTO OBRAS = 60 |
| `r18_el_prefijo_sale_de_la_configuracion` | Adaptar: ALFA Postventa = solo `PV_0702`; ALFA Obras acaba en `0102` |
| `r3_cabecera_autofiltro_paneles_anchos_e_impresion` (×2) | Adaptar: `max_row` y autofiltro por hoja (8 y 7) |
| `r11_total_desviacion_y_estado_iguales_en_las_tres_hojas` | Adaptar: emparejar con Detalle por Empleado; G = Obras `[0, -0.1, None, ≈0.1]`, Postventa `[0, 0, ≈0.1]` |
| `r13_valor_en_todas_las_filas_y_combinadas_con_la_agregada` | Adaptar y renombrar `…_y_combinadas_por_grupo`: `A3:A4` en Obras y `A4:A5` en Postventa |
| `r18_el_prefijo_de_la_configuracion_llega_al_libro` | Adaptar: Postventa C4/D4 = `PV_0702` / `PV_Hotel Inventado`; Obras C5 = `0101` |
| `r14_bandas_…`, `r21_celda_de_observaciones_…` | Sin cambiar el cuerpo: pasan con `_GRUPOS` nuevo; en r21, el comentario «también en la agregada» se quita |

Siguen **sin tocar**: `r1`, `r2`, `r17`, `r20`. Ninguna aserción sobre
«Detalle» se relaja.

### 6.2 `tests/test_f040_excel.py`

| Test | Destino |
|---|---|
| `test_f040_r2_titulo_en_fila_1_cabecera_en_2_datos_desde_3` | Adaptar: A3 esperado por hoja, Obras y Detalle «ALFA PRUEBA UNO», Postventa «GAMMA PRUEBA TRES» (el único con postventa en su muestra) |

Docstring del módulo: «Obras» y «Postventa» solo con su parte. El resto del
fichero no cambia.

## 7. Verificación manual (humano, M1)

```powershell
curl.exe -o "$env:TEMP\f076.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"
start "$env:TEMP\f076.xlsx"
```

Con la api local (`python main.py` en `services/dedicacion-api`). Mirar:
sin aviso de reparación; en Obras y Postventa ninguna fila «RESTO …»; un
trabajador solo de postventa no está en Obras y viceversa; Detalle con
todos; filtro Estado ≠ OK con los mismos trabajadores problemáticos en las
tres hojas (los que aparecen); y si Total/Estado se leen bien según D1.
El resultado se anota en `progress/`.

## 8. Riesgos y alternativas descartadas

- **La columna % de un grupo ya no suma su Total** (con D1 = a): ALFA sale
  con 60 + 25 = 85 % y Total 100 % OK. Es lo coherente con «en obra solo
  obra», y el Estado sigue diciendo la verdad del trabajador. Se avisa al
  humano en D1 y se mira en M1.
- **Contar trabajadores por pestaña** deja de dar la plantilla: el número
  de cada pestaña es el de quien tiene algo de esa parte. La plantilla
  completa está en «Detalle».
- **Quien leía el libro por posición o por nombre** de hoja no se rompe:
  siguen las tres hojas, también vacías (D3).
- **Conservar `agregada` y `AGREGADA_EN_*` sin uso**: descartado (D5), como
  `filas_resumen` en F-045 §8: código sin consumidor; git lo guarda.
- **Filtrar por % (> 0) en vez de por línea**: descartado; una línea al 0 %
  existe en el cuadrante y en «Detalle», y esconderla aquí haría que las
  hojas discreparan sin que nadie lo pidiera.
- **Recalcular el Estado por pestaña (D1 b)**: un trabajador al 100 %
  repartido saldría «FALTA 15 %» en una hoja y «FALTA 85 %» en la otra; el
  filtro Estado ≠ OK se llenaría de falsos avisos.

## 9. Frontera

**¿Cruza la frontera del proyecto? No.** Ninguna llamada nueva, ningún
recurso compartido, ninguna ruta ni contrato nuevo: el Excel lo descarga el
usuario y `azure-apps/dedicacion.md` solo lo cita en el historial de
despliegues, sin describir su contenido. Ese historial lo actualiza el líder
al desplegar, como siempre; esta feature no toca `azure-apps`.

## 10. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Total empleado, Desviación y Estado en Obras y Postventa | (a) los del trabajador completo, como hoy (F-045 D9): iguales en las tres hojas; la columna % del grupo suma solo su parte; (b) los de la pestaña: Total = suma de la parte y Estado recalculado sobre él: un repartido al 100 % sale «FALTA»; (c) Total de la pestaña, Desviación y Estado del completo: Desviación ≠ Total − 100; (d) columna nueva «Total pestaña» junto a los del completo: diez columnas, Observaciones pasa a J | (a): el Estado sigue siendo la regla del 100 % y el filtro Estado ≠ OK no da falsos avisos; lo de la otra parte está en su hoja y en Detalle | |
| D2 Trabajador sin carga | (a) «SIN CARGA» en las dos pestañas, como hoy (F-045 D3): un mes sin postventa saldría una Postventa solo con «SIN CARGA»; (b) en Obras y Detalle, no en Postventa; (c) solo en Detalle | (b): Postventa queda solo con postventa y el aviso de «sin cargar» sigue en la primera hoja | |
| D3 Pestaña sin nadie (mes sin postventa) | (a) la hoja sale con título y cabecera, vacía; (b) ese mes no se crea | (a): el libro siempre tiene las mismas tres hojas, como ya pasa con un periodo vacío | |
| D4 Criterio con los tests de F-045 | (a) borrar los de los R que mueren y adaptar los vigentes que fallan por datos; lo nuevo, en `test_f076` (§6); (b) adaptarlos todos en sitio, también los de R7-R9 reescritos al revés, sin fichero nuevo | (a): un `test_f045_r7_*` que comprueba lo contrario de R7 engaña la traza | |
| D5 `LineaDetalle.agregada`, `AGREGADA_EN_*` y `_CURSIVA` | (a) se borran; (b) se conservan sin uso | (a): sin consumidor; git lo guarda (precedente F-045 §8) | |
