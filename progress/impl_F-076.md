<!-- progress/impl_F-076.md -->
# F-076 · Informe del implementer (`estandar`)

Rama `feature/F-076-excel-sin-resto-de`. Spec aprobada el 2026-11-24 (D1 = b, D2-D5 = a). Solo `dedicacion-api`.

## Hecho

- **«Obras» lleva solo líneas de obra y «Postventa» solo de postventa.** Ya no hay línea agregada «RESTO POSTVENTA» / «RESTO OBRAS» (R2-R4).
- **Un trabajador con líneas, pero ninguna de una parte, no sale en esa pestaña** (R5). Basta una línea de esa parte, aunque esté al 0 %. Se respeta el orden de la API (R6).
- **«SIN CARGA» sigue en las dos pestañas y en «Detalle»** (R7, D2).
- **Total, Desviación y Estado de cada pestaña son los de esa parte** (R8, D1 = b). Se calculan como suma exacta en `Decimal` y con la regla del 100 % de `domain.estados`, sin umbral propio. Un trabajador repartido 85/15 sale «FALTA 15%» en Obras y «FALTA 85%» en Postventa.
- **Una pestaña sin nadie sale con título y cabecera**, autofiltro `A2:I2` (R9). No hizo falta código: ya lo hacía `exportar([])`.
- **Fuera la cursiva, `LineaDetalle.agregada` y `AGREGADA_EN_*`** (R11, D5).
- **«Detalle» no cambia** (R12): trabajador completo, con su total y su estado.
- **Docs sin «RESTO»** (R14), y nota de sustitución en `specs/F-045-excel-obras-postventa/requirements.md`.

## Tareas y commits

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `5dae66f` | `tests/test_f076_excel_sin_resto.py` (14 tests, 15 items), en rojo |
| T2 | `bfdd7b6` | `contenido.py`: `_grupo(fila, lineas, total, num)`, `grupos_pestana` nuevo, fuera `agregada` y `AGREGADA_EN_*` |
| T3 | `97b94d7` | `exporter.py`: fuera `_CURSIVA` y el bloque `if linea.agregada`; docstring |
| T4 | `dc29cf1` | `test_f045_excel_pestanas.py` según design §6.1 (y `_rgb` sin usar fuera del import de `test_f076`) |
| T5 | `280aa04` | `test_f040_excel.py`: `r2` y docstring (design §6.2) |
| T6 | `a84fae5` | `docs/ARCHITECTURE.md`, README de la api y nota en F-045 |
| T7 | — | MANUAL del humano (abajo) |
| T8 | — | `bash harness/init.sh` (abajo) |

Commits con rutas concretas. `infra/imagenes.json` (modificado por el despliegue del humano) no se ha tocado ni añadido.

## Ficheros

- `services/dedicacion-api/infrastructure/excel/contenido.py`, `exporter.py`.
- `services/dedicacion-api/tests/test_f076_excel_sin_resto.py` (nuevo), `test_f045_excel_pestanas.py`, `test_f040_excel.py`.
- `docs/ARCHITECTURE.md` (línea `excel/`), `services/dedicacion-api/README.md` (fila `export.xlsx`), `specs/F-045-excel-obras-postventa/requirements.md` (nota), `specs/F-076-excel-sin-resto-de/tasks.md` (casillas).
- No se tocan: `domain/`, `application/`, `interface_adapters/`, `config/`, `test_f039`, `test_f024`, front, transfer, `infra/` ni `azure-apps` (design §9: no cruza la frontera).

## Lista cerrada (design §6): medida, no supuesta

Primero se quitaron solo los imports `AGREGADA_EN_*` de `test_f045`, con T2 y T3 ya aplicados. Después se pasaron `test_f045`, `test_f040`, `test_f039`, `test_f024` y `test_f076`:
`27 failed, 113 passed`. Los fallos fueron:
- los **24 de F-045** que nombra §6.1, exactamente;
- **1 de F-040** (`test_f040_r2_…`);
- los 2 de `test_f076_r14`, que quedaban para T6.

Ninguno cayó fuera de la lista. F-039 y F-024 estaban en verde sin tocarlos.

En `test_f045` (28 funciones → 16):
- **Borradas (12):** `r4_mismos_…`, `r7_agregada_…`, `r7_suma_exacta_…`, `r8_…`, `r9_…`, `r11_…_completo`, `r12_la_suma_coincide_…`, `r4_r10_…_obras`, `r4_r10_…_postventa`, `r11_…_iguales_en_las_tres_hojas`, `r15_…` y `r16_…`.
- **Adaptadas (8):**
  - `r5`: OMEGA → `["0200","0150"]`.
  - `r6`: EPSILON sin «OBRAS».
  - `r10`: tuplas de 3.
  - `r5_d5`: renombrada `…_var_en_obras_y_nunca_en_postventa`, sin la aserción RESTO = 60.
  - `r18` de contenido: ALFA Obras acaba en `0102`.
  - `r3` (×2): `max_row` 8, `A2:I8`.
  - `r13`: renombrada `…_y_combinadas_por_grupo`, `A3:A4` en Obras y `A4:A5` en Postventa.
  - `r18` del libro: C4/D4 = `PV_0702`, Obras C5 = `0101`.
- **Solo por los cambios comunes (3):** `r12_…_en_el_libro`, `r14` y `r21` (en `r21` se quitó «también en la agregada» del comentario).
- **Comunes:** fuera los imports, `_filas` con tuplas de 3, `_GRUPOS` nuevo, fuera `_AGREGADAS` y `_empleados`, y docstring.
- **Sin tocar:** `r1`, `r2`, `r12_…_suma_el_total` (×2), `r17` y `r20`.

Ninguna aserción sobre «Detalle» se ha relajado.

## Fase RED (T1, contra el código de `8d6ec0f`)

Comando, desde `services/dedicacion-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f076_excel_sin_resto.py -q -p no:cacheprovider --tb=line
```

Salida real (una línea por fallo; la traza de r9 sacada de `--tb=short`):

```
test_f076_excel_sin_resto.py:132: AssertionError: assert [('0101', 'Ob...ecimal('15'))] == [('0101', 'Ob...ecimal('25'))]   # r2: ALFA Obras trae RESTO POSTVENTA 15
test_f076_excel_sin_resto.py:150: AssertionError: assert [('Postv-0702...ecimal('85'))] == [('Postv-0702...ecimal('15'))]   # r3: ALFA Postventa trae RESTO OBRAS 85
test_f076_excel_sin_resto.py:169: AssertionError: ALFA PRUEBA UNO                         # r4: código «POSTVENTA» en el grupo
test_f076_excel_sin_resto.py:188: AssertionError: assert 'GAMMA PRUEBA TRES' not in {...}   # r5: GAMMA sale en Obras
test_f076_excel_sin_resto.py:208: AssertionError: assert ['ALFA PRUEBA...PRUEBA CINCO'] == [...]   # r6: orden con todos
test_f076_excel_sin_resto.py:232: AssertionError: Obras                                   # r7: DELTA no está en la fila 7
test_f076_excel_sin_resto.py:243: AssertionError: assert [('ALFA PRUEB...'EXCESO 10%')] == [('ALFA PRUEB... 'FALTA 40%')]   # r8: total del completo
>       assert postv.max_row == 2
E       assert 3 == 2                                                                     # r9: BETA sale con RESTO OBRAS
test_f076_excel_sin_resto.py:309: AssertionError: ('Obras', 'A', 4)                       # r10: bandas desplazadas
test_f076_excel_sin_resto.py:325: AssertionError: ('Obras', 'C5')                         # r11: cursiva en la agregada
test_f076_excel_sin_resto.py:358: AssertionError: OBRAS                                   # r13: «OBRAS» sin prefijo en Postventa
test_f076_excel_sin_resto.py:375: AssertionError: assert 'otra parte en una línea' not in '<!-- docs/A...'   # r14 ARCHITECTURE
test_f076_excel_sin_resto.py:374: AssertionError: assert 'RESTO' not in '<!-- README...'                      # r14 README
13 failed, 2 passed in 1.08s
```

Pasan en RED, y es lo esperado: `r1` (las tres hojas y su cabecera ya existían) y `r12` (Detalle no cambia; es la guarda de regresión). Todos los fallos son de aserción, ninguno de import. Una primera versión de `r12` falló en RED por leer F/G/H de las no ancla con `load_workbook`, que las vacía. Era un error del test, no del código: se corrigió leyéndolas del XML (`_fgh`) antes del commit de T1.

Verde tras T2-T6:

```
.venv/Scripts/python.exe -m pytest tests/test_f076_excel_sin_resto.py -q -p no:cacheprovider
15 passed in 2.33s
.venv/Scripts/python.exe -m pytest tests/test_f045_excel_pestanas.py -q -p no:cacheprovider
18 passed in 1.57s
.venv/Scripts/python.exe -m pytest tests/test_f040_excel.py tests/test_f039_registro_var.py tests/test_f024_rutas_empresa.py -q -p no:cacheprovider
95 passed, 1 warning in 12.04s
```

## Desviaciones (para el reviewer)

1. **Orden de verificación de T2/T3.** La verificación de T2 (`-k "r2 … r12"`) no puede correr sola. `test_f076` importa `_muestra` de `test_f045`, que no colecciona sin quitar los `AGREGADA_EN_*` (§6 lo anticipa), y el libro necesita T3. T2 y T3 se commitearon por separado. Su verificación se hizo tras quitar esos imports, como primer paso de T4: 13/13 de r1-r13 en verde, en la medición de arriba.
2. **`_rgb`.** El design §5 dice que `test_f076` lo reutiliza, pero ningún test lo necesita: se quitó del import (ruff F401).
3. **`test_f076_r4` comprueba también D5**: que no existan `LineaDetalle.agregada` ni `AGREGADA_EN_*`.
4. **Ruff I001** en los imports de `test_f076`, `test_f045` y `exporter.py`: es el mismo aviso que ya tenían `test_f045` y `exporter.py` antes (deuda previa, mismo estilo de bloque). No se reordena.

## MANUAL pendiente (T7, humano)

M1 (design §7). Con la api local (`python main.py` en `services/dedicacion-api`):

```powershell
curl.exe -o "$env:TEMP\f076.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"
start "$env:TEMP\f076.xlsx"
```

Qué mirar:
- que no salga el aviso de reparación;
- que no haya ninguna fila «RESTO …»;
- que quien solo tiene postventa no esté en Obras, y viceversa;
- que salga «SIN CARGA» en las tres hojas;
- que un trabajador repartido salga «FALTA» en cada pestaña y «OK» en Detalle;
- que lo filtrado por Empleado en una pestaña sume su Total;
- que Detalle tenga a todos;
- visto bueno a la cabecera «Total empleado» en las pestañas (design §8).

El resultado se anota en `progress/`.

## Salida de `bash harness/init.sh` (T8)

Ejecutado tal cual el 2026-11-24, con código de salida 0 y ningún `[KO]`. Líneas clave:

```
[AVISO] ruff: 439 avisos (deuda previa, no bloquea).
2319 passed, 47 skipped in 602.35s (0:10:02)
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/dedicacion-api): pytest en verde (caché: … verde del 2026-11-24 16:54)
[OK] servicio front …: pytest en verde (caché)
[OK] servicio transfer …: pytest en verde (caché)
[OK] PUERTA COBERTURA: 100.0% de 4 líneas cambiadas cubiertas (4/4, umbral 80% (global), nivel estandar; diff desde 2eac660ed0, merge-base con dev)
[OK] PUERTA TAMAÑO: F-076 dentro de los topes (requirements 119/150, design 248/250, impl 141/220)
[OK] PUERTA CARRIL: N/A (F-076 es de nivel estandar: no declara límites)
[OK] CAPA E2E: N/A (ningún servicio declara el bloque e2e)
[OK] Rama actual: feature/F-076-excel-sin-resto-de
ENTORNO LISTO. Puedes trabajar.
```

La suite de la api salió de caché. Para comprobarlo, se lanzó sin caché desde `services/dedicacion-api`, con `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`: `1695 passed, 1 warning in 27.76s`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz `2319 passed, 47 skipped`; api `1695 passed` (de ellos, 15 items de `test_f076`, 18 de `test_f045` y 95 de F-040/F-039/F-024) |
| Cobertura de las líneas cambiadas | 100,0 % (4/4), según `PUERTA COBERTURA` |
| Mutantes generados / supervivientes | No lanzada: la campaña va en la pasada tras el APPROVED. En `estandar` es informativa (`harness/rigor.json`) |
| Tiempo de la suite | raíz 602,35 s; api 27,76 s |
| Capa e2e | N/A (`CAPA E2E: N/A`, ningún servicio declara e2e) |

**Pendiente para cerrar:**
- la review;
- la pasada de campaña de mutación (informativa);
- la MANUAL M1 (T7) del humano.

## Vuelta de la review, pasada 1 (CHANGES_REQUESTED, punto 2)

En `test_f045_excel_pestanas.py`, los huecos de las funciones borradas en T4 dejaban más de dos líneas en blanco (l. 115, 126, 142, 191, 235 y 293).

- **Arreglo:** `ruff check --select E3 --preview --fix`. Solo se quitan 12 líneas en blanco; no cambia ninguna aserción.
- **Ahora:** `ruff check --select E3 --preview` da 0 avisos y `pytest tests/test_f045_excel_pestanas.py` da `18 passed in 1.48s`.
- **Pendiente:** el `init.sh` completo queda para la pasada 2.
