# tests/test_f054_mutacion.py
"""F-054 · T17: lo que la campaña de mutación del transfer dejó vivo
(`progress/mutacion_F-054.md`). Cada test nombra el mutante que mata.

- Guarda de `PonerACero`: los bordes de `can` (también el `_EPS` exacto), la
  obra de pruebas que no aparece, todo omitido sigue siendo `ok` y el fallo
  de la ruta (502, `ok: false`).
- Coberturas y sobrantes: acción sin línea, partida del vinculado, partida
  0, y el `cod_var` limpio que llega desde los ajustes.
- Traducción: la partida 0 no casa con la 1 (postventa y VAR) y `desde`
  sale 0 si no hay ajuste.
- Los modelos nuevos son inmutables y sin partida es 0.

`ClienteFalso` y dobles de los tests de F-054. Sin red ni BBDD.
"""
from __future__ import annotations

import dataclasses
import logging
from types import SimpleNamespace

import pytest
from application.pipelines import registro_lote as modulo_lote
from application.pipelines.poner_a_cero import (
    _EPS,
    MOTIVO_CAMBIADA,
    MOTIVO_FUERA_PRUEBAS,
    MOTIVO_NO_ESTA,
    MOTIVO_NO_QUEDO,
    PonerACero,
)
from application.services import porcentajes_existentes as modulo_pe
from application.services.porcentajes_existentes import (
    MOTIVO_PV_NINGUNA,
    traducir,
)
from application.services.reglas_obra_cero import Cobertura, coberturas_de
from domain.models.registro_models import LineaMensualSigrid, Sobrante
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app

from tests.test_f050_endpoint_propuesta import AJUSTES
from tests.test_f054_obra_cero import (
    ClienteMensual,
    _a,
    _ajustes,
    _con_partida,
    _cub,
    _m,
    _obra,
    _pf,
    _sob,
)
from tests.test_f054_poner_a_cero import _cli, _pedida, _poner
from tests.test_f054_traduccion import _l


# -------------------------------- la guarda ------------------------------- #
@pytest.mark.parametrize("leido, pedido", [
    (0.0, _EPS),    # mata `>= _EPS` -> `> _EPS`: el borde exacto cambia
    (1.0, 0),       # mata `p["can"] or 1`
    (0.0, 1.0),     # mata `ls.can or 1`
])
def test_f054_r35_can_distinto_es_cambiada(leido, pedido):
    cli = _cli((7001, 200, leido, "MENC", None))
    r = _poner(cli, [_pedida(7001, can=pedido)])
    assert r == {"ok": True, "puestas": [],
                 "omitidas": [{"hmores_ide": 7001,
                               "motivo": MOTIVO_CAMBIADA}]}
    assert cli.escritos == []


def test_f054_r35_todas_omitidas_sigue_siendo_ok():
    """Mata `"ok": False` cuando no queda nada que escribir: la api
    trataría una omisión como un fallo y no registraría nada."""
    assert _poner(_cli(), [_pedida(9999)]) == {
        "ok": True, "puestas": [],
        "omitidas": [{"hmores_ide": 9999, "motivo": MOTIVO_NO_ESTA}]}


def test_f054_r35_en_pruebas_sin_la_0404_todas_fuera():
    """Mata `obra is None and not obra.ide` (reventaría con None)."""
    cli = _cli((7001, 200, 0.3, "MENC", None))
    cli.obra_por_codigo = lambda cod, empresa: None
    r = _poner(cli, [_pedida(7001)])
    assert r["omitidas"] == [{"hmores_ide": 7001,
                              "motivo": MOTIVO_FUERA_PRUEBAS}]
    assert cli.escritos == []


def test_f054_r35_relectura_con_el_eps_exacto_no_quedo():
    """Mata `>= _EPS` -> `> _EPS` al comprobar que quedó a 0."""
    cli = _cli((7001, 200, 0.3, "MENC", None))
    cli.lineas_registradas = lambda _a, ides: (
        {}, {i: SimpleNamespace(can=_EPS) for i in ides})
    r = _poner(cli, [_pedida(7001)])
    assert r["puestas"] == []
    assert r["omitidas"] == [{"hmores_ide": 7001,
                              "motivo": MOTIVO_NO_QUEDO}]


def test_f054_r35_el_log_de_la_puesta_a_cero_va_sin_registro(caplog):
    """Mata `_traza("pone a 0", 1, …)`: la sobrante no viene de ninguna
    línea del cuadrante."""
    caplog.set_level(logging.INFO)
    _poner(_cli((7001, 200, 0.3, "MENC", None)), [_pedida(7001)])
    assert "registro=0 " in next(m for m in caplog.messages
                                 if m.startswith("[registro] pone a 0"))


def test_f054_r35_ruta_si_falla_502_con_ok_false(monkeypatch):
    class _Roto:
        def __init__(self, **kw) -> None:
            pass

        def ejecutar(self, *a):
            raise RuntimeError("sigrid caido")

    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: _cli())
    monkeypatch.setattr(modulo_app, "PonerACero", _Roto)
    st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4})
    r = TestClient(modulo_app.build_app(st)).post(
        "/api/registro/poner-a-cero", json={
            "empresa": 1, "ano": 2026, "mes": 7, "lineas": [_pedida(1)]})
    assert r.status_code == 502
    assert r.json() == {"ok": False, "error": "sigrid caido"}


# -------------------------- coberturas y sobrantes ------------------------ #
def test_f054_r31_accion_sin_su_linea_cubre_por_su_recurso():
    """Mata `a.recurso_ide and (…)`."""
    cob = coberturas_de(_pf([_a(1, 10)]), [])
    assert list(cob) == [10]


def test_f054_r38_el_vinculado_cubre_con_su_partida():
    """Mata `int(v.paride and 0)`."""
    cob = coberturas_de(_pf(vinculados=[_a(1, 5000, paride=81)]), [])
    assert [c.paride for c in cob[5000]] == [81]


def test_f054_r32_en_pruebas_la_partida_0_no_es_la_1():
    """Mata `int(linea.paride or 1)` en `cubierta`."""
    assert not _cub(_m(1, paride=0), [Cobertura(694, "obra", 1, None)],
                    pruebas=True)


def test_f054_r33_la_sobrante_sin_partida_lleva_paride_0():
    """Mata `paride=int(l.paride or 1)`."""
    [s] = _sob([_m(1, obra=713, paride=0)],
               {10: [Cobertura(694, "obra", 0, None)]})
    assert s.paride == 0


def test_f054_r31_cod_var_limpio_desde_los_ajustes(monkeypatch):
    """Mata `(… and "").strip()`: sin código VAR, una sobrante de la obra
    VAR se trataría como de una obra normal."""
    vistos = []

    def espia(mensuales, coberturas, **kw):
        vistos.append(kw["cod_var"])
        return []

    monkeypatch.setattr(modulo_lote, "sobrantes", espia)
    st = _ajustes()
    st.var_obra_cod = " 0999 "
    modulo_lote.RegistroLote(cliente=ClienteMensual(), settings=st)         .preflight_completo([(_obra(1), [_con_partida(1)])])
    assert vistos == ["0999"]


# ------------------------------- traducción ------------------------------- #
def test_f054_r9_postventa_sin_partida_no_casa_con_la_1():
    """Mata `linea.paride or 1` en el casado inverso."""
    t = traducir(_l(1, 7, "PV", paride=0), cod_pruebas="P", cod_postventa="PV",
                 cod_var="V", inverso={1: [SimpleNamespace(ide=55)]},
                 catalogo_var=None, desde=0, motivo_postventa=None)
    assert t["obra_origen_ide"] is None
    assert t["motivo"] == MOTIVO_PV_NINGUNA.format(partida=0, pv="PV")


def test_f054_r10_var_sin_partida_se_pregunta_con_la_0(monkeypatch):
    """Mata `linea.paride or 1` en la VAR."""
    vistas = []

    def espia(catalogo, obra, paride, desde):
        vistas.append((paride, desde))
        return None, "fuera"

    monkeypatch.setattr(modulo_pe, "partida_var_de", espia)
    t = traducir(_l(1, 7, "V", paride=0), cod_pruebas="P", cod_postventa="PV",
                 cod_var="V", inverso={}, catalogo_var=object(), desde=3,
                 motivo_postventa=None)
    assert vistas == [(0, 3)]
    assert t["motivo"] == "fuera"


def test_f054_r10_sin_ajuste_de_desde_es_0(monkeypatch):
    """Mata los dos `1` de `var_partida_desde` (el `getattr` y el `or`)."""
    vistos = []

    def espia(linea, **kw):
        vistos.append(kw["desde"])

    monkeypatch.setattr(modulo_pe, "traducir", espia)
    cli = SimpleNamespace(lineas_mensuales_del_periodo=lambda *a: [
        _l(1, 7, "0007")])
    modulo_pe.PorcentajesExistentes(cliente=cli, settings=SimpleNamespace(
        postventa_obra_cod="PV", obra_pruebas_cod="P")).calcular(1, 2026, 9, [])
    assert vistos == [0]


# --------------------------------- modelos -------------------------------- #
@pytest.mark.parametrize("clase", [LineaMensualSigrid, Sobrante, Cobertura])
def test_f054_t17_los_modelos_son_inmutables(clase):
    assert clase.__dataclass_params__.frozen is True


def test_f054_t17_sin_partida_es_0():
    campos = {f.name: f for f in dataclasses.fields(LineaMensualSigrid)}
    assert campos["paride"].default == 0
