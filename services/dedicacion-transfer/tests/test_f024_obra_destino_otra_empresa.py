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
