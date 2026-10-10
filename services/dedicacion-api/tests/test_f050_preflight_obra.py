# tests/test_f050_preflight_obra.py
"""F-050 · T15c, punto 5 de la M2 (humano, 2026-10-11): el preflight de UNA
obra.

Al cambiar una partida en el modal de registro, el front repite el preflight
solo de la obra de esa línea (y del trabajador, si la petición era de una
fila): `obra_ide` en el cuerpo de `POST …/registro/preflight`. Antes se
repetía el del mes entero, una llamada al transfer por obra, y el proxy del
front cortaba a los 120 s con 502. La obra es la del GRUPO de la petición
(la de registro en las entradas VAR, F-039), la misma que el front lee de
`obras[].obra.ide`. El transfer no cambia. Registrar (`ejecutar`) no se acota.

Sesión y transfer falsos de `test_f022_empresa_en_linea.py`, obras de
`test_f039_registro_var.py` y la app con el registro falso de
`test_f024_rutas_empresa.py`. Ni red ni BBDD.
"""
from __future__ import annotations

from application.registro_sigrid import RegistroSigrid

from tests.test_f022_empresa_en_linea import _Sesion, _Transfer
from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)
from tests.test_f039_registro_var import O678, VAR, VAR_29, VAR_IDE, _fila

FILAS = [_fila(1, 10, O678), _fila(2, 11, VAR_29), _fila(3, 12, VAR),
         _fila(4, 10, O678, pv=True)]


def _preflight(**kw) -> tuple[dict, list[dict]]:
    transfer = _Transfer()
    registro = RegistroSigrid(lambda: _Sesion(FILAS), transfer, 1)
    return registro.preflight(2026, 8, **kw), transfer.payloads


def test_f050_m2_5_solo_la_obra_pedida_va_al_transfer():
    r, payloads = _preflight(obra_ide=678)
    assert [p["obra"]["ide"] for p in payloads] == [678]
    assert [ln["registro_id"] for ln in payloads[0]["lineas"]] == [1, 4]
    assert [o["obra"]["ide"] for o in r["obras"]] == [678]
    assert r["ok"] is True


def test_f050_m2_5_la_obra_es_la_del_grupo_var_incluida():
    """`VAR-29` viaja en la petición de la obra VAR: pedir la VAR la trae
    con la línea de la propia VAR."""
    _, payloads = _preflight(obra_ide=VAR_IDE)
    assert [p["obra"]["ide"] for p in payloads] == [VAR_IDE]
    assert [ln["registro_id"] for ln in payloads[0]["lineas"]] == [2, 3]


def test_f050_m2_5_sin_obra_todas_como_antes():
    r, payloads = _preflight()
    assert [p["obra"]["ide"] for p in payloads] == [678, VAR_IDE]
    assert len(r["obras"]) == 2
    _, payloads = _preflight(obra_ide=None, trabajador_ide=None)
    assert len(payloads) == 2


def test_f050_m2_5_obra_sin_lineas_ninguna_llamada():
    r, payloads = _preflight(obra_ide=999)
    assert payloads == []
    assert r == {"ok": True, "obras": [], "no_vigentes": []}


def test_f050_m2_5_la_ruta_pasa_la_obra(api):  # noqa: F811
    cliente, contenedor = api
    for cuerpo, obra in (({"trabajador_ide": 11, "obra_ide": 694}, 694),
                         ({"trabajador_ide": 11}, None),
                         ({"obra_ide": 678}, 678)):
        contenedor.registro_sigrid.llamadas.clear()
        r = cliente.post(f"{BASE}/registro/preflight", json=cuerpo)
        assert r.status_code == 200, r.text
        [(fase, kw)] = contenedor.registro_sigrid.llamadas
        assert fase == "preflight"
        assert kw["obra_ide"] == obra
        assert kw["trabajador_ide"] == cuerpo.get("trabajador_ide")


def test_f050_m2_5_registrar_no_se_acota_por_obra(api):  # noqa: F811
    """Solo el análisis se acota: `ejecutar` no recibe `obra_ide`."""
    cliente, contenedor = api
    r = cliente.post(f"{BASE}/registro/ejecutar",
                     json={"trabajador_ide": 11, "obra_ide": 694})
    assert r.status_code == 200, r.text
    [(fase, kw)] = contenedor.registro_sigrid.llamadas
    assert fase == "ejecutar" and "obra_ide" not in kw
