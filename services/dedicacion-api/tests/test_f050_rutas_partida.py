# tests/test_f050_rutas_partida.py
"""F-050 · Rutas de la partida de una línea: `PUT …/partida` (R13), los
campos de partida de cada línea (R18) y `GET …/partidas` (R17).

`TestClient` sobre la app real con el contenedor sustituido: la UnitOfWork
en memoria de F-024 con el `reemplazar` de `test_f050_partida_linea.py` (que
conserva la partida) y unos eventos que anotan su tipo; para R17, un
transfer falso. Sin red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Self

import pytest
from config.settings import Settings
from domain.models import EstadoPeriodo, Periodo
from fastapi.testclient import TestClient
from interface_adapters.api.app import build_app
from interface_adapters.api.deps import obtener_contenedor

from tests.test_f024_cuadrante_empresa import ANIO, MES, P_ACT, _Eventos
from tests.test_f050_partida_linea import P, _AsignacionesConPartida, _lp, _Uow

BASE = f"/api/v1/periodos/{ANIO}/{MES}"
PARTIDA = {"ide": 80003, "cod": "CI.1.9", "res": "ADMINISTRATIVO"}


class _EventosConTipo(_Eventos):
    def __init__(self) -> None:
        super().__init__()
        self.tipos: list[tuple] = []

    def registrar(self, periodo_id, ide, tipo, usuario, antes, despues):
        self.tipos.append((ide, tipo.value, usuario, antes, despues))
        super().registrar(periodo_id, ide, tipo, usuario, antes, despues)


class _AsignacionesR15(_AsignacionesConPartida):
    """F-055 (R15; lista cerrada): el selector guarda la propuesta; aquí
    solo se anota."""

    def guardar_propuesta(self, periodo_id, ide, clave, propuesta, *,
                          solo_si_vacia=False):
        self._uow.propuestas_guardadas.append((ide, clave, propuesta))
        return True


class _UowCM(_Uow):
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class _PeriodoCerrado:
    def obtener(self, anio, mes):
        return P_ACT, Periodo(anio, mes, EstadoPeriodo.CERRADO)


def _cliente(lineas, monkeypatch, **extra):
    monkeypatch.delenv("EMPRESA_IMPUTACION", raising=False)
    settings = Settings(_env_file=None)
    uow = _UowCM({P_ACT: lineas})
    uow.asignaciones = _AsignacionesR15(uow)
    uow.propuestas_guardadas = []
    uow.eventos = _EventosConTipo()
    # F-055 (R29-R37; lista cerrada): las propuestas del mes, falsas.
    from tests.test_f024_rutas_empresa import _PropuestasFalsas
    contenedor = SimpleNamespace(settings=settings, uow=lambda: uow,
                                 propuestas_mes=_PropuestasFalsas(), **extra)
    app = build_app(settings)
    app.dependency_overrides[obtener_contenedor] = lambda: contenedor
    return TestClient(app), uow


def _put(cliente, ide=14, *, obra=100, pv=False, partida=PARTIDA,
         usuario="ana"):
    return cliente.put(f"{BASE}/trabajadores/{ide}/partida",
                       headers={"X-Usuario": usuario},
                       json={"obra_ide": obra, "es_postventa": pv,
                             "partida": partida})


def _lineas_de(cuerpo):
    return [(ln["obra_ide"], ln["partida_ide"], ln["partida_cod"],
             ln["partida_res"]) for ln in cuerpo["trabajador"]["lineas"]]


# ================================ R13 ==================================== #
def test_f050_r13_cambia_solo_esa_linea_y_deja_evento(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "60"), _lp(101, "40")]},
                            monkeypatch)
    r = _put(cliente)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert _lineas_de(cuerpo) == [(100, 80003, "CI.1.9", "ADMINISTRATIVO"),
                                  (101, None, None, None)]
    assert cuerpo["resumen"]["total"] == 2
    assert [(i, t, u) for i, t, u, _, _ in uow.eventos.tipos] == [
        (14, "PARTIDA", "ana")]
    _, _, _, antes, despues = uow.eventos.tipos[0]
    assert antes == [
        {"obra_ide": 100, "es_postventa": False, "porcentaje": "60"},
        {"obra_ide": 101, "es_postventa": False, "porcentaje": "40"}]
    assert despues[0] == {"obra_ide": 100, "es_postventa": False,
                          "porcentaje": "60", **P}
    assert [str(ln.porcentaje) for ln in uow.lineas[P_ACT][14]] == [
        "60", "40"]


def test_f050_r13_null_vuelve_a_automatica(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "100", **P)]}, monkeypatch)
    r = _put(cliente, partida=None)
    assert r.status_code == 200, r.text
    assert _lineas_de(r.json()) == [(100, None, None, None)]
    assert [t for _, t, *_ in uow.eventos.tipos] == ["PARTIDA"]


def test_f050_r13_la_misma_partida_no_deja_evento(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "100", **P)]}, monkeypatch)
    assert _put(cliente).status_code == 200
    assert uow.eventos.tipos == [] and uow.reemplazados == []


def test_f050_r13_distingue_el_modo_de_la_linea(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "50"), _lp(100, "50", pv=True)]},
                            monkeypatch)
    r = _put(cliente, pv=True)
    assert r.status_code == 200, r.text
    assert [(ln.es_postventa, ln.partida_ide)
            for ln in uow.lineas[P_ACT][14]] == [(False, None), (True, 80003)]


def test_f050_r13_ctrl_z_devuelve_la_partida(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "100", **P)]}, monkeypatch)
    _put(cliente, partida={"ide": 80002, "cod": "CI.1.20", "res": "JEFE"})
    assert uow.lineas[P_ACT][14][0].partida_ide == 80002
    r = cliente.post(f"{BASE}/trabajadores/14/deshacer",
                     headers={"X-Usuario": "ana"})
    assert r.status_code == 200, r.text
    assert _lineas_de(r.json()) == [(100, 80003, "CI.1.9", "ADMINISTRATIVO")]


@pytest.mark.parametrize("ide, obra, pv, codigo", [
    (999, 100, False, 404),         # trabajador inexistente
    (14, 101, False, 404),          # línea inexistente
    (14, 100, True, 404),           # mismo obra, otro modo
])
def test_f050_r13_404_sin_tocar_nada(monkeypatch, ide, obra, pv, codigo):
    cliente, uow = _cliente({14: [_lp(100, "100")]}, monkeypatch)
    r = _put(cliente, ide, obra=obra, pv=pv)
    assert r.status_code == codigo, r.text
    assert "error" in r.json()
    assert uow.eventos.tipos == [] and uow.reemplazados == []


def test_f050_r13_periodo_inexistente_404_y_cerrado_409(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "100")]}, monkeypatch)
    r = cliente.put(f"/api/v1/periodos/{ANIO}/{MES + 1}/trabajadores/14/"
                    "partida", json={"obra_ide": 100, "partida": PARTIDA})
    assert r.status_code == 404
    uow.periodos = _PeriodoCerrado()
    assert _put(cliente).status_code == 409
    assert uow.eventos.tipos == [] and uow.reemplazados == []


def test_f050_r13_var_es_422(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "100", partida_fija=True)]},
                            monkeypatch)
    r = _put(cliente)
    assert r.status_code == 422
    assert r.json() == {"error": "La línea de la obra 100 es una entrada "
                                 "VAR: su partida es fija"}
    assert uow.eventos.tipos == [] and uow.reemplazados == []


@pytest.mark.parametrize("partida", [
    {"ide": 0, "cod": "X", "res": "X"}, {"ide": -5, "cod": "X", "res": "X"},
    {"cod": "X", "res": "X"}])
def test_f050_r13_ide_no_positivo_es_422(monkeypatch, partida):
    cliente, uow = _cliente({14: [_lp(100, "100")]}, monkeypatch)
    assert _put(cliente, partida=partida).status_code == 422
    assert uow.eventos.tipos == [] and uow.reemplazados == []


# ================================ R18 ==================================== #
def test_f050_r18_cada_linea_publica_su_partida(monkeypatch):
    cliente, _ = _cliente({14: [_lp(100, "60", **P),
                                _lp(101, "40", partida_fija=True)]},
                          monkeypatch)
    cuerpo = cliente.get(f"{BASE}/cuadrante").json()
    eva = next(t for t in cuerpo["trabajadores"] if t["ide"] == 14)
    assert [(ln["partida_ide"], ln["partida_cod"], ln["partida_res"],
             ln["partida_fija"]) for ln in eva["lineas"]] == [
        (80003, "CI.1.9", "ADMINISTRATIVO", False), (None, None, None, True)]


# ================================ R17 ==================================== #
CATALOGO = [
    {"ide": 80003, "cod": "CI.1.9", "res": "ADMINISTRATIVO",
     "categoria": "CI", "mayor": "CI"},
    {"ide": 1001, "cod": "01.19.03.20", "res": "PROPORCIONAL",
     "categoria": "CP", "mayor": "CD"}]
PV = [{"ide": 70001, "cod": "0678", "res": "15 VIVIENDAS",
       "categoria": "CD", "mayor": "CP"}]
PROPUESTA = {"paride": 80003, "cod": "CI.1.9", "res": "ADMINISTRATIVO",
             "metodo": "parte_anterior", "origen": "parte PT26/1"}


class _TransferFalso:
    def __init__(self, respuesta=None, fallo=None) -> None:
        self.respuesta = respuesta or {
            "ok": True, "partidas_obra": CATALOGO, "partidas_postventa": PV,
            "propuestas": {"linea": PROPUESTA},
            "mayor_inicial": {"linea": "CI"}}
        self.fallo = fallo
        self.payloads: list[dict] = []

    def propuesta_partidas(self, payload):
        self.payloads.append(payload)
        if self.fallo is not None:
            raise self.fallo
        return self.respuesta


def _cliente_r17(lineas, monkeypatch, transfer):
    from application.partidas_linea import PartidasDeLinea
    return _cliente(lineas, monkeypatch,
                    partidas_linea=PartidasDeLinea(transfer))


def _get(cliente, ide=14, obra=100, pv=False):
    return cliente.get(f"{BASE}/trabajadores/{ide}/partidas",
                       params={"obra_ide": obra,
                               "es_postventa": "true" if pv else "false"})


def test_f050_r17_catalogo_propuesta_y_payload(monkeypatch):
    transfer = _TransferFalso()
    cliente, _ = _cliente_r17({14: [_lp(100, "100")]}, monkeypatch, transfer)
    r = _get(cliente)
    assert r.status_code == 200, r.text
    assert r.json() == {"partidas": CATALOGO, "partidas_postventa": PV,
                        "ambito": "CI", "propuesta": PROPUESTA,
                        "elegida": None, "fija": None}
    assert transfer.payloads == [{
        "empresa": 1, "ano": ANIO, "mes": MES,
        "obra": {"ide": 100, "codigo": "0100", "nombre": "OBRA 100"},
        "lineas": [{"clave": "linea", "recurso_ide": 14, "nombre": "Eva",
                    "categoria": "Encargado", "es_postventa": False}]}]


def test_f050_r17_ambito_el_mayor_de_la_elegida(monkeypatch):
    elegida = {"partida_ide": 1001, "partida_cod": "01.19.03.20",
               "partida_res": "PROPORCIONAL"}
    cliente, _ = _cliente_r17({14: [_lp(100, "100", **elegida)]},
                              monkeypatch, _TransferFalso())
    cuerpo = _get(cliente).json()
    assert cuerpo["ambito"] == "CD"
    assert cuerpo["elegida"] == {"ide": 1001, "cod": "01.19.03.20",
                                 "res": "PROPORCIONAL"}


def test_f050_r17_elegida_fuera_del_catalogo_usa_mayor_inicial(monkeypatch):
    cliente, _ = _cliente_r17({14: [_lp(100, "100", partida_ide=5,
                                        partida_cod="X", partida_res="Y")]},
                              monkeypatch, _TransferFalso())
    assert _get(cliente).json()["ambito"] == "CI"
    sin = _TransferFalso()
    sin.respuesta = dict(sin.respuesta, mayor_inicial={"linea": None})
    cliente, _ = _cliente_r17({14: [_lp(100, "100")]}, monkeypatch, sin)
    assert _get(cliente).json()["ambito"] is None


def test_f050_r17_postventa_busca_en_su_catalogo(monkeypatch):
    transfer = _TransferFalso()
    cliente, _ = _cliente_r17(
        {14: [_lp(100, "100", pv=True, partida_ide=70001, partida_cod="0678",
                  partida_res="15 VIVIENDAS")]}, monkeypatch, transfer)
    assert _get(cliente, pv=True).json()["ambito"] == "CP"
    assert transfer.payloads[0]["lineas"][0]["es_postventa"] is True


def test_f050_r17_var_partida_fija_sin_transfer(monkeypatch):
    transfer = _TransferFalso()
    cliente, _ = _cliente_r17({14: [_lp(100, "100", partida_fija=True)]},
                              monkeypatch, transfer)
    assert _get(cliente).json() == {
        "partidas": [], "partidas_postventa": [], "ambito": None,
        "propuesta": None, "elegida": None,
        "fija": {"ide": -100, "cod": "0100", "res": "OBRA 100"}}
    assert transfer.payloads == []


def test_f050_r17_linea_inexistente_404(monkeypatch):
    transfer = _TransferFalso()
    cliente, _ = _cliente_r17({14: [_lp(100, "100")]}, monkeypatch, transfer)
    assert _get(cliente, obra=101).status_code == 404
    assert _get(cliente, ide=999).status_code == 404
    assert transfer.payloads == []


def test_f050_r17_transfer_caido_502_y_el_cuadrante_igual(monkeypatch):
    from domain.errors import PropuestaNoDisponible
    transfer = _TransferFalso(fallo=PropuestaNoDisponible(
        "propuesta de partidas no disponible: transfer inaccesible"))
    cliente, _ = _cliente_r17({14: [_lp(100, "100")]}, monkeypatch, transfer)
    r = _get(cliente)
    assert r.status_code == 502
    assert r.json() == {"error": "propuesta de partidas no disponible: "
                                 "transfer inaccesible"}
    assert cliente.get(f"{BASE}/cuadrante").status_code == 200


# ---------------------- TransferClient (R17) ---------------------------- #
class _Resp:
    def __init__(self, status, cuerpo):
        self.status_code = status
        self._cuerpo = cuerpo
        self.text = str(cuerpo)

    def json(self):
        return self._cuerpo


def _transfer_real(monkeypatch, respuesta):
    from infrastructure.transfer import transfer_client as mod
    llamadas = []

    def post(url, json, timeout):
        llamadas.append((url, json, timeout))
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    monkeypatch.setattr(mod.httpx, "post", post)
    ajustes = SimpleNamespace(transfer_base_url="http://transfer.invalid/",
                              transfer_timeout_s=7.0)
    return mod.TransferClient(ajustes), llamadas


def test_f050_r17_cliente_del_transfer_ok(monkeypatch):
    cuerpo = {"ok": True, "propuestas": {"linea": None}}
    cli, llamadas = _transfer_real(monkeypatch, _Resp(200, cuerpo))
    assert cli.propuesta_partidas({"x": 1}) == cuerpo
    assert llamadas == [("http://transfer.invalid/api/partidas/propuesta",
                         {"x": 1}, 7.0)]


@pytest.mark.parametrize("respuesta, motivo", [
    (_Resp(422, {"ok": False, "error": "empresa no válida: None"}),
     "empresa no válida: None"),
    (_Resp(200, {"ok": True}),
     "la respuesta del transfer no trae propuestas"),
    (_Resp(200, {"ok": "si", "propuestas": {}}),
     "la respuesta del transfer no trae propuestas"),
])
def test_f050_r17_cliente_del_transfer_sin_propuesta(monkeypatch, respuesta,
                                                     motivo):
    from domain.errors import PropuestaNoDisponible
    cli, _ = _transfer_real(monkeypatch, respuesta)
    with pytest.raises(PropuestaNoDisponible) as exc:
        cli.propuesta_partidas({})
    assert str(exc.value) == f"propuesta de partidas no disponible: {motivo}"


def test_f050_r17_cliente_del_transfer_caido(monkeypatch):
    import httpx
    from domain.errors import PropuestaNoDisponible
    cli, _ = _transfer_real(monkeypatch, httpx.ConnectError("sin red"))
    with pytest.raises(PropuestaNoDisponible, match="transfer inaccesible"):
        cli.propuesta_partidas({})


def test_f050_r17_elegida_de_mayor_otro_sale_en_todas(monkeypatch):
    transfer = _TransferFalso()
    transfer.respuesta = dict(transfer.respuesta, partidas_obra=[
        dict(CATALOGO[0], mayor="OTRO")])
    cliente, _ = _cliente_r17({14: [_lp(100, "100", **P)]}, monkeypatch,
                              transfer)
    assert _get(cliente).json()["ambito"] is None


# ============ T15 · casos que la campaña de mutación dejó vivos ============ #
def test_f050_r17_sin_modo_en_la_consulta_es_la_linea_normal(monkeypatch):
    transfer = _TransferFalso()
    cliente, _ = _cliente_r17({14: [_lp(100, "100"), _lp(100, "50", pv=True)]},
                              monkeypatch, transfer)
    r = cliente.get(f"{BASE}/trabajadores/14/partidas",
                    params={"obra_ide": 100})
    assert r.status_code == 200, r.text
    assert transfer.payloads[0]["lineas"][0]["es_postventa"] is False


def test_f050_r13_sin_modo_en_el_cuerpo_es_la_linea_normal(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "50"), _lp(100, "50", pv=True)]},
                            monkeypatch)
    r = cliente.put(f"{BASE}/trabajadores/14/partida",
                    json={"obra_ide": 100, "partida": PARTIDA})
    assert r.status_code == 200, r.text
    assert [(ln.es_postventa, ln.partida_ide)
            for ln in uow.lineas[P_ACT][14]] == [(False, 80003), (True, None)]


def test_f050_r13_la_partida_1_es_valida(monkeypatch):
    cliente, uow = _cliente({14: [_lp(100, "100")]}, monkeypatch)
    r = _put(cliente, partida={"ide": 1, "cod": "1", "res": "UNO"})
    assert r.status_code == 200, r.text
    assert uow.lineas[P_ACT][14][0].partida_ide == 1
