<!-- specs/F-044-recursos-vinculados/requirements.md -->
# F-044 · Registrar los recursos vinculados con el % del trabajador

Rigor **`critico`** (escribe en Sigrid). Toca **los tres servicios**: la api
trae el vínculo en el sync, guarda la partida elegida de cada vinculado y lo
manda en el contrato; el transfer, única pluma, propone, decide y escribe; el
front pinta subfilas y selector (design §1). **Todas las decisiones, cerradas
por el humano el 2026-10-25** (design §9): D1 cualquier tipo vinculado, D2 el
campo de Sigrid, D4 la CI de su tipo y el mismo % que el titular en cada obra
(también postventa y VAR), D7 con D4, D8 columna «tipo recurso» y subfila con
partida editable; D1b, D3, D4b, D5, D6 y D9-D15 con la opción A («ok a todo»).
Cada `[Dn]` remite a su decisión. Fuera: mensajería (F-052), traer
% de Sigrid (F-054), rachas (F-062), deshacer en Sigrid (F-033) y `partes`.

## 0. Lo que hay en Sigrid (solo lectura)

Detalle en `progress/explore_F-044_sigrid.md`. El vínculo es el campo extendido
**«Recurso Asociado»** (`defext` 46, `conext.cod = '5'`, `valn` = `res.ide` del
principal): 538 recursos no persona lo tienen, siempre hacia una persona de su
empresa. Teléfono, gasoil y vehículo se imputan hoy como la persona (mismo
parte, mismo %, `pre` de `reshor`, cuenta de `reshor.caaide`); su partida es la
hoja **CI cuya cuenta tiene la subcuenta del vinculado** (`CICO13` ↔ `CI.4.13`)
y, si el titular va a postventa, VAR o `CP*`, la del titular. Glosario:
**vinculado** = recurso no persona con el campo hacia un trabajador;
**titular** = la línea de % de ese trabajador en una obra.

## 1. El vínculo (api, en el sync)

- **R1.** `[D1]` El sync de maestros lee de Sigrid los recursos no persona con
  el campo de `sync.vinculados` de `config.yaml` (código del campo y tabla), de
  **cualquier** clasificación, con tipo y su descripción (`auxrestip`),
  código, descripción, empresa, baja y hora por defecto (`res.horide`).
- **R2.** `[D2]` Un vinculado es del trabajador cuyo `ide` es el valor del
  campo. Lo decide **una** función pura de `dedicacion-api/domain/`. Un
  trabajador tiene **todos** sus vinculados.
- **R3.** Con el campo vacío o hacia un recurso que no es trabajador de
  dedicación, no se vincula; el preview del sync publica cuántos y sus códigos
  (para que Administración rellene el campo). No se casa por nombre. `[D1b]`
  Un tipo de `tipos_excluidos` (hoy `VP`) no se vincula y el preview lo cuenta.
- **R4.** El vinculado cuenta en el mes M con `vigente_en` sobre su propia
  baja (`#regla-recurso`).
- **R5.** El vínculo se guarda en `recurso_vinculado` (ORM). El que sale del
  sync o pierde su trabajador queda inactivo; no se borra. Si el sync falla,
  no se persiste nada.

## 2. Cuadrante (api y front)

- **R6.** `[D8]` El cuadrante gana la columna **«Tipo recurso»** (`Persona` en
  la fila del trabajador) y, bajo cada línea (obra + modo) de un trabajador con
  vinculados vigentes en el mes, **una subfila por vinculado** con su tipo, su
  código y la partida a la que va. Sin vinculados, la fila es la de hoy.
- **R7.** El % de la subfila es el de su titular y no se edita: el que se pone
  al titular en una obra se aplica tal cual al titular y a sus vinculados.
- **R8.** `[D8]` La partida de la subfila se **cambia** con el selector de
  F-050 (`#regla-partida`: catálogo de la obra, botones CD · CI · CP, orden
  natural). Se guarda como elegida en `asignacion_vinculado`; cambiarla deja
  un evento que se deshace como cualquier otro (`#regla-deshacer`); guardar la
  fila la conserva y copiar el mes la copia.
- **R9.** Sin elegida, la subfila enseña la **propuesta** (R15-R17) en cursiva
  con su método, calculada por el transfer con la misma función que el
  preflight, y la api la guarda como en F-055. El front no calcula nada.

## 3. Contrato api → transfer

- **R10.** `[D13]` Cada línea de % de un periodo ≥ `sync.vinculados.desde`
  lleva `vinculados` (`recurso_ide`, tipo, descripción del tipo, partida
  elegida o propuesta guardada, `hmores_ide`). Lo manda la api; el transfer
  no busca vínculos.
- **R11.** Sin `vinculados`, una línea se decide **exactamente igual** que
  antes de F-044, con las mismas lecturas.

## 4. Qué se escribe (transfer)

- **R12.** `[D4]` Por cada titular que se escribe o se edita y cada vinculado,
  **una** línea en el mismo parte, con la `fec` y el `can` **del titular** en
  esa obra (normal, postventa o VAR, sin normalizar), la hora por defecto del
  vinculado, `pre` = su `reshor.pre` y `tot = round(can × pre, 2)`. Cuenta por
  `#regla-analitica` con su recurso y hora; modo pruebas y empresa, como
  cualquier línea.
- **R13.** `[D9]` `synckey` `porcentajes:vin:{registro_id}:{recurso_ide}`;
  reejecutar no duplica (`ya_registrado`).
- **R14.** `[D1b, D3]` Sin su hora en `reshor` o con `pre` 0, el vinculado se
  omite con motivo «sin importe mensual», tipo y hora; el titular no cambia.
- **R15.** `[D4]` Partida si el titular va a una partida `CI*` de una obra
  normal: la elegida si es hoja activa del presupuesto (si no, omitida con
  motivo, como F-050); si no hay elegida, la **única** hoja activa de la obra
  cuya cuenta tiene la subcuenta de la cuenta del vinculado (su «CI»).
- **R16.** `[D4b]` Si esa hoja no existe o hay varias, `#regla-sin-partida`
  por línea (nunca la primera); se elige en la subfila o en el modal.
  *Enmienda F-068 (2026-10-28) de R15-R16: antes, historial en la obra; varias ⇒ nombre y CI.4.*
- **R17.** `[D4b]` Si el titular va a postventa, a una entrada VAR o a una
  partida que no es `CI*` (`CP*`, `CD*`), el vinculado va a la **partida del
  titular**, salvo elegida válida.
- **R18.** `[D10]` Titular omitido o retenido por un aviso sin confirmar ⇒ sus
  vinculados se omiten («sigue al trabajador» y su motivo). Titular **ya
  registrado** ⇒ cada vinculado se decide solo.
- **R19.** Las líneas de vinculado no suman a la jornada del trabajador
  (`#regla-capacidad`) ni son su pisado ni su línea al 0 %: una `MESVE`
  (empieza por `M`) no es `M*` del trabajador.

## 5. Lo que ya está en el parte (como el % normal)

- **R20.** `[D6]` Identidad de `#regla-conflicto` (recurso vinculado, mes, hora,
  partida) en todos los partes del periodo de la obra destino: un choque En
  registro es un **pisado a confirmar** por vinculado, que **edita** el de
  menor `ide` y pone a 0 los demás (`#regla-cero`).
- **R21.** `[D6]` Una línea del vinculado con su hora y `can` 0 o nulo en un
  parte En registro del periodo es **pisable sin confirmar** (emparejado de
  `#regla-cero`) y el preflight lo avisa.
- **R22.** Un choque en un parte cerrado omite la línea (`parte_cerrado`); en
  un cerrado nunca se escribe ni se edita; nunca se emite `DELETE`.
- **R23.** `[D11]` Capacidad del vinculado: la suma de `can` de sus líneas de
  esa hora en los partes de la obra y el mes (cerrados incluidos), con lo
  nuevo y los pisados confirmados, no pasa de 1 (tolerancia 0,00005); si se
  pasa, **sobrecarga a confirmar** de ese vinculado.
- **R24.** Cada `UPDATE` de una línea de vinculado lleva la guarda de
  `#regla-cero` con **su** hora (no `M*`).

## 6. Preflight, ejecutar, lecturas y traza

- **R25.** Preflight y `ejecutar` devuelven `vinculados` (una entrada por
  línea: `registro_id`, recurso, tipo, acción, hora, `can`, `pre`, `tot`,
  partida y método, parte, `linea_cero`, `hmores_ide`, motivo) solo si la
  petición los trae; sus conflictos van en `conflictos` con su clave, tipo y
  código.
- **R26.** Se confirman como hoy (`pisar_claves`), cada uno por separado: el
  del titular no confirma el del vinculado ni al revés.
- **R27.** Lecturas: `reshor` de los vinculados en la misma lectura que la de
  los trabajadores; sus líneas en la misma de líneas del periodo; las cuentas
  de las hojas de la obra, **una** lectura más, solo si alguno necesita
  propuesta. Un fallo o `truncated`: falla sin escribir.
- **R28.** En `ejecutar` el vinculado se escribe después de su titular; si el
  titular no queda escrito, el vinculado sale en `omitidas`.
- **R29.** Suelto, por lote y en `partidas/propuesta(-lote)` el resultado es el
  mismo (F-055).
- **R30.** La api guarda por asignación y vinculado estado, parte, motivo y
  `hmores.ide` en `asignacion_vinculado`, y manda ese `hmores.ide` después.

## 7. Modal, documentación y verificación

- **R31.** El modal de registro enseña los vinculados bajo cada línea del
  trabajador (acción, %, partida con el selector de F-050) y sus avisos en la
  lista de siempre, con tipo y código.
  *Enmienda F-064 (2026-10-26) de R20 y R31: su pisado sale marcado, desmarcable.*
- **R32.** `docs/ARCHITECTURE.md` gana `#regla-vinculado` (fuente única,
  `ANCLAS`), remitida desde `#regla-capacidad`, `#regla-cero` y
  `#regla-partida`; `docs/INTEGRACION.md` §1, §5 y §7.
- **R33.** MANUAL del humano en modo pruebas con Administración (tasks T21).
- **R34.** Al desplegar, `azure-apps/dedicacion.md` y el **aviso a `partes`**
  (lo transmite el humano): dedicación escribe y edita líneas de recursos no
  persona (`OTEL`, `OGAS`, `MESVE`…) en los partes compartidos.
