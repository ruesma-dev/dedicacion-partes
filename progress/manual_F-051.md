<!-- progress/manual_F-051.md -->
# F-051 · Verificación MANUAL (T15) · CUMPLIDA (líder, 2026-10-21)

**T15 EJECUTADA por el líder el 2026-10-21, a petición del humano
(«realiza tu las pruebas»; escrituras autorizadas: «escribe en prueba para
51»). Resultado: CUMPLIDA.** Modo pruebas comprobado antes de escribir
(`OBRA_PRUEBAS_FORZAR=True`, obra `0404`, marca `PRUEBA-PORC`, base
`ruesma`). Transfer, api y front locales con el código de la rama (HEAD
`33f6db1`; cwd en la copia principal para su `.env`, sin leerlo). Sin
navegador (extensión no conectada): las llamadas, por el proxy del front
local (`localhost:8080/api/v1/...`), las mismas que hace la pantalla; el
texto del modal, con `rotuloConflicto` real de `app.js` en node sobre el
conflicto real.
1. Limpieza previa: `limpiar --confirmar` borró `porcentajes:148/149`
   (PT26/00344) y `porcentajes:180` (PT26/00371): PT26/00371 vacío.
2. Preparación: dos líneas `MADM` a `can` 0, `synckey` vacía, en PT26/00371
   con `stmt_insert_linea` del transfer: `ide` 411587 (recurso 1705036,
   `pos` 1) y 411588 (recurso 2786385, `pos` 2).
3. Cuadrante local 11/2026, GONZALEZ PANIAGUA 100 % en la 0694. Preflight:
   acción `escribir` sin conflicto, aviso «se edita la línea 411587 al 0 %
   del parte PT26/00371 (MADM, partida CI.1.5) en vez de añadir otra».
   `ejecutar`: `editada: true`, `hmores_ide` 411587, `borradas` 0; `estado`:
   **misma línea 411587, `pos` 1**, `can` 1.0, partida 384155,
   `PRUEBA-PORC`, `porcentajes:186`; la 411588 sigue a 0; ninguna línea nueva.
4. Reparto 60 % 0694 + 40 % 0672. Preflight: 0694 pisado con `edita_ide`
   411587; el modal diría «MADM de GONZALEZ PANIAGUA, … en el parte
   PT26/00371: se edita la línea 411587 (MADM 100%, fec 20261130) y se
   escribe 60%». 0672: sobrecarga (artefacto del modo pruebas: las dos
   obras caen en la 0404 y el 40 % se suma al 100 % aún sin pisar);
   confirmados los dos. `ejecutar`: 411587 editada en su sitio a 0.6 con
   `porcentajes:187` (`pos` 1); la 0672, línea nueva 411595 al 0.4; `borradas`
   0.
5. Tercera vez: preflight con `hmores_ide` 411587 y 411595 (los guardó la
   api) ⇒ las dos «ya registrada»; `ejecutar`: nada escrito ni editado,
   `ya_registradas_ide` {187: 411587, 188: 411595}.
6. Log del transfer: 2 `UPDATE hmores`, 1 `INSERT INTO hmores`, **0
   `DELETE`**; trazas «[registro] edita ide=411587 … antes=… despues=…».
7. Limpieza final: `limpiar --confirmar` (411587 y 411595) y borrado guardado
   de la 411588 (comprobado antes: parte, recurso, `can` 0, sin `synckey`,
   marca): PT26/00371 vacío. Cuadrante local de la trabajadora devuelto a
   vacío; servicios parados.
Observación (anterior a F-051, no bloquea): en modo pruebas la línea de la
0672 se escribió en la 0404 con la partida de la obra de origen (`paride`
351515); es el comportamiento de siempre del modo pruebas.
