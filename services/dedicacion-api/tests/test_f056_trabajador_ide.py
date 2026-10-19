# tests/test_f056_trabajador_ide.py
"""F-056 · `trabajador_ide` validado en `POST …/registro/preflight` y
`…/registro/ejecutar` (observación de la review 4 de F-050).

Antes llegaba crudo del cuerpo y `registro_sigrid.py` filtraba con
`if trabajador_ide`: un valor falso (`0`, `""`, `false`) QUITABA el filtro y
`ejecutar` registraba el mes entero en vez de un trabajador; un texto llegaba
a PostgreSQL y daba 500. Ahora:

- Las dos rutas lo validan como `obra_ide` (F-050): entero o `null`; texto
  numérico (`"11"`) y `11.0` valen; `0` y negativos son enteros (no 422);
  cualquier otro valor es 422 ANTES de llamar al registro (ni se analiza ni
  se escribe).
- El filtro usa `is not None`: un `0` nunca quita el filtro (no casa con
  nadie y no se manda nada al transfer).

Dobles: la app con el registro falso de `test_f024_rutas_empresa.py`, el
transfer falso de `test_f022_empresa_en_linea.py` y una sesión que APLICA el
filtro por trabajador que lleva la sentencia (si no lo lleva, devuelve el mes
entero, como la base). Ni red ni BBDD.
"""
from __future__ import annotations

from typing import Any

import pytest
from application.registro_sigrid import RegistroSigrid
from domain.errors import ErrorDominio, ObraNoValida, TrabajadorNoValido
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import (
    BinaryExpression,
    BindParameter,
    ColumnClause,
)
from sqlalchemy.sql.visitors import iterate

from tests.test_f022_empresa_en_linea import _fila, _Resultado, _Transfer
from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)

#: Trabajador 10 en dos obras y trabajador 11 en una: el mes entero son dos
#: obras y tres líneas.
FILAS = [_fila(1, 10, 678), _fila(2, 11, 678), _fila(3, 10, 713)]

RUTAS = ["preflight", "ejecutar"]

#: Valores que NO son un entero (cuerpo JSON crudo: `Infinity` no se puede
#: escribir con `json=`).
NO_ENTEROS = [b'""', b"false", b"true", b'"abc"', b"1.5", b'"1.5"',
              b"[11]", b'{"a": 11}', b"Infinity"]


class _SesionQueFiltra:
    """Sesión falsa que aplica `asignacion.trabajador_ide == X` si la
    sentencia lo lleva en su WHERE; si no, devuelve todas las filas (el mes
    entero). `filtros` anota el valor de cada filtro encontrado."""

    def __init__(self, filas: list[tuple]) -> None:
        self._filas = filas
        self.filtros: list[Any] = []

    def __enter__(self) -> _SesionQueFiltra:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sentencia: Any) -> _Resultado:
        filas = list(self._filas)
        for nodo in iterate(sentencia.whereclause):
            if (isinstance(nodo, BinaryExpression)
                    and nodo.operator is operators.eq
                    and isinstance(nodo.left, ColumnClause)
                    and nodo.left.table.name == "asignacion"
                    and nodo.left.name == "trabajador_ide"
                    and isinstance(nodo.right, BindParameter)):
                valor = nodo.right.value
                self.filtros.append(valor)
                filas = [f for f in filas if f[1].ide == valor]
        return _Resultado(filas)


def _registro() -> tuple[RegistroSigrid, _Transfer, _SesionQueFiltra]:
    transfer = _Transfer()
    sesion = _SesionQueFiltra(FILAS)
    return RegistroSigrid(lambda: sesion, transfer, 1), transfer, sesion


def _llamar(registro: RegistroSigrid, fase: str, **kw) -> dict:
    if fase == "preflight":
        return registro.preflight(2026, 8, **kw)
    return registro.ejecutar(2026, 8, pisar_claves=[], **kw)


def _post(cliente, fase: str, crudo: bytes):
    return cliente.post(f"{BASE}/registro/{fase}", content=crudo,
                        headers={"Content-Type": "application/json"})


# ------------------------- El error de dominio ------------------------- #
def test_f056_trabajador_no_valido_es_error_de_dominio_propio():
    assert issubclass(TrabajadorNoValido, ErrorDominio)
    assert not issubclass(TrabajadorNoValido, ObraNoValida)


# ------------------ Rutas: lo que no es entero, 422 ------------------- #
@pytest.mark.parametrize("valor", NO_ENTEROS)
@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a1_no_entero_422_sin_analizar_ni_escribir(api, fase, valor):  # noqa: F811
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, b'{"trabajador_ide": ' + valor + b"}")
    assert r.status_code == 422, r.text
    assert r.json()["error"].startswith("trabajador_ide no es un entero")
    assert contenedor.registro_sigrid.llamadas == []


@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a1_se_valida_antes_que_los_overrides(api, fase):  # noqa: F811
    """El 422 llega antes de leer nada más del cuerpo: unos `overrides`
    rotos (que hoy dan 500, fuera de alcance) no lo tapan."""
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase,
              b'{"trabajador_ide": "", "overrides": {"x": "y"}}')
    assert r.status_code == 422, r.text
    assert contenedor.registro_sigrid.llamadas == []


# --------------- Rutas: enteros y null pasan como entero -------------- #
@pytest.mark.parametrize(("crudo", "esperado"), [
    (b"0", 0), (b"11", 11), (b'"11"', 11), (b"11.0", 11), (b"-3", -3),
    (b"null", None)])
@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a1_entero_o_null_llega_al_registro(api, fase, crudo, esperado):  # noqa: F811
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, b'{"trabajador_ide": ' + crudo + b"}")
    assert r.status_code == 200, r.text
    [(llamada, kw)] = contenedor.registro_sigrid.llamadas
    assert llamada == fase
    assert kw["trabajador_ide"] == esperado
    assert type(kw["trabajador_ide"]) is type(esperado)


@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a1_sin_trabajador_es_el_mes_entero(api, fase):  # noqa: F811
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, fase, b"{}")
    assert r.status_code == 200, r.text
    [(_, kw)] = contenedor.registro_sigrid.llamadas
    assert kw["trabajador_ide"] is None


def test_f056_a1_obra_no_valida_sigue_siendo_de_obra(api):  # noqa: F811
    """Con trabajador válido y obra rota, el error es de `obra_ide`."""
    cliente, contenedor = api
    contenedor.registro_sigrid.llamadas.clear()
    r = _post(cliente, "preflight", b'{"trabajador_ide": 11, "obra_ide": "x"}')
    assert r.status_code == 422, r.text
    assert r.json()["error"].startswith("obra_ide no es un entero")
    assert contenedor.registro_sigrid.llamadas == []


# ------------- El filtro: un 0 nunca coge el mes entero --------------- #
@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a2_cero_filtra_y_no_manda_nada(fase):
    registro, transfer, sesion = _registro()
    r = _llamar(registro, fase, trabajador_ide=0)
    assert sesion.filtros == [0]
    assert transfer.payloads == []
    assert r == {"ok": True, "obras": [], "no_vigentes": []}


@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a2_un_trabajador_solo_sus_lineas(fase):
    registro, transfer, sesion = _registro()
    _llamar(registro, fase, trabajador_ide=11)
    assert sesion.filtros == [11]
    assert [[ln["registro_id"] for ln in p["lineas"]]
            for p in transfer.payloads] == [[2]]


@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a2_sin_trabajador_el_mes_entero(fase):
    registro, transfer, sesion = _registro()
    _llamar(registro, fase, trabajador_ide=None)
    assert sesion.filtros == []
    assert sorted(ln["registro_id"] for p in transfer.payloads
                  for ln in p["lineas"]) == [1, 2, 3]


# --------- De punta a punta: ruta + registro real + transfer ---------- #
@pytest.mark.parametrize(("crudo", "http"), [(b'""', 422), (b"false", 422),
                                             (b'"abc"', 422), (b"0", 200)])
@pytest.mark.parametrize("fase", RUTAS)
def test_f056_a1_a2_ruta_con_registro_real_no_escribe(api, fase, crudo, http):  # noqa: F811
    """Con el registro de verdad detrás: ni un valor rechazado ni un `0`
    llegan a mandar una sola línea al transfer."""
    cliente, contenedor = api
    registro, transfer, sesion = _registro()
    contenedor.registro_sigrid = registro
    r = _post(cliente, fase, b'{"trabajador_ide": ' + crudo + b"}")
    assert r.status_code == http, r.text
    assert transfer.payloads == []
    assert sesion.filtros == ([0] if http == 200 else [])
