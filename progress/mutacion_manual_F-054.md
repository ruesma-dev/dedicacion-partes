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
