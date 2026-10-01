<!-- progress/review_F-032.md -->
Revisión completa (pasada 1) · base `56e79f3` .. HEAD `feff7e4` (rama `feature/F-032-empresas-desde-sigrid`, árbol principal, limpio)

# F-032 · Review — Nombres de empresa sincronizados desde Sigrid

**Veredicto: CHANGES_REQUESTED** — solo por el rastro (`progress/current.md`).
El código, los tests y la campaña están bien: con el cambio 1 hecho, la pasada 2
(incremental desde `feff7e4`) puede aprobar sin volver a leer código.

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige C1–C5, C4
con tests trazables, fase RED, cobertura ≥ 80 % de lo cambiado y campaña de
mutación con supervivientes analizados. `sdd: false`: mini-spec = descripción +
`acceptance` (R1–R7); `tasks.md` N/A.

## Verificación ejecutada por el reviewer
- `bash harness/init.sh`: **ENTORNO LISTO**; raíz `355 passed, 1 skipped`;
  `PUERTA COBERTURA 100.0% (106/106)`; `PUERTA TAMAÑO` OK; ruff 193 avisos (deuda previa).
- Suites sin caché (`-p no:cacheprovider`, por el defecto conocido de la caché que
  cruza ramas): api **342 passed**, front **20 passed**, transfer **317 passed**.
- Mutación, recálculo puro: `alcance_de_feature("F-032")` = 11 ficheros, **258
  líneas**; `generar_mutantes` = **30**. Coinciden con el informe. Los 2
  supervivientes existen tal cual (`models.py:92` booleano `frozen=True→False`;
  `orm_models.py:91` booleano `nullable=False→True`).
- **Campaña no reejecutada: 118,2 s según el informe (> 60 s)**; vale recálculo + RM.

## Checkpoints
**C1** [x] init.sh exit 0 · [x] ficheros base presentes.
**C2** [x] una sola `in_progress` (F-032) · [x] rama correcta · [x] `current.md`
de la sesión activa (más las secciones fijas habituales) · [x] `done` con historia.
**C3** [x] hexagonal: `domain/empresas.py` y `models.py` sin imports de infra; regla
«de baja» en dominio (`empresa_de_baja`), aplicada en el repo al mapear y en
`ListarEmpresas`; el front solo pinta `e.de_baja` · [x] primera línea con ruta en
los dos ficheros nuevos · [x] sin `print`, sin secretos, sin dependencias nuevas ·
[x] trampas de dominio: no toca porcentaje, postventa ni escritura a Sigrid
(la consulta de `auxemp` es SELECT sin `;` ni DML, vía `sigrid-api` de lectura).
**C3 bis** N/A — no toca `docs/referencia/`.
**C4** [x] cada `acceptance` R1–R5 con tests `test_f032_rN_*` en verde (tabla
abajo); R6 MANUAL; R7 esta review · [x] sin red ni BBDD (sesión doble, dialecto
PG sin motor, Sigrid falso, `TestClient` con contenedor doble) ·
**[ ] MANUAL en `current.md` con su comando exacto**: ver cambio 1.
**C4 bis**
- [x] rigor declarado (`estandar`).
- [x] RED: trazas reales T1–T7 en `impl_F-032.md` (ImportError/KeyError/TypeError/
  AssertionError previos al código), incluidos R2/R3/R5 centrales (T6) y el front (T7).
- [x] cobertura `[OK]` 100 %.
- [x] mutación: informe de la herramienta, totales verificados (arriba).
- [x] muertos: campaña > 60 s → recálculo puro + RM, dicho aquí.
- [x] coste por mutante = 118,2 × 4 ÷ 20 = 23,6 s (> 1 s).
- [x] sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base medida (18,0–18,1 s).
- [x] RM1: SHA medido `8160220…`; `git diff --stat 8160220..HEAD` solo toca
  `progress/` y `tests/test_f032_empresas_sigrid.py` → alcance de producción idéntico.
- [x] RM2: media 5,9 s × 4 workers = 23,6 s ≥ base 18 s; 20 × 5,9 ≈ 118,2 s. Coherente.
- RM3 (criterio): revisados los 30 mutantes; ninguno es equivalente (p. ej.
  `fecbaj or 1`, `> 1`, `desact == 2`, `and ResultadoSyncMaestro()` cambian
  comportamiento y hay test que lo fija). Ningún equivalente muerto.
- [x] RM5 N/A: nivel `estandar` y no hay supervivientes declarados equivalentes.
- [x] RM6 N/A: el diff de producción no quita ninguna guarda; los 2 supervivientes
  se mataron con tests nuevos (`fe93a43`), sin tocar código.
- [x] campaña manual N/A: la automática dio 30 mutantes.
- [x] supervivientes analizados (ninguno `PENDIENTE`), reproducidos por el implementer en copia.
- [x] «Evidencias» con los cuatro números y workers (4).
- [x] ningún N/A sin motivo.
**C4 ter** N/A — sin `harness/rutas_sensibles.json` señalado por init.sh.
**C5** [x] `tasks.md` N/A (`sdd=false`); 8 commits `F-032 Tn:` + ajustes `F-032:` ·
[x] árbol limpio, sin temporales · [x] `features.json` `in_progress`, acceptance R5
reescrito con la decisión del humano.

## Cobertura acceptance → tests
| R | Tests (api salvo indicación) |
|---|---|
| R1 tabla ORM sin DDL, lectura `auxemp` | `r1_tabla_empresa_declarada_en_el_orm`, `r1_numemp_no_es_autoincremental`, `r1_esquema_la_crea_create_all_y_no_un_alter`, `r1_nulabilidad_…`, `r1_config_lee_auxemp_con_los_alias_exactos`, `r1_config_consulta_de_solo_lectura`, `r1_repo_*` (alta, idempotente, sin numemp, repetido), `r1_pipeline_*`, `r1_el_sync_real_incluye_las_empresas`, `r1_la_respuesta_del_sync_…` |
| R2 nombre de la tabla, cambio llega tras sync | `r2_repo_actualiza_cambios_de_sigrid[×4]`, `r2_nombres_de_la_tabla_y_mismo_conjunto…`, `r2_la_por_defecto_sin_trabajadores…`, `r2_r5_alta_cambio_de_nombre_y_baja_llegan_tras_el_sync`, `r2_r5_get_empresas_expone_nombre_y_baja`, `r2_…_inmutable` |
| R3 sin `empresas.nombres`, «Empresa N» de reserva | `r3_empresa_n_solo_si_no_esta…`, `r3_config_yaml_sin_empresas_nombres`, `r3_el_contenedor_no_lleva_nombres_de_config` |
| R4 preview | `r4_preview_informa…`, `r4_preview_sin_numemp_o_nombre…`, `r4_preview_sin_consulta…`, `r4_el_preview_real_usa_la_consulta_de_config` |
| R5 de baja marcada, nunca oculta | `r5_empresa_de_baja[×9]`, `r5_empresa_de_baja_con_trabajadores_sale_marcada`, `r2_r5_*`; front `test_f032_r5_*` (×2, estáticos) |
| R6 | MANUAL pendiente (no bloquea APPROVED, sí `done`) |

## Puntos pedidos por el líder
- **ORM / upsert / consulta**: `EmpresaORM` (PK `numemp`, `autoincrement=False`) creada
  por `create_all`; `alters_faltantes` no emite nada (test). Upsert por `numemp`,
  idempotente, no borra ausentes, repetido = una alta. SQL con alias exactos
  `numemp, cod, nombre(=res), fecbaj, desact`, contrastados con `auxemp` en
  `azure-apps/sigrid_tablas.md` (l. 1751).
- **Conjunto del selector intacto**: `empresas_activas() | {por_defecto}`, igual que
  F-024; la 39 en tabla sin trabajadores no sale (test). «Empresa N» solo fuera de
  tabla o con nombre vacío.
- **Regla en API/dominio**: sí. `app.js` solo concatena « (de baja)» si `e.de_baja`;
  test estático de que no filtra ni mira `fecbaj`/`desact`.
- **Desviación F-024**: verificada línea a línea. `r1_empresas_ordenadas` conserva
  `[1,18,28]` y `[1,5,18,28]`; `r2_nombre_…` conserva los tres pares; el JSON de
  `r1_r2_get_empresas` conserva números y nombres y solo añade `de_baja: false`.
  Eliminados `r2_config_yaml_trae_los_nombres_de_d1` → sustituto
  `test_f032_r3_config_yaml_sin_empresas_nombres`; `r2_el_contenedor_lleva_los_nombres…`
  → `test_f032_r3_el_contenedor_no_lleva_nombres_de_config`. Nada aflojado. F-023:
  solo dobles, ningún assert tocado.
- **Si falla la lectura de `auxemp`**: el pipeline hace los tres fetch antes de
  cualquier upsert y un único commit, así que un fallo (red o columnas) aborta el
  sync entero: **no se actualizan empleados ni obras**, pero tampoco queda nada a
  medias. **Lo considero aceptable**: es atómico, el sync es manual (el error se ve
  en `POST /sync`), `auxemp` es un catálogo pequeño leído por la misma pasarela que
  ya funciona para `emp`/`obr`, y está documentado en `docs/INTEGRACION.md` («qué se
  rompe»). Un paso tolerante escondería justo el fallo que F-032 quiere evitar. El
  riesgo real (permiso de `sigrid-api` sobre `auxemp`) lo despeja la verificación
  MANUAL antes de desplegar.
- **Sin `.env`**, ni en el diff ni versionado (init.sh). **`azure-apps/` sin tocar**:
  último commit `f6ef278` (F-024, 13:36, anterior a la rama) y árbol limpio.

## Cambios requeridos
1. **`progress/current.md`, sección «Verificación MANUAL (humano) de F-032»**: hoy
   dice «El líder prepara el script», sin comando (C4, tercer punto). Copiar los
   comandos exactos de `progress/impl_F-032.md` §«Verificaciones MANUAL», puntos 1 y
   2: arranque `python main.py` desde `services/dedicacion-api` (rama F-032, para que
   `create_all` cree `empresa`), `GET http://localhost:8090/api/v1/sync/preview`
   (comprobar `empresas.nombres["18"]` y `["31"]`), `POST
   http://localhost:8090/api/v1/sync`, `GET http://localhost:8090/api/v1/empresas` y
   el selector en `http://localhost:8080`, con el resultado esperado de cada uno.
2. **Mismo fichero**: listar como pendiente antes del `done` la actualización de
   `azure-apps/dedicacion.md` (punto 3 de ese mismo apartado del informe: cabecera,
   fila de `sigrid-api`, tabla `empresa`, `de_baja` en `/empresas`, fila `auxemp` en
   «qué se rompe»). La regla de `CLAUDE.md` la hace parte de este trabajo y ahora
   solo consta en el informe del implementer.

## Observaciones no bloqueantes (para recoger, no para dejar «anotado»)
- `filtros_maestros.resumir_empresas` publica `nombre` sin `strip`, mientras el repo
  lo limpia con `_texto`: el preview puede enseñar espacios que la tabla no guarda.
- El literal de la empresa 1 pasa de «Construcciones Ruesma» a «CONSTRUCCIONES
  RUESMA» (el de Sigrid): avisarlo al humano en el resumen de cierre.
- `sync_en` solo se fija al alta (igual que `trabajador`/`obra`): no indica el último sync.

## Propuesta de automejora (no aplicada)
- `CHECKPOINTS.md` C4: añadir «y las actualizaciones pendientes de `azure-apps/`»
  junto a las MANUAL, para que no dependan de que el implementer las mencione.
