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

---

## Decisiones cerradas y trabajo hecho (2026-08-20)

- **Icono: `chart`.** Lo eligió el líder a petición del humano. Motivo: esto es
  un **cuadrante de porcentajes**, no una comparativa; `compare` ya lo usa
  «Comparativos» y confundiría dos cosas distintas en la misma parrilla.
- **D3 ya no bloquea.** Decisión del humano: la tarjeta se deja **con el grupo
  configurado** y él dará de alta a las personas a mano cuando decida quién
  entra. La restricción funciona desde el primer día aunque el grupo esté casi
  vacío.
- **T1 · objectId obtenido** con `az ad group show`. **No se ha escrito en este
  repositorio**; solo en `catalog.js` de `front-portal`, que es donde el propio
  mecanismo del portal lo espera (todas sus entradas llevan el suyo).
- **T2 · entrada añadida** a
  `front-portal/public/assets/js/catalog.js`, en la categoría **Obra**, justo
  detrás de «Partes de Trabajo». Sintaxis verificada con `node --check`.

### ⚠ Lo que queda, y una advertencia

**`front-portal` tenía cambios sin commitear ANTES de que se tocara nada**:
`deploy.ps1` (211 líneas), `app.js` y el propio `catalog.js`. Entre esos
cambios previos hay uno a medias que conviene mirar antes de desplegar:

```
requiredGroupId: ['REEMPLAZAR_OBJECT_ID_compras_usuarios'],
```

Es un marcador sin sustituir en la entrada de **Comparativos**. No es nuestro y
no se ha tocado, pero **si se despliega así, esa tarjeta no dejará entrar a
nadie**.

El humano debe: revisar el diff completo de `front-portal`, commitear allí
(es otro repositorio: el commit es suyo), y lanzar `.\deploy.ps1 -SoloFront`.
