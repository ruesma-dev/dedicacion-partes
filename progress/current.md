<!-- progress/current.md -->
# Trabajo en curso

**F-008 · Infraestructura y despliegue en Azure**
Rama `feature/F-008-infra-azure` · `sdd: true` · rigor `critico` · prioridad 3
Estado: **arrancada el 2026-08-20. Spec en redacción.**

---

## ⚠ ACCIÓN PENDIENTE EN PRODUCCIÓN (Sigrid)

**Hay una fila de prueba viva en Sigrid**, escrita el 2026-08-20 en la
verificación T14 de F-002. El humano pidió **verla en la pantalla de partes
del ERP antes de borrarla**, y esa comprobación visual es la única que ningún
agente puede hacer.

| Qué | Dónde |
|---|---|
| Línea | `hmores.ide = **403039**`, `synckey = 'porcentajes:77'`, `tex = 'PRUEBA-PORC'` |
| Parte | `PT26/00296` (`hmo.ide = 2820419`), **creado por nosotros** |
| Obra | `0404 · CUBIERTA NAVE 14 - JOHN DEERE` (obra de pruebas) |
| Contenido | Álvarez Seguido, Rafael · `MCAP` · `can=0.5` · `pre=4500` · `tot=2250` · partida `CI.1.8` (`paride=94178`) · `fec=20260731` |

**Cómo borrarla cuando el humano dé el visto bueno:**

```bash
cd services/dedicacion-transfer
.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar --ano 2026 --mes 7
```

Ojo: ese comando borra **solo** lo marcado `PRUEBA-PORC` con `synckey`
`porcentajes:%`. La **cabecera** del parte `PT26/00296` quedaría creada y
vacía: hay que decidir si se borra también.

---

## Lo que demostró T14 (2026-08-20)

**La escritura en Sigrid funciona.** Es la primera vez que este sistema
escribe en el ERP; hasta ahora nunca lo había hecho (consulta C6). Evidencia
completa en `progress/sigrid_F-002.md`.

Queda demostrado: `sql/write` está habilitado contra `ruesma`; el `INSERT` en
`hmores` no rechaza los campos nunca confirmados (`ortide = 0`, `caaide = 0`);
la creación del parte (`con` + `hmo`) funciona; y el mapeo es correcto (fecha
al último día del mes, `can` sobre 1, `tot = can × pre` al céntimo).

**NO queda demostrado**: la imputación a partidas en producción (en modo
pruebas todo va a `0404` conservando la partida de la obra de origen, así que
solo la línea elegida era fiel), que Sigrid **muestre** bien la línea, ni el
camino de **conflicto y pisado** (`DELETE` + `INSERT`), porque había 0
conflictos.

## Estado de F-002 · `blocked`

Fases 1 y 2 aprobadas y en `dev`. **T13 y T14 ya ejecutadas.** Queda:

1. **T6.1** · avisar a Administración de las cuatro partidas duplicadas de
   POSTV2 (`656`, `664`, `680`, `693`, colgando de la raíz en vez de `CD`).
2. **T6.2** · decidir quién firma la procedencia de las reglas. Hoy dice
   `Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
   verificado contra Sigrid`. El test no clava el interlocutor.
3. **Regla nueva decidida por el humano el 2026-08-20**: una línea que
   **no casa partida** (`paride = 0`) ya no debe escribirse en silencio —
   tiene que **avisar y esperar confirmación**, igual que la sobrecarga del
   100 %. Hoy se escribe sin preguntar: lo vimos en el preflight de julio
   (Arriaza en la obra 0025, 2.132 € sin imputar). **Hay que implementarlo.**

## Lo que enseñó el preflight real de julio 2026 (T13)

13 obras, 25 acciones: **4 escribir, 21 omitir, 0 conflictos**. Las cuatro
líneas cuadraban al céntimo y una trabajadora sumaba **exactamente 1,0**
repartida entre tres obras.

De las 21 omisiones, **14 son por datos de Sigrid, no por nuestra lógica**:
10 recursos **sin código de hora mensual `M*`** y 4 empleados **sin recurso**
asociado. Es justo lo que ataca **F-011**. Otras 7 son líneas de postventa
cuyas obras (`0009`, `0285`, `0404`, `0700`) **no tienen partida en POSTV2**:
la regla las omite con motivo, pero esa dedicación no llega a Sigrid hasta
que Administración cree esas partidas.

## Backlog

- **F-001**, **F-003**, **F-009** · `done`.
- **F-002** · `blocked` (ver arriba).
- **F-008** · `in_progress` — esta.
- **F-004**, **F-005**, **F-006**, **F-011**, **F-012** · `pending`.
- **F-007** y **F-010** retiradas el 2026-08-20: se hacen en `arnes-base`.
  Su razonamiento está en `progress/history.md`.

## Hechos comprobados que no conviene volver a descubrir

- El sistema **corre entero en local**: transfer 8006 → api 8090 → front 8080,
  cada uno desde su carpeta con su venv. El api expone la salud en
  **`/api/v1/health`**, no en `/health`.
- `ruff` **no está instalado** en el venv de `dedicacion-api`: usar el
  intérprete de la raíz para lintar ese servicio.
- La fase `verificar` de `prueba_escritura_porcentajes.py` busca **sus
  propias** líneas de ejemplo (las de la plantilla `LINEAS_PRUEBA`, que nunca
  se editaron), no lo que escriba el sistema por su camino normal. Para
  comprobar una escritura real hay que leer por `synckey`.
