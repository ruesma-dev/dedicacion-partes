# tests/test_f024_registro_empresa.py
"""F-024 · Registro en Sigrid con la empresa elegida (R16-R19), adaptado a
F-034.

La API manda al transfer solo las líneas de los trabajadores visibles en la
empresa elegida (F-034 R2-R3), todas con `empresa` = la empresa de las obras
(`EMPRESA_IMPUTACION`), sea cual sea la elegida (F-034 R7); las de obras de
otra empresa se mandan igual y su omisión queda trazada. La regla está en
`docs/ARCHITECTURE.md#regla-empresa`; los cambios de F-034, declarados en
`progress/impl_F-034.md`.

Offline: sesión de SQLAlchemy falsa (devuelve tuplas fijas y anota cada
sentencia) y transfer falso que captura el payload. Ni red, ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Self

import pytest
from application.registro_sigrid import RegistroSigrid
from sqlalchemy.sql.dml import Update

#: Empresa por defecto (EMPRESA_IMPUTACION) de los tests.
DEF = 1


class _Resultado:
    def __init__(self, filas: list[tuple]) -> None:
        self._filas = filas

    def all(self) -> list[tuple]:
        return list(self._filas)


class _Sesion:
    """Sesión falsa: el SELECT devuelve las filas fijadas; los UPDATE de la
    traza se anotan en `updates` (compartida entre sesiones)."""

    def __init__(self, filas: list[tuple], updates: list[dict]) -> None:
        self._filas = filas
        self._updates = updates

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sentencia: Any) -> _Resultado | None:
        if isinstance(sentencia, Update):
            self._updates.append(sentencia.compile().params)
            return None
        return _Resultado(self._filas)

    def commit(self) -> None:
        self._updates.append({"commit": True})


class _Transfer:
    """Transfer falso: guarda cada payload y contesta lo que se le fije."""

    def __init__(self, respuesta: dict | None = None) -> None:
        self.payloads: list[dict] = []
        self.respuesta = respuesta or {"ok": True}

    def preflight(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return dict(self.respuesta)

    def ejecutar(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return dict(self.respuesta)


def _fila(asig_id: int, trab: tuple[int, int | None],
          obra: tuple[int, int | None]) -> tuple:
    """(asignación, trabajador, obra) como las devuelve la consulta;
    `trab` y `obra` son (ide, empresa)."""
    asignacion = SimpleNamespace(id=asig_id, porcentaje=50,
                                 es_postventa=False)
    # `activo` y `fecha_baja` (F-026, C3): vigente en cualquier mes.
    trabajador = SimpleNamespace(ide=trab[0], dni=None, nombre=f"T{trab[0]}",
                                 categoria="Encargado", empresa=trab[1],
                                 activo=True, fecha_baja=None)
    # F-039: sin obra ni partida de registro (no es una entrada VAR).
    o = SimpleNamespace(ide=obra[0], cod=f"0{obra[0]}", descripcion="OBRA",
                        empresa=obra[1], registro_obra_ide=None,
                        registro_obra_cod=None, registro_paride=None)
    return asignacion, trabajador, o


#: 10 es de la 1 (una línea en obra de la 28); 11 de la 28; 12 sin empresa
#: con carga en la 28; 13 sin empresa con carga en obra sin empresa.
FILAS = [
    _fila(1, (10, 1), (678, 1)),
    _fila(2, (10, 1), (9, 28)),
    _fila(3, (11, 28), (9, 28)),
    _fila(4, (12, None), (9, 28)),
    _fila(5, (13, None), (500, None)),
]


def _registro(transfer: _Transfer, filas: list[tuple] = FILAS,
              updates: list[dict] | None = None) -> RegistroSigrid:
    anotadas = updates if updates is not None else []
    return RegistroSigrid(lambda: _Sesion(filas, anotadas), transfer, DEF)


def _lineas(transfer: _Transfer) -> list[tuple[int, int]]:
    return [(lin["registro_id"], lin["empresa"])
            for p in transfer.payloads for lin in p["lineas"]]


# ------------------------------ R16 → F-034 R7 ------------------------ #
@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
@pytest.mark.parametrize("empresa, esperadas", [
    # sin empresa: la por defecto; la 4 (12, NULL) pasa a la por defecto (R3)
    (None, [(1, 1), (2, 1), (4, 1), (5, 1)]),
    (1, [(1, 1), (2, 1), (4, 1), (5, 1)]),
    (28, [(3, 1)]),                         # Bea, con la empresa de las obras
    (18, []),
])
def test_f034_r7_solo_visibles_y_todas_con_la_empresa_de_las_obras(
        fase, empresa, esperadas):
    """F-034 (R7) · Sustituye a
    `test_f024_r16_solo_visibles_y_todas_con_la_empresa_elegida`."""
    transfer = _Transfer()
    registro = _registro(transfer)
    if fase == "preflight":
        r = registro.preflight(2026, 7, empresa=empresa)
    else:
        r = registro.ejecutar(2026, 7, pisar_claves=[], empresa=empresa)
    assert sorted(_lineas(transfer)) == esperadas
    assert r["ok"] is True


# --------------------------------- R17 -------------------------------- #
def test_f024_r17_obra_de_otra_empresa_se_manda_y_su_omision_se_traza():
    """La línea 2 (obra 9 de la 28) de un trabajador de la 1 viaja con
    `empresa = 1`; el transfer la omite y la API lo deja en la asignación.
    F-034 (R3): la 4, de 12 (NULL, carga en la obra 9), pasa a verse en la 1
    y viaja también en la obra 9; la traza de la omitida 2 no cambia."""
    motivo = ("la obra 09 es de la empresa 28 y la línea se imputa a la "
              "empresa 1: no se escribe")
    transfer = _Transfer({"ok": True, "escritas": [], "ya_registradas": [],
                          "omitidas": [{"registro_id": 2,
                                        "motivo": motivo}]})
    updates: list[dict] = []
    registro = _registro(transfer, updates=updates)
    registro.ejecutar(2026, 7, pisar_claves=[], empresa=1)
    obra_9 = [p for p in transfer.payloads if p["obra"]["ide"] == 9]
    assert [(lin["registro_id"], lin["empresa"])
            for lin in obra_9[0]["lineas"]] == [(2, 1), (4, 1)]
    omitidos = [u for u in updates if u.get("sigrid_estado") == "omitido"]
    assert {u["id_1"] for u in omitidos} == {2}
    assert all(u["sigrid_motivo"] == motivo for u in omitidos)


# --------------------------------- R18 -------------------------------- #
@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f024_r18_trabajador_no_visible_no_llama_al_transfer(fase):
    transfer = _Transfer()
    filas_11 = [f for f in FILAS if f[1].ide == 11]
    registro = _registro(transfer, filas_11)
    if fase == "preflight":
        r = registro.preflight(2026, 7, trabajador_ide=11, empresa=1)
    else:
        r = registro.ejecutar(2026, 7, pisar_claves=[], trabajador_ide=11,
                              empresa=1)
    # F-026 (R16, B1): la respuesta lleva siempre `no_vigentes`.
    assert r == {"ok": True, "obras": [], "no_vigentes": []}
    assert transfer.payloads == []


# --------------------------------- R19 -------------------------------- #
ERROR_PRUEBAS = "obra de pruebas 0404 no encontrada en la empresa 28"


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f024_r19_sin_obra_de_pruebas_error_por_obra_y_nada_trazado(fase):
    """Lo que `TransferClient._post` devuelve ante el 502 del transfer.

    F-034 (D4): la D3 de F-024 (error de modo pruebas con otra empresa
    elegida) queda sin objeto, porque la línea viaja siempre con la empresa
    de las obras y la obra de pruebas se busca en ella. El test se conserva
    como prueba de que un error por obra del transfer se propaga y no se
    traza."""
    transfer = _Transfer({"ok": False, "error": ERROR_PRUEBAS})
    updates: list[dict] = []
    registro = _registro(transfer, updates=updates)
    if fase == "preflight":
        r = registro.preflight(2026, 7, empresa=28)
    else:
        r = registro.ejecutar(2026, 7, pisar_claves=[], empresa=28)
    assert r["ok"] is False
    assert [o["obra"]["ide"] for o in r["obras"]] == [9]
    assert all(o["ok"] is False and o["error"] == ERROR_PRUEBAS
               for o in r["obras"])
    assert updates == []
