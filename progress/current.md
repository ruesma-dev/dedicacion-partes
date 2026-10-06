<!-- progress/current.md -->
# Trabajo en curso

**F-039 en curso** (obras VAR y de 6 dígitos; implementada, en review), rama
`feature/F-039-obras-var-y-seis-digitos`. F-037 se cerró el 2026-10-06 y está en
`dev` **pendiente de desplegar** (sección siguiente). F-029 se desplegó el
2026-10-06 (resúmenes en `history.md`). El arnés es la **1.7.3**.

## F-039 · Obras VAR desde la 29 y fuera las de 6 dígitos (en curso)

- **Qué es** (pedida el 2026-10-06; spec `specs/F-039-obras-var-y-seis-digitos/`,
  aprobada con D1-D6): las partidas de la obra VAR desde la 29 se ofrecen como
  obras propias `VAR-NN` (universo en el transfer, `POST /api/var/universo`;
  registro en VAR con la partida fija); VAR deja de ofrecerse como obra normal;
  se ignoran las obras cuyo código contiene 6+ dígitos seguidos (240).
- **Implementación** (`progress/impl_F-039.md`): cobertura 181/181, mutación en
  serie 60/60; tests anteriores, solo los de design §7.1. **Review 1: CAMBIOS
  PEDIDOS solo por este fichero**, corregidos por el líder; código, tests,
  mutación y docs dados por buenos hasta `3b531ac`. **Review 2: APROBADO.**
  Para el `done` solo faltan las MANUAL T12-T14 del humano; no se mergea a
  `dev` hasta entonces.
- **T9 (líder): hecha**, copia a `azure-apps` `f01156f` («sin desplegar»).
- **MANUAL (humano, NADA escribe en Sigrid).** Arranque, en ventanas aparte y
  desde esta rama: `python main.py` con la `.venv` de cada servicio en
  `services/dedicacion-transfer` y en `services/dedicacion-api` (la api con
  `PG_HOST=localhost`). Luego, desde la raíz:
  - **T12 (M1):** `powershell -ExecutionPolicy Bypass -File scripts/verif_f039_var.ps1 -Paso M1`
    → `excluidas_por_codigo = 240`, `entradas_var = 1`, `VAR-29` activa en el
    cuadrante, sin `VAR` normal ni obras de 6+ dígitos; `RESULTADO M1: OK`.
    **Resultado (2026-10-06, humano): CUMPLIDA.** Preview: brutas 923, total
    289, `excluidas_por_codigo` 240, `entradas_var` 1, `obra_var` VAR, motivos
    nulos. Sync local: obras 289 recibidas, 240 desactivadas. Cuadrante:
    `VAR-29` (ide -417055, activa), sin VAR normal, sin `150414`, 0 obras
    activas con 6+ dígitos. `RESULTADO M1: OK`.
  - **T13 (M2):** `powershell -ExecutionPolicy Bypass -File scripts/verif_f039_var.ps1 -Paso M2 -Anio AAAA -Mes MM`
    (periodo de prueba LOCAL) → grupo de la obra `VAR`, `escribir`,
    `paride = 417055`, `partida_cod = "29"`, `partida_metodo = "var"`;
    `RESULTADO M2: OK`. Resultado: _pendiente_.
  - **T14 (M3, usabilidad):** además `python main.py` en
    `services/dedicacion-front` y abrir `http://127.0.0.1:8080`; buscar «29» y
    «arroyo» → `VAR-29`; no salen `VAR` ni `150414`; Completar al 100 % hacia
    `VAR-29`; «Registrar en Sigrid» enseña la partida fija «29» (cerrar SIN
    registrar). Resultado: _pendiente_.
  - **Despliegue:** orden transfer → api → front.
- **Observaciones de la review 1, recogidas:** `registro_sigrid.py` da 0
  mutantes automáticos (lo cubren dos mutantes a mano) y la 1.ª campaña dio
  dos falsos supervivientes → encargo de `arnes-base` (falsos supervivientes /
  generador).

## Features con spec aprobada, en cola (copias de trabajo aparte)

- **F-040 · Excel como el modelo de Juan** (prioridad 1; absorbe F-020): spec
  aprobada con D1-D6 = A (`c16af41`) en `PycharmProjects/porcentajes-f040`,
  rama `feature/F-040-excel-modelo-juan`. Corrige además la notación
  científica del Resumen actual («0702 = 1E+2%»). **Implementer lanzado en
  su copia el 2026-10-06** con F-039 ya aprobada y a la espera solo de las
  MANUAL del humano (dos ramas en curso a la vez, por decisión del humano de
  trabajar en paralelo; en cada rama solo hay una `in_progress`).
- **F-041 · Filtro de obra con el texto visible** (prioridad 3): spec aprobada
  con D1-D4 = A (`9b5fc46`) en `PycharmProjects/porcentajes-f041`, rama
  `feature/F-041-filtro-obra-postventa`. La causa real: el buscador global no
  casa con `Postv-` y la columna mezcla chips.
- Las dos copias tienen los `.venv` como uniones a los de esta carpeta.

## ⚠ Despliegue de F-037 (pendiente; lo lanza el humano)

- Cambia **solo el transfer** (`.\redeploy_dedicacion.ps1 -Solo transfer`,
  desde `dev`); el transfer desplegado ya escribe en real
  (`OBRA_PRUEBAS_FORZAR=false`), no hay que tocar permisos ni variables. Sin
  DDL ni sync.
- **Comprobación tras desplegar:** un preflight de producción (solo lectura)
  con una línea MENC o MJEFO: `caa_cod` `<obra>.CIMO0x`, `caa_origen`
  `recurso`. Desde ese momento, lo registrado lleva la cuenta analítica.

## Producción, hoy

- **Desplegado el 2026-10-06: F-029** (api `r20261006-1140`, front
  `r20261006-1141`): selección múltiple con Ctrl/Shift y «Completar al
  100 %» (tecla C). **Comprobación pendiente:** un trabajador en FALTA,
  Ctrl+clic, C, confirmar la obra → 100 %; Ctrl+Z lo devuelve.
- **Desplegado el 2026-10-05: F-027** (solo la api, `r20261005-0915`): cada
  usuario solo deshace lo suyo. **Comprobación pendiente, con dos personas
  (A y B) en el mismo mes y trabajador:** A guarda → B no ve el botón y su
  Ctrl+Z enseña «La última modificación de este trabajador es de A…»; A
  deshace bien; si B guarda después de A, A ya no puede.
- **Desplegado el 2026-10-03: F-025** (transfer `r20261003-1444`, api
  `r20261003-1446`, front `r20261003-1447`, en orden transfer → api → front).
  Preview de producción: `admiten_postventa` 83, `solo_postventa` 73,
  `motivo_postventa` nulo. **Sync hecho y `Postv-0656` visible en el
  cuadrante** (confirmado por el humano el 2026-10-05): ya se puede
  registrar postventa con normalidad.
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
- **El script de vaciado ya funciona contra Azure** (F-035, 2026-10-03): usa
  `psql` y lee la contraseña de `PG-PASSWORD` del Key Vault. `-SoloRecuento`
  cuenta sin escribir: el 2026-10-03 dio 0 asignaciones, 0 eventos, 1
  periodo y 196 trabajadores.

## F-028 · Borrar lo filtrado (plan aprobado, va después de F-037)

- Plan aprobado por el humano el 2026-10-06 con **A** (siempre todo lo
  visible). Detalle en la descripción de `features.json`.

## Recursos cerrados en bloque en Sigrid (2026-10-05)

- Correo de Miguel Ángel: recursos que salen en agosto y no en septiembre.
  Causa comprobada en Sigrid: el 2026-08-06 se cerraron en bloque 46 fichas
  de recurso de personas que se fueron en 2024-2025; por la regla de F-026
  cuentan en agosto. **Decisión del humano: opción B** (que Administración
  corrija la fecha de baja en Sigrid) y **spec de la A** como F-036, sin
  implementar de momento.

## Lo siguiente, por prioridad

`BACKLOG.md` tiene el orden completo (reordenado por el humano el
2026-10-06): **F-040** (Excel), **F-038** (cuadro de mando = el Excel
navegable), **F-041** (filtro de obra), **F-039** (en curso, implementada),
F-028 (plan aprobado), F-021, F-030, F-036 (solo spec de momento), F-031,
F-033 y, detrás, F-017, F-018… F-037 está cerrada y pendiente de desplegar
(sección de despliegue).

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

7. **F-037, complementario en real (aplazado por el humano el 2026-10-06):**
   probar con Administración que, con el parte del mes contabilizado, una
   línea nueva va a un complementario `Parte <obra>`. Los tests lo cubren;
   en Sigrid no se ha visto.
8. **F-037, aviso a `partes` (T11):** ya recogieron la carrera (D17, su
   `9ea7c59`); falta pasarles el test de inmutabilidad de `OrigenSubcuenta`.
   Su DA11 pondrá en rojo `test_f037_copias_partes.py::…ref_vigilada`:
   recopiar y mover `COMMIT_COPIADO`.
9. Decidir si se abre como feature lo que vio el implementer de F-037: la
   capacidad no se evalúa en un periodo sin ningún parte (dos líneas nuevas
   del mismo recurso que sumen más del 100 % no avisan). Preexistente.

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
