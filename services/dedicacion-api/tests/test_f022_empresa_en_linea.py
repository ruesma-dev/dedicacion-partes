# tests/test_f022_empresa_en_linea.py
"""F-022 · La API pone la empresa en cada línea que manda al transfer
(R20-R21).

La API no decide nada sobre obras de Sigrid: solo pone en cada línea la
empresa a la que se imputa, que hoy sale del ajuste `EMPRESA_IMPUTACION`
(decisión D1, puente hasta F-024). La regla que la usa vive en
`docs/ARCHITECTURE.md#regla-empresa`.

Offline: sesión de SQLAlchemy falsa (devuelve tuplas fijas) y transfer falso
que captura el payload. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from application.registro_sigrid import RegistroSigrid
from config.settings import Settings
from pydantic import ValidationError


class _Resultado:
    def __init__(self, filas: list[tuple]) -> None:
        self._filas = filas

    def all(self) -> list[tuple]:
        return list(self._filas)


class _Sesion:
    """Sesión falsa: cualquier `execute` devuelve las filas fijadas."""

    def __init__(self, filas: list[tuple]) -> None:
        self._filas = filas

    def __enter__(self) -> _Sesion:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, _sentencia: Any) -> _Resultado:
        return _Resultado(self._filas)


class _Transfer:
    """Transfer falso: guarda cada payload y contesta sin escribir nada."""

    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def preflight(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"ok": True}

    def ejecutar(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"ok": False}                # sin traza: no toca la sesión


def _fila(asig_id: int, trab_ide: int, obra_ide: int) -> tuple:
    """(asignación, trabajador, obra) como las devuelve la consulta."""
    asignacion = SimpleNamespace(id=asig_id, porcentaje=40,
                                 es_postventa=False)
    trabajador = SimpleNamespace(ide=trab_ide, dni=None,
                                 nombre=f"T{trab_ide}", categoria="Encargado")
    obra = SimpleNamespace(ide=obra_ide, cod=f"0{obra_ide}",
                           descripcion="OBRA")
    return asignacion, trabajador, obra


FILAS = [_fila(1, 10, 678), _fila(2, 11, 678), _fila(3, 10, 713)]


@pytest.mark.parametrize("empresa", [1, 28])
@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f022_r20_cada_linea_lleva_la_empresa_de_imputacion(fase, empresa):
    """R20 · Todas las líneas de todas las obras llevan `empresa` =
    `EMPRESA_IMPUTACION`, en preflight y en ejecutar."""
    transfer = _Transfer()
    registro = RegistroSigrid(lambda: _Sesion(FILAS), transfer, empresa)
    if fase == "preflight":
        registro.preflight(2026, 7)
    else:
        registro.ejecutar(2026, 7, pisar_claves=[])
    assert [p["obra"]["ide"] for p in transfer.payloads] == [678, 713]
    lineas = [lin for p in transfer.payloads for lin in p["lineas"]]
    assert [lin["registro_id"] for lin in lineas] == [1, 2, 3]
    assert [lin["empresa"] for lin in lineas] == [empresa] * 3


def test_f022_r20_la_empresa_es_obligatoria_al_construir():
    """R20 · `RegistroSigrid` no tiene empresa por defecto: sin ella no se
    construye (el valor sale SIEMPRE del ajuste)."""
    with pytest.raises(TypeError):
        RegistroSigrid(lambda: _Sesion([]), _Transfer())   # type: ignore


def test_f022_r21_empresa_imputacion_por_defecto_es_1(monkeypatch):
    """R21 · Sin declarar `EMPRESA_IMPUTACION`, vale 1."""
    monkeypatch.delenv("EMPRESA_IMPUTACION", raising=False)
    assert Settings(_env_file=None).empresa_imputacion == 1


def test_f022_r21_empresa_imputacion_se_lee_del_entorno(monkeypatch):
    monkeypatch.setenv("EMPRESA_IMPUTACION", "28")
    assert Settings(_env_file=None).empresa_imputacion == 28


@pytest.mark.parametrize("valor", ["0", "-1", "x"])
def test_f022_r21_empresa_imputacion_invalida_no_arranca(monkeypatch, valor):
    """R21 · ≤ 0 o no numérico: error de validación, la API no arranca."""
    monkeypatch.setenv("EMPRESA_IMPUTACION", valor)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_f022_r21_el_ejemplo_declara_la_variable():
    """R21 · El `.env.example` de la API la declara, con su valor puente."""
    from pathlib import Path

    ejemplo = Path(__file__).resolve().parents[1] / ".env.example"
    assert "EMPRESA_IMPUTACION=1" in ejemplo.read_text(encoding="utf-8")
