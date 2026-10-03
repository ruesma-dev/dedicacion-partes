<!-- progress/current.md -->
# Trabajo en curso

**Ninguna feature en ejecución.** F-035 se cerró el 2026-10-03; F-034 y
F-026 se cerraron y se **desplegaron el 2026-10-02** (resúmenes en
`history.md`).

## F-025 · Obras de postventa desde los capítulos de POSTV2 (en spec)

- **Estado: `spec_ready`, revisión de spec en curso** (2026-10-03). La spec
  (`specs/F-025-obras-postventa-postv2/`) la aprobó el humano el 2026-10-01
  (`d49348c`) con **D2 = B** (la cascada de P5 no imputa a partidas ajenas),
  **D4 cambiada** (solo la POSTV2 de Construcciones Ruesma: las obras son
  siempre de la empresa de las obras, F-034) y **D6** (la POSTV antigua
  fuera). Se escribió ANTES de F-034 y F-026; la rama se puso al día con `dev`
  el 2026-10-03.
- **Spec revisada (2026-10-03)** → `progress/spec_F-025_revision.md`: D4
  reescrita en todos sus sitios (un único universo, el de la empresa de las
  obras; contrato de una empresa por petición, R4 pasa a 422), ajustes a
  F-034/F-026 y lista cerrada de tests que cambian **comprobada ejecutando**
  (design §7.1): 8 de F-002 en el transfer y 46 de la api por firma/doble.
- **Pendiente del humano antes de implementar:** aprobar la revisión y
  decidir **D8** (obra-capítulo `0678`→`0678.MO` con D2 = B; recomendada A:
  aceptarlo y reescribir 4 tests de F-002 sobre el presupuesto `hojas`).
- **Riesgo vivo en producción hasta que se despliegue:** el aviso de CP/OT de
  «Producción, hoy». El arnés es la **1.7.3**.

## Producción, hoy

- **Desplegado el 2026-10-02: F-034 y F-026**, sobre lo del 2026-10-01 (F-022,
  F-023, F-024, F-032). Imágenes `transfer:r20261002-1705`,
  `api:r20261002-1706`, `front:r20261002-1708`; la api añadió
  `trabajador.fecha_baja` al arrancar. **Datos de prueba vaciados** (312
  asignaciones, 376 eventos, 7 periodos, 207 trabajadores → 0) y **sync
  hecho**: 196 trabajadores (183 / 8 / 4 / 1 en las empresas 1 / 18 / 31 /
  25), ventana de bajas desde el 2026-09-01, 38 empresas. **Eusebio Vindel
  Duro aparece** (confirmado por el humano).
- **El transfer desplegado escribe DE VERDAD** (`OBRA_PRUEBAS_FORZAR=false`)
  por orden expresa del humano (`docs/INTEGRACION.md` §8). Siguen abiertos
  F-017 (partidas sin validar por Administración) y F-011 (varios códigos M*).
- **Aviso a usuarios hasta F-025:** no registrar postventa en las obras CP ni
  OT (la cascada vigente de P5 las casa con partidas ajenas).
- **El script de vaciado ya funciona contra Azure** (F-035, 2026-10-03): usa
  `psql` y lee la contraseña de `PG-PASSWORD` del Key Vault. `-SoloRecuento`
  cuenta sin escribir: el 2026-10-03 dio 0 asignaciones, 0 eventos, 1
  periodo y 196 trabajadores.

## Lo siguiente, por prioridad

`BACKLOG.md` tiene el orden completo. Primero **F-025** (spec
aprobada con D4 cambiada: solo la POSTV2 de Construcciones Ruesma; el
spec-author la reescribe en su sitio antes de implementar), F-027, F-020,
F-028, F-021, F-029, F-030, F-031, F-033 y, detrás, F-017, F-018…

## ⚠ Lo que espera al humano

1. Decidir si se abren como features las dos observaciones de F-026: la fila
   de guardar/deshacer no conoce el mes, y el front no enseña `no_vigentes`.
2. **Correcciones de la review del despliegue del 2026-10-01**
   (`progress/review_despliegue_20261001.md`: digests de `imagenes.json`,
   textos de scripts que aún dicen «modo pruebas», F-017/F-018) y si **F-017**
   se hace en real con Administración delante. Plan propuesto, **sin
   respuesta**.
3. **`git push`** de `dev` en `porcentajes` y de `main` en `arnes-base`.
4. Decidir si la corrección de `ruesma_rep` de `azure-apps/dedicacion.md` se
   lleva a `docs/INTEGRACION.md`.
5. **F-014** y **F-016**, cuando quiera.
6. Decidir si se abre una feature para que `crear_base_dedicacion.ps1` pida
   las contraseñas antes de sus pasos 1-2 (observación del implementer de
   F-035): hoy, una contraseña rechazada llega después de comprobar el
   servidor y, si faltaba, crear la regla de servicios de Azure.

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
