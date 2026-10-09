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
    uow.asignaciones = _AsignacionesConPartida(uow)
    uow.eventos = _EventosConTipo()
    contenedor = SimpleNamespace(settings=settings, uow=lambda: uow, **extra)
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
