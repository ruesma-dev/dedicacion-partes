<!-- progress/spec_F-015.md -->
# F-015 · Spec escrita (2026-08-20)

`specs/F-015-portal-tarjeta-y-usuarios/` — tres ficheros, rigor `documental`,
sin código y sin tests nuevos. Todo el trabajo es manual del humano.

## Lo que se averiguó de `front-portal`

`azure-apps/portal.md` §8.2 y §4.1: **no hay canal ni petición a un tercero**.
Dar de alta una app es editar `public/assets/js/catalog.js` en el repositorio
`front-portal` (del propio humano) y lanzar `.\deploy.ps1 -SoloFront` + Ctrl+F5.
La entrada de catálogo ya está redactada en `design.md §1`, lista para pegar.

## Decisiones abiertas

1. **D3 · quién entra en el grupo.** Tres opciones en `design.md §2`
   (A: jefes de obra, encargados y Administración — recomendada; B: + jefes de
   grupo; C: toda la oficina técnica). Bloquea T4 y el criterio 2 de aceptación.
2. **Icono de la tarjeta**: `compare` o `chart` del diccionario `ICONS`, o uno
   nuevo. Decisión estética del humano.
3. ~~**Licencia Entra ID P1**~~ · **CERRADA por el líder el 2026-08-20.**
   Comprobado con `az ad sp list --display-name "dedicacion" --query
   "[].appRoleAssignmentRequired"`: devuelve **True**, así que la asignación
   requerida **sí está activa** y quien no esté en el grupo no obtiene token.
   La duda era legítima —sin licencia P1 la restricción se ignora en
   silencio— pero no se cumple aquí. T5 sigue siendo útil como comprobación
   de extremo a extremo, no como descarte de esto.

Ningún GUID entra en la spec: solo el comando que lo obtiene.
