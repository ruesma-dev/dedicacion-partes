<!-- specs/F-015-portal-tarjeta-y-usuarios/design.md -->
# F-015 · Diseño

**En este repositorio no se toca código.** Solo se ejecutan comandos y, al
final, se refresca `docs/INTEGRACION.md` → copia en `azure-apps/dedicacion.md`
(commit de ese repo: del humano).

## 1 · Qué se le pide a `front-portal`

Según `azure-apps/portal.md` §8.2 **no hay canal ni formulario**: dar de alta
una app es editar `public/assets/js/catalog.js` en
`C:\Users\pgris\PycharmProjects\front-portal` —repositorio del propio humano— y
lanzar `.\deploy.ps1 -SoloFront`. Entrada lista para pegar (esquema §4.1):

```js
{
  id: 'dedicacion',
  title: 'Dedicación',
  description: 'Cuadrante mensual de dedicación por obra y su registro en los partes de Sigrid.',
  category: 'Obra',
  icon: 'compare',            // o 'chart'; si se quiere uno propio, añadir a ICONS de app.js
  url: 'https://ca-dedicacion-front.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io',
  requiredGroupName: 'dedicacion-portal-users',
  requiredGroupId: ['<pegar aquí la salida del comando de abajo, NO en este repo>'],
  comingSoon: false
}
```

El GUID va **solo** ahí, nunca en este repositorio. Se obtiene con:

```powershell
az ad group show --group 'dedicacion-portal-users' --query id -o tsv
```

Luego `.\deploy.ps1 -SoloFront` y **Ctrl+F5** en el navegador.

## 2 · D3 — quién entra en el grupo (decide el humano)

El cuadrante lo rellena quien conoce la dedicación real de cada trabajador: los
176 trabajadores del maestro **no** son 176 usuarios. Tres opciones:

**A** jefes de obra y encargados + Administración (recomendada) · **B** A +
jefes de grupo/producción · **C** toda la oficina técnica.

## 3 · Alta de miembros (y de bajas)

Desde `infra/`, con las variables cargadas:

```powershell
. .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1
.\setup_front_easyauth.ps1 -Miembros "persona@ruesma.es","otra@ruesma.es"
```

Idempotente: a quien ya es miembro lo salta y a quien no existe lo avisa sin
fallar. **Cada persona debe cerrar sesión y volver a entrar** para que su token
traiga el grupo (`portal.md` §6.5). Para una baja,
`az ad group member remove --group 'dedicacion-portal-users' --member-id <oid>`.

## 4 · Riesgo conocido

Si el script avisó de que no pudo asignar el grupo a la Enterprise App (falta
licencia Entra ID P1), la restricción no está activa y entra cualquiera del
tenant. Se comprueba en T5; no se da por hecho.
