Revisión completa (pasada 1): `git diff 651bc4c..HEAD` (HEAD `3ae2caf`; alcance de mutación desde `9f20dd5`, merge-base con `dev`)

# F-029 · Review · Selección múltiple con Ctrl/Shift y completar hasta el 100 %

**Veredicto: CHANGES_REQUESTED.** Solo por el **rastro** (dos cambios de una línea, abajo).
El código, los tests, la mutación y la documentación quedan **revisados y bien**: la pasada 2
puede ser incremental y limitarse a `tasks.md` y `current.md`.

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige C1-C5, fase RED en los
requisitos centrales, cobertura ≥ 80 % de lo cambiado y campaña de mutación (muestreada a 20,
semilla 20260820) con los supervivientes analizados; RM5 es N/A por nivel.

## Lo que se verificó, con resultado real

- **`bash harness/init.sh`** tal cual: ENTORNO LISTO, exit 0. Raíz `418 passed, 1 skipped`;
  `PUERTA COBERTURA [OK] 100.0 %` (84/84); tamaño dentro de los topes; ruff 222 (deuda previa).
- **Suites sin caché** (init.sh usó la caché por servicio, y la caché cruza ramas): sobre una
  copia `git archive HEAD` en el scratchpad, `-p no:cacheprovider`: api **586 passed**, front
  **53 passed**, transfer **379 passed**. Coinciden con «Evidencias».
- **Tests anteriores cambiados: ninguno.** `git diff 651bc4c..HEAD -- '*tests*'` solo trae
  dos ficheros **nuevos** (`A`): `test_f029_completar.py` y `test_f029_seleccion.py`. Lista
  cerrada de requirements §4 respetada.
- **Ficheros:** exactamente los de design §3-§4. Ninguno de §10 tocado (transfer, repositorios,
  ORM, `ports.py`, `app.py`, `deps.py`, Python del front). Árbol limpio al terminar.

### Los ocho puntos del encargo

1. **R12 / R20.** El cuerpo que manda `lanzarCompletar` es `{trabajadores, obra_ide,
   es_postventa}`, sin cifras (test `r12` lo vigila en las seis funciones nuevas). «Lo que
   falta» sale de `domain/estados.py::completar_hasta_100`. El caso de uso valida periodo y
   obra **antes** de tocar a nadie y hace **un** `commit` al final; si algo revienta a mitad,
   la UoW hace rollback. Tests `r22_caso_…` (5 obras: `reemplazados == []`, sin eventos,
   `commits == 0`) y `r25_caso_…_un_solo_commit`.
2. **R15-R19.** Clave `Linea.clave() == (obra_ide, es_postventa)`; las demás líneas salen
   como **el mismo objeto** (`is`, test `r15_dominio`). Total 100,00 exacto (`r16`, D5 con
   0,01 y escala `-2`). R18 en los dos sentidos con un doble que conserva el modo. Un evento
   `COMPLETAR` por trabajador con `X-Usuario` y snapshots de `_snapshot`; deshacer restaura
   para quien lanzó y `DeshacerAjeno` para otro; `puede_deshacer` True/False (`r19`).
3. **R22-R24.** `_obra_destino_o_error` busca en `obras.listar_para_periodo` con
   `empresa_obras` y decide con la ÚNICA `Linea.ofrecible`: 102 inactiva, 101 como `Postv-`,
   104 cerrada como normal, 900 (de la 28) y 999 → 422 sin tocar a nadie (caso y ruta);
   104 como `Postv-` sí se completa. No visibles (11, 15, 999) y no vigentes (12, 13, en
   FALTA) no paran el lote (`r23_r24`).
4. **R5 / teclado.** Las ramas de `teclas` de antes siguen **literales** (test compara el
   texto plano entero). C y Esc van **detrás**, en la rama de editor cerrado y `!enInput`;
   C exige `!ctrl && !meta && !alt` (Ctrl+C intacto). El campo del diálogo y el `.modal`
   hacen `stopPropagation()` de todo; `abrirModal` recrea el `.modal`, así que los
   `keydown` no se acumulan entre aperturas.
5. **Tests anteriores:** ninguno (arriba).
6. **Mutación** (sección siguiente): 20/20 confirmado; el falso superviviente, **reproducido
   muerto**.
7. **Documentación:** punto 15 `#regla-completar` con procedencia, la ruta en la lista de
   endpoints y el ancla en la cabecera de fuentes únicas; INTEGRACION §5; fila del README de
   la api. `azure-apps` `a593bd4`: el párrafo de §5 es **literal** (comparado línea a línea)
   y la cabecera dice «Sin desplegar todavía».
8. **Rastro:** `grep -n "Ninguna feature" progress/current.md` → **vacío**. T9 MANUAL listada
   con el comando exacto de arranque, la URL y «Resultado: _pendiente_»; la condición del
   humano (probar en local antes de desplegar) consta. **Dos incoherencias**: cambios 1 y 2.

## Mutación (C4 bis)

- **Recálculo independiente** (`alcance_de_feature` + `generar_mutantes`, cálculo puro):
  5 ficheros, **272 líneas**, **20 mutantes** (use_cases 9, estados 6, models 2, schemas 3,
  routes 0). Coincide con el informe; 20 = tope, así que «campaña completa» es correcto.
- **Campaña no reejecutada: 398,2 s según el informe** (> 60 s). Vale el recálculo + RM.
- **Coste por mutante:** 398,2 × 1 ÷ 20 = 19,9 s (> 1 s). **RM2:** media 19,9 s frente a
  base 36,1 s (más de la décima parte; `-x` con 20/20 muertos la baja); 20 × 19,9 = 398 ✓.
- **RM1:** SHA medido `53e3f79`. Desde ahí solo cambian `progress/` y `tasks.md`
  (`git diff --name-only 53e3f79..HEAD`): el alcance medido es el revisado.
- **RM4, sobre copia en el scratchpad**, solo `test_f029_completar.py`:
  - `use_cases.py:380` `is` → `is not` (el **falso superviviente** de la 1.ª campaña):
    **3 failed** — `r17_caso_ok_y_exceso…`, `r25_ruta_200…`, `r14_ruta_empresa…`. Lo que
    dice el implementer, al pie de la letra. Con `is not`, OK sale EXCESO: el mutante NO es
    equivalente y la suite lo caza. Su supervivencia en la 1.ª campaña es un fallo de la
    herramienta, no un hueco de tests; ya está encargado a `arnes-base` (`58403df`, existe).
  - `use_cases.py:411` `and` → `or`: 10 failed. `models.py:112` `frozen` → `False`:
    1 failed (`r25_dominio_resultados_inmutables`, el test de T8). `estados.py:69`
    `sumada = True`: 14 failed.
- **RM3:** ninguno de los 20 es equivalente (todos cambian comportamiento observable).
  **RM5:** N/A por nivel `estandar`. **RM6:** N/A: no se quitó ninguna guarda; T8 **añadió**
  un test. Sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto» 0, workers 1, 0 supervivientes.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` (F-029) · [x] rama `feature/F-029-…` · [x] `current.md`
  de la sesión activa (con la deriva del cambio 2) · [x] `done` con resumen en `history.md`.
- **C3** [x] hexagonal: `estados.py` solo importa `domain.models`; el caso de uso, dominio
  y puertos existentes · [x] primera línea con ruta (también los tests nuevos, como F-024/25)
  · [x] sin prints, TODOs, secretos ni dependencias nuevas (el correo de prueba ya está en
  `test_f027`) · [x] trampas: **escala** 0-100 sin conversión nueva (`anadido` float 0-100);
  **postventa** en la clave; **Sigrid** intacto, R26 con `registro_sigrid.llamadas == []`.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: no hay `rutas_sensibles.json`.
- **C4** [x] R1-R27 con tests `test_f029_rN_*` en verde (tabla) · [x] sin red ni BBDD
  (estáticos y dobles) · [x] T9 MANUAL en `current.md` con comando exacto, pendiente.
- **C4 bis** [x] `rigor` declarado · [x] RED con trazas reales de T1-T5 (R15-R20, R22 en T2)
  · [x] cobertura 100 % · [x] recálculo 272/20 · [x] campaña de 398 s no reejecutada (dicho)
  · [x] 19,9 s por mutante · [x] sin cabecera de no válida · [x] RM1, RM2 · [x] RM5 y RM6
  N/A justificados · [x] nada `PENDIENTE` · [x] «Evidencias» con los cuatro números y
  `--workers 1` · [x] ningún N/A sin motivo.
- **C5** [ ] **T7 hecha pero sin marcar** (cambio 1); T1-T6, T8, T10 `[x]` con commit
  `F-029 Tn:`; T9 N/A **justificado** (MANUAL del humano: bloquea el `done`, no la review)
  · [x] sin temporales · [x] `features.json` en `in_progress`.

## Cobertura requisito → test

| R | Tests |
|---|---|
| R1-R7 | `test_f029_seleccion.py`: `r1` (2), `r2` (2), `r3`, `r4`, `r5` (3), `r6`, `r7` (2) |
| R8-R13 | idem: `r8` (4), `r9` (2), `r10` (2), `r11` (3), `r12`, `r13` |
| R14 | `r14_caso_repetidos…`, `r14_ruta_empresa…`, `r14_ruta_422_sin_abrir_uow` (×7), `r14_ruta_admite_500_ides` |
| R15-R18 | `r15_dominio` (3), `r16_dominio` (3), `r17_dominio` (2, 5 casos), `r18_dominio`; `r15_caso` (3), `r16_caso`, `r17_caso`, `r18_caso` (3) |
| R19 | `r19_dominio_tipos_nuevos`, `r19_caso_un_evento…`, `r19_caso_deshacer…`; usuario en `r25_ruta_200` |
| R20-R22 | `r22_caso_obra_no_valida…` (×5, `commits == 0`), `r22_caso_postv_de_obra_cerrada…`, `r21_caso…`, `r22_ruta` (×4), `r21_ruta_…404` |
| R23-R26 | `r23_r24_caso…`, `r25_caso_resumen…`, `r25_ruta_200…` (forma + R26), `r25_dominio_resultados_inmutables` |
| R27 | documental: leído (punto 7 arriba); `test_f002_fuente_unica` y `test_f004_readme` en verde |

## Cambios requeridos

1. **`specs/F-029-seleccion-multiple-completar-100/tasks.md`, T7:** está `[ ]`, pero
   `current.md` y el commit `3ae2caf` la dan por hecha (`azure-apps` `a593bd4`, literal, lo
   he comprobado). Marcarla `[x]`. No es una MANUAL pendiente: dejarla abierta dice lo
   contrario de lo que pasó.
2. **`progress/current.md`, «Lo siguiente, por prioridad»:** dice «Primero **F-028**;
   después F-021, F-029, F-030…», con F-029 ya en curso por decisión del humano (cabecera
   y sección F-029). Reescribirlo para que diga qué viene **después de F-029** (F-028, F-021,
   F-030, …) sin listar como futura la feature en curso.

## Observaciones (no bloquean; para T9)

- **Ctrl/Shift+clic con el editor abierto** repinta la tabla (`renderTabla` reconstruye la
  fila del editor desde `state.edicion`): no se pierde nada, pero el foco puede saltar.
  Merece un vistazo en T9 (a).
- **Front, solo estático.** El comportamiento real (rango, foco, Enter en el diálogo) solo lo
  cubren T9 y la comprobación en node del implementer, no versionada. Es lo previsto en el
  design §11; la condición del humano de probar en local antes de desplegar lo cubre.
- `progress/impl_F-029.md` dice aún «Falta: T7»: es el informe del implementer en su
  momento; no hace falta tocarlo.
