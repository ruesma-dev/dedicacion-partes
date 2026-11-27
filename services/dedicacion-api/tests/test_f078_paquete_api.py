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
from application.registro_sigrid import RegistroSigrid
from sqlalchemy.sql import operators
from sqlalchemy.sql.dml import Update
from sqlalchemy.sql.elements import (
    BinaryExpression,
    BindParameter,
    ColumnClause,
)
from sqlalchemy.sql.visitors import iterate

from tests.test_f024_registro_empresa import _fila
from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)
from tests.test_f030_r30_identidad import _inc_traza
from tests.test_f054_registro_cero import SOBRANTE, _TransferCero

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
                                    (b'{"trabajador_ide": 11, '
                                     b'"trabajador_ides": null}')])
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


# ======================================================================= #
#              El registro: solo el paquete, cada uno entero              #
# ======================================================================= #
class _Resultado:
    def __init__(self, filas: list[tuple]) -> None:
        self._filas = filas

    def all(self) -> list[tuple]:
        return list(self._filas)


class _SesionPaquete:
    """Sesión falsa que APLICA el filtro por trabajador de la sentencia
    (`trabajador_ide == X` o `trabajador_ide IN (…)`) sobre la tabla que lee
    (`asignacion` o `incidencia`); sin filtro, todo el mes, como la base.
    `filtros` anota (tabla, operador, valor) de cada filtro; el catálogo de
    tipos responde (código, letra) y los UPDATE se anotan."""

    def __init__(self, filas, incidencias, anotado) -> None:
        self._filas = filas
        self._incidencias = incidencias
        self._anotado = anotado

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sentencia):
        if isinstance(sentencia, Update):
            self._anotado["updates"].append(sentencia.compile().params)
            return None
        texto = str(sentencia)
        if "FROM tipo_incidencia" in texto:
            return _Resultado([("CIV", "V"), ("CIE", "B")])
        tabla = "incidencia" if "FROM incidencia" in texto else "asignacion"
        filas = list(self._incidencias if tabla == "incidencia"
                     else self._filas)
        for nodo in iterate(sentencia.whereclause):
            if (isinstance(nodo, BinaryExpression)
                    and isinstance(nodo.left, ColumnClause)
                    and nodo.left.table.name == tabla
                    and nodo.left.name == "trabajador_ide"
                    and isinstance(nodo.right, BindParameter)):
                valor = nodo.right.value
                if nodo.operator is operators.eq:
                    self._anotado["filtros"].append((tabla, "==", valor))
                    filas = [f for f in filas if f[1].ide == valor]
                elif nodo.operator is operators.in_op:
                    self._anotado["filtros"].append(
                        (tabla, "in", list(valor)))
                    filas = [f for f in filas if f[1].ide in valor]
                else:                                   # pragma: no cover
                    raise AssertionError(f"operador inesperado: {nodo}")
        return _Resultado(filas)

    def commit(self) -> None:
        self._anotado["updates"].append({"commit": True})


def _asig(asig_id, trab, obra, **kw):
    a, t, o = _fila(asig_id, trab, obra)
    for k, v in kw.items():
        setattr(a, k, v)
    return a, t, o


def _no_vigente(asig_id, trab, obra):
    a, t, o = _fila(asig_id, trab, obra)
    t.activo = False
    return a, t, o


def _filas():
    """El mes, en el orden de la consulta (código de obra, nombre): el 10
    en la 678, la 694 y una de postventa en la 800; el 11 en la 678 y la
    713; el 12 en la 678 y la 700 (solo suya); el 13, de baja, en la 694; el
    20, de otra empresa (la 28), en la 678."""
    return [_fila(1, (10, 1), (678, 1)), _fila(2, (11, 1), (678, 1)),
            _fila(3, (12, 1), (678, 1)), _fila(21, (20, 28), (678, 1)),
            _fila(4, (10, 1), (694, 1)), _no_vigente(6, (13, 1), (694, 1)),
            _fila(5, (12, 1), (700, 1)), _fila(7, (11, 1), (713, 1)),
            _asig(8, (10, 1), (800, 1), es_postventa=True)]


def _incs():
    """Las del mes, en su orden: el 10 tiene la 7 (con traza) y la 5
    (quitada con traza) en la 678 y la 8 en la 694; el 12, la 6 en la 678
    (obra compartida) y la 3 (quitada con traza) en la 700; el 11, la 9 y la
    4 (quitada sin traza) en la 694."""
    return [_inc_traza(7, (10, 1), (678, 1), ini=9001, fin=9002, dia_ini=5,
                       dia_fin=9),
            _inc_traza(5, (10, 1), (678, 1), desde=20, hasta=22, ini=9101,
                       dia_ini=20, quitada=True),
            _inc_traza(6, (12, 1), (678, 1), desde=1, hasta=2),
            _inc_traza(8, (10, 1), (694, 1), desde=12, hasta=16),
            _inc_traza(9, (11, 1), (694, 1), codigo="CIE", desde=1, hasta=3),
            _inc_traza(4, (11, 1), (694, 1), desde=27, hasta=28,
                       quitada=True),
            _inc_traza(3, (12, 1), (700, 1), desde=6, hasta=7, fin=9301,
                       dia_fin=7, quitada=True)]


def _registro(transfer=None, filas=None, incs=None):
    transfer = transfer if transfer is not None else _TransferCero()
    anotado = {"updates": [], "filtros": []}
    filas = _filas() if filas is None else filas
    incs = _incs() if incs is None else incs
    reg = RegistroSigrid(lambda: _SesionPaquete(filas, incs, anotado),
                         transfer, 1)
    return reg, transfer, anotado


def _llamar(reg, fase, **kw):
    if fase == "preflight":
        return reg.preflight(2026, 7, **kw)
    return reg.ejecutar(2026, 7, pisar_claves=[], **kw)


def _del_mes(fase):
    """Las peticiones del mes entero, como las recibe el transfer."""
    reg, transfer, _ = _registro()
    _llamar(reg, fase)
    return transfer.payloads


def _recortar(payloads, ides, orden=None):
    """Lo que R6 pide: las peticiones del mes sin nada de los de fuera,
    sin las obras vacías y con `cierres_recursos` designados de nuevo en el
    `orden` de obras dado (el del paquete: una obra donde el paquete solo
    tiene incidencias va al final, como en el modo trabajador)."""
    quedan = []
    for p in payloads:
        q = {k: v for k, v in p.items() if k != "cierres_recursos"}
        for clave in ("lineas", "incidencias", "quitadas", "incidencias_mes"):
            if clave in q:
                q[clave] = [x for x in q[clave] if x["recurso_ide"] in ides]
                if not q[clave] and clave != "lineas":
                    del q[clave]
        if q["lineas"] or q.get("incidencias") or q.get("quitadas"):
            quedan.append(q)
    if orden is not None:
        quedan.sort(key=lambda q: orden.index(q["obra"]["ide"]))
    vistos: set[int] = set()
    for q in quedan:
        suyos = []
        for x in [*q["lineas"], *q.get("incidencias", [])]:
            if x["recurso_ide"] not in vistos:
                vistos.add(x["recurso_ide"])
                suyos.append(x["recurso_ide"])
        if suyos:
            q["cierres_recursos"] = suyos
    return quedan


def _ids(payloads, clave="lineas"):
    return {p["obra"]["ide"]: [x.get("registro_id", x.get("id"))
                               for x in p.get(clave, [])]
            for p in payloads}


# ------------------------------- R1 ------------------------------------ #
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r1_filtra_por_in_en_asignaciones_e_incidencias(fase):
    reg, _, anotado = _registro()
    _llamar(reg, fase, trabajador_ides=[10, 11])
    assert anotado["filtros"] == [("asignacion", "in", [10, 11]),
                                  ("incidencia", "in", [10, 11])]


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r1_r5_un_trabajador_sigue_con_igual(fase):
    """R5: sin paquete, el filtro de F-056 (`==`) o ninguno (el mes)."""
    reg, _, anotado = _registro()
    _llamar(reg, fase, trabajador_ide=11)
    assert anotado["filtros"] == [("asignacion", "==", 11),
                                  ("incidencia", "==", 11)]
    reg, _, anotado = _registro()
    _llamar(reg, fase)
    assert anotado["filtros"] == []


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r1_cada_trabajador_entero(fase):
    """R1 (D2): todas sus líneas (obra y postventa) e incidencias, en todas
    sus obras; nada del 12 (fuera), ni de la 700, que es solo suya."""
    reg, transfer, _ = _registro()
    _llamar(reg, fase, trabajador_ides=[10, 11])
    assert _ids(transfer.payloads) == {678: [1, 2], 694: [4], 713: [7],
                                       800: [8]}
    assert _ids(transfer.payloads, "incidencias") == {
        678: [7], 694: [8, 9], 713: [], 800: []}
    assert {ln["recurso_ide"] for p in transfer.payloads
            for ln in p["lineas"]} == {10, 11}


# ------------------------------- R6 ------------------------------------ #
@pytest.mark.parametrize("ides", [[10, 11], [12], [11], [10, 12], [13]])
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r6_las_del_mes_sin_los_de_fuera(fase, ides):
    reg, transfer, _ = _registro()
    _llamar(reg, fase, trabajador_ides=ides)
    orden = [p["obra"]["ide"] for p in transfer.payloads]
    assert transfer.payloads == _recortar(_del_mes(fase), set(ides), orden)


@pytest.mark.parametrize("ide", [10, 11, 12, 13])
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r6_paquete_de_uno_es_el_modo_trabajador(fase, ide):
    """Design §3: el modo trabajador ya es «un paquete de uno»; las mismas
    peticiones, en el mismo orden (el 11 solo tiene una incidencia en la
    694: esa obra va al final, como hoy)."""
    reg, paquete, _ = _registro()
    r_paquete = _llamar(reg, fase, trabajador_ides=[ide])
    reg, uno, _ = _registro()
    r_uno = _llamar(reg, fase, trabajador_ide=ide)
    assert paquete.payloads == uno.payloads and r_paquete == r_uno


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r6_detalle_del_paquete_de_dos(fase):
    """El 10 y el 11: la 678 sin la línea ni la incidencia del 12, con la
    quitada del 10 y las del mes de los dos; los cierres, otra vez."""
    reg, transfer, _ = _registro()
    _llamar(reg, fase, trabajador_ides=[10, 11])
    p678, p694, p713, p800 = transfer.payloads
    assert [q["id"] for q in p678["quitadas"]] == [5]
    assert [i["id"] for i in p678["incidencias_mes"]] == [7, 8, 9]
    assert [i["id"] for i in p694["incidencias_mes"]] == [7, 8, 9]
    assert "quitadas" not in p694
    assert p678["cierres_recursos"] == [10, 11]
    assert all("cierres_recursos" not in p for p in (p694, p713, p800))
    assert 700 not in {p["obra"]["ide"] for p in transfer.payloads}


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r6_r11_con_todos_las_peticiones_del_mes(fase):
    """R11 (D7): sin tope; con todos los del mes, las mismas peticiones."""
    reg, transfer, _ = _registro()
    _llamar(reg, fase, trabajador_ides=[10, 11, 12, 13, 20])
    assert transfer.payloads == _del_mes(fase)


# ------------------------------- R9 ------------------------------------ #
@pytest.mark.parametrize(("ides", "no_vigentes"), [
    ([10, 11], []), ([11, 13], [6]), ([13], [6])])
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r9_no_vigentes_solo_del_paquete(fase, ides, no_vigentes):
    reg, _, _ = _registro()
    assert _llamar(reg, fase, trabajador_ides=ides)["no_vigentes"] == \
        no_vigentes
    reg, _, _ = _registro()
    assert _llamar(reg, fase)["no_vigentes"] == [6]


@pytest.mark.parametrize(("ides", "quitadas"), [
    ([10, 11], [5, 4]), ([12], [3]), ([11], [4]), ([13], None)])
def test_f078_r9_incidencias_quitadas_solo_del_paquete(ides, quitadas):
    reg, _, _ = _registro()
    r = reg.preflight(2026, 7, trabajador_ides=ides)
    if quitadas is None:
        assert "incidencias_quitadas" not in r
    else:
        assert [q["id"] for q in r["incidencias_quitadas"]] == quitadas
        assert {q["trabajador_ide"] for q in r["incidencias_quitadas"]} <= \
            set(ides)
    reg, _, _ = _registro()
    assert [q["id"] for q in reg.preflight(2026, 7)[
        "incidencias_quitadas"]] == [5, 4, 3]


# ------------------------------- R10 ----------------------------------- #
@pytest.mark.parametrize("ides", [[99], [20], [99, 20], [13]])
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r10_nada_que_registrar_como_un_trabajador(fase, ides):
    """Un `ide` que no existe, uno de otra empresa o uno de baja: lo mismo
    que el modo trabajador en ese caso, y el transfer sin llamadas."""
    reg, transfer, _ = _registro()
    r = _llamar(reg, fase, trabajador_ides=ides)
    assert r == {"ok": True, "obras": [],
                 "no_vigentes": [6] if 13 in ides else []}
    assert transfer.llamadas == [] and transfer.payloads == []
    uno, t_uno, _ = _registro()
    assert _llamar(uno, fase, trabajador_ide=ides[0]) == r
    assert t_uno.payloads == []


@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r10_lista_vacia_por_codigo_no_es_el_mes(fase):
    """La ruta da 422 con `[]`; si llegase por código, `IN ()` no casa con
    nadie: nunca el mes entero (design §5)."""
    reg, transfer, anotado = _registro()
    r = _llamar(reg, fase, trabajador_ides=[])
    assert anotado["filtros"] == [("asignacion", "in", []),
                                  ("incidencia", "in", [])]
    assert r == {"ok": True, "obras": [], "no_vigentes": []}
    assert transfer.payloads == []


# ------------------------------- R7 ------------------------------------ #
def test_f078_r7_paquete_sin_obra_es_completo_con_sobrantes():
    t = _TransferCero([SOBRANTE])
    reg, _, _ = _registro(t)
    r = reg.preflight(2026, 7, trabajador_ides=[10, 11])
    assert t.llamadas == [("preflight_lote", True)]
    assert r["sobrantes"] == [SOBRANTE]
    assert [o["obra"]["ide"] for o in r["obras"]] == [678, 694, 713, 800]


@pytest.mark.parametrize("sobrantes", [None, []])
def test_f078_r7_sin_sobrantes_la_clave_no_va(sobrantes):
    t = _TransferCero(sobrantes)
    reg, _, _ = _registro(t)
    r = reg.preflight(2026, 7, trabajador_ides=[10, 11])
    assert t.llamadas == [("preflight_lote", True)]
    assert "sobrantes" not in r


@pytest.mark.parametrize(("obra", "lineas"), [(694, [4]), (678, [1, 2])])
def test_f078_r7_con_obra_solo_esa_del_paquete_y_sin_sobrantes(obra, lineas):
    t = _TransferCero([SOBRANTE])
    reg, _, _ = _registro(t)
    r = reg.preflight(2026, 7, trabajador_ides=[10, 11], obra_ide=obra)
    assert t.llamadas == [("preflight_lote", False)]
    assert "sobrantes" not in r
    [p] = t.payloads
    assert p["obra"]["ide"] == obra
    assert [ln["registro_id"] for ln in p["lineas"]] == lineas


def test_f078_r7_con_obra_que_no_es_del_paquete_nada():
    """La 700 es solo del 12: con el paquete del 10 y el 11, ni se pide."""
    t = _TransferCero([SOBRANTE])
    reg, _, _ = _registro(t)
    r = reg.preflight(2026, 7, trabajador_ides=[10, 11], obra_ide=700)
    assert t.llamadas == [] and r["obras"] == []
    assert "incidencias_quitadas" not in r


# ------------------------------- R8 ------------------------------------ #
def test_f078_r8_ejecutar_pone_a_cero_y_luego_las_del_paquete():
    t = _TransferCero()
    reg, _, _ = _registro(t)
    r = reg.ejecutar(2026, 7, pisar_claves=["k"], trabajador_ides=[10, 11],
                     sobrantes_a_cero=[SOBRANTE])
    assert t.llamadas == [
        ("poner_a_cero", 1, 2026, 7, [{
            "hmores_ide": 7001, "recurso_ide": 201, "hora": "MENC",
            "vinculado": None, "can": 0.3, "synckey": None}]),
        ("ejecutar", 678), ("ejecutar", 694), ("ejecutar", 713),
        ("ejecutar", 800)]
    assert r["sobrantes_a_cero"] == {"puestas": [{"hmores_ide": 7001}],
                                     "omitidas": []}
    assert all(p["pisar_claves"] == ["k"] and p["usuario"] == "local"
               for p in t.payloads)


def test_f078_r8_ejecutar_sin_sobrantes_solo_las_del_paquete():
    t = _TransferCero()
    reg, _, _ = _registro(t)
    r = reg.ejecutar(2026, 7, pisar_claves=[], trabajador_ides=[12])
    assert t.llamadas == [("ejecutar", 678), ("ejecutar", 700)]
    assert "sobrantes_a_cero" not in r
    assert [o["obra"]["ide"] for o in r["obras"]] == [678, 700]


def test_f078_r8_ejecutar_traza_lo_que_vuelve():
    """La traza de hoy (F-054 R35): lo escrito se anota en su asignación."""
    class _TransferEscribe(_TransferCero):
        def ejecutar(self, payload):
            super().ejecutar(payload)
            return {"ok": True, "escritas": [
                {"registro_id": ln["registro_id"], "parte_cod": "PT",
                 "hmores_ide": 5000 + ln["registro_id"]}
                for ln in payload["lineas"]]}

    t = _TransferEscribe()
    reg, _, anotado = _registro(t)
    reg.ejecutar(2026, 7, pisar_claves=[], trabajador_ides=[11])
    escritas = sorted(u["sigrid_hmores_ide"] for u in anotado["updates"]
                      if "sigrid_hmores_ide" in u
                      and u.get("sigrid_estado") == "registrado")
    assert escritas == [5002, 5007]


# ------------------------------- R24 ----------------------------------- #
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r24_obra_compartida_sin_nada_de_los_de_fuera(fase):
    """La 678 tiene al 10, al 11, al 12 y al 20: con el paquete del 10 y el
    12, su petición no lleva ni línea, ni incidencia, ni quitada, ni
    incidencia del mes del 11 ni del 20 (el transfer no los ve: no los pisa,
    no los pone a 0 ni los cuenta como sobrantes)."""
    reg, transfer, _ = _registro()
    _llamar(reg, fase, trabajador_ides=[10, 12])
    p678 = next(p for p in transfer.payloads if p["obra"]["ide"] == 678)
    recursos = {x["recurso_ide"] for clave in (
        "lineas", "incidencias", "quitadas", "incidencias_mes")
        for x in p678.get(clave, [])}
    assert recursos == {10, 12}
    assert [ln["registro_id"] for ln in p678["lineas"]] == [1, 3]
    assert [i["id"] for i in p678["incidencias"]] == [7, 6]
    assert p678["cierres_recursos"] == [10, 12]
    todos = {x["recurso_ide"] for p in transfer.payloads for clave in (
        "lineas", "incidencias", "quitadas", "incidencias_mes")
        for x in p.get(clave, [])}
    assert todos == {10, 12}


# ------------------------------- R23 ----------------------------------- #
@pytest.mark.parametrize("fase", RUTAS)
def test_f078_r23_sin_bloqueo_ni_aviso_por_el_100(fase):
    """D6: el 10 en FALTA (40 %) y el 11 en EXCESO (70 + 50 %) van como
    cualquier otro, y la respuesta no trae ninguna clave nueva."""
    filas = [_asig(1, (10, 1), (678, 1), porcentaje=40),
             _asig(2, (11, 1), (678, 1), porcentaje=70),
             _asig(3, (11, 1), (694, 1), porcentaje=50)]
    reg, transfer, _ = _registro(filas=filas, incs=[])
    r = _llamar(reg, fase, trabajador_ides=[10, 11])
    assert set(r) == {"ok", "obras", "no_vigentes"}
    assert [[(ln["registro_id"], ln["porcentaje"]) for ln in p["lineas"]]
            for p in transfer.payloads] == [[(1, 0.4), (2, 0.7)], [(3, 0.5)]]
    assert all(set(o) <= {"obra", "ok"} for o in r["obras"])


# ------------------------------- R25 ----------------------------------- #
def _doc(nombre: str) -> str:
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[3]
    return " ".join((raiz / "docs" / nombre).read_text(encoding="utf-8")
                    .split())


def test_f078_r25_architecture_describe_el_paquete():
    doc = _doc("ARCHITECTURE.md")
    assert "de un paquete con `trabajador_ides`, F-078" in doc
    assert ("El preflight del periodo, de un trabajador o de un paquete "
            "(`trabajador_ides`, F-078") in doc
    assert "el botón general del front registra siempre el paquete" in doc
    assert "el botón general del front ya no pide el mes entero" in doc
    assert "Desde F-078 el botón general registra un **paquete**" in doc


def test_f078_r25_integracion_describe_la_validacion():
    doc = _doc("INTEGRACION.md")
    assert "Desde F-078, las dos rutas admiten además `trabajador_ides`" in doc
    for trozo in ("lista **no vacía** de enteros", "sin repetidos",
                  "la lista junto a un `trabajador_ide` no nulo son **422**",
                  "No tiene tope"):
        assert trozo in doc, trozo
