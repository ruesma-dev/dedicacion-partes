Revisión completa (pasada 1): `git diff 8ac020b..HEAD` (HEAD `171464defe282c11cc10984a195930403d7ec9a4`)

# F-025 · Review · Obras de postventa sacadas de los capítulos de POSTV2

**Veredicto: CHANGES_REQUESTED**, **solo por el rastro** (C2, `progress/current.md`).
El código, los tests, `#regla-p5` y la campaña de mutación están bien. La pasada 2 puede
limitarse al delta de `progress/`.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige C1-C5, RED, cobertura
≥ 80 %, mutación completa con 0 supervivientes, RM1-RM6 y MANUAL con comando exacto.

## Verificación ejecutada

- `bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz `418 passed, 1 skipped`;
  cobertura `[OK]` 100 % (162/162); tamaño dentro de los topes; ruff 215 avisos (no bloquea).
- Las suites de servicio venían de la caché, así que las relancé **sin caché** sobre una copia
  `git archive HEAD` (scratchpad, `-p no:cacheprovider`): api `503 passed`, transfer
  `379 passed`, front `28 passed`. Coincide con el informe.
- El árbol queda limpio y sin `stash`, y la rama es la correcta.

## Los ocho puntos del líder

1. **D1.** El preflight (`_destino_postventa`) y `POST /api/postventa/universo` llaman a las
   mismas `cargar_catalogo_postventa` y `casar_postventa`. La api no casa: manda y guarda
   `ide`. El front solo pinta `activa`, `admite_postventa` y `ofrecible`. Contra la
   divergencia: `r2_universo_y_preflight_casan_igual` (8 obras), `r3_*` (mismo texto con la
   obra de postventa ausente o ambigua) y `r12_lo_que_se_manda_es_lo_que_se_guarda`.
2. **D2 = B y D8 = A.** Casa el código exacto, o un prefijo seguido solo de letras
   (`normalize_code` quita los guiones, no los puntos). Fuera: `CP→CP.1`, `0678→0678.MO`,
   `OT→CI.7.5` y `191105→0611`. Sigue dentro `0654→0654-B` (`test_f025_casado_p5.py` y el
   cruce).
3. **`#regla-p5` sigue siendo cierta.** Mantiene hoja activa, el casado de R10, el universo,
   `(#regla-empresa)` y «Confirmado por», y añade la procedencia F-025. No queda ninguna
   mención de la cascada vieja en el código ni en la documentación, y F-002 está en verde.
4. **Tests anteriores.** El diff `'*tests*'` toca 13 ficheros: 5 nuevos, los dos
   `conftest.py` (previstos en design §3) y los de §7.1, contrastados fila a fila con la
   tabla §3: ninguno sin declarar, ninguno pierde exigencia (`r16_el_capitulo_…` exige
   omitir sin `paride` ni inserts; los overrides prueban capítulo `11` y hoja `0713`; `r19`
   con dos candidatas reales; la api solo cambia firmas y dobles).
5. **Mutación**: C4 bis; los 3 falsos supervivientes en paralelo, **reproducidos** (RM4).
6. **`_nodos_pv`** fuera de producción: la instancia solo guarda `_cli` y `_st` (`r8_*`, `r9_*`).
7. **Script.** No contiene `ejecutar`, ni siquiera en comentarios, y solo llama a
   `127.0.0.1`. Además de lo que lista la T11 hace `POST periodos` y `PUT asignaciones`, los
   dos contra la BBDD local; la cabecera los declara y M2 los necesita. No lo he ejecutado.
8. **`current.md` NO es coherente** (ver cambios requeridos). La parte MANUAL sí está bien:
   T10, T13 y T14 tienen comando exacto, y lo pendiente en `azure-apps` está listado
   (22+/2−, sin commit).

## Checkpoints

**C1** [x] exit 0 · [x] ficheros base.

**C2** [x] una `in_progress` · [x] rama · [x] `done` en `history.md` (script) · **[ ]
`current.md` solo con la sesión activa**: l. 4 «**Ninguna feature en ejecución.**» con F-025
en curso; l. 65-67 («el spec-author la reescribe … antes de implementar»), anterior a la
revisión de la spec. Mismo defecto que la obs. 2 de F-034 y la pasada 2 de F-026.

**C3** [x] hexagonal (`texto_o_none` al dominio, impl §2.1) · [x] primera línea con ruta ·
[x] sin prints, TODOs, secretos ni dependencias · [x] trampas: escala intacta;
`admite_postventa` independiente de `activa` y clave `(obra, es_postventa)`; sin escritura ni
SQL nueva contra Sigrid, modo pruebas e `ide` intactos.

**C3 bis** N/A: el diff no toca `docs/referencia/`. **C4 ter** N/A: no hay
`rutas_sensibles.json`, solo el ejemplo.

**C4** [x] R1-R25 tienen tests en verde (tabla abajo); R26 es documental (`INTEGRACION.md`
§5 y §7, y `azure-apps` en la T10). [x] Sin red ni BBDD: `ClienteFalso`, `UniversoFalso`,
`httpx.post` sustituido, `_SesionRepo` y `TestClient`. [x] MANUAL en `current.md`.

**C4 bis**
- [x] `rigor` declarado. [x] RED con trazas reales de T1-T8 (impl §4). [x] Cobertura al
  100 %.
- [x] Recálculo independiente (`harness.alcance` + `generar_mutantes` en HEAD): **17
  ficheros, 458 líneas, 56 mutantes**, igual que el informe.
- [x] Campaña **no reejecutada**: 649,9 s, por encima de 60 s, así que basta el recálculo
  con RM1-RM6 y RM4. El coste por mutante es 649,9 × 1 ÷ 56 = 11,6 s, por encima de 1 s.
- [x] No hay «⚠ CAMPAÑA NO VÁLIDA» y «Sin veredicto» es 0; declara la línea base.
- [x] RM1: midió `be3d3ae`. Hasta HEAD solo cambian `progress/` y `tasks.md`, y el alcance
  recalculado es idéntico.
- [x] RM2: bases de 21,3 s (api) y 6,2 s (transfer); media 11,6 s con W = 1;
  56 × 11,6 ≈ 649,9 s.
- [x] RM5 N/A **justificado**: no hay ningún superviviente ni ningún equivalente declarado.
- [x] RM6: se quitó `and postventa_registrar` (impl §2.3). Era una comprobación duplicada, no
  una guarda `is None`. El invariante está en quien construye el catálogo:
  `cargar_catalogo_postventa` devuelve `MOTIVO_POSTVENTA_OFF` sin leer (`r5_…sin_leer`).
  Comprobado en la copia: el preflight con postventa desactivada omite con ese motivo, no
  lee el presupuesto y devuelve `partidas_postventa == []`.
- [x] No hay campaña manual (la automática da 56). [x] 0 supervivientes, ninguno
  `PENDIENTE`. [x] «Evidencias» trae los cuatro números y los workers (§6: `--workers 1`).
  [x] Ningún N/A sin motivo.
- **RM3:** he repasado los 56 mutantes y ningún equivalente sale muerto. `frozen` y los
  `default` tienen test (`r18_resultado_universo_es_inmutable`, `r9_el_catalogo_…`,
  `r21_columna_…`).
- **RM4:** copia `git archive`, suite del transfer `-x` sin caché (base `379 passed`):
  `universo_postventa.py:31` y `:80`, `app.py:182` (`r4_…[ausente]`) y `:190`
  (`r6_fallo_de_sigrid_502`) dan `1 failed` cada uno; también mueren `:179/181/187/191`. El
  defecto es del arnés en paralelo (encargo `0ecafc2` en `arnes-base`, existe).

**C5** [x] T1-T9, T11, T12 y T15 en `[x]`, con un commit `F-025 Tn:` cada una. T10, T13 y
T14 son N/A **justificado**: son MANUAL (humano) y bloquean el `done`, no la review. [x] Sin
temporales. [x] `features.json` en `in_progress`.

## Cobertura requisito → test

| R | Tests |
|---|---|
| R1-R9 | `test_f025_universo_postventa.py`: `r1` (3), `r2` (8 casos), `r3` (2), `r4` (×4), `r5`-`r8` (2 c/u), `r9` (3) |
| R10-R11 | `test_f025_casado_p5.py` (14 + parametrizados), `r11_el_universo_del_cruce_…` |
| R12-R16 | `test_f025_sync_postventa.py`: `r12` (4), `r13` (4), `r14` (2), `r15` (8), `r16` (3) |
| R17-R21 | `test_f025_cuadrante_postventa.py` / `_sync_`: `r17` (4), `r18` (6), `r19` (3), `r20` (8), `r21` (3) |
| R22-R24 | `dedicacion-front/tests/test_f025_catalogo_postventa.py` (7) |
| R25 / R26 | `r25_el_modulo_nuevo_no_lleva_el_literal` + lectura de `#regla-p5` / `INTEGRACION.md` + T10 |

## Cambios requeridos

1. `progress/current.md`, l. 4: quitar «Ninguna feature en ejecución». Debe decir que F-025
   está en curso, con la review pendiente solo del rastro.
2. `progress/current.md`, l. 65-67: quitar «spec aprobada con D4 cambiada … el spec-author la
   reescribe en su sitio antes de implementar». La spec ya está aprobada con D8 = A e
   implementada; a F-025 le quedan T10, T13, T14 y el `done`.
3. `progress/current.md`, sección F-025: anotar las condiciones de despliegue, que hoy
   están repartidas entre impl §7 e `INTEGRACION.md` §7:
   - El transfer se despliega **antes o junto con** la api; si no, el sync da 502 (D3).
   - Hay que lanzar un **sync justo después**: hasta entonces ninguna obra ofrece `Postv-`
     y las líneas de postventa guardadas salen como no ofrecibles.
   - El aviso a usuarios sobre CP/OT se retira con ese despliegue.

## Observaciones (no bloquean; recoger o descartar por escrito)

- `depurar_obras` compara `fila["ide"] in universo` sin convertir, mientras que
  `sincronizar` hace `int(fila["ide"])`. Con un `ide` en texto, ninguna obra admitiría
  postventa y nada fallaría. M1 lo cazaría (83/73); `_entero` lo cierra en una línea.
- Hay 15 avisos nuevos de ruff (de 200 a 215), arreglables con `--fix`. Además,
  `sync_pipeline.py` importa `_entero`, privado de `filtros_maestros`.

## Automejora (propuesta, no aplicada)

Tercera feature seguida (F-034, F-026, F-025) con la cabecera de `current.md` contra
`features.json`: subir de prioridad el encargo `69df67b` de `arnes-base` y, mientras, añadir a
`leader.md` antes de lanzar la review: `grep -n "Ninguna feature" progress/current.md` vacío.
