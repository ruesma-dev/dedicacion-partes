# tests/test_f051_modal_pisado.py
"""F-051 · El modal del pisado dice qué línea se EDITA y cuáles quedan a 0
(R6): ya no se borra ninguna. El detalle termina como antes, en «se escribe
N%» (opción B del humano, 2026-10-20: los tests de F-049 R2 lo miran).

El transfer publica en cada conflicto de pisado `edita_ide` (el choque de
menor `ide`, el que se edita en su sitio) y `a_cero_ides` (los demás, que
se ponen a 0). `rotuloConflicto` solo lo formatea: no decide nada. Código
real de `app.js` en node (ayudantes de `test_f049_avisos_registro.py`); sin
`node` se saltan con su motivo. Sin red ni BBDD.
"""
from __future__ import annotations

from tests.test_f049_avisos_registro import (
    JS,
    PISADO,
    SIN_PARTIDA,
    SOBRECARGA,
    _funcion,
    _linea,
    _rotulos,
)

TRES = PISADO | {"lineas": [_linea(8001, 0.4),
                            _linea(8002, 0.25, fecha=20260915),
                            _linea(8003, 0.1, hora="MADM", fecha=20260901)],
                 "edita_ide": 8001, "a_cero_ides": [8002, 8003]}


def test_f051_r6_un_choque_se_edita_y_se_escribe_el_nuevo():
    [r] = _rotulos([PISADO | {"lineas": [_linea(8001, 0.4)],
                              "edita_ide": 8001, "a_cero_ides": []}])
    assert r == {
        "tipo": "pisado", "titulo": "Pisar",
        "detalle": ("MADM de GONZALEZ PANIAGUA en el parte PT26/00319: se "
                    "edita la línea 8001 (MADM 40%, fec 20260930) y se "
                    "escribe 60%")}


def test_f051_r6_varios_choques_dice_cuales_quedan_a_cero():
    [r] = _rotulos([TRES])
    assert r["detalle"] == (
        "MADM de GONZALEZ PANIAGUA en el parte PT26/00319: se edita la "
        "línea 8001 (MADM 40%, fec 20260930); quedan a 0: línea 8002 (MADM "
        "25%, fec 20260915), línea 8003 (MADM 10%, fec 20260901) y se "
        "escribe 60%")


def test_f051_r6_edita_el_que_dice_el_transfer_no_el_primero():
    [r] = _rotulos([TRES | {"edita_ide": 8003, "a_cero_ides": [8001, 8002]}])
    assert "se edita la línea 8003 (MADM 10%" in r["detalle"]
    assert "quedan a 0: línea 8001 (MADM 40%" in r["detalle"]


def test_f051_r6_sin_edita_ide_el_de_menor_ide():
    """Un transfer anterior a F-051 no publica `edita_ide`: se nombra el de
    menor `ide`, que es el que editaría uno nuevo, sin inventar ninguno."""
    [r] = _rotulos([PISADO | {"lineas": [_linea(8002, 0.25),
                                         _linea(8001, 0.4)]}])
    assert "se edita la línea 8001 (MADM 40%" in r["detalle"]
    assert "quedan a 0" not in r["detalle"]
    assert r["detalle"].endswith("y se escribe 60%")


def test_f051_r6_ni_se_borran_ni_borra_en_ningun_detalle():
    rotulos = _rotulos([PISADO, TRES, SIN_PARTIDA, SOBRECARGA,
                        PISADO | {"motivo": None}])
    for r in rotulos:
        assert "borr" not in r["detalle"].lower(), r
    assert "borr" not in _funcion("rotuloConflicto").lower()
    assert "se borran" not in JS
