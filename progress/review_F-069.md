<!-- progress/review_F-069.md -->
Revisión incremental desde 3f9b5ff (pasada 3), principal, sobre `789e8c4` (`git diff 3f9b5ff..789e8c4`: 4 commits, 5 ficheros).

# F-069 · Review 3 (principal, incremental)

**Veredicto: APPROVED.** El código sigue aprobado en `3f9b5ff` y el delta no lo toca. Los cambios 1 y
2 de la review 2 están resueltos y O1-O3 recogidas. Quedan tres erratas de rastro que no inducen a
error (O1-O3, abajo); se corrigen antes de la pasada de evidencias, que las comprueba.

**Reviews anteriores (resumen):**
- **Review 1** (`ed7c212`): CAMBIOS REQUERIDOS, 1-7 (D11 en el front, RED de R15/R8/R32,
  `MARCA_PRUEBAS` en la api, T16, R30, `current.md`, spec). Resueltos en la pasada 2.
- **Review 2** (`3f9b5ff`, completa): código APROBADO; CAMBIOS REQUERIDOS solo de papeleo:
  1, design §6.5 y §7.1 y la decisión 8 del informe frente a lo construido; 2, seis frases falsas de
  `current.md`. Observaciones O1 (log en T16), O2 (`comentario_de_tex` sin espacio) y O3 (alcance de
  la campaña). Con detalle de D20, tabla de cambios y C1-C5: `git show 909a5e2:progress/review_F-069.md`.

**Rigor:** `critico` (`features.json`): RED en los centrales, cobertura ≥ 90 %, mutación con 0
supervivientes en la muestra y MANUAL con su comando. Mutación y RM1-RM7: **pendiente: pasada de
evidencias** (T13/T18). Capa e2e N/A (ningún servicio la declara).

## El delta: sin código

`git diff --stat 3f9b5ff..789e8c4`: `progress/current.md`, `progress/impl_F-069.md`,
`progress/review_F-069.md`, `specs/F-069-importe-caja-km/design.md` y `tasks.md`. Nada en
`services/`, `tests/`, `docs/` ni `harness/`: la review puede ser incremental entera. El §9.1 del
design solo se ha reflowado (mismo texto palabra a palabra, comprobado con `md5sum` del texto
normalizado en los dos SHA).

## Cambio 1 de la review 2 (design y decisión 8): resuelto

Contrastado con `registro_pipeline.py` en `789e8c4` (`_actualizar_tex`, l. 1478-1533;
`_tex_sigue_valiendo`, l. 1535-1544; retornos de `ejecutar`, l. 1250, 1278, 1441, 1454, 1475):

| Lo que dice §6.5 «Paso 10» | En el código |
|---|---|
| Lo último de `ejecutar`, tras titulares y vinculados o sin nada más que escribir | Los cinco retornos pasan por `_ejecutar_vinculados`, que acaba siempre en `_actualizar_tex` (también sin vinculados, l. 1454) |
| Solo si alguna trae `tex_nuevo` | `piezas` vacías ⇒ `return res` sin leer |
| Relectura propia `lineas_para_editar` | `self._cli.lineas_para_editar([...hmores_ide])` |
| Las que siguen valiendo (nuestra, recurso y hora, sin enlaces, En registro) | `_tex_sigue_valiendo`: `enlazada`, `reside`, `porcentajes:`, `parte_est`, `M*` o la hora del vinculado |
| `stmt_editar_tex` en un lote propio | un `escribir(statements)` aparte, con `obride` en pruebas (§7.1) |
| Comprobación `lineas_registradas(con_tex=True)` ⇒ `tex_actualizadas`; las demás, al log | igual, con el `warning` «la guarda no dejo cambiar el tex» |
| Solo el `tex`; nunca `DELETE` | `stmt_editar_tex` (aprobado en la review 2) |

- [x] §7.1 añade la comprobación tras `stmt_editar_tex` con la misma lectura ampliada.
- [x] El paso 6 de §6.5 se reescribe sin cambio de sentido.
- [x] Decisión 8 del informe: «dos lecturas (relectura y comprobación) y una escritura más, solo si
  alguna trae `tex_nuevo`». Preciso salvo un detalle menor: si la relectura descarta todas, solo hay
  una lectura y ninguna escritura (`if not statements: return res`); no hace falta tocarlo.
- [x] Tamaño: design 250/250 (sustitución, no añadido).

## Cambio 2 de la review 2 (seis frases de `current.md`): resuelto

| Punto | Hoy |
|---|---|
| l. 19, hotfix `/propuestas` | «Desplegado el 2026-11-11 (api `r20261111-1915`)» |
| l. 29, hotfix VP | «Desplegado el 2026-11-11…; si no se ha hecho, queda “Sincronizar Sigrid”» |
| l. 59, `arnes-base` | «1 commit por delante (`8de97cb`)»: comprobado, `main...origin/main [ahead 1]` |
| l. 256, «Producción, hoy» | entrada nueva en l. 259 con api `r20261111-1915`, front `r20261111-1916`, transfer `r20261028-1914` |
| l. 491, orden | «Orden de lo pendiente: el de `BACKLOG.md`» |
| l. 578, F-062 | «T19 y T20, MANUAL, HECHAS (`progress/manual_F-062.md`)»: el fichero existe |

## O1-O3 de la review 2: recogidas

- [x] **O1** en `tasks.md` T16 (los dos `warning` del transfer, con su texto real) y en `current.md`
  l. 89 (uno de los dos; ver O2 abajo).
- [x] **O2** aceptada y anotada en `current.md` l. 81.
- [x] **O3** en `current.md` l. 81 y l. 84 (alcance de T13).
- [x] La automejora de la review 2 queda anotada en l. 81, para después del cierre.

## `current.md` releído entero (707 líneas): lo que queda

Las seis de la review 2 están bien. Al releer entero quedan estas, todas menores; **son todas**:

- **O1 · «decisión 8» donde es la 6.** `current.md` l. 88 («el del titular no vuelve en modo pruebas:
  decisión 8 del informe») y `tasks.md` T16 («decisión 8 del implementer»). En `impl_F-069.md` esa es
  la **decisión 6**; la 8 es D20. El paréntesis dice ya el motivo, así que no lleva a error, pero la
  referencia es falsa. Ya estaba en `3f9b5ff` y se me pasó en la review 2.
- **O2 · O1 a medias en `current.md`.** l. 89 da solo uno de los dos `warning`; `tasks.md` T16 da los
  dos («la guarda no dejo cambiar el tex» y «no se cambia el tex de la linea … ya no vale»). Añadir
  el segundo o remitir a T16.
- **O3 · «Sincronizar Sigrid» pendiente, ya hecho.** l. 304-305 (despliegue de F-044 en «Producción,
  hoy») sigue diciendo «Pendiente del humano: … **«Sincronizar Sigrid»** (sin él no hay vínculos ni
  subfilas)», y l. 53 dice que está hecho (el humano lo confirmó el 2026-10-27). Lo mismo para F-030
  en l. 223-224 («lanzar un sync… hasta que el sync llene el catálogo»): ese sync es anterior. Dejar
  en esas entradas solo lo que de verdad queda (MANUAL B de F-064 y aviso a `partes`).

No bloquean: no cambian lo que hace nadie ni la MANUAL que ejecutará el humano, y ninguna es de esta
pasada. **Se recogen antes de la pasada de evidencias**, que las mira (si no, vuelven como bloqueo).

## Checkpoints (delta)

- **C1** [x] `ARNES_SIN_CACHE=1 bash harness/init.sh` entero sobre `789e8c4` (pie). [x] Arnés sin tocar.
- **C2** [x] Una sola activa (F-069 `in_review`), rama `feature/F-069-importe-caja-km`, orden. [x]
  `current.md`: los seis de la review 2 corregidos; las tres erratas residuales, O1-O3.
- **C3** [x] Sin código en el delta: lo aprobado en `3f9b5ff` sigue valiendo (hexagonal, ruta en la
  1.ª línea, sin `print`/secretos, límite de servicio, solo escribe el transfer).
- **C3 bis** N/A: el delta no toca `docs/referencia/`. **C3 ter** [x] design §6.5 y §7.1 frente a lo
  construido (tabla arriba); D17-D21 con cita y fecha (sin cambios).
- **C3 quater** pendiente de T17 al desplegar, listado con contenido en `current.md` l. 93.
- **C4** [x] R1-R36 con test o MANUAL (tabla de la review 2, sin cambios: el delta no mueve tests).
  [x] MANUAL T16 y T17 con comando y resultado esperado; T16 con O1 de la review 2.
- **C4 bis** [x] Nivel declarado. [x] RED y «Evidencias» (aprobadas en la review 2). [x] Cobertura
  `[OK]` (pie). Mutación y RM1-RM7: **pendiente: pasada de evidencias** (T13/T18), con el alcance de O3
  de la review 2 (`texto_linea.py`, `_actualizar_tex`, `_tex_sigue_valiendo`).
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] Commits del delta con prefijo `F-069:` (papeleo, sin tarea). T13, T16-T18 abiertas,
  legítimas en esta fase.

## Cobertura (requisito → test)

Sin cambios desde la review 2 (el delta no toca tests): R1-R34 con test, R35-R36 MANUAL (T16, T17).
Tabla completa: `git show 909a5e2:progress/review_F-069.md`, sección «Cobertura».

## Cambios requeridos

Ninguno. Para el líder, antes de la pasada de evidencias: O1-O3 de esta review.

## Automejora (propuesta para `reviewer.md`)

La «decisión N» citada en otro fichero se desfasa cuando el informe se renumera entre pasadas. Al
releer `current.md` y `tasks.md`, contrastar cada «decisión N del informe» con la lista del informe.

## Resultado de `ARNES_SIN_CACHE=1 bash harness/init.sh` (`789e8c4`, sin pipes)

- **1.ª ejecución, código 1:** raíz 1 failed, 2231 passed (`-x`). Cayó
  `tests/test_mutacion_prueba_de_verdad.py::test_F_cada_patron_da_su_mutante…` con «TIMEOUT tras 258 s
  en 1 mutante… máquina sobresuscrita». Test del arnés, ajeno al delta. La suite duró 15 h 23 min
  porque la máquina se suspendió durante la noche. No se aprueba sobre ella.
- **2.ª ejecución (2026-11-20), código 0, ningún `[KO]`, «ENTORNO LISTO»:** raíz 2319 passed / 47
  skipped (17 min 14 s); api 1632; front 573; transfer 1956. `[OK]` PUERTA COBERTURA 99,6 % (687/690),
  TAMAÑO, CARRIL N/A y CAPA E2E N/A. Este informe, medido con `harness.tamano` (código 0).
