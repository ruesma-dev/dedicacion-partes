# F-062 · Diseño técnico

Requisitos: `requirements.md` (R1-R30, casos C1-C12 en `tasks.md`; D5-D16
decididas el 2026-10-24: A salvo D14 = B). La base es el diseño de F-030
(`specs/F-030-dias-bajas-incidencias/design.md`) salvo lo dicho aquí.
## 1. Servicios que toca y por qué (límite de servicio)
| Servicio | Qué hace en F-062 | Por qué ahí |
|---|---|---|
| `dedicacion-transfer` | Lee las rachas del recurso en todos los partes (ventana), decide abrir, continuar o cerrar, escribe y mueve `CI*`/`CIZ` | Es la única pluma contra Sigrid, y la decisión depende de lo que hay en Sigrid |
| `dedicacion-api` | Manda el contexto del mes (`incidencias_mes`, `cierres_recursos`, `quitadas`) y guarda la traza (`sigrid_dia_fin_antes`) | Es la dueña del cuadrante: solo ella ve las incidencias de todas las obras del recurso |
| `dedicacion-front` | Pinta en el modal lo que responde el preflight (R25) | Captura y pintura; no decide nada |

Ni servicio nuevo ni nada de `partes`. «Pegado», «fin de mes» (D2, D7) y el
emparejamiento (D5) viven **solo** en el transfer: la api no calcula pegadas
(D11 = A; el 422 de B las duplicaría). No se copia `partes-transfer`: sv4
decide el papel con los días del parte diario (`azure-apps/partes.md` §3,
paso 3); aquí, con las líneas de Sigrid. `estado_parte.py` y
`cuenta_analitica.py` (copias de `partes`) se **llaman**, no se editan.
## 2. El modelo, puro: `application/services/rachas.py` (nuevo)
Sin I/O ni `settings`, como `reglas_incidencias.py`; fechas `int` AAAAMMDD.
- `pegado(c: int, d: int) -> bool` — D2: `c < d` y todos los días de
  `(c, d)` son sábado o domingo. `llega_a_fin(h: int) -> bool` — D7.
- `Racha(codigo, inicio, cierre | None)` (líneas `LineaIncidenciaSigrid`);
  `emparejar(lineas) -> list[Racha]` — D5: orden (`fec`, inicio antes que
  `CIZ`, `ide`) y una pila; un `CIZ` sin abierto no forma racha.
- `Cadena(recurso, codigo, duena, miembros, desde, hasta)`;
  `cadenas(incidencias_mes) -> list[Cadena]`: por (recurso, código, `desde`),
  une la siguiente si está pegada y no tiene traza `hmores_ide_*` (R11, D11).
- `propias(cadena, lineas) -> dict[rol, línea]`: la de la `synckey` de la
  dueña o la del `ide` de su traza (con `dia_fin_antes`, ajena movida).
- `previa(rachas, cadena) -> (Racha | None, avisos)`: R1 a-c y R10.
- `decidir_cadena(cadena, lineas, base, *, est, empresa, obride_pruebas) ->
  PlanCadena(acciones, resumenes)`: R1-R11, R14, R16, R18, R21. `base` es lo
  de `decidir_incidencia` (R26 igual; si omite, se omite la cadena). Dueña:
  `ini` (`escribir`|`editar`|`ya_registrado`|`continua`|`omitir`), `fin`
  (`escribir`|`editar`|`ya_registrado`|`abierta`|`omitir`) y `devolver`; el
  resto, `continua` «cadena de la incidencia N». `RachaResumen(id, papel,
  inicio_fec, inicio_parte, cierre, cierre_fec, cierre_parte, duena_id,
  avisos)` por incidencia (R22).
- `cierres_mes_anterior(rachas, recurso, incidencias_mes, partes_m1, ano,
  mes, *, est, empresa, obride_pruebas) -> list[CierreRacha]` (R12-R13; D14
  = B: `partes_m1` son los partes de M−1 de la obra de cada inicio anterior a
  M−1; se elige el En registro de la empresa de mayor `ide`): `recurso_ide`,
  `codigo`, `inicio_ide`/`_fec`/`_parte`, `accion` (`escribir`|
  `ya_registrado`|`aviso`), `fecha_int`, `parte_cod`, `hmoide`, `obride`,
  `cenide`, `paride`, `caaide`, `synckey`, `incidencia_id` o nulo, `motivo`.
- `no_coincide(lineas, recurso, quitadas, incidencias_mes, previas, ano, mes)
  -> list[NoCoincide]` (R17, R30): `tipo` `quitada` (sus propias aún en
  Sigrid, menos el `CIZ` ajeno que se devuelve) o `solo_sigrid` (las de M sin
  incidencia, quitada ni previa que las explique, por racha; solo designados),
  `recurso_ide`, `incidencia_id` o nulo, `lineas` (`ide`, código, `fec`,
  parte), `motivo`; y por quitada, `en_sigrid` (sus `ide` que siguen).
Pasos de `decidir_cadena`, en orden:
1. Quita de `lineas` las propias de la cadena y devuelve a su día
   (`dia_fin_antes`) el `CIZ` ajeno movido; empareja (D5).
2. Guarda R9: una línea ajena en `[desde, hasta]` que no es de la previa ⇒
   `omitir` todo.
3. La dueña con inicio propio ⇒ abre (R11) y su inicio se edita a `desde`
   como F-030 R41-R43. Si no, `previa` ⇒ `continua` o abre (R2-R3).
4. Cierre: `llega_a_fin(hasta)` ⇒ `abierta`, salvo que ya haya un `CIZ` de
   la racha en M (propio o de la previa): ese va al último día (R11). Si no
   llega: con `CIZ` de la racha en M+1 ⇒ aviso R21 sin escribir; `fin`
   propio ⇒ editar o `ya_registrado`; previa (c) ⇒ mover su `CIZ` (si es
   ajeno, solo hacia delante; en `hasta` o después, «cubierta», R4); si no,
   `escribir` (destino R5). Ajeno movido que ya no se usa ⇒ `devolver` (R16).
5. Cada `editar` o `devolver` lleva `fec_antes`, `synckey_leida`,
   `can_leido` y `ajena` (guarda y relectura, R14). Una quitada solo puede
   dar `devolver` (D16 = A: nada más se edita solo).
`reglas_incidencias.py` conserva `decidir_incidencia`, `synckey_incidencia`
y los motivos; `reconciliar` desaparece (R1, R9); `sigue_editable` compara
con `synckey_leida` y `can_leido` de la acción (no con nuestra `synckey` y
0); `no_editar_el_par` va **por cadena** (id de la dueña); nueva constante
`PREFIJO_CIERRE = "porcentajes:inc:cierre:"`.
## 3. Ficheros a crear
- transfer: `application/services/rachas.py` (§2).
- Tests sin red ni BBDD: transfer `tests/test_f062_rachas.py` (puras, C1-C11),
  `tests/test_f062_pipeline_rachas.py` (preflight y `ejecutar` con el cliente
  falso: sentencias, ningún `DELETE`), `tests/test_f062_cliente_ventana.py`
  (SQL y trozos) y `tests/test_f062_lote.py` (una lectura, ronda C); api
  `tests/test_f062_payload_rachas.py` (claves, designación, `quitadas`,
  traza); front `tests/test_f062_modal_rachas.py` (estático + node, como F-030);
  contrato `tests/contratos/f062_rachas.json` y sus dos mitades
  `test_f062_punta_a_punta.py` (api y transfer, como F-030 §13.6).
## 4. Ficheros a modificar
- **transfer** `domain/models/registro_models.py`: `IncidenciaEntrada` +
  `obra_ide`, `dia_fin_antes`; `AccionIncidencia` + `synckey_leida`,
  `can_leido`, `ajena`, `hmoide_destino`, `obride`, `cenide`;
  `LineaIncidenciaSigrid` + `obride`, `cenide`, `paride`, `caaide`,
  `parte_emp`; `Preflight` + `rachas`, `cierres_racha`.
- `config/settings.py`: `incidencias_meses_atras: int = Field(12,
  alias="INCIDENCIAS_MESES_ATRAS")`, que tiene que ser ≥ 1.
- `infrastructure/sigrid/sigrid_write_client.py`: `incidencias_del_mes` →
  `incidencias_en_ventana(resides, desde, hasta, *, obride_pruebas=None,
  ides=())` (§6); `stmt_editar_fecha_incidencia(…, can_leido=0.0)` (la
  firma de hoy y el SQL no cambian si no se pasa).
- `application/pipelines/registro_pipeline.py`: `_reconciliar_incidencias` →
  `_decidir_rachas` (§7); `ejecutar`, `_planear_ediciones`, `_comprobar_escrito`.
- `application/services/lecturas_lote.py`: `_por_leer_incidencias` y la
  memoria de `incidencias_en_ventana` (§8). `application/pipelines/
  registro_lote.py`: pasa `incidencias_mes`, `cierres_recursos` y `quitadas`.
- `interface_adapters/api/app.py`: `IncidenciaIn` + `obra_ide`,
  `dia_fin_antes`; `PeticionIn`/`LoteIn` + `incidencias_mes`,
  `cierres_recursos`, `quitadas` (por defecto `[]`); respuesta + `rachas`,
  `cierres_racha`, `no_coincide` y `fec_antes`/`ajena` en cada línea.
- `prueba_escritura_porcentajes.py`: `--incidencia` admite varias, `--cierres
  RECURSO` y muestra `rachas` y `cierres_racha` (T20).
- **api** `infrastructure/db/orm_models.py`: `IncidenciaORM.sigrid_dia_fin_antes`
  (`SmallInteger`, nulo; por `alters_faltantes`). `domain/models.py`: el
  campo. `application/traza_incidencias.py`: `campos_de_traza` + el campo;
  `trazar_incidencias` con `continua`/`abierta` (`registrado` sin `ide`),
  `devolver`, `cierres_racha` y `en_sigrid` (R15, R17, R23).
  `application/registro_sigrid.py`: `_sumar_incidencias` arma `incidencias_mes`
  y `quitadas`; `_designar_cierres(payloads)` tras el filtro `obra_ide` (R24).
- **front** `static/js/app.js`: `pintarModalPreflight` + `pintarRachas`,
  `pintarCierresRacha` y `pintarNoCoincide`, que sustituye a la lista de
  quitadas de F-030 R38 (R25). Nada en la captura.
- **docs**: `docs/ARCHITECTURE.md` (`#regla-incidencia` y la línea del
  transfer «decidir el par» → «decidir la racha»), `docs/INTEGRACION.md` §5 y
  su fila de `sigrid-api`, `test_f002_fuente_unica.py` si cambia el texto
  vigilado.
## 5. Ficheros que NO se tocan
`reglas_porcentajes.py`, `domain/estados.py`, `estado_parte.py`,
`cuenta_analitica.py`, `propuesta_partida.py`, `partida_*`, `universo_*`, la
captura del front (`chipEditable`, `chipIncidencia`,
`montarDesplegableIncidencias`), el catálogo y el sync (F-030 R3-R7, F-061),
`domain/incidencias.py` (`validar_incidencias`: D11 = A, sin 422 nuevo), el
esquema de `asignacion`, `stmt_editar_linea`, `stmt_poner_a_cero`,
`_guarda` (su texto no cambia), `stmt_borrar_linea` (sigue solo para
`limpiar`), el repositorio de `partes` y `azure-apps/partes.md`.
## 6. Contrato api → transfer y SQL
Petición (preflight, lote por obra y `ejecutar`), además de lo de F-030:
`incidencias_mes: [{id, obra_ide, recurso_ide, empresa, codigo, ano, mes,
desde, hasta, hmores_ide_ini, hmores_ide_fin, dia_ini, dia_fin,
dia_fin_antes}]`, `cierres_recursos: [recurso_ide]` y `quitadas` (mismo
elemento que `incidencias_mes`, de las quitadas con traza). `incidencias`
(las de la obra) es un subconjunto de `incidencias_mes`. Respuesta: `rachas:
[RachaResumen]`, `cierres_racha: [CierreRacha sin los campos de escritura]`,
`no_coincide: [NoCoincide]` e `incidencias` con `rol` `devolver`, las
acciones `continua`/`abierta`, `fec_antes` y `ajena`. Sin las claves nuevas,
el transfer responde como F-030 (despliegue: transfer → api → front).
Lectura (Sigrid, base `ruesma`, solo `SELECT`), en trozos de
`LOTE_PARAMETROS`:
```sql
SELECT h.ide, h.reside, h.fec, a.cod, h.synckey, c.cod AS parte, h.can,
       h.hmoide, c.est, c.emp, m.obride, h.cenide, h.paride, h.caaide
FROM hmores h JOIN auxhor a ON a.ide = h.horide
JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide
WHERE (h.reside IN (…) AND h.fec BETWEEN ? AND ? AND a.cod LIKE ?
       OR h.ide IN (…)) [AND m.obride = ?]        -- en pruebas
ORDER BY h.fec, h.ide
```
`desde` es el día 1 de M − `incidencias_meses_atras` y `hasta` el último de
M+1. Escrituras: el `INSERT` de siempre (`stmt_insert_linea`, con un
`ObraEntrada` de `ide` = `obride` y su `cenide` cuando va al parte del
inicio, R5) y el `UPDATE` de F-030 §13.5 con el `can` leído (R14). Sin DDL
en Sigrid; en PostgreSQL, una columna por `alters_faltantes`.
## 7. Pipeline: dónde encaja
En el preflight, tras el paso 4 bis (cuentas) y antes del paso 5, como
F-030: `_decidir_rachas` hace **una** lectura (R19) con los recursos de
`incidencias` y `cierres_recursos` y los `ide` de las trazas de
`incidencias_mes` y `quitadas`. Después: `cadenas(incidencias_mes)` → por
cada cadena con alguna incidencia de esta petición, `decidir_cadena` (si la
dueña es de otra obra, solo los `continua` de las suyas) →
`cierres_mes_anterior` (antes, si algún cierre es D14, **una** lectura
`partes_de_periodos` de F-055 con esas obras y M−1) y `no_coincide` (R17,
R30). Las acciones `escribir` sin
`hmoide_destino` piden parte en el paso 5 como hoy. Las que lo tienen
(R5, R12) no lo piden, y su cuenta y su partida son las del inicio. En
`ejecutar`, en este orden: los `UPDATE` de `editar`/`devolver` (releídos en
la lectura de `_planear_ediciones`; si uno no cumple, `no_editar_el_par`
por cadena), los `INSERT` de la petición y los de cierre (`max_pos` de su
`hmoide`). `_comprobar_escrito` relee por `synckey`, también la de cierre.
`ejecutar` va por obra y en serie: la cadena entre obras la escribe la
petición de su dueña; las demás solo dicen `continua`.
## 8. Lote (F-055) y coste
`_por_leer_incidencias` agrupa por (año, mes, `obride` de pruebas o `None`)
los recursos de las incidencias y de `cierres_recursos` y los `ide` de las
trazas: **ronda C**, en paralelo con `_cargar_lineas`, una llamada por lote
(≤ 500 recursos; E-1: ~1.100 filas en 13 meses, lejos de `MAX_ALLOWED_ROWS`).
Memoria: misma ventana y recursos e `ide` dentro; si no, cliente y fallo
apuntado (F-055 R22). Es **una lectura más por lote** (R20, T19); los partes
de M−1 de D14, una ronda D solo si hace falta (caso raro, E-11 y E-14).
## 9. Api: designación, `quitadas` y traza
- `_designar_cierres`: en el orden de los payloads (código de obra), cada
  recurso (de líneas o incidencias) va a `cierres_recursos` del primero donde
  sale; tras el filtro `obra_ide` (el repreflight de una obra también avisa).
- `incidencias_mes`: las del periodo de sus recursos (no quitadas, visibles,
  vigentes) con `obra_ide` y traza. `quitadas`: las quitadas con algún `ide`,
  en el payload de su obra (si no existe, se crea).
- Traza: `editar` de un `fin` `ajena` guarda `sigrid_dia_fin_antes =
  fec_antes % 100` si estaba nulo; `devolver` hecho anula `sigrid_ide_fin`,
  `sigrid_dia_fin` y `sigrid_dia_fin_antes` y borra la incidencia si está
  `quitada` y sin `ide`, igual que una quitada con `en_sigrid` vacío (R17);
  `continua`/`abierta` cuentan como hechas sin `ide`;
  un `cierres_racha` con `incidencia_id` escribe el `fin` de esa (por `id`).
## 10. Front
`pintarModalPreflight` añade, por obra, una línea por elemento de `rachas`
(«abre» · «continúa la racha del dd/mm (parte X)» · «cierra el dd/mm en el
parte Y» · «queda abierta» · «cadena de …» y sus avisos) y la sección
«Cierres de rachas» (`cierres_racha`) y el bloque «No coincide con Sigrid»
(`no_coincide`: por elemento, trabajador, motivo y sus líneas con código, día
y parte, para editarlas a mano). Sin botones ni confirmaciones (F-030 R28).
## 11. Documentación y otros repositorios
- `#regla-incidencia` se reescribe: «Qué se escribe» → «La racha» (R1-R11),
  «Sin duplicar» → «La previa y la guarda» (R1, R9), «Cambiar los días» y
  «Quitar» (aviso contra Sigrid) con R14-R18 y R30, «Una lectura» (R19) y
  «Cierre del mes anterior» (R12-R13); pie «Decidido por Pablo Gris el
  2026-10-23 (D1-D4) y el 2026-10-24 (D5-D16) · F-062». P2 no cambia.
- `INTEGRACION.md` §5: los campos de §6 y la fila de `sigrid-api` (lectura
  en ventana; se mueven `CIZ` ajenos). `azure-apps/dedicacion.md` (§1, §5, §7
  y la variable `INCIDENCIAS_MESES_ATRAS`): el líder, en el mismo trabajo y
  antes de desplegar (precedente F-030 T19).
- Aviso a `partes` (lo da el humano): dedicación **mueve la `fec`** de `CIZ`
  ajenos (también `synckey partes:`), **añade** `CIZ` en sus partes y deja
  rachas **abiertas** a fin de mes, que el papel de sv4 verá; nunca borra.
## 12. Tests que cambian (lista CERRADA; si cambia otro, PARA)
- **Propios de F-030 que fijan D3, R27 o R44**, reescritos citando el R de
  F-062: `test_f030_reglas_incidencias.py` (`reconciliar`; quedan los de
  `decidir_incidencia` y `synckey_incidencia`), `test_f030_pipeline_incidencias.py`
  (par por mes, R27, `r33_cliente_*`), `test_f030_r30_editar.py`
  (`sigue_editable`, `no_editar_el_par` por cadena), `tests/contratos/f030_r30.json`
  y sus dos `test_f030_r30_punta_a_punta.py` (6-9 y 12-14 son ahora una
  cadena: un `UPDATE` por línea de la 7, nada para la 8), en
  `test_f030_registro.py` los de `trazar_incidencias` con `omitido` sin líneas
  y los de «la quitada no va al transfer» (ahora va en `quitadas`, R17), y en
  `test_f030_r30_front.py` el de la lista de quitadas del modal (R25).
- **Ajenos, solo dobles y claves**: `ClienteFalso`/`EdicionesFalsas` de
  `services/dedicacion-transfer/tests/conftest.py` (`incidencias_en_ventana`,
  `can_leido`); los de `services/dedicacion-api/tests/` que comparan un
  payload entero solo añaden `cierres_recursos` (e `incidencias_mes`) al
  esperado. Ninguna otra aserción; cada cambio, marca «F-062 (lista cerrada)».
## 13. Riesgos y decisiones
- **Escritura nueva en partes ajenos** (mover o añadir un `CIZ`): guarda de
  F-051/D16 con `can` y `synckey` leídos, solo hacia delante (R4), relectura
  en `ejecutar`. Sin T20 en la `0404` no se cierra ni se despliega (el
  transfer desplegado está en **modo real**).
- **Lo que no se puede deshacer sin borrar** (D9): las líneas que F-030 ya
  escribió desde el 2026-10-22 con un `CIZ` por mes se quedan y avisan (R11).
- **Inicios abiertos viejos** (E-11: 9): D14 = B los cierra el último día de
  M−1, a la vista en «Cierres de rachas». Recurso sin registro en M: abierta.
- **Cadena entre obras con `ejecutar` a medias**: si falla la de la dueña, las
  otras quedan `continua` sin líneas; el registro siguiente lo completa (R18).
- **Cuenta del `CIZ` en el parte del inicio** (R5): la del inicio (mismo
  recurso, obra y partida); resolverla costaría lecturas de otra obra.
- **Descartado**: la racha en PostgreSQL (dos verdades); que decida la api (no
  ve Sigrid, duplicaría D2); D11 B; cambiar la `synckey` de un `CIZ` ajeno.
- **`no_coincide` sin lecturas nuevas** (R30): sale de la misma lectura de
  R19; una quitada que el humano ya corrigió en Sigrid deja de avisar sola.
- **Fuera de alcance**: festivos (F-059), elegir días en el front (sigue el
  chip «del al»), deshacer (F-033) y la bandeja de `partes` (F-060).
