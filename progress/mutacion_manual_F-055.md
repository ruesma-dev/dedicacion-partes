<!-- progress/mutacion_manual_F-055.md -->
# F-055 · Campaña de mutación manual del front (`app.js`)

El arnés no muta JavaScript: campaña a mano con el script del implementer
(`js_mut.py`, en el scratchpad de la sesión), en una COPIA AISLADA
(`git worktree add --detach`), nunca en la copia de trabajo. Cada mutante
cambia UN texto exacto de `services/dedicacion-front/static/js/app.js` (que
aparece una sola vez) en el código de T13 y T13b, corre
`tests/test_f055_propuesta_celda.py` y `tests/test_f050_subfilas.py` (un
subconjunto de la suite: solo puede dejar MÁS vivos) y anota cuántos tests
fallan. El fichero se restaura después de cada uno.

- **Primera pasada** (HEAD `337ea74`): 36 mutantes,
  **32 muertos, 4 vivos**
  (J07, J10, J15, J35), 1090.5 s. Los cuatro eran huecos reales:
  `68a5c6b` añade `test_f055_r36_la_propuesta_va_a_su_modo_y_con_sus_tres_campos`
  (J07, J10, J35) y `test_f055_r36_tras_reiniciar_se_puede_volver_a_consultar`
  (J15).
- **Segunda pasada** (`app.js` de `337ea74`, igual que en `68a5c6b`, con los
  tests de `68a5c6b`): **36 generados,
  36 muertos, 0
  supervivientes**, 1045.8 s en serie.

| Id | app.js:línea | Texto original → mutado (espacios plegados) | Fallos |
|---|---|---|---|
| J01 | 172 | `if (l.partida_ide != null) { return `<span class="partida-elegida">` → `if (l.partida_ide == null) { return `<span class="partida-elegida">` | 6 |
| J02 | 175 | `if (l.propuesta_cod) { const metodo` → `if (l.propuesta_res) { const metodo` | 1 |
| J03 | 177 | `[l.propuesta_cod, l.propuesta_res].filter(Boolean).join(" · ")` → `[l.propuesta_cod, l.propuesta_res].filter(Boolean).join(" - ")` | 2 |
| J04 | 178 | `title="Propuesta: ${escapeHtml(metodo)}"` → `title="${escapeHtml(metodo)}"` | 3 |
| J05 | 182 | `return enCurso ? '<span class="partida-auto buscando">` → `return !enCurso ? '<span class="partida-auto buscando">` | 2 |
| J06 | 183 | `buscando partida…</span>' : '<span class="partida-auto">automática` → `buscando…</span>' : '<span class="partida-auto">automática` | 1 |
| J07 | 368 | `x.es_postventa === p.es_postventa && x.partida_ide == null);` → `x.partida_ide == null);` | 1 |
| J08 | 368 | `x.es_postventa === p.es_postventa && x.partida_ide == null);` → `x.es_postventa === p.es_postventa);` | 1 |
| J09 | 369 | `if (!l) return; l.propuesta_cod = p.propuesta_cod;` → `l.propuesta_cod = p.propuesta_cod;` | 2 |
| J10 | 372 | `l.propuesta_metodo = p.propuesta_metodo;` → `(nada)` | 1 |
| J11 | 379 | `state.propuestasEnCurso = !!enCurso;` → `state.propuestasEnCurso = true;` | 2 |
| J12 | 379 | `state.propuestasEnCurso = !!enCurso; if (state.propuestasEnCurso) seguirPropuestas();` → `state.propuestasEnCurso = !!enCurso;` | 6 |
| J13 | 385 | `propuestas.generacion += 1;` → `(nada)` | 1 |
| J14 | 386 | `if (propuestas.timer !== null) clearTimeout(propuestas.timer);` → `(nada)` | 2 |
| J15 | 386 | `clearTimeout(propuestas.timer); propuestas.timer = null;` → `clearTimeout(propuestas.timer);` | 1 |
| J16 | 392 | `if (propuestas.timer !== null) return; const generacion` → `const generacion` | 2 |
| J17 | 398 | `}, INTERVALO_PROPUESTAS);` → `}, 0);` | 1 |
| J18 | 98 | `const INTERVALO_PROPUESTAS = 5000;` → `const INTERVALO_PROPUESTAS = 500;` | 2 |
| J19 | 411 | `if (generacion !== propuestas.generacion) return; if (datos)` → `if (datos)` | 1 |
| J20 | 412 | `if (datos) aplicarPropuestas(datos.lineas \|\| []);` → `(nada)` | 2 |
| J21 | 413 | `state.propuestasEnCurso = !!(datos && datos.en_curso);` → `state.propuestasEnCurso = !!datos;` | 2 |
| J22 | 414 | `repintarCeldasPartida(); if (state.propuestasEnCurso) seguirPropuestas();` → `if (state.propuestasEnCurso) seguirPropuestas();` | 2 |
| J23 | 414 | `repintarCeldasPartida(); if (state.propuestasEnCurso) seguirPropuestas();` → `repintarCeldasPartida();` | 1 |
| J24 | 423 | `if (ide === state.editandoIde) return;` → `(nada)` | 1 |
| J25 | 426 | `if (!l \|\| l.partida_fija) return;` → `if (!l) return;` | 1 |
| J26 | 1189 | `td.dataset.ide = t.ide;` → `(nada)` | 1 |
| J27 | 1196 | `} else if (l.propuesta_cod \|\| state.propuestasEnCurso) {` → `} else if (l.propuesta_cod) {` | 1 |
| J28 | 354 | `reiniciarPropuestas(); marcarPropuestas(datos.propuestas_en_curso);` → `marcarPropuestas(datos.propuestas_en_curso);` | 1 |
| J29 | 1912 | `marcarPropuestas(datos.propuestas_en_curso); renderCabecera();` → `renderCabecera();` | 1 |
| J30 | 1102 | `fijarSeleccion([]); marcarPropuestas(datos.propuestas_en_curso);` → `fijarSeleccion([]);` | 1 |
| J31 | 2040 | `); marcarPropuestas(datos.propuestas_en_curso); // F-055 (R36, D9) await cargarPeriodo` → `); await cargarPeriodo` | 1 |
| J32 | 396 | `propuestas.timer = null; consultarPropuestas(generacion, ruta);` → `consultarPropuestas(generacion, ruta);` | 1 |
| J33 | 394 | `${state.mes}/propuestas`;` → `${state.mes}/propuesta`;` | 1 |
| J34 | 1190 | `td.dataset.linea = idx;` → `(nada)` | 1 |
| J35 | 371 | `l.propuesta_res = p.propuesta_res;` → `(nada)` | 1 |
| J36 | 92 | `propuestasEnCurso: false,` → `propuestasEnCurso: true,` | 1 |
