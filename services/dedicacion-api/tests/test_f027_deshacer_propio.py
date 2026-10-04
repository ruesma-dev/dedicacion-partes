# tests/test_f027_deshacer_propio.py
"""F-027 · Deshacer solo lo propio (decisión A del 2026-10-04).

Solo se deshace si el ÚLTIMO evento pendiente del trabajador en el periodo es
del usuario que lo pide; si es de otro, se rechaza con un motivo que lo
nombra y el mismo 409 que «nada que deshacer». `puede_deshacer` (cuadrante y
fila) sigue la misma regla. Los usuarios se comparan sin mayúsculas ni
espacios en los extremos (`domain/deshacer.py`).

Offline: el repositorio con una sesión falsa que captura la sentencia, los
casos de uso con la UnitOfWork en memoria de `test_f024_cuadrante_empresa`
(con dos usuarios) y la API con `TestClient`. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from domain.deshacer import clave_usuario, deshacer_permitido
from domain.errors import DeshacerAjeno, ErrorDominio, NadaQueDeshacer
from domain.models import EventoPendiente
from infrastructure.db.repositories import PgEventoRepository
from sqlalchemy.dialects import postgresql


# =========================== dominio (T1) ============================== #
@pytest.mark.parametrize("autor, usuario", [
    ("pablo@ruesma.es", "pablo@ruesma.es"),
    ("Pablo@Ruesma.ES", "pablo@ruesma.es"),
    ("  pablo@ruesma.es\t", "PABLO@ruesma.es "),
])
def test_f027_r4_mismo_usuario_sin_mayusculas_ni_espacios(autor, usuario):
    assert deshacer_permitido(autor, usuario) is True


@pytest.mark.parametrize("autor, usuario", [
    ("ana@ruesma.es", "pablo@ruesma.es"),
    ("pablo@ruesma.es", "pablo@ruesma.es.otro"),   # prefijo no es el mismo
    ("pa blo@ruesma.es", "pablo@ruesma.es"),       # el interior no se toca
    (None, "pablo@ruesma.es"),                     # nada pendiente
])
def test_f027_r4_otro_usuario_o_nada_pendiente(autor, usuario):
    assert deshacer_permitido(autor, usuario) is False


def test_f027_r4_clave_usuario_es_la_unica_normalizacion():
    assert clave_usuario("  Ana.López@Ruesma.ES  ") == "ana.lópez@ruesma.es"


def test_f027_r1_el_error_es_de_dominio_y_distinto_de_nada_que_deshacer():
    assert issubclass(DeshacerAjeno, ErrorDominio)
    assert not issubclass(DeshacerAjeno, NadaQueDeshacer)


# ========================= repositorio (T2) ============================ #
class _Filas:
    def __init__(self, valores: list[Any]) -> None:
        self._valores = valores

    def all(self) -> list[Any]:
        return list(self._valores)

    def first(self) -> Any:
        return self._valores[0] if self._valores else None


class _Sesion:
    """Sesión falsa: guarda cada sentencia y devuelve los valores fijados."""

    def __init__(self, valores: list[Any]) -> None:
        self.valores = valores
        self.sentencias: list[Any] = []

    def scalars(self, stmt: Any) -> _Filas:
        self.sentencias.append(stmt)
        return _Filas(self.valores)

    def execute(self, stmt: Any) -> _Filas:
        self.sentencias.append(stmt)
        return _Filas(self.valores)


def _compilada(stmt: Any) -> tuple[str, dict[str, Any]]:
    c = stmt.compile(dialect=postgresql.dialect())
    return " ".join(str(c).split()), dict(c.params)


def test_f027_r3_ultimo_pendiente_trae_su_autor():
    orm = SimpleNamespace(id=7, usuario="ana@ruesma.es",
                          snapshot_antes=[{"obra_ide": 100}])
    sesion = _Sesion([orm])
    pendiente = PgEventoRepository(sesion).ultimo_pendiente(3, 10)  # type: ignore[arg-type]
    assert pendiente == EventoPendiente(id=7, usuario="ana@ruesma.es",
                                        snapshot_antes=[{"obra_ide": 100}])
    assert PgEventoRepository(_Sesion([])).ultimo_pendiente(3, 10) is None  # type: ignore[arg-type]


def test_f027_r3_autores_del_ultimo_pendiente_de_todo_el_periodo():
    """El autor es el del ÚLTIMO pendiente de cada trabajador (max(id) de
    los no deshechos del periodo), no «alguno pendiente mío»."""
    sesion = _Sesion([(10, "ana@ruesma.es"), (14, "pablo@ruesma.es")])
    autores = PgEventoRepository(sesion).autores_ultimo_pendiente(3)  # type: ignore[arg-type]
    assert autores == {10: "ana@ruesma.es", 14: "pablo@ruesma.es"}
    [stmt] = sesion.sentencias
    sql, params = _compilada(stmt)
    assert sql.startswith(
        "SELECT evento.trabajador_ide, evento.usuario FROM evento "
        "WHERE evento.id IN (SELECT max(evento.id) AS max_1 FROM evento "
        "WHERE evento.periodo_id = %(periodo_id_1)s "
        "AND evento.deshecho IS false GROUP BY evento.trabajador_ide)")
    assert params == {"periodo_id_1": 3}
