<!-- progress/manual_F-074.md -->
# F-074 · Verificaciones MANUAL

## T18 · Producción (2026-11-24): CUMPLE, tras sincronizar

Hecha por el **líder** a petición del humano («miralo tu en produccion»), en
el navegador con la sesión del humano y con lecturas de Azure (revisiones y
Log Analytics). Nada escribe en Sigrid; no se abrió el modal de registro.

**Hallazgo: faltaba «Sincronizar Sigrid».** El despliegue se hizo api
(`r20261124-1616`, 15:16 UTC) → transfer (`r20261124-1636`) → front
(`r20261124-1637`), pero el último `POST /api/v1/sync` de los logs de Azure
era del 2026-11-10: tras la api nueva nadie había sincronizado. Efecto
comprobado en el cuadrante de octubre (CERRADO): las 52 líneas de postventa
salían sin partida ni motivo («—»), porque `obra.postventa_partida_*` estaba
vacía (`estado_partida.py`: «sync pendiente, ninguna marca»). Con el
transfer nuevo, esa postventa **no se habría registrado**.

**Sincronización.** Con el OK expreso del humano (2026-11-24, «Sí, sincroniza
tú»), el líder pulsó «Sincronizar Sigrid» en producción: «Sigrid OK (18.89s):
250 empleados (+2/-0), 295 obras (+2/-0)». Lee de Sigrid y actualiza los
maestros de `dedicacion`; no escribe en Sigrid.

**Resultado tras sincronizar** (`GET …/cuadrante` desde la sesión):

| Qué se mira | Resultado |
|---|---|
| `app.js` servido | el del front nuevo |
| Noviembre (ABIERTO): ninguna «automática» | 0 «automática»; 8 líneas pasaron de «buscando partida…» a «no encuentra partida» en ~25 s, con el motivo en el `title` de la celda (D6 b) |
| Octubre (CERRADO): postventa con su partida | 52 de 52 líneas de postventa con la partida de su obra (método `postventa`, p. ej. `0594 · VIV. CASARES`); 0 sin nada, 0 no encontradas |
| Noviembre: postventa | aún no hay líneas de postventa en el mes |

**Pendientes del humano:** T15-T17 (local), sin cambios.
