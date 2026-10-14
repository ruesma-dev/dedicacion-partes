# tests/test_f055_medicion.py
"""F-055 · T1: medición de las lecturas del transfer (R1, R2 y C2 «antes»).

- R1: cada lectura de `SigridWriteClient` deja un log con el nombre del
  método del cliente, sus filas y sus segundos, sin SQL ni parámetros; cada
  preflight, un resumen con su obra, sus lecturas, los segundos leyendo y los
  totales. La medición (`medir_lecturas`) es la misma que suma el resumen.
- R2: la fase `medir` de `prueba_escritura_porcentajes.py` enseña segundos
  por lectura, por obra y en total, sin llamar a `escribir` ni a `ejecutar`.
- C2 («antes»): fija las lecturas de HOY de una obra con partidas elegidas,
  en serie, con un `ClienteFalso` que cuenta. Es la cifra contra la que se
  medirá el «después» (T7); T4 la cambiará a propósito.

Sin red: `httpx.post` se sustituye por una respuesta fija. Los `ide` son
inventados.
"""
from __future__ import annotations

import logging
import re

import pytest
from application.pipelines import registro_pipeline as pipeline_mod
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ObraEntrada
from infrastructure.sigrid import sigrid_write_client as mod
from infrastructure.sigrid.sigrid_write_client import (
    SigridWriteClient,
    apuntar_lectura,
    medir_lecturas,
)

from tests.conftest import (
    OBRA_ORIGEN,
    OBRA_SIN_PARTIDA_PV,
    ClienteFalso,
    SettingsFalso,
    linea,
)

#: Un parámetro que no puede aparecer en ningún log (R1: sin parámetros).
PARAMETRO_SECRETO = "ZZ-PARAM-9"

#: Los métodos de lectura del cliente que usa el pipeline.
LECTURAS_PIPELINE = (
    "obra_por_codigo", "obra_por_ide", "capitulos_de_obra",
    "horas_de_recursos", "cuentas_de_centro", "partidas_de_lineas",
    "historial_partidas", "partes_del_periodo", "siguiente_cod_pt",
    "max_pos", "lineas_del_parte", "lineas_por_synckey",
)


class _Respuesta:
    def __init__(self, cuerpo: dict, status: int = 200) -> None:
        self.status_code = status
        self._cuerpo = cuerpo
        self.text = str(cuerpo)

    def json(self) -> dict:
        return self._cuerpo


def _sigrid(monkeypatch, cuerpo: dict | None = None, status: int = 200):
    """`httpx.post` falso: devuelve siempre `cuerpo` y guarda lo pedido."""
    pedidas: list[dict] = []
    cuerpo = cuerpo if cuerpo is not None else {
        "ok": True, "columns": [], "rows": []}

    def post(url, **kw):
        pedidas.append(kw["json"])
        return _Respuesta(cuerpo, status)

    monkeypatch.setattr(mod.httpx, "post", post)
    return pedidas


def _reloj(monkeypatch, modulo, *marcas: float) -> None:
    """`time.perf_counter` del módulo, con marcas fijas y en orden."""
    it = iter(marcas)
    monkeypatch.setattr(modulo, "_ahora", lambda: next(it))


def _cliente() -> SigridWriteClient:
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="sin-clave", database="ruesma")


def _logs(caplog, prefijo: str) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.getMessage().startswith(prefijo)]


# ============================ R1 · el cliente ============================ #

def test_f055_r1_lectura_loguea_nombre_filas_y_segundos(monkeypatch, caplog):
    _sigrid(monkeypatch, {"ok": True,
                          "columns": ["IDE", "COD", "RES", "CENIDE", "EMP"],
                          "rows": [[7, PARAMETRO_SECRETO, "OBRA", 3, 1]]})
    _reloj(monkeypatch, mod, 10.0, 11.5)
    caplog.set_level(logging.INFO, logger=mod.__name__)
    with medir_lecturas() as m:
        _cliente().obra_por_codigo(PARAMETRO_SECRETO, 1)
    assert _logs(caplog, "[sigrid-read]") == [
        "[sigrid-read] obra_por_codigo filas=1 segundos=1.50"]
    assert [(l.nombre, l.filas, l.segundos) for l in m.lecturas] == [
        ("obra_por_codigo", 1, 1.5)]


def test_f055_r1_el_log_no_lleva_sql_ni_parametros(monkeypatch, caplog):
    _sigrid(monkeypatch)
    caplog.set_level(logging.DEBUG)
    cli = _cliente()
    cli.obra_por_codigo(PARAMETRO_SECRETO, 1)
    cli.lineas_por_synckey([PARAMETRO_SECRETO])
    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert "[sigrid-read]" in texto
    for prohibido in (PARAMETRO_SECRETO, "SELECT", "FROM", "WHERE", "?"):
        assert prohibido not in texto, prohibido


@pytest.mark.parametrize("metodo, args", [
    ("obra_por_codigo", ("0694", 1)),
    ("obra_por_ide", (1,)),
    ("capitulos_de_obra", (1,)),
    ("horas_de_recursos", ([1],)),
    ("cuentas_de_centro", (1, 1, ["CIMO03"])),
    ("partidas_de_lineas", ([1],)),
    ("historial_partidas", ([1], 202410, 202609)),
    ("partes_del_periodo", (1, 2026, 9)),
    ("partes_existentes", (1, [(2026, 9)])),
    ("siguiente_cod_pt", (2026, 1)),
    ("max_pos", (1,)),
    ("lineas_del_parte", (1, [1])),
    ("lineas_por_synckey", (["porcentajes:1"],)),
    ("inspeccionar_mensuales", (1,)),
])
def test_f055_r1_cada_lectura_lleva_el_nombre_de_su_metodo(
        monkeypatch, metodo, args):
    _sigrid(monkeypatch)
    with medir_lecturas() as m:
        getattr(_cliente(), metodo)(*args)
    assert [(l.nombre, l.filas) for l in m.lecturas] == [(metodo, 0)]


def test_f055_r1_read_conserva_su_contrato_y_sus_dobles(monkeypatch):
    """`_read(sql, params)` no cambia de firma: los dobles de F-022, F-024,
    F-037 y F-050 lo sustituyen con dos argumentos, y la medición va por
    fuera (`_lectura`), con el nombre del método."""
    cli = _cliente()
    pedidas = []

    def doble(sql, params):
        pedidas.append(params)
        return [{"ide": 1}, {"ide": 2}]

    cli._read = doble                       # type: ignore[method-assign]
    with medir_lecturas() as m:
        assert cli.capitulos_de_obra(5) == [{"ide": 1}, {"ide": 2}]
    assert pedidas == [[5]]
    assert [(l.nombre, l.filas) for l in m.lecturas] == [
        ("capitulos_de_obra", 2)]


@pytest.mark.parametrize("cuerpo, status", [
    ({"ok": False}, 500),
    ({"ok": False, "error": "x"}, 200),
    ({"ok": True, "columns": ["X"], "rows": [[1]], "truncated": True}, 200),
])
def test_f055_r1_una_lectura_que_falla_tambien_se_mide(
        monkeypatch, caplog, cuerpo, status):
    _sigrid(monkeypatch, cuerpo, status)
    _reloj(monkeypatch, mod, 2.0, 2.25)
    caplog.set_level(logging.INFO, logger=mod.__name__)
    with medir_lecturas() as m, pytest.raises(RuntimeError):
        _cliente().capitulos_de_obra(1)
    assert [(l.nombre, l.filas, l.segundos) for l in m.lecturas] == [
        ("capitulos_de_obra", None, 0.25)]
    assert _logs(caplog, "[sigrid-read]") == [
        "[sigrid-read] capitulos_de_obra filas=error segundos=0.25"]


def test_f055_r1_mediciones_anidadas_y_fuera_de_medicion():
    apuntar_lectura("fuera", 1, 9.0)
    with medir_lecturas() as fuera:
        apuntar_lectura("a", 2, 0.5)
        with medir_lecturas() as dentro:
            apuntar_lectura("b", 3, 1.25)
        apuntar_lectura("c", None, 0.25)
    apuntar_lectura("despues", 1, 9.0)
    assert [l.nombre for l in fuera.lecturas] == ["a", "b", "c"]
    assert [l.nombre for l in dentro.lecturas] == ["b"]
    assert (fuera.n, fuera.segundos) == (3, 2.0)
    assert (dentro.n, dentro.segundos) == (1, 1.25)


# ===================== R1 · el resumen del preflight ===================== #

class ClienteQueCuenta(ClienteFalso):
    """`ClienteFalso` que apunta cada lectura en la medición en curso, como
    `SigridWriteClient._read`, con `segundos` fijos por lectura."""

    def __init__(self, segundos: float = 0.5, **kw) -> None:
        super().__init__(**kw)
        for nombre in LECTURAS_PIPELINE:
            setattr(self, nombre,
                    self._medida(nombre, getattr(self, nombre), segundos))

    @staticmethod
    def _medida(nombre, lectura, segundos):
        def medida(*a, **kw):
            r = lectura(*a, **kw)
            filas = (0 if r is None else len(r)
                     if hasattr(r, "__len__") and not isinstance(r, str)
                     else 1)
            apuntar_lectura(nombre, filas, segundos)
            return r
        return medida

    def escribir(self, statements):
        raise AssertionError("medir no escribe en Sigrid")


def _elegidas() -> list:
    """Una obra con partidas ELEGIDAS (hojas activas del presupuesto de
    origen del doble): el caso de C2."""
    return [linea(registro_id=1, recurso_ide=200, paride=80001,
                  partida_cod="CI.1.10"),
            linea(registro_id=2, recurso_ide=400, paride=80002,
                  partida_cod="CI.1.20", nombre="Jefe", categoria="Jefe")]


def _preflight(cli, lineas, obra=OBRA_ORIGEN):
    pl = RegistroPipeline(cliente=cli, settings=SettingsFalso())
    return pl.preflight(obra=ObraEntrada(codigo=obra), lineas=lineas)


def test_f055_r1_preflight_resume_obra_lecturas_y_segundos(monkeypatch,
                                                           caplog):
    _reloj(monkeypatch, pipeline_mod, 100.0, 105.75)
    caplog.set_level(logging.INFO, logger=pipeline_mod.__name__)
    _preflight(ClienteQueCuenta(segundos=0.5), _elegidas())
    assert _logs(caplog, "[registro] lecturas preflight") == [(
        f"[registro] lecturas preflight obra={OBRA_ORIGEN} lecturas=8 "
        f"segundos_leyendo=4.00 segundos_totales=5.75")]


def test_f055_r1_preflight_que_falla_tambien_resume(monkeypatch, caplog):
    _reloj(monkeypatch, pipeline_mod, 1.0, 1.5)
    caplog.set_level(logging.INFO, logger=pipeline_mod.__name__)
    with pytest.raises(RuntimeError, match="no encontrada"):
        _preflight(ClienteQueCuenta(segundos=0.25), _elegidas(),
                   obra="9999")
    assert _logs(caplog, "[registro] lecturas preflight") == [(
        "[registro] lecturas preflight obra=9999 lecturas=1 "
        "segundos_leyendo=0.25 segundos_totales=0.50")]


def test_f055_r1_preflight_por_ide_resume_con_el_ide(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=pipeline_mod.__name__)
    pl = RegistroPipeline(cliente=ClienteQueCuenta(), settings=SettingsFalso())
    pl.preflight(obra=ObraEntrada(ide=555001), lineas=_elegidas())
    [resumen] = _logs(caplog, "[registro] lecturas preflight")
    assert resumen.startswith("[registro] lecturas preflight obra=555001 ")


# ========================= C2 · «antes» (hoy) ========================= #

def test_f055_c2_antes_una_obra_con_elegidas_hace_8_lecturas_en_serie():
    """Hoy: 8 lecturas en serie, una tras otra, para una obra con todas sus
    partidas elegidas (modo pruebas, parte existente, recursos con
    subcuenta). La de presupuesto (`capitulos_de_obra`) es la que F-055
    sustituye por `validar_partidas` (T4)."""
    with medir_lecturas() as m:
        pf = _preflight(ClienteQueCuenta(), _elegidas())
    assert [a.partida_metodo for a in pf.acciones] == ["manual", "manual"]
    assert [l.nombre for l in m.lecturas] == [
        "obra_por_codigo",          # obra de origen
        "obra_por_codigo",          # obra de pruebas (0404)
        "horas_de_recursos",
        "capitulos_de_obra",        # presupuesto de origen (R20 de F-050)
        "cuentas_de_centro",
        "partes_del_periodo",
        "lineas_por_synckey",
        "lineas_del_parte",
    ]


def test_f055_c2_antes_recurso_sin_subcuenta_hace_9_lecturas():
    """El otro extremo de «8-9»: un recurso sin cuenta de plantilla obliga a
    leer la cuenta de su partida (`partidas_de_lineas`)."""
    cli = ClienteQueCuenta()
    for h in cli.horas[200]:
        h.caa_cod = None
    with medir_lecturas() as m:
        _preflight(cli, _elegidas())
    nombres = [l.nombre for l in m.lecturas]
    assert len(nombres) == 9
    assert nombres.index("partidas_de_lineas") \
        == nombres.index("capitulos_de_obra") + 1


# ======================= R2 · la fase `medir` ======================= #

def _medir(monkeypatch, cli, *argv):
    import prueba_escritura_porcentajes as script

    def prohibido(*a, **kw):
        raise AssertionError("la fase medir no registra nada")

    monkeypatch.setattr(script, "get_settings", lambda: SettingsFalso())
    monkeypatch.setattr(script, "_cliente", lambda st: cli)
    monkeypatch.setattr(RegistroPipeline, "ejecutar", prohibido)
    monkeypatch.setattr("sys.argv", ["prueba_escritura_porcentajes.py",
                                     "medir", *argv])
    script.main()


def _bloques(salida: str) -> dict[str, list[str]]:
    """Las líneas de la salida, agrupadas por la cabecera `== Obra X ==`."""
    out: dict[str, list[str]] = {}
    actual = None
    for l in salida.splitlines():
        m = re.match(r"== Obra (\S+) ==", l)
        if m:
            actual = out.setdefault(m.group(1), [])
        elif actual is not None:
            actual.append(l)
    return out


def test_f055_r2_medir_ensena_segundos_por_lectura_obra_y_total(
        monkeypatch, capsys):
    cli = ClienteQueCuenta(segundos=0.5)
    _medir(monkeypatch, cli, "--ano", "2026", "--mes", "7",
           "--obra", OBRA_ORIGEN, "--obra", OBRA_SIN_PARTIDA_PV,
           "--recurso", "200", "--recurso", "400")
    salida = capsys.readouterr().out
    assert cli.escritos == []
    bloques = _bloques(salida)
    assert list(bloques) == [OBRA_ORIGEN, OBRA_SIN_PARTIDA_PV]
    for obra, lineas in bloques.items():
        lecturas = [l for l in lineas if l.startswith("  lectura ")]
        assert lecturas, obra
        assert all(re.fullmatch(r"  lectura \w+: (\d+ filas|error) · "
                                r"\d+\.\d\d s", l) for l in lecturas), lecturas
        n = len(lecturas)
        resumen = [l for l in lineas if l.startswith(f"Obra {obra}: ")]
        assert len(resumen) == 1
        assert re.fullmatch(
            rf"Obra {obra}: {n} lecturas · {n * 0.5:.2f} s leyendo · "
            r"\d+\.\d\d s en total", resumen[0]), resumen
    # Sin partida elegida: las dos líneas van por la automática de hoy.
    assert "historial_partidas" in "\n".join(bloques[OBRA_ORIGEN])
    total = [l for l in salida.splitlines() if l.startswith("TOTAL: ")]
    n_total = sum(len([l for l in b if l.startswith("  lectura ")])
                  for b in bloques.values())
    assert len(total) == 1
    assert re.fullmatch(
        rf"TOTAL: 2 obras · {n_total} lecturas · {n_total * 0.5:.2f} s "
        r"leyendo · \d+\.\d\d s en total", total[0]), total


def test_f055_r2_medir_con_partida_elegida_por_obra(monkeypatch, capsys):
    cli = ClienteQueCuenta()
    _medir(monkeypatch, cli, "--ano", "2026", "--mes", "7",
           "--obra", OBRA_ORIGEN, "--obra", OBRA_SIN_PARTIDA_PV,
           "--recurso", "200", "--partida", f"{OBRA_ORIGEN}:80001")
    bloques = _bloques(capsys.readouterr().out)
    origen = "\n".join(bloques[OBRA_ORIGEN])
    assert "recurso=200 paride=80001 manual" in origen
    assert "historial_partidas" not in origen
    assert "manual" not in "\n".join(bloques[OBRA_SIN_PARTIDA_PV])


def test_f055_r2_medir_con_lote_aun_mide_obra_a_obra(monkeypatch, capsys):
    _medir(monkeypatch, ClienteQueCuenta(), "--obra", OBRA_ORIGEN,
           "--recurso", "200", "--lote")
    salida = capsys.readouterr().out
    assert "--lote: aún sin efecto" in salida
    assert list(_bloques(salida)) == [OBRA_ORIGEN]


def test_f055_r2_medir_sigue_si_una_obra_falla(monkeypatch, capsys):
    _medir(monkeypatch, ClienteQueCuenta(segundos=0.25), "--obra", "9999",
           "--obra", OBRA_ORIGEN, "--recurso", "200")
    salida = capsys.readouterr().out
    bloques = _bloques(salida)
    assert list(bloques) == ["9999", OBRA_ORIGEN]
    fallo = "\n".join(bloques["9999"])
    assert "NO se pudo: obra no encontrada en Sigrid" in fallo
    assert re.search(r"Obra 9999: 1 lecturas · 0\.25 s leyendo", fallo)
    assert re.search(r"TOTAL: 2 obras · \d+ lecturas", salida)


@pytest.mark.parametrize("argv", [
    ("--recurso", "200"),
    ("--obra", OBRA_ORIGEN),
    ("--obra", OBRA_ORIGEN, "--recurso", "200", "--partida", "80001"),
    ("--obra", OBRA_ORIGEN, "--recurso", "200", "--partida",
     f"{OBRA_ORIGEN}:abc"),
    ("--obra", OBRA_ORIGEN, "--recurso", "200", "--partida", "0001:80001"),
])
def test_f055_r2_medir_rechaza_argumentos_incompletos(monkeypatch, argv):
    with medir_lecturas() as m, pytest.raises(SystemExit):
        _medir(monkeypatch, ClienteQueCuenta(), *argv)
    assert m.n == 0
