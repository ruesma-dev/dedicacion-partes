<!-- progress/mutacion_F-057.md -->
# F-057 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-057` el 2026-10-19 13:54.

## Alcance

Origen del diff: **rama** (`41d2885ab1167f0e06142f267fb1deb9e64730b2` .. `feature/F-057-buscando-solo-pendientes`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/propuestas_mes.py` | 40 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 27 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 23 |
| **Total** | **90** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 11 |
| Mutantes evaluados | 11 |
| Muertos | 10 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 407.2 s |
| SHA de HEAD medido | `1258c98e11921effc8f56eccaa0652d34ac1c4d8` |
| Línea base (s) — `services/dedicacion-api` | 51.9 |
| Media por mutante evaluado (s) | 37.0 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/interface_adapters/api/schemas.py:97` [booleano]

- Original: `propuesta_pendiente: bool = False`
- Mutado:   `propuesta_pendiente: bool = True`

#### Análisis (implementer)

> Por qué ningún test lo caza: el valor por defecto nunca se usa. El único
> sitio que construye `LineaOut` en producción es `a_trabajador_out`
> (`schemas.py`, `LineaOut(` aparece una sola vez fuera de los tests: `grep -rn
> "LineaOut(" services/dedicacion-api --include=*.py`), y SIEMPRE pasa
> `propuesta_pendiente=` explícito, calculado contra las pendientes de la cola.
> Ningún camino crea la línea con el defecto.
> Decisión: **mutante equivalente**. Se deja el defecto `False` igual que los
> demás campos opcionales de `LineaOut` (`propuesta_cod = None`, …): si mañana
> otro sitio construye la línea sin decirlo, lo seguro es «no pendiente»
> («automática»), no «buscando partida…» para siempre.

## Campaña paralela descartada (defecto de la herramienta, para el líder)

La primera campaña se lanzó con los workers por defecto (**4**, mismo HEAD
`1258c98`): 11 mutantes, 6 muertos, **5 supervivientes**, 317,3 s. Cuatro de
esos supervivientes (`propuestas_mes.py:73` `==`→`!=`, `:113` `[0]`→`[1]`,
`:127` y `routes.py:93` `False`→`True`) eran los mutantes 5-8, la SEGUNDA
tanda de los cuatro workers, y son **falsos**: reproducido a mano el de
`propuestas_mes.py:73` en un `git worktree --detach` aparte, 7 tests fallan
(entre ellos `test_f055_r30_en_curso_mientras_quede_alguna_y_no_se_reencola`).
Esta campaña EN SERIE (`--workers 1`) los da los cuatro por muertos. Vale esta;
la paralela se descarta (copia en el scratchpad del implementer, no
versionada). Indica que `harness/mutacion_paralela.py` puede juzgar una
tanda contra código sin mutar: a revisar en el arnés (y en `arnes-base`).

