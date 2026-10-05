Revisión completa (pasada 1): `git diff f08d911..ac4c0a5` (HEAD `ac4c0a57dd0998208891ac8f4f35c734221d2e1a`)

# F-034 · Review · Las obras son siempre de Construcciones Ruesma

**Veredicto: APPROVED**

Rama `feature/F-034-obras-siempre-ruesma` en el árbol principal (verificado), árbol limpio
antes y después de la review. Los commits de rastro del líder (features.json, BACKLOG,
current.md, y `26d87bb` de F-026, que solo toca current.md) no tienen código.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige: C1-C5, fase RED, cobertura ≥ 80 %,
mutación con cero supervivientes salvo justificación aceptada por el humano, RM5 (muestra de
un equivalente) y las MANUAL en `current.md` con su comando exacto.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 355 passed / 1 skipped; COBERTURA
  `[OK]` 100,0 % (6/6); TAMAÑO en topes; ningún `.env` versionado.
- `init.sh` sirvió las suites de servicio desde caché, así que las relancé enteras sin
  caché: api **368 passed** (copia de HEAD en el scratchpad), front **21**, transfer **317**.
- `git diff f08d911..HEAD -- services/dedicacion-transfer` vacío (R9). Ningún `.env` en el
  diff. `azure-apps` sin commits de F-034 y limpio (T8 sigue pendiente, como debe).

## Revisión funcional

- **R1:** obras con `filtro.empresa_obras` (`use_cases.py:70`), único punto que arma la
  lista; el export reutiliza `ObtenerCuadrante`.
- **R2-R3:** `visible_en_empresa(t, filtro)` sin obras y NULL solo en la por defecto. Lo usan
  `_filas_de_empresa` (cuadrante, resumen y copia) y `registro_sigrid.py:74`.
- **R7-R8:** `"empresa": filtro.empresa_obras` (`registro_sigrid.py:87`). **R5:** las cuatro
  rutas pasan `filtro.empresa_obras` a `a_trabajador_out`.
- **Dónde sigue la elegida:** `routes.py:286/302` (a `RegistroSigrid`, que solo filtra
  trabajadores con ella) y `routes.py:171/258` (campo `empresa` de la respuesta y nombre del
  Excel, que deben ser E). `GuardarAsignaciones` no mira la empresa de la obra. **Ninguna ruta
  usa la elegida para las obras ni para la línea.**
- Contrato API ↔ transfer y esquemas sin campos nuevos. Front: solo dos textos.
- **Tests cambiados vs. design §6:** revisé los 5 ficheros línea a línea. Cada assert
  cambiado está en la lista cerrada (con B1-B4 de `ba55567`) o es consecuencia literal de
  «el resto de R6/R13/R15 cambia solo en los NULL» o «las llamadas pierden el argumento de
  obras». La tabla R2 baja de 7 a 5 casos porque dos quedaban duplicados (declarado).
  `acepta_cualquier_iterable` se sustituye como manda §6 y F-022 no se toca. **Ningún test
  aflojado.**

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base.
**C2** [x] una `in_progress` · [x] rama · [x] current.md (ver observación 2) · [x] `done`
con resumen.
**C3** [x] hexagonal (`domain/empresas.py` solo importa `domain.models`) · [x] primera línea
con ruta · [x] sin prints, TODO, secretos ni dependencias nuevas · [x] trampas: sin escala,
sin postventa, sin escritura nueva en Sigrid.
**C3 bis** N/A: el diff no toca `docs/referencia/`.
**C4** [x] trazabilidad (tabla abajo) · [x] tests offline (UoW, sesión, transfer y
contenedor falsos; `Settings(_env_file=None)`) · [x] T8 y T9 en `current.md` («F-034 ·
pendiente antes del done») con comando exacto y resultado esperado.
**C4 bis**
- [x] `rigor: critico` declarado · [x] RED: trazas reales de T1-T5 y R3 contra `d34e4a1` ·
  [x] cobertura `[OK]` 100 %.
- [x] Recálculo independiente: `harness.alcance` da 7 ficheros y 72 líneas;
  `generar_mutantes` da 3 (`registro_sigrid.py:74 [not]`, `use_cases.py:70 [comparacion]`,
  `routes.py:63 [logico]`). Coincide con el informe.
- [x] Los muertos, comprobados. «Tiempo total» 78,6 s, más de 60, así que no tocaba
  reejecutar; aun así, por la anomalía que declara el implementer, apliqué los 3 sobre una
  copia (RM4): A1 30 fallos, A2 13, A3 22. Muertos.
- [x] Coste por mutante 78,6 × 3 ÷ 3 = 78,6 s · [x] sin «CAMPAÑA NO VÁLIDA»; «base rota» 0.
- [x] RM1: medido en `1401935`; desde entonces solo cambian `progress/` y `tasks.md`.
- [x] RM2: base 26,3 s; media 26,2 s × 3 workers = 78,6 s por mutante. Sin salto de orden.
- [x] RM5: el único equivalente es M4 (`"empresa": filtro.por_defecto`). Reproducido: 368
  passed, sobrevive. La equivalencia, comprobada en el código: `_payloads` solo se llama con
  `self._filtro(...)` (`registro_sigrid.py:101,117`), que da a los dos campos el mismo
  `self._por_defecto`. **Falta la aceptación del humano** (observación 1).
- [x] RM6: no se quitó defensa. Lo retirado (`conocidas`, `empresas_de`) es la regla vieja.
- [x] Campaña manual. No es el caso «0 automáticos», pero la valoré igual: cubre los cambios
  de atributo que el operador automático no muta. El texto exacto de las 15 filas está en
  `git show 8349775:scripts/mutantes_manuales_f034.py`. **Reproduje las 15** sobre una copia
  de HEAD, sin `-x` y al pie de la letra: 14 muertas (fallos: M1 9, M2 3, M3 9, M5 9, M6 2,
  M7 7, M8 6, M9 1, M10 65, M11 37, M12 1, M13.1 2, M13.2 1, M13.3 1); M4 sobrevive. El primer
  test que cae es el que cita el informe. **Evidencia suficiente y reproducible.**
  Toda línea con lógica nueva tiene al menos un mutante: `use_cases:70`,
  `registro:47-48,74,87`, `routes:63-65,174,201,221,241`, `schemas:186-187`,
  `empresas:26-27`. `models.py` (campo obligatorio, ya cubierto por el TypeError de
  `test_f034_r10_filtro_…`) y `settings.py` (solo comentario) no tienen lógica que mutar.
- [x] Campaña automática sin supervivientes en `PENDIENTE` · [x] «Evidencias» con los cuatro
  números (los workers, 3, constan en el informe de mutación, no en «Evidencias») ·
  [x] ningún N/A sin motivo.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] T1-T7, T10 y T11 `[x]`, cada una con su commit `F-034 Tn:`. T8 y T9 siguen `[ ]`
porque son MANUAL del líder y del humano: no bloquean el APPROVED, sí el `done`.
· [x] sin temporales (el script se retiró en `1401935`) · [x] features.json coherente.

## Cobertura requisito → test

| Req. | Test |
|---|---|
| R1 | `test_f034_r1_obras_leen_…`, `…_obras_de_la_28_si_…`, `…_obras_siempre_…` (cuadrante), `…_cuadrante_ofrece_…` (HTTP, None/1/18/28) |
| R2 | `test_f034_r2_trabajador_con_empresa_…`, `test_f034_r2_con_empresa_no_lee_…`, `test_f024_r8_…_solo_en_la_suya` |
| R3 | `test_f034_r3_trabajador_null_solo_en_la_por_defecto`, `…_null_con_por_defecto_distinta_de_1`, `…_null_lee_la_por_defecto_…` |
| R4 | `test_f034_r4_filas_y_resumen_…`, `test_f024_r13_*`, `test_f024_r15_export_*`, `test_f024_r6_r13_*` |
| R5 | `test_f034_r5_*` de `test_f034_rutas.py` (cuadrante 1 y 28, guardar 18, deshacer y copiar 28), `…_otra_empresa_no_depende_…` |
| R6 | `test_f034_r6_aviso_de_la_linea_y_title_del_selector`, `test_f024_r12_marcas_…` |
| R7 | `test_f034_r7_lineas_de_los_visibles_…` (18/31/1/None/28), `test_f034_r7_solo_visibles_…` |
| R8 | `test_f034_r8_obra_de_otra_empresa_…`, `test_f024_r17_*` |
| R9 | diff vacío del transfer, su suite (317 passed) y las claves de `test_f034_r1_cuadrante_…` |
| R10 | `test_f034_r10_*` (filtro, registro, rutas), `test_f022_r21_*` (> 0 o no arranca) |
| R11 | tabla R11 de `impl_F-034.md`, contrastada con el diff |
| R12 | `test_f002_fuente_unica.py` en verde + diff de los 4 ficheros revisado |
| R13 | MANUAL T9 (humano), en `current.md` |

## Observaciones para el líder (no bloquean el APPROVED; 1 y 2 sí el `done`)

1. **M4 necesita la aceptación escrita del humano** (en crítico, cero supervivientes salvo
   justificación aceptada). Va a «F-034 · pendiente antes del done» en `current.md`, junto a
   T8 y T9, con la respuesta anotada.
2. **`current.md` se contradice:** la línea 4 dice «Ninguna feature en ejecución» con F-034
   en `in_progress`, y «Lo que el sistema sabe hacer» dice «El transfer sigue en modo
   pruebas» cuando está desplegado en real. No viene de F-034, pero es información falsa que
   parece vigente sobre producción.
3. En `impl_F-034.md` §Mutación, enlazar `git show 8349775:scripts/mutantes_manuales_f034.py`
   como fuente del texto exacto de M1-M13.
4. La anomalía de la campaña (3 supervivientes en la corrida de las 09:15) no se reproduce
   en copia aislada. Si vuelve a pasar, ficha en `arnes-base`.
5. design §10: F-034 escribe en real líneas que hoy se omiten, con el recurso aún sin elegir
   por empresa. El humano decidió desplegarla con F-026: que no se despliegue sola.

## Automejora (propuesta, no aplicada)

- **`harness.mutacion` (`arnes-base`):** formato declarativo para mutantes manuales fuera del
  alcance de producción (p. ej. `progress/mutantes_manuales_F-XXX.json`: fichero, original,
  mutado), ejecutado e informado por la herramienta. Hoy un script en `scripts/` rompe la
  línea base y la evidencia queda solo en el historial.
- **`CHECKPOINTS.md` C4 bis:** aplicar el punto de campaña MANUAL (texto exacto, nº de
  fallos, dos filas reproducidas) también cuando complementa a una automática pequeña, no
  solo cuando sustituye a una de 0 mutantes.
