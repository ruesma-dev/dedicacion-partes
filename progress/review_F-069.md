<!-- progress/review_F-069.md -->
Revisión completa (pasada 2), principal, sobre `3f9b5ff` (`git diff 5381243...HEAD`, 67 ficheros; delta de la pasada 2, `ed7c212..3f9b5ff`, leído entero).

# F-069 · Review 2 (principal)

**Veredicto: CAMBIOS REQUERIDOS (CHANGES_REQUESTED), solo de papeleo.** El código queda aprobado en
`3f9b5ff`: los cambios 1-7 de la review 1 están resueltos, D17-D21 implementadas, RED de lo nuevo
con trazas reales y D20 escribe solo donde debe. Lo que bloquea: el design §6.5 describe un paso 10
que no es el construido (decisión 8) y `current.md` dice seis cosas falsas hoy. La review 3 puede ser
incremental desde `3f9b5ff` y limitarse a esos ficheros, si no se toca código.

**Review 1 (resumen):** CAMBIOS REQUERIDOS sobre `ed7c212`: el front mandaba todas las casillas y
«Revisado» en una revisaba las demás (D11); faltaba la RED de R15, R8 y R32; `MARCA_PRUEBAS` copiada
en la api; T16 incompleta; R30 sin test; `current.md` falso en 5 sitios; spec frente a lo construido.

**Rigor:** `critico` (`features.json`): RED en los centrales, cobertura ≥ 90 %, mutación con 0
supervivientes en la muestra (uno por línea, 60 %, [100, 300]) y MANUAL con su comando. Mutación y
RM1-RM7: **pendiente: pasada de evidencias** (T13/T18). Capa e2e N/A (ningún servicio la declara).

## Cambios 1-7 de la review 1

| Cambio | Estado | Dónde |
|---|---|---|
| 1 (D11, `PUT` con todas) | resuelto | `app.js` `cuerpoImportes` filtra por `guardada`/`revisado`; api `_validar` conserva `copiado` (D18); tests `r12_d18_dos_copiadas…`, `r4_d18_revisado_en_una_solo_quita_esa`, `r4_d18_solo_el_comentario_no_revisa_ninguna` |
| 2 (RED R15, R8, R32) | resuelto | `impl_F-069.md` T25: ≥ 1 failed por ruptura, descartadas |
| 3 (`MARCA_PRUEBAS`) | resuelto por D17 | `grep PRUEBA-PORC\|MARCA_PRUEBAS` en `domain`, `application`, `infrastructure`, `interface_adapters` de la api: 0 aciertos; el transfer usa `st.marca_pruebas` (`comentario_de_tex`) |
| 4 (T16) | resuelto | `tasks.md` T16 y `current.md` l. 84-91 |
| 5 (R30) | resuelto | `test_f069_r30_la_traza_de_una_caja_conserva…`, con RED |
| 6 (`current.md`) | resuelto (los 5) | pero hay otros seis: cambio 2 abajo |
| 7 (spec) | resuelto | R32 y §6.4 con D21; §4 con el puerto real |

## D17-D21 frente a la spec enmendada

- **D17** [x] `existentes` publica `tex` y `vinculados_registrados` con `comentario_de_tex(tex,
  st.marca_pruebas)`; la api, `comentario_de_sigrid(tex)` sin marca. RED T19/T21.
- **D18** [x] `copiado` solo cae si la cantidad cambia o `revisado: true`; `validar_revisado` (422).
- **D19** [x] `importe_vinculado.cantidad` nulable; fila con solo comentario; copia sin `copiado`.
- **D20** [x] ver la sección siguiente. **D21** [x] evento `IMPORTES` para las del mes.

## D20 con lupa (el `UPDATE hmores SET tex`)

Comprobado en `texto_linea.py`, `registro_pipeline.py` (`_decision_tex`, `_actualizar_tex`,
`_tex_sigue_valiendo`), `registro_vinculados.py` y `sigrid_write_client.py` (`stmt_editar_tex`, `_guarda`):

- **Solo nuestras:** tres capas. Preflight (`tex_a_actualizar`: `synckey` empieza por `porcentajes:`),
  relectura (`_tex_sigue_valiendo`) y SQL (`synckey = ?` la leída, que ya empieza por `porcentajes:`).
- **Parte activo:** preflight (`hit.parte_est`), relectura (`ls.parte_est`) y SQL (`EXISTS … c.est = ?`).
- **Recurso y hora:** `reside = ?` y `a.cod LIKE 'M%'` (titular) o `a.cod = ?` (vinculado); sin enlaces.
- **Pruebas, solo la 0404:** `obride` = `pf.obra_destino.ide`, que en pruebas es siempre la obra de
  pruebas de la empresa (`_obra_destino`); preflight y `AND obride = ?`. Una obra sin `ide` da 0 y no casa.
- **Ni `DELETE` ni otras columnas:** `UPDATE hmores SET tex = ? WHERE …`; orden de parámetros
  correcto (`[tex] + guarda + [obride]`). Test `r26_stmt_editar_tex` con la SQL real.
- **Sin comentarios, nada cambia:** `con_tex` solo si `hay_comentarios`; `r24_…la_sql_de_hoy`.
- `ejecutar` no va en lote (F-055 D6): la memoria de `LecturasDelLote` no puede servir una relectura vieja.

**Decisión 8 (relectura y lote propios al final): aceptable.** El caso principal de D20 (solo cambia el
comentario) no tiene nada más que escribir y `ejecutar` sale antes del paso 9 bis por los dos `return`
de «nada que escribir»; los dos pasan ahora por `_actualizar_tex`. Ir al final, tras titulares y
vinculados, sigue el precedente de `EscrituraVinculados` (lote propio) y la comprobación al releer el
de `_comprobar_escrito`. Coste: solo con algo que actualizar, **dos** lecturas (relectura y
comprobación) y una escritura más; el informe dice «una lectura más» (impreciso). Riesgo, el mismo que
F-044: si ese lote falla tras escribir los titulares, `ejecutar` devuelve error y el reintento los ve
`ya_registrado`. **La spec sí tiene que recogerlo** (cambio 1): §6.5 dice «la relectura
`lineas_para_editar` de siempre (sin otras piezas, esa sola)» y «en el mismo lote».

## Checkpoints

- **C1** [x] `ARNES_SIN_CACHE=1 bash harness/init.sh` entero (pie). [x] Ficheros del arnés.
- **C2** [x] Una sola activa (F-069 `in_review`), rama, orden, history. [ ] `current.md` con seis
  afirmaciones falsas hoy (cambio 2).
- **C3** [x] Hexagonal: `texto_linea.py` puro en `application/services`; `domain/importes.py` sin
  infraestructura. [x] Ruta en la 1.ª línea de los nuevos; sin `print`/`TODO`/secretos.
  [x] Límite de servicio: la marca vive solo en el transfer (D17). [x] Front sin lógica de negocio:
  `revisado` lo decide el usuario, el `copiado` lo decide la api; la marca del front solo pinta.
  [x] Solo escribe el transfer, con guarda, sin `DELETE`.
- **C3 bis** N/A: no toca `docs/referencia/`. **C3 ter** [x] D17-D21 con cita y fecha (design §9.2,
  `#regla-vinculado`). [ ] design §6.5 frente a lo construido (cambio 1).
- **C3 quater** pendiente de T17 al desplegar, listado con contenido en `current.md` l. 92.
- **C4** [x] R1-R36 con test o MANUAL (tabla). [x] Sin red ni BBDD. [x] MANUAL T16 y T17 con comando
  y resultado esperado (`tasks.md`, `current.md` l. 84-92). [x] Dobles: `lineas_registradas(con_tex)`,
  `stmt_editar_tex`, `lineas_para_editar` y `lineas_por_synckey_del_periodo` existen en el cliente
  real con la misma firma (cruzado a mano).
- **C4 bis** [x] Nivel declarado. [x] RED de lo nuevo (T19-T25 y T9/R30, salidas reales en el
  informe). [x] Cobertura `[OK]` (pie). [x] «Evidencias» con sus números (mutación pendiente).
  Mutación y RM1-RM7: pendiente: pasada de evidencias.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] Un commit por tarea `F-069 Tn:`; T13, T16-T18 abiertas, legítimas en esta fase.

## Cobertura (requisito → test)

| R | Test |
|---|---|
| R1, R2, R5 | `test_f069_importes_dominio.py` (y `validar_revisado`) |
| R3-R10, R15, R16, R30 | `test_f069_importes_api.py` (`r3`… `r16`, `r4_d18_*`, `r4_d19_*`, `r8_d19_*`, `r30_*`) |
| R11-R14, R29 | `test_f069_importes_front.py` (`r12_d18_*`, `r12_d19_*`, `r29` con `tex_nuevo`) |
| R17-R22, R24 | `test_f069_reglas_importe.py` |
| R23, R25-R28 | `test_f069_pipeline_importe.py`, `test_f069_tex_registrada.py` (D20, R27 suelto = lote) |
| R31, R32 | `test_f069_existentes_tex.py` (`r31`), `test_f069_traer_comentarios.py` (`r32_*`) |
| R33, R34 | `ARCHITECTURE.md` `#regla-vinculado` y `#regla-traer-sigrid`; `INTEGRACION.md` §1, §5, §7 |
| R35, R36 | MANUAL T16 y T17 (pendientes) |

## Cambios requeridos

1. **Design §6.5, «Paso 10», y §7.1 frente a la decisión 8.** Sustituir el texto del paso 10 por lo
   construido: «al final de `ejecutar` (`_actualizar_tex`), tras titulares y vinculados y también si
   no hay nada más que escribir: relectura propia `lineas_para_editar` de esas líneas, `stmt_editar_tex`
   en un lote propio y una lectura más de comprobación (`lineas_registradas(con_tex=True)`); solo con
   alguna `tex_nuevo`». Y en §7.1, esa lectura de comprobación. Design está en 249/250: sustitución,
   no añadido. Corregir también en `impl_F-069.md` la decisión 8 («una lectura más» ⇒ dos).
2. **`current.md`, falso hoy** (leído entero, líneas reales; son todas):
   - l. 19: hotfix `propuestas-subfilas`, «Pendiente del humano: desplegar SOLO la api»: desplegada
     el 2026-11-11 (`r20261111-1915`, l. 10).
   - l. 29: hotfix `vinculados-incluye-vp`, «Pendiente del humano: despliegue SOLO de la api»: la misma
     api; queda, si acaso, «Sincronizar Sigrid».
   - l. 59: «`arnes-base` va 3 commits por delante de su `origin/main`»: hoy va 1 (`8de97cb`).
   - l. 256: «Producción, hoy» acaba en F-068 (2026-10-28) y no tiene el despliegue del 2026-11-11
     (api `r20261111-1915`, front `r20261111-1916`): la api y el front que enseña no son los de hoy.
   - l. 491: «Orden: **F-058**…, F-044, F-052, F-053, **F-054**…»: F-044 y F-054 están `done`.
   - l. 578: «F-062: T19 y T20, MANUAL, con sus comandos exactos en «F-062 · T19 y T20» (arriba)»:
     las dos están HECHAS (`progress/manual_F-062.md`) y esa sección ya no existe.

## Observaciones (no bloquean; el líder las recoge)

- **O1** El paso de D20 en `current.md` l. 88 y T16 no dicen qué mirar si `tex_actualizadas` sale
  vacío (guarda que no deja): el log `[registro] la guarda no dejo cambiar el tex`. Útil en la MANUAL.
- **O2** `comentario_de_tex` quita la marca también sin espacio detrás («PRUEBA-PORCx» ⇒ «x»). Solo
  afecta a un `tex` escrito a mano así; menor.
- **O3** Tras este APPROVED de código, la campaña (T13) debe incluir `texto_linea.py` y
  `_actualizar_tex`/`_tex_sigue_valiendo`: son las guardas que protegen D20 (RM6 si alguien las quita).

## Automejora (propuesta para `reviewer.md`)

Al releer `current.md` entero, contrastar cada «Pendiente del humano: desplegar…» con «Producción,
hoy» y con las entradas de despliegue posteriores: en la review 1 se me pasaron tres de las seis.

## Resultado de `ARNES_SIN_CACHE=1 bash harness/init.sh` (2026-11-19, `3f9b5ff`, sin pipes)

Código de salida **0**, ningún `[KO]`. Suites sin caché, todas en verde: raíz 2319 passed / 47 skipped
(612,5 s); api 1632 passed; front 573 passed; transfer 1956 passed. `[OK]` PUERTA COBERTURA 99,6 %
(687/690), TAMAÑO (review 1, 139/140; este, 140/140 con `harness.tamano`, código 0), CARRIL y E2E N/A.
