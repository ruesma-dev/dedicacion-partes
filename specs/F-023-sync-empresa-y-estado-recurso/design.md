<!-- specs/F-023-sync-empresa-y-estado-recurso/design.md -->
# F-023 · Diseño — Empresa en los maestros y activo según el estado del recurso

Requisitos: `requirements.md`. Rutas relativas a `services/dedicacion-api/`
salvo que se diga otra cosa.

## 0. Encaje y límite de servicio

Todo vive en `dedicacion-api`, que ya es el dueño de los maestros
(`docs/ARCHITECTURE.md` «dedicacion-api — el dueño del dato»). El cambio
recorre las capas en su sentido normal:

- `config/config.yaml` — las dos consultas (datos versionados, no código).
- `application/filtros_maestros.py` — la depuración, **función pura**: aquí
  van todas las reglas nuevas, porque es lo que se prueba sin red ni BBDD.
- `application/sync_pipeline.py` y `application/use_cases.py::PreviewSync` —
  pasan la configuración y publican los recuentos.
- `infrastructure/db/orm_models.py` + `repositories.py` — columna y upsert.
- `domain/models.py` — `empresa` en `Trabajador` y `Obra`.

Sin responsabilidades nuevas fuera del servicio. No se consume ninguna tabla
nueva de Sigrid (`con`, `conest`, `res`, `emphis` ya se leían), así que
`docs/INTEGRACION.md` y `azure-apps/dedicacion.md` **no cambian**.

## 1. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `infrastructure/db/orm_models.py` | `empresa: Mapped[int \| None] = mapped_column(Integer)` en `TrabajadorORM` y `ObraORM`, tras `activo` / `activa`. Nulable y sin default (§7). Sin índice: el que haga falta para filtrar lo decide F-024. |
| `domain/models.py` | `empresa: int \| None = None` como **último** campo de `Trabajador` y `Obra` (tiene default, no rompe constructores existentes). |
| `infrastructure/db/repositories.py` | `sincronizar` de trabajadores y obras: escribir `empresa` en alta y en actualización; incluir `existente.empresa != _entero(fila.get("empresa"))` en `cambio`. Nuevo helper `_entero(valor) -> int \| None`. `_a_trabajador` / `_a_obra` mapean `empresa`. `listar_para_periodo` **no cambia**. |
| `config/config.yaml` | Consultas de §3; claves nuevas `filtro_estado_recurso`, `estados_recurso_excluidos` (vacía, D1) y `excluir_recurso_con_fecha_baja` (`false` al implementar; **`true` desde que D1 se cerró el 2026-10-01**, T9) bajo `sync.empleados`, con comentario que cite `sigrid_tablas.md` l. 5657-5658 y 6083-6089. |
| `application/filtros_maestros.py` | §2. |
| `application/sync_pipeline.py` | `FetchEmpleadosStep` recibe `criterio: CriterioActivoRecurso`; exige columnas `{"ide", "nombre", "empresa"}`. `FetchObrasStep` exige `{"ide", "cod", "empresa"}`. El log de empleados añade los tres recuentos nuevos. |
| `application/use_cases.py` | `PreviewSync` recibe `criterio`, valida columnas igual que el pipeline (R6: reutiliza `_validar_columnas`, que pasa a importarse de `sync_pipeline`) y publica las claves de R17. |
| `interface_adapters/api/deps.py` | Lee las tres claves nuevas, construye **un** `CriterioActivoRecurso` y se lo pasa al step y al preview (R18: mismo objeto). |

## 2. `application/filtros_maestros.py`

```python
@dataclass(frozen=True)
class CriterioActivoRecurso:
    estados_excluidos: tuple[str, ...] = ()
    excluir_con_fecha_baja: bool = False
    activo: bool = True           # filtro_estado_recurso

def depurar_empleados(filas, categorias_incluidas, filtro_activo,
                      exigir_codigo_mes=True,
                      criterio: CriterioActivoRecurso = CriterioActivoRecurso()
                      ) -> ResultadoDepuracion
```

`ResultadoDepuracion` gana tres campos: `excluidos_otra_empresa: int = 0`,
`excluidos_estado_recurso: Counter` y `con_baja_laboral: int = 0`.

Orden nuevo de `depurar_empleados` (R14):

0. **Fila a fila, antes de todo:**
   - `empresa_recurso` no nula y `!= empresa` → descarte, `excluidos_otra_empresa += 1` (R9);
   - si `criterio.activo`: `normalizar(estado_recurso)` contiene un literal
     normalizado de `estados_excluidos` → descarte, contado bajo el literal
     original (R12); si `excluir_con_fecha_baja` y `_entero(baja_recurso) > 0`
     → descarte bajo `"(fecha de baja del recurso)"` (R13). Mismo criterio de
     subcadena normalizada que `depurar_obras`, a propósito.
1. Dedupe por empleado (`ide`) — sin cambios.
2. Dedupe por persona: `_clave_persona` pasa a devolver
   `f"{empresa}|dni:..."` / `f"{empresa}|nom:..."` (R10, R11). Con `empresa`
   nula la clave empieza por `"None|"`: no se mezcla con ninguna empresa.
3. Código de hora mensual y categoría — sin cambios.
4. Por cada fila incluida con `_entero(baja_laboral) > 0`: `con_baja_laboral += 1` (R15).

`limpia.pop(...)` retira también `empresa_recurso`, `estado_recurso`,
`baja_recurso` y `baja_laboral`: el upsert solo recibe lo que persiste.
`empresa` **se queda**.

`depurar_obras` **no cambia** (F-025).

## 3. SQL contra Sigrid (`config/config.yaml`)

Capa: consultas de lectura vía `sigrid-api`, base configurada
(`SIGRID_API_DATABASE`). Sin parámetros de usuario: no hay nada que
concatenar.

**Obras** — la actual más `con.emp AS empresa`; `ORDER BY con.emp, con.cod`.
El filtro por estado de obra no se toca.

**Empleados** — sigue partiendo de `dbo.emp` (el eje recurso es F-026):

```sql
SELECT emp.ide  AS ide,      con.cod AS cod,      con.res AS nombre,
       emp.dni  AS dni,      con.emp AS empresa,
       tip.res  AS categoria, res.ide AS recurso_ide,
       rcon.emp AS empresa_recurso,
       COALESCE(rest.res, CAST(rcon.est AS VARCHAR(16))) AS estado_recurso,
       rcon.fecbaj AS baja_recurso,
       uh.fecbaj   AS baja_laboral,
       hm.cod AS cod_hora_mes, hm.pre AS importe_mes
FROM dbo.emp AS emp
JOIN dbo.con AS con ON con.ide = emp.ide
OUTER APPLY (SELECT TOP 1 h.fecbaj FROM dbo.emphis AS h
             WHERE h.empide = emp.ide ORDER BY h.fec DESC, h.ide DESC) AS uh
LEFT JOIN dbo.res  AS res  ON res.conide = emp.ide
LEFT JOIN dbo.con  AS rcon ON rcon.ide = res.ide
LEFT JOIN dbo.conest AS rest ON rest.tip = rcon.tip AND rest.est = rcon.est
LEFT JOIN dbo.auxrestip AS tip ON tip.ide = res.restipide
OUTER APPLY (...hm igual que hoy...) AS hm
ORDER BY con.emp, con.res, res.ide
```

Sin `WHERE` (R5, D3). Un empleado sin recurso trae `rcon.*` a NULL: no se
descarta por estado ni por empresa, y cae después por no tener código `M*`,
como hoy.

## 4. Consultas de confirmación (SOLO LECTURA, las lanza el humano)

Por `POST /api/sql/read` contra `ruesma_rep`. Ningún agente las ejecuta.

**Q1 — cierra D1** (no lanzada: la D1 se cerró el 2026-10-01 sin ella). Estados reales de los recursos de la empresa 1 y su
relación con la fecha de baja:

```sql
SELECT rcon.tip, rcon.est, est.cod, est.res AS literal,
       CASE WHEN COALESCE(rcon.fecbaj, 0) = 0 THEN 0 ELSE 1 END AS con_fecha_baja,
       COUNT(*) AS n
FROM dbo.res AS res
JOIN dbo.con AS rcon ON rcon.ide = res.ide
LEFT JOIN dbo.conest AS est ON est.tip = rcon.tip AND est.est = rcon.est
WHERE rcon.emp = 1
GROUP BY rcon.tip, rcon.est, est.cod, est.res,
         CASE WHEN COALESCE(rcon.fecbaj, 0) = 0 THEN 0 ELSE 1 END
ORDER BY rcon.tip, rcon.est
```

Lectura: si hay un literal que solo aparece con `con_fecha_baja = 1`, ese es
el estado de baja y `est` basta; si aparecen recursos con fecha de baja en un
estado «activo», hace falta además `excluir_recurso_con_fecha_baja: true`.

**Q2 — R19.** Los recursos que señaló negocio (lista D5), uno a uno:
`SELECT rcon.cod, rcon.emp, rcon.est, est.res, rcon.fecbaj FROM dbo.res res
JOIN dbo.con rcon ON rcon.ide = res.ide LEFT JOIN dbo.conest est ON est.tip =
rcon.tip AND est.est = rcon.est WHERE rcon.emp = 1 AND rcon.cod IN (...)`.

## 5. Ficheros que NO se tocan

- `services/dedicacion-front/**` — `empresa` no se expone aún (F-024).
- `services/dedicacion-transfer/**` — incluido `obra_por_codigo` sin empresa
  (explore §D): es de F-022/F-024.
- `interface_adapters/api/schemas.py` y `routes.py` — las respuestas no
  cambian; el preview devuelve un `dict` que ya pasa tal cual.
- `infrastructure/db/esquema.py` y `main.py` — el mecanismo de F-003 ya
  deriva el DDL; solo se usa.
- `depurar_obras`, `estados_excluidos` de obras, `registro_sigrid.py`.
- `infrastructure/sigrid/sigrid_client.py` — sin paginación (D6).

## 6. Tests (offline, `tests/test_f023_sync_empresa.py`)

Todos sin red ni BBDD: fixtures de filas como dicts, un `SigridGateway`
falso que devuelve listas, y una **sesión doble** para el repositorio (patrón
de `tests/test_f003_esquema.py`: `scalars(...).all()` devuelve las filas
previas y `add` las captura).

| Test | R |
|---|---|
| columna `empresa` en ambos ORM, `INTEGER`, nulable, sin default | R1 |
| `alters_faltantes` sobre base sin `empresa` = las dos cadenas exactas | R2 |
| `config.yaml` cargado: alias `empresa` en obras; los cinco alias en empleados; sin `COALESCE(uh.fecbaj` | R3-R5 |
| step y preview con filas sin `empresa` → `ValueError` con el nombre | R6 |
| repo de obras: dos filas mismo `cod`, empresas 1 y 28 → dos `ObraORM` con su empresa | R7 |
| repo: alta con empresa; existente con otra empresa → `actualizados == 1` | R8 |
| `empresa_recurso != empresa` → fuera y contado | R9 |
| mismo DNI misma empresa → 1; mismo DNI empresas 1 y 18 → 2; ídem sin DNI por nombre | R10, R11 |
| estado excluido → fuera, contado por literal original; con acentos/mayúsculas | R12 |
| `baja_recurso > 0` con interruptor on → fuera; off → dentro | R13 |
| empleado con recurso inactivo (ide mayor) y activo → entra con el activo | R14 |
| `baja_laboral > 0` y recurso activo → dentro y `con_baja_laboral == 1` | R15 |
| criterio vacío → mismos netos que sin criterio | R16 |
| preview: claves nuevas y antiguas presentes con valores esperados | R17 |
| mismas filas por pipeline (upsert espía) y por preview → mismos netos | R18 |

R19 es **MANUAL** (tasks T10).

## 7. Riesgos y decisiones

- **Filtrar en Python, no en SQL.** Filtrar estado y empresa en la consulta
  sería más barato, pero el preview no podría contar los excluidos
  (acceptance) ni se podría probar offline. Descartado.
- **Criterio en configuración, no en código.** Los valores de estado no están
  en el diccionario (D1): meterlos en código sería inventarlos. Con la lista
  vacía el comportamiento es el de «nadie inactivo por estado» (R16), que es
  un estado seguro y visible en el preview.
- **Empresa del trabajador = la de su ficha `emp`** (D2). Mantener
  `trabajador.ide = emp.ide` exige que cada `emp` tenga una sola empresa, y la
  ficha solo tiene una. Descartar los recursos de otra empresa (R9) evita que
  una ficha de Ruesma se registre con un recurso de UTE. Descartada «empresa
  del recurso»: con el eje `emp` un mismo `ide` podría acabar con dos
  empresas y chocar en la PK. **F-026** puede cambiar el eje; ver D2.
- **Columna nulable.** `NOT NULL` sin default aborta en
  `alters_faltantes` (F-003 R12) sobre una tabla con filas. Las filas previas
  quedan a NULL hasta el siguiente sync, que las rellena.
- **Duplicados visibles hasta F-024** (D4) y **volumen** (D6): ver
  requirements.
- **Trabajadores desactivados con líneas** siguen saliendo en su periodo
  (`repositories.py` `listar_para_periodo`): es deliberado y no cambia.
