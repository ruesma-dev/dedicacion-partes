<!-- specs/F-015-portal-tarjeta-y-usuarios/tasks.md -->
# F-015 · Tareas

Todo MANUAL (humano). Ningún agente ejecuta `az`, ni toca `front-portal`, ni
prueba el acceso. T1–T2 se pueden hacer ya; T3–T4 esperan a D3.

- [x] T1 · HECHA (2026-08-20): Sacar el objectId del grupo. | Verificación: MANUAL —
      `az ad group show --group 'dedicacion-portal-users' --query id -o tsv`
      devuelve un GUID. **No se pega en este repositorio.**
- [~] T2 · entrada AÑADIDA al catálogo; falta el commit y el despliegue, que son del humano: Añadir la entrada de `catalog.js` en `front-portal` con ese GUID y
      lanzar `.\deploy.ps1 -SoloFront`. | Verificación: MANUAL — la tarjeta
      «Dedicación» aparece en `https://ohana.ruesma.es` tras Ctrl+F5.
- [x] T3 · RESUELTA de otro modo: el humano da de alta a la gente a mano cuando decide; la tarjeta ya restringe por grupo. Original: El humano elige A, B o C (design.md §2) y da la lista de correos.
      | Verificación: la decisión queda escrita en `progress/current.md`.
- [x] T4 · HECHA por el humano (2026-08-21): 8 miembros en el grupo, verificado con az: Dar de alta a esas personas con
      `.\setup_front_easyauth.ps1 -Miembros "…"`. | Verificación: MANUAL —
      `az ad group member list --group 'dedicacion-portal-users' --query "[].userPrincipalName" -o tsv`
      los lista.
- [ ] T5: Ventana de incógnito: un miembro entra al front y ve el cuadrante;
      alguien fuera del grupo NO obtiene token. | Verificación: MANUAL.
- [x] T6 · HECHA (2026-08-21): Actualizar `docs/INTEGRACION.md` (§5, la tarjeta y quién entra) y
      refrescar la copia `azure-apps/dedicacion.md`. | Verificación: el
      documento dice quién puede entrar y cómo se da acceso a alguien nuevo;
      el commit de `azure-apps` lo hace el humano.
- [ ] T7: Ejecutar `bash harness/init.sh` en verde. | Verificación: portero en
      verde, incluido `tests/test_f008_infra_sin_secretos.py` (barre `specs/`).
