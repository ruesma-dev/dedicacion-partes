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


# --- R12-R16 · el sync pide el universo y guarda las dos marcas ---------------
#
# Obras de Sigrid de los tests (empresa de las obras = 1):
#   10 · CERRADA y en el universo      → solo postventa (activa=F, admite=T)
#   11 · CERRADA y fuera del universo  → descartada, como hoy (R14)
#   12 · EN CURSO y en el universo     → activa=T, admite=T
#   13 · EN CURSO y fuera              → activa=T, admite=F
#   14 · EN CURSO, empresa "1" en texto → cuenta como de la 1 (fuera)
#   20 · EN CURSO de la 28             → no va al transfer; activa=T, admite=F
# El doble sabe que 10, 12 y 20 «casarían»: 20 no sale porque no se pide.

SQL_EMP = "SELECT ... FROM dbo.emp AS emp"
SQL_OBR = "SELECT ... FROM dbo.obr AS obr"
UNIVERSO = (10, 12, 20)


def _o(ide: int, estado: str = "EN CURSO", empresa: object = 1,
       cod: str | None = None, descripcion: str | None = None) -> dict:
    return {"ide": ide, "cod": cod or f"0{ide}",
            "descripcion": descripcion or f"OBRA {ide}",
            "estado_sigrid": estado, "empresa": empresa}


def _obras_sigrid() -> list[dict]:
    return [_o(10, "CERRADA"), _o(11, "CERRADA"), _o(12), _o(13),
            _o(14, empresa="1"), _o(20, empresa=28)]


def _sigrid(obras: list[dict] | None = None):
    from tests.test_f023_sync_empresa import _SigridFalso, _emp

    return _SigridFalso([_emp(1)], _obras_sigrid() if obras is None else obras)


def _pipeline(sigrid, universo, empresa_obras: int = 1):
    from application import sync_pipeline as sp

    return sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, SQL_EMP),
        sp.FetchObrasStep(sigrid, SQL_OBR, ["cerrada"], universo=universo,
                          empresa_obras=empresa_obras),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
    ])


def _preview(sigrid, universo, empresa_obras: int = 1):
    from application.use_cases import PreviewSync

    return PreviewSync(sigrid, SQL_EMP, SQL_OBR, estados_excluidos=["cerrada"],
                       universo=universo, empresa_obras=empresa_obras)


def _sync(obras: list[dict] | None = None, **doble) -> tuple:
    from tests.conftest import UniversoFalso
    from tests.test_f023_sync_empresa import _UowEspia

    universo = UniversoFalso(**({"ides": UNIVERSO} | doble))
    uow = _UowEspia()
    _pipeline(_sigrid(obras), universo).ejecutar(uow)
    return universo, uow


def _marcas(filas: list[dict]) -> dict[int, tuple[bool, bool]]:
    return {f["ide"]: (f["activa"], f["admite_postventa"]) for f in filas}


def test_f025_r12_el_sync_pide_el_universo_una_vez_con_la_empresa_de_las_obras(
) -> None:
    """R12 · Una sola petición, con la empresa de las obras y TODAS sus obras
    leídas (también las cerradas); la de la 28, no."""
    universo, _ = _sync()
    assert universo.llamadas == [(1, [
        {"ide": i, "codigo": f"0{i}", "nombre": f"OBRA {i}"}
        for i in (10, 11, 12, 13, 14)])]


def test_f025_r12_la_empresa_de_las_obras_es_la_configurada() -> None:
    """R12 · Con otra empresa de las obras, se manda esa y sus obras."""
    from tests.conftest import UniversoFalso
    from tests.test_f023_sync_empresa import _UowEspia

    universo = UniversoFalso(ides=UNIVERSO)
    _pipeline(_sigrid(), universo, empresa_obras=28).ejecutar(_UowEspia())
    assert universo.llamadas == [(28, [
        {"ide": 20, "codigo": "020", "nombre": "OBRA 20"}])]


def test_f025_r12_lo_que_se_manda_es_lo_que_se_guarda() -> None:
    """R12 · El `codigo` y el `nombre` que viajan son el `cod` y la
    `descripcion` que el repositorio guarda (y que el preflight recibirá):
    sin espacios de relleno y, sin descripción, cadena vacía."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    obras = [_o(10, cod=" 0656 ", descripcion="  TOMARES "),
             {**_o(12), "descripcion": None}]
    universo, uow = _sync(obras)
    enviadas = {o["ide"]: (o["codigo"], o["nombre"])
                for o in universo.llamadas[0][1]}
    sesion = _SesionRepo()
    PgObraRepository(sesion).sincronizar(uow.obras.recibido)
    guardadas = {o.ide: (o.cod, o.descripcion) for o in sesion.anadidas}
    assert enviadas == guardadas == {10: ("0656", "TOMARES"), 12: ("012", "")}


def test_f025_r13_r14_el_sync_marca_activa_y_admite_postventa() -> None:
    """R13-R14 · Cada obra sale con sus dos marcas, independientes; la
    cerrada fuera del universo no se recibe; la de otra empresa nunca
    admite postventa aunque el transfer la hubiera casado."""
    _, uow = _sync()
    assert _marcas(uow.obras.recibido) == {
        10: (False, True), 12: (True, True), 13: (True, False),
        14: (True, False), 20: (True, False)}


def test_f025_r13_sin_filtro_de_estados_todas_son_activas() -> None:
    """R13 · `activa` la sigue decidiendo solo el filtro de estado: sin él,
    la cerrada es activa y además admite postventa si está en el universo."""
    from application import sync_pipeline as sp

    from tests.conftest import UniversoFalso
    from tests.test_f023_sync_empresa import _UowEspia

    uow = _UowEspia()
    sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(_sigrid(), SQL_EMP),
        sp.FetchObrasStep(_sigrid(), SQL_OBR, ["cerrada"], False,
                          universo=UniversoFalso(ides=UNIVERSO),
                          empresa_obras=1),
        sp.UpsertTrabajadoresStep(), sp.UpsertObrasStep(),
    ]).ejecutar(uow)
    assert _marcas(uow.obras.recibido)[10] == (True, True)
    assert _marcas(uow.obras.recibido)[11] == (True, False)


def _orm(ide: int, activa: bool, admite: bool) -> ObraORM:
    return ObraORM(ide=ide, cod=f"0{ide}", descripcion=f"OBRA {ide}",
                   estado_sigrid="EN CURSO", activa=activa, empresa=1,
                   admite_postventa=admite)


def _fila_repo(ide: int, activa: bool, admite: bool) -> dict:
    return {**_o(ide), "activa": activa, "admite_postventa": admite}


def test_f025_r13_el_repositorio_guarda_las_dos_marcas_en_el_alta() -> None:
    """R13 · Alta: `activa` y `admite_postventa` tal y como llegan."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    sesion = _SesionRepo()
    res = PgObraRepository(sesion).sincronizar([
        _fila_repo(10, False, True), _fila_repo(13, True, False)])
    assert res.altas == 2
    assert {o.ide: (o.activa, o.admite_postventa)
            for o in sesion.anadidas} == {10: (False, True), 13: (True, False)}


@pytest.mark.parametrize(("previa", "nueva", "actualizados"), [
    ((True, False), (False, True), 1),   # se cierra y entra en el universo
    ((True, False), (True, True), 1),    # solo cambia la postventa
    ((True, True), (False, True), 1),    # solo cambia la activa
    ((False, True), (False, True), 0),   # nada cambia
])
def test_f025_r13_el_repositorio_actualiza_y_cuenta_las_marcas(
    previa: tuple[bool, bool], nueva: tuple[bool, bool], actualizados: int
) -> None:
    """R13 · Cambiar una marca cuenta como actualizado; si no cambia nada,
    no."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    existente = _orm(10, *previa)
    res = PgObraRepository(_SesionRepo([existente])).sincronizar(
        [_fila_repo(10, *nueva)])
    assert (res.altas, res.actualizados, res.desactivados) == (
        0, actualizados, 0)
    assert (existente.activa, existente.admite_postventa) == nueva


@pytest.mark.parametrize("previa", [(True, False), (False, True), (True, True)])
def test_f025_r14_la_obra_no_recibida_queda_sin_ninguna_marca(
    previa: tuple[bool, bool]
) -> None:
    """R14 · La que no llega (cerrada fuera del universo) se trata como hoy:
    `activa` y `admite_postventa` a `false`, y cuenta como desactivada."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    existente = _orm(11, *previa)
    res = PgObraRepository(_SesionRepo([existente])).sincronizar([])
    assert res.desactivados == 1
    assert (existente.activa, existente.admite_postventa) == (False, False)


def test_f025_r14_la_ya_desmarcada_no_cuenta_otra_vez() -> None:
    """R14 · Una obra que ya no tenía ninguna marca no se «desactiva» de
    nuevo."""
    from infrastructure.db.repositories import PgObraRepository

    from tests.test_f023_sync_empresa import _SesionRepo

    res = PgObraRepository(_SesionRepo([_orm(11, False, False)])).sincronizar([])
    assert res.desactivados == 0


def test_f025_r15_transfer_caido_el_sync_falla_sin_persistir() -> None:
    """R15 · Sin universo, el sync entero falla y no persiste nada (D3)."""
    from domain.errors import UniversoPostventaNoDisponible

    with pytest.raises(UniversoPostventaNoDisponible):
        _sync(fallo=UniversoPostventaNoDisponible(
            "universo de postventa no disponible: transfer inaccesible"))


def test_f025_r15_transfer_caido_nada_llega_al_repositorio() -> None:
    """R15 · Ni empleados ni obras llegan al upsert, y no hay `commit`."""
    from domain.errors import UniversoPostventaNoDisponible

    from tests.conftest import UniversoFalso
    from tests.test_f023_sync_empresa import _UowEspia

    uow = _UowEspia()
    universo = UniversoFalso(fallo=UniversoPostventaNoDisponible("caído"))
    with pytest.raises(UniversoPostventaNoDisponible):
        _pipeline(_sigrid(), universo).ejecutar(uow)
    assert uow.trabajadores.recibido is None and uow.obras.recibido is None
    assert uow.commits == 0


def test_f025_r15_el_sync_por_http_responde_502_nombrando_el_universo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R15 · `POST /api/v1/sync` con el transfer caído: 502 y el error dice
    que es el universo de postventa."""
    from types import SimpleNamespace

    from config.settings import Settings
    from domain.errors import UniversoPostventaNoDisponible
    from fastapi.testclient import TestClient
    from interface_adapters.api.app import build_app
    from interface_adapters.api.deps import obtener_contenedor

    from tests.conftest import UniversoFalso
    from tests.test_f023_sync_empresa import _UowEspia

    class _Uow(_UowEspia):
        def __enter__(self):
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    uow = _Uow()
    universo = UniversoFalso(fallo=UniversoPostventaNoDisponible(
        "universo de postventa no disponible: transfer inaccesible"))
    contenedor = SimpleNamespace(sync_pipeline=_pipeline(_sigrid(), universo),
                                 uow=lambda: uow)
    app = build_app(Settings(_env_file=None))
    app.dependency_overrides[obtener_contenedor] = lambda: contenedor
    r = TestClient(app).post("/api/v1/sync")
    assert r.status_code == 502, r.text
    assert r.json() == {
        "error": "universo de postventa no disponible: transfer inaccesible"}
    assert uow.commits == 0


def test_f025_r16_el_preview_publica_el_universo() -> None:
    """R16 · El preview calcula lo mismo que el sync y publica cuántas
    admiten postventa, cuántas SOLO postventa (excluidas por estado y en el
    universo) y `motivo_postventa` nulo cuando hay universo."""
    from tests.conftest import UniversoFalso

    universo = UniversoFalso(ides=UNIVERSO)
    obr = _preview(_sigrid(), universo).ejecutar()["obras"]
    assert obr["admiten_postventa"] == 2
    assert obr["solo_postventa"] == 1
    assert obr["motivo_postventa"] is None
    assert obr["total"] == 5 and obr["brutas"] == 6
    assert obr["excluidas_por_estado"] == {"CERRADA": 1}
    assert obr["por_estado"] == {"EN CURSO": 4, "CERRADA": 1}
    assert _marcas(obr["muestra"]) == {
        10: (False, True), 12: (True, True), 13: (True, False),
        14: (True, False), 20: (True, False)}
    assert universo.llamadas == _sync()[0].llamadas


def test_f025_r16_sin_universo_el_preview_publica_el_motivo() -> None:
    """R16 · Sin universo (p. ej., obra de postventa ausente), el motivo del
    transfer; ninguna admite postventa y la cerrada sale como hoy."""
    from tests.conftest import UniversoFalso

    motivo = "obra de postventa no encontrada en Sigrid en la empresa 1"
    obr = _preview(_sigrid(), UniversoFalso(motivo=motivo)).ejecutar()["obras"]
    assert obr["motivo_postventa"] == motivo
    assert (obr["admiten_postventa"], obr["solo_postventa"]) == (0, 0)
    assert obr["excluidas_por_estado"] == {"CERRADA": 2}


def test_f025_r16_el_preview_falla_igual_sin_transfer() -> None:
    """R16 · Lo mismo que el sync: sin universo, el preview no inventa uno."""
    from domain.errors import UniversoPostventaNoDisponible

    from tests.conftest import UniversoFalso

    universo = UniversoFalso(fallo=UniversoPostventaNoDisponible("caído"))
    with pytest.raises(UniversoPostventaNoDisponible):
        _preview(_sigrid(), universo).ejecutar()


def test_f025_r12_el_contenedor_comparte_un_solo_transfer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R12 · `deps.py` crea UN `TransferClient` para el step, el preview y el
    registro, y les pasa la empresa de las obras (`EMPRESA_IMPUTACION`)."""
    from config.settings import Settings
    from interface_adapters.api import deps

    from tests.conftest import UniversoFalso
    from tests.test_f023_sync_empresa import _UowLectura

    creados: list[UniversoFalso] = []

    def fabrica(_settings: object) -> UniversoFalso:
        creados.append(UniversoFalso())
        return creados[-1]

    monkeypatch.setenv("EMPRESA_IMPUTACION", "7")
    monkeypatch.setattr(deps, "TransferClient", fabrica)
    monkeypatch.setattr(deps, "SqlAlchemyUnitOfWork", _UowLectura)
    monkeypatch.setattr(deps, "SigridApiClient", lambda _s: _sigrid())
    contenedor = deps.construir_contenedor(Settings(_env_file=None), None)
    assert len(creados) == 1
    contenedor.preview_sync.ejecutar()
    assert [e for e, _ in creados[0].llamadas] == [7]
    assert contenedor.registro_sigrid._transfer is creados[0]


def test_f025_r13_el_ide_en_texto_admite_postventa_igual() -> None:
    """R13 · Si Sigrid devolviera el `ide` como texto, la obra tiene que
    entrar en el universo igual: se convierte a entero como en
    `sincronizar`, al pedir el universo y al marcar (review 1, obs. 1)."""
    universo, uow = _sync([{**_o(10, "CERRADA"), "ide": "10"},
                           {**_o(12), "ide": "12"}])
    assert [o["ide"] for o in universo.llamadas[0][1]] == [10, 12]
    assert _marcas(uow.obras.recibido) == {"10": (False, True),
                                           "12": (True, True)}
