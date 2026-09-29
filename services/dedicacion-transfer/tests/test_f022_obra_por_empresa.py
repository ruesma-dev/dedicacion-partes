# tests/test_f022_obra_por_empresa.py
"""F-022 · El transfer busca cada obra por código y empresa (R1-R19).

El código de obra solo es único DENTRO de su empresa (`con.emp`): `POSTV2`
tiene ficha en la empresa 1 y en la 28. La regla vive en
`docs/ARCHITECTURE.md#regla-empresa`; aquí se prueba, no se reenuncia.

Todo offline: el cliente de Sigrid se prueba con `_read` sustituido por un
doble que guarda la consulta y devuelve filas fijas, y el pipeline con un
doble de cliente indexado por `(código, empresa)` que anota cada llamada.
Ni red, ni BBDD, ni `.env`. Los `ide` son inventados.
"""
from __future__ import annotations

import dataclasses

import pytest

from domain.models.registro_models import LineaEntrada, ObraEntrada


# ============================ dominio (T1) ============================ #

def test_f022_r1_dominio_la_linea_lleva_empresa():
    """R1 · La línea de entrada lleva `empresa`, opcional a propósito: su
    ausencia tiene que llegar al pipeline para omitirse con motivo."""
    campos = {f.name: f for f in dataclasses.fields(LineaEntrada)}
    assert "empresa" in campos
    assert campos["empresa"].default is None
    assert LineaEntrada(registro_id=1, ano=2026, mes=7, porcentaje=0.4,
                        empresa=28).empresa == 28


def test_f022_r9_dominio_la_obra_lleva_empresa():
    """R9 · La obra resuelta publica su `con.emp`."""
    campos = {f.name: f for f in dataclasses.fields(ObraEntrada)}
    assert "empresa" in campos
    assert campos["empresa"].default is None
    assert ObraEntrada(ide=1, codigo="X", empresa=1).empresa == 1


def test_f022_r4_r8_dominio_errores_propios():
    """R4 y R8 · Los dos errores de la regla son del dominio y heredan de
    lo que la app ya sabe tratar."""
    from domain.errores import EmpresasMezcladas, ObraAmbigua

    assert issubclass(EmpresasMezcladas, ValueError)
    assert issubclass(ObraAmbigua, RuntimeError)
