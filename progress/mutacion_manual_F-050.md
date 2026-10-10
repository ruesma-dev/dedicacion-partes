<!-- progress/mutacion_manual_F-050.md -->
# F-050 · Campaña de mutación manual del front (`app.js`)

El arnés no muta JavaScript: campaña a mano, con el script del implementer
(`js_mut.py`, en el scratchpad de la sesión), en una COPIA AISLADA
(`git worktree add --detach`, con unión al `.venv` del front), nunca en la
copia de trabajo. Cada mutante cambia UN texto exacto de
`services/dedicacion-front/static/js/app.js` y corre la suite ENTERA del front
(`pytest tests -q`); se anota cuántos tests fallan. El fichero se restaura
después de cada uno.

- **Primera pasada** (HEAD `7f5f115`): 56 mutantes, **52 muertos, 4 vivos** (J19, J36, J46, J56), 596.9 s.
  Los cuatro eran huecos reales (no equivalentes): T15 añade
  `test_f050_r28_la_partida_fija_casa_por_su_descripcion` (J19),
  `test_f050_r26_r29_cada_modo_con_su_catalogo` (J36 y J46) y
  `test_f050_r29_repintar_el_modal_olvida_las_lineas_de_antes` (J56).
- **Segunda pasada** (HEAD `f4cdb11`, la final): **56 generados, 56 muertos, 0 supervivientes**, 785.5 s en serie.
- **Textos de la tabla** (review 1): copiados de la salida de la segunda pasada
  (`js_mut2.json`), sin cortar. `app.js` no ha cambiado de `f4cdb11` a
  `493bf35` (`git diff` vacío) y cada texto original aparece una sola vez en
  él, en la línea anotada. Los de varias líneas, al final.

| Id | app.js:línea | Texto original → mutado (exacto, espacios plegados) | Fallos |
|---|---|---|---|
| J01 | 122 | `if (!p \|\| p.partida_ide == null) return "";` → `if (!p) return "";` | 1 |
| J02 | 123 | `.filter(Boolean).join(" · ") \|\|` → `.filter(Boolean).join(" - ") \|\|` | 1 |
| J03 | 124 | ``partida ${p.partida_ide}`; }` → ``${p.partida_ide}`; }` | 1 |
| J04 | 133 | `if (mayor && p.mayor !== mayor) return false;` → `if (mayor && p.mayor === mayor) return false;` | 6 |
| J05 | 135 | `return palabras.every((w) => pajar.includes(w));` → `return palabras.some((w) => pajar.includes(w));` | 9 |
| J06 | 134 | `const pajar = normalizar(`${p.cod \|\| ""} ${p.res \|\| ""}`);` → `const pajar = normalizar(`${p.res \|\| ""}`);` | 3 |
| J07 | 131 | `const palabras = normalizar(texto).split(/\s+/).filter(Boolean);` → `const palabras = [normalizar(texto)];` | 1 |
| J08 | 145 | `const primera = prop ? lista.find((p) => p.ide === prop.paride) : undefined;` → `const primera = prop ? resp.partidas.find((p) => p.ide === prop.paride) : undefined;` | 1 |
| J09 | 147 | `.concat(lista.filter((p) => p !== primera))` → `.concat(lista)` | 1 |
| J10 | 148 | `.map((p) => ({ ...p, propuesta: p === primera }));` → `.map((p) => ({ ...p, propuesta: false }));` | 1 |
| J11 | 165 | `return origen ? `${texto}: ${origen}` : texto;` → `return texto;` | 2 |
| J12 | 164 | `const texto = textos[metodo] \|\| metodo;` → `const texto = textos[metodo] \|\| "";` | 1 |
| J13 | 163 | `if (!metodo) return ""; const texto` → `const texto` | 1 |
| J14 | 220 | `const tras = c === "partida" ? validas.indexOf("asignaciones") : -1;` → `const tras = -1;` | 2 |
| J15 | 221 | `if (tras >= 0) validas.splice(tras + 1, 0, c);` → `if (tras >= 0) validas.splice(tras, 0, c);` | 3 |
| J16 | 217 | `if (validas.includes(c)) return;` → `(borrado)` | 4 |
| J17 | 594 | `if (!casaPartida) return false;` → `if (casaPartida) return false;` | 2 |
| J18 | 593 | `: "automática").includes(filtro));` → `: "").includes(filtro));` | 1 |
| J19 | 590 | `l.partida_fija ? l.descripcion` → `l.partida_fija ? ""` | 1 |
| J20 | 609 | `` " " + t.lineas.map((l) => `${l.partida_cod \|\| ""} ${l.partida_res \|\| ""}`).join(" ") `` → `""` | 1 |
| J21 | 670 | `const n = Math.max(1, t.lineas.length);` → `const n = 1;` | 1 |
| J22 | 686 | `td.rowSpan = n;` → `td.rowSpan = 1;` | 1 |
| J23 | 673 | `tr.className = idx ? "fila subfila" : "fila";` → `tr.className = "fila";` | 1 |
| J24 | 53 | `const COLUMNAS_POR_LINEA = ["asignaciones", "partida"];` → `const COLUMNAS_POR_LINEA = ["asignaciones"];` | 1 |
| J25 | 966 | `const l = t.lineas[idx]; if (!l) {` → `const l = t.lineas[0]; if (!l) {` | 1 |
| J26 | 994 | `` } else if (l.partida_ide != null) { td.innerHTML = `<span class="partida-elegida"> `` → `` } else if (l.partida_ide == null) { td.innerHTML = `<span class="partida-elegida"> `` ([exacto](#textos-exactos-de-j26-j28-j34-y-j43)) | 1 |
| J27 | 999 | `if (state.periodoEstado === "ABIERTO" && !l.partida_fija) {` → `if (!l.partida_fija) {` | 1 |
| J28 | 1002 | `ev.stopPropagation(); abrirSelectorPartida(t.ide, l.obra_ide, l.es_postventa, td);` → `abrirSelectorPartida(t.ide, l.obra_ide, l.es_postventa, td);` ([exacto](#textos-exactos-de-j26-j28-j34-y-j43)) | 1 |
| J29 | 1666 | `viejas.forEach((tr) => tr.remove());` → `(borrado)` | 1 |
| J30 | 1462 | `if (state.editandoIde === trabajadorIde) await guardarAhora();` → `(borrado)` | 1 |
| J31 | 1473 | `selector.cache.set(clave, resp);` → `(borrado)` | 1 |
| J32 | 1465 | `let resp = selector.cache.get(clave);` → `let resp = undefined;` | 1 |
| J33 | 309 | `selector.cache.clear(); // F-050` → `// F-050` | 1 |
| J34 | 1449 | `return [state.anio, state.mes, state.empresa, trabajadorIde, obraIde, esPostventa].join("\|");` → `return [trabajadorIde, obraIde, esPostventa].join("\|");` ([exacto](#textos-exactos-de-j26-j28-j34-y-j43)) | 1 |
| J35 | 1497 | `let mayor = resp.ambito \|\| null;` → `let mayor = null;` | 1 |
| J36 | 1494 | `partidas: ctx.esPostventa ? resp.partidas_postventa : resp.partidas,` → `partidas: resp.partidas,` | 1 |
| J37 | 1517 | `const partida = op.automatica ? null : { ide: op.ide, cod: op.cod, res: op.res };` → `const partida = { ide: op.ide, cod: op.cod, res: op.res };` | 1 |
| J38 | 1524 | `selector.cache.delete(ctx.clave);` → `(borrado)` | 2 |
| J39 | 1526 | `if (ctx.despues) ctx.despues();` → `(borrado)` | 3 |
| J40 | 1525 | `aplicarFila(datos); if (ctx.despues)` → `if (ctx.despues)` | 2 |
| J41 | 1534 | `opciones = listaSelector(base, input.value, mayor).concat([{ automatica: true }]);` → `opciones = listaSelector(base, input.value, mayor);` | 1 |
| J42 | 1595 | `elegir(opciones[activa]);` → `elegir(opciones[0]);` | 1 |
| J43 | 1584 | `ev.stopPropagation(); if (ev.key === "ArrowDown") { ev.preventDefault(); activa = Math.min(activa + 1, opciones.length - 1);` → `if (ev.key === "ArrowDown") { ev.preventDefault(); activa = Math.min(activa + 1, opciones.length - 1);` ([exacto](#textos-exactos-de-j26-j28-j34-y-j43)) | 1 |
| J44 | 1576 | `mayor = b.dataset.mayor \|\| null;` → `mayor = null;` | 1 |
| J45 | 1523 | `es_postventa: ctx.esPostventa, partida }) });` → `es_postventa: false, partida }) });` | 2 |
| J46 | 1544 | `: `<span class="cod">` → `: `<span class="cod">X` | 2 |
| J47 | 1970 | `if (!a.paride) return "sin partida";` → `if (a.paride == null) return "sin partida";` | 2 |
| J48 | 1971 | `return a.partida_cod \|\| `partida ${a.paride}`;` → `return `partida ${a.paride}`;` | 4 |
| J49 | 2094 | `trabajador: a.recurso_ide, obra_ide: o.obra.ide,` → `trabajador: a.recurso_ide, obra_ide: o.obra.codigo,` | 3 |
| J50 | 2095 | `es_postventa: a.es_postventa, };` → `es_postventa: false, };` | 1 |
| J51 | 2132 | `abrirSelectorPartida(l.trabajador, l.obra_ide, l.es_postventa, boton, repreflightPartida);` → `abrirSelectorPartida(l.trabajador, l.obra_ide, l.es_postventa, boton, null);` | 4 |
| J52 | 2100 | `` (origen ? `<div class="origen-partida">${escapeHtml(origen)}</div>` : "") `` → `""` | 2 |
| J53 | 2099 | ``${escapeHtml(textoPartidaAccion(a))}</button>`` → ``${textoPartidaAccion(a)}</button>`` | 1 |
| J54 | 1979 | `body: JSON.stringify({ trabajador_ide: registro.trabajadorIde }) });` → `body: JSON.stringify({}) });` | 6 |
| J55 | 2147 | `pisar_claves: pisar, trabajador_ide: registro.trabajadorIde,` → `pisar_claves: pisar,` | 1 |
| J56 | 2069 | `registro.lineas = {}; let html` → `let html` | 1 |

## Textos exactos de J26, J28, J34 y J43

Son los cuatro mutantes de varias líneas: en la tabla van con los espacios
plegados; aquí, tal cual los busca y sustituye el script (sangría incluida).

**J26** (app.js:994, 1 fallo). Original:

```js
} else if (l.partida_ide != null) {
      td.innerHTML = `<span class="partida-elegida">
```

Mutado:

```js
} else if (l.partida_ide == null) {
      td.innerHTML = `<span class="partida-elegida">
```

**J28** (app.js:1002, 1 fallo). Original:

```js
        ev.stopPropagation();
        abrirSelectorPartida(t.ide, l.obra_ide, l.es_postventa, td);
```

Mutado:

```js
        abrirSelectorPartida(t.ide, l.obra_ide, l.es_postventa, td);
```

**J34** (app.js:1449, 1 fallo). Original:

```js
  return [state.anio, state.mes, state.empresa, trabajadorIde, obraIde,
    esPostventa].join("|");
```

Mutado:

```js
  return [trabajadorIde, obraIde, esPostventa].join("|");
```

**J43** (app.js:1584, 1 fallo). Original:

```js
    ev.stopPropagation();
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      activa = Math.min(activa + 1, opciones.length - 1);
```

Mutado:

```js
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      activa = Math.min(activa + 1, opciones.length - 1);
```

## T15b · omitida por R20 con selector (ampliación del 2026-10-10)

Mismo método, en otra COPIA AISLADA (`services/dedicacion-front` sin `.venv`
ni `.env`, más `propuesta_partida.py` y `reglas_porcentajes.py` del transfer,
que leen los tests nuevos, copiados en el scratchpad), con el script
`mut_t15b.py` del scratchpad: un texto exacto de `app.js` por mutante (cada
original aparece una sola vez en él; se comprueba antes de mutar), suite
ENTERA del front (`pytest tests -q -p no:cacheprovider`, 187 tests en verde
sin mutar) y restauración tras cada uno (`cmp` con la copia de trabajo al
final: idénticos). Sobre el `app.js` de T15b (HEAD `1c78608` + el cambio).

**11 generados, 11 muertos, 0 supervivientes**, 122,9 s en serie. Los de
una línea van en la tabla; los de varias (K08, K09, K10), debajo.

| Id | app.js:línea | Texto original → mutado (exacto) | Fallos |
|---|---|---|---|
| K01 | 2112 | `/^la partida (.+) elegida no es una partida hoja activa del presupuesto de la obra /` → `/la partida (.+) elegida no es una partida hoja activa del presupuesto de la obra /` | 1 |
| K02 | 2113 | `.exec(a.motivo);` → `.exec(a.aviso);` | 2 |
| K03 | 2114 | `sel = (r20 ? botonPartida(r20[1]) : "") +` → `sel = "" +` | 2 |
| K04 | 2114 | `botonPartida(r20[1])` → `botonPartida(r20[0])` | 2 |
| K05 | 2112 | `/^la partida (.+) elegida no es una partida hoja activa del presupuesto de la obra /` → `/^la partida (.+) /` | 3 |
| K06 | 2094 | `` `${escapeHtml(texto)}</button>`; `` → `` `${texto}</button>`; `` | 2 |
| K07 | 2090 | `trabajador: a.recurso_ide, obra_ide: o.obra.ide,` → `trabajador: a.recurso_ide, obra_ide: o.obra.codigo,` | 4 |
| K08 | 2091 | [exacto](#textos-exactos-de-k08-k09-y-k10) | 1 |
| K09 | 2089 | [exacto](#textos-exactos-de-k08-k09-y-k10) | 5 |
| K10 | 2114 | [exacto](#textos-exactos-de-k08-k09-y-k10) | 1 |
| K11 | 2103 | `sel = botonPartida(textoPartidaAccion(a)) +` → `sel = botonPartida(a.partida_cod) +` | 1 |

### Textos exactos de K08, K09 y K10

**K08** (app.js:2091, 1 fallo). Original:

```js
          es_postventa: a.es_postventa,
        };
        return
```

Mutado:

```js
          es_postventa: false,
        };
        return
```

**K09** (app.js:2089, 5 fallos). Original:

```js
        registro.lineas[a.registro_id] = {
          trabajador: a.recurso_ide, obra_ide: o.obra.ide,
          es_postventa: a.es_postventa,
        };
        return
```

Mutado:

```js
        return
```

**K10** (app.js:2114, 1 fallo). Original:

```js
sel = (r20 ? botonPartida(r20[1]) : "") +
          `<span class="motivo">${escapeHtml(a.motivo || "")}</span>`;
```

Mutado:

```js
sel = r20 ? botonPartida(r20[1]) :
          `<span class="motivo">${escapeHtml(a.motivo || "")}</span>`;
```

## T15c · arreglos de la M2 (2026-10-11): `app.js` y `styles.css`

Mismo método, con `js_mut_t15c.py` (scratchpad de la sesión) en una COPIA
AISLADA (`git worktree add --detach` en el scratchpad, unión al `.venv` del
front, retirada después). Cada mutante cambia UN texto exacto (que aparece
una sola vez en el fichero) de lo que añade T15c, corre la suite ENTERA del
front (`pytest tests -q`, 218 tests) y anota cuántos fallan; después se
restaura. La línea es la de inicio del texto en `app.js` de `d46b012`.

- **Primera pasada** (HEAD `d46b012`): **46 generados, 45 muertos, 1 vivo
  (T20)**, 1185,4 s en serie. T20 quita la guarda `if (selector.cerrar !==
  vivo) return;` antes de `llenar(resp)`: la respuesta tardía se pintaba en el
  panel YA QUITADO (fuera de `<body>`), sin efecto visible, por eso ningún
  test lo cazaba. No es equivalente del todo (pinta y pide el foco en un
  nodo suelto, trabajo perdido): **hueco real**, cerrado con aserciones
  nuevas en `test_f050_m2_3_solo_pinta_el_ultimo_pedido` y
  `test_f050_m2_3_cerrado_mientras_carga_no_se_reabre` (el panel quitado
  sigue con «Cargando partidas…»), commit `5d75623`.
- **Segunda pasada** (HEAD `5d75623`, `app.js` igual que en `d46b012`): T20
  **muerto con 3 fallos** (48,5 s). Los otros 45 no se repiten: solo se han
  añadido aserciones, que no pueden revivir un mutante muerto.
- **Final: 46 generados, 46 muertos, 0 supervivientes.**

| Id | Fichero:línea | Texto original → mutado (exacto) | Fallos | Estado |
|---|---|---|---|---|
| T01 | app.js:483 | `if (total <= disponible) return preferidos;` → `if (total >= disponible) return preferidos;` | 6 | muerto |
| T02 | app.js:484 | `preferidos.map((w, i) => Math.min(w, minimos[i]));` → `preferidos.map((w, i) => minimos[i]);` | 1 | muerto |
| T03 | app.js:486 | `const f = Math.max(0, (disponible - suelo) / (total - suelo));` → `const f = (disponible - suelo) / (total - suelo);` | 2 | muerto |
| T04 | app.js:487 | `Math.floor(suelos[i] + (w - suelos[i]) * f)` → `Math.round(suelos[i] + (w - suelos[i]) * f)` | 3 | muerto |
| T05 | app.js:499 | `tabla.parentElement.clientWidth);` → `1e9);` | 2 | muerto |
| T06 | app.js:497 | `state.columnas.map((c) => state.anchos[c] \|\| COLUMNAS[c].ancho),` → `state.columnas.map((c) => COLUMNAS[c].ancho),` | 1 | muerto |
| T07 | app.js:502 | `.forEach((th, i) => { th.style.width = anchos[i] + "px"; });` → `.forEach((th, i) => { });` | 2 | muerto |
| T08 | app.js:504 | `tabla.style.width = anchos.reduce((s, w) => s + w, 0) + "px";` → `tabla.style.width = "100%";` | 1 | muerto |
| T09 | app.js:1911 | `new ResizeObserver(() => sincronizarAnchoTabla()).observe($("#tabla").parentElement);` → (borrado) | 1 | muerto |
| T10 | app.js:58 | `partida: 150, total: 190 };` → `partida: 150, total: 100 };` | 1 | muerto |
| T11 | app.js:716 | `if (td && c === 0) td.classList.add("col-primera");` → (borrado) | 3 | muerto |
| T12 | app.js:717 | `if (td && c === state.columnas.length - 1) td.classList.add("col-ultima");` → `if (td && c === state.columnas.length) td.classList.add("col-ultima");` | 3 | muerto |
| T13 | app.js:716 | `if (td && c === 0) td.classList.add("col-primera");` → `if (c === 0) td.classList.add("col-primera");` | 1 | muerto |
| T14 | styles.css:255 | `tr.fila.seleccionada td { background: var(--brand-soft); }` → `tr.fila.seleccionada td { background: var(--brand-soft); box-shadow: inset 3px 0 0 var(--brand); }` | 1 | muerto |
| T15 | styles.css:257 | `tr.fila.seleccionada td.col-ultima { box-shadow: inset -3px 0 0 var(--brand); }` → `tr.fila.seleccionada td.col-ultima { box-shadow: inset 3px 0 0 var(--brand); }` | 1 | muerto |
| T16 | styles.css:261 | `tr.fila.multi td.col-primera { box-shadow: inset 3px 0 0 var(--pv); }` → `tr.fila.multi td:first-child { box-shadow: inset 3px 0 0 var(--pv); }` | 1 | muerto |
| T17 | app.js:1496 | `if (selector.abierto === clave) return;` → (borrado) | 1 | muerto |
| T18 | app.js:1502 | `selector.abierto = clave;` → (borrado) | 1 | muerto |
| T19 | app.js:1484 | [exacto](#textos-exactos-t15c) | 2 | muerto |
| T20 | app.js:1516 | [exacto](#textos-exactos-t15c) | 0 → 3 | VIVO → muerto (segunda pasada) |
| T21 | app.js:1509 | [exacto](#textos-exactos-t15c) | 1 | muerto |
| T22 | app.js:1509 | [exacto](#textos-exactos-t15c) | 1 | muerto |
| T23 | app.js:1501 | `const vivo = selector.cerrar;` → `const vivo = null;` | 9 | muerto |
| T24 | app.js:1545 | `if (!panel.contains(ev.target) && !ctx.ancla.contains(ev.target)) cerrarSelectorPartida();` → `if (!panel.contains(ev.target)) cerrarSelectorPartida();` | 1 | muerto |
| T25 | app.js:1526 | `panel.innerHTML = '<div class="vacio">Cargando partidas…</div>';` → `panel.innerHTML = '';` | 3 | muerto |
| T26 | app.js:1554 | [exacto](#textos-exactos-t15c) | 1 | muerto |
| T27 | app.js:1516 | [exacto](#textos-exactos-t15c) | 8 | muerto |
| T28 | app.js:2015 | [exacto](#textos-exactos-t15c) | 1 | muerto |
| T29 | app.js:2063 | `if (!previo) return nuevo;` → (borrado) | 1 | muerto |
| T30 | app.js:2066 | `obras.splice(sitio < 0 ? obras.length : sitio, 0, ...nuevo.obras);` → `obras.splice(sitio, 0, ...nuevo.obras);` | 1 | muerto |
| T31 | app.js:2066 | `obras.splice(sitio < 0 ? obras.length : sitio, 0, ...nuevo.obras);` → `obras.push(...nuevo.obras);` | 4 | muerto |
| T32 | app.js:2067 | `return { ...previo, obras };` → `return { obras };` | 1 | muerto |
| T33 | app.js:2065 | `const obras = previo.obras.filter((o) => o.obra.ide !== obraIde);` → `const obras = previo.obras.slice();` | 6 | muerto |
| T34 | app.js:2039 | `trabajador_ide: registro.trabajadorIde, obra_ide: obraIde })` → `trabajador_ide: registro.trabajadorIde })` | 6 | muerto |
| T35 | app.js:2045 | `registro.analizando.clear();     // lo que se repetía era del modal de antes` → (borrado) | 2 | muerto |
| T36 | app.js:2051 | [exacto](#textos-exactos-t15c) | 4 | muerto |
| T37 | app.js:2080 | `registro.analizando.set(obraIde, seq);` → (borrado) | 8 | muerto |
| T38 | app.js:2085 | [exacto](#textos-exactos-t15c) | 4 | muerto |
| T39 | app.js:2086 | [exacto](#textos-exactos-t15c) | 3 | muerto |
| T40 | app.js:2091 | `registro.pf = obraIde ? unirPreflight(registro.pf, pf, obraIde) : pf;` → `registro.pf = pf;` | 4 | muerto |
| T41 | app.js:2094 | `if (registro.analizando.size && nuevo) {` → `if (false && nuevo) {` | 1 | muerto |
| T42 | app.js:2097 | [exacto](#textos-exactos-t15c) | 2 | muerto |
| T43 | app.js:2099 | [exacto](#textos-exactos-t15c) | 2 | muerto |
| T44 | app.js:2101 | `if (btn && !registro.analizando.size) {` → `if (btn) {` | 1 | muerto |
| T45 | app.js:1588 | `if (ctx.despues) ctx.despues(ctx.obraIde);` → `if (ctx.despues) ctx.despues();` | 4 | muerto |
| T46 | app.js:2083 | `const vigente = () => registro.analizando.get(obraIde) === seq;` → `const vigente = () => true;` | 5 | muerto |

### Textos exactos T15c

**T19** (static/js/app.js:1484, 2 fallos). Original:

```
  selector.cerrar = null;
  selector.abierto = null;
```

Mutado:

```
  selector.cerrar = null;
```

**T20** (static/js/app.js:1516, 0 fallos). Original:

```
  if (selector.cerrar !== vivo) return;
  llenar(resp);
```

Mutado:

```
  llenar(resp);
```

**T21** (static/js/app.js:1509, 1 fallos). Original:

```
      if (selector.cerrar !== vivo) return;
      cerrarSelectorPartida();
```

Mutado:

```
      cerrarSelectorPartida();
```

**T22** (static/js/app.js:1509, 1 fallos). Original:

```
      if (selector.cerrar !== vivo) return;
      cerrarSelectorPartida();
```

Mutado:

```
      if (selector.cerrar !== vivo) return;
```

**T26** (static/js/app.js:1554, 1 fallos). Original:

```
    panel.remove();
  };
  recolocar();
```

Mutado:

```
    panel.remove();
  };
```

**T27** (static/js/app.js:1516, 8 fallos). Original:

```
  if (selector.cerrar !== vivo) return;
  llenar(resp);
```

Mutado:

```
  if (selector.cerrar !== vivo) return;
```

**T28** (static/js/app.js:2015, 1 fallos). Original:

```
function abrirModal(html) {
  cerrarSelectorPartida();
```

Mutado:

```
function abrirModal(html) {
```

**T36** (static/js/app.js:2051, 4 fallos). Original:

```
    registro.pisar = new Set();
    registro.pf = pf;
```

Mutado:

```
    registro.pisar = new Set();
```

**T38** (static/js/app.js:2085, 4 fallos). Original:

```
    const pf = await pedirPreflight(obraIde);
    if (!vigente()) return;
```

Mutado:

```
    const pf = await pedirPreflight(obraIde);
```

**T39** (static/js/app.js:2086, 3 fallos). Original:

```
    if (!vigente()) return;
    registro.analizando.delete(obraIde);
    if ($(
```

Mutado:

```
    if (!vigente()) return;
    if ($(
```

**T42** (static/js/app.js:2097, 2 fallos). Original:

```
  } catch (err) {
    if (!vigente()) return;
```

Mutado:

```
  } catch (err) {
```

**T43** (static/js/app.js:2099, 2 fallos). Original:

```
    registro.analizando.delete(obraIde);
    toast(err.message, true);
```

Mutado:

```
    toast(err.message, true);
```
