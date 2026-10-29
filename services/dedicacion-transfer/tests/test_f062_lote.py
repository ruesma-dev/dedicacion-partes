# tests/test_f062_lote.py
"""F-062 · Las rachas en el lote de F-055 (R19, R20, R26; design §8).

Sin red ni BBDD: el `ClienteInc` de los tests de F-030 con las líneas de
incidencia de ``lineas_incidencia`` (la lectura en ventana del
`ClienteFalso` de `conftest.py`). Los `ide` son inventados y no coinciden
con ningún dato real.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.lecturas_lote import LecturasDelLote
from domain.models.registro_models import ContextoRachas, ObraEntrada

from tests.conftest import OBRA_SIN_PARTIDA_PV, SettingsFalso, linea
from tests.test_f062_pipeline_rachas import OBRA, ClienteInc, _cli, _inc, _l

OBRA_B = ObraEntrada(codigo=OBRA_SIN_PARTIDA_PV)
#: En pruebas, solo las de la obra de pruebas (`conftest.py`).
PRUEBAS = 828942


def _st(pruebas: bool) -> SettingsFalso:
    st = SettingsFalso(obra_pruebas_forzar=pruebas)
    st.sigrid_lecturas_paralelas = 4
    return st


def _lineas(obride):
    """Una racha de 5-9 de octubre del 200 ya registrada en `obride` y un
    inicio de agosto del 400 sin cerrar (D14), de Administración."""
    return [_l(51, 20261005, sk="porcentajes:inc:7:ini", hmoide=777,
               parte="PT26/00251", obride=obride),
            _l(52, 20261009, "CIZ", sk="porcentajes:inc:7:fin", hmoide=777,
               parte="PT26/00251", obride=obride),
            _l(61, 20260815, reside=400, obride=obride, cenide=555101,
               paride=0, caaide=0, parte_emp=1)]


def _peticiones():
    traza = {"hmores_ide_ini": 51, "dia_ini": 5, "hmores_ide_fin": 52,
             "dia_fin": 9}
    inc7 = _inc(7, 5, 9, **traza)
    return [
        (OBRA, [linea(registro_id=1, mes=10)], [inc7, _inc(8, 12, 16)],
         ContextoRachas(incidencias_mes=[inc7, _inc(8, 12, 16)],
                        cierres_recursos=[200])),
        (OBRA_B, [linea(registro_id=2, mes=10, recurso_ide=400)], [],
         ContextoRachas(cierres_recursos=[400])),
        (OBRA, [linea(registro_id=3, mes=10)]),
    ]


def _suelto(cli, p, st):
    obra, lineas, *resto = p
    ctx = resto[1] if len(resto) > 1 else None
    pipe = RegistroPipeline(cliente=cli, settings=st, contexto=ctx)
    kw = {"incidencias": resto[0]} if resto and resto[0] else {}
    return pipe.preflight(obra=obra, lineas=lineas, **kw)


@pytest.mark.parametrize("pruebas", [True, False])
def test_f062_r20_lote_una_lectura_y_lo_mismo_que_suelto(pruebas):
    from interface_adapters.api.app import _respuesta_preflight

    obride = PRUEBAS if pruebas else 555001
    cli = _cli(_lineas(obride))
    st = _st(pruebas)
    lote = RegistroLote(cliente=cli, settings=st).preflight(_peticiones())
    # R19-R20: UNA lectura por lote, en la ronda C, con los recursos de las
    # incidencias y de los designados y los `ide` de las trazas.
    assert cli.leidas_ventana == [
        ([200, 400], 20251001, 20261130, PRUEBAS if pruebas else None,
         [51, 52])]
    for p, r in zip(_peticiones(), lote):
        suelto = _suelto(_cli(_lineas(obride)), p, st)
        assert _respuesta_preflight(r, True) == _respuesta_preflight(
            suelto, True)
    a, b, _ = lote
    assert [x.accion for x in a.incidencias] == [
        "ya_registrado", "editar", "continua", "continua"]
    assert [(c.recurso_ide, c.fecha_int) for c in b.cierres_racha] == [
        (400, 20260930)]


def test_f062_r20_lote_sin_fallos_de_memoria_y_ronda_d_solo_con_d14():
    cli = _cli(_lineas(555001))
    cli.periodos = []
    partes = cli.partes_de_periodos

    def contar(obrides, periodos):
        cli.periodos.append((sorted(obrides), sorted(periodos)))
        return partes(obrides, periodos)
    cli.partes_de_periodos = contar
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar(_peticiones(), _st(False))
    # Ronda B: los del periodo; ronda D: los de M−1 de la obra del inicio
    # de agosto (D14), solo por ese cierre.
    assert cli.periodos == [([555001, 555002], [(2026, 10)]),
                            ([555001], [(2026, 9)])]
    for p in _peticiones():
        _suelto(memoria, p, _st(False))
    assert memoria.fallos_de_memoria == {}
    assert len(cli.leidas_ventana) == 1 and len(cli.periodos) == 2


def test_f062_r20_lote_sin_cierres_d14_no_hay_ronda_d():
    cli = _cli(_lineas(555001)[:2])
    cli.periodos = []
    partes = cli.partes_de_periodos

    def contar(obrides, periodos):
        cli.periodos.append((sorted(obrides), sorted(periodos)))
        return partes(obrides, periodos)
    cli.partes_de_periodos = contar
    LecturasDelLote(cli, 2).precargar(_peticiones(), _st(False))
    assert cli.periodos == [([555001, 555002], [(2026, 10)])]


def test_f062_r26_lote_sin_nada_que_escribir_cerrar_ni_devolver_no_lee():
    cli = _cli()
    lote = RegistroLote(cliente=cli, settings=_st(False)).preflight([
        (OBRA, [linea(registro_id=1, mes=10)], [_inc(7, 5, 9, recurso_ide=300)]),
        (OBRA, [linea(registro_id=2, mes=10)], [], ContextoRachas()),
        (OBRA, [linea(registro_id=3, mes=10)])])
    assert not hasattr(cli, "leidas_ventana")
    assert [x.accion for x in lote[0].incidencias] == ["omitir", "omitir"]


def test_f062_r19_lote_lo_que_no_se_precargo_va_al_cliente():
    cli = _cli(_lineas(555001))
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar(_peticiones(), _st(False))
    assert memoria.incidencias_en_ventana(
        [400], 20251001, 20261130, ides=[51]) == [_lineas(555001)[i]
                                                  for i in (2, 0)]
    assert memoria.fallos_de_memoria == {}
    for args, kw in ((([200, 300], 20251001, 20261130), {}),
                     (([200], 20250901, 20261130), {}),
                     (([200], 20251001, 20261231), {}),
                     (([200], 20251001, 20261130), {"ides": [53]}),
                     (([200], 20251001, 20261130),
                      {"obride_pruebas": PRUEBAS})):
        memoria.incidencias_en_ventana(*args, **kw)
    assert memoria.fallos_de_memoria == {"incidencias_en_ventana": 5}
    assert len(cli.leidas_ventana) == 6


def test_f062_r19_lote_filtra_lo_precargado_como_la_consulta():
    otra = _l(70, 20261020, "HNOR", reside=200)     # no es `CI*`
    vieja = _l(71, 20250915, reside=200)            # fuera de la ventana
    cli = _cli([*_lineas(555001), otra, vieja])
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar([(OBRA, [linea(registro_id=1, mes=10)], [_inc()],
                        ContextoRachas(quitadas=[_inc(
                            9, 20, 22, hmores_ide_ini=70,
                            hmores_ide_fin=71)]))], _st(False))
    assert cli.leidas_ventana == [([200], 20251001, 20261130, None,
                                   [70, 71])]
    assert [x.ide for x in memoria.incidencias_en_ventana(
        [200], 20251101, 20261130)] == [51, 52]
    assert [x.ide for x in memoria.incidencias_en_ventana(
        [200], 20251001, 20261130, ides=[71])] == [71, 51, 52]
    assert memoria.fallos_de_memoria == {}


def test_f062_r19_lote_si_la_lectura_falla_falla_el_lote():
    class Falla(ClienteInc):
        def incidencias_en_ventana(self, *a, **kw):
            raise RuntimeError("sigrid-api devolvio una respuesta truncada")

    with pytest.raises(RuntimeError, match="truncada"):
        RegistroLote(cliente=_cli(cls=Falla),
                     settings=_st(False)).preflight(_peticiones())


def test_f062_r17_lote_la_peticion_solo_con_quitadas_como_suelta():
    traza = {"hmores_ide_fin": 62, "dia_fin": 9, "dia_fin_antes": 7}
    adm = [_l(61, 20261005, obride=40, parte_emp=1),
           _l(62, 20261009, "CIZ", obride=40, parte_emp=1, can=1.0)]
    p = (OBRA, [], [], ContextoRachas(quitadas=[_inc(**traza)]))
    cli = _cli(adm)
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar([p], _st(False))
    pf = _suelto(memoria, p, _st(False))
    # La ventana, precargada (sin líneas, `lineas_registradas` va vacía al
    # cliente, como la obra solo con incidencias de F-030).
    assert len(cli.leidas_ventana) == 1
    assert "incidencias_en_ventana" not in memoria.fallos_de_memoria
    assert [(a.rol, a.accion, a.fecha_int) for a in pf.incidencias] == [
        ("devolver", "editar", 20261007)]


def test_f062_r19_lote_la_ventana_de_memoria_incluye_sus_dos_extremos():
    # Mutación (T22): como el `BETWEEN` de la consulta, el primer y el
    # último día de la ventana pedida entran; uno antes o uno después, no.
    cli = _cli(_lineas(555001))
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar([(OBRA, [linea(registro_id=1, mes=10)], [_inc()],
                        ContextoRachas())], _st(False))
    def ides(desde, hasta):
        return [x.ide for x in memoria.incidencias_en_ventana(
            [200], desde, hasta)]
    assert ides(20261005, 20261009) == [51, 52]
    assert ides(20261006, 20261009) == [52]
    assert ides(20261005, 20261008) == [51]
    assert memoria.fallos_de_memoria == {}
