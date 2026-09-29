# Exploración · por qué no sale «Eusebio Vindel Duro» (1-MO/0772) en el cuadrante

Explorador de solo lectura, 2026-09-29. Fuentes: código del repo, `azure-apps/sigrid_tablas.md` y el data mart
`sigrid_dm` (MCP `bbdd-ruesma-azure`, `personal.recursos` construido el 2026-09-29 03:11 UTC; `raw.res` y `raw.emp`
ingeridos con éxito esa noche). No se ha llamado a sigrid-api ni leído ningún `.env`. Sin DNI en este informe.

## Causa raíz (confianza ALTA en lo inmediato, MEDIA en el porqué)

**El recurso no tiene rellenado «Empleado asociado» (`res.conide = 0`), y la SQL de sync parte de `dbo.emp` y solo
llega a un recurso por `res.conide = emp.ide`.** Un recurso sin ese campo no puede salir nunca. Es un fallo de
DATOS con consecuencia; pero la CONSULTA es más exigente que el propio Sigrid, que imputa partes a estos recursos
sin ficha de empleado (ver evidencia 4). Recomendación: arreglar las dos cosas.

## Evidencia

1. **Campos de enlace** (`sigrid_tablas.md`): `res.conide` = «Empleado asociado», índice a `emp` (l. 19911); `res.cif`
   = CIF/NIF propio del recurso (l. 19910); `emp.reside` = «Recurso relacionado», índice a `res` (l. 12157);
   `emp.dni` (l. 12149), `emp.fecbaj` (l. 12185); la lista de referencias de `emp` incluye `res.conide` (l. 12317)
   y la de `res` incluye `emp.reside` (l. 19962). Son dos enlaces independientes, uno en cada dirección.
2. **`empleado_id` del data mart sale de `res.conide`, no de `emp.reside`** (inferencia fuerte): 825 recursos con
   empleado → 822 empleados distintos, y 3 empleados con varios recursos. Con `emp.reside` (un solo recurso por
   empleado) eso no podría pasar. El diccionario no documenta la fórmula; por eso es inferencia, no cita.
3. **Eusebio no tiene NINGUNA ficha de empleado enlazada a ningún recurso**: sus 3 recursos (`1-MO/0772` PERSONA
   ENCARGADO DE OBRA activo, `1-CO0175` gasoil, `1-TF0382` móvil) tienen `empleado_id` NULL; el NIF del recurso
   está informado y **no coincide** con el NIF ni con el DNI de empleado de ningún otro recurso de ninguna empresa.
   El data mart no publica empleados sin recurso, así que si existe una ficha `emp` suya SUELTA, aquí no se ve.
4. **Sigrid imputa sin empleado**: `1-MO/0772` tiene 3 líneas de parte (3 partes, 2026-07-31 a 2026-09-30), tipo de
   hora por defecto MENC. `1-MO/0496` lleva **1.201 líneas en 177 partes desde 2020** sin empleado asociado.
5. **No es azar, es un patrón de alta**: en la empresa 1, todos los recursos persona activos con código ≤ MO/0758
   tienen empleado. De las altas recientes (`recurso_id ≥ 2.740.000`) tienen empleado 6/6 JEFE PRODUCCIÓN, 2/2
   ADMVO OBRA, 1/1 OFICINA TÉCNICA y 4/5 JEFE DE OBRA; **no lo tiene ninguno** de los 7 ENCARGADO DE OBRA (0759,
   0760, 0762, 0772, 0774, 0775, 0779), el CAPATAZ 0776 ni los 3 gruistas (0766, 0767, 0773). Comparado con un
   par que SÍ sale (p. ej. `1-MO/0770`/`0771`, JEFE PRODUCCIÓN, MAJO): misma empresa, activo, 9 tipos de hora,
   contrapartida informada, NIF informado; la única diferencia es `res.conide` informado (y su DNI de empleado
   coincide con el NIF del recurso).

## Los otros nueve

- **0759, 0760, 0762, 0774, 0775, 0779 (encargados), 0776 (capataz), 0777 (jefe de obra, MJEFO)**: mismo caso que
  Eusebio: sin empleado, sin otra ficha con su NIF, ya con partes imputados en Sigrid (1-12 líneas, abr-sep 2026).
- **0496 (encargado, MENC) es distinto**: su NIF coincide con `18-MO/0006` (empresa 18, CAPATAZ, MCAP, activo) que
  SÍ tiene empleado con DNI coincidente. Es decir, su ficha `emp` existe pero está enlazada solo al recurso de la
  UTE. Como la SQL no filtra empresa, esa persona probablemente sí entra en el cuadrante, **pero con el recurso de
  la empresa 18** (el único que tiene `res.conide`) → el transfer escribiría en el recurso de la UTE. No verificado
  contra la BBDD `dedicacion`.

## ¿El transfer tiene el mismo problema? Sí

`recursos_de_empleados` resuelve `SELECT res.ide, res.conide FROM res WHERE res.conide IN (…)`
(`services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:138-151`), y el pipeline solo lo usa si
la línea no trae `recurso_ide` (`application/pipelines/registro_pipeline.py:12,146-172`); sin recurso, la regla P1
omite la línea. La API hoy manda solo `empleado_ide = emp.ide`, nunca `recurso_ide`
(`services/dedicacion-api/application/registro_sigrid.py:61-67`). Con el dato actual, aunque Eusebio entrara en el
maestro, no se registraría.

## Cómo se arregla

- **En Sigrid (Administración), sin código**: para cada uno de los 9 de la empresa 1, abrir su ficha de EMPLEADO (si
  existe) o crearla en la empresa 1 con alta en el historial laboral (`emphis` sin fecha de baja, porque la SQL
  exige eso), y en la ficha del RECURSO `MO/07xx` rellenar **«Empleado asociado»** (`res.conide`). Rellenar solo
  «Recurso relacionado» en el empleado (`emp.reside`) **no basta**: ni la SQL ni el transfer lo leen. Para 0496,
  enlazar también el recurso de la empresa 1 al empleado que ya existe.
- **En la SQL (feature propia, con spec)**: rehacer la consulta con el RECURSO como eje (`FROM dbo.res JOIN dbo.con
  ON con.ide = res.ide WHERE con.emp = 1`, activo por `con.fecbaj` del recurso, `LEFT JOIN dbo.emp ON emp.ide =
  res.conide` solo para DNI), clave del trabajador = `recurso_ide`, y enviar `recurso_ide` al transfer (que ya lo
  acepta). Sin `emp`, no hay DNI: el dedupe usaría `res.cif`. Encaja con la propuesta 2-3 de `explore_maestros_sync.md`.
  Parche mínimo que NO sirve para Eusebio: añadir `OR emp.reside = res.ide` al JOIN (solo ayuda si existe su `emp`).

## Sin confirmar (requiere `POST /api/sql/read`, solo SELECT, sobre `ruesma_rep`)

```sql
-- Q1: ¿res.conide vacío? Confirma la causa si conide = 0 en los 10.
SELECT c.cod, c.emp, res.ide, res.conide FROM res JOIN con c ON c.ide = res.ide
WHERE c.emp = 1 AND c.cod IN ('MO/0496','MO/0759','MO/0760','MO/0762','MO/0772','MO/0774','MO/0775','MO/0776','MO/0777','MO/0779');
-- Q2: ¿hay emp enlazado por la otra vía? Filas => H3 (enlazado solo por emp.reside).
SELECT emp.ide, emp.reside, c.cod, c.emp, c.fecbaj, emp.fecbaj FROM emp JOIN con c ON c.ide = emp.ide
WHERE emp.reside IN (SELECT r.ide FROM res r JOIN con rc ON rc.ide = r.ide WHERE rc.emp = 1 AND rc.cod = 'MO/0772');
-- Q3: ¿existe un emp suelto de Eusebio? Filas => H2 (existe sin enlazar); vacío con Q2 vacío => H1 (no existe).
SELECT emp.ide, c.cod, c.emp, c.fecbaj, emp.fecbaj, emp.reside,
       CASE WHEN REPLACE(emp.dni,'-','') = REPLACE(r0.cif,'-','') THEN 1 ELSE 0 END AS dni_coincide,
       (SELECT COUNT(*) FROM emphis h WHERE h.empide = emp.ide) AS n_emphis
FROM emp JOIN con c ON c.ide = emp.ide
JOIN res r0 ON r0.ide = (SELECT r.ide FROM res r JOIN con rc ON rc.ide = r.ide WHERE rc.emp = 1 AND rc.cod = 'MO/0772')
WHERE REPLACE(emp.dni,'-','') = REPLACE(r0.cif,'-','') OR c.res LIKE '%VINDEL%DURO%';
```

Si Q3 da una ficha en otra empresa o de baja en `emphis`, el arreglo en Sigrid cambia (crear en empresa 1 / dar
alta). Queda también sin confirmar el efecto real de 0496 en el cuadrante (mirar `trabajador` en la BBDD local).
Pregunta para negocio: ¿los encargados y gruistas se dan de alta sin ficha de empleado a propósito (nómina fuera
de Sigrid, contrato por UTE…)? Si es deliberado, el arreglo tiene que ser el de la SQL, no el de datos.
