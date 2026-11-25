<!-- progress/review_F-080.md -->
Revisión de evidencias desde bb5798d

# F-080 · Review (`critico`): principal + pasada de evidencias

**Principal (pasada 1):** APPROVED sobre `bb5798d`, con mutación «pendiente: pasada de evidencias» y O1-O5; texto
íntegro en `git show eaab1f0:progress/review_F-080.md` (RED, cobertura 13/13, trazabilidad R1-R15, C1-C5).

## Pasada de evidencias · **Veredicto: APPROVED** (HEAD `38c09d2`)

Delta revisado: `bb5798d..HEAD` (5 commits). Toca solo `progress/` (`current.md`, `impl_F-080.md`,
`mutacion_F-080.{md,json}`, este informe), una cita de `docs/ARCHITECTURE.md` y `requirements.md` (O4) y la tarea T9 de
`tasks.md` (O2). **Ni código de producción, ni tests, ni `harness/`** (`git diff --stat bb5798d..HEAD -- services
harness tests` vacío): no invalida nada de lo aprobado y no hace falta relanzar el principal.

## Nivel de rigor

`critico`, declarado en `features.json`. Mutación exigida: uno por línea, 60 % de los candidatos en [100, 300], cero
supervivientes sin aceptación escrita del humano; RM1-RM7. `harness/rigor.local.json` no existe ni lo toca el delta.

## Lo verificado por mí

- **`ARNES_SIN_CACHE=1 bash harness/init.sh`**, sin pipes: código 0, `ENTORNO LISTO`, ningún `[KO]`, suites
  sin caché. Raíz `2319 passed, 47 skipped` (1371 s); api `1713 passed`; front `614`; transfer `2021`. `PUERTA
  COBERTURA [OK] 100.0%` (13/13, umbral 90 % de `critico`); `TAMAÑO` OK (impl 188/220); `CARRIL` y `CAPA E2E` N/A.
- **Totales recalculados, no copiados.** `alcance_de_feature('F-080', rama_base_configurada())` → 2 ficheros, 41
  líneas, origen rama `c5f768e..feature/F-080-caja-por-trabajador`: `use_cases.py` 38 y `routes.py` 3 (l. 267, 514,
  515). `generar_mutantes` → **9** (todos en `use_cases.py` l. 1220, 1221 ×5, 1226 ×3) y 0 en `routes.py`.
  `seleccionar(…, ReglaMuestreo(por_linea=True, fraccion=0.6, suelo=100, techo=300), semilla 20261030)` → **3
  candidatos, tope 100, campaña completa**, y los 3 elegidos coinciden uno a uno (línea, operador y texto
  original→mutado) con los del JSON: l. 1220 `ternario` `if not tipos`, l. 1221 `comparacion` `!=`, l. 1226
  `comparacion` `is not None`. Cuadra con el informe (9 / 3 / 3 / 0).
- **Prueba de control de `routes.py` (0 mutantes).** `generar_mutantes` sobre el fichero entero, sin exclusión de
  alcance: **40** mutantes. El generador funciona; el cero es legítimo: las 3 líneas son paso de argumento
  (`_tipos(contenedor)`) sin operador mutable. La declaración del implementer no está en `PENDIENTE` y la respalda la
  campaña a mano.
- **Campaña a mano, dos filas reproducidas al pie de la letra** en una copia `git archive HEAD` del repo entero en mi
  scratchpad (nunca en el árbol), con la suite entera de la api y el mismo comando del informe:
  - **M3** (`use_cases.py:1220`, `… if tipos else None` → `tipo = tipo_de(v.tipo, tipos)`): `11 failed, 1702 passed`
    (entre ellos `test_f080_r11_un_tipo_por_obra_y_sin_tipos_como_hoy[periodo]` y `…r11_sin_propuesta_por_tipo`).
    Igual que el informe.
  - **M1** (`routes.py:267`, `CopiarPeriodoAnterior(_tipos(contenedor))` → `CopiarPeriodoAnterior()`): `1 failed,
    1712 passed`, `test_f080_r11_las_rutas_pasan_los_tipos_del_contenedor[CopiarPeriodoAnterior-/copiar-anterior]`.
    Igual que el informe. M2 no la repetí (simétrica de M1; la principal ya rompió esa ruta en copia).
- **Tiempo total 200,8 s > 60 s:** campaña automática **no reejecutada**; me quedo en el recálculo puro, las dos filas a
  mano y RM1-RM6.
- **Árbol:** `git status` limpio tras todo lo anterior.

## C4 bis · puntos pendientes de la principal

- [x] `progress/mutacion_F-080.md` generado por `python -m harness.mutacion --feature F-080 --workers 3`, con totales
  reales y JSON de respaldo (`fiable: true`, `sha` completo, regla `origen: nivel`).
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» 0; la línea base **sí** corrió (72,5 s en los 3 workers):
  el cero de supervivientes no es el de una base rota.
- [x] Totales recalculados con `harness.alcance` y `generar_mutantes` (arriba): coinciden.
- [x] Muestreo: 3 candidatos ≤ tope 100 del nivel ⇒ campaña completa; candidatos, evaluados y motivo cuadran con
  `harness/rigor.json`. No es incremental (no hay fila «Modo»). PODADO: N/A, selección de tests apagada (0 podados).
- [x] Supervivientes: **0**, así que no hay análisis que pueda quedar en `PENDIENTE` ni aceptación del humano que pedir.
  «Ficheros sin mutantes» (`routes.py`): declaración escrita y no `PENDIENTE`, con prueba de control hecha.
- [x] Campaña manual con una fila por mutante, texto exacto original→mutado y número de fallos; dos filas reproducidas.
- [x] **RM1.** SHA medido `eaab1f0c7bc3c3ffbd16b29ca43a345aa9d227bb`, distinto de HEAD; `eaab1f0..HEAD` solo toca
  `progress/` (4 ficheros): ninguna línea del alcance cambió después de medir. No hay que repetirla.
- [x] **RM2.** Línea base 72,5 s, media por mutante 66,9 s (juzgado con suite entera 53,0 s): mismo orden de
  magnitud, y por debajo de la base lo explica `-x` con 3/3 muertos. Total 200,8 s ≈ base + una tanda de 3 mutantes en
  paralelo + preparación de worktrees: cuadra.
- [x] **RM3.** Los 3 mutantes muertos cambian el comportamiento observable (con `tipos` presente, `if not tipos` deja la
  caja sin tipo; `!=` invierte la rama `pct`; `is not None` invierte `copiado`): ninguno es equivalente.
- RM4: no hizo falta; ningún veredicto concreto me dejó en duda (los dos más finos los reproduje enteros).
- RM5: N/A, ningún mutante declarado equivalente.
- [x] **RM6.** La guarda `if tipos else None` de `_subfila_copiada` sigue en `use_cases.py:1220` (el delta no toca
  producción) y M3, reproducida por mí, demuestra que no es decorativa. Ningún mutante se mató quitando código.
- RM7: N/A (ya justificado en la principal): R11 transforma subfilas, no protege un orden entre colaboradores.
- [x] «Evidencias» de `impl_F-080.md` (l. 179-188): fila de mutación con 9/3/3/0, SHA y las 3 a mano; fila de workers
  (3, 200,8 s, base 72,5 s, timeout 146 s); tests, cobertura, tiempos y capa e2e N/A. Coinciden con el informe.
- Capa e2e: N/A, `CAPA E2E: N/A` (ningún servicio con e2e ni requisitos `(capa: e2e)`).

## Observaciones de la principal: recogidas

- [x] **O1** (`8ea459c`): la entrada F-080 de `current.md` es un único párrafo al día; fuera los restos «en curso» y el
  recorte de F-077 ya hecho; la nota de F-071 consta en «⚠» (recogida en su spec, D10); dice el paso siguiente.
- [x] **O2** (`8ea459c`): T9 y `current.md` dicen lo mismo («el líder a petición del humano»); M1 suma la lectura por
  `sigrid-api` de las `CO` `porcentajes:vin:%` desde el 2026-11-21, la URL base y el criterio de recuento. La URL del
  front ya es pública en el repo (`docs/INTEGRACION.md` l. 71 y 733): no es un secreto nuevo.
- [x] **O3** (`ce6359d`): `impl_F-080.md` dice «18 items» y mide 188/220.
- [x] **O4** (`8ea459c`): la cita va literal con «[sic]» en `requirements.md` y `ARCHITECTURE.md`.
- O5 sigue fuera de alcance a propósito (D1 b): docstrings de la caja «por obra» en api y transfer, para esa limpieza.

## Checkpoints de la pasada

**C1** [x] `init.sh` sin caché en verde. **C2** [x] F-080 única activa, `in_review`, rama correcta. **C3** [x] El
delta no trae código; las líneas nuevas de docs llevan cita con fecha y origen. **C3 quater:** sigue **pendiente de T8**
(líder, al desplegar), listada en «⚠»; se exige con su SHA antes del cierre. **C4 / C4 bis** [x] arriba. **C5** T7-T10
siguen abiertas por ser MANUAL o `azure-apps`, como en la principal; constan en `current.md`.

## Cambios requeridos

Ninguno.

## Pendiente para cerrar (no lo cierra ningún agente)

M1 (T9) justo antes de desplegar, M3 (T7), M4 (T10) y `azure-apps` (T8, C3 quater), según `current.md` («⚠»).

## Automejora (propuestas para `arnes-base`, no aplicadas)

- (Principal) C4 bis, fase RED: un rojo solo de firma (`TypeError`, `ImportError`) no prueba el comportamiento; exigir
  además una ruptura semántica en copia con su traza.
- (Evidencias) La fila «Workers» de «Evidencias» da el coste por mutante como `total × W ÷ evaluados`, que incluye la
  línea base y la preparación: con pocos mutantes (aquí 3) sale igual al tiempo total y no dice nada. Proponer que el
  informe de mutación imprima «tiempo sin línea base» y que esa fila se calcule sobre él.
