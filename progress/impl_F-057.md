<!-- progress/impl_F-057.md -->
# F-057 · Informe del implementer

«Buscando partida…» solo en las líneas cuya propuesta se está calculando.
`sdd: false`, rigor **estándar**. Rama `feature/F-057-buscando-solo-pendientes`
(copia principal). Plan seguido: «F-057 · plan aprobado (2026-10-19)» de
`progress/current.md`, con dos desviaciones menores justificadas abajo (D1, D2).

## Qué cambió

| Commit | Fichero | Cambio |
|---|---|---|
| `87f7e9e` T1 | `services/dedicacion-api/application/propuestas_mes.py` | `pendientes(periodo_id)`: las líneas de `_en_cola` del periodo, como `(trabajador, obra, False)`. `en_curso` = `bool(pendientes)`. `encolar()` = `(en_curso, pendientes)` de la misma foto; `lanzar()` queda como envoltorio que da el `bool`. `_lanzar` devuelve las pendientes. `estado()` añade `pendientes`. |
| `87f7e9e` T1 | `…/interface_adapters/api/schemas.py` | `LineaOut.propuesta_pendiente: bool = False`; `PendienteOut`; `PropuestasOut.pendientes`; `a_trabajador_out(…, pendientes)` marca cada línea por identidad `(trabajador, obra, es_postventa)`. |
| `87f7e9e` T1 | `…/interface_adapters/api/routes.py` | `_encolar` devuelve `(en_curso, pendientes)` vía `encolar()` (fallo ⇒ `(False, ∅)` y log). Cuadrante, guardar fila, partida, deshacer y F8 construyen la fila DESPUÉS de encolar; completar y copiar mes toman `[0]` (no devuelven líneas). |
| `87f7e9e` T1 | tests de la api | Nuevo `test_f057_pendientes.py` (19). Ajustes de contrato: el falso `_PropuestasFalsas` (`test_f024_rutas_empresa.py`) gana `pendientes` y `encolar`; `test_f034_rutas.py` añade el campo a `CAMPOS_LINEA`; `test_f055_r35_estado…` espera `pendientes`. |
| `3c32cc2` T2 | `services/dedicacion-front/static/js/app.js` | `htmlPartida(l)`: «buscando partida…» solo si `l.propuesta_pendiente` (antes, el global). `aplicarPendientes(pendientes)`: copia la lista a las marcas, casando trabajador, obra y modo. `consultarPropuestas` la aplica antes de repintar (con `[]` si la api falla). `construirCelda` y `repintarCeldasPartida` usan la marca. El sondeo sigue gobernado por `en_curso`. |
| `3c32cc2` T2 | tests del front | Nuevo `test_f057_buscando_pendientes.py` (14). `test_f055_propuesta_celda.py` pasa al contrato nuevo (caso «buscando» con la marca, `htmlPartida(l)`, `aplicarPendientes` en la lista de funciones). |
| `1258c98` T3 | `docs/INTEGRACION.md`, `docs/ARCHITECTURE.md` | Contrato de `propuesta_pendiente` y `pendientes`; la regla de qué dice «buscando partida…». |

`azure-apps/` no se toca (se hace al desplegar, según el plan).

## Decisiones de diseño

- **D1 · Triples, no pares.** `pendientes` da `(trabajador_ide, obra_ide,
  es_postventa)` con `es_postventa` siempre `False` (la cola solo tiene líneas
  normales). Con pares, la línea de postventa de la MISMA obra que una normal
  encolada se marcaría también; así la api y el front casan por identidad
  completa y ninguno de los dos aplica la regla «la postventa no se encola».
- **D2 · `encolar()` = `(en_curso, pendientes)` de una sola foto.** Las rutas no
  tienen el `periodo_id` (sí `anio`/`mes`); `_lanzar` ya lo resuelve. Devolver
  las dos cosas desde ahí evita una lectura extra por petición y, sobre todo,
  la incoherencia de leerlas por separado: `en_curso` falso con líneas
  marcadas dejaría «buscando partida…» sin sondeo que lo apague. `lanzar()`
  sigue existiendo (lo usan `tras_sync` y los tests de F-055) y
  `pendientes(periodo_id)` es el método del plan, que usan `en_curso`,
  `estado` y `_lanzar`.
- **D3 · «Pendiente» = en la cola, sin más.** La api no vuelve a mirar
  partida elegida, fija ni postventa para marcar: lo que no se encola nunca
  está en la cola. Una línea cuya partida se elige mientras su propuesta se
  calcula sigue marcada hasta que acaba la tarea, pero el front pinta antes la
  elegida (`htmlPartida`), así que no se ve.
- **D4 · Si la consulta falla, ninguna marca.** `consultarPropuestas` aplica
  `[]` cuando la api no contesta o no trae la lista: el sondeo se para (F-055)
  y nada se queda diciendo «buscando partida…» sin nadie que lo actualice. Es
  el mismo efecto visible que antes (el global pasaba a falso).
- **D5 · `construirCelda` conserva su estructura** (rama de la elegida y
  `else` «automática»), cambiando solo la condición a `l.propuesta_pendiente`:
  así el test estático de F-050 (`test_f050_r24_…`) no cambia.

## Tests

- **api, `tests/test_f057_pendientes.py` (19):** con `PropuestasDelMes` real y
  ejecutor retenido: línea encolada (sí), **en cálculo** (sí, vista desde el
  transfer falso mientras calcula; al acabar, no), de **postventa**, con
  **partida elegida**, con **partida fija** y con propuesta guardada (no), en la
  **memoria «sin propuesta»** (no, y no se reencola), periodo cerrado o
  inexistente, `encolar` nunca lanza, `estado` con y sin cola. Rutas con
  `TestClient`: el cuadrante marca cada línea (y no la postventa de la misma
  obra), sin cola nada marcado, las cuatro escrituras con fila marcan con la
  cola de DESPUÉS de encolar, encolar roto ⇒ nada marcado, `GET …/propuestas`
  con `pendientes`, y de punta a punta con la cola real.
- **front, `tests/test_f057_buscando_pendientes.py` (14):** el `app.js` real en
  `node`: «buscando» solo con la marca y con independencia del global; la
  propuesta y la elegida mandan; `aplicarPendientes` casa por identidad (la
  postventa de la misma obra no); dos consultas seguidas actualizan marcas y
  la línea que recibe propuesta la enseña sin recargar; error o respuesta sin
  lista ⇒ ninguna marca. Estáticos: `htmlPartida`, la celda y el repintado no
  miran `propuestasEnCurso`; `aplicarPendientes` no mira partida ni propuesta.

## Fase RED (trazas reales)

**api** — `test_f057_pendientes.py` escrito (y el falso ampliado) antes del
código. Comando, desde `services/dedicacion-api`:
`.venv/Scripts/python -m pytest tests/test_f057_pendientes.py -q -p no:cacheprovider`
→ `19 failed, 1 warning in 6.81s`. Errores (salida agrupada con `sort | uniq -c`):

```
      5 E       AttributeError: 'PropuestasDelMes' object has no attribute 'encolar'. Did you mean: '_en_cola'?
      5 E   KeyError: 'propuesta_pendiente'
      3 E       KeyError: 'propuesta_pendiente'
      2 E       KeyError: 'pendientes'
E       AttributeError: 'PropuestasDelMes' object has no attribute 'pendientes'
E       assert ([])
E           pydantic_core._pydantic_core.ValidationError: 1 validation error for PropuestasOut
E           pendientes
E             Extra inputs are not permitted [type=extra_forbidden, input_value=[{'trabajador_ide': 10, '... 'es_postventa': False}], input_type=list]
FAILED tests/test_f057_pendientes.py::test_f057_r2_encolada_es_pendiente_y_las_demas_no
FAILED tests/test_f057_pendientes.py::test_f057_r2_en_calculo_sigue_pendiente_y_al_acabar_deja_de_serlo
FAILED tests/test_f057_pendientes.py::test_f057_r2_en_la_memoria_sin_propuesta_no_es_pendiente
FAILED tests/test_f057_pendientes.py::test_f057_r2_cuadrante_marca_cada_linea
FAILED tests/test_f057_pendientes.py::test_f057_r2_la_postventa_de_la_misma_obra_no_es_pendiente
FAILED tests/test_f057_pendientes.py::test_f057_r2_las_escrituras_marcan_la_fila_tras_encolar[partida]
FAILED tests/test_f057_pendientes.py::test_f057_r2_get_propuestas_publica_pendientes
… (19 en total)
```

Tras T1: `943 passed` en la suite de la api.

**front** — `test_f057_buscando_pendientes.py` antes del código. Desde
`services/dedicacion-front`:
`.venv/Scripts/python -m pytest tests/test_f057_buscando_pendientes.py -q -p no:cacheprovider`
→ `14 failed in 1.23s`:

```
     11 E       AssertionError: no existe la función aplicarPendientes en app.js
E        +  where False = <built-in method startswith ...>('function htmlPartida(l) {')
E        +    where ... = 'function htmlPartida(l, enCurso) { if (l.partida_ide != null) { ...
E       assert 'td.innerHTML = htmlPartida(l);' in 'function construirCelda(t, clave, idx) { ...
E       AssertionError: assert 'aplicarPendientes((datos && datos.pendientes) || []);' in 'async function consultarPropuestas(generacion, ruta) { ...
FAILED tests/test_f057_buscando_pendientes.py::test_f057_r1_buscando_solo_si_la_linea_es_pendiente[postventa_con_cola]
FAILED tests/test_f057_buscando_pendientes.py::test_f057_r1_cada_consulta_actualiza_las_marcas_y_repinta
… (14 en total)
```

Y el defecto de partida, con el `htmlPartida` de `dev` (`0b48c9e`) en `node`
y la llamada que hacía `construirCelda` (`htmlPartida(l,
state.propuestasEnCurso)`), para una línea de postventa con la cola ocupada
por otras: `postventa, cola con otras lineas -> <span class="partida-auto
buscando">buscando partida…</span>`. Tras T2: `305 passed` en la suite del front.

## Mutación

- **Python** (`progress/mutacion_F-057.md`, generado por la herramienta, **en
  serie, `--workers 1`**, HEAD `1258c98`): 11 generados, **10 muertos, 1
  superviviente**, 0 timeouts, 407,2 s; base 51,9 s, media 37,0 s por mutante.
  El superviviente (`schemas.py:97`, defecto `False`→`True` de
  `propuesta_pendiente`) es **equivalente**: el único `LineaOut(` de producción
  pasa siempre el valor explícito. Análisis completo en el informe.
- **Campaña paralela descartada.** La primera, con los 4 workers por defecto
  (mismo HEAD), dio 5 supervivientes; 4 eran falsos (la 2.ª tanda de los
  workers): reproduje a mano `propuestas_mes.py:73` `==`→`!=` en un worktree
  aparte y fallan 7 tests; en serie mueren los cuatro. Detalle y aviso para el
  arnés en `progress/mutacion_F-057.md` («Campaña paralela descartada»).
- **JavaScript** (`progress/mutacion_manual_F-057.md`): campaña manual sobre un
  worktree aislado, 13 mutantes con su texto exacto, **13 muertos**, 91,2 s.

## Verificaciones

- `bash harness/init.sh` (tras borrar `.arnes_cache/suite_*.ok`), en el
  último commit de código (`1258c98`): **ENTORNO LISTO**; api 943, front 305 y
  transfer 932 passed; raíz 418 passed y 1 skipped; **PUERTA COBERTURA 100,0 %
  de 30 líneas cambiadas (30/30)**. Repetido al cerrar el informe (caché
  borrada otra vez, con este informe y los de mutación en el árbol): **ENTORNO
  LISTO**, mismos totales, cobertura 100,0 % (30/30), `PUERTA TAMAÑO` impl
  174/220.
- **MANUAL pendiente (lo hace el líder, solo BBDD LOCAL)**, comando exacto en
  `progress/current.md` («F-057 · plan aprobado», punto MANUAL): comprobar
  `PG_HOST=localhost` y `PG_DB=dedicacion`, vaciar las `propuesta_*` de 09/2026
  con el `UPDATE asignacion SET propuesta_ide = NULL, … WHERE periodo_id =
  (SELECT id FROM periodo WHERE anio = 2026 AND mes = 9)` que está allí, abrir
  septiembre 2026 en `http://localhost:8080` y mirar que las de postventa dicen
  «automática» y las demás «buscando partida…» hasta llenarse. **No lo he
  ejecutado.**

## Fuera de alcance y observaciones

- Qué se encola y cuándo: sin cambios (`_lanzar` intacto salvo su retorno).
- Desplegar: api antes que front (un front nuevo contra una api vieja no ve
  `propuesta_pendiente` ni `pendientes` y dice «automática» en todo; uno viejo
  contra una api nueva sigue como hoy). `azure-apps/dedicacion.md`, al desplegar.
- **Para el líder / arnés:** la campaña de mutación paralela dio supervivientes
  falsos (arriba). Si es un defecto de `harness/mutacion_paralela.py`, vale
  para cualquier proyecto (regla de propagación a `arnes-base`). No lo he
  tocado: fuera del alcance de F-057.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | api **943 passed**, front **305 passed**, transfer **932 passed**, raíz **418 passed, 1 skipped**; 0 fallos. Nuevos de F-057: 19 (api) + 14 (front) |
| Cobertura de las líneas cambiadas | **100,0 %** (30/30, umbral 80 %, nivel estándar) — línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| Mutantes Python | **11 generados, 10 muertos, 1 superviviente** (equivalente, analizado), 0 timeouts — `progress/mutacion_F-057.md` |
| Workers de la campaña | **1** (en serie; fila «Workers» del informe) → coste por mutante 407,2 s × 1 ÷ 11 ≈ **37 s** (base 51,9 s; media 37,0 s, por debajo de la base por `-x`) |
| Mutantes JS (manual) | **13 generados, 13 muertos, 0 supervivientes** — `progress/mutacion_manual_F-057.md` |
| Tiempo de la suite | último `init.sh`: api 67,1 s · front 36,4 s · transfer 22,1 s · raíz 46,8 s; línea base de la api en la campaña: 51,9 s |
