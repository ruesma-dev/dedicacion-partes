<!-- progress/mutacion_F-045.md -->
# F-045 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-045` el 2026-10-08 14:23.

## Alcance

Origen del diff: **rama** (`20f65b443dd937b7688016fb9b46c37b42e5711d` .. `feature/F-045-excel-obras-postventa`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | 68 |
| `services/dedicacion-api/infrastructure/excel/exporter.py` | 44 |
| **Total** | **112** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 28 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 678.3 s |
| SHA de HEAD medido | `ca221b50f74f93adcf190d5058bd52b32207110c` |
| Línea base (s) — `services/dedicacion-api` | 49.7 |
| Media por mutante evaluado (s) | 33.9 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | sí — 20 de 28 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/infrastructure/excel/contenido.py:84` [comparacion]

- Original: `if ln.es_postventa != postventa]`
- Mutado:   `if ln.es_postventa == postventa]`

#### Análisis (implementer, 2026-10-08)

> **Falso superviviente: no es un hueco ni un mutante equivalente.** Aplicado
> a mano (`__pycache__` borrado, `.venv/Scripts/python.exe -B -m pytest tests -q
> -p no:cacheprovider` desde `services/dedicacion-api`), la suite cae en al menos
> 8 tests de F-045 (r5, r6, r7 ×2, r8, r9, r12 ×2…): invertir el filtro manda
> las líneas propias a la agregada. En las dos campañas anteriores de esta
> ampliación, sobre el mismo HEAD y la misma semilla, el MISMO mutante salió
> **muerto**. Los supervivientes cambian de una ejecución a otra (campaña 1:
> `contenido.py:116`, `:118` y `exporter.py:110`; campaña 2: `exporter.py:110`;
> esta: `contenido.py:84`) y todos mueren a mano. Durante las campañas otros
> procesos importaban esta copia sin `PYTHONDONTWRITEBYTECODE`: la api local
> (`main.py`, arrancada a las 14:01:18, en mitad de la campaña 2) y algo que a
> las 14:20:13 compiló la app entera (`main.cpython-312.pyc`, `routes`, `deps`…)
> en mitad de esta. Causa exacta sin cerrar; va al encargo de `arnes-base` de
> falsos supervivientes (`5370838`). Decisión: sin test nuevo.
