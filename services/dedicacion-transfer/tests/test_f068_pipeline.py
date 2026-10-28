# tests/test_f068_pipeline.py
"""F-068 · el pipeline con la partida del vinculado como la del trabajador
(design §2, §6.2; requirements R11-R18).

- R18 (T1): el contrato de entrada gana `descripcion` (registro y
  propuesta) y `tipo_res` (propuesta), opcionales; sin ellos, la entrada de
  hoy.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import VinculadoEntrada
from interface_adapters.api.app import (
    LineaPropuestaIn,
    VinculadoIn,
    VinculadoPropuestaIn,
)

from tests.test_f044_pipeline_vinculados import api  # noqa: F401
from tests.test_f044_pipeline_vinculados import ClienteVin, _cuerpo, _linea
from tests.test_f044_sql_vinculados import (  # noqa: F401
    _cuerpo_registro,
    ruta_espiada,
)


# ================================ R18 ==================================== #
def test_f068_r18_vinculado_de_registro_con_descripcion():
    v = VinculadoIn(recurso_ide=10, tipo="TF", tipo_res="TELEFONO",
                    descripcion="MOVIL 600")
    assert v.descripcion == "MOVIL 600"
    assert VinculadoEntrada(**v.model_dump()).descripcion == "MOVIL 600"


def test_f068_r18_sin_descripcion_la_entrada_de_hoy():
    assert VinculadoIn(recurso_ide=10).descripcion is None
    assert VinculadoEntrada(recurso_ide=10).descripcion is None


def test_f068_r18_la_ruta_de_registro_pasa_la_descripcion(ruta_espiada):
    cliente, recibidas = ruta_espiada
    r = cliente.post("/api/registro/preflight", json=_cuerpo_registro(
        vinculados=[{"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
                     "cod": "TF-10", "descripcion": "MOVIL 600"}]))
    assert r.status_code == 200
    [[l]] = recibidas
    assert l.vinculados == [VinculadoEntrada(
        recurso_ide=10, tipo="TF", tipo_res="TELEFONO", cod="TF-10",
        descripcion="MOVIL 600")]


def test_f068_r18_vinculado_de_propuesta_con_tipo_res_y_descripcion():
    l = LineaPropuestaIn(clave="a", recurso_ide=200, vinculados=[
        VinculadoPropuestaIn(recurso_ide=10, tipo="TF", cod="TF-10",
                             tipo_res="TELEFONO", descripcion="MOVIL 600")])
    assert l.para_pipeline()["vinculados"] == [{
        "recurso_ide": 10, "tipo": "TF", "categoria": None, "cod": "TF-10",
        "tipo_res": "TELEFONO", "descripcion": "MOVIL 600"}]


@pytest.mark.parametrize("extra, esperado", [
    ({}, {}),
    ({"tipo_res": "TELEFONO"}, {"tipo_res": "TELEFONO"}),
    ({"descripcion": "MOVIL"}, {"descripcion": "MOVIL"}),
])
def test_f068_r18_sin_ellos_la_entrada_de_propuesta_de_hoy(extra, esperado):
    """Lo que no llega no viaja: el dict del pipeline es el de F-044 más
    solo lo que la api mandó."""
    l = LineaPropuestaIn(clave="a", recurso_ide=200, vinculados=[
        VinculadoPropuestaIn(recurso_ide=10, tipo="TF", cod="TF-10",
                             **extra)])
    assert l.para_pipeline()["vinculados"] == [{
        "recurso_ide": 10, "tipo": "TF", "categoria": None, "cod": "TF-10",
        **esperado}]


def test_f068_r18_la_ruta_de_propuesta_pasa_tipo_res_y_descripcion(
        api, monkeypatch):  # noqa: F811
    recibidas: list[list[dict]] = []
    original = RegistroPipeline.proponer

    def espia(self, **kw):
        recibidas.append(kw["lineas"])
        return original(self, **kw)

    monkeypatch.setattr(RegistroPipeline, "proponer", espia)
    vin = [{"recurso_ide": 10, "tipo": "TF", "categoria": None,
            "cod": "TF-10", "tipo_res": "TELEFONO",
            "descripcion": "MOVIL 600"}]
    r = api(ClienteVin()).post("/api/partidas/propuesta", json=_cuerpo(
        _linea(vinculados=vin)))
    assert r.status_code == 200
    assert recibidas == [[{**_linea(), "vinculados": vin}]]
