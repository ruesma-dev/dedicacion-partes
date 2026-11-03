# tests/test_f054_mutacion.py
"""F-054 · T17: lo que la campaña de mutación de la api dejó vivo
(`progress/mutacion_F-054.md`). Cada test nombra el mutante que mata.

- Los modelos de F-054 son inmutables (`frozen`) y sus valores por defecto
  son los del contrato del transfer (lo que falta en la respuesta).
- La obra de la base que no se ofrece tampoco se ofrece en postventa.
- Un `aceptar` sin `es_postventa` es normal (llamada directa al caso de uso).
- Una línea sin partida y otra con partida, en la misma obra normal, son
  partidas distintas (R15).
- El preflight del lote, si no se dice, no es completo.
- `sobrantes_a_cero`: lo que no es una lista de objetos con `hmores_ide`
  entero es 422; topes y defectos de los esquemas; el cliente con respuestas
  incompletas; la relectura del periodo.

Sin red ni BBDD: los dobles de `test_f054_aceptar.py`,
`test_f054_comparar.py` y `test_f054_registro_cero.py`.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal
from types import SimpleNamespace

import pytest
from application.traer_sigrid import ResultadoTraer, TrabajadorTraido
from domain.errors import LineasInvalidas
from domain.models import LineaSigridTraida, ResultadoExistentes
from domain.traer_sigrid import (
    MOTIVO_PARTIDAS_DISTINTAS,
    Comparada,
    Contadores,
    EntradaSigrid,
    NoTraida,
)
from infrastructure.db.repositories import PgPeriodoRepository
from interface_adapters.api.routes import _sobrantes_a_cero
from interface_adapters.api.schemas import TraerSigridIn, TraerSigridOut
from pydantic import ValidationError

from tests.test_f054_aceptar import _acepta, _datos, _Gateway, _s, _traer, _Uow
from tests.test_f054_comparar import _entradas
from tests.test_f054_comparar import _s as _sc
from tests.test_f054_registro_cero import _cliente as _cliente_cero
from tests.test_f054_registro_cero import _registro, _TransferCero
from tests.test_f054_rutas import RESPUESTA, RUTA, _app
from tests.test_f054_rutas import _cliente as _cliente_existentes


@pytest.mark.parametrize("clase", [
    LineaSigridTraida, ResultadoExistentes, EntradaSigrid, NoTraida,
    Contadores, Comparada, TrabajadorTraido, ResultadoTraer])
def test_f054_t17_los_modelos_son_inmutables(clase):
    assert dataclasses.is_dataclass(clase)
    assert clase.__dataclass_params__.frozen is True


def _defectos(clase) -> dict:
    return {f.name: f.default for f in dataclasses.fields(clase)
            if f.default is not dataclasses.MISSING}


def test_f054_t17_valores_por_defecto_de_la_linea_traida():
    assert _defectos(LineaSigridTraida) == {
        "obra_cod": None, "parte_ide": None, "parte_cod": None,
        "parte_est": None, "en_registro": False, "hora": None, "can": 0.0,
        "fec": None, "paride": 0, "partida_cod": None, "partida_res": None,
        "synckey": None, "destino": "normal", "obra_origen_ide": None,
        "var_paride": None, "motivo": None}


def test_f054_t17_valores_por_defecto_del_resultado_y_la_entrada():
    assert _defectos(ResultadoExistentes) == {
        "lineas_leidas": 0, "excluidas_pruebas": 0, "motivo_postventa": None,
        "motivo_var": None, "lineas": ()}
    assert _defectos(Contadores) == {"fuera_maestro": 0, "de_vinculados": 0}
    assert _defectos(EntradaSigrid) == {
        "partida_ide": None, "partida_cod": None, "partida_res": None,
        "hmores_ide": 0, "parte_cod": None, "n_lineas": 0, "motivo": None,
        "destino": "normal"}


def test_f054_r14_obra_en_la_base_sin_ofrecerse_tampoco_en_postventa():
    """Mata `admite_postventa=True` en la obra que se completa desde la
    base (application/traer_sigrid.py, `_obras`)."""
    class _UowStub(_Uow):
        def __init__(self, d):
            super().__init__(d)
            self.obras.codigos = lambda ides: {
                i: "0708" for i in set(ides) & {555}}

    g = _Gateway([_s(980, 20, 555, 0.3, destino="postventa",
                     obra_origen_ide=555)])
    d = _datos()
    r, _, _ = _traer(d, [], g, uow=_UowStub(d))
    assert [(n.hmores_ide, n.motivo) for n in r.no_traidas] == [
        (980, "la obra 0708 no se ofrece en postventa")]


def test_f054_r19_aceptar_sin_es_postventa_es_la_normal():
    """Mata el `True` por defecto de `item.get("es_postventa", …)`."""
    d = _datos()
    r, _, _ = _traer(d, [{"trabajador_ide": 10, "obra_ide": 713}])
    assert r.tocados == [10]
    assert {(f["linea"].obra_ide, f["linea"].es_postventa)
            for f in d.filas[10]} >= {(713, False)}
    assert _acepta(10, 713) == {"trabajador_ide": 10, "obra_ide": 713,
                                "es_postventa": False}


def test_f054_r15_sin_partida_y_con_partida_son_partidas_distintas():
    """Mata `l.paride or 1`: la partida 0 (sin partida) y la 1 no casan."""
    por, _, _ = _entradas([_sc(1, paride=0), _sc(2, paride=1)])
    [e] = por[10]
    assert e.motivo == MOTIVO_PARTIDAS_DISTINTAS
    assert e.porcentaje == Decimal("100.00")


def test_f054_r31_el_lote_sin_decir_nada_no_es_completo():
    """Mata `completo: bool = True` en `RegistroSigrid._preflight_lote`."""
    t = _TransferCero([{"clave": "cero:1"}])
    _, sobrantes = _registro(t)._preflight_lote(
        [{"obra": {"ide": 678}}])
    assert t.llamadas == [("preflight_lote", False)]
    assert sobrantes == []


# ---------------------- validación de `sobrantes_a_cero` ------------------- #
@pytest.mark.parametrize("valor", [
    "x", 7, {"hmores_ide": 1},                  # no es una lista
    [7], ["cero:1"],                            # no son objetos
    [{}], [{"hmores_ide": "1"}], [{"hmores_ide": None}],   # sin `ide` entero
    [{"hmores_ide": True}], [{"hmores_ide": False}],       # un bool no vale
    [{"hmores_ide": 1}, {"hmores_ide": "2"}],   # basta con que una falle
])
def test_f054_r35_sobrantes_a_cero_invalidas_422(valor):
    with pytest.raises(LineasInvalidas):
        _sobrantes_a_cero(valor)


@pytest.mark.parametrize("valor, sale", [
    (None, None), ([], []), ([{"hmores_ide": 1, "can": 0.2}],
                             [{"hmores_ide": 1, "can": 0.2}])])
def test_f054_r35_sobrantes_a_cero_validas(valor, sale):
    assert _sobrantes_a_cero(valor) == sale


# ------------------------------ esquemas y cliente ------------------------- #
def test_f054_r19_aceptar_como_mucho_5000():
    item = {"trabajador_ide": 1, "obra_ide": 2}
    assert len(TraerSigridIn(aceptar=[item] * 5000).aceptar) == 5000
    with pytest.raises(ValidationError):
        TraerSigridIn(aceptar=[item] * 5001)


def test_f054_r26_propuestas_en_curso_por_defecto_false():
    assert TraerSigridOut.model_fields["propuestas_en_curso"].default is False


def test_f054_r27_la_entrada_solo_cuadrante_no_suma_lineas(monkeypatch):
    cli, _, _, _ = _app(monkeypatch)
    j = cli.post(RUTA, json={"aceptar": []}).json()
    ana = next(t for t in j["trabajadores"] if t["trabajador_ide"] == 10)
    [e] = [x for x in ana["entradas"] if x["estado"] == "solo_cuadrante"]
    assert e["n_lineas"] == 0


@pytest.mark.parametrize("campo", ["lineas_leidas", "excluidas_pruebas"])
def test_f054_r27_cliente_sin_el_contador_es_0(monkeypatch, campo):
    respuesta = {k: v for k, v in RESPUESTA.items() if k != campo}
    cli, _ = _cliente_existentes(monkeypatch, respuesta)
    assert getattr(cli.porcentajes_existentes(1, 2026, 9, []), campo) == 0


def test_f054_r35_cliente_el_error_es_el_del_transfer(monkeypatch):
    """Mata `r.get('error') and r` por los dos lados."""
    cli, _ = _cliente_cero(monkeypatch, {"ok": False, "error": "truncada"})
    with pytest.raises(RuntimeError, match=r"sobrantes: truncada$"):
        cli.poner_a_cero(1, 2026, 10, [{"hmores_ide": 1}])
    cli, _ = _cliente_cero(monkeypatch, {"ok": False})
    with pytest.raises(RuntimeError, match=r"sobrantes: \{'ok': False\}$"):
        cli.poner_a_cero(1, 2026, 10, [{"hmores_ide": 1}])


def test_f054_r22_el_periodo_se_relee_de_la_base():
    """Mata `populate_existing=False`: sin él no se vería el cierre hecho
    entre medias (la sentencia, sin BBDD)."""
    vistas = []

    class _Sesion:
        def scalars(self, stmt):
            vistas.append(stmt)
            return SimpleNamespace(first=lambda: None)

    assert PgPeriodoRepository(_Sesion()).obtener(2026, 9) is None
    [stmt] = vistas
    assert stmt.get_execution_options()["populate_existing"] is True
