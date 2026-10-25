<!-- specs/F-044-recursos-vinculados/requirements.md -->
# F-044 · Registrar los recursos vinculados con el % del trabajador

Rigor **`critico`** (escribe en Sigrid). Toca **los tres servicios**: la api
casa y guarda el vínculo (es un maestro) y lo manda en el contrato; el
transfer, única pluma, decide y escribe las líneas; el front las enseña
(design §1). Pedida por el humano el 2026-10-07 y 2026-10-08; alcance de Juan
Romero el 2026-10-08: «solo los recursos persona, gasoil, vehículo y
teléfono» van por porcentaje. **Decisiones abiertas D1-D15 en design §9**:
cada R marcado `[Dn]` está escrito con la opción recomendada y cambia si el
humano elige otra. Fuera: kilómetros (`VP`/`KM`), cajas, viajes, mensajería
(F-052), traer % de Sigrid (F-054), rachas de incidencia (F-062), deshacer en
Sigrid (F-033) y el repositorio `partes`.

## 0. Lo que hay en Sigrid (solo lectura)

Detalle en `progress/explore_F-044_sigrid.md`. No hay vínculo estructurado
(`resres` vacía, sin conductor, sin CIF): el vinculado se llama
`<CONCEPTO> <nombre del recurso persona>`, y casado así cada vinculado activo
da 0 o 1 mensual. Teléfono (`TF`, hora `OTEL`), gasoil (`CO`, `OGAS`) y
vehículo (`VE`, `MESVE`) llevan importe mensual en `reshor` y hoy se
imputan como la persona: mismo parte, `can` = su %, `pre` = `reshor.pre`,
una línea por cada `M*` suya, la cuenta de su `reshor.caaide` y, en obra
normal, la partida de su concepto (`CI.4.13`, `CI.4.1`, `CI.03P.9`…).
Glosario: **vinculado** = recurso no persona casado con un trabajador;
**titular** = la línea de % del trabajador de la que cuelga.

## 1. El vínculo (api, en el sync)

- **R1.** `[D1]` El sync lee de Sigrid los recursos `res.cla = 0` cuya
  clasificación (`auxrestip.cod`) esté en `sync.vinculados.tipos` de
  `config.yaml` (`TF`, `CO`, `VE`), de todas las empresas, con su código,
  descripción, empresa, baja y hora por defecto (`res.horide`).
- **R2.** `[D2]` Un vinculado es de un trabajador si y solo si su
  descripción, sin espacios en los extremos, **termina** en un espacio
  seguido del nombre exacto del trabajador y los dos son de la **misma
  empresa**. Lo decide **una** función pura de `dedicacion-api/domain/`.
- **R3.** Si casa con ninguno o con varios trabajadores, no se vincula; si un
  trabajador casa con dos vinculados del mismo tipo, no se vincula ninguno de
  ese tipo. **Nunca se elige el primero.** El preview del sync publica
  cuántos hay de cada caso y sus códigos.
- **R4.** El vinculado cuenta en el mes M con la regla de vigencia del
  trabajador (`vigente_en`, `#regla-recurso`) sobre su propia baja.
- **R5.** El vínculo se guarda en la tabla `recurso_vinculado` (ORM). Un
  vinculado que sale del sync o pierde su trabajador queda inactivo; no se
  borra. Si el sync falla, no se persiste nada (como hoy).

## 2. Contrato api → transfer

- **R6.** `[D13]` Cada línea de % de un periodo ≥ `sync.vinculados.desde`
  lleva `vinculados`: los vigentes en el mes de su trabajador (`recurso_ide`,
  `tipo`, descripción del tipo). La api manda; el transfer no los busca.
- **R7.** Una línea sin `vinculados` (o con la lista vacía) se decide
  **exactamente igual** que antes de F-044, con las mismas lecturas.

## 3. Qué se escribe (transfer)

- **R8.** `[D3, D7]` Por cada titular que se escribe o se edita y cada
  vinculado suyo, **una** línea en el **mismo parte** que el titular, con la
  `fec` del titular, `can` = el del titular, la hora por defecto del vinculado,
  `pre` = su `reshor.pre` para esa hora y `tot = round(can × pre, 2)`.
- **R9.** La cuenta analítica sale de `#regla-analitica` con el recurso y la
  hora del vinculado; el modo pruebas, la empresa y el alta protegida, como
  cualquier línea (`#regla-pruebas`, `#regla-empresa`).
- **R10.** `[D9]` Su `synckey` es `porcentajes:vin:{registro_id}:{recurso_ide}`;
  reejecutar no duplica (`ya_registrado`).
- **R11.** Si el vinculado no tiene en `reshor` su hora por defecto, o su
  `pre` es 0, se omite con un motivo que nombra el tipo y la hora; el titular
  no cambia.
- **R12.** `[D10]` Si el titular se omite o queda retenido por un aviso sin
  confirmar, sus vinculados se omiten con «sigue al trabajador» y el motivo
  del titular. Si el titular está **ya registrado**, cada vinculado se
  decide solo (el que falta se escribe).
- **R13.** `[D4]` Partida en obra normal: la propuesta de `#regla-partida`
  calculada para el **recurso y la hora del vinculado** (parte anterior en
  esa obra → casamiento con la descripción de su tipo como categoría →
  último parte trasladado). Sin propuesta, `#regla-sin-partida` por línea.
- **R14.** `[D4]` En postventa, la partida del titular (`#regla-p5`); en una
  entrada VAR, la de la entrada (`#regla-var`). Sin ella, como el titular.
- **R15.** Las líneas de vinculado **no suman** a la jornada del trabajador
  (`#regla-capacidad`), ni son su pisado ni su línea al 0 %: una `MESVE`
  (empieza por `M`) de su vehículo no cuenta como `M*` del trabajador.

## 4. Lo que ya está en el parte

- **R16.** `[D6]` Identidad: la de `#regla-conflicto` (recurso vinculado,
  mes, hora, partida) en todos los partes del periodo de la obra destino.
  Un choque En registro es un **pisado a confirmar**, uno por vinculado, que
  **edita** el de menor `ide` y pone a 0 los demás (`#regla-cero`).
- **R17.** `[D6]` Una línea del vinculado con su hora y `can` 0 o nulo, en
  un parte En registro del periodo, es **pisable sin confirmar** con el
  emparejado de `#regla-cero` (misma partida > menor `ide`), y el preflight
  lo avisa.
- **R18.** Un choque en un parte cerrado omite la línea (`parte_cerrado`).
  En un cerrado nunca se escribe ni se edita; ningún caso emite `DELETE`.
- **R19.** `[D11]` Capacidad del vinculado: la suma de `can` de sus líneas
  de esa hora en los partes de la obra y el mes (cerrados incluidos), más lo
  nuevo y suponiendo confirmados los pisados, no pasa de 1 con la tolerancia
  0,00005; si se pasa, **sobrecarga a confirmar** de ese vinculado.
- **R20.** Cada `UPDATE` de una línea de vinculado lleva la guarda de
  `#regla-cero` con **su** hora (no `M*`): mismo `ide`, recurso, `can` y
  `synckey` leídos, sin enlaces y parte En registro.

## 5. Preflight, ejecutar, lecturas y traza

- **R21.** Preflight y `ejecutar` devuelven `vinculados`: una entrada por
  línea (`registro_id`, recurso, tipo, acción, hora, `can`, `pre`, `tot`,
  partida y método, parte, `linea_cero`, `hmores_ide`, motivo y aviso), solo
  si la petición trae vinculados. Sus conflictos van en `conflictos`, con su
  propia clave y el tipo y código del vinculado.
- **R22.** Los avisos se confirman como hoy (`pisar_claves`): confirmar el
  del titular no confirma el de su vinculado ni al revés.
- **R23.** Lecturas: las horas de los vinculados van en la **misma** lectura
  de `reshor` que las de los trabajadores, y sus líneas en la misma de
  líneas del periodo; el historial de sus partidas es **una** lectura más por
  petición, solo si alguno necesita propuesta. Un fallo o un `truncated`:
  la petición falla sin escribir nada.
- **R24.** En `ejecutar`, la línea del vinculado se escribe después de la de
  su titular, en el mismo parte; si el titular no queda escrito (guarda,
  relectura), el vinculado no se escribe y sale en `omitidas`.
- **R25.** Suelto y por lote (`registro/preflight-lote`) dan el mismo
  resultado (F-055), con las lecturas de R23.
- **R26.** La api guarda por asignación y vinculado su estado, parte, motivo
  y `hmores.ide` (tabla `registro_vinculado`), y manda ese `hmores.ide` en el
  siguiente registro para reconocer la línea (`#regla-cero`, localizar lo
  nuestro).

## 6. Front (solo pinta)

- **R27.** `[D8]` El cuadrante marca en la fila del trabajador los tipos de
  sus vinculados del mes (`TF · CO · VE`), con el código de cada uno en el
  título; lo trae la api en el cuadrante. Sin vinculados, nada.
- **R28.** `[D8]` El modal de registro enseña, bajo cada línea del
  trabajador, sus vinculados con la acción, el % y la partida, y sus avisos
  en la lista de siempre nombrando el tipo y el código. El front no calcula.

## 7. Documentación y verificación

- **R29.** `docs/ARCHITECTURE.md` gana `#regla-vinculado` (fuente única,
  `ANCLAS` de `test_f002_fuente_unica.py`) y la remiten
  `#regla-capacidad`, `#regla-cero` y `#regla-partida`; `docs/INTEGRACION.md`
  §1, §5 y §7 (lectura nueva de `res`, contrato `vinculados`, salida).
- **R30.** MANUAL del humano, en modo pruebas y con Administración: un
  trabajador con teléfono, gasoil y vehículo, en una y en dos obras, con una
  línea de vinculado al 0 % y otra metida a mano (tasks T19).
- **R31.** Al desplegar: `azure-apps/dedicacion.md` y el **aviso a
  `partes`** (lo transmite el humano): dedicación escribe y edita líneas
  `OTEL`, `OGAS` y `MESVE` de recursos no persona en los partes compartidos.
