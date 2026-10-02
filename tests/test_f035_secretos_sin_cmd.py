# tests/test_f035_secretos_sin_cmd.py
"""F-035 · Ningun secreto pasa por la linea de comandos de `cmd.exe`.

En Windows `az` es un `.cmd`: su linea de comandos la interpreta `cmd.exe`,
que se come o reinterpreta `" & | < > ^ %`. En el despliegue del 2026-10-02 el
vaciado contra Azure fallo con «password authentication failed» por eso: la
contrasena le llegaba a PostgreSQL corrompida. Criterios `acceptance` de F-035
en `harness/features.json` (sin spec: rigor estandar, sdd false).

  - **R1**: el vaciado contra Azure usa `psql` (un `.exe`, sin `cmd.exe`) con
    `PGPASSWORD` y `PGSSLMODE=require` en el entorno solo durante la llamada,
    borrados en el `finally`; el FQDN sale de `az ... show` (solo lectura); sin
    `rdbms-connect` ni `az ... execute`.
  - **R2**: `-SoloRecuento` pide la contrasena, cuenta y sale SIN la sentencia
    de vaciado, en local y en Azure.
  - **R3**: si `psql` no conecta con Azure, el mensaje apunta a la regla de
    acceso de la IP propia, sin tocar nada del servidor.
  - **R4**: `crear_base` y `add_secrets` rechazan, ANTES de la primera llamada
    a `az` que lleva el secreto, los caracteres que interpreta `cmd.exe`.
  - **R5**: la revision del resto de `infra/` queda escrita en su README.

Los scripts NO se ejecutan: se leen como texto. Ni red, ni BBDD, ni `az`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INFRA = RAIZ / "infra"
VACIAR = INFRA / "vaciar_datos_prueba_dedicacion.ps1"
CREAR_BASE = INFRA / "crear_base_dedicacion.ps1"
ADD_SECRETS = INFRA / "add_secrets_dedicacion.ps1"

#: Lo que `cmd.exe` interpreta dentro de la linea de un `.cmd`.
CARACTERES_CMD = ('"', "&", "|", "<", ">", "^", "%")


def _texto(script: Path) -> str:
    return script.read_bytes().decode("utf-8-sig")


def _codigo(script: Path, impresiones: bool = False) -> list[str]:
    """Lineas de codigo: sin comentarios ni vacias; sin las que solo imprimen,
    salvo que `impresiones` las pida (`Write-Host (Ejecutar-Sql ...)` ejecuta)."""
    lineas = []
    for linea in _texto(script).splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        if limpia.startswith("Write-Host") and not impresiones:
            continue
        lineas.append(limpia)
    return lineas


def _primera(patron: str, lineas: list[str], desde: int = 0) -> int:
    for i in range(desde, len(lineas)):
        if re.search(patron, lineas[i]):
            return i
    return len(lineas)


def _llaves(linea: str, primera: bool) -> int:
    """Saldo de llaves; en la linea que abre, sin el `}` que cierra el anterior
    (`} finally {`, `} else {`)."""
    if primera:
        linea = re.sub(r"^\}\s*", "", linea)
    return linea.count("{") - linea.count("}")


def _bloque(lineas: list[str], inicio: int) -> list[str]:
    """Las lineas del bloque `{ ... }` que abre `lineas[inicio]`, sin ella."""
    nivel, cuerpo = 0, []
    for i, linea in enumerate(lineas[inicio:]):
        if nivel >= 1:
            cuerpo.append(linea)
        nivel += _llaves(linea, i == 0)
        if nivel == 0:
            break
    return cuerpo


def _primer_nivel(lineas: list[str], inicio: int) -> list[str]:
    """Las lineas del primer nivel del bloque que abre `lineas[inicio]`."""
    nivel, directas = 0, []
    for i, linea in enumerate(lineas[inicio:]):
        if nivel == 1:
            directas.append(linea)
        nivel += _llaves(linea, i == 0)
        if nivel == 0:
            break
    return directas


def _nivel(lineas: list[str], indice: int) -> int:
    """Profundidad de llaves a la que esta `lineas[indice]`."""
    return sum(ln.count("{") - ln.count("}") for ln in lineas[:indice])


def _funcion_ejecutar_sql() -> list[str]:
    codigo = _codigo(VACIAR)
    inicio = _primera(r"^function Ejecutar-Sql\b", codigo)
    assert inicio < len(codigo), "falta la funcion Ejecutar-Sql"
    return _bloque(codigo, inicio)


# --- R1 · El vaciado contra Azure, con psql --------------------------------


def test_f035_r1_azure_sin_contrasena_por_argumento_de_az() -> None:
    texto = _texto(VACIAR)
    assert "flexible-server execute" not in texto
    assert "rdbms-connect" not in texto
    assert not re.search(r"(?<![\w-])-p\s+\$", texto)
    assert "--querytext" not in texto


def test_f035_r1_azure_usa_psql_contra_el_fqdn() -> None:
    psql = [ln for ln in _funcion_ejecutar_sql() if re.search(r"\bpsql\s+-h\b", ln)]
    azure = [ln for ln in psql if "-h $PG_FQDN" in ln]
    assert len(azure) == 1, psql
    assert ("-h $PG_FQDN -d $PG_DB -U $PG_APP_USER -v ON_ERROR_STOP=1 -c $sql"
            in azure[0])


def test_f035_r1_fqdn_por_show_de_solo_lectura() -> None:
    codigo = _codigo(VACIAR)
    llamadas = [ln for ln in codigo if re.search(r"(^|[=(]\s*)az\s", ln)]
    assert llamadas, "el script no llama a az"
    for llamada in llamadas:
        assert re.search(r"\baz (account set|postgres flexible-server show) ",
                         llamada), llamada
    show = [ln for ln in llamadas if "flexible-server show" in ln]
    assert len(show) == 1
    assert re.search(r"^\$PG_FQDN\s*=\s*az postgres flexible-server show -n \$PG "
                     r"-g \$PG_RG --query \"?fullyQualifiedDomainName\"? -o tsv",
                     show[0]), show[0]
    # Y si no aparece, se para antes de pedir nada.
    i = codigo.index(show[0])
    assert re.search(r"IsNullOrWhiteSpace\(\$PG_FQDN\)", codigo[i + 1]), codigo[i + 1]


def test_f035_r1_psql_en_el_path_en_ambos_modos() -> None:
    codigo = _codigo(VACIAR)
    comprobacion = _primera(r"Get-Command psql\b", codigo)
    assert comprobacion < len(codigo), "falta la comprobacion de psql"
    # Al primer nivel del script y sin condicion de modo: ni colgada de un
    # `if ($Local)` ni con `$Local` en su propia condicion.
    assert _nivel(codigo, comprobacion) == 0, codigo[comprobacion]
    assert re.match(r"^if \(-not \(Get-Command psql -ErrorAction SilentlyContinue\)\) \{$",
                    codigo[comprobacion]), codigo[comprobacion]
    assert comprobacion < _primera(r"Read-Host", codigo)


def test_f035_r1_pgsslmode_require_solo_en_azure() -> None:
    cuerpo = _funcion_ejecutar_sql()
    local = _primera(r"\bpsql -h localhost\b", cuerpo)
    ssl = _primera(r'^\$env:PGSSLMODE\s*=\s*"require"$', cuerpo)
    azure = _primera(r"\bpsql -h \$PG_FQDN\b", cuerpo)
    assert local < ssl < azure < len(cuerpo), (local, ssl, azure)
    # Entre la rama local y la de Azure esta el `else` que las separa.
    assert any(re.match(r"^\}\s*else\s*\{$", ln) for ln in cuerpo[local:ssl])


def test_f035_r1_el_entorno_se_borra_en_el_finally() -> None:
    cuerpo = _funcion_ejecutar_sql()
    intento = _primera(r"^try\s*\{$", cuerpo)
    remate = _primera(r"^\}\s*finally\s*\{$", cuerpo)
    assert intento < remate < len(cuerpo)
    # Se ponen DENTRO del try, para que el finally los alcance siempre.
    for variable in ("PGPASSWORD", "PGSSLMODE"):
        puesta = _primera(r"^\$env:" + variable + r"\s*=", cuerpo)
        assert intento < puesta < remate, variable
    final = _bloque(cuerpo, remate)
    for variable in ("PGPASSWORD", "PGSSLMODE"):
        assert any(re.match(r"^Remove-Item Env:" + variable + r"\b", ln)
                   for ln in final), (variable, final)


def test_f035_r1_cuenta_de_azure_y_nada_mas_de_az() -> None:
    texto = _texto(VACIAR)
    assert "az account set --subscription $SUBSCRIPTION" in texto
    assert "az extension" not in texto


# --- R2 · -SoloRecuento -----------------------------------------------------


def test_f035_r2_parametro_solo_recuento() -> None:
    assert re.search(r"param\((?:(?!\n\)).)*\[switch\]\s*\$SoloRecuento\b",
                     _texto(VACIAR), re.DOTALL)


def test_f035_r2_solo_recuento_conecta_sin_confirmar() -> None:
    """Es de solo lectura: no necesita -Confirmar. Sin ninguno, no conecta."""
    codigo = _codigo(VACIAR)
    salida = _primera(r"^if \(-not \$Confirmar -and -not \$SoloRecuento\) \{$",
                      codigo)
    assert salida < len(codigo), "falta la salida sin -Confirmar ni -SoloRecuento"
    assert "return" in _primer_nivel(codigo, salida)


def test_f035_r2_solo_recuento_y_confirmar_se_excluyen() -> None:
    codigo = _codigo(VACIAR)
    choque = _primera(r"^if \(\$Confirmar -and \$SoloRecuento\)", codigo)
    assert choque < len(codigo), "falta el rechazo de -Confirmar con -SoloRecuento"
    assert "throw" in codigo[choque] or any(
        ln.startswith("throw") for ln in _primer_nivel(codigo, choque))
    assert choque < _primera(r"\baz\s|\bpsql\b|Read-Host", codigo)


def test_f035_r2_solo_recuento_sale_antes_del_vaciado() -> None:
    codigo = _codigo(VACIAR, impresiones=True)
    recuento = _primera(r"Ejecutar-Sql \$RECUENTO", codigo)
    salida = _primera(r"^if \(\$SoloRecuento\) \{$", codigo, recuento)
    vaciado = _primera(r"Ejecutar-Sql \$SENTENCIA", codigo)
    assert recuento < salida < vaciado < len(codigo), (recuento, salida, vaciado)
    assert _nivel(codigo, salida) == 0
    assert "return" in _primer_nivel(codigo, salida)


def test_f035_r2_el_plan_explica_solo_recuento() -> None:
    texto = _texto(VACIAR)
    impresas = [ln for ln in texto.splitlines() if "Write-Host" in ln]
    assert any("-SoloRecuento" in ln for ln in impresas)
    # Y la cabecera dice como usarlo, en local y en Azure.
    cabecera = texto.split("param(")[0]
    assert re.search(r"vaciar_datos_prueba_dedicacion\.ps1 -SoloRecuento", cabecera)
    assert re.search(r"vaciar_datos_prueba_dedicacion\.ps1 -Local -SoloRecuento",
                     cabecera)


# --- R3 · Si no conecta, la regla de acceso de la IP propia ----------------


def test_f035_r3_el_error_de_azure_apunta_a_la_ip_propia() -> None:
    # El `throw` de Azure es el que sigue al de la rama local en Ejecutar-Sql.
    cuerpo = _funcion_ejecutar_sql()
    local = _primera(r'^if \(\$Local\) \{ throw "Fallo ejecutando SQL', cuerpo)
    azure = _primera(r'^throw "Fallo ejecutando SQL', cuerpo, local + 1)
    assert local < azure < len(cuerpo), (local, azure)
    mensaje = cuerpo[azure]
    assert "tu IP no tenga acceso" in mensaje, mensaje
    assert re.search(r"regla de firewall de tu IP", mensaje), mensaje
    assert re.search(r"NO (la )?(crea|toca)", mensaje), mensaje
    assert "IP" not in cuerpo[local]


def test_f035_r3_sin_tocar_nada_del_servidor() -> None:
    texto = _texto(VACIAR)
    assert not re.search(r"firewall-rule", texto, re.IGNORECASE)
    assert not re.search(r"flexible-server\s+(update|restart|db|parameter)", texto)
    assert "PG_ADMIN" not in texto


# --- R4 · Control de caracteres antes de la primera az con el secreto ------

#: Script -> (variable del secreto, patron de la primera linea de codigo que
#: lo lleva a una llamada de `az`, directa o a traves de otra variable).
CONTROLADOS = {
    CREAR_BASE: [
        ("PGADMIN_PWD", r"-p \$PGADMIN_PWD\b"),
        ("APP_PWD", r"^\$APP_PWD_SQL\s*="),
    ],
    ADD_SECRETS: [
        ("val", r"--value \$val\b"),
    ],
}

#: Nombre de la funcion de control en los dos scripts.
CONTROL = "Rechazar-CaracteresDeCmd"


def _clase_de_caracteres(script: Path) -> str:
    """La clase `[...]` del `-match` dentro de la funcion de control."""
    codigo = _codigo(script)
    inicio = _primera(r"^function " + CONTROL + r"\b", codigo)
    assert inicio < len(codigo), f"falta la funcion {CONTROL} en {script.name}"
    cuerpo = "\n".join(_bloque(codigo, inicio))
    hallado = re.search(r"-match\s+'(\[[^']+\])'", cuerpo)
    assert hallado, cuerpo
    assert re.search(r"^\s*throw\b", cuerpo, re.MULTILINE), cuerpo
    return hallado.group(1)


@pytest.mark.parametrize("script", [CREAR_BASE, ADD_SECRETS], ids=lambda s: s.stem)
def test_f035_r4_el_control_rechaza_justo_los_caracteres_de_cmd(script: Path) -> None:
    # La clase de PowerShell, evaluada con el motor de Python: mismos
    # caracteres, misma semantica para estos siete.
    clase = re.compile(_clase_de_caracteres(script))
    for caracter in CARACTERES_CMD:
        assert clase.search("abc" + caracter + "123"), caracter
    for valido in ("Abc123", "a.b-c_d~e", "x!y?z*", "comilla'simple", "a=b+c/d", "es pacio"):
        assert not clase.search(valido), valido


@pytest.mark.parametrize("script", [CREAR_BASE, ADD_SECRETS], ids=lambda s: s.stem)
def test_f035_r4_el_mensaje_dice_que_caracteres_y_por_que(script: Path) -> None:
    codigo = _codigo(script)
    inicio = _primera(r"^function " + CONTROL + r"\b", codigo)
    cuerpo = "\n".join(_bloque(codigo, inicio))
    assert "cmd.exe" in cuerpo
    assert '" & | < > ^ %' in cuerpo.replace('`"', '"')
    # Y no imprime el valor rechazado.
    assert "$clave" not in cuerpo.split("throw", 1)[1]


@pytest.mark.parametrize(
    ("script", "variable", "uso"),
    [(s, v, u) for s, pares in CONTROLADOS.items() for v, u in pares],
    ids=lambda x: x.stem if isinstance(x, Path) else str(x)[:12],
)
def test_f035_r4_el_control_va_antes_de_la_primera_az_con_el_secreto(
        script: Path, variable: str, uso: str) -> None:
    codigo = _codigo(script)
    lectura = _primera(r"^\$" + variable + r"\s*=\s*\[System\.Net\.NetworkCredential\]",
                       codigo)
    control = _primera(r"^" + CONTROL + r"\s+\$" + variable + r"\b", codigo)
    primera_az = _primera(uso, codigo)
    assert lectura < control < primera_az < len(codigo), (lectura, control, primera_az)


def test_f035_r4_barrido_ningun_secreto_por_argumento_de_az_sin_control() -> None:
    """Todo `-p $x` / `--value $x` / `--password $x` de `infra/*.ps1`.

    Solo se admiten los que pasan por el control (crear_base, add_secrets) y
    el client secret de `setup_front_easyauth.ps1`, que lo genera Azure con
    un juego de caracteres sin ninguno de los de cmd.exe (R5).
    """
    admitidos = {
        ("crear_base_dedicacion.ps1", "PGADMIN_PWD"),
        ("add_secrets_dedicacion.ps1", "val"),
        ("setup_front_easyauth.ps1", "CLIENT_SECRET"),
    }
    vistos = set()
    for script in sorted(INFRA.glob("*.ps1")):
        if script.name.endswith(".local.ps1"):
            continue  # copia local NO versionada: no se lee
        for linea in _codigo(script):
            for variable in re.findall(r"(?<![\w-])(?:-p|--value|--password)\s+\$(\w+)",
                                       linea):
                vistos.add((script.name, variable))
    assert vistos <= admitidos, vistos - admitidos
    # Y el barrido no esta mirando a la nada.
    assert ("setup_front_easyauth.ps1", "CLIENT_SECRET") in vistos


@pytest.mark.parametrize("script", [VACIAR, CREAR_BASE, ADD_SECRETS], ids=lambda s: s.stem)
def test_f035_formato_de_los_ps1_tocados(script: Path) -> None:
    """UTF-8 con BOM, CRLF y ASCII, la convencion de los .ps1 del repositorio."""
    crudo = script.read_bytes()
    assert crudo.startswith(b"\xef\xbb\xbf")
    assert crudo.count(b"\n") == crudo.count(b"\r\n") > 0
    crudo[3:].decode("ascii")
    assert _texto(script).splitlines()[0] == f"# infra/{script.name}"


# --- R5 · La revision de infra/, escrita en su README ----------------------

README = INFRA / "README_dedicacion.md"


def _seccion(titulo: str) -> str:
    """Desde el encabezado que contiene `titulo` hasta el siguiente `---`."""
    texto = README.read_text(encoding="utf-8")
    hallado = re.search(r"^#{2,4} [^\n]*" + re.escape(titulo) + r"[^\n]*\n(.*?)^---$",
                        texto, re.MULTILINE | re.DOTALL)
    assert hallado, titulo
    return hallado.group(0)


def test_f035_r5_el_3_bis_pide_psql_y_acceso_desde_tu_ip_en_azure() -> None:
    seccion = _seccion("3 bis")
    assert "-SoloRecuento" in seccion
    assert re.search(r"psql[^\n]*(tambi[eé]n en Azure|en Azure tambi[eé]n)"
                     r"|(tambi[eé]n en Azure|en Azure tambi[eé]n)[^\n]*psql",
                     seccion), seccion
    assert re.search(r"\bIP\b", seccion)
    assert r"C:\Program Files\PostgreSQL\16\bin" in seccion


def test_f035_r5_nota_de_cmd_exe_con_la_revision_de_infra() -> None:
    seccion = _seccion("cmd.exe")
    filas = [ln for ln in seccion.splitlines() if ln.startswith("| `")]
    esperado = {
        "vaciar_datos_prueba_dedicacion.ps1": r"psql",
        "crear_base_dedicacion.ps1": r"rechaza",
        "add_secrets_dedicacion.ps1": r"rechaza",
        "setup_front_easyauth.ps1": r"generad[oa] por Azure",
        "create_": r"Key Vault",
        "redeploy_dedicacion.ps1": r"Key Vault",
        "fase1_infra_dedicacion.ps1": r"Key Vault",
    }
    for fichero, patron in esperado.items():
        fila = [ln for ln in filas if fichero in ln]
        assert fila, fichero
        assert re.search(patron, fila[0]), (fichero, fila[0])
    for caracter in CARACTERES_CMD:
        assert caracter in seccion, caracter


def test_f035_r5_la_tabla_de_ficheros_cita_solo_recuento() -> None:
    # Solo la tabla de ficheros de la §7, no la de la revision de la §6 bis.
    texto = README.read_text(encoding="utf-8").split("\n## 7 ", 1)[1]
    fila = [ln for ln in texto.splitlines()
            if ln.startswith("| `vaciar_datos_prueba_dedicacion.ps1`")]
    assert len(fila) == 1 and "-SoloRecuento" in fila[0], fila
