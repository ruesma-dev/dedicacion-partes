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


def test_f051_r7_el_cerrado_de_un_periodo_no_se_olvida_en_el_siguiente():
    """Las líneas al 0 % de un parte cerrado se buscan por periodo; los
    registros omitidos por un cerrado (que filtran el «sin partida») se
    acumulan entre periodos, como antes de F-051."""
    from tests.test_f037_pipeline import PT_CER9, PT_REG7, ClienteF037
    from tests.test_f013_sin_partida import linea_que_no_casa
    cli = ClienteF037(periodo=[PT_CER9, PT_REG7], lineas_por_parte={
        9: [linea_previa(ide=6001, reside=400, horide=6,
                         hora_codigo="MJEFO", paride=0)]})
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea_que_no_casa(registro_id=1),
        linea(registro_id=2, mes=8, recurso_ide=400)])
    assert pf.acciones[0].accion == "omitir"
    assert [c.motivo for c in pf.conflictos
            if 1 in c.registros] == []


# ============== R6, R8-R13, R18 · paso 10 (ejecutar) ============== #
def _sin_delete(cli) -> None:
    """R6: ninguna sentencia del registro borra."""
    assert cli.borrados() == []
    assert all("delete" not in s["sql"].lower() for s in cli.escritos)


MOTIVO_1 = ("la línea 410600 del parte ha cambiado en Sigrid desde el "
            "análisis: no se ha escrito nada en su lugar; vuelve a registrar")


def test_f051_r8_edita_la_linea_al_cero_sin_insertar_ni_borrar():
    cli = _caso_0707()
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    _sin_delete(cli)
    assert cli.inserts() == [] and res.borradas == 0
    (ed,) = cli.ediciones()
    assert ed == {
        "ide": 410600, "reside": 200, "can_leido": 0.0,
        "synckey_leida": None, "horide": 5, "can": 0.4, "pre": 9000.0,
        "paride": 80001, "caaide": ed["caaide"], "fecha_int": 20260731,
        "synckey": synckey_de(1), "tex": "PRUEBA-PORC"}
    assert ed["caaide"] == res.editadas[0]["despues"]["caaide"] != 0
    (e,) = res.escritas
    assert (e["registro_id"], e["editada"], e["hmores_ide"], e["hmoide"],
            e["parte_cod"]) == (1, True, 410600, 777, "PT26/00251")
    assert (e["can"], e["tot"], e["partida_cod"]) == (0.4, 3600.0, "CI.1.10")
    # Lo que queda en el doble (la guarda dejó pasar la edición).
    ls = cli.lineas_parte[0]
    assert (ls.ide, ls.can, ls.synckey, ls.paride) == (
        410600, 0.4, synckey_de(1), 80001)
    # Las demás, intactas (R7).
    assert [l.can for l in cli.lineas_parte[1:]] == [0.0, 0.0]


def test_f051_r8_la_editada_no_consume_pos_la_insertada_si():
    cli = ClienteFalso(lineas_parte=[_cero(410600)])
    pos0 = cli.max_pos(777)
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, recurso_ide=400)])
    assert [i["pos"] for i in cli.inserts()] == [pos0 + 64]
    assert [(e["registro_id"], e["editada"]) for e in res.escritas] == [
        (1, True), (2, False)]


def test_f051_r8_si_todas_editan_no_se_crea_parte_ni_se_lee_pos():
    class Anota(ClienteFalso):
        def max_pos(self, hmoide):
            self.pos_leidas = getattr(self, "pos_leidas", 0) + 1
            return super().max_pos(hmoide)

    cli = Anota(lineas_parte=[_cero(410600)])
    _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert getattr(cli, "pos_leidas", 0) == 0


def test_f051_r10_en_real_no_toca_el_tex():
    cli = _caso_0707()
    res = _pl(cli, obra_pruebas_forzar=False).ejecutar(obra=OBRA,
                                                       lineas=[linea()])
    assert cli.ediciones()[0]["tex"] is None
    assert res.editadas[0]["despues"]["tex"] is None


def test_f051_r9_synckey_de_otro_sistema_intacta():
    cli = ClienteFalso(lineas_parte=[_cero(410600, synckey=SK_PARTES)])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    (ed,) = cli.ediciones()
    assert (ed["synckey_leida"], ed["synckey"]) == (SK_PARTES, SK_PARTES)
    assert cli.lineas_parte[0].synckey == SK_PARTES
    assert res.escritas[0]["hmores_ide"] == 410600


def test_f051_r9_nuestra_de_otra_asignacion_pasa_a_esta():
    cli = ClienteFalso(lineas_parte=[_cero(410600, synckey=synckey_de(77))])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert cli.ediciones()[0]["synckey"] == synckey_de(1)
    assert res.escritas[0]["hmores_ide"] == 410600


def test_f051_r18_editadas_con_antes_y_despues_y_el_log(caplog):
    cli = ClienteFalso(lineas_parte=[_cero(
        410600, paride=81234, horide=8, hora_codigo="MADM")])
    cli.lineas_parte[0].pre = 8500.0
    cli.lineas_parte[0].caaide = 90007
    cli.lineas_parte[0].tex = "copia sept"
    caplog.set_level(logging.INFO)
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    (ed,) = res.editadas
    caa = ed["despues"]["caaide"]
    assert ed == {
        "registro_id": 1, "ide": 410600, "hmoide": 777,
        "parte_cod": "PT26/00251",
        "antes": {"can": 0.0, "pre": 8500.0, "tot": 0.0, "horide": 8,
                  "hora_codigo": "MADM", "paride": 81234, "caaide": 90007,
                  "fecha_int": 20260731, "synckey": None,
                  "tex": "copia sept"},
        "despues": {"can": 0.4, "pre": 9000.0, "tot": 3600.0, "horide": 5,
                    "hora_codigo": "MENC", "paride": 80001, "caaide": caa,
                    "fecha_int": 20260731, "synckey": synckey_de(1),
                    "tex": "PRUEBA-PORC"}}
    assert res.a_cero == []
    logs = [r.getMessage() for r in caplog.records
            if "[registro] edita" in r.getMessage()]
    assert len(logs) == 1 and "ide=410600" in logs[0]
    assert "parte=PT26/00251" in logs[0] and "registro=1" in logs[0]
    assert "'tex': 'copia sept'" in logs[0] and "Acuna" not in logs[0]


def test_f051_r4_pisado_confirmado_edita_el_mismo_ide():
    cli = ClienteFalso(lineas_parte=[linea_previa(ide=5009, paride=80001,
                                                  can=0.5, tot=4500.0)])
    (c,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).conflictos
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()],
                            pisar_claves={c.clave})
    _sin_delete(cli)
    assert cli.inserts() == [] and res.pisadas == [c.clave]
    (ed,) = cli.ediciones()
    assert (ed["ide"], ed["can_leido"], ed["synckey"]) == (
        5009, 0.5, synckey_de(1))
    assert res.escritas[0]["hmores_ide"] == 5009
    assert res.editadas[0]["antes"]["can"] == 0.5


def test_f051_r4_pisado_sin_confirmar_no_escribe():
    cli = ClienteFalso(lineas_parte=[linea_previa(ide=5009, paride=80001)])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert cli.escritos == [] and res.editadas == []
    assert [c.edita_ide for c in res.pendientes_confirmacion] == [5009]


def test_f051_r5_r18_tres_choques_uno_edita_y_dos_a_cero():
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5009, paride=80001, can=0.2, tot=1800.0,
                     fecha_int=20260709),
        linea_previa(ide=5003, paride=80001, can=0.3, tot=2700.0,
                     synckey=synckey_de(55), fecha_int=20260703),
        linea_previa(ide=5005, paride=80001, can=0.1, tot=900.0,
                     fecha_int=20260705)])
    (c,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).conflictos
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()],
                            pisar_claves={c.clave})
    _sin_delete(cli)
    assert [e["ide"] for e in cli.ediciones()] == [5003]
    assert cli.a_ceros() == [
        {"ide": 5005, "reside": 200, "can_leido": 0.1, "synckey_leida": None},
        {"ide": 5009, "reside": 200, "can_leido": 0.2, "synckey_leida": None}]
    assert [(z["registro_id"], z["ide"], z["antes"]["can"],
             z["despues"]["can"], z["despues"]["tot"], z["despues"]["paride"])
            for z in res.a_cero] == [(1, 5005, 0.1, 0.0, 0.0, 80001),
                                     (1, 5009, 0.2, 0.0, 0.0, 80001)]
    assert {ls.ide: ls.can for ls in cli.lineas_parte} == {
        5009: 0.0, 5003: 0.4, 5005: 0.0}


def test_f051_r5_dos_registros_dos_choques_cada_uno_edita_uno():
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5009, paride=80001, can=0.2),
        linea_previa(ide=5003, paride=80001, can=0.3)])
    lineas = [linea(registro_id=1, porcentaje=0.2),
              linea(registro_id=2, porcentaje=0.2)]
    (c,) = _pl(cli).preflight(obra=OBRA, lineas=lineas).conflictos
    res = _pl(cli).ejecutar(obra=OBRA, lineas=lineas,
                            pisar_claves={c.clave})
    assert [(e["ide"], e["synckey"]) for e in cli.ediciones()] == [
        (5003, synckey_de(1)), (5009, synckey_de(2))]
    assert cli.a_ceros() == [] and cli.inserts() == []
    assert {e["registro_id"]: e["hmores_ide"] for e in res.escritas} == {
        1: 5003, 2: 5009}


def test_f051_r4_mas_registros_que_choques_el_que_sobra_inserta():
    """Dos asignaciones con la misma identidad y un solo choque: la de menor
    `registro_id` edita el choque y la otra se inserta."""
    cli = ClienteFalso(lineas_parte=[linea_previa(ide=5009, paride=80001,
                                                  can=0.5)])
    lineas = [linea(registro_id=1, porcentaje=0.2),
              linea(registro_id=2, porcentaje=0.2)]
    (c,) = _pl(cli).preflight(obra=OBRA, lineas=lineas).conflictos
    assert (c.edita_ide, c.a_cero_ides) == (5009, [])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=lineas,
                            pisar_claves={c.clave})
    _sin_delete(cli)
    assert [(e["ide"], e["synckey"]) for e in cli.ediciones()] == [
        (5009, synckey_de(1))]
    assert [i["synckey"] for i in cli.inserts()] == [synckey_de(2)]
    assert {e["registro_id"]: e["editada"] for e in res.escritas} == {
        1: True, 2: False}


def test_f051_r12_pisable_que_cambio_va_a_omitidas_sin_insertar():
    """Entre el preflight y la escritura, Administración le pone un 30 %."""
    class Cambia(ClienteFalso):
        def lineas_para_editar(self, ides):
            out = super().lineas_para_editar(ides)
            out[410600].can = 0.3
            return out

    cli = Cambia(lineas_parte=_caso_0707().lineas_parte)
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert cli.escritos == [] and res.escritas == []
    assert res.omitidas == [{"registro_id": 1, "motivo": MOTIVO_1}]


@pytest.mark.parametrize("cambio", [
    {"parte_est": 3}, {"enlazada": True}, {"reside": 400},
    {"hora_codigo": "HEGR"}, None,
], ids=["parte_cerrado", "enlazada", "otro_recurso", "hora_no_m",
        "desaparecida"])
def test_f051_r12_cada_condicion_de_la_pisable(cambio):
    class Cambia(ClienteFalso):
        def lineas_para_editar(self, ides):
            out = super().lineas_para_editar(ides)
            if cambio is None:
                return {}
            for k, v in cambio.items():
                setattr(out[410600], k, v)
            return out

    cli = Cambia(lineas_parte=[_cero(410600)])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, recurso_ide=400)])
    assert res.omitidas == [{"registro_id": 1, "motivo": MOTIVO_1}]
    assert [e["registro_id"] for e in res.escritas] == [2]
    assert cli.ediciones() == [] and len(cli.inserts()) == 1


@pytest.mark.parametrize("cambio", [
    {"paride": 81234}, {"horide": 8}, {"parte_est": 3}, {"enlazada": True},
    {"reside": 400}, {"hora_codigo": "HEGR"}, None,
], ids=["otra_partida", "otra_hora", "parte_cerrado", "enlazada",
        "otro_recurso", "hora_no_m", "desaparecida"])
def test_f051_r12_choque_que_cambio_omite_el_pisado_entero(cambio):
    def previas():
        return [linea_previa(ide=5003, paride=80001, can=0.3),
                linea_previa(ide=5009, paride=80001, can=0.2)]
    (c,) = _pl(ClienteFalso(lineas_parte=previas())).preflight(
        obra=OBRA, lineas=[linea()]).conflictos

    class Cambia(ClienteFalso):
        def lineas_para_editar(self, ides):
            out = super().lineas_para_editar(ides)
            if cambio is None:
                del out[5009]
                return out
            for k, v in cambio.items():
                setattr(out[5009], k, v)        # la que iba a 0
            return out

    cli = Cambia(lineas_parte=previas())
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()],
                            pisar_claves={c.clave})
    assert cli.escritos == [] and res.escritas == res.a_cero == []
    assert res.omitidas == [{"registro_id": 1, "motivo": MOTIVO_1.replace(
        "410600", "5009")}]


def test_f051_r13_guarda_fallida_va_a_omitidas_nunca_inserta():
    cli = ClienteFalso(lineas_parte=[_cero(410600)])
    cli.guarda_falla = frozenset({410600})
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(registro_id=1), linea(registro_id=2, recurso_ide=400)])
    assert len(cli.ediciones()) == 1 and len(cli.inserts()) == 1
    assert [e["registro_id"] for e in res.escritas] == [2]
    assert res.editadas == []
    assert res.omitidas == [{"registro_id": 1, "motivo": MOTIVO_1}]


def test_f051_r13_editada_con_otra_synckey_tras_escribir_no_cuenta():
    """La guarda dejó pasar la fila pero otra escritura le puso otra
    `synckey`: no es la nuestra."""
    class Otra(ClienteFalso):
        def _aplicar_ediciones(self, statements):
            super()._aplicar_ediciones(statements)
            self.lineas_parte[0].synckey = "partes:y"

    cli = Otra(lineas_parte=[_cero(410600)])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert res.escritas == [] and res.editadas == []
    assert res.omitidas == [{"registro_id": 1, "motivo": MOTIVO_1}]


def test_f051_r13_editada_con_otro_can_tras_escribir_no_cuenta():
    class Otra(ClienteFalso):
        def _aplicar_ediciones(self, statements):
            super()._aplicar_ediciones(statements)
            self.lineas_parte[0].can = 0.9

    cli = Otra(lineas_parte=[_cero(410600)])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert res.escritas == [] and res.omitidas[0]["registro_id"] == 1


def test_f051_r13_a_cero_que_no_quedo_a_cero_al_log(caplog):
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5003, paride=80001, can=0.3),
        linea_previa(ide=5009, paride=80001, can=0.2)])
    (c,) = _pl(cli).preflight(obra=OBRA, lineas=[linea()]).conflictos
    cli.guarda_falla = frozenset({5009})
    caplog.set_level(logging.WARNING)
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()],
                            pisar_claves={c.clave})
    assert [e["registro_id"] for e in res.escritas] == [1]
    assert res.a_cero == []
    assert any("[registro] no quedo a 0 la linea 5009" in r.getMessage()
               for r in caplog.records)


def test_f051_r12_una_sola_lectura_previa_con_todas():
    cli = ClienteFalso(lineas_parte=[
        _cero(410600), linea_previa(ide=5003, reside=400, horide=6,
                                    hora_codigo="MJEFO", paride=80002),
        linea_previa(ide=5009, reside=400, horide=6, hora_codigo="MJEFO",
                     paride=80002)])
    lineas = [linea(registro_id=1),
              linea(registro_id=2, recurso_ide=400, paride=80002,
                    partida_cod="CI.1.20")]
    claves = {c.clave for c in _pl(cli).preflight(
        obra=OBRA, lineas=lineas).conflictos}
    assert claves
    res = _pl(cli).ejecutar(obra=OBRA, lineas=lineas, pisar_claves=claves)
    assert cli.para_editar == [[5003, 5009, 410600]]
    assert sorted(e["registro_id"] for e in res.escritas) == [1, 2]


def test_f051_r12_sin_nada_que_editar_no_se_lee():
    cli = ClienteFalso()
    _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert getattr(cli, "para_editar", []) == []


def test_f051_r6_ningun_delete_en_ningun_escenario():
    escenarios = [
        (_caso_0707(), [linea()], False),
        (ClienteFalso(lineas_parte=[linea_previa(ide=5009, paride=80001)]),
         [linea()], True),
        (ClienteFalso(lineas_parte=[linea_previa(ide=5009, paride=80001)]),
         [linea()], False),
        (ClienteFalso(), [linea(), linea(registro_id=2, recurso_ide=400)],
         False),
    ]
    for cli, lineas, pisar in escenarios:
        claves = ({c.clave for c in _pl(cli).preflight(
            obra=OBRA, lineas=lineas).conflictos} if pisar else set())
        res = _pl(cli).ejecutar(obra=OBRA, lineas=lineas,
                                pisar_claves=claves)
        _sin_delete(cli)
        assert res.borradas == 0


def test_f051_r13_reejecutar_ya_registrada():
    cli = _caso_0707()
    res1 = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    res2 = _pl(cli).ejecutar(obra=OBRA, lineas=[
        linea(hmores_ide=res1.escritas[0]["hmores_ide"])])
    assert res2.ya_registradas == [1]
    assert res2.ya_registradas_ide == {1: 410600}
    assert len(cli.ediciones()) == 1


def test_f051_r13_reejecutar_sin_ide_por_la_synckey_puesta():
    """La línea de Administración lleva ya nuestra `synckey` (design §6.3):
    sin `hmores_ide` se reconoce igual."""
    cli = _caso_0707()
    _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    cli.synckeys = {synckey_de(1): cli.lineas_parte[0]}
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea()])
    assert res.ya_registradas == [1] and len(cli.ediciones()) == 1


# ================== R19 · el lote da lo mismo, mismas lecturas ================== #
def _previas_0707():
    return [_cero(410600), _cero(410601, reside=400, horide=6,
                                 hora_codigo="MJEFO"),
            _cero(410935)]


def _previas_pisado():
    return [linea_previa(ide=5003, paride=80001, can=0.3),
            linea_previa(ide=5009, paride=80001, can=0.2),
            _cero(410601, reside=400, horide=6, hora_codigo="MJEFO")]


def _ajustes_lote() -> SettingsFalso:
    st = SettingsFalso()
    st.sigrid_lecturas_paralelas = 4
    return st


@pytest.mark.parametrize("previas", [_previas_0707, _previas_pisado],
                         ids=["0707", "pisado"])
def test_f051_r19_lote_igual_que_suelto_y_mismas_lecturas(previas):
    from tests.test_f055_lecturas_lote import ClienteQueAnota
    lineas = [linea(registro_id=1), linea(registro_id=2, recurso_ide=400)]

    def suelto(lineas_parte):
        cli = ClienteQueAnota(lineas_parte=lineas_parte)
        pf = RegistroPipeline(cliente=cli, settings=_ajustes_lote()
                              ).preflight(obra=OBRA, lineas=lineas)
        return pf, sorted(cli.nombres())

    def en_lote(lineas_parte):
        cli = ClienteQueAnota(lineas_parte=lineas_parte)
        [pf] = RegistroLote(cliente=cli, settings=_ajustes_lote()
                            ).preflight([(OBRA, lineas)])
        return pf, sorted(cli.nombres())

    pf_suelto, leidas_suelto = suelto(previas())
    pf_lote, leidas_lote = en_lote(previas())
    assert asdict(pf_lote) == asdict(pf_suelto)
    assert any(a.linea_cero for a in pf_suelto.acciones)
    # Las mismas lecturas que sin ninguna línea previa: las pisables y el
    # reparto del pisado no leen nada (R19).
    assert leidas_suelto == suelto([])[1]
    assert leidas_lote == en_lote([])[1]
    assert "lineas_para_editar" not in leidas_suelto + leidas_lote


# =================== campaña de mutación (T14) =================== #
def test_f051_r15_sin_ide_no_se_mira_la_fila_de_otro_ide():
    """Una línea sin `hmores_ide` se busca solo por su `synckey`, aunque en
    la misma lectura venga la fila de otra (aquí, la del `ide` 1)."""
    cli = ClienteFalso(lineas_parte=[_nuestra(1, synckey=SK_PARTES)])
    pf = _pl(cli).preflight(obra=OBRA, lineas=[
        linea(registro_id=1, hmores_ide=1), linea(registro_id=2, mes=8)])
    assert [(a.registro_id, a.accion) for a in pf.acciones] == [
        (1, "ya_registrado"), (2, "escribir")]


def test_f051_r8_edita_sin_partida_confirmada_con_partida_cero():
    from tests.test_f013_sin_partida import linea_que_no_casa
    cli = ClienteFalso(lineas_parte=[_cero(410600, reside=400, horide=6,
                                           hora_codigo="MJEFO")])
    lineas = [linea_que_no_casa()]
    claves = {c.clave for c in _pl(cli).preflight(
        obra=OBRA, lineas=lineas).conflictos}
    res = _pl(cli).ejecutar(obra=OBRA, lineas=lineas, pisar_claves=claves)
    (ed,) = cli.ediciones()
    assert (ed["ide"], ed["paride"]) == (410600, 0)
    assert res.editadas[0]["despues"]["paride"] == 0


def test_f051_r8_edita_sin_cuenta_con_cuenta_cero():
    from tests.test_f037_pipeline import SIN_CUENTA, ClienteF037
    cli = ClienteF037(lineas_parte=[_cero(410600, reside=SIN_CUENTA,
                                          horide=7, hora_codigo="MCAP")])
    res = _pl(cli).ejecutar(obra=OBRA, lineas=[linea(recurso_ide=SIN_CUENTA)])
    (ed,) = cli.ediciones()
    assert (ed["ide"], ed["caaide"]) == (410600, 0)
    assert res.editadas[0]["despues"]["caaide"] == 0
