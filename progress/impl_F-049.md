<!-- progress/impl_F-049.md -->
# F-049 · Avisos del modal de registro rotulados por tipo · informe del implementer

- **Rama:** `feature/F-049-avisos-registro-por-tipo`, en la copia aparte
  `PycharmProjects/porcentajes-f041`. `sdd: false`, rigor **estándar**.
- **Commits:** `3ad478b` (T1), `a854138` (T2), T3 (este informe, la línea
  «Estado» de `current.md`).
- **Alcance respetado:** solo `services/dedicacion-front/static/js/app.js`
  (más su test y el papeleo). Ni transfer, ni api, ni CSS (no hizo falta), ni
  `.env`, ni Azure, ni Sigrid.

## Qué cambió

Tareas derivadas de los `acceptance`:

- **T1** (`3ad478b`) · `app.js`:
  - `pctNuevas(c)` (nueva, pura): el % de lo que se escribiría = suma de
    `c.nuevas[].can` × 100, formateado con `fmtPct`. Es la misma suma que la
    propiedad `Conflicto.nueva_can` del transfer, que `asdict` **no**
    serializa (por eso el front leía `undefined` y pintaba 0 %).
  - `rotuloConflicto(c)` (nueva, pura, sin DOM): devuelve
    `{tipo, titulo, detalle}` en texto plano según `c.motivo`:
    - `sin_partida` → «**Sin partida** · `<nombre>, <hora> <%> en el parte
      <cod>`: se escribiría sin partida de imputación. Elige una partida en
      la tabla o marca la casilla para escribirlo sin partida».
    - `sobrecarga` → «**Sobrecarga** · `<nombre> en el parte <cod>`: ya tiene
      `<suma_existente>` (`<hora %>` de cada línea de `contexto`), se añade
      `<% nuevas>` y sumaría `<suma_total>`, un `<exceso>` por encima de la
      jornada. Marca la casilla para escribirlo igualmente».
    - `pisado`, vacío o ausente → «**Pisar** · `<hora> de <nombre> en el
      parte <cod>`: se borran línea `<ide>` (`<hora> <%>`, fec `<fecha>`), …
      y se escribe `<% nuevas>`».
    - cualquier otro `motivo` → «**Confirmar** · `<nombre>, <hora> <%> en el
      parte <cod>: <motivo>`» (no se disfraza de «Pisar»).
  - `pintarModalPreflight`: cada conflicto se pinta con
    `<strong>titulo</strong> · detalle`, ambos con `escapeHtml`. La casilla no
    cambia: `class="chk-pisar"` y `value="${escapeHtml(c.clave)}"`.
    `registroEjecutar` no se toca: sigue mandando esos `value` como
    `pisar_claves`.
- **T2** (`a854138`) · campaña manual de mutantes
  (`progress/mutacion_manual_F-049.md`) y un test más para el único
  superviviente de la primera pasada (M19).
- **T3** · este informe; `bash harness/init.sh` en verde; línea «Estado» de
  F-049 en `progress/current.md` (solo esa línea).

Test nuevo: `services/dedicacion-front/tests/test_f049_avisos_registro.py`
(18 tests). Patrón de F-041/F-042: extrae el código REAL de `app.js` y lo
ejecuta en `node`.

## Decisiones de diseño (dentro del plan aprobado)

1. **Campos reales leídos en el código**, no supuestos:
   `Conflicto` (`dedicacion-transfer/domain/models/registro_models.py:193`)
   se publica con `asdict` (`interface_adapters/api/app.py:151`) y la api lo
   reenvía tal cual (`dedicacion-api/application/registro_sigrid.py:129-131`).
   `nuevas` viene de `_nueva()` (`registro_pipeline.py:99`: `registro_id`,
   `can`, `tot`, `hora_codigo`, `fecha_int`, `partida_cod`). `motivo` es
   `"pisado"` (defecto del dataclass), `"sobrecarga"` o `"sin_partida"`.
   `can`, `suma_*` y `exceso` en escala 0-1 → `× 100` para `fmtPct`.
2. **El front no decide nada**: suma `nuevas` para mostrar el % (lo mismo
   que `nueva_can`), y lo demás lo pinta tal cual llega. No compara con la
   jornada ni filtra conflictos (lo vigila
   `test_f049_r3_el_rotulo_no_decide_nada`).
3. **Función pura que devuelve texto plano** y el escapado en quien pinta:
   `escapeHtml` usa el DOM, y así el rotulado se prueba en `node` sin DOM.
4. **Motivo desconocido → «Confirmar»** con el motivo literal. Decisión
   menor, defensiva, sin cambio de comportamiento: antes cualquier aviso
   salía como «Pisar» (que dice que se borra algo) y ese es justo el fallo.
5. **En la sobrecarga se listan las líneas de `contexto`** (`hora` y `%`):
   en un `Conflicto` de sobrecarga `contexto` son las líneas contadas
   (`cap.contadas`, `registro_pipeline.py:552`). Es lo que explica «ya tiene
   95 %» en el caso de la captura (MADM 95 % metida a mano).
6. **Sin CSS**: `<strong>` basta para distinguir el tipo; no se añadió clase.

## Fase RED (trazas reales)

### 1 · El fallo, reproducido con el código de antes (sin tocar `app.js`)

Script de un solo uso en el scratchpad que ejecuta en `node` el
`pintarModalPreflight` REAL de `9c81898` con los datos de prueba del test (el
caso de la captura: 0672 con un «sin partida»; 0694 con un «sin partida» y
una sobrecarga) e imprime el texto de cada casilla:

```
$ python <scratchpad>/red_modal.py
Pisar MADM de GONZALEZ PANIAGUA: se borran  y se escribe 0%
Pisar MADM de GONZALEZ PANIAGUA: se borran  y se escribe 0%
Pisar MADM de GONZALEZ PANIAGUA: se borran  y se escribe 0%
```

Es exactamente lo que vio el humano: «Pisar» 1 vez en la 0672 y 2 en la 0694,
sin líneas que borrar y con 0 %.

### 2 · Los tests, antes del código

```
$ cd services/dedicacion-front
$ python -m pytest tests/test_f049_avisos_registro.py -q -p no:cacheprovider
FFFFFFFFFFFFFFF.F                                                        [100%]
...
nombre = 'pctNuevas'
>       assert m, f"no existe la función {nombre} en app.js"
E       AssertionError: no existe la función pctNuevas en app.js
...
___________________ test_f049_r2_el_front_no_lee_nueva_can ____________________
    def test_f049_r2_el_front_no_lee_nueva_can():
>       assert "nueva_can" not in JS
E         'nueva_can' is contained here:
E           {fmtPct(c.nueva_can != null ? c.nueva_can * 100 : 0)}` +
...
16 failed, 1 passed in 1.19s
```

(El que pasaba es `test_f049_r3_ejecutar_manda_las_mismas_claves`: fija lo
que **no** debe cambiar.) Después, `test_f049_r2_el_front_no_lee_nueva_can`
se afinó a `re.search(r"\.nueva_can\b", JS)` para que el comentario que
explica el porqué no lo dispare; con el `app.js` de `9c81898` sigue dando
`True` (comprobado: `git show HEAD:…/app.js | python -c …` → `True`).

### 3 · Verde

```
$ python -m pytest tests/test_f049_avisos_registro.py -q -p no:cacheprovider
.................                                                        [100%]
17 passed in 3.91s
```

El mismo script del punto 1 con las funciones nuevas:

```
<strong>Sin partida</strong> · GONZALEZ PANIAGUA, MADM 50% en el parte PT26/00319: se escribiría sin partida de imputación. Elige una partida en la tabla o marca la casilla para escribirlo sin partida
<strong>Sin partida</strong> · GONZALEZ PANIAGUA, MADM 50% en el parte PT26/00319: se escribiría sin partida de imputación. Elige una partida en la tabla o marca la casilla para escribirlo sin partida
<strong>Sobrecarga</strong> · GONZALEZ PANIAGUA en el parte PT26/00319: ya tiene 95% (MADM 95%), se añade 50% y sumaría 145%, un 45% por encima de la jornada. Marca la casilla para escribirlo igualmente
```

(Cifras de prueba: el % real de cada línea lo da el preflight de verdad.)

## Mutación

La mutación automática no muta JS: campaña manual en
`progress/mutacion_manual_F-049.md` (script reproducible incluido).
**33 mutantes, 33 muertos, 0 supervivientes.** En la primera pasada
sobrevivió **M19** (separador entre las líneas contadas de la sobrecarga):
hueco real, los datos solo tenían una línea contada. Cerrado en T2 con
`test_f049_r1_sobrecarga_con_varias_lineas_contadas`.

## Fuera del alcance

- El toast de `registroEjecutar` («… pendientes de confirmar (repite y marca
  pisar)») sigue diciendo «pisar» para cualquier aviso: no estaba en el plan.
  Si se quiere, es una línea; queda para el líder/humano.
- El texto de la tabla de acciones (`a.aviso`, `a.motivo`) no se toca.
- Transfer y api: sin cambios (el campo `nueva_can` no se añade a la
  respuesta; el front usa `nuevas`, que es lo que ya viaja).
- `azure-apps/`: nada que actualizar (no cambia lo que se expone ni consume).

## MANUAL pendiente (humano, en local, sin pulsar «Registrar»)

**Ojo con el front:** la copia principal está en la rama de F-045 y su
`app.js` **no** lleva F-049. Transfer y api se arrancan desde la copia
principal (tienen `.env`); el **front, desde la copia aparte** (no necesita
`.env`: sus valores por defecto apuntan a la api en `127.0.0.1:8090`).

```powershell
# 1) Transfer (copia principal). Su .env debe tener OBRA_PRUEBAS_FORZAR=true.
cd C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-transfer
.\.venv\Scripts\python.exe main.py
# en otra consola: debe decir modo_pruebas = True
Invoke-RestMethod http://localhost:8006/health
# 2) Api (copia principal), con TRANSFER_BASE_URL apuntando al 8006 local
cd C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api
.\.venv\Scripts\python.exe main.py
# 3) Front (copia APARTE, rama F-049); parar antes cualquier front en el 8080
cd C:\Users\pgris\PycharmProjects\porcentajes-f041\services\dedicacion-front
.\.venv\Scripts\python.exe main.py
```

4. `http://127.0.0.1:8080`, **Ctrl+F5**, septiembre 2026, fila de
   **GONZALEZ PANIAGUA**, botón «⇪ Sigrid» de la fila. **Esperado:** ningún
   aviso dice «Pisar … se borran  y se escribe 0%»; cada uno empieza por
   **Sin partida**, **Sobrecarga** o **Pisar** con su % real (el de la
   línea), y «Pisar» solo aparece si hay líneas que se borran. **Cancelar.**
5. **Limitación del modo pruebas:** con `OBRA_PRUEBAS_FORZAR=true` el
   preflight analiza los partes de la **0404**, no los de la 0672/0694, así
   que la **sobrecarga** de la captura (MADM 95 % a mano en PT26/00319 de la
   0694) **no** sale en local; los «sin partida» dependen del casado contra
   la 0404. Reproducirla exacta exige el transfer local en modo real, que
   según `CLAUDE.md` **necesita autorización expresa del humano** (y aun
   así, solo preflight). No se propone aquí.
6. **Comprobación visual de los tres tipos sin depender de los datos**: en
   la misma página, consola del navegador (F12), pegar:

```js
pintarModalPreflight({obras: [{obra: {codigo: "0694", nombre: "Prueba F-049"}, ok: true, partes: [], acciones: [], conflictos: [
 {clave: "sin_partida:1", motivo: "sin_partida", nombre: "GONZALEZ PANIAGUA", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.05}], lineas: [], contexto: []},
 {clave: "sobrecarga:1|2026-09", motivo: "sobrecarga", nombre: "GONZALEZ PANIAGUA", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.1}], lineas: [], contexto: [{hora_codigo: "MADM", can: 0.95}], suma_existente: 0.95, suma_total: 1.05, exceso: 0.05},
 {clave: "1|2026|9|5|0", motivo: "pisado", nombre: "GONZALEZ PANIAGUA", recurso_ide: 1, hora_codigo: "MADM", parte_cod: "PT26/00319", nuevas: [{can: 0.6}], lineas: [{ide: 8001, hora_codigo: "MADM", can: 0.4, fecha_int: 20260930}], contexto: []}]}]})
```

   **Esperado:** tres casillas rotuladas «Sin partida» (5%), «Sobrecarga»
   (ya tiene 95% (MADM 95%), se añade 10% y sumaría 105%, un 5% por
   encima) y «Pisar» (se borran línea 8001 (MADM 40%, fec 20260930) y se
   escribe 60%). Pintarlo no llama a nada, pero el modal trae el botón
   «Registrar» de verdad: **NO pulsarlo** (lanzaría `registro/ejecutar` del
   periodo; en modo pruebas, contra la 0404). **Cancelar.**

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-049 | `test_f049_avisos_registro.py`: **18 passed** (17 de T1 + 1 de T2), en node v24.14.1 |
| Suite del front (`init.sh`) | **118 passed**, 19 warnings previas, 19,97 s |
| Suite raíz (`init.sh`) | 418 passed, 1 skipped, 97,65 s; api y transfer en verde (caché) |
| Cobertura de líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-049 no cambia líneas Python de producción frente a dev)`; el cambio es JS, que no se mide |
| Mutantes | `harness.mutacion` no muta JS: campaña manual, **33 generados, 0 supervivientes** (`progress/mutacion_manual_F-049.md`); **campaña en serie, 1 worker**: 299 s en total sin `-x` (medida en la review 1; la pasada con `-x` no se cronometró) |
| `bash harness/init.sh` (sin pipes, código 0) | **ENTORNO LISTO**; todo `[OK]` salvo el `[AVISO]` de `ruff` (237, deuda previa; el test de F-049 no añade ninguno); `PUERTA TAMAÑO: impl 216/220`. Mutación repetida tras el ajuste de `ruff` del test: 33/33 muertos |
