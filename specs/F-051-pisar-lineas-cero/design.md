<!-- specs/F-051-pisar-lineas-cero/design.md -->
# F-051 · Diseño

Requisitos en `requirements.md`; exploración en `progress/spec_F-051.md`.
Las decisiones **D1-D9** (§9) están **abiertas**: este diseño implementa la
recomendación de cada una.

## 1. Servicios y límite

- **Solo `dedicacion-transfer`**, que es la única pluma contra Sigrid
  (`CLAUDE.md`, ARCHITECTURE «la única pluma»). Saber qué líneas de un parte
  se pueden borrar exige leer el parte, y eso solo lo hace el transfer.
- **api y front, sin cambios** (R16). El front ya pinta `a.aviso` en el
  modal (`app.js`, F-049); la api reenvía `acciones` del transfer tal cual
  (`registro_sigrid.preflight`) y del resultado de `ejecutar` solo lee
  `escritas`, `omitidas` y `ya_registradas`: los campos nuevos le son
  invisibles.
- **`partes` no se toca** (otro repositorio). Comparte el parte (F-037):
  ver §8. Ninguna responsabilidad nueva fuera del transfer: no hay que
  proponer otro servicio.

## 2. Ficheros a crear

- `services/dedicacion-transfer/tests/test_f051_reglas_cero.py` — la función
  pura (R1, R2, R5-R9).
- `services/dedicacion-transfer/tests/test_f051_pipeline_cero.py` —
  preflight y ejecutar con el `ClienteFalso` de `conftest.py` (R3-R5,
  R8-R11, R13-R15) y el lote (`RegistroLote.preflight` da lo mismo, R15).
- `services/dedicacion-transfer/tests/test_f051_sql_cero.py` — texto y
  parámetros de la sentencia de borrado con guarda (R12) y respuesta de
  `POST /api/registro/ejecutar` con `pisadas_cero` (R13, `TestClient`).

## 3. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/services/reglas_porcentajes.py` | `es_linea_al_cero`, `pisables_al_cero`, `AVISO_LINEAS_CERO` (§5) y la línea del docstring del módulo |
| `domain/models/registro_models.py` | `AccionLinea.lineas_cero: list[int]` y `ResultadoRegistro.pisadas_cero: list[int]` (vacías por defecto) |
| `application/pipelines/registro_pipeline.py` | paso 7: pisables antes de los choques; paso 10: borrado con guarda; docstring de pasos (§6) |
| `infrastructure/sigrid/sigrid_write_client.py` | `stmt_borrar_linea_cero` (§7) |
| `interface_adapters/api/app.py` | la respuesta de `ejecutar` gana `pisadas_cero` |
| `prueba_escritura_porcentajes.py` | `preflight` imprime `lineas_cero` por acción; `ejecutar`, `pisadas_cero` (solo salida) |
| `tests/test_f002_fuente_unica.py` | `ANCLAS` gana `"regla-cero"` (única aserción anterior que cambia) |
| `docs/ARCHITECTURE.md` | regla nueva `#regla-cero` y remisión desde `#regla-conflicto` y el índice de anclas (R17) |
| `docs/INTEGRACION.md` | §1 (qué escribimos) y §7 (qué se rompe) (R18) |

Rutas relativas a `services/dedicacion-transfer/` salvo las de `docs/`.

## 4. Ficheros que NO se tocan

- `criterio_choque`, `campos_identidad`, `CAMPOS_CLAVE`, `clave_conflicto`:
  la identidad de una línea no cambia; las pisables se **apartan** de los
  existentes antes de llamar a `criterio_choque` (§6). Cambiar la clave
  invalidaría confirmaciones en vuelo.
- `evaluar_capacidad`: recibe las pisables dentro de `pisadas` (R4).
- `estado_parte.py`, `cuenta_analitica.py` (copias de `partes`, lista
  cerrada), `propuesta_partida.py`, `lecturas_lote.py`, `registro_lote.py`.
- `sigrid_write_client.lineas_del_parte` / `lineas_de_partes`: ya traen
  `can`, `synckey`, hora y partida; **ninguna lectura nueva** (R15). Los
  enlaces de Sigrid solo se miran en la guarda del borrado (§7).
- Todo `dedicacion-api` y `dedicacion-front`.

## 5. Funciones nuevas (application, puras)

En `reglas_porcentajes.py`, junto al bloque de identidad:

```python
def es_linea_al_cero(ls: LineaSigrid) -> bool:
    """Hora M* (`es_linea_mensual`), `can` 0 o nulo, sin synckey y con
    recurso. ARCHITECTURE.md#regla-cero."""

def pisables_al_cero(existentes: Iterable[LineaSigrid],
                     accion: AccionLinea, *,
                     en_cerrado: set[int]) -> tuple[LineaSigrid, ...]:
    """Las líneas de `existentes` que `accion` pisa: al cero, del MISMO
    recurso (`_DE_LINEA["recurso"]` == `_DE_ACCION["recurso"]`), fuera de
    `en_cerrado` (ides de líneas que viven en un parte cerrado) y, si
    `accion.destino == "postventa"`, con su misma partida (D7). Por `ide`
    ascendente. Una acción que no es `escribir` no pisa nada."""

AVISO_LINEAS_CERO = ("sustituye {n} línea(s) al 0 % del parte {partes}: "
                     "se borran al registrar")
```

`can` se compara **exacto** con 0 (`_can(ls.can) == 0.0`): Sigrid guarda
`0.0` y el SQL de la guarda compara igual (`ISNULL(can, 0) = 0`); una
tolerancia aquí y otra allí divergirían. Lee recurso y partida con los
mismos lectores que `criterio_choque` (`_DE_LINEA`, `_DE_ACCION`).

## 6. Pipeline

**Preflight, paso 7** (por destino + periodo, donde ya se leen `existentes`
de todos los partes del periodo y `donde[ide]`):

1. `en_cerrado = {ls.ide for ls in existentes if donde[ls.ide].cod in
   parte.cerrados}`.
2. Por cada acción del grupo: `ceros = pisables_al_cero(existentes, a,
   en_cerrado=en_cerrado)`; `choques` = los de hoy **sin** los `ide` de
   `ceros` (R4).
3. Si un choque está en un cerrado, la acción se omite **como hoy** y no
   guarda `lineas_cero` (R8). Si no: `a.lineas_cero = [ide…]` y, si hay,
   `_sumar_aviso(a, AVISO_LINEAS_CERO…)` con los códigos de parte (R3).
4. `contexto` de un conflicto de pisado excluye los `lineas_cero` del
   recurso (R4).
5. Paso 7 bis: `pisadas[recurso]` gana los `lineas_cero` de sus acciones
   que siguen en `escribir` (R4); la cifra no cambia (suman 0), pero el
   `contexto` de la sobrecarga ya no las lista.

**Ejecutar, paso 10**, después de los borrados de pisados confirmados y
antes de las inserciones, con el mismo `ides_borrados`:

```python
for a in sorted(a_escribir, key=lambda x: (x.ano, x.mes, x.registro_id)):
    for ide in a.lineas_cero:
        if ide in ides_borrados: continue
        ides_borrados.add(ide)
        statements.append(self._cli.stmt_borrar_linea_cero(
            ide, reside=int(a.recurso_ide),
            est_registro=int(self._st.est_parte_activo)))
        res.borradas += 1
        res.pisadas_cero.append(ide)
        logger.info("[registro] pisa linea al cero ide=%s parte=%s "
                    "recurso=%s", ide, …, a.recurso_ide)
```

`a_escribir` ya excluye las acciones retenidas por un aviso sin confirmar,
las omitidas y las ya registradas: eso es R11. R5 hace que una acción
escrita del recurso baste para borrar sus pisables.

`ejecutar` rehace el preflight antes de escribir (como hoy): la ventana entre
lo leído y el borrado es de segundos, y la guarda cubre lo que cambie en ella.

## 7. SQL (Sigrid, base `ruesma`, solo el transfer)

No hay SQL de PostgreSQL ni ficheros `NN_*.sql`. Sentencia nueva en
`sigrid_write_client.py`, junto a `stmt_borrar_linea`:

```sql
DELETE FROM hmores WHERE ide = ? AND reside = ?
  AND ISNULL(can, 0) = 0 AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ''
  AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0
  AND ISNULL(hdereside, 0) = 0 AND ISNULL(empdpreide, 0) = 0
  AND ISNULL(empabside, 0) = 0 AND ISNULL(emprccide, 0) = 0
  AND EXISTS (SELECT 1 FROM auxhor a WHERE a.ide = hmores.horide
              AND a.cod LIKE 'M%')
  AND EXISTS (SELECT 1 FROM con c WHERE c.ide = hmores.hmoide
              AND c.est = ?)
-- parámetros: [ide, reside, est_registro]
```

- Los enlaces son los de `azure-apps/sigrid_tablas.md` (`hmores`: línea de
  albarán, de factura, dedicación de recursos, nóminas) y los mismos que
  `partes` F-046 se niega a tocar. En 2025-2026 **ninguna** línea `M*` los
  tiene (exploración): la guarda es defensiva.
- `escribir` devuelve filas afectadas del lote, no por sentencia: si la
  guarda no borra, `borradas` cuenta de más. Es el mismo límite que el
  pisado de hoy; el log y `pisadas_cero` dicen qué se **pidió** borrar.

## 8. Coordinación con `partes` y con F-044

- **Mismo parte.** `partes` escribe horas `H*`/`C*` con `synckey`
  `partes:…` y nunca `M*` («los mensuales con MENC no registran por horas»,
  `azure-apps/partes.md` §3.5): ninguna línea suya es pisable (R7). Sus
  pisados, sus comprobaciones (F-024) y su reajuste (F-046) solo miran
  líneas con su `synckey`. No hay carrera nueva: el borrado va en el mismo
  envío que nuestras inserciones, bajo las mismas reglas de lote.
- **Qué cambia para ellos**: el transfer pasa a borrar, sin confirmación,
  líneas de Administración (sin `synckey`) en partes que también usa
  `partes`. Se les avisa al desplegar (R18; el humano o el líder, por el
  canal de siempre) por si un día quieren lo mismo para las horas, sin
  tocar su repositorio.
- **F-044 (recursos vinculados)**: sus líneas al 0 % (`OTEL`, `OGAS`, `KM`,
  `MESVE`… de 0707) **se quedan** con F-051 (R6). F-044 debería reutilizar
  `pisables_al_cero` para su recurso vinculado (hora no `M*`: tendrá que
  ampliar `es_linea_al_cero` con su propia decisión).

## 9. Decisiones abiertas (las decide el humano)

- **D1 · Qué es «pisar».** (A) borrar la línea al 0 % e insertar la nuestra
  al final del parte (el mecanismo del pisado de hoy); (B) igual, pero
  insertando en la `pos` de la línea al 0 % (conserva el orden de
  Administración: la persona junto a su teléfono y gasoil); (C) `UPDATE` de
  la línea al 0 % en su sitio (`can`, `tot`, `pre`, `horide`, `paride`,
  `caaide`, `synckey`, `tex`). **Recomiendo A**: es el camino probado (el
  pisado confirmado y `limpiar` ya borran e insertan), no estrena escritura y
  deshacer sigue siendo borrar por `synckey`. B es barata si el orden importa
  a Administración (leer `pos`, que `lineas_de_partes` ya trae). C es una
  escritura nueva en el ERP y deja a medias líneas ajenas si falla.
- **D2 · ¿Se confirma?** (A) sin confirmación, con el aviso de R3 en el
  modal; (B) como un pisado de hoy (conflicto que hay que marcar). **Recomiendo
  A**: la línea no imputa nada (`can = 0`, `tot = 0`), es lo que pidió Juan y
  B añade un clic por persona y mes sin decisión real detrás.
- **D3 · Qué línea al 0 % «casa».** (A) cualquier `M*` al 0 % del recurso en
  la obra y periodo, sea cual sea su hora y partida; (B) solo la de su misma
  partida; (C) solo la de los cuatro campos (la identidad de hoy). **Recomiendo
  A**: es la que resuelve lo que se pidió (con otra partida, B y C la dejan, y
  es el caso que hoy falla); un recurso con dos líneas al 0 % las pierde las
  dos, que no imputaban nada.
- **D4 · «Al 0 %» = `can` exactamente 0 o nulo**, sin tolerancia (Sigrid
  guarda `0.0`, §5). **Recomiendo** así; si no, la de la capacidad (0,00005).
- **D5 · Solo líneas sin `synckey`** (las de Administración); con la de
  `partes` o la nuestra, nunca. **Recomiendo** confirmarlo tal cual.
- **D6 · Partes cerrados.** (A) como hoy: no se toca nada y, si coincide por
  identidad, la nuestra se omite con `parte_cerrado`; (B) la línea al 0 % de
  un cerrado se ignora (ni se toca ni bloquea: la nuestra iría al
  complementario). **Recomiendo A**: F-051 es de partes En registro y B
  crearía complementarios en meses cerrados.
- **D7 · Postventa.** (A) la regla de D3 también en el parte de la obra de
  postventa; (B) allí solo la línea al 0 % de la **misma partida** (la de la
  obra original); (C) postventa fuera. **Recomiendo B**: el parte de
  postventa lo comparten todas las obras y cada petición es de una obra;
  con A, registrar la obra X borraría la línea al 0 % que el recurso tenga
  por la obra Y.
- **D8 · Líneas al 0 % donde el recurso ya no tiene línea este mes** (pasó
  de la 0707 a otra obra): F-051 no las ve (solo mira la obra que registra).
  **Recomiendo** dejarlas fuera: o las borra Administración, como pidió Juan
  el 2026-10-08, o feature aparte que avise de ellas en el preflight del mes.
- **D9 · Verificación y origen.** (A) para R19, el humano o Administración
  crea a mano en Sigrid, en el parte En registro de la 0404 del mes de
  prueba, las dos líneas al 0 % (como las crea Administración); (B) una fase
  nueva `sembrar-cero` del script, que escribe (solo en modo pruebas, con
  `--confirmar`). **Recomiendo A**: no añade código que escribe y reproduce
  el origen real. Y una pregunta para Juan o Administración, que no cambia el
  diseño: ¿esas líneas salen de una función de copia de Sigrid o se copian a
  mano? En la base no se distingue (`hmores` no guarda autor).

## 10. Riesgos y alternativas descartadas

- **Borrar sin confirmar en producción** (D2 = A). Acotado por R1 (solo
  recurso propio, al 0 %, sin `synckey`, En registro), la guarda (R12) y R11
  (solo si la nuestra se escribe). Lo peor que puede pasar es perder una
  línea que imputaba 0.
- **Borrado e inserción en lotes distintos** (más de 15 sentencias). Si el
  segundo falla, la línea al 0 % ya no está y la nuestra tampoco: no se
  pierde importe y reejecutar lo arregla (R14). Es la razón por la que la
  regla R32 de F-002 (no borrar sin escribir) no hace falta aquí más allá de
  R11.
- **La propuesta de partida ve las líneas al 0 %** (F-050, paso «parte
  anterior»: el mes en curso cuenta, con suma 0). Con una sola, propone su
  partida, que es la que copió Administración; con dos de partidas
  distintas hay empate y ese paso no propone. No se toca: F-051 no cambia la
  propuesta (R15). Si molesta, es de F-050.
- **Descartado: cambiar `criterio_choque`** para que una línea al 0 % choque
  con cualquier partida. Mezcla dos reglas (identidad y limpieza), cambia la
  clave de los conflictos y obligaría a confirmar (D2 = B por la puerta de
  atrás).
- **Descartado: leer los enlaces en el preflight** (avisar solo de lo que
  la guarda borraría): cambia dos lecturas del lote (F-055) por un caso que
  hoy no existe (§7).
