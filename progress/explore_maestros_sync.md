# Exploración · maestros sincronizados de Sigrid (obras y recursos)

Explorador de solo lectura, 2026-09-29. Fuentes: código del repo, `azure-apps/sigrid_tablas.md`,
`azure-apps/sigrid_api.md` §4.1 y el data mart `sigrid_dm` (MCP `bbdd-ruesma-azure`, build nocturno
del 2026-09-29; consultas solo SELECT). No se ha llamado a sigrid-api ni leído ningún `.env`.
Por datos personales, aquí solo se citan códigos de recurso, no nombres (salvo el que dio negocio).

## Hechos de partida (lo que hace hoy el código)

- SQL de empleados: `FROM dbo.emp JOIN dbo.con ON con.ide = emp.ide` + `LEFT JOIN dbo.res ON res.conide = emp.ide`,
  activo = último `emphis` sin `fecbaj` (`services/dedicacion-api/config/config.yaml:29-55`). **Sin filtro de empresa.**
- SQL de obras: `dbo.obr JOIN dbo.con` + `conest`, **sin filtro de empresa ni de baja** (`config.yaml:104-112`);
  después se excluyen por texto de estado `terminada/cerrada/liquidada/anulada` (`config.yaml:117-126`,
  `application/filtros_maestros.py:147-162`).
- En el front, la versión «Postv-XXXX» de una obra solo se ofrece si la obra XXXX está activa en el maestro
  (`services/dedicacion-front/static/js/app.js:175-191`: `state.obras.filter(o => o.activa)` y se duplica normal/postventa).
- Topes: la API pide `max_rows=5000` (`config/settings.py:64`); la instancia admite 500.000 (`azure-apps/sigrid_api.md:326`)
  y si llega `truncated` el cliente **lanza error**, no pierde filas en silencio (`infrastructure/sigrid/sigrid_client.py:59-64`).
  El tope de filas queda descartado como causa.
- Empresa en Sigrid: `con.emp` (Entero, «Empresa») en todo concepto (`sigrid_tablas.md:5646`); catálogo `auxemp`
  (`sigrid_tablas.md:1751-1766`, con `numemp`, `fecbaj`, `desact`). El data mart une `auxemp.numemp = con.emp`.
  **Construcciones Ruesma = empresa 1**, Porsan = 28, el resto UTE (regla `R-CODIGO-POR-EMPRESA` del data mart).
  `emp.numemp` y `emphis.numemp` están marcados OBSOLETO (`sigrid_tablas.md` bloque emp/emphis): no sirven.

## A. Faltan obras de postventa — causa: el filtro de estado (confianza ALTA)

Hipótesis confirmada: las obras en postventa son obras **CERRADAS** en Sigrid, y el filtro `estados_excluidos`
las quita del maestro; sin la obra activa, el front no ofrece su «Postv-».

Evidencia (data mart): partidas activas con código de obra (3-4 dígitos) del presupuesto de las obras de
postventa de Ruesma, cruzadas con el estado de la obra de la empresa 1:

| Obra de postventa | Estado de la obra original | Nº obras |
|---|---|---|
| POSTV2 (la de P5, 86 partidas según `docs/ARCHITECTURE.md:166-199`) | CERRADA | **69** |
| POSTV2 | EN CURSO / RECIBIDA DEF. / RECIBIDA PROV. | 6 / 2 / 1 |
| POSTV (antigua) | CERRADA | 15 |

Es decir, **69 de las 78** obras que admiten postventa en POSTV2 no llegan al cuadrante (p. ej. 0656, 0660,
0669, 0689). Las obras POSTV/POSTV2 como tales sí entran (EN CURSO). Descartadas: otro `con.tip` o que no
estén en `dbo.obr` (las 78 están en `maestro.obras`, que sale de `obr JOIN con`).

## B. Salen recursos inactivos — dos causas (confianza ALTA en la 1, MEDIA en la 2)

1. **Falta el filtro por empresa** (ALTA). La consulta trae fichas de todas las empresas. Con código M*:
   empresa 18 (8 fichas), 31 (4) y 25 (1) además de la 1. En obras es peor: hoy entran **~140 fichas de obra
   de otras empresas** (97 son copias de Porsan en EN CURSO), 81 de ellas con código repetido con Ruesma
   → la misma obra aparece dos veces. El dedupe por DNI (`filtros_maestros.py:66-79`) además elige la ficha de
   `ide` más alto, que puede ser la de otra empresa.
2. **«Activo» se decide en el sitio equivocado** (MEDIA). Hoy: último `emphis` sin `fecbaj` (`config.yaml:39-54`).
   Huecos: (a) un `emp` sin ninguna fila en `emphis` cuenta como activo (`COALESCE(NULL,0)=0`); (b) se ignoran
   `emp.fecbaj` y, sobre todo, la **baja del concepto del recurso** (`con.fecbaj` del `res`), que es el criterio de
   negocio de Administración («los recursos en rojo están de baja», así lo publica el data mart en
   `personal.recursos.activo`). Magnitud: en la empresa 1 hay **276 recursos persona con código M* dados de baja**
   (272 con empleado); cuántos se cuelan depende de su `emphis`, que el data mart no ingiere → no verificable sin
   sigrid-api. Otros campos de inactividad vistos: `con.est`, `con.fecbaj`, `emp.fecbaj`, `emphis.fecbaj/motbajide`,
   `emp.estocu` («Estado de ocupación»), `auxemp.desact`.
   Nota menor: el repositorio mantiene visible a un trabajador desactivado si tiene líneas en el periodo
   (`infrastructure/db/repositories.py:90-99`); es deliberado, pero también «saca inactivos».

## C. Falta «Eusebio Vindel Duro» — causa: no tiene ficha de empleado (confianza ALTA)

Data mart: recurso `1-MO/0772`, PERSONA, ENCARGADO DE OBRA, **activo**, empresa 1, tipo de hora por defecto
**MENC** (M*), pero **`empleado_id` NULL** (ninguna ficha `emp` enlazada). La SQL arranca en `dbo.emp` y llega al
recurso por `res.conide = emp.ide`; un recurso sin empleado **no aparece nunca**. Mismo caso, activos y con M*:
empresa 1 `MO/0496, 0759, 0760, 0762, 0772, 0774, 0775, 0776, 0777, 0779` (casi todos altas recientes) y 5 de
otras empresas. Duda abierta: el data mart no dice si su `empleado_id` sale de `res.conide` o de `emp.reside`
(`emp` también tiene `reside`, «Recurso relacionado»); si Administración enlazó por `emp.reside`, la SQL tampoco lo ve.

Puntos del pipeline donde se descarta a una persona, en orden:
1. SQL: no tiene `emp` enlazado por `res.conide` (**caso Eusebio**) · último `emphis` con `fecbaj` (`config.yaml:54`).
2. Dedupe por empleado: se queda un recurso por `emp.ide` (M* > categoría > `res.ide` mayor) (`filtros_maestros.py:53-64`).
3. Dedupe por persona: DNI normalizado o, sin DNI, **nombre** → dos personas homónimas sin DNI se funden (`:66-106`).
4. Sin código M* en el recurso elegido (`:85-88`) · categoría si `filtro_categorias` (desactivado, `config.yaml:68`).
5. Upsert: nunca descarta; desactiva lo que no llega (`repositories.py:78-82`). Tope de filas: descartado (ver arriba).

Consecuencia aguas abajo: la API manda al transfer `empleado_ide = emp.ide` (`application/registro_sigrid.py:64`)
y el transfer resuelve el recurso por `res.conide` (`dedicacion-transfer/.../sigrid_write_client.py:141-148`). Aunque
entrara en el maestro, **hoy no se podría registrar** a un recurso sin empleado.

## D. Hallazgo colateral (transfer, fuera de alcance pero del mismo origen)

`obra_por_codigo` busca `WHERE con.cod = ?` sin empresa ni `ORDER BY` y toma `filas[0]`
(`dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:105-126`). **POSTV2 tiene dos fichas (empresa 1 y
28)**: el destino de postventa puede caer en la de Porsan según el orden que devuelva SQL Server. Lo mismo para
cualquier obra con copia en otra empresa (`registro_pipeline.py:96,117,228`). Convendría filtrar `con.emp = 1`.

## Propuesta de cambio (una por fallo; ninguna implementada)

1. **Obras / postventa.** (a) Añadir `WHERE con.emp = :empresa` con `empresa: 1` en `config.yaml` (literal, no
   parámetro de usuario). (b) Separar los dos universos: obras «normales» = filtro de estado actual; obras
   «postventa» = las que tengan partida hoja activa en el presupuesto de `POSTVENTA_OBRA_COD`, **cualquiera que
   sea su estado** (mismo universo que `partidas_postventa` de P5: el front y el transfer no pueden divergir).
   Sincronizarlas con una marca (`admite_normal`, `admite_postventa`) y que el front ofrezca solo lo que toque.
   Riesgo de límite de servicio: `POSTVENTA_OBRA_COD` vive hoy solo en el `.env` del transfer → decidir si la API
   lo lee también o si pide el universo al transfer. Alternativa mínima: quitar «cerrada» de la lista (entrarían
   ~467 obras cerradas, también en modo normal).
2. **Recursos inactivos.** Rehacer la SQL con el **recurso** como eje: `FROM dbo.res JOIN dbo.con cr ON cr.ide = res.ide`
   con `cr.emp = 1` y `COALESCE(cr.fecbaj,0) = 0` (baja del recurso), `LEFT JOIN dbo.emp` para DNI; mantener el
   `emphis` solo si negocio lo quiere además. Dedupe por DNI dentro de la empresa 1.
3. **Eusebio (y los otros 9).** Dos vías: (i) de datos, sin código: Administración enlaza su ficha de empleado en
   Sigrid (`res.conide`); (ii) de modelo: clave del trabajador = `recurso_ide` (no `emp.ide`) y enviar el recurso al
   transfer, que ya admite recibirlo «si viene dado» (`registro_pipeline.py:12`). La (ii) cambia contrato API↔transfer
   y la clave de `trabajador` → feature propia con spec.

## Preguntas para negocio

1. ¿«Postventa» significa «obra con partida en POSTV2»? ¿Y POSTV (la antigua, 15 obras) sigue viva?
2. ¿Una obra CERRADA debe ofrecerse solo como «Postv-» o también en modo normal?
3. ¿Solo empresa 1 o también UTE/Porsan en algún caso (p. ej. personas de Ruesma que imputan a la ficha de la UTE)?
4. ¿«Inactivo» = recurso en rojo (baja del concepto del recurso), baja laboral en `emphis`, o ambas?
5. ¿Por qué las altas recientes de encargados (MO/0759-0779) no tienen ficha de empleado? ¿Se va a crear, o se
   enlazan por otra vía (`emp.reside`)?
