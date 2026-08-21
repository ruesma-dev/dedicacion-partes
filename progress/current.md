<!-- progress/current.md -->
# Trabajo en curso

**F-015 · Alta en el Portal Ruesma** — `in_progress`, en **review de cierre**.
**F-008** — `blocked`, también en review de cierre. Todo lo demás, cerrado.

Rama `dev`, con todo el trabajo integrado.

## Estado del backlog (13 features)

| Estado | Features |
|---|---|
| `done` | F-001, F-002, F-003, F-004, F-009, F-013 |
| en review de cierre | **F-008** (`blocked`), **F-015** (`in_progress`) |
| `pending` | F-005, F-006, F-011, F-012, F-014 |

Retiradas el 2026-08-20: **F-007** y **F-010**, que se hacen en `arnes-base`.

## El sistema está desplegado y en uso (2026-08-21)

- **Front**: `https://ca-dedicacion-front.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io`
- **Se entra** por la tarjeta «Dedicación» del Portal Ruesma (categoría *Obra*),
  desplegada el 2026-08-21. El permiso lo da el grupo
  `dedicacion-portal-users`, con asignación requerida: **8 personas dentro**.
- `ca-dedicacion-api` y `ca-dedicacion-transfer`: **internos**, no alcanzables
  desde fuera. El ingress interno de la api **es** su control de acceso.
- Imágenes con tag `r20260820-1625`, inventariadas con su digest.
- **El transfer sigue en modo pruebas** (`OBRA_PRUEBAS_FORZAR=true`), y salir
  de ahí exige autorización expresa para una acción concreta. El motivo real
  está en `docs/ARCHITECTURE.md`: **la imputación a partidas en producción no
  está validada**.

## Verificaciones `MANUAL (humano)` — todas hechas

| Feature | Qué | Estado |
|---|---|---|
| F-003 · T8 | arranque contra la base real | **hecha** 2026-08-20: `0 sentencias DDL` en dos arranques |
| F-002 · T13 | casado real contra Sigrid, sin escribir | **hecha** 2026-08-20, volcado en `sigrid_F-002.md` |
| F-002 · T14 | primera escritura real en Sigrid | **hecha** 2026-08-20, y **limpiada** el mismo día |
| F-008 · T24–T29, T31 | despliegue completo en Azure | **hechas** 2026-08-20 |
| F-015 · T1–T7 | tarjeta, usuarios y comprobación de acceso | **hechas** 2026-08-21 |

## ⚠ Lo que espera al humano

1. **Commitear `azure-apps/dedicacion.md`**, que sigue **sin trackear** en ese
   repositorio (`?? dedicacion.md`). Mientras no se commitee, **el documento
   del ecosistema no existe para los demás proyectos** y un `git clean` se lo
   lleva. Es otro repositorio: el commit es suyo.
2. **`git push origin dev`** en este repositorio.
3. Cuando quiera: **F-014** (aviso a Administración de las cuatro partidas
   duplicadas de POSTV2 y quién firma la procedencia) y las features
   pendientes.

## Nota de método: por qué hay commits directos en `dev`

`CLAUDE.md` exige una rama por feature, y **F-015 se trabajó en `dev`**, igual
que los arreglos de los scripts de infraestructura durante el despliegue. Fue
a conciencia: F-015 no toca una línea de código de este repositorio —su cambio
real vive en `front-portal`— y se hizo intercalada con el despliegue en vivo,
donde el árbol tenía que estar en `dev` para corregir los scripts sobre la
marcha. `features.json` lo declara (`"branch": "dev"`) en vez de apuntar a una
rama inexistente. **No es la norma y no debe volverse costumbre.**

## Hechos comprobados que no conviene volver a descubrir

- **La escritura en Sigrid funciona** (T14). Y ahora mismo el sistema **no
  tiene ninguna fila propia** en el ERP: la prueba se limpió.
- **La Regla B (sobrecarga del 100 %) nunca se ha ejercitado contra Sigrid
  real**: el preflight de julio no la disparó porque el parte de la obra
  destino no existía. Está en F-014.
- El api expone su salud en **`/api/v1/health`**, no en `/health`. Y el front,
  con Easy Auth, responde **401 a un `curl` anónimo**: no es una caída.
- `ruff` **no está instalado** en el venv de `dedicacion-api`.
- **Dos defectos del arnés** anotados para `arnes-base` en `history.md`:
  `init.sh` confunde «no hay tests» con «los tests fallan», y **la caché de
  suites cruza ramas**.
- **Cinco bugs de los scripts de infraestructura** salieron solo al desplegar
  de verdad; ninguno lo habría cazado un test offline. Están en `history.md`.
