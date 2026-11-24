# tests/test_f074_estados.py
"""F-074 · T6-T7: el estado de la partida de cada línea y subfila, que
decide la api y el front solo pinta (R13, R14, R19).

- R13: la línea normal sin elegida ni propuesta guardada en la memoria de
  «sin propuesta» publica `propuesta_no_encontrada: true` y su motivo (el del
  transfer o el error de su obra `{ok: false}`), en el cuadrante, en cada
  escritura y en `GET …/propuestas` (`no_encontradas`); de la misma foto de
  la cola que `pendientes`; las claves, solo con valor.
- R14: la subfila, `propuesta_pendiente` en su cola y
  `propuesta_no_encontrada` con su motivo en su memoria; `…/propuestas` gana
  `subfilas_pendientes` y `subfilas_no_encontradas`, solo con alguna.

Sin red ni BBDD.
"""
from __future__ import annotations

import dataclasses

from application.estado_partida import Marcas, estado_de_linea, estado_de_subfila
from interface_adapters.api.schemas import PropuestasOut, a_trabajador_out
from tests.test_f024_cuadrante_empresa import ANIO, MES, P_ACT
from tests.test_f024_rutas_empresa import (  # noqa: F401  (fixture `api`)
    _PropuestasFalsas,
    api,
)
from tests.test_f044_cuadrante_vinculados import (
    TEL,
    _con,
    _mes,
    _periodos_abiertos,
    _TransferLote,
    _uow_selector,
)
from tests.test_f044_cuadrante_vinculados import _ln as _ln_vin
from tests.test_f055_propuesta_guardada import DEL_TRANSFER, PR, _lp
from tests.test_f055_propuestas_mes import _pm, _Retenido, _Transfer, _uow_cm

MOTIVO = "ningún paso de la regla da partida"
BASE = f"/api/v1/periodos/{ANIO}/{MES}"


class _TransferConMotivos(_Transfer):
    """El de F-055 con `motivos` (R9) en las obras que van bien."""

    def __init__(self, *a, motivos=None, **kw) -> None:
        super().__init__(*a, **kw)
        self.motivos = motivos or {}

    def propuesta_lote(self, peticiones):
        r = super().propuesta_lote(peticiones)
        for p, o in zip(peticiones, r["obras"]):
            m = {l["clave"]: self.motivos[l["clave"]] for l in p["lineas"]
                 if l["clave"] in self.motivos}
            if o.get("ok") and m:
                o["motivos"] = m
        return r


# ============================ R13 · la cola ============================== #
def test_f074_r13_la_memoria_guarda_el_motivo_del_transfer():
    uow = _uow_cm({14: [_lp(100, "60"), _lp(101, "40")]})
    t = _TransferConMotivos({(14, 101): DEL_TRANSFER}, motivos={"14": MOTIVO})
    en_curso, marcas = _pm(uow, t).encolar_marcas(ANIO, MES)
    assert en_curso is False
    assert marcas.no_encontradas == {(14, 100, False): MOTIVO}
    assert marcas.pendientes == frozenset()


def test_f074_r13_obra_ok_false_el_motivo_es_su_error():
    uow = _uow_cm({14: [_lp(100, "100")]})
    _, marcas = _pm(uow, _Transfer(fallan={100})).encolar_marcas(ANIO, MES)
    assert marcas.no_encontradas == {(14, 100, False): "otra empresa"}


def test_f074_r13_sin_motivo_del_transfer_queda_nulo():
    uow = _uow_cm({14: [_lp(100, "100")]})
    _, marcas = _pm(uow, _Transfer()).encolar_marcas(ANIO, MES)
    assert marcas.no_encontradas == {(14, 100, False): None}


def test_f074_r13_pendiente_y_no_encontrada_son_excluyentes():
    uow = _uow_cm({14: [_lp(100, "100")]})
    ejecutor = _Retenido()
    pm = _pm(uow, _TransferConMotivos(motivos={"14": MOTIVO}), ejecutor)
    en_curso, marcas = pm.encolar_marcas(ANIO, MES)
    assert en_curso and marcas.pendientes == {(14, 100, False)}
    assert marcas.no_encontradas == {}
    ejecutor.soltar()
    en_curso, marcas = pm.encolar_marcas(ANIO, MES)
    assert not en_curso and marcas.pendientes == frozenset()
    assert marcas.no_encontradas == {(14, 100, False): MOTIVO}
    assert ejecutor.pendientes == []               # no se reencola


def test_f074_r13_encolar_sigue_dando_solo_las_pendientes():
    uow = _uow_cm({14: [_lp(100, "100")]})
    pm = _pm(uow, _Transfer(), _Retenido())
    assert pm.encolar(ANIO, MES) == (True, frozenset({(14, 100, False)}))


def test_f074_r13_tras_el_sync_se_olvidan_con_su_motivo():
    uow = _uow_cm({14: [_lp(100, "100")]})
    pm = _pm(uow, _TransferConMotivos(motivos={"14": MOTIVO}))
    pm.encolar_marcas(ANIO, MES)
    pm.olvidar()
    assert pm._foto(P_ACT)[1].no_encontradas == {}


def test_f074_r13_estado_con_no_encontradas_solo_si_hay():
    uow = _uow_cm({14: [_lp(100, "60"), _lp(101, "40", **PR)]})
    pm = _pm(uow, _TransferConMotivos(motivos={"14": MOTIVO}))
    assert "no_encontradas" not in pm.estado(uow, ANIO, MES)
    pm.encolar_marcas(ANIO, MES)
    r = pm.estado(uow, ANIO, MES)
    assert r["no_encontradas"] == [{"trabajador_ide": 14, "obra_ide": 100,
                                    "es_postventa": False, "motivo": MOTIVO}]
    assert "subfilas_pendientes" not in r
    assert "subfilas_no_encontradas" not in r
    assert PropuestasOut(**r).no_encontradas[0].motivo == MOTIVO


# ===================== R13 · las claves de la línea ====================== #
def test_f074_r13_linea_no_encontrada_con_motivo():
    out = estado_de_linea(14, _lp(100, "60"), Marcas(
        no_encontradas={(14, 100, False): MOTIVO}))
    assert out == {"propuesta_cod": None, "propuesta_res": None,
                   "propuesta_metodo": None, "propuesta_pendiente": False,
                   "propuesta_no_encontrada": True,
                   "propuesta_motivo": MOTIVO}


def test_f074_r13_sin_motivo_sin_la_clave_del_motivo():
    out = estado_de_linea(14, _lp(100, "60"), Marcas(
        no_encontradas={(14, 100, False): None}))
    assert out["propuesta_no_encontrada"] is True
    assert "propuesta_motivo" not in out


def test_f074_r13_elegida_propuesta_o_fija_mandan_sobre_la_memoria():
    marcas = Marcas(no_encontradas={(14, 100, False): MOTIVO})
    for ln in (_lp(100, "60", partida_ide=1), _lp(100, "60", **PR),
               _lp(100, "60", partida_fija=True)):
        assert "propuesta_no_encontrada" not in estado_de_linea(14, ln,
                                                               marcas)


def test_f074_r13_cuadrante_publica_las_claves_solo_con_valor():
    from domain.models import CuadranteTrabajador, Trabajador

    fila = CuadranteTrabajador(
        trabajador=Trabajador(ide=14, cod=None, nombre="Eva", dni=None,
                             categoria="Encargado"),
        lineas=[_lp(100, "60"), _lp(101, "40")])
    out = a_trabajador_out(fila, 1, marcas=Marcas(
        no_encontradas={(14, 100, False): MOTIVO})).model_dump()
    [l100, l101] = out["lineas"]
    assert (l100["propuesta_no_encontrada"], l100["propuesta_motivo"]) == (
        True, MOTIVO)
    assert "propuesta_no_encontrada" not in l101
    assert "propuesta_motivo" not in l101
    # Sin marcas, la salida de siempre (`pendientes` sigue valiendo).
    sin = a_trabajador_out(fila, 1, frozenset({(14, 101, False)})).model_dump()
    assert sin["lineas"][1]["propuesta_pendiente"] is True
    assert "propuesta_no_encontrada" not in sin["lineas"][0]


def test_f074_r13_rutas_publican_las_marcas_de_la_cola(api):  # noqa: F811
    cliente, contenedor = api

    class _ConMarcas(_PropuestasFalsas):
        def encolar_marcas(self, anio, mes, trabajadores=None):
            self.lanzar(anio, mes, trabajadores)
            return True, Marcas(no_encontradas={(10, 100, False): MOTIVO})

    contenedor.propuestas_mes = _ConMarcas(en_curso=True)
    cliente.put(f"{BASE}/trabajadores/10/asignaciones",
                json={"lineas": [{"obra_ide": 100, "porcentaje": 100}]},
                headers={"X-Usuario": "ana"})
    r = cliente.get(f"{BASE}/cuadrante")
    assert r.status_code == 200, r.text
    [t10] = [t for t in r.json()["trabajadores"] if t["ide"] == 10]
    assert t10["lineas"][0]["propuesta_no_encontrada"] is True
    assert t10["lineas"][0]["propuesta_motivo"] == MOTIVO


def test_f074_r13_ruta_propuestas_sin_listas_vacias(api):  # noqa: F811
    cliente, contenedor = api
    r = cliente.get(f"{BASE}/propuestas")
    assert r.status_code == 200, r.text
    assert not {"no_encontradas", "subfilas_pendientes",
                "subfilas_no_encontradas"} & set(r.json())


# ============================ R14 · subfilas ============================= #
def test_f074_r14_subfila_en_su_cola_y_en_su_memoria():
    uow = _uow_selector(_con(_ln_vin(100, "60"), TEL))
    _periodos_abiertos(uow)
    t = _TransferLote(lambda ps: {"ok": True, "obras": [
        {"ok": True, "propuestas": {"10": None},
         "motivos_vinculados": {"10": {"10": "sin cuenta"}},
         "vinculados": {"10": {"10": None}}}]})
    m = _mes(uow, t)
    _, marcas = m.encolar_marcas(ANIO, MES)
    assert marcas.subfilas_no_encontradas == {(10, 100, False, 10):
                                              "sin cuenta"}
    r = m.estado(uow, ANIO, MES)
    assert r["subfilas_no_encontradas"] == [{
        "trabajador_ide": 10, "obra_ide": 100, "es_postventa": False,
        "vinculado_ide": 10, "motivo": "sin cuenta"}]
    assert PropuestasOut(**r).subfilas_no_encontradas[0].vinculado_ide == 10


def test_f074_r14_subfila_pendiente_mientras_se_calcula():
    from application.propuestas_mes import PropuestasDelMes

    uow = _uow_selector(_con(_ln_vin(100, "60"), TEL))
    _periodos_abiertos(uow)

    class _Fabrica:
        def __call__(self):
            return self

        def __enter__(self):
            return uow

        def __exit__(self, *exc):
            return None

    ejecutor = _Retenido()
    m = PropuestasDelMes(_Fabrica(), _TransferLote(lambda ps: {}), ejecutor,
                         empresa_obras=1)
    en_curso, marcas = m.encolar_marcas(ANIO, MES)
    assert en_curso and marcas.subfilas_pendientes == {(10, 100, False, 10)}
    assert m.estado(uow, ANIO, MES)["subfilas_pendientes"] == [{
        "trabajador_ide": 10, "obra_ide": 100, "es_postventa": False,
        "vinculado_ide": 10}]


def test_f074_r14_claves_de_la_subfila():
    ln = _con(_ln_vin(100, "60"), TEL)
    v = ln.vinculados[0]
    clave = (10, 100, False, v.vinculado_ide)
    assert estado_de_subfila(10, ln, v, Marcas(
        subfilas_pendientes=frozenset({clave})))["propuesta_pendiente"] is True
    out = estado_de_subfila(10, ln, v, Marcas(
        subfilas_no_encontradas={clave: "sin cuenta"}))
    assert (out["propuesta_no_encontrada"], out["propuesta_motivo"]) == (
        True, "sin cuenta")
    assert estado_de_subfila(10, ln, v) == {
        "propuesta_cod": None, "propuesta_res": None,
        "propuesta_metodo": None}
    elegida = dataclasses.replace(v, partida_ide=5)
    assert "propuesta_no_encontrada" not in estado_de_subfila(
        10, ln, elegida, Marcas(subfilas_no_encontradas={clave: "x"}))


def test_f074_r14_cuadrante_marca_la_subfila_solo_con_valor():
    from domain.models import CuadranteTrabajador, Trabajador

    ln = _con(_ln_vin(100, "60"), TEL)
    fila = CuadranteTrabajador(
        trabajador=Trabajador(ide=10, cod=None, nombre="Ana", dni=None,
                             categoria="Encargado"),
        lineas=[ln])
    clave = (10, 100, False, ln.vinculados[0].vinculado_ide)
    [sub] = a_trabajador_out(fila, 1, marcas=Marcas(
        subfilas_no_encontradas={clave: "sin cuenta"})).model_dump()[
        "lineas"][0]["vinculados"]
    assert (sub["propuesta_no_encontrada"], sub["propuesta_motivo"]) == (
        True, "sin cuenta")
    assert "propuesta_pendiente" not in sub
    [sin] = a_trabajador_out(fila, 1).model_dump()["lineas"][0]["vinculados"]
    assert not {"propuesta_pendiente", "propuesta_no_encontrada",
                "propuesta_motivo"} & set(sin)
