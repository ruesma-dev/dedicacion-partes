<!-- progress/spec_F-051.md -->
# F-051 · Informe del spec-author (2026-10-20)

Spec: `specs/F-051-pisar-lineas-cero/`. Rama `feature/F-051-pisar-lineas-cero`,
copia `porcentajes-f051`. **Pasada 2 (abajo, §6) manda**: D1-D9 decididas,
D10-D13 abiertas. Las §2 y §3 son de la pasada 1 y quedan como historia.

## 1. Exploración en Sigrid (solo lectura)

Cómo: `POST /api/sql/read` de sigrid-api, base `ruesma`, con `SELECT`
parametrizados lanzados por un script del scratchpad que usa
`SigridWriteClient._lectura` (con `escribir` anulado y una guarda que rechaza
todo lo que no sea `SELECT`/`WITH`), desde
`porcentajes/services/dedicacion-transfer` para su configuración. Ninguna
escritura, ni `ejecutar`, ni fases que escriben del script. Diez lecturas.
Sin nombres, DNI ni importes salariales en este informe.

### 1.1 Cuántas hay (partes de trabajo, `con.tip = 35`, de obra)

| Periodo | Líneas `M*` con `can = 0` | Dónde |
|---|---|---|
| 2024 (feb-dic) | 6 | 5 partes, hoy Imputados |
| 2025 (ene-may) | 12 | GG (`paride = 0`) y obras 0685/0695, Cerrados o Imputados |
| jun 2025 - sep 2026 | **0** | — |
| **oct 2026** | **5** | **un parte: PT26/00370, obra 0707, En registro** |

Octubre está en curso (14 líneas `M*` en todo el mes a 2026-10-20), así que
la muestra es corta. Ninguna de las 18 anteriores convive con otra línea `M*`
de su recurso en el mismo parte: se quedaron solas, a 0, y el parte se cerró
así. Además hay líneas a 0 con horas `C*` (incidencias de `partes`, `can = 0`
por diseño), `K*` y `O*`: no son de porcentajes.

### 1.2 El caso de octubre: obra 0707

Parte PT26/00332 (septiembre, Cerrado) frente a PT26/00370 (octubre, En
registro, cabecera `Parte <obra>` de Administración, empresa 1, sin una sola
línea de `partes` ni nuestra; 95 líneas: 80 `H*` tecleadas por Administración).

| `hmores` oct | Hora | Partida | `can` oct | Septiembre (misma persona) |
|---|---|---|---|---|
| 410600 | MADM | CI.1.5 | 0 | 406275, MADM, CI.1.5, 0,9 |
| 410931 | MENC | CI.1.3 | 0 | 406278, MENC, CI.1.3, 1 |
| 410935 | MCAP | CI.1.8 | 0 | 406283, MCAP, CI.1.8, 1 |
| 410937 | MCAP | CI.1.8 | 0 | 406285, MCAP, CI.1.8, 1 |

Y los recursos vinculados de esas personas, también a 0 y copiados igual:
410601, 410932, 410936 y 410938 (`OTEL`, CI.4.13), 410933 y 410940 (`OGAS`,
CI.4.1), 410602 (`KM`, CI.03P.9) y 410939 (`MESVE` de un vehículo,
`res.cla = 0`, CI.03P.9). Una línea `OTRO` (410598) se copió con `can = 1`.

Rasgos comunes de las copias: mismo recurso, hora, partida y cuenta analítica
(`caaide`) y mismo `pre` que en septiembre; `fec` = 20261031; `synckey` y
`tex` vacíos; ningún enlace (`dvaproide`, `dvfproide`, `hdereside`,
`empdpreide`, `empabside`, `emprccide`, `tarreside`, `ortide`, `taride`,
`dvpproide`, `hmorespro`: 0 en todas las `M*` de 2025-2026, a cero o no). No
están todas las de septiembre: faltan, por ejemplo, las de horas `MJG`,
`MJEFO` y `MAJO` (se copiaron y se borraron, o no se copiaron). Cada uno de
los cuatro recursos tiene **un solo** código `M*` en `reshor`, que es su tipo
por defecto.

**Cuándo**: los `ide` 410597-410602 rodean al 410599 de la prueba M3 de
F-050 (escrita en local antes del despliegue del 2026-10-14) y `con.tiemod` del parte es 2026-10-14 14:44; los
410931-410940, posteriores. Es decir, **después** de la indicación de Juan
del 2026-10-08.

**Quién**: Administración, en Sigrid. `hmores` no guarda autor ni fecha
(`INFORMATION_SCHEMA`: solo `fec`, `fec1`, `fec2`, `fecext`; `con` solo
`tiemod`), así que no se distingue entre una función de copia de Sigrid y una
copia a mano. Ni `partes` (sin `synckey partes:`, y `partes` no escribe `M*`)
ni este proyecto (sin `porcentajes:`). Ninguna plantilla de parte en los datos.

### 1.3 Por qué hoy no se pisa (siempre)

`criterio_choque` compara recurso, hora y **partida** (ARCHITECTURE
`#regla-conflicto`); `can` no entra. Con la misma partida, la línea al 0 %
choca y sale un pisado **a confirmar** (conflicto en el modal). Con otra
partida —una elegida, o una propuesta distinta, que era lo normal antes de
F-050 (desplegada el 2026-10-14, después de la petición del 2026-10-08)— o
con otro código `M*`, no choca: la línea a 0 se queda y la nuestra se añade
al lado. La capacidad no avisa porque suma 0.

Efecto lateral visto: el paso «parte anterior» de la propuesta (F-050)
cuenta el mes en curso, así que una línea al 0 % de octubre hace que se
proponga **su** partida (suma 0, única); dos líneas al 0 % de partidas
distintas empatan y ese paso no propone. F-051 no lo cambia (design §10).

## 2. Lo que propone la spec (con las recomendaciones)

Solo transfer. Una línea es **pisable** si es del mismo recurso, `M*`, `can`
0, sin `synckey`, en un parte En registro del periodo de la obra destino (en
postventa, además, de la misma partida). El preflight la anuncia en el
`aviso` de la acción (sin conflicto); `ejecutar` la borra con guarda antes de
insertar, solo si alguna acción del recurso se escribe. api y front sin
cambios. Regla nueva `#regla-cero` en ARCHITECTURE.

## 3. Preguntas para el humano (design §9, con recomendación)

1. **D1 · Qué es pisar**: borrar e insertar al final (A, recomendada), en la
   misma posición (B) o `UPDATE` en su sitio (C).
2. **D2 · Confirmación**: sin confirmar, con aviso (A, recomendada) o como
   un pisado de hoy (B).
3. **D3 · Qué casa**: cualquier `M*` al 0 % del recurso en la obra (A,
   recomendada), misma partida (B) o los cuatro campos (C).
4. **D4 · «Al 0 %»**: `can` exacto 0 o nulo (recomendada) o con tolerancia.
5. **D5 · Solo sin `synckey`** (recomendada).
6. **D6 · Partes cerrados**: como hoy (A, recomendada) o ignorar la línea al
   0 % (B).
7. **D7 · Postventa**: solo la de la misma partida (B, recomendada), la regla
   general (A) o fuera (C).
8. **D8 · Líneas al 0 % en obras donde el recurso ya no tiene línea**: fuera
   de F-051 (recomendada).
9. **D9 · Verificación**: las líneas al 0 % de la prueba las crea a mano el
   humano o Administración en la 0404 (A, recomendada) o una fase nueva del
   script que escribe (B). Más una pregunta para Juan: ¿copia de Sigrid o a
   mano?

## 4. Coordinación

- **`partes`** (mismo parte): no escribe `M*`; nada que cambiar allí. Se les
  avisa al desplegar (T11). No se ha tocado su repositorio.
- **F-044**: las líneas al 0 % de teléfono, gasoil, KM y vehículo siguen ahí
  tras F-051; F-044 debería reutilizar la función (design §8).
- **`azure-apps/dedicacion.md`**: se refresca al desplegar (T11).

## 5. `bash harness/init.sh` (worktree, 2026-10-20, tras los commits)

- pytest **418 passed, 1 skipped**; PUERTA TAMAÑO de F-051 dentro (120/150,
  249/250); PUERTA COBERTURA N/A (sin código de producción).
- **1 `[KO]` de entorno, no de la spec:** «servicio 'api': el venv declarado
  'services/dedicacion-api/.venv' no contiene intérprete». La copia
  `porcentajes-f051` es un worktree y los `.venv` (ignorados por git) solo
  existen en la copia principal. Hay que crearlos en el worktree antes de que
  el implementer trabaje aquí (decisión del líder; el spec-author no toca el
  entorno).

## 6. Pasada 2 (2026-10-20): D1 = C y D5

**Decisiones del humano** (vía líder): «d1, nunca borramos lineas, editamos
el valor. d5, cualquier linea a 0% se puede pisar». D2-D4 y D6-D9, las
recomendadas.

**Lecturas nuevas (solo lectura, 2 `SELECT`):**
- Líneas con `synckey` de `partes`: 358, todas `H*` (353) o `C*` (5); 9 a
  0. **Ninguna `M*`, nunca.** Nuestras: 16, todas `M*` y distintas de 0.
- Una línea nuestra (410599) y una de Administración al 0 % (410931) tienen
  las mismas columnas rellenas; lo que cambiaría un `UPDATE` para dejarla
  igual que una insertada es `can`, `pre`, `tot`, `horide`, `paride`,
  `caaide`, `fec`, `synckey` (y `tex` en pruebas). `hmoide`, `pos`,
  `cenide`, `obride`, `ano`, `mes`, `fac`, `ortide` no cambian.
- `sigrid-api` admite `UPDATE` en `/api/sql/write` con `WHERE` obligatorio
  (`azure-apps/sigrid_api.md`); `partes` F-046 ya edita `hmores` así.

**Qué cambia en la spec** (requirements 123 líneas, design 239, 13 tareas):
- Pisar = **`UPDATE` en su sitio** (mismo `ide`, `pos` y parte), con guarda
  (mismo recurso, `M*`, al 0 %, la `synckey` leída, sin enlaces, parte En
  registro); nunca `DELETE`.
- Cada acción edita **como mucho una** línea al 0 % (emparejado
  determinista: misma partida, misma hora, menor `ide`); las que sobran **se
  quedan a 0** y el aviso lo dice.
- Si la guarda no cambia la fila, la acción va a `omitidas` (se detecta con
  la relectura por `synckey` que ya existe) y no se inserta nada en su lugar.
- D5: una línea al 0 % con nuestra `synckey` de otra asignación es pisable;
  las de esta ejecución (`mias`) no. Las de `partes`, según D11.
- api y front siguen sin cambios; ninguna lectura nueva.

**Preguntas nuevas para el humano** (design §9, con recomendación):

10. **D10 · Qué campos se editan.** (A) solo `can`/`tot` con el `pre` de la
    línea: la partida de Sigrid no sería la que enseñan cuadrante y modal,
    la hora puede no ser la de P1, `tot` sale del `pre` copiado del mes
    anterior y la api trazaría una partida que no es la de Sigrid. (B) todo
    lo que insertaríamos: la línea queda como una nuestra salvo `ide` y
    `pos`; se pierde la partida de Administración (copia del mes anterior;
    el aviso la enseña para poder elegirla). **Recomiendo B.**
11. **D11 · `synckey`, `tex` y líneas de `partes`.** La `synckey` pasa a ser
    la nuestra (si no, se pierde la idempotencia). `tex`: marca en pruebas,
    el que tenía en real. Una línea de `partes` editada con nuestra
    `synckey`: su comprobación (F-024, por `synckey` y sin ella por `ide`)
    la daría por `borrado_sigrid` y al reaprobar sv5 **la reinsertaría**
    (doble imputación); conservando la suya, nosotros la volveríamos a ver
    como pisado. Hoy 0 casos. **Recomiendo excluir las de `partes`** (es una
    excepción a D5: que la confirme).
12. **D12 · ¿«Nunca borramos» alcanza al pisado confirmado de hoy y a
    `limpiar`?** **Recomiendo** fuera de F-051: feature aparte que convierta
    el pisado confirmado en `UPDATE` con la misma sentencia; `limpiar` se
    queda como herramienta de pruebas. Hasta entonces el pisado confirmado
    sigue borrando, y `limpiar` borraría la línea editada de la prueba T11.
13. **D13 · Cómo se deshace un `UPDATE`.** Borrar por `synckey` (F-033)
    eliminaría una línea que era de Administración. **Recomiendo** que F-051
    publique y registre en el log lo que tenía (hora, partida, `fec`,
    `synckey`; `pre`, cuenta y `tex` no se leen hoy) y que F-033 la devuelva
    a 0 con un `UPDATE` guardado por nuestra `synckey`, sin borrar. Guardarlo
    en la api (columna nueva) sacaría la feature de «solo transfer».

## 7. Pasada 3 (2026-10-20): D10-D13 decididas

**Decisiones del humano** (vía líder): D10 = B; D13, la recomendada; D11
(«y no deberia encontrarla por el ide de sigrid una vez que se registra la
linea? es unico y no se edita nunca», «d11 que ya localice»): no se cambia la
`synckey` de otro sistema y lo editado se localiza por `hmores.ide`; D12
(«que pase a editar»): el pisado confirmado también edita, dentro de F-051.

**Lecturas nuevas (solo lectura, 2 `SELECT`; código, solo lectura):**
- Identidad repetida (mismo parte, recurso, hora `M*` y partida), partes de
  obra: 48 grupos en 2024, 67 en 2025 y **63 en 2026**, ninguno con línea a
  0. Ejemplo: PT26/00109 (En registro), `MDEL`/`MESVE` una línea por día,
  hasta 9 por recurso, sin `synckey`. Un pisado confirmado puede tener varios
  choques: abre **D14**.
- La api **ya guarda** `asignacion.sigrid_hmores_ide` (ORM, tras cada
  escritura, en `_trazar`) y no lo manda al transfer. `reemplazar` borra y
  recrea las asignaciones al guardar la fila: el `ide` guardado se pierde con
  cualquier edición del cuadrante (como la `synckey`, que es por
  `registro_id`).
- `partes` (`azure-apps/partes.md`): F-024 comprueba por `synckey` y usa el
  `ide` solo para las que no la tienen; las que da por borradas conservan
  `sigrid_hmores_ide`. F-046 edita solo con el `can` esperado y revierte si
  la guarda falla.
- El front dice hoy «se borran … y se escribe …» en el pisado
  (`app.js`, línea 2392) y lo vigila `test_f049_avisos_registro.py`.
- El pisado borra hoy en 5 ficheros de tests del transfer (lista cerrada en
  tasks.md). `limpiar` borra lo marcado `PRUEBA-PORC` en `tex` con nuestra
  `synckey`, sin mirar la obra.

**Qué cambia en la spec** (requirements 130 líneas, design 230, 17 tareas):
- **Toca los tres servicios.** Transfer: casi todo. Api: manda
  `hmores_ide` y guarda el de las ya registradas, **sin columna nueva**
  (`sigrid_hmores_ide` existe). Front: el texto del pisado. Orden de
  despliegue: transfer → api → front (design §1).
- **Ningún `DELETE` en el registro:** el pisado confirmado edita el choque de
  menor `ide`; el resto, a 0 (D14). `stmt_borrar_linea` queda solo para
  `limpiar` (D15).
- **Idempotencia (R15):** ya registrada si la fila de su `hmores_ide` existe,
  es del recurso y no lleva `synckey` nuestra de otra asignación; si no, por
  `synckey`, como hoy. Una sola lectura (`synckey IN … OR ide IN …`), también
  en el lote: el preflight no gana lecturas. Las registradas antes de F-051
  se completan con `ya_registradas_ide`.
- **`synckey` de una línea de Administración (vacía): se le pone la nuestra**
  además de localizarla por `ide` (decisión del spec-author, design §6.3):
  cubre el caso de que la api no llegue a guardar el `ide`, mantiene el
  pisado de hoy al editar el cuadrante y deja a `limpiar`/F-033 localizarla.
  Solo la `synckey` de otro sistema se conserva.
- **Antes de escribir, una lectura** de las líneas a editar con todo lo que
  tienen (`pre`, `caaide`, `tex`, estado del parte, enlaces): sirve a la
  guarda, a la comprobación de que no han cambiado y al log de D13. Es una
  lectura nueva solo en `ejecutar`; las de `lineas_del_parte`, compartidas con
  el lote de F-055, **no** se amplían.
- **Líneas de `partes`:** no son editables hoy (0 `M*`); si lo fueran,
  conservan su `synckey`, su F-024 las vería presentes y su F-046 fallaría sin
  pisarlas (design §8). Aviso a `partes` al desplegar.

**Preguntas para el humano** (design §9, con recomendación):

14. **D14 · Pisado con varios choques** (63 grupos en 2026). (A) editar el de
    menor `ide` y poner los demás a 0; (B) no pisar y omitir con motivo;
    (C) editar uno y dejar los demás (sumarían). **Recomiendo A.**
15. **D15 · `limpiar`** (solo pruebas). (A) sigue borrando lo marcado;
    (B) deja a 0 y la 0404 acumula líneas. **Recomiendo A.**
