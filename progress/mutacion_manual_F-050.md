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

| Id | app.js:línea | Texto original → mutado (exacto, espacios plegados) | Fallos |
|---|---|---|---|
| J01 | 122 | `if (!p \|\| p.partida_ide == null) return "";` → `if (!p) return "";` | 1 |
| J02 | 123 | `.filter(Boolean).join(" · ") \|\|` → `.filter(Boolean).join(" - ") \|\|` | 1 |
| J03 | 124 | ``partida ${p.partida_ide}`; }` → ``${p.partida_ide}`; }` | 1 |
| J04 | 133 | `if (mayor && p.mayor !== mayor) return false;` → `if (mayor && p.mayor === mayor) return false;` | 6 |
| J05 | 135 | `return palabras.every((w) => pajar.includes(w));` → `return palabras.some((w) => pajar.includes(w));` | 9 |
| J06 | 134 | `const pajar = normalizar(`${p.cod \|\| ""} ${p.res \|\| ""}`);` → `const pajar = normalizar(`${p.res \|\| ""}`);` | 3 |
| J07 | 131 | `const palabras = normalizar(texto).split(/\s+/).filter(Boolean);` → `const palabras = [normalizar(texto)];` | 1 |
| J08 | 145 | `const primera = prop ? lista.find((p) => p.ide === prop.paride) : unde…` → `const primera = prop ? resp.partidas.find((p) => p.ide === prop.paride…` | 1 |
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
| J20 | 609 | `" " + t.lineas.map((l) => `${l.partida_cod \|\| ""} ${l.partida_res \|…` → `""` | 1 |
| J21 | 670 | `const n = Math.max(1, t.lineas.length);` → `const n = 1;` | 1 |
| J22 | 686 | `td.rowSpan = n;` → `td.rowSpan = 1;` | 1 |
| J23 | 673 | `tr.className = idx ? "fila subfila" : "fila";` → `tr.className = "fila";` | 1 |
| J24 | 53 | `const COLUMNAS_POR_LINEA = ["asignaciones", "partida"];` → `const COLUMNAS_POR_LINEA = ["asignaciones"];` | 1 |
| J25 | 966 | `const l = t.lineas[idx]; if (!l) {` → `const l = t.lineas[0]; if (!l) {` | 1 |
| J26 | 994 | `} else if (l.partida_ide != null) { td.innerHTML = `<span class="parti…` → `} else if (l.partida_ide == null) { td.innerHTML = `<span class="parti…` | 1 |
| J27 | 999 | `if (state.periodoEstado === "ABIERTO" && !l.partida_fija) {` → `if (!l.partida_fija) {` | 1 |
| J28 | 1002 | `ev.stopPropagation(); abrirSelectorPartida(t.ide, l.obra_ide, l.es_pos…` → `abrirSelectorPartida(t.ide, l.obra_ide, l.es_postventa, td);` | 1 |
| J29 | 1666 | `viejas.forEach((tr) => tr.remove());` → `(borrado)` | 1 |
| J30 | 1462 | `if (state.editandoIde === trabajadorIde) await guardarAhora();` → `(borrado)` | 1 |
| J31 | 1473 | `selector.cache.set(clave, resp);` → `(borrado)` | 1 |
| J32 | 1465 | `let resp = selector.cache.get(clave);` → `let resp = undefined;` | 1 |
| J33 | 309 | `selector.cache.clear(); // F-050` → `// F-050` | 1 |
| J34 | 1449 | `return [state.anio, state.mes, state.empresa, trabajadorIde, obraIde, …` → `return [trabajadorIde, obraIde, esPostventa].join("\|");` | 1 |
| J35 | 1497 | `let mayor = resp.ambito \|\| null;` → `let mayor = null;` | 1 |
| J36 | 1494 | `partidas: ctx.esPostventa ? resp.partidas_postventa : resp.partidas,` → `partidas: resp.partidas,` | 1 |
| J37 | 1517 | `const partida = op.automatica ? null : { ide: op.ide, cod: op.cod, res…` → `const partida = { ide: op.ide, cod: op.cod, res: op.res };` | 1 |
| J38 | 1524 | `selector.cache.delete(ctx.clave);` → `(borrado)` | 2 |
| J39 | 1526 | `if (ctx.despues) ctx.despues();` → `(borrado)` | 3 |
| J40 | 1525 | `aplicarFila(datos); if (ctx.despues)` → `if (ctx.despues)` | 2 |
| J41 | 1534 | `opciones = listaSelector(base, input.value, mayor).concat([{ automatic…` → `opciones = listaSelector(base, input.value, mayor);` | 1 |
| J42 | 1595 | `elegir(opciones[activa]);` → `elegir(opciones[0]);` | 1 |
| J43 | 1584 | `ev.stopPropagation(); if (ev.key === "ArrowDown") { ev.preventDefault(…` → `if (ev.key === "ArrowDown") { ev.preventDefault(); activa = Math.min(a…` | 1 |
| J44 | 1576 | `mayor = b.dataset.mayor \|\| null;` → `mayor = null;` | 1 |
| J45 | 1523 | `es_postventa: ctx.esPostventa, partida }) });` → `es_postventa: false, partida }) });` | 2 |
| J46 | 1544 | `: `<span class="cod">` → `: `<span class="cod">X` | 2 |
| J47 | 1970 | `if (!a.paride) return "sin partida";` → `if (a.paride == null) return "sin partida";` | 2 |
| J48 | 1971 | `return a.partida_cod \|\| `partida ${a.paride}`;` → `return `partida ${a.paride}`;` | 4 |
| J49 | 2094 | `trabajador: a.recurso_ide, obra_ide: o.obra.ide,` → `trabajador: a.recurso_ide, obra_ide: o.obra.codigo,` | 3 |
| J50 | 2095 | `es_postventa: a.es_postventa, };` → `es_postventa: false, };` | 1 |
| J51 | 2132 | `abrirSelectorPartida(l.trabajador, l.obra_ide, l.es_postventa, boton, …` → `abrirSelectorPartida(l.trabajador, l.obra_ide, l.es_postventa, boton, …` | 4 |
| J52 | 2100 | `(origen ? `<div class="origen-partida">${escapeHtml(origen)}</div>` : …` → `""` | 2 |
| J53 | 2099 | ``${escapeHtml(textoPartidaAccion(a))}</button>`` → ``${textoPartidaAccion(a)}</button>`` | 1 |
| J54 | 1979 | `body: JSON.stringify({ trabajador_ide: registro.trabajadorIde }) });` → `body: JSON.stringify({}) });` | 6 |
| J55 | 2147 | `pisar_claves: pisar, trabajador_ide: registro.trabajadorIde,` → `pisar_claves: pisar,` | 1 |
| J56 | 2069 | `registro.lineas = {}; let html` → `let html` | 1 |
