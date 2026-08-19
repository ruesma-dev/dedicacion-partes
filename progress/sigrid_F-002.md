<!-- progress/sigrid_F-002.md -->
# F-002 · Lecturas contra Sigrid

Registro de las consultas de **solo lectura** lanzadas para cerrar las
decisiones abiertas de `specs/F-002-reglas-postventa-conflicto/requirements.md` §2.
Sin este volcado, la decisión no sería trazable.

---

## C2 · Árbol del presupuesto de la obra de postventa

- **Fecha:** 2026-08-19 · **Lanzada por:** el arnés, autorizada por el humano en sesión.
- **Vía:** `POST /api/sql/read` de `sigrid-api` (instancia `dev`), base **`ruesma`**.
- **Tipo:** `SELECT` puro. Ninguna escritura.
- **Parámetros:** `con.cod = 'POSTV2'`, `OFFSET 0 FETCH 2000`.
- **Resultado:** HTTP 200, **248 filas**, `truncated: false` (no hace falta paginar).

### Qué contesta

| Pregunta de la spec | Respuesta con datos |
|---|---|
| D1.1 · ¿existe la obra `POSTV2`? | **Sí**, y tiene presupuesto. Confirma la versión del README y del `.env.example`; el `'postventa-2'` del docstring de `reglas_porcentajes.py:15` es falso. |
| D1.2 · ¿partida (hoja) o capítulo? | **Partida.** Las 86 líneas de obra del presupuesto tienen `n_hijos = 0`: todas son hojas. |
| ¿`cod` = `0610` o `0610 COLEGIO ALEGRA` todo junto? | **Separados**: `cod = '0610'`, `res = 'COLEGIO ALEGRA'`. Lo que se ve en la interfaz de Sigrid es la concatenación de los dos campos. El emparejamiento por código exacto que hace `partida_resolver.resolver_postventa` es el correcto. |

### Estructura

- **248 nodos** en total: 225 hojas y 23 capítulos.
- Capítulos: `CD`, `CI.1`, `CI.03P`, `3`, `4`, `5`, `6`, `7`, `8`, `CI.03A`, `9`, `10`, `11`, `CI.2`, `CI`, `CI.3`, `CP`, `CI.4`, `CI.5`, `CI.6`, `CI.7`, `1.9`, `REP_SOLADO`.
- En la raíz (`padide = 0`) cuelgan: `CD`, `656`, `664`, `CI`, `680`, `CP`, `693`.
- Las 86 partidas de obra cuelgan de **`CD` · COSTES DIRECTOS**, salvo cuatro (ver aviso).

### Aviso · cuatro partidas duplicadas sin el cero inicial

Cuelgan de la **raíz**, no de `CD`, y duplican una partida que ya existe:

| Suelta en la raíz | Ya existe bajo CD | Descripción |
|---|---|---|
| `656` (ide 392112) | `0656` | 33+34 VIVIENDAS TOMARES |
| `664` (ide 398253) | `0664` | 76 VIVIENDAS EN LOS GUINDOS (MALAGA) - GRUPO LAR |
| `680` (ide 407098) | `0680` | APARTHOTEL ARGIS C/CAVANILLES |
| `693` (ide 410702) | `0693` | 54 VIV. "CELERE BAVIERA GOLF" EN  VELEZ-MALAGA |

No rompen nada hoy: `text_match.normalize_code` **no** quita ceros a la
izquierda, así que `0656` y `656` son códigos distintos y la obra `0656`
casa siempre con su partida bajo `CD`. Pero son ruido de presupuesto y
conviene que Administración sepa que están ahí.

### Las 84 partidas de obra

| cod | res | hijos | padre |
|---|---|---|---|
| `0342` | PARROQUIA VILLANUEVA DEL PARDILLO | 0 | CD |
| `0402` | COLEGIO VALDEBERNARDO | 0 | CD |
| `0489` | 97 VIVIENDAS VALDEBEBAS | 0 | CD |
| `0502` | 64 VIV. GUADALAJARA | 0 | CD |
| `0536` | UTE_NUEVA SEDE COLEGIO DE ENFERMERIA | 0 | CD |
| `0539` | 22 VIVIENDAS LAS CARCAVAS | 0 | CD |
| `0542` | AMPLIACION COLEGIO EL VALLE LAS TABLAS | 0 | CD |
| `0561 ` | 35 VIVIENDAS UNIFAMILIARES BOADILLA | 0 | CD |
| `0567` | 11+9 VIVIENDAS UNIFAMILIARES MY HOME | 0 | CD |
| `0574` | AMPLIACION COLEGIO LAS TABLAS | 0 | CD |
| `0578B` | 12 VIVIENDAS CANILLAS | 0 | CD |
| `0585` | RESIDENCIA ESTUDIANTES ALCOR | 0 | CD |
| `0588` | PARROQUIA STA. Mª DE LA CABEZA | 0 | CD |
| `0592` | 67 VIV. FUENTELUCHA | 0 | CD |
| `0593` | 38 VIV. EL CAÑAVERAL | 0 | CD |
| `0593B` | REPARACION SOLADOS EL CAÑAVERAL | 0 | CD |
| `0594` | VIV. CASARES | 0 | CD |
| `0595` | 20 VIVIENDAS VILLARCAYO | 0 | CD |
| `0598` | VIV. VILLALBILLA FASE-2 | 0 | CD |
| `0599` | TANATORIO MAJADAHONDA | 0 | CD |
| `0601` | RESIDENCIA ESTUDIANTES TEATINOS | 0 | CD |
| `0602` | AHORRAMAS LAS ROZAS | 0 | CD |
| `0606` | POY DU FOU (UTE) | 0 | CD |
| `0609` | 52 VIV. GUADALAJARA | 0 | CD |
| `0610` | COLEGIO ALEGRA | 0 | CD |
| `0611` | EDIF. OFICINAS Y COMERCIO AHORRAMAS BARAJAS | 0 | CD |
| `0612` | COLEGIO SAFA MADRID | 0 | CD |
| `0613` | COLEGIO RICHMOND | 0 | CD |
| `0613-B` | COLEGIO RICHMOND F-2 | 0 | CD |
| `0615` | 14 VIV. POZUELO | 0 | CD |
| `0616` | EDIF. PROCESAMIENTO DATOS LAS ROZAS | 0 | CD |
| `0617` | REMODELACION PABELLON COLEGIO EL PRADO | 0 | CD |
| `0620` | 18 VIV. GUADALAJARA | 0 | CD |
| `0625` | EDIF. INDUSTRIAL Y OFICINAS EN MECO | 0 | CD |
| `0626` | VIV. VELEZ MALAGA | 0 | CD |
| `0627` | RESIDENCIA LA CARTUJA - SEVILLA | 0 | CD |
| `0631` | RESIDENCIA ESTUDIANTES EN GETAFE | 0 | CD |
| `0633` | CENTRO ACUATICO GETAFE | 0 | CD |
| `0634` | 46 VIV. EN GUADALAJARA | 0 | CD |
| `0635` | CENTRO ESTUDIOS EN GALAPAGAR | 0 | CD |
| `0637` | 131 VIV. VEGA-II EN MALAGA | 0 | CD |
| `0638` | CENTRO DE FORMACION PROFESIONAL SAFA(VALLADOLID) | 0 | CD |
| `0639` | 10 VIV. ANZIO POZUELO (MADRID) | 0 | CD |
| `0642` | 12 VIVIENDAS CALLE PUERTO ALTO | 0 | CD |
| `0644` | COLEGIO MAYOR MONTALBAN | 0 | CD |
| `0646` | 26 VIVIENDAS JOSE BARBASTRE | 0 | CD |
| `0647` | COLEGIO EDUCREA FASE1 | 0 | CD |
| `0648` | 30 VIVIENDAS C/ LA MILAGROSA | 0 | CD |
| `0649` | PARROQUIA STA. Mª JOSEFA LA GAVIA | 0 | CD |
| `0651` | 63 TALLERES, GARAJE Y PISCINA EN S.S. DE LOS REYES | 0 | CD |
| `0652` | REFORMA COLEGIO ALDOVEA | 0 | CD |
| `0653` | ADEC. NORMATIVA UNIVERSIDAD VILLANUEVA | 0 | CD |
| `0654` | URBANIZ. Y VIVIENDAS RONDA DE LA PLAZUELA.  LAS ROZAS | 0 | CD |
| `0655` | HOTEL FLORIDA NORTE | 0 | CD |
| `0656` | VIV. TOMARES | 0 | CD |
| `0658` | AMPLIACION PABELLON SECUNDARIA COLEGIO EL PRADO | 0 | CD |
| `0659` | 28 VIVIENDAS TRES CANTOS (MADRID) | 0 | CD |
| `0660` | COMISARIA POLICIA LOCAL CABANILLAS DEL CAMPO | 0 | CD |
| `0661` | AHORRAMAS VILLANUEVA DEL PARDILLO (MADRID) | 0 | CD |
| `0662` | REFORMA EDIFICIO C/ VICENTE MUZAS (MADRID) | 0 | CD |
| `0663` | EDIF. LABORATORIOS SEK VILLANUEVA DE LA CAÑADA | 0 | CD |
| `0664` | 76 VIVIENDAS EN LOS GUINDOS (MALAGA) - GRUPO LAR | 0 | CD |
| `0666` | AHORRAMAS ALCALA DE HENARES (MADRID) | 0 | CD |
| `0667` | RESIDENCIA ESTUDIANTES ALCALA DE HENARES | 0 | CD |
| `0668` | REFORMA HOTEL WESTIN PALACE | 0 | CD |
| `0669` | 57 VIVIENDAS "CELERE BLOSSOM II" EN BENALMADENA | 0 | CD |
| `0672` | 79 VIVIENDAS CULMIA EN CARABANCHEL (MADRID) | 0 | CD |
| `0674` | TERMINACION OBRA ROGASA SS DE LOS REYES | 0 | CD |
| `0677` | 15 VIV. UNIFAMILIARES MIRASIERRA (MADRID) | 0 | CD |
| `0679` | AMPLIACION PABELLON INFANTIL COLEGIO MONTEALTO | 0 | CD |
| `0680` | APARTAHOTEL ARGIS C/ CAVANILLES.  MADRID | 0 | CD |
| `0681` | 52 VIVIENDAS CULMIA EN VILLAVERDE (MADRID) | 0 | CD |
| `0682` | COLEGIO EDUCREA VILLALBILLA FASE-2 | 0 | CD |
| `0685` | TERMINACION VIV. CHIPIONA | 0 | CD |
| `0687` | CENTRO ACOGIDA MENORES "LA CANTUEÑA", FUENLABRADA | 0 | CD |
| `0688` | REMODELACION PATIO EN COLEGIO CEU MONTEPRINCIPE | 0 | CD |
| `0689` | COLEGIO INTERNACIONAL TORREQUEBRADA, BENALMADENA | 0 | CD |
| `0690` | REF. INSTITUTO FORMACION CAMARA COMERCIO (MADRID) | 0 | CD |
| `0691` | HOTEL 131 APARTAMENTOS PP4 - FASE 2, LEGANES | 0 | CD |
| `0693` | 54 VIV. "CELERE BAVIERA GOLF" EN  VELEZ-MALAGA | 0 | CD |
| `0698` | AMPL. PABELLON ESSO COLEGIO MONTEALTO | 0 | CD |
| `0705` | REF. EDIF. CAMPUS CREATIVIDAD CEU, C/ TUTOR. MADRID | 0 | CD |
| `656` | 33+34 VIVIENDAS TOMARES | 0 | raíz |
| `664` | 76 VIVIENDAS EN LOS GUINDOS (MALAGA) - GRUPO LAR | 0 | raíz |
| `680` | APARTHOTEL ARGIS C/CAVANILLES | 0 | raíz |
| `693` | 54 VIV. "CELERE BAVIERA GOLF" EN  VELEZ-MALAGA | 0 | raíz |

### SQL ejecutado

```sql
SELECT p.ide, ISNULL(p.padide,0) AS padide, p.pos, p.cod, p.res,
       ISNULL(p.tipdes,0) AS tipdes,
       (SELECT COUNT(*) FROM obrparpar h WHERE h.padide = p.ide) AS n_hijos
  FROM obrparpar p JOIN obr ON obr.ide = p.obride
  JOIN con ON con.ide = obr.ide
 WHERE con.cod = ?          -- 'POSTV2'
 ORDER BY p.pos, p.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
```

---

## C6 · ¿Ha escrito este sistema alguna vez en Sigrid?

- **Fecha:** 2026-08-19 · **Motivo:** cerrar la ventana ciega del 25/07/2026
  que detectó `progress/explore_transfer_original.md` §5 (el log del original
  solo empieza el 26/07 a las 12:09).
- **Vía:** `POST /api/sql/read`, base **`ruesma`**. `SELECT` puro.
- **Busca:** cualquier fila de `hmores` con `synckey LIKE 'porcentajes:%'` o
  con la marca de pruebas en `tex` (`%PRUEBA-PORC%`).
- **Resultado: 0 filas.** `truncated: false`.

**Conclusión: este sistema nunca ha escrito en Sigrid.** No hay restos de
pruebas que limpiar, y la afirmación queda demostrada, no supuesta. La
verificación T14 (escritura real en la obra de pruebas `0404`) sigue **entera
por hacer** y exige autorización expresa del humano para esa acción concreta.

### SQL ejecutado

```sql
SELECT TOP 500 h.ide, h.hmoide, hmo.ano, hmo.mes, con.cod AS obra_cod,
       h.reside, h.fec, a.cod AS hora_cod, h.can, h.pre, h.tot,
       ISNULL(h.paride,0) AS paride, CAST(h.tex AS NVARCHAR(200)) AS tex,
       h.synckey
  FROM hmores h
  JOIN hmo ON hmo.ide = h.hmoide
  JOIN obr ON obr.ide = hmo.obride
  JOIN con ON con.ide = obr.ide
  LEFT JOIN auxhor a ON a.ide = h.horide
 WHERE h.synckey LIKE ?              -- 'porcentajes:%'
    OR CAST(h.tex AS NVARCHAR(200)) LIKE ?   -- '%PRUEBA-PORC%'
 ORDER BY h.ide DESC
```
