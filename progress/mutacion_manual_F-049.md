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
