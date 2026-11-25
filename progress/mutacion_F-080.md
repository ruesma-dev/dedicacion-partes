<!-- progress/mutacion_F-080.md -->
# F-080 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-080 --workers 3` el 2026-11-25 12:49.

## Alcance

Origen del diff: **rama** (`c5f768e779b1198d3905deb6ea3e2607ae1f5d68` .. `feature/F-080-caja-por-trabajador`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/dedicacion-api/application/use_cases.py` | 38 | 9 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 3 | 0 — sin mutantes |
| **Total** | **41** | **9** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 9 |
| Mutantes evaluados | 3 |
| Muertos | 3 |
| Supervivientes | 0 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 200.8 s |
| SHA de HEAD medido | `eaab1f0c7bc3c3ffbd16b29ca43a345aa9d227bb` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-080_1ikj1gdi/wk_0/services/dedicacion-api` | 72.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-080_1ikj1gdi/wk_1/services/dedicacion-api` | 72.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-080_1ikj1gdi/wk_2/services/dedicacion-api` | 72.5 |
| Media por mutante evaluado (s) | 66.9 |
| Timeout efectivo por mutante (s) | 146 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 3 |
| Un mutante por línea | sí — 9 generados → 3 candidatos, uno por línea |
| Muestreo | no: campaña completa (3 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 53.0 (3 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/dedicacion-api/interface_adapters/api/routes.py` — 3 líneas en alcance, 0 mutantes

#### Declaración del implementer

> Las 3 líneas son el paso de `_tipos(contenedor)` a `CopiarPeriodoAnterior` (l. 267) y a `CopiarTrabajadorAnterior` (l. 514-515): llamadas sin operador, comparación ni constante que el generador sepa mutar. Las cubre `test_f080_r11_las_rutas_pasan_los_tipos_del_contenedor` (sus dos casos). Se comprobó con dos mutantes a mano, M1 y M2 (abajo): ambos mueren.

## Campaña a mano (implementer, 2026-11-25)

Complementa la automática donde el generador no saca mutantes (`routes.py`) y en la guarda que la review 1 señala para RM6. Cada mutante se aplica sobre el árbol de `eaab1f0`, con la suite **entera** de la api (`cd services/dedicacion-api && .venv/Scripts/python.exe -m pytest -q --tb=no -p no:cacheprovider -W ignore`), y se deshace con `git checkout -- <fichero>`.

| # | Fichero:línea | Original → mutado (texto exacto) | Resultado |
|---|---|---|---|
| M1 | `interface_adapters/api/routes.py:267` | `CopiarPeriodoAnterior(_tipos(contenedor)).ejecutar(` → `CopiarPeriodoAnterior().ejecutar(` | **muerto**: `1 failed, 1712 passed` (`test_f080_r11_las_rutas_pasan_los_tipos_del_contenedor[CopiarPeriodoAnterior-/copiar-anterior]`) |
| M2 | `interface_adapters/api/routes.py:514-515` | `CopiarTrabajadorAnterior(⏎            _tipos(contenedor)).ejecutar(` → `CopiarTrabajadorAnterior(⏎            ).ejecutar(` | **muerto**: `1 failed, 1712 passed` (`…[CopiarTrabajadorAnterior-/trabajadores/14/copiar-anterior]`) |
| M3 | `application/use_cases.py:1220` | `    tipo = tipo_de(v.tipo, tipos) if tipos else None` → `    tipo = tipo_de(v.tipo, tipos)` | **muerto**: `11 failed, 1702 passed` (`AttributeError` con `tipos=None`: 7 de `test_f069_importes_api.py -k r8`, `test_f044_r8_copiar_el_mes_copia_la_elegida_sin_la_propuesta` y 3 de `test_f080_r11`) |

M3 confirma la nota RM6 de la review 1: la guarda no es decorativa, y no se ha quitado (ni se quita) para matar ningún mutante. Ningún superviviente a mano: no hay nada que la persona deba aceptar como equivalente.

