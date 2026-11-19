<!-- progress/spec_F-069_enmienda.md -->
# F-069 · Enmienda de la spec tras la review 1 (spec-author, 2026-11-19)

Rama `feature/F-069-importe-caja-km` (copia `porcentajes-f069`), sobre `c995a81`.
Fuentes: `progress/review_F-069.md` (cambios 1-7, O1-O4), `progress/impl_F-069.md`
(decisiones 1-10) y las decisiones D17-D21 del humano en `progress/current.md`
(«F-069 · en review»). No se ha tocado código, `current.md` ni `features.json`.

**Preguntas abiertas: ninguna que bloquee.** Hay lecturas mías, derivadas de
reglas que ya estaban en la spec, que el líder debe enseñar al humano en el
resumen (sección «Para el resumen al humano»).

## Qué cambió y dónde

| Origen | requirements | design | tasks |
|---|---|---|---|
| **D17** (el transfer quita la marca) | R31 (publica el `tex` sin `st.marca_pruebas` ni espacios), R32 (la api lo pone tal cual) | §1, §4 (`texto_linea.comentario_de_tex`, `porcentajes_existentes`, `traer_sigrid` sin marca), §6.1 (`comentario_de_sigrid(tex)` sin marca ni parámetro), §6.4, §9.2 | T19 (transfer), T21 (api), T26 (`INTEGRACION.md` §7) |
| **D18** (solo el comentario no revisa) + cambio 1 | R4 (`revisado?`; `copiado` a `false` solo si cambia la cantidad o `revisado: true`), R5 (`revisado` booleano), R12 (el `PUT` lleva solo las casillas que cambiaron) | §4 (`ImporteIn.revisado`, `cuerpoImportes`), §6.3, §9.2 | T22 (api), T23 (front, con el test de dos copiadas) |
| **D19** (comentario sin cantidad) | R3 (`cantidad` nulable), R4, R5 («sin más chequeo»), R8 (`copiado` solo si se copia una cantidad) | §4 (`ImporteMes.cantidad` opcional), §6.1, §6.3, §7.2 (`importe_vinculado.cantidad` nulable) | T22, T23; T16 (paso del comentario antes de los km y `ALTER` local) |
| **D20** (comentario de una ya registrada a Sigrid) | R26 (condiciones y `UPDATE` solo de `tex`), R27, R28 (`tex_nuevo`, `tex_actualizadas`), R29 (modal) | §1, §4, §6.5 (nueva: paso 6 y paso 10), §7.1 (`stmt_editar_tex`, `lineas_registradas` ampliada), §8, §9.1 (D9 salvo `tex`), §10 | T20 (transfer), T24 (modal), T16 (paso D20), T17 (aviso a `partes`) |
| **D21** (evento `IMPORTES` para las del mes) | R32 | §6.4, §9.2 | T21 |
| Cambio 4 (T16) | — | — | T16: «Revisado» solo en el km, y que el comentario del titular no vuelve en modo pruebas (decisión 8) |
| Cambio 5 (R30) | R30 reescrito como requisito propio: la traza conserva cantidad, `copiado` y comentario | — | T9 **reabierta** (solo por R30): pide un `test_f069_r30_*` con RED |
| Cambio 7 (puerto real) | — | §4: `de_trabajador`, `del_periodo`, `guardar`, `borrar`; `guardar_subfila_importe`, `poner_comentario`, `registradas` en `AsignacionRepository`; la función `importes_del_mes_de` | — |
| Cambio 2 (RED de R15, R8, R32) | — | — | T25 |
| Frontera (SPECS.md) | — | §8 pasa a «Contrato y frontera», con la respuesta «¿Cruza la frontera?» | — |

Tareas nuevas: **T19-T26**, con su verificación y RED; las hechas no se
renumeran. T13 (mutación) pasa a cubrir las dos pasadas y se coloca tras las
nuevas; T18 sigue la última. El encabezado de `tasks.md` dice que, si una
hecha choca con la enmienda (T7 con D18, T10 con el cambio 1, T14/T15 con
D17), manda la nueva. Solo T9 se reabre: es la única cuya verificación era
falsa (`-k r30` sin tests).

## Diseño de D20 (resumen; detalle en design §6.5 y §7.1)

- **Preflight, paso 6.** `lineas_registradas` trae, en la misma lectura y solo
  si algo trae comentario (si no, la SQL de hoy, R24), `tex`, `obride` y el
  `con.est` del parte. Una función pura, `tex_a_actualizar`, decide
  `tex_nuevo`: hay comentario, su `tex_de` (con la marca en pruebas) difiere
  del leído, la `synckey` empieza por `porcentajes:`, el parte está En
  registro y, en pruebas, la línea es de la obra de pruebas.
- La acción **sigue siendo `ya_registrado`**: la traza de la api no cambia.
  El motivo dice «se actualiza el comentario» o por qué no.
- **Ejecutar, paso 10.** Las líneas con `tex_nuevo` entran en la relectura
  `lineas_para_editar` de siempre. Si siguen valiendo, `stmt_editar_tex`:
  `UPDATE hmores SET tex = ?` con la `_guarda` de F-051 y, en pruebas,
  `AND obride = ?`. Nunca `DELETE`; no toca `can`, `pre`, `tot`, hora,
  partida ni cuenta. La respuesta lleva `tex_actualizadas`.

## Para el resumen al humano (lecturas mías, no decisiones nuevas)

1. **D20, comentario borrado.** Si el usuario borra un comentario, el `tex`
   de Sigrid se queda: es la regla R23 ya aprobada (sin comentario, la de
   antes) y evita que una api vieja, que no manda comentarios, vacíe `tex`.
   Consecuencia: el siguiente «Sincronizar Sigrid» lo vuelve a traer (D15).
2. **D20, cuándo no se actualiza:** parte cerrado (nunca se escribe en uno
   cerrado, F-037), línea sin `synckey` `porcentajes:` (D20 pide solo las
   nuestras; una titular enlazada por `sigrid_hmores_ide` a una línea a mano
   trae su `tex` al sincronizar, R32, pero no se le escribe) y, en modo
   pruebas, una línea fuera de la obra de pruebas. Esto último protege una
   línea registrada en real de recibir «PRUEBA-PORC …» desde una prueba.
3. **D18.** Volver a teclear el mismo número no cuenta como revisar: la api
   solo ve que la cantidad no cambia. Para eso está «Revisado».
4. **D19.** «Sin chequeo de contenido»: se quitan los espacios de los lados y
   se mantiene el tope de 200 caracteres, que es el de la columna. Nada más.
5. **BBDD local.** Si la `dedicacion` local ya tiene `importe_vinculado` de la
   pasada 1, el humano pasa `cantidad` a nulable a mano (comando en T16).
   `esquema.py` solo deriva `ADD COLUMN`. En Azure la tabla aún no existe.

## Lo que no recoge esta enmienda (no estaba en el encargo)

- **O3** (`CopiarTrabajadorAnterior` sustituye también la caja tecleada) y
  **O4** (`orden = 0` sin `sigrid_hmores_ide` en `_comentarios`): siguen
  abiertas para el líder.
- **Cambio 6** (`current.md`): es del líder.
- **Topes:** requirements 149/150 y design 249/250
  (`python -m harness.tamano --feature F-069`, código 0). Una enmienda más
  exige recortar antes, o partir la feature.
