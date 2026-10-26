# tests/test_f030_r30_punta_a_punta.py
"""F-030 · R30 de punta a punta, mitad de la api (design §13.6, T22).

El hueco de la review 1: cambiar los días de una incidencia ya registrada
llegaba al transfer como OTRA incidencia (otro `id`, sin los `hmores.ide`
de su traza) y el transfer escribía un par nuevo. Esta mitad recorre el
código REAL de la api sobre una sesión en memoria:

  1. `PgIncidenciaRepository.reemplazar` guarda la 7 del 5 al 9;
  2. `RegistroSigrid.ejecutar` (con un transfer falso que contesta que
     escribió el par 9001/9002) deja su traza con `trazar_incidencias`;
  3. `reemplazar` le cambia los días con su `id` (lo que manda el PUT, R37);
  4. `RegistroSigrid._payloads` arma la petición, que tiene que ser la de
     `tests/contratos/f030_r30.json`.

La otra mitad (`services/dedicacion-transfer/tests/test_f030_r30_punta_a_punta.py`)
ejecuta esa misma petición contra el par en Sigrid. Los servicios no
comparten intérprete: el contrato JSON es lo que los une. Ni red ni BBDD.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from application.registro_sigrid import RegistroSigrid
from domain.models import Incidencia
from infrastructure.db.orm_models import IncidenciaORM
from infrastructure.db.repositories import PgIncidenciaRepository
from sqlalchemy.sql.dml import Update

CONTRATO = json.loads(
    (Path(__file__).resolve().parents[3] / "tests" / "contratos"
     / "f030_r30.json").read_text(encoding="utf-8"))
PERIODO = 3
RECURSO = 200
OBRA = SimpleNamespace(ide=678, cod="0678", descripcion="OBRA", empresa=1,
                       registro_obra_ide=None, registro_obra_cod=None,
                       registro_paride=None)
TRABAJADOR = SimpleNamespace(ide=RECURSO, dni=None, nombre="Ana", empresa=1,
                             categoria="Encargado", activo=True,
                             fecha_baja=None)


class _Filas:
    def __init__(self, filas) -> None:
        self._filas = list(filas)

    def all(self):
        return list(self._filas)


class _SesionMem:
    """Sesión en memoria con lo que usan `reemplazar`, `_payloads` y la
    traza: las filas de `incidencia` (con `id` al hacer `flush`, desde 7),
    sus `UPDATE` por `id` y la lectura de las incidencias del periodo (las
    asignaciones, ninguna)."""

    def __init__(self) -> None:
        self.filas: list[IncidenciaORM] = []
        self.siguiente = 7

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def scalars(self, stmt):
        return _Filas(sorted(self.filas, key=lambda o: o.id))

    def add(self, orm) -> None:
        self.filas.append(orm)

    def delete(self, orm) -> None:
        self.filas.remove(orm)

    def flush(self) -> None:
        for orm in self.filas:
            if orm.id is None:
                orm.id, self.siguiente = self.siguiente, self.siguiente + 1

    def commit(self) -> None:
        return None

    def execute(self, stmt):
        if isinstance(stmt, Update):
            params = stmt.compile().params
            [orm] = [o for o in self.filas if o.id == params["id_1"]]
            for k, v in params.items():
                if k != "id_1":
                    setattr(orm, k, v)
            return None
        if "FROM incidencia" in str(stmt):
            return _Filas([(o, TRABAJADOR, OBRA) for o in self.filas])
        return _Filas([])


class _TransferRegistro:
    """Contesta a `ejecutar` que escribió el par de la incidencia 7 con los
    `hmores.ide` del contrato (lo que hizo el registro del 5 al 9)."""

    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def ejecutar(self, payload: dict) -> dict:
        self.payloads.append(payload)
        reg = CONTRATO["registro"]
        return {"ok": True, "escritas": [], "omitidas": [],
                "ya_registradas": [], "incidencias": [
                    {"id": 7, "rol": rol, "accion": "escribir",
                     "fecha_int": reg[rol]["fecha_int"],
                     "hora_codigo": reg[rol]["hora_codigo"], "paride": 0,
                     "parte_cod": reg[rol]["parte_cod"],
                     "hmores_ide": reg[rol]["hmores_ide"], "motivo": None}
                    for rol in ("ini", "fin")]}


def _registrada_del_5_al_9() -> tuple[_SesionMem, RegistroSigrid]:
    sesion = _SesionMem()
    PgIncidenciaRepository(sesion).reemplazar(  # type: ignore[arg-type]
        PERIODO, RECURSO, [Incidencia(obra_ide=678, codigo="CIV",
                                      dia_desde=5, dia_hasta=9)], "ana")
    reg = RegistroSigrid(lambda: sesion, _TransferRegistro(), 1)  # type: ignore[arg-type]
    reg.ejecutar(2026, 7, pisar_claves=[], usuario="ana")
    return sesion, reg


@pytest.mark.parametrize("caso", CONTRATO["casos"],
                         ids=[f"{c['dias'][0]}-{c['dias'][1]}"
                              for c in CONTRATO["casos"]])
def test_f030_r30_punta_a_punta_la_api_manda_la_misma_con_su_traza(caso):
    sesion, reg = _registrada_del_5_al_9()
    [orm] = sesion.filas
    assert (orm.id, orm.sigrid_ide_ini, orm.sigrid_ide_fin) == (7, 9001, 9002)
    desde, hasta = caso["dias"]
    # El PUT del front manda el `id` de la guardada (R37).
    PgIncidenciaRepository(sesion).reemplazar(  # type: ignore[arg-type]
        PERIODO, RECURSO, [Incidencia(obra_ide=678, codigo="CIV",
                                      dia_desde=desde, dia_hasta=hasta,
                                      id=7)], "ana")
    payloads, no_vigentes = reg._payloads(
        sesion, 2026, 7, {}, None, reg._filtro(None))  # type: ignore[arg-type]
    # F-062 (lista cerrada): R24, el recurso designado, como en `ejecutar`.
    reg._designar_cierres(payloads)
    assert no_vigentes == []
    assert payloads == [caso["peticion"]]
