<!-- progress/spec_F-069.md -->
# F-069 · Informe del spec-author (2026-11-10, revisado el 2026-11-11 y dos veces el 2026-11-12)

Spec en `specs/F-069-importe-caja-km/` (rama `feature/F-069-importe-caja-km`,
copia `porcentajes-f069`): `requirements.md` R1-R36 (148 líneas), `design.md`
(241), `tasks.md` T1-T18. Estado en `features.json`: `spec_ready`, **sin
decisiones abiertas**, pendiente de que el humano apruebe la spec.

## Resumen

Los vinculados de cantidad son de tres tipos:
- `VP`: km del mes, que se multiplican por 0,20 €/km y se reparten por %.
- `VIAJE`: € del mes, repartidos por %.
- `CAJA`: € **por obra**, cada línea del titular con la suya, que van enteros a esa obra (`can` 1, `pre` = `tot`).

Se teclean en el editor. Las cantidades del mes van a la tabla nueva
`importe_vinculado` y las de caja a `asignacion_vinculado`. Hay un
**comentario** en cada línea (del titular y de los vinculados de cantidad) que se escribe
en `hmores.tex`; en modo pruebas va como marca + comentario. Cuando F-054 esté
unida, «Sincronizar Sigrid» trae el `tex` de nuestras líneas como comentario.
Copiar el mes copia las cantidades y los comentarios, marcados como «copiado». La hora es siempre la por defecto del recurso.
Despliegue: transfer → api → front.

## Decisiones cerradas

- 2026-11-11, el humano («d2, caja en euros, km en km y viaje en wuros. d7, copia importes. A a lo demas»): D1 A, D2 (caja y viaje en €, VP en km), D3 A, D4 A, D5 A (ahora solo VP y viaje), D6 A, D7 B (copia marcada `copiado`), D8 A, D9 A.
- 2026-11-12, Juan Romero (Dir. Admón. y Control de Costes, correo «RE: parte km», que no se versiona) y el humano:
  - **D10**: precio por km único, 0,20 € en `config.yaml` («que el sistema multiplique por 0,20€»). Deja de ser una búsqueda en Sigrid; lo leído consta en design §9.1.
  - **Hora de caja**: la por defecto (`CO`, «lleve al parte el tipo de hora por defecto»). Es lo que ya hace `hora_del_vinculado`: toma la `defecto` de `reshor`, es decir `res.horide`. Leído el 2026-11-12: `CO` en los 120 `CAJA` activos, `KM` en los 57 `VP` y `VI` en los 22 `VIAJE`.
  - **Viaje dentro, en €** («aunque es posible que de momento no se use»).
  - **Caja por obra** («la caja se asigna a la obra, cada obra con la suya»).
  - **Columna de comentarios**, que «deben traerse al sincronizar».

## Decisiones cerradas el 2026-11-12 por el humano («elijo opcion A en d11. a en las demas»)

- D11 = A: la copiada sin revisar se omite al registrar hasta que se teclee o se pulse «Revisado».
- D12 = A: caja en una casilla «Caja · obra» por línea en el editor; línea con `can` 1 y `pre` = `tot` = cantidad (una caja por obra y mes en la capacidad).
- D13 = A, **en contra de mi recomendación (B)**: como D4, cada obra con la caja vacía avisa «falta la caja del mes» y se omite esa línea; con 0, no se escribe nada en esa obra. Aplicado en R20, en design §9.2 y en T2.
- D14 = A: comentario en la línea del titular y en los vinculados de cantidad.
- D15 = A: al traer, el `tex` de Sigrid manda en nuestras líneas ya registradas.
- D16 = A: primero se cierra F-054 y se une a `dev`; esta rama se rebasa sobre `dev` y se implementa F-069 entera, sin tareas condicionadas (en la cabecera de tasks).

**No queda ninguna decisión abierta.**

## Lecturas contra Sigrid (solo `SELECT` vía `sigrid-api` `POST /api/sql/read`, base `ruesma`)

Las hice con el `SigridApiClient` de la api y un script del scratchpad; usé el `.env` de la copia principal solo para leerlo.
- 2026-11-11, precio por km. `reshor` hora `KM` de los VP: a 0 salvo VP0016 160, VP0046 600 y VP0115 175. `auxhor` 46 sin precio. `tarmob`, `rescen` y `conext`: nada. `auxgas` 8 «Kilometros»: 0,1923. `hmores` KM de 2026: 602 líneas; 8 de ellas con `can` = km y `pre` 0,20.
- 2026-11-12: hora por defecto de los `CAJA`, `VP` y `VIAJE` activos (las cifras están arriba).

## Notas para el líder

- Hoy el transfer escribe en `tex` la marca `PRUEBA-PORC` en modo pruebas y `""` al insertar en real; al editar conserva el `tex` de antes. `limpiar` busca el `tex` **igual** a la marca, así que pasa a buscarla como prefijo (T3).
- F-054 hoy solo lee las líneas `M*` (y las de los vinculados para el «a cero»): traer el comentario de los vinculados necesita una lectura más (R31).
- `bash harness/init.sh` en verde tras la revisión (ver el commit). F-071 tiene que dejar fuera la caja (`can` 1); hay que anotarlo en su spec.
