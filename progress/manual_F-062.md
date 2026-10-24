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

## T20 · escritura en modo pruebas sobre la 0404 — EN CURSO

Comandos exactos en `progress/current.md`, «F-062 · T19 y T20». Ejecutada
por el humano en PowerShell, desde `services/dedicacion-transfer`, con el
`.venv` (modo comprobado: `True 0404`), recurso `1705036`, 2026-10-25.

### (1) C1 y C2 — CUMPLE

- Dry-run `ejecutar --ano 2026 --mes 10 --incidencia 1705036:CIV:5:9`: `ini CIV`
  el 20261005 y `fin CIZ` el 20261009 en PT26/00373 (0404); «DRY-RUN».
- Con `--confirmar`: `ini escribir hmores.ide=411883` (20261005) y `fin
  escribir hmores.ide=411884` (20261009); `RACHA inc=991001 abre · cierra el
  20261009 en el parte PT26/00373`.
- Con `--incidencia …:5:9 --incidencia …:12:16`: `ini ya_registrado 411883`,
  `fin editar hmores.ide=411884 fec=20261016 fec_antes=20261009`, la 991002
  `continua` (ini y fin, sin `ide`); **ningún inicio nuevo** (el 10 y el 11
  son sábado y domingo).
- `verificar`: `porcentajes:inc:991001:fin hmores.ide=411884 … fec=20261016
  cod=CIZ can=0.0 tot=0.0` (el **mismo** `ide`) e `…:ini 411883 fec=20261005 CIV`.
- `limpiar --confirmar`: 2 líneas `PRUEBA-PORC` (411883, 411884), borradas.
- **Observación (no bloquea):** la línea de resumen `escritas=0 editadas=0 …`
  sale a 0 aunque se escribieron y editaron incidencias: esos contadores son
  de las líneas de %; las incidencias se ven en las líneas `INCIDENCIA`.

### (2) C3 — CUMPLE

- Octubre, `--incidencia 1705036:CIV:27:31`: `ini escribir hmores.ide=411883`
  (20261027, PT26/00373) y `fin abierta` «llega a fin de mes: queda abierta
  (sin CIZ)»; `RACHA inc=991001 abre · queda abierta`.
- Noviembre, `--incidencia 1705036:CIV:2:6`: `ini continua` «continúa la racha
  CIV del 27/10 (parte PT26/00373, línea 411883)», **sin inicio nuevo**, y `fin
  escribir hmores.ide=411884` el 20261106 en **PT26/00371, el parte de
  noviembre** (`hmoide` 2854393, distinto del de octubre 2855815): R5 literal,
  el arreglo B1 de la review 1. El 1-nov es domingo: la racha se pega.
- `limpiar --confirmar`: 2 líneas (`porcentajes:inc:991001:ini`,
  `porcentajes:inc:991101:fin`), borradas.

### (3) C4 — CUMPLE

- Octubre, `--incidencia 1705036:CIV:27:31`: `ini escribir hmores.ide=411883`
  (20261027, PT26/00373), `fin abierta`.
- Noviembre, `--cierres 1705036`: `CIERRE recurso=1705036 CIV inicio=411883
  20261027 (PT26/00373) escribir fec=20261031 parte=PT26/00373
  hmores.ide=411884` «no sigue en 11/2026: CIZ el 31/10 en el parte
  PT26/00373», **sin `--pisar`** (inicio en M−1, R12; D17 no aplica).
  La línea testigo `reg=990201` sale `omitir` (porcentaje 0), como prevé el
  script (P3 la omite siempre).
- Repetir octubre: `ini` y `fin` `ya_registrado` (411883, 411884), aviso R11
  «no se deja abierta: el CIZ (línea 411884) ya está en el mes; va al último
  día»; nada nuevo. Repetir noviembre: `CIERRE … ya_registrado` «ya está
  cerrada el 31/10 (línea 411884)»; nada nuevo. Idempotente.
- `limpiar --confirmar`: 2 líneas (`…991001:ini` 20261027, `…991001:fin`
  20261031, las dos en el parte de octubre `hmoide` 2855815), borradas.

### (4) C12 y C13 (D17) — CUMPLE

- Septiembre, `--incidencia 1705036:CIV:15:30`: `ini escribir hmores.ide=411883`
  (20260915, PT26/00344), `fin abierta`.
- Octubre, `--incidencia 1705036:CIV:1:31`: `ini continua` «continúa la racha
  CIV del 15/09 (parte PT26/00344, línea 411883)» y `fin abierta`; nada escrito.
- Noviembre, `--cierres 1705036` **sin `--pisar`**: `PENDIENTE cierre:411883:
  relanza con --pisar cierre:411883` y `CIERRE … pendiente fec=20261031
  parte=PT26/00373 hmores.ide=None` «sin confirmar, no se escribe» (C13).
- Con `--pisar cierre:411883`: `CIERRE … escribir fec=20261031 parte=PT26/00373
  hmores.ide=411884` (C12): el `CIZ` en el parte de **octubre** (M−1) de la
  0404, no en el del inicio.
- `limpiar --confirmar`: 2 líneas (`…990901:ini` 20260915 `hmoide` 2850247;
  `…990901:fin` 20261031 `hmoide` 2855815), borradas.
- **Observación (no bloquea):** la línea `CIERRE` del preflight que imprime el
  script dice `escribir` sin decir que pedirá confirmación; solo la de
  `ejecutar` dice `pendiente`. El modal no tiene ese problema: pinta la casilla
  con `accion == "escribir" && requiere_confirmar` del preflight
  (`app.js:3003`). Mejora del script, si se quiere: imprimir
  `requiere_confirmar` y la `clave` también en el preflight.
