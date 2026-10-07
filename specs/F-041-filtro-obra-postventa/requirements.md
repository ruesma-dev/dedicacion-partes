<!-- specs/F-041-filtro-obra-postventa/requirements.md -->
# F-041 · El filtro de obra casa con el texto tal como sale en la app (incluido Postv-)

Rigor **`estandar`**. Servicio: **solo `dedicacion-front`** (`static/js/app.js` y
sus tests). Es presentación: decide qué filas se ven y qué candidatas se ofrecen,
no qué se guarda ni qué se registra en Sigrid. **No se tocan** `dedicacion-api` ni
`dedicacion-transfer` (design §1).

Pedido del humano (2026-10-06): «al filtrar por obra no filtra bien postventa.
Quiero filtrar todas las obras de postventa (empiezan por Postv-), y si pongo
pos, y voy completando, que filtre por texto incluido en el nombre de la obra
tal cual sale en la app».

## 0. Causa, comprobada ejecutando el `app.js` de hoy en node

Con un cuadrante de prueba (design §6) el comportamiento real es:

| Texto | «Filtrar obra…» (columna) | Buscador global («/») |
|---|---|---|
| `pos`, `postv`, `Postv-06` | casa con las `Postv-` | **no casa con ninguna `Postv-`** |
| `postventa` | nada | nada (el autocompletado del editor **sí** la ofrece) |
| `naves postv` | casa con quien tiene `0701 Naves` **y otra** línea `Postv-` | — |

1. **El buscador global ignora el prefijo `Postv-`**: compara con `l.cod` y
   `l.descripcion` a secas. Es el fallo que explica «no filtra postventa».
2. La columna ya añade un alias propio (`"postv postv-"`), distinto del del
   catálogo (`"postv postventa postv-"`): tres textos para la misma obra.
3. La columna junta todas las líneas en un solo texto: un filtro puede casar
   «a caballo» entre dos chips distintos.

Y lo que **no** es fallo de filtrado: con el filtro activo, la fila sigue
pintando **todos** sus chips (los que no son `Postv-` también). Ocultarlos es
F-021 (D3).

Glosario. **Etiqueta**: lo que pinta el chip, `Postv-0656`, `0656` o `VAR-29`.
**Texto visible** de una obra o línea: etiqueta + espacio + descripción (la
descripción es la que enseñan el `title` del chip y el autocompletado).
**Normalizar**: la función `normalizar` de hoy (minúsculas, sin tildes).
**Casar**: el texto visible normalizado **contiene** el filtro normalizado.

## 1. Una sola fuente del texto visible

- **R1.** El sistema debe calcular la etiqueta de una obra en una única función:
  `Postv-` delante del código si la línea o entrada es de postventa, y el código
  tal cual en otro caso, sin ningún otro caso especial por prefijo ni por obra.
- **R2.** El sistema debe calcular el texto visible como etiqueta + espacio +
  descripción, en una única función que use la de R1.
- **R3.** El chip de la tabla, el chip del editor y la entrada del catálogo del
  cuadrante deben pintar su código con la función de R1: no debe quedar en
  `app.js` otra concatenación de `"Postv-"` con un código.

## 2. Filtro «Filtrar obra…» de la columna de asignaciones

- **R4.** MIENTRAS el filtro de la columna de asignaciones no esté vacío, el
  sistema debe mostrar solo los trabajadores con **alguna línea** cuyo texto
  visible case con el filtro (D2: por línea, no sobre todas juntas).
- **R5.** CUANDO el usuario escribe `pos` y sigue completando (`post`, `postv`,
  `postv-`, `postv-0`…), el sistema debe mostrar todos los trabajadores con
  alguna línea `Postv-` mientras el texto sea prefijo de `postv-` y, con cada
  letra, un subconjunto de lo que se veía con la anterior. Con `pos` casan
  también las obras cuya descripción contiene «pos» (`Depósito`): es lo que
  significa «contiene», y se acota al seguir escribiendo.
- **R6.** El casado debe ignorar mayúsculas y tildes en los dos lados
  (`POSTV-0656`, `depósito` y `DEPOSITO` casan igual).
- **R7.** El casado debe valer para cualquier parte del texto visible: el código
  (`0656`), la etiqueta entera (`Postv-0656`), la descripción o un trozo que
  cruce de una a otra dentro de la misma línea (`0656 edif`).
- **R8.** SI el filtro de la columna está vacío, ENTONCES el sistema debe
  mostrar las mismas filas, en el mismo orden, que hoy.

## 3. Buscador global

- **R9.** CUANDO el usuario escribe en el buscador global, el sistema debe casar
  con el nombre, la categoría y el **texto visible** de las líneas (R2), de modo
  que `pos`/`postv`/`Postv-0656` encuentren a quien tiene líneas de postventa.
  Sigue siendo una búsqueda sobre todos los campos juntos, como hoy (design §5).

## 4. Catálogo, autocompletado y «Completar al 100 %» (F-029)

- **R10.** El texto con el que casan las entradas del catálogo del cuadrante
  (autocompletado del editor y candidatas de «Completar al 100 %») debe ser el
  texto visible normalizado de la entrada (R2), sin alias añadidos (D1).
- **R11.** Para el mismo texto de filtro, una línea (obra, modo) que casa en la
  columna implica que la entrada (obra, modo) del catálogo, si existe, es
  candidata de «Completar al 100 %», y viceversa: los dos parten del mismo texto.
- **R12.** La ordenación de candidatas de F-029 (las de etiqueta exacta,
  primero) y la precarga del diálogo con «Filtrar obra…» no cambian.

## 5. Compatibilidad con F-039 (`VAR-29`)

- **R13.** Una línea o entrada cuyo código llegue de la API como `VAR-29` debe
  casar por `var`, `var-2`, `29` o su descripción, sin que `app.js` contenga
  ningún literal `VAR` ni ninguna rama por prefijo de código.

## 6. Decisiones (decididas por el humano el 2026-10-06: D1-D4 = A)

- **D1 · El alias «postventa» = A: fuera.** Solo casa el texto que se ve
  (`pos`, `postv`, `postv-0656` valen; `postve…` deja de valer, también en el
  autocompletado, que hoy sí la encontraba). Una sola regla, «tal cual sale en
  la app». Descartada B: mantener `postventa` como alias oculto en los tres sitios.
- **D2 · Casar por línea = A** (R4): `naves postv` ya no casa con dos chips
  distintos, y queda lista la pieza que F-021 usará para saber qué chip casa.
  Descartada B: casar sobre todas las líneas juntas, como antes.
- **D3 · Ocultar los chips que no casan = A: fuera de F-041**, sigue en F-021,
  donde están las cuestiones que no son de esta feature (total y estado con
  chips ocultos; selección por Sesame); F-021 reutilizará el criterio por línea
  (D2). Descartada B: meter aquí el ocultado y adelantar ese debate.
- **D4 · Tests de lógica en node = A**: además de los estáticos, tests que
  ejecutan las funciones reales de `app.js` en `node` (v24 en la máquina de
  desarrollo) con datos de prueba; sin `node`, el test se salta **con su
  motivo** y el reviewer exige verlos `passed`. Fijan R5 (acotar letra a letra)
  y R11. Descartada B: solo estáticos (patrón de F-025/F-029).

## 7. Tests anteriores que cambian (lista CERRADA)

**Ninguno.** Comprobado con un prototipo de design §3 aplicado y revertido:
front `53 passed` y `services/dedicacion-transfer/tests/test_f013_sin_partida.py`
(lee `app.js`) `44 passed`. Si al implementar falla otro, PARA y avisa.

## 8. Verificación manual (humano, en local)

En tasks.md, T6: front de la rama contra la api local, `pos` → `postv-0656`
en la columna y en el buscador, `postventa` no filtra (D1), `naves postv`, Completar
al 100 % precargado con `postv` y sin filtro igual que hoy.
