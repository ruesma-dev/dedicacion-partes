<!-- progress/spec_F-025_revision.md -->
# F-025 · Revisión de la spec tras F-034 y F-026 (2026-10-03)

Spec-author, rama `feature/F-025-obras-postventa-postv2` sobre `5895969`. Spec aprobada el
2026-10-01 (`d49348c`) con D2 = B, D6 y **D4 cambiada**. Ficheros:
`specs/F-025-obras-postventa-postv2/{requirements,design,tasks}.md`. Topes:
`python -m harness.tamano --feature F-025` → requirements 149/150, design 248/250.

**Resumen.** (1) D4 reescrita en su sitio y en todo lo que dependía de «POSTV2 por
empresa»: hay un único universo, el de la empresa de las obras. (2) La spec se ajusta al
código de `dev` (F-034, F-026). (3) La lista cerrada de tests anteriores que cambian se
ha **comprobado ejecutando**, no estimado: salen **ocho** tests de F-002, no los cuatro
aprobados, lo que abrió una decisión nueva, **D8**. **Decidido por el humano el
2026-10-03: D8 = A** (revisión aprobada; §4).

## 1. D4, sitio a sitio

`grep` de «D4», «por empresa», «empresas», «POSTV2», «empresa E» sobre los tres ficheros.

| Sitio | Antes | Ahora |
|---|---|---|
| req. D4 | «Otras empresas, por `#regla-empresa`, cada una con su POSTV2» | Solo la POSTV2 de Construcciones Ruesma: obras siempre de la empresa de las obras (F-034); un único universo; obra de otra empresa nunca admite postventa |
| req. Contexto | viñeta de la empresa 28 (6 hojas sin cero) y Porsan | retirada (ya no influye); nueva viñeta con F-034 y F-026; la POSTV antigua pasa a D6 |
| req. definición | «Universo de postventa de la empresa E» | universo de la empresa de las obras, con la obra de postventa de esa misma empresa |
| R1 | obras con `empresa` cada una | una `empresa` por petición y sus obras |
| R3 | «deja fuera todas las obras de E; `empresas[E].motivo`» | `obras` vacía y `motivo` |
| R4 | obra sin empresa válida → fuera del universo | petición sin empresa válida → 422 sin leer (ya no hay empresa por obra) |
| R5 | «motivo en cada empresa» | universo vacío con el motivo, sin leer Sigrid |
| R7 | «una vez por empresa y petición» | una sola vez por petición |
| R12 | todas las obras leídas, con su `empresa` | solo las de la empresa de las obras; las demás no se mandan |
| R13 | — | `admite_postventa` nunca en obra de otra empresa |
| R16 | «desglose por empresa y motivo de cada empresa» | `motivo_postventa` único |
| R17 | «las de la empresa **elegida**» (contrario a F-034) | las de la empresa de las obras, con cualquier elegida |
| R25 | — | «P5 en la empresa de las obras» |
| D3 | coste «~20 empresas × una lectura + dos presupuestos» (design §9) | dos lecturas por sync (obra de postventa y su presupuesto) |
| D5 / design §9 | «empresas sin POSTV2 dejan de ofrecer `Postv-`» | retirado: con F-034 ninguna obra de otra empresa se ofrece |
| design §1 | diagrama «obra POSTVENTA_OBRA_COD de cada empresa»; respuesta `empresas: {E: …}` | la de ESA empresa; respuesta plana `obra_postventa`, `motivo`, `casadas` |
| design §3 (l. 58 vieja) | `conftest.py` «admite POSTV2 por empresa (R3, D4)» | solo contadores; ausente/ambigua con `ClienteEmpresas` de `test_f022_…` |
| design §4.1 | `calcular(obras)` agrupa por empresa | `calcular(empresa, obras)`, una carga |
| design §5 | contrato con `empresa` por obra y `empresas` | `{"empresa", "obras"}` → respuesta plana; 422 por empresa |
| design §7 | «POSTV2 en 1 y 28; ausente en 18»; cruce con «otra empresa» | presente/ausente/ambigua; una obra de la 28 que no va al gateway |
| tasks T2, T6, T13 | universo por empresa; «cuadrante de la 1» | `calcular(empresa, obras)`; solo obras de la empresa de las obras; cualquier elegida |

**Simplificaciones derivadas (no son decisiones nuevas, pero cambian lo aprobado):** el
contrato pasa a una empresa por petición, como el preflight (`#regla-empresa`: «una
petición es de una sola empresa»), y por eso R4 cambia de «obra fuera» a 422. D3 sigue
igual (el sync falla entero); solo baja su coste. D5 pierde la mitad que hablaba de
empresas sin POSTV2.

## 2. Contraste con `dev` (F-034, F-026)

- **R17 contradecía F-034** («empresa elegida»): corregido. El cuadrante ya filtra por
  `filtro.empresa_obras` (`ObtenerCuadrante`).
- **Empresa que manda la api**: `settings.empresa_imputacion`, la misma que `RegistroSigrid`
  pone en cada línea; `deps.py` comparte un solo `TransferClient`.
- **Errores de la api**: el 502 se declara en la tabla `_HTTP_POR_ERROR` de `app.py`.
- **`TransferClient` sin estado**: la versión aprobada «guardaba `empresas` para el
  preview»; ahora el gateway devuelve `ResultadoUniverso(ides, motivo)`.
- **R20**: `GuardarAsignaciones` ya lee `antes`; se usa como «líneas previas» en vez de
  añadir un parámetro a `_validar_lineas`.
- **Transfer**: se reutiliza `ObraIn` y `empresa_valida`; Pydantic convierte `true` en 1,
  así que «booleana» sale de R4 (no se podía cumplir con `Optional[int]`).
- **F-026**: el cruce R2 compara `capitulo_postventa`, no la acción (que depende de las
  horas del recurso); `conftest.linea()` ya trae `recurso_ide=200`. M2 exige un
  trabajador vigente en el mes (si no, la línea va a `no_vigentes`) y comprueba
  `no_vigentes: []`; el script sigue el patrón de `scripts/verif_f034_f026.ps1`.
- **R25**: `FUENTES_SIN_LITERAL` de `test_f002_fuente_unica.py` es una tupla cerrada que
  no ve el módulo nuevo; la verificación de T9 no lo cubría. Se comprueba en
  `test_f025_universo_postventa.py` sin tocar el de F-002.
- **Texto de `#regla-p5`**: lo vigilan `test_f022_r22_…` (enlace `(#regla-empresa)`) y
  `test_f002_r4_…` (línea «Confirmado por»); la spec obliga a conservarlos.
- **Front**: la función de copia es `copiarDeArriba`; la marca `chip-otra-empresa` de
  F-034 no cambia. Ningún test del front lee esas partes de `app.js`.
- **T3** añade `test_f013_sin_partida.py` a su verificación: busca el texto «no casa».

## 3. Lista cerrada de tests anteriores, comprobada

Método: copia del repositorio en el scratchpad (`git archive HEAD`), con la forma mínima
de la spec aplicada (resolver D2 = B; columna, marcas, `ofrecible`, firmas de
`FetchObrasStep`/`PreviewSync`, R20, schemas y `deps.py` en la api; catálogo y PV en el
front). Nada de eso está en el repositorio. Línea base: transfer 330, api 440, front 21.

- **Transfer**: 8 fallos, todos en `test_f002_postventa.py`. Por escalón retirado (D2,
  aprobados): `r18_la_cascada_solo_actua_sin_exacto`, `r18_el_ultimo_escalon_casa_por_nombre_de_obra`
  y los dos `r19` (prefijo `06` + dígitos). Por la obra-capítulo `0678` → `0678.MO` del
  presupuesto `capitulos` (D8 = A, aprobados el 2026-10-03): `r16_el_capitulo_no_llega_al_paride_de_la_linea`,
  `r16_un_override_manual_a_un_capitulo_se_omite`, `r16_un_override_manual_a_una_hoja_si_vale`
  y `r17_el_automatico_y_el_desplegable_comparten_universo[capitulos]`. Quitar
  `self._nodos_pv` no rompe ninguno más.
- **API**: 46 fallos, todos de firma o de doble: `PreviewSync` (15) y `FetchObrasStep`
  (5) sin gateway, `_Obras` sin `modos_ofrecibles` (10), `TransferClient` real en los
  `_contenedor` (7), filas de `sincronizar` sin marcas (5), `CAMPOS_LINEA` (3), un
  `SimpleNamespace` sin `admite_postventa` (1). Con los ajustes de design §7.1 la suite
  queda en **440/440**: ningún valor esperado cambia salvo `CAMPOS_LINEA` (R18).
- **Front**: 21/21 sin tocar ningún test. **Raíz**: no se ejecutó la simulación de docs;
  las dos restricciones de texto conocidas están en design §3.

La lista completa, con nombres, está en design §7.1.

## 4. D8 = A · Decidido por el humano el 2026-10-03

**D8 · La obra-capítulo con D2 = B.** R10 («código exacto o prefijo seguido solo de
letras») no distingue `0678` → `0678.MO` (obra que fuera capítulo con partidas debajo)
de `CP` → `CP.1` (falso casado que D2 quita): las dos son prefijo + punto. Con D2 = B
ambas quedan fuera, y por eso cambian cuatro tests de F-002 más que los cuatro que
nombró la aprobación del 2026-10-01.

**Decisión (A):** se acepta. En el presupuesto real no hay ninguna obra-capítulo (las 86
partidas de obra son hojas, `progress/sigrid_F-002.md` §C2), y las 83 obras del universo
esperado casan por exacto o sufijo de letra. Los cuatro tests se reescriben probando lo
mismo (ningún capítulo como `paride`; override a capítulo omitido y a hoja respetado)
sobre el presupuesto `hojas`. Con ello, los **ocho** tests de F-002 de design §7.1 quedan
aprobados.

Descartadas en una línea: la excepción al capítulo de código exacto (volvería a casar
`CP` → `CP.1`) y ampliar R10 a prefijo + `.letras` (rama de P5 sin caso real).

Sitios cerrados el 2026-10-03: requirements (encabezado de Decisiones, D2, D8), design
(cabecera y §7.1), tasks (cabecera) y este informe (resumen, §3 y §4).

## 5. Observaciones (no son decisiones)

- `Linea.ofrecible` no mira la empresa: una línea normal en una obra activa de otra
  empresa sigue siendo «ofrecible» y conserva la marca `otra_empresa` de F-034. Es lo
  mismo que hoy; cambiarlo sería otra feature.
- El override manual de postventa no rescata una obra que no casa: el preflight la omite
  antes de mirar el `paride` (comportamiento de hoy, coherente con el universo).
- No se ha tocado `harness/features.json` ni `progress/current.md`.
