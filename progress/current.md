<!-- progress/current.md -->
# Trabajo en curso

**F-026 en curso** (recursos por recurso, rigor crítico): review pasada 2 con
el código y la mutación aprobados; quedan la aceptación del superviviente nº 5
y las MANUAL. **F-034 `blocked`** solo por su T9, que se hace junto con las de
F-026. Las dos se **despliegan juntas**. El arnés es la **1.7.3**.

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

## F-026 · El sync parte del recurso (en curso)

- Rama `feature/F-026-recursos-sin-ficha-empleado` (lleva `dev` con F-034).
  Spec aprobada con la enmienda del humano del 2026-10-02 (clave = `res.ide`
  sin migración; vaciado de los datos de prueba al desplegar; vigencia por
  mes) y con el cambio de método para los tests anteriores (`features.json`).
- Implementer: `progress/impl_F-026.md`. Review: `progress/review_F-026.md`
  (pasada 1, un punto de evidencia resuelto en el ciclo 2; pasada 2, código y
  campaña 55/56 correctos, cambios pedidos solo en este fichero).
- **Pendiente antes del `done`:**
  - **Superviviente nº 5 (humano):** aceptar por escrito el equivalente
    `prueba_escritura_porcentajes.py:53` `900003→900004`
    (`progress/mutacion_F-026.md`). Resultado: _pendiente_.
  - **T14 (R24), local: vaciado con autorización del humano + sync.**
    `cd infra; .\vaciar_datos_prueba_dedicacion.ps1 -Local` (esperado: solo el
    plan) y `.\vaciar_datos_prueba_dedicacion.ps1 -Local -Confirmar` (pide la
    contraseña de `$env:PGUSER` o `postgres`; esperado: recuento antes, la
    sentencia, recuento 0/0/0/0). API de la rama
    (`cd services\dedicacion-api; .venv\Scripts\python main.py`);
    `GET http://localhost:8090/api/v1/sync/preview` (esperado:
    `empleados.ventana_baja` = día 1 del mes anterior o del ABIERTO más
    antiguo; `posible_misma_persona` con `MO/0061` y `MO/0736`) y
    `POST http://localhost:8090/api/v1/sync`. En la base:
    `SELECT ide, cod, empresa, activo, fecha_baja FROM trabajador WHERE cod IN ('MO/0772','MO/0759','MO/0760','MO/0762','MO/0774','MO/0775','MO/0776','MO/0777','MO/0779','MO/0496') AND empresa = 1`
    (esperado: diez activos, `ide` = su `res.ide`) y
    `SELECT COUNT(*) FROM trabajador WHERE fecha_baja < <ventana_baja>` (0). Un
    recurso con `fecha_baja` en el mes en curso sale en ese mes y no en el
    siguiente. Resultado: _pendiente_.
  - **T15 (R25), preflight de SOLO LECTURA** con el transfer local en modo
    pruebas (`OBRA_PRUEBAS_FORZAR=true`;
    `cd services\dedicacion-transfer; .venv\Scripts\python main.py`): dar a
    Eusebio (`1-MO/0772`) una línea en un periodo local y
    `curl -X POST http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight -H "Content-Type: application/json" -d "{}"`.
    Esperado: su acción `escribir` con `recurso_ide` = su `res.ide`; ninguna
    omitida por «la línea no trae el recurso del trabajador»;
    `no_vigentes: []`. **NO lanzar `registro/ejecutar`.** Resultado: _pendiente_.
  - **T16 (líder, con autorización del humano): copia a
    `azure-apps/dedicacion.md`** de las piezas de T12 de `docs/INTEGRACION.md`
    (cabecera, avisos, vaciado en §2, contrato de la línea en §9, dos filas en
    cada tabla de §7). Commit en `azure-apps`. Resultado: _pendiente_.
- **Observaciones de las reviews, recogidas o descartadas por escrito:**
  - Frase de `infra/README_dedicacion.md` §3 bis («sus líneas llevarían un
    `emp.ide`… que el transfer omite (P1)»): **corregida** (tras el sync esas
    líneas son de trabajadores no vigentes y van a `no_vigentes`).
  - `ruff I001` (orden de imports) en 4 ficheros de test nuevos:
    **descartada** como deuda de estilo; `ruff` no bloquea (193 avisos previos)
    y tocar los tests ahora obligaría a otra pasada de review. Entra en F-006
    (sanear suites).
  - Fila tras guardar/deshacer sin conocer el mes, y el front sin enseñar
    `no_vigentes`: **propuestas al humano como features pequeñas**, pendientes
    de su decisión.
  - Automejoras (RM5: «que la suite pase con el mutante prueba que sobrevive,
    no que sea equivalente»; `init.sh` compruebe que la cabecera de
    `current.md` nombra la `in_progress`) → encargo `69df67b` en `arnes-base`.
  - Falsos supervivientes con `workers > 1` (tercera feature seguida) →
    añadido al encargo de `arnes-base` (`affff93`).

## F-034 · Obras siempre de Construcciones Ruesma (`blocked` solo por T9)

- En `dev` (`d6656ad`). Review APROBADA; T8 (copia a `azure-apps`, `b4d5340`)
  hecha; M4 aceptado por el humano el 2026-10-02.
- **T9 (humano), se hace junto con T14/T15 de F-026.** Transfer local con
  `OBRA_PRUEBAS_FORZAR=true`; api y front de la rama (`python main.py` en
  cada servicio). En `http://localhost:8080/?empresa=18` las obras ofrecidas
  son las de Construcciones Ruesma; dar a un trabajador de la 18 una línea en
  una de ellas y, desde Git Bash,
  `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight?empresa=18" -H "Content-Type: application/json" -d "{}"`.
  **Esperado:** `ok: true`, `obra_origen.empresa` = 1 y la acción de esa línea
  `escribir`, no `omitir` por empresa. **No lanzar `registro/ejecutar`.**
  Resultado: _pendiente_.
- **Tras desplegar (humano, no bloquea el `done`):** cuadrante de producción
  con `?empresa=18`: obras de Construcciones Ruesma, **sin pulsar Registrar**.

## Despliegue conjunto F-034 + F-026 (cuando las dos cierren)

`infra/README_dedicacion.md` §3 bis: republicar transfer y api juntos →
vaciado de los datos de prueba en Azure (`infra/vaciar_datos_prueba_dedicacion.ps1`,
plan y `-Confirmar`, **autorización expresa del humano**) →
`GET /api/v1/sync/preview` → `POST /api/v1/sync`. El transfer desplegado
escribe de verdad: **nada de `registro/ejecutar` hasta terminar**. Lo lanza
el humano (el permiso del entorno no deja desplegar al líder).

## Lo siguiente, por prioridad

`BACKLOG.md` tiene el orden completo. Tras F-034 y F-026: **F-025** (spec
aprobada con D4 cambiada: solo la POSTV2 de Construcciones Ruesma; el
spec-author la reescribe en su sitio antes de implementar), F-027, F-020,
F-028, F-021, F-029, F-030, F-031, F-033 y, detrás, F-017, F-018…

## ⚠ Lo que espera al humano

1. Aceptar el superviviente nº 5 de F-026, y las MANUAL T9, T14 y T15.
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
