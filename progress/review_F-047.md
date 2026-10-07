<!-- progress/review_F-047.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD`, HEAD `579d7b7`

# F-047 · Review — Tope de filas del transfer (obras con más de 2.000 partidas)

**Veredicto: APROBADO.** Para pasar a `done` faltan dos cosas que no son del
reviewer: (1) que el **humano acepte la justificación de M8** (rigor crítico) y
(2) la **MANUAL** del humano. Ninguna se da aquí por hecha.

**Rigor:** `critico` (declarado). Exige C1–C5, fase RED, cobertura ≥ 80 %,
mutación con cero supervivientes salvo justificación aceptada por el humano y
MANUAL con comando exacto. `sdd: false`: criterios = los 6 `acceptance` y el
plan aprobado («ponle 200k. apruebo») de la descripción y de `current.md`.

## Lo que se pidió comprobar en especial

- **`truncated` sigue siendo error en todas las lecturas.** Hay UN solo
  `/api/sql/read` en el transfer (`sigrid_write_client.py:89`, `_read`) y su
  `raise RuntimeError(... truncada)` (`:101-103`) está intacto. Grep en los
  `.py` versionados: ninguna otra lectura ni ningún `2000` fijo. Lo vigilan
  `test_f037_r16_read_truncado_lanza` y `test_f047_a2_*` (M5 tumba ambos).
- **El tope llega a todos los constructores.** Grep repo-wide de
  `SigridWriteClient(`: fuera de tests solo `api/app.py:102` y
  `prueba_escritura_porcentajes.py:68`; ambos pasan `max_rows=…sigrid_max_rows`,
  cada uno con su test (M9, M10).
- **`.env` no tocado.** Ningún commit lo incluye (solo `.env.example`), está en
  `.gitignore` y los tres `.env` locales tienen mtime 2026-08-19, anterior a la
  rama. El del transfer no declara `SIGRID_MAX_ROWS` (vale el defecto) y
  mantiene `OBRA_PRUEBAS_FORZAR=true` (comprobado sin imprimir valores).
- **Punto 4 (una obra con error no bloquea las demás): se sostiene.** Transfer:
  502 `{"ok":false}` por petición (`app.py:158-161`, `:186-189`).
  `TransferClient._post` nunca lanza (`transfer_client.py:20-33`). Api: agrupa
  por `obra["ide"]` (`registro_sigrid.py:100`), la postventa va en la misma
  petición (`es_postventa` es campo de línea), los bucles `:128`/`:145` no
  cortan y `_trazar` solo si `ok` (`:150`). Front: `return` dentro del
  `forEach` (`app.js:1705`), toast que solo da cuentas (`:1776-1782`), y los
  «⇪ Sigrid» de fila (`:893-897`, `:1028-1033`) mandan un solo trabajador.
  Sin cambio de comportamiento: correcto, se propone aparte.
- **`azure-apps/dedicacion.md`:** sin commit, con exactamente las dos filas
  nuevas, idénticas a `docs/INTEGRACION.md` §3 y §7. Listado en `current.md`.

## Checkpoints

**C1** [x] `bash harness/init.sh` exit 0 (418 passed, 1 skipped; tres
servicios en verde). [x] Ficheros base presentes.
**C2** [x] Una sola `in_progress`. [x] Rama `feature/F-047-…`. [x]
`current.md` con F-047 en la primera línea y sección propia. [x] Sin `done`
nuevas.
**C3** [x] Hexagonal: `config` no importa de `infrastructure` (por eso el
200.000 está dos veces, constante y literal, cada uno con test y mutante
muerto: aceptable). [x] Primera línea con ruta en los `.py` tocados. [x] Sin
`print`, TODOs, secretos (`sin-clave` es un doble) ni dependencias nuevas.
[x] Trampas del dominio: no toca escala, postventa ni escrituras;
`OBRA_PRUEBAS_FORZAR` intacto.
**C3 bis** N/A: nada en `docs/referencia/`. **C4** [x] Cada `acceptance` trazado (tabla abajo), 10/10 en verde. [x] Sin
red ni BBDD (`httpx.post` → `SigridApiEmulada`; `Settings(_env_file=None)`;
el script solo actúa bajo `__main__`). [x] MANUAL en `current.md` (ver O2).

**C4 bis**
- [x] `rigor` declarado. [x] Fase RED real (`assert [2000] == [200000]` y el
  `RuntimeError … truncada` del preflight: reproduce el fallo de producción).
- [x] Cobertura: `100.0% de 3 líneas cambiadas (3/3)`.
- [x] Recálculo puro: `alcance_de_feature` = 4 ficheros / 20 líneas
  (5+13+1+1); `generar_mutantes` = 2 (`settings.py:30`,
  `sigrid_write_client.py:56`, `entero` 200_000→200001). Coinciden.
- [x] «Tiempo total» 27,5 s < 60 s ⇒ **campaña reejecutada** (`--workers 1`,
  salida en el scratchpad): 2 evaluados, 2 muertos, 0 supervivientes,
  0 timeouts, 0 sin veredicto, 54,7 s, mismos mutantes. Árbol limpio después.
- [x] Coste por mutante 27,5 × 1 ÷ 2 = 13,7 s. [x] Sin «⚠ CAMPAÑA NO
  VÁLIDA», base rota = 0.
- [x] RM1: medido en `354ddbb…`; desde ahí solo cambian `progress/` y una
  línea de imports del test: el alcance de producción es el revisado.
- [x] RM2: base 8,4 s, media 13,7 s, 1 worker, 2 × 13,7 ≈ 27,5. Coherente.
- [x] RM5: único equivalente (M8) reproducido (abajo). [x] RM6: no se quitó
  código defensivo.
- N/A justificado, «manual sustitutiva»: la automática dio 2 y es válida; la
  manual es **complementaria**. Aun así reproduje 5 filas al pie de la letra
  sobre una copia (`git archive HEAD` en el scratchpad; base 651 passed +
  4 skipped): M1 `"max_rows": self._max_rows}`→`"max_rows": 2000}` **4
  fallos**; M3 `int(max_rows)`→`max_rows` **1**; M5 `raise …truncada")`→`pass`
  **2** (`f037_r16`, `f047_a2`); M10 sin `max_rows=st.sigrid_max_rows,` **1**;
  M8 alias→`SIGRID_API_MAX_ROWS` **0** (sobrevive). Coinciden con la tabla.
- [x] Supervivientes analizados: automática, ninguno; M8 con justificación
  escrita, **aceptación del humano PENDIENTE** (la exige el rigor crítico).
- [x] «Evidencias» con los cuatro números y `--workers 1`. [x] Ningún N/A sin
  motivo.

**M8 (RM5).** `populate_by_name=True` (`settings.py:13-16`), pydantic 2.13.4,
pydantic-settings 2.15.0. Original: `SIGRID_MAX_ROWS=350000`→350000,
`SIGRID_API_MAX_ROWS=7`→200000 (ignorada). Mutante: 350000 y **7**. Se sostiene
**respecto al contrato documentado** (`SIGRID_MAX_ROWS` y el defecto no
cambian), pero no es equivalente en sentido estricto: el mutante además honra
`SIGRID_API_MAX_ROWS` —el nombre que sugería el encargo— y el original la
ignora. El informe lo reconoce («añade un nombre aceptado más»). Riesgo
práctico nulo hoy: infra no declara ninguna de las dos.

**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** N/A `tasks.md` (`sdd: false`); un commit `F-047 Tn:` por tarea. [x]
Árbol limpio. [x] `features.json` en `in_progress`, correcto hasta MANUAL y M8.

## Cobertura: acceptance → tests (`tests/test_f047_tope_filas.py`)

| Acceptance | Test(s) |
|---|---|
| a1 tope configurable, 200.000, `.env.example`, docs | `a1_el_tope_por_defecto_…`, `a1_el_tope_configurado_…`, `a1_todas_las_lecturas_…`, `a1_ajuste_…`, `a1_la_app_inyecta_…`, `a1_el_script_…`, `a1_env_example_…`; docs a mano |
| a2 `truncated` sigue siendo error | `a2_una_obra_mayor_que_el_tope_…`, `a2_justo_en_el_tope_…`, `test_f037_r16_read_truncado_lanza` |
| a3 tope, truncado y obra > 2.000 | `a3_obra_con_mas_de_2000_partidas_…` (partida tras la fila 2.000, `_read` real) |
| a4 punto 4 | Revisado contra el código (arriba) |
| a5 MANUAL | Pendiente del humano (no bloquea la review) |
| a6 review + init.sh | Este informe; init.sh en verde |

## MANUAL: se puede seguir contra el código

Los tres servicios tienen `.venv/Scripts/python.exe` y `main.py`; puertos
8006/8090/8080 en sus `settings.py`; `/health` devuelve `modo_pruebas`
(`app.py:122-127`). La api no declara `TRANSFER_BASE_URL` en su `.env`: va al
defecto `127.0.0.1:8006`, el transfer **local** (no el de Azure, en modo real).
En modo pruebas el preflight lee el presupuesto de la obra **origen**
(`registro_pipeline.py:380`): la prueba ejercita la 0696. El modal tiene
«Cancelar» (`app.js:1752`). La opción B del impl casa con `LineaIn`.

## Observaciones no bloqueantes (recoger, no dejar en «anotado»)

1. **O1** `mutacion_F-047.md`, tabla manual: añadir `fichero:línea`, texto
   exacto original→mutado y nº de fallos (los míos, arriba). M2, M4, M6, M7,
   M9 y M11 se describen solo con palabras.
2. **O2** MANUAL de `current.md`: falta la precondición (base local con
   septiembre 2026 y Bas Leal) y la opción B como alternativa, que solo están
   en `impl_F-047.md`. En la opción B, `empresa = 1` debe ser la de la 0696.
3. **O3** Al pedir al humano que acepte M8, darle el matiz de arriba.

**Cambios requeridos:** ninguno.

## Automejora (propuesta, no aplicada)

C4 bis exige `fichero:línea`, texto exacto y nº de fallos solo a la campaña
manual **sustitutiva**. Propongo extenderlo a la manual **complementaria en
rigor crítico** que declare un equivalente: es lo que el humano debe aceptar
y necesita poder reproducir.
