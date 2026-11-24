<!-- progress/mutacion_F-076.md -->
# F-076 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-076 --workers 1` el 2026-11-24 17:34.

> **Cómo se lanzó:** el árbol principal tiene `infra/imagenes.json` modificado por el despliegue del humano. Con esos cambios sin commitear, la campaña paralela se niega a arrancar, y `--workers 1` mutaría el árbol del que el humano está desplegando. Por eso se midió en un worktree limpio, separado y en el mismo HEAD (`6324db8`): `python -m harness.mutacion --feature F-076 --rama feature/F-076-excel-sin-resto-de --raiz <worktree> --workers 1`. El venv de la api se enlazó al del árbol principal, que es lo que hace también la campaña paralela (`raiz_venvs`). El árbol principal no se tocó. Este informe y el `.json` se copiaron de ese worktree.

## Alcance

Origen del diff: **rama** (`2eac660ed09909ceb2053f2e8fb2ed03e424ae05` .. `feature/F-076-excel-sin-resto-de`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | 33 | 5 |
| `services/dedicacion-api/infrastructure/excel/exporter.py` | 13 | 0 — sin mutantes |
| **Total** | **46** | **5** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 5 |
| Mutantes evaluados | 3 |
| Muertos | 3 |
| Supervivientes | 0 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 82.2 s |
| SHA de HEAD medido | `6324db8e66749df87491fa52247e63e444fd5270` |
| Línea base (s) — `services/dedicacion-api` | 33.4 |
| Media por mutante evaluado (s) | 27.4 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Un mutante por línea | sí — 5 generados → 3 candidatos, uno por línea |
| Muestreo | no: campaña completa (3 candidatos ≤ tope 20 del nivel `estandar`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 16.2 (3 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/dedicacion-api/infrastructure/excel/exporter.py` — 13 líneas en alcance, 0 mutantes

#### Declaración del implementer

> Las 13 líneas en alcance de `exporter.py` son el docstring del módulo, reescrito en T3: solo cadenas. Lo demás que T3 cambió son borrados: la constante `_CURSIVA` y el bloque `if linea.agregada: … font = _CURSIVA`. Un borrado no deja líneas nuevas que mutar. Lo cubren `test_f076_r11_ninguna_cursiva` (ninguna celda de las tres hojas en cursiva, también con THETA), que estaba en rojo en la fase RED (`('Obras', 'C5')`, ver `progress/impl_F-076.md`), y `test_f076_r4_ninguna_linea_agregada` (sin `LineaDetalle.agregada` ni `AGREGADA_EN_*`).

