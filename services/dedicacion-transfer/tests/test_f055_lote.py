# tests/test_f055_lote.py
"""F-055 · T7: `POST /api/registro/preflight-lote` (R19, R21, R24, R25;
C1 y C2 «después»).

- R19: una entrada por petición, en su orden, con la forma del preflight de
  hoy o `{ok: false, error}`.
- R21: cada obra en el lote da lo MISMO que su petición suelta. Se prueba
  repitiendo en lote cada preflight de los escenarios de `test_f037_pipeline`,
  `test_f050_pipeline`, `test_f002_pipeline` y `test_f039_preflight_var`
  (plugin `tests/f055_equivalencia_lote.py`, en un pytest aparte) y con
  lotes de varias obras.
- R24: el fallo propio de una obra solo marca su entrada; una lectura
  agrupada que falla, 502.
- R25: la ruta es síncrona (`def`, threadpool de FastAPI).
- C1: con 1, 2 y 10 obras con partida, las mismas lecturas salvo
  `cuentas_de_centro` (una por centro); ninguna de presupuesto ni historial.
- C2 «después»: una obra con elegidas, lecturas y rondas.

Sin red ni BBDD. Los `ide` son inventados.
"""
from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ObraEntrada, PartidaValida
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app
from interface_adapters.api.app import _respuesta_preflight

from tests.conftest import OBRA_ORIGEN, SettingsFalso, linea, linea_previa
from tests.test_f050_endpoint_propuesta import AJUSTES
from tests.test_f055_lecturas_lote import ClienteQueAnota

SERVICIO = Path(__file__).resolve().parents[1]
ESCENARIOS = ["tests/test_f037_pipeline.py", "tests/test_f050_pipeline.py",
              "tests/test_f002_pipeline.py",
              "tests/test_f039_preflight_var.py"]


def _ajustes(**kw) -> SettingsFalso:
    st = SettingsFalso(**kw)
    st.sigrid_lecturas_paralelas = 4
    return st


def _lote(cli, peticiones, **kw):
    return RegistroLote(cliente=cli, settings=_ajustes(**kw)).preflight(
        peticiones)


def _suelto(cli, obra, lineas, **kw):
    return RegistroPipeline(cliente=cli, settings=_ajustes(**kw)).preflight(
        obra=obra, lineas=lineas)


# ================ R21 · los escenarios de hoy, en lote ================== #
def test_f055_r21_cada_escenario_da_lo_mismo_suelto_y_en_lote(tmp_path):
    salida = tmp_path / "cuenta.json"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", *ESCENARIOS, "-q", "-x",
         "-p", "no:cacheprovider", "-p", "tests.f055_equivalencia_lote"],
        cwd=SERVICIO, capture_output=True, text=True, timeout=300,
        env={**__import__("os").environ,
             "F055_EQUIVALENCIA_SALIDA": str(salida)})
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
    cuenta = json.loads(salida.read_text(encoding="utf-8"))
    assert cuenta["iguales"] >= 100, cuenta
    assert cuenta["errores_iguales"] >= 1, cuenta
    assert cuenta["sin_comparar"] == 1, cuenta


def test_f055_r21_siguiente_cod_pt_una_vez_y_lo_mismo():
    """El escenario que el plugin no compara, con un `siguiente_cod_pt`
    puro (como `MAX(cod) + 1` en Sigrid): dos partes nuevos, mismo código
    en suelto y en lote, y en lote una sola lectura por año y empresa."""
    def cli():
        c = ClienteObras(1, parte_existe=False)
        return c
    lineas = [_con_partida(1), _con_partida(1, registro_id=2, mes=8)]
    suelto = _suelto(cli(), _obra(1), lineas)
    en_lote = cli()
    [lote] = _lote(en_lote, [(_obra(1), lineas)])
    assert [p.cod for p in lote.partes] == ["PT26/09999", "PT26/09999"]
    assert _respuesta_preflight(lote) == _respuesta_preflight(suelto)
    assert en_lote.nombres().count("siguiente_cod_pt") == 1


# ==================== R19/R21 · varias obras a la vez ==================== #
class ClienteObras(ClienteQueAnota):
    """N obras de origen (`ide` 600001…), cada una con su hoja activa
    `700000 + i` y su centro; la obra 600099 no existe."""

    def __init__(self, n: int = 10, **kw) -> None:
        self.obras = {}
        for i in range(1, n + 1):
            o = ObraEntrada(ide=600000 + i, codigo=f"O{i:03d}",
                            nombre=f"OBRA {i}", empresa=1)
            o.cenide = 610000 + i
            self.obras[o.ide] = o
        super().__init__(**kw)

    def obra_por_ide(self, ide):
        return self.obras.get(int(ide))

    def validar_partidas(self, parides):
        return {int(p): PartidaValida(int(p), int(p) - 100000, "CI.1",
                                      "PARTIDA", True, True)
                for p in parides if 700001 <= int(p) <= 700099}


def _obra(i: int) -> ObraEntrada:
    return ObraEntrada(ide=600000 + i)


def _con_partida(i: int, registro_id: int | None = None, **kw):
    return linea(registro_id=registro_id or i, paride=700000 + i,
                 partida_cod="CI.1", **kw)


def test_f055_r21_varias_obras_cada_una_como_su_suelta():
    cli = ClienteObras(3)
    cli.lineas_parte = [linea_previa(paride=700002)]
    peticiones = [(_obra(1), [_con_partida(1)]),
                  (_obra(2), [_con_partida(2), linea(registro_id=20)]),
                  (_obra(3), [_con_partida(3, recurso_ide=400)])]
    lote = _lote(cli, peticiones)
    assert [type(r).__name__ for r in lote] == ["Preflight"] * 3
    for (obra, lineas), r in zip(peticiones, lote):
        suelto = ClienteObras(3)
        suelto.lineas_parte = list(cli.lineas_parte)
        assert _respuesta_preflight(r) == _respuesta_preflight(
            _suelto(suelto, obra, lineas))


def test_f055_r19_una_entrada_por_peticion_y_en_su_orden():
    cli = ClienteObras(3)
    r = _lote(cli, [(_obra(3), [_con_partida(3)]),
                    (_obra(1), [_con_partida(1)])])
    assert [x.obra_origen.ide for x in r] == [600003, 600001]
    assert [x.acciones[0].paride for x in r] == [700003, 700001]


# ===================== R24 · fallos de una obra o del lote =============== #
def test_f055_r24_la_obra_que_falla_solo_marca_su_entrada():
    cli = ClienteObras(2)
    r = _lote(cli, [(_obra(1), [_con_partida(1)]),
                    (ObraEntrada(ide=600099), [linea(registro_id=9)]),
                    (_obra(2), [_con_partida(2, empresa=1),
                                linea(registro_id=8, empresa=28)])])
    assert r[0].acciones[0].accion == "escribir"
    assert isinstance(r[1], RuntimeError) and "no encontrada" in str(r[1])
    assert type(r[2]).__name__ == "EmpresasMezcladas"


def test_f055_r24_una_agrupada_que_falla_hace_fallar_el_lote():
    cli = ClienteObras(2)

    def falla(*a):
        raise RuntimeError("sigrid-api devolvio una respuesta truncada")

    cli.lineas_por_synckey = falla
    with pytest.raises(RuntimeError, match="truncada"):
        _lote(cli, [(_obra(1), [_con_partida(1)]),
                    (_obra(2), [_con_partida(2)])])


def test_f055_r22_sin_estado_entre_llamadas():
    cli = ClienteObras(1)
    lote = RegistroLote(cliente=cli, settings=_ajustes())
    assert lote.preflight([(_obra(1), [_con_partida(1)])])[0] \
        .acciones[0].accion == "escribir"
    cli.synckeys = {"porcentajes:1": linea_previa(ide=9001)}
    assert lote.preflight([(_obra(1), [_con_partida(1)])])[0] \
        .acciones[0].accion == "ya_registrado"


def test_f055_r23_el_limite_sale_del_ajuste():
    st = _ajustes()
    st.sigrid_lecturas_paralelas = 1
    cli = ClienteObras(4, espera=0.02)
    RegistroLote(cliente=cli, settings=st).preflight(
        [(_obra(i), [_con_partida(i)]) for i in range(1, 5)])
    assert cli.max_a_la_vez == 1


# ============================== C1 y C2 ================================== #
def _lecturas(n: int, forzar: bool) -> list[str]:
    cli = ClienteObras(n)
    _lote(cli, [(_obra(i), [_con_partida(i)]) for i in range(1, n + 1)],
          obra_pruebas_forzar=forzar)
    return cli.nombres()


@pytest.mark.parametrize("forzar", [True, False], ids=["pruebas", "real"])
def test_f055_c1_mismas_lecturas_con_1_2_y_10_obras(forzar):
    por_n = {n: _lecturas(n, forzar) for n in (1, 2, 10)}
    sin_cuentas = {n: sorted(x for x in l if x != "cuentas_de_centro")
                   for n, l in por_n.items()}
    assert sin_cuentas[1] == sin_cuentas[2] == sin_cuentas[10]
    for l in sin_cuentas.values():
        assert "capitulos_de_obra" not in l and "historial_partidas" not in l
    centros = {n: por_n[n].count("cuentas_de_centro") for n in por_n}
    assert centros == ({1: 1, 2: 1, 10: 1} if forzar
                       else {1: 1, 2: 2, 10: 10})


@pytest.mark.parametrize("forzar", [True, False], ids=["pruebas", "real"])
def test_f055_c2_despues_una_obra_con_elegidas(forzar, monkeypatch):
    """El caso de C2 «antes» (8 lecturas en serie en pruebas, 7 en real):
    en lote, ≤ 6 lecturas contadas como en C1 (sin `cuentas_de_centro`, una
    por centro, ni la obra de pruebas, una por lote; decisión del humano del
    2026-10-15) y ≤ 4 rondas: las tandas de la precarga (por estructura, no
    por reloj) más la de `cuentas_de_centro`, la única lectura de la obra."""
    from tests.test_f055_lecturas_lote import contar_tandas
    from tests.test_f055_medicion import _elegidas
    tandas = contar_tandas(monkeypatch)
    cli = ClienteQueAnota()
    [pf] = _lote(cli, [(ObraEntrada(codigo=OBRA_ORIGEN), _elegidas())],
                 obra_pruebas_forzar=forzar)
    assert [a.partida_metodo for a in pf.acciones] == ["manual", "manual"]
    esperadas = ["obra_por_codigo", "horas_de_recursos",
                 "lineas_por_synckey", "validar_partidas",
                 "partes_de_periodos", "lineas_de_partes",
                 "cuentas_de_centro"]
    if forzar:
        esperadas.append("obra_por_codigo")
    assert sorted(cli.nombres()) == sorted(esperadas)
    propias = [c for c in cli.llamadas if c[0] != "cuentas_de_centro"
               and c[:2] != ("obra_por_codigo", "0404")]
    assert len(propias) == 6
    precargadas = sum(n for n, _ in tandas)
    assert cli.nombres()[precargadas:] == ["cuentas_de_centro"]
    assert sum(t for _, t in tandas) + 1 <= 4


# ================================ HTTP ==================================== #
@pytest.fixture
def api(monkeypatch):
    def fabricar(cli, **ajustes):
        monkeypatch.setattr(modulo_app, "SigridWriteClient",
                            lambda **kw: cli)
        st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4,
                                **ajustes})
        return TestClient(modulo_app.build_app(st))
    return fabricar


def _json_linea(i: int, **kw) -> dict:
    return {"registro_id": i, "ano": 2026, "mes": 7, "porcentaje": 0.4,
            "recurso_ide": 200, "nombre": "Acuna Mera, Antonio",
            "categoria": "Encargado", "empresa": 1, **kw}


def test_f055_r19_ruta_forma_de_hoy_por_obra(api):
    cli = ClienteObras(2)
    cliente = api(cli)
    peticiones = [
        {"obra": {"ide": 600001}, "lineas": [_json_linea(
            1, paride=700001, partida_cod="CI.1")]},
        {"obra": {"ide": 600099}, "lineas": [_json_linea(2)]},
        {"obra": {"ide": 600002}, "lineas": [_json_linea(
            3, paride=700002, partida_cod="CI.1")]}]
    r = cliente.post("/api/registro/preflight-lote",
                     json={"peticiones": peticiones})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["ok"] is True and len(cuerpo["obras"]) == 3
    sueltas = [api(ClienteObras(2)).post("/api/registro/preflight",
                                         json=p).json() for p in peticiones]
    assert cuerpo["obras"][0] == sueltas[0]
    assert cuerpo["obras"][2] == sueltas[2]
    assert cuerpo["obras"][1] == {
        "ok": False, "error": "obra no encontrada en Sigrid (ide=600099 "
                              "cod=None empresa=1)"}


def test_f055_r19_ruta_sin_peticiones(api):
    r = api(ClienteObras(1)).post("/api/registro/preflight-lote",
                                  json={"peticiones": []})
    assert r.json() == {"ok": True, "obras": []}


def test_f055_r24_ruta_502_si_falla_una_agrupada(api):
    cli = ClienteObras(1)

    def falla(*a):
        raise RuntimeError("sigrid-api read HTTP 500: caída")

    cli.horas_de_recursos = falla
    r = api(cli).post("/api/registro/preflight-lote", json={"peticiones": [
        {"obra": {"ide": 600001}, "lineas": [_json_linea(1)]}]})
    assert r.status_code == 502
    assert r.json() == {"ok": False,
                        "error": "sigrid-api read HTTP 500: caída"}


def test_f055_r25_la_ruta_es_sincrona():
    app = modulo_app.build_app(SimpleNamespace(**AJUSTES))
    [ruta] = [r for r in app.routes
              if getattr(r, "path", "") == "/api/registro/preflight-lote"]
    assert not inspect.iscoroutinefunction(ruta.endpoint)
