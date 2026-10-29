# tests/test_f044_vinculo.py
"""F-044 · T1: el vínculo de un recurso no persona con su trabajador.

- R2: el vinculado es del trabajador cuyo `ide` es el valor del campo
  «Recurso Asociado»; un trabajador tiene TODOS sus vinculados; una sola
  función pura (`domain.vinculados.vincular`), determinista.
- R3 (D1b): campo vacío, hacia un recurso que no es trabajador de
  dedicación o de un tipo de `tipos_excluidos` ⇒ sin vínculo y contado, con
  sus códigos (sin nombres). No se casa por nombre.
- R4: el vinculado cuenta en el mes con `vigente_en` sobre su propia baja.

Sin red ni BBDD.
"""
from __future__ import annotations

import random

import pytest
from domain.models import RecursoVinculado
from domain.vinculados import (
    ESTADO_NO_TRABAJADOR,
    ESTADO_SIN_CAMPO,
    ESTADO_VINCULADO,
    ResultadoVinculos,
    codigos,
    vigentes,
    vincular,
)

TRABAJADORES = {1705036, 1705040}
EXCLUIDOS = {"VP"}


def _v(ide: int, principal: int | None, tipo: str = "TF",
       cod: str | None = None, fecha_baja: int | None = None,
       descripcion: str | None = None) -> RecursoVinculado:
    return RecursoVinculado(
        ide=ide, principal_ide=principal, cod=cod or f"R{ide}",
        descripcion=descripcion, empresa=1, fecha_baja=fecha_baja,
        tipo=tipo, tipo_res=f"TIPO {tipo}", horide=900 + ide % 10)


# ================================ R2 ===================================== #
def test_f044_r2_el_valor_del_campo_es_el_trabajador():
    r = vincular([_v(10, 1705036)], TRABAJADORES, EXCLUIDOS)
    assert [(v.ide, t) for v, t in r.vinculos] == [(10, 1705036)]
    assert (r.sin_campo, r.hacia_no_trabajador, r.excluidos) == ((), (), ())


def test_f044_r2_un_trabajador_tiene_todos_sus_vinculados():
    """Dos del mismo tipo y uno de otro: los tres son suyos."""
    r = vincular([_v(12, 1705036, "TF"), _v(11, 1705036, "TF"),
                  _v(13, 1705036, "CO"), _v(14, 1705040, "VE")],
                 TRABAJADORES, EXCLUIDOS)
    assert {t: [v.ide for v in vs]
            for t, vs in r.por_trabajador().items()} == {
        1705036: [11, 12, 13], 1705040: [14]}


def test_f044_r2_entrada_barajada_mismo_resultado():
    base = [_v(i, 1705036 if i % 3 else None,
               "VP" if i % 7 == 0 else "TF") for i in range(1, 40)]
    base += [_v(100 + i, 999) for i in range(5)]
    esperado = vincular(base, TRABAJADORES, EXCLUIDOS)
    for semilla in range(5):
        barajada = list(base)
        random.Random(semilla).shuffle(barajada)
        assert vincular(barajada, TRABAJADORES, EXCLUIDOS) == esperado


def test_f044_r2_no_se_casa_por_nombre():
    """La descripción con el nombre de otro trabajador no cuenta: manda el
    campo."""
    r = vincular([_v(10, 1705040, descripcion="CONSUMOS TELEFONO 1705036")],
                 TRABAJADORES, EXCLUIDOS)
    assert [(v.ide, t) for v, t in r.vinculos] == [(10, 1705040)]


def test_f044_r2_resultado_inmutable_y_ordenado_por_ide():
    r = vincular([_v(30, 1705036), _v(20, 1705040)], TRABAJADORES,
                 EXCLUIDOS)
    assert isinstance(r, ResultadoVinculos)
    assert [v.ide for v, _ in r.vinculos] == [20, 30]
    with pytest.raises(AttributeError):
        r.vinculos = ()  # type: ignore[misc]


# ================================ R3 ===================================== #
@pytest.mark.parametrize("principal", [None, 0])
def test_f044_r3_campo_vacio_no_vincula_y_cuenta(principal):
    r = vincular([_v(10, principal, cod="TF-10")], TRABAJADORES, EXCLUIDOS)
    assert r.vinculos == ()
    assert codigos(r.sin_campo) == ["TF-10"]
    assert r.estado(10) == ESTADO_SIN_CAMPO


def test_f044_r3_hacia_un_no_trabajador_no_vincula_y_cuenta():
    r = vincular([_v(10, 555, cod="TF-10")], TRABAJADORES, EXCLUIDOS)
    assert r.vinculos == ()
    assert codigos(r.hacia_no_trabajador) == ["TF-10"]
    assert r.estado(10) == ESTADO_NO_TRABAJADOR


@pytest.mark.parametrize("tipo", ["VP", " vp ", "Vp"])
def test_f044_r3_tipo_excluido_no_vincula_y_cuenta(tipo):
    """D1b: un `VP` (kilómetros) se queda fuera aunque apunte a un
    trabajador; el tipo se compara sin espacios y sin mayúsculas."""
    r = vincular([_v(10, 1705036, tipo=tipo, cod="VP-10")], TRABAJADORES,
                 EXCLUIDOS)
    assert r.vinculos == ()
    assert codigos(r.excluidos) == ["VP-10"]
    assert r.estado(10) is None


def test_f044_r3_el_excluido_se_mira_antes_que_el_campo():
    r = vincular([_v(10, None, tipo="VP"), _v(11, 555, tipo="VP")],
                 TRABAJADORES, EXCLUIDOS)
    assert [v.ide for v in r.excluidos] == [10, 11]
    assert (r.sin_campo, r.hacia_no_trabajador) == ((), ())


def test_f044_r3_codigos_ordenados_sin_nombres():
    r = vincular([_v(12, None, cod="TF-B", descripcion="TELEFONO PEPE"),
                  _v(11, None, cod="TF-A", descripcion="TELEFONO ANA"),
                  _v(13, None, cod=None)], TRABAJADORES, EXCLUIDOS)
    assert codigos(r.sin_campo) == ["R13", "TF-A", "TF-B"]


def test_f044_r3_estado_del_vinculado():
    r = vincular([_v(10, 1705036)], TRABAJADORES, EXCLUIDOS)
    assert r.estado(10) == ESTADO_VINCULADO
    assert r.estado(99) is None


def test_f044_r3_sin_excluidos_todo_tipo_vale():
    """D1: cualquier tipo vinculado al principal (también `VP` si no está
    en la lista)."""
    r = vincular([_v(10, 1705036, tipo="VP"), _v(11, 1705036, tipo="CAJA")],
                 TRABAJADORES, set())
    assert [v.ide for v, _ in r.vinculos] == [10, 11]


# ================================ R4 ===================================== #
@pytest.mark.parametrize("fecha_baja, vigente", [
    (None, True), (0, True), (20261001, True), (20261015, True),
    (20260930, False), (20260101, False)])
def test_f044_r4_vigencia_por_su_propia_baja(fecha_baja, vigente):
    v = _v(10, 1705036, fecha_baja=fecha_baja)
    assert (vigentes([v], 2026, 10) == [v]) is vigente


def test_f044_r4_vigentes_conserva_el_orden():
    vs = [_v(3, 1), _v(1, 1, fecha_baja=20250101), _v(2, 1)]
    assert [v.ide for v in vigentes(vs, 2026, 10)] == [3, 2]
