<!-- progress/manual_F-054.md -->
# F-054 · verificaciones MANUAL

## T18 (humano, local, solo lecturas en Sigrid)

### Paso 1 · HECHO el 2026-11-02

Transfer, api y front locales desde la copia `porcentajes-f054` (rama
`feature/F-054-sync-trae-porcentajes`), con el transfer en modo pruebas
(`/health`: `modo_pruebas` true, obra de pruebas `0404`, base `ruesma`).
Comando, en PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8006/api/porcentajes/existentes -ContentType 'application/json' -Body '{"empresa":1,"ano":2026,"mes":9,"obras":[]}'
```

Resultado: `ok` true, `lineas_leidas` 429 (353 `normal`, 72 `postventa`,
4 `var`), `excluidas_pruebas` 0, obras VAR y POSTV2 resueltas sin motivo.
La `MADM` de la 0694 (recurso 1705036, parte PT26/00319) sale con
`can` 0,95, partida `CI.1.5` y `destino = normal`. Cumple.

### Pasos 2 a 4 · pendientes (humano, sobre la ventana de T23-T26)

**R48 (T27), parte visual de T18 paso 2: comprobada por el humano el 2026-11-06** sobre `083076c`, tras dos retoques que pidió él mismo (cabecera fija en su sitio y no pegada al borde: «si hazlo asi»; franja de 1 px entre títulos y filtros) ⇒ «perfecto». Resto del paso 2 y pasos 3 y 4: **HECHOS el 2026-11-06 por el líder en el navegador**, a petición del humano («haz tu las pruebas en el navegador»), sobre `bee39c8`.

- **Entorno.** Transfer, api y front locales desde `porcentajes-f054`. `/health`: `modo_pruebas` true, obra `0404`, base `ruesma`. Cuadrante 01/2026.
- **Paso 2.**
  - **Ventana:** 389 líneas leídas, 284 filas (279 «solo en Sigrid», 3 `igual`, 2 «no se puede traer») y ninguna marcada.
  - **Filtro y Escape:** con `0696` en Obra quedan sus 20 filas y «Aceptar 0 marcadas». Escape vacía el filtro y la ventana sigue abierta.
  - **Marcado:** «Marcar las visibles» da «Aceptar 20 marcadas». Con el filtro en `0686`: «Aceptar 20 marcadas (20 ocultas por el filtro)». «Limpiar» deja los filtros vacíos, Estado en «Todos» y 20 marcadas. «Desmarcar todas» vuelve a «Aceptar 0 marcadas».
  - **Orden:** dos clics en Obra invierten el orden (0502…GG ↔ GG…0502).
  - **«No se traen (11)»:** 11 filas, cabecera Parte, Obra, Recurso, Líneas, Motivo; recurso como `MO/xxxx · nombre`; `PT26/00028 · POSTV2 · MO/0492` sale con ×2.
  - **Motivos por código, ninguno con números internos:**
    - «la obra 0708 no se ofrece normal»;
    - «la partida 0654-B de POSTV2 casa con varias obras (0654, 0654-B)»;
    - «partida VAR 28 fuera del universo VAR de VAR».
  - **Los dos «Limpiar»:** el de «No se traen» no toca el filtro de la principal.
  - **Aceptar una sola entrada:** se marca solo la 0709 al 40 % de MO/0306 RABADAN LOPEZ (que tiene también la 0706 y la 0712) y se acepta. En el cuadrante queda solo la 0709 al 40 %, con sus subfilas de vinculados; la 0706 y la 0712 no se tocan.
  - **«Deshacer» (O6):** devuelve la fila a «sin carga», y al volver a sincronizar la 0709 sale «solo en Sigrid», no «pisado».
- **Paso 3.** Se vuelve a aceptar y se abre el registro del trabajador: «ya_registrado», 40 %, MJG, «ya registrada en Sigrid (línea 376325); no se duplica», sin pisado ni sobrecarga, con el aviso de MODO PRUEBAS. **Cancelar**, no se registra.
  - No apareció ninguna omitida VAR o de postventa con partida no hoja, así que el texto de D21 en el preflight no se ha visto aquí. Lo cubren los tests de T26 y O11.
- **Paso 4.** Al sincronizar de nuevo, la 0709 de MO/0306 sale `igual` (40 % / 40 %).
- **Al terminar.** Se deshace la aceptación y el cuadrante local de 01/2026 queda como estaba.
- **Cumple.**

Ver `specs/F-054-sync-trae-porcentajes/tasks.md`, T18.

## T19 · HECHA el 2026-11-18 (líder, modo pruebas, a petición del humano)

Peticiones del humano: «hazlo tu», con mes de prueba «usa 2032», «escribe en la 404» y «crealo usando sigrid-api» para las líneas de partida.

- **Entorno.** Transfer y api locales desde `porcentajes-f054`. El `/health` del transfer da `modo_pruebas` true, obra de pruebas `0404` y base `ruesma`. Trabajador de prueba 1972126 (PEDROSA CORTES, JUAN), con TF0207 y CO0070 vinculados. Cuadrante local 01/2032: 0722 al 100 %, con partidas propuestas CI.1.3, CI.4.13 y CI.4.1.
- **Paso 0: alta del parte.** Un primer `registro/ejecutar` crea en la 0404 el parte **PT32/00001** (`hmo` 2874009, En registro). Escribe tres líneas `PRUEBA-PORC`: 414543 MENC 1, 414544 OTEL 1 y 414545 OGAS 1.
- **Paso 1: las líneas «manuales».** El humano no las crea a mano: pide crearlas «usando sigrid-api». Se insertan con el `stmt_insert_linea` del transfer, con `synckey` NULL y `tex` vacío, en una sola transacción. Antes se comprueba que el parte es el PT32/00001 de la 0404 y está En registro. Script en el scratchpad de la sesión, no versionado.
  - **415966**: 1972126, MENC, `can` 0,2, partida de la 0404 CI.1.5 (`paride` 94175), `pos` 256.
  - **415967**: TF0207, OTEL, `can` 0,2, partida CI.4.4 (`paride` 94227), `pos` 320.
- **Paso 2: preflight (solo lectura).** Las tres líneas propias salen `ya_registrado`. Las dos manuales salen como `sobrantes` confirmables, `cero:415966` y `cero:415967`, la segunda con `vinculado` TF0207.
- **Paso 3: registrar sin marcarlas.** `ejecutar` responde 200 con 0 escritas, 0 editadas, 0 a cero y 0 borradas. 415966 y 415967 siguen igual: 0,2 / 1300 € y 0,2 / 8 €. **Cumple.**
- **Paso 4: registrar marcándolas** (`sobrantes_a_cero` con las dos claves, como el front). `sobrantes_a_cero.puestas` trae las dos, con `antes` y `despues`: `can` y `tot` a 0, y `pre`, hora, partida, cuenta y fecha sin tocar. El `estado` lo confirma: **mismo `ide` y mismo `pos`** (415966/256 y 415967/320), con `can` y `tot` a 0. El log del transfer escribe dos `UPDATE hmores SET can = 0, tot = 0 …` y tiene **0 `DELETE`**. **Cumple** (R30, R37).
- **Tiempo del preflight.** Cuatro medidas: 13,01 s (en frío, el primero tras arrancar), 10,74 s, 10,12 s y 9,68 s. La mediana es **10,43 s**, por debajo del tope de 11,89 s (1,15 × 10,34 s de T10). **Cumple**, con la salvedad de que la primera medida en frío lo supera.
- **Qué queda en Sigrid.** En el parte PT32/00001 de la 0404 quedan las cinco líneas: las tres `PRUEBA-PORC` y las dos manuales, a 0. La limpieza no está hecha: es opcional y la decide el humano. El `limpiar` del script solo borra las marcadas; las dos manuales llevan `tex` vacío y no las borraría. En la BBDD local queda el periodo 01/2032.

Ver `specs/F-054-sync-trae-porcentajes/tasks.md`, T19.
