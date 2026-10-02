<!-- progress/current.md -->
# Trabajo en curso

**F-034 en curso** (review APROBADA; faltan T8, T9 y la aceptación de M4 para
`done`). F-032 se cerró el 2026-10-01 (resumen en `history.md`). El arnés es la **1.7.3**.

> **2026-10-01, en curso:** el humano aclara que las OBRAS (incluida la
> postventa) son siempre de Construcciones Ruesma; los trabajadores, de varias
> empresas. F-024 se desplegó con la regla contraria y **los trabajadores de
> la 18 y la 31 no pueden registrar en producción**. Entra **F-034** con
> prioridad 1; spec **aprobada** por el humano con D1-D5 (`edab7d9`);
> plan confirmado. **BLOCKED (2026-10-01)**: el implementer
> paró antes de escribir código porque la lista cerrada de tests que cambian
> (design §6) se quedó corta: 4 tests de F-024 (R17 registro, R10 cuadrante,
> R6 y R6/R13 rutas) cambian como consecuencia directa de R1/R3 y no estaban
> en la lista (`progress/impl_F-034.md`, «Motivo del bloqueo»). El humano acepta
> (2026-10-02): `in_progress` de nuevo; §6 completado (`ba55567`).
> **Implementer terminado** (`ef56e2d` … `573ee1e`, `progress/impl_F-034.md`);
> **review APROBADA** (`progress/review_F-034.md`). Manuales, copia a
> `azure-apps` y aceptación de M4: sección «F-034 · pendiente» más abajo.
> **F-034 está en `dev` pero NO se despliega sola**: va con F-026.
> Se despliega **junto con F-026**.
> **F-026**: decisión del humano 2026-10-01, «no debe buscar por empleado sino
> por recurso»: el sync parte de los RECURSOS activos (sin fecha de baja) con
> código de hora mes; la ficha de empleado es opcional (solo DNI); la api
> manda al transfer el recurso exacto. Spec aprobada por el
> humano el 2026-10-02 con la enmienda (`56cfd3e`): clave = `res.ide` sin
> migración (vaciado de los datos de prueba al desplegar, con autorización
> expresa), vigencia por mes con ventana de bajas, D2 y D4-D7. `dev` (con
> F-034) traído a su rama; **BLOCKED (2026-10-02) en T2**: la lista cerrada de
> tests que cambian (design §7) se queda corta, como pasó en F-034. T1 hecha
> (`3627a6b`); T2 hecha pero guardada en `stash@{0}` para no dejar la rama en
> rojo. El implementer listó de antemano lo que tocarán T2-T9 (A1-A8 en F-023,
> B1 en F-024, C1-C3 dobles): `progress/impl_F-026.md`. **El humano aprueba
> (2026-10-02)** la ampliación y un cambio de método para el resto de F-026
> (cambios de test consecuencia directa de un requisito, declarados en tabla y
> verificados uno a uno por el reviewer; ver `features.json`). `in_progress`
> de nuevo. **Implementer terminado** (`75271a3` … `1bdb08b`,
> `progress/impl_F-026.md`): mutación 50/56 con 6 equivalentes justificados.
> Review pasada 1: **CHANGES_REQUESTED** por un solo punto de evidencia: 5 de
> los 6 supervivientes de `prueba_escritura_porcentajes.py` no son equivalentes
> (duplican `registro_id`/`synckey` o quitan el centinela `recurso_ide: 0`).
> Ciclo 2 hecho (`df7e94c` … `bc4cf86`): test R20 que fija
> `registro_id` únicos y `recurso_ide` 0 en el script; campaña 55/56; queda el
> nº 5 (`900003→900004`, identificador arbitrario) como equivalente, **pendiente
> de aceptación del humano**. **Reviewer, pasada 2, lanzado.** Manuales en «F-026 · pendiente» más abajo. F-034 queda `blocked` solo por su T9, que el
> humano hará junto con las manuales de F-026 (el líder le guía).
> **F-025** tiene la spec aprobada (con D4 cambiada por esta regla) y espera
> turno en su rama. Orden: F-034 + F-026 (un solo despliegue) → F-025.
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

## F-034 · pendiente antes del `done`

- **T8 — CUMPLIDA. Copia a `azure-apps/dedicacion.md`**,
  literal, de las piezas de T7: los puntos de `#regla-empresa` cambiados en
  `docs/ARCHITECTURE.md` y, de `docs/INTEGRACION.md`, la cabecera, la fila
  `EMPRESA_IMPUTACION` de §3 y el párrafo «Una línea sin empresa no se
  registra» de §9 (`git diff d34e4a1 -- docs/`). Commit en `azure-apps`.
  **Resultado: HECHA (2026-10-02)**, commit `b4d5340` en `azure-apps`, marcada
  «aún NO desplegado». (ARCHITECTURE no tiene copia en `azure-apps`.)
- **T9 (humano, R13, D5): preflight en local, solo lectura. Se hará JUNTO con
  las verificaciones de F-026 (decisión del humano 2026-10-02); el líder le
  guía cuando esté listo.** Transfer local
  con `OBRA_PRUEBAS_FORZAR=true` en su `.env`; api y front de esta rama
  (`python main.py` en cada servicio). En `http://localhost:8080/?empresa=18`:
  las obras ofrecidas son las de Construcciones Ruesma; dar a un trabajador
  de la 18 una línea en una de ellas en 2026-09 (solo BBDD local). Después,
  desde Git Bash:
  `curl -s -X POST "http://localhost:8090/api/v1/periodos/2026/9/registro/preflight?empresa=18" -H "Content-Type: application/json" -d "{}"`.
  **Esperado:** `ok: true` por obra, `obra_origen.empresa` = 1 y la acción de
  esa línea `escribir`, no `omitir` por empresa. **No lanzar
  `registro/ejecutar`.** Resultado: _pendiente_.
- **Tras desplegar (humano, no bloquea el `done`):** cuadrante de producción
  con `?empresa=18`: obras de Construcciones Ruesma, **sin pulsar Registrar**.
- **M4 — ACEPTADO. Mutante equivalente.** En
  `RegistroSigrid` `filtro.por_defecto` y `filtro.empresa_obras` salen del
  mismo ajuste (D1), así que cambiar uno por otro no lo distingue ningún test;
  reproducido por el reviewer (RM5). **ACEPTADO por el humano el 2026-10-02.**
- **Despliegue:** junto con F-026 (decisión del humano). No se despliega sola.
- Observación de la review: una corrida de la campaña dio 3 supervivientes
  que no se reprodujeron en copia aislada. Si vuelve a pasar, encargo en
  `arnes-base` (es la misma familia que el de la caché previa de F-022).

## F-026 · pendiente antes del `done`

El humano las hará **junto con la T9 de F-034** (el líder le guía con un
script versionado cuando la review apruebe).

- **T14 (R24), local, vaciado con autorización del humano + sync.**
  `cd infra; .\vaciar_datos_prueba_dedicacion.ps1 -Local` (esperado: solo el
  plan) y `.\vaciar_datos_prueba_dedicacion.ps1 -Local -Confirmar` (pide la
  contraseña de `$env:PGUSER` o `postgres`; esperado: recuento antes, la
  sentencia, recuento 0/0/0/0). API de la rama
  (`cd services\dedicacion-api; .venv\Scripts\python main.py`);
  `GET http://localhost:8090/api/v1/sync/preview` (esperado:
  `empleados.ventana_baja` = día 1 del mes anterior o del ABIERTO más antiguo;
  `posible_misma_persona` con `MO/0061` y `MO/0736`) y
  `POST http://localhost:8090/api/v1/sync`. En la base:
  `SELECT ide, cod, empresa, activo, fecha_baja FROM trabajador WHERE cod IN ('MO/0772','MO/0759','MO/0760','MO/0762','MO/0774','MO/0775','MO/0776','MO/0777','MO/0779','MO/0496') AND empresa = 1`
  (esperado: diez activos, `ide` = su `res.ide`) y
  `SELECT COUNT(*) FROM trabajador WHERE fecha_baja < <ventana_baja>` (0).
  Un recurso con `fecha_baja` en el mes en curso sale en ese mes y no en el
  siguiente. Resultado: _pendiente_.
- **T15 (R25), preflight de SOLO LECTURA** con el transfer local en modo
  pruebas (`OBRA_PRUEBAS_FORZAR=true`; `cd services\dedicacion-transfer;
  .venv\Scripts\python main.py`): dar a Eusebio (`1-MO/0772`) una línea en un
  periodo local y
  `curl -X POST http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight -H "Content-Type: application/json" -d "{}"`.
  Esperado: su acción `escribir` con `recurso_ide` = su `res.ide`; ninguna
  omitida por «la línea no trae el recurso del trabajador»; `no_vigentes: []`.
  **NO lanzar `registro/ejecutar`.** Resultado: _pendiente_.
- **T16 (líder, con autorización del humano): copia a `azure-apps/dedicacion.md`**
  de las piezas de T12 de `docs/INTEGRACION.md` (cabecera, avisos, vaciado en
  §2, contrato de la línea en §9, dos filas en cada tabla de §7). Commit en
  `azure-apps`. Resultado: _pendiente_.
- **Despliegue conjunto F-034 + F-026 (D7)**, `infra/README_dedicacion.md` §3
  bis: republicar transfer y api juntos → vaciado en Azure (plan y
  `-Confirmar`, **autorización expresa del humano**) → `sync/preview` → `sync`.
  El transfer desplegado escribe de verdad: **nada de `registro/ejecutar`
  hasta terminar**.
- **Superviviente nº 5 (humano): aceptar por escrito el equivalente**
  `prueba_escritura_porcentajes.py:53` `900003→900004` (ver
  `progress/mutacion_F-026.md`). Resultado: _pendiente_.
- **Observaciones del implementer, propuestas al humano como features
  aparte:** (a) la fila que devuelven guardar y deshacer no conoce el mes: un
  trabajador no vigente con líneas vuelve con el `activo` del ORM hasta
  recargar; (b) el front no enseña `no_vigentes`: esas líneas no se
  registran y el usuario no ve el motivo. (c) Arnés: la mutación con
  `workers > 1` volvió a dar falsos supervivientes (tercera vez: F-022, F-034,
  F-026) → se añade al encargo de `arnes-base` de la caché previa.

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
- **El transfer desplegado escribe DE VERDAD desde el 2026-10-01**, por
  decisión expresa del humano (`docs/INTEGRACION.md` §8, con el comando para
  volver a pruebas). Sigue sin validar la imputación a partidas en producción
  (`docs/ARCHITECTURE.md`, F-017).

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
