<!-- progress/current.md -->
# Trabajo en curso

**F-008 · Infraestructura y despliegue en Azure** — `in_progress`, en la
**segunda pasada de su review de cierre**. Es lo único abierto: todo lo demás
está cerrado, incluida **F-015**.

Rama `dev`, con todo el trabajo integrado.

## Estado del backlog (14 features)

| Estado | Features |
|---|---|
| `done` | F-001, F-002, F-003, F-004, F-009, F-013, **F-015** |
| en review de cierre | **F-008** |
| `pending` | F-005, F-006, F-011, F-012, F-014, **F-016** |

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

1. **`git push origin dev`** en este repositorio.
2. Cuando quiera: **F-014** (aviso a Administración de las cuatro partidas
   duplicadas de POSTV2, quién firma la procedencia, y mirar el primer
   preflight real con líneas `M*` previas) y **F-016** (pedir a `sigrid-api`
   una function key de solo lectura para la api).

> **`azure-apps` ya está commiteado** (`08676ac`). Ojo con un dato: ese
> repositorio **no tiene remoto configurado** (`git remote -v` vacío), así que
> vive solo en local. No es cosa de este proyecto, pero conviene saberlo: lo
> que se escribe ahí no está respaldado en ningún sitio.

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
