# tests/test_f024_obra_destino_otra_empresa.py
"""F-024 · En el corte por obra de otra empresa, `obra_destino` y
`obra_origen` son la obra de origen RESUELTA en Sigrid, con su empresa
(R20); el contrato API ↔ transfer no cambia (R21).

Recogido de la review 1 de F-022: antes se publicaba la obra de ENTRADA con
`empresa: null`. La regla está en `docs/ARCHITECTURE.md#regla-empresa`.
Offline: los dobles de `test_f022_obra_por_empresa.py`, sin red ni `.env`.
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import ObraEntrada

from tests.conftest import linea
from tests.test_f022_obra_por_empresa import ClienteEmpresas, _pl

#: Obra que llega por `ide` y en Sigrid es de la 28; sus líneas, de la 1.
OBRA_28 = ObraEntrada(ide=555028, codigo="0678")
LINEAS = [linea(registro_id=1), linea(registro_id=2, es_postventa=True)]


# --------------------------------- R20 -------------------------------- #
@pytest.mark.parametrize("forzar", [True, False], ids=["pruebas", "normal"])
def test_f024_r20_preflight_publica_la_obra_de_origen_resuelta(forzar):
    cli = ClienteEmpresas()
    pf = _pl(cli, forzar).preflight(obra=OBRA_28, lineas=LINEAS)
    assert [a.accion for a in pf.acciones] == ["omitir", "omitir"]
    for publicada in (pf.obra_destino, pf.obra_origen):
        assert (publicada.ide, publicada.codigo, publicada.empresa) == (
            555028, "0678", 28)
    assert pf.forzada_pruebas is forzar
    assert pf.partes == [] and cli.escritos == []


@pytest.mark.parametrize("forzar", [True, False], ids=["pruebas", "normal"])
def test_f024_r20_ejecutar_publica_la_obra_de_origen_resuelta(forzar):
    cli = ClienteEmpresas()
    res = _pl(cli, forzar).ejecutar(obra=OBRA_28, lineas=LINEAS)
    assert (res.obra_destino.ide, res.obra_destino.empresa) == (555028, 28)
    assert res.escritas == [] and cli.escritos == []
    assert [o["registro_id"] for o in res.omitidas] == [1, 2]


@pytest.mark.parametrize("forzar", [True, False], ids=["pruebas", "normal"])
def test_f024_r20_corte_sin_empresa_sigue_con_la_obra_de_entrada(forzar):
    """Sin empresa no se resuelve ninguna obra: se publica la de entrada."""
    cli = ClienteEmpresas()
    sin = [linea(registro_id=1, empresa=None)]
    pf = _pl(cli, forzar).preflight(obra=OBRA_28, lineas=sin)
    assert pf.obra_destino is OBRA_28 and pf.obra_origen is OBRA_28
    assert cli.llamadas == []
    res = _pl(cli, forzar).ejecutar(obra=OBRA_28, lineas=sin)
    assert res.obra_destino is OBRA_28


# --------------------------------- R21 -------------------------------- #
#: Claves de la respuesta ANTES de F-024 (`interface_adapters/api/app.py`).
CLAVES_PREFLIGHT = {"ok", "obra_destino", "obra_postventa",
                    "capitulo_postventa", "partidas_obra",
                    "partidas_postventa", "forzada_pruebas", "partes",
                    "acciones", "conflictos", "resumen"}
CLAVES_EJECUTAR = {"ok", "obra_destino", "forzada_pruebas", "partes",
                   "escritas", "omitidas", "ya_registradas", "pisadas",
                   "borradas", "pendientes_confirmacion", "error"}
CLAVES_OBRA = {"ide", "codigo", "nombre", "empresa"}


@pytest.fixture
def cliente_app(monkeypatch):
    """`build_app` con ajustes falsos y la lectura de Sigrid sustituida por
    la de `test_f022_obra_por_empresa.py`; escribir está prohibido."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
    from interface_adapters.api.app import build_app

    from tests.test_f022_obra_por_empresa import (
        SigridFalsaApp,
        _escribir_prohibido,
    )

    ajustes = SimpleNamespace(
        sigrid_api_base_url="http://sigrid.invalid",
        sigrid_api_function_key="sin-clave", sigrid_api_database="ruesma",
        sigrid_api_timeout_s=1.0, sigrid_max_statements=15,
        sigrid_max_rows=200_000,
        tip_parte_trabajo=35, est_parte_activo=1, obra_pruebas_forzar=True,
        obra_pruebas_cod="0404", marca_pruebas="PRUEBA-PORC",
        postventa_registrar=True, postventa_obra_cod="POSTV2", paso_pos=64)
    lectura = SigridFalsaApp()
    monkeypatch.setattr(SigridWriteClient, "_read",
                        lambda self, sql, params: lectura(self, sql, params))
    monkeypatch.setattr(SigridWriteClient, "escribir", _escribir_prohibido)
    return TestClient(build_app(ajustes))


#: La obra `999028` es de la 28 en la lectura falsa; la línea, de la 1.
PETICION = {"obra": {"ide": 999028, "codigo": "POSTV2"},
            "lineas": [{"registro_id": 1, "ano": 2026, "mes": 7,
                        "porcentaje": 0.4, "empresa": 1}]}


@pytest.mark.parametrize("ruta, claves", [
    ("/api/registro/preflight", CLAVES_PREFLIGHT),
    ("/api/registro/ejecutar", CLAVES_EJECUTAR),
], ids=["preflight", "ejecutar"])
def test_f024_r21_contrato_igual_en_el_corte_por_otra_empresa(
        cliente_app, ruta, claves):
    r = cliente_app.post(ruta, json=PETICION)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert set(cuerpo) == claves
    assert set(cuerpo["obra_destino"]) == CLAVES_OBRA
    # R20 a través de la app: la obra resuelta, con su empresa.
    assert (cuerpo["obra_destino"]["ide"],
            cuerpo["obra_destino"]["empresa"]) == (999028, 28)
