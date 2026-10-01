Revisión completa (pasada 1) desde `9ea9a81` (salida de `dev`) hasta `a92cc42` (HEAD)

# F-024 · Review 1 · Selector de empresa, Ruesma por defecto

- **Veredicto:** APPROVED
- **Rama:** `feature/F-024-selector-empresa` (árbol principal, limpio; merge-base con `dev` = `9ea9a81`).
- **Nivel de rigor:** `estandar`, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 % y
  mutación con supervivientes analizados.
- **`bash harness/init.sh`** (tal cual): `ENTORNO LISTO`. 355 passed y 1 skipped; los tres servicios en
  verde; cobertura 100 % (105/105); tamaño dentro de topes; ningún `.env`. Único aviso: ruff 193 (previo).

## Comprobaciones pedidas por el líder

- **Filtro de empresa.** Las ocho rutas del periodo que leen, resumen, copian, exportan o registran
  reciben `empresa: EmpresaQ` → `_filtro` (`routes.py:141-297`). Sin ella quedan `cerrar`/`reabrir`, que
  no leen ni escriben filas, `GET/POST /periodos` y `/sync`. En aplicación el `filtro` es obligatorio en
  los seis casos de uso. `_filas_de_empresa` es el único punto del filtro (cuadrante, `_resumen_periodo`,
  copia del mes) y `RegistroSigrid._payloads` aplica la misma función de dominio. Su consulta añade
  `porcentaje > 0`, pero `ck_asignacion_pct` ya obliga a > 0: la visibilidad es la misma que en el cuadrante.
- **El front, sin lógica.** `conEmpresa()` va en `api()` para toda ruta `/periodos/` y en el export. No
  hay `fetch` directo (grep). Las marcas leen campos de la API (`t.empresa`, `l.otra_empresa`), sin
  `filter` ni comparaciones. La única comprobación, si `?empresa=` está en la lista, la exige R4.
- **Assert anterior cambiado.** Solo uno, el de `test_f022_r10_r11_pipeline_obra_de_otra_empresa_se_omite`
  (design §7). `test_f022_empresa_en_linea.py` solo añade `empresa=None` a los dobles.
- **R21.** `PeticionIn` y `app.py` del transfer no están en el diff. `test_f024_r21_…` compara las claves
  exactas y el 200 con `TestClient`, y su RED se probó en una copia aislada.
- **R20 no abre escrituras.** `obra_destino` pasa a ser una obra real, pero todas las acciones son
  `omitir`, así que `ejecutar` sale por `if not a_escribir: return res` antes de crear parte o línea. Los
  tests lo afirman en los dos modos (`cli.escritos == []`).
- **D4 y D5.** Probados con datos: un trabajador NULL con carga en la 28 sale en la 28; con carga solo
  en obra NULL o sin líneas, en la por defecto; con carga en la 1 y la 28, en las dos. Ana (de la 1, con
  una línea en la 28) lleva todas sus líneas, cuentan en su total y van marcadas `otra_empresa`. Las obras
  NULL no se ofrecen. Al registrar, la línea va con `empresa = 1` y su omisión se traza (R17).
- **Sin red ni BBDD.** UoW y sesiones falsas, `dependency_overrides` y una Sigrid falsa con `escribir`
  prohibido. Ningún `.env` en el diff. `azure-apps/` limpio, último commit ajeno a esta feature.
- **T11, T12 y T13 (MANUAL).** Están en `current.md` con su comando o sus pasos. No bloquean el APPROVED;
  sí el `done`.

## Checkpoints

**C1:** [x] init.sh termina con 0 · [x] están los ficheros base.

**C2:** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md` sobre la sesión activa,
con el backlog y avisos permanentes como en las reviews anteriores · [x] cada `done` en `history.md`.

**C3:**
- [x] Hexagonal: `domain/empresas.py` solo importa `domain.models`. El import del ORM en
  `registro_sigrid.py` es anterior a F-024.
- [x] Primera línea con la ruta.
- [x] Sin prints, TODO nuevos, secretos ni dependencias. Ruff, base frente a HEAD fichero a fichero:
  iguales; los ficheros nuevos, limpios.
- [x] Reglas de dominio: sin conversión de escala nueva, postventa intacta, ninguna escritura nueva en
  Sigrid y modo pruebas intacto.

**C3 bis:** N/A, justificado: no toca `docs/referencia/`.

**C4:**
- [x] Cada requisito tiene su test (tabla abajo) y pasa.
- [x] Sin red ni BBDD.
- [x] Las MANUAL están en `current.md`.

**C4 bis:**
- [x] `rigor` declarado.
- [x] Fase RED con salida real de T1 a T9. T5 en dos pasos, el segundo de comportamiento; T8 en una copia
  aislada.
- [x] Cobertura en `[OK]` al 100 %.
- [x] Mutación verificada de forma independiente. `alcance_de_feature("F-024")`: 11 ficheros y 312
  líneas (`9ea9a81..rama`). `generar_mutantes`: **17** (registro_sigrid 2, use_cases 2, empresas 7,
  models 1, repositories 1, deps 2, routes 2). Coincide con el informe.
- [x] **Campaña no reejecutada: 93,9 s según el informe (> 60 s).** Me quedo en el recálculo puro más RM.
- [x] Coste por mutante: 93,9 × 4 ÷ 17 = 22,1 s (> 1 s).
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; base rota 0; línea base medida.
- [x] RM1: SHA medido `fda620d…`. Después solo cambian `progress/` y `tasks.md`; el alcance recalculado
  sobre HEAD es idéntico.
- [x] RM2: media × W = 5,5 × 4 = 22 s, frente a una base de 18,2-18,7 s; 17 × 5,5 ≈ 93,9 s. Coherente.
- [x] RM3: ningún mutante es equivalente. Todos cambian algo observable (`or`→`and`, `gt=1`,
  `frozen=False`, `is_(False)`).
- N/A RM5, justificado: rigor `estandar` y sin supervivientes.
- [x] RM6: no se quitó ninguna guarda.
- N/A campaña manual, justificado: la automática generó 17.
- [x] Sin supervivientes ni análisis `PENDIENTE`.
- [x] «Evidencias» con los cuatro números y los workers (4).
- [x] Ningún N/A sin motivo.

**C4 ter:** N/A, justificado: no existe `harness/rutas_sensibles.json`.

**C5:**
- [x] T1 a T10 y T14 en `[x]`, con un commit `F-024 Tn:` cada una. T11, T12 y T13 son MANUAL y bloquean
  el `done`.
- [x] Árbol limpio.
- [x] `features.json` coherente.

## Cobertura: requisito → test

| Req | Test(s) |
|---|---|
| R1 | `test_f024_r1_empresas_activas_solo_activos_y_sin_null`, `…_r1_empresas_ordenadas_con_la_por_defecto`, `…_r1_r2_get_empresas` |
| R2 | `…_r2_nombre_de_config_o_empresa_n`, `…_r2_config_yaml_trae_los_nombres_de_d1`, `…_r2_el_contenedor_lleva_los_nombres_de_config` |
| R3-R5 | `test_f024_selector.py` (r3 ×2, r4, r5 ×3; estáticos, apariencia en T13) |
| R6 | `…_r6_sin_empresa_la_por_defecto`, `…_r6_con_empresa_la_elegida`, `…_r6_empresa_invalida_es_422_sin_tocar_nada` (8 rutas × 4 valores) |
| R7 / R9 | `…_r7_cuadrante_solo_trabajadores_visibles` / `…_r9_obras_solo_de_la_empresa_y_nunca_las_null` |
| R8 | `test_f024_visibilidad.py` (r8 ×6) |
| R10 | `…_r10_fila_con_todas_sus_lineas_y_total_sobre_todas`, `…_r10_la_regla_no_quita_lineas`, `…_r10_puede_deshacer_se_conserva` |
| R11 | `…_r11_linea_de_otra_empresa`, `…_r11_a_linea_mapea…`, `…_r11_empresa_del_trabajador_y_de_cada_linea`, `…_r11_otra_empresa_depende_de_la_elegida` |
| R12 | `test_f024_r12_marcas_sin_empresa_y_otra_empresa` |
| R13 | `…_r13_resumen_del_cuadrante_solo_visibles`, `…_r13_resumen_de_las_respuestas_por_fila`, `…_r6_r13_…` |
| R14 / R15 | `…_r14_copiar_mes_*` ×2, `…_r6_r14_…` / `…_r15_export_filtrado_y_con_la_empresa_en_el_nombre` |
| R16-R19 | `test_f024_registro_empresa.py` (preflight y ejecutar), `…_r6_r18_registro_recibe_la_empresa_por_query` |
| R20 / R21 | `test_f024_r20_*` ×3 y el assert de F-022 / `test_f024_r21_contrato_igual_en_el_corte_por_otra_empresa` |
| R22 | diff revisado de `ARCHITECTURE.md#regla-empresa`, `INTEGRACION.md` (§3, §5, §9, cabecera), `settings.py`, `.env.example`; `azure-apps`, en T11 |

## Desviaciones del implementer, validadas

1. **T3-T5 sin cablear hasta T6:** es el orden de `tasks.md`; desde `89b61a2` todo está en verde.
2. **Assert de F-022:** el único, y es el que declara design §7.
3. **`INTEGRACION.md` sin SHA de origen:** correcto, el merge aún no existe. Fijarlo al cerrar.
4. **`StarletteDeprecationWarning`:** viene de la librería; no es un fallo.

## Observaciones no bloqueantes (recógelas, no las dejes en «anotado»)

- **O1.** Guardar, deshacer y copiar trabajador no comprueban que el trabajador sea visible en E. Es
  coherente con design §4.2 y §10 y el front no lo provoca, pero que conste si la API se abre a más
  clientes.
- **O2.** Con `?empresa=99` (no ofrecida), el front usa la por defecto pero deja 99 en la URL. R4 no pide
  reescribirla; es cosmético.
- **O3.** `cerrar` y `reabrir` reciben `?empresa=` del front y lo ignoran sin validarlo. Es inocuo y R6 no
  los incluye.
- **O4.** El cambio del transfer (R20) y `schemas.py` no generan mutantes. Lo sostienen la RED de T7, los
  tests de R20 en los dos modos y el assert de R20 dentro del test de contrato.

## Cambios requeridos

Ninguno.

## Automejora (propuesta, no aplicada)

Hoy C4 bis solo pide la prueba de control cuando la campaña entera da 0 mutantes. Propongo añadir: «si
un fichero del alcance con lógica nueva da 0 mutantes, el reviewer comprueba que la fase RED cubre ese
cambio». En F-024 se cumple (O4), pero hoy nada obliga a mirarlo.
