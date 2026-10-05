# tests/test_f026_vaciado.py
"""F-026 · Script de vaciado de los datos de prueba de `dedicacion` (D1).

Trazabilidad con `specs/F-026-recursos-sin-ficha-empleado/requirements.md`:

  - **R10**: sin `-Confirmar` solo imprime el plan y sale ANTES de conectar;
    con `-Confirmar` ejecuta una única sentencia `TRUNCATE TABLE asignacion,
    evento, periodo, trabajador CONTINUE IDENTITY` en la base `dedicacion` y
    nada más: ni `obra` ni `empresa`, ni borrar tablas, ni en cascada, ni
    reiniciar secuencias, ni nada a nivel de servidor.
  - **R11**: conserva las secuencias (`CONTINUE IDENTITY`), para que un
    `asignacion.id` nuevo no reutilice una `synckey` ya escrita en Sigrid.

El script NO se ejecuta: se lee como texto. Ni red, ni BBDD, ni `az`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "infra" / "vaciar_datos_prueba_dedicacion.ps1"
SENTENCIA = ("TRUNCATE TABLE asignacion, evento, periodo, trabajador "
             "CONTINUE IDENTITY")


def _texto() -> str:
    return SCRIPT.read_bytes().decode("utf-8-sig")


def _codigo() -> list[str]:
    """Líneas de código: sin comentarios ni líneas que solo imprimen."""
    lineas = []
    for linea in _texto().splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#") or limpia.startswith("Write-Host"):
            continue
        lineas.append(limpia)
    return lineas


def _primera(patron: str, lineas: list[str]) -> int:
    for i, linea in enumerate(lineas):
        if re.search(patron, linea):
            return i
    return len(lineas)


def test_f026_r10_formato_de_los_ps1_del_repositorio() -> None:
    """UTF-8 con BOM, CRLF y texto ASCII, como `crear_base_dedicacion.ps1`."""
    crudo = SCRIPT.read_bytes()
    assert crudo.startswith(b"\xef\xbb\xbf")
    assert crudo.count(b"\n") == crudo.count(b"\r\n") > 0
    crudo[3:].decode("ascii")
    assert _texto().splitlines()[0] == "# infra/vaciar_datos_prueba_dedicacion.ps1"


def test_f026_r10_parametros_confirmar_y_local() -> None:
    # F-035 añade un tercer conmutador, `-SoloRecuento` (solo lectura).
    texto = _texto()
    assert re.search(r"param\(\s*(?:#[^\n]*\n\s*)*\[switch\]\s*\$Confirmar\s*,"
                     r"\s*(?:#[^\n]*\n\s*)*\[switch\]\s*\$Local\s*,"
                     r"\s*(?:#[^\n]*\n\s*)*\[switch\]\s*\$SoloRecuento\s*\)", texto)


def test_f026_r10_sin_confirmar_sale_antes_de_conectar() -> None:
    # Desde F-035 tambien conecta `-SoloRecuento` (solo lectura, sin
    # -Confirmar): sin NINGUNO de los dos, el script sigue sin conectar.
    codigo = _codigo()
    salida = _primera(r"^if \(-not \$Confirmar -and -not \$SoloRecuento\) \{",
                      codigo)
    assert salida < len(codigo), "falta el bloque que sale sin -Confirmar"
    # `return` en el primer nivel del bloque, no dentro de un if anidado.
    nivel, en_primer_nivel = 0, []
    for linea in codigo[salida:]:
        if nivel == 1:
            en_primer_nivel.append(linea)
        nivel += linea.count("{") - linea.count("}")
        if nivel == 0:
            break
    assert "return" in en_primer_nivel, en_primer_nivel
    conexion = _primera(r"^(\$\w+\s*=\s*)?(&\s*)?(az|psql)\b|"
                        r"\b(az|psql)\s+(postgres|account|extension|-h)\b"
                        r"|Read-Host", codigo)
    assert salida < conexion, codigo[conexion] if conexion < len(codigo) else ""


def test_f026_r10_una_sola_sentencia_sql_de_escritura() -> None:
    texto = _texto()
    assert texto.count("TRUNCATE") == 1
    assert re.search(r'\$SENTENCIA\s*=\s*"' + re.escape(SENTENCIA) + '"', texto)
    # La que se imprime en el plan y la que se ejecuta son la MISMA variable.
    usos = re.findall(r"\$SENTENCIA\b", texto)
    assert len(usos) >= 3, usos


def test_f026_r10_solo_en_la_base_dedicacion() -> None:
    # Desde F-035 Azure tambien va con psql (antes `az ... execute`, que
    # pasaba la contrasena por cmd.exe): DOS psql, uno por modo, y cada uno
    # contra la base `dedicacion` y nada mas.
    texto = _texto()
    assert "flexible-server execute" not in texto
    psql = [ln for ln in _codigo() if re.search(r"\bpsql\s+-h\b", ln)]
    local = [ln for ln in psql if "-h localhost" in ln]
    azure = [ln for ln in psql if "-h $PG_FQDN" in ln]
    assert len(local) == 1 and len(azure) == 1 and len(psql) == 2, psql
    assert "-d dedicacion" in local[0]
    assert "-d $PG_DB" in azure[0] and "-U $PG_APP_USER" in azure[0]
    assert "PG_ADMIN" not in texto


@pytest.mark.parametrize("prohibido", [
    r"\bDROP\b", r"\bCASCADE\b", r"\bALTER\s+SYSTEM\b", r"\bCREATE\b",
    r"\bRESTART\s+IDENTITY\b", r"\bDELETE\b", r"\bALTER\s+TABLE\b",
    r"firewall-rule", r"\bparameter\b", r"flexible-server\s+(update|restart|db)",
])
def test_f026_r10_nada_fuera_de_las_cuatro_tablas(prohibido: str) -> None:
    assert not re.search(prohibido, _texto(), re.IGNORECASE), prohibido


def test_f026_r10_la_sentencia_no_toca_obra_ni_empresa() -> None:
    tablas = SENTENCIA.removeprefix("TRUNCATE TABLE ").removesuffix(
        " CONTINUE IDENTITY").split(", ")
    assert tablas == ["asignacion", "evento", "periodo", "trabajador"]
    sql = [ln for ln in _codigo() if re.search(r"\b(TRUNCATE|SELECT)\b", ln)]
    assert sql and not any(re.search(r"\b(obra|empresa)\b", ln) for ln in sql)


def test_f026_r11_conserva_las_secuencias() -> None:
    assert "CONTINUE IDENTITY" in _texto()
    assert SENTENCIA.endswith("CONTINUE IDENTITY")


def test_f026_r10_la_contrasena_no_se_escribe_en_disco() -> None:
    texto = _texto()
    assert "Read-Host" in texto and "-AsSecureString" in texto
    for volcado in ("Out-File", "Set-Content", "Add-Content", "Export-"):
        assert volcado not in texto, volcado


def test_f026_r10_el_readme_de_infra_lo_documenta() -> None:
    readme = (RAIZ / "infra" / "README_dedicacion.md").read_text(encoding="utf-8")
    assert "vaciar_datos_prueba_dedicacion.ps1" in readme
    assert "-Confirmar" in readme and "F-026" in readme
