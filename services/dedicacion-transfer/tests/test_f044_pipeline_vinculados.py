# tests/test_f044_pipeline_vinculados.py
"""F-044 · el pipeline con recursos vinculados.

- R9 (T5): `partidas/propuesta` propone la partida de cada subfila con la
  misma regla que el preflight (`partida_del_vinculado`): titular en `CI*`
  ⇒ la CI de su tipo; en postventa o en una partida no `CI*` ⇒ la del
  titular; sin hoja con la subcuenta o con varias ⇒ sin propuesta. Sin
  vinculados, la respuesta y las lecturas de hoy.
- R29 (T5): el lote da lo mismo que la petición suelta y lee las cuentas
  del presupuesto UNA vez por obra (y solo si alguna subfila las necesita).

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

from typing import Any

import pytest
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.partida_resolver import construir_catalogo
from application.services.reglas_vinculados import (
    PartidaTitular,
    partida_ci_del_tipo,
    partida_del_vinculado,
)
from domain.models.registro_models import HoraRecurso, ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    PRESUPUESTO_ORIGEN,
    ClienteFalso,
    SettingsFalso,
    _fila,
)
from tests.test_f055_lote import _ajustes

#: Presupuesto de la obra de origen con las hojas CI de los vinculados.
PRESUPUESTO_VIN = [
    *PRESUPUESTO_ORIGEN,
    _fila(81001, 80000, 3, "CICO13", "TELEFONIA"),
    _fila(81002, 80000, 4, "CIGA14", "GASOIL"),
    _fila(81003, 80000, 5, "CIVE20", "VEHICULO A"),
    _fila(81004, 80000, 6, "CIVE21", "VEHICULO B"),
    _fila(81100, 0, 7, "CD", "COSTES DIRECTOS"),
    _fila(81101, 81100, 1, "CD.1", "HORMIGON"),
]
CUENTAS_VIN = {81001: "0678.CI.4.13", 81002: "0678.CI.4.14",
               81003: "0678.CI.4.20", 81004: "0678.CI.4.20",
               81101: "0678.CD.1.1"}
#: Vinculados: 10 teléfono (CI.4.13), 11 gasoil (CI.4.14), 12 vehículo
#: (CI.4.20, dos hojas), 13 sin cuenta en su hora por defecto.
HORAS_VIN = {
    10: [HoraRecurso(31, "OTEL", None, 30.0, caa_cod="RES.CI.4.13",
                     defecto=True)],
    11: [HoraRecurso(32, "HLPE", None, 1.0, caa_cod="RES.CI.4.99"),
         HoraRecurso(33, "OGAS", None, 120.0, caa_cod="RES.CI.4.14",
                     defecto=True)],
    12: [HoraRecurso(34, "MESVE", None, 300.0, caa_cod="RES.CI.4.20",
                     defecto=True)],
    13: [HoraRecurso(35, "OKM", None, 0.0, defecto=True)],
}


class ClienteVin(ClienteFalso):
    """`ClienteFalso` con el presupuesto de los vinculados, sus horas y las
    cuentas del presupuesto (cada lectura, apuntada)."""

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.partidas_origen = PRESUPUESTO_VIN
        self.horas = {**self.horas, **HORAS_VIN}
        self.cuentas_leidas: list[int] = []
        self.horas_leidas: list[list[int]] = []

    def cuentas_del_presupuesto(self, obra_ide):
        self.cuentas_leidas.append(int(obra_ide))
        return dict(CUENTAS_VIN) if obra_ide == self.obra_origen.ide else {}

    def horas_de_recursos(self, resides):
        self.horas_leidas.append(sorted(resides))
        return super().horas_de_recursos(resides)


def _vin(*ides: int) -> list[dict]:
    return [{"recurso_ide": i, "tipo": "TF", "categoria": None,
             "cod": f"TF-{i}"} for i in ides]


def _linea(clave: str = "a", recurso: int = 200, pv: bool = False,
           paride: int | None = None, vinculados: list[dict] | None = None,
           categoria: str = "Encargado",
           nombre: str = "Acuna Mera, Antonio") -> dict:
    d = {"clave": clave, "recurso_ide": recurso, "nombre": nombre,
         "categoria": categoria, "es_postventa": pv}
    if paride is not None:
        d["paride"] = paride
    if vinculados is not None:
        d["vinculados"] = vinculados
    return d


def _proponer(cli: ClienteFalso, *lineas: dict) -> dict:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso()).proponer(
        empresa=1, obra=ObraEntrada(codigo=OBRA_ORIGEN), ano=2026, mes=7,
        lineas=list(lineas))


def _esperada(titular: PartidaTitular, recurso: int) -> dict | None:
    """Lo que decide la regla del preflight con las mismas entradas."""
    from application.services.cuenta_analitica import subcuenta_de_linea

    nodos = construir_catalogo(PRESUPUESTO_VIN)
    p = partida_del_vinculado(titular, None, True, lambda: partida_ci_del_tipo(
        nodos, CUENTAS_VIN, subcuenta_de_linea(HORAS_VIN[recurso], None)))
    if not p.paride:
        return None
    return {"paride": p.paride, "cod": p.cod, "res": p.res,
            "metodo": p.metodo, "origen": None}


# ================================ R9 ===================================== #
def test_f044_r9_titular_en_ci_cada_vinculado_a_la_ci_de_su_tipo():
    cli = ClienteVin()
    r = _proponer(cli, _linea(vinculados=_vin(10, 11, 12, 13)))
    assert r["propuestas"]["a"]["cod"] == "CI.1.10"     # el titular, en CI
    assert r["vinculados"] == {"a": {
        "10": {"paride": 81001, "cod": "CICO13", "res": "TELEFONIA",
               "metodo": "ci_tipo", "origen": None},
        "11": {"paride": 81002, "cod": "CIGA14", "res": "GASOIL",
               "metodo": "ci_tipo", "origen": None},
        "12": None,                                      # dos hojas
        "13": None,                                      # sin cuenta
    }}
    assert cli.cuentas_leidas == [555001]


def test_f044_r9_la_misma_partida_que_la_regla_del_preflight():
    r = _proponer(ClienteVin(), _linea(vinculados=_vin(10, 11, 12, 13)))
    titular = PartidaTitular(destino="obra", paride=80001, cod="CI.1.10",
                             res="ENCARGADO (ACUNA)", metodo="auto_nombre")
    assert r["vinculados"]["a"] == {
        str(i): _esperada(titular, i) for i in (10, 11, 12, 13)}


def test_f044_r9_titular_en_postventa_va_con_su_partida_sin_leer_cuentas():
    cli = ClienteVin()
    r = _proponer(cli, _linea("pv", pv=True, vinculados=_vin(10, 11)))
    pv = {"paride": 70001, "cod": "0678", "res": "15 VIVIENDAS Y HOSTEL",
          "metodo": "titular", "origen": None}
    assert r["vinculados"] == {"pv": {"10": pv, "11": pv}}
    assert cli.cuentas_leidas == []


def test_f044_r9_titular_con_elegida_no_ci_va_con_ella():
    cli = ClienteVin()
    r = _proponer(cli, _linea(paride=81101, vinculados=_vin(10)))
    assert r["vinculados"] == {"a": {"10": {
        "paride": 81101, "cod": "CD.1", "res": "HORMIGON",
        "metodo": "titular", "origen": None}}}
    assert cli.cuentas_leidas == []


def test_f044_r9_titular_con_elegida_ci_va_a_la_ci_del_tipo():
    r = _proponer(ClienteVin(), _linea(paride=80002, vinculados=_vin(10)))
    assert r["vinculados"]["a"]["10"]["paride"] == 81001


def test_f044_r9_titular_con_elegida_que_no_vale_no_propone():
    """Su titular se omitiría en el preflight («sigue al trabajador»)."""
    cli = ClienteVin()
    r = _proponer(cli, _linea(paride=80000, vinculados=_vin(10)))  # capítulo
    assert r["vinculados"] == {"a": {"10": None}}
    assert cli.cuentas_leidas == []


def test_f044_r9_titular_sin_propuesta_va_a_la_ci_del_tipo():
    r = _proponer(ClienteVin(), _linea(categoria="X", nombre="Nadie",
                                       vinculados=_vin(11)))
    assert r["propuestas"]["a"] is None
    assert r["vinculados"]["a"]["11"]["cod"] == "CIGA14"


def test_f044_r9_varias_lineas_una_lectura_de_cuentas_y_de_horas():
    cli = ClienteVin()
    r = _proponer(cli, _linea("a", vinculados=_vin(10)),
                  _linea("b", recurso=400, nombre="Otro",
                         vinculados=_vin(11, 12)),
                  _linea("c", recurso=300))
    assert set(r["vinculados"]) == {"a", "b"}
    assert cli.cuentas_leidas == [555001]
    assert cli.horas_leidas == [[10, 11, 12]]


@pytest.mark.parametrize("vinculados", [None, []])
def test_f044_r9_sin_vinculados_la_respuesta_y_las_lecturas_de_hoy(
        vinculados):
    con, sin = ClienteVin(), ClienteVin()
    r = _proponer(con, _linea(vinculados=vinculados), _linea("pv", pv=True))
    hoy = _proponer(sin, _linea(), _linea("pv", pv=True))
    assert r == hoy
    assert "vinculados" not in r
    assert con.cuentas_leidas == con.horas_leidas == []
    assert con.n_capitulos_de_obra == sin.n_capitulos_de_obra


# ================================ R29 ==================================== #
def _peticion(*lineas: dict) -> dict:
    return {"empresa": 1, "obra": ObraEntrada(codigo=OBRA_ORIGEN),
            "ano": 2026, "mes": 7, "lineas": list(lineas)}


def test_f044_r29_lote_igual_que_suelto():
    lineas = (_linea("a", vinculados=_vin(10, 12)),
              _linea("pv", pv=True, vinculados=_vin(11)))
    suelto = _proponer(ClienteVin(), *lineas)
    cli = ClienteVin()
    [lote] = RegistroLote(cliente=cli, settings=_ajustes()).proponer(
        [_peticion(*lineas)])
    assert lote == {"ok": True, "propuestas": suelto["propuestas"],
                    "vinculados": suelto["vinculados"]}


def test_f044_r29_lote_cuentas_una_vez_por_obra_y_horas_precargadas():
    peticiones = [_peticion(_linea("a", vinculados=_vin(10))),
                  _peticion(_linea("b", recurso=400, nombre="Otro",
                                   vinculados=_vin(11)))]
    cli = ClienteVin()
    r = RegistroLote(cliente=cli, settings=_ajustes()).proponer(
        peticiones)
    assert [x["vinculados"] for x in r] == [
        _proponer(ClienteVin(), *p["lineas"])["vinculados"]
        for p in peticiones]
    assert r[0]["vinculados"]["a"]["10"]["cod"] == "CICO13"
    assert cli.cuentas_leidas == [555001]
    assert cli.horas_leidas == [[10, 11]]


def test_f044_r29_lote_sin_vinculados_como_hoy():
    cli = ClienteVin()
    [r] = RegistroLote(cliente=cli, settings=_ajustes()).proponer(
        [_peticion(_linea("a"))])
    assert set(r) == {"ok", "propuestas"}
    assert cli.cuentas_leidas == cli.horas_leidas == []


# ======================= R9 · las rutas de propuesta ===================== #
@pytest.fixture
def api(monkeypatch):
    """(TestClient) con el cliente de Sigrid sustituido por `cli`."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    def fabricar(cli):
        monkeypatch.setattr(modulo_app, "SigridWriteClient",
                            lambda **kw: cli)
        ajustes = SimpleNamespace(**AJUSTES, sigrid_lecturas_paralelas=4)
        return TestClient(modulo_app.build_app(ajustes))
    return fabricar


def _cuerpo(*lineas: dict) -> dict:
    return {"empresa": 1, "obra": {"codigo": OBRA_ORIGEN}, "ano": 2026,
            "mes": 7, "lineas": list(lineas)}


def test_f044_r9_la_ruta_devuelve_los_vinculados(api):
    r = api(ClienteVin()).post("/api/partidas/propuesta", json=_cuerpo(
        _linea(vinculados=_vin(10)), _linea("pv", pv=True)))
    assert r.status_code == 200
    assert r.json()["vinculados"] == {"a": {"10": {
        "paride": 81001, "cod": "CICO13", "res": "TELEFONIA",
        "metodo": "ci_tipo", "origen": None}}}


def test_f044_r9_la_ruta_sin_vinculados_pasa_la_linea_de_hoy(api,
                                                              monkeypatch):
    """Sin `paride` ni `vinculados`, el pipeline recibe las cinco claves de
    siempre; con ellos, también esos."""
    recibidas: list[list[dict]] = []
    original = RegistroPipeline.proponer

    def espia(self, **kw):
        recibidas.append(kw["lineas"])
        return original(self, **kw)

    monkeypatch.setattr(RegistroPipeline, "proponer", espia)
    cliente = api(ClienteVin())
    r = cliente.post("/api/partidas/propuesta", json=_cuerpo(_linea()))
    assert "vinculados" not in r.json()
    cliente.post("/api/partidas/propuesta", json=_cuerpo(
        _linea(paride=80001, vinculados=_vin(10))))
    assert recibidas == [
        [_linea()],
        [{**_linea(), "paride": 80001, "vinculados": [
            {"recurso_ide": 10, "tipo": "TF", "categoria": None,
             "cod": "TF-10"}]}]]


def test_f044_r29_la_ruta_del_lote_devuelve_los_vinculados(api):
    r = api(ClienteVin()).post("/api/partidas/propuesta-lote", json={
        "peticiones": [_cuerpo(_linea(vinculados=_vin(10))),
                       _cuerpo(_linea("b"))]})
    assert r.status_code == 200
    a, b = r.json()["obras"]
    assert a["vinculados"]["a"]["10"]["cod"] == "CICO13"
    assert set(b) == {"ok", "propuestas"}


# ======================= T13 · el preflight con vinculados =============== #
# Fixture «de la 0694» con `ide` inventados: el trabajador 200 (MENC) con su
# teléfono 10 (OTEL), su gasoil 11 (OGAS), su vehículo 12 (MESVE, dos hojas
# con su cuenta: sin partida) y unos km 13 (`pre` 0). En pruebas todo va al
# parte 777 de la 0404; el 778 es un parte cerrado del mismo periodo.
from application.services.reglas_porcentajes import (  # noqa: E402
    clave_conflicto,
    clave_sin_partida,
)
from application.services.reglas_vinculados import (  # noqa: E402
    MOTIVO_ELEGIDA_NO_VALIDA,
    MOTIVO_SIGUE_AL_TRABAJADOR,
    MOTIVO_SIN_IMPORTE,
    synckey_vinculado,
)
from domain.models.registro_models import (  # noqa: E402
    LineaSigrid,
    ParteSigrid,
    VinculadoEntrada,
)

from tests.conftest import OBRA_PRUEBAS, linea, linea_previa  # noqa: E402

PT_REG = ParteSigrid(777, "PT26/00251", 1)
PT_CER = ParteSigrid(778, "PT26/00200", 3)


class ClientePre(ClienteVin):
    """`ClienteVin` con los partes del periodo (`periodo`) y las líneas de
    cada uno (777: `lineas_parte`; los demás, `lineas_por_parte`). Anota
    cada lectura de líneas con sus recursos."""

    def __init__(self, *, lineas_parte=None, cerradas=None, **kw) -> None:
        super().__init__(lineas_parte=lineas_parte, **kw)
        self.periodo = [PT_REG, PT_CER] if cerradas is not None else None
        self.lineas_por_parte = ({PT_CER.ide: list(cerradas)}
                                 if cerradas is not None else {})
        self.lecturas_lineas: list[tuple[int, list[int]]] = []
        self.registradas: list[tuple[list, list]] = []

    def partes_del_periodo(self, obra_ide, ano, mes):
        if self.periodo is None:
            return super().partes_del_periodo(obra_ide, ano, mes)
        return list(self.periodo)

    def lineas_del_parte(self, hmoide, resides):
        self.lecturas_lineas.append((int(hmoide), sorted(resides)))
        if int(hmoide) == 777:
            return super().lineas_del_parte(hmoide, resides)
        return [ls for ls in self.lineas_por_parte.get(int(hmoide), [])
                if ls.reside in set(resides)]

    def lineas_registradas(self, claves, ides=()):
        self.registradas.append((sorted(claves), sorted(i for i in ides
                                                        if i)))
        return super().lineas_registradas(claves, ides)


def _v(*ides: int, **kw) -> list[VinculadoEntrada]:
    return [VinculadoEntrada(recurso_ide=i, tipo="TF", tipo_res="TELEFONO",
                             cod=f"TF-{i}", **kw) for i in ides]


def _ls_vin(ide: int, reside: int, can: float | None, *, paride: int = 0,
            synckey: str | None = None) -> LineaSigrid:
    horide, hora = {10: (31, "OTEL"), 11: (33, "OGAS"),
                    12: (34, "MESVE")}[reside]
    return LineaSigrid(ide=ide, reside=reside, fecha_int=20260731,
                       horide=horide, hora_codigo=hora, can=can, tot=None,
                       synckey=synckey, paride=paride)


def _pf(cli: ClienteFalso, *lineas_, obra: str = OBRA_ORIGEN):
    return RegistroPipeline(cliente=cli, settings=SettingsFalso()).preflight(
        obra=ObraEntrada(codigo=obra), lineas=list(lineas_))


def _por(pf) -> dict:
    return {(v.registro_id, v.recurso_ide): v for v in pf.vinculados}


def test_f044_r12_una_linea_por_vinculado_con_el_can_y_la_fec_del_titular():
    cli = ClientePre()
    pf = _pf(cli, linea(vinculados=_v(10, 11, 13)))
    [titular] = pf.acciones
    v = _por(pf)
    assert [(x.recurso_ide, x.accion) for x in pf.vinculados] == [
        (10, "escribir"), (11, "escribir"), (13, "omitir")]
    tel = v[(1, 10)]
    assert (tel.can, tel.fecha_int, tel.hora_codigo, tel.pre, tel.tot) == (
        titular.can, titular.fecha_int, "OTEL", 30.0, 12.0)
    assert (tel.paride, tel.partida_cod, tel.partida_metodo) == (
        81001, "CICO13", "ci_tipo")
    assert (tel.parte_cod, tel.destino) == ("PT26/00251", "obra")
    # R12: la cuenta por `#regla-analitica` con su recurso y su hora, en el
    # centro de la obra destino (en pruebas, la 0404).
    assert (tel.caa_cod, tel.caa_origen) == (f"{OBRA_PRUEBAS}.CI.4.13",
                                             "recurso")
    assert v[(1, 13)].motivo == MOTIVO_SIN_IMPORTE.format(
        tipo="TF", cod="TF-13", hora="OKM")
    assert titular.accion == "escribir" and titular.can == 0.4
    assert cli.cuentas_leidas == [555001]


def test_f044_r27_horas_y_lineas_en_las_mismas_lecturas():
    cli = ClientePre()
    _pf(cli, linea(vinculados=_v(10, 11)))
    assert cli.horas_leidas == [[10, 11, 200]]
    assert cli.lecturas_lineas == [(777, [10, 11, 200])]
    [(claves, ides)] = cli.registradas
    assert claves == sorted(["porcentajes:1", synckey_vinculado(1, 10),
                             synckey_vinculado(1, 11)])


def test_f044_r15_elegida_valida_manda_y_la_que_no_vale_se_omite():
    pf = _pf(ClientePre(), linea(vinculados=[
        *_v(10, paride=81002, partida_cod="CIGA14"),
        *_v(11, paride=80000, partida_cod="CI")]))
    v = _por(pf)
    assert (v[(1, 10)].paride, v[(1, 10)].partida_metodo,
            v[(1, 10)].partida_res) == (81002, "manual", "GASOIL")
    assert v[(1, 11)].accion == "omitir"
    assert v[(1, 11)].motivo == MOTIVO_ELEGIDA_NO_VALIDA.format(cod="CI")


def test_f044_r15_propuesta_guardada_de_la_ci_que_vale_sin_leer_cuentas():
    cli = ClientePre()
    pf = _pf(cli, linea(vinculados=_v(
        10, propuesta_paride=81001, propuesta_cod="CICO13",
        propuesta_res="TELEFONIA", propuesta_metodo="ci_tipo")))
    [v] = pf.vinculados
    assert (v.paride, v.partida_metodo) == (81001, "ci_tipo")
    assert cli.cuentas_leidas == []


def test_f044_r16_sin_ci_del_tipo_o_varias_sin_partida_a_confirmar():
    pf = _pf(ClientePre(), linea(vinculados=_v(12)))
    [v] = pf.vinculados
    assert (v.accion, v.paride) == ("escribir", 0)
    [c] = [c for c in pf.conflictos if c.motivo == "sin_partida"
           and c.vinculado]
    assert c.vinculado == {"tipo": "TF", "cod": "TF-12"}
    assert (c.recurso_ide, c.registros, c.lineas) == (12, [1], [])
    assert c.clave != clave_sin_partida(pf.acciones[0])
    assert c.clave == "sin_partida:1:12"


@pytest.mark.parametrize("extra, paride, cod", [
    ({"es_postventa": True}, 70001, "0678"),
    ({"paride": 81101, "partida_cod": "CD.1"}, 81101, "CD.1")])
def test_f044_r17_titular_en_postventa_o_no_ci_va_con_su_partida(extra,
                                                                 paride, cod):
    cli = ClientePre()
    pf = _pf(cli, linea(vinculados=_v(10, 11), **extra))
    assert {(v.paride, v.partida_cod, v.partida_metodo)
            for v in pf.vinculados} == {(paride, cod, "titular")}
    assert cli.cuentas_leidas == []


def test_f044_r18_titular_omitido_sus_vinculados_le_siguen():
    pf = _pf(ClientePre(), linea(recurso_ide=300, vinculados=_v(10)))
    [t] = pf.acciones
    [v] = pf.vinculados
    assert (t.accion, v.accion) == ("omitir", "omitir")
    assert v.motivo == MOTIVO_SIGUE_AL_TRABAJADOR.format(motivo=t.motivo)


def test_f044_r20_pisado_por_vinculado_a_confirmar():
    """Gasoil a mano al 95 % con su partida CI: la misma identidad."""
    cli = ClientePre(lineas_parte=[_ls_vin(5101, 11, 0.95, paride=81002)])
    pf = _pf(cli, linea(vinculados=_v(10, 11)))
    [c] = [c for c in pf.conflictos if c.vinculado]
    assert (c.motivo, c.clave, c.recurso_ide, c.registros) == (
        "pisado", "11|202607|33|81002", 11, [1])
    assert (c.edita_ide, c.a_cero_ides, c.parte_cod) == (5101, [],
                                                         "PT26/00251")
    assert c.vinculado == {"tipo": "TF", "cod": "TF-11"}
    assert c.nuevas == [{"registro_id": 1, "recurso_ide": 11, "can": 0.4,
                         "tot": 48.0, "hora_codigo": "OGAS",
                         "fecha_int": 20260731, "partida_cod": "CIGA14"}]
    assert _por(pf)[(1, 11)].accion == "escribir"
    assert not [c for c in pf.conflictos if not c.vinculado]


def test_f044_r20_dos_choques_edita_el_menor_y_pone_a_cero_el_otro():
    cli = ClientePre(lineas_parte=[_ls_vin(5102, 11, 0.5, paride=81002),
                                   _ls_vin(5101, 11, 0.45, paride=81002)])
    [c] = [c for c in _pf(cli, linea(vinculados=_v(11))).conflictos
           if c.vinculado]
    assert (c.edita_ide, c.a_cero_ides) == (5101, [5102])


def test_f044_r21_linea_al_cero_del_vinculado_se_edita_sin_confirmar():
    """Teléfono a mano al 0 %: se edita (con aviso), no es conflicto."""
    cli = ClientePre(lineas_parte=[_ls_vin(5201, 10, 0.0, paride=81001)])
    pf = _pf(cli, linea(vinculados=_v(10)))
    [v] = pf.vinculados
    assert v.linea_cero == {
        "ide": 5201, "hmoide": 777, "parte_cod": "PT26/00251", "horide": 31,
        "hora_codigo": "OTEL", "paride": 81001, "can": 0.0,
        "fecha_int": 20260731, "synckey": None}
    assert "se edita la línea 5201" in v.aviso
    assert not pf.conflictos


def test_f044_r21_la_linea_al_cero_del_trabajador_no_es_del_vinculado():
    cli = ClientePre(lineas_parte=[linea_previa(ide=5301, can=0.0)])
    pf = _pf(cli, linea(vinculados=_v(10)))
    assert pf.acciones[0].linea_cero["ide"] == 5301
    assert pf.vinculados[0].linea_cero is None


def test_f044_r22_choque_en_un_parte_cerrado_se_omite():
    cli = ClientePre(cerradas=[_ls_vin(5401, 11, 0.95, paride=81002)])
    pf = _pf(cli, linea(vinculados=_v(10, 11)))
    v = _por(pf)
    assert v[(1, 11)].accion == "omitir"
    assert "PT26/00200" in v[(1, 11)].motivo
    assert v[(1, 11)].caa_ide == 0
    assert v[(1, 10)].accion == "escribir"
    assert not [c for c in pf.conflictos if c.vinculado]


def test_f044_r22_titular_omitido_por_un_cerrado_arrastra_a_sus_vinculados():
    cli = ClientePre(cerradas=[linea_previa(ide=5402, paride=80001)],
                     lineas_parte=[_ls_vin(5101, 11, 0.95, paride=81002)])
    pf = _pf(cli, linea(vinculados=_v(11, 12)))
    [t] = pf.acciones
    assert t.accion == "omitir"
    assert {v.accion for v in pf.vinculados} == {"omitir"}
    assert all(v.motivo == MOTIVO_SIGUE_AL_TRABAJADOR.format(motivo=t.motivo)
               for v in pf.vinculados)
    assert not [c for c in pf.conflictos if c.vinculado]


def test_f044_r23_sobrecarga_del_vinculado_a_confirmar():
    cli = ClientePre(lineas_parte=[_ls_vin(5501, 11, 0.8, paride=81001)])
    pf = _pf(cli, linea(vinculados=_v(11)))
    [c] = [c for c in pf.conflictos if c.vinculado]
    assert (c.motivo, c.clave, c.lineas) == ("sobrecarga",
                                             "sobrecarga:11|202607", [])
    assert (c.suma_existente, c.suma_total) == (0.8, 1.2)
    assert [ls.ide for ls in c.contexto] == [5501]


def test_f044_r19_una_mesve_del_vinculado_no_es_jornada_del_trabajador():
    cli = ClientePre(lineas_parte=[
        _ls_vin(5601, 12, 1.0, paride=81003),
        linea_previa(ide=5602, can=0.5, paride=80002)])
    pf = _pf(cli, linea(vinculados=_v(12)))
    # La del trabajador: 0,5 + 0,4; la MESVE no le suma. La del vehículo
    # (1 + 0,4, su hora) sí es su sobrecarga (R23).
    assert [(c.recurso_ide, c.suma_total) for c in pf.conflictos
            if c.motivo == "sobrecarga"] == [(12, 1.4)]
    assert pf.acciones[0].linea_cero is None


def test_f044_r25_cada_conflicto_con_su_clave_y_el_del_titular_aparte():
    cli = ClientePre(lineas_parte=[
        linea_previa(ide=5701, can=0.4, paride=80001),
        _ls_vin(5702, 10, 0.4, paride=81001)])
    pf = _pf(cli, linea(vinculados=_v(10)))
    claves = {c.clave: c.vinculado for c in pf.conflictos}
    assert claves == {clave_conflicto(pf.acciones[0]): None,
                      "10|202607|31|81001": {"tipo": "TF", "cod": "TF-10"}}


def test_f044_r25_modo_pruebas_solo_la_0404():
    cli = ClientePre()
    pf = _pf(cli, linea(vinculados=_v(10)), linea(
        registro_id=2, es_postventa=True, vinculados=_v(10)))
    assert pf.obra_destino.codigo == OBRA_PRUEBAS
    assert {v.parte_cod for v in pf.vinculados} == {"PT26/00251"}
    assert [p.obra_cod for p in pf.partes] == [OBRA_PRUEBAS]


def test_f044_r26_dos_vinculados_iguales_en_el_mismo_parte_no_comparten_cero():
    """Normal y postventa del mismo trabajador en pruebas: el mismo parte;
    cada acción del teléfono edita su propia línea al 0 %."""
    cli = ClientePre(lineas_parte=[_ls_vin(5801, 10, 0.0, paride=81001),
                                   _ls_vin(5802, 10, 0.0, paride=70001)])
    pf = _pf(cli, linea(vinculados=_v(10)), linea(
        registro_id=2, es_postventa=True, porcentaje=0.6, vinculados=_v(10)))
    v = _por(pf)
    assert (v[(1, 10)].linea_cero["ide"], v[(2, 10)].linea_cero["ide"]) == (
        5801, 5802)


def test_f044_r18_sin_empresa_todo_omitido_y_sus_vinculados_tambien():
    cli = ClientePre()
    pf = _pf(cli, linea(empresa=None, vinculados=_v(10)))
    [t] = pf.acciones
    [v] = pf.vinculados
    assert (t.accion, v.accion) == ("omitir", "omitir")
    assert v.motivo == MOTIVO_SIGUE_AL_TRABAJADOR.format(motivo=t.motivo)
    assert cli.horas_leidas == [] and cli.cuentas_leidas == []
