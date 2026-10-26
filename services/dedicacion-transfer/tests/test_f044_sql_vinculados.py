# tests/test_f044_sql_vinculados.py
"""F-044 · SQL del transfer para los recursos vinculados.

- R27 (T4): `cuentas_del_presupuesto(obra_ide)`, UNA lectura parametrizada
  (design §7.1): el código de la cuenta de cada partida del presupuesto que
  la tiene; nada concatenado; un fallo o `truncated` sube.

Sin red ni BBDD: `_read` sustituido por un doble.
"""
from __future__ import annotations

import pytest
from infrastructure.sigrid.sigrid_write_client import (
    SigridWriteClient,
    medir_lecturas,
)


class _Falso:
    def __init__(self, filas: list[dict] | None = None,
                 fallo: Exception | None = None) -> None:
        self.filas = filas or []
        self.fallo = fallo
        self.llamadas: list[tuple[str, list]] = []

    def __call__(self, sql: str, params: list) -> list[dict]:
        self.llamadas.append((sql, params))
        if self.fallo is not None:
            raise self.fallo
        return [dict(f) for f in self.filas]


def _cliente(falso: _Falso) -> SigridWriteClient:
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma")
    cli._read = falso                        # type: ignore[method-assign]
    return cli


# ================================ R27 ==================================== #
def test_f044_r27_sql_de_las_cuentas_del_presupuesto():
    falso = _Falso()
    _cliente(falso).cuentas_del_presupuesto(694001)
    [(sql, params)] = falso.llamadas
    assert " ".join(sql.split()) == (
        "SELECT p.ide AS ide, cc.cod AS cod FROM obrparpar p "
        "JOIN con cc ON cc.ide = p.caaide "
        "WHERE p.obride = ? AND ISNULL(p.caaide,0) <> 0")
    assert params == [694001]


def test_f044_r27_mapea_ide_y_codigo():
    falso = _Falso([{"ide": 70001, "cod": " 0694.CI.4.13 "},
                    {"ide": "70002", "cod": "0694.CI.4.14"},
                    {"ide": 70003, "cod": None}])
    assert _cliente(falso).cuentas_del_presupuesto("694001") == {
        70001: "0694.CI.4.13", 70002: "0694.CI.4.14", 70003: None}
    assert falso.llamadas[0][1] == [694001]


def test_f044_r27_una_lectura_medida_con_su_nombre():
    with medir_lecturas() as m:
        _cliente(_Falso([{"ide": 1, "cod": "X.CI.1"}])
                 ).cuentas_del_presupuesto(5)
    assert [(l.nombre, l.filas) for l in m.lecturas] == [
        ("cuentas_del_presupuesto", 1)]


def test_f044_r27_un_fallo_sube():
    falso = _Falso(fallo=RuntimeError(
        "sigrid-api devolvio una respuesta truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(falso).cuentas_del_presupuesto(5)


# ===================== R10, R25 · modelos y contrato ===================== #
def test_f044_r25_modelos_sin_vinculados_por_defecto():
    from domain.models.registro_models import (
        AccionVinculado,
        Conflicto,
        ObraEntrada,
        Preflight,
        ResultadoRegistro,
    )
    obra = ObraEntrada(ide=1, codigo="0404")
    assert Preflight(obra_destino=obra, obra_origen=obra,
                     forzada_pruebas=True).vinculados == []
    assert ResultadoRegistro(ok=True, obra_destino=obra,
                             forzada_pruebas=True).vinculados == []
    assert Conflicto(clave="k", recurso_ide=1, nombre=None, ano=2026,
                     mes=7, parte_cod=None).vinculado is None
    a = AccionVinculado(registro_id=1, recurso_ide=10, accion="escribir",
                        ano=2026, mes=7, fecha_int=20260731)
    assert (a.destino, a.paride, a.caa_ide, a.linea_cero, a.hmores_ide,
            a.motivo, a.aviso) == ("obra", 0, 0, None, None, None, None)


@pytest.fixture
def ruta_espiada(monkeypatch):
    """(TestClient, lineas recibidas por `RegistroPipeline.preflight`)."""
    from types import SimpleNamespace

    from application.pipelines.registro_pipeline import RegistroPipeline
    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.conftest import ClienteFalso
    from tests.test_f050_endpoint_propuesta import AJUSTES

    recibidas: list = []
    original = RegistroPipeline.preflight

    def espia(self, **kw):
        recibidas.append(kw["lineas"])
        return original(self, **kw)

    monkeypatch.setattr(RegistroPipeline, "preflight", espia)
    monkeypatch.setattr(modulo_app, "SigridWriteClient",
                        lambda **kw: ClienteFalso())
    ajustes = SimpleNamespace(**AJUSTES, sigrid_lecturas_paralelas=4)
    return TestClient(modulo_app.build_app(ajustes)), recibidas


def _cuerpo_registro(**extra) -> dict:
    return {"obra": {"codigo": "0678"}, "lineas": [{
        "registro_id": 1, "ano": 2026, "mes": 7, "porcentaje": 0.4,
        "recurso_ide": 200, "empresa": 1, **extra}]}


def test_f044_r10_la_ruta_convierte_los_vinculados(ruta_espiada):
    from domain.models.registro_models import VinculadoEntrada
    cliente, recibidas = ruta_espiada
    r = cliente.post("/api/registro/preflight", json=_cuerpo_registro(
        vinculados=[{"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
                     "cod": "TF-10", "paride": 81001,
                     "partida_cod": "CICO13", "hmores_ide": 77}]))
    assert r.status_code == 200
    [[l]] = recibidas
    assert l.vinculados == [VinculadoEntrada(
        recurso_ide=10, tipo="TF", tipo_res="TELEFONO", cod="TF-10",
        paride=81001, partida_cod="CICO13", hmores_ide=77)]


def test_f044_r11_la_ruta_sin_vinculados_la_linea_de_hoy(ruta_espiada):
    cliente, recibidas = ruta_espiada
    cliente.post("/api/registro/preflight", json=_cuerpo_registro())
    [[l]] = recibidas
    assert l.vinculados == []
