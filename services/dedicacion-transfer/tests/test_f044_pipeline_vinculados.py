# tests/test_f044_pipeline_vinculados.py
"""F-044 · el pipeline con recursos vinculados.

- R9 (T5): `partidas/propuesta` propone la partida de cada subfila con la
  misma regla que el preflight (`partida_del_vinculado`): titular en `CI*`
  ⇒ la CI de su tipo; en postventa o en una partida no `CI*` ⇒ la del
  titular; sin hoja con la subcuenta o con varias ⇒ sin propuesta. Sin
  vinculados, la respuesta y las lecturas de hoy.
- R29 (T5): el lote da lo mismo que la petición suelta y lee las cuentas
  del presupuesto UNA vez por obra (y solo si alguna subfila las necesita).

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

from typing import Any

import pytest
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.partida_resolver import construir_catalogo
from application.services.reglas_vinculados import (
    PartidaTitular,
    partida_ci_del_tipo,
    partida_del_vinculado,
)
from domain.models.registro_models import HoraRecurso, ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    PRESUPUESTO_ORIGEN,
    ClienteFalso,
    SettingsFalso,
    _fila,
)
from tests.test_f055_lote import _ajustes

#: Presupuesto de la obra de origen con las hojas CI de los vinculados.
PRESUPUESTO_VIN = [
    *PRESUPUESTO_ORIGEN,
    _fila(81001, 80000, 3, "CICO13", "TELEFONIA"),
    _fila(81002, 80000, 4, "CIGA14", "GASOIL"),
    _fila(81003, 80000, 5, "CIVE20", "VEHICULO A"),
    _fila(81004, 80000, 6, "CIVE21", "VEHICULO B"),
    _fila(81100, 0, 7, "CD", "COSTES DIRECTOS"),
    _fila(81101, 81100, 1, "CD.1", "HORMIGON"),
]
CUENTAS_VIN = {81001: "0678.CI.4.13", 81002: "0678.CI.4.14",
               81003: "0678.CI.4.20", 81004: "0678.CI.4.20",
               81101: "0678.CD.1.1"}
#: Vinculados: 10 teléfono (CI.4.13), 11 gasoil (CI.4.14), 12 vehículo
#: (CI.4.20, dos hojas), 13 sin cuenta en su hora por defecto.
HORAS_VIN = {
    10: [HoraRecurso(31, "OTEL", None, 30.0, caa_cod="RES.CI.4.13",
                     defecto=True)],
    11: [HoraRecurso(32, "HLPE", None, 1.0, caa_cod="RES.CI.4.99"),
         HoraRecurso(33, "OGAS", None, 120.0, caa_cod="RES.CI.4.14",
                     defecto=True)],
    12: [HoraRecurso(34, "MESVE", None, 300.0, caa_cod="RES.CI.4.20",
                     defecto=True)],
    13: [HoraRecurso(35, "OKM", None, 0.0, defecto=True)],
}


class ClienteVin(ClienteFalso):
    """`ClienteFalso` con el presupuesto de los vinculados, sus horas y las
    cuentas del presupuesto (cada lectura, apuntada)."""

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.partidas_origen = PRESUPUESTO_VIN
        self.horas = {**self.horas, **HORAS_VIN}
        self.cuentas_leidas: list[int] = []
        self.horas_leidas: list[list[int]] = []

    def cuentas_del_presupuesto(self, obra_ide):
        self.cuentas_leidas.append(int(obra_ide))
        return dict(CUENTAS_VIN) if obra_ide == self.obra_origen.ide else {}

    def horas_de_recursos(self, resides):
        self.horas_leidas.append(sorted(resides))
        return super().horas_de_recursos(resides)


def _vin(*ides: int) -> list[dict]:
    return [{"recurso_ide": i, "tipo": "TF", "categoria": None,
             "cod": f"TF-{i}"} for i in ides]


def _linea(clave: str = "a", recurso: int = 200, pv: bool = False,
           paride: int | None = None, vinculados: list[dict] | None = None,
           categoria: str = "Encargado",
           nombre: str = "Acuna Mera, Antonio") -> dict:
    d = {"clave": clave, "recurso_ide": recurso, "nombre": nombre,
         "categoria": categoria, "es_postventa": pv}
    if paride is not None:
        d["paride"] = paride
    if vinculados is not None:
        d["vinculados"] = vinculados
    return d


def _proponer(cli: ClienteFalso, *lineas: dict) -> dict:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso()).proponer(
        empresa=1, obra=ObraEntrada(codigo=OBRA_ORIGEN), ano=2026, mes=7,
        lineas=list(lineas))


def _esperada(titular: PartidaTitular, recurso: int) -> dict | None:
    """Lo que decide la regla del preflight con las mismas entradas."""
    from application.services.cuenta_analitica import subcuenta_de_linea

    nodos = construir_catalogo(PRESUPUESTO_VIN)
    p = partida_del_vinculado(titular, None, True, lambda: partida_ci_del_tipo(
        nodos, CUENTAS_VIN, subcuenta_de_linea(HORAS_VIN[recurso], None)))
    if not p.paride:
        return None
    return {"paride": p.paride, "cod": p.cod, "res": p.res,
            "metodo": p.metodo, "origen": None}


# ================================ R9 ===================================== #
def test_f044_r9_titular_en_ci_cada_vinculado_a_la_ci_de_su_tipo():
    cli = ClienteVin()
    r = _proponer(cli, _linea(vinculados=_vin(10, 11, 12, 13)))
    assert r["propuestas"]["a"]["cod"] == "CI.1.10"     # el titular, en CI
    assert r["vinculados"] == {"a": {
        "10": {"paride": 81001, "cod": "CICO13", "res": "TELEFONIA",
               "metodo": "ci_tipo", "origen": None},
        "11": {"paride": 81002, "cod": "CIGA14", "res": "GASOIL",
               "metodo": "ci_tipo", "origen": None},
        "12": None,                                      # dos hojas
        "13": None,                                      # sin cuenta
    }}
    assert cli.cuentas_leidas == [555001]


def test_f044_r9_la_misma_partida_que_la_regla_del_preflight():
    r = _proponer(ClienteVin(), _linea(vinculados=_vin(10, 11, 12, 13)))
    titular = PartidaTitular(destino="obra", paride=80001, cod="CI.1.10",
                             res="ENCARGADO (ACUNA)", metodo="auto_nombre")
    assert r["vinculados"]["a"] == {
        str(i): _esperada(titular, i) for i in (10, 11, 12, 13)}


def test_f044_r9_titular_en_postventa_va_con_su_partida_sin_leer_cuentas():
    cli = ClienteVin()
    r = _proponer(cli, _linea("pv", pv=True, vinculados=_vin(10, 11)))
    pv = {"paride": 70001, "cod": "0678", "res": "15 VIVIENDAS Y HOSTEL",
          "metodo": "titular", "origen": None}
    assert r["vinculados"] == {"pv": {"10": pv, "11": pv}}
    assert cli.cuentas_leidas == []


def test_f044_r9_titular_con_elegida_no_ci_va_con_ella():
    cli = ClienteVin()
    r = _proponer(cli, _linea(paride=81101, vinculados=_vin(10)))
    assert r["vinculados"] == {"a": {"10": {
        "paride": 81101, "cod": "CD.1", "res": "HORMIGON",
        "metodo": "titular", "origen": None}}}
    assert cli.cuentas_leidas == []


def test_f044_r9_titular_con_elegida_ci_va_a_la_ci_del_tipo():
    r = _proponer(ClienteVin(), _linea(paride=80002, vinculados=_vin(10)))
    assert r["vinculados"]["a"]["10"]["paride"] == 81001


def test_f044_r9_titular_con_elegida_que_no_vale_no_propone():
    """Su titular se omitiría en el preflight («sigue al trabajador»)."""
    cli = ClienteVin()
    r = _proponer(cli, _linea(paride=80000, vinculados=_vin(10)))  # capítulo
    assert r["vinculados"] == {"a": {"10": None}}
    assert cli.cuentas_leidas == []


def test_f044_r9_titular_sin_propuesta_va_a_la_ci_del_tipo():
    r = _proponer(ClienteVin(), _linea(categoria="X", nombre="Nadie",
                                       vinculados=_vin(11)))
    assert r["propuestas"]["a"] is None
    assert r["vinculados"]["a"]["11"]["cod"] == "CIGA14"


def test_f044_r9_varias_lineas_una_lectura_de_cuentas_y_de_horas():
    cli = ClienteVin()
    r = _proponer(cli, _linea("a", vinculados=_vin(10)),
                  _linea("b", recurso=400, nombre="Otro",
                         vinculados=_vin(11, 12)),
                  _linea("c", recurso=300))
    assert set(r["vinculados"]) == {"a", "b"}
    assert cli.cuentas_leidas == [555001]
    assert cli.horas_leidas == [[10, 11, 12]]


@pytest.mark.parametrize("vinculados", [None, []])
def test_f044_r9_sin_vinculados_la_respuesta_y_las_lecturas_de_hoy(
        vinculados):
    con, sin = ClienteVin(), ClienteVin()
    r = _proponer(con, _linea(vinculados=vinculados), _linea("pv", pv=True))
    hoy = _proponer(sin, _linea(), _linea("pv", pv=True))
    assert r == hoy
    assert "vinculados" not in r
    assert con.cuentas_leidas == con.horas_leidas == []
    assert con.n_capitulos_de_obra == sin.n_capitulos_de_obra


# ================================ R29 ==================================== #
def _peticion(*lineas: dict) -> dict:
    return {"empresa": 1, "obra": ObraEntrada(codigo=OBRA_ORIGEN),
            "ano": 2026, "mes": 7, "lineas": list(lineas)}


def test_f044_r29_lote_igual_que_suelto():
    lineas = (_linea("a", vinculados=_vin(10, 12)),
              _linea("pv", pv=True, vinculados=_vin(11)))
    suelto = _proponer(ClienteVin(), *lineas)
    cli = ClienteVin()
    [lote] = RegistroLote(cliente=cli, settings=_ajustes()).proponer(
        [_peticion(*lineas)])
    assert lote == {"ok": True, "propuestas": suelto["propuestas"],
                    "vinculados": suelto["vinculados"]}


def test_f044_r29_lote_cuentas_una_vez_por_obra_y_horas_precargadas():
    peticiones = [_peticion(_linea("a", vinculados=_vin(10))),
                  _peticion(_linea("b", recurso=400, nombre="Otro",
                                   vinculados=_vin(11)))]
    cli = ClienteVin()
    r = RegistroLote(cliente=cli, settings=_ajustes()).proponer(
        peticiones)
    assert [x["vinculados"] for x in r] == [
        _proponer(ClienteVin(), *p["lineas"])["vinculados"]
        for p in peticiones]
    assert r[0]["vinculados"]["a"]["10"]["cod"] == "CICO13"
    assert cli.cuentas_leidas == [555001]
    assert cli.horas_leidas == [[10, 11]]


def test_f044_r29_lote_sin_vinculados_como_hoy():
    cli = ClienteVin()
    [r] = RegistroLote(cliente=cli, settings=_ajustes()).proponer(
        [_peticion(_linea("a"))])
    assert set(r) == {"ok", "propuestas"}
    assert cli.cuentas_leidas == cli.horas_leidas == []


# ======================= R9 · las rutas de propuesta ===================== #
@pytest.fixture
def api(monkeypatch):
    """(TestClient) con el cliente de Sigrid sustituido por `cli`."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    def fabricar(cli):
        monkeypatch.setattr(modulo_app, "SigridWriteClient",
                            lambda **kw: cli)
        ajustes = SimpleNamespace(**AJUSTES, sigrid_lecturas_paralelas=4)
        return TestClient(modulo_app.build_app(ajustes))
    return fabricar


def _cuerpo(*lineas: dict) -> dict:
    return {"empresa": 1, "obra": {"codigo": OBRA_ORIGEN}, "ano": 2026,
            "mes": 7, "lineas": list(lineas)}


def test_f044_r9_la_ruta_devuelve_los_vinculados(api):
    r = api(ClienteVin()).post("/api/partidas/propuesta", json=_cuerpo(
        _linea(vinculados=_vin(10)), _linea("pv", pv=True)))
    assert r.status_code == 200
    assert r.json()["vinculados"] == {"a": {"10": {
        "paride": 81001, "cod": "CICO13", "res": "TELEFONIA",
        "metodo": "ci_tipo", "origen": None}}}


def test_f044_r9_la_ruta_sin_vinculados_pasa_la_linea_de_hoy(api,
                                                              monkeypatch):
    """Sin `paride` ni `vinculados`, el pipeline recibe las cinco claves de
    siempre; con ellos, también esos."""
    recibidas: list[list[dict]] = []
    original = RegistroPipeline.proponer

    def espia(self, **kw):
        recibidas.append(kw["lineas"])
        return original(self, **kw)

    monkeypatch.setattr(RegistroPipeline, "proponer", espia)
    cliente = api(ClienteVin())
    r = cliente.post("/api/partidas/propuesta", json=_cuerpo(_linea()))
    assert "vinculados" not in r.json()
    cliente.post("/api/partidas/propuesta", json=_cuerpo(
        _linea(paride=80001, vinculados=_vin(10))))
    assert recibidas == [
        [_linea()],
        [{**_linea(), "paride": 80001, "vinculados": [
            {"recurso_ide": 10, "tipo": "TF", "categoria": None,
             "cod": "TF-10"}]}]]


def test_f044_r29_la_ruta_del_lote_devuelve_los_vinculados(api):
    r = api(ClienteVin()).post("/api/partidas/propuesta-lote", json={
        "peticiones": [_cuerpo(_linea(vinculados=_vin(10))),
                       _cuerpo(_linea("b"))]})
    assert r.status_code == 200
    a, b = r.json()["obras"]
    assert a["vinculados"]["a"]["10"]["cod"] == "CICO13"
    assert set(b) == {"ok", "propuestas"}
