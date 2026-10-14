# tests/test_f050_endpoint_propuesta.py
"""F-050 · `POST /api/partidas/propuesta` (R8, R9, R11) y la fase de solo
lectura `propuesta` del script manual (T5).

`TestClient` sobre la app real: el cliente de Sigrid que construye
`build_app` se sustituye por el doble de `test_f050_pipeline.py`, que anota
las lecturas y prohíbe escribir. Sin red ni BBDD; `ide` inventados.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ObraEntrada
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app

from tests.conftest import OBRA_ORIGEN, SettingsFalso, linea
from tests.test_f050_pipeline import ClienteHistorial, _h

AJUSTES = {
    "sigrid_api_base_url": "http://sigrid.invalid",
    "sigrid_api_function_key": "sin-clave", "sigrid_api_database": "ruesma",
    "sigrid_api_timeout_s": 1.0, "sigrid_max_statements": 15,
    "sigrid_max_rows": 200_000, "tip_parte_trabajo": 35,
    "est_parte_activo": 1, "est_parte_cerrado": 3, "est_parte_imputado": 10,
    "obra_pruebas_forzar": True, "obra_pruebas_cod": "0404",
    "marca_pruebas": "PRUEBA-PORC", "postventa_registrar": True,
    "postventa_obra_cod": "POSTV2", "paso_pos": 64, "var_obra_cod": "VAR",
    "var_partida_desde": 29, "propuesta_meses_atras": 24}


class ClienteSoloLectura(ClienteHistorial):
    """Anota también las lecturas de presupuesto; escribir revienta."""

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.presupuestos: list[int] = []

    def capitulos_de_obra(self, obride):
        self.presupuestos.append(int(obride))
        return super().capitulos_de_obra(obride)

    def escribir(self, statements):
        raise AssertionError("la propuesta no escribe en Sigrid")


@pytest.fixture
def api(monkeypatch):
    """(TestClient, doble) con el cliente de Sigrid sustituido."""
    def fabricar(cli):
        monkeypatch.setattr(modulo_app, "SigridWriteClient",
                            lambda **kw: cli)
        return TestClient(modulo_app.build_app(SimpleNamespace(**AJUSTES)))
    return fabricar


def _peticion(*lineas, empresa=1, obra=None) -> dict:
    return {"empresa": empresa, "obra": obra or {"codigo": OBRA_ORIGEN},
            "ano": 2026, "mes": 7, "lineas": list(lineas)}


def _l(clave, recurso=200, categoria="Encargado",
       nombre="Acuna Mera, Antonio", pv=False) -> dict:
    return {"clave": clave, "recurso_ide": recurso, "nombre": nombre,
            "categoria": categoria, "es_postventa": pv}


RUTA = "/api/partidas/propuesta"


# ================================ R8 ==================================== #
def test_f050_r8_forma_de_la_respuesta(api):
    cli = ClienteSoloLectura([_h()])
    r = api(cli).post(RUTA, json=_peticion(
        _l("a"), _l("b", recurso=400, categoria="Jefe de obra",
                    nombre="Nadie")))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert [p["cod"] for p in cuerpo["partidas_obra"]] == [
        "CI.1.9", "CI.1.10", "CI.1.20"]
    assert cuerpo["partidas_obra"][0] == {
        "ide": 80003, "cod": "CI.1.9", "res": "ADMINISTRATIVO",
        "categoria": "CI", "mayor": "CI"}
    assert cuerpo["partidas_postventa"] == []
    assert cuerpo["propuestas"] == {
        "a": {"paride": 80003, "cod": "CI.1.9", "res": "ADMINISTRATIVO",
              "metodo": "parte_anterior",
              "origen": "parte PT26/00100 · 07/2026 · obra 0678"},
        "b": {"paride": 80002, "cod": "CI.1.20", "res": "JEFE DE OBRA",
              "metodo": "auto_categoria", "origen": None}}
    assert cuerpo["mayor_inicial"] == {"a": "CI", "b": "CI"}


def test_f050_r8_una_lectura_de_historial_y_de_presupuesto(api):
    cli = ClienteSoloLectura([])
    api(cli).post(RUTA, json=_peticion(_l("a"), _l("b", recurso=400),
                                       _l("c", pv=True)))
    assert cli.lecturas == [([200, 400], 202407, 202607)]
    assert cli.presupuestos.count(cli.obra_origen.ide) == 1
    assert cli.escritos == []


def test_f050_r8_sin_propuesta_y_mayor_inicial(api):
    cli = ClienteSoloLectura([])
    cuerpo = api(cli).post(RUTA, json=_peticion(
        _l("mando", categoria="Gruista", nombre="Nadie Nunca",
           recurso=None),
        _l("oficial", categoria="Astronauta", nombre="Nadie Nunca"))).json()
    assert cuerpo["propuestas"] == {"mando": None, "oficial": None}
    assert cuerpo["mayor_inicial"] == {"mando": "CI", "oficial": None}
    assert cli.lecturas == [([200], 202407, 202607)]


def test_f050_r8_sin_lineas_normales_no_lee_historial(api):
    cli = ClienteSoloLectura([_h()])
    cuerpo = api(cli).post(RUTA, json=_peticion(_l("pv", pv=True))).json()
    assert cli.lecturas == []
    assert [p["cod"] for p in cuerpo["partidas_obra"]] == [
        "CI.1.9", "CI.1.10", "CI.1.20"]


# ================================ R11 =================================== #
def test_f050_r11_postventa_propone_el_casado_p5(api):
    cli = ClienteSoloLectura([_h()])
    cuerpo = api(cli).post(RUTA, json=_peticion(_l("pv", pv=True))).json()
    assert cuerpo["propuestas"]["pv"] == {
        "paride": 70001, "cod": "0678", "res": "15 VIVIENDAS Y HOSTEL",
        "metodo": "postventa", "origen": None}
    assert cuerpo["mayor_inicial"]["pv"] == "CD"
    pv = cuerpo["partidas_postventa"]
    assert pv[0] == {"ide": 69110, "cod": "11.01", "res": "REPARACIONES",
                     "categoria": "CD", "mayor": "CD"}
    assert len(pv) == 9


def test_f050_r11_postventa_sin_casado_sin_propuesta(api):
    cli = ClienteSoloLectura([], presupuesto_postventa="hojas_inactivas")
    cuerpo = api(cli).post(RUTA, json=_peticion(
        _l("pv", pv=True, categoria="Peón"))).json()
    assert cuerpo["propuestas"] == {"pv": None}
    assert cuerpo["mayor_inicial"] == {"pv": None}
    assert [p["cod"] for p in cuerpo["partidas_postventa"]] == ["0713"]


# ================================ R9 ==================================== #
def test_f050_r9_misma_propuesta_que_el_preflight(api):
    historial = [_h(), _h(recurso=400, mes=5, paride=80002, cod="CI.1.20",
                          res="JEFE DE OBRA")]
    cuerpo = api(ClienteSoloLectura(historial)).post(RUTA, json=_peticion(
        _l("1"), _l("2", recurso=400, categoria="X", nombre="Y"))).json()
    pf = RegistroPipeline(cliente=ClienteHistorial(historial),
                          settings=SettingsFalso()).preflight(
        obra=ObraEntrada(codigo=OBRA_ORIGEN),
        lineas=[linea(registro_id=1),
                linea(registro_id=2, recurso_ide=400, categoria="X",
                      nombre="Y")])
    assert [(a.paride, a.partida_metodo, a.partida_origen)
            for a in pf.acciones] == [
        (cuerpo["propuestas"][k]["paride"], cuerpo["propuestas"][k]["metodo"],
         cuerpo["propuestas"][k]["origen"]) for k in ("1", "2")]


# ============================ R8 · errores =============================== #
@pytest.mark.parametrize("empresa", [None, 0, -1])
def test_f050_r8_empresa_no_valida_es_422(api, empresa):
    cli = ClienteSoloLectura([])
    r = api(cli).post(RUTA, json=_peticion(_l("a"), empresa=empresa))
    assert r.status_code == 422
    assert r.json() == {"ok": False,
                        "error": f"empresa no válida: {empresa!r}"}
    assert cli.presupuestos == [] and cli.lecturas == []


def test_f050_r8_obra_de_otra_empresa_es_422(api):
    cli = ClienteSoloLectura([])
    r = api(cli).post(RUTA, json=_peticion(
        _l("a"), empresa=28, obra={"ide": cli.obra.ide}))
    assert r.status_code == 422
    assert r.json() == {"ok": False, "error": (
        "la obra 0404 es de la empresa 1 y la línea se imputa a la empresa "
        "28: no se escribe")}
    assert cli.presupuestos == [] and cli.lecturas == []


def test_f050_r8_obra_inexistente_es_502(api):
    cli = ClienteSoloLectura([])
    r = api(cli).post(RUTA, json=_peticion(_l("a"),
                                           obra={"codigo": "9999"}))
    assert r.status_code == 502
    assert "obra no encontrada" in r.json()["error"]


def test_f050_r8_r7_lectura_que_falla_es_502(api):
    cli = ClienteSoloLectura(fallo=RuntimeError(
        "sigrid-api devolvio una respuesta truncada"))
    r = api(cli).post(RUTA, json=_peticion(_l("a")))
    assert r.status_code == 502
    assert r.json() == {"ok": False, "error": (
        "sigrid-api devolvio una respuesta truncada")}


# ================= T5 · fase `propuesta` del script manual ================ #
def _script(monkeypatch, cli, *argv):
    import prueba_escritura_porcentajes as script

    def prohibido(*a, **kw):
        raise AssertionError("la fase propuesta no registra nada")

    monkeypatch.setattr(script, "get_settings",
                        lambda: SimpleNamespace(**AJUSTES))
    monkeypatch.setattr(script, "_cliente", lambda st: cli)
    monkeypatch.setattr(RegistroPipeline, "ejecutar", prohibido)
    monkeypatch.setattr("sys.argv", ["prueba_escritura_porcentajes.py",
                                     "propuesta", *argv])
    script.main()


def test_f050_script_propuesta_solo_lee_y_ensena_todo(monkeypatch, capsys):
    cli = ClienteSoloLectura([_h()])
    _script(monkeypatch, cli, "--obra", OBRA_ORIGEN, "--recurso", "200",
            "--ano", "2026", "--mes", "7")
    salida = capsys.readouterr().out
    assert cli.escritos == []
    assert cli.lecturas == [([200], 202407, 202607)]
    for texto in ("CI   CI.1.9", "CI   CI.1.10", "CI   CI.1.20",
                  "Catálogo de 0678: 3 partidas hoja activas",
                  "Por mayor: CD 0 · CI 3 · CP 0 · OTRO 0",
                  "Propuesta: CI.1.9 · ADMINISTRATIVO (paride 80003)",
                  ("método parte_anterior · origen parte PT26/00100 · "
                   "07/2026 · obra 0678"),
                  "Botón preelegido (mayor_inicial): CI"):
        assert texto in salida, texto
    lecturas = [x for x in salida.splitlines() if x.startswith("  lectura ")]
    assert [x.split()[1].rstrip(":") for x in lecturas] == [
        "obra_por_codigo", "capitulos_de_obra", "historial_partidas"]
    assert all(x.endswith(" s") for x in lecturas)
    assert salida.index("CI.1.9") < salida.index("CI.1.10")


def test_f050_script_propuesta_sin_propuesta_y_con_casamiento(monkeypatch,
                                                              capsys):
    cli = ClienteSoloLectura([])
    _script(monkeypatch, cli, "--obra", OBRA_ORIGEN, "--recurso", "200",
            "--ano", "2026", "--mes", "7", "--categoria", "Gruista")
    salida = capsys.readouterr().out
    assert "Propuesta: ninguna" in salida
    assert "Botón preelegido (mayor_inicial): CI" in salida
    _script(monkeypatch, cli, "--obra", OBRA_ORIGEN, "--recurso", "200",
            "--ano", "2026", "--mes", "7", "--categoria", "Encargado",
            "--nombre", "Acuna Mera, Antonio")
    salida = capsys.readouterr().out
    assert "método auto_nombre · origen —" in salida


def test_f050_script_propuesta_obra_de_otra_empresa(monkeypatch, capsys):
    cli = ClienteSoloLectura([])
    cli.obra_origen.empresa = 28
    _script(monkeypatch, cli, "--obra", OBRA_ORIGEN, "--recurso", "200")
    salida = capsys.readouterr().out
    assert "NO se propone: la obra 0678 es de la empresa 28" in salida
    assert cli.lecturas == []


def test_f050_script_propuesta_exige_obra_y_recurso(monkeypatch, capsys):
    cli = ClienteSoloLectura([])
    with pytest.raises(SystemExit):
        _script(monkeypatch, cli, "--obra", OBRA_ORIGEN)
    assert "--recurso" in capsys.readouterr().err


# ============ T15 · casos que la campaña de mutación dejó vivos ============ #
def test_f050_r8_una_linea_sin_modo_es_de_obra_normal(api):
    cli = ClienteSoloLectura([_h()])
    linea = _l("a")
    del linea["es_postventa"]
    cuerpo = api(cli).post(RUTA, json=_peticion(linea)).json()
    assert cuerpo["propuestas"]["a"]["metodo"] == "parte_anterior"
    assert cuerpo["partidas_postventa"] == []


def test_f050_script_propuesta_linea_completa_y_tiempos(monkeypatch, capsys):
    cli = ClienteSoloLectura([_h()])
    _script(monkeypatch, cli, "--obra", OBRA_ORIGEN, "--recurso", "200")
    salida = capsys.readouterr().out
    assert "  CI   CI.1.9           ADMINISTRATIVO" in salida.splitlines()
    segundos = [float(x.split(": ")[1].split()[0]) for x in
                salida.splitlines() if x.startswith("  lectura ")]
    assert len(segundos) == 3 and all(0 <= s < 60 for s in segundos)
