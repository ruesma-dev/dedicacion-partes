<!-- progress/impl_F-050.md -->
# F-050 · Subfilas por obra con columna Partida y partida propuesta · informe del implementer

Rama `feature/F-050-subfilas-partida`, rigor **crítico**, spec aprobada el
2026-10-09 (D1-D10 = A). Tareas T1-T15 hechas, una por commit
(`686d00a`..`f4cdb11` y el cierre). T16-T18 son MANUAL del humano. Dos
paradas por tests fuera de la lista cerrada, las dos aprobadas por el humano
y recogidas en requirements §6: `test_f037_r3_…` (T3) y `test_f003_r8_…` (T6).

## Qué cambió

**Transfer** (propone la partida, calcula el mayor, solo lee):
- `application/services/propuesta_partida.py` (nuevo, puro): `proponer_partida`
  (parte anterior → último parte → casamiento), `previa_en_obra`,
  `ultima_de_recurso`, `mayor_de` (por la raíz), `catalogo`,
  `mayor_inicial`, `clave_orden_codigo` (orden natural), `ventana`,
  `MOTIVO_PARTIDA_NO_HOJA`.
- `sigrid_write_client.historial_partidas` (SQL de design §6, lotes de 500,
  `truncated` = error); ajuste `PROPUESTA_MESES_ATRAS` (24) y `.env.example`.
- `registro_pipeline`: una lectura del historial por petición con los
  recursos de las líneas automáticas; la propuesta sustituye a
  `resolver_normal`; R20 (elegida que no es hoja activa → omitida con
  motivo); `AccionLinea.partida_origen`; `_cat` en orden natural;
  `RegistroPipeline.proponer` y `POST /api/partidas/propuesta` (422/502).
- `prueba_escritura_porcentajes.py propuesta --obra --recurso [--ano --mes
  --categoria --nombre]`: solo lectura, catálogo con su mayor, recuento por
  CD/CI/CP/OTRO, propuesta con método, origen y botón, segundos por lectura.

**Api** (guarda la elegida): `AsignacionORM.partida_ide/cod/res`
(nulables, DDL derivado al arrancar); `Linea.partida_*` y `partida_fija`;
repositorio (`_a_linea_con_partida`, `reemplazar`); `_snapshot` (partida
solo si hay), `_validar_lineas`, `_conservar_partidas` en
`GuardarAsignaciones`; `CambiarPartida` + `PUT …/trabajadores/{ide}/partida`
(evento `PARTIDA`; 404 `LineaNoEncontrada`, 409, 422 VAR / `ide` ≤ 0);
`PartidasDeLinea` (`application/partidas_linea.py`) + `GET …/partidas`
(502 `PropuestaNoDisponible`); `TransferClient.propuesta_partidas`;
`LineaOut` con los cuatro campos de R18; registro con `paride` = elegida.

**Front**: columna `partida` (tras obras, también en preferencias viejas),
subfilas (`DocumentFragment`, `rowSpan`, `data-linea`), celda Partida
(elegida / «automática» / fija), filtro «Partida» línea a línea y buscador
con la partida; selector (`abrirSelectorPartida` / `montarSelectorPartida`,
buscador sin tildes ni mayúsculas, Todas · CD · CI · CP, propuesta primera
con su origen, «automática», ↑ ↓ Enter Esc, caché, PUT y repintado); modal:
botón `.sel-partida` con `textoPartidaAccion` y `rotuloOrigen` que abre el
mismo selector y repite el preflight; fuera `overrides` y `opcionesPartida`.

**Docs**: `#regla-partida` (punto 19) en `ARCHITECTURE.md`, endpoints y
tabla; `INTEGRACION.md` §3, §5, §7; READMEs de api y transfer; `ANCLAS`.

## Decisiones y desviaciones (justificadas)

1. **Ventana:** `desde` = periodo − 24 meses, `hasta` = periodo (incluido).
2. **Empate** con tolerancia de 1e-6 en las sumas de `can` (ruido de coma
   flotante; `can` viaja con 4 decimales).
3. **`_a_linea_con_partida`** envuelve `_a_linea` en vez de cambiarlo:
   `test_f024_r11` y `test_f025_r18` llaman a `_a_linea` con dobles sin
   `partida_*` y NO están en la lista cerrada.
4. **VAR:** la asignación no guarda partida (`partida_*` nulas,
   `partida_fija` = `obra.registro_paride` no nulo). La celda enseña la
   descripción de la entrada; `GET …/partidas` devuelve `fija` = `{ide:
   −obra_ide, cod, res}` (`domain.obras.ide_entrada`), sin llamar al transfer.
5. **`proponer`** casa la postventa con `cargar_catalogo_postventa` +
   `casar_postventa` (las funciones que envuelve `_destino_postventa`), con
   la obra de origen ya resuelta: el flag de pruebas de `_destino_postventa`
   no se usaba y dejaba un mutante equivalente.
6. **`ambito`:** si el mayor de la elegida es OTRO, `null` (Todas): OTRO no
   tiene botón.
7. **Selector:** «automática» es la última opción (Enter al abrir elige la
   propuesta); si el ancla se rehace al guardar el editor, el panel se
   coloca donde estaba al abrir; la caché se vacía en cada carga del
   cuadrante (cubre cambio de mes y de empresa) y su clave tras cada PUT.
8. **`MOTIVO_PARTIDA_NO_HOJA`** vive en `propuesta_partida.py`:
   `reglas_porcentajes.py` no se toca (design §9).
9. **Fase `propuesta`:** `--categoria` y `--nombre` opcionales para ver el
   casamiento; la empresa es la del script (`EMPRESA_PRUEBA` = 1).
10. **`test_f037_r3`:** la línea aprobada necesita importar
    `PRESUPUESTO_ORIGEN` y `_fila` de `conftest` (dos líneas de import, sin
    tocar aserciones). **`test_f049_ampliacion`:** dos concatenaciones
    implícitas de los tests reescritos van entre paréntesis (ruff ISC004).

**Aviso para `partes`** (regla de las copias): su copia de
`partida_catalog.categoria` clasifica mal las hojas bajo `CD` (design §5.1);
ya avisado al humano el 2026-10-09. Aquí no se toca la copia.

## Tests anteriores que cambian (todos de la lista cerrada)

Transfer: `conftest.py` (`historial_partidas` vacío, `propuesta_meses_atras`)
y `test_pipeline_offline.py` (lo mismo); `test_f022`, `test_f047` y
`test_f049_partidas_obra` no necesitaron cambio (heredan del doble);
`test_f002_fuente_unica` (`ANCLAS`); `test_f037_r3` (aprobado). Api: `_fila`
de `test_f022_empresa_en_linea`, `test_f024_registro_empresa`,
`test_f026_registro_recurso`, `test_f039_registro_var`; `CAMPOS_LINEA` de
`test_f034_rutas`; `test_f003_r8` (aprobado). Front: los de T12 (`test_f039_r22_
el_resto…`, `_modal` y ejecutar de `test_f049_avisos`, los nombrados de
`test_f049_ampliacion` y los seis `c_*` + `_opciones` / `_elegida` borrados;
su intención vive en `test_f050_modal_registro.py`).

## Fase RED (trazas reales, comando exacto)

Cada tarea de código, antes de escribir el código (desde la carpeta del
servicio, `.venv/Scripts/python.exe -m pytest … -q -p no:cacheprovider`):

```
T1 $ … tests/test_f050_propuesta.py
E   ModuleNotFoundError: No module named 'application.services.propuesta_partida'
1 error in 0.46s
T2 $ … tests/test_f050_propuesta.py -k historial
E       AttributeError: 'SigridWriteClient' object has no attribute 'historial_partidas'   (×6)
E       AttributeError: 'Settings' object has no attribute 'propuesta_meses_atras'
7 failed, 37 deselected in 1.91s
T3 $ … tests/test_f050_pipeline.py
E       AssertionError: assert ('escribir', ...'auto_nombre') == ('escribir', ...rte_anterior')
E       AttributeError: 'AccionLinea' object has no attribute 'partida_origen'
E       assert [] == [([200, 400], 202407, 202607)]
E       Failed: DID NOT RAISE RuntimeError
E       AssertionError: assert 'escribir' == 'omitir'      (×6, R20)
18 failed, 5 passed in 0.75s
T4 $ … tests/test_f050_endpoint_propuesta.py
E       assert 404 == 422 (×4) · KeyError: 'propuestas' (×4) · assert 404 == 502 (×2) · assert 404 == 200
13 failed in 1.79s
T5 $ … tests/test_f050_endpoint_propuesta.py -k script
E   argparse.ArgumentError: argument fase: invalid choice: 'propuesta' (choose from 'inspeccionar', …)
4 failed, 13 deselected in 2.54s
T6 $ … tests/test_f050_partida_linea.py -k "r12 or r14 or r15 or r16"   (api)
E   ImportError: cannot import name '_conservar_partidas' from 'application.use_cases'
1 error in 0.36s
T7 $ … tests/test_f050_rutas_partida.py tests/test_f034_rutas.py -k "r13 or r18 or f034"
E       assert 404 == 200 (×4) · assert 404 == 422 (×3) · assert 'error' in {'detail': 'Not Found'} (×3)
E       Extra items in the right set: 'partida_res' 'partida_ide' …   (CAMPOS_LINEA, ×3)
T8 $ … tests/test_f050_rutas_partida.py -k r17
E       ModuleNotFoundError: No module named 'application.partidas_linea' (×6)
E       ImportError: cannot import name 'PropuestaNoDisponible' from 'domain.errors' (×5)
E       AttributeError: 'TransferClient' object has no attribute 'propuesta_partidas'
12 failed, 14 deselected in 3.01s
T9 $ … tests/test_f050_partida_linea.py -k r19
E       KeyError: 'paride'  (×2)
2 failed, 3 passed, 17 deselected in 1.49s
T10 $ … tests/test_f050_subfilas.py   (front)
E       AssertionError: no existe la función textoPartida en app.js
E       assert 'const frag = document.createDocumentFragment();' in 'function construirFila(t) { …
E       AssertionError: assert ['total', 'as..., 'categoria'] == ['total', 'as..., 'categoria']
E       AssertionError: assert [] == ['Ana']        (filtro Partida)
T11 $ … tests/test_f050_selector_partida.py
E       AssertionError: no existe la función filtrarPartidas en app.js (×10)
E       AssertionError: no existe la función montarSelectorPartida en app.js (×5)
19 failed in 0.32s
T12 $ … tests/test_f050_modal_registro.py
E       AssertionError: no existe la función textoPartidaAccion en app.js (×7)
E       AssertionError: assert [['/periodos/...or_ide': 77}]] == [['/periodos/...or_ide': 77}]]
E       AssertionError: assert 'overrides' not in '// static/j…'
11 failed in 0.31s
T13 $ … tests/test_f002_fuente_unica.py   (transfer, solo con ANCLAS cambiada)
FAILED …test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-partida]
FAILED …test_f002_r1_fuente_unica_el_ancla_no_esta_repetida[regla-partida]
2 failed, 70 passed in 0.25s
```

Los que pasaban en RED eran controles de lo que no cambia (sin líneas
automáticas no se lee historial, la manual válida se escribe, VAR fija…).
Tras cada tarea: verde de su verificación y de la suite del servicio.

## Mutación (T15)

- **Python** (`python -m harness.mutacion --feature F-050 --workers 1` en un
  `git worktree add --detach` del scratchpad con uniones a los `.venv`,
  retirado después): primera pasada sobre `7f5f115`, **160 generados, 16
  supervivientes**, 914,8 s. Ninguno se dejó como equivalente sin más:
  - 13 huecos reales → tests nuevos (`f4cdb11`): modo por defecto `False` en
    `GET …/partidas`, `PartidaIn` y `LineaPropuestaIn`; `PartidaElegidaIn.ide
    = 1` válido; los recursos del historial (solo automáticos: sin
    postventa, manual ni omitida); dataclasses inmutables; empate < 1e-6;
    `can` nulo suma 0 (pasos 1 y 2); la línea completa del catálogo y los
    segundos (≥ 0, < 60) de la fase `propuesta`.
  - 3 equivalentes que se ELIMINAN cambiando el código sin cambiar la
    conducta: las constantes `(1, 0, …)` de `clave_orden_codigo` (ahora
    `(False, n)` / `(True, texto)`) y el flag de pruebas de
    `_destino_postventa` en `proponer` (decisión 5).
  - **Segunda pasada, la final** (`f4cdb11`): **158 generados, 158 muertos,
    0 supervivientes**, 0 timeouts, 1236,8 s → `progress/mutacion_F-050.md`
    (SHA, workers 1, sin muestreo).
- **JS manual** (`progress/mutacion_manual_F-050.md`, fichero:línea, texto
  exacto y nº de fallos por mutante, en otra copia aislada): primera pasada
  56 mutantes, 4 vivos (J19 filtro de la fija, J36 catálogo de postventa en
  el selector, J46 código pintado en la opción, J56 `registro.lineas` sin
  vaciar), los cuatro huecos reales con test nuevo; **segunda pasada 56/56
  muertos**, 785,5 s.

## Fuera del alcance

F-051 (pisar al 0 %), F-044 (vinculados), F-054 (velar etiquetas), F-021,
el Excel (D8) y dos partidas para una misma línea. `azure-apps/dedicacion.md`
lo pone al día el líder (T14, anotado en `progress/current.md`). Ninguna
lectura ni escritura contra Sigrid ni Azure en esta implementación.

## MANUAL pendiente (humano)

**T16 · M1, solo lectura** (Git Bash, desde la raíz del repo):
```
cd services/dedicacion-transfer && .venv/Scripts/python prueba_escritura_porcentajes.py propuesta --ano 2026 --mes 9 --obra 0694 --recurso <res.ide de GONZALEZ PANIAGUA>
cd services/dedicacion-transfer && .venv/Scripts/python prueba_escritura_porcentajes.py propuesta --ano 2026 --mes 9 --obra 0696 --recurso <res.ide de GONZALEZ PANIAGUA>
```
Esperado (0694): «Propuesta: CI.1.5 …», `método parte_anterior · origen parte
PT26/00319 · 09/2026 · obra 0694`; «Por mayor: CD 727 · CI 95 · CP 13 · OTRO
…»; `01.19.03.20` sale con `CD`, `CP.1`-`CP.12` con `CP`; botón preelegido
CI; cada «lectura …» < 30 s (si no, PARAR: design §10).

**T17 · M2, navegador en modo pruebas**: en tres consolas de Git Bash, en
este orden, `cd services/dedicacion-transfer && .venv/Scripts/python main.py`,
`cd services/dedicacion-api && .venv/Scripts/python main.py`, `cd
services/dedicacion-front && .venv/Scripts/python main.py`; `curl -s
http://localhost:8006/health` debe decir `"modo_pruebas": true`. En
`http://localhost:8080`, septiembre 2026, los puntos (a)-(f) de `tasks.md`
T17 (subfilas y columna; selector en la 0694 con CI preelegido, «jefe» y
«JÉFE», CD · CI · CP · Todas, «Sin partidas con ese filtro», ↑ ↓ Enter,
Ctrl+Z; `Postv-` y `VAR-NN`; regresión de teclas y filtros; modal con
«MODO PRUEBAS», botón de partida que abre el mismo selector y Esc que lo
cierra sin cerrar el modal; **Cancelar, sin Registrar**; tiempo en la 0696).
La api añade al arrancar las tres columnas `partida_*` a la base local.

**T18 · M3, registro en pruebas** (solo con autorización del humano en ese
momento): con T17 arrancado, «⇪ Sigrid» → Registrar en un trabajador con
partida elegida; luego `cd services/dedicacion-transfer && .venv/Scripts/
python prueba_escritura_porcentajes.py estado --ano 2026 --mes 9` → la línea
en la 0404 con `PRUEBA-PORC` y su `paride` el elegido; anotar en
`progress/current.md` las líneas que quedan en la 0404 para borrarlas.

## Evidencias

| Evidencia | Valor real |
|---|---|
| `bash harness/init.sh` (tal cual, sin `.arnes_cache/suite_*.ok`) | VER_INIT |
| Tests por servicio (ejecutados, no caché) | VER_SUITES |
| Tests nuevos de F-050 | transfer `test_f050_propuesta` 47, `test_f050_pipeline` 24, `test_f050_endpoint_propuesta` 19; api `test_f050_partida_linea` 23, `test_f050_rutas_partida` 30; front `test_f050_subfilas` 16, `test_f050_selector_partida` 19, `test_f050_modal_registro` 14 |
| Cobertura de las líneas cambiadas | VER_COBERTURA |
| Mutantes Python | **158 generados, 0 supervivientes** (final; la primera, 160/16), 1236,8 s, 1 worker, sin muestreo |
| Mutantes JS (manual) | **56 generados, 0 supervivientes** (final; la primera, 56/4), 785,5 s en serie |
| ruff | 237 avisos, los mismos de antes (los ficheros de F-050 no añaden ninguno) |
