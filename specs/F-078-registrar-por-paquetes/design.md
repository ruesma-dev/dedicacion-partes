# F-078 · Diseño: registrar por paquetes (seleccionados o visibles)

**Rigor: `critico`.** Disparador 2 de «Niveles de rigor» (`CHECKPOINTS.md`):
**escribe en producción y en lo compartido**. `registro/ejecutar` de la api
(`services/dedicacion-api/application/registro_sigrid.py`) manda al transfer
lo que se escribe en `hmores` de Sigrid (base `ruesma`, la misma que usa
`partes`) y las sobrantes que se ponen a 0; esta feature cambia **qué
trabajadores y qué líneas** entran en esa escritura, y el botón general
deja de registrar el mes entero. D3 y D4 decididas por el humano el
2026-11-27; D1, D2 y D5-D11 abiertas (§10).

## 1. Servicios y límite

| Servicio | Qué cambia | Por qué ahí |
|---|---|---|
| api | `trabajador_ides` en las dos rutas del registro y su filtro | dueña del dato: decide qué asignaciones van |
| front | `#btn-registro` pasa al paquete: alcance, rótulo, cuerpo, modal y aviso final | solo elige a quién (selección y filtros son suyos) |
| transfer | **nada** | ya trabaja por recurso (§3) |

Ninguna responsabilidad nueva fuera de su servicio; nada se copia entre
servicios. El front manda `ide` de trabajadores, como hoy manda uno.

## 2. Lo que hay hoy (leído el 2026-11-27)

- **api.** `RegistroSigrid.preflight/ejecutar(anio, mes, …, trabajador_ide,
  obra_ide)`; `_payloads` y `_sumar_incidencias` filtran con
  `AsignacionORM/IncidenciaORM.trabajador_ide == X` (F-056, `is not None`).
  El preflight sin `obra_ide` pide `preflight_lote(…, completo=True)`
  (sobrantes, F-054 R31); `ejecutar` va por obra y en serie, con
  `poner_a_cero` antes si hay `sobrantes_a_cero`.
- **front.** `registroPreflight(trabajadorIde)` guarda `registro.trabajadorIde`
  y lo mandan `pedirPreflight(obraIde)` y `registroEjecutar`. Entradas:
  `#btn-registro` (mes), «⇪ Sigrid» de fila y del editor (uno). Selección:
  `state.seleccion` (F-029), `seleccionEfectiva()` (múltiple ∩ visibles; sin
  múltiple, el cursor), `trabajadoresVisibles()` (filtros por trabajador: uno
  pasa si **alguna** línea casa con el filtro de Obras o Partida).
- **transfer.** `RegistroLote.preflight_completo` calcula las sobrantes de
  los **recursos de las líneas del lote** (`reglas_obra_cero.sobrantes`), y el
  pipeline decide por recurso: pisables, choques, `a_cero`, capacidad
  (`#regla-capacidad`) y rachas. Lo de un recurso que no viene en la
  petición no se lee como suyo ni se toca.

## 3. Por qué el transfer no cambia (D1, R24)

El modo trabajador ya es «un paquete de uno»: el lote con los recursos de
ese trabajador, completo, con sus sobrantes. Con N trabajadores el lote
lleva los recursos de los N y el transfer hace lo mismo para cada uno:

- **Sobrantes**: solo de recursos del lote (y de sus vinculados).
- **Parte compartido**: el paso 5 elige el parte En registro de la obra y
  mes o crea uno (alta protegida, relee el periodo); las líneas de otros
  recursos de ese parte no se pisan, no se ponen a 0 ni suman a la capacidad
  de los del paquete. El registro de los de fuera, después, reutiliza el
  parte.
- **Rachas** (F-062): `cierres_recursos` e `incidencias_mes` por recurso.

Lo único que el transfer no puede saber es si le faltan líneas de un
recurso: por eso cada trabajador va **entero** (D2). Si fuesen solo sus
líneas de la obra filtrada, sus otras líneas de Sigrid saldrían como
sobrantes y se ofrecería ponerlas a 0.

## 4. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `services/dedicacion-api/interface_adapters/api/routes.py` | `_trabajador_ides(valor)` (R2-R4) y pasarlo en `registro_preflight` y `registro_ejecutar` |
| `services/dedicacion-api/application/registro_sigrid.py` | `trabajador_ides` en `preflight`, `ejecutar`, `_payloads` y `_sumar_incidencias`; `_filtro_trabajadores` |
| `services/dedicacion-front/templates/index.html` | solo la ayuda del pie (el botón es el mismo `#btn-registro`) |
| `services/dedicacion-front/static/js/app.js` | §6 |
| `docs/ARCHITECTURE.md` | endpoints (`trabajador_ides`), `#regla-obra-cero` y «Timeouts encadenados» (paquete = menos obras) |
| `docs/INTEGRACION.md` | párrafo de `trabajador_ides` junto al de F-056 |
| `azure-apps/dedicacion.md` | el mismo párrafo (commit aparte, §9) |

**Ficheros a crear**: `services/dedicacion-api/tests/test_f078_paquete_api.py`
y `services/dedicacion-front/tests/test_f078_paquete_front.py`.

**Ficheros que NO se tocan**: todo `services/dedicacion-transfer/`;
`infrastructure/transfer/transfer_client.py` (el lote ya admite `completo`);
`domain/estados.py` (D6); `orm_models.py` y `esquema.py` (sin DDL); la ruta
del mes sin `trabajador_ides` (se queda, §5); el
`_trabajador_ide` de F-056 y el filtro `==` del trabajador (R5);
`seleccionEfectiva`, `marcarSeleccion`, `fijarSeleccion` y
`trabajadoresVisibles` (se llaman, no se cambian); `pintarSobrantes`,
`unirPreflight` y `esperarRegistroCortado`.

## 5. api

**`routes.py`** (interface_adapters):

```python
def _trabajador_ides(valor: Any) -> list[int] | None:
    """F-078 (R2, R3): None si no viene; si no, lista NO vacía de enteros
    (cada uno con `_entero_opcional`, sin `None` dentro), sin repetidos y
    en su orden. Lo demás, TrabajadorNoValido (422)."""
```

En las dos rutas, tras `_trabajador_ide`: si los dos vienen (el de F-056 no
nulo), `TrabajadorNoValido` (R4). Se pasa `trabajador_ides=` al registro. Un
elemento `None` dentro es 422 (no «sin filtro»): `_entero_opcional` admite
`None`, así que se comprueba aparte.

**`registro_sigrid.py`** (application):

```python
@staticmethod
def _filtro_trabajadores(columna, trabajador_ide: int | None,
                         trabajador_ides: Sequence[int] | None) -> list:
    """`[columna == ide]` (F-056, igual que hoy), `[columna.in_(ides)]`
    (paquete) o `[]` (mes). Nunca las dos (las rutas lo impiden)."""
```

- `_payloads(…, trabajador_ide, filtro, quitadas, trabajador_ides=None)` y
  `_sumar_incidencias(…, trabajador_ides=None)` usan ese filtro en vez del
  `*([…== trabajador_ide] if … else [])` de hoy. Con un solo trabajador la
  sentencia es la misma (R5).
- `preflight(…, trabajador_ides=None)` y `ejecutar(…, trabajador_ides=None)`
  lo pasan. `completo = obra_ide is None`, como hoy (R7); `ejecutar`, igual
  (R8). Lista vacía no llega (la ruta da 422), pero si llegara por código,
  `in_([])` no casa con nadie: nunca el mes entero.
- Sin tope (D7): sin filtros ni selección el botón manda **todos** los
  visibles, que es el mes; un tope impediría registrarlo de una vez. Una
  lista de N `ide` es un `IN` de N parámetros; el mes tiene cientos.
- **La ruta del mes** (sin `trabajador_ides` ni `trabajador_ide`) **se
  queda** tal cual: la usan sus tests, el script de pruebas y la «otra
  forma de registrar» que el humano deja para más adelante; quitarla no
  aporta seguridad (el front ya no la llama, R12).

Sin SQL nuevo fuera del ORM, sin DDL y sin YAML de Sigrid.

## 6. front (`app.js`)

`state.seleccion` puede quedar con 0, 1 o más `ide` (Ctrl+clic quita; Esc la
vacía); el cursor `state.seleccionIde` siempre cae en una fila visible
(`renderTabla`). Puras (sin DOM, para el arnés node):

- `alcanceRegistro(visibles, seleccion)` → `{origen: "seleccionados" |
  "visibles", ides, ocultos, bloqueado}` (R13, R14; D3, D4, D11):
  `vis` = los visibles que están en `seleccion`, en el orden de la tabla.
  `vis.length ≥ 2` ⇒ seleccionados, `ides = vis`, `ocultos = seleccion.size
  − vis.length`. `seleccion.size ≥ 2` y `vis.length < 2` ⇒ `bloqueado: true`,
  `ides = []`. Si no (0 o 1 seleccionados), visibles: `ides` = todos los
  visibles, `ocultos = 0`. Nunca un `ide` que no esté en `visibles`.
- `rotuloRegistro(a)` → «Registrar seleccionados (M)» o «Registrar visibles
  (N)» (D10); `tituloRegistro(a)` → el `title` (alcance; selección oculta).
- `cabeceraPaquete(a, nombres)` → HTML del título, `<details>` con los
  nombres escapados y la línea de ocultos (R20).

Con DOM:

- `pintarBotonRegistro()`, llamado al final de `renderTabla()`: calcula el
  alcance, pone `textContent` y `dataset.rotulo` con `rotuloRegistro`,
  `title` y `disabled` (periodo no ABIERTO, `ides` vacío, `bloqueado` o
  `registro.cortado`; R12, R14, R15). Si `registro.cortado` o hay un
  preflight en vuelo, no toca el texto («Analizando…», «Registro en curso…»).
- `registrarPaquete()` (el clic de `#btn-registro`, que hoy llama a
  `registroPreflight(null)`): recalcula el alcance; sin `ides`, nada (R15);
  si `state.editandoIde !== null`, `await guardarAhora()` (R17); después
  `registroPreflight(null, alcance)`.
- `registroPreflight(trabajadorIde = null, paquete = null)`: guarda
  `registro.paquete = paquete` (congelado, R18). `pedirPreflight(obraIde)`
  y `registroEjecutar` añaden `trabajador_ides: registro.paquete.ides` solo
  si hay paquete (R18, R22). Al acabar, el `finally` y
  `esperarRegistroCortado` restauran el texto con `btn.dataset &&
  btn.dataset.rotulo || "Registrar en Sigrid"` (R19): los dobles de hoy no
  tienen `dataset` y siguen viendo «Registrar en Sigrid» (requirements §6);
  `esperarRegistroCortado` llama además a `pintarBotonRegistro` si existe.
- `pintarModalPreflight(pf)`: con `registro.paquete`, el título lleva
  `cabeceraPaquete` (R20). `registroEjecutar`: el aviso empieza por «N
  trabajadores · » (R21).
- `index.html`: el mismo `#btn-registro` (sin botón nuevo); el texto
  inicial «Registrar en Sigrid» se sustituye en el primer pintado. La ayuda
  del pie gana «Registrar: seleccionados (2+) o visibles».
- El camino `registroPreflight(null)` sin paquete (el mes) queda en el código
  sin ningún botón que lo llame; lo usan los tests de hoy y la «otra forma»
  futura.

## 7. Riesgos

- **Que un paquete se convierta en el mes entero.** Es la avería de F-056.
  Defensas: 422 ante lista vacía o mal formada (R3), `in_` y no «sin
  filtro» en el código, y el botón desactivado con 0 o con la selección
  oculta (R14, R15). Tests de
  R3 con cada valor malo y de que el transfer falso no recibe nada.
- **El botón cambia de significado.** Quien lo pulse por costumbre ya no
  registra el mes, sino lo que dice el rótulo; sin filtros ni selección es
  lo mismo (todos los visibles). Un seleccionado suelto (el cursor) no
  registra solo a ese: para eso está «⇪ Sigrid» de la fila.
- **Filtro de obra y trabajador entero.** Filtrar por la 0694 y registrar
  los visibles registra **todas** las obras de esos trabajadores (D2). El
  modal enseña cada obra y la lista de nombres; queda dicho en el título.
- **Dos registros a la vez** (dos usuarios, o un paquete y el mes): lo
  cubre lo que ya hay (alta protegida del parte, guarda y relectura de
  `#regla-cero`); no se añade cerrojo.
- **El corte del proxy.** Un paquete pequeño toca menos obras y termina
  antes (octubre: 56 obras en ~3,5 min, unos 4 s por obra), pero un
  paquete con muchas obras puede cortarse igual: lo recoge el hotfix.

## 8. Alternativas descartadas

- Que la api recalcule los visibles con los filtros (D8 c): duplicaría en
  Python la presentación de `trabajadoresVisibles` (texto, partida,
  incidencias) y divergiría.
- Sustituir `trabajador_ide` por la lista (D8 b): cambia F-056 y sus tests
  sin ganar nada.
- Registrar solo las líneas que casan con el filtro (D2 b): sobrantes
  falsas (§3) o preflight sin sobrantes, con lo que se pierde F-054.

## 9. Frontera

**¿Cruza la frontera del proyecto? Sí, en el contrato documentado**: el
cuerpo de `POST /api/v1/periodos/{a}/{m}/registro/preflight` y `…/ejecutar`
de la api gana `trabajador_ides`. Lo consume solo nuestro front, pero el
contrato está en `azure-apps/dedicacion.md` (junto al párrafo de F-056): se
actualiza en la misma feature, con `git pull --rebase`, commit aparte y push
del humano. El contrato del transfer, los recursos de Azure, las variables
de entorno y la base no cambian; las escrituras en Sigrid son las mismas
(mismo transfer, mismas guardas), solo para menos trabajadores.

## 10. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Preflight y ejecutar del paquete | (a) como el de un trabajador o el mes: lote completo, con las sobrantes (F-054) de los trabajadores del paquete; (b) como el de una obra: sin sobrantes | (a) | |
| D2 Qué entra de cada trabajador | (a) el trabajador entero (todas sus obras, `Postv-`, VAR, vinculados e incidencias), aunque el filtro de Obras o Partida case con una sola línea; (b) solo las líneas que casan con el filtro, sin sobrantes | (a) | |
| D3 Seleccionados ocultos por el filtro | (a) no van (selección ∩ visibles) y el modal dice cuántos; (b) van todos, se vean o no | (a) | (a), Pablo Gris 2026-11-27: «registra todos los que estan visibles, sin ocultos» |
| D4 Cómo se lanza | (a) un botón nuevo junto a «Completar al 100 %»; (b) dos botones fijos; (c) un menú en «Registrar en Sigrid»; (d) el botón actual pasa a ser el del paquete y el mes entero sale de la interfaz | (a) | (d), Pablo Gris 2026-11-27: «quiero que el registrar actual sea el boton registrar seleccionados. ya veremos otra forma de registrar. si solo hay 1 seleccionado (…, en ese caso sin seleccion) registra todos los que estan visibles» |
| D5 Cómo se enseña en el modal y al terminar | (a) título «· N trabajadores (seleccionados \| visibles)», lista plegable de nombres, línea de ocultos y aviso final «N trabajadores · …»; el resto, igual; (b) el modal de hoy sin cambios | (a) | |
| D6 Regla del 100 % | (a) como hoy: no bloquea ni avisa (cada trabajador va entero); (b) aviso informativo en el modal con los que no están OK; (c) no registrar a los que no están al 100 % | (a) | |
| D7 Tope de tamaño | (a) sin tope (sin filtros el botón es el mes; el corte lo recoge el hotfix y F-073); (b) tope configurable de trabajadores, 422 por encima; (c) aviso en el modal por número de obras | (a) | |
| D8 Contrato | (a) campo nuevo `trabajador_ides` (lista), excluyente con `trabajador_ide`, que se queda como está; (b) sustituir `trabajador_ide` por la lista; (c) mandar los filtros y que la api calcule los visibles | (a) | |
| D9 Editor abierto al pulsar | (a) guardar antes, como el «⇪ Registrar en Sigrid» del editor; (b) pedir que se cierre, como «Completar al 100 %» | (a) | |
| D10 Rótulo del botón | (a) «Registrar seleccionados (M)» / «Registrar visibles (N)»; (b) «Registrar en Sigrid» fijo y el alcance en un rótulo al lado | (a) | |
| D11 Varios seleccionados pero menos de 2 visibles | (a) botón desactivado, con el `title` «la selección está oculta por el filtro»; (b) se cuenta lo visible: con 0 o 1 a la vista, todos los visibles | (a) | |
