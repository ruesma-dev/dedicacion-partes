# tests/test_f054_poner_a_cero.py
"""F-054 · T13: poner a 0 las sobrantes confirmadas (R35-R36; design §6.3).

`PonerACero.ejecutar(empresa, ano, mes, lineas)`: relee cada línea
(`lineas_para_editar`), comprueba que sigue siendo la del preflight (mismo
recurso, `can`, `synckey` y hora —`M*` para el trabajador, la suya para el
vinculado—, sin enlaces, En registro, no de otro sistema y, en pruebas, en
la 0404) y la pone a 0 en su sitio (`can` y `tot`) con la guarda de F-051;
relee y la que no quedó a 0 es `omitida`. Log antes y después; ningún
`DELETE`. `POST /api/registro/poner-a-cero` lo expone.

`ClienteFalso` de `conftest.py` (su `escribir` aplica la guarda como el
SQL). Sin red ni BBDD.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
from application.pipelines.poner_a_cero import (
    MOTIVO_CAMBIADA,
    MOTIVO_ENLAZADA,
    MOTIVO_FUERA_PRUEBAS,
    MOTIVO_NO_ESTA,
    MOTIVO_NO_QUEDO,
    MOTIVO_OTRA_HORA,
    MOTIVO_OTRO_RECURSO,
    MOTIVO_OTRO_SISTEMA,
    MOTIVO_PARTE_CERRADO,
    PonerACero,
)
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ParteSigrid
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app

from tests.conftest import (
    ClienteFalso,
    SettingsFalso,
    linea,
    linea_previa,
)
from tests.test_f050_endpoint_propuesta import AJUSTES


def _cli(*lineas, **kw):
    return ClienteFalso(lineas_parte=[
        linea_previa(ide=i, reside=r, can=c, tot=round(c * 9000, 2),
                     hora_codigo=h, synckey=sk, paride=9,
                     fecha_int=20260731)
        for i, r, c, h, sk in lineas], **kw)


def _pedida(ide, recurso=200, can=0.3, hora="MENC", synckey=None,
            vinculado=None):
    return {"hmores_ide": ide, "recurso_ide": recurso, "hora": hora,
            "vinculado": vinculado, "can": can, "synckey": synckey}


def _poner(cli, lineas, **kw):
    return PonerACero(cliente=cli, settings=SettingsFalso(**kw)).ejecutar(
        1, 2026, 7, lineas)


def _can(cli, ide):
    return next(ls.can for ls in cli.lineas_parte if ls.ide == ide)


def test_f054_r35_pone_a_cero_en_su_sitio_con_la_guarda(caplog):
    cli = _cli((7001, 200, 0.3, "MENC", None),
               (7002, 200, 0.2, "MENC", "porcentajes:5"))
    caplog.set_level(logging.INFO)
    r = _poner(cli, [_pedida(7001), _pedida(7002, can=0.2,
                                            synckey="porcentajes:5")])
    assert r["ok"] is True and r["omitidas"] == []
    assert [(p["hmores_ide"], p["parte_cod"], p["antes"]["can"],
             p["despues"]["can"], p["despues"]["tot"])
            for p in r["puestas"]] == [(7001, "PT26/00251", 0.3, 0.0, 0.0),
                                       (7002, "PT26/00251", 0.2, 0.0, 0.0)]
    assert [s["sql"] for s in cli.escritos] == ["a_cero", "a_cero"]
    assert cli.escritos[0]["parameters"] == {
        "ide": 7001, "reside": 200, "can_leido": 0.3, "synckey_leida": None,
        "hora": None}
    assert (_can(cli, 7001), _can(cli, 7002)) == (0.0, 0.0)
    assert sum("pone a 0 ide=7001" in m for m in caplog.messages) == 1
    assert not any("DELETE" in str(s) for s in cli.escritos)


def test_f054_r35_el_vinculado_con_su_hora_en_la_guarda():
    cli = _cli((7005, 5000, 0.4, "OTEL", "porcentajes:vin:3:5000"))
    r = _poner(cli, [_pedida(7005, recurso=5000, can=0.4, hora="OTEL",
                             synckey="porcentajes:vin:3:5000",
                             vinculado={"tipo": "TF", "cod": "TEL1"})])
    assert [p["hmores_ide"] for p in r["puestas"]] == [7005]
    assert cli.escritos[0]["parameters"]["hora"] == "OTEL"
    assert _can(cli, 7005) == 0.0


@pytest.mark.parametrize("pedida, motivo", [
    (_pedida(7001, can=0.5), MOTIVO_CAMBIADA),
    (_pedida(7001, synckey="porcentajes:1"), MOTIVO_CAMBIADA),
    (_pedida(7001, recurso=400), MOTIVO_OTRO_RECURSO),
    (_pedida(7001, hora="MJEFO"), MOTIVO_OTRA_HORA),
    (_pedida(7003, hora="OTEL", recurso=5000, can=0.1), MOTIVO_OTRA_HORA),
    (_pedida(7004, can=0.1, synckey="partes:9"), MOTIVO_OTRO_SISTEMA),
    (_pedida(9999), MOTIVO_NO_ESTA),
])
def test_f054_r35_lo_que_no_cumple_la_guarda_se_omite_sin_escribir(
        pedida, motivo):
    cli = _cli((7001, 200, 0.3, "MENC", None),
               (7003, 5000, 0.1, "OTEL", None),
               (7004, 200, 0.1, "MENC", "partes:9"))
    r = _poner(cli, [pedida])
    assert r["puestas"] == [] and r["omitidas"] == [
        {"hmores_ide": pedida["hmores_ide"], "motivo": motivo}]
    assert cli.escritos == []


def test_f054_r35_el_trabajador_solo_m():
    """Una línea del trabajador que no es `M*` no se toca aunque la hora
    enviada coincida."""
    cli = _cli((7001, 200, 0.3, "HLPE", None))
    r = _poner(cli, [_pedida(7001, hora="HLPE")])
    assert r["omitidas"] == [{"hmores_ide": 7001,
                              "motivo": MOTIVO_OTRA_HORA}]


def test_f054_r35_cerrada_o_enlazada_se_omite():
    cli = _cli((7001, 200, 0.3, "MENC", None), (7002, 200, 0.3, "MENC", None))
    cli.enlazadas = frozenset({7002})
    cli.lineas_por_parte = {888: [linea_previa(
        ide=7009, reside=200, can=0.3, tot=2700, hora_codigo="MENC")]}
    cli.periodo = [ParteSigrid(888, "PT26/00888", 3)]
    r = _poner(cli, [_pedida(7002), _pedida(7009), _pedida(7001)],
               obra_pruebas_forzar=False)
    assert r["omitidas"] == [
        {"hmores_ide": 7002, "motivo": MOTIVO_ENLAZADA},
        {"hmores_ide": 7009, "motivo": MOTIVO_PARTE_CERRADO}]
    assert [p["hmores_ide"] for p in r["puestas"]] == [7001]
    assert len(cli.escritos) == 1


def test_f054_r35_en_pruebas_solo_en_la_0404():
    cli = _cli((7001, 200, 0.3, "MENC", None))
    cli.lineas_por_parte = {888: [linea_previa(
        ide=7009, reside=200, can=0.3, tot=2700, hora_codigo="MENC")]}
    cli.periodo = [ParteSigrid(888, "PT26/00888", 1)]
    r = _poner(cli, [_pedida(7009), _pedida(7001)])
    assert r["omitidas"] == [{"hmores_ide": 7009,
                              "motivo": MOTIVO_FUERA_PRUEBAS}]
    assert [p["hmores_ide"] for p in r["puestas"]] == [7001]
    # En real, la del otro parte sí.
    cli = _cli((7001, 200, 0.3, "MENC", None))
    cli.lineas_por_parte = {888: [linea_previa(
        ide=7009, reside=200, can=0.3, tot=2700, hora_codigo="MENC")]}
    cli.periodo = [ParteSigrid(888, "PT26/00888", 1)]
    r = _poner(cli, [_pedida(7009)], obra_pruebas_forzar=False)
    assert [p["hmores_ide"] for p in r["puestas"]] == [7009]


def test_f054_r35_la_relectura_sin_el_cero_es_omitida():
    cli = _cli((7001, 200, 0.3, "MENC", None), (7002, 200, 0.2, "MENC", None))
    cli.guarda_falla = frozenset({7002})
    r = _poner(cli, [_pedida(7001), _pedida(7002, can=0.2)])
    assert [p["hmores_ide"] for p in r["puestas"]] == [7001]
    assert r["omitidas"] == [{"hmores_ide": 7002, "motivo": MOTIVO_NO_QUEDO}]
    assert len(cli.escritos) == 2


def test_f054_r35_sin_lineas_no_lee_ni_escribe():
    cli = _cli()
    assert _poner(cli, []) == {"ok": True, "puestas": [], "omitidas": []}
    assert cli.escritos == [] and not getattr(cli, "para_editar", [])


def test_f054_r36_tras_ponerla_a_cero_no_suma_y_la_omitida_si():
    """El `ejecutar` (y su preflight) releen del cliente: la puesta a 0 no
    suma en la jornada; la omitida, sí. `registro_pipeline.py` no cambia."""
    for falla, sobrecarga in ((frozenset(), False), (frozenset({7001}), True)):
        cli = _cli((7001, 200, 0.7, "MENC", None))
        cli.guarda_falla = falla
        _poner(cli, [_pedida(7001, can=0.7)])
        pf = RegistroPipeline(cliente=cli, settings=SettingsFalso()).preflight(
            obra=cli.obra_origen, lineas=[linea(porcentaje=0.5)])
        assert any(c.motivo == "sobrecarga"
                   for c in pf.conflictos) is sobrecarga


def test_f054_r35_ruta_poner_a_cero(monkeypatch):
    cli = _cli((7001, 200, 0.3, "MENC", None))
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4})
    api = TestClient(modulo_app.build_app(st))
    r = api.post("/api/registro/poner-a-cero", json={
        "empresa": 1, "ano": 2026, "mes": 7, "lineas": [_pedida(7001)]})
    assert r.status_code == 200, r.text
    assert [p["hmores_ide"] for p in r.json()["puestas"]] == [7001]
    r = api.post("/api/registro/poner-a-cero", json={
        "empresa": 1, "ano": 2026, "mes": 7,
        "lineas": [{"hmores_ide": 7001}]})
    assert r.status_code == 422
