<!-- specs/F-015-portal-tarjeta-y-usuarios/requirements.md -->
# F-015 · Requisitos

Rigor `documental`: no hay código, no hay tests nuevos. Lo verifica el humano.

- **R1.** El sistema debe aparecer como tarjeta en el Portal Ruesma, apuntando
  al FQDN del front y desbloqueada por el grupo `dedicacion-portal-users`.
- **R2.** CUANDO se dé de alta a una persona, debe hacerse con
  `infra/setup_front_easyauth.ps1 -Miembros`, y esa persona debe entrar al
  front tras cerrar y reabrir sesión.
- **R3.** SI alguien fuera del grupo abre la URL del front, ENTONCES Entra no
  debe emitirle token (asignación requerida ON).
- **R4.** El repositorio no debe contener ningún objectId, GUID ni tenant.
- **R5.** `azure-apps/dedicacion.md` debe decir quién puede entrar y cómo se da
  acceso a alguien nuevo.
