# F-047 · Informe del implementer — Tope de filas del transfer (obras con más de 2.000 partidas)

Rama `feature/F-047-tope-filas-transfer`. Rigor **crítico**, `sdd: false`. Solo
`dedicacion-transfer` (api y front intactos). Nada contra Azure ni Sigrid; el
script de escritura no se ha ejecutado. No tocados: `.env`, `features.json`,
`azure-apps/`; de `current.md`, solo la línea «**Estado:**» de F-047.

## Qué cambió

| Commit | Tarea |
|---|---|
| `7c81b7c` T1 | Tope configurable + tests (fase RED abajo) + `.env.example` |
| `354ddbb` T2 | `docs/INTEGRACION.md` §3 y §7, `docs/ARCHITECTURE.md` (topes de sigrid-api) |
| `c75d3e8` T3 | Campaña de mutación (`progress/mutacion_F-047.md`) y orden de imports del test (ruff I001) |

Producción (+21/−1), todo en `services/dedicacion-transfer/`:

- `infrastructure/sigrid/sigrid_write_client.py`: `MAX_ROWS_POR_DEFECTO =
  200_000`; el constructor admite `max_rows` (defecto esa constante, como
  `int`) y `_read` lo manda en vez del `2000` fijo. **El `RuntimeError` ante
  `truncated` se mantiene tal cual** (F-037 R7/R16).
- `config/settings.py`: `sigrid_max_rows = Field(200_000, alias="SIGRID_MAX_ROWS")`.
- `interface_adapters/api/app.py` (`build_app`) y
  `prueba_escritura_porcentajes.py` (`_cliente`), los dos únicos sitios que
  construyen el cliente: inyectan `max_rows=<ajustes>.sigrid_max_rows`.
- `.env.example`: `SIGRID_MAX_ROWS=200000` con su comentario.

**Tests anteriores que cambian (solo dobles, ninguna aserción):**
`tests/conftest.py` (`SettingsFalso.sigrid_max_rows`, lo usan las rutas de
F-025 y F-039) y los ajustes `SimpleNamespace` de `test_f022_obra_por_empresa.py`
y `test_f024_obra_destino_otra_empresa.py`: `build_app` lee ahora el ajuste.

### Decisiones

- **Variable `SIGRID_MAX_ROWS`** (el encargo sugería p. ej.
  `SIGRID_API_MAX_ROWS`): el mismo nombre que ya usa la api para lo mismo
  (`docs/INTEGRACION.md` §3) y vecino de `SIGRID_MAX_STATEMENTS`.
- **Dato a corregir en el encargo:** el `sigrid_max_rows` de la api vale
  **5.000** (`services/dedicacion-api/config/settings.py:65`), no 200.000. La
  api no se toca.
- Defecto en el cliente (constante) y en el ajuste (literal): settings no
  importa de infrastructure; cada uno con su test y su mutante muerto.
- `ARCHITECTURE.md` decía «paginar, no subir el tope» (del cliente de la api):
  añadido que el transfer es la excepción por decisión del humano.

### Otras lecturas del transfer (punto 1)

Todas pasan por el mismo `_read` y heredan el tope; ninguna depende de otro:
`lineas_por_synckey` trocea en lotes de 200 **claves** por el límite de
parámetros del `IN` (~2.100 en SQL Server), no por filas (una línea por
clave); `horas_de_recursos` y `partidas_de_lineas`, igual (límite de
parámetros); `inspeccionar_mensuales` lleva su `TOP`. `capitulos_de_obra`, la
que fallaba, la usan además `universo_postventa` (`POSTV2`) y
`universo_var`/`cargar_catalogo_var` (`VAR`): si esas obras pasaran de 2.000
partidas también se habrían caído; no lo he medido (nada contra Sigrid).
**Riesgo residual:** el corte del balanceador a los 230 s con la obra mayor
(`BD`, 26.812 partidas); no medido. **`partes`** (solo lectura):
`partes-transfer` pide `max_rows: 1000` fijo
(`partes/services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:94`)
pero lee `obrparpar` por lista de ids, no el presupuesto entero.

## Punto 4 · ¿Un error en una obra impide registrar las demás?

**Conclusión: no, en el código.** Cada obra es una petición independiente al
transfer y un fallo se queda en su obra. Evidencia:

1. Transfer: el error de una petición (la de UNA obra) se devuelve como
   `502 {"ok": false, "error": ...}`
   (`services/dedicacion-transfer/interface_adapters/api/app.py:158-161`
   preflight, `:186-189` ejecutar). La lectura falla antes de escribir: de esa
   obra no se escribe nada.
2. Cliente de la api: no lanza; convierte cualquier fallo en
   `{"ok": False, "error": ...}`
   (`services/dedicacion-api/infrastructure/transfer/transfer_client.py:20-33`).
3. Api: agrupa las líneas **por obra** (`application/registro_sigrid.py:100`)
   y recorre todas en bucle, sin cortar: preflight `:128-132`, ejecutar
   `:145-152`; solo traza (`_trazar`) las obras con `ok`. El `ok` global es
   `False` si falla alguna, pero el resto se ha escrito igual.
4. Front: en el modal de preflight, una obra con error pinta su caja roja y
   sigue con las demás (`static/js/app.js:1705`, `return` dentro de
   `forEach`); el botón «Registrar» se pinta siempre (`:1752`). Tras ejecutar,
   el aviso solo da cuentas (`:1776-1782`, rojo si `!r.ok`) y **no enseña qué
   obra falló ni por qué**.

Comprobación empírica (script desechable en el scratchpad, sin BBDD ni red:
`RegistroSigrid` con `_payloads` y transfer falsos, 0696 falla y 0699 no):

```
ejecutar: {'ok': False, 'obras': [{'obra': {'ide': 1, 'codigo': '0696'}, 'ok': False, 'error': 'sigrid-api devolvio una respuesta truncada'}, {'obra': {'ide': 2, 'codigo': '0699'}, 'ok': True, 'escritas': [{'registro_id': 2}], ...}], 'no_vigentes': []}
llamadas al transfer: ['0696', '0699', '0696', '0699']
trazadas: [{'ok': True, 'escritas': [{'registro_id': 2}], ...}]
```

**Por qué pudo verse «no me registra nada»** (hipótesis, sin datos): el
botón «⇪ Sigrid» de una fila (`app.js:896`, `:1033`) manda solo ese
trabajador; si todo lo de Bas Leal estaba en la 0696, todo iba en la petición
que fallaba. Y la **postventa** de la 0696 viaja en la misma petición
(`registro_sigrid.py:96-101`, `es_postventa` es campo de la línea): basta una
línea normal sin partida manual para leer el presupuesto
(`registro_pipeline.py:374-381`) y que caiga la petición entera. El aviso
final dice «0 escritas» en rojo sin nombrar la obra ni el error.

No se ha cambiado nada de este comportamiento (encargo: lo propone el líder).

## Fase RED (trazas reales)

Tests escritos antes que el código. Comando (desde `services/dedicacion-transfer`):

```
.venv/Scripts/python.exe -m pytest tests/test_f047_tope_filas.py -q --tb=short -p no:cacheprovider -k "por_defecto_que_se_envia or mas_de_2000"
```

Salida antes del cambio (el segundo reproduce **el error de producción**):

```
___________ test_f047_a1_el_tope_por_defecto_que_se_envia_es_200000 ___________
tests\test_f047_tope_filas.py:129: in test_f047_a1_el_tope_por_defecto_que_se_envia_es_200000
    assert [p["max_rows"] for p in api.peticiones] == [TOPE_DEFECTO]
E   assert [2000] == [200000]
_______ test_f047_a3_obra_con_mas_de_2000_partidas_resuelve_su_partida ________
tests\test_f047_tope_filas.py:230: in test_f047_a3_obra_con_mas_de_2000_partidas_resuelve_su_partida
    pf = _preflight(cli)
application\pipelines\registro_pipeline.py:380: in preflight
    self._cli.capitulos_de_obra(int(origen.ide)))
tests\test_f047_tope_filas.py:114: in capitulos_de_obra
    return self.real.capitulos_de_obra(obride)
infrastructure\sigrid\sigrid_write_client.py:169: in capitulos_de_obra
    return self._read(
infrastructure\sigrid\sigrid_write_client.py:91: in _read
    raise RuntimeError("sigrid-api devolvio una respuesta truncada")
E   RuntimeError: sigrid-api devolvio una respuesta truncada
2 failed, 8 deselected in 0.96s
```

Fichero completo antes del cambio: `10 failed` (TypeError por `max_rows`
desconocido, `AttributeError` de `sigrid_max_rows`, `.env.example` sin la
variable). Después: `10 passed in 2.15s`; suite del transfer `655 passed`.

**a3 sin red:** `SigridApiEmulada` sustituye a `httpx.post` como
`/api/sql/read` (`rows[:max_rows]`, `truncated` si sobran); 3.024 partidas de
relleno y la del encargado **al final**, tras la fila 2.000; el pipeline la
lee con el `capitulos_de_obra` y el `_read` **reales** (`ClienteObraGrande`).

## Tests nuevos

10 en `test_f047_tope_filas.py`, nombrados `test_f047_aN_*` por el
`acceptance` N: a1 (tope enviado por defecto y configurado, todas las lecturas,
ajuste, inyección en app y script, `.env.example`), a2 (obra mayor que el tope
= error en cliente y preflight, nada escrito; frontera exacta) y a3 (3.027
filas → `paride 80001`, `CI.1.10`, `escribir`).

## Documentación

- `docs/INTEGRACION.md` §3: fila `SIGRID_MAX_ROWS`; §7: bajar el
  `MAX_ALLOWED_ROWS` de sigrid-api por debajo del presupuesto de una obra la
  deja sin poder registrarse.
- **Pendiente del líder:** portar ambas cosas a
  `C:\Users\pgris\PycharmProjects\azure-apps\dedicacion.md` (no tocado).
- **Infra:** `infra/create_transfer_dedicacion.ps1:85-106` fija las variables
  del transfer y no lleva `SIGRID_MAX_ROWS`: **vale el defecto** (200.000).

## MANUAL pendiente (humano, en local, solo lectura)

Transfer local con su `.env` en modo pruebas (`OBRA_PRUEBAS_FORZAR=true`; sin
`SIGRID_MAX_ROWS`, vale el defecto). En PowerShell:

```powershell
cd C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-transfer
.\.venv\Scripts\python.exe main.py
# en otra consola: debe decir modo_pruebas = True
Invoke-RestMethod http://localhost:8006/health
```

Opción A (front local, si la base local tiene septiembre): septiembre 2026,
fila de **Bas Leal, José María**, botón «⇪ Sigrid» de la fila → en el modal, la
obra **0696** sin «respuesta truncada» y con partida elegida → **Cancelar**
(no pulsar «Registrar»).

Opción B (solo el transfer, `preflight` no escribe). `<IDE>` es el `ide` del
trabajador en el cuadrante (`res.ide`) y `<CATEGORIA>` su categoría:

```powershell
$cuerpo = @{ obra = @{ codigo = "0696" }; pisar_claves = @(); lineas = @(@{
  registro_id = 990001; ano = 2026; mes = 9; porcentaje = 1.0; empresa = 1
  recurso_ide = <IDE>; nombre = "Bas Leal, José María"; categoria = "<CATEGORIA>" }) } |
  ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri http://localhost:8006/api/registro/preflight `
  -ContentType "application/json; charset=utf-8" `
  -Body ([Text.Encoding]::UTF8.GetBytes($cuerpo)) | ConvertTo-Json -Depth 8
```

Esperado: `ok: true`, `forzada_pruebas: true`, ninguna «respuesta truncada»,
y en `acciones` la línea con `accion: escribir` y `paride`/`partida_cod` de la
0696 (o `aviso` de sin partida si su categoría no casa con ninguna, que ya no
es el fallo de F-047). **No** usar `/api/registro/ejecutar`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| `bash harness/init.sh` | **verde**, código 0: «ENTORNO LISTO» (tras T3) |
| Tests transfer | **655 passed**, 1 warning previo (`test_pipeline_offline::test_preflight` devuelve valor) en **11.32 s** |
| Tests raíz (con cobertura) | **418 passed, 1 skipped** en **61.55 s**; api y front en verde (caché) |
| Tests F-047 | **10 passed** en 2.15 s (fase RED: 10 failed) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 3 líneas cambiadas cubiertas (3/3, umbral 80%, nivel critico)` |
| Mutación automática | `python -m harness.mutacion --feature F-047 --workers 1`: **2 generados, 2 muertos, 0 supervivientes**, 27.5 s → `progress/mutacion_F-047.md` |
| ruff | 237 avisos, los mismos que antes de F-047 (el I001 del test nuevo se corrigió en T3) |

**Mutación manual complementaria** (la automática solo generó los dos
literales 200.000): **11 mutantes, 10 muertos, 1 equivalente (M8, alias del
ajuste: pydantic-settings lee también por nombre de campo)**. Tabla, método
y justificación de M8 en `progress/mutacion_F-047.md` §«Campaña manual».

## Qué queda fuera y qué falta

- Fuera (por encargo): cambiar el trato de una obra con error (punto 4),
  paginar `capitulos_de_obra`, el tope de la api (5.000), medir la lectura de `BD`.
- Falta: la MANUAL del humano, portar a `azure-apps/dedicacion.md` (líder), el
  aviso a `partes`, la review y desplegar solo el transfer.
