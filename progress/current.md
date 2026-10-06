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

- **Pedida por el humano el 2026-10-05** a partir del correo de Juan Romero
  «ARBOL ANALITICO OBRAS» (2026-09-29): cuentas analíticas por centro de
  coste de la obra; ejemplo, asiento con 6XX desglosado al 100 % en
  `0702.CP0004`. Escritura en Sigrid: rigor crítico, solo el transfer.
- **Exploración** (`progress/explore_F-037.md`): Sigrid YA genera el asiento
  analítico de cada parte (documento `ANA`, uno por obra y mes, lo lanza
  Administración por lotes): debe a `hmores.caaide` de cada línea, haber a
  `res.caaconide`; el 6XX lo pone la nómina. **El transfer escribe hoy
  `caaide = 0`**, así que sus líneas no entrarían en el ANA. Cero líneas
  `porcentajes:` en Sigrid a día de hoy.
- **Spec entregada** (`5dd3d75`), recomendada D1 = A: el transfer rellena
  `caaide` (`<obra>.CIMOxx` del tipo de hora) y no escribe asientos.
  **Espera al humano / Juan Romero** con D1-D11 abiertas
  (requirements §6).
- **Ajustada con la respuesta de Juan del 2026-10-05** (`4c3d7d1`): la
  cuenta analítica sale del TIPO DE HORA del recurso (540 de 540 líneas
  manuales), no de la partida; el centro (`hmores.cenide`) ya lo escribe
  bien el transfer; «Contabiliza parte…» deja el parte en `con.est = 10`
  (502 partes con ANA desde 2025). T0 bloquea: preguntas a Juan sobre el
  botón, MPRL (`CIMO16` o `CIMO04`) y escribir en un parte contabilizado.
- **Decisiones del humano (2026-10-05) aplicadas** (`52e1c02`): la cuenta
  sale del recurso con la regla de `partes` F-021 (`reshor.caaide`,
  subcuenta en el centro de la obra destino); un parte contabilizado va a
  un **complementario** (en Sigrid no hay convención: 9 casos de dos partes
  por obra y mes, sin enlace). **Abiertas para el humano:** D8, D10, D12,
  D13, D14 y **D15** (copiar `cuenta_analitica.py` de `partes` = ampliar la
  lista cerrada de `CLAUDE.md`, decisión expresa).
- **2026-10-06: aprobada por el humano con A en D8, D10 y D12-D15**
  (`3e6c7c4`); `CLAUDE.md` amplía la lista cerrada con `cuenta_analitica.py`
  (`b7ef1e6`). «Lo aprendido en partes» en design §13: la F-031 de `partes`
  (`feature/F-031-asiento-analitico`, en curso allí) añade el respaldo de la
  partida (R3) y entiende «cerrado» como estado ≠ 1. **Pendiente del humano:**
  D16 (qué estado manda al complementario) y si se espera a que la F-031 de
  `partes` llegue a su `dev` antes de copiar (sin ella, R3 queda `blocked`).
- **Riesgo vivo:** el transfer desplegado escribe en real; lo que se
  registre antes de F-037 queda con `caaide = 0` y fuera del ANA.
- **Fuera del proyecto (aviso al humano):** `partes-persistencia` también
  escribe `caaide = 0` en sus líneas `partes:`.

- **2026-10-06, nueva instrucción del humano:** no esperar a que la F-031 de
  `partes` llegue a su `dev`: revisarla en su rama y copiarla ADAPTADA, porque
  porcentajes y partes escriben en el MISMO parte. La condición de entrada de
  `tasks.md` (`655dbdc`) queda anulada.
- **Spec reescrita como copia adaptada de la F-031 de `partes`** (`497f224`;
  revisión de su rama en `progress/explore_F-037_partes_F-031.md`): copia
  literal de `estado_parte.py` y `cuenta_analitica.py` (rama `9b202e9`, sin
  cambios hasta `5ff4d91`) con test anti-divergencia; elección del parte,
  complementario, relectura, conflictos y avisos idénticos; corrige
  `siguiente_cod_pt` y el alta de `hmo` sin `emp`. **Pendiente del humano:**
  D13 reabierta (título `Parte <obra>` como partes), D17 (carrera entre
  servicios al crear el parte) y D18 (`estado_parte.py` a la lista cerrada).
- **2026-10-06: el humano aprueba D13 = `Parte <obra>`, D17 y D18**
  (`3fe200a`); `CLAUDE.md` con `estado_parte.py` en la lista (`32c33ad`).
- **Implementación terminada** (`progress/impl_F-037.md`, T1-T10 y T15,
  `6f97dc2`…`40b9feb`): copia literal de `partes` `9b202e9` con test
  anti-divergencia; mutación en serie 85/85 (y 25/25 en las copias sin el
  test de copias; 13 huecos reales cerrados con tests). Tests anteriores:
  solo los dobles y la ancla de la lista cerrada. Desviaciones declaradas en
  el informe §3 (p. ej. `partes_existentes` se queda porque la usa el script
  de prueba). **Review lanzada** → `progress/review_F-037.md`.
- **T14 (líder): hecha**, piezas de INTEGRACION copiadas a `azure-apps`
  (`5416cd1`, «sin desplegar»).
- **T11 (humano): pendiente.** Pasar a la sesión de `partes` el aviso de la
  carrera al crear el parte (D17) y del hueco de `OrigenSubcuenta` sin test
  de inmutabilidad. INTEGRACION §7 ya dice «`partes` está avisado»: será
  cierto antes del `done`.
- **Observación del implementer para el humano:** preexistente, la capacidad
  no se evalúa en un periodo sin ningún parte (dos líneas nuevas del mismo
  recurso que sumen > 1 no avisan). Se le propone abrirla como feature.
- **MANUAL (humano):**
  - **T12, solo lectura:** transfer de la rama con `OBRA_PRUEBAS_FORZAR=true`
    y api local; en un periodo de prueba con un MENC o MJEFO y un MPRL:
    `curl -s -X POST "http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight" -H "Content-Type: application/json" -d "{}"`.
    Esperado: MENC/MJEFO `escribir` con `caa_cod` `0404.CIMO03`/`CIMO02` y
    `caa_origen` `recurso`; MPRL con `caa_ide` 0 y aviso de `.CIMO16`; en
    `partes[]` el `estado`, `complementario` y `aviso`. NO `ejecutar`.
    Resultado: _pendiente_.
  - **T13:** escritura en modo pruebas en la 0404 con autorización expresa
    y Administración avisada (pasos en `tasks.md`). Resultado: _pendiente_.

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
(asiento analítico, en spec); después F-028, F-021, F-030, F-020 (Excel), **F-038**
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
