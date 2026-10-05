<!-- progress/explore_nombres_empresas.md -->
# Exploración: nombres de empresa (auxemp.res) — solo lectura

Fuente: MCP `bbdd-ruesma-azure` (data mart `sigrid_dm`). El esquema `raw` (donde
vive `raw.auxemp`) NO está autorizado, pero tres vistas publican el nombre
`raw.auxemp.res` por `numemp = con.emp`: `contabilidad.plan_cuentas.empresa_nombre`,
`maestro.obras.nombre_empresa` y `personal.recursos.nombre_empresa`. Builds OK del
2026-10-01 (07:08-07:29 UTC). Las tres coinciden letra a letra en todas las empresas
en las que aparecen, y cada empresa tiene un único nombre (sin ambigüedad).

| numemp | nombre (auxemp.res)               | fichas obra | personas activas (recursos) |
|-------:|-----------------------------------|-----:|-----:|
| 1  | CONSTRUCCIONES RUESMA                 | 782 | 229 |
| 8  | URBAQUER UTE                          | 1 | – |
| 9  | UNGRIA LOGISTICA UTE                  | 1 | – |
| 11 | CONCORDIA SISTEMAS SL                 | 6 | – |
| 12 | CP PRIMO DE RIVERA UTE                | 2 | 9 |
| 14 | R.C.S. VILLAVICIOSA ODON UTE          | 2 | 3 |
| 15 | RUESMA-AVINTIA RIVAS UTE              | 2 | – |
| 18 | **RUESMA SERVICIOS SL**               | 8 | 12 |
| 20 | CALANESO S.L.                         | 3 | – |
| 22 | CONSULTORIA VINH LONG                 | 1 | – |
| 25 | UTE COLEGIO SESEÑA                    | 2 | 3 |
| 26 | UTE HOSPITAL HSFA                     | 1 | – |
| 27 | UTE VILLAS MASCARO RUESMA             | 1 | 20 |
| 28 | PORSAN E HIJOS CONSTRUCCIONES SL      | 103 | 39 |
| 29 | IBERHABITAT GESTION SL                | 1 | – |
| 31 | **UTE RUESMA-INESCO TOLEDO**          | 1 | 5 |
| 32 | PUERTO NUMANCIA SL                    | 2 | – |
| 34 | UTE PA5 PARLA                         | 1 | – |
| 39 | RUESMA EKONS SYSTEM MADRID SL         | 2 | – |

("fichas obra" = filas de `maestro.obras`, sin filtrar estado; "personas activas" =
`personal.recursos` con `clase='PERSONA' AND activo`; "–" = la empresa no tiene recursos.)

Confirmado: 1 = CONSTRUCCIONES RUESMA (sin "S.A." en auxemp; la razón social completa
"CONSTRUCCIONES RUESMA, S.A." solo aparece como proveedor) y 28 = PORSAN E HIJOS
CONSTRUCCIONES SL. 18 no es UTE: es la sociedad RUESMA SERVICIOS SL. 31 es UTE.

Confianza: alta para los nombres (3 vistas independientes, mismo literal, dato de hoy).

No resuelto: `auxemp.fecbaj` / `auxemp.desact` (baja o desactivación de la empresa).
Ninguna vista autorizada los publica y `raw` está vetado; habría que leerlo vía
`sigrid-api` (no consultado por instrucción) o pedir al dueño del data mart que lo exponga.
