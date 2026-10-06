<!-- specs/F-039-obras-var-y-seis-digitos/requirements.md -->
# F-039 · Obras VAR por partidas (desde la 29) y fuera las obras de 6 dígitos — requisitos

Rigor **crítico**: cambia qué se escribe en Sigrid y el transfer desplegado escribe de verdad
(`docs/INTEGRACION.md` §8). Servicios: **transfer** (universo VAR y validación al registrar),
**api** (filtro de código, entradas, registro), **front** (una condición de pintado).

**Base (humano, 2026-10-06):** «añade como se ha hecho en postventa la obra de código VAR, hay
que coger sus partidas, pero a partir de la que empieza por 29 (inclusive), si empieza por un
número inferior no. Por otro lado las obras con código de 6 números juntos o más ignóralas».

## Contexto (lecturas de solo lectura del 2026-10-06, sigrid-api y BBDD local)

- **VAR** «OBRAS VARIAS», empresa 1: `con.ide` 683806, estado 15 = **EN CURSO**, que
  `estados_excluidos` **no** excluye: hoy se ofrece como obra normal (local: `activa`, 0
  asignaciones). Centro 683807 (`VAR`), con cuentas `VAR.CIMO01`…`VAR.CIMO16`.
- Su presupuesto: 136 partidas; 29 hojas activas `01`…`29` colgando de `CD` (52979), cada una
  una obra pequeña; el resto `CI.*`, `CI.03P.*`, `CP`… (ningún otro código empieza por cifra).
  Hoy entra solo la **29** (ide **417055**, «ACOND. NAVE MODUL-A, ARROYOMOLINOS»).
- Líneas `hmores` en VAR: todas en partidas numeradas (o `paride` 0), **ninguna** en `CI.*`
  ni con `synckey` nuestra. En la 29: 4 líneas de 2026-08 (MESVE, MPRL, OGAS, OTEL) de
  Administración. La VAR de la empresa 28 no cuenta: las obras son de la empresa de las obras.
- **6+ dígitos seguidos**: 240 obras (239 de la empresa 1, 1 de la 25): 196 EN ESTUDIO, 28
  ADJUDICADA DEF., 15 EN CURSO (13 «OBRA PRUEBA…», 150414 y 150703). Ninguna con parte desde
  2024 ni partida en POSTV2. Local: las 240 `activa`, **0 asignaciones**.

**Entrada VAR**: una partida VAR ofrecida como obra propia del cuadrante. **Partida VAR**: hoja
activa del presupuesto de la obra `VAR_OBRA_COD` de la empresa de las obras que cumple R2.

## Transfer: el universo VAR, en un solo sitio

R1. CUANDO llega `POST /api/var/universo` con una `empresa`, el sistema debe devolver la obra
`VAR_OBRA_COD` de esa empresa (`ide`, `codigo`, `nombre`, `empresa`), el umbral y sus partidas
VAR (`ide`, `cod`, `res`) ordenadas por `ide`, leyendo la obra y su presupuesto una sola vez y
sin escribir en Sigrid.

R2. [D3] El sistema debe tomar como partida VAR la hoja activa cuyo **número inicial** del
código (los dígitos con que empieza) sea ≥ `VAR_PARTIDA_DESDE` (29 por defecto): `29`, `30`,
`100`, `029`, `29.1` y `29A` sí; `28`, `05`, `CI.1.1`, un capítulo o una partida de baja, no.

R3. SI la obra VAR no existe en la empresa o es ambigua, o `VAR_OBRA_COD` está vacío,
ENTONCES el sistema debe devolver `obra_var: null`, `partidas: []` y el motivo (vacío: sin
leer Sigrid).

R4. SI la empresa no es válida, ENTONCES 422 `{"ok": false, …}` sin leer Sigrid; SI falla una
lectura, ENTONCES 502, nunca un universo parcial.

R5. CUANDO una línea del preflight trae `var_paride`, el sistema debe imputarla a esa partida
(`paride`, `partida_cod`, `partida_metodo = "var"`), sin casado por categoría ni nombre, si y
solo si `var_paride` está en el universo VAR de la empresa de la línea, calculado con las
**mismas** funciones que R1, y la obra de la petición es esa obra VAR.

R6. SI la línea con `var_paride` no cumple R5 (partida fuera del universo, otra obra, sin
universo por R3) o es de postventa, ENTONCES el sistema debe omitirla con un motivo que nombre
la partida o la obra, sin aviso de «sin partida».

R7. El `paride` manual que acompañe a una línea con `var_paride` no debe cambiar su partida.

R8. La línea VAR debe seguir las reglas de siempre: modo pruebas (`#regla-pruebas`, a `0404`
con la partida VAR), cuenta del centro de la obra destino (`#regla-analitica`), parte del
periodo, `synckey` `porcentajes:{id}`, identidad con su partida (`#regla-conflicto`) y
capacidad (`#regla-capacidad`).

R9. Una línea sin `var_paride` debe tratarse exactamente como hoy.

## API: filtro de código, entradas y registro

R10. [D4] CUANDO se sincronizan los maestros o se pide el preview, el sistema debe descartar,
antes de pedir ningún universo, toda obra cuyo código contenga N o más dígitos seguidos, con
N = `sync.obras.digitos_seguidos_excluidos` de `config.yaml` (6; 0 = sin filtro), lleve o no
letras o sufijo: `150414`, `0902051`, `090205A` y `150301-1` caen; `12345` y `VAR` no.

R11. Una obra descartada por R10 no debe mandarse al universo de postventa ni guardarse; si ya
estaba en la base, debe quedar con `activa` y `admite_postventa` a `false`.

R12. CUANDO se sincronizan los maestros o se pide el preview, el sistema debe pedir al
transfer **una vez** el universo VAR de la empresa de las obras.

R13. [D2, D6] El sync debe guardar cada partida VAR como una fila de `obra` con `ide` = −(ide
de la partida), `cod` = `<código de la obra VAR>-<código de la partida>` (`VAR-29`),
`descripcion` = su `res`, la empresa de la obra VAR, `activa = true`, `admite_postventa =
false`, y `registro_obra_ide`, `registro_obra_cod` y `registro_paride` (obra y partida de
Sigrid donde se registra). Las obras normales llevan esas tres a `NULL`.

R14. [D1] El sistema debe guardar la obra VAR que devuelve el universo con `activa = false`,
sea cual sea su estado.

R15. SI una partida deja de estar en el universo, ENTONCES su entrada debe quedar con `activa
= false` en el sync siguiente, sin borrar nada.

R16. SI el transfer no responde al universo VAR, o responde sin `ok: true` o sin `partidas`,
ENTONCES el sync y el preview deben fallar enteros con HTTP 502 nombrando el universo VAR, sin
persistir nada (como F-025 D3).

R17. El preview debe publicar en `obras`: `excluidas_por_codigo`, `muestra_excluidas_por_codigo`
(hasta 10 códigos), `entradas_var`, `obra_var` (código o `null`) y `motivo_var`.

R18. Las tres columnas de R13 deben declararse, nulables, solo en el ORM, con el `ALTER`
derivado por `esquema.py`.

R19. [D5] Las líneas ya guardadas en una obra o entrada que deja de ofrecerse (R11, R14, R15)
deben conservarse con `ofrecible = false` (F-025): cuentan para el 100 %, no se copian, no se
aceptan nuevas y el registro las manda como hoy.

R20. CUANDO se registra (preflight o ejecutar), el sistema debe mandar las líneas de las
entradas en la petición de su `registro_obra_ide`, junto a las demás de esa obra, con
`var_paride` = `registro_paride` y sin `paride` manual; las demás líneas, como hoy.

R21. Una entrada debe comportarse en cuadrante, Completar, copias, guardar, deshacer y Excel
como cualquier obra normal: código `VAR-29`, su descripción y sin modo postventa.

## Front: solo pinta

R22. CUANDO el preflight trae una acción `escribir` con `partida_metodo = "var"`, el front debe
enseñar su `partida_cod` fija en vez del desplegable de partida; sin otro cambio ni literal de
la obra VAR en `app.js`.

## Documentación

R23. `docs/ARCHITECTURE.md` debe tener la regla `#regla-var` (universo, entrada, registro) y
`#regla-seis-digitos`, citadas en la lista de anclas y en la tabla `obra`, y
`test_f002_fuente_unica.py` debe vigilarlas.

R24. `docs/INTEGRACION.md` debe documentar el endpoint (§5), los ajustes del transfer (§3), el
orden de despliegue transfer → api y lo que se rompe (§7); `azure-apps/dedicacion.md` se
refresca (commit del humano).

## Decisiones (todas decididas por el humano el 2026-10-06: D4 con sus palabras, el resto «lo demás ok»)

- **D1 = A · VAR no se ofrece como obra normal**, solo sus entradas `VAR-NN` (R14): nadie
  imputa M* a `CI.*` de VAR. Descartada B (seguir ofreciéndola, con cascada a `CI.1.x`).
- **D2 = A · Entrada `VAR-29` con la descripción de la partida** (R13). Descartadas B (código
  `29`, descripción `VAR · …`) y C (`VAR29`).
- **D3 = A · «Empieza por 29» es número inicial ≥ 29** (R2; `29.1` entra). Descartadas B
  (códigos numéricos con valor ≥ 29) y C (texto ≥ `'29'`: `'3'` entraría y `'100'` no). El 29 es
  ajuste del transfer (`VAR_PARTIDA_DESDE`), no constante.
- **D4 · Fuera toda obra cuyo código CONTENGA 6 o más dígitos seguidos** (R10): «si tienen 6
  números seguidos también ignóralas». Solo numéricas (`090201`, `0902051`) y con letras o
  sufijo (`090205A`, `150301-1`, `160304-LOCAL`): las 240, sin excepciones. Ojo: `240101`,
  `250801` y `260901` son de 2024-2026 (EN ESTUDIO); si una se adjudica así, no saldrá.
- **D5 = A · Las líneas ya guardadas en obras que desaparecen se quedan marcadas** (R19), como
  en F-025; local: cero. Descartadas B (no mandarlas al registro) y C (borrarlas).
- **D6 = A · La entrada es una fila propia de `obra`** (R13): solo `ADD COLUMN`. Descartada B
  (`paride` en la clave de `asignacion`: migración a mano y tocar todo lo que usa `obra_ide`).
