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
    # Al primer nivel del script: no colgada de un `if ($Local)`.
    assert _nivel(codigo, comprobacion) == 0, codigo[comprobacion]
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
    texto = _texto(VACIAR)
    error = re.findall(r'throw\s*\(?"[^\n]*', texto)
    azure = [ln for ln in error if "IP" in ln]
    assert azure, error
    assert re.search(r"firewall", azure[0], re.IGNORECASE)
    assert re.search(r"NO (la )?(crea|toca)", azure[0]), azure[0]


def test_f035_r3_sin_tocar_nada_del_servidor() -> None:
    texto = _texto(VACIAR)
    assert not re.search(r"firewall-rule", texto, re.IGNORECASE)
    assert not re.search(r"flexible-server\s+(update|restart|db|parameter)", texto)
    assert "PG_ADMIN" not in texto
