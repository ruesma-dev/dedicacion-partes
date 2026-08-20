<!-- progress/current.md -->
# Trabajo en curso

**F-008 · Infraestructura y despliegue en Azure**
Rama `feature/F-008-infra-azure` · `sdd: true` · rigor `critico` · prioridad 3
Estado: **spec APROBADA por el humano el 2026-08-20. Implementer lanzado con
las fases 1–6.** La fase 7 (crear recursos en Azure) es MANUAL del humano.

## Decisiones del humano sobre F-008 (2026-08-20)

| # | Decisión | Elegido |
|---|---|---|
| **D1** | dónde vive la BBDD `dedicacion` | **base propia en `psql-albaranes-rs9k2`**, como quinto inquilino, con las cuatro salvaguardas de `postventa-incidencias`: base y rol creados **una vez por una persona**, rol de aplicación propio (nunca el admin del servidor), **nada a nivel de servidor**, `PG_SSLMODE=require` |
| **D1b** | esquema | **`public`** dentro de nuestra base, como albaranes y partes |
| **D2** | exposición | **solo el front** con ingress externo; **api y transfer internos**. La api no tiene autenticación propia (`deps.py` se cree la cabecera `X-Usuario`), así que el ingress interno **es** su control de acceso |
| **D4** | réplicas | **`min-replicas 1`** en los tres: comportamiento predecible mientras se valida |

**Sin cerrar, y no bloquean el arranque:**

- **D3** · quién entra en el grupo `dedicacion-portal-users` (hace falta para
  Easy Auth, tarea manual T26).
- **D5** · pedir al proyecto `sigrid-api` una **function key de solo lectura**
  para la api: hoy api y transfer comparten la misma clave, y lo único que
  impide que la api escriba es que su código no tiene rutas de escritura, no
  la credencial.

---

## ⚠ FASE 7 de F-008 · MANUAL (humano) — lo que solo puedes hacer tú

Las fases 1–6 están **implementadas y APROBADAS** (`progress/review_F-008.md`).
Lo que queda **crea recursos, gasta dinero y toca la suscripción**: ningún
agente lo ejecuta. Detalle con el resultado esperado de cada paso en
`specs/F-008-infra-azure/tasks.md` fase 7 y en `infra/README_dedicacion.md`.

> **PRECONDICIÓN de toda la fase 7:** cerrar antes la comprobación pendiente
> de F-002 en Sigrid (fila `hmores.ide=403039`, parte `PT26/00296`, obra
> `0404`). Probar el registro desde Azure escribirá **más** líneas
> `PRUEBA-PORC` en la misma obra y mes, **indistinguibles de esa**.

**T24 · provisión base** (desde `infra/`, tras `. .\00_vars_dedicacion.ps1`):
`fase1_infra_dedicacion.ps1` → `crear_base_dedicacion.ps1` (crea la base en
`psql-albaranes-rs9k2`, decisión D1) → `add_secrets_dedicacion.ps1`.
Verificación: `az resource list -g rg-dedicacion-dev -o table` lista RG, MI,
Log Analytics, Key Vault y CAE, **y ninguna Storage Account**.

**T25 · imágenes y alta de los tres servicios, en orden**:
`build_images_dedicacion.ps1` → `create_transfer_dedicacion.ps1` →
`create_api_dedicacion.ps1` → `create_front_dedicacion.ps1`.

**T26 · Easy Auth**: `setup_front_easyauth.ps1`. **Necesita D3**, la lista de
personas del grupo `dedicacion-portal-users`, que sigue sin decidir.

**T27 · la verificación que de verdad importa**: que **solo el front** sea
externo, que el transfer siga con `OBRA_PRUEBAS_FORZAR=true`, que api y
transfer tengan **una réplica como máximo**, y que **todos los secretos** sean
referencias a Key Vault.

**T28–T31**: salud de los tres servicios; prueba funcional de extremo a
extremo **parando en `registro/preflight`, sin ejecutar**; pedir a
`front-portal` el alta del enlace; y refrescar `docs/INTEGRACION.md` y
`azure-apps/dedicacion.md` con los valores reales. **El commit en
`azure-apps` es del humano**: es otro repositorio.

> **Al pegar la salida real de los comandos `az` en `progress/`**: contiene
> identificadores de suscripción y objectId. El guardián de secretos se está
> ampliando para vigilar también ese directorio (§7.2 de la review). Usa
> marcadores (`<SUSCRIPCION>`, `<OBJECT-ID>`) en vez de los valores reales.

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
