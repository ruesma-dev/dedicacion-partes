# tests/test_f026_recurso_dado.py
"""F-026 · El transfer usa el recurso que manda la API y no lo elige.

Trazabilidad con `specs/F-026-recursos-sin-ficha-empleado/requirements.md`:
R19 (el `recurso_ide` de la línea se usa tal cual, sin consultar
`res.conide`), R20 (sin `recurso_ide` la línea se omite «sin recurso»,
traiga o no `empleado_ide`), R21 (no se exige que la empresa del recurso sea
la de la línea) y R22 (P1 sigue omitiendo el recurso sin `M*`). Regla en
`docs/ARCHITECTURE.md#regla-recurso`.

Sin red ni BBDD: el pipeline habla con el `ClienteFalso` de `conftest.py`
(que acumula sentencias sin escribir) y la app con la lectura falsa de
`test_f022_obra_por_empresa.py`, que anota cada consulta y prohíbe escribir.
"""
from __future__ import annotations

import dataclasses

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services import reglas_porcentajes as reglas
from domain.models.registro_models import (
    AccionLinea, HoraRecurso, LineaEntrada, ObraEntrada,
)
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

from tests.conftest import OBRA_ORIGEN, ClienteFalso, SettingsFalso, linea
from tests.test_f022_obra_por_empresa import app_falsa  # noqa: F401 (fixture)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)

#: Recurso M* de una persona de la UTE 18 (F-034: imputa a obras de la 1).
RECURSO_18 = 1800


class ClienteSinElegir(ClienteFalso):
    """Doble que revienta si el pipeline intenta elegir el recurso."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.horas[RECURSO_18] = [HoraRecurso(5, "MENC", None, 8000.0)]
        self.horas_pedidas: list[list[int]] = []

    def recursos_de_empleados(self, emp_ides):
        raise AssertionError("el transfer no debe resolver el recurso")

    def horas_de_recursos(self, resides):
        self.horas_pedidas.append(sorted(resides))
        return super().horas_de_recursos(resides)


def _preflight(cli: ClienteFalso, lineas: list[LineaEntrada]):
    pipeline = RegistroPipeline(cliente=cli, settings=SettingsFalso())
    return pipeline.preflight(obra=OBRA, lineas=lineas)


# ------------------------------- R19 ------------------------------- #

def test_f026_r19_usa_el_recurso_de_la_linea_tal_cual():
    cli = ClienteSinElegir()
    pf = _preflight(cli, [linea(registro_id=1, recurso_ide=200),
                          linea(registro_id=2, recurso_ide=400)])
    assert [(a.registro_id, a.accion, a.recurso_ide) for a in pf.acciones] \
        == [(1, "escribir", 200), (2, "escribir", 400)]
    assert cli.horas_pedidas == [[200, 400]]


def test_f026_r19_el_recurso_sin_mensual_no_se_cambia_por_otro():
    """Antes, con `empleado_ide=10`, el transfer elegía el 200 (MENC) entre
    sus recursos. Ahora el 100 que manda la API se respeta y P1 lo omite."""
    pf = _preflight(ClienteSinElegir(), [linea(recurso_ide=100)])
    (a,) = pf.acciones
    assert (a.accion, a.recurso_ide, a.motivo) == (
        "omitir", 100, reglas.MOTIVO_SIN_MENSUAL)


def test_f026_r19_el_cliente_ya_no_resuelve_por_conide():
    assert not hasattr(SigridWriteClient, "recursos_de_empleados")


# ------------------------------- R20 ------------------------------- #

def test_f026_r20_motivo_sin_recurso():
    assert reglas.MOTIVO_SIN_RECURSO == "la línea no trae el recurso del trabajador"


def test_f026_r20_sin_recurso_se_omite_en_el_pipeline():
    pf = _preflight(ClienteSinElegir(), [linea(recurso_ide=None)])
    (a,) = pf.acciones
    assert (a.accion, a.motivo, a.recurso_ide) == (
        "omitir", reglas.MOTIVO_SIN_RECURSO, None)


@pytest.mark.parametrize("extra", [{}, {"empleado_ide": 10}])
def test_f026_r20_app_sin_recurso_se_omite_traiga_o_no_empleado_ide(
        app_falsa, extra):  # noqa: F811
    cliente, lectura = app_falsa()
    lin = {"registro_id": 1, "ano": 2026, "mes": 7, "porcentaje": 0.4,
           "empresa": 1, **extra}
    r = cliente.post("/api/registro/preflight",
                     json={"obra": {"codigo": "0678"}, "lineas": [lin]})
    assert r.status_code == 200, r.text
    (accion,) = r.json()["acciones"]
    assert (accion["accion"], accion["motivo"]) == (
        "omitir", reglas.MOTIVO_SIN_RECURSO)
    assert "empleado_ide" not in accion
    assert not any("conide" in sql for sql, _ in lectura.consultas)


def test_f026_r20_el_contrato_ya_no_tiene_empleado_ide():
    from interface_adapters.api.app import LineaIn

    assert "empleado_ide" not in LineaIn.model_fields
    assert "recurso_ide" in LineaIn.model_fields
    for modelo in (LineaEntrada, AccionLinea):
        assert "empleado_ide" not in {f.name for f in dataclasses.fields(modelo)}
    viejo = LineaIn(registro_id=1, ano=2026, mes=7, porcentaje=0.4,
                    empleado_ide=10)  # cliente viejo: se ignora
    assert "empleado_ide" not in viejo.model_dump()


# ------------------------------- R21 ------------------------------- #

def test_f026_r21_recurso_de_otra_empresa_en_linea_de_la_1_se_escribe():
    pf = _preflight(ClienteSinElegir(), [linea(recurso_ide=RECURSO_18,
                                                empresa=1)])
    (a,) = pf.acciones
    assert (a.accion, a.recurso_ide) == ("escribir", RECURSO_18), a.motivo


# ------------------------------- R22 ------------------------------- #

def test_f026_r22_recurso_sin_mensual_sigue_omitido_por_p1():
    pf = _preflight(ClienteSinElegir(), [linea(recurso_ide=300)])
    (a,) = pf.acciones
    assert (a.accion, a.motivo) == ("omitir", reglas.MOTIVO_SIN_MENSUAL)
