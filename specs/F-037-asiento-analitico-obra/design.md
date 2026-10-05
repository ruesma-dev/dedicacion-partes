<!-- specs/F-037-asiento-analitico-obra/design.md -->
# F-037 · Diseño técnico

Diseñado para **D1 = A** (requirements §6): el transfer rellena
`hmores.caaide`; el asiento analítico (ANA) lo sigue generando Administración.
Si D1 sale B o C, este diseño no vale y se rehace. Evidencia y cifras:
`progress/explore_F-037.md`.

## 1. Encaje en la arquitectura y límite de servicio

- **Solo `dedicacion-transfer`**: es la única pluma sobre Sigrid
  (`ARCHITECTURE.md` § «la única pluma») y ya resuelve la obra destino, su
  centro (`obr.cenide`) y los tipos de hora del recurso (`reshor`). La cuenta
  analítica es una columna más de la línea que ya escribe.
- **No es un microservicio nuevo** ni una responsabilidad nueva: no se
  escriben asientos (R11). Generar o regenerar ANA es de Administración.
- `dedicacion-api` y `dedicacion-front` **no se tocan**: los campos nuevos
  (`AccionLinea.caaide`, `AccionLinea.cuenta_analitica`,
  `ParteDestino.contabilizado`, `escritas[].cuenta_analitica`) viajan
  dentro de listas que la api reenvía sin esquema, y el front ya pinta
  `AccionLinea.aviso` (`app.js`, tabla del preflight). Las claves de primer
  nivel de las respuestas no cambian (`test_f024_r21`).
- Capas: la regla de la cuenta es **application/services** (pura, sin E/S),
  la lectura es **infrastructure/sigrid**, la orquestación el **pipeline**.
- Fuera de este monorepo: `partes-persistencia` tiene el mismo hueco (sus
  líneas `partes:` van con `caaide = 0`). Se avisa al humano; no se toca.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/application/services/cuenta_analitica.py` | Regla pura de #regla-analitica (§5.1) |
| `services/dedicacion-transfer/tests/test_f037_cuenta_analitica.py` | R2-R5 sobre las funciones puras |
| `services/dedicacion-transfer/tests/test_f037_pipeline.py` | R1, R3 (pruebas/postventa), R5-R7, R9-R13 con `ClienteFalso` |
| `services/dedicacion-transfer/tests/test_f037_cliente_sigrid.py` | R1, R7, R8, R11 sobre `SigridWriteClient` con `_read`/HTTP sustituidos |

## 3. Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-transfer/domain/models/registro_models.py` | `HoraRecurso.hoja_analitica: Optional[str] = None` (5.º campo, con defecto: los `HoraRecurso(...)` posicionales de los tests siguen valiendo); `AccionLinea.caaide: int = 0` y `AccionLinea.cuenta_analitica: Optional[str] = None`; `ParteDestino.contabilizado: bool = False`; constante de dominio `ESTADO_PARTE_CONTABILIZADO = 10`; docstring del módulo remite a `#regla-analitica` |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | `_read` falla si `truncated` (R7); `horas_de_recursos` con la hoja (§6.1); método nuevo `cuentas_de_centro` (§6.2); `partes_existentes` lee `con.est` y rellena `contabilizado` (§6.3); `stmt_insert_linea(..., caaide: int = 0)` con `caaide` como parámetro `?` en vez del literal 0; docstring de cabecera sin «caaide=0» ni «pendiente de confirmar» |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | Paso 6 ter (§7); `ejecutar` pasa `caaide` al insert y añade `cuenta_analitica` a `escritas`; docstring de pasos |
| `services/dedicacion-transfer/tests/conftest.py` | Solo el doble (§9.2) |
| `services/dedicacion-transfer/tests/test_pipeline_offline.py` | Solo el doble (§9.2) |
| `services/dedicacion-transfer/tests/test_f002_fuente_unica.py` | `"regla-analitica"` en `ANCLAS` (§9.2) |
| `docs/ARCHITECTURE.md` | Punto 16 `#regla-analitica`; lista de anclas de la cabecera de la sección; frase de `#regla-sin-partida` (R15); fila de `sigrid-api`/transfer en «Acceso a datos» con las lecturas nuevas |
| `docs/INTEGRACION.md` | Fecha y origen; §1 fila de `sigrid-api` (lecturas del transfer: `caa`, `con.est` del parte); §7 «Si tocan algo de otros»: filas de `caa`/`reshor.caaide`/`auxhor.caacod` y de «Contabiliza parte…» (`con.est = 10`) de Administración |
| `azure-apps/dedicacion.md` (otro repo) | Copia literal de las piezas de `INTEGRACION.md` (T12; commit en `azure-apps` lo hace el humano) |

## 4. Ficheros que NO se tocan

- `application/services/reglas_porcentajes.py`: P1-P5, identidad, capacidad
  y sin partida no cambian. `decidir` sigue eligiendo la hora; la hoja la
  busca el pipeline en `horas` por `hora_ide` (§7). `sin_partida` mira
  `paride`, no el aviso, así que componer avisos no lo altera.
- `partida_resolver.py`, `partida_catalog.py`, `partida_matcher.py`,
  `text_match.py`, `universo_postventa.py`: la cuenta **no** sale de la
  partida (explore §3: en postventa las partidas no tienen cuenta).
- `interface_adapters/api/app.py`: serializa con `asdict`; los campos nuevos
  salen solos. `prueba_escritura_porcentajes.py`: `inspeccionar` ya enseña
  `caaide` y `limpiar` borra por `PRUEBA-PORC`, que basta para R18.
- `services/dedicacion-api/**`, `services/dedicacion-front/**`, `infra/**`.
- `synckey_de`, `PREFIJO_SYNCKEY` y el bloqueo `MAX(ide)+1`.

## 5. Clases y funciones

### 5.1 `application/services/cuenta_analitica.py` (application, pura)

```python
def hoja_de_codigo(cod: str | None) -> str | None
    # Tras el primer '.', sin espacios, mayúsculas; sin punto, el código
    # entero; vacío o None -> None.  '00000.CIMO02'->'CIMO02', 'CIMO05'->'CIMO05'
def hoja_analitica(caa_reshor: str | None, caa_tipo: str | None) -> str | None
    # R2: la de reshor si la hay; si no, la del tipo de hora.
def indice_cuentas(filas: Iterable[dict]) -> dict[str, list[tuple[int, str]]]
    # filas {ide, cod} de un centro -> hoja -> [(ide, cod)], en el orden dado.
def resolver_cuenta(indice: dict | None, hoja: str | None, *, obra_cod: str
                    ) -> tuple[int, str | None, str | None]
    # R3/R4 -> (caaide, cod, aviso). indice None = obra sin centro.
    # Exactamente una -> (ide, cod, None); 0 o >1 -> (0, None, aviso).
def componer_aviso(actual: str | None, nuevo: str | None) -> str | None
    # R5: une con ' · ' sin perder el anterior; None si no hay ninguno.
```

Textos (constantes del módulo, cada uno cabe en los 300 caracteres de
`sigrid_motivo`): `AVISO_SIN_HOJA`, `AVISO_SIN_CENTRO`, `AVISO_SIN_CUENTA`
(`{obra}`, `{hoja}`), `AVISO_CUENTA_AMBIGUA` (`{obra}`, `{hoja}`, `{n}`) y
`AVISO_PARTE_CONTABILIZADO` (`{parte}`). Todos dicen qué pasa: «se escribe
sin cuenta analítica: no entrará en el asiento analítico del parte» o «el
parte {parte} ya está contabilizado: la línea no entrará en su asiento
analítico hasta que Administración lo regenere».

### 5.2 `SigridWriteClient` (infrastructure)

- `horas_de_recursos(resides) -> dict[int, list[HoraRecurso]]`: misma firma;
  cada `HoraRecurso` con `hoja_analitica = hoja_analitica(caa_reshor,
  caa_tipo)`.
- `cuentas_de_centro(cenide: int) -> list[dict]`: filas `{ide, cod}`.
- `partes_existentes(obra_ide, periodos)`: misma firma; cada `ParteDestino`
  existente con `contabilizado = (est == ESTADO_PARTE_CONTABILIZADO)`.
- `stmt_insert_linea(..., paride: int = 0, caaide: int = 0) -> dict`.

## 6. SQL (en el cliente del transfer, parametrizado, base `ruesma`)

El transfer no tiene YAML de consultas: sus SQL viven en
`sigrid_write_client.py`, como hoy. **Ninguna contiene la cadena `conide`**
(`test_f026_r19` lo vigila en toda lectura).

1. `horas_de_recursos`: la de hoy más `kr.cod AS caa_reshor, auxhor.caacod AS
   caa_tipo` y `LEFT JOIN con kr ON kr.ide = reshor.caaide` (`caaide = 0` no
   casa: `NULL`).
2. `cuentas_de_centro`: `SELECT caa.ide AS ide, con.cod AS cod FROM caa JOIN
   con ON con.ide = caa.ide WHERE caa.cenide = ? ORDER BY caa.ide` (~270
   filas por obra; `max_rows` 2000).
3. `partes_existentes`: la de hoy más `con.est AS est` (misma lectura, R10).
   El 10 es el estado que deja «Contabiliza parte…»: 502 de 502 partes con
   ANA desde 2025 y ninguno sin él (explore §9).
4. `INSERT INTO hmores`: igual que hoy salvo `caaide = ?`.

## 7. Flujo en el pipeline

- **R9-R10** no añaden paso: `contabilizado` llega con el parte (paso 5).
  Un parte nuevo nunca lo está.
- **Paso 6 ter (R1-R7)**, tras la idempotencia y antes de los conflictos, por
  cada acción `escribir`: `d = obra_de(a)`; `cenide = getattr(d, "cenide",
  0)`; índice del centro desde una caché local de la petición (una lectura
  por `cenide > 0`; `None` si 0); hoja = la de la `HoraRecurso` de
  `horas[a.recurso_ide]` con `horide == a.hora_ide`; `a.caaide,
  a.cuenta_analitica, aviso = resolver_cuenta(...)`; `a.aviso =
  componer_aviso(a.aviso, aviso)`; y si su parte está `contabilizado`,
  `componer_aviso` con `AVISO_PARTE_CONTABILIZADO`.
- `obra_de(a)` ya da la obra de pruebas en modo pruebas y la de postventa en
  postventa (o la de pruebas si ambas): R3 sale sin ramas nuevas.
- **`ejecutar`**: `stmt_insert_linea(..., caaide=int(a.caaide or 0))`;
  `escritas[]` con `cuenta_analitica`. Borrados de pisado: sin cambios (R13).
- Las acciones `omitir` y `ya_registrado` no reciben cuenta ni aviso (R12).

## 8. Contrato HTTP (aditivo)

`acciones[]`: `caaide` (int, 0 sin cuenta) y `cuenta_analitica` (str|null).
`partes[]`: `contabilizado` (bool). `escritas[]` (ejecutar):
`cuenta_analitica`. Nada se quita ni se renombra; `PeticionIn` no cambia.

## 9. Tests

### 9.1 Nuevos (sin red ni BBDD; nombres `test_f037_rN_*`)

- `test_f037_cuenta_analitica.py`: R2 (`reshor` manda; sin `reshor`, el tipo;
  `00000.CIMO02`, `CIMO05`, ` cimo03 `, vacío y `None`); R3 (una cuenta);
  R4 (sin hoja, sin centro, sin cuenta, dos cuentas -> 0 y aviso con causa,
  nunca la primera); R5 (`componer_aviso` con y sin aviso previo).
- `test_f037_cliente_sigrid.py`: R1/R8 (`stmt_insert_linea` con `caaide`
  lleva el valor en la posición de la columna `caaide`, `cenide` el de la
  obra y la SQL no nombra `cuaide`); R7 (`_read` con `truncated: true` lanza;
  `horas_de_recursos` rellena `hoja_analitica` desde las dos columnas);
  R10 (`partes_existentes` lee `con.est` en la misma consulta; 10 ->
  `contabilizado`, 1 y 3 -> no);
  R11 (ninguna SQL de `stmts_crear_parte`, `stmt_insert_linea`,
  `stmt_borrar_linea` nombra `asi`, `asa`, `apu`, `apa`; el `con` insertado
  lleva `tip` del parte).
- `test_f037_pipeline.py`: R1 (insert con el `caaide` de la cuenta); R3 en
  modo normal, postventa y pruebas (el centro leído es el de la obra
  destino); R4/R5 (sin cuenta: se escribe con 0, aviso, sin conflicto; con
  «sin partida» los dos textos); R6 (`acciones` y `escritas`); R7 (dos
  líneas del mismo centro: una lectura de cuentas); R9/R10 (parte contabilizado:
  aviso, sin conflicto; parte nuevo o sin contabilizar: sin aviso);
  R12 (`ya_registrado` sin insert ni cuenta); R13 (pisado confirmado: el
  insert nuevo lleva su `caaide`, el borrado es el de siempre).
- R14-R16: `test_f002_fuente_unica.py` con la ancla nueva, y revisión del
  `git diff` de los dos documentos (reviewer).

### 9.2 Tests anteriores que cambian (lista cerrada)

1. `tests/conftest.py`, **solo el doble y sus datos**: `cenide` en las cuatro
   obras de `ClienteFalso`; hoja en `HoraRecurso` de MENC (`CIMO03`) y MJEFO
   (`CIMO02`); método `cuentas_de_centro` (devuelve esas dos hojas para
   cualquier `cenide > 0`, contando lecturas). `partes_existentes` no cambia:
   su `ParteDestino` ya trae `contabilizado = False`. Ningún
   assert cambia: así ninguna acción de los tests anteriores gana un aviso
   (`test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe`
   compara el aviso entero).
2. `tests/test_pipeline_offline.py`: `cuentas_de_centro` en su `ClienteFalso`.
   Ningún assert cambia.
3. `tests/test_f002_fuente_unica.py`: `"regla-analitica"` en `ANCLAS`.

Los demás (`test_f022`, `test_f024`, `test_f025`, `test_f026`, `test_f013`,
`test_f002_*`) deben pasar **sin tocarlos**; los dobles que heredan de
`ClienteFalso` heredan los métodos, y `SigridFalsaApp` devuelve `[]` a las
lecturas nuevas.

## 10. Mutación (rigor crítico)

Campaña completa sobre las líneas cambiadas de `cuenta_analitica.py`,
`registro_pipeline.py` y `sigrid_write_client.py`. Puntos que la campaña
tiene que encontrar muertos: el orden `reshor` > tipo; el `== 1` de
`resolver_cuenta` (un `>= 1` elegiría la primera); el `cenide > 0`; la caché
por centro (R7); `caaide` en la posición correcta del INSERT; el `== 10` del
estado contabilizado.

## 11. Riesgos y decisiones

- **Alternativas descartadas** (D1): ANA propio del transfer (duplica el de
  Administración, que es por parte, y no tiene `synckey`); asiento 64X
  (duplica la nómina); cuenta desde la partida (`obrparpar.caaide` vacío en
  postventa; cuando partida y tipo de hora difieren, 540 de 540 líneas M\*
  siguen al tipo, explore §9).
- **El ANA lo genera, casi seguro, «Contabiliza parte…»** (explore §9). Que
  lea `hmores.caaide` es inferencia fuerte (GG sin cuenta = sin ANA; 438/440
  al céntimo), no prueba: la confirma R18 con Administración. Si no la lee,
  se para y se vuelve a D1.
- **Aviso y no conflicto** (D9): un conflicto nuevo obliga a tocar api y
  front. Riesgo: un aviso que nadie atiende (lo que pasó con «sin partida»
  antes de F-013). Mitigación: el aviso dice la consecuencia, y la mutación
  vigila que no desaparezca.
- **`con.est = 10` como «contabilizado»**: inferido (502/502), no documentado.
  Solo alimenta un aviso: un falso positivo no bloquea nada. Lo confirma T0.
- **Modo real ya activo**: hasta desplegar F-037 el transfer seguirá
  escribiendo `caaide = 0` (D10). Hoy hay 0 líneas `porcentajes:` en Sigrid.
- **`_read` y `truncated`**: hoy el transfer lo ignora; se corrige aquí
  porque la lectura nueva de cuentas es la más grande que hace (R7).
- **Verificación real (R17-R18)**: escribe en 0404 y Administración genera
  un ANA de prueba. Mes sin actividad en 0404, `PRUEBA-PORC` en la línea (el
  ANA la saca en apunte aparte, por texto) y limpieza de los dos lados.

## 12. Documentación (`#regla-analitica`, punto 16 de ARCHITECTURE)

Una regla con: de dónde sale la hoja (R2) y la cuenta (R3), qué pasa sin ella
(R4), que la contrapartida, el 6XX, la fecha, la serie y la agrupación son
del ANA de Administración (D2-D7), que el transfer no escribe asientos (R11),
qué pasa al deshacer o corregir (D8, heredado por F-033) y la línea de
procedencia con las decisiones validadas.
