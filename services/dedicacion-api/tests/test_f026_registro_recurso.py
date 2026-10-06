# tests/test_f026_registro_recurso.py
"""Tests offline de F-026: la API manda el RECURSO y solo los vigentes.

Trazabilidad con `specs/F-026-recursos-sin-ficha-empleado/requirements.md`:
R16 (las líneas de un trabajador no vigente en el mes no se mandan ni se
trazan; sus `registro_id` salen en `no_vigentes`) y R18 (cada línea lleva
`recurso_ide` = `trabajador.ide`, sin `empleado_ide`).

Dobles de F-024 (`test_f024_registro_empresa.py`): sesión falsa que devuelve
tuplas fijas y anota cada UPDATE de la traza, y transfer falso que captura
el payload. Ni red, ni BBDD, ni `registro/ejecutar` real.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from application.registro_sigrid import RegistroSigrid

from tests.test_f024_registro_empresa import _Sesion, _Transfer

#: Periodo de las pruebas: octubre de 2026.
ANIO, MES = 2026, 10


def _fila(asig_id: int, trab_ide: int, obra_ide: int, *,
          activo: bool = True, fecha_baja: int | None = None,
          empresa: int | None = 1) -> tuple:
    """(asignación, trabajador, obra) como las devuelve la consulta."""
    asignacion = SimpleNamespace(id=asig_id, porcentaje=50, es_postventa=False)
    trabajador = SimpleNamespace(ide=trab_ide, dni=None, nombre=f"T{trab_ide}",
                                 categoria="Encargado", empresa=empresa,
                                 activo=activo, fecha_baja=fecha_baja)
    # F-039: sin obra ni partida de registro (no es una entrada VAR).
    obra = SimpleNamespace(ide=obra_ide, cod=f"0{obra_ide}",
                           descripcion="OBRA", empresa=1,
                           registro_obra_ide=None, registro_obra_cod=None,
                           registro_paride=None)
    return asignacion, trabajador, obra


#: 772 sin baja (Eusebio); 10 con baja en octubre; 11 con baja en
#: septiembre; 12 desactivado por el sync; 13 con baja en septiembre pero de
#: otra empresa (no visible en la 1).
FILAS = [
    _fila(1, 772, 678),
    _fila(2, 10, 678, fecha_baja=20261015),
    _fila(3, 11, 678, fecha_baja=20260915),
    _fila(4, 11, 713, fecha_baja=20260915),
    _fila(5, 12, 713, activo=False),
    _fila(6, 772, 713),
    _fila(7, 13, 678, fecha_baja=20260915, empresa=18),
]


def _registro(transfer: _Transfer, filas: list[tuple] = FILAS,
              updates: list[dict] | None = None) -> RegistroSigrid:
    anotadas = updates if updates is not None else []
    return RegistroSigrid(lambda: _Sesion(filas, anotadas), transfer, 1)


def _llamar(registro: RegistroSigrid, fase: str, **kwargs: Any) -> dict:
    if fase == "preflight":
        return registro.preflight(ANIO, MES, empresa=1, **kwargs)
    return registro.ejecutar(ANIO, MES, pisar_claves=[], empresa=1, **kwargs)


def _lineas(transfer: _Transfer) -> list[dict]:
    return [lin for p in transfer.payloads for lin in p["lineas"]]


# --- R18: la línea lleva el recurso ------------------------------------------


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f026_r18_cada_linea_lleva_recurso_ide_y_no_empleado_ide(fase):
    transfer = _Transfer()
    _llamar(_registro(transfer), fase)
    lineas = _lineas(transfer)
    assert sorted((lin["registro_id"], lin["recurso_ide"]) for lin in lineas) \
        == [(1, 772), (2, 10), (6, 772)]
    assert all("empleado_ide" not in lin for lin in lineas)


# --- R16: no vigentes en el mes ----------------------------------------------


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f026_r16_no_vigentes_no_se_mandan_y_se_listan(fase):
    transfer = _Transfer()
    r = _llamar(_registro(transfer), fase)
    assert sorted(lin["registro_id"] for lin in _lineas(transfer)) == [1, 2, 6]
    assert r["no_vigentes"] == [3, 4, 5]
    assert r["ok"] is True


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f026_r16_la_baja_en_el_mes_se_manda(fase):
    transfer = _Transfer()
    r = _llamar(_registro(transfer, [_fila(2, 10, 678, fecha_baja=20261001)]),
                fase)
    assert [lin["registro_id"] for lin in _lineas(transfer)] == [2]
    assert r["no_vigentes"] == []


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f026_r16_solo_no_vigentes_no_llama_al_transfer(fase):
    transfer = _Transfer()
    r = _llamar(_registro(transfer, [_fila(3, 11, 678, fecha_baja=20260930)]),
                fase, trabajador_ide=11)
    assert r == {"ok": True, "obras": [], "no_vigentes": [3]}
    assert transfer.payloads == []


class _TransferEco(_Transfer):
    """Contesta omitiendo, con motivo, cada línea que recibe."""

    def ejecutar(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"ok": True, "escritas": [], "ya_registradas": [],
                "omitidas": [{"registro_id": lin["registro_id"],
                              "motivo": "omitida"}
                             for lin in payload["lineas"]]}


def test_f026_r16_ejecutar_no_traza_a_los_no_vigentes():
    """Un `omitido` pisaría la traza `registrado` de una asignación ya
    escrita: las de los no vigentes no se tocan."""
    transfer = _TransferEco()
    updates: list[dict] = []
    r = _registro(transfer, updates=updates).ejecutar(ANIO, MES,
                                                      pisar_claves=[],
                                                      empresa=1)
    assert r["no_vigentes"] == [3, 4, 5]
    trazadas = {u["id_1"] for u in updates if "id_1" in u}
    assert trazadas == {1, 2, 6}


def test_f026_r16_la_vigencia_es_la_del_mes_pedido():
    """La baja de octubre es vigente en octubre y no en noviembre."""
    filas = [_fila(2, 10, 678, fecha_baja=20261015)]
    octubre, noviembre = _Transfer(), _Transfer()
    r_oct = _registro(octubre, filas).preflight(2026, 10, empresa=1)
    r_nov = _registro(noviembre, filas).preflight(2026, 11, empresa=1)
    assert (r_oct["no_vigentes"], r_nov["no_vigentes"]) == ([], [2])
    assert len(_lineas(octubre)) == 1 and _lineas(noviembre) == []
