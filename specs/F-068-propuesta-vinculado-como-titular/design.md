<!-- specs/F-068-propuesta-vinculado-como-titular/design.md -->
# F-068 · Diseño: la partida del vinculado, como la del trabajador

Evidencia en `progress/explore_F-068.md`; decisiones abiertas en §9. Es una
enmienda de F-044 (`specs/F-044-recursos-vinculados/design.md` §6.2, §6.3,
§7.1): todo lo que aquí no se nombra sigue como allí.

## 1. Servicios y límite

| Servicio | Qué hace en F-068 | Por qué ahí |
|---|---|---|
| `dedicacion-transfer` | La regla nueva (R1-R10), la lectura del historial de los vinculados (R11-R15) y la propuesta guardada con los métodos nuevos (R16) | Ya propone la partida del vinculado con la misma función en selector y preflight (F-044 R9, R29); única pluma contra Sigrid |
| `dedicacion-api` | Guarda las propuestas con los métodos nuevos (R17) y manda la descripción del vinculado (R18) | Guarda lo que devuelve el transfer (F-055); `recurso_vinculado` es suyo |
| `dedicacion-front` | Un rótulo, `capitulo_ci4` (R20) | Solo pinta: el texto del método |

Sin microservicio nuevo ni lógica copiada entre servicios: la api no propone,
el front no calcula. `partes` no se toca. Contra Sigrid, una **lectura** más;
la escritura es la de F-044.

## 2. Encaje

`PasoVinculados._partida` (preflight) y `PasoVinculados.proponer` (selector y
cola) llaman a `partida_del_vinculado` con lecturas perezosas que el
paso construye **una vez por petición** (`_UnaVez`, como hoy las cuentas):

elegida válida → titular (R17) → historial (R2; lee `historial_de_vinculados`
y el presupuesto) → cuenta, nombre y CI.4 (R4-R7; lee `cuentas_del_presupuesto`)
→ sin partida (R9).

La propuesta guardada que vale (R16) se usa antes de la regla, como hoy la
`ci_tipo`. Sin vinculados, o con todos resueltos antes del historial, no se
construye ninguna lectura (R14).

## 3. Ficheros a crear

Tests sin red ni BBDD (dobles de cliente como los de F-044):

- `services/dedicacion-transfer/tests/test_f068_reglas.py` — R1-R10 (puro).
- `services/dedicacion-transfer/tests/test_f068_pipeline.py` — R11-R16,
  suelto, lote y `partidas/propuesta(-lote)`.
- `services/dedicacion-transfer/tests/test_f068_sql.py` — la SQL de §7.
- `services/dedicacion-api/tests/test_f068_api.py` — R17, R18.
- `services/dedicacion-front/tests/test_f068_front.py` — R20.

## 4. Ficheros a modificar

**transfer**
- `application/services/reglas_vinculados.py` — §6.1.
- `application/pipelines/registro_vinculados.py` — §6.2.
- `application/pipelines/registro_pipeline.py` — `_preflight` pasa a
  `paso.decidir` la ventana del historial (`ventana(max periodo,
  propuesta_meses_atras)`, la de `_historial`); `proponer` pasa
  `ventana(ano, mes, …)` a `PasoVinculados.proponer`. Nada más.
- `infrastructure/sigrid/sigrid_write_client.py` — `historial_de_vinculados`
  (§7); el paso de fila a `LineaHistorial` sale a `_linea_historial(f)`, que
  usan los dos historiales. La SQL de `historial_partidas` **no cambia**.
- `application/services/lecturas_lote.py` — `historial_de_vinculados` por
  `_una_vez`, clave `(obra, desde, hasta, recursos)` (R15). Sin precarga: es
  una lectura por obra y solo si hace falta, como `cuentas_del_presupuesto`.
- `domain/models/registro_models.py` — `VinculadoEntrada.descripcion:
  str | None = None`.
- `interface_adapters/api/app.py` — `VinculadoIn.descripcion`;
  `VinculadoPropuestaIn.tipo_res` y `.descripcion` (opcionales).
- `tests/conftest.py` — `ClienteFalso.historial_de_vinculados` (devuelve
  `[]`); y los dobles de `test_pipeline_offline.py` y de los tests de F-044
  que lo necesiten (mismos métodos y firma, F-037).
- Tests de F-044 que fijan el orden viejo (R22): §10.

**api**
- `application/registro_sigrid.py` — `METODOS_PROPUESTA_VINCULADO =
  ("ci_tipo", "titular", "parte_anterior", "auto_nombre", "auto_categoria",
  "capitulo_ci4")`; `_vinculado` añade `descripcion` (R18).
- `domain/models.py` — `SubfilaVinculado.descripcion: str | None = None`.
- `infrastructure/db/repositories.py` — `_a_subfila` la rellena con
  `RecursoVinculadoORM.descripcion` (ya existe: sin cambio de esquema).
- `application/partidas_linea.py` — `peticion_de_subfilas` añade `tipo_res`
  y `descripcion` a cada vinculado.
- `application/propuestas_mes.py` — **sin cambio de código**: ya filtra con
  `es_metodo_de_propuesta_vinculado` (R17); se cubre en `test_f068_api.py`.

**front**: `static/js/app.js` — en `rotuloOrigen`, `capitulo_ci4: "capítulo
CI.4 en empate"`. `htmlPartida` no cambia (pinta cualquier método).

**docs**: `docs/ARCHITECTURE.md#regla-vinculado` (viñetas «Partida» y
«Lecturas»); `docs/INTEGRACION.md` §5 (`descripcion`, `tipo_res` y los
métodos); `specs/F-044-recursos-vinculados/requirements.md` (una línea bajo
R16, ya puesta por esta spec).

## 5. Ficheros que NO se tocan

`propuesta_partida.py` (se **usa** `previa_en_obra`, `_maximo_unico`,
`ventana` y `LineaHistorial`; la propuesta del titular no cambia);
`partida_matcher.py`, `text_match.py`, `partida_catalog.py`,
`cuenta_analitica.py`, `estado_parte.py` (copias cerradas: solo se usan);
`partida_resolver.py`; `reglas_porcentajes.py`; la SQL de
`historial_partidas` y de `cuentas_del_presupuesto`; la decisión de los
titulares en `registro_pipeline.py`; `use_cases.py`, `orm_models.py` y
`schemas.py` de la api (la descripción no sale en el cuadrante:
`SubfilaOut` tiene sus campos); los `.env`; el repositorio `partes`.

## 6. Clases y funciones

### 6.1 transfer · `reglas_vinculados.py` (application, puro)

- Constantes: `METODO_PARTE_ANTERIOR = "parte_anterior"`,
  `METODO_CAPITULO_CI4 = "capitulo_ci4"`; `METODOS_PROPUESTA_PROPIA` = los
  cinco de R16; `MOTIVO_EMPATE_NOMBRE = "empate_nombre"`; `_POR_QUE_SIN_CI`
  gana los textos de R9 («…ni el historial, ni el nombre ni el capítulo CI.4
  deciden»), dentro de los 300 caracteres de `sigrid_motivo`.
- `PartidaElegida` y `PartidaVinculado` ganan `origen: str | None = None`.
- `hojas_con_subcuenta(hojas, cuentas, sub) -> list[PartidaNodo]` — las
  hojas activas con esa subcuenta, en el orden de hoy. `partida_ci_del_tipo`
  se reescribe sobre ella **sin cambiar su contrato** (sus tests siguen).
- `es_capitulo_ci4(cod: str | None) -> bool` — R8, con
  `text_match.normalize_code`.
- `puntuar(candidatas, tipo_res, descripcion, *, solo_casadas) ->
  dict[int, tuple[float, str | None]]` — R5-R6: por candidata,
  `match_partida(tipo_res, descripcion, [n])` (una a una: el casador elige
  «la primera» en empate y aquí el empate se ve); la que no casa, `(0.0,
  None)` o fuera si `solo_casadas`.
- `desempate_ci4(empatadas) -> PartidaNodo | None` — R7: la única con
  `es_capitulo_ci4`; 0 o 2+ ⇒ None.
- `partida_por_cuenta_o_nombre(hojas, cuentas, sub, tipo_res, descripcion)
  -> tuple[PartidaElegida | None, str]` — R4-R9: una con su cuenta ⇒
  `ci_tipo`; varias ⇒ `puntuar(…, solo_casadas=False)`; ninguna ⇒ entre las
  hojas activas `CI*` con `solo_casadas=True`; el máximo único con
  `_maximo_unico` ⇒ el método del casador; empate ⇒ `desempate_ci4`; si no,
  `(None, motivo)` (`varias_ci`, `sin_ci` o `empate_nombre`).
- `partida_por_historial(historial, recurso, obra_ide, hojas) ->
  PartidaElegida | None` — R2-R3: deja las líneas con `par_cod` `CI*` (D2) y
  llama a `previa_en_obra(…, hojas activas)`; con su `origen`.
- `partida_del_vinculado(titular, elegida, elegida_valida, ci, historial=None)`
  — R1: elegida → titular → `historial()` → `ci()` → sin partida. `ci`
  devuelve `(partida, método)` o `(None, motivo)` (como hoy, pero el método
  ya no es siempre `ci_tipo`). `historial=None` es «no hay paso de historial»
  (las llamadas de F-044 en tests siguen valiendo).

### 6.2 transfer · `PasoVinculados` (application)

- `decidir(..., desde: int, hasta: int)`: construye `historial =
  _UnaVez(lambda: cli.historial_de_vinculados(recursos, origen_ide, desde,
  hasta))` con los recursos de **todos** los vinculados de la petición
  (superconjunto: una lectura, R11); `_partida` le pasa a
  `partida_del_vinculado` el paso de historial (`partida_por_historial`
  sobre `historial()` y las hojas activas de `presupuesto()`) y el de cuenta
  y nombre (`partida_por_cuenta_o_nombre` con `v.tipo_res`, `v.descripcion`).
- `_partida`, propuesta guardada (R16): la condición `propuesta_metodo ==
  METODO_CI_TIPO` pasa a `in METODOS_PROPUESTA_PROPIA`; copia método y
  origen guardados.
- `proponer(..., desde: int, hasta: int)`: lo mismo con el presupuesto que
  ya trae; la propuesta lleva `origen` (`asdict(Propuesta(...))`).

## 7. SQL (Sigrid, solo lectura)

`SigridWriteClient.historial_de_vinculados(resides, obra_ide, desde, hasta)
-> list[LineaHistorial]`, lotes de `LOTE_RECURSOS_HISTORIAL`, sin recursos no
lee, `truncated` es excepción (R13). Alias exactos los de
`historial_partidas`:

```sql
SELECT h.reside AS reside, m.obride AS obride, co.cod AS obra_cod, c.cod AS parte_cod,
       m.ano AS ano, m.mes AS mes, h.can AS can, h.paride AS paride, p.cod AS par_cod, p.res AS par_res
FROM hmores h JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide
JOIN con co ON co.ide = m.obride JOIN obrparpar p ON p.ide = h.paride
WHERE h.reside IN (?, …) AND m.obride = ? AND c.tip = ? AND p.obride = m.obride
  AND (m.ano * 100 + m.mes) BETWEEN ? AND ?
```

Diferencias con `historial_partidas`: **sin** `auxhor`/`LIKE 'M%'` (la hora
del vinculado no es `M*`: `OTEL`, `OGAS`, `MESVE`…; explore §2: casi nunca
dos horas suyas en un mes y obra) y **con** `m.obride = ?` (solo la obra de
origen: R2 no mira otras). Volumen: unas pocas filas por vinculado y mes.
PostgreSQL: sin cambios de esquema.

## 8. Contrato (api ↔ transfer)

Entrada, por vinculado: `descripcion?` en registro y en propuesta; `tipo_res?`
en propuesta. Salida: `partida_metodo` y `partida_origen` del vinculado con
los métodos nuevos. Api vieja con transfer nuevo: sin textos, R5-R6 no casan
⇒ como mucho «sin partida» o CI.4 en empate de todas a 0 (nunca una
partida inventada). Api nueva con transfer viejo: campos ignorados. Se
despliega **transfer → api → front**.

## 9. Decisiones abiertas (para el humano)

- **D1 · Qué es «el capítulo CI.4»** (R8). (A) Por número: primer trozo `CI`
  y segundo `4` o `04` (`CI.4.13`, `CI.04.13`; no `CI0.04`, `CI_F1.04`).
  (B) Literal: el código empieza por `CI.4.`. En la 0692 hay `CI.4.x` (casi
  todo hasta 2025-07) y `CI.04.x` (desde 2026-02): con (B) un vinculado sin
  historial iría al capítulo **que se dejó de usar**; con (A) queda «sin
  partida» y se elige. En la 0678 y la 0694 las dos dan lo mismo. **Recomiendo A.**
- **D2 · Historial solo en partidas `CI*`** (R2). (A) Sí: se quitan antes las
  líneas en partidas no `CI*` y se toma el último mes de las que quedan. (B)
  No: el último mes con cualquier partida. Al historial solo se llega con el
  titular en una `CI*` (R17 manda las demás con el titular); con (B), un
  mes en que el titular fue a una `CP*` arrastraría al vinculado a esa `CP*`
  aunque su titular vaya ahora a una `CI*` (explore §1: de 13 a 55 pares
  por tipo). **Recomiendo A.**
- **D3 · Ventana** (R2). (A) La del trabajador: `PROPUESTA_MESES_ATRAS` (24)
  hacia atrás, **con** el periodo que se registra, como su `parte_anterior`
  (si Administración ya metió la línea del mes, se propone esa partida y el
  preflight la ve como pisado, no como línea nueva al lado). (B) Solo meses
  anteriores al periodo, como dice la petición al pie de la letra.
  **Recomiendo A** («como el `parte_anterior` del trabajador»).
- **D4 · Propuestas guardadas antes de F-068** (R19). Las subfilas con
  propuesta `ci_tipo` ya guardada (octubre) la conservan: F-055 escribe lo
  que enseña el cuadrante, y R16 no la recalcula. El historial daría otra en
  pocos casos (explore §1: TF 14, CO 21, VE 3, CAJA 29 pares en dos años).
  (A) Se quedan; el humano las ve y las cambia si quiere. (B) Tras desplegar,
  el humano borra a mano en `asignacion_vinculado` las propuestas sin
  elegida de los periodos abiertos y la cola las recalcula (escritura en la
  BBDD `dedicacion`, comando en la MANUAL). Las que estaban «sin partida»
  (el caso pedido) se recalculan solas: no tienen propuesta guardada y la
  memoria de «sin propuesta» se vacía al reiniciar. **Recomiendo A.**
- **D5 · Alcance del desempate** (R5-R7). (A) Con varias hojas con su cuenta,
  «ninguna casa por nombre» es un empate a 0 y decide el CI.4; sin su
  cuenta, el CI.4 desempata solo entre las que casan. (B) Con varias con su
  cuenta y ninguna que case, «sin partida». En las cinco obras medidas las
  parejas tienen la **misma** descripción: (A) y (B) solo difieren si el
  casador no reconoce esa descripción. **Recomiendo A** («empate ⇒ preferir
  el capítulo CI.4»).

Decididas por el spec-author (técnicas): métodos `parte_anterior`, `ci_tipo`,
`auto_*` (los del trabajador, con sus rótulos) y uno nuevo, `capitulo_ci4`;
la descripción del recurso como «nombre» y la del tipo como «categoría» del
casador; el historial de cualquier hora del vinculado (explore §2).

## 10. Riesgos, relaciones y avisos

- **Tests de F-044 que cambian (R22)**: los de `test_f044_pipeline_vinculados.py`
  y `test_f044_lote.py` cuyo doble llega al paso de cuenta (necesitan
  `historial_de_vinculados`) y los que fijan «varias ⇒ sin partida» o «CI del
  tipo sin mirar historial» (`test_f044_r16_sin_ci_del_tipo_o_varias_…`,
  `test_f044_r9_titular_sin_propuesta_va_a_la_ci_del_tipo`). Se ajustan
  dándoles historial vacío; si alguno cambia de resultado, el informe lo
  dice con el requisito que lo explica. `partida_ci_del_tipo` y sus tests no
  cambian. Mutación: campaña entera (rigor crítico).
- **0692 y 0693**: sin historial, el vinculado nuevo quedará «sin partida»
  (D1-A; fases `CI_F1`/`CI_F2`): es a propósito, nunca la primera.
- **Vehículo de la 0678** (`CI.0.06` / `CI.03P.9`): ninguna es CI.4; sin
  historial, «sin partida». Hoy todos los vehículos de esas obras lo tienen.
- **`can` de cajas**: su hora no es mensual (F-044 D1b: se omiten al
  registrar) pero su subfila se propone igual; sumar su `can` es «la más
  usada» en su unidad.
- **F-054** va después y no se toca aquí; la elegida que F-054 traiga de
  Sigrid manda sobre esta propuesta (R1).
- **azure-apps**: el contrato api ↔ transfer es interno; al desplegar se
  comprueba si `azure-apps/dedicacion.md` lista las lecturas del transfer y,
  si las lista, se añade esta (tasks T14). La lectura nueva filtra por
  recurso, no por prefijo de hora: una `MESVE` no se cuela (F-044 §10).
