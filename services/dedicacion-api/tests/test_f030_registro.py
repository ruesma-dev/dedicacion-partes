# tests/test_f030_registro.py
"""F-030 · T16: las incidencias en el registro de la api (R23, R25, R31).

- R23: cada obra lleva en su petición la lista `incidencias` de sus
  trabajadores visibles y vigentes; una obra solo con incidencias también
  va; sin incidencias, la petición es la de siempre (sin la clave).
- R25: `paride` = la partida elegida o la propuesta guardada de la
  asignación del trabajador en esa obra (no de postventa); si no, 0.
- R31: al volver de `ejecutar`, la traza de cada incidencia (estado, parte,
  `hmores.ide` de sus dos líneas y motivo).

Offline: sesión falsa que responde a la lectura de asignaciones y a la de
incidencias con filas fijas, y transfer falso. Ni red, ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from application.registro_sigrid import RegistroSigrid
from sqlalchemy.sql.dml import Update

from tests.test_f024_registro_empresa import _fila, _Transfer

DEF = 1


class _Resultado:
    def __init__(self, filas: list[tuple]) -> None:
        self._filas = filas

    def all(self) -> list[tuple]:
        return list(self._filas)


class _Sesion:
    """La lectura de `incidencia` devuelve `incidencias`; cualquier otra,
    `filas`. Anota los SELECT (como texto) y los UPDATE (tabla y valores)."""

    def __init__(self, filas, incidencias, anotado) -> None:
        self._filas = filas
        self._incidencias = incidencias
        self._anotado = anotado

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sentencia: Any):
        if isinstance(sentencia, Update):
            self._anotado["updates"].append(
                (sentencia.table.name, sentencia.compile().params))
            self._anotado.setdefault("wheres", []).append(
                str(sentencia.whereclause))
            return None
        texto = str(sentencia)
        self._anotado["selects"].append(texto)
        if "FROM incidencia" in texto:
            return _Resultado(self._incidencias)
        return _Resultado(self._filas)

    def commit(self) -> None:
        self._anotado["updates"].append(("commit", {}))


def _inc(inc_id, trab, obra, codigo="CIV", desde=5, hasta=9):
    """(incidencia, trabajador, obra) como los devuelve la lectura; `trab` y
    `obra` son (ide, empresa)."""
    _, t, o = _fila(0, trab, obra)
    i = SimpleNamespace(id=inc_id, trabajador_ide=trab[0], obra_ide=obra[0],
                        codigo=codigo, dia_desde=desde, dia_hasta=hasta)
    return i, t, o


def _registro(transfer, filas=(), incidencias=(), anotado=None):
    anotado = anotado if anotado is not None else {"updates": [],
                                                   "selects": []}
    return RegistroSigrid(
        lambda: _Sesion(list(filas), list(incidencias), anotado),
        transfer, DEF)


def _asig(asig_id, trab, obra, **kw):
    a, t, o = _fila(asig_id, trab, obra)
    for k, v in kw.items():
        setattr(a, k, v)
    return a, t, o


# ================================ R23 ==================================== #
@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f030_r23_cada_obra_con_sus_incidencias(fase):
    transfer = _Transfer()
    filas = [_asig(1, (10, 1), (678, 1), partida_ide=80001,
                   partida_cod="CI.1.10")]
    incs = [_inc(7, (10, 1), (678, 1)),
            _inc(8, (11, 1), (694, 1), codigo="CIE", desde=1, hasta=31)]
    reg = _registro(transfer, filas, incs)
    if fase == "preflight":
        reg.preflight(2026, 7)
    else:
        reg.ejecutar(2026, 7, pisar_claves=[])
    p678, p694 = transfer.payloads
    assert p678["obra"] == {"ide": 678, "codigo": "0678", "nombre": "OBRA"}
    assert [l["registro_id"] for l in p678["lineas"]] == [1]
    assert p678["incidencias"] == [{
        "id": 7, "recurso_ide": 10, "empresa": DEF, "codigo": "CIV",
        "ano": 2026, "mes": 7, "desde": 5, "hasta": 9, "paride": 80001}]
    # Una obra solo con incidencias también va, con las líneas vacías.
    assert p694["obra"] == {"ide": 694, "codigo": "0694", "nombre": "OBRA"}
    assert p694["lineas"] == []
    assert p694["incidencias"] == [{
        "id": 8, "recurso_ide": 11, "empresa": DEF, "codigo": "CIE",
        "ano": 2026, "mes": 7, "desde": 1, "hasta": 31, "paride": 0}]


def test_f030_r23_sin_incidencias_la_peticion_de_siempre():
    transfer = _Transfer()
    _registro(transfer, [_fila(1, (10, 1), (678, 1))]).preflight(2026, 7)
    assert [set(p) for p in transfer.payloads] == [
        {"obra", "lineas", "pisar_claves"}]


def test_f030_r23_ni_invisibles_ni_no_vigentes():
    transfer = _Transfer()
    baja = _inc(9, (12, 1), (678, 1))
    baja[1].activo = False
    baja[1].fecha_baja = None
    incs = [_inc(7, (10, 28), (678, 1)),        # otra empresa: no visible
            baja,                               # no vigente en el mes
            _inc(8, (11, 1), (678, 1))]
    r = _registro(transfer, [], incs).preflight(2026, 7, empresa=1)
    assert [i["id"] for p in transfer.payloads for i in p["incidencias"]] == [8]
    assert r["no_vigentes"] == []


def test_f030_r23_el_filtro_de_trabajador_y_de_obra():
    transfer = _Transfer()
    anotado = {"updates": [], "selects": []}
    incs = [_inc(7, (10, 1), (678, 1)), _inc(8, (10, 1), (694, 1))]
    _registro(transfer, [], incs, anotado).preflight(
        2026, 7, trabajador_ide=10, obra_ide=694)
    [sel_inc] = [s for s in anotado["selects"] if "FROM incidencia" in s]
    assert "incidencia.trabajador_ide = " in sel_inc
    assert [p["obra"]["ide"] for p in transfer.payloads] == [694]
    _registro(_Transfer(), [], incs, anotado).preflight(2026, 7)
    assert "incidencia.trabajador_ide =" not in [
        s for s in anotado["selects"] if "FROM incidencia" in s][-1]


def test_f030_r23_la_lectura_de_incidencias_es_la_del_periodo():
    """La sesión falsa no filtra: el texto de la consulta dice qué cruza
    (periodo, trabajador y obra de la incidencia) y qué periodo pide."""
    anotado = {"updates": [], "selects": []}
    _registro(_Transfer(), [], [], anotado).preflight(2026, 7)
    [sql] = [" ".join(s.split()) for s in anotado["selects"]
             if "FROM incidencia" in s]
    assert "JOIN periodo ON periodo.id = incidencia.periodo_id" in sql
    assert "JOIN trabajador ON trabajador.ide = incidencia.trabajador_ide"         in sql
    assert "JOIN obra ON obra.ide = incidencia.obra_ide" in sql
    assert "WHERE periodo.anio = :anio_1 AND periodo.mes = :mes_1" in sql


# ================================ R25 ==================================== #
def test_f030_r25_partida_elegida_propuesta_o_cero():
    transfer = _Transfer()
    filas = [
        _asig(1, (10, 1), (678, 1), partida_ide=80001),
        _asig(2, (11, 1), (678, 1), propuesta_ide=80002),
        _asig(3, (12, 1), (678, 1), es_postventa=True, partida_ide=70001),
        _asig(4, (13, 1), (694, 1), partida_ide=80004),
        _asig(5, (14, 1), (678, 1)),            # ni elegida ni propuesta
    ]
    incs = [_inc(1, (10, 1), (678, 1)), _inc(2, (11, 1), (678, 1)),
            _inc(3, (12, 1), (678, 1)), _inc(4, (13, 1), (678, 1)),
            _inc(5, (14, 1), (678, 1))]
    _registro(transfer, filas, incs).preflight(2026, 7)
    p678 = next(p for p in transfer.payloads if p["obra"]["ide"] == 678)
    assert [(i["id"], i["paride"]) for i in p678["incidencias"]] == [
        (1, 80001), (2, 80002), (3, 0), (4, 0), (5, 0)]


# ================================ R31 ==================================== #
def _respuesta(*acciones):
    return {"ok": True, "escritas": [], "omitidas": [], "ya_registradas": [],
            "incidencias": [
                {"id": i, "rol": rol, "accion": acc, "fecha_int": 20260705,
                 "hora_codigo": "CIV", "paride": 0, "parte_cod": parte,
                 "hmores_ide": ide, "motivo": motivo}
                for i, rol, acc, parte, ide, motivo in acciones]}


def _trazas(anotado):
    return [v for tabla, v in anotado["updates"] if tabla == "incidencia"]


def test_f030_r31_traza_registrada_omitida_y_mixta():
    anotado = {"updates": [], "selects": []}
    transfer = _Transfer(_respuesta(
        (7, "ini", "escribir", "PT26/00251", 70001, None),
        (7, "fin", "escribir", "PT26/00251", 70002, None),
        (8, "ini", "omitir", None, None, "sin CIZ"),
        (8, "fin", "omitir", None, None, "sin CIZ"),
        (9, "ini", "ya_registrado", "PT26/00031", 51, "ya registrada"),
        (9, "fin", "omitir", "PT26/00041", None, "ya hay una línea CIZ")))
    _registro(transfer, [_fila(1, (10, 1), (678, 1))],
              [_inc(7, (10, 1), (678, 1))], anotado).ejecutar(
        2026, 7, pisar_claves=[], usuario="ana")
    t7, t8, t9 = _trazas(anotado)
    # Cada UPDATE, solo a su incidencia.
    assert anotado["wheres"][-3:] == ["incidencia.id = :id_1"] * 3
    assert t7["id_1"] == 7 and t7["sigrid_estado"] == "registrado"
    assert (t7["sigrid_parte_cod"], t7["sigrid_ide_ini"], t7["sigrid_ide_fin"],
            t7["sigrid_motivo"], t7["sigrid_registrado_by"]) == (
        "PT26/00251", 70001, 70002, None, "ana")
    assert t7["sigrid_registrado_at_utc"] is not None
    assert (t8["id_1"], t8["sigrid_estado"], t8["sigrid_motivo"]) == (
        8, "omitido", "sin CIZ")
    assert "sigrid_registrado_by" not in t8
    # Una ya registrada y la otra ya en Sigrid de otro: registrada, con el
    # motivo de la omitida y sin pisar quién la registró.
    assert (t9["id_1"], t9["sigrid_estado"], t9["sigrid_parte_cod"],
            t9["sigrid_ide_ini"], t9["sigrid_ide_fin"], t9["sigrid_motivo"]) \
        == (9, "registrado", "PT26/00031", 51, None, "ya hay una línea CIZ")
    assert "sigrid_registrado_by" not in t9


def test_f030_r31_motivo_recortado_a_300():
    anotado = {"updates": [], "selects": []}
    largo = "x" * 400
    transfer = _Transfer(_respuesta((8, "ini", "omitir", None, None, largo),
                                    (8, "fin", "omitir", None, None, largo)))
    _registro(transfer, [_fila(1, (10, 1), (678, 1))], [],
              anotado).ejecutar(2026, 7, pisar_claves=[])
    [t8] = _trazas(anotado)
    assert t8["sigrid_motivo"] == "x" * 300


def test_f030_r31_sin_incidencias_en_la_respuesta_no_traza():
    anotado = {"updates": [], "selects": []}
    _registro(_Transfer({"ok": True, "escritas": [], "omitidas": [],
                         "ya_registradas": []}),
              [_fila(1, (10, 1), (678, 1))], [], anotado).ejecutar(
        2026, 7, pisar_claves=[])
    assert _trazas(anotado) == []
    # Si el transfer falla, tampoco.
    _registro(_Transfer({**_respuesta(
        (7, "ini", "escribir", "P", 1, None)), "ok": False}),
              [_fila(1, (10, 1), (678, 1))], [], anotado).ejecutar(
        2026, 7, pisar_claves=[])
    assert _trazas(anotado) == []


def test_f030_r31_la_traza_escribe_columnas_de_incidencia():
    """Como `test_f003_r17_la_traza_escribe_exactamente_esas_columnas` para
    la asignación: los `sigrid_*` de `traza_incidencias.py` son columnas de
    `incidencia` (y la traza cubre todas)."""
    import re
    from pathlib import Path

    from infrastructure.db.orm_models import IncidenciaORM

    fuente = (Path(__file__).resolve().parents[1] / "application"
              / "traza_incidencias.py").read_text(encoding="utf-8")
    mencionadas = set(re.findall(r"\bsigrid_[a-z_]+\b", fuente))
    columnas = {c.name for c in IncidenciaORM.__table__.columns
                if c.name.startswith("sigrid_")}
    assert mencionadas == columnas
