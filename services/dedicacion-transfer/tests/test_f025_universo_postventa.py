# tests/test_f025_universo_postventa.py
"""F-025 · El universo de postventa, calculado en un solo sitio (R1-R9, R25).

La regla es `docs/ARCHITECTURE.md#regla-p5`; aquí solo se comprueba que el
universo que publica `POST /api/postventa/universo` y lo que el preflight
hace con la línea de postventa salen de las MISMAS funciones, y que ningún
catálogo sobrevive a la petición que lo leyó.

Sin red ni BBDD: todo sale de los dobles de `conftest.py` y de
`test_f022_obra_por_empresa.py`.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_porcentajes import (
    MOTIVO_PARTIDA_PV_NO_HOJA,
    MOTIVO_POSTVENTA_OFF,
)
from domain.models.registro_models import ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    PRESUPUESTO_PV_HOJAS,
    ClienteFalso,
    SettingsFalso,
    _fila,
    linea,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)


def _pipeline(cli, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))


# ------------- R8 · sin líneas de postventa, catálogo vacío -------------- #

def test_f025_r8_preflight_sin_postventa_tras_otro_con_postventa():
    """R8 · La instancia del pipeline es única en la app (F-022): un preflight
    sin líneas de postventa no puede publicar el catálogo que leyó el
    anterior, que era de otra petición."""
    pl = _pipeline(ClienteFalso())
    con_pv = pl.preflight(obra=OBRA, lineas=[
        linea(registro_id=3, es_postventa=True)])
    assert con_pv.partidas_postventa, "control: el primero sí lo publica"

    sin_pv = pl.preflight(obra=OBRA, lineas=[linea(registro_id=1)])
    assert sin_pv.partidas_postventa == []


def test_f025_r8_preflight_sin_postventa_en_instancia_nueva():
    """R8 · Control: en una instancia recién creada también sale vacío."""
    pf = _pipeline(ClienteFalso()).preflight(obra=OBRA,
                                             lineas=[linea(registro_id=1)])
    assert pf.partidas_postventa == []


# ------------- R9 · el catálogo no sobrevive a su petición -------------- #

def test_f025_r9_el_pipeline_no_guarda_estado_entre_peticiones():
    """R9 · Ningún catálogo sobrevive a la petición que lo leyó: tras un
    preflight con postventa, la instancia solo conserva lo que tenía al
    nacer (cliente y ajustes)."""
    pl = _pipeline(ClienteFalso())
    antes = set(vars(pl))
    pl.preflight(obra=OBRA, lineas=[linea(registro_id=3, es_postventa=True)])
    assert set(vars(pl)) == antes


def test_f025_r9_override_validado_contra_el_presupuesto_de_su_peticion():
    """R9 · El override a `0713` vale con el presupuesto `hojas`; si en la
    petición siguiente `0713` ya tiene partidas debajo (es capítulo), el
    mismo override se omite: se valida contra lo leído en ESA petición."""
    cli = ClienteFalso()
    pl = _pipeline(cli)
    override = dict(registro_id=3, es_postventa=True, paride=70002,
                    partida_cod="0713")
    primero = pl.preflight(obra=OBRA, lineas=[linea(**override)])
    assert primero.acciones[0].partida_metodo == "manual", primero.acciones

    cli.capitulos = PRESUPUESTO_PV_HOJAS + [
        _fila(70031, 70002, 1, "0713.MO", "MANO DE OBRA")]
    segundo = pl.preflight(obra=OBRA, lineas=[linea(**override)])
    a = segundo.acciones[0]
    assert a.accion == "omitir", a
    assert a.motivo == MOTIVO_PARTIDA_PV_NO_HOJA.format(paride=70002)


# ======================= T2 · el universo (R1-R7) ======================= #

#: Presupuesto de la obra de postventa para el cruce de R2. Un caso por
#: forma de casado (o de no casar) que importa: exacta, sufijo de letra (la
#: más corta y, a igualdad, la menor), el capítulo `CP` con su `CP.1` (falso
#: casado de la cascada vieja), la obra-capítulo (D8), un código que solo
#: aparece en la descripción y un nombre que solo aparece en la descripción.
PRESUPUESTO_CRUCE: list[dict] = [
    _fila(69000, 0, 0, "CD", "COSTES DIRECTOS"),
    _fila(71001, 69000, 1, "0656", "33+34 VIVIENDAS TOMARES"),
    _fila(71002, 69000, 2, "0578C", "OBRA 0578 FASE C"),
    _fila(71003, 69000, 3, "0578B", "OBRA 0578 FASE B"),
    _fila(71004, 69000, 4, "0654-B", "OBRA 0654 FASE B"),
    _fila(69200, 0, 5, "CP", "COSTES PROPORCIONALES"),
    _fila(71005, 69200, 1, "CP.1", "SEGUROS"),
    _fila(71006, 69000, 5, "0679", "OBRA CAPITULO"),
    _fila(71007, 71006, 1, "0679.MO", "MANO DE OBRA"),
    _fila(71008, 69000, 6, "CI.7.5", "OT VARIOS"),
    _fila(71009, 69000, 7, "0611", "RESIDENCIA LOS OLIVOS"),
]

#: (ide, código, nombre) de las obras del cruce. El ide no existe en Sigrid:
#: el doble resuelve cualquier `ide` a la obra de pruebas, de la empresa 1.
OBRAS_CRUCE = [
    (1, "0656", "TOMARES"),                  # exacta
    (2, "0578", "OBRA 0578"),                # sufijo de letra: 0578B
    (3, "0654", "OBRA 0654"),                # sufijo de letra con guion
    (4, "CP", "COSTES"),                     # prefijo + punto: CP.1
    (5, "0679", "OBRA CAPITULO"),            # obra-capítulo: 0679.MO (D8)
    (6, "OT", "OTROS"),                      # solo en la descripción
    (7, "191105", "RESIDENCIA LOS OLIVOS"),  # solo el nombre
    (8, "9999", "SIN NADA"),                 # sin casado
]


def _universo(cli, empresa: int = 1, obras=None, **ajustes) -> dict:
    from application.services.universo_postventa import UniversoPostventa

    obras = OBRAS_CRUCE if obras is None else obras
    return UniversoPostventa(
        cliente=cli, settings=SettingsFalso(**ajustes)).calcular(
            empresa, [ObraEntrada(ide=i, codigo=c, nombre=n)
                      for i, c, n in obras])


def _cli_cruce() -> ClienteFalso:
    cli = ClienteFalso()
    cli.capitulos = PRESUPUESTO_CRUCE
    return cli


def _preflight_pv(cli, ide, codigo, nombre, **ajustes):
    """Preflight de UNA línea de postventa de la obra dada, como lo manda
    la api (`RegistroSigrid._payloads`: ide, código y nombre)."""
    return _pipeline(cli, **ajustes).preflight(
        obra=ObraEntrada(ide=ide, codigo=codigo, nombre=nombre),
        lineas=[linea(registro_id=ide, es_postventa=True)])


@pytest.mark.parametrize("ide, codigo, nombre", OBRAS_CRUCE,
                         ids=[c for _i, c, _n in OBRAS_CRUCE])
def test_f025_r2_universo_y_preflight_casan_igual(ide, codigo, nombre):
    """R2 · EL test de la feature: una obra está en el universo con la
    partida X si y solo si el preflight de su línea de postventa publica X
    en `capitulo_postventa`; y fuera si y solo si el preflight la omite."""
    universo = {o["ide"]: o["partida"]
                for o in _universo(_cli_cruce())["obras"]}
    pf = _preflight_pv(_cli_cruce(), ide, codigo, nombre)
    publicada = getattr(pf, "capitulo_postventa")
    a = pf.acciones[0]

    assert universo.get(ide) == publicada, (codigo, universo.get(ide))
    if publicada is None:
        assert a.accion == "omitir" and "no casa" in a.motivo, a
    else:
        assert a.accion == "escribir" and a.paride == publicada["ide"], a


def test_f025_r1_universo_publica_obras_con_su_partida():
    """R1 · Cada obra del universo sale con la partida que le daría P5
    (`ide`, `cod`, `res`); las que no casan no salen. Sin escribir."""
    cli = _cli_cruce()
    r = _universo(cli, obras=[(1, "0656", "TOMARES"), (8, "9999", "NADA")])
    assert r["obras"] == [{"ide": 1, "partida": {
        "ide": 71001, "cod": "0656", "res": "33+34 VIVIENDAS TOMARES"}}]
    assert r["casadas"] == 1
    assert r["empresa"] == 1 and r["motivo"] is None
    assert r["obra_postventa"] == {"ide": 999001, "codigo": "POSTV2",
                                   "nombre": "POSTVENTA 2", "empresa": 1}
    assert cli.escritos == []


def test_f025_r1_casadas_cuenta_las_obras_del_universo():
    """R1 · `casadas` es el número de obras del universo, no de las pedidas."""
    r = _universo(_cli_cruce(), obras=[(1, "0656", "TOMARES"), (2, "0578", "X"),
                                       (8, "9999", "SIN NADA")])
    assert r["casadas"] == len(r["obras"]) == 2


def _ambigua():
    from tests.test_f022_obra_por_empresa import ClienteEmpresas

    return ClienteEmpresas(ambiguas={("POSTV2", 1)})


@pytest.mark.parametrize("cliente, motivo", [
    (lambda: ClienteFalso(obra_postventa_existe=False), "no encontrada"),
    (_ambigua, "ambigua"),
], ids=["ausente", "ambigua"])
def test_f025_r3_sin_obra_de_postventa_universo_vacio_con_su_motivo(
        cliente, motivo):
    """R3 · Obra de postventa ausente o ambigua en la empresa: `obras`
    vacía y en `motivo` EL MISMO texto con el que el preflight omite la
    línea de postventa."""
    r = _universo(cliente())
    pf = _preflight_pv(cliente(), 555001, "0678", "15 VIVIENDAS")
    assert r["obras"] == [] and r["casadas"] == 0
    assert r["obra_postventa"] is None
    assert motivo in r["motivo"]
    assert pf.acciones[0].accion == "omitir"
    assert r["motivo"] == pf.acciones[0].motivo


def test_f025_r3_la_empresa_pedida_es_la_que_se_busca():
    """R3 · La obra de postventa se busca en la empresa pedida: en la 28 el
    doble no tiene ninguna, así que no hay universo."""
    r = _universo(_cli_cruce(), empresa=28)
    assert r["obras"] == [] and r["empresa"] == 28
    assert "en la empresa 28" in r["motivo"]


def test_f025_r5_postventa_desactivada_universo_vacio_sin_leer():
    """R5 · Con `POSTVENTA_REGISTRAR=false`: universo vacío, ese motivo y
    ninguna lectura de Sigrid."""
    cli = _cli_cruce()
    r = _universo(cli, postventa_registrar=False)
    assert r["obras"] == [] and r["casadas"] == 0
    assert r["motivo"] == MOTIVO_POSTVENTA_OFF
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (0, 0)


def _roto(_obride):
    raise RuntimeError("sigrid-api caído")


def test_f025_r6_un_fallo_de_sigrid_sube():
    """R6 · Un fallo de lectura no se convierte en universo parcial."""
    cli = _cli_cruce()
    cli.capitulos_de_obra = _roto
    with pytest.raises(RuntimeError, match="caído"):
        _universo(cli)


def test_f025_r7_una_lectura_por_peticion_no_por_obra():
    """R7 · Ocho obras, una lectura de la obra de postventa y una de su
    presupuesto."""
    cli = _cli_cruce()
    r = _universo(cli)
    assert len(r["obras"]) >= 2
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (1, 1)


def test_f025_r7_sin_obras_no_se_lee_nada():
    """R7 · Sin obras no hay nada que casar: ni una lectura."""
    cli = _cli_cruce()
    r = _universo(cli, obras=[])
    assert r == {"empresa": 1, "obra_postventa": None, "motivo": None,
                 "casadas": 0, "obras": []}
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (0, 0)


# ---------------- la ruta POST /api/postventa/universo ------------------ #

@pytest.fixture
def ruta(monkeypatch):
    """`build_app` con ajustes falsos y el cliente de Sigrid sustituido por
    el doble que se le pase."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo

    def fabricar(cli, **cambios):
        ajustes = SimpleNamespace(**{
            **vars(SettingsFalso()),
            "sigrid_api_base_url": "http://sigrid.invalid",
            "sigrid_api_function_key": "sin-clave",
            "sigrid_api_database": "ruesma", "sigrid_api_timeout_s": 1.0,
            "sigrid_max_statements": 15, "tip_parte_trabajo": 35,
            "est_parte_activo": 1, **cambios})
        monkeypatch.setattr(modulo, "SigridWriteClient", lambda **_kw: cli)
        return TestClient(modulo.build_app(ajustes))

    return fabricar


CUERPO = {"empresa": 1, "obras": [
    {"ide": 1, "codigo": "0656", "nombre": "TOMARES"},
    {"ide": 8, "codigo": "9999", "nombre": "SIN NADA"}]}


def test_f025_r1_ruta_devuelve_el_contrato(ruta):
    """R1 · Contrato de design §5 por HTTP: `ok`, `empresa`,
    `obra_postventa`, `motivo`, `casadas` y `obras` con `ide` y `partida`."""
    cli = _cli_cruce()
    r = ruta(cli).post("/api/postventa/universo", json=CUERPO)
    assert r.status_code == 200, r.text
    assert r.json() == {
        "ok": True, "empresa": 1,
        "obra_postventa": {"ide": 999001, "codigo": "POSTV2",
                           "nombre": "POSTVENTA 2", "empresa": 1},
        "motivo": None, "casadas": 1,
        "obras": [{"ide": 1, "partida": {
            "ide": 71001, "cod": "0656",
            "res": "33+34 VIVIENDAS TOMARES"}}]}
    assert cli.escritos == []


@pytest.mark.parametrize("empresa", ["ausente", None, 0, -1])
def test_f025_r4_sin_empresa_valida_422_sin_leer(ruta, empresa):
    """R4 · Sin empresa válida: 422 `{"ok": false, "error": …}` y ninguna
    lectura de Sigrid."""
    cli = _cli_cruce()
    cuerpo = {"obras": CUERPO["obras"]}
    if empresa != "ausente":
        cuerpo["empresa"] = empresa
    r = ruta(cli).post("/api/postventa/universo", json=cuerpo)
    assert r.status_code == 422, r.text
    assert r.json()["ok"] is False and "empresa" in r.json()["error"]
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (0, 0)


def test_f025_r6_fallo_de_sigrid_502(ruta):
    """R6 · Un fallo de lectura de Sigrid es un 502 con el error, nunca un
    universo parcial."""
    cli = _cli_cruce()
    cli.capitulos_de_obra = _roto
    r = ruta(cli).post("/api/postventa/universo", json=CUERPO)
    assert r.status_code == 502, r.text
    assert r.json() == {"ok": False, "error": "sigrid-api caído"}


def test_f025_r5_ruta_con_postventa_desactivada(ruta):
    """R5 · Por HTTP también: 200, universo vacío y el motivo."""
    cli = _cli_cruce()
    r = ruta(cli, postventa_registrar=False).post(
        "/api/postventa/universo", json=CUERPO)
    assert r.status_code == 200, r.text
    assert r.json()["obras"] == []
    assert r.json()["motivo"] == MOTIVO_POSTVENTA_OFF


# -------------------- R25 · sin el literal en el módulo ------------------ #

def test_f025_r25_el_modulo_nuevo_no_lleva_el_literal():
    """R25 · `universo_postventa.py` cita el ajuste, nunca su valor (como
    `test_f002_r5_…`, cuya tupla cerrada no ve este módulo)."""
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[1] / "application" /
             "services" / "universo_postventa.py").read_text(encoding="utf-8")
    assert "POSTV2" not in texto
    assert "POSTVENTA_OBRA_COD" in texto


# ----------- R10-R11 · quién queda dentro del universo del cruce ---------- #

def test_f025_r11_el_universo_del_cruce_solo_tiene_exactas_y_sufijos():
    """R10-R11 · Del cruce de R2, en el universo solo quedan la exacta y las
    dos de sufijo de letra; `CP`, la obra-capítulo, la de la descripción, la
    del nombre y la que no casa, fuera."""
    r = _universo(_cli_cruce())
    assert {o["ide"]: o["partida"]["cod"] for o in r["obras"]} == {
        1: "0656", 2: "0578B", 3: "0654-B"}
