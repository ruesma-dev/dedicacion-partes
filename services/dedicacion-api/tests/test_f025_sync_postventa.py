# tests/test_f025_sync_postventa.py
"""Tests offline de F-025 en la api: el universo de postventa se pide en el
sync y se guarda en la obra (R12-R16, R18, R21).

Trazabilidad con `specs/F-025-obras-postventa-postv2/requirements.md`. El
universo lo calcula SOLO el transfer (D1): aquí se sustituye por el doble
`UniversoFalso` de `tests/conftest.py`. Nada abre un socket ni una conexión.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest
from domain.models import Linea, Obra
from infrastructure.db.orm_models import Base, ObraORM
from sqlalchemy.dialects import postgresql

DIALECTO = postgresql.dialect()


# --- R18 · `ofrecible`, una sola definición en el dominio ---------------------


def _linea(es_postventa: bool, activa: bool, admite: bool) -> Linea:
    return Linea(obra_ide=1, es_postventa=es_postventa,
                 porcentaje=Decimal("50"), obra_activa=activa,
                 obra_admite_postventa=admite)


@pytest.mark.parametrize(("es_postventa", "activa", "admite", "ofrecible"), [
    (False, True, False, True),     # normal en obra activa
    (False, False, True, False),    # normal en obra solo de postventa
    (True, False, True, True),      # postventa en obra que la admite
    (True, True, False, False),     # postventa en obra que no la admite
])
def test_f025_r18_ofrecible_segun_el_modo_de_la_linea(
    es_postventa: bool, activa: bool, admite: bool, ofrecible: bool
) -> None:
    """R18 · La normal es ofrecible si la obra está `activa`; la de
    postventa, si la obra `admite_postventa`. Nada más."""
    assert _linea(es_postventa, activa, admite).ofrecible is ofrecible


def test_f025_r18_por_defecto_una_linea_no_admite_postventa() -> None:
    """R18 · Sin marca, una línea de postventa no es ofrecible."""
    linea = Linea(obra_ide=1, es_postventa=True, porcentaje=Decimal("1"))
    assert linea.obra_admite_postventa is False
    assert linea.ofrecible is False


def test_f025_r18_la_obra_por_defecto_no_admite_postventa() -> None:
    """R18 · `Obra.admite_postventa` existe y por defecto es `False`."""
    obra = Obra(ide=1, cod="0001", descripcion="X", estado_sigrid=None)
    assert obra.admite_postventa is False and obra.activa is True


def test_f025_r18_resultado_universo_es_inmutable() -> None:
    """R18 · `ResultadoUniverso` (lo que devuelve el puerto) es inmutable."""
    from domain.models import ResultadoUniverso

    r = ResultadoUniverso(ides=frozenset({1, 2}), motivo=None)
    assert r.ides == frozenset({1, 2}) and r.motivo is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.motivo = "x"  # type: ignore[misc]


# --- R21 · la columna, solo en el ORM y con su ALTER derivado ------------------


def test_f025_r21_columna_booleana_no_nula_false_por_defecto() -> None:
    """R21 · `obra.admite_postventa`: booleano, no nulo, `false` en servidor
    (así el ALTER sobre una tabla con filas no necesita migración)."""
    columna = ObraORM.__table__.columns["admite_postventa"]
    assert columna.type.compile(dialect=DIALECTO) == "BOOLEAN"
    assert columna.nullable is False
    assert columna.default is not None and columna.default.arg is False
    assert str(columna.server_default.arg.compile(dialect=DIALECTO)) == "false"


def test_f025_r21_el_alter_lo_deriva_esquema() -> None:
    """R21 · Sobre una base sin la columna, `alters_faltantes` deriva el
    `ADD COLUMN` (sin PostgreSQL); con ella, nada."""
    from infrastructure.db.esquema import alters_faltantes

    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()}
    assert alters_faltantes(Base.metadata, existentes) == []
    existentes["obra"].discard("admite_postventa")
    assert alters_faltantes(Base.metadata, existentes) == [
        "ALTER TABLE obra ADD COLUMN IF NOT EXISTS admite_postventa BOOLEAN "
        "DEFAULT false NOT NULL"]


def test_f025_r21_solo_la_tabla_obra_la_tiene() -> None:
    """R21 · La marca es de la obra, no de la asignación ni de otra tabla."""
    con_marca = {t.name for t in Base.metadata.tables.values()
                 if "admite_postventa" in t.columns}
    assert con_marca == {"obra"}


# --- R15 · el cliente del transfer y el 502 -----------------------------------


class _Respuesta:
    def __init__(self, cuerpo: object, status: int = 200) -> None:
        self._cuerpo = cuerpo
        self.status_code = status
        self.text = str(cuerpo)

    def json(self) -> object:
        if isinstance(self._cuerpo, Exception):
            raise self._cuerpo
        return self._cuerpo


def _cliente(monkeypatch: pytest.MonkeyPatch, respuesta: object) -> tuple:
    """`TransferClient` con `httpx.post` sustituido; apunta lo enviado."""
    from types import SimpleNamespace

    from infrastructure.transfer import transfer_client as modulo

    enviado: list[tuple] = []

    def post(url: str, json: dict, timeout: float) -> _Respuesta:
        enviado.append((url, json, timeout))
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta  # type: ignore[return-value]

    monkeypatch.setattr(modulo.httpx, "post", post)
    ajustes = SimpleNamespace(transfer_base_url="http://transfer.invalid/",
                              transfer_timeout_s=7.0)
    return modulo.TransferClient(ajustes), enviado


OBRAS = [{"ide": 10, "codigo": "0656", "nombre": "TOMARES"},
         {"ide": 11, "codigo": "9999", "nombre": "NADA"}]


def test_f025_r15_el_cliente_pide_el_universo_y_devuelve_los_ides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R15 · Un POST a `/api/postventa/universo` con la empresa y las obras;
    vuelven los `ide` del universo y el motivo."""
    from domain.models import ResultadoUniverso

    cliente, enviado = _cliente(monkeypatch, _Respuesta({
        "ok": True, "empresa": 1, "motivo": None, "casadas": 1,
        "obras": [{"ide": 10, "partida": {"ide": 5, "cod": "0656"}}]}))
    r = cliente.universo_postventa(1, OBRAS)
    assert r == ResultadoUniverso(ides=frozenset({10}), motivo=None)
    assert enviado == [("http://transfer.invalid/api/postventa/universo",
                        {"empresa": 1, "obras": OBRAS}, 7.0)]


def test_f025_r15_el_motivo_del_transfer_llega_sin_universo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R15 · Sin universo (obra de postventa ausente), `ok: true`, `obras`
    vacía y el motivo del transfer: no es un fallo."""
    cliente, _ = _cliente(monkeypatch, _Respuesta({
        "ok": True, "motivo": "obra de postventa no encontrada",
        "obras": []}))
    r = cliente.universo_postventa(1, OBRAS)
    assert r.ides == frozenset() and r.motivo == "obra de postventa no encontrada"


@pytest.mark.parametrize(("respuesta", "causa"), [
    (_Respuesta({"ok": False, "error": "sigrid-api caído"}, 502),
     "sigrid-api caído"),
    (_Respuesta({"ok": True, "motivo": None}), "no trae obras"),
    (_Respuesta({"obras": []}), "no trae obras"),           # sin `ok`
    (_Respuesta({"ok": "true", "obras": []}), "no trae obras"),
    (_Respuesta(ValueError("no es JSON"), 500), "transfer HTTP 500"),
], ids=["ok-false", "sin-obras", "sin-ok", "ok-texto", "no-json"])
def test_f025_r15_respuesta_no_valida_es_universo_no_disponible(
    monkeypatch: pytest.MonkeyPatch, respuesta: _Respuesta, causa: str
) -> None:
    """R15 · `ok` que no es `true` o sin `obras`: el universo no está
    disponible, y el error lo nombra y dice la causa."""
    from domain.errors import UniversoPostventaNoDisponible

    cliente, _ = _cliente(monkeypatch, respuesta)
    with pytest.raises(UniversoPostventaNoDisponible) as fallo:
        cliente.universo_postventa(1, OBRAS)
    assert str(fallo.value).startswith(
        "universo de postventa no disponible: ")
    assert causa in str(fallo.value)


def test_f025_r15_transfer_caido_es_universo_no_disponible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R15 · Transfer inaccesible: mismo error, con la causa."""
    import httpx
    from domain.errors import UniversoPostventaNoDisponible

    cliente, _ = _cliente(monkeypatch, httpx.ConnectError("sin red"))
    with pytest.raises(UniversoPostventaNoDisponible, match="sin red"):
        cliente.universo_postventa(1, OBRAS)


def test_f025_r15_el_error_es_de_dominio_y_se_traduce_a_502() -> None:
    """R15 · `UniversoPostventaNoDisponible` es un error de dominio y la
    tabla de la app lo traduce a 502."""
    from domain.errors import ErrorDominio, UniversoPostventaNoDisponible
    from interface_adapters.api.app import _HTTP_POR_ERROR

    assert issubclass(UniversoPostventaNoDisponible, ErrorDominio)
    assert (UniversoPostventaNoDisponible, 502) in _HTTP_POR_ERROR
