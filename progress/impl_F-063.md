<!-- progress/impl_F-063.md -->
# F-063 · informe del implementer

Fichas por tipo de incidencia en la fila del resumen, que filtran la tabla
como las de estado. `sdd: false`, rigor estándar, solo front. Rama
`feature/F-063-filtro-por-incidencia` (desde `dev` `b8c78b7`), worktree
`porcentajes-f063` (los tres `.venv` enlazados con junction a la copia
principal, sin versionar).

## Qué cambió

| Commit | Tarea | Ficheros |
|---|---|---|
| `f3513f5` | T1 · tests (fase RED: 13 en rojo) | `services/dedicacion-front/tests/test_f063_filtro_incidencia.py` (nuevo) |
| `05254ca` | T2 · fichas y filtro | `services/dedicacion-front/static/js/app.js`, `services/dedicacion-front/README.md` |
| `b982703` | T3 · test de dos tipos con la misma letra (mata M14) | `test_f063_filtro_incidencia.py` |
| (este) | campaña, informe y rastro | `progress/mutacion_manual_F-063.md` (nuevo), `progress/current.md`, este informe |

En `app.js` (+63 líneas, ninguna borrada):

- `state.filtroIncidencia: null`: el tipo de la ficha activa,
  `{codigo, letra, nombre}`, o `null`.
- `renderCabecera`: detrás de las cinco fichas de estado, una por tipo de
  incidencia del mes: `badge chip-inc`, texto «letra nombre nº» («V
  Vacaciones 3»), `title` «Filtrar por incidencia». Un clic la activa (y
  sustituye a la que hubiera) o, si ya lo estaba, la quita, y repinta
  cabecera y tabla. «N trabajadores» quita también la de incidencia; las de
  estado no la tocan.
- `tiposIncidenciaDelMes(trabajadores)` (nueva, pura): un tipo por
  `codigo` con `n` = trabajadores (no incidencias) con alguna no quitada;
  ordenados por letra y, a igual letra, por nombre.
- `tieneIncidencia(t, codigo)` (nueva, pura): la única regla de «una quitada
  no cuenta»; la usan el conteo y el filtro.
- `trabajadoresVisibles`: una condición más, detrás de la de estado
  (`state.filtroIncidencia && !tieneIncidencia(...)` ⇒ fuera). Como el resto
  de condiciones del `filter`, se suma (Y) a la ficha de estado, «Solo
  pendientes», los filtros de columna y el buscador.
- `moverMes`: quita el filtro de incidencia, igual que el de estado.

`README.md` del front: la frase de los chips del resumen menciona las
fichas de incidencia. No cambia la api, el transfer, el CSS ni ningún test
existente; `azure-apps/` no cambia (no cambia lo que se expone ni consume).

## Decisiones

- **La clave del tipo es `codigo`**, no la letra: es la identidad del tipo en
  la api (`IncidenciaOut.codigo`, el `codigo` del PUT). Dos códigos con la
  misma letra salen en dos fichas (test `misma_letra…`).
- **Cuenta y filtra solo `t.incidencias`**, las del cuadrante del mes que ya
  sirve la api (F-030 R21). Las rachas de meses anteriores no viven ahí (las
  trae el preflight del modal, F-062), así que no entran por construcción.
- **Las bajas sin carga no cuentan**: `trabajadoresVisibles` no las enseña
  nunca, así que contarlas haría que la ficha dijera 3 y el clic enseñara 2.
  Mismo criterio (`!t.activo && !t.lineas.length`) que el filtrado.
- **La ficha activa no desaparece aunque el mes se quede sin ese tipo** (p.
  ej. se quita en el editor la única incidencia): sigue, recuadrada y con 0,
  para poder quitarla con otro clic, como «0 falta» con la de estado. Por eso
  el estado guarda letra y nombre, no solo el código. Sin filtro activo y sin
  incidencias, ninguna ficha nueva (criterio 1).
- **Orden por letra** (`localeCompare` «es»), desempate por nombre: estable
  y predecible. No se usa el orden del catálogo `GET /incidencias`, para no
  depender de que esté cargado.
- **Estilo y accesibilidad, los de las fichas de estado**: `span.badge` con
  `title` y `filtro-activo` para la activa. La clase `chip-inc` ya existente
  (borde discontinuo, `styles.css:463`) las distingue de las de estado sin
  tocar el CSS.
- **Las funciones nuevas van detrás de `renderCabecera`, como `function`
  propias**: ningún arnés existente ejecuta `renderCabecera`, y los que
  ejecutan `trabajadoresVisibles` no traen `filtroIncidencia` en su `state`
  (queda `undefined` y la condición corta antes de llamar a
  `tieneIncidencia`). Confirmado: la suite del front entera pasa sin tocar
  un test.
- Ningún texto nuevo nombra motivos de conflicto (F-013 R4).

## Fase RED (T1, antes de tocar `app.js`)

Tests escritos sobre `e6dd5ce` (sin código de F-063). El arnés carga las
funciones nuevas solo si existen, así que el rojo es de comportamiento (no
hay ficha que pulsar), no de un nombre que falta. Comando, desde
`services/dedicacion-front`:

```
.venv/Scripts/python -m pytest tests/test_f063_filtro_incidencia.py -q -p no:cacheprovider --tb=short
```

Salida real (recortada a una línea por test; la traza de node es igual en
los diez que pulsan una ficha):

```
test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores
E   AssertionError: assert ['6 trabajado...', '1 exceso'] == ['6 trabajado...medad 1', ...]
E     Right contains 3 more items, first extra item: 'B Enfermedad 1'
test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo
E   AssertionError: assert 'no existe' == [{'codigo': 'CIE', 'letra': 'B', 'nombre': 'Enfermedad', 'n': 1}, {'codigo': 'CIP', ...}, {'codigo': 'CIV', ..., 'n': 2}]
test_f063_r2_un_clic_filtra_y_marca_la_ficha
E   AssertionError: [stdin]:199
E       if (!h) throw new Error("no hay ficha «" + texto + "»: " +
E     Error: no hay ficha «V Vacaciones 2»: ["6 trabajadores","3 OK","1 sin carga","1 falta","1 exceso"]
test_f063_r2_una_quitada_no_filtra
E     Error: no hay ficha «B Enfermedad 1»: ["6 trabajadores","3 OK","1 sin carga","1 falta","1 exceso"]
test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo
E     Error: no hay ficha «V Vacaciones 0»: ["6 trabajadores","3 OK","1 sin carga","1 falta","1 exceso"]
test_f063_r2_cambiar_de_mes_quita_el_filtro_de_incidencia
E   AssertionError: assert 'state.filtroIncidencia = null;' in 'async function moverMes(delta) { ... state.filtroEstado = null; fijarSeleccion([]); await cargarPeriodo(anio, mes); }'
test_f063_el_filtro_solo_vive_en_la_cabecera_y_el_filtrado
E   AssertionError: assert set() == {'moverMes', ...oresVisibles'}
(otro_clic, n_trabajadores, elegir_otra, r3 ×3: «no hay ficha «V Vacaciones 2»», como arriba)
PASSED tests/test_f063_filtro_incidencia.py::test_f063_r1_sin_incidencias_en_el_mes_ninguna_ficha_nueva
PASSED tests/test_f063_filtro_incidencia.py::test_f063_r1_las_quitadas_solas_no_sacan_ficha
13 failed, 2 passed in 6.46s
```

Los dos en verde antes de existir el código son las guardas de «sin
incidencias, ninguna ficha nueva»: hoy no sale ninguna, y la mutación
demuestra que muerden (M3, M4 y M8 los tumban). Tras T2:
`15 passed in 7.14s`. El test de T3 (`misma_letra…`) se escribió **después**
del código, a raíz del superviviente M14: no tiene fase RED propia; su rojo
es la campaña (M14 vivo sin él, muerto con él).

## Tests (`test_f063_filtro_incidencia.py`, 16; sin red ni BBDD)

Código REAL de `app.js` en node (`renderCabecera`, `trabajadoresVisibles` y
sus dependencias) con un DOM de mentira: `#resumen` guarda sus fichas y su
manejador de clic, y el test **pulsa** la ficha y mira los visibles. Los
dobles tienen la forma de `TrabajadorOut`/`LineaOut`/`IncidenciaOut` de la
api: todas las claves, `id`/`sigrid_*`/partida/propuesta a `null`, `quitada`
siempre presente (`false`/`true`). Cubren:

- **Conteo** (criterio 1): una ficha por tipo, letra/nombre/nº; un
  trabajador con dos del mismo tipo cuenta una vez; la quitada no cuenta
  (aunque vaya delante en la lista); la baja sin carga no cuenta; la recién
  añadida sin `id` sí; sin incidencias, o solo quitadas, ninguna ficha nueva;
  dos códigos con la misma letra, dos fichas por nombre.
- **Filtrado** (criterio 2): clic filtra, marca y repinta la tabla; la
  quitada no filtra; otro clic quita; «N trabajadores» quita incidencia y
  estado; otra ficha sustituye; la activa sin trabajadores sigue con 0 y se
  quita; cambiar de mes la quita.
- **Combinación** (criterio 3): con la ficha de estado (y quitar la de
  estado no quita la de incidencia), con el buscador y con los filtros de
  columna «Obra» y «Trabajador».
- **Límite**: solo `renderCabecera`, `trabajadoresVisibles` y `moverMes`
  tocan `filtroIncidencia`; las dos funciones nuevas no leen `state` ni
  llaman a la api.

## Mutación manual del JS

`harness.mutacion` solo muta Python; la campaña manual está en
`progress/mutacion_manual_F-063.md` (SHA, línea base, workers, tiempo, una
fila por mutante y el script que la reproduce). Resultado sobre `b982703`
(1 worker, 811,1 s): **25 mutantes, 24 muertos, 1 superviviente**.

- **M14** (sin desempate por nombre) sobrevivía en la primera pasada (sobre
  `05254ca`): ningún dato tenía dos tipos con la misma letra. Lo mata el
  test de T3.
- **M25** (quitar el `|| []` de `tieneIncidencia`) sobrevive y es
  **equivalente**: `TrabajadorOut.incidencias` se serializa siempre (lista,
  por defecto `[]`, sin `exclude_if`), y `state.trabajadores` solo se llena
  con esa respuesta. Matarlo pediría un doble sin la clave, contrario a la
  forma real. Análisis completo en la campaña.

## Pendiente (MANUAL)

La comprobación en el navegador, solo lectura de pantalla (vale en
producción tras desplegar el front): pasos exactos en `progress/current.md`,
«⚠ Lo que espera al humano», entrada F-063.

## Fuera del alcance

- Filtrar por varias incidencias a la vez (O entre fichas): el criterio pide
  una sola activa.
- Contar las rachas abiertas de meses anteriores o las quitadas.
- Desplegar: lo decide el humano tras la review.

## Evidencias

`bash harness/init.sh` tal cual, solo, sobre `b982703` más este papeleo
(2026-10-27; `.arnes_cache/` no existía en el worktree, así que no había
`suite_*.ok` que borrar): termina en «ENTORNO LISTO. Puedes trabajar.»,
código de salida 0, **sin ningún [KO]**.

| Evidencia | Valor real |
|---|---|
| Tests de la raíz | 418 passed, 1 skipped en 229,73 s |
| Tests de la api | 1308 passed en 258,37 s |
| Tests del front | 430 passed en 278,16 s (16 de F-063) |
| Tests del transfer | 1585 passed en 83,29 s (incluido `test_f013_sin_partida.py`) |
| Tests de F-063 sueltos | 16 passed en 15,07 s |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: N/A (F-063 no cambia líneas Python de producción frente a dev)`; el JS no tiene medidor de cobertura |
| Mutantes | `harness.mutacion` no aplica (no hay Python de producción). Campaña manual del JS (`progress/mutacion_manual_F-063.md`, `b982703`, 1 worker, 811,1 s): **25 generados, 1 superviviente** (M25, equivalente, analizado) |
| Tamaño | `PUERTA TAMAÑO: F-063 dentro de los topes (impl 176/220)` |

Los tiempos van inflados: la máquina estaba cargada (la línea base de la
campaña pasó de 7,8 s a 15,8 s con un solo test más).
