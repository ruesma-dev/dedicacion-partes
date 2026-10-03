# tests/test_f034_rutas.py
"""F-034 · Obras ofrecidas y marca `otra_empresa` en la respuesta HTTP
(R1, R5), con E = 1, 18 y 28.

`TestClient` sobre la app real con el contenedor falso de
`test_f024_rutas_empresa.py` (UnitOfWork en memoria, `EMPRESA_IMPUTACION`
= 1). Ni red, ni BBDD, ni `.env`. La regla está en
`docs/ARCHITECTURE.md#regla-empresa`.
"""
from __future__ import annotations

import pytest
from config.settings import Settings

from tests.test_f024_cuadrante_empresa import P_ANT, _ln
from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)

#: Campos de la respuesta del cuadrante y de cada línea: F-034 no añade ni
#: quita ninguno (design §4.3).
CAMPOS_CUADRANTE = {"periodo", "empresa", "obras", "trabajadores", "resumen"}
CAMPOS_LINEA = {"obra_ide", "cod", "descripcion", "es_postventa",
                "porcentaje", "obra_activa", "obra_empresa", "otra_empresa"}


def _marcas(trabajador: dict) -> list[tuple[int, int | None, bool]]:
    return [(ln["obra_ide"], ln["obra_empresa"], ln["otra_empresa"])
            for ln in trabajador["lineas"]]


# ================================== R1 ================================== #
@pytest.mark.parametrize("empresa", [None, 1, 18, 28])
def test_f034_r1_cuadrante_ofrece_las_obras_de_la_empresa_de_las_obras(
        api, empresa):  # noqa: F811
    cliente, _ = api
    params = {} if empresa is None else {"empresa": empresa}
    r = cliente.get(f"{BASE}/cuadrante", params=params)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert [o["ide"] for o in cuerpo["obras"]] == [100, 101, 102]
    assert cuerpo["empresa"] == (empresa or 1)
    assert set(cuerpo) == CAMPOS_CUADRANTE
    for t in cuerpo["trabajadores"]:
        for ln in t["lineas"]:
            assert set(ln) == CAMPOS_LINEA


# ================================== R5 ================================== #
def test_f034_r5_cuadrante_con_la_28_marca_la_obra_de_la_28(api):  # noqa: F811
    """Bea (28) con su línea en la 900 (28): con E = 28 la obra no es de la
    empresa de las obras, así que se marca (con F-024 no se marcaba)."""
    cliente, _ = api
    cuerpo = cliente.get(f"{BASE}/cuadrante", params={"empresa": 28}).json()
    [bea] = cuerpo["trabajadores"]
    assert _marcas(bea) == [(900, 28, True)]


def test_f034_r5_cuadrante_con_la_1_marca_igual(api):  # noqa: F811
    cliente, _ = api
    cuerpo = cliente.get(f"{BASE}/cuadrante", params={"empresa": 1}).json()
    por_nombre = {t["nombre"]: t for t in cuerpo["trabajadores"]}
    assert _marcas(por_nombre["Ana"]) == [(100, 1, False), (900, 28, True)]
    assert _marcas(por_nombre["Dani"]) == [(500, None, False)]


def test_f034_r5_guardar_con_la_18_marca_contra_la_empresa_de_las_obras(
        api):  # noqa: F811
    """Fran (18) guarda una línea en una obra de Ruesma y otra en la 900: la
    de Ruesma no se marca aunque la elegida sea la 18."""
    cliente, _ = api
    r = cliente.put(f"{BASE}/trabajadores/15/asignaciones",
                    params={"empresa": 18},
                    json={"lineas": [{"obra_ide": 101, "porcentaje": 60},
                                     {"obra_ide": 900, "porcentaje": 40}]})
    assert r.status_code == 200, r.text
    assert _marcas(r.json()["trabajador"]) == [(101, 1, False),
                                               (900, 28, True)]


def test_f034_r5_deshacer_y_copiar_marcan_contra_la_empresa_de_las_obras(
        api):  # noqa: F811
    """Las otras dos respuestas por fila, con E = 28: Bea vuelve a su 900 y
    sale marcada en las dos."""
    cliente, contenedor = api
    params = {"empresa": 28}
    r = cliente.put(f"{BASE}/trabajadores/11/asignaciones", params=params,
                    json={"lineas": [{"obra_ide": 101, "porcentaje": 100}]})
    assert _marcas(r.json()["trabajador"]) == [(101, 1, False)]
    r = cliente.post(f"{BASE}/trabajadores/11/deshacer", params=params)
    assert r.status_code == 200, r.text
    assert _marcas(r.json()["trabajador"]) == [(900, 28, True)]

    contenedor.uow().lineas[P_ANT][11] = [_ln(900, "100")]
    r = cliente.post(f"{BASE}/trabajadores/11/copiar-anterior", params=params)
    assert r.status_code == 200, r.text
    assert _marcas(r.json()["trabajador"]) == [(900, 28, True)]


# ================================== R10 ================================= #
def test_f034_r10_la_empresa_de_las_obras_sale_del_ajuste_en_las_rutas(
        api):  # noqa: F811
    """Con `EMPRESA_IMPUTACION` = 28, las obras ofrecidas y la marca de cada
    línea se miden contra la 28, no contra un 1 fijo: Ana (1) tiene marcada
    su línea en la 100 (de la 1) y no la de la 900 (de la 28). Cubre el
    superviviente manual M12 de `progress/impl_F-034.md`."""
    cliente, contenedor = api
    contenedor.settings = Settings(_env_file=None, empresa_imputacion=28)
    cuerpo = cliente.get(f"{BASE}/cuadrante", params={"empresa": 1}).json()
    assert [o["ide"] for o in cuerpo["obras"]] == [900]
    ana = next(t for t in cuerpo["trabajadores"] if t["nombre"] == "Ana")
    assert _marcas(ana) == [(100, 1, True), (900, 28, False)]
