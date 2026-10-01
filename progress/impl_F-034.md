# F-034 · Informe del implementer — BLOQUEADA

## Motivo del bloqueo (leer primero)

La **lista cerrada de `design.md` §6** no coincide con lo que la regla nueva
(R1, R3) hace con los fixtures de F-024. Hay asserts que tienen que cambiar
y que la lista no recoge, y **uno que la spec dice expresamente que no cambia
y sí cambia** (R17). La consigna del líder era: «cualquier otro cambio de
assert, para y responde `blocked`». Paro antes de escribir nada.

**Estado del árbol:** limpio, sin commits de F-034 del implementer. Ninguna
tarea marcada. El ensayo se hizo en el árbol de trabajo y se revirtió con
`git checkout -- services/dedicacion-api` (`git status` limpio salvo
`.claude/worktrees/`, que no es mío: es el worktree de F-026).

### Cómo se detectó

Ensayo en seco: apliqué en el árbol de trabajo exactamente los cambios de
producción de design §3-§4 (`FiltroEmpresa.empresa_obras`,
`visible_en_empresa(empresa_trabajador, filtro)`, obras por
`filtro.empresa_obras`, `_payloads` sin `empresas_de` y con
`"empresa": filtro.empresa_obras`, `routes._filtro` y
`a_trabajador_out(…, filtro.empresa_obras)` en las cuatro rutas) más el
`_f` de `test_f024_cuadrante_empresa.py` con `empresa_obras=DEF` (cambio que
la spec sí autoriza), y lancé la suite de la API con su venv:

```
cd services/dedicacion-api && .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider \
  tests/test_f024_cuadrante_empresa.py tests/test_f024_registro_empresa.py tests/test_f024_rutas_empresa.py
30 failed, 59 passed, 1 warning in 13.87s
```

Las 30 caídas, clasificadas contra §6:

### A. Previstas por §6 (sin problema)

| Test | Cambio |
|---|---|
| `cuadrante::test_f024_r7_…[1]`, `[28]` | NULL: Carlos y Gil salen de la 28 y entran en la 1 |
| `cuadrante::test_f024_r9_…[28]`, `[18]` | pasa a `test_f034_r1_…` (`[100, 101, 102]`) |
| `cuadrante::test_f024_r13_…` (×4) | resúmenes por los NULL |
| `registro::test_f024_r16_…` (×6) | pasa a `test_f034_r7_…` con los valores de §6 |
| `rutas::test_f024_r6_sin_empresa_la_por_defecto` | nombres NULL |
| `rutas::test_f024_r11_otra_empresa_depende_de_la_elegida` | pasa a `test_f034_r5_…` |
| `rutas::test_f024_r15_…` (×2) | nombres NULL |

(R14 de cuadrante y de rutas, R18 y R19 de registro siguen en verde sin
tocarlos, como dice §6.)

### B. NO previstas por §6 — requieren decisión

1. **`test_f024_registro_empresa.py::test_f024_r17_obra_de_otra_empresa_se_manda_y_su_omision_se_traza`**
   — §6 dice «R17 no cambia de valores (ya era E = 1)». **Falso**: con R3 el
   trabajador 12 (NULL, carga en la obra 9 de la 28) pasa a verse en la 1,
   así que la obra 9 lleva dos líneas.
   ```
   E       assert [(2, 1), (4, 1)] == [(2, 1)]
   ```
   Assert viejo `[(2, 1)]` → nuevo `[(2, 1), (4, 1)]`. El resto del test
   (traza de la omitida 2 con su motivo) no cambia.
   *Alternativa sin tocar el assert de valores:* que el test filtre el
   payload a `registro_id == 2`, o quitar la fila 4 del fixture de ese test;
   ambas son también cambios de test no previstos.

2. **`test_f024_cuadrante_empresa.py::test_f024_r10_puede_deshacer_se_conserva`**
   — no está en §6 (que solo nombra R7, R13 y R14 en ese fichero). Con E = 1
   ahora hay cinco filas (entra Carlos, NULL):
   ```
   E       assert [True, False,... False, False] == [True, False, False, False]
   ```
   Assert viejo `[True, False, False, False]` → nuevo
   `[True, False, False, False, False]`. Es la misma consecuencia de R3 que §6
   describe para R7, pero el test no está en la lista.

3. **`test_f024_rutas_empresa.py::test_f024_r6_con_empresa_la_elegida`**
   (E = 28) — §6 dice que en R6 «cambian solo [las listas de nombres] en los
   NULL». Cambian **tres** asserts:
   - nombres `["Bea", "Carlos", "Gil"]` → `["Bea"]` (NULL, previsto);
   - **obras `[900]` → `[100, 101, 102]`** (consecuencia directa de R1, no
     prevista para este test);
   - **`resumen.total` `3` → `1`** (consecuencia de los NULL; no es una lista
     de nombres).

4. **`test_f024_rutas_empresa.py::test_f024_r6_r13_respuestas_por_fila_con_el_resumen_de_la_empresa`**
   (×9) — parámetros `(None, 4), (1, 4), (28, 3)` → `(None, 5), (1, 5), (28, 1)`.
   Es un **contador** del resumen, no una lista de nombres; §6 habla de «las
   listas de nombres por empresa de R6/R13/R15». Probablemente cubierto por
   el espíritu, pero no por la letra.

### Qué pido al líder

Confirmar (o corregir) los cambios de B1-B4 con estos valores nuevos, para
que la lista cerrada de §6 quede completa. Con eso la implementación es
directa: el ensayo demuestra que el código de §3-§4 basta y que ningún otro
test de la API (276 restantes) se ve afectado. F-022 (`test_f022_empresa_en_linea.py`)
sigue en verde sin tocarlo, como prevé §6.

Sugerencia de redacción para §6 (para que el spec-author o el líder la
adopten si están de acuerdo):

> - `test_f024_cuadrante_empresa.py`: … En R7, **R10 (`puede_deshacer`)**,
>   R13 y R14 cambian solo los casos de trabajadores NULL …
> - `test_f024_registro_empresa.py`: … **R17 añade la línea 4 a la obra 9
>   (`[(2, 1), (4, 1)]`)**: el trabajador 12, NULL, pasa a verse en la 1; la
>   traza de la omitida 2 no cambia.
> - `test_f024_rutas_empresa.py`: … En R6 con E = 28, **las obras pasan a
>   `[100, 101, 102]` (R1)** y los nombres y **los totales del resumen** de
>   R6/R13/R15 cambian solo por los NULL (`4 → 5` con la 1, `3 → 1` con la 28).

## Entorno

- Rama verificada: `feature/F-034-obras-siempre-ruesma`.
- `bash harness/init.sh`: la **primera** ejecución salió en rojo en
  `compileall` por `PermissionError: [WinError 5] Acceso denegado` al
  renombrar `.pyc` dentro de `.claude/worktrees/agent-a2f02d376189d33db/`
  (el worktree de F-026, compilando a la vez desde otra sesión: carrera de
  ficheros, no error de sintaxis). La **segunda**, sin cambiar nada, salió
  en verde: `ENTORNO LISTO`, 355 passed, 1 skipped. Aviso para el líder:
  mientras ese worktree viva dentro del árbol, `compileall` de `init.sh`
  puede dar falsos rojos intermitentes.
- Tras revertir el ensayo el árbol queda como lo encontré (sin cambios en
  ficheros versionados).

## Tareas

Ninguna iniciada. T1-T11 pendientes.

## Evidencias

No aplica todavía: no hay código de F-034. Tests ejecutados en el ensayo
(revertido): 89 de los tres ficheros F-024 afectados → 30 fallos, todos
listados arriba (A previstos, B no previstos).
