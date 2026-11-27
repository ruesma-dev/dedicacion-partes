<!-- progress/mutacion_F-078.md -->
# F-078 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-078 --workers 4` el 2026-11-27 16:01.

## Alcance

Origen del diff: **rama** (`b383f3c4bf963c3f98d1760ebcab296457dbcb74` .. `feature/F-078-registrar-por-paquetes`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 42 | 5 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 47 | 13 |
| **Total** | **89** | **18** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 18 |
| Mutantes evaluados | 9 |
| Muertos | 9 |
| Supervivientes | 0 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 630.7 s |
| SHA de HEAD medido | `b15042ab2943cfa06cba80cd4d6bd5a4f4ce3630` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_w9k_szwm/wk_0/services/dedicacion-api` | 123.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_w9k_szwm/wk_1/services/dedicacion-api` | 123.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_w9k_szwm/wk_2/services/dedicacion-api` | 123.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_w9k_szwm/wk_3/services/dedicacion-api` | 123.5 |
| Media por mutante evaluado (s) | 70.1 |
| Timeout efectivo por mutante (s) | 248 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Un mutante por línea | sí — 18 generados → 9 candidatos, uno por línea |
| Muestreo | no: campaña completa (9 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 98.8 (9 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

