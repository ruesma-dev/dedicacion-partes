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


# ======================= R9-R11, R15 · el parte ======================= #

PT_REG7 = ParteSigrid(7, "PT26/00007", REG)
PT_REG5 = ParteSigrid(5, "PT26/00005", REG)
PT_CER9 = ParteSigrid(9, "PT26/00009", CER)
PT_IMP4 = ParteSigrid(4, "PT26/00004", IMP)


def test_f037_r9_una_lectura_de_partes_por_destino_y_periodo():
    cli = ClienteF037()
    _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, recurso_ide=400),
        linea(registro_id=3, mes=8), linea(registro_id=4, recurso_ide=100)])
    assert cli.de("partes") == [(828942, 2026, 7), (828942, 2026, 8)]


def test_f037_r9_sin_acciones_escribir_no_se_leen_partes():
    cli = ClienteF037()
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea(recurso_ide=100)])
    assert cli.de("partes") == [] and pf.partes == []


def test_f037_r10_r15_en_registro_aunque_haya_un_cerrado_de_ide_mayor():
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7],
                      lineas_por_parte={})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    (p,) = pf.partes
    aviso = ("el parte PT26/00009 (Cerrado) de 07/2026 esta cerrado: las "
             "lineas van al parte complementario PT26/00007 (ya existe, en "
             "registro)")
    assert (p.existe, p.ide, p.cod, p.estado, p.complementario, p.cerrados,
            p.del_periodo, p.aviso, p.obra_cod) == (
        True, 7, "PT26/00007", REG, True, ["PT26/00009"],
        [PT_CER9, PT_REG7], aviso, "0404")
    assert pf.acciones[0].aviso == aviso            # R6: se suma
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert [i["hmoide"] for i in cli.inserts()] == [7]
    assert [s for s in cli.escritos if s["sql"] == "crear"] == []
    assert res.partes[0].aviso == aviso


def test_f037_r10_el_complementario_que_creo_partes_se_reutiliza():
    cli = ClienteF037(periodo=[ParteSigrid(11, "PT26/00350", REG), PT_IMP4],
                      lineas_por_parte={})
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert [i["hmoide"] for i in cli.inserts()] == [11]
    assert res.partes[0].complementario and not res.partes[0].creado
    assert cli.de("siguiente") == []


def test_f037_r10_r11_todos_cerrados_crea_el_complementario_parte_obra():
    nuevo = ParteSigrid(950, "PT26/00350", REG)
    cli = ClienteF037(periodo=[PT_IMP4], lineas_por_parte={},
                      tras_crear=[[nuevo, PT_IMP4]])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    aviso = ("el parte PT26/00004 (Imputado) de 07/2026 esta cerrado: las "
             "lineas van al parte complementario PT26/00350 (se creara)")
    (p,) = pf.partes
    assert (p.existe, p.cod, p.complementario, p.aviso) == (
        False, "PT26/00350", True, aviso)
    cli.cods = iter(["PT26/00350"])
    # Dos líneas del mismo parte nuevo: se crea UNA vez (T10).
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, recurso_ide=400)])
    [crear] = [s["parameters"] for s in cli.escritos if s["sql"] == "crear"]
    assert crear["desc"] == "Parte PRUEBAS (PRUEBA-PORC)"       # D13
    assert (crear["cod"], crear["obra"], crear["ano"], crear["mes"]) == (
        "PT26/00350", cli.obra, 2026, 7)
    assert [i["hmoide"] for i in cli.inserts()] == [950, 950]
    assert (res.partes[0].existe, res.partes[0].ide,
            res.partes[0].creado) == (True, 950, True)


def test_f037_r11_d13_en_modo_normal_la_descripcion_es_parte_obra():
    cli = ClienteF037(periodo=[], tras_crear=[[ParteSigrid(950, "PT26/00350",
                                                           REG)]])
    _pl(cli, forzar=False).ejecutar(obra=OBRA, lineas=[linea()])
    [crear] = [s["parameters"] for s in cli.escritos if s["sql"] == "crear"]
    assert crear["desc"] == "Parte 15 VIVIENDAS"
    assert crear["obra"] is cli.obra_origen


def test_f037_r10_sin_partes_del_periodo_parte_nuevo_sin_aviso():
    cli = ClienteF037(periodo=[])
    (p,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).partes
    assert (p.existe, p.complementario, p.aviso, p.cod) == (
        False, False, None, "PT26/00350")
    assert cli.de("lineas") == []           # nada que mirar


def test_f037_d17_si_otro_servicio_creo_el_parte_a_la_vez_se_usa_el_suyo():
    suyo = ParteSigrid(951, "PT26/00360", REG)
    cli = ClienteF037(periodo=[], tras_crear=[[suyo]])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert [i["hmoide"] for i in cli.inserts()] == [951]
    assert (res.partes[0].cod, res.partes[0].creado) == ("PT26/00360", False)
    assert len([s for s in cli.escritos if s["sql"] == "crear"]) == 1


def test_f037_r11_d17_codigo_ocupado_reintenta_una_vez_con_otro_codigo():
    nuevo = ParteSigrid(952, "PT26/00351", REG)
    cli = ClienteF037(periodo=[PT_IMP4], lineas_por_parte={},
                      tras_crear=[[PT_IMP4], [nuevo, PT_IMP4]])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    crear = [s["parameters"]["cod"] for s in cli.escritos
             if s["sql"] == "crear"]
    assert crear == ["PT26/00350", "PT26/00351"]
    assert cli.de("siguiente") == [(2026, 1), (2026, 1)]
    assert [i["hmoide"] for i in cli.inserts()] == [952]
    assert res.partes[0].creado is True


def test_f037_r11_d17_sin_parte_en_registro_tras_reintentar_falla_sin_lineas():
    cli = ClienteF037(periodo=[PT_IMP4], lineas_por_parte={},
                      tras_crear=[[PT_IMP4], [PT_IMP4], [PT_IMP4]])
    with pytest.raises(RuntimeError, match="no se pudo crear el parte"):
        _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert len([s for s in cli.escritos if s["sql"] == "crear"]) == 2
    assert len(cli.de("siguiente")) == 2        # preflight + UN reintento
    assert cli.inserts() == [] and cli.borrados() == []


# ================== R12-R14, R17 · todos los partes del periodo ================== #

def _previa(ide: int, **kw) -> LineaSigrid:
    """Línea ajena con la MISMA identidad que `linea()` (MENC, CI.1.10)."""
    return linea_previa(ide=ide, paride=80001, **kw)


def test_f037_r12_synckey_en_un_parte_cerrado_es_ya_registrado():
    hit = _previa(6001, synckey=synckey_de(1), nuestra=True)
    setattr(hit, "hmoide", 9)
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7],
                      synckeys={synckey_de(1): hit},
                      lineas_por_parte={9: [hit]})
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert res.ya_registradas == [1]
    assert cli.escritos == []               # ni se reescribe ni se rellena
    # Sin acciones `escribir` en el periodo no hay líneas que mirar (T10).
    assert cli.de("lineas") == []


def test_f037_r13_choque_con_un_parte_cerrado_se_omite_sin_cuenta():
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7],
                      lineas_por_parte={9: [_previa(6001)], 7: []})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    (a,) = pf.acciones
    assert a.accion == "omitir"
    assert a.motivo == ("parte_cerrado: ya hay horas de ese recurso, dia y "
                        "tipo en el parte PT26/00009 (Cerrado); no se "
                        "registran")
    assert _caa(a) == (0, None, None, None, None, None)
    assert pf.conflictos == []
    assert sorted(cli.de("lineas")) == [(7,), (9,)]
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert cli.escritos == [] and res.escritas == []
    assert res.omitidas == [{"registro_id": 1, "motivo": a.motivo}]


def test_f037_r13_choque_con_cerrado_aunque_el_elegido_sea_nuevo():
    cli = ClienteF037(periodo=[PT_IMP4],
                      lineas_por_parte={4: [_previa(6001)]})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    assert pf.acciones[0].accion == "omitir"
    assert "PT26/00004 (Imputado)" in pf.acciones[0].motivo
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert cli.escritos == [] and res.escritas == []


def test_f037_r13_el_cerrado_prevalece_sobre_el_en_registro():
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7],
                      lineas_por_parte={7: [_previa(6002)],
                                        9: [_previa(6001)]})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    assert pf.acciones[0].accion == "omitir" and pf.conflictos == []
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()],
                            pisar_claves={"200|202607|5|80001"})
    assert cli.borrados() == [] and res.borradas == 0


def test_f037_r13_choque_en_registro_es_conflicto_con_el_parte_donde_vive():
    cli = ClienteF037(periodo=[PT_REG7, PT_REG5],
                      lineas_por_parte={5: [_previa(6005)]})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    (c,) = pf.conflictos
    assert (c.motivo, c.parte_cod, [ls.ide for ls in c.lineas]) == (
        "pisado", "PT26/00005", [6005])
    assert pf.partes[0].cod == "PT26/00007"
    # R14: confirmado, se borra (parte En registro) y se escribe en el 7.
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()],
                            pisar_claves={c.clave})
    assert cli.borrados() == [6005] and res.borradas == 1
    assert [i["hmoide"] for i in cli.inserts()] == [7]
    assert cli.inserts()[0]["caaide"] == 90001        # R17: con su cuenta


def test_f037_r13_sin_partida_que_choca_con_cerrado_solo_se_omite():
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7], lineas_por_parte={
        9: [linea_previa(ide=6001, reside=400, horide=6,
                         hora_codigo="MJEFO", paride=0)]})
    lin = linea(recurso_ide=400, categoria="Peon", nombre="Nadie Conocido")
    pf = _pl(cli).preflight(obra=OBRA, lineas=[lin])
    assert pf.acciones[0].accion == "omitir" and pf.conflictos == []
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[lin])
    assert [o["registro_id"] for o in res.omitidas] == [1]
    assert res.pendientes_confirmacion == []


def test_f037_r13_la_capacidad_suma_las_lineas_del_parte_cerrado():
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7], lineas_por_parte={
        9: [linea_previa(ide=6001, can=0.7, paride=80002)], 7: []})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    (c,) = pf.conflictos
    assert (c.motivo, c.suma_existente, c.suma_total) == (
        "sobrecarga", 0.7, 1.1)
    assert [ls.ide for ls in c.contexto] == [6001]
    assert pf.acciones[0].accion == "escribir"


def test_f037_r13_la_capacidad_no_cuenta_la_accion_omitida_por_cerrado():
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7], lineas_por_parte={
        9: [_previa(6001, can=0.9)]})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1, porcentaje=0.4),
        linea(registro_id=2, porcentaje=0.05, paride=80002,
              partida_cod="CI.1.20")])
    assert [a.accion for a in pf.acciones] == ["omitir", "escribir"]
    assert pf.conflictos == []              # 0.9 + 0.05: cabe


@pytest.mark.parametrize("lectura", ["partes", "lineas"])
def test_f037_r16_si_falla_la_lectura_del_periodo_no_se_escribe(lectura):
    cli = ClienteF037(periodo=[PT_REG7], falla={lectura})
    with pytest.raises(RuntimeError, match=lectura):
        _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert cli.escritos == []


def test_f037_r17_solo_se_crean_partes_y_se_insertan_o_borran_lineas():
    cli = ClienteF037(periodo=[PT_IMP4], lineas_por_parte={},
                      tras_crear=[[ParteSigrid(950, "PT26/00350", REG)]])
    _pl(cli).ejecutar(obra=OBRA, lineas=[linea(registro_id=1),
                                         linea(registro_id=2, mes=8)])
    assert {s["sql"] for s in cli.escritos} <= {"crear", "insert", "delete"}
    assert all(i["hmoide"] != 4 for i in cli.inserts())


def test_f037_r15_el_contrato_http_de_partes_y_acciones_es_aditivo():
    """La app serializa con `asdict`: los campos nuevos viajan solos."""
    import dataclasses

    cli = ClienteF037(periodo=[PT_CER9, PT_REG7], lineas_por_parte={})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    parte = dataclasses.asdict(pf.partes[0])
    assert {"estado", "complementario", "cerrados", "del_periodo",
            "aviso", "obra_cod", "cod", "ide", "existe"} <= set(parte)
    assert parte["del_periodo"] == [
        {"ide": 9, "cod": "PT26/00009", "est": CER},
        {"ide": 7, "cod": "PT26/00007", "est": REG}]
    accion = dataclasses.asdict(pf.acciones[0])
    assert {"caa_ide", "caa_cod", "caa_motivo", "caa_aviso", "caa_origen",
            "caa_nota", "aviso", "motivo"} <= set(accion)


# ============= T10 · casos que la campaña de mutación dejó vivos ============= #

def test_f037_r3_una_linea_sin_partida_no_hereda_la_de_otra():
    """`paride = 0` no es una partida: nunca toma la cuenta de otra línea,
    aunque esa otra sea la partida de `ide` 1."""
    cli = ClienteF037(partidas={1: PartidaCuenta(1, "CI.9", "0678.CIMO04")})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1, recurso_ide=SIN_CUENTA, paride=1,
              partida_cod="CI.9"),
        linea(registro_id=2, recurso_ide=SIN_CUENTA, categoria="Peon",
              nombre="Nadie Conocido")])
    assert [(a.paride, a.caa_origen, a.caa_cod) for a in pf.acciones] == [
        (1, "partida", "0404.CIMO04"), (0, None, None)]


@pytest.mark.parametrize("sin_centro", ["sin_atributo", "cero"])
def test_f037_r4_obra_sin_centro_no_lee_cuentas_y_avisa(sin_centro):
    cli = ClienteF037()
    if sin_centro == "sin_atributo":
        delattr(cli.obra, "cenide")
    else:
        cli.obra.cenide = 0
    (a,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).acciones
    assert cli.de("cuentas") == []
    assert (a.caa_ide, a.caa_motivo) == (0, "obra_sin_cuenta")


def test_f037_r7_el_log_cuenta_las_lineas_por_origen(caplog):
    cli = ClienteF037(partidas={80001: PartidaCuenta(80001, "CI.1.10",
                                                     "0678.CIMO03")})
    with caplog.at_level("INFO",
                         logger="application.pipelines.registro_pipeline"):
        _pl(cli).preflight(obra=OBRA, lineas=[
            linea(registro_id=1), linea(registro_id=2, recurso_ide=400),
            linea(registro_id=3, recurso_ide=SIN_CUENTA)])
    assert ("[registro] cuenta analitica obra=0404 recurso=2 partida=1 "
            "ninguna=0") in caplog.messages
