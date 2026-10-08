<!-- progress/mutacion_manual_F-049.md -->
# F-049 · Mutación manual de `app.js`

`python -m harness.mutacion` solo muta Python y F-049 solo cambia JavaScript
(`services/dedicacion-front/static/js/app.js`): esta campaña la sustituye,
como en F-041 y F-042.

- **Medida sobre** `3ad478b` (T1) más el test que añade T2 (T2 no toca
  `app.js`, así que las líneas son las de `3ad478b`).
- **Método**: el script de abajo aplica cada mutante como sustitución de
  texto exacto (tiene que aparecer **una** vez; si no, `NO_APLICA`) sobre
  `app.js`, pasa `tests/test_f049_avisos_registro.py` con el `.venv` del
  front y `-x`, y **restaura el original en un `finally`**. `git status`
  quedó sin `app.js` modificado después de cada pasada (comprobado).
- «Test que lo mata» es el primero que falla (con `-x`).
- «Fallos (sin `-x`)»: nº de tests en rojo de 18, medido por el implementer en la vuelta de la review 1 con
  el mismo script **sin `-x`** sobre un `git archive HEAD` (`12627f7`, mismo
  `app.js` que `3ad478b`) fuera del árbol: 33/33 MUERTOS, cifras idénticas a
  las del reviewer, 299 s en serie.
- La columna «Mutación» **resume**: el texto exacto original → mutado de cada
  mutante es el de la lista `M` del script (la canónica).

## Reproducir

Guardar el bloque del final como `mutacion_manual_f049.py` **fuera del repo**
(un `.py` fuera de `tests/` entra en el alcance de producción de
`harness/alcance.py`) y, desde la raíz del repo:

```bash
PYTHONIOENCODING=utf-8 python <ruta>/mutacion_manual_f049.py
```

## 1 · Primera pasada (T1, `3ad478b`): 33 mutantes, 1 superviviente

**M19** (separador `", "` → `" "` entre las líneas contadas de la
sobrecarga) **sobrevivía**: todos los datos de prueba tenían una sola línea
contada, así que el separador no se veía. **Hueco real, no equivalente**: con
dos líneas el texto sale pegado («MADM 60% MENC 35%»). Se cierra en T2 con
`test_f049_r1_sobrecarga_con_varias_lineas_contadas`.

## 2 · Campaña final (T2): 33 mutantes, 33 muertos, 0 supervivientes

| Mutante | Sitio | Mutación (resumen) | Resultado | Fallos (sin `-x`) | Test que lo mata (con `-x`) |
|---|---|---|---|---|---|
| M01 | `app.js:1718` | `c.motivo \|\| "pisado"` → `c.motivo` | MUERTO | 2 | test_f049_r1_motivo_vacio_es_pisado[] |
| M02 | `app.js:1718` | por defecto `"pisado"` → `"sin_partida"` | MUERTO | 2 | test_f049_r1_motivo_vacio_es_pisado[] |
| M03 | `app.js:1719` | `motivo === "sin_partida"` → `!==` | MUERTO | 11 | test_f049_r1_sin_partida_se_rotula_como_sin_partida |
| M04 | `app.js:1725` | `"sobrecarga"` → `"sobrecarga_"` | MUERTO | 4 | test_f049_r1_sobrecarga_ensena_existente_total_y_exceso |
| M05 | `app.js:1735` | `if (motivo === "pisado")` → `if (true)` | MUERTO | 1 | test_f049_r1_motivo_desconocido_no_se_disfraza_de_pisado |
| M06 | `app.js:1745` | `titulo: "Confirmar"` → `"Pisar"` | MUERTO | 1 | test_f049_r1_motivo_desconocido_no_se_disfraza_de_pisado |
| M07 | `app.js:1709` | `Number(n.can) \|\| 0` → `\|\| 1` | MUERTO | 1 | test_f049_r2_decimales_y_sin_nuevas |
| M08 | `app.js:1709` | `s + (…)` → `s - (…)` | MUERTO | 9 | test_f049_r1_sin_partida_se_rotula_como_sin_partida |
| M09 | `app.js:1710` | `fmtPct(suma * 100)` → `fmtPct(suma)` | MUERTO | 9 | test_f049_r1_sin_partida_se_rotula_como_sin_partida |
| M10 | `app.js:1709` | `c.nuevas` → `c.lineas` | MUERTO | 9 | test_f049_r1_sin_partida_se_rotula_como_sin_partida |
| M11 | `app.js:1714` | `String(c.recurso_ide)` → `""` | MUERTO | 1 | test_f049_r1_sin_nombre_ni_parte |
| M12 | `app.js:1716` | `enParte` siempre con `parte_cod` | MUERTO | 1 | test_f049_r1_sin_nombre_ni_parte |
| M13 | `app.js:1716` | `enParte` siempre vacío | MUERTO | 4 | test_f049_r1_sin_partida_se_rotula_como_sin_partida |
| M14 | `app.js:1721` | sin partida sin `${nuevo}` | MUERTO | 3 | test_f049_r1_sin_partida_se_rotula_como_sin_partida |
| M15 | `app.js:1730` | «ya tiene» con `suma_total` | MUERTO | 3 | test_f049_r1_sobrecarga_ensena_existente_total_y_exceso |
| M16 | `app.js:1731` | «sumaría» con `suma_existente` | MUERTO | 1 | test_f049_r1_sobrecarga_ensena_existente_total_y_exceso |
| M17 | `app.js:1732` | exceso con `suma_existente` | MUERTO | 1 | test_f049_r1_sobrecarga_ensena_existente_total_y_exceso |
| M18 | `app.js:1730` | sin el paréntesis de líneas contadas | MUERTO | 2 | test_f049_r1_sobrecarga_ensena_existente_total_y_exceso |
| M19 | `app.js:1727` | separador de contadas `", "` → `" "` | MUERTO | 1 | test_f049_r1_sobrecarga_con_varias_lineas_contadas (añadido en T2) |
| M20 | `app.js:1727` | contadas sin `hora_codigo` | MUERTO | 2 | test_f049_r1_sobrecarga_ensena_existente_total_y_exceso |
| M21 | `app.js:1737` | `línea ${l.ide}` → `${l.reside}` | MUERTO | 1 | test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo |
| M22 | `app.js:1738` | sin `fec ${l.fecha_int}` | MUERTO | 1 | test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo |
| M23 | `app.js:1738` | separador de borradas `", "` → `" "` | MUERTO | 1 | test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo |
| M24 | `app.js:1738` | % de borradas sin `* 100` | MUERTO | 1 | test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo |
| M25 | `app.js:1740` | pisado sin `${viejas}` | MUERTO | 1 | test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo |
| M26 | `app.js:1741` | `escribe ${nuevo}` → `escribe 0%` (el fallo original) | MUERTO | 3 | test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo |
| M27 | `app.js:1746` | motivo desconocido sin `${motivo}` | MUERTO | 1 | test_f049_r1_motivo_desconocido_no_se_disfraza_de_pisado |
| M28 | `app.js:1792` | casilla con `c.registros` en vez de `c.clave` | MUERTO | 1 | test_f049_r3_las_casillas_llevan_la_clave_de_cada_conflicto |
| M29 | `app.js:1793` | `r.detalle` sin `escapeHtml` | MUERTO | 1 | test_f049_r3_el_rotulo_se_escapa |
| M30 | `app.js:1793` | título fijo `Pisar` (el fallo original) | MUERTO | 1 | test_f049_r3_el_modal_pinta_el_rotulo_por_tipo |
| M31 | `app.js:1790` | `rotuloConflicto({...c, motivo: ""})` | MUERTO | 1 | test_f049_r3_el_modal_pinta_el_rotulo_por_tipo |
| M32 | `app.js:1788` | `conflictos.slice(1)` (se pierde una casilla) | MUERTO | 3 | test_f049_r3_las_casillas_llevan_la_clave_de_cada_conflicto |
| M33 | `app.js:1811` | `pisar` sin la primera clave marcada | MUERTO | 1 | test_f049_r3_ejecutar_manda_las_mismas_claves |

M26 y M30 son, en miniatura, el fallo que comunicó el humano (todo «Pisar»
con 0 %): la suite caza los dos.

## Script

```python
# Campaña manual de mutantes de F-049 sobre app.js (la mutación automática no muta JS).
import subprocess, sys
from pathlib import Path
SERV = Path.cwd() / "services" / "dedicacion-front"
APP = SERV / "static" / "js" / "app.js"
PY = SERV / ".venv" / "Scripts" / "python.exe"
ORIG = APP.read_bytes()
M = [
 ("M01", 'const motivo = c.motivo || "pisado";', 'const motivo = c.motivo;'),
 ("M02", 'const motivo = c.motivo || "pisado";', 'const motivo = c.motivo || "sin_partida";'),
 ("M03", 'if (motivo === "sin_partida") {', 'if (motivo !== "sin_partida") {'),
 ("M04", 'if (motivo === "sobrecarga") {', 'if (motivo === "sobrecarga_") {'),
 ("M05", 'if (motivo === "pisado") {', 'if (true) {'),
 ("M06", 'titulo: "Confirmar"', 'titulo: "Pisar"'),
 ("M07", 's + (Number(n.can) || 0), 0)', 's + (Number(n.can) || 1), 0)'),
 ("M08", 's + (Number(n.can) || 0), 0)', 's - (Number(n.can) || 0), 0)'),
 ("M09", 'return fmtPct(suma * 100);', 'return fmtPct(suma);'),
 ("M10", '(c.nuevas || []).reduce', '(c.lineas || []).reduce'),
 ("M11", 'const quien = c.nombre || String(c.recurso_ide);', 'const quien = c.nombre || "";'),
 ("M12", 'const enParte = c.parte_cod ? ` en el parte ${c.parte_cod}` : "";', 'const enParte = ` en el parte ${c.parte_cod}`;'),
 ("M13", 'const enParte = c.parte_cod ? ` en el parte ${c.parte_cod}` : "";', 'const enParte = "";'),
 ("M14", 'detalle: `${quien}, ${hora} ${nuevo}${enParte}: se escribiría sin ` +', 'detalle: `${quien}, ${hora}${enParte}: se escribiría sin ` +'),
 ("M15", '`${fmtPct(c.suma_existente * 100)}${ya', '`${fmtPct(c.suma_total * 100)}${ya'),
 ("M16", 'sumaría ${fmtPct(c.suma_total * 100)}', 'sumaría ${fmtPct(c.suma_existente * 100)}'),
 ("M17", '`${fmtPct(c.exceso * 100)} por encima', '`${fmtPct(c.suma_existente * 100)} por encima'),
 ("M18", '${ya ? ` (${ya})` : ""}', ''),
 ("M19", '`${l.hora_codigo || ""} ${fmtPct((Number(l.can) || 0) * 100)}`).join(", ");', '`${l.hora_codigo || ""} ${fmtPct((Number(l.can) || 0) * 100)}`).join(" ");'),
 ("M20", '`${l.hora_codigo || ""} ${fmtPct((Number(l.can) || 0) * 100)}`).join(", ");', '`${fmtPct((Number(l.can) || 0) * 100)}`).join(", ");'),
 ("M21", '`línea ${l.ide} (', '`línea ${l.reside} ('),
 ("M22", '${fmtPct((Number(l.can) || 0) * 100)}, fec ${l.fecha_int})`).join(", ");', '${fmtPct((Number(l.can) || 0) * 100)})`).join(", ");'),
 ("M23", '${fmtPct((Number(l.can) || 0) * 100)}, fec ${l.fecha_int})`).join(", ");', '${fmtPct((Number(l.can) || 0) * 100)}, fec ${l.fecha_int})`).join(" ");'),
 ("M24", '${fmtPct((Number(l.can) || 0) * 100)}, fec ${l.fecha_int})`).join(", ");', '${fmtPct(Number(l.can) || 0)}, fec ${l.fecha_int})`).join(", ");'),
 ("M25", 'detalle: `${hora} de ${quien}${enParte}: se borran ${viejas} y se ` +', 'detalle: `${hora} de ${quien}${enParte}: se borran y se ` +'),
 ("M26", '`escribe ${nuevo}` };', '`escribe 0%` };'),
 ("M27", 'detalle: `${quien}, ${hora} ${nuevo}${enParte}: ${motivo}` };', 'detalle: `${quien}, ${hora} ${nuevo}${enParte}` };'),
 ("M28", 'class="chk-pisar" value="${escapeHtml(c.clave)}"> ` +\n        `<strong>', 'class="chk-pisar" value="${escapeHtml(c.registros)}"> ` +\n        `<strong>'),
 ("M29", '`<strong>${escapeHtml(r.titulo)}</strong> · ${escapeHtml(r.detalle)}`', '`<strong>${escapeHtml(r.titulo)}</strong> · ${r.detalle}`'),
 ("M30", '`<strong>${escapeHtml(r.titulo)}</strong> · ${escapeHtml(r.detalle)}`', '`<strong>Pisar</strong> · ${escapeHtml(r.detalle)}`'),
 ("M31", 'const r = rotuloConflicto(c);', 'const r = rotuloConflicto({ ...c, motivo: "" });'),
 ("M32", '(o.conflictos || []).forEach((c) => {\n      // F-049', '(o.conflictos || []).slice(1).forEach((c) => {\n      // F-049'),
 ("M33", '.map((c) => c.value);', '.map((c) => c.value).slice(1);'),
]
res = []
try:
    for mid, a, b in M:
        txt = ORIG.decode("utf-8")
        n = txt.count(a)
        if n != 1:
            res.append((mid, "NO_APLICA(%d)" % n, a, b)); continue
        APP.write_bytes(txt.replace(a, b).encode("utf-8"))
        r = subprocess.run([str(PY), "-m", "pytest", "tests/test_f049_avisos_registro.py", "-q", "-x", "-p", "no:cacheprovider"],
                           cwd=SERV, capture_output=True, text=True, encoding="utf-8")
        ultima = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
        failed = [l.split("::")[1].split(" ")[0] for l in r.stdout.splitlines() if l.startswith("FAILED")]
        res.append((mid, "MUERTO" if r.returncode else "VIVO", ultima, failed[:1]))
finally:
    APP.write_bytes(ORIG)
for x in res:
    print(x)
```

## 3 · Ampliación (T4-T7): 32 mutantes, 32 muertos, 0 supervivientes

La ampliación toca `app.js` (T5) y `styles.css` (T6); el transfer (T4) lo
muta `harness.mutacion` (`progress/mutacion_F-049.md`: 7/7 muertos).

- **Medida sobre** `e7b660f` (T6) más el test que añade T7 (T7 no toca
  `app.js` ni `styles.css`: las líneas son las de `e7b660f`).
- **Método**: el script de abajo (mismo patrón que el de §2) aplica cada
  mutante como sustitución de texto exacto (una sola aparición; si no,
  `NO_APLICA`), pasa **sin `-x`** los tres ficheros que miran ese código
  (`test_f049_ampliacion_registro.py`, `test_f049_avisos_registro.py` y
  `test_f039_partida_fija.py`: **45 tests**) con el `.venv` del front y
  restaura el original en un `finally` tras cada mutante. `git status`
  quedó sin `app.js` ni `styles.css` modificados (comprobado).
- **En serie, 1 proceso: 302 s** la campaña final completa. Repetida tras
  quitar los avisos de `ruff` del test (solo forma): **resultados idénticos**
  mutante a mutante, 325 s.
- «Fallos»: nº de tests en rojo de 45. «Primer test»: el primero en rojo.
- `⏎` es un salto de línea del texto exacto.

**Primera pasada** (antes de T7): 32/32 muertos, pero **A27** (llamar a
`repreflightPartida()` antes de apuntar la partida, con lo que viajaría la
anterior) solo lo mataba la comprobación ESTÁTICA del orden
(`test_f049_a_solo_el_desplegable_repite_el_preflight`, 1 fallo). Hueco real
de comportamiento, no equivalente: T7 añade
`test_f049_a_el_preflight_repetido_lleva_la_partida_recien_elegida` (modal,
`change` y petición reales) y A27 pasa a 2 fallos.

| Mutante | Sitio | Texto exacto original | Mutado | Resultado | Fallos | Primer test |
|---|---|---|---|---|---|---|
| A01 | `app.js:1684` | `` if (sel && !(partidas \|\| []).some((p) => p.ide === sel)) { `` | `` if (false) { `` | MUERTO | 5 | test_f049_c_partida_fuera_de_la_lista_se_ensena_igual |
| A02 | `app.js:1684` | `` if (sel && !(partidas \|\| []).some((p) => p.ide === sel)) { `` | `` if (!(partidas \|\| []).some((p) => p.ide === sel)) { `` | MUERTO | 2 | test_f049_c_sin_partida_no_inventa_ninguna[0] |
| A03 | `app.js:1684` | `` if (sel && !(partidas \|\| []).some((p) => p.ide === sel)) { `` | `` if (sel && (partidas \|\| []).some((p) => p.ide === sel)) { `` | MUERTO | 6 | test_f049_c_partida_de_la_lista_se_marca_sin_opcion_extra |
| A04 | `app.js:1685` | `` ops.push(`<option value="${sel}" selected>` + `` | `` ops.push(`<option value="${sel}">` + `` | MUERTO | 4 | test_f049_c_partida_fuera_de_la_lista_se_ensena_igual |
| A05 | `app.js:1686` | `` `${escapeHtml(cod \|\| `partida ${sel}`)} · (no está en la lista) `` | `` `${escapeHtml(cod \|\| "")} · (no está en la lista) `` | MUERTO | 1 | test_f049_c_fuera_de_la_lista_sin_codigo |
| A06 | `app.js:1686` | `` `${escapeHtml(cod \|\| `partida ${sel}`)} · (no está en la lista) `` | `` `${cod \|\| `partida ${sel}`} · (no está en la lista) `` | MUERTO | 1 | test_f049_c_el_codigo_se_escapa |
| A07 | `app.js:1700` | `` { method: "POST", body: JSON.stringify({ overrides: registro.overrides, ⏎         trabajador_ide: registro.trabajadorIde }) }); `` | `` { method: "POST", body: JSON.stringify({ overrides: {}, ⏎         trabajador_ide: registro.trabajadorIde }) }); `` | MUERTO | 3 | test_f049_a_repreflight_manda_las_elegidas_y_el_trabajador |
| A08 | `app.js:1701` | `` { method: "POST", body: JSON.stringify({ overrides: registro.overrides, ⏎         trabajador_ide: registro.trabajadorIde }) }); `` | `` { method: "POST", body: JSON.stringify({ overrides: registro.overrides, ⏎         trabajador_ide: null }) }); `` | MUERTO | 4 | test_f049_a_repreflight_manda_las_elegidas_y_el_trabajador |
| A09 | `app.js:1707` | ``   registro.overrides = {}; ⏎   registro.trabajadorIde = trabajadorIde; `` | ``   registro.trabajadorIde = trabajadorIde; `` | MUERTO | 2 | test_f049_b_abrir_desde_un_boton_empieza_sin_partidas_elegidas |
| A10 | `app.js:1709` | `` const seq = ++registro.seq; ⏎   const btn = $("#btn-registro"); `` | `` const seq = registro.seq; ⏎   const btn = $("#btn-registro"); `` | MUERTO | 2 | test_f049_b_abrir_de_nuevo_descarta_un_repreflight_en_vuelo |
| A11 | `app.js:1714` | ``     if (seq !== registro.seq) return; ⏎     registro.pisar = new Set(); `` | ``     registro.pisar = new Set(); `` | MUERTO | 1 | test_f049_b_una_apertura_vieja_no_pinta_encima_de_otra |
| A12 | `app.js:1715` | ``     registro.pisar = new Set(); ⏎     pintarModalPreflight(pf); `` | ``     pintarModalPreflight(pf); `` | MUERTO | 1 | test_f049_b_abrir_desde_un_boton_empieza_sin_partidas_elegidas |
| A13 | `app.js:1727` | `` const seq = ++registro.seq; ⏎   const btn = $("#btn-ejecutar-registro"); `` | `` const seq = registro.seq; ⏎   const btn = $("#btn-ejecutar-registro"); `` | MUERTO | 2 | test_f049_a_solo_pinta_la_ultima_peticion |
| A14 | `app.js:1729` | ``   if (btn) { btn.disabled = true; btn.textContent = "Analizando…"; } `` | _(vacío)_ | MUERTO | 3 | test_f049_a_registrar_bloqueado_mientras_se_analiza |
| A15 | `app.js:1732` | ``     if (seq !== registro.seq) return; ⏎     if ($("#modal-registro") `` | ``     if ($("#modal-registro") `` | MUERTO | 2 | test_f049_a_solo_pinta_la_ultima_peticion |
| A16 | `app.js:1733` | ``     if ($("#modal-registro").classList.contains("oculto")) return; ⏎     registro.pisar `` | ``     registro.pisar `` | MUERTO | 1 | test_f049_a_modal_cerrado_no_se_reabre |
| A17 | `app.js:1734-1735` | `` registro.pisar = new Set([...document.querySelectorAll(".chk-pisar:checked")] ⏎       .map((c) => c.value)); `` | `` registro.pisar = new Set(); `` | MUERTO | 1 | test_f049_a_conserva_las_casillas_marcadas_por_su_clave |
| A18 | `app.js:1734` | `` new Set([...document.querySelectorAll(".chk-pisar:checked")] ⏎       .map `` | `` new Set([...document.querySelectorAll(".chk-pisar")] ⏎       .map `` | MUERTO | 1 | test_f049_a_conserva_las_casillas_marcadas_por_su_clave |
| A19 | `app.js:1738` | ``     if (seq !== registro.seq) return; ⏎     toast(err.message, true); `` | ``     toast(err.message, true); `` | MUERTO | 1 | test_f049_a_el_error_de_una_peticion_vieja_no_desbloquea |
| A20 | `app.js:1739` | ``     toast(err.message, true); ⏎     if (btn) { btn.disabled = false; `` | ``     if (btn) { btn.disabled = false; `` | MUERTO | 1 | test_f049_a_error_avisa_y_devuelve_el_boton |
| A21 | `app.js:1740` | ``     if (btn) { btn.disabled = false; btn.textContent = "Registrar"; } `` | _(vacío)_ | MUERTO | 1 | test_f049_a_error_avisa_y_devuelve_el_boton |
| A22 | `app.js:1818` | `` ${opcionesPartida(partidas, a.paride, a.partida_cod)} `` | `` ${opcionesPartida(partidas, a.paride)} `` | MUERTO | 2 | test_f049_c_el_modal_pinta_la_partida_de_la_accion |
| A23 | `app.js:1837` | `` `${registro.pisar.has(c.clave) ? " checked" : ""}> ` + `` | `` `> ` + `` | MUERTO | 1 | test_f049_a_las_casillas_de_registro_pisar_salen_marcadas |
| A24 | `app.js:1837` | `` `${registro.pisar.has(c.clave) ? " checked" : ""}> ` + `` | `` `${registro.pisar.has(c.clave) ? "" : " checked"}> ` + `` | MUERTO | 3 | test_f049_a_las_casillas_de_registro_pisar_salen_marcadas |
| A25 | `app.js:1849` | ``       repreflightPartida(); ⏎     }); `` | ``     }); `` | MUERTO | 3 | test_f049_a_cambiar_la_partida_la_apunta_y_repite_el_preflight |
| A26 | `app.js:1848-1849` | `` registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) \|\| 0; ⏎       repreflightPartida(); `` | `` repreflightPartida(); `` | MUERTO | 3 | test_f049_a_cambiar_la_partida_la_apunta_y_repite_el_preflight |
| A27 | `app.js:1848-1849` | `` registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) \|\| 0; ⏎       repreflightPartida(); `` | `` repreflightPartida(); ⏎       registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) \|\| 0; `` | MUERTO | 2 | test_f049_a_el_preflight_repetido_lleva_la_partida_recien_elegida |
| A28 | `app.js:1848-1849` | `` registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) \|\| 0; ⏎       repreflightPartida(); `` | `` registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) \|\| 0; ⏎       repreflightPartida(); repreflightPartida(); `` | MUERTO | 3 | test_f049_a_cambiar_la_partida_la_apunta_y_repite_el_preflight |
| C01 | `styles.css:509-510` | `` .modal .aviso { color: var(--warn); font-size: .76rem; ⏎   white-space: normal; overflow-wrap: anywhere; } `` | `` .modal .aviso { color: var(--warn); font-size: .76rem; } `` | MUERTO | 1 | test_f049_e_el_aviso_amarillo_ajusta_el_texto |
| C02 | `styles.css:511` | `` .modal .conflicto .check { display: block; white-space: normal; `` | `` .modal .conflicto .check { display: block; `` | MUERTO | 1 | test_f049_e_el_texto_de_la_casilla_no_se_sale_del_recuadro |
| C03 | `styles.css:511` | `` .modal .conflicto .check { display: block; white-space: normal; `` | `` .modal .conflicto .check { white-space: normal; `` | MUERTO | 1 | test_f049_e_el_texto_de_la_casilla_no_se_sale_del_recuadro |
| C04 | `styles.css:511-512` | `` .modal .conflicto .check { display: block; white-space: normal; ⏎   overflow-wrap: anywhere; } `` | `` .modal .conflicto .check { display: block; white-space: normal; } `` | MUERTO | 1 | test_f049_e_el_texto_de_la_casilla_no_se_sale_del_recuadro |

Los CSS (C01-C04) solo los caza la comprobación estática de la regla: el
efecto visual lo comprobó el implementer con Chrome headless (antes /
después, `progress/impl_F-049.md`, decisión 2) y lo verifica el humano en
la MANUAL (paso 8).

### Script de la ampliación

Guardarlo **fuera del repo** y lanzarlo desde la raíz:
`PYTHONIOENCODING=utf-8 python <ruta>/mutacion_manual_f049_ampliacion.py`
(con ids como argumentos, solo esos mutantes).

```python
# Campaña manual de mutantes de la ampliación de F-049 (app.js y styles.css).
# Uso, desde la raíz del repo: PYTHONIOENCODING=utf-8 python <ruta>/mutacion_manual_f049_ampliacion.py
import subprocess, sys, time
from pathlib import Path
SERV = Path.cwd() / "services" / "dedicacion-front"
APP = SERV / "static" / "js" / "app.js"
CSS = SERV / "static" / "css" / "styles.css"
PY = SERV / ".venv" / "Scripts" / "python.exe"
TESTS = ["tests/test_f049_ampliacion_registro.py", "tests/test_f049_avisos_registro.py",
         "tests/test_f039_partida_fija.py"]
ORIG = {APP: APP.read_bytes(), CSS: CSS.read_bytes()}
J, C = APP, CSS
M = [
 ("A01", J, 'if (sel && !(partidas || []).some((p) => p.ide === sel)) {', 'if (false) {'),
 ("A02", J, 'if (sel && !(partidas || []).some((p) => p.ide === sel)) {', 'if (!(partidas || []).some((p) => p.ide === sel)) {'),
 ("A03", J, 'if (sel && !(partidas || []).some((p) => p.ide === sel)) {', 'if (sel && (partidas || []).some((p) => p.ide === sel)) {'),
 ("A04", J, 'ops.push(`<option value="${sel}" selected>` +', 'ops.push(`<option value="${sel}">` +'),
 ("A05", J, '`${escapeHtml(cod || `partida ${sel}`)} · (no está en la lista)', '`${escapeHtml(cod || "")} · (no está en la lista)'),
 ("A06", J, '`${escapeHtml(cod || `partida ${sel}`)} · (no está en la lista)', '`${cod || `partida ${sel}`} · (no está en la lista)'),
 ("A07", J, '{ method: "POST", body: JSON.stringify({ overrides: registro.overrides,\n        trabajador_ide: registro.trabajadorIde }) });', '{ method: "POST", body: JSON.stringify({ overrides: {},\n        trabajador_ide: registro.trabajadorIde }) });'),
 ("A08", J, '{ method: "POST", body: JSON.stringify({ overrides: registro.overrides,\n        trabajador_ide: registro.trabajadorIde }) });', '{ method: "POST", body: JSON.stringify({ overrides: registro.overrides,\n        trabajador_ide: null }) });'),
 ("A09", J, '  registro.overrides = {};\n  registro.trabajadorIde = trabajadorIde;', '  registro.trabajadorIde = trabajadorIde;'),
 ("A10", J, 'const seq = ++registro.seq;\n  const btn = $("#btn-registro");', 'const seq = registro.seq;\n  const btn = $("#btn-registro");'),
 ("A11", J, '    if (seq !== registro.seq) return;\n    registro.pisar = new Set();', '    registro.pisar = new Set();'),
 ("A12", J, '    registro.pisar = new Set();\n    pintarModalPreflight(pf);', '    pintarModalPreflight(pf);'),
 ("A13", J, 'const seq = ++registro.seq;\n  const btn = $("#btn-ejecutar-registro");', 'const seq = registro.seq;\n  const btn = $("#btn-ejecutar-registro");'),
 ("A14", J, '  if (btn) { btn.disabled = true; btn.textContent = "Analizando…"; }', ''),
 ("A15", J, '    if (seq !== registro.seq) return;\n    if ($("#modal-registro")', '    if ($("#modal-registro")'),
 ("A16", J, '    if ($("#modal-registro").classList.contains("oculto")) return;\n    registro.pisar', '    registro.pisar'),
 ("A17", J, 'registro.pisar = new Set([...document.querySelectorAll(".chk-pisar:checked")]\n      .map((c) => c.value));', 'registro.pisar = new Set();'),
 ("A18", J, 'new Set([...document.querySelectorAll(".chk-pisar:checked")]\n      .map', 'new Set([...document.querySelectorAll(".chk-pisar")]\n      .map'),
 ("A19", J, '    if (seq !== registro.seq) return;\n    toast(err.message, true);', '    toast(err.message, true);'),
 ("A20", J, '    toast(err.message, true);\n    if (btn) { btn.disabled = false;', '    if (btn) { btn.disabled = false;'),
 ("A21", J, '    if (btn) { btn.disabled = false; btn.textContent = "Registrar"; }', ''),
 ("A22", J, '${opcionesPartida(partidas, a.paride, a.partida_cod)}', '${opcionesPartida(partidas, a.paride)}'),
 ("A23", J, '`${registro.pisar.has(c.clave) ? " checked" : ""}> ` +', '`> ` +'),
 ("A24", J, '`${registro.pisar.has(c.clave) ? " checked" : ""}> ` +', '`${registro.pisar.has(c.clave) ? "" : " checked"}> ` +'),
 ("A25", J, '      repreflightPartida();\n    });', '    });'),
 ("A26", J, 'registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) || 0;\n      repreflightPartida();', 'repreflightPartida();'),
 ("A27", J, 'registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) || 0;\n      repreflightPartida();', 'repreflightPartida();\n      registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) || 0;'),
 ("A28", J, 'registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) || 0;\n      repreflightPartida();', 'registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) || 0;\n      repreflightPartida(); repreflightPartida();'),
 ("C01", C, '.modal .aviso { color: var(--warn); font-size: .76rem;\n  white-space: normal; overflow-wrap: anywhere; }', '.modal .aviso { color: var(--warn); font-size: .76rem; }'),
 ("C02", C, '.modal .conflicto .check { display: block; white-space: normal;', '.modal .conflicto .check { display: block;'),
 ("C03", C, '.modal .conflicto .check { display: block; white-space: normal;', '.modal .conflicto .check { white-space: normal;'),
 ("C04", C, '.modal .conflicto .check { display: block; white-space: normal;\n  overflow-wrap: anywhere; }', '.modal .conflicto .check { display: block; white-space: normal; }'),
]
solo = set(sys.argv[1:])
res = []
t0 = time.time()
try:
    for mid, f, a, b in M:
        if solo and mid not in solo:
            continue
        txt = ORIG[f].decode("utf-8")
        n = txt.count(a)
        if n != 1:
            res.append((mid, "NO_APLICA(%d)" % n, 0, "")); continue
        f.write_bytes(txt.replace(a, b).encode("utf-8"))
        try:
            r = subprocess.run([str(PY), "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider"],
                               cwd=SERV, capture_output=True, text=True, encoding="utf-8")
        finally:
            f.write_bytes(ORIG[f])
        failed = [l.split("::")[1].split(" ")[0] for l in r.stdout.splitlines() if l.startswith("FAILED")]
        res.append((mid, "MUERTO" if r.returncode else "VIVO", len(failed), failed[0] if failed else ""))
        print(res[-1], flush=True)
finally:
    for f, b in ORIG.items():
        f.write_bytes(b)
print("total %.0f s" % (time.time() - t0))
```
