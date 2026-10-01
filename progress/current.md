<!-- progress/current.md -->
# Trabajo en curso

**Ninguna feature en ejecución.** F-032 se cerró el 2026-10-01 (resumen en
`history.md`). El arnés es la **1.7.3**.

> **2026-10-01, en curso:** el humano aclara que las OBRAS (incluida la
> postventa) son siempre de Construcciones Ruesma; los trabajadores, de varias
> empresas. F-024 se desplegó con la regla contraria y **los trabajadores de
> la 18 y la 31 no pueden registrar en producción**. Entra **F-034** con
> prioridad 1; spec entregada (`edab7d9`) y en `spec_ready`: **espera la
> aprobación del humano** (D1-D5 y si se despliega sola o con F-026).
> **F-025** tiene la spec aprobada (con D4 cambiada por esta regla) y espera
> turno en su rama. Orden: F-034 → F-026 → F-025.
> **Aviso a usuarios hasta F-025:** no registrar postventa en las obras CP ni
> OT (la cascada vigente de P5 las casa con partidas ajenas y se escribiría en
> real).
> **Pendiente de respuesta del humano:** el plan de correcciones de la review
> del despliegue (`progress/review_despliegue_20261001.md`) y si F-017 se hace
> en real con Administración delante.

## ⚠ DESPLEGADO EN MODO REAL (2026-10-01)

- **Despliegue** de F-022, F-023, F-024 y F-032 lanzado por el humano con
  `infra/redeploy_dedicacion.ps1` (el permiso del entorno no dejó lanzarlo al
  líder). Imágenes `transfer:r20261001-1805`, `api:r20261001-1807`,
  `front:r20261001-1808`; las tres revisiones `…--r20261001180529` activas y
  listas. La api aplicó el esquema al arrancar (`ALTER … ADD COLUMN empresa`
  en `trabajador` y `obra`; tabla `empresa` por `create_all`). Ya se ha hecho
  un sync en producción: 536 recursos fuera por fecha de baja, 38 empresas.
- **El transfer escribe DE VERDAD** (`OBRA_PRUEBAS_FORZAR=false`) por orden
  expresa del humano, a sabiendas de F-017, F-026 y F-011 (anotado en F-018).
  **Incidente durante el despliegue:** el humano cambió a real ANTES de
  desplegar y durante un rato corrió el transfer VIEJO en real (revisión
  `--0000001`, sin F-022). Comprobado en los logs: en ese tiempo y después
  solo hubo **preflights**, **ningún `ejecutar`**; no se escribió nada en
  Sigrid.
- **El primer despliegue falló** al escribir `infra/imagenes.json`: causa raíz
  encontrada (en PowerShell `$inventario` pisaba `$INVENTARIO`, la ruta; es la
  misma del fallo del 2026-08-20). Hotfix del líder con autorización del
  humano en `d449a58` (rama `chore/despliegue-20261001`). **Pendiente: review
  de ese hotfix.**
- Documentación al día con el modo real: `CLAUDE.md`, `README.md`,
  `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` (§8 con el comando para volver
  a pruebas) y su copia en `azure-apps`.

## Lo siguiente, por prioridad

El backlog completo está en `BACKLOG.md`. Por orden:

| # | Feature | Qué es |
|---|---|---|
| 1 | **F-017** | probar con Administración sobre la obra de pruebas `0404` |
| 2 | **F-018** | pasar a escritura real. Requiere F-017 firmada, **F-026** cerrada y autorización expresa (F-022 ya está) |
| 3 | **F-025**, **F-026** | obras de postventa desde POSTV2; recursos sin ficha de empleado |
| 4 | **F-027**, F-020 | deshacer solo lo propio; Excel |

## ⚠ Lo que espera al humano

1. **`git push`** de `dev` en `porcentajes` y de `main` en `arnes-base`.
   `azure-apps` no tiene remoto.
2. **Decidir** si la corrección de `ruesma_rep` («no es réplica, es la base
   documental») que tiene `azure-apps/dedicacion.md` se lleva a
   `docs/INTEGRACION.md`.
3. **Datos para F-026**: las tres consultas de
   `progress/explore_eusebio.md`, y si encargados y gruistas se dan de alta
   sin ficha de empleado a propósito.
4. **F-014** y **F-016**, cuando quiera: aviso a Administración de las cuatro
   partidas duplicadas de POSTV2 y quién firma P4/P5; pedir a `sigrid-api`
   una clave de solo lectura para la api.

> **`azure-apps` no tiene remoto configurado** (`git remote -v` vacío): vive
> solo en local. No es de este proyecto, pero ahí está la documentación de todo
> el ecosistema y no está respaldada en ningún sitio.

## Lo que el sistema sabe hacer, comprobado

- **Corre en local y en Azure.** En local: transfer 8006 → api 8090 →
  front 8080, cada uno desde su carpeta con su venv (`README.md`).
- **Escribe en Sigrid de verdad**: crea el parte si no existe e inserta la
  línea con su `synckey` (T14). Ahora mismo **no tiene ninguna fila propia** en
  el ERP: la prueba se limpió.
- **Avisa y espera confirmación** en tres casos, cada uno con su clave: pisar
  una línea existente, pasarse del 100 % de un trabajador (F-002) y escribir
  sin partida casada (F-013).
- **El transfer sigue en modo pruebas.** El motivo real está en
  `docs/ARCHITECTURE.md`: **la imputación a partidas en producción no está
  validada**. Salir de ahí exige autorización expresa para una acción concreta.

## Lo que NO está verificado, y consta

- **R34**: el `/health` del transfer con `modo_pruebas` y `database` no se ha
  comprobado en caliente — su ingress es interno y no es alcanzable desde
  fuera, que es lo que la decisión D2 buscaba.
- **T29**: la prueba funcional de extremo a extremo se apoya en la
  confirmación del humano, **sin volcado**.
- **La Regla B nunca se ha ejercitado contra Sigrid real** (F-014).

## Hechos que no conviene volver a descubrir

- El api expone su salud en **`/api/v1/health`**, no en `/health`. El front,
  con Easy Auth, responde **401** a un `curl` anónimo, y el Portal **302**:
  no son caídas.
- `ruff` **no está instalado** en el venv de `dedicacion-api`.
- **Dos defectos del arnés**, anotados para `arnes-base`: `init.sh` confunde
  «no hay tests» (pytest código 5) con «los tests fallan» —desde la 1.7.2 es
  defecto CONOCIDO con ficha (F-041 en `albaranes`), aún sin arreglar—, y **la
  caché de suites cruza ramas**, que sigue sin ficha.
- **Los scripts de `infra/` solo se prueban ejecutándolos contra Azure**: cinco
  bugs salieron así, ninguno lo habría cazado un test offline.
- **Un fichero de rastro puede contener información única.** Resolver su
  conflicto de merge reescribiéndolo la destruye en silencio: pasó con el
  volcado de T13 y se recuperó del historial.
