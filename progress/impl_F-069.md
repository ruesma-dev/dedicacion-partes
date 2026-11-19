<!-- progress/impl_F-069.md -->
# F-069 · Informe del implementer (`critico`)

Rama `feature/F-069-importe-caja-km` (copia `porcentajes-f069`) sobre `dev`
`5381243`; spec `specs/F-069-importe-caja-km/` aprobada el 2026-11-12. 2026-11-19.

## Qué cambió

Los vinculados de tipo `CAJA`, `VIAJE` y `VP` dejan de omitirse «sin importe
mensual»: tienen una **cantidad** tecleada y un **comentario**, y llegan a
Sigrid.
- **Por %** (km y viaje): una cantidad del mes por vinculado, tabla nueva
  `importe_vinculado`. El transfer la reparte con el % del titular; en km
  multiplica por `precio_km` 0,20.
- **Por obra** (caja): una cantidad por cada línea, en `asignacion_vinculado`,
  entera a su obra (`can` 1).
- **Comentarios**: cada línea del titular y cada vinculado de cantidad tienen
  el suyo. Viaja como `tex`, con `PRUEBA-PORC` delante en modo pruebas, y al
  sincronizar vuelve de Sigrid sin la marca.
- **Copiar el mes** marca las cantidades como `copiado`: no se registran hasta
  que alguien pulsa «Revisado» o teclea otra.

Sin tipos de cantidad ni comentarios, el payload y las respuestas son los de
hoy. Las claves nuevas solo salen con valor; hay tests en el transfer (R24) y
en la api (R16).

## Commits (uno por tarea)

`eca0f8f` in_progress · `59583d4` T1 · `be4dc10` T2 · `a308d4c` T3+T4 ·
`4069ed3` T14 · `6f4c753` T5 · `adebb98` T6 · `9c27ce2` T7 · `5529256` T8 ·
`47a1f82` T9 · `7924b42` T15 · `917f392` T10+T11 · `de6de26` T12 ·
informe en commit propio. Diff contra `dev`: 59 ficheros, +4522 / −122.

## Ficheros principales

- **Transfer:** `registro_models.py`; `reglas_vinculados.py`
  (`precio_del_vinculado` y motivos); `texto_linea.py` (`tex_de`);
  `registro_pipeline.py`, `registro_vinculados.py`;
  `porcentajes_existentes.py`; `sigrid_write_client.py` (una lectura más,
  parametrizada, de las `porcentajes:vin:`); `prueba_escritura_porcentajes.py`
  (marca como prefijo).
- **Api:** `domain/importes.py` (nuevo), `models.py`, `ports.py`, `errors.py`
  (`ImporteInvalido` → 422); `config.yaml` (`importes`, `precio_km`),
  `sync_pipeline.py`; `orm_models.py`, `repositories.py`
  (`PgImporteRepository`, `guardar_subfila_importe`, `poner_comentario`,
  `registradas`); `use_cases.py` (`GuardarImportes`, deshacer `IMPORTES`,
  `_copiar_importes`); `registro_sigrid.py`, `traer_sigrid.py`,
  `transfer_client.py`; `schemas.py`, `routes.py`
  (`PUT /periodos/{a}/{m}/trabajadores/{ide}/importes`), `deps.py`.
- **Front:** `app.js` (`chipImporte`, `importesDeFila`, `cantidadTecleada`,
  `cuerpoImportes`, `fotoImportes`, columna «Comentario»,
  `htmlCantidadVinculado`, `textoImporteVinculado`, comentario en
  `chipEditable`, PUT de importes en `guardarAhora`); `styles.css`.
- **Docs:** `ARCHITECTURE.md` («Cantidad y comentario» en `#regla-vinculado`
  con cita y fecha, `#regla-deshacer`, `#regla-traer-sigrid`);
  `INTEGRACION.md` §5 (contrato y esquema) y §7 (dos filas).
- **Tests nuevos:** transfer `test_f069_reglas_importe.py`,
  `test_f069_pipeline_importe.py`, `test_f069_existentes_tex.py`; api
  `test_f069_importes_dominio.py`, `test_f069_importes_api.py`,
  `test_f069_traer_comentarios.py`; front `test_f069_importes_front.py`.
- **Tests adaptados** (con comentario F-069): fakes y listas cerradas de
  esquema, claves y columnas de F-003, F-024, F-044, F-050, F-054 y F-055.

## Decisiones de diseño y desviaciones (justificadas)

1. **Firma de `tex_de(comentario, marca)`.** Es más simple que la del design.
   Quien llama ya sabe si está en modo pruebas y le pasa la marca o `None`.
2. **`obra` entra en `decidir_vinculados`.** Hace falta para el motivo «falta
   la caja del mes» con la obra (D13-A).
3. **Las casillas por % salen de las subfilas.** Un trabajador sin líneas no
   tiene casillas: sin %, no hay nada que repartir.
4. **Una cantidad `null` en un vinculado por % borra la fila**, comentario
   incluido. En uno por obra, la cantidad se pone a `null` y el comentario se
   conserva.
5. **Caja y comentarios se escriben con upserts dirigidos**
   (`guardar_subfila_importe`, `poner_comentario`), no con `reemplazar`. Así se
   conserva la traza de ya registrada de la línea (F-054); `reemplazar` la
   habría perdido.
6. **Desviación del design.** Al traer de Sigrid, el comentario de una cantidad
   del mes (vinculado por %) va en su propio evento `IMPORTES`, no en el
   `SIGRID`. Motivo: deshacer `SIGRID` restaura las líneas y no la tabla
   `importe_vinculado`, y deshacer `IMPORTES` sí. Los de titular y caja van en
   el `SIGRID`, como pide la spec.
7. **Riesgo: `MARCA_PRUEBAS` («PRUEBA-PORC») está duplicada** como constante en
   `dedicacion-api/domain/importes.py`. Refleja la de los settings del
   transfer. Consta en `INTEGRACION.md` §7. Si se quiere evitar, el transfer
   podría devolver el `tex` ya sin la marca; propongo decidirlo en la review.
8. **En modo pruebas no vuelve el comentario del titular.** `existentes`
   excluye las líneas de titular en modo pruebas (lo hace F-054), así que ese
   comentario no se trae de vuelta. El de los vinculados sí funciona. Afecta al
   último paso de la MANUAL T16, que prueba el km y sí debería funcionar.
9. **`_tipos(contenedor)` en `routes.py` usa `getattr` con un valor por
   defecto.** Los contenedores falsos de tests anteriores no tienen `importes`.
10. **En el front, un texto que no es número se manda tal cual.** La api lo
    rechaza con 422 y sale el aviso de siempre: el front no valida reglas de
    negocio.

## Fase RED (trazas reales)

**T1-T2, transfer.**
- Comando: `.venv/Scripts/python -m pytest tests/test_f069_reglas_importe.py -q`
- Una primera pasada dio 23 fallos. La traza que se guardó es la de dos tests
  del reparto por obra (selección `-k`, sin el código):
  ```
  E       TypeError: decidir_vinculados() got an unexpected keyword argument 'obra'
  E       TypeError: decidir_vinculados() got an unexpected keyword argument 'obra'
  2 failed, 23 deselected in 1.63s
  ```

**T3, transfer.**
- Comando: `.venv/Scripts/python -m pytest tests/test_f069_pipeline_importe.py -q -k r23`
- Sin el código, el pipeline todavía no llevaba el comentario:
  ```
  E       AssertionError: assert None == 'mes con visita'
  E       AssertionError: assert 'PRUEBA-PORC' == 'PRUEBA-PORC mes con visita'
  E       AssertionError: assert None == 'nuevo'
  E       AssertionError: assert (5201, None, 0.4, 20.0) == (5201, 'km de...s', 0.4, 20.0)
  FAILED tests/test_f069_pipeline_importe.py::test_f069_r23_modo_real_el_tex_es_el_comentario
  FAILED tests/test_f069_pipeline_importe.py::test_f069_r23_modo_pruebas_marca_y_comentario
  FAILED tests/test_f069_pipeline_importe.py::test_f069_r23_al_editar_sin_comentario_conserva_y_con_el_lo_pone
  FAILED tests/test_f069_pipeline_importe.py::test_f069_r23_el_vinculado_al_editar_su_linea_al_cero
  4 failed, 2 passed, 8 deselected, 1 warning in 3.86s
  ```

**T14, transfer.**
- Comando: `.venv/Scripts/python -m pytest tests/test_f069_existentes_tex.py -q`
- Antes del código, error de colección: `ImportError` al importar
  `LineaVinculadoSigrid` (de `domain.models.registro_models`) y
  `PREFIJO_VINCULADOS` (de `porcentajes_existentes`).

**T5, api.**
- Comando: `.venv/Scripts/python -m pytest tests/test_f069_importes_dominio.py -q`
- Antes del código:
  ```
  ImportError: cannot import name 'ImporteInvalido' from 'domain.errors'
  ```

**Sin traza RED: T6-T11 y T15.**
- Esos tests se escribieron justo después del código, en la misma tarea.
- Los requisitos centrales de la feature (el reparto, el importe, el `tex` y la
  lectura de Sigrid) son T2, T3, T5 y T14, y esos sí tienen RED.
- El reviewer puede tratar T6-T11 y T15 como sin fase RED. La mutación de la
  pasada de campaña es la defensa que queda para ellos.

## Salida de `bash harness/init.sh` (2026-11-19, rama F-069, tras T12)

Ejecutado tal cual, con la salida a fichero. Código de salida **0**, ningún
`[KO]`.

```
[AVISO] BACKLOG.md regenerado desde features.json: inclúyelo en el commit
[AVISO] ruff: 396 avisos (deuda previa, no bloquea).
2319 passed, 47 skipped in 949.43s (0:15:49)      # raíz
1618 passed, 1 warning in 123.06s (0:02:03)       # dedicacion-api
568 passed, 19 warnings in 130.99s (0:02:10)      # dedicacion-front
[OK] PUERTA COBERTURA: 99.7% de 580 líneas cambiadas cubiertas (578/580, umbral 90% (del nivel critico), nivel critico; diff desde 538124397f, merge-base con dev)
[OK] PUERTA TAMAÑO: F-069 dentro de los topes (requirements 148/150, design 241/250)
[OK] PUERTA CARRIL: N/A (F-069 es de nivel critico: no declara límites)
[OK] CAPA E2E: N/A (ningún servicio declara el bloque e2e)
```

## Verificaciones por tarea (resultado real)

- Transfer 1933 passed tras T14 (en `init.sh`, dentro de la raíz); api 1618;
  front 568, 9 de ellos de `test_f069_importes_front.py`.
- **T12:** `test_f002_fuente_unica.py` da 86 passed. El grep de
  `importe_vinculado|importe_mensual|precio_km` da 4 aciertos en
  `ARCHITECTURE.md` y 5 en `INTEGRACION.md`.

## Pendiente (fuera de mi alcance)

- **T13 / T18 (mutación, `critico`).**
  - Ni la campaña ni T18 están hechas: T18 exige la mutación completa y la
    dejo sin marcar `[x]`.
  - La campaña es para la pasada de campaña: tras el APPROVED, el líder me
    relanza y ejecuto `python -m harness.mutacion --feature F-069`, que deja
    `progress/mutacion_F-069.md` con el análisis de cada superviviente.
- **T16, MANUAL (humano o líder). Escribe en la obra 0404 de pruebas; no la he
  ejecutado.**
  - Antes:
    - transfer, api y front de esta rama con `OBRA_PRUEBAS_FORZAR=true`
    - `curl -s http://127.0.0.1:8006/health` ⇒ `modo_pruebas: true` y `0404`
    - `transfer_base_url` de la api ⇒ `http://127.0.0.1:8006`
  - Lectura previa: `cd services/dedicacion-transfer && .venv/Scripts/python prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`
  - Pasos: los de `tasks.md` T16, en 2026-11.
  - Resultado esperado:
    - km: «100 km × 0,20 €/km», con 12,00 € y 8,00 € de 20,00 €
    - caja: 80 € solo en la primera obra
    - `tex`: «PRUEBA-PORC visita a proveedor»
    - registrar dos veces ⇒ «ya registrada»
    - copiar a 2026-12 ⇒ omitido hasta «Revisado»
    - el comentario vuelve al sincronizar (ver la decisión 8: el del titular
      no vuelve en modo pruebas)
  - Limpieza: `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --ano 2026 --mes 11 --confirmar`, y lo mismo con `--mes 12`.
  - Resultado en `progress/manual_F-069.md`.
- **T17, al desplegar (humano).**
  - Orden: **transfer → api → front**.
  - Después, `azure-apps/dedicacion.md`, desde `docs/INTEGRACION.md` §5 y §7:
    - tabla y columnas nuevas
    - `PUT …/importes`
    - claves del contrato
    - `tex`
    - lectura de F-054 ampliada
  - Va en un commit aparte en `azure-apps`, con `pull --rebase` antes.
  - En `progress/current.md`, el aviso a `partes` y el apunte para F-071.
- **Documento del ecosistema:** la feature cruza la frontera y `CLAUDE.md`
  declara `azure-apps`, pero la spec lo deja en T17: no lo he tocado.
  `BACKLOG.md`, regenerado por `init.sh`, va en el commit del informe.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz 2319 passed / 47 skipped · api 1618 passed · front 568 passed; 0 failed |
| Cobertura de líneas cambiadas | **99,7 %** (578/580; umbral 90 %, `critico`) |
| Mutantes generados / supervivientes | **PENDIENTE de la pasada de campaña**: la lanza el líder tras el APPROVED (`python -m harness.mutacion --feature F-069`) |
| Tiempo de la suite | raíz 949,43 s · api 123,06 s · front 130,99 s |
| Capa e2e | `CAPA E2E: N/A` (ningún servicio declara el bloque e2e) |
