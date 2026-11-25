# tests/test_f080_reglas_caja.py
"""F-080 · T2: regresión del transfer con la caja POR % (R6-R8; design §2,
§8). Sin código nuevo: es el de F-069 para cualquier tipo `pct` en `eur`.

- R6 (D4): caja del mes > 0 ⇒ en CADA línea del titular (obra normal,
  postventa y VAR) una línea de caja con su hora por defecto (`CO`), `can`
  = el del titular (sin normalizar), `pre` = la caja del mes y `tot =
  round(can × pre, 2)`: 300 € al 60 % y al 40 % ⇒ 180 y 120.
- R7 (D5): sin ajuste de céntimos: 100 € al 33,33 % × 3 ⇒ 99,99; un total
  por debajo del 100 % reparte menos de lo tecleado.
- R8: nula ⇒ «falta el importe del mes» (sin obra); 0 ⇒ «importe 0»;
  copiada sin revisar ⇒ «sin revisar» sin «en la obra». Los motivos de la
  caja por obra no salen.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from application.services.reglas_vinculados import (
    MOTIVO_CAJA_CERO,
    MOTIVO_FALTA_CAJA,
    MOTIVO_FALTA_IMPORTE,
    MOTIVO_IMPORTE_CERO,
    MOTIVO_SIN_REVISAR,
    PartidaTitular,
    decidir_vinculados,
    va_con_el_titular,
)

from tests.test_f069_reglas_importe import HORAS, _caja, _linea, _titular


def _caja_pct(**kw):
    """La caja como la manda la api tras F-080: `reparto: pct`."""
    return _caja(reparto="pct", cantidad=300.0, **kw)


def _en(v, **titular):
    [av] = decidir_vinculados(_titular(**titular), _linea(v), HORAS,
                              obra="0678")
    return av


# ================================ R6 ===================================== #
def test_f080_r6_300_al_60_y_al_40_en_postventa_da_180_y_120():
    obra = _en(_caja_pct(), can=0.6)
    postventa = _en(_caja_pct(), can=0.4, destino="postventa",
                    es_postventa=True)
    for av, can, tot, destino in ((obra, 0.6, 180.0, "obra"),
                                  (postventa, 0.4, 120.0, "postventa")):
        assert (av.accion, av.hora_ide, av.hora_codigo) == (
            "escribir", 43, "CO")
        assert (av.can, av.pre, av.tot) == (can, 300.0, tot)
        assert (av.reparto, av.km, av.precio_km) == ("pct", None, None)
        assert av.destino == destino
    assert obra.tot + postventa.tot == 300.0


def test_f080_r6_tambien_en_la_entrada_var_con_la_partida_del_titular():
    av = _en(_caja_pct(), can=0.25, partida_metodo="var")
    assert (av.accion, av.can, av.pre, av.tot) == ("escribir", 0.25, 300.0,
                                                   75.0)
    assert va_con_el_titular(PartidaTitular(destino="obra", paride=80001,
                                            cod="CI.1.10", metodo="var"))
    assert va_con_el_titular(PartidaTitular(destino="postventa", paride=0))


def test_f080_r6_el_can_es_el_del_titular_sin_normalizar():
    av = _en(_caja_pct(), can=0.45)
    assert (av.can, av.pre, av.tot) == (0.45, 300.0, 135.0)   # no 300 × 1


# ================================ R7 ===================================== #
def test_f080_r7_sin_ajuste_de_centimos_33_33_por_tres_da_99_99():
    tots = [_en(_caja(reparto="pct", cantidad=100.0), can=0.3333).tot
            for _ in range(3)]
    assert tots == [33.33, 33.33, 33.33]
    assert round(sum(tots), 2) == 99.99


def test_f080_r7_por_debajo_del_100_reparte_menos():
    tots = [_en(_caja_pct(), can=c).tot for c in (0.5, 0.3)]
    assert tots == [150.0, 90.0] and sum(tots) == 240.0


# ================================ R8 ===================================== #
def test_f080_r8_nula_falta_el_importe_sin_obra():
    av = _en(_caja(reparto="pct", cantidad=None))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_FALTA_IMPORTE.format(tipo="CAJA",
                                                    cod="CA0022")
    assert "0678" not in av.motivo


def test_f080_r8_cero_importe_0():
    av = _en(_caja(reparto="pct", cantidad=0.0))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_IMPORTE_CERO.format(tipo="CAJA", cod="CA0022")


def test_f080_r8_copiada_sin_revisar_sin_en_la_obra():
    av = _en(_caja_pct(copiado=True))
    assert av.accion == "omitir"
    assert av.motivo == MOTIVO_SIN_REVISAR.format(tipo="CAJA", cod="CA0022",
                                                  donde="")
    assert "en la obra" not in av.motivo


@pytest.mark.parametrize("cantidad", [None, 0.0])
def test_f080_r8_los_motivos_de_la_caja_por_obra_no_salen(cantidad):
    av = _en(_caja(reparto="pct", cantidad=cantidad))
    obra = dict(tipo="CAJA", cod="CA0022", obra="0678")
    assert av.motivo not in (MOTIVO_FALTA_CAJA.format(**obra),
                             MOTIVO_CAJA_CERO.format(**obra))
    assert "en la obra" not in av.motivo
    assert not av.motivo.startswith(("falta la caja", "caja 0"))
