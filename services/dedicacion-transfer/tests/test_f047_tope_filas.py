# tests/test_f047_tope_filas.py
"""F-047 · Tope de filas de las lecturas del transfer (obras con más de
2.000 partidas).

Fallo de producción del 2026-10-07: `SigridWriteClient._read` pedía
`max_rows: 2000` fijo y `capitulos_de_obra` lee TODO el presupuesto de la
obra (`obrparpar`) para resolver la partida. La 0696 tiene 3.024 partidas:
sigrid-api devolvía `truncated: true` y el preflight caía con «sigrid-api
devolvio una respuesta truncada».

Trazabilidad con los `acceptance` de F-047 (`harness/features.json`, sdd
false): a1 (tope configurable, 200.000 por defecto, inyectado donde se
construye el cliente y documentado en `.env.example`), a2 (`truncated` sigue
siendo error: nunca se decide con filas parciales, F-037 R7/R16) y a3 (el
tope que se envía, el truncado y una obra con más de 2.000 partidas que
resuelve su partida en el pipeline).

Sin red: `httpx.post` se sustituye por `SigridApiEmulada`, que se comporta
como `POST /api/sql/read` de sigrid-api respecto al tope (devuelve como mucho
`max_rows` filas y marca `truncated` si había más; `azure-apps/sigrid_api.md`
§6.3). Los `ide` son inventados.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ObraEntrada
from infrastructure.sigrid import sigrid_write_client as mod
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

from tests.conftest import (
    OBRA_ORIGEN,
    PRESUPUESTO_ORIGEN,
    ClienteFalso,
    SettingsFalso,
    _fila,
    linea,
)

#: Tope por defecto aprobado por el humano el 2026-10-07 («ponle 200k»).
TOPE_DEFECTO = 200_000
#: Partidas de la 0696 el día del fallo (lectura del líder en Sigrid).
PARTIDAS_0696 = 3_024


class _Respuesta:
    def __init__(self, cuerpo: dict) -> None:
        self.status_code = 200
        self._cuerpo = cuerpo
        self.text = str(cuerpo)

    def json(self) -> dict:
        return self._cuerpo


class SigridApiEmulada:
    """`POST /api/sql/read` de sigrid-api, solo en lo que toca al tope:
    devuelve como mucho `max_rows` filas, con `truncated` a true si había
    más. Anota el cuerpo de cada petición en ``peticiones``."""

    def __init__(self, filas: list[dict]) -> None:
        self.filas = filas
        self.peticiones: list[dict] = []

    def __call__(self, url, *, headers, timeout, json):
        self.peticiones.append(json)
        tope = int(json["max_rows"])
        columnas = list(self.filas[0]) if self.filas else []
        filas = [[f[c] for c in columnas] for f in self.filas]
        return _Respuesta({
            "ok": True, "database": json["database"], "columns": columnas,
            "rows": filas[:tope], "row_count": min(len(filas), tope),
            "truncated": len(filas) > tope})


def _emulada(monkeypatch, filas: list[dict]) -> SigridApiEmulada:
    api = SigridApiEmulada(filas)
    monkeypatch.setattr(mod.httpx, "post", api)
    return api


def _cliente(**kw) -> SigridWriteClient:
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="sin-clave", database="ruesma",
                             **kw)


def presupuesto_grande(n_relleno: int = PARTIDAS_0696) -> list[dict]:
    """Presupuesto de una obra con más de 2.000 partidas: un capítulo `CD`
    con ``n_relleno`` partidas que no casan con nadie y, AL FINAL (más allá
    de la fila 2.000), el capítulo `CI` con la partida del encargado. Una
    lectura cortada a 2.000 no la vería nunca."""
    relleno = [_fila(81000, 0, 0, "CD", "COSTES DIRECTOS")]
    relleno += [_fila(81001 + i, 81000, i + 1, f"CD.{i + 1:04d}",
                      f"HORMIGON TRAMO {i + 1}") for i in range(n_relleno)]
    return relleno + list(PRESUPUESTO_ORIGEN)


class ClienteObraGrande(ClienteFalso):
    """El doble de `conftest.py`, salvo que el presupuesto de la obra de
    origen se lee con el cliente REAL (su `capitulos_de_obra` y su `_read`)
    contra la sigrid-api emulada."""

    def __init__(self, real: SigridWriteClient, **kw) -> None:
        super().__init__(**kw)
        self.real = real

    def capitulos_de_obra(self, obride):
        if obride == self.obra_origen.ide:
            self.n_capitulos_de_obra += 1
            return self.real.capitulos_de_obra(obride)
        return super().capitulos_de_obra(obride)


def _preflight(cli) -> object:
    pl = RegistroPipeline(cliente=cli, settings=SettingsFalso())
    return pl.preflight(obra=ObraEntrada(codigo=OBRA_ORIGEN),
                        lineas=[linea(registro_id=1)])


# ================== a1 · el tope que se envía a sigrid-api ================== #

def test_f047_a1_el_tope_por_defecto_que_se_envia_es_200000(monkeypatch):
    api = _emulada(monkeypatch, [{"x": 1}])
    assert _cliente()._read("SELECT 1 AS x", []) == [{"x": 1}]
    assert [p["max_rows"] for p in api.peticiones] == [TOPE_DEFECTO]


def test_f047_a1_el_tope_configurado_es_el_que_se_envia(monkeypatch):
    api = _emulada(monkeypatch, [{"x": 1}])
    _cliente(max_rows=350_000)._read("SELECT 1 AS x", [])
    _cliente(max_rows="1234")._read("SELECT 1 AS x", [])
    assert [p["max_rows"] for p in api.peticiones] == [350_000, 1234]
    assert all(type(p["max_rows"]) is int for p in api.peticiones)


def test_f047_a1_todas_las_lecturas_usan_el_tope_del_cliente(monkeypatch):
    """No queda ningún 2.000 fijo: cualquier lectura (aquí la de partes y
    la del presupuesto) manda el tope del cliente."""
    api = _emulada(monkeypatch, [])
    cli = _cliente(max_rows=4321)
    cli.capitulos_de_obra(1)
    cli.partes_del_periodo(1, 2026, 9)
    assert [p["max_rows"] for p in api.peticiones] == [4321, 4321]


def test_f047_a1_ajuste_sigrid_max_rows_200000_por_defecto(monkeypatch):
    from config.settings import Settings

    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "sin-clave")
    monkeypatch.delenv("SIGRID_MAX_ROWS", raising=False)
    assert Settings(_env_file=None).sigrid_max_rows == TOPE_DEFECTO
    monkeypatch.setenv("SIGRID_MAX_ROWS", "350000")
    assert Settings(_env_file=None).sigrid_max_rows == 350_000


def test_f047_a1_la_app_inyecta_el_tope_de_los_ajustes(monkeypatch):
    from interface_adapters.api import app as modulo

    recibido: dict = {}

    def fabrica(**kw):
        recibido.update(kw)
        return ClienteFalso()

    monkeypatch.setattr(modulo, "SigridWriteClient", fabrica)
    ajustes = SimpleNamespace(**{
        **vars(SettingsFalso()),
        "sigrid_api_base_url": "http://sigrid.invalid",
        "sigrid_api_function_key": "sin-clave",
        "sigrid_api_database": "ruesma", "sigrid_api_timeout_s": 1.0,
        "sigrid_max_statements": 15, "sigrid_max_rows": 98_765,
        "tip_parte_trabajo": 35, "est_parte_activo": 1})
    modulo.build_app(ajustes)
    assert recibido["max_rows"] == 98_765


def test_f047_a1_el_script_de_pruebas_inyecta_el_tope():
    import prueba_escritura_porcentajes as script

    ajustes = SimpleNamespace(
        sigrid_api_base_url="http://sigrid.invalid",
        sigrid_api_function_key="sin-clave", sigrid_api_database="ruesma",
        sigrid_api_timeout_s=1.0, sigrid_max_statements=15,
        sigrid_max_rows=76_543, tip_parte_trabajo=35, est_parte_activo=1)
    assert script._cliente(ajustes)._max_rows == 76_543


def test_f047_a1_env_example_documenta_el_tope():
    ejemplo = Path(__file__).resolve().parents[1] / ".env.example"
    lineas = ejemplo.read_text(encoding="utf-8").splitlines()
    assert "SIGRID_MAX_ROWS=200000" in lineas


# ============== a2 · un `truncated` sigue siendo un error ============== #

def test_f047_a2_una_obra_mayor_que_el_tope_sigue_siendo_error(monkeypatch):
    """Con el tope por debajo del presupuesto, la lectura NO devuelve las
    filas parciales: lanza. Y el preflight cae sin decidir nada."""
    _emulada(monkeypatch, presupuesto_grande())
    real = _cliente(max_rows=2000)
    with pytest.raises(RuntimeError, match="truncada"):
        real.capitulos_de_obra(555001)
    cli = ClienteObraGrande(real)
    with pytest.raises(RuntimeError, match="truncada"):
        _preflight(cli)
    assert cli.escritos == []


def test_f047_a2_justo_en_el_tope_no_es_truncado(monkeypatch):
    """Frontera: una obra con tantas filas como el tope se lee entera."""
    filas = presupuesto_grande(n_relleno=10)
    _emulada(monkeypatch, filas)
    assert len(_cliente(max_rows=len(filas)).capitulos_de_obra(1)) \
        == len(filas)


# ====== a3 · una obra con más de 2.000 partidas resuelve su partida ====== #

def test_f047_a3_obra_con_mas_de_2000_partidas_resuelve_su_partida(
        monkeypatch):
    filas = presupuesto_grande()
    assert len(filas) > 3_000
    api = _emulada(monkeypatch, filas)
    cli = ClienteObraGrande(_cliente())
    pf = _preflight(cli)
    (a,) = pf.acciones
    assert a.accion == "escribir"
    assert (a.paride, a.partida_cod) == (80001, "CI.1.10")
    assert [p["max_rows"] for p in api.peticiones] == [TOPE_DEFECTO]
    assert cli.escritos == []
