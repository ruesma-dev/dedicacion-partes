# tests/test_f074_postventa.py
"""F-074 · T5-T6: la partida de postventa de cada obra, guardada en el sync
y mandada al registro (R11, R12; D2).

- R11: el universo del transfer trae la partida de cada obra (`obras[].
  partida`) y el motivo de las que no casan (`motivos`); `depurar_obras` la
  pone en cada fila (`postventa_partida_ide/_cod/_res` o `postventa_motivo`),
  con la MISMA llamada de hoy, y el repositorio la guarda, la actualiza y la
  anula en la obra que no llega. Cuatro columnas nulables sin default en
  `obra` (el ADD COLUMN lo deriva `esquema`).
- R12: la línea de postventa sin elegida publica como propuesta la de su obra
  (método `postventa`) y la manda al registro como `propuesta_*`; si la obra
  no casa, «no encontrada» con su motivo; sin sync, ninguna marca.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

import dataclasses
from types import SimpleNamespace

import pytest

from application.estado_partida import Marcas, estado_de_linea
from application.filtros_maestros import depurar_obras
from domain.models import ResultadoUniverso
from infrastructure.db.orm_models import ObraORM
from tests.test_f025_sync_postventa import (
    OBRAS,
    SQL_EMP,
    SQL_OBR,
    _cliente,
    _o,
    _orm,
    _Respuesta,
    _sigrid,
)
from tests.test_f055_propuesta_guardada import PR, _lp
from tests.test_f055_registro_lote import _fila, _lineas, _registro, _TransferLote

PARTIDA_10 = {"ide": 70001, "cod": "0656", "res": "TOMARES"}
NO_CASA = "la obra 0013 no casa con ninguna partida de POSTV2"
COLUMNAS = ("postventa_partida_ide", "postventa_partida_cod",
            "postventa_partida_res", "postventa_motivo")


# ============================ R11 · el sync ============================== #
def test_f074_r11_el_cliente_lee_partidas_y_motivos(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _Respuesta({
        "ok": True, "motivo": None, "obras": [
            {"ide": 10, "codigo": "0656", "partida": PARTIDA_10}],
        "motivos": {"11": NO_CASA}}))
    r = cliente.universo_postventa(1, OBRAS)
    assert r == ResultadoUniverso(ides=frozenset({10}), motivo=None,
                                  partidas={10: PARTIDA_10},
                                  motivos={11: NO_CASA})


def test_f074_r11_transfer_anterior_sin_partida_ni_motivos(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _Respuesta({
        "ok": True, "motivo": None, "obras": [{"ide": 10}]}))
    r = cliente.universo_postventa(1, OBRAS)
    assert (r.partidas, r.motivos) == ({}, {})


def test_f074_r11_depurar_obras_pone_la_partida_o_el_motivo():
    filas = [_o(10), _o(12), _o(13)]
    r = depurar_obras(filas, [], False, frozenset({10}),
                      partidas={10: PARTIDA_10}, motivos={13: NO_CASA})
    por_ide = {f["ide"]: tuple(f[c] for c in COLUMNAS) for f in r.filas}
    assert por_ide == {10: (70001, "0656", "TOMARES", None),
                       12: (None, None, None, None),
                       13: (None, None, None, NO_CASA)}


def test_f074_r11_sin_partidas_las_columnas_nulas():
    r = depurar_obras([_o(12)], [], False, frozenset())
    assert all(r.filas[0][c] is None for c in COLUMNAS)


def test_f074_r11_el_sync_las_guarda_con_la_misma_llamada():
    from application import sync_pipeline as sp
    from tests.test_f023_sync_empresa import _UowEspia

    class _Universo:
        llamadas = 0

        def universo_postventa(self, empresa, obras):
            self.llamadas += 1
            return ResultadoUniverso(ides=frozenset({10}), motivo=None,
                                     partidas={10: PARTIDA_10},
                                     motivos={13: NO_CASA})

        def universo_var(self, empresa):
            from domain.models import ResultadoUniversoVar
            return ResultadoUniversoVar(obra_ide=None, obra_cod=None,
                                        empresa=None, partidas=(),
                                        motivo=None)

    universo, uow = _Universo(), _UowEspia()
    sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(_sigrid(), SQL_EMP),
        sp.FetchObrasStep(_sigrid([_o(10), _o(12), _o(13)]), SQL_OBR,
                          ["cerrada"],
                          universo=universo, empresa_obras=1),
        sp.UpsertTrabajadoresStep(), sp.UpsertObrasStep()]).ejecutar(uow)
    por_ide = {f["ide"]: f for f in uow.obras.recibido}
    assert universo.llamadas == 1
    assert por_ide[10]["postventa_partida_cod"] == "0656"
    assert por_ide[13]["postventa_motivo"] == NO_CASA


def test_f074_r11_el_repositorio_guarda_actualiza_y_anula():
    from infrastructure.db.repositories import PgObraRepository
    from tests.test_f023_sync_empresa import _SesionRepo

    def fila(ide, **pv):
        return {**_o(ide), "activa": True, "admite_postventa": bool(pv),
                **dict.fromkeys(COLUMNAS), **pv}

    existente = _orm(10, True, True)
    fuera = _orm(11, True, True)
    fuera.postventa_partida_ide, fuera.postventa_motivo = 1, "x"
    sesion = _SesionRepo([existente, fuera])
    res = PgObraRepository(sesion).sincronizar([
        fila(10, postventa_partida_ide=70001, postventa_partida_cod="0656",
             postventa_partida_res="TOMARES"),
        fila(13, postventa_motivo=NO_CASA)])
    assert res.actualizados == 1 and res.altas == 1
    assert (existente.postventa_partida_ide, existente.postventa_partida_cod,
            existente.postventa_motivo) == (70001, "0656", None)
    [nueva] = sesion.anadidas
    assert (nueva.postventa_partida_ide, nueva.postventa_motivo) == (
        None, NO_CASA)
    assert all(getattr(fuera, c) is None for c in COLUMNAS)


def test_f074_r11_cambiar_solo_la_partida_cuenta_como_actualizada():
    from infrastructure.db.repositories import PgObraRepository
    from tests.test_f023_sync_empresa import _SesionRepo

    existente = _orm(10, True, True)
    res = PgObraRepository(_SesionRepo([existente])).sincronizar([{
        **_o(10), "activa": True, "admite_postventa": True,
        "postventa_partida_ide": 70002}])
    assert res.actualizados == 1


@pytest.mark.parametrize("columna", COLUMNAS)
def test_f074_r11_columnas_nulables_sin_default(columna):
    c = ObraORM.__table__.c[columna]
    assert c.nullable and c.default is None and c.server_default is None


def test_f074_r11_el_alter_lo_deriva_esquema():
    from infrastructure.db.esquema import alters_faltantes

    metadata = ObraORM.metadata
    existentes = {t.name: {c.name for c in t.columns}
                  for t in metadata.tables.values()}
    existentes["obra"] -= set(COLUMNAS)
    assert alters_faltantes(metadata, existentes) == [
        "ALTER TABLE obra ADD COLUMN IF NOT EXISTS postventa_partida_ide BIGINT",
        "ALTER TABLE obra ADD COLUMN IF NOT EXISTS postventa_partida_cod TEXT",
        "ALTER TABLE obra ADD COLUMN IF NOT EXISTS postventa_partida_res TEXT",
        "ALTER TABLE obra ADD COLUMN IF NOT EXISTS postventa_motivo TEXT"]


# ==================== R12 · la línea de postventa ======================== #
def _pv(**kw):
    return _lp(100, "40", pv=True, **kw)


def test_f074_r12_postventa_publica_la_de_su_obra():
    ln = _pv(obra_pv_ide=70001, obra_pv_cod="0656", obra_pv_res="TOMARES")
    assert estado_de_linea(14, ln) == {
        "propuesta_cod": "0656", "propuesta_res": "TOMARES",
        "propuesta_metodo": "postventa", "propuesta_pendiente": False}


def test_f074_r12_postventa_que_no_casa_no_encontrada_con_motivo():
    ln = _pv(obra_pv_motivo=NO_CASA)
    out = estado_de_linea(14, ln)
    assert (out["propuesta_cod"], out["propuesta_no_encontrada"],
            out["propuesta_motivo"]) == (None, True, NO_CASA)


def test_f074_r12_postventa_sin_sync_ninguna_marca():
    out = estado_de_linea(14, _pv(), Marcas(no_encontradas={
        (14, 100, True): "x"}))
    assert out == {"propuesta_cod": None, "propuesta_res": None,
                   "propuesta_metodo": None, "propuesta_pendiente": False}


def test_f074_r12_postventa_con_elegida_no_publica_la_de_su_obra():
    ln = _pv(partida_ide=70002, partida_cod="0713", obra_pv_ide=70001,
             obra_pv_cod="0656")
    assert estado_de_linea(14, ln)["propuesta_cod"] is None


def _fila_pv(asig_id, **obra_pv):
    a, t, o = _fila(asig_id, pv=True)
    return a, t, SimpleNamespace(**vars(o), **obra_pv)


def test_f074_r12_el_registro_manda_la_de_su_obra():
    t = _TransferLote()
    _registro([_fila_pv(1, postventa_partida_ide=70001,
                        postventa_partida_cod="0656",
                        postventa_partida_res="TOMARES")], t)[0] \
        .preflight(2026, 8)
    [ln] = _lineas(t)
    assert {k: ln[k] for k in ln if k.startswith("propuesta_")} == {
        "propuesta_paride": 70001, "propuesta_cod": "0656",
        "propuesta_res": "TOMARES", "propuesta_metodo": "postventa"}
    assert "paride" not in ln


def test_f074_r12_sin_partida_de_su_obra_viaja_sin_ninguna():
    t = _TransferLote()
    _registro([_fila_pv(1, postventa_partida_ide=None,
                        postventa_motivo=NO_CASA)], t)[0].preflight(2026, 8)
    [ln] = _lineas(t)
    assert not any(k.startswith("propuesta_") or k == "paride" for k in ln)


def test_f074_r12_postventa_nunca_manda_una_guardada():
    a, tr, o = _fila(1, pv=True, **PR)
    t = _TransferLote()
    _registro([(a, tr, o)], t)[0].preflight(2026, 8)
    [ln] = _lineas(t)
    assert not any(k.startswith("propuesta_") for k in ln)


def test_f074_r12_la_elegida_de_postventa_manda():
    a, tr, o = _fila_pv(1, postventa_partida_ide=70001,
                        postventa_partida_cod="0656")
    a = SimpleNamespace(**{**vars(a), "partida_ide": 70002,
                           "partida_cod": "0713"})
    t = _TransferLote()
    _registro([(a, tr, o)], t)[0].preflight(2026, 8)
    [ln] = _lineas(t)
    assert ln["paride"] == 70002
    assert not any(k.startswith("propuesta_") for k in ln)


def test_f074_r12_obra_y_linea_la_leen_del_repositorio():
    from infrastructure.db.orm_models import AsignacionORM
    from infrastructure.db.repositories import _a_linea, _a_obra

    orm = _orm(10, True, True)
    orm.postventa_partida_ide, orm.postventa_partida_cod = 70001, "0656"
    orm.postventa_partida_res, orm.postventa_motivo = "TOMARES", None
    o = _a_obra(orm)
    assert (o.postventa_partida_ide, o.postventa_partida_cod,
            o.postventa_partida_res, o.postventa_motivo) == (
        70001, "0656", "TOMARES", None)
    ln = _a_linea(AsignacionORM(obra_ide=10, es_postventa=True,
                                porcentaje=40), orm)
    assert (ln.obra_pv_ide, ln.obra_pv_cod, ln.obra_pv_res,
            ln.obra_pv_motivo) == (70001, "0656", "TOMARES", None)
    # No entra en la identidad de la línea.
    assert ln.clave() == dataclasses.replace(ln, obra_pv_ide=None).clave()
