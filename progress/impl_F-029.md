# F-029 · Informe del implementer — Selección múltiple y completar al 100 %

Rama `feature/F-029-…`, rigor **estándar**, `sdd: true`, spec aprobada (D1-D6
= A). Hechas T1-T6, T8, T10; T7 del líder (`azure-apps` sin tocar); T9 MANUAL
(al final). Servicios **api** y **front**; transfer intacto. **Nada escrito
en Sigrid**, ni transfer, ni `sigrid-api`, ni `registro/ejecutar`. Tests
anteriores cambiados: **ninguno** (ninguno cayó en ningún momento).

## Qué cambió, por tarea

| Commit | Tarea |
|---|---|
| `b09e333` T1 | `domain/models.py`: `TipoEvento.COMPLETAR`, enum `ResultadoCompletado` (valor = nombre), dataclasses `Completado` y `ResultadoCompletarTrabajador` (`anadido` 0 por defecto). `domain/estados.py`: `completar_hasta_100(lineas, obra_ide, es_postventa)`, pura, junto a `calcular_estado` y con su épsilon |
| `50ad36d` T2 | `application/use_cases.py`: `CompletarHasta100.ejecutar(...) -> (resultados, resumen)`, helpers `_completar_uno` y `_obra_destino_o_error` |
| `977424c` T3 | `schemas.py`: `CompletarIn` (`extra=forbid`, 1-500 `ide`), `ResultadoCompletarOut`, `CompletarOut`, `a_completar_out`. `routes.py`: `POST /periodos/{anio}/{mes}/completar` (función `completar_lote`), `Usuario` + `EmpresaQ` como guardar |
| `9881fc1` T4 | `app.js`: `state.seleccion` (Set) y `state.ancla`; `construirFila` (clase `multi`, `mousedown` con Shift sin selección de texto, Ctrl/Cmd/Shift+clic → `marcarSeleccion`, clic simple vacía); `marcarSeleccion`, `fijarSeleccion`; contador «· N seleccionados»; Esc vacía; `cambiarEmpresa` y `moverMes` vacían. `styles.css`: `tr.fila.multi` |
| `6a6f5cd` T5 | `app.js`: `seleccionEfectiva`, `candidatasDestino`, `abrirCompletar`, `montarDialogoCompletar`, `lanzarCompletar`, `pintarResultadoCompletar`; tecla C en `teclas`; `#btn-completar` desactivado si CERRADO. `index.html`: botón en `.toolbar` y pie de ayuda. `styles.css`: lo mínimo del diálogo |
| `21ec1ee` T6 | `docs/ARCHITECTURE.md`: punto 15 `#regla-completar` (con procedencia), `completar` en la lista de endpoints y el ancla en la cabecera de fuentes únicas. `docs/INTEGRACION.md` §5: párrafo de la ruta (solo para el front). `services/dedicacion-api/README.md`: fila de la ruta |
| `53e3f79` T8 | Test de inmutabilidad (`frozen`) de `Completado` y `ResultadoCompletarTrabajador`: mata 2 supervivientes de la 1.ª campaña |

Ficheros nuevos de test: `services/dedicacion-api/tests/test_f029_completar.py`
(51 tests: 16 dominio, 20 caso de uso, 15 ruta) y
`services/dedicacion-front/tests/test_f029_seleccion.py` (25 estáticos).

### Decisiones de diseño (dentro de la spec)

- **Validación (R20-R22):** periodo (404/409) → obra (422) → nadie se toca.
  La obra, de `obras.listar_para_periodo` con la empresa de las obras; si se
  ofrece, de `Linea.ofrecible` (única definición). `_completar_uno`: una rama
  por resultado; YA_AL_100/EXCESO los decide el mismo `calcular_estado` (D5).
- **R1, Ctrl+clic con selección vacía sobre la propia fila del cursor:** se
  lee «si no estaba» en el momento del clic (`const estaba` antes de que
  entre el cursor), así esa fila queda marcada en vez de entrar y salir. Es
  lectura literal de R1, no desviación.
- **R2, Shift+clic sin ancla visible:** el rango sale del cursor. El ancla no
  se mueve con Shift (se puede rehacer el rango); sí con clic y Ctrl+clic.
- **Diálogo (R10, R11):** el campo y el contenedor `.modal` cortan la
  propagación (ni Enter/Esc sobre los botones llegan a `teclas`). Confirmar
  desactivado sin destino o con el envío en curso (no hay doble lote). Con
  error: diálogo abierto, `toast` y selección conservada. Botón con el editor
  abierto: «Cierra el editor (Esc)…» (la tecla C ni llega a `teclas`).

## Fase RED (trazas reales)

**T1 (dominio)** — test escrito antes que el código:

```
$ cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f029_completar.py -k dominio -q
E   ImportError: cannot import name 'completar_hasta_100' from 'domain.estados' (...\domain\estados.py)
ERROR tests/test_f029_completar.py
1 error in 1.44s
```
Tras el código: `15 passed in 0.29s`.

**T2 (caso de uso, R15-R20, R22)** — primero `ImportError: cannot import name
'CompletarHasta100' from 'application.use_cases'`; para que el fallo fuera de
aserción y no de importación, se puso un stub vacío temporal
(`return [], ResumenPeriodo()`, nunca commiteado) y se ejecutó:

```
$ .venv/Scripts/python -m pytest tests/test_f029_completar.py -k caso -q --tb=line
E   AssertionError: assert [] == [ResultadoCom...mal('49.50'))]          (r15 suma a la existente)
E   AssertionError: assert [] == [ResultadoCom...al('100.00'))]          (r15 sin carga)
E   AssertionError: assert Decimal('66.66') == Decimal('100.00')          (r16 total 100)
E   AssertionError: assert [(103, True, Decimal('40'))] == [(103, True, ...ecimal('60'))]   (r18)
E   ValueError: not enough values to unpack (expected 1, got 0)           (r19 un evento)
E   assert False is True                                                  (r19 puede_deshacer)
E   Failed: DID NOT RAISE ObraNoValida                                    (r22 / r20)
20 failed, 15 deselected in 5.74s
```
Tras el código: `35 passed in 4.65s`.

**T3 (ruta)**:
```
$ .venv/Scripts/python -m pytest tests/test_f029_completar.py -k ruta -q --tb=line
E   AssertionError: {"detail":"Not Found"}            (x13: la ruta no existía)
E   ImportError: cannot import name 'CompletarIn' from 'interface_adapters.api.schemas'
E   IndexError: list index out of range               (404: ni se abrió UoW)
15 failed, 35 deselected, 1 warning in 13.76s
```
Tras el código: `50 passed`; suite api entera `585 passed` (586 con el test de T8).

**T4 (front, R1-R7)**:
```
$ cd services/dedicacion-front && .venv/Scripts/python -m pytest tests/test_f029_seleccion.py -q --tb=line
E   AssertionError: no existe la función marcarSeleccion en app.js
E   assert 'tr.addEventListener("mousedown", (ev) => { if (ev.shiftKey) ev.preventDefault(); });' in 'function construirFila(t) { ...'
E   assert 'if (state.seleccion.has(t.ide)) tr.classList.add("multi");' in 'function construirFila(t) { ...'
E   assert 'else if (ev.key === "Escape" && state.seleccion.size) { fijarSeleccion([]); }' in ' }'
E   AssertionError: cambiarEmpresa
E   AssertionError: no existe la función fijarSeleccion en app.js
10 failed, 2 passed in 0.10s
```
Los 2 que pasaban son guardas de regresión de R5 (`teclas` de antes literal):
deben pasar antes y después.

**T5 (front, R8-R13)**:
```
E   AssertionError: no existe la función abrirCompletar en app.js
E   AssertionError: no existe la función seleccionEfectiva en app.js
E   AssertionError: no existe la función candidatasDestino en app.js
E   AssertionError: no existe la función lanzarCompletar en app.js
E   assert 'Ctrl/Shift+clic seleccionar varios' in 'muted small"> ↑↓ moverse · Enter editar · ...'
13 failed, 12 passed in 0.17s
```
Tras el código: front entero `53 passed`.

## Verificaciones adicionales hechas (no sustituyen a T9)

- `node --check static/js/app.js`: sintaxis OK. **Comportamiento en node** (script desechable, `vm` y DOM falso, no
  versionado): 17 comprobaciones OK de `marcarSeleccion` (Ctrl+clic, Shift+clic
  en los dos sentidos, rango solo de visibles), `seleccionEfectiva`,
  `fijarSeleccion` y `candidatasDestino` (`0656` → `0656`, `10656`,
  `Postv-0656`; obra cerrada → solo `Postv-`; sin texto → ninguna).
- BBDD local (solo lectura): 196 activos, 313 obras de la 1, 10/2026 ABIERTO.

## Resultado de `bash harness/init.sh`

Ejecutado tal cual al final (tras T8), **ENTORNO LISTO**:

```
[OK] pytest en verde (con medición de cobertura)      418 passed, 1 skipped in 57.35s  (raíz)
[OK] servicio api: pytest en verde                    586 passed, 1 warning in 45.93s
[OK] servicio front: pytest en verde                  (53 passed en la pasada anterior; caché)
[OK] servicio transfer: pytest en verde               (379 passed, ejecutado a mano: lee app.js)
[OK] PUERTA COBERTURA: 100.0% de 84 líneas cambiadas cubiertas (84/84, umbral 80%, nivel estandar)
[OK] PUERTA TAMAÑO: F-029 dentro de los topes (requirements 145/150, design 248/250)
[AVISO] ruff: 222 avisos (deuda previa, no bloquea)
```
Ruff nuevos: el estilo ya existente (`FURB157`, `F811` del fixture, como F-027).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | api **586 passed**; front **53 passed**; transfer **379 passed**; raíz **418 passed, 1 skipped**. Cero fallos. Nuevos de F-029: 51 (api) + 25 (front) |
| Cobertura de las líneas cambiadas | **100,0 %** (84/84), `PUERTA COBERTURA` |
| Mutantes (campaña final) | **20 generados, 20 muertos, 0 supervivientes**, 0 timeouts, en serie (`--workers 1`), SHA `53e3f79`, campaña completa → `progress/mutacion_F-029.md` |
| Mutantes (1.ª campaña) | 20 / 17 muertos / 3 supervivientes (SHA `21ec1ee`). Dos `frozen` = hueco real, matado con test (T8). El tercero, `use_cases.py:380` `is`→`is not`: **falso superviviente**, reproducido a mano con la orden exacta de la campaña y muere en `test_f029_r17_caso_ok_y_exceso…`; en la 2.ª campaña, mismo código, muerto. Causa no encontrada en el arnés: **aviso al líder**. Detalle en el «Historial» de `mutacion_F-029.md` |
| Tiempo de la suite | api 45,9 s; raíz 57,4 s; front ~2 s; transfer ~5 s. Campaña: 643 s (1.ª), 398 s (2.ª) |
| JS | Fuera de la herramienta de mutación y de cobertura (no es Python): lo cubren los 25 tests estáticos, la comprobación en node y T9 |

## Cómo probarlo en local (antes de desplegar)

Desde esta rama, en **Git Bash**, dos terminales (el transfer NO hace falta
para T9; no pulses «Registrar en Sigrid» ni «Sincronizar Sigrid»):

```bash
# Terminal 1 · api (puerto 8090; usa su .env con PG_HOST=localhost)
cd /c/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-api
.venv/Scripts/python main.py

# Terminal 2 · front (puerto 8080; API_BASE_URL=http://127.0.0.1:8090)
cd /c/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-front
.venv/Scripts/python main.py
```

Abrir `http://localhost:8080` (crea el periodo del mes si falta, ABIERTO).
**¿Hay trabajadores en FALTA?** La base local ya tiene datos (196 activos,
octubre ABIERTO casi vacío). SIN_CARGA también se completa; para tener alguno
en FALTA: Enter sobre él y `60 Enter <código> Enter` (solo base local).

**Si la base local estuviera vacía**, dos caminos:

1. *Sin Sigrid* (recomendado): sembrar a mano en la base local con el venv de
   la api. Ides altos para no chocar con los de Sigrid:
   ```bash
   cd /c/Users/pgris/PycharmProjects/porcentajes/services/dedicacion-api
   .venv/Scripts/python -c "
   from sqlalchemy import text
   from config.settings import get_settings
   from infrastructure.db.database import crear_engine
   with crear_engine(get_settings()).begin() as c:
       c.execute(text(\"INSERT INTO obra (ide, cod, descripcion, activa, empresa, admite_postventa) VALUES (990001,'9901','OBRA PRUEBA A',true,1,true),(990002,'9902','OBRA PRUEBA B',true,1,false) ON CONFLICT DO NOTHING\"))
       c.execute(text(\"INSERT INTO trabajador (ide, cod, nombre, categoria, activo, empresa) SELECT 990100+g, 'P'||g, 'PRUEBA '||g, 'Encargado', true, 1 FROM generate_series(1,5) g ON CONFLICT DO NOTHING\"))
   "
   ```
   Se borran igual: `DELETE` de `asignacion` y `evento` con `trabajador_ide
   >= 990100`, luego `trabajador` (`ide >= 990100`) y `obra` (`ide >= 990001`).
2. *Sync local* (`POST /api/v1/sync` o el botón, solo en este caso): **lee**
   Sigrid vía `sigrid-api` y escribe solo en la base local, pero pide el
   universo de postventa al transfer y **falla entero sin él** (F-025):
   arrancar también `services/dedicacion-transfer` (`.venv/Scripts/python
   main.py`, `OBRA_PRUEBAS_FORZAR=true`; el universo solo lee).

## Verificación MANUAL pendiente · T9 (humano)

Local, SIN Sigrid, con api y front como arriba. Periodo en curso ABIERTO.

- **(a) Selección.** En «Filtrar obra…» escribe el código de una obra con
  varios trabajadores. Ctrl+clic en dos filas y Shift+clic en una tercera.
  *Debe verse:* filas en violeta claro (distinto del burdeos del cursor),
  «Mostrando X de Y · N seleccionados», sin editor ni texto seleccionado.
  Clic simple: vacía y abre el editor; Esc (editor cerrado) vacía.
- **(b) Completar.** Pulsa **C** (o el botón «Completar al 100 %»). *Debe
  verse:* diálogo con el campo precargado con el filtro, la obra elegida
  («Destino: 0656 · …») o la lista si casa con normal y `Postv-` (↑ ↓ para
  elegir), los nombres y, si hay seleccionados ocultos por filtros, «N
  seleccionado(s) quedan fuera…». Enter. *Debe verse:* resultado con nombres
  («completado (+40%)»; «sin cambios: ya estaba al 100 %»), cuadrante
  recargado con los completados al 100 % en esa obra y sus otras obras
  igual; selección vacía.
- **(c) Deshacer.** Ctrl+Z sobre una fila completada (o su ↩): vuelve a lo
  de antes del lote.
- **(d) Regresión del teclado, sin selección:** ↑ ↓; Enter abre el editor;
  `60 Enter <código> Enter` añade la obra; Esc cierra; R, F7, F8, Ctrl+Z y
  «/» como antes. Ctrl+C dentro de un campo copia (no abre el diálogo).
  Periodo CERRADO: botón desactivado y C no hace nada.
- **(e) Contraste por la api:**
  `curl -s -X POST "http://localhost:8090/api/v1/periodos/<año>/<mes>/completar" -H "Content-Type: application/json" -H "X-Usuario: prueba" -d '{"trabajadores":[<ide>],"obra_ide":<obra_ide>}'`
  → `resultados[0].resultado` y `anadido` coherentes con el cuadrante (y un
  `obra_ide` inexistente → 422 con el motivo).

Resultado de (a)-(e): **pendiente del humano**.

## Fuera de alcance / qué falta para cerrar

- Fuera (design §9): Sesame (F-021), deshacer el lote de una vez, vista
  previa de cifras, Shift+flechas, registrar en Sigrid tras completar.
- Falta: **T7** (líder: copiar el párrafo nuevo de `INTEGRACION.md` §5 a
  `azure-apps/dedicacion.md`, literal), **T9** (humano) y la review.
