<!-- progress/manual_F-044.md -->
# F-044 · T21: verificación MANUAL en modo pruebas (0404)

Ejecutada por el **líder a petición expresa del humano** (2026-10-26, «haz
tu la prueba»), en local y en **modo pruebas**: toda escritura a la obra
`0404`, marcada `PRUEBA-PORC`. Código: commit `e223d22` de la rama, sacado
en la copia principal con `git checkout --detach` (el worktree no tiene los
`.env` y no se copian); al acabar, la copia principal volvió a `dev`.

**Modo comprobado antes de cada escritura** (guion corregido en la review 1,
B1): (a) `GET :8006/health` ⇒ `"modo_pruebas":true,"obra_pruebas":"0404",
"database":"ruesma"`; (b) `transfer_base_url` de la api ⇒
`http://127.0.0.1:8006` (comprobado tras la review, con los mismos `.env`
de la copia principal, sin cambios entre medias); (c) el modal dice «MODO
PRUEBAS: se escribirá en la obra 0404» y el preflight trae
`forzada_pruebas: true`; y `get_settings` del transfer ⇒ `True 0404`.

## Preparación

- `POST /api/v1/sync` (lee Sigrid, escribe solo la base local): log `sync
  vinculados: 469 vinculados, 18 sin campo, 9 hacia un no trabajador, 60 de
  un tipo excluido`; `recurso_vinculado` 496 altas. Activos por tipo: TF 181,
  CAJA 115, CO 102, VE 53, VIAJE 18.
- Trabajador de prueba: **1972126** (encargado), con TF0207, CO0070 y VE0032.
  Noviembre 2026: **0722 al 60 %** y **Postv-0646 al 40 %**.

## Resultado

| Paso | Esperado | Resultado |
|---|---|---|
| Cuadrante (api y front) | Columna «Tipo recurso» y una subfila por vinculado bajo cada línea, con su partida | CUMPLE. 0722: TF `CI.4.13` y CO `CI.4.1` («CI del tipo»), VE `CI.03P.9`; Postv-0646: los tres con la del trabajador («la del trabajador») |
| Cambiar la partida del vehículo en su subfila | Queda elegida | CUMPLE: `PUT …/partida` con `vinculado_ide` ⇒ VE de la 0722 con `CI.4.4` elegida, el resto igual |
| Preflight 60/40 | Los tres vinculados en cada línea, con el % del trabajador sobre su `pre` | CUMPLE. 0722: `MENC` 0,6 · `OTEL` 24 € `CI.4.13` · `OGAS` 168 € `CI.4.1` · `MESVE` 240 € `CI.4.4` (manual). Postv: 0,4 · 16 / 112 / 160 € con la partida `0646` del titular. Parte PT26/00371 (0404) |
| Ejecutar | 8 líneas nuevas | CUMPLE: `hmores.ide` 412123-412130; las de vinculados con su `reside` propio y `synckey porcentajes:vin:{registro}:{recurso}` |
| `estado --ano 2026 --mes 11` | Las 8, `PRUEBA-PORC` | CUMPLE: 8 líneas, 6 en «Líneas de vinculados (porcentajes:vin:)» |
| Registrar otra vez | Todo «ya registrada» | CUMPLE: titular y vinculados `ya_registrado` (misma línea), nada que escribir |
| Cambiar a 70/30 y registrar | Pide confirmar el pisado de cada línea propia (F-051) y **edita** | CUMPLE: conflictos por línea para titular y vinculados (más `sobrecarga`, artefacto del modo pruebas: las dos obras van al mismo parte); con las claves confirmadas, `editadas` con su `antes`, **las mismas `ide`** 412123-412130; `estado` ⇒ 8 líneas a 0,3 / 0,7, ningún `DELETE` |
| Modal de registro (navegador) | Vinculados bajo el trabajador | CUMPLE: filas «↳ CONSUMOS TELEFONO MOVIL TF0207 · Postventa · ya_registrado · 30 % · OTEL…», igual gasoil y vehículo, en las dos obras |
| Limpieza | `limpiar` en seco y `--confirmar` | CUMPLE: lista exactamente las 8, borradas; `estado` ⇒ 0 líneas. Fila local del trabajador vaciada (solo PostgreSQL local) |

## Líneas en Sigrid, completas (para Administración; O2 de la review)

Tras el primer `ejecutar` (60/40), salida de `estado --ano 2026 --mes 11`
(parte PT26/00371, `hmoide` 2854393, 0404):

```
{"ide": 412123, "reside": 1972126, "fec": 20261130, "hora": "MENC",  "paride": 360138, "can": 0.4, "pre": 6500.0, "tot": 2600.0, "synckey": "porcentajes:192"}
{"ide": 412124, "reside": 1975857, "fec": 20261130, "hora": "OTEL",  "paride": 360138, "can": 0.4, "pre": 40.0,   "tot": 16.0,   "synckey": "porcentajes:vin:192:1975857"}
{"ide": 412125, "reside": 1975883, "fec": 20261130, "hora": "OGAS",  "paride": 360138, "can": 0.4, "pre": 280.0,  "tot": 112.0,  "synckey": "porcentajes:vin:192:1975883"}
{"ide": 412126, "reside": 2271380, "fec": 20261130, "hora": "MESVE", "paride": 360138, "can": 0.4, "pre": 400.0,  "tot": 160.0,  "synckey": "porcentajes:vin:192:2271380"}
{"ide": 412127, "reside": 1972126, "fec": 20261130, "hora": "MENC",  "paride": 409236, "can": 0.6, "pre": 6500.0, "tot": 3900.0, "synckey": "porcentajes:193"}
{"ide": 412128, "reside": 1975857, "fec": 20261130, "hora": "OTEL",  "paride": 409303, "can": 0.6, "pre": 40.0,   "tot": 24.0,   "synckey": "porcentajes:vin:193:1975857"}
{"ide": 412129, "reside": 1975883, "fec": 20261130, "hora": "OGAS",  "paride": 409291, "can": 0.6, "pre": 280.0,  "tot": 168.0,  "synckey": "porcentajes:vin:193:1975883"}
{"ide": 412130, "reside": 2271380, "fec": 20261130, "hora": "MESVE", "paride": 409294, "can": 0.6, "pre": 400.0,  "tot": 240.0,  "synckey": "porcentajes:vin:193:2271380"}
```

Todas con `tex = "PRUEBA-PORC"`. `paride` 409303 = `CI.4.13`, 409291 =
`CI.4.1`, 409294 = `CI.4.4` (elegida), 409236 = `CI.1.3`, 360138 = `0646`
(postventa). Tras el 70/30: mismas `ide`, `can` 0,3/0,7 y `tot` 1950 / 12 /
84 / 120 y 4550 / 28 / 196 / 280; `synckey` con el `registro_id` nuevo
(195 y 194), porque guardar el cuadrante rehace las asignaciones.

## Lo que NO se ha probado (queda del humano)

- **Líneas ajenas hechas a mano** (guion de `tasks.md` T21: una `OTEL` con
  `can = 0` y una `OGAS` al 95 % en el parte de la 0404, creadas en Sigrid
  por una persona): el líder no puede crearlas (solo el transfer escribe y
  no crea líneas ajenas). Sin ellas no se ha visto editar la `OTEL` al 0 %
  ni confirmar el pisado de una `OGAS` **ajena**; sí el de líneas propias.
- **Validación de Administración** de importes, partidas y cuentas.

## Observaciones (no bloquean)

1. La respuesta de `POST /api/v1/sync` no trae el conteo de `vinculados`
   (el log sí: `vinculados=ResultadoSyncMaestro(recibidos=496, altas=496…)`).
   La spec no lo pide (R3 lo pone en el preview); el aviso del front tras
   «Sincronizar Sigrid» no lo enseñará.
2. El `resumen` de cada obra del preflight cuenta solo las líneas del
   titular (`escribir: 1` con tres vinculados a escribir).
