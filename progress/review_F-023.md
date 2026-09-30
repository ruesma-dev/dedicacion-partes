Revisión completa (pasada 1) del trabajo de F-023: `git diff 792870f..HEAD` (base = merge de `dev` con F-022; HEAD `9c7810c`)

# F-023 · Review — Sync de maestros: todas las empresas y activo según el estado del recurso

**Veredicto: APPROVED** (el `done` sigue bloqueado por T9, T10 y T11, MANUAL del humano).

**Rama:** `feature/F-023-sync-empresa-y-estado-recurso`, árbol principal, limpio antes y después de la review.
**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de las
líneas cambiadas, mutación con cero supervivientes, RM1-RM6 y verificaciones MANUAL con su comando.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh`: **ENTORNO LISTO**. 355 passed, 1 skipped; PUERTA COBERTURA `[OK]` 100,0 % (67/67);
  PUERTA TAMAÑO `[OK]`; ningún `.env` versionado; ruff 193 avisos.
- Ruff comparado fichero a fichero (`792870f` frente a HEAD) en los 8 `.py` tocados: **0 avisos nuevos**.
- `pytest tests/test_f023_sync_empresa.py`: **53 passed** (1,6 s).
- Mutación, **recálculo puro**: `alcance_de_feature("F-023")` = `6fb5147..rama`, 7 ficheros, **182 líneas**;
  `generar_mutantes` = **33 mutantes**. Coinciden fichero a fichero con `progress/mutacion_F-023.md`.
- Mutación, **campaña reejecutada** (el informe declara 51,0 s, menos de 60 s):
  `python -m harness.mutacion --feature F-023 --max-mutantes 0 --salida <scratchpad>` sobre HEAD `9c7810c`
  da **33 evaluados, 33 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 53,4 s**, con la línea base
  ejecutada (4,4-4,5 s por worker) y sin cabecera «CAMPAÑA NO VÁLIDA». Los totales coinciden. `git status`
  queda limpio.

## Checkpoints

**C1** [x] init.sh sale con 0 · [x] existen los ficheros base.
**C2** [x] una sola `in_progress` (F-023) · [x] la rama es la de la feature · [x] `current.md` refleja la
sesión (F-023 en review) · [x] todas las `done` tienen su entrada en `history.md` (comprobado por script).
**C3** [x] Hexagonal: `domain/` sin imports nuevos; `filtros_maestros` es función pura en `application/`;
el ORM y el upsert viven en `infrastructure/db`; `deps.py` solo cablea. · [x] La primera línea de los
9 ficheros tocados es su ruta. · [x] Sin `print`, sin TODO, sin secretos y sin dependencias nuevas.
· [x] Las tres trampas: ni porcentajes, ni postventa, ni escrituras a Sigrid (la SQL es de lectura y va
por `sigrid-api`).
**C3 bis** N/A: la feature no toca `docs/referencia/`.
**C4** [x] Hay tests de R1 a R18 y pasan (tabla abajo). · [x] Sin red ni BBDD: la sesión, `SigridGateway`
y el UoW son dobles; `SigridApiClient` va parcheado con monkeypatch; `construir_contenedor(..., None)`
no abre ningún engine; `cargar_config` solo lee el yaml. · [x] T9, T10 y T11 constan en `current.md` con su
comando (Q1 de design §4, `GET …/sync/preview`, `SELECT empresa, COUNT(*)…`).
**C4 bis** [x] rigor `critico` declarado · [x] RED: traza real pegada (47 failed, 3 passed). Los 3 verdes son
de R10, que caracteriza el comportamiento de hoy, y el cambio lo demuestra R11 en rojo. · [x] Cobertura:
100 %. · [x] Mutación con totales verificados de forma independiente. · [x] Campaña reejecutada (arriba).
· [x] Coste por mutante: 51,0 × 4 ÷ 33 = 6,2 s, más de 1 s. · [x] Sin «CAMPAÑA NO VÁLIDA» y 0 sin
veredicto. · [x] **RM1**: se midió sobre `fd2831c`; de ahí a HEAD solo cambian `progress/` y `tasks.md`,
así que el alcance es el mismo (la reejecución sobre HEAD da lo mismo). · [x] **RM2**: media × W =
1,5 × 4 = 6,2 s, coherente con la línea base de 4,6 s. · **RM3**: revisé los 33; ninguno es equivalente,
todos cambian algo observable (p. ej. `or ""` → `and ""` vacía el estado que se compara). · RM5 N/A: no
hay equivalentes declarados. · [x] **RM6**: no se quitó ninguna guarda. Los cuatro supervivientes de la
primera campaña se mataron **añadiendo** tests (`7e1bf24`). · Campaña manual N/A: la automática dio 33.
· [x] Cero supervivientes. · [x] La sección «Evidencias» trae los cuatro números y los workers (4).
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] T1-T8 y T12 `[x]`, cada una con su commit `F-023 Tn:`, más dos commits de ajuste con motivo.
T9-T11 quedan `[ ]` **justificado**: son MANUAL del humano y bloquean el `done`, no esta review.
· [x] Sin artefactos sin trackear. · [x] `features.json` en `in_progress`.

## Cobertura: requisito → test (`services/dedicacion-api/tests/test_f023_sync_empresa.py`)

| R | Tests | R | Tests |
|---|---|---|---|
| R1 | `r1_columna_empresa_integer_nulable_sin_default` ×2, `r1_empresa_solo_en_trabajador_y_obra` | R10 | `r10_*` ×3 |
| R2 | `r2_alters_de_una_base_sin_empresa` (las dos cadenas exactas) | R11 | `r11_*` ×3 (incluida empresa nula) |
| R3 | `r3_obras_devuelven_empresa_de_su_ficha` | R12 | `r12_*` ×3 |
| R4 | `r4_empleados_devuelven_los_cinco_alias` | R13 | `r13_*` ×2 |
| R5 | `r5_empleados_sin_filtro_de_emphis`, `r5_config_criterio_…_vacio_por_d1` | R14 | `r14_*` ×3 (estado, empresa y fecha) |
| R6 | `r6_pipeline_…` ×2, `r6_preview_…` ×2, `r6_las_demas_columnas…` | R15 | `r15_baja_laboral_no_excluye_pero_se_cuenta` |
| R7 | `r7_mismo_codigo_en_dos_empresas_son_dos_obras` | R16 | `r16_*` ×3 |
| R8 | `r8_*` ×10 | R17 | `r17_*` ×2 |
| R9 | `r9_*` ×3 | R18 | `r18_*` ×6 (contenedor real con el yaml parcheado) |

R19: MANUAL (T10).

## Puntos de la petición del líder

- **Columnas `empresa` en el ORM, sin ALTER a mano**: [x]. `Integer`, nulable, sin default, solo en
  `trabajador` y `obra`. El `ALTER` sale de `alters_faltantes` (R2). `esquema.py` y `main.py` no se tocan.
- **El dedupe por persona no mezcla empresas**: [x]. `_clave_persona` = `"{empresa}|dni:…"`; con empresa
  nula la clave es `None|…`.
- **El descarte fila a fila va antes de los dedupes**: [x]. El paso 0 construye `validas` y el dedupe por
  `ide` recorre solo esas.
- **Preview y sync usan el mismo criterio y el mismo objeto**: [x]. En `deps.py` se crea una sola instancia
  y se pasa a los dos; las columnas requeridas son constantes compartidas.
- **Config vacía por D1**: [x]. `estados_recurso_excluidos: []` y `excluir_recurso_con_fecha_baja: false`.
  No es defecto.
- **Alcance de F-024, F-025 y F-026 sin tocar**: [x]. Front, transfer, `depurar_obras`, `schemas.py` y
  `routes.py` intactos; la SQL sigue partiendo de `dbo.emp`.
- **Tests sin red ni BBDD y ningún `.env`**: [x].

## Desviaciones del implementer, validadas

1. **Filtros `-k` de `tasks.md`.** `-k` casa por subcadena, así que se usó `-k "r1_ or r2_"`. Es correcto y
   no cambia lo que se verifica. Para specs futuras: mejor `-k "r1_"`.
2. **`_entero` duplicado** en `repositories.py` y `filtros_maestros.py`. Aceptable: `application` no puede
   importar de `infrastructure`, son una línea cada uno y es el mismo servicio. Si se unifica, su sitio es
   `domain/normalizacion.py`.
3. **Tests extra, `CRITERIO_VACIO` como singleton y `COLUMNAS_*` compartidas**: mejoran lo que pide el
   diseño sin cambiar el comportamiento.

## Observaciones (no bloquean; el líder debe recogerlas, no dejarlas en «anotado»)

1. **Hallazgo del explorador (el tipo 33 no tiene estados en `conest`; la baja es `con.fecbaj`).**
   Ningún requisito queda sin sentido: R13 es justo el criterio real, y R19 sigue valiendo porque los
   descartes por fecha salen dentro de `excluidos_por_estado_recurso` bajo `"(fecha de baja del recurso)"`.
   Pero R12 y el `LEFT JOIN dbo.conest AS rest` del recurso (`config.yaml`) quedan **inertes en la práctica**:
   `estado_recurso` siempre será el `CAST(rcon.est)` numérico. Es código probado y sin riesgo mientras la
   lista siga vacía. El peligro está en rellenarla con un número: la comparación es por **subcadena**, así
   que `"1"` casaría también `"10"` y `"21"`. Además, el comentario de `config.yaml` («Literales de
   conest.res del recurso») invita a meter `BAJA`/`2`, que es el estado del **tipo 43 (empleado)**, la trampa
   que señala el explorador. **Al cerrar T9**, corregir ese comentario (decir que para recursos no hay
   literales y que el criterio es la fecha de baja) o simplificar R12 en una feature aparte. Lo decide el
   humano.
2. **T11 tal como está escrita va a fallar.** Pide `SELECT empresa, COUNT(*) FROM obra GROUP BY empresa`
   «sin NULL tras el sync». Pero el upsert solo escribe `empresa` en las filas **recibidas**. Las
   desactivadas (obras terminadas que filtra `estados_excluidos`, trabajadores sin código M* o ya de baja)
   se quedan con `empresa` NULL para siempre. Hay que cambiar la comprobación a `… WHERE activa` / `WHERE
   activo`. Y avisar en F-024: `listar_para_periodo` sigue mostrando desactivados que tienen líneas en el
   periodo, y esos llegarán con empresa NULL al filtro de empresa.
3. **Orden respecto a T9.** Con el criterio vacío y sin el filtro de `emphis` (R5), el sync de esta rama
   **mete más gente inactiva que `dev` hoy**: según el explorador, 535 personas con ficha que están de
   baja como recurso. Por D4 no se despliega sin F-024, pero conviene que `excluir_recurso_con_fecha_baja`
   quede fijado (T9) **antes del merge a `dev`**, no solo antes del despliegue.

## Cambios requeridos

Ninguno.

## Propuesta de automejora (para el humano, no aplicada)

- `CHECKPOINTS.md` C4: añadir que el reviewer compruebe que el **resultado esperado** de cada verificación
  MANUAL es alcanzable con el código revisado, no solo que el comando está en `current.md`. La observación 2
  habría devuelto a T11 un «falla» sin que hubiera defecto en el código.
