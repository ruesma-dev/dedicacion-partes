Revisión incremental desde a14025e (pasada 3, solo documental), HEAD `910d95a`. Las pasadas 1 y 2 van resumidas primero.

# F-023 · Review — Sync de maestros: todas las empresas y activo según el estado del recurso

**Veredicto vigente: APPROVED** (pasada 3). **Nivel de rigor:** `critico`, declarado en
`harness/features.json` (fase RED, cobertura ≥ 80 %, mutación con cero supervivientes, RM1-RM6, MANUAL
con su comando). T10 y T11 siguen MANUAL pendientes: bloquean el `done`, no el merge a `dev`.

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
  `WHERE activo`. (3) T9 antes del merge a `dev`. Automejora: C4 debe comprobar que el resultado esperado
  de una MANUAL es alcanzable.

## Pasada 2 · Incremental desde `ef38fa8` (HEAD `a14025e`) — CHANGES_REQUESTED solo de rastro (resumen)

Delta: `9b9c1d9` (T9: `config.yaml` + `test_f023_sync_empresa.py`) y `a14025e` (rastro). **Código y tests
aprobados**; lo verificado:

- `init.sh` tal cual: ENTORNO LISTO, 355 passed, 1 skipped; COBERTURA `[OK]` 100,0 % (67/67).
- Ningún `.py` de producción en el delta; el YAML queda fuera del alcance de mutación.
- **RED reproducida** en worktree desechable (HEAD con el `config.yaml` de `ef38fa8`): `2 failed` con las
  trazas del informe; con el config de HEAD, 53 passed. Worktree eliminado, árbol limpio.
- Mutación, recálculo puro: `6fb5147..rama`, 7 ficheros, 182 líneas, **33 mutantes** (24+0+1+0+0+5+3),
  coincide con `progress/mutacion_F-023.md`. **Campaña no reejecutada: 255,6 s según el informe** (> 60 s).
  RM1 [x] (medida sobre `ef38fa8`, sin cambios de alcance hasta HEAD); RM2 [x] (33 × 7,7 ≈ 255,6 s;
  media 7,7 s frente a línea base 14,5 s, por el `-x`); RM3 sin equivalentes; RM5 N/A; RM6 [x] (ninguna
  guarda quitada); 0 supervivientes, 0 sin veredicto.
- Tests no aflojados: `r5_config_inactivo_es_la_fecha_de_baja_del_recurso` fija las tres claves;
  `r18_con_el_config_real_cae_el_recurso_con_fecha_de_baja` es más fuerte que el anterior (netos
  `([1, 2], [1])`, `{"(fecha de baja del recurso)": 1}`, `excluidos_recurso_otra_empresa == 1`).
- Comentario de `config.yaml` recoge la observación 1 de la pasada 1.
- Cobertura del delta: R5 → `r5_config_*`; R9, R13, R18 → `r18_con_el_config_real_*` (+ `r13_*`, `r18_*`).

Cambios pedidos (todos de rastro): (1) `current.md` daba la D1 por pendiente y citaba Q1 entre lo que
espera al humano; (2) descripción de F-023 en `features.json` con la D1 pendiente; (3) `requirements.md`
(D1) y `design.md` l. 32 sin decir que la D1 está cerrada ni con qué valor.

## Pasada 3 · Incremental desde `a14025e` (HEAD `910d95a`) — solo documental

Delta (`git diff --stat a14025e..HEAD`): `BACKLOG.md`, `harness/features.json`, `progress/current.md`,
`progress/review_F-023.md` (el informe de la pasada 2), `design.md` y `requirements.md`. **Ningún
fichero de código ni de tests** (`git diff --name-only` sin `.py` ni `.yaml`).

### Verificación ejecutada por el reviewer

- `bash harness/init.sh`, tal cual: **ENTORNO LISTO**. 355 passed, 1 skipped; COBERTURA `[OK]` 100,0 %
  (67/67, nivel critico); TAMAÑO `[OK]` (requirements 146/150, design 203/250, impl 218/220);
  `BACKLOG.md al día`; `features.json` válido; ningún `.env`; una sola `in_progress` (F-023).
- `grep -rn` de «D1», «Q1», «hasta decidir» y «pendiente» en `specs/F-023-*/`, `progress/current.md` y la
  entrada F-023 de `features.json`: resultados abajo.
- `git status` limpio al empezar y al terminar (solo se escribe este informe).

### Los tres cambios pedidos

1. **`current.md`** [x]. La viñeta «Explorador (D1)» dice ahora «Aceptado por el humano el 2026-10-01 y
   aplicado en T9 (`9b9c1d9`)»; desaparece «pendiente de su respuesta» y «Mientras no responda». En «Lo
   que espera al humano», punto 3, ya no aparece la Q1: queda solo la lista D5 «para T10 de F-023». T9
   figura «CUMPLIDA (2026-10-01)». Los dos «_pendiente_» que quedan son los resultados de T10 y T11, que
   sí lo están.
2. **`features.json`** [x]. La descripción lista «D1 inactivo = fecha de baja del recurso (con.fecbaj > 0),
   decidida el 2026-10-01 con progress/explore_estado_recurso.md, sin lanzar Q1» entre las decisiones y
   deja como pendiente solo «(T10): D5». `BACKLOG.md` regenerado con el mismo texto (init: «al día»).
3. **Spec** [x]. `requirements.md` l. 126-130: «D1 · CERRADA el 2026-10-01 (humano, sin Q1)», con los dos
   valores (`excluir_recurso_con_fecha_baja: true`, lista vacía), el motivo y la referencia al
   explorador; reescrita en su sitio (146/150). `design.md` l. 32: «`false` al implementar; `true` desde
   que D1 se cerró el 2026-10-01, T9». El acceptance 2 («campo y valores documentados en la spec») queda
   cubierto.

### Menciones residuales de D1 / Q1 (ninguna la da por abierta)

- `requirements.md` l. 28-31 (contexto): «sus valores quedan en D1, con la consulta que la cierra (design
  §4)». Remite a D1, que ya dice cerrada y con qué valor.
- `requirements.md` l. 110 (R19): «con los valores de D1 en `config.yaml`». Correcto: ya están.
- `design.md` l. 118 (§4, catálogo de consultas): «Q1 — cierra D1», bajo «las lanza el humano». Describe
  para qué se diseñó la consulta; no afirma que D1 siga abierta. Ver observación 1.
- `design.md` l. 188 (§7): «los valores de estado no están en el diccionario (D1)». Sigue siendo cierto.
- `tasks.md` l. 20: T9 `[x]` con «Cerrada: … sin lanzar Q1».

### Checkpoints (pasada 3; lo no tocado sigue como en las pasadas 1 y 2)

**C1** [x] init.sh sale con 0 · [x] ficheros base.
**C2** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md` coherente con
`features.json` (cambios 1 y 2) · [x] `history.md` sin cambios que pedir.
**C3** [x] sin código en el delta; primera línea con ruta en los `.md` tocados · [x] sin secretos.
**C3 bis** N/A: el delta no toca `docs/referencia/`.
**C4** [x] sin tests en el delta; los de la pasada 2 siguen en verde · [x] T10 y T11 con su comando.
**C4 bis** [x] RM1: el delta no toca ningún fichero del alcance de mutación, así que la campaña de la
pasada 2 (33/33 sobre `ef38fa8`) sigue valiendo · resto sin cambios respecto a la pasada 2.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] T1-T9 y T12 `[x]` · T10 y T11 `[ ]` justificado (MANUAL del humano; bloquean el `done`, no el
merge) · [x] árbol limpio · [x] `features.json` con la D1 cerrada.

## Observaciones (no bloqueantes; el líder las recoge o las descarta por escrito)

1. `design.md` §4, «**Q1 — cierra D1.**» (l. 118): añadir «(no lanzada: D1 se cerró el 2026-10-01 sin
   ella)», y en `requirements.md` l. 31 cambiar «con la consulta que la cierra» por «cerrada el
   2026-10-01». Sin eso, quien lea el design suelto puede lanzar Q1 sin necesidad (inofensivo: es solo
   lectura). No bloquea: el sitio de autoridad (D1 en `requirements.md`, T9 en `tasks.md`) está bien.
2. `current.md` l. 3 sigue diciendo «review APROBADA (pasada 1)»: al recoger esta, poner «pasada 3».

## Propuesta de automejora (para el humano, no aplicada)

- `leader.md`: al cerrar una decisión abierta (Dn), checklist de dónde vive: `features.json`
  (descripción), `requirements.md` (sección de decisiones **y las menciones de contexto**), `design.md`
  (tablas y consultas que la citan), `current.md` (todas las viñetas) y la tarea. Un `grep -rn "Dn"`
  sobre la spec, `current.md` y `features.json` antes de lanzar la review lo cierra de una vez.
