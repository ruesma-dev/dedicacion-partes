<!-- progress/explore_F-037_partes_F-031.md -->
# F-037 · Revisión de la F-031 de `partes` (rama en curso) para copiarla adaptada

Explorador de solo lectura, 2026-10-06, por encargo del líder tras la
instrucción del humano: «la f31 de partes ya in progress, revísalo, y copia
adaptándolo aquí a porcentajes (se usa el mismo parte realmente)». Leído con
`git show` en `C:\Users\pgris\PycharmProjects\partes`, rama
`feature/F-031-asiento-analitico`, punta **`9b202e9`** (2026-10-06 01:17; la
rama se movió durante la revisión). Rutas relativas a `services/partes-transfer/`.

## 0. Qué debe copiar o adaptar porcentajes (`services/dedicacion-transfer`)

Estado de la F-031: T1-T6 de 20 hechas. En código: las reglas puras
(`application/services/estado_parte.py` entero y el respaldo de la partida en
`application/services/cuenta_analitica.py`), modelos y dobles. Solo en su
design (§7.3, §7.4, §9): las lecturas `partes_del_periodo` y
`partidas_de_lineas` y los cambios del pipeline (pasos 4b, 5, 7 y 8). Su
pipeline sigue hoy eligiendo el parte de mayor `ide` sin mirar `con.est`.

1. **Cerrado = `con.est != EST_PARTE_ACTIVO` (1, «En registro»)**: Cerrado (3),
   Imputado (10) o cualquier otro. Confirmado por el humano el 2026-10-06. Un
   único predicado, en `elegir_parte`.
2. **Leer todos los partes del periodo**, una consulta por obra y mes:
   `SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo JOIN con ON
   con.ide = hmo.ide WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? AND
   ISNULL(hmo.reside, 0) = 0 AND con.tip = ? ORDER BY hmo.ide DESC`. Si falla
   o viene `truncated`, la petición falla entera sin escribir (su R15).
3. **Elegir el parte** (`elegir_parte`, copiar tal cual): gana el de mayor
   `ide` En registro aunque haya cerrados con `ide` mayor; si no hay ninguno En
   registro, se propone uno nuevo; `complementario = bool(cerrados)`. Con el
   mismo criterio, partes y porcentajes caen en el mismo parte y cada uno
   reutiliza el complementario que creó el otro (su R8).
4. **Crear el complementario** con el alta de hoy, sin campos nuevos ni enlace
   al original: `con` (emp = empresa de la obra, tip 35, est 1, cod
   `PT<AA>/NNNNN` correlativo **por empresa**, res = `Parte <obra.nombre o
   código>` + ` (MARCA_PRUEBAS)` en modo pruebas, fec = último día del mes) y
   `hmo` (mismo ide, cenide, obride, ano, mes, reside 0, cenmul 0). El original
   no se toca (ni UPDATE ni cambio de estado; R5, R31). **Releer** tras crear
   por el `cod` propuesto y estado En registro; si no aparece, fallar antes de
   insertar líneas (R9). Administración ya hace complementarios como «un parte
   más», `PT..` propio y descripción `Parte <obra>`: 7 periodos en 2024-26
   (`progress/spec_F-031.md` §D11 de partes).
5. **Duplicados y conflictos contra todos los partes del periodo:** synckey en
   cualquier parte, también cerrado → `ya_registrado`, sin escribir ni borrar
   (R10; `lineas_por_synckey` ya es global). `lineas_existentes` se lee en cada
   parte de `del_periodo`. Choque (recurso, día, `horide`) con línea ajena de un
   parte **cerrado** → `omitir` con motivo `parte_cerrado: ya hay horas de ese
   recurso, dia y tipo en el parte X (Cerrado); no se registran`, `caa_ide = 0`
   y resto de `caa_*` a None (R11, R14). Choque con línea ajena de un parte En
   registro → conflicto confirmable con el `parte_cod` donde vive (R11 prevalece
   sobre R12). `pisar_claves` solo borra en partes En registro (R13). Todo
   dentro del lock e igual en preflight y ejecución (R16).
6. **Cuenta analítica:** subcuenta de la ficha de horas del recurso
   (`subcuenta_de_linea`, F-021); si no da, la de la partida
   (`obrparpar.caaide`) **solo si empieza por CI o CD** (mayúsculas; nunca CP
   ni INGR); con ella, la `caa` del centro de la obra destino y su empresa
   (`resolver_cuenta`); sin cuenta, `caaide = 0`. Lectura de partidas una por
   petición, fuera del lock, sin try: `SELECT p.ide AS ide, p.cod AS cod, pc.cod
   AS caacod FROM obrparpar p LEFT JOIN con pc ON pc.ide = p.caaide AND
   ISNULL(p.caaide, 0) <> 0 WHERE p.ide IN (?, …)`. Una sola lectura de cuentas
   del centro con las subcuentas de ambos orígenes. Medida: de 544 líneas con
   recurso sin cuenta, 478 llevan la de la partida; cuando difieren, manda el
   recurso.
7. **Avisos del preflight** (mismo contrato si se quiere): cada parte con
   `estado`, `complementario`, `cerrados`, `del_periodo` y `aviso`; cada acción
   con `caa_origen` (`recurso` | `partida` | None) y `caa_nota`. Textos en ASCII
   sin tildes. Ejemplo de aviso: «el parte PT26/00004 (Imputado) de 01/2026 esta
   cerrado: las lineas van al parte complementario PT26/00350 (se creara)».
8. **Diferencias que YA tiene porcentajes y conviene alinear** (rama
   `feature/F-037-asiento-analitico-obra`, `services/dedicacion-transfer/
   infrastructure/sigrid/sigrid_write_client.py`):
   - `:178-197` `partes_existentes`: el SQL antiguo, sin `con.est`, mayor `ide`.
   - `:199-209` `siguiente_cod_pt(ano)`: **no filtra por `emp`** (partes sí
     desde su F-023: `WHERE cod LIKE ? AND emp = ?`).
   - `:302-306`: el `INSERT INTO hmo … WHERE cod = ? AND tip = ?` **no lleva
     `AND emp = ?`** (en partes sí).
   - `:312-329`: `caaide` siempre 0.
   - **Carrera entre servicios:** el lock de sv5 es un `threading.Lock` de su
     proceso; no protege frente a porcentajes. Los dos pueden calcular a la vez
     el mismo `PT<AA>/NNNNN` con `MAX(cod)` y crear dos complementarios. El
     `UPDLOCK, HOLDLOCK` solo cubre `MAX(ide)` de `con`. Ni la spec de partes ni
     la nuestra lo tratan.
   - **Synckeys ajenas:** partes solo reconoce el prefijo `partes:`; nuestras
     líneas son ajenas para ella (y viceversa). Si escribimos en un parte que
     luego se cierra, podrían provocarle `omitir` o conflictos cuando coincidan
     recurso, día y `horide`. Nosotros escribimos horas `M*` y partes las manda
     a dedicación (su F-019): en la práctica no deberían chocar.

## 1. Referencias en `partes` (rama `9b202e9`)

- Estado: `harness/features.json:396-410` (in_progress, crítico),
  `progress/current.md:4-36` (spec v4 aprobada 2026-10-06; T1-T6 hechas; 410
  passed tras T6), `progress/spec_F-031.md` (anexo §D1-§D11).
- Decisiones (`specs/F-031-asiento-analitico/design.md:158-189`): DA1/DA2
  complementario («juan ha dicho que si hay modificar un parte ya cerrado se
  hace con complementario»; cerrado = no En registro, confirmado 2026-10-06);
  DA3 contrapartida fuera (borrador a Juan); DA4 sv5 no contabiliza ni cambia
  estados; DA5 omitir con motivo; DA6 v4 la cuenta sale del recurso, respaldo
  C[ID]; DA7 estados como ajustes; DA8 herramienta de comprobación.
- Código: `application/services/estado_parte.py` (`:16` predicado, `:23`
  `MOTIVO_PARTE_CERRADO`, `:26-40` `elegir_parte`, `:43-50` `nombre_estado`,
  `:53-66` `aviso_de_parte`, `:69-73` `motivo_choque`);
  `domain/models/registro_models.py` (`:97` `ParteSigrid`, `:106`
  `PartidaCuenta`, `:115` `ParteDestino` ampliado, `:134` `AccionLinea` con
  `caa_origen`/`caa_nota`); `application/services/cuenta_analitica.py` (`:36`
  `SUBCUENTAS_COSTE_PARTIDA`, `:64-70` `subcuenta_de_partida`, `:74`
  `OrigenSubcuenta`, `:81-93` `origen_subcuenta`; `resolver_cuenta` e
  `indexar_cuentas` sin cambios).
- Pendiente de código en partes: T7-T8 cliente, T9-T10 pipeline de la cuenta,
  T11-T12 pipeline del parte (`EST_PARTE_CERRADO=3`, `EST_PARTE_IMPUTADO=10`
  solo para textos), T13-T20 front, herramienta, docs, mutación.
- Tests de referencia: `tests/test_f031_estado_parte.py` (R2 `:30-42`, R3
  `:59-64`, R4, R7, R18 textos `:90-120`, R11 `:125-131`),
  `tests/test_f031_cuenta_partida.py` (válidas e inválidas `:38-55`, R20-R22),
  `tests/test_f031_pipeline_estado.py` y `tests/test_f031_pipeline_cuenta_partida.py`
  (caracterización), `tests/dobles.py`.
- Pendiente de verificar en partes: M1-M5 (0696 enero 2026 PT26/00004
  Imputado con ANA26/00017; 0404 julio 2026 PT26/00296 sin asiento; modal en
  producción; modo pruebas; primer complementario contabilizado).
