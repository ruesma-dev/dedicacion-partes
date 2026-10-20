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
