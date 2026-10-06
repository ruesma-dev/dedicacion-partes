# tests/test_f037_pipeline.py
"""F-037 · Pipeline: cuenta analítica de la línea y parte del periodo.

Trazabilidad con `specs/F-037-asiento-analitico-obra/requirements.md`:
R1-R8 (cuenta analítica, `#regla-analitica`) y R9-R17 (el parte del
periodo: elección, complementario, duplicados y conflictos contra todos los
partes del periodo). Copia adaptada de la F-031 de `partes` (design §7).

Sin red ni BBDD: `ClienteF037` es el `ClienteFalso` de `conftest.py` con
cada lectura nueva anotada y configurable. Nada se escribe: las sentencias
se acumulan en `escritos`.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_porcentajes import AVISO_SIN_PARTIDA
from domain.models.registro_models import (
    HoraRecurso, LineaSigrid, ObraEntrada, ParteSigrid, PartidaCuenta,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de

from tests.conftest import (
    OBRA_ORIGEN, ClienteFalso, SettingsFalso, linea, linea_previa,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)
#: Centros de las obras del doble de `conftest.py`.
CEN_PRUEBAS, CEN_PV, CEN_ORIGEN = 828943, 999002, 555101
REG, CER, IMP = 1, 3, 10
#: Recurso sin cuenta en su ficha de horas (respaldo de la partida).
SIN_CUENTA = 500


class ClienteF037(ClienteFalso):
    """Doble con las lecturas de F-037 anotadas en ``lecturas`` y
    configurables. ``falla``: lecturas que revientan como sigrid-api caída.
    ``cuentas``: cuentas por centro y subcuenta (None = las del padre, una
    por subcuenta). ``periodo``: partes del periodo (None = derivado de
    ``parte``); ``tras_crear``: lo que se lee en cada relectura tras una
    alta. ``lineas_por_parte``: líneas de cada `hmo` (None = las del padre).
    """

    def __init__(self, *, cuentas=None, partidas=None, falla=(),
                 periodo=None, tras_crear=None, lineas_por_parte=None,
                 **kw) -> None:
        super().__init__(**kw)
        self.horas[SIN_CUENTA] = [HoraRecurso(7, "MCAP", None, 5000.0),
                                  HoraRecurso(1, "HLPE", None, 20.0)]
        self.cuentas = cuentas
        self.partidas = dict(partidas or {})
        self.falla = set(falla)
        self.periodo = periodo
        self.tras_crear = list(tras_crear or [])
        self.lineas_por_parte = lineas_por_parte
        self.lecturas: list[tuple] = []
        self.cods = iter(["PT26/00350", "PT26/00351", "PT26/00352"])

    def _anota(self, *lectura) -> None:
        self.lecturas.append(lectura)
        if lectura[0] in self.falla:
            raise RuntimeError(f"sigrid-api caida en {lectura[0]}")

    def de(self, nombre: str) -> list[tuple]:
        return [x[1:] for x in self.lecturas if x[0] == nombre]

    def cuentas_de_centro(self, cenide, empresa, subcuentas):
        self._anota("cuentas", cenide, empresa, sorted(subcuentas))
        if self.cuentas is None:
            return super().cuentas_de_centro(cenide, empresa, subcuentas)
        del_centro = self.cuentas.get(cenide, {})
        return {s: list(del_centro[s]) for s in subcuentas if s in del_centro}

    def partidas_de_lineas(self, parides):
        self._anota("partidas", sorted(parides))
        return {i: self.partidas[i] for i in parides if i in self.partidas}

    def partes_del_periodo(self, obra_ide, ano, mes):
        self._anota("partes", obra_ide, ano, mes)
        if self.periodo is None:
            return super().partes_del_periodo(obra_ide, ano, mes)
        return list(self.periodo)

    def lineas_del_parte(self, hmoide, resides):
        self._anota("lineas", hmoide)
        if self.lineas_por_parte is None:
            return super().lineas_del_parte(hmoide, resides)
        return [ls for ls in self.lineas_por_parte.get(hmoide, [])
                if ls.reside in set(resides)]

    def siguiente_cod_pt(self, ano, empresa=None):
        self._anota("siguiente", ano, empresa)
        return next(self.cods)

    def escribir(self, statements):
        if any(s["sql"] == "crear" for s in statements) and self.tras_crear:
            self.periodo = self.tras_crear.pop(0)
        return super().escribir(statements)


def _pl(cli, forzar: bool = True) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli,
                            settings=SettingsFalso(obra_pruebas_forzar=forzar))


def _caa(a) -> tuple:
    return (a.caa_ide, a.caa_cod, a.caa_motivo, a.caa_aviso, a.caa_origen,
            a.caa_nota)


# ===================== R1 · la línea lleva su cuenta ===================== #

def test_f037_r1_la_linea_escrita_lleva_la_cuenta_de_la_obra():
    cli = ClienteF037()
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea(registro_id=1)])
    [ins] = cli.inserts()
    assert ins["caaide"] == 90001
    assert res.escritas[0]["caa_cod"] == "0404.CIMO03"
    assert cli.de("cuentas") == [(CEN_PRUEBAS, 1, ["CIMO03"])]


def test_f037_r1_r6_la_accion_publica_la_cuenta_resuelta():
    cli = ClienteF037()
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea(registro_id=1)])
    (a,) = pf.acciones
    assert _caa(a) == (90001, "0404.CIMO03", None, None, "recurso", None)
    assert a.aviso is None


# ================ R2 · tipo escrito, luego tipo por defecto ================ #

def test_f037_r2_manda_el_tipo_escrito_sobre_el_de_por_defecto():
    cli = ClienteF037()
    cli.horas[200].append(HoraRecurso(1, "HLPE", None, 20.0,
                                      caa_cod="00000.CIMO05", defecto=True))
    (a,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).acciones
    assert (a.caa_cod, a.caa_origen) == ("0404.CIMO03", "recurso")


def test_f037_r2_sin_cuenta_del_tipo_va_la_del_tipo_por_defecto():
    cli = ClienteF037()
    cli.horas[SIN_CUENTA][1] = HoraRecurso(1, "HLPE", None, 20.0,
                                           caa_cod="00000.CIMO05",
                                           defecto=True)
    (a,) = _pl(cli).preflight(
        obra=OBRA, lineas=[linea(recurso_ide=SIN_CUENTA)]).acciones
    assert (a.caa_cod, a.caa_origen) == ("0404.CIMO05", "recurso")
    assert cli.de("partidas") == []         # el recurso ya da: no se lee


# ===================== R3 · respaldo de la partida ===================== #

def test_f037_r3_sin_cuenta_del_recurso_vale_la_de_la_partida_ci():
    cli = ClienteF037(partidas={80001: PartidaCuenta(80001, "CI.1.10",
                                                     "0678.CIMO03")})
    (a,) = _pl(cli).preflight(
        obra=OBRA, lineas=[linea(recurso_ide=SIN_CUENTA)]).acciones
    assert a.paride == 80001
    nota = ("el recurso no tiene cuenta para esa hora: se usa la de la "
            "partida CI.1.10 (.CIMO03)")
    assert _caa(a) == (90001, "0404.CIMO03", None, None, "partida", nota)
    assert a.aviso == nota                  # R6: se suma al aviso
    assert cli.de("partidas") == [([80001],)]


@pytest.mark.parametrize("caa_cod", ["0678.CP0001", "0678.INGR01", None])
def test_f037_r3_la_partida_que_no_es_de_coste_no_vale(caa_cod):
    cli = ClienteF037(partidas={80001: PartidaCuenta(80001, "CI.1.10",
                                                     caa_cod)})
    (a,) = _pl(cli).preflight(
        obra=OBRA, lineas=[linea(recurso_ide=SIN_CUENTA)]).acciones
    assert _caa(a) == (0, None, "recurso_sin_cuenta", None, None, None)
    assert a.aviso is None and cli.de("cuentas") == []


def test_f037_r3_r7_partidas_una_lectura_solo_de_las_que_la_necesitan():
    cli = ClienteF037(partidas={80001: PartidaCuenta(80001, "CI.1.10",
                                                     "0678.CIMO03"),
                                80002: PartidaCuenta(80002, "CI.1.20",
                                                     "0678.CIMO02")})
    lineas = [linea(registro_id=1),         # MENC con cuenta: no la necesita
              linea(registro_id=2, recurso_ide=SIN_CUENTA, mes=7),
              linea(registro_id=3, recurso_ide=SIN_CUENTA, mes=8,
                    paride=80002, partida_cod="CI.1.20")]
    pf = _pl(cli).preflight(obra=OBRA, lineas=lineas)
    assert cli.de("partidas") == [([80001, 80002],)]
    assert cli.de("cuentas") == [(CEN_PRUEBAS, 1, ["CIMO02", "CIMO03"])]
    assert [a.caa_origen for a in pf.acciones] == [
        "recurso", "partida", "partida"]


# ============== R4 · la cuenta del centro de la obra destino ============== #

def test_f037_r4_modo_normal_cuenta_de_la_obra_de_origen():
    cli = ClienteF037()
    (a,) = _pl(cli, forzar=False).preflight(obra=OBRA,
                                            lineas=[linea()]).acciones
    assert a.caa_cod == "0678.CIMO03"
    assert cli.de("cuentas") == [(CEN_ORIGEN, 1, ["CIMO03"])]


def test_f037_r4_modo_normal_postventa_con_la_cuenta_de_postventa():
    cli = ClienteF037()
    pf = _pl(cli, forzar=False).preflight(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, es_postventa=True,
                                    recurso_ide=400)])
    assert [(a.destino, a.caa_cod) for a in pf.acciones] == [
        ("obra", "0678.CIMO03"), ("postventa", "POSTV2.CIMO02")]
    assert sorted(cli.de("cuentas")) == [(CEN_ORIGEN, 1, ["CIMO03"]),
                                         (CEN_PV, 1, ["CIMO02"])]


def test_f037_r4_modo_pruebas_una_lectura_del_centro_de_pruebas():
    cli = ClienteF037()
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, es_postventa=True,
                                    recurso_ide=400)])
    assert [a.caa_cod for a in pf.acciones] == ["0404.CIMO03",
                                                "0404.CIMO02"]
    assert cli.de("cuentas") == [(CEN_PRUEBAS, 1, ["CIMO02", "CIMO03"])]


def test_f037_r4_la_empresa_de_la_cuenta_es_la_de_la_obra():
    cli = ClienteF037()
    cli.obra.empresa = 28                   # dato del test, no del doble
    cli.obra_por_codigo = lambda cod, emp: (
        cli.obra if cod == "0404" else cli.obra_origen)
    _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    assert cli.de("cuentas") == [(CEN_PRUEBAS, 28, ["CIMO03"])]


# ====================== R5 · sin cuenta, se escribe ====================== #

def test_f037_r5_obra_sin_esa_cuenta_aviso_y_se_escribe_con_cero():
    cli = ClienteF037(cuentas={CEN_PRUEBAS: {}})
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    aviso = ("la obra 0404 no tiene la cuenta analitica .CIMO03: la linea "
             "ira sin cuenta")
    [ins] = cli.inserts()
    assert ins["caaide"] == 0 and res.escritas[0]["caa_cod"] is None
    assert res.pendientes_confirmacion == [] and res.omitidas == []
    pf = _pl(ClienteF037(cuentas={CEN_PRUEBAS: {}})).preflight(
        obra=OBRA, lineas=[linea()])
    (a,) = pf.acciones
    assert _caa(a) == (0, None, "obra_sin_cuenta", aviso, "recurso", None)
    assert a.aviso == aviso and pf.conflictos == []


def test_f037_r5_cuenta_ambigua_nunca_se_elige_la_primera():
    cli = ClienteF037(cuentas={CEN_PRUEBAS: {"CIMO03": [
        (701, "0404.CIMO03"), (702, "0404. CIMO03")]}})
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    [ins] = cli.inserts()
    assert ins["caaide"] == 0 and res.escritas[0]["caa_cod"] is None
    (a,) = _pl(ClienteF037(cuentas={CEN_PRUEBAS: {"CIMO03": [
        (701, "0404.CIMO03"), (702, "0404. CIMO03")]}})).preflight(
            obra=OBRA, lineas=[linea()]).acciones
    assert (a.caa_motivo, a.aviso) == (
        "cuenta_ambigua",
        "la obra 0404 tiene varias cuentas .CIMO03: la linea ira sin cuenta")


def test_f037_r5_recurso_sin_subcuenta_cero_sin_aviso():
    cli = ClienteF037()
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea(recurso_ide=SIN_CUENTA)])
    [ins] = cli.inserts()
    assert ins["caaide"] == 0
    assert res.escritas[0]["caa_cod"] is None and cli.de("cuentas") == []


# ======================== R6 · avisos sumados ======================== #

def test_f037_r6_el_aviso_de_cuenta_se_suma_al_de_sin_partida():
    cli = ClienteF037(cuentas={CEN_PRUEBAS: {}})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(categoria="Peon", nombre="Nadie Conocido", recurso_ide=400)])
    (a,) = pf.acciones
    assert a.paride == 0
    assert a.aviso == (
        f"{AVISO_SIN_PARTIDA} · la obra 0404 no tiene la cuenta analitica "
        ".CIMO02: la linea ira sin cuenta")
    assert [c.motivo for c in pf.conflictos] == ["sin_partida"]


def test_f037_r6_las_omitidas_no_reciben_cuenta():
    cli = ClienteF037()
    (a,) = _pl(cli).preflight(obra=OBRA,
                              lineas=[linea(recurso_ide=100)]).acciones
    assert a.accion == "omitir"
    assert _caa(a) == (0, None, None, None, None, None)
    assert cli.de("cuentas") == [] and cli.de("partidas") == []


# ==================== R7 · una lectura; si falla, nada ==================== #

def test_f037_r7_una_lectura_de_cuentas_por_centro_aunque_haya_dos_meses():
    cli = ClienteF037()
    _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1, mes=7), linea(registro_id=2, mes=8),
        linea(registro_id=3, mes=8, recurso_ide=400)])
    assert cli.de("cuentas") == [(CEN_PRUEBAS, 1, ["CIMO02", "CIMO03"])]


@pytest.mark.parametrize("lectura", ["cuentas", "partidas"])
def test_f037_r7_si_una_lectura_falla_la_peticion_falla_sin_escribir(
        lectura):
    cli = ClienteF037(falla={lectura})
    lineas = [linea(registro_id=1),
              linea(registro_id=2, recurso_ide=SIN_CUENTA)]
    with pytest.raises(RuntimeError, match=lectura):
        _pl(cli).ejecutar(obra=OBRA, lineas=lineas)
    assert cli.escritos == []
    with pytest.raises(RuntimeError):
        _pl(ClienteF037(falla={lectura})).preflight(obra=OBRA, lineas=lineas)


# ==================== R8 · centro de la obra destino ==================== #

def test_f037_r8_la_linea_va_al_centro_de_la_obra_destino_sin_cuaide():
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

    cli = ClienteF037()
    _pl(cli, forzar=False).ejecutar(obra=OBRA, lineas=[linea()])
    [ins] = cli.inserts()
    assert ins["obra"] is cli.obra_origen
    st = SigridWriteClient.stmt_insert_linea(
        SigridWriteClient(base_url="http://x", function_key="k",
                          database="ruesma"), **ins)
    assert st["parameters"][2] == CEN_ORIGEN          # hmores.cenide
    assert "cuaide" not in st["sql"]


# ================ R11 · correlativo de la empresa de la obra ================ #

def test_f037_r11_el_codigo_propuesto_es_el_de_la_empresa_de_la_obra():
    cli = ClienteF037(parte_existe=False)
    cli.obra.empresa = 28                   # dato del test, no del doble
    cli.obra_por_codigo = lambda cod, emp: (
        cli.obra if cod == "0404" else cli.obra_origen)
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    assert cli.de("siguiente") == [(2026, 28)]
    assert pf.partes[0].cod == "PT26/00350"
