Revisión incremental desde ef38fa8 (pasada 2), HEAD `a14025e`. La pasada 1 (completa, sobre `9c7810c`) va resumida primero.

# F-023 · Review — Sync de maestros: todas las empresas y activo según el estado del recurso

**Veredicto vigente: CHANGES_REQUESTED** (pasada 2). Solo por rastro documental: config, tests y
mutación están bien. **Nivel de rigor:** `critico`, declarado en `harness/features.json` (fase RED,
cobertura ≥ 80 %, mutación con cero supervivientes, RM1-RM6, MANUAL con su comando).

## Pasada 1 · Revisión completa `792870f..9c7810c` — APPROVED (resumen)

- `init.sh` verde (355 passed, 1 skipped; cobertura 100 % 67/67); ruff sin avisos nuevos en los 8 `.py`.
- Mutación: recálculo puro (182 líneas, 33 mutantes) y **campaña reejecutada** (51,0 s < 60 s): 33/33
  muertos, 0 sin veredicto; RM1 y RM2 coherentes; RM3 revisados los 33, ninguno equivalente; RM6 los
  supervivientes de la primera campaña se mataron **añadiendo** tests (`7e1bf24`).
- C1-C5 `[x]`; C3 bis y C4 ter N/A (no toca `docs/referencia/`; no hay `rutas_sensibles.json`); T9-T11
  `[ ]` justificado (MANUAL del humano: bloquean el `done`, no la review).
- Trazabilidad R1-R18 con tests `test_f023_rN_*` en `services/dedicacion-api/tests/test_f023_sync_empresa.py`;
  R19 MANUAL (T10). Desviaciones aceptadas: filtros `-k` por subcadena, `_entero` duplicado entre capas
  (su sitio, si se unifica, es `domain/normalizacion.py`), tests extra y `CRITERIO_VACIO` singleton.
- Observaciones: (1) R12 y el JOIN a `conest` del recurso quedan inertes y la comparación es por
  subcadena; corregir el comentario de `config.yaml` al cerrar T9. (2) T11 debe filtrar `WHERE activa` /
  `WHERE activo`. (3) T9 antes del merge a `dev`. Automejora propuesta: C4 debe comprobar que el resultado
  esperado de una MANUAL es alcanzable.

## Pasada 2 · Revisión incremental desde `ef38fa8` (HEAD `a14025e`)

Delta: `9b9c1d9` (F-023 T9) y `a14025e` (rastro). Ficheros: `config/config.yaml`,
`tests/test_f023_sync_empresa.py`, `tasks.md`, `progress/{current,impl_F-023,mutacion_F-023}.md`.

### Verificación ejecutada por el reviewer

- `bash harness/init.sh`, tal cual: **ENTORNO LISTO**. 355 passed, 1 skipped; COBERTURA `[OK]` 100,0 %
  (67/67); TAMAÑO `[OK]`; ningún `.env`; `config.yaml` válido.
- **Ningún `.py` de producción en el delta** (`git diff --stat ef38fa8..HEAD`): solo YAML, tests, spec y
  rastro. `filtrar_produccion` deja el YAML fuera del alcance de mutación.
- **Fase RED reproducida** en un worktree desechable del scratchpad (HEAD con el `config.yaml` de
  `ef38fa8`): `2 failed` con las mismas trazas del informe (`assert False is True`;
  `([1, 2, 3], [1]) == ([1, 2], [1])`). Con el config de HEAD: fichero entero **53 passed**. Worktree
  eliminado; `git status` limpio.
- **Mutación, recálculo puro**: `alcance_de_feature("F-023")` = `6fb5147..rama`, 7 ficheros, 182 líneas;
  `generar_mutantes` = 33 (24+0+1+0+0+5+3). Coincide con `progress/mutacion_F-023.md`.
  **Campaña no reejecutada: 255,6 s según el informe** (> 60 s); vale recálculo + RM.

### Puntos de la petición del líder

- **Solo config, tests, rastro y spec**: [x]. `deps.py` sigue leyendo la clave con default `False`; el
  cambio de comportamiento sale solo del YAML.
- **RM1**: [x]. La campaña se midió sobre `ef38fa8` con el árbol en disco (`--workers 1`); de ahí a HEAD
  no cambia ningún fichero del alcance. Es la misma campaña que `impl_F-023.md` §T9 declara (33/33,
  255,6 s) y la de la pasada 1 sigue valiendo.
- **RM2**: [x]. 33 × 7,7 = 254 s ≈ 255,6 s; media × W = 7,7 × 1 frente a línea base 14,5 s: por debajo
  por el `-x`, sin salto de orden de magnitud. Coste por mutante 7,7 s > 1 s. Timeout 120 s (no comparable
  con la pasada 1: línea base distinta). Sin «CAMPAÑA NO VÁLIDA», 0 sin veredicto, 0 supervivientes.
- **Tests no aflojados**: [x]. `r5_config_inactivo_es_la_fecha_de_baja_del_recurso` fija las tres
  claves (interruptor `True`, lista `[]`, fecha de baja `True`): meter «BAJA» en la lista lo rompe.
  `r18_con_el_config_real_cae_el_recurso_con_fecha_de_baja` es **más fuerte** que el anterior (antes
  solo `netos_emp == [1, 2, 3]`): con el yaml real exige netos `([1, 2], [1])` iguales en sync y preview,
  `excluidos_por_estado_recurso == {"(fecha de baja del recurso)": 1}` (cae el 3), el 2 con estado
  «Baja» sin fecha se queda, y `excluidos_recurso_otra_empresa == 1` (cae el 4).
- **Comentario de `config.yaml` recoge la observación 1**: [x]. Dice que el criterio es `con.fecbaj > 0`
  (D1, fuente el data mart), que el tipo 33 no tiene estados en `conest`, que no se mete «BAJA» ni «2»
  (estado del tipo 43) y que la subcadena haría casar «1» con «10» y «21».
- **`current.md` con T10 y T11 y su comando exacto**: [x]. T11 ya con `WHERE activa` / `WHERE activo`.
- **`current.md` coherente con `features.json`**: [ ]. Ver cambios requeridos 1 y 2.

### Checkpoints (pasada 2; lo no tocado por el delta sigue como en la pasada 1)

**C1** [x] init.sh sale con 0 · [x] ficheros base.
**C2** [x] una sola `in_progress` · [x] rama de la feature · [ ] `current.md` **conserva restos
contradictorios** (cambio 1) · [x] `history.md` sin cambios que pedir.
**C3** [x] primera línea con ruta en los dos ficheros tocados · [x] sin prints, TODO ni secretos ·
[x] hexagonal intacta (sin código) · [x] las tres trampas: ni porcentajes, ni postventa, ni escrituras.
**C3 bis** N/A: el delta no toca `docs/referencia/`.
**C4** [x] R5, R13 y R18 con tests adaptados y en verde · [x] sin red ni BBDD (`SigridApiClient` parcheado,
yaml real solo leído) · [x] T10 y T11 en `current.md` con su comando.
**C4 bis** [x] rigor declarado · [x] RED con traza real, reproducida · [x] cobertura 100 % · [x] totales
recalculados · [x] campaña > 60 s: recálculo + RM, dicho arriba · [x] coste por mutante 7,7 s ·
[x] sin cabecera de no válida · [x] RM1 · [x] RM2 · RM3: los mutantes no cambian respecto a la pasada 1,
ninguno equivalente · RM5 N/A: no hay equivalentes declarados · [x] RM6: no se quitó ninguna guarda ·
campaña manual N/A: la automática dio 33 · [x] cero supervivientes · [x] «Evidencias T9» con tests,
cobertura, mutantes y workers (1).
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] T9 `[x]` con su commit `F-023 T9:` · T10 y T11 `[ ]` justificado (MANUAL del humano; bloquean
el `done`, no el merge) · [x] árbol limpio · [ ] la descripción de F-023 en `features.json` sigue dando
D1 por pendiente (cambio 2).

### Cobertura del delta: requisito → test

| R | Test |
|---|---|
| R5 | `test_f023_r5_config_inactivo_es_la_fecha_de_baja_del_recurso` (+ `r5_empleados_sin_filtro_de_emphis`) |
| R13 | `test_f023_r18_con_el_config_real_cae_el_recurso_con_fecha_de_baja` con el yaml real (+ `r13_*` ×2) |
| R9 | ídem: `excluidos_recurso_otra_empresa == 1` |
| R18 | ídem más los cinco `r18_*` con yaml parcheado |

## Cambios requeridos (pasada 2; todos de rastro, ninguno de código)

1. `progress/current.md` l. 29-34, viñeta «Explorador (D1)»: dice «Propuesta al humano para T9,
   **pendiente de su respuesta**» y «Mientras no responda, `config.yaml` sigue con el criterio vacío».
   Es falso desde `9b9c1d9`. Dejarla como «aceptada el 2026-10-01 (T9)» o quitarla. Y en «Lo que espera
   al humano», punto 3 (l. 82), quitar «la consulta Q1 de F-023 (design §4)»: D1 se cerró sin Q1. La lista D5
   (para T10) sí sigue pendiente.
2. `harness/features.json`, descripción de F-023: sigue diciendo «Pendiente antes de verificar (T9/T10):
   D1, valores de estado de recurso inactivo (consulta Q1)» y no lista D1 entre las decisiones. Añadir
   «D1 inactivo = fecha de baja del recurso (`con.fecbaj > 0`), 2026-10-01» y dejar solo D5 como
   pendiente. Regenerar `BACKLOG.md` con `bash harness/init.sh`.
3. `specs/F-023-sync-empresa-y-estado-recurso/requirements.md` l. 126-131 (D1: «Hasta decidirlo, la
   configuración entra vacía») y `design.md` l. 32 (`false`, D1): anotar que D1 está cerrada y con qué
   valor. El acceptance 2 de `features.json` pide el campo y los valores «documentados en la spec»; hoy
   solo los recoge la coletilla de T9 en `tasks.md`. Ojo: `requirements.md` está en 147/150 líneas;
   reescribir la viñeta D1 en su sitio, no añadir un bloque.

Con eso, la pasada 3 puede ser solo documental: no hace falta repetir la mutación ni la RED.

## Propuesta de automejora (para el humano, no aplicada)

- `leader.md`: al cerrar una decisión abierta (Dn), checklist de dónde vive: `features.json`
  (descripción), `requirements.md` (sección de decisiones), `current.md` (todas las viñetas que la citan)
  y la tarea. Aquí se actualizaron dos de cuatro sitios.
