<!-- progress/review_F-045.md -->
Revisión incremental desde e6ab33d (pasada 4) · la 1 fue completa (`dev...6959c91`); la 2, la 3 y esta, incrementales

# F-045 · Review

**Veredicto vigente: APPROVED** (pasada 4, abajo). Tres cosas de rastro que el
líder hace AL CERRAR, sin nueva review (ver «Al cerrar»).

## Pasadas 1 a 3 (resumidas por el tope)

- **1 · CHANGES_REQUESTED** (MANUAL contra 2026/09) · **2 · APPROVED** ·
  **3 · CHANGES_REQUESTED** (D10 «abierta» en `design.md`; recuento de octubre).
  Detalle de HEAD idéntica celda a celda a la de `dev`, listas cerradas sin
  aserciones relajadas y campañas 14/14 verificadas. Lo de la 3, corregido en
  `e6ab33d`. Su automejora (grep de Dn abiertas en C5), pendiente del humano.

## Pasada 4 · Revisión incremental desde e6ab33d

Delta: `628b9bb`..`fea1517` (ampliación D11/D12: spec `7f99e7b`, `a3578c0`;
T12-T15 `b7e3616`..`33b9011`; `current.md` `3835c0c`; M2 cumplida `fea1517`,
que entró mientras revisaba: solo cambia «Resultado» de M2 en `current.md`).
**Nivel de rigor: `estandar`** (declarado en `features.json`): fase RED,
cobertura ≥ 80 %, mutación muestreada con supervivientes analizados.

### Lo comprobado

- `bash harness/init.sh` (tal cual, solo): **ENTORNO LISTO**, raíz 418 passed /
  1 skipped, api/front/transfer en verde, cobertura 100 % (38/38), tamaño OK.
- **Código = design §3.3**, punto por punto: solo `exporter.py` (9.º elemento
  de cabecera, ancho 50, `_OBSERVACIONES`, `_AJUSTE`, bucle hasta
  `len(_CABECERA_DETALLE)`, ajuste en I). Ningún valor en I; `_COMBINADAS` y la
  cursiva `(3, 4, 5)` sin tocar. `contenido.py` y `test_f039_…` sin diff. Ruff
  de los tres ficheros tocados, limpio. Docs R19: solo `ARCHITECTURE.md:79` y
  `README.md:41`, con «Observaciones vacía».
- **R20, R21 y D12 = A contra los tests.** r20: I2 «Observaciones» con relleno
  y fuente de cabecera, ancho 50, autofiltro `A2:I<max_row>` y `A2:I2` vacío,
  `max_column == 9`, `fitToWidth == 1`, en las tres hojas. r21: por XML, cada
  fila de 3 a `max_row` de las tres hojas (los grupos de `_GRUPOS` y
  `_GRUPOS_DETALLE` son contiguos y cubren las agregadas Obras 5/8/11,
  Postventa 4/5/11 y las «SIN CARGA» Obras 9, Postventa 8, Detalle 10) tiene I
  sin valor, banda del grupo, `medium`/`thin` abajo, fino a los lados y arriba;
  por openpyxl, ajuste, arriba, sin cursiva ni fórmula; ningún rango `I…`. D12
  queda fijada: con la B, r21 falla en las agregadas y la «SIN CARGA».
- **Lista cerrada de design §7.2**: el diff de tests es exactamente
  `_CABECERA` + f045 r3, r4_r10 ×2, r17 + f040 r3, r4, r6, r9, y los dos tests
  nuevos de §7.3. Todo AÑADE (I en rangos, el 50, «Observaciones», `None` al
  final de la fila «SIN CARGA», que ahora se compara entera): ninguna
  aserción quitada ni relajada. Docstrings de los dos módulos actualizados.
- **Ninguna Dn abierta**: `grep -i abierta` en `specs/F-045-…/`, vacío.
- **RED de T12** pegado en impl §9.2: 11 failed contra el exportador de
  `a3578c0` (r20 por I2 vacía, r21 por I3 ausente en el XML); tras T13, 715.
- **M2 seguida en solo lectura** (`build_app` en proceso desde la copia
  principal con `-B`, sin `main.py` ni DDL; xlsx en mi scratchpad):
  `GET …/2026/10/export.xlsx?empresa=1` → 200; Obras/Postventa/Detalle con I2
  «Observaciones», ancho 50, autofiltro `A2:I190`/`A2:I188`/`A2:I190`,
  `max_column` 9, 0 valores en I, ajuste en todas, bandas blanca/azul, I sin
  combinar, horizontal a 1 página de ancho. Comando bueno; cumplida por el
  humano (`fea1517`). El `.pyc` de la copia principal es el del fuente actual
  (comparado con un `compile` limpio): reiniciar la api carga el código bueno.

### Mutación (C4 bis) · campaña REEJECUTADA en copia aislada

- **Recálculo independiente**: `alcance_de_feature("F-045")` → 112 líneas
  (`contenido.py` 68, `exporter.py` 44); `generar_mutantes` → 28 (8 + 20).
  Igual que el informe. El superviviente declarado (`contenido.py:84`,
  `!=` → `==`, `comparacion`) existe con ese texto exacto.
- **Por qué reejecutar con 678 s (> 60 s)**: el implementer la declara
  inestable (3, 1 y 1 supervivientes distintos en tres campañas) y el informe
  lleva uno. Repetida con `git worktree add --detach` de `3835c0c` en mi
  scratchpad, uniones a los dos `.venv`, `--workers 1`, misma semilla y
  `--salida` en el scratchpad: **20 evaluados, 20 muertos, 0 supervivientes, 0
  timeouts, 0 sin veredicto, 658,6 s**, base 43,4 s, media 32,9 s. Misma
  muestra: incluye los cuatro «supervivientes» de las tres campañas
  (`contenido.py:84`, `:116`, `:118`, `exporter.py:110` ×2) y todos mueren.
  Worktree y uniones retirados; `git status` limpio; los `.venv` intactos.
- **Juicio**: supervivientes falsos, de entorno, como decía el implementer
  (los `.pyc` de la copia los compiló un proceso lanzado desde la RAÍZ, y el
  arnés solo purga al escribir el fuente). Informe válido, superviviente
  analizado; el número bueno es 20/20.
- Coste 678,3 × 1 ÷ 20 = 33,9 s/mutante · sin «⚠ CAMPAÑA NO VÁLIDA» · 0 sin
  veredicto. **RM1**: SHA medido `ca221b5` (T14). `git diff ca221b5..fea1517` solo toca
  `progress/` y `tasks.md`: alcance medido = revisado (y mi campaña, sobre
  `3835c0c`, lo confirma).
- **RM2**: base 49,7 s, media 33,9 s, 1 worker, 19/20 muertos con `-x`:
  coherente; 20 × 33,9 = 678 s = total.
- **RM3**: ningún mutante equivalente entre los 28 (todos cambian algo
  observable: `+ 2` en 110 pinta J y `max_column` pasa a 10; 51 de ancho;
  `_OBSERVACIONES = 10` saca el ajuste de I…).
- **RM4**: innecesaria (campaña entera repetida) · **RM5** N/A: rigor
  `estandar` · **RM6** [x]: no se quitó defensa.

### Checkpoints (pasada 4)

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama `feature/F-045-…` · [x]
  `current.md` centrado en F-045 · [x] F-045 no cierra nada aún.
- **C3** [x] hexagonal (solo `infrastructure/excel/`) · [x] ruta en primera
  línea · [x] sin `print`, secretos ni dependencias nuevas · [x] trampas: no
  escribe en Sigrid, no toca escala ni `es_postventa`.
- **C3 bis** N/A: no toca `docs/referencia/` · **C4 ter** N/A: no existe
  `harness/rutas_sensibles.json`.
- **C4** [x] R1-R21 con test trazable y en verde (tabla abajo); R19 por el
  diff · [x] sin red ni BBDD · [x] M2 en `current.md` con comando exacto
  (cumplida).
- **C4 bis** [x] rigor declarado · [x] RED real (impl §9.2) · [x] cobertura
  `[OK]` 100 % · [x] mutación recalculada y REEJECUTADA (arriba) · [x]
  superviviente analizado · [x] «Evidencias» con los cuatro números; workers
  en §9.3 y en el informe (1) · [x] ningún N/A sin motivo.
- **C5** [x] T12-T15 `[x]` con commit `F-045 Tn:` (`b7e3616`, `927d592`,
  `ca221b5`, `33b9011`); T16 es MANUAL, cumplida en `fea1517`, falta marcarla
  (Al cerrar 1) · [x] árbol limpio · [x] `features.json` coherente.

### Cobertura requisito → test (`test_f045_*` salvo indicación)

R1-R19 como en la pasada 3 (r1 … r18, f040 r1-r19, f039 r21), con r3, r4_r10
×2 y r17 de F-045 y r3, r4, r6, r9 de F-040 ampliados a la columna I ·
**R20** `r20_observaciones_a_la_derecha_en_las_tres_hojas` (+ f040 r3, r4, r6)
· **R21** `r21_celda_de_observaciones_vacia_por_linea` (+ r13 y f040 r11:
rangos combinados exactos; r15: sin cursiva en I) · M1 y M2: humano.

### Al cerrar (no bloquean; los hace el líder en el commit de cierre)

1. `specs/F-045-excel-obras-postventa/tasks.md`: T16 → `[x]` con «Cumplida
   por el humano el 2026-10-08 («todo ok»)», como T6.
2. `design.md:95`: «— pendiente (T13)» → «— hecho (T13)»; y `design.md:30`:
   «lo pendiente es la ampliación D11, T12-T16» → T1-T16 hechas.
3. `progress/current.md:45`: «**Review 4 lanzada.** Después, M2.» → review 4
   APROBADA y M2 cumplida; y la mutación, con el resultado aislado (20/20).

### Automejora (propuesta, no aplicada)

- **arnes-base, `harness/mutacion.py`**: los falsos supervivientes de F-045
  salen de un `.pyc` escrito por OTRO proceso (ruta relativa desde la raíz)
  entre la purga y la ejecución. Propuesta: lanzar cada mutante con
  `PYTHONPYCACHEPREFIX` apuntando a un directorio propio y vacío de la
  campaña, de modo que el subproceso nunca lea `__pycache__` del árbol; o,
  mínimo, que `init.sh` avise si hay una campaña en curso (el centinela ya
  existe). Va al encargo de falsos supervivientes (`5370838`).
- **`reviewer.md`**: campaña declarada inestable ⇒ el reviewer la repite en un
  `git worktree` aislado aunque pase de 60 s (aquí, 11 min zanjaron la duda).
