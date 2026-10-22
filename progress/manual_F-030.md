<!-- progress/manual_F-030.md -->
# F-030 · T20 (MANUAL en la 0404) · resultado real

## Primera mitad: alta del par (2026-10-21, el líder)

Autorización del humano: «autorizo pruebas de f30». Transfer LOCAL con el
código de la rama (HEAD `90d83eb`), lanzado desde
`porcentajes/services/dedicacion-transfer` (su `.env`, modo pruebas,
`OBRA_PRUEBAS_FORZAR=true`); `RECURSO` 1705036, octubre de 2026.

- `preflight … --incidencia 1705036:CIV:5:9`: obra destino `0404`
  (pruebas), parte `PT26/00373`; `escribir` ini `CIV` 20261005 y fin `CIZ`
  20261009, `paride` 0, `pre` 0.
- `ejecutar --confirmar`: `hmores.ide` **411730** (`CIV`) y **411731**
  (`CIZ`).
- `verificar`: las dos con `reside` 1705036, `can` 0, `tot` 0 y sus
  `synckey` `porcentajes:inc:990101:ini|fin`; `estado`: `tex` `PRUEBA-PORC`.
- Segundo `ejecutar`: las dos `ya_registrado` («ya registrada en Sigrid
  (línea 41173x); no se duplica»), nada escrito.
- `limpiar` en seco: exactamente esas dos; `limpiar --confirmar`: borradas.
  El parte vuelve a sus 4 líneas (`PRUEBA-IA` de `partes`, no tocadas).

Queda probado contra Sigrid: el `INSERT` del par `CI*`/`CIZ`, la lectura de
las `CI*` del mes (R27/R33), la relectura por `synckey` y `limpiar`.

## Segunda mitad: cambio de días (R49, 2026-10-22, el líder)

Autorización del humano: «1 si» (2026-10-22). Transfer LOCAL con el código
de la rama (HEAD `97229a0`, con D16), mismo lanzamiento y `RECURSO` que la
primera mitad. Como la primera mitad se limpió, se repitió antes:

- `preflight`/`ejecutar --confirmar … --incidencia 1705036:CIV:5:9`: par
  escrito otra vez, `hmores.ide` **411828** (`CIV`, 20261005) y **411829**
  (`CIZ`, 20261009); `verificar`: `can` 0, `tot` 0, `synckey`
  `porcentajes:inc:990101:ini|fin`.
- `preflight … --incidencia 1705036:CIV:6:12`: dos `editar`, `fec` 20261006
  y 20261012, `fec_antes` 20261005 y 20261009, con sus `ide` 411828/411829.
- `ejecutar --confirmar … 1705036:CIV:6:12`: las dos `editar` con su
  `fec_antes`. `verificar`: **los mismos dos `ide`**, `fec` 20261006 (`CIV`)
  y 20261012 (`CIZ`), `can` 0.
- Otro `ejecutar`: las dos `ya_registrado` («ya registrada en Sigrid (línea
  41182x); no se duplica»), nada escrito.
- `limpiar` en seco: **exactamente 2** líneas `PRUEBA-PORC` (las dos de
  arriba, `fec` 6 y 12): ninguna línea nueva. `limpiar --confirmar`:
  borradas; el seco siguiente da 0 y `estado` enseña el parte `PT26/00373`
  con sus 4 líneas `PRUEBA-IA` de `partes`, no tocadas.

Queda probado contra Sigrid: el `UPDATE … SET fec` con su guarda (incluido
`AND fec = ?`, D16), `lineas_para_editar` sobre líneas `CI*`, la relectura
por `ide` y las columnas nuevas que lee (`can`, `hmoide`, `est`). Sin probar
contra Sigrid (solo tests): la rama `OR h.ide IN (…)`, R42 con día y una
`fec` movida a mano entre la relectura y el `UPDATE`.
