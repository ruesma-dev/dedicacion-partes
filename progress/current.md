<!-- progress/current.md -->
# Trabajo en curso

**Ninguna feature en ejecución ni bloqueada.** Rama `dev`, portero en verde.

El sistema está **desplegado y en uso**: se entra por la tarjeta «Dedicación»
del Portal Ruesma y hay 8 personas con acceso.

## Estado del backlog (14 features)

| Estado | Features |
|---|---|
| `done` | F-001, F-002, F-003, F-004, **F-008**, F-009, F-013, F-015 |
| `pending` | F-005, F-006, F-011, F-012, F-014, F-016 |

Retiradas el 2026-08-20 por decisión del humano: **F-007** y **F-010**, que se
hacen en `arnes-base`. Su razonamiento sigue en `progress/history.md`.

## Lo siguiente, por prioridad

| # | Feature | Qué es |
|---|---|---|
| 5 | **F-005** | alinear los literales internos con el nombre «dedicación» |
| 6 | **F-006** | sanear la suite del transfer (un test que devuelve en vez de asertar) |
| 7 | **F-011** | que un trabajador no pueda tener dos códigos `M*` |
| 8 | **F-012** | el test de la épsilon compartida ata el transfer al monorepo |
| 9 | **F-016** | pedir a `sigrid-api` una function key de **solo lectura** para la api |
| 20 | **F-014** | los cabos de Sigrid y Administración |

## ⚠ Lo que espera al humano

1. **`git push origin dev`**: hay commits locales sin subir.
2. **F-014**, cuando quiera: avisar a Administración de las cuatro partidas
   duplicadas de POSTV2 (`656`, `664`, `680`, `693`), decidir quién firma la
   procedencia de las reglas P4/P5, y **mirar el primer preflight real que
   tenga líneas `M*` previas** — es la única forma de ver la Regla B
   (sobrecarga del 100 %) ejercitada contra datos de verdad.
3. **F-016**: preguntar al dueño de `sigrid-api` si puede emitir una clave de
   solo lectura. Hoy api y transfer comparten la misma, y lo único que impide
   que la api escriba en el ERP es que su código no tiene rutas de escritura.

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
  «no hay tests» (pytest código 5) con «los tests fallan», y **la caché de
  suites cruza ramas**.
- **Los scripts de `infra/` solo se prueban ejecutándolos contra Azure**: cinco
  bugs salieron así, ninguno lo habría cazado un test offline.
- **Un fichero de rastro puede contener información única.** Resolver su
  conflicto de merge reescribiéndolo la destruye en silencio: pasó con el
  volcado de T13 y se recuperó del historial.
