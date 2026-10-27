<!-- progress/impl_F-065.md -->
# F-065 · informe del implementer

La ficha de incidencia activa que se queda a 0 sale en su sitio por letra (y
nombre), no al final. `sdd: false`, rigor estándar, solo front. Es la O1 de
`progress/review_F-063.md`. Rama `feature/F-065-ficha-activa-en-su-sitio`
(desde `dev` `c82171c`; alta en `9672f6d`), worktree `porcentajes-f065` (los
tres `.venv` enlazados con junction a la copia principal, sin versionar).

## Qué cambió

| Commit | Tarea | Ficheros |
|---|---|---|
| `27c36da` | T1 · tests (fase RED: 3 en rojo) | `services/dedicacion-front/tests/test_f065_ficha_activa_en_su_sitio.py` (nuevo) |
| `6abe00d` | T2 · la activa entra antes de ordenar | `services/dedicacion-front/static/js/app.js` |
| (este) | campaña, informe y rastro | `progress/mutacion_manual_F-065.md` (nuevo), `progress/current.md`, este informe |

En `app.js` (+9 / −8):

- `tiposIncidenciaDelMes(trabajadores, activo)`: segundo parámetro opcional,
  el tipo de la ficha activa (`{codigo, letra, nombre}` o `null`). Tras
  contar, si el mes ya no tiene ese código, entra en el mapa con `n: 0`
  **antes** del `sort`, así que sale ordenado como los demás (letra con
  `localeCompare` «es», desempate por nombre).
- `renderCabecera`: llama a `tiposIncidenciaDelMes(state.trabajadores,
  activa)` y pinta lo que devuelve; desaparece el `tipos.push` que la añadía
  después de ordenar.

No cambia nada más del filtro (conteo, filtrado, clics, cambio de mes), ni la
api, el transfer, el CSS, el README ni ningún test existente. `azure-apps/`
no cambia (no cambia lo que se expone ni se consume).

## Decisiones

- **El orden vive en un solo sitio**: el comparador sigue solo en
  `tiposIncidenciaDelMes`. En vez de sacar un comparador y reordenar en
  `renderCabecera` (dos `sort`, y una función nueva que el arnés de F-063 no
  carga), la activa entra en el mapa antes del único `sort`. Lo fija el
  estático `el_orden_de_las_fichas_vive_en_un_solo_sitio` (`renderCabecera`
  sin `localeCompare`, `.sort(` ni `tipos.push(`).
- **La siembra va DESPUÉS del conteo y solo si el código no está**: si la
  activa sigue presente, su ficha es la del conteo (su letra y nombre los de
  los datos), exactamente como antes; si no, la del filtro con 0, como antes.
  Mismo contenido que F-063, distinta posición.
- **Parámetro, no `state`**: `tiposIncidenciaDelMes` sigue pura (no lee
  `state` ni llama a la api) y no nombra `filtroIncidencia`: el límite de
  F-063 (`el_filtro_solo_vive_en_la_cabecera_y_el_filtrado`) sigue en verde
  sin tocarlo. Las llamadas de un solo argumento (la del test de F-063)
  funcionan igual.
- **Tests sobre el arnés de F-063**: el fichero nuevo importa de
  `test_f063_filtro_incidencia.py` el arnés de node y los dobles (forma de
  `TrabajadorOut`/`LineaOut`/`IncidenciaOut`, claves opcionales a `null`,
  `quitada` siempre), como hacen otros tests del front (`from tests.…`).
- Ningún texto nuevo nombra motivos de conflicto.

## Fase RED (T1, antes de tocar `app.js`)

Tests escritos sobre `9672f6d` (sin código de F-065). Comando, desde
`services/dedicacion-front`:

```
.venv/Scripts/python.exe -m pytest tests/test_f065_ficha_activa_en_su_sitio.py -q -p no:cacheprovider --tb=line
```

Salida real:

```
FF.F                                                                     [100%]
================================== FAILURES ===================================
E   AssertionError: assert ['6 trabajado...rmiso 1', ...] == ['6 trabajado...medad 0', ...]
      At index 5 diff: 'P Permiso 1' != 'B Enfermedad 0'
C:\...\tests\test_f065_ficha_activa_en_su_sitio.py:50: AssertionError
E   AssertionError: assert ['P Permiso 1...Vacaciones 0'] == ['P Permiso 1...o anterior 1']
      At index 1 diff: 'V Vacaciones año anterior 1' != 'V Vacaciones 0'
C:\...\tests\test_f065_ficha_activa_en_su_sitio.py:70: AssertionError
E   AssertionError: tipos.push(
    assert 'tipos.push(' not in 'function re...isibles`).\n'
      'tipos.push(' is contained here:
            tipos.push({ ...activa, n: 0 });
C:\...\tests\test_f065_ficha_activa_en_su_sitio.py:92: AssertionError: tipos.push(
=========================== short test summary info ===========================
FAILED tests/test_f065_ficha_activa_en_su_sitio.py::test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final
FAILED tests/test_f065_ficha_activa_en_su_sitio.py::test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra
FAILED tests/test_f065_ficha_activa_en_su_sitio.py::test_f065_r1_el_orden_de_las_fichas_vive_en_un_solo_sitio
3 failed, 1 passed in 0.64s
```

El índice 5 es la primera ficha de incidencia (detrás de las cinco de
estado): con el código de antes salía «P Permiso 1» y «B Enfermedad 0» iba al
final. El que pasa en RED es la guarda `sin_filtro_activo_la_fila_no_cambia`
(los demás casos no cambian: tiene que estar en verde antes y después; la
mutación demuestra que muerde, N6 y N11). Tras T2:
`.venv/Scripts/python.exe -m pytest tests/test_f065_ficha_activa_en_su_sitio.py tests/test_f063_filtro_incidencia.py -q -p no:cacheprovider`
⇒ `20 passed in 2.97s` (los 16 de F-063 sin tocar sus aserciones).

## Tests (`test_f065_ficha_activa_en_su_sitio.py`, 4; sin red ni BBDD)

Código REAL de `app.js` en node con el DOM de mentira de F-063; el test pulsa
las fichas como el usuario.

- `la_activa_a_0_sale_por_letra_y_no_al_final`: con los datos de F-063, clic
  en «B Enfermedad 1» (fila igual que sin filtro: ni duplicada ni movida),
  se quitan las enfermedades del mes y se repinta: «B Enfermedad 0»,
  recuadrada, delante de «P» y «V», tabla vacía; otro clic la quita y las
  demás siguen en su orden.
- `la_activa_a_0_desempata_por_nombre_con_la_misma_letra`: «V Vacaciones»
  activa a 0 con «V Vacaciones año anterior» (otro código) y «P» presentes:
  P, V Vacaciones 0, V Vacaciones año anterior.
- `sin_filtro_activo_la_fila_no_cambia`: guarda de «los demás casos».
- `el_orden_de_las_fichas_vive_en_un_solo_sitio`: estático (arriba).

## Mutación manual del JS

`harness.mutacion` solo muta Python; la campaña manual, reproducible, está en
`progress/mutacion_manual_F-065.md` (SHA completo, línea base, workers,
tiempo, una fila por mutante y el script). Sobre
`6abe00dc656c81da38a8ea9479e9e8dcaa9fcf13`, 1 worker, 76,9 s: **12
mutantes, 11 muertos, 1 superviviente**.

- **N2** reintroduce el fallo de antes (la activa después de ordenar, dentro
  de la función): lo matan solo los dos tests nuevos de posición, que es
  justo el hueco que señalaba la O1.
- **N10** (guardar la activa con la letra como clave del mapa en vez del
  código) sobrevive y es **equivalente**: la clave es interna, la siembra va
  tras el conteo y solo si el código falta, y lo que sale son los valores.
  Solo cambiaría con un código de incidencia de una letra igual a la letra de
  la activa, que la api no sirve (códigos de catálogo, `CIV`, `CIE`…).
  Análisis completo en la campaña.

## Pendiente (MANUAL)

La comprobación en el navegador, **en local** (llevar una ficha a 0 exige
quitar una incidencia en el editor, que escribe en la BBDD de la app; a
Sigrid no va nada): pasos exactos en `progress/current.md`, «⚠ Lo que espera
al humano», entrada F-065 (detrás de la de F-063).

## Fuera del alcance

- Cualquier otro cambio del filtro de F-063 (conteo, filtrado, varias
  activas a la vez).
- F-066 (la regla «baja sin carga» en una sola función): otra feature.
- Desplegar: lo decide el humano tras la review (siguiente despliegue del
  front).

## Evidencias

`bash harness/init.sh` tal cual, solo, sobre `6abe00d` más este papeleo
(2026-10-27), tras borrar `.arnes_cache/suite_api.ok`, `suite_front.ok` y
`suite_transfer.ok` para que las tres suites corrieran de verdad: termina en
«ENTORNO LISTO. Puedes trabajar.», **sin ningún [KO]** (solo el [AVISO] de
ruff, 309, deuda previa).

| Evidencia | Valor real |
|---|---|
| Tests de la raíz | 418 passed, 1 skipped en 83,99 s |
| Tests de la api | 1308 passed en 118,50 s |
| Tests del front | 434 passed en 93,87 s (430 de antes + 4 de F-065; los 16 de F-063 sin tocar) |
| Tests del transfer | 1585 passed en 54,19 s |
| Tests de F-063 + F-065 sueltos | 20 passed en 2,97 s |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de producción frente a dev)`; el JS no tiene medidor de cobertura |
| Mutantes | `harness.mutacion` no aplica (no hay Python de producción). Campaña manual del JS (`progress/mutacion_manual_F-065.md`, `6abe00dc656c81da38a8ea9479e9e8dcaa9fcf13`, 1 worker, 76,9 s): **12 generados, 11 muertos, 1 superviviente** (N10, equivalente, analizado) |
| Tamaño | `PUERTA TAMAÑO: F-065 dentro de los topes (impl 147/220)` |
