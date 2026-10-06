<!-- progress/current.md -->
# Trabajo en curso

**F-037 en curso** (asiento analítico, rigor crítico), rama
`feature/F-037-asiento-analitico-obra`. F-029 se cerró el 2026-10-05 y está en
`dev` **pendiente de desplegar** (sección siguiente). F-027 se desplegó el
2026-10-05 (resúmenes en `history.md`). El arnés es la **1.7.3**.

## ⚠ Despliegue de F-029 (pendiente; lo lanza el humano)

- Cambian la **api** y el **front** (`redeploy_dedicacion.ps1 -Solo api,front`,
  que respeta el orden api → front); sin DDL (`evento.tipo` es texto) ni sync.
- **Comprobación tras desplegar:** en producción, seleccionar con Ctrl+clic a
  un trabajador en FALTA, pulsar C, confirmar la obra y ver que queda al
  100 %; Ctrl+Z lo devuelve. No hace falta registrar en Sigrid.

## Producción, hoy

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

## F-037 · El registro genera el asiento analítico de la obra (en curso)

- **Qué es** (pedida el 2026-10-05; correo de Juan Romero «ARBOL ANALITICO
  OBRAS»): Sigrid YA genera el asiento analítico de cada parte (`ANA`, botón
  «Contabiliza parte…», que deja el parte en Imputado); el 6XX lo pone la
  nómina. El transfer escribía `hmores.caaide = 0` y sus líneas no entraban en
  el `ANA`. **F-037 rellena `caaide` y no escribe asientos** (D1 = A).
- **Spec aprobada** (D1-D18 decididas el 2026-10-05 y 2026-10-06; resumen en
  `history.md` al cerrar): copia ADAPTADA de la F-031 de `partes`, porque los
  dos escriben en el MISMO parte. Copia literal de `estado_parte.py` y
  `cuenta_analitica.py` (rama de `partes` `9b202e9`; lista cerrada de
  `CLAUDE.md` ampliada, `b7ef1e6` y `32c33ad`); complementario `Parte <obra>`
  (D13); alta protegida (D17); cualquier estado ≠ En registro es cerrado (D16).
- **Implementación** (`progress/impl_F-037.md`, `6f97dc2`…`40b9feb`): cobertura
  219/219; mutación en serie 85/85 (y 25/25 en las copias sin el test de
  copias). Tests anteriores: solo dobles y la ancla de la lista cerrada.
- **Review 1 (2026-10-06): CAMBIOS PEDIDOS solo por el rastro** (este fichero y
  la `acceptance` de `features.json`), corregidos por el líder; código, tests,
  mutación y docs dados por buenos hasta `ac125cb`. **Review 2: APROBADO.**
  NO se mergea a `dev` hasta cumplir T12 y T13 (para que un despliegue
  desde `dev` no lleve F-037 sin verificar en Sigrid).
- **T14 (líder): hecha**, copia a `azure-apps` `5416cd1` («sin desplegar»).
- **T11 (aviso a `partes`):** `partes` YA recogió la carrera y el alta
  protegida de D17 (su commit `9ea7c59`). **Falta avisarles** del hueco de
  `OrigenSubcuenta` sin test de inmutabilidad (lo pasa el humano). Además su
  DA11 cambiará la cabecera de las copias: pondrá en rojo
  `test_f037_copias_partes.py::…ref_vigilada` y habrá que **recopiar** y mover
  `COMMIT_COPIADO` (design §12: «texto, se recopia»).
- **Observación del implementer, propuesta al humano como feature:** la
  capacidad no se evalúa en un periodo sin ningún parte (dos líneas nuevas del
  mismo recurso que sumen > 1 no avisan). Preexistente.
- **MANUAL (humano), API y transfer LOCALES desde esta rama:**
  - **T12, solo lectura.** Transfer con `OBRA_PRUEBAS_FORZAR=true` y api con
    `TRANSFER_BASE_URL=http://127.0.0.1:8006`; periodo de prueba local con un
    MENC o MJEFO y un MPRL:
    `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight" -H "Content-Type: application/json" -d "{}"`.
    Esperado: MENC/MJEFO `escribir` con `caa_cod` `0404.CIMO03`/`CIMO02` y
    `caa_origen` `recurso`; MPRL con `caa_ide` 0 y aviso de `.CIMO16`; en
    `partes[]` `estado`, `complementario` y `aviso`. **NO `ejecutar`.**
    **Resultado (2026-10-06, humano, octubre 2026, 7 obras forzadas a 0404):
    CUMPLIDA.** 11 acciones `escribir`: MENC → `0404.CIMO03` y MJEFO →
    `0404.CIMO02`, `caa_origen` `recurso`; MPRL → sin cuenta,
    `caa_motivo` `obra_sin_cuenta` y aviso «la obra 0404 no tiene la cuenta
    analitica .CIMO16». Parte de 0404 2026-10 inexistente: se crearía
    `PT26/00343`, `complementario` falso, sin cerrados (el camino del
    complementario se ejercita en T13). La MPRL trae además el conflicto
    `sin_partida` de F-013 (preexistente, no de F-037).
  - **T13 — AUTORIZADA por el humano el 2026-10-06 («autorizo»).** Paso 1
    hecho por el humano (`ejecutar` con `trabajador_ide` 2750167): creado
    `PT26/00343` (con.ide 2848891, est 1, «Parte CUBIERTA NAVE 14 - JOHN
    DEERE (PRUEBA-PORC)», fec 20261031, obra 828942, centro 828943); 2 líneas
    (`porcentajes:124` y `:125`, hmores 408963-408964, MENC 0,5 × 6.000 =
    3.000 cada una) con `cenide` 828943 y `caaide` 829178 = `0404.CIMO03`,
    `tex` PRUEBA-PORC. Leído por el líder (solo lectura). Siguiente: paso 3
    (Administración contabiliza `PT26/00343`).
  - **T13, ESCRITURA en modo pruebas (0404).** Condición previa: autorización
    expresa del humano para esta acción y Administración avisada. Pasos:
    1. `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/ejecutar" -H "Content-Type: application/json" -d "{\"trabajador_ide\": <ide>}"`
       (mes sin actividad en 0404). Esperado: la línea `registrado`.
    2. Lectura, desde `services/dedicacion-api` con `PYTHONPATH=.`:
       `.venv/Scripts/python -c "from config.settings import get_settings; from infrastructure.sigrid.sigrid_client import SigridApiClient as C; print(C(get_settings()).leer(\"SELECT hmores.caaide, cc.cod AS cuenta, pt.cod AS parte, pt.est, hmores.cenide, hmores.tot FROM hmores JOIN con pt ON pt.ide = hmores.hmoide LEFT JOIN con cc ON cc.ide = hmores.caaide WHERE hmores.synckey = 'porcentajes:<id>'\"))"` (Git Bash; `<id>` = el `registro_id` de la línea: el transfer desplegado escribe en real y `LIKE` traería líneas reales).
       Esperado: `caaide` ≠ 0, `cuenta` `0404.CIMOxx`, `cenide` el de 0404,
       parte `est` 1.
    3. Administración pulsa «Contabiliza parte…»: parte en `est` 10 y `ANA` con
       debe a `0404.CIMOxx` por `tot` y haber a `CP.<persona>`; confirma que la
       línea se ve como una tecleada.
    4. Otra línea del mismo mes (paso 1 con otro trabajador): va a un
       complementario `Parte 0404 …` nuevo, que se contabiliza aparte.
    5. Limpieza, desde `services/dedicacion-transfer`:
       `.venv/Scripts/python prueba_escritura_porcentajes.py limpiar` (dry-run)
       y luego `… limpiar --confirmar`; Administración anula los `ANA` y el
       complementario.
    Resultado: _pendiente_.

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
2026-10-05: F-028, F-021, F-029 y F-030 delante de F-020; F-037 nueva y
primera). **F-029 espera a que el humano decida desplegar.** Ahora **F-037**
(asiento analítico, en curso, sección de arriba); después F-028, F-021, F-030, F-020 (Excel), **F-038**
(pestaña de analítica, pedida el 2026-10-06 justo detrás del Excel), **F-036**
(solo spec de momento), F-031, F-033 y, detrás, F-017, F-018…

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
