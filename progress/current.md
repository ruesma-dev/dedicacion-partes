<!-- progress/current.md -->
# Trabajo en curso

**F-032 en review** (nombres de empresa desde Sigrid, rigor estándar, sin
spec: guían sus `acceptance`). El arnés es la **1.7.3**.

## F-032 · Nombres de empresa sincronizados desde Sigrid

- Rama `feature/F-032-empresas-desde-sigrid`. Plan confirmado por el humano
  el 2026-10-01, con la decisión abierta cerrada: una empresa de baja o
  desactivada con trabajadores activos se enseña marcada «(de baja)», nunca
  oculta (`features.json`).
- **Implementer terminado**: 11 commits (`4e4f070` … `106e345`), tabla
  `empresa` desde `auxemp`, preview con las empresas leídas, `/empresas` con
  nombre y `de_baja` de la tabla, fuera `empresas.nombres`; el front solo
  pinta «(de baja)». Mutación con muestreo estándar: 2 supervivientes
  reproducidos a mano y cazados con tests nuevos. Desviación declarada: tests
  de F-024 que fijaban `empresas.nombres` sustituidos por su equivalente
  sobre la tabla, sin cambiar valores esperados. Review pasada 1
  (`progress/review_F-032.md`): código, tests y campaña **bien**;
  CHANGES_REQUESTED solo por el rastro (faltaban aquí el comando exacto de la
  manual y la copia pendiente a `azure-apps`; corregido). Observaciones:
  `resumir_empresas` del preview no hace `strip` del nombre y `sync_en` solo
  se fija al alta, **descartadas por escrito**: el preview es diagnóstico y la
  tabla guarda el nombre limpio; `sync_en` se comporta igual que en
  `trabajador` y `obra`. El cambio de literal de la empresa 1 se avisa al
  humano. Automejora → encargo `620b83d` en `arnes-base`. Pasada 2 lanzada.

### Verificación MANUAL (humano) de F-032

1. **Sync real en local.** Arrancar la api de esta rama con `python main.py`
   desde `services/dedicacion-api` (así `create_all` crea la tabla `empresa`).
   Lanzar el script del líder (solo lectura de Sigrid; el sync escribe solo en
   la BBDD local):
   `powershell -ExecutionPolicy Bypass -File "C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-porcentajes\5cb867d0-7a0e-4697-8553-fb67f1894080\scratchpad\verif_f032_empresas.ps1"`.
   Hace `GET http://localhost:8090/api/v1/sync/preview` (esperado:
   `empresas.leidas` ≥ 19), `POST http://localhost:8090/api/v1/sync`
   (esperado: bloque `empresas` en la respuesta) y
   `GET http://localhost:8090/api/v1/empresas` (esperado: por defecto 1;
   18 = `RUESMA SERVICIOS SL`; 31 = `UTE RUESMA-INESCO TOLEDO`; ninguna
   «Empresa N»; las mismas 3 empresas que antes). Contraste:
   `progress/explore_nombres_empresas.md`. Resultado: _pendiente_.
2. **Selector en `http://localhost:8080`**: enseña 18 = RUESMA SERVICIOS SL,
   31 = UTE RUESMA-INESCO TOLEDO y **1 = CONSTRUCCIONES RUESMA** (el literal
   cambia al de Sigrid: antes «Construcciones Ruesma» de `config.yaml`). Si
   alguna con trabajadores activos está de baja, sale «(de baja)».
   Resultado: _pendiente_.

### Pendiente antes del `done` (líder, con autorización del humano)

- **Copia a `azure-apps/dedicacion.md`**, como en F-022 y F-024: cabecera,
  fila de `sigrid-api` de §1, árbol de §2 (tabla `empresa`), párrafo de
  `GET /api/v1/empresas` (`de_baja`) y fila nueva de `auxemp` en «qué se
  rompe». Commit en `azure-apps`. Resultado: _pendiente_.

> **Aviso de despliegue:** F-022, F-023 y F-024 están en `dev` pero se
> despliegan **junto con F-032**; hasta entonces el selector enseña «Empresa
> 18» y «Empresa 31». La BBDD local ya tiene maestros de todas las empresas.

## Lo siguiente, por prioridad

El backlog completo está en `BACKLOG.md`. Por orden:

| # | Feature | Qué es |
|---|---|---|
| 1 | **F-017** | probar con Administración sobre la obra de pruebas `0404` |
| 2 | **F-018** | pasar a escritura real. Requiere F-017 firmada, **F-026** cerrada y autorización expresa (F-022 ya está) |
| — | **F-032** | en review (arriba) |
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
