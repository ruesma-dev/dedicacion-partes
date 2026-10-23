# tests/test_f061_palabras.py
"""F-061 · Palabras extra de las incidencias (criterio 1).

Las palabras extra viven en `config/config.yaml`, junto a
`sync.incidencias.sql`, como una lista ordenada de entradas `codigo` +
`palabras`. `GET /api/v1/incidencias` publica en cada incidencia `palabras`
(lista, vacía si no tiene) y `orden_busqueda` (posición de su entrada en la
config, `null` sin entrada); la lista sigue por letra (F-030 R6).

Offline: la ruta se monta con el contenedor doble de
`test_f024_rutas_empresa.py` y la config real o una de prueba. Ni red, ni
BBDD, ni `.env`.
"""
from __future__ import annotations

from typing import Any

import pytest

#: Lo aprobado por el humano el 2026-10-22, en el orden decidido (B, AT, M,
#: FJ, F, V, H).
APROBADAS = [
    ("CIE", ["baja", "IT", "enfermedad común"]),
    ("CIA", ["baja", "accidente de trabajo"]),
    ("CIM", ["baja", "nacimiento", "permiso"]),
    ("CIP", ["permiso", "ausencia"]),
    ("CIF", ["ausencia"]),
    ("CIV", []),
    ("CIH", []),
]


# ------------------------------ config ----------------------------------- #
def test_f061_r1_config_trae_las_palabras_aprobadas_en_su_orden():
    from config.settings import cargar_config

    entradas = cargar_config()["sync"]["incidencias"]["palabras_extra"]
    assert [(e["codigo"], e["palabras"]) for e in entradas] == APROBADAS


def test_f061_r1_leer_la_config_da_posicion_y_palabras_por_codigo():
    from application.palabras_incidencia import palabras_por_codigo

    leidas = palabras_por_codigo([
        {"codigo": "CIE", "palabras": ["baja", "IT"]},
        {"codigo": " CIV ", "palabras": []},
        {"codigo": "CIH"},
    ])
    assert leidas == {"CIE": (0, ["baja", "IT"]), "CIV": (1, []),
                      "CIH": (2, [])}


def test_f061_r1_sin_palabras_extra_en_la_config_nadie_tiene():
    from application.palabras_incidencia import palabras_por_codigo

    assert palabras_por_codigo(None) == {}
    assert palabras_por_codigo([]) == {}


@pytest.mark.parametrize("entradas, motivo", [
    ({"CIE": ["baja"]}, "lista"),
    (["CIE"], "codigo"),
    ([{"palabras": ["baja"]}], "codigo"),
    ([{"codigo": "  ", "palabras": []}], "codigo"),
    ([{"codigo": 7, "palabras": []}], "codigo"),
    ([{"codigo": "CIE", "palabras": "baja"}], "palabras"),
    ([{"codigo": "CIE", "palabras": ["baja", 3]}], "palabras"),
    ([{"codigo": "CIE", "palabras": ["baja", "  "]}], "palabras"),
    ([{"codigo": "CIE", "palabras": []}, {"codigo": "CIE", "palabras": []}],
     "repetido"),
    # Review 1 (O1): un valor presente que no es lista no vale por vacía;
    # solo la clave que falta.
    ([{"codigo": "CIE", "palabras": ""}], "palabras"),
    ([{"codigo": "CIE", "palabras": 0}], "palabras"),
    ([{"codigo": "CIE", "palabras": False}], "palabras"),
    ([{"codigo": "CIE", "palabras": None}], "palabras"),
])
def test_f061_r1_una_config_mal_escrita_avisa_con_su_motivo(entradas, motivo):
    from application.palabras_incidencia import palabras_por_codigo

    with pytest.raises(ValueError, match=rf"sync\.incidencias\.palabras_extra.*{motivo}"):
        palabras_por_codigo(entradas)


def test_f061_r1_la_api_no_arranca_con_la_config_mal_escrita(monkeypatch):
    """Como las consultas: mal escrita, falla al montar el contenedor, no
    al primer `GET /incidencias`."""
    from config.settings import cargar_config

    from tests.test_f023_sync_empresa import _contenedor, _SigridFalso

    config: dict[str, Any] = {**cargar_config()}
    config["sync"] = {**config["sync"], "incidencias": {
        **config["sync"]["incidencias"], "palabras_extra": [{"codigo": "CIE"},
                                                            {"codigo": "CIE"}]}}
    with pytest.raises(ValueError, match="repetido"):
        _contenedor(monkeypatch, _SigridFalso([], []), config)


# ------------------------------- ruta ------------------------------------ #
def _get_incidencias(tipos: list[Any]) -> Any:
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.api.app import build_app
    from interface_adapters.api.deps import obtener_contenedor

    from tests.test_f024_rutas_empresa import _Contenedor, _UowCM

    class _Tipos:
        def activos(self):
            return tipos

    uow = _UowCM({})
    uow.tipos_incidencia = _Tipos()
    settings = Settings(_env_file=None)
    app = build_app(settings)
    app.dependency_overrides[obtener_contenedor] = lambda: _Contenedor(
        settings=settings, uow=lambda: uow)
    return TestClient(app).get("/api/v1/incidencias")


def test_f061_r1_ruta_publica_palabras_y_orden_de_la_config():
    """Por letra, como en F-030; un código sin entrada sale con la lista
    vacía y `orden_busqueda` nulo, y una entrada sin código en el catálogo
    (aquí CIF y CIH) no aparece."""
    from domain.models import TipoIncidencia

    r = _get_incidencias([
        TipoIncidencia(11, "CIA", "AT", "Accidente/Enf. Profesional"),
        TipoIncidencia(12, "CIE", "B", "Enfermedad/Acc. no laboral"),
        TipoIncidencia(16, "CIP", "FJ", "Falta Justificada/Permiso"),
        TipoIncidencia(15, "CIM", "M", "Maternidad/Paternidad"),
        TipoIncidencia(17, "CIV", "V", "Vacaciones"),
        TipoIncidencia(19, "CIX", "X", "Nueva en Sigrid"),
    ])
    assert r.status_code == 200, r.text
    assert r.json() == {"incidencias": [
        {"codigo": "CIA", "letra": "AT", "nombre": "Accidente/Enf. Profesional",
         "palabras": ["baja", "accidente de trabajo"], "orden_busqueda": 1},
        {"codigo": "CIE", "letra": "B", "nombre": "Enfermedad/Acc. no laboral",
         "palabras": ["baja", "IT", "enfermedad común"], "orden_busqueda": 0},
        {"codigo": "CIP", "letra": "FJ", "nombre": "Falta Justificada/Permiso",
         "palabras": ["permiso", "ausencia"], "orden_busqueda": 3},
        {"codigo": "CIM", "letra": "M", "nombre": "Maternidad/Paternidad",
         "palabras": ["baja", "nacimiento", "permiso"], "orden_busqueda": 2},
        {"codigo": "CIV", "letra": "V", "nombre": "Vacaciones",
         "palabras": [], "orden_busqueda": 5},
        {"codigo": "CIX", "letra": "X", "nombre": "Nueva en Sigrid",
         "palabras": [], "orden_busqueda": None},
    ]}


def test_f061_r1_ruta_sin_palabras_en_la_config(monkeypatch):
    from config.settings import cargar_config
    from domain.models import TipoIncidencia
    from interface_adapters.api import routes

    config: dict[str, Any] = {**cargar_config()}
    config["sync"] = {**config["sync"], "incidencias": {
        "sql": config["sync"]["incidencias"]["sql"]}}
    monkeypatch.setattr(routes, "cargar_config", lambda: config)
    r = _get_incidencias([TipoIncidencia(12, "CIE", "B", "Enfermedad")])
    assert r.json() == {"incidencias": [
        {"codigo": "CIE", "letra": "B", "nombre": "Enfermedad",
         "palabras": [], "orden_busqueda": None}]}
