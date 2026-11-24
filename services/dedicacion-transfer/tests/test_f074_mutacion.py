# tests/test_f074_mutacion.py
"""F-074 · Tests que matan supervivientes de la campaña de mutación
`critico` (`progress/mutacion_F-074.md`), reproducidos en serie antes de
escribirlos (C4 bis).

- `partida_definida.py:81`: `DefinidaVinculado` es inmutable (la decisión de
  una subfila no se retoca después de tomarla).
- `registro_pipeline.py:220`: la línea de postventa con `var_paride` se
  omite sin partida (`paride` 0), no con una partida inventada.
"""
from __future__ import annotations

import dataclasses

import pytest

from application.services.partida_definida import DefinidaVinculado
from application.services.reglas_vinculados import PartidaVinculado
from application.services.universo_var import MOTIVO_VAR_POSTVENTA
from domain.models.registro_models import ObraEntrada
from tests.conftest import OBRA_ORIGEN, linea
from tests.test_f039_preflight_var import P29, _pf
from tests.test_f039_universo_var import ClienteVar


def test_f074_mut_definida_del_vinculado_es_inmutable():
    d = DefinidaVinculado(PartidaVinculado(paride=81001, cod="CICO13"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.no_valida = "CICO13"  # type: ignore[misc]


def test_f074_mut_postventa_con_var_se_omite_sin_partida():
    """F-039 R6 con F-074 (R1): la VAR no va a postventa; la acción omitida
    no lleva partida (0), ni la VAR ni otra."""
    pf = _pf(ClienteVar(), obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=[
        linea(es_postventa=True, var_paride=P29)])
    a = pf.acciones[0]
    assert a.motivo == MOTIVO_VAR_POSTVENTA.format(paride=P29)
    assert (a.accion, a.paride, a.partida_cod) == ("omitir", 0, None)
