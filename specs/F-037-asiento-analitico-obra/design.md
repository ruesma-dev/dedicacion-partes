<!-- specs/F-037-asiento-analitico-obra/design.md -->
# F-037 · Diseño técnico

Decisiones del humano del 2026-10-05 y 2026-10-06 (requirements §6); queda
abierta D16. El transfer rellena `hmores.caaide` con la regla de `partes`
y, si el parte del mes está cerrado, escribe en un complementario. El ANA lo
genera Administración con «Contabiliza parte…». Evidencia:
`progress/explore_F-037.md` (§9-§11). Lo que trae `partes`: §13.

## 1. Encaje en la arquitectura y límite de servicio

- **Solo `dedicacion-transfer`**: la única pluma sobre Sigrid; ya resuelve la
  obra destino, su centro (`obr.cenide`), los partes, las partidas y los tipos
  de hora. La cuenta es una columna más; el complementario, un parte más con
  la sentencia que ya existe (`stmts_crear_parte`). No es un servicio nuevo:
  no se escriben asientos ni se cambian estados (R15).
- `dedicacion-api` y `dedicacion-front` **no se tocan**: campos nuevos dentro
  de `acciones[]`, `partes[]` y `escritas[]`, que la api reenvía sin esquema;
  el front pinta `AccionLinea.aviso`; las claves de primer nivel no cambian
  (`test_f024_r21`).
- **Regla común con `partes` (D15)**: `cuenta_analitica.py` es **copia literal
  de la versión vigente en `dev` de `partes`** (§13.1) y entra en la lista
  cerrada de copias de `CLAUDE.md` (la línea la pone el líder). Un test
  compara las dos (§9.1). Las SQL de horas y cuentas copian las de su cliente.
- Capas: regla de la cuenta en **application/services** (pura); elección del
  parte del mes en **domain** (pura, la usa el cliente); lecturas en
  **infrastructure/sigrid**; orquestación en el **pipeline**.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/application/services/cuenta_analitica.py` | Copia de `partes` (§13.1): `subcuenta`, `subcuenta_de_linea`, `subcuenta_de_partida` (de F-031), `indexar_cuentas`, `resolver_cuenta`, `CuentaLinea`, `MOTIVO_*` |
| `services/dedicacion-transfer/domain/parte_del_mes.py` | `elegir_parte(filas, ano, mes, est_activo) -> ParteDestino` (§5.2) |
| `services/dedicacion-transfer/tests/test_f037_cuenta_analitica.py` | R2-R5 y la comparación con `partes` |
| `services/dedicacion-transfer/tests/test_f037_cliente_sigrid.py` | R1, R8-R10, R15 sobre `SigridWriteClient` con `_read`/HTTP sustituidos |
| `services/dedicacion-transfer/tests/test_f037_pipeline.py` | R1, R3-R9, R16, R17 con `ClienteFalso` |
| `services/dedicacion-transfer/tests/test_f037_complementario.py` | R10-R14 con `ClienteFalso` y `elegir_parte` |

## 3. Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `…/domain/models/registro_models.py` | `HoraRecurso.caa_cod: Optional[str] = None`, `defecto: bool = False` (campos 5.º y 6.º con defecto: los `HoraRecurso(...)` posicionales siguen valiendo); `AccionLinea.caa_ide: int = 0`, `caa_cod`, `caa_origen: Optional[str] = None`; `ParteDestino.estado: Optional[int] = None`, `complementario: bool = False`, `cerrados: list[str]`, `ides_mes: list[int]` (`default_factory=list`); docstring remite a `#regla-analitica` |
| `…/infrastructure/sigrid/sigrid_write_client.py` | `_read` falla con `truncated` (R8); `horas_de_recursos`, `cuentas_de_centro` y `cuentas_de_partidas` (§6); `partes_existentes` lee todos los partes del mes con `con.est` y elige con `elegir_parte`; `stmt_insert_linea(..., caaide: int = 0)` con `caaide = ?`; docstring sin «caaide=0 … pendiente» |
| `…/application/services/reglas_porcentajes.py` | Solo la constante `MOTIVO_PARTE_CERRADO` (`{parte}`, `{estado}`), ≤ 300 caracteres |
| `…/application/pipelines/registro_pipeline.py` | Paso 4 bis (cuentas), paso 5 (complementario), paso 7 (todos los partes del mes), `ejecutar` (§7) |
| `…/tests/conftest.py`, `…/tests/test_pipeline_offline.py`, `…/tests/test_f002_fuente_unica.py` | §9.2 |
| `docs/ARCHITECTURE.md` | Punto 16 `#regla-analitica`; anclas; alcance «los partes del mes» en `#regla-conflicto` y `#regla-capacidad`; frase de `#regla-sin-partida`; «Acceso a datos» (R18) |
| `docs/INTEGRACION.md` | Fecha y origen; §1 y §7 (R19) |
| `azure-apps/dedicacion.md` (otro repo) | Copia literal de las piezas de `INTEGRACION.md` (commit del humano) |

## 4. Ficheros que NO se tocan

- `reglas_porcentajes.py` salvo la constante: P1-P5, `campos_identidad`,
  `criterio_choque`, `evaluar_capacidad` y `sin_partida` no cambian; cambia
  **qué líneas** reciben (las de todos los partes del mes).
- `partida_resolver.py`, `partida_catalog.py`, `partida_matcher.py`,
  `text_match.py`, `universo_postventa.py`: la partida se sigue casando igual;
  solo se lee su cuenta para el respaldo (R3).
- `interface_adapters/api/app.py` (serializa con `asdict`),
  `prueba_escritura_porcentajes.py` (`limpiar` borra `PRUEBA-PORC` en 0404 en
  cualquier parte), `synckey_de`, el bloqueo `MAX(ide)+1`.
- `services/dedicacion-api/**`, `services/dedicacion-front/**`, `infra/**`,
  `CLAUDE.md` (lo cambia el líder) y el repositorio `partes`.

## 5. Clases y funciones

### 5.1 `cuenta_analitica.py` (application, pura; copia de `partes`)

`subcuenta(cod)`; `subcuenta_de_linea(horas, horide)` (tipo escrito; si no,
`defecto`); `subcuenta_de_partida(caa_cod)` (la subcuenta si empieza por
`CI`/`CD`, si no `None`); `indexar_cuentas(filas)`; `resolver_cuenta(sub,
cuentas, obra_cod) -> CuentaLinea(caa_ide, caa_cod, motivo, aviso)` con
`MOTIVO_RECURSO_SIN_CUENTA` (sin aviso), `MOTIVO_OBRA_SIN_CUENTA` y
`MOTIVO_CUENTA_AMBIGUA` (con aviso). Firmas exactas: las de la copia.

### 5.2 `domain/parte_del_mes.py` (domain, pura)

`elegir_parte(filas, ano, mes, est_activo) -> ParteDestino`; `filas` = partes
del mes `{ide, cod, est}` en cualquier orden. Sin filas → `existe=False`. Con
alguna en `est_activo` → la de **mayor `ide`** de ellas (`existe=True`,
`estado`). Todas cerradas → `existe=False, complementario=True`. Siempre
`cerrados` = códigos de las cerradas, `ides_mes` = todos los `ide`, por
`ide`; `complementario` = hay alguna cerrada. **D16 vive aquí**: «cerrada» =
`est != est_activo` (A); con B sería `est == 10`. Determinista.

### 5.3 `SigridWriteClient` (infrastructure)

`horas_de_recursos(resides)` (misma firma; `HoraRecurso` con `caa_cod`,
`defecto`); `cuentas_de_centro(cenide, empresa, subcuentas)`;
`cuentas_de_partidas(parides) -> dict[int, str | None]`;
`partes_existentes(obra_ide, periodos)` (misma firma; `elegir_parte` con
`est_parte` del ajuste que ya existe, 1); `lineas_del_parte(hmoide, resides)`
sin cambios (el pipeline la llama por cada `ide` de `ides_mes`);
`stmt_insert_linea(..., paride=0, caaide=0)`.

## 6. SQL (en el cliente, parametrizado, base `ruesma`; ninguna con `conide`)

1. `horas_de_recursos`: la de `partes` (§13.1): la de hoy más `cc.cod AS
   caacod` y `CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END AS
   defecto`, `LEFT JOIN res ON res.ide = reshor.reside` y `LEFT JOIN con cc ON
   cc.ide = reshor.caaide AND ISNULL(reshor.caaide, 0) <> 0`.
2. `cuentas_de_centro`: la de `partes`: `caa a JOIN con c`, `a.cenide = ?`,
   `c.emp = ?` y subcuenta `IN (?, …)`; una por centro y petición.
3. `cuentas_de_partidas`: `SELECT p.ide AS ide, c.cod AS cod FROM obrparpar p
   LEFT JOIN con c ON c.ide = p.caaide WHERE p.ide IN (?, …)`; una por
   petición y solo si alguna acción `escribir` sin subcuenta del recurso tiene
   partida (como `partes` F-031 R24).
4. `partes_existentes`: la de hoy más `con.est AS est`, sin quedarse con la
   primera fila.
5. `INSERT INTO hmores`: igual que hoy salvo `caaide = ?`.

## 7. Flujo en el pipeline

- **Paso 4 bis (R1-R9)**, tras casar partidas, acciones `escribir`:
  `subcuenta_de_linea`; si no da y hay `paride`, `subcuenta_de_partida` de su
  cuenta (`caa_origen = "partida"`); una `cuentas_de_centro` por centro de
  obra destino con las subcuentas de los dos orígenes; `resolver_cuenta`;
  `a.aviso` compuesto con «·». Sin `try`: si falla una lectura, falla la
  petición (la api devuelve el error; aquí no hay cola que reintente, §13.3).
- **Paso 5 (R10-R12)**: `partes_existentes` ya elige; si el elegido es
  `complementario`, cada acción `escribir` de ese parte suma el aviso con el
  código (o «nuevo») y los cerrados.
- **Paso 6 (R14)**: sin cambios: `lineas_por_synckey` busca en todo `hmores`.
- **Paso 7 (R13)**: `existentes` = `lineas_del_parte` de cada `ide` de
  `ides_mes` (o `[parte.ide]` si viene vacía y el parte existe: los dobles
  antiguos siguen valiendo), también si el destino es un complementario
  nuevo. Choque con una línea de un parte cerrado → `omitir` con
  `MOTIVO_PARTE_CERRADO`, sin conflicto y con `caa_ide = 0`; prevalece sobre
  el conflicto confirmable. La capacidad cuenta las líneas de todos.
- **`ejecutar`**: complementario nuevo con `stmts_crear_parte` y `desc =
  "Parte <obra> (complementario)"` + marca de pruebas; se relee con
  `partes_existentes` y, si no es el nuevo En registro, falla antes de
  insertar (R11). `stmt_insert_linea(..., caaide=a.caa_ide)`; `escritas[]`
  con `caa_cod`. Solo se borran líneas de partes En registro.

## 8. Contrato HTTP (aditivo)

`acciones[]` + `caa_ide`, `caa_cod`, `caa_origen`; `partes[]` + `estado`, `complementario`, `cerrados`, `ides_mes`; `escritas[]` + `caa_cod`. Nada se quita.

## 9. Tests

### 9.1 Nuevos (sin red ni BBDD; nombres `test_f037_rN_*`)

- `test_f037_cuenta_analitica.py`: R2 (tipo escrito; respaldo del tipo por
  defecto); R3 (partida `CI…`/`CD…` solo si el recurso no da; `CP`/`INGR`
  no); R4-R5 (una cuenta; sin subcuenta → 0 sin aviso; obra sin cuenta y dos
  cuentas → 0 con aviso; nunca la primera). **Comparación con `partes`**: el
  fichero es idéntico al de `partes/services/partes-transfer/application/
  services/cuenta_analitica.py` salvo la línea 1; si el otro repositorio no
  está en disco, `skip` con motivo. El commit copiado consta en el docstring.
- `test_f037_cliente_sigrid.py`: R1/R9 (posición de `caaide`, `cenide` de la
  obra, sin `cuaide`); R8 (`truncated` lanza; SQL parametrizadas; una lectura
  de cuentas por centro con las dos subcuentas); R10 (`con.est`, sin quedarse
  con la primera fila); R15 (ninguna SQL de escritura nombra `asi`, `asa`,
  `apu`, `apa` ni actualiza `con`).
- `test_f037_complementario.py`: `elegir_parte` (sin filas; uno En registro;
  uno cerrado de cada estado; cerrado + En registro; dos En registro → mayor
  `ide`; orden indiferente) (R10-R11); complementario nuevo con
  `(complementario)` y aviso; relectura fallida sin inserts (R11-R12); choque
  con línea de un parte cerrado → `omitir` sin borrado ni cuenta (R13);
  capacidad sumando el cerrado (R13); `synckey` en un cerrado → `ya_registrado`
  (R14).
- `test_f037_pipeline.py`: R1; R3 (respaldo, `caa_origen`); R4 en normal,
  postventa y pruebas (centro de la obra destino); R6 (con «sin partida» los
  dos avisos); R7; R8 (fallo de lectura → excepción, nada escrito); R16; R17.
- R18-R19: `test_f002_fuente_unica.py` y revisión del `git diff` (reviewer).

### 9.2 Tests anteriores que cambian (lista cerrada)

1. `tests/conftest.py`, **solo el doble y sus datos**: `cenide` en las cuatro
   obras de `ClienteFalso`; `caa_cod` en los `HoraRecurso` de MENC
   (`00000.CIMO03`) y MJEFO (`00000.CIMO02`); métodos `cuentas_de_centro`
   (esas dos subcuentas para cualquier `cenide > 0`, contando lecturas) y
   `cuentas_de_partidas` (vacío). `partes_existentes` y `lineas_del_parte` no
   cambian. Ningún assert cambia: ninguna acción anterior gana un aviso
   (`test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe`
   compara el aviso entero).
2. `tests/test_pipeline_offline.py`: los dos métodos en su doble. Ningún
   assert cambia.
3. `tests/test_f002_fuente_unica.py`: `"regla-analitica"` en `ANCLAS`.

Los demás (`test_f002_*`, `test_f013`, `test_f022`, `test_f024`, `test_f025`,
`test_f026`) pasan **sin tocarlos**.

## 10. Mutación (rigor crítico)

Campaña completa sobre las líneas cambiadas de `cuenta_analitica.py`,
`parte_del_mes.py`, `registro_pipeline.py` y `sigrid_write_client.py`. Deben
salir muertos: tipo escrito > defecto > partida; el `CI`/`CD`; el `> 1` de la
ambigüedad; `est != est_activo`; «mayor `ide`»; el choque con un cerrado; la
caché por centro; la posición de `caaide`. `partes` cerró 33/33 en F-021.

## 11. Riesgos

- **«Contabiliza parte…» deja el parte en Imputado (10)**: lo confirma el log
  de Sigrid («Contabilizar parte», `partes` §D2) y 502/502 partes. Que el ANA
  lea `hmores.caaide` se confirma en R21.
- **D16 abierta**: con A, de marzo a agosto de 2026 las líneas irían a
  complementarios de partes Cerrados; con B, a los Cerrados. Un predicado.
- **Respaldo de partida (R3) aún no está en `partes`** (su F-031, aprobada y
  sin mergear): §13.1 dice cómo se copia.
- **Complementario sin precedente posterior a contabilizar** (explore §10);
  R21 comprueba que se contabiliza aparte.
- **Aviso y no conflicto** (un conflicto tocaría api y front). **Modo real
  activo**: hasta desplegar, `caaide = 0` (hoy 0 líneas `porcentajes:`).

## 12. Documentación (`#regla-analitica`)

R2-R5 (regla común con `partes`), R10-R14, que 6XX, contrapartida, fecha,
serie y agrupación son del ANA, R15, D8 (heredado por F-033) y procedencia.

## 13. Lo aprendido en `partes`

1. **Versión que se copia.** Hoy la vigente en `dev` de `partes` es la de
   F-021, commit `b038943` (2026-10-01; único cambio posterior a `9947927`,
   estilo), **sin** `subcuenta_de_partida`, que añade su F-031 (rama
   `feature/F-031-asiento-analitico`, spec v4 `b816059`, sin implementar). En
   T2 se copia la vigente **en ese momento** y su commit queda en el
   docstring y en `progress/impl_F-037.md`. Si F-031 aún no está en `dev`, se
   copia `b038943` y R3 queda en rojo y `blocked` hasta que lo esté: no se
   escribe un respaldo propio (dos verdades). El test de §9.1 obliga a
   recopiar cuando `partes` cambie.
2. **Medido allí** (`partes/progress/explore_F-021_sigrid.md`): 99,64 % de
   coincidencia con las líneas manuales en la empresa 1; `res.caaide` 0 en
   todos; 1 cuenta de baja de 184.234 y ninguna usada (no se filtran bajas);
   media 231 cuentas por centro, máximo 768 (por eso la lectura filtra por
   subcuenta). F-031 §D10: cuando partida y recurso difieren (1.013 líneas
   de 2026), la línea lleva la del recurso; recurso sin cuenta 544, 478 con
   la de la partida.
3. **La lectura que tumba la petición** (`partes` F-021 DA7, observación O1
   de `review_F-021.md`): allí el docstring prometía un reintento de cola que
   no existe. Aquí no hay cola: el fallo vuelve a la api como error del
   registro y nada se escribe. No se promete reintento.
4. **Porsan y otras empresas.** En `partes` la 28 no tiene cuenta en `reshor`
   (0 %, DA13: nada en código). Aquí las obras son de la 1 y los recursos de
   varias: de los recursos M\* activos, empresa 1 183/183 con subcuenta, 18
   7/8, 25 0/1, 31 4/4 (explore §11): dos irían sin cuenta y sin aviso (R5).
5. **Complementario y estados** (`partes` F-031 R1-R14, §D2, §D11): los mismos
   estados de `conest`, el mismo «mayor `ide` En registro», choque con un
   cerrado = omitir, relectura obligatoria tras crear. Diferencias decididas
   aquí: el texto `(complementario)` (D13; `partes` usa `Parte <obra>`) y que
   aquí no hay lock ni cola.
6. **Pendiente en `partes`**: sus M2-M4 de F-021 (escritura en 0404 y
   confirmación de Administración) no se han hecho; R20-R21 de esta spec las
   cubren para `dedicacion`. Su `comprobar_asiento_analitico.py` (F-031 R35,
   solo lectura) servirá para R21 cuando exista.
