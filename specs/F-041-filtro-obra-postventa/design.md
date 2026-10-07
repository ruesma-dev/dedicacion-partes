<!-- specs/F-041-filtro-obra-postventa/design.md -->
# F-041 · Diseño: el filtro de obra casa con el texto visible

## 1. Encaje y límite de servicio

Solo **`dedicacion-front`**. `docs/ARCHITECTURE.md` («`dedicacion-front` —
captura, nada más») y `docs/CONVENTIONS.md` (JS vanilla, el front no calcula
reglas de negocio): filtrar filas y casar texto con el catálogo es presentación.
Nada de lo que cambia decide qué se guarda, qué cifra se pone (Completar sigue
calculándolo la API, regla 15 `#regla-completar`) ni qué se registra en Sigrid.
No cruza la frontera del proyecto: no cambia nada de lo que exponemos ni
consumimos, así que `azure-apps/` no se toca. Sin SQL, sin ORM, sin `.env`.

## 2. Ficheros

**Modificar**

| Fichero | Qué cambia |
|---|---|
| `services/dedicacion-front/static/js/app.js` | 3 funciones nuevas (§3) y sus 6 usos (§4) |

**Crear**

| Fichero | Qué contiene |
|---|---|
| `services/dedicacion-front/tests/test_f041_filtro_obra.py` | estáticos + lógica en node (§6) |

**No se tocan** (colindantes que tientan)

- `services/dedicacion-api/**` y `services/dedicacion-transfer/**`: el texto de
  las líneas y del catálogo ya llega completo (`LineaOut.cod`, `.descripcion`,
  `.es_postventa`; `ObraOut`). Ni un campo nuevo.
- `normalizar` (minúsculas + sin tildes): se reutiliza tal cual.
- `candidatasDestino` y `montarAutocompletado`: su código no cambia; cambia la
  `clave` que construye `construirCatalogoObras` (R10).
- `pintarModalPreflight`: lo toca F-039 (T7); F-041 no, para no pisarse.
- `templates/index.html`, `static/css/styles.css`: ni placeholders ni estilos.
- Los tests anteriores (lista cerrada en requirements §7: ninguno).

## 3. Funciones nuevas (sección «utilidades» de `app.js`, tras `normalizar`)

```js
// Etiqueta de una obra tal como la pinta la app: «Postv-» delante si es de
// postventa; el código, tal cual, en otro caso (F-041, R1).
function etiquetaObra(cod, esPostventa) {
  return (esPostventa ? "Postv-" : "") + cod;
}

// Texto visible: etiqueta y descripción, lo que enseñan el chip, su `title` y
// el autocompletado. De aquí salen todos los casados de obra (R2).
function textoObra(cod, descripcion, esPostventa) {
  return etiquetaObra(cod, esPostventa) + " " + (descripcion || "");
}

// ¿La línea del cuadrante casa con el filtro? `q` llega ya normalizado (R4).
function lineaCasa(l, q) {
  return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);
}
```

Sin caso especial por prefijo: `VAR-29` (F-039) llega como `cod` de la línea y
de la obra, y sale `VAR-29 <descripción>` como cualquier otra (R13). `lineaCasa`
es la pieza que F-021 usará para decidir qué chip se ve.

## 4. Usos (todos en `app.js`)

1. **`construirCatalogoObras`** (R3, R10). Mantiene el orden de las claves del
   objeto (lo fija `test_f025_r22_*`):
   - normal: `cod: etiquetaObra(o.cod, false)`,
     `clave: normalizar(textoObra(o.cod, o.descripcion, false))`;
   - postventa: `cod: etiquetaObra(o.cod, true)`,
     `clave: normalizar(textoObra(o.cod, o.descripcion, true))`.
   Desaparece el alias `"postv postventa postv-" + o.cod + " " + o.cod`
   (D1 = A, decidido por el humano el 2026-10-06).
2. **`textoColumna`**: se borra su rama `asignaciones` (con el alias
   `"postv postv-"`); las de `nombre`, `categoria` y `total` no cambian.
3. **`trabajadoresVisibles`**, bucle de filtros por columna (R4, R8):
   ```js
   const filtro = normalizar(state.filtrosCol[clave] || "");
   if (!filtro) continue;
   const casa = clave === "asignaciones"
     ? t.lineas.some((l) => lineaCasa(l, filtro))
     : normalizar(textoColumna(t, clave)).includes(filtro);
   if (!casa) return false;
   ```
   (D2 = A, decidido por el humano el 2026-10-06; descartado casar todas juntas.)
4. **`trabajadoresVisibles`**, buscador global (R9): en el `pajar`, las líneas
   pasan de `l.cod + " " + l.descripcion` a
   `textoObra(l.cod, l.descripcion, l.es_postventa)`. Resto igual.
5. **`construirCelda`**, chip de la tabla (R3):
   `<span class="cod">${escapeHtml(etiquetaObra(l.cod, l.es_postventa))}</span>`.
   El HTML que resulta es idéntico al de hoy (`Postv-` no lleva nada que escapar).
6. **`chipEditable`** (R3): `cod.textContent = etiquetaObra(linea.cod,
   linea.es_postventa);`. El botón PV repinta el editor, así que la etiqueta
   sigue al modo sin más cambios.

`candidatasDestino` no se toca: su orden por etiqueta exacta
(`normalizar(e.cod) === q`) sigue funcionando porque `e.cod` ya era la etiqueta
(R12). `montarDialogoCompletar` sigue precargando con `state.filtrosCol.asignaciones`.

## 5. Decisiones tomadas y descartadas

- **El buscador global sigue mezclando campos** (nombre + categoría + líneas en
  un solo texto): es un buscador libre de la fila y nadie ha pedido cambiarlo.
  Solo cambia qué texto aporta cada línea. Lo «por línea» (D2) es para la columna,
  que es un filtro de obra.
- **Descartado: un `texto_visible` calculado por la API.** Es presentación y el
  front ya tiene los tres campos; añadirlo a `LineaOut`/`ObraOut` tocaría la api
  y su contrato por algo que es un `+` de cadenas.
- **Descartado: comparar con el `innerText` del chip.** Ata el filtro al DOM
  (y no vale para el catálogo, que no tiene chip); la función compartida da el
  mismo texto sin pintar nada.
- **Descartado: casar por inicio de palabra** en vez de «contiene». El humano
  pide «texto incluido»; `pos` también trae `Depósito`, y se acota escribiendo.
- **No se recorta (`trim`) el filtro**: hoy no se hace y nadie lo ha pedido.

## 6. Tests (`tests/test_f041_filtro_obra.py`)

Nombres `test_f041_rN_…`. Sin red ni BBDD. Dos familias:

**Estáticos** (patrón de `test_f029_seleccion.py`: `_funcion`, `_plano`):
- R1/R2: cuerpo de `etiquetaObra` y `textoObra`; `textoObra` llama a `etiquetaObra`.
- R3: el literal `"Postv-"` (con comillas) aparece **una sola vez** en `app.js` y
  dentro de `etiquetaObra`; `construirCelda`, `chipEditable` y
  `construirCatalogoObras` llaman a `etiquetaObra`.
- R4/R9/R10: `trabajadoresVisibles` usa `lineaCasa` y `textoObra`;
  `construirCatalogoObras` usa `textoObra`; `textoColumna` ya no tiene la rama
  `asignaciones`; ni `"postv postv-"` ni (D1) `postventa` en minúsculas
  dentro de una clave.
- R12: `candidatasDestino` sin cambios (las aserciones de `test_f029_r10_*`
  ya lo fijan; no se duplican).
- R13: ni `"VAR` ni `'VAR` en `app.js`; `etiquetaObra` sin más ramas que `esPostventa`.

**Lógica en node** (D4 = A, decidido por el humano el 2026-10-06). Un ayudante `_node(funciones, cuerpo) -> object`:
1. extrae con `_funcion` el código real de `normalizar`, `etiquetaObra`,
   `textoObra`, `lineaCasa`, `fmtPct`, `textoColumna`, `trabajadoresVisibles`,
   `construirCatalogoObras` y `candidatasDestino` (ninguna toca el DOM);
2. extrae `const ORDEN_ESTADO = {…};` de `app.js` con una regex (no se copia);
3. concatena `var state = <json>;`, el `cuerpo` y
   `process.stdout.write(JSON.stringify(resultado))`;
4. `subprocess.run([node, "-"], input=…, capture_output=True, text=True,
   encoding="utf-8", timeout=30, check=True)` y `json.loads` de la salida.
Si `shutil.which("node")` es `None`: `pytest.skip("node no está instalado: los
tests de lógica de F-041 no se ejecutan")`. El reviewer los exige `passed`.

Datos de prueba (los del prototipo, §7): obras `0656 Edificio Arroyo` (activa,
admite postventa), `0700 Depósito agua` (activa), `VAR-29 Arroyo varios`
(activa, sin postventa); trabajadores Ana (`Postv-0656`), Benito (`0700`),
Carla (`0701 Naves` + `Postv-0656`), Dani (`0656`), Eva (`VAR-29`), Fede (sin
líneas, activo) y Gil (baja sin líneas, nunca visible).

Casos (filas visibles por nombre):
- R5: `pos` → Ana, Benito, Carla; `post`, `postv`, `postv-`, `Postv-06`,
  `Postv-0656` → Ana, Carla; y cada prefijo ⊆ el anterior.
- R6: `POSTV-0656 Edif` → Ana, Carla; `depósito` = `DEPOSITO` → Benito.
- R7: `0656` → Ana, Carla, Dani; `0656 edif` → Ana, Carla, Dani.
- D2: `naves postv` → nadie (hoy: Carla).
- D1: `postventa` → nadie en la columna y ninguna candidata.
- R8: sin filtro → todos menos Gil, por nombre (`orden = {campo: "nombre",
  dir: 1}`), que es lo que da el `app.js` de hoy con esos datos.
- R9: buscador `postv` → Ana, Carla; `beni` → Benito; `naves postv` → Carla.
- R10/R11: para cada texto de la lista, el conjunto (cod, pv) de líneas que casan
  ⊆ el de candidatas de `candidatasDestino`, y cada candidata cuya obra tenga
  línea en ese modo casa en la columna; `postv` → solo `Postv-0656`;
  `0656` → `0656` primero (R12).
- R13: `var-2` → Eva y candidata `VAR-29`; `29` → Eva; `arroyo` → Ana, Carla,
  Dani, Eva.

## 7. Prototipo y riesgos

**Prototipo** (desechable, aplicado sobre la rama y revertido con
`git checkout`): §3 + §4 tal cual (D1 = A y D2 = A). `node --check` OK; front
`53 passed`; transfer `test_f013_sin_partida.py` `44 passed`; en node, todos
los casos de §6 dan lo esperado. Por eso la lista de tests que cambian es
**ninguno**.

**Mutación.** `python -m harness.mutacion` solo muta Python: para F-041 el
alcance sale vacío, y la puerta de cobertura tampoco mide JS. Las sustituye una
**campaña manual** (patrón de `progress/mutacion_manual_F-035.md`): el script
vive **fuera del repo**, muta una copia de `app.js` en un directorio temporal,
pasa `tests/test_f041_filtro_obra.py` y anota cada mutante en
`progress/mutacion_manual_F-041.md`. Mínimo: quitar `"Postv-"` de
`etiquetaObra`; `" "` → `""` en `textoObra`; `includes` → `startsWith` en
`lineaCasa`; `some` → `every`; `continue` → `return false`; quitar `textoObra`
del `pajar`; `true` → `false` en la entrada postventa del catálogo; quitar
`normalizar` de la `clave`. Cada superviviente, con su análisis (rigor estándar:
juzga el reviewer).

**Riesgos.**
- *Merge con F-039* (en paralelo): F-039 toca `pintarModalPreflight` y añade
  `test_f039_partida_fija.py`; F-041 toca otras seis funciones. Sin solape
  previsto. Quien entre segundo pasa la suite del front completa.
- *D1 quita `postventa` del autocompletado*: quien la busque así tendrá que
  escribir `postv`. Aceptado por el humano el 2026-10-06.
- *Rendimiento*: `lineaCasa` normaliza cada línea en cada pulsación, como hoy
  hacía `textoColumna` con todas juntas; mismo orden de coste (cientos de filas).
