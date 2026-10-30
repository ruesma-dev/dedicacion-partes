<!-- progress/review_F-054.md -->
Revisión completa (pasada 1), HEAD `560c10a`, base `1ed18be` (`dev`; `a2d90f7` desciende de ella).

# F-054 · Review 1

**Veredicto: RECHAZADO (CHANGES_REQUESTED)**, solo por el rastro (bloqueos 1 y 2).
El código no tiene bloqueos: la pasada 2 puede ser incremental, sin repetir campaña
si `services/` no cambia.

**Rigor:** `critico`, declarado en `features.json`. Exige RED, cobertura, mutación
completa con 0 supervivientes y MANUAL con comando exacto.

## Bloqueos

1. **C4, `progress/current.md:12-17`.** T18 y T19 son `MANUAL (humano)` y el
   checkbox las pide listadas en `current.md` **con su comando exacto**. Hoy solo
   hay un puntero a `tasks.md` e `impl_F-054.md`. Copiar a `current.md` el `curl`
   de T18, el `prueba_escritura_porcentajes.py estado --ano 2026 --mes 11` de T19
   con sus pasos, y lo de T10 y T20. T10 no tiene comando ni en `tasks.md`: escribir
   cómo se mide (remite a F-055 T18) y que va sobre `ccad4db`.
2. **C2, `progress/current.md`, sección de la línea 52.** «La copia no tiene
   `.venv`» es falso hoy: hay tres. La sección («spec REVISADA») es de antes de
   implementar y da otro tamaño de spec («requirements 149»). Podarla a lo vigente.

## Lo que pediste juzgar

**Parte B, escritura en producción: correcta.**
- Guarda doble: `poner_a_cero.py:54-76` relee y compara recurso, hora, `can`,
  `synckey`, otro sistema, enlaces, En registro y 0404; el SQL repite la guarda
  (`sigrid_write_client.py`, `_guarda`). La 0404 solo está en la guarda previa, como
  dice el design.
- Nunca `DELETE`: la única sentencia es `UPDATE hmores SET can = 0, tot = 0`.
- Solo lo confirmado: `registroEjecutar` (`app.js`) filtra por `.chk-cero:checked`.
  Las no confirmables no tienen casilla y el transfer las rechaza igual. D17 se
  cumple. La api no contrasta con el preflight: reenvía lo recibido y la defensa es
  la guarda del transfer.
- Fallo ⇒ sin `ejecutar`: `RegistroSigrid.ejecutar` llama antes del bucle; una
  excepción, un 502 o un `ok` ausente dan `RuntimeError` (`transfer_client.py`
  `poner_a_cero`, también con transfer viejo: 404 ⇒ error). `ok: true` con todo
  omitido sigue, y es lo diseñado (R36). Si falla a mitad de lotes, lo ya puesto
  queda a 0, pero `_traza` ya lo dejó en el log antes de escribir.
- `_sobrantes_a_cero` valida el cuerpo antes de llamar al caso de uso (422).

**Desviaciones.**
- Nº 1 (vigencia): aceptada. `vigente_en` es la regla única, y mejor que `activo`.
- Nº 6 (`populate_existing`): aceptada. La sesión tiene autoflush por defecto y no
  hay `no_autoflush`, así que no pisa cambios pendientes. Llamantes revisados:
  `propuestas_mes.py:158`, `use_cases.py:708` y `:942`. Solo refresca `PeriodoORM`.
- Nº 13 (código en vez de `ide`): aceptada. No exige lecturas extra y el código es
  único dentro de la empresa, que es por la que se lee. Efecto: `cod_pruebas` no se
  usa en `cubierta` (ver O4).
- Nº 14 (partida 0 en pruebas): aceptada, solo reduce sobrantes y solo en pruebas.
- Nº 16 (`_fila`/`_traza`): aceptada. Es acoplamiento a privados, pero da el log de
  F-051 sin duplicar y sin tocar `registro_pipeline.py`. El log con `antes` sale
  antes de escribir.

**ruff, de 309 a 363: los 54 son de esta feature**, no deuda previa como dice
`impl_F-054.md` (init imprime esa etiqueta para todo). Comparado fichero a fichero
contra `dev`: todo el aumento cae en ficheros del diff. Casi todo es estilo (RUF100,
FURB157, I001, modelos). Ver O1.

**requirements/venvs:** la feature no toca ningún `requirements*`; el techo
`SQLAlchemy<2.1` viene de `dev`. La api tiene 2.0.55. `.venv` está ignorado.

## Checkpoints

- **C1** [x] `init.sh` código 0, sin `[KO]`, con `suite_*.ok` borrados · [x] ficheros.
- **C2** [x] una `in_progress` · [x] rama · **[ ] `current.md`, bloqueo 2** · [x] history.
- **C3** [x] Hexagonal: dominio limpio; `application` importa `PREFIJO_SYNCKEY` de
  infraestructura igual que `registro_pipeline.py` y `reglas_porcentajes.py` ·
  [x] primera línea · [x] sin `print`, TODO ni secretos, sin dependencias nuevas ·
  [x] escala (`can × 100` en `domain/traer_sigrid.py`, sobre 1 en el resto) ·
  [x] postventa con `es_postventa` en la clave · [x] solo escribe el transfer, y B
  edita sin insertar (no necesita `synckey` nueva ni reserva `ide`).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazables · [x] sin red ni BBDD · **[ ] MANUAL, bloqueo 1**.
- **C4 bis** [x] rigor declarado · [x] RED con trazas reales, T1-T15 · [x] cobertura
  `[OK]` 99,5 % (744/748) · [x] totales recalculados: 1626 líneas, 21 ficheros y
  262 mutantes coinciden · [x] «CAMPAÑA NO VÁLIDA» ausente, sin veredicto 0 ·
  [x] **campaña no reejecutada: 3767 s según el informe**; recálculo puro más RM ·
  [x] coste por mutante 57,5 s · [x] sin supervivientes, nada PENDIENTE ·
  [x] Evidencias con workers.
- **RM1** [x] SHA `c614be3`; `c614be3..HEAD` solo toca `progress/` y `tasks.md`.
  **RM2** [x] media 14,4 × 4 = 57,6 s frente a bases 78 y 40 s; 262 × 14,4 ≈ 3767 s.
  **RM3** [x] sin equivalentes declarados. **RM4** usada: dos mutantes de la guarda
  sobre copia, muertos (`hora.startswith("M")`, 2 fallos; `ls.enlazada`, 1), y copia
  limpia 36 passed. **RM5** N/A: ningún equivalente que muestrear. **RM6** [x]: T17 no
  quitó guardas (`impl_F-054.md`: sin cambiar producción; diff sin código de servicio).
- **Manual `app.js`** [x] tabla por fila con texto exacto. Reproducidas A3 (1 fallo,
  declara 1) y B20 (2 fallos, declara 2) con los ficheros de la feature.
- **C4 ter** N/A: sin `harness/rutas_sensibles.json` que lo active.
- **C5** [x] tareas no MANUAL `[x]`, commits `F-054 Tn:` · T10, T18-T20 `[ ]` por
  MANUAL, legítimo · [x] árbol limpio · [x] `features.json` `in_progress`.

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R3 | `test_f054_r1_*` (front), `r2`, `r3` (rutas, aceptar, endpoint) |
| R4-R7 | `test_f054_lectura_mensuales`, `r5`, `r6`, `r7` en endpoint |
| R8-R12 | `test_f054_traduccion` |
| R13-R18 | `test_f054_comparar` |
| R19-R26 | `test_f054_aceptar`, `r26` en rutas |
| R27-R28 | `test_f054_rutas`, `test_f054_traer_front` |
| R29 | `test_f002_fuente_unica` (ANCLAS) y grep; `azure-apps`, T20 |
| R30, R37 | MANUAL T10, T18, T19 |
| R31-R34, R38 | `test_f054_obra_cero`, `test_f054_modal_cero` |
| R35-R36 | `test_f054_poner_a_cero`, `test_f054_registro_cero` |

Suites: api 1467, transfer 1845, front 479, raíz 418 (1 skipped). **R37 sigue sin
cifra**: T10 no medido; si T19 supera el 15 %, PARA (design §6.4).

## Observaciones (no bloquean; recoger o decidir, no dejar en «anotado»)

- **O1. ruff.** Corregir lo que entra con la feature en ficheros nuevos, sobre todo
  `test_f054_mutacion.py:30` (F401, transfer) y `test_f054_obra_cero.py:343` (F811);
  y corregir en `impl_F-054.md` «deuda previa».
- **O2. Postventa omitida antes de resolverse** (`reglas_porcentajes.py:528-549`):
  `omitir` crea la acción con `destino = "obra"` y `paride = 0`. Con motivo de
  postventa o `POSTVENTA_REGISTRAR=false`, dos efectos en `cubierta`
  (`reglas_obra_cero.py`): la línea real en la obra de postventa sale sobrante, y
  esa `Postv-` «cubre» una línea normal de la obra de origen que la plataforma no
  da. Lo primero choca con «también omitida» (R31); el design §6.1 dice «resolvió».
  La casilla sale desmarcada: no hay escritura sin confirmar. Decide el humano.
- **O3. Línea de la 0404 en modo real:** sale como sobrante normal y confirmable. Es
  coherente con la spec, que solo define pruebas; conviene que el humano lo sepa.
- **O4.** Quitar `cod_pruebas` de `cubierta`, que no se usa.
- **O5. Front.** El toast solo da el número de omitidas, no su motivo, aunque R35
  las devuelve con motivo; y sale como éxito. Sincronizar en un mes cerrado o sin
  periodo da un toast rojo por el 409/404 de R2.
- **O6. Deshacer un `SIGRID`** va por `reemplazar`, que recrea toda la fila sin traza:
  la otra línea del trabajador pierde `sigrid_hmores_ide` y pasa a pisado (R24), sin
  duplicar. Comprobarlo en T18, paso 2.

## Cambios requeridos

1. `progress/current.md`: bloqueo 1.
2. `progress/current.md`: bloqueo 2.
