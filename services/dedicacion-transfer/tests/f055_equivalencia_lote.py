# tests/f055_equivalencia_lote.py
"""F-055 · R21: plugin de pytest que compara cada preflight suelto con el
mismo preflight en un lote de una petición.

Lo carga `test_f055_lote.py` en un pytest aparte (`-p
tests.f055_equivalencia_lote`) sobre los ficheros de escenarios de
`test_f037_pipeline`, `test_f050_pipeline`, `test_f002_pipeline` y
`test_f039_preflight_var`: cada `RegistroPipeline.preflight` que hagan sus
tests se repite con `RegistroLote` sobre una COPIA del doble tomada antes
(así sus contadores no ven la repetición) y con los logs apagados (así sus
aserciones de log tampoco), y la respuesta HTTP de los dos
(`_respuesta_preflight`) tiene que ser idéntica; si el suelto falla, el
lote tiene que fallar con la misma excepción. Al terminar escribe cuántos
comparó en el fichero de `F055_EQUIVALENCIA_SALIDA`. Igual con cada
`RegistroPipeline.proponer` (el selector) contra `RegistroLote.proponer`.

Excepción, una y con nombre (`SIN_COMPARAR`): el doble de
`test_f037_r17_solo_se_crean_partes_y_se_insertan_o_borran_lineas` da un
código distinto en cada `siguiente_cod_pt` (un iterador), y el lote lo lee
una vez por año y empresa (design §2): en Sigrid es `MAX(cod) + 1`, una
lectura pura, y en suelto da también el mismo código a los dos partes
nuevos. Lo cubre `test_f055_r21_siguiente_cod_pt_una_vez_y_lo_mismo`. Y
los `test_f050_script_propuesta_*`: la fase `propuesta` del script envuelve
los métodos del doble con cierres sobre el ORIGINAL (para cronometrarlos), así
que la copia los comparte y el lote ensuciaría sus contadores; la propuesta
que comparan es la misma `proponer` que ya comparan los tests del endpoint.

No es un fichero de tests (no empieza por `test_`): sin el `-p` no hace nada.
"""
from __future__ import annotations

import copy
import json
import logging
import os

from application.pipelines import registro_pipeline as modulo
from application.pipelines.registro_lote import RegistroLote
from application.services.lecturas_lote import LecturasDelLote
from interface_adapters.api.app import _respuesta_preflight

_ORIGINAL = modulo.RegistroPipeline.preflight
_ORIGINAL_PROPONER = modulo.RegistroPipeline.proponer
_CUENTA = {"iguales": 0, "errores_iguales": 0, "sin_comparar": 0,
           "propuestas_iguales": 0, "propuestas_error_iguales": 0}
SIN_COMPARAR = (
    "test_f037_r17_solo_se_crean_partes_y_se_insertan_o_borran_lineas",
    "test_f050_script_propuesta_")


def _en_lote(cli, settings, obra, lineas):
    logging.disable(logging.CRITICAL)
    try:
        return RegistroLote(cliente=cli, settings=settings, limite=4) \
            .preflight([(obra, lineas)])[0]
    except Exception as exc:                        # noqa: BLE001
        return exc
    finally:
        logging.disable(logging.NOTSET)


def _comparado(self, *, obra, lineas):
    if isinstance(self._cli, LecturasDelLote):
        return _ORIGINAL(self, obra=obra, lineas=lineas)
    if any(n in os.environ.get("PYTEST_CURRENT_TEST", "")
           for n in SIN_COMPARAR):
        _CUENTA["sin_comparar"] += 1
        return _ORIGINAL(self, obra=obra, lineas=lineas)
    copia = copy.deepcopy((self._cli, obra, lineas))
    try:
        suelto = _ORIGINAL(self, obra=obra, lineas=lineas)
    except Exception as exc:
        lote = _en_lote(copia[0], self._st, copia[1], copia[2])
        assert type(lote) is type(exc) and str(lote) == str(exc), (
            f"R21: el suelto falla con {exc!r} y el lote da {lote!r}")
        _CUENTA["errores_iguales"] += 1
        raise
    lote = _en_lote(copia[0], self._st, copia[1], copia[2])
    assert not isinstance(lote, Exception), (
        f"R21: el suelto va y el lote falla con {lote!r}")
    assert _respuesta_preflight(lote) == _respuesta_preflight(suelto), \
        "R21: el lote no da lo mismo que el suelto"
    _CUENTA["iguales"] += 1
    return suelto


def _propuesta_en_lote(cli, settings, peticion):
    logging.disable(logging.CRITICAL)
    try:
        lote = RegistroLote(cliente=cli, settings=settings, limite=4)
        return lote.proponer([peticion])[0]
    except Exception as exc:                        # noqa: BLE001
        return exc
    finally:
        logging.disable(logging.NOTSET)


def _proponer_comparado(self, **peticion):
    """Lo mismo para `proponer` (R34): la entrada del lote es `{ok: true,
    propuestas}` con las de la suelta, su `{ok: false, error}` o su misma
    excepción."""
    if isinstance(self._cli, LecturasDelLote):
        return _ORIGINAL_PROPONER(self, **peticion)
    if any(n in os.environ.get("PYTEST_CURRENT_TEST", "")
           for n in SIN_COMPARAR):
        _CUENTA["sin_comparar"] += 1
        return _ORIGINAL_PROPONER(self, **peticion)
    copia = copy.deepcopy((self._cli, peticion))
    try:
        suelta = _ORIGINAL_PROPONER(self, **peticion)
    except Exception as exc:
        lote = _propuesta_en_lote(copia[0], self._st, copia[1])
        assert type(lote) is type(exc) and str(lote) == str(exc), (
            f"R21: la suelta falla con {exc!r} y el lote da {lote!r}")
        _CUENTA["propuestas_error_iguales"] += 1
        raise
    lote = _propuesta_en_lote(copia[0], self._st, copia[1])
    esperado = ({"ok": True, "propuestas": suelta["propuestas"]}
                if suelta["ok"] else suelta)
    assert lote == esperado, f"R21: {lote!r} != {esperado!r}"
    _CUENTA["propuestas_iguales"] += 1
    return suelta


def pytest_configure(config) -> None:
    modulo.RegistroPipeline.preflight = _comparado
    modulo.RegistroPipeline.proponer = _proponer_comparado


def pytest_unconfigure(config) -> None:
    modulo.RegistroPipeline.preflight = _ORIGINAL
    modulo.RegistroPipeline.proponer = _ORIGINAL_PROPONER
    salida = os.environ.get("F055_EQUIVALENCIA_SALIDA")
    if salida:
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(_CUENTA, f)
