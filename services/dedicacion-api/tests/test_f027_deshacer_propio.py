# tests/test_f027_deshacer_propio.py
"""F-027 · Deshacer solo lo propio (decisión A del 2026-10-04).

Solo se deshace si el ÚLTIMO evento pendiente del trabajador en el periodo es
del usuario que lo pide; si es de otro, se rechaza con un motivo que lo
nombra y el mismo 409 que «nada que deshacer». `puede_deshacer` (cuadrante y
fila) sigue la misma regla. Los usuarios se comparan sin mayúsculas ni
espacios en los extremos (`domain/deshacer.py`).

Offline: el repositorio con una sesión falsa que captura la sentencia, los
casos de uso con la UnitOfWork en memoria de `test_f024_cuadrante_empresa`
(con dos usuarios) y la API con `TestClient`. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

import pytest
from domain.deshacer import clave_usuario, deshacer_permitido
from domain.errors import DeshacerAjeno, ErrorDominio, NadaQueDeshacer


# =========================== dominio (T1) ============================== #
@pytest.mark.parametrize("autor, usuario", [
    ("pablo@ruesma.es", "pablo@ruesma.es"),
    ("Pablo@Ruesma.ES", "pablo@ruesma.es"),
    ("  pablo@ruesma.es\t", "PABLO@ruesma.es "),
])
def test_f027_r4_mismo_usuario_sin_mayusculas_ni_espacios(autor, usuario):
    assert deshacer_permitido(autor, usuario) is True


@pytest.mark.parametrize("autor, usuario", [
    ("ana@ruesma.es", "pablo@ruesma.es"),
    ("pablo@ruesma.es", "pablo@ruesma.es.otro"),   # prefijo no es el mismo
    ("pa blo@ruesma.es", "pablo@ruesma.es"),       # el interior no se toca
    (None, "pablo@ruesma.es"),                     # nada pendiente
])
def test_f027_r4_otro_usuario_o_nada_pendiente(autor, usuario):
    assert deshacer_permitido(autor, usuario) is False


def test_f027_r4_clave_usuario_es_la_unica_normalizacion():
    assert clave_usuario("  Ana.López@Ruesma.ES  ") == "ana.lópez@ruesma.es"


def test_f027_r1_el_error_es_de_dominio_y_distinto_de_nada_que_deshacer():
    assert issubclass(DeshacerAjeno, ErrorDominio)
    assert not issubclass(DeshacerAjeno, NadaQueDeshacer)
