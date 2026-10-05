<!-- specs/F-037-asiento-analitico-obra/design.md -->
# F-037 · Diseño técnico

Diseñado con las decisiones del humano del 2026-10-05 (requirements §6): el
transfer rellena `hmores.caaide` con la regla de `partes` F-021 y, si el parte
del mes está contabilizado, escribe en un complementario. El asiento analítico
(ANA) lo sigue generando Administración con «Contabiliza parte…». Evidencia:
`progress/explore_F-037.md` (§9 y §10).

## 1. Encaje en la arquitectura y límite de servicio

- **Solo `dedicacion-transfer`**: es la única pluma sobre Sigrid y ya resuelve
  la obra destino, su centro (`obr.cenide`), los partes y los tipos de hora.
  La cuenta es una columna más de la línea; el complementario, un parte más
  creado con la sentencia que ya existe (`stmts_crear_parte`).
- **No es un servicio nuevo** ni una responsabilidad nueva: no se escriben
  asientos (R15).
- `dedicacion-api` y `dedicacion-front` **no se tocan**: los campos nuevos van
  dentro de `acciones[]`, `partes[]` y `escritas[]`, que la api reenvía sin
  esquema; el front ya pinta `AccionLinea.aviso`; las claves de primer nivel
  no cambian (`test_f024_r21`).
- **Regla compartida con `partes`** (D15 = A): `cuenta_analitica.py` es copia
  literal de `partes/services/partes-transfer/application/services/
  cuenta_analitica.py` (F-021, l. 1-96) y entra en la lista cerrada de copias
  de `CLAUDE.md` con decisión expresa del humano. Si D15 = B, se reescribe con
  la misma interfaz y los mismos tests. Las SQL de horas y cuentas copian las
  de su cliente (l. 231-242 y 265-270).
- Capas: regla de la cuenta en **application/services** (pura); elección del
  parte del mes en **domain** (pura, la usa el cliente); lecturas en
  **infrastructure/sigrid**; orquestación en el **pipeline**.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/application/services/cuenta_analitica.py` | `subcuenta`, `subcuenta_de_linea`, `CuentaLinea`, `indexar_cuentas`, `resolver_cuenta` y los tres `MOTIVO_*` (copia de `partes`) |
| `services/dedicacion-transfer/domain/parte_del_mes.py` | `elegir_parte(filas, ano, mes) -> ParteDestino` (§5.2) |
| `services/dedicacion-transfer/tests/test_f037_cuenta_analitica.py` | R2-R4 sobre las funciones puras |
| `services/dedicacion-transfer/tests/test_f037_cliente_sigrid.py` | R1, R7, R8, R9, R15 sobre `SigridWriteClient` con `_read`/HTTP sustituidos |
| `services/dedicacion-transfer/tests/test_f037_pipeline.py` | R1, R3, R5-R7, R16, R17 con `ClienteFalso` |
| `services/dedicacion-transfer/tests/test_f037_complementario.py` | R10-R14 con `ClienteFalso` y `elegir_parte` |

## 3. Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `…/domain/models/registro_models.py` | `HoraRecurso.caa_cod: Optional[str] = None` y `defecto: bool = False` (campos 5.º y 6.º, con defecto: los `HoraRecurso(...)` posicionales siguen valiendo); `AccionLinea.caa_ide: int = 0`, `caa_cod: Optional[str] = None`; `ParteDestino.complementario: bool = False`, `contabilizados: list[str]` y `ides_mes: list[int]` (`default_factory=list`); `ESTADO_PARTE_CONTABILIZADO = 10`; docstring remite a `#regla-analitica` |
| `…/infrastructure/sigrid/sigrid_write_client.py` | `_read` falla con `truncated` (R7); `horas_de_recursos` y `cuentas_de_centro(cenide, empresa, subcuentas)` como en `partes` (§6); `partes_existentes` lee todos los partes del mes con `con.est` y elige con `elegir_parte` (R9-R10); `stmt_insert_linea(..., caaide: int = 0)` con `caaide = ?`; docstring de cabecera sin «caaide=0 … pendiente» |
| `…/application/services/reglas_porcentajes.py` | Solo una constante: `MOTIVO_PISADO_CONTABILIZADO` (`{parte}`), ≤ 300 caracteres |
| `…/application/pipelines/registro_pipeline.py` | Paso 4 bis (cuentas), paso 5 (complementario), paso 7 (todos los partes del mes), `ejecutar` (`caaide`, descripción del complementario, `caa_cod` en `escritas`) (§7) |
| `…/tests/conftest.py`, `…/tests/test_pipeline_offline.py`, `…/tests/test_f002_fuente_unica.py` | §9.2 |
| `docs/ARCHITECTURE.md` | Punto 16 `#regla-analitica`; anclas de la cabecera; alcance «los partes del mes» en `#regla-conflicto` y `#regla-capacidad`; frase de `#regla-sin-partida` (R18); tabla «Acceso a datos» |
| `docs/INTEGRACION.md` | Fecha y origen; §1 (lecturas del transfer: `caa`, `con.est`, `reshor.caaide`, `res.horide`); §7: qué se rompe si cambian, y «Contabiliza parte…» (`est = 10`) |
| `CLAUDE.md` (si D15 = A) | `cuenta_analitica.py` en la lista cerrada de copias de `partes` |
| `azure-apps/dedicacion.md` (otro repo) | Copia literal de las piezas de `INTEGRACION.md` (T12; commit del humano) |

## 4. Ficheros que NO se tocan

- `reglas_porcentajes.py` fuera de la constante: P1-P5, `campos_identidad`,
  `criterio_choque`, `evaluar_capacidad` y `sin_partida` no cambian; lo que
  cambia es **qué líneas** reciben (las de todos los partes del mes).
- `partida_resolver.py`, `partida_catalog.py`, `partida_matcher.py`,
  `text_match.py`, `universo_postventa.py`: la cuenta no sale de la partida.
- `interface_adapters/api/app.py` (serializa con `asdict`),
  `prueba_escritura_porcentajes.py` (`limpiar` borra por `PRUEBA-PORC` en 0404
  en cualquier parte, también el complementario; `inspeccionar` ya enseña
  `caaide`), `synckey_de`, `PREFIJO_SYNCKEY`, el bloqueo `MAX(ide)+1`.
- `services/dedicacion-api/**`, `services/dedicacion-front/**`, `infra/**`.
- **El repositorio `partes`**: no se toca. Si alguien corrige su
  `cuenta_analitica.py`, avisa de la copia (regla de `CLAUDE.md`).

## 5. Clases y funciones

### 5.1 `application/services/cuenta_analitica.py` (application, pura)

Interfaz de `partes` (R2-R4): `subcuenta(cod) -> str | None` (tras el primer
punto, `strip`; sin punto o vacío → `None`); `subcuenta_de_linea(horas,
horide)` (la del tipo escrito; si no, la del `defecto`); `indexar_cuentas(
filas)`; `resolver_cuenta(sub, cuentas, obra_cod) -> CuentaLinea(caa_ide,
caa_cod, motivo, aviso)`, con `MOTIVO_RECURSO_SIN_CUENTA` (sin aviso),
`MOTIVO_OBRA_SIN_CUENTA` y `MOTIVO_CUENTA_AMBIGUA` (con aviso).

### 5.2 `domain/parte_del_mes.py` (domain, pura)

`elegir_parte(filas: list[dict], ano, mes) -> ParteDestino`. `filas` = los
partes del mes `{ide, cod, est}` en cualquier orden. Devuelve:

- sin filas → `existe=False`;
- con alguna sin contabilizar → la de **mayor `ide`** de ellas (`existe=True`,
  `complementario` = hay alguna contabilizada o alguna de menor `ide`);
- todas contabilizadas → `existe=False, complementario=True` (hay que crear);
- siempre `contabilizados` = sus `cod` e `ides_mes` = todos los `ide`, en
  orden de `ide`. Determinista: el orden de las filas no cambia el resultado.

### 5.3 `SigridWriteClient` (infrastructure)

- `horas_de_recursos(resides)`: misma firma; `HoraRecurso` con `caa_cod` y
  `defecto`.
- `cuentas_de_centro(cenide, empresa, subcuentas) -> dict[str, list[tuple[int,
  str]]]`: una lectura, agrupada con `indexar_cuentas`.
- `partes_existentes(obra_ide, periodos)`: misma firma y tipo de vuelta; por
  periodo, `elegir_parte` sobre todas las filas.
- `lineas_del_parte(hmoide, resides)`: sin cambios; el pipeline la llama por
  cada `ide` de `ides_mes` y marca qué líneas son de un parte contabilizado.
- `stmt_insert_linea(..., paride: int = 0, caaide: int = 0) -> dict`.

## 6. SQL (en el cliente del transfer, parametrizado, base `ruesma`)

Ninguna contiene `conide` (`test_f026_r20` lo vigila en toda lectura).

1. `horas_de_recursos`: la de `partes` — la de hoy más `cc.cod AS caacod` y
   `CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END AS defecto`, con
   `LEFT JOIN res ON res.ide = reshor.reside` y `LEFT JOIN con cc ON cc.ide =
   reshor.caaide AND ISNULL(reshor.caaide, 0) <> 0`.
2. `cuentas_de_centro`: `SELECT a.ide AS caaide, c.cod AS cod FROM caa a JOIN
   con c ON c.ide = a.ide WHERE a.cenide = ? AND c.emp = ? AND
   LTRIM(RTRIM(SUBSTRING(c.cod, CHARINDEX('.', c.cod) + 1, 24))) IN (?, …)`.
3. `partes_existentes`: la de hoy (`hmo.obride`, `ano`, `mes`, `reside = 0`,
   `con.tip` de parte) más `con.est AS est`, sin quedarse con la primera fila.
4. `INSERT INTO hmores`: igual que hoy salvo `caaide = ?`.

## 7. Flujo en el pipeline

- **Paso 4 bis (R1-R7)**, tras las reglas, solo acciones `escribir`: por obra
  destino (`obra_de(a)`), `subcuenta_de_linea(horas[recurso], a.hora_ide)`;
  una lectura `cuentas_de_centro(cenide, obra.empresa, subcuentas)` por centro
  y petición (sin `try`: si falla, falla la petición); `resolver_cuenta`;
  `a.caa_ide`, `a.caa_cod`; `a.aviso = componer(a.aviso, c.aviso)` con «·».
  Centro 0 → sin lectura y `caa_ide = 0` con aviso de obra sin cuenta.
- **Paso 5 (R9-R12)**: `partes_existentes` ya elige. Si el elegido es
  `complementario`, cada acción `escribir` de ese parte suma un aviso que
  nombra el parte (existente o «nuevo») y los contabilizados.
- **Paso 6 (R14)**: sin cambios: `lineas_por_synckey` ya busca en todo
  `hmores`, sea cual sea el parte.
- **Paso 7 (R13)**: por destino y mes, `existentes` = `lineas_del_parte` de
  cada `ide` de `ides_mes` (o `[parte.ide]` si la lista viene vacía y el parte
  existe: así los dobles antiguos siguen valiendo); se evalúa también cuando el
  destino es un complementario **nuevo**. Si alguna línea con la que choca una
  acción es de un parte contabilizado, la acción pasa a `omitir` con
  `MOTIVO_PISADO_CONTABILIZADO` y no genera conflicto; la capacidad cuenta las
  líneas de todos los partes.
- **`ejecutar`**: un complementario nuevo se crea con `stmts_crear_parte` y
  `desc = "Parte <obra> (complementario)"` + marca de pruebas; se relee con
  `partes_existentes` (que ahora elige el nuevo, único sin contabilizar).
  `stmt_insert_linea(..., caaide=a.caa_ide)`; `escritas[]` con `caa_cod`. Los
  borrados de pisado solo pueden ser de partes sin contabilizar (R15).

## 8. Contrato HTTP (aditivo)

`acciones[]`: `caa_ide` (int) y `caa_cod` (str|null). `partes[]`:
`complementario` (bool), `contabilizados` (list[str]), `ides_mes`
(list[int]). `escritas[]`: `caa_cod`. Nada se quita ni se renombra.

## 9. Tests

### 9.1 Nuevos (sin red ni BBDD; nombres `test_f037_rN_*`)

- `test_f037_cuenta_analitica.py`: R2 (tipo escrito; respaldo del tipo por
  defecto; `00000.CIMO08`, `CIMO05` sin punto → nada, `' x. '`); R3 (una
  cuenta); R4 (sin subcuenta → 0 sin aviso; obra sin cuenta y dos cuentas →
  0 con aviso; nunca la primera). Si D15 = A, además: el fichero es idéntico
  al de `partes` salvo la primera línea (test que lee los dos si el otro
  repositorio está presente; si no, `skip` con motivo).
- `test_f037_cliente_sigrid.py`: R1/R8 (posición de `caaide` en el INSERT,
  `cenide` de la obra, sin `cuaide`); R7 (`truncated` lanza; `horas_de_
  recursos` rellena `caa_cod` y `defecto`; `cuentas_de_centro` filtra centro,
  empresa y subcuentas, parametrizada); R9 (`partes_existentes` lee `con.est`
  y no se queda con la primera fila); R15 (ninguna SQL de escritura nombra
  `asi`, `asa`, `apu`, `apa`).
- `test_f037_complementario.py`: `elegir_parte` (sin filas, uno abierto, uno
  contabilizado, contabilizado + abierto, dos abiertos → mayor `ide`, orden
  de filas indiferente) (R10-R11); pipeline: contabilizado → parte nuevo con
  `(complementario)` y aviso (R11-R12); pisado contra línea del contabilizado
  → `omitir` con motivo, sin borrado (R13); capacidad sumando el
  contabilizado (R13); `synckey` en el contabilizado → `ya_registrado` (R14).
- `test_f037_pipeline.py`: R1 (insert con su `caaide`); R3 normal, postventa y
  pruebas (el centro leído es el de la obra destino); R5 (con «sin partida»
  los dos avisos, sin conflicto nuevo); R6; R7 (dos líneas, un centro: una
  lectura; fallo de lectura → excepción); R16; R17.
- R18-R19: `test_f002_fuente_unica.py` y revisión del `git diff` (reviewer).

### 9.2 Tests anteriores que cambian (lista cerrada)

1. `tests/conftest.py`, **solo el doble y sus datos**: `cenide` en las cuatro
   obras de `ClienteFalso`; `caa_cod` en los `HoraRecurso` de MENC
   (`00000.CIMO03`) y MJEFO (`00000.CIMO02`); método `cuentas_de_centro`
   (esas dos subcuentas para cualquier `cenide > 0`, contando lecturas).
   `partes_existentes` y `lineas_del_parte` no cambian. Ningún assert cambia:
   ninguna acción de los tests anteriores gana un aviso
   (`test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe` compara
   el aviso entero).
2. `tests/test_pipeline_offline.py`: `cuentas_de_centro` en su doble. Ningún
   assert cambia.
3. `tests/test_f002_fuente_unica.py`: `"regla-analitica"` en `ANCLAS`.

Los demás (`test_f002_*`, `test_f013`, `test_f022`, `test_f024`, `test_f025`,
`test_f026`) pasan **sin tocarlos**: heredan el doble, `SigridFalsaApp`
devuelve `[]` a las lecturas nuevas y un `ParteDestino` con `ides_mes` vacío
se trata como hoy.

## 10. Mutación (rigor crítico)

Campaña completa sobre las líneas cambiadas de `cuenta_analitica.py`,
`parte_del_mes.py`, `registro_pipeline.py` y `sigrid_write_client.py`. Deben
salir muertos: el orden tipo escrito > tipo por defecto; el `> 1` de la
ambigüedad; el `== 10`; «mayor `ide`» frente a «menor»; el pisado contra el
contabilizado; la caché por centro; la posición de `caaide` en el INSERT.

## 11. Riesgos y decisiones

- **Alternativas descartadas**: ANA propio (duplica el de Administración y no
  tiene `synckey`); asiento 64X (duplica la nómina); cuenta desde la partida o
  desde `auxhor.caacod` (la regla de `partes`, decidida por el humano, no los
  usa; explore §10 mide el efecto).
- **«Contabiliza parte…» y `est = 10`**: inferidos (502/502), no
  documentados. Lo confirma R21; si no, se para y se vuelve a D1.
- **Complementario sin precedente**: en Sigrid no hay ningún parte creado
  **después** de contabilizar el del mes (explore §10); los segundos partes
  reales se crearon antes y cada uno tuvo su ANA. R21 comprueba que
  Administración lo contabiliza aparte.
- **Alcance de identidad y capacidad** (D14): pasar de «el parte» a «los
  partes del mes» cambia dos reglas de ARCHITECTURE; sin ello, un
  complementario podría duplicar la jornada del mes sin aviso.
- **Aviso y no conflicto** (D9): un conflicto nuevo obliga a tocar api y
  front. Mitigación: el aviso dice la consecuencia, y la mutación lo vigila.
- **Modo real ya activo**: hasta desplegar F-037 el transfer escribe
  `caaide = 0` (D10). Hoy hay 0 líneas `porcentajes:` en Sigrid.
- **Verificación real (R20-R21)**: escribe en 0404 y Administración contabiliza
  dos partes de prueba; mes sin actividad en 0404 y limpieza de los dos lados.

## 12. Documentación (`#regla-analitica`, punto 16 de ARCHITECTURE)

Una regla con: origen y destino de la cuenta (R2-R4, remitiendo a `partes`
F-021 como regla común), el parte complementario (R9-R14), que el 6XX, la
contrapartida, la fecha, la serie y la agrupación son del ANA de
Administración, que el transfer no escribe asientos (R15), deshacer y
corregir (D8, heredado por F-033) y la línea de procedencia con las decisiones.
