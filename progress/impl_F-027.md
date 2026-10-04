# F-027 · Informe del implementer — Deshacer solo lo propio

Rama `feature/F-027-deshacer-por-usuario`, rigor **estándar**, `sdd: false`
(se trabaja contra los `acceptance` de `harness/features.json`). Decisión A
del humano (2026-10-04). Solo **api**; front comprobado, sin cambios.

## Qué cambió

| Commit | Tarea |
|---|---|
| `0988f6b` T1 | `domain/deshacer.py` (nuevo): `clave_usuario` (`strip().casefold()`) y `deshacer_permitido(autor, usuario)`. `domain/errors.py`: `DeshacerAjeno` |
| `2bc12f3` T2 | Puerto y repositorio: `ultimo_pendiente` devuelve `EventoPendiente(id, usuario, snapshot_antes)` (nuevo en `domain/models.py`); `trabajadores_con_pendientes` → `autores_ultimo_pendiente(periodo) -> {trabajador: autor}` con `max(id)` en SQL. Casos de uso y dobles adaptados **sin cambiar comportamiento** |
| `a7710a7` T3 | Regla A en `DeshacerUltimaModificacion`; `ObtenerCuadrante` y `ObtenerFilaTrabajador` reciben `usuario` (keyword obligatorio) y calculan `puede_deshacer` con `deshacer_permitido`. Rutas `cuadrante` y `export.xlsx` toman el `Usuario` de la cabecera; guardar, deshacer y copiar trabajador ya lo tenían |
| `94995b2` T4 | `app.py`: `(DeshacerAjeno, 409)`, como `NadaQueDeshacer` |
| `9e0c472` T5 | `docs/ARCHITECTURE.md`: regla 14 `#regla-deshacer` (y el ancla en la lista de fuentes únicas y en los endpoints) |
| `cc91bca` | Orden de imports del test (ruff I001) |
| `3d2db3b` T6 | Test que mata el superviviente de la 1.ª campaña de mutación |

**Regla** (`application/use_cases.py`): sin pendiente → `NadaQueDeshacer`
(igual que antes); pendiente de otro → `DeshacerAjeno("La última modificación
de este trabajador es de <autor>: solo puede deshacerla quien la hizo")` y no
se toca nada; pendiente propio → se restaura. Solo se mira el **último**
evento: nunca se deshace otro. `puede_deshacer` = la misma función con el autor
del último pendiente.

**SQL de `autores_ultimo_pendiente`** (test fija la sentencia compilada):
`SELECT trabajador_ide, usuario FROM evento WHERE id IN (SELECT max(id) FROM
evento WHERE periodo_id = :p AND deshecho IS false GROUP BY trabajador_ide)`.
Comprobada además **fuera de la suite** (los unit tests no tocan BBDD) contra
un SQLite en memoria con el repositorio real: eventos `10: ana, pablo` →
`pablo`; `14: pablo, ana, ana(deshecho)` → `ana`; `16: solo deshecho` → sin
entrada; otro periodo aparte. Salida real: `periodo 3: {10: 'pablo', 14:
'ana'}` / `periodo 4: {10: 'eva'}`.

### Decisiones de diseño

- **Una sola normalización**, en `domain/deshacer.py`: extremos y mayúsculas
  (`casefold`); el interior no se toca (`"pa blo"` ≠ `"pablo"`, test). No uso
  `domain/normalizacion.normalizar` porque quita acentos y colapsa espacios:
  podría fundir dos usuarios distintos.
- **`usuario` obligatorio (keyword)** en los dos casos de uso de lectura, sin
  valor por defecto: olvidarlo en una ruta falla en vez de apagar el deshacer
  en silencio. Por eso `export.xlsx` también recibe el `Usuario` (no lo usa).
- **El autor se compara en Python, no en SQL**: el SQL solo da el autor del
  último pendiente por trabajador; así la normalización vive en un sitio.
- El índice `ix_evento_periodo_trab_id` ya cubre la subconsulta; no hay DDL.

## Front (criterio 5): comprobado, sin cambios

- Botón (`app.js` ~627): se pinta solo si `t.puede_deshacer` y el periodo está
  `ABIERTO`. Ahora `puede_deshacer` es por usuario: el botón desaparece solo.
- `api()` (~108-120): ante cualquier no-2xx lanza `Error(cuerpo.error)`;
  `deshacer()` (~1051) lo pinta con `toast(err.message, true)`. El 409 enseña
  el motivo con el nombre del otro usuario.
- **Ctrl+Z** (~1279 y ~1300) **no consulta `puede_deshacer`**: llama siempre a
  la API, que aplica la misma regla y responde 409 con el motivo, que el toast
  enseña (igual que antes con «nada que deshacer»). **No lo cambio**: el front
  no decide nada y filtrar Ctrl+Z por `puede_deshacer` lo dejaría mudo en el
  único caso en que el usuario necesita saber por qué no puede. Lo dejo
  explícito para el reviewer por si se prefiere el filtro (sería una línea de
  presentación).

## Tests anteriores cambiados (por firma o por doble; ninguna aserción tocada)

| Test | Antes | Ahora | Motivo |
|---|---|---|---|
| `test_f024_cuadrante_empresa._Eventos` (doble; también lo usa el fixture `api`) | `ultimo_pendiente` → `(1, snapshot)`; `trabajadores_con_pendientes` → set; `marcar_deshecho` vaciaba todo | lista de `EventoPendiente` con autor; deshace uno a uno; `autores_ultimo_pendiente` → dict del último | puerto nuevo (T2); más fiel al repositorio |
| `test_f024_r10_puede_deshacer_se_conserva` | `eventos.pendientes[10] = []`; cuadrante sin usuario | `eventos.registrar(..., 10, GUARDAR, "u", [], [])`; `usuario="u"` | doble y firma; misma aserción |
| `test_f024_r7_…visibles`, `test_f034_r1_obras_siempre_de_la_empresa_de_las_obras`, `test_f024_r10_fila_con_todas_sus_lineas…`, `test_f024_r13_resumen_del_cuadrante_solo_visibles` | `ObtenerCuadrante().ejecutar(uow, A, M, filtro)` | `+ usuario="u"` | firma |
| `test_f024_r13_resumen_de_las_respuestas_por_fila` | `ObtenerFilaTrabajador(..., filtro=)` | `+ usuario="u"` | firma |
| `test_f025_cuadrante_postventa._Uow._Eventos` (doble) | tupla / set | `EventoPendiente` / dict de autores | puerto nuevo |
| `test_f025_r17_el_cuadrante_ofrece…` | sin usuario | `+ usuario="u"` | firma |
| `test_f034_r1_obras_leen_la_empresa_de_las_obras_no_la_elegida`, `test_f034_r1_obras_de_la_28_si…`, `test_f034_r4_filas_y_resumen_con_la_visibilidad_nueva` | sin usuario | `+ usuario="u"` | firma |

Ningún test perdió exigencia ni cambió por otra causa.

## Tests nuevos — `services/dedicacion-api/tests/test_f027_deshacer_propio.py` (25)

Dominio: misma persona con mayúsculas/espacios (3 casos); otro usuario,
prefijo, interior distinto y sin pendiente (4); `clave_usuario`; jerarquía de
`DeshacerAjeno`. Repositorio: `ultimo_pendiente` trae el autor; SQL y
parámetros de `autores_ultimo_pendiente`. Casos de uso con **Ana y Pablo**:
deshago lo mío; no deshago lo del otro (mensaje exacto, nada reemplazado ni
deshecho); el otro cambia después → bloqueado, y cuando él deshace el suyo,
yo sí; nada que deshacer sigue igual; deshacer con otras mayúsculas;
`puede_deshacer` del cuadrante por usuario (4 usuarios, incluido el caso
«Pablo tiene un evento en Ana, pero el último es de Ana»); `puede_deshacer` de
la fila de guardar (incluido guardar sin cambios), de `ObtenerFilaTrabajador`,
de deshacer (dos cambios propios seguidos) y de copiar trabajador; deshacer
con una obra que ya no existe. API: 409 con `{"error": <motivo>}` y mismo
código que «nada que deshacer»; el autor con otras mayúsculas sí deshace;
el otro cambia después; `puede_deshacer` del `GET cuadrante` según `x-usuario`.

## Fase RED (trazas reales)

T1 — `cd services/dedicacion-api && python -m pytest tests/test_f027_deshacer_propio.py -q`
(intérprete del venv de la raíz; los demás con `.venv/Scripts/python.exe` del servicio):
```
E   ModuleNotFoundError: No module named 'domain.deshacer'
1 error in 0.21s
```
T2 — `.venv/Scripts/python.exe -m pytest tests/test_f027_deshacer_propio.py -q -k r3`
con `EventoPendiente` ya en el modelo y el repositorio sin tocar:
```
E       AssertionError: assert (7, [{'obra_ide': 100}]) == EventoPendiente(id=7, usuario='ana@ruesma.es', snapshot_antes=[{'obra_ide': 100}])
E       AttributeError: 'PgEventoRepository' object has no attribute 'autores_ultimo_pendiente'
2 failed, 9 deselected in 1.65s
```
T3 — `.venv/Scripts/python.exe -m pytest tests/test_f027_deshacer_propio.py -q`:
```
E       Failed: DID NOT RAISE DeshacerAjeno
E       Failed: DID NOT RAISE DeshacerAjeno
E       TypeError: ObtenerCuadrante.ejecutar() got an unexpected keyword argument 'usuario'
E       TypeError: ObtenerCuadrante.ejecutar() got an unexpected keyword argument 'usuario'
E       TypeError: ObtenerCuadrante.ejecutar() got an unexpected keyword argument 'usuario'
E       TypeError: ObtenerCuadrante.ejecutar() got an unexpected keyword argument 'usuario'
E       TypeError: ObtenerFilaTrabajador.ejecutar() got an unexpected keyword argument 'usuario'
7 failed, 14 passed in 1.32s
```
Como el `TypeError` solo prueba la firma, repetí el RED de `puede_deshacer` en
un worktree temporal sobre T2 con la **firma nueva y la semántica vieja**
(`usuario` aceptado e ignorado), `-k "r3_puede_deshacer_por_usuario and not http"`:
```
E       AssertionError: assert {'Ana': True, 'Eva': True} == {'Ana': True, 'Eva': False}
E       AssertionError: assert {'Ana': True, 'Eva': True} == {'Ana': False, 'Eva': True}
E       AssertionError: assert {'Ana': True, 'Eva': True} == {'Ana': False, 'Eva': True}
E       AssertionError: assert {'Ana': True, 'Eva': True} == {'Ana': False, 'Eva': False}
E       AssertionError: assert True is False
5 failed, 16 deselected in 1.55s
```
T4 — `.venv/Scripts/python.exe -m pytest tests/test_f027_deshacer_propio.py -q`:
```
E       AssertionError: {"error":"La última modificación de este trabajador es de ana@ruesma.es: solo puede deshacerla quien la hizo"}
E       assert 400 == 409
2 failed, 22 passed, 1 warning in 3.92s
```
`test_f027_r3_por_http_puede_deshacer_por_usuario` no tuvo RED propio: pasó
en T4 porque las rutas ya pasaban el usuario desde T3 (su RED es el de T3).

## `bash harness/init.sh` (resultado real, tras T6)

`ENTORNO LISTO`. Raíz: 418 passed, 1 skipped (43.81 s; 36.07 s en la última pasada). Servicio api: **534
passed** (16.34 s); front y transfer en verde (caché). `PUERTA COBERTURA:
100.0% de 33 líneas cambiadas cubiertas (33/33, umbral 80%)`. ruff: 198
avisos, los mismos que al empezar (la 1.ª pasada dio 199 por el orden de
imports del test nuevo; corregido en `cc91bca`). `PUERTA TAMAÑO: F-027 dentro
de los topes (impl 196/220)`.

## Mutación — `python -m harness.mutacion --feature F-027 --workers 1`

Detalle y análisis en `progress/mutacion_F-027.md`.

- **1.ª campaña** (HEAD `cc91bca`): 8 generados, 6 muertos, **2
  supervivientes**, 77.9 s. Uno era **hueco real**: `use_cases.py:186`
  `permitir_inactivas=True → False` (ningún test deshacía un snapshot con una
  obra que ya no existe; comportamiento anterior a F-027 en una línea que
  reescribí). Cerrado con `test_f027_r6_deshacer_lo_mio_con_una_obra_que_ya_no_existe`,
  comprobado a mano contra el mutante (`ObraNoValida: Obras inexistentes: [777]`).
- **2.ª campaña** (HEAD `3d2db3b`, la que queda en el informe): 8 generados,
  **7 muertos, 1 superviviente**, 0 timeouts, 67.3 s.
- Superviviente: `models.py:134` `@dataclass(frozen=True) → frozen=False` en
  `EventoPendiente`. **Equivalente**: nadie modifica el valor; no hay
  comportamiento observable que cambie.
- Límite honesto: el generador solo produjo 8 mutantes (no muta llamadas como
  `strip`/`casefold` ni `max`/`group_by`). Esos puntos los fijan tests
  directos (normalización y sentencia SQL compilada), no la campaña.

## Fuera de alcance

Deshacer un cambio que no sea el último, deshacer por línea, historial
visible. La fila del front puede quedar con `puede_deshacer` desfasado si
otro usuario cambia después: al pulsar, la API responde 409 con el motivo y
la fila no se refresca hasta recargar (no hay push; sin cambio en F-027).

## Pendiente para el líder

- **`azure-apps/dedicacion.md`** (§ «La cadena de identidad»): `X-Usuario`
  ya no es solo auditoría, **decide quién puede deshacer**. Propuesta: en el
  diagrama, `auditoría (tabla evento) y permiso de deshacer (F-027)`. No lo he
  tocado: es otro repositorio y no estaba en el encargo.
- **MANUAL tras desplegar** (no hay ninguna antes del `done`): con dos
  personas en el mismo mes y trabajador, A guarda → B no ve el botón y su
  Ctrl+Z da el toast «La última modificación de este trabajador es de A…»; A
  deshace bien; si B guarda después, A ya no puede. Comprobar que el nombre
  del toast es el `X-MS-CLIENT-PRINCIPAL-NAME` real. Ojo: los eventos previos
  al despliegue llevan el usuario con el que se guardaron; si alguno quedó
  como `local`, nadie con Easy Auth podrá deshacerlo (es lo correcto).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | api 534 passed (25 nuevos de F-027); raíz 418 passed, 1 skipped; front y transfer en verde |
| Cobertura de líneas cambiadas | **100.0 %** (33/33), `PUERTA COBERTURA` |
| Mutantes generados / supervivientes | 8 / **1** (equivalente); 1.ª campaña 8 / 2, hueco cerrado |
| Tiempo de la suite | api 16.34 s; raíz 43.81 s (init.sh) |
