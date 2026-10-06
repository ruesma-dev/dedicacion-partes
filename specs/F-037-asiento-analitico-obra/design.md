<!-- specs/F-037-asiento-analitico-obra/design.md -->
# F-037 · Diseño técnico

Copia adaptada de la F-031 de `partes` (humano, 2026-10-06: «se usa el mismo
parte realmente»). Fuente: rama `feature/F-031-asiento-analitico`, revisada
en `progress/explore_F-037_partes_F-031.md`. Todas las decisiones cerradas.

## 1. Encaje y límite de servicio

- **Solo `dedicacion-transfer`**: la única pluma sobre Sigrid. Cuenta en la
  línea, elección del parte, complementario y duplicados son lo mismo que
  hace `sv5` de `partes` sobre **los mismos partes**: lo que decide sobre el
  parte se copia; lo que es de nuestro pipeline se adapta. No se escriben
  asientos ni se cambian estados (R17).
- `dedicacion-api` y `dedicacion-front` **no se tocan**: los campos nuevos
  van dentro de `acciones[]`, `partes[]` y `escritas[]`, que la api reenvía
  sin esquema; lo que el usuario debe leer se suma a `AccionLinea.aviso`, que
  el front ya pinta; las claves de primer nivel no cambian (`test_f024_r21`).
- Capas como en `partes`: reglas puras en **application/services**
  (`estado_parte.py`, `cuenta_analitica.py`), modelos en **domain**, lecturas
  y sentencias en **infrastructure/sigrid**, orquestación en el **pipeline**.

## 2. Ficheros a crear

| Ruta (bajo `services/dedicacion-transfer/`) | Qué |
|---|---|
| `application/services/estado_parte.py` | **Copia literal** de `partes` (§12): `elegir_parte`, `nombre_estado`, `aviso_de_parte`, `motivo_choque`, `MOTIVO_PARTE_CERRADO` |
| `application/services/cuenta_analitica.py` | **Copia literal** de `partes` (§12): F-021 + respaldo `CI`/`CD` (`subcuenta_de_partida`, `origen_subcuenta`) |
| `tests/test_f037_reglas_partes.py` | R2-R5, R10, R13, R15 sobre las dos copias (casos de `test_f031_estado_parte.py` y `test_f031_cuenta_partida.py` de `partes`, renombrados) |
| `tests/test_f037_copias_partes.py` | Anti-divergencia (§12) |
| `tests/test_f037_cliente_sigrid.py` | R1, R7-R9, R11, R16, R17 y D17 sobre `SigridWriteClient` con `_read`/HTTP sustituidos |
| `tests/test_f037_pipeline.py` | R1-R8, R10-R15, R17 con `ClienteFalso` |

## 3. Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `domain/models/registro_models.py` | Como en `partes`: `ParteSigrid(ide, cod, est)` y `PartidaCuenta(ide, cod, caa_cod)` (frozen); `HoraRecurso.caa_cod`, `defecto` (con defecto: los `HoraRecurso(...)` posicionales siguen valiendo); `AccionLinea.caa_ide`, `caa_cod`, `caa_motivo`, `caa_aviso`, `caa_origen`, `caa_nota`; `ParteDestino.estado`, `complementario`, `cerrados`, `del_periodo`, `aviso` (se queda `obra_cod`) |
| `config/settings.py` | `est_parte_cerrado` (`EST_PARTE_CERRADO`, 3) y `est_parte_imputado` (`EST_PARTE_IMPUTADO`, 10), solo para textos (DA7 de `partes`); `.env.example` |
| `infrastructure/sigrid/sigrid_write_client.py` | `_read` falla con `truncated`; `horas_de_recursos`, `cuentas_de_centro`, `partes_del_periodo`, `partidas_de_lineas` (§6); **`siguiente_cod_pt(ano, empresa)`** con `AND emp = ?`; **`stmts_crear_parte`** con `hmo` por `cod`, `tip` **y `emp`** y alta condicional (D17); `stmt_insert_linea(..., caaide)`; fuera `partes_existentes` (sin uso); docstring |
| `application/pipelines/registro_pipeline.py` | Pasos 4 bis, 5, 7, 9 y 10 (§7) |
| `tests/conftest.py`, `tests/test_pipeline_offline.py`, `tests/test_f002_fuente_unica.py` | §9.2 |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | R18, R19 |
| `azure-apps/dedicacion.md` (otro repo) | Copia de las piezas de `INTEGRACION.md` (commit del humano) |

## 4. Ficheros que NO se tocan

- `reglas_porcentajes.py`: P1-P5, `campos_identidad`, `criterio_choque`,
  `evaluar_capacidad` y `sin_partida` no cambian; cambia **qué líneas**
  reciben (las de todos los partes del periodo). El motivo `parte_cerrado`
  sale de `estado_parte.motivo_choque` (copia).
- `partida_resolver.py`, `partida_catalog.py`, `partida_matcher.py`,
  `text_match.py`, `universo_postventa.py`: la partida se casa igual; solo se
  lee su cuenta para el respaldo.
- `interface_adapters/api/app.py` (serializa con `asdict`),
  `prueba_escritura_porcentajes.py` (`limpiar` borra `PRUEBA-PORC` en 0404 en
  cualquier parte), `synckey_de`, el bloqueo `MAX(ide)+1` de `hmores`.
- `services/dedicacion-api/**`, `services/dedicacion-front/**`, `infra/**`,
  `CLAUDE.md` (líder) y el repositorio `partes`.

## 5. Funciones

- **Copias** (§12): firmas y textos de `partes` tal cual. `elegir_parte(ano,
  mes, partes, *, est_registro)`; `aviso_de_parte(p, nombres)`;
  `motivo_choque(cod, estado)`; `origen_subcuenta(horas, horide, partida) ->
  OrigenSubcuenta(sub, origen, nota)`; `resolver_cuenta(sub, cuentas, obra_cod)
  -> CuentaLinea(caa_ide, caa_cod, motivo, aviso)`. Textos en ASCII.
- **Cliente** (`partes` T8, `d0feff1`): `partes_del_periodo(obra_ide, ano,
  mes) -> list[ParteSigrid]`; `partidas_de_lineas(parides) -> dict[int,
  PartidaCuenta]`; `cuentas_de_centro(cenide, empresa, subcuentas)`;
  `siguiente_cod_pt(ano, empresa)`; `stmts_crear_parte(*, obra, ano, mes, cod,
  desc)` (§6.5); `stmt_insert_linea(..., paride=0, caaide=0)`.
- **Pipeline** (adaptado de `partes` design §7.3-§7.4; nuestro pipeline no
  tiene cola ni lock: el preflight se repite dentro de `ejecutar`).

## 6. SQL (en el cliente, parametrizado, base `ruesma`; ninguna con `conide`)

1. `horas_de_recursos` y `cuentas_de_centro`: las de `partes` F-021
   (`cc.cod AS caacod`, `defecto` por `res.horide`; `caa a JOIN con c` con
   `a.cenide = ?`, `c.emp = ?` y subcuenta `IN (?, …)`).
2. `partes_del_periodo`: `SELECT hmo.ide AS ide, con.cod AS cod, con.est AS
   est FROM hmo JOIN con ON con.ide = hmo.ide WHERE hmo.obride = ? AND
   hmo.ano = ? AND hmo.mes = ? AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ?
   ORDER BY hmo.ide DESC`.
3. `partidas_de_lineas`: `SELECT p.ide AS ide, p.cod AS cod, pc.cod AS
   caacod FROM obrparpar p LEFT JOIN con pc ON pc.ide = p.caaide AND
   ISNULL(p.caaide, 0) <> 0 WHERE p.ide IN (?, …)`.
4. `siguiente_cod_pt`: `SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ?
   AND emp = ?` (hoy **no filtra por empresa**: el número sale del mayor de
   todas las empresas).
5. `stmts_crear_parte`, **una transacción** (un solo lote de `escribir`):
   - `INSERT INTO con (ide, emp, tip, est, cod, res, fec) SELECT x.n, ?, ?, ?,
     ?, ?, ? FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM con WITH (UPDLOCK,
     HOLDLOCK)) x WHERE NOT EXISTS (código `cod`+`emp`+`tip` ya usado) AND
     NOT EXISTS (parte En registro de esa obra, `ano`, `mes`, `reside = 0`)`,
     las dos subconsultas con `WITH (UPDLOCK, HOLDLOCK)`. **Trampa**: la
     condición va fuera del agregado; un `SELECT MAX … WHERE NOT EXISTS`
     devuelve una fila aunque la condición falle e insertaría `ide = 1`.
     Los seis primeros parámetros, en el orden de hoy (`test_f022_r17`).
   - `INSERT INTO hmo (…) SELECT ide, … FROM con WHERE cod = ? AND tip = ? AND
     emp = ? AND NOT EXISTS (SELECT 1 FROM hmo h WHERE h.ide = con.ide)`
     (hoy **sin `emp`**: con dos empresas con el mismo código, dos `hmo`).
6. `INSERT INTO hmores`: igual que hoy salvo `caaide = ?`.

## 7. Flujo en el pipeline

- **Paso 4 bis (R1-R8)**, tras casar partidas, acciones `escribir`, por obra
  destino (`obra_de(a)`): las que no dan subcuenta del recurso y traen
  `paride` ⇒ una `partidas_de_lineas` por petición; `origen_subcuenta`; una
  `cuentas_de_centro` por centro con las subcuentas de ambos orígenes;
  `resolver_cuenta`; copia `caa_*`, `caa_origen`, `caa_nota`; `a.aviso` suma
  `caa_aviso` y `caa_nota` con « · ». Sin `try` (R7). INFO por obra con el
  recuento recurso/partida/ninguna (sin nombres).
- **Paso 5 (R9-R11, R15)**: por destino y periodo, `partes_del_periodo` →
  `elegir_parte(est_registro=est_parte_activo)`; si no `existe`, `cod =
  siguiente_cod_pt(ano, obra.empresa)`; `aviso = aviso_de_parte(p, nombres)`
  con `nombre_estado`; se suma al `aviso` de sus acciones `escribir`.
- **Paso 6 (R12)**: sin cambios (`lineas_por_synckey` ya es global).
- **Paso 7 (R13-R14)**: por destino y periodo, `lineas_del_parte` de **cada**
  parte de `del_periodo` (aunque el elegido sea nuevo), recordando su parte.
  Choque con una línea de un parte cerrado ⇒ `omitir`, `motivo_choque(cod,
  nombre)`, `caa_ide = 0` y demás `caa_*` a `None`, sin conflicto. Si no,
  conflicto como hoy con el `parte_cod` del parte donde vive la línea. La
  capacidad suma las líneas de todos los partes.
- **Paso 9 (R11, D17)**: si el elegido no existe, `stmts_crear_parte` con
  `desc = "Parte <obra>"` (D13; + marca de pruebas), luego `partes_del_periodo` +
  `elegir_parte`. Si hay uno En registro (el nuestro o el que creó `partes`
  en ese instante), se usa y se registra en el log cuál. Si no (código
  ocupado), se recalcula `siguiente_cod_pt` y se reintenta **una** vez; si
  tampoco, `RuntimeError` antes de insertar líneas.
- **Paso 10**: inserta en el elegido con su `caaide`; solo borra líneas de
  partes En registro (las de un cerrado nunca llegan a conflicto).

## 8. Contrato HTTP (aditivo, el de `partes`)

`acciones[]` + `caa_ide`, `caa_cod`, `caa_motivo`, `caa_aviso`, `caa_origen`,
`caa_nota`; `partes[]` + `estado`, `complementario`, `cerrados`, `del_periodo`
(`ide`, `cod`, `est`), `aviso`; `escritas[]` + `caa_cod`. Nada se quita.

## 9. Tests

### 9.1 Nuevos (sin red ni BBDD; nombres `test_f037_rN_*`)

- `test_f037_reglas_partes.py`: los casos de los tests de `partes` sobre las
  copias, renombrados: elegir (mayor `ide` En registro aunque haya cerrados
  mayores, ninguno, todos cerrados, orden indiferente), textos, `motivo_choque`,
  subcuenta del tipo escrito y por defecto, partida `CI`/`CD` válida e
  inválida (`CP`, `INGR`, sin punto), obra sin cuenta, ambigua.
- `test_f037_cliente_sigrid.py`: `caaide` en su posición; `truncated` lanza;
  `partes_del_periodo` y `partidas_de_lineas` parametrizadas;
  `siguiente_cod_pt` filtra por `emp`; el `hmo` del alta lleva `emp`; D17: el
  `con` lleva las dos condiciones fuera del agregado y el `hmo` el `NOT
  EXISTS`; ninguna sentencia nombra `asi`, `asa`, `apu`, `apa` ni hace
  `UPDATE con`.
- `test_f037_pipeline.py`: R1; R3 con `caa_origen`/`caa_nota`; R4 en normal,
  postventa y pruebas; R5-R6 (avisos sumados, sin conflicto); R7 (una lectura
  por centro y de partidas; fallo ⇒ excepción y nada escrito); R10 (cerrado
  de `ide` mayor no gana; todos cerrados ⇒ nuevo con su aviso; complementario
  de otro servicio reutilizado); R11 (relectura sin En registro ⇒ reintento
  y luego excepción, sin inserts); R12-R14 (synckey en cerrado; choque con
  cerrado ⇒ `omitir` sin borrado ni cuenta; capacidad sumando el cerrado;
  `pisar_claves` no borra en cerrado); R15; R17.
- `test_f037_copias_partes.py`: §12. R18-R19: `test_f002_fuente_unica.py` y
  revisión del `git diff` (reviewer).

### 9.2 Tests anteriores que cambian (lista cerrada, comprobada el 2026-10-06)

Comprobado leyendo cada doble frente a lo que el pipeline nuevo llama
(`ClienteFalso` de `conftest.py` y su subclase de F-022 y F-026, el doble de
`test_pipeline_offline.py`, `SigridFalsaApp` de F-022/F-024) y con la suite
del transfer en verde hoy (379 pasan):

1. `tests/conftest.py`, **solo el doble y sus datos**: `cenide` en las cuatro
   obras; `caa_cod` en MENC (`00000.CIMO03`) y MJEFO (`00000.CIMO02`);
   métodos `cuentas_de_centro`, `partidas_de_lineas` (vacío) y
   `partes_del_periodo` (deriva de `self.parte` **en cada llamada**:
   `[ParteSigrid(ide, cod, 1)]` si existe, si no `[]`; la subclase de F-022
   lo actualiza al crear, y la relectura de `test_f022_r17_pipeline_…` ve el
   parte nuevo);
   `siguiente_cod_pt(self, ano, empresa=None)`. Ningún assert cambia: ninguna
   acción anterior gana aviso (`test_f013_r1_…` compara el aviso entero).
2. `tests/test_pipeline_offline.py`: los mismos métodos y firma en su doble.
   Ningún assert cambia.
3. `tests/test_f002_fuente_unica.py`: `"regla-analitica"` en `ANCLAS`.

Sin tocar: `test_f022_r17` (los seis primeros parámetros del `con` no
cambian), `test_f026_r19/r20` (ninguna SQL con `conide`), `test_f024_r21`,
`test_f025` (sus contadores no cuentan las lecturas nuevas) y el resto.

## 10. Mutación (rigor crítico)

Campaña completa sobre las líneas cambiadas de las dos copias,
`registro_pipeline.py` y `sigrid_write_client.py`. Deben salir muertos: tipo
escrito > defecto > partida; `CI`/`CD`; el `> 1` de la ambigüedad;
`est != est_registro`; «mayor `ide`»; el choque con cerrado; el `emp` del
correlativo y del `hmo`; las dos condiciones del alta; el reintento único.

## 11. Riesgos

- **La rama de `partes` se mueve** (de `9b202e9` a `5ff4d91` durante la
  revisión): §12 dice cómo se sigue.
- **D17 (decidida)**: la mitigación solo cubre nuestro lado; `partes` puede crear su
  parte justo después de nuestra comprobación. Hay que avisarles.
- **Synckeys ajenas**: para `partes` nuestras líneas son ajenas y viceversa.
  Escribimos `M*` el último día del mes y `partes` manda los `M*` a
  dedicación (su F-019): en la práctica no chocan.
- **El texto de `motivo_choque`** dice «dia y tipo» (identidad de `partes`);
  la nuestra es recurso, mes, hora y partida (P4). Se acepta por ser copia.
- **Modo real activo**: hasta desplegar, `caaide = 0` (hoy 0 líneas).

## 12. Fuente de la copia y anti-divergencia

- **Copia**: `estado_parte.py` y `cuenta_analitica.py` de
  `services/partes-transfer/application/services/` en la rama
  `feature/F-031-asiento-analitico`: su contenido es el de **`9b202e9`**
  (T6; `estado_parte.py` desde `b205681`), igual en la punta `5ff4d91` del
  2026-10-06. Sin cambiar ni una línea (la primera ya coincide). El commit
  copiado se anota en `progress/impl_F-037.md` y en la constante del test.
  Lo que en `partes` aún no tiene código (pipeline, pasos 5, 7 y 9) se escribe
  aquí siguiendo su design §7.3, §7.4 y §9.
- **Test anti-divergencia** (`test_f037_copias_partes.py`): `git -C
  C:\Users\pgris\PycharmProjects\partes show <ref>:<ruta>` de los dos ficheros
  y comparación byte a byte con los nuestros. `<ref>` es la rama
  `feature/F-031-asiento-analitico` **hasta que F-031 llegue a `dev` de
  `partes`**; entonces se cambia a `dev` en el mismo trabajo. Sin el
  repositorio o sin la ref: `skip` con motivo (no hay red).
- **Si falla**: se mira el diff. Si es estilo o texto, se recopia, se anota el
  commit nuevo y se pasa la suite. Si cambia la regla (estado, elección,
  respaldo, contrato), **se para** y se avisa al líder antes de recopiar:
  puede obligar a revisar esta spec. Al revés, quien corrija aquí una copia
  avisa a `partes` (regla de `CLAUDE.md`).
- **Lo medido en `partes`** que sostiene la regla: 99,64 % de coincidencia de
  F-021; respaldo de partida en 478 de 544 líneas sin cuenta del recurso;
  estados de `conest` 1/3/10; 7 complementarios de Administración como «un
  parte más» con `Parte <obra>`; sus M1-M5 aún sin hacer (R20-R21 las cubren
  para `dedicacion`).
