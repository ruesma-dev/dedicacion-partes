<!-- progress/explore_transfer_original.md -->
# Exploración del original `porcentajes-transfer`

Fuente: `C:\Users\pgris\PycharmProjects\porcentajes-transfer` (sin git) contra
`C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-transfer`.

> Informe producido por un subagente explorador de solo lectura el 2026-08-19.
> El subagente no tenía permiso de escritura, así que el fichero lo ha creado
> el líder con su contenido íntegro. Ningún valor de `.env` se ha transcrito.

## 1. Evidencia de pruebas reales contra Sigrid

**Solo existe un artefacto de ejecución: un log de 10 líneas.** No hay volcados
JSON, ni CSV, ni capturas, ni notas sueltas. `porcentajes-api` y
`porcentajes-front` no tienen ni carpeta `logs/`.

`porcentajes-transfer\logs\partes-transfer.log` — 1930 bytes, todo del
**2026-07-26**, cinco llamadas:

| Líneas | Hora | Obra pedida | Resultado |
|---|---|---|---|
| 1-2 | 13:23:26 → 13:23:30 | 0403 | `preflight obra=0404 partes=0 escribir=0 omitir=1 ya=0 conflictos=0` |
| 3-4 | 13:23:31 → 13:23:34 | 0403 | idéntico |
| 5-6 | 13:23:38 → 13:23:43 | 0404 | `partes=0 escribir=0 omitir=2` |
| 7-8 | 13:23:43 → 13:23:51 | 0404 | `partes=0 escribir=0 omitir=2` |
| 9-10 | 13:37:08 → 13:37:25 | 0404 | `partes=1 escribir=1 omitir=1 ya=0 conflictos=0` |

Cada par es `registro_pipeline.py:62` (aviso de MODO PRUEBAS) +
`registro_pipeline.py:283` (fin del preflight).

**No hubo ninguna escritura real en `hmores`.** La prueba es negativa pero
sólida:

- `sigrid_write_client.py:86-88` loguea a INFO **cada sentencia** SQL antes de
  mandarla (`[sigrid-write] …`). No aparece ninguna.
- `registro_pipeline.py:403` loguea `[registro] escritas=… borradas=… filas=…`
  tras toda ejecución. No aparece.
- `registro_pipeline.py:366` loguea `parte creado`. No aparece.
- `registro_pipeline.py:308`: `ejecutar()` llama primero a `preflight()`, así
  que una ejecución dejaría la línea de preflight **y** después o bien
  `escritas=` (403) o bien `nada que escribir` (336). Tras la línea 10 no hay
  nada ⇒ fue una llamada a `/api/registro/preflight`, no a `ejecutar`.
- El handler de fichero es rotatorio con `backupCount=5`
  (`config/logging_config.py:21-24`) y **no hay ficheros `.1`…`.5`**: no se ha
  perdido nada por rotación.

**Quién lanzó esas llamadas.** No fue `prueba_escritura_porcentajes.py`: ese
script fija la obra origen `0678` (`:52`) y el log dice 0403/0404. El patrón
coincide con `services/dedicacion-api/application/registro_sigrid.py:63-80`,
que agrupa el payload por obra. Es decir: **prueba end-to-end front/API →
transfer → sigrid-api, en modo preflight**.

**Modo pruebas activo.** Las cinco llamadas dispararon `OBRA_PRUEBAS_FORZAR`
(`settings.py:29-30`): todo se desviaba a la obra `0404`.

**Casi todo se omitía.** `omitir=1`/`omitir=2` en todas las corridas,
`escribir=0` salvo la última. Los motivos no se loguean, pero por
`reglas_porcentajes.py:87-104` solo pueden ser «sin recurso en Sigrid» o «sin
código M*». En la última corrida (13:37) una línea sí quedó lista para
escribir, y ahí se paró.

**Ventana ciega:** el directorio `logs/` se creó el 2026-07-26 a las 12:09 y el
`.env` a las 12:08. Cualquier ejecución anterior (el trabajo del 25/07) **no
dejó rastro en fichero**.

**Evidencia indirecta de lecturas reales sí verificadas:** los docstrings
afirman haber confirmado el modelo contra datos reales —
`sigrid_write_client.py:4` («Modelo del parte de trabajo, confirmado contra
datos reales, 25/07/2026»), incluido que `ortide` es NOT NULL sin default
(`:9-11`), y `reglas_porcentajes.py:4` / `README.md:8` fechan las reglas en
«Administración, 25/07/2026». Es un dato que solo sale de mirar filas reales,
pero **el volcado no se guardó**.

## 2. Scripts de prueba disponibles

`porcentajes-transfer\prueba_escritura_porcentajes.py` (233 líneas, idéntico al
migrado). CLI argparse (`:202-208`) con `--confirmar`, `--ano`, `--mes`,
`--pisar`. Fases:

| Fase | Línea | Qué hace |
|---|---|---|
| `inspeccionar` | `:77` | Vuelca las 20 últimas líneas `M*` reales (`can/canres/pre/tot/paride/caaide`) + `TOP 10 hderes`. Paso previo obligado para fijar el mapeo. |
| `capitulos` | `:91` | Lista los capítulos de la obra de postventa para verificar el casado. |
| `estado` | `:104` | Parte de la obra de pruebas del mes y todas sus líneas. |
| `preflight` | `:128` | Preflight de las líneas de ejemplo; imprime acciones y conflictos. |
| `ejecutar` | `:151` | Escribe; sin `--confirmar` es dry-run (`:155`). Avisa si `OBRA_PRUEBAS_FORZAR=false` (`:157-159`). |
| `verificar` | `:172` | Relee por `synckey` lo escrito. |
| `limpiar` | `:183` | Borra solo lo marcado `MARCA_PRUEBAS` en `tex` y con synckey `porcentajes:%`. |

**Hallazgo decisivo:** las líneas de ejemplo `LINEAS_PRUEBA` (`:40-48`) siguen
con los marcadores de plantilla — `"EDITAR: encargado con MENC"`, `"EDITAR:
jefe de obra con MJEFO"`, `empleado_ide: 0`. El `README.md:59-61` prescribe la
receta «`estado` → **editar `LINEAS_PRUEBA`** → `ejecutar --confirmar` →
`verificar` → pantalla de Sigrid → `limpiar --confirmar`». **Ese paso de
edición nunca se hizo**, y con `empleado_ide=0` la fase `ejecutar` habría
omitido las tres líneas. Corrobora que el script nunca escribió nada real.

Otros: `tests/test_pipeline_offline.py` (245 líneas, cliente falso, sin red) y
`main.py` (uvicorn, puerto 8006). **No hay notebooks ni ningún otro
`prueba_*.py` / `test_*.py`.**

## 3. Diferencias con el código migrado

**Ninguna. Los dos árboles son byte a byte idénticos en todo el código.**

`diff -r` (excluyendo `.venv`, `__pycache__`, `.idea`, `logs`, `.env`) devuelve
solo tres entradas, y las tres son de presencia, no de contenido:

- `.env.example` — solo en el monorepo (añadido en la migración).
- `.gitignore` — solo en el original.
- `ARCHIVADO.md` — solo en el original (nota de archivado, 2026-08-19).

Los 5 ficheros nucleares coinciden en tamaño y contenido: `registro_pipeline.py`
(413 líneas), `reglas_porcentajes.py` (118), `sigrid_write_client.py` (336),
`main.py` (23), `prueba_escritura_porcentajes.py` (233).

Confirmado también por git: `git log -- services/dedicacion-transfer` da 3
commits (`dfb828f` migración, `a15abc3` arnés, `d6a72a1`), y `d6a72a1` tocó
**solo `coverage.json`** en ese servicio.

**No se migró:** el `logs/` con la única evidencia de ejecución, y el
`.gitignore`. **Se añadió:** `.env.example` y artefactos de test. No hay lógica
perdida ni lógica cambiada.

## 4. Las tres afirmaciones del humano, verificadas

Como los ficheros son idénticos, **cada cita vale para los dos árboles en el
mismo número de línea**. Ninguna de las tres difiere entre árboles.

### 4.1 Fecha = último día del mes — **CUMPLE**

- `domain/models/registro_models.py:37-41` — `LineaEntrada.fecha_int` calcula
  `calendar.monthrange(ano, mes)[1]` y compone `YYYYMMDD`.
- `application/services/reglas_porcentajes.py:67` — la acción hereda ese
  `fecha_int`.
- `application/pipelines/registro_pipeline.py:390` — se pasa al insert.
- `infrastructure/sigrid/sigrid_write_client.py:314` — llega tal cual a
  `hmores.fec`.
- La cabecera del parte también: `sigrid_write_client.py:281-282`.
- Cubierto offline: `tests/test_pipeline_offline.py:166` y `:203` asertan
  `20260731`.

### 4.2 `can` = porcentaje sobre 1, y `tot` en consecuencia — **CUMPLE**

- `reglas_porcentajes.py:95-96` — rechaza (omite) todo lo que no esté en
  `0 < p <= 1`. Un `40` se omite: `test_pipeline_offline.py:145-146`, `:172`.
- `reglas_porcentajes.py:112-116` — `can = round(porcentaje, 4)`,
  `pre = hora.pre` (importe mensual de `reshor`), `tot = round(can * pre, 2)`.
- `sigrid_write_client.py:316` — el valor realmente escrito se recalcula ahí:
  `round(float(can) * float(pre), 2)`, con `can` a 4 decimales (`:315`).
  `AccionLinea.tot` es informativo.
- Verificado offline: 0,4 × 9.000 = 3.600,0 (`test_pipeline_offline.py:164-165`).
- **De punta a punta:** la BBDD guarda 0-100 (`docs/ARCHITECTURE.md:84`) y la
  conversión la hace el api en
  `services/dedicacion-api/application/registro_sigrid.py:72`
  (`round(float(a.porcentaje) / 100.0, 4)`). El transfer no convierte: si
  alguien le manda 40, lo omite.
- **Matiz no verificado:** cuando el recurso tiene varios códigos `M*`, se
  elige el **primero por orden alfabético** (`reglas_porcentajes.py:105`), y de
  ahí sale el `pre`. Es una heurística **sin confirmar con Administración**.

### 4.3 Imputación a la obra indicada, y en postventa a la partida — **CUMPLE con dos matices**

- **Obra normal:** el destino se resuelve por `ide` o `codigo` de la obra
  pedida (`registro_pipeline.py:66-76`) y el insert lleva `obride = obra.ide`
  (`sigrid_write_client.py:313`). La partida se casa contra el presupuesto de
  la **obra origen** por categoría+nombre (`registro_pipeline.py:177-195`,
  `partida_resolver.py:35-44`); sin casado, `paride = 0` + aviso.
- **Postventa:** `reglas_porcentajes.py:76-85` marca `destino="postventa"`;
  `registro_pipeline.py:79-108` resuelve la obra de postventa (`POSTV2`) y
  busca dentro de ella la partida cuyo código es el de la obra original
  (`partida_resolver.py:47-76`: exacto > empieza por > en la descripción >
  nombre). Sin casado, la línea **se omite**. Verificado offline:
  `test_pipeline_offline.py:158-159` (obra 0678 → `paride=70001`).

**Matiz 1 — modo pruebas.** `registro_pipeline.py:56-65`: con
`OBRA_PRUEBAS_FORZAR` (por defecto `True`) **toda** escritura se desvía a
`OBRA_PRUEBAS_COD` (`0404`), ignorando la obra indicada. Las cinco corridas de
julio corrieron así. **La afirmación «se imputa a la obra indicada» no se ha
probado nunca contra Sigrid**, porque nunca se ha ejecutado con ese flag en
`false`.

**Matiz 2 — en postventa cambia la obra, no solo la partida.** El código no
solo cambia la partida: **la línea se escribe en otra obra** (`POSTV2`), y
dentro de ella en la partida de la obra original. (El humano lo confirmó
verbalmente el 2026-08-19 al cerrar D1, y la lectura C2 de
`progress/sigrid_F-002.md` lo respalda con datos.)

## 5. Lo que NO se ha podido determinar

- **Si alguna vez se escribió o borró una fila real en `hmores`.** El log lo
  desmiente para las cinco corridas registradas, pero no cubre el 25/07 ni la
  mañana del 26/07. La única forma de cerrarlo es consultar Sigrid por
  `synckey LIKE 'porcentajes:%'` o por `CAST(tex AS NVARCHAR(200)) =
  'PRUEBA-PORC'` — lo que hace `prueba_escritura_porcentajes.py:184-187`.
- **Si el `inspeccionar` llegó a ejecutarse y qué devolvió.** Los docstrings lo
  afirman, pero no hay volcado. Sigue abierto lo que el propio `README.md:57-59`
  deja pendiente: si `paride`/`caaide` deben ir rellenos. Hoy `caaide` se
  escribe a 0 sin confirmar (`sigrid_write_client.py:304-305`, `:311`).
- **Si el casado de capítulos de `POSTV2` funciona con datos reales.** Lo único
  verificado es el test offline con capítulos inventados. (La lectura C2 del
  2026-08-19 cubre ya la estructura del presupuesto: ver
  `progress/sigrid_F-002.md`.)
- **Los motivos de omisión de las corridas de julio** (omitir=1/2): no se
  loguean, solo el contador.
- **Quién disparó las llamadas** (UI del front o curl): no hay access log de
  uvicorn en fichero.
- **El contenido del `.env`.** No se ha leído. Existe en
  `porcentajes-transfer\.env` y en `porcentajes\services\dedicacion-transfer\.env`;
  declara las mismas claves que `config/settings.py`, entre ellas una
  credencial de acceso a sigrid-api. **Ningún valor se ha transcrito.**
