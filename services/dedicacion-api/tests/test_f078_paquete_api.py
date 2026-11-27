# tests/test_f078_paquete_api.py
"""F-078 · `trabajador_ides` en `POST …/registro/preflight` y
`…/registro/ejecutar`: registrar un paquete de trabajadores (los
seleccionados o los visibles del front) en vez del mes entero.

- Rutas (R2-R5): la lista se valida antes de nada; mal formada, vacía o
  junto a un `trabajador_ide` no nulo es 422 sin llamar al registro (un
  paquete roto nunca registra el mes entero). Sin la clave o con `null`, la
  llamada de hoy.
- Registro (R1, R6-R11, R23, R24): solo esos trabajadores y cada uno entero,
  con las peticiones del mes quitando lo de los de fuera.

Dobles: la app con el registro falso de `test_f024_rutas_empresa.py`, el
transfer falso de `test_f054_registro_cero.py` y una sesión que APLICA el
filtro por trabajador que lleva la sentencia (`==` o `IN`, en `asignacion` y
en `incidencia`); sin filtro, el mes entero, como la base. Ni red ni BBDD.
Los `ide` son inventados.
"""
from __future__ import annotations

import pytest

from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)

RUTAS = ["preflight", "ejecutar"]

#: Claves con que las rutas llaman hoy al registro (F-056), sin la nueva.
CLAVES_HOY = {
    "preflight": {"trabajador_ide", "empresa", "obra_ide"},
    "ejecutar": {"pisar_claves", "overrides", "usuario", "trabajador_ide",
                 "empresa", "sobrantes_a_cero"},
}


def _post(cliente, fase: str, crudo: bytes):
    return cliente.post(f"{BASE}/registro/{fase}", content=crudo,
                        headers={"Content-Type": "application/json"})


# ====================== R3: lo mal formado, 422 ======================== #
#: Valores de `trabajador_ides` que no son una lista NO vacía de enteros
#: (cuerpo JSON crudo).
MAL_FORMADOS = [
    b"[]", b"[null]", b"[11, null]", b'[""]', b"[true]", b"[false]",
    b"[11, true]", b'["abc"]', b"[1.5]", b'["1.5"]', b"[[11]]",
    b'[{"a": 11}]', b"[Infinity]",
    # No es una lista.
    b'"11"', b"11", b'""', b"true", b"false", b'{"a": 11}', b"0",
]


@pytest.mark.parametrize("valor", MAL_FORMADOS)
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r3_mal_formado_422_sin_llamar_al_registro(api, fase, valor):  # noqa: F811
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, b'{"trabajador_ides": ' + valor + b"}")
    assert r.status_code == 422, r.text
    assert r.json()["error"].startswith("trabajador_ides ")
    assert contenedor.registro_sigrid.llamadas == []


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r3_se_valida_antes_que_los_overrides(api, fase):  # noqa: F811
    """Unos `overrides` rotos (500 hoy, fuera de alcance) no tapan el 422."""
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase,
              b'{"trabajador_ides": [], "overrides": {"x": "y"}}')
    assert r.status_code == 422, r.text
    assert contenedor.registro_sigrid.llamadas == []


# ================= R4: los dos a la vez, 422 ========================== #
@pytest.mark.parametrize("trabajador", [b"11", b"0", b'"12"'])
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r4_lista_y_trabajador_a_la_vez_422(api, fase, trabajador):  # noqa: F811
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, b'{"trabajador_ides": [11, 12], '
              b'"trabajador_ide": ' + trabajador + b"}")
    assert r.status_code == 422, r.text
    assert r.json()["error"].startswith("trabajador_ides ")
    assert contenedor.registro_sigrid.llamadas == []


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r4_lista_con_trabajador_null_vale(api, fase):  # noqa: F811
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase,
              b'{"trabajador_ides": [11], "trabajador_ide": null}')
    assert r.status_code == 200, r.text
    [(_, kw)] = contenedor.registro_sigrid.llamadas
    assert kw["trabajador_ides"] == [11] and kw["trabajador_ide"] is None


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r4_trabajador_roto_sigue_siendo_su_error(api, fase):  # noqa: F811
    """El `trabajador_ide` se valida primero, como en F-056."""
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, b'{"trabajador_ides": [11], "trabajador_ide": ""}')
    assert r.status_code == 422, r.text
    assert r.json()["error"].startswith("trabajador_ide no es un entero")
    assert contenedor.registro_sigrid.llamadas == []


# ============== R2: enteros, en su orden y sin repetidos ============== #
@pytest.mark.parametrize(("crudo", "esperado"), [
    (b'["11", 12.0, 11]', [11, 12]),
    (b"[12, 11, 12, 12]", [12, 11]),
    (b"[0]", [0]),
    (b"[-3, 7]", [-3, 7]),
    (b'[7, "7", 7.0]', [7]),
])
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r2_enteros_sin_repetidos_en_su_orden(api, fase, crudo,  # noqa: F811
                                                  esperado):
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, b'{"trabajador_ides": ' + crudo + b"}")
    assert r.status_code == 200, r.text
    [(llamada, kw)] = contenedor.registro_sigrid.llamadas
    assert llamada == fase
    assert kw["trabajador_ides"] == esperado
    assert all(type(x) is int for x in kw["trabajador_ides"])
    assert kw["trabajador_ide"] is None


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r2_r11_sin_tope(api, fase):  # noqa: F811
    """R11 (D7): uno con «todos los del mes» (aquí, 900) se acepta."""
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    ides = list(range(1, 901))
    r = cliente.post(f"{BASE}/registro/{fase}", json={"trabajador_ides": ides})
    assert r.status_code == 200, r.text
    [(_, kw)] = contenedor.registro_sigrid.llamadas
    assert kw["trabajador_ides"] == ides


# =============== R5: sin la clave o con null, como hoy ================ #
@pytest.mark.parametrize("cuerpo", [b"{}", b'{"trabajador_ides": null}',
                                    b'{"trabajador_ide": 11}',
                                    b'{"trabajador_ide": 11, '
                                    b'"trabajador_ides": null}'])
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r5_sin_paquete_la_llamada_de_hoy(api, fase, cuerpo):  # noqa: F811
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, cuerpo)
    assert r.status_code == 200, r.text
    [(_, kw)] = contenedor.registro_sigrid.llamadas
    assert "trabajador_ides" not in kw
    assert set(kw) == CLAVES_HOY[fase]
    assert kw["trabajador_ide"] == (11 if b"11" in cuerpo else None)
