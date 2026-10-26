# tests/test_f044_lote.py
"""F-044 · Los vinculados en el lote de F-055 (R11, R27, R29; design §6.3).

Sin vinculados, el preflight es el de hoy: la misma salida (más
`vinculados: []`) y las mismas lecturas. Con ellos, el lote da lo mismo que
el suelto, sin fallos de memoria (sus horas, sus líneas, sus `synckey` y
sus partidas, precargadas con las de los titulares) y con UNA lectura de
cuentas del presupuesto por obra, solo si alguna subfila la pide.

Sin red ni BBDD: el `ClientePre` de `test_f044_pipeline_vinculados.py`. Los
`ide` son inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

import copy
from dataclasses import asdict

from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.lecturas_lote import LecturasDelLote
from domain.models.registro_models import ObraEntrada

from tests.conftest import OBRA_ORIGEN, SettingsFalso, linea, linea_previa
from tests.test_f044_pipeline_vinculados import ClientePre, _ls_vin, _v

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)


def _st() -> SettingsFalso:
    st = SettingsFalso()
    st.sigrid_lecturas_paralelas = 4
    return st


def _cli() -> ClientePre:
    """Un parte En registro con la línea al 0 % del teléfono 10, dos
    choques del gasoil 11 y la del 12 que ya escribimos (su traza). Los
    trabajadores 201 y 202, con las horas del 200."""
    cli = ClientePre(lineas_parte=[
        _ls_vin(5201, 10, 0.0, paride=81001),
        _ls_vin(5102, 11, 0.5, paride=81002),
        _ls_vin(5101, 11, 0.45, paride=81002),
        _ls_vin(5301, 12, 0.4, synckey="porcentajes:vin:3:12")])
    cli.horas = {**cli.horas, 201: cli.horas[200], 202: cli.horas[200]}
    return cli


def _peticiones(con_vinculados: bool = True) -> list[tuple]:
    v = _v if con_vinculados else (lambda *a, **k: [])
    return [
        # CI del titular: el 10 y el 11 a la CI de su tipo (cuentas).
        (OBRA, [linea(registro_id=1, paride=80001, partida_cod="CI.1.10",
                      vinculados=v(10, 11)),
                # elegida en la subfila (validar_partidas) y propuesta
                # guardada (sin cuentas).
                linea(registro_id=2, recurso_ide=201, vinculados=[
                    *v(10, paride=81002, partida_cod="CIGA14"),
                    *v(11, propuesta_paride=81002, propuesta_cod="CIGA14",
                       propuesta_res="GASOIL", propuesta_metodo="ci_tipo")])]),
        # la misma obra otra vez (una sola lectura de cuentas) y un
        # vinculado ya registrado por su `hmores_ide`.
        (OBRA, [linea(registro_id=3, recurso_ide=202, paride=80001,
                      partida_cod="CI.1.10",
                      vinculados=v(12, hmores_ide=5301))]),
    ]


def _suelto(cli, obra, lineas):
    return RegistroPipeline(cliente=cli, settings=_st()).preflight(
        obra=obra, lineas=lineas)


def _sin_vinculados(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "vinculados"}


def test_f044_r11_sin_vinculados_la_salida_y_las_lecturas_de_hoy():
    """Sin vinculados no hay ni una lectura más: horas, líneas y lo ya
    registrado solo con los titulares; nada de cuentas del presupuesto."""
    cli = _cli()
    [(obra, lineas)] = _peticiones(False)[1:]
    pf = _suelto(cli, obra, lineas)
    assert pf.vinculados == []
    assert cli.cuentas_leidas == []
    assert cli.horas_leidas == [[202]]
    assert cli.lecturas_lineas == [(777, [202])]
    assert cli.registradas == [(["porcentajes:3"], [])]
    d = asdict(pf)
    assert d["vinculados"] == []
    assert not [c for c in d["conflictos"] if c["vinculado"]]


def test_f044_r11_sin_vinculados_lote_igual_que_suelto_y_sin_fallos():
    cli = _cli()
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar(_peticiones(False), _st())
    for obra, lineas in _peticiones(False):
        _suelto(memoria, obra, lineas)
    assert memoria.fallos_de_memoria == {}
    lote = RegistroLote(cliente=_cli(), settings=_st()).preflight(
        _peticiones(False))
    for (obra, lineas), r in zip(_peticiones(False), lote, strict=True):
        assert asdict(r) == asdict(_suelto(_cli(), obra, lineas))
        assert r.vinculados == []


def test_f044_r29_con_vinculados_lote_igual_que_suelto():
    lote = RegistroLote(cliente=_cli(), settings=_st()).preflight(
        _peticiones())
    for (obra, lineas), r in zip(_peticiones(), lote, strict=True):
        suelto = _suelto(_cli(), obra, lineas)
        assert asdict(r) == asdict(suelto)
    a, b = lote
    assert {(v.registro_id, v.recurso_ide): v.accion
            for v in [*a.vinculados, *b.vinculados]} == {
        (1, 10): "escribir", (1, 11): "escribir", (2, 10): "escribir",
        (2, 11): "escribir", (3, 12): "ya_registrado"}


def test_f044_r27_con_vinculados_el_lote_no_tiene_fallos_de_memoria():
    """Horas, líneas de los partes, `synckey`/`hmores.ide` y partidas de
    los vinculados: precargadas en las mismas lecturas de los titulares."""
    cli = _cli()
    memoria = LecturasDelLote(cli, 2)
    memoria.precargar(_peticiones(), _st())
    for obra, lineas in _peticiones():
        _suelto(memoria, obra, lineas)
    assert memoria.fallos_de_memoria == {}
    assert cli.horas_leidas == [[10, 11, 12, 200, 201, 202]]
    assert cli.cuentas_leidas == [555001]       # una vez por obra
    assert len(cli.registradas) == 1


def test_f044_r29_lote_sin_subfila_que_pida_cuentas_no_las_lee():
    cli = _cli()
    RegistroLote(cliente=cli, settings=_st()).preflight([
        (OBRA, [linea(vinculados=_v(10, paride=81001,
                                    partida_cod="CICO13"))])])
    assert cli.cuentas_leidas == []


def test_f044_r11_lote_las_peticiones_no_se_tocan():
    """El lote no muta las entradas (una petición se puede repetir)."""
    pet = _peticiones()
    antes = copy.deepcopy(pet)
    RegistroLote(cliente=_cli(), settings=_st()).preflight(pet)
    assert pet == antes


def test_f044_r27_un_titular_ya_registrado_no_impide_precargar_el_suyo():
    previa = linea_previa(ide=6001, can=0.4, paride=80001,
                          synckey="porcentajes:1")
    cli = _cli()
    cli.synckeys = {"porcentajes:1": previa}
    memoria = LecturasDelLote(cli, 2)
    pet = [(OBRA, [linea(paride=80001, partida_cod="CI.1.10",
                         vinculados=_v(10))])]
    memoria.precargar(pet, _st())
    [pf] = [_suelto(memoria, *p) for p in pet]
    assert memoria.fallos_de_memoria == {}
    assert pf.acciones[0].accion == "ya_registrado"
    assert pf.vinculados[0].accion == "escribir"
