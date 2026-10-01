<!-- specs/F-026-recursos-sin-ficha-empleado/design.md -->
# F-026 · Diseño técnico

Requisitos: [`requirements.md`](requirements.md). Asume D1-D7 tal como se
proponen; si el humano elige otra, se rehace lo afectado antes de implementar.

## 1. Límite de servicio y encaje con F-034

| Servicio | Qué hace en F-026 | Por qué ahí |
|---|---|---|
| `dedicacion-api` | sync desde `res`, adopción, `recurso_ide` en la línea | dueño del maestro y de qué se registra |
| `dedicacion-transfer` | deja de resolver el recurso; fuera `empleado_ide` | la elección es del dueño del dato, no de la pluma |
| `dedicacion-front` | **nada** | la fila del trabajador sigue llamándose por `ide` |

Sin servicio nuevo ni lógica copiada. **F-034** reescribe la empresa de la
línea en `registro_sigrid._payloads`, la función que F-026 toca: T0 trae `dev`
**con F-034 mergeada** o la feature se para (`blocked`). `visible_en_empresa`
no cambia: lee `trabajador.empresa`, que pasa a ser la del recurso.

## 2. Datos que sostienen el diseño (data mart, solo lectura, 2026-10-01)

- `res.cla`: 1 PERSONA, 0 CONSUMO, 2 MEDIO (ETL del data mart,
  `personal/01_recursos.sql`; `sigrid_tablas.md` solo dice «Clase, Byte»). Con
  `M*` y activos hay 57 vehículos (`MESVE`), un suministro (`MA`) y un «JEFE DE
  GRUPO» de clase consumo en la 25 (`MJG`: queda fuera, como hoy).
- Personas válidas: 1 → 182 (172 con ficha + 10 sin), 18 → 8 (4 + 4), 25 → 1
  (sin ficha), 31 → 4; hoy activos 171 / 4 / 0 / 4. En la 1 la diferencia es
  Eusebio y sus nueve más el par `MO/0061`-`MO/0736`, que hoy se funde por DNI.
- Ningún empleado tiene dos recursos válidos: la adopción no tiene ambigüedad
  hoy. 5 personas tienen recurso válido en la 1 y en la 18 o la 31 (p. ej.
  `1-MO/0496` y `18-MO/0006`): dos filas, cada una con su 100 % (R3).
- Para los 180 recursos válidos con ficha, el que elegía el transfer por
  `res.conide` (M* de `ide` mayor, cualquier empresa) **coincide** con el que
  adopta R10: lo ya registrado está sobre el recurso que se mandará.
- Volumen: ~1.354 personas, bajo `SIGRID_MAX_ROWS=5000` (`truncated` falla).

## 3. Ficheros a crear

`api/` = `services/dedicacion-api/`, `transfer/` = `services/dedicacion-transfer/`.
`api/application/adopcion_recurso.py` (§5.2) y, sin red ni BBDD:
`api/tests/test_f026_sync_recurso.py` (R1-R6, R13, sobre el `config.yaml` real),
`api/tests/test_f026_adopcion.py` (R7-R14, sesión falsa de F-023 y UoW espía),
`api/tests/test_f026_registro_recurso.py` (R15, R16, R21, dobles de F-024) y
`transfer/tests/test_f026_recurso_dado.py` (R17-R20, doble de `conftest.py` y
contrato por `TestClient`).

## 4. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `api/config/config.yaml` | SQL nueva (§6) y comentarios del bloque `empleados` |
| `api/application/filtros_maestros.py` | `depurar_empleados` sin dedupes ni filtro de empresa; `posible_misma_persona` (§5.1) |
| `api/application/sync_pipeline.py` | `COLUMNAS_EMPLEADOS`; `ctx.brutas_empleados`; `AdoptarRecursosStep` |
| `api/application/use_cases.py` | solo `PreviewSync` (§5.4) |
| `api/domain/models.py` | `Trabajador.recurso_ide`; `FilaLegada`; `ResultadoSyncMaestro.adoptados`, `.sin_recurso` |
| `api/domain/ports.py` | `TrabajadorRepository`: `legadas`, `recursos_asignados`, `adoptar` |
| `api/infrastructure/db/orm_models.py` | `TrabajadorORM.recurso_ide` (R7) |
| `api/infrastructure/db/repositories.py` | `sincronizar` por `recurso_ide`; métodos nuevos; `_a_trabajador` |
| `api/interface_adapters/api/deps.py` | compone `AdoptarRecursosStep`; fábrica de UoW para `PreviewSync` |
| `api/interface_adapters/api/schemas.py` | `SyncMaestroOut.adoptados`, `.sin_recurso` (por defecto 0) |
| `api/application/registro_sigrid.py` | `recurso_ide` en la línea, fuera `empleado_ide`; `sin_recurso` (§5.5) |
| `transfer/domain/models/registro_models.py` | fuera `empleado_ide` de `LineaEntrada` y `AccionLinea` |
| `transfer/interface_adapters/api/app.py` | fuera `empleado_ide` de `LineaIn` |
| `transfer/application/pipelines/registro_pipeline.py` | `_resolver_recursos` → `_horas_de_lineas`; docstring del paso 2 |
| `transfer/application/services/reglas_porcentajes.py` | texto de `MOTIVO_SIN_RECURSO`; `base` sin `empleado_ide` |
| `transfer/infrastructure/sigrid/sigrid_write_client.py` | se retira `recursos_de_empleados` |
| `transfer/prueba_escritura_porcentajes.py`, `transfer/README.md` | `recurso_ide` en las líneas de ejemplo y en el contrato |
| `transfer/tests/test_f002_fuente_unica.py` | `ANCLAS` gana `regla-recurso` |
| tests existentes | §7, lista cerrada |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | §8 (R22) |

## 5. Clases y funciones

### 5.1 `filtros_maestros.depurar_empleados` (application)

Misma firma. Pasos: (0) fila a fila, recurso inactivo según
`CriterioActivoRecurso` (sin cambio); (1) sin `M*`, fuera; (2) categoría
opcional; (3) recuento de `baja_laboral`. **Desaparecen** el descarte por
empresa del recurso y los dedupes por empleado y por persona (R3, R6).
`_AUXILIARES` = `("empleado_ide", "cif", "estado_recurso", "baja_recurso",
"baja_laboral")`: `recurso_ide` **se persiste**. `ResultadoDepuracion` pierde
`duplicados_recurso`, `duplicados_persona` y `excluidos_otra_empresa`, y gana
`posible_misma_persona: list[list[str]]`: grupos (≥ 2) de `cod` incluidos con
la misma `empresa` y el mismo documento normalizado (`dni` o, si vacío, `cif`;
sin espacios, guiones ni puntos; mayúsculas). Sin documento no se agrupa
(nunca por nombre: homónimos).

### 5.2 `application/adopcion_recurso.py` (application, puro)

```python
@dataclass(frozen=True)
class PlanAdopcion:
    adopciones: dict[int, int]       # ide de la fila legada -> recurso_ide
    sin_recurso: tuple[int, ...]     # filas legadas sin candidato

def planificar_adopcion(legadas: Iterable[FilaLegada], asignados: Set[int],
                        brutas: Iterable[Mapping[str, Any]]) -> PlanAdopcion
```

- `FilaLegada(ide, empresa, activo)` (dominio, `frozen`): `recurso_ide` NULL.
- Candidatos de `E`: brutas con `empleado_ide == E.ide` y `recurso_ide` ni en
  `asignados` ni elegido ya; si `E.empresa` no es NULL, solo de esa empresa.
- Se elige el mayor `(activo, tiene_M*, recurso_ide)`; `activo` =
  `baja_recurso` NULL o 0; `tiene_M*` con la regla de `_cod_mes`.
- Recorre las legadas por `ide` ascendente: resultado determinista.

### 5.3 Repositorio y pipeline

- `PgTrabajadorRepository.legadas() -> list[FilaLegada]`,
  `recursos_asignados() -> set[int]` y `adoptar(adopciones) -> int`, que solo
  asigna `orm.recurso_ide` (nunca `ide`, nunca otra tabla: R14).
- `sincronizar(filas)`: `actuales` por `recurso_ide` (no NULL); alta con
  `ide = recurso_ide`; actualiza como hoy; desactiva toda fila activa cuyo
  `recurso_ide` no llegó, **incluidas las legadas sin adoptar** (R11).
- `AdoptarRecursosStep` (entre `FetchEmpresasStep` y
  `UpsertTrabajadoresStep`): plan con `legadas()`, `recursos_asignados()` y
  `ctx.brutas_empleados` (filas **antes** de depurar, para adoptar también
  recursos de baja); `adoptar`; deja los dos contadores en el contexto y
  `ResultadoSync.empleados` los lleva. Misma transacción y un solo `commit`.

### 5.4 Preview

`PreviewSync(..., uow_factory: Callable[[], UnitOfWork] | None = None)`. Con
fábrica, abre una UoW **solo para leer** `legadas()` y
`recursos_asignados()` (sin `commit`) y publica `empleados.adopcion =
{legadas, adoptables, sin_recurso, sin_recurso_activas}` con el mismo
planificador; sin fábrica no publica el bloque. Claves: R4, R6.

### 5.5 Registro (`registro_sigrid.py`)

Cada línea lleva `"recurso_ide": t.recurso_ide` y ya no `"empleado_ide"`. Un
trabajador visible con `recurso_ide` NULL no genera líneas: sus `a.id` salen
en `"sin_recurso"` de la respuesta de `preflight` y `ejecutar` (vacía si no
hay), **sin `_trazar`** (R16): un `omitido` pisaría la traza `registrado` de
una asignación ya escrita. `Trabajador.recurso_ide: int | None = None` y
`_a_trabajador` lo mapea; `TrabajadorOut` no cambia.

### 5.6 Transfer

- `_horas_de_lineas(lineas)`: `horas_de_recursos` de los `recurso_ide`
  presentes; no lee `res` ni toca las líneas (R17).
- `MOTIVO_SIN_RECURSO = "la línea no trae el recurso del trabajador"` (R18).
- `LineaIn` sin `empleado_ide`: si un cliente viejo lo manda, Pydantic lo
  ignora (comportamiento por defecto, fijado por test de contrato).
- Ninguna comprobación de empresa del recurso (R19).

## 6. SQL

Lectura contra Sigrid en `config.yaml`; en PostgreSQL, ningún `NN_*.sql` (R7).

```sql
SELECT res.ide AS recurso_ide, NULLIF(res.conide, 0) AS empleado_ide,
       rcon.cod AS cod, rcon.res AS nombre, emp.dni AS dni, res.cif AS cif,
       rcon.emp AS empresa, tip.res AS categoria,
       COALESCE(rest.res, CAST(rcon.est AS VARCHAR(16))) AS estado_recurso,
       rcon.fecbaj AS baja_recurso, uh.fecbaj AS baja_laboral,
       hm.cod AS cod_hora_mes, hm.pre AS importe_mes
FROM dbo.res AS res
JOIN dbo.con AS rcon ON rcon.ide = res.ide
LEFT JOIN dbo.emp AS emp ON emp.ide = res.conide AND res.conide > 0
OUTER APPLY (SELECT TOP 1 h.fecbaj FROM dbo.emphis AS h
             WHERE h.empide = emp.ide ORDER BY h.fec DESC, h.ide DESC) AS uh
LEFT JOIN dbo.conest AS rest ON rest.tip = rcon.tip AND rest.est = rcon.est
LEFT JOIN dbo.auxrestip AS tip ON tip.ide = res.restipide
OUTER APPLY (<el mismo TOP 1 M* de hoy sobre reshor/auxhor>) AS hm
WHERE res.cla = 1
ORDER BY rcon.emp, rcon.res, res.ide
```

Campos de `res` según `azure-apps/sigrid_tablas.md` (`cla`, `cif`, `conide`,
`restipide`). `COLUMNAS_EMPLEADOS = {"recurso_ide", "nombre", "empresa"}`.

## 7. Tests existentes que cambian (lista cerrada)

Se declaran en `progress/impl_F-026.md` (test, assert viejo y nuevo,
requisito); si aparece otro afectado, el implementer **para y avisa**.

- `test_f023_sync_empresa.py`: `r4` (alias) → `test_f026_r1_…`; `r6`
  (requerida `recurso_ide` en vez de `ide`); `r8` (dobles con `recurso_ide`,
  `ide` del alta = recurso); **se retiran** los tres `r9`, los tres `r10`, los
  tres `r11` y `r14_recurso_de_otra_empresa…` (el filtro ya no existe), y los
  sustituyen `test_f026_r3_…` y `test_f026_r4_…`; `r17` (claves, R6);
  `r18_upsert_recibe_empresa_sin_columnas_auxiliares` (lista nueva).
- `test_f022_empresa_en_linea.py`, `test_f024_registro_empresa.py` (o sus
  sucesores `test_f034_*`): el trabajador de los dobles gana `recurso_ide`;
  ningún assert cambia.
- Transfer: `conftest.linea()` pasa de `empleado_ide=10` a `recurso_ide=200`
  (lo que resolvía el doble) y los dobles pierden `recursos_de_empleados`; en
  `test_f002_reglas.py`, `test_f002_pipeline.py`, `test_f013_sin_partida.py`,
  `test_f022_obra_por_empresa.py` y `test_pipeline_offline.py` cada
  `empleado_ide=E` pasa al recurso que resolvía su doble (10→200, 11→300,
  12→400) o se borra si ya iba con `recurso_ide`, sin tocar asserts.
  **Excepción:** la prueba de `test_pipeline_offline.py` que fija
  `recurso_ide == 200` tras resolver por `res.conide` pasa a probar que el
  recurso dado se respeta (R17).

## 8. Documentación y despliegue

- `ARCHITECTURE.md`: punto 13 `#regla-recurso` (trabajador = recurso válido;
  ficha opcional, solo DNI; una fila por recurso; la API manda el recurso y el
  transfer no lo elige; `ide` opaco, identidad = `recurso_ide`), con
  procedencia *decidido por Pablo Gris el 2026-10-01 · F-026*. Se retiran «el
  recurso elegido sin mirar la empresa (F-026)» del aviso de modo real y la
  última frase de `#regla-empresa`; se ajustan el paso «resolver el recurso de
  cada empleado» del transfer y «PK = el `ide` de Sigrid» de las tablas.
- `INTEGRACION.md`: cabecera, aviso de §8, contrato de la línea, «qué se
  rompe» (`res.cla`, `res.conide`, `res.cif`).
- **Despliegue (D7, MANUAL del humano)**: api y transfer **juntos**. Por
  separado ningún orden escribe en un recurso equivocado (api nueva + transfer
  viejo usa el recurso dado; api vieja + transfer nuevo lo omite todo), pero
  en el segundo la traza `omitido` pisaría `registrado`. Tras desplegar:
  copia de la base `dedicacion`; `GET /sync/preview` (esperado
  `adopcion.sin_recurso_activas` = 0); `POST /sync`; solo entonces se
  registra. Hasta el sync, R16 impide mandar líneas de filas legadas.

## 9. Fuera de alcance

- Pedir a Administración «Empleado asociado»; varios `M*` por recurso (F-011:
  hoy ninguno válido tiene dos); que el transfer mire la baja (D3); retirar
  `estado_recurso`/`conest` inertes (F-023); borrar legadas sin recurso.
- `UNIQUE` sobre `trabajador.recurso_ide`: `esquema.py` no crea índices en
  tablas existentes y crearlo solo en bases nuevas daría dos verdades. La
  unicidad la garantizan el planificador y `sincronizar` (con tests).

## 10. Riesgos y decisiones

- **Producción en real.** Cambia lo que se escribe solo en que entran 15
  recursos sin ficha (y el par que ya no se funde) y en que el recurso lo fija
  la API; para los 180 con ficha coincide con el de hoy (§2). Ninguna
  verificación lanza `ejecutar`; R24 usa el transfer local en modo pruebas.
- **Descartada (D1): reclavar `trabajador.ide`.** Mueve `asignacion` y
  `evento` y la PK con FK sin `ON UPDATE CASCADE` (inserta-mueve-borra): es
  «mover datos», el disparador de Alembic de F-003 §6. La adopción da la misma
  identidad sin tocar `asignacion`. El otro disparador de F-003 §6 («más de un
  entorno con la base») ya se cumple desde el despliegue: Alembic merece su
  propia feature.
- **Visibles:** el nombre del recurso puede diferir en formato del de la
  ficha (D6), y la 25 aparece en el selector (F-024 R1) por su recurso válido.
- **Mutación (`critico`)**, sin tope, sobre las líneas cambiadas de los
  ficheros de §4 con código. Esperables: orden de la tupla de preferencia,
  filtro por empresa de la legada, `asignados`, `res.conide > 0`.

## 11. Ficheros que NO se tocan

`services/dedicacion-front/`, `infra/`, los `.env`, `esquema.py` (ya deriva el
`ADD COLUMN`), `domain/empresas.py` (de F-034), `use_cases.py` salvo
`PreviewSync`, las tablas `asignacion` y `evento`; en el transfer,
`campos_identidad`, capacidad, sin partida, postventa y empresa.
