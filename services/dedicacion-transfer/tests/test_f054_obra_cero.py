# tests/test_f054_obra_cero.py
"""F-054 · parte B: la obra sin nada en la plataforma es un 0 % (R31-R34,
R36, R38; design §6.1-§6.2).

T11 (`-k reglas`): `reglas_obra_cero.py`, puro. Una línea mensual de
Sigrid de un recurso del lote es **sobrante** si ninguna acción de ese
recurso (en cualquier estado, también omitida) la cubre: normal, si alguna
va a esa obra; en la obra de postventa, si alguna de postventa resolvió esa
partida; en la VAR, si alguna tiene ese `var_paride`. En pruebas solo
cuentan las de la 0404, cubiertas si se reconocen (ya registrada, choque,
al 0) o alguna acción tiene su partida. Los vinculados, igual con sus
`AccionVinculado`. Parte cerrado o `synckey` de otro sistema ⇒ no
confirmable, con motivo; la nuestra huérfana y la `porcentajes:vin:`, sí.

T12 (`-k lote`): la lectura en la ronda A de `precargar` y
`RegistroLote.preflight_completo`.

Sin red ni BBDD.
"""
from __future__ import annotations

from application.services.reglas_obra_cero import (
    MOTIVO_CERRADO,
    MOTIVO_OTRO_SISTEMA,
    Cobertura,
    coberturas_de,
    confirmable,
    cubierta,
    reconocidas_de,
    sobrantes,
)
from domain.models.registro_models import (
    AccionLinea,
    AccionVinculado,
    Conflicto,
    LineaEntrada,
    LineaMensualSigrid,
    LineaSigrid,
    ObraEntrada,
    Preflight,
    Sobrante,
    VinculadoEntrada,
)

PV, VAR, PRU = "POSTV2", "VAR", "0404"
AJ = {"cod_pv": PV, "cod_var": VAR, "cod_pruebas": PRU}


def _m(ide, recurso=10, obra=694, cod=None, *, paride=0, hora="MADM",
       est=1, en_registro=True, synckey=None, can=0.2):
    return LineaMensualSigrid(
        hmores_ide=ide, recurso_ide=recurso, obra_ide=obra,
        obra_cod=cod or f"{obra:04d}", parte_ide=500 + obra,
        parte_cod=f"PT26/{obra}", parte_est=est, en_registro=en_registro,
        hora=hora, can=can, fec=20260930, paride=paride,
        partida_cod=f"P{paride}" if paride else None, synckey=synckey)


def _cub(lineas, cob, *, pruebas=False, reconocidas=()):
    return cubierta(lineas, cob, cod_pv=PV, cod_var=VAR,
                    modo_pruebas=pruebas, reconocidas=set(reconocidas))


# --------------------------------- reglas -------------------------------- #
def test_f054_r31_reglas_normal_cubierta_si_alguna_va_a_esa_obra():
    assert _cub(_m(1), [Cobertura(694, "obra", 0, None)])
    assert not _cub(_m(1), [Cobertura(713, "obra", 0, None)])
    # Una de postventa o VAR a esa obra no cubre la normal.
    assert not _cub(_m(1), [Cobertura(694, "postventa", 0, None)])
    assert not _cub(_m(1), [Cobertura(694, "obra", 7, 7)])
    assert not _cub(_m(1), [])


def test_f054_r31_reglas_postventa_por_la_partida_resuelta():
    linea = _m(2, obra=999001, cod=PV, paride=81)
    assert _cub(linea, [Cobertura(694, "postventa", 81, None)])
    assert not _cub(linea, [Cobertura(694, "postventa", 82, None)])
    assert not _cub(linea, [Cobertura(999001, "obra", 81, None)])


def test_f054_r31_reglas_var_por_su_var_paride():
    linea = _m(3, obra=777, cod=VAR, paride=2105)
    assert _cub(linea, [Cobertura(777, "obra", 0, 2105)])
    assert not _cub(linea, [Cobertura(777, "obra", 2105, None)])
    assert not _cub(linea, [Cobertura(777, "obra", 0, 2106)])


def test_f054_r32_reglas_en_pruebas_reconocida_o_con_su_partida():
    linea = _m(4, obra=404, cod=PRU, paride=33)
    assert _cub(linea, [], pruebas=True, reconocidas={4})
    assert _cub(linea, [Cobertura(404, "obra", 33, None)], pruebas=True)
    assert not _cub(linea, [Cobertura(404, "obra", 34, None)], pruebas=True)
    # En pruebas no basta con ir a la obra.
    assert not _cub(linea, [Cobertura(404, "obra", 0, None)], pruebas=True)


def test_f054_r34_reglas_confirmable():
    assert confirmable(_m(1)) == (True, None)
    assert confirmable(_m(1, synckey="porcentajes:77")) == (True, None)
    assert confirmable(_m(1, synckey="porcentajes:vin:77:5000")) == (True,
                                                                     None)
    assert confirmable(_m(1, en_registro=False, est=3)) == (
        False, MOTIVO_CERRADO.format(parte="PT26/694"))
    assert confirmable(_m(1, synckey="partes:9")) == (
        False, MOTIVO_OTRO_SISTEMA.format(synckey="partes:9"))
    assert MOTIVO_CERRADO.format(parte="X") == "el parte X no está En registro"
    assert MOTIVO_OTRO_SISTEMA.format(synckey="s") == (
        "la línea es de otro sistema (synckey s)")


def _sob(mensuales, cob, **kw):
    return sobrantes(mensuales, cob, vinculados=kw.pop("vinculados", {}),
                     reconocidas=set(kw.pop("reconocidas", ())),
                     excluidos=set(kw.pop("excluidos", ())),
                     modo_pruebas=kw.pop("pruebas", False), **AJ)


def test_f054_r31_r33_reglas_sobrantes_ordenados_con_su_clave():
    cob = {10: [Cobertura(694, "obra", 0, None)], 20: []}
    r = _sob([_m(9, obra=713, paride=5, synckey="partes:1"), _m(1),
              _m(3, recurso=20, obra=694, en_registro=False, est=3),
              _m(2, recurso=99, obra=713)], cob)
    assert [s.hmores_ide for s in r] == [3, 9]
    assert r[1] == Sobrante(
        clave="cero:9", hmores_ide=9, recurso_ide=10, vinculado=None,
        obra_ide=713, obra_cod="0713", parte_cod="PT26/713", parte_est=1,
        hora="MADM", paride=5, partida_cod="P5", can=0.2,
        synckey="partes:1", confirmable=False,
        motivo="la línea es de otro sistema (synckey partes:1)")
    assert (r[0].confirmable, r[0].motivo) == (
        False, "el parte PT26/694 no está En registro")


def test_f054_d14_reglas_recurso_sin_lineas_en_el_lote_o_excluido_fuera():
    cob = {10: []}
    assert _sob([_m(1, recurso=20)], cob) == []
    assert _sob([_m(1)], cob, excluidos={10}) == []
    assert [s.hmores_ide for s in _sob([_m(1)], cob)] == [1]


def test_f054_r31_reglas_mesve_del_vinculado_no_es_del_trabajador():
    """La `MESVE` de su vinculado en el mismo parte es de OTRO recurso: no
    es sobrante del trabajador (ni del vinculado si no va en el lote)."""
    cob = {10: [Cobertura(694, "obra", 0, None)]}
    assert _sob([_m(5, recurso=5000, obra=713, hora="MESVE")], cob) == []


def test_f054_r32_reglas_en_pruebas_solo_las_de_la_0404():
    cob = {10: [Cobertura(404, "obra", 0, None)]}
    r = _sob([_m(1, obra=713), _m(2, obra=404, cod=PRU, paride=33),
              _m(3, obra=404, cod=PRU, paride=34)], cob, pruebas=True,
             reconocidas={3})
    assert [s.hmores_ide for s in r] == [2]


def test_f054_r38_reglas_vinculado_con_sus_acciones_y_su_dato():
    cob = {10: [Cobertura(694, "obra", 0, None)],
           5000: [Cobertura(694, "obra", 81, None)]}
    vin = {5000: {"tipo": "TF", "cod": "TEL1", "titular_ide": 10}}
    r = _sob([_m(1, recurso=5000, obra=694, hora="MESVE"),
              _m(2, recurso=5000, obra=713, hora="OTEL",
                 synckey="porcentajes:vin:4:5000")], cob, vinculados=vin)
    assert [(s.hmores_ide, s.vinculado, s.hora, s.confirmable)
            for s in r] == [(2, vin[5000], "OTEL", True)]


def _pf(acciones=(), vinculados=(), conflictos=(), obra=694):
    return Preflight(obra_destino=ObraEntrada(ide=obra, codigo=f"{obra:04d}"),
                     obra_origen=ObraEntrada(ide=obra), forzada_pruebas=False,
                     acciones=list(acciones), vinculados=list(vinculados),
                     conflictos=list(conflictos))


def _a(rid, recurso, accion="escribir", **kw):
    return AccionLinea(registro_id=rid, accion=accion, ano=2026, mes=9,
                       fecha_int=20260930, recurso_ide=recurso, **kw)


def test_f054_r31_reglas_coberturas_de_toda_accion_tambien_omitida():
    lineas = [LineaEntrada(registro_id=1, ano=2026, mes=9, porcentaje=0.5,
                           recurso_ide=10),
              LineaEntrada(registro_id=2, ano=2026, mes=9, porcentaje=0.5,
                           recurso_ide=10, var_paride=2105, vinculados=[
                               VinculadoEntrada(recurso_ide=5000)])]
    pf = _pf([_a(1, 10, "omitir", motivo="x"),
              _a(2, 10, paride=2105, destino="obra")],
             [AccionVinculado(registro_id=2, recurso_ide=5000,
                              accion="omitir", ano=2026, mes=9,
                              fecha_int=20260930, paride=0)])
    assert coberturas_de(pf, lineas) == {
        10: [Cobertura(694, "obra", 0, None), Cobertura(694, "obra", 2105,
                                                        2105)],
        5000: [Cobertura(694, "obra", 0, 2105)]}


def test_f054_r32_reglas_reconocidas_ya_registrada_cero_y_choque():
    pf = _pf([_a(1, 10, "ya_registrado", hmores_ide=11),
              _a(2, 10, linea_cero={"ide": 12})],
             [AccionVinculado(registro_id=1, recurso_ide=5000,
                              accion="ya_registrado", ano=2026, mes=9,
                              fecha_int=20260930, hmores_ide=13)],
             [Conflicto(clave="k", recurso_ide=10, nombre=None, ano=2026,
                        mes=9, parte_cod=None, edita_ide=14,
                        a_cero_ides=[15], lineas=[LineaSigrid(
                            ide=16, reside=10, fecha_int=1, horide=None,
                            hora_codigo=None, can=0, tot=0, synckey=None)])])
    assert reconocidas_de(pf) == {11, 12, 13, 14, 15, 16}


# ---------------------------------- lote --------------------------------- #
from dataclasses import asdict

from application.pipelines.registro_lote import RegistroLote
from interface_adapters.api.app import _respuesta_preflight

from tests import test_f055_lote as lote_f055
from tests.conftest import linea, linea_previa
from tests.test_f055_lote import (
    ClienteObras,
    _ajustes,
    _con_partida,
    _json_linea,
    _obra,
)

#: La fixture de F-055, aquí con el mismo nombre.
api = lote_f055.api

LECTURA = "lineas_mensuales_del_periodo"


class ClienteMensual(ClienteObras):
    """`ClienteObras` de F-055 con la lectura de §4.1, anotada y filtrada
    por recurso (y `M*` si `solo_m`), como la real."""

    def __init__(self, n: int = 2, mensuales=(), **kw) -> None:
        self.lineas_mensuales = list(mensuales)
        super().__init__(n, **kw)

    def lineas_mensuales_del_periodo(self, empresa, ano, mes, resides=None,
                                     solo_m=True):
        self.llamadas.append((LECTURA, empresa, ano, mes,
                              tuple(resides or ()), solo_m))
        return [l for l in self.lineas_mensuales
                if l.recurso_ide in set(resides or ())
                and (not solo_m or (l.hora or "").startswith("M"))]


def _mes(ide, obra, cod, paride=0, recurso=200, **kw):
    return LineaMensualSigrid(
        hmores_ide=ide, recurso_ide=recurso, obra_ide=obra, obra_cod=cod,
        parte_ide=1, parte_cod="PT26/1", parte_est=1, en_registro=True,
        hora=kw.pop("hora", "MENC"), can=kw.pop("can", 0.3), fec=20260731,
        paride=paride, **kw)


def _completo(cli, peticiones, **kw):
    return RegistroLote(cliente=cli, settings=_ajustes(**kw)) \
        .preflight_completo(peticiones)


def test_f054_r31_lote_una_lectura_mas_y_en_la_ronda_a():
    peticiones = [(_obra(1), [_con_partida(1)]),
                  (_obra(2), [_con_partida(2, registro_id=2)])]
    solo = ClienteMensual()
    RegistroLote(cliente=solo, settings=_ajustes()).preflight(peticiones)
    cli = ClienteMensual()
    _completo(cli, peticiones)
    assert LECTURA not in solo.nombres()
    assert sorted(cli.nombres()) == sorted([*solo.nombres(), LECTURA])
    assert [c for c in cli.llamadas if c[0] == LECTURA] == [
        (LECTURA, 1, 2026, 7, (200,), True)]
    nombres = cli.nombres()
    ronda_b = [i for i, n in enumerate(nombres)
               if n in ("partes_de_periodos", "validar_partidas")]
    assert ronda_b and nombres.index(LECTURA) < min(ronda_b)


def test_f054_r38_lote_con_vinculados_dos_lecturas_y_sin_ellos_ninguna():
    con = [VinculadoEntrada(recurso_ide=5000, tipo="TF", cod="TEL1")]
    cli = ClienteMensual()
    _completo(cli, [(_obra(1), [_con_partida(1, vinculados=con)])])
    assert [c for c in cli.llamadas if c[0] == LECTURA] == [
        (LECTURA, 1, 2026, 7, (200,), True),
        (LECTURA, 1, 2026, 7, (5000,), False)]
    cli = ClienteMensual()
    _completo(cli, [(_obra(1), [_con_partida(1)])])
    assert all(c[5] is True for c in cli.llamadas if c[0] == LECTURA)


def test_f054_r31_lote_mismos_preflights_tambien_con_cuatro_elementos():
    peticiones = [(_obra(1), [_con_partida(1)], [], None),
                  (_obra(2), [_con_partida(2, registro_id=2)])]
    normal = RegistroLote(cliente=ClienteMensual(),
                          settings=_ajustes()).preflight(peticiones)
    completos, _ = _completo(ClienteMensual(), peticiones)
    assert [_respuesta_preflight(r) for r in completos] == [
        _respuesta_preflight(r) for r in normal]


def test_f054_r32_r33_lote_en_pruebas_una_por_linea_con_su_clave():
    cli = ClienteMensual(mensuales=[
        _mes(7003, 828942, "0404", paride=700001),
        _mes(7001, 828942, "0404", paride=9),
        _mes(7002, 600002, "O002", paride=9)])
    _, sob = _completo(cli, [(_obra(1), [_con_partida(1)])])
    assert [s.clave for s in sob] == ["cero:7001"]
    assert asdict(sob[0])["vinculado"] is None


def test_f054_r31_lote_en_real_por_obra_y_el_que_falla_no_da():
    cli = ClienteMensual(mensuales=[
        _mes(7001, 600001, "O001"), _mes(7002, 600002, "O002"),
        _mes(7003, 600002, "O002", recurso=400)])
    _, sob = _completo(cli, [
        (_obra(1), [_con_partida(1)]),
        (ObraEntrada(ide=600099), [linea(registro_id=9, recurso_ide=400)])],
        obra_pruebas_forzar=False)
    assert [s.hmores_ide for s in sob] == [7002]


def test_f054_r38_lote_sobrante_de_vinculado_con_su_dato():
    con = [VinculadoEntrada(recurso_ide=5000, tipo="TF", cod="TEL1")]
    cli = ClienteMensual(mensuales=[
        _mes(7005, 600002, "O002", recurso=5000, hora="OTEL")])
    _, sob = _completo(cli, [(_obra(1), [_con_partida(1, vinculados=con)])],
                       obra_pruebas_forzar=False)
    assert [(s.hmores_ide, s.vinculado, s.hora) for s in sob] == [
        (7005, {"tipo": "TF", "cod": "TEL1", "titular_ide": 200}, "OTEL")]


def test_f054_r36_lote_la_sobrante_suma_en_la_capacidad_del_parte():
    """En pruebas todo va a la 0404: la sobrante de ese parte cuenta como
    otra línea suya al medir la jornada (`#regla-capacidad`)."""
    cli = ClienteMensual(mensuales=[_mes(7001, 828942, "0404", paride=9,
                                         can=0.7)])
    cli.lineas_parte = [linea_previa(ide=7001, reside=200, can=0.7,
                                     paride=9, fecha_int=20260731)]
    [pf], sob = _completo(cli, [(_obra(1), [_con_partida(
        1, porcentaje=0.5)])])
    [c] = [c for c in pf.conflictos if c.motivo == "sobrecarga"]
    assert (c.suma_existente, c.suma_total) == (0.7, 1.2)
    assert [s.hmores_ide for s in sob] == [7001]


def test_f054_r31_lote_ruta_sin_completo_como_hoy_y_con_el_sobrantes(api):
    peticiones = [{"obra": {"ide": 600001}, "lineas": [_json_linea(
        1, paride=700001, partida_cod="CI.1")]}]
    mensuales = [_mes(7001, 828942, "0404", paride=9)]
    cli = ClienteMensual(mensuales=mensuales)
    hoy = api(cli).post("/api/registro/preflight-lote",
                        json={"peticiones": peticiones}).json()
    assert "sobrantes" not in hoy and LECTURA not in cli.nombres()
    sin = api(ClienteMensual(mensuales=mensuales)).post(
        "/api/registro/preflight-lote",
        json={"peticiones": peticiones, "completo": False}).json()
    assert sin == hoy
    con = api(ClienteMensual(mensuales=mensuales)).post(
        "/api/registro/preflight-lote",
        json={"peticiones": peticiones, "completo": True}).json()
    assert con["obras"] == hoy["obras"]
    assert con["sobrantes"] == [{
        "clave": "cero:7001", "hmores_ide": 7001, "recurso_ide": 200,
        "vinculado": None, "obra_ide": 828942, "obra_cod": "0404",
        "parte_cod": "PT26/1", "parte_est": 1, "hora": "MENC",
        "paride": 9, "partida_cod": None, "can": 0.3, "synckey": None,
        "confirmable": True, "motivo": None}]


# ---------- O2: la postventa omitida antes de resolverse (review 1) -------- #
def _postv(rid, recurso=10, **kw):
    return LineaEntrada(registro_id=rid, ano=2026, mes=9, porcentaje=0.5,
                        recurso_ide=recurso, es_postventa=True, **kw)


def test_f054_r31_o2_postventa_omitida_sigue_siendo_de_postventa():
    """`omitir` deja `destino="obra"` y `paride=0` en una `Postv-` sin
    partida: la cobertura es de postventa, también la de su vinculado."""
    lineas = [_postv(1, vinculados=[VinculadoEntrada(recurso_ide=5000)])]
    pf = _pf([_a(1, 10, "omitir", motivo="postventa off", es_postventa=True)],
             [AccionVinculado(registro_id=1, recurso_ide=5000,
                              accion="omitir", ano=2026, mes=9,
                              fecha_int=20260930, destino="obra")])
    assert coberturas_de(pf, lineas) == {
        10: [Cobertura(694, "postventa", 0, None)],
        5000: [Cobertura(694, "postventa", 0, None)]}


def test_f054_r31_o2_sin_resolver_cubre_la_obra_de_postventa_sin_la_de_origen():
    cob = [Cobertura(694, "postventa", 0, None)]
    assert _cub(_m(1, obra=999, cod=PV, paride=33), cob)
    assert _cub(_m(2, obra=999, cod=PV, paride=0), cob)
    assert not _cub(_m(3, obra=694), cob)


def test_f054_r31_o2_resuelta_solo_cubre_su_partida():
    cob = [Cobertura(694, "postventa", 33, None)]
    assert _cub(_m(1, obra=999, cod=PV, paride=33), cob)
    assert not _cub(_m(2, obra=999, cod=PV, paride=34), cob)
    assert not _cub(_m(3, obra=999, cod=PV, paride=0), cob)


def test_f054_r31_o2_lote_postventa_apagada_de_punta_a_punta():
    """Con `POSTVENTA_REGISTRAR=false`: la línea real de postventa no sale
    y la normal de la obra de origen, que la plataforma no da, sí."""
    cli = ClienteMensual(mensuales=[
        _mes(7001, 999, "POSTV2", paride=9), _mes(7002, 600001, "O001")])
    _, sob = _completo(
        cli, [(_obra(1), [linea(es_postventa=True)])],
        obra_pruebas_forzar=False, postventa_registrar=False)
    assert [s.hmores_ide for s in sob] == [7002]
