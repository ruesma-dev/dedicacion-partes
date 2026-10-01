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
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services import reglas_porcentajes as reglas
from domain.errores import EmpresasMezcladas, ObraAmbigua
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    ParteDestino,
)
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

from tests.conftest import (
    PRESUPUESTO_ORIGEN,
    PRESUPUESTO_PV_HOJAS,
    ClienteFalso,
    SettingsFalso,
    linea,
)

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
    assert obra.cenide == 70 + ide_esperado % 10


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


# ============================= reglas (T3) ============================= #

#: Horas del recurso 200 (MENC): basta para que una línea válida se escriba.
HORAS = {200: [HoraRecurso(5, "MENC", None, 9000.0)]}


def _linea_regla(**kw) -> LineaEntrada:
    datos = dict(registro_id=1, ano=2026, mes=7, porcentaje=0.4,
                 recurso_ide=200, nombre="Acuna Mera, Antonio", empresa=1)
    datos.update(kw)
    return LineaEntrada(**datos)


@pytest.mark.parametrize("valor, esperado", [
    (None, False), (0, False), (-1, False), (True, False), (False, False),
    ("1", False), (1.0, False), (1, True), (28, True),
])
def test_f022_r2_reglas_empresa_valida(valor, esperado):
    """R2 · Empresa válida = entero > 0. Un booleano no es una empresa."""
    assert reglas.empresa_valida(valor) is esperado


@pytest.mark.parametrize("empresas, esperada", [
    ([], None), ([None, 0, -3], None), ([1], 1), ([1, None], 1),
    ([None, 28, 28], 28),
])
def test_f022_r3_reglas_empresa_de_peticion(empresas, esperada):
    """R3 · La empresa de la petición es la única válida de sus líneas;
    ninguna válida -> None."""
    lineas = [_linea_regla(registro_id=i, empresa=e)
              for i, e in enumerate(empresas)]
    assert reglas.empresa_de_peticion(lineas) == esperada


def test_f022_r4_reglas_empresas_mezcladas():
    """R4 · Más de una empresa válida en la misma petición: error que las
    nombra, ordenadas."""
    lineas = [_linea_regla(registro_id=1, empresa=28),
              _linea_regla(registro_id=2, empresa=None),
              _linea_regla(registro_id=3, empresa=1)]
    with pytest.raises(EmpresasMezcladas) as exc:
        reglas.empresa_de_peticion(lineas)
    assert "[1, 28]" in str(exc.value)


def test_f022_r2_reglas_motivos_exactos_y_cortos():
    """R2 y R11 · Los motivos son el texto que el humano lee en la
    asignación: caben en los 300 caracteres de `sigrid_motivo`."""
    assert reglas.MOTIVO_SIN_EMPRESA == (
        "la línea llega sin empresa: no se adivina a qué empresa imputarla "
        "y no se escribe")
    texto = reglas.MOTIVO_EMPRESA_OBRA.format(cod="0678", emp_obra=28,
                                              emp_linea=1)
    assert texto == ("la obra 0678 es de la empresa 28 y la línea se imputa "
                     "a la empresa 1: no se escribe")
    assert len(reglas.MOTIVO_SIN_EMPRESA) <= 300 and len(texto) <= 300


@pytest.mark.parametrize("empresa", [None, 0, -1])
def test_f022_r2_reglas_linea_sin_empresa_se_omite(empresa):
    """R2 · Sin empresa válida, la línea se omite con su motivo."""
    a = reglas.ReglasPorcentajes(HORAS).decidir(_linea_regla(empresa=empresa))
    assert a.accion == "omitir"
    assert a.motivo == reglas.MOTIVO_SIN_EMPRESA


def test_f022_r2_reglas_sin_empresa_va_antes_que_la_postventa():
    """R2 · El motivo de empresa se decide ANTES que la rama de postventa:
    si no, una postventa sin empresa saldría con el motivo de P5."""
    r = reglas.ReglasPorcentajes(HORAS, postventa_registrar=False)
    a = r.decidir(_linea_regla(empresa=None, es_postventa=True))
    assert a.motivo == reglas.MOTIVO_SIN_EMPRESA


def test_f022_r11_reglas_motivo_de_empresa_de_la_obra():
    """R11 · Con `motivo_empresa`, toda línea con empresa se omite con él;
    la que no trae empresa conserva el suyo."""
    motivo = reglas.MOTIVO_EMPRESA_OBRA.format(cod="0678", emp_obra=28,
                                               emp_linea=1)
    r = reglas.ReglasPorcentajes(HORAS, motivo_empresa=motivo,
                                 postventa_registrar=False)
    con = r.decidir(_linea_regla())
    pv = r.decidir(_linea_regla(registro_id=2, es_postventa=True))
    sin = r.decidir(_linea_regla(registro_id=3, empresa=None))
    assert (con.accion, con.motivo) == ("omitir", motivo)
    assert (pv.accion, pv.motivo) == ("omitir", motivo)
    assert sin.motivo == reglas.MOTIVO_SIN_EMPRESA


def test_f022_r19_reglas_linea_con_empresa_sigue_igual():
    """R19 · Control: con empresa válida y sin motivo, se escribe como
    siempre."""
    a = reglas.ReglasPorcentajes(HORAS).decidir(_linea_regla())
    assert a.accion == "escribir" and a.hora_codigo == "MENC"


# ============================ pipeline (T4) ============================ #

#: Fichas del doble: (código, empresa) -> ide. `0678` y `POSTV2` tienen
#: copia en la empresa 28, como en Sigrid; `0404` solo existe en la 1.
FICHAS = {("0404", 1): 828942, ("0678", 1): 555001, ("0678", 28): 555028,
          ("POSTV2", 1): 999001, ("POSTV2", 28): 999028}


class ClienteEmpresas(ClienteFalso):
    """Doble indexado por `(código, empresa)` y por `ide` que ANOTA cada
    búsqueda de obra. `ambiguas`: claves que fallan con `ObraAmbigua`."""

    def __init__(self, *, quitar=(), ambiguas=(), **kw) -> None:
        super().__init__(**kw)
        self.fichas = {
            clave: ObraEntrada(ide=ide, codigo=clave[0],
                               nombre=f"{clave[0]} emp {clave[1]}",
                               empresa=clave[1])
            for clave, ide in FICHAS.items() if clave not in quitar}
        self.por_ide = {o.ide: o for o in self.fichas.values()}
        self.ambiguas = set(ambiguas)
        self.llamadas: list[tuple] = []
        self.creados: list[ObraEntrada] = []

    def obra_por_codigo(self, cod, empresa):
        self.llamadas.append(("codigo", cod, empresa))
        if (cod, empresa) in self.ambiguas:
            raise ObraAmbigua(f"obra {cod} ambigua: 2 fichas en la empresa "
                              f"{empresa}")
        return self.fichas.get((cod, empresa))

    def obra_por_ide(self, ide):
        self.llamadas.append(("ide", ide))
        return self.por_ide.get(ide)

    def capitulos_de_obra(self, obride):
        if obride in (999001, 999028):
            return PRESUPUESTO_PV_HOJAS
        if obride in (555001, 555028):
            return PRESUPUESTO_ORIGEN
        return []

    def stmts_crear_parte(self, **kw):
        self.creados.append(kw["obra"])
        self.parte = ParteDestino(ano=2026, mes=7, existe=True, ide=778,
                                  cod=kw["cod"])
        return super().stmts_crear_parte(**kw)


def _pl(cli, forzar: bool = True) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli,
                            settings=SettingsFalso(obra_pruebas_forzar=forzar))


ORIGEN_1 = ObraEntrada(codigo="0678")


def test_f022_r4_pipeline_empresas_mezcladas_no_lee_nada():
    """R4 · Dos empresas en la misma petición: error, sin buscar obras."""
    cli = ClienteEmpresas()
    with pytest.raises(EmpresasMezcladas):
        _pl(cli).preflight(obra=ORIGEN_1, lineas=[
            linea(registro_id=1, empresa=1), linea(registro_id=2, empresa=28)])
    assert cli.llamadas == [] and cli.escritos == []


@pytest.mark.parametrize("forzar", [True, False])
def test_f022_r3_pipeline_ninguna_empresa_no_lee_ninguna_obra(forzar):
    """R3 · Ninguna línea con empresa: todas omitidas, sin leer ninguna
    obra y sin escribir nada."""
    cli = ClienteEmpresas()
    lineas = [linea(registro_id=1, empresa=None),
              linea(registro_id=2, empresa=0, es_postventa=True)]
    pf = _pl(cli, forzar).preflight(obra=ORIGEN_1, lineas=lineas)
    assert [(a.accion, a.motivo) for a in pf.acciones] == [
        ("omitir", reglas.MOTIVO_SIN_EMPRESA)] * 2
    assert cli.llamadas == []
    assert pf.obra_destino is ORIGEN_1 and pf.obra_origen is ORIGEN_1
    assert pf.forzada_pruebas is forzar
    assert pf.partes == [] and pf.conflictos == []
    res = _pl(cli, forzar).ejecutar(obra=ORIGEN_1, lineas=lineas)
    assert cli.escritos == [] and res.escritas == []
    assert [o["motivo"] for o in res.omitidas] == [
        reglas.MOTIVO_SIN_EMPRESA] * 2


def test_f022_r2_pipeline_la_linea_sin_empresa_no_frena_a_las_demas():
    """R2 · La línea sin empresa se omite con motivo y la otra se escribe."""
    cli = ClienteEmpresas()
    lineas = [linea(registro_id=1, empresa=None),
              linea(registro_id=2, empleado_ide=12)]
    res = _pl(cli).ejecutar(obra=ORIGEN_1, lineas=lineas)
    assert res.omitidas == [{"registro_id": 1,
                             "motivo": reglas.MOTIVO_SIN_EMPRESA}]
    assert [e["registro_id"] for e in res.escritas] == [2]


@pytest.mark.parametrize("forzar", [True, False])
def test_f022_r10_r11_pipeline_obra_de_otra_empresa_se_omite(forzar):
    """R10 y R11 · La obra llega por `ide` y es de la 28; las líneas se
    imputan a la 1. En los DOS modos: todo omitido con el motivo que nombra
    obra y empresas, sin resolver destinos y sin escribir."""
    cli = ClienteEmpresas()
    obra = ObraEntrada(ide=555028, codigo="0678")
    lineas = [linea(registro_id=1), linea(registro_id=2, es_postventa=True),
              linea(registro_id=3, empresa=None)]
    pf = _pl(cli, forzar).preflight(obra=obra, lineas=lineas)
    motivo = ("la obra 0678 es de la empresa 28 y la línea se imputa a la "
              "empresa 1: no se escribe")
    assert [(a.accion, a.motivo) for a in pf.acciones] == [
        ("omitir", motivo), ("omitir", motivo),
        ("omitir", reglas.MOTIVO_SIN_EMPRESA)]
    assert cli.llamadas == [("ide", 555028)]
    # F-024 (R20, design §7): se publica la obra de origen RESUELTA.
    assert (pf.obra_destino.ide, pf.obra_destino.empresa) == (555028, 28)
    assert pf.forzada_pruebas is forzar
    assert pf.partes == [] and pf.conflictos == []
    res = _pl(cli, forzar).ejecutar(obra=obra, lineas=lineas)
    assert cli.escritos == [] and res.escritas == []


@pytest.mark.parametrize("forzar, llamadas", [
    (True, [("ide", 555001), ("codigo", "0404", 1)]),
    (False, [("ide", 555001)]),
])
def test_f022_r10_pipeline_obra_por_ide_de_la_empresa_se_escribe(forzar,
                                                                 llamadas):
    """R10 · Misma empresa: la obra de origen se comprueba en los dos modos
    y la línea se escribe."""
    cli = ClienteEmpresas()
    obra = ObraEntrada(ide=555001, codigo="0678")
    res = _pl(cli, forzar).ejecutar(obra=obra, lineas=[linea(registro_id=1)])
    assert cli.llamadas == llamadas
    assert [e["registro_id"] for e in res.escritas] == [1]
    assert res.obra_destino.empresa == 1


def test_f022_r12_pipeline_obra_sin_ide_por_codigo_y_empresa():
    """R12 · Sin `ide`, la obra se busca por código y empresa de la
    petición: la `0678` de la 28 es otra ficha que la de la 1."""
    cli = ClienteEmpresas()
    pf = _pl(cli, forzar=False).preflight(
        obra=ORIGEN_1, lineas=[linea(registro_id=1, empresa=28)])
    assert cli.llamadas == [("codigo", "0678", 28)]
    assert pf.obra_destino.ide == 555028 and pf.obra_destino.empresa == 28
    assert pf.acciones[0].accion == "escribir"


def test_f022_r12_pipeline_obra_no_encontrada_en_la_empresa():
    """R12 · Si no existe en esa empresa, error que nombra la empresa."""
    cli = ClienteEmpresas(quitar={("0678", 28)})
    with pytest.raises(RuntimeError) as exc:
        _pl(cli, forzar=False).preflight(
            obra=ORIGEN_1, lineas=[linea(registro_id=1, empresa=28)])
    assert "0678" in str(exc.value) and "empresa=28" in str(exc.value)


def test_f022_r12_pipeline_obra_sin_ide_ni_codigo():
    cli = ClienteEmpresas()
    with pytest.raises(RuntimeError, match="obra no encontrada"):
        _pl(cli).preflight(obra=ObraEntrada(), lineas=[linea()])
    assert cli.llamadas == []


def test_f022_r13_pipeline_pruebas_por_codigo_y_empresa():
    """R13 · En pruebas, la obra de pruebas se busca en la empresa de la
    petición."""
    cli = ClienteEmpresas()
    pf = _pl(cli).preflight(obra=ORIGEN_1, lineas=[linea(registro_id=1)])
    assert cli.llamadas == [("codigo", "0678", 1), ("codigo", "0404", 1)]
    assert pf.obra_destino.codigo == "0404" and pf.obra_destino.empresa == 1
    assert pf.forzada_pruebas is True


def test_f022_r13_pipeline_pruebas_inexistente_en_la_empresa_falla():
    """R13 · La `0404` solo existe en la 1: con la 28, error con código y
    empresa, sin escribir nada (D3, estricta)."""
    cli = ClienteEmpresas()
    with pytest.raises(RuntimeError) as exc:
        _pl(cli).ejecutar(obra=ORIGEN_1,
                          lineas=[linea(registro_id=1, empresa=28)])
    assert "0404" in str(exc.value) and "empresa 28" in str(exc.value)
    assert cli.escritos == []


@pytest.mark.parametrize("forzar", [True, False])
def test_f022_r14_pipeline_la_partida_usa_el_origen_ya_resuelto(forzar):
    """R14 · La partida normal se casa contra la obra de origen del paso 1:
    una sola búsqueda de esa obra."""
    cli = ClienteEmpresas()
    pf = _pl(cli, forzar).preflight(obra=ORIGEN_1,
                                    lineas=[linea(registro_id=1)])
    assert [c for c in cli.llamadas if c[1] == "0678"] == [
        ("codigo", "0678", 1)]
    assert pf.acciones[0].partida_cod == "CI.1.10"


@pytest.mark.parametrize("empresa, ide_pv", [(1, 999001), (28, 999028)])
def test_f022_r15_pipeline_postventa_de_la_empresa_pedida(empresa, ide_pv):
    """R15 · `POSTV2` existe en la 1 y en la 28: se elige la de la empresa
    de la petición."""
    cli = ClienteEmpresas()
    pf = _pl(cli, forzar=False).preflight(obra=ORIGEN_1, lineas=[
        linea(registro_id=1, empresa=empresa, es_postventa=True)])
    assert ("codigo", "POSTV2", empresa) in cli.llamadas
    assert pf.obra_postventa.ide == ide_pv
    assert pf.obra_postventa.empresa == empresa
    assert pf.acciones[0].accion == "escribir"


@pytest.mark.parametrize("quitar, ambiguas, texto", [
    ({("POSTV2", 28)}, set(), "no encontrada"),
    (set(), {("POSTV2", 28)}, "ambigua"),
], ids=["inexistente", "ambigua"])
def test_f022_r16_pipeline_postventa_sin_ficha_en_la_empresa(quitar,
                                                            ambiguas, texto):
    """R16 · Sin ficha de postventa (o con dos) en la empresa: la postventa
    se omite con un motivo que nombra código y empresa; la normal sigue."""
    cli = ClienteEmpresas(quitar=quitar, ambiguas=ambiguas)
    res = _pl(cli, forzar=False).ejecutar(obra=ORIGEN_1, lineas=[
        linea(registro_id=1, empresa=28, es_postventa=True),
        linea(registro_id=2, empresa=28, empleado_ide=12)])
    [omitida] = res.omitidas
    assert omitida["registro_id"] == 1
    assert "'POSTV2'" in omitida["motivo"]
    assert "empresa 28" in omitida["motivo"] and texto in omitida["motivo"]
    assert [e["registro_id"] for e in res.escritas] == [2]


@pytest.mark.parametrize("forzar, empresa, ide", [
    (True, 1, 828942), (False, 1, 555001), (False, 28, 555028)])
def test_f022_r17_pipeline_el_parte_nuevo_lleva_la_obra_resuelta(
        forzar, empresa, ide):
    """R17 · El parte nuevo se crea con la obra destino RESUELTA, que es la
    que trae la empresa que irá a `con.emp`."""
    cli = ClienteEmpresas(parte_existe=False)
    res = _pl(cli, forzar).ejecutar(obra=ORIGEN_1, lineas=[
        linea(registro_id=1, empresa=empresa)])
    [creada] = cli.creados
    assert (creada.ide, creada.empresa) == (ide, empresa)
    assert [e["registro_id"] for e in res.escritas] == [1]


def test_f022_r6_pipeline_sin_literales_de_obra_ni_de_empresa():
    """R6 y D4 · Ni la obra de pruebas ni una empresa «por defecto» viven
    como literal en el código que resuelve obras: salen de los ajustes y de
    la línea. (`POSTV2` ya lo vigila `test_f002_fuente_unica.py`.)"""
    import re
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    for rel in ("application/pipelines/registro_pipeline.py",
                "application/services/reglas_porcentajes.py",
                "infrastructure/sigrid/sigrid_write_client.py"):
        texto = (raiz / rel).read_text(encoding="utf-8")
        assert "0404" not in texto, rel
        assert re.search(r"empresa\w*\s*(=|==|!=|:\s*int\s*=)\s*1\b",
                         texto) is None, rel


# =========================== app y ajustes (T5) =========================== #

#: Fichas que devuelve la lectura falsa de la app: (código, empresa) -> ide.
FICHAS_APP = {("0404", 1): 828942, ("0678", 1): 555001,
              ("POSTV2", 1): 999001, ("POSTV2", 28): 999028}


class SigridFalsaApp:
    """Sustituye a `SigridWriteClient._read` para la app entera: contesta a
    cada consulta del pipeline por su forma, anota cada una y no escribe.
    `repetir`: claves (código, empresa) que salen DOS veces (ambiguas)."""

    def __init__(self, repetir=()) -> None:
        self.consultas: list[tuple[str, list]] = []
        self.repetir = set(repetir)

    def __call__(self, cli, sql: str, params: list) -> list[dict]:
        self.consultas.append((sql, list(params)))
        if "con.cod = ? AND con.emp = ?" in sql:
            cod, emp = params
            ide = FICHAS_APP.get((cod, emp))
            if ide is None:
                return []
            fila = {"ide": ide, "cod": cod, "res": cod, "cenide": 1,
                    "emp": emp}
            return [fila, fila] if (cod, emp) in self.repetir else [fila]
        if "WHERE obr.ide = ?" in sql:
            por_ide = {i: c for c, i in FICHAS_APP.items()}
            cod, emp = por_ide[params[0]]
            return [{"ide": params[0], "cod": cod, "res": cod, "cenide": 1,
                     "emp": emp}]
        if "FROM obrparpar" in sql and params[0] in (999001, 999028):
            return PRESUPUESTO_PV_HOJAS
        return []


def _escribir_prohibido(self, statements):
    raise AssertionError("la app no debe escribir en estos tests")


@pytest.fixture
def app_falsa(monkeypatch):
    """`build_app` con ajustes falsos y la lectura de Sigrid sustituida."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api.app import build_app

    ajustes = SimpleNamespace(
        sigrid_api_base_url="http://sigrid.invalid",
        sigrid_api_function_key="sin-clave", sigrid_api_database="ruesma",
        sigrid_api_timeout_s=1.0, sigrid_max_statements=15,
        tip_parte_trabajo=35, est_parte_activo=1, obra_pruebas_forzar=True,
        obra_pruebas_cod="0404", marca_pruebas="PRUEBA-PORC",
        postventa_registrar=True, postventa_obra_cod="POSTV2", paso_pos=64)

    def fabricar(repetir=()):
        lectura = SigridFalsaApp(repetir)
        monkeypatch.setattr(SigridWriteClient, "_read",
                            lambda self, sql, params: lectura(self, sql,
                                                              params))
        monkeypatch.setattr(SigridWriteClient, "escribir",
                            _escribir_prohibido)
        return TestClient(build_app(ajustes)), lectura

    return fabricar


def _peticion(*empresas, postventa: bool = False) -> dict:
    lineas = []
    for i, emp in enumerate(empresas, start=1):
        lin = {"registro_id": i, "ano": 2026, "mes": 7, "porcentaje": 0.4,
               "es_postventa": postventa}
        if emp != "ausente":
            lin["empresa"] = emp
        lineas.append(lin)
    return {"obra": {"codigo": "0678"}, "lineas": lineas}


def test_f022_r1_app_la_empresa_llega_al_dominio(app_falsa):
    """R1 · El campo `empresa` de cada línea llega al pipeline: la que no lo
    trae (ausente o nulo) sale omitida por empresa; la que sí, por otra
    cosa (aquí, no tiene recurso)."""
    cliente, _ = app_falsa()
    r = cliente.post("/api/registro/preflight",
                     json=_peticion(1, "ausente", None))
    assert r.status_code == 200, r.text
    motivos = [a["motivo"] for a in r.json()["acciones"]]
    assert motivos == [reglas.MOTIVO_SIN_RECURSO, reglas.MOTIVO_SIN_EMPRESA,
                       reglas.MOTIVO_SIN_EMPRESA]


@pytest.mark.parametrize("ruta", ["/api/registro/preflight",
                                  "/api/registro/ejecutar"])
def test_f022_r4_app_empresas_mezcladas_es_422_sin_leer(app_falsa, ruta):
    """R4 · Petición con líneas de dos empresas: 422 que las nombra, sin una
    sola lectura en Sigrid."""
    cliente, lectura = app_falsa()
    r = cliente.post(ruta, json=_peticion(28, 1))
    assert r.status_code == 422
    cuerpo = r.json()
    assert cuerpo["ok"] is False and "[1, 28]" in cuerpo["error"]
    assert lectura.consultas == []


@pytest.mark.parametrize("ruta", ["/api/registro/preflight",
                                  "/api/registro/ejecutar"])
def test_f022_r8_app_obra_ambigua_es_502(app_falsa, ruta):
    """R8 · Obra de pruebas con dos fichas en la empresa: el error genérico
    de siempre (502), no un 422 de dato de entrada."""
    cliente, _ = app_falsa(repetir={("0404", 1)})
    r = cliente.post(ruta, json=_peticion(1))
    assert r.status_code == 502
    assert r.json()["ok"] is False and "ambigua" in r.json()["error"]


def test_f022_r18_app_preflight_publica_la_empresa(app_falsa):
    """R18 · `obra_destino` y `obra_postventa` del preflight llevan su
    empresa. En modo pruebas el destino de la postventa es la obra de
    pruebas (ARCHITECTURE.md#regla-p5): la elección de `POSTV2` por empresa
    la cubre `test_f022_r15_pipeline_postventa_de_la_empresa_pedida`."""
    cliente, _ = app_falsa()
    r = cliente.post("/api/registro/preflight",
                     json=_peticion(1, postventa=True))
    cuerpo = r.json()
    assert cuerpo["obra_destino"]["empresa"] == 1
    assert cuerpo["obra_destino"]["codigo"] == "0404"
    assert cuerpo["obra_postventa"]["empresa"] == 1
    assert cuerpo["obra_postventa"]["ide"] == 828942
    assert cuerpo["capitulo_postventa"]["cod"] == "0678"


def test_f022_r18_app_ejecutar_publica_la_empresa(app_falsa):
    """R18 · `obra_destino` de ejecutar lleva su empresa (sin escribir: la
    única línea no tiene recurso)."""
    cliente, _ = app_falsa()
    r = cliente.post("/api/registro/ejecutar", json=_peticion(1))
    assert r.status_code == 200, r.text
    assert r.json()["obra_destino"]["empresa"] == 1
    assert r.json()["escritas"] == []


def test_f022_r5_app_ajustes_sin_sigrid_empresa():
    """R5 · El transfer no tiene empresa por defecto: ni en sus ajustes ni en
    su `.env.example` (D4)."""
    from pathlib import Path

    from config.settings import Settings

    assert "sigrid_empresa" not in Settings.model_fields
    ejemplo = Path(__file__).resolve().parents[1] / ".env.example"
    assert "SIGRID_EMPRESA" not in ejemplo.read_text(encoding="utf-8")


# ========================== documentación (T7) ========================== #

def _raiz_repo():
    from pathlib import Path

    return Path(__file__).resolve().parents[3]


def _plano(ruta) -> str:
    return " ".join(ruta.read_text(encoding="utf-8").split())


def test_f022_r22_la_regla_se_remite_no_se_reenuncia():
    """R22 · La regla vive en `#regla-empresa`; P5, el modo pruebas, el
    pipeline y el README del transfer REMITEN a ella."""
    raiz = _raiz_repo()
    arq = _plano(raiz / "docs" / "ARCHITECTURE.md")
    p5 = arq[arq.index('<a id="regla-p5"></a>'):
             arq.index('<a id="regla-p4"></a>')]
    pruebas = arq[arq.index('<a id="regla-pruebas"></a>'):
                  arq.index("10. **`ide` reservado a mano.**")]
    assert "(#regla-empresa)" in p5
    assert "(#regla-empresa)" in pruebas
    transfer = raiz / "services" / "dedicacion-transfer"
    for rel in ("README.md", "application/pipelines/registro_pipeline.py"):
        assert "ARCHITECTURE.md#regla-empresa" in (
            transfer / rel).read_text(encoding="utf-8"), rel


def test_f022_r23_infra_sin_sigrid_empresa():
    """D4 · El despliegue del transfer ya no declara `SIGRID_EMPRESA`."""
    ps1 = _raiz_repo() / "infra" / "create_transfer_dedicacion.ps1"
    assert "SIGRID_EMPRESA" not in ps1.read_text(encoding="utf-8-sig")


# ================== script manual de pruebas (T5, T9) ================== #

def test_f022_r13_script_de_pruebas_imputa_a_la_empresa_de_la_0404():
    """R13 y D3 · El script manual busca sus obras y manda sus líneas en
    `EMPRESA_PRUEBA`, que tiene que ser la 1: la obra de pruebas solo existe
    ahí y, con otra, el preflight falla sin escribir. Sus líneas de ejemplo
    siguen incluyendo una de postventa, que es lo que el script ejercita."""
    import prueba_escritura_porcentajes as script

    assert script.EMPRESA_PRUEBA == 1
    lineas = script._lineas(2026, 7)
    assert [lin.empresa for lin in lineas] == [1] * len(script.LINEAS_PRUEBA)
    assert any(lin.es_postventa for lin in lineas)
