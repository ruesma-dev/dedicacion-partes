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

**R48 (T27), parte visual de T18 paso 2: comprobada por el humano el 2026-11-06** sobre `083076c`, tras dos retoques que pidió él mismo (cabecera fija en su sitio y no pegada al borde: «si hazlo asi»; franja de 1 px entre títulos y filtros) ⇒ «perfecto». El resto del paso 2 y los pasos 3 y 4 siguen pendientes.

Ver `specs/F-054-sync-trae-porcentajes/tasks.md`, T18.

## T19 · pendiente (humano, modo pruebas)
