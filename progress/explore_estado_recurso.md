<!-- progress/explore_estado_recurso.md -->
# Explorador · estado de BAJA del recurso (D1 de F-023)

Solo lectura. Fuentes: MCP `bbdd-ruesma-azure` (sigrid_dm, build `personal` 2026-09-30 03:11 UTC,
diccionario v37), `azure-apps/sigrid_tablas.md` y el SQL/config del ETL en
`datamart-seg-anual` (solo leído). No se llamó a sigrid-api ni se leyó ningún `.env`.

## Respuesta

**Lo que decide la baja es `con.fecbaj` del recurso, no `con.est`.** Confianza ALTA en lo que
sigue; lo que queda sin confirmar se lista al final.

1. **Los recursos son `con.tip = 33`** (`datamart-seg-anual/config/tables_sigrid.yaml:610`, y
   `config/diccionario/raw.yaml:1412`: «extension especifica del concepto de tipo 33 en `con`»).
2. **`conest` no tiene ningún estado para el tipo 33.** El catálogo se ingiere entero
   (`tables_sigrid.yaml:1195-1199`, `where: null`) y se publica sin filtro en
   `maestro.estados_documento` (`FROM raw.conest ce`, sin WHERE): 193 filas en 29 tipos, y el 33
   no está entre ellos (4, 5, 8-15, 21, 24-27, 35, 36, 42-44, 46, 47, 49, 53, 54, 72, 306, 707, 708).
   ⇒ en Q1 y en la SQL de empleados de design §3, `LEFT JOIN dbo.conest rest ON rest.tip = rcon.tip
   AND rest.est = rcon.est` **devuelve siempre NULL**, así que `estado_recurso` será siempre el
   `CAST(rcon.est …)` numérico. No existe ningún literal de `conest.res` de recurso que poner en
   `estados_recurso_excluidos`.
3. **Trampa a evitar:** el tipo **43 sí tiene `1=ALT/ALTA | 2=BAJA/BAJA`**, pero el tipo 43 es el
   **empleado** (`emp`, `raw.yaml:1436`), no el recurso. Es el `con.est` del `con` con `ide = emp.ide`,
   no el de `rcon`. No debe confundirse con el estado del recurso.
4. **El data mart traduce «en rojo» a la fecha de baja del concepto**, y solo a ella.

## Definición de `activo` en el data mart (cita literal)

Diccionario (`personal.recursos.activo`): «El criterio de negocio de Juan Romero («los recursos en
rojo estan de baja»), traducido a la baja del CONCEPTO del recurso.» `fecha_baja`: «Es la del
concepto: el recurso no tiene fecha de baja propia en Sigrid.»

SQL (`etl_sigrid/infrastructure/postgres/sql/personal/01_recursos.sql:22-23` y `:90-91`):
«"En rojo" se traduce a `con.fecbaj > 0` —`raw.res` NO tiene columna de baja propia: la baja es la
del CONCEPTO—» · `(COALESCE(c.fecbaj, 0) = 0) AS activo`. Origen: correo «RECURSOS PARTES TRABAJO»
de Juan Romero del 2026-09-03 (cabecera del mismo fichero).

## Q1 reconstruida (parcial: sin `est`)

`raw` no está autorizado en el MCP (`OBJETO_NO_PERMITIDO`), así que `con.est` de los recursos no se
puede medir. Lo que sí: `personal.recursos`, empresa 1, por clase × activo × fecha de baja (COUNT en SQL):

| clase | activo | con fecha de baja | n | con ficha de empleado |
|---|---|---|---|---|
| PERSONA | false | sí | 1.035 | 535 |
| PERSONA | true | no | 229 | 216 |
| CONSUMO | false | sí | 584 | 0 |
| CONSUMO | true | no | 552 | 0 |
| MEDIO | false | sí | 102 | 0 |
| MEDIO | true | no | 1 | 0 |

`activo` coincide exactamente con `fecha_baja IS NULL` (no hay combinaciones cruzadas), y la fecha
de baja SÍ se informa en los recursos: 1.721 de 2.503 en la empresa 1 (en obras, en cambio,
`con.fecbaj` no se informa nunca). **535 personas con ficha de empleado están de baja como
recurso**: son las que hoy pueden colarse si solo se mira `emphis`.

## Propuesta para `config.yaml` (D1)

- `excluir_recurso_con_fecha_baja: true` — es el criterio publicado de Administración y discrimina.
- `estados_recurso_excluidos: []` — no hay literales de `conest` para el tipo 33. No inventar valores.
- Consecuencia para la spec: `filtro_estado_recurso` por literal de `conest` no aporta nada hoy.
  El spec-author/líder puede decidir simplificarlo (quitar el JOIN a `conest` del recurso) o dejarlo
  como gancho vacío. Si se mantiene, recordar que lo que llega es el número de `con.est` en texto.

## Sin confirmar

- **Distribución real de `con.est` en `con.tip = 33`**: no medible desde el data mart. Si el humano
  lanza Q1 por sigrid-api, lo esperable es un único valor (probablemente 0) o valores sin relación
  con la baja; si aparece un `est` que solo va con `con_fecha_baja = 1`, reabrir.
- Que el «rojo» de la pantalla de Sigrid sea literalmente `fecbaj > 0` es la traducción del data
  mart del correo de Juan Romero, no una comprobación sobre la interfaz. Lo confirmaría R19 (Q2 con la
  lista D5 de negocio).
- Cifras del build del 2026-09-30; `personal` puede ir atrasado respecto a `raw` (R-FRESCURA).
