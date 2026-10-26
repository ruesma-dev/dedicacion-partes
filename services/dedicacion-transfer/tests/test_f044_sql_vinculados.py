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


# ============ R24 · la guarda de la edición con la hora del vinculado ===== #
_SIN_ENLACES = ("AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0 "
                "AND ISNULL(hdereside, 0) = 0 AND ISNULL(empdpreide, 0) = 0 "
                "AND ISNULL(empabside, 0) = 0 AND ISNULL(emprccide, 0) = 0 ")
#: La guarda de F-051 tal cual, con el hueco del código de hora.
_GUARDA = ("WHERE ide = ? AND reside = ? AND ABS(ISNULL(can, 0) - ?) "
           "< 0.000001 AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ? "
           + _SIN_ENLACES + "AND EXISTS (SELECT 1 FROM auxhor a WHERE "
           "a.ide = hmores.horide AND {codigo}) AND EXISTS (SELECT 1 FROM "
           "con c WHERE c.ide = hmores.hmoide AND c.est = ?)")
_EDITAR = ("UPDATE hmores SET can = ?, pre = ?, tot = ?, horide = ?, "
           "paride = ?, caaide = ?, fec = ?, synckey = ? ")
_A_CERO = "UPDATE hmores SET can = 0, tot = 0 "
_EDICION = {"ide": 5, "reside": 11, "can_leido": 0.95,
            "synckey_leida": None, "horide": 33, "can": 0.6, "pre": 120.0,
            "paride": 7, "caaide": 0, "fecha_int": 20261031,
            "synckey": "porcentajes:vin:12:11", "tex": None}


def test_f044_r24_sin_hora_el_sql_de_hoy_caracter_a_caracter():
    cli = _cliente(_Falso())
    e = cli.stmt_editar_linea(**_EDICION)
    z = cli.stmt_poner_a_cero(ide=6, reside=11, can_leido=0.3,
                              synckey_leida="x")
    assert e["sql"] == _EDITAR + _GUARDA.format(codigo="a.cod LIKE 'M%'")
    assert z["sql"] == _A_CERO + _GUARDA.format(codigo="a.cod LIKE 'M%'")
    assert e["parameters"] == [0.6, 120.0, 72.0, 33, 7, 0, 20261031,
                               "porcentajes:vin:12:11", 5, 11, 0.95, "", 1]
    assert z["parameters"] == [6, 11, 0.3, "x", 1]
    assert cli.stmt_editar_linea(**_EDICION, hora=None) == e


def test_f044_r24_con_hora_la_guarda_exige_esa_hora_como_parametro():
    cli = _cliente(_Falso())
    e = cli.stmt_editar_linea(**_EDICION, hora=" OGAS ")
    z = cli.stmt_poner_a_cero(ide=6, reside=11, can_leido=0.3,
                              synckey_leida="x", hora="OTEL")
    assert e["sql"] == _EDITAR + _GUARDA.format(codigo="a.cod = ?")
    assert z["sql"] == _A_CERO + _GUARDA.format(codigo="a.cod = ?")
    assert e["parameters"][-2:] == ["OGAS", 1]
    assert z["parameters"] == [6, 11, 0.3, "x", "OTEL", 1]
    for st in (e, z):
        assert "OGAS" not in st["sql"] and "OTEL" not in st["sql"]
        assert "DELETE" not in st["sql"].upper()


# ================= R25 · la salida de preflight y ejecutar ================ #
#: Lo que R25 publica de cada vinculado (además van su cuenta y su aviso).
CLAVES_R25 = {"registro_id", "recurso_ide", "tipo", "cod", "accion",
              "hora_codigo", "can", "pre", "tot", "paride", "partida_cod",
              "partida_metodo", "parte_cod", "linea_cero", "hmores_ide",
              "motivo"}


@pytest.fixture
def ruta_vin(monkeypatch):
    """(TestClient, doble) con el `ClientePre` de los tests del pipeline:
    un parte En registro con la línea del 200 que choca (5701) y la del
    teléfono 10 que también (5702)."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.conftest import linea_previa
    from tests.test_f044_pipeline_vinculados import ClientePre, _ls_vin
    from tests.test_f050_endpoint_propuesta import AJUSTES

    cli = ClientePre(lineas_parte=[
        linea_previa(ide=5701, can=0.4, paride=80001),
        _ls_vin(5702, 10, 0.4, paride=81001)])
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    ajustes = SimpleNamespace(**AJUSTES, sigrid_lecturas_paralelas=4)
    return TestClient(modulo_app.build_app(ajustes)), cli


_TF10 = {"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
         "cod": "TF-10"}


def _con_pisado(**extra) -> dict:
    return _cuerpo_registro(paride=80001, partida_cod="CI.1.10", **extra)


def test_f044_r25_respuesta_del_preflight_con_vinculados(ruta_vin):
    cliente, _ = ruta_vin
    r = cliente.post("/api/registro/preflight",
                     json=_con_pisado(vinculados=[_TF10]))
    assert r.status_code == 200
    cuerpo = r.json()
    [v] = cuerpo["vinculados"]
    assert CLAVES_R25 <= set(v)
    assert (v["registro_id"], v["recurso_ide"], v["accion"],
            v["hora_codigo"], v["paride"], v["partida_metodo"]) == (
        1, 10, "escribir", "OTEL", 81001, "ci_tipo")
    claves = {c["clave"]: c.get("vinculado") for c in cuerpo["conflictos"]}
    assert claves == {"200|202607|5|80001": None,
                      "10|202607|31|81001": {"tipo": "TF", "cod": "TF-10"}}


def test_f044_r25_respuesta_del_preflight_sin_vinculados_la_de_hoy(ruta_vin):
    """Sin vinculados en la petición: ni la clave `vinculados` ni la clave
    `vinculado` en los conflictos (la respuesta de siempre)."""
    cliente, _ = ruta_vin
    cuerpo = cliente.post("/api/registro/preflight",
                          json=_con_pisado()).json()
    assert "vinculados" not in cuerpo
    [c] = cuerpo["conflictos"]
    assert "vinculado" not in c and c["clave"] == "200|202607|5|80001"


def test_f044_r25_respuesta_de_ejecutar_con_y_sin_vinculados(ruta_vin):
    cliente, _ = ruta_vin
    sin = cliente.post("/api/registro/ejecutar", json=_con_pisado()).json()
    assert "vinculados" not in sin
    assert all("vinculado" not in c for c in sin["pendientes_confirmacion"])
    con = cliente.post("/api/registro/ejecutar", json={
        **_con_pisado(vinculados=[_TF10]),
        "pisar_claves": ["200|202607|5|80001"]}).json()
    [v] = con["vinculados"]
    # R26: confirmado el del titular, el del vinculado sigue pendiente.
    assert (v["recurso_ide"], v["accion"]) == (10, "omitir")
    assert [c["vinculado"] for c in con["pendientes_confirmacion"]] == [
        {"tipo": "TF", "cod": "TF-10"}]
    assert [e["registro_id"] for e in con["escritas"]] == [1]


def test_f044_r25_respuesta_del_preflight_lote_con_vinculados(ruta_vin):
    cliente, _ = ruta_vin
    r = cliente.post("/api/registro/preflight-lote", json={"peticiones": [
        _con_pisado(vinculados=[_TF10]), _con_pisado()]})
    con, sin = r.json()["obras"]
    assert [v["recurso_ide"] for v in con["vinculados"]] == [10]
    assert "vinculados" not in sin


# ============== T17 · el script de pruebas con los vinculados ============= #
class _ScriptFalso:
    """Lo que leen `fase_estado` y `fase_limpiar`: la obra de pruebas, su
    parte y las filas de `hmores` (cada consulta, apuntada)."""

    def __init__(self, filas: list[dict]) -> None:
        from domain.models.registro_models import ObraEntrada, ParteDestino
        self.filas = filas
        self.lecturas: list[tuple[str, list]] = []
        self.escritos: list = []
        self._obra = ObraEntrada(ide=828942, codigo="0404", nombre="PRUEBAS",
                                 empresa=1)
        self._parte = ParteDestino(ano=2026, mes=11, existe=True, ide=777,
                                   cod="PT26/00251")

    def obra_por_codigo(self, cod, empresa):
        return self._obra

    def partes_existentes(self, obra_ide, periodos):
        return {p: self._parte for p in periodos}

    def _read(self, sql, params):
        self.lecturas.append((sql, list(params)))
        return [dict(f) for f in self.filas]

    def escribir(self, statements):
        self.escritos.append(list(statements))
        return len(statements)


_FILAS_PARTE = [
    {"ide": 5101, "pos": 128, "reside": 200, "fec": "2026-11-30",
     "hora": "MENC", "can": 0.4, "synckey": "porcentajes:900001",
     "tex": "PRUEBA-PORC"},
    {"ide": 5201, "pos": 256, "reside": 10, "fec": "2026-11-30",
     "hora": "OTEL", "can": 0.4, "synckey": "porcentajes:vin:900001:10",
     "tex": "PRUEBA-PORC"},
    {"ide": 5301, "pos": 384, "reside": 11, "fec": "2026-11-30",
     "hora": "OGAS", "can": 0.95, "synckey": None, "tex": None},
]


def test_f044_script_estado_lista_las_lineas_de_los_vinculados(capsys):
    import prueba_escritura_porcentajes as script

    from tests.conftest import SettingsFalso

    script.fase_estado(_ScriptFalso(_FILAS_PARTE), SettingsFalso(), 2026, 11)
    salida = capsys.readouterr().out
    assert "Líneas del parte: 3" in salida
    assert "Líneas de vinculados (porcentajes:vin:): 1" in salida
    assert ("  titular 900001 · recurso 10 · hmores.ide=5201 · OTEL · "
            "can=0.4") in salida


def test_f044_script_estado_sin_vinculados_lo_de_siempre(capsys):
    import prueba_escritura_porcentajes as script

    from tests.conftest import SettingsFalso

    script.fase_estado(_ScriptFalso(_FILAS_PARTE[:1]), SettingsFalso(), 2026,
                       11)
    salida = capsys.readouterr().out
    assert "Líneas de vinculados (porcentajes:vin:): 0" in salida


def test_f044_script_limpiar_incluye_los_vinculados_con_la_marca(capsys):
    """`limpiar` ya filtra por la marca `PRUEBA-PORC` y el prefijo
    `porcentajes:`, que cubre `porcentajes:vin:`; en seco no escribe."""
    import prueba_escritura_porcentajes as script

    from tests.conftest import SettingsFalso

    vin = [f for f in _FILAS_PARTE if f["synckey"]
           and f["synckey"].startswith("porcentajes:vin:")]
    cli = _ScriptFalso(vin)
    script.fase_limpiar(cli, SettingsFalso(), False)
    [(sql, params)] = cli.lecturas
    assert "CAST(tex AS NVARCHAR(200)) = ?" in sql
    assert "synckey LIKE ?" in sql
    assert params == ["PRUEBA-PORC", "porcentajes:%"]
    assert "porcentajes:vin:900001:10".startswith(params[1].rstrip("%"))
    assert "Líneas marcadas 'PRUEBA-PORC' de este hilo: 1" in (
        capsys.readouterr().out)
    assert cli.escritos == []
