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

## T19 · pendiente (humano, modo pruebas)
