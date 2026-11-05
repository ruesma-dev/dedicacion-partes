<!-- progress/mutacion_manual_F-054.md -->
# F-054 · Mutación manual de `app.js`

`python -m harness.mutacion` **solo muta Python** y la puerta de cobertura de
`init.sh` no mide JS. F-054 añade al front la ventana de «traer de Sigrid»
(T9) y la sección de sobrantes del modal de registro (T15), todo en
`services/dedicacion-front/static/js/app.js`. Esta campaña sustituye a la
automática para esas líneas (patrón de `progress/mutacion_manual_F-068.md`).

- **Siempre sobre una copia**: el script extrae `HEAD` con `git archive` a un
  directorio temporal y reescribe allí `app.js` por mutante (el original
  tiene que aparecer **una sola vez**; si no, aborta), `node --check` y los
  cinco ficheros de test que cargan esas funciones **sin `-x`**:
  `test_f054_traer_front.py`, `test_f054_modal_cero.py`,
  `test_f050_modal_registro.py`, `test_f064_pisado_vinculados.py` y
  `test_f050_t15e_sombreado.py`. El árbol de trabajo no se toca. En serie
  (**1 worker**).
- **Qué se muta**: cada condición, rama, texto y campo que añade F-054 a
  `app.js` (44 de T9 y 25 de T15). Los comentarios no se mutan.
- Convención de las celdas: `\|` es `|`; los espacios aplanados; «(nada)»
  es borrar el texto. El canónico es la lista `M` del script.

## Campaña 1 (`95cc089`): 69 mutantes, 60 muertos, 9 supervivientes

Línea base (sin mutar, en verde): 51 passed in 8.83s · Tiempo: 806.5 s

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| A1 sincronizar con éxito devuelve false | `app.js:2824` | `return true; // F-054 (R1)` → `return false; // F-054 (R1)` | MUERTO | 2 | test_f054_r1_sincronizar_devuelve_si_fue_bien, test_f054_r1_tras_un_sync_con_exito_se_pide_comparar |
| A2 sincronizar fallido devuelve true | `app.js:2826` | `toast(err.message, true); return false; } finally { boton.disabled = false; boton.textContent = "Sincronizar Sigrid";` → `toast(err.message, true); return true; } finally { boton.disabled = false; boton.textContent = "Sincronizar Sigrid";` | MUERTO | 2 | test_f054_r1_sincronizar_devuelve_si_fue_bien, test_f054_r1_tras_un_sync_fallido_no_se_compara |
| A3 compara aunque el sync falle | `app.js:2839` | `if (await sincronizar()) await traerDeSigrid([]);` → `await sincronizar(); await traerDeSigrid([]);` | MUERTO | 1 | test_f054_r1_tras_un_sync_fallido_no_se_compara |
| A4 no manda `aceptar` | `app.js:2848` | `body: JSON.stringify({ aceptar }),` → `body: JSON.stringify({}),` | MUERTO | 7 | test_f054_r1_tras_un_sync_con_exito_se_pide_comparar, test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r28_sin_pulsar_no_se_manda_nada |
| A5 condición de comparar invertida | `app.js:2854` | `if (!aceptar.length) { abrirTraerSigrid(datos); return; }` → `if (aceptar.length) { abrirTraerSigrid(datos); return; }` | MUERTO | 7 | test_f054_r1_tras_un_sync_con_exito_se_pide_comparar, test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r28_sin_pulsar_no_se_manda_nada |
| A6 no cierra el modal al aceptar | `app.js:2855` | `cerrarModal(); const rechazadas` → `const rechazadas` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A7 el toast de rechazadas nunca es error | `app.js:2860` | `: ""), rechazadas.length > 0);` → `: ""), false);` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A8 sin el motivo de las rechazadas | `app.js:2859` | `rechazadas.map((r) => r.motivo).join("; ")` → `""` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A9 no marca las propuestas en curso | `app.js:2861` | `marcarPropuestas(datos.propuestas_en_curso); // F-055 (R26) await cargarPeriodo(state.anio, state.mes); } function textoEstadoSigrid` → `await cargarPeriodo(state.anio, state.mes); } function textoEstadoSigrid` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A10 no recarga el periodo tras aceptar | `app.js:2862` | `await cargarPeriodo(state.anio, state.mes); } function textoEstadoSigrid` → `} function textoEstadoSigrid` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A11 rótulo de solo_sigrid crudo | `app.js:2867` | `solo_sigrid: "solo en Sigrid",` → `solo_sigrid: "solo_sigrid",` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A12 rótulo de no_traducible crudo | `app.js:2868` | `no_traducible: "no se puede traer",` → `no_traducible: "no_traducible",` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A13 casilla solo si las dos (&&) | `app.js:2876` | `const conCasilla = e.estado === "distinta" \|\| e.estado === "solo_sigrid";` → `const conCasilla = e.estado === "distinta" && e.estado === "solo_sigrid";` | MUERTO | 1 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid |
| A14 casilla también en igual | `app.js:2876` | `const conCasilla = e.estado === "distinta" \|\| e.estado === "solo_sigrid";` → `const conCasilla = e.estado !== "no_traducible";` | MUERTO | 2 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar |
| A15 todas marcadas por defecto | `app.js:2882` | `${e.estado === "solo_sigrid" ? " checked" : ""}>`` → `${" checked"}>`` | MUERTO | 1 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid |
| A16 ninguna marcada por defecto | `app.js:2882` | `${e.estado === "solo_sigrid" ? " checked" : ""}>`` → `${""}>`` | MUERTO | 1 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid |
| A17 data-postventa invertido | `app.js:2881` | `data-postventa="${e.es_postventa ? 1 : 0}"` → `data-postventa="${e.es_postventa ? 0 : 1}"` | MUERTO | 1 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid |
| A18 pct de undefined no es — | `app.js:2884` | `(v === null \|\| v === undefined ? "—" : fmtPct(v))` → `(v === null ? "—" : fmtPct(v))` | SUPERVIVIENTE | 0 | — |
| A19 pct de null no es — | `app.js:2884` | `(v === null \|\| v === undefined ? "—" : fmtPct(v))` → `(v === undefined ? "—" : fmtPct(v))` | SUPERVIVIENTE | 0 | — |
| A20 sin «(postventa)» en la obra | `app.js:2885` | `${e.es_postventa ? " (postventa)" : ""}`;` → ``;` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A21 sin el parte en el detalle | `app.js:2886` | `e.parte_cod ? `parte ${e.parte_cod}` : "",` → `"",` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A22 sin la partida en el detalle | `app.js:2887` | `e.partida_cod ? `partida ${e.partida_cod}` : "", e.motivo \|\| ""]` → `"", e.motivo \|\| ""]` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A23 sin el motivo en el detalle | `app.js:2887` | `: "", e.motivo \|\| ""]` → `: "", ""]` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A24 sin la columna del cuadrante | `app.js:2891` | ``<td>${pct(e.pct_cuadrante)}</td><td>${pct(e.pct_sigrid)}</td>`` → ``<td></td><td>${pct(e.pct_sigrid)}</td>`` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A25 sin la columna de Sigrid | `app.js:2891` | ``<td>${pct(e.pct_cuadrante)}</td><td>${pct(e.pct_sigrid)}</td>`` → ``<td>${pct(e.pct_cuadrante)}</td><td></td>`` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A26 resumen sin líneas leídas | `app.js:2897` | ``${datos.lineas_leidas} líneas leídas en los partes`,` → `(nada)` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A27 resumen sin las de pruebas | `app.js:2898` | ``${datos.excluidas_pruebas} de la obra de pruebas`,` → `(nada)` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A28 resumen sin vinculados | `app.js:2899` | ``${datos.de_vinculados} de recursos vinculados`,` → `(nada)` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A29 resumen sin fuera del maestro | `app.js:2900` | ``${datos.fuera_maestro} de recursos fuera del maestro`,` → `(nada)` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A30 sin el aviso de postventa | `app.js:2904` | `[datos.motivo_postventa, datos.motivo_var].filter(Boolean)` → `[datos.motivo_var].filter(Boolean)` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A31 sin el aviso de VAR | `app.js:2904` | `[datos.motivo_postventa, datos.motivo_var].filter(Boolean)` → `[datos.motivo_postventa].filter(Boolean)` | SUPERVIVIENTE | 0 | — |
| A32 texto de vacío invertido | `app.js:2908` | `if (!trabajadores.length) { html += "<p>Ningún` → `if (trabajadores.length) { html += "<p>Ningún` | SUPERVIVIENTE | 0 | — |
| A33 sin cabecera del trabajador | `app.js:2913` | `html += `<h3>${escapeHtml(`${t.cod} · ${t.nombre}`)}</h3>` +` → `html += `<h3></h3>` +` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A34 no cuenta las casillas | `app.js:2918` | `e.estado === "solo_sigrid") casillas += 1;` → `e.estado === "solo_sigrid") casillas += 0;` | MUERTO | 4 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A35 botón de aceptar siempre | `app.js:2932` | `(casillas ? `<button class="btn primary" id="btn-traer-aceptar">` → `(true ? `<button class="btn primary" id="btn-traer-aceptar">` | MUERTO | 1 | test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar |
| A36 sin la lista de no traídas | `app.js:2924` | `if (noTraidas.length) {` → `if (false) {` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A37 no traídas sin su motivo | `app.js:2928` | ``${n.recurso_ide}: ${n.motivo}`)}</li>`)` → ``${n.recurso_ide}`)}</li>`)` | MUERTO | 1 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api |
| A38 aceptadas sin filtrar por marcadas | `app.js:2938` | `#modal-registro .chk-traer:checked` → `#modal-registro .chk-traer` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A39 trabajador_ide sin Number | `app.js:2940` | `trabajador_ide: Number(c.dataset.trabajador),` → `trabajador_ide: c.dataset.trabajador,` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A40 obra_ide sin Number | `app.js:2941` | `obra_ide: Number(c.dataset.obra),` → `obra_ide: c.dataset.obra,` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A41 es_postventa invertido | `app.js:2942` | `es_postventa: c.dataset.postventa === "1",` → `es_postventa: c.dataset.postventa === "0",` | MUERTO | 1 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga |
| A42 aceptar sin marcadas no avisa | `app.js:2953` | `if (!marcadas.length) {` → `if (false) {` | MUERTO | 1 | test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda |
| A43 el botón de sync sin traer | `app.js:2982` | `$("#btn-sync").addEventListener("click", () => sincronizarYTraer());` → `$("#btn-sync").addEventListener("click", () => sincronizar());` | MUERTO | 1 | test_f054_r1_el_boton_de_sync_llama_a_sincronizar_y_traer |
| A44 un error de comparar no avisa | `app.js:2851` | `toast(`No se pudo comparar con Sigrid: ${err.message}`, true);` → `(nada)` | MUERTO | 1 | test_f054_r28_un_error_se_avisa_sin_recargar |
| B1 un preflight nuevo no desmarca | `app.js:3179` | `registro.cero = new Set(); // F-054 (D17): las sobrantes, desmarcadas` → `(nada)` | MUERTO | 1 | test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas |
| B2 el repreflight pierde lo marcado | `app.js:3221` | `registro.cero = new Set([...document.querySelectorAll(".chk-cero:checked")] .map((c) => c.value));` → `registro.cero = new Set();` | MUERTO | 1 | test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas |
| B3 sin la sección de sobrantes | `app.js:3586` | `if ((pf.sobrantes \|\| []).length) html += pintarSobrantes(pf);` → `(nada)` | MUERTO | 3 | test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas, test_f054_r33_seccion_casillas_desmarcadas_y_avisos, test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar |
| B4 la sección también con lista vacía | `app.js:3586` | `if ((pf.sobrantes \|\| []).length) html += pintarSobrantes(pf);` → `if (pf.sobrantes) html += pintarSobrantes(pf);` | MUERTO | 1 | test_f054_r33_sin_sobrantes_el_modal_de_hoy |
| B5 sin el título de la sección | `app.js:3615` | `"<h3>En Sigrid, en obras que no tiene en la plataforma</h3>" +` → `"" +` | MUERTO | 1 | test_f054_r33_seccion_casillas_desmarcadas_y_avisos |
| B6 el vinculado sin tipo | `app.js:3619` | ``${s.vinculado.tipo \|\| ""} ${s.vinculado.cod \|\| ""} de ` +` → `` ${s.vinculado.cod \|\| ""} de ` +` | SUPERVIVIENTE | 0 | — |
| B7 el vinculado sin código | `app.js:3619` | ``${s.vinculado.tipo \|\| ""} ${s.vinculado.cod \|\| ""} de ` +` → ``${s.vinculado.tipo \|\| ""} de ` +` | SUPERVIVIENTE | 0 | — |
| B8 el vinculado con su propio nombre | `app.js:3620` | `nombreTrabajador(s.vinculado.titular_ide)` → `nombreTrabajador(s.recurso_ide)` | SUPERVIVIENTE | 0 | — |
| B9 el vinculado como trabajador | `app.js:3618` | `const quien = s.vinculado` → `const quien = false` | SUPERVIVIENTE | 0 | — |
| B10 obra por su ide | `app.js:3622` | `obra ${s.obra_cod \|\| s.obra_ide}` → `obra ${s.obra_ide}` | MUERTO | 1 | test_f054_r33_seccion_casillas_desmarcadas_y_avisos |
| B11 sin el parte | `app.js:3623` | ``parte ${s.parte_cod \|\| "—"} · ${s.hora \|\| ""} · ` +` → ``parte — · ${s.hora \|\| ""} · ` +` | MUERTO | 1 | test_f054_r33_seccion_casillas_desmarcadas_y_avisos |
| B12 sin la hora | `app.js:3623` | ``parte ${s.parte_cod \|\| "—"} · ${s.hora \|\| ""} · ` +` → ``parte ${s.parte_cod \|\| "—"} · · ` +` | SUPERVIVIENTE | 0 | — |
| B13 sin la partida | `app.js:3624` | ``${s.partida_cod \|\| "sin partida"} · ${fmtPct((s.can \|\| 0) * 100)}`;` → ``sin partida · ${fmtPct((s.can \|\| 0) * 100)}`;` | MUERTO | 1 | test_f054_r33_seccion_casillas_desmarcadas_y_avisos |
| B14 el % sin ×100 | `app.js:3624` | `${fmtPct((s.can \|\| 0) * 100)}`;` → `${fmtPct((s.can \|\| 0))}`;` | MUERTO | 1 | test_f054_r33_seccion_casillas_desmarcadas_y_avisos |
| B15 todas confirmables | `app.js:3625` | `if (s.confirmable) {` → `if (true) {` | MUERTO | 2 | test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas, test_f054_r33_seccion_casillas_desmarcadas_y_avisos |
| B16 ninguna confirmable | `app.js:3625` | `if (s.confirmable) {` → `if (false) {` | MUERTO | 3 | test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas, test_f054_r33_seccion_casillas_desmarcadas_y_avisos, test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar |
| B17 nunca marcadas al repintar | `app.js:3628` | `${registro.cero.has(s.clave) ? " checked" : ""}> ` +` → `${""}> ` +` | MUERTO | 1 | test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas |
| B18 siempre marcadas (contra D17) | `app.js:3628` | `${registro.cero.has(s.clave) ? " checked" : ""}> ` +` → `${" checked"}> ` +` | MUERTO | 4 | test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas, test_f054_r33_seccion_casillas_desmarcadas_y_avisos, test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar, test_f054_r35_sin_marcar_no_se_manda_nada |
| B19 el aviso sin su motivo | `app.js:3632` | ``${escapeHtml(s.motivo \|\| "")}</div>`;` → ``</div>`;` | MUERTO | 1 | test_f054_r33_seccion_casillas_desmarcadas_y_avisos |
| B20 manda todas las sobrantes | `app.js:3646` | `.filter((x) => ceros.has(x.clave));` → `.filter(() => true);` | MUERTO | 2 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar, test_f054_r35_sin_marcar_no_se_manda_nada |
| B21 lee las marcadas de pisar | `app.js:3643` | `const ceros = new Set([...document.querySelectorAll(".chk-cero:checked")]` → `const ceros = new Set([...document.querySelectorAll(".chk-pisar:checked")]` | MUERTO | 1 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar |
| B22 sobrantes_a_cero siempre | `app.js:3655` | `...(sobrantes.length ? { sobrantes_a_cero: sobrantes } : {})` → `...({ sobrantes_a_cero: sobrantes })` | MUERTO | 1 | test_f054_r35_sin_marcar_no_se_manda_nada |
| B23 sobrantes_a_cero nunca | `app.js:3655` | `...(sobrantes.length ? { sobrantes_a_cero: sobrantes } : {})` → `...({})` | MUERTO | 1 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar |
| B24 toast sin las puestas a 0 | `app.js:3674` | `? ` · ${r.sobrantes_a_cero.puestas.length} puestas a 0` +` → `? `` +` | MUERTO | 1 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar |
| B25 toast sin las omitidas | `app.js:3675` | `(r.sobrantes_a_cero.omitidas.length` → `(false` | MUERTO | 1 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar |

## Análisis de los 9 supervivientes (todos huecos reales, ninguno equivalente)

- **A18, A19** (`pct` de la ventana): ningún test miraba la celda de un %
  ausente; con el mutante sale `null%`/`undefined%`. Test nuevo
  `test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya`.
- **A31** (aviso de VAR): los datos del test traían `motivo_var: null`.
  Test nuevo `test_f054_r28_los_avisos_de_postventa_y_de_var`.
- **A32** (texto de vacío): solo se miraba con trabajadores. Test nuevo
  `test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores`.
- **B6-B9, B12** (texto de la sobrante): el test buscaba los textos en todo
  el modal y el pisado de vinculado de F-064 del mismo escenario ya trae
  «TF TF-10 de GONZALEZ PANIAGUA» y «MADM». Test nuevo
  `test_f054_r33_el_texto_de_cada_sobrante_en_su_seccion`, que mira solo
  la sección y cada sobrante por separado.

Los cuatro tests van en el commit `e72d22c`.

## Campaña 2 (`e72d22c`): los 9 supervivientes, 9 muertos, 0 supervivientes

Línea base (sin mutar, en verde): 55 passed in 8.98s · Tiempo: 102.5 s

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| A18 pct de undefined no es — | `app.js:2884` | `(v === null \|\| v === undefined ? "—" : fmtPct(v))` → `(v === null ? "—" : fmtPct(v))` | MUERTO | 1 | test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya |
| A19 pct de null no es — | `app.js:2884` | `(v === null \|\| v === undefined ? "—" : fmtPct(v))` → `(v === undefined ? "—" : fmtPct(v))` | MUERTO | 1 | test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya |
| A31 sin el aviso de VAR | `app.js:2904` | `[datos.motivo_postventa, datos.motivo_var].filter(Boolean)` → `[datos.motivo_postventa].filter(Boolean)` | MUERTO | 1 | test_f054_r28_los_avisos_de_postventa_y_de_var |
| A32 texto de vacío invertido | `app.js:2908` | `if (!trabajadores.length) { html += "<p>Ningún` → `if (trabajadores.length) { html += "<p>Ningún` | MUERTO | 1 | test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores |
| B6 el vinculado sin tipo | `app.js:3619` | ``${s.vinculado.tipo \|\| ""} ${s.vinculado.cod \|\| ""} de ` +` → `` ${s.vinculado.cod \|\| ""} de ` +` | MUERTO | 1 | test_f054_r33_el_texto_de_cada_sobrante_en_su_seccion |
| B7 el vinculado sin código | `app.js:3619` | ``${s.vinculado.tipo \|\| ""} ${s.vinculado.cod \|\| ""} de ` +` → ``${s.vinculado.tipo \|\| ""} de ` +` | MUERTO | 1 | test_f054_r33_el_texto_de_cada_sobrante_en_su_seccion |
| B8 el vinculado con su propio nombre | `app.js:3620` | `nombreTrabajador(s.vinculado.titular_ide)` → `nombreTrabajador(s.recurso_ide)` | MUERTO | 1 | test_f054_r33_el_texto_de_cada_sobrante_en_su_seccion |
| B9 el vinculado como trabajador | `app.js:3618` | `const quien = s.vinculado` → `const quien = false` | MUERTO | 1 | test_f054_r33_el_texto_de_cada_sobrante_en_su_seccion |
| B12 sin la hora | `app.js:3623` | ``parte ${s.parte_cod \|\| "—"} · ${s.hora \|\| ""} · ` +` → ``parte ${s.parte_cod \|\| "—"} · · ` +` | MUERTO | 1 | test_f054_r33_el_texto_de_cada_sobrante_en_su_seccion |

**Total: 69 mutantes, 69 muertos, 0 supervivientes.** Coste: 806.5 s
y 102.5 s de reloj.

## Campaña 3 (`97e5fed`, review 1, O5): 14 mutantes, 12 muertos, 1 vivo, 1 dudoso

Las líneas de `app.js` que cambia O5: `api()` deja `status` en el error,
`traerDeSigrid` calla el 404/409 al comparar y el aviso de registrar da el
motivo de las omitidas y sale en rojo. Mismo script con la lista de abajo y
`test_f024_selector.py` añadido a los tests. Línea base `71 passed`.

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| C1 api sin el código en el error | `app.js:275` | `throw Object.assign(new Error(mensaje), { status: respuesta.status });` → `throw new Error(mensaje);` | MUERTO | 1 | test_f054_o5_api_deja_el_codigo_http_en_el_erro
| C2 se calla también al aceptar | `app.js:2854` | `if (!aceptar.length && [404, 409].includes(err.status)) return;` → `if ([404, 409].includes(err.status)) return;` | MUERTO | 1 | test_f054_o5_aceptar_si_avisa_del_er
| C3 se calla ante cualquier error al comparar | `app.js:2854` | `if (!aceptar.length && [404, 409].includes(err.status)) return;` → `if (!aceptar.length) return;` | MUERTO | 1 | test_f054_o5_comparar_con_otro_error_si
| C4 el 404 sí avisa | `app.js:2854` | `if (!aceptar.length && [404, 409].includes(err.status)) return;` → `if (!aceptar.length && [409].includes(err.status)) return;` | MUERTO | 1 | test_f054_o5_comparar_en_mes_cerra
| C5 el 409 sí avisa | `app.js:2854` | `if (!aceptar.length && [404, 409].includes(err.status)) return;` → `if (!aceptar.length && [404].includes(err.status)) return;` | MUERTO | 1 | test_f054_o5_comparar_en_mes_cerra
| C6 condición negada | `app.js:2854` | `if (!aceptar.length && [404, 409].includes(err.status)) return;` → `if (aceptar.length && [404, 409].includes(err.status)) return;` | MUERTO | 2 | test_f054_o5_aceptar_si_avisa
| C7 sin sobrantes_a_cero revienta | `app.js:3674` | `const ceroOmitidas = r.sobrantes_a_cero ? r.sobrantes_a_cero.omitidas : [];` → `const ceroOmitidas = r.sobrantes_a_cero.omitidas;` | SUPERVIVIENTE | 0 | — |
| C8 sin omitidas siempre | `app.js:3674` | `const ceroOmitidas = r.sobrantes_a_cero ? r.sobrantes_a_cero.omitidas : [];` → `const ceroOmitidas = [];` | MUERTO | 2 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_
| C9 sin los motivos | `app.js:3683` | `ceroOmitidas.map((x) => x.motivo).join("; ") : "")` → `"" : "")` | MUERTO | 2 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar, test_f054_r35_o5_sin_omitidas_es_exi
| C10 motivos sin separar | `app.js:3683` | `ceroOmitidas.map((x) => x.motivo).join("; ") : "")` → `ceroOmitidas.map((x) => x.motivo).join("") : "")` | MUERTO | 1 | test_f054_r35_o5_sin_omitidas_es_exito_y_los_motivos_
| C11 con omitidas sale como éxito | `app.js:3685` | `!r.ok \|\| ceroOmitidas.length > 0);` → `!r.ok);` | MUERTO | 2 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar, test_f054_r35_o5_sin_omitidas_es_exi
| C12 siempre como error | `app.js:3685` | `!r.ok \|\| ceroOmitidas.length > 0);` → `true);` | MUERTO | 1 | test_f054_r35_o5_sin_omitidas_es_exito_y_los_motivos_se_unen |
| C13 un fallo de registro no es error (&&) | `app.js:3685` | `!r.ok \|\| ceroOmitidas.length > 0);` → `!r.ok && ceroOmitidas.length > 0);` | MUERTO | 2 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar, t
| C14 el borde de omitidas (> 1) | `app.js:3685` | `!r.ok \|\| ceroOmitidas.length > 0);` → `!r.ok \|\| ceroOmitidas.length > 1);` | MUERTO | 0 | — |

- **C7** vivo: ningún test registraba con una respuesta **sin**
  `sobrantes_a_cero` mirando el aviso (el mutante revienta y sale el
  `TypeError` en rojo). Test nuevo
  `test_f054_r35_o5_sin_sobrantes_a_cero_el_aviso_de_siempre` (`870e585`).
- **C14** salió «MUERTO» con 0 fallos: la campaña llegó al `timeout 590` de
  la orden y el proceso se cortó. No cuenta; se repite.

## Campaña 4 (`870e585`): C7 y C14, en serie, 2 muertos

Línea base `72 passed`; 103,7 s.

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| C7 sin sobrantes_a_cero revienta | `app.js:3674` | `const ceroOmitidas = r.sobrantes_a_cero ? r.sobrantes_a_cero.omitidas : [];` → `const ceroOmitidas = r.sobrantes_a_cero.omitidas;` | MUERTO | 1 | test_f054_r35_o5_sin_sobrantes_a_cero_el_aviso_de_siempre |
| C14 el borde de omitidas (> 1) | `app.js:3685` | `!r.ok \|\| ceroOmitidas.length > 0);` → `!r.ok \|\| ceroOmitidas.length > 1);` | MUERTO | 1 | test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar |

**Total de `app.js`: 69 + 14 mutantes, 0 supervivientes.**

## Reproducir

Guardar el bloque como `mutacion_manual_f054.py` **fuera del repo** y, desde
la raíz, con `e72d22c` (o un descendiente que no toque `app.js` ni esos
tests) en `HEAD`:

```bash
PYTHONIOENCODING=utf-8 services/dedicacion-front/.venv/Scripts/python.exe <ruta>/mutacion_manual_f054.py
```

La campaña 2 es la misma con `M` filtrada a los nueve de arriba.

```python
# mutacion_manual_f054.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-054 sobre `app.js` (T9 y T15).

Se ejecuta desde la raíz del repositorio. Extrae `HEAD` con `git archive`
a un directorio temporal (el árbol de trabajo no se toca) y, por cada
mutante, reescribe en esa copia `app.js` con la sustitución (el original
tiene que aparecer UNA sola vez; si no, aborta), comprueba la sintaxis con
`node --check`, pasa los tests del front que cargan esas funciones sin `-x`
y anota los que caen. En serie (1 worker). Al final restaura el original y
borra la copia.
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

FRONT = Path("services/dedicacion-front")
PYTHON = str((FRONT / ".venv" / "Scripts" / "python.exe").resolve())
TESTS = ["tests/test_f054_traer_front.py",
         "tests/test_f054_modal_cero.py",
         "tests/test_f050_modal_registro.py",
         "tests/test_f064_pisado_vinculados.py",
         "tests/test_f050_t15e_sombreado.py"]
JS = "static/js/app.js"

M = [
    # ---- T9: traer de Sigrid al sincronizar (R1, R28) ----
    ("A1", "sincronizar con éxito devuelve false",
     "return true;    // F-054 (R1)", "return false;    // F-054 (R1)"),
    ("A2", "sincronizar fallido devuelve true",
     "    toast(err.message, true);\n    return false;\n  } finally {\n    boton.disabled = false;\n    boton.textContent = \"Sincronizar Sigrid\";",
     "    toast(err.message, true);\n    return true;\n  } finally {\n    boton.disabled = false;\n    boton.textContent = \"Sincronizar Sigrid\";"),
    ("A3", "compara aunque el sync falle",
     "if (await sincronizar()) await traerDeSigrid([]);",
     "await sincronizar(); await traerDeSigrid([]);"),
    ("A4", "no manda `aceptar`",
     "body: JSON.stringify({ aceptar }),", "body: JSON.stringify({}),"),
    ("A5", "condición de comparar invertida",
     "if (!aceptar.length) { abrirTraerSigrid(datos); return; }",
     "if (aceptar.length) { abrirTraerSigrid(datos); return; }"),
    ("A6", "no cierra el modal al aceptar",
     "  cerrarModal();\n  const rechazadas", "  const rechazadas"),
    ("A7", "el toast de rechazadas nunca es error",
     ": \"\"), rechazadas.length > 0);", ": \"\"), false);"),
    ("A8", "sin el motivo de las rechazadas",
     "rechazadas.map((r) => r.motivo).join(\"; \")", "\"\""),
    ("A9", "no marca las propuestas en curso",
     "  marcarPropuestas(datos.propuestas_en_curso);    // F-055 (R26)\n  await cargarPeriodo(state.anio, state.mes);\n}\n\nfunction textoEstadoSigrid",
     "  await cargarPeriodo(state.anio, state.mes);\n}\n\nfunction textoEstadoSigrid"),
    ("A10", "no recarga el periodo tras aceptar",
     "  await cargarPeriodo(state.anio, state.mes);\n}\n\nfunction textoEstadoSigrid",
     "}\n\nfunction textoEstadoSigrid"),
    ("A11", "rótulo de solo_sigrid crudo",
     "solo_sigrid: \"solo en Sigrid\",", "solo_sigrid: \"solo_sigrid\","),
    ("A12", "rótulo de no_traducible crudo",
     "no_traducible: \"no se puede traer\",", "no_traducible: \"no_traducible\","),
    ("A13", "casilla solo si las dos (&&)",
     "const conCasilla = e.estado === \"distinta\" || e.estado === \"solo_sigrid\";",
     "const conCasilla = e.estado === \"distinta\" && e.estado === \"solo_sigrid\";"),
    ("A14", "casilla también en igual",
     "const conCasilla = e.estado === \"distinta\" || e.estado === \"solo_sigrid\";",
     "const conCasilla = e.estado !== \"no_traducible\";"),
    ("A15", "todas marcadas por defecto",
     "${e.estado === \"solo_sigrid\" ? \" checked\" : \"\"}>`",
     "${\" checked\"}>`"),
    ("A16", "ninguna marcada por defecto",
     "${e.estado === \"solo_sigrid\" ? \" checked\" : \"\"}>`",
     "${\"\"}>`"),
    ("A17", "data-postventa invertido",
     "data-postventa=\"${e.es_postventa ? 1 : 0}\"",
     "data-postventa=\"${e.es_postventa ? 0 : 1}\""),
    ("A18", "pct de undefined no es —",
     "(v === null || v === undefined ? \"—\" : fmtPct(v))",
     "(v === null ? \"—\" : fmtPct(v))"),
    ("A19", "pct de null no es —",
     "(v === null || v === undefined ? \"—\" : fmtPct(v))",
     "(v === undefined ? \"—\" : fmtPct(v))"),
    ("A20", "sin «(postventa)» en la obra",
     "${e.es_postventa ? \" (postventa)\" : \"\"}`;", "`;"),
    ("A21", "sin el parte en el detalle",
     "e.parte_cod ? `parte ${e.parte_cod}` : \"\",", "\"\","),
    ("A22", "sin la partida en el detalle",
     "e.partida_cod ? `partida ${e.partida_cod}` : \"\", e.motivo || \"\"]",
     "\"\", e.motivo || \"\"]"),
    ("A23", "sin el motivo en el detalle",
     ": \"\", e.motivo || \"\"]", ": \"\", \"\"]"),
    ("A24", "sin la columna del cuadrante",
     "`<td>${pct(e.pct_cuadrante)}</td><td>${pct(e.pct_sigrid)}</td>`",
     "`<td></td><td>${pct(e.pct_sigrid)}</td>`"),
    ("A25", "sin la columna de Sigrid",
     "`<td>${pct(e.pct_cuadrante)}</td><td>${pct(e.pct_sigrid)}</td>`",
     "`<td>${pct(e.pct_cuadrante)}</td><td></td>`"),
    ("A26", "resumen sin líneas leídas",
     "`${datos.lineas_leidas} líneas leídas en los partes`,", ""),
    ("A27", "resumen sin las de pruebas",
     "`${datos.excluidas_pruebas} de la obra de pruebas`,", ""),
    ("A28", "resumen sin vinculados",
     "`${datos.de_vinculados} de recursos vinculados`,", ""),
    ("A29", "resumen sin fuera del maestro",
     "`${datos.fuera_maestro} de recursos fuera del maestro`,", ""),
    ("A30", "sin el aviso de postventa",
     "[datos.motivo_postventa, datos.motivo_var].filter(Boolean)",
     "[datos.motivo_var].filter(Boolean)"),
    ("A31", "sin el aviso de VAR",
     "[datos.motivo_postventa, datos.motivo_var].filter(Boolean)",
     "[datos.motivo_postventa].filter(Boolean)"),
    ("A32", "texto de vacío invertido",
     "  if (!trabajadores.length) {\n    html += \"<p>Ningún",
     "  if (trabajadores.length) {\n    html += \"<p>Ningún"),
    ("A33", "sin cabecera del trabajador",
     "html += `<h3>${escapeHtml(`${t.cod} · ${t.nombre}`)}</h3>` +",
     "html += `<h3></h3>` +"),
    ("A34", "no cuenta las casillas",
     "e.estado === \"solo_sigrid\") casillas += 1;",
     "e.estado === \"solo_sigrid\") casillas += 0;"),
    ("A35", "botón de aceptar siempre",
     "(casillas ? `<button class=\"btn primary\" id=\"btn-traer-aceptar\">",
     "(true ? `<button class=\"btn primary\" id=\"btn-traer-aceptar\">"),
    ("A36", "sin la lista de no traídas",
     "  if (noTraidas.length) {", "  if (false) {"),
    ("A37", "no traídas sin su motivo",
     "`${n.recurso_ide}: ${n.motivo}`)}</li>`)", "`${n.recurso_ide}`)}</li>`)"),
    ("A38", "aceptadas sin filtrar por marcadas",
     "#modal-registro .chk-traer:checked", "#modal-registro .chk-traer"),
    ("A39", "trabajador_ide sin Number",
     "trabajador_ide: Number(c.dataset.trabajador),",
     "trabajador_ide: c.dataset.trabajador,"),
    ("A40", "obra_ide sin Number",
     "obra_ide: Number(c.dataset.obra),", "obra_ide: c.dataset.obra,"),
    ("A41", "es_postventa invertido",
     "es_postventa: c.dataset.postventa === \"1\",",
     "es_postventa: c.dataset.postventa === \"0\","),
    ("A42", "aceptar sin marcadas no avisa",
     "      if (!marcadas.length) {", "      if (false) {"),
    ("A43", "el botón de sync sin traer",
     "$(\"#btn-sync\").addEventListener(\"click\", () => sincronizarYTraer());",
     "$(\"#btn-sync\").addEventListener(\"click\", () => sincronizar());"),
    ("A44", "un error de comparar no avisa",
     "toast(`No se pudo comparar con Sigrid: ${err.message}`, true);",
     ""),
    # ---- T15: sobrantes en el modal de registro (R33-R35, D17) ----
    ("B1", "un preflight nuevo no desmarca",
     "    registro.cero = new Set();      // F-054 (D17): las sobrantes, desmarcadas\n",
     ""),
    ("B2", "el repreflight pierde lo marcado",
     "registro.cero = new Set([...document.querySelectorAll(\".chk-cero:checked\")]\n      .map((c) => c.value));",
     "registro.cero = new Set();"),
    ("B3", "sin la sección de sobrantes",
     "  if ((pf.sobrantes || []).length) html += pintarSobrantes(pf);\n", ""),
    ("B4", "la sección también con lista vacía",
     "  if ((pf.sobrantes || []).length) html += pintarSobrantes(pf);\n",
     "  if (pf.sobrantes) html += pintarSobrantes(pf);\n"),
    ("B5", "sin el título de la sección",
     "\"<h3>En Sigrid, en obras que no tiene en la plataforma</h3>\" +", "\"\" +"),
    ("B6", "el vinculado sin tipo",
     "`${s.vinculado.tipo || \"\"} ${s.vinculado.cod || \"\"} de ` +",
     "` ${s.vinculado.cod || \"\"} de ` +"),
    ("B7", "el vinculado sin código",
     "`${s.vinculado.tipo || \"\"} ${s.vinculado.cod || \"\"} de ` +",
     "`${s.vinculado.tipo || \"\"}  de ` +"),
    ("B8", "el vinculado con su propio nombre",
     "nombreTrabajador(s.vinculado.titular_ide)", "nombreTrabajador(s.recurso_ide)"),
    ("B9", "el vinculado como trabajador",
     "    const quien = s.vinculado\n", "    const quien = false\n"),
    ("B10", "obra por su ide",
     "obra ${s.obra_cod || s.obra_ide}", "obra ${s.obra_ide}"),
    ("B11", "sin el parte",
     "`parte ${s.parte_cod || \"—\"} · ${s.hora || \"\"} · ` +",
     "`parte — · ${s.hora || \"\"} · ` +"),
    ("B12", "sin la hora",
     "`parte ${s.parte_cod || \"—\"} · ${s.hora || \"\"} · ` +",
     "`parte ${s.parte_cod || \"—\"} ·  · ` +"),
    ("B13", "sin la partida",
     "`${s.partida_cod || \"sin partida\"} · ${fmtPct((s.can || 0) * 100)}`;",
     "`sin partida · ${fmtPct((s.can || 0) * 100)}`;"),
    ("B14", "el % sin ×100",
     "${fmtPct((s.can || 0) * 100)}`;", "${fmtPct((s.can || 0))}`;"),
    ("B15", "todas confirmables",
     "    if (s.confirmable) {", "    if (true) {"),
    ("B16", "ninguna confirmable",
     "    if (s.confirmable) {", "    if (false) {"),
    ("B17", "nunca marcadas al repintar",
     "${registro.cero.has(s.clave) ? \" checked\" : \"\"}> ` +",
     "${\"\"}> ` +"),
    ("B18", "siempre marcadas (contra D17)",
     "${registro.cero.has(s.clave) ? \" checked\" : \"\"}> ` +",
     "${\" checked\"}> ` +"),
    ("B19", "el aviso sin su motivo",
     "`${escapeHtml(s.motivo || \"\")}</div>`;", "`</div>`;"),
    ("B20", "manda todas las sobrantes",
     ".filter((x) => ceros.has(x.clave));", ".filter(() => true);"),
    ("B21", "lee las marcadas de pisar",
     "  const ceros = new Set([...document.querySelectorAll(\".chk-cero:checked\")]",
     "  const ceros = new Set([...document.querySelectorAll(\".chk-pisar:checked\")]"),
    ("B22", "sobrantes_a_cero siempre",
     "...(sobrantes.length ? { sobrantes_a_cero: sobrantes } : {})",
     "...({ sobrantes_a_cero: sobrantes })"),
    ("B23", "sobrantes_a_cero nunca",
     "...(sobrantes.length ? { sobrantes_a_cero: sobrantes } : {})",
     "...({})"),
    ("B24", "toast sin las puestas a 0",
     "? ` · ${r.sobrantes_a_cero.puestas.length} puestas a 0` +",
     "? `` +"),
    ("B25", "toast sin las omitidas",
     "(r.sobrantes_a_cero.omitidas.length\n", "(false\n"),
]


def esc(s: str) -> str:
    return " ".join(s.split()).replace("|", "\\|") or "(nada)"


def correr(front: Path, js: str) -> tuple[str, list[str], str]:
    (front / JS).write_bytes(js.encode("utf-8"))
    chk = subprocess.run(["node", "--check", JS], cwd=front,
                         capture_output=True, text=True, check=False)
    if chk.returncode != 0:
        return "SINTAXIS", [], chk.stderr.strip().splitlines()[-1:]
    r = subprocess.run([PYTHON, "-m", "pytest", *TESTS, "-q", "-rA",
                        "--tb=no", "-p", "no:cacheprovider"], cwd=front,
                       capture_output=True, text=True, encoding="utf-8",
                       check=False)
    caidos = sorted(set(re.findall(
        r"^(?:FAILED|ERROR) tests/(test_\w+)\.py::(\w+)", r.stdout,
        re.MULTILINE)))
    resumen = (r.stdout.strip().splitlines() or [""])[-1]
    return ("MUERTO" if r.returncode else "SUPERVIVIENTE"), \
        [t for _, t in caidos], resumen


def main() -> None:
    t0 = time.monotonic()
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True, check=True).stdout.strip()
    tar = subprocess.run(["git", "archive", "HEAD"], capture_output=True,
                         check=True).stdout
    with tempfile.TemporaryDirectory(prefix="mm_f054_") as tmp:
        raiz = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(tar)) as t:
            t.extractall(raiz)
        front = raiz / FRONT
        original = (front / JS).read_bytes().decode("utf-8")
        print(f"SHA: {sha}")
        estado, _, resumen = correr(front, original)
        print(f"Línea base: {estado} · {resumen}", flush=True)
        if estado != "SUPERVIVIENTE":
            sys.exit("la línea base no está en verde: la campaña no vale")
        vivos = 0
        for ide, desc, antes, despues in M:
            n = original.count(antes)
            if n != 1:
                sys.exit(f"{ide}: el original aparece {n} veces, tiene que ser 1")
            linea = original[:original.index(antes)].count("\n") + 1
            estado, caidos, resumen = correr(
                front, original.replace(antes, despues))
            vivos += estado == "SUPERVIVIENTE"
            print(f"| {ide} {desc} | `app.js:{linea}` | `{esc(antes)}` → "
                  f"`{esc(despues)}` | {estado} | {len(caidos)} | "
                  f"{', '.join(caidos) or '—'} |", flush=True)
        (front / JS).write_bytes(original.encode("utf-8"))
        print(f"Mutantes: {len(M)} · supervivientes: {vivos}")
    print(f"Tiempo: {time.monotonic() - t0:.1f} s")


if __name__ == "__main__":
    main()
```

Campañas 3 y 4 (importa el script de arriba como `mutacion_manual_f054`):

```python
# mutacion_manual_f054_c3.py (fuera del repo, a propósito)
"""Mini-campaña de F-054 (O5): las líneas de `app.js` que cambian tras la
review 1. Mismo mecanismo que `mutacion_manual_f054.py`: reutiliza su
`correr`, `esc` y `main` con otra lista `M` y sus tests."""
import mutacion_manual_f054 as base

base.TESTS.append("tests/test_f024_selector.py")
base.M[:] = [
    ("C1", "api sin el código en el error",
     "throw Object.assign(new Error(mensaje), { status: respuesta.status });",
     "throw new Error(mensaje);"),
    ("C2", "se calla también al aceptar",
     "if (!aceptar.length && [404, 409].includes(err.status)) return;",
     "if ([404, 409].includes(err.status)) return;"),
    ("C3", "se calla ante cualquier error al comparar",
     "if (!aceptar.length && [404, 409].includes(err.status)) return;",
     "if (!aceptar.length) return;"),
    ("C4", "el 404 sí avisa",
     "if (!aceptar.length && [404, 409].includes(err.status)) return;",
     "if (!aceptar.length && [409].includes(err.status)) return;"),
    ("C5", "el 409 sí avisa",
     "if (!aceptar.length && [404, 409].includes(err.status)) return;",
     "if (!aceptar.length && [404].includes(err.status)) return;"),
    ("C6", "condición negada",
     "if (!aceptar.length && [404, 409].includes(err.status)) return;",
     "if (aceptar.length && [404, 409].includes(err.status)) return;"),
    ("C7", "sin sobrantes_a_cero revienta",
     "const ceroOmitidas = r.sobrantes_a_cero ? r.sobrantes_a_cero.omitidas : [];",
     "const ceroOmitidas = r.sobrantes_a_cero.omitidas;"),
    ("C8", "sin omitidas siempre",
     "const ceroOmitidas = r.sobrantes_a_cero ? r.sobrantes_a_cero.omitidas : [];",
     "const ceroOmitidas = [];"),
    ("C9", "sin los motivos",
     'ceroOmitidas.map((x) => x.motivo).join("; ") : "")',
     '"" : "")'),
    ("C10", "motivos sin separar",
     'ceroOmitidas.map((x) => x.motivo).join("; ") : "")',
     'ceroOmitidas.map((x) => x.motivo).join("") : "")'),
    ("C11", "con omitidas sale como éxito",
     "!r.ok || ceroOmitidas.length > 0);", "!r.ok);"),
    ("C12", "siempre como error",
     "!r.ok || ceroOmitidas.length > 0);", "true);"),
    ("C13", "un fallo de registro no es error (&&)",
     "!r.ok || ceroOmitidas.length > 0);",
     "!r.ok && ceroOmitidas.length > 0);"),
    ("C14", "el borde de omitidas (> 1)",
     "!r.ok || ceroOmitidas.length > 0);",
     "!r.ok || ceroOmitidas.length > 1);"),
]

if __name__ == "__main__":
    base.main()
```

## Campaña 5 (`488d423`, T23): 81 mutantes, 78 muertos, 3 supervivientes

Las funciones nuevas o reescritas de la ventana de «Sincronizar Sigrid»
(T23, R28 y R39-R42): `modeloTraerSigrid`, `filasTraerVisibles`,
`textoAceptarTraer`, `textoBotonTraer`, `filaEntradaSigrid`,
`cuerpoTraerSigrid`, `titulosTraerSigrid`, `pintarTraerSigrid`,
`aceptadasMarcadas` y `abrirTraerSigrid`. Mismo script (tests y mecanismo
de arriba) con la lista `M` de `mutacion_manual_f054_c5.py`, abajo.

Línea base (sin mutar, en verde): 81 passed in 20.60s · Tiempo: 1613.0 s

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| D1 sale marcada (D12 antigua) | `app.js:2885` | `t, e, i: filas.length, marcada: false,` → `t, e, i: filas.length, marcada: true,` | MUERTO | 8 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D2 casilla solo si las dos (&&) | `app.js:2886` | `casilla: e.estado === "distinta" \|\| e.estado === "solo_sigrid",` → `casilla: e.estado === "distinta" && e.estado === "solo_sigrid",` | MUERTO | 10 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_sin_pulsar_no_se_manda_nada, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D3 casilla también en igual y solo_cuadrante | `app.js:2886` | `casilla: e.estado === "distinta" \|\| e.estado === "solo_sigrid",` → `casilla: e.estado !== "no_traducible",` | MUERTO | 5 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D4 trabajador sin código | `app.js:2888` | `trabajador: `${t.cod} · ${t.nombre}`,` → `trabajador: `${t.nombre}`,` | MUERTO | 11 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D5 obra sin «(postventa)» | `app.js:2889` | `obra: `${e.cod} ${e.descripcion}${e.es_postventa ? " (postventa)" : ""}`,` → `obra: `${e.cod} ${e.descripcion}`,` | MUERTO | 8 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D6 estado con el código crudo | `app.js:2890` | `estado: textoEstadoSigrid(e.estado),` → `estado: e.estado,` | MUERTO | 10 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D7 detalle sin el parte | `app.js:2891` | `detalle: [e.parte_cod ? `parte ${e.parte_cod}` : "",` → `detalle: ["",` | MUERTO | 3 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D8 detalle sin la partida | `app.js:2892` | `e.partida_cod ? `partida ${e.partida_cod}` : "", e.motivo \|\| ""]` → `"", e.motivo \|\| ""]` | MUERTO | 3 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D9 detalle sin el motivo | `app.js:2892` | `: "", e.motivo \|\| ""]` → `: "", ""]` | MUERTO | 5 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D10 orden inicial descendente | `app.js:2897` | `orden: { col: null, asc: true },` → `orden: { col: null, asc: false },` | SUPERVIVIENTE | 0 | — |
| D11 filtro inicial no vacío | `app.js:2898` | `filtros: { trabajador: "", obra: "", estado: "", detalle: "" } };` → `filtros: { trabajador: "", obra: "x", estado: "", detalle: "" } };` | SUPERVIVIENTE | 0 | — |
| D12 texto pintado con mayúsculas | `app.js:2907` | `texto.toLowerCase().includes(filtro.toLowerCase());` → `texto.includes(filtro.toLowerCase());` | MUERTO | 3 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D13 filtro con mayúsculas | `app.js:2907` | `texto.toLowerCase().includes(filtro.toLowerCase());` → `texto.toLowerCase().includes(filtro);` | MUERTO | 1 | test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D14 sin filtro de trabajador | `app.js:2909` | `contiene(f.textos.trabajador, filtros.trabajador) &&` → `true &&` | MUERTO | 3 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D15 sin filtro de obra | `app.js:2910` | `contiene(f.textos.obra, filtros.obra) &&` → `true &&` | MUERTO | 5 | test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas |
| D16 sin filtro de detalle | `app.js:2911` | `contiene(f.textos.detalle, filtros.detalle) &&` → `true &&` | MUERTO | 1 | test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D17 sin filtro de estado | `app.js:2912` | `(!filtros.estado \|\| f.e.estado === filtros.estado));` → `true);` | MUERTO | 1 | test_f054_r41_desplegable_de_estado_y_filtros_combinados |
| D18 estado sin «Todos» | `app.js:2912` | `(!filtros.estado \|\| f.e.estado === filtros.estado));` → `(f.e.estado === filtros.estado));` | MUERTO | 12 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D19 filtros con || (no se combinan) | `app.js:2909` | `contiene(f.textos.trabajador, filtros.trabajador) &&` → `contiene(f.textos.trabajador, filtros.trabajador) \|\|` | MUERTO | 7 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D20 nunca ordena | `app.js:2913` | `if (!orden.col) return visibles;` → `return visibles;` | MUERTO | 6 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D21 Sigrid no es numérica | `app.js:2914` | `const numerica = orden.col === "cuadrante" \|\| orden.col === "sigrid";` → `const numerica = orden.col === "cuadrante";` | MUERTO | 4 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D22 Cuadrante no es numérica | `app.js:2914` | `const numerica = orden.col === "cuadrante" \|\| orden.col === "sigrid";` → `const numerica = orden.col === "sigrid";` | MUERTO | 1 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final |
| D23 raya solo si null | `app.js:2916` | `const raya = (v) => v === null \|\| v === undefined;` → `const raya = (v) => v === null;` | MUERTO | 1 | test_f054_r40_la_raya_tambien_si_falta_el_porcentaje |
| D24 raya solo si undefined | `app.js:2916` | `const raya = (v) => v === null \|\| v === undefined;` → `const raya = (v) => v === undefined;` | MUERTO | 3 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D25 raya al principio | `app.js:2920` | `if (raya(va) \|\| raya(vb)) return raya(va) - raya(vb);` → `if (raya(va) \|\| raya(vb)) return raya(vb) - raya(va);` | MUERTO | 4 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D26 la raya sigue al sentido | `app.js:2920` | `if (raya(va) \|\| raya(vb)) return raya(va) - raya(vb);` → `if (raya(va) \|\| raya(vb)) return (raya(va) - raya(vb)) * (orden.asc ? 1 : -1);` | MUERTO | 2 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje |
| D27 sin la rama de la raya | `app.js:2920` | `if (raya(va) \|\| raya(vb)) return raya(va) - raya(vb);` → `(nada)` | MUERTO | 4 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D28 texto distinguiendo mayúsculas | `app.js:2922` | `: va.toLowerCase().localeCompare(vb.toLowerCase(), "es");` → `: va.localeCompare(vb, "es");` | MUERTO | 1 | test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable |
| D29 numérico al revés | `app.js:2921` | `const c = numerica ? va - vb` → `const c = numerica ? vb - va` | MUERTO | 4 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D30 no invierte | `app.js:2923` | `return orden.asc ? c : -c;` → `return c;` | MUERTO | 4 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable |
| D31 siempre invierte | `app.js:2923` | `return orden.asc ? c : -c;` → `return -c;` | MUERTO | 6 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D32 ocultas también con 0 | `app.js:2930` | `(ocultas > 0 ?` → `(ocultas >= 0 ?` | MUERTO | 7 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla, test_f054_r42_texto_del_boton_de_aceptar |
| D33 nunca dice las ocultas | `app.js:2930` | `(ocultas > 0 ?` → `(false ?` | MUERTO | 3 | test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_texto_del_boton_de_aceptar |
| D34 sin el número | `app.js:2929` | `return `Aceptar ${n} marcadas` +` → `return `Aceptar marcadas` +` | MUERTO | 7 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla, test_f054_r42_texto_del_boton_de_aceptar |
| D35 cuenta las casillas, no las marcadas | `app.js:2934` | `const marcadas = modelo.filas.filter((f) => f.marcada);` → `const marcadas = modelo.filas.filter((f) => f.casilla);` | MUERTO | 6 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D36 ocultas = todas las marcadas | `app.js:2936` | `marcadas.filter((f) => !visibles.includes(f)).length);` → `marcadas.length);` | MUERTO | 4 | test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D37 ocultas = las visibles | `app.js:2936` | `marcadas.filter((f) => !visibles.includes(f)).length);` → `marcadas.filter((f) => visibles.includes(f)).length);` | MUERTO | 3 | test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D38 la casilla no refleja marcada | `app.js:2944` | ``${f.marcada ? " checked" : ""}>`` → ``${""}>`` | MUERTO | 2 | test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D39 casilla siempre marcada | `app.js:2944` | ``${f.marcada ? " checked" : ""}>`` → ``${" checked"}>`` | MUERTO | 4 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D40 data-fila fijo | `app.js:2943` | `data-fila="${f.i}"` → `data-fila="0"` | MUERTO | 3 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D41 casilla en todas las filas | `app.js:2942` | `const casilla = f.casilla` → `const casilla = true` | MUERTO | 4 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas |
| D42 trabajador sin escapar | `app.js:2947` | `<td>${escapeHtml(f.textos.trabajador)}</td>` → `<td>${f.textos.trabajador}</td>` | MUERTO | 8 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D43 obra sin escapar | `app.js:2948` | ``<td>${escapeHtml(f.textos.obra)}</td>`` → ``<td>${f.textos.obra}</td>`` | MUERTO | 11 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado |
| D44 detalle sin escapar | `app.js:2951` | ``<td>${escapeHtml(f.textos.detalle)}</td></tr>`` → ``<td>${f.textos.detalle}</td></tr>`` | MUERTO | 1 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos |
| D45 cuadrante y Sigrid cruzados | `app.js:2950` | ``<td>${pct(f.e.pct_cuadrante)}</td><td>${pct(f.e.pct_sigrid)}</td>` + `<td>${escapeHtml(f.textos.detalle)}` → ``<td>${pct(f.e.pct_sigrid)}</td><td>${pct(f.e.pct_cuadrante)}</td>` + `<td>${escapeHtml(f.textos.detalle)}` | MUERTO | 1 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos |
| D46 sin la fila de «ninguna» | `app.js:2955` | `return visibles.length ? visibles.map(filaEntradaSigrid).join("")` → `return true ? visibles.map(filaEntradaSigrid).join("")` | MUERTO | 1 | test_f054_r41_sin_filas_visibles_lo_dice |
| D47 ▲/▼ cruzados | `app.js:2965` | `(orden.asc ? " ▲" : " ▼")` → `(orden.asc ? " ▼" : " ▲")` | MUERTO | 1 | test_f054_r40_la_columna_ordenada_lleva_su_marca |
| D48 marca en todas las columnas | `app.js:2965` | `${col === orden.col ?` → `${true ?` | MUERTO | 2 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_la_columna_ordenada_lleva_su_marca |
| D49 sin la cabecera de la casilla | `app.js:2961` | `return "<th></th>" + [["trabajador", "Trabajador"]` → `return "" + [["trabajador", "Trabajador"]` | MUERTO | 1 | test_f054_r40_la_columna_ordenada_lleva_su_marca |
| D50 sin la columna Detalle | `app.js:2962` | `["sigrid", "Sigrid"], ["detalle", "Detalle"]]` → `["sigrid", "Sigrid"]]` | MUERTO | 1 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos |
| D51 tabla aunque no haya filas | `app.js:2984` | `if (modelo.filas.length) { // R39-R42` → `if (true) { // R39-R42` | SUPERVIVIENTE | 0 | — |
| D52 botones de marcado sin casillas | `app.js:2990` | `if (casillas) { html += `<div class="acciones-traer">`` → `if (true) { html += `<div class="acciones-traer">`` | MUERTO | 1 | test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar |
| D53 casillas = todas (every) | `app.js:2983` | `const casillas = modelo.filas.some((f) => f.casilla);` → `const casillas = modelo.filas.every((f) => f.casilla);` | MUERTO | 11 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_sin_pulsar_no_se_manda_nada, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D54 opción de estado con el código | `app.js:2999` | ``<option value="${s}">${escapeHtml(textoEstadoSigrid(s))}</option>`` → ``<option value="${s}">${escapeHtml(s)}</option>`` | MUERTO | 1 | test_f054_r41_desplegable_de_estado_y_filtros_combinados |
| D55 sin la opción igual | `app.js:2988` | `const estados = ["distinta", "solo_sigrid", "igual", "solo_cuadrante",` → `const estados = ["distinta", "solo_sigrid", "solo_cuadrante",` | MUERTO | 1 | test_f054_r41_desplegable_de_estado_y_filtros_combinados |
| D56 rótulo inicial antiguo | `app.js:3013` | ``${textoBotonTraer(modelo, modelo.filas)}</button>`` → ``Aceptar las marcadas</button>`` | MUERTO | 1 | test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid |
| D57 sin el filtro de detalle | `app.js:3000` | ``</select></th><th></th><th></th>${texto("detalle")}</tr></thead>`` → ``</select></th><th></th><th></th><th></th></tr></thead>`` | MUERTO | 1 | test_f054_r41_desplegable_de_estado_y_filtros_combinados |
| D58 manda las de casilla, no las marcadas | `app.js:3021` | `return modelo.filas.filter((f) => f.marcada).map((f) => ({` → `return modelo.filas.filter((f) => f.casilla).map((f) => ({` | MUERTO | 4 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D59 trabajador_ide equivocado | `app.js:3022` | `trabajador_ide: f.t.trabajador_ide,` → `trabajador_ide: f.i,` | MUERTO | 2 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D60 obra_ide equivocado | `app.js:3023` | `obra_ide: f.e.obra_ide, es_postventa` → `obra_ide: f.i, es_postventa` | MUERTO | 2 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D61 es_postventa siempre false | `app.js:3024` | `es_postventa: f.e.es_postventa, }));` → `es_postventa: false, }));` | MUERTO | 2 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D62 visibles sin filtrar ni ordenar | `app.js:3036` | `filasTraerVisibles(modelo.filas, modelo.filtros, modelo.orden); const repintarBoton` → `modelo.filas; const repintarBoton` | MUERTO | 13 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D63 botón sin guarda | `app.js:3038` | `if (aceptar) aceptar.textContent` → `aceptar.textContent` | MUERTO | 1 | test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable |
| D64 repintar sin títulos | `app.js:3042` | `$("#traer-titulos").innerHTML = titulosTraerSigrid(modelo.orden);` → `(nada)` | MUERTO | 1 | test_f054_r40_la_columna_ordenada_lleva_su_marca |
| D65 repintar sin cuerpo | `app.js:3043` | `$("#traer-cuerpo").innerHTML = cuerpoTraerSigrid(v);` → `(nada)` | MUERTO | 11 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D66 repintar sin botón | `app.js:3044` | `repintarBoton(v); };` → `};` | MUERTO | 4 | test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D67 escuchas aunque no haya filas | `app.js:3046` | `if (modelo.filas.length) { $("#traer-titulos")` → `if (true) { $("#traer-titulos")` | MUERTO | 1 | test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores |
| D68 la cabecera de la casilla ordena | `app.js:3049` | `if (!col) return;` → `(nada)` | MUERTO | 1 | test_f054_r40_la_cabecera_de_la_casilla_no_ordena |
| D69 otra columna sigue el sentido | `app.js:3050` | `asc: modelo.orden.col !== col \|\| !modelo.orden.asc` → `asc: !modelo.orden.asc` | MUERTO | 7 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas |
| D70 nunca invierte (siempre asc) | `app.js:3050` | `asc: modelo.orden.col !== col \|\| !modelo.orden.asc` → `asc: true` | MUERTO | 5 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable |
| D71 el filtro no repinta | `app.js:3054` | `modelo.filtros[ev.target.dataset.filtro] = ev.target.value; repintar();` → `modelo.filtros[ev.target.dataset.filtro] = ev.target.value;` | MUERTO | 7 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas |
| D72 el filtro no se guarda | `app.js:3054` | `modelo.filtros[ev.target.dataset.filtro] = ev.target.value;` → `(nada)` | MUERTO | 7 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D73 la casilla siempre marca | `app.js:3058` | `modelo.filas[Number(ev.target.dataset.fila)].marcada = ev.target.checked;` → `modelo.filas[Number(ev.target.dataset.fila)].marcada = true;` | MUERTO | 3 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas |
| D74 la casilla no rehace el botón | `app.js:3059` | `repintarBoton(visibles());` → `(nada)` | MUERTO | 1 | test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas |
| D75 con 0 marcadas también manda | `app.js:3065` | `if (!marcadas.length) { toast("No hay ninguna entrada marcada", true);` → `if (false) { toast("No hay ninguna entrada marcada", true);` | MUERTO | 2 | test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas |
| D76 acepta mandando nada | `app.js:3069` | `return traerDeSigrid(marcadas);` → `return traerDeSigrid([]);` | MUERTO | 2 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D77 desmarcar no hace nada | `app.js:3072` | `modelo.filas.forEach((f) => { f.marcada = false; });` → `(nada)` | MUERTO | 1 | test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas |
| D78 desmarcar no repinta | `app.js:3072` | `modelo.filas.forEach((f) => { f.marcada = false; }); repintar();` → `modelo.filas.forEach((f) => { f.marcada = false; });` | MUERTO | 1 | test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas |
| D79 marcar todas, no las visibles | `app.js:3076` | `visibles().forEach((f) => { if (f.casilla) f.marcada = true; });` → `modelo.filas.forEach((f) => { if (f.casilla) f.marcada = true; });` | MUERTO | 1 | test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D80 marcar también sin casilla | `app.js:3076` | `visibles().forEach((f) => { if (f.casilla) f.marcada = true; });` → `visibles().forEach((f) => { f.marcada = true; });` | MUERTO | 1 | test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D81 marcar no repinta | `app.js:3076` | `visibles().forEach((f) => { if (f.casilla) f.marcada = true; }); repintar();` → `visibles().forEach((f) => { if (f.casilla) f.marcada = true; });` | MUERTO | 1 | test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |

**Análisis de los 3 supervivientes:**

- **D10** (`asc: true` → `false` en el orden inicial): **equivalente**. Con
  `col: null` nadie lee `asc`; el primer clic pone `asc = true` porque la
  columna cambia. Se quita el campo (`orden: { col: null }`, `2af8177`) en
  vez de pedir al humano que acepte un equivalente; el mutante que queda en
  esa línea (D10b, `col: "obra"`) muere.
- **D11** (filtro de Obra inicial `"x"`): **hueco real**. Los datos de
  prueba decían «OBRA <X>», que contiene la x. Test nuevo
  `test_f054_r41_al_abrir_ningun_filtro_esta_puesto`.
- **D51** (la tabla se pinta sin filas): **hueco real**. Ningún test miraba
  que sin entradas no hubiera tabla. Test nuevo
  `test_f054_r39_sin_entradas_no_hay_tabla`.

## Campaña 6 (`2af8177`): los vivos de la 5, 3 muertos, 0 supervivientes

Línea base (sin mutar, en verde): 83 passed in 21.09s · Tiempo: 86.8 s

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| D10b orden inicial por una columna | `app.js:2897` | `orden: { col: null },` → `orden: { col: "obra" },` | MUERTO | 5 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla |
| D11 filtro inicial no vacío | `app.js:2898` | `filtros: { trabajador: "", obra: "", estado: "", detalle: "" } };` → `filtros: { trabajador: "", obra: "x", estado: "", detalle: "" } };` | MUERTO | 1 | test_f054_r41_al_abrir_ningun_filtro_esta_puesto |
| D51 tabla aunque no haya filas | `app.js:2984` | `if (modelo.filas.length) { // R39-R42` → `if (true) { // R39-R42` | MUERTO | 1 | test_f054_r39_sin_entradas_no_hay_tabla |

**Total T23: 81 + 3 mutantes, 0 supervivientes** (D10 equivalente,
eliminado del código). Además, el `<select` acotado de
`test_f050_r29_el_front_ya_no_manda_overrides_ni_lee_catalogos` (opción «a»
del humano, 2026-11-02) se probó con 5 mutantes a mano, un
`const sel = "<select>";` al principio de `pintarModalPreflight`,
`montarSelectorPartida`, `listaSelector`, `htmlPartida` y
`textoPartidaAccion` (este último lo caza el recuento global): **5/5
muertos** (`1 failed` cada uno; base `1 passed`).

Campañas 5 y 6 (importan `mutacion_manual_f054.py` de arriba):

```python
# mutacion_manual_f054_c5.py (fuera del repo, a propósito)
"""Campaña 5 de F-054 (T23): las funciones nuevas o reescritas de la
ventana de «Sincronizar Sigrid» en `app.js`. Mismo mecanismo que
`mutacion_manual_f054.py` (copia con `git archive` de HEAD, original único,
`node --check`, tests sin `-x`, en serie): reutiliza su `correr`, `esc` y
`main` con otra lista `M`."""
import mutacion_manual_f054 as base

base.M[:] = [
    # ---- modeloTraerSigrid ----
    ("D1", "sale marcada (D12 antigua)", "t, e, i: filas.length, marcada: false,",
     "t, e, i: filas.length, marcada: true,"),
    ("D2", "casilla solo si las dos (&&)",
     'casilla: e.estado === "distinta" || e.estado === "solo_sigrid",',
     'casilla: e.estado === "distinta" && e.estado === "solo_sigrid",'),
    ("D3", "casilla también en igual y solo_cuadrante",
     'casilla: e.estado === "distinta" || e.estado === "solo_sigrid",',
     'casilla: e.estado !== "no_traducible",'),
    ("D4", "trabajador sin código", "trabajador: `${t.cod} · ${t.nombre}`,",
     "trabajador: `${t.nombre}`,"),
    ("D5", "obra sin «(postventa)»",
     'obra: `${e.cod} ${e.descripcion}${e.es_postventa ? " (postventa)" : ""}`,',
     "obra: `${e.cod} ${e.descripcion}`,"),
    ("D6", "estado con el código crudo", "estado: textoEstadoSigrid(e.estado),",
     "estado: e.estado,"),
    ("D7", "detalle sin el parte",
     'detalle: [e.parte_cod ? `parte ${e.parte_cod}` : "",', 'detalle: ["",'),
    ("D8", "detalle sin la partida",
     'e.partida_cod ? `partida ${e.partida_cod}` : "", e.motivo || ""]',
     '"", e.motivo || ""]'),
    ("D9", "detalle sin el motivo", ': "", e.motivo || ""]', ': "", ""]'),
    ("D10", "orden inicial descendente", "orden: { col: null, asc: true },",
     "orden: { col: null, asc: false },"),
    ("D11", "filtro inicial no vacío",
     'filtros: { trabajador: "", obra: "", estado: "", detalle: "" } };',
     'filtros: { trabajador: "", obra: "x", estado: "", detalle: "" } };'),
    # ---- filasTraerVisibles ----
    ("D12", "texto pintado con mayúsculas",
     "texto.toLowerCase().includes(filtro.toLowerCase());",
     "texto.includes(filtro.toLowerCase());"),
    ("D13", "filtro con mayúsculas",
     "texto.toLowerCase().includes(filtro.toLowerCase());",
     "texto.toLowerCase().includes(filtro);"),
    ("D14", "sin filtro de trabajador",
     "contiene(f.textos.trabajador, filtros.trabajador) &&", "true &&"),
    ("D15", "sin filtro de obra", "contiene(f.textos.obra, filtros.obra) &&",
     "true &&"),
    ("D16", "sin filtro de detalle",
     "contiene(f.textos.detalle, filtros.detalle) &&", "true &&"),
    ("D17", "sin filtro de estado",
     "(!filtros.estado || f.e.estado === filtros.estado));", "true);"),
    ("D18", "estado sin «Todos»",
     "(!filtros.estado || f.e.estado === filtros.estado));",
     "(f.e.estado === filtros.estado));"),
    ("D19", "filtros con || (no se combinan)",
     "contiene(f.textos.trabajador, filtros.trabajador) &&",
     "contiene(f.textos.trabajador, filtros.trabajador) ||"),
    ("D20", "nunca ordena", "if (!orden.col) return visibles;",
     "return visibles;"),
    ("D21", "Sigrid no es numérica",
     'const numerica = orden.col === "cuadrante" || orden.col === "sigrid";',
     'const numerica = orden.col === "cuadrante";'),
    ("D22", "Cuadrante no es numérica",
     'const numerica = orden.col === "cuadrante" || orden.col === "sigrid";',
     'const numerica = orden.col === "sigrid";'),
    ("D23", "raya solo si null",
     "const raya = (v) => v === null || v === undefined;",
     "const raya = (v) => v === null;"),
    ("D24", "raya solo si undefined",
     "const raya = (v) => v === null || v === undefined;",
     "const raya = (v) => v === undefined;"),
    ("D25", "raya al principio",
     "if (raya(va) || raya(vb)) return raya(va) - raya(vb);",
     "if (raya(va) || raya(vb)) return raya(vb) - raya(va);"),
    ("D26", "la raya sigue al sentido",
     "if (raya(va) || raya(vb)) return raya(va) - raya(vb);",
     "if (raya(va) || raya(vb)) return (raya(va) - raya(vb)) * (orden.asc ? 1 : -1);"),
    ("D27", "sin la rama de la raya",
     "if (raya(va) || raya(vb)) return raya(va) - raya(vb);", ""),
    ("D28", "texto distinguiendo mayúsculas",
     ': va.toLowerCase().localeCompare(vb.toLowerCase(), "es");',
     ': va.localeCompare(vb, "es");'),
    ("D29", "numérico al revés", "const c = numerica ? va - vb",
     "const c = numerica ? vb - va"),
    ("D30", "no invierte", "return orden.asc ? c : -c;", "return c;"),
    ("D31", "siempre invierte", "return orden.asc ? c : -c;", "return -c;"),
    # ---- textoAceptarTraer / textoBotonTraer ----
    ("D32", "ocultas también con 0", "(ocultas > 0 ?", "(ocultas >= 0 ?"),
    ("D33", "nunca dice las ocultas", "(ocultas > 0 ?", "(false ?"),
    ("D34", "sin el número", "return `Aceptar ${n} marcadas` +",
     "return `Aceptar marcadas` +"),
    ("D35", "cuenta las casillas, no las marcadas",
     "const marcadas = modelo.filas.filter((f) => f.marcada);",
     "const marcadas = modelo.filas.filter((f) => f.casilla);"),
    ("D36", "ocultas = todas las marcadas",
     "marcadas.filter((f) => !visibles.includes(f)).length);",
     "marcadas.length);"),
    ("D37", "ocultas = las visibles",
     "marcadas.filter((f) => !visibles.includes(f)).length);",
     "marcadas.filter((f) => visibles.includes(f)).length);"),
    # ---- filaEntradaSigrid / cuerpo / títulos ----
    ("D38", "la casilla no refleja marcada", '`${f.marcada ? " checked" : ""}>`',
     '`${""}>`'),
    ("D39", "casilla siempre marcada", '`${f.marcada ? " checked" : ""}>`',
     '`${" checked"}>`'),
    ("D40", "data-fila fijo", 'data-fila="${f.i}"', 'data-fila="0"'),
    ("D41", "casilla en todas las filas", "const casilla = f.casilla\n",
     "const casilla = true\n"),
    ("D42", "trabajador sin escapar", "<td>${escapeHtml(f.textos.trabajador)}</td>",
     "<td>${f.textos.trabajador}</td>"),
    ("D43", "obra sin escapar", "`<td>${escapeHtml(f.textos.obra)}</td>`",
     "`<td>${f.textos.obra}</td>`"),
    ("D44", "detalle sin escapar", "`<td>${escapeHtml(f.textos.detalle)}</td></tr>`",
     "`<td>${f.textos.detalle}</td></tr>`"),
    ("D45", "cuadrante y Sigrid cruzados",
     "`<td>${pct(f.e.pct_cuadrante)}</td><td>${pct(f.e.pct_sigrid)}</td>` +\n    `<td>${escapeHtml(f.textos.detalle)}",
     "`<td>${pct(f.e.pct_sigrid)}</td><td>${pct(f.e.pct_cuadrante)}</td>` +\n    `<td>${escapeHtml(f.textos.detalle)}"),
    ("D46", "sin la fila de «ninguna»",
     'return visibles.length ? visibles.map(filaEntradaSigrid).join("")',
     'return true ? visibles.map(filaEntradaSigrid).join("")'),
    ("D47", "▲/▼ cruzados", '(orden.asc ? " ▲" : " ▼")', '(orden.asc ? " ▼" : " ▲")'),
    ("D48", "marca en todas las columnas", "${col === orden.col ?", "${true ?"),
    ("D49", "sin la cabecera de la casilla",
     'return "<th></th>" + [["trabajador", "Trabajador"]',
     'return "" + [["trabajador", "Trabajador"]'),
    ("D50", "sin la columna Detalle", '["sigrid", "Sigrid"],\n    ["detalle", "Detalle"]]',
     '["sigrid", "Sigrid"]]'),
    # ---- pintarTraerSigrid ----
    ("D51", "tabla aunque no haya filas", "if (modelo.filas.length) {\n    // R39-R42",
     "if (true) {\n    // R39-R42"),
    ("D52", "botones de marcado sin casillas",
     "if (casillas) {\n      html += `<div class=\"acciones-traer\">`",
     "if (true) {\n      html += `<div class=\"acciones-traer\">`"),
    ("D53", "casillas = todas (every)", "const casillas = modelo.filas.some((f) => f.casilla);",
     "const casillas = modelo.filas.every((f) => f.casilla);"),
    ("D54", "opción de estado con el código",
     "`<option value=\"${s}\">${escapeHtml(textoEstadoSigrid(s))}</option>`",
     "`<option value=\"${s}\">${escapeHtml(s)}</option>`"),
    ("D55", "sin la opción igual",
     'const estados = ["distinta", "solo_sigrid", "igual", "solo_cuadrante",',
     'const estados = ["distinta", "solo_sigrid", "solo_cuadrante",'),
    ("D56", "rótulo inicial antiguo", "`${textoBotonTraer(modelo, modelo.filas)}</button>`",
     "`Aceptar las marcadas</button>`"),
    ("D57", "sin el filtro de detalle",
     "`</select></th><th></th><th></th>${texto(\"detalle\")}</tr></thead>`",
     "`</select></th><th></th><th></th><th></th></tr></thead>`"),
    # ---- aceptadasMarcadas ----
    ("D58", "manda las de casilla, no las marcadas",
     "return modelo.filas.filter((f) => f.marcada).map((f) => ({",
     "return modelo.filas.filter((f) => f.casilla).map((f) => ({"),
    ("D59", "trabajador_ide equivocado", "trabajador_ide: f.t.trabajador_ide,",
     "trabajador_ide: f.i,"),
    ("D60", "obra_ide equivocado", "obra_ide: f.e.obra_ide,\n    es_postventa",
     "obra_ide: f.i,\n    es_postventa"),
    ("D61", "es_postventa siempre false", "es_postventa: f.e.es_postventa,\n  }));",
     "es_postventa: false,\n  }));"),
    # ---- abrirTraerSigrid ----
    ("D62", "visibles sin filtrar ni ordenar",
     "filasTraerVisibles(modelo.filas, modelo.filtros, modelo.orden);\n  const repintarBoton",
     "modelo.filas;\n  const repintarBoton"),
    ("D63", "botón sin guarda", "if (aceptar) aceptar.textContent",
     "aceptar.textContent"),
    ("D64", "repintar sin títulos",
     '$("#traer-titulos").innerHTML = titulosTraerSigrid(modelo.orden);', ""),
    ("D65", "repintar sin cuerpo", '$("#traer-cuerpo").innerHTML = cuerpoTraerSigrid(v);', ""),
    ("D66", "repintar sin botón", "    repintarBoton(v);\n  };", "  };"),
    ("D67", "escuchas aunque no haya filas",
     'if (modelo.filas.length) {\n    $("#traer-titulos")',
     'if (true) {\n    $("#traer-titulos")'),
    ("D68", "la cabecera de la casilla ordena", "      if (!col) return;\n", ""),
    ("D69", "otra columna sigue el sentido",
     "asc: modelo.orden.col !== col || !modelo.orden.asc", "asc: !modelo.orden.asc"),
    ("D70", "nunca invierte (siempre asc)",
     "asc: modelo.orden.col !== col || !modelo.orden.asc", "asc: true"),
    ("D71", "el filtro no repinta",
     "modelo.filtros[ev.target.dataset.filtro] = ev.target.value;\n      repintar();",
     "modelo.filtros[ev.target.dataset.filtro] = ev.target.value;"),
    ("D72", "el filtro no se guarda",
     "modelo.filtros[ev.target.dataset.filtro] = ev.target.value;", ""),
    ("D73", "la casilla siempre marca",
     "modelo.filas[Number(ev.target.dataset.fila)].marcada = ev.target.checked;",
     "modelo.filas[Number(ev.target.dataset.fila)].marcada = true;"),
    ("D74", "la casilla no rehace el botón", "      repintarBoton(visibles());\n", ""),
    ("D75", "con 0 marcadas también manda",
     'if (!marcadas.length) {\n        toast("No hay ninguna entrada marcada", true);',
     'if (false) {\n        toast("No hay ninguna entrada marcada", true);'),
    ("D76", "acepta mandando nada", "return traerDeSigrid(marcadas);",
     "return traerDeSigrid([]);"),
    ("D77", "desmarcar no hace nada",
     "modelo.filas.forEach((f) => { f.marcada = false; });", ""),
    ("D78", "desmarcar no repinta",
     "modelo.filas.forEach((f) => { f.marcada = false; });\n      repintar();",
     "modelo.filas.forEach((f) => { f.marcada = false; });"),
    ("D79", "marcar todas, no las visibles",
     "visibles().forEach((f) => { if (f.casilla) f.marcada = true; });",
     "modelo.filas.forEach((f) => { if (f.casilla) f.marcada = true; });"),
    ("D80", "marcar también sin casilla",
     "visibles().forEach((f) => { if (f.casilla) f.marcada = true; });",
     "visibles().forEach((f) => { f.marcada = true; });"),
    ("D81", "marcar no repinta",
     "visibles().forEach((f) => { if (f.casilla) f.marcada = true; });\n      repintar();",
     "visibles().forEach((f) => { if (f.casilla) f.marcada = true; });"),
]

if __name__ == "__main__":
    base.main()
```

```python
# mutacion_manual_f054_c6.py (fuera del repo): los vivos de la campaña 5.
import mutacion_manual_f054 as base
base.M[:] = [
    ("D10b", "orden inicial por una columna", "orden: { col: null },",
     'orden: { col: "obra" },'),
    ("D11", "filtro inicial no vacío",
     'filtros: { trabajador: "", obra: "", estado: "", detalle: "" } };',
     'filtros: { trabajador: "", obra: "x", estado: "", detalle: "" } };'),
    ("D51", "tabla aunque no haya filas", "if (modelo.filas.length) {\n    // R39-R42",
     "if (true) {\n    // R39-R42"),
]
if __name__ == "__main__":
    base.main()
```

## Campaña 7 (`0fc94fb`, T24): 90 mutantes, 85 muertos, 5 supervivientes

Las funciones nuevas o reescritas por T24 (cabecera estándar y «No se
traen» en tabla agrupada; R43-R45): `modeloTraerSigrid` (su parte
`noTraidas`), `agruparNoTraidas`, `noTraidasVisibles`, `titulosOrdenables`,
`titulosTraerSigrid`, `titulosNoTraidas`, `celdaFiltroTraer`,
`filaNoTraida`, `cuerpoNoTraidas`, `enlazarCabeceraTraer`,
`pintarTraerSigrid` y `abrirTraerSigrid`. Mismo script y mismos cinco
ficheros de test, con la lista `M` de `mutacion_manual_f054_c7.py` (fuera
del repo; sus 90 sustituciones son exactamente las de la tabla). 1 worker.

Línea base (sin mutar, en verde): 99 passed in 26.88s · Tiempo: 2821.5 s

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| E1 sin no_traidas agrupa undefined | `app.js:2898` | `filas: agruparNoTraidas(datos.no_traidas \|\| []),` → `filas: agruparNoTraidas(datos.no_traidas),` | MUERTO | 1 | test_f054_r44_sin_no_traidas_ni_la_seccion |
| E2 orden inicial de «No se traen» por Parte | `app.js:2898` | `const noTraidas = { filas: agruparNoTraidas(datos.no_traidas \|\| []), orden: { col: null },` → `const noTraidas = { filas: agruparNoTraidas(datos.no_traidas \|\| []), orden: { col: "parte" },` | MUERTO | 3 | test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E3 filtro inicial no vacío en Motivo | `app.js:2900` | `filtros: { parte: "", obra: "", recurso: "", motivo: "" } };` → `filtros: { parte: "", obra: "", recurso: "", motivo: "x" } };` | MUERTO | 3 | test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E4 filtro de Recurso sin clave | `app.js:2900` | `filtros: { parte: "", obra: "", recurso: "", motivo: "" } };` → `filtros: { parte: "", obra: "", motivo: "" } };` | SUPERVIVIENTE | 0 | — |
| E5 clave sin parte | `app.js:2912` | `const clave = JSON.stringify([n.parte_cod, n.obra_cod, n.recurso_ide,` → `const clave = JSON.stringify([n.obra_cod, n.recurso_ide,` | MUERTO | 7 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_agrupar_no_traidas, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E6 clave sin obra | `app.js:2912` | `const clave = JSON.stringify([n.parte_cod, n.obra_cod, n.recurso_ide,` → `const clave = JSON.stringify([n.parte_cod, n.recurso_ide,` | SUPERVIVIENTE | 0 | — |
| E7 clave sin recurso | `app.js:2912` | `const clave = JSON.stringify([n.parte_cod, n.obra_cod, n.recurso_ide,` → `const clave = JSON.stringify([n.parte_cod, n.obra_cod,` | MUERTO | 2 | test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E8 clave sin motivo | `app.js:2912` | `n.recurso_ide, n.motivo]);` → `n.recurso_ide, ]);` | MUERTO | 9 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_agrupar_no_traidas, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E9 clave por lo pintado del recurso | `app.js:2912` | `n.obra_cod, n.recurso_ide,` → `n.obra_cod, n.recurso_cod,` | MUERTO | 1 | test_f054_r44_el_recurso_distingue_por_su_ide |
| E10 no agrupa (cada línea, su fila) | `app.js:2915` | `if (grupo) { grupo.n += 1; return; }` → `(nada)` | MUERTO | 5 | test_f054_r44_agrupar_no_traidas, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E11 agrupa sin contar | `app.js:2915` | `if (grupo) { grupo.n += 1; return; }` → `if (grupo) { return; }` | MUERTO | 5 | test_f054_r44_agrupar_no_traidas, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E12 agrupa sin cortar (la repite) | `app.js:2915` | `if (grupo) { grupo.n += 1; return; }` → `if (grupo) { grupo.n += 1; }` | MUERTO | 5 | test_f054_r44_agrupar_no_traidas, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E13 índice siempre 0 | `app.js:2916` | `grupos.set(clave, { i: grupos.size, n: 1,` → `grupos.set(clave, { i: 0, n: 1,` | MUERTO | 1 | test_f054_r44_agrupar_no_traidas |
| E14 n inicial 0 | `app.js:2916` | `grupos.set(clave, { i: grupos.size, n: 1,` → `grupos.set(clave, { i: grupos.size, n: 0,` | MUERTO | 4 | test_f054_r44_agrupar_no_traidas, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_no_se_traen_en_una_tabla_agrupada |
| E15 parte nula sin raya | `app.js:2917` | `parte: n.parte_cod \|\| "—",` → `parte: n.parte_cod,` | MUERTO | 9 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_agrupar_no_traidas, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E16 obra nula sin raya | `app.js:2918` | `obra: n.obra_cod \|\| "—",` → `obra: n.obra_cod,` | MUERTO | 8 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_agrupar_no_traidas, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E17 recurso siempre por su ide | `app.js:2919` | `recurso: n.recurso_cod ? `${n.recurso_cod} · ${n.recurso_nombre}`` → `recurso: false ? `${n.recurso_cod} · ${n.recurso_nombre}`` | MUERTO | 4 | test_f054_r44_agrupar_no_traidas, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E18 recurso sin nombre | `app.js:2919` | `recurso: n.recurso_cod ? `${n.recurso_cod} · ${n.recurso_nombre}`` → `recurso: n.recurso_cod ? `${n.recurso_cod}`` | MUERTO | 4 | test_f054_r44_agrupar_no_traidas, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E19 recurso sin código ni ide | `app.js:2920` | `: String(n.recurso_ide), motivo: n.motivo,` → `: "", motivo: n.motivo,` | MUERTO | 4 | test_f054_r44_agrupar_no_traidas, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E20 motivo vacío | `app.js:2921` | `motivo: n.motivo, } });` → `motivo: "", } });` | MUERTO | 6 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r44_agrupar_no_traidas, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E21 filtro con mayúsculas en lo pintado | `app.js:2932` | `f.textos[k].toLowerCase().includes(filtros[k].toLowerCase())));` → `f.textos[k].includes(filtros[k].toLowerCase())));` | MUERTO | 1 | test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E22 filtro tecleado con mayúsculas | `app.js:2932` | `f.textos[k].toLowerCase().includes(filtros[k].toLowerCase())));` → `f.textos[k].toLowerCase().includes(filtros[k])));` | MUERTO | 1 | test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E23 filtros con some (no se combinan) | `app.js:2931` | `const visibles = filas.filter((f) => Object.keys(filtros).every((k) =>` → `const visibles = filas.filter((f) => Object.keys(filtros).some((k) =>` | MUERTO | 2 | test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E24 sin filtrar | `app.js:2931` | `const visibles = filas.filter((f) => Object.keys(filtros).every((k) =>` → `const visibles = filas.filter((f) => true \|\| Object.keys(filtros).every((k) =>` | MUERTO | 2 | test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E25 nunca ordena | `app.js:2933` | `if (!orden.col) return visibles; return visibles.sort((a, b) => { const c = orden.col === "lineas"` → `return visibles; return visibles.sort((a, b) => { const c = orden.col === "lineas"` | MUERTO | 2 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E26 Líneas al revés | `app.js:2935` | `const c = orden.col === "lineas" ? a.n - b.n` → `const c = orden.col === "lineas" ? b.n - a.n` | MUERTO | 1 | test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E27 Líneas como texto | `app.js:2935` | `const c = orden.col === "lineas" ? a.n - b.n` → `const c = orden.col === "lineasX" ? a.n - b.n` | MUERTO | 2 | test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E28 texto con mayúsculas al ordenar | `app.js:2936` | `: a.textos[orden.col].toLowerCase() .localeCompare(b.textos[orden.col].toLowerCase(), "es");` → `: a.textos[orden.col] .localeCompare(b.textos[orden.col], "es");` | SUPERVIVIENTE | 0 | — |
| E29 texto siempre en empate | `app.js:2936` | `: a.textos[orden.col].toLowerCase() .localeCompare(b.textos[orden.col].toLowerCase(), "es");` → `: 0;` | MUERTO | 2 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E30 la segunda pulsación no invierte | `app.js:2964` | `return orden.asc ? c : -c; }); } // Pura (R42)` → `return c; }); } // Pura (R42)` | MUERTO | 4 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable |
| E31 siempre descendente | `app.js:2964` | `return orden.asc ? c : -c; }); } // Pura (R42)` → `return -c; }); } // Pura (R42)` | MUERTO | 9 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_al_abrir_ningun_filtro_esta_puesto, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla |
| E32 ordena el modelo, no una copia | `app.js:2931` | `const visibles = filas.filter((f) => Object.keys(filtros).every((k) => f.textos[k].toLowerCase().includes(filtros[k].toLowerCase()))); if (!orden.col) return visibles;` → `filas.filter((f) => Object.keys(filtros).every((k) => f.textos[k].toLowerCase().includes(filtros[k].toLowerCase()))); const visibles = filas; if (!orden.col) return visibles;` | MUERTO | 2 | test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E33 sin th-sort | `app.js:3005` | ``<th class="th-sort" data-orden="${col}">${titulo}<span class="sort-arrow">` +` → ``<th data-orden="${col}">${titulo}<span class="sort-arrow">` +` | MUERTO | 3 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar, test_f054_r44_la_columna_ordenada_lleva_su_marca |
| E34 flecha fuera del span | `app.js:3005` | ``<th class="th-sort" data-orden="${col}">${titulo}<span class="sort-arrow">` + `${col === orden.col ? (orden.asc ? " ▲" : " ▼") : ""}</span></th>`` → ``<th class="th-sort" data-orden="${col}">${titulo}` + `${col === orden.col ? (orden.asc ? " ▲" : " ▼") : ""}<span class="sort-arrow"></span></th>`` | MUERTO | 2 | test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r44_la_columna_ordenada_lleva_su_marca |
| E35 flecha en todas | `app.js:3006` | ``${col === orden.col ? (orden.asc ? " ▲" : " ▼") : ""}</span></th>`` → ``${true ? (orden.asc ? " ▲" : " ▼") : ""}</span></th>`` | MUERTO | 3 | test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla |
| E36 flecha siempre ▲ | `app.js:3006` | ``${col === orden.col ? (orden.asc ? " ▲" : " ▼") : ""}</span></th>`` → ``${col === orden.col ? " ▲" : ""}</span></th>`` | MUERTO | 2 | test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r44_la_columna_ordenada_lleva_su_marca |
| E37 sin la casilla en los títulos | `app.js:3011` | `return "<th></th>" + titulosOrdenables(orden, [["trabajador", "Trabajador"],` → `return titulosOrdenables(orden, [["trabajador", "Trabajador"],` | MUERTO | 2 | test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E38 Líneas sin su clave | `app.js:3018` | `["recurso", "Recurso"], ["lineas", "Líneas"], ["motivo", "Motivo"]]);` → `["recurso", "Recurso"], ["n", "Líneas"], ["motivo", "Motivo"]]);` | MUERTO | 2 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar, test_f054_r44_la_columna_ordenada_lleva_su_marca |
| E39 Recurso sin título | `app.js:3018` | `["recurso", "Recurso"], ["lineas", "Líneas"], ["motivo", "Motivo"]]);` → `["lineas", "Líneas"], ["motivo", "Motivo"]]);` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E40 sin filtro-celda | `app.js:3024` | ``<th><div class="filtro-celda"><input class="col-filter" type="text" ` +` → ``<th><div><input class="col-filter" type="text" ` +` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E41 input sin col-filter | `app.js:3024` | ``<th><div class="filtro-celda"><input class="col-filter" type="text" ` +` → ``<th><div class="filtro-celda"><input class="filtro" type="text" ` +` | MUERTO | 2 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E42 sin data-filtro | `app.js:3025` | ``data-filtro="${clave}" placeholder="Contiene…">` +` → ``placeholder="Contiene…">` +` | MUERTO | 2 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E43 Limpiar en todas | `app.js:3026` | `(limpiar ? `<button type="button" class="filter-clear" id="${limpiar}">` +` → `(true ? `<button type="button" class="filter-clear" id="${limpiar}">` +` | MUERTO | 2 | test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E44 sin Limpiar | `app.js:3026` | `(limpiar ? `<button type="button" class="filter-clear" id="${limpiar}">` +` → `(false ? `<button type="button" class="filter-clear" id="${limpiar}">` +` | MUERTO | 41 | test_f054_r1_tras_un_sync_con_exito_se_pide_comparar, test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_los_avisos_de_postventa_y_de_var, test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r28_sin_pulsar_no_se_manda_nada, test_f054_r39_sin_entradas_no_hay_tabla, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_al_abrir_ningun_filtro_esta_puesto, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna, test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte, test_f054_r44_sin_no_traidas_ni_la_seccion, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E45 Limpiar sin filter-clear | `app.js:3026` | `(limpiar ? `<button type="button" class="filter-clear" id="${limpiar}">` +` → `(limpiar ? `<button type="button" id="${limpiar}">` +` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E46 parte sin escapar | `app.js:3031` | `return `<tr><td>${escapeHtml(f.textos.parte)}</td>` +` → `return `<tr><td>${f.textos.parte}</td>` +` | SUPERVIVIENTE | 0 | — |
| E47 recurso sin escapar | `app.js:3033` | ``<td>${escapeHtml(f.textos.recurso)}</td>` +` → ``<td>${f.textos.recurso}</td>` +` | MUERTO | 2 | test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E48 motivo sin escapar | `app.js:3035` | ``<td>${escapeHtml(f.textos.motivo)}</td></tr>`;` → ``<td>${f.textos.motivo}</td></tr>`;` | MUERTO | 2 | test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E49 obra sin escapar | `app.js:3032` | ``<td>${escapeHtml(f.textos.obra)}</td>` + `<td>${escapeHtml(f.textos.recurso)}` → ``<td>${f.textos.obra}</td>` + `<td>${escapeHtml(f.textos.recurso)}` | SUPERVIVIENTE | 0 | — |
| E50 ×K también con K = 1 | `app.js:3034` | ``<td>${f.n > 1 ? `×${f.n}` : ""}</td>` +` → ``<td>${f.n > 0 ? `×${f.n}` : ""}</td>` +` | MUERTO | 3 | test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_no_se_traen_en_una_tabla_agrupada |
| E51 ×K nunca | `app.js:3034` | ``<td>${f.n > 1 ? `×${f.n}` : ""}</td>` +` → ``<td>${""}</td>` +` | MUERTO | 3 | test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_no_se_traen_en_una_tabla_agrupada |
| E52 sin el texto de vacío | `app.js:3039` | `return visibles.length ? visibles.map(filaNoTraida).join("") : '<tr><td colspan="5" class="motivo">Ninguna línea con estos filtros.</td></tr>';` → `return visibles.map(filaNoTraida).join("");` | MUERTO | 1 | test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E53 el clic en la flecha no ordena | `app.js:3051` | `const th = ev.target.closest("[data-orden]");` → `const th = ev.target;` | MUERTO | 16 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_sin_pulsar_no_se_manda_nada, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_al_abrir_ningun_filtro_esta_puesto, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E54 clic sin columna no se ignora | `app.js:3052` | `if (!th) return; const col = th.dataset.orden;` → `const col = th && th.dataset.orden;` | MUERTO | 2 | test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna |
| E55 la segunda pulsación no invierte | `app.js:3054` | `parte.orden = { col, asc: parte.orden.col !== col \|\| !parte.orden.asc };` → `parte.orden = { col, asc: true };` | MUERTO | 7 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E56 otra columna sigue el sentido | `app.js:3054` | `parte.orden = { col, asc: parte.orden.col !== col \|\| !parte.orden.asc };` → `parte.orden = { col, asc: !parte.orden.asc };` | MUERTO | 1 | test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte |
| E57 ordenar no repinta | `app.js:3054` | `parte.orden = { col, asc: parte.orden.col !== col \|\| !parte.orden.asc }; repintar();` → `parte.orden = { col, asc: parte.orden.col !== col \|\| !parte.orden.asc };` | MUERTO | 9 | test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E58 filtrar no guarda | `app.js:3059` | `parte.filtros[ev.target.dataset.filtro] = ev.target.value;` → `(nada)` | MUERTO | 11 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla, test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E59 filtrar no repinta | `app.js:3059` | `parte.filtros[ev.target.dataset.filtro] = ev.target.value; repintar();` → `parte.filtros[ev.target.dataset.filtro] = ev.target.value;` | MUERTO | 10 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados |
| E60 cualquier tecla vacía | `app.js:3063` | `if (ev.key !== "Escape" \|\| ev.target.tagName !== "INPUT") return;` → `if (ev.target.tagName !== "INPUT") return;` | MUERTO | 1 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta |
| E61 Escape vacía también el desplegable | `app.js:3063` | `if (ev.key !== "Escape" \|\| ev.target.tagName !== "INPUT") return;` → `if (ev.key !== "Escape") return;` | MUERTO | 1 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta |
| E62 Escape con && (nunca corta) | `app.js:3063` | `if (ev.key !== "Escape" \|\| ev.target.tagName !== "INPUT") return;` → `if (ev.key !== "Escape" && ev.target.tagName !== "INPUT") return;` | MUERTO | 1 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta |
| E63 Escape no vacía el campo | `app.js:3064` | `ev.target.value = ""; parte.filtros[ev.target.dataset.filtro] = "";` → `parte.filtros[ev.target.dataset.filtro] = "";` | MUERTO | 1 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta |
| E64 Escape no vacía el modelo | `app.js:3064` | `ev.target.value = ""; parte.filtros[ev.target.dataset.filtro] = ""; repintar();` → `ev.target.value = ""; repintar();` | MUERTO | 1 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta |
| E65 Escape no repinta | `app.js:3065` | `parte.filtros[ev.target.dataset.filtro] = ""; repintar(); });` → `parte.filtros[ev.target.dataset.filtro] = ""; });` | MUERTO | 1 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta |
| E66 Escape cierra la ventana | `app.js:3065` | `parte.filtros[ev.target.dataset.filtro] = ""; repintar(); });` → `parte.filtros[ev.target.dataset.filtro] = ""; repintar(); cerrarModal(); });` | MUERTO | 1 | test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta |
| E67 Limpiar no vacía el modelo | `app.js:3069` | `Object.keys(parte.filtros).forEach((k) => { parte.filtros[k] = ""; });` → `(nada)` | MUERTO | 3 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla |
| E68 Limpiar solo el primer filtro | `app.js:3069` | `Object.keys(parte.filtros).forEach((k) => { parte.filtros[k] = ""; });` → `parte.filtros[Object.keys(parte.filtros)[0]] = "";` | MUERTO | 3 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla |
| E69 Limpiar no vacía los campos | `app.js:3070` | `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; });` → `(nada)` | MUERTO | 2 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla |
| E70 Limpiar vacía solo el primer campo | `app.js:3070` | `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; });` → `filtros.querySelectorAll(".col-filter")[0].value = "";` | MUERTO | 2 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla |
| E71 Limpiar no repinta | `app.js:3070` | `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; }); repintar();` → `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; });` | MUERTO | 3 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla |
| E72 Limpiar también desmarca | `app.js:3070` | `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; }); repintar();` → `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; }); (parte.filas \|\| []).forEach((f) => { f.marcada = false; }); repintar();` | MUERTO | 1 | test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla |
| E73 Limpiar también quita el orden | `app.js:3070` | `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; }); repintar();` → `filtros.querySelectorAll(".col-filter").forEach((c) => { c.value = ""; }); parte.orden = { col: null }; repintar();` | MUERTO | 2 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla |
| E74 tabla de entradas sin filterable | `app.js:3102` | `html += `<table class="tabla-reg filterable"><thead>` + `<tr id="traer-titulos">` → `html += `<table class="tabla-reg"><thead>` + `<tr id="traer-titulos">` | MUERTO | 2 | test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E75 filtros de entradas sin filter-row | `app.js:3104` | ``<tr id="traer-filtros" class="filter-row"><th></th>` +` → ``<tr id="traer-filtros"><th></th>` +` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E76 Estado sin filtro-celda | `app.js:3106` | ``<th><div class="filtro-celda"><select class="col-filter" data-filtro="estado">` +` → ``<th><div><select class="col-filter" data-filtro="estado">` +` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E77 Estado sin col-filter (Limpiar no lo vacía) | `app.js:3106` | ``<th><div class="filtro-celda"><select class="col-filter" data-filtro="estado">` +` → ``<th><div class="filtro-celda"><select data-filtro="estado">` +` | MUERTO | 2 | test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E78 Limpiar de entradas sin id | `app.js:3110` | ``${celdaFiltroTraer("detalle", "traer-limpiar")}</tr></thead>` +` → ``${celdaFiltroTraer("detalle")}</tr></thead>` +` | MUERTO | 40 | test_f054_r1_tras_un_sync_con_exito_se_pide_comparar, test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_los_avisos_de_postventa_y_de_var, test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r28_sin_pulsar_no_se_manda_nada, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_al_abrir_ningun_filtro_esta_puesto, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna, test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte, test_f054_r44_sin_no_traidas_ni_la_seccion, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E79 N = líneas, no filas | `app.js:3116` | `html += `<h3>No se traen (${nt.filas.length})</h3>` +` → `html += `<h3>No se traen (${(datos.no_traidas \|\| []).length})</h3>` +` | MUERTO | 3 | test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_no_se_traen_en_una_tabla_agrupada |
| E80 «No se traen» sin filterable | `app.js:3117` | ``<table class="tabla-reg filterable"><thead>` + `<tr id="no-traidas-titulos">` → ``<table class="tabla-reg"><thead>` + `<tr id="no-traidas-titulos">` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E81 «No se traen» sin filter-row | `app.js:3119` | ``<tr id="no-traidas-filtros" class="filter-row">` +` → ``<tr id="no-traidas-filtros">` +` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E82 Líneas con filtro | `app.js:3121` | ``${celdaFiltroTraer("recurso")}<th></th>` +` → ``${celdaFiltroTraer("recurso")}${celdaFiltroTraer("n")}` +` | MUERTO | 1 | test_f054_r43_las_dos_tablas_con_la_cabecera_estandar |
| E83 Limpiar de «No se traen» sin id | `app.js:3122` | ``${celdaFiltroTraer("motivo", "no-traidas-limpiar")}</tr></thead>` +` → ``${celdaFiltroTraer("motivo")}</tr></thead>` +` | MUERTO | 40 | test_f054_r1_tras_un_sync_con_exito_se_pide_comparar, test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_aceptar_sin_ninguna_marcada_avisa_y_no_manda, test_f054_r28_casilla_solo_en_distinta_y_solo_sigrid, test_f054_r28_el_texto_de_vacio_solo_sin_trabajadores, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_los_avisos_de_postventa_y_de_var, test_f054_r28_porcentaje_nulo_o_ausente_es_una_raya, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r28_sin_pulsar_no_se_manda_nada, test_f054_r39_sin_entradas_no_hay_tabla, test_f054_r39_una_sola_tabla_con_las_entradas_de_los_dos, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_al_abrir_ningun_filtro_esta_puesto, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna, test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_las_dos_tablas_con_la_cabecera_estandar, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_dos_iguales_y_una_distinta_dos_filas, test_f054_r44_el_recurso_distingue_por_su_ide, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_no_se_traen_en_una_tabla_agrupada, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte, test_f054_r45_recurso_con_codigo_y_nombre_o_su_ide |
| E84 sección aunque no haya | `app.js:3114` | `const nt = modelo.noTraidas; if (nt.filas.length) { html +=` → `const nt = modelo.noTraidas; if (true) { html +=` | MUERTO | 2 | test_f054_r39_sin_entradas_no_hay_tabla, test_f054_r44_sin_no_traidas_ni_la_seccion |
| E85 «No se traen» sin escuchas | `app.js:3162` | `const nt = modelo.noTraidas; if (nt.filas.length) { enlazarCabeceraTraer(` → `const nt = modelo.noTraidas; if (false) { enlazarCabeceraTraer(` | MUERTO | 10 | test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r39_sin_entradas_no_hay_tabla, test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E86 «No se traen» con escuchas aunque no haya | `app.js:3162` | `const nt = modelo.noTraidas; if (nt.filas.length) { enlazarCabeceraTraer(` → `const nt = modelo.noTraidas; if (true) { enlazarCabeceraTraer(` | MUERTO | 2 | test_f054_r39_sin_entradas_no_hay_tabla, test_f054_r44_sin_no_traidas_ni_la_seccion |
| E87 repintar «No se traen» sin títulos | `app.js:3165` | `$("#no-traidas-titulos").innerHTML = titulosNoTraidas(nt.orden);` → `(nada)` | MUERTO | 1 | test_f054_r44_la_columna_ordenada_lleva_su_marca |
| E88 repintar «No se traen» sin filtrar ni ordenar | `app.js:3167` | `cuerpoNoTraidas(noTraidasVisibles(nt.filas, nt.filtros, nt.orden));` → `cuerpoNoTraidas(nt.filas);` | MUERTO | 4 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E89 «No se traen» con el modelo de entradas | `app.js:3164` | `enlazarCabeceraTraer("no-traidas", nt, () => {` → `enlazarCabeceraTraer("no-traidas", modelo, () => {` | MUERTO | 5 | test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r44_filtros_contiene_sin_mayusculas_y_combinados, test_f054_r44_la_columna_ordenada_lleva_su_marca, test_f054_r44_ordena_cada_columna_y_la_segunda_invierte |
| E90 entradas sin la cabecera enlazada | `app.js:3171` | `enlazarCabeceraTraer("traer", modelo, repintar);` → `(nada)` | MUERTO | 25 | test_f054_r28_aceptar_manda_justo_las_marcadas_y_recarga, test_f054_r28_la_ventana_pinta_lo_que_manda_la_api, test_f054_r28_sin_entradas_aceptables_no_hay_boton_de_aceptar, test_f054_r28_sin_pulsar_no_se_manda_nada, test_f054_r40_cuadrante_y_sigrid_numericos_con_la_raya_al_final, test_f054_r40_la_cabecera_de_la_casilla_no_ordena, test_f054_r40_la_columna_ordenada_lleva_su_marca, test_f054_r40_la_raya_tambien_si_falta_el_porcentaje, test_f054_r40_ordena_por_texto_y_la_segunda_pulsacion_invierte, test_f054_r40_texto_sin_distinguir_mayusculas_y_empate_estable, test_f054_r41_al_abrir_ningun_filtro_esta_puesto, test_f054_r41_desplegable_de_estado_y_filtros_combinados, test_f054_r41_filtrar_u_ordenar_no_toca_las_casillas, test_f054_r41_filtro_de_obra_deja_solo_esa_obra, test_f054_r41_sin_filas_visibles_lo_dice, test_f054_r41_texto_sin_distinguir_mayusculas_sobre_lo_pintado, test_f054_r42_desmarcar_todas_quita_tambien_las_ocultas, test_f054_r42_el_boton_cuenta_las_marcadas_y_las_ocultas, test_f054_r42_marcar_las_visibles_solo_las_visibles_con_casilla, test_f054_r43_el_clic_en_la_flecha_ordena_por_su_columna, test_f054_r43_escape_vacia_el_filtro_de_texto_y_repinta, test_f054_r43_limpiar_de_no_se_traen_no_toca_la_otra, test_f054_r43_limpiar_vacia_los_filtros_de_esa_tabla, test_f054_r43_limpiar_vacia_todos_los_filtros_de_la_tabla, test_f054_r44_la_columna_ordenada_lleva_su_marca |

**Análisis de los 5 supervivientes** (todos huecos reales de test; ningún
cambio de código de producción):

- **E4** (el modelo sin la clave `recurso` en los filtros): el filtro se
  crea al teclear, así que la ventana se comportaba igual; ningún test
  miraba el modelo inicial. Test `test_f054_r44_el_filtro_de_recurso_existe_desde_el_principio`.
- **E6** (clave del grupo sin la obra): los datos no tenían dos líneas que
  solo difiriesen en la obra. Test `test_f054_r44_cada_clave_del_grupo_distingue`.
- **E28** (ordenar sin pasar a minúsculas): ningún dato de «No se traen»
  con el mismo texto en mayúsculas y minúsculas. Test
  `test_f054_r44_ordenar_texto_sin_distinguir_mayusculas_empate_estable`.
- **E46, E49** (Parte y Obra sin escapar): los datos no traían `<` en esas
  columnas. Test `test_f054_r44_parte_y_obra_escapadas`.

## Campaña 8 (`4e5ac80`): los vivos de la 7, 5 muertos, 0 supervivientes

Línea base (sin mutar, en verde): 103 passed in 28.78s · Tiempo: 186.1 s

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| E4 filtro de Recurso sin clave | `app.js:2900` | `filtros: { parte: "", obra: "", recurso: "", motivo: "" } };` → `filtros: { parte: "", obra: "", motivo: "" } };` | MUERTO | 1 | test_f054_r44_el_filtro_de_recurso_existe_desde_el_principio |
| E6 clave sin obra | `app.js:2912` | `const clave = JSON.stringify([n.parte_cod, n.obra_cod, n.recurso_ide,` → `const clave = JSON.stringify([n.parte_cod, n.recurso_ide,` | MUERTO | 1 | test_f054_r44_cada_clave_del_grupo_distingue |
| E28 texto con mayúsculas al ordenar | `app.js:2936` | `: a.textos[orden.col].toLowerCase() .localeCompare(b.textos[orden.col].toLowerCase(), "es");` → `: a.textos[orden.col] .localeCompare(b.textos[orden.col], "es");` | MUERTO | 1 | test_f054_r44_ordenar_texto_sin_distinguir_mayusculas_empate_estable |
| E46 parte sin escapar | `app.js:3031` | `return `<tr><td>${escapeHtml(f.textos.parte)}</td>` +` → `return `<tr><td>${f.textos.parte}</td>` +` | MUERTO | 1 | test_f054_r44_parte_y_obra_escapadas |
| E49 obra sin escapar | `app.js:3032` | ``<td>${escapeHtml(f.textos.obra)}</td>` + `<td>${escapeHtml(f.textos.recurso)}` → ``<td>${f.textos.obra}</td>` + `<td>${escapeHtml(f.textos.recurso)}` | MUERTO | 1 | test_f054_r44_parte_y_obra_escapadas |

**Total T24: 90 + 5 mutantes, 0 supervivientes.** `mutacion_manual_f054_c8.py`
filtra la `M` de la campaña 7 a `{E4, E6, E28, E46, E49}`.

## Campaña 9 (`ff3d1ac`, T27/R48): 15 mutantes, 15 muertos, 0 supervivientes

La regla nueva de `styles.css` (la automática no muta CSS) y los dos `<thead><tr id=…>` de
`app.js` de los que depende su `:has(> #…)`. A diferencia de las campañas 1-8, sobre el
**árbol de trabajo** (cada mutante restaurado en un `finally`; `git diff` limpio al acabar) y
solo con `tests/test_f054_traer_front.py` sin `-x` (importa el escenario de
`test_f054_modal_cero.py`). Textos recortados a 70 caracteres en la tabla; el canónico es la
lista `M` del script `mutacion_manual_f054_c9.py` (fuera del repo, copiado abajo).

Línea base (sin mutar, en verde): 64 passed in 42.69s

| Mutante | Fichero | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| F1 sin sticky | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `top: 0; z-index: 2; background: var(--paper); }` | MUERTO | 2 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas, test_f054_r48_ninguna_otra_regla_sticky_nueva |
| F2 relative en vez de sticky | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `position: relative; top: 0; z-index: 2; background: var(--paper); }` | MUERTO | 2 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas, test_f054_r48_ninguna_otra_regla_sticky_nueva |
| F3 sin top | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `position: sticky; z-index: 2; background: var(--paper); }` | MUERTO | 1 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| F4 top con hueco | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `position: sticky; top: 22px; z-index: 2; background: var(--paper); }` | MUERTO | 1 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| F5b z-index por debajo | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `position: sticky; top: 0; z-index: 0; background: var(--paper); }` | MUERTO | 1 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| F5 sin z-index | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `position: sticky; top: 0; background: var(--paper); }` | MUERTO | 1 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| F6 sin background | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `position: sticky; top: 0; z-index: 2; }` | MUERTO | 1 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| F7 background transparente | `styles.css` | `position: sticky; top: 0; z-index: 2; background: var(--paper); }` → `position: sticky; top: 0; z-index: 2; background: transparent; }` | MUERTO | 1 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| F8 sin el selector de entradas | `styles.css` | `.modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-tit` → `.modal thead:has(> #no-traidas-titulos) {` | MUERTO | 2 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas, test_f054_r48_ninguna_otra_regla_sticky_nueva |
| F9 sin el selector de No se traen | `styles.css` | `.modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-tit` → `.modal thead:has(> #traer-titulos) {` | MUERTO | 2 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas, test_f054_r48_ninguna_otra_regla_sticky_nueva |
| F10 a todo thead del modal | `styles.css` | `.modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-tit` → `.modal thead {` | MUERTO | 2 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas, test_f054_r48_ninguna_otra_regla_sticky_nueva |
| F11 sin el hijo directo | `styles.css` | `.modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-tit` → `.modal thead:has(#traer-titulos), .modal thead:has(#no-traidas-titulos` | MUERTO | 2 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas, test_f054_r48_ninguna_otra_regla_sticky_nueva |
| F12 sticky en .filter-row | `styles.css` | `.modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-tit` → `.modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-tit` | MUERTO | 2 | test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas, test_f054_r48_ninguna_otra_regla_sticky_nueva |
| F13 tr de entradas no hijo del thead | `app.js` | ``<table class="tabla-reg filterable"><thead>` + `<tr id="traer-t` → ``<table class="tabla-reg filterable"><thead><tr></tr>` + `<tr id` | MUERTO | 1 | test_f054_r48_los_id_van_en_la_primera_fila_hija_del_thead |
| F14 tr de No se traen sin id | `app.js` | ``<tr id="no-traidas-titulos">${titulosNoTraidas` → ``<tr>${titulosNoTraidas` | MUERTO | 45 | test_f054_r1_tras_un_sync_con_exito_se_pide_comparar … (45 tests) |

**Total T27: 15 mutantes, 0 supervivientes.**

```python
# mutacion_manual_f054_c9.py (fuera del repo): T27, regla de R48.
import pathlib, re, subprocess, sys

RAIZ = pathlib.Path(r"C:\Users\pgris\PycharmProjects\porcentajes-f054\services\dedicacion-front")
CSS = RAIZ / "static" / "css" / "styles.css"
JS = RAIZ / "static" / "js" / "app.js"
REGLA = (".modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-titulos) {")
DECL = "  position: sticky; top: 0; z-index: 2; background: var(--paper); }"
M = [
    ("F1 sin sticky", CSS, DECL, "  top: 0; z-index: 2; background: var(--paper); }"),
    ("F2 relative en vez de sticky", CSS, DECL, "  position: relative; top: 0; z-index: 2; background: var(--paper); }"),
    ("F3 sin top", CSS, DECL, "  position: sticky; z-index: 2; background: var(--paper); }"),
    ("F4 top con hueco", CSS, DECL, "  position: sticky; top: 22px; z-index: 2; background: var(--paper); }"),
    ("F5b z-index por debajo", CSS, DECL, "  position: sticky; top: 0; z-index: 0; background: var(--paper); }"),
    ("F5 sin z-index", CSS, DECL, "  position: sticky; top: 0; background: var(--paper); }"),
    ("F6 sin background", CSS, DECL, "  position: sticky; top: 0; z-index: 2; }"),
    ("F7 background transparente", CSS, DECL, "  position: sticky; top: 0; z-index: 2; background: transparent; }"),
    ("F8 sin el selector de entradas", CSS, REGLA, ".modal thead:has(> #no-traidas-titulos) {"),
    ("F9 sin el selector de No se traen", CSS, REGLA, ".modal thead:has(> #traer-titulos) {"),
    ("F10 a todo thead del modal", CSS, REGLA, ".modal thead {"),
    ("F11 sin el hijo directo", CSS, REGLA, ".modal thead:has(#traer-titulos), .modal thead:has(#no-traidas-titulos) {"),
    ("F12 sticky en .filter-row", CSS, REGLA, ".modal thead:has(> #traer-titulos), .modal thead:has(> #no-traidas-titulos), .filterable .filter-row {"),
    ("F13 tr de entradas no hijo del thead", JS, '`<table class="tabla-reg filterable"><thead>` +\n      `<tr id="traer-titulos">', '`<table class="tabla-reg filterable"><thead><tr></tr>` +\n      `<tr id="traer-titulos">'),
    ("F14 tr de No se traen sin id", JS, '`<tr id="no-traidas-titulos">${titulosNoTraidas', '`<tr>${titulosNoTraidas'),
]


def pytest():
    r = subprocess.run([str(RAIZ / ".venv" / "Scripts" / "python.exe"), "-m", "pytest",
                        "tests/test_f054_traer_front.py", "-q", "-p", "no:cacheprovider", "-rf"],
                       cwd=RAIZ, capture_output=True, text=True)
    fallos = sorted(set(re.findall(r"^FAILED \S+::(\w+)", r.stdout, re.M)))
    return r.returncode, fallos, r.stdout.strip().splitlines()[-1]


base = pytest()
print("BASE", base[0], base[2])
assert base[0] == 0
vivos = 0
for nombre, f, a, b in M:
    orig = f.read_bytes()
    txt = orig.decode("utf-8")
    nl = "\r\n" in txt
    t = txt.replace("\r\n", "\n")
    assert t.count(a) == 1, nombre
    t = t.replace(a, b)
    f.write_bytes((t.replace("\n", "\r\n") if nl else t).encode("utf-8"))
    try:
        rc, fallos, ult = pytest()
    finally:
        f.write_bytes(orig)
    estado = "MUERTO" if rc else "VIVO"
    vivos += not rc
    print(f"| {nombre} | `{f.name}` | `{a.strip()[:70]}` → `{b.strip()[:70]}` | {estado} | {len(fallos)} | {', '.join(fallos)} |")
print("VIVOS", vivos)
```

## Campaña 10 (`c9611c3`, corrección de T27/R48): 13 mutantes, 13 muertos, 0 supervivientes

La MANUAL de T18 paso 2 (2026-11-05) vio la franja de 22 px sobre la cabecera fija: `top: 0`
en un `.modal` con padding. Mutantes del **valor del `top`** y de lo que lo ata al padding
(`--modal-pad-top`). Mismo método que la campaña 9 (árbol de trabajo, `finally`, solo
`tests/test_f054_traer_front.py` sin `-x`). G10 y G11 cambian padding y `top` a la vez (sin
hueco, pero el modal cambia de aspecto): los mata el `22px` fijado en el test.

Línea base (sin mutar, en verde): 66 passed in 72.19s

| Mutante | Texto exacto original → mutado (recortado a 60) | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|
| G1 top 0 (el fallo) | `position: sticky; top: calc(-1 * var(--modal-pad-top)); z-in` → `position: sticky; top: 0; z-index: 2;` | MUERTO | 2 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal, test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| G2 top positivo | `position: sticky; top: calc(-1 * var(--modal-pad-top)); z-in` → `position: sticky; top: var(--modal-pad-top); z-index: 2;` | MUERTO | 2 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal, test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| G3 top -22px a mano | `position: sticky; top: calc(-1 * var(--modal-pad-top)); z-in` → `position: sticky; top: -22px; z-index: 2;` | MUERTO | 2 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal, test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| G4 top calc con 22px | `position: sticky; top: calc(-1 * var(--modal-pad-top)); z-in` → `position: sticky; top: calc(-1 * 22px); z-index: 2;` | MUERTO | 2 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal, test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| G5 top -padding/2 | `position: sticky; top: calc(-1 * var(--modal-pad-top)); z-in` → `position: sticky; top: calc(-0.5 * var(--modal-pad-top)); z-` | MUERTO | 2 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal, test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| G6 top otra variable | `position: sticky; top: calc(-1 * var(--modal-pad-top)); z-in` → `position: sticky; top: calc(-1 * var(--modal-pad)); z-index:` | MUERTO | 2 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal, test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| G7 top sin el signo | `position: sticky; top: calc(-1 * var(--modal-pad-top)); z-in` → `position: sticky; top: calc(1 * var(--modal-pad-top)); z-ind` | MUERTO | 2 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal, test_f054_r48_la_regla_fija_las_dos_cabeceras_y_las_hace_opacas |
| G8 padding a mano | `padding: var(--modal-pad-top) 26px; }` → `padding: 22px 26px; }` | MUERTO | 1 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal |
| G9 padding-top aparte | `padding: var(--modal-pad-top) 26px; }` → `padding: var(--modal-pad-top) 26px; padding-top: 30px; }` | MUERTO | 1 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal |
| G10 variable a 0 | `.modal { --modal-pad-top: 22px; background: var(--paper);` → `.modal { --modal-pad-top: 0; background: var(--paper);` | MUERTO | 1 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal |
| G11 variable distinta | `.modal { --modal-pad-top: 22px; background: var(--paper);` → `.modal { --modal-pad-top: 30px; background: var(--paper);` | MUERTO | 1 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal |
| G12 sin la variable | `.modal { --modal-pad-top: 22px; background: var(--paper);` → `.modal { background: var(--paper);` | MUERTO | 1 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal |
| G13 padding redefinido en otra regla .modal | `.modal h2 {` → `.modal { padding: 10px 26px; } .modal h2 {` | MUERTO | 1 | test_f054_r48_el_top_compensa_el_padding_superior_del_modal |

**Total corrección T27: 13 mutantes, 0 supervivientes.**

```python
# mutacion_manual_f054_c10.py (fuera del repo): T27, valor del `top` de R48.
import pathlib, re, subprocess

RAIZ = pathlib.Path(r"C:\Users\pgris\PycharmProjects\porcentajes-f054\services\dedicacion-front")
CSS = RAIZ / "static" / "css" / "styles.css"
TOP = "position: sticky; top: calc(-1 * var(--modal-pad-top)); z-index: 2;"
VAR = ".modal { --modal-pad-top: 22px; background: var(--paper);"
PAD = "  padding: var(--modal-pad-top) 26px; }"
M = [
    ("G1 top 0 (el fallo)", TOP, "position: sticky; top: 0; z-index: 2;"),
    ("G2 top positivo", TOP, "position: sticky; top: var(--modal-pad-top); z-index: 2;"),
    ("G3 top -22px a mano", TOP, "position: sticky; top: -22px; z-index: 2;"),
    ("G4 top calc con 22px", TOP, "position: sticky; top: calc(-1 * 22px); z-index: 2;"),
    ("G5 top -padding/2", TOP, "position: sticky; top: calc(-0.5 * var(--modal-pad-top)); z-index: 2;"),
    ("G6 top otra variable", TOP, "position: sticky; top: calc(-1 * var(--modal-pad)); z-index: 2;"),
    ("G7 top sin el signo", TOP, "position: sticky; top: calc(1 * var(--modal-pad-top)); z-index: 2;"),
    ("G8 padding a mano", PAD, "  padding: 22px 26px; }"),
    ("G9 padding-top aparte", PAD, "  padding: var(--modal-pad-top) 26px; padding-top: 30px; }"),
    ("G10 variable a 0", VAR, ".modal { --modal-pad-top: 0; background: var(--paper);"),
    ("G11 variable distinta", VAR, ".modal { --modal-pad-top: 30px; background: var(--paper);"),
    ("G12 sin la variable", VAR, ".modal { background: var(--paper);"),
    ("G13 padding redefinido en otra regla .modal", ".modal h2 {", ".modal { padding: 10px 26px; }\n.modal h2 {"),
]


def pytest():
    r = subprocess.run([str(RAIZ / ".venv" / "Scripts" / "python.exe"), "-m", "pytest",
                        "tests/test_f054_traer_front.py", "-q", "-p", "no:cacheprovider", "-rf"],
                       cwd=RAIZ, capture_output=True, text=True)
    fallos = sorted(set(re.findall(r"^FAILED \S+::(\w+)", r.stdout, re.M)))
    return r.returncode, fallos, r.stdout.strip().splitlines()[-1]


base = pytest()
print("BASE", base[0], base[2])
assert base[0] == 0
vivos = 0
for nombre, a, b in M:
    orig = CSS.read_bytes()
    txt = orig.decode("utf-8")
    nl = "\r\n" in txt
    t = txt.replace("\r\n", "\n")
    assert t.count(a) == 1, nombre
    t = t.replace(a, b)
    CSS.write_bytes((t.replace("\n", "\r\n") if nl else t).encode("utf-8"))
    try:
        rc, fallos, ult = pytest()
    finally:
        CSS.write_bytes(orig)
    estado = "MUERTO" if rc else "VIVO"
    vivos += not rc
    print(f"| {nombre} | `{a.strip()[:60]}` → `{b.strip()[:60]}` | {estado} | {len(fallos)} | {', '.join(fallos)} |")
print("VIVOS", vivos)
```
