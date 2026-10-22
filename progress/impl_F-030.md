<!-- progress/impl_F-030.md -->
# F-030 · Informe del implementer (incidencias en el cuadrante)

Rama `feature/F-030-dias-bajas-incidencias` (copia `porcentajes-f030`),
rigor **crítico**. Dos entregas, un commit `F-030 Tn` por tarea:

- **T1-T19 y T21** (`8b17e85`): detalle completo (decisiones D-a…D-g, lista
  cerrada de T4-T16, fusión de `dev`, trazas RED de T2-T19, mutación de T21)
  en **`progress/impl_F-030_anexo.md`**; aquí, el resumen de §1.
- **Anexo R30, T22-T37** (código cerrado en `b614b91`): cambiar los días de
  una incidencia registrada **edita la `fec`** de su par, nunca escribe otro
  (D11-D15 del humano). El resto de este informe.

**T20 (MANUAL) es del líder** (§7). Nada escrito ni leído en Sigrid, ningún
`push`, ningún `.env` tocado.

## 1. Qué hacía ya F-030 (T1-T21, resumen)

api: catálogo `auxhor` (`CI*`), tabla `incidencia`, `GET /incidencias` y
`PUT …/incidencias` con evento deshacible, fuera del 100 %, payload y traza.
Front: letras en la celda del %, chip «del/al», subfilas, sección del modal.
Transfer: el par `CI*`/`CIZ` con `can = 0`, R27, una lectura, script
`--incidencia`. Docs: regla 21 `#regla-incidencia`, `INTEGRACION.md`.

## 2. Qué cambió en el anexo R30 (T22-T37)

- **Contrato** (T22): `tests/contratos/f030_r30.json`, la petición que la
  api debe mandar y lo que el transfer debe hacer (6-9 y 12-14), probado en
  dos mitades sin red (`test_f030_r30_punta_a_punta.py` en api y transfer).
- **api** (T23-T26):
  - `incidencia` + `quitada` (no nula, `false`), `sigrid_dia_ini`,
    `sigrid_dia_fin` (`alters_faltantes`); dominio, ORM y `IncidenciaOut`.
  - PUT por `id` (R36): `identificar` da 422 si el `id` no es del trabajador
    o del periodo, viene repetido, o una registrada cambia de obra o código;
    `reemplazar` conserva la fila por `id`, borra la no registrada que no
    viene y deja `quitada` la registrada (R38). Solapes sin las quitadas.
  - Evento con `id` y `quitada`; deshacer repone con su `id` (R47).
  - Registro: las quitadas no viajan; el preflight las lista en
    `incidencias_quitadas`; la incidencia lleva `hmores_ide_ini/_fin` y
    `dia_ini/_fin` si tiene traza; la traza guarda `ide` y día por rol y un
    `omitir` de una registrada solo cambia el motivo (R39).
- **transfer** (T27-T31, T34):
  - Contrato: los cuatro campos; `fec_antes` y `hmoide` en la acción.
  - `incidencias_del_mes(…, ides=())` trae `can`, `hmoide`, `con.est` y
    busca también por `h.ide`; `stmt_editar_fecha_incidencia`: `UPDATE
    hmores SET fec = ?` con la guarda de F-051 y `a.cod = ?` (sin `hora`,
    el texto de F-051 idéntico).
  - `reconciliar` (sustituye a `deduplicar`, obs. 6), puro: la nuestra por
    `ide` o `synckey` (del recurso y con nuestra `synckey`) con su `fec` →
    `ya_registrado`; con otra → `editar`, salvo cambiada a mano (R42), parte
    no En registro (R43) o día ocupado con las ediciones aplicadas, en
    punto fijo (R44). Sin la nuestra, R27.
  - Preflight y lote: `reconciliar` **antes** del paso 5 (obs. 7: `editar`
    no pide parte; en pruebas el parte se lee una vez) y los `ide` de la
    traza en la misma lectura y ronda; fuera la línea larga (obs. 3).
  - `ejecutar` (R45, R46): las `editar` en la relectura única de
    `_planear_ediciones`; `sigue_editable` y `no_editar_el_par` (el par o
    ninguna); `UPDATE` juntos en el lote con log de lo releído; la
    relectura de lo escrito las pide por `ide` y sin la `fec` nueva van a
    `omitir`. Ningún `INSERT`, `DELETE` ni parte nuevo por ellas.
  - Script: `editar`, `fec_antes` y `hmores.ide` en preflight y ejecutar.
- **front** (T32): `id` en `cargarEdicion` y en el PUT; tras el PUT las
  nuevas toman el `id` de la respuesta (`idsDeLaRespuesta`, R37); la quitada
  sale tachada, «quitada · sigue en Sigrid», y fuera del editor; el modal
  dice «se cambia del d al d» y lista las quitadas (`seccionQuitadas`).
  Solo formato e identidad: ninguna regla.
- **docs** (T35): `#regla-incidencia` con «Cambiar los días» y «Quitar»;
  `INTEGRACION.md` §1 y §5. **T36**: fuera los 16 avisos de ruff de
  `test_f030_incidencias.py` de la api (obs. 4); el repo, en 277 como `dev`.

## 3. Decisiones y desviaciones (justificadas)

- **Nombres del contrato**: `hmores_ide_ini`, `hmores_ide_fin`, `dia_ini`,
  `dia_fin` (design §6 no los fijaba); solo viajan si hay alguno.
- **Los `xfail` estrictos del punta a punta se quitaron antes de T33**: el
  de la api en T26 y el del transfer en T31, al pasar cada mitad a XPASS
  (con `strict` la suite se habría puesto roja). T33 solo verificó las dos
  en verde y el contrato sin tocar desde T22.
- **R42 sin día en la traza** (registrada antes del anexo): la nuestra
  cuenta como cambiada si está fuera del mes pedido (R48: no cambia de mes).
- **R43**: «sigue del d al h» con los días que tiene hoy el par en Sigrid
  (`?` si falta una línea).
- **`sigue_editable` y `no_editar_el_par`**, puras en `reglas_incidencias.py`.
- **`deduplicar` desaparece**: sus tests propios de R27 siguen iguales, con
  un adaptador local `deduplicar → reconciliar(…, [], …, est=1)` en
  `test_f030_reglas_incidencias.py`.
- **Front**: `idsDeLaRespuesta` solo si la fila trae `incidencias` y
  `seccionQuitadas` solo si hay quitadas, como `seccionIncidencias` (los
  arneses del guardado de R15 y del modal de F-049/F-050 no las cargan).
- **T34**: `verificar` ya imprimía `hmores.ide` y `fec`; ahora con test.
  La traza sigue en `traza_incidencias.py` (lo exige `test_f003_r17`).

## 4. Tests que cambiaron (lista cerrada de design §13.7)

Ajenos, solo dobles: `services/dedicacion-transfer/tests/conftest.py`
(`stmt_editar_fecha_incidencia` y su guarda en `EdicionesFalsas`).
`test_f051_sql_cero.py` intacto (`git diff --quiet`). Propios de F-030:

| Fichero | Cambio |
|---|---|
| api `test_f030_incidencias.py` | esquema con las columnas nuevas; `r17_guardar_*` y `repo_reemplazar_*` por `id`; snapshot `r20_*` con `id`/`quitada`; T36 |
| api `test_f030_registro.py` | doble `_inc` con la traza; `r31_traza_*` reescritos (dos UPDATE, el `omitir` no toca el `ide`) |
| transfer `test_f030_pipeline_incidencias.py` | `ClienteInc` con `ides`; `r33_cliente_*` (SQL nueva, dedupe); `r30_ejecutar_no_reescribe_*` → `editar` |
| transfer `test_f030_reglas_incidencias.py` | adaptador `deduplicar`; `r30_deduplicar_la_nuestra_*` reescrito (R40, R41) |
| front `test_f030_tabla_incidencias.py` | `r15_cargar_edicion_*` con `id` (design §13.3) |

## 5. Fase RED del anexo (trazas reales)

Desde cada servicio, `.venv/Scripts/python -m pytest <fichero> [-k …] -q
-p no:cacheprovider`, con el test escrito y sin el código; líneas `E` y
resumen (completas en `red/T2*.txt`/`red/T3*.txt` del scratchpad).

```
T22 tests/test_f030_r30_punta_a_punta.py en api y en transfer (antes de la marca xfail)
E   At index 0 diff: {'obra': …, 'incidencias': [{'id': 8, 'recurso_ide': 200, …   2 failed in 1.21s
E   At index 0 diff: ['ini', 'ya_registrado', 20260706, None] != ['ini', 'editar', 20260706, 20260705]   2 failed in 0.80s
T23 api test_f030_r30_identidad.py -k esquema
E   Right contains 3 more items, first extra item: 'ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS quitada …'
E   TypeError: 'quitada' is an invalid keyword argument for IncidenciaORM   5 failed in 3.30s
T24 api -k "r36 or r38"
E   assert (2, 6, 9, False) == (7, 6, 9, False)
E   Failed: DID NOT RAISE IncidenciaInvalida   (x7)
16 failed, 1 passed, 5 deselected in 3.06s
T25 api -k r47
E   At index 0 diff: (7, 5, 9, False, 9001, 9002) != (7, 5, 9, True, 9001, 9002)   1 failed, 4 passed, 22 deselected
T26 api -k "r39 or r38_registro"
E   Right contains 4 more items: {'dia_fin': 9, 'dia_ini': 5, 'hmores_ide_fin': 9002, 'hmores_ide_ini': 9001}
E   KeyError: 'incidencias_quitadas'   E   KeyError: 'sigrid_dia_ini'   10 failed, 27 deselected
T27 transfer test_f030_r30_editar.py -k contrato
E   AttributeError: 'IncidenciaEntrada' object has no attribute 'hmores_ide_ini'
E   TypeError: AccionIncidencia.__init__() got an unexpected keyword argument 'fec_antes'   3 failed, 1 passed
T28 transfer -k sql
E   TypeError: SigridWriteClient.incidencias_del_mes() got an unexpected keyword argument 'ides'
E   AttributeError: 'SigridWriteClient' object has no attribute 'stmt_editar_fecha_incidencia'   6 failed, 4 deselected
T29 transfer -k "r40 or r41 or r42 or r43 or r44 or r27"
E   ImportError: cannot import name 'reconciliar' from 'application.services.reglas_incidencias'
E   ImportError: cannot import name 'MOTIVO_INC_CERRADO' from …   15 failed, 6 passed, 4 deselected
T30 transfer -k "preflight or lote or r33"
E   At index 0 diff: ('ini', 'ya_registrado', 20260706, None, 9001, …) != ('ini', 'editar', 20260706, 20260705, 9001, …)
E   assert [[]] == [[9001, 9002]]              (la lectura no pedía los `ide`)
E   assert not [351]                           (obs. 3)
8 failed, 26 deselected in 1.44s
T31 transfer -k "ejecutar or r45 or r46"
E   AssertionError: assert [] == ['editar_fec', 'editar_fec']
E   AssertionError: assert ['insert'] == ['insert', 'editar_fec']   14 failed, 2 passed, 33 deselected
T32 front test_f030_r30_front.py
E   assert [[None, 5], [...], [None, 25]] == [[7, 5], [9, 25]]
E   AssertionError: no existe la función idsDeLaRespuesta en app.js   9 failed in 0.79s
T34 transfer test_f030_pipeline_incidencias.py -k script
E   assert 'fec_antes=20260705 hmores.ide=70001' in '… [editar       ] inc=990101 ini CIV …'   1 failed, 10 passed
T35 transfer test_f030_r30_editar.py -k r34
E   'no se\n      reescribe aunque cambien sus días' is contained here
E   assert 'hmores_ide_ini' in '<!-- docs/INTEGRACION.md --> …'   2 failed, 49 deselected
```

T33 y T36 no tienen RED (quitan marcas y avisos de ruff). Los tests de los
7 supervivientes de la 4.ª campaña (§6) se probaron con cada mutante
aplicado a mano: «1 failed» los siete.

## 6. `bash harness/init.sh` y mutación (T37)

`init.sh` del cierre (código de `b614b91`), cachés `suite_*.ok` borradas: **ENTORNO
LISTO**, ningún `[KO]`; ruff 277 avisos (`[AVISO]`, los mismos que `dev`).
PUERTA COBERTURA 99,9 % (831/832; la que falta es el `continue` de
`lecturas_lote.py:362`, obra de pruebas no encontrada en el lote, de T15).
PUERTA TAMAÑO: requirements 150/150, design 243/250, impl 216/220.

Mutación en serie (`--workers 1`), completa, sobre todo el diff de F-030
(23 ficheros, 1.997 líneas): **4.ª campaña** (`42c1cc8`) 405 mutantes, 7
supervivientes + 1 timeout; los 7 eran huecos reales y se cerraron con
tests (`b614b91`). **5.ª campaña** (`b614b91`): 405 mutantes, 404 muertos,
**0 supervivientes**, 1 timeout (detectado: el punto fijo de R44 no
termina). Ninguno se dio por equivalente; análisis uno a uno en
`progress/mutacion_F-030.md` § «Historial».

## 7. Verificación MANUAL pendiente (T20, del líder)

Requiere autorización expresa del humano para esta acción. La primera
mitad (5-9) ya la hizo el líder (`progress/manual_F-030.md`); si se limpió,
repetirla antes con `RECURSO:CIV:5:9`. Segunda mitad (R49): transfer
**local** con `OBRA_PRUEBAS_FORZAR=true`, desde `services/dedicacion-transfer`,
el mismo `RECURSO` (con `CIV` y `CIZ` en `reshor`):

```
python prueba_escritura_porcentajes.py preflight --ano 2026 --mes 10 --incidencia RECURSO:CIV:6:12
python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:6:12
python prueba_escritura_porcentajes.py verificar --incidencia RECURSO:CIV:6:12
python prueba_escritura_porcentajes.py ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:6:12
python prueba_escritura_porcentajes.py limpiar --confirmar
```

Esperado: el preflight da las dos `editar` con `fec_antes` 5 y 9; tras
`ejecutar`, `verificar` enseña **los mismos dos `hmores.ide`** con `fec` 6 y
12 y ninguna línea nueva; el último `ejecutar`, `ya_registrado` sin escribir
nada; `limpiar` las borra.

## 8. Fuera del alcance y pendiente

- **`azure-apps/dedicacion.md`** (R34), del líder al desplegar: leemos
  `auxhor` (`CI*`); escribimos `CI*`/`CIZ` con `can = 0` y `synckey
  porcentajes:inc:`, tras una lectura de las `CI*` del mes (y por `ide`);
  **editamos la `fec`** del par de una registrada que cambia de días
  (`UPDATE` con guarda, nunca `DELETE`); las rutas y campos nuevos
  (`id`, `quitada`, `incidencias_quitadas`). Avisar a `partes` de que su
  `partes.md` debería contar la incidencia también.
- Por D10 quedan fuera el % por días con el calendario (F-059) y la bandeja
  de `partes` (F-060). Retirar de Sigrid una `quitada` es a mano (D11).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 3.126 passed, 1 skipped, 0 failed: raíz 418 (+1 skipped), api 1.125, front 359 (los de node `passed`), transfer 1.224 |
| Cobertura de líneas cambiadas | 99,9 % (831/832), PUERTA COBERTURA de `init.sh` |
| Mutación | 5.ª campaña: 405 generados, 404 muertos, **0 supervivientes**, 1 timeout (detectado); `--workers 1`; 1.626,6 s (HEAD `b614b91`). 4.ª: 7 supervivientes, cerrados con tests |
| Tiempo de la suite | raíz 32,48 s, api 26,78 s, front 24,65 s, transfer 11,94 s (95,85 s en total; `init.sh` del cierre) |
