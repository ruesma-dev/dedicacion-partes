<!-- progress/current.md -->
# Trabajo en curso

**F-023 con review APROBADA** (pasada 1, rigor crítico; `progress/review_F-023.md`).
T9 cumplida; falta la pasada 3 (documental) de la review para mergear a `dev`, y T10 y T11 para `done`. El arnés es la **1.7.3**.

## F-023 · Sync de maestros: todas las empresas y activo según el estado del recurso

- Rama `feature/F-023-sync-empresa-y-estado-recurso`, con `dev` traído
  (`792870f`, incluye F-022). Estado `in_progress`. Spec aprobada el
  2026-09-29; decisiones en `features.json`.
- **Implementer terminado**: T1-T8 y T12 hechas, un commit por tarea más dos
  de ajuste (`5ae53d1` … `19d4f40`); informe `progress/impl_F-023.md`, con
  mutación 33/33 y dos desviaciones menores, aceptadas. **Review APROBADA**:
  campaña reejecutada 33/33, cobertura 100 % (67/67), 0 avisos de ruff nuevos.
- Observaciones de la review, **recogidas**:
  1. R12 y el JOIN a `conest` del recurso quedan inertes (el tipo 33 no tiene
     estados) y la comparación es por subcadena: un `"1"` casaría `"10"`. **Al
     cerrar T9**, el líder corrige el comentario de `config.yaml` (para
     recursos no hay literales; el criterio es la fecha de baja). Simplificar
     R12 sería otra feature, si el humano la quiere.
  2. T11 corregida abajo: las filas **desactivadas** conservan `empresa` NULL
     (el upsert solo escribe las recibidas). Aviso llevado a F-024.
  3. **T9 antes del merge a `dev`**, no solo antes del despliegue: sin el
     criterio, esta rama mete en el maestro ~535 personas de baja como recurso
     que hoy filtra `emphis`.
  - Automejora (C4: comprobar que el resultado esperado de una MANUAL es
    alcanzable) → encargo en el backlog de `arnes-base`.
- **Explorador (D1)** → `progress/explore_estado_recurso.md`: el «rojo» de
  Administración es la **fecha de baja del concepto del recurso**
  (`con.fecbaj > 0`); el tipo 33 no tiene estados en `conest`. **Aceptado por
  el humano el 2026-10-01 y aplicado en T9** (`9b9c1d9`).
- **No se despliega sin F-024** (D4: sin selector, una persona con fichas en
  dos empresas sale dos veces). Mergear a `dev` no despliega.

### Verificaciones MANUAL (humano) de F-023

- **T9 · D1 — CUMPLIDA (2026-10-01)**: decidida por el humano, sin lanzar Q1:
  inactivo = fecha de baja del recurso. Implementada en `9b9c1d9`:
  `excluir_recurso_con_fecha_baja: true`, lista de estados vacía con
  comentario corregido (observación 1 de la review), `r5` y `r18` adaptados
  con fase RED real, mutación 33/33, `init.sh` en verde. Review pasada 2:
  código y tests **aprobados**; CHANGES_REQUESTED solo porque la D1 seguía
  abierta en otros sitios del rastro (corregido). Pasada 3, solo documental,
  lanzada. Automejora → encargo `c94c072` en `arnes-base`.
- **T10 · R19 y D6**: con la API local apuntando a Sigrid,
  `GET http://localhost:8090/api/v1/sync/preview`. Comprobar que no llega
  truncada, que los recursos inactivos que señaló negocio (lista D5, **aún no
  entregada**) salen en `excluidos_por_estado_recurso`, y revisar
  `por_empresa`. Resultado: _pendiente_.
- **T11**: API contra la BBDD local `dedicacion`; comprobar que el esquema
  añade `empresa` a `trabajador` y `obra`; `POST /api/v1/sync` y
  `SELECT empresa, COUNT(*) FROM obra WHERE activa GROUP BY empresa` y
  `SELECT empresa, COUNT(*) FROM trabajador WHERE activo GROUP BY empresa`,
  sin NULL. Las filas desactivadas **sí** pueden quedar con NULL, y es
  correcto (observación 2 de la review). Resultado: _pendiente_.

## Lo siguiente, por prioridad

El backlog completo está en `BACKLOG.md`. Por orden:

| # | Feature | Qué es |
|---|---|---|
| 1 | **F-017** | probar con Administración sobre la obra de pruebas `0404` |
| — | **F-023** | en curso (arriba); **no se despliega sin F-024** |
| 2 | **F-018** | pasar a escritura real. Requiere F-017 firmada, **F-026** cerrada y autorización expresa (F-022 ya está) |
| 3 | **F-025**, **F-026** | obras de postventa desde POSTV2; recursos sin ficha de empleado |
| 4 | **F-024**, **F-027**, F-020 | selector de empresa; deshacer solo lo propio; Excel |

**Efecto visible de F-022 hasta que lleguen F-023 y F-024:** las líneas
imputadas a una obra que en el maestro local es la ficha de otra empresa (por
ejemplo 0009 y 0025, de Porsan) salen **omitidas con motivo** en el
preflight. Es lo seguro; se arregla limpiando el maestro.

## ⚠ Lo que espera al humano

1. **`git push`** de `dev` en `porcentajes` y de `main` en `arnes-base`.
   `azure-apps` no tiene remoto.
2. **Decidir** si la corrección de `ruesma_rep` («no es réplica, es la base
   documental») que tiene `azure-apps/dedicacion.md` se lleva a
   `docs/INTEGRACION.md`.
3. **Datos para F-023 y F-026**: la lista de recursos inactivos que señaló
   negocio (para T10 de F-023), las tres consultas de
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
