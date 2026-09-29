# tests/test_f022_obra_por_empresa.py
"""F-022 · El transfer busca cada obra por código y empresa (R1-R19).

El código de obra solo es único DENTRO de su empresa (`con.emp`): `POSTV2`
tiene ficha en la empresa 1 y en la 28. La regla vive en
`docs/ARCHITECTURE.md#regla-empresa`; aquí se prueba, no se reenuncia.

Todo offline: el cliente de Sigrid se prueba con `_read` sustituido por un
doble que guarda la consulta y devuelve filas fijas, y el pipeline con un
doble de cliente indexado por `(código, empresa)` que anota cada llamada.
Ni red, ni BBDD, ni `.env`. Los `ide` son inventados.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest

from domain.models.registro_models import LineaEntrada, ObraEntrada
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient


# ============================ dominio (T1) ============================ #

def test_f022_r1_dominio_la_linea_lleva_empresa():
    """R1 · La línea de entrada lleva `empresa`, opcional a propósito: su
    ausencia tiene que llegar al pipeline para omitirse con motivo."""
    campos = {f.name: f for f in dataclasses.fields(LineaEntrada)}
    assert "empresa" in campos
    assert campos["empresa"].default is None
    assert LineaEntrada(registro_id=1, ano=2026, mes=7, porcentaje=0.4,
                        empresa=28).empresa == 28


def test_f022_r9_dominio_la_obra_lleva_empresa():
    """R9 · La obra resuelta publica su `con.emp`."""
    campos = {f.name: f for f in dataclasses.fields(ObraEntrada)}
    assert "empresa" in campos
    assert campos["empresa"].default is None
    assert ObraEntrada(ide=1, codigo="X", empresa=1).empresa == 1


def test_f022_r4_r8_dominio_errores_propios():
    """R4 y R8 · Los dos errores de la regla son del dominio y heredan de
    lo que la app ya sabe tratar."""
    from domain.errores import EmpresasMezcladas, ObraAmbigua

    assert issubclass(EmpresasMezcladas, ValueError)
    assert issubclass(ObraAmbigua, RuntimeError)


# ========================= cliente Sigrid (T2) ========================= #

class LecturaFalsa:
    """Sustituye a `SigridWriteClient._read`: guarda cada consulta y
    devuelve las filas fijadas. IGNORA el WHERE a propósito: así se prueba
    que el cliente acierta aunque Sigrid devuelva fichas de otra empresa."""

    def __init__(self, filas: list[dict]) -> None:
        self.filas = filas
        self.llamadas: list[tuple[str, list]] = []

    def __call__(self, sql: str, params: list) -> list[dict]:
        self.llamadas.append((sql, list(params)))
        return list(self.filas)


def _ficha(ide: int, emp, cod: str = "POSTV2") -> dict:
    """Una fila de `obr JOIN con` tal y como la devuelve `_read`."""
    return {"ide": ide, "cod": cod, "res": f"POSTVENTA emp {emp}",
            "cenide": 70 + ide % 10, "emp": emp}


def _cliente(filas: list[dict]) -> tuple[SigridWriteClient, LecturaFalsa]:
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma")
    lectura = LecturaFalsa(filas)
    cli._read = lectura                       # type: ignore[method-assign]
    return cli, lectura


def test_f022_r6_cliente_busca_por_codigo_y_empresa():
    """R6 · La consulta filtra código Y empresa, parametrizados."""
    cli, lectura = _cliente([_ficha(9028, 28)])
    cli.obra_por_codigo("POSTV2", 28)
    [(sql, params)] = lectura.llamadas
    plano = " ".join(sql.split())
    assert "con.cod = ?" in plano and "con.emp = ?" in plano
    assert "con.emp AS emp" in plano
    assert params == ["POSTV2", 28]
    assert "POSTV2" not in plano and "28" not in plano


@pytest.mark.parametrize("orden", [(1, 28), (28, 1)],
                         ids=["filas_1_28", "filas_28_1"])
@pytest.mark.parametrize("pedida, ide_esperado", [(1, 9001), (28, 9028)],
                         ids=["pide_1", "pide_28"])
def test_f022_r7_cliente_postv2_elige_la_empresa_pedida(orden, pedida,
                                                        ide_esperado):
    """R7 · `POSTV2` existe en las empresas 1 y 28. Sea cual sea el orden de
    las filas, se queda con la ficha de la empresa pedida."""
    fichas = {1: _ficha(9001, 1), 28: _ficha(9028, 28)}
    cli, _ = _cliente([fichas[e] for e in orden])
    obra = cli.obra_por_codigo("POSTV2", pedida)
    assert obra is not None
    assert obra.ide == ide_esperado
    assert obra.empresa == pedida
    assert obra.codigo == "POSTV2"
    assert obra.nombre == f"POSTVENTA emp {pedida}"
    assert getattr(obra, "cenide") == 70 + ide_esperado % 10


def test_f022_r8_cliente_sin_ficha_en_la_empresa_no_encontrada():
    """R8 · Hay ficha, pero de otra empresa: «no encontrada», no la otra."""
    cli, _ = _cliente([_ficha(9028, 28)])
    assert cli.obra_por_codigo("POSTV2", 1) is None


def test_f022_r8_cliente_sin_filas_no_encontrada():
    cli, _ = _cliente([])
    assert cli.obra_por_codigo("POSTV2", 1) is None


def test_f022_r8_cliente_ficha_sin_empresa_no_casa_con_ninguna():
    """R8 · Una ficha con `con.emp` nulo no es de ninguna empresa válida: no
    se le adjudica la pedida."""
    cli, _ = _cliente([_ficha(9000, None)])
    assert cli.obra_por_codigo("POSTV2", 1) is None


def test_f022_r8_cliente_dos_fichas_en_la_empresa_es_ambigua():
    """R8 · Nunca «la primera»: dos fichas en la empresa pedida fallan con
    código, empresa y número de fichas."""
    from domain.errores import ObraAmbigua

    cli, _ = _cliente([_ficha(9001, 1), _ficha(9002, 1), _ficha(9028, 28)])
    with pytest.raises(ObraAmbigua) as exc:
        cli.obra_por_codigo("POSTV2", 1)
    texto = str(exc.value)
    assert "POSTV2" in texto and "empresa 1" in texto and "2 fichas" in texto


def test_f022_r9_cliente_obra_por_ide_devuelve_su_empresa():
    """R9 · Por `ide` también se lee `con.emp` (el `ide` es único: no se
    filtra por empresa)."""
    cli, lectura = _cliente([_ficha(9028, 28)])
    obra = cli.obra_por_ide(9028)
    assert obra is not None and obra.empresa == 28 and obra.ide == 9028
    [(sql, params)] = lectura.llamadas
    assert "con.emp AS emp" in " ".join(sql.split())
    assert "con.emp = ?" not in sql
    assert params == [9028]


def test_f022_r9_cliente_obra_por_ide_sin_empresa_no_inventa_una():
    """R9 · Una ficha con `con.emp` nulo sale con empresa 0, que no es
    válida: el pipeline la tratará como de otra empresa (R11)."""
    cli, _ = _cliente([_ficha(9000, None)])
    assert cli.obra_por_ide(9000).empresa == 0


def test_f022_r9_cliente_obra_por_ide_inexistente():
    cli, _ = _cliente([])
    assert cli.obra_por_ide(1) is None


@pytest.mark.parametrize("empresa", [1, 28])
def test_f022_r17_cliente_la_cabecera_lleva_la_empresa_de_la_obra(empresa):
    """R17 · `con.emp` de la cabecera del parte = empresa de la obra
    destino, no un ajuste del servicio."""
    cli, _ = _cliente([])
    obra = ObraEntrada(ide=828942, codigo="0404", nombre="PRUEBAS",
                       empresa=empresa)
    stmts = cli.stmts_crear_parte(obra=obra, ano=2026, mes=7,
                                  cod="PT26/09999", desc="Parte")
    assert "INSERT INTO con (ide, emp," in stmts[0]["sql"]
    assert stmts[0]["parameters"][0] == empresa
    assert stmts[0]["parameters"][1:4] == [35, 1, "PT26/09999"]


def test_f022_r17_cliente_cabecera_sin_empresa_no_se_adivina():
    """R17 · Una obra sin empresa no produce cabecera: `ValueError`."""
    cli, _ = _cliente([])
    with pytest.raises(ValueError):
        cli.stmts_crear_parte(obra=ObraEntrada(ide=1, codigo="0404"),
                              ano=2026, mes=7, cod="PT26/09999", desc="P")


def test_f022_r5_cliente_sin_empresa_por_defecto():
    """R5 y R6 · El constructor no acepta empresa y la búsqueda por código
    la exige, sin valor por defecto."""
    ctor = inspect.signature(SigridWriteClient.__init__).parameters
    assert "empresa" not in ctor
    with pytest.raises(TypeError):
        SigridWriteClient(base_url="http://x", function_key="k",
                          database="ruesma", empresa=1)
    busqueda = inspect.signature(SigridWriteClient.obra_por_codigo).parameters
    assert "empresa" in busqueda
    assert busqueda["empresa"].default is inspect.Parameter.empty
