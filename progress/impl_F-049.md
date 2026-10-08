<!-- progress/impl_F-049.md -->
# F-049 · Avisos del modal de registro por tipo · informe del implementer

- **Rama:** `feature/F-049-avisos-registro-por-tipo`, copia aparte
  `PycharmProjects/porcentajes-f041`. `sdd: false`, rigor **estándar**.
- **Parte 1** (T1-T3, review 2 APROBADA): `3ad478b`, `a854138`, `d6d8658`,
  `81dbbd8`. Su informe completo, tal como se revisó:
  `git show cbc0451:progress/impl_F-049.md`. Aquí va resumido.
- **Ampliación** (aprobada por el humano el 2026-10-08, T4-T7): `24bef2f`
  (T4), `50a8d1e` (T5), `e7b660f` (T6), T7 (mutación, informe, estado). Ni
  `.env`, ni Azure, ni Sigrid real, ni push.

## Parte 1 · avisos rotulados por tipo (resumen)

`app.js`: `pctNuevas(c)` (suma de `c.nuevas[].can`, como `nueva_can`, que
`asdict` no publica) y `rotuloConflicto(c)` (pura) → **Sin partida**,
**Sobrecarga** (`suma_existente` con `contexto`, `suma_total`, `exceso`),
**Pisar** (líneas que se borran y % nuevo) o, si el motivo es desconocido,
**Confirmar**. La casilla sigue llevando `c.clave`; `registroEjecutar`, igual.
Test: `services/dedicacion-front/tests/test_f049_avisos_registro.py` (18).

**RED (parte 1, trazas reales).** El `pintarModalPreflight` de `9c81898`
con el caso de la captura (`python <scratchpad>/red_modal.py`):

```
Pisar MADM de GONZALEZ PANIAGUA: se borran  y se escribe 0%
Pisar MADM de GONZALEZ PANIAGUA: se borran  y se escribe 0%
Pisar MADM de GONZALEZ PANIAGUA: se borran  y se escribe 0%
```

```
$ python -m pytest tests/test_f049_avisos_registro.py -q -p no:cacheprovider
E       AssertionError: no existe la función pctNuevas en app.js
E           {fmtPct(c.nueva_can != null ? c.nueva_can * 100 : 0)}` +
16 failed, 1 passed in 1.19s
```

Verde: 18 passed. Mutación manual: 33/33 muertos (`mutacion_manual` §1-2).

## Ampliación · qué cambió

- **T4 · d) transfer** (`registro_pipeline.py`, tras el bucle de partidas
  del paso 4): si no se ha leído el presupuesto de origen y hay alguna
  acción `escribir` de obra normal (no postventa, no VAR), se lee una vez y
  `partidas_obra` sale con su catálogo. Antes, con todas las líneas de obra
  con partida manual, salía `[]`. Ninguna partida ni escritura cambia.
  Test: `services/dedicacion-transfer/tests/test_f049_partidas_obra.py` (5).
- **T5 · a), b), c) front** (`app.js`):
  - `pedirPreflight()` (nueva): la petición de siempre (overrides, trabajador).
  - **b)** `registroPreflight` (los tres botones: general, «⇪ Sigrid» de
    fila y el del editor) empieza con `registro.overrides = {}`.
  - **a)** `repreflightPartida()` (nueva), llamada desde el `change` de
    `.sel-partida` después de apuntar la partida: desactiva «Registrar»
    («Analizando…»), repite el preflight y repinta. Las casillas marcadas
    se leen al llegar la respuesta y `pintarModalPreflight` las vuelve a
    marcar (`checked`) si su `clave` sigue en el preflight nuevo
    (`registro.pisar`, que existía y no se usaba).
  - `registro.seq`: solo pinta la última petición; nunca reabre un modal cerrado.
  - **c)** `opcionesPartida(partidas, sel, cod)`: si `sel` (la `paride`) no
    está en la lista, añade una opción `selected` «`cod` · (no está en la
    lista)» (`partida <ide>` sin código). Con `sel` 0/nulo, como antes.
  - Test: `services/dedicacion-front/tests/test_f049_ampliacion_registro.py` (24).
- **T6 · e) CSS** (`styles.css`): `.modal .aviso` y `.modal .conflicto
  .check` con `white-space: normal; overflow-wrap: anywhere;` (la segunda,
  además, `display: block`).

## Ampliación · decisiones y desviaciones (justificadas)

1. **Si falla el preflight repetido:** `toast` y «Registrar» vuelve a estar
   activo. Seguro: `ejecutar` reanaliza con las partidas elegidas y solo
   confirma claves marcadas que sigan existiendo. Bloquearlo obligaría a
   reabrir, que (b) borra las partidas elegidas.
2. **e), qué se salía de verdad** (modal y CSS REALES en Chrome headless,
   script de un solo uso): el aviso amarillo con el texto real ya se
   ajustaba; se salía el **rótulo de la casilla del conflicto** (hereda el
   `nowrap` de `.check`; los rótulos de la parte 1 son largos): cortado en
   «… imputación. Eli» → en dos líneas dentro de su caja. El aviso sí se
   salía con palabras largas sin espacios (probado): se corrigen los dos.
3. **Tests anteriores que cambian (dos):**
   - `test_f039_r22_el_resto_de_acciones_sigue_igual` (front): el literal
     de la llamada pasa a `opcionesPartida(partidas, a.paride,
     a.partida_cod)` (c). Lo demás de R22, igual.
   - `test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos` (transfer)
     **llevaba en rojo desde `3ad478b` (parte 1)**: exige que `app.js` no
     nombre los motivos, y rotular por motivo es el plan aprobado. **`init.sh`
     no lo vio**: la caché del servicio transfer solo mira su árbol y
     `app.js` es del front; salió al tocar el transfer en T4 (`app.js` de
     `3ad478b^` nombra 0 veces cada motivo; el de `3ad478b`, 2/1/1). Su
     docstring pide «decidir si el contrato sigue siendo el de F-002»: lo
     sigue (ningún campo nuevo). Queda solo para la api, y
     `test_f013_r4_el_front_rotula_por_motivo_y_degrada` exige que el front
     ramifique solo en `rotuloConflicto` y caiga en «Confirmar». **Para el
     líder:** esa caché no ve tests que leen ficheros de otro servicio.
4. **MANUAL: transfer con el código de esta copia** (d no está en la rama
   de F-045), arrancado **desde la carpeta del transfer de la principal**:
   su `.env` se lee de la carpeta de arranque (`env_file=".env"`). No se
   copia ni toca `.env`.

## Ampliación · fase RED (trazas reales)

**d) transfer**, antes de T4 (desde `services/dedicacion-transfer`):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f049_partidas_obra.py -q -p no:cacheprovider
>       assert pf.partidas_obra == CATALOGO_ORIGEN
E       AssertionError: assert [] == [{'ide': 8000...goria': 'CI'}]
E         Right contains 2 more items, first extra item: {'ide': 80001, 'cod': 'CI.1.10', 'res': 'ENCARGADO (ACUNA)', 'categoria': 'CI'}
FAILED tests/test_f049_partidas_obra.py::test_f049_d_todas_manuales_publica_el_catalogo_de_origen
FAILED tests/test_f049_partidas_obra.py::test_f049_d_varias_manuales_una_sola_lectura
2 failed, 3 passed in 0.82s
```

(Los 3 que pasan son controles de lo que no cambia: una sola lectura con
mezcla, nada con solo postventa, la escritura con la partida manual. Una
primera pasada dio 3 fallos por un dato mío mal puesto en un control
—`categoria` es `"CI"`—; se corrigió el dato, no el código.) Verde: 5
passed; suite del transfer 658 passed.

**a), b), c), e) front**, antes de T5 (desde `services/dedicacion-front`):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f049_ampliacion_registro.py -q -p no:cacheprovider
E       AssertionError: no existe la función pedirPreflight en app.js      (×10, a y b)
E       AssertionError: assert ({'3002': 80002} == {'3002': 80002} ... and 0 == 1)
E       AssertionError: assert [('sin_partid...6|9|5|0', '')] == [('sin_partid..., ' checked')]
E       AssertionError: assert [] == [('80002', 'C...n la lista)')]
E       assert 'A&lt;b&gt;&amp;C · (no está en la lista)' in '<option value="0">— sin partida —</option>'
E       AssertionError: assert 'white-space: normal;' in 'color: var(--warn); font-size: .76rem;'
E       AssertionError: no hay regla .modal .conflicto .check en styles.css
20 failed, 3 passed in 5.52s
```

(`0 == 1`: el `change` no repetía el preflight; `[] == […]`: c) salía
«— sin partida —»; pasan 3 controles de c).) Verde tras T6: 23 passed; T7
añade 1 (A27): **24 passed**.

## Ampliación · mutación

- **Python** (borrados los `__pycache__` del transfer; luego
  `python -m harness.mutacion --feature F-049 --workers 1`): **7
  generados, 7 muertos, 0 supervivientes**, 74,6 s, sin muestreo
  (`progress/mutacion_F-049.md`).
- **JS y CSS, manual** (`progress/mutacion_manual_F-049.md` §3, con
  fichero:línea, texto exacto y nº de fallos): **32 (28 `app.js`, 4
  `styles.css`), 32 muertos**, 302 s en serie. En la primera pasada **A27**
  (repreflight ANTES de apuntar la partida: viajaría la anterior) solo lo
  mataba la comprobación estática del orden: hueco real, no equivalente;
  T7 añade `test_f049_a_el_preflight_repetido_lleva_la_partida_recien_elegida`.

## Fuera del alcance

- Toast final «repite y marca pisar»: F-048. Los % que ya hay en el
  parte, en el cuadrante: F-054. Caché de `init.sh` (decisión 3): líder.
- `azure-apps/`: sin cambios (`partidas_obra` ya existía; ahora sale lleno
  en un caso en que salía vacío).

## MANUAL pendiente (humano, en local, sin pulsar «Registrar»)

Tres consolas. **Transfer: código de ESTA copia, arrancado desde la carpeta
de la principal** (decisión 4); api, de la principal; front, de esta copia.

```powershell
# 1) Transfer (debe salir modo_pruebas = True; si no, PARAR)
cd C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-transfer
.\.venv\Scripts\python.exe C:\Users\pgris\PycharmProjects\porcentajes-f041\services\dedicacion-transfer\main.py
Invoke-RestMethod http://localhost:8006/health      # en otra consola
# 2) Api (copia principal)
cd C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api
.\.venv\Scripts\python.exe main.py
# 3) Front (esta copia); antes, parar cualquier otro front en el 8080
cd C:\Users\pgris\PycharmProjects\porcentajes-f041\services\dedicacion-front
.\.venv\Scripts\python.exe main.py
```

4. `http://127.0.0.1:8080`, **Ctrl+F5**, septiembre 2026, «⇪ Sigrid» en
   GONZALEZ PANIAGUA. Marca una casilla que **no** sea la «Sin partida» de
   la línea que vas a cambiar (si la hay).
5. **a)** En la línea con aviso amarillo «partida no localizada…», elige
   una partida. **Esperado:** «Registrar» pasa a «Analizando…» (no se
   puede pulsar) y el modal se repinta: desaparecen el aviso amarillo y la
   casilla «Sin partida» de esa línea, la partida elegida sigue elegida y
   la casilla marcada en el paso 4 sigue marcada.
6. **d)** Si en esa obra todas las líneas «escribir» tienen ya partida
   elegida: el desplegable enseña la partida con su descripción y la lista
   entera (no «— sin partida —»). F12 → Red → la última petición
   `preflight` → Respuesta: `partidas_obra` de esa obra **no** está vacío.
7. **b)** **Cancelar**, abrir otra vez con «⇪ Sigrid» (y con «Registrar
   en Sigrid» general): vuelve la propuesta automática con su aviso, no la
   partida del paso 5. **Cancelar.**
8. **c) y e)** F12 → consola (Chrome pide `allow pasting` antes del primer
   pegado), pegar:

```js
pintarModalPreflight({obras: [{obra: {codigo: "0694", nombre: "Prueba F-049 c/e"}, ok: true, partes: [], partidas_obra: [], partidas_postventa: [], acciones: [
 {registro_id: 999999, nombre: "PRUEBA", destino: "obra", accion: "escribir", can: 0.5, hora_codigo: "MADM", paride: 99999, partida_cod: "CI.9.99",
  aviso: "partida no localizada para la categoría/nombre: no se escribe sin confirmarlo — elige una partida o marca la confirmación · palabra_larga_sin_espacios_para_ver_que_el_texto_no_se_sale_del_recuadro_xxxxxxxxxxxxxxxxxxxx"}],
 conflictos: [{clave: "x", motivo: "sin_partida", nombre: "GONZALEZ PANIAGUA, MILAGROS", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.5}], lineas: [], contexto: []}]}]})
```

   **Esperado:** el desplegable enseña **«CI.9.99 · (no está en la
   lista)»** elegida, no «— sin partida —» (c); el aviso amarillo y el
   texto de la casilla «Sin partida» se parten en varias líneas **dentro**
   de su recuadro (e). **No tocar el desplegable ni «Registrar»
   (lanzaría el registro del periodo; en modo pruebas, contra la 0404).
   Cancelar.**

La MANUAL de la parte 1 (rótulos por tipo) sigue en `progress/current.md`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la ampliación | transfer `test_f049_partidas_obra.py` **5 passed**; front `test_f049_ampliacion_registro.py` **24 passed** (node v24.14.1) |
| Suites por servicio (`init.sh`, sin caché) | front **142 passed** (22,26 s; 19 warnings previas); transfer **658 passed** (17,98 s); api en verde (caché) |
| `bash harness/init.sh` (tal cual, código 0) | **ENTORNO LISTO**; raíz 418 passed, 1 skipped (90,39 s); todo `[OK]` salvo el `[AVISO]` de `ruff` (237, deuda previa: los tests nuevos no añaden ninguno); `PUERTA TAMAÑO` impl 219/220 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 2 líneas cambiadas cubiertas (2/2, umbral 80%)` (Python; el JS no se mide) |
| Mutantes Python | **7 generados, 0 supervivientes**, 74,6 s, 1 worker |
| Mutantes JS/CSS (manual) | **32 generados, 0 supervivientes**, 302 s en serie (325 s al repetirla tras `ruff`: idéntica) |
| Captura del CSS (e) | Chrome headless, modal real: antes, rótulo cortado; después, dentro (decisión 2) |
