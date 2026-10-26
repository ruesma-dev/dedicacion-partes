# tests/test_f062_punta_a_punta.py
"""F-062 · las rachas de punta a punta, mitad de la api (design §3, como
F-030 §13.6).

Cada escenario de `tests/contratos/f062_rachas.json` encadena sus pasos
sobre el código REAL de la api y una sesión en memoria:

  1. `PgIncidenciaRepository.reemplazar` guarda el cuadrante del paso
     (`plataforma`; sin la registrada, queda quitada);
  2. `RegistroSigrid.ejecutar` manda la petición, que tiene que ser la del
     contrato (con `incidencias_mes`, `quitadas` y `cierres_recursos`, R24);
  3. con la `respuesta` del contrato (la que da el transfer, lo comprueba la
     otra mitad, `services/dedicacion-transfer/tests/test_f062_punta_a_punta.py`)
     la traza de cada incidencia queda como `traza` (R15, R17, R23); la
     quitada sin `ide` o sin líneas en Sigrid, borrada.

Los servicios no comparten intérprete: el contrato JSON es lo que los une.
Ni red ni BBDD.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from application.registro_sigrid import RegistroSigrid
from domain.models import Incidencia
from infrastructure.db.repositories import PgIncidenciaRepository
from sqlalchemy.sql.dml import Delete, Update

from tests.test_f030_r30_punta_a_punta import PERIODO, RECURSO, _SesionMem

CONTRATO = json.loads(
    (Path(__file__).resolve().parents[3] / "tests" / "contratos"
     / "f062_rachas.json").read_text(encoding="utf-8"))
ANO, MES = CONTRATO["periodo"]["ano"], CONTRATO["periodo"]["mes"]


class _SesionGuardas(_SesionMem):
    """La de F-030 con las guardas del `WHERE` (`IS NULL`, `quitada IS
    true`) en los `UPDATE` y los `DELETE` de la traza."""

    def _cumple(self, stmt):
        params = stmt.compile().params
        where = str(stmt.whereclause)
        nulas = re.findall(r"incidencia\.(\w+) IS NULL", where)
        return params, [
            o for o in self.filas if o.id == params["id_1"]
            and all(getattr(o, c) is None for c in nulas)
            and ("quitada IS true" not in where or o.quitada)]

    def execute(self, stmt):
        if isinstance(stmt, Delete):
            for o in self._cumple(stmt)[1]:
                self.filas.remove(o)
            return None
        if isinstance(stmt, Update):
            params, filas = self._cumple(stmt)
            for o in filas:
                for k, v in params.items():
                    if k != "id_1":
                        setattr(o, k, v)
            return None
        return super().execute(stmt)


class _TransferContrato:
    """Contesta a `ejecutar` la `respuesta` del paso y guarda la petición."""

    def __init__(self) -> None:
        self.payloads: list[dict] = []
        self.respuesta: dict = {}

    def ejecutar(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"ok": True, "escritas": [], "omitidas": [],
                "ya_registradas": [], **self.respuesta}


def _traza(o) -> dict:
    return {"id": o.id, "quitada": bool(o.quitada),
            "estado": o.sigrid_estado, "ide_ini": o.sigrid_ide_ini,
            "dia_ini": o.sigrid_dia_ini, "ide_fin": o.sigrid_ide_fin,
            "dia_fin": o.sigrid_dia_fin,
            "dia_fin_antes": o.sigrid_dia_fin_antes}


@pytest.mark.parametrize("escenario", CONTRATO["escenarios"],
                         ids=[e["nombre"] for e in CONTRATO["escenarios"]])
def test_f062_punta_a_punta_la_api_manda_y_traza_lo_del_contrato(escenario):
    sesion = _SesionGuardas()
    transfer = _TransferContrato()
    reg = RegistroSigrid(lambda: sesion, transfer, 1)  # type: ignore[arg-type]
    for paso in escenario["pasos"]:
        PgIncidenciaRepository(sesion).reemplazar(  # type: ignore[arg-type]
            PERIODO, RECURSO, [Incidencia(obra_ide=678, codigo=x["codigo"],
                                          dia_desde=x["desde"],
                                          dia_hasta=x["hasta"], id=x["id"])
                               for x in paso["plataforma"]], "ana")
        transfer.respuesta = paso["respuesta"]
        r = reg.ejecutar(ANO, MES, pisar_claves=[], usuario="ana")
        assert r["ok"], paso["nombre"]
        [enviada] = transfer.payloads[-1:]
        transfer.payloads.clear()
        assert {k: v for k, v in enviada.items()
                if k not in ("pisar_claves", "usuario")} == paso["peticion"], \
            paso["nombre"]
        assert [_traza(o) for o in sorted(sesion.filas, key=lambda o: o.id)
                ] == paso["traza"], paso["nombre"]
