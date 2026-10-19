<!-- progress/mutacion_manual_F-057.md -->
# F-057 · Campaña de mutación manual del front (`app.js`)

El arnés no muta JavaScript: campaña a mano, como en F-055, con un script del
implementer (`js_mut.py`, en el scratchpad de la sesión) sobre una COPIA
AISLADA (`git worktree add --detach` de HEAD `1258c98`), nunca en la copia de
trabajo. Cada mutante cambia UN texto exacto de
`services/dedicacion-front/static/js/app.js` (que aparece una sola vez) en el
código de F-057, corre `tests/test_f057_buscando_pendientes.py`,
`tests/test_f055_propuesta_celda.py` y `tests/test_f050_subfilas.py` con el
venv del front (un subconjunto de la suite: solo puede dejar MÁS vivos) y
anota cuántos tests fallan; el fichero se restaura tras cada uno. Línea base:
52 passed en 5,25 s. **13 mutantes, 13 muertos, 0 supervivientes, 91,2 s en
serie.**

Nota: el script escribía el fichero con fin de línea CRLF (`write_text` en
Windows; el original es LF). Para descartar que los muertos lo fueran por eso,
tras la campaña se corrió el mismo subconjunto sobre el `app.js` restaurado
(CRLF, sin mutar) en el worktree: **52 passed en 4,45 s**. La única diferencia
entre esa base y cada mutante es la mutación. El worktree se borró después.

Para reproducir una fila: en una copia aislada, sustituir el texto original
(con sus saltos de línea y sangría reales; aquí van plegados) por el mutado y
lanzar, desde `services/dedicacion-front`,
`.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_f057_buscando_pendientes.py tests/test_f055_propuesta_celda.py tests/test_f050_subfilas.py`.

| Id | app.js:línea | Texto original → mutado (espacios plegados) | Fallos |
|---|---|---|---|
| J01 | 184 | `return l.propuesta_pendiente ? '<span` → `return !l.propuesta_pendiente ? '<span` | 7 |
| J02 | 184 | `return l.propuesta_pendiente ? '<span` → `return state.propuestasEnCurso ? '<span` | 5 |
| J03 | 386 | `p.trabajador_ide === t.ide && p.obra_ide === l.obra_ide &&` → `p.obra_ide === l.obra_ide &&` | 1 |
| J04 | 386 | `p.trabajador_ide === t.ide && p.obra_ide === l.obra_ide &&` → `p.trabajador_ide === t.ide &&` | 2 |
| J05 | 387 | `p.es_postventa === l.es_postventa); }); });` → `true); }); });` | 3 |
| J06 | 385 | `l.propuesta_pendiente = pendientes.some((p) =>` → `l.propuesta_pendiente = pendientes.every((p) =>` | 4 |
| J07 | 385 | `l.propuesta_pendiente = pendientes.some((p) =>` → `l.propuesta_pendiente = l.propuesta_pendiente || pendientes.some((p) =>` | 4 |
| J08 | 430 | `aplicarPendientes((datos && datos.pendientes) || []);` → `(nada)` | 4 |
| J09 | 430 | `aplicarPendientes((datos && datos.pendientes) || []);` → `if (datos) aplicarPendientes(datos.pendientes || []);` | 2 |
| J10 | 444 | `if (!l || l.partida_fija) return; td.innerHTML = htmlPartida(l);` → `if (!l || l.partida_fija) return; td.innerHTML = htmlPartida({...l, propuesta_pendiente: state.propuestasEnCurso});` | 2 |
| J11 | 1214 | `} else if (l.propuesta_cod || l.propuesta_pendiente) {` → `} else if (l.propuesta_cod || state.propuestasEnCurso) {` | 2 |
| J12 | 1214 | `} else if (l.propuesta_cod || l.propuesta_pendiente) {` → `} else if (l.propuesta_cod) {` | 1 |
| J13 | 430 | `aplicarPendientes((datos && datos.pendientes) || []); state.propuestasEnCurso = !!(datos && datos.en_curso); repintarCeldasPartida();` → `state.propuestasEnCurso = !!(datos && datos.en_curso); repintarCeldasPartida(); aplicarPendientes((datos && datos.pendientes) || []);` | 1 |
