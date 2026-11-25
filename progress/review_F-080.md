<!-- progress/review_F-080.md -->
Revisión completa (pasada 1)

# F-080 · Review principal (`critico`; habrá pasada de evidencias por la mutación exigida)

**Veredicto: APPROVED** sobre HEAD `bb5798d` (diff `dev...HEAD`, merge-base `c5f768e`). Sus puntos de mutación quedan
«pendiente: pasada de evidencias». Las observaciones O1-O4 se recogen antes de esa pasada: si no, vuelven como bloqueo.

## Nivel de rigor

`critico`, declarado en `features.json` (no aplica el defecto), por el disparador 1: cambia el importe de caja que el
transfer escribe en Sigrid. Exige: fase RED, cobertura ≥ 90 % de lo cambiado, mutación exigida (uno por línea, 60 % de
los candidatos en [100, 300], 0 supervivientes sin aceptación escrita del humano) y MANUAL con comando exacto. E2e,
informativa. `harness/rigor.local.json` no existe y el diff no lo toca.

## Lo verificado por mí (no copiado del informe)

- **`ARNES_SIN_CACHE=1 bash harness/init.sh`**, sin pipes: código 0, `ENTORNO LISTO`, ningún `[KO]` ni suite servida
  de caché. Raíz `2319 passed, 47 skipped` (956 s); api `1713`; front `614`; transfer `2021`. `PUERTA COBERTURA [OK]
  100.0% … (13/13, umbral 90% (del nivel critico)…)`; `TAMAÑO` OK (impl 217/220); `CARRIL` y `CAPA E2E` N/A; ruff 439
  (deuda previa).
- **Cobertura real.** Alcance recalculado con `harness.alcance.alcance_de_feature('F-080', 'dev')`: `use_cases.py`
  (l. 35, 482-489, 520, 551-556, 578-579, 1198-1228) y `routes.py` (l. 267, 514-515). Sus 13 ejecutables (486, 488,
  554, 556, 578, 1198, 1216, 1220-1222, 1225; 267, 514) están en `executed_lines` del `coverage.json` de este
  `init.sh` (12:38), ninguna en `missing_lines`.
- **RED de T1, reproducida** en una copia `git archive` de HEAD en mi scratchpad con `CAJA: {…, reparto: obra}`:
  `-k "f080_r1_ or f080_r2_ or f080_r4_ or f080_r5_"` da `8 failed, 1 passed`. Son los mismos 8 y las mismas causas
  (`KeyError: 30`, `DID NOT RAISE`, `'obra' != 'pct'`), y pasa `r1_el_reparto_obra_sigue_siendo_valido`.
- **Lista cerrada (requirements §5), medida de nuevo.** HEAD con los dos tests de §5 en su versión de `dev`: la api da
  **`2 failed, 1706 passed`**, exactamente `test_f069_r15_el_contenedor_pasa_tipos_y_precio` y
  `test_f069_r1_config_versionada`. Excluí los dos `punta_a_punta`, que no cargan fuera del árbol real. Las 16
  `test_f069_r26_*` (R10) no cambian.
- **RED de T4.** Con `use_cases.py`/`routes.py` de `dev` salen los 7 `TypeError` del informe, pero ese rojo **es solo
  de firma**. Lo completé rompiendo el comportamiento sobre HEAD, en la copia, y la suite cae siempre. Con la guarda
  apagada o el comentario del resto conservado, caen 3 (`r11_el_resto…` ×2, `r11_sin_propuesta_por_tipo`); con
  `CopiarPeriodoAnterior()` sin tipos en la ruta, `r11_las_rutas…`; con `CopiarTrabajadorAnterior` ignorando `tipos`,
  `r11_el_resto…[trabajador]`. Los tests vigilan R11, no solo la firma.
- **T2 y T3: ruptura deliberada reproducida** (no hay RED de código: es el de F-069, como prevé tasks.md). Con
  `reparto="obra"` fallan **10 de 10** en el transfer (`can` 1.0, «falta la caja… en la obra 0678») y **3 de 3** en el
  front (casilla por obra, «falta importe», «180,00 € · caja de esta obra»).
- **Diagnóstico de design §2, contrastado en el código.** Todo decide por `reparto` y nada mira el nombre `CAJA`: en la
  api, `importes_del_mes`, `GuardarImportes._validar`, `_cantidad_al_transfer`, `_sumar_vinculados`,
  `schemas._cantidad_out` y `traer_sigrid` l. 310; en el transfer, `precio_del_vinculado`; en el front, `app.js`
  l. 1288, 1325, 1841 y 1856. La capacidad por recurso vinculado (`registro_vinculados` l. 430) mejora con `can` < 1.
- **Árbol:** `git status` limpio; lo roto, solo en `scratchpad/red/`.

## Checkpoints

**C1** [x] `init.sh` sin caché, código 0. [x] Los ficheros base existen.

**C2** [x] Una sola activa (F-080, `in_review`). [x] Orden: `todo` prioridad 1; nada `blocked` ni `human_review`.
[x] Rama `feature/F-080-caja-por-trabajador`. [x] `current.md` l. 4 describe la sesión activa (restos internos en O1).
[x] `features.json` coherente; F-077 recortada (D7).

**C3** [x] Hexagonal: solo `application/` e `interface_adapters/`, que importan `domain.importes`. [x] Primera línea
con la ruta en los 3 tests nuevos y en los tocados. [x] Sin `print`, TODO, secretos ni dependencias nuevas; type hints
en las firmas; ruff (config raíz) limpio en los tests nuevos. [x] Trampas del dominio:
- **escala:** sin conversión nueva; `can` = el del titular (0,6) y `tot = round(can × pre, 2)`;
- **postventa:** con el destino y la partida del titular (`r6_…_postventa`, `va_con_el_titular`);
- **escritura:** ninguna nueva, y el transfer no se toca.

**C3 bis:** N/A, no se toca `docs/referencia/`.

**C3 ter** [x] Las citas del humano llevan fecha y origen («f80 ok», «d1 y d2 ignoralo…», la petición del 2026-11-25),
en design §13, `ARCHITECTURE.md` y `config.yaml`. «Decidido (a)» de D3-D5 y D7 es el OK a la spec con esas
recomendaciones, y así lo dice current.md l. 4, separado de la cita. Matiz en O4.

**C3 quater** (la spec, §12, dice «Sí» en lo que se escribe): **pendiente de T8**, del líder al desplegar y en commit
aparte, listada en `current.md` («⚠», entrada F-080), como en F-069. Se exige con su SHA en `impl_F-080.md` antes del
cierre.

**C4** [x] Cada requisito tiene su test (tabla abajo), en verde. [x] Sin red ni BBDD (dobles de F-069, `node` sobre
`app.js`; R12 solo lee dos ficheros). [x] M1, M3 y M4 están en `current.md` («⚠»), con sus pasos y
`infra/d.local.ps1 api`, que existe y admite `api`; los matices de M1 van en O2. [x] Dobles: ningún método nuevo;
`_Espia` hereda de la clase real con su misma firma `__init__(self, tipos=None)`.

**C4 bis**
- [x] Nivel declarado. [x] Fase RED: trazas de T1, T4 y T5 y ruptura en copia de T2 y T3, todas reproducidas (arriba).
  [x] Cobertura `[OK]` 100 % (13/13), contrastada con `coverage.json`.
- **Pendiente: pasada de evidencias:** totales de `mutacion_F-080.md` (recálculo con `harness.alcance` y
  `generar_mutantes`; reejecución si < 60 s), coste por mutante, «⚠ CAMPAÑA NO VÁLIDA», RM1, RM2, RM5, RM6, campaña
  manual, supervivientes y su análisis, PODADO y las filas de mutación y workers de «Evidencias».
- RM7: N/A. Ningún requisito central protege un orden entre colaboradores: R11 transforma subfilas, sin colaboradores.
- [x] «Evidencias» trae tests, cobertura, tiempos y capa e2e. Lo de mutación, «sin medir todavía», es lo que toca aquí.
- Capa e2e: N/A, `CAPA E2E: N/A` (ni servicios con e2e ni requisitos `(capa: e2e)`). [x] Ningún N/A sin motivo.

**C4 ter:** N/A, no existe `harness/rutas_sensibles.json`.

**C5** [x] T1-T6 y T11 en `[x]`, con un commit `F-080 Tn:` cada una. T7, T9 y T10 son las MANUAL M3, M1 y M4, y T8 es
`azure-apps`, del líder al desplegar: no las puede cerrar ningún agente y constan en `current.md`. [x] Sin temporales.
[x] `features.json` dice `in_review`.

## Trazabilidad requisito → test (prefijo `test_f080_`)

| R | Test(s) |
|---|---|
| R1 | api `r1_config_caja_en_euros_por_pct`, `r1_el_reparto_obra_sigue_siendo_valido`; `test_f069_r1_config_versionada` |
| R2 | api `r2_la_caja_una_vez_por_trabajador_en_importes` (con resto), `r2_sin_caja_del_mes_sale_la_casilla_vacia` |
| R3 | front `r3_una_casilla_de_caja_por_trabajador_…`, `r3_la_subfila_ensena_la_caja_del_mes_o_falta_importe` |
| R4 | api `r4_la_caja_se_guarda_como_caja_del_mes` ×2 (con y sin `obra_ide`), `r4_dos_de_la_misma_caja_es_422_repetido` |
| R5 | api `r5_cada_linea_lleva_la_caja_del_mes_por_pct` (una lectura), `r5_sin_caja_del_mes_va_nula_…` |
| R6-R8 | transfer `r6_*` ×3 (postventa, VAR, `can` sin normalizar), `r7_*` ×2, `r8_*` ×5 |
| R9 | front `r9_el_modal_ensena_la_caja_como_los_km` |
| R10 | las 16 `test_f069_r26_*` del transfer, sin cambios |
| R11 | api `r11_el_resto_…` ×2, `r11_un_tipo_por_obra_y_sin_tipos_como_hoy` ×2, `r11_sin_propuesta_por_tipo`, `r11_las_rutas_…` ×2 |
| R12 | api `r12_la_doc_dice_caja_por_pct_y_sin_restos`, `r12_el_comentario_de_la_config_tambien` |
| R13-R15 | MANUAL M1 (T9), M3 (T7) y M4 (T10); `azure-apps` (T8, C3 quater pendiente) |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean ahora; la pasada de evidencias comprueba que se recogieron)

- **O1 · `current.md`, restos desfasados de esta misma sesión.**
  - L. 5 se titula «Implementer … en curso:» y acaba en «terminado».
  - L. 6 pone como pendiente recortar F-077 (D7), que ya está hecho (`fb5b767`) y que l. 4 da por hecho.
  - Lo que sigue vivo de l. 6, la nota en F-071 de que la caja ya no tiene `can` 1 (design §11), no está en la entrada
    F-080 de «⚠», adonde manda l. 4: hacerla en la descripción de F-071 o listarla allí.
  - A l. 4 le falta el paso siguiente: la campaña de mutación **exigida** y el reviewer de evidencias.
- **O2 · M1.**
  - tasks.md T9 dice «MANUAL (humano)» y current.md, «líder»: alinearlos.
  - El cuadrante no expone la traza de la subfila, así que M1 no ve una caja por obra **registrada y luego vaciada**,
    el caso que D3 dice que contaría caja dos veces. Propuesta: sumar una lectura por `sigrid-api` de las líneas `CO`
    con `synckey` `porcentajes:vin:%` desde el 2026-11-21, con 0 esperado, o la confirmación del humano.
  - Poner la URL base y el criterio de recuento: subfilas `tipo: "CAJA"` con la clave `cantidad`.
- **O3 · `impl_F-080.md`.** «20 items» en `test_f080_caja_api.py`; `--collect-only` da 18. Va a 217/220: resumir.
- **O4 · C3 ter.** «…una por trabajador…» corrige erratas del original («una pro trabjador»): marcarlo o citar literal.
- **O5 · Fuera de alcance a propósito (design §5, D1 a).** Docstrings que aún ponen la caja como ejemplo de «por obra»,
  para la limpieza D1 b: api `domain/importes.py` l. 2-10, `orm_models.py` l. 401/416 y `schemas.py` l. 43; transfer
  `reglas_vinculados.py` l. 381.
- **Para la pasada de evidencias (RM6).** La guarda `if tipos else None` de `_subfila_copiada` no es decorativa:
  `tipo_de(…, None)` lanza `AttributeError`, y `tipos=None` es el defecto de ~20 tests de copia anteriores. No se mata
  un mutante quitándola.

## Automejora (propuesta para `arnes-base`, no aplicada)

`CHECKPOINTS.md` C4 bis, fase RED: un rojo que solo es de firma (`TypeError` de argumentos, `ImportError`) no demuestra
que el test vigile el comportamiento. Exigir junto a él una ruptura semántica en copia (la guarda apagada, el cableado
quitado) con su traza. En F-080 la hice yo; nada obligaba a hacerla.
