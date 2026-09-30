<!-- specs/F-022-transfer-obra-por-empresa/design.md -->
# F-022 · El transfer busca cada obra por código y empresa — diseño

## 1. Encaje y límite de servicio

- **`dedicacion-transfer`** es el único que resuelve obras en Sigrid para
  escribir: la regla vive aquí (cliente + pipeline + reglas).
- **`dedicacion-api`** solo **pone** la empresa en cada línea; no decide nada
  sobre obras de Sigrid.
- **`dedicacion-front`**: no se toca. Los campos nuevos de la respuesta
  (`empresa` en `obra_destino`/`obra_postventa`) son aditivos.
- Nada cruza a otro proyecto salvo la copia documental de
  `azure-apps/dedicacion.md` (su commit lo hace el humano, como en F-015 T6).
- Ninguna lógica se copia entre servicios. La lista de duplicados tolerados
  (`partida_*`, `text_match`) no se toca.

## 2. Flujo del preflight tras el cambio (`registro_pipeline.py`)

```
Paso 0  empresa = empresa_de_peticion(lineas)      # R4: >1 distinta -> EmpresasMezcladas
        si empresa es None -> todas omitidas (R3), sin leer Sigrid, fin
Paso 1  origen = _obra_origen(obra, empresa)        # R10/R12
        si origen.empresa != empresa -> todas omitidas (R11), fin
Paso 1a destino_normal = origen | obra de pruebas (cod, empresa)   # R13
Paso 1b destino_pv = obra de postventa (cod, empresa)              # R15/R16
Pasos 2-10 sin cambios (reglas, partes, idempotencia, conflictos, escritura)
```

Los dos «fin» anticipados construyen las acciones con el mismo
`ReglasPorcentajes.decidir` (omisión centralizada, §4.3) y devuelven un
`Preflight` con `obra_destino = obra` de entrada, `forzada_pruebas =
settings.obra_pruebas_forzar`, `partes = []`, `conflictos = []`. `ejecutar`
ya sale sin escribir cuando no hay acciones `escribir`: no cambia.

## 3. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/dedicacion-transfer/domain/errores.py` | `EmpresasMezcladas(ValueError)`, `ObraAmbigua(RuntimeError)` |
| `services/dedicacion-transfer/tests/test_f022_obra_por_empresa.py` | Tests offline R1-R19 (cliente, reglas, pipeline, app) |
| `services/dedicacion-api/tests/test_f022_empresa_en_linea.py` | Tests offline R20-R21 |

## 4. Ficheros a modificar

### 4.1 `domain/models/registro_models.py` (transfer, domain)

- `LineaEntrada.empresa: Optional[int] = None`.
- `ObraEntrada.empresa: Optional[int] = None` (la `con.emp` resuelta; `cenide`
  sigue como hoy, por `setattr`, fuera de alcance).

### 4.2 `infrastructure/sigrid/sigrid_write_client.py` (transfer, infrastructure)

- Constructor **sin** `empresa` (R5). `self._empresa` desaparece.
- `obra_por_codigo(self, cod: str, empresa: int) -> ObraEntrada | None`:
  `SELECT obr.ide, con.cod, con.res, obr.cenide, con.emp AS emp FROM obr JOIN
  con ON con.ide = obr.ide WHERE con.cod = ? AND con.emp = ?`, parámetros
  `[cod, int(empresa)]` (R6).
- `obra_por_ide(self, ide: int)`: añade `con.emp AS emp` al SELECT (R9).
- `_obra(filas, empresa: int | None = None)`: si `empresa` viene, **filtra en
  Python** `int(f["emp"]) == empresa` (defensa en profundidad: el test de R7
  devuelve las dos fichas aunque el SQL filtre, y el cliente debe acertar
  igual); 0 filas → `None`; >1 → `ObraAmbigua(f"obra {cod} ambigua: {n}
  fichas en la empresa {empresa}")`; 1 → `ObraEntrada(..., empresa=emp)`.
  Por `ide` se llama sin `empresa` (el `ide` es único) (R8).
- `stmts_crear_parte`: `con.emp` = `int(obra.empresa)` de la obra destino
  (R17). Si la obra no trae empresa → `ValueError` (no se adivina; es
  inalcanzable desde el pipeline, que siempre resuelve con empresa, y el test
  lo cubre llamando al método directamente).

### 4.3 `application/services/reglas_porcentajes.py` (transfer, application)

Constantes (caben en los 300 caracteres de `asignacion.sigrid_motivo`):

```python
MOTIVO_SIN_EMPRESA = ("la línea llega sin empresa: no se adivina a qué "
                      "empresa imputarla y no se escribe")
MOTIVO_EMPRESA_OBRA = ("la obra {cod} es de la empresa {emp_obra} y la línea "
                       "se imputa a la empresa {emp_linea}: no se escribe")
```

Funciones puras nuevas:

- `empresa_valida(valor) -> bool`: `int` > 0 (un `bool` no cuenta).
- `empresa_de_peticion(lineas) -> int | None`: conjunto de empresas válidas;
  vacío → `None`; uno → ese; más → `EmpresasMezcladas` con las empresas
  ordenadas en el mensaje (R4).

`ReglasPorcentajes.__init__` gana `motivo_empresa: Optional[str] = None`.
`decidir` añade, **antes** de la rama de postventa y en este orden:
(1) sin empresa válida → `omitir(MOTIVO_SIN_EMPRESA)` (R2);
(2) `self._motivo_empresa` → `omitir(self._motivo_empresa)` (R11).
El resto de `decidir` no cambia.

### 4.4 `application/pipelines/registro_pipeline.py` (transfer, application)

- Docstring de pasos: se añade el paso 0 y se **remite** a
  `ARCHITECTURE.md#regla-empresa` (sin reenunciarla).
- `_obra_origen(obra, empresa) -> ObraEntrada`: por `ide` →
  `obra_por_ide`; si no, por código → `obra_por_codigo(cod, empresa)`; no
  encontrada → `RuntimeError` como hoy, con la empresa en el mensaje (R10,
  R12). Se llama en **los dos modos**.
- `_obra_destino(origen, empresa) -> (ObraEntrada, bool)`: en pruebas,
  `obra_por_codigo(obra_pruebas_cod, empresa)`; `None` → `RuntimeError`
  «obra de pruebas {cod} no encontrada en la empresa {empresa}» (R13). Fuera
  de pruebas devuelve `origen`.
- `_destino_postventa(..., empresa)`: `obra_por_codigo(postventa_obra_cod,
  empresa)` dentro de `try/except ObraAmbigua`; `None` o ambigua → motivo
  que nombra código y empresa (R15, R16). Resto igual.
- Paso de partida normal (hoy líneas 223-231): usa `origen` del paso 1 en
  vez de volver a buscar la obra (R14).
- Sin literales de `POSTV2` ni `0404` ni de la empresa 1 (lo vigila
  `test_f002_fuente_unica.py` para el primero; los tests de F-022 para los
  otros dos).

### 4.5 `interface_adapters/api/app.py` (transfer)

- `LineaIn.empresa: Optional[int] = None` (opcional a propósito: la ausencia
  debe llegar al pipeline para omitirse con motivo, no morir en un 422 de
  pydantic) (R1).
- `SigridWriteClient(...)` sin `empresa=`.
- `preflight` y `ejecutar`: `except EmpresasMezcladas` **antes** del
  `except Exception` → `JSONResponse(422, {"ok": False, "error": str(exc)})`
  (R4). `ObraAmbigua` en la obra normal o de pruebas cae en el 502 genérico.
- Respuestas: `asdict(ObraEntrada)` ya incluye `empresa` (R18).

### 4.6 `config/settings.py` y `.env.example` (transfer)

Se retira `sigrid_empresa` / `SIGRID_EMPRESA` (R5, D4).

### 4.7 `prueba_escritura_porcentajes.py` (transfer, script manual)

Constante `EMPRESA_PRUEBA = 1` junto a `LINEAS_PRUEBA` (datos «EDITAR» como
los demás); cada línea de prueba lleva `empresa`; las búsquedas de la obra de
postventa y de pruebas pasan `EMPRESA_PRUEBA`; constructor sin `empresa=`.
No cambia ninguna fase ni ninguna salvaguarda del script.

### 4.8 `dedicacion-api`

- `config/settings.py`: `empresa_imputacion: Annotated[int, Field(gt=0)] = 1`
  (variable `EMPRESA_IMPUTACION`; `default` solo en la firma, CONVENTIONS)
  (R21). Comentario: puente hasta F-024.
- `application/registro_sigrid.py`: `RegistroSigrid.__init__(session_factory,
  transfer, empresa_imputacion: int)`; `_payloads` añade `"empresa":
  self._empresa` a cada línea (R20). F-024 cambiará **solo** de dónde sale
  ese valor.
- `interface_adapters/api/deps.py`: pasa `settings.empresa_imputacion`.
- `.env.example` de la API: `EMPRESA_IMPUTACION=1` con comentario.

### 4.9 Documentación

- `docs/ARCHITECTURE.md`: punto 12 `<a id="regla-empresa"></a>` «La obra se
  busca por código y empresa»: el código solo es único dentro de su empresa;
  la empresa viaja en la línea; sin empresa se omite; obra de otra empresa se
  omite; aplica a la obra de origen, a la de pruebas y a la de postventa; la
  cabecera del parte hereda la empresa de su obra. Una línea de remisión en
  el punto 5 (P5) y en el 9 (`#regla-pruebas`).
- `services/dedicacion-transfer/tests/test_f002_fuente_unica.py`: se añade
  `"regla-empresa"` a `ANCLAS` (única modificación del fichero).
- `services/dedicacion-transfer/README.md`: línea del contrato con `empresa`.
- `docs/INTEGRACION.md`: §3 (fuera `SIGRID_EMPRESA`, dentro
  `EMPRESA_IMPUTACION`), §9 un párrafo «una línea sin empresa no se
  registra», fecha y commit de origen.
- `infra/create_transfer_dedicacion.ps1`: fuera `"SIGRID_EMPRESA=1"` (D4).
- `C:\Users\pgris\PycharmProjects\azure-apps\dedicacion.md`: refresco de la
  copia desde `INTEGRACION.md` (cabecera propia intacta). Commit: el humano.

## 5. Ficheros que NO se tocan

- `services/dedicacion-front/**` (ni `app.js`: la empresa no la decide él).
- `partida_catalog.py`, `partida_matcher.py`, `text_match.py`,
  `partida_resolver.py`: el casado de partidas no cambia.
- `recursos_de_empleados` y `horas_de_recursos` (D5).
- `siguiente_cod_pt`, `partes_existentes`, `stmt_insert_linea` (la línea
  hereda la obra por `obride`; `hmores` no tiene empresa propia).
- `orm_models.py` / `esquema.py` de la API: F-022 **no** añade columnas; la
  empresa de obras y trabajadores es F-023.
- `services/dedicacion-api/config/config.yaml` (SQL de sync: F-023).

## 6. SQL

Sin SQL nuevo en PostgreSQL. En Sigrid (vía `sigrid-api`, solo lectura en
estas dos): la búsqueda por código gana `AND con.emp = ?` y ambas búsquedas
leen `con.emp AS emp`. Siguen incrustadas en el cliente del transfer, como
todas las de ese servicio (la regla del YAML de CONVENTIONS es de la API).
`con.emp` («Empresa», entero): `azure-apps/sigrid_tablas.md` (bloque `con`).

## 7. Tests (offline, sin red ni BBDD)

**Cliente** (`SigridWriteClient` con `_read` sustituido por un doble que
guarda `sql`/`params` y devuelve filas fijas):

- R6: el SQL contiene `con.emp = ?` y los parámetros son `[cod, empresa]`.
- R7: filas `POSTV2` emp 1 (ide 9001) y emp 28 (ide 9028), en orden
  `[1, 28]` y `[28, 1]`; pedir 1 → 9001 y pedir 28 → 9028 en los cuatro
  casos (`pytest.mark.parametrize`). El doble **ignora** el WHERE a
  propósito.
- R8: sin filas → `None`; dos filas de la misma empresa → `ObraAmbigua` con
  código, empresa y «2» en el mensaje.
- R9: `obra_por_ide` devuelve `empresa`.
- R17: `stmts_crear_parte` con obra de empresa 28 → primer parámetro 28; sin
  empresa → `ValueError`.
- R5: `inspect.signature` del constructor sin `empresa`; `obra_por_codigo`
  con `empresa` sin valor por defecto; `Settings` sin `sigrid_empresa`.

**Reglas**: `empresa_valida` con `None`, 0, -1, `True`, 1, 28;
`empresa_de_peticion` con vacío, `{1}`, `{1, None}`, `{1, 28}` (mensaje con
«1» y «28»); `decidir` con los dos motivos y el texto exacto formateado.

**Pipeline** (doble de cliente indexado por `(cod, empresa)` y por `ide`,
que **anota cada llamada**): R2 (una línea sin empresa omitida, la otra se
escribe); R3 (ninguna → cero búsquedas de obra); R10/R11 en los dos modos
(obra por `ide` de la 28, líneas de la 1 → todas omitidas, cero escrituras);
R12; R13 (0404 inexistente en la 28 → error con «0404» y «28»); R14 (una sola
búsqueda de la obra de origen); R15/R16 (POSTV2 de la 1 y de la 28 en el
doble: se elige la de la empresa pedida; inexistente → postventa omitida y
la normal se escribe); R17 vía `ejecutar` con parte nuevo; R18.

**App** (`TestClient`, `build_app` con ajustes falsos y `_read` sustituido):
R1 (el campo llega al dominio), R4 (422 sin ninguna lectura), R18.

**API** (`RegistroSigrid` con sesión falsa cuyo `execute(...).all()` devuelve
tuplas `(asignación, trabajador, obra)` de `SimpleNamespace` y transfer
falso que captura el payload): R20 con `empresa_imputacion` 1 y 28; R21 con
`Settings(EMPRESA_IMPUTACION=0)` y `"x"` → `ValidationError`, y sin
declararla → 1.

**Existentes**: los dobles de `conftest.py` y `test_pipeline_offline.py`
pasan a `obra_por_codigo(cod, empresa)` y sus obras y líneas llevan
`empresa=1`; ningún assert cambia (R19).

## 8. Riesgos y decisiones

- **Cambio de comportamiento en pruebas**: hoy el modo pruebas no resuelve la
  obra de origen; tras F-022 sí (R10). Una obra de origen inexistente pasa de
  «sin partida» a error. La API siempre manda `ide` de su maestro, así que no
  debería darse; se asume a cambio de validar en pruebas lo que valdrá en
  producción.
- **Filtro doble (SQL + Python)**: redundante a propósito. El de Python es el
  que hace comprobable R7 offline y el que protege si alguien toca el SQL.
- **Ambigüedad dentro de una empresa**: el data mart dice que no ocurre; se
  falla en vez de elegir (R8), porque elegir es lo que causó este defecto.
- **Mutación en rigor crítico** (0 supervivientes): el diseño evita ramas que
  ningún test pueda ejercitar. Riesgo: `prueba_escritura_porcentajes.py` no
  tiene tests; si la campaña lo incluye, sus supervivientes se justifican por
  escrito (script manual, sin llamada desde producción) para el humano.
- **Descartado**: empresa a nivel de petición (la decisión fija «en cada
  línea»); rechazar con 422 la línea sin empresa (perdería la traza en la
  asignación); elegir la ficha de Ruesma «por defecto» (es adivinar).
- Decisiones abiertas D1-D5: `requirements.md` § final.
