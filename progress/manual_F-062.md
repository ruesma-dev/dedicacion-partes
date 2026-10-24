<!-- progress/manual_F-062.md -->
# F-062 · verificaciones MANUAL (humano)

## T19 · medir el preflight (solo lectura, R20) — HECHA el 2026-10-25

Ejecutada por el humano en PowerShell, desde `services/dedicacion-transfer`,
con el `.venv` del transfer. Salida pegada en el chat; aquí, lo esencial.

Primer paso: `.venv/Scripts/python -c "from config.settings import get_settings as g; s=g(); print(s.obra_pruebas_forzar, s.obra_pruebas_cod)"`
⇒ `True 0404`.

| Copia | Comando | Lecturas | Leyendo | **Total** |
|---|---|---|---|---|
| `dev` (`91648df`) | `medir --lote --ano 2026 --mes 9 --obra 0694 --obra 0696 --recurso 1705036` | 11 | 46.69 s | **18.25 s** |
| rama (`1de1de5`) | lo mismo `--cierres 1705036` | 12 | 24.54 s | **10.49 s** |

- **Una** línea `lectura incidencias_en_ventana: 0 filas · 0.99 s` en el
  lote de la rama (R20: una lectura más que en `dev`). Cumple.
- Total de la rama ≤ 1,15 × el de `dev`: 10.49 s frente a 18.25 s. Cumple,
  pero la diferencia es ruido de red (la de `dev` corrió primero, con
  lecturas en frío de 6-10 s); el dato que vale es que la lectura nueva
  cuesta ~1 s y va en paralelo en la ronda C.
- **Límite de la medida:** en modo pruebas la lectura en ventana filtra por
  la obra 0404 (`#regla-incidencia`, O3 de la review 1), y ahí no hay
  incidencias de ese recurso: 0 filas. En modo real lee las `CI*`/`CIZ` del
  recurso en todas las obras de 12 meses más el siguiente; por la evidencia
  de Sigrid (`explore_F-062_sigrid.md`, 1.895 líneas `CI*` de mensuales
  desde 2025) son decenas de filas por recurso, no miles.

## T20 · escritura en modo pruebas sobre la 0404 — PENDIENTE

Comandos exactos en `progress/current.md`, «F-062 · T19 y T20».
