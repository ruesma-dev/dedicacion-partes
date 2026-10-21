<!-- progress/current.md -->
# Trabajo en curso

**En curso: F-030** (incidencias en el cuadrante; `sdd: true`, rigor
crítico), `in_progress` desde el 2026-10-21, en la copia
`C:\Users\pgris\PycharmProjects\porcentajes-f030`, rama
`feature/F-030-dias-bajas-incidencias` (`dev` fusionado: F-051 desplegada,
F-059 y F-060); sus `.venv` son uniones de directorio a los de la copia
principal (del líder, no versionadas). Spec aprobada el 2026-10-20 (D1-D10).
T1-T19 y T21 hechas; review 1 **RECHAZADO** por R30; el humano eligió la
opción **C** y **aprobó el anexo R30 el 2026-10-21** («si»: D11 = B, D12-D15
= A, todas la recomendada). **Implementer lanzado el 2026-10-21 para
T22-T37.** T20: primera mitad hecha por el líder en la 0404
(`progress/manual_F-030.md`); la segunda (cambio de días), tras T37, con
autorización expresa del humano. Ningún agente escribe en Sigrid por su
cuenta. El arnés es la **1.7.3**.

**Pendiente del humano:** la comprobación de F-051 en producción (Ctrl+F5;
un registro con una línea `M*` al 0 % en el parte la edita en su sitio y el
modal lo avisa; un pisado dice «se edita la línea X (…) y se escribe N%»).
**Aviso a `partes`** (lo transmite el humano; aquí no se toca `partes`):
desde F-051 el transfer de dedicación **edita en su sitio** líneas `M*` de
los partes compartidos (también las que tengan `synckey partes:…`, sin
cambiarla) y no borra ninguna; su `partes.md` debería decirlo.

## F-030 · anexo R30: implementación EN CURSO (implementer, 2026-10-21)

- **Tarea en curso:** T32 (T31 hecha: `ejecutar` edita la `fec` (R45, R46) en la relectura única de F-051, el par o ninguna, relectura tras escribir; la mitad transfer del punta a punta pasó a XPASS estricto y su `xfail` se quitó en T31, no en T33, igual que la de la api en T26; `test_f030_r30_ejecutar_no_reescribe_*` reescrito otra vez (§13.7) con el par en el parte. T30 hecha: preflight y lote reconcilian antes del paso 5 con los `ide` de la traza; `deduplicar` eliminado, sus tests propios pasan por `reconciliar` con un adaptador local y `test_f030_r30_deduplicar_*` y `test_f030_r30_ejecutar_no_reescribe_*` reescritos (lista cerrada §13.7). T29 hecha: `reconciliar` puro. T28 hecha: cliente, lectura por `ide` y `UPDATE` de la `fec`. T27 hecha: contrato del transfer. T26 hecha: traza R39, payload y quitadas; la mitad api del punta a punta ya pasa y su `xfail` estricto se quitó en T26, no en T33 (con la marca, el XPASS ponía la suite en rojo). T25 hecha: deshacer R47. T24 hecha: guardar por `id` y quitadas. T23 hecha: esquema; T22 hecha: contrato `tests/contratos/f030_r30.json`
  y sus dos mitades en `xfail(strict=True)`).
- **Decisiones:** los cuatro campos del contrato api → transfer se llaman
  `hmores_ide_ini`, `hmores_ide_fin`, `dia_ini` y `dia_fin` (design §6 no
  los nombra); la api solo los manda si la incidencia está registrada.

## F-030 · anexo R30 escrito (spec-author) y APROBADO (humano, 2026-10-21)

- **Qué**: anexo a la spec por la obs. 1 de la review 1 y la opción C del
  humano. `requirements.md` §8 (R36-R49) y R30 reescrito; `design.md` §11
  (D11-D15), §12 y §13; `tasks.md` T22-T37 y T20 ampliada. Informe:
  `progress/spec_F-030.md` §«Anexo R30». Topes: 150/150 y 243/250. Ni código
  ni Sigrid tocados.
- **Para caber en los topes**, el texto ya implementado o decidido del design
  (§2, §3, §5, §10, §11 de antes) se ha movido **sin cambios** al informe y el
  design guarda su resumen; la redacción de R1-R35 se ha apretado sin quitar
  ningún requisito.
- **D11-D15 DECIDIDAS** por el humano el 2026-10-21 («si», todas la
  recomendada): **D11 = B** (quitar una registrada la deja `quitada`, tachada
  «sigue en Sigrid» y listada en el modal para retirarla a mano; nunca se
  borra; deshacer la repone); **D12 = A** y **D13 = A** (cambiar tipo u obra
  = quitar + nueva); **D14 = A** (línea nuestra cambiada a mano en Sigrid: no
  se toca y se avisa; borrada, se reescribe); **D15 = A** (día nuevo con una
  igual ajena: no se edita y se avisa). Implementer lanzado para T22-T37.
- **MANUAL T20 ampliada** (tras T37, con autorización expresa): además de lo
  anterior, desde `services/dedicacion-transfer` con
  `OBRA_PRUEBAS_FORZAR=true`:
  `python prueba_escritura_porcentajes.py preflight --ano 2026 --mes 10 --incidencia RECURSO:CIV:6:12`,
  `… ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:6:12`
  y `… verificar --incidencia RECURSO:CIV:6:12`: los **mismos dos `ide`** que
  dio el registro del 5 al 9, con `fec` 6 y 12, y ninguna línea nueva.
- **azure-apps** (líder, al desplegar): `dedicacion.md` dirá también que el
  transfer edita la `fec` de sus líneas `CI*`/`CIZ`; avisar a `partes`.

## F-030 · spec escrita y aprobada (D1-D10 decididas, 2026-10-20)

- **Petición del humano (2026-10-20)**, literal en `features.json`: en la
  celda del %, si se escribe texto, desplegable con las incidencias de
  `partes`; con número, todo igual que hoy.
- **Spec**: `specs/F-030-dias-bajas-incidencias/` (requirements 150/150,
  design 250/250, tasks T1-T21). Informe: `progress/spec_F-030.md`.
- **Toca los tres servicios**: front (desplegable al teclear letras en la
  celda del %, chips y subfilas), api (catálogo desde Sigrid, tabla
  `incidencia`, evento y deshacer, payload) y transfer (par `CI*`/`CIZ`).
- **Decisiones del humano** (requirements §7, todas la recomendada,
  2026-10-20): D1 fuente de la lista (A: `auxhor` de Sigrid); D2 fechas
  (A: tramo de días del mes obligatorio); D3 tramo que cruza meses (A: cada
  mes con su `CIZ`); D4 100 % (A: no cuenta); D5 qué se escribe (A: par
  `CI*`/`CIZ`, `can = 0`); D6 partida (A: la de la línea de % de esa obra o
  0); D7 duplicados y obras (A: misma `fec` y código en cualquier obra del
  mes; solo obra normal); D8 alcance (A: captura y registro en F-030); D9
  línea recién añadida (A: se convierte en incidencia); D10 % por días,
  calendario de convenio y bandeja de `partes` (fuera, features nuevas).
- **MANUAL de la feature** (T20): prueba en modo pruebas en la `0404`; la
  ejecuta el líder con autorización expresa del humano. **Primera mitad
  hecha el 2026-10-21** («autorizo pruebas de f30»; `progress/manual_F-030.md`:
  `ide` 411730/411731, `ya_registrado`, limpia); la segunda, tras T37. Comando exacto, desde `services/dedicacion-transfer` con
  `OBRA_PRUEBAS_FORZAR=true` y `RECURSO` = un `res.ide` con `CIV` y `CIZ` en
  `reshor` (p. ej. 1705036):
  `python prueba_escritura_porcentajes.py preflight --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9`,
  `… ejecutar --confirmar --ano 2026 --mes 10 --incidencia RECURSO:CIV:5:9`,
  `… verificar --incidencia RECURSO:CIV:5:9`, otra vez `ejecutar` (debe dar
  `ya_registrado`) y `… limpiar --confirmar`. **Lo que deja sin probar su
  ausencia** (review 1): que SQL Server y sigrid-api acepten el `INSERT` del
  par `CI*`/`CIZ` y la lectura de las `CI*` del mes (R27); el resto está
  cubierto por tests. Con la opción C de R30 se añade el cambio de días.
- **azure-apps**: `dedicacion.md` lo actualiza el **líder al desplegar**
  (no en T19); `partes.md` (de
  `partes`) debería decir que `porcentajes` escribirá `CI*`/`CIZ` en los
  mismos partes: avisar al humano.
- Sigrid, solo lectura durante la spec (consultas en `progress/spec_F-030.md`).

## F-030 · implementación: TERMINADA, lista para review (implementer, 2026-10-21)

- **Estado:** T1-T19 y T21 `[x]`, cada una con su commit `F-030 Tn`. El
  informe está en `progress/impl_F-030.md` y la mutación en
  `progress/mutacion_F-030.md`. **T20 (MANUAL) es del líder** y exige
  autorización expresa del humano. Su comando exacto está en el informe §6:
  transfer local con `OBRA_PRUEBAS_FORZAR=true` y
  `prueba_escritura_porcentajes.py preflight|ejecutar --confirmar|verificar
  --incidencia RECURSO:CIV:5:9`, repetir `ejecutar` y `limpiar --confirmar`.
- **Fusión de `dev` (F-051) antes de T15:** commit `46cf116`, conservando
  los dos comportamientos. Las incidencias quedan fuera de pisados,
  sobrecarga y líneas al 0 %, y comparten la relectura de F-051.
- **`bash harness/init.sh`:** en verde sobre `8b17e85` (con la caché de suites borrada): raíz 418 (+1 skipped), api 1.083, front 350, transfer 1.168; cobertura de líneas cambiadas 99,5 % (634/637); tamaño 150/150 y 250/250.
- **Mutación:**
  - 1.ª campaña (en serie, sin muestreo): 251 mutantes, 31 supervivientes,
    todos huecos reales. Les puse tests (`42c0fb5`) y reescribí la
    comprobación del lote que miraba solo la primera línea del par.
  - 2.ª campaña: 250 mutantes, 1 superviviente (el test del log tenía cuentas simétricas; corregido en `8b17e85`). **3.ª campaña: 250 mutantes, 0 supervivientes**, en serie (`--workers 1`) y completa, sin muestreo.
- **Desviaciones justificadas** (informe §2):
  - La traza de la incidencia va en `application/traza_incidencias.py`, no
    en `registro_sigrid.py`, para no tocar `test_f003_r17`. Un test igual la
    vigila contra las columnas de `incidencia`.
  - Sin incidencias, ni el kwarg ni la clave de respuesta `incidencias`
    (R2 literal).
  - Con `--incidencia`, el script manda solo las incidencias.
- **Lista cerrada de tests ajenos:** la tabla exacta está en el informe §3.
  Solo dobles, salvo la aserción de f013 (opción A del humano).
- **Pendiente del líder al desplegar** (orden transfer → api → front):
  - `azure-apps/dedicacion.md` (R34) debe decir que leemos `auxhor` y
    escribimos `CI*`/`CIZ` con `can = 0` y `synckey porcentajes:inc:`, más
    las rutas nuevas.
  - Avisar a `partes` de que su `azure-apps/partes.md` debería decir que
    `porcentajes` escribe `CI*`/`CIZ` en los mismos partes.
- Nada escrito en Sigrid; ningún `push`.

## F-030 · implementación: bloqueo de T14 RESUELTO (implementer, 2026-10-21)

**Resuelto por el humano el 2026-10-21 con la opción A** («a»): la aserción
de `test_f013_r3_la_confirmacion_no_estrena_canal` acepta `incidencias`
(`tasks.md`, cabecera). F-030 vuelve a `in_progress`; el implementer sigue
en T14. **Estado al bloquear:** `blocked` (ya no). Hechas T1-T14, cada una con su commit y su traza RED
(T10 `fc039a7`, T11 `d407bf6`, T12 `4207de3`, T13 `07671d3`, T14 `3e63ba7` +
`1cde163`). Api 1063 y front 341 en verde (tras T9); **transfer 986 en verde
y 1 en rojo**, el de abajo. Nada escrito en Sigrid; todos los dobles ajenos
adaptados hasta aquí son los de la lista cerrada (sin ninguna aserción).

**Motivo: un test ajeno exige cambiar una ASERCIÓN.**
`services/dedicacion-transfer/tests/test_f013_sin_partida.py::test_f013_r3_la_confirmacion_no_estrena_canal`
fija la firma literal de `RegistroPipeline.ejecutar`:
`["self", "obra", "lineas", "pisar_claves", "usuario"]`. T14 (R23, R24;
design §3: «`ejecutar` inserta sus líneas en los mismos lotes») necesita que
`ejecutar` reciba las incidencias de la petición, y se lo pasé como
parámetro nuevo, opcional y al final (`incidencias=None`): la lista pasa a
tener 6 nombres. El test vigila otra cosa (que la **confirmación** de F-013
viaje por `pisar_claves` y no por un canal nuevo); las incidencias no son
una confirmación, pero la aserción es literal. El otro test que cayó
(`test_f055_lote.py::…cada_escenario…`, por el doble `_comparado` de
`f055_equivalencia_lote.py`) lo arreglé sin tocarlo: sin incidencias,
`ejecutar` llama a `preflight` exactamente como antes (`1cde163`).

**Opciones:**

- **A (recomendada).** Mantener `incidencias=None` en `ejecutar` y que la
  aserción de f013 sea `["self", "obra", "lineas", "pisar_claves", "usuario",
  "incidencias"]`, con la marca «F-030 (lista cerrada)» y una línea que diga
  que `incidencias` no es un canal de confirmación. Lo que vigila sigue
  vigilado: un parámetro de confirmación nuevo seguiría rompiéndolo. Es un
  cambio de una línea y se lista en `progress/impl_F-030.md`.
- **B.** No tocar la firma: un método público hermano (p. ej.
  `registrar(obra, lineas, incidencias, pisar_claves, usuario)`) con toda la
  lógica, `ejecutar` delegando en él sin incidencias, y `app.py` llamando a
  uno u otro. No cambia ningún test ajeno, pero deja dos entradas para la
  misma operación solo para respetar una aserción literal; no la recomiendo.
- **C.** Que las incidencias viajen dentro de `lineas` (lista mixta que el
  pipeline separa por tipo). No la recomiendo: rompe el tipo de `lineas` y a
  todos los que lo recorren.

**Para retomar:** con A, cambio esa aserción (commit propio, «F-030 T14:
f013 lista cerrada») y sigo con T15 (lote y `app.py`), T16-T19 y T21; T20 se
queda para el líder con su comando exacto (`tasks.md`).

## F-030 · implementación: bloqueo de T4 RESUELTO (implementer, 2026-10-21)

**Resuelto por el humano el 2026-10-21 con la opción A** («la a»): lista
cerrada de adaptaciones solo de dobles, sin cambiar ninguna aserción
(`tasks.md`, cabecera). F-030 vuelve a `in_progress`; el implementer sigue en
T4. Lo de abajo es el motivo y las opciones, tal como se plantearon.


**Estado al bloquear:** `blocked` (ya no). Hechas y con su commit T1
(`a5c0386`, test de lo de hoy en la celda del %, verde antes de tocar
`app.js`), T2 (`6c01edd`, `domain/incidencias.py`, con traza RED) y T3
(`44d74ab`, `TipoIncidenciaORM` e `IncidenciaORM`). Suite de la api en verde
en ese punto. Nada escrito en Sigrid; ningún test ajeno tocado.

**Motivo (lista cerrada de tests ajenos).** El diseño aprobado obliga a que
los **dobles de test** de 23 ficheros ajenos a la spec aprendan que existen
las incidencias. Medido con un experimento desechable (cambio mínimo de cada
causa, suite de la api, y revertido con `git checkout`; los números son
reales):

| Causa (diseño) | Qué cambia en producción | Tests que caen |
|---|---|---|
| A · R21 | `ObtenerCuadrante` y `ObtenerFilaTrabajador` leen `uow.incidencias` | 109 en 13 ficheros (los `_Uow` en memoria no tienen ese repositorio) |
| B · R20 | `ultimo_pendiente` lee `evento.tipo` para despachar el deshacer | 1: `test_f027_r3_ultimo_pendiente_trae_su_autor` (su `SimpleNamespace` no trae `tipo`) |
| C · R23 | `_payloads` hace una 2.ª lectura (las incidencias del mes) | 77 en 9 ficheros (las sesiones falsas devuelven las filas de asignación a cualquier `SELECT`) |
| D · R3 | el contenedor real compone el paso `auxhor` del sync | 8 en 3 ficheros (el Sigrid falso responde filas de empleado a `auxhor`, y su UoW no tiene `tipos_incidencia`); el preview sumará los de `test_f025_sync_postventa` |

Los dobles están casi todos centralizados: `_Uow` de
`test_f024_cuadrante_empresa.py` y de `test_f025_cuadrante_postventa.py`;
`_Sesion` de `test_f024_registro_empresa.py`, la de `test_f022_empresa_en_linea.py`,
`_SesionQueFiltra` de `test_f056_trabajador_ide.py` y el `_S` de
`test_f055_registro_lote.py`; `_SigridFalso`/`_UowEspia` de
`test_f023_sync_empresa.py` y `test_f032_empresas_sigrid.py`, y el
`SimpleNamespace` de `test_f027`. Unos 10 ficheros que editar; los demás
heredan.

**Opciones:**

- **A (recomendada).** Lista cerrada de adaptaciones **solo de dobles**,
  ninguna aserción cambia: los `_Uow` ganan un repositorio `incidencias`
  vacío; el `SimpleNamespace` de `test_f027`, `tipo="GUARDAR"`; las sesiones
  falsas del registro responden `[]` a la lectura de `incidencia`; el Sigrid
  falso del sync responde `[]` a `dbo.auxhor` y su UoW lleva
  `tipos_incidencia`. Cada cambio con la marca «F-030 (lista cerrada)», como
  hizo F-055, y la lista exacta en `progress/impl_F-030.md`. Para el front
  (T8, T9, T17), el mismo criterio: los estáticos de F-042/F-050 que ya
  admite el design §12, y los arneses de node que solo necesiten un doble
  nuevo; si alguno exigiera cambiar una aserción, vuelvo a parar.
- **A'.** Como A, pero sin tocar los 9 ficheros del registro (causa C): a
  `RegistroSigrid` se le inyecta un lector de incidencias opcional (patrón
  `sql_empresas=None` de `PreviewSync`), que el contenedor siempre pasa. No
  la recomiendo: el parámetro solo existe para no tocar dobles, y un
  cableado roto registraría sin incidencias sin avisar.
- **B.** Producción tolerante a dobles viejos (`getattr(uow, "incidencias",
  None)` y similares). No recomendada: lógica para tests en producción.
- **C.** Cambiar la spec: cuadrante y fila sin incidencias (endpoint aparte
  que el front pide), registro con lector inyectado. No evita la causa B,
  complica el front y reabre una spec aprobada.

**Para retomar:** con A, sigo en T4 (sync, repositorio, preview y cableado),
adaptando los dobles en la misma tarea que los rompe.

## F-051 · CERRADA y DESPLEGADA (2026-10-21)

**F-051** (pisar las líneas del parte
editándolas, nunca borrando) cerrada el 2026-10-21 y **desplegada el
2026-10-21** por el líder con permiso del humano («autorizo … despliegue de
f51»), transfer → api → front (ver «Producción, hoy»); T16 hecho
(`azure-apps/dedicacion.md` `223490c`).
Altas nuevas del 2026-10-21: **F-058** (un % que redondea a 0 no se
registra), **F-059** (% por días con el calendario de convenio) y **F-060**
(leer la bandeja de `partes`). El arnés es la **1.7.3**.
## F-051 · bloqueos de implementación (2026-10-20) · RESUELTOS

- **T3**: añadir `edita_ide` y `a_cero_ides` a `Conflicto` rompía
  `test_f013_r4_no_hace_falta_ningun_campo_nuevo`, fuera de la lista cerrada.
  Humano: **opción A** («a»): entra en la lista y su conjunto acepta los dos
  campos (`c5bc6e9`).
- **T12**: el texto nuevo del pisado rompía los dos `test_f049_r2_…`.
  Humano: **opción B** («La b»): el detalle termina como hoy, «se edita la
  línea X (…)[; quedan a 0: …] y se escribe N%»; esos tests no se tocan
  (`d0c1ab7`, hecho en `24ba7aa`).

## F-051 · implementación (implementer, 2026-10-20)

- **Estado:** T1-T14 y T17 `[x]`; informe en `progress/impl_F-051.md`.
  **Cambios de la review 1 hechos (2026-10-21):** test de la frontera de
  R13 que mata el mutante de `registro_pipeline.py:1095` (`d807cce`);
  formato de la línea 568 y de un docstring del lote (`7a5f801`); 3.ª
  campaña de mutación en serie (`--workers 1`) sobre `7a5f801`: **134
  mutantes, 0 supervivientes** (`e51ba7b`, `progress/mutacion_F-051.md`);
  primera línea con la ruta en el informe. Ya no hay ningún equivalente que
  aceptar. `init.sh` sin `[KO]`, cobertura 99,2 %. Listo para la pasada 2.
- **T18 hecha (2026-10-21, O2 aceptada por el humano, «ok o2»):** el paso 6
  exige además `es_linea_mensual` de la línea del `hmores_ide`; si no es
  `M*`, se sigue por `synckey` (`d5d61ac`, 4 tests nuevos con RED en el
  informe; docs `ARCHITECTURE` «Localizar lo nuestro» e `INTEGRACION` §5).
  R13 no cambia (no usa ese criterio; la guarda ya exige `M*`). 4.ª campaña
  en serie sobre `d5d61ac`: **136 mutantes, 0 supervivientes** (`6ca3074`).
  `init.sh` sin `[KO]`: transfer 1080, api 949, front 310, raíz 418;
  cobertura 99,2 %. O4 es F-058; T15, del líder.
- **Decisiones del implementer** (detalle en el informe §2):
  `lineas_registradas(claves, ides)` sin `ides` delega en
  `lineas_por_synckey`; `repartir_choques` y `es_nuestra_de_otra` puras
  nuevas; `despues` del log usa `a.can`/`a.tot` ya redondeados; `usadas`
  arranca vacío (una línea al 0 % nunca es choque).
- **Desviaciones justificadas:** la fase `estado` del script lee además
  `pos`, `paride` y `tex` (para T15); la api usa
  `getattr(a, "sigrid_hmores_ide", None)`; el paso 9 bis va antes del alta de
  partes y solo lo que inserta crea parte o lee `max_pos`.
- **T15 CUMPLIDA por el líder el 2026-10-21** (modo pruebas, 0404,
  escrituras autorizadas por el humano). Detalle en
  `progress/manual_F-051.md`; resumen en `progress/impl_F-051.md` §6.
- **T16 HECHO el 2026-10-21** al desplegar (transfer → api → front):
  `azure-apps/dedicacion.md` `223490c` (§1, §5 y §7 desde
  `docs/INTEGRACION.md`). Aviso a `partes`: en «Pendiente del humano», arriba.

## F-051 · decisiones del humano sobre la spec (2026-10-20, todas cerradas)

- **Pasada 2:** «d1, nunca borramos lineas, editamos el valor. d5, cualquier
  linea a 0% se puede pisar». **D1 = C** (`UPDATE` en su sitio, nunca
  `DELETE`); **D5**: cualquier línea al 0 %, también con `synckey` de
  `partes` o nuestra. D2-D4 y D6-D9, las recomendadas (D2 = A sin confirmar,
  con aviso; D3 = A; D4 `can` 0 exacto o nulo; D6 = A; D7 = B; D8 fuera;
  D9 = A).
- **Pasada 3:** D10 = B (se edita todo lo que insertaríamos) y D13 como
  recomendado («ok a lo demás»). **D11:** «y no deberia encontrarla por el
  ide de sigrid una vez que se registra la linea? es unico y no se edita
  nunca» y «d11 que ya localice»: F-051 **no cambia la `synckey` de una
  línea de otro sistema** y localiza lo editado por `hmores.ide`; a una línea
  de Administración (`synckey` vacía) se le pone la nuestra. **D12:** «que
  pase a editar»: el pisado confirmado de hoy también pasa a `UPDATE`.
- **D14 = A y D15 = A** («si me vale»): con varios choques se edita el de
  menor `ide` y los demás a 0; `limpiar` (solo el script de pruebas) sigue
  borrando lo marcado `PRUEBA-PORC`.
- **Exploración (solo lectura, 10 `SELECT` por sigrid-api, base `ruesma`):**
  en octubre, parte PT26/00370 de la 0707 (En registro), cuatro personas con
  su línea `M*` a 0 (`hmores` 410600, 410931, 410935, 410937): copia de
  septiembre por Administración, sin `synckey`. En 2026, 63 grupos con
  varios choques (PT26/00109 llega a 9 líneas `MDEL`).

## Producción, hoy

- **Desplegado el 2026-10-21: F-051**, los tres servicios en orden, por el
  líder con `redeploy_dedicacion.ps1 -Solo transfer|api|front` (permiso del
  humano): transfer `r20261021-1611` (revisión
  `ca-dedicacion-transfer--r20261021161055`), api `r20261021-1613`
  (`…--r20261021161322`) y front `r20261021-1615` (`…--r20261021161520`), las
  tres `RunningAtMaxScale`, `Healthy` y con el 100 % del tráfico (`az
  containerapp revision list`). El transfer sigue en **modo real**
  (`OBRA_PRUEBAS_FORZAR=false`, `az containerapp show`) y arrancó sin errores
  (`containerapp logs`). El script volvió a cortarse tras cada `containerapp
  update` (el `Run-Az` de «Lo que espera al humano»). `infra/imagenes.json`
  al día en este commit; `azure-apps/dedicacion.md` `223490c`.
- **Desplegado el 2026-10-20: F-057**, api y front, en ese orden, lanzado por
  el humano con `redeploy_dedicacion.ps1 -Solo api` y `-Solo front` (esta vez
  sin cortarse): api `r20261020-1342` (revisión
  `ca-dedicacion-api--r20261020134227`) y front `r20261020-1351` (revisión
  `ca-dedicacion-front--r20261020135103`), las dos `RunningAtMaxScale`,
  `Healthy` y con el 100 % del tráfico (comprobado por el líder con `az
  containerapp revision list`). Transfer sin cambios.
  `azure-apps/dedicacion.md` al día (`a4c046c`). **Comprobado por el humano
  en producción el 2026-10-20:** «he revisado en real y funciona todo
  perfectamente».
- **Desplegado el 2026-10-19: F-056**, solo la api: `r20261019-1020`
  (revisión `ca-dedicacion-api--r20261019102033`, `RunningAtMaxScale`,
  `Healthy`, 100 % del tráfico; transfer y front sin cambios). El script volvió
  a cortarse tras el `containerapp update` (el `Run-Az` de «Lo que espera al
  humano»); la revisión se comprobó con `az containerapp revision list`.
  Comprobado por el líder en el navegador (solo preflight): `trabajador_ide`
  `""`, `false` y `"abc"` ⇒ 422 `trabajador_ide no es un entero: …`; `/health`
  200. `azure-apps/dedicacion.md` al día (`16dfece`).
- **Desplegado el 2026-10-17: F-055**, los tres servicios en orden: transfer
  `r20261017-1306`, api `r20261017-1310` y front `r20261017-1314` (revisiones
  `…--r20261017130616`, `…131025` y `…131348`, las tres `RunningAtMaxScale` con
  el 100 % del tráfico; el transfer sigue en **modo real**,
  `OBRA_PRUEBAS_FORZAR=false`, comprobado con `az containerapp show`). La api
  aplicó al arrancar las 5 columnas `asignacion.propuesta_*` («5 sentencias DDL
  aplicadas», sin errores). **C6 CUMPLIDA** (líder en el navegador, a petición
  del humano, «intenta hacerlo tu», 2026-10-18; septiembre 2026, solo preflight
  y **Cancelar**): GONZALEZ PANIAGUA 1,05 y 0,80 s (≤ 30 s; 0672 y 0694 por
  `parte_anterior`, mismas partidas que en local; el modal enseña la 0672 ya
  registrada, línea 409559, y la 0694 omitida por parte PT26/00319 cerrado);
  mes entero 8,37 s, 59 obras, 304 líneas, sin 502 ni obras con error (≤ 60 s);
  repreflight de la 0694 0,81 s. Las propuestas del mes ya estaban calculadas
  al abrirlo (`propuestas_en_curso: false`), así que no se vio «buscando
  partida…». O2 comprobada después pintando el mes en curso en la pestaña del
  líder (sin llamar a la api): 62 líneas dirían «buscando partida…» sin
  encolarse nunca (53 de postventa y 9 de GG) ⇒ **F-057** (humano,
  2026-10-19).
- **Desplegado el 2026-10-14: F-050**, los tres servicios: transfer
  `r20261014-1740`, api `r20261014-1743` y front `r20261014-1746` (revisiones
  `…--r20261014173903`, las tres `Running`; el transfer sigue en **modo real**,
  comprobado con `az containerapp show`): subfilas por obra con columna Partida,
  selector con Todas · CD · CI · CP y partida propuesta. **Pendiente del humano:**
  la comprobación en producción (Ctrl+F5, septiembre 2026; Partida de GONZALEZ
  PANIAGUA en la 0694: selector con CI preelegido; «⇪ Sigrid»: partida y origen
  en cada línea; **Cancelar**). Los `digest` de `infra/imagenes.json` siguen sin
  actualizarse al publicar (punto 2 de «Lo que espera al humano»).
- **Desplegado el 2026-10-09: F-049**, transfer `r20261009-1045` y front
  `r20261009-1046` (ambos `Running`; el transfer sigue en **modo real**,
  comprobado con `az containerapp show`): avisos del modal rotulados por tipo,
  repreflight al elegir partida y catálogo de partidas siempre. **Pendiente
  del humano:** la comprobación en producción (GONZALEZ PANIAGUA, 0694: «Sin
  partida» y «Sobrecarga»; **no confirmar la sobrecarga**, el 95 % ya está a
  mano). El texto de `redeploy_dedicacion.ps1` que dice «SIGUE en modo
  pruebas» está caducado.
- **Desplegado el 2026-10-08: F-045**, solo la api (`r20261008-1509`, revisión
  `Running` comprobada con `az containerapp show`): el Excel lleva Obras,
  Postventa y Detalle (sin Resumen) y la columna Observaciones vacía.
  **Pendiente del humano:** un Excel de producción y avisar a Juan y
  Administración de que desaparece el Resumen.
- **Desplegado el 2026-10-07 (noche): F-047**, solo el transfer
  (`r20261007-2029`): lecturas de hasta 200.000 filas, ya se registra en obras
  con más de 2.000 partidas. Comprobado por el líder (solo lectura): el
  transfer desplegado sigue en **modo real** (`OBRA_PRUEBAS_FORZAR=false`) y
  la línea de Bas Leal (`porcentajes:3599`) está en la **0696 real**, parte
  PT26/00298 (En registro), partida CI.1.8, con cuenta analítica. Las dos
  líneas de Bas Leal en la **0404** (`porcentajes:148` y `:149`, parte
  PT26/00344) son de la prueba LOCAL en modo pruebas (ids de la base local):
  **pendiente que el humano las borre**, como las de F-037.
- **Desplegado el 2026-10-07 (tarde): F-041 y F-042**, solo el front
  (`r20261007-1734`, revisión `Running` comprobada con `az containerapp show`):
  el filtro de obra casa con `Postv-` y la última fila abre el desplegable de
  obras. **Comprobación pendiente del humano** (Ctrl+F5): `pos` en «Filtrar
  obra…» y en `/`; en la última fila, Enter y escribir una obra (Esc dos veces).
  Al lanzarlo salió `The subscription of 'redactado-ver-copia-local' doesn't
  exist`: no se cargó `00_vars_dedicacion.local.ps1` y `az` siguió con la
  suscripción por defecto, que era la buena. Ver «Lo que espera al humano».
- **Desplegado el 2026-10-07: F-037, F-039 y F-040** (transfer
  `r20261007-0851`, api `r20261007-0852`, front `r20261007-0853`, en orden
  transfer → api → front). Desde ya, cada línea registrada lleva la cuenta
  analítica de la obra (F-037), las partidas de VAR desde la 29 se ofrecen
  como `VAR-NN` y se ignoran las obras con 6+ dígitos (F-039, **tras el
  sync**), y el Excel sale como el modelo de Juan (F-040). **Pendiente de
  confirmar por el humano:** sync («Actualizar Sigrid») y preview con
  `excluidas_por_codigo` 240 y `entradas_var` 1; un Excel de producción.
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

`BACKLOG.md` tiene el orden completo. Nuevas el 2026-10-08 (pedidas por el
humano): **F-049** (los avisos del modal de registro rotulados por tipo, con su
%; desplegada), **F-051** (pisar las líneas del parte al 0 % que ya existan),
**F-050** (subfilas por obra con columna Partida y partida propuesta; absorbe
F-043) y **F-021** redefinida (velar las etiquetas de las demás obras al
filtrar). **F-044** (recursos vinculados) sube. Del correo de Juan del
2026-10-08: **F-052** (una línea de mensajería por obra en curso y mes, con
la fecha fin de Sigrid) y **F-053** (delegados: parte único, cada línea a su
obra e imputada al CP); F-044 queda en persona, gasoil, vehículo y teléfono
(KM no). Juan quiere registrar **octubre entero desde la app**. F-045 desplegada.
F-049 desplegada. F-050 desplegada. F-055 cerrada y desplegada el 2026-10-17. F-056 cerrada y
desplegada el 2026-10-19. F-057 cerrada el 2026-10-19 y desplegada el
2026-10-20. F-051 cerrada y desplegada el 2026-10-21. Orden: **F-030** (en curso), **F-058** (un % que redondea a 0 no se registra), F-044, F-052, F-053, **F-054** (el sync trae los %
que ya hay en los partes de Sigrid; 2026-10-08), F-021, F-048, F-046, F-038, F-028, F-036, F-031, F-059, F-060,
F-033 y, detrás, F-017, F-018…

## ⚠ Lo que espera al humano

- **O1 de F-056: ¿feature propia para validar el resto del cuerpo del
  registro?** `overrides` no enteros dan 500 (`int(k)`, `int(v)` en
  `routes.py`, preflight y ejecutar); `pisar_claves` y `usuario` llegan crudos
  a `ejecutar` (`list()` de un texto lo trocea en caracteres). Se le suma la
  O1 de la review 1 de F-056: un entero enorme (`10**30`) en `trabajador_ide`
  u `obra_ide` pasa la validación y PostgreSQL da 500 (`integer out of
  range`), no 422; no escribe nada.

- **`Run-Az` de `infra/00_capps_vars_dedicacion.ps1` aborta tras un `update`
  que sí se aplica** (2026-10-17 las tres veces y otra el 2026-10-19 con la
  api de F-056; el 2026-10-20, api y front de F-057, NO se cortó: `az : ` vacío,
  `NativeCommandError` en PS 5.1): el `containerapp update` crea la revisión y
  PowerShell convierte lo que `az` escribe en stderr en error terminante, así que
  `redeploy` para tras el primer servicio. Se desplegó relanzando `-Solo api,front`
  y `-Solo front`, comprobando cada revisión. Propuesta a decidir: que `Run-Az`
  rebaje `ErrorActionPreference` a `Continue` alrededor de la llamada y decida solo
  por `$LASTEXITCODE`.
- **Trabajo del arnés tras F-055** (líder, a proponer): O1 y dos automejoras de
  sus reviews —`CHECKPOINTS.md` C4: trazar un R «como hoy» o documental; una
  mutación manual de Python también exige tabla con texto exacto y el reviewer
  corre los mutantes del generador sobre esas líneas—, portadas a `arnes-base`.
  Más la automejora de la review 1 de F-056: que C4 bis acepte el nº de
  workers de `mutacion_F-XXX.md` (la herramienta ya lo imprime) o que
  init.sh compruebe que «Evidencias» lo lleva (un rechazo de solo papeleo).
  Más el aviso del implementer de F-057: `harness/mutacion_paralela.py` con 4
  workers dio 4 supervivientes falsos (la 2.ª tanda de los workers; a mano y
  en serie mueren), detalle en `progress/mutacion_F-057.md`. Si es defecto de
  la herramienta, vale para cualquier proyecto ⇒ `arnes-base`. Y la
  automejora de la review de F-057: C4 dice «MANUAL … pendientes de que el
  humano las ejecute», pero aquí el líder las cumple a menudo antes de la
  review (F-055, F-056, F-057); propuesta: «listadas con su comando exacto y,
  si ya se ejecutaron, con quién, cuándo y el resultado real» ⇒ `arnes-base`.
- **Borrar en la 0404 las líneas de las pruebas locales** (modo pruebas,
  `PRUEBA-PORC`): las dos de Bas Leal (parte PT26/00344, `porcentajes:148` y
  `:149`) y la de la M3 de F-050 (parte PT26/00371, noviembre 2026, `hmores`
  410599, GONZALEZ PANIAGUA, `porcentajes:180`).
- **Cargar también la copia local de variables al desplegar.** El orden es
  `. .\00_vars_dedicacion.ps1`, `. .\00_vars_dedicacion.local.ps1` y
  `. .\00_capps_vars_dedicacion.ps1`. Si falta la local, `redeploy` sigue con
  la suscripción por defecto de `az` (el 2026-10-07 acertó por suerte).
  Propuesto al humano: que `redeploy` pare si `SUBSCRIPTION` está redactada.
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

- **F-050, postventa en la propuesta (R9):** `proponer` casa la postventa con
  `origen.codigo` (leído en Sigrid) y el preflight con `obra.codigo` (el que
  manda la api). Hoy coinciden; si alguna vez divergen, la propuesta del
  selector y la automática del registro diferirían en postventa.
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
