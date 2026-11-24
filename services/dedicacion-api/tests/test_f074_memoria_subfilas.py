# tests/test_f074_memoria_subfilas.py
"""F-074 · T8: al cambiar la partida del titular, sus subfilas salen de la
memoria de «sin propuesta» y se recalculan (R15).

`CambiarPartida` borra la propuesta de las subfilas de la línea (F-044 R9);
con F-074 avisa a la memoria de las propuestas del mes ANTES de que la ruta
encole, para que la cola las vuelva a pedir con la partida nueva. Sin red ni
BBDD.
"""
from __future__ import annotations

from application.use_cases import CambiarPartida
from domain.models import FiltroEmpresa
from tests.test_f024_cuadrante_empresa import ANIO, MES, P_ACT
from tests.test_f024_rutas_empresa import (  # noqa: F401  (fixture `api`)
    _PropuestasFalsas,
    api,
)
from tests.test_f044_cuadrante_vinculados import (
    GAS,
    TEL,
    _con,
    _mes,
    _periodos_abiertos,
    _TransferLote,
    _uow_selector,
)
from tests.test_f044_cuadrante_vinculados import _ln as _ln_vin

FILTRO = FiltroEmpresa(empresa=1, por_defecto=1, empresa_obras=1)
PARTIDA = {"ide": 80001, "cod": "CI.1.10", "res": "ENCARGADO"}


def _sin_propuesta(ps):
    return {"ok": True, "obras": [
        {"ok": True, "propuestas": {}, "vinculados": {
            ln["clave"]: {str(v["recurso_ide"]): None
                          for v in ln.get("vinculados", [])}
            for ln in p["lineas"]}} for p in ps]}


def test_f074_r15_olvidar_subfilas_solo_las_de_esa_linea():
    uow = _uow_selector(_con(_ln_vin(100, "60"), TEL, GAS),
                        _con(_ln_vin(101, "40"), TEL))
    _periodos_abiertos(uow)
    m = _mes(uow, _TransferLote(_sin_propuesta))
    _, marcas = m.encolar_marcas(ANIO, MES)
    assert set(marcas.subfilas_no_encontradas) == {
        (10, 100, False, 10), (10, 100, False, 11), (10, 101, False, 10)}
    m.olvidar_subfilas(P_ACT, 10, 100, False)
    assert set(m._foto(P_ACT)[1].subfilas_no_encontradas) == {
        (10, 101, False, 10)}


def test_f074_r15_cambiar_la_del_titular_las_recalcula():
    uow = _uow_selector(_con(_ln_vin(100, "60"), TEL))
    _periodos_abiertos(uow)
    t = _TransferLote(_sin_propuesta)
    m = _mes(uow, t)
    m.encolar_marcas(ANIO, MES)
    m.encolar_marcas(ANIO, MES)
    assert len(t.peticiones) == 1                  # en memoria: no se repite
    CambiarPartida(al_borrar_subfilas=m.olvidar_subfilas).ejecutar(
        uow, ANIO, MES, 10, 100, False, PARTIDA, "ana", filtro=FILTRO)
    m.encolar_marcas(ANIO, MES)
    assert len(t.peticiones) == 2                  # se recalcula
    assert t.peticiones[1][0]["lineas"][0]["vinculados"][0][
        "recurso_ide"] == 10


def test_f074_r15_cambiar_la_de_una_subfila_no_olvida_nada():
    llamadas = []
    uow = _uow_selector(_con(_ln_vin(100, "60"), TEL))
    _periodos_abiertos(uow)
    CambiarPartida(al_borrar_subfilas=lambda *a: llamadas.append(a)).ejecutar(
        uow, ANIO, MES, 10, 100, False, PARTIDA, "ana", filtro=FILTRO,
        vinculado_ide=10)
    assert llamadas == []


def test_f074_r15_sin_subfilas_o_sin_cambio_no_avisa():
    llamadas = []
    uow = _uow_selector(_ln_vin(100, "60"))
    _periodos_abiertos(uow)
    CambiarPartida(al_borrar_subfilas=lambda *a: llamadas.append(a)).ejecutar(
        uow, ANIO, MES, 10, 100, False, PARTIDA, "ana", filtro=FILTRO)
    uow2 = _uow_selector(_con(_ln_vin(100, "60"), TEL))
    _periodos_abiertos(uow2)
    CambiarPartida(al_borrar_subfilas=lambda *a: llamadas.append(a)).ejecutar(
        uow2, ANIO, MES, 10, 100, False, None, "ana", filtro=FILTRO)
    assert llamadas == []


def test_f074_r15_avisa_con_la_linea():
    llamadas = []
    uow = _uow_selector(_con(_ln_vin(100, "60"), TEL))
    _periodos_abiertos(uow)
    CambiarPartida(al_borrar_subfilas=lambda *a: llamadas.append(a)).ejecutar(
        uow, ANIO, MES, 10, 100, False, PARTIDA, "ana", filtro=FILTRO)
    assert llamadas == [(P_ACT, 10, 100, False)]


def test_f074_r15_la_ruta_lo_cablea_antes_de_encolar(api, monkeypatch):  # noqa: F811
    """La ruta da a `CambiarPartida` el `olvidar_subfilas` de la cola, y lo
    que olvida pasa ANTES de encolar al trabajador."""
    from interface_adapters.api import routes

    cliente, contenedor = api
    orden, recibido = [], {}

    class _ConMemoria(_PropuestasFalsas):
        def olvidar_subfilas(self, *linea):
            orden.append(("olvidar", linea))

        def encolar(self, anio, mes, trabajadores=None):
            orden.append(("encolar", trabajadores))
            return super().encolar(anio, mes, trabajadores)

    class _Espia(CambiarPartida):
        def __init__(self, **kw):
            recibido.update(kw)
            super().__init__(**kw)

        def ejecutar(self, *a, **kw):
            # Como si la línea tuviera subfilas y su partida cambiara.
            recibido["al_borrar_subfilas"](P_ACT, 10, 100, False)
            return super().ejecutar(*a, **kw)

    contenedor.propuestas_mes = _ConMemoria()
    monkeypatch.setattr(routes, "CambiarPartida", _Espia)
    base = f"/api/v1/periodos/{ANIO}/{MES}/trabajadores/10"
    cliente.put(f"{base}/asignaciones",
                json={"lineas": [{"obra_ide": 100, "porcentaje": 100}]},
                headers={"X-Usuario": "ana"})
    orden.clear()
    r = cliente.put(f"{base}/partida", json={
        "obra_ide": 100, "es_postventa": False, "partida": PARTIDA},
        headers={"X-Usuario": "ana"})
    assert r.status_code == 200, r.text
    assert recibido["al_borrar_subfilas"] == (
        contenedor.propuestas_mes.olvidar_subfilas)
    assert orden == [("olvidar", (P_ACT, 10, 100, False)),
                     ("encolar", [10])]