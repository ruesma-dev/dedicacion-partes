# tests/test_f039_sync_var.py
"""Tests offline de F-039 en la api: filtro de código de obra, universo VAR y
entradas `VAR-NN` en el sync y el preview (R10-R18).

Trazabilidad con `specs/F-039-obras-var-y-seis-digitos/requirements.md`. La
regla es `docs/ARCHITECTURE.md#regla-var` y `#regla-seis-digitos`. El
universo VAR lo calcula SOLO el transfer: aquí se sustituye por el doble
`UniversoFalso` de `tests/conftest.py`. Nada abre un socket ni una conexión.
"""
from __future__ import annotations

import dataclasses

import pytest
from infrastructure.db.orm_models import Base, ObraORM
from sqlalchemy.dialects import postgresql

DIALECTO = postgresql.dialect()


# --- R10 · reglas puras del código de obra (domain/obras.py) ------------------


@pytest.mark.parametrize(("cod", "cae"), [
    ("150414", True), ("0902051", True), ("090205A", True),
    ("150301-1", True), ("160304-LOCAL", True), ("160310 ", True),
    ("A123456", True), ("12345", False), ("VAR", False), ("0678", False),
    ("12345-12345", False), ("", False), (None, False),
])
def test_f039_r10_tiene_digitos_seguidos(cod: str | None, cae: bool) -> None:
    """R10 · Cae la obra cuyo código CONTIENE 6 o más dígitos seguidos,
    lleve o no letras o sufijo; con menos, o partidos, no."""
    from domain.obras import tiene_digitos_seguidos

    assert tiene_digitos_seguidos(cod, 6) is cae


@pytest.mark.parametrize("n", [0, -1])
def test_f039_r10_sin_filtro_con_n_cero_o_negativo(n: int) -> None:
    """R10 · `N <= 0` = sin filtro: ningún código cae."""
    from domain.obras import tiene_digitos_seguidos

    assert tiene_digitos_seguidos("150414", n) is False


def test_f039_r10_el_umbral_es_el_que_se_pasa() -> None:
    """R10 · Con N = 5, `12345` cae; con N = 7, `150414` no."""
    from domain.obras import tiene_digitos_seguidos

    assert tiene_digitos_seguidos("12345", 5) is True
    assert tiene_digitos_seguidos("1234", 5) is False
    assert tiene_digitos_seguidos("150414", 7) is False


# --- R13 · la entrada VAR: código e ide (D2, D6) -----------------------------


@pytest.mark.parametrize(("obra", "partida", "codigo"), [
    ("VAR", "29", "VAR-29"), ("VAR", "29.1", "VAR-29.1"),
    (" VAR ", " 100 ", "VAR-100"),
])
def test_f039_r13_codigo_de_la_entrada(obra: str, partida: str,
                                       codigo: str) -> None:
    """R13 · `<código de la obra VAR>-<código de la partida>`, sin
    espacios de relleno (D2)."""
    from domain.obras import codigo_entrada

    assert codigo_entrada(obra, partida) == codigo


def test_f039_r13_ide_de_la_entrada_es_el_de_la_partida_en_negativo() -> None:
    """R13 · `ide` = −(ide de la partida): no choca con ninguna obra (D6)."""
    from domain.obras import ide_entrada

    assert ide_entrada(417055) == -417055
    assert ide_entrada("417055") == -417055  # type: ignore[arg-type]


def test_f039_r13_el_resultado_del_universo_var_es_inmutable() -> None:
    """R13 · `PartidaVar` y `ResultadoUniversoVar`, inmutables."""
    from domain.models import PartidaVar, ResultadoUniversoVar

    p = PartidaVar(ide=417055, cod="29", res="NAVE")
    r = ResultadoUniversoVar(obra_ide=683806, obra_cod="VAR", empresa=1,
                             partidas=(p,), motivo=None)
    assert r.partidas[0].cod == "29" and r.motivo is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.motivo = "x"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.cod = "30"  # type: ignore[misc]


# --- R16 · el error y su 502 -------------------------------------------------


def test_f039_r16_el_error_es_de_dominio_y_se_traduce_a_502() -> None:
    """R16 · `UniversoVarNoDisponible` es un error de dominio y la tabla de
    la app lo traduce a 502."""
    from domain.errors import ErrorDominio, UniversoVarNoDisponible
    from interface_adapters.api.app import _HTTP_POR_ERROR

    assert issubclass(UniversoVarNoDisponible, ErrorDominio)
    assert (UniversoVarNoDisponible, 502) in _HTTP_POR_ERROR


def test_f039_r16_el_puerto_de_los_dos_universos() -> None:
    """R16 · `UniversosGateway` reúne los dos puertos; el transfer es UNO."""
    from domain.ports import (
        UniversoPostventaGateway,
        UniversosGateway,
        UniversoVarGateway,
    )

    assert UniversoPostventaGateway in UniversosGateway.__mro__
    assert UniversoVarGateway in UniversosGateway.__mro__
    assert hasattr(UniversoVarGateway, "universo_var")


# --- R18 · las tres columnas, solo en el ORM y con su ALTER derivado ---------

COLUMNAS_R18 = {"registro_obra_ide": "BIGINT", "registro_obra_cod": "TEXT",
                "registro_paride": "BIGINT"}


@pytest.mark.parametrize(("columna", "tipo"), sorted(COLUMNAS_R18.items()))
def test_f039_r18_columnas_nulables_sin_default(columna: str,
                                                tipo: str) -> None:
    """R18 · Nulables, sin default (las obras normales llevan `NULL`)."""
    c = ObraORM.__table__.columns[columna]
    assert c.type.compile(dialect=DIALECTO) == tipo
    assert c.nullable is True
    assert c.default is None and c.server_default is None


def test_f039_r18_el_alter_lo_deriva_esquema() -> None:
    """R18 · Sobre una base sin las columnas, `alters_faltantes` deriva los
    tres `ADD COLUMN`; con ellas, nada."""
    from infrastructure.db.esquema import alters_faltantes

    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()}
    assert alters_faltantes(Base.metadata, existentes) == []
    existentes["obra"] -= set(COLUMNAS_R18)
    assert sorted(alters_faltantes(Base.metadata, existentes)) == sorted(
        f"ALTER TABLE obra ADD COLUMN IF NOT EXISTS {c} {t}"
        for c, t in COLUMNAS_R18.items())


def test_f039_r18_solo_la_tabla_obra_las_tiene() -> None:
    """R18 · Son de la obra (la entrada), no de la asignación."""
    for columna in COLUMNAS_R18:
        con = {t.name for t in Base.metadata.tables.values()
               if columna in t.columns}
        assert con == {"obra"}, columna


# --- R16 · el cliente del transfer: universo_var -----------------------------


def _cliente(monkeypatch: pytest.MonkeyPatch, respuesta: object) -> tuple:
    """`TransferClient` con `httpx.post` sustituido (dobles de F-025)."""
    from tests.test_f025_sync_postventa import _cliente as cliente_f025

    return cliente_f025(monkeypatch, respuesta)


def _resp(cuerpo: object, status: int = 200) -> object:
    from tests.test_f025_sync_postventa import _Respuesta

    return _Respuesta(cuerpo, status)


CUERPO_VAR = {
    "ok": True, "empresa": 1, "desde": 29, "motivo": None,
    "obra_var": {"ide": 683806, "codigo": "VAR", "nombre": "OBRAS VARIAS",
                 "empresa": 1},
    "partidas": [{"ide": 417055, "cod": "29", "res": "NAVE ARROYOMOLINOS"},
                 {"ide": 417057, "cod": "30", "res": None}]}


def test_f039_r16_el_cliente_pide_el_universo_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R12, R16 · Un POST a `/api/var/universo` con la empresa; vuelven la
    obra VAR y sus partidas."""
    from domain.models import PartidaVar, ResultadoUniversoVar

    cliente, enviado = _cliente(monkeypatch, _resp(CUERPO_VAR))
    r = cliente.universo_var(1)
    assert r == ResultadoUniversoVar(
        obra_ide=683806, obra_cod="VAR", empresa=1, motivo=None,
        partidas=(PartidaVar(417055, "29", "NAVE ARROYOMOLINOS"),
                  PartidaVar(417057, "30", None)))
    assert enviado == [("http://transfer.invalid/api/var/universo",
                        {"empresa": 1}, 7.0)]


def test_f039_r16_sin_obra_var_no_es_un_fallo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R3, R16 · `ok: true`, `obra_var` nula y sin partidas: resultado sin
    obra, con el motivo del transfer."""
    cliente, _ = _cliente(monkeypatch, _resp({
        "ok": True, "empresa": 1, "obra_var": None, "partidas": [],
        "motivo": "obra VAR no encontrada"}))
    r = cliente.universo_var(1)
    assert (r.obra_ide, r.obra_cod, r.empresa, r.partidas) == (
        None, None, None, ())
    assert r.motivo == "obra VAR no encontrada"


@pytest.mark.parametrize(("cuerpo", "status", "causa"), [
    ({"ok": False, "error": "sigrid-api caído"}, 502, "sigrid-api caído"),
    ({"ok": True, "motivo": None, "obra_var": None}, 200,
     "la respuesta del transfer no trae partidas"),
    ({"partidas": []}, 200, "la respuesta del transfer no trae partidas"),
    ({"ok": "true", "partidas": []}, 200,
     "la respuesta del transfer no trae partidas"),
    (ValueError("no es JSON"), 500, "transfer HTTP 500: no es JSON"),
], ids=["ok-false", "sin-partidas", "sin-ok", "ok-texto", "no-json"])
def test_f039_r16_respuesta_no_valida_es_universo_var_no_disponible(
    monkeypatch: pytest.MonkeyPatch, cuerpo: object, status: int, causa: str
) -> None:
    """R16 · `ok` que no es `true` o sin `partidas`: no hay universo VAR, y
    el error lo nombra y dice la causa."""
    from domain.errors import UniversoVarNoDisponible

    cliente, _ = _cliente(monkeypatch, _resp(cuerpo, status))
    with pytest.raises(UniversoVarNoDisponible) as fallo:
        cliente.universo_var(1)
    assert str(fallo.value) == f"universo VAR no disponible: {causa}"


def test_f039_r16_transfer_caido_es_universo_var_no_disponible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R16 · Transfer inaccesible: mismo error, con la causa."""
    import httpx
    from domain.errors import UniversoVarNoDisponible

    cliente, _ = _cliente(monkeypatch, httpx.ConnectError("sin red"))
    with pytest.raises(UniversoVarNoDisponible, match="sin red"):
        cliente.universo_var(1)


# --- R10-R17 · el sync y el preview -----------------------------------------
#
# Obras de Sigrid (empresa de las obras = 1):
#   1 · 150414        EN ESTUDIO, «casaría» en postventa → cae por código
#   2 · 0902051       EN ESTUDIO                         → cae
#   3 · 090205A       ADJUDICADA                         → cae
#   4 · 150301-1      EN CURSO                           → cae
#   7 · "160310 "     EN CURSO (relleno)                 → cae
#   5 · 12345         EN CURSO                           → activa
#   6 · 0678          CERRADA, en el universo de postventa → solo postventa
#   683806 · VAR      EN CURSO                           → no activa (D1)
# Universo VAR: la 29 (417055) y la 30 (417057).

SQL_EMP = "SELECT ... FROM dbo.emp AS emp"
SQL_OBR = "SELECT ... FROM dbo.obr AS obr"
VAR_IDE = 683806
DESCARTADAS = ["150414", "0902051", "090205A", "150301-1", "160310 "]


def _o(ide: int, cod: str, estado: str = "EN CURSO", empresa: int = 1) -> dict:
    return {"ide": ide, "cod": cod, "descripcion": f"OBRA {ide}",
            "estado_sigrid": estado, "empresa": empresa}


def _obras_sigrid() -> list[dict]:
    return [_o(1, "150414", "EN ESTUDIO"), _o(2, "0902051", "EN ESTUDIO"),
            _o(3, "090205A", "ADJUDICADA DEF."), _o(4, "150301-1"),
            _o(7, "160310 "), _o(5, "12345"), _o(6, "0678", "CERRADA"),
            _o(VAR_IDE, "VAR")]


def _uvar(**cambios: object):
    from domain.models import PartidaVar, ResultadoUniversoVar

    datos: dict = {"obra_ide": VAR_IDE, "obra_cod": "VAR", "empresa": 1,
                   "motivo": None, "partidas": (
                       PartidaVar(417055, "29", "ACOND. NAVE MODUL-A"),
                       PartidaVar(417057, "30", None))}
    datos.update(cambios)
    return ResultadoUniversoVar(**datos)


SIN_VAR = {"obra_ide": None, "obra_cod": None, "empresa": None,
           "partidas": ()}


def _universo(**cambios: object):
    from tests.conftest import UniversoFalso

    return UniversoFalso(**({"ides": (1, 6), "var": _uvar()} | cambios))


def _sigrid(obras: list[dict] | None = None):
    from tests.test_f023_sync_empresa import _emp, _SigridFalso

    return _SigridFalso([_emp(1)], _obras_sigrid() if obras is None else obras)


def _pipeline(sigrid, universo, empresa_obras: int = 1, digitos: int = 6):
    from application import sync_pipeline as sp

    return sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, SQL_EMP),
        sp.FetchObrasStep(sigrid, SQL_OBR, ["cerrada"], universo=universo,
                          empresa_obras=empresa_obras,
                          digitos_excluidos=digitos),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
    ])


def _preview(sigrid, universo, empresa_obras: int = 1, digitos: int = 6):
    from application.use_cases import PreviewSync

    return PreviewSync(sigrid, SQL_EMP, SQL_OBR, estados_excluidos=["cerrada"],
                       universo=universo, empresa_obras=empresa_obras,
                       digitos_excluidos=digitos)


def _sync(obras: list[dict] | None = None, digitos: int = 6, **doble) -> tuple:
    from tests.test_f023_sync_empresa import _UowEspia

    universo = _universo(**doble)
    uow = _UowEspia()
    _pipeline(_sigrid(obras), universo, digitos=digitos).ejecutar(uow)
    return universo, uow


def _por_ide(filas: list[dict]) -> dict[int, dict]:
    return {f["ide"]: f for f in filas}


def test_f039_r10_r11_el_sync_descarta_por_codigo_antes_del_universo() -> None:
    """R10-R11 · Las obras con 6+ dígitos seguidos ni van al universo de
    postventa (aunque «casaran») ni llegan al repositorio."""
    universo, uow = _sync()
    assert [o["ide"] for o in universo.llamadas[0][1]] == [5, 6, VAR_IDE]
    assert set(_por_ide(uow.obras.recibido)) == {
        5, 6, VAR_IDE, -417055, -417057}


def test_f039_r10_sin_filtro_no_se_descarta_nada() -> None:
    """R10 · `digitos_seguidos_excluidos: 0` (o el defecto del step y del
    preview): sin filtro, como antes de F-039."""
    from application import sync_pipeline as sp
    from application.use_cases import PreviewSync

    from tests.test_f023_sync_empresa import _UowEspia

    _, uow = _sync(digitos=0)
    assert {1, 2, 3, 4, 7} <= set(_por_ide(uow.obras.recibido))
    uow = _UowEspia()
    sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(_sigrid(), SQL_EMP),
        sp.FetchObrasStep(_sigrid(), SQL_OBR, universo=_universo(),
                          empresa_obras=1),
        sp.UpsertTrabajadoresStep(), sp.UpsertObrasStep(),
    ]).ejecutar(uow)
    assert {1, 2, 3, 4, 7} <= set(_por_ide(uow.obras.recibido))
    obr = PreviewSync(_sigrid(), SQL_EMP, SQL_OBR, universo=_universo(),
                      empresa_obras=1).ejecutar()["obras"]
    assert obr["excluidas_por_codigo"] == 0
    assert obr["muestra_excluidas_por_codigo"] == []


def test_f039_r12_el_universo_var_se_pide_una_vez_con_la_empresa_de_las_obras(
) -> None:
    """R12 · Una sola petición del universo VAR, con la empresa de las obras
    (y una del de postventa, como hoy)."""
    from tests.test_f023_sync_empresa import _UowEspia

    universo, _ = _sync()
    assert universo.llamadas_var == [1] and len(universo.llamadas) == 1
    otro = _universo()
    _pipeline(_sigrid(), otro, empresa_obras=28).ejecutar(_UowEspia())
    assert otro.llamadas_var == [28]


def test_f039_r13_cada_partida_var_es_una_fila_de_obra() -> None:
    """R13 · Una fila por partida, con `ide` negativo, código `VAR-NN`, su
    descripción, la empresa de la obra VAR, activa, sin postventa y la obra
    y partida de registro (D2, D6)."""
    _, uow = _sync()
    filas = _por_ide(uow.obras.recibido)
    assert filas[-417055] == {
        "ide": -417055, "cod": "VAR-29", "descripcion": "ACOND. NAVE MODUL-A",
        "empresa": 1, "estado_sigrid": None, "activa": True,
        "admite_postventa": False, "registro_obra_ide": VAR_IDE,
        "registro_obra_cod": "VAR", "registro_paride": 417055}
    assert filas[-417057]["cod"] == "VAR-30"
    assert filas[-417057]["descripcion"] is None
    assert all("registro_paride" not in f for i, f in filas.items() if i > 0)


def test_f039_r13_la_empresa_de_la_entrada_es_la_de_la_obra_var() -> None:
    """R13 · La empresa de cada entrada es la de la obra VAR del universo."""
    from application.filtros_maestros import entradas_var

    filas = entradas_var(_uvar(empresa=25))
    assert [f["empresa"] for f in filas] == [25, 25]
    assert entradas_var(_uvar(**SIN_VAR, motivo="x")) == []


def test_f039_r13_sin_obra_var_no_hay_entradas() -> None:
    """R3, R13 · Sin obra VAR en el universo, ninguna entrada, y la obra
    VAR (si llega) se trata como cualquier otra."""
    _, uow = _sync(var=_uvar(**SIN_VAR, motivo="no encontrada"))
    filas = _por_ide(uow.obras.recibido)
    assert set(filas) == {5, 6, VAR_IDE}
    assert filas[VAR_IDE]["activa"] is True


@pytest.mark.parametrize("estado", ["EN CURSO", "CERRADA"])
def test_f039_r14_la_obra_var_se_guarda_no_activa(estado: str) -> None:
    """R14 · La obra VAR se guarda con `activa = false`, sea cual sea su
    estado (D1); no cuenta como excluida ni como «solo postventa»."""
    from application.filtros_maestros import depurar_obras

    obras = [o if o["ide"] != VAR_IDE else _o(VAR_IDE, "VAR", estado)
             for o in _obras_sigrid()]
    _, uow = _sync(obras)
    var = _por_ide(uow.obras.recibido)[VAR_IDE]
    assert (var["activa"], var["admite_postventa"]) == (False, False)
    r = depurar_obras([_o(VAR_IDE, "VAR", estado), _o(9, "0009", "CERRADA")],
                      ["cerrada"], True, frozenset({9}),
                      frozenset({VAR_IDE}))
    assert (r.excluidos_filtro, r.solo_postventa, len(r.filas)) == (0, 1, 2)


def test_f039_r14_la_obra_var_conserva_su_postventa() -> None:
    """R14 · No ofrecerla como normal no le quita la marca de postventa si
    está en ese universo (son modos independientes, F-025)."""
    _, uow = _sync(ides=(1, 6, VAR_IDE))
    var = _por_ide(uow.obras.recibido)[VAR_IDE]
    assert (var["activa"], var["admite_postventa"]) == (False, True)


def test_f039_r16_sin_universo_var_el_sync_falla_sin_persistir() -> None:
    """R16 · Sin universo VAR, el sync entero falla: nada llega al
    repositorio y no hay `commit` (como F-025 D3); el preview, igual."""
    from domain.errors import UniversoVarNoDisponible

    from tests.test_f023_sync_empresa import _UowEspia

    uow = _UowEspia()
    universo = _universo(fallo_var=UniversoVarNoDisponible("caído"))
    with pytest.raises(UniversoVarNoDisponible):
        _pipeline(_sigrid(), universo).ejecutar(uow)
    assert uow.trabajadores.recibido is None and uow.obras.recibido is None
    assert uow.commits == 0
    with pytest.raises(UniversoVarNoDisponible):
        _preview(_sigrid(), universo).ejecutar()


def test_f039_r16_el_sync_por_http_responde_502_nombrando_el_universo_var(
) -> None:
    """R16 · `POST /api/v1/sync` sin universo VAR: 502 y el error lo dice."""
    from types import SimpleNamespace

    from config.settings import Settings
    from domain.errors import UniversoVarNoDisponible
    from fastapi.testclient import TestClient
    from interface_adapters.api.app import build_app
    from interface_adapters.api.deps import obtener_contenedor

    from tests.test_f023_sync_empresa import _UowEspia

    class _Uow(_UowEspia):
        def __enter__(self):
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    uow = _Uow()
    universo = _universo(fallo_var=UniversoVarNoDisponible(
        "universo VAR no disponible: transfer inaccesible"))
    contenedor = SimpleNamespace(sync_pipeline=_pipeline(_sigrid(), universo),
                                 uow=lambda: uow)
    app = build_app(Settings(_env_file=None))
    app.dependency_overrides[obtener_contenedor] = lambda: contenedor
    r = TestClient(app).post("/api/v1/sync")
    assert r.status_code == 502, r.text
    assert r.json() == {
        "error": "universo VAR no disponible: transfer inaccesible"}
    assert uow.commits == 0


def test_f039_r17_el_preview_publica_codigo_y_var() -> None:
    """R17 · El preview publica las excluidas por código (y su muestra), las
    entradas VAR, la obra VAR y su motivo; lo que enseña es lo que guarda."""
    universo = _universo()
    obr = _preview(_sigrid(), universo).ejecutar()["obras"]
    assert obr["excluidas_por_codigo"] == 5
    assert obr["muestra_excluidas_por_codigo"] == DESCARTADAS
    assert obr["entradas_var"] == 2
    assert obr["obra_var"] == "VAR" and obr["motivo_var"] is None
    assert obr["brutas"] == 8
    sync_universo, uow = _sync()
    assert obr["total"] == len(uow.obras.recibido) == 5
    assert universo.llamadas_var == [1] and len(universo.llamadas) == 1
    assert universo.llamadas == sync_universo.llamadas


def test_f039_r17_sin_obra_var_el_preview_publica_el_motivo() -> None:
    """R17 · Sin obra VAR: `obra_var` nulo, cero entradas y el motivo."""
    motivo = "obra VAR no encontrada en Sigrid en la empresa 1"
    obr = _preview(_sigrid(), _universo(var=_uvar(
        **SIN_VAR, motivo=motivo))).ejecutar()["obras"]
    assert (obr["obra_var"], obr["entradas_var"]) == (None, 0)
    assert obr["motivo_var"] == motivo


def test_f039_r17_la_muestra_de_excluidas_llega_a_diez() -> None:
    """R17 · La muestra de excluidas por código, hasta 10 códigos."""
    obras = [_o(100 + i, f"2401{i:02d}") for i in range(12)]
    obr = _preview(_sigrid(obras), _universo()).ejecutar()["obras"]
    assert obr["excluidas_por_codigo"] == 12
    assert obr["muestra_excluidas_por_codigo"] == [
        f"2401{i:02d}" for i in range(10)]


# --- R11, R13, R15 · el repositorio ------------------------------------------


def _fila_entrada(paride: int = 417055, **cambios: object) -> dict:
    fila = {"ide": -paride, "cod": "VAR-29", "descripcion": "NAVE",
            "empresa": 1, "estado_sigrid": None, "activa": True,
            "admite_postventa": False, "registro_obra_ide": VAR_IDE,
            "registro_obra_cod": "VAR", "registro_paride": paride}
    fila.update(cambios)
    return fila


def _orm_entrada(paride: int = 417055, **cambios: object) -> ObraORM:
    datos = _fila_entrada(paride)
    datos.update(cambios)
    return ObraORM(**datos)


def test_f039_r13_el_repositorio_guarda_las_tres_columnas_en_el_alta() -> None:
    """R13 · Alta de la entrada con su obra y partida de registro; una obra
    normal, con las tres a `NULL`."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    sesion = _SesionRepo()
    normal = {**_o(5, "12345"), "activa": True, "admite_postventa": False}
    res = PgObraRepository(sesion).sincronizar([_fila_entrada(), normal])
    assert res.altas == 2
    por_ide = {o.ide: o for o in sesion.anadidas}
    e = por_ide[-417055]
    assert (e.cod, e.activa, e.registro_obra_ide, e.registro_obra_cod,
            e.registro_paride) == ("VAR-29", True, VAR_IDE, "VAR", 417055)
    n = por_ide[5]
    assert (n.registro_obra_ide, n.registro_obra_cod,
            n.registro_paride) == (None, None, None)


@pytest.mark.parametrize(("campo", "valor"), [
    ("registro_obra_ide", 999), ("registro_obra_cod", "VAR2"),
    ("registro_paride", 417099)])
def test_f039_r13_cambiar_una_columna_de_registro_cuenta(
    campo: str, valor: object
) -> None:
    """R13 · Si cambia la obra o la partida de registro, se actualiza y
    cuenta; si no cambia nada, no."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    existente = _orm_entrada()
    res = PgObraRepository(_SesionRepo([existente])).sincronizar(
        [_fila_entrada(**{campo: valor})])
    assert (res.altas, res.actualizados) == (0, 1)
    assert getattr(existente, campo) == valor
    igual = _orm_entrada()
    res = PgObraRepository(_SesionRepo([igual])).sincronizar(
        [_fila_entrada()])
    assert res.actualizados == 0


def test_f039_r15_la_entrada_que_sale_del_universo_queda_inactiva() -> None:
    """R15 · La partida que deja de estar en el universo: su entrada queda
    `activa = false` en el sync siguiente, sin borrar nada."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    sigue, sale = _orm_entrada(417055), _orm_entrada(417057, cod="VAR-30")
    sesion = _SesionRepo([sigue, sale])
    res = PgObraRepository(sesion).sincronizar([_fila_entrada(417055)])
    assert res.desactivados == 1
    assert (sale.activa, sale.admite_postventa) == (False, False)
    assert sale.registro_paride == 417057 and sigue.activa is True


def test_f039_r11_la_obra_de_seis_digitos_ya_guardada_queda_sin_marcas() -> None:
    """R11 · Si la obra descartada por código ya estaba en la base, queda
    con `activa` y `admite_postventa` a `false` (no se borra)."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    vieja = ObraORM(ide=1, cod="150414", descripcion="OBRA 1",
                    estado_sigrid="EN ESTUDIO", activa=True, empresa=1,
                    admite_postventa=True)
    _, uow = _sync()
    PgObraRepository(_SesionRepo([vieja])).sincronizar(uow.obras.recibido)
    assert (vieja.activa, vieja.admite_postventa) == (False, False)


# --- R10 · deps.py y config.yaml --------------------------------------------


def test_f039_r10_config_yaml_declara_seis() -> None:
    """R10 · El número vive en `config.yaml` (D4: 6)."""
    from config.settings import cargar_config

    assert cargar_config()["sync"]["obras"]["digitos_seguidos_excluidos"] == 6


@pytest.mark.parametrize(("digitos", "quedan"), [
    (6, {5, 6, VAR_IDE, -417055, -417057}),
    (None, {1, 2, 3, 4, 5, 6, 7, VAR_IDE, -417055, -417057}),
], ids=["con-6", "sin-clave"])
def test_f039_r10_el_contenedor_pasa_el_numero_al_step_y_al_preview(
    monkeypatch: pytest.MonkeyPatch, digitos: int | None, quedan: set
) -> None:
    """R10, R12 · `deps.py` lee el número de `config.yaml` (sin la clave, sin
    filtro) y se lo da al step y al preview; el `TransferClient` sigue
    siendo UNO y hace de los dos universos."""
    from config.settings import Settings
    from interface_adapters.api import deps

    from tests.test_f023_sync_empresa import (
        _config_prueba,
        _UowEspia,
        _UowLectura,
    )

    config = _config_prueba({})
    config["sync"]["obras"]["estados_excluidos"] = ["cerrada"]
    if digitos is not None:
        config["sync"]["obras"]["digitos_seguidos_excluidos"] = digitos
    creados: list = []

    def fabrica(_settings: object):
        creados.append(_universo())
        return creados[-1]

    monkeypatch.setattr(deps, "cargar_config", lambda: config)
    monkeypatch.setattr(deps, "TransferClient", fabrica)
    monkeypatch.setattr(deps, "SqlAlchemyUnitOfWork", _UowLectura)
    monkeypatch.setattr(deps, "SigridApiClient", lambda _s: _sigrid())
    contenedor = deps.construir_contenedor(Settings(_env_file=None), None)
    uow = _UowEspia()
    contenedor.sync_pipeline.ejecutar(uow)
    obr = contenedor.preview_sync.ejecutar()["obras"]
    assert set(_por_ide(uow.obras.recibido)) == quedan
    assert obr["total"] == len(quedan)
    assert len(creados) == 1 and creados[0].llamadas_var == [1, 1]
    assert contenedor.registro_sigrid._transfer is creados[0]
