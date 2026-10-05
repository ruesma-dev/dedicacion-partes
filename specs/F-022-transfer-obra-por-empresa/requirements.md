<!-- specs/F-022-transfer-obra-por-empresa/requirements.md -->
# F-022 · El transfer busca cada obra por código y empresa — requisitos

Rigor **crítico**. Servicios: transfer (resuelve las obras) y API (pone la
empresa en cada línea); el front no se toca. Origen:
`progress/explore_maestros_sync.md` §D. Bloquea F-018.

## Contexto (hechos, no requisitos)

El código de obra solo es único **dentro de su empresa** (`con.emp`; Ruesma
= 1, Porsan = 28). Data mart, 2026-09-29: `POSTV2` tiene ficha en las
empresas 1 y 28; `0404` y `POSTV`, solo en la 1. Hoy `obra_por_codigo`
filtra solo `con.cod` y toma `filas[0]`. Decisión del humano (2026-09-29):
se imputa a la empresa filtrada en el cuadrante, la empresa viaja en cada
línea y sin empresa la línea se rechaza con motivo.

**Empresa válida** = entero > 0. **Empresa de la petición** = la única
empresa válida que traen sus líneas (una petición es una obra, y una obra es
de una empresa).

## Contrato API → transfer

R1. El sistema debe aceptar un campo `empresa` (entero) en cada línea de
`preflight` y `ejecutar` y llevarlo al modelo de dominio de la línea.

R2. SI una línea llega sin empresa válida (ausente, nula, 0 o negativa),
ENTONCES el sistema debe omitirla con el motivo `MOTIVO_SIN_EMPRESA`, no
escribirla, y seguir procesando el resto de líneas de la petición.

R3. SI ninguna línea trae empresa válida, ENTONCES el sistema debe omitirlas
todas (R2) **sin leer ninguna obra en Sigrid** y sin escribir nada.

R4. SI las líneas con empresa válida traen más de una empresa distinta,
ENTONCES el sistema debe rechazar la petición entera con HTTP 422,
`{"ok": false, "error": …}` nombrando las empresas recibidas, sin leer ni
escribir en Sigrid.

R5. El transfer no debe tener empresa por defecto: fuera `SIGRID_EMPRESA` de
sus ajustes y del constructor del cliente de Sigrid (D4).

## Búsqueda de la obra en Sigrid

R6. El sistema debe buscar una obra por código **siempre** con código y
empresa: la consulta filtra `con.cod = ?` y `con.emp = ?`, ambos
parametrizados, y la firma de la búsqueda exige la empresa (sin valor por
defecto).

R7. CUANDO la lectura devuelve fichas de varias empresas para un código, el
sistema debe quedarse con la de la empresa pedida **sea cual sea el orden de
las filas**. Test obligatorio: `POSTV2` en empresas 1 y 28, con las filas en
los dos órdenes, pidiendo 1 y pidiendo 28.

R8. SI tras filtrar por empresa no queda ninguna ficha, ENTONCES la búsqueda
debe devolver «no encontrada»; SI queda más de una, ENTONCES debe fallar con
un error de obra ambigua que nombre código, empresa y número de fichas. Nunca
se elige «la primera».

R9. Toda búsqueda de obra, también por `ide`, debe devolver su `con.emp`.

## Obra de origen, destino normal y modo pruebas

R10. CUANDO la obra trae `ide`, el sistema debe comprobar que su empresa en
Sigrid es la de la petición, en modo normal **y** en modo pruebas.

R11. SI la empresa de la obra no coincide con la empresa de la petición,
ENTONCES el sistema debe omitir las líneas con empresa por el motivo
`MOTIVO_EMPRESA_OBRA` (nombra la obra y las dos empresas), no resolver
destinos y no escribir nada (ver D2).

R12. CUANDO la obra llega sin `ide`, el sistema debe resolverla por código y
empresa de la petición.

R13. MIENTRAS `OBRA_PRUEBAS_FORZAR=true`, el sistema debe resolver la obra de
pruebas por `OBRA_PRUEBAS_COD` **y** la empresa de la petición. SI no existe
en esa empresa, ENTONCES debe fallar con un error que nombre código y empresa,
sin escribir nada (ver D3).

R14. El sistema debe casar la partida normal contra la obra de origen **ya
resuelta** en R10/R12, sin una segunda búsqueda por código.

## Destino de postventa (P5)

R15. El sistema debe resolver la obra de postventa por `POSTVENTA_OBRA_COD`
**y** la empresa de la petición.

R16. SI la obra de postventa no existe en esa empresa, o es ambigua, ENTONCES
el sistema debe omitir las líneas de postventa con un motivo que nombre el
código y la empresa, y seguir con las líneas normales.

## Escritura

R17. CUANDO crea la cabecera de un parte, el sistema debe escribir en
`con.emp` la empresa de la obra destino resuelta.

R18. Las respuestas deben publicar `empresa` en `obra_destino` (preflight y
ejecutar) y en `obra_postventa` (preflight).

R19. El sistema debe mantener intactas las reglas P1-P5, conflicto,
capacidad y sin partida para las líneas con empresa válida: la suite
existente sigue en verde con sus fixtures adaptadas a `empresa = 1`.

## `dedicacion-api`

R20. CUANDO la API construye las peticiones de registro, debe poner en cada
línea `empresa` = el ajuste `EMPRESA_IMPUTACION` (D1).

R21. `EMPRESA_IMPUTACION` debe ser entero > 0 (1 si no se declara); SI es
≤ 0 o no numérico, ENTONCES la API no debe arrancar (error de validación).

## Documentación

R22. El sistema debe enunciar la regla en `docs/ARCHITECTURE.md` con el ancla
`#regla-empresa`, remitida (no reenunciada) desde P5, `#regla-pruebas`, el
pipeline y el README del transfer.

R23. `docs/INTEGRACION.md` (§3 variables, fecha y commit de origen) y el
README del transfer (contrato de la línea) deben reflejar el cambio, y
`azure-apps/dedicacion.md` debe refrescarse como copia en el mismo trabajo.

## Verificación MANUAL (humano)

M1. Preflight real, solo lectura, en modo pruebas, con postventa: empresa 1
en `obra_postventa` y en `obra_destino` (`0404`). Comando: `tasks.md` T10.

## Fuera de alcance

Recurso por empresa (D5); numeración `PTaa/nnnnn` (global, sin ambigüedad);
F-023 (empresa en maestros), F-024 (selector) y F-018 (salir de pruebas).

## Decisiones abiertas (las valida el humano)

- **D1 · Empresa mientras no hay F-023/F-024.** Propuesta: ajuste
  `EMPRESA_IMPUTACION` de la API (1 por defecto) en cada línea; F-024 cambia
  solo esa fuente. Efecto: una copia de obra de Porsan/UTE colada en el
  cuadrante sale **omitida con motivo** (R11), no en la ficha equivocada.
  Descartado: esperar a F-023 (alarga el bloqueo de F-018) o un `1` literal.
- **D2 · Obra de otra empresa: omitir o rechazar.** Propuesta: omitir (R11);
  la API guarda el motivo en la asignación y se ve. Un 4xx no deja traza.
- **D3 · Pruebas con empresa ≠ 1.** La `0404` solo existe en la 1: con R13
  estricta, una línea de otra empresa falla en modo pruebas sin escribir.
  Alternativa: `OBRA_PRUEBAS_EMPRESA` fija. Propuesta: estricta, revisar con
  F-024.
- **D4 · Retirar `SIGRID_EMPRESA`.** Con R17 sería una segunda verdad.
  Propuesta: fuera del código, del `.env.example`, de
  `infra/create_transfer_dedicacion.ps1` y de `docs/INTEGRACION.md` (en el
  contenedor desplegado es inocua: `extra="ignore"`).
- **D5 · El recurso tampoco mira la empresa.** `recursos_de_empleados` (por
  `res.conide`) elige el `M*` de `ide` mayor de cualquier empresa (hay `M*`
  en las 18, 25 y 31). Propuesta: feature aparte o ampliar F-023, antes de
  F-018.
