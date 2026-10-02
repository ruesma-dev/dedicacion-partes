<!-- progress/current.md -->
# Trabajo en curso

**F-035 en curso** (script de vaciado contra Azure, rigor estándar, sin spec),
rama `feature/F-035-vaciado-psql-azure`. F-034 y F-026 se cerraron y se
**desplegaron el 2026-10-02** (resúmenes en `history.md`). El arnés es la **1.7.3**.

## F-035 · El vaciado contra Azure sin pasar la contraseña por `cmd.exe`

- **Plan aprobado por el humano el 2026-10-02** (PARADA 1). Criterios en
  `harness/features.json`. Resumen: el vaciado usa `psql` también en Azure
  (FQDN por `az … show`, `PGPASSWORD` + `PGSSLMODE=require` solo durante la
  llamada); conmutador nuevo `-SoloRecuento` (cuenta y sale, sin escribir);
  `crear_base` y `add_secrets` rechazan contraseñas con `" & | < > ^ %`
  antes de llamar a `az`; resultado de la revisión de `infra/` en
  `infra/README_dedicacion.md`.
- **Fuera:** volver a vaciar producción, cambiar la contraseña de
  `dedicacion_app`, firewall o cualquier cosa del servidor, `azure-apps`.
- **Test anterior que cambia (declarado):** `test_f026_r10_solo_en_la_base_dedicacion`.
- **Estado:** implementer lanzado. Informe: `progress/impl_F-035.md`.
- **MANUAL (humano, al final, NO escribe nada):** comandos exactos en
  `progress/impl_F-035.md` cuando el implementer termine.

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
- **El script de vaciado no funcionó contra Azure** (la contraseña se corrompe
  al pasar por `cmd.exe`); se hizo a mano con `psql`. Corrección: **F-035**.

## Lo siguiente, por prioridad

`BACKLOG.md` tiene el orden completo. Primero **F-035** (script de vaciado
contra Azure); después **F-025** (spec
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
