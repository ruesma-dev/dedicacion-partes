<!-- specs/F-026-recursos-sin-ficha-empleado/design.md -->
# F-026 · Diseño técnico

Requisitos: [`requirements.md`](requirements.md). D1-D7 validadas por el humano
el 2026-10-02 (D1 y D3 reescritas a petición suya).

## 1. Límite de servicio y encaje con F-034

| Servicio | Qué hace en F-026 | Por qué ahí |
|---|---|---|
| `dedicacion-api` | sync desde `res`, vigencia por mes, `recurso_ide` en la línea | dueño del maestro y de qué se registra |
| `dedicacion-transfer` | deja de resolver el recurso; fuera `empleado_ide` | la elección es del dueño del dato, no de la pluma |
| `infra/` | script de vaciado de la base `dedicacion` (D1) | operación de despliegue, la ejecuta una persona |
| `dedicacion-front` | **nada** | la fila sigue llamándose por `ide` y `activo` |

Sin servicio nuevo ni lógica copiada. **F-034** reescribe la empresa de la
línea en `registro_sigrid._payloads`, la función que F-026 toca: T0 trae `dev`
**con F-034 mergeada** o la feature se para (`blocked`). `visible_en_empresa`
no cambia: lee `trabajador.empresa`, que pasa a ser la del recurso.

## 2. Datos que sostienen el diseño (data mart, solo lectura, 2026-10-01)

- `res.cla`: 1 PERSONA, 0 CONSUMO, 2 MEDIO (`personal/01_recursos.sql`); con
  `M*` quedan fuera, como hoy, 57 vehículos, un suministro y un `MJG` consumo.
- Personas M\* sin baja: 1 → 182 (10 sin ficha), 18 → 8 (4 sin), 25 → 1 (sin),
  31 → 4; hoy activos 171 / 4 / 0 / 4: Eusebio y sus nueve más el par
  `MO/0061`-`MO/0736`, que hoy se funde por DNI. 5 personas con recurso en la 1
  y en la 18 o la 31 (`1-MO/0496`, `18-MO/0006`): dos filas, dos 100 % (R3).
- Para los 180 válidos con ficha, el recurso que elegía el transfer por
  `res.conide` **es** su `res.ide`. Fechas: `AAAAMMDD`, 0 = nulo
  (`azure-apps/sigrid_api.md`). Volumen ~1.354, bajo `SIGRID_MAX_ROWS=5000`.

## 3. Ficheros a crear

`api/` = `services/dedicacion-api/`, `transfer/` = `services/dedicacion-transfer/`.
`api/domain/vigencia.py` (§5.2), `infra/vaciar_datos_prueba_dedicacion.ps1`
(§5.6; UTF-8 con BOM, CRLF y texto ASCII, como `crear_base_*.ps1`) y, sin red
ni BBDD: `api/tests/test_f026_sync_recurso.py` (R1-R6, R13, R17, sobre el
`config.yaml` real), `api/tests/test_f026_vigencia.py` (R7-R9, R12, R14, R15;
sesión falsa de F-023), `api/tests/test_f026_registro_recurso.py` (R16, R18;
dobles de F-024), `tests/test_f026_vaciado.py` (R10, R11: lee el `.ps1` como
texto) y `transfer/tests/test_f026_recurso_dado.py` (R19-R22, doble de
`conftest.py` y contrato por `TestClient`).

## 4. Ficheros a modificar

Además de los tests de §7 (lista cerrada):

| Fichero | Cambio |
|---|---|
| `api/config/config.yaml` | SQL nueva (§6); `excluir_recurso_con_fecha_baja` → `excluir_baja_anterior_a_ventana`; comentarios |
| `api/application/filtros_maestros.py` | `depurar_empleados` sin dedupes ni filtro de empresa, con ventana; `posible_misma_persona` (§5.1) |
| `api/application/sync_pipeline.py` | `FetchEmpleadosStep` calcula la ventana (reloj inyectable) |
| `api/application/use_cases.py` | solo `PreviewSync` (§5.3) |
| `api/domain/models.py`, `api/infrastructure/db/orm_models.py` | `Trabajador.fecha_baja: int \| None = None`; `TrabajadorORM.fecha_baja` (R8) |
| `api/infrastructure/db/repositories.py` | `sincronizar` guarda `fecha_baja`; `listar_para_periodo` con vigencia (§5.3); `_a_trabajador` |
| `api/interface_adapters/api/deps.py` | criterio con la clave nueva; fábrica de UoW y reloj para `PreviewSync` |
| `api/application/registro_sigrid.py` | `recurso_ide` en la línea, fuera `empleado_ide`; `no_vigentes` (§5.4) |
| `transfer/domain/models/registro_models.py`, `transfer/interface_adapters/api/app.py` | fuera `empleado_ide` de `LineaEntrada`, `AccionLinea` y `LineaIn` |
| `transfer/application/pipelines/registro_pipeline.py`, `transfer/application/services/reglas_porcentajes.py`, `transfer/infrastructure/sigrid/sigrid_write_client.py` | `_resolver_recursos` → `_horas_de_lineas` y docstring del paso 2; texto de `MOTIVO_SIN_RECURSO` y `base` sin `empleado_ide`; se retira `recursos_de_empleados` |
| `transfer/prueba_escritura_porcentajes.py`, `transfer/README.md` | `recurso_ide` en ejemplos y contrato |
| `transfer/tests/test_f002_fuente_unica.py` | `ANCLAS` gana `regla-recurso` |
| `infra/README_dedicacion.md` | paso del vaciado en el despliegue de F-026 y fila en §7 |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | §8 (R23) |

## 5. Clases y funciones

### 5.1 `filtros_maestros.depurar_empleados` (application)

Firma + `baja_desde: int | None = None` (la ventana, `AAAAMMDD`). Pasos: (0)
fila a fila, recurso inactivo según `CriterioActivoRecurso`; (1) sin `M*`,
fuera; (2) categoría opcional; (3) recuentos de `baja_laboral` y
`incluidos_con_baja`. `excluir_con_fecha_baja` pasa a
`excluir_baja_anterior_a_ventana`: con él y `baja_desde`, fuera la fila con
`0 < fecha_baja < baja_desde`, contada bajo `"(baja anterior a la ventana)"`.
**Desaparecen** el descarte por empresa del recurso y los dedupes por empleado
y por persona (R3, R6). `_AUXILIARES` = `("cif", "estado_recurso",
"baja_laboral")`: `fecha_baja` **se persiste**. `ResultadoDepuracion` pierde
`duplicados_recurso`, `duplicados_persona` y `excluidos_otra_empresa`, y gana
`incluidos_con_baja` y `posible_misma_persona: list[list[str]]`: grupos (≥ 2)
de `cod` incluidos con la misma `empresa` y el mismo documento normalizado
(`dni` o, si vacío, `cif`; sin espacios, guiones ni puntos; mayúsculas). Sin
documento no se agrupa (nunca por nombre: homónimos).

### 5.2 `domain/vigencia.py` (domain, puro)

- `inicio_de_mes(anio, mes) -> int`: `AAAAMM01`.
- `vigente_en(activo: bool, fecha_baja: int | None, anio, mes) -> bool`:
  `activo and (not fecha_baja or fecha_baja >= inicio_de_mes)` (R14). Única
  regla: la usan repositorio y registro.
- `inicio_ventana_baja(abiertos: Iterable[tuple[int, int]], hoy: date) -> int`:
  mínimo de `inicio_de_mes` del mes anterior a `hoy` (enero → diciembre del
  año anterior) y de cada `(anio, mes)` abierto (R12).

**Por qué esta ventana.** Cubre todo periodo donde se captura o registra
(los `ABIERTO`) y el mes anterior aunque aún no esté abierto (el que se
captura a primeros de mes); se ajusta sola. Descartadas: «solo el mes
anterior» (un periodo abierto más antiguo perdería sus bajas) y «toda la
historia» (filas muertas y empresas fantasma en el selector).

### 5.3 Repositorio y pipeline

- `sincronizar(filas)`: misma clave `ide`, ahora la del recurso (R7); alta y
  actualización guardan `fecha_baja` (0 → NULL) y su cambio cuenta como
  actualización; desactiva lo que no llega (R9).
- `listar_para_periodo(periodo_id)`: lee `anio`/`mes` del periodo; devuelve
  los vigentes más los que tengan líneas, con `activo = vigente_en(...)`
  (R15): front, `resumir`, copia del mes y export pasan a ser por mes sin
  tocarlos. `empresas_activas()` no cambia (cuenta `activo`, bajas de la
  ventana incluidas: una empresa con carga reciente no se oculta, F-032).
- `FetchEmpleadosStep(..., hoy: Callable[[], date] = date.today)`: ventana con
  los `(anio, mes)` `ABIERTO` de `uow.periodos.listar()`, pasada a
  `depurar_empleados`. `COLUMNAS_EMPLEADOS` sin cambio (R5).
- `PreviewSync(..., uow_factory: Callable[[], UnitOfWork] | None = None,
  hoy=date.today)`: con fábrica, una UoW **solo para leer** los periodos (sin
  `commit`); sin ella, ventana del mes anterior. Publica
  `empleados.ventana_baja`, `incluidos_con_baja` y `posible_misma_persona`;
  retira las claves de R6.

### 5.4 Registro (`registro_sigrid.py`)

Cada línea lleva `"recurso_ide": t.ide` y ya no `"empleado_ide"` (R18). Un
trabajador con `not vigente_en(t.activo, t.fecha_baja, anio, mes)` no genera
líneas: sus `a.id` salen en `"no_vigentes"` de la respuesta de `preflight` y
`ejecutar` (vacía si no hay), **sin `_trazar`** (R16): un `omitido` pisaría la
traza `registrado` de una asignación ya escrita.

### 5.5 Transfer

`_horas_de_lineas(lineas)`: `horas_de_recursos` de los `recurso_ide`
presentes, sin leer `res` ni tocar las líneas (R19). `MOTIVO_SIN_RECURSO =
"la línea no trae el recurso del trabajador"` (R20). `LineaIn` sin
`empleado_ide`: si un cliente viejo lo manda, Pydantic lo ignora (fijado por
test de contrato). Ninguna comprobación de empresa del recurso (R21).

### 5.6 `infra/vaciar_datos_prueba_dedicacion.ps1` (D1)

Patrón de `crear_base_dedicacion.ps1`: `param([switch] $Confirmar,
[switch] $Local)`. Sin `-Confirmar` imprime destino (`$PG`/`$PG_DB` o
`localhost/dedicacion`), la sentencia exacta y lo que no toca (`obra`,
`empresa`, otras bases, el servidor), y sale **antes de conectar**. Con
`-Confirmar`: contraseña del rol de aplicación `$PG_APP_USER` por `Read-Host
-AsSecureString` (nunca a disco; la del admin del servidor compartido no hace
falta: `GRANT ALL` incluye `TRUNCATE`), cuenta filas, ejecuta **una**
sentencia —`TRUNCATE TABLE asignacion, evento, periodo, trabajador CONTINUE
IDENTITY`— y vuelve a contar (0). Azure: `az postgres flexible-server execute
-d $PG_DB`; `-Local`: `psql -h localhost -d dedicacion` (sin `psql`, falla
diciéndolo). Sin `CASCADE`: van las cuatro tablas juntas.

## 6. SQL

Lectura contra Sigrid en `config.yaml` (campos de `res` según
`azure-apps/sigrid_tablas.md`); en PostgreSQL, ningún `NN_*.sql`: la columna
`fecha_baja` la deriva `esquema.py` del ORM (R8).

```sql
SELECT res.ide AS ide, rcon.cod AS cod, rcon.res AS nombre, emp.dni AS dni,
       res.cif AS cif, rcon.emp AS empresa, tip.res AS categoria,
       COALESCE(rest.res, CAST(rcon.est AS VARCHAR(16))) AS estado_recurso,
       NULLIF(rcon.fecbaj, 0) AS fecha_baja, uh.fecbaj AS baja_laboral,
       hm.cod AS cod_hora_mes, hm.pre AS importe_mes
FROM dbo.res AS res
JOIN dbo.con AS rcon ON rcon.ide = res.ide
LEFT JOIN dbo.emp AS emp ON emp.ide = res.conide AND res.conide > 0
OUTER APPLY (<el mismo TOP 1 de emphis de hoy, por emp.ide>) AS uh
LEFT JOIN dbo.conest AS rest ON rest.tip = rcon.tip AND rest.est = rcon.est
LEFT JOIN dbo.auxrestip AS tip ON tip.ide = res.restipide
OUTER APPLY (<el mismo TOP 1 M* de hoy sobre reshor/auxhor>) AS hm
WHERE res.cla = 1
ORDER BY rcon.emp, rcon.res, res.ide
```

## 7. Tests existentes que cambian (lista cerrada)

Se declaran en `progress/impl_F-026.md` (test, assert viejo y nuevo,
requisito); si aparece otro afectado, el implementer **para y avisa**.

- `test_f023_sync_empresa.py`: `r4` (alias) → `test_f026_r1_…`; `r5_config_…`
  y los dos `r13` (de «con fecha de baja» a «baja anterior a la ventana»);
  `AUXILIARES` y `_emp` (`fecha_baja` en vez de `baja_recurso`, sin
  `recurso_ide` ni `empresa_recurso`); **se retiran** los tres `r9`, `r10`,
  `r11` y `r14` (el filtro de empresa y los dedupes ya no existen), y los
  sustituyen `test_f026_r3_…` y `test_f026_r4_…`; `r17` (claves, R6);
  `r18_upsert_…` (lista nueva) y `r18_con_el_config_real_…` (ventana).
- `test_f032_empresas_sigrid.py` (fixture: `fecha_baja` por `baja_recurso`,
  sin `recurso_ide`), `test_f024_cuadrante_empresa.py`,
  `test_f022_empresa_en_linea.py`, `test_f024_registro_empresa.py` (o sus
  sucesores `test_f034_*`): dobles con `fecha_baja`; ningún assert cambia.
- Transfer: `conftest.linea()` pasa de `empleado_ide=10` a `recurso_ide=200`
  y los dobles pierden `recursos_de_empleados`; en `test_f002_reglas.py`,
  `test_f002_pipeline.py`, `test_f013_sin_partida.py`,
  `test_f022_obra_por_empresa.py` y `test_pipeline_offline.py` cada
  `empleado_ide=E` pasa al recurso de su doble (10→200, 11→300, 12→400) o se
  borra si ya iba con `recurso_ide`, sin tocar asserts. **Excepción:** la de
  `test_pipeline_offline.py` que fija `recurso_ide == 200` tras resolver por
  `res.conide` pasa a probar que el recurso dado se respeta (R19).

## 8. Documentación y despliegue

- `ARCHITECTURE.md`: punto 13 `#regla-recurso` (recurso persona M\*, clave
  `res.ide`; ficha opcional, solo DNI; una fila por recurso; vigencia por mes
  y ventana; la API manda el recurso), *decidido por Pablo Gris el 2026-10-01
  y el 2026-10-02 · F-026*. Se retiran «el recurso elegido sin mirar la
  empresa (F-026)» y la última frase de `#regla-empresa`; se ajustan «resolver
  el recurso de cada empleado» y «PK = el `ide` de Sigrid».
- `INTEGRACION.md`: cabecera, aviso de §8, contrato de la línea, «qué se
  rompe» (`res.cla`, `res.conide`, `res.cif`, `con.fecbaj`).
- **Despliegue (D7, MANUAL del humano)**: api y transfer **juntos y con
  F-034**: (1) desplegar (el arranque añade `fecha_baja`); (2) con
  autorización expresa, el vaciado (plan y `-Confirmar`); (3) `GET
  /sync/preview`; (4) `POST /sync`; solo entonces se registra. Si (2) se
  olvida, nada se escribe mal: las filas viejas se desactivan (R9) y sus
  líneas llevarían un `emp.ide` sin `reshor`, que P1 omite.

## 9. Fuera de alcance

Migrar o conservar los datos de `dedicacion` (D1: son pruebas); Alembic (esto
sigue siendo «añadir una columna nulable», F-003 §6); pedir a Administración
«Empleado asociado»; varios `M*` por recurso (F-011); que el transfer mire la
baja (la filtra la API, R16); retirar `estado_recurso`/`conest` inertes
(F-023); que abrir un periodo lance el sync (§10).

## 10. Riesgos y decisiones

- **Producción en real.** Cambia lo que se escribe solo en que entran 15
  recursos sin ficha, el par que ya no se funde y las bajas del mes; para los
  180 con ficha el recurso es el de hoy (§2). Nada lanza `ejecutar`.
- **Clave `ide` = `res.ide` (D1)**, frente a clave propia más `recurso_ide`:
  es el dato que necesita el transfer, es único en Sigrid (los `ide` de `con`
  no se repiten entre tipos), no cambia tipo ni FK de `asignacion` y `evento`
  y el front sigue igual. Sin DDL ni recrear tablas: basta vaciar.
- **Secuencias.** `RESTART IDENTITY` reutilizaría `asignacion.id` y, con él,
  `synckey` de líneas de prueba ya escritas en la obra `0404`: el transfer las
  daría por `ya_registrado` (R11). Por eso `CONTINUE IDENTITY`, explícito.
- **Ventana.** Un periodo abierto tras el último sync no tiene sus bajas hasta
  el siguiente (`#regla-recurso`: «tras abrir un periodo antiguo, sincronizar»).
  Una baja retroactiva anterior a la ventana desactiva el recurso (R9).
- **Visibles:** el nombre del recurso puede diferir del de la ficha (D6); la
  25 entra en el selector (F-024 R1) por su recurso válido.
- **Mutación (`critico`)**, sin tope, sobre las líneas cambiadas de §4.
  Esperables: `>=` frente a `>` en `vigente_en` y en la ventana, el mes
  anterior en enero, `res.conide > 0`, `no_vigentes`.

## 11. Ficheros que NO se tocan

`services/dedicacion-front/`, los `.env`, `esquema.py` (ya deriva el `ADD
COLUMN`), `domain/empresas.py` (F-034), `use_cases.py` salvo `PreviewSync`,
la estructura de `asignacion` y `evento`, `infra/` salvo el script y su
README; en el transfer, `campos_identidad`, capacidad, sin partida, postventa
y empresa.
