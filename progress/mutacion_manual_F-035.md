# F-035 · Mutación manual de los `.ps1`

`python -m harness.mutacion` solo muta Python y para F-035 da **alcance vacío**
(lo de producción es PowerShell). Esta campaña la sustituye. Pedida por la
review 1 (`progress/review_F-035.md`, C4 bis): una fila por mutante, texto
exacto y número de fallos, reproducible.

- **Medida sobre** `301dfed` (ciclo 2, con `)` en la clase). Las líneas son las
  de ese commit.
- **Siempre sobre una copia**: el script copia `infra/` (sin `*.local.ps1`) y
  `tests/` a un directorio temporal, muta allí, pasa
  `tests/test_f035_secretos_sin_cmd.py` y `tests/test_f026_vaciado.py`
  **sin `-x`** y borra la copia. El árbol de trabajo no se toca (`git status`
  limpio después). Ningún `.ps1` se ejecuta.
- **Convención de las celdas**: `⏎` es un salto de línea CRLF y `\|` es `|`.
  El texto canónico es el de la lista `M` del script de abajo.

## Reproducir

Guardar el bloque del final como `mutacion_manual_f035.py` **fuera del repo**
(no hay ruta del repo segura para él: un `.py` fuera de `tests/`, `specs/`,
`progress/` o `docs/` entra en el alcance de producción de `harness/alcance.py`)
y, desde la raíz del repo:

```bash
PYTHONIOENCODING=utf-8 python <ruta>/mutacion_manual_f035.py            # tabla 1
PYTHONIOENCODING=utf-8 python <ruta>/mutacion_manual_f035.py b8189d3    # tabla 2
```

## 1 · Campaña final (tests de `301dfed`): 21 mutantes, 0 supervivientes

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| M1 sin borrar PGSSLMODE en finally | `vaciar_datos_prueba_dedicacion.ps1:171` | `        Remove-Item Env:PGSSLMODE -ErrorAction SilentlyContinue⏎` → (nada) | MUERTO | 1 | test_f035_r1_el_entorno_se_borra_en_el_finally |
| M2 sin borrar PGPASSWORD en finally | `vaciar_datos_prueba_dedicacion.ps1:170` | `        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue⏎` → (nada) | MUERTO | 1 | test_f035_r1_el_entorno_se_borra_en_el_finally |
| M3 PGSSLMODE tambien en local | `vaciar_datos_prueba_dedicacion.ps1:160` | `        $env:PGPASSWORD = $CLAVE⏎` → `        $env:PGPASSWORD = $CLAVE⏎        $env:PGSSLMODE = "require"⏎` | MUERTO | 1 | test_f035_r1_pgsslmode_require_solo_en_azure |
| M4 sin PGSSLMODE en Azure | `vaciar_datos_prueba_dedicacion.ps1:164` | `            $env:PGSSLMODE = "require"⏎` → (nada) | MUERTO | 2 | test_f035_r1_el_entorno_se_borra_en_el_finally, test_f035_r1_pgsslmode_require_solo_en_azure |
| M5 SoloRecuento sin return | `vaciar_datos_prueba_dedicacion.ps1:189` | `    return⏎}⏎⏎# --- 4)` → `}⏎⏎# --- 4)` | MUERTO | 1 | test_f035_r2_solo_recuento_sale_antes_del_vaciado |
| M6 salida solo sin -Confirmar | `vaciar_datos_prueba_dedicacion.ps1:112` | `if (-not $Confirmar -and -not $SoloRecuento) {` → `if (-not $Confirmar) {` | MUERTO | 2 | test_f026_r10_sin_confirmar_sale_antes_de_conectar, test_f035_r2_solo_recuento_conecta_sin_confirmar |
| M7 sin rechazo Confirmar+SoloRecuento | `vaciar_datos_prueba_dedicacion.ps1:69` | `if ($Confirmar -and $SoloRecuento) {` → `if ($false) {` | MUERTO | 1 | test_f035_r2_solo_recuento_y_confirmar_se_excluyen |
| M8 psql solo en local | `vaciar_datos_prueba_dedicacion.ps1:124` | `if (-not (Get-Command psql` → `if ($Local -and -not (Get-Command psql` | MUERTO | 1 | test_f035_r1_psql_en_el_path_en_ambos_modos |
| M9 vuelve az execute con -p | `vaciar_datos_prueba_dedicacion.ps1:165` | `$salida = psql -h $PG_FQDN -d $PG_DB -U $PG_APP_USER -v ON_ERROR_STOP=1 -c $sql` → `$salida = az postgres flexible-server execute -n $PG -u $PG_APP_USER -p $CLAVE -d $PG_DB --querytext $sql` | MUERTO | 6 | test_f026_r10_solo_en_la_base_dedicacion, test_f035_r1_azure_sin_contrasena_por_argumento_de_az, test_f035_r1_azure_usa_psql_contra_el_fqdn, test_f035_r1_fqdn_por_show_de_solo_lectura, test_f035_r1_pgsslmode_require_solo_en_azure, test_f035_r4_barrido_ningun_secreto_por_argumento_de_az_sin_control |
| M10 error Azure sin pista de IP | `vaciar_datos_prueba_dedicacion.ps1:175` | `lo mas probable es que tu IP no tenga acceso` → `lo mas probable es que algo falle` | MUERTO | 1 | test_f035_r3_el_error_de_azure_apunta_a_la_ip_propia |
| M11 crear_base sin control admin | `crear_base_dedicacion.ps1:117` | `Rechazar-CaracteresDeCmd $PGADMIN_PWD` → `# Rechazar-CaracteresDeCmd $PGADMIN_PWD` | MUERTO | 1 | test_f035_r4_el_control_va_antes_de_la_primera_az_con_el_secreto |
| M12 crear_base sin control app | `crear_base_dedicacion.ps1:124` | `Rechazar-CaracteresDeCmd $APP_PWD ` → `# Rechazar-CaracteresDeCmd $APP_PWD ` | MUERTO | 1 | test_f035_r4_el_control_va_antes_de_la_primera_az_con_el_secreto |
| M13 add_secrets sin control | `add_secrets_dedicacion.ps1:90` | `    Rechazar-CaracteresDeCmd $val` → `    # Rechazar-CaracteresDeCmd $val` | MUERTO | 1 | test_f035_r4_el_control_va_antes_de_la_primera_az_con_el_secreto |
| M14 clase sin % | `crear_base_dedicacion.ps1:53` | `'["&\|<>^%)]'` → `'["&\|<>^)]'` | MUERTO | 1 | test_f035_r4_el_control_rechaza_justo_los_caracteres_de_cmd |
| M15 clase sin comilla | `add_secrets_dedicacion.ps1:49` | `'["&\|<>^%)]'` → `'[&\|<>^%)]'` | MUERTO | 1 | test_f035_r4_el_control_rechaza_justo_los_caracteres_de_cmd |
| M16 control despues de az | `add_secrets_dedicacion.ps1:90` | `    Rechazar-CaracteresDeCmd $val "El valor de '$nombre'"⏎⏎    az keyvault secret set --vault-name $KV --name $nombre --value $val --only-show-errors \| Out-Null⏎` → `⏎    az keyvault secret set --vault-name $KV --name $nombre --value $val --only-show-errors \| Out-Null⏎    Rechazar-CaracteresDeCmd $val "El valor de '$nombre'"⏎` | MUERTO | 1 | test_f035_r4_el_control_va_antes_de_la_primera_az_con_el_secreto |
| M17 error de Azure sin firewall | `vaciar_datos_prueba_dedicacion.ps1:175` | `la regla de firewall de tu IP` → `la configuracion` | MUERTO | 1 | test_f035_r3_el_error_de_azure_apunta_a_la_ip_propia |
| M18 FQDN sin comprobar vacio | `vaciar_datos_prueba_dedicacion.ps1:131` | `    if ([string]::IsNullOrWhiteSpace($PG_FQDN)) {` → `    if ($false) {` | MUERTO | 1 | test_f035_r1_fqdn_por_show_de_solo_lectura |
| M19 rdbms-connect de vuelta | `vaciar_datos_prueba_dedicacion.ps1:128` | `    az account set --subscription $SUBSCRIPTION \| Out-Null⏎` → `    az account set --subscription $SUBSCRIPTION \| Out-Null⏎    az extension add --name rdbms-connect --upgrade --only-show-errors \| Out-Null⏎` | MUERTO | 3 | test_f035_r1_azure_sin_contrasena_por_argumento_de_az, test_f035_r1_cuenta_de_azure_y_nada_mas_de_az, test_f035_r1_fqdn_por_show_de_solo_lectura |
| M20 crear_base: clase sin ) | `crear_base_dedicacion.ps1:53` | `'["&\|<>^%)]'` → `'["&\|<>^%]'` | MUERTO | 1 | test_f035_r4_el_control_rechaza_justo_los_caracteres_de_cmd |
| M21 add_secrets: clase sin ) | `add_secrets_dedicacion.ps1:49` | `'["&\|<>^%)]'` → `'["&\|<>^%]'` | MUERTO | 1 | test_f035_r4_el_control_rechaza_justo_los_caracteres_de_cmd |

Salida: `supervivientes: 0 de 21`. M1–M19 son los de la campaña del ciclo 1
(misma lista que `mutps1.py`; M14 y M15 adaptados a la clase con `)`); M20 y
M21 son los nuevos del `)`. Ningún mutante es equivalente: todos cambian algo
observable (orden, condición, texto del mensaje o juego de caracteres).

## 2 · Primera pasada: M8 y M10 contra los tests de `b8189d3` (antes de T4)

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| M8 psql solo en local | `vaciar_datos_prueba_dedicacion.ps1:124` | `if (-not (Get-Command psql` → `if ($Local -and -not (Get-Command psql` | **SOBREVIVE** | 0 | - |
| M10 error Azure sin pista de IP | `vaciar_datos_prueba_dedicacion.ps1:175` | `lo mas probable es que tu IP no tenga acceso` → `lo mas probable es que algo falle` | **SOBREVIVE** | 0 | - |

Salida: `supervivientes: 2 de 2`. Los `.ps1` no cambiaron en esas líneas entre
`b8189d3` y `301dfed`: solo cambian los tests.

- **M8 — hueco real.** El test de «psql en el PATH en ambos modos» solo
  comprobaba que la línea estaba al nivel 0 de llaves; `if ($Local -and -not
  (Get-Command psql …` sigue a nivel 0 y deja Azure sin comprobación. Cerrado
  en `30c28c7`: el test exige la condición exacta, sin `$Local`.
- **M10 — casi equivalente.** El mensaje mutado seguía diciendo «revisa … la
  regla de firewall de tu IP», así que seguía apuntando a la IP; pero el test
  aceptaba cualquier `throw` con «IP» en cualquier parte del script. Cerrado en
  `30c28c7`: el test ancla el `throw` de la rama Azure de `Ejecutar-Sql` y
  exige «tu IP no tenga acceso» y «regla de firewall de tu IP» (M17 mata la
  segunda mitad).

## Script

```python
# mutacion_manual_f035.py (incrustado en progress/mutacion_manual_F-035.md)
# Mutacion manual de los .ps1 de F-035, SIEMPRE sobre una copia: copia infra/
# (sin *.local.ps1) y tests/ a un directorio temporal, aplica cada mutante en
# la copia, pasa los tests de F-035 y F-026 SIN -x (para contar los fallos) y
# restaura. El arbol de trabajo no se toca. Uso, desde la raiz del repo:
#     python mutacion_manual_f035.py            # M1-M21 con los tests de HEAD
#     python mutacion_manual_f035.py b8189d3    # M8 y M10 con los tests de esa
#                                               # revision (primera pasada)
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path.cwd()
V = "infra/vaciar_datos_prueba_dedicacion.ps1"
C = "infra/crear_base_dedicacion.ps1"
A = "infra/add_secrets_dedicacion.ps1"
N = "\r\n"
TESTS = ["tests/test_f035_secretos_sin_cmd.py", "tests/test_f026_vaciado.py"]
CLASE = "'[\"&|<>^%)]'"
M = [
    ("M1", "sin borrar PGSSLMODE en finally", V,
     "        Remove-Item Env:PGSSLMODE -ErrorAction SilentlyContinue" + N, ""),
    ("M2", "sin borrar PGPASSWORD en finally", V,
     "        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue" + N, ""),
    ("M3", "PGSSLMODE tambien en local", V,
     "        $env:PGPASSWORD = $CLAVE" + N,
     "        $env:PGPASSWORD = $CLAVE" + N + '        $env:PGSSLMODE = "require"' + N),
    ("M4", "sin PGSSLMODE en Azure", V, '            $env:PGSSLMODE = "require"' + N, ""),
    ("M5", "SoloRecuento sin return", V,
     "    return" + N + "}" + N + N + "# --- 4)", "}" + N + N + "# --- 4)"),
    ("M6", "salida solo sin -Confirmar", V,
     "if (-not $Confirmar -and -not $SoloRecuento) {", "if (-not $Confirmar) {"),
    ("M7", "sin rechazo Confirmar+SoloRecuento", V,
     "if ($Confirmar -and $SoloRecuento) {", "if ($false) {"),
    ("M8", "psql solo en local", V,
     "if (-not (Get-Command psql", "if ($Local -and -not (Get-Command psql"),
    ("M9", "vuelve az execute con -p", V,
     "$salida = psql -h $PG_FQDN -d $PG_DB -U $PG_APP_USER -v ON_ERROR_STOP=1 -c $sql",
     "$salida = az postgres flexible-server execute -n $PG -u $PG_APP_USER -p $CLAVE"
     " -d $PG_DB --querytext $sql"),
    ("M10", "error Azure sin pista de IP", V,
     "lo mas probable es que tu IP no tenga acceso", "lo mas probable es que algo falle"),
    ("M11", "crear_base sin control admin", C,
     "Rechazar-CaracteresDeCmd $PGADMIN_PWD", "# Rechazar-CaracteresDeCmd $PGADMIN_PWD"),
    ("M12", "crear_base sin control app", C,
     "Rechazar-CaracteresDeCmd $APP_PWD ", "# Rechazar-CaracteresDeCmd $APP_PWD "),
    ("M13", "add_secrets sin control", A,
     "    Rechazar-CaracteresDeCmd $val", "    # Rechazar-CaracteresDeCmd $val"),
    ("M14", "clase sin %", C, CLASE, CLASE.replace("%", "")),
    ("M15", "clase sin comilla", A, CLASE, CLASE.replace('"', "")),
    ("M16", "control despues de az", A,
     "    Rechazar-CaracteresDeCmd $val \"El valor de '$nombre'\"" + N + N
     + "    az keyvault secret set --vault-name $KV --name $nombre --value $val"
       " --only-show-errors | Out-Null" + N,
     N + "    az keyvault secret set --vault-name $KV --name $nombre --value $val"
         " --only-show-errors | Out-Null" + N
     + "    Rechazar-CaracteresDeCmd $val \"El valor de '$nombre'\"" + N),
    ("M17", "error de Azure sin firewall", V,
     "la regla de firewall de tu IP", "la configuracion"),
    ("M18", "FQDN sin comprobar vacio", V,
     "    if ([string]::IsNullOrWhiteSpace($PG_FQDN)) {", "    if ($false) {"),
    ("M19", "rdbms-connect de vuelta", V,
     "    az account set --subscription $SUBSCRIPTION | Out-Null" + N,
     "    az account set --subscription $SUBSCRIPTION | Out-Null" + N
     + "    az extension add --name rdbms-connect --upgrade --only-show-errors | Out-Null" + N),
    ("M20", "crear_base: clase sin )", C, CLASE, CLASE.replace(")", "")),
    ("M21", "add_secrets: clase sin )", A, CLASE, CLASE.replace(")", "")),
]


def copia(destino: Path, revision_tests: str | None) -> None:
    def ignorar(_dir, nombres):
        return [n for n in nombres if n.endswith(".local.ps1") or n == "__pycache__"]
    shutil.copytree(RAIZ / "infra", destino / "infra", ignore=ignorar)
    shutil.copytree(RAIZ / "tests", destino / "tests", ignore=ignorar)
    if revision_tests:
        for t in TESTS:
            texto = subprocess.run(["git", "show", f"{revision_tests}:{t}"], cwd=RAIZ,
                                   capture_output=True, check=True).stdout
            (destino / t).write_bytes(texto)


def celda(texto: str) -> str:
    return "`" + texto.replace(N, "⏎").replace("|", "\\|") + "`" if texto else "(nada)"


def main() -> None:
    revision = sys.argv[1] if len(sys.argv) > 1 else None
    elegidos = [m for m in M if m[0] in ("M8", "M10")] if revision else M
    destino = Path(tempfile.mkdtemp(prefix="mutacion_f035_"))
    try:
        copia(destino, revision)
        vivos = 0
        for ident, nombre, ruta, de, a in elegidos:
            fichero = destino / ruta
            original = fichero.read_bytes()
            texto = original.decode("utf-8-sig")
            if texto.count(de) != 1:
                print(f"| {ident} | {ruta} | PATRON {texto.count(de)} VECES: revisar |")
                vivos += 1
                continue
            linea = texto[: texto.index(de)].count("\n") + 1
            fichero.write_bytes(b"\xef\xbb\xbf" + texto.replace(de, a, 1).encode("ascii"))
            try:
                r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                    *TESTS], cwd=destino, capture_output=True, text=True)
            finally:
                fichero.write_bytes(original)
            fallos = re.search(r"(\d+) failed", r.stdout)
            n = int(fallos.group(1)) if fallos else 0
            tests = sorted({ln.split("::")[1].split(" ")[0].split("[")[0]
                            for ln in r.stdout.splitlines() if ln.startswith("FAILED")})
            if r.returncode == 0:
                vivos += 1
            estado = "MUERTO" if r.returncode != 0 else "**SOBREVIVE**"
            print(f"| {ident} {nombre} | `{Path(ruta).name}:{linea}` | {celda(de)} → {celda(a)}"
                  f" | {estado} | {n} | {', '.join(tests) or '-'} |")
        print(f"\nsupervivientes: {vivos} de {len(elegidos)}  (copia en {destino.name}, borrada)")
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    main()
```
