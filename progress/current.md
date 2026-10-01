<!-- progress/current.md -->
# Trabajo en curso

**F-024 en curso** (selector de empresa, rigor estándar). Spec aprobada por
el humano el 2026-10-01 con D1-D7 (`features.json`). Plan confirmado por el
humano: **implementer lanzado** (T1-T10 y T14 → `progress/impl_F-024.md`) y
explorador de solo lectura en paralelo para los nombres de las empresas 18 y
31 (T12) con el data mart, informe en el scratchpad del líder.

### Verificaciones MANUAL (humano) de F-024

- **T11**: copiar a `azure-apps/dedicacion.md` las piezas de T10, literales, y
  hacer el commit allí. Resultado: _pendiente_.
- **T12**: nombres de las empresas con trabajadores activos (18 y 31) en
  `config.yaml` `empresas.nombres`. Puede cerrarlo el explorador si el humano
  acepta sus nombres; si no, `SELECT numemp, res FROM dbo.auxemp WHERE numemp
  IN (1, 18, 28, 31)` por sigrid-api. Resultado: _pendiente_.
- **T13**: prueba en local (API de la rama, transfer en modo pruebas): sin
  `?empresa` sale Construcciones Ruesma; cambiar a 18 y volver; julio 2026 con
  la 1, las líneas de 0009 y 0025 marcadas `otra_empresa` y omitidas en el
  preflight con `obra_destino.empresa == 28`; preflight con la 18, error de
  obra de pruebas por obra y nada escrito. **NO** lanzar `registro/ejecutar`.
  Resultado: _pendiente_. El arnés es la **1.7.3**.

> **Aviso de despliegue:** F-022 y F-023 están en `dev` pero **no se
> despliegan sin F-024** (sin selector, el cuadrante mezcla empresas). La
> BBDD local ya tiene maestros de todas las empresas desde T11 de F-023.

## Lo siguiente, por prioridad

El backlog completo está en `BACKLOG.md`. Por orden:

| # | Feature | Qué es |
|---|---|---|
| 1 | **F-017** | probar con Administración sobre la obra de pruebas `0404` |
| 2 | **F-018** | pasar a escritura real. Requiere F-017 firmada, **F-026** cerrada y autorización expresa (F-022 ya está) |
| 3 | **F-025**, **F-026** | obras de postventa desde POSTV2; recursos sin ficha de empleado |
| — | **F-024** | en curso (arriba) |
| 4 | **F-027**, F-020 | deshacer solo lo propio; Excel |

**Efecto visible de F-022 hasta que llegue F-024:** la api imputa siempre a
la empresa 1 (`EMPRESA_IMPUTACION`), así que las líneas puestas en una obra
de otra empresa (por ejemplo 0009 y 0025, de Porsan) salen **omitidas con
motivo** en el preflight. Con F-023 el maestro ya distingue la empresa de
cada ficha; falta que el usuario elija empresa (F-024).

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
