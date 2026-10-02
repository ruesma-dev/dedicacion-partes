<!-- progress/current.md -->
# Trabajo en curso

**Ninguna feature en ejecución.** F-034 y F-026 se cerraron el 2026-10-02
(resúmenes en `history.md`); están en `dev` y **pendientes de desplegarse
juntas** (sección siguiente). El arnés es la **1.7.3**.

## Producción, hoy

- Desplegado el 2026-10-01: F-022, F-023, F-024 y F-032 (imágenes
  `transfer:r20261001-1805`, `api:r20261001-1807`, `front:r20261001-1808`).
- **El transfer desplegado escribe DE VERDAD** (`OBRA_PRUEBAS_FORZAR=false`)
  por orden expresa del humano (`docs/INTEGRACION.md` §8, con el comando para
  volver a pruebas). A sabiendas: F-017 (partidas sin validar por
  Administración) y F-011 (varios códigos M*). F-034 y F-026, que corrigen el
  resto, aún **no** están desplegadas.
- **Hasta desplegar F-034 + F-026:** los trabajadores de la 18 y la 31 no
  pueden registrar (sus líneas se omiten), y el recurso se elige sin mirar la
  empresa.
- **Aviso a usuarios hasta F-025:** no registrar postventa en las obras CP ni
  OT (la cascada vigente de P5 las casa con partidas ajenas).

## ⚠ Despliegue conjunto F-034 + F-026 (pendiente; lo lanza el humano)

`infra/README_dedicacion.md` §3 bis: republicar transfer y api juntos →
vaciado de los datos de prueba en Azure (`infra/vaciar_datos_prueba_dedicacion.ps1`,
plan y `-Confirmar`, **autorización expresa del humano**) →
`GET /api/v1/sync/preview` → `POST /api/v1/sync`. El transfer desplegado
escribe de verdad: **nada de `registro/ejecutar` hasta terminar**. Lo lanza
el humano (el permiso del entorno no deja desplegar al líder).

## Lo siguiente, por prioridad

`BACKLOG.md` tiene el orden completo. Tras desplegar F-034 + F-026: **F-025** (spec
aprobada con D4 cambiada: solo la POSTV2 de Construcciones Ruesma; el
spec-author la reescribe en su sitio antes de implementar), F-027, F-020,
F-028, F-021, F-029, F-030, F-031, F-033 y, detrás, F-017, F-018…

## ⚠ Lo que espera al humano

1. **Desplegar F-034 + F-026** (sección de arriba), con el vaciado en Azure
   autorizado expresamente, y pulsar «actualizar Sigrid» antes de registrar.
2. **Correcciones de la review del despliegue del 2026-10-01**
   (`progress/review_despliegue_20261001.md`: digests de `imagenes.json`,
   textos de scripts que aún dicen «modo pruebas», F-017/F-018) y si **F-017**
   se hace en real con Administración delante. Plan propuesto, **sin
   respuesta**.
3. **`git push`** de `dev` en `porcentajes` y de `main` en `arnes-base`.
4. Decidir si la corrección de `ruesma_rep` de `azure-apps/dedicacion.md` se
   lleva a `docs/INTEGRACION.md`.
5. **F-014** y **F-016**, cuando quiera.

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
