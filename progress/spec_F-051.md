<!-- progress/spec_F-051.md -->
# F-051 · Informe del spec-author (2026-10-20)

Spec: `specs/F-051-pisar-lineas-cero/` (requirements 121 líneas, design 249,
tasks 12 tareas). Rama `feature/F-051-pisar-lineas-cero`, copia
`porcentajes-f051`. **Estado: spec lista, D1-D9 abiertas** (design §9): toca
al humano decidir antes de pasar a `spec_ready`/implementar.

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
