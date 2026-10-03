<!-- specs/F-034-obras-siempre-ruesma/design.md -->
# F-034 · Diseño técnico

Requisitos: [`requirements.md`](requirements.md). Regla de dominio:
[`docs/ARCHITECTURE.md#regla-empresa`](../../docs/ARCHITECTURE.md#regla-empresa).
El diseño asume las propuestas de D1-D5; si el humano elige otra, se rehace
la sección afectada antes de implementar. Base: el diseño de F-024
([`specs/F-024-selector-empresa/design.md`](../F-024-selector-empresa/design.md)),
del que aquí solo se cuenta lo que cambia.

## 1. Límite de servicio

| Servicio | Qué hace en F-034 | Por qué ahí |
|---|---|---|
| `dedicacion-api` | obras ofrecidas, visibilidad NULL, marca `otra_empresa`, empresa de cada línea | es quien decide la empresa de la línea desde F-024 |
| `dedicacion-front` | dos textos (aviso de la línea y `title` del selector) | presentación pura |
| `dedicacion-transfer` | **nada** | ya busca la obra por código y empresa de la línea y omite la de otra empresa; con `empresa = 1` en cada línea, una obra de Ruesma pasa y la `0404` y la `POSTV2` se buscan en la 1 |

Nada exige un servicio nuevo ni mueve lógica entre servicios.

## 2. Ficheros a crear

- `services/dedicacion-api/tests/test_f034_obras_siempre_ruesma.py` — R1,
  R3, R5, R7, R8, R10 sobre la UoW falsa de F-024 y la sesión/transfer
  falsos de `test_f024_registro_empresa.py` (importados o copiados en el
  propio fichero; sin red ni BBDD).
- `services/dedicacion-api/tests/test_f034_rutas.py` — R1 y R5 en la
  respuesta HTTP con `TestClient` y contenedor falso (como
  `test_f024_rutas_empresa.py`), con E = 1, 18 y 28.

## 3. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `dedicacion-api/domain/models.py` | `FiltroEmpresa` gana `empresa_obras: int` (obligatorio, sin valor por defecto) y su docstring |
| `dedicacion-api/domain/empresas.py` | `visible_en_empresa(empresa_trabajador, filtro)` sin `empresas_obras` (R3); docstrings con la regla nueva |
| `dedicacion-api/application/use_cases.py` | `ObtenerCuadrante`: obras con `o.empresa == filtro.empresa_obras` (R1); `_filas_de_empresa` llama a la firma nueva |
| `dedicacion-api/application/registro_sigrid.py` | `_filtro` rellena `empresa_obras`; `_payloads` sin `empresas_de` y con `"empresa": filtro.empresa_obras` (R7, R8) |
| `dedicacion-api/interface_adapters/api/routes.py` | `_filtro` rellena `empresa_obras`; `a_trabajador_out(…, filtro.empresa_obras)` en las cuatro rutas que lo llaman |
| `dedicacion-api/interface_adapters/api/schemas.py` | `a_trabajador_out(fila, empresa_obras)`: el segundo argumento cambia de nombre y de sentido (R5) |
| `dedicacion-api/config/settings.py`, `.env.example` | solo el comentario de `empresa_imputacion` (R10, R12) |
| `dedicacion-front/static/js/app.js` | texto del `title` de la línea `otra_empresa` (R6) |
| `dedicacion-front/templates/index.html` | `title="Empresa de los trabajadores"` en `#selector-empresa` (R6) |
| tests de F-022 y F-024 | §6, lista cerrada |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | §7 (R12) |

## 4. Clases y funciones

### 4.1 Dominio

```python
@dataclass(frozen=True)
class FiltroEmpresa:
    empresa: int        # E, la elegida: filtra trabajadores
    por_defecto: int    # EMPRESA_IMPUTACION: E si no llega; casa a los NULL
    empresa_obras: int  # EMPRESA_IMPUTACION (D1): obras ofrecidas y línea
```

```python
def visible_en_empresa(empresa_trabajador: int | None,
                       filtro: FiltroEmpresa) -> bool
```

- Con empresa: `empresa_trabajador == filtro.empresa` (R2, sin cambio).
- Con NULL: `filtro.empresa == filtro.por_defecto` (R3).

`linea_de_otra_empresa(obra_empresa, empresa)` **no cambia** de cuerpo ni de
firma: lo que cambia es quién la llama y con qué (§4.3). `empresa_de_baja`
no se toca.

### 4.2 Aplicación (`use_cases.py`)

- `_filas_de_empresa`: `visible_en_empresa(t.empresa, filtro)`. Sigue siendo
  el único punto del filtro de trabajadores; cuadrante, resumen y copia lo
  heredan (R4). La fila sigue llevando todas sus líneas.
- `ObtenerCuadrante.ejecutar`: `if o.empresa == filtro.empresa_obras` (R1).
  `Cuadrante.empresa` sigue siendo E (lo pinta el selector).
- Copias, guardar y deshacer: sin cambio de código.

### 4.3 Interfaz

- `routes._filtro(contenedor, empresa)`: `por_defecto = empresa_obras =
  contenedor.settings.empresa_imputacion` (D1).
- `schemas.a_trabajador_out(fila, empresa_obras)`: `otra_empresa =
  linea_de_otra_empresa(ln.obra_empresa, empresa_obras)` (R5). Las rutas le
  pasan `filtro.empresa_obras`, nunca `filtro.empresa` ni `cuadrante.empresa`.
- Ningún campo de entrada ni de salida cambia (`CuadranteOut`,
  `TrabajadorOut`, `LineaOut`, `EmpresasOut`): el front no necesita saber cuál
  es la empresa de las obras.

### 4.4 Registro (`registro_sigrid.py`)

- `_filtro(empresa)`: `FiltroEmpresa(empresa=empresa or d, por_defecto=d,
  empresa_obras=d)` con `d = self._por_defecto`. El constructor no cambia de
  firma; su comentario dice que el tercer argumento es la por defecto **y**
  la empresa de las obras.
- `_payloads`: desaparece el diccionario `empresas_de` (R3 ya no mira las
  obras); el filtro queda `visible_en_empresa(t.empresa, filtro)` y cada
  línea lleva `"empresa": filtro.empresa_obras` (R7). Las de obra de otra
  empresa se mandan igual (R8); `_trazar` no cambia.

## 5. SQL

Ninguno: ni consultas nuevas contra Sigrid, ni columnas, ni DDL.

## 6. Tests existentes que cambian

Lista **cerrada**. Cada cambio se declara en `progress/impl_F-034.md` (R11).
Cuando un assert pasa a probar un requisito de F-034, el test se renombra a
`test_f034_rN_…` y se queda en su fichero; ningún caso se borra sin su
equivalente.

- `test_f024_visibilidad.py`: todas las llamadas a `visible_en_empresa`
  pierden el argumento de obras y el helper `_f` construye `FiltroEmpresa`
  con `empresa_obras`. `test_f024_r8_trabajador_null_donde_tiene_carga` y
  `…_null_sin_obras_con_empresa_en_la_por_defecto` se funden en
  `test_f034_r3_trabajador_null_solo_en_la_por_defecto` (elegidas 1, 18 y
  28; visible solo con la 1). `…_acepta_cualquier_iterable_una_sola_vez`
  pierde el objeto: se sustituye por un caso de R3 con por defecto ≠ 1 (que
  la por defecto sale del filtro, no de un literal). La tabla de
  `linea_de_otra_empresa` no cambia.
- `test_f024_cuadrante_empresa.py`: `_f` con `empresa_obras = DEF`.
  `test_f024_r9_…` pasa a `test_f034_r1_obras_siempre_de_la_empresa_de_las_obras`
  (E = 1, 18 y 28 → `[100, 101, 102]`; la 900 de la 28 nunca). En R7, R10,
  R13 y R14 cambian **solo** los casos de trabajadores NULL (R3): dejan de
  verse en la 28 y se ven en la 1 (p. ej. Gil, NULL con carga en la 1 y la
  28, sale solo en la 1). `test_f024_r10_puede_deshacer_se_conserva` pasa de
  `[True, False, False, False]` a `[True, False, False, False, False]`
  (con E = 1 entra Carlos, NULL).
- `test_f024_registro_empresa.py`: R16 pasa a `test_f034_r7_…` con
  `None`/1 → `[(1,1),(2,1),(4,1),(5,1)]`, 28 → `[(3,1)]`, 18 → `[]` (la
  línea 4, del NULL con carga en la 28, pasa a la por defecto; todas con
  empresa 1). `test_f024_r17_…` **sí cambia** (R3): la obra 9 pasa de
  `[(2, 1)]` a `[(2, 1), (4, 1)]` porque el trabajador 12, NULL, pasa a verse
  en la 1; la traza de la omitida 2 no cambia. R18 y R19 no cambian de
  asserts; R19 actualiza su docstring (D4).
- `test_f024_rutas_empresa.py`: `test_f024_r11_otra_empresa_depende_de_la_elegida`
  pasa a `test_f034_r5_otra_empresa_no_depende_de_la_elegida`: Gil con E = 1
  da `[(1, False), (28, True)]`, y lo mismo para cualquier E en que sea
  visible. `test_f024_r6_con_empresa_la_elegida` (E = 28): obras `[900]` →
  `[100, 101, 102]` (R1), nombres `["Bea", "Carlos", "Gil"]` → `["Bea"]` y
  `resumen.total` `3` → `1` (R3).
  `test_f024_r6_r13_respuestas_por_fila_con_el_resumen_de_la_empresa`:
  parámetros `(None, 4), (1, 4), (28, 3)` → `(None, 5), (1, 5), (28, 1)`
  (R3). En el resto de R6/R13/R15 las listas de nombres cambian solo en los
  NULL, como arriba.
- `test_f022_empresa_en_linea.py`: **no cambia**. Construye
  `RegistroSigrid` con 1 o 28 y no pasa `empresa`: la línea lleva la empresa
  de las obras, que es ese mismo ajuste (R10).
- `dedicacion-front/tests/test_f024_selector.py::test_f024_r12_…`: el
  assert del texto «no se registrará en esta empresa» pasa a comprobar el
  texto nuevo y que el viejo ya no está; y se añade el `title` del selector.
- Transfer: **ningún test cambia** (R9).

## 7. Documentación (R12)

- `#regla-empresa` en `docs/ARCHITECTURE.md`, reescribiendo **solo** los
  puntos afectados: «La empresa viaja en cada línea» (es la empresa de las
  obras, `EMPRESA_IMPUTACION`, no la elegida); «Cada empresa ve lo suyo» →
  «El selector filtra trabajadores» (R1-R3); «Se registra en la empresa
  elegida» → en la de las obras (R7-R8); «Modo pruebas con otra empresa» se
  retira (D4). Firma: *decidido por Pablo Gris el 2026-10-01 · F-034*. El
  resto (búsqueda por código y empresa, petición de una sola empresa, obra
  de otra empresa omitida, parte que hereda la empresa) no cambia.
- `docs/INTEGRACION.md`: cabecera (fecha, origen, versión anterior), fila
  `EMPRESA_IMPUTACION` de §3 y párrafo «Una línea sin empresa no se
  registra» de §9.
- Comentarios de `settings.py` y `.env.example` (sin tildes en este último,
  como hoy).
- `test_f002_fuente_unica.py` debe seguir en verde: la regla se enuncia solo
  en `#regla-empresa`; el resto enlaza.

## 8. Fuera de alcance

- El recurso del trabajador en su empresa (F-026, va justo detrás).
- El universo de postventa y cómo se ofrece (F-025, spec aprobada en su
  rama con D4 ya cambiada por esta regla: no se toca aquí).
- Rechazar al guardar líneas en obras que no son de la empresa de las obras
  (F-031 / D7 de F-025): hoy el front no las ofrece (R1) y el transfer las
  omite (R8).
- Que copiar el mes anterior descarte esas líneas: se copian y salen
  marcadas, como en F-024.

## 9. Ficheros que NO se tocan

- Todo `services/dedicacion-transfer/` (R9).
- `orm_models.py`, `esquema.py`, `repositories.py` (`_a_linea` ya mapea
  `obra_empresa`), sync y `config.yaml`.
- `ListarEmpresas` y `GET /api/v1/empresas`: el selector sigue listando
  empresas con trabajadores activos más la por defecto.
- `infra/` y el `.env` desplegado: `EMPRESA_IMPUTACION` conserva nombre y
  valor (D1).
- `dedicacion-front/interface_adapters/web/app.py` (proxy).

## 10. Riesgos y decisiones

- **Producción en real.** El cambio solo puede hacer que se escriban líneas
  que hoy se omiten (las de la 18 y la 31 en obras de Ruesma). Escribirlas
  es el objetivo, pero con el recurso todavía elegido sin mirar la empresa
  (F-026): el humano debe decidir si se despliega F-034 sola o junto con
  F-026. Ninguna verificación de esta feature lanza `registro/ejecutar`.
- **Un ajuste, dos papeles (D1).** Si un día la por defecto del selector y
  la empresa de las obras difieren, el cambio es partir el ajuste en
  `_filtro` (rutas y registro); el dominio ya los separa.
- **Mutación (`critico`).** Campaña sin tope sobre las líneas cambiadas de
  `domain/empresas.py`, `use_cases.py`, `registro_sigrid.py`, `schemas.py` y
  `routes.py`; cero supervivientes sin test o sin justificación aceptada.
  Mutantes esperables: `empresa_obras` ↔ `empresa` en las cuatro llamadas,
  `==` ↔ `!=` en R1 y R3; los casos con E ≠ empresa de las obras de §2 los
  matan.
- **`azure-apps`.** Cambia el sentido de una variable, no lo que exponemos:
  copia literal de las piezas de §7 por el líder (T8).
