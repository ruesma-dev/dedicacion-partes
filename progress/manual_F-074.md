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

T15-T17 (local): hechas por el líder el 2026-11-25, abajo.

## T15-T17 · Local (2026-11-25): CUMPLEN

Hechas por el **líder** a petición del humano («puedes hacer tu las
verificaciones?»), sobre `dev` (`d00e266`, con F-074 unida) y con
`bash harness/init.sh` en verde antes de empezar. Los tres servicios en local:
transfer con `OBRA_PRUEBAS_FORZAR=true` (`/health`: `modo_pruebas: true`,
obra `0404`), api con `PG_HOST=localhost` y `TRANSFER_BASE_URL` al transfer
local, front contra la api local; parados al terminar. Nada escribe en Sigrid:
el log del transfer registra 4 `POST /api/registro/preflight-lote` y 0
`ejecutar`; en octubre ninguna línea de la base local tiene estado de Sigrid.

### T15 (M1) · Octubre de 2026, ABIERTO en la base local: CUMPLE

- «Sincronizar Sigrid» (lee de Sigrid y actualiza la base local). Abrió el
  modal «Porcentajes en Sigrid · 10/2026» (427 líneas leídas en los partes):
  se cerró con «Cerrar», sin importar nada.
- Tras la cola: 0 «automática», 0 «buscando partida…», 7 «no encuentra
  partida», todas subfilas de recursos vinculados en la 0654, con el motivo
  en el `title` («varias partidas del presupuesto tienen la cuenta de su tipo
  y ni el historial, ni el nombre ni el capítulo CI.4 deciden»).
- «⇪ Sigrid» de ALVAREZ SEGUIDO, ROBERTO (postventa 0626 al 50 % y obra 0726
  al 50 %): el preflight escribe lo que enseña cada celda: en la 0626, la
  partida `0626` «obra de postventa» (vinculados: «la del trabajador»); en la
  0726, `CI.01.03` «casada por categoría» (vinculados: «CI del tipo»); el
  vinculado sin importe del mes, «omitir». **Cancelar**.
- «⇪ Sigrid» de ALMAGRO MOLINA, MIGUEL (0654 al 100 %): el titular con
  `CI1.01.02` «casada por categoría»; los tres vinculados sin partida salen
  listados como «Sin partida», cada uno con su casilla de escribirlo sin
  partida; ninguno como automática. **Cancelar**.

### T16 (M2) · Medición, solo lectura: CUMPLE

`prueba_escritura_porcentajes.py medir --ano 2026 --mes 10 --obra 0694 --obra
0696 --recurso 2666958 --lote` con el transfer en modo pruebas. «Antes»: el
código del transfer de `c44bf60` (el `dev` previo al merge de F-074, sacado
con `git archive` a la carpeta temporal, ejecutado desde la carpeta del
transfer para leer su configuración); «después»: `dev`.

| | Lecturas | Segundos leyendo | Segundos en total |
|---|---|---|---|
| Antes (`c44bf60`) | 11 | 16,93 | 8,17 |
| Después (`dev`, F-074) | 8 | 9,53 | 5,27 |

Desaparecen `capitulos_de_obra` × 2 (presupuesto de cada obra, 992 y 3.037
filas) e `historial_partidas` (11 filas): las N + 1 del design §8 para un lote
de 2 obras sin partida definida. Sigue `cuentas_de_centro` (1 lectura, también
antes): es la cuenta analítica del centro del parte (F-037 R4), no las cuentas
del presupuesto de R6. Antes, cada obra salía con la partida del último parte
(`384152` y `376826`, «ultimo_parte»); después, sin partida (`paride=0`, «sin
partida … no se escribe sin confirmar»), como pide F-074.

### T17 (M3) · Base `dedicacion` LOCAL: CUMPLE

- Línea 126 (ALMAGRO MOLINA, MIGUEL, 0654 al 100 %), guardada
  `325705 · CI1.01.02 · JEFE DE OBRA · auto_categoria`. `UPDATE asignacion SET
  propuesta_ide = 1 WHERE id = 126` (sin `psql` en la máquina: con SQLAlchemy y
  la configuración de la api, comprobando que `PG_HOST` es local).
- Preflight: la línea sale «omitir» nombrando la partida («la partida
  CI1.01.02 propuesta no es una partida hoja activa del presupuesto de la obra
  0654: no se escribe; elige otra partida»), con el selector; sus vinculados,
  omitidos con el mismo motivo. **Cancelar**.
- Recarga: la celda pasa a «buscando partida…» a los 0,3 s y a
  `CI1.01.02 · JEFE DE OBRA · casada por categoría` a los 10,4 s (la nueva).
- Sin preflight, la guardada no se toca al recargar (F-055 D8, design §9): se
  vio en una segunda vuelta, que se cerró con su preflight.
- Al terminar, la línea 126 quedó igual que al principio (`325705`,
  `CI1.01.02`, `auto_categoria`), recalculada por la cola.
