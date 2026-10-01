# tests/test_f024_rutas_empresa.py
"""F-024 · El parámetro `empresa` en la API y `GET /api/v1/empresas`
(R1, R2, R6, R11, R15, R18).

`TestClient` sobre la app real con `dependency_overrides[obtener_contenedor]`:
el contenedor falso trae la UnitOfWork en memoria de
`test_f024_cuadrante_empresa.py`, un exportador y un registro que anotan lo
que reciben. El engine de SQLAlchemy no conecta hasta usarse: ni red, ni
BBDD, ni `.env`.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Self

import pytest
from config.settings import Settings
from domain.models import Empresa
from fastapi.testclient import TestClient
from interface_adapters.api.app import build_app
from interface_adapters.api.deps import obtener_contenedor

from tests.test_f024_cuadrante_empresa import (
    ANIO,
    MES,
    P_ACT,
    P_ANT,
    _lineas_actuales,
    _ln,
    _Uow,
)


class _UowCM(_Uow):
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class _Exportador:
    def __init__(self) -> None:
        self.filas: list[Any] | None = None

    def exportar(self, periodo, filas) -> bytes:
        self.filas = filas
        return b"xlsx"


class _Registro:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, dict]] = []

    def preflight(self, anio, mes, overrides=None, **kw) -> dict:
        self.llamadas.append(("preflight", kw))
        return {"ok": True, "obras": []}

    def ejecutar(self, anio, mes, **kw) -> dict:
        self.llamadas.append(("ejecutar", kw))
        return {"ok": True, "obras": []}


class _Contenedor(SimpleNamespace):
    pass


@pytest.fixture
def api(monkeypatch):
    """(cliente, contenedor falso) con EMPRESA_IMPUTACION = 1."""
    monkeypatch.delenv("EMPRESA_IMPUTACION", raising=False)
    settings = Settings(_env_file=None)
    # Una sola UoW en memoria para todas las peticiones del test (así
    # «deshacer» ve lo que guardó el PUT); `uows` anota cada apertura.
    compartida = _UowCM({P_ACT: _lineas_actuales(),
                         P_ANT: {14: [_ln(101, "100")]}})
    # Catálogo de empresas en la tabla (F-032; antes, `empresas.nombres`).
    compartida.empresas.fichas = [Empresa(1, "Construcciones Ruesma"),
                                  Empresa(28, "Porsan")]
    uows: list[_UowCM] = []

    def nueva_uow() -> _UowCM:
        uows.append(compartida)
        return compartida

    contenedor = _Contenedor(settings=settings, uow=nueva_uow,
                             exporter=_Exportador(), registro_sigrid=_Registro(),
                             uows=uows)
    app = build_app(settings)
    app.dependency_overrides[obtener_contenedor] = lambda: contenedor
    return TestClient(app), contenedor


BASE = f"/api/v1/periodos/{ANIO}/{MES}"


# ------------------------------ R1 / R2 ------------------------------- #
def test_f024_r1_r2_get_empresas(api):
    cliente, _ = api
    r = cliente.get("/api/v1/empresas")
    assert r.status_code == 200, r.text
    assert r.json() == {"por_defecto": 1, "empresas": [
        {"empresa": 1, "nombre": "Construcciones Ruesma", "de_baja": False},
        {"empresa": 18, "nombre": "Empresa 18", "de_baja": False},
        {"empresa": 28, "nombre": "Porsan", "de_baja": False},
    ]}


# --------------------------------- R6 --------------------------------- #
def test_f024_r6_sin_empresa_la_por_defecto(api):
    cliente, _ = api
    cuerpo = cliente.get(f"{BASE}/cuadrante").json()
    assert cuerpo["empresa"] == 1
    assert [t["nombre"] for t in cuerpo["trabajadores"]] == [
        "Ana", "Dani", "Eva", "Gil"]


def test_f024_r6_con_empresa_la_elegida(api):
    cliente, _ = api
    cuerpo = cliente.get(f"{BASE}/cuadrante", params={"empresa": 28}).json()
    assert cuerpo["empresa"] == 28
    assert [t["nombre"] for t in cuerpo["trabajadores"]] == [
        "Bea", "Carlos", "Gil"]
    assert [o["ide"] for o in cuerpo["obras"]] == [900]
    assert cuerpo["resumen"]["total"] == 3


RUTAS = [
    ("get", "/cuadrante", None),
    ("put", "/trabajadores/14/asignaciones",
     {"lineas": [{"obra_ide": 101, "porcentaje": 100}]}),
    ("post", "/trabajadores/14/deshacer", None),
    ("post", "/trabajadores/14/copiar-anterior", None),
    ("post", "/copiar-anterior", None),
    ("get", "/export.xlsx", None),
    ("post", "/registro/preflight", {}),
    ("post", "/registro/ejecutar", {}),
]


@pytest.mark.parametrize("valor", ["0", "-3", "abc", "1.5"])
@pytest.mark.parametrize("metodo, ruta, cuerpo", RUTAS,
                         ids=[r[1] for r in RUTAS])
def test_f024_r6_empresa_invalida_es_422_sin_tocar_nada(api, metodo, ruta,
                                                        cuerpo, valor):
    cliente, contenedor = api
    r = cliente.request(metodo.upper(), f"{BASE}{ruta}",
                        params={"empresa": valor}, json=cuerpo)
    assert r.status_code == 422, r.text
    assert contenedor.uows == []
    assert contenedor.registro_sigrid.llamadas == []


@pytest.mark.parametrize("empresa, total", [(None, 4), (1, 4), (28, 3)])
@pytest.mark.parametrize("metodo, ruta, cuerpo", RUTAS[1:4],
                         ids=[r[1] for r in RUTAS[1:4]])
def test_f024_r6_r13_respuestas_por_fila_con_el_resumen_de_la_empresa(
        api, metodo, ruta, cuerpo, empresa, total):
    cliente, _ = api
    params = {} if empresa is None else {"empresa": empresa}
    if ruta.endswith("deshacer"):     # que haya algo que deshacer
        cliente.put(f"{BASE}/trabajadores/14/asignaciones", params=params,
                    json={"lineas": [{"obra_ide": 101, "porcentaje": 50}]})
    r = cliente.request(metodo.upper(), f"{BASE}{ruta}", params=params,
                        json=cuerpo)
    assert r.status_code == 200, r.text
    assert r.json()["resumen"]["total"] == total


@pytest.mark.parametrize("empresa, copiados", [(None, 1), (1, 1), (28, 0)])
def test_f024_r6_r14_copiar_mes_con_la_empresa(api, empresa, copiados):
    cliente, contenedor = api
    params = {} if empresa is None else {"empresa": empresa}
    r = cliente.post(f"{BASE}/copiar-anterior", params=params)
    assert r.status_code == 200, r.text
    assert r.json()["trabajadores_copiados"] == copiados
    assert contenedor.uows[0].reemplazados == ([14] if copiados else [])


# --------------------------------- R11 -------------------------------- #
def test_f024_r11_empresa_del_trabajador_y_de_cada_linea(api):
    cliente, _ = api
    cuerpo = cliente.get(f"{BASE}/cuadrante", params={"empresa": 1}).json()
    por_nombre = {t["nombre"]: t for t in cuerpo["trabajadores"]}
    assert por_nombre["Ana"]["empresa"] == 1
    assert por_nombre["Dani"]["empresa"] is None
    assert [(ln["obra_ide"], ln["obra_empresa"], ln["otra_empresa"])
            for ln in por_nombre["Ana"]["lineas"]] == [
        (100, 1, False), (900, 28, True)]
    assert [(ln["obra_empresa"], ln["otra_empresa"])
            for ln in por_nombre["Dani"]["lineas"]] == [(None, False)]
    # R10: el total y el estado se calculan sobre todas las líneas.
    assert (por_nombre["Ana"]["total"], por_nombre["Ana"]["estado"]) == (
        100.0, "OK")


def test_f024_r11_otra_empresa_depende_de_la_elegida(api):
    cliente, _ = api
    cuerpo = cliente.get(f"{BASE}/cuadrante", params={"empresa": 28}).json()
    gil = next(t for t in cuerpo["trabajadores"] if t["nombre"] == "Gil")
    assert [(ln["obra_empresa"], ln["otra_empresa"])
            for ln in gil["lineas"]] == [(1, True), (28, False)]


# --------------------------------- R15 -------------------------------- #
@pytest.mark.parametrize("empresa, nombres", [
    (None, ["Ana", "Dani", "Eva", "Gil"]), (28, ["Bea", "Carlos", "Gil"])])
def test_f024_r15_export_filtrado_y_con_la_empresa_en_el_nombre(
        api, empresa, nombres):
    cliente, contenedor = api
    params = {} if empresa is None else {"empresa": empresa}
    r = cliente.get(f"{BASE}/export.xlsx", params=params)
    assert r.status_code == 200, r.text
    esperado = f"dedicacion_{ANIO}{MES:02d}_emp{empresa or 1}.xlsx"
    assert r.headers["content-disposition"] == (
        f'attachment; filename="{esperado}"')
    assert [f.trabajador.nombre for f in contenedor.exporter.filas] == nombres


# --------------------------------- R18 -------------------------------- #
@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
@pytest.mark.parametrize("empresa", [None, 18])
def test_f024_r6_r18_registro_recibe_la_empresa_por_query(api, fase,
                                                         empresa):
    cliente, contenedor = api
    params = {} if empresa is None else {"empresa": empresa}
    r = cliente.post(f"{BASE}/registro/{fase}", params=params,
                     json={"trabajador_ide": 11})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "obras": []}
    [(llamada, kw)] = contenedor.registro_sigrid.llamadas
    assert llamada == fase
    assert kw["empresa"] == (empresa or 1)
    assert kw["trabajador_ide"] == 11
