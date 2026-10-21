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

## Segunda mitad: cambio de días (R49)

Pendiente, tras T37 (opción C de R30): mismos dos `ide` con `fec` 6 y 12.
