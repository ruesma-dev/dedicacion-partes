<!-- progress/review_F-026.md -->
Revisión completa desde `5a02ddb` (pasada 1) hasta HEAD `e91874a`

# F-026 · Review: el trabajador es el recurso

**Veredicto: CHANGES_REQUESTED.** Código, tests, documentos y script de vaciado
están bien. Falla un solo punto, de evidencia: de los 6 supervivientes que se
declaran «equivalentes», 5 no lo son (RM5, cambio 1). El arreglo es pequeño y
no toca producción.

**Rigor: `critico`** (declarado). Exige fase RED, cobertura ≥ 80 %, mutación con
cero supervivientes salvo justificación aceptada por el humano y MANUAL con
comando exacto.

## Verificación propia (resultados reales)

- Rama correcta, árbol limpio. `bash harness/init.sh`: **ENTORNO LISTO**. Raíz
  `374 passed, 1 skipped`, `PUERTA COBERTURA 100.0% (92/92)`, `PUERTA TAMAÑO`
  en verde. Los servicios salieron de caché; relanzados sin ella: api `440
  passed`, transfer `329 passed`, front `21 passed`.
- **Tabla §3 de tests cambiados, fila a fila contra el diff.**
  - Todo cambio de assert está declarado y sale del requisito que cita.
  - Nada se afloja. Los 12 retirados de F-023 (`r9`-`r11`, `r14`) los
    sustituyen `test_f026_r3_*` y `r4_*`. El `excluidos_otra_empresa == 0` de
    `r16` lo cubre `r6_*`. `r5` queda más estricto (`fullmatch` y sin `fecbaj`).
  - Los dobles del transfer solo renombran `empleado_ide` a `recurso_ide`
    (10→200, 11→300, 12→400); ningún assert cambia.
  - Detalle: `r4` busca `JOIN dbo.con AS rcon…`, que también casaría con un
    `LEFT JOIN`. El `INNER` lo fija `test_f026_r1_parte_de_res_y_filtra_personas`.
- **Mutación, recálculo propio** (`harness.alcance` y `generar_mutantes`).
  - 14 ficheros, **262 líneas y 56 mutantes**, como el informe. Los 6
    supervivientes existen con el mismo operador y el mismo texto.
  - La base `5f498cb` se diferencia de `5a02ddb` solo en spec y rastro.
  - **Campaña no reejecutada: 506,4 s según el informe**, por encima de 60 s.
  - RM1: SHA `5bea52e`; después solo cambian `progress/` y `tasks.md`. RM2:
    base 11,5 s, media 9,0 s, 56 × 9,0 ≈ 504 s, 1 worker. RM3: ninguno de
    los 50 muertos es equivalente.
  - RM5: superviviente nº 1 reproducido en una copia (`git archive`, scratchpad):
    `329 passed`. **Sobrevive pero NO es equivalente**: deja dos líneas con
    `registro_id` 900002 y, con él, la misma synckey.

## Comprobaciones pedidas por el líder: todas correctas

- **Sync desde recursos**: `FROM dbo.res JOIN dbo.con rcon`, `WHERE res.cla = 1`,
  `LEFT JOIN dbo.emp … res.conide > 0`. La ficha solo da el DNI. Sin dedupes ni
  filtro de empresa. Un `dni` NULL entra (`r2`), así que Eusebio y los nueve
  entrarían (lo confirma la T14).
- **Clave por el ORM**: `trabajador.ide` = `res.ide`. Solo se añade
  `fecha_baja` (nulable, sin default), que deriva `esquema.py` (`r8`). Sin DDL,
  sin columnas puente ni convivencia. Las claves `emp.ide` viejas se desactivan
  sin tocar `asignacion` ni `evento` (`r9`).
- **Vigencia por mes**: `vigencia.vigente_en` es la única regla. La usan
  `listar_para_periodo` (cuadrante, resumen, copia y export, este vía
  `ObtenerCuadrante`) y `_payloads`. Los no vigentes van a `no_vigentes`, sin
  mandarse ni trazarse.
- **Contrato**: la línea lleva `recurso_ide = t.ide`, sin `empleado_ide`. Fuera
  `recursos_de_empleados`; en el transfer no queda `res.conide`.
- **Orden de despliegue**: ninguno escribe en un recurso equivocado. API
  nueva y transfer viejo: este respeta el `recurso_ide` dado. Transfer nuevo y
  API vieja: todo «sin recurso». Sin vaciar: el `emp.ide` no tiene `reshor` y
  P1 lo omite; tras el sync pasa a `no_vigentes`.
- **Vaciado `.ps1`**: sin `-Confirmar`, `return` antes de cualquier `az` o
  `psql`. Una sola `TRUNCATE … CONTINUE IDENTITY` con `-d $PG_DB`
  (`"dedicacion"`); nada de `obra`, `empresa` ni del servidor. Contraseña por
  `Read-Host -AsSecureString`; BOM, CRLF, ASCII y sin identificadores.
- **F-034 y F-025 intactas** (ni `empresas.py` ni postventa). Tests sin red
  ni BBDD, ningún `.env`, `azure-apps/` sin tocar.
- **MANUAL** T14-T16 y despliegue en `current.md` con comando y resultado
  esperado. Bloquean el `done`, no esta review.

## Checkpoints

- C1 `[x]`. C2 `[x]`: una sola `in_progress` y la rama correcta (F-034 sigue
  `blocked` por su T9, que va con F-026).
- C3 `[x]`: hexagonal, ruta en la primera línea, sin prints ni secretos;
  escala `/100`, postventa y escritura solo en el transfer, intactas.
- C3 bis `N/A`: no entra ningún documento de fuera.
- C4 `[x]`: trazabilidad completa (tabla abajo), sin red ni BBDD, MANUAL listadas.
- C4 bis:
  - `[x]` rigor, fase RED con salida real (T1-T9, T11, T13; T1 y T2 vistas en
    `6b53a65`), cobertura, recálculo, regla de 60 s, coste por mutante, sin
    «CAMPAÑA NO VÁLIDA», RM1-RM3 y Evidencias con workers.
  - **`[ ]` RM5**: la muestra contradice el «equivalente».
  - **`[ ]` supervivientes en `critico`**: la premisa es falsa en 5 de 6 y
    falta la aceptación del humano.
  - `N/A` RM6: no se quitó ninguna guarda; el muerto nuevo lo mata un test añadido.
  - `N/A` campaña manual: la automática dio 56 mutantes.
- C4 ter `N/A`: no existe `harness/rutas_sensibles.json`. C5 `[x]`: T0-T13 y
  T17 con su commit `F-026 Tn`; T14-T16 son MANUAL; árbol limpio.

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1-R3 | `test_f026_r1_*` (6), f023 `r4`/`r5`, `r2_recurso_sin_ficha…`, `r3_*` (3) |
| R4-R6 | `r4_*` (7), `r17_preview_publica_posible…`, `r5_sync…`/`r5_preview…` (×3), `r6_*` (2) |
| R7-R9 | `r7_alta…`, `r8_*` (4), `r9_fila_que_no_llega…` |
| R10, R11 | `tests/test_f026_vaciado.py` |
| R12-R15 | `r12_*` (5+3), `r13_*` (8), `r14_*` (9 casos), `r15_*` (6) |
| R16-R18 | `test_f026_registro_recurso.py` (`r16_*` ×5, `r18_*`), `r17_*` (5) |
| R19-R22 | `transfer/tests/test_f026_recurso_dado.py` + suites f002/f022 |
| R23 | `test_f002_fuente_unica` (`ANCLAS` con `regla-recurso`), `r10_el_readme…` |
| R24, R25 | MANUAL T14 y T15 |

## Cambios requeridos

1. **`progress/mutacion_F-026.md`, supervivientes 1-6**
   (`prueba_escritura_porcentajes.py:47/50/53`). Que la suite pase con el
   mutante demuestra que sobrevive, no que sea equivalente:
   - Nº 1 y 3 (`900001→900002`, `900002→900003`) duplican el `registro_id`, y
     con él la synckey, de otra línea.
   - Nº 2, 4 y 6 (`recurso_ide 0→1`) quitan el centinela que omite «sin
     recurso» las líneas sin editar.
   - Solo el nº 5 (`900003→900004`) es equivalente de verdad.

   Elige una vía:
   - **(a) Preferida.** Un test del transfer (p. ej.
     `test_f026_r20_lineas_de_ejemplo_sin_editar_no_escriben`): `registro_id`
     únicos en `LINEAS_PRUEBA` y todo `recurso_ide` de ejemplo a 0, omitido
     por `MOTIVO_SIN_RECURSO`. Es una propiedad de seguridad de un script que
     escribe en Sigrid y mata 5 de los 6. Después, relanzar la campaña
     (`--workers 1`).
   - **(b)** Reescribir los análisis 1-4 y 6 como «NO equivalente, sin test
     a propósito», con la diferencia exacta citada arriba.

   Lo que quede vivo necesita **aceptación escrita del humano** antes del
   `done`. La recoge el líder en `current.md`, como M4 en F-034.

## Observaciones (no bloquean; el líder las recoge o las descarta por escrito)

- Falsos supervivientes en paralelo (§7 del implementer): confirmados y es la
  tercera vez (F-022, F-034, F-026). El encargo a `arnes-base` ya no es
  «si se repite».
- `ruff` `I001` en 4 ficheros tocados (deuda de estilo). En
  `infra/README_dedicacion.md` §3 bis, «sus líneas llevarían un `emp.ide`»
  solo vale antes del sync: después van a `no_vigentes`.

**Automejora (propuesta):** en RM5 (`CHECKPOINTS.md` y `reviewer.md`), «que la
suite pase con el mutante demuestra que sobrevive, no que sea equivalente; la
demostración enseña que no cambia nada observable». Vale para `arnes-base`.
