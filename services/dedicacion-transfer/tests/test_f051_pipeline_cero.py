# tests/test_f051_pipeline_cero.py
"""F-051 · El pipeline edita, nunca borra (R3-R19; design §6).

Con el `ClienteFalso` de `conftest.py`, cuyo `escribir` aplica a sus líneas
las sentencias de edición con la misma guarda que el SQL: la relectura de
después ve lo que vería en Sigrid. El escenario de la 0707 (octubre de
2026, PT26/00370) está reducido a sus rasgos: líneas `M*` a 0 copiadas del
mes anterior por Administración, con hora, partida y sin `synckey`. Los
`ide` son inventados. Sin red ni BBDD.
"""
from __future__ import annotations

import logging
from dataclasses import asdict

import pytest
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ObraEntrada, ParteSigrid
from infrastructure.sigrid.sigrid_write_client import (
    medir_lecturas, synckey_de,
)

from tests.conftest import (
    OBRA_ORIGEN, ClienteFalso, SettingsFalso, linea, linea_previa,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)
SK_PARTES = "partes:2026-10-03:410931"


def _pl(cli, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))


def _cero(ide: int, **kw):
    """Línea `M*` a 0 de Administración en el parte En registro (777)."""
    datos = dict(ide=ide, reside=200, fecha_int=20260731, horide=5,
                 hora_codigo="MENC", can=0.0, tot=0.0, synckey=None,
                 paride=80001)
    datos.update(kw)
    return linea_previa(**datos)


def _nuestra(ide: int, registro_id: int = 1, **kw):
    """Una línea que ya escribimos (can 0,4, nuestra synckey)."""
    datos = dict(ide=ide, can=0.4, tot=3600.0, paride=80001,
                 synckey=synckey_de(registro_id), nuestra=True)
    datos.update(kw)
    return linea_previa(**datos)


# ========================= R15-R17 · paso 6 ========================= #
def test_f051_r15_por_ide_aunque_la_synckey_sea_de_otro_sistema():
    cli = ClienteFalso(lineas_parte=[_nuestra(410931, synckey=SK_PARTES,
                                              nuestra=False)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea(hmores_ide=410931)])
    (a,) = pf.acciones
    assert (a.accion, a.hmores_ide) == ("ya_registrado", 410931)
    assert "410931" in a.motivo and pf.conflictos == []


@pytest.mark.parametrize("cambio", [
    {"reside": 400}, {"synckey": synckey_de(2)},
], ids=["otro_recurso", "nuestra_de_otra_asignacion"])
def test_f051_r15_ide_que_no_es_suyo_no_cuenta(cambio):
    """`ide` reutilizado (`MAX(ide)+1`) o de otra asignación: no es la
    suya; sin `synckey` propia en Sigrid, se escribe."""
    cli = ClienteFalso(lineas_parte=[_nuestra(410931, **cambio)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea(hmores_ide=410931)])
    assert pf.acciones[0].accion == "escribir"


def test_f051_r15_sin_ide_por_synckey_como_hoy():
    hit = _nuestra(9001)
    cli = ClienteFalso(synckeys={synckey_de(1): hit})
    (a,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).acciones
    assert (a.accion, a.hmores_ide) == ("ya_registrado", 9001)


def test_f051_r15_ide_de_otro_pero_synckey_propia_por_synckey():
    cli = ClienteFalso(lineas_parte=[_nuestra(410931, reside=400)],
                       synckeys={synckey_de(1): _nuestra(9001)})
    (a,) = _pl(cli).preflight(obra=OBRA,
                              lineas=[linea(hmores_ide=410931)]).acciones
    assert (a.accion, a.hmores_ide) == ("ya_registrado", 9001)


def test_f051_r15_una_sola_lectura_con_claves_e_ides():
    class Anota(ClienteFalso):
        def lineas_registradas(self, claves, ides=()):
            self.pedidas = getattr(self, "pedidas", []) + [
                (sorted(claves), sorted(i for i in ides if i))]
            return super().lineas_registradas(claves, ides)

    cli = Anota()
    _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1, hmores_ide=410931), linea(registro_id=2,
                                                       recurso_ide=400)])
    assert cli.pedidas == [([synckey_de(1), synckey_de(2)], [410931])]


def test_f051_r17_ide_desaparecido_se_vuelve_a_escribir():
    cli = ClienteFalso()
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea(hmores_ide=410931)])
    assert [e["registro_id"] for e in res.escritas] == [1]
    assert len(cli.inserts()) == 1 and res.ya_registradas == []


def test_f051_r16_ya_registradas_ide_publicado():
    cli = ClienteFalso(lineas_parte=[_nuestra(410931, synckey=SK_PARTES)],
                       synckeys={synckey_de(2): _nuestra(9002, 2,
                                                         reside=400)})
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(registro_id=1, hmores_ide=410931),
        linea(registro_id=2, recurso_ide=400)])
    assert res.ya_registradas == [1, 2]
    assert res.ya_registradas_ide == {1: 410931, 2: 9002}
    assert cli.escritos == []


# ===================== R3-R5, R7 · paso 7 (preflight) ===================== #
def _caso_0707(**kw):
    """El parte En registro con la copia de Administración: la línea a 0
    del recurso (MENC, CI.1.10) y la de su vehículo (otro recurso, `OTEL`,
    también a 0), más una `H*` a 0 del mismo recurso."""
    return ClienteFalso(lineas_parte=[
        _cero(410600),
        _cero(410601, reside=400, horide=6, hora_codigo="MJEFO"),
        _cero(410602, horide=9, hora_codigo="HEGR"),
    ], **kw)


def test_f051_r3_misma_partida_sin_conflicto_con_linea_cero_y_aviso():
    pf = _pl(_caso_0707()).preflight(obra=OBRA, lineas=[linea()])
    (a,) = pf.acciones
    assert a.accion == "escribir" and pf.conflictos == []
    assert a.linea_cero == {
        "ide": 410600, "hmoide": 777, "parte_cod": "PT26/00251",
        "horide": 5, "hora_codigo": "MENC", "paride": 80001, "can": 0.0,
        "fecha_int": 20260731, "synckey": None}
    assert a.aviso == ("se edita la línea 410600 al 0 % del parte "
                       "PT26/00251 (MENC, partida CI.1.10) en vez de añadir "
                       "otra")


def test_f051_r3_otra_partida_igual_y_la_nombra_por_su_ide():
    cli = ClienteFalso(lineas_parte=[_cero(410600, paride=81234, horide=8,
                                           hora_codigo="MADM")])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    (a,) = pf.acciones
    assert pf.conflictos == [] and a.linea_cero["ide"] == 410600
    assert "(MADM, partida 81234)" in a.aviso


def test_f051_r3_las_que_sobran_se_dicen():
    cli = ClienteFalso(lineas_parte=[_cero(410600), _cero(410931),
                                     _cero(410935, paride=0)])
    (a,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).acciones
    assert a.linea_cero["ide"] == 410600
    assert a.aviso.endswith(" · quedan 2 línea(s) al 0 % de este "
                            "trabajador sin tocar")


def test_f051_r3_pisable_no_cuenta_en_la_capacidad_ni_en_el_contexto():
    """Una sobrecarga con las cifras de hoy: la pisable (a 0) no sale entre
    las contadas ni en el `n` del motivo."""
    cli = ClienteFalso(lineas_parte=[
        _cero(410600, paride=81234),
        linea_previa(ide=5002, can=0.8, paride=82222)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    (c,) = pf.conflictos
    assert c.motivo == "sobrecarga"
    assert (c.suma_existente, c.suma_total) == (0.8, 1.2)
    assert [ls.ide for ls in c.contexto] == [5002]
    assert pf.acciones[0].linea_cero["ide"] == 410600


def test_f051_r3_sin_partida_como_hoy_y_tambien_edita():
    from tests.test_f013_sin_partida import linea_que_no_casa
    cli = ClienteFalso(lineas_parte=[_cero(410600, reside=400, horide=6,
                                           hora_codigo="MJEFO")])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea_que_no_casa()])
    (c,) = pf.conflictos
    assert (c.motivo, c.lineas, c.registros) == ("sin_partida", [], [1])
    assert pf.acciones[0].linea_cero["ide"] == 410600


def test_f051_r4_choque_pisado_a_confirmar_edita_el_de_menor_ide():
    cli = ClienteFalso(lineas_parte=[linea_previa(ide=5009, paride=80001),
                                     _cero(410600, paride=81234)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    (c,) = pf.conflictos
    assert (c.motivo, c.edita_ide, c.a_cero_ides) == ("pisado", 5009, [])
    assert [ls.ide for ls in c.lineas] == [5009]
    assert c.contexto == []                 # la pisable no es contexto
    assert pf.acciones[0].linea_cero is None


def test_f051_r5_tres_choques_uno_edita_dos_a_cero():
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5009, paride=80001, fecha_int=20260709),
        linea_previa(ide=5003, paride=80001, fecha_int=20260703),
        linea_previa(ide=5005, paride=80001, fecha_int=20260705)])
    (c,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).conflictos
    assert (c.edita_ide, c.a_cero_ides) == (5003, [5005, 5009])


def test_f051_r7_al_cero_en_parte_cerrado_choca_como_hoy():
    from tests.test_f037_pipeline import PT_CER9, PT_REG7, ClienteF037
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7],
                      lineas_por_parte={9: [_cero(6001)]})
    (a,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).acciones
    assert a.accion == "omitir" and "PT26/00009 (Cerrado)" in a.motivo
    assert a.linea_cero is None


def test_f051_r7_la_del_cerrado_no_se_edita_la_del_en_registro_si():
    from tests.test_f037_pipeline import PT_CER9, PT_REG7, ClienteF037
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7],
                      lineas_por_parte={9: [_cero(6001, paride=81234)],
                                        7: [_cero(6002, paride=81235)]})
    (a,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).acciones
    assert a.accion == "escribir"
    assert (a.linea_cero["ide"], a.linea_cero["parte_cod"]) == (
        6002, "PT26/00007")
    assert "quedan" not in a.aviso


def test_f051_r7_otro_recurso_y_horas_no_m_no_se_tocan():
    pf = _pl(_caso_0707()).preflight(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, recurso_ide=300)])
    a1, a2 = pf.acciones
    assert a1.linea_cero["ide"] == 410600 and "quedan" not in a1.aviso
    assert a2.accion == "omitir" and a2.linea_cero is None


def test_f051_r7_modo_pruebas_solo_lee_los_partes_de_la_obra_de_pruebas():
    class Anota(ClienteFalso):
        def partes_del_periodo(self, obra_ide, ano, mes):
            self.obras_leidas = getattr(self, "obras_leidas", []) + [obra_ide]
            return super().partes_del_periodo(obra_ide, ano, mes)

    cli = Anota(lineas_parte=[_cero(410600)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea()])
    assert cli.obras_leidas == [cli.obra.ide]           # la 0404
    assert pf.acciones[0].linea_cero["hmoide"] == 777


def test_f051_r1_postventa_solo_la_de_su_partida():
    cli = ClienteFalso(lineas_parte=[_cero(410600, paride=80001),
                                     _cero(410700, paride=70001)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[linea(es_postventa=True)])
    (a,) = pf.acciones
    assert a.destino == "postventa" and a.linea_cero["ide"] == 410700
    assert "quedan" not in a.aviso
