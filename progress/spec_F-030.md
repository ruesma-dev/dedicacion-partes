<!-- progress/spec_F-030.md -->
# F-030 · Informe del spec-author (2026-10-20)

Rama `feature/F-030-dias-bajas-incidencias`, copia
`C:\Users\pgris\PycharmProjects\porcentajes-f030`. Spec en
`specs/F-030-dias-bajas-incidencias/`: requirements (R1-R35, 150/150 líneas),
design (250/250), tasks (T1-T21; bloque A captura T1-T9, bloque B registro
T10-T18, docs T19, MANUAL T20, init T21). `python -m harness.tamano --feature
F-030`: dentro de los topes.

## Qué propone, en una línea por servicio

- **front**: en la celda del %, valor con al menos una letra ⇒ panel de F-042
  con las incidencias; con cifras, el código de hoy (R1, fijado por T1 antes
  de tocar nada). Chip «obra · letra · del/al» y subfila en la tabla.
- **api**: catálogo `tipo_incidencia` desde `auxhor` por el sync (como
  `empresa`, F-032), tabla nueva `incidencia` (por `create_all`; `asignacion`
  no cambia y su `CHECK porcentaje > 0` sigue), `PUT …/incidencias` con
  evento `INCIDENCIAS` y deshacer por tipo; no cuenta para el 100 %.
- **transfer**: cada incidencia = `CI*` el día desde + `CIZ` el día hasta,
  `can = 0`, `synckey porcentajes:inc:{id}:ini|fin`, en el parte del periodo
  de su obra; fuera de pisados, sobrecarga y sin partida; deduplica contra
  cualquier parte del mes (R27).

## Decisiones abiertas (requirements §7, alternativas en design §11)

D1 fuente (rec. `auxhor`), D2 fechas (rec. tramo obligatorio), D3 cruce de
mes (rec. cada mes con su `CIZ`), D4 100 % (rec. no cuenta), D5 qué se
escribe (rec. par `CI*`/`CIZ`), D6 partida (rec. la de la línea de % o 0), D7
duplicados (rec. cualquier obra del mes; solo obra normal), D8 alcance (rec.
todo en F-030; alternativa: partir tras T9), D9 línea recién añadida (rec. se
convierte en incidencia), D10 % por días, calendario de convenio y bandeja de
`partes` (rec. fuera).

## Exploración en Sigrid (solo lectura)

Script en el scratchpad de la sesión, ejecutado con el intérprete y desde
`porcentajes\services\dedicacion-transfer` (su `.env`, sin imprimirlo); solo
`POST /api/sql/read`, base `ruesma`, `SELECT` parametrizados. Consultas:

1. `auxhor WHERE cod LIKE 'CI%'`: 8 filas (7 incidencias + `CIZ`), la letra
   entre paréntesis en `res`, `numemp = 0`, `pre = 0`, `tipincnom = 0` en
   todas (ese campo no sirve para clasificar).
2. `reshor` × `auxhor`: 711 recursos con los 8 códigos; 451 de 658 mensuales;
   169 de 229 mensuales activos (`con.fecbaj = 0`). Los 60 restantes darán
   «el recurso no tiene el código» (R26).
3. `hmores` desde 2025 con `CI*`: casi todas sin `synckey` (Administración a
   mano); de mensuales, 784 `CIV`, 1.000 `CIZ`; con `synckey partes:`, 2.
4. Muestra 2026 de mensuales (solo `ide` internos, sin nombres): inicio y fin
   en el parte de la obra donde está su `M*`, partida la de esa línea o 0;
   un día = `CIV` y `CIZ` el mismo día; bajas largas repetidas el día 1 de
   cada mes con un único `CIZ` final.

Ni nombres, ni DNI, ni importes en la spec ni aquí. Nada escrito en Sigrid.

## Avisos para el líder

- `azure-apps/partes.md` lo mantiene `partes`: avisar al humano de que
  `porcentajes` escribiría `CI*`/`CIZ` en los mismos partes.
- El interruptor `MENSUALES_A_DEDICACION` de `partes` (su F-019) debe seguir
  apagado: nadie lee aún `dedicacion_bandeja` (D10).
- `bash harness/init.sh` en el worktree (2026-10-20): pytest 418 passed, 1
  skipped; tamaño 150/150 y 250/250; cobertura N/A (sin código). Un único
  `[KO]`, el conocido: `services/dedicacion-api/.venv` no existe en el
  worktree (`harness/servicios.json`). No se ha tocado.
